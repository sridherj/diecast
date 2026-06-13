# Sub-phase 1b: Recording columns on `goals` + model threading

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase3b/_shared_context.md` before starting.
> Source: Work Package C of `docs/plan/2026-06-11-refine-requirements-v2-phase3b-workflow-router.md`.

## Objective

Give the `goals` table the three columns the recorder writes — `workflow_family`, `routing_handle`,
`routed_at` — in both the canonical schema and the runtime migration, thread the client-settable
fields through `GoalUpdate`, and extend `goal.yaml` rendering so a full re-render of a routed goal
preserves them. This is the **write target** for sp2's `record_routing_decision`. It is independent of
the registry/resolver (sp1a/sp2) — pure persistence plumbing following the exact `gstack_dir`
precedent — so it runs in parallel with sp1a.

## Dependencies
- **Requires completed:** None within Phase 3b. **Phase 2 must be landed** (Hard Prerequisite) — but
  this sub-phase touches no Phase 2 code.
- **Assumed codebase state:** `db/schema.sql` has `CREATE TABLE IF NOT EXISTS goals (...)` with
  `gstack_dir TEXT` (line ~12). `db/connection.py::_run_migrations()` has the `gstack_dir`/
  `external_project_dir` ALTER loop at lines 100-104. `models/goal.py` has `Goal`, `GoalCreate`,
  `GoalUpdate`. `goal_service.py` has `_write_goal_yaml`, `_update_goal_yaml_fields`,
  `_resolve_goal_dir` with a `gstack_dir` conditional-include precedent.

## Scope

**In scope:**
- Add `workflow_family TEXT`, `routing_handle TEXT`, `routed_at TEXT` to `CREATE TABLE goals` in the
  **canonical** `cast-server/cast_server/db/schema.sql`.
- Mirror an idempotent `ALTER TABLE … ADD COLUMN` loop in `_run_migrations()` (the `gstack_dir`
  pattern at `connection.py:100-104`).
- Thread `workflow_family: str | None = None` and `routing_handle: str | None = None` into `Goal` and
  `GoalUpdate` (NOT `routed_at` on `GoalUpdate` — server-set only; `routed_at` IS added to `Goal`).
- Add conditional includes in `_write_goal_yaml` (mirroring `gstack_dir`) so a full re-render preserves
  the three fields when present.
- Migration + render tests.

**Out of scope (do NOT do these):**
- The **root** `db/schema.sql` (legacy/diverged — do NOT edit it; only the `cast_server/db/schema.sql`
  canonical copy).
- The resolver / recorder write logic (sp2). sp1b only makes the columns exist and renderable; the
  single writer is `record_routing_decision` in sp2.
- `WORKFLOW_REGISTRY` (sp1a). The route endpoint (sp3).
- A `goal_routing` history/audit table (deferred — HOLD SCOPE; US6 S4 needs only current-vs-previous).
- Using `tags` for routing data (explicitly rejected — flat, unstructured, collides with real tags).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/db/schema.sql` | Modify | `goals` table has `gstack_dir`; no routing columns |
| `cast-server/cast_server/db/connection.py` | Modify | `_run_migrations` has `gstack_dir` ALTER loop (l.100-104) |
| `cast-server/cast_server/models/goal.py` | Modify | `Goal`/`GoalUpdate` lack routing fields |
| `cast-server/cast_server/services/goal_service.py` | Modify | `_write_goal_yaml` has `gstack_dir` conditional include |
| `cast-server/tests/test_goal_routing_columns.py` | Create | Does not exist |

## Detailed Steps

### Step 1b.1: Canonical schema

In `cast-server/cast_server/db/schema.sql`, add to `CREATE TABLE IF NOT EXISTS goals (...)`, alongside
`gstack_dir`:

```sql
    workflow_family TEXT,
    routing_handle TEXT,
    routed_at TEXT,
```

### Step 1b.2: Migration mirror (idempotent)

In `db/connection.py::_run_migrations()`, replicate the `gstack_dir` precedent exactly:

```python
for col in ["workflow_family", "routing_handle", "routed_at"]:
    try:
        conn.execute(f"ALTER TABLE goals ADD COLUMN {col} TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists
```

This makes a legacy pre-column DB self-heal on next open, and is safe to run repeatedly.

### Step 1b.3: Model threading

