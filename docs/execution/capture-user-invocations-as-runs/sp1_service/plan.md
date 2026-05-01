# Sub-phase 1: User-Invocation Service + Unit Tests

> **Pre-requisite:** Read `docs/execution/capture-user-invocations-as-runs/_shared_context.md` before starting.

## Objective

Implement `cast-server/cast_server/services/user_invocation_service.py` with two public
functions — `register(agent_name, prompt, session_id) -> run_id` and
`complete(session_id) -> int` — and ship comprehensive unit tests against a tmp DB. This
is the foundation: every later sub-phase depends on this service existing and being
correct. No HTTP, no hooks, no settings.json yet.

## Dependencies

- **Requires completed:** None.
- **Assumed codebase state:** `agent_service.create_agent_run` and `update_agent_run` work.
  `db/connection.get_connection` returns a SQLite connection. `agent_runs` table exists
  with the expected columns (verify by reading `db/connection.py` and `models/agent_run.py`).

## Scope

**In scope:**
- New file `cast-server/cast_server/services/user_invocation_service.py` with the exact
  shape from the plan (Architecture > "New file: user_invocation_service.py").
- New file `cast-server/tests/test_user_invocation_service.py` with the 10 unit tests
  enumerated below.
- Verify the bespoke UPDATE works against the existing schema (it does — the discriminator
  uses `json_extract(input_params, '$.source')` which is SQLite-native).

**Out of scope (do NOT do these):**
- HTTP endpoints (sp2).
- DB index (sp3).
- Hook handlers, console_script, or installer (sp4, sp5).
- Modifications to `agent_service.py` — Decision #11 keeps this layer clean.
- Adding any new field to `models/agent_run.py` — Decision #2 forbids.
- Auto-cancellation logic — Decision #14: Stop always reports `completed`.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/services/user_invocation_service.py` | Create | Does not exist |
| `cast-server/tests/test_user_invocation_service.py` | Create | Does not exist |

## Detailed Steps

### Step 1.1: Read existing service signatures

Confirm `create_agent_run` and `update_agent_run` parameter names match what the plan calls.

```bash
grep -n "def create_agent_run\|def update_agent_run\|def get_agent_run" \
  cast-server/cast_server/services/agent_service.py
```

The plan assumes:
- `create_agent_run(agent_name, goal_slug, task_id, input_params, session_id, status, parent_run_id, db_path) -> run_id`
- `update_agent_run(run_id, started_at=..., db_path=...)`

If signatures differ (kwargs renamed, ordering, optional `db_path`), adapt the service to
the actual signatures — do **not** refactor agent_service.py to match the plan.

### Step 1.2: Create the service module

Create `cast-server/cast_server/services/user_invocation_service.py` with the body shown in
the plan ("New file: user_invocation_service.py"). Critical details:

