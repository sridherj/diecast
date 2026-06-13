# Sub-phase 2b: Thin DB Spine — Schema + Migration + Migration Test

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase1/_shared_context.md` before starting.

## Objective

Add the three thin-spine tables (`requirement_versions`, `requirement_comments`, `comment_events`) and
their indexes to the canonical schema and the migration hook, idempotently, so they exist on both a fresh
`init_db()` and a pre-existing DB after `_run_migrations()`. Extend the migration test to prove both
paths. This is the storage half of Phase 1's keystone; sp3's version service writes into it.

## Dependencies

- **Requires completed:** sp1 (the design note documents the deliberately-absent columns and the
  CASCADE-vs-SET-NULL deviation this sub-phase encodes in a comment).
- **Assumed codebase state:** `cast-server/cast_server/db/connection.py` has `init_db()`,
  `_run_migrations(conn)`, and `SCHEMA_PATH = <pkg>/db/schema.sql`. The `agent_error_memories` block in
  `_run_migrations()` (~line 125) is the precedent for adding `CREATE TABLE IF NOT EXISTS` migrations.
- **Runs in parallel with sp2a** (disjoint files — sp2b touches only `db/schema.sql`, `db/connection.py`,
  and `tests/test_schema_migration.py`).

## Scope

**In scope:**
- Append the canonical DDL (3 tables + 3 indexes) to `cast-server/cast_server/db/schema.sql`.
- Add the identical `CREATE TABLE IF NOT EXISTS` + `CREATE INDEX IF NOT EXISTS` statements to
  `_run_migrations()` in `cast-server/cast_server/db/connection.py`.
- Extend `cast-server/tests/test_schema_migration.py` to assert the three tables exist on the fresh-DB
  path and after `_run_migrations()` on a pre-existing DB.
- Confirm `bin/run-migrations.py` picks the tables up unchanged (it drives `_run_migrations`).

**Out of scope (do NOT do these):**
- The root-level `db/schema.sql` — it is legacy/diverged. Do NOT edit it. (Housekeeping flag only.)
- Any `block_anchor` / element-surrogate / per-element-ID column.
- Routing columns on `goals` (Phase 3b); `change_request*` / `notifications_outbox` (Phase 5).
- The version service or any write logic (sp3). This sub-phase only creates the tables.
- The parser package (sp2a).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/db/schema.sql` | Modify (append) | 3784 B; canonical schema `connection.py` reads via `SCHEMA_PATH` |
| `cast-server/cast_server/db/connection.py` | Modify (`_run_migrations`) | Has `init_db`, `_run_migrations`, `agent_error_memories` precedent ~line 125 |
| `cast-server/tests/test_schema_migration.py` | Modify (extend) | Has `isolated_db` fixture + `test_run_migrations_idempotent_on_pre_existing_db` |

## Detailed Steps

### Step 2b.1: Append the DDL to the canonical `schema.sql`

