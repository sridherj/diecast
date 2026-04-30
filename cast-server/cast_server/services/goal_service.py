"""Goal service — CRUD, status transitions, phase management, write-back to goal.yaml."""

import ast
import json
import logging
import re
from datetime import date
from pathlib import Path

import yaml

from cast_server.config import (
    GOALS_DIR, STATUSES, STATUS_TRANSITIONS, TERMINAL_STATUSES, PHASES,
)
from cast_server.db.connection import get_connection

logger = logging.getLogger(__name__)


def _parse_tags(raw: str | None) -> list:
    """Parse tags from DB — handles both JSON and Python repr formats."""
    if not raw:
        return []
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(raw)
        except (ValueError, SyntaxError):
            return []


def get_all_goals(db_path=None) -> list[dict]:
    """Get all goals with tags_list pre-parsed."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute("SELECT * FROM goals ORDER BY title").fetchall()
        goals = []
        for row in rows:
            goal = dict(row)
            goal["tags_list"] = _parse_tags(goal.get("tags"))
            goals.append(goal)
        return goals
    finally:
        conn.close()


def get_goal(slug: str, db_path=None) -> dict | None:
    """Get a single goal with tags_list pre-parsed."""
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM goals WHERE slug = ?", (slug,)).fetchone()
        if not row:
            return None
        goal = dict(row)
        goal["tags_list"] = _parse_tags(goal.get("tags"))
        return goal
    finally:
        conn.close()


def create_goal(title: str, tags: list[str] = None, in_focus: bool = False,
                goals_dir: Path = None, db_path=None) -> dict:
    """Create a new goal. Creates directory + goal.yaml + DB record + starter tasks."""
    goals_dir = goals_dir or GOALS_DIR
    slug = _slugify(title)
    goal_dir = goals_dir / slug
    goal_dir.mkdir(parents=True, exist_ok=True)

    goal_data = {
        "slug": slug,
        "title": title,
        "status": "accepted",
        "phase": "requirements",
        "origin": "manual",
        "in_focus": in_focus,
        "created_at": str(date.today()),
        "accepted_at": str(date.today()),
        "tags": tags or [],
    }

    _write_goal_yaml(goal_dir, goal_data)

    conn = get_connection(db_path)
    try:
        conn.execute(
            """INSERT OR REPLACE INTO goals
               (slug, title, status, phase, origin, in_focus, created_at, accepted_at,
                tags, folder_path, gstack_dir, external_project_dir)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (slug, title, "accepted", "requirements", "manual",
             1 if in_focus else 0, goal_data["created_at"],
             goal_data["accepted_at"], json.dumps(tags or []),
             str(goal_dir), None, None),
        )
        conn.commit()
    finally:
        conn.close()

    _create_starter_tasks(slug, goals_dir, db_path)
    return get_goal(slug, db_path)


def update_status(slug: str, target_status: str,
                  goals_dir: Path = None, db_path=None) -> dict | None:
    """Change goal lifecycle status. Validates via STATUS_TRANSITIONS."""
    goal = get_goal(slug, db_path)
    if not goal:
        return None

    current = goal["status"]
    allowed = STATUS_TRANSITIONS.get(current, [])
    if target_status not in allowed:
        raise ValueError(f"Cannot transition from {current} to {target_status}")

    goals_dir = goals_dir or GOALS_DIR
    conn = get_connection(db_path)
    try:
        updates = {"status": target_status}

        # When accepting: set phase to "requirements" and create starter tasks
        phase = goal["phase"]
        if current == "idea" and target_status == "accepted":
            phase = "requirements"
            updates["accepted_at"] = str(date.today())
            updates["phase"] = phase

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        conn.execute(
            f"UPDATE goals SET {set_clause} WHERE slug = ?",
            list(updates.values()) + [slug],
        )
        conn.commit()
    finally:
        conn.close()

    # Write changes to goal.yaml
    goal_dir = goals_dir / slug
    yaml_updates = {"status": target_status}
    if current == "idea" and target_status == "accepted":
        yaml_updates["phase"] = "requirements"
        yaml_updates["accepted_at"] = str(date.today())
        _update_goal_yaml_fields(goal_dir, yaml_updates)
        _create_starter_tasks(slug, goals_dir, db_path)
    else:
        _update_goal_yaml_fields(goal_dir, yaml_updates)

    return get_goal(slug, db_path)


