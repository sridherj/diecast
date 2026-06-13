"""The block-recipe render engine — the net-new build of Phase 3a (sp2, WP-B).

`render_requirements()` is a **pure, deterministic** function over a `ParsedRequirements`:
it reads the persisted classification (never re-classifies), resolves the family recipe,
pulls parser blocks per `RECIPE_REALIZATION`, and renders each realized section — in recipe
order — into the sp1 `document.html.j2` shell. It emits NO timestamps and NO run-varying
value (the `source-hash` comment is the service's job, sp4), so golden snapshots (sp5a) are
byte-stable.

Discipline (shared context + plan):
- **No I/O, no DB, no timestamps.** Templates load from the package via the sp1 Jinja env.
- **Never re-classify.** `validate_classification` only *reads* the persisted mapping.
- **Zero silent drops.** Every `unrecognized_sections` entry is surfaced inside an L3
  `<details>` and named in a warning.
- **One reused markdown instance** with `.reset()` between sections (plan-review #5) — never
  a per-block `markdown.markdown()` and never a whole-document dump.
- **Thin spine.** No element `id=`, no `data-block-anchor`; every block is one semantic
  `<section>`/`<li>` of contiguous text under a real heading (the Phase 4 DOM contract).
- **Goal Card is a placeholder here** — sp3 (`goal_card.py` + WP-D) fills the job statement
  and the L2 assertions. The slot/markup contract stays stable.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import markdown
from markupsafe import escape

from .blocks import Block, BlockKind, ParsedRequirements
from .families import (
    FAMILY_PILL_LABELS,
    FAMILY_RECIPES,
    RECIPE_REALIZATION,
    Classification,
    RecipeBlock,
    WorkFamily,
    modulate,
    validate_classification,
)
from .goal_card import derive_l2_assertions, extract_job_statement, strip_inline_markdown
from .stub import STUB_WORD_THRESHOLD, is_stub
from .templating import get_environment

# Density thresholds (warnings, NOT failures — Step 2.6).
_MAX_WORDS_PER_BLOCK = 50
_MAX_WORDS_PER_BULLET = 15
_MAX_ELEMENTS_PER_UNIT = 6

# The unclassified pill label + warning text (Step 2.1 / 2.4). Kept verbatim so the
# rescue-path tests and sp3 can assert against one source of truth.
_UNCLASSIFIED_LABEL = "Unclassified — re-run refinement to classify"
_UNCLASSIFIED_WARNING = "unclassified — re-run refinement to classify"

# --- Disclosure boundary (sp3, WP-D) ---------------------------------------------------
# Only *depth* collapses; the WHAT is always open (decisions doc + Step 3.5). These sets
# partition the recipe block kinds by visual treatment:
#
# - INTENT: pure WHAT — flowing prose, always open, never behind <details>.
# - EVIDENCE / DECISION: lead paragraph open (the assertion), the rest (evidence detail
#   beyond the lead / decision rationale) collapsed into a closed <details>.
# - USER_STORY: heading + story sentence open (L2), acceptance/EARS depth collapsed (L3).
# - FR / SC / CONSTRAINT: the table / constraint detail is depth — collapsed under the open
#   section heading. (SC *outcomes* are promoted, open, to the Goal Card assertions.)
# - SCOPE (Out of Scope) / OPEN_QUESTION: short boundary / open-item lists — left open.
_OPEN_PROSE_KINDS = frozenset({BlockKind.INTENT})
_LEAD_THEN_DEPTH_PROSE = frozenset({BlockKind.EVIDENCE, BlockKind.DECISION})
_COLLAPSED_BULLET_KINDS = frozenset(
    {BlockKind.FR, BlockKind.SC, BlockKind.CONSTRAINT}
)
_OPEN_BULLET_KINDS = frozenset({BlockKind.SCOPE, BlockKind.OPEN_QUESTION})

# The Directional muted-grammar marker (Step 3.6) — kept verbatim so tests assert one source.
_DIRECTIONAL_NOTE = "Non-binding — subject to change by exploration."


@dataclass(frozen=True)
class RenderResult:
    """The pure renderer's output: the self-contained HTML and any non-fatal warnings.

    `warnings` is a tuple (immutable, order-stable) so callers and goldens can rely on it.
    """

    html: str
    warnings: tuple[str, ...]


# --- One reused markdown instance (plan-review #5) -------------------------------------
# Module-level, configured once. Every section calls `_md_to_html`, which `.reset()`s the
# shared instance before converting — never `markdown.markdown(...)` per block (which would
# rebuild the parser each call) and never a whole-document dump (the structure-blind path
# this engine replaces). The reuse is guarded by `test_markdown_instance_reused`.
#
# Extensions are deliberately minimal: `sane_lists` only. The `extra`/`footnotes`/`attr_list`
# extensions can emit `id=` attributes (footnote anchors, header ids), which would violate
# the thin-spine DOM contract (no ids on requirement blocks) — so they are excluded by design.
_MD = markdown.Markdown(extensions=["sane_lists"], output_format="html5")


def _md_to_html(text: str) -> str:
    """Convert a markdown fragment to inline HTML using the single shared `_MD` instance,
    resetting its state first so no cross-section leakage occurs."""
    _MD.reset()
    return _MD.convert(text)


def render_requirements(
    parsed: ParsedRequirements,
    *,
    version: int | None = None,
    goal_slug: str | None = None,
    version_count: int | None = None,
) -> RenderResult:
    """Render `parsed` into the self-contained HTML document. Pure & deterministic.

    Args:
        parsed: the typed block model from the Phase 1 parser.
        version: optional current requirement version for the Goal Card chip (`v{n}`).
        goal_slug: the goal slug — needed only to link the version toggle to
            `/goals/{slug}/render/diff` (Phase 4, sp4a). Omitted ⇒ no toggle.
        version_count: how many versions exist for this goal. The diff toggle renders
            ONLY when `version_count >= 2` (there is a prior version to compare).

    Returns:
        A `RenderResult` with the composed HTML and any density / rescue warnings.
    """
    warnings: list[str] = []

    classification, family, unclassified = _resolve_classification(parsed, warnings)

    # Stub gate (Step 2.2): short-circuit BEFORE the recipe — never an empty skeleton.
    if is_stub(parsed):
        warnings.append(
            f"stub document — refine to build it out "
            f"(below STUB_WORD_THRESHOLD={STUB_WORD_THRESHOLD} words)"
        )
        html = _compose(
            parsed,
            goal_card_html=_render_stub_card(
                parsed, family, unclassified, classification.reasoning
            ),
            recipe_sections_html="",
            unmodeled_html="",
            directional_html="",
            version=version,
            goal_slug=goal_slug,
            version_count=version_count,
        )
        return RenderResult(html=html, warnings=tuple(warnings))

    blocks_by_kind = _group_by_kind(parsed.blocks)

    # Resolve the family recipe (with modifiers) ONCE — both the Goal Card (scope-grid gate)
    # and the recipe-section pipeline read it, so they can never disagree on SCOPE presence.
    recipe = modulate(
        FAMILY_RECIPES[family],
        irreversible=classification.modifiers.irreversible,
        unknown_cause=classification.modifiers.unknown_cause,
    )

    goal_card_html = _render_goal_card(
        parsed,
        family,
        unclassified,
        version,
        recipe,
        blocks_by_kind,
        warnings,
        classification.reasoning,
    )
    recipe_sections_html = _render_recipe_sections(recipe, blocks_by_kind, warnings)
    unmodeled_html = _render_unmodeled(parsed, warnings)
    directional_html = _render_directional(blocks_by_kind, warnings)

    html = _compose(
        parsed,
        goal_card_html=goal_card_html,
        recipe_sections_html=recipe_sections_html,
        unmodeled_html=unmodeled_html,
        directional_html=directional_html,
        version=version,
        goal_slug=goal_slug,
        version_count=version_count,
    )
    return RenderResult(html=html, warnings=tuple(warnings))


# --- Classification (read-only; never re-classifies) -----------------------------------
def _resolve_classification(
    parsed: ParsedRequirements, warnings: list[str]
) -> tuple[Classification, WorkFamily, bool]:
    """Read the persisted `classification` front-matter (Step 2.1 / 2.4).

    Absent OR unparseable ⇒ `GENERIC` recipe + the *unclassified* rescue state (a distinct
    pill) + a warning. A present, valid classification is used verbatim. NEVER crashes
    (`validate_classification` is defence-in-depth) and NEVER re-classifies.
    """
    raw = parsed.front_matter.get("classification")
    classification = validate_classification(raw if isinstance(raw, dict) else {})

    # "Unparseable" = absent, or present-but-the-family-coerced (the model gave us garbage
    # the validator had to rescue to random_idea). Either way we fall to GENERIC + the
    # unclassified pill — distinct from a model-*selected* generic/random_idea.
    family_was_coerced = any(c.startswith("family ") for c in classification.coercions)
    if raw is None or family_was_coerced:
        warnings.append(_UNCLASSIFIED_WARNING)
        return classification, WorkFamily.GENERIC, True

    return classification, classification.family, False


# --- Recipe sections (the pipeline core) -----------------------------------------------
def _render_recipe_sections(
    recipe: tuple[RecipeBlock, ...],
    blocks_by_kind: dict[BlockKind, list[Block]],
    warnings: list[str],
) -> str:
    """Render each realized section of the (already-modulated) recipe in recipe order.
    Skips a recipe block with no realized content — never pads (Step 2.1)."""
    rendered: list[str] = []
    consumed: set[BlockKind] = set()
    for recipe_block in recipe:
        realization = RECIPE_REALIZATION[recipe_block]
        for heading, kind in zip(realization.headings, realization.block_kinds):
            if kind in consumed:
                continue
            blocks = blocks_by_kind.get(kind, [])
            if not blocks:
                continue  # no realized content — skip, do not pad
            consumed.add(kind)
            rendered.append(_render_section(heading, kind, blocks, warnings))
    return "\n".join(rendered)


def _render_section(
    heading: str, kind: BlockKind, blocks: list[Block], warnings: list[str]
) -> str:
    """One canonical consulting-exhibit treatment under a real `<h2>`, with the **disclosure
    boundary** applied (Step 3.5): the section's lead assertion is always open; only *depth*
    collapses into a closed `<details>`. Contiguous text, no `id=`, no `data-block-anchor`
    (Phase 4 DOM contract)."""
    head_html = f'<h2 class="slide-title">{escape(heading)}</h2>'

    if kind is BlockKind.USER_STORY:
        body_html = _render_user_stories(heading, blocks, warnings)
    elif kind in _OPEN_PROSE_KINDS:
        body_html = _render_prose(heading, blocks, warnings)
    elif kind in _LEAD_THEN_DEPTH_PROSE:
        body_html = _render_prose_lead_then_depth(heading, blocks, warnings)
    elif kind in _COLLAPSED_BULLET_KINDS:
        body_html = _render_collapsed_bullets(heading, blocks, warnings)
    else:  # _OPEN_BULLET_KINDS — Out of Scope / Open Questions stay open
        body_html = _render_bullets(heading, blocks, warnings)

    return (
        f'<section class="recipe-section">\n{head_html}\n{body_html}\n</section>'
    )


def _render_prose(heading: str, blocks: list[Block], warnings: list[str]) -> str:
    """Render whole-section (level-1) blocks as flowing prose under the section heading,
    fully **open** — this is the WHAT (Intent), never behind `<details>`. The leading
    `## Heading` line is stripped (it is already the `<h2>`)."""
    weight = "l1-body" if any(b.kind is BlockKind.INTENT for b in blocks) else "l2-body"
    parts: list[str] = []
    for block in blocks:
        body = _strip_leading_heading(block.body)
        _warn_density(heading, body, _MAX_WORDS_PER_BLOCK, "block", warnings)
        parts.append(_md_to_html(body))
    return f'<div class="{weight}">\n' + "\n".join(parts) + "\n</div>"


def _render_prose_lead_then_depth(
    heading: str, blocks: list[Block], warnings: list[str]
) -> str:
    """Render Evidence / Decisions: the **lead paragraph is open** (the assertion), the
    remaining depth (evidence beyond the lead, decision rationale) collapses into a closed
    `<details>` whose `<summary>` carries the section heading (Step 3.5)."""
    lead_parts: list[str] = []
    depth_parts: list[str] = []
    for block in blocks:
        body = _strip_leading_heading(block.body)
        _warn_density(heading, body, _MAX_WORDS_PER_BLOCK, "block", warnings)
        lead, depth = _split_lead_and_depth(body)
        lead_parts.append(_md_to_html(lead))
        if depth:
            depth_parts.append(_md_to_html(depth))

    html = '<div class="l2-body">\n' + "\n".join(lead_parts) + "\n</div>"
    if depth_parts:
        html += "\n" + _details(
            f"More on {heading}", '<div class="l2-body">\n'
            + "\n".join(depth_parts)
            + "\n</div>"
        )
    return html


def _render_collapsed_bullets(
    heading: str, blocks: list[Block], warnings: list[str]
) -> str:
    """Render FR / SC / Constraints: the section heading stays open, but the table rows /
    constraint detail are **depth** — collapsed into a closed `<details>` whose `<summary>`
    carries the section heading (Step 3.5). SC *outcomes* are promoted, open, to the Goal
    Card; this is the full table behind the disclosure."""
    inner = _render_bullets(heading, blocks, warnings)
    count = len(blocks)
    summary = f"{heading} ({count})" if count else heading
    return _details(summary, inner)


def _render_bullets(heading: str, blocks: list[Block], warnings: list[str]) -> str:
    """Render element (level-2) blocks as bold-lead bullets in a single `<ul>`."""
    if len(blocks) > _MAX_ELEMENTS_PER_UNIT:
        warnings.append(
            f"density: section '{heading}' has {len(blocks)} elements "
            f"(>{_MAX_ELEMENTS_PER_UNIT})"
        )
    items: list[str] = []
    for block in blocks:
        items.append(_render_bullet(block, heading, warnings))
    return "<ul>\n" + "\n".join(items) + "\n</ul>"


def _render_bullet(block: Block, heading: str, warnings: list[str]) -> str:
    """A single `<li class="l2-body">` with an optional bold lead (ref or heading)."""
    lead, body = _bullet_lead_and_body(block)
    _warn_density(heading, body, _MAX_WORDS_PER_BULLET, "bullet", warnings)
    lead_html = f"<strong>{escape(lead)}</strong> " if lead else ""
    body_html = _md_to_html(body) if body else ""
    return f'<li class="l2-body">{lead_html}{body_html}</li>'


def _bullet_lead_and_body(block: Block) -> tuple[str, str]:
    """Derive the bold lead + the remaining body for an element block.

    - FR/SC table rows: lead = ref (`FR-007`), body = the row's description cell(s).
    - User stories: lead = heading (`US1 — …`), body = the story minus its heading line.
    - Bullets (constraints / scope / open questions): no lead; body is the bullet text.
    """
    if block.kind in (BlockKind.FR, BlockKind.SC) and block.ref:
        return block.ref, _row_description(block.body)
    if block.kind is BlockKind.USER_STORY and block.heading:
        return block.heading, _strip_leading_heading(block.body)
    return "", block.body


def _render_user_stories(
    heading: str, blocks: list[Block], warnings: list[str]
) -> str:
    """Render User Stories: each story's heading + story sentence are **open** (L2); the
    acceptance / EARS depth collapses into a closed `<details>` whose `<summary>` carries the
    story heading as visible text (Step 3.5)."""
    parts: list[str] = []
    for block in blocks:
        story_heading = block.heading or "User story"
        body = _strip_leading_heading(block.body)
        _warn_density(heading, body, _MAX_WORDS_PER_BLOCK, "block", warnings)
        lead, depth = _split_lead_and_depth(body)
        lead_html = _md_to_html(lead) if lead else ""
        story = (
            '<div class="user-story">\n'
            f'<p class="l2-body"><strong>{escape(story_heading)}</strong></p>\n'
            f"{lead_html}"
        )
        if depth:
            story += "\n" + _details(
                story_heading, f'<div class="l2-body">\n{_md_to_html(depth)}\n</div>'
            )
        story += "\n</div>"
        parts.append(story)
    return "\n".join(parts)


def _details(summary: str, body_html: str) -> str:
    """A closed `<details>` with a non-empty `<summary>` (the assertion heading) — the one
    disclosure primitive for *depth*. Never emits an empty summary (Step 3.5 a11y rule)."""
    label = summary.strip() or "Details"
    return (
        '<details>\n'
        f"<summary>{escape(label)}</summary>\n"
        f'<div class="details-body">{body_html}</div>\n'
        "</details>"
    )


def _split_lead_and_depth(body: str) -> tuple[str, str]:
    """Split a prose body into (lead_paragraph, remaining_depth). The lead is the first
    paragraph (the assertion that stays open); the depth is everything after the first blank
    line. A single-paragraph body has no depth."""
    paragraphs = body.split("\n\n", 1)
    lead = paragraphs[0].strip()
    depth = paragraphs[1].strip() if len(paragraphs) > 1 else ""
    return lead, depth


def _render_unmodeled(parsed: ParsedRequirements, warnings: list[str]) -> str:
    """Render every `unrecognized_sections` entry verbatim inside an L3 `<details>` labelled
    "unmodeled section", and append a warning naming it. Zero silent drops (Step 2.5)."""
    parts: list[str] = []
    for name in parsed.unrecognized_sections:
        warnings.append(f"unmodeled section preserved: '{name}'")
        body = _section_body(parsed.source_text, name)
        body_html = _md_to_html(body) if body else ""
        parts.append(
            "<details class=\"unmodeled\">\n"
            f"<summary>Unmodeled section: {escape(name)}</summary>\n"
            f'<div class="details-body">{body_html}</div>\n'
            "</details>"
        )
    return "\n".join(parts)


def _render_directional(
    blocks_by_kind: dict[BlockKind, list[Block]], warnings: list[str]
) -> str:
    """WHAT-before-HOW (Step 3.6): render DIRECTIONAL **last**, in the muted/italic
    `.question-annotation` grammar, marked non-binding. **Omit-not-pad** — return ``""`` when
    no Directional block exists (the family making HOW irrelevant needs no placeholder);
    render it when an author wrote genuine Directional content (even in such a family). The
    render is not a second enforcement point — Phase 2's checker already WARNs on stray HOW."""
    blocks = blocks_by_kind.get(BlockKind.DIRECTIONAL, [])
    if not blocks:
        return ""
    parts: list[str] = []
    for block in blocks:
        body = _strip_leading_heading(block.body)
        _warn_density("Directional", body, _MAX_WORDS_PER_BLOCK, "block", warnings)
        parts.append(_md_to_html(body))
    return (
        '<aside class="directional">\n'
        '<h2>Directional</h2>\n'
        '<div class="question-annotation">\n'
        '<span class="question-icon">✎</span>\n'
        '<div class="question-text">\n'
        f'<p class="source-citation">{escape(_DIRECTIONAL_NOTE)}</p>\n'
        + "\n".join(parts)
        + "\n</div>\n</div>\n</aside>"
    )


