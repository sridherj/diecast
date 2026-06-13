"""Unit tests for the comment-survival gate (sp4b-1, `check_comment_survival`).

The survival gate is the machine-check behind SC-003 ("zero new orphans"): every OPEN comment's
verbatim quote must still place on a candidate maker DOM, or the loss is surfaced. It is pure
(no I/O / DB / LLM) and rides the SAME container-text walker as the carriage check — so this
suite covers, with at least one fixture per classification branch:

- **in-block** (quote ⊂ a block's anchorable text): MUST place; a miss is a witnessed
  verbatim-carriage failure → a prompt-ready `violations` entry, `passed=False`, id in `unplaced`.
- **cross-boundary** (quote spans blocks / a markdown-strip seam / quotes render decoration):
  best-effort, recorded in `unplaced` on a miss but **NEVER** a violation and never flips `passed`.

Plus the DECISION #10 OVERRIDE invariant (cross-boundary never blocks), the 1b
split-across-inline-elements self-test replayed through the gate, the legacy-cutover mitigation
(a quote selected on the v2 deterministic DOM reads cross-boundary, not a failure), and the
deterministic-fallback trust pin (the ungated fallback substrate never regresses below the gate).
"""
from __future__ import annotations

import pytest

from cast_server.requirements_render.maker_gate import (
    check_comment_survival,
    container_text_index,
    strip_inline_markdown,
)
from cast_server.requirements_render.parser import parse_requirements
from cast_server.requirements_render.renderer import render_requirements


# ======================================================================================
# Shared hand-crafted fixtures (source + maker HTML both under test control — mirrors
# test_maker_gate so an in-block quote is placeable-by-construction on the proven page).
# ======================================================================================
_SOURCE = """\
---
classification:
  family: new_initiative
  confidence: 0.95
---
# Demo Goal

## Intent

The team wants a dependable nightly report export so downstream data lands on time.

## User Stories

### US1 — export cadence

As a user I want a recurring cadence for a report export.

Acceptance: the export runs nightly.

## Functional Requirements

| ID | Requirement | Source |
|---|---|---|
| FR-001 | The system must export nightly. | US1 |

## Success Criteria

| ID | Criterion | Measure |
|---|---|---|
| SC-001 | Exports complete within ten minutes. | timed |
"""

_PASS_HTML = """\
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Demo Goal</title>
<style>.rr-unit{margin:0}</style></head>
<body data-goal-slug="demo-goal">
<main class="rr-document">
<h2>Delivery story</h2>
<section class="rr-unit">
<h3>US1 — export cadence</h3>
<p>As a user I want a recurring cadence for a report export.</p>
<details><summary>US1 — export cadence</summary>
<p>Acceptance: the export runs nightly.</p></details>
</section>
<h2>What it must do</h2>
<ul>
<li><strong>FR-001</strong> The system must export nightly.</li>
</ul>
<h2>How we will know</h2>
<ul>
<li><strong>SC-001</strong> Exports complete within ten minutes.</li>
</ul>
</main>
<script src="/static/requirements_comments.js" defer></script>
</body>
</html>
"""


@pytest.fixture
def parsed():
    return parse_requirements(_SOURCE)


def _comment(cid: int, quote: str) -> dict:
    return {"id": cid, "quoted_text": quote}


# ======================================================================================
# in-block: placeable (the verbatim-carriage guarantee)
# ======================================================================================
def test_in_block_placeable_passes(parsed):
    """A quote that is a substring of FR-001's anchorable text places on a faithful DOM."""
    rep = check_comment_survival(
        _PASS_HTML, parsed, [_comment(1, "The system must export nightly.")]
    )
    assert rep["passed"] is True
    assert rep["placed"] == [1]
    assert rep["unplaced"] == []
    assert rep["violations"] == []


def test_in_block_placeable_at_depth(parsed):
    """A quote from the US1 acceptance-depth paragraph (inside a <details>) still places —
    the walker concatenates descendant text regardless of disclosure nesting."""
    rep = check_comment_survival(
        _PASS_HTML, parsed, [_comment(7, "Acceptance: the export runs nightly.")]
    )
    assert rep["passed"] and rep["placed"] == [7]


