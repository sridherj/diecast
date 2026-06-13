# Sub-phase 1: Proposal Spine — change-request schema, event trail, outbox + payload model

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase5/_shared_context.md` before starting.

## Objective

Lay the substrate the rest of Phase 5 builds on. Three tables (`change_requests`,
`change_request_events`, `notifications_outbox`) must exist on a fresh DB **and** migrate cleanly
onto a pre-Phase-5 DB, and a downstream agent must be able to emit a validated
`requirements_writeback` artifact in its `output.json` that round-trips through a pydantic model
without breaking any existing parent. **Nothing applies anything yet** — this is the proposal
substrate only.

## Dependencies

- **Requires completed:** None within Phase 5. Consumes only landed Phase 1 schema (`requirement_versions`) and the contract-v2 `output.json` shape. **Build first.**
- **Assumed codebase state:** `cast-server/cast_server/db/schema.sql` already has `requirement_versions`/`requirement_comments`/`comment_events`; `_run_migrations()` already mirrors them.

## Scope

**In scope:**
- Add the three Phase 5 tables to the canonical schema + the migration mirror.
- Define the `RequirementsWriteback` pydantic v2 model and register `requirements_writeback` as an `artifacts[].type` value.
- Migration + model tests (fresh-DB + legacy-DB-upgrade paths).

**Out of scope (do NOT do these):**
- No intake route (sp2). No conflict logic (sp3a). No outbox relay loop (sp3b). No file writer (sp4).
- Do **not** add a `target_surrogate` / `spec_elements` FK — that table does not exist (thin spine).
- Do **not** touch the root `db/schema.sql` (legacy/diverged).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/db/schema.sql` | Modify | Canonical schema; has Phase 1–4 tables; header reserves "change_request* tables (Phase 5)" |
| `cast-server/cast_server/db/connection.py` | Modify | `_run_migrations()` mirrors every `CREATE TABLE IF NOT EXISTS` |
| `cast-server/cast_server/schemas/requirements_writeback.py` | Create | Does not exist |
| `cast-server/cast_server/schemas/__init__.py` | Modify (maybe) | Export the new model if the package re-exports |
| `cast-server/tests/test_schema_migration.py` | Modify | Has Phase 1–4 table-existence assertions; extend |
| `cast-server/tests/test_change_request_model.py` | Create | Does not exist |

## Detailed Steps

### Step 1.1: Add the three tables to the canonical schema

Add the `change_requests`, `change_request_events`, `notifications_outbox` `CREATE TABLE IF NOT
EXISTS` blocks **verbatim from `_shared_context.md` → "Data Schemas & Contracts"** to
`cast-server/cast_server/db/schema.sql`, immediately after the `comment_events` / requirements
indexes block. Add a comment block at the top of the change-request tables noting the **thin-spine
substitution** so a future reader does not "restore" a surrogate FK:

```sql
-- Phase 5 (round-trip write-back). THIN SPINE: change_requests locates its target by
-- target_quote + section_hint (mirrors requirement_comments) — there is NO spec_elements
-- surrogate FK (that table never existed). base_version is the integer requirement_versions.version
-- the change assumed. Do not "restore" a surrogate column.
```

Also add the matching indexes:

```sql
CREATE INDEX IF NOT EXISTS idx_change_requests_goal_status ON change_requests(goal_slug, status);
CREATE INDEX IF NOT EXISTS idx_change_request_events_cr ON change_request_events(change_request_id);
CREATE INDEX IF NOT EXISTS idx_notifications_outbox_status ON notifications_outbox(status);
```

> **Statement-separator caveat (from the schema header):** `init_db()` splits this file on the
> statement separator, so inline comments inside `CREATE TABLE` must not contain it. Match the exact
> comment style already used in `requirement_versions`.

### Step 1.2: Mirror byte-identically in `_run_migrations()`

In `cast-server/cast_server/db/connection.py`, `_run_migrations()`, add the **same three
`CREATE TABLE IF NOT EXISTS` statements + indexes** so a legacy (pre-Phase-5) DB upgrades on next
boot. Phase 1 canon: the canonical `schema.sql` and `_run_migrations()` must stay byte-aligned. Copy
the statements; do not paraphrase them.

### Step 1.3: Define the `RequirementsWriteback` pydantic v2 model

Create `cast-server/cast_server/schemas/requirements_writeback.py`. Mirror the table columns the
downstream agent controls (NOT the server-managed ones like `id`/`status`/timestamps):

