# Sub-phase 3.1: Feature Backbone — Stage-Navigator Canvas & E1 Evidence

> **Pre-requisite:** Read
> `docs/execution/product-revamp-diecast-phase3-feature-debug-morph/_shared_context.md` before
> starting. Every BINDING CONSTRAINT and the PRF1/PRF2 owner feedback there apply here.

## Objective

`#/goal/CAST-412` becomes the **real feature canvas** and the backbone every later sub-phase
consumes: the 2c-derived `segments` spine (no watermark, real vocabulary from
`ORG.stageModels.feature`) acts as a **navigator** — clicking a step shows that stage's artifacts
rendered as its familiar-tool surface; the work-happening stream renders **live tickets from
`goal.work_stream` + the `@you` manual item** (PRF1); the **E1 acceptance panel** (real screenshot
images + test summary + checker rows + PR link) sits at its home step (`feat-05`); one L1 decision
chip and the CAST-417 L3 needs-you moment surface at the WHAT level. The first screenful is
WHAT-only. This sub-phase also extends ORG (via the generator) with the `execution`/`morph_view`
data that 3.2 and 3.4 consume, and introduces `SCRIPTS.feature` + per-goal `scriptKey` (PRF2).

## Dependencies
- **Requires completed:** Phase 2a (`org.js` frozen), 2b (kit + aesthetic lock), 2c (`stageModels`
  rewritten, `placeholder: false`). **None of the Phase 3 sub-phases** — this is the root of the chain.
- **Assumed codebase state:** `prototype/index.html` carries the Phase-1 morph skeleton +
  dispatcher/scenario engine, the 2a data spine, and the 2b component kit (`#/kit`). Routes live:
  Home / `#/goal` / `#/board` / `#/kit`. `ORG.goals['CAST-412'].work_stream` already exists
  (ticket-shaped, assignees resolve to `ORG.agents`).
- **Gate check before building:** if 2c's vocabulary has **not** landed (`placeholder:true` still on
  `stageModels.feature`, or a watermark renders), **stop and resolve 2c first** — building against
  watermarked placeholders violates the owner's directive.

**Estimated effort:** 1.5 sessions (~4h; the illustration delegation runs in parallel with the canvas work).

## Scope

**In scope:**
- Extend ORG via the generator: `goals[id].execution` (CAST-412 full / CAST-431 thin),
  `goals['CAST-412'].morph_view`, and the three new invariants.
- `StageSurface({step, artifacts})` renderer keyed on `step.surface`.
- Make `StageSpine` a navigator (reuse `drillInto` with step-id targets; `appState.stageFocus`).
- Work-happening stream from `goal.work_stream` resolved against `ORG.agents` (**PRF1**).
- E1 wiring (`EvidenceBlock {kind:'E1'}`) at `feat-05`, with real raster screenshots
  (delegate creation + checking).
- Decision chips (L1 6A pill) + the CAST-417 L3 needs-you chip + `EscalationRail` at WHAT level.
- `SCRIPTS.feature` (~7 steps) + `appState.chat.scriptKey`, **keyed per-goal** (**PRF2**).

**Out of scope (do NOT do these):**
- The execution drill-in panel internals (`RunNode`, `IterationPanel`, the dispatch tree) — that is
  **3.2**. (3.1 only authors the *data* and the canvas shell that hosts the Execution tab.)
- The debug canvas `#/goal/CAST-431` rendering — that is **3.3**.
- The real morph / `vt-evidence-strip` claiming / flow stitch / slop gate — that is **3.4**.
- Any spike/data canvas, board/hiring surfaces, walkthrough overlays, asset base64-inlining.
- **Any test file, suite, harness, or CI.** **Any hand-edit of `org.js`.**

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `prototype/data/_build/generate-org.mjs` | Modify | Seeded generator; gains `execution`/`morph_view` emit + 3 new invariants |
| `prototype/data/org.js` | Regenerate (never hand-edit) | Frozen; gains additive `execution`/`morph_view` keys only |
| `prototype/index.html` | Modify | Has Phase 1/2a/2b base; gains `StageSurface`, navigator, work-stream, E1, chips, `SCRIPTS.feature` |
| `prototype/assets/e1-*.png` | Create (via delegation) | Do not exist; 2–3 fake checkout before/after-RBAC screenshots |

## Detailed Steps

### Step 3.1.1: Extend the spine via the generator (the sanctioned path — do this FIRST)
- Edit `generate-org.mjs` to emit the `execution` blocks (CAST-412 full / CAST-431 thin),
  `morph_view`, and the new invariants (see `_shared_context.md` → Data Schemas).
- The ~13-node `focus_run` tree reuses existing roster slugs (`crud-orchestrator` +
  `crud-compliance-checker` prominent; depth ≤3) and one `↻ rework #1` node consistent with
  `iteration.rework {used:1, budget:3}`.
- Add the three invariants: every tree node's `agent` resolves in `ORG.agents`; `focus_run` rework
  tags consistent with `iteration.rework`; exactly one `focus_run` per goal that has `execution`.
