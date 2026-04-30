"""Tests for ``POST /api/tasks/{task_id}/run-agent`` precondition handling.

Mirrors ``tests/test_dispatch_precondition.py`` for the task-run route:
the route must surface ``MissingExternalProjectDirError`` as a structured
HTTP 422 (not a generic 500) so the UI can show an actionable toast.
"""

from __future__ import annotations

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


def _insert_task(db_path: Path, goal_slug: str, agent_name: str) -> int:
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        cur = conn.execute(
            "INSERT INTO tasks (goal_slug, title, status, recommended_agent) "
            "VALUES (?, ?, 'pending', ?)",
            (goal_slug, "Refine requirements writeup", agent_name),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


@pytest.fixture
def env(monkeypatch, tmp_path):
    """Hermetic env: fresh DB + goals dir wired into config and the task router."""
    pytest.importorskip("cast_server.config")

    goals_dir = tmp_path / "goals"
    goals_dir.mkdir()
    db_path = tmp_path / "test.db"

    from cast_server import config as _config
    monkeypatch.setattr(_config, "DB_PATH", db_path)
    monkeypatch.setattr(_config, "GOALS_DIR", goals_dir)

    from cast_server.db import connection as _connection
    monkeypatch.setattr(_connection, "DB_PATH", db_path)

    from cast_server.routes import api_tasks
    monkeypatch.setattr(api_tasks, "GOALS_DIR", goals_dir)

    from cast_server.db.connection import init_db
    init_db(db_path)

    app = FastAPI()
    app.include_router(api_tasks.router)
    return {"client": TestClient(app), "db_path": db_path, "tmp_path": tmp_path}


def test_run_agent_route_returns_422_when_external_project_dir_unset(env):
    _insert_goal(env["db_path"], "blocked", external_project_dir=None)
    task_id = _insert_task(env["db_path"], "blocked", "cast-refine-requirements")

    resp = env["client"].post(f"/api/tasks/{task_id}/run-agent")

    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["error_code"] == "missing_external_project_dir"
    assert body["goal_slug"] == "blocked"
    assert body["configured_path"] is None
    # Detail is actionable — points the user at the inline form on the page.
    assert "project directory" in body["detail"].lower()
    assert "top of this page" in body["hint"].lower()

    # No agent_runs row was created — precondition fires before enqueue.
    conn = sqlite3.connect(str(env["db_path"]))
    try:
        rows = conn.execute(
            "SELECT COUNT(*) FROM agent_runs WHERE goal_slug = ?", ("blocked",)
        ).fetchone()
        assert rows[0] == 0
    finally:
        conn.close()


def test_run_agent_route_returns_422_when_path_missing(env, tmp_path):
    bogus = str(tmp_path / "ghost-project")
    _insert_goal(env["db_path"], "bad-path", external_project_dir=bogus)
    task_id = _insert_task(env["db_path"], "bad-path", "cast-refine-requirements")

    resp = env["client"].post(f"/api/tasks/{task_id}/run-agent")

    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["error_code"] == "missing_external_project_dir"
    assert body["configured_path"] == bogus


def test_run_agent_route_400_when_task_has_no_recommended_agent(env):
    """Existing contract — task without a recommended_agent should 400, not 500."""
    _insert_goal(env["db_path"], "no-agent", external_project_dir=None)
    conn = sqlite3.connect(str(env["db_path"]))
    try:
        cur = conn.execute(
            "INSERT INTO tasks (goal_slug, title, status) VALUES (?, ?, 'pending')",
            ("no-agent", "manual task"),
        )
        conn.commit()
        task_id = int(cur.lastrowid)
    finally:
        conn.close()

    resp = env["client"].post(f"/api/tasks/{task_id}/run-agent")
    assert resp.status_code == 400, resp.text
