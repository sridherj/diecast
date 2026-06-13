"""The code-owned gate for the v3 quality checker (sp4a-1).

`cast-requirements-render-checker` emits ONE bare-JSON verdict grading comprehension **and**
visual quality in a single pass. This module parses that verdict and **computes the binary PASS
and the canonical ranking score CODE-SIDE** — the agent never decides its own gate (the FR-010
"the gate is the boolean" discipline, here extended to the visual dimension AND to best-attempt
ranking). A judge that emits a flattering `score` float, or that is charitable about an `error`,
can never flip the gate or skew the rank: `derive_pass` and `canonical_score` recompute from the
structured fields, not from the agent's self-assessment.

Pure by discipline, beside `maker_gate.py`: no I/O, no DB, no LLM, no subprocess. The service
layer (`render_job_service.py`, sp4a-2) owns the subprocess dispatch and maps a `parse_verdict`
raise to checker-unavailable handling — this module only ever turns a *string* into a verdict and
two derived values.

Trust-boundary note (shared context): the checker owns the *reader's experience* (can a cold
reader state the WHAT; does the page look like quality work). Fidelity to the source — id parity,
verbatim carriage, the DOM contract — is `maker_gate`'s job. Nothing here consults the source; the
verdict is computed from the agent's report of the rendered artifact alone.

Scoring convention (the preso convention, shared with `cast-requirements-checker`):
``1.0 − 0.15·errors − 0.05·warnings``, floored at 0.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

# --------------------------------------------------------------------------------------
# Module constants — one source of truth the test AND the agent prompt reference
# --------------------------------------------------------------------------------------
#: The contract id the agent stamps on a v1 verdict (advisory provenance, not gate input).
CHECKER_CONTRACT = "cast-requirements-render-checker/v1"

#: The gated WHAT pieces. A `missing[]` entry naming any of these fails the binary gate — the same
#: tokens the v2 `cast-requirements-checker` / `eval_render_checker._GATED_PIECES` gate on.
GATED_TOKENS: tuple[str, ...] = ("job", "outcome", "scope")

#: The two severities. `error` blocks the gate; `warning` is taste-variance that must never block.
SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"

#: The two issue dimensions (carried for observability; the gate treats both the same — an `error`
#: in either dimension blocks).
DIMENSION_COMPREHENSION = "comprehension"
DIMENSION_VISUAL = "visual"

#: Preso scoring weights (recomputed code-side; the agent-emitted float is advisory only).
_SCORE_ERROR_WEIGHT = 0.15
_SCORE_WARNING_WEIGHT = 0.05


# --------------------------------------------------------------------------------------
# CheckerIssue / CheckerVerdict — the frozen value shapes mirroring the JSON contract
# --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class CheckerIssue:
    """One graded issue. `dimension` + `evidence` are the v3 additions over the v2 issue shape."""

    dimension: str
    criterion: str
    severity: str
    description: str
    evidence: str = ""

    @property
    def is_error(self) -> bool:
        return self.severity == SEVERITY_ERROR

    @property
    def is_warning(self) -> bool:
        return self.severity == SEVERITY_WARNING


@dataclass(frozen=True)
class CheckerVerdict:
    """The parsed verdict — a strict superset of the v2 SC-001 cold-reader shape.

    The v2 fields (`can_state_what`, `restated_*`, `missing`, `score`, `issues`) keep their exact
    names and semantics; `issues[]` gains `dimension`/`evidence` and `rework_feedback[]` is new.
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


# --------------------------------------------------------------------------------------
# parse_verdict — tolerant extraction; malformed RAISES (never coerced into a verdict)
# --------------------------------------------------------------------------------------
class CheckerVerdictError(ValueError):
    """Raised when the agent output cannot be parsed into a verdict. The service layer maps this
    to checker-unavailable handling — the parser NEVER coerces garbage into a verdict."""


def _extract_json_object(raw: str) -> str:
    """Pull the single bare JSON object out of possibly-fenced / chatty output.

    Reuses the `eval_render_checker._parse_verdict_json` salvage pattern: tolerate a leading code
    fence and surrounding prose, then take the outermost `{ … }`. A genuinely object-less string
    raises (the caller turns that into checker-unavailable)."""
    if raw is None:
        raise CheckerVerdictError("checker output was None")
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        brace = text.find("{")
        if brace != -1:
            text = text[brace:]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise CheckerVerdictError(f"no JSON object in checker output: {raw[:200]!r}")
    return text[start : end + 1]


def _as_bool(value: Any) -> bool:
    return value is True


def _as_str(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _as_str_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(v) for v in value)


def _as_scope(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {"in": [], "out": []}

    def _side(key: str) -> list[str]:
        side = value.get(key)
        return [str(v) for v in side] if isinstance(side, list) else []

    return {"in": _side("in"), "out": _side("out")}


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _as_issues(value: Any) -> tuple[CheckerIssue, ...]:
    if not isinstance(value, list):
        return ()
    issues: list[CheckerIssue] = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        issues.append(
            CheckerIssue(
                dimension=_as_str(entry.get("dimension")),
                criterion=_as_str(entry.get("criterion")),
                severity=_as_str(entry.get("severity")),
                description=_as_str(entry.get("description")),
                evidence=_as_str(entry.get("evidence")),
            )
        )
    return tuple(issues)


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
# derive_pass — the binary PASS, code-side (extends the v2 boolean with the error-issue rule)
# --------------------------------------------------------------------------------------
def _missing_names_gated_token(missing: tuple[str, ...]) -> bool:
    """True if any `missing[]` entry contains a gated WHAT token (`job`/`outcome`/`scope`)."""
    return any(
        token in str(entry).lower() for entry in missing for token in GATED_TOKENS
    )


def derive_pass(v: CheckerVerdict) -> bool:
    """The binary quality PASS, computed code-side.

    PASS iff ALL of:
      - `can_state_what` is True, AND
      - no `missing[]` entry names a gated WHAT token (`job`/`outcome`/`scope`), AND
      - zero `severity:"error"` issues in EITHER dimension.

    Warnings NEVER block (judge taste-variance must not churn the loop). This is the v2 SC-001
    boolean (`can_state_what` + gated-missing) extended with the zero-error-issue rule, so a
    real visual or comprehension `error` fails a render whose WHAT is technically restate-able.

    Note: this is the *quality* PASS only. A **clean** publish additionally requires structural
    validity from `maker_gate` — that join lives in `decide_quality` (sp4a-2), not here."""
    if not v.can_state_what:
        return False
    if _missing_names_gated_token(v.missing):
        return False
    if v.error_issues:
        return False
    return True


# --------------------------------------------------------------------------------------
# canonical_score — recomputed code-side from issue counts (never the agent's float)
# --------------------------------------------------------------------------------------
def canonical_score(v: CheckerVerdict) -> float:
    """Recompute the ranking score from issue counts — the value best-attempt ranking uses.

    ``1.0 − 0.15·errors − 0.05·warnings``, floored at 0.0 (the preso convention). The
    agent-emitted `v.score` is **ignored** here on purpose: a judge cannot skew best-attempt
    ranking by emitting a flattering float."""
    errors = len(v.error_issues)
    warnings = len(v.warning_issues)
    raw = 1.0 - (_SCORE_ERROR_WEIGHT * errors) - (_SCORE_WARNING_WEIGHT * warnings)
    return max(0.0, raw)
