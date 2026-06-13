"""Behaviour tests for `extract_zero_click_view()` (Phase 3a, sp5a, WP-F).

The extractor is the SC-001 gate's *input* discipline: it returns exactly the text a
non-clicking reader sees. These tests pin the two halves of that contract —

1. the OPEN surface is kept: Goal Card text, headings, and every `<summary>` label;
2. the CLOSED surface is dropped: the body of a closed `<details>` never leaks through.

Both run against a real render (so the test tracks the live HTML shape, not a hand-built
fixture) plus a couple of hand-built fragments that isolate edge cases (open details, nesting).
"""
from __future__ import annotations

from cast_server.requirements_render.families import WorkFamily
from cast_server.requirements_render.parser import parse_requirements
from cast_server.requirements_render.renderer import render_requirements
from cast_server.requirements_render.zero_click import extract_zero_click_view


def _words(n: int, tag: str = "w") -> str:
    return " ".join(f"{tag}{i}" for i in range(n))


def _new_initiative_doc() -> str:
    """A full new_initiative doc — its render collapses FR/SC tables into closed
    `<details>`, so it exercises both the open surface and the dropped depth."""
    return (
        "---\nclassification:\n  family: new_initiative\n  confidence: 0.95\n---\n"
        "# Build the Widget Exporter\n\n"
        "## Intent\n\n" + _words(210, "intent") + "\n\n"
        "## User Stories\n\n### US1 — operator exports a widget\n\n"
        "As an operator I want to export so that I can share.\n\n"
        "**Acceptance scenarios**\n\nWHEN I click export, THE SYSTEM SHALL produce a file.\n\n"
        "## Functional Requirements\n\n"
        "| ID | Requirement | Source |\n|---|---|---|\n"
        "| FR-001 | The system SHALL export widgets as CSV | US1 |\n\n"
        "## Success Criteria\n\n"
        "| ID | Criterion | Measure |\n|---|---|---|\n"
        "| SC-001 | Export completes in under 2 seconds | timed test |\n\n"
        "## Out of Scope\n\n- Bulk import of widgets\n"
    )


# --------------------------------------------------------------------------------------
# The OPEN surface is kept
# --------------------------------------------------------------------------------------
def test_keeps_goal_card_title_and_headings() -> None:
    html = render_requirements(parse_requirements(_new_initiative_doc())).html
    view = extract_zero_click_view(html)

    # Goal Card text (title + pill label) survives.
    assert "Build the Widget Exporter" in view
    assert "new initiative" in view.lower()
    # Section headings survive.
    assert "Intent" in view
    assert "User Stories" in view
    assert "Out of Scope" in view


def test_keeps_summary_labels() -> None:
    """The `<summary>` of a collapsed section is the visible disclosure label — it stays."""
    html = render_requirements(parse_requirements(_new_initiative_doc())).html
    view = extract_zero_click_view(html)
    # new_initiative collapses the FR/SC tables; their summaries carry the section heading.
    assert "Functional Requirements" in view
    assert "Success Criteria" in view


def test_keeps_open_content() -> None:
    html = render_requirements(parse_requirements(_new_initiative_doc())).html
    view = extract_zero_click_view(html)
    # The Intent prose (open, never collapsed) is present.
    assert "intent0" in view
    # The open Out-of-Scope bullet is present.
    assert "Bulk import of widgets" in view


# --------------------------------------------------------------------------------------
# The CLOSED surface is dropped
# --------------------------------------------------------------------------------------
def test_drops_closed_details_body() -> None:
    """The FR/SC table *rows* live inside closed `<details>` — they must NOT leak into the
    zero-click view, even though their `<summary>` heading does."""
    html = render_requirements(parse_requirements(_new_initiative_doc())).html
    view = extract_zero_click_view(html)

    # The collapsed FR table body (requirement text + ref) is hidden — the FR rows are pure
    # depth, never promoted. (SC *outcomes* ARE promoted, open, to the Goal Card scope grid,
    # so they legitimately remain visible — that is the design, not a leak.)
    assert "export widgets as CSV" not in view
    assert "FR-001" not in view
    # But the FR section summary label survived (asserted above) — we drop the BODY, not the tag.


def test_open_details_body_is_kept() -> None:
    """A `<details open>` (e.g. after "Expand all") reveals its body to the reader."""
    fragment = (
        "<section><h2>Visible heading</h2>"
        "<details open><summary>Open label</summary>"
        "<div>revealed body text</div></details></section>"
    )
    view = extract_zero_click_view(fragment)
    assert "Visible heading" in view
    assert "Open label" in view
    assert "revealed body text" in view


def test_nested_details_inside_closed_is_fully_hidden() -> None:
    """A details nested in a CLOSED details is unreachable — neither its summary nor body
    shows (you cannot expand the child without first expanding the parent)."""
    fragment = (
        "<details><summary>Outer label</summary>"
        "<details open><summary>Inner label</summary>"
        "<div>inner body</div></details></details>"
    )
    view = extract_zero_click_view(fragment)
    assert "Outer label" in view  # the reachable, top-level summary
    assert "Inner label" not in view  # unreachable — parent is collapsed
    assert "inner body" not in view


def test_style_and_script_content_never_leak() -> None:
    """The inlined `<style>` theme and the expand-all `<script>` must not pollute the view."""
    html = render_requirements(parse_requirements(_new_initiative_doc())).html
    view = extract_zero_click_view(html)
    assert "color-accent" not in view  # a CSS token name
    assert "addEventListener" not in view  # the expand-all script
    assert "{" not in view  # no raw CSS/JS braces


def test_empty_input_is_empty_output() -> None:
    assert extract_zero_click_view("") == ""
