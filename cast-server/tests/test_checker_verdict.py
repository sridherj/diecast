"""Unit tests for the code-owned quality gate (sp4a-1).

`checker_verdict.py` is the acceptance machinery for the v3 quality loop: it turns the checker
agent's bare-JSON verdict into the binary PASS and the canonical ranking score, **code-side**, so
judge variance can never flip the gate or skew the rank. So it is not rubber-stamp tested — there
is ≥1 fixture per terminal outcome the plan enumerates:

- a clean pass → `derive_pass` True, `canonical_score` 1.0;
- fail-on-gated-missing (`missing` names `outcome`) → `derive_pass` False;
- fail-on-error-issue (one `severity:"error"` visual issue, `can_state_what` True, no missing) →
  `derive_pass` False — the error-issue extension over the v2 boolean;
- warnings-only → `derive_pass` True (warnings never block) + `canonical_score` reflects `−0.05·w`;
- malformed JSON → `parse_verdict` raises;
- fenced / chatty wrapper around valid JSON → salvaged and parsed;
- `canonical_score` recomputed independent of the agent-emitted `score` (flattering 1.0 + two
  errors → recomputed 0.7).
"""
from __future__ import annotations

import json

import pytest

from cast_server.requirements_render.checker_verdict import (
    CHECKER_CONTRACT,
    GATED_TOKENS,
    CheckerVerdict,
    CheckerVerdictError,
    canonical_score,
    derive_pass,
    parse_verdict,
)


# ======================================================================================
# Verdict builders — a clean baseline JSON dict the cases mutate
# ======================================================================================
def _clean_verdict_dict() -> dict:
    """A passing verdict: WHAT stateable, nothing missing, no issues."""
    return {
        "contract": CHECKER_CONTRACT,
        "can_state_what": True,
        "restated_job": "Render requirements per work-family so a cold reader gets it.",
        "restated_outcome": "A page that beats the plain render on comprehension and looks shippable.",
        "restated_scope": {"in": ["per-family render"], "out": ["the diff agent"]},
        "missing": [],
        "issues": [],
        "score": 1.0,
        "rework_feedback": [],
    }


def _dump(d: dict) -> str:
    return json.dumps(d)


# ======================================================================================
# parse_verdict — shape + tolerant extraction
# ======================================================================================
def test_parse_clean_verdict_round_trips_fields():
    v = parse_verdict(_dump(_clean_verdict_dict()))
    assert isinstance(v, CheckerVerdict)
    assert v.can_state_what is True
    assert v.contract == CHECKER_CONTRACT
    assert v.missing == ()
    assert v.issues == ()
    assert v.rework_feedback == ()
    assert v.restated_scope == {"in": ["per-family render"], "out": ["the diff agent"]}


def test_parse_salvages_fenced_and_chatty_wrapper():
    """A ```json fence + leading/trailing prose is tolerated (the _parse_verdict_json precedent)."""
    raw = (
        "Sure — here is my verdict:\n\n```json\n"
        + _dump(_clean_verdict_dict())
        + "\n```\nLet me know if you need anything else."
    )
    v = parse_verdict(raw)
    assert v.can_state_what is True
    assert v.contract == CHECKER_CONTRACT


def test_parse_salvages_bare_chatty_without_fence():
    raw = "My final answer: " + _dump(_clean_verdict_dict()) + " (done)"
    v = parse_verdict(raw)
    assert v.can_state_what is True


def test_parse_issue_carries_dimension_and_evidence():
    d = _clean_verdict_dict()
    d["issues"] = [
        {
            "dimension": "visual",
            "criterion": "whitespace-breathes",
            "severity": "warning",
            "description": "Cramped evidence section.",
            "evidence": "Three tables stack with no margin.",
        }
    ]
    v = parse_verdict(_dump(d))
    assert len(v.issues) == 1
    issue = v.issues[0]
    assert issue.dimension == "visual"
    assert issue.evidence == "Three tables stack with no margin."
    assert issue.is_warning and not issue.is_error


def test_malformed_json_raises():
    with pytest.raises(CheckerVerdictError):
        parse_verdict("{ this is not valid json , , }")


def test_no_json_object_raises():
    with pytest.raises(CheckerVerdictError):
        parse_verdict("I could not produce a verdict.")


def test_non_object_json_raises():
    # Valid JSON, but a list — there is no `{ … }` object to extract, so it raises.
    with pytest.raises(CheckerVerdictError):
        parse_verdict("[1, 2, 3]")


# ======================================================================================
# derive_pass — the binary gate, code-side
# ======================================================================================
def test_clean_verdict_passes():
    v = parse_verdict(_dump(_clean_verdict_dict()))
    assert derive_pass(v) is True


