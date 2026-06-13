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


# ---------------------------------------------------------------------------
# Requirements thin spine (refine-requirements-v2 Phase 1, sp2b)
# ---------------------------------------------------------------------------

_SPINE_TABLES = ("requirement_versions", "requirement_comments", "comment_events")
_SPINE_INDEXES = (
    "idx_req_versions_goal_status",
    "idx_req_comments_goal_state",
    "idx_comment_events_comment",
)


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def _index_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name=?", (name,)
    ).fetchone()
    return row is not None


def test_thin_spine_tables_present_on_fresh_db(isolated_db: Path) -> None:
    """Fresh ``init_db()`` (run by the fixture) materialises all three
    thin-spine tables via ``schema.sql``.
    """
    conn = get_connection(isolated_db)
    try:
        for table in _SPINE_TABLES:
            assert _table_exists(conn, table), f"missing table {table}"
    finally:
        conn.close()


def test_thin_spine_indexes_present_on_fresh_db(isolated_db: Path) -> None:
    """The three perf indexes ship alongside the tables."""
    conn = get_connection(isolated_db)
    try:
        for index in _SPINE_INDEXES:
            assert _index_exists(conn, index), f"missing index {index}"
    finally:
        conn.close()


def test_requirement_comments_render_anchor_columns_present_on_fresh_db(
    isolated_db: Path,
) -> None:
    """refine-req-v3 sp2: a fresh DB carries the two render-anchor columns. ``anchor_space``
    is NOT NULL DEFAULT 'source'; ``block_ref`` is nullable (cross-boundary / ref-less = NULL)."""
    conn = get_connection(isolated_db)
    try:
        rows = conn.execute("PRAGMA table_info(requirement_comments)").fetchall()
    finally:
        conn.close()
    by_name = {r["name"]: r for r in rows}
    assert "block_ref" in by_name
    assert "anchor_space" in by_name
    # block_ref is nullable; anchor_space is NOT NULL with the source default.
    assert by_name["block_ref"]["notnull"] == 0
    assert by_name["anchor_space"]["notnull"] == 1
    assert by_name["anchor_space"]["dflt_value"] in ("'source'", "source")


def test_requirement_comments_render_anchor_columns_added_to_pre_v3_db(
    isolated_db: Path,
) -> None:
    """A requirement_comments that predates the render-anchor columns gets them added additively;
    a pre-existing row reads back the back-compatible default (anchor_space='source', block_ref
    NULL) and survives — no row rewrites, idempotent on a second migration."""
    conn = get_connection(isolated_db)
    try:
        # Simulate a pre-v3 requirement_comments (no block_ref / anchor_space columns).
        conn.execute("DROP TABLE IF EXISTS comment_events")
        conn.execute("DROP TABLE IF EXISTS requirement_comments")
        conn.execute(
            "CREATE TABLE requirement_comments ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT, goal_slug TEXT NOT NULL, version INTEGER NOT NULL,"
            " quoted_text TEXT NOT NULL, section_hint TEXT, body TEXT NOT NULL,"
            " state TEXT NOT NULL DEFAULT 'open', author TEXT NOT NULL,"
            " author_kind TEXT NOT NULL DEFAULT 'human', created_at TEXT NOT NULL, updated_at TEXT)"
        )
        conn.execute(
            "INSERT INTO requirement_comments "
            "(goal_slug, version, quoted_text, body, state, author, author_kind, created_at) "
            "VALUES ('g', 1, 'an old quote', 'body', 'open', 'alice', 'human', "
            "'2026-06-12T00:00:00+00:00')"
        )
        conn.commit()
        pre_cols = {r["name"] for r in conn.execute(
            "PRAGMA table_info(requirement_comments)").fetchall()}
        assert "block_ref" not in pre_cols and "anchor_space" not in pre_cols

        _run_migrations(conn)
        _run_migrations(conn)  # idempotency: second run must not raise

        cols = {r["name"] for r in conn.execute(
            "PRAGMA table_info(requirement_comments)").fetchall()}
        assert {"block_ref", "anchor_space"} <= cols

        # The pre-existing row survives and reads the back-compat default.
        row = conn.execute(
            "SELECT * FROM requirement_comments WHERE quoted_text = 'an old quote'"
        ).fetchone()
        assert row["anchor_space"] == "source"
        assert row["block_ref"] is None
    finally:
        conn.close()


