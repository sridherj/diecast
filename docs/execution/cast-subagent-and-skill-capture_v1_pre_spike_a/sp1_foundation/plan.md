# Sub-phase 1: Foundation — payload spike + schema migration + system seeds

> **Pre-requisite:** Read
> `docs/execution/cast-subagent-and-skill-capture/_shared_context.md` before
> starting.

## Outcome

`agent_runs` has a new `skills_used TEXT DEFAULT '[]'` column. Parent
resolution is fast via the pre-existing composite index
`idx_agent_runs_session_status ON agent_runs(session_id, status)` — no new
index needed. The `system-ops` goal is auto-seeded (already shipped in
`_seed_system_goals`) so sibling and this plan can write rows without FK
violations; sp1 keeps the idempotency test as the lock. SQLite 3.9+ is enforced
at startup so `record_skill` can rely on `json_insert(... '$[#]' ...)` without
fallback. The shared cast-name pattern AND the input-source discriminator
constants live in dedicated modules for downstream reuse. The actual
`SubagentStart`, `SubagentStop`, and `PreToolUse(Skill)` payload shapes are
empirically captured and pinned in this sub-phase's notes.

## Dependencies

- **Requires completed:** None.
- **Assumed codebase state:** sibling shipped — `user_invocation_service.py`
  exists; `_seed_system_goals` already in `_run_migrations()`; composite
  `idx_agent_runs_session_status` already exists; `agent_runs.session_id` is
  populated.

## Estimated effort

1 session.

## Scope

**In scope:**

- Spike A: live capture of `SubagentStart`, `SubagentStop`,
  `PreToolUse(Skill)` payloads to `goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md`.
- Schema migration: add `skills_used` column to `agent_runs` in both
  `db/schema.sql` and `db/connection.py::_run_migrations()`.
- SQLite 3.9+ startup check in `db/connection.py::get_connection()`.
- Add `skills_used: list[dict] = []` to `models/agent_run.py::AgentRun`.
- New module `cast-server/cast_server/cli/_cast_name.py` with `CAST_NAME_BODY`,
  `PROMPT_PATTERN`, `AGENT_TYPE_PATTERN`. Refactor `hook_handlers.py` to import
  `PROMPT_PATTERN`.
- New module `cast-server/cast_server/services/_invocation_sources.py` with
  `USER_PROMPT`, `SUBAGENT_START`, `source_filter_clause()`. Refactor sibling
  `user_invocation_service.complete()` to use the helper.
- New `agent_service.py::resolve_run_by_session_id(session_id)` returning the
  most-recent running row id keyed on `session_id`.
- Tests: `test_schema_migration.py`, `test_cast_name_pattern.py`,
  `test_invocation_sources.py`, `test_system_ops_seed_idempotent`,
  `test_sqlite_version_check_rejects_old_versions`.

**Out of scope (do NOT do):**

- Implement `_seed_system_goals` — already shipped. Only write the
  idempotency test.
- Add a single-column `idx_agent_runs_session_id` — composite index already
  covers.
- Add a `claude_session_id` column — `session_id` IS the Claude Code session id.
- New `subagent_invocation_service.py` (sp2).
- HTTP endpoints (sp2).
- Hook handlers / install_hooks changes (sp3).
- UI changes (sp4).

## Files to Create/Modify

