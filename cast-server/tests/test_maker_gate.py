"""Unit tests for the deterministic maker gate (sp3b).

The gate **is** the acceptance machinery for FR-003 / FR-007 — so it is not rubber-stamp
tested: every dimension of both `check_what_doc` and `check_html` gets at least one passing
fixture AND at least one real violation fixture. Plus:

- an **independent** `container_text_index` class (split-across-inline-elements, nested
  containers, whitespace fidelity) so Phase 4b-1 can import the walker on a proven contract;
- a gate↔golden consistency replay (the renderer's zero-`id` golden against the gate);
- **T1 (plan-review):** the live v2 deterministic render passes `check_html` *in full*, not
  just the zero-`id` subset — pinning the trust that lets 3c publish the fallback ungated.
"""
from __future__ import annotations

import pytest

from cast_server.requirements_render.maker_gate import (
    ContainerTextIndex,
    GateReport,
    check_html,
    check_what_doc,
    container_text_index,
)
from cast_server.requirements_render.parser import parse_requirements
from cast_server.requirements_render.renderer import render_requirements


# ======================================================================================
# Shared source fixtures (hand-crafted: source + maker HTML are both under test control)
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

# A maker-style page that PASSES every dimension: zero `id=`, self-contained, `data-goal-slug`
# on <body>, real headings, each id owned by one unit carrying its verbatim text.
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


# ======================================================================================
# GateReport shape
# ======================================================================================
def test_gate_report_is_frozen_and_passed_tracks_violations(parsed):
    rep = check_html(_PASS_HTML, parsed)
    assert isinstance(rep, GateReport)
    assert rep.passed is True
    assert rep.violations == ()
    with pytest.raises(Exception):
        rep.passed = False  # frozen


def test_violations_are_prompt_ready_strings(parsed):
    """Every violation is a plain string (3c feeds them to the HOW agent verbatim)."""
    bad = _PASS_HTML.replace("<strong>FR-001</strong> The system must export nightly.", "")
    rep = check_html(bad, parsed)
    assert not rep.passed
    assert all(isinstance(v, str) and v for v in rep.violations)


# ======================================================================================
# check_html — passing baseline
# ======================================================================================
def test_check_html_passes_clean_maker_page(parsed):
    assert check_html(_PASS_HTML, parsed).passed


def test_check_html_reads_id_label_abutting_body_text(parsed):
    """A maker that runs the anchor label straight into the body text
    (`<span>FR-001</span><span>The system…</span>` → concat `FR-001The system…`) must still
    be read as the id `FR-001` — there is no whitespace word boundary after the digits, so a
    trailing-`\\b` scan would wrongly report the label missing."""
    abutting = _PASS_HTML.replace(
        "<li><strong>FR-001</strong> The system must export nightly.</li>",
        '<li><span class="anchor">FR-001</span>'
        '<span class="req-text">The system must export nightly.</span></li>',
    )
    assert check_html(abutting, parsed).passed


# --- Dimension 1: id-token set equality ------------------------------------------------
def test_check_html_flags_missing_id(parsed):
    bad = _PASS_HTML.replace(
        "<li><strong>FR-001</strong> The system must export nightly.</li>", ""
    )
    rep = check_html(bad, parsed)
    assert not rep.passed
    assert any("FR-001" in v and "missing" in v for v in rep.violations)


def test_check_html_flags_invented_id(parsed):
    bad = _PASS_HTML.replace(
        "<strong>SC-001</strong> Exports complete within ten minutes.",
        "<strong>SC-001</strong> Exports complete within ten minutes. See also SC-999.",
    )
    rep = check_html(bad, parsed)
    assert not rep.passed
    assert any("SC-999" in v and "invented" in v for v in rep.violations)


# --- Dimension 2: per-block correspondence / one-unit-one-container (FR-003) -----------
def test_check_html_paraphrased_leaf_text_is_now_allowed(parsed):
    """refine-req-v3 sp3b — the flip: the blanket verbatim-carriage class is GONE. FR-001's label
    sits on its one unit but the leaf text is paraphrased ("Totally unrelated placeholder prose").
    CREATE may paraphrase freely, so this no longer flags — id-parity + one-unit-one-container hold.
    (Meaning-fidelity is now LLM-guarded only — a recorded known limitation, not a structural gate.)"""
    paraphrased = _PASS_HTML.replace(
        "<li><strong>FR-001</strong> The system must export nightly.</li>",
        "<li><strong>FR-001</strong> Totally unrelated placeholder prose.</li>",
    )
    assert check_html(paraphrased, parsed).passed