def test_thin_spine_tables_present_after_migration_on_pre_existing_db(
    isolated_db: Path,
) -> None:
    """The migration path (``_run_migrations``) creates the tables on a
    pre-existing DB, and re-running it is a safe idempotent no-op.

    Mirrors ``test_run_migrations_idempotent_on_pre_existing_db``: we drop the
    spine tables to simulate an older DB that predates this migration, then
    prove ``_run_migrations`` brings them back and a second call does not raise.
    """
    conn = get_connection(isolated_db)
    try:
        # Simulate a DB created before this migration shipped.
        conn.execute("DROP TABLE IF EXISTS comment_events")
        conn.execute("DROP TABLE IF EXISTS requirement_comments")
        conn.execute("DROP TABLE IF EXISTS requirement_versions")
        conn.commit()
        for table in _SPINE_TABLES:
            assert not _table_exists(conn, table)

        _run_migrations(conn)
        _run_migrations(conn)  # idempotency: second run must not raise

        for table in _SPINE_TABLES:
            assert _table_exists(conn, table), f"migration did not create {table}"
        for index in _SPINE_INDEXES:
            assert _index_exists(conn, index), f"migration did not create {index}"
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Round-trip write-back proposal spine (refine-requirements-v2 Phase 5, sp1)
# ---------------------------------------------------------------------------

_WRITEBACK_TABLES = ("change_requests", "change_request_events", "notifications_outbox")
_WRITEBACK_INDEXES = (
    "idx_change_requests_goal_status",
    "idx_change_request_events_cr",
    "idx_notifications_outbox_status",
)


def test_writeback_tables_present_on_fresh_db(isolated_db: Path) -> None:
    """Fresh ``init_db()`` materialises all three Phase 5 proposal-spine tables
    via ``schema.sql``.
    """
    conn = get_connection(isolated_db)
    try:
        for table in _WRITEBACK_TABLES:
            assert _table_exists(conn, table), f"missing table {table}"
    finally:
        conn.close()


def test_writeback_indexes_present_on_fresh_db(isolated_db: Path) -> None:
    """The three Phase 5 perf indexes ship alongside the tables."""
    conn = get_connection(isolated_db)
    try:
        for index in _WRITEBACK_INDEXES:
            assert _index_exists(conn, index), f"missing index {index}"
    finally:
        conn.close()


def test_change_requests_author_type_check_enforced(isolated_db: Path) -> None:
    """``author_type`` is a ``CHECK (... IN ('human','agent'))`` enum — DATA, never a
    code branch (FR-013). A value outside the enum must be rejected by SQLite, and a
    valid value must insert. ``PRAGMA foreign_keys=ON`` is set by ``get_connection``,
    so we seed the FK target goal first.
    """
    conn = get_connection(isolated_db)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) "
            "VALUES ('wb-goal', 'Writeback Goal', 'wb-goal')"
        )
        conn.commit()

        def _insert(author_type: str) -> None:
            conn.execute(
                "INSERT INTO change_requests "
                "(goal_slug, proposed_body, kind, author, author_type, created_at) "
                "VALUES ('wb-goal', 'body', 'addition', 'someone', ?, '2026-06-12T00:00:00Z')",
                (author_type,),
            )
            conn.commit()

        # Out-of-enum value is rejected by the CHECK constraint.
        with pytest.raises(sqlite3.IntegrityError):
            _insert("robot")

        # Both legal members insert cleanly.
        _insert("human")
        _insert("agent")
        expected_count = 2
        actual_count = conn.execute(
            "SELECT COUNT(*) AS c FROM change_requests WHERE goal_slug = 'wb-goal'"
        ).fetchone()["c"]
        assert actual_count == expected_count
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Background maker render-job pipeline (refine-requirements-v3 Phase 3c)
# ---------------------------------------------------------------------------

