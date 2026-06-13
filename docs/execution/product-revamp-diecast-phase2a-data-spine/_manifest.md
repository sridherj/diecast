# Execution Manifest: Product Revamp Diecast — Phase 2a Data Spine

## How to Execute

Each sub-phase runs in a **separate Claude context**. The three sub-phases are **strictly
sequential** (2a.1 → 2a.2 → 2a.3) — never run them in parallel. For each sub-phase:
1. Start a new Claude session (or dispatch a `cast-subphase-runner`).
2. Tell Claude: "Read `docs/execution/product-revamp-diecast-phase2a-data-spine/_shared_context.md`,
   then execute `docs/execution/product-revamp-diecast-phase2a-data-spine/spN_name/plan.md`."
3. After completion, update the Status column below.

**Binding constraints (carried in `_shared_context.md` and every sub-phase file):**
- **NO TESTS** anywhere — no test files, suites, harnesses, or CI. Verification is manual
  click-through only, plus the self-validating generator's invariant gate (which is **NOT** a
  test file).
- **`file://` legality** — no `fetch()`, no local ES-module imports; org data ships as a
  classic script `prototype/data/org.js` setting `window.ORG = Object.freeze({...})`. Only
  https CDN import-map imports, classic `<script src>`, relative `<img>`.
- **Prototype code root** `/home/sridherj/workspace/diecast/prototype/`. Phase 1 is BUILT
  (`index.html`, appState v1, 5-op dispatcher, scenario engine, View-Transitions morph
  PASSED). Extend additively; never regress Phase 1 contracts.
- **F4 single-source rule** — the generator gate is the single source of `org.js`; later
  phases extend it additively only.
- Binding context docs the runner MUST read first:
  `docs/plan/product-revamp-diecast-decisions-so-far.md` (run config, owner-locked inputs,
  NO-TESTS rule, cross-phase contracts, Reconciliation Outcome F1–F5) and
  `docs/plan/2026-06-11-product-revamp-diecast-phase2a-data-spine.md`.

## Sub-Phase Overview

