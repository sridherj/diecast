# Code Exploration: Prototype Build Approach (Step 06)

**Goal context:** Build a VISION-GRADE clickable HTML prototype of Diecast — self-contained
HTML/JS/CSS, no backend, no build step, realistic fake data, scripted chat moments,
canvas-morph transitions, scenario-chooser entry, demo-script overlay. (refined_requirements
v0.3.0; FR-001, FR-002, FR-004, FR-019)
**Codebase:** /data/workspace/diecast (+ referenced deck at
/data/workspace/second-brain/taskos/goals/taskos-gtm/presentation_v3)
**Date:** 2026-06-11
**Framing:** VISION-FIRST terrain map. Existing assets are reference, never an anchor.
This file delivers a **strictly-optional reuse list** — what to lift, what to drop, with reasons.

---

## TL;DR for the synthesizer

There are exactly **two pools of existing HTML craft** in reach, and they pull in opposite
directions:

1. **The preso v2/v3 deck** (`presentation_v3/`) + **`cast-preso-visual-toolkit` skill** —
   gorgeous, but it is a **reveal.js slide deck built with a Vite single-file build step**,
   and its key surfaces (board, marketplace, resume, chain, dashboard) are **hand-drawn inline
   SVG exhibits**, not interactive DOM. Reuse its **design language + canonical fake
   data/vocabulary + screen compositions as visual blueprints**. **Drop** reveal.js, the Vite
   build, the slide-archetype catalog, the cast-preso-* agent pipeline, and the SVG exhibits as
   live UI.

2. **`docs/plan/mockups/runs-threaded.html`** — the **only real app-chrome HTML in the entire
   repo**. Vanilla, no build step, `onclick="this.classList.toggle('expanded')"` interactivity,
   CDN fonts, a richer app-grade token palette (success/warning/danger/info/focus + radius
   scale). This is the **truer substrate precedent** for a clickable product and the closest
   thing to the prototype's actual build recipe. It directly seeds US3's execution drill-in
   (run dispatch tree).

**The cheapest credible recipe the repo already proves works:** a single (or few) hand-authored
HTML file(s), `:root` CSS-token design system, vanilla `classList.toggle` / tiny JS state
machine for interactivity, CDN Google Fonts, **no framework and no build step** — exactly the
`runs-threaded.html` pattern, scaled up with the deck's design tokens and screen blueprints.
The canvas-morph, scenario-chooser, and demo-script overlay have **no existing precedent** and
are greenfield (small, well-understood greenfield).

---

## 1. Data Model & Schema

No runtime data model is relevant — the deliverable is static with fake data (FR-001). The
"schema" that matters here is the **fake-data spine** (Directional Idea: one coherent fictional
org reused across every screen) and the **design-token schema**. Both already exist in partial
form and are reusable.

### 1a. Canonical fake-data vocabulary (REUSE verbatim — high value, zero cost)

The preso v3 and the requirements already fix a consistent fictional vocabulary. Lifting it
verbatim makes the prototype's screens feel like one product and satisfies FR-018 brand rules:

| Token | Value | Source | Maps to |
|-------|-------|--------|---------|
| Ticket id | `CAST-412` | refined_requirements FR-010; preso a08–a11 | US5 board/ticket arc |
| Checker rule codes | `M04` / `S03` / `R02` | FR-010; preso a09 | US5 S2 inline violations |
| Rework budget | `1/3 used` | FR-010; preso a09 | US5 S2 rework budget |
| Reversibility levels | `L1 / L2 / L3` | FR-022; preso a10–a11 | US10 autonomy model |
| Canonical agent | `crud-orchestrator` | Constraints; preso | marketplace/board |
| 8-agent chain | refine → decompose → research → synthesize → plan → detail → orchestrate → run | US9 S2; preso `A-v3-chain` | US9 pipeline view |
| 12 named contracts | (enumerated on `A-v3-chain` / Layer-2 slide) | US9 S1; preso `s7-layer-2` | US9 catalogue |
| Archetypes | Maker / Checker / Decision / Spike / Escalation / Mentor | US6 S5; preso marketplace | US6 marketplace |
| Marketplace cred stat | "99.9% compliant code in 2 maker-checker loops across 505 runs" | US6 S3 | US6 credibility |

