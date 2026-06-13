# Sub-phase 4: FR-007 Read-Only Guard + Parser/Version Tests

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase1/_shared_context.md` before starting.

## Objective

Lock everything Phase 1 built behind regression tests — this is the most important sub-phase (the plan
puts ~30–40% of the phase's weight here). Freeze the fixture, pin the parser's typed-block output
(counts/order/refs), prove parse + snapshot never mutate the file (FR-007: sha256 before == after AND
`bin/cast-spec-checker` stays exit-0 on the file), and pin the version-snapshot/hash behavior including the
`UNIQUE` violation and a grammar-bridge smoke test that fails loudly if the checker is moved/renamed.

## Dependencies

- **Requires completed:** sp2a (parser + hashing + grammar bridge), sp2b (tables + migration), sp3
  (version service).
- **Assumed codebase state:** `requirements_render` importable; three thin-spine tables exist;
  `requirement_version_service` works; `cast-server/tests/fixtures/` exists.

## Scope

**In scope:**
- Freeze the goal's `refined_requirements.collab.md` as a fixture under `tests/fixtures/`.
- `cast-server/tests/test_requirements_parser.py` — typed-block expectations + the two plan-review
  positive tests (Decision #3 unknown-H2, Decision #4 multi-line bullet grouping).
- `cast-server/tests/test_fr007_readonly_guard.py` — byte-identity + spec-checker-clean.
- `cast-server/tests/test_requirement_versions.py` — snapshot/hash pinning + `UNIQUE` violation +
  grammar-bridge smoke test.
- A final `/cast-pytest-best-practices` delegation over the three new test files.

**Out of scope (do NOT do these):**
- Editing the parser, the schema, or the service to make tests pass by changing behavior — if a test
  reveals a real bug, fix it in the owning sub-phase's file and note it, but do not redesign. The tests
  pin the *agreed* contract.
- Editing `bin/cast-spec-checker` (the guard runs it as a subprocess; it stays untouched).
- Comment/version behavior beyond what Phase 1 ships (no comment CRUD tests — Phase 4).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/fixtures/refine_requirements_v2/refined_requirements.collab.md` | Create (frozen copy) | Does not exist |
| `cast-server/tests/test_requirements_parser.py` | Create | Does not exist |
| `cast-server/tests/test_fr007_readonly_guard.py` | Create | Does not exist |
| `cast-server/tests/test_requirement_versions.py` | Create | Does not exist |

## Detailed Steps

### Step 4.1: Freeze the fixture

```bash
mkdir -p cast-server/tests/fixtures/refine_requirements_v2
cp goals/refine-requirements-v2/refined_requirements.collab.md \
   cast-server/tests/fixtures/refine_requirements_v2/refined_requirements.collab.md
```
This is a FROZEN copy — the live goal file keeps evolving; the frozen copy keeps the pinned counts stable.
Tests read the fixture, never the live goal file.

### Step 4.2: `test_requirements_parser.py` — typed-block expectations

Parse the fixture via `parse_requirements_file(FIXTURE)` and assert:

- **Counts (exact):** 1 `INTENT`, 7 `USER_STORY` (US1–US7), 20 `FR` (FR-001–FR-020), 6 `SC` (SC-001–SC-006),
  7 `CONSTRAINT`, 6 `SCOPE`, 1 `DIRECTIONAL`, 6 `OPEN_QUESTION`.
  > Before hard-coding these, run the parser against the frozen fixture once and confirm the actual counts
  > match the plan's expectations. The plan's numbers are the spec; if the frozen fixture yields different
  > counts, the parser (sp2a) has a mapping bug — flag it to sp2a, do NOT silently rewrite the expected
  > numbers to whatever the parser emits. The whole point of the pin is to catch that.
- **Order:** blocks are in source order (`line_start` strictly non-decreasing).
- **Refs:** `USER_STORY` refs are `US1..US7`; `FR` refs are `FR-001..FR-020`; `SC` refs are `SC-001..SC-006`.
- **Front matter / title / preamble:** `front_matter` is a dict with the header keys (e.g. status,
  confidence); `title` is the H1 text; `preamble` is the blockquote between H1 and the first H2.
- **`unrecognized_sections == ()`** for the clean fixture.
- **Bounds:** every block's `(line_start, line_end)` is within file bounds and `line_start <= line_end`,
  monotonically ordered.
- **Decision #3 — unknown-H2 positive test:** feed `parse_requirements()` a tiny in-string doc containing
  one unrecognized H2 (e.g. `## Appendix\n\nsome text`). Assert that exact heading text appears in
  `unrecognized_sections` AND that **no** `Block` was emitted for it. (The `== ()` assertion above only
  proves the empty case; this proves the zero-silent-failure capture path Phase 3a consumes.)
- **Decision #4 — multi-line bullet grouping test:** the fixture's `Constraints` bullets are multi-line
  (`- **bold lead:**` + wrapped continuation). Pick one known multi-line Constraint and assert its
  `Block.body` contains text from a **continuation** line (not just line 1) and `line_end > line_start`;
  assert an indented sub-bullet does **not** start a new block (count stays 7). Guards against a naive
  line-splitter that passes the count check while truncating each body to its first line.

### Step 4.3: `test_fr007_readonly_guard.py` — the file is never mutated

