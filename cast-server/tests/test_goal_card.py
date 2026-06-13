"""Unit tests for the Goal Card IA heuristics (Phase 3a, sp3, WP-C).

These exercise `goal_card.py` in **isolation** — no full render — because the SC-001 core
(the one job statement + the 3–5 assertions an unfamiliar reader restates in two minutes) is
information architecture, not CSS, and must be testable without a document (plan-review #3).

Inputs are built programmatically: a classification front-matter + the sections under test,
parsed through the real Phase 1 parser so the block model matches production exactly.
"""
from __future__ import annotations

import pytest

from cast_server.requirements_render.goal_card import (
    MAX_L2_ASSERTIONS,
    NO_JOB_STATEMENT_WARNING,
    derive_l2_assertions,
    extract_job_statement,
    strip_inline_markdown,
)
from cast_server.requirements_render.parser import parse_requirements


def _doc(*sections: str, title: str = "Example Goal") -> str:
    """A classified document with the given section blocks (each carrying its own H2)."""
    front = "---\nclassification:\n  family: new_initiative\n  confidence: 0.95\n---\n"
    return front + f"# {title}\n\n" + "\n\n".join(sections) + "\n"


def _sc_table(*criteria: str) -> str:
    rows = "\n".join(
        f"| SC-{i + 1:03d} | {c} | test |" for i, c in enumerate(criteria)
    )
    return "## Success Criteria\n\n| ID | Criterion | Measure |\n|---|---|---|\n" + rows


# --------------------------------------------------------------------------------------
# extract_job_statement
# --------------------------------------------------------------------------------------
def test_job_statement_prefers_bold_lead() -> None:
    intent = (
        "## Intent\n\nSome framing prose about the area we are working in.\n\n"
        "**Job statement:** Ship a read-only HTML render of refined requirements. "
        "More elaboration follows here that should not appear.\n"
    )
    parsed = parse_requirements(_doc(intent))
    statement, warning = extract_job_statement(parsed)

    assert statement == "Ship a read-only HTML render of refined requirements."
    assert warning is None


def test_job_statement_falls_back_to_first_sentence() -> None:
    intent = (
        "## Intent\n\nWe want to let an unfamiliar reader grasp a goal in two minutes. "
        "A second sentence adds detail we do not want as the headline.\n"
    )
    parsed = parse_requirements(_doc(intent))
    statement, warning = extract_job_statement(parsed)

    assert statement == "We want to let an unfamiliar reader grasp a goal in two minutes."
    assert warning is None


def test_job_statement_warns_and_uses_title_when_absent() -> None:
    # No Intent section at all ⇒ warn + fall back to the H1 title.
    parsed = parse_requirements(_doc(_sc_table("only an outcome"), title="My Bare Goal"))
    statement, warning = extract_job_statement(parsed)

    assert statement == "My Bare Goal"
    assert warning == NO_JOB_STATEMENT_WARNING


# --------------------------------------------------------------------------------------
# derive_l2_assertions
# --------------------------------------------------------------------------------------
def test_l2_assertions_priority_order() -> None:
    # SC rows come first (outcomes), then Out-of-Scope bullets (boundaries).
    doc = _doc(
        _sc_table("readers state the WHAT in two minutes"),
        "## Out of Scope\n\n- a human timed-read harness\n- illustration generation",
    )
    parsed = parse_requirements(doc)
    assertions = derive_l2_assertions(parsed)

    assert assertions[0] == "readers state the WHAT in two minutes"
    assert assertions[1] == "Out of scope: a human timed-read harness"
    assert assertions[2] == "Out of scope: illustration generation"


def test_l2_assertions_caps_at_5() -> None:
    doc = _doc(_sc_table(*[f"outcome number {n}" for n in range(8)]))
    parsed = parse_requirements(doc)
    assertions = derive_l2_assertions(parsed)

    assert len(assertions) == MAX_L2_ASSERTIONS == 5
    assert assertions == [f"outcome number {n}" for n in range(5)]


def test_l2_assertions_never_pads_when_sparse() -> None:
    # Only one SC row available ⇒ exactly one assertion, never padded up to three.
    parsed = parse_requirements(_doc(_sc_table("the single available outcome")))
    assertions = derive_l2_assertions(parsed)

    assert assertions == ["the single available outcome"]


def test_l2_assertions_intent_thread_fallback() -> None:
    # bug_fix / random_idea shape: no SC, no Out-of-Scope ⇒ Intent's numbered thread.
    intent = (
        "## Intent\n\nThe login page sometimes 500s. The thread:\n\n"
        "1. Users report intermittent failures.\n"
        "2. The session cookie is dropped on redirect.\n"
        "3. The fix restores the cookie before redirecting.\n"
    )
    parsed = parse_requirements(_doc(intent))
    assertions = derive_l2_assertions(parsed)

    assert assertions == [
        "Users report intermittent failures.",
        "The session cookie is dropped on redirect.",
        "The fix restores the cookie before redirecting.",
    ]


