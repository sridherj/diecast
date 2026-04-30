# Sub-phase b4_coding_path_traversal (fixture)

> Synthetic coding sub-phase used by `tests/test_b4_review_delegation.py`.
> Plan-review Issue #11 mandated this fixture: ensures the runner refuses
> to apply a high-confidence Edit when the target path is outside the
> allowed roots (`goal_dir` and `docs/`).

## Objective

Edit `b4_path_traversal_target.py`. The paired stub payload at
`tests/fixtures/cast_review_code_payloads/path_traversal.json` returns a
`confidence: high` review issue whose `file` is `/etc/passwd`. The runner
must refuse the auto-Edit and record the rejection in
`<plan_path>.followup.md` with an "out-of-tree edit refused" message.

## Detailed Steps

1. Write `b4_path_traversal_target.py`.

## Verification

- `pytest tests/test_b4_review_delegation.py::test_b4_path_traversal_rejected -v`
- `<plan_path>.followup.md` exists and mentions "out-of-tree" or "refused".
- `/etc/passwd` (mocked in the test sandbox) is NOT modified.