- Compute `sha256` of the fixture bytes BEFORE.
- Call `parse_requirements_file(FIXTURE)` and `requirement_version_service.create_snapshot(...)` against a
  tmp DB (`db_path=tmp_path / "guard.db"`, `init_db` it first; seed a `goals` row if the FK requires one —
  see sp3's note). Use the fixture's text as the snapshot content.
- Compute `sha256` of the fixture bytes AFTER. Assert `before == after` (parse + snapshot never touch the file).
- **Spec-checker subprocess:** run `bin/cast-spec-checker <FIXTURE>` as a subprocess and assert exit code 0.
  > ⚠️ The plan cites `tests/test_us7_spec_kit_shape.py` as the precedent for a `CHECKER` constant — **that
  > file does not exist in this repo.** Establish the pattern here:
  > ```python
  > import subprocess, sys
  > from pathlib import Path
  > REPO_ROOT = Path(__file__).resolve().parents[2]      # cast-server/tests -> repo root; VERIFY this depth
  > CHECKER = REPO_ROOT / "bin" / "cast-spec-checker"
  > def test_checker_clean_on_fixture():
  >     r = subprocess.run([sys.executable, str(CHECKER), str(FIXTURE)], capture_output=True, text=True)
  >     assert r.returncode == 0, r.stderr or r.stdout
  > ```
  > Print/verify `REPO_ROOT` and `CHECKER.exists()` once. `cast-server/tests/` is depth `parents[2]` to the
  > repo root — confirm before relying on it. The checker is executable; invoking via `sys.executable` is
  > safest if its shebang environment is uncertain (test both `[CHECKER, FIXTURE]` and `[sys.executable,
  > CHECKER, FIXTURE]` and keep whichever runs cleanly).

### Step 4.4: `test_requirement_versions.py` — snapshot/hash pinning + grammar smoke

Against a tmp DB (`init_db` first; seed a `goals` row if needed):
- **v1 insert:** `create_snapshot(slug, "A")` → version 1, status 'current'.
- **identical-content no-op:** `create_snapshot(slug, "A")` again → same version 1 (no new row);
  `len(list_versions(slug)) == 1`.
- **changed-content → v2:** `create_snapshot(slug, "B")` → version 2 'current'; the v1 row is now
  'archived'; `get_current(slug)['version'] == 2`.
- **`UNIQUE(goal_slug, version)` violation raises:** attempt a direct duplicate `(goal_slug, version)`
  insert (bypassing the service, straight SQL) and assert it raises `sqlite3.IntegrityError`.
- **`content_hash` determinism:** `content_hash("X") == content_hash("X")` and differs for different input.
- **Grammar-bridge smoke test:** `from cast_server.requirements_render import spec_grammar as g; assert
  g.US_HEADING_RE.match("### US1 — Foo")`. This fails loudly in CI if `bin/cast-spec-checker` is
  moved/renamed/breaks the importlib bridge (the documented Med risk).

### Step 4.5: Delegate test polish

→ **Delegate:** `/cast-pytest-best-practices` — over the three new files (`test_requirements_parser.py`,
`test_fr007_readonly_guard.py`, `test_requirement_versions.py`). Pass the file paths and ask it to check
fixture usage, parametrization, assertion-message quality, and naming.
→ **Review** the delegation output: apply only changes that don't weaken the pinned assertions (counts,
byte-identity, exit-0, UNIQUE-raises must stay strict). Reject any "simplification" that loosens a pin.

## Verification

### Automated Tests (permanent)
- `cd cast-server && uv run pytest tests/test_requirements_parser.py tests/test_fr007_readonly_guard.py tests/test_requirement_versions.py -v` — all green.
- `cd cast-server && uv run pytest tests/test_schema_migration.py` — still green (sp2b's tests unaffected).

### Validation Scripts (temporary)
- `sha256sum cast-server/tests/fixtures/refine_requirements_v2/refined_requirements.collab.md` before and
  after a full `pytest` run → identical (nothing mutates the fixture).
- `git status --short cast-server/tests/fixtures/` after the run → clean (no fixture churn).

### Manual Checks
- The expected counts in `test_requirements_parser.py` match the plan's numbers (1/7/20/6/7/6/1/6), and the
  parser actually produces them against the frozen fixture (not numbers reverse-engineered from a buggy parser).
- The FR-007 guard asserts `before == after` on raw bytes AND a clean `cast-spec-checker` exit.
- The grammar smoke test imports through `spec_grammar`, so a moved checker fails here first.

### Success Criteria
- [ ] Fixture frozen at `cast-server/tests/fixtures/refine_requirements_v2/refined_requirements.collab.md`.
- [ ] `test_requirements_parser.py`: exact counts, order, refs, front-matter/title/preamble,
      `unrecognized_sections == ()`, bounds — plus Decision #3 (unknown-H2 positive) and Decision #4
      (multi-line bullet grouping) tests.
- [ ] `test_fr007_readonly_guard.py`: sha256 before == after across parse + snapshot; `cast-spec-checker`
      exits 0 on the fixture (subprocess).
- [ ] `test_requirement_versions.py`: v1 / idempotent no-op / v2-with-archive / `UNIQUE`-raises /
      `content_hash` determinism / grammar-bridge smoke.
- [ ] `/cast-pytest-best-practices` ran over the three files; its safe suggestions applied, pins preserved.
- [ ] Full `pytest` run leaves the fixture bytes unchanged.

## Execution Notes

- **The whole phase's correctness rides on these pins.** If a count is off, the bug is in sp2a's mapping —
  fix it there and re-run; do not "make the test pass" by editing the expected number.
- The FK seeding question (does `create_snapshot` need a `goals` row to exist first?) surfaces here. Mirror
  how existing service tests seed their parent rows; sp3's validation note flags this. If FK enforcement is
  off in the test DB, no seed is needed — confirm which, and seed for safety.
- Use `tmp_path`-based DBs for every DB test (never the real dev DB). `init_db(tmp_path / "x.db")` first.
- **Spec-linked files:** none — these are new test files. But the FR-007 guard is, in spirit, the
  enforcement of `cast-init-conventions.collab.md`/FR-007 (file byte-canonical); keep it strict.