def test_check_html_flags_duplicate_label_on_two_units(parsed):
    """One-unit-one-container STAYS hard: the same canonical id may label exactly ONE unit. A second
    unit echoing FR-001's bare label → flagged (each id labels exactly one block)."""
    bad = _PASS_HTML.replace(
        "<li><strong>SC-001</strong> Exports complete within ten minutes.</li>",
        "<li><strong>FR-001</strong> a second unit that also claims the FR-001 label.</li>"
        "<li><strong>SC-001</strong> Exports complete within ten minutes.</li>",
    )
    rep = check_html(bad, parsed)
    assert not rep.passed
    assert any("FR-001" in v and "different containers" in v for v in rep.violations)


def test_check_html_paraphrased_depth_paragraph_is_allowed(parsed):
    """A reworded acceptance-depth paragraph (US1) — previously a verbatim-carriage failure — now
    passes: CREATE optimizes for readability, the verbatim class is gone."""
    paraphrased = _PASS_HTML.replace(
        "Acceptance: the export runs nightly.",
        "Acceptance: the export runs weekly.",
    )
    assert check_html(paraphrased, parsed).passed


# --- Dimension 4: DOM + self-containment ----------------------------------------------
def test_check_html_flags_id_attribute(parsed):
    bad = _PASS_HTML.replace('<section class="rr-unit">', '<section class="rr-unit" id="us1">')
    rep = check_html(bad, parsed)
    assert not rep.passed
    assert any("id=" in v for v in rep.violations)


def test_check_html_flags_data_block_anchor(parsed):
    bad = _PASS_HTML.replace("<li><strong>FR-001</strong>", '<li data-block-anchor="fr1"><strong>FR-001</strong>')
    rep = check_html(bad, parsed)
    assert not rep.passed
    assert any("data-block-anchor" in v for v in rep.violations)


def test_check_html_flags_external_resource(parsed):
    bad = _PASS_HTML.replace(
        "<head>",
        '<head><link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Inter">',
    )
    rep = check_html(bad, parsed)
    assert not rep.passed
    assert any("external resource" in v and "fonts.googleapis.com" in v for v in rep.violations)


def test_check_html_allows_internal_static_and_toggle_hrefs(parsed):
    """Internal `/static/...` script src and an internal version-toggle href are navigation,
    not external fetches — they must NOT trip self-containment."""
    ok = _PASS_HTML.replace(
        "</main>",
        '<a href="/goals/demo-goal/render/diff">Changes</a></main>',
    )
    assert check_html(ok, parsed).passed


def test_check_html_flags_missing_goal_slug(parsed):
    bad = _PASS_HTML.replace('<body data-goal-slug="demo-goal">', "<body>")
    rep = check_html(bad, parsed)
    assert not rep.passed
    assert any("data-goal-slug" in v for v in rep.violations)


def test_check_html_flags_no_headings(parsed):
    bad = _PASS_HTML.replace("<h2>Delivery story</h2>", "").replace(
        "<h2>What it must do</h2>", ""
    ).replace("<h2>How we will know</h2>", "").replace(
        "<h3>US1 — export cadence</h3>", "<p>US1 — export cadence</p>"
    ).replace("<summary>US1 — export cadence</summary>", "<summary>cadence</summary>")
    rep = check_html(bad, parsed)
    assert not rep.passed
    assert any("heading hierarchy" in v for v in rep.violations)