# --- Goal Card (the zero-click SC-001 surface — sp3, WP-C) ------------------------------
def _render_goal_card(
    parsed: ParsedRequirements,
    family: WorkFamily,
    unclassified: bool,
    version: int | None,
    recipe: tuple[RecipeBlock, ...],
    blocks_by_kind: dict[BlockKind, list[Block]],
    warnings: list[str],
    reasoning: str,
) -> str:
    """Render the zero-click Goal Card — the entire SC-001 above-the-fold surface (Step 3.3).

    Always open, outside any `<details>`: the family pill (+ reasoning title), the version
    chip (omitted when no snapshot), the inert `[PENDING Phase 4]` open-comment-count slot,
    the L1 job statement, the 3–5 L2 assertions, and the open scope-compare grid. The IA
    heuristics live in `goal_card.py`; this function only *renders* their output.
    """
    pill_html = _render_pill(family, unclassified, reasoning)
    chip_html = (
        f'<span class="version-chip">v{int(version)}</span>' if version is not None else ""
    )
    title = parsed.title or "Untitled goal"

    job_statement, job_warning = extract_job_statement(parsed)
    if job_warning:
        warnings.append(job_warning)
    assertions = derive_l2_assertions(parsed)

    job_html = f'<p class="goal-card__job-text l1-body">{escape(job_statement)}</p>'
    assertions_html = _render_assertions(assertions)
    scope_grid_html = _render_scope_grid(recipe, blocks_by_kind)

    return (
        '<section class="goal-card">\n'
        f"{pill_html}{chip_html}\n"
        f'<h1 class="slide-title">{escape(title)}</h1>\n'
        # Inert open-comment-count slot — renders nothing until Phase 4 wires the live count.
        "<!-- open-comment-count: [PENDING Phase 4] -->\n"
        f'<div class="goal-card__job">\n{job_html}\n</div>\n'
        f"{assertions_html}"
        f"{scope_grid_html}"
        "</section>"
    )


