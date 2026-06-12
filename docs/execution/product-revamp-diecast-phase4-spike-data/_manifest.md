# Execution Manifest: Product Revamp Diecast — Phase 4 (Spike + Data-Analysis Flows)

## How to Execute

Each sub-phase runs in a **separate Claude context**. The dependency DAG is
`4.1 ∥ 4.2 → 4.3 → 4.4` with **critical path 4.1 → 4.3 → 4.4**. For each sub-phase:
1. Start a new Claude session (or dispatch a `cast-subphase-runner`).
2. Tell Claude: "Read
   `docs/execution/product-revamp-diecast-phase4-spike-data/_shared_context.md`, then execute
   `docs/execution/product-revamp-diecast-phase4-spike-data/spN_name/plan.md`."
3. After completion, update the Status column below.

**FULL AUTONOMY (owner-approved, end-to-end through Phase 6):** no user questions, no approval gates,
no idle waits; pick the recommended option at every gate and **propagate the directive to any child
agent** (the slop-gate visual/tone checkers in 4.4).

**This phase ships CODE** — all changes land in the single file `prototype/index.html` plus the one
generator-authored ORG extension batch (owned by 4.1). **NO TESTS anywhere** — verification is manual
click-through / static observation only, with non-blocking human-eyeball carry-forwards for
rendered-pixel items (no live browser in autonomous runs).

### Binding constraints (full text in `_shared_context.md`; the runner MUST read it first)
1. **NO TESTS** — no test files/suites/harness/CI; manual click-through only; never flag missing tests.
2. **`file://` legality** — ONE inline `index.html`; no `fetch()`, no local ES-module imports; only
   https CDN imports, classic `<script src>`, relative `<img>`; notebook cells use native `<details>`.
3. **ORG FROZEN (2a FREEZE)** — all data extensions via `generate-org.mjs` (gate re-runs, refuses on
   violation); **never hand-edit `org.js`**; additive keys only; **generator single-owned by 4.1**.
4. **Section-stability (Reconciliation F4)** — ORG sections outside the four declared additions stay
   byte-identical; **no mutation of CAST-461's authored report v1/v2** (`resolved_view` is additive).
5. **Generator serialization (Reconciliation F3)** — 4.1's batch commits `org.js` before Phase 5.0's.
6. **2c stage vocabulary is canonical** (`placeholder:false`) — meter math + all labels/budgets read
   from `stageModels` + `spine_state`; hardcoded vocabulary is a defect.
7. **Closed 5-op vocabulary** — spine-step nav **reuses `drillInto`**; `spike_ref` nav = local
   disclosure; parity reveal = script-patch-driven additive flag; **no sixth op**.
8. **vt- anchors 6×1, shell-zone-wrappers only** — a duplicate name silently kills all transitions;
   the parity layout (4.3) introduces no vt- name.
9. **L3 budget: exactly one hard stop per flow** — spike L3 inert (shown, not resolved); data L3 =
   the one script-wired rail resolution (overlay + receipt, ORG unmutated, reload resets).
10. **Failure policy:** retry once; second failure off the critical path → log gap + continue; on the
    critical path (4.1 → 4.3 → 4.4) → **stop and report**.

### Binding context docs the runner MUST read first
- `docs/plan/2026-06-11-product-revamp-diecast-phase4-spike-data.md` (the plan)
- `docs/plan/product-revamp-diecast-decisions-so-far.md` (run config, NO-TESTS, Phase 4 decision block)
- `docs/plan/2026-06-12-product-revamp-diecast-reconciliation.md` (F2 script-set, F3/F4 generator rules)
- `docs/plan/product-revamp-diecast-stage-models.md` (canonical stage vocabulary — compare against)

## Sub-Phase Overview

