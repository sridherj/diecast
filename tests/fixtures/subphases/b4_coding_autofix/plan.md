# Sub-phase b4_coding_autofix (fixture)

> Synthetic coding sub-phase used by `tests/test_b4_review_delegation.py`.
> Creates a Python source file with one mechanical lint issue (missing trailing
> newline). The paired stub payload at
> `tests/fixtures/cast_review_code_payloads/autofix.json` returns a single
> `confidence: high` review issue that the runner should auto-apply via Edit.

## Objective

Write `b4_autofix_target.py` containing a function with a missing trailing
newline. The post-execution review classifies as **coding** because the
verification mentions tests and an Edit-tool action.

## Detailed Steps

1. Write the target file `b4_autofix_target.py` with intentional missing newline.

## Verification

- `pytest tests/test_b4_review_delegation.py::test_b4_coding_autofix -v`
- The target file gains a trailing newline after the runner processes the
  high-confidence review issue.
