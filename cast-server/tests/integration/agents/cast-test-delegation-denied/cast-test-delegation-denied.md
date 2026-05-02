---
name: cast-test-delegation-denied
model: haiku
description: >
  DELIBERATELY-FAILING delegation-test fixture. Tries to HTTP-dispatch
  cast-test-child-worker-subagent (NOT in this agent's allowlist) so US3.S2
  can assert that allowlist denial flows through to a 422 with a deterministic
  summary string. The misalignment between allowed_delegations and the curl
  target is intentional test data — do not "fix" it.
tags:
  - test
  - integration
  - delegation
  - deliberately-failing
effort: trivial
---

<!--
DELIBERATELY-FAILING FIXTURE — do not "fix" the bug.
This agent's prompt tries to dispatch a non-allowlisted target so US3.S2
can assert that allowlist denial flows through to a 422 with a deterministic
summary string. See sp1.2 of the execution plan
(goals/child-delegation-integration-tests/execution/sp1_2_fixture_configs/plan.md).
-->

# cast-test-delegation-denied

DELIBERATELY-FAILING delegation-test fixture. Attempts to HTTP-dispatch
`cast-test-child-worker-subagent`, which is **not** in this agent's allowlist
(`allowed_delegations: [cast-test-child-worker]`). The 422 response body is
captured and surfaced verbatim in the parent's `summary`, so sp5.2's substring
assertion against `"denied (422)"` is byte-stable.

## Procedure (literal — do not paraphrase, do not add steps)

1. Read `<run_id>` and `<goal_slug>` from the runtime prompt preamble
   (`Your run ID: <run_id>`, `Goal slug: <goal_slug>`).

2. Run this exact curl (no substitutions other than `<goal_slug>` and `<run_id>`,
   no paraphrase). The target `cast-test-child-worker-subagent` is intentionally
   NOT in this agent's allowed_delegations — this curl is expected to receive
   a 422 response:

   ```bash
   curl -s -o /tmp/denied_body.json -w '%{http_code}' \
        -X POST http://localhost:8005/api/agents/cast-test-child-worker-subagent/trigger \
        -H 'Content-Type: application/json' \
        -d '{
          "goal_slug": "<goal_slug>",
          "parent_run_id": "<run_id>",
          "delegation_context": {
            "agent_name": "cast-test-child-worker-subagent",
            "instructions": "should never run — this dispatch is denied",
            "context": {"goal_title": "delegation-denied-test"},
            "output": {"output_dir": "<goal_dir>", "expected_artifacts": []}
          }
        }'
   ```

   Capture the HTTP status as `<http_code>` (expected: `422`).

3. Write to `<output_path>` (i.e. `<goal_dir>/.agent-<run_id>.output.json`)
   EXACTLY this JSON, do not paraphrase, do not add fields, do not omit fields.
   Substitute only `<started_at>` and `<completed_at>` (ISO-8601 UTC, Z-suffixed).
   The `summary` MUST contain the literal substring `denied (422)` so sp5.2's
   assertion is deterministic:

   ```json
   {
     "contract_version": "2",
     "agent_name": "cast-test-delegation-denied",
     "task_title": "delegation-denied test",
     "status": "failed",
     "summary": "cast-test-delegation-denied attempted to dispatch cast-test-child-worker-subagent and was denied (422) by the allowlist check.",
     "artifacts": [],
     "errors": ["allowlist denial: cast-test-child-worker-subagent not in allowed_delegations of cast-test-delegation-denied (HTTP 422)"],
     "next_steps": [],
     "human_action_needed": false,
     "human_action_items": [],
     "started_at": "<started_at>",
     "completed_at": "<completed_at>"
   }
   ```

4. Use atomic-write (write `.tmp`, fsync, rename) per
   `docs/specs/cast-delegation-contract.collab.md` § Atomic Write Contract.

5. Exit cleanly. The agent's run status is `failed` because the dispatch was
   denied — that is the expected outcome of this fixture.

## Constraints

- Determinism is non-negotiable. The substring `denied (422)` in `summary` is
  what sp5.2 pins against — do not paraphrase, do not change parentheses,
  do not change spacing.
- DO NOT "fix" the misalignment between `allowed_delegations` and the curl
  target. The misalignment IS the test.
- Do NOT do anything else. Zero side effects beyond the (denied) HTTP trigger
  and the parent's own `.agent-<run_id>.output.json` write.
