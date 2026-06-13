# Execution Manifest: Product Revamp Diecast — Phase 3 (Feature + Debug Flows & the Real Hero Morph)

## How to Execute

Each sub-phase runs in a **separate Claude context**. The four sub-phases are **strictly sequential**
on the critical path (3.1 → 3.2 → 3.3 → 3.4) — **never run any two in parallel** (see the autonomous
decision below). For each sub-phase:
1. Start a new Claude session (or dispatch a `cast-subphase-runner`).
2. Tell Claude: "Read
   `docs/execution/product-revamp-diecast-phase3-feature-debug-morph/_shared_context.md`, then
   execute `docs/execution/product-revamp-diecast-phase3-feature-debug-morph/spN_name/plan.md`."
3. After completion, update the Status column below.

**FULL AUTONOMY (owner-approved, end-to-end through Phase 6):** no user questions, no approval gates,
no idle waits; pick the recommended option at every gate and **propagate the directive to any child
agent** (illustration creator/checker in 3.1; slop-gate visual/tone checkers in 3.4).

**This phase ships CODE** — all changes land in the single file `prototype/index.html` plus
generator-authored ORG extensions and `prototype/assets/` rasters. **NO TESTS anywhere** —
verification is manual click-through / static observation only.

### Binding constraints (full text in `_shared_context.md`; the runner MUST read it first)
1. **NO TESTS** — no test files/suites/harness/CI; manual click-through only.
2. **`file://` legality** — ONE inline `index.html`; no `fetch()`, no local ES-module imports; only
   https CDN imports, classic `<script src>`, and relative `<img>` (E1 rasters under `assets/`).
3. **ORG FROZEN (2a FREEZE)** — all data extensions via `generate-org.mjs` (gate re-runs, refuses on
   violation); **never hand-edit `org.js`**; additive keys only.
4. **Section-stability (Reconciliation F4)** — ORG sections outside the batch's declared additions
   stay byte-identical before/after.
5. **2c stage vocabulary is canonical** (`placeholder:false`) — all labels/surfaces/counts read from
   `stageModels` + `spine_state`; hardcoded vocabulary is a defect.
6. **Closed 5-op vocabulary** — stage nav **reuses `drillInto`** with step-id targets; **no sixth op**.
7. **Morph stays on CAST-412** (header/crumb/chat never change); **undo emits no second receipt**.
8. **`vt-evidence-strip` on the evidence ZONE WRAPPER only** — a duplicate (e.g. via `#/kit`) silently
   kills all transitions.
9. **PRF1** (work_stream agents) + **PRF2** (per-goal chat) are **binding** (owner feedback 2026-06-12).
10. **Failure policy:** retry once with refined instructions; second failure off the critical path →
    log gap + continue; on the critical path (all four sub-phases) → **stop and report**.

### Binding context docs the runner MUST read first
- `docs/plan/2026-06-11-product-revamp-diecast-phase3-feature-debug-morph.md` (the plan)
- `docs/plan/product-revamp-diecast-decisions-so-far.md` (run config, NO-TESTS, **PRF1/PRF2**)
- `docs/plan/2026-06-12-product-revamp-diecast-reconciliation.md` (F4 section-stability)
- `docs/plan/product-revamp-diecast-stage-models.md` (canonical stage vocabulary — compare against)

## Sub-Phase Overview