# ======================================================================================
# check_what_doc
# ======================================================================================
def _what_doc(parsed, *, contract="cast-requirements-what/v1", source_hash=None,
             sections=None, unmapped="[]", gaps="[]"):
    """Assemble a WHAT doc with the parsed source's real hash unless overridden.

    `gaps` is the raw YAML value after `gaps:` — `"[]"` (the clean default), or a newline-led
    indented list body for the Phase-5a gaps-schema fixtures."""
    sh = parsed.content_hash if source_hash is None else source_hash
    if sections is None:
        sections = (
            "  - title: Delivery cadence\n"
            "    outcome: Readers see the export rhythm.\n"
            "    block_refs: [US1, FR-001]\n"
            "  - title: Confidence measures\n"
            "    outcome: Readers see how success is proven.\n"
            "    block_refs: [SC-001]\n"
        )
    return (
        "---\n"
        f"contract: {contract}\n"
        "goal_slug: demo-goal\n"
        "family: new_initiative\n"
        f"source_hash: {sh}\n"
        "sections:\n"
        f"{sections}"
        f"unmapped_refs: {unmapped}\n"
        f"gaps: {gaps}\n"
        "---\n\n"
        "Communication-intent prose goes here.\n"
    )


def test_check_what_doc_passes_valid(parsed):
    assert check_what_doc(_what_doc(parsed), parsed).passed


def test_check_what_doc_flags_broken_front_matter(parsed):
    rep = check_what_doc("no front matter here at all\n", parsed)
    assert not rep.passed
    assert any("front matter" in v for v in rep.violations)


def test_check_what_doc_flags_wrong_contract(parsed):
    rep = check_what_doc(_what_doc(parsed, contract="cast-requirements-what/v2"), parsed)
    assert not rep.passed
    assert any("contract" in v for v in rep.violations)


def test_check_what_doc_flags_source_hash_mismatch(parsed):
    rep = check_what_doc(_what_doc(parsed, source_hash="deadbeef"), parsed)
    assert not rep.passed
    assert any("source_hash" in v for v in rep.violations)


def test_check_what_doc_flags_unmapped_ref(parsed):
    """SC-001 is omitted from every section's block_refs — totality fails."""
    sections = (
        "  - title: Delivery cadence\n"
        "    outcome: x\n"
        "    block_refs: [US1, FR-001]\n"
    )
    rep = check_what_doc(_what_doc(parsed, sections=sections), parsed)
    assert not rep.passed
    assert any("SC-001 is unmapped" in v for v in rep.violations)


def test_check_what_doc_flags_invented_ref(parsed):
    sections = (
        "  - title: Delivery cadence\n"
        "    outcome: x\n"
        "    block_refs: [US1, FR-001, SC-001, FR-099]\n"
    )
    rep = check_what_doc(_what_doc(parsed, sections=sections), parsed)
    assert not rep.passed
    assert any("FR-099" in v and "no such ref" in v for v in rep.violations)


def test_check_what_doc_flags_duplicate_ref(parsed):
    sections = (
        "  - title: Delivery cadence\n"
        "    outcome: x\n"
        "    block_refs: [US1, FR-001]\n"
        "  - title: Confidence measures\n"
        "    outcome: y\n"
        "    block_refs: [SC-001, FR-001]\n"
    )
    rep = check_what_doc(_what_doc(parsed, sections=sections), parsed)
    assert not rep.passed
    assert any("FR-001 appears in more than one section" in v for v in rep.violations)


def test_check_what_doc_flags_slot_name_title(parsed):
    sections = (
        "  - title: Functional Requirements\n"
        "    outcome: x\n"
        "    block_refs: [US1, FR-001, SC-001]\n"
    )
    rep = check_what_doc(_what_doc(parsed, sections=sections), parsed)
    assert not rep.passed
    assert any("slot name" in v for v in rep.violations)


def test_check_what_doc_flags_empty_section_title(parsed):
    sections = (
        "  - title: ''\n"
        "    outcome: x\n"
        "    block_refs: [US1, FR-001, SC-001]\n"
    )
    rep = check_what_doc(_what_doc(parsed, sections=sections), parsed)
    assert not rep.passed
    assert any("empty or missing `title`" in v for v in rep.violations)


def test_check_what_doc_flags_nonempty_unmapped_refs(parsed):
    rep = check_what_doc(_what_doc(parsed, unmapped="[FR-001]"), parsed)
    assert not rep.passed
    assert any("unmapped_refs" in v for v in rep.violations)