- Regenerate `org.js`. Confirm the **gate passes** and `git diff prototype/data/org.js` shows
  **only additive keys** (BINDING #3). Confirm all sections outside the additions are
  **byte-identical** (BINDING #4 / Reconciliation F4).

### Step 3.1.2: Build `StageSurface({step, artifacts})`
- One renderer keyed on `step.surface`: `doc` (rendered document card: title, version chip, body
  excerpt), `board` (ticket-list rows), `pr-thread` (review-thread rows), `ledger`/`notebook`/`memo`
  (thin Phase 3 versions; Phase 4 fleshes out notebook/memo).
- Full-bleed in the stage-artifacts zone (familiar-tool principle); one-line `surfaceWhy` caption
  ties the surface to the step.
- **Unknown surface kind** renders a visible `unknown surface` placeholder with `console.warn`
  (zero silent failures). New CSS prefix `surf-*`.

### Step 3.1.3: Make `StageSpine` a navigator
- Step clicks set `appState.stageFocus = '<step-id>'` through a scripted-safe local handler that
  **routes through `dispatch('drillInto:<step-id>')`** — **do NOT add a sixth op** (BINDING #6).
  `drillInto`'s argument grammar already supports targets: `'execution'` = HOW target, `<step-id>` =
  stage focus. The dispatcher's `drillInto(arg)` branches on `arg === 'execution'`. **Document the
  branch next to the OPS table.**
- `stageFocus: null` = "current step" (default view). Clicking the current step (or an explicit
  "current" affordance) returns to default. Back/forward and re-render preserve `stageFocus`.

### Step 3.1.4: Work-happening stream — **PRF1 (BINDING)**
- Render rows of line-density `ColleagueCard`s from **`ORG.goals[id].work_stream`**, resolving each
  `assignee` against **`ORG.agents`** (`entity-creation · api-contractor · migration-author ·
  crud-orchestrator`, plus `@you`). **Replace the 2b kit FIXTURES** (`FIXTURES.CO/CC/YOU`) —
  rendering kit fixtures here is the exact defect PRF1 names.
- Run-status pills come from data; the `@you` manual item renders the needs-you accent **only when
  blocking**. The stream is family-agnostic chrome (the same frame the debug canvas fills with
  experiments in 3.3).

### Step 3.1.5: Wire E1 (with real raster screenshots)
- First, **verify relative `<img>` loads from `file://` in Chrome** (BINDING #2) — this is the
  *first* E1 activity. If a quirk surfaces, fall back to 2b's CSS/SVG thumbnails and record in
  `borderline-calls.md`.
- Place `EvidenceBlock {kind:'E1', data: goal.evidence}` at its home step (the step whose
  `evidence === 'E1'` → `feat-05`); also summarize it in the default view's evidence strip.
- Replace 2b's CSS/SVG placeholder thumbnails with real images:
  → **Delegate: `/cast-preso-illustration-creator`** — brief: 2–3 fake product screenshots for the
    E1 strip (checkout UI before/after RBAC, matching the spine's `assets/e1-*.png` refs; alt text +
    captions supplied from `ORG`), Diecast light-world style tokens, **no glass/gradient/glow**.
    Output to `prototype/assets/`. **Pass the FULL AUTONOMY directive down.**
  → **Delegate: `/cast-preso-illustration-checker`** on the results; rework on fail (budgeted loop).
    Review output for style-bible consistency with the locked identity before accepting.
- E1 panel renders: 2–3 screenshot images (alt + captions from the spine), `47 passed / 0 failed` +
  coverage delta, checker rows `M04 ✓ · S03 ✓ · R02 ⚠ flagged`, and the `PR #2341` **link only**
  (no diff on canvas — the diff lives behind the Execution tab, locked Q#17 call).
- **Error path:** missing `assets/` images (file moved / creator output rejected) must render the 2b
  CSS/SVG placeholder thumbnail via an `onerror` swap — a visible fallback, never a broken-image icon.

### Step 3.1.6: Decision chips + L3 at WHAT level
- Render 6A `Decision` pills for the goal's in-context atoms on their owning artifacts (e.g. the
  superseded GraphQL→REST L1); clicking opens the 6B callout; the `DEC-…` id matches the atom.
- The CAST-417 L3 atom renders a persistent "⚠ needs you" chip in the header band; clicking opens
  the `EscalationRail` (3 ranked options, **nothing pre-selected**, evidence pack visible) **without
  entering the Execution tab** (US3 S3). Rail options stay **inert** except where 3.4's script wires
  one (Decision 10).

### Step 3.1.7: Author the feature flow script + per-goal chat — **PRF2 (BINDING)**
- `SCRIPTS.feature` (~7 steps): open goal → Guide nudge (why-line) → click-through beat on the spine
  navigator → promote/pin beat (reuse Phase 1's promote against a *real* artifact) → evidence beat
  (E1) → the L3 needs-you beat → close. Narration **interpolates canonical tokens from `ORG`**
  (CAST-412, M04/S03/R02, 1/3, PR #2341, agent slugs) — never retype them.
- Add `appState.chat.scriptKey` (additive), set on goal-route entry by family.
- **Key chat state per-goal:** `appState.chat.byGoal[goalId] = {messages, scriptIndex, scriptKey}`
  (or equivalent). Switching goals must show that goal's thread, not a shared one. This refines (does
  not rename) the Phase-1 `chat` contract and composes with `scriptKey`.

## Verification (manual click-through — NO TESTS)

### Manual Checks
- Open `prototype/index.html` from disk → `#/goal/CAST-412`: **console clean**; the spine renders
  2c's real step labels (compare against `docs/plan/product-revamp-diecast-stage-models.md`: Shape
  the Problem · Commit & Scope · Design Approach · Build & Ship · Show It's Done); **no `PLACEHOLDER`
  watermark** anywhere.
- **First screenful is WHAT-only**: goal header, spine, nudge, stage artifacts, work stream,
  evidence, decision chips — **zero runs/dispatch/log content** (US3 S1).
- Click each spine step → stage-artifacts zone swaps to that step's familiar surface (requirements
  step → `doc` surface; execution step → ticket-list/`pr-thread`) with its artifacts from `ORG`;
  clicking the current step returns to default. Back/forward and re-render preserve `stageFocus`.
- **PRF1:** the work-happening stream shows RBAC-relevant tickets whose assignees are real
  `ORG.agents` (`entity-creation · api-contractor · migration-author · crud-orchestrator`, `@you`)
  — **not** the generic `FIXTURES.CO/CC/YOU` colleagues.
- E1 panel at `feat-05`: 2–3 real screenshot images (alt + captions from spine), `47 passed / 0
  failed` + coverage delta, `M04 ✓ · S03 ✓ · R02 ⚠ flagged`, `PR #2341` link (no diff on canvas).
  Images load from disk (`file://`) in Chrome.
- One 6A `Decision` pill (superseded GraphQL→REST L1) renders on its owning artifact; clicking opens
  the 6B callout; `DEC-…` id matches the atom.
- CAST-417 L3 renders as a persistent "⚠ needs you" chip at WHAT level; clicking opens
  `EscalationRail` (3 ranked options, nothing pre-selected, evidence pack visible) **without**
  entering the Execution tab (US3 S3).
- "Next ▸" walks `SCRIPTS.feature` start-to-finish: open → Guide nudge → stage navigation beat →
  evidence beat → L3 beat. Narration accumulates in the chat rail; reload resets clean.
- **PRF2:** open `#/goal/CAST-412`, advance the script a couple of steps, switch to another goal,
  switch back → CAST-412's own thread + scenario position is restored (not a shared global thread).
- **Drift spot-check:** every canonical token on screen (CAST-412, M04/S03/R02, 1/3, PR #2341, agent
  slugs) renders from `ORG` — temporarily edit a value in the generator, regenerate, reload, confirm
  the screen changes; **revert**.
- **Generator discipline:** `git diff prototype/data/org.js` shows additive keys only; sections
  outside the additions are byte-identical (F4).

### Success Criteria (binary — every item must pass)
- [ ] `#/goal/CAST-412` renders real 2c vocabulary, no watermark, console clean.
- [ ] First screenful is WHAT-only (no runs/dispatch/log).
- [ ] Spine is a navigator via `drillInto:<step-id>` — **no sixth op added**; dispatcher branch documented.
- [ ] `StageSurface` renders `doc/board/pr-thread/ledger/notebook/memo`; unknown kind → visible placeholder + `console.warn`.
- [ ] **PRF1:** work-stream renders from `goal.work_stream` resolved against `ORG.agents`; kit fixtures gone from this zone.
- [ ] E1 at `feat-05` with real rasters (or `onerror` fallback to 2b thumbnails); PR link only.
- [ ] L1 6A pill + CAST-417 L3 chip + `EscalationRail` (no pre-selection, no Execution-tab entry).
- [ ] `SCRIPTS.feature` walks start-to-finish; **PRF2:** chat keyed per-goal.
- [ ] ORG extended ONLY via the generator; gate passes; diff additive-only; non-batch sections byte-identical.

## Execution Notes
- **Do Step 3.1.1 first** — 3.2/3.4 consume the `execution`/`morph_view` data; the generator gate
  must be green before canvas work depends on it.
- The illustration delegation runs **concurrently** with the canvas work; its output is consumed by
  Step 3.1.5's E1 wiring at the end.
- **Naming:** `StageSurface` PascalCase; CSS `surf-*` (stage surfaces). Keep the inline stylesheet greppable.
- **Spec-linked files:** none — the prototype is greenfield (FR-020); no `/cast-update-spec` action.
- **Failure policy:** retry once with refined instructions; on critical path (it is) a second failure
  → **stop and report**.
