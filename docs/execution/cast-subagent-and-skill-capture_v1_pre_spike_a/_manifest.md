# Execution Manifest: Cast Subagent and Skill Capture

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:

1. Start a new Claude session.
2. Tell Claude:
   "Read `docs/execution/cast-subagent-and-skill-capture/_shared_context.md` then execute
   `docs/execution/cast-subagent-and-skill-capture/spN_<name>/plan.md`."
3. After completion, update the Status column below.

## Sub-Phase Overview

| # | Sub-phase | Directory/File | Depends On | Status | Notes |
|---|-----------|----------------|-----------|--------|-------|
| 1 | Foundation: schema migration + helpers + sp1 verification | `sp1_foundation/` | -- | Not Started | Adds `skills_used` column; SQLite 3.9+ floor; `_cast_name.py` and `_invocation_sources.py`; `agent_service.resolve_run_by_session_id`; sibling `complete()` refactor; `test_system_ops_seed_idempotent` (auto-seed already shipped). **Decision gate: Spike A.** |
| 2 | Server: subagent capture service + 3 endpoints | `sp2_capture_service/` | 1 | Not Started | New `subagent_invocation_service.py` (register/complete/record_skill); 3 POST endpoints under `/api/agents/subagent-invocations/`. Goal-slug inheritance. Skill attribution = most-recent running cast-* row. Delegate `/cast-pytest-best-practices`. |
| 3 | Hook layer: HOOK_EVENTS extension + matcher + fire-and-forget POST | `sp3_hook_layer/` | 2 | Not Started | 3 new entries in `HOOK_EVENTS` (4-tuple shape); `install_hooks.py` learns per-event `matcher`; `_post()` refactored to fire-and-forget; hook-side scope filter via `AGENT_TYPE_PATTERN`. Delegate `/cast-pytest-best-practices`. |
| 4 | UI: L2 chip-list + L3 detail in /runs | `sp4_ui_surface/` | 3 | Not Started | New `run_skills_chips.html` and `run_skills_detail.html` partials; `/runs` route parses `skills_used`; CSS for `.skills-chips`. Empty `skills_used` hides chip row entirely. Delegate `/cast-pytest-best-practices`. |
| 5 | Spec capture + e2e smoke + close-out | `sp5_spec_and_e2e/` | 4 | Not Started | New spec `cast-subagent-and-skill-capture.collab.md` via `/cast-update-spec`; lint via `/cast-spec-checker`; register in `_registry.md`; cross-spec back-references; end-to-end manual smoke. |

Status: Not Started → In Progress → Done → Verified → Skipped

## Dependency Graph

```
sp1 (Foundation) ──► sp2 (Capture service) ──► sp3 (Hook layer) ──► sp4 (UI) ──► sp5 (Spec + E2E)
```

**Critical path:** sp1 → sp2 → sp3 → sp4 → sp5. Strictly linear — no genuine
parallelism. Sub-sub-phases within a single sp can run in any order, but the
inter-sp dependency chain is sequential.

## Execution Order

### Sequential Group 1
1. Sub-phase 1: foundation (schema, helpers, sp1 verification tests)

### Sequential Group 2 (after sp1)
2. Sub-phase 2: subagent capture service + 3 endpoints

### Sequential Group 3 (after sp2)
3. Sub-phase 3: hook layer (events, handlers, installer, fire-and-forget)

### Sequential Group 4 (after sp3)
4. Sub-phase 4: /runs UI surface (chips at L2, table at L3)

### Sequential Group 5 (after sp4)
5. Sub-phase 5: spec capture + registry + e2e smoke

## Critical Accuracy Notes (plan was patched against codebase reality)

- **sp1 system-ops auto-seed has ALREADY landed**
  (`cast-server/cast_server/db/connection.py::_seed_system_goals`). sp1 retains
  only the verification test (`test_system_ops_seed_idempotent`), not the
  implementation activity.
- **sp1 does NOT add a new single-column `idx_agent_runs_session_id`.** The
  existing composite `idx_agent_runs_session_status ON agent_runs(session_id,
  status)` already covers the lookup pattern (`WHERE session_id = ? AND status
  = 'running'`); sp1 verification reflects that.
- Build order is strictly LINEAR. No parallelism between sub-phases.
- Each sub-phase preserves its full Verification, Key activities, and Design
  review sections from the source plan.

## Progress Log

<!-- Update after each sub-phase completes. Capture surprises, scope adjustments,
     and any divergence from the plan. -->