# ======================================================================================
# gaps[] schema (Phase 5a — the reserved seam activated)
# ======================================================================================
def _gap(gap_id="GAP-01", *, block_refs="[FR-001]", question="What is the export's data source?",
         extra=""):
    """One YAML `gaps[]` entry (indented list body). `extra` injects an extra field (answer-smuggle
    fixtures)."""
    body = (
        f"\n  - gap_id: {gap_id}\n"
        f"    section_title: Delivery cadence\n"
        f"    block_refs: {block_refs}\n"
        f"    question: {question}\n"
        f"    why_it_matters: A reader cannot trust the export without its source.\n"
    )
    if extra:
        body += f"    {extra}\n"
    return body


def test_check_what_doc_passes_valid_gaps(parsed):
    """A well-formed single gap (real block_ref, sequential id, non-empty question, no answer)."""
    assert check_what_doc(_what_doc(parsed, gaps=_gap()), parsed).passed


def test_check_what_doc_passes_two_sequential_gaps(parsed):
    two = _gap("GAP-01") + _gap("GAP-02", question="What retention window applies?")
    assert check_what_doc(_what_doc(parsed, gaps=two), parsed).passed


def test_check_what_doc_flags_duplicate_gap_id(parsed):
    dup = _gap("GAP-01") + _gap("GAP-01", question="A second question.")
    rep = check_what_doc(_what_doc(parsed, gaps=dup), parsed)
    assert not rep.passed
    assert any("sequential" in v for v in rep.violations)  # GAP-01 at position 2 is out of sequence


def test_check_what_doc_flags_non_sequential_gap_ids(parsed):
    seq = _gap("GAP-01") + _gap("GAP-03", question="A third question.")
    rep = check_what_doc(_what_doc(parsed, gaps=seq), parsed)
    assert not rep.passed
    assert any("sequential" in v and "GAP-03" in v for v in rep.violations)


def test_check_what_doc_flags_gap_unknown_block_ref(parsed):
    rep = check_what_doc(_what_doc(parsed, gaps=_gap(block_refs="[FR-099]")), parsed)
    assert not rep.passed
    assert any("FR-099" in v and "not a parsed source ref" in v for v in rep.violations)


def test_check_what_doc_flags_gap_empty_question(parsed):
    rep = check_what_doc(_what_doc(parsed, gaps=_gap(question="''")), parsed)
    assert not rep.passed
    assert any("empty or missing `question`" in v for v in rep.violations)


def test_check_what_doc_flags_answer_smuggled_into_gap(parsed):
    """The WHAT doc NEVER carries an answer — an `answer:`/`proposed_body:` field on a gap fails."""
    rep = check_what_doc(
        _what_doc(parsed, gaps=_gap(extra='answer: "The source is the Stripe webhook stream."')),
        parsed,
    )
    assert not rep.passed
    assert any("NEVER supplies an answer" in v for v in rep.violations)


def test_check_what_doc_flags_gap_nn_as_canonical_ref_in_gap(parsed):
    """A `GAP-NN` token is never a canonical ref — not even inside a gap's own block_refs."""
    rep = check_what_doc(_what_doc(parsed, gaps=_gap(block_refs="[GAP-02]")), parsed)
    assert not rep.passed
    assert any("GAP-02" in v and "never a canonical ref" in v for v in rep.violations)


def test_check_what_doc_flags_gap_nn_as_canonical_ref_in_section(parsed):
    """A `GAP-NN` smuggled into a SECTION's block_refs is rejected (id-space collision guard)."""
    sections = (
        "  - title: Delivery cadence\n"
        "    outcome: x\n"
        "    block_refs: [US1, FR-001, SC-001, GAP-01]\n"
    )
    rep = check_what_doc(_what_doc(parsed, sections=sections), parsed)
    assert not rep.passed
    assert any("GAP-01" in v and "never a canonical ref" in v for v in rep.violations)


# ======================================================================================
# check_gaps_state — the single closed status vocabulary (Phase 5a / A3)
# ======================================================================================
def test_check_gaps_state_passes_in_enum_statuses():
    from cast_server.requirements_render.maker_gate import GAP_STATUS_ENUM, check_gaps_state
    gaps = [{"gap_id": f"GAP-0{i}", "status": s} for i, s in enumerate(sorted(GAP_STATUS_ENUM), 1)]
    assert check_gaps_state({"gaps": gaps}).passed


