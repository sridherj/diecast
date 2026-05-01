# Sub-phase 3: DB Index for Close-By-Session Query

> **Pre-requisite:** Read `docs/execution/capture-user-invocations-as-runs/_shared_context.md` before starting.

## Objective

Add `idx_agent_runs_session_status ON agent_runs(session_id, status)` to
`cast-server/cast_server/db/connection.py` so the Stop hook's close-by-session UPDATE
filters in sub-millisecond time as `agent_runs` grows. Verify with `EXPLAIN QUERY PLAN`.

## Dependencies

- **Requires completed:** sp1 (so the close-by-session query exists to be measured).
- **Assumed codebase state:** `db/connection.py` already has at least one
  `CREATE INDEX IF NOT EXISTS` precedent (`idx_error_memories_agent` near line 137 per
  the plan's reference section). The schema-init function runs on every server start.

## Scope

**In scope:**
- One-line `CREATE INDEX IF NOT EXISTS` statement next to the existing index precedent.
- A small verification step using `EXPLAIN QUERY PLAN`.

**Out of scope (do NOT do these):**
- Any migration tooling (the `IF NOT EXISTS` makes it idempotent across restarts; matches
  the existing pattern in this file).
- Renaming or restructuring existing indices.
- Adding indices for any other query.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/db/connection.py` | Modify | Already has indices around line 137; add one more |

## Detailed Steps

### Step 3.1: Locate the index precedent

```bash
grep -n "CREATE INDEX" cast-server/cast_server/db/connection.py
```

Confirm the line near `:137` mentioned in the plan. The new index goes adjacent to it
(grouped with peers for readability).

### Step 3.2: Add the index

Insert this line in the index-creation block:

```python
# Stop's close-by-session query needs this for sub-millisecond filtering as agent_runs grows.
conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_runs_session_status ON agent_runs(session_id, status)")
```

Do **not** wrap it in a try/except or any conditional — `IF NOT EXISTS` already handles
the re-init case.

### Step 3.3: Verify the index is created on init

```bash
# From a clean state (or use a tmp DB):
cd cast-server && uv run python -c "
from cast_server.db.connection import get_connection
conn = get_connection()
rows = conn.execute(\"SELECT name FROM sqlite_master WHERE type='index' AND name='idx_agent_runs_session_status'\").fetchall()
print('Index present:' , bool(rows), rows)
"
```

Expect `Index present: True ...`.

### Step 3.4: Verify the close query uses the index

Use SQLite's `EXPLAIN QUERY PLAN`:

```bash
cd cast-server && uv run python -c "
from cast_server.db.connection import get_connection
conn = get_connection()
plan = conn.execute('''
EXPLAIN QUERY PLAN
UPDATE agent_runs
   SET status='completed', completed_at=?
 WHERE session_id=?
   AND status='running'
   AND json_extract(input_params, \$\$.source\$\$)='user-prompt'
   AND started_at > ?
''', ('x','x','x')).fetchall()
for r in plan: print(r)
"
```

(Adjust quoting in your shell as needed — easier may be running it inside an interactive
`sqlite3 <db>` session.) The plan output should reference `idx_agent_runs_session_status`
(e.g., `SEARCH agent_runs USING INDEX idx_agent_runs_session_status (session_id=? AND status=?)`).

If it falls back to a full table scan, double-check: index column order is
`(session_id, status)` — that order matters for SQLite's planner given the WHERE clause.

## Verification

### Automated Tests (permanent)

None added in this sub-phase (the schema-init code path is exercised indirectly by every
test that opens a DB).

### Validation Scripts (temporary)

The two snippets in Step 3.3 and 3.4. Both run from a fresh DB.

### Manual Checks

```bash
git diff cast-server/cast_server/db/connection.py
# Should show exactly one new line + a comment line; no other modifications.
```

### Success Criteria

- [ ] One new `CREATE INDEX IF NOT EXISTS idx_agent_runs_session_status` statement added.
- [ ] Index column order is `(session_id, status)`.
- [ ] After server init, `sqlite_master` shows the index.
- [ ] `EXPLAIN QUERY PLAN` for the close-by-session UPDATE references the new index.
- [ ] No other indices renamed or removed.
- [ ] The full test suite (`uv run pytest cast-server/tests`) still passes.

## Execution Notes

- The `IF NOT EXISTS` clause is essential — `connection.py` runs on every server start
  and re-running CREATE INDEX without the guard would error.
- The plan refers to `db/connection.py:137` as the precedent location; if the file has
  been edited since, just place the new line near other `CREATE INDEX` statements.
- This sub-phase is structurally tiny but worth keeping separate so the index addition is
  reviewable in isolation and easy to revert if perf regresses.
- **Spec-linked files:** None.
