"""Unit tests for ``services.subagent_invocation_service``.

Sub-phase 2 of cast-subagent-and-skill-capture. Covers the
``register`` / ``complete`` / ``record_skill`` lifecycle for
Task()-dispatched cast-* subagents, including:

* server-side cast-* scope filter (Decision #2),
* parent resolution via ``resolve_parent_for_subagent``
  (most-recent running cast-* row in the session — Decision #1),
* goal_slug inheritance (parent → inherited; orphan → ``"system-ops"``),
* exact ``claude_agent_id`` closure on ``SubagentStop`` (Decision #14),
* skill attribution to the most-recent running cast-* row (Decision #1).

Tests run against the ``isolated_db`` fixture (``conftest.py``); the
``system-ops`` goal is seeded as the FK target for orphan-fallback rows
and for any test that creates a cast-* row outside an explicit goal.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cast_server.db.connection import get_connection
from cast_server.services import subagent_invocation_service, user_invocation_service
from cast_server.services.agent_service import create_agent_run

from tests.conftest import ensure_goal


SESSION_A = "session-aaaaaaaa"
SESSION_B = "session-bbbbbbbb"


@pytest.fixture
def tmp_db(isolated_db: Path) -> Path:
    """Isolated DB pre-seeded with the ``system-ops`` goal (FK target)."""
    ensure_goal(isolated_db, slug="system-ops", title="System Ops")
    return isolated_db


def _row(db_path: Path, run_id: str) -> dict:
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM agent_runs WHERE id = ?", (run_id,)
        ).fetchone()
    finally:
        conn.close()
    assert row is not None, f"run {run_id} not found"
    return dict(row)


def _shift_started_at(db_path: Path, run_id: str, started_at: str) -> None:
    """Override a row's ``started_at`` so most-recent ordering is deterministic."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            "UPDATE agent_runs SET started_at = ? WHERE id = ?",
            (started_at, run_id),
        )
        conn.commit()
    finally:
        conn.close()


def _seed_user_invocation(db_path: Path, *,
                          session_id: str,
                          agent_name: str = "cast-plan-review",
                          started_at: str | None = None) -> str:
    """Seed a user-invocation parent (no claude_agent_id) for parent-resolution tests."""
    run_id = user_invocation_service.register(
        agent_name=agent_name,
        prompt=f"/{agent_name}",
        session_id=session_id,
        db_path=db_path,
    )
    if started_at is not None:
        _shift_started_at(db_path, run_id, started_at)
    return run_id


# ---------------------------------------------------------------------------
# register()
# ---------------------------------------------------------------------------


def test_register_creates_running_row_for_cast_agent(tmp_db: Path) -> None:
    """Cast-* agent_type yields a ``running`` agent_run with the documented shape."""
    run_id = subagent_invocation_service.register(
        agent_type="cast-detailed-plan",
        session_id=SESSION_A,
        claude_agent_id="claude-agent-1",
        prompt="do the thing",
        transcript_path="/tmp/t.jsonl",
        db_path=tmp_db,
    )
    assert run_id is not None

    row = _row(tmp_db, run_id)
    assert row["agent_name"] == "cast-detailed-plan"
    assert row["status"] == "running"
    assert row["session_id"] == SESSION_A
    assert row["claude_agent_id"] == "claude-agent-1"
    assert row["completed_at"] is None
    assert row["started_at"] is not None
    payload = json.loads(row["input_params"])
    assert payload == {
        "source": "subagent-start",
        "prompt": "do the thing",
        "transcript_path": "/tmp/t.jsonl",
    }


def test_register_returns_null_for_non_cast_agent_type(tmp_db: Path) -> None:
    """Non-cast agent_type (e.g. ``Explore``) returns None and writes no row."""
    run_id = subagent_invocation_service.register(
        agent_type="Explore",
        session_id=SESSION_A,
        claude_agent_id="claude-agent-x",
        db_path=tmp_db,
    )
    assert run_id is None

    conn = get_connection(tmp_db)
    try:
        count = conn.execute("SELECT COUNT(*) AS n FROM agent_runs").fetchone()["n"]
    finally:
        conn.close()
    assert count == 0


