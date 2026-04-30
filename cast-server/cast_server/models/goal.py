"""Goal models."""

from datetime import date
from pydantic import BaseModel


class Goal(BaseModel):
    """Goal entity as stored in DB."""
    slug: str
    title: str
    status: str = "idea"
    phase: str | None = None
    origin: str = "manual"
    in_focus: bool = False
    created_at: date | None = None
    accepted_at: date | None = None
    tags: list[str] = []
    folder_path: str = ""
    gstack_dir: str | None = None
    external_project_dir: str | None = None


class GoalCreate(BaseModel):
    """Input for creating a new goal."""
    title: str
    tags: list[str] = []
    in_focus: bool = False


class GoalUpdate(BaseModel):
    """Input for updating a goal."""
    status: str | None = None
    phase: str | None = None
    in_focus: bool | None = None
    tags: list[str] | None = None
    gstack_dir: str | None = None
    external_project_dir: str | None = None
