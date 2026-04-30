"""Migration round-trip + idempotency tests (Decision #16).

Two cases:

1. ``alembic upgrade head`` from an empty DB produces the same schema as
   running ``schema.sql`` directly — guards against silent drift between
   the SQL source-of-truth and the migration tree.
2. Running ``alembic upgrade head`` twice is a no-op — guards against
   migrations that accidentally re-run DDL on a stamped DB.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CAST_SERVER_DIR = REPO_ROOT / "cast-server"
ALEMBIC_INI = CAST_SERVER_DIR / "alembic.ini"
SCHEMA_SQL = CAST_SERVER_DIR / "cast_server" / "db" / "schema.sql"


def _alembic(db_path: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "DIECAST_DB_URL": f"sqlite:///{db_path}"}
    return subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ALEMBIC_INI), *args],
        cwd=CAST_SERVER_DIR,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def _schema_dump(db_path: Path) -> list[tuple[str, str, str]]:
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT type, name, sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' AND name != 'alembic_version' "
            "ORDER BY type, name"
        ).fetchall()
    finally:
        conn.close()
    return [(t, n, (s or "").strip()) for t, n, s in rows]


def test_round_trip(tmp_path: Path) -> None:
    """alembic upgrade head from empty DB matches direct schema.sql apply."""
    alembic_db = tmp_path / "alembic.db"
    raw_db = tmp_path / "raw.db"

    _alembic(alembic_db, "upgrade", "head")

    conn = sqlite3.connect(str(raw_db))
    try:
        conn.executescript(SCHEMA_SQL.read_text())
    finally:
        conn.close()

    assert _schema_dump(alembic_db) == _schema_dump(raw_db)


def test_idempotent(tmp_path: Path) -> None:
    """Running alembic upgrade head twice is a no-op."""
    db = tmp_path / "x.db"
    _alembic(db, "upgrade", "head")
    before = _schema_dump(db)
    _alembic(db, "upgrade", "head")
    after = _schema_dump(db)
    assert before == after
