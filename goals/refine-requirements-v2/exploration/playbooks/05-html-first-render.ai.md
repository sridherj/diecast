# Playbook — Step 5: HTML-First Human-Consumption Render

> **Goal:** Refine Requirements v2 · **Step 5 of 7** · **Strategy:** GO-BROAD (recommend the best
> approach, unconstrained by current code — then note the migration cost).
> **Serves:** SC-001 (2-min comprehension), SC-003 (HTML replaces md for humans), FR-001 (WHAT-before-HOW),
> FR-002 (classification pill), FR-005/FR-006 (HTML render + L1/L2/L3 + progressive disclosure),
> FR-007 (keep emitting spec-kit markdown), FR-008 (stable element IDs), FR-012 (OSS-generalizable),
> FR-013 (agents are first-class consumers).
> **Author:** cast-playbook-synthesizer · **Date:** 2026-06-11 · **Inputs:** `research/05-html-first-render.ai.md`
> (web), `research/05-html-first-render-code.ai.md` (codebase), `steps.ai.md` (Step 5), `refined_requirements.collab.md`.

---

## TL;DR

**Build one thing: a spec-kit-aware structured renderer. Everything else is reuse.**

The 2-minute test (SC-001) is an *information-architecture* problem, not a CSS problem. Today's render is
structure-blind (`md.markdown(text, extensions=[fenced_code, tables, toc, codehilite])` dumped into a
`.markdown-body` div) — it styles markdown but understands nothing about requirements. It cannot lead with
the WHAT, rank by importance, or vary by family. **That parser-renderer is the entire net-new build.** The
visual foundation is already paid for: `cast-server/.../static/style.css:2–48` `:root` tokens are
**byte-for-byte identical** to the cast-preso toolkit, fonts are loaded app-wide, native `<details>` is
already styled and used, the pill/badge pattern already exists, and a standalone-HTML serving precedent
(`/preso/review/{goal_slug}`) already ships.

The render is **five stacked layers**, top to bottom: (1) an above-the-fold **Goal Card** that is the entire
SC-001 surface — classification pill + one-sentence **job statement (L1)** + 3–5 **outcome/scope assertions
(L2)**, all WHAT, zero clicks to read; (2) a **three-level visual hierarchy** lifted from cast-preso,
distinct on size + weight + color; (3) **progressive disclosure** of depth via native `<details>` — the WHAT
is **never** collapsed; (4) **WHAT-before-HOW**, with HOW quarantined to a muted "Directional ideas" section
at the bottom, **omitted entirely** when the family makes HOW irrelevant; (5) **per-family structural
variation** driven by a **block-recipe** model (`family → ordered blocks → HTML`), not five hardcoded layouts.

The keystone decision: **the render is the origin of stable element IDs.** Emit
`<section id="fr-007" data-kind="FR" data-level="2">` at generation time and Steps 2/4/7 (comments, diffs,
round-trip) inherit durable anchors for free. Emit generic `md.markdown()` and every later feature is back to
fragile text-anchoring. HTML and the spec-kit markdown (FR-007) are **two pure projections of the same
element model** — they cannot drift. **No framework migration, no new runtime dependency, no data-model
rewrite.** The single biggest mistake to avoid: treating "HTML output" as a theming task — if the L1 line
isn't a self-contained assertion of the job, no styling passes the 2-minute test.

---

## Recommended Stack

