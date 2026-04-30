"""Tests for the dispatch precondition: every trigger requires a usable
``external_project_dir`` on the goal.

Covers:

* ``_validate_dispatch_preconditions`` raises ``MissingExternalProjectDirError``
  when the goal lacks an ``external_project_dir`` or the configured path is
  not a directory on disk; passes when the path exists.
* ``trigger_agent`` propagates the error before enqueueing a run (no DB row
  is created on rejection).
* ``POST /api/agents/{name}/trigger`` maps the error to **HTTP 422** with the
  structured payload the ``cast-child-delegation`` skill consumes
  (``error_code``, ``goal_slug``, ``configured_path``, ``hint``).
* ``_launch_agent`` raises the same error if it ever runs without an
  ``external_project_dir`` — defense-in-depth against an unenforced path.
"""

from __future__ import annotations

import asyncio
import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CAST_SERVER_DIR = REPO_ROOT / "cast-server"
if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))


def _insert_goal(db_path: Path, slug: str, external_project_dir: str | None) -> None:
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute(
            "INSERT OR REPLACE INTO goals "
            "(slug, title, status, created_at, folder_path, external_project_dir) "
            "VALUES (?, ?, 'accepted', '2026-04-30T00:00:00+00:00', ?, ?)",
            (slug, slug, slug, external_project_dir),
        )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def env(monkeypatch, tmp_path):
    """Hermetic env: fresh DB + goals dir wired into config and routes."""
    pytest.importorskip("cast_server.config")

    goals_dir = tmp_path / "goals"
    goals_dir.mkdir()
    db_path = tmp_path / "test.db"

    from cast_server import config as _config
    monkeypatch.setattr(_config, "DB_PATH", db_path)
    monkeypatch.setattr(_config, "GOALS_DIR", goals_dir)

    from cast_server.db import connection as _connection
    monkeypatch.setattr(_connection, "DB_PATH", db_path)

    from cast_server.routes import api_agents
    monkeypatch.setattr(api_agents._config, "GOALS_DIR", goals_dir)

    from cast_server.db.connection import init_db
    init_db(db_path)

    app = FastAPI()
    app.include_router(api_agents.router)
    return {"client": TestClient(app), "db_path": db_path, "tmp_path": tmp_path}


# ---------------------------------------------------------------------------
# _validate_dispatch_preconditions — direct unit coverage
# ---------------------------------------------------------------------------

def test_validate_raises_when_goal_has_no_external_project_dir(env):
    from cast_server.services.agent_service import (
        MissingExternalProjectDirError,
        _validate_dispatch_preconditions,
    )

    _insert_goal(env["db_path"], "no-ext-dir", external_project_dir=None)

    with pytest.raises(MissingExternalProjectDirError) as exc:
        _validate_dispatch_preconditions("no-ext-dir", db_path=env["db_path"])

    assert exc.value.goal_slug == "no-ext-dir"
    assert exc.value.configured_path is None


def test_validate_raises_when_external_project_dir_path_missing(env, tmp_path):
    from cast_server.services.agent_service import (
        MissingExternalProjectDirError,
        _validate_dispatch_preconditions,
    )

    bogus = str(tmp_path / "does-not-exist")
    _insert_goal(env["db_path"], "bad-ext-dir", external_project_dir=bogus)

    with pytest.raises(MissingExternalProjectDirError) as exc:
        _validate_dispatch_preconditions("bad-ext-dir", db_path=env["db_path"])

    assert exc.value.goal_slug == "bad-ext-dir"
    assert exc.value.configured_path == bogus


def test_validate_passes_when_external_project_dir_exists(env, tmp_path):
    from cast_server.services.agent_service import _validate_dispatch_preconditions

    real_dir = tmp_path / "real-project"
    real_dir.mkdir()
    _insert_goal(env["db_path"], "good-goal", external_project_dir=str(real_dir))

    _validate_dispatch_preconditions("good-goal", db_path=env["db_path"])


