"""The generic checker-verdict schema base, shared by both render-jobs.

A render-checker (requirements or exploration) emits ONE bare-JSON verdict grading comprehension
AND visual quality in a single pass. This module owns the GENERIC parts: the JSON-object salvage,
the value coercers, the preso scoring weights + `canonical_score` math, a base verdict dataclass
carrying the common fields, and `derive_pass` generalized over a `gated_tokens` parameter.

Pure by discipline: no I/O, no DB, no LLM, no subprocess. The binary PASS and the canonical ranking
score are computed CODE-SIDE from the structured fields — never from the agent's self-assessed float
(FR-010 "the gate is the boolean"). A judge that emits a flattering `score`, or that is charitable
about an `error`, can never flip the gate or skew the rank.

Scoring convention (the preso convention): ``1.0 − 0.15·errors − 0.05·warnings``, floored at 0.

Each render-job builds its requirements/exploration-specific verdict ON TOP of this base — keeping
its own gated-token vocabulary, contract id, and any extra restated fields — without re-implementing
the coercers or the score math.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

#: The two severities. `error` blocks the gate; `warning` is taste-variance that must never block.
SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"

#: Preso scoring weights (recomputed code-side; the agent-emitted float is advisory only).
_SCORE_ERROR_WEIGHT = 0.15
_SCORE_WARNING_WEIGHT = 0.05


class CheckerVerdictError(ValueError):
    """Raised when the agent output cannot be parsed into a verdict. The service layer maps this
    to checker-unavailable handling — the parser NEVER coerces garbage into a verdict."""


@dataclass(frozen=True)
class CheckerIssue:
    """One graded issue. `dimension` tags the rubric axis; `evidence` is an optional citation."""

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
class BaseVerdict:
    """The fields EVERY render-checker verdict carries, the gate/score recompute over.

    A render-job subclass adds its own restated_* fields and a fixed `contract`/`gated_tokens`; the
    `can_state_what` / `missing` / `issues` / `score` / `rework_feedback` shape is shared.
    """

    can_state_what: bool
    missing: tuple[str, ...]
    issues: tuple[CheckerIssue, ...]
    score: float
    rework_feedback: tuple[str, ...]
    contract: str = ""

    @property
    def error_issues(self) -> tuple[CheckerIssue, ...]:
        return tuple(i for i in self.issues if i.is_error)

    @property
    def warning_issues(self) -> tuple[CheckerIssue, ...]:
        return tuple(i for i in self.issues if i.is_warning)


# --------------------------------------------------------------------------------------
# JSON-object salvage + value coercers (tolerant extraction; malformed RAISES)
# --------------------------------------------------------------------------------------
def _extract_json_object(raw: str | None) -> str:
    """Pull the single bare JSON object out of possibly-fenced / chatty output.

    Tolerate a leading code fence and surrounding prose, then take the outermost `{ … }`. A
    genuinely object-less string raises (the caller turns that into checker-unavailable)."""
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


# --------------------------------------------------------------------------------------
# derive_pass / canonical_score — code-side, generic over the gated-token vocabulary
# --------------------------------------------------------------------------------------
def missing_names_gated_token(missing: tuple[str, ...], gated_tokens: tuple[str, ...]) -> bool:
    """True if any `missing[]` entry contains one of `gated_tokens` (case-insensitive substring)."""
    return any(
        token in str(entry).lower() for entry in missing for token in gated_tokens
    )


def derive_pass(v: BaseVerdict, gated_tokens: tuple[str, ...]) -> bool:
    """The binary quality PASS, computed code-side, over a render-job's gated-token vocabulary.

    PASS iff ALL of:
      - `can_state_what` is True, AND
      - no `missing[]` entry names a gated token, AND
      - zero `severity:"error"` issues.

    Warnings NEVER block (judge taste-variance must not churn the loop). This is the *quality* PASS
    only — a clean publish additionally requires structural validity from the render-job's gate.
    """
    if not v.can_state_what:
        return False
    if missing_names_gated_token(v.missing, gated_tokens):
        return False
    if v.error_issues:
        return False
    return True


def canonical_score(v: BaseVerdict) -> float:
    """Recompute the ranking score from issue counts — the value best-attempt ranking uses.

    ``1.0 − 0.15·errors − 0.05·warnings``, floored at 0.0 (the preso convention). The agent-emitted
    `v.score` is IGNORED here on purpose: a judge cannot skew best-attempt ranking by a flattering
    float."""
    errors = len(v.error_issues)
    warnings = len(v.warning_issues)
    raw = 1.0 - (_SCORE_ERROR_WEIGHT * errors) - (_SCORE_WARNING_WEIGHT * warnings)
    return max(0.0, raw)
