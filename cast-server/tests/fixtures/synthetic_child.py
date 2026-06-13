"""Simulated downstream emitter for the round-trip write-back E2E (Phase 5, SC-006).

Real planner/executor emitters are **hard-deferred** to a later goal (the v2 deferral fence).
This fixture stands in for them so SC-006 is provable *without* wiring a real emitter: it builds
exactly the contract-v2 ``output.json`` shape a downstream phase would write — an ``AgentOutput``
envelope whose ``artifacts[]`` carries one ``requirements_writeback`` item — and a tiny extractor
that pulls the write-back proposals back out.

It is a pure payload factory: it writes **no file**, drives **no live subagent**, and performs
**no I/O**. The receiving side under test (intake → conflict → apply → notify) is what closes the
loop; the emitter only produces the proposal the server intakes. Crucially, the emitter never
stamps trusted identity — ``author``/``author_type`` are *server-derived* at intake (the anti-spoof
seam in ``routes/change_requests.py``), so this fixture deliberately carries only the columns an
emitter legitimately controls (``kind`` / ``proposed_body`` / ``base_version`` / ``target_quote`` /
``section_hint`` / ``origin_*``), exactly like the real ``RequirementsWriteback`` artifact model.

Keeping the emitter deterministic (no timestamps in the payload, no randomness) lets the SC-006
proof run in the default suite rather than as a slow ``eval_`` test.
"""
from __future__ import annotations

from typing import Any

from cast_server.models.requirements_writeback import RequirementsWriteback

# The artifact ``type`` discriminator a downstream phase tags its write-back proposal with. A
# parent that does not understand it ignores it for free (contract-v2 "parents ignore unknown
# fields"); the receiving server keys on this exact string to find proposals in artifacts[].
WRITEBACK_ARTIFACT_TYPE = "requirements_writeback"


def writeback_artifact(
    *,
    kind: str,
    proposed_body: str,
    base_version: int,
    target_quote: str | None = None,
    section_hint: str | None = None,
    origin_phase: str | None = "planning",
    origin_activity_id: str | None = None,
    origin_artifact_path: str | None = "plan.collab.md",
) -> dict[str, Any]:
    """Build one ``requirements_writeback`` ``artifacts[]`` item, validated against the real model.

    The payload is run through :class:`RequirementsWriteback` so this fixture can only ever emit a
    proposal the production intake route would accept (same-door at the schema level): the ``kind``
    enum, the required integer ``base_version``, a non-empty ``proposed_body``, and the
    ``kind``↔``target_quote`` cross-field rule (an ``addition`` must NOT name a region; a
    ``modification``/``annotation`` MUST). A bad shape raises here, in the fixture, never silently.

    Returns the ``artifacts[]`` item shape: ``{type, path, description, **proposal}`` — ``type`` is
    the discriminator, ``path`` records the artifact the change was *derived from* (provenance), and
    the proposal columns are flattened alongside so the receiver reads them with no nested unwrap.
    """
    proposal = RequirementsWriteback(
        kind=kind,
        proposed_body=proposed_body,
        base_version=base_version,
        target_quote=target_quote,
        section_hint=section_hint,
        origin_phase=origin_phase,
        origin_activity_id=origin_activity_id,
        origin_artifact_path=origin_artifact_path,
    )
    return {
        "type": WRITEBACK_ARTIFACT_TYPE,
        "path": origin_artifact_path or "(downstream artifact)",
        "description": f"Proposed requirement {kind} from {origin_phase or 'a downstream phase'}",
        **proposal.model_dump(),
    }


def emit_output(
    run_id: str,
    writebacks: list[dict[str, Any]],
    *,
    agent_name: str = "synthetic-downstream-emitter",
    summary: str = "Surfaced a requirement-affecting change while working downstream.",
) -> dict[str, Any]:
    """Wrap one or more write-back artifacts in a contract-v2 ``AgentOutput`` envelope.

    Mirrors the envelope a real downstream agent writes to
    ``<goal_dir>/.agent-<run_id>.output.json``. The receiving server reads ``artifacts[]`` and
    intakes every ``requirements_writeback`` item; all other contract-v2 fields are present so the
    shape is faithful, but only the write-back artifacts are load-bearing for SC-006.
    """
    return {
        "contract_version": "2",
        "agent_name": agent_name,
        "run_id": run_id,
        "status": "completed",
        "summary": summary,
        "artifacts": list(writebacks),
        "errors": [],
        "next_steps": [],
    }


def extract_writebacks(output: dict[str, Any]) -> list[dict[str, Any]]:
    """Pull every ``requirements_writeback`` proposal out of an emitted ``output.json`` envelope.

    The receiving counterpart to :func:`emit_output`: filters ``artifacts[]`` on the ``type``
    discriminator and returns only the proposal columns the intake route consumes (the envelope's
    ``type``/``path``/``description`` framing is dropped — the server derives ``author`` itself).
    A parent that does not understand the type simply never calls this, ignoring it for free.
    """
    proposals: list[dict[str, Any]] = []
    for artifact in output.get("artifacts", []):
        if not isinstance(artifact, dict) or artifact.get("type") != WRITEBACK_ARTIFACT_TYPE:
            continue
        proposals.append({
            "kind": artifact["kind"],
            "proposed_body": artifact["proposed_body"],
            "base_version": artifact["base_version"],
            "target_quote": artifact.get("target_quote"),
            "section_hint": artifact.get("section_hint"),
            "origin_phase": artifact.get("origin_phase"),
            "origin_activity_id": artifact.get("origin_activity_id"),
            "origin_artifact_path": artifact.get("origin_artifact_path"),
        })
    return proposals