def test_register_persists_claude_agent_id(tmp_db: Path) -> None:
    """``claude_agent_id`` round-trips into the ``agent_runs`` row."""
    run_id = subagent_invocation_service.register(
        agent_type="cast-controller",
        session_id=SESSION_A,
        claude_agent_id="agent-id-zzzz",
        db_path=tmp_db,
    )
    row = _row(tmp_db, run_id)
    assert row["claude_agent_id"] == "agent-id-zzzz"


def test_register_resolves_parent_via_most_recent_running_cast_row(tmp_db: Path) -> None:
    """A second register() in the same session points at the first via parent_run_id."""
    parent_id = _seed_user_invocation(tmp_db, session_id=SESSION_A)
    child_id = subagent_invocation_service.register(
        agent_type="cast-controller",
        session_id=SESSION_A,
        claude_agent_id="child-1",
        db_path=tmp_db,
    )
    child_row = _row(tmp_db, child_id)
    assert child_row["parent_run_id"] == parent_id


def test_register_returns_orphan_when_no_running_cast_row_in_session(tmp_db: Path) -> None:
    """No cast-* parent in the session → ``parent_run_id`` NULL, goal_slug ``system-ops``."""
    run_id = subagent_invocation_service.register(
        agent_type="cast-detailed-plan",
        session_id=SESSION_A,
        claude_agent_id="orphan-1",
        db_path=tmp_db,
    )
    row = _row(tmp_db, run_id)
    assert row["parent_run_id"] is None
    assert row["goal_slug"] == "system-ops"


def test_register_ignores_non_cast_running_rows_when_resolving_parent(tmp_db: Path) -> None:
    """An ``Explore`` row in the same session must NOT become a cast-* parent."""
    create_agent_run(
        agent_name="Explore",
        goal_slug="system-ops",
        task_id=None,
        input_params={"source": "task-dispatch"},
        session_id=SESSION_A,
        status="running",
        db_path=tmp_db,
    )
    run_id = subagent_invocation_service.register(
        agent_type="cast-controller",
        session_id=SESSION_A,
        claude_agent_id="child-2",
        db_path=tmp_db,
    )
    row = _row(tmp_db, run_id)
    assert row["parent_run_id"] is None  # Explore parent ignored


def test_subagent_register_inherits_parent_goal_slug(tmp_db: Path) -> None:
    """Resolved parent's ``goal_slug`` propagates to the child row."""
    ensure_goal(tmp_db, slug="user-goal", title="User Goal")
    parent_id = create_agent_run(
        agent_name="cast-plan-review",
        goal_slug="user-goal",
        task_id=None,
        input_params={"source": "user-prompt", "prompt": "/cast-plan-review"},
        session_id=SESSION_A,
        status="running",
        db_path=tmp_db,
    )
    _shift_started_at(tmp_db, parent_id,
                      datetime.now(timezone.utc).isoformat())
    child_id = subagent_invocation_service.register(
        agent_type="cast-controller",
        session_id=SESSION_A,
        claude_agent_id="child-3",
        db_path=tmp_db,
    )
    row = _row(tmp_db, child_id)
    assert row["parent_run_id"] == parent_id
    assert row["goal_slug"] == "user-goal"


def test_subagent_register_falls_back_to_system_ops_when_orphan(tmp_db: Path) -> None:
    """Orphan child gets ``goal_slug='system-ops'`` (no parent goal to inherit from)."""
    run_id = subagent_invocation_service.register(
        agent_type="cast-controller",
        session_id=SESSION_B,
        claude_agent_id="orphan-2",
        db_path=tmp_db,
    )
    row = _row(tmp_db, run_id)
    assert row["goal_slug"] == "system-ops"


# ---------------------------------------------------------------------------
# complete()
# ---------------------------------------------------------------------------