# ======================================================================================
# in-block: missing from the candidate DOM → witnessed carriage failure → violation
# ======================================================================================
def test_in_block_missing_is_violation(parsed):
    """The maker dropped FR-001's carried text. The quote is in-block (source) but absent from
    the DOM → `passed=False`, a prompt-ready violation naming the comment + container, id in
    `unplaced` and NOT in `placed`."""
    bad = _PASS_HTML.replace(
        "<li><strong>FR-001</strong> The system must export nightly.</li>", ""
    )
    rep = check_comment_survival(bad, parsed, [_comment(12, "The system must export nightly.")])
    assert rep["passed"] is False
    assert rep["unplaced"] == [12]
    assert rep["placed"] == []
    assert len(rep["violations"]) == 1
    v = rep["violations"][0]
    assert isinstance(v, str) and v
    assert "comment 12" in v and "FR-001" in v and "missing" in v


def test_in_block_wrong_container_is_violation(parsed):
    """The FR-001 text echoes inside a DIFFERENT unit that does not show the FR-001 label —
    placement is valid only in the id's own container, so this is still a miss (the hit lands
    in the wrong unit)."""
    bad = _PASS_HTML.replace(
        "<li><strong>FR-001</strong> The system must export nightly.</li>",
        "<li><strong>FR-001</strong> Unrelated placeholder.</li>"
        '<section class="rr-unit"><h3>Stray</h3>'
        "<p>The system must export nightly.</p></section>",
    )
    rep = check_comment_survival(bad, parsed, [_comment(13, "The system must export nightly.")])
    assert rep["passed"] is False
    assert 13 in rep["unplaced"]
    assert any("comment 13" in v for v in rep["violations"])


# ======================================================================================
# cross-boundary: recorded but NEVER a violation, never flips passed (the OVERRIDE invariant)
# ======================================================================================
def test_cross_boundary_spans_two_blocks_not_a_violation(parsed):
    """A quote splicing two different blocks' text is not a substring of any single block's
    anchorable body → cross-boundary. Absent from the DOM → recorded in `unplaced`, but NEVER a
    violation and `passed` stays True."""
    quote = "a report export joined to export nightly"
    rep = check_comment_survival(_PASS_HTML, parsed, [_comment(20, quote)])
    assert rep["passed"] is True
    assert rep["unplaced"] == [20]
    assert rep["violations"] == []


def test_cross_boundary_inline_markdown_seam_not_a_violation(parsed):
    """A quote carrying inline-markdown markers (`**`) is not a substring of the stripped
    anchorable body → cross-boundary, not a violation (it can fail on the deterministic
    substrate too — the markers never reach the rendered DOM)."""
    rep = check_comment_survival(_PASS_HTML, parsed, [_comment(21, "export **nightly**")])
    assert rep["passed"] is True
    assert 21 in rep["unplaced"]
    assert rep["violations"] == []


def test_cross_boundary_maker_decoration_text_not_a_violation(parsed):
    """A quote of maker-added decoration ("Delivery story" — a heading the maker invented, in no
    source block) is cross-boundary. It is present in this DOM so it *places*, but the point is
    it is NEVER a violation regardless."""
    rep = check_comment_survival(_PASS_HTML, parsed, [_comment(22, "Delivery story")])
    assert rep["passed"] is True
    assert rep["violations"] == []
    assert 22 in rep["placed"]


def test_cross_boundary_miss_never_flips_passed_alongside_in_block_pass(parsed):
    """A clean in-block placement and a cross-boundary miss in the SAME pass: passed stays True
    (only an in-block miss can flip it), with the in-block id placed and the cross-boundary id
    surfaced in `unplaced`."""
    rep = check_comment_survival(
        _PASS_HTML, parsed,
        [_comment(1, "The system must export nightly."), _comment(2, "nowhere-near-the-source")],
    )
    assert rep["passed"] is True
    assert rep["placed"] == [1]
    assert rep["unplaced"] == [2]
    assert rep["violations"] == []