| Component | Pick (ONE) | Version / Source | Why this, not the alternative |
|---|---|---|---|
| **Render runtime** | Server-rendered **Jinja2**, no JS framework | `jinja2>=3.1` (installed) | Static hierarchy + native disclosure need no client framework; Step 4 already returned a hard *no* on React. |
| **Element parser** | **stdlib `re` + the installed `markdown` lib's AST** → typed element model | `markdown==3.10.2` (installed) | Spec-kit markdown has textual IDs (`US1`/`FR-007`/`SC-001`) + stable section headings; parse them into `{kind, id, level, family, blocks[]}`. No new dep. |
| **Progressive disclosure** | Native **`<details>/<summary>`** | HTML standard | Zero JS, a11y-by-default, print-friendly; already styled (`style.css`) and used (`phase_tab_content.html:65`). Extend from per-file to per-section. |
| **Visual hierarchy** | **Lift cast-preso level + annotation classes** | `theme.css:100–192` → append to `style.css` | `.slide-title/.l1-body/.l2-body/.source-citation/.callout/.question-annotation`. Tokens already identical → zero token/font migration. |
| **Classification pill** | Restyle existing `[data-*]`→tint badge | `style.css:1979–1992` (`.phase-badge`) | `<span class="classification-pill" data-family="...">`; reuse the exact tint idiom. |
| **Stable IDs** | **Render-time `id="fr-007"` promotion** of spec-kit textual IDs | net-new in renderer | The keystone every later step consumes (FR-008). Renderer is the *producer*. |
| **Serving** | Clone **`/preso/review/{goal_slug}`** → `/goals/{slug}/render` | `pages.py:299–307` | Thin route serves a self-contained generated `.html`; sidesteps the `.md`-only read validation. |
| **Regeneration** | Mirror **`_rerender_tasks_md()`** → `_rerender_requirements_html()` | `task_service.py:389,428` | Writes HTML to the goal folder with the `<!-- AUTO-GENERATED -->` header convention; same `rows→render` discipline. |
| **SC-001 gate** | **LLM judge pre-screen** on headings + Goal Card | reuse cast-preso `one-clear-takeaway` / `l1-l2-hierarchy` rubric (`claude-haiku-4-5`) | CI-cheap proxy for the human timed-read; fails the render before a human ever sees it. |
| **FR-007 guard** | **Golden-file byte check** on `refined_requirements.collab.md` vs `bin/cast-spec-checker` | new pytest | The markdown contract (SC-004) can never regress when HTML generation is added. |
| **Illustrations (v2)** | **None** (default-off) | — | Decorative illustration fails the cast-preso visual checker and *slows* the scan. Defer heavy-UI/research SVG to a later increment. |

---

## Implementation Steps

> Ordered by dependency. Each step is independently shippable behind the others.

### Step 1 — Parse spec-kit markdown into a typed element model (the real build)
**Impact: 10 · Effort: M.** Write `requirements_render/parser.py`: read `refined_requirements.collab.md`,
emit an ordered list of typed elements `{kind: US|FR|SC|Intent|Scope|OpenQ|Directional, id, level, family,
blocks[]}`. Promote spec-kit textual IDs (`FR-007`) to model IDs. Assign **level by importance rule** — L1 =
"survives a 90% cut" (job statement), L2 = "survives a 50% cut" (outcomes, scope), L3 = everything else
(acceptance detail, EARS, rationale, provenance). This module is the origin of element identity (FR-008) and
the substrate Steps 2/4/7 consume. *Everything downstream depends on this — budget here.*

### Step 2 — Lift the cast-preso level + annotation CSS into `style.css`
**Impact: 7 · Effort: L.** Append `.slide-title / .l1-body / .l2-body / .source-citation / .callout /
.question-annotation` from `theme.css:100–192` to `style.css`. Tokens are already identical (`style.css:2–48`
≡ `theme.css:12–31`) so this is a pure copy-in, **zero token/font conflict**. **Hard rule: never hardcode
hex — always `var(--color-*)`** so an OSS project re-brands with a one-line `--color-accent` override (FR-012
win for free). Enforce the `l1-l2-hierarchy` rule: L2 must never visually out-weigh L1.