| # | Sub-phase | Directory/File | Depends On | Status | Notes |
|---|-----------|----------------|-----------|--------|-------|
| 1 | Schema Lock & Self-Validating Generator (2a.1) | `sp1_schema_lock_generator/` | — | Done | Generator + in-code invariant gate; schema-complete content-thin `org.js` (commit fb19586) |
| 2 | Author the Org — Goals, Decisions, Roster, Hiring, Layer-2 (2a.2) | `sp2_author_org/` | 1 | Done | Content-complete: 21 atoms (1 L3/goal), 12 agents, 6 candidates, 12 contracts; gate green (commit 87f3a32) |
| 3 | Wire, Sweep, Freeze (2a.3) | `sp3_wire_sweep_freeze/` | 2 | Done | Wired into `index.html`, appState v1.1, drift-clean (#/kit exception only), FROZEN; 2c vocab merged (commit 5d1341e) |

Status: Not Started → In Progress → Done → Verified → Skipped

No decision gates: all judgment-call gates were resolved at planning time under full autonomy
(see the plan doc's "Decisions Made Autonomously"). No parallel groups — strictly sequential.

## Dependency Graph

```
sp1 (2a.1 schema + self-validating generator)
   │
   ▼
sp2 (2a.2 author content — gate stays green)
   │
   ▼
sp3 (2a.3 wire into index.html, drift sweep, FREEZE)
   │
   └─► (downstream) 2b swaps fixtures for the spine after freeze;
       2c rewrites the stageModels region later via the generator;
       Phases 3/4/5 consume the frozen spine.
```

**Critical path within the phase:** strictly sequential — 2a.2 needs 2a.1's invariant gate to
author against; 2a.3 needs full content to sweep. Total 1.5–2 sessions (matches the
high-level 0.5–1 day estimate).

## Execution Order

### Sequential Group 1
1. **sp1 — Schema Lock & Self-Validating Generator (2a.1)** (~0.5 session)

### Sequential Group 2 (after Group 1)
2. **sp2 — Author the Org (2a.2)** (~1 session — the bulk)

### Sequential Group 3 (after Group 2)
3. **sp3 — Wire, Sweep, Freeze (2a.3)** (~0.5 session)

## Key Risks & Mitigations (from the plan)

| Risk | Impact | Mitigation |
|------|--------|------------|
| Phase 1 execution hasn't landed when 2a.3 starts | Med | 2a.1–2a.2 have zero runtime dependency; 2a.3 degrades to a wiring patch spec against Phase 1's contracted shapes, folded in when `index.html` exists |
| 2c's derived vocabulary changes step counts, breaking `spine_state.current`/artifact refs | Med | Step-id indirection + the generator's referential refusal; 2c regenerates via the generator, so the gate re-runs then |
| Hand-tuned prose drifts canonical tokens inside `org.js` itself | Med | Canonical strings are named constants, interpolated into prose templates — never retyped |
| Spine over-grows (audit theater) | Med | Generator hard-caps: 5–8 atoms/goal, exactly 1 L3, 6 candidates, 12 agents, 12 contracts |
| 2b's fixture shape drifts (planned in parallel) | Low–Med | Fixture shape locked in decisions-so-far; 2a.3 wiring is the reconciliation checkpoint |
| E1 screenshot refs point at images Phase 3 owns | Low | Refs + alt + captions give Phase 3 a work-list; Phase 6 drift sweep catches dead refs |
| faker version drift | Low | Exact version pin + committed output; the committed file is canon |

## Plan Review

**Skipped** per the run configuration in `product-revamp-diecast-decisions-so-far.md`
("Plan review: skipped — cross-phase reconciliation only", owner-approved; consistent with
Phase 1/2b/2c precedent). See `_review_summary.md`. Rerun manually via `/cast-plan-review`
against any sub-phase file if wanted.

## Progress Log

- **2026-06-12 — sp1 Done** (run_20260611_220551_2354c0, commit fb19586): seeded generator + in-code invariant gate; content-thin `org.js` (11 keys, `window.ORG=Object.freeze`, deterministic). Verified: byte-identical re-run, refuse-on-second-L3, 11 keys, zero require/import.
- **2026-06-12 — sp2 Done** (run_20260611_223231_37184d, commit 87f3a32): content-complete via generator constants only (F4). 21 atoms (6/5/5/5, exactly 1 L3/goal), 4 locked L3 beats, morph atom DEC-CAST-412-03, 1 superseded L1 pair, 12 agents (crud-orchestrator 99.9%/505/2; feature roster aggregate generator-tied to 99.4%/312), 6 candidates, 12 layer-2 contracts, 6-project portfolio, 9-ticket board, E1–E5 payloads, thin US7. Verified: gate green, 0 lorem/TODO, deterministic, 1 em dash (Phase-1 nudge kept verbatim).
- **2026-06-12 — sp3 Done** (run_20260611_225407_8becfb, commit 5d1341e): `<script src="data/org.js">` before the inline module + missing-ORG error banner; appState v1.1 (`org` key, four families derived from `stageModels`+`spine_state`, receipts gain `decision_id`); route guard for all four goal ids; morph receipt derived from DEC-CAST-412-03. Drift grep clean — all canonical hits confined to the sanctioned 2b `#/kit` fixture block (retires at 2b's data swap). FROZEN: `meta.frozen_at='2026-06-11T18:00:00.000Z'` (constant), byte-identical re-run; decisions-so-far 2a appendix appended. **2c's `stageModels` rewrite landed concurrently** via the same generator (`placeholder:false`, real per-family vocabulary) — F1 satisfied ahead of Phase 3. **PROVISIONAL human-eyeball carry-forward** (V1/V2/V3 click-through): no browser in autonomous run — static checks all passed; visual confirmation deferred to a human, non-blocking.

**Phase 2a: COMPLETE.** Frozen spine is the single source for Phases 3/4/5; Phase 3 is unblocked.