| # | Sub-phase | Directory/File | Depends On | Status | Notes |
|---|-----------|----------------|-----------|--------|-------|
| 4.1 | Spike Flow — Timebox Canvas, Memo Surface & Verdict↔Decision Linkage | `sp1_spike_canvas/` | — (Phase 3 done) | Done | Owns the ONE generator batch for **both** Phase 4 goals (thin `execution` ×2, `parity`, `resolved_view`); spike canvas (meter + one card), `memo` kind, E4 + bidirectional `spike_ref`, `SCRIPTS.spike` with parity slot reserved. **Critical path.** |
| 4.2 | Data-Analysis Flow — Pipeline Canvas, Notebook Surface & E5 Rendered Report | `sp2_data_canvas/` | — (Phase 3 done); consumes 4.1's `org.js` at E5/exec wiring | Done | Pipeline canvas, `notebook` kind (native `<details>` cells), data-source list (8% disagreement flagged), **E5 inline-SVG chart** (one renderer, two states), the **one** script-wired L3 resolution, `SCRIPTS.data`. **Parallel with 4.1.** |
| 4.3 | FR-017 Three-Access-Tiers Parity Moment (hosted in the spike flow) | `sp3_parity_moment/` | 4.1 | Not Started | Script-patch-driven parity reveal (`appState.parityOpen`, `parity-*` prefix); ink-dark terminal pane (identity exception); same E4 verdict card in both panes; wires the beat into `SCRIPTS.spike`'s reserved slot. **Critical path.** |
| 4.4 | Four-Family Stitch, Slop Gate & Drift Sweep | `sp4_stitch_gates/` | 4.1, 4.2, 4.3 | Not Started | Stitch all four scripts; **SC-001 + SC-005** met; 4-up glance screenshot; slop gate (`/cast-preso-check-visual` + `/cast-preso-check-tone`) on 4 surfaces; extended drift grep; append the Phase 4 decision summary to `decisions-so-far.md`. **Critical path (terminal).** |

Status: Not Started → In Progress → Done → Verified → Skipped

> **No decision gates in this phase.** Full-autonomy mode resolves all judgment calls; there are no
> human-pause points and no `gate_*` files. (The plan's reserved gates were all upstream — 2c
> sign-off and the Phase 1 morph feasibility gate — and are resolved.)

## Dependency Graph

```
                    ┌──► 4.1  sp1_spike_canvas ───────► 4.3  sp3_parity_moment ──┐
   Phase 3 done ────┤        (+ generator batch:                                 ├──► 4.4  sp4_stitch_gates
                    │         both goals' data)                                  │        (stitch + slop gate
                    └──► 4.2  sp2_data_canvas ──────────────────────────────────┘         + drift sweep)
                             (consumes 4.1's org.js
                              at E5/exec wiring only)

   Critical path: 4.1 ──► 4.3 ──► 4.4
   4.2 runs fully parallel with 4.1 + 4.3; single sync point = the regenerated org.js.
```

## Execution Order

### Parallel Group 1 (run concurrently — see the file-collision note)
- **4.1** `sp1_spike_canvas` — spike canvas + the single generator batch (owns `generate-org.mjs`)
- **4.2** `sp2_data_canvas` — data canvas; all UI work starts immediately against frozen 2a data,
  syncing to 4.1's regenerated `org.js` only at the E5/exec-wiring steps

### Sequential Group 2 (after 4.1)
- **4.3** `sp3_parity_moment` — needs the spike canvas + the `parity` data block from 4.1; runs
  parallel-capable with 4.2

### Sequential Group 3 (after 4.1 + 4.2 + 4.3)
- **4.4** `sp4_stitch_gates` — the stitch/gate/drift pass must see all three prior sub-phases