_RENDER_JOB_INDEXES = ("idx_render_jobs_goal_hash", "idx_render_jobs_status")
# revision (a): heartbeat_at ships in the INITIAL create table, not a later migration.
_RENDER_JOB_COLUMNS = {
    "id", "goal_slug", "source_hash", "status", "attempts", "error",
    "started_at", "finished_at", "heartbeat_at",
}
# 4a-2 adds exactly these four flag columns (the queryable/observability copy). heartbeat_at is NOT
# here — it already ships in Phase 3's CREATE TABLE (reconciliation C4).
_FLAG_4A_COLUMNS = {"human_review", "review_reason", "published_attempt", "published_score"}


def test_render_jobs_table_present_on_fresh_db(isolated_db: Path) -> None:
    conn = get_connection(isolated_db)
    try:
        assert _table_exists(conn, "render_jobs")
    finally:
        conn.close()


def test_render_jobs_has_heartbeat_in_initial_table(isolated_db: Path) -> None:
    """revision (a): heartbeat_at is in the create table on a fresh DB; 4a-2's four flag columns
    are now present too (added by the 4a-2 schema change)."""
    cols = _columns(isolated_db, "render_jobs")
    assert "heartbeat_at" in cols
    assert _RENDER_JOB_COLUMNS <= cols
    assert _FLAG_4A_COLUMNS <= cols, "4a-2's four flag columns must be present"


def test_render_jobs_flag_columns_present_on_fresh_db(isolated_db: Path) -> None:
    """4a-2 (C4): exactly the four flag columns are added. human_review defaults to 0; the rest are
    nullable. heartbeat_at is NOT re-added (it predates 4a-2)."""
    conn = get_connection(isolated_db)
    try:
        rows = conn.execute("PRAGMA table_info(render_jobs)").fetchall()
    finally:
        conn.close()
    by_name = {r["name"]: r for r in rows}
    assert _FLAG_4A_COLUMNS <= set(by_name)
    assert by_name["human_review"]["dflt_value"] in ("0", 0)
    assert by_name["human_review"]["notnull"] == 1
    # The nullable flag columns carry no NOT NULL constraint (additive / no row rewrites).
    for col in ("review_reason", "published_attempt", "published_score"):
        assert by_name[col]["notnull"] == 0


def test_render_jobs_mode_column_present_on_fresh_db(isolated_db: Path) -> None:
    """HOW-update-mode 3a: a fresh DB carries the nullable ``mode`` column (additive observability —
    the CREATE/UPDATE decision stamp). Old / pre-decision rows read NULL."""
    conn = get_connection(isolated_db)
    try:
        rows = conn.execute("PRAGMA table_info(render_jobs)").fetchall()
    finally:
        conn.close()
    by_name = {r["name"]: r for r in rows}
    assert "mode" in by_name, "render_jobs.mode column missing on a fresh DB"
    assert by_name["mode"]["notnull"] == 0, "mode must be nullable (old rows read NULL)"


def test_render_jobs_mode_column_added_to_pre_3a_db(isolated_db: Path) -> None:
    """A render_jobs that predates the ``mode`` column (a 4a-shape table: flag columns but no mode)
    gets ``mode`` added additively; a pre-existing row reads it back as NULL and survives — no row
    rewrites, idempotent on a second migration."""
    conn = get_connection(isolated_db)
    try:
        # Simulate a pre-3a render_jobs: 4a shape (flag columns present), NO mode column.
        conn.execute("DROP TABLE IF EXISTS render_jobs")
        conn.execute(
            "CREATE TABLE render_jobs ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT, goal_slug TEXT NOT NULL, source_hash TEXT NOT NULL,"
            " status TEXT NOT NULL DEFAULT 'running', attempts INTEGER NOT NULL DEFAULT 0, error TEXT,"
            " started_at TEXT, finished_at TEXT, heartbeat_at TEXT,"
            " human_review INTEGER NOT NULL DEFAULT 0, review_reason TEXT,"
            " published_attempt INTEGER, published_score REAL)"
        )
        conn.execute(
            "INSERT INTO render_jobs (goal_slug, source_hash, status, attempts, heartbeat_at) "
            "VALUES ('g', 'h0', 'published', 4, '2026-06-12T00:00:00+00:00')"
        )
        conn.commit()
        pre_cols = {r["name"] for r in conn.execute("PRAGMA table_info(render_jobs)").fetchall()}
        assert "mode" not in pre_cols

        _run_migrations(conn)
        _run_migrations(conn)  # idempotency: second run must not raise

        cols = {r["name"] for r in conn.execute("PRAGMA table_info(render_jobs)").fetchall()}
        assert "mode" in cols, "the mode column was not added by the migration"

        # The pre-existing row survives; mode defaults to NULL (no row rewrite).
        row = conn.execute("SELECT * FROM render_jobs WHERE source_hash = 'h0'").fetchone()
        assert row["status"] == "published" and row["attempts"] == 4
        assert row["mode"] is None
    finally:
        conn.close()


