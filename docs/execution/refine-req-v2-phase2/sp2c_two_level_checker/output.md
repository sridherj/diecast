# sp2c — Two-Level Family-Aware Checker — Output

**Status:** ✅ Complete. All Detailed Steps executed, all verification run, every success
criterion met.

## What landed

`bin/cast-spec-checker` now applies **two levels of inspection**, selected by a new
`--family <value>` CLI flag. With no flag it behaves **byte-for-byte as before**.

- **Step 2c.1 — `--family` + two-level split.** New optional `--family <value>` flag.
  Level 1 (always): H1-title present (new rule `R8`), per-User-Story shape (R2–R4),
  FR/SC id formats + duplicates (R5), orphan `[NEEDS CLARIFICATION]` (R6), mixed-shape
  (R7). Level 2 (only with `--family`): the per-family required-section profile + family
  assertions. No flag → today's full-spec `REQUIRED_SECTIONS` path, unchanged.
- **Step 2c.2 — mirrored `REQUIRED_SECTIONS_BY_FAMILY`.** Pasted as a literal `dict[str,
  tuple[str, ...]]` (string keys = `WorkFamily` values) with a mandatory header comment
  stating the deliberate divergence (portable stdlib linter; the pin test keeps it honest)
  and contrasting it with `bin/cast-classify-gate`, which imports `families.py` on purpose.
- **Step 2c.3 — Level-2 family assertions:**
  - `F2` (error) — Template-Enforcer guard: `random_idea` / `personal_non_eng` error on an
    empty/placeholder `User Stories` / `Functional Requirements` / `Success Criteria` /
    `Out of Scope` section (present-with-real-content is fine). Empty markdown tables
    (header + separator, zero data rows) and placeholder tokens (TBD/TODO/N/A/…) count as
    empty.
  - `F1` (error) — missing required section; this delivers the "missing `## Evidence`"
    error for `bug_fix` / `data_analysis` / `testing_qa` and the `## Decisions` requirement
    for `pilot_poc` / `refactor_migration` via their profiles. **No global Decisions/Evidence
    requirement was added** to the no-family path.
  - `F3` (warning) — `data_analysis` / `personal_non_eng` warn (never error) on a present
    `## Directional` section.
- **Step 2c.4 — agent doc + skills.** `agents/cast-spec-checker/cast-spec-checker.md`
  documents the two levels, the `--family` flag, the family assertions, and the mirror/pin
  rationale. `bin/generate-skills` re-run; the regenerated `cast-spec-checker` SKILL.md
  reflects the new docs.

## Contracts for downstream sub-phases

- **`--family <value>` is the caller's contract** (Decision D1): the family comes from the
  flag, **never** from parsing front matter. sp3a's `cast-refine-requirements` integration
  must pass `--family <classification.family>` when validating the refined doc. Valid values
  are exactly the nine `WorkFamily` strings; an unknown value is an invocation error (exit 2).
- **Rule codes:** Level 1 generic = `R1`–`R8`; Level 2 family = `F1` (missing required
  section), `F2` (Template-Enforcer empty-section guard), `F3` (Directional WARN).
- **Exit codes unchanged:** `0` no errors (warnings OK), `1` ≥1 error, `2` invocation error.
  `--warn-only` still forces `0`.
- **The mirror is pinned** to `families.py` by
  `test_spec_checker_family.py::test_mirror_matches_families` (full-mapping equality). If
  sp1's `REQUIRED_SECTIONS_BY_FAMILY` ever changes, re-sync the literal dict in the checker
  or this test fails. sp3b's `cast-goal-classification.collab.md` should cite this two-level
  contract.

## Verification (all green)

- `cast-server/tests/test_spec_checker_family.py` — **19 passed**: per-family valid matrix
  (9), padded-`random_idea` FAIL, missing-Evidence FAIL, Directional WARN, unknown-family
  exit 2, no-family product-spec unchanged, no-family-does-not-apply-family-sections, the
  D5 pin test, and the `spec_grammar` bridge import.
- **No-family byte-for-byte confirmed empirically:** the new checker produces identical
  findings + exit codes to `HEAD`'s checker across all 28 `docs/specs/*.collab.md` + the
  frozen `refined_requirements.collab.md` fixture (0 diffs).
- **Existing checker suites green untouched:** `test_fr007_readonly_guard`,
  `test_requirement_versions` (grammar-bridge smoke), `test_families`,
  `test_requirements_parser` (135 passed), and `tests/test_us7_spec_kit_shape.py`
  (12 passed).
- **Frozen grammar regexes + `_section_spans` untouched** (verified via `git diff`); the
  Phase-1 `spec_grammar.py` importlib bridge still imports cleanly.
- `/cast-pytest-best-practices` applied to the test file (behavior-focused, AAA, enum used
  for coverage cross-check, helper return-type annotations added).

## Files

| File | Action |
|------|--------|
| `bin/cast-spec-checker` | Modified — `--family` flag, two-level split, mirror, F1/F2/F3, R8 |
| `agents/cast-spec-checker/cast-spec-checker.md` | Modified — two-level + `--family` docs |
| `cast-server/tests/test_spec_checker_family.py` | Created — 19 tests incl. D5 pin test |
| `tests/fixtures/family_docs/*.md` | Created — 9 valid + padded-fail + no-evidence + directional |
| `~/.claude/skills/cast-spec-checker/SKILL.md` | Regenerated via `bin/generate-skills` |

## Notes / non-blocking

- One pre-existing, unrelated e2e error surfaced in the broad sweep
  (`e2e/test_tier_delegation.py::test_mid_flight_session_isolation` — a `shutil.move`
  fixture-path `OSError`, same tmux-delegation context as that file's already-skipped flaky
  tests). Not caused by sp2c; the checker change touches no delegation code.
