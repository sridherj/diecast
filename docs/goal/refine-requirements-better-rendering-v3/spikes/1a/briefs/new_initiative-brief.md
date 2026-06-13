# Maker brief — `new_initiative` family (spike 1a)

> **Conscious non-delegation (record it):** `/cast-preso-how` is **NOT** invoked for this
> spike. That agent generates a reveal.js *slide* and the net-new requirements maker agents
> are Phase-3-owned. This brief follows only the **8-step preso-how discipline by hand**,
> adapted to a **scrolling document page** (not a 1920×1080 slide). An execution-time reader
> must neither invoke the slide agent here nor skip the discipline.

Source: `docs/goal/refine-requirements-better-rendering-v3/refined_requirements.collab.md`
(this goal's own classified doc — the only real `new_initiative` doc in the repo).

## Step 1 — Brainstorm 2–3 visual approaches

**Approach A — "Slide-deck-as-scroll" (one archetype per scroll section).**
Treat the page as a vertical sequence of preso archetypes: single-stat-hero Goal Card →
compare-contrast for the chosen direction → outcome cards for the user stories →
consulting-exhibit tables for FRs/SCs → scope compare → one-statement open question.
*Pro:* maximal reuse of the toolkit's named archetypes; each section lands one idea.
*Con:* risk of feeling like 8 disconnected slides stacked rather than one document.
*Steve-Jobs test:* **passes** if a connective spine (running accent rail + numbered section
markers) is added so it reads as one argument, not a pile.

**Approach B — "Dense brief" (everything above the fold, tight two-column body).**
A newspaper-style masthead + multi-column requirement grid.
*Pro:* information-dense, few scrolls. *Con:* fails SC-001 — the zero-click surface gets
crowded and the job/outcome/scope stop being instantly restate-able; violates the toolkit's
30% whitespace / one-idea discipline. *Steve-Jobs test:* **fails** — clever, not clear.

**Approach C — "Narrative long-read" (prose-first, ids as footnote-style margin tags).**
*Pro:* readable. *Con:* buries the FR/SC backbone and the per-block id labels into running
prose, making FR-003 per-block correspondence fragile and the scan-for-a-requirement task
slow. *Steve-Jobs test:* **fails for this artifact** — a requirements render must stay
scannable by id, not only readable as an essay.

**Chosen: Approach A**, with the connective accent rail from the critique.

## Step 2 — Archetype shortlist (from the 11-archetype toolkit library)

| Scroll section | Archetype borrowed | Why |
|---|---|---|
| Goal Card (zero-click) | **single-stat-hero** + **one-statement** | The job statement is the one thing; family pill + job + in/out scope, ≥ a third whitespace. |
| The bet (Intent) | **illustrated-section-opener** vocabulary (no raster — inline accent rule) | A breathing intro paragraph that frames *why now*. |
| Key decisions | **compare-contrast** (chose ▸ over ▸ because) | The Decisions table *is* a set of binary contrasts; the contrast is the insight. |
| What the reader experiences | **build-up-sequence** of outcome cards | US1–US7 are ordered outcomes; each card one complete thought. |
| What we're building | **consulting-exhibit** | FR rows = evidence body under an action-title section head. |
| How we'll know it worked | **consulting-exhibit** | SC rows = measurable outcomes; source/measure line per row. |
| In focus / Out of scope | **compare-contrast** | The scope grid is a two-column compare by construction. |
| The one deferred knob | **one-statement** | A single muted statement; quiet by design. |

## Step 3 — (this brief)

## Step 4 — Craft discipline (applied in `new_initiative-maker.html`)

- **Style tokens lifted verbatim** from `visual_toolkit.human.md`: `--color-bg #F5F4F0`,
  `--color-text #1A1A28`, `--color-muted #4A4860`, `--color-surface #ECEAE4`,
  `--color-accent #D6235C`; IBM Plex Mono headings / DM Sans body; the 40px 3–4%-opacity
  engineering-grid background; heading tracking -0.02em. Adapted from reveal's 32px slide
  base to a 17px document base (a scroll page, not a projected slide).
- **Family-appropriate section names**, never US/FR/SC slots: *"The bet," "Key decisions,"
  "What a reader walks away with," "What we're building," "How we'll know it worked,"
  "In focus / Out of scope."*
- **Canonical ids as visible anchoring labels** (`<span class="anchor">FR-003</span>`),
  never `id=` attributes. Every id from the source appears exactly once, on the block whose
  text it identifies (FR-003 per-block correspondence).
- **DOM contract:** each requirement unit is one contiguous semantic `<section class="req-unit">`
  or `<li class="req-unit">` under a real `<h2>`/`<h3>`; zero `id=`, zero `data-block-anchor`.
- **Self-contained:** all CSS inline; no CDN fonts (system-stack fallbacks only); the only
  external refs are the FR-028-sanctioned `/static/htmx.min.js` +
  `/static/requirements_comments.js` and `data-goal-slug` on `<body>` — so **sp1b can reuse
  this file** as its varying maker-style HTML.

## Step 5–8 — covered by the audits + checker

Audits (`spike_id_audit.py`, self-containment grep, zero-`id` grep) and the
`cast-requirements-checker` delegation stand in for the slide-checker. The human-eyeball
browser pass is a **carry-forward** item (autonomous run — no browser).
