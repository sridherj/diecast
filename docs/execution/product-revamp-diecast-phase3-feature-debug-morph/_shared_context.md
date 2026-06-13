# Shared Context: Product Revamp Diecast — Phase 3 (Feature + Debug Flows & the Real Hero Morph)

> Read this file at the start of **every** sub-phase session, then execute that sub-phase's
> `plan.md`. The binding constraints below are not optional — they are reconciled cross-phase
> contracts. Violating one is a defect, not a judgment call.

## Source Documents
- **Plan (the source of this split):**
  `docs/plan/2026-06-11-product-revamp-diecast-phase3-feature-debug-morph.md`
- **Decisions / run config / owner feedback:**
  `docs/plan/product-revamp-diecast-decisions-so-far.md`
  (Run Configuration; **Owner Prototype-Review Feedback (2026-06-12 — BINDS Phase 3)** = PRF1/PRF2)
- **Cross-phase reconciliation (F4 section-stability):**
  `docs/plan/2026-06-12-product-revamp-diecast-reconciliation.md`
- **Canonical stage vocabulary (THE single source — never re-derive):**
  `docs/plan/product-revamp-diecast-stage-models.md`

## Project Background

Phase 3 makes the product thesis real. The two most-contrasting workflow families become clickable
end-to-end from the frozen org spine, and the **real** "this is actually a bug, not a feature" chat
morph lands between them — proving **SC-003 for real** and making **SC-005's feature-vs-debug
contrast obvious at a glance**.

