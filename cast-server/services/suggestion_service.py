"""Suggestion service — manage GoalDetector suggestions."""

import json
from datetime import datetime, timezone
from pathlib import Path

from taskos.db.connection import get_connection
from taskos.services.goal_service import create_goal


def create_suggestions(suggestions: list[dict], db_path=None):
    """Insert GoalDetector suggestions into DB."""
    conn = get_connection(db_path)
    try:
        for s in suggestions:
            conn.execute(
                """INSERT INTO goal_suggestions
                   (title, rationale, source_entries, status, created_at)
                   VALUES (?, ?, ?, 'pending', ?)""",
                (
                    s["title"],
                    s.get("rationale", ""),
                    json.dumps(s.get("source_dates", [])),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
        conn.commit()
    finally:
        conn.close()


def get_pending_suggestions(db_path=None) -> list[dict]:
    """Get all pending suggestions."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM goal_suggestions WHERE status = 'pending' ORDER BY created_at DESC"
        ).fetchall()
        suggestions = [dict(r) for r in rows]
        for s in suggestions:
            s["source_entries_list"] = json.loads(s["source_entries"]) if s["source_entries"] else []
        return suggestions
    finally:
        conn.close()


def approve_suggestion(suggestion_id: int, goals_dir: Path = None, db_path=None) -> dict:
    """Approve a suggestion — creates a goal at 'idea' stage with origin 'goal-detector'."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM goal_suggestions WHERE id = ?", (suggestion_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"Suggestion {suggestion_id} not found")

        suggestion = dict(row)

        # Create the goal
        goal = create_goal(
            title=suggestion["title"],
            tags=[],
            goals_dir=goals_dir,
            db_path=db_path,
        )

        # Update goal status to 'idea' and origin to 'goal-detector'
        conn.execute(
            "UPDATE goals SET status = 'idea', origin = 'goal-detector' WHERE slug = ?",
            (goal["slug"],),
        )

        # Mark suggestion as approved
        conn.execute(
            """UPDATE goal_suggestions SET status = 'approved',
               resolved_at = ?, created_goal_slug = ?
               WHERE id = ?""",
            (datetime.now(timezone.utc).isoformat(), goal["slug"], suggestion_id),
        )
        conn.commit()
    finally:
        conn.close()

    return goal


def decline_suggestion(suggestion_id: int, db_path=None):
    """Decline a suggestion."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            "UPDATE goal_suggestions SET status = 'declined', resolved_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), suggestion_id),
        )
        conn.commit()
    finally:
        conn.close()
