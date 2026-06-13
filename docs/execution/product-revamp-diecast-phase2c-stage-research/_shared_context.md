# Shared Context: Product Revamp Diecast — Phase 2c Stage-Model Research

> Read this file at session start **before** executing any sub-phase. It carries the binding
> constraints, the contracts 2c must honor, and the cross-phase decisions every 2c sub-phase
> depends on. This is a DRY reference — sub-phase files cite it, they do not re-inline it.

## RUN MODE — FULL AUTONOMY (owner-approved)

**Never ask the user questions, never pause for approval gates, never go idle waiting for
input.** At any decision gate, pick the recommended option and document it inline. The one
plan-reserved human gate for this phase (owner sign-off on the four spines) is **replaced by
the written self-evaluation gate** in sp3 (the five-test rubric + per-family verdict, loop-once
rework on failure). **Propagate this autonomy directive verbatim** into any child agent you
dispatch (e.g. `/cast-web-researcher`).

## Source Documents (READ FIRST, in this order)

1. **`docs/plan/product-revamp-diecast-decisions-so-far.md`** — run configuration, owner-locked
   inputs, the NO-TESTS rule, every cross-phase contract, and the Reconciliation Outcome
   (F1–F5). Read the **Phase 1**, **Phase 2a**, and **Phase 2c** sections in particular.
2. **`docs/plan/2026-06-11-product-revamp-diecast-phase2c-stage-research.md`** — the Phase 2c
   detailed plan this execution directory splits. Canonical source for any ambiguity.
3. (Reference) **`docs/plan/2026-06-12-product-revamp-diecast-reconciliation.md`** — the COHESIVE
   verdict and finding **F1** (the stageModels encoding-ownership fix, summarized below). Read
   F1 before sp3/sp4.
4. (Evidence, cheap, already curated) `exploration/research/03-family-canvases-evidence.ai.md`
   §"Expert-Practitioner Insights" + §"The Four Family Blueprints" + Consolidated Sources /
   Reference-Link Map; and `exploration/research/05-decisions-autonomy.ai.md` Lens 1. (Paths are
   relative to the goal artifacts dir `/data/workspace/diecast/goals/product-revamp-diecast/`.)

## Project Background

Phase 2c is a **research spike, not code**. It derives the real per-family stage vocabulary for
the four workflow families — **`feature` · `debug` · `spike` · `data`** — from how the *best
practitioners in each category actually work*, and captures it as the single canonical
stage-model note that Phases 3–4 build their canvases from and Phase 2a encodes into the org
data. The exploration's illustrative steps (feature: prototype-with-UI-choices → locked design →
eng design; debug: repro · RCA · evidence · fix · tests) are **explicitly dropped as
placeholders** by owner directive ("those are not the right steps — we have to explore online
and come up with the right mental models"). Every derived step must pass the test: *would a top
practitioner in this category recognize this as their actual workflow?*

Phase 2c is on nobody's critical path for chrome, but it **gates every canvas build**: Phase 3
cannot author the feature/debug canvases until the spines are derived, and 2a's `stageModels`
region stays watermarked-placeholder until 2c's encode step lands.

## BINDING CONSTRAINTS (apply to every sub-phase — non-negotiable)

### NO TESTS anywhere
This deliverable has **no concept of tests** — no pytest, no unit/integration/e2e suites, no
test harness, no CI, no test files of any kind, in any sub-phase. All verification is **manual
file-inspection** (does the note have every required section/field?) plus, for sp4 only, the
**self-validating generator's invariant gate** (which runs *inside* `generate-org.mjs` before it
writes `org.js` and refuses to emit on violation — that gate is **NOT a test file**) and a
`node -e` / `jq` **JSON-parse check** on the encoding block. No reviewer or runner may flag
"missing tests" as a finding. (Fake practitioner-step *content* is data, not tests.)

