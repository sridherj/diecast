"""SQLite database connection for Task OS."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from cast_server.config import DB_PATH

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def init_db(db_path: Path | str | None = None) -> None:
    """Initialize DB schema and run migrations. Call once at startup."""
    if isinstance(db_path, str):
        db_path = Path(db_path)
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


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Get a SQLite connection. Auto-creates schema if DB file is new."""
    # SQLite 3.9+ is a hard contract — record_skill (sp2) relies on
    # json_insert(... '$[#]' ...) array-append semantics that landed in 3.9.
    # 3.9 was released in 2015; the floor is a contract, not a fallback dance.
    if sqlite3.sqlite_version_info < (3, 9, 0):
        raise SystemExit(
            "cast-server requires SQLite 3.9+ for record_skill's "
            f"json_insert(... '$[#]' ...) semantics; got {sqlite3.sqlite_version}."
        )
    if isinstance(db_path, str):
        db_path = Path(db_path)
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
    # Stop's close-by-session query needs this for sub-millisecond filtering as agent_runs grows.
    conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_runs_session_status ON agent_runs(session_id, status)")

    # Subagent capture (cast-subagent-and-skill-capture sp1).
    # `skills_used` carries a JSON array of {name, invoked_at} appended on
    # PreToolUse(Skill); `claude_agent_id` carries SubagentStart.agent_id and
    # is the closure key on SubagentStop.
    try:
        conn.execute("ALTER TABLE agent_runs ADD COLUMN skills_used TEXT DEFAULT '[]'")
    except sqlite3.OperationalError:
        pass  # column already exists

    try:
        conn.execute("ALTER TABLE agent_runs ADD COLUMN claude_agent_id TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists

    # Partial index covers the SubagentStop closure path (exact-match WHERE
    # claude_agent_id = ?). Partial because only subagent rows ever populate
    # the column; user-invocation and CLI rows leave it NULL.
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_agent_runs_claude_agent_id "
        "ON agent_runs(claude_agent_id) WHERE claude_agent_id IS NOT NULL"
    )

    _seed_system_goals(conn)


def _seed_system_goals(conn: sqlite3.Connection) -> None:
    """Idempotently ensure rows that other services FK into.

    ``system-ops`` is the goal_slug used by user_invocation_service.register and
    by agent_service.invoke_agent's fallback path. agent_runs.goal_slug is NOT
    NULL with an FK to goals(slug) and ``PRAGMA foreign_keys=ON``, so any
    insert against a missing target row would fail.
    """
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT OR IGNORE INTO goals (slug, title, status, in_focus, origin,
                                     folder_path, created_at, accepted_at)
        VALUES ('system-ops', 'System Ops', 'accepted', 0, 'manual',
                'system-ops', ?, ?)
        """,
        (now, now),
    )
    conn.commit()