**Action:** extract this into a single `data/fixtures.js` (plain JS object literals) so every
screen reads from one spine. This is the cheapest highest-leverage reuse in the whole step.

### 1b. Design-token schema (REUSE — two variants exist; merge them)

Two `:root` token sets exist. The prototype should adopt the **superset**:

- **Deck tokens** (`presentation_v3/presentation/index.html` lines 19–55;
  `cast-preso-visual-toolkit/templates/css/*.css`): cream/navy/raspberry identity —
  `--color-bg #F5F4F0`, `--color-text #1A1A28`, `--color-muted #4A4860`,
  `--color-surface #ECEAE4`, `--color-accent #D6235C`, callout/question bg pairs, font stacks
  (`IBM Plex Mono` headings / `DM Sans` body). Strong, distinctive, "engineering-notebook" feel.
- **App-mockup tokens** (`docs/plan/mockups/runs-threaded.html` lines 11–30): the **same**
  identity **plus app-grade additions** the deck lacks — `--color-success #2D7D4F`,
  `--color-warning #B5821A`, `--color-danger #B22439`, `--color-info #3B5BB0`,
  `--color-focus #6B47B0`, `--color-border #DDD8CD`, `--color-faint #8E8AA3`,
  `--radius-sm/md/lg`, white `--color-surface #FFFFFF` for cards on cream.

**Finding:** the mockup token set is the better foundation — it already extended the deck palette
toward real app UI (status colors, borders, radii). **Adopt the mockup `:root` as the base**,
keep the deck's accent/identity values. The token-override pattern (visual_toolkit Section 10)
documents how theming cascades — reusable as-is.

---

## 2. Existing Implementation (the reuse inventory)

### 2a. `cast-preso-visual-toolkit` skill — `skills/claude-code/cast-preso-visual-toolkit/`

**228KB skill.** Contents and reuse verdict:

| Asset | Path | Verdict | Why |
|-------|------|---------|-----|
| Style tokens table | `visual_toolkit.human.md` §1 | **REUSE** | Authoritative token list; copy into prototype `:root`. |
| Typography scale | `visual_toolkit.human.md` §2 | **REUSE (adapt)** | Font stacks + scale are good; the em-based reveal sizing is deck-specific, rescale to px for an app. |
| Grid background CSS | `templates/css/grid-background.css` | **REUSE** | Cheap "precision notebook" identity; two `linear-gradient`s on a container. Drop the print override. |
| Callout / question CSS | `templates/css/components.css`, `templates/components/*.html` | **MAYBE** | Generic annotation chip (accent left-border + number badge). Reusable as a generic "decision/comment chip", but semantics are presenter-assertion; re-skin if used. |
| Slide-archetype catalog (9) | `templates/slide-archetypes/*.html`, `visual_toolkit.human.md` §9 | **DROP** | single-stat-hero, compare-contrast, timeline, takahashi, etc. are **rhetorical slide layouts**, not app screens. Useless for a clickable product. |
| Illustration style guide | `visual_toolkit.human.md` §8 | **DROP** | Watercolor/Stitch image-gen workflow; the prototype is UI, not editorial illustration. |
| Base template (Vite) | `base-template/{index.html,main.js,theme.css,vite.config.js,package.json}` | **DROP the build** | `vite.config.js` uses `vite-plugin-singlefile`; `package.json` declares `vite ^6` + a `build` script. This is a **build step** — violates FR-001 "no build step required". The CDN comment-block in `base-template/index.html` (lines 8–11) shows the no-build escape hatch; that pattern survives, the Vite pipeline does not. |

### 2b. The preso v3 deck — `presentation_v3/presentation/index.html` (6,665 lines, 25 sections)

A **single self-contained reveal.js file** (CDN reveal@5.1.0 + inlined `:root` tokens + per-
`<section>` scoped `<style>` blocks). Browser-openable directly (the CDN version; the Vite build
produces the offline single-file). **The "self-contained, one HTML file, browser-openable"
proof-of-concept is real and reassuring** — but the *shell* is reveal.js (slide nav), wrong for
an app.

