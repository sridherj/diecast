# Sub-phase 1: Foundation — schema migration + helpers + sp1 verification

> **Pre-requisite:** Read
> `docs/execution/cast-subagent-and-skill-capture/_shared_context.md` before
> starting.
>
> **Spike A is settled.** Do NOT re-spike. Empirical payload shapes live at
> `goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md` and are
> authoritative. There is no `parent_session_id`; use `claude_agent_id`.

## Outcome

`agent_runs` has TWO new columns: `skills_used TEXT DEFAULT '[]'` AND
`claude_agent_id TEXT`. A new partial index
`idx_agent_runs_claude_agent_id ON agent_runs(claude_agent_id) WHERE
claude_agent_id IS NOT NULL` covers `SubagentStop`'s exact-match closure
path. The pre-existing composite `idx_agent_runs_session_status ON
agent_runs(session_id, status)` already covers parent-resolution lookups —
no new single-column session index is added. The `system-ops` goal is
auto-seeded (already shipped in `_seed_system_goals`) so sibling and this
plan can write rows without FK violations; sp1 keeps the idempotency test
as the lock. SQLite 3.9+ is enforced at startup so `record_skill` can rely
on `json_insert(... '$[#]' ...)` without fallback. The shared cast-name
pattern AND the input-source discriminator constants live in dedicated
modules for downstream reuse. `agent_service` exposes two new resolvers:
`resolve_parent_for_subagent(session_id)` and
`resolve_run_by_claude_agent_id(claude_agent_id)`.

## Dependencies

- **Requires completed:** None.
- **Assumed codebase state:** sibling shipped — `user_invocation_service.py`
  exists; `_seed_system_goals` already in `_run_migrations()`; composite
  `idx_agent_runs_session_status` already exists; `agent_runs.session_id`
  column exists and is populated by sibling's `register()`.

## Estimated effort

1 session.

## Scope

**In scope:**

- Schema migration: add BOTH `skills_used` AND `claude_agent_id` columns
  to `agent_runs` in `db/schema.sql` and `db/connection.py::_run_migrations()`.
- New partial index `idx_agent_runs_claude_agent_id`.
- SQLite 3.9+ startup check in `db/connection.py::get_connection()`.
- Add `skills_used: list[dict] = []` AND `claude_agent_id: str | None =
  None` to `models/agent_run.py::AgentRun`. Update `session_id` docstring.
- New module `cast-server/cast_server/cli/_cast_name.py` with
  `CAST_NAME_BODY`, `PROMPT_PATTERN`, `AGENT_TYPE_PATTERN`. Refactor
  `hook_handlers.py` to import `PROMPT_PATTERN`.
- New module `cast-server/cast_server/services/_invocation_sources.py`
  with `USER_PROMPT`, `SUBAGENT_START`, `source_filter_clause()`. Refactor
  sibling `user_invocation_service.complete()` to use the helper.
- `agent_service.py`: add `resolve_parent_for_subagent(session_id)` AND
  `resolve_run_by_claude_agent_id(claude_agent_id)`. Add `claude_agent_id`
  kwarg to `create_agent_run` (so sp2 can write it at INSERT time).
- Tests: `test_schema_migration.py`, `test_cast_name_pattern.py`,
  `test_invocation_sources.py`, `test_system_ops_seed_idempotent.py`,
  `test_sqlite_version_check.py`, plus resolver tests in
  `test_agent_service.py`.

**Out of scope (do NOT do):**

- Implement `_seed_system_goals` — already shipped. Only write the
  idempotency test.
- Add a single-column `idx_agent_runs_session_id` — composite index already
  covers the parent-resolution lookup pattern.
