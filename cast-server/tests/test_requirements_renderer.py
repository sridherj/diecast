"""Behavioural / pipeline tests for the block-recipe render engine (Phase 3a, sp2, WP-B).

sp2 owns the *behavioural* contract here: recipe-order rendering, the stub and
classification-rescue paths, never-drop-unrecognized, the reused markdown instance, density
warnings, determinism, and the thin-spine DOM contract (no ids/anchors). sp5a extends this
file with golden byte-compares + the full structural battery + per-family golden snapshots.

Inputs are built **programmatically** (parse inline markdown with classification front
matter) rather than from `tests/fixtures/family_docs/` — that Phase 2 WP-D fixture set is a
precondition that has not landed, and these behavioural tests should not block on it. sp5a's
goldens will consume the real fixtures once they exist.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

from cast_server.requirements_render import renderer as renderer_mod
from cast_server.requirements_render.families import (
    FAMILY_RECIPES,
    RECIPE_REALIZATION,
    WorkFamily,
    modulate,
)
from cast_server.requirements_render.parser import parse_requirements
from cast_server.requirements_render.renderer import RenderResult, render_requirements


# --------------------------------------------------------------------------------------
# Doc builders — assemble a recognized-section document per family, programmatically.
# --------------------------------------------------------------------------------------
def _words(n: int, tag: str = "w") -> str:
    """`n` deterministic filler words (keeps docs above the stub threshold)."""
    return " ".join(f"{tag}{i}" for i in range(n))


# One recognized-H2 body per heading the recipes can realize. Each carries its own ATX
# heading line (the parser keys on it) + enough words to read as real content. The Intent
# body alone clears STUB_WORD_THRESHOLD (200) so every family doc — even random_idea, whose
# recipe is (Intent,) only — renders the full recipe rather than the stub card.
_SECTION_BODIES: dict[str, str] = {
    "Intent": "## Intent\n\n" + _words(210, "intent"),
    "Evidence": "## Evidence\n\n" + _words(40, "ev"),
    "Decisions": "## Decisions\n\n" + _words(40, "dec"),
    "User Stories": "## User Stories\n\n### US1 — example story\n\n" + _words(30, "us"),
    "Functional Requirements": (
        "## Functional Requirements\n\n"
        "| ID | Requirement | Source |\n|---|---|---|\n"
        "| FR-001 | " + _words(12, "fr") + " | US1 |\n"
    ),
    "Success Criteria": (
        "## Success Criteria\n\n"
        "| ID | Criterion | Measure |\n|---|---|---|\n"
        "| SC-001 | " + _words(12, "sc") + " | test |\n"
    ),
    "Out of Scope": "## Out of Scope\n\n- " + _words(10, "oos") + "\n- " + _words(10, "oosb"),
    "Constraints": "## Constraints\n\n- " + _words(10, "con"),
    "Open Questions": "## Open Questions\n\n- " + _words(10, "oq"),
}


def _expected_headings(family: WorkFamily) -> list[str]:
    """The section headings, in render order, for a doc that provides every realized
    section of `family`'s recipe (mirrors the renderer's consumed-kind dedupe)."""
    recipe = modulate(FAMILY_RECIPES[family], irreversible=False, unknown_cause=False)
    headings: list[str] = []
    seen: set = set()
    for recipe_block in recipe:
        realization = RECIPE_REALIZATION[recipe_block]
        for heading, kind in zip(realization.headings, realization.block_kinds):
            if kind in seen:
                continue
            seen.add(kind)
            headings.append(heading)
    return headings


def _build_family_doc(family: WorkFamily) -> str:
    """A full document for `family`: classification front matter + every recipe section."""
    front = (
        "---\n"
        "classification:\n"
        f"  family: {family.value}\n"
        "  confidence: 0.95\n"
        "---\n"
    )
    body = ["# Example Goal — " + family.value]
    for heading in _expected_headings(family):
        body.append(_SECTION_BODIES[heading])
    return front + "\n".join(body) + "\n"


def _body(html: str) -> str:
    """The rendered `<main>` body only — excludes the inlined `<style>` theme, whose class
    *definitions* (`.family-pill--unclassified`, `.recipe-section`, …) would otherwise
    pollute substring assertions about what was actually *rendered*."""
    match = re.search(r"<main\b[^>]*>(.*)</main>", html, re.S)
    assert match, "rendered HTML has no <main> body"
    return match.group(1)


def _rendered_headings(html: str) -> list[str]:
    return re.findall(r'<h2 class="slide-title">([^<]+)</h2>', _body(html))


# --------------------------------------------------------------------------------------
# Recipe-order + pill class, per family
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize("family", list(WorkFamily))
def test_renders_each_family_in_recipe_order(family: WorkFamily) -> None:
    parsed = parse_requirements(_build_family_doc(family))
    result = render_requirements(parsed)

    assert isinstance(result, RenderResult)
    body = _body(result.html)
    # Sections appear in FAMILY_RECIPES order.
    assert _rendered_headings(result.html) == _expected_headings(family)
    # The family pill carries family-pill--{value} (a real classification, not unclassified).
    assert f"family-pill--{family.value}" in body
    assert "family-pill--unclassified" not in body
    # No spurious unclassified warning for a validly-classified doc.
    assert all("unclassified" not in w for w in result.warnings)


# --------------------------------------------------------------------------------------
# Stub → prompt-to-begin
# --------------------------------------------------------------------------------------
def test_stub_renders_prompt_to_begin() -> None:
    doc = (
        "---\nclassification:\n  family: random_idea\n  confidence: 0.4\n---\n"
        "# Tiny Idea\n\n## Intent\n\nA brief thought I have not fleshed out yet.\n"
    )
    parsed = parse_requirements(doc)
    result = render_requirements(parsed)
    body = _body(result.html)

    assert "Refine this goal to build it out" in body
    # No recipe sections rendered for a stub.
    assert 'class="recipe-section"' not in body
    assert _rendered_headings(result.html) == []
    # A warning names the stub state.
    assert any("stub" in w.lower() for w in result.warnings)


# --------------------------------------------------------------------------------------
# Classification rescue: missing / garbage ⇒ GENERIC + unclassified pill
# --------------------------------------------------------------------------------------
def _full_intent_doc(front: str) -> str:
    """A non-stub doc (front matter under test) with a substantial Intent + Open Questions."""
    return (
        front
        + "# Goal\n\n"
        + "## Intent\n\n"
        + _words(210, "intent")
        + "\n\n## Open Questions\n\n- "
        + _words(15, "oq")
        + "\n"
    )


def test_missing_classification_falls_back_generic() -> None:
    parsed = parse_requirements(_full_intent_doc("---\nstatus: refined\n---\n"))
    result = render_requirements(parsed)

    assert "family-pill--unclassified" in _body(result.html)
    assert any("unclassified" in w for w in result.warnings)
    # GENERIC recipe = (PROBLEM, OPEN) ⇒ Intent then Open Questions.
    assert _rendered_headings(result.html) == ["Intent", "Open Questions"]


def test_garbage_classification_falls_back_generic() -> None:
    front = "---\nclassification:\n  family: definitely_not_a_family\n  confidence: 9\n---\n"
    parsed = parse_requirements(_full_intent_doc(front))
    result = render_requirements(parsed)  # must not raise

    assert "family-pill--unclassified" in _body(result.html)
    assert any("unclassified" in w for w in result.warnings)
    assert _rendered_headings(result.html) == ["Intent", "Open Questions"]


def test_non_dict_classification_falls_back_generic() -> None:
    parsed = parse_requirements(_full_intent_doc('---\nclassification: "a string"\n---\n'))
    result = render_requirements(parsed)  # must not raise

    assert "family-pill--unclassified" in _body(result.html)
    assert any("unclassified" in w for w in result.warnings)


# --------------------------------------------------------------------------------------
# Never drop unrecognized sections
# --------------------------------------------------------------------------------------
def test_unrecognized_sections_rendered_and_warned() -> None:
    doc = (
        "---\nclassification:\n  family: generic\n  confidence: 0.9\n---\n"
        "# Goal\n\n## Intent\n\n"
        + _words(210, "intent")
        + "\n\n## Glossary\n\nTerm one means alpha. Term two means beta.\n"
    )
    parsed = parse_requirements(doc)
    assert "Glossary" in parsed.unrecognized_sections  # parser flagged it
    result = render_requirements(parsed)
    body = _body(result.html)

    assert "Unmodeled section: Glossary" in body
    assert "<details" in body
    # The verbatim body is preserved (zero silent drop).
    assert "Term one means alpha" in body
    # A warning names the section.
    assert any("Glossary" in w for w in result.warnings)


# --------------------------------------------------------------------------------------
# Determinism, markdown reuse, density, DOM contract
# --------------------------------------------------------------------------------------
def test_render_is_deterministic() -> None:
    doc = _build_family_doc(WorkFamily.NEW_INITIATIVE)
    first = render_requirements(parse_requirements(doc))
    second = render_requirements(parse_requirements(doc))

    assert first.html == second.html  # byte-identical (no timestamps)
    assert first.warnings == second.warnings
    # No clock/run-varying tokens leaked in.
    assert "source-hash" not in first.html
    assert not re.search(r"\d{4}-\d{2}-\d{2}T", first.html)


def test_markdown_instance_reused(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"reset": 0, "convert": 0}
    real_reset = renderer_mod._MD.reset
    real_convert = renderer_mod._MD.convert

    def spy_reset() -> None:
        calls["reset"] += 1
        real_reset()

    def spy_convert(text: str) -> str:
        calls["convert"] += 1
        return real_convert(text)

    monkeypatch.setattr(renderer_mod._MD, "reset", spy_reset)
    monkeypatch.setattr(renderer_mod._MD, "convert", spy_convert)

    # Guard the perf decision: building a NEW Markdown instance mid-render is a failure.
    def _no_new_instance(*_a: object, **_k: object) -> None:
        raise AssertionError("renderer built a new markdown.Markdown instance")

    monkeypatch.setattr(renderer_mod.markdown, "Markdown", _no_new_instance)

    render_requirements(parse_requirements(_build_family_doc(WorkFamily.NEW_INITIATIVE)))

    assert calls["convert"] >= 2  # multiple sections converted
    assert calls["reset"] == calls["convert"]  # one reset per conversion


def test_density_warnings_emitted() -> None:
    doc = (
        "---\nclassification:\n  family: generic\n  confidence: 0.9\n---\n"
        "# Goal\n\n## Intent\n\n" + _words(300, "intent") + "\n"
    )
    result = render_requirements(parse_requirements(doc))
    assert any("density" in w and "Intent" in w for w in result.warnings)


def test_no_ids_or_anchors() -> None:
    result = render_requirements(parse_requirements(_build_family_doc(WorkFamily.NEW_INITIATIVE)))
    body = _body(result.html)
    assert "id=" not in body
    assert "data-block-anchor" not in body


def test_render_result_is_frozen() -> None:
    result = render_requirements(parse_requirements(_build_family_doc(WorkFamily.GENERIC)))
    with pytest.raises(Exception):
        result.html = "mutated"  # type: ignore[misc]


def test_version_chip_rendered_when_provided() -> None:
    doc = _build_family_doc(WorkFamily.GENERIC)
    assert "version-chip" not in _body(render_requirements(parse_requirements(doc)).html)
    body_v = _body(render_requirements(parse_requirements(doc), version=7).html)
    assert "version-chip" in body_v
    assert ">v7<" in body_v


# ======================================================================================
# sp3 (WP-C + WP-D): Goal Card, disclosure boundary, scope compare, WHAT-before-HOW
# ======================================================================================
def _goal_card(html: str) -> str:
    """The rendered `<section class="goal-card">…</section>` block only."""
    match = re.search(r'<section class="goal-card">(.*?)</section>', _body(html), re.S)
    assert match, "rendered HTML has no goal-card section"
    return match.group(0)


def _directional_doc(family: WorkFamily, *, with_directional: bool) -> str:
    """A non-stub doc for `family` (Intent clears the stub threshold), optionally carrying an
    authored `## Directional` HOW section."""
    front = (
        "---\nclassification:\n"
        f"  family: {family.value}\n  confidence: 0.95\n---\n"
    )
    body = [f"# Example Goal — {family.value}", "## Intent\n\n" + _words(210, "intent")]
    if with_directional:
        body.append(
            "## Directional\n\nWe might reach for a vanilla template engine here, "
            "but this is non-binding."
        )
    return front + "\n\n".join(body) + "\n"


def test_goal_card_outside_details() -> None:
    """The entire Goal Card — pill, job statement, assertions, scope compare — is WHAT and is
    NEVER inside a `<details>`."""
    html = render_requirements(parse_requirements(_build_family_doc(WorkFamily.NEW_INITIATIVE))).html
    card = _goal_card(html)

    assert "family-pill" in card
    assert "goal-card__job" in card
    assert "goal-card__assertions" in card
    assert "scope-grid" in card  # new_initiative recipe has SCOPE
    # The WHAT is open: no disclosure element anywhere inside the card.
    assert "<details" not in card
    assert "<summary" not in card


def test_what_never_collapsed() -> None:
    """Only *depth* collapses. The job statement, assertions, and scope compare are open;
    the FR/SC tables are the depth that lives behind `<details>`."""
    html = render_requirements(parse_requirements(_build_family_doc(WorkFamily.NEW_INITIATIVE))).html
    body = _body(html)
    card = _goal_card(html)

    # WHAT is open (in the card, outside any details).
    assert "goal-card__job" in card and "<details" not in card
    # Depth IS collapsed: the FR/SC sections wrap their tables in <details>.
    assert "<details" in body
    fr_section = re.search(r'<section class="recipe-section">\s*<h2[^>]*>Functional Requirements.*?</section>', body, re.S)
    assert fr_section and "<details" in fr_section.group(0)


def test_pill_has_family_class() -> None:
    html = render_requirements(parse_requirements(_build_family_doc(WorkFamily.BUG_FIX))).html
    assert "family-pill--bug_fix" in _goal_card(html)


def test_pill_carries_reasoning_title() -> None:
    """The pill exposes the model's classification reasoning on hover via `title` (Step 3.3)."""
    doc = (
        "---\nclassification:\n  family: bug_fix\n  confidence: 0.95\n"
        '  reasoning: "a defect in existing behaviour"\n---\n'
        "# Goal\n\n## Intent\n\n" + _words(210, "intent") + "\n"
    )
    card = _goal_card(render_requirements(parse_requirements(doc)).html)
    assert 'title="a defect in existing behaviour"' in card