```python
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class RequirementsWriteback(BaseModel):
    """Additive output.json artifact a downstream agent rides to propose a requirement change.

    Carried as one item in AgentOutput.artifacts[] with type 'requirements_writeback'. Parents
    that don't understand it MUST ignore it (contract-v2 rule) — so this is purely additive.
    """
    kind: Literal["addition", "modification", "annotation"]
    proposed_body: str = Field(min_length=1)
    base_version: int                       # the requirement_versions.version assumed (owner decision #2)
    target_quote: str | None = None         # NULL ⇒ pure addition (no target region)
    section_hint: str | None = None
    origin_phase: str | None = None
    origin_activity_id: str | None = None
    origin_artifact_path: str | None = None

    @field_validator("target_quote")
    @classmethod
    def _modification_needs_target(cls, v, info):
        # A modification/annotation must name what it changes; an addition must not.
        return v
```

> Cross-check the *actual* `AgentOutput` / `artifacts[]` model location before wiring (likely
> `cast_server/schemas/` or wherever contract-v2 lives — grep `class AgentOutput`). Register
> `"requirements_writeback"` wherever artifact `type` is enumerated/validated (if it is a free
> string today, no change is needed beyond documenting the new value — confirm by reading the
> contract-v2 model). Keep it **additive**.

### Step 1.4: Tests

`cast-server/tests/test_change_request_model.py`:
- `RequirementsWriteback` validates a good addition payload (`kind="addition"`, `target_quote=None`).
- Rejects a bad `kind` (e.g. `"delete"`) → `ValidationError`.
- Rejects a missing `base_version` → `ValidationError`.
- An `AgentOutput` carrying `artifacts=[{... type:"requirements_writeback" ...}]` parses, **and** an
  old/minimal parser fixture that doesn't know the type ignores it without error (prove "parents
  ignore unknown fields").

Extend `cast-server/tests/test_schema_migration.py`:
- Assert the three new tables exist on a freshly-initialized DB (mirror the Phase 1 sp2b
  table-existence pattern: query `sqlite_master`).
- Assert the legacy-upgrade path: initialize a DB **without** the Phase 5 tables (or a snapshot of
  the pre-Phase-5 schema), run `_run_migrations()`, assert the three tables + their indexes + the
  `author_type` CHECK now exist. Assert idempotency: running migrations twice does not error.

→ **Delegate:** `/cast-pytest-best-practices` over `test_change_request_model.py` +
`test_schema_migration.py`. Review its output for: legacy-DB migration idempotency coverage
(CREATE-IF-NOT-EXISTS re-run), and that the CHECK constraint on `author_type` is actually exercised.

## Verification

### Automated Tests (permanent)
- `uv run pytest cast-server/tests/test_schema_migration.py` — green, including the new
  three-table existence + legacy-upgrade + idempotency assertions.
- `uv run pytest cast-server/tests/test_change_request_model.py` — green.

### Validation Scripts (temporary)
- Fresh DB: `uv run python -c "from cast_server.db.connection import get_connection; c=get_connection(); print([r[0] for r in c.execute(\"select name from sqlite_master where type='table' and name like 'change_request%' or name='notifications_outbox'\")])"` → lists all three.

### Manual Checks
- Open `schema.sql` and `connection.py` side by side; confirm the three `CREATE TABLE` blocks are byte-identical between them.
- Confirm the thin-spine comment block is present in `schema.sql`.

### Success Criteria
- [ ] Three tables present on a fresh DB and after migrating a pre-Phase-5 DB.
- [ ] `schema.sql` ↔ `_run_migrations()` are byte-aligned for the new tables (pinned by the existence test).
- [ ] `author_type` CHECK enum (`human|agent`) enforced.
- [ ] `RequirementsWriteback` validates good / rejects bad payloads; unknown artifact type ignored by an old parser.
- [ ] No `spec_elements`/`surrogate` FK introduced; thin-spine comment present.
- [ ] Migration is idempotent (runs twice, no error).

## Execution Notes
- The plan prose says "Four tables" once but lists three — **three tables** is correct; the fourth is
  the `RequirementsWriteback` *artifact* model, not a table.
- `base_version INTEGER` references `requirement_versions.version` (owner decision #2) — **not** a
  synthetic row id. Do not add an FK to `requirement_versions.id`.
- **Spec-linked files:** this sub-phase modifies the DB schema referenced indirectly by
  `cast-requirements-render.collab.md`; you are *adding* tables, not changing landed behavior — no
  SAV regression. The roundtrip spec itself is authored in sp5.
