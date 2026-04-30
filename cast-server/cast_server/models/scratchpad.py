"""Scratchpad models."""

from pydantic import BaseModel


class ScratchpadEntry(BaseModel):
    """Single scratchpad entry."""
    id: int | None = None
    entry_date: str
    content: str
    flagged_as_goal: bool = False
    synced_at: str = ""


class ScratchpadCreate(BaseModel):
    """Input for creating a scratchpad entry."""
    content: str