def test_unclassified_pill_state() -> None:
    """Missing classification ⇒ the distinct unclassified rescue pill (text + class)."""
    doc = _full_intent_doc("---\nstatus: refined\n---\n")
    card = _goal_card(render_requirements(parse_requirements(doc)).html)
    assert "family-pill--unclassified" in card
    assert "Unclassified" in card  # the visible rescue label


def test_scope_grid_open_or_omitted() -> None:
    """The scope compare renders open when the recipe has a SCOPE block, and is omitted
    entirely otherwise."""
    # new_initiative recipe = (PROBLEM, DECISION, SCOPE, OPEN) ⇒ grid present.
    with_scope = render_requirements(
        parse_requirements(_build_family_doc(WorkFamily.NEW_INITIATIVE))
    ).html
    grid_card = _goal_card(with_scope)
    assert "scope-grid" in grid_card
    assert "<details" not in grid_card  # the compare is never collapsed

    # bug_fix recipe = (PROBLEM, EVIDENCE, OPEN) ⇒ no SCOPE block ⇒ no grid.
    without_scope = render_requirements(
        parse_requirements(_build_family_doc(WorkFamily.BUG_FIX))
    ).html
    assert "scope-grid" not in _body(without_scope)


def test_directional_muted_last_or_omitted() -> None:
    # Authored Directional ⇒ rendered last, in the muted .question-annotation grammar.
    html = render_requirements(
        parse_requirements(_directional_doc(WorkFamily.NEW_INITIATIVE, with_directional=True))
    ).html
    body = _body(html)
    assert 'class="directional"' in body
    assert "question-annotation" in body
    assert "non-binding" in body.lower()
    # It is the LAST layer — after every recipe section.
    assert body.index('class="directional"') > body.rindex('class="recipe-section"')

    # A HOW-irrelevant family with no authored Directional ⇒ omitted (never padded).
    omitted = render_requirements(
        parse_requirements(_directional_doc(WorkFamily.DATA_ANALYSIS, with_directional=False))
    ).html
    assert 'class="directional"' not in _body(omitted)


