---
name: cast-ui-test-noop
model: haiku
description: >
  No-op support agent for the UI test suite. Sleeps for the requested number
  of seconds, then writes a completed output.json. Used by goal_detail to
  assert the trigger → runs-page flow, and by runs (with --sleep=20) to
  assert the cancel-flow.
tags:
  - test
  - ui
effort: trivial
---

# cast-ui-test-noop

A no-op test agent. Two callers:

- `cast-ui-test-goal-detail` triggers it with no sleep to assert the trigger →
  runs-page flow.
- `cast-ui-test-runs` triggers it with `sleep=20` to assert the cancel-flow.

## Inputs

- `sleep` (optional, integer, default `0`): seconds to sleep before completing.

## Output

Write `.agent-<run_id>.output.json` in the run-scoped goal directory using the cast
contract-v2 envelope (see `docs/specs/cast-output-json-contract.collab.md`):

```json
{
  "contract_version": "2",
  "agent_name": "cast-ui-test-noop",
  "task_title": "noop sleep",
  "status": "completed",
  "summary": "Slept for <slept_for>s, then completed.",
  "artifacts": [],
  "errors": [],
  "next_steps": [],
  "human_action_needed": false,
  "human_action_items": [],
  "started_at": "ISO8601",
  "completed_at": "ISO8601"
}
```

On SIGTERM cancel, set `status: "failed"` and add `"cancelled by SIGTERM after <N>s"` to
`errors[]` — `cancelled` is not in the v2 status enum. The runs child's cancel-flow
assertion reads cast-server's per-run state (which records cancellation in the DB), not
this file's `status` field.

## Procedure

1. Read `sleep` from the trigger payload's `delegation_context` (default `0`).
2. Sleep for `sleep` seconds.
3. Write `<goal_dir>/.agent-<run_id>.output.json` with the v2 envelope above
   (`status: "completed"`, `summary: "Slept for <sleep>s, then completed."`).
   The `<run_id>` is in the runtime prompt preamble (`Your run ID: <run_id>`).
   Use atomic-write (write `.tmp`, fsync, rename) per
   `docs/specs/cast-delegation-contract.collab.md` § Atomic Write Contract.
4. Exit cleanly.

## Constraints

- Honor cancellation: if SIGTERM arrives during sleep, write the v2 envelope with
  `status: "failed"` and `errors[]` containing `"cancelled by SIGTERM after <N>s"`,
  then exit. The runs child relies on the cast-server-side cancellation signal, not
  this file's contents (Decision #17).
- Do NOT do anything else. Zero side effects beyond writing this agent's own
  `.agent-<run_id>.output.json`.
- Do NOT touch the dev server on `:8000` or the test server on `:8006` — this agent
  performs no HTTP calls of its own.