def update_phase(slug: str, target_phase: str,
                 goals_dir: Path = None, db_path=None) -> dict | None:
    """Change goal work phase. Free-form — any valid phase allowed."""
    if target_phase not in PHASES:
        raise ValueError(f"Invalid phase: {target_phase}. Must be one of: {PHASES}")

    goal = get_goal(slug, db_path)
    if not goal:
        return None

    if goal["status"] in TERMINAL_STATUSES:
        raise ValueError(f"Cannot change phase of {goal['status']} goal")

    goals_dir = goals_dir or GOALS_DIR
    conn = get_connection(db_path)
    try:
        conn.execute(
            "UPDATE goals SET phase = ? WHERE slug = ?",
            (target_phase, slug),
        )
        conn.commit()
    finally:
        conn.close()

    goal_dir = goals_dir / slug
    _update_goal_yaml_fields(goal_dir, {"phase": target_phase})

    return get_goal(slug, db_path)


def ensure_cast_symlink(goal_slug: str, external_project_dir: str,
                        goals_dir: Path = None) -> Path | None:
    """Create/update .cast symlink in external project pointing to goal dir.

    Returns the symlink path, or None if external_project_dir is invalid.
    """
    goals_dir = goals_dir or GOALS_DIR
    ext_path = Path(external_project_dir).expanduser()
    if not ext_path.exists():
        logger.warning("External project dir does not exist: %s", ext_path)
        return None

    symlink_path = ext_path / ".cast"
    target = (goals_dir / goal_slug).resolve()

    if symlink_path.is_symlink():
        if symlink_path.resolve() == target:
            return symlink_path  # already correct
        symlink_path.unlink()  # points elsewhere, recreate
    elif symlink_path.exists():
        logger.warning(".cast exists as a real file/dir in %s, skipping", ext_path)
        return None

    symlink_path.symlink_to(target)
    logger.info("Created .cast symlink: %s -> %s", symlink_path, target)

    # Add .cast to .gitignore if not already there
    gitignore = ext_path / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text()
        if ".cast" not in content:
            with gitignore.open("a") as f:
                f.write("\n.cast\n")
    else:
        gitignore.write_text(".cast\n")

    return symlink_path


def remove_cast_symlink(external_project_dir: str) -> None:
    """Remove .cast symlink from external project dir (only if it's a symlink)."""
    ext_path = Path(external_project_dir).expanduser()
    symlink_path = ext_path / ".cast"
    if symlink_path.is_symlink():
        symlink_path.unlink()
        logger.info("Removed .cast symlink from %s", ext_path)


def update_config(slug: str, gstack_dir: str | None = None,
                  external_project_dir: str | None = None,
                  goals_dir: Path = None, db_path=None) -> dict | None:
    """Update goal directory config fields (gstack_dir, external_project_dir)."""
    goal = get_goal(slug, db_path)
    if not goal:
        return None

    goals_dir = goals_dir or GOALS_DIR
    old_ext_dir = goal.get("external_project_dir")

    conn = get_connection(db_path)
    try:
        updates = {}
        if gstack_dir is not None:
            updates["gstack_dir"] = gstack_dir or None  # empty string -> NULL
        if external_project_dir is not None:
            updates["external_project_dir"] = external_project_dir or None

        if updates:
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            conn.execute(
                f"UPDATE goals SET {set_clause} WHERE slug = ?",
                (*updates.values(), slug),
            )
            conn.commit()
    finally:
        conn.close()

    # Update goal.yaml
    goal_dir = goals_dir / slug
    yaml_updates = {k: v for k, v in updates.items() if v is not None}
    if yaml_updates:
        _update_goal_yaml_fields(goal_dir, yaml_updates)

    # Manage .cast symlink
    new_ext_dir = updates.get("external_project_dir", old_ext_dir)
    if external_project_dir is not None:
        if old_ext_dir and old_ext_dir != new_ext_dir:
            remove_cast_symlink(old_ext_dir)
        if new_ext_dir:
            ensure_cast_symlink(slug, new_ext_dir, goals_dir)
        elif old_ext_dir:
            remove_cast_symlink(old_ext_dir)

    return get_goal(slug, db_path)