def test_every_summary_has_text() -> None:
    """No empty `<summary>` — every disclosure affordance has a discernible visible label
    (the a11y / print rule, Step 3.5). new_initiative collapses FR/SC depth, so it must
    produce summaries; whichever families emit one, none may be empty."""
    seen_any = False
    for family in list(WorkFamily):
        html = render_requirements(parse_requirements(_build_family_doc(family))).html
        summaries = re.findall(r"<summary>(.*?)</summary>", _body(html), re.S)
        for text in summaries:
            assert text.strip(), f"{family.value}: empty <summary>"
        seen_any = seen_any or bool(summaries)
    # The disclosure path is genuinely exercised (new_initiative collapses FR/SC tables).
    assert seen_any


# ======================================================================================
# sp5a (WP-F): golden HTML snapshots (default CI) + structural assertion battery
# ======================================================================================
# Render determinism (sp2) is the precondition for byte-compares; if a golden goes flaky the
# bug is a stray nondeterminism in the renderer — fix the renderer, not the test (sp5a note).
#
# Inputs: the Phase 2 WP-D `tests/fixtures/family_docs/` fixture set has NOT landed (the
# behavioural section above documents this). Rather than block sp5a on a missing precondition,
# the goldens render the SAME programmatic family docs the behavioural tests build — these are
# deterministic and byte-stable, so they are a faithful golden input. When the real fixtures
# land, point `_golden_input(...)` at them and regenerate with UPDATE_GOLDENS=1.
GOLDEN_DIR = Path(__file__).resolve().parent / "golden" / "requirements_render"


