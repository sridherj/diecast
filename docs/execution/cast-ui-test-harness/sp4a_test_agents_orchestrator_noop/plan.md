# Sub-phase 4a: Orchestrator + noop test agent definitions

> **Pre-requisite:** Read `docs/execution/cast-ui-test-harness/_shared_context.md` AND
> `skills/claude-code/cast-child-delegation/SKILL.md` before starting.

## Objective

Author the orchestrator agent (`cast-ui-test-orchestrator`) and the support agent
(`cast-ui-test-noop`) under `cast-server/tests/ui/agents/`. Both follow the canonical
`cast-child-delegation` skill verbatim. The orchestrator dispatches the dashboard child
first (to create the test goal), polls to completion, then triggers the remaining 6 screen
children in parallel, polls all to terminal status, aggregates per-child results into a
single `output.json`.

The `noop` agent supports two callers: goal_detail (no sleep, used to assert the runs-page
flow) and runs (`--sleep=20`, used to assert the cancel-flow). It writes `output.json` with
`status: completed` after sleeping the requested amount.

## Dependencies
- **Requires completed:** sp3 (`runner.py` CLI contract). The orchestrator does not call
  runner.py itself, but its dispatch pattern must align with what the screen agents (sp4b)
  invoke — sharing a base test agents directory means the contract has to settle first.
- **Assumed codebase state:** `cast-server/tests/ui/agents/` exists (sp2 may have created it
  as a placeholder). Test agent registry merge logic from sp1 is in place (so the test server
  loads these agents).

## Scope

**In scope:**
- `cast-server/tests/ui/agents/cast-ui-test-orchestrator/cast-ui-test-orchestrator.md` (instructions)
- `cast-server/tests/ui/agents/cast-ui-test-orchestrator/config.yaml`
- `cast-server/tests/ui/agents/cast-ui-test-noop/cast-ui-test-noop.md` (instructions)
- `cast-server/tests/ui/agents/cast-ui-test-noop/config.yaml`