def _render_assertions(assertions: list[str]) -> str:
    """Render the 3–5 L2 assertions as an open list. Empty when none exist — a sparse card is
    honest (never padded). Each assertion is plain escaped text (no markdown wrapper)."""
    if not assertions:
        return ""
    items = "\n".join(
        f'<li class="l2-body">{escape(a)}</li>' for a in assertions
    )
    return f'<ul class="goal-card__assertions">\n{items}\n</ul>\n'


def _render_scope_grid(
    recipe: tuple[RecipeBlock, ...], blocks_by_kind: dict[BlockKind, list[Block]]
) -> str:
    """The open, side-by-side scope compare (Step 3.4): primary outcomes (`.callout` accent)
    vs. Out-of-Scope boundaries (muted). Renders **open** (a comparison is never collapsed)
    and is **omitted entirely** when the family's recipe has no `SCOPE` block."""
    if RecipeBlock.SCOPE not in recipe:
        return ""

    outcomes = [
        strip_inline_markdown(_row_description(b.body))
        for b in blocks_by_kind.get(BlockKind.SC, [])
    ]
    out_of_scope = [
        strip_inline_markdown(_strip_leading_marker(b.body))
        for b in blocks_by_kind.get(BlockKind.SCOPE, [])
    ]
    if not outcomes and not out_of_scope:
        return ""

    left = (
        '<div class="scope-col scope-col--in callout"><div class="callout-text">\n'
        "<h3>In focus</h3>\n"
        + _ul(outcomes, "l2-body")
        + "\n</div></div>"
    )
    right = (
        '<div class="scope-col scope-col--out">\n'
        "<h3>Out of scope</h3>\n"
        + _ul(out_of_scope, "l2-body muted")
        + "\n</div>"
    )
    return f'<div class="scope-grid">\n{left}\n{right}\n</div>\n'