### Step 3 — Build the block-recipe render engine (`family → ordered blocks → HTML`)
**Impact: 9 · Effort: M.** A thin Jinja engine that selects an **ordered block recipe** per family and
renders each block with **one canonical visual treatment** (the consulting-exhibit shape: assertion heading →
bold-lead bullets → source line). Blocks: `problem`, `evidence`, `decision`, `scope`, `question`, `open`.
**Data-driven** (`FAMILY_RECIPES: dict[family, list[block]]`) so adding a family is a config change, not a
template rewrite — and it consumes whatever taxonomy Step 3 lands. Include a **generic fallback** recipe and a
**stub→prompt-to-begin** render (a 2-line input renders a *prompt to begin*, not an empty skeleton — the
Template-Enforcer guard at the render layer).

### Step 4 — Render the Goal Card (the entire SC-001 surface) + classification pill
**Impact: 10 · Effort: L–M.** Above-the-fold, always-open: classification pill (`data-family`) + version state
(`v3 · 2 open comments`) + **one-sentence job statement (L1)** + **3–5 outcome/scope assertions (L2)**. Scope
renders **open, side-by-side** (compare/contrast: muted=out / accent=in) — never collapsed (it's a
comparison). A competent stranger must pass the 2-minute test from this card *alone*, with **zero clicks**.
Pill renders Step 3's `{family, confidence}` field; confidence-gated (≥0.9 silent / 0.5–0.9 pill+confirm /
<0.5 two-option choice), one-click overridable (GitHub-issue-forms escape hatch — never a cage).

### Step 5 — Wire the progressive-disclosure boundary (WHAT open, depth collapsed)
**Impact: 8 · Effort: L.** Wrap **only depth** in per-section `<details>` (closed by default): acceptance
scenarios, EARS detail, symptom/repro, constraints, rationale, full FR/SC tables, cross-references. **The WHAT
is never behind a `<details>`** — this boundary *is* the design. A11y: every `<summary>` carries discernible
visible text; `@media print` forces all `open`; layout tolerates reflow on expand. Add an "expand all" control
for reviewers doing deep review (vs. the 2-min skim).

### Step 6 — WHAT-before-HOW: the Directional section
**Impact: 7 · Effort: L.** Confine all HOW to a single bottom **"Directional ideas"** section rendered with
the **`.question-annotation`** muted/italic grammar (visibly tentative, non-binding, subject to change by
exploration). WHAT uses the **`.callout`** accent grammar (asserted/decided). **Omit the section entirely**
when the family makes HOW irrelevant (US1 Scenario 3 — e.g. pure data-analysis). Do not pad it.

### Step 7 — Serve the standalone render + regeneration hook
**Impact: 8 · Effort: L.** Clone `/preso/review/{goal_slug}` → `GET /goals/{slug}/render`
(`HTMLResponse(refined_requirements.html)`). Add `_rerender_requirements_html()` mirroring
`_rerender_tasks_md()` (`task_service.py:389`), writing the file with the `<!-- AUTO-GENERATED -->` header on
every refinement. Markdown stays the **edit-and-agent source** (EasyMDE unchanged); HTML is a **generated,
read-only** consumption artifact (like preso review) — this cleanly decouples Step 5 from Step 4 (annotation
overlay) and Step 2 (storage).

### Step 8 — FR-007 golden-file guard + SC-001 LLM pre-screen
**Impact: 9 · Effort: M.** (a) A pytest **golden-file/byte check** that `refined_requirements.collab.md` stays
byte-compatible with `bin/cast-spec-checker` after HTML generation is added (protects SC-004). (b) An **LLM
judge** fed *only* the rendered headings + Goal Card (HTML stripped to text), prompted: *"State this goal's
job, primary outcome, and what's in/out of scope. If you cannot, say what's missing."* Reuse cast-preso's
`one-clear-takeaway` (<5s) + `l1-l2-hierarchy` criteria. Fail → fix before any human timed-read. Snapshot one
**golden HTML render per family** to catch structural regressions.

### Step 9 — (Deferred increment) Per-family illustrations
**Impact: 3 · Effort: M.** Ship v2 with **no illustrations**. Add the heavy-UI user-flow diagram and
research/architecture SVG later, *only* where a diagram out-communicates text (SVG, `viewBox`, class-named
colors, ≤5 elements, **text overlaid in HTML, not inside the image**). Flagged, not built.