**Out of scope (do NOT do these):**
- Do NOT author the 7 per-screen agents — sp4b owns those.
- Do NOT modify `runner.py`.
- Do NOT modify `agent_service.py` or fixtures.
- Do NOT inline curl-based delegation in the orchestrator instructions; reference the
  canonical `/cast-child-delegation` skill instead (FR-004 / Decision #3).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/ui/agents/cast-ui-test-orchestrator/cast-ui-test-orchestrator.md` | Create | Does not exist. |
| `cast-server/tests/ui/agents/cast-ui-test-orchestrator/config.yaml` | Create | Does not exist. |
| `cast-server/tests/ui/agents/cast-ui-test-noop/cast-ui-test-noop.md` | Create | Does not exist. |
| `cast-server/tests/ui/agents/cast-ui-test-noop/config.yaml` | Create | Does not exist. |

## Detailed Steps

### Step 4a.1: Read the canonical delegation skill

Open `skills/claude-code/cast-child-delegation/SKILL.md`. The orchestrator and any future
multi-child test agent invoke this skill verbatim — it owns the `parent_run_id`, the
trigger payload shape, the polling cadence, and the failure handling.

Two things to extract before authoring:
- The exact HTTP shape: `POST /api/agents/{name}/trigger` body schema, response shape, and
  which fields the parent threads through to children (`parent_run_id`, `delegation_context`,
  etc.).
- The polling pattern: endpoint, cadence, timeout convention, terminal status set.

### Step 4a.2: Author the orchestrator instructions file

Create `cast-server/tests/ui/agents/cast-ui-test-orchestrator/cast-ui-test-orchestrator.md`.
Structure:

```markdown
# cast-ui-test-orchestrator

Drive the Diecast UI e2e test suite by delegating each screen to a per-screen child agent.

## Inputs

- `goal_slug` (required, string): the unique slug for this run, format `ui-test-<unix_ts>-<rand4>`.
  Provided by the harness via the trigger payload's `delegation_context`.
- `base_url` (optional, string, default `http://127.0.0.1:8006`): the test server.

## Output

Write `output.json` in the goal directory with this shape:

```json
{
  "status": "completed" | "partial" | "failed",
  "children": {
    "cast-ui-test-dashboard":   {"run_id": "...", "status": "...", "output_path": "..."},
    "cast-ui-test-agents":      {...},
    "cast-ui-test-runs":        {...},
    "cast-ui-test-scratchpad":  {...},
    "cast-ui-test-goal-detail": {...},
    "cast-ui-test-focus":       {...},
    "cast-ui-test-about":       {...}
  },
  "summary": {"total": 7, "completed": <n>, "failed": <n>, "skipped": <n>}
}
```

- `completed`: every child reached `status: completed` with no `assertions_failed` and no `console_errors`.
- `partial`: at least one child failed but others succeeded.
- `failed`: orchestrator itself errored (could not even dispatch).

## Procedure

1. Read the canonical delegation contract: `/cast-child-delegation`. Use it verbatim for every
   child trigger and poll. Do NOT inline curl-based dispatch.

2. **Phase 1 — dashboard first (sequential).** Trigger `cast-ui-test-dashboard` with
   `delegation_context = {"goal_slug": "<inherited>", "base_url": "<inherited>"}`.
   Poll until terminal (max 90s). Reason: the dashboard child creates the shared test goal
   used by `goal_detail`. If dashboard fails to terminal-state within 90s, abort
   subsequent fan-out and write `status: partial`.

3. **Phase 2 — fan-out (parallel).** Trigger these 6 children in parallel, each with the
   same `delegation_context` (so `goal_slug` propagates):
   - `cast-ui-test-agents`
   - `cast-ui-test-runs`
   - `cast-ui-test-scratchpad`
   - `cast-ui-test-goal-detail`
   - `cast-ui-test-focus`
   - `cast-ui-test-about`

   Poll each independently. Per-child cap: 90s. If a child times out, mark it `failed`
   with a timeout error and continue rather than blocking on it.

4. **Phase 3 — aggregate.** For each child:
   - Read the child's `output.json` from its goal directory (run-scoped).
   - Record `run_id`, terminal `status`, and `output_path` in the orchestrator's
     `children` map.

5. Compute the top-level `status`:
   - `completed` iff every child has `status == "completed"` AND empty `assertions_failed`
     AND empty `console_errors`.
   - else `partial`.

6. Write `output.json` and exit cleanly.

## Constraints

- Do NOT touch the dev server on `:8000`.
- Do NOT delete the test goal — teardown is the harness fixture's job (sp2).
- Per-child polling cap: 90s. Total wall-clock budget: ~110s (SC-001 says <120s).
- 7 children running 7 Chromium instances in parallel is intentional (no throttle).

## Failure Modes

- `cast-ui-test-dashboard` fails → set top-level `status: partial`, do NOT fan out.
- A fan-out child fails → record its failure, continue with the others.
- All children fail → top-level `status: partial` (not `failed`; orchestrator itself succeeded).
- This agent itself errors before writing output.json → harness will see no output and
  treat as `failed`.
```

### Step 4a.3: Author the orchestrator config.yaml

Mirror the structure of an existing production agent's `config.yaml`. Inspect one
under the production agents root to confirm the exact key names; minimal expected shape:

```yaml
name: cast-ui-test-orchestrator
description: |
  Diecast UI e2e test orchestrator. Fans out to 7 per-screen children
  and aggregates results.
entrypoint: cast-ui-test-orchestrator.md
inputs:
  goal_slug:
    type: string
    required: true
  base_url:
    type: string
    required: false
    default: http://127.0.0.1:8006
# If the production agents use a `tags`, `category`, `visible` key, mirror them here so the
# /agents page renders this child consistently. visible: true so US3 Scenario 1 is provable.
tags:
  - test
  - ui
visible: true
```

**If the production config schema requires fields not listed here**, copy them from a
production agent and fill in test-appropriate values. The goal is for the registry merge
to produce a usable entry, not to invent a new schema.

### Step 4a.4: Author the noop instructions file

Create `cast-server/tests/ui/agents/cast-ui-test-noop/cast-ui-test-noop.md`:

```markdown
# cast-ui-test-noop

A no-op test agent. Used by the goal_detail child to assert the trigger → runs-page flow,
and by the runs child to assert the cancel-flow (with `--sleep=20`).

## Inputs

- `sleep` (optional, integer, default 0): seconds to sleep before completing.

## Procedure

1. Sleep for `sleep` seconds (default 0).
2. Write `output.json` with:

   ```json
   {
     "status": "completed",
     "message": "noop",
     "slept_for": <sleep>
   }
   ```

3. Exit cleanly.

## Constraints

- Honor cancellation: if SIGTERM arrives during sleep, write `output.json` with
  `status: cancelled` and exit. (The runs child relies on this for the cancel-flow assertion.)
- Do NOT do anything else. This agent has zero side effects beyond writing its own output.
```

### Step 4a.5: Author the noop config.yaml

```yaml
name: cast-ui-test-noop
description: |
  No-op support agent for the UI test suite. Sleeps for the requested
  number of seconds, then writes a completed output.json.
entrypoint: cast-ui-test-noop.md
inputs:
  sleep:
    type: integer
    required: false
    default: 0
tags:
  - test
  - ui
visible: true
```

### Step 4a.6: Verify the registry picks them up

Once sp1's `get_all_agents()` extension is in place, you can verify the merge sees these
two new agents:

```bash
CAST_TEST_AGENTS_DIR=$(pwd)/cast-server/tests/ui/agents \
  python -c "from cast_server.services.agent_service import get_all_agents; \
             names = sorted(get_all_agents().keys()); \
             for n in names: \
                 if n.startswith('cast-ui-test-'): print(n)"
# Expect:
# cast-ui-test-noop
# cast-ui-test-orchestrator
```

## Verification

### Automated Tests (permanent)

This sub-phase ships agent definitions. Permanent verification belongs to sp1's
`test_registry_visibility.py` (which now expects all 9 names — but the names list there
is forward-looking and is satisfied piecewise as sp4a/sp4b land their files).

If `test_registry_visibility.py` was written expecting all 9 immediately, expect it to be
red until sp4b also lands. That's fine — the manifest's parallel ordering accepts this.

### Validation Scripts (temporary)

```bash
# Confirm the two new dirs and their files exist with the expected names.
find cast-server/tests/ui/agents/cast-ui-test-orchestrator cast-server/tests/ui/agents/cast-ui-test-noop -type f | sort

# YAML syntax sanity.
python -c "import yaml, pathlib; \
[yaml.safe_load(p.read_text()) \
 for p in pathlib.Path('cast-server/tests/ui/agents').rglob('config.yaml')]; \
print('all configs parsed')"
```

### Manual Checks

- Diff against an existing production agent's `<name>.md` to confirm the structure is
  consistent (front matter, headers, sections).
- Diff against an existing production agent's `config.yaml` to confirm the schema is
  consistent.
- Re-read the orchestrator instructions: it must reference `/cast-child-delegation`
  explicitly. No inline curl or HTTP call instructions.

### Success Criteria

- [ ] All 4 files created at the paths in the table above.
- [ ] Both `config.yaml` files parse as YAML.
- [ ] Orchestrator instructions reference `/cast-child-delegation` skill verbatim and contain
      the dashboard-first / fan-out-others sequence (Decision #7).
- [ ] Orchestrator instructions specify the 90s per-child polling cap (Decision #12).
- [ ] noop instructions specify `--sleep` arg, default 0, and SIGTERM-on-cancel behavior (Decision #17).
- [ ] With `CAST_TEST_AGENTS_DIR` set, `get_all_agents()` returns `cast-ui-test-orchestrator`
      and `cast-ui-test-noop`.

## Execution Notes

- **Reference, don't inline.** The orchestrator instructions reference the canonical
  delegation skill. Do not paste curl examples — drift in the production contract should
  surface as test failure, which only happens when tests use the canonical path.
- **`config.yaml` schema:** the exact required fields depend on the production agent loader.
  Inspect a real prod agent's config first; mirror its shape.
- **Visibility (`visible: true`):** required so US4 Scenario 6 (assert at least one
  `cast-ui-test-*` card visible on `/agents`) can be observed by the agents-page child.
  In the dev server (without `CAST_TEST_AGENTS_DIR`), these agents are not loaded at all,
  so this `visible: true` does not leak into dev — US3 still holds.
- **Skill delegation:** -> Use `/cast-agent-design-guide` for cross-checking the agent file
  structure (front matter, sections, IO schema) against the project canon. Run it once
  against the orchestrator file and once against the noop file.
- **Spec-linked files:** None of the modified files are covered by a spec in `docs/specs/`.