def _ul(items: list[str], li_class: str) -> str:
    """A simple `<ul>` of escaped plain-text items (no markdown). Empty list ⇒ a muted dash
    placeholder so a one-sided compare still renders a balanced grid."""
    if not items:
        return f'<ul><li class="{li_class}">—</li></ul>'
    body = "\n".join(f'<li class="{li_class}">{escape(_first_line(i))}</li>' for i in items)
    return f"<ul>\n{body}\n</ul>"


def _first_line(text: str) -> str:
    """The first non-empty line of `text`, whitespace-collapsed — keeps the scope compare to
    one glanceable phrase per item."""
    for line in text.split("\n"):
        if line.strip():
            return " ".join(line.split())
    return ""


def _strip_leading_marker(text: str) -> str:
    """Strip a single leading list marker (`- `, `* `) from a bullet body for the scope grid."""
    return re.sub(r"^\s*[-*]\s+", "", text.strip(), count=1)


def _render_stub_card(
    parsed: ParsedRequirements, family: WorkFamily, unclassified: bool, reasoning: str
) -> str:
    """The stub → prompt-to-begin card (Step 2.2): names what exists and invites refinement,
    never an empty skeleton. Returned in place of the Goal Card + recipe sections."""
    pill_html = _render_pill(family, unclassified, reasoning)
    title = parsed.title or "Untitled goal"
    preamble = parsed.preamble.strip()
    existing = (
        f'<p class="l2-body">{_md_to_html(preamble)}</p>' if preamble else ""
    )
    return (
        '<section class="goal-card">\n'
        f"{pill_html}\n"
        f'<h1 class="slide-title">{escape(title)}</h1>\n'
        '<div class="callout"><div class="callout-text l1-body">\n'
        "<p>This goal is just getting started — there is not enough yet to render.</p>\n"
        f"{existing}\n"
        "<p><em>Refine this goal to build it out.</em></p>\n"
        "</div></div>\n"
        "</section>"
    )


