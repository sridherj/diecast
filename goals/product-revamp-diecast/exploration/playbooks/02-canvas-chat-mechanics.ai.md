# Step 2: Canvas + Chat Steering Mechanics — Playbook (morph · nudge · promote · drill-in)

> Synthesis of Research Note 02 (web — the 2026 generative-UI field) + Code Exploration 02
> (terrain map of today's cast-server UI + the FR-017 substrate) into an opinionated, build-ready
> interaction spec for the **static HTML clickable prototype** (no backend, scripted chat).
> This is the **core-thesis step**: it specifies the one interaction model the prototype exists
> to *demonstrate, not describe* (SC-003). Later steps (3 family canvases, 4 colleagues, 5
> decisions, 6 build recipe) inherit the binding grammar and motion register pinned here.
> **Agent:** cast-playbook-synthesizer · **Date:** 2026-06-11 · **Status:** ai
> **Framing:** VISION-FIRST. The codebase is terrain, never an anchor — and the terrain map is
> blunt: the two surfaces this step is about (adaptive canvas, chat rail) **do not exist today**.
> That is liberating, not a problem. Design them fresh from the verdicts below.

---

## TL;DR

**Stop thinking "chat that generates UI." Build "chat that emits typed commands against a UI
*you* own."** The entire 2025–2026 field has converged on one shape and it is exactly the shape
the spec already locked: a persistent, intentionally-designed **canvas is the source of truth**;
**chat is an ephemeral command rail** that mutates it; the agent **never paints pixels** — it
resolves each turn to one of a *small, named set of canvas operations*. Vercel paused its
free-form RSC generative-UI track, Shopify's MCP-UI thesis is literally "agents shouldn't
generate UIs themselves," Google's A2UI renders only from a trusted catalog, and Litt/Wattenberger
argue direct-manipulation-primary with the LLM as a *secondary* loop. The spec's instincts match
the discipline; this playbook turns them into a build.

**The keystone** (the single thing that makes all four mechanics cohere and the prototype cheap):
the canvas is driven by **typed events, not generated markup**. Every scripted chat line carries a
`data-op` (`morph:debug`, `nudge:run-exploration`, `promote:hiring-report`, `drill:run-CAST-412`,
`pin:spike-conclusion`). A ~30-line vanilla-JS dispatcher reads the op and calls the matching
canvas function *inside* `document.startViewTransition(...)`. **No model, no backend, no
framework** — yet the interaction grammar is byte-for-byte the real product's tool-call binding.
The prototype becomes an *honest preview*, not a Potemkin facade.

**The one demo that proves the thesis** is US1's hero morph: type *"this is actually a bug, not a
feature"* → the canvas shared-element-morphs from feature stages to the debug loop without losing
goal context, drops a promotable decision receipt, and keeps an execution drill-in. Get this *one*
transition flawless and the prototype earns SC-003. **Recommendation: build one hero morph
perfectly, not four mediocre ones.**

**The one reusable asset from today's code:** `macros/run_node.html` — the recursive dispatch-tree
renderer (rework tags, context-usage bars, skill chips, rolled-up failure state). It *is* US3's
execution drill-in already built in HTML/CSS. Lift its visual logic; design everything else fresh.

---

## Recommended Stack

One pick per concern. Because the deliverable is a *static prototype* (FR-001), "stack" means the
actual build tech — not a production architecture (FR-020 says the prototype's HTML choices imply
nothing about the real product). Each pick names the exact primitive plus its production-idiom
equivalent, so the prototype is an honest preview of the real binding.

| Concern | Pick (prototype) | Production-idiom equivalent | Why this, not the alternative |
|---------|------------------|-----------------------------|-------------------------------|
| **Canvas↔chat binding** | **`data-op` attributes → a ~30-line vanilla-JS dispatcher** calling named canvas fns | AG-UI `TOOL_CALL_*` events / CopilotKit `useCopilotAction` / A2UI JSON | Industry is *retreating* from free-form generative UI toward constrained vocabularies. A named op-set is both the safe production choice and the cheapest honest fake. |
| **Op vocabulary** | **5 named ops: `morph` · `nudge` · `promote` · `drillInto` · `pin`** | Schema-validated tool calls | Small closed set = no mode confusion, trivially scriptable, identical grammar to the real product. |
| **Morph transition** | **CSS View Transitions API** (`document.startViewTransition`) + `view-transition-name` on ~4 anchors | Same API in prod; FLIP / Framer Motion `layoutId` if React | *Baseline newly-available* (Oct 2025); ~20 lines, zero deps; the canonical "one thing becomes another" primitive. |
| **Morph fallback** | **Opacity/transform crossfade** (Web Animations API) under `prefers-reduced-motion` / no-support | Same | WCAG 2.3.3; ~35% of adults 40+ have vestibular sensitivity. Non-negotiable. |
| **Framework** | **None — vanilla ES modules + one hand-rolled CSS file** | (irrelevant to prod) | Echoes the team's proven zero-build fluency; a framework is pure overhead for a scripted static demo. FR-020 frees the *design* but not the *build cost*. |
| **State** | **One JSON `scenario` object** (state-as-data) + optional `localStorage` for expand state | `STATE_SNAPSHOT`/`STATE_DELTA` | Deterministic, inspectable, replayable; matches AG-UI's state-event model conceptually. |
| **Nudge** | **One-primary "next-step card" component** (filled primary + receding secondaries + always-visible chat/nav override) | Same choice-architecture pattern | "Exactly one recommended action per screen" (Apple HIG/Material); never a gate (Rails sharp knives). |
| **Promote** | **Explicit "Pin to canvas" button** that clones a chat artifact card into a canvas slot with a `from chat · <agent> · <time>` provenance stub + version label | Tool-call → durable component + "pin" | Explicit beats auto-promote (NotebookLM "Save to note" wins over ChatGPT auto-open); a staging gate prevents canvas clutter. |
| **Drill-in** | **WHAT panel above the fold + "Execution" tab**; lift `run_node.html` visual logic; ≤2 disclosure levels; escalations promoted *up* to WHAT | Progressive disclosure / master-detail | NN/g: >2 levels and users get lost; burying escalations in HOW is the worst FR-008 failure. |
| **Three tiers (FR-017)** | **Static two-pane side-by-side mock** (faux terminal `cast crud-orchestrator` ‖ canvas with defaults; same artifact card in both) | Real: one `.md` substrate, `bin/generate-skills` + tmux dispatch | The substrate parity is *literally true* in code — the mock depicts a real mechanism, not a claim. |

---

## Implementation Steps

The build order for the interaction layer. Sequenced so the highest-ROI, thesis-proving item ships
first and de-risks SC-003 immediately; everything after is additive and independently demoable.

### Step 1 — Build the op-dispatcher + scenario spine *first* (the keystone)
**Impact: High** | **Effort: Low (~½ day)**

Before any visible mechanic, build the binding substrate every mechanic rides on. A single JSON
`scenario` object holds canvas states; each canned chat line is `<button data-op="morph:debug">`.
A ~30-line dispatcher parses `op:arg`, looks up the canvas function, and runs it inside
`startViewTransition`. This is the prototype's spine — get it right once and morph/nudge/promote/
drill all become thin functions hanging off it.

```js
const OPS = { morph, nudge, promote, drillInto, pin };          // named, closed set
function dispatch(opStr) {                                       // e.g. "morph:debug"
  const [op, arg] = opStr.split(':');
  if (!document.startViewTransition) return OPS[op](arg);        // reduced-motion / fallback path
  document.startViewTransition(() => OPS[op](arg));              // shared-element morph
}
document.querySelectorAll('[data-op]').forEach(el =>
  el.addEventListener('click', () => dispatch(el.dataset.op)));
```

**Why first:** it is the production grammar (typed ops, not pixels) *and* the cheapest fake. Skip
it and you hand-wire four bespoke animations that can't compose.

### Step 2 — Ship the hero morph: feature → debug (this *is* SC-003)
**Impact: High** | **Effort: Medium (~1 day)**

Keep both canvas layouts in the DOM. Tag the **4 conceptually-persistent anchors** — goal header,
decision trail, evidence strip, the chat rail — with `view-transition-name`; they glide/resize.
The family-specific stages crossfade (feature `req→explore→plan→execute` out; debug
`hypothesis→experiment→observation + iteration counter` in). Duration **~350ms** (Dynamic Island
sweet spot). Fire a **decision receipt** toast ("Reclassified feature→bug — debug loop") that is
itself promotable, and make the morph **undoable**.

This single transition exercises all four mechanics in sequence (nudge on open → morph on steer →
promotable receipt → drill-in preserved) and is the one thing the prototype must *show*. **Do this
one flawlessly; do not spread effort across morphing all four families** (diminishing demo return —
the research and the owner both flag this as the judgment call, and the answer is one hero morph).

### Step 3 — Nudge component: one dominant next step, never a gate
**Impact: High** | **Effort: Low (~½ day)**

A reusable "next-step card" rendered per canvas state: one filled/high-contrast primary that says
*what and why now* ("Run exploration → 3 open questions block planning"), secondaries tinted/
outline, and the chat rail + manual nav always present as cheap overrides. Reuse today's latent
`task_suggestion_card` framing as the seed. The nudge is a *suggestion* — doing nothing or picking
a sibling costs nothing; a power user bypasses via chat/terminal. This is the operational meaning
of "opinionated, meaningful defaults" (FR-003).

### Step 4 — Promote gesture: chat artifact → pinned canvas object
**Impact: Medium-High** | **Effort: Low (~½ day)**

Chat artifacts (hiring report, spike conclusion, chart) appear as **rail cards** with an explicit
**"Pin to canvas"** button. Clicking clones the card into a canvas slot carrying a version label +
`from chat · <agent> · <time>` provenance stub; the chat keeps a lightweight "Pinned ✓" back-stub.
Explicit, not automatic; reversible, non-destructive. This makes FR-005 / US1 Scenario 3 clickable
and kills the "lost-in-scrollback" anti-pattern. Note the genuine differentiator: Claude Artifacts
has **no "pin to Project"** — so "pin to the goal canvas" is a real gap to own, not a copy.

### Step 5 — Drill-in: WHAT above the fold, HOW behind the Execution tab (lift `run_node.html`)
**Impact: High** | **Effort: Medium — but mostly reuse (~1 day)**

First screenful = WHAT only (outcome, state, evidence, the nudged next step). HOW lives behind an
**Execution tab** that expands run list → one run's dispatch tree → maker-checker with rework
budget + named exits (fix/retry/escalate). **Lift the visual logic of `run_node.html` wholesale** —
it already renders the tree rail, `↻ rework #N` tags, context-usage bars, skill chips, and
rolled-up failure state. Hard cap at **≤2 disclosure levels** (NN/g). This is the single largest
reuse in the whole goal; do not rebuild it.

### Step 6 — Promote human-needed moments *up* to the WHAT level
**Impact: Medium** | **Effort: Low (~¼ day)**

A persistent **"⚠ needs you" chip** at the WHAT level whenever a scripted escalation fires — the
user never polls the Execution tab to discover they're blocked (FR-008 / US3 Scenario 3). This chip
is the *same surface* as the US5 escalation rail and the US10 L3 clarify gate, so Steps 4 and 5 of
the exploration inherit it directly. Wire it as a `drillInto`/`pin` op target so it composes with
the dispatcher.

### Step 7 — FR-017 side-by-side parity mock (in the spike flow)
**Impact: Medium** | **Effort: Low (~½ day)**

A static two-pane illustration: a faux terminal running `cast crud-orchestrator …` beside the
canvas doing the same with defaults — **the same artifact card landing in both**. No logic; it's a
parity *depiction*. The honesty bonus: in real code this parity is true — one `agents/cast-*/cast-*.md`
is materialized to a terminal skill by `bin/generate-skills` and dispatched by the server via tmux,
both emitting the identical `contract_version "2"` envelope. The chat tier is the one leg with no
real surface — which is fine, the prototype invents it (scripted).

### Step 8 — Lock the motion register + accessibility gate (feeds Step 1 design language)
**Impact: Medium** | **Effort: Low (~¼ day)**

Pin the constants every later screen obeys: **~350ms, speed > spectacle, motion reveals layout
(never performs), `prefers-reduced-motion` degrades to a sub-200ms fade.** These are design-language
constraints that flow back to exploration Step 1 and forward to Step 3's per-family shapes. Centralize
them as CSS custom properties (`--morph-duration`, `--ease-morph`) so the whole prototype is tunable
from one place.

---

## Architecture / Interaction Flow

How a chat steer becomes a canvas change — the binding the whole prototype rides on:

```
        CHAT RAIL (ephemeral command log)              CANVAS (durable source of truth)
   ┌──────────────────────────────┐            ┌─────────────────────────────────────────┐
   │ user: "this is a bug not a   │            │  ┌─ goal header ───────────────┐ ◄┐      │
   │        feature"              │            │  │ CAST-412 · Checkout RBAC     │  │      │
   │                              │            │  └──────────────────────────────┘  │      │
   │ ▸ canned reply               │            │  ┌─ WHAT (above the fold) ──────┐  │ view- │
   │   [data-op="morph:debug"]────┼──┐         │  │ outcome · state · evidence   │  │ trans │
   │                              │  │         │  │ ▣ NUDGE: one primary step    │  │ -ition│
   │ ▸ artifact card              │  │         │  │ ⚠ needs you (escalation chip)│  │ -name │
   │   [Pin to canvas]────────────┼┐ │         │  └──────────────────────────────┘ ◄┘ keeps│
   │   [data-op="promote:report"] ││ │         │  ┌─ FAMILY STAGES (crossfade) ──┐  identity│
   └──────────────────────────────┘│ │         │  │ feature: req→explore→plan→…  │  on morph│
                                    │ │         │  │   ⇅ morph ⇅                  │         │
                                    │ │         │  │ debug: hypo→exper→obs ↻2/3   │         │
              ┌─────────────────────┘ │         │  └──────────────────────────────┘         │
              ▼                       ▼         │  ┌─ [Execution tab] HOW drill-in ≤2 lvl ─┐ │
   ┌─────────────────────────────────────┐     │  │ run list → dispatch tree (run_node)   │ │
   │  dispatch(op:arg)                    │     │  │ → maker-checker · rework · fix/retry  │ │
   │  ─────────────────────────────────── │     │  └───────────────────────────────────────┘ │
   │  document.startViewTransition(() =>  │────►└─────────────────────────────────────────┘
   │     OPS[op](arg))   // morph|nudge|  │           ▲ shared-element morph, ~350ms,
   │     promote|drillInto|pin            │           │ undoable, reduced-motion safe
   │  fallback: call OPS[op] directly     │           │
   └──────────────────────────────────────┘           │
        the agent NEVER paints pixels ───────► it emits a typed op the canvas owns

   FR-017 parity (spike flow, static mock):
   ┌─ faux terminal ──────────────┐   ‖   ┌─ canvas (defaults) ──────────┐
   │ $ cast crud-orchestrator …   │   ‖   │ [Run with defaults] ▸        │
   └──────────────┬───────────────┘   ‖   └──────────────┬───────────────┘
                  └────── same .output.json artifact card lands in both ──────┘
```

---

## Key Decisions

| Decision | Recommendation | Rationale (what's traded off) |
|----------|----------------|-------------------------------|
| Chat→UI binding model | **Typed op vocabulary (`data-op` → dispatcher)** | Trades "magical" free-gen UI for predictability + a cheap honest fake. The whole industry is retreating from free-form generative UI (Vercel paused RSC, A2UI catalog, Shopify "agents shouldn't generate UIs"). |
| Morph primitive | **CSS View Transitions API + `view-transition-name` anchors** | Trades a tiny browser-support tail (gated by fallback) for the native, zero-dep, canonical morph. FLIP/Framer are React-idiom fallbacks the prod product can pick later. |
| Morph scope | **One hero morph (feature→debug), flawless** | Trades breadth for polish. Morphing all four families is more build for diminishing demo return; SC-003 needs one undeniable transition, not four soft ones. |
| Framework | **None — vanilla ES modules + one CSS file** | Trades "modern SPA" for zero build cost on a scripted static demo. FR-020 frees the *design*, not the *build*; React buys nothing for canned steps. |
| Promote trigger | **Explicit "Pin to canvas" gesture + staging** | Trades auto-promote speed for predictability + no canvas clutter. NotebookLM "Save to note" / Cursor accept-diff beat ChatGPT auto-open. |
| Source-of-truth rule | **Canvas always authoritative; chat is a lever** | Trades chat-first flexibility for killing three-surface mode confusion (Norman mode-error). Pure chat-first was already rejected in the spec (rebuilds Claude Code, WHAT lives in scrollback). |
| Drill-in depth | **≤2 disclosure levels; escalations promoted to WHAT** | Trades "everything visible" for not-getting-lost (NN/g) and never-blocked-silently (the worst FR-008 failure). |
| Execution surface | **Lift `run_node.html` visual logic wholesale** | Trades bespoke control for a working, elegant in-house component. Rebuilding the dispatch tree is the waste to avoid. |
| Motion register | **~350ms, speed>spectacle, reduced-motion → <200ms fade** | Trades spectacle for trackable responsiveness + accessibility (WCAG 2.3.3). Gimmick morph is the one real contrarian risk; this retires it. |
| Receipt + undo | **Every morph emits a receipt and is reversible** | Trades a little build for retiring the "did I lose my context?" fear (Keyhole Effect). |

---

## Pitfalls to Avoid

1. **Free-generating UI from the model.** Bind chat to the small named op-set; the agent emits
   intents, the product owns the components. *(Vercel paused RSC · A2UI · Shopify MCP-UI)*
2. **Hard-swapping canvases.** Carry the 4 anchor elements across with `view-transition-name`;
   morph with shared identity, <500ms, undoable, reduced-motion safe — never a cognitive reload.
   *(Material Container Transform · Dynamic Island · Keyhole Effect · WCAG 2.3.3)*
3. **Morphing unprompted.** A morph is *always* the visible consequence of an explicit user steer,
   never a surprise. *(Nielsen consistency)*
4. **Two equal-weight primaries.** Exactly one recommended next step per screen; secondaries
   recede. *(Apple HIG / Material)*
5. **Gating the nudge.** Opinionated default + always-present, *cheaper-than-the-mistake* override
   (chat/terminal/manual nav). Adding friction to overrides backfires. *(Rails sharp knives ·
   arXiv 2509.08514)*
6. **Over-nudging.** Repeated suggestions get tuned out (alert fatigue); nudge sparingly.
7. **Leaving value in scrollback.** Explicit, named promote gesture with provenance + version;
   nothing important lives only in chat. *(Hatchworks "Infinite Chat Transcript" · NotebookLM)*
8. **Auto-promote without a staging gate.** Speculative output pollutes the durable canvas. *(Cursor
   accept-diff)*
9. **Artifact divergence.** Once pinned, the canvas object is canonical; chat references it, never a
   stale copy. *(Claude Artifacts footgun)*
10. **Exceeding 2 disclosure levels, or burying escalations in HOW.** Promote human-needed moments
    up to WHAT. *(NN/g)*
11. **Ending a drill-in at a bare pass/fail badge.** Bottom out in evidence (US4). *(Hatchworks
    "Black Box Action-Taking")*
12. **Letting one surface out-power its peers.** Terminal/chat/canvas parity over one substrate; the
    canvas is the always-visible source of truth. *(Stripe/gh · Norman mode-error)*
13. **Gimmick morph — animation for its own sake.** Motion must *reveal* the new layout, not perform.
    Speed > spectacle. *(Linear / Raycast register)*
14. **Re-skinning the dispatch tree.** `run_node.html` already solves it; lifting beats rebuilding.

---

## Success Metrics

- **SC-003 proven, not described:** the feature→debug hero morph visibly reshapes the canvas in one
  scripted chat turn, preserving goal context — target: a single click produces a tracked ~350ms
  shared-element transition + decision receipt, undoable.
- **Binding grammar is honest:** every canvas change in the prototype routes through one named-op
  dispatcher (no bespoke per-screen animation) — target: 100% of interactive canvas changes are
  `morph`/`nudge`/`promote`/`drillInto`/`pin`, zero free-generated markup.
- **One dominant action per screen (SC-002 comprehension):** every canvas state renders exactly one
  visually-primary next step with always-visible overrides — target: a peer states the recommended
  next action at a glance on each screen.
- **WHAT/HOW split holds:** the first screenful of every goal is WHAT-only; HOW is ≤2 levels behind
  the Execution tab; escalations surface at WHAT — target: no runs/dispatch/logs above the fold, no
  silently-blocked state.
- **Promote retires scrollback loss:** at least one chat artifact is pinned to the canvas with
  provenance + version — target: pinned object is canonical, chat keeps only a back-stub.
- **FR-017 parity is depictable:** the side-by-side mock shows the same artifact landing from
  terminal and canvas — target: one screen, no apology, mechanism faithful to the real substrate.
- **Accessibility gate present:** `prefers-reduced-motion` degrades every morph to a <200ms fade —
  target: the hero demo is watchable by a vestibular-sensitive viewer without nausea.
- **Citations carry through:** Steps 3–6 reuse this binding grammar + motion register instead of
  re-deriving — target: zero re-research of interaction mechanics downstream.

---

## Impact Rating: 9/10

**Justification:** This step specifies the **core thesis** of the entire product — the one claim
the prototype must *demonstrate, not describe* (SC-003), and the one moment (the feature→debug
morph) that makes "the canvas adapts per workflow" undeniable rather than asserted. Its highest-
leverage move is naming the keystone — **typed ops, not generated pixels** — which simultaneously
(a) aligns the prototype with where the whole 2026 field has landed, (b) collapses four mechanics
into thin functions off one ~30-line dispatcher, and (c) makes the static fake *grammatically
identical* to the real product's tool-call binding, so the prototype is an honest preview rather
than a façade. It also redirects build effort decisively (one hero morph flawless > four mediocre),
identifies the single liftable asset (`run_node.html`) so US3 isn't rebuilt, and pins a motion
register + accessibility gate the later steps inherit for free. Docked one point only because the
final visual identity that clothes these mechanics is correctly owned by Step 1 (design language)
and the per-family canvas shapes the morph connects are owned by Step 3 — this step supplies the
*interaction skeleton and the strong prior*, not the finished skin.
