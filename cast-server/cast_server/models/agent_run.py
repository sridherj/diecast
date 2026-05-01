"""Pydantic model for agent execution run records (DB-backed)."""

from pydantic import BaseModel


class AgentRun(BaseModel):
    """Represents a single agent execution run, stored in the agent_runs table.

    ``session_id`` carries the Claude Code (parent main-loop) session id —
    shared by every subagent in the session. Populated by the user-invocation
    hook and by SubagentStart for cast-* subagents.

    ``claude_agent_id`` carries the Claude Code per-subagent runtime id from
    ``SubagentStart.agent_id``. NULL for user-invocation rows and CLI
    dispatches; populated only on subagent rows. Closure on ``SubagentStop``
    keys on this column for an exact-match single-row update.
    """

    id: str
    agent_name: str
    goal_slug: str
    task_id: int | None = None
    status: str = "pending"  # pending, running, completed, failed
    input_params: dict | None = None
    output: dict | None = None  # parsed output.json
    artifacts: list[dict] | None = None
    error_message: str | None = None
    exit_code: int | None = None
    session_id: str | None = None
    claude_agent_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    started_at: str | None = None
    completed_at: str | None = None
    needs_attention: int = 0
    parent_run_id: str | None = None
    result_summary: str | None = None
    git_branch: str | None = None
    git_worktree_path: str | None = None
    rate_limit_pauses: str = "[]"
    skills_used: list[dict] = []
    active_execution_seconds: int | None = None
    cache_read_tokens: int | None = None
    cache_write_tokens: int | None = None
    session_name: str | None = None
    directories: dict | None = None
    resume_command: str | None = None
    context_usage: dict | None = None
    scheduled_at: str | None = None
    created_at: str | None = None