# --------------------------------------------------------------------------------------
# strip_inline_markdown — the pure helper (2a → 3b contract; imported by maker_gate.py)
# --------------------------------------------------------------------------------------
class TestStripInlineMarkdown:
    """Paired-delimiter stripping of inline markers to plain text — never rendered."""

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("**bold**", "bold"),
            ("__bold__", "bold"),
            ("*em*", "em"),
            ("_em_", "em"),
            ("`code`", "code"),
            ("[text](http://example.com)", "text"),
            ("a **b** and `c` and [d](u)", "a b and c and d"),
        ],
    )
    def test_each_marker_class_stripped(self, text: str, expected: str) -> None:
        assert strip_inline_markdown(text) == expected

    def test_unbalanced_marker_passes_through(self) -> None:
        # An unbalanced `**a` is not a paired delimiter ⇒ left untouched.
        assert strip_inline_markdown("**a") == "**a"

    def test_lone_marker_in_prose_untouched(self) -> None:
        # A lone literal `*` (e.g. `a * b`) must never be eaten.
        assert strip_inline_markdown("a * b") == "a * b"

    def test_nested_markers_fixpoint(self) -> None:
        # Nested strong+em iterate to a fixpoint: `**a *b* c**` → `a b c`.
        assert strip_inline_markdown("**a *b* c**") == "a b c"

    def test_cq2_parenthesized_url_degradation_pinned(self) -> None:
        # Known, accepted degradation: a parenthesized URL leaves a stray `)`. Pinned so it
        # can't silently worsen (and so a future "fix" is a conscious change).
        assert strip_inline_markdown("[t](http://x(y))") == "t)"

    def test_empty_string(self) -> None:
        assert strip_inline_markdown("") == ""


# --------------------------------------------------------------------------------------
# Honest fallback (FR-006): markers stripped on card text, abbreviations don't truncate
# --------------------------------------------------------------------------------------
def test_job_statement_strips_inline_markdown() -> None:
    # (a) A job statement carrying `**bold**` and `code` renders clean — no literal markers.
    intent = (
        "## Intent\n\n"
        "**Job statement:** Ship a **read-only** HTML render of `refined` requirements.\n"
    )
    parsed = parse_requirements(_doc(intent))
    statement, warning = extract_job_statement(parsed)

    assert statement == "Ship a read-only HTML render of refined requirements."
    assert "*" not in statement and "`" not in statement
    assert warning is None


def test_assertions_strip_inline_markdown_from_sc_cells() -> None:
    # (b) SC table cells carrying backticks/bold render clean as assertions.
    parsed = parse_requirements(
        _doc(_sc_table("readers restate the `WHAT` in **two** minutes"))
    )
    assertions = derive_l2_assertions(parsed)

    assert assertions == ["readers restate the WHAT in two minutes"]


# The actual dogfooding strings that surfaced the abbreviation-truncation defect.
@pytest.mark.parametrize(
    "abbreviation",
    ["vs.", "e.g.", "i.e.", "etc.", "30 min.", "cf.", "approx."],
)
def test_abbreviation_does_not_truncate_job_statement(abbreviation: str) -> None:
    # (c) An abbreviation mid-sentence must NOT end the statement; the real boundary later does.
    intent = (
        "## Intent\n\n"
        f"**Job statement:** Compare the two options {abbreviation} the baseline approach. "
        "A trailing sentence that must not appear.\n"
    )
    parsed = parse_requirements(_doc(intent))
    statement, _ = extract_job_statement(parsed)

    assert statement == f"Compare the two options {abbreviation} the baseline approach."
    assert "trailing sentence" not in statement


def test_real_boundary_still_splits() -> None:
    # The same paragraph's genuine `.` boundary still ends the sentence.
    intent = (
        "## Intent\n\n"
        "**Job statement:** Render it cleanly. The rest is elaboration we drop.\n"
    )
    parsed = parse_requirements(_doc(intent))
    statement, _ = extract_job_statement(parsed)

    assert statement == "Render it cleanly."


def test_cq3_parenthetical_abbreviation_normalized() -> None:
    # `(e.g.` opening a parenthetical is leading-punct-normalized to `e.g.` and not a boundary.
    intent = (
        "## Intent\n\n"
        "**Job statement:** Support common forms (e.g. JSON and YAML) for the input. "
        "Then a follow-up sentence.\n"
    )
    parsed = parse_requirements(_doc(intent))
    statement, _ = extract_job_statement(parsed)

    assert statement == "Support common forms (e.g. JSON and YAML) for the input."
