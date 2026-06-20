CREATE TABLE IF NOT EXISTS goals (
    slug TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'idea',
    phase TEXT,
    origin TEXT NOT NULL DEFAULT 'manual',
    in_focus INTEGER NOT NULL DEFAULT 0,
    created_at TEXT,
    accepted_at TEXT,
    tags TEXT,
    folder_path TEXT NOT NULL,
    gstack_dir TEXT,
    external_project_dir TEXT,
    workflow_family TEXT,
    routing_handle TEXT,
    routed_at TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_slug TEXT NOT NULL,
    phase TEXT,
    parent_id INTEGER REFERENCES tasks(id),
    title TEXT NOT NULL,
    outcome TEXT,
    action TEXT,
    task_type TEXT,
    estimated_time TEXT,
    energy TEXT,
    assigned_to TEXT,
    status TEXT DEFAULT 'pending',
    actual_time TEXT,
    moved_toward_goal TEXT,
    completion_notes TEXT,
    sort_order INTEGER,
    tip TEXT,
    recommended_agent TEXT,
    task_artifacts TEXT,  -- JSON array of relative-to-goal file paths
    rationale TEXT,
    is_spike INTEGER DEFAULT 0,
    FOREIGN KEY (goal_slug) REFERENCES goals(slug)
);

CREATE TABLE IF NOT EXISTS scratchpad_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_date TEXT NOT NULL,
    content TEXT NOT NULL,
    flagged_as_goal INTEGER DEFAULT 0,
    synced_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS goal_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    rationale TEXT,
    source_entries TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    created_goal_slug TEXT
);

CREATE TABLE IF NOT EXISTS agents (
    name TEXT PRIMARY KEY,
    type TEXT,
    description TEXT,
    input TEXT,
    output TEXT,
    tags TEXT,
    triggers TEXT,
    last_tested TEXT,
    synced_at TEXT NOT NULL
);

