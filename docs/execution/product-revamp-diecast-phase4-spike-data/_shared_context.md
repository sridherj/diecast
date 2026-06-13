# Shared Context: Product Revamp Diecast — Phase 4 (Spike + Data-Analysis Flows)

> Read this file at the start of **every** sub-phase session, then execute that sub-phase's
> `plan.md`. The binding constraints below are not optional — they are reconciled cross-phase
> contracts. Violating one is a defect, not a judgment call.

## Source Documents
- **Plan (the source of this split):**
  `docs/plan/2026-06-11-product-revamp-diecast-phase4-spike-data.md`
- **Decisions / run config / cumulative cross-phase contracts:**
  `docs/plan/product-revamp-diecast-decisions-so-far.md`
  (Run Configuration; Owner-Locked Inputs; the Phase 4 decision block; Phase 3 close record)
- **Cross-phase reconciliation (F1–F5; F3/F4 bind this phase's generator batch):**
  `docs/plan/2026-06-12-product-revamp-diecast-reconciliation.md`
- **Canonical stage vocabulary (THE single source — never re-derive):**
  `docs/plan/product-revamp-diecast-stage-models.md`
- **Borderline-call log (append here if a flagged-but-taken taste call ships):**
  `docs/plan/product-revamp-diecast-borderline-calls.md`

## Project Background

Phase 4 completes the four-family thesis. The two remaining workflow families become clickable
end-to-end from the frozen org spine, finishing **SC-001 and SC-005**.

- **Spike family** — `CAST-452 — Does the vendor checkout SDK fit our 200ms p95 budget?`: runs its
  derived `timebox` shape — a **meter spine** (3h budget · 1h40m used, with the L2 extension
  2h→3h recorded on it), a single **probes-tried card** as the work zone, the **memo** familiar
  surface at the conclusion step, and the **E4 verdict card** ("adds 180ms p95 — borderline", ◐
  confidence, 3 deciding data points) whose `spike_ref` linkage to the L3 decision atom is
  navigable in **both directions in ≤1 click each** (FR-016 made visible). This flow also hosts the
  **FR-017 three-access-tiers parity moment** (sub-phase 4.3).
- **Data-analysis family** — `CAST-461 — Which segment drove the Q2 revenue dip?`: runs its derived
  `pipeline` shape — question → data sources → analysis → **E5 rendered visualization** (a real
  data-driven inline-SVG chart + table + provenance, **never prose-only**). The family's single L3
  ("which source do I trust?" — the 8% finance-DB-vs-billing-export disagreement) is the **one
  script-wired rail resolution in the whole prototype**: choosing "show both with a reconciliation
  note" visibly re-renders the headline chart to the reconciled view.

The exploration's build-cost insight governs everything: each canvas is a **projection of `ORG`
through the existing `render(appState)`** — the marginal cost of a family is data plus two deviated
zones. The canvas grammar, component kit, evidence conventions, scripted-flow pattern, and
stage-navigator behavior were all settled in Phases 1–3. Phase 4's net-new work is two thin
data-slice canvases, the fleshed-out `memo`/`notebook` `StageSurface` kinds (Phase 3 shipped thin
versions on purpose), the one hand-authored chart, the parity pane, and two flow scripts.

**Operating mode: HOLD SCOPE.** Plan exactly the five activities the high-level plan bounds Phase 4
to: the spike canvas (timebox meter, memo surface, E4 verdict with `spike_ref`), the spike→decision
wiring (FR-016), the data-analysis canvas (pipeline/notebook surface, data-source list, E5 rendered
report), the FR-017 three-access-tiers side-by-side moment, and each family's scripted chat steps +
single L3 moment. **No colleague surfaces (Phase 5), no entry-screen routing or asset inlining
(Phase 6), no new families, no new ops.**

**FULL AUTONOMY MODE (owner-approved, end-to-end through Phase 6):** never ask the user questions,
never pause for approval gates, never go idle waiting for input. At every decision gate pick the
recommended option and document it. **Propagate this directive verbatim to any child agent you
dispatch** (the slop-gate visual/tone checkers in 4.4).

**No-browser static-verification posture (project-wide, autonomous runs):** autonomous runner
sessions **cannot connect a live browser** (the Claude-in-Chrome extension is not connected — same
as every prior phase). Therefore every "Verification (manual click-through)" item is satisfied by
the strongest **static** evidence available (`node --check` of the extracted module, grep audits,
pure-logic assertion harnesses in `/tmp` that are never committed) **plus** a recorded
**human-eyeball carry-forward** for any item that genuinely needs rendered pixels (glance tests,
chart legibility, motion feel, slop-gate-on-screenshot). Carry-forwards are **non-blocking** — they
never stop the phase; they are logged for a later human pass. This posture is the inherited Phase
1/2a/2b/3 precedent, not a Phase 4 invention.

## BINDING CONSTRAINTS (carried into every sub-phase; each is a defect if violated)

1. **NO TESTS anywhere.** No test files, suites, harness, or CI in any sub-phase. All verification
   is **manual click-through / static observation only** — open `prototype/index.html` from disk,
   click, observe. Fake test-result *content* rendered as prototype data is fine (and none appears
   in these two families anyway — E4/E5 carry their own proof forms). **No review pass may flag
   "missing tests" as a finding.**
2. **`file://` legality — ONE inline file.** Everything ships in the single `prototype/index.html`
   (inline `<style>` + inline module). `file://` blocks `fetch()` and **local ES-module imports**.
   Allowed: **https CDN** imports via the import-map, classic `<script src>` (how `org.js` loads),
   and **relative `<img src>`** (assets under `prototype/assets/`). The notebook surface's
   collapsible cells use **native `<details>`** (`file://`-safe, no JS dependency).
3. **ORG data is FROZEN (2a FREEZE).** All data extensions MUST go through the seeded generator
   `prototype/data/_build/generate-org.mjs`, which re-runs its invariant gate and **refuses to emit
   on violation**. **NEVER hand-edit `prototype/data/org.js`.** Only additive keys; `git diff` must
   show additions only. **The Phase 4 generator batch has a single owner: sub-phase 4.1.** 4.2/4.3
   never touch `generate-org.mjs`.
4. **Section-stability invariant (Reconciliation F4).** All ORG sections **outside** the batch's
   declared additions must be **byte-identical** before/after regeneration. After regenerating, diff
   `org.js` and confirm nothing outside the declared additions (`goals['CAST-452'].execution`,
   `goals['CAST-461'].execution`, `goals['CAST-452'].parity`,
   `goals['CAST-461'].evidence.resolved_view`) changed. **No mutation of the authored report v1/v2
   values** on CAST-461 — `resolved_view` is additive only.
5. **Generator serialization (Reconciliation F3).** Phase 4.1's generator batch commits `org.js`
   **before** Phase 5.0's batch starts. The 4∥5 parallelism applies to everything **except** these
   two generator batches.
6. **2c stage vocabulary is canonical and already in `org.js`** (`placeholder: false`). All
   labels/surfaces/budgets/step-order read from `ORG.stageModels.<family>.steps[]` + each goal's
   `spine_state`. **Any hardcoded stage vocabulary in `index.html` is a defect** — meter math reads
   `timebox.budget` + `spine_state.timebox_used`; a grep for any 2c label string in `index.html`
   must return nothing.
7. **Closed 5-op vocabulary stays closed** (`morph · nudge · promote · drillInto · pin`). Spine-step
   navigation **REUSES `drillInto`** with step-id targets — **NO sixth op**. `spike_ref` navigation
   is **local disclosure** (the existing chip→callout mechanism + scroll/highlight), not a new op.
   The parity reveal is **script-patch-driven** via an additive `appState` flag (e.g.
   `appState.parityOpen`) — no sixth op, no new `drillInto` target class.
8. **vt- anchors live on shell zone wrappers, NEVER on kit components.** The anchor set is **6×1**
   after Phase 3 (`vt-goal-header · vt-chat-rail · vt-nudge-card · vt-receipt-trail · vt-nav-rail ·
   vt-evidence-strip`). A duplicate `view-transition-name` **silently kills all transitions**. The
   parity layout (4.3) must introduce **no** element carrying any vt- name (DevTools count
   unchanged).
9. **L3 budget: exactly one hard stop per flow.** The spike L3 stays an **unresolved stop** (options
   complete but inert — the stop is *shown*, not resolved; Phase 3 decision #10). The data L3 is the
   **one script-wired rail resolution** in the prototype (presentation overlay + one receipt with
   the atom's `decision_id`; ORG unmutated; reload resets). At-rest atoms keep `chosen: false` on
   all options (2a gate invariant untouched).
10. **Failure policy:** retry a failed sub-phase **once** with refined instructions. Second failure
    **off** the critical path → log a gap and continue. Second failure **on** the critical path
    (4.1 → 4.3 → 4.4) → **stop and report**.

## Codebase Conventions

- **Single-file prototype:** `prototype/index.html` — inline `<style>` + inline `<script type=module>`,
  `render(appState) → DOM` (pure render), htm + preact-style components via https CDN import-map.
- **Banner sections:** partition `index.html` by banner-comment sections (the 2b/3 precedent) so the
  growing single file stays navigable and parallel work stays disjoint. Phase 4 owns the
  CAST-452/CAST-461 canvas sections + the parity section. Phase 6 owns packaging.
- **CSS prefixes (greppable):** `surf-*` = stage surfaces (`StageSurface`); `exec-*` = execution
  drill-in; **`parity-*` = the FR-017 parity pane (4.3, new prefix)**. The spike/data canvases stay
  under `surf-*` / existing kit classes — no new prefix in 4.1/4.2 beyond `parity-*` in 4.3.
- **Component naming:** PascalCase — `StageSpine`, `StageSurface`, `EvidenceBlock`, `EscalationRail`,
  `ColleagueCard`, `Decision`, `NudgeCard`, `GuideMark`, `RunNode`, `IterationPanel`.
- **vt- anchors live on shell zone wrappers, NEVER on kit components.**
- **Org-data key convention:** lower_snake_case (e.g. `parity` block keys, `resolved_view`).

## Key File Paths

| File | Role |
|------|------|
| `prototype/index.html` | THE single-file prototype — all four sub-phases edit it (see manifest for parallelism + the file-collision note) |
| `prototype/data/org.js` | Frozen `window.ORG` (classic script). **Generated — never hand-edit.** |
| `prototype/data/_build/generate-org.mjs` | The seeded generator + invariant gate; the ONLY sanctioned path to extend ORG. **Single owner this phase = 4.1.** |
| `prototype/assets/` | Raster assets, loaded via relative `<img src>` + `onerror` fallback (no new rasters expected in Phase 4 — the E5 chart is inline SVG, not a raster) |
| `docs/plan/product-revamp-diecast-stage-models.md` | Canonical stage vocabulary to compare the rendered spine against (spike `timebox`/4 steps `spk-NN`; data `pipeline`/5 steps `data-NN`) |

## Data Schemas & Contracts (copy verbatim into ORG via the generator — 4.1 owns this)

**Stage models (already encoded in `org.js`, `placeholder:false` — READ, do not author):**
- `spike` — shape `timebox`, `timebox:{budget:'3h'}`, **4 steps** `spk-01..04`
  (Frame the Question · Probe Options · Evaluate Findings · Land the Verdict). **E4 home = `spk-04`.**
  `spine_state.timebox_used: '1h40m'`. The `timebox` band must render its **four sub-steps beneath
  the budget meter** (the meter is a wrapper, not the only element — 2c FLAG carried into 2b/Phase 3).
- `data` — shape `pipeline`, **5 steps** `data-01..05` (Import Sources · Tidy & Validate · Transform ·
  Explore (Viz↔Model) · Publish + Provenance). **E5 home = `data-05`.** Inner explore loop is
  intra-`data-04` (NO top-level loop). `spine_state.current: 'data-03'`.
- Each step shape: `{id, label, shortLabel?, does, surface, surfaceWhy, artifacts[], refs[], evidence}`.

**ORG additive extension this phase authors — ONE generator batch, owned by 4.1 (plan contract #5):**
```js
// (a) thin execution — both goals, run list only, NO focus_run tree
goals['CAST-452'].execution = { runs: [{ id, agent, status, when, summary, rework_count }] }  // 1–2 runs
goals['CAST-461'].execution = { runs: [{ id, agent, status, when, summary, rework_count }] }  // 1–2 runs

// (b) FR-017 terminal text — lives in the spine so skill names + artifact ids can't drift
goals['CAST-452'].parity = { command, transcript: [ ...lines... ], artifact_id, caption }

// (c) reconciled-chart series — additive on the evidence payload; v1/v2 report semantics UNTOUCHED
goals['CAST-461'].evidence.resolved_view = { series: [ ...both sources... ], reconciliation_note }
```
**New generator invariants** (added alongside the data): `parity.artifact_id` resolves to the E4
verdict artifact; `transcript` is non-empty and contains the artifact line; `resolved_view.series`
covers **exactly** the two disagreeing sources (finance DB vs billing export); every thin
`execution.runs[].agent` resolves in `ORG.agents`. Regenerate → gate green → `git diff` additive-only
→ F4 byte-identical outside the four declared keys.

**Decision atoms (already in ORG, PB-05 schema + `diff`):** each Phase 4 goal has 5–8 atoms with
**exactly one L3**. Spike L3 = the vendor-SDK borderline go/no-go (options: proceed / self-host /
renegotiate). Data L3 = the 8% source disagreement (options: source-of-record / show both with
reconciliation note / flag for analyst review). L3s carry 3 ranked options, **none `chosen`**, plus
an evidence pack. The spike's 2h→3h timebox extension is an **L2** atom. `spike_ref` integrity is
**bidirectional and gate-enforced** (the E4 verdict references the atom that references it).

**E4 / E5 evidence data shapes (locked in 2b; render via `EvidenceBlock {kind, data}`):**
- **E4 (verdict card):** one-line answer + confidence glyph (◐ = M, never a percentage) + the 3
  deciding data points + the `spike_ref` link. **Never a bare pass state.**
- **E5 (rendered report):** the headline chart is a **pure function of the ORG series → inline SVG**
  (the M9 burndown idiom: hand-authored axes, bars, real `<text>` labels, `<title>`/`<desc>` for
  a11y; existing tokens only — ink/muted for the source-of-record series, raspberry accent for the
  disagreeing series + annotations); the data table beneath; provenance disclosure (collapsed by
  default); report version chips (v1 accessible, never deleted — FR-007). One renderer, two states
  (at-rest ◐-flagged vs `resolved_view`), verifiable in `#/kit`.

**Components consumed AS-IS (Phase 2b/3 — pure props, never modified here):** `StageSpine {spine}`
(the `timebox` and `pipeline` shapes **already exist**; the spike meter reads
`spine.timebox.{budget, used}`); `StageSurface({step, artifacts})` keyed on `step.surface`
(`doc | board | pr-thread | ledger | notebook | memo` — Phase 4 **fleshes out** the thin `memo` and
`notebook` kinds in place, no interface change); `EvidenceBlock {kind, data}` (E4/E5 branches);
`ColleagueCard {agent, density}` (line density on probe attribution); `Decision {atom, layer}`
ladder; `NudgeCard {nudge}`; `EscalationRail`; `GuideMark` + Guide voice; `RunNode`/`IterationPanel`
(thin exec tab only — run list, **no dispatch tree**, the single `RunNode` call-site rule preserved).

**Scenario engine (Phase 1, unchanged API):** `{narration, patch, transition?}` steps + `advance()`,
index at `appState.chat.scriptIndex`. Phase 4 adds `SCRIPTS.spike` (~6–7 beats) and `SCRIPTS.data`
(~7 beats), keyed on goal-route entry via `appState.chat.scriptKey` (the Phase 3 contract, **per-goal
per PRF2**). After Phase 4, `SCRIPTS = {feature, debug, spike, data}` — the four-**family** set is
**closed** (Reconciliation F2; demo-arc keys like Phase 5's `SCRIPTS.hiring` are additive; final
closure at 5 keys in Phase 6).

**vt- anchors (6×1, on shell zone wrappers):** `vt-goal-header · vt-chat-rail · vt-nudge-card ·
vt-receipt-trail · vt-nav-rail · vt-evidence-strip`. **Motion tokens:** `--morph-duration: 350ms`,
`--ease-morph`, `--motion-fast: 120ms`, reduced-motion fade ≤200ms. A duplicate
`view-transition-name` silently kills the whole transition.

**Contracts this phase EXPORTS (Phases 5/6 consume):** the complete `SCRIPTS = {feature, debug,
spike, data}`; the fleshed `StageSurface` kinds `memo` and `notebook`; the **E5 chart idiom**
(data-driven inline-SVG chart inside `EvidenceBlock`'s E5 branch); the **parity-pane pattern**
(`parity-*` prefix, script-patch-driven reveal — a named beat for Phase 6's walkthrough); the ORG
additive extensions (thin `execution` ×2, `parity`, `resolved_view`) with their new gate invariants.

## Pre-Existing Decisions (from the plan's Decisions Made Autonomously + Run Config)

- **Plan review: SKIPPED** per the owner-approved run config (cross-phase reconciliation only;
  Phase 1/2a/2b/2c/3 precedent). Re-run manually via `/cast-plan-review` against the plan file if
  wanted. This split therefore does **not** dispatch `/cast-plan-review`, and inserts **no**
  plan-review or reconciliation sub-phases (NO REVIEWS).
- **NO human-checkpoint gates** in any sub-phase file (FULL AUTONOMY). There are **no decision gates**
  in this phase.
- Sub-phase split `4.1 ∥ 4.2 → 4.3 → 4.4` (Decision 1); one generator batch owned by 4.1 (Decision 2);
  the E5 chart is hand-authored data-driven inline SVG, not a raster (Decision 3); the spike L3 stays
  an unresolved stop and the data L3 is the one script-wired resolution (Decision 4); the reconciled
  chart ships as additive `evidence.resolved_view`, not a re-read of v1/v2 (Decision 5); scripted L3
  resolution = presentation overlay + one receipt, ORG unmutated (Decision 6); the parity terminal
  pane renders ink-dark as a deliberate, contained identity exception (Decision 7); parity beat sits
  after the verdict beat, before the L3 stop (Decision 8); parity reveal is script-patch-driven via
  an additive flag, no sixth op (Decision 9); thin exec (run list, no tree) for both goals (Decision
  10); `spike_ref` navigation = local disclosure, not an op (Decision 11); the FR-017 chat tier is
  the existing persistent rail, no fake animation (Decision 12); the L2 timebox-extension chip renders
  on the meter (Decision 13); `cast-plan-review` auto-dispatch skipped (Decision 14).

## Relevant Specs

`docs/specs/_registry.md` — all seven specs govern the **cast-server runtime**. Per **FR-020 the
prototype is greenfield**: no spec applies, none is contradicted, and **no `/cast-update-spec`
action** is in scope for this phase. The FR-017 parity pane *depicts* the real `agents/cast-*.md` →
`bin/generate-skills` → terminal-skill substrate as **fake transcript data** — reference material
rendered as prototype content, not a spec'd surface being modified. **No specs cover files in this
plan.**

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|-----------|------|-----------|--------|-------------------|
| 4.1 Spike Canvas + Generator Batch (`sp1_spike_canvas`) | Sub-phase | Phase 3 done | 4.3, 4.4; unblocks 4.2's sync point | **4.2** (disjoint sections; generator single-owned by 4.1) |
| 4.2 Data-Analysis Canvas (`sp2_data_canvas`) | Sub-phase | Phase 3 done; consumes 4.1's regenerated `org.js` at E5/exec wiring | 4.4 | **4.1** (disjoint sections) |
| 4.3 FR-017 Parity Moment (`sp3_parity_moment`) | Sub-phase | **4.1** (spike canvas + `parity` block) | 4.4 | **4.2** |
| 4.4 Stitch, Slop Gate & Drift Sweep (`sp4_stitch_gates`) | Sub-phase | **4.1 + 4.2 + 4.3** | — | None |

> **Critical path: 4.1 → 4.3 → 4.4.** 4.2 runs fully parallel with 4.1+4.3; its only sync point is
> consuming the regenerated `org.js` (for `resolved_view` + thin exec) at its E5/exec-wiring steps.
>
> **File-collision honesty note (mirrors the Phase 3 split):** the plan calls 4.1 and 4.2
> "parallel-capable" via disjoint banner sections, and this manifest models them as parallel per the
> mandated DAG. But both edit the **same single file** `prototype/index.html`, and there is **no
> merge mechanism** between two independent `cast-subphase-runner` agents. If the orchestrator
> dispatches 4.1 and 4.2 as concurrent independent runners, **serialize their `index.html` writes**
> (4.1 commits its generator batch + spike sections first, then 4.2 layers its disjoint sections) or
> run them in one session. The generator is single-owned by 4.1 regardless, so the `org.js` write is
> never concurrent. The logical parallelism (disjoint zones, independent data slices) is real; the
> physical serialization is a single-file artifact, not a plan change.
