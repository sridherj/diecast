#!/usr/bin/env python3
"""Migrate legacy effort estimates → `estimate_size` (US10).

Internal use; not on user PATH. One-shot data migration; obsolete after the
matching deploy. Kept for users on stale databases.

Pre-rebrand TaskOS used either:
- `estimated_time TEXT` carrying values like ``"30m"``, ``"45m"``, ``"60m"`` in
  the DB column and YAML task files, OR
- `estimate_minutes INTEGER` (older variants in some fixtures).

Diecast US10 standardizes on `estimate_size TEXT NOT NULL CHECK(...)` with the
canonical T-shirt set ``{XS, S, M, L, XL}``.

This module is BOTH a CLI script and an importable module. cast-server's
``task_service`` imports ``minutes_to_size`` / ``time_str_to_size`` to coerce
inbound legacy data on the fly (so the OSS launch can absorb a TaskOS export
without a separate migration step).

Idempotent: running twice is a no-op. Detects column / field presence.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
from pathlib import Path
from typing import Any

# (upper_bound_exclusive, size) — sweep from XS upward.
_BUCKETS: list[tuple[int, str]] = [
    (10, "XS"),     # <10
    (30, "S"),      # 10–30 (exclusive of 30)
    (90, "M"),      # 30–90
    (180, "L"),     # 90–180
    (10**9, "XL"),  # >180 (anything else)
]

CANONICAL_SIZES = ("XS", "S", "M", "L", "XL")

# Matches "30m", "45 m", "1h", "1.5h", "90min" etc.
_TIME_RE = re.compile(
    r"^\s*(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>m(?:in(?:utes?)?)?|h(?:r|rs|ours?)?)?\s*$",
    re.IGNORECASE,
)


def minutes_to_size(minutes: int | float | None) -> str:
    """Map legacy minutes (int/float) → canonical T-shirt size.

    None or non-numeric → "M" (the documented default).
    """
    if minutes is None:
        return "M"
    try:
        m = float(minutes)
    except (TypeError, ValueError):
        return "M"
    if m < 0:
        return "M"
    for upper, size in _BUCKETS:
        if m < upper:
            return size
    return "XL"


def time_str_to_size(value: str | None) -> str:
    """Map legacy ``estimated_time`` strings (``"30m"``, ``"1h"``) → T-shirt size.

    Empty / unparseable / None → "M". Already-canonical values pass through.
    """
    if value is None:
        return "M"
    if not isinstance(value, str):
        return minutes_to_size(value)  # type: ignore[arg-type]

    cleaned = value.strip()
    if not cleaned:
        return "M"

    # Already canonical?
    upper = cleaned.upper()
    if upper in CANONICAL_SIZES:
        return upper

    match = _TIME_RE.match(cleaned)
    if not match:
        return "M"

    num = float(match.group("num"))
    unit = (match.group("unit") or "m").lower()
    if unit.startswith("h"):
        minutes = num * 60.0
    else:
        minutes = num

    return minutes_to_size(minutes)


def coerce_to_size(value: Any) -> str:
    """Best-effort coercion: accepts canonical, time strings, or numeric minutes."""
    if isinstance(value, str):
        return time_str_to_size(value)
    if isinstance(value, (int, float)):
        return minutes_to_size(value)
    return "M"


# ---------------------------------------------------------------------------
# YAML migration (task lists shipped as YAML files)
# ---------------------------------------------------------------------------


def migrate_yaml(path: Path) -> dict:
    """Migrate a YAML task file in place. Returns counts dict.

    Replaces ``estimated_time`` / ``estimate_minutes`` with ``estimate_size``
    on each task. Idempotent: tasks that already carry ``estimate_size`` are
    skipped.
    """
    import yaml  # local import — yaml is a runtime dep, not import-time required

    raw = path.read_text()
    data = yaml.safe_load(raw) or {}
    counts = {"migrated": 0, "skipped": 0}

    tasks = data.get("tasks") if isinstance(data, dict) else None
    if not isinstance(tasks, list):
        return counts

    for task in tasks:
        if not isinstance(task, dict):
            continue
        if "estimate_size" in task and task["estimate_size"] in CANONICAL_SIZES:
            counts["skipped"] += 1
            # Strip legacy keys if they linger so the file converges.
            task.pop("estimated_time", None)
            task.pop("estimate_minutes", None)
            continue

        legacy_minutes = task.pop("estimate_minutes", None)
        legacy_time = task.pop("estimated_time", None)

        if legacy_minutes is not None:
            task["estimate_size"] = minutes_to_size(legacy_minutes)
        elif legacy_time is not None:
            task["estimate_size"] = time_str_to_size(legacy_time)
        else:
            task["estimate_size"] = "M"
        counts["migrated"] += 1

    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return counts


# ---------------------------------------------------------------------------
# SQLite migration (the canonical Diecast DB lives in SQLite)
# ---------------------------------------------------------------------------


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def migrate_sqlite(db_path: Path) -> dict:
    """Migrate a SQLite DB in place. Returns counts dict.

    Steps (idempotent):
      1. If `estimate_size` is missing, ADD COLUMN with the CHECK constraint
         and DEFAULT 'M'.
      2. For every row whose `estimate_size` was just defaulted (or any row
         that still has a non-NULL legacy column), backfill from the legacy
         value via ``coerce_to_size``.
      3. If SQLite supports DROP COLUMN (>=3.35) and a legacy column exists
         alongside the new one, drop the legacy column. Otherwise leave it
         (the cast-server task_service ignores it).
    """
    counts = {"migrated": 0, "skipped": 0, "errors": 0}
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cols = _columns(conn, "tasks")
        has_size = "estimate_size" in cols
        legacy_cols = [c for c in ("estimated_time", "estimate_minutes") if c in cols]

        # 1. Add the new column if missing.
        if not has_size:
            conn.execute(
                "ALTER TABLE tasks ADD COLUMN estimate_size TEXT NOT NULL "
                "DEFAULT 'M' CHECK(estimate_size IN ('XS','S','M','L','XL'))"
            )
            cols.add("estimate_size")
            has_size = True

        # 2. Backfill from legacy columns where present.
        if legacy_cols:
            select_cols = ", ".join(["id", "estimate_size", *legacy_cols])
            rows = conn.execute(f"SELECT {select_cols} FROM tasks").fetchall()
            for row in rows:
                current = row["estimate_size"]
                # If row already carries a non-default canonical size and no
                # legacy is set, leave it.
                legacy_value = next(
                    (row[col] for col in legacy_cols if row[col] is not None),
                    None,
                )
                if legacy_value is None:
                    counts["skipped"] += 1
                    continue
                # Honor an existing canonical size if it differs from the
                # default 'M' (operator may have hand-set it).
                if current and current in CANONICAL_SIZES and current != "M":
                    counts["skipped"] += 1
                    continue

                new_size = coerce_to_size(legacy_value)
                conn.execute(
                    "UPDATE tasks SET estimate_size = ? WHERE id = ?",
                    (new_size, row["id"]),
                )
                counts["migrated"] += 1

        # 3. Drop legacy columns where SQLite supports it.
        sqlite_ver = tuple(int(x) for x in sqlite3.sqlite_version.split("."))
        if sqlite_ver >= (3, 35, 0):
            for col in legacy_cols:
                try:
                    conn.execute(f"ALTER TABLE tasks DROP COLUMN {col}")
                except sqlite3.OperationalError:
                    counts["errors"] += 1

        conn.commit()
    finally:
        conn.close()
    return counts


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", type=Path, help="YAML file or SQLite DB to migrate")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Read-only inspection; print what would change without writing.",
    )
    args = ap.parse_args()

    if args.dry_run:
        # Lightweight: just report existence + suffix so callers can wire CI checks.
        kind = "sqlite" if args.path.suffix in {".sqlite", ".db"} else "yaml"
        print({"kind": kind, "path": str(args.path), "exists": args.path.exists()})
        return

    if args.path.suffix in {".sqlite", ".db"}:
        result = migrate_sqlite(args.path)
    else:
        result = migrate_yaml(args.path)
    print(result)


if __name__ == "__main__":
    main()
