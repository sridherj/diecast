# Execution Manifest: Capture User Invocations As Runs

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:

1. Start a new Claude session.
2. Tell Claude:
   "Read `docs/execution/capture-user-invocations-as-runs/_shared_context.md` then execute
   `docs/execution/capture-user-invocations-as-runs/spN_<name>/plan.md`."
3. After completion, update the Status column below.

## Sub-Phase Overview

| # | Sub-phase | Directory/File | Depends On | Status | Notes |
|---|-----------|----------------|-----------|--------|-------|
| 1 | User-Invocation Service + Unit Tests | `sp1_service/` | -- | Done | Foundation; no HTTP/hooks. |
| 2 | API Endpoints + Tests | `sp2_endpoints/` | 1 | Done | Two thin endpoints; can parallel with 3, 4. |
| 3 | DB Index for Close-By-Session | `sp3_db_index/` | 1 | Done | One-line index addition; can parallel with 2, 4. |
| 4 | Hook Events, Handlers, `cast-hook` Console Script | `sp4_hooks_cli/` | 1 | Done | New `cli/` package + `pyproject.toml`. Can parallel with 2, 3. |
| 5 | settings.json Installer + Tests | `sp5_installer/` | 4 | In Progress | **User-safety critical.** Module-level autouse isolation fixture is non-negotiable. Delegate `/cast-pytest-best-practices`. |
| 6 | Wire Installer into `/cast-init` | `sp6_wire_cast_init/` | 5 | Not Started | Default ON; `--no-hooks` opt-out. |
| 7 | Spec Capture (Two Specs) | `sp7_specs/` | 6 | Not Started | `cast-user-invocation-tracking` + `cast-hooks`. Delegate `/cast-update-spec` and `/cast-spec-checker`. |
| 8 | End-to-End Smoke | `sp8_e2e_smoke/` | 7 | Not Started | Real Claude Code session; failure-mode probes. |

Status: Not Started → In Progress → Done → Verified → Skipped

## Dependency Graph

```
                  sp1 (service)
                /   |     \
              sp2  sp3   sp4    (parallel after sp1)
              (endpoints) (index) (hooks/cli)
                              |
                            sp5  (installer — depends on cli/ from sp4)
                              |
                            sp6  (wire into /cast-init)
                              |
                            sp7  (specs — depends on actual shipped behavior)
                              |
                            sp8  (e2e smoke)
```

## Execution Order

### Sequential Group 1
1. Sub-phase 1: service + unit tests

### Parallel Group 2 (after sp1 — run simultaneously OR sequentially, author's choice)
2. Sub-phase 2: API endpoints + tests
3. Sub-phase 3: DB index
4. Sub-phase 4: hook events + handlers + console script

**Parallel safety verified:** sp2, sp3, sp4 touch disjoint files
(sp2: `routes/api_agents.py`, `tests/test_api_agents.py`;
sp3: `db/connection.py`;
sp4: new `cli/` package, `pyproject.toml`, new `tests/test_cli_hook.py`).

### Sequential Group 3 (after Parallel Group 2)
5. Sub-phase 5: installer + tests (user-safety critical)

### Sequential Group 4 (after sp5)
6. Sub-phase 6: wire into /cast-init

### Sequential Group 5 (after sp6)
7. Sub-phase 7: spec capture (two specs)

### Sequential Group 6 (after sp7)
8. Sub-phase 8: end-to-end smoke

## Progress Log

<!-- Update after each sub-phase completes. Capture surprises, scope adjustments,
     and any divergence from the plan. -->