### Derive-first, compare-after (the anti-anchoring protocol)
The dropped placeholder steps and Phase 1's watermarked stub labels **must NOT be used as search
queries or candidate lists** during sp1, and must NOT seed sp2's derivation. Gather evidence
fresh in sp1; derive spines purely from that evidence in sp2; **only then** diff against the
dropped placeholders and record the diff in the dropped-placeholder ledger. The ledger existing
(showing derivation preceded comparison) is the audited proof the protocol was followed.

### Practitioner-account source requirement (the owner's failure mode, mechanized)
The owner's directive fails exactly when the evidence base is built from abstract methodology
texts / consulting lifecycle diagrams. **≥1 hands-on practitioner account per family** (a
practitioner describing their *own* process) is **mandatory, not advisory**. Mark every
reference `practitioner-account` / `tool-documented-workflow` / `methodology-text`. Reject SEO
listicles and consultant lifecycle diagrams.

### `file://` plain-JSON constraint (Phase 1 hard contract)
The prototype opens from disk. Org data ships as a **classic script** `prototype/data/org.js`
setting `window.ORG = Object.freeze({...})` — **never** `fetch()`, never local ES-module
imports. Therefore the `stageModels` encoding 2c produces must be **plain-JSON-compatible data**:
no functions, no module imports, no computed values — only objects, arrays, strings, numbers,
booleans, `null`. The encoding block must `JSON.parse` cleanly (sp4's gate).

## Reconciliation Outcome — Finding F1 (binding for sp3/sp4)

**F1 (HIGH) — stageModels encoding ownership.** The `org.js` `stageModels` rewrite is owned by
**2c itself**, executed **via 2a's generator** (`prototype/data/_build/generate-org.mjs`),
scheduled **after 2a.1 (the generator exists) and before Phase 3 dispatch**. 2a ships
`stageModels` with `placeholder: true` content; nobody else performs the rewrite. This is why
this execution plan **splits the original 2c.3 into two sub-phases**:

- **sp3 (`2c.3 authoring`)** — writes the canonical markdown note + appends to decisions-so-far.
  **No dependency on Phase 2a.** Runs as soon as sp2 is done.
- **sp4 (`2c.4 encode`)** — the generator edit + `org.js` re-emit + invariant-gate re-run.
  **Gated on sp3 AND on the external Phase 2a artifacts** `prototype/data/_build/generate-org.mjs`
  and `prototype/data/org.js` existing (produced by a SEPARATE parallel orchestrate run). The
  orchestrator **parks sp4** until those files exist, polling Phase 2a. sp4 **must complete
  before Phase 3 dispatch.**

The `stageModels` region is the **one standing exception** to 2a's post-freeze policy.

## Contracts 2c MUST honor (copy verbatim — do not rename keys)

### `appState.spines` v1 contract (Phase 1; keys extend-only, never renamed)
`appState.spines.<family> = { placeholder, shape, steps: string[], current, iter?:{current,
budget} }`. Phase 1 labels carry `placeholder:true` + a visible PLACEHOLDER watermark. 2c's
output is what flips that flag to `false`. **`steps` stays a flat `string[]` at the appState
level** — rich per-step data lives only in the org data (`stageModels`). At boot,
`appState.spines.<f>.steps` is derived via `stageModels.<f>.steps.map(s => s.shortLabel ?? s.label)`.

### `stageModels.<family>` field contract (THE 2a coordination point; plain JSON)
```js
// org data (window.ORG.stageModels) — canonical, authored by 2c (sp3), encoded by 2c (sp4)
stageModels: {
  feature: {
    shape: 'segments', progression: 'linear-reentrant',   // illustrative values
    steps: [
      { id: 'feat-01', label: '…', shortLabel: '…',        // shortLabel optional, required if label > 18 chars
        does: 'one-line practitioner description',
        surface: 'doc', surfaceWhy: 'one-line rationale',
        artifacts: ['…'],                                  // >= 1
        refs: ['shape-up'],                                // >= 2 keys into the references table
        evidence: null },                                  // exactly one step per family carries 'E1'..'E5'
      // … 4–7 steps
    ]
  },
  debug: { shape: 'loop',     loop:    { over: ['dbg-02','dbg-03','dbg-04'], budget: 3 }, steps: [/*…*/] },
  spike: { shape: 'timebox',  timebox: { budget: '3h' },                                 steps: [/*…*/] },
  data:  { shape: 'pipeline',                                                            steps: [/*…*/] },
}
```
Field names here are **the contract** — 2a/2c must not rename them, and may extend. The block
fixes the **shape**; the step *content* is sp2's derived output.

### Family keys & step-id grammar (locked)
- Family keys exactly **`feature | debug | spike | data`** — matches Phase 1's `appState.family`
  values and the `morph:<family>` op vocabulary. **`data`, not `analysis`.** No "bug-fix family",
  no "analysis family" as keys.
- Step ids **`<family>-NN`**: `feat-01`, `dbg-01`, `spk-01`, `data-01`. Labels Title Case.

### Locked spine shape variants (from 2b's component picks — validate or *flag*, never silently change)
- `feature` = **`segments`** (1B labeled segment bar, `progression: 'linear-reentrant'`)
- `debug` = **`loop`** (2B staged band + ↺ iter counter; `loop:{over,budget}`)
- `spike` = **`timebox`** (budget meter; `timebox:{budget}`)
- `data` = **`pipeline`** (DAG)

If research genuinely contradicts a shape (e.g. spike needs visible sub-steps not just a meter),
**do NOT redesign** — record a "spine-variant revision proposed" flag in the note's Suggested
Revisions channel for 2b/Phase 3 and proceed with the best fit.

### Familiar-tool working surface set (owner-locked; map every step to one, or flag a new one)
`doc · board/ticket list · PR-thread/report · investigation ledger · notebook+chart ·
memo+timebox`. Every derived step maps to one of these via its `surface` field, or explicitly
raises a new-surface flag (never a silent invention).

### Canvas-anatomy principle
Each stage owns its artifacts; the spine is a navigator. **Every derived step must name ≥1
concrete artifact** it owns (`artifacts` field).

### E1–E5 evidence catalog (owner-blessed; each gets exactly one home step)
- **E1** acceptance panel → `feature`
- **E2** confirm/refute ledger + **E3** red→green repro → `debug`
- **E4** verdict card w/ `spike_ref` → `spike`
- **E5** rendered report + provenance → `data`

Each treatment is annotated as the `evidence` value on exactly one step in its family's spine.

## Renderability bounds (spine-band realities, not taste — enforced in sp2)
- **4–7 steps per family.**
- Labels that fit a segment bar: **≤ ~18 chars**; if the honest practitioner name is longer,
  keep the full name in `label` and add a **`shortLabel` ≤18 chars** (the band renders `shortLabel`).
- Each step owns ≥1 artifact (canvas anatomy).
- E1–E5 each get a named home step in their family.

## The five-test practicality rubric (every candidate step must pass all five)
1. **Verb+artifact test** — names something a practitioner *does* yielding a tangible artifact
   ("Get a failing repro", not "Analysis").
2. **Recognition test** — appears (under any name) in **≥2 independent sp1 sources**; cite both.
3. **Hole test** — a top practitioner would notice its *absence* from the spine.
4. **Tidy-label kill test** — if it only appears in textbooks/consulting frameworks and never in
   practitioner accounts, **kill or rename it** (the owner's directive, mechanized).
5. **Familiar-surface test** — maps to a surface in the locked working set, or raises an explicit
   new-surface flag for 2b/Phase 3 (never a silent invention).

## Loop-vs-progress (decide per family from evidence, not symmetry)
Debug expected to confirm as a loop (hypothesis↔experiment↔observation); feature
linear-but-re-entrant; spike a single timebox; data likely an inner transform↔visualize loop
inside a linear question→communicate frame — **but the research decides.** Record which steps the
loop iterates over (`loop.over`) — this feeds Phase 1's debug `iter` counter semantics.
**Asymmetry is a feature (SC-005):** if families land on different step counts and loop shapes,
that is the design working. Reject any pressure to make the four spines symmetric.

## Key File Paths

| File | Role |
|------|------|
| `docs/execution/product-revamp-diecast-phase2c-stage-research/sp1_evidence_base/evidence-base.md` | sp1 scratch deliverable — per-family evidence base (≥3 refs/family, source-quality marks). Feeds sp2/sp3. |
| `docs/execution/product-revamp-diecast-phase2c-stage-research/sp2_spine_derivation/spine-derivation.md` | sp2 scratch deliverable — derived spine tables + rubric scoring + dropped-placeholder ledger + loop/progress calls. Feeds sp3. |
| `docs/plan/product-revamp-diecast-stage-models.md` | **THE canonical deliverable** (sp3) — single source of stage vocabulary. Does not exist yet. |
| `docs/plan/product-revamp-diecast-decisions-so-far.md` | Cross-phase decision log; sp3 appends the Phase 2c spine-labels + flags section (~10–20 lines). |
| `prototype/data/_build/generate-org.mjs` | **External, owned by Phase 2a.** sp4 edits ONLY its stage-model section. Does not exist until 2a.1 lands. |
| `prototype/data/org.js` | **External, owned by Phase 2a.** sp4 re-emits it via the generator. Does not exist until 2a.1 lands. |

## Pre-Existing Decisions (constrain implementation)
- **Stage-model note location** `docs/plan/product-revamp-diecast-stage-models.md` — a design
  source-of-truth doc, alongside the phase plans (not shipped prototype data).
- **Encoding split:** rich step objects live only in `stageModels` (org data); `appState.spines`
  keeps Phase 1's `steps: string[]` via `map`. (Phase 1 contract: keys extend, never rename.)
- **Owner sign-off → written self-evaluation** (rubric table + per-family verdict, loop-once
  rework on failure).
- **Targeted scan over full `/cast-web-researcher` fan-out** as the default research method
  (escalation only on a thin family — <3 quality refs).
- **Step-count bound 4–7 and ≤18-char shortLabel convention** — derived from spine-band
  renderability; honest longer names keep their full form in `label`.
- **Plan review skipped** per run config (Phase 1/2a/2b precedent). No `/cast-update-spec` —
  FR-020 greenfield, no spec applies.

## Relevant Specs
No specs cover files in this plan. `docs/specs/_registry.md`'s 7 specs all govern the
**cast-server runtime**; the prototype is greenfield (FR-020). None apply, none contradicted. No
`/cast-update-spec` action. The stage-model note itself is the canonical definition for the
prototype's scope.

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|-----------|------|-----------|--------|-------------------|
| sp1 — Practitioner Evidence Base (2c.1) | Sub-phase | None (Phase 1 contracts absorbed) | sp2 | None (4 family *scans* parallel internally) |
| sp2 — Spine Derivation & Pressure-Test (2c.2) | Sub-phase | sp1 | sp3 | None |
| sp3 — Canonical Note + Self-Eval (2c.3 authoring) | Sub-phase | sp2 | sp4 | None — **no Phase 2a dependency** |
| sp4 — Encode into org.js (2c.4 encode) | Sub-phase | sp3 **AND** external 2a artifacts (`generate-org.mjs` + `org.js` exist) | Phase 3 dispatch | None — orchestrator parks until 2a artifacts exist |

**Critical path:** strictly sequential `sp1 → sp2 → sp3 → sp4`. The four family scans inside sp1
run in parallel. sp4 carries the **one external gate** (Phase 2a's generator artifacts).
