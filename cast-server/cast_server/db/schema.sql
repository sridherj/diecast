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
    external_project_dir TEXT
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
