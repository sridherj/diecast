# Sub-phase 2c: Two-Level Family-Aware Checker (`bin/cast-spec-checker`)

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase2/_shared_context.md` before starting.
> Source: Work Package D of `docs/plan/2026-06-11-refine-requirements-v2-phase2-classification.md`.

## Objective

Restructure `bin/cast-spec-checker` rule application into **two levels of inspection** (owner
Decision #1): Level 1 generic (always runs), Level 2 family-specific (selected by a new `--family
<value>` CLI flag). With no `--family` flag, the checker behaves **byte-for-byte as today** — product
specs in `docs/specs/` and pre-v2 refined docs keep working untouched. Level 2 applies the per-family
required-section profile + family assertions, and crucially makes the Template-Enforcer guard a
permanent regression test: a padded `random_idea` doc with empty US/FR/SC tables FAILS.

## Dependencies
- **Requires completed:** sp1 (`families.py` — `REQUIRED_SECTIONS_BY_FAMILY` is the source the
  checker **mirrors**; the pin test compares against it).
- **Assumed codebase state:** `bin/cast-spec-checker` exists (~11.5 KB) with today's full-spec
  `REQUIRED_SECTIONS` path; Phase 1's `spec_grammar.py` importlib bridge re-exports its grammar
  regexes and `_section_spans`.
- **Parallel with:** sp2a, sp2b. **Shared-file caution:** sp2c and sp2a both run `bin/generate-skills`
  — see Execution Notes.

## Scope

**In scope:**
- Add the `--family <value>` CLI flag and split rule application into Level 1 / Level 2.
- A **mirrored** (NOT imported) copy of `REQUIRED_SECTIONS_BY_FAMILY` inside the checker.
- Level 2 family assertions (empty-section ERRORs, missing-Evidence ERRORs, Directional WARNs).
- A fixture matrix: one minimal VALID doc per family + the padded `random_idea` fixture that must FAIL.
- A pin test asserting the mirrored mapping == `families.py`'s (FULL mapping, not just keys).
- Update `agents/cast-spec-checker/cast-spec-checker.md`; re-run `bin/generate-skills`.

**Out of scope (do NOT do these):**
- **Touching the grammar regexes or `_section_spans`** — they are re-exported by `spec_grammar.py`
  and MUST keep working unchanged (a Phase 1 test imports the bridge; it stays green). The two-level
  change touches `REQUIRED_SECTIONS` handling **only**.
- **Importing `families.py`** into the checker — it is a portable stdlib-only linter that must run in
  CI / pre-commit where `cast-server` may not be importable. Keep the mirror (Decision D5).
- Adding a YAML front-matter reader to the checker — family comes from the `--family` flag, NOT from
  parsing front-matter (Decision D1).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `bin/cast-spec-checker` | Modify | Exists; full-spec `REQUIRED_SECTIONS` path; frozen grammar regexes |
| `agents/cast-spec-checker/cast-spec-checker.md` | Modify | Exists; documents shape rules |
| `cast-server/tests/test_spec_checker_family.py` | Create | Does not exist (family tests + pin test) |
| `tests/fixtures/family_docs/*.md` | Create | Does not exist (one valid per family + padded-fail) |
| (generated) skill for `cast-spec-checker` | Regenerate via `bin/generate-skills` | Exists |

## Detailed Steps

### Step 2c.1: Add `--family <value>` and the two-level split
- **Level 1 (generic, always runs):** H1 present; US heading shape / `Priority:` / Independent-test
  / EARS grammar / FR–SC ID formats — **applied to whichever of those sections exist** (use the frozen
  re-exported regexes; do not modify them).
- **Level 2 (family, only when `--family` is passed):** apply
  `REQUIRED_SECTIONS_BY_FAMILY[family]` (the mirrored table) + the family assertions (Step 2c.3).
- **No `--family` flag → today's full-spec `REQUIRED_SECTIONS` path, byte-for-byte.** Existing checker
  tests must stay green untouched.

### Step 2c.2: Mirror `REQUIRED_SECTIONS_BY_FAMILY` (Decision D5)
- Paste the table from `_shared_context.md` as a literal dict in the checker (string keys = the
  `WorkFamily` values, since the checker can't import the enum).
- **Header comment (mandatory):** state that this mirror is deliberate — the checker is a portable
  stdlib-only linter that may run without `cast-server` importable; the pin test (Step 2c.4) keeps
  the mirror honest. Contrast with `bin/cast-classify-gate` (sp2b), which DOES import `families.py`.

### Step 2c.3: Level 2 family assertions
- `random_idea` / `personal_non_eng` → **ERROR** on empty/placeholder US/FR/SC/Out-of-Scope sections
  (present-with-real-content is fine — structure is *offered*, never auto-generated empty). This is
  the Template-Enforcer guard.
- `bug_fix` / `data_analysis` / `testing_qa` → **ERROR** on missing `## Evidence`.
- `data_analysis` / `personal_non_eng` → **WARN** (not error) on a present `## Directional` section
  (US1 S3 says omit, but genuine content shouldn't hard-fail).
- `pilot_poc` / `refactor_migration` → require `## Decisions` (per their profiles). **Do NOT** add a
  global Decisions requirement — the no-family/full-spec profile must not start requiring it (product
  specs would break — Suggested Revision #3).

### Step 2c.4: Update agent doc + regenerate
- Update `agents/cast-spec-checker/cast-spec-checker.md` to describe the two levels and the `--family`
  flag.
- `bin/generate-skills`; verify the regenerated `cast-spec-checker` skill reflects the new docs.

## Verification

### Automated Tests (permanent) — `cast-server/tests/test_spec_checker_family.py`
- **Fixture matrix** (`tests/fixtures/family_docs/`): one minimal VALID doc per `WorkFamily` passes
  `cast-spec-checker --family <value>` with zero errors.
- **The padded-`random_idea` fixture FAILS:** a `random_idea` doc carrying an empty Success Criteria
  table errors under `--family random_idea` (the Template-Enforcer guard as a permanent regression).
- **Missing-Evidence:** a `bug_fix` doc with no `## Evidence` errors under `--family bug_fix`.
- **Directional WARN:** a `data_analysis` doc with `## Directional` warns (does not error).
- **No-`--family` byte-for-byte:** a `docs/specs/*.collab.md` product spec (no classification
  front-matter) passes the same as before — run with no flag, assert identical findings.
- **Pin test (Decision D5):** import `REQUIRED_SECTIONS_BY_FAMILY` from `families.py` and assert the
  checker's mirrored copy equals it as a **FULL mapping** (every family's exact section tuple), not
  merely key presence — any drift in section *content* fails CI.
- **Grammar-bridge stays green:** confirm the Phase 1 test that imports `spec_grammar.py` still passes
  (run it explicitly).

→ **Delegate:** `/cast-pytest-best-practices` over the test file. Review output for compliance.

### Validation Scripts (temporary)
```bash
bin/cast-spec-checker --family random_idea tests/fixtures/family_docs/random_idea_padded.md ; echo "exit=$?"   # expect FAIL
bin/cast-spec-checker --family bug_fix tests/fixtures/family_docs/bug_fix_valid.md ; echo "exit=$?"            # expect PASS
bin/cast-spec-checker docs/specs/<some-existing-spec>.collab.md ; echo "exit=$?"                               # no flag → unchanged
uv run --project cast-server pytest cast-server/tests/test_spec_checker_family.py -v
```

### Manual Checks
- `git diff bin/cast-spec-checker` shows **no change** to grammar regexes or `_section_spans` — only
  `REQUIRED_SECTIONS` handling + the new flag/level dispatch.
- Both `bin/cast-spec-checker` and `bin/cast-classify-gate` headers state their (opposite) import
  policies.
- Existing pre-Phase-2 checker tests still pass (run the full checker test module).

### Success Criteria
- [ ] `--family <value>` flag added; Level 1/Level 2 split implemented.
- [ ] No `--family` → byte-for-byte today's behavior; existing checker tests green untouched.
- [ ] Mirrored `REQUIRED_SECTIONS_BY_FAMILY` + header rationale; pin test asserts full-mapping equality.
- [ ] Padded-`random_idea` fixture FAILS; one valid doc per family PASSES; Evidence/Directional rules work.
- [ ] Grammar regexes / `_section_spans` untouched; `spec_grammar.py` bridge test stays green.
- [ ] Agent doc updated; `bin/generate-skills` run.

## Execution Notes
- **`bin/generate-skills` coordination (parallel with sp2a):** idempotent and deterministic; if the
  skills tree looks partial after a concurrent run, re-run `bin/generate-skills`. Commit generated
  output with this sub-phase. (Same note in sp2a.)
- The most common mistake is "completing" the checker by adding a global `## Decisions` or `## Evidence`
  requirement to the full-spec path — DON'T. Those are family-scoped only; the no-family path is frozen.
- The checker must run **without** `cast-server` on the path (CI/pre-commit). Test it from a clean
  shell if possible. The pin test runs *with* `cast-server` available (it imports `families.py`), which
  is fine — the pin test is a CI guard, not part of the checker's runtime.

**Spec-linked files:** `bin/cast-spec-checker` is documented by `agents/cast-spec-checker/cast-spec-checker.md`
(updated here) and the new `cast-goal-classification.collab.md` (sp3b) records the two-level contract.
If a spec in `docs/specs/` lists `bin/cast-spec-checker` in `linked_files`, read it and verify its SAV
behaviors (the no-family path) are preserved.
