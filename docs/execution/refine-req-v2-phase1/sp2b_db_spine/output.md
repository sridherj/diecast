# Sub-phase 2b — Thin DB Spine: Output

**Status:** ✅ Completed. All Detailed Steps executed, all verification run, every success
criterion met.

## What was done

Added the three thin-spine tables and their indexes to the canonical schema and the migration
hook, idempotently, and extended the migration test to prove both the fresh-init and
pre-existing-DB paths.

### Files modified

| File | Change |
|------|--------|
| `cast-server/cast_server/db/schema.sql` | Appended the canonical DDL (3 tables + 3 indexes) after the last index. |
| `cast-server/cast_server/db/connection.py` | Mirrored the identical `CREATE ... IF NOT EXISTS` statements in `_run_migrations()`, placed after the `idx_agent_runs_claude_agent_id` block and before `_seed_system_goals(conn)`, following the `agent_error_memories` `conn.execute(...)`-per-statement idiom. |
| `cast-server/tests/test_schema_migration.py` | Added `_table_exists`/`_index_exists` helpers and three tests: fresh-DB tables present, fresh-DB indexes present, and tables+indexes created by `_run_migrations` on a pre-existing DB with double-run idempotency. |

### Tables shipped (EMPTY — no seed rows)

- `requirement_versions` — version snapshots (`goal_slug`, `version`, `content`, `content_hash`,
  `status`, `created_at`, `created_by`; `UNIQUE(goal_slug, version)`; FK → `goals(slug)` `ON DELETE CASCADE`).
- `requirement_comments` — comment rows (`quoted_text` + `section_hint`, `state`, `author`,
  `author_kind`; FK → `goals(slug)` `ON DELETE CASCADE`). CRUD is **Phase 4**, not now.
- `comment_events` — append-only event trail (FK → `requirement_comments(id)` `ON DELETE CASCADE`).
- Indexes: `idx_req_versions_goal_status`, `idx_req_comments_goal_state`, `idx_comment_events_comment`.

**Deliberately absent** (encoded in the schema comment + design note): `block_anchor` / element-surrogate
columns (thin-spine decision #1), routing columns (Phase 3b), `change_request*` / `notifications_outbox`
(Phase 5).

## Verification results

- **`uv run pytest tests/test_schema_migration.py`** → **14 passed** (existing + 3 new spine tests).
- **Fresh-DB validation script** → `init_db()` materialises `['comment_events',
  'requirement_comments', 'requirement_versions']` and all three `idx_*` indexes.
- **Pre-existing-DB path** → after dropping the spine tables, `_run_migrations(conn)` recreates all
  three; a second `_run_migrations(conn)` call is a clean idempotent no-op (no error).
- **`bin/run-migrations.py --dry-run`** → exits 0, no change required (it is the file-based runner under
  `migrations/`; the live table-creation path is `init_db()` / `get_connection()`, both verified above).
- **Lockstep check** → built the schema via the `schema.sql` path and via the `_run_migrations` path,
  then compared `sqlite_master` definitions for all 6 objects: **STRUCTURAL MATCH: True** (byte-identical
  table/column/index definitions across the two sources).
- **Root `db/schema.sql`** → `git diff --stat` shows **no change**; only the canonical
  `cast-server/cast_server/db/schema.sql` was edited.
- **Forbidden tokens** (`block_anchor`, `change_request`, etc.) appear **only** inside the
  "Deliberately absent" documentation comments — no actual columns/tables.

## Success criteria

- [x] Three tables + three indexes appended to the **canonical** `cast-server/cast_server/db/schema.sql`.
- [x] Identical `CREATE ... IF NOT EXISTS` mirrored in `_run_migrations()`, matching the file's idiom.
- [x] `test_schema_migration.py` proves tables exist on fresh init AND after `_run_migrations()` on a
      pre-existing DB; double-run idempotency green.
- [x] `bin/run-migrations.py` picks them up unchanged (exit 0).
- [x] Root `db/schema.sql` untouched; no deferred columns/tables added.

## Note for downstream sub-phases

**Comment-syntax constraint discovered:** `init_db()` (`connection.py`) loads `schema.sql` and splits it
on the `;` statement separator before executing each fragment. Therefore SQL `--` comments inside
`schema.sql` **must not contain a `;` character** — a semicolon inside a comment splits the comment
mid-line and leaks the tail into the next statement (caused a transient `syntax error` during this
sub-phase). The canonical DDL's leading comment from `_shared_context.md` originally read
`routing columns (Phase 3b); change_request* tables (Phase 5).` — the semicolon was changed to a comma
in `schema.sql` to satisfy this parser. The Python-side `_run_migrations` copy (a `#` comment + a single
whole-statement `conn.execute`) is unaffected, but its wording was kept matching for lockstep. **sp3**
(version service) and any later phase appending DDL to `schema.sql` must keep semicolons out of SQL
comments.

The tables are EMPTY by design. `requirement_versions` inserts arrive in **sp3**
(`requirement_version_service.create_snapshot`); `requirement_comments` / `comment_events` inserts are
**Phase 4**.