def _check_golden(name: str, html: str) -> None:
    """Byte-compare `html` against `golden/requirements_render/{name}.html`.

    `UPDATE_GOLDENS=1` regenerates the golden instead of asserting (the documented
    intentional-change path). Without the flag, a missing or mismatched golden fails.
    """
    path = GOLDEN_DIR / f"{name}.html"
    if os.environ.get("UPDATE_GOLDENS"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
        return
    assert path.is_file(), (
        f"missing golden {path} — regenerate with `UPDATE_GOLDENS=1 pytest "
        f"tests/test_requirements_renderer.py`"
    )
    expected = path.read_text(encoding="utf-8")
    assert html == expected, (
        f"golden mismatch for {name!r}. If this change is intentional, regenerate with "
        f"UPDATE_GOLDENS=1 and review the diff; otherwise the renderer drifted."
    )


# --- One golden per family -------------------------------------------------------------
@pytest.mark.parametrize("family", list(WorkFamily), ids=lambda f: f.value)
def test_golden_family_render(family: WorkFamily) -> None:
    html = render_requirements(parse_requirements(_build_family_doc(family))).html
    _check_golden(family.value, html)


# --- Rescue-path goldens (plan-review #4): assert the warning, not just the HTML ------
def test_golden_rescue_missing_classification() -> None:
    result = render_requirements(parse_requirements(_full_intent_doc("---\nstatus: refined\n---\n")))
    _check_golden("rescue_missing_classification", result.html)
    assert any("unclassified" in w for w in result.warnings)


def test_golden_rescue_garbage_classification() -> None:
    front = "---\nclassification:\n  family: definitely_not_a_family\n  confidence: 9\n---\n"
    result = render_requirements(parse_requirements(_full_intent_doc(front)))
    _check_golden("rescue_garbage_classification", result.html)
    assert any("unclassified" in w for w in result.warnings)


def test_golden_rescue_stub() -> None:
    doc = (
        "---\nclassification:\n  family: random_idea\n  confidence: 0.4\n---\n"
        "# Tiny Idea\n\n## Intent\n\nA brief thought I have not fleshed out yet.\n"
    )
    result = render_requirements(parse_requirements(doc))
    _check_golden("rescue_stub", result.html)
    assert any("stub" in w.lower() for w in result.warnings)


# --- Full structural assertion battery (from the plan's Verification list) -------------
_STYLE_RE = re.compile(r"<style\b[^>]*>(.*?)</style>", re.S)
_ROOT_BLOCK_RE = re.compile(r":root\s*\{.*?\}", re.S)
_HEX_RE = re.compile(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b")


@pytest.mark.parametrize("family", list(WorkFamily), ids=lambda f: f.value)
def test_structural_goal_card_outside_details(family: WorkFamily) -> None:
    """The Goal Card (the zero-click WHAT) is never inside a `<details>`."""
    html = render_requirements(parse_requirements(_build_family_doc(family))).html
    card = _goal_card(html)
    assert "<details" not in card
    assert "<summary" not in card


@pytest.mark.parametrize("family", list(WorkFamily), ids=lambda f: f.value)
def test_structural_family_pill_present(family: WorkFamily) -> None:
    """A validly-classified doc carries its `family-pill--{value}`, not the unclassified pill."""
    html = render_requirements(parse_requirements(_build_family_doc(family))).html
    body = _body(html)
    assert f"family-pill--{family.value}" in body
    assert "family-pill--unclassified" not in body


def test_structural_scope_compare_open_when_present() -> None:
    """Families whose recipe has a SCOPE block render the scope grid OPEN (never collapsed)."""
    html = render_requirements(parse_requirements(_build_family_doc(WorkFamily.NEW_INITIATIVE))).html
    card = _goal_card(html)
    assert "scope-grid" in card
    assert "<details" not in card  # the compare is never behind disclosure


@pytest.mark.parametrize("family", list(WorkFamily), ids=lambda f: f.value)
def test_structural_no_ids_or_anchors(family: WorkFamily) -> None:
    """Thin-spine DOM contract: zero `id=` and zero `data-block-anchor` on the rendered body
    (Phase 4 stores the quote and re-derives placement). FR-008 was superseded."""
    body = _body(render_requirements(parse_requirements(_build_family_doc(family))).html)
    assert "id=" not in body
    assert "data-block-anchor" not in body


@pytest.mark.parametrize("family", list(WorkFamily), ids=lambda f: f.value)
def test_structural_no_hardcoded_hex_outside_root(family: WorkFamily) -> None:
    """FR-012: no hardcoded hex colour anywhere OUTSIDE a `:root {}` token block — neither in
    the inlined theme nor as an inline style on the body."""
    html = render_requirements(parse_requirements(_build_family_doc(family))).html
    # Strip every :root {...} token block; no hex may remain anywhere in the document.
    stripped = _ROOT_BLOCK_RE.sub("", html)
    leftover = _HEX_RE.findall(stripped)
    assert not leftover, f"hardcoded hex outside :root for {family.value}: {leftover}"


@pytest.mark.parametrize("family", list(WorkFamily), ids=lambda f: f.value)
def test_structural_every_recipe_section_under_heading(family: WorkFamily) -> None:
    """Every rendered recipe `<section>` leads with a real `<h2>` heading, and the document
    never suppresses text selection (the Phase 4 "selectable unit" contract)."""
    body = _body(render_requirements(parse_requirements(_build_family_doc(family))).html)
    assert "user-select" not in body  # no selection suppression
    for section in re.findall(r'<section class="recipe-section">(.*?)</section>', body, re.S):
        assert "<h2" in section, f"{family.value}: a recipe-section has no <h2> heading"


def test_structural_no_per_word_span_fragmentation() -> None:
    """Contiguous text: the renderer must not fragment content into adjacent spans
    (`</span><span>`), which would break Phase 4's quote-and-re-derive placement."""
    for family in list(WorkFamily):
        body = _body(render_requirements(parse_requirements(_build_family_doc(family))).html)
        assert "</span><span" not in body.replace(" ", ""), (
            f"{family.value}: adjacent-span text fragmentation detected"
        )


# ======================================================================================
# sp2a (honest fallback): the A1 boundary — recipe-section bodies STILL render markdown.
# strip_inline_markdown is for Goal-Card escape() text ONLY; the markdown pipeline that
# realizes recipe-section bodies must keep rendering `**bold**` → <strong>. This guards
# against a future edit routing section bodies through strip_inline_markdown.
# ======================================================================================
def test_recipe_section_body_still_renders_strong() -> None:
    """A recipe-section body containing `**bold**` emits `<strong>` — NOT stripped to plain
    text. Locks the strip-only-the-card boundary (plan-review A1)."""
    doc = (
        "---\nclassification:\n  family: generic\n  confidence: 0.9\n---\n"
        "# Goal\n\n## Intent\n\n"
        + _words(210, "intent")
        + "\n\n## Open Questions\n\n- a question about **emphasized** scope\n"
    )
    body = _body(render_requirements(parse_requirements(doc)).html)
    oq_section = re.search(
        r'<section class="recipe-section">\s*<h2[^>]*>Open Questions.*?</section>',
        body,
        re.S,
    )
    assert oq_section, "Open Questions recipe section not rendered"
    assert "<strong>emphasized</strong>" in oq_section.group(0)