**The screen blueprints that map 1:1 to user stories** (lift the *composition + styling +
vocabulary*, re-implement the interactive bits as real DOM):

| Slide id | Lines | Maps to | Reuse verdict |
|----------|-------|---------|---------------|
| `s8a-board-view` / `A-v2-a08` | 2944 / 3297 | US5 S1 shared board (human+agent assignees) | **BLUEPRINT** — strongest existing asset; board layout + assignee framing. |
| `A-v2-a09` | 3617 | US5 S2 ticket maker-checker activity log (M04/S03/R02, rework 1/3, PR link) | **BLUEPRINT** — the four-frame arc frame 2. |
| `A-v2-a10` | 4124 | US5 S3 / US10 decision artifact (id, reversibility, spike_ref, consequences) | **BLUEPRINT** — frame 3. |
| `A-v2-a11` | 4642 | US5 S4 L3 escalation rail (three pre-framed options) | **BLUEPRINT** — frame 4. |
| `A-v2-s10-stack-marketplace` | 5526 | US6 marketplace grid + credibility stats | **BLUEPRINT** — re-implement as DOM cards. |
| `A-v2-s10-stack-resume` | 5885 | US6 S3 full agent resume | **BLUEPRINT**. |
| `A-v3-chain` | 1826 | US9 S2 8-agent chain pipeline view | **BLUEPRINT**. |
| `A-v3-dash` | 2134 | US9 S3 portfolio dashboard | **BLUEPRINT**. |
| `s7-layer-2` | 1697 | US9 S1 12-contract catalogue | **BLUEPRINT**. |

**Critical caveat on liftability (verified):** these surfaces are **hand-drawn inline SVG
exhibits**, not interactive DOM. Element counts for `A-v2-a08` (board): `1 <svg>, 14 <rect>,
51 <text>, 6 <g>, 14 <div>` — i.e. one big SVG illustration of a board, plus a callouts column.
Same for marketplace/resume/chain/dash (`1 <svg>` + dozens of `<rect>`/`<text>`). **You cannot
click an SVG `<rect>` into a ticket.** So the deck gives you:
- the **visual language** (layout proportions — 62/38 hero+callout split; the callout chip
  styling; token-mapped SVG fill classes `.fill-bg/.fill-surface/.fill-accent/...`),
- the **exact content/vocabulary** to reproduce,
- a **pixel reference** to match,
but **not reusable interactive components**. Budget to **re-author these as real DOM** (divs,
grids, cards) — the SVG is a design comp, not a head start on code.

### 2c. `docs/plan/mockups/runs-threaded.html` — the real precedent (777 lines, REUSE as foundation)

The **only genuine app-chrome HTML in the repo**, and it already embodies the prototype's exact
build constraints:
- **No build step, no framework.** Plain `<!doctype html>` + inline `<style>` + CDN Google Fonts.
- **Vanilla interactivity:** rows expand via `onclick="this.classList.toggle('expanded')"`
  (lines 316, 341, 360, 379, 410, 575, 600, 648) and one small `<script>` (line 761) wiring
  `.copy-resume` buttons via `querySelectorAll(...).forEach`. This is **the entire interactivity
  toolkit the prototype needs** — class toggles + a few event listeners.
- **App-grade component CSS already written:** `.run-group`, `.run-node` (two-line row),
  `.row-1/.row-2`, status left-borders (`.has-failure`/`.has-warning`), `is-child`/`ctx-low`
  threading. This is **directly the US3 execution drill-in surface** (run list → dispatch tree).
- **Organizational pattern:** a single scrollable page stacking multiple mock states, divided by
  `.mockup-label` headers (lines 53–65) with an uppercase mono label + plain-language `.desc`.

**Verdict: this file is the seed of the prototype's CSS foundation and its US3 execution surface.
Start from its `:root` + component CSS, not from the deck.**

---

## 3. Gap Analysis (what the repo does NOT give you — all greenfield, all small)

