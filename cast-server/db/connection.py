"""SQLite database connection for Task OS."""

import sqlite3
from pathlib import Path

from taskos.config import DB_PATH

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def init_db(db_path: Path | None = None) -> None:
    """Initialize DB schema and run migrations. Call once at startup."""
    conn = get_connection(db_path)
    try:
        with open(SCHEMA_PATH) as f:
            schema = f.read()
        # Execute each statement individually to avoid executescript's implicit COMMIT
        for statement in schema.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(statement)
        conn.commit()
        _run_migrations(conn)
    finally:
        conn.close()


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Get a SQLite connection. Auto-creates schema if DB file is new."""
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not path.exists() or path.stat().st_size == 0
    conn = sqlite3.connect(str(path), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    if is_new:
        with open(SCHEMA_PATH) as f:
            conn.executescript(f.read())
        _run_migrations(conn)
    return conn


def _run_migrations(conn: sqlite3.Connection) -> None:
    """Run idempotent schema migrations for columns added after initial schema."""
    try:
        conn.execute("ALTER TABLE tasks ADD COLUMN task_artifacts TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists

    # Agent run token tracking columns
    for col, coltype in [
        ("session_id", "TEXT"),
        ("input_tokens", "INTEGER"),
        ("output_tokens", "INTEGER"),
        ("cost_usd", "REAL"),
        ("cache_write_tokens", "INTEGER"),
        ("cache_read_tokens", "INTEGER"),
    ]:
        try:
            conn.execute(f"ALTER TABLE agent_runs ADD COLUMN {col} {coltype}")
        except sqlite3.OperationalError:
            pass  # column already exists

    # Attention flagging column on agent_runs
    try:
        conn.execute("ALTER TABLE agent_runs ADD COLUMN needs_attention INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # column already exists

    # Phase 1: Agent Orchestration v3 — new columns on agent_runs
    for col_name, col_type in [
        ("parent_run_id", "TEXT"),
        ("result_summary", "TEXT"),
        ("git_branch", "TEXT"),
        ("git_worktree_path", "TEXT"),
        ("rate_limit_pauses", "TEXT DEFAULT '[]'"),
        ("active_execution_seconds", "INTEGER"),
        ("working_dir", "TEXT"),
    ]:
        try:
            conn.execute(f"ALTER TABLE agent_runs ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass  # column already exists

    # Goal directory config columns
    for col in ["gstack_dir", "external_project_dir"]:
        try:
            conn.execute(f"ALTER TABLE goals ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass  # column already exists

    # Session display name for agent runs (Phase 3.4)
    try:
        conn.execute("ALTER TABLE agent_runs ADD COLUMN session_name TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists

    # Directory metadata JSON blob on agent_runs (Phase 3.1, Req 4.1)
    try:
        conn.execute("ALTER TABLE agent_runs ADD COLUMN directories TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists

    # Resume command and context usage on agent_runs (Phase 3.2, Req 4.2)
    for col_name in ["resume_command", "context_usage"]:
        try:
            conn.execute(f"ALTER TABLE agent_runs ADD COLUMN {col_name} TEXT")
        except sqlite3.OperationalError:
            pass  # column already exists

    # Phase 1: agent_error_memories table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS agent_error_memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_name TEXT NOT NULL,
        error_pattern TEXT NOT NULL,
        pattern_hash TEXT NOT NULL,
        error_category TEXT NOT NULL,
        is_transient INTEGER NOT NULL DEFAULT 0,
        occurrence_count INTEGER NOT NULL DEFAULT 1,
        first_seen TEXT NOT NULL,
        last_seen TEXT NOT NULL,
        run_ids TEXT NOT NULL DEFAULT '[]',
        resolution TEXT,
        resolution_status TEXT NOT NULL DEFAULT 'unresolved',
        suppress_after_days INTEGER,
        inject_as_context INTEGER NOT NULL DEFAULT 1,
        UNIQUE(agent_name, pattern_hash)
    )
    """)
    conn.execute("""
    CREATE INDEX IF NOT EXISTS idx_error_memories_agent
    ON agent_error_memories(agent_name, resolution_status)
    """)
