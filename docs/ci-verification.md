# Anonymization-lint CI Verification

Phase-1.3 Gate **G1.3.a** requires that the planted-fixture branch
produces a **real** CI failure — not "we wired the YAML, trust us."
This page captures that ritual.

## Workflow

- Path: `.github/workflows/anonymization-lint.yml`
- Triggers: `push`, `pull_request`
- Runner: `ubuntu-latest`, Python 3.11 with `cache: "pip"` (D10).
- Steps: checkout → setup-python → `pip install pytest` →
  `bin/lint-anonymization` → `bin/audit-interdependencies` → `pytest tests/`.

## CI badge (for 1.4 README, per D1)

Embed in `README.md`:

```markdown
[![Anonymization Lint](https://github.com/sridherj/diecast/actions/workflows/anonymization-lint.yml/badge.svg)](https://github.com/sridherj/diecast/actions/workflows/anonymization-lint.yml)
```

Sub-phase 1.4 may opt out per D1; the badge URL is captured here for
copy-paste either way.

## Initial main-branch run (post-1.3 commit)

| Field | Value |
|-------|-------|
| Run ID | 25138134864 |
| Trigger | `push` to `main` |
| Commit | `feat(ci): anonymization lint + audit-stub + planted-fixture infra` |
| Result | success (13s) |
| Steps | all green: lint, audit-stub, pytest (16 tests) |
| Date  | 2026-04-29 |

## Planted-fixture ritual (G1.3.a)

### What we did

1. Branched `test/fixture-sj-leak` off `main`.
2. Added `tests/fixtures/planted/leaked.md` containing one line:
   the literal initials-leak sentence per the spec
   (`<initials> asked me to ship Diecast.`).
3. Pushed the branch.
4. Opened draft PR [#1](https://github.com/sridherj/diecast/pull/1).
5. Observed CI failing on both the `push` and `pull_request` runs.
6. Captured the failure log (below).
7. Closed the PR.
8. Deleted the remote branch and the fixture file.
9. Confirmed `main` is still green.

### Captured failure

PR run: <https://github.com/sridherj/diecast/actions/runs/25138170301>

Truncated step log from `Run bin/lint-anonymization`:

```
1 hit(s) in 31 file(s) (0.03s)
tests/fixtures/planted/leaked.md:1: matched pattern '\bSJ\b' — anonymization rule X violated. See CONTRIBUTING.md > Anonymization.
##[error]Process completed with exit code 1.
```

The lint emits one message per hit in the spec'd format
(`<file>:<line>: matched pattern '<pattern>' — anonymization rule X
violated. See CONTRIBUTING.md > Anonymization.`) and exits 1, which
fails the `lint` job and therefore the workflow as a whole.

### Cleanup confirmation

- Draft PR #1: closed (verified via `gh pr close 1`).
- Remote branch `test/fixture-sj-leak`: deleted (`git push origin
  --delete test/fixture-sj-leak`).
- Local branch `test/fixture-sj-leak`: deleted (`git branch -D`).
- Fixture file `tests/fixtures/planted/leaked.md`: never landed on
  `main`; the entire `tests/fixtures/planted/` directory does not
  exist on `main`.

### Gate verdict

Gate **G1.3.a passes**. The lint catches a planted leak in CI with a
clear, line-anchored failure message; cleanup is complete; `main`
remains green.

## Implementation note: fixture-dir exclusion

The Phase-1.3 spec listed both `tests/fixtures/forbidden/` and
`tests/fixtures/planted/` as default-excluded by the lint, while also
requiring the planted fixture (which lands under
`tests/fixtures/planted/`) to produce a real CI failure on push. Those
two requirements are mutually exclusive: if `planted/` is excluded by
default, the planted commit cannot fail CI.

Resolution (favoring G1.3.a, the load-bearing gate):

- `tests/fixtures/forbidden/` is default-excluded — its contents are
  pattern-coverage canaries that should fire only with
  `--include-fixtures`.
- `tests/fixtures/planted/` is **not** excluded — it is the canonical
  location for ad-hoc planted leaks that must trigger CI on commit.

The `bin/lint-anonymization` source contains a comment documenting
this rationale next to `DEFAULT_SKIP_DIRS`. The pytest case
`test_default_excludes_forbidden_fixture_dir` exercises the
`forbidden/` exclusion only; no planted/ exclusion test exists.