def test_render_jobs_indexes_present_on_fresh_db(isolated_db: Path) -> None:
    indexes = _index_names(isolated_db, "render_jobs")
    for index in _RENDER_JOB_INDEXES:
        assert index in indexes, f"missing index {index}"


def test_render_jobs_present_after_migration_on_pre_existing_db(isolated_db: Path) -> None:
    """The migration path creates render_jobs on a pre-existing DB, idempotently, with the flag
    columns present."""
    conn = get_connection(isolated_db)
    try:
        conn.execute("DROP TABLE IF EXISTS render_jobs")
        conn.commit()
        assert not _table_exists(conn, "render_jobs")

        _run_migrations(conn)
        _run_migrations(conn)  # idempotency: second run must not raise

        assert _table_exists(conn, "render_jobs")
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(render_jobs)").fetchall()}
        assert "heartbeat_at" in cols
        assert _FLAG_4A_COLUMNS <= cols
    finally:
        conn.close()


def test_render_jobs_flag_columns_added_to_pre_4a_db_without_data_loss(isolated_db: Path) -> None:
    """4a-2 migration on a DB whose render_jobs predates the flag columns: the four columns are
    ADDED additively (nullable/defaulted) and the pre-existing row is preserved — no row rewrites,
    and heartbeat_at is NOT re-added (it already existed)."""
    conn = get_connection(isolated_db)
    try:
        # Simulate a pre-4a render_jobs (Phase-3 shape: heartbeat_at, NO flag columns).
        conn.execute("DROP TABLE IF EXISTS render_jobs")
        conn.execute(
            "CREATE TABLE render_jobs ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT, goal_slug TEXT NOT NULL, source_hash TEXT NOT NULL,"
            " status TEXT NOT NULL DEFAULT 'running', attempts INTEGER NOT NULL DEFAULT 0, error TEXT,"
            " started_at TEXT, finished_at TEXT, heartbeat_at TEXT)"
        )
        conn.execute(
            "INSERT INTO render_jobs (goal_slug, source_hash, status, attempts, heartbeat_at) "
            "VALUES ('g', 'h0', 'published', 4, '2026-06-12T00:00:00+00:00')"
        )
        conn.commit()
        pre_cols = {r["name"] for r in conn.execute("PRAGMA table_info(render_jobs)").fetchall()}
        assert not (_FLAG_4A_COLUMNS & pre_cols)

        _run_migrations(conn)
        _run_migrations(conn)  # idempotency

        cols = {r["name"] for r in conn.execute("PRAGMA table_info(render_jobs)").fetchall()}
        assert _FLAG_4A_COLUMNS <= cols, "the four flag columns were not added"

        # The pre-existing row survives; new columns default sanely (human_review=0, rest NULL).
        row = conn.execute("SELECT * FROM render_jobs WHERE source_hash = 'h0'").fetchone()
        assert row["status"] == "published" and row["attempts"] == 4
        assert row["human_review"] == 0
        assert row["review_reason"] is None
        assert row["published_attempt"] is None
        assert row["published_score"] is None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Same-door version-diff narration (refine-requirements-v3 Phase 4b-3)
# ---------------------------------------------------------------------------

_NARRATION_INDEXES = ("idx_version_diff_narrations_goal",)
_NARRATION_COLUMNS = {
    "id", "goal_slug", "base_version", "head_version",
    "overview", "item_notes", "created_by", "created_at",
}