def toggle_focus(slug: str, in_focus: bool,
                 goals_dir: Path = None, db_path=None) -> dict | None:
    """Toggle the in_focus flag for a goal."""
    goals_dir = goals_dir or GOALS_DIR
    goal = get_goal(slug, db_path)
    if not goal:
        return None

    conn = get_connection(db_path)
    try:
        conn.execute(
            "UPDATE goals SET in_focus = ? WHERE slug = ?",
            (1 if in_focus else 0, slug),
        )
        conn.commit()
    finally:
        conn.close()

    goal_dir = goals_dir / slug
    _update_goal_yaml_fields(goal_dir, {"in_focus": in_focus})

    return get_goal(slug, db_path)


def _create_starter_tasks(slug: str, goals_dir=None, db_path=None):
    """Create the starter tasks and their artifact files when goal becomes accepted.

    Idempotent: skips if tasks already exist for this goal.
    """
    from cast_server.config import STARTER_TASKS, GOALS_DIR
    from cast_server.services.task_service import create_tasks_batch

    # Guard: skip if tasks already exist (prevents duplicates on re-acceptance)
    conn = get_connection(db_path)
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE goal_slug = ?", (slug,)
        ).fetchone()[0]
        if count > 0:
            logger.debug("Starter tasks already exist for '%s', skipping", slug)
            return
    finally:
        conn.close()

    goals_dir = goals_dir or GOALS_DIR
    goal_dir = goals_dir / slug

    # Create artifact stub files for tasks that define them
    for task in STARTER_TASKS:
        artifact = task.get("artifact")
        if not artifact:
            continue
        artifact_path = goal_dir / artifact
        if not artifact_path.exists():
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(f"# {task['title']}\n\n")

    create_tasks_batch(slug, STARTER_TASKS, goals_dir, db_path)


def _write_goal_yaml(goal_dir: Path, data: dict):
    """Render goal.yaml from DB state (read-only, not synced back)."""
    yaml_data = {
        "slug": data["slug"],
        "title": data["title"],
        "status": data["status"],
        "phase": data.get("phase"),
        "origin": data.get("origin", "manual"),
        "in_focus": data.get("in_focus", False),
        "created_at": data.get("created_at", str(date.today())),
        "tags": data.get("tags", []),
    }
    if data.get("accepted_at"):
        yaml_data["accepted_at"] = data["accepted_at"]

    # Include directory config fields when set
    if data.get("gstack_dir"):
        yaml_data["gstack_dir"] = data["gstack_dir"]
    if data.get("external_project_dir"):
        yaml_data["external_project_dir"] = data["external_project_dir"]

    with open(goal_dir / "goal.yaml", "w") as f:
        f.write("# AUTO-GENERATED: Read-only render of DB state. Do not edit directly.\n")
        f.write("# Changes: use /cast-goals agent or goal_service API.\n")
        f.write("# Directory config: gstack_dir = reference-only external context (not authoritative),\n")
        f.write("#   external_project_dir = code/execution artifacts destination.\n")
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)


def _update_goal_yaml_fields(goal_dir: Path, fields: dict):
    """Update multiple fields in goal.yaml atomically."""
    yaml_path = goal_dir / "goal.yaml"
    if not yaml_path.exists():
        logger.error("Cannot update fields: goal.yaml missing in %s", goal_dir)
        return

    try:
        with open(yaml_path) as f:
            data = yaml.safe_load(f) or {}

        data.update(fields)

        with open(yaml_path, "w") as f:
            f.write("# AUTO-GENERATED: Read-only render of DB state. Do not edit directly.\n")
            f.write("# Changes: use /cast-goals agent or goal_service API.\n")
            f.write("# Directory config: gstack_dir = reference-only external context (not authoritative),\n")
            f.write("#   external_project_dir = code/execution artifacts destination.\n")
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    except (yaml.YAMLError, OSError) as e:
        logger.error("Failed to update fields in %s: %s", yaml_path, e)


def _slugify(title: str) -> str:
    """Convert title to URL-safe slug."""
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")
