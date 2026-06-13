# Execution Manifest: refine-req-v3-phase1 (Validate the Maker & the Anchor Backbone)

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:
1. Start a new Claude session.
2. Tell Claude: "Read `docs/execution/refine-req-v3-phase1/_shared_context.md` then execute
   `docs/execution/refine-req-v3-phase1/spN_name/plan.md`".
3. After completion, update the Status column below.

sp1a and sp1b are **independent and parallel** (disjoint output dirs) — run them in either order
or simultaneously. The orchestrator **stops at G1**, a human decision gate.

## Sub-Phase Overview

| # | Sub-phase / Gate | Directory/File | Depends On | Status | Notes |
|---|------------------|----------------|-----------|--------|-------|
| 1a | Maker Quality Ceiling (proven by hand) | `sp1a_maker_quality/` | — | Done | `BEATS DETERMINISTIC: yes` (bug_fix strong, new_initiative qualified); 4 audits PASS; checker anomaly→Phase-4a input |
| 1b | Quote-Anchored Backbone Survival | `sp1b_anchor_survival/` | — | Done | `BACKBONE HOLDS: confirmed`; zero new orphans; reanchor live; diff deterministic; zero-`id` PASS |
| G1 | Combined Phase-1 Spike Gate → Phase 3 entry | `gate_1_phase1_combined.md` | 1a, 1b | Done | **Option A — GO-TO-PHASE-3** (owner, 2026-06-12). Both spikes green; verdict in `spikes/PHASE1-GATE.md` |

Status: Not Started → In Progress → Done → Verified → Skipped

The **G1** row (G-prefix ID, `gate_` file prefix) pauses the orchestrator for a human decision.
There are no skippable sub-phases in Phase 1 — both spikes feed the single combined gate.

## Dependency Graph

```
  sp1a (maker quality ceiling) ──┐
                                 ├──► G1 (combined gate → PHASE1-GATE.md) ──► Phase 3 / surface-to-owner
  sp1b (anchor survival)     ────┘
        (no dependency between 1a and 1b; 1b may reuse 1a HTML opportunistically,
         but must not wait — it hand-crafts a minimal varying pair otherwise)
```

**Parallel-safety check:** sp1a writes only under `spikes/1a/`; sp1b writes only under
`spikes/1b/` (plus a throwaway scratch DB inside `spikes/1b/`). **No shared files** — safe to run
simultaneously.

## Execution Order

### Parallel Group 1 (run simultaneously)
- **1a.** Maker Quality Ceiling — `sp1a_maker_quality/`
- **1b.** Quote-Anchored Backbone Survival — `sp1b_anchor_survival/`

### Decision Gate (after both 1a and 1b complete)
- **G1.** Combined Phase-1 Spike Gate — `gate_1_phase1_combined.md`
  - Aggregate both `spike-results.md` into `spikes/PHASE1-GATE.md`.
  - Decide **GO-TO-PHASE-3** (both green) vs **surface-to-owner** (a revisit-trigger fired).
  - Orchestrator **stops** here for the human decision.

## Progress Log

<Update after each sub-phase / gate decision.>
- 2026-06-12: sp1a Done — maker BEATS DETERMINISTIC for bug_fix (structural: baseline drops 5/7 ids) + new_initiative (qualified, hierarchy/scannability); all 4 audits PASS; checker necessary-but-not-sufficient anomaly recorded as Phase-4a input.
- 2026-06-12: sp1b Done — BACKBONE HOLDS: confirmed; zero new orphans for surviving content; cast-comment-reanchor dispatched live (verbatim relocates, FR-019 backstop clean); diff_blocks deterministic; zero-`id`/FR-028 PASS on both renders; no revisit-trigger.
- 2026-06-12: G1 reached — both spikes green (Option A). Orchestrator STOPPED for owner decision.
- 2026-06-12: G1 DECIDED by owner — **GO-TO-PHASE-3** (Option A). Aggregate verdict written to `spikes/PHASE1-GATE.md`. Owner chose "Record GO, then stop"; session ends here. Phase 1 COMPLETE.