-- Agent execution runs (DB-only, not synced from files)
CREATE TABLE IF NOT EXISTS agent_runs (
    id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    goal_slug TEXT NOT NULL,
    task_id INTEGER,
    status TEXT NOT NULL DEFAULT 'pending',
    input_params TEXT,          -- JSON
    output TEXT,                -- JSON (from output.json)
    artifacts TEXT,             -- JSON array of {path, type, description}
    error_message TEXT,
    exit_code INTEGER,
    started_at TEXT,
    completed_at TEXT,
    scheduled_at TEXT,                    -- ISO timestamp for scheduled runs (nullable)
    created_at TEXT NOT NULL DEFAULT '',  -- ISO timestamp, always set at insertion
    skills_used TEXT DEFAULT '[]',        -- JSON array of {name, invoked_at}
    claude_agent_id TEXT,                 -- Claude Code SubagentStart.agent_id (subagent rows only)
    FOREIGN KEY (goal_slug) REFERENCES goals(slug) ON DELETE SET NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_tasks_goal_slug ON tasks(goal_slug);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_phase ON tasks(phase);
CREATE INDEX IF NOT EXISTS idx_goals_in_focus ON goals(in_focus);
CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);
CREATE INDEX IF NOT EXISTS idx_scratchpad_date ON scratchpad_entries(entry_date DESC);
CREATE INDEX IF NOT EXISTS idx_suggestions_status ON goal_suggestions(status);
CREATE INDEX IF NOT EXISTS idx_tasks_goal_status ON tasks(goal_slug, status);
CREATE INDEX IF NOT EXISTS idx_agent_runs_goal ON agent_runs(goal_slug);
CREATE INDEX IF NOT EXISTS idx_agent_runs_task ON agent_runs(task_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_status ON agent_runs(status);
CREATE INDEX IF NOT EXISTS idx_agent_runs_scheduled ON agent_runs(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_agent_runs_created ON agent_runs(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_parent_id ON tasks(parent_id);

-- Requirements thin spine (refine-requirements-v2 Phase 1).
-- Deliberately absent: block_anchor / element surrogate columns (thin-spine decision #1).
-- change_request* tables (Phase 5) now live below. Routing columns (Phase 3b: workflow_family,
-- routing_handle, routed_at) now live on the goals table above.
-- NB: init_db() splits this file on the statement separator, so comments here must avoid it.
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
);

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
    block_ref TEXT,                          -- canonical id of the enclosing labeled unit container,
                                             --   server-resolved. NULL = cross-boundary OR a
                                             --   ref-less render (zero anchor labels) — both honest
    anchor_space TEXT NOT NULL DEFAULT 'source', -- 'source' | 'render' (refine-req-v3 sp2: comments
                                             --   anchor to the published render snapshot, not source)
    artifact_ref TEXT,                       -- goal-relative path of the SERVED .html the quote was
                                             --   minted against (exploration-pipeline-nxm sp3b). NULL
                                             --   means refined_requirements.html (the back-compatible
                                             --   default). A value keys multi-artifact render-space
                                             --   anchoring so a comment never cross-anchors elsewhere
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY (goal_slug) REFERENCES goals(slug) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comment_events (    -- append-only trail (US5 S3 retrieval is free)
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    comment_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,                -- 'created'|'resolved'|'reopened'|'orphaned'|'relocated'
    actor TEXT,
    payload TEXT,                            -- JSON
    created_at TEXT NOT NULL,
    FOREIGN KEY (comment_id) REFERENCES requirement_comments(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_req_versions_goal_status ON requirement_versions(goal_slug, status);
CREATE INDEX IF NOT EXISTS idx_req_comments_goal_state ON requirement_comments(goal_slug, state);
CREATE INDEX IF NOT EXISTS idx_comment_events_comment ON comment_events(comment_id);

-- Phase 5 (round-trip write-back). THIN SPINE: change_requests locates its target by
-- target_quote + section_hint (mirrors requirement_comments) — there is NO spec_elements
-- surrogate FK (that table never existed). base_version is the integer requirement_versions.version
-- the change assumed. Do not "restore" a surrogate column.
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
);

CREATE TABLE IF NOT EXISTS change_request_events (    -- append-only audit (generalizes comment_events)
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    change_request_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,                -- 'proposed'|'accepted'|'rejected'|'conflicted'|'applied'|'superseded'
    actor TEXT,
    payload TEXT,                            -- JSON
    created_at TEXT NOT NULL,
    FOREIGN KEY (change_request_id) REFERENCES change_requests(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notifications_outbox (    -- transactional outbox (dual-write fix)
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    change_request_id INTEGER NOT NULL,
    payload TEXT NOT NULL,                   -- JSON: what changed + from where
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'delivered'
    created_at TEXT NOT NULL,
    delivered_at TEXT,
    FOREIGN KEY (change_request_id) REFERENCES change_requests(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_change_requests_goal_status ON change_requests(goal_slug, status);
CREATE INDEX IF NOT EXISTS idx_change_request_events_cr ON change_request_events(change_request_id);
CREATE INDEX IF NOT EXISTS idx_notifications_outbox_status ON notifications_outbox(status);

-- Background maker render-job pipeline (refine-requirements-v3 Phase 3c). INITIAL CREATE TABLE
-- per revision (a): heartbeat_at ships HERE, in the initial table — NOT a later migration. The
-- per-job thread writes heartbeat_at at EVERY stage boundary (run_what / gate_what / run_how /
-- gate_html / publish) — it is the staleness detector the lazy reaper reads. Readiness is NEVER
-- derived from this table — the published artifact's embedded source-hash is the single source of
-- truth (3d). This table is the observability / status / failure-reason surface only.
-- 4a-2's migration LATER adds ONLY the four flag columns (human_review, review_reason,
-- published_attempt, published_score) — Phase 3 does NOT create those. Mirrors db/connection.py.
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
    -- 4a-2 (the four flag columns ONLY — heartbeat_at already ships above, reconciliation C4). The
    -- queryable/observability copy (Phase-5 sweep input, post-mortem) — NOT the status-poll read
    -- path (that reads the served-artifact envelope stamp). Status enum is UNCHANGED, with
    -- `published` covering flagged publishes (the page IS served, human_review orthogonal).
    human_review INTEGER NOT NULL DEFAULT 0,
    review_reason TEXT,                        -- non_convergent|checker_unavailable|structural_degradation|structural_violation
    published_attempt INTEGER,
    published_score REAL,
    -- HOW-update-mode 3a: the CREATE/UPDATE decision for this job (additive observability, nullable —
    -- old rows / pre-decision rows read NULL). 'create' | 'update'. The job-start decide_mode() stamps
    -- the DECIDED mode even while production renders CREATE (the path is flag-gated inert until 3b).
    mode TEXT,
    FOREIGN KEY (goal_slug) REFERENCES goals(slug) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_render_jobs_goal_hash ON render_jobs(goal_slug, source_hash);
CREATE INDEX IF NOT EXISTS idx_render_jobs_status ON render_jobs(status);

-- Same-door version-diff narration (refine-requirements-v3 Phase 4b-3). One stored narration
-- per (goal_slug, base_version, head_version), POSTed by whichever agent cut the version. The
-- server NEVER dispatches an LLM on the version path. It stores and structurally validates. The
-- write path recomputes summarize(diff_blocks(old, new)) server-side and rejects (422) any note
-- referencing a change absent from that deterministic set, so the UI cannot show an invented
-- change even if this table were hand-edited. UNIQUE(goal_slug, base, head) makes a re-post an
-- UPSERT (a retried loop cycle replaces, never duplicates). Mirrors db/connection.py.
-- NB: init_db() splits this file on the statement separator, so comments here must avoid it.
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
);
CREATE INDEX IF NOT EXISTS idx_version_diff_narrations_goal
    ON version_diff_narrations(goal_slug, base_version, head_version);