def test_version_diff_narrations_table_present_on_fresh_db(isolated_db: Path) -> None:
    conn = get_connection(isolated_db)
    try:
        assert _table_exists(conn, "version_diff_narrations")
    finally:
        conn.close()


def test_version_diff_narrations_columns_present_on_fresh_db(isolated_db: Path) -> None:
    cols = _columns(isolated_db, "version_diff_narrations")
    assert _NARRATION_COLUMNS <= cols


def test_version_diff_narrations_index_present_on_fresh_db(isolated_db: Path) -> None:
    indexes = _index_names(isolated_db, "version_diff_narrations")
    for index in _NARRATION_INDEXES:
        assert index in indexes, f"missing index {index}"


def test_version_diff_narrations_unique_on_goal_base_head(isolated_db: Path) -> None:
    """UNIQUE(goal_slug, base_version, head_version): a second insert on the same triple is
    rejected (the upsert key the service relies on for repost-replaces-never-duplicates)."""
    conn = get_connection(isolated_db)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) "
            "VALUES ('narr-goal', 'Narration Goal', 'narr-goal')"
        )
        conn.commit()

        def _insert() -> None:
            conn.execute(
                "INSERT INTO version_diff_narrations "
                "(goal_slug, base_version, head_version, overview, item_notes, created_by, created_at) "
                "VALUES ('narr-goal', 1, 2, 'ov', '[]', 'agent', '2026-06-12T00:00:00Z')"
            )
            conn.commit()

        _insert()
        with pytest.raises(sqlite3.IntegrityError):
            _insert()
    finally:
        conn.close()


def test_version_diff_narrations_present_after_migration_on_pre_existing_db(
    isolated_db: Path,
) -> None:
    """The migration path creates version_diff_narrations on a pre-existing DB, idempotently."""
    conn = get_connection(isolated_db)
    try:
        conn.execute("DROP TABLE IF EXISTS version_diff_narrations")
        conn.commit()
        assert not _table_exists(conn, "version_diff_narrations")

        _run_migrations(conn)
        _run_migrations(conn)  # idempotency: second run must not raise

        assert _table_exists(conn, "version_diff_narrations")
        cols = {row["name"] for row in conn.execute(
            "PRAGMA table_info(version_diff_narrations)"
        ).fetchall()}
        assert _NARRATION_COLUMNS <= cols
        for index in _NARRATION_INDEXES:
            assert _index_exists(conn, index), f"missing index {index}"
    finally:
        conn.close()


def test_writeback_tables_present_after_migration_on_pre_existing_db(
    isolated_db: Path,
) -> None:
    """The migration path (``_run_migrations``) creates the Phase 5 tables on a
    pre-existing DB that predates them, and re-running it is a safe idempotent no-op.

    Mirrors the thin-spine migration test: drop the Phase 5 tables to simulate an
    older DB, then prove ``_run_migrations`` brings back the tables + indexes and a
    second call does not raise.
    """
    conn = get_connection(isolated_db)
    try:
        # Simulate a DB created before Phase 5 shipped. Drop children before parent
        # (FKs reference change_requests).
        conn.execute("DROP TABLE IF EXISTS notifications_outbox")
        conn.execute("DROP TABLE IF EXISTS change_request_events")
        conn.execute("DROP TABLE IF EXISTS change_requests")
        conn.commit()
        for table in _WRITEBACK_TABLES:
            assert not _table_exists(conn, table)

        _run_migrations(conn)
        _run_migrations(conn)  # idempotency: second run must not raise

        for table in _WRITEBACK_TABLES:
            assert _table_exists(conn, table), f"migration did not create {table}"
        for index in _WRITEBACK_INDEXES:
            assert _index_exists(conn, index), f"migration did not create {index}"

        # The CHECK constraint survives the migration path too (not just fresh init).
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) "
            "VALUES ('wb-mig', 'WB Mig', 'wb-mig')"
        )
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO change_requests "
                "(goal_slug, proposed_body, kind, author, author_type, created_at) "
                "VALUES ('wb-mig', 'b', 'addition', 'x', 'robot', '2026-06-12T00:00:00Z')"
            )
    finally:
        conn.close()