| # | Sub-phase | Directory/File | Depends On | Status | Notes |
|---|-----------|----------------|-----------|--------|-------|
| 3.1 | Feature Backbone — Stage-Navigator Canvas & E1 Evidence | `sp1_feature_backbone/` | — | Done | Root of the chain; authored ORG `execution`/`morph_view` via generator (gate green, additive-only, F4 byte-identical); PRF1 work-stream + PRF2 per-goal chat **both done**; E1 raster generated directly (illustration agents not in this runner's allowlist — see `borderline-calls.md`) + `onerror` fallback; live-verified (console clean, navigator, surfaces, E1, L1/L3, scripts) |
| 3.2 | Execution Drill-In — Runs, Dispatch Tree, Maker-Checker Loop | `sp2_exec_drillin/` | 3.1 | Done | `RunNode` + `IterationPanel` (pure props-only) + `ExecPanel` shell (`exec-*`); ONE external `RunNode` mount-point (ExecPanel); generator-additive per-node `skills`+`ctx` (gate green, F4 holds); drill beat opens tab + final beat clears `drill` (morph-safe). Static-verified (no browser per autonomy gate) |
| 3.3 | Debug-Loop Canvas — Investigation, E2 Ledger & E3 Red→Green | `sp3_debug_canvas/` | 3.1, **3.2 (serial)** | Done | `#/goal/CAST-431` debug canvas: loop band + `↺ iter 2/3` from data, InvestigationLedger (FR-007 collapsible passes) with E2 hero, E3 red→green @dbg-05, L3 chip+rail, L1 pill, per-goal nudge + Guide line, SCRIPTS.debug (~9 beats incl. thin exec-tab beat). E2/E3 reshaped to the locked EvidenceBlock contracts + `investigation` authored via generator (gate green, deterministic, F4: only CAST-431 changed). PRF1 + PRF2 hold; feature canvas + exec drill-in un-regressed. Static-verified (no browser per autonomy gate; SC-005 glance = human-eyeball carry-forward) |
| 3.4 | The Real Hero Morph & Flow Stitch (SC-003) | `sp4_morph_stitch/` | 3.2, 3.3 | Done | Claimed `vt-evidence-strip` (anchor set now 6×1, on the `.evidence-zone` wrapper); morph data path reads `morph_view` on CAST-412 (loop band/iter 1/3, seeded E2); forward morph = 1 receipt (idempotent), reverse = NO second receipt, morph-safe (clears `drill`); `SCRIPTS.feature` stitched open→…→HOW→collapse→**morph→reverse→L3→close**; generator-additive `statement` on the E2-seed (gate green, F4: 1-line diff). Static-verified: node --check, drift clean, 6×1 anchors, 21/21 logic; morph + slop gates PASS-PROVISIONAL pending eyeball per the no-browser autonomy gate (`borderline-calls.md` 7–10) |

**PHASE 3 COMPLETE** (2026-06-12, run_20260612_043626_bb7d70). All four sub-phases Done; SC-003 (the real "bug, not feature" morph) + SC-005 (feature-vs-debug contrast) proven. Verification is static-only per the full-autonomy no-browser gate; visual/taste items are non-blocking human-eyeball carry-forwards (see `decisions-so-far.md`).

Status: Not Started → In Progress → Done → Verified → Skipped

> **No decision gates in this phase.** Full-autonomy mode resolves all judgment calls; there are no
> human-pause points. (The plan's two reserved gates — 2c sign-off, Phase 1 morph feasibility — are
> already closed in prior phases.)

## AUTONOMOUS DECISION — 3.2 and 3.3 modelled SERIAL, not parallel

The source plan calls Sub-phases 3.2 and 3.3 **"parallel-capable"** (disjoint zones: 3.2 builds the
exec tab, 3.3 builds the debug canvas). **This split overrides that to a SERIAL chain
`3.1 → 3.2 → 3.3 → 3.4`, each its own group.**

**Reason (single-file write-collision avoidance):** all four sub-phases edit the **same single file**
`prototype/index.html`, and there is **no merge mechanism** between two independent
`cast-subphase-runner` agents. Running 3.2 and 3.3 concurrently would race on that file and lose
edits. The plan explicitly permits serial execution ("serially the phase is 4–4.5 sessions, matching
the high-level 2–2.5 day estimate"), so serial is within the planned envelope at zero scope cost. The
disjoint-zone discipline is preserved as a **banner-section** convention (3.2 → `exec-*` section;
3.3 → its own debug-canvas section) so the serial edits stay non-overlapping and reviewable.

## Dependency Graph

```
Sub-phase 3.1 ──► Sub-phase 3.2 ──► Sub-phase 3.3 ──► Sub-phase 3.4 ──► SC-003 + SC-005 proven
 (feature canvas   (exec drill-in)   (debug canvas)    (real morph,
  + ORG extension                                       flow stitch,
  + E1 evidence)                                        slop gate)

  └─ dispatches /cast-preso-illustration-creator + -checker (concurrent within 3.1)
                                                          └─ dispatches /cast-preso-check-visual + -check-tone (within 3.4)
```

> Note: the plan's original DAG had 3.2 ∥ 3.3 as a parallel group after 3.1. This manifest serializes
> that group (see the autonomous decision above). The intra-sub-phase delegations (illustration in
> 3.1; slop-gate checkers in 3.4) remain concurrent *within* their sub-phase — that is in-context
> child dispatch, not a cross-runner file race.

## Execution Order

### Sequential Group 1
3.1 — Feature Backbone (`sp1_feature_backbone/`)

### Sequential Group 2 (after 3.1)
3.2 — Execution Drill-In (`sp2_exec_drillin/`)

### Sequential Group 3 (after 3.2)
3.3 — Debug-Loop Canvas (`sp3_debug_canvas/`)

### Sequential Group 4 (after 3.3)
3.4 — Real Hero Morph & Flow Stitch (`sp4_morph_stitch/`)

## Plan Review

**Skipped** per the owner-approved run configuration ("Plan review: skipped — cross-phase
reconciliation only"; Phase 1/2a/2b/2c precedent, and the plan's Decision 13). This split therefore
does **not** dispatch `/cast-plan-review` and produces no `_review_summary.md`. Re-run manually via
`/cast-plan-review` against any sub-phase file if wanted.

## Progress Log
<Update after each sub-phase.>
- 2026-06-12 — Execution plan created (cast-create-execution-plan, run_20260612_030213_af7357).
  Four sub-phases authored; 3.2/3.3 serialized (single-file write-collision avoidance). All Not Started.
- 2026-06-12 — **3.1 Done** (cast-subphase-runner, run_20260612_031032_7e6f9e). Generator extended with
  `execution` (CAST-412 full / CAST-431 thin) + `morph_view` + 3 new invariants (Rules 12/13/14);
  org.js regenerated (gate green, +303/−0 additive, F4 byte-identical, deterministic). index.html:
  StageSurface (doc/board/pr-thread/ledger/notebook/memo + unknown), StageSpine navigator via
  `drillInto:<step-id>` (no sixth op), PRF1 work-stream from ORG.agents, E1 real raster + `onerror`
  fallback, L1 decision pills, CAST-417 L3 needs-you chip → EscalationRail, SCRIPTS.feature (~7 beats),
  PRF2 per-goal chat. **PRF1 + PRF2 both done.** Live-verified via Chrome (console clean, all paths).
  Next: 3.2 (exec drill-in — consumes the `execution` data authored here).
- 2026-06-12 — **3.2 Done** (cast-subphase-runner, run_20260612_035244_794efa). Built the execution
  drill-in: `RunNode` (recursive, pure props-only — the run_node.html visual idiom: rail-threaded
  recursion, has-failure/has-warning rollup, ↻ rework #N, status dots, skill chips, ctx-tint bars),
  `IterationPanel` (pure props-only — maker/checker ColleagueCard line-density pair + bracket tie,
  M04 ✓ · S03 ✓ · R02 ⚠ finding rows, 3-segment rework meter at 1/3, three INERT named exits with
  raspberry `escalate`, PR diff stub framed as a pr-thread surface), and `ExecPanel` (the `exec-*`
  tab shell below the canvas zones — level-1 flat run list → focus run expands to level-2 tree +
  loop). Mounted at EXACTLY ONE external `RunNode` call-site (ExecPanel); no mini-tree on the WHAT
  surface (trace-creep guard). Generator extended additively (per-focus_run-node `skills`+`ctx` for
  the idiom — the sanctioned DATA RULE path; gate green, deterministic, F4: only the 15 focus_run
  nodes gained keys, all other ORG sections byte-identical, org.js never hand-edited). Feature script
  gained a drill beat (opens the tab) + the final beat now clears `drill` (panel CLOSED at rest →
  the 3.4 morph never snapshots the tree DOM = morph-safe). **PRF1 + PRF2 still hold** (GoalCanvas
  change was solely the stub→ExecPanel swap; work_stream + per-goal chat untouched). Verification:
  `node --check` OK; C2 (no fetch/local imports) OK; single external RunNode mount-point; exec-*
  scoping; drift grep clean; pure-logic checks vs real ORG (13 nodes, rollup=has-failure, rework
  count == iteration.rework.used=1, 0 unresolved agents, CAST-431 thin=2). **Static-only** — a
  browser was connected but live-driving it requires a user-selection gate that FULL-AUTONOMY mode
  forbids; per the prototype no-browser-visual-gate pattern, a human eyeball click-through is the
  carry-forward (does not block). Next: 3.3 (debug canvas — inherits this exec tab for free).
- 2026-06-12 — **3.3 Done** (cast-subphase-runner, run_20260612_041521_4b225a). Built the debug-loop
  canvas at `#/goal/CAST-431` from the SHARED grammar — only spine + evidence/work deviate (SC-005).
  Spine: the `loop` band + `↺ iter 2/3` render from `stageModels.debug` + `spine_state.iter` (no
  watermark; symptom-as-question header). Work zone: a new `InvestigationLedger` (`dbg-*`, pure
  props-only) renders the FR-007 iteration history — passes that COLLAPSE via `<details>` (pass 1
  closed, pass 2 live), each with experiment rows (line-density `ColleagueCard` attribution resolved
  vs ORG.agents) and the LOCKED E2 `EvidenceBlock` as the live pass's hero (H1/H2 struck-but-visible,
  H3 confirmed) + the one L1 decision pill. E3 red→green renders at its home step (dbg-05) via the
  navigator. Debug L3 → the needs-you chip + EscalationRail (exactly one L3). `SCRIPTS.debug` (~9
  beats, every token ORG-derived) walks open → nudge → investigation → E2 → E3 → L3 → the THIN
  exec-tab beat → close; keyed per-goal (PRF2). `SpineLoop` gained an iter-overflow guard (`--fail` +
  console.warn, no silent clamp). The Guide line + nudge are now PER-GOAL (feature line/nudge
  byte-identical → no regression). DATA: CAST-431's E2/E3 reshaped to the locked EvidenceBlock
  contracts + an additive `investigation.passes` authored via `generate-org.mjs` (new invariant Rule
  15; gate green, deterministic, F4: only CAST-431 changed — CAST-412/452/461 + stageModels/agents/
  decisions byte-identical; org.js never hand-edited). **PRF1 + PRF2 hold for CAST-431; the
  shared-grammar rule held; the feature canvas + exec drill-in are un-regressed.** Verification:
  `node --check` OK; C2 (no fetch/local imports) OK; no 2c stage-label hardcoding; 24/24 pure-logic
  render-path assertions pass. **LIVE-VERIFIED** (the user reconnected the Chrome extension after the
  static pass; prototype served on `http://localhost:8123`): console clean across the full flow;
  **SC-005 glance test PASSES** (feature segment bar vs debug loop band + `↺ iter 2/3`, side-by-side);
  InvestigationLedger passes (pass 1 collapsed / pass 2 live) + E2 hero (H2 struck-visible, H3
  confirmed); E3 red→green at dbg-05 (FAIL-before then PASS-after); all 9 SCRIPTS.debug beats fire in
  order; thin exec tab (2 runs, 2-node shallow tree — no deep tree); feature canvas byte-identical.
  See `sp3_debug_canvas/borderline-calls.md` §6. Next: 3.4 (the real CAST-412 morph).
- 2026-06-12 — **3.4 Done — PHASE 3 COMPLETE** (cast-subphase-runner, run_20260612_043626_bb7d70). The
  real hero morph replaces the Phase-1 placeholder. **Sixth anchor `vt-evidence-strip`** claimed on the
  new `.evidence-zone` wrapper (the `.body` second zone), present in both the feature and morphed renders
  so it glides while its EvidenceBlock content crossfades (E1 strip ⇄ E2 seed); anchor set is **6×1**,
  absent from `#/kit`. **Morph data path:** on CAST-412 (a feature goal) viewed as debug, the spine +
  work stream + evidence read `goals['CAST-412'].morph_view` (loop band, iter 1/3, the coupon-apply
  symptom + first hypotheses, the E2 seed) via two pure helpers (`deriveMorphSpine`,
  `deriveMorphInvestigation`) — NOT the real debug goal; header/crumb/chat/nudge persist (same goal, new
  shape). **Undo = one atom, one receipt:** the forward morph drops the `DEC-CAST-412-03` receipt (once,
  idempotent), the scripted reverse emits NO second receipt and restores the feature canvas exactly;
  `morph()` force-clears `drill` (morph-safe — the exec tree never joins a snapshot). **Flow stitch:**
  `SCRIPTS.feature` now runs open→navigator→promote→evidence→HOW→collapse→**morph→reverse→L3→close** via
  `advance()` + the locked `startViewTransition` path (350ms / `--ease-morph`; reduced-motion → 180ms
  fade); the morph fires ONLY from the scripted user line; reload resets; PRF2 holds across the morph.
  **DATA:** the sole ORG change is an additive `statement` on `morph_view.evidence.E2-seed` (via
  `generate-org.mjs`; gate green; F4: that one line is the only org.js diff; never hand-edited). No
  Phase-1 placeholder morph/spine data remained to delete (superseded by spine reads in 3.1; placeholder
  vocabulary lives only in the `#/kit` FIXTURES, the sanctioned C4 exception). **Verification (static /
  no-tests, no-browser autonomy gate):** `node --check` OK; C2 (no fetch/local imports) OK; vt- anchors
  6×1; `.evidence-zone` at exactly one call-site, not on `#/kit`; drift grep clean (zero new hardcoded
  canonical tokens in rendered strings — all hits are `data/`, comments, or the `#/kit`/FIXTURES
  allowlist); **21/21 pure-logic morph assertions pass**. **Morph gate (5-item):** item 3 (`file://`)
  hard PASS; items 1/2/4/5 (glide / no-flash / ~350ms / reduced-motion) PASS-PROVISIONAL pending eyeball.
  **Slop gate (4 surfaces):** external checkers not in this runner's allowlist → static self-assessment,
  PASS-PROVISIONAL (not-generic / not-ai-aesthetic; new morph copy em-dash-free + GPT-ism-free). No
  panel-swap contingency needed (real-DOM View-Transition path retained). PRF1/PRF2 + all three canvases
  (feature, debug, exec drill-in) un-regressed. Carry-forwards: eyeball the morph + re-run both slop
  checkers on a real 1440px screenshot; CF3 de-em-dash copy pass across all narration. See
  `borderline-calls.md` §7–10.
