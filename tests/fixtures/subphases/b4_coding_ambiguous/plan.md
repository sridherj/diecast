# Sub-phase b4_coding_ambiguous (fixture)

> Synthetic coding sub-phase used by `tests/test_b4_review_delegation.py`.
> Verification mentions tests and source paths, so it classifies as coding,
> but the paired stub payload at
> `tests/fixtures/cast_review_code_payloads/low_confidence.json` returns a
> single `confidence: low` review issue. The runner should NOT auto-apply;
> the issue must land in `<plan_path>.followup.md`.

## Objective

Edit `b4_ambiguous_target.py` introducing a debatable naming choice that
reviewers will flag with low confidence.

## Detailed Steps

1. Write `b4_ambiguous_target.py` containing a function named `do_thing`.

## Verification

- `pytest tests/test_b4_review_delegation.py::test_b4_low_confidence_goes_to_followup -v`
- After the runner finishes, `plan.md.followup.md` exists with the
  low-confidence issue recorded; the source file is unchanged.
