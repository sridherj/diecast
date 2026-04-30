"""Task service — CRUD, status changes, batch creation, tasks.md re-render."""

import json
import logging
from pathlib import Path

from taskos.config import GOALS_DIR, PHASES
from taskos.db.connection import get_connection
from taskos.models.task import TASK_CREATION_STATUSES
from taskos.services.goal_service import get_goal

logger = logging.getLogger(__name__)


def _validate_artifact_paths(paths: list[str] | None, goal_slug: str = None, db_path=None) -> None:
    """Validate artifact paths are safe — reject traversal and absolute paths.

    Uses Path.resolve() canonicalization (R5: avoids false-positives on names like foo..bar.md).
    """
    if not paths:
        return
    for p in paths:
        if p.startswith('/'):
            raise ValueError(f"Invalid artifact path (absolute): {p}")
        # Use canonicalization to catch traversal (../../../etc)
        if goal_slug:
            goal_dir = GOALS_DIR / goal_slug
            resolved = (goal_dir / p).resolve()
            
            is_valid = resolved.is_relative_to(goal_dir.resolve())
            if not is_valid:
                goal = get_goal(goal_slug, db_path)
                if goal and goal.get("external_project_dir"):
                    ext_dir = Path(goal["external_project_dir"]).expanduser().resolve()
                    if resolved.is_relative_to(ext_dir):
                        is_valid = True
            
            if not is_valid:
                raise ValueError(f"Invalid artifact path (traversal): {p}")
        else:
            # Fallback: check for .. path components when goal_slug unavailable
            if any(part == '..' for part in Path(p).parts):
                raise ValueError(f"Invalid artifact path (traversal): {p}")


def get_tasks_for_goal(goal_slug: str, phase: str = None, include_suggestions: bool = False, db_path=None) -> list[dict]:
    """Get tasks for a goal, optionally filtered by phase. Excludes sub-tasks from top level.
    Each parent task has a 'subtasks' list attached.
    By default excludes suggested/declined tasks unless include_suggestions=True."""
    conn = get_connection(db_path)
    try:
        status_filter = "" if include_suggestions else " AND status NOT IN ('suggested', 'declined')"
        if phase:
            rows = conn.execute(
                f"SELECT * FROM tasks WHERE goal_slug = ? AND phase = ? AND parent_id IS NULL{status_filter} ORDER BY sort_order",
                (goal_slug, phase),
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT * FROM tasks WHERE goal_slug = ? AND parent_id IS NULL{status_filter} ORDER BY sort_order",
                (goal_slug,),
            ).fetchall()
        tasks = [dict(r) for r in rows]
        for task in tasks:
            raw = task.get("task_artifacts")
            try:
                task["task_artifacts"] = json.loads(raw) if raw and raw.strip() else None
            except (json.JSONDecodeError, TypeError):
                task["task_artifacts"] = None

        # Batch-fetch all subtasks for this goal
        all_subtasks = conn.execute(
            f"SELECT * FROM tasks WHERE goal_slug = ? AND parent_id IS NOT NULL{status_filter} ORDER BY sort_order",
            (goal_slug,),
        ).fetchall()

        # Group by parent_id
        subtasks_by_parent = {}
        for sub in all_subtasks:
            sub_dict = dict(sub)
            sub_dict["task_artifacts"] = json.loads(sub_dict["task_artifacts"]) if sub_dict.get("task_artifacts") else None
            subtasks_by_parent.setdefault(sub_dict["parent_id"], []).append(sub_dict)

        # Attach to parents
        for task in tasks:
            task["subtasks"] = subtasks_by_parent.get(task["id"], [])

        return tasks
    finally:
        conn.close()


