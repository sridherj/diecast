"""Endpoint tests for `POST /api/agents/user-invocations` and `/complete`.

Sub-phase 2 of capture-user-invocations-as-runs. Covers happy path,
optional session_id, idempotent close on missing session, and the
**load-bearing safety property** (Decision #2 + #11): closing a session
must NOT touch subprocess-dispatched rows that happen to share the same
``session_id``. The discriminator is
``json_extract(input_params, '$.source') = 'user-prompt'``.

Tests stand up a hermetic FastAPI app + ``TestClient`` per the existing
``test_runs_api.py`` pattern; ``isolated_db`` from ``conftest.py`` swaps
``cast_server.config.DB_PATH`` so the service-layer write goes to the
test database. The ``system-ops`` goal is seeded as the FK target for
user-invocation rows.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CAST_SERVER_DIR = REPO_ROOT / "cast-server"

if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))

from tests.conftest import ensure_goal  # noqa: E402


SESSION_X = "session-xxxxxxxx"


@pytest.fixture
def env(isolated_db: Path, monkeypatch):
    """Wire up a TestClient over the api_agents router on a hermetic DB.

    ``isolated_db`` already monkeypatched ``cast_server.config.DB_PATH``,
    but ``cast_server.db.connection`` imports ``DB_PATH`` at module load
    so the binding inside ``get_connection`` is unaffected by config
    patches. Mirror the pattern in ``test_runs_api.py`` and patch the
    ``connection`` module's ``DB_PATH`` directly. ``system-ops`` is
    seeded as the FK target for user-invocation rows.
    """
    pytest.importorskip("cast_server.config")
    ensure_goal(isolated_db, slug="system-ops", title="System Ops")

    from cast_server.db import connection as _connection
    monkeypatch.setattr(_connection, "DB_PATH", isolated_db)

    from cast_server.routes import api_agents

    app = FastAPI()
    app.include_router(api_agents.router)
    return {
        "client": TestClient(app),
        "db_path": isolated_db,
    }


def _row(db_path: Path, run_id: str) -> dict:
    from cast_server.db.connection import get_connection

    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM agent_runs WHERE id = ?", (run_id,)
        ).fetchone()
    finally:
        conn.close()
    assert row is not None, f"run {run_id} not found"
    return dict(row)


# ---------------------------------------------------------------------------
# POST /api/agents/user-invocations
# ---------------------------------------------------------------------------


def test_open_user_invocation_returns_run_id(env):
    """Happy path: a valid body returns 200 and a non-empty run_id."""
    r = env["client"].post(
        "/api/agents/user-invocations",
        json={
            "agent_name": "cast-plan-review",
            "prompt": "/cast-plan-review look at this",
            "session_id": SESSION_X,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert "run_id" in body
    assert isinstance(body["run_id"], str)
    assert body["run_id"]


def test_open_user_invocation_creates_running_row(env):
    """Posted body materializes the Decision-#2 row shape in agent_runs."""
    r = env["client"].post(
        "/api/agents/user-invocations",
        json={
            "agent_name": "cast-plan-review",
            "prompt": "/cast-plan-review do the thing",
            "session_id": SESSION_X,
        },
    )
    assert r.status_code == 200
    run_id = r.json()["run_id"]

    row = _row(env["db_path"], run_id)
    assert row["agent_name"] == "cast-plan-review"
    assert row["status"] == "running"
    assert row["parent_run_id"] is None
    assert row["session_id"] == SESSION_X
    payload = json.loads(row["input_params"])
    assert payload == {
        "source": "user-prompt",
        "prompt": "/cast-plan-review do the thing",
    }


def test_open_user_invocation_session_id_optional(env):
    """``session_id`` is optional — row inserts with NULL session_id."""
    r = env["client"].post(
        "/api/agents/user-invocations",
        json={
            "agent_name": "cast-doctor",
            "prompt": "/cast-doctor",
        },
    )
    assert r.status_code == 200
    run_id = r.json()["run_id"]

    row = _row(env["db_path"], run_id)
    assert row["session_id"] is None
    assert row["status"] == "running"


# ---------------------------------------------------------------------------
# POST /api/agents/user-invocations/complete
# ---------------------------------------------------------------------------


