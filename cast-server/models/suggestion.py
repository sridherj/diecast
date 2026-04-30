"""Goal suggestion models."""

from pydantic import BaseModel


class GoalSuggestion(BaseModel):
    """Goal suggestion from GoalDetector."""
    id: int | None = None
    title: str
    rationale: str | None = None
    source_entries: list[str] = []
    status: str = "pending"
    created_at: str = ""
    resolved_at: str | None = None
    created_goal_slug: str | None = None
