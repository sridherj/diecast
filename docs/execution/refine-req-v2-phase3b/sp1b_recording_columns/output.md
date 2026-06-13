# sp1b — Recording columns on `goals` + model threading — OUTPUT

**Status: COMPLETE.** All 5 success criteria met; `pytest` green (7 new tests, 0 regressions).

## What landed

The `goals` table now carries the three columns the sp2 recorder writes, and a
full `goal.yaml` re-render preserves them. This is pure persistence plumbing —
**no routing values are written by sp1b**; the single writer is
`record_routing_decision` (sp2).

| File | Change |
|------|--------|
| `cast-server/cast_server/db/schema.sql` | Added `workflow_family TEXT, routing_handle TEXT, routed_at TEXT` to `CREATE TABLE goals` (after `external_project_dir`). Updated the "deliberately absent" comment block to note routing columns now live on `goals`. **Root `db/schema.sql` untouched (legacy/diverged).** |
| `cast-server/cast_server/db/connection.py` | New idempotent `ALTER TABLE goals ADD COLUMN` loop in `_run_migrations()`, immediately after the `gstack_dir`/`external_project_dir` loop, over `["workflow_family", "routing_handle", "routed_at"]` with `try/except sqlite3.OperationalError`. |
| `cast-server/cast_server/models/goal.py` | `Goal` gains all three fields (`str \| None = None`). `GoalUpdate` gains `workflow_family` + `routing_handle` **only** — `routed_at` is server-set, never client-supplied. |
| `cast-server/cast_server/services/goal_service.py` | `_write_goal_yaml` now conditionally includes the three fields (mirroring the `gstack_dir` `yaml_data[...] = ...` house style) so a full re-render of a routed goal preserves the stamp. `_update_goal_yaml_fields` already merges arbitrary keys (`data.update(fields)`) — **no change needed**, confirmed by reading it. |
| `cast-server/tests/test_goal_routing_columns.py` | **NEW** — 7 tests (see below). |

## Contracts for downstream sub-phases

- **Column names / types:** `workflow_family TEXT`, `routing_handle TEXT`, `routed_at TEXT` — all nullable, no default. An un-routed goal has `NULL`s; the conditional-include render skips them (no empty keys in `goal.yaml`).
- **`GoalUpdate` is NOT a write path.** It currently has no consumers in the codebase; threading `workflow_family`/`routing_handle` onto it is additive contract-completeness only. The actual (and only) write path is sp2's `record_routing_decision` — do not "finish" a second writer.
- **`routed_at` is absent from `GoalUpdate` by design** — sp2 sets it (ISO-8601 UTC). Do not add a client-supplied or default timestamp.
- **`goal.yaml` columns render via `_write_goal_yaml`** when present; sp2's recorder mirrors via `goal_service._update_goal_yaml_fields(...)` (best-effort — DB authoritative).

## Tests (`cast-server/tests/test_goal_routing_columns.py`)

1. `test_fresh_db_exposes_routing_column[workflow_family|routing_handle|routed_at]` — parametrized; fresh `init_db` exposes each column on `goals`.
2. `test_migration_adds_routing_columns_to_legacy_db` — builds a full current-schema DB then `ALTER TABLE goals DROP COLUMN` the three (faithful pre-3b legacy DB, keeps every other migration-touched table intact), runs `_run_migrations` → columns added.
3. `test_migration_is_idempotent` — runs `_run_migrations` twice on the legacy DB → no raise, columns present.
4. `test_write_goal_yaml_renders_routing_fields_when_present` — all three render and round-trip via yaml.
5. `test_write_goal_yaml_omits_routing_fields_when_absent` — conditional-include holds; no stray keys.

`/cast-pytest-best-practices` applied. Two deliberate calls: routing values passed as plain strings (columns are opaque `TEXT`; sp1b intentionally does NOT couple to the Phase 2 `WorkFamily` enum), and `routed_at` asserted by string equality (byte-faithful TEXT round-trip, no timezone conversion → DateTimeComparator not applicable).

## Verification run

```
pytest cast-server/tests/test_goal_routing_columns.py -v   → 7 passed
pytest test_schema_migration.py test_goal_routing_columns.py → 21 passed
pytest test_goal_service_ext_routing.py                      → 14 passed (no regression)
grep routing cols in cast_server/db/schema.sql              → present (lines 14-16)
grep routing cols in root db/schema.sql                     → absent (legacy untouched, correct)
Goal has all three: True | GoalUpdate has wf+handle: True | GoalUpdate NOT routed_at: True
```

## Success criteria — all met
- [x] Three columns in canonical `cast_server/db/schema.sql` `goals` table; root `db/schema.sql` untouched.
- [x] Idempotent migration in `_run_migrations` (run twice → no error).
- [x] `Goal` has all three fields; `GoalUpdate` has `workflow_family` + `routing_handle` only.
- [x] `_write_goal_yaml` conditionally renders all three; absent goal renders no stray keys.
- [x] `pytest cast-server/tests/test_goal_routing_columns.py` green.