# ---------------------------------------------------------------------------
# trigger_agent — service-layer behaviour
# ---------------------------------------------------------------------------

def test_trigger_agent_raises_before_enqueue_when_precondition_fails(env):
    from cast_server.services import agent_service
    from cast_server.services.agent_service import MissingExternalProjectDirError

    _insert_goal(env["db_path"], "blocked", external_project_dir=None)

    async def go():
        await agent_service.trigger_agent(
            agent_name="cast-create-execution-plan",
            goal_slug="blocked",
            db_path=env["db_path"],
        )

    with pytest.raises(MissingExternalProjectDirError):
        asyncio.run(go())

    # No agent_runs row was created — precondition fires before enqueue.
    conn = sqlite3.connect(str(env["db_path"]))
    try:
        rows = conn.execute(
            "SELECT COUNT(*) FROM agent_runs WHERE goal_slug = ?", ("blocked",)
        ).fetchone()
        assert rows[0] == 0
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Route layer — 422 contract the skill consumes
# ---------------------------------------------------------------------------

def test_trigger_route_returns_422_with_structured_payload(env):
    _insert_goal(env["db_path"], "blocked-route", external_project_dir=None)

    resp = env["client"].post(
        "/api/agents/cast-create-execution-plan/trigger",
        json={"goal_slug": "blocked-route"},
    )

    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["error_code"] == "missing_external_project_dir"
    assert body["goal_slug"] == "blocked-route"
    assert body["configured_path"] is None
    assert "external_project_dir" in body["hint"]
    assert "detail" in body


def test_trigger_route_returns_422_when_path_missing(env, tmp_path):
    bogus = str(tmp_path / "ghost-project")
    _insert_goal(env["db_path"], "bad-path-route", external_project_dir=bogus)

    resp = env["client"].post(
        "/api/agents/cast-create-execution-plan/trigger",
        json={"goal_slug": "bad-path-route"},
    )

    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["error_code"] == "missing_external_project_dir"
    assert body["configured_path"] == bogus


