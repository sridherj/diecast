"""B1 Domain Web Search — prompt + trigger-heuristic regression tests.

Covers three behaviors documented in
`agents/cast-refine-requirements/cast-refine-requirements.md`
§ "Step 2.2.1: Domain Web Search":

  1. Positive — a product-reference question fires a WebSearch and the
     rendered evidence line cites the source URL.
  2. Negative — an internal/technical question fires zero WebSearch calls.
  3. Failure — WebSearch raising/empty falls back to an explanatory
     ungrounded recommendation; the question still renders.

Plus prompt-artifact regression guards (Issue #14: numeric caps must NOT
be re-introduced; positive + negative examples MUST stay documented).

The full cast-refine agent is LLM-driven; these tests exercise the trigger
heuristic via the deterministic mirror in `tests/helpers/refine_harness.py`.
The `SPEC_ANCHOR` docstrings in that module document the prompt-side source
of truth.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tests.helpers.refine_harness import (  # noqa: E402
    PRODUCT_CATEGORY_KEYWORDS,
    run_cast_refine_with_fixture,
)

PROMPT_PATH = (
    REPO_ROOT
    / "agents"
    / "cast-refine-requirements"
    / "cast-refine-requirements.md"
)
CASSETTE_PATH = REPO_ROOT / "tests" / "fixtures" / "b1_websearch_cassette.yaml"


# ---------------------------------------------------------------------------
# Cassette loader (no vcrpy dependency)
# ---------------------------------------------------------------------------


def _load_cassette() -> list[dict]:
    """Return the recorded `results` list from the first interaction."""
    data = yaml.safe_load(CASSETTE_PATH.read_text())
    return data["interactions"][0]["response"]["body"]["results"]


@pytest.fixture
def websearch_cassette():
    results = _load_cassette()

    def _stub(_query: str) -> list[dict]:
        return results

    return _stub


# ---------------------------------------------------------------------------
# Behavior tests — trigger heuristic
# ---------------------------------------------------------------------------


def test_b1_positive_search_cites_url(websearch_cassette):
    """PM-reference question → at least one WebSearch + URL in evidence."""
    trace = run_cast_refine_with_fixture(
        "b1_positive_pm_question", websearch=websearch_cassette
    )
    websearch_calls = [c for c in trace if c.tool == "WebSearch"]
    assert len(websearch_calls) >= 1, "expected ≥1 WebSearch call"
    assert any("task tracking" in c.query.lower() for c in websearch_calls)
    rendered = trace.last_ask_user_question
    assert rendered is not None
    assert "https://" in rendered.evidence, (
        "evidence line must cite a source URL when grounded in search"
    )


def test_b1_negative_no_search_for_internal_question():
    """POST-vs-PUT-style question → zero WebSearch calls."""
    trace = run_cast_refine_with_fixture("b1_negative_internal_question")
    websearch_calls = [c for c in trace if c.tool == "WebSearch"]
    assert websearch_calls == [], (
        "internal/technical questions must not trigger WebSearch"
    )
    rendered = trace.last_ask_user_question
    assert rendered is not None
    assert "https://" not in rendered.evidence


def test_b1_websearch_failure_falls_back_ungrounded():
    """Network error → ungrounded recommendation + explanatory note."""

    def raising_websearch(_query: str):
        raise RuntimeError("network down")

    trace = run_cast_refine_with_fixture(
        "b1_positive_pm_question", websearch=raising_websearch
    )
    rendered = trace.last_ask_user_question
    assert rendered is not None
    # The question still rendered — the failure did NOT fail the question.
    assert rendered.question
    assert "unable to find product references" in rendered.evidence


# ---------------------------------------------------------------------------
# Prompt-artifact regression guards
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def prompt_text() -> str:
    return PROMPT_PATH.read_text()


def test_prompt_contains_domain_web_search_section(prompt_text):
    assert "Domain Web Search" in prompt_text, (
        "Domain Web Search section missing from cast-refine-requirements.md"
    )


def test_prompt_documents_negative_examples(prompt_text):
    """Negative examples are load-bearing without numeric caps."""
    assert "DO NOT search" in prompt_text


def test_prompt_no_numeric_caps_reintroduced(prompt_text):
    """Issue #14: per-question / per-conversation numeric caps were dropped.

    Guard against drift if a future contributor adds them back. The regex
    flags any "per-X cap/limit" mention; we then drop matches that are
    explicitly negated ("no", "not", "without", "dropped") within the
    preceding 40 characters so the prompt's own "no caps" rationale
    doesn't trip the guard.
    """
    forbidden = re.compile(
        r"(.{0,40})(per[- ](?:question|conversation).{0,30}"
        r"(?:cap|limit|max(?:imum)?|\b\d+\b))",
        re.IGNORECASE | re.DOTALL,
    )
    negation = re.compile(
        r"\b(no|not|without|drop(?:ped)?|never|zero)\b",
        re.IGNORECASE,
    )
    real_hits = [
        match
        for prefix, match in forbidden.findall(prompt_text)
        if not negation.search(prefix)
    ]
    assert real_hits == [], (
        f"numeric caps appear to have been re-introduced (matches: {real_hits!r}); "
        "see plan-review Issue #14 — trigger heuristic is the cost guard"
    )


def test_prompt_lists_at_least_five_positive_categories(prompt_text):
    """Worked examples cover ≥5 product categories (success criterion)."""
    section_marker = "DO search"
    assert section_marker in prompt_text
    section = prompt_text.split(section_marker, 1)[1].split("DO NOT search", 1)[0]
    bullet_lines = [
        line for line in section.splitlines() if line.lstrip().startswith("-")
    ]
    assert len(bullet_lines) >= 5, (
        f"expected ≥5 positive examples, found {len(bullet_lines)}"
    )


def test_harness_keyword_list_overlaps_prompt(prompt_text):
    """Sanity: the Python mirror cites at least a few keywords that appear
    in the prompt's positive-examples block. Drift between prompt and
    mirror is the failure mode this guards against.
    """
    overlap = [kw for kw in PRODUCT_CATEGORY_KEYWORDS if kw in prompt_text.lower()]
    assert len(overlap) >= 4, (
        "Python trigger mirror has drifted from prompt; "
        f"only {len(overlap)} keywords are still referenced in the prompt"
    )
