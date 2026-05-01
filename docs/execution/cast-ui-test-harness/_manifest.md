# Execution Manifest: Cast-UI E2E Test Harness

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:
1. Start a new Claude session.
2. Tell Claude: "Read `docs/execution/cast-ui-test-harness/_shared_context.md` then execute `docs/execution/cast-ui-test-harness/<spX_name>/plan.md`."
3. After completion, update the Status column below.

## Sub-Phase Overview

| #   | Sub-phase                              | Directory                              | Depends On            | Status      | Notes                                       |
|-----|----------------------------------------|----------------------------------------|-----------------------|-------------|---------------------------------------------|
| 1   | Registry env-var merge + meta-test     | `sp1_registry_extension/`              | --                    | Done | FR-001, FR-009, SC-003                      |
| 2   | Pytest fixtures + dev dep + teardown   | `sp2_test_infra_fixtures/`             | --                    | Done | FR-002, FR-006, FR-008                      |
| 3   | Shared Playwright runner.py            | `sp3_runner_helper/`                   | --                    | Done | FR-005. Defines CLI contract for sp4a/sp4b. |
| 4a  | Orchestrator + noop test agents        | `sp4a_test_agents_orchestrator_noop/`  | 3                     | Done | FR-004 (orch + noop). Parallel with 4b.     |
| 4b  | 7 per-screen test agents               | `sp4b_test_agents_screens/`            | 3                     | Done | FR-004 (screen children). Parallel with 4a. |
| 5   | `test_full_sweep.py` + README          | `sp5_e2e_test_and_readme/`             | 1, 2, 3, 4a, 4b       | Done | FR-003, FR-007. Final glue.                 |

Status: Not Started → In Progress → Done → Verified → Skipped

No decision gates in this plan.

## Dependency Graph

```
                  ┌──────────────────────┐
                  │ sp1_registry_extens. │──┐
                  └──────────────────────┘  │
                                            │
                  ┌──────────────────────┐  │
                  │ sp2_test_infra_fixtu.│──┤
                  └──────────────────────┘  │
                                            ▼
┌───────────────────┐  ┌───────────────────┐    ┌──────────────────────────┐
│ sp3_runner_helper │─▶│ sp4a_orch+noop    │───▶│ sp5_e2e_test_and_readme  │
└───────────────────┘  └───────────────────┘    └──────────────────────────┘
        │                                            ▲
        │              ┌───────────────────┐         │
        └─────────────▶│ sp4b_screens (×7) │─────────┘
                       └───────────────────┘
```

## Execution Order

### Parallel Group 1 — independent foundations (run simultaneously)
1. sp1: Registry env-var merge
2. sp2: Pytest fixtures + dev dep
3. sp3: Shared Playwright runner.py

### Parallel Group 2 — agent definitions (after Group 1; need sp3's runner.py CLI contract)
4a. sp4a: Orchestrator + noop test agents
4b. sp4b: 7 per-screen test agents

### Sequential Group 3 — final glue (after Groups 1 & 2)
5. sp5: `test_full_sweep.py` + README

> **Why sp1, sp2, sp3 are parallel:** they touch entirely disjoint files (`agent_service.py` /
> meta-test vs `conftest.py` / `pyproject.toml` vs `runner.py`). Verify before parallelizing.
> **Why sp4a and sp4b are parallel:** disjoint agent directories (`orchestrator/`, `noop/` vs the
> 7 screen dirs).

## Progress Log

(Update after each sub-phase completes.)

- _none yet_