def test_complete_user_invocation_returns_closed_count(env):
    """Register-then-complete returns ``{"closed": 1}`` and flips the row."""
    open_r = env["client"].post(
        "/api/agents/user-invocations",
        json={
            "agent_name": "cast-plan-review",
            "prompt": "/cast-plan-review",
            "session_id": SESSION_X,
        },
    )
    assert open_r.status_code == 200
    run_id = open_r.json()["run_id"]

    close_r = env["client"].post(
        "/api/agents/user-invocations/complete",
        json={"session_id": SESSION_X},
    )
    assert close_r.status_code == 200
    assert close_r.json() == {"closed": 1}

    row = _row(env["db_path"], run_id)
    assert row["status"] == "completed"
    assert row["completed_at"] is not None


def test_complete_with_no_session_id_returns_zero(env):
    """Missing/null session_id is **not** an error — returns ``{"closed": 0}``."""
    # Empty body
    r1 = env["client"].post(
        "/api/agents/user-invocations/complete",
        json={},
    )
    assert r1.status_code == 200
    assert r1.json() == {"closed": 0}

    # Explicit null
    r2 = env["client"].post(
        "/api/agents/user-invocations/complete",
        json={"session_id": None},
    )
    assert r2.status_code == 200
    assert r2.json() == {"closed": 0}


def test_complete_does_not_close_subprocess_rows(env):
    """**Safety property:** rows lacking the user-prompt discriminator survive.

    Insert a subprocess-dispatched ``running`` row that shares ``session_id``
    with a user-invocation. ``/complete`` must close only the user-invocation
    row and leave the subprocess row alone.
    """
    from cast_server.services.agent_service import create_agent_run
    from cast_server.db.connection import get_connection

    # User-invocation via the endpoint.
    open_r = env["client"].post(
        "/api/agents/user-invocations",
        json={
            "agent_name": "cast-plan-review",
            "prompt": "/cast-plan-review",
            "session_id": SESSION_X,
        },
    )
    user_run_id = open_r.json()["run_id"]

    # Subprocess row sharing the session_id; uses a non-user-prompt source so
    # the JSON discriminator filters it out.
    subprocess_run_id = create_agent_run(
        agent_name="cast-controller",
        goal_slug="system-ops",
        task_id=None,
        input_params={"source": "subprocess", "context": "child work"},
        session_id=SESSION_X,
        status="running",
        db_path=env["db_path"],
    )
    # Set a started_at inside the staleness window — the only thing protecting
    # this row is the discriminator, not the time filter.
    conn = get_connection(env["db_path"])
    try:
        conn.execute(
            "UPDATE agent_runs SET started_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), subprocess_run_id),
        )
        conn.commit()
    finally:
        conn.close()

    close_r = env["client"].post(
        "/api/agents/user-invocations/complete",
        json={"session_id": SESSION_X},
    )
    assert close_r.status_code == 200
    assert close_r.json() == {"closed": 1}

    user_row = _row(env["db_path"], user_run_id)
    sub_row = _row(env["db_path"], subprocess_run_id)
    assert user_row["status"] == "completed"
    assert sub_row["status"] == "running"
    assert sub_row["completed_at"] is None


# ---------------------------------------------------------------------------
# POST /api/agents/subagent-invocations*
# Sub-phase 2 of cast-subagent-and-skill-capture. One named test per route.
# ---------------------------------------------------------------------------


SUBAGENT_SESSION = "session-subagent-1"


