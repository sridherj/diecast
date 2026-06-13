# Sub-phase 3: Version-Snapshot Service

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase1/_shared_context.md` before starting.

## Objective

Ship the only service Phase 1 produces: `requirement_version_service.py`, which records byte-faithful
snapshots of a goal's requirements file into `requirement_versions`, content-hash-idempotent, with a
clean current/archived lifecycle. This is canon — Phase 4's `comment_service` copies this service's DB
shape, and Phase 4's `create_next()` open-comment gate builds ON `create_snapshot`. It writes the DB
only; the `.collab.md` file stays canonical and untouched.

## Dependencies

- **Requires completed:** sp2a (`requirements_render.hashing.content_hash`) and sp2b (the
  `requirement_versions` table + `UNIQUE(goal_slug, version)` constraint).
- **Assumed codebase state:** `requirement_versions` exists with the canonical columns; `content_hash` is
  importable from `cast_server.requirements_render.hashing`; `goal_service.py` / `task_service.py`
  demonstrate the `get_connection(db_path)` DB house pattern.

## Scope

**In scope:**
- New module `cast-server/cast_server/services/requirement_version_service.py` with four flat functions:
  `create_snapshot`, `get_current`, `get_version`, `list_versions`.
- Content-hash idempotency + single-transaction current→archived flip in `create_snapshot`.

**Out of scope (do NOT do these):**
- Comment CRUD (`requirement_comments` / `comment_events` writes) — **Phase 4**.
- The `create_next()` open-comment gate — **Phase 4** (it builds on this service; do not pre-build it).
- Any file write — the service touches the DB only (delegation contract: cast-server never writes artifact
  files; a snapshot is a *copy into* the DB).
- A `BEGIN IMMEDIATE` locking change — plan-review Decision #5 **accepts** the single-user read-then-write
  limitation; record `BEGIN IMMEDIATE` only as a documented fix-forward comment, do not implement it.
- The service's tests — sp4 owns `test_requirement_versions.py`. (You may REPL-exercise the service while
  developing; commit no test here.)
- Modeling on `orchestration_service.py` (file/manifest-based — Decision #1 forbids it).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/services/requirement_version_service.py` | Create | Does not exist |

## Detailed Steps

### Step 3.1: Establish the house DB pattern from the real models

