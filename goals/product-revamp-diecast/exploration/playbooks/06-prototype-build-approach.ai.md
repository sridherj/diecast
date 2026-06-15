# Prototype Build Approach — Playbook

> **Step 6 of** `exploration/steps.ai.md` — *the cheapest credible way to build a vision-grade
> clickable HTML prototype.* The 10x lens: the wrong build approach turns a mockup into a project.
> **Synthesized from:** `research/06-prototype-build-approach.ai.md` (web, 7-angle GO-BROAD) +
> `research/06-prototype-build-approach-code.ai.md` (in-repo terrain map).
> **Serves:** FR-001 (self-contained, no backend, no build), FR-002 (scenario entry), FR-004 +
> SC-003 (chat morphs the canvas), FR-006/FR-007 (four distinct family canvases + visible
> iteration), FR-018/FR-019 (brand + polish bar), FR-020 (greenfield, not bound to cast-server),
> SC-004 (showable without apology), SC-006 (surfaces map to buildable goals).
> **Author:** cast-playbook-synthesizer | **Date:** 2026-06-11 | **Framing:** VISION-FIRST.

---

## TL;DR

Build **one `index.html`, no build step, with every screen rendered as a pure function of one
JSON object** — `render(appState) → DOM`. Wire it with native **import maps + htm/Preact** (≈3KB,
JSX ergonomics, zero compiler), route on the **URL hash**, fake all interactivity with a
**scenario script** (an ordered list of `{state-patch, narration}` steps a "Next" button walks),
and implement the marquee canvas-morph (FR-004) with the native **CSS View Transitions API** in
two lines. The single insight that makes days-not-weeks possible: **the spec's ~35 surfaces are
projections of one fake org, not 35 hand-built pages** — author the data once and the screens fall
out. Lift the **design tokens + fake-data vocabulary** from the preso deck and the **vanilla
app-chrome + execution-drill-in CSS** from `docs/plan/mockups/runs-threaded.html`; drop reveal.js,
Vite, and the cast-preso agent/checker pipeline entirely. Time-to-vision-grade: **~5–7 focused days.**

## Recommended Stack

