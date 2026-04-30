"""Tests for `GET /api/agents/jobs/{run_id}` file-canonical read-through (sp5).

Covers all four branches of the precedence rule documented in
``cast-server/docs/runs-api.md``:

* file present + parseable → file wins (field-by-field merge)
* file missing            → DB-only with ``source: "db"``
* file malformed          → 502 with ``source: "file_invalid"``
* unknown run_id          → 404, no filesystem scan
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CAST_SERVER_DIR = REPO_ROOT / "cast-server"

if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))


@pytest.fixture
def env(monkeypatch, tmp_path):
    """Stub goals_dir + DB path so tests are hermetic (per T11 fix)."""
    pytest.importorskip("cast_server.config")

    goals_dir = tmp_path / "goals"
    goals_dir.mkdir()
    db_path = tmp_path / "test.db"

    from cast_server import config as _config
    monkeypatch.setattr(_config, "GOALS_DIR", goals_dir)
    monkeypatch.setattr(_config, "DB_PATH", db_path)

    from cast_server.db import connection as _connection
    monkeypatch.setattr(_connection, "DB_PATH", db_path)

    from cast_server.routes import api_agents
    monkeypatch.setattr(api_agents._config, "GOALS_DIR", goals_dir)

    # Force DB schema initialization on this fresh path.
    from cast_server.db.connection import init_db
    init_db(db_path)

    app = FastAPI()
    app.include_router(api_agents.router)
    return {
        "client": TestClient(app),
        "goals_dir": goals_dir,
        "db_path": db_path,
    }


def _insert_run(db_path: Path, run_id: str, goal_slug: str = "g1", **fields):
    """Insert an agent_runs row directly. Returns nothing."""
    import sqlite3

    # Ensure goal exists for FK referential integrity (FK is ON DELETE SET NULL,
    # so the row will still insert even without — but be explicit anyway).
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, status, created_at, folder_path) "
            "VALUES (?, ?, 'accepted', '2026-04-30T00:00:00+00:00', ?)",
            (goal_slug, goal_slug, goal_slug),
        )
        defaults = {
            "agent_name": "test-agent",
            "status": "running",
            "created_at": "2026-04-30T00:00:00+00:00",
            "started_at": "2026-04-30T00:00:01+00:00",
        }
        defaults.update(fields)
        cols = ["id", "goal_slug", *defaults.keys()]
        vals = [run_id, goal_slug, *defaults.values()]
        placeholders = ", ".join("?" for _ in cols)
        conn.execute(
            f"INSERT INTO agent_runs ({', '.join(cols)}) VALUES ({placeholders})",
            vals,
        )
        conn.commit()
    finally:
        conn.close()


def _plant_file(goals_dir: Path, goal_slug: str, run_id: str, payload):
    goal_dir = goals_dir / goal_slug
    goal_dir.mkdir(parents=True, exist_ok=True)
    out = goal_dir / f".agent-run_{run_id}.output.json"
    if isinstance(payload, str):
        out.write_text(payload, encoding="utf-8")
    else:
        out.write_text(json.dumps(payload), encoding="utf-8")
    return out


def test_file_present_wins(env):
    """File status overrides DB status; response carries source=file."""
    run_id = "run_test_file_present"
    _insert_run(env["db_path"], run_id, goal_slug="g1", status="running")
    _plant_file(env["goals_dir"], "g1", run_id, {
        "contract_version": "2",
        "agent_name": "test-agent",
        "status": "completed",
        "summary": "all done",
    })

    r = env["client"].get(f"/api/agents/jobs/{run_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "completed"
    assert body["source"] == "file"
    assert body["summary"] == "all done"


def test_file_missing_falls_back_to_db(env):
    """No file on disk → DB-only state with source=db."""
    run_id = "run_test_file_missing"
    _insert_run(env["db_path"], run_id, goal_slug="g1", status="running")

    r = env["client"].get(f"/api/agents/jobs/{run_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "db"
    assert body["status"] == "running"
    assert body["id"] == run_id


def test_file_malformed_returns_502(env):
    """Invalid JSON file → 502 with source=file_invalid and parse error in body."""
    run_id = "run_test_file_bad"
    _insert_run(env["db_path"], run_id, goal_slug="g1", status="running")
    _plant_file(env["goals_dir"], "g1", run_id, "{not: valid json,,,")

    r = env["client"].get(f"/api/agents/jobs/{run_id}")
    assert r.status_code == 502
    body = r.json()
    assert body["source"] == "file_invalid"
    assert body["run_id"] == run_id
    assert "Malformed output file" in body["error"]
    # DB fallback state is included for debugging.
    assert body["db_state"]["status"] == "running"


def test_unknown_run_id_returns_404(env):
    """No DB row, no file → 404. Server-dispatched-only carve-out (Q#17/A3)."""
    # Plant a file under some goal — confirm the API does NOT scan for it.
    _plant_file(env["goals_dir"], "g1", "run_orphan_file", {"status": "completed"})

    r = env["client"].get("/api/agents/jobs/run_orphan_file")
    assert r.status_code == 404
    body = r.json()
    assert "Unknown run_id" in body["detail"]


def test_field_merge_preserves_db_only_fields(env):
    """File supplies status+summary; DB-only fields (created_at, agent_name) survive."""
    run_id = "run_test_merge"
    _insert_run(
        env["db_path"], run_id, goal_slug="g1",
        status="running",
        agent_name="db-agent",
        created_at="2026-04-30T01:23:45+00:00",
    )
    _plant_file(env["goals_dir"], "g1", run_id, {
        "status": "completed",
        "summary": "wrapped up",
    })

    r = env["client"].get(f"/api/agents/jobs/{run_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "file"
    assert body["status"] == "completed"        # file wins
    assert body["summary"] == "wrapped up"      # file-only field present
    assert body["created_at"] == "2026-04-30T01:23:45+00:00"  # DB fills gap
    assert body["agent_name"] == "db-agent"     # DB fills gap (file omitted)
