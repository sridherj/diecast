# Execution Manifest: Cast-UI Harness Layered Fixes

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:
1. Start a new Claude session.
2. Tell Claude: "Read `docs/execution/cast-ui-harness-layered-fixes/_shared_context.md` then execute `docs/execution/cast-ui-harness-layered-fixes/<spX_name>/plan.md`."
3. After completion, update the Status column below.

## Sub-Phase Overview

| #  | Sub-phase                                  | Directory                                  | Depends On       | Status      | Notes                                                |
|----|--------------------------------------------|--------------------------------------------|------------------|-------------|------------------------------------------------------|
| 1  | Layer A1 — orchestrator output path        | `sp1_layer_a1_orchestrator_output_path/`   | --               | Done | FR-001, SC-001. `_read_orchestrator_output` rewrite. |
| 2  | Layer A2 — server stdout capture           | `sp2_layer_a2_server_stdout_capture/`      | --               | Done | FR-002, SC-002. conftest.py log + makereport hook.   |
| 3  | Layer A3 — runner domcontentloaded         | `sp3_layer_a3_runner_domcontentloaded/`    | --               | Done | FR-003, SC-003. Replace `networkidle` in runner.py.  |
| 4  | Layer B — assertion fixes per child        | `sp4_layer_b_assertion_fixes/`             | 1, 2, 3          | Done        | FR-004, SC-004. Per-child selector/route patch. Static work verified (5 funcs patched). Dynamic re-run revealed an unrelated child-completion bug (children dispatched but never write output.json) — tracked separately as `cast-ui-test-children-completion`. |
| 5  | Layer C — bug enumeration into tasks       | `sp5_layer_c_bug_enumeration/`             | 4                | Skipped     | FR-005, SC-005. Premise blocked: no post-sp4 red list because UI test children don't complete. Pick this back up after `cast-ui-test-children-completion` lands. |

Status: Not Started → In Progress → Done → Verified → Skipped

**Decision gate after sp4:** before sp5 runs, the human SHALL inspect the post-A+B
red list and confirm each item is a real product bug (vs. a still-mistaken assertion).
sp5 only enumerates items the human classified as Layer C.

## Dependency Graph

```
┌──────────────────────────────────┐
│ sp1 layer_a1 orchestrator_output │──┐
└──────────────────────────────────┘  │
                                      │
┌──────────────────────────────────┐  │      ┌────────────────────────┐      ┌────────────────────────┐
│ sp2 layer_a2 stdout_capture      │──┼─────▶│ sp4 layer_b assertions │─────▶│ sp5 layer_c bug_tasks  │
└──────────────────────────────────┘  │      └────────────────────────┘      └────────────────────────┘
                                      │
┌──────────────────────────────────┐  │
│ sp3 layer_a3 domcontentloaded    │──┘
└──────────────────────────────────┘
```

## Execution Order

### Parallel Group 1 — Layer A foundations (run simultaneously)
1. sp1: Orchestrator output-path fix  (`test_full_sweep.py`)
2. sp2: Server stdout capture + dump-on-failure  (`conftest.py`)
3. sp3: Runner `domcontentloaded` migration  (`runner.py`)

> **Why these are parallel:** sp1, sp2, sp3 touch three disjoint files. No shared
> imports, no shared symbols. Verify file targets before parallelizing.

### Sequential — Layer B (after Group 1 lands)
4. sp4: Per-child assertion patches in `runner.py` `_assert_<screen>` functions.

> sp4 cannot start before Group 1 because: (a) without sp1 the parent test reports
> wrong status, (b) without sp2 server-side 500s are invisible, (c) without sp3 the
> red list is dominated by `networkidle` timeouts. Layer B work is guesswork until
> these three signals are clean.

### Sequential — Layer C (after sp4 + human gate)
5. sp5: File one Diecast task per remaining real bug on the existing
   `comprehensive-ui-test` goal.

> sp5 needs the post-sp4 red list AND human classification of which entries are
> genuine product bugs vs. still-mistaken assertions.

## Progress Log

(Update after each sub-phase completes.)

- 2026-05-01: sp1, sp2, sp3 (Layer A) dispatched in parallel via /cast-orchestrate; all three Done within 3 minutes.
- 2026-05-01: sp4 (Layer B) dispatched. Static work landed in 26m (5 `_assert_<screen>` funcs patched in `cast-server/tests/ui/runner.py`; 2 assertions removed under Scenario B3). Dynamic verification initially blocked on root-owned `.venv`.
- 2026-05-01: After venv restored, dynamic verification revealed a **second, deeper Layer A regression** masked by sp2's incomplete capture: `cast-server/alembic/env.py` was calling `fileConfig()` without `disable_existing_loggers=False`, silencing every cast_server.app + uvicorn logger after the first DB stamp on every boot — production bug. Fixed in `cast-server/alembic/env.py:24-25` and defense-in-depth `PYTHONUNBUFFERED=1` added in `cast-server/tests/ui/conftest.py:135-138`. Server log went from 14 to 219 lines.
- 2026-05-01: With harness fixed, sweep still fails — but now for a downstream reason: the 7 per-screen test children (`cast-ui-test-*`) get dispatched, start tmux sessions, but never write `output.json`. Out of scope for *harness* fixes; track as a separate goal `cast-ui-test-children-completion`. sp4 marked Done, sp5 Skipped.