- Module docstring identifies it as the user-invocation lifecycle file.
- `STALENESS_WINDOW = timedelta(hours=1)` at module scope (Decision #5).
- `register()`:
  - `goal_slug="system-ops"` (matches existing CLI invocation default — confirm this is
    the literal slug used elsewhere; grep for `system-ops` if unsure).
  - `task_id=None`, `parent_run_id=None`, `status="running"`.
  - `input_params={"source": "user-prompt", "prompt": prompt}` — exact keys.
  - Calls `update_agent_run(run_id, started_at=now)` to set `started_at`. (If
    `create_agent_run` already sets `started_at` automatically, the second call is still
    safe but record this in a code comment.)
  - Returns `run_id`.
- `complete()`:
  - Returns `0` immediately if `session_id` is falsy (Decision: API contract for missing
    session_id).
  - Computes `cutoff = now - STALENESS_WINDOW` in UTC isoformat.
  - Single SQL UPDATE; uses `json_extract(input_params, '$.source')='user-prompt'`.
  - `cur.rowcount` is the return value.
  - **Closes connection** in a `try/finally` block to avoid leaks.

### Step 1.3: Author the unit tests

Create `cast-server/tests/test_user_invocation_service.py`. **Delegate: `/cast-pytest-best-practices`** at the end of authoring (or rely on existing project conventions if the
delegation skill has already shaped the testing approach used in nearby files).

Required tests (mirror the plan's "Unit tests" block):

```python
def test_register_creates_running_row(tmp_db)
def test_register_input_params_carries_source_and_prompt(tmp_db)
def test_register_session_id_persisted(tmp_db)
def test_complete_marks_running_row_completed(tmp_db)
def test_complete_returns_count_of_rows_closed(tmp_db)
def test_complete_closes_orphans_in_same_session(tmp_db)         # 2 running rows, same session → both close
def test_complete_skips_rows_older_than_staleness_window(tmp_db) # row started 90min ago stays running
def test_complete_only_touches_user_prompt_rows(tmp_db)          # subprocess-dispatched row with same session_id NOT closed
def test_complete_returns_zero_when_no_session_id(tmp_db)
def test_complete_returns_zero_when_no_matching_running_rows(tmp_db)
```

Look at `cast-server/tests/conftest.py` for the existing `tmp_db` / `db_path` fixture
pattern — reuse it (or add a thin wrapper if needed).

### Step 1.4: Staleness-window test mechanics

For `test_complete_skips_rows_older_than_staleness_window`:

- Insert a row directly via `create_agent_run` (or directly via the connection if the
  service doesn't allow custom `started_at`).
- After insertion, manually `UPDATE agent_runs SET started_at = ? WHERE id = ?` to a
  timestamp 90 minutes in the past (ISO8601 UTC).
- Call `complete(session_id)` and assert returned count is `0` and the row's `status`
  remains `running`.

For `test_complete_closes_orphans_in_same_session`:

- Create two `running` rows for the same session_id, both within the 1h window.
- Call `complete(session_id)` once.
- Assert returned count is `2`; both rows are now `completed` with `completed_at` set.

For `test_complete_only_touches_user_prompt_rows`:

- Create one `running` row with `input_params.source='user-prompt'` (via `register`).
- Create another `running` row with the **same session_id** but different
  `input_params` (e.g., `{"source": "subprocess"}` or no `source` key) — simulate via
  direct `create_agent_run` with the same session_id.
- Call `complete(session_id)`.
- Assert only the user-prompt row is closed; the subprocess row is still `running`.

### Step 1.5: Run the test suite

```bash
cd cast-server && uv run pytest tests/test_user_invocation_service.py -v
```

All 10 tests must pass.

## Verification

### Automated Tests (permanent)

`cast-server/tests/test_user_invocation_service.py` — 10 tests as enumerated above.

### Validation Scripts (temporary)

Optional sanity check (no DB needed beyond tmp):

```bash
cd cast-server && uv run python -c "
from cast_server.services import user_invocation_service
print('STALENESS_WINDOW:', user_invocation_service.STALENESS_WINDOW)
print('register:', user_invocation_service.register)
print('complete:', user_invocation_service.complete)
"
```

### Manual Checks

```bash
# Verify the service file is the only file changed
git status cast-server/cast_server/services/ cast-server/tests/

# Confirm agent_service.py is untouched
git diff cast-server/cast_server/services/agent_service.py
# (must show no changes)
```

### Success Criteria

- [ ] `services/user_invocation_service.py` exists with `register` and `complete`.
- [ ] `STALENESS_WINDOW` is `timedelta(hours=1)`.
- [ ] `register` creates a row with `agent_name`, `session_id`, `input_params={source, prompt}`,
      `status="running"`, `parent_run_id=None`, `goal_slug="system-ops"`.
- [ ] `complete` returns 0 when `session_id` is falsy.
- [ ] `complete` returns the number of rows updated by the UPDATE.
- [ ] `complete` ignores subprocess-dispatched rows even when their session_id matches.
- [ ] `complete` ignores rows older than 1h.
- [ ] All 10 unit tests pass.
- [ ] `agent_service.py` shows zero git diff.
- [ ] DB connection is closed on every `complete` invocation (look for `finally`/`with`).

## Execution Notes

- The service uses `get_connection(db_path)` for the bespoke UPDATE. Other code paths
  inside `register` use the existing service functions, so DB-layer code is **not**
  duplicated.
- Time mocking: prefer monkeypatching `datetime.now` via a small helper if your test fixture
  pattern doesn't already use `freezegun`. Or just write rows with explicit past
  `started_at` strings — it's simpler and avoids a new test dependency.
- **Spec-linked files:** None at this point. Specs are authored in sp7.
- If `create_agent_run` already sets `started_at`, the explicit `update_agent_run` call in
  `register` is a no-op (still safe). Add a code comment explaining the redundancy if you
  keep both.
- **Skill/agent delegation:** consider invoking `/cast-pytest-best-practices` after the
  initial test draft to catch structural issues. Skill output should be reviewed for
  fixture-scope and isolation findings.
- Watch for: SQLite stores datetimes as TEXT; ensure all comparisons use ISO8601 strings
  in UTC for consistency. The plan's `complete()` already does this.