| File | Action | Notes |
|------|--------|-------|
| `cast-server/cast_server/db/schema.sql` | Modify | Add `skills_used TEXT DEFAULT '[]'` column to `agent_runs`. |
| `cast-server/cast_server/db/connection.py` | Modify | Add `ALTER TABLE` for `skills_used` in `_run_migrations()`; add SQLite 3.9+ check in `get_connection()`. |
| `cast-server/cast_server/models/agent_run.py` | Modify | Add `skills_used: list[dict] = []`. Update docstring on `session_id`. |
| `cast-server/cast_server/cli/_cast_name.py` | Create | `CAST_NAME_BODY`, `PROMPT_PATTERN`, `AGENT_TYPE_PATTERN`. |
| `cast-server/cast_server/cli/hook_handlers.py` | Modify | Import `PROMPT_PATTERN` from `_cast_name`; delete local definition. |
| `cast-server/cast_server/services/_invocation_sources.py` | Create | `USER_PROMPT`, `SUBAGENT_START`, `source_filter_clause()`. |
| `cast-server/cast_server/services/user_invocation_service.py` | Modify | sibling `complete()` uses `source_filter_clause()` + `USER_PROMPT`. |
| `cast-server/cast_server/services/agent_service.py` | Modify | Add `resolve_run_by_session_id(session_id) -> str | None`. |
| `cast-server/tests/test_schema_migration.py` | Create | Fresh-DB and live-DB migration tests. |
| `cast-server/tests/test_cast_name_pattern.py` | Create | Positive/negative cases for both regexes. |
| `cast-server/tests/test_invocation_sources.py` | Create | Constant values + SQL clause shape. |
| `cast-server/tests/test_system_ops_seed_idempotent.py` | Create | Fresh-DB / pre-existing-DB / pre-existing-goal cases. |
| `cast-server/tests/test_sqlite_version_check.py` | Create | `test_sqlite_version_check_rejects_old_versions`. |
| `goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md` | Create | Verbatim live captures from Spike A. |

## Detailed Steps

### Step 1.1: Spike A — live payload capture (DECISION GATE)

Add a temporary `/tmp/log-payload.sh` hook entry to this project's
`.claude/settings.json` for `SubagentStart`, `SubagentStop`, and `PreToolUse`.
Trigger one cast-* and one non-cast `Task()` plus one Skill invocation. Save
raw payloads verbatim to
`goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md`.

Confirm:
- (a) `parent_session_id` IS in `SubagentStart`.
- (b) `SubagentStop` carries `session_id` and any error/exit signal.
- (c) `PreToolUse` for `Skill` carries `session_id` and `tool_input.skill_name`.

**Decision gate:** if `parent_session_id` is missing or under a different key,
abort sp2's resolver design and revisit (see source plan's Risks).

Also validate (per Open Question O5): does `parent_session_id` equal the
**immediate** parent's session_id (not the root's)? If yes, nested attribution
is correct.

After Spike A is captured, REMOVE the temporary hook entries from
`.claude/settings.json` so they don't pollute later sub-phases.

### Step 1.2: Schema migration

Edit `cast-server/cast_server/db/schema.sql` — add `skills_used TEXT DEFAULT
'[]'` to the `agent_runs` table definition.

Add a corresponding block in `_run_migrations()`
(`cast-server/cast_server/db/connection.py`) following the existing
`try/except sqlite3.OperationalError` pattern:

```python
try:
    conn.execute("ALTER TABLE agent_runs ADD COLUMN skills_used TEXT DEFAULT '[]'")
except sqlite3.OperationalError:
    pass  # column already exists
```

**Do NOT add a new index.** The composite `idx_agent_runs_session_status`
already covers session_id-keyed lookups. **Do NOT add a `claude_session_id`
column** — `session_id` is already the Claude Code session id, populated by
`user_invocation_service.register()` line 49.

### Step 1.3: System-ops seed verification (test only — implementation already shipped)

`_seed_system_goals(conn)` already exists in `_run_migrations()` and uses
`INSERT OR IGNORE` on `slug='system-ops'` (with `folder_path='system-ops'` to
satisfy the NOT NULL column). Live DB row is also seeded out-of-band.

Write `cast-server/tests/test_system_ops_seed_idempotent.py` with three cases:
- Fresh DB → goal exists after `_run_migrations()`.
- Pre-existing DB without goal → goal added, no error.
- Pre-existing goal → no error, no duplicate (count remains 1).

### Step 1.4: SQLite 3.9+ startup check

In `cast-server/cast_server/db/connection.py:get_connection()`, after the
`PRAGMA` calls, assert `sqlite3.sqlite_version_info >= (3, 9, 0)` and
`SystemExit` with a clear message:

```
cast-server requires SQLite 3.9+ for record_skill's
json_insert(... '$[#]' ...) semantics; got <ver>.
```

3.9 was released in 2015 — every reasonable system has it; the floor is a
contract, not a fallback dance.

Test: `cast-server/tests/test_sqlite_version_check.py::test_sqlite_version_check_rejects_old_versions`
— monkeypatch `sqlite3.sqlite_version_info` to `(3, 8, 0)`, assert `SystemExit`
at `get_connection()` call.

