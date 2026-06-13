# Execution Manifest: Refine Requirements v2 — Phase 1 (Parser & Thin Sidecar Spine)

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:

1. Start a new Claude session in the repo root (`/home/sridherj/workspace/diecast`, which resolves to
   `/data/workspace/diecast`).
2. Tell Claude: "Read `docs/execution/refine-req-v2-phase1/_shared_context.md` then execute
   `docs/execution/refine-req-v2-phase1/spN_<name>/plan.md`."
3. After completion, update the Status column below and commit.

Source plan: `docs/plan/2026-06-11-refine-requirements-v2-phase1-foundation.md` (Activities A–E).
Cross-phase interface ledger: `docs/plan/refine-requirements-v2-decisions-so-far.md`.
The whole phase ships as one PR (or one PR per parallel branch that merges cleanly — disjoint files).

## Sub-Phase Overview

| #   | Sub-phase                                                          | Directory/File              | Plan activity | Depends On       | Status      | Notes |
|-----|-------------------------------------------------------------------|-----------------------------|---------------|------------------|-------------|-------|
| 1   | Design note — files-canonical + thin-spine contract               | `sp1_design_note/`          | A             | —                | Not Started | Docs only; the "do not re-inherit anchors/ULIDs" marker. Create `docs/design/`. |
| 2a  | Parser package `cast_server.requirements_render`                  | `sp2a_parser/`              | B             | 1                | Not Started | New package (5 modules). Parallel with 2b — disjoint files. |
| 2b  | Thin DB spine — schema + migration + migration test               | `sp2b_db_spine/`            | C             | 1                | Not Started | Edits canonical `schema.sql` + `_run_migrations()` + `test_schema_migration.py`. Parallel with 2a. |
| 3   | Version-snapshot service                                          | `sp3_version_service/`      | D             | 2a, 2b           | Not Started | New `requirement_version_service.py`. Needs hashing (2a) + tables (2b). |
| 4   | FR-007 guard + parser/version tests                               | `sp4_fr007_tests/`          | E             | 2a, 2b, 3        | Not Started | Freeze fixture + 3 test files; `Delegate: /cast-pytest-best-practices`. ~30–40% of phase weight. |

Status: Not Started → In Progress → Done → Verified → Skipped

**No decision gates.** The plan's "Open Questions: None blocking" — the two planning-level decisions
(importlib grammar bridge; `unrecognized_sections` over a 9th block kind) were resolved before this split.
No `gate_*` files exist in this project.

## Dependency Graph

```
            ┌──▶ sp2a_parser ─────┐
sp1_design ─┤                     ├──▶ sp3_version_service ──▶ sp4_fr007_tests
            └──▶ sp2b_db_spine ───┘
```

- sp2a ∥ sp2b run simultaneously after sp1 (disjoint files: `requirements_render/` vs `db/` + migration test).
- sp3 needs BOTH: `content_hash` (sp2a) and the `requirement_versions` table (sp2b).
- sp4 needs all three code sub-phases (it tests the parser, the migration, and the service).

## Execution Order

### Sequential Group 1
1. **sp1_design_note** — write `docs/design/2026-06-11-requirements-files-canonical-thin-spine.collab.md`.
   The contract the rest of the phase implements. No code; independently verifiable by file existence +
   content checklist.

### Parallel Group 2 (after sp1 — independent files, run simultaneously)
2a. **sp2a_parser** — the `requirements_render` package: `spec_grammar` (importlib bridge over
   `bin/cast-spec-checker`), `blocks`, `parser`, `hashing`, `__init__`. Touches only the new package.
2b. **sp2b_db_spine** — append 3 tables + 3 indexes to the **canonical** `cast-server/cast_server/db/schema.sql`,
   mirror them in `_run_migrations()`, extend `cast-server/tests/test_schema_migration.py`. Touches only
   `db/` + the migration test. No overlap with 2a.

### Sequential Group 3 (after sp2a AND sp2b)
3. **sp3_version_service** — `requirement_version_service.py` (`create_snapshot` / `get_current` /
   `get_version` / `list_versions`), content-hash idempotent, house DB pattern. New file only.

### Sequential Group 4 (after sp3)
4. **sp4_fr007_tests** — freeze the fixture; `test_requirements_parser.py`, `test_fr007_readonly_guard.py`,
   `test_requirement_versions.py`; `Delegate: /cast-pytest-best-practices`. Tests pin the *agreed* contract;
   a failing pin means an upstream bug to fix in its owning sub-phase, not a number to rewrite.

## Files Touched by More Than One Sub-Phase

**None.** Every sub-phase owns a disjoint file set — this is what makes sp2a ∥ sp2b safe and the whole
phase mergeable without conflicts:

| File set | Sub-phase | Owner notes |
|----------|-----------|-------------|
| `docs/design/2026-06-11-requirements-files-canonical-thin-spine.collab.md` | sp1 only | New file. |
| `cast-server/cast_server/requirements_render/{__init__,spec_grammar,blocks,parser,hashing}.py` | sp2a only | New package. |
| `cast-server/cast_server/db/schema.sql` | sp2b only | Append-only. |
| `cast-server/cast_server/db/connection.py` | sp2b only | `_run_migrations()` block added after `agent_error_memories`. |
| `cast-server/tests/test_schema_migration.py` | sp2b only | Extended with table/index existence assertions. |
| `cast-server/cast_server/services/requirement_version_service.py` | sp3 only | New file. |
| `cast-server/tests/fixtures/refine_requirements_v2/refined_requirements.collab.md` | sp4 only | New frozen fixture. |
| `cast-server/tests/test_requirements_parser.py` | sp4 only | New file. |
| `cast-server/tests/test_fr007_readonly_guard.py` | sp4 only | New file. |
| `cast-server/tests/test_requirement_versions.py` | sp4 only | New file. |

`bin/cast-spec-checker` is **read by** sp2a (importlib bridge) and **run by** sp4 (subprocess) but
**modified by neither** — it stays byte-identical.

## Out-of-Manifest (intentionally NO sub-phase)

- **Routing columns on `goals`** → Phase 3b.
- **`change_request*` tables + `notifications_outbox`** → Phase 5.
- **Comment CRUD service + API, block-diff engine, runtime re-location subagent** → Phase 4.
- **The `create_next()` open-comment gate** → Phase 4 (builds on sp3's `create_snapshot`).
- **`/cast-update-spec` / a new `docs/specs/` entry** → none this phase (Phase 1 ships no user-facing
  behavior). Specs come with Phases 3a/3b/4/5.
- **Retiring the legacy root `db/schema.sql`** → separate housekeeping commit; sp2b only edits the
  canonical copy.
- **`BEGIN IMMEDIATE` locking on `create_snapshot`** → not built (plan-review Decision #5 accepts the
  single-user limitation; recorded as a fix-forward comment only).

## Progress Log

<!-- Update after each sub-phase completes. -->