- **Feature family** — `CAST-412 — Add RBAC to checkout`: the 2c-derived `segments` spine acts as a
  *navigator* (click a step → that stage's artifacts render as a familiar-tool surface), the
  work-happening stream renders live tickets + the `@you` manual item, and the **E1 acceptance
  evidence** panel sits at its home step (`feat-05`).
- **Debug family** — `CAST-431 — Checkout 500s on coupon apply`: the 2c-derived `loop` spine with an
  `↺ iter 2/3` counter, an investigation work zone where iteration history is first-class (refuted
  hypotheses struck but visible), the **E2** confirm/refute ledger as the work-zone hero (home step
  `dbg-04`), and the **E3** red→green repro (home step `dbg-05`).
- **The morph** — replaces the Phase-1 placeholder: on `#/goal/CAST-412`, the scripted chat line
  reshapes the feature canvas into the debug-family shape in ~350ms with ≥4 anchors gliding, drops
  the receipt derived from atom `DEC-CAST-412-03`, and is undoable via a scripted reverse.

The exploration's build-cost insight governs everything: the two canvases are **one canvas grammar
with two deviated zones** (spine + evidence/work), not two bespoke layouts. The shared zones
(header, work-stream frame, drill-in, decision chips, chat rail) are what make the morph cheap and
the product read as one product. Almost every pixel composes from the **Phase 2b component kit**.

**Operating mode: HOLD SCOPE.** Plan exactly the five activities the high-level plan bounds Phase 3
to: feature backbone canvas, execution drill-in, E1 wiring, debug-loop canvas, the real morph. No
spike/data canvases (Phase 4), no board/hiring/Layer-2 surfaces (Phase 5), no walkthrough overlays
or asset inlining (Phase 6).

**FULL AUTONOMY MODE (owner-approved, end-to-end through Phase 6):** never ask the user questions,
never pause for approval gates, never go idle waiting for input. At every decision gate pick the
recommended option and document it. **Propagate this directive verbatim to any child agent you
dispatch** (the illustration creator/checker and the slop-gate checkers).

## BINDING CONSTRAINTS (carried into every sub-phase; each is a defect if violated)

1. **NO TESTS anywhere.** No test files, suites, harness, or CI in any sub-phase. All verification
   is **manual click-through / static observation only** — open `prototype/index.html` from disk,
   click, observe. (The E1 panel's fake test summary `47 passed / 0 failed` and E3's red→green
   output are rendered prototype **data**, not tests.)
2. **`file://` legality — ONE inline file.** Everything ships in the single `prototype/index.html`
   (inline `<style>` + inline module). `file://` blocks `fetch()` and **local ES-module imports**.
   Allowed: **https CDN** imports via the import-map, classic `<script src>` (this is how `org.js`
   loads), and **relative `<img src>`** (E1 rasters under `prototype/assets/` load fine from
   `file://`). Verify relative `<img>` from `file://` in Chrome as the *first* E1 activity.
3. **ORG data is FROZEN (2a FREEZE).** All data extensions (`goals[id].execution`, `focus_run`
   tree, `iteration`, `morph_view`, etc.) MUST go through the seeded generator
   `prototype/data/_build/generate-org.mjs`, which re-runs its invariant gate and **refuses to emit
   on violation**. **NEVER hand-edit `prototype/data/org.js`.** Only additive keys; `git diff` must
   show additions only.
4. **Section-stability invariant (Reconciliation F4).** All ORG sections **outside** the batch's
   declared additions must be **byte-identical** before/after regeneration. After regenerating,
   diff `org.js` and confirm nothing outside your declared additions changed.
5. **2c stage vocabulary is canonical and already in `org.js`** (`placeholder: false`; watermarks
   dropped). All labels/surfaces/counts/step-order read from `ORG.stageModels.<family>.steps[]`
   + each goal's `spine_state`. **Any hardcoded stage vocabulary in `index.html` is a defect.**
   A grep for any 2c label string in `index.html` must return nothing (labels appear only via data).
6. **Closed 5-op vocabulary stays closed** (`morph · nudge · promote · drillInto · pin`). Stage
   navigation **REUSES `drillInto`** with step-id targets — **NO sixth op**. The dispatcher's
   `drillInto(arg)` branches: `arg === 'execution'` = HOW target; `arg === '<step-id>'` = stage
   focus. Document the branch next to the OPS table.
7. **The morph stays on CAST-412.** Goal id, title, crumb, and chat history never change (same goal,
   new shape). `morph_view` supplies the post-reclassification debug-shape state. The **undo emits
   NO second receipt** (one atom `DEC-CAST-412-03`, one receipt, reversibility shown via scripted
   reverse).
8. **`vt-evidence-strip` anchor goes on the evidence ZONE WRAPPER only.** A duplicate
   `view-transition-name` (e.g. via `#/kit` rendering a wrapper with the same name) **silently kills
   all transitions** (Phase 1 uniqueness rule). The `#/kit` route shows bare components — it must
   not render a wrapper carrying this anchor.
9. **Failure policy:** retry a failed sub-phase **once** with refined instructions. Second failure
   **off** the critical path → log a gap and continue. Second failure **on** the critical path
   (3.1 → 3.2 → 3.3 → 3.4 — all four are on it under the serial model) → **stop and report**.

## OWNER REVIEW FEEDBACK — BINDING (PRF1, PRF2)

- **PRF1 — work-happening stream renders from ORG, not kit fixtures.** `GoalCanvas` today renders
  three **2b kit FIXTURES** (`FIXTURES.CO/CC/YOU`) for the "In flight · work" stream, so CAST-412
  shows generic colleagues unrelated to "Add RBAC to checkout". Phase 3's per-goal work renderer
  MUST read `ORG.goals[id].work_stream` (ticket-shaped `{id, label, assignee, step, kind}`),
  **resolving each `assignee` against `ORG.agents`**, and replace the kit-fixture `ColleagueCard`s.
  CAST-412's assignees resolve to real agents: `entity-creation · api-contractor · migration-author
  · crud-orchestrator`, plus `@you`. **Lands in sub-phase 3.1** (the work-happening stream).
- **PRF2 — ChatRail is PER-GOAL, not global.** Phase 1 left `appState.chat = {messages,
  scriptIndex}` as one **global** object shared across goals. Key chat state by goal id
  (e.g. `appState.chat.byGoal[goalId] = {messages, scriptIndex, scriptKey}` or equivalent) so
  switching goals shows that goal's thread. This **refines (does not rename)** the Phase-1 `chat`
  contract and **composes with** the additive `scriptKey`. **Lands in the sub-phase that introduces
  SCRIPTS/scriptKey** — author the per-goal keying in 3.1 (where SCRIPTS.feature + scriptKey are
  introduced) and confirm it holds across the morph in 3.4.

## Codebase Conventions

- **Single-file prototype:** `prototype/index.html` — inline `<style>` + inline `<script type=module>`,
  `render(appState) → DOM` (pure render), htm + preact-style components via https CDN import-map.
- **Banner sections:** partition `index.html` by banner-comment sections (the 2b precedent) so the
  growing single file stays navigable. Phase 6 owns packaging.
- **CSS prefixes (greppable):** `surf-*` = stage surfaces (`StageSurface`); `exec-*` = execution
  drill-in. Existing kit prefixes unchanged.
- **Component naming:** PascalCase — `StageSurface`, `RunNode`, `IterationPanel`.
- **vt- anchors live on shell zone wrappers, NEVER on kit components.**

## Key File Paths

| File | Role |
|------|------|
| `prototype/index.html` | THE single-file prototype — all four sub-phases edit it (serial; see manifest) |
| `prototype/data/org.js` | Frozen `window.ORG` (classic script). **Generated — never hand-edit.** |
| `prototype/data/_build/generate-org.mjs` | The seeded generator + invariant gate; the ONLY sanctioned path to extend ORG |
| `prototype/assets/` | E1 raster screenshots (`e1-*.png`), loaded via relative `<img src>` |
| `cast-server/cast_server/templates/macros/run_node.html` | The `run_node` **visual idiom** lifted (not modified) into `RunNode` |
| `docs/plan/product-revamp-diecast-stage-models.md` | Canonical stage vocabulary to compare the rendered spine against |

## Data Schemas & Contracts (copy verbatim into ORG via the generator)

**Stage models (already encoded in `org.js`, `placeholder:false` — read, do not author):**
- `feature` — shape `segments`, `linear-reentrant`, 5 steps: `feat-01..05`
  (Shape the Problem · Commit & Scope · Design Approach · Build & Ship · Show It's Done).
  Surfaces: `doc · board · doc · pr-thread · pr-thread`. **E1 home = `feat-05`.**
  `spine_state.current: 'feat-04'`.
- `debug` — shape `loop`, `loop:{over:['dbg-02','dbg-03','dbg-04'], budget:3}`, 5 steps:
  `dbg-01..05` (Reproduce Reliably · Form a Hypothesis · Run an Experiment · Log Confirm/Refute ·
  Prove the Fix). Surfaces: `ledger · ledger · ledger · ledger · pr-thread`.
  **E2 home = `dbg-04`, E3 home = `dbg-05`.** `spine_state.iter: {current: 2, budget: 3}`.
- Each step shape: `{id, label, shortLabel?, does, surface, surfaceWhy, artifacts[], refs[], evidence}`.

**ORG additive extension this phase authors (contract #4 of the plan):**
```js
goals[id].execution = {
  runs: [{ id, agent, status, when, summary, rework_count }],
  focus_run: <recursive node tree>,            // ~13 sub-agents on CAST-412; none on CAST-431
  iteration: {
    maker, checker,
    findings: [{ code, label, status, round }], // M04 ✓ · S03 ✓ · R02 ⚠ flagged
    rework: { used: 1, budget: 3 },
    exits: ['fix','retry','escalate'],
    pr: { id, label, diff_stub }
  }
}                                              // FULL depth on CAST-412; THIN on CAST-431 (2 runs, no deep tree)

goals['CAST-412'].morph_view = {
  spine_state: { iter: { current: 1, budget: 3 } },
  work_stream: [ ...2-3 experiment rows... ],   // symptom row + first hypotheses (coupon-apply weave)
  evidence: { 'E2-seed': <first hypotheses> }
}
```
**New generator invariants** (added alongside the data): every tree node's `agent` resolves in
`ORG.agents`; `focus_run` rework tags consistent with `iteration.rework`; exactly **one** `focus_run`
per goal that has `execution`.

**Decision atoms (already in ORG, PB-05 schema + `diff`):** `DEC-CAST-412-03` "Classify CAST-412 as
bug, not feature" (L2 — the morph receipt); the feature L3 on ticket `CAST-417` (roles-column
migration, 3 ranked options + evidence pack); the debug L3 (shared-auth-middleware fix scope); the
superseded L1 pair (GraphQL→REST) in the feature goal.

**Scenario engine (Phase 1, unchanged API):** `{narration, patch, transition?}` steps + `advance()`.
Phase 3 adds `SCRIPTS = { feature: [...], debug: [...] }` and `appState.chat.scriptKey` (additive,
set on goal-route entry by family) — **keyed per-goal per PRF2**.

**vt- anchors (on shell zone wrappers):** `vt-goal-header · vt-chat-rail · vt-nudge-card ·
vt-receipt-trail · vt-nav-rail` (Phase 1) **+ `vt-evidence-strip`** (this phase exports it).
**Motion tokens:** `--morph-duration: 350ms`, `--ease-morph`, `--motion-fast: 120ms`,
reduced-motion fade ≤200ms. A duplicate `view-transition-name` silently kills the whole transition.

**Contracts this phase EXPORTS (Phases 4/5/6 consume):** `vt-evidence-strip`; the stage-navigator
interaction (`appState.stageFocus`); the execution drill-in grammar (`RunNode` + `IterationPanel`);
the ORG `execution`/`morph_view` extension; per-family `SCRIPTS` + `scriptKey`; the
`prototype/assets/` raster-evidence rule.

## Pre-Existing Decisions (from the plan's Decisions Made Autonomously + Run Config)

- **Plan review: SKIPPED** per the owner-approved run config (cross-phase reconciliation only;
  Phase 1/2a/2b/2c precedent). Re-run manually via `/cast-plan-review` against the plan file if
  wanted. This split therefore does **not** dispatch `/cast-plan-review`.
- Execution: end-to-end through Phase 6, no human checkpoints.
- Sub-phase split `3.1 → (3.2, 3.3) → 3.4`; the morph comes last (it swaps between the two *real*
  canvases). **AUTONOMOUS ORDERING OVERRIDE (this split): 3.2 and 3.3 run SERIAL, not parallel** —
  see the manifest's autonomous decision note (single shared `index.html`, no merge mechanism
  between two independent runner agents → serial avoids a write collision; the plan permits serial
  at ~4–4.5 sessions).
- Execution-run data added as an ORG **additive** extension via the 2a generator (Decision 2).
- The morph stays on CAST-412 (Decision 3); stage nav reuses `drillInto` (Decision 4);
  `vt-evidence-strip` on the evidence zone wrapper (Decision 5); E1 screenshots = real rasters via
  `/cast-preso-illustration-creator` + `-checker` (Decision 6); per-family `SCRIPTS` + additive
  `scriptKey` (Decision 7); full drill-in depth only on the feature flow (Decision 8); undo emits no
  second receipt (Decision 9); named exits/rail options render complete but **inert** except
  script-wired beats (Decision 10); `RunNode`/`IterationPanel` are pure props-only kit components
  (Decision 11); slop gate on four surfaces (Decision 12).

## Relevant Specs

`docs/specs/_registry.md` — all seven specs govern the **cast-server runtime**. Per **FR-020 the
prototype is greenfield**: no spec applies, none is contradicted, and **no `/cast-update-spec`
action** is in scope for this phase. `run_node.html` is lifted as a *visual idiom* into greenfield
prototype code — the `/runs` page itself is untouched. **No specs cover files in this plan.**

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|-----------|------|-----------|--------|-------------------|
| 3.1 Feature Backbone (`sp1_feature_backbone`) | Sub-phase | — | 3.2, 3.3 | None |
| 3.2 Execution Drill-In (`sp2_exec_drillin`) | Sub-phase | 3.1 | 3.3 (serial) → 3.4 | **None** (serial override) |
| 3.3 Debug-Loop Canvas (`sp3_debug_canvas`) | Sub-phase | 3.1, 3.2 (serial) | 3.4 | **None** (serial override) |
| 3.4 Real Hero Morph (`sp4_morph_stitch`) | Sub-phase | 3.2, 3.3 | — | None |

> **Why serial, not parallel:** the plan calls 3.2 and 3.3 "parallel-capable" (disjoint zones), but
> all four sub-phases edit the **same single file** `prototype/index.html` and there is **no merge
> mechanism** between two independent `cast-subphase-runner` agents. Running them concurrently would
> race on the file. The plan explicitly permits serial execution (~4–4.5 sessions), so this split
> models the chain `3.1 → 3.2 → 3.3 → 3.4`, each its own group.