- Add a `claude_session_id` column — `session_id` IS the Claude Code
  session id (populated by sibling's `register()` line 49).
- Re-run Spike A. The notes file is authoritative; trust the field names.
- New `subagent_invocation_service.py` (sp2).
- HTTP endpoints (sp2).
- Hook handlers / `install_hooks` changes (sp3).
- UI changes (sp4).

## Files to Create/Modify

| File | Action | Notes |
|------|--------|-------|
| `cast-server/cast_server/db/schema.sql` | Modify | Add `skills_used TEXT DEFAULT '[]'` AND `claude_agent_id TEXT` columns to `agent_runs`. |
| `cast-server/cast_server/db/connection.py` | Modify | Two `ALTER TABLE` blocks in `_run_migrations()`; new `CREATE INDEX IF NOT EXISTS idx_agent_runs_claude_agent_id ON agent_runs(claude_agent_id) WHERE claude_agent_id IS NOT NULL`; SQLite 3.9+ check in `get_connection()`. |
| `cast-server/cast_server/models/agent_run.py` | Modify | Add `skills_used: list[dict] = []` AND `claude_agent_id: str | None = None`. Update `session_id` docstring. |
| `cast-server/cast_server/cli/_cast_name.py` | Create | `CAST_NAME_BODY`, `PROMPT_PATTERN`, `AGENT_TYPE_PATTERN`. |
| `cast-server/cast_server/cli/hook_handlers.py` | Modify | Import `PROMPT_PATTERN` from `_cast_name`; delete local definition. |
| `cast-server/cast_server/services/_invocation_sources.py` | Create | `USER_PROMPT`, `SUBAGENT_START`, `source_filter_clause()`. |
| `cast-server/cast_server/services/user_invocation_service.py` | Modify | sibling `complete()` uses `source_filter_clause()` + `USER_PROMPT`. |
| `cast-server/cast_server/services/agent_service.py` | Modify | Add `resolve_parent_for_subagent(session_id)` AND `resolve_run_by_claude_agent_id(claude_agent_id)`. Add `claude_agent_id` kwarg to `create_agent_run` so sp2 can populate at INSERT time. |
| `cast-server/tests/test_schema_migration.py` | Create | **Migration cluster — consolidated** (Plan-review decision 2). Tests: fresh-DB and live-DB migration paths; both new columns present; new partial index `idx_agent_runs_claude_agent_id` present; old composite `idx_agent_runs_session_status` untouched; system-ops seed idempotent under fresh / pre-existing-DB / pre-existing-goal cases (`test_system_ops_seed_idempotent`); SQLite 3.9+ startup check (`test_sqlite_version_check_rejects_old_versions`). |
| `cast-server/tests/test_cast_name_pattern.py` | Create | Positive/negative cases for both regexes (`PROMPT_PATTERN`, `AGENT_TYPE_PATTERN`). |
| `cast-server/tests/test_invocation_sources.py` | Create | Constant values + SQL clause shape. |
| `cast-server/tests/test_agent_service.py` | Modify (or create) | Tests for both new resolvers — `resolve_parent_for_subagent` and `resolve_run_by_claude_agent_id` (see Step 1.8). |
| `cast-server/tests/conftest.py` | **Reuse, do NOT fork** | Existing fixtures (`isolated_db`, `ensure_goal`) cover most setup. New tests in this sp use them rather than rolling new in-memory DB scaffolding. (Plan-review decision 4.) |

## Detailed Steps

### Step 1.1: Schema migration

Edit `cast-server/cast_server/db/schema.sql` — add both columns to the
`agent_runs` table definition:

```sql
skills_used TEXT DEFAULT '[]',
claude_agent_id TEXT
```

In `_run_migrations()` (`cast-server/cast_server/db/connection.py`), follow
the existing `try/except sqlite3.OperationalError` pattern for both:

```python
try:
    conn.execute("ALTER TABLE agent_runs ADD COLUMN skills_used TEXT DEFAULT '[]'")
except sqlite3.OperationalError:
    pass  # column already exists

try:
    conn.execute("ALTER TABLE agent_runs ADD COLUMN claude_agent_id TEXT")
except sqlite3.OperationalError:
    pass  # column already exists
```

Add the new partial index for the closure path (also wrap in try/except
for migration idempotency):

```python
conn.execute(
    "CREATE INDEX IF NOT EXISTS idx_agent_runs_claude_agent_id "
    "ON agent_runs(claude_agent_id) WHERE claude_agent_id IS NOT NULL"
)
```

**Do NOT add a single-column `idx_agent_runs_session_id`.** The composite
`idx_agent_runs_session_status` already covers session_id-keyed lookups.
**Do NOT add a `claude_session_id` column** — `session_id` is already the
Claude Code session id, populated by `user_invocation_service.register()`
line 49.

### Step 1.2: System-ops seed verification (test only — implementation already shipped)

`_seed_system_goals(conn)` already exists in `_run_migrations()` and uses
`INSERT OR IGNORE` on `slug='system-ops'` (with `folder_path='system-ops'`
to satisfy the NOT NULL column). Live DB row is also seeded out-of-band.

Write `cast-server/tests/test_system_ops_seed_idempotent.py` with three
cases:

- Fresh DB → goal exists after `_run_migrations()`.
- Pre-existing DB without goal → goal added, no error.
- Pre-existing goal → no error, no duplicate (count remains 1).

### Step 1.3: SQLite 3.9+ startup check

In `cast-server/cast_server/db/connection.py:get_connection()`, after the
`PRAGMA` calls, assert `sqlite3.sqlite_version_info >= (3, 9, 0)` and
`SystemExit` with a clear message:

```
cast-server requires SQLite 3.9+ for record_skill's
json_insert(... '$[#]' ...) semantics; got <ver>.
```

3.9 was released in 2015 — every reasonable system has it; the floor is a
contract, not a fallback dance.

Test:
`cast-server/tests/test_sqlite_version_check.py::test_sqlite_version_check_rejects_old_versions`
— monkeypatch `sqlite3.sqlite_version_info` to `(3, 8, 0)`, assert
`SystemExit` at `get_connection()` call.

### Step 1.4: Model update

`cast-server/cast_server/models/agent_run.py:AgentRun` — add:

- `skills_used: list[dict] = []`
- `claude_agent_id: str | None = None`

Existing `session_id: str | None = None` stays. Update docstring(s) to
note that:

- `session_id` carries the Claude Code (parent main-loop) session id —
  shared by every subagent in the session.
- `claude_agent_id` carries the Claude Code per-subagent runtime id from
  `SubagentStart.agent_id`. NULL for user-invocation rows and CLI
  dispatches.

### Step 1.5: DRY extraction — `_cast_name.py`

Create `cast-server/cast_server/cli/_cast_name.py`:

```python
import re

CAST_NAME_BODY = r"cast-[a-z0-9-]+"
PROMPT_PATTERN     = re.compile(rf"^\s*/({CAST_NAME_BODY})")     # slash-prefixed user prompts
AGENT_TYPE_PATTERN = re.compile(rf"^{CAST_NAME_BODY}$")          # bare subagent_type names
```

Update `hook_handlers.py` to import `PROMPT_PATTERN` from this module
(delete the local definition).

New `cast-server/tests/test_cast_name_pattern.py` covers both regexes:

- Positive: `cast-foo`, `cast-foo-bar-baz`.
- Negative: `Cast-foo`, `cast_foo`, `cast-`, `not-cast-foo`.

Existing `test_cli_hook.py` tests must still pass after the import
refactor.

### Step 1.6: Invocation sources module

Create `cast-server/cast_server/services/_invocation_sources.py`:

```python
USER_PROMPT = "user-prompt"
SUBAGENT_START = "subagent-start"

def source_filter_clause() -> str:
    return "json_extract(input_params, '$.source') = ?"
```

Both `user_invocation_service.py` and the new
`subagent_invocation_service.py` (sp2) import from here. Update sibling's
`complete()` (line 86) to use `source_filter_clause()` + the
`USER_PROMPT` constant.

Tests in `cast-server/tests/test_invocation_sources.py` cover:

- The constant values are the literal strings `"user-prompt"` and
  `"subagent-start"`.
- The SQL clause shape is exactly
  `json_extract(input_params, '$.source') = ?`.
- Sibling's existing `complete()` tests must still pass after the
  refactor.

### Step 1.7: `agent_service.create_agent_run` claude_agent_id surface

Add a `claude_agent_id: str | None = None` kwarg to `create_agent_run` and
include it in the INSERT statement. sp1 only adds the surface; sp2 starts
populating it. Existing call sites (sibling user_invocation_service,
HTTP-dispatched runs) pass nothing and the column stays NULL.

### Step 1.8: `agent_service` resolvers (TWO)

Add to `cast-server/cast_server/services/agent_service.py`:

```python
def resolve_parent_for_subagent(
    session_id: str,
    db_path: str | None = None,
) -> str | None:
    """Return id of the most-recent running cast-* agent_run in `session_id`, or None.

    SQL:
      SELECT id FROM agent_runs
       WHERE session_id = ?
         AND status = 'running'
         AND agent_name LIKE 'cast-%'
       ORDER BY started_at DESC
       LIMIT 1

    The `agent_name LIKE 'cast-%'` filter is contract: a non-cast subagent
    (e.g., user-dispatched `Explore`) MUST NOT become a parent of a later
    cast-* subagent.
    """

def resolve_run_by_claude_agent_id(
    claude_agent_id: str,
    db_path: str | None = None,
) -> str | None:
    """Return id of the agent_run whose claude_agent_id matches, or None.

    SQL:
      SELECT id FROM agent_runs
       WHERE claude_agent_id = ?
       ORDER BY started_at DESC
       LIMIT 1

    Used by SubagentStop to close the exact row. claude_agent_id is unique
    per subagent dispatch — single-row lookup.
    """
```

Tests (in `cast-server/tests/test_agent_service.py`):

- `test_resolve_parent_for_subagent_returns_none_when_no_row`
- `test_resolve_parent_for_subagent_returns_none_when_no_cast_row_but_other_rows_exist`
  (e.g. only an `Explore` row is running — must NOT be returned)
- `test_resolve_parent_for_subagent_returns_single_running_cast_row`
- `test_resolve_parent_for_subagent_returns_most_recent_when_multiple_running`
  (parent + nested subagent — most-recent-by-`started_at` wins)
- `test_resolve_parent_for_subagent_excludes_completed_rows`
  (stale parent guard via `status='running'`)
- `test_resolve_run_by_claude_agent_id_returns_none_when_missing`
- `test_resolve_run_by_claude_agent_id_returns_id_when_present`
- `test_resolve_run_by_claude_agent_id_defends_against_dup_returns_most_recent`
  (shouldn't happen but defend)

### Step 1.9: Run the test suites

```bash
cd cast-server && uv run pytest \
  tests/test_schema_migration.py \
  tests/test_cast_name_pattern.py \
  tests/test_invocation_sources.py \
  tests/test_system_ops_seed_idempotent.py \
  tests/test_sqlite_version_check.py \
  tests/test_agent_service.py \
  tests/test_cli_hook.py \
  tests/test_user_invocation_service.py \
  -v
```

All listed tests must pass. `test_cli_hook.py` and
`test_user_invocation_service.py` are included to catch sibling regressions
from the import / SQL refactors.

## Verification

### Automated Tests (permanent)

- `pytest cast-server/tests/test_schema_migration.py` green:
  - schema has BOTH `skills_used` AND `claude_agent_id` columns;
  - the new partial index `idx_agent_runs_claude_agent_id` exists;
  - the pre-existing composite `idx_agent_runs_session_status` is left
    intact (no new single-column `idx_agent_runs_session_id` added).
- Live-DB test inside `test_schema_migration.py`: copy
  `~/.cast/diecast.db` to a tmp path, restart cast-server pointing at it
  — migration is idempotent (no errors, no extra rows, both ALTERs and
  the index creation re-run cleanly).
- `pytest cast-server/tests/test_cast_name_pattern.py` green.
- Existing `test_cli_hook.py` tests still green after the import
  refactor.
- `pytest cast-server/tests/test_invocation_sources.py` green.
- Sibling `test_user_invocation_service.py` still green after sibling's
  `complete()` SQL is refactored to use `source_filter_clause()` +
  `USER_PROMPT`.
- `pytest cast-server/tests/test_system_ops_seed_idempotent.py` green:
  fresh DB → goal exists; pre-existing DB without goal → goal added;
  pre-existing goal → no error, no duplicate.
- `pytest cast-server/tests/test_sqlite_version_check.py::test_sqlite_version_check_rejects_old_versions`
  green: monkeypatch `sqlite3.sqlite_version_info` to `(3, 8, 0)`, assert
  `SystemExit` at `get_connection()` call.
- All resolver tests in `test_agent_service.py` (Step 1.8) green.

### Validation Artifacts (already in place — not reproduced in sp1)

- `goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md` —
  authoritative Spike A capture. **Do not modify.**

### Manual Checks

```bash
# Confirm both schema columns exist
sqlite3 ~/.cast/diecast.db "PRAGMA table_info(agent_runs);" \
  | grep -E '(skills_used|claude_agent_id)'
# Expected: two rows.

# Confirm the new partial index and the composite index both exist
sqlite3 ~/.cast/diecast.db ".indexes agent_runs" | grep -i -E '(session_status|claude_agent_id)'
# Expected: idx_agent_runs_session_status   AND   idx_agent_runs_claude_agent_id
# (and no idx_agent_runs_session_id — single-column session index NOT added)
```

### Success Criteria

- [ ] `agent_runs.skills_used` column exists, defaulting to `'[]'`.
- [ ] `agent_runs.claude_agent_id` column exists (TEXT, nullable).
- [ ] `idx_agent_runs_claude_agent_id` partial index exists; the existing
      composite `idx_agent_runs_session_status` is intact; no new
      single-column `idx_agent_runs_session_id` exists.
- [ ] `system-ops` goal row exists in DB; idempotent on re-migration.
- [ ] `get_connection()` SystemExits on SQLite < 3.9.
- [ ] `models/agent_run.py:AgentRun.skills_used` defaults to `[]`;
      `claude_agent_id` defaults to `None`. Docstrings updated.
- [ ] `_cast_name.py` exports `CAST_NAME_BODY`, `PROMPT_PATTERN`,
      `AGENT_TYPE_PATTERN`. `hook_handlers.py` imports `PROMPT_PATTERN`
      from it.
- [ ] `_invocation_sources.py` exports `USER_PROMPT`, `SUBAGENT_START`,
      `source_filter_clause()`. Sibling `complete()` uses them.
- [ ] `agent_service.resolve_parent_for_subagent` returns most-recent
      running cast-* row id (with `agent_name LIKE 'cast-%'` filter)
      or None.
- [ ] `agent_service.resolve_run_by_claude_agent_id` returns the
      matching row id or None.
- [ ] `agent_service.create_agent_run` accepts `claude_agent_id` kwarg
      and persists it on INSERT.
- [ ] All sp1 tests pass; sibling `test_cli_hook.py` and
      `test_user_invocation_service.py` still green.

## Design Review

- **Naming:** `skills_used` matches plural-noun convention (`artifacts`,
  `directories`, `rate_limit_pauses`). `claude_agent_id` deliberately
  avoids collision with `cast_server.models.agent_config.AgentConfig.agent_id`
  (which is the agent CONFIG folder name). `_invocation_sources.py`
  follows the leading-underscore convention for "internal-but-importable"
  modules used elsewhere in `services/`. ✓
- **Architecture:** migration via `_run_migrations()` mirrors all eight
  existing examples in `connection.py`. The seed step is one
  already-shipped call; sp1 only verifies. ✓
- **Spec consistency:** no impact on
  `cast-delegation-contract.collab.md` (file-based delegation outputs,
  unrelated to hook-tracking). No impact on
  `cast-output-json-contract.collab.md` (hook-created rows have no
  output.json). ✓
- **DRY:** `PROMPT_PATTERN` and `AGENT_TYPE_PATTERN` share
  `CAST_NAME_BODY` — single source of truth for "what counts as
  cast-*". Source discriminators share constants — typo-proof.
- **Error & rescue:** `resolve_parent_for_subagent` is the SOLE
  parent-resolution path (no `parent_session_id` to fall back on — it
  doesn't exist). Stale-parent guard is the `status='running'` filter;
  the `agent_name LIKE 'cast-%'` filter ensures non-cast subagents don't
  accidentally become parents. `resolve_run_by_claude_agent_id` is the
  SOLE closure path on `SubagentStop`. SQLite version check fails LOUD
  at startup so deployment surprises happen once, not per-skill.
- **Index choice:** composite `idx_agent_runs_session_status` (existing)
  covers parent-resolution (`session_id` + `status='running'` +
  `agent_name LIKE 'cast-%'` does the leftmost-prefix scan; `LIKE` is a
  SARG-able row-level filter). New partial index
  `idx_agent_runs_claude_agent_id WHERE claude_agent_id IS NOT NULL`
  covers closure path — partial because user-invocation rows never have
  it.

## Execution Notes

- **Spec-linked files:** sp1 doesn't touch any spec files yet — sp5
  authors the new spec.
- **Skill/agent delegation:** consider invoking
  `/cast-pytest-best-practices` after the initial test draft to catch
  structural issues. Skill output should be reviewed for fixture-scope
  and isolation findings.
- **Live DB caution:** the live-DB migration test in
  `test_schema_migration.py` MUST copy `~/.cast/diecast.db` to a tmp
  path before mutating. Never write directly to the user's real DB
  during tests.
- **Sibling-test regression check:** after the `PROMPT_PATTERN` import
  refactor in `hook_handlers.py`, run the full `test_cli_hook.py` suite
  to confirm no breakage. The regex IS the contract for `cast-*`
  detection; any subtle behavior change there breaks the sibling.
  Likewise after refactoring sibling `complete()` to use
  `source_filter_clause()`, run the full `test_user_invocation_service.py`
  suite.
- **No decision gate.** Spike A is settled. The notes file is
  authoritative for `SubagentStart`, `SubagentStop`, `PreToolUse(Skill)`
  field names. Trust it; do not re-spike.