### Step 1.5: Model update

`cast-server/cast_server/models/agent_run.py:AgentRun` — add `skills_used:
list[dict] = []`. Existing `session_id: str | None = None` (line 19) stays;
update the docstring to document that it now carries the Claude Code session
id.

### Step 1.6: DRY extraction — `_cast_name.py`

Create `cast-server/cast_server/cli/_cast_name.py`:

```python
import re

CAST_NAME_BODY = r"cast-[a-z0-9-]+"
PROMPT_PATTERN = re.compile(rf"^\s*/({CAST_NAME_BODY})")        # slash-prefixed user prompts
AGENT_TYPE_PATTERN = re.compile(rf"^{CAST_NAME_BODY}$")         # bare subagent_type names
```

Update `hook_handlers.py` to import `PROMPT_PATTERN` from this module (delete
the local definition).

New `cast-server/tests/test_cast_name_pattern.py` covers both regexes:
- Positive: `cast-foo`, `cast-foo-bar-baz`.
- Negative: `Cast-foo`, `cast_foo`, `cast-`, `not-cast-foo`.

Existing `test_cli_hook.py` tests must still pass after the import refactor.

### Step 1.7: Invocation sources module

Create `cast-server/cast_server/services/_invocation_sources.py`:

```python
USER_PROMPT = "user-prompt"
SUBAGENT_START = "subagent-start"

def source_filter_clause() -> str:
    return "json_extract(input_params, '$.source') = ?"
```

Both `user_invocation_service.py` and the new `subagent_invocation_service.py`
(sp2) import from here. Update sibling's `complete()` (line 86) to use
`source_filter_clause()` + the `USER_PROMPT` constant.

Tests in `cast-server/tests/test_invocation_sources.py` cover:
- The constant values are the literal strings `"user-prompt"` and
  `"subagent-start"`.
- The SQL clause shape is exactly `json_extract(input_params, '$.source') = ?`.
- Sibling's existing `complete()` tests must still pass after the refactor.

### Step 1.8: `agent_service.resolve_run_by_session_id`

Add to `cast-server/cast_server/services/agent_service.py`:

```python
def resolve_run_by_session_id(session_id: str, db_path: str | None = None) -> str | None:
    """Return the id of the most-recent running agent_run keyed on session_id, or None."""
    # SELECT id FROM agent_runs WHERE session_id = ? AND status = 'running'
    #   ORDER BY started_at DESC LIMIT 1
```

Tests (added to existing `test_agent_service.py` or a new file):
- stale parent (status=completed) → None
- no row → None
- running row → that row's id
- multiple running rows in same session → most-recent (by started_at) wins

### Step 1.9: Run the test suites

```bash
cd cast-server && uv run pytest \
  tests/test_schema_migration.py \
  tests/test_cast_name_pattern.py \
  tests/test_invocation_sources.py \
  tests/test_system_ops_seed_idempotent.py \
  tests/test_sqlite_version_check.py \
  tests/test_cli_hook.py \
  -v
```

All listed tests must pass. `test_cli_hook.py` is included to verify the
import refactor didn't break sibling tests.

## Verification

### Automated Tests (permanent)

- `pytest cast-server/tests/test_schema_migration.py` green: schema has
  `skills_used` column; pre-existing composite `idx_agent_runs_session_status`
  is left intact (no new single-column index added).
- Live-DB test inside `test_schema_migration.py`: copy `~/.cast/diecast.db` to
  a tmp path, restart cast-server pointing at it — migration is idempotent
  (no errors, no extra rows).
- `pytest cast-server/tests/test_cast_name_pattern.py` green.
- Existing `test_cli_hook.py` tests still green after the import refactor.
- `pytest cast-server/tests/test_invocation_sources.py` green.
- `pytest cast-server/tests/test_system_ops_seed_idempotent.py` green:
  fresh DB → goal exists; pre-existing DB without goal → goal added;
  pre-existing goal → no error, no duplicate.
- `pytest cast-server/tests/test_sqlite_version_check.py::test_sqlite_version_check_rejects_old_versions`
  green: monkeypatch `sqlite3.sqlite_version_info` to `(3, 8, 0)`, assert
  `SystemExit` at `get_connection()` call.

### Validation Artifacts (permanent)