| Component | Choice | Why (and why not the alternative) |
|-----------|--------|-----------------------------------|
| Build step | **None — native import maps** | `<script type="importmap">` resolves bare specifiers to CDN URLs; no node_modules, no bundler. FR-001 says "no build step required" — this makes it literally true, not aspirational. Vite/Webpack/Next is day-2 tax for a file someone double-clicks. |
| Render layer | **htm + Preact (CDN)** | ~3KB, JSX-like via tagged template literals, no compiler. Reconciliation keeps the morph + drill-in + promote interactions flicker-free across 35 surfaces. *Not* raw `innerHTML` re-render (loses focus/scroll/event-wiring on every patch); *not* React (200KB + toolchain you don't need). |
| State | **One JSON object in memory** | Single source of truth → cross-screen coherence (the spec's named constraint: same CAST-412/agents recur everywhere). Not Redux/Zustand — a plain object + `render()` is the part of a state library you actually use. |
| Routing | **`location.hash` + 20-line switch** | Deep-linkable screens (`#/feature/CAST-412/execution`), working back button, scenario chooser = a list of links. Not a router library — the platform already routes. |
| Canvas morph | **CSS View Transitions API (native)** | `document.startViewTransition(() => render(next))` = FR-004 in two lines; same-document transitions hit Baseline Oct 2025. `view-transition-name` on the chat rail + goal title makes shared chrome *persist and slide*. Not bespoke keyframes (multi-day yak-shave per flow). |
| Fake data | **`@faker-js/faker`, seeded, build-time only** | `faker.seed(42)` → deterministic org; run once, hand-tune, **commit the JSON**. Faker never ships — runtime imports a frozen file, keeping FR-001 clean. LLM-generate the *prose* (ticket text, hiring-report pros/cons, decision rationale); faker for the structured spine (names, IDs, SHAs, dates). |
| Demo overlay | **`driver.js` (MIT, ~5KB)** | Highlights an element, dims the rest, next/prev popover = the guided walkthrough for SC-002. MIT, not `shepherd.js`/`intro.js` (AGPL/paid) — no copyleft string on a showable artifact. |
| Design tokens | **Lift the merged `:root` superset** | `runs-threaded.html` app-grade tokens (status colors, borders, radii) as the **base**, deck identity values (cream/navy/raspberry, IBM Plex Mono / DM Sans) layered on. Instant craft floor + FR-018 continuity. |
| Execution drill-in CSS | **Lift `runs-threaded.html` components** | `.run-group`/`.run-node`/status left-borders/`classList.toggle` expand — the *only* real app-chrome in the repo, and it already IS the US3 run→dispatch-tree surface. Start the CSS here, not from the deck. |
| Single-file packaging | **Hand-inline (optional one-shot `vite-plugin-singlefile`)** | The app is small enough to inline by hand at the end. Keep the Vite single-file trick only as an optional "bundle to one emailable file" convenience — **never in the dev loop.** |

**Total runtime weight: <15KB of library code, all CDN-or-inlined. Zero `npm install` to run.**

## Implementation Steps

> Ordered by dependency. Polish comes from *amortization* (build the spine + kit once, every
> screen inherits it), not per-screen effort — that ratio is what turns weeks into days.

### Step 1: Spine + skeleton — `index.html`, tokens, router stub
**Impact: High** | **Effort: ~0.5 day**

Stand up one `index.html` with the import map and the merged design tokens, plus the
`render(state)` + hash-router switch that everything else hangs off. This is the load-bearing
half-day: get it right and screens become 10-line data slices.

```html
<!doctype html><html><head>
<script type="importmap">{ "imports": {
  "preact": "https://esm.sh/preact@10",
  "preact/hooks": "https://esm.sh/preact@10/hooks",
  "htm/preact": "https://esm.sh/htm@3/preact"
}}</script>
<style>:root{
  /* base: runs-threaded.html app palette */
  --color-bg:#F5F4F0; --color-surface:#FFFFFF; --color-text:#1A1A28; --color-muted:#4A4860;
  --color-border:#DDD8CD; --color-success:#2D7D4F; --color-warning:#B5821A;
  --color-danger:#B22439; --color-info:#3B5BB0; --color-focus:#6B47B0;
  --radius-sm:4px; --radius-md:8px; --radius-lg:14px;
  /* deck identity layered on top */
  --color-accent:#D6235C; --font-heading:'IBM Plex Mono',monospace; --font-body:'DM Sans',sans-serif;
}</style></head>
<body><div id="app"></div>
<script type="module">
import { html, render } from 'htm/preact';
import { state } from './state.js';
const routes = { '': Chooser, '#/board': Board, '#/feature': FeatureCanvas, /* … */ };
function App(){ const View = routes[location.hash.split('/').slice(0,2).join('/')] ?? Chooser;
  return html`<${View} state=${state} />`; }
function paint(){ render(html`<${App}/>`, document.getElementById('app')); }
addEventListener('hashchange', paint); paint();
</script></body></html>
```

### Step 2: The fake-org data spine — `data/org.json`
**Impact: High** | **Effort: ~0.5 day**

Author one coherent fictional org *once*; every screen reads from it. This is the cheapest
highest-leverage reuse in the whole build — reuse the canonical vocabulary verbatim so screens
feel like one product (FR-018) and satisfy the coherence constraint.

Lift these fixed values (from preso v3 + the spec) — do **not** hand-name ad hoc:

| Token | Value |
|-------|-------|
| Ticket | `CAST-412` |
| Checker rule codes | `M04` / `S03` / `R02` |
| Rework budget | `1/3 used` |
| Reversibility levels | `L1 / L2 / L3` |
| Canonical agent | `crud-orchestrator` |
| 8-agent chain | refine → decompose → research → synthesize → plan → detail → orchestrate → run |
| 12 named contracts | (the Layer-2 catalogue list) |
| Archetypes | Maker / Checker / Decision / Spike / Escalation / Mentor |
| Marketplace cred stat | "99.9% compliant code in 2 maker-checker loops across 505 runs" |

Run `faker.seed(42)` for the structured filler (8 agents, 6 goals across the four families, PR
links, SHAs, timestamps), LLM-write the prose, then **commit the resulting JSON**. No generation
at runtime.

### Step 3: The component kit (~8 reusable pieces)
**Impact: High** | **Effort: ~1.5 days**

Build once, reuse on every screen — this is what collapses 35 screens into 8 components × 1 spine
× 4 scripts. The four *family canvases* are **data-driven configs of one `CanvasFrame`, keyed on
`family`**, not four separate screens (that's also what makes the morph a state change, not a
navigation).

```
AppShell        nav rail + chat rail + canvas slot (the persistent chrome)
ChatRail        scripted message list + scripted-send control
CanvasFrame     the View-Transition container; renders per-family stage shape
WhatPanel       outcome / status / evidence / nudged-next-step (the WHAT-first top level)
ExecutionDrillIn  tabs → run list → dispatch tree → maker-checker  (LIFT runs-threaded.html CSS)
Board / Ticket  assignee-filtered board + ticket activity log
AgentCard / Resume  marketplace card (maker-checker paired in-card) + full resume
EvidenceBlock   variants: screenshot | chart | rendered-HTML | test-summary  (FR-009)
```

### Step 4: Backbone flow — feature family, end to end
**Impact: High** | **Effort: ~1 day**

Wire the **new-feature flow** first as the richest backbone (US2 flow 1): WHAT-first canvas
(US3) → execution drill-in → one `EvidenceBlock` (US4). Proving the full vertical slice on the
richest flow de-risks everything; the other three families are then config + script over the same
kit.

### Step 5: The scenario engine + the aha morph (build this early — it's the riskiest piece)
**Impact: High** | **Effort: ~1 day**

The scenario engine is the no-backend interactivity engine: each flow is an ordered array of
steps, a single "Next"/scripted-send control walks it, and **every dynamic moment in the spec is
faked through this one mechanism.** Author the feature→debug morph (SC-003, the one thing that
*must* be demonstrated) as the headline step.

```js
scenarios.feature = [
  { narration: "Opening the goal…",  patch: s => { s.route = '#/feature/CAST-412'; } },
  { narration: "Actually this is a bug, not a feature.",            // ← the SC-003 moment
    patch: s => { s.family = 'debug'; s.canvas = debugShape; },
    transition: 'morph' },                                          // → document.startViewTransition
  { narration: "Iteration 2/3 — new hypothesis…",
    patch: s => { s.debug.iteration = 2; } },
];
// advance():
function advance(){ const step = script[++i];
  step.patch(state);
  if (step.transition === 'morph' && document.startViewTransition)
    document.startViewTransition(() => paint());
  else paint();
}
```

Put `view-transition-name: chat-rail` / `goal-title` on persistent chrome so it slides rather than
cross-fades — the "engineered, not janky" finish. Degrades to an instant swap where View
Transitions are unsupported (Chrome primary).

### Step 6: The other three family canvases + their scripts
**Impact: High** | **Effort: ~1 day**

Add **debug / spike / data** as `CanvasFrame` configs + scenario scripts. Debug =
hypothesis→experiment→observation with an iteration counter (FR-007); spike = timebox→conclusion
artifact referenced by a decision via `spike_ref` (FR-016); data = question→sources→analysis→viz
(`EvidenceBlock` chart variant). Make the feature-vs-debug shape contrast obvious at a glance
(SC-005).

### Step 7: Agent-colleague + decision surfaces (re-DOM the preso blueprints)
**Impact: High** | **Effort: ~1.5 days**

Build the board→ticket→decision→escalation arc (US5), hiring flow (US6), agent-ops/skillification
(US8), Layer-2 catalogue/chain/portfolio (US9), and the requirements-doc loop (US7) — all
data-driven views over the existing spine. **Mine the preso a08–a11 / marketplace / resume / chain
/ dash slides for layout and vocabulary, then re-implement as real DOM.** Critical: those slides
are hand-drawn inline `<svg>` exhibits, not components — they compress *design* time, not *build*
time. This re-authoring is the single largest build cost; plan it as such. Thread decision records
+ the autonomy-gated L3 clarification (US10/SC-007, reusing the escalation-rail mechanism) through
the flows.

### Step 8: Polish, overlay, package
**Impact: Medium** | **Effort: ~1 day + buffer**

Add the `driver.js` demo-script overlay per flow (SC-002) and the scenario-chooser entry screen
(FR-002). Run a content-density pass (LLM-generate believable ticket prose, hiring-report
pros/cons, decision rationale) so it reads as a product, not a skeleton (SC-004). Inline to one
self-contained `.html`; Chrome smoke test.

## Architecture / Layout

```
  index.html  (single file, no build) ── importmap ▶ preact/htm/driver.js from CDN
      │
      │ location.hash → render(appState)
      ▼
 ┌──────────────────────────────────────────────────────────────────────────┐
 │  AppShell                                                                  │
 │  ┌────────────┐  ┌──────────────────────────────┐  ┌────────────────────┐ │
 │  │  Nav rail  │  │  CanvasFrame (WHAT-first)     │  │  ChatRail (fixed)   │ │
 │  │            │  │  per-family stage shape       │◀▶│  scripted steps[]   │ │
 │  │ feature    │  │  ┌─────────────────────────┐  │  │  advance() on click │ │
 │  │ debug      │  │  │ WhatPanel: outcome /    │  │  │   → state.patch     │ │
 │  │ spike      │  │  │ status / evidence /     │  │  │   → startViewTrans. │ │
 │  │ data       │  │  │ nudged next step        │  │  └────────────────────┘ │
 │  │ ─────────  │  │  └─────────────────────────┘  │   FR-004 morph lives    │
 │  │ board      │  │  [ execution tab ▼ ]          │   HERE (family swap =   │
 │  │ market     │  │   ExecutionDrillIn            │   state change)         │
 │  │ layer-2    │  │   run list → dispatch tree →  │                         │
 │  └────────────┘  │   maker-checker (rework 1/3)  │   driver.js overlay     │
 │                  └──────────────────────────────┘   (fixed, key-toggle)   │
 └──────────────────────────────────────────────────────────────────────────┘
      ▲
      │  every component reads from ▼
 data/org.json  ── ONE fake-org spine (CAST-412, 8 agents, 8-chain, 12 contracts, decisions)

 MORPH:  chat.advance() → steps[i].patch(state) → document.startViewTransition(() => render(state))
         shared chrome (chat-rail, goal-title) carries view-transition-name → slides, not cross-fades
```

## Key Decisions

| Decision | Recommendation | Rationale / trade-off |
|----------|---------------|-----------------------|
| Build vs no-build | **No build step (import maps)** | FR-001 mandates it; the browser ships the toolchain in 2026. Trade-off: lose HMR/TS — irrelevant for a static prototype. |
| Render: vanilla vs Preact | **htm/Preact** | Both research notes hedge "start vanilla, adopt Preact if flicker." Decided pick: **Preact from the start.** The interaction surface (morph, drill-in tabs, promote-to-canvas, scenario patches, autonomy modal) is genuinely stateful across 35 screens; reconciliation prevents the focus/scroll/flicker tax that `innerHTML` re-render incurs, and it pairs cleanly with the `render(state)` spine. Cost is ~3KB. **Fallback if Preact ever feels heavy: vanilla template-literal `render()` — `runs-threaded.html` proves it's sufficient.** This is the one reversible fork; revisit only if Preact causes friction by Day 2. |
| One file vs many files | **Single document, hash routing** | Same-document View Transitions are fully Baseline; cross-document ones don't animate in Firefox and carry a 4s timeout. One file sidesteps both and keeps state global. |
| Interactivity | **Scripted state-patches, not real logic** | A vision prototype is a rail, not an app. One scenario engine fakes morph + iteration + autonomy-gate uniformly. Trade-off: no real edge cases — viewers can't tell, and you buy back days. |
| Family canvases | **Configs of one `CanvasFrame`, keyed on `family`** | Makes "switch family" a state change (= the morph) instead of four pages, and guarantees the visible contrast (SC-005) is data, not duplicated chrome. |
| Fake data | **Seeded faker (structure) + LLM (prose), frozen to JSON** | Deterministic + coherent + zero runtime dependency. The believable density is what separates SC-004 "showable" from "obviously a mock." |
| Design tokens base | **`runs-threaded.html` superset, not the deck `:root`** | The mockup already extended the palette toward real app UI (status/border/radius); the deck lacks those. Adopt the mockup base, keep deck identity values. |
| Preso slide reuse | **Mine for layout + vocabulary; re-implement as DOM** | The board/marketplace/resume/chain slides are hand-drawn `<svg>` exhibits — design comps, not components. They save design time, not build time. Importing the SVG wholesale is the trap. |
| AI tooling role | **Content/component gun, never the architect** | v0/Lovable/Bolt ship a React/Next/Supabase repo (forbidden by FR-001/FR-020) and are weakest at the cross-screen coherence the spec demands. Use them to generate dense leaf cards/prose to paste in; keep the spine + renderer human-owned. |
| reveal.js / Vite / cast-preso pipeline | **Drop all three** | reveal.js is a linear slide engine (wrong substrate); Vite reintroduces a build step (violates FR-001); the cast-preso checkers validate *slide decks*, not app prototypes, and would actively mislead. |

## Pitfalls to Avoid

1. **Building screens instead of data + one renderer.** The cardinal sin. If `bug-screen.html` and
   `feature-screen.html` exist as separate files with copy-pasted chrome, you've already lost the
   budget — the crossover where data-driven beats hand-authoring is ~screen 6, and there are 35.
   Refactor any shared chrome into a component the moment it appears twice.
2. **Standing up a framework toolchain.** `npm create vite`, a router lib, a state lib, Tailwind's
   JIT — each is a 30-minute setup and a lifetime of "why won't the build work" for an artifact
   that ships as one double-clickable file. Use the platform.
3. **Letting an AI app-builder own the architecture.** It inherits a backend/stack the spec
   forbids and drifts the fake org between screens (the exact coherence constraint it's weakest
   at). Buys polish on screen 1, bankrupts you by screen 15.
4. **Making interactions *real*** — real filters, real validation, real empty states. Every hour
   making the assignee filter actually filter is an hour not spent on the next vision surface. Fake
   the happy path; the viewer can't tell.
5. **Embedding the preso SVG exhibits as live UI.** They're static illustrations; you can't click
   an `<svg><rect>` into a ticket. Read them as pixel references, re-author as DOM. Anyone
   estimating "we'll just reuse the slides" is mis-reading comps as components.
6. **Many HTML files + cross-document View Transitions.** Firefox won't animate them and the 4s
   timeout bites. The single-document SPA gets fully-Baseline same-document transitions for free.
7. **Hand-naming fake data ad hoc.** Drifts instantly across 35 screens. Seed it, commit it,
   reference it from one spine.
8. **Hardcoding hex colors.** Use the `--color-*` tokens so Step 1's chosen design direction can
   re-skin the whole prototype by overriding `:root`. (Also a cast-preso hard rule, FR-018.)
9. **Reintroducing Vite/npm into the dev loop "just to bundle."** A reviewer should reject any plan
   that does. Keep `vite-plugin-singlefile` as an optional final one-shot only.
10. **Over-building the scenario engine into a state machine.** It's an array walker, not XState.
    `{patch, narration, transition}` + `advance()` is the whole thing — ~50 lines.

## Success Metrics

- **Per-screen authoring cost ≤ a 10-line data slice + a 10-line scenario step**, once the spine +
  kit exist (measured: time to add screen N for N>10). If a new screen needs new chrome, the kit
  is incomplete — fix the kit, not the screen.
- **Runtime library weight < 15KB**, zero `npm install` required to open the file (measured: view
  source; the only deps are CDN `<script>`s + frozen JSON).
- **The morph is real, not faked frame-to-frame**: one chat step visibly reshapes the canvas
  feature→debug via `startViewTransition`, shared chrome persisting (SC-003 — binary: present/absent).
- **Feature-vs-debug canvas contrast obvious in a side-by-side screenshot** (SC-005 — pass when a
  cold viewer names them as different workflow shapes).
- **All four flows clickable start-to-finish with no broken state** (SC-001 — count: 4/4 walk
  cleanly via the scenario chooser).
- **≥1 in-context decision record per flow + ≥1 autonomy-gated clarification moment** in the build
  (SC-007 — count across the four flows).
- **Time-to-vision-grade ≤ 7 focused days** (the budget; tracked against the Step 1–8 plan).

## Impact Rating: 9/10

**Justification:** This step is the 10x lens for the entire goal — it decides whether the ~35
surfaces the spec demands cost days or weeks, and the data-driven-render + scenario-engine + native
View Transitions recipe is the *unique* architecture where the vision-grade bar (SC-004) and the
days-not-weeks budget are simultaneously reachable. Every other surface playbook (US1–US10) is
*executed through* this one: get the spine + kit + morph right and the rest is data authoring; get
it wrong (per-screen HTML, a framework toolchain, an AI-builder repo) and the mockup becomes a
project that never ships. Held back from 10 only because two inputs are still open — the Step 1
design language (re-skins `:root`, doesn't change the architecture) and the Step 3 per-family
evidence treatments (fills `EvidenceBlock` variants) — both of which slot cleanly into this recipe
without altering it.