def _render_pill(family: WorkFamily, unclassified: bool, reasoning: str = "") -> str:
    """The family pill — or the distinct dashed `family-pill--unclassified` rescue state.

    Hover reveals the model's `reasoning` via the native `title` attribute (Step 3.3); it is
    omitted when there is no reasoning so the markup stays clean and the goldens stable.
    """
    title_attr = f' title="{escape(reasoning)}"' if reasoning else ""
    if unclassified:
        return (
            f'<span class="family-pill family-pill--unclassified"{title_attr}>'
            f"{escape(_UNCLASSIFIED_LABEL)}</span>"
        )
    label = FAMILY_PILL_LABELS[family]
    return (
        f'<span class="family-pill family-pill--{family.value}"{title_attr}>'
        f"{escape(label)}</span>"
    )


# --- Compose into the sp1 shell --------------------------------------------------------
def _compose(
    parsed: ParsedRequirements,
    *,
    goal_card_html: str,
    recipe_sections_html: str,
    unmodeled_html: str,
    directional_html: str,
    version: int | None = None,
    goal_slug: str | None = None,
    version_count: int | None = None,
) -> str:
    """Render the sp1 `document.html.j2` shell with the four pre-built HTML fragments.

    Fragments are built in Python (user text already escaped via markdown/`escape`) and
    injected with `| safe` in the template — autoescape stays on for everything else.

    The version toggle (Phase 4, sp4a) renders ONLY when a `goal_slug` is supplied AND
    `version_count >= 2` (a prior version exists to diff against). It is a plain link to
    the throwaway diff view — the canonical render itself gains no `id=` and no script.
    """
    env = get_environment()
    template = env.get_template("document.html.j2")
    show_diff_toggle = bool(goal_slug) and (version_count or 0) >= 2
    return template.render(
        document_title=parsed.title or "Requirements",
        goal_card_html=goal_card_html,
        recipe_sections_html=recipe_sections_html,
        unmodeled_html=unmodeled_html,
        directional_html=directional_html,
        show_diff_toggle=show_diff_toggle,
        goal_slug=goal_slug,
        current_version=version,
    )


