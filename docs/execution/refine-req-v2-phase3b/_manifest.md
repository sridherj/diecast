# Execution Manifest: Refine Requirements v2 — Phase 3b (Routing: Phase-Agnostic Workflow Router)

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:

1. Start a new Claude session in the Diecast repo root.
2. Tell Claude: "Read `docs/execution/refine-req-v2-phase3b/_shared_context.md` then execute
   `docs/execution/refine-req-v2-phase3b/spN_<name>/plan.md`."
3. After completion, update the Status column below and commit.

Each sub-phase corresponds to a **Work Package** (A–F) from the source plan
(`docs/plan/2026-06-11-refine-requirements-v2-phase3b-workflow-router.md`), preserving the plan's own
Build Order. The whole phase ships as **1–2 sessions** of work (the plan's estimate: A+B ≈ ½ session,
C+D ≈ ½–1, E+F ≈ ½–1).

> **⚠️ Hard prerequisite (read `_shared_context.md` → "Hard Prerequisite"):** Phase 2's
> `cast-server/cast_server/requirements_render/families.py` (the `WorkFamily` enum) and the Phase 2
> WP-E "Step 0 — Classify" wiring in `cast-refine-requirements.md` must be landed before **any**
> Phase 3b sub-phase. Phase 3b is **off the critical path** of the whole goal (Phase 4 depends on
> Phase 3a, not 3b) and runs in parallel with Phase 3a.

## Sub-Phase Overview

| #    | Sub-phase                                          | Directory/File                   | Source WP | Depends On            | Status      | Notes |
|------|----------------------------------------------------|----------------------------------|-----------|-----------------------|-------------|-------|
| 1a   | Family registry in `config.py` — the keystone      | `sp1a_family_registry/`          | A         | — (Phase 2 landed)    | Not Started | `WORKFLOW_REGISTRY` + derived `WORKFLOW_FAMILIES` beside `STARTER_TASKS`. Parallel with 1b. The registry IS the router — build first. |
| 1b   | Recording columns on `goals` + model threading     | `sp1b_recording_columns/`        | C         | — (Phase 2 landed)    | Not Started | 3 columns (schema + migration), `GoalUpdate` threading, `goal.yaml` render. Parallel with 1a. The write target. |
| 2    | Pure resolver `workflow_router_service.py`         | `sp2_resolver_service/`          | B         | 1a, 1b                | Not Started | `resolve` (PURE+TOTAL) + `record_routing_decision` (one writer) + CLI hook + full test module. Critical path. |
| 3    | `POST /api/goals/{slug}/route` (phase-agnostic API)| `sp3_route_endpoint/`            | D         | 2                     | Not Started | Agent-facing JSON; FR-016 pure re-resolve; SC-005 byte-stability. Critical path. |
| 4a   | Wire the single v2 caller + `/cast-router` skill   | `sp4a_refine_wiring/`            | E         | 3                     | Not Started | ~15 lines appended to Phase 2 Step 0 + new read-only `/cast-router`. Runs `bin/generate-skills`. Parallel with 4b. Critical path. |
| 4b   | Spec lockstep (`cast-workflow-routing.collab.md`)  | `sp4b_routing_spec/`             | F         | 1a, 2, 3 (interfaces) | Not Started | New spec via `/cast-update-spec`; appends to Phase 2 add-a-family checklist (D3). Doc-only. Parallel with 4a. |

Status: Not Started → In Progress → Done → Verified → Skipped

**No decision gates.** Operating mode is HOLD SCOPE — all five plan-review decisions (D1–D5) are
resolved and recorded in the source plan's `## Decisions` section; there is nothing to pause for. The
one autonomous-run default (ship `/cast-router`) is recorded in `_shared_context.md` and `_review_summary.md`.

## Dependency Graph

```
sp1a_family_registry (A) ──┐
   (WORKFLOW_REGISTRY)      │
                            ├──▶ sp2_resolver_service (B) ──▶ sp3_route_endpoint (D) ──┬──▶ sp4a_refine_wiring (E)
sp1b_recording_columns (C)──┘        (resolve + recorder)        (POST /route)         │      (sole v2 caller + /cast-router)
   (goals columns)                                                                     └──▶ sp4b_routing_spec (F)
                                                                                            (parallel with sp4a)
```

**Critical path:** sp1a → sp2 → sp3 → sp4a.
sp1b runs parallel with sp1a (both feed sp2 — the recorder writes the columns sp1b creates).
sp4b (spec/docs) runs parallel with sp4a once the sp1a–sp3 interfaces have settled.
All of Phase 3b parallels Phase 3a.

## Execution Order

### Parallel Group 1 (after Phase 2 — independent files)
1a. **sp1a_family_registry** (WP A) — `cast-server/cast_server/config.py` + a registry-shape unit
    test. The dependency-free bottom layer; everything reads it. Independently verifiable: the
    status/`steps` validity tests pass with no service/route/migration work present. (The
    registry↔enum key-set pin test is co-located in sp2's module — it is the one place Phase 3b
    imports `families.py`, in tests only.)