| Gap | Severity | Notes |
|-----|----------|-------|
| **Canvas-morph transition** (FR-004; the one fluidity demo) | **Medium** | No precedent anywhere. Reveal.js *fragments* are the nearest thing and are the wrong abstraction. Greenfield, but cheap: Directional Idea already prescribes "CSS-transitioned panel swaps keyed to scripted chat steps". Modern path: CSS View Transitions API or FLIP/`transform`+`opacity` keyed to a JS step index. ~1 well-understood component. |
| **Scenario-chooser entry screen** (FR-002) | Low | No precedent; trivial greenfield (a grid of 5 cards routing via hash). |
| **Persistent chat rail + scripted chat** (FR-004/FR-005) | Medium | No precedent. Greenfield: a fixed-position panel + a canned-exchange array advanced by clicks; "promote artifact to canvas" = move a DOM node / set a flag. |
| **Demo-script overlay** (Directional Idea) | Low | No precedent; greenfield overlay (`position:fixed`, toggled by a key). |
| **Multi-screen app routing** | Low | Deck uses reveal hash-nav (wrong). Greenfield: `location.hash` → `show(screenId)` switch, or one-file-per-screen + plain links. Tiny. |
| **Interactive board/marketplace/etc.** | Medium | The deck's versions are static SVG; must be re-built as DOM (see §2b). This is the **largest single re-authoring cost** and should be planned as such — the deck saves design time, not build time, here. |
| **Per-family canvas shapes** (FR-006) | Medium | No precedent (that's step 3's design output); build cost lands here. |

**Honest call:** the prototype is **~80% greenfield app code**. The existing assets compress the
*design* effort (tokens, palette, screen compositions, vocabulary) substantially, but compress
the *build* effort only for the US3 execution surface (`runs-threaded.html`). Anyone estimating
"we'll just reuse the preso slides" is mis-reading static SVG exhibits as reusable UI.

---

## 4. Patterns & Conventions (what the repo proves about no-build static prototyping)

The repo demonstrates **three viable no-build patterns**; the prototype should pick the second.

1. **Single self-contained reveal.js file** (deck) — CDN libs + inline tokens + per-section
   scoped `<style id-prefixed>`. Pattern works, *substrate wrong* (slides ≠ app).
2. **Single/few vanilla HTML files, `classList.toggle` interactivity, CDN fonts**
   (`runs-threaded.html`) — **this is the prototype's pattern.** No framework, no build, opens
   on `file://`, scoped per-component CSS. Scales fine to ~15 screens if split into a few files
   or one-file-with-hash-routing.
3. **Vite + `vite-plugin-singlefile`** (toolkit base-template) — produces an offline single
   file but **is a build step**; **rejected by FR-001**. Keep only as an *optional* final
   "bundle to one file for emailing" convenience, never as the dev loop.

**Scoped-style convention (REUSE):** both the deck (`#sectionId .class { ... }`) and the mockup
(plain component classes) keep CSS local to a screen. For a multi-screen single-file prototype,
prefix per-screen styles by a screen id to avoid bleed — the deck's exact pattern.

**Vocabulary/brand conventions (REUSE — FR-018):** lowercase `cast-*` module names, "Diecast"
product name, "Layer" not "Tier", maker-checker as the quality unit, hyphens not em dashes, no
GPT-isms. The deck already complies; copy its tone.

**`plan_and_progress/` noise (IGNORE):** many dirs (`agents/*/plan_and_progress/`,
`skills/*/plan_and_progress/`, `docs/plan/mockups/plan_and_progress/`) contain
`sessions/*.jsonl` agent-telemetry logs. These are session exhaust, not assets — ignore entirely.

---

## 5. Entry Points & Flow (recommended prototype architecture, grounded in what exists)

