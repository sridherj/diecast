"""Pydantic model for the ``requirements_writeback`` output.json artifact.

A downstream phase (exploration / planning / execution) that surfaces a
requirement-affecting change does NOT edit the canonical ``.collab.md``. It rides
this payload as one item in ``AgentOutput.artifacts[]`` with
``type == "requirements_writeback"``, proposing a change-request the server will
intake (sp2), conflict-check (sp3a), and — only if accepted — apply via the sole
file-writer agent (sp4). Nothing here applies anything; it is the proposal payload.

``AgentOutput.artifacts`` is ``list[dict]``, so a parent that does not understand
this type ignores it for free (contract-v2 "parents ignore unknown fields"). This
model is therefore purely additive — it exists to *validate* an emitter's payload,
not to gate any existing parent.

The fields mirror the ``change_requests`` columns the emitter controls; the
server owns ``id`` / ``status`` / timestamps / ``author*`` (server-derived) and
they are deliberately absent here.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class RequirementsWriteback(BaseModel):
    """Additive output.json artifact a downstream agent rides to propose a change.

    A ``modification`` or ``annotation`` must name the region it changes
    (``target_quote``); a pure ``addition`` must not (there is no target region).
    """

    kind: Literal["addition", "modification", "annotation"]
    proposed_body: str = Field(min_length=1)
    base_version: int  # the requirement_versions.version assumed (owner decision #2)
    target_quote: str | None = None  # NULL => pure addition (no target region)
    section_hint: str | None = None
    origin_phase: str | None = None
    origin_activity_id: str | None = None
    origin_artifact_path: str | None = None

    @model_validator(mode="after")
    def _kind_matches_target(self) -> RequirementsWriteback:
        # A modification/annotation must name what it changes; an addition must not.
        if self.kind == "addition":
            if self.target_quote is not None:
                raise ValueError("an 'addition' must not carry a target_quote (no target region)")
        else:  # modification | annotation
            if not self.target_quote:
                raise ValueError(
                    f"a '{self.kind}' must name the region it changes via target_quote"
                )
        return self