In `models/goal.py`:
- `Goal`: add `workflow_family: str | None = None`, `routing_handle: str | None = None`,
  `routed_at: str | None = None`.
- `GoalUpdate`: add `workflow_family: str | None = None`, `routing_handle: str | None = None` only
  (`routed_at` is server-set, never client-supplied).

> Note: `GoalUpdate` currently has **no consumers** in the codebase — this threading is additive
> contract-completeness, NOT a write path. The actual write path is `record_routing_decision`
> (single-writer discipline). State this in your output so nobody "finishes" a second write path.

### Step 1b.4: `goal.yaml` render preservation

- `_update_goal_yaml_fields` already merges arbitrary keys — recording works day one, no change needed
  there. (Verify by reading it; do not modify unless it does not in fact merge arbitrary keys.)
- In `_write_goal_yaml`, add conditional includes mirroring `gstack_dir` so a **full re-render** of an
  already-routed goal preserves the three fields:

```python
    if goal_data.get("workflow_family"):
        lines.append(f"workflow_family: {goal_data['workflow_family']}")
    if goal_data.get("routing_handle"):
        lines.append(f"routing_handle: {goal_data['routing_handle']}")
    if goal_data.get("routed_at"):
        lines.append(f"routed_at: {goal_data['routed_at']}")
```

(Match the exact serialization style `_write_goal_yaml` already uses for `gstack_dir` — quoting,
ordering, indentation. Read the function first and follow its house style.)

### Step 1b.5: Tests

Create `cast-server/tests/test_goal_routing_columns.py`:
- **Fresh-DB:** `init_db` on a tmp path → `PRAGMA table_info(goals)` includes the three columns.
- **Legacy-DB migration idempotency:** build a goals table WITHOUT the columns, run `_run_migrations`
  → columns added; run `_run_migrations` **again** → no error, still present.
- **`goal.yaml` round-trip:** write a goal dict carrying `workflow_family`/`routing_handle`/`routed_at`
  via `_write_goal_yaml` to a tmp goal dir → read the file back → all three present and correctly
  serialized; a goal WITHOUT them renders no stray keys (conditional include holds).

→ **Delegate:** apply `/cast-pytest-best-practices`; review output.

## Verification

### Automated Tests (permanent) — `cast-server/tests/test_goal_routing_columns.py`
- Fresh `init_db` exposes `workflow_family`, `routing_handle`, `routed_at`.
- `_run_migrations` adds them to a legacy DB and is idempotent (run twice).
- `_write_goal_yaml` round-trips all three when present, omits them when absent.

### Validation Scripts (temporary)
```bash
uv run --project cast-server pytest cast-server/tests/test_goal_routing_columns.py -v
# Confirm the canonical schema (not the legacy root copy) was edited:
grep -n "workflow_family\|routing_handle\|routed_at" cast-server/cast_server/db/schema.sql
grep -n "workflow_family\|routing_handle\|routed_at" db/schema.sql && echo "WARNING: legacy root schema edited — revert" || echo "legacy root schema untouched (correct)"
```

### Manual Checks
- `GoalUpdate` has `workflow_family` + `routing_handle` but NOT `routed_at`.
- `Goal` has all three.
- The migration loop matches the `gstack_dir` try/except shape exactly.

### Success Criteria
- [ ] Three columns in canonical `cast_server/db/schema.sql` `goals` table; root `db/schema.sql`
      untouched.
- [ ] Idempotent migration in `_run_migrations` (run twice → no error).
- [ ] `Goal` has all three fields; `GoalUpdate` has `workflow_family` + `routing_handle` only.
- [ ] `_write_goal_yaml` conditionally renders all three; absent goal renders no stray keys.
- [ ] `pytest cast-server/tests/test_goal_routing_columns.py` green.

## Execution Notes
- The columns are nullable `TEXT` with no default — an un-routed goal simply has `NULL`s, which the
  conditional-include render skips (no empty keys in `goal.yaml`).
- `routed_at` is ISO-8601 UTC **written by the recorder (sp2)**, never by a client — that is why it is
  absent from `GoalUpdate`. Do not add a default timestamp here.
- This sub-phase deliberately writes NO routing values — it only makes the columns exist and
  renderable. Asserting a *recorded* value is sp2's job. Keep the boundary clean.

**Spec-linked files:** No spec covers these columns yet — sp4b documents the three columns + the
`goal.yaml` render. No SAV behaviors to preserve here.
