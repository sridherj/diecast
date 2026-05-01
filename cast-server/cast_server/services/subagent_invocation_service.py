"""Subagent-invocation lifecycle service for Claude Code Task() dispatches.

Captures every Task()-dispatched ``cast-*`` subagent as an ``agent_runs`` row
and closes it on the matching ``SubagentStop``. Skill invocations recorded
through ``PreToolUse(Skill)`` are appended to whichever cast-* row is the
most-recent running in that session (Decision #1).

Distinguishing characteristics of a subagent-invocation row:

    agent_name      = "<agent_type>"   e.g. "cast-detailed-plan"
    input_params    = {"source": "subagent-start", "prompt": ..., "transcript_path": ...}
    parent_run_id   = resolve_parent_for_subagent(session_id) — most-recent running cast-* row
    goal_slug       = inherited from parent row, or "system-ops" if orphan
    session_id      = SubagentStart.session_id (Claude main-loop session)
    claude_agent_id = SubagentStart.agent_id (per-subagent runtime id)

Closure on ``SubagentStop`` keys on exact ``claude_agent_id`` match — single
row update with no staleness window. User-invocation rows do not populate
``claude_agent_id`` so cross-contamination is structurally impossible.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from cast_server.cli._cast_name import AGENT_TYPE_PATTERN
from cast_server.db.connection import get_connection
from cast_server.services._invocation_sources import SUBAGENT_START
from cast_server.services.agent_service import (
    create_agent_run,
    resolve_parent_for_subagent,
    update_agent_run,
)

_ORPHAN_GOAL_SLUG = "system-ops"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parent_goal_slug(parent_run_id: str | None,
                      db_path: Path | str | None) -> str:
    """Return parent's ``goal_slug`` or ``"system-ops"`` if missing/null/orphan."""
    if not parent_run_id:
        return _ORPHAN_GOAL_SLUG
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT goal_slug FROM agent_runs WHERE id = ?",
            (parent_run_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None or row["goal_slug"] is None:
        return _ORPHAN_GOAL_SLUG
    return row["goal_slug"]


def register(
    agent_type: str,
    session_id: str,
    claude_agent_id: str,
    transcript_path: str | None = None,
    prompt: str | None = None,
    db_path: Path | str | None = None,
) -> str | None:
    """Open a ``running`` agent_run for a Task()-dispatched cast-* subagent.

    Returns the new ``run_id`` or ``None`` when ``agent_type`` is not a
    cast-* name (server-side scope filter — Decision #2). The row inherits
    ``goal_slug`` from its resolved parent or falls back to ``"system-ops"``
    when orphan.
    """
    if not AGENT_TYPE_PATTERN.match(agent_type):
        return None

    parent_run_id = resolve_parent_for_subagent(session_id, db_path=db_path)
    goal_slug = _parent_goal_slug(parent_run_id, db_path)

    run_id = create_agent_run(
        agent_name=agent_type,
        goal_slug=goal_slug,
        task_id=None,
        input_params={
            "source": SUBAGENT_START,
            "prompt": prompt,
            "transcript_path": transcript_path,
        },
        session_id=session_id,
        status="running",
        parent_run_id=parent_run_id,
        claude_agent_id=claude_agent_id,
        db_path=db_path,
    )
    update_agent_run(run_id, started_at=_now_iso(), db_path=db_path)
    return run_id


def complete(claude_agent_id: str,
             db_path: Path | str | None = None) -> int:
    """Close the running subagent row whose ``claude_agent_id`` matches.

    Single-row exact match. Returns 1 on success, 0 when the id is unknown
    or the row has already been closed. No source filter is needed because
    user-invocation rows don't populate ``claude_agent_id``.
    """
    if not claude_agent_id:
        return 0

    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            """
            UPDATE agent_runs
               SET status = 'completed',
                   completed_at = ?
             WHERE claude_agent_id = ?
               AND status = 'running'
            """,
            (_now_iso(), claude_agent_id),
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def record_skill(
    session_id: str,
    skill_name: str,
    invoked_at: str | None = None,
    db_path: Path | str | None = None,
) -> int:
    """Append ``{name, invoked_at}`` to the most-recent running cast-* row.

    Decision #1: no source filter. The most-recent-running cast-* row in
    the session wins, so a Task()-dispatched subagent supersedes its
    slash-command parent for skill attribution while running, and skills
    naturally flow back to the parent after the subagent's
    :func:`complete` flips its status.

    Returns the SQLite ``rowcount`` (0 when no candidate row exists).
    """
    if not session_id or not skill_name:
        return 0

    invoked = invoked_at or _now_iso()
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            """
            UPDATE agent_runs
               SET skills_used = json_insert(
                       skills_used,
                       '$[#]',
                       json_object('name', ?, 'invoked_at', ?))
             WHERE id = (
                 SELECT id FROM agent_runs
                  WHERE session_id = ?
                    AND status = 'running'
                    AND agent_name LIKE 'cast-%'
                  ORDER BY started_at DESC
                  LIMIT 1
             )
            """,
            (skill_name, invoked, session_id),
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()
