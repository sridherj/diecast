"""User-invocation lifecycle service for Claude Code slash commands.

Captures every user-typed ``/cast-*`` slash command as a top-level
``agent_runs`` row, then closes it on the matching ``Stop`` event.

Distinguishing characteristics of a user-invocation row (Decision #2):

    agent_name    = "<slash-command-name without leading '/'>"
    input_params  = {"source": "user-prompt", "prompt": "<full prompt text>"}
    parent_run_id = NULL  (always top-level — Decision #3)
    goal_slug     = "system-ops"

The ``register`` write goes through ``agent_service.create_agent_run`` so
DB-layer code is not duplicated; ``complete`` issues a bespoke UPDATE that
filters on the JSON discriminator and a 1-hour staleness window so orphaned
rows from prior sessions never get retroactively closed.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from cast_server.db.connection import get_connection
from cast_server.services._invocation_sources import USER_PROMPT, source_filter_clause
from cast_server.services.agent_service import create_agent_run, update_agent_run

# Decision #5: Stop only closes rows whose started_at is within this window.
# Older "running" rows are treated as stale orphans and left alone.
STALENESS_WINDOW = timedelta(hours=1)

# Decision #1: user-invocation rows live under the system-ops goal, matching
# the existing CLI invocation default in agent_service.invoke_agent.
_GOAL_SLUG = "system-ops"


def register(agent_name: str, prompt: str, session_id: str | None,
             db_path: Path | str | None = None) -> str:
    """Insert a top-level ``running`` agent_run for a user slash-command invocation.

    Returns the new ``run_id``. The row's ``input_params`` JSON carries the
    Decision #2 discriminator ``{"source": "user-prompt", "prompt": prompt}``.
    """
    now = datetime.now(timezone.utc).isoformat()
    run_id = create_agent_run(
        agent_name=agent_name,
        goal_slug=_GOAL_SLUG,
        task_id=None,
        input_params={"source": USER_PROMPT, "prompt": prompt},
        session_id=session_id,
        status="running",
        parent_run_id=None,
        db_path=db_path,
    )
    # create_agent_run sets only `created_at`; the runs tree uses started_at
    # for chronological ordering and rollups, so set it explicitly here.
    update_agent_run(run_id, started_at=now, db_path=db_path)
    return run_id


def complete(session_id: str | None,
             db_path: Path | str | None = None) -> int:
    """Mark every still-``running`` user-prompt row in this session ``completed``.

    Returns the number of rows updated. Returns 0 when ``session_id`` is
    falsy. Decision #4: closing keys off ``session_id`` (no marker file).
    Decision #5: only rows started within ``STALENESS_WINDOW`` are touched —
    older orphans stay running. Decision #14: status is always ``completed``;
    v1 does not detect cancellation.
    """
    if not session_id:
        return 0

    now_dt = datetime.now(timezone.utc)
    now_iso = now_dt.isoformat()
    cutoff_iso = (now_dt - STALENESS_WINDOW).isoformat()

    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            f"""
            UPDATE agent_runs
               SET status = 'completed',
                   completed_at = ?
             WHERE session_id = ?
               AND status = 'running'
               AND {source_filter_clause()}
               AND started_at > ?
            """,
            (now_iso, session_id, USER_PROMPT, cutoff_iso),
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()
