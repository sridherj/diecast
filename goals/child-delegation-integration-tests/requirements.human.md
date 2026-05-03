# Child Delegation Integration Tests — Raw Requirements

## Origin

User invocation of `/cast-refine-requirements`, 2026-05-01:

> we had some very good integration tests for child-delegation in
> <SECOND_BRAIN_ROOT>. Can you take a look? though the contracts have
> changed, it was very useful to confirm this important feature worked. Right
> now I feel its breaking in quite a few ways. It probably had a spec as well.

## Reference material identified

- `<SECOND_BRAIN_ROOT>/docs/specs/taskos_agent_delegation.collab.md` (310 lines) — the previous spec
- `<SECOND_BRAIN_ROOT>/taskos/tests/test_delegation.py` (869 lines) — the integration suite
- `<SECOND_BRAIN_ROOT>/taskos/tests/e2e/test_tier2_delegation.py` (129 lines) — live E2E
- `<SECOND_BRAIN_ROOT>/agents/test-parent-delegator/`, `agents/test-child-worker/` — fixture agents
- `<SECOND_BRAIN_ROOT>/docs/plan/2026-03-28-delegation-test-plan.md` — plan that drove the suite

Existing diecast counterparts:
- `docs/specs/cast-delegation-contract.collab.md` (264 lines) — file-canonical contract spec
- `skills/claude-code/cast-child-delegation/SKILL.md` (794 lines) — runtime encoding
- `tests/test_b5_*.py`, `tests/test_b3_*.py`, `tests/test_b4_*.py` — primitive-level tests (not feature-level)

## Refinement Q&A (verbatim, 2026-05-01)

**Q1 — scope:** _Tests + fix the broken behaviors in the same goal._
**Q2 — goal/scope:** _New goal, BOTH transports (HTTP + subagent)._
**Q3 — test tiers:** _T1 mocked + T2 live HTTP E2E + manual subagent checklist (Recommended)._
**Q4 — observed symptoms:** _Allowlist/depth/output-JSON violations get through silently;
cleanup or contract drift (orphan .delegation/.prompt/.tmp; 422 shape; mixed-transport
preamble malformed); parent stalls/mis-finalizes despite child writing output.json._

## What the user explicitly asked for

1. Re-establish the test discipline that worked in second-brain — same *types* of test,
   adapted to diecast's file-canonical contract.
2. Pin down the currently-suspected breakages with red tests, then ship the fixes in
   the same goal.
3. Cover both HTTP and subagent transports.
4. Use second-brain's spec as a starting reference (intent, behaviors, quality bar)
   without copying contract details that have changed.