# ======================================================================================
# 1b split-across-inline-elements self-test, replayed through the gate
# ======================================================================================
def test_split_across_inline_elements_places(parsed):
    """The 1b harness invariant via `check_comment_survival`: an in-block quote that straddles an
    inline `<strong>` boundary still places (the walker concatenates descendant text nodes)."""
    split = _PASS_HTML.replace(
        "<p>As a user I want a recurring cadence for a report export.</p>",
        "<p>As a user I want a <strong>recurring</strong> cadence for a report export.</p>",
    )
    # sanity: the walker concatenates across the inline boundary
    assert container_text_index(split).find("recurring cadence for a report export") >= 0
    rep = check_comment_survival(
        split, parsed, [_comment(30, "recurring cadence for a report export")]
    )
    assert rep["passed"] and rep["placed"] == [30]


# ======================================================================================
# Purity / single-walk discipline (P1) — no mutation, deterministic, no I/O
# ======================================================================================
def test_gate_is_pure_and_repeatable(parsed):
    """Two identical calls return equal reports and never mutate inputs (no hidden state)."""
    comments = [_comment(1, "The system must export nightly.")]
    a = check_comment_survival(_PASS_HTML, parsed, comments)
    b = check_comment_survival(_PASS_HTML, parsed, comments)
    assert a == b
    assert comments == [{"id": 1, "quoted_text": "The system must export nightly."}]


def test_empty_comment_set_passes(parsed):
    rep = check_comment_survival(_PASS_HTML, parsed, [])
    assert rep == {
        "passed": True, "violations": [], "unplaced": [], "placed": [], "expected_misses": []
    }


# ======================================================================================
# Deterministic render — legacy-cutover mitigation + the fallback trust pin
# ======================================================================================
_CLASSIFIED = """\
---
classification:
  family: new_initiative
  confidence: 0.95
---
# Nightly Export Initiative

## Intent

%s

## User Stories

### US1 — export cadence

As a user I want a recurring cadence for a report export so data lands on time.

Acceptance: the export runs nightly.

## Functional Requirements

| ID | Requirement | Source |
|---|---|---|
| FR-001 | The system must export nightly. | US1 |

## Success Criteria

| ID | Criterion | Measure |
|---|---|---|
| SC-001 | Exports complete within ten minutes. | timed |
""" % " ".join("intent%d" % i for i in range(210))


def test_deterministic_fallback_trust_pin_in_block_places():
    """Mirror of Phase 3 T1: `check_comment_survival` over the LIVE `render_requirements()` output
    passes for an in-block quote. The fallback is published ungated, so this pins that the
    deterministic substrate never regresses below the gate."""
    parsed = parse_requirements(_CLASSIFIED)
    res = render_requirements(parsed)
    rep = check_comment_survival(
        res.html, parsed, [_comment(40, "The system must export nightly.")]
    )
    assert rep["passed"] is True
    assert 40 in rep["placed"]


def test_legacy_quote_selected_on_deterministic_dom_reads_cross_boundary():
    """Key-Risk row 1 mitigation: a legacy comment whose quote was selected on the v2
    deterministic DOM — carrying render decoration absent from any stripped block body — classifies
    cross-boundary → surfaced (if it misses) but NEVER a violation. Without this, "legacy comments
    read as cross-boundary, not failures" is an unverified claim guarding the cutover."""
    parsed = parse_requirements(_CLASSIFIED)
    res = render_requirements(parsed)
    idx = container_text_index(res.html)
    # The renderer's "Functional Requirements" section label is decoration present in the DOM but
    # in NO block's stripped anchorable body — exactly the legacy-quote shape (selected off the
    # rendered page, carrying render chrome the source markdown never had).
    label = "Functional Requirements"
    assert label in idx.document_text
    assert all(
        label not in strip_inline_markdown(b.body) for b in parsed.blocks if b.ref
    )
    rep = check_comment_survival(res.html, parsed, [_comment(41, label)])
    assert rep["passed"] is True            # never blocks
    assert rep["violations"] == []          # cross-boundary decoration is never a violation
    assert 41 in rep["placed"]              # it IS in the served DOM, so it places (and is fine)
