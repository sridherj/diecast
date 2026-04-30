"""Minimal deterministic harness for B1 (Domain Web Search) tests.

The full cast-refine-requirements agent is LLM-driven and not unit-testable
in-process. This harness mirrors the trigger heuristic encoded in the
`Step 2.2.1: Domain Web Search` section of
`agents/cast-refine-requirements/cast-refine-requirements.md` so the rule
itself can be exercised deterministically. The mirror is explicit — see the
SPEC_ANCHOR docstring below — and the prompt-side regression tests guard
against drift between the prompt and this Python mirror.

When the prompt's trigger heuristic changes, this module MUST be updated to
match (and vice versa). The B1 tests assert both halves.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional

# SPEC_ANCHOR: keep this list in sync with the positive examples in
# agents/cast-refine-requirements/cast-refine-requirements.md
# § "Step 2.2.1: Domain Web Search".
PRODUCT_CATEGORY_KEYWORDS: tuple[str, ...] = (
    "task tracking",
    "project management",
    "pm tool",
    "feature flag",
    "feature-flag",
    "analytics platform",
    "observability",
    "design system",
    "error tracking",
    "ci provider",
    "ci/cd provider",
    "ux",
)

# SPEC_ANCHOR: negative examples — internal/technical questions that must
# NOT trigger a web search. Pattern-only; not exhaustive.
NEGATIVE_PATTERNS: tuple[str, ...] = (
    r"\bpost\b.*\bput\b",
    r"\bput\b.*\bpost\b",
    r"primary key",
    r"how many retries",
    r"\bnullable\b",
)


@dataclass
class WebSearchCall:
    tool: str
    query: str


@dataclass
class RenderedQuestion:
    question: str
    evidence: str  # "grounded rationale" line per cast-interactive-questions


@dataclass
class InteractionTrace:
    """Captures what the harness did for one Phase-2 question."""

    calls: List[WebSearchCall] = field(default_factory=list)
    last_ask_user_question: Optional[RenderedQuestion] = None

    def __iter__(self):
        return iter(self.calls)


# ---------------------------------------------------------------------------
# Trigger heuristic — Python mirror of the prompt rule
# ---------------------------------------------------------------------------


def should_search(question_text: str) -> bool:
    """Return True iff the question references a product-category keyword
    AND does not match a negative pattern.

    Mirrors the prompt's Step 2.2.1 trigger heuristic.
    """
    text = question_text.lower()
    for pattern in NEGATIVE_PATTERNS:
        if re.search(pattern, text):
            return False
    return any(kw in text for kw in PRODUCT_CATEGORY_KEYWORDS)


def derive_query(question_text: str) -> str:
    """Pick a short, year-tagged query for the matched category."""
    text = question_text.lower()
    for kw in PRODUCT_CATEGORY_KEYWORDS:
        if kw in text:
            return f"best {kw} 2026"
    return "best tools 2026"


# ---------------------------------------------------------------------------
# Pluggable WebSearch tool (real or stubbed in tests)
# ---------------------------------------------------------------------------

WebSearchFn = Callable[[str], List[dict]]


def _empty_websearch(_query: str) -> List[dict]:
    return []


# ---------------------------------------------------------------------------
# Prebaked fixtures (no LLM involved — purely the trigger + render rule)
# ---------------------------------------------------------------------------

_FIXTURES = {
    "b1_positive_pm_question": (
        "What task tracking tool should we model the UX after?",
        [
            "Option A — Linear-style command bar (Recommended)",
            "Option B — Jira-style hierarchical issues",
        ],
    ),
    "b1_negative_internal_question": (
        "Should we use POST or PUT for the update endpoint?",
        ["Option A — POST (Recommended)", "Option B — PUT"],
    ),
}


def _render(
    question: str,
    rationale_seed: str,
    websearch_results: List[dict],
    websearch_failed: bool,
) -> RenderedQuestion:
    """Build the rendered question + evidence line.

    Mirrors the prompt's "Evidence rendering" + "Failure handling" rules.
    """
    if websearch_failed or not websearch_results:
        evidence = (
            f"{rationale_seed} "
            "(unable to find product references; recommendation is from training data)"
        )
        return RenderedQuestion(question=question, evidence=evidence)
    top = websearch_results[0]
    url = top.get("url", "")
    snippet = top.get("snippet", "")
    evidence = f"{rationale_seed} See {url} — {snippet}"
    return RenderedQuestion(question=question, evidence=evidence)


def run_cast_refine_with_fixture(
    fixture_id: str,
    websearch: WebSearchFn = _empty_websearch,
) -> InteractionTrace:
    """Drive the trigger heuristic against a named fixture.

    `websearch` is the (possibly stubbed) WebSearch callable. Tests pass a
    cassette-replaying stub or a raising stub for the failure path.
    """
    if fixture_id not in _FIXTURES:
        raise KeyError(f"unknown B1 fixture: {fixture_id}")
    question_text, _options = _FIXTURES[fixture_id]
    trace = InteractionTrace()
    rationale_seed = "Recommended option grounded in the dominant real-world reference."

    if not should_search(question_text):
        trace.last_ask_user_question = RenderedQuestion(
            question=question_text,
            evidence=rationale_seed,  # no URL, no failure note — purely internal call
        )
        return trace

    query = derive_query(question_text)
    websearch_failed = False
    results: List[dict] = []
    try:
        results = websearch(query) or []
    except Exception:
        websearch_failed = True
    trace.calls.append(WebSearchCall(tool="WebSearch", query=query))
    trace.last_ask_user_question = _render(
        question_text, rationale_seed, results, websearch_failed
    )
    return trace