def test_check_gaps_state_flags_out_of_enum_status():
    from cast_server.requirements_render.maker_gate import check_gaps_state
    rep = check_gaps_state({"gaps": [{"gap_id": "GAP-01", "status": "provisional"}]})
    assert not rep.passed
    assert any("outside the closed enum" in v for v in rep.violations)


# ======================================================================================
# check_html — gap-marker correspondence (Phase 5a, incl. T3 two-open-gap)
# ======================================================================================
_GAP_Q1 = "What is the upstream data source for the export?"
_GAP_Q2 = "What retention window applies to exported files?"


def _with_gap_markers(*marker_texts: str) -> str:
    """Inject `.rr-gap` callouts (class-based, zero id) into the `.rr-document` of _PASS_HTML — each
    carries the given text as its question line."""
    inject = "\n".join(
        f'<div class="rr-gap"><p>{t}</p><p>missing — upstream could not supply it</p></div>'
        for t in marker_texts
    )
    return _PASS_HTML.replace(
        '<main class="rr-document">', '<main class="rr-document">\n' + inject
    )


def test_check_html_no_gaps_no_markers_passes(parsed):
    """The common case: no open gaps and no `.rr-gap` markers → correspondence is a no-op."""
    assert check_html(_PASS_HTML, parsed, open_gap_questions=[]).passed


def test_check_html_gap_marker_correspondence_passes(parsed):
    html = _with_gap_markers(_GAP_Q1)
    assert check_html(html, parsed, open_gap_questions=[_GAP_Q1]).passed


def test_check_html_flags_open_gap_with_no_marker(parsed):
    rep = check_html(_PASS_HTML, parsed, open_gap_questions=[_GAP_Q1])
    assert not rep.passed
    assert any("has no `.rr-gap` marker" in v for v in rep.violations)


def test_check_html_flags_stray_marker_with_no_gap(parsed):
    """A `.rr-gap` on a page with no matching open gap is an invented marker."""
    rep = check_html(_with_gap_markers(_GAP_Q1), parsed, open_gap_questions=[])
    assert not rep.passed
    assert any("no open-gap question verbatim" in v for v in rep.violations)


def test_T3_two_open_gaps_each_distinct_marker_passes(parsed):
    html = _with_gap_markers(_GAP_Q1, _GAP_Q2)
    assert check_html(html, parsed, open_gap_questions=[_GAP_Q1, _GAP_Q2]).passed


def test_T3_two_gaps_merged_into_one_marker_fails(parsed):
    """Merging two gaps into ONE marker → that marker carries two questions → fail."""
    html = _with_gap_markers(f"{_GAP_Q1} {_GAP_Q2}")
    rep = check_html(html, parsed, open_gap_questions=[_GAP_Q1, _GAP_Q2])
    assert not rep.passed
    assert any("merged into one marker" in v for v in rep.violations)


def test_T3_two_gaps_swapped_into_same_marker_fails(parsed):
    """A swap that duplicates one question across both markers (and drops the other) → fail: the
    duplicated question matches 2 markers, the dropped question matches 0."""
    html = _with_gap_markers(_GAP_Q1, _GAP_Q1)
    rep = check_html(html, parsed, open_gap_questions=[_GAP_Q1, _GAP_Q2])
    assert not rep.passed
    assert any(_clip_q(_GAP_Q1) in v and "markers" in v for v in rep.violations)  # Q1 in 2 markers
    assert any(_clip_q(_GAP_Q2) in v and "no `.rr-gap` marker" in v for v in rep.violations)  # Q2 dropped


def _clip_q(q: str) -> str:
    """Mirror maker_gate._clip so assertions match the clipped excerpt in a violation string."""
    flat = " ".join(q.split())
    return flat if len(flat) <= 60 else flat[:59] + "…"


