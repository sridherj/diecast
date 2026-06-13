# sp1 Proposal Spine — Execution Output

**Status:** completed
**Run:** run_20260612_051546_451992 (cast-subphase-runner)
**Date:** 2026-06-12

## What was built

The Phase 5 proposal substrate — three tables, three indexes, one pydantic payload
model, and the migration/model test coverage that pins them. Nothing applies anything
yet (that is sp2–sp4); this is the receiving substrate only.

### 1. Canonical schema (`cast-server/cast_server/db/schema.sql`)

The three Phase 5 tables (`change_requests`, `change_request_events`,
`notifications_outbox`) + their indexes + the thin-spine guard comment were **already
present** in the canonical schema (lines 160–205) from the proposal-spine groundwork.
Verified against `_shared_context.md` "Data Schemas & Contracts" — they match verbatim,
including:
- `author_type TEXT NOT NULL CHECK (author_type IN ('human','agent'))` (FR-013: data, not a code branch)
- `base_version INTEGER` referencing `requirement_versions.version` (owner decision #2 — no surrogate FK)
- the thin-spine comment block warning future readers not to "restore" a `spec_elements` surrogate.

No change was needed here beyond verification.

### 2. Migration mirror (`cast-server/cast_server/db/connection.py` `_run_migrations()`)

This was the missing half. Added the three `CREATE TABLE IF NOT EXISTS` statements +
three `CREATE INDEX IF NOT EXISTS` statements, mirroring the canonical schema, so a
legacy (pre-Phase-5) DB upgrades on next boot. Updated the stale comment that had
declared `change_request*` tables "deliberately absent."

The mirror follows the **established precedent**: as with the landed
`requirement_versions`/`comment_events` mirror, table-header inline comments are dropped
in the migration's triple-quoted strings (the stored SQLite SQL differs only in
comments/whitespace between the two paths, exactly as it already does for the spine
tables). Both paths were verified to produce **functionally identical** tables
(columns, types, NOT NULL, defaults, PK, foreign keys, indexes all match via
`PRAGMA table_info` / `foreign_key_list`).

### 3. Payload model (`cast-server/cast_server/models/requirements_writeback.py` — created)

`RequirementsWriteback` pydantic v2 model. **Placement note:** the plan named
`cast_server/schemas/`, but the landed convention is `cast_server/models/` (where
`AgentOutput` lives) — adopted the landed location per the decisions-so-far
"do not fork the vocabulary" rule. Mirrors the emitter-controlled columns; the
server-managed `id`/`status`/timestamps/`author*` are deliberately absent. A
`model_validator` enforces: a `modification`/`annotation` must name its `target_quote`;
a pure `addition` must not.

`requirements_writeback` needs **no enum registration** — `AgentOutput.artifacts` is
`list[dict]`, so the new artifact type is additive for free and unknown to old parsers
by construction.

### 4. Tests

- **`cast-server/tests/test_change_request_model.py`** (created, 10 tests): good
  addition/modification payloads validate; bad `kind` rejected; missing `base_version`
  rejected; empty `proposed_body` rejected; addition-with-target and
  modification/annotation-without-target rejected; `AgentOutput` carries the artifact;
  a legacy parser ignores the unknown type without error.
- **`cast-server/tests/test_schema_migration.py`** (extended, +4 tests): three tables +
  three indexes present on a fresh DB; `author_type` CHECK enforced (out-of-enum →
  `IntegrityError`, both legal members insert); legacy-DB upgrade path creates the
  tables/indexes and is idempotent (double `_run_migrations`), with the CHECK constraint
  surviving the migration path too.

## Verification

- `uv run pytest cast-server/tests/test_schema_migration.py cast-server/tests/test_change_request_model.py` → **28 passed**.
- Fresh-DB table listing → `['change_request_events', 'change_requests', 'notifications_outbox']`.
- Fresh-init vs migrated DB → **functionally identical** tables (cols + FKs match).

## Success criteria (all met)

- [x] Three tables present on a fresh DB and after migrating a pre-Phase-5 DB.
- [x] `schema.sql` ↔ `_run_migrations()` aligned for the new tables (pinned by existence + migration tests).
- [x] `author_type` CHECK enum (`human|agent`) enforced (exercised on both fresh + migration paths).
- [x] `RequirementsWriteback` validates good / rejects bad payloads; unknown artifact type ignored by an old parser.
- [x] No `spec_elements`/`surrogate` FK introduced; thin-spine comment present.
- [x] Migration is idempotent (runs twice, no error).

## Deviations from plan (intentional, low-risk)

- **Model location:** `models/` not `schemas/` — the package the plan referenced
  (`schemas/`) does not exist; `models/` is where `AgentOutput` and all contract models
  live. Landed-convention rule applied.
- **`RequirementsWriteback` validator:** implemented as a `model_validator(mode="after")`
  (kind↔target cross-field rule) rather than the plan's stub `field_validator` that did
  no validation. Same intent, working enforcement.

## Notes for downstream sub-phases

- sp2 (intake) `POST /api/goals/{slug}/change-requests` writes `change_requests` +
  appends `change_request_events('proposed')` + enqueues `notifications_outbox`.
- sp3a conflict predicate keys off `base_version` (integer version) + `content_hash()`
  over the located region.
- The `RequirementsWriteback` payload is the emitter-side shape; the server derives
  `author`/`author_type` at intake (humans never self-assert `author_type`).
