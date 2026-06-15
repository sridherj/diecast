# Per-Family Canvas Shapes & Output-Evidence Treatments — Playbook

> **Step 3 of `exploration/steps.ai.md`** — *How should each workflow family's canvas be shaped, and
> how should its output evidence be shown?* Synthesized from
> `research/03-family-canvases-evidence.ai.md` (web, 7 angles) +
> `research/03-family-canvases-evidence-code.ai.md` (codebase terrain).
> **Author:** cast-playbook-synthesizer | **Date:** 2026-06-11 | **Audience:** prototype designer +
> owner sign-off. **Resolves:** [USER-DEFERRED: evidence presentation patterns per family] (Q#12).
> **Serves:** US2, US3, US4, FR-006/007/009/016, SC-005.

## TL;DR

**Do not build four bespoke canvases. Build one six-zone canvas *grammar* and deviate exactly two
zones per family — the stage spine and the evidence surface.** Those two zones carry SC-005 (the
feature-vs-debug contrast "obvious at a glance") almost by themselves; the other four zones (header,
work zone, execution drill-in, decision chips) are pixel-identical across all four flows, which is
what keeps them reading as *one product* (SC-002/004). The non-obvious insight the research forces:
the four evidence treatments are **not stylistic choices — they are forced by what "done well" means
for each work type** (a feature proves itself with screenshots+tests; a bug can *only* be honestly
proven by a formerly-red test now green; a spike's proof is external — the decision it unblocks; an
analysis proves itself with a viz + provenance). Lock the five named treatments **E1–E5** below into
the design system and the deferred Q#12 is answered defensibly. The single biggest mistake to avoid:
rendering any family as the LangSmith/Langfuse span-tree — that trace belongs *behind* the execution
tab (the HOW), never on the WHAT canvas.

## Recommended Stack

| Component | Choice | Why (and why not the alternative) |
|-----------|--------|-----------------------------------|
| Canvas architecture | **One component, six family-keyed slots** ("static component selection" — CopilotKit's 2026 generative-UI pattern) | Frontend owns the frame, the "agent" just picks the variant + fills fake data. Four hand-drawn layouts = 4× build + a disoriented user (contrarian §6). Free-redraw per page is overkill for a static prototype. |
| Per-family differentiator #1 | **Stage spine** — 4 variants: linear backbone / loop counter / timebox meter / pipeline-DAG | This zone alone carries most of SC-005. The current `phase_breadcrumb.html` linear `→` stepper is the *wrong shape* for loops/branches — author 3 new spine shapes. |
| Per-family differentiator #2 | **Evidence surface** — the E1–E5 catalog (one fitted treatment per family) | Forced by first principles (§7): the *form of proof* differs by work type. Today evidence is 100% `markdown → python-markdown → .markdown-body` — a total gap; all four must be authored. |
| Morph mechanic (FR-004) | **CSS-transitioned zone swap** keyed to scripted chat steps (header stays, spine + evidence morph) | Because it's one component with keyed slots, "this is a bug, not a feature" is a cheap, visibly-dramatic Backbone→Investigation-Board swap — not a page reload. Matches Directional-Ideas "CSS-transitioned panel swaps." |
| Build substrate | **Greenfield static HTML/CSS/JS** lifting `_mocks.css` tokens + classes (FR-001/020) | The cast-server FastAPI/HTMX/SQLite stack is *not* the substrate (FR-001 bans a backend). Lift the preso `_mocks.css` palette + PM-shell/card/chip classes; they are zero-dep static HTML. |
| Spike-family canvas seed | **Lift M6 (`M6-A26-spike-branching.html`) near-verbatim** | The preso already designed a two-panel spike canvas: isolation styling (dashed border + muted bg), learned-note that "attaches to CAST-201", decision-file write. Reuse-not-reinvent. |
| Debug-iteration seed | **M5 (`M5-A25-ticket-iterations.html`) v1→v2 activity log + rework budget 1/3** | Closest existing maker-checker loop with checker comments M04/S03/R02. The hypothesis/experiment/observation *vocabulary* is net-new — author it on top of M5's bones. |
| Data-viz idiom | **M9 (`M9-A29-activity-rollup.html`) inline-SVG burndown** | The *only* real chart in either codebase. Proves the palette carries a chart; supplies the inline-SVG idiom for the analysis family's headline viz. |
| Execution drill-in (shared) | **Lift the `/runs` `macros/run_node.html` recursive tree**, re-homed under a goal | The one strong existing asset: dispatch tree + `↻ rework #N` + failure-tint + context-usage bars. Marry it to M5's checker semantics (rule codes, budget X/3, named exits). |
| Trust signal (all evidence) | **Confidence/flag indicator on every treatment** (never a bare green badge) | Trust-calibration research: confident summaries *increase* overreliance. Show what was ruled out / checked / flagged, not just "pass". |

## The Shared Canvas Grammar (build once, deviate per family)

All four families render the **same six zones**. Build this as one component with family-keyed slots.
Zones 2 and 4 are the only ones that change shape per family.

1. **Header band** *(shared, identical chrome)* — classification **pill** + **L1 line** (job statement
   for feature; the *question* for debug/spike/analysis) + status + **the nudged next step rendered as
   the visually-primary action** (FR-003, US1 S4). This band is what makes the four flows one product.
2. **Stage spine** *(differentiator #1)* — linear backbone / loop counter / timebox meter / pipeline.
3. **Work / iteration zone** *(shared frame, family content)* — the live or last pass; **iteration
   history is first-class here** (FR-007), never hidden repeat passes.
4. **Evidence surface** *(differentiator #2)* — the fitted E1–E5 treatment, above the fold (US4).
5. **Execution drill-in** *(shared)* — one tab into the HOW: run list → dispatch tree → maker-checker
   loop with rework budget + named exits (US3 S2). **This is the only place the span-tree lives.**
6. **Decision chips** *(shared)* — in-context decision records (US10); L3 reversibility surfaces the
   escalation rail at WHAT level.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ [PILL]  L1 line / question …………………… status …………… ▶ NUDGED NEXT ACTION │  ← 1 HEADER (shared)
├──────────────────────────────────────────────────────────────────────────┤
│  ◆──◆──●──○──○   |  ↺ iter 2/3   |  ▣ 3h·1h40m used   |  ⬡→⬡→⬡          │  ← 2 STAGE SPINE (×4 variants)
│  feature backbone  debug loop      spike timebox        analysis pipeline   │
├──────────────────────────────────────────────────────────────────────────┤
│  WORK / ITERATION ZONE  (live pass + first-class iteration history)        │  ← 3 (shared frame)
├──────────────────────────────────────────────────────────────────────────┤
│  EVIDENCE SURFACE  →  E1 Accept.Panel | E2+E3 Ledger+Repro | E4 Verdict |  │  ← 4 EVIDENCE (E1–E5)
│                       E5 Report+Provenance                                 │
├──────────────────────────────────────────────────────────────────────────┤
│  ▸ Execution (HOW)  run list → dispatch tree → maker-checker (rework 1/3)  │  ← 5 DRILL-IN (shared)
│  ◦ decision chip  ◦ decision chip                                          │  ← 6 CHIPS (shared)
└──────────────────────────────────────────────────────────────────────────┘
        chat rail (persistent, shared) ─ steers + morphs zones 2 & 4
```

## The Five Named Evidence Treatments (E1–E5) — the answer to Q#12

| # | Name | Family | What it shows | 2026 precedent to mock |
|---|------|--------|---------------|------------------------|
| **E1** | **Acceptance Evidence Panel** | Feature | UI screenshot strip + test-run summary (47 passed/0 failed) + checker-compliance rows (M04/S03/R02 resolved/flagged) + PR #2341 link | ProofShot bundle + Devin computer-use checkpoint screenshots |
| **E2** | **Confirm/Refute Ledger** | Debug | Per-hypothesis *prediction vs observation*, confirmed/refuted mark, alternatives ruled out | Hypothesizer evidence timeline (UIST 2023) |
| **E3** | **Red→Green Repro** | Debug (close) | The failing repro test, then the *same test passing* post-fix | Scientific-debugging "prove the bug, prove the fix" (Undo/Replay) |
| **E4** | **Verdict Card** | Spike | One-line answer + confidence (H/M/L) + the 2–3 deciding data points + `spike_ref` link | Agile spike findings → decision linkage |
| **E5** | **Rendered Report + Provenance** | Analysis | Headline viz/table/HTML + "show the query/source lineage" drill-in | Hex/Deepnote report + data-lineage trust views |

All five obey one rule — **outcome first, proof one click in, full trace two clicks in** (progressive
disclosure: max 3–4 nesting depths). They differ only in the *form of proof*.

## Implementation Steps

Order is by dependency, not impact. Steps 1–2 are the foundation every family consumes; 3–6 build the
four families (do Feature first — it's the backbone the others contrast against, and 3 of 4 evidence
treatments reuse its screenshot/test/checker primitives); 7–8 wire the contrast moments.

### Step 1: Build the six-zone shell + lift the `_mocks.css` design system
**Impact: High** | **Effort: 1 day**

One HTML component with six slots; family selected by a `data-family="feature|debug|spike|analysis"`
attribute on the root. Lift the preso palette and component classes verbatim so all four families
inherit one look:

```css
/* from _mocks.css — lift these tokens */
:root { --bg:#F5F4F0; --text:#1A1A28; --muted:#4A4860; --accent:#D6235C; } /* no blue/purple */
/* reuse classes: .pm-row-head .pm-avatar.agent .pm-chip(.status-spike/.status-progress/.status-done)
   .act-row/.act-body/.act-time (activity log)  .linked-item/.li-id  .ticket-main/.t-head/.t-title
   .dec-box (decision frontmatter)  .pm-integration  .mock-annotation */
```

```html
<section class="canvas" data-family="feature">
  <header class="zone-header">…pill + L1 + status + .nudge-primary…</header>
  <nav    class="zone-spine">…family-keyed spine variant…</nav>
  <main   class="zone-work">…iteration history…</main>
  <aside  class="zone-evidence">…E1–E5…</aside>
  <details class="zone-exec">▸ Execution (HOW)</details>
  <div    class="zone-chips">…decision chips…</div>
</section>
```

The nudged next step is `.nudge-primary` (accent-filled button) in the header of *every* family — the
only visually-primary CTA on the screen (FR-003).

### Step 2: Author the four stage-spine variants
**Impact: High** | **Effort: 1 day**

This zone carries most of SC-005, so make the four shapes *materially* different — not four colorings
of the same stepper:

- **Feature → linear backbone:** horizontal 5-node `Requirements → Exploration → Plan → Execution →
  Done`; current node accent-filled, completed checked, future hollow. Each node clickable.
- **Debug → loop counter:** `Symptom → Hypothesis → Experiment → Observation → ↺ → Root cause → Fix`
  with a prominent **iteration counter "2/3"**. The loop glyph (↺) is the signature — there is *no
  fixed node count* because the search length is unknown (first-principles §7).
- **Spike → timebox meter:** a single horizontal **budget bar** "3h box · 1h 40m used" as the
  dominant status element. Deliberately *lighter* than a spine (one meter, no phase nodes).
- **Analysis → pipeline DAG:** `Question → Sources → Analysis → Visualized answer`; each node opens
  its detail; nodes are *data stages*, not phases.

The AG-UI lifecycle (`started → streaming → finished/failed`) is the per-node status vocabulary to
mimic.

### Step 3: Family 1 — Feature → **Backbone Canvas** + **E1 Acceptance Evidence Panel**
**Impact: High** | **Effort: 1.5 days**

The richest flow and the source of three reusable evidence primitives. Header: feature pill + job
statement + "Execution · 2 of 5 tickets done" + nudge "Review CAST-412's PR". Work zone surfaces the
requirements doc (US7 reachable here). **E1** is a pinned, above-the-fold panel with three rows + a
pointer:

1. **UI screenshot strip** — 2–3 key-moment screenshots (before/after), faked as static images.
2. **Test-run summary** — `47 passed / 0 failed`, coverage delta, "view full log" (badge → counts →
   log = the three disclosure tiers).
3. **Checker-compliance rows** — `M04 ✓ resolved · S03 ✓ resolved · R02 ⚠ flagged` (US4 S3 — *not* a
   bare green badge; show what was checked).
4. **PR link** — `PR #2341` as the artifact pointer (Devin/Codex outcome convention).

**Taste call to confirm with owner:** PR/diff *link* on canvas, full diff in the execution tab — keeps
the WHAT surface about acceptance evidence, not raw code. (Research flags this as a non-blocker.)

### Step 4: Family 2 — Bug fix → **Investigation Board** + **E2 Ledger / E3 Red→Green** (the morph target)
**Impact: High** | **Effort: 1.5 days**

Maximally different on purpose (SC-005) and the destination of the FR-004 morph. Use the detective
case-file layout (UX Magazine): **two panels — left = evidence/case-file** (accepted observations),
**right = live hypotheses** streaming in, hypotheses *visually elevated* above observations (the
"accusation" treatment). Header: bug pill + symptom-as-question "Checkout 500s on coupon apply" +
"Iteration 2/3" + nudge "Run experiment for H3".

The **iteration ledger is the hero**: each pass a row; each hypothesis carries `prediction → observation
→ confirmed/refuted`; refuted hypotheses **stay visible** (`H1 refuted · H2 refuted · H3 confirmed`).
Close with **E3 Red→Green**: the failing repro test, then the same test passing — a green badge alone
is insufficient; the formerly-red test now green is the only honest proof. Seed the activity log from
M5's v1→v2 structure.

### Step 5: Family 3 — Spike → **Timebox Card** + **E4 Verdict Card** (hosts the terminal-parity moment)
**Impact: High** | **Effort: 1 day** *(0.5 if lifting M6 directly)*

Lift **M6** near-verbatim. Deliberately *lighter* than every other family — one card, not a spine
(contrarian §6: a spike must never look like a mini-feature). Header: spike pill + question-as-L1
"Can we use SQLite for the event store?" + the timebox meter. Work zone: a single card with the
**probes-tried list** (each option + one-line result), no phase re-entry, no dispatch tree by default.

**E4 Verdict Card:** one-line answer ("Yes — SQLite holds to 10k events/s; revisit at sharding") +
**confidence (H/M/L)** + the **2–3 deciding data points** + a first-class **`spike_ref`** link shown
*both directions* (the decision references the spike; the spike shows what it feeds). This is also the
**FR-017 host**: render the one side-by-side terminal/canvas moment here — a terminal pane invoking the
same skill next to the canvas doing it with defaults, same artifact landing either way.

### Step 6: Family 4 — Data analysis → **Notebook→Report** + **E5 Rendered Report + Provenance**
**Impact: High** | **Effort: 1.5 days**

A pipeline, not a loop (Hex/Deepnote notebook→report split). Header: analysis pill + question-as-L1
"Which onboarding step drops the most users?". Work zone: analysis steps as **collapsible cells**
(notebook lane), collapsed by default. **E5** is the headline: **the visualized answer up top** —
lift M9's inline-SVG idiom for a real chart/table (US2 S4 / US4 S1 explicitly ban prose-only) — with
**provenance on demand** ("show the query / source lineage": which sources, which transforms, the
SQL). Provenance is this family's trust mechanism — the analog of debug's confirm/refute and feature's
checker rows. Re-runs render as **dated report versions** ("Report v2 · re-run on fresh data").

### Step 7: Wire the canvas-morph (FR-004) — the fluidity demo moment
**Impact: High** | **Effort: 0.5 day**

The scripted chat line "this is actually a bug, not a feature" re-binds `data-family` from `feature`
to `debug`: **header stays**, spine morphs `linear → loop`, evidence morphs `E1 → E2`, goal context
preserved. Implement as a CSS view-transition / class swap on the single canvas component:

```js
canvas.dataset.family = 'debug';   // one attribute flip; CSS handles the transition
// header L1, pill, and chat history persist; only zones 2 & 4 re-render
```

This is the "fluidity demonstrated, not described" requirement (SC-003) — make it visibly dramatic.

### Step 8: Wire the shared execution drill-in + decision chips
**Impact: Medium** | **Effort: 1 day**

One execution tab for all four families: run list → one run's dispatch tree (lift `run_node.html`
recursion) → maker-checker loop with **rework budget 1/3** and **named exits (fix / retry / escalate)**.
This is the only home for the span-tree. Decision chips (US10) sit on the relevant zone; L3
reversibility surfaces the escalation rail at WHAT level (the M8 → @you-with-3-options pattern), so the
user never polls the execution tab to discover they are blocked (US3 S3).

## Architecture / Component Map

```
canvas (ONE component, data-family attribute)
│
├── SHARED (build once, identical across all 4 families)
│     ├── zone-header        pill + L1 + status + .nudge-primary
│     ├── zone-work frame     iteration-history container
│     ├── zone-exec (HOW)      run_node.html tree + M5 maker-checker (rework 1/3, named exits)
│     └── zone-chips           decision records (US10) + L3 escalation rail (M8)
│
└── DEVIATED (the SC-005 contrast — build 4 variants each)
      ├── zone-spine                         ├── zone-evidence
      │   ├─ feature : ◆──◆──●──○──○ backbone │   ├─ feature : E1 Acceptance Panel
      │   ├─ debug   : ↺ loop + "iter 2/3"    │   ├─ debug   : E2 Ledger + E3 Red→Green
      │   ├─ spike   : ▣ timebox meter         │   ├─ spike   : E4 Verdict Card (+ FR-017)
      │   └─ analysis: ⬡→⬡→⬡ pipeline DAG       │   └─ analysis: E5 Report + Provenance (M9 SVG)
      │
      └── chat rail (shared) ── morph: flips data-family → CSS-transitions zones 2 & 4 only
```

**Build-cost insight:** because only 2 of 6 zones deviate, the four "distinct canvases" cost roughly
*1 shell + 8 zone-variants*, not 4 full layouts — and the morph is a one-attribute flip.

## Key Decisions

| Decision | Recommendation | Rationale (and the trade-off) |
|----------|----------------|-------------------------------|
| Four bespoke canvases vs one grammar | **One six-zone grammar, deviate 2 zones** | Preserves SC-005 contrast *and* SC-002/004 coherence; 4× cheaper. Trade-off: families can't diverge arbitrarily — acceptable, the spec wants them to feel like one product. |
| Where the span-tree lives | **Execution tab only, never the canvas** | Observability ("what did the agent do") ≠ outcome ("is the work good"). Diecast's canvas is a WHAT surface. Trade-off: power users click once for the trace — correct per WHAT-primary posture. |
| Debug "done" proof | **E3 Red→Green repro, not a green badge** | A bug is only honestly fixed when the failing test passes. Trade-off: requires faking a before/after test pair — worth it; it's the family's signature proof. |
| Spike shape | **Lightweight Timebox Card, materially lighter than a spine** | If it looks like a shrunk backbone, the "timeboxed/disposable/decision-feeding" signal dies (the exact one-pipeline failure the goal escapes). Trade-off: less visual heft — that *is* the point. |
| Spike value location | **`spike_ref` first-class, shown both directions** | A spike's value is *external* — in the decision it unblocks (Agile canon). Trade-off: needs a decision artifact to link to (reuse M7 `.dec-box`). |
| Analysis answer form | **Headline viz (inline SVG, M9 idiom), prose banned** | US2 S4 explicitly bans prose-only; the viz is the proof. Trade-off: must hand-author a chart — M9 proves the palette carries it. |
| Iteration visibility | **First-class history, refuted hypotheses stay visible** | FR-007; Hypothesizer's whole measured value (5× fix success) is the visible confirmed/refuted trail. Trade-off: more on screen — collapse older passes, never delete them. |
| Morph implementation | **CSS-transitioned `data-family` swap on one component** | Cheap + visibly dramatic; matches Directional Ideas. Trade-off: families must share the shell — already the chosen architecture. |
| Trust signal | **Confidence/flag on every treatment** | Confident summaries *increase* overreliance (trust-calibration research). Trade-off: slightly busier evidence — show what was ruled out, that's the trust mechanism. |
| Visibility default per family | **Feature/spike = outcome-first (hide loop); debug = show every observation** | API-agent vs GUI-agent framing: debug's process *is* the product; the others' loop is rework noise behind the tab. Trade-off: inconsistent default — justified by work type. |

## Pitfalls to Avoid

1. **Trace-tree-as-canvas.** Putting the LangSmith/Langfuse span tree on the WHAT surface. A
   2,000-span run is slow to read even for experts (Braintrust); it makes Diecast look like an
   observability dashboard, not an opinionated workspace. The trace is the execution tab (HOW), full
   stop.
2. **Green-badge-only "done."** A pass/fail badge with no checker rows and no Red→Green repro. Violates
   US4 S3 and trust calibration — a confident badge with no shown-work *increases* overreliance.
3. **Spike-as-mini-feature.** Rendering the spike with the feature backbone shrunk down. Destroys the
   timebox/disposable signal and collapses the family back into the one-pipeline failure mode. The
   Timebox Card must look materially lighter — a budget meter, not a phase spine.
4. **Prose-only analysis.** An analysis answer rendered as text without the viz. US2 S4 bans this
   outright; today's `markdown → python-markdown` renderer would do exactly this by default — it must
   be replaced for this family, not reused.
5. **Hidden iterations.** Collapsing debug passes or report re-runs into a single "latest" with no
   history. Violates FR-007; the entire value of the Hypothesizer pattern is the *visible* search.
6. **Confidence theater.** A confident verdict with no uncertainty indicator and no alternatives-ruled-
   out. Every E1–E5 treatment must carry a confidence/flag signal.
7. **Reusing the linear breadcrumb for loops.** `phase_breadcrumb.html` is an inherently linear `→`
   stepper — wrong shape for the debug loop and the analysis DAG. Author new spine shapes; don't
   recolor the stepper.
8. **Letting the four families drift apart.** If header, drill-in, decision chips, or chat rail differ
   between families, a user who learns the feature flow is lost in the debug flow. Those four zones
   must be pixel-identical; only spine + evidence change.

## Success Metrics

- **Glance-test contrast (SC-005):** in a side-by-side screenshot of the feature and debug canvases, a
  viewer names which is which in **< 3 seconds**, citing the spine shape (backbone vs loop counter).
- **Evidence fit (US4/FR-009):** all four families show a **non-markdown** evidence surface — feature
  has a screenshot strip + test summary, analysis has a rendered chart. Target: **0 of 4** families
  fall back to prose-only.
- **Morph drama (SC-003):** the scripted "this is a bug" chat line visibly reshapes ≥ 2 zones (spine +
  evidence) in a single transition with goal context preserved. Target: **1 demonstrated morph**, no
  page reload.
- **Spike linkage (US2 S3/FR-016):** the spike's Verdict Card and a decision artifact reference each
  other via `spike_ref`, navigable **both directions** in ≤ 1 click each.
- **WHAT-primary (US3 S1):** the first screenful of every family contains **only** WHAT content; the
  span-tree requires **exactly one** click (the execution tab) to reach.
- **Trust signal coverage:** **5 of 5** evidence treatments carry a confidence or flag indicator (no
  bare green badge anywhere).
- **Build economy:** the four canvases ship as **1 shell + 8 zone-variants**, not 4 full layouts; the
  morph is a **1-attribute** flip.

## Impact Rating: 9/10

**Justification:** This step *is* the proof of the product's core thesis — "the UI adapts per
workflow." SC-005 (feature-vs-debug obvious at a glance) and SC-003 (the morph) both live or die here,
and US4's first-class evidence is the "testing is the outcome" posture made visible. The grammar +
E1–E5 decisions are load-bearing for the prototype designer and feed directly into Step 6's build
recipe. It is 9 rather than 10 only because it depends on Step 2's morph mechanic being consistent and
because three of four evidence treatments are net-new authoring (no codebase asset to lift) — execution
risk, not design risk. Get the stage spine and evidence surface right per family and the entire "this
adapts" claim proves itself by contrast.

## Hand-off Notes

- **Resolves Q#12** with the E1–E5 catalog — lock these names into the design system so all four flows
  mock consistently.
- **One open taste call for the owner:** feature-family PR shown *on canvas* (Devin convention) vs
  *execution tab only*. Recommendation: **link on canvas, diff in the tab.** Non-blocker.
- **Reuse map:** M6 → spike canvas (near-verbatim); M5 → debug iteration log; M9 → analysis chart
  idiom; `run_node.html` → execution drill-in; M7 `.dec-box`/M8 escalation → decision chips. The five
  evidence treatments (E1–E5) are net-new design.
- **Dependency on Step 2** (canvas + chat mechanics): the zone-swap morph mechanic is specified there;
  this note assumes the six-zone grammar is the swap unit. Keep consistent.
