"""Delegation context for parent-child agent orchestration."""
from pydantic import BaseModel, ConfigDict


class DelegationContextData(BaseModel):
    model_config = ConfigDict(extra="allow")  # Allow custom fields (phase_section, etc.)

    goal_title: str
    goal_phase: str = ""  # Optional — not always meaningful for orchestrators
    relevant_artifacts: list[str] = []  # Absolute paths — parent resolves before delegation
    prior_output: str = ""  # 2-3 sentence summary of parent's work so far
    constraints: list[str] = []  # "do not delete files", "read-only run", etc.
    error_memories: list[dict] = []  # Pre-fetched from error_memory_service


class DelegationOutputConfig(BaseModel):
    # Empty = "use goal_dir" (route layer backfills via setdefault before construction).
    output_dir: str = ""
    expected_artifacts: list[str] = []
    contract_version: str = "1.0"


class DelegationContext(BaseModel):
    agent_name: str
    goal_slug: str = ""  # Auto-injected from top-level request field if missing
    task_id: int | None = None
    parent_run_id: str = ""  # Auto-injected from top-level request field if missing
    instructions: str
    context: DelegationContextData
    output: DelegationOutputConfig
