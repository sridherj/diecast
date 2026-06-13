# Bug Fix Fixture

## Intent

The refine endpoint returns a 500 when the writeup has no front matter; it
should fall back to an empty header instead of raising.

## Evidence

- Repro: POST a writeup with no leading `---` block.
- Stack trace points at `_split_front_matter` returning before the body is set.
- First seen in run `run_20260610_140002_ab12cd`.
