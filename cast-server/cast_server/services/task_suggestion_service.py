"""Task suggestion service — approve/decline suggestions stored as tasks.

Suggestions are tasks with status='suggested'. This service queries the tasks
table directly and performs status transitions for approve/decline.
"""

from pathlib import Path

from cast_server.db.connection import get_connection
from cast_server.services.task_service import get_task, update_task_status, _rerender_tasks_md


def get_pending_suggestions(goal_slug: str, phase: str = None, db_path=None) -> list[dict]:
    """Get pending suggestions (tasks with status='suggested') for a goal.

    Returns top-level suggestions with 'children' list attached.
    Dict shape matches old task_suggestions format for template compatibility.
    """
    conn = get_connection(db_path)
    try:
        base_query = "SELECT * FROM tasks WHERE goal_slug = ? AND status = 'suggested'"
        params = [goal_slug]
        if phase:
            base_query += " AND phase = ?"
            params.append(phase)
        base_query += " ORDER BY id"

        rows = conn.execute(base_query, params).fetchall()
        all_tasks = [dict(r) for r in rows]
    finally:
        conn.close()

    # Separate parents and children
    children_by_parent = {}
    top_level = []
    for t in all_tasks:
        if t["parent_id"] is not None:
            children_by_parent.setdefault(t["parent_id"], []).append(_to_suggestion_dict(t))
        else:
            top_level.append(_to_suggestion_dict(t))

    # Attach children to parents
    for s in top_level:
        s["children"] = children_by_parent.get(s["id"], [])

    return top_level


def _to_suggestion_dict(task: dict) -> dict:
    """Map task row to the dict shape templates expect."""
    return {
        "id": task["id"],
        "goal_slug": task["goal_slug"],
        "title": task["title"],
        "outcome": task["outcome"],
        "rationale": task["rationale"],
        "task_type": task["task_type"],
        "phase": task["phase"],
        "recommended_agent": task["recommended_agent"],
        "effort_estimate": task["estimated_time"],
        "is_spike": bool(task["is_spike"]),
        "parent_suggestion_id": task["parent_id"],
        "children": [],
    }


def approve_suggestion(suggestion_id: int, goals_dir: Path = None, db_path=None) -> dict:
    """Approve a suggestion — transition status from 'suggested' to 'pending'.

    Returns the updated task dict (for task_item.html fragment).
    """
    task = get_task(suggestion_id, db_path)
    if not task:
        raise ValueError(f"Task {suggestion_id} not found")

    # Idempotency: already approved is a no-op
    if task["status"] == "pending":
        return task

    update_task_status(suggestion_id, "pending", goals_dir=goals_dir, db_path=db_path)
    return get_task(suggestion_id, db_path)


def approve_suggestion_group(suggestion_id: int, goals_dir: Path = None, db_path=None) -> list[dict]:
    """Approve parent + all suggested children to 'pending'.

    Returns list of updated task dicts. Re-renders tasks.md once.
    """
    task = get_task(suggestion_id, db_path)
    if not task:
        raise ValueError(f"Task {suggestion_id} not found")

    conn = get_connection(db_path)
    try:
        # Update parent
        conn.execute(
            "UPDATE tasks SET status = 'pending' WHERE id = ? AND status = 'suggested'",
            (suggestion_id,),
        )
        # Update children
        conn.execute(
            "UPDATE tasks SET status = 'pending' WHERE parent_id = ? AND status = 'suggested'",
            (suggestion_id,),
        )
        conn.commit()
    finally:
        conn.close()

    _rerender_tasks_md(task["goal_slug"], goals_dir, db_path)

    # Collect all updated tasks for the response
    updated_parent = get_task(suggestion_id, db_path)
    result = [updated_parent]
    for sub in updated_parent.get("subtasks", []):
        result.append(sub)
    return result


def approve_parent_only(suggestion_id: int, goals_dir: Path = None, db_path=None) -> dict:
    """Approve only the parent suggestion. Children remain as suggested tasks.

    Children keep their parent_id so they stay grouped under the approved parent.
    """
    task = get_task(suggestion_id, db_path)
    if not task:
        raise ValueError(f"Task {suggestion_id} not found")

    conn = get_connection(db_path)
    try:
        # Approve parent only — orphan children so they appear as standalone suggestions
        conn.execute(
            "UPDATE tasks SET status = 'pending' WHERE id = ? AND status = 'suggested'",
            (suggestion_id,),
        )
        conn.execute(
            "UPDATE tasks SET parent_id = NULL WHERE parent_id = ? AND status = 'suggested'",
            (suggestion_id,),
        )
        conn.commit()
    finally:
        conn.close()

    _rerender_tasks_md(task["goal_slug"], goals_dir, db_path)
    return get_task(suggestion_id, db_path)


def decline_suggestion(suggestion_id: int, db_path=None):
    """Decline a suggestion — transition status to 'declined'."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            "UPDATE tasks SET status = 'declined' WHERE id = ?",
            (suggestion_id,),
        )
        conn.commit()
    finally:
        conn.close()


def decline_suggestion_group(suggestion_id: int, db_path=None):
    """Decline parent + all suggested children."""
    conn = get_connection(db_path)
    try:
        # Decline children first
        conn.execute(
            "UPDATE tasks SET status = 'declined' WHERE parent_id = ? AND status = 'suggested'",
            (suggestion_id,),
        )
        # Decline parent
        conn.execute(
            "UPDATE tasks SET status = 'declined' WHERE id = ?",
            (suggestion_id,),
        )
        conn.commit()
    finally:
        conn.close()