- `goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md` exists
  with verbatim live captures of `SubagentStart`, `SubagentStop`,
  `PreToolUse(Skill)`. Decision-gate confirmation noted in the file.

### Manual Checks

```bash
# Confirm the schema column exists
sqlite3 ~/.cast/diecast.db "PRAGMA table_info(agent_runs);" | grep skills_used

# Confirm composite index is intact and no new single-column index was added
sqlite3 ~/.cast/diecast.db ".indexes agent_runs" | grep -i session
# Expected: idx_agent_runs_session_status   (and only that)
```

### Success Criteria

- [ ] `agent_runs.skills_used` column exists, defaulting to `'[]'`.
- [ ] No new single-column `idx_agent_runs_session_id` exists; composite
      `idx_agent_runs_session_status` is intact.
- [ ] `system-ops` goal row exists in DB; idempotent on re-migration.
- [ ] `get_connection()` SystemExits on SQLite < 3.9.
- [ ] `models/agent_run.py:AgentRun.skills_used` defaults to `[]`.
- [ ] `_cast_name.py` exports `CAST_NAME_BODY`, `PROMPT_PATTERN`,
      `AGENT_TYPE_PATTERN`. `hook_handlers.py` imports `PROMPT_PATTERN` from
      it.
- [ ] `_invocation_sources.py` exports `USER_PROMPT`, `SUBAGENT_START`,
      `source_filter_clause()`. Sibling `complete()` uses them.
- [ ] `agent_service.resolve_run_by_session_id` returns most-recent running
      row id or None.
- [ ] All sp1 tests pass; sibling `test_cli_hook.py` still green.
- [ ] Spike A payload notes exist; decision-gate confirmation recorded.
- [ ] Temporary `/tmp/log-payload.sh` hooks REMOVED from `.claude/settings.json`.

## Design Review

- **Naming:** `skills_used` matches plural-noun convention (`artifacts`,
  `directories`, `rate_limit_pauses`). `_invocation_sources.py` follows the
  leading-underscore convention for "internal-but-importable" modules used
  elsewhere in `services/`. ✓
- **Architecture:** migration via `_run_migrations()` mirrors all eight
  existing examples in `connection.py`. The seed step is one already-shipped
  call; sp1 only verifies. ✓
- **Spec consistency:** no impact on `cast-delegation-contract.collab.md`
  (file-based delegation outputs, unrelated to hook-tracking). No impact on
  `cast-output-json-contract.collab.md` (hook-created rows have no
  output.json). ✓
- **DRY:** `PROMPT_PATTERN` and `AGENT_TYPE_PATTERN` share `CAST_NAME_BODY` —
  single source of truth for "what counts as cast-*". Source discriminators
  share constants — typo-proof.
- **Error & rescue:** `resolve_run_by_session_id` is the SOLE
  parent-resolution path; stale-parent guard is the `status='running'`
  filter. SQLite version check fails LOUD at startup (not at first
  `record_skill` call) so deployment surprises happen once, not per-skill.
- **Index choice:** composite `(session_id, status)` already exists and
  covers `WHERE session_id = ? AND status = 'running'`. No new index needed.

## Decision Gate Reminder

Spike A's outcome determines whether sp2's resolver design holds. Before
moving to sp2, confirm in `payload-shapes.ai.md`:
- `parent_session_id` is present in `SubagentStart`.
- `parent_session_id` equals the immediate parent's `session_id`, not the
  root's.

If either fails, escalate to user before sp2 starts.

## Execution Notes

- **Spec-linked files:** sp1 doesn't touch any spec files yet — sp5 authors
  the new spec.
- **Skill/agent delegation:** consider invoking `/cast-pytest-best-practices`
  after the initial test draft to catch structural issues. Skill output
  should be reviewed for fixture-scope and isolation findings.
- **Live DB caution:** the live-DB migration test in
  `test_schema_migration.py` MUST copy `~/.cast/diecast.db` to a tmp path
  before mutating. Never write directly to the user's real DB during tests.
- **Sibling-test regression check:** after the `PROMPT_PATTERN` import
  refactor in `hook_handlers.py`, run the full `test_cli_hook.py` suite to
  confirm no breakage. The regex IS the contract for `cast-*` detection;
  any subtle behavior change there breaks the sibling.