def create_task(
    goal_slug: str,
    title: str,
    outcome: str = None,
    action: str = None,
    task_type: str = None,
    estimated_time: str = None,
    energy: str = None,
    assigned_to: str = None,
    phase: str = "execution",
    tip: str = None,
    recommended_agent: str = None,
    parent_id: int = None,
    task_artifacts: list[str] = None,
    rationale: str = None,
    is_spike: bool = False,
    status: str = "pending",
    goals_dir: Path = None,
    db_path=None,
    _conn=None,
) -> dict:
    """Create a new task. Inserts into DB, then re-renders tasks.md.

    If parent_id is set, validates that the parent exists and is not itself a sub-task (1-level max).
    If _conn is provided, uses that connection without committing (caller manages transaction).
    """
    if status not in TASK_CREATION_STATUSES:
        raise ValueError(f"Status on creation must be one of {TASK_CREATION_STATUSES}, got '{status}'")

    own_conn = _conn is None
    conn = _conn or get_connection(db_path)
    try:
        # Validate parent_id if provided
        if parent_id is not None:
            parent = conn.execute(
                "SELECT id, parent_id FROM tasks WHERE id = ?", (parent_id,)
            ).fetchone()
            if not parent:
                raise ValueError(f"Parent task not found: {parent_id}")
            if parent["parent_id"] is not None:
                raise ValueError(f"Cannot nest sub-tasks: task {parent_id} is already a sub-task")

        if parent_id is not None:
            max_order = conn.execute(
                "SELECT MAX(sort_order) FROM tasks WHERE goal_slug = ? AND parent_id = ?",
                (goal_slug, parent_id),
            ).fetchone()[0]
        else:
            max_order = conn.execute(
                "SELECT MAX(sort_order) FROM tasks WHERE goal_slug = ? AND parent_id IS NULL",
                (goal_slug,),
            ).fetchone()[0]
        sort_order = (max_order or 0) + 1

        _validate_artifact_paths(task_artifacts, goal_slug=goal_slug, db_path=db_path)
        artifacts_json = json.dumps(task_artifacts) if task_artifacts else None

        cursor = conn.execute(
            """INSERT INTO tasks
               (goal_slug, phase, parent_id, title, outcome, action, task_type,
                estimated_time, energy, assigned_to, status, sort_order,
                tip, recommended_agent, task_artifacts, rationale, is_spike)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (goal_slug, phase, parent_id, title, outcome, action, task_type,
             estimated_time, energy, assigned_to, status, sort_order,
             tip, recommended_agent, artifacts_json, rationale,
             1 if is_spike else 0),
        )
        task_id = cursor.lastrowid
        if own_conn:
            conn.commit()

        task = dict(conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone())
    finally:
        if own_conn:
            conn.close()

    if own_conn and status != 'suggested':
        _rerender_tasks_md(goal_slug, goals_dir, db_path)
    return task


def create_tasks_batch(goal_slug: str, tasks_data: list[dict],
                       goals_dir=None, db_path=None):
    """Insert N tasks in one transaction, rerender tasks.md once at end.

    tasks_data: list of dicts with keys: title, phase, tip (optional), recommended_agent (optional)
    """
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT COALESCE(MAX(sort_order), 0) as max_order FROM tasks WHERE goal_slug = ?",
            (goal_slug,),
        ).fetchone()
        next_order = row["max_order"] + 1

        for task in tasks_data:
            conn.execute(
                """INSERT INTO tasks (goal_slug, phase, title, tip, recommended_agent, task_artifacts, status, sort_order)
                   VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)""",
                (goal_slug, task["phase"], task["title"],
                 task.get("tip"), task.get("recommended_agent"),
                 json.dumps(task.get("task_artifacts")) if task.get("task_artifacts") else None,
                 next_order),
            )
            next_order += 1

        conn.commit()
    finally:
        conn.close()

    _rerender_tasks_md(goal_slug, goals_dir, db_path)


def update_task_status(
    task_id: int,
    status: str,
    goals_dir: Path = None,
    db_path=None,
) -> dict | None:
    """Update task status (pending/in_progress/completed).

    If the task is a subtask (has parent_id), also returns refreshed parent
    as task["parent_task"] for OOB swap in the API layer.
    """
    conn = get_connection(db_path)
    try:
        conn.execute(
            "UPDATE tasks SET status = ? WHERE id = ?",
            (status, task_id),
        )
        conn.commit()

        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            return None
        task = dict(row)
    finally:
        conn.close()

    _rerender_tasks_md(task["goal_slug"], goals_dir, db_path)

    # If this is a subtask, attach refreshed parent for OOB swap
    if task.get("parent_id"):
        task["parent_task"] = get_task(task["parent_id"], db_path)

    return task


def complete_task(
    task_id: int,
    actual_time: str = None,
    moved_toward_goal: str = None,
    notes: str = None,
    goals_dir: Path = None,
    db_path=None,
) -> dict | None:
    """Mark a task as completed with metadata."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            """UPDATE tasks SET status = 'completed',
               actual_time = ?, moved_toward_goal = ?, completion_notes = ?
               WHERE id = ?""",
            (actual_time, moved_toward_goal, notes, task_id),
        )
        conn.commit()

        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            return None
        task = dict(row)
    finally:
        conn.close()

    _rerender_tasks_md(task["goal_slug"], goals_dir, db_path)

    # If this is a subtask, attach refreshed parent for OOB swap
    if task.get("parent_id"):
        task["parent_task"] = get_task(task["parent_id"], db_path)

    return task


def get_task(task_id: int, db_path=None) -> dict | None:
    """Get a single task by ID. Always attaches subtasks list."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            return None
        task = dict(row)
        raw = task.get("task_artifacts")
        try:
            task["task_artifacts"] = json.loads(raw) if raw and raw.strip() else None
        except (json.JSONDecodeError, TypeError):
            task["task_artifacts"] = None
        # Attach subtasks (empty list for leaf tasks or subtasks themselves)
        subtask_rows = conn.execute(
            "SELECT * FROM tasks WHERE parent_id = ? ORDER BY sort_order",
            (task_id,),
        ).fetchall()
        task["subtasks"] = []
        for r in subtask_rows:
            sub = dict(r)
            sub["task_artifacts"] = json.loads(sub["task_artifacts"]) if sub.get("task_artifacts") else None
            task["subtasks"].append(sub)
        return task
    finally:
        conn.close()


