# Manual Subagent Mode Verification Checklist

> **When to run:** After any change to `_build_agent_prompt` subagent-block
> emission, the subagent dispatch path, or `cast-delegation-contract.collab.md`
> §Subagent Dispatch.
> **Budget:** <5 minutes start-to-finish.
> **Spec authority:** `docs/specs/cast-delegation-contract.collab.md` §Subagent Dispatch.

## Prerequisites

- cast-server bin available
- Claude Code session
- `CAST_TEST_AGENTS_DIR` set to `cast-server/tests/integration/agents/` (so the
  subagent fixture is discoverable)

## Steps

1. **Start a fresh Claude Code session** with the cast-server running locally.
2. **Trigger** the parent agent that has a subagent target in its allowlist.
   Example: `/invoke cast-test-parent-delegator <prompt>` (adapt to your local
   workflow).
3. **In the parent agent's preamble**, confirm the Subagent-dispatch block
   names `cast-test-child-worker-subagent`. (The agent's starting prompt is
   visible in the parent's terminal scrollback or its `.agent-run_*.prompt` file.)
4. **Watch the parent dispatch** the subagent via Claude Code's Agent tool
   (NOT via curl — subagent mode bypasses the HTTP queue).
5. **Verify the verdict is surfaced as-is** in the parent's output JSON
   `summary` field — not paraphrased, not summarized.
6. **Verify NO new row** appears in `agent_runs` for the subagent dispatch:
   ```sql
   SELECT count(*) FROM agent_runs WHERE agent_name = 'cast-test-child-worker-subagent'
   AND created_at > '<start of session>';
   ```
   Expected: 0.
7. **Verify the parent's run row** shows `status = completed` and the verdict
   substring is present in `result_summary`.
8. **Record the result** in the footer below.

## "Verified By" Footer

| Date | Maintainer | Result | Notes |
|------|-----------|--------|-------|
| <YYYY-MM-DD> | <name> | <pass/fail> | <one-line> |

## Cross-References

- T1 builder unit-test: `cast-server/tests/integration/test_child_delegation.py`
  → `TestSubagentOnlyPreamble` (sp6.1)
- Mixed-transport preamble test: `TestMixedTransportPreamble` (sp2.3)
- Spec: `docs/specs/cast-delegation-contract.collab.md` §Subagent Dispatch
