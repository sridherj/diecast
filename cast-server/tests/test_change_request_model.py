"""Contract tests for the ``RequirementsWriteback`` output.json artifact (Phase 5 sp1).

This is the proposal *payload* a downstream emitter rides in
``AgentOutput.artifacts[]``. The load-bearing properties:

* a good ``addition`` (no target region) validates;
* ``kind`` is constrained to the three-value enum — a bad kind is a ``ValidationError``;
* ``base_version`` is required (owner decision #2: integer ``requirement_versions.version``);
* a ``modification``/``annotation`` must name its target region, an ``addition`` must not;
* the artifact rides ``AgentOutput`` cleanly, **and** a parent that does not know the
  ``requirements_writeback`` type ignores it without error (contract-v2 "parents ignore
  unknown fields") — proving the type is purely additive.
"""
from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from cast_server.models.agent_output import AgentOutput
from cast_server.models.requirements_writeback import RequirementsWriteback


# ---------------------------------------------------------------------------
# RequirementsWriteback validation
# ---------------------------------------------------------------------------

def test_valid_addition_payload() -> None:
    """A pure addition (no target region) validates with target_quote unset."""
    expected_base_version = 3
    wb = RequirementsWriteback(
        kind="addition",
        proposed_body="FR-099: The system MUST emit a heartbeat every 30s.",
        base_version=expected_base_version,
    )
    assert wb.kind == "addition"
    assert wb.target_quote is None
    assert wb.base_version == expected_base_version


def test_valid_modification_payload_with_target() -> None:
    """A modification names the region it changes via target_quote."""
    wb = RequirementsWriteback(
        kind="modification",
        proposed_body="FR-001: The system MUST authenticate via OIDC.",
        base_version=2,
        target_quote="The system MUST authenticate via password.",
        section_hint="## Authentication",
        origin_phase="planning",
        origin_activity_id="run_20260612_000000_abcdef",
        origin_artifact_path="plan.collab.md",
    )
    assert wb.kind == "modification"
    assert wb.target_quote == "The system MUST authenticate via password."


def test_rejects_bad_kind() -> None:
    """``kind`` is a closed enum — 'delete' is not a member."""
    with pytest.raises(ValidationError):
        RequirementsWriteback(
            kind="delete",  # type: ignore[arg-type]
            proposed_body="anything",
            base_version=1,
        )


def test_rejects_missing_base_version() -> None:
    """``base_version`` is required (owner decision #2)."""
    with pytest.raises(ValidationError):
        RequirementsWriteback(  # type: ignore[call-arg]
            kind="addition",
            proposed_body="anything",
        )


def test_rejects_empty_proposed_body() -> None:
    """``proposed_body`` must carry the change text (min_length=1)."""
    with pytest.raises(ValidationError):
        RequirementsWriteback(
            kind="addition",
            proposed_body="",
            base_version=1,
        )


def test_rejects_addition_with_target_quote() -> None:
    """A pure addition must not carry a target region."""
    with pytest.raises(ValidationError):
        RequirementsWriteback(
            kind="addition",
            proposed_body="new requirement",
            base_version=1,
            target_quote="some existing text",
        )


def test_rejects_modification_without_target_quote() -> None:
    """A modification must name the region it changes."""
    with pytest.raises(ValidationError):
        RequirementsWriteback(
            kind="modification",
            proposed_body="changed text",
            base_version=1,
        )


def test_rejects_annotation_without_target_quote() -> None:
    """An annotation, like a modification, must name its target region."""
    with pytest.raises(ValidationError):
        RequirementsWriteback(
            kind="annotation",
            proposed_body="note: revisit this",
            base_version=1,
        )


# ---------------------------------------------------------------------------
# Additive-artifact contract: rides AgentOutput; unknown to old parsers
# ---------------------------------------------------------------------------

def _writeback_artifact() -> dict:
    wb = RequirementsWriteback(
        kind="addition",
        proposed_body="FR-099: heartbeat every 30s",
        base_version=3,
    )
    return {
        "path": "plan.collab.md",
        "type": "requirements_writeback",
        "description": "proposed FR-099 from planning",
        "payload": wb.model_dump(),
    }


def test_agent_output_carries_writeback_artifact() -> None:
    """An AgentOutput carrying a requirements_writeback artifact parses cleanly."""
    out = AgentOutput(
        agent_name="synthetic-child",
        status="completed",
        summary="proposed a requirement change",
        artifacts=[_writeback_artifact()],
    )
    assert out.artifacts[0]["type"] == "requirements_writeback"
    assert out.artifacts[0]["payload"]["kind"] == "addition"


def test_old_parser_ignores_unknown_artifact_type() -> None:
    """A parent built before Phase 5 — modelled here as a minimal AgentOutput-shaped
    parser that does not enumerate artifact types — ignores the unknown type without
    error. This is the contract-v2 "parents ignore unknown fields" guarantee that
    makes ``requirements_writeback`` purely additive.
    """

    class LegacyAgentOutput(BaseModel):
        # A pre-Phase-5 consumer: knows the envelope, treats artifacts opaquely.
        agent_name: str
        status: str
        summary: str
        artifacts: list[dict] = []

    payload = {
        "agent_name": "synthetic-child",
        "status": "completed",
        "summary": "proposed a requirement change",
        "artifacts": [_writeback_artifact()],
    }

    legacy = LegacyAgentOutput.model_validate(payload)
    # The legacy parser neither rejects nor specially-handles the new type.
    assert legacy.artifacts[0]["type"] == "requirements_writeback"
