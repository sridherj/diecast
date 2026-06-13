# sp3 — Version-Snapshot Service — Output

**Status:** ✅ Complete. All 6 success criteria met; validation script passes.

## What was built

`cast-server/cast_server/services/requirement_version_service.py` (NEW) — the only service
Phase 1 produces. Four flat module-level functions, modeled on the `goal_service.py` /
`task_service.py` DB house pattern (NOT `orchestration_service.py` — plan-review Decision #1):

```python
create_snapshot(goal_slug: str, content: str, created_by: str | None = None, *, db_path=None) -> dict
get_current(goal_slug: str, *, db_path=None) -> dict | None
get_version(goal_slug: str, version: int, *, db_path=None) -> dict | None
list_versions(goal_slug: str, *, db_path=None) -> list[dict]
```

### Behavior (canon for Phase 4)
- **Content-hash idempotent.** `create_snapshot` computes `content_hash(content)` (imported
  from the canonical `cast_server.requirements_render.hashing` — no local hashlib). If the
  current row's hash matches, it returns that row unchanged — **no new row**.
- **Changed content → `version = max(version) + 1`** inserted as `'current'`, prior `'current'`
  row flipped to `'archived'`, in **ONE transaction** (single `commit()`). No window where two
  rows are `'current'` for the same goal (verified: exactly-one-current invariant holds).
- All functions take `db_path: Path | None = None`, acquire the handle via
  `get_connection(db_path)` in a try/finally with `conn.close()`, and return plain `dict(row)`
  values (never `sqlite3.Row`, never entities).
- `list_versions` orders **ascending by `version`** (matches `task_service`'s `ORDER BY sort_order`
  oldest-first idiom; documented in the docstring).
- **DB-only — no file writes.** `grep` for `open(` / `write_text` / `Path(` in write context is
  clean (`Path` appears only as an import + type annotation). The `.collab.md` stays canonical.

### Decision #5 (concurrency) — recorded, not implemented
The `version = max + 1` read-then-write is documented in the `create_snapshot` docstring as an
**accepted single-user/local limitation**, with `BEGIN IMMEDIATE` named as the fix-forward.
No locking change was made (over-implementing would diverge from the recorded decision).

## Validation (temporary REPL — nothing committed)
v1 → version 1 `current`; identical content → same version (idempotent no-op); changed content
→ version 2 `current` with v1 flipped `archived`; `get_current` returns v2; exactly one `current`
row; returned hash equals `content_hash('hello world')`; returns are plain dicts; missing
version/goal → `None`. All pass.

## ⚠️ Note for sp4 (test fixture seeding)
FK enforcement is **ON** (`PRAGMA foreign_keys=ON` in `get_connection`), so `create_snapshot`
requires a parent `goals` row. When seeding that row, **`goals.folder_path` is `NOT NULL`** —
the seed must supply it (e.g. `INSERT INTO goals (slug, title, status, phase, created_at,
folder_path) VALUES (...)`). A bare slug/title-only insert fails with
`NOT NULL constraint failed: goals.folder_path`.

## Files
| File | Action |
|------|--------|
| `cast-server/cast_server/services/requirement_version_service.py` | Created |