def test_complete_closes_only_the_subagent_with_matching_claude_agent_id(tmp_db: Path) -> None:
    """``complete`` flips exactly the row whose ``claude_agent_id`` matches."""
    a = subagent_invocation_service.register(
        agent_type="cast-controller",
        session_id=SESSION_A,
        claude_agent_id="agent-A",
        db_path=tmp_db,
    )
    b = subagent_invocation_service.register(
        agent_type="cast-service",
        session_id=SESSION_A,
        claude_agent_id="agent-B",
        db_path=tmp_db,
    )
    closed = subagent_invocation_service.complete("agent-A", db_path=tmp_db)
    assert closed == 1

    row_a = _row(tmp_db, a)
    row_b = _row(tmp_db, b)
    assert row_a["status"] == "completed"
    assert row_a["completed_at"] is not None
    assert row_b["status"] == "running"
    assert row_b["completed_at"] is None


def test_complete_does_not_touch_user_invocation_rows(tmp_db: Path) -> None:
    """User-invocation rows lack ``claude_agent_id`` so they cannot match."""
    user_run_id = _seed_user_invocation(tmp_db, session_id=SESSION_A)
    closed = subagent_invocation_service.complete("agent-Z", db_path=tmp_db)
    assert closed == 0

    row = _row(tmp_db, user_run_id)
    assert row["status"] == "running"
    assert row["claude_agent_id"] is None


def test_complete_returns_zero_when_claude_agent_id_unknown(tmp_db: Path) -> None:
    """Unknown id → ``rowcount == 0`` (no exception, no side-effects)."""
    closed = subagent_invocation_service.complete("never-seen", db_path=tmp_db)
    assert closed == 0


# ---------------------------------------------------------------------------
# record_skill()
# ---------------------------------------------------------------------------


def test_record_skill_attaches_to_user_invocation_when_no_subagent_running(tmp_db: Path) -> None:
    """Decision #1: slash command shows skills even without Task() subagents."""
    parent_id = _seed_user_invocation(tmp_db, session_id=SESSION_A)
    appended = subagent_invocation_service.record_skill(
        session_id=SESSION_A,
        skill_name="landing-report",
        invoked_at="2026-05-01T12:00:00+00:00",
        db_path=tmp_db,
    )
    assert appended == 1

    row = _row(tmp_db, parent_id)
    skills = json.loads(row["skills_used"])
    assert skills == [
        {"name": "landing-report", "invoked_at": "2026-05-01T12:00:00+00:00"}
    ]


def test_record_skill_attaches_to_subagent_when_both_running(tmp_db: Path) -> None:
    """Most-recent running cast-* row wins; skill goes to the subagent, not the parent."""
    now = datetime.now(timezone.utc)
    parent_id = _seed_user_invocation(
        tmp_db,
        session_id=SESSION_A,
        started_at=(now - timedelta(seconds=10)).isoformat(),
    )
    child_id = subagent_invocation_service.register(
        agent_type="cast-controller",
        session_id=SESSION_A,
        claude_agent_id="child-recent",
        db_path=tmp_db,
    )
    _shift_started_at(tmp_db, child_id, now.isoformat())

    appended = subagent_invocation_service.record_skill(
        session_id=SESSION_A,
        skill_name="cast-spec-checker",
        db_path=tmp_db,
    )
    assert appended == 1

    parent_skills = json.loads(_row(tmp_db, parent_id)["skills_used"])
    child_skills = json.loads(_row(tmp_db, child_id)["skills_used"])
    assert parent_skills == []
    assert len(child_skills) == 1
    assert child_skills[0]["name"] == "cast-spec-checker"


def test_record_skill_appends_in_invocation_order(tmp_db: Path) -> None:
    """Multiple invocations land in the JSON array in call order."""
    parent_id = _seed_user_invocation(tmp_db, session_id=SESSION_A)
    subagent_invocation_service.record_skill(
        session_id=SESSION_A, skill_name="first",
        invoked_at="2026-05-01T12:00:00+00:00", db_path=tmp_db,
    )
    subagent_invocation_service.record_skill(
        session_id=SESSION_A, skill_name="second",
        invoked_at="2026-05-01T12:00:01+00:00", db_path=tmp_db,
    )
    subagent_invocation_service.record_skill(
        session_id=SESSION_A, skill_name="third",
        invoked_at="2026-05-01T12:00:02+00:00", db_path=tmp_db,
    )

    skills = json.loads(_row(tmp_db, parent_id)["skills_used"])
    assert [s["name"] for s in skills] == ["first", "second", "third"]
