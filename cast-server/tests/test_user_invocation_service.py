"""Unit tests for ``services.user_invocation_service``.

Covers the ``register`` / ``complete`` lifecycle for user-typed slash-command
invocations (sub-phase 1 of capture-user-invocations-as-runs). Tests run
against a fresh ``isolated_db`` (provided by ``conftest.py``); the
``system-ops`` goal — the goal_slug user-invocations live under — is seeded
per-test via the conftest ``ensure_goal`` helper.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cast_server.db.connection import get_connection
from cast_server.services import user_invocation_service
from cast_server.services.agent_service import create_agent_run

from tests.conftest import ensure_goal


SESSION_A = "session-aaaaaaaa"
SESSION_B = "session-bbbbbbbb"


@pytest.fixture
def tmp_db(isolated_db: Path) -> Path:
    """Isolated DB pre-seeded with the ``system-ops`` goal (FK target).

    user_invocation_service.register inserts rows with goal_slug='system-ops'
    and the agent_runs.goal_slug FK is enforced (PRAGMA foreign_keys=ON), so
    the parent goal row must exist before any register() call.
    """
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
    """Backdate a row's ``started_at`` to test the staleness window."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            "UPDATE agent_runs SET started_at = ? WHERE id = ?",
            (started_at, run_id),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# register()
# ---------------------------------------------------------------------------

def test_register_creates_running_row(tmp_db: Path) -> None:
    run_id = user_invocation_service.register(
        agent_name="cast-plan-review",
        prompt="/cast-plan-review look at this",
        session_id=SESSION_A,
        db_path=tmp_db,
    )

    row = _row(tmp_db, run_id)
    assert row["status"] == "running"
    assert row["agent_name"] == "cast-plan-review"
    assert row["goal_slug"] == "system-ops"
    assert row["parent_run_id"] is None
    assert row["task_id"] is None
    assert row["completed_at"] is None
    assert row["started_at"] is not None


def test_register_input_params_carries_source_and_prompt(tmp_db: Path) -> None:
    run_id = user_invocation_service.register(
        agent_name="cast-plan-review",
        prompt="/cast-plan-review do a thing",
        session_id=SESSION_A,
        db_path=tmp_db,
    )

    row = _row(tmp_db, run_id)
    payload = json.loads(row["input_params"])
    assert payload == {
        "source": "user-prompt",
        "prompt": "/cast-plan-review do a thing",
    }


def test_register_session_id_persisted(tmp_db: Path) -> None:
    run_id = user_invocation_service.register(
        agent_name="cast-doctor",
        prompt="/cast-doctor",
        session_id=SESSION_A,
        db_path=tmp_db,
    )

    row = _row(tmp_db, run_id)
    assert row["session_id"] == SESSION_A


# ---------------------------------------------------------------------------
# complete()
# ---------------------------------------------------------------------------

def test_complete_marks_running_row_completed(tmp_db: Path) -> None:
    run_id = user_invocation_service.register(
        agent_name="cast-plan-review",
        prompt="/cast-plan-review",
        session_id=SESSION_A,
        db_path=tmp_db,
    )

    closed = user_invocation_service.complete(SESSION_A, db_path=tmp_db)

    assert closed == 1
    row = _row(tmp_db, run_id)
    assert row["status"] == "completed"
    assert row["completed_at"] is not None


def test_complete_returns_count_of_rows_closed(tmp_db: Path) -> None:
    user_invocation_service.register(
        agent_name="cast-plan-review",
        prompt="/cast-plan-review",
        session_id=SESSION_A,
        db_path=tmp_db,
    )

    closed = user_invocation_service.complete(SESSION_A, db_path=tmp_db)
    assert closed == 1

    # Second call has nothing left to close.
    closed_again = user_invocation_service.complete(SESSION_A, db_path=tmp_db)
    assert closed_again == 0


def test_complete_closes_orphans_in_same_session(tmp_db: Path) -> None:
    run_a = user_invocation_service.register(
        agent_name="cast-plan-review",
        prompt="/cast-plan-review first",
        session_id=SESSION_A,
        db_path=tmp_db,
    )
    run_b = user_invocation_service.register(
        agent_name="cast-doctor",
        prompt="/cast-doctor second",
        session_id=SESSION_A,
        db_path=tmp_db,
    )

    closed = user_invocation_service.complete(SESSION_A, db_path=tmp_db)

    assert closed == 2
    for run_id in (run_a, run_b):
        row = _row(tmp_db, run_id)
        assert row["status"] == "completed"
        assert row["completed_at"] is not None


def test_complete_skips_rows_older_than_staleness_window(tmp_db: Path) -> None:
    run_id = user_invocation_service.register(
        agent_name="cast-plan-review",
        prompt="/cast-plan-review",
        session_id=SESSION_A,
        db_path=tmp_db,
    )

    # Backdate started_at to 90 minutes ago — outside the 1h window.
    backdated = (datetime.now(timezone.utc) - timedelta(minutes=90)).isoformat()
    _shift_started_at(tmp_db, run_id, backdated)

    closed = user_invocation_service.complete(SESSION_A, db_path=tmp_db)

    assert closed == 0
    row = _row(tmp_db, run_id)
    assert row["status"] == "running"
    assert row["completed_at"] is None


def test_complete_only_touches_user_prompt_rows(tmp_db: Path) -> None:
    user_run_id = user_invocation_service.register(
        agent_name="cast-plan-review",
        prompt="/cast-plan-review",
        session_id=SESSION_A,
        db_path=tmp_db,
    )

    # A subprocess-dispatched row sharing the same session_id must NOT be
    # closed by complete() — the discriminator filters it out.
    subprocess_run_id = create_agent_run(
        agent_name="cast-controller",
        goal_slug="system-ops",
        task_id=None,
        input_params={"source": "subprocess", "context": "child work"},
        session_id=SESSION_A,
        status="running",
        db_path=tmp_db,
    )
    # Give it a started_at inside the window so the only thing protecting it
    # is the JSON discriminator, not the staleness filter.
    _shift_started_at(
        tmp_db,
        subprocess_run_id,
        datetime.now(timezone.utc).isoformat(),
    )

    closed = user_invocation_service.complete(SESSION_A, db_path=tmp_db)

    assert closed == 1
    user_row = _row(tmp_db, user_run_id)
    sub_row = _row(tmp_db, subprocess_run_id)
    assert user_row["status"] == "completed"
    assert sub_row["status"] == "running"
    assert sub_row["completed_at"] is None


def test_complete_returns_zero_when_no_session_id(tmp_db: Path) -> None:
    # Even with a matching row in the DB, a falsy session_id short-circuits.
    user_invocation_service.register(
        agent_name="cast-plan-review",
        prompt="/cast-plan-review",
        session_id=SESSION_A,
        db_path=tmp_db,
    )

    assert user_invocation_service.complete(None, db_path=tmp_db) == 0
    assert user_invocation_service.complete("", db_path=tmp_db) == 0


def test_complete_returns_zero_when_no_matching_running_rows(tmp_db: Path) -> None:
    # Row belongs to SESSION_A; calling complete() for SESSION_B finds nothing.
    user_invocation_service.register(
        agent_name="cast-plan-review",
        prompt="/cast-plan-review",
        session_id=SESSION_A,
        db_path=tmp_db,
    )

    closed = user_invocation_service.complete(SESSION_B, db_path=tmp_db)
    assert closed == 0
