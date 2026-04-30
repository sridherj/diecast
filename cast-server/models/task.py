"""Task models."""

from pydantic import BaseModel, field_validator

# Valid statuses: pending, in_progress, completed, suggested, declined
TASK_STATUSES = {"pending", "in_progress", "completed", "suggested", "declined"}
TASK_CREATION_STATUSES = {"pending", "suggested"}


class Task(BaseModel):
    """Task entity as stored in DB."""
    id: int | None = None
    goal_slug: str
    phase: str | None = None
    parent_id: int | None = None
    title: str
    outcome: str | None = None
    action: str | None = None
    task_type: str | None = None
    estimated_time: str | None = None
    energy: str | None = None
    assigned_to: str | None = None
    status: str = "pending"
    actual_time: str | None = None
    moved_toward_goal: str | None = None
    completion_notes: str | None = None
    sort_order: int | None = None
    tip: str | None = None
    recommended_agent: str | None = None
    task_artifacts: list[str] | None = None
    rationale: str | None = None
    is_spike: bool = False


class TaskCreate(BaseModel):
    """Input for creating a new task."""
    title: str
    outcome: str | None = None
    action: str | None = None
    task_type: str | None = None
    estimated_time: str | None = None
    energy: str | None = None
    assigned_to: str | None = None
    phase: str | None = None
    tip: str | None = None
    recommended_agent: str | None = None
    parent_id: int | None = None
    task_artifacts: list[str] | None = None
    rationale: str | None = None
    is_spike: bool = False
    status: str = "pending"

    @field_validator("status")
    @classmethod
    def status_must_be_creation_valid(cls, v: str) -> str:
        if v not in TASK_CREATION_STATUSES:
            raise ValueError(f"Status on creation must be one of {TASK_CREATION_STATUSES}, got '{v}'")
        return v


class TaskComplete(BaseModel):
    """Input for completing a task."""
    actual_time: str | None = None
    moved_toward_goal: str | None = None
    notes: str | None = None
