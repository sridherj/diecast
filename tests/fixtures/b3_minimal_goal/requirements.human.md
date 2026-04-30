# B3 Auto-Review Fixture Requirements

## Problem
A synthetic minimal goal used by `tests/test_b3_auto_review.py` and
`tests/test_b3_full_chain.py` to verify that `cast-detailed-plan`'s Step 10
auto-trigger of `cast-plan-review` fires by default and is suppressed by the
`--no-review` flag.

## Constraints
- Keep the fixture small — the test verifies the dispatch chain, not plan content.
- All paths resolve under this fixture root.
- One intentionally-questionable decision in the produced plan so `cast-plan-review`
  has at least one issue to surface in the chain test.

## Examples
- A `cast-detailed-plan` dry-run reads `requirements.human.md`, writes
  `docs/plan/<date>-b3-minimal-goal-fixture.md`.
- A `cast-plan-review` dry-run reads that plan and, in the chain test,
  appends a `## Decisions` appendix per B2 single-Write contract.