# --- Small pure helpers ----------------------------------------------------------------
def _group_by_kind(blocks: tuple[Block, ...]) -> dict[BlockKind, list[Block]]:
    """Group parser blocks by kind, preserving source order within each kind."""
    grouped: dict[BlockKind, list[Block]] = {}
    for block in blocks:
        grouped.setdefault(block.kind, []).append(block)
    return grouped


def _strip_leading_heading(body: str) -> str:
    """Drop a single leading ATX heading line (`#`/`##`/`###` …) from a block body — the
    section already carries that heading as its `<h2>`/lead."""
    lines = body.split("\n")
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    if idx < len(lines) and lines[idx].lstrip().startswith("#"):
        idx += 1
    return "\n".join(lines[idx:]).strip()


def _row_description(row: str) -> str:
    """Extract the human description from an FR/SC markdown table row.

    `| FR-001 | <description> | <source> |` → the description cell (the id is already the
    bold lead; the trailing source/trace cell is dropped for the headline treatment).
    """
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    cells = [c for c in cells if c]
    if len(cells) >= 2:
        return cells[1]
    return cells[-1] if cells else row.strip()


def _section_body(source_text: str, name: str) -> str:
    """Re-derive a named H2 section's verbatim body from the source, reusing the Phase 1
    parser's own section-span grammar so this can never drift from it."""
    # Imported lazily to keep the dependency local to the one call site.
    from .parser import _section_spans, _slice_body

    lines = source_text.split("\n")
    spans = _section_spans(lines)
    if name not in spans:
        return ""
    start, end = spans[name]
    return _slice_body(lines, start, end)


def _warn_density(
    heading: str, text: str, limit: int, unit: str, warnings: list[str]
) -> None:
    """Append a density warning (never a failure) when `text` exceeds `limit` words."""
    count = len(text.split())
    if count > limit:
        warnings.append(
            f"density: {unit} in section '{heading}' is {count} words (>{limit})"
        )
