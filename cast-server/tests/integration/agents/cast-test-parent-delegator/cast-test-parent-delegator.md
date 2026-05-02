---
name: cast-test-parent-delegator
model: haiku
description: >
  Delegation-test parent fixture. Dispatches cast-test-child-worker via HTTP,
  polls the child's output file, then writes a literal contract-v2 envelope.
  Determinism is non-negotiable — output bytes are byte-stable so T2 substring
  assertions can pin them.
tags:
  - test
  - integration
  - delegation
effort: trivial
---

# cast-test-parent-delegator

Delegation-test parent. Dispatches `cast-test-child-worker` via HTTP, polls the
child's `.agent-<child_run_id>.output.json`, then writes the parent's literal
contract-v2 envelope to `<output_path>` and exits.

## Procedure (literal — do not paraphrase, do not add steps)

1. Read `<run_id>` and `<goal_slug>` from the runtime prompt preamble
   (`Your run ID: <run_id>`, `Goal slug: <goal_slug>`).

2. Run this exact curl (no substitutions other than `<goal_slug>` and `<run_id>`,
   no paraphrase):

   ```bash
   curl -s -X POST http://localhost:8005/api/agents/cast-test-child-worker/trigger \
        -H 'Content-Type: application/json' \
        -d '{
          "goal_slug": "<goal_slug>",
          "parent_run_id": "<run_id>",
          "delegation_context": {
            "agent_name": "cast-test-child-worker",
            "instructions": "Write the literal contract-v2 envelope and exit.",
            "context": {"goal_title": "delegation-test"},
            "output": {"output_dir": "<goal_dir>", "expected_artifacts": []}
          }
        }'
   ```

   Capture the returned `run_id` as `<child_run_id>`.

3. Poll `<goal_dir>/.agent-<child_run_id>.output.json` every 1s up to 30s.
   Stop polling as soon as the file exists and parses as JSON with a terminal
   `status` field (one of `completed`, `partial`, `failed`).

4. Write to `<output_path>` (i.e. `<goal_dir>/.agent-<run_id>.output.json`)
   EXACTLY this JSON, do not paraphrase, do not add fields, do not omit fields.
   Substitute only `<run_id>`, `<child_run_id>`, `<started_at>`, and
   `<completed_at>` (ISO-8601 UTC, Z-suffixed):

   ```json
   {
     "contract_version": "2",
     "agent_name": "cast-test-parent-delegator",
     "task_title": "delegation-test parent",
     "status": "completed",
     "summary": "cast-test-parent-delegator dispatched cast-test-child-worker (child_run_id=<child_run_id>) and observed terminal child output.",
     "artifacts": [],
     "errors": [],
     "next_steps": [],
     "human_action_needed": false,
     "human_action_items": [],
     "started_at": "<started_at>",
     "completed_at": "<completed_at>"
   }
   ```

5. Use atomic-write (write `.tmp`, fsync, rename) per
   `docs/specs/cast-delegation-contract.collab.md` § Atomic Write Contract.

6. Exit cleanly.

## Constraints

- Determinism is non-negotiable. The `summary` field above is the literal
  sentinel string T2 substring assertions match against — do not paraphrase,
  do not add adjectives, do not change the substring `dispatched cast-test-child-worker`.
- Do NOT do anything else. Zero side effects beyond the HTTP trigger and the
  parent's own `.agent-<run_id>.output.json` write.
- Allowed delegations: `cast-test-child-worker`, `cast-test-child-worker-subagent`.