---

## Architecture

```
                       ┌─────────────────────────────────────────────────────┐
  refine-requirements  │  refined_requirements.collab.md  (spec-kit markdown) │  ← FR-007, UNCHANGED
        agent  ───────▶│         the agent + downstream contract              │     (planner/suggester/checker)
                       └───────────────────────┬─────────────────────────────┘
                                               │
                                  ┌────────────▼────────────┐
                                  │  parser.py (Step 1)      │  parse US/FR/SC → typed elements
                                  │  → element model:        │  assign id="fr-007", level L1/L2/L3,
                                  │    [{kind,id,level,       │  family, blocks[]
                                  │      family, blocks[]}]   │  ◀── THE NET-NEW BUILD
                                  └────────────┬────────────┘
                                               │  (single source → two projections)
                         ┌─────────────────────┴─────────────────────┐
                         ▼                                             ▼
          ┌──────────────────────────┐                 ┌──────────────────────────────┐
          │  rows → markdown          │                 │  rows → HTML (Steps 3–6)      │
          │  (FR-007, agents)         │                 │  family → block recipe → HTML │
          │  UNCHANGED                │                 │  Goal Card · L1/L2/L3 ·        │
          └──────────────────────────┘                 │  <details> depth · Directional │
                                                        └───────────────┬───────────────┘
                                                                        │ _rerender_requirements_html()
                                                                        ▼  (AUTO-GENERATED header)
                                                        ┌──────────────────────────────┐
                                                        │  refined_requirements.html     │
                                                        └───────────────┬───────────────┘
                                                                        │ GET /goals/{slug}/render
                                                                        ▼  (clone /preso/review)
   ┌───────────────────────────────────────────────────────────────────────────────────────┐
   │  THE RENDERED PAGE (the SC-001 surface)                                                  │
   │  ┌──────────────────────────────────────────────────────────────────────────────────┐ │
   │  │ [pill: "Bug fix · debug"]                       [ v3 · 2 open comments ]            │ │ pill+version
   │  │ L1  Job statement (one sentence, the WHAT) ─ accent ─ ALWAYS open, zero clicks      │ │ ◀ Goal Card
   │  │ L2  • Outcome assertion   • In scope / Out of scope (compare-contrast, open)        │ │   (squint test)
   │  ├──────────────────────────────────────────────────────────────────────────────────┤ │
   │  │ ▸ Acceptance scenarios (EARS)        <details, closed>   L3 depth — never the WHAT  │ │ ◀ disclosure
   │  │ ▸ Symptom / repro / constraints       <details, closed>  family-specific blocks     │ │   boundary
   │  ├──────────────────────────────────────────────────────────────────────────────────┤ │
   │  │ ? Directional ideas (non-binding HOW) — muted/italic — OMITTED if HOW irrelevant    │ │ ◀ WHAT/HOW
   │  └──────────────────────────────────────────────────────────────────────────────────┘ │
   │   id="fr-007" anchors  ──▶  consumed by Step 4 (comments) · Step 7 (round-trip diff)    │
   └───────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Decisions

| Decision | Verdict | Rationale |
|---|---|---|
| Render technology | **Server-rendered Jinja, no React** | Static hierarchy + native `<details>` need no client framework; Step 4 already returned a hard *no*. |
| Source of the render | **Structured element model, not `md.markdown()`** | Generic conversion is structure-blind — can't lead with WHAT, rank levels, or vary by family. The parser is the build. |
| One source or two? | **One element model → two projections (HTML + md)** | HTML and FR-007 markdown derive from the same rows; they *cannot* drift. Agent write-back regenerates both for free (FR-013). |
| Stable element IDs | **Renderer emits `id="fr-007"` at generation time** | The keystone every later step consumes (FR-008); promotes spec-kit textual IDs to DOM anchors. |
| Per-family variation | **Block-recipe model, not 5 hardcoded layouts** | Families differ in *which blocks appear, in what order*; each block has *one* visual treatment. Adding a family = config change. |
| Disclosure boundary | **WHAT always open; depth always collapsed** | Hidden content is missed content — the WHAT behind a click fails SC-001. Disclosure is for secondary depth only. |
| Scope rendering | **Open, side-by-side (compare/contrast)** | Scope is a comparison (in vs out); NN/g says never collapse content users need to see simultaneously. |
| LLM-generated layout | **Rejected for the canonical render** | Non-deterministic, breaks golden-file testing, breaks the layer-cake scan. Model fills *content*; template fixes *layout*. |
| Serving model | **Clone `/preso/review`, not the artifact sidebar** | Sidesteps the `.md`-only read validation; the standalone-HTML loop already works for presentations. |
| Edit surface | **Markdown stays the edit + agent source; HTML is read-only** | Decouples Step 5 from annotation (Step 4) and storage (Step 2); HTML never becomes the source. |
| Illustrations (v2) | **None** | Decorative illustration fails the visual checker and slows the scan; defer per-family SVG. |
| SC-001 verification | **LLM pre-screen (CI) → human timed-read (gate)** | Cheap automated proxy catches failures before the expensive human study. |

---

## Pitfalls to Avoid

1. **Treating this as a CSS/theming task.** The hard problem is information architecture. If the L1 line isn't
   a self-contained **assertion** of the job ("Restore child-completion signalling so parents resume" — not
   "Child Completion"), no styling passes the 2-minute test. *Assertion-format headings are the single
   highest-leverage rule.*
2. **Burying the WHAT behind a `<details>`.** A reader doing the 2-minute test must need **zero clicks** to
   state the job/outcome/scope. Any disclosure on the WHAT is a bug.
3. **L2 visually competing with L1.** The eye must rank *before* it reads — differentiate on **size + weight +
   color** (color is the cheapest, most-skipped differentiator), not size alone.
4. **Rendering tentative HOW with the authority of decided WHAT.** This lies to the reader and corrupts the
   model they build. Accent/`.callout` = decided; muted/`.question-annotation` = open. Confidence must be
   *visible*.
5. **Vanity HTML that's slower than the markdown it replaces (SC-003 risk).** Decorative illustrations, dense
   multi-column layouts, animation — polish that doesn't speed comprehension is *negative value*.
6. **Per-family layouts so different the reader re-learns the page each time.** Vary *which blocks appear and
   their order*; keep *one visual grammar* across families so the layer-cake scan holds.
7. **Letting an LLM emit bespoke HTML per goal.** Non-deterministic, breaks golden-file tests, breaks scan
   consistency. Separate generation (content) from layout (template).
8. **Regressing the FR-007 markdown bytes.** Adding HTML generation must not touch the `.collab.md` bytes
   downstream agents read (SC-004). Gate with the golden-file check from day one.
9. **Rendering an empty skeleton for a stub.** A 2-line input is a *render-state*, not a family — render a
   **prompt-to-begin**, never a hollow template (Template-Enforcer guard).
10. **Density creep.** ≤50 words/block, ≤15/bullet, ≤6 elements/unit, ≥30% whitespace, ≥18pt-equivalent
    (WCAG AA). Make these **render-time warnings** — a too-dense block is an SC-001 regression caught at
    generation time.

---

## Success Metrics

| Metric | Target | How measured |
|---|---|---|
| **SC-001 — 2-minute comprehension** | ≥3 unfamiliar readers state job + outcome + scope within 2:00, **zero `<details>` expansions**, across ≥3 families | Human timed-read; record clicks/scroll/first-fixation. Preceded by the LLM pre-screen. |
| **SC-001 LLM pre-screen** | LLM judge restates WHAT from headings + Goal Card alone | CI gate using `one-clear-takeaway` + `l1-l2-hierarchy` rubric; must pass before human study. |
| **SC-003 — HTML replaces markdown for humans** | Owner reads HTML, never the md, for 2+ weeks | Owner self-report. |
| **SC-004 — downstream unchanged (FR-007)** | planner / task-suggester / spec-checker run green on v2 output | Golden-file byte check + existing agent chain on a v2-refined goal. |
| **Stable-ID coverage (FR-008)** | 100% of US/FR/SC elements carry a stable `id` anchor | Parse the rendered HTML; assert one `id` per spec-kit element. |
| **Density compliance** | Zero blocks over the limits in a passing render | Render-time warnings emit zero on golden renders. |
| **Family coverage** | One golden HTML render per family passes SC-001 | Snapshot test per family; a render that passes for a PRD but fails for a bug isn't done. |

---

## Impact Rating

**9 / 10.** This is the goal's only measurable headline criterion (SC-001) and its most visible output —
get the information architecture right and the whole "faster comprehension" thread lands; the render also
becomes the origin of the stable element IDs that unblock comments (Step 4), round-trip (Step 7), and the
markdown contract (FR-007). Held back from 10 only because the comprehension payoff depends on disciplined
*authoring* (assertion headings, tight L1 lines) the renderer can warn about but not guarantee — and on Step
3's final taxonomy landing for the block recipes.

---

## Open Items for Plan Review

1. **Block recipes depend on Step 3's final taxonomy** (5 families → possibly ~8). Build the recipe table
   data-driven (`FAMILY_RECIPES`) so adding a family is config, not a template rewrite.
2. **Pill confidence display** — confirm the three-tier UX (silent / confirm / choose) belongs in the render
   vs. only in the agent interaction.
3. **Disclosure default per family** — recommended: WHAT open, depth collapsed everywhere; confirm the owner
   accepts acceptance-scenarios-collapsed for heavy families (expand-all + print-forces-open cover review).
4. **Illustration scope** — recommend shipping v2 with **no illustrations**; add heavy-UI/research SVG as a
   later per-family increment. Confirm.
5. **SC-001 study logistics** — the ≥3 unfamiliar readers should *not* all be the maintainer (OSS-generalization
   constraint, FR-012). Who are they?

---

## Sources

**Synthesized from (this goal's research):**
- `exploration/research/05-html-first-render.ai.md` — 7-angle web research (NN/g scanning corpus, progressive
  disclosure, inverted pyramid/BLUF, visual hierarchy, Stripe/Diátaxis/ADR prior art, the render-design synthesis).
- `exploration/research/05-html-first-render-code.ai.md` — codebase terrain map (the structure-blind
  `md.markdown()` path, identical `:root` tokens, `/preso/review` serving precedent, gap analysis, migration costs).
- `exploration/steps.ai.md` §Step 5 + `refined_requirements.collab.md` (US1/US3, FR-001/002/005/006/007/008,
  SC-001/003/004).

**Primary code evidence (read these to ground the build):**
- `cast-server/cast_server/routes/api_goals.py:263–354` (generic `render_md()` to supplement) ·
  `routes/api_artifacts.py:14,52–57,132` (the other `md.markdown()` copy + `.md`-only read validation) ·
  `routes/pages.py:299–307` (`/preso/review` serving precedent to clone).
- `cast-server/cast_server/services/task_service.py:389,428` (`_rerender_tasks_md` + `AUTO-GENERATED` header to mirror).
- `cast-server/cast_server/static/style.css:2–48` (tokens ≡ cast-preso), `:1979–1992` (pill pattern) ·
  `config.py:53–73` (`PHASE_ARTIFACTS` registry).
- `skills/claude-code/cast-preso-visual-toolkit/base-template/theme.css:100–192` (`.slide-title/.l1-body/.l2-body/
  .source-citation/.callout/.question-annotation`) · `templates/slide-archetypes/consulting-exhibit.html` (the
  canonical requirement-block shape) · `visual_toolkit.human.md §5` (density limits + assertion-heading rule).
- `agents/cast-preso-check-{content,visual,tone}.md`, `cast-preso-compliance-checker.md` (SC-001 LLM pre-screen rubric).
