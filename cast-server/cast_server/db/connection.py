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

    # Workflow routing columns (Phase 3b) — written by record_routing_decision
    for col in ["workflow_family", "routing_handle", "routed_at"]:
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

    # Phase: requirements thin spine (refine-requirements-v2 Phase 1).
    # Deliberately absent: block_anchor / element surrogate (thin-spine #1), routing cols (Phase 3b).
    # change_request* tables (Phase 5) now live below. Mirrors db/schema.sql — keep the two in lockstep.
    conn.execute("""
    CREATE TABLE IF NOT EXISTS requirement_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal_slug TEXT NOT NULL,
        version INTEGER NOT NULL,                -- 1, 2, 3, ... per goal
        content TEXT NOT NULL,                   -- full .collab.md snapshot, byte-faithful
        content_hash TEXT NOT NULL,              -- requirements_render.hashing.content_hash(content)
        status TEXT NOT NULL DEFAULT 'current',  -- 'current' | 'archived'
        created_at TEXT NOT NULL,                -- ISO timestamp
        created_by TEXT,                         -- agent name or 'human'
        UNIQUE (goal_slug, version),
        FOREIGN KEY (goal_slug) REFERENCES goals(slug) ON DELETE CASCADE
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS requirement_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal_slug TEXT NOT NULL,
        version INTEGER NOT NULL,                -- version the comment was left against
        quoted_text TEXT NOT NULL,               -- the reviewer's selection, verbatim
        section_hint TEXT,                       -- nearest heading at capture time (a hint, not a key)
        body TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'open',      -- 'open' | 'resolved' | 'orphaned'
        author TEXT NOT NULL,
        author_kind TEXT NOT NULL DEFAULT 'human', -- 'human' | 'agent' (FR-013: the ONLY distinction)
        block_ref TEXT,                          -- canonical id of the enclosing labeled unit
                                                 --   container (server-resolved); NULL = cross-boundary
                                                 --   OR a ref-less render — both honest (sp2 Decision #1)
        anchor_space TEXT NOT NULL DEFAULT 'source', -- 'source' | 'render' (refine-req-v3 sp2)
        artifact_ref TEXT,                       -- goal-relative served-.html path the quote was minted
                                                 --   against (sp3b); NULL = refined_requirements.html
        created_at TEXT NOT NULL,
        updated_at TEXT,
        FOREIGN KEY (goal_slug) REFERENCES goals(slug) ON DELETE CASCADE
    )
    """)
    # refine-req-v3 sp2: a pre-existing DB whose requirement_comments predates the render-anchor
    # columns gets them added additively. Old rows keep anchor_space='source', block_ref=NULL —
    # the back-compatible default (a legacy source-anchored comment until the one-time migration
    # flips it). heartbeat/flag precedent: nullable/defaulted, no row rewrites.
    # exploration-pipeline-nxm sp3b: artifact_ref keys render-space anchoring to the SPECIFIC served
    # .html the quote was minted from. Nullable/defaulted — NULL = refined_requirements.html (the
    # existing meaning); additive only, old rows read NULL and keep requirements behavior byte-for-byte.
    for col_name, col_type in [
        ("block_ref", "TEXT"),
        ("anchor_space", "TEXT NOT NULL DEFAULT 'source'"),
        ("artifact_ref", "TEXT"),
    ]:
        try:
            conn.execute(f"ALTER TABLE requirement_comments ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass  # column already exists
    conn.execute("""
    CREATE TABLE IF NOT EXISTS comment_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        comment_id INTEGER NOT NULL,
        event_type TEXT NOT NULL,                -- 'created'|'resolved'|'reopened'|'orphaned'|'relocated'
        actor TEXT,
        payload TEXT,                            -- JSON
        created_at TEXT NOT NULL,
        FOREIGN KEY (comment_id) REFERENCES requirement_comments(id) ON DELETE CASCADE
    )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_req_versions_goal_status "
        "ON requirement_versions(goal_slug, status)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_req_comments_goal_state "
        "ON requirement_comments(goal_slug, state)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_comment_events_comment "
        "ON comment_events(comment_id)"
    )

    # Phase 5 (round-trip write-back). THIN SPINE: change_requests locates its target by
    # target_quote + section_hint (mirrors requirement_comments) — there is NO spec_elements
    # surrogate FK (that table never existed). base_version is the integer requirement_versions.version
    # the change assumed. Do not "restore" a surrogate column. Mirrors db/schema.sql byte-for-byte.
    conn.execute("""
    CREATE TABLE IF NOT EXISTS change_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal_slug TEXT NOT NULL,
        target_quote TEXT,                       -- NULL means pure addition, no target region
        section_hint TEXT,                       -- nearest heading hint, mirrors requirement_comments
        base_version INTEGER,                    -- the requirement_versions.version the change assumed
        proposed_body TEXT NOT NULL,             -- the addition/modification text
        kind TEXT NOT NULL,                      -- 'addition' | 'modification' | 'annotation'
        status TEXT NOT NULL DEFAULT 'proposed', -- 'proposed'|'applied'|'conflicted'|'rejected'|'superseded'
        origin_phase TEXT,                       -- e.g. 'planning'
        origin_activity_id TEXT,                 -- run_id of the emitting agent
        origin_artifact_path TEXT,               -- e.g. 'plan.collab.md'
        author TEXT NOT NULL,                    -- agent name or human identity (server-derived for humans)
        author_type TEXT NOT NULL CHECK (author_type IN ('human','agent')),  -- DATA, never a code branch (FR-013)
        created_at TEXT NOT NULL,
        updated_at TEXT,
        FOREIGN KEY (goal_slug) REFERENCES goals(slug) ON DELETE CASCADE
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS change_request_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        change_request_id INTEGER NOT NULL,
        event_type TEXT NOT NULL,                -- 'proposed'|'accepted'|'rejected'|'conflicted'|'applied'|'superseded'
        actor TEXT,
        payload TEXT,                            -- JSON
        created_at TEXT NOT NULL,
        FOREIGN KEY (change_request_id) REFERENCES change_requests(id) ON DELETE CASCADE
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS notifications_outbox (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        change_request_id INTEGER NOT NULL,
        payload TEXT NOT NULL,                   -- JSON: what changed + from where
        status TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'delivered'
        created_at TEXT NOT NULL,
        delivered_at TEXT,
        FOREIGN KEY (change_request_id) REFERENCES change_requests(id) ON DELETE CASCADE
    )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_change_requests_goal_status "
        "ON change_requests(goal_slug, status)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_change_request_events_cr "
        "ON change_request_events(change_request_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_notifications_outbox_status "
        "ON notifications_outbox(status)"
    )

    # Background maker render-job pipeline (refine-requirements-v3 Phase 3c). INITIAL table per
    # revision (a): heartbeat_at ships in the create table, not a later migration. 4a-2 adds ONLY
    # the four flag columns later — Phase 3 does not. Mirrors db/schema.sql byte-for-byte.
    conn.execute("""
    CREATE TABLE IF NOT EXISTS render_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal_slug TEXT NOT NULL,
        source_hash TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'running',  -- running|published|fallback|superseded|failed|flagged
        attempts INTEGER NOT NULL DEFAULT 0,
        error TEXT,
        started_at TEXT,
        finished_at TEXT,
        heartbeat_at TEXT,                        -- revision a: written at every stage boundary
        -- 4a-2: the four flag columns (queryable/observability copy; status enum unchanged).
        human_review INTEGER NOT NULL DEFAULT 0,
        review_reason TEXT,
        published_attempt INTEGER,
        published_score REAL,
        -- HOW-update-mode 3a: the CREATE/UPDATE decision for the job (additive observability, nullable).
        mode TEXT,
        FOREIGN KEY (goal_slug) REFERENCES goals(slug) ON DELETE CASCADE
    )
    """)
    # 4a-2 migration: a pre-existing v3 DB whose render_jobs predates the flag columns gets them
    # added additively (nullable / defaulted; no row rewrites). heartbeat_at is NOT here — it ships
    # in the CREATE TABLE above (revision a / reconciliation C4). HOW-update-mode 3a adds `mode` to
    # the SAME additive list (nullable; old rows read NULL).
    for col_name, col_type in [
        ("human_review", "INTEGER NOT NULL DEFAULT 0"),
        ("review_reason", "TEXT"),
        ("published_attempt", "INTEGER"),
        ("published_score", "REAL"),
        ("mode", "TEXT"),
    ]:
        try:
            conn.execute(f"ALTER TABLE render_jobs ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass  # column already exists
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_render_jobs_goal_hash "
        "ON render_jobs(goal_slug, source_hash)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_render_jobs_status "
        "ON render_jobs(status)"
    )

    # Same-door version-diff narration (refine-requirements-v3 Phase 4b-3). One row per
    # (goal_slug, base_version, head_version); the write path recomputes the deterministic diff
    # server-side and 422s any note referencing a change absent from it. UNIQUE makes a re-post an
    # upsert. Mirrors db/schema.sql byte-for-byte.
    conn.execute("""
    CREATE TABLE IF NOT EXISTS version_diff_narrations (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        goal_slug     TEXT NOT NULL,
        base_version  INTEGER NOT NULL,
        head_version  INTEGER NOT NULL,
        overview      TEXT NOT NULL,
        item_notes    TEXT NOT NULL,            -- JSON [{change, heading_or_ref, note}]
        created_by    TEXT,                     -- the dispatching parent's actor id
        created_at    TEXT NOT NULL,
        UNIQUE (goal_slug, base_version, head_version),
        FOREIGN KEY (goal_slug) REFERENCES goals(slug) ON DELETE CASCADE
    )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_version_diff_narrations_goal "
        "ON version_diff_narrations(goal_slug, base_version, head_version)"
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
