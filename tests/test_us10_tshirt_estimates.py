"""US10 — T-shirt CC-time estimates: end-to-end coverage.

Asserts the schema flip + Pydantic enum + migrator correctness. The
``cast-task-suggester`` end-to-end check is implemented as a static-prompt
audit (not a live agent run) — the live-agent path requires the cast-server
to be up, which Phase 3a doesn't ship. The audit catches the same regression
class (a prompt regression that re-introduces ``estimated_time``).
"""

from __future__ import annotations

import importlib.util
import sqlite3
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# bin/migrate-legacy-estimates.py — load by file path because the filename has
# a hyphen and bin/ is not a Python package.
_MIGRATOR_PATH = REPO_ROOT / "bin" / "migrate-legacy-estimates.py"
_spec = importlib.util.spec_from_file_location("migrate_legacy_estimates", _MIGRATOR_PATH)
assert _spec is not None and _spec.loader is not None
mle = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mle)


# Pydantic model lives in cast_server (installed via `pip install -e .`).


# ---------------------------------------------------------------------------
# 1. cast-task-suggester prompt audit
# ---------------------------------------------------------------------------


def test_us10_task_suggester_emits_estimate_size():
    """The suggester prompt must reference `estimate_size` and have zero
    `estimated_time` / `minutes` references in its body. (Live agent runs
    are gated on cast-server, which Phase 3a doesn't ship; this audit
    catches the same regression class — a prompt edit that re-introduces
    the legacy field.)
    """
    prompt = (REPO_ROOT / "agents" / "cast-task-suggester" / "cast-task-suggester.md").read_text()
    assert "estimate_size" in prompt, "prompt does not reference estimate_size"
    assert "estimated_time" not in prompt, "legacy estimated_time still in prompt"
    # The 30m/45m/60m vocabulary must be gone too.
    for legacy in ('"30m"', '"45m"', '"60m"'):
        assert legacy not in prompt, f"legacy effort token {legacy} still in prompt"
    # Calibration table must list all five canonical sizes.
    for size in ("XS", "S", "M", "L", "XL"):
        assert size in prompt, f"calibration table missing size {size}"


# ---------------------------------------------------------------------------
# 2. Pydantic enum acceptance / rejection
# ---------------------------------------------------------------------------


def test_us10_task_model_validates_enum():
    """Task model accepts canonical values; rejects junk like 'HUGE'."""
    from cast_server.models.task_v2 import Task

    t = Task(goal_slug="g", title="x", estimate_size="S")
    assert t.estimate_size == "S"

    with pytest.raises((ValueError, Exception)):  # pydantic.ValidationError subclass
        Task(goal_slug="g", title="x", estimate_size="HUGE")


# ---------------------------------------------------------------------------
# 3. Mapping table (legacy minutes → T-shirt)
# ---------------------------------------------------------------------------


def test_us10_minutes_to_size_mapping():
    """Per US10 mapping table."""
    assert mle.minutes_to_size(5) == "XS"
    assert mle.minutes_to_size(15) == "S"     # in [10, 30)
    assert mle.minutes_to_size(45) == "M"     # in [30, 90)
    assert mle.minutes_to_size(120) == "L"    # in [90, 180)
    assert mle.minutes_to_size(240) == "XL"
    assert mle.minutes_to_size(None) == "M"   # default

    # String-form ("30m"/"1h") used by the legacy source data.
    assert mle.time_str_to_size("30m") == "M"   # 30 → M (lower bound of M bucket)
    assert mle.time_str_to_size("60m") == "M"
    assert mle.time_str_to_size("1h") == "M"
    assert mle.time_str_to_size("2h") == "L"
    assert mle.time_str_to_size("3h") == "XL"
    assert mle.time_str_to_size("XS") == "XS"   # already canonical
    assert mle.time_str_to_size(None) == "M"
    assert mle.time_str_to_size("garbage") == "M"


# ---------------------------------------------------------------------------
# 4. YAML migrator is idempotent
# ---------------------------------------------------------------------------


def test_us10_yaml_migration_idempotent(tmp_path):
    yaml_path = tmp_path / "tasks.yaml"
    yaml_path.write_text(
        "tasks:\n"
        "  - title: foo\n"
        "    estimate_minutes: 20\n"
        "  - title: bar\n"
        "    estimated_time: 1h\n"
    )
    r1 = mle.migrate_yaml(yaml_path)
    r2 = mle.migrate_yaml(yaml_path)
    assert r1["migrated"] == 2
    assert r2["migrated"] == 0          # idempotent
    assert r2["skipped"] == 2

    # Resulting file must use the canonical field, not the legacy ones.
    text = yaml_path.read_text()
    assert "estimate_size:" in text
    assert "estimate_minutes:" not in text
    assert "estimated_time:" not in text


# ---------------------------------------------------------------------------
# 5. SQLite up-migration drops the legacy column and carries data
# ---------------------------------------------------------------------------


def test_us10_db_migration_drops_column_and_carries_data(tmp_path):
    db_path = tmp_path / "tasks.db"
    fixture = REPO_ROOT / "tests" / "fixtures" / "legacy_tasks_db.sqlite"
    db_path.write_bytes(fixture.read_bytes())

    mle.migrate_sqlite(db_path)

    conn = sqlite3.connect(db_path)
    try:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()}
        assert "estimate_size" in cols
        # SQLite DROP COLUMN requires >= 3.35; CI runs on 3.40+, so the
        # legacy column must be gone post-migration.
        sqlite_ver = tuple(int(x) for x in sqlite3.sqlite_version.split("."))
        if sqlite_ver >= (3, 35, 0):
            assert "estimate_minutes" not in cols, "legacy column should be dropped"

        # Every row carries a non-null estimate_size in the canonical set.
        rows = conn.execute(
            "SELECT title, estimate_size FROM tasks ORDER BY id"
        ).fetchall()
        assert len(rows) == 5
        sizes = [r[1] for r in rows]
        for size in sizes:
            assert size in ("XS", "S", "M", "L", "XL")
        # Spot-check a couple of mapped values from the fixture (5/20/60/120/250).
        assert sizes[0] == "XS"   # 5  → XS
        assert sizes[1] == "S"    # 20 → S
        assert sizes[2] == "M"    # 60 → M
        assert sizes[3] == "L"    # 120 → L
        assert sizes[4] == "XL"   # 250 → XL
    finally:
        conn.close()


def test_us10_db_migration_idempotent(tmp_path):
    """Running the SQLite migrator twice is a no-op on the second pass."""
    db_path = tmp_path / "tasks.db"
    fixture = REPO_ROOT / "tests" / "fixtures" / "legacy_tasks_db.sqlite"
    db_path.write_bytes(fixture.read_bytes())

    r1 = mle.migrate_sqlite(db_path)
    r2 = mle.migrate_sqlite(db_path)
    assert r1["migrated"] == 5
    assert r2["migrated"] == 0