```
                          ┌─────────────────────────────────────────────┐
  index.html  ──hash──▶   │  Scenario Chooser  (GREENFIELD, ~1 screen)   │
  (single file or         │  "Follow a feature / Chase a bug / Run a     │
   few files, no build)   │   spike / Answer a data question / Hire"     │
                          └───────────────┬─────────────────────────────┘
                                          │ location.hash → show(screenId)
                  ┌───────────────────────┼───────────────────────────┐
                  ▼                       ▼                           ▼
        ┌──────────────────┐   ┌──────────────────┐       ┌────────────────────┐
        │  CANVAS (main)   │   │  CHAT RAIL (fixed)│       │  DEMO-SCRIPT OVERLAY│
        │  per-family shape │◀─▶│ scripted steps[]  │       │  (fixed, key-toggle)│
        │  WHAT-first       │   │ advance on click  │       └────────────────────┘
        │  + execution tab  │   │ → morph(canvas)   │   ← FR-004 the one fluidity demo
        └─────────┬─────────┘   └──────────────────┘       (CSS View Transitions /
                  │                                          FLIP keyed to step index)
                  │ "execution" tab  (REUSE runs-threaded.html component)
                  ▼
        ┌──────────────────────────────────────────────────────────┐
        │ run list → dispatch tree → maker-checker (rework 1/3)     │  ← US3, lifted CSS
        │ board(a08) → ticket(a09) → decision(a10) → escalation(a11)│  ← US5, re-DOM'd blueprints
        └──────────────────────────────────────────────────────────┘

  data/fixtures.js  ── one fake-org spine (CAST-412, agents, chain, contracts) ──▶ every screen
```

**The morph flow (the only non-obvious mechanic), grounded:**
```
chat.advance()  →  steps[i].canvasState  →  document.startViewTransition(() => render(state))
                                            (fallback: toggle .morphing class; transition
                                             transform/opacity on swapped panels — the
                                             Directional-Idea "CSS-transitioned panel swaps")
```
No existing code does this; it is a ~50-line greenfield module. Reveal's fragment system is
explicitly NOT reused.

---

## 6. Tests & Coverage

Not applicable — the deliverable is a throwaway static prototype (Out of Scope: working
software). No test infrastructure is relevant or should be built. The only "verification" is the
walkthrough-based Success Criteria (SC-001..SC-007), done by eye. **Finding:** do not import the
`cast-preso-*` checker pipeline (content/visual/tone/compliance checkers) — it validates *slide
decks* against deck rules, not app prototypes; it would actively mislead here.

---

## 7. Config & Dependencies (the cheap-and-credible stack)

**Recommended dependency surface — deliberately near-zero, all CDN, no install:**

| Need | Choice | Cost | Source-of-precedent |
|------|--------|------|---------------------|
| Fonts | Google Fonts CDN: `IBM Plex Mono` + `DM Sans` (+ `Caveat` only if a hand-annotation moment is wanted) | 0, CDN | both deck + mockup use exactly this |
| Styling | Hand-written CSS, `:root` tokens, scoped per-screen | 0 | mockup + deck |
| Interactivity | Vanilla JS: `classList.toggle`, `addEventListener`, `location.hash` | 0 | mockup proves sufficiency |
| Transitions | CSS View Transitions API (Chrome/Edge native 2026) + FLIP fallback | 0 | greenfield |
| Charts/data-viz (US4 data-analysis family) | inline SVG or a single CDN micro-lib only if needed | ~0 | deck draws charts as inline SVG by hand |
| Icons | inline SVG | 0 | deck pattern |
| Bundling | **none** (FR-001). Optional: a one-shot `vite-plugin-singlefile` pass ONLY if a single emailable file is later wanted — never in the dev loop | 0 in dev | toolkit base-template (as escape hatch, not workflow) |

**Hard constraint check:** the only thing in the existing assets that *introduces a build step*
is the `cast-preso-visual-toolkit/base-template` Vite config + the assembler's
`npx vite build`. Both are **excluded** to honor FR-001. Everything else the prototype needs is
CDN-or-vanilla. **A reviewer should reject any plan that reintroduces npm/Vite into the dev
loop.**

