"""Workflow-routing persistence plumbing — Phase 3b sp1b (Work Package C).

Covers the three contracts of sp1b in one file:

* The canonical schema exposes ``workflow_family`` / ``routing_handle`` /
  ``routed_at`` on a freshly-initialised ``goals`` table.
* ``_run_migrations`` adds the columns to a *legacy* goals table that predates
  them, and is idempotent (a second run must not raise).
* ``_write_goal_yaml`` renders all three fields when present and omits them
  entirely when absent (the conditional-include contract — no stray keys).

sp1b deliberately writes NO routing *values*; it only makes the columns exist
and renderable. Asserting a recorded value is sp2's job, so these tests pass
the fields in by hand rather than through ``record_routing_decision``.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from cast_server.db.connection import _run_migrations, get_connection, init_db
from cast_server.services.goal_service import _write_goal_yaml

ROUTING_COLUMNS = ["workflow_family", "routing_handle", "routed_at"]


def _columns(db_path: Path, table: str) -> set[str]:
    conn = get_connection(db_path)
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    finally:
        conn.close()
    return {row["name"] for row in rows}


# ---------------------------------------------------------------------------
# Fresh-DB schema
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("column", ROUTING_COLUMNS)
def test_fresh_db_exposes_routing_column(isolated_db: Path, column: str) -> None:
    assert column in _columns(isolated_db, "goals")


# ---------------------------------------------------------------------------
# Legacy-DB migration + idempotency
# ---------------------------------------------------------------------------

def _legacy_goals_db(db_path: Path) -> None:
    """Build a full current-schema DB, then drop the Phase 3b routing columns
    to faithfully simulate a pre-3b database that ``_run_migrations`` self-heals
    on next open. Dropping (vs. hand-rolling a partial schema) keeps every other
    table the migration touches intact.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        for column in ROUTING_COLUMNS:
            conn.execute(f"ALTER TABLE goals DROP COLUMN {column}")
        conn.commit()
    finally:
        conn.close()


def test_migration_adds_routing_columns_to_legacy_db(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.db"
    _legacy_goals_db(db_path)
    assert not (set(ROUTING_COLUMNS) & _columns(db_path, "goals"))

    conn = get_connection(db_path)
    try:
        _run_migrations(conn)
    finally:
        conn.close()

    assert set(ROUTING_COLUMNS) <= _columns(db_path, "goals")


def test_migration_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.db"
    _legacy_goals_db(db_path)

    conn = get_connection(db_path)
    try:
        _run_migrations(conn)
        _run_migrations(conn)  # second run must not raise
    finally:
        conn.close()

    assert set(ROUTING_COLUMNS) <= _columns(db_path, "goals")


# ---------------------------------------------------------------------------
# goal.yaml render preservation
# ---------------------------------------------------------------------------

def _base_goal(**extra) -> dict:
    data = {
        "slug": "demo-goal",
        "title": "Demo Goal",
        "status": "idea",
        "phase": "requirements",
    }
    data.update(extra)
    return data


def test_write_goal_yaml_renders_routing_fields_when_present(tmp_path: Path) -> None:
    goal_dir = tmp_path
    _write_goal_yaml(
        goal_dir,
        _base_goal(
            workflow_family="bug_fix",
            routing_handle="bug_fix:stub",
            routed_at="2026-06-11T21:00:00+00:00",
        ),
    )

    rendered = yaml.safe_load((goal_dir / "goal.yaml").read_text())
    assert rendered["workflow_family"] == "bug_fix"
    assert rendered["routing_handle"] == "bug_fix:stub"
    assert rendered["routed_at"] == "2026-06-11T21:00:00+00:00"


def test_write_goal_yaml_omits_routing_fields_when_absent(tmp_path: Path) -> None:
    goal_dir = tmp_path
    _write_goal_yaml(goal_dir, _base_goal())

    rendered = yaml.safe_load((goal_dir / "goal.yaml").read_text())
    for column in ROUTING_COLUMNS:
        assert column not in rendered
