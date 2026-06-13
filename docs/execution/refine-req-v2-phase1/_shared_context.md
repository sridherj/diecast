# Shared Context: Refine Requirements v2 — Phase 1 (Parser & Thin Sidecar Spine)

> Read this file at the start of EVERY sub-phase in this project, then read your sub-phase's
> `plan.md`. This file is the DRY reference; sub-phase files do not repeat it.

## Source Documents
- Plan: `docs/plan/2026-06-11-refine-requirements-v2-phase1-foundation.md` (canon — every module path,
  table name, column name, and function signature in it is binding on Phases 2/3a/3b/4/5).
- Cross-phase decisions: `docs/plan/refine-requirements-v2-decisions-so-far.md` (the cumulative fan-out
  interface ledger — adopt these names verbatim).
- Plan-review verdict: `cast-plan-review` run_20260611_160312_654fa9, BIG CHANGE scope — 5 issues raised,
  5 resolved, 0 deferred. The five resolutions are folded into the plan's `## Decisions` block and into
  the relevant sub-phases below. Implementation proceeds without re-litigation.

## Project Background

Refine Requirements v2 turns `refined_requirements.collab.md` into a navigable, annotatable artifact.
Exploration's playbooks proposed a DB-canonical, per-element-ULID "keystone." **Plan review rejected
that.** The locked architecture is **files-canonical + thin DB sidecar**:

- The `.collab.md` file stays the single byte-canonical source of truth (FR-007 — never mutated).
- The DB holds only a **thin spine**: version snapshots, comment rows, and a content hash for conflict
  detection. There is **no deterministic anchoring engine and no per-element ID column.**