def test_subagent_invocation_open_endpoint(env):
    """POST /subagent-invocations: validates request shape, response shape, DB write.

    Covers the cast-* scope filter (Decision #2): a non-cast ``agent_type``
    returns ``{"run_id": null}`` and creates no row, while a cast-* type
    returns a real run_id and persists ``claude_agent_id``.
    """
    # Cast-* agent → run_id + persisted claude_agent_id.
    r_cast = env["client"].post(
        "/api/agents/subagent-invocations",
        json={
            "agent_type": "cast-detailed-plan",
            "session_id": SUBAGENT_SESSION,
            "claude_agent_id": "claude-agent-open-1",
            "transcript_path": "/tmp/t.jsonl",
            "prompt": "do the thing",
        },
    )
    assert r_cast.status_code == 200
    body = r_cast.json()
    assert isinstance(body["run_id"], str)
    assert body["run_id"]

    row = _row(env["db_path"], body["run_id"])
    assert row["agent_name"] == "cast-detailed-plan"
    assert row["status"] == "running"
    assert row["session_id"] == SUBAGENT_SESSION
    assert row["claude_agent_id"] == "claude-agent-open-1"
    payload = json.loads(row["input_params"])
    assert payload == {
        "source": "subagent-start",
        "prompt": "do the thing",
        "transcript_path": "/tmp/t.jsonl",
    }

    # Non-cast agent → run_id is null and no new row inserted.
    r_explore = env["client"].post(
        "/api/agents/subagent-invocations",
        json={
            "agent_type": "Explore",
            "session_id": "session-non-cast",
            "claude_agent_id": "claude-agent-explore",
        },
    )
    assert r_explore.status_code == 200
    assert r_explore.json() == {"run_id": None}

    from cast_server.db.connection import get_connection
    conn = get_connection(env["db_path"])
    try:
        n = conn.execute(
            "SELECT COUNT(*) AS n FROM agent_runs WHERE session_id = ?",
            ("session-non-cast",),
        ).fetchone()["n"]
    finally:
        conn.close()
    assert n == 0


def test_subagent_invocation_complete_endpoint(env):
    """POST /subagent-invocations/complete: round-trips a single ``claude_agent_id``."""
    # Open two distinct subagents in the same session — only one should close.
    open_r1 = env["client"].post(
        "/api/agents/subagent-invocations",
        json={
            "agent_type": "cast-controller",
            "session_id": SUBAGENT_SESSION,
            "claude_agent_id": "agent-A",
        },
    )
    open_r2 = env["client"].post(
        "/api/agents/subagent-invocations",
        json={
            "agent_type": "cast-service",
            "session_id": SUBAGENT_SESSION,
            "claude_agent_id": "agent-B",
        },
    )
    assert open_r1.status_code == 200 and open_r2.status_code == 200
    run_a = open_r1.json()["run_id"]
    run_b = open_r2.json()["run_id"]

    close_r = env["client"].post(
        "/api/agents/subagent-invocations/complete",
        json={"claude_agent_id": "agent-A"},
    )
    assert close_r.status_code == 200
    assert close_r.json() == {"closed": 1}

    row_a = _row(env["db_path"], run_a)
    row_b = _row(env["db_path"], run_b)
    assert row_a["status"] == "completed"
    assert row_a["completed_at"] is not None
    assert row_b["status"] == "running"

    # Unknown id → 200 + {"closed": 0} (FR-010 — never 4xx on miss).
    miss_r = env["client"].post(
        "/api/agents/subagent-invocations/complete",
        json={"claude_agent_id": "never-seen"},
    )
    assert miss_r.status_code == 200
    assert miss_r.json() == {"closed": 0}


def test_subagent_invocation_skill_endpoint(env):
    """POST /subagent-invocations/skill: ``skill`` (singular) lands on most-recent cast-* row."""
    # Slash-command parent so the skill has a cast-* row to attach to.
    open_r = env["client"].post(
        "/api/agents/user-invocations",
        json={
            "agent_name": "cast-plan-review",
            "prompt": "/cast-plan-review",
            "session_id": SUBAGENT_SESSION,
        },
    )
    assert open_r.status_code == 200
    parent_run_id = open_r.json()["run_id"]

    skill_r = env["client"].post(
        "/api/agents/subagent-invocations/skill",
        json={
            "session_id": SUBAGENT_SESSION,
            "skill": "landing-report",
            "invoked_at": "2026-05-01T12:00:00+00:00",
        },
    )
    assert skill_r.status_code == 200
    assert skill_r.json() == {"appended": 1}

    row = _row(env["db_path"], parent_run_id)
    skills = json.loads(row["skills_used"])
    assert skills == [
        {"name": "landing-report", "invoked_at": "2026-05-01T12:00:00+00:00"}
    ]

    # No candidate cast-* row in a different session → 200 + {"appended": 0}.
    miss_r = env["client"].post(
        "/api/agents/subagent-invocations/skill",
        json={"session_id": "session-empty", "skill": "anything"},
    )
    assert miss_r.status_code == 200
    assert miss_r.json() == {"appended": 0}
