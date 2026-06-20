"""The code-owned gate for the v3 quality checker (sp4a-1).

`cast-requirements-render-checker` emits ONE bare-JSON verdict grading comprehension **and**
visual quality in a single pass. This module parses that verdict and **computes the binary PASS
and the canonical ranking score CODE-SIDE** — the agent never decides its own gate (the FR-010
"the gate is the boolean" discipline, here extended to the visual dimension AND to best-attempt
ranking). A judge that emits a flattering `score` float, or that is charitable about an `error`,
can never flip the gate or skew the rank: `derive_pass` and `canonical_score` recompute from the
structured fields, not from the agent's self-assessment.

**Refactor (exploration-pipeline-nxm sub-phase 4, Decision 2A):** the GENERIC verdict machinery —
the JSON-object salvage, the value coercers, the preso score weights + `canonical_score` math, and
the `derive_pass` logic generalized over a gated-token vocabulary — now lives in
`cast_server.render_common.verdict`, shared with the exploration render-checker. This module keeps
its requirements-specific SURFACE (the `restated_*` cold-reader fields, `GATED_TOKENS`,
`CHECKER_CONTRACT`) and re-exports the shared names so callers' import paths are byte-unchanged.

Pure by discipline, beside `maker_gate.py`: no I/O, no DB, no LLM, no subprocess. The service
layer (`render_job_service.py`, sp4a-2) owns the subprocess dispatch and maps a `parse_verdict`
raise to checker-unavailable handling — this module only ever turns a *string* into a verdict and
two derived values.

Scoring convention (the preso convention, shared with `cast-requirements-checker`):
``1.0 − 0.15·errors − 0.05·warnings``, floored at 0.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from cast_server.render_common.verdict import (
    SEVERITY_ERROR,
    SEVERITY_WARNING,
    CheckerIssue,
    CheckerVerdictError,
    _as_bool,
    _as_float,
    _as_issues,
    _as_str,
    _as_str_tuple,
    _extract_json_object,
)
from cast_server.render_common.verdict import canonical_score as _canonical_score
from cast_server.render_common.verdict import derive_pass as _derive_pass

# --------------------------------------------------------------------------------------
# Module constants — one source of truth the test AND the agent prompt reference
# --------------------------------------------------------------------------------------
#: The contract id the agent stamps on a v1 verdict (advisory provenance, not gate input).
CHECKER_CONTRACT = "cast-requirements-render-checker/v1"

#: The gated WHAT pieces. A `missing[]` entry naming any of these fails the binary gate — the same
#: tokens the v2 `cast-requirements-checker` / `eval_render_checker._GATED_PIECES` gate on.
GATED_TOKENS: tuple[str, ...] = ("job", "outcome", "scope")

#: The two issue dimensions (carried for observability; the gate treats both the same — an `error`
#: in either dimension blocks).
DIMENSION_COMPREHENSION = "comprehension"
DIMENSION_VISUAL = "visual"

# Re-exported so existing `from ...checker_verdict import CheckerVerdictError` / CheckerIssue paths
# and the SEVERITY_* constants keep resolving (the shape moved to render_common; names unchanged).
__all__ = [
    "CHECKER_CONTRACT", "GATED_TOKENS", "DIMENSION_COMPREHENSION", "DIMENSION_VISUAL",
    "SEVERITY_ERROR", "SEVERITY_WARNING", "CheckerIssue", "CheckerVerdict",
    "CheckerVerdictError", "parse_verdict", "derive_pass", "canonical_score",
]


# --------------------------------------------------------------------------------------
# CheckerVerdict — the requirements verdict shape (adds the cold-reader restated_* fields)
# --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class CheckerVerdict:
    """The parsed verdict — a strict superset of the v2 SC-001 cold-reader shape.

    The v2 fields (`can_state_what`, `restated_*`, `missing`, `score`, `issues`) keep their exact
    names and semantics; `issues[]` carries `dimension`/`evidence` and `rework_feedback[]` is new.
    `score` is the **agent-emitted** float and is advisory only — `canonical_score()` recomputes
    the value the service actually ranks on.
    """

    can_state_what: bool
    restated_job: str
    restated_outcome: str
    restated_scope: dict[str, list[str]]
    missing: tuple[str, ...]
    issues: tuple[CheckerIssue, ...]
    score: float
    rework_feedback: tuple[str, ...]
    contract: str = CHECKER_CONTRACT

    @property
    def error_issues(self) -> tuple[CheckerIssue, ...]:
        return tuple(i for i in self.issues if i.is_error)

    @property
    def warning_issues(self) -> tuple[CheckerIssue, ...]:
        return tuple(i for i in self.issues if i.is_warning)


def _as_scope(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {"in": [], "out": []}

    def _side(key: str) -> list[str]:
        side = value.get(key)
        return [str(v) for v in side] if isinstance(side, list) else []

    return {"in": _side("in"), "out": _side("out")}


def parse_verdict(raw: str) -> CheckerVerdict:
    """Parse a checker's bare-JSON output into a `CheckerVerdict`.

    Tolerant of code fences and chatty wrappers (the salvage precedent). Genuinely malformed JSON,
    or output with no JSON object at all, raises `CheckerVerdictError` — the parser never invents a
    verdict from garbage; the service layer treats the raise as checker-unavailable."""
    candidate = _extract_json_object(raw)
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise CheckerVerdictError(f"malformed checker JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise CheckerVerdictError(f"checker JSON was not an object: {type(data).__name__}")

    return CheckerVerdict(
        can_state_what=_as_bool(data.get("can_state_what")),
        restated_job=_as_str(data.get("restated_job")),
        restated_outcome=_as_str(data.get("restated_outcome")),
        restated_scope=_as_scope(data.get("restated_scope")),
        missing=_as_str_tuple(data.get("missing")),
        issues=_as_issues(data.get("issues")),
        score=_as_float(data.get("score")),
        rework_feedback=_as_str_tuple(data.get("rework_feedback")),
        contract=_as_str(data.get("contract")) or CHECKER_CONTRACT,
    )


# --------------------------------------------------------------------------------------
# derive_pass / canonical_score — thin requirements-flavored wrappers over render_common
# --------------------------------------------------------------------------------------
def derive_pass(v: CheckerVerdict) -> bool:
    """The binary quality PASS, computed code-side over the requirements `GATED_TOKENS`.

    PASS iff ALL of: `can_state_what` is True; no `missing[]` entry names a gated WHAT token
    (`job`/`outcome`/`scope`); zero `severity:"error"` issues in EITHER dimension. Warnings NEVER
    block. Generic logic lives in `render_common.verdict.derive_pass`; this binds `GATED_TOKENS`.

    Note: this is the *quality* PASS only. A **clean** publish additionally requires structural
    validity from `maker_gate` — that join lives in `decide_quality` (sp4a-2), not here."""
    return _derive_pass(v, GATED_TOKENS)


def canonical_score(v: CheckerVerdict) -> float:
    """Recompute the ranking score from issue counts (``1.0 − 0.15·errors − 0.05·warnings``,
    floored at 0.0). Delegates to `render_common.verdict.canonical_score`; the agent-emitted
    `v.score` is ignored on purpose."""
    return _canonical_score(v)