- Comments store `quoted_text` + a `section_hint` and are re-located at runtime by a Claude subagent
  (a Phase 4 concern; trust-and-iterate, plan-review decisions #1 and #9).

The keystone insight: the only deterministic machinery kept is the three places where being wrong means
**silent data loss** — comment rows exist, version snapshots are recorded, and a conflict is a
content-hash compare. Everything else (anchors, ULIDs, element surrogates) was deleted at plan review.

Phase 1 is the first wave in a parallel fan-out. It builds the keystone the later phases consume:
a **spec-kit parser** (`refined_requirements.collab.md` → an ordered, typed block model) and the
**thin DB spine** (three tables + a version-snapshot service + content hashing).

## Operating Mode — HOLD SCOPE

The phase boundary was surgically cut at plan review: "the anchoring engine is *deleted*", "**no
`block_anchor` column, no element surrogate**", "defer routing columns to Phase 3b and `change_request*`
tables to Phase 5." The reduction already happened at the plan level. This project's job is **rigorous
adherence to the downscaled definition** — do NOT re-add deleted machinery (anchors/ULIDs/element IDs),
do NOT make further cuts. Every activity traces to a bullet in the Phase 1 plan.

## Codebase Conventions

- **Feature package layout.** New parser code is a self-contained package under
  `cast-server/cast_server/requirements_render/` (precedent: `cast-server/cast_server/plan_and_progress/`).
- **Schema-first DB.** `cast-server/cast_server/db/connection.py` reads `SCHEMA_PATH = <pkg>/db/schema.sql`
  on fresh init, then runs `_run_migrations(conn)`. New tables are added in **two** places that must stay
  identical: appended to `db/schema.sql` AND added as `CREATE TABLE IF NOT EXISTS` in `_run_migrations()`
  (precedent: the `agent_error_memories` block at `connection.py:125`). `init_db()` and `_run_migrations()`
  both live in `connection.py`; `bin/run-migrations.py` drives `_run_migrations` unchanged.
- **Service layer = flat functions + injectable `db_path`.** The canonical DB-access house pattern is
  `services/goal_service.py` / `services/task_service.py`: module-level functions, `db_path: Path | None
  = None` parameter, `get_connection(db_path)` for the handle, returning plain row-dicts. **Do NOT model
  on `orchestration_service.py`** — it shows the flat-function *style* but is file/manifest-based and
  never touches the DB (plan-review Decision #1, Opt A).
- **The spec checker is canon grammar, never modified.** `bin/cast-spec-checker` (stdlib-only,
  import-safe — module level is regex + dataclass defs) owns the spec-kit regexes. Phase 1 re-exports
  them via an importlib bridge; it does **not** copy, fork, or edit the checker.
- **`docs/design/` design notes.** Date-prefixed per `cast-init-conventions.collab.md` FR-003;
  `.collab.md` suffix per FR-001 when recording owner decisions. The `docs/design/` directory does not
  exist yet — sp1 creates it.

## Key File Paths

| File | Role | Sub-phase |
|------|------|-----------|
| `docs/design/2026-06-11-requirements-files-canonical-thin-spine.collab.md` | NEW design note — the "do not re-inherit anchors/ULIDs" contract | sp1 |
| `cast-server/cast_server/requirements_render/__init__.py` | NEW — re-exports `parse_requirements`, `parse_requirements_file`, `Block`, `BlockKind`, `ParsedRequirements` | sp2a |
| `cast-server/cast_server/requirements_render/spec_grammar.py` | NEW — importlib bridge re-exporting `bin/cast-spec-checker` regexes | sp2a |
| `cast-server/cast_server/requirements_render/blocks.py` | NEW — `BlockKind`, `Block`, `ParsedRequirements` dataclasses | sp2a |
| `cast-server/cast_server/requirements_render/parser.py` | NEW — `parse_requirements` / `parse_requirements_file` | sp2a |
| `cast-server/cast_server/requirements_render/hashing.py` | NEW — `content_hash(text) -> str` (the conflict-detection spine) | sp2a |
| `cast-server/cast_server/db/schema.sql` | EDIT (append 3 tables + 3 indexes) — the CANONICAL schema `connection.py` reads | sp2b |
| `cast-server/cast_server/db/connection.py` | EDIT — mirror the 3 `CREATE TABLE IF NOT EXISTS` in `_run_migrations()` | sp2b |
| `cast-server/tests/test_schema_migration.py` | EXTEND — assert the 3 tables exist on fresh + pre-existing DB paths | sp2b |
| `cast-server/cast_server/services/requirement_version_service.py` | NEW — `create_snapshot / get_current / get_version / list_versions` | sp3 |
| `cast-server/tests/fixtures/refine_requirements_v2/refined_requirements.collab.md` | NEW — FROZEN copy of the goal's requirements file (test fixture) | sp4 |
| `cast-server/tests/test_requirements_parser.py` | NEW — typed-block expectations | sp4 |
| `cast-server/tests/test_fr007_readonly_guard.py` | NEW — byte-identity + spec-checker-clean guard | sp4 |
| `cast-server/tests/test_requirement_versions.py` | NEW — snapshot/hash pinning + grammar smoke test | sp4 |

**Fixture source:** `goals/refine-requirements-v2/refined_requirements.collab.md` (the live goal file —
copy it FROZEN into `tests/fixtures/`; the live file keeps evolving, the frozen copy keeps pinned counts
stable).

### ⚠️ Path drift flags (the plan names files that do not exist under those exact names)

| Plan reference | Actual file in this repo | Action |
|---|---|---|
| `tests/test_migrations.py` (Verification + Activity C) | `cast-server/tests/test_schema_migration.py` | sp2b extends the **real** file; do not create a new `test_migrations.py` |
| `tests/test_us7_spec_kit_shape.py` (subprocess-checker precedent for FR-007 guard) | **does not exist** | sp4 establishes the subprocess pattern from scratch (see sp4 Execution Notes); no precedent file to copy |
| Tests live at `tests/...` in the plan | actual root is `cast-server/tests/...` | all test paths below are written with the real `cast-server/tests/` prefix |

## Data Schemas & Contracts (copy verbatim — canon for downstream phases)

### Typed block model (`blocks.py`)

```python
class BlockKind(str, Enum):
    INTENT = "intent"; USER_STORY = "user_story"; FR = "fr"; SC = "sc"
    CONSTRAINT = "constraint"; SCOPE = "scope"
    DIRECTIONAL = "directional"; OPEN_QUESTION = "open_question"

@dataclass(frozen=True)
class Block:
    kind: BlockKind
    level: int            # 1 = whole-section block, 2 = element within a section
    body: str             # exact source slice, byte-faithful
    heading: str | None   # e.g. "US1 — WHAT/HOW separation"; None for bullet blocks
    ref: str | None       # "US1" | "FR-007" | "SC-001" | None — parsed in-memory ONLY;
                          # never persisted to a DB column, never used as a comment anchor
    line_start: int       # 1-indexed in source
    line_end: int

@dataclass(frozen=True)
class ParsedRequirements:
    title: str                    # H1 text
    front_matter: dict            # YAML header (status/confidence/...)
    preamble: str                 # blockquote between H1 and first H2 (spec maturity etc.)
    blocks: tuple[Block, ...]     # source order
    unrecognized_sections: tuple[str, ...]  # H2s the typed model skipped — never silent
    source_text: str              # full original text, untouched
    content_hash: str             # sha256 hex of source_text (UTF-8)
```

### Section → kind mapping (uses the checker's `SECTION_HEADING_RE` spans, same algorithm as the checker's `_section_spans`)

| H2 section | Blocks emitted |
|---|---|
| `Intent` | ONE `INTENT` block, level 1, whole section |
| `User Stories` | one `USER_STORY` block per `US_HEADING_RE` match, level 2, `ref="US1"…` |
| `Functional Requirements` | one `FR` block per table row matching `FR_ID_RE`, level 2, `ref="FR-001"…`, body = the row line |
| `Success Criteria` | one `SC` block per row matching `SC_ID_RE`, level 2 |
| `Constraints` | one `CONSTRAINT` block per top-level bullet, level 2 |
| `Out of Scope` | one `SCOPE` block per top-level bullet, level 2 |
| heading starting `Directional` | ONE `DIRECTIONAL` block, level 1, whole section (HOW quarantined wholesale) |
| `Open Questions` | one `OPEN_QUESTION` block per top-level bullet, level 2 |

**Deliberate non-goals (state in the `parser.py` module docstring):** blocks do NOT tile the file (table
headers, dividers, intro prose between landmarks stay only in `source_text`); inline `[NEEDS
CLARIFICATION]` markers inside a user story stay inside that `USER_STORY` block's body (only the Open
Questions section emits `OPEN_QUESTION` blocks); this is a **render model, NOT a comment-anchoring index.**
Unknown H2 sections land in `unrecognized_sections` (zero silent failures).

### Content hash (`hashing.py`) — the conflict-detection spine

```python
import hashlib
def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
```

This exact function is what Phase 5 compares against for conflict detection. ONE canonical
implementation, never reimplemented. `hashing.py` is deliberately tiny and import-light so Phases 4/5
can use it without importing the parser.

### Grammar bridge (`spec_grammar.py`)

`importlib.util.spec_from_file_location` loads `bin/cast-spec-checker` and re-exports its compiled
regexes as the single grammar source: `US_HEADING_RE`, `FR_ID_RE`, `SC_ID_RE`, `EARS_SCENARIO_RE`,
`SECTION_HEADING_RE`, `NEEDS_CLAR_INLINE_RE` (plus `_section_spans` if the parser reuses it).
Checker path: `Path(__file__).resolve().parents[3] / "bin" / "cast-spec-checker"`. **Raise loudly**
(`FileNotFoundError` with the expected path) if missing — never a silent fallback grammar. The checker
file is **not modified at all.**

### Canonical DDL (the thin spine — `schema.sql` + `_run_migrations()`)

```sql
-- Requirements thin spine (refine-requirements-v2 Phase 1).
-- Deliberately absent: block_anchor / element surrogate columns (thin-spine decision #1);
-- routing columns (Phase 3b); change_request* tables (Phase 5).
CREATE TABLE IF NOT EXISTS requirement_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_slug TEXT NOT NULL,
    version INTEGER NOT NULL,                -- 1, 2, 3, ... per goal
    content TEXT NOT NULL,                   -- full .collab.md snapshot, byte-faithful
    content_hash TEXT NOT NULL,              -- requirements_render.hashing.content_hash(content)
    status TEXT NOT NULL DEFAULT 'current',  -- 'current' | 'archived'
    created_at TEXT NOT NULL,                -- ISO timestamp
    created_by TEXT,                         -- agent name or 'human'
    UNIQUE (goal_slug, version),
    FOREIGN KEY (goal_slug) REFERENCES goals(slug) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS requirement_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_slug TEXT NOT NULL,
    version INTEGER NOT NULL,                -- version the comment was left against
    quoted_text TEXT NOT NULL,               -- the reviewer's selection, verbatim
    section_hint TEXT,                       -- nearest heading at capture time (a hint, not a key)
    body TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'open',      -- 'open' | 'resolved' | 'orphaned'
    author TEXT NOT NULL,
    author_kind TEXT NOT NULL DEFAULT 'human', -- 'human' | 'agent' (FR-013: the ONLY distinction)
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY (goal_slug) REFERENCES goals(slug) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comment_events (    -- append-only trail (US5 S3 retrieval is free)
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    comment_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,                -- 'created'|'resolved'|'reopened'|'orphaned'|'relocated'
    actor TEXT,
    payload TEXT,                            -- JSON
    created_at TEXT NOT NULL,
    FOREIGN KEY (comment_id) REFERENCES requirement_comments(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_req_versions_goal_status ON requirement_versions(goal_slug, status);
CREATE INDEX IF NOT EXISTS idx_req_comments_goal_state ON requirement_comments(goal_slug, state);
CREATE INDEX IF NOT EXISTS idx_comment_events_comment ON comment_events(comment_id);
```

**No `block_anchor` column, no element surrogate.** `FK ON DELETE CASCADE` is intentional (sidecar rows
are meaningless without their goal) — a deliberate deviation from `agent_runs`' `SET NULL`, documented in
the schema comment + the design note. Comment CRUD (`requirement_comments` writes) is **Phase 4**, not
Phase 1 — only `requirement_versions` gets a service this phase.

### Version-snapshot service (`requirement_version_service.py`)

```python
create_snapshot(goal_slug: str, content: str, created_by: str | None = None, *, db_path=None) -> dict
get_current(goal_slug, *, db_path=None) -> dict | None
get_version(goal_slug, version, *, db_path=None) -> dict | None
list_versions(goal_slug, *, db_path=None) -> list[dict]
```

`create_snapshot` computes `content_hash(content)`; **idempotent** — if the current version's hash is
identical, return it unchanged (no new row); else insert `version = max + 1` as `'current'` and flip the
prior row to `'archived'`, in ONE transaction. Returns plain row-dicts. **Reads and writes the DB only —
never touches goal files** (the delegation contract forbids cast-server writing artifact files; a snapshot
is a *copy into* the DB, the file stays canonical). Phase 4's `create_next()` open-comment gate will build
ON this service — do not build the gate now.

## Pre-Existing Decisions (plan-review, verbatim — reference by `Decision #N`)

| # | Section | Decision |
|---|---------|----------|
| 1 | Architecture | Version service models on `goal_service.py` / `task_service.py` (real `get_connection(db_path)` DB house pattern), **NOT** `orchestration_service.py` (file/manifest-based). |
| 2 | Code Quality | `Block.ref` wording: "parsed in-memory only; never persisted to a DB column and never used as a comment anchor." No `ref`/anchor column on `requirement_comments`. |
| 3 | Tests | Add a positive unknown-H2 test: feed a synthetic doc with one unrecognized H2 (e.g. `## Appendix`); assert it appears in `unrecognized_sections` with **no** block emitted. The `== ()` empty assertion is not enough. |
| 4 | Tests | Multi-line bullet grouping test: assert a known multi-line `Constraints` bullet's `Block.body` includes continuation-line text and `line_end > line_start`, and a nested sub-bullet does NOT start a new block. Guards against a naive line-splitter that passes the count check but truncates each body to line 1. |
| 5 | Performance/Txn | `create_snapshot`'s `version = max + 1` read-then-write: **accepted single-user/local limitation**; `BEGIN IMMEDIATE` recorded as the fix-forward if concurrency ever appears. Phase 4's `create_next()` inherits this discipline. |

## Relevant Specs

| Spec | Linked-files overlap with this plan | Action this phase |
|------|-------------------------------------|-------------------|
| `cast-init-conventions.collab.md` | `docs/design/` naming (FR-001 authorship suffix, FR-003 date prefix); `_v2` filename rule; FR-011 (only current version lives in the goal folder) | sp1's design-note name complies; DB versioning sits OUTSIDE the filename rule (versions live in the DB sidecar). No spec edit. |
| `cast-delegation-contract.collab.md` | "cast-server never writes artifact files" | sp3's `requirement_version_service` writes the DB only; the `.collab.md` stays canonical and untouched. No spec edit. |

**No new spec and no `/cast-update-spec` step is needed in Phase 1** — it introduces no user-facing
behavior (no UI, no API, no agent I/O contract). Per the registry rules, specs come with Phases 3a/3b/4/5.
Sub-phases here do NOT modify any spec-linked production file, so no on-demand spec read is required.

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|-----------|------|-----------|--------|-------------------|
| sp1 — Design note (the contract) | Sub-phase | — | sp2a, sp2b | — |
| sp2a — Parser package (`requirements_render`) | Sub-phase | sp1 | sp3 | sp2b |
| sp2b — Thin DB spine (schema + migration + migration test) | Sub-phase | sp1 | sp3 | sp2a |
| sp3 — Version-snapshot service | Sub-phase | sp2a (hashing), sp2b (tables) | sp4 | — |
| sp4 — FR-007 guard + parser/version tests | Sub-phase | sp2a, sp2b, sp3 | (none) | — |

No decision gates. No skip-conditional sub-phases. (The plan's "Open Questions: None blocking.")

## Out-of-Phase (deferred by design — do NOT build here)

- Routing columns on `goals` → **Phase 3b**.
- `change_request*` tables + `notifications_outbox` → **Phase 5**.
- Comment CRUD service + API, block-diff engine, the runtime re-location subagent → **Phase 4**.
- The `create_next()` open-comment gate → **Phase 4** (builds on sp3's service).
- Reintroducing any anchor/ULID/element-surrogate → **never** unless the runtime re-anchoring proves
  flaky (the design note's documented fallback), and only as a deliberate later decision.

## Housekeeping Flag (not a sub-phase)

Two `schema.sql` files exist and have diverged: root `db/schema.sql` (4289 B, legacy) and
`cast-server/cast_server/db/schema.sql` (3784 B, canonical — the one `connection.py` reads). sp2b edits
the **canonical** one only. Retiring/syncing the root copy is a **separate housekeeping commit** — out of
scope for this phase; flagged so no later phase edits the dead copy.
