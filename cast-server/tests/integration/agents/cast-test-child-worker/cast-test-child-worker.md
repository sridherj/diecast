---
name: cast-test-child-worker
model: haiku
description: >
  Delegation-test HTTP child fixture. Writes a literal contract-v2 envelope to
  <output_path> and exits. The summary is a fixed sentinel string that T1 and T2
  substring assertions match exactly.
tags:
  - test
  - integration
  - delegation
effort: trivial
---

# cast-test-child-worker

Delegation-test HTTP child. Writes a literal contract-v2 envelope to
`<output_path>` and exits. No HTTP calls, no further delegation.

## Procedure (literal — do not paraphrase, do not add steps)

1. Read `<run_id>` from the runtime prompt preamble (`Your run ID: <run_id>`).

2. Write to `<output_path>` (i.e. `<goal_dir>/.agent-<run_id>.output.json`)
   EXACTLY this JSON, do not paraphrase, do not add fields, do not omit fields.
   Substitute only `<started_at>` and `<completed_at>` (ISO-8601 UTC, Z-suffixed):

   ```json
   {
     "contract_version": "2",
     "agent_name": "cast-test-child-worker",
     "task_title": "delegation-test child",
     "status": "completed",
     "summary": "cast-test-child-worker completed successfully",
     "artifacts": [],
     "errors": [],
     "next_steps": [],
     "human_action_needed": false,
     "human_action_items": [],
     "started_at": "<started_at>",
     "completed_at": "<completed_at>"
   }
   ```

3. Use atomic-write (write `.tmp`, fsync, rename) per
   `docs/specs/cast-delegation-contract.collab.md` § Atomic Write Contract.

4. Exit cleanly.

## Constraints

- Determinism is non-negotiable. The `summary` field above is the literal
  sentinel string `cast-test-child-worker completed successfully` — do not
  paraphrase, do not add adjectives, do not change a single byte.
- Do NOT do anything else. Zero side effects beyond writing this agent's own
  `.agent-<run_id>.output.json`.
- `allowed_delegations: []` — this agent MUST NOT issue any HTTP triggers.
