"""Tests for the new sp1 resolvers on ``services.agent_service``.

* ``resolve_parent_for_subagent(session_id)`` — the SOLE parent-resolution
  path on SubagentStart. Most-recent running cast-* row in the session
  wins; non-cast rows must NOT be returned; completed/failed rows must be
  ignored.
* ``resolve_run_by_claude_agent_id(claude_agent_id)`` — the SOLE closure
  path on SubagentStop. Single-row exact match; defends against duplicates
  by returning the most-recent.
* ``create_agent_run(claude_agent_id=...)`` — sp1 surface so sp2 can
  populate at INSERT time. Existing call sites that pass nothing keep the
  column NULL.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from cast_server.db.connection import get_connection
from cast_server.services.agent_service import (
    create_agent_run,
    resolve_parent_for_subagent,
    resolve_run_by_claude_agent_id,
    update_agent_run,
)

from tests.conftest import ensure_goal


SESSION_A = "session-aaaaaaaa"
SESSION_B = "session-bbbbbbbb"


def _seed(
    db_path: Path,
    *,
    agent_name: str,
    session_id: str | None,
    status: str,
    started_at: str,
    claude_agent_id: str | None = None,
    goal_slug: str = "system-ops",
) -> str:
    ensure_goal(db_path, slug=goal_slug, title=goal_slug)
    run_id = create_agent_run(
        agent_name=agent_name,
        goal_slug=goal_slug,
        task_id=None,
        input_params=None,
        session_id=session_id,
        status=status,
        claude_agent_id=claude_agent_id,
        db_path=db_path,
    )
    update_agent_run(run_id, started_at=started_at, db_path=db_path)
    return run_id


def _iso(seconds_offset: int) -> str:
    base = datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)
    return (base + timedelta(seconds=seconds_offset)).isoformat()


# ---------------------------------------------------------------------------
# resolve_parent_for_subagent
# ---------------------------------------------------------------------------

def test_resolve_parent_for_subagent_returns_none_when_no_row(isolated_db: Path) -> None:
    assert resolve_parent_for_subagent(SESSION_A, db_path=isolated_db) is None


def test_resolve_parent_for_subagent_returns_none_when_no_cast_row_but_other_rows_exist(
    isolated_db: Path,
) -> None:
    """Only a non-cast row (e.g. ``Explore``) is running in the session — must
    NOT be returned. The ``agent_name LIKE 'cast-%'`` filter is contract.
    """
    _seed(
        isolated_db,
        agent_name="Explore",
        session_id=SESSION_A,
        status="running",
        started_at=_iso(0),
    )
    assert resolve_parent_for_subagent(SESSION_A, db_path=isolated_db) is None


def test_resolve_parent_for_subagent_returns_single_running_cast_row(
    isolated_db: Path,
) -> None:
    parent = _seed(
        isolated_db,
        agent_name="cast-detailed-plan",
        session_id=SESSION_A,
        status="running",
        started_at=_iso(0),
    )
    assert resolve_parent_for_subagent(SESSION_A, db_path=isolated_db) == parent


def test_resolve_parent_for_subagent_returns_most_recent_when_multiple_running(
    isolated_db: Path,
) -> None:
    """Outer cast-* + nested cast-* both running; nested is most-recent and
    must win so the next inner subagent attaches to it.
    """
    _seed(
        isolated_db,
        agent_name="cast-orchestrate",
        session_id=SESSION_A,
        status="running",
        started_at=_iso(0),
    )
    nested = _seed(
        isolated_db,
        agent_name="cast-detailed-plan",
        session_id=SESSION_A,
        status="running",
        started_at=_iso(5),
    )
    assert resolve_parent_for_subagent(SESSION_A, db_path=isolated_db) == nested


def test_resolve_parent_for_subagent_excludes_completed_rows(isolated_db: Path) -> None:
    """A completed parent must not be returned — stale-parent guard."""
    _seed(
        isolated_db,
        agent_name="cast-orchestrate",
        session_id=SESSION_A,
        status="completed",
        started_at=_iso(0),
    )
    assert resolve_parent_for_subagent(SESSION_A, db_path=isolated_db) is None

    # Add a running cast-* and confirm we see it (and not the completed one).
    running = _seed(
        isolated_db,
        agent_name="cast-detailed-plan",
        session_id=SESSION_A,
        status="running",
        started_at=_iso(5),
    )
    assert resolve_parent_for_subagent(SESSION_A, db_path=isolated_db) == running


def test_resolve_parent_for_subagent_filters_by_session(isolated_db: Path) -> None:
    """A running cast-* row in a *different* session must not leak through."""
    _seed(
        isolated_db,
        agent_name="cast-orchestrate",
        session_id=SESSION_B,
        status="running",
        started_at=_iso(0),
    )
    assert resolve_parent_for_subagent(SESSION_A, db_path=isolated_db) is None


def test_resolve_parent_for_subagent_returns_none_for_falsy_session(
    isolated_db: Path,
) -> None:
    assert resolve_parent_for_subagent("", db_path=isolated_db) is None


# ---------------------------------------------------------------------------
# resolve_run_by_claude_agent_id
# ---------------------------------------------------------------------------

def test_resolve_run_by_claude_agent_id_returns_none_when_missing(
    isolated_db: Path,
) -> None:
    assert (
        resolve_run_by_claude_agent_id("nonexistent-agent-id", db_path=isolated_db)
        is None
    )


def test_resolve_run_by_claude_agent_id_returns_id_when_present(
    isolated_db: Path,
) -> None:
    run_id = _seed(
        isolated_db,
        agent_name="cast-detailed-plan",
        session_id=SESSION_A,
        status="running",
        started_at=_iso(0),
        claude_agent_id="agent-xyz",
    )
    assert (
        resolve_run_by_claude_agent_id("agent-xyz", db_path=isolated_db) == run_id
    )


def test_resolve_run_by_claude_agent_id_defends_against_dup_returns_most_recent(
    isolated_db: Path,
) -> None:
    """Shouldn't happen — but if two rows share a claude_agent_id, return the
    most-recent by ``started_at``.
    """
    _seed(
        isolated_db,
        agent_name="cast-detailed-plan",
        session_id=SESSION_A,
        status="completed",
        started_at=_iso(0),
        claude_agent_id="dup-agent",
    )
    newer = _seed(
        isolated_db,
        agent_name="cast-detailed-plan",
        session_id=SESSION_B,
        status="running",
        started_at=_iso(60),
        claude_agent_id="dup-agent",
    )
    assert (
        resolve_run_by_claude_agent_id("dup-agent", db_path=isolated_db) == newer
    )


def test_resolve_run_by_claude_agent_id_returns_none_for_falsy_input(
    isolated_db: Path,
) -> None:
    assert resolve_run_by_claude_agent_id("", db_path=isolated_db) is None


# ---------------------------------------------------------------------------
# create_agent_run claude_agent_id surface
# ---------------------------------------------------------------------------

def test_create_agent_run_persists_claude_agent_id(isolated_db: Path) -> None:
    ensure_goal(isolated_db, slug="system-ops", title="System Ops")
    run_id = create_agent_run(
        agent_name="cast-detailed-plan",
        goal_slug="system-ops",
        task_id=None,
        input_params={"source": "subagent-start"},
        session_id=SESSION_A,
        status="running",
        claude_agent_id="agent-xyz",
        db_path=isolated_db,
    )

    conn = get_connection(isolated_db)
    try:
        row = conn.execute(
            "SELECT claude_agent_id FROM agent_runs WHERE id = ?", (run_id,)
        ).fetchone()
    finally:
        conn.close()
    assert row["claude_agent_id"] == "agent-xyz"


def test_create_agent_run_defaults_claude_agent_id_to_null(isolated_db: Path) -> None:
    """Existing call sites that don't pass the kwarg must leave the column NULL."""
    ensure_goal(isolated_db, slug="system-ops", title="System Ops")
    run_id = create_agent_run(
        agent_name="cast-plan-review",
        goal_slug="system-ops",
        task_id=None,
        input_params={"source": "user-prompt"},
        session_id=SESSION_A,
        status="running",
        db_path=isolated_db,
    )

    conn = get_connection(isolated_db)
    try:
        row = conn.execute(
            "SELECT claude_agent_id FROM agent_runs WHERE id = ?", (run_id,)
        ).fetchone()
    finally:
        conn.close()
    assert row["claude_agent_id"] is None