> **File-collision honesty note (mirrors the Phase 3 split's serial override):** the plan calls 4.1
> and 4.2 "parallel-capable" via disjoint banner sections, and this manifest models them as parallel
> per the mandated DAG. But both edit the **same single file** `prototype/index.html`, and there is
> **no merge mechanism** between two independent runner agents. If 4.1 and 4.2 are dispatched
> concurrently, **serialize their `index.html` writes** (4.1 commits its generator batch + spike
> sections first; 4.2 then layers its disjoint sections) or run them in one session. The generator is
> single-owned by 4.1 regardless, so `org.js` is never written concurrently. The logical parallelism
> (disjoint zones, independent data slices) is real; the physical serialization is a single-file
> artifact constraint, not a deviation from the DAG.

## What This Phase Delivers (high-level plan verification, restated)

- The **spike flow** produces a **verdict artifact (E4) linked from a decision** — `spike_ref`
  navigable both directions in ≤1 click each (FR-016 made visible).
- The **data flow ends in a rendered chart/table, not text** — E5 is a real inline-`<svg>` element
  (US2 S4 / SC verification); prose-only is banned.
- Both families render the **familiar-tool surface** for their step (memo + timebox for spike,
  notebook + chart for analysis); iteration/timebox state shown cleanly (meter + extension chip;
  collapsed-not-deleted cells/versions).
- The **FR-017 three-access-tiers parity moment** lands as a scripted beat in the spike flow.
- **SC-001 + SC-005** fully met: all four families clickable end-to-end from disk; the 4-up glance
  contrast (segment bar / loop band + ↺ / timebox meter / pipeline DAG) is named in <3 seconds.

## Progress Log

<!-- Each runner appends a one-line dated entry after completing its sub-phase. -->
- 2026-06-12 · **4.2 sp2_data_canvas DONE** — data-analysis canvas layered onto the SAME `index.html` (disjoint banner section "4.2 — DATA-ANALYSIS CANVAS"); `org.js`/generator UNTOUCHED (consumed `resolved_view` + thin `execution` read-only). `SpinePipeline` is now a navigator (clickable `drillInto:<data-NN>` nodes); `notebook` `StageSurface` fleshed out (import step → data-source list with the 8% finance-DB-vs-billing-export disagreement in `--warn`; analysis steps → native `<details>` cells + L1/L2 decision callouts); **E5 reworked into the real report** — one hand-authored grouped inline-`<svg>` chart (muted-ink source-of-record vs raspberry disagreeing series, existing tokens only; real `<text>` axes/labels + `<title>`/`<desc>`), data table, provenance-on-demand, v1/v2 chips (v1 always accessible). The **one script-wired L3 resolution**: `resolveDataSource` (script-patch, NOT a 6th op) flips additive `appState.dataResolved` → the E5 re-renders to `resolved_view` + ONE receipt carries `DEC-CAST-461-03`; ORG unmutated (options stay `chosen:false`), reload resets. `SCRIPTS.data` (8 beats, resolution framed as the USER's reply). Static verification: `node --check` clean; 26/26 logic assertions + 23/23 SSR-render assertions pass (preact-render-to-string harness, `/tmp`, uncommitted); drift grep clean (zero revenue figures / source names / `8%` literals in `index.html`); closed 5-op set + 6×1 vt-anchors intact; E5 is inline `<svg>` not `<img>` (source check). No live browser (autonomous run) → chart legibility / two-series contrast / collapse-cell feel carried forward for a human eyeball pass, non-blocking.
- 2026-06-12 · **4.1 sp1_spike_canvas DONE** — generator batch landed for BOTH Phase-4 goals (thin `execution`×2, `parity`, `resolved_view`) with 4 new gate invariants; `org.js` regenerated, gate green, `git diff` additive-only (0 removals vs pre-4.1), F4 holds. Spike canvas: timebox meter + 4 navigable sub-steps + L2-extension chip (over/unparseable guards), single ProbesCard work zone, fleshed-out `memo` `StageSurface`, E4 verdict (card + default-view strip) with bidirectional `spike_ref` local disclosure (no sixth op), L1/L2/L3 chips (NeedsYouChip → inert EscalationRail), `SCRIPTS.spike` (7 beats + reserved parity slot for 4.3). Static verification: `node --check` clean on the module + generator; 19/19 logic assertions pass; closed 5-op set + 6×1 vt-anchors intact; zero hardcoded 2c labels. No live browser (autonomous run) → rendered-pixel items (lightness glance, meter fill, memo layout, flash motion) carried forward for a human eyeball pass, non-blocking.