Append the **exact** canonical DDL block from `_shared_context.md` (Data Schemas & Contracts → "Canonical
DDL") to `cast-server/cast_server/db/schema.sql`. Keep the two leading comment lines verbatim — they are
the in-schema "deliberately absent" marker:

```sql
-- Requirements thin spine (refine-requirements-v2 Phase 1).
-- Deliberately absent: block_anchor / element surrogate columns (thin-spine decision #1);
-- routing columns (Phase 3b); change_request* tables (Phase 5).
```

All three `CREATE TABLE` use `IF NOT EXISTS`; all three indexes use `CREATE INDEX IF NOT EXISTS`. The FKs
reference `goals(slug)` / `requirement_comments(id)` with `ON DELETE CASCADE` (intentional — comment in
the DDL already explains it; sidecar rows are meaningless without their goal).

### Step 2b.2: Mirror the identical statements in `_run_migrations()`

Open `connection.py`, find the `agent_error_memories` block in `_run_migrations()` (~line 125), and add an
analogous block AFTER it:

```python
    # Phase: requirements thin spine (refine-requirements-v2 Phase 1).
    # Deliberately absent: block_anchor / element surrogate (thin-spine #1); routing cols (Phase 3b);
    # change_request* (Phase 5). Mirrors db/schema.sql — keep the two in lockstep.
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS requirement_versions ( ... );      -- full DDL, verbatim
        CREATE TABLE IF NOT EXISTS requirement_comments ( ... );
        CREATE TABLE IF NOT EXISTS comment_events ( ... );
        CREATE INDEX IF NOT EXISTS idx_req_versions_goal_status ON requirement_versions(goal_slug, status);
        CREATE INDEX IF NOT EXISTS idx_req_comments_goal_state ON requirement_comments(goal_slug, state);
        CREATE INDEX IF NOT EXISTS idx_comment_events_comment ON comment_events(comment_id);
        """
    )
```

- Match the **existing style** of `_run_migrations` exactly (whether it uses `conn.execute` per statement,
  `conn.executescript`, or a helper). Read the `agent_error_memories` block and copy its mechanism — do
  not introduce a new idiom.
- The statements in `_run_migrations` must be **byte-for-byte the same table/column/index definitions** as
  in `schema.sql`. A divergence here is the classic two-source-of-truth bug; keep them identical.
- `IF NOT EXISTS` everywhere means re-running against a DB that already has the tables is a safe no-op.

### Step 2b.3: Extend the migration test

In `cast-server/tests/test_schema_migration.py` (uses the `isolated_db` fixture; precedents:
`test_run_migrations_idempotent_on_pre_existing_db`, the `*_column_present` tests):

- **Fresh-DB path:** after the fixture's `init_db()`, assert all three tables exist. Use a helper that
  queries `sqlite_master`:
  ```python
  def _table_exists(conn, name):
      row = conn.execute(
          "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
      ).fetchone()
      return row is not None
  ```
  Add a test asserting `requirement_versions`, `requirement_comments`, `comment_events` all exist.
- **Pre-existing-DB path:** mirror `test_run_migrations_idempotent_on_pre_existing_db` — open the
  isolated DB, call `_run_migrations(conn)` twice (idempotency), and assert the three tables exist after.
- **(Optional, cheap) index assertion:** assert the three `idx_*` indexes exist via
  `sqlite_master WHERE type='index'`. Keeps a regression net under the perf indexes.
- Follow the file's existing fixture and assertion style; do not restructure the module.

### Step 2b.4: Confirm `bin/run-migrations.py` needs no change

`bin/run-migrations.py` drives `_run_migrations` — it should pick up the new tables with zero edits. Run
it against a throwaway DB and confirm no error and the tables appear. Do NOT modify the script.

## Verification

### Automated Tests (permanent)
- `cd cast-server && uv run pytest tests/test_schema_migration.py` — all existing tests still pass; the
  new fresh-DB and pre-existing-DB table-existence tests pass; the idempotency (double `_run_migrations`)
  test still passes with the new tables present.

### Validation Scripts (temporary)
- Fresh DB:
  ```bash
  cd cast-server && python -c "
  import pathlib, sqlite3
  from cast_server.db.connection import init_db
  p = pathlib.Path('/tmp/spine_fresh.db'); p.unlink(missing_ok=True)
  init_db(p)
  c = sqlite3.connect(p)
  print(sorted(r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'requirement%' OR name='comment_events'\")))
  "
  ```
  Expect: `['comment_events', 'requirement_comments', 'requirement_versions']`.
- Pre-existing DB: take a DB created WITHOUT the new tables (or simulate by running an older schema), then
  `_run_migrations(conn)` and confirm the tables appear; run it twice to confirm no error.
- `bin/run-migrations.py` against a throwaway DB: exits 0, tables present.

### Manual Checks
- `git diff --stat db/schema.sql` (repo root) shows **no change** — only
  `cast-server/cast_server/db/schema.sql` was edited.
- The DDL in `schema.sql` and the DDL in `_run_migrations()` are identical (diff the two blocks by eye).
- No `block_anchor` / element-ID column anywhere in the new DDL.

### Success Criteria
- [ ] Three tables + three indexes appended to the **canonical** `cast-server/cast_server/db/schema.sql`.
- [ ] Identical `CREATE ... IF NOT EXISTS` mirrored in `_run_migrations()`, matching the file's existing idiom.
- [ ] `test_schema_migration.py` proves the tables exist on fresh init AND after `_run_migrations()` on a
      pre-existing DB; idempotency (double-run) is green.
- [ ] `bin/run-migrations.py` picks them up unchanged.
- [ ] Root `db/schema.sql` untouched; no deferred columns/tables added.

## Execution Notes

- **Two sources, one truth.** The #1 risk is `schema.sql` and `_run_migrations()` drifting. Paste the
  same DDL into both; the migration test guards the migration path but not the lockstep — a careful diff
  is your guard for that.
- The `goals(slug)` FK requires the `goals` table to exist first. In `schema.sql`, ensure the new tables
  are appended AFTER the `goals` definition (they will be — appending to the end is fine). On a real DB,
  `goals` already exists, so the migration path is safe regardless of order.
- This sub-phase ships the tables EMPTY. Inserts are sp3 (`requirement_versions`) and Phase 4
  (`requirement_comments` / `comment_events`). Do not add seed rows.
- **Spec-linked files:** none. `db/schema.sql`, `connection.py`, and `test_schema_migration.py` are not
  listed in any spec's `linked_files` for this change (Phase 1 introduces no user-facing behavior).
