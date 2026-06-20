"""The exploration render-checker verdict (FR-017's 4 locked criteria), built on render_common.

The exploration checker emits ONE bare-JSON verdict grading FR-017's 4 criteria. `distinctness_ok`
(criterion 3) is a FIRST-CLASS dimension — never collapsed into `visual`. `derive_pass` requires the
generic gate (can_state_what + no gated missing token + zero error issues) AND all four per-criterion
booleans clear, so a degraded step (a `missing[]` naming `hat_coverage`) cannot false-pass.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from cast_server.render_common.verdict import (
    BaseVerdict,
    CheckerVerdictError,
    _as_bool,
    _as_float,
    _as_issues,
    _as_str_tuple,
    _extract_json_object,
)
from cast_server.render_common.verdict import canonical_score as _canonical_score
from cast_server.render_common.verdict import derive_pass as _derive_pass

CHECKER_CONTRACT = "cast-exploration-render-checker/v1"
#: The FR-017 4-criteria gated-token vocabulary. A `missing[]` entry naming any of these fails the
#: gate. `distinctness` is first-class (criterion 3), never collapsed into `visual`.
GATED_TOKENS: tuple[str, ...] = ("pov", "distinctness", "hat_coverage", "visual")


@dataclass(frozen=True)
class ExplorationVerdict(BaseVerdict):
    """The shared verdict base plus the four FR-017 per-criterion booleans."""

    hat_coverage_ok: bool = False
    pov_legible: bool = False
    distinctness_ok: bool = False
    visual_ok: bool = False


def parse_exploration_verdict(raw: str) -> ExplorationVerdict:
    """Parse the exploration checker's bare-JSON output. Malformed → `CheckerVerdictError`."""
    candidate = _extract_json_object(raw)
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise CheckerVerdictError(f"malformed checker JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise CheckerVerdictError(f"checker JSON was not an object: {type(data).__name__}")
    return ExplorationVerdict(
        can_state_what=_as_bool(data.get("can_state_what")),
        missing=_as_str_tuple(data.get("missing")),
        issues=_as_issues(data.get("issues")),
        score=_as_float(data.get("score")),
        rework_feedback=_as_str_tuple(data.get("rework_feedback")),
        contract=str(data.get("contract") or CHECKER_CONTRACT),
        hat_coverage_ok=_as_bool(data.get("hat_coverage_ok")),
        pov_legible=_as_bool(data.get("pov_legible")),
        distinctness_ok=_as_bool(data.get("distinctness_ok")),
        visual_ok=_as_bool(data.get("visual_ok")),
    )


def derive_pass(v: ExplorationVerdict) -> bool:
    """Binary PASS: the generic gate AND all four FR-017 per-criterion booleans clear."""
    if not _derive_pass(v, GATED_TOKENS):
        return False
    return v.hat_coverage_ok and v.pov_legible and v.distinctness_ok and v.visual_ok


def canonical_score(v: ExplorationVerdict) -> float:
    return _canonical_score(v)
