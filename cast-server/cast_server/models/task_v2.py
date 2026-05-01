"""Task models (US10 — `estimate_size` schema).

The legacy `estimated_time: str | None` field is replaced with
`estimate_size: EstimateSize` end-to-end. See:
- `db/schema.sql` (canonical column definition + CHECK constraint)
- `bin/migrate-legacy-estimates.py` (legacy → T-shirt mapping, importable)
- `agents/cast-task-suggester/cast-task-suggester.md` (calibration table)

This module sits alongside the legacy `task.py` until the full rebrand
sub-phase migrates remaining cast-server consumers off `estimated_time`.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator

# Valid statuses: pending, in_progress, completed, suggested, declined
TASK_STATUSES = {"pending", "in_progress", "completed", "suggested", "declined"}
TASK_CREATION_STATUSES = {"pending", "suggested"}


class EstimateSize(str, Enum):
    """T-shirt CC-time estimate (US10).

    See cast-task-suggester prompt for the calibration table:
    XS  <5 min        / <50K tokens   — trivial
    S   5–15 min     / 50–200K       — small focused change
    M   15–45 min    / 200–500K      — default; multi-file change
    L   45 min–2 hr  / 500K–1M       — substantial; consider splitting
    XL  >2 hr        / >1M           — too big; MUST split
    """

    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"


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
    estimate_size: EstimateSize = Field(
        default=EstimateSize.M,
        description="T-shirt CC-time estimate. See US10 calibration table.",
    )
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
    estimate_size: EstimateSize = Field(
        default=EstimateSize.M,
        description="T-shirt CC-time estimate (XS|S|M|L|XL). Default: M.",
    )
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
            raise ValueError(
                f"Status on creation must be one of {TASK_CREATION_STATUSES}, got '{v}'"
            )
        return v


class TaskComplete(BaseModel):
    """Input for completing a task."""

    actual_time: str | None = None
    moved_toward_goal: str | None = None
    notes: str | None = None
