#!/usr/bin/env python3
"""Build the `legacy_tasks_db.sqlite` fixture used by US10 tests.

Run from the repo root:

    python3 tests/fixtures/build_legacy_tasks_db.py

The output is committed because it's tiny (a few KB) and the build script is
deterministic. Re-run any time the legacy schema definition needs to change.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "legacy_tasks_db.sqlite"

LEGACY_SCHEMA = """
CREATE TABLE goals (
    slug TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    folder_path TEXT NOT NULL
);

CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_slug TEXT NOT NULL,
    title TEXT NOT NULL,
    estimate_minutes INTEGER,
    status TEXT DEFAULT 'pending'
);
"""

ROWS = [
    # (title, minutes) — covers each T-shirt bucket boundary
    ("Trivial typo fix",       5),    # XS
    ("Add a small test",       20),   # S
    ("Refactor a function",    60),   # M
    ("Multi-file refactor",    120),  # L
    ("Rewrite a subsystem",    250),  # XL
]


def build() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(LEGACY_SCHEMA)
        conn.execute(
            "INSERT INTO goals (slug, title, folder_path) VALUES (?, ?, ?)",
            ("legacy", "Legacy fixture goal", "/tmp/legacy"),
        )
        for title, minutes in ROWS:
            conn.execute(
                "INSERT INTO tasks (goal_slug, title, estimate_minutes) VALUES (?, ?, ?)",
                ("legacy", title, minutes),
            )
        conn.commit()
    finally:
        conn.close()
    print(f"wrote {DB_PATH} ({DB_PATH.stat().st_size} bytes, {len(ROWS)} rows)")


if __name__ == "__main__":
    build()