**Browser target:** desktop-first (Out of Scope: mobile). Author at a fixed desktop width;
unlike the deck (authored 1920×1080 for reveal's auto-scale), an app prototype should use normal
responsive-ish desktop CSS, not reveal's scale transform.

---

## Key Takeaways

1. **Single biggest reuse decision: split the two pools by purpose.** Take **design** from the
   preso deck (tokens, palette, screen compositions, vocabulary, fake-data spine) and take
   **build pattern** from `runs-threaded.html` (vanilla, no-build, `classList.toggle`). Mixing
   them up — trying to build the app *in* reveal.js, or trying to *embed* the SVG exhibits as
   live UI — is the trap. Drop reveal.js, drop Vite, drop the slide-archetype catalog.

2. **The preso "reusable surfaces" are static SVG illustrations, not components.** Verified:
   board/marketplace/resume/chain/dash are each one hand-drawn `<svg>`. They compress *design*
   time, not *build* time. Re-authoring them as interactive DOM (clickable board→ticket→
   decision→escalation, US5; marketplace cards, US6) is the **single largest build cost** and
   must be planned as such — not hand-waved as "reuse the slides."

3. **What's surprisingly good and should be preserved: `runs-threaded.html`.** It's the lone
   real app-chrome artifact and it already nails the exact constraints (no build, vanilla,
   CDN fonts, expanded app-token palette, expand/collapse threading). It seeds both the CSS
   foundation and the US3 execution drill-in surface directly. Start there.

4. **What would break the constraint if reused naively: the toolkit's Vite build + the
   assembler's `npx vite build`.** FR-001 says "no build step required." The CDN/vanilla path is
   already demonstrated in-repo, so the build pipeline is pure downside — exclude it from the dev
   loop (keep only as an optional final single-file-bundle convenience).

5. **Most impactful cheap win: the fake-data spine + token superset, extracted once.** A single
   `data/fixtures.js` (CAST-412, M04/S03/R02, rework 1/3, the 8-agent chain, 12 contracts, 6
   archetypes, credibility stats) plus the merged `:root` (mockup palette + deck identity) makes
   every screen feel like one coherent product — satisfying SC-004 (showable without apology) and
   FR-018 (brand continuity) for near-zero effort.

6. **The morph/chat/scenario/overlay mechanics are all greenfield but all small.** None exist in
   the repo; none are hard. CSS View Transitions (or FLIP) keyed to a scripted-step index covers
   the one fluidity demo (FR-004); a hash router + canned chat array + fixed overlay cover the
   rest. Total greenfield interactivity is on the order of a few hundred lines of vanilla JS.

7. **Do not import the cast-preso-* generation/checker pipeline.** Narrative→what→how→assembler→
   checkers is machinery for producing *slide decks* and would mis-validate an app prototype.
   This is a hand-built artifact; build it by hand from the design references.

## Key Files

- `docs/plan/mockups/runs-threaded.html` — **the build-pattern seed**: vanilla no-build app
  chrome, `classList.toggle` interactivity, expanded app-token `:root`, US3 execution component.
- `skills/claude-code/cast-preso-visual-toolkit/visual_toolkit.human.md` — authoritative design
  tokens (§1), typography (§2), grid background (§3), token-override pattern (§10). Reuse design,
  ignore slide archetypes (§9) and illustration guide (§8).
- `.../cast-preso-visual-toolkit/templates/css/{grid-background,typography,components}.css` —
  liftable CSS snippets (grid bg + type scale; callout chip optional).
- `.../cast-preso-visual-toolkit/base-template/{vite.config.js,package.json}` — **the build step
  to AVOID**; read only to confirm what not to reuse. `index.html` lines 8–11 show the no-build
  CDN escape hatch.
- `presentation_v3/presentation/index.html` — the assembled deck; **design reference** for the
  nine blueprint surfaces (see §2b table for the line numbers per slide). Self-contained-file
  proof, reveal.js shell (don't reuse the shell).
- `presentation_v3/how/<slide-id>/slide.html` — per-slide sources (board `s8a-board-view`,
  `A-v2-a08..a11`; marketplace/resume `A-v2-s10-stack`; `A-v3-chain`, `A-v3-dash`,
  `s7-layer-2`) — design comps to re-implement as DOM.
- `agents/cast-preso-assembler/cast-preso-assembler.md` — documents the Vite single-file build
  pipeline; read to understand why it's excluded (build step) for this prototype.
- `goals/product-revamp-diecast/refined_requirements.collab.md` — FR-001 (no build), FR-002
  (entry), FR-004 (morph), FR-018 (brand), FR-019 (polish bar), Directional Ideas (scenario
  chooser, scripted chat, CSS-panel-swap morph, fake-data spine).
- `goals/product-revamp-diecast/exploration/steps.ai.md` — Step 6 success criteria (build recipe
  + strictly-optional reuse list).
</content>
</invoke>
