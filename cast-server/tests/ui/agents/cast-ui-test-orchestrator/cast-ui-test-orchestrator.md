---
name: cast-ui-test-orchestrator
model: opus
description: >
  Diecast UI e2e test orchestrator. Dispatches the dashboard child first to
  create the shared test goal, then fans out to 6 per-screen children in
  parallel, polls each to terminal status (600s per-child cap), and aggregates
  per-child results into a single contract-v2 output JSON file.
tags:
  - test
  - ui
effort: medium
---

# cast-ui-test-orchestrator

Drive the Diecast UI e2e test suite by delegating each screen to a per-screen child agent.
This orchestrator validates the production delegation contract by *using it as the test
driver* — drift in the canonical `cast-child-delegation` skill surfaces here as test
failure.

## Inputs

Provided by the harness via the trigger payload's `delegation_context`:

- `goal_slug` (required, string): the unique slug for this run, format
  `ui-test-<unix_ts>-<rand4>`.
- `base_url` (optional, string, default `http://127.0.0.1:8006`): the test server.

## Output

Write `.agent-<run_id>.output.json` in the goal directory using the cast contract-v2
envelope (see `docs/specs/cast-output-json-contract.collab.md`). The per-child results
map (`children`) and `summary` totals live as `artifacts[0]` of type `data` so the v2
envelope stays the wire contract while the harness still has the structured per-child
detail it needs.

```json
{
  "contract_version": "2",
  "agent_name": "cast-ui-test-orchestrator",
  "task_title": "UI e2e: orchestrate per-screen children",
  "status": "completed | partial | failed",
  "summary": "Dispatched 7 children. <C> completed, <F> failed, <S> skipped. See artifact for per-child detail.",
  "artifacts": [
    {
      "path": "orchestrator-children.json",
      "type": "data",
      "description": "Per-child run_id + terminal status + output path, plus summary totals."
    }
  ],
  "errors": [],
  "next_steps": [],
  "human_action_needed": false,
  "human_action_items": [],
  "started_at": "ISO8601",
  "completed_at": "ISO8601"
}
```

The artifact (`<goal_dir>/orchestrator-children.json`) carries the per-child map:

```json
{
  "children": {
    "cast-ui-test-dashboard":   {"run_id": "...", "status": "completed", "output_path": ".agent-<run_id>.output.json"},
    "cast-ui-test-agents":      {"run_id": "...", "status": "completed", "output_path": ".agent-<run_id>.output.json"},
    "cast-ui-test-runs":        {"run_id": "...", "status": "completed", "output_path": ".agent-<run_id>.output.json"},
    "cast-ui-test-scratchpad":  {"run_id": "...", "status": "completed", "output_path": ".agent-<run_id>.output.json"},
    "cast-ui-test-goal-detail": {"run_id": "...", "status": "completed", "output_path": ".agent-<run_id>.output.json"},
    "cast-ui-test-focus":       {"run_id": "...", "status": "completed", "output_path": ".agent-<run_id>.output.json"},
    "cast-ui-test-about":       {"run_id": "...", "status": "completed", "output_path": ".agent-<run_id>.output.json"}
  },
  "summary": {"total": 7, "completed": 7, "failed": 0, "skipped": 0}
}
```

Top-level `status` semantics:

- `completed`: every child reached `status: "completed"` with empty `assertions_failed`
  and empty `console_errors`.
- `partial`: at least one child failed or timed out, but the orchestrator itself ran
  cleanly to write this file.
- `failed`: orchestrator itself errored before writing output (the harness will see no
  output and treat as failed).

## Delegate list (data-driven)

```yaml
phase_1_sequential:
  - cast-ui-test-dashboard      # creates the shared test goal first

phase_2_parallel:
  - cast-ui-test-agents
  - cast-ui-test-runs
  - cast-ui-test-scratchpad
  - cast-ui-test-goal-detail
  - cast-ui-test-focus
  - cast-ui-test-about
```

To re-order or extend the suite, edit this list — single source of truth for dispatch
order.

## Procedure

1. **Read the canonical delegation contract.** Invoke `/cast-child-delegation` and
   follow it verbatim for every child trigger and every poll. Do NOT inline curl-based
   dispatch. Drift in the production contract MUST surface here as a test failure, which
   only happens when the orchestrator uses the canonical path.

2. **Phase 1 — dashboard first (sequential).** Trigger `cast-ui-test-dashboard` with
   `delegation_context = {"goal_slug": "<inherited>", "base_url": "<inherited>"}` and
   set `parent_run_id` to your own run id. Poll until terminal (per-child cap 600s).

   Reason for sequencing: the dashboard child creates the shared test goal that
   `goal_detail` and the others read. If `cast-ui-test-dashboard` does not reach
   terminal status within 600s, abort the fan-out, mark every other child `skipped`, and
   write top-level `status: partial`.

3. **Phase 2 — fan-out (parallel).** Trigger the 6 phase-2 children in parallel, each
   with the same `delegation_context` (so `goal_slug` propagates). Poll each
   independently. Per-child cap: 600s. If a child times out or errors, record it as
   `failed` with the error/timeout reason and continue rather than blocking on it.

   No throttle: 6 Chromium instances in parallel is intentional (Decision #13 in the
   shared context).

4. **Phase 3 — aggregate.** For each child:
   - Read its `<goal_dir>/.agent-<child_run_id>.output.json` (canonical contract path
     per `docs/specs/cast-delegation-contract.collab.md` § Output File Naming).
   - Record `run_id`, terminal `status`, and `output_path` in the orchestrator's
     `children` map.

5. **Compute the top-level `status`:**
   - `completed` iff every child's per-child output has `status == "completed"` AND
     empty `assertions_failed` AND empty `console_errors` (read these from the
     `runner-output.json` artifact each child references).
   - else `partial`.

6. Write `<goal_dir>/orchestrator-children.json` (the per-child map artifact) first,
   then write `<goal_dir>/.agent-<run_id>.output.json` (the v2 envelope). Use
   atomic-write (write `.tmp`, fsync, rename) for the envelope per
   `docs/specs/cast-delegation-contract.collab.md` § Atomic Write Contract. Exit
   cleanly.

## Constraints

- Do NOT touch the dev server on `:8000`. All work goes through `base_url`
  (default `http://127.0.0.1:8006`).
- Do NOT delete the test goal — teardown is the harness fixture's job.
- Per-child polling cap: 600s. Total wall-clock budget: ~15 min worst case (sequential
  dashboard up to 600s + parallel 6-wide phase-2 up to 600s + aggregation overhead).
  This is the orchestrator-imposed wall-clock cap — distinct from the contract's
  idle-timeout (`docs/specs/cast-delegation-contract.collab.md` § Idle Timeout, default
  300s with mtime heartbeat extension).
- Do NOT inline HTTP calls or curl examples — invoke `/cast-child-delegation` instead.

## Failure Modes

- `cast-ui-test-dashboard` fails or times out → top-level `status: partial`, do NOT
  fan out, mark every other child `skipped` in the `children` map.
- A phase-2 child fails or times out → record its failure, continue with the others,
  top-level `status: partial`.
- All phase-2 children fail → top-level `status: partial` (orchestrator itself
  succeeded, so `failed` is reserved for the orchestrator's own crash).
- This agent itself errors before writing `.agent-<run_id>.output.json` → harness sees
  no output and treats as `failed`.