def test_trigger_route_succeeds_when_external_project_dir_set(env, tmp_path):
    real_dir = tmp_path / "happy-project"
    real_dir.mkdir()
    _insert_goal(env["db_path"], "happy", external_project_dir=str(real_dir))

    resp = env["client"].post(
        "/api/agents/cast-create-execution-plan/trigger",
        json={"goal_slug": "happy"},
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "pending"


# ---------------------------------------------------------------------------
# _launch_agent — defense in depth
# ---------------------------------------------------------------------------

def test_launch_agent_raises_when_external_project_dir_unset(env, monkeypatch):
    """If anything bypasses the trigger contract (scheduled run, direct DB
    insert), the launcher refuses to fall back to a default cwd and raises
    explicitly. Mirrors the trigger-time contract."""
    from cast_server.services import agent_service
    from cast_server.services.agent_service import MissingExternalProjectDirError

    _insert_goal(env["db_path"], "leak-goal", external_project_dir=None)

    # Insert a pending run directly (skipping trigger_agent's precondition).
    conn = sqlite3.connect(str(env["db_path"]))
    try:
        conn.execute(
            "INSERT INTO agent_runs (id, agent_name, goal_slug, status, created_at) "
            "VALUES (?, ?, ?, 'pending', '2026-04-30T00:00:00+00:00')",
            ("leak-run", "cast-create-execution-plan", "leak-goal"),
        )
        conn.commit()
    finally:
        conn.close()

    # Stub tmux so we can run _launch_agent without real subprocess work.
    from unittest.mock import MagicMock
    monkeypatch.setattr(agent_service, "_get_tmux", lambda: MagicMock())

    async def go():
        await agent_service._launch_agent("leak-run", db_path=env["db_path"])

    # _launch_agent wraps exceptions and marks the run as failed; verify the
    # run was NOT marked 'running' and an error was recorded.
    asyncio.run(go())

    conn = sqlite3.connect(str(env["db_path"]))
    try:
        row = conn.execute(
            "SELECT status, error_message FROM agent_runs WHERE id = 'leak-run'"
        ).fetchone()
    finally:
        conn.close()

    assert row[0] == "failed"
    assert "external_project_dir" in (row[1] or "")


# ---------------------------------------------------------------------------
# delegation_context shape — output_dir default + 422 envelope
# ---------------------------------------------------------------------------

def _delegation_payload(**output_overrides):
    """Minimal valid delegation_context with overrideable output block."""
    return {
        "agent_name": "cast-create-execution-plan",
        "instructions": "stub",
        "context": {"goal_title": "stub"},
        "output": {"expected_artifacts": ["x.md"], **output_overrides},
    }


def _stub_trigger(monkeypatch, captured):
    """Replace agent_service.trigger_agent with a capturing async stub.

    Returns the (intercepted) DelegationContext argument via ``captured`` so
    the test can assert on what the route built and forwarded — without
    requiring the goal_dir to exist on disk for the file write at line 1486.
    """
    from cast_server.routes import api_agents

    async def _capture(agent_name, **kwargs):
        captured["agent_name"] = agent_name
        captured["delegation_context"] = kwargs.get("delegation_context")
        return "stub-run-id"

    monkeypatch.setattr(api_agents.agent_service, "trigger_agent", _capture)


def test_trigger_defaults_output_dir_to_goal_dir(env, tmp_path, monkeypatch):
    """When delegation_context.output omits output_dir, the server backfills
    GOALS_DIR/<slug> before constructing the pydantic model."""
    real_dir = tmp_path / "proj-default-out"
    real_dir.mkdir()
    _insert_goal(env["db_path"], "default-out", external_project_dir=str(real_dir))

    captured: dict = {}
    _stub_trigger(monkeypatch, captured)

    resp = env["client"].post(
        "/api/agents/cast-create-execution-plan/trigger",
        json={
            "goal_slug": "default-out",
            "delegation_context": _delegation_payload(),  # no output_dir
        },
    )

    assert resp.status_code == 200, resp.text

    from cast_server.routes import api_agents
    expected = str(api_agents._config.GOALS_DIR / "default-out")

    delegation_context = captured["delegation_context"]
    assert delegation_context is not None
    assert delegation_context.output.output_dir == expected


def test_trigger_returns_422_on_malformed_delegation_context(env, tmp_path):
    """Missing required fields (no instructions, no context) → 422 envelope
    with error_code='invalid_delegation_context' and a non-empty errors list."""
    real_dir = tmp_path / "proj-malformed"
    real_dir.mkdir()
    _insert_goal(env["db_path"], "malformed", external_project_dir=str(real_dir))

    resp = env["client"].post(
        "/api/agents/cast-create-execution-plan/trigger",
        json={
            "goal_slug": "malformed",
            "delegation_context": {"agent_name": "cast-create-execution-plan"},
        },
    )

    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["error_code"] == "invalid_delegation_context"
    assert body["detail"] == "delegation_context failed validation"
    assert isinstance(body.get("errors"), list) and body["errors"], body
    assert "cast-delegation-contract" in body["hint"]


def test_trigger_preserves_explicit_output_dir(env, tmp_path, monkeypatch):
    """Regression: an explicit output_dir must NOT be clobbered by the
    setdefault default. Locks down semantics so a future refactor replacing
    setdefault with hard assignment fails this test."""
    real_dir = tmp_path / "proj-explicit"
    real_dir.mkdir()
    _insert_goal(env["db_path"], "explicit-out", external_project_dir=str(real_dir))

    captured: dict = {}
    _stub_trigger(monkeypatch, captured)

    explicit = "/some/explicit/path"
    resp = env["client"].post(
        "/api/agents/cast-create-execution-plan/trigger",
        json={
            "goal_slug": "explicit-out",
            "delegation_context": _delegation_payload(output_dir=explicit),
        },
    )

    assert resp.status_code == 200, resp.text
    delegation_context = captured["delegation_context"]
    assert delegation_context is not None
    assert delegation_context.output.output_dir == explicit
