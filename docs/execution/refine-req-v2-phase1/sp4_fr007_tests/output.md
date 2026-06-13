# sp4_fr007_tests — Output

**Status:** completed. All success criteria met; 45/45 tests green; fixture byte-stable.

## What was built

| File | Action | Notes |
|------|--------|-------|
| `cast-server/tests/fixtures/refine_requirements_v2/refined_requirements.collab.md` | Created (frozen copy) | sha256 `851a2bd80738fdd5b7434d1051128a71bb98fe07026ee3ff47241e1905ea122d`. Frozen from the live goal file; tests read the fixture, never the live file. |
| `cast-server/tests/test_requirements_parser.py` | Created | Typed-block pins + Decision #3 + Decision #4. |
| `cast-server/tests/test_fr007_readonly_guard.py` | Created | Byte-identity + spec-checker subprocess. |
| `cast-server/tests/test_requirement_versions.py` | Created | Snapshot/hash/UNIQUE + grammar-bridge smoke. |

No production code (parser, schema, service, checker) was modified — the parser already
produced the plan's exact counts, so nothing needed fixing.

## Pin confirmation (counts verified against the frozen fixture, not reverse-engineered)

The parser was run against the frozen fixture once before hard-coding; actual counts matched
the plan's numbers exactly:

`INTENT=1, USER_STORY=7 (US1–US7), FR=20 (FR-001–FR-020), SC=6 (SC-001–SC-006),
CONSTRAINT=7, SCOPE=6, DIRECTIONAL=1, OPEN_QUESTION=6` — total 54 blocks.
`unrecognized_sections == ()`; blocks in source order.

## Test inventory

**`test_requirements_parser.py`** — per-kind count pins (parametrized), total count, source
order, in-bounds spans, US/FR/SC refs, front-matter dict (status/confidence), H1 title,
spec-maturity preamble, `unrecognized_sections == ()`. Decision #3: synthetic `## Appendix`
doc → heading recorded in `unrecognized_sections`, no block emitted. Decision #4: fixture's
first Constraint carries continuation-line text with `line_end > line_start` and count stays
7; synthetic doc proves an indented sub-bullet does NOT start a new block.

**`test_fr007_readonly_guard.py`** — sha256(fixture) identical before/after a parse +
`create_snapshot` round-trip against a tmp DB; checker discoverable at
`REPO_ROOT/bin/cast-spec-checker` (`REPO_ROOT = parents[2]`, verified); `cast-spec-checker`
exits 0 on the fixture via `subprocess.run([sys.executable, CHECKER, FIXTURE])`.

**`test_requirement_versions.py`** — v1-current insert; identical-content idempotent no-op
(`len(list_versions)==1`); changed content → v2 current + v1 archived + single current row;
`UNIQUE(goal_slug, version)` direct-insert raises `sqlite3.IntegrityError`; `content_hash`
determinism + 64-hex-char shape; grammar-bridge smoke (`spec_grammar.US_HEADING_RE` matches
`### US1 — Foo`) + all six canonical regexes exposed.

## FK seeding resolution

`PRAGMA foreign_keys=ON` is set in `get_connection`, and `requirement_versions.goal_slug`
FKs to `goals(slug)`. So DB tests **must** seed a `goals` row first. Each DB test seeds it
inline via `INSERT OR IGNORE INTO goals (slug, title, folder_path)` (mirrors conftest's
`ensure_goal`) on a `tmp_path` DB after `init_db`.

## Verification results

- `uv run pytest tests/test_requirements_parser.py tests/test_fr007_readonly_guard.py tests/test_requirement_versions.py tests/test_schema_migration.py -q` → **45 passed**.
- Fixture sha256 identical before and after a full pytest run (byte-stable).
- `git status --short cast-server/tests/fixtures/` → only the new untracked dir, no churn.

## Test polish (`/cast-pytest-best-practices`)

Ran the skill over the three files. Applied the one safe, non-pin-weakening change it flags:
added return-type annotations to the two fixtures (`parsed() -> ParsedRequirements`,
`db_path() -> Path`). All pins (counts, byte-identity, exit-0, UNIQUE-raises) kept strict;
no "simplification" that loosened an assertion was accepted. Re-ran: still 45 passed.

## Downstream notes

- Phase 4 (comment CRUD, `create_next()` open-comment gate) builds ON `create_snapshot`; the
  snapshot pins here are the contract it inherits.
- Phase 5 conflict detection must use `requirements_render.hashing.content_hash` (pinned for
  determinism here) — never reimplement sha256.
- The grammar-bridge smoke test is the canary: if `bin/cast-spec-checker` is moved/renamed,
  `test_requirement_versions.py` fails first.