1b. **sp1b_recording_columns** (WP C) — `db/schema.sql` + `db/connection.py` migration + `models/goal.py`
    + `services/goal_service.py` (`_write_goal_yaml` conditional includes). Independently verifiable:
    fresh-DB `init_db` exposes the columns; legacy-DB migration is idempotent (run `_run_migrations`
    twice) — with no router service present.

> **Parallel-safety (1a ∥ 1b):** disjoint source files — sp1a touches only `config.py`; sp1b touches
> `schema.sql`, `connection.py`, `goal.py`, `goal_service.py`. No shared file, no shared action.

### Sequential Group 2 (after Group 1 — needs both)
2. **sp2_resolver_service** (WP B) — `services/workflow_router_service.py` + `tests/test_workflow_router_service.py`.
   Imports `WORKFLOW_REGISTRY`/`WORKFLOW_FAMILIES` (sp1a) and writes the goal columns (sp1b). The
   recorder's idempotency / change-path / `goal.yaml` round-trip / missing-yaml tests need sp1b's
   columns to be green — hence sp2 follows **both** 1a and 1b, not just 1a.

### Sequential Group 3 (after Group 2)
3. **sp3_route_endpoint** (WP D) — `routes/api_goals.py` `POST /{slug}/route` + `tests/test_api_goals_route.py`.
   The phase-agnostic HTTP door; carries the SC-005 phase-flip byte-stability trace and the
   no-reclassify source pin on the handler module (D4).

### Parallel Group 4 (after Group 3 — independent files)
4a. **sp4a_refine_wiring** (WP E) — `agents/cast-refine-requirements/*` (~15-line Step 0 tail) + new
    `agents/cast-router/*`. Runs `bin/generate-skills`. Critical path.
4b. **sp4b_routing_spec** (WP F) — `docs/specs/cast-workflow-routing.collab.md` + `_registry.md`;
    appends routing steps to `cast-goal-classification.collab.md`'s add-a-family checklist (D3).
    Documentation lockstep; no code change.

> **Parallel-safety (4a ∥ 4b):** sp4a touches `agents/` (and runs `generate-skills`); sp4b touches
> `docs/specs/`. Disjoint. sp4b *reads* `config.py`/`workflow_router_service.py` to copy exact names
> but writes neither.

## Files Touched by More Than One Sub-Phase

| File / Action | Sub-phases | Conflict resolution |
|---|---|---|
| `cast-server/tests/test_workflow_router_service.py` | sp2 owns it. The registry↔enum **pin test** logically belongs to WP-A but is **co-located here** (per the source plan: "Tests in WP-B's test module"; it is the ONE place Phase 3b imports `families.py`). | Single owner: sp2. sp1a writes only the registry-shape validity test in its own file. No overlap. |
| `agents/cast-refine-requirements/cast-refine-requirements.md` | sp4a **(this plan)** + **Phase 2 WP-E** + **Phase 1b** (different phases) | sp4a appends the routing call as the **tail of Phase 2's "Step 0 — Classify"** — it does not duplicate or move Phase 2/1b content; it only sequences the existing question budget. Respect the ~650-line ceiling. |
| `bin/generate-skills` (action, not a file) | sp4a **(this plan)** + Phase 2 sub-phases (different phase) | Idempotent; regenerates the whole skills tree from `agents/`. sp4a runs it after editing `cast-refine-requirements` and creating `cast-router`; re-run if a partial tree appears. |
| `cast-server/cast_server/config.py` | sp1a only (within this plan) | Single owner. |
| `cast-server/cast_server/db/schema.sql`, `db/connection.py`, `models/goal.py`, `services/goal_service.py` | sp1b only (within this plan) | Single owner. (Phase 1/2 may have touched these in earlier phases; sp1b rebases additively over the `gstack_dir` precedent — do not clobber.) |

All other files are written by exactly one sub-phase. The parallel groups (1a/1b and 4a/4b) modify
disjoint source files — verified during analysis.

## Cross-Phase Interface Contract (Phases 4/5 and future pipeline goals adopt verbatim)

sp1a + sp2 set the names the rest of Refine-Requirements-v2 and every future per-family pipeline goal
consume — do not rename after sp3 starts:
- `WORKFLOW_REGISTRY`, `WORKFLOW_FAMILIES` (`config.py`); `WorkflowHandle`, `resolve`,
  `record_routing_decision` (`workflow_router_service.py`).
- Stored handle format `routing_handle = f"{family}:{status}"`; `goals.workflow_family` is the
  **authoritative** routing record (D2).
- `POST /api/goals/{slug}/route` request/response contract (sp3).
- Resolve from the persisted `goals.workflow_family` column, never re-classify (FR-016/SC-005).

## Progress Log

_(Update after each sub-phase: date, sub-phase, status, commit, notes.)_

- _Not started._