# ======================================================================================
# container_text_index — independent contract (revision b; proven for Phase 4b-1)
# ======================================================================================
class TestContainerTextIndex:
    _SPLIT_HTML = """\
<main class="rr-document">
<section class="rr-unit">
<h3>US1 — cadence</h3>
<p>a <strong>recurring</strong> cadence for a report export</p>
</section>
<ul>
<li><strong>FR-001</strong> The system must export nightly.</li>
</ul>
</main>
"""

    def test_returns_typed_index(self):
        idx = container_text_index(self._SPLIT_HTML)
        assert isinstance(idx, ContainerTextIndex)
        assert idx.units()  # at least one requirement-unit container

    def test_quote_split_across_inline_elements_places(self):
        """A quote straddling a <strong> still matches — the walker concatenates descendant
        text nodes with NO whitespace normalization (1b harness fidelity)."""
        idx = container_text_index(self._SPLIT_HTML)
        quote = "a recurring cadence for a report export"
        at = idx.find(quote)
        assert at >= 0
        # and it lands inside the US1 unit, not some other container
        unit = idx.unit_at(at)
        assert unit is not None and "US1" in unit.text

    def test_whitespace_is_byte_faithful_not_normalized(self):
        """A re-spaced quote (double space) must NOT match — proving no normalization."""
        idx = container_text_index(self._SPLIT_HTML)
        assert idx.find("a  recurring cadence") == -1

    def test_unit_at_returns_innermost_unit(self):
        """An FR `<li>` nested in a unit context resolves to the `<li>`, not an ancestor."""
        idx = container_text_index(self._SPLIT_HTML)
        at = idx.document_text.find("The system must export nightly.")
        unit = idx.unit_at(at)
        assert unit is not None
        assert unit.tag == "li"
        assert "FR-001" in unit.text

    def test_find_is_first_match_like_indexOf(self):
        html = '<main class="rr-document"><p>alpha beta alpha</p></main>'
        idx = container_text_index(html)
        assert idx.find("alpha") == idx.document_text.index("alpha")

    def test_document_text_scopes_to_rr_document(self):
        """Text outside `.rr-document` (page chrome) is excluded from the doc concat — the JS
        TreeWalker only ever walks the `.rr-document` node."""
        html = (
            "<body><nav>CHROME-ONLY-TOKEN</nav>"
            '<main class="rr-document"><p>inside body text</p></main></body>'
        )
        idx = container_text_index(html)
        assert "inside body text" in idx.document_text
        assert "CHROME-ONLY-TOKEN" not in idx.document_text


# ======================================================================================
# gate ↔ golden consistency + T1
# ======================================================================================
def _classified_doc(family_value: str) -> str:
    """A classified, full-recipe document whose every section the recipe realizes — the kind
    of render T1 pins (a classified doc renders all its refs; the unclassified/generic path
    renders a recipe subset and is out of T1's scope)."""
    intent = " ".join(f"intent{i}" for i in range(210))
    return f"""\
---
classification:
  family: {family_value}
  confidence: 0.95
---
# Nightly Export Initiative

## Intent

{intent}

## User Stories

### US1 — export cadence

As a user I want a recurring cadence for a report export so data lands on time.

Acceptance: the export runs nightly.

## Functional Requirements

| ID | Requirement | Source |
|---|---|---|
| FR-001 | The system must export nightly. | US1 |
| FR-002 | The export is idempotent across reruns. | US1 |

## Success Criteria

| ID | Criterion | Measure |
|---|---|---|
| SC-001 | Exports complete within ten minutes. | timed |

## Out of Scope

- Real-time streaming export.
"""


def test_gate_golden_consistency_zero_id(parsed):
    """The renderer's zero-`id` golden (test_requirements_renderer.test_no_ids_or_anchors)
    replayed through the gate: a real deterministic render has no `id=` violations."""
    res = render_requirements(parse_requirements(_classified_doc("new_initiative")))
    rep = check_html(res.html, parse_requirements(_classified_doc("new_initiative")))
    assert not any("id=" in v for v in rep.violations)
    assert not any("data-block-anchor" in v for v in rep.violations)


@pytest.mark.parametrize("family", ["new_initiative", "pilot_poc", "refactor_migration"])
def test_T1_live_deterministic_render_passes_in_full(family):
    """T1 (plan-review): the live v2 deterministic render passes `check_html` in FULL — not
    just the zero-`id` subset. 3c publishes the fallback ungated on the trust that the
    deterministic substrate is always structurally valid; this pins that trust so a future
    renderer change cannot silently make the fallback un-gateable."""
    parsed = parse_requirements(_classified_doc(family))
    res = render_requirements(parsed)
    rep = check_html(res.html, parsed)
    assert rep.passed, f"{family}: deterministic render failed the gate: {rep.violations}"