def test_fail_on_gated_missing_outcome():
    d = _clean_verdict_dict()
    d["can_state_what"] = False
    d["missing"] = ["outcome"]
    v = parse_verdict(_dump(d))
    assert derive_pass(v) is False


def test_fail_on_gated_missing_substring_match():
    """`missing` entries are matched by gated-token substring, not exact equality."""
    d = _clean_verdict_dict()
    d["can_state_what"] = True  # WHAT technically restate-able...
    d["missing"] = ["the in/out scope is unclear"]  # ...but `scope` named ⇒ gate fails
    v = parse_verdict(_dump(d))
    assert any(tok in "the in/out scope is unclear" for tok in GATED_TOKENS)
    assert derive_pass(v) is False


def test_fail_on_error_issue_even_when_what_is_stateable():
    """The v3 extension over the v2 boolean: an `error` issue fails an otherwise-stateable page."""
    d = _clean_verdict_dict()
    d["can_state_what"] = True
    d["missing"] = []
    d["issues"] = [
        {
            "dimension": "visual",
            "criterion": "not-ai-aesthetic",
            "severity": "error",
            "description": "Reads as generic AI slop — uniform centered cards, no hierarchy.",
            "evidence": "Every section is an identical centered card.",
        }
    ]
    d["rework_feedback"] = ["Give the page a point of view: vary card layout, add a hierarchy spine."]
    v = parse_verdict(_dump(d))
    assert derive_pass(v) is False


def test_comprehension_error_also_blocks():
    d = _clean_verdict_dict()
    d["issues"] = [
        {
            "dimension": "comprehension",
            "criterion": "section-outcomes-land",
            "severity": "error",
            "description": "Sections reflow raw FR rows with no takeaway.",
            "evidence": "The 'Decisions' section is a bulleted dump of FR-001..FR-009.",
        }
    ]
    d["rework_feedback"] = ["Lead each section with its one takeaway before the supporting detail."]
    v = parse_verdict(_dump(d))
    assert derive_pass(v) is False


def test_warnings_only_passes():
    d = _clean_verdict_dict()
    d["issues"] = [
        {
            "dimension": "visual",
            "criterion": "anchor-labels-unobtrusive",
            "severity": "warning",
            "description": "Anchor labels are a touch loud.",
            "evidence": "FR-003 label is full-size body text.",
        },
        {
            "dimension": "visual",
            "criterion": "whitespace-breathes",
            "severity": "warning",
            "description": "Slightly cramped.",
            "evidence": "Tables abut.",
        },
    ]
    v = parse_verdict(_dump(d))
    assert derive_pass(v) is True  # warnings never block


# ======================================================================================
# canonical_score — recomputed code-side, never the agent's float
# ======================================================================================
def test_clean_verdict_scores_one():
    v = parse_verdict(_dump(_clean_verdict_dict()))
    assert canonical_score(v) == pytest.approx(1.0)


def test_warnings_only_score_reflects_warning_term():
    d = _clean_verdict_dict()
    d["issues"] = [
        {"dimension": "visual", "criterion": "whitespace-breathes", "severity": "warning",
         "description": "x", "evidence": "y"},
        {"dimension": "visual", "criterion": "anchor-labels-unobtrusive", "severity": "warning",
         "description": "x", "evidence": "y"},
    ]
    v = parse_verdict(_dump(d))
    # 1.0 − 0.05·2 = 0.9
    assert canonical_score(v) == pytest.approx(0.9)


def test_score_recomputed_independent_of_agent_float():
    """A flattering agent `score:1.0` with two error issues recomputes to 0.7 — not the float."""
    d = _clean_verdict_dict()
    d["score"] = 1.0  # the agent tries to game its own gate
    d["issues"] = [
        {"dimension": "visual", "criterion": "not-generic", "severity": "error",
         "description": "x", "evidence": "y"},
        {"dimension": "comprehension", "criterion": "scannable-not-wall", "severity": "error",
         "description": "x", "evidence": "y"},
    ]
    d["rework_feedback"] = ["fix a", "fix b"]
    v = parse_verdict(_dump(d))
    assert v.score == pytest.approx(1.0)  # the advisory float is preserved verbatim...
    assert canonical_score(v) == pytest.approx(0.7)  # ...but ranking uses the recompute: 1−0.15·2
    assert derive_pass(v) is False  # and the gate still fails on the error issues


def test_score_floors_at_zero():
    d = _clean_verdict_dict()
    d["issues"] = [
        {"dimension": "visual", "criterion": "not-generic", "severity": "error",
         "description": "x", "evidence": "y"}
        for _ in range(10)  # 10 errors ⇒ 1.0 − 1.5 = −0.5, floored to 0.0
    ]
    d["rework_feedback"] = ["fix"]
    v = parse_verdict(_dump(d))
    assert canonical_score(v) == 0.0
