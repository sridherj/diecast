"""Pydantic model for the agent output.json contract.

Agents write .agent-{run_id}.output.json in the goal directory when they complete.
This model validates and parses that output. It also serves as the canonical
documentation of the output contract (contract_version: "2").
"""

from pydantic import BaseModel


class AgentOutput(BaseModel):
    """Structured output written by agents on completion.

    Contract version 2. Bump contract_version when schema changes;
    consumer (agent_service) handles legacy versions.

    v2 additions: human_action_needed, human_action_items
    """

    contract_version: str = "2"
    agent_name: str
    task_title: str = ""
    status: str  # completed, partial, failed
    summary: str
    artifacts: list[dict] = []  # [{path, type, description}]
    errors: list[str] = []
    next_steps: list[str] = []
    started_at: str = ""  # ISO 8601, injected by Diecast into the prompt
    completed_at: str = ""  # ISO 8601, written by agent at time of output
    human_action_needed: bool = False
    human_action_items: list[str] = []  # e.g., ["Approve spec update", "Fix Series A amount"]
