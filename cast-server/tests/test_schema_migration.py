"""Migration cluster — consolidated (Plan-review decision 2).

Covers, in one file, every contract of sp1's schema migration:

* Both new columns (``skills_used`` default ``'[]'`` and ``claude_agent_id``)
  exist on a freshly-initialised DB.
* The new partial index ``idx_agent_runs_claude_agent_id`` exists.
* The pre-existing composite ``idx_agent_runs_session_status`` is untouched
  (no single-column ``idx_agent_runs_session_id`` is introduced).
* ``_run_migrations`` is idempotent against a DB that already has the new
  shape (the live-DB path) — the second call must not raise.
* ``_seed_system_goals`` is idempotent under fresh / pre-existing-DB /
  pre-existing-goal cases (``test_system_ops_seed_idempotent``).
* ``get_connection`` rejects SQLite < 3.9 with ``SystemExit``
  (``test_sqlite_version_check_rejects_old_versions``).

Tests reuse the shared ``isolated_db`` fixture; we do NOT fork new
in-memory DB scaffolding (Plan-review decision 4).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from cast_server.db import connection as db_connection
from cast_server.db.connection import (
    _run_migrations,
    _seed_system_goals,
    get_connection,
    init_db,
)


def _columns(db_path: Path, table: str) -> set[str]:
    conn = get_connection(db_path)
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    finally:
        conn.close()
    return {row["name"] for row in rows}


def _index_names(db_path: Path, table: str) -> set[str]:
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name = ?",
            (table,),
        ).fetchall()
    finally:
        conn.close()
    return {row["name"] for row in rows}


# ---------------------------------------------------------------------------
# Schema columns + indexes (fresh DB)
# ---------------------------------------------------------------------------

def test_skills_used_column_present_with_default(isolated_db: Path) -> None:
    cols = _columns(isolated_db, "agent_runs")
    assert "skills_used" in cols

    # Default literal is `'[]'`.
    conn = get_connection(isolated_db)
    try:
        rows = conn.execute("PRAGMA table_info(agent_runs)").fetchall()
    finally:
        conn.close()
    skills_row = next(r for r in rows if r["name"] == "skills_used")
    assert skills_row["dflt_value"] == "'[]'"


def test_claude_agent_id_column_present(isolated_db: Path) -> None:
    cols = _columns(isolated_db, "agent_runs")
    assert "claude_agent_id" in cols


def test_partial_index_for_claude_agent_id_present(isolated_db: Path) -> None:
    indexes = _index_names(isolated_db, "agent_runs")
    assert "idx_agent_runs_claude_agent_id" in indexes


def test_composite_session_status_index_intact(isolated_db: Path) -> None:
    indexes = _index_names(isolated_db, "agent_runs")
    assert "idx_agent_runs_session_status" in indexes


def test_no_single_column_session_id_index(isolated_db: Path) -> None:
    """Plan-review decision 11: composite index already covers session lookups;
    sp1 must NOT add a single-column ``idx_agent_runs_session_id``.
    """
    indexes = _index_names(isolated_db, "agent_runs")
    assert "idx_agent_runs_session_id" not in indexes


# ---------------------------------------------------------------------------
# Live-DB / re-migration idempotency
# ---------------------------------------------------------------------------

def test_run_migrations_idempotent_on_pre_existing_db(isolated_db: Path) -> None:
    """Re-running ``_run_migrations`` against a DB that already has the new
    columns + index must not raise. This is the contract the live cast-server
    DB hits on every startup once sp1 has shipped.
    """
    conn = get_connection(isolated_db)
    try:
        # First call already happened in the fixture's init_db().
        # A second call should be a silent no-op for the ALTERs and a
        # CREATE INDEX IF NOT EXISTS for the partial index.
        _run_migrations(conn)
        _run_migrations(conn)  # belt-and-braces
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# system-ops seed idempotency (test_system_ops_seed_idempotent)
# ---------------------------------------------------------------------------

def _goal_count(db_path: Path, slug: str) -> int:
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM goals WHERE slug = ?", (slug,)
        ).fetchone()
    finally:
        conn.close()
    return row["c"]


def test_system_ops_seed_idempotent_fresh_db(isolated_db: Path) -> None:
    # init_db already ran _run_migrations once.
    assert _goal_count(isolated_db, "system-ops") == 1


def test_system_ops_seed_idempotent_preexisting_db_without_goal(tmp_path, monkeypatch) -> None:
    """Pre-existing DB that somehow lacks the goal — seed must add it cleanly."""
    db_path = tmp_path / "preexisting.db"

    from cast_server import config as cast_config
    monkeypatch.setattr(cast_config, "DB_PATH", db_path)

    # Bring the DB into existence with schema only — then nuke the seed row.
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        conn.execute("DELETE FROM goals WHERE slug = 'system-ops'")
        conn.commit()
        assert _goal_count(db_path, "system-ops") == 0

        # Re-seed.
        _seed_system_goals(conn)
    finally:
        conn.close()

    assert _goal_count(db_path, "system-ops") == 1


def test_system_ops_seed_idempotent_preexisting_goal(isolated_db: Path) -> None:
    """Calling _seed_system_goals when the goal already exists is a no-op."""
    assert _goal_count(isolated_db, "system-ops") == 1
    conn = get_connection(isolated_db)
    try:
        _seed_system_goals(conn)
        _seed_system_goals(conn)
    finally:
        conn.close()
    assert _goal_count(isolated_db, "system-ops") == 1


# ---------------------------------------------------------------------------
# SQLite 3.9+ startup check (test_sqlite_version_check_rejects_old_versions)
# ---------------------------------------------------------------------------

def test_sqlite_version_check_rejects_old_versions(tmp_path, monkeypatch) -> None:
    """``get_connection`` must SystemExit on SQLite < 3.9.

    record_skill (sp2) relies on ``json_insert(... '$[#]' ...)`` which
    landed in 3.9. The floor is a contract — we fail loud at startup so a
    deployment surprise happens once, not once per skill invocation.
    """
    monkeypatch.setattr(db_connection.sqlite3, "sqlite_version_info", (3, 8, 0))
    monkeypatch.setattr(db_connection.sqlite3, "sqlite_version", "3.8.0")

    with pytest.raises(SystemExit) as excinfo:
        get_connection(tmp_path / "version_check.db")

    assert "3.9" in str(excinfo.value)


def test_sqlite_version_check_accepts_modern_versions(isolated_db: Path) -> None:
    """Sanity check: the floor doesn't reject the actually-installed sqlite."""
    assert sqlite3.sqlite_version_info >= (3, 9, 0)
    # The fixture already opened a connection — no SystemExit raised.