Open `cast-server/cast_server/services/goal_service.py` (and/or `task_service.py`) and copy its
**data-access shape**: module-level flat functions, a `db_path: Path | None = None` parameter, the
`get_connection(db_path)` call for the handle, row-factory usage, and the row→dict conversion helper.
Match its import of `get_connection` (same module path) and its transaction/commit idiom. **Do NOT** look
at `orchestration_service.py` for this — it is file/manifest-based and would propagate a file-shaped
service across the fan-out (plan-review Decision #1, Opt A).

### Step 3.2: Implement the four functions

```python
"""Version snapshots for the requirements thin spine (refine-requirements-v2 Phase 1).

DB-only: writes requirement_versions; NEVER touches goal files (the .collab.md stays canonical).
House DB pattern: flat functions + injectable db_path + get_connection(db_path), modeled on
goal_service.py / task_service.py (NOT orchestration_service.py — plan-review Decision #1).
Phase 4's comment_service inherits this exact shape; Phase 4's create_next() gate builds on create_snapshot.
"""
from pathlib import Path
from datetime import datetime, timezone

from cast_server.db.connection import get_connection          # match the real import path
from cast_server.requirements_render.hashing import content_hash


def create_snapshot(goal_slug: str, content: str, created_by: str | None = None, *, db_path: Path | None = None) -> dict:
    """Record a content-hash-idempotent snapshot.

    Idempotent: if the current version's hash == content_hash(content), return that row unchanged
    (no new row). Otherwise insert version = (max existing version) + 1 as 'current' and flip the
    prior 'current' row to 'archived' — in ONE transaction.

    Concurrency (plan-review Decision #5): `version = max + 1` is a read-then-write. Under a default
    deferred BEGIN, two concurrent snapshots for the same goal could both read the same max and one
    insert would hit UNIQUE(goal_slug, version). ACCEPTED as a single-user/local limitation — no
    locking change now. Fix-forward if concurrency ever appears: wrap read+insert+archive-flip in a
    single `BEGIN IMMEDIATE` so the max-read and insert serialize. Phase 4's create_next() inherits this.
    """
    h = content_hash(content)
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection(db_path)
    try:
        current = conn.execute(
            "SELECT * FROM requirement_versions WHERE goal_slug=? AND status='current'",
            (goal_slug,),
        ).fetchone()
        if current is not None and current["content_hash"] == h:
            return _row_to_dict(current)                       # idempotent no-op

        next_version = (conn.execute(
            "SELECT COALESCE(MAX(version), 0) AS m FROM requirement_versions WHERE goal_slug=?",
            (goal_slug,),
        ).fetchone()["m"]) + 1

        # one transaction: archive prior current, insert new current
        if current is not None:
            conn.execute(
                "UPDATE requirement_versions SET status='archived' WHERE id=?",
                (current["id"],),
            )
        cur = conn.execute(
            """INSERT INTO requirement_versions
               (goal_slug, version, content, content_hash, status, created_at, created_by)
               VALUES (?, ?, ?, ?, 'current', ?, ?)""",
            (goal_slug, next_version, content, h, now, created_by),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM requirement_versions WHERE id=?", (cur.lastrowid,)
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()                                           # match goal_service's connection handling
```

- `get_current(goal_slug, *, db_path=None) -> dict | None` — the `status='current'` row or `None`.
- `get_version(goal_slug, version, *, db_path=None) -> dict | None` — by `(goal_slug, version)`.
- `list_versions(goal_slug, *, db_path=None) -> list[dict]` — all versions for the goal, ordered by
  `version` (ascending or descending — pick the order `task_service` uses for its list functions and stay
  consistent; document it in the docstring).
- `_row_to_dict` — match the row→dict helper `goal_service` uses (or `dict(row)` if rows are
  `sqlite3.Row`). Return plain dicts, never `sqlite3.Row` objects, never entities.
- **Connection/commit handling must mirror `goal_service`/`task_service` exactly** (whether they
  `get_connection` per call and close, or use a context manager). The snippet above is illustrative — copy
  the real idiom from the house models, including how they manage the row factory and commit boundary.

### Step 3.3: Confirm no file writes

`grep -n "open(" requirement_version_service.py` → nothing in write mode; no `Path.write_text`, no goal-dir
path construction. The service's universe is `requirement_versions` rows.

## Verification

### Automated Tests (permanent)
- None authored here — sp4's `test_requirement_versions.py` pins the behavior: v1 insert, identical-content
  no-op (no v2), changed-content → v2 with the prior row archived, and the `UNIQUE(goal_slug, version)`
  violation path. This sub-phase makes those tests pass.

### Validation Scripts (temporary — commit nothing)
```bash
cd cast-server && python -c "
import pathlib
from cast_server.db.connection import init_db
from cast_server.services import requirement_version_service as svc
p = pathlib.Path('/tmp/spine_svc.db'); p.unlink(missing_ok=True); init_db(p)
# A goal row may be needed for the FK — insert one if create_snapshot fails on FK:
import sqlite3
# (only if FK enforcement is on; check how other service tests seed a goal)
v1 = svc.create_snapshot('demo', 'hello', created_by='human', db_path=p); print('v1', v1['version'], v1['status'])
v1b = svc.create_snapshot('demo', 'hello', db_path=p); print('idempotent same version:', v1b['version'] == v1['version'])
v2 = svc.create_snapshot('demo', 'hello world', db_path=p); print('v2', v2['version'], v2['status'])
print('current is v2:', svc.get_current('demo', db_path=p)['version'])
print('list:', [r['version'] for r in svc.list_versions('demo', db_path=p)])
"
```
Expect: v1 version 1 'current'; idempotent True; v2 version 2 'current'; current is v2; prior archived.
(If FK enforcement rejects the insert because no `goals` row exists, seed a `goals` row first — mirror how
the existing service tests seed their parent rows; note that for sp4 to wire up.)

### Manual Checks
- The module imports `content_hash` from `requirements_render.hashing` (the canonical one) — not a local
  `hashlib` reimplementation.
- The current/archived flip and the insert are in one transaction (single `commit()`); no window where two
  rows are `'current'` for the same goal.
- The Decision #5 concurrency comment is present verbatim-in-spirit (accepted limitation + `BEGIN
  IMMEDIATE` fix-forward).

### Success Criteria
- [ ] `requirement_version_service.py` exists with `create_snapshot / get_current / get_version / list_versions`.
- [ ] `create_snapshot` is content-hash idempotent (identical content → same row, no new version).
- [ ] Changed content → `version = max + 1` 'current', prior flipped 'archived', in one transaction.
- [ ] All functions take `db_path: Path | None = None`, use `get_connection(db_path)`, return plain dicts.
- [ ] Imports the canonical `content_hash`; reimplements no hashing.
- [ ] No file writes anywhere; DB only.

## Execution Notes

- **Copy the real house pattern, not this snippet.** The code above is a guide; the authoritative shape is
  whatever `goal_service.py` / `task_service.py` actually do (connection lifecycle, row factory, commit).
  Match them so Phase 4's `comment_service` inherits a consistent idiom.
- Do NOT implement `BEGIN IMMEDIATE`. Decision #5 explicitly accepts the limitation; over-implementing
  here diverges from the recorded decision. A comment documenting the fix-forward is the deliverable.
- `created_by` is nullable ('human' or an agent name). `create_snapshot` may be called without it.
- **Spec-linked files:** none. New service module covered by no spec; `cast-delegation-contract.collab.md`
  is satisfied by writing the DB only (no on-demand spec edit needed — verify by NOT writing any file).