def update_task(
    task_id: int,
    goals_dir: Path = None,
    db_path=None,
    **fields,
) -> dict | None:
    """Update editable fields on a task. Re-renders tasks.md."""
    allowed = {
        "title", "outcome", "action", "task_type",
        "estimated_time", "energy", "assigned_to",
        "phase", "tip", "recommended_agent", "task_artifacts",
    }
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    for k, v in updates.items():
        if v == "":
            updates[k] = None

    # Fetch goal_slug for artifact path validation (needs canonicalization against goal dir)
    goal_slug = None
    if "task_artifacts" in updates:
        conn_lookup = get_connection(db_path)
        try:
            row = conn_lookup.execute("SELECT goal_slug FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if row:
                goal_slug = row["goal_slug"]
        finally:
            conn_lookup.close()

    # Handle task_artifacts serialization
    if "task_artifacts" in updates:
        val = updates["task_artifacts"]
        if isinstance(val, list):
            _validate_artifact_paths(val, goal_slug=goal_slug, db_path=db_path)
            updates["task_artifacts"] = json.dumps(val)
        elif isinstance(val, str):
            # Already JSON string from form
            parsed = json.loads(val) if val else None
            if parsed:
                _validate_artifact_paths(parsed, goal_slug=goal_slug, db_path=db_path)
            updates["task_artifacts"] = val

    if not updates:
        return get_task(task_id, db_path)

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [task_id]

    conn = get_connection(db_path)
    try:
        conn.execute(
            f"UPDATE tasks SET {set_clause} WHERE id = ?", values,
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            return None
        task = dict(row)
    finally:
        conn.close()

    # Deserialize task_artifacts
    raw = task.get("task_artifacts") if task else None
    if raw and isinstance(raw, str) and raw.strip():
        try:
            task["task_artifacts"] = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            task["task_artifacts"] = None
    elif task:
        task["task_artifacts"] = None

    _rerender_tasks_md(task["goal_slug"], goals_dir, db_path)
    return task


def _rerender_tasks_md(goal_slug: str, goals_dir: Path = None, db_path=None):
    """Re-render tasks.md from DB, grouped by phase."""
    goals_dir = goals_dir or GOALS_DIR
    goal = get_goal(goal_slug, db_path)
    if not goal:
        return

    conn = get_connection(db_path)
    try:
        # Get top-level tasks (exclude suggested/declined from rendered output)
        tasks = conn.execute(
            "SELECT * FROM tasks WHERE goal_slug = ? AND parent_id IS NULL AND status NOT IN ('suggested', 'declined') ORDER BY sort_order",
            (goal_slug,),
        ).fetchall()

        # Batch-fetch ALL subtasks for this goal (fixes N+1), excluding suggested/declined
        all_subtasks = conn.execute(
            "SELECT * FROM tasks WHERE goal_slug = ? AND parent_id IS NOT NULL AND status NOT IN ('suggested', 'declined') ORDER BY sort_order",
            (goal_slug,),
        ).fetchall()
        subtasks_by_parent = {}
        for sub in all_subtasks:
            subtasks_by_parent.setdefault(sub["parent_id"], []).append(dict(sub))

        # Group by phase
        phase_tasks = {phase: [] for phase in PHASES}
        for task in tasks:
            phase = task["phase"] or "execution"
            if phase in phase_tasks:
                phase_tasks[phase].append(dict(task))

        # Sort within phase: in_progress first, then pending, then completed
        status_order = {"in_progress": 0, "pending": 1, "completed": 2}
        for phase in PHASES:
            phase_tasks[phase].sort(key=lambda t: status_order.get(t["status"], 1))

        # Render
        lines = [
            "<!-- AUTO-GENERATED: Read-only render of DB state. Do not edit directly. -->",
            "<!-- Changes: use /taskos-tasks agent or task_service API. -->",
            f"# Tasks — {goal['title']}",
            "",
        ]

        for phase in PHASES:
            lines.append(f"## {phase.capitalize()}")
            tasks_in_phase = phase_tasks[phase]
            if not tasks_in_phase:
                lines.append("")
                continue
            for task in tasks_in_phase:
                lines.extend(_render_task(task))
                # Render sub-tasks indented (from batch dict, no extra query)
                for sub in subtasks_by_parent.get(task["id"], []):
                    sub_lines = _render_task(sub)
                    lines.extend("    " + sl for sl in sub_lines)
            lines.append("")
    finally:
        conn.close()

    # Write file
    goal_dir = goals_dir / goal_slug
    tasks_path = goal_dir / "tasks.md"
    try:
        tasks_path.write_text("\n".join(lines))
    except OSError as e:
        logger.error("Failed to write tasks.md for %s: %s", goal_slug, e)


def _render_task(task: dict) -> list[str]:
    """Render a single task as markdown lines."""
    checkbox = {"pending": " ", "in_progress": "-", "completed": "x"}.get(task["status"], " ")

    # Title line (bold title + optional outcome/action)
    title_part = f"**{task['title']}**"
    if task.get("outcome") and task.get("action"):
        title_part += f": {task['outcome']} → {task['action']}"
    elif task.get("outcome"):
        title_part += f": {task['outcome']}"

    line = f"- [{checkbox}] {title_part}"

    # Agent badge inline
    if task.get("recommended_agent"):
        line += f" [agent: {task['recommended_agent']}]"

    lines = [line]

    # Metadata lines (indented)
    if task.get("tip"):
        lines.append(f"      Tip: {task['tip']}")

    # Render artifacts (DB stores as JSON list, render as comma-separated)
    artifacts = task.get("task_artifacts")
    if artifacts:
        if isinstance(artifacts, str):
            artifacts = json.loads(artifacts)
        if artifacts:
            lines.append(f"      Artifacts: {', '.join(artifacts)}")

    if task["status"] != "completed":
        meta_parts = []
        if task.get("task_type"):
            meta_parts.append(f"Type: {task['task_type']}")
        if task.get("estimated_time"):
            meta_parts.append(f"Est: {task['estimated_time']}")
        if task.get("energy"):
            meta_parts.append(f"Energy: {task['energy']}")

        if meta_parts:
            lines.append(f"      {' | '.join(meta_parts)}")
        if task.get("assigned_to"):
            lines.append(f"      Assigned: {task['assigned_to']}")
    else:
        completion_parts = []
        if task.get("actual_time"):
            completion_parts.append(f"Actual: {task['actual_time']}")
        if task.get("moved_toward_goal"):
            completion_parts.append(f"Moved toward goal: {task['moved_toward_goal']}")
        if completion_parts:
            lines.append(f"      {' | '.join(completion_parts)}")
        if task.get("completion_notes"):
            lines.append(f"      Notes: {task['completion_notes']}")

    return lines
