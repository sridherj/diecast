# Refine Requirements v2: Phase 1 — Foundation: Spec-Kit Parser & Thin Sidecar Spine

## Overview

Phase 1 builds the downscaled keystone every later phase consumes: a **spec-kit parser** that turns
`refined_requirements.collab.md` into an ordered, typed block model, and a **thin DB sidecar spine**
— version snapshots, comment rows, and content hashes — with **no deterministic anchoring engine and
no per-element IDs**. The `.collab.md` file stays byte-canonical (FR-007 untouched); comments store a
`quoted_text` + `section_hint` and are re-located by a Claude subagent at runtime (high-level plan,
"Decisions Resolved at Plan Review" #1 and #9). The key insight from exploration + plan review: the
playbooks' DB-canonical/ULID keystone was rejected — files stay canonical, and the only deterministic
machinery kept is the three places where being wrong means silent data loss (comment rows exist,
version snapshots, conflict = content-hash compare).

**This is the first sub-phase planned in a parallel-waves fan-out.** Every module path, table name,
column name, and function signature below is **canon** — Phases 2, 3a, 3b, 4, and 5 adopt these names.
See "Canonical Decisions for Downstream Sub-Phases" at the end.

## Position in Overall Plan

```
Phase 0: SPIKES ✅ (human gate CLEARED 2026-06-11)
   ▼
▶ Phase 1: Parser & Thin Spine ◀ ── YOU ARE HERE (no dependencies; first wave)
   │
   ├──► Phase 2: Classification (recipes select over Phase 1's block model)
   │       ├──► Phase 3a: HTML Render (consumes ParsedRequirements)
   │       └──► Phase 3b: Router (independent of parser; depends on Phase 2 only)
   ├──► Phase 4: Annotation & Versioning (consumes requirement_versions/_comments tables + hashing)
   └──► Phase 5: Round-Trip (consumes content_hash() for conflict detection; adds change_request*)

Phase 1b (gbrain prompt upgrades) runs in parallel — zero overlap with this plan.
```

## Depends On (from prior plans)

First wave — no prior sub-phase decisions exist. Inputs are the high-level `plan.collab.md`
(Overview + Decisions Resolved at Plan Review + Phase 1 section) and
`refined_requirements.collab.md` (the file the parser must consume, and the test fixture).

## Operating Mode

**HOLD SCOPE** — the phase boundary was already surgically cut at plan review (owner, 2026-06-11):
"the anchoring engine is *deleted*", "**no `block_anchor` column, no element surrogate**", "Defer
routing columns to Phase 3b and `change_request*` tables to Phase 5". The scope reduction has
already happened at the plan level; this plan's job is rigorous adherence to the downscaled
definition — no re-adding deleted machinery, no further cuts. Every activity below traces to a
bullet in the Phase 1 section of `plan.collab.md`.

## Sub-phase: Phase 1 — Spec-Kit Parser & Thin Sidecar Spine

**Outcome:** `refined_requirements.collab.md` parses into an ordered, typed block model
(`ParsedRequirements`); the SQLite sidecar has `requirement_versions`, `requirement_comments`, and
`comment_events` tables created idempotently on both fresh and existing DBs; a version-snapshot
service exists with content-hash idempotency; and a golden-file test proves parsing + snapshotting
never mutates `.collab.md` bytes (`bin/cast-spec-checker` stays green on the file unchanged).

**Dependencies:** None (Phase 0 human gate already cleared).

**Estimated effort:** 1-2 sessions.

**Verification:**
- `pytest tests/test_requirements_parser.py` — the fixture (this goal's own
  `refined_requirements.collab.md`, frozen under `tests/fixtures/`) parses into exactly the expected
  typed blocks: 1 Intent, 7 UserStory (US1–US7), 20 FR (FR-001–FR-020), 6 SC (SC-001–SC-006),
  7 Constraint, 6 Scope, 1 Directional, 6 OpenQuestion — in source order, with correct `ref` tokens.
- `pytest tests/test_fr007_readonly_guard.py` — parse + snapshot leave the fixture bytes identical
  (sha256 before == after), and `bin/cast-spec-checker <fixture>` exits 0 (subprocess, same pattern
  as `tests/test_us7_spec_kit_shape.py`).
- `pytest tests/test_requirement_versions.py` — snapshot test pins version-snapshot + content-hash
  behavior: v1 insert, identical-content no-op, changed-content → v2 with prior archived.
- `pytest tests/test_migrations.py` (extended) — the three new tables exist after `_run_migrations()`
  on a pre-existing DB and after fresh `init_db()`.

### Key activities

**A. Design note — codify the resolved architecture** (~30 min, write first; it is the contract
the rest of this phase implements)

- Write `docs/design/2026-06-11-requirements-files-canonical-thin-spine.collab.md` (date prefix
  mandated by `cast-init-conventions.collab.md` FR-003 for `docs/design/`; `.collab.md` because it
  records owner decisions). Create `docs/design/` — it does not exist yet.
- Content: files-canonical + thin DB spine (comment rows / version snapshots / conflict hash); **no
  per-element IDs; no deterministic anchoring engine** — comments store `quoted_text` +
  `section_hint`, re-located by a Claude subagent (trust + iterate, plan-review decisions #1, #9);
  what was explicitly rejected (the playbooks' DB-canonical/ULID keystone AND heading-path/ordinal
  anchors) and the fallback if re-anchoring proves flaky (reintroduce a lightweight anchor).
  Link to `plan.collab.md` "Decisions Resolved at Plan Review".

**B. Grammar bridge + parser — `cast_server.requirements_render`** (the core deliverable)

- Create package `cast-server/cast_server/requirements_render/` (precedent: the
  `cast_server/plan_and_progress/` feature package) with four modules:
  - `__init__.py` — re-exports `parse_requirements`, `parse_requirements_file`, `Block`,
    `BlockKind`, `ParsedRequirements`.
  - `spec_grammar.py` — **the no-drift bridge** (owner-approved 2026-06-11):
    `importlib.util.spec_from_file_location` loads `bin/cast-spec-checker` (stdlib-only,
    import-safe — module level is regex + dataclass definitions) and re-exports its compiled
    regexes as the single grammar source: `US_HEADING_RE`, `FR_ID_RE`, `SC_ID_RE`,
    `EARS_SCENARIO_RE`, `SECTION_HEADING_RE`, `NEEDS_CLAR_INLINE_RE`. Checker path:
    `Path(__file__).resolve().parents[3] / "bin" / "cast-spec-checker"` — raise loudly (not
    silently) if missing. **The checker file is not modified at all.**
  - `blocks.py` — the typed model:
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
        ref: str | None       # "US1" | "FR-007" | "SC-001" | None — parsed in-memory only;
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
  - `parser.py` — `parse_requirements(text: str) -> ParsedRequirements` and
    `parse_requirements_file(path: Path) -> ParsedRequirements` (read-only; never writes).
- **Section → kind mapping** (uses the checker's `SECTION_HEADING_RE` spans, same algorithm as the
  checker's `_section_spans`):

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

- **Deliberate non-goals, stated in the module docstring:** blocks do NOT tile the file (table
  headers, dividers, intro prose between landmarks stay only in `source_text` — Phase 3a renders
  from blocks + falls back to `source_text` where it needs to); inline `[NEEDS CLARIFICATION]`
  markers inside a user story stay inside that `USER_STORY` block's body (only the Open Questions
  section emits `OPEN_QUESTION` blocks); this is a render model, **not** a comment-anchoring index.
- Unknown H2 sections land in `unrecognized_sections` (zero silent failures) — Phase 3a decides
  whether to render them raw or warn.
- `hashing.py` is deliberately tiny and import-light so Phases 4/5 can use it without the parser:
  `cast-server/cast_server/requirements_render/hashing.py` →
  `def content_hash(text: str) -> str: return hashlib.sha256(text.encode("utf-8")).hexdigest()`.
  **This exact function is the conflict-detection spine Phase 5 compares against — one canonical
  implementation, never reimplemented.**

**C. Thin DB spine — schema + migration** (house migration pattern)

- Append to `cast-server/cast_server/db/schema.sql` (the one `connection.py` `SCHEMA_PATH` reads —
  NOT the stale root-level `db/schema.sql`, see Design Review) AND add the identical
  `CREATE TABLE IF NOT EXISTS` statements to `_run_migrations()` in
  `cast-server/cast_server/db/connection.py` (precedent: `agent_error_memories`). Canonical DDL:
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
- **No `block_anchor` column, no element surrogate** — re-location is a runtime subagent step
  (Phase 4), not a stored key. **Deferred on purpose:** routing columns on `goals` → Phase 3b;
  `change_request*` + `notifications_outbox` → Phase 5.
- Verify `bin/run-migrations.py` picks the new tables up unchanged (it should — it drives
  `_run_migrations`); extend `tests/test_migrations.py` with the three new tables on both the
  fresh-DB and existing-DB paths.

**D. Version-snapshot service** (the only service Phase 1 ships; comment CRUD is Phase 4's)

- `cast-server/cast_server/services/requirement_version_service.py` (house pattern: flat functions,
  `db_path: Path | None = None` injectable + `get_connection(db_path)`, model: `goal_service.py` /
  `task_service.py` — the canonical **DB-access** house pattern. (Plan-review #1: `orchestration_service.py`
  shows the flat-function *style* but is file/manifest-based and never touches the DB — do NOT copy its
  data-access shape. Phase 4's `comment_service` inherits this same `get_connection(db_path)` pattern.)):
  - `create_snapshot(goal_slug: str, content: str, created_by: str | None = None, *, db_path=None) -> dict`
    — computes `content_hash(content)`; **idempotent**: if the current version's hash is identical,
    return it unchanged (no new row); else insert `version = max + 1` as `'current'` and flip the
    prior row to `'archived'`, in ONE transaction.
    - **Concurrency note (plan-review #5):** `version = max + 1` is a read-then-write. Under a default
      deferred `BEGIN`, two concurrent snapshots for the same goal could both read the same max and one
      insert would then hit the `UNIQUE(goal_slug, version)` constraint. **Accepted as a single-user/local
      limitation** — cast-server is single-user — so no locking change is required now. **Fix-forward if
      concurrency ever appears:** wrap the read+insert+archive-flip in a single `BEGIN IMMEDIATE`
      transaction so the max read and the insert are serialized. Phase 4's `create_next()` gate inherits
      this same discipline.
  - `get_current(goal_slug, *, db_path=None) -> dict | None`
  - `get_version(goal_slug, version, *, db_path=None) -> dict | None`
  - `list_versions(goal_slug, *, db_path=None) -> list[dict]`
  - Returns plain row-dicts. **Reads and writes DB only — never touches goal files** (the
    delegation contract forbids cast-server writing artifact files; snapshots are *copies into* the
    DB, the file remains canonical).
- Phase 4's `create_next()` open-comment gate builds ON this service — do not build the gate now.

**E. FR-007 read-only guard — golden-file tests**

- Freeze this goal's `refined_requirements.collab.md` as
  `tests/fixtures/refine_requirements_v2/refined_requirements.collab.md` (a frozen copy — the live
  goal file keeps evolving; pinned counts stay stable).
- `tests/test_requirements_parser.py` — typed-block expectations (counts/order/refs per
  Verification above); front-matter, title, preamble extraction; `unrecognized_sections == ()`;
  every block's `(line_start, line_end)` within file bounds and monotonically ordered.
  - **Unknown-H2 positive test (plan-review #3):** feed `parse_requirements()` a tiny in-string doc
    containing one unrecognized H2 (e.g. `## Appendix`); assert that exact heading text appears in
    `unrecognized_sections` and that **no** `Block` was emitted for it. The `== ()` assertion above only
    proves the empty case — this proves the zero-silent-failure capture path Phase 3a is told to consume.
  - **Multi-line bullet grouping test (plan-review #4):** the fixture's `Constraints` bullets are
    multi-line (`- **bold lead:**` + wrapped continuation). Pick one known multi-line Constraint and
    assert its `Block.body` contains text from a **continuation** line (not just line 1) and
    `line_end > line_start`; assert an indented sub-bullet does **not** start a new block. Guards against a
    naive line-splitter that passes the count check (7 markers) while truncating each body to its first line.
- `tests/test_fr007_readonly_guard.py` — sha256 of fixture bytes before == after
  `parse_requirements_file()` + `create_snapshot()` (tmp DB); then run `bin/cast-spec-checker`
  on the fixture as a subprocess (pattern: `tests/test_us7_spec_kit_shape.py` `CHECKER`
  constant) and assert exit code 0.
- `tests/test_requirement_versions.py` — the snapshot/hash pinning test per Verification; plus
  `UNIQUE(goal_slug, version)` violation raises; plus a `spec_grammar` smoke test (bridge imports,
  `US_HEADING_RE.match("### US1 — Foo")` truthy) so a moved/renamed checker fails loudly in CI.

### Design review

- **Spec consistency** — `cast-init-conventions.collab.md` FR-003 (date prefix under `docs/design/`)
  and FR-001 (authorship suffix) honored by the design note name. The `_v2` filename versioning rule
  does NOT apply to requirement versions: versions live in the DB sidecar (FR-011 keeps only the
  current file in the goal folder) — noted in the design note. No spec conflict; Phase 1 introduces
  no user-facing behavior (no UI, no API, no agent I/O contract), so per the registry rules **no new
  spec and no `/cast-update-spec` step is needed in this phase** (Phases 3a/3b/4/5 will need them).
- **⚠️ Two `schema.sql` files exist:** root `db/schema.sql` (4289 B) and
  `cast-server/cast_server/db/schema.sql` (3784 B) have diverged; `connection.py` reads ONLY the
  latter. Activity C edits the canonical one. Flag: confirm root `db/schema.sql` is legacy and
  either delete it or sync it in a separate housekeeping commit — do not let a future phase edit
  the dead copy.
- **Naming** — `requirement_versions` / `requirement_comments` / `comment_events` follow the house
  plural-table convention (`goals`, `tasks`, `agent_runs`, `agent_error_memories`) ✓. Package name
  `requirements_render` matches the high-level plan's literal module path ✓.
- **Architecture** — FK `ON DELETE CASCADE` deliberately deviates from `agent_runs`' `SET NULL`:
  sidecar rows are meaningless without their goal; cascading is the correct lifecycle. Noted here so
  the deviation is visible, not accidental.
- **Error & rescue** — `spec_grammar.py` raises `FileNotFoundError` with the expected path if the
  checker is missing (never a silent fallback grammar); `create_snapshot` is transactional (no
  half-applied current/archived flip); unknown H2 sections surface in `unrecognized_sections`
  (zero silent failures).
- **Security** — no new API surface, no user input paths in this phase; `parse_requirements_file`
  reads whatever path the caller passes (path validation is the responsibility of the Phase 3a/4
  route layer when one appears — flagged forward to those plans).

## Design Review Flags

| Flag | Action |
|------|--------|
| Diverged duplicate `db/schema.sql` at repo root; canonical is `cast-server/cast_server/db/schema.sql` | Activity C edits the canonical file only; confirm/retire the root copy in a housekeeping commit |
| FK `ON DELETE CASCADE` deviates from `agent_runs`' `SET NULL` pattern | Intentional — documented in schema comment + design note |
| Unknown H2 sections could silently vanish from the future render | `ParsedRequirements.unrecognized_sections` makes the skip visible; Phase 3a must consume it |
| `bin/cast-spec-checker` gets copied to `~/.claude/skills/diecast/bin/` on install (cast-hooks precedent) | Bridge loads the checker from the REPO path only (server always runs in-repo); checker itself is untouched, so the installed copy is unaffected |
| Path validation on file-reading APIs | Not applicable this phase (no route layer); flagged forward to Phase 3a/4 plans |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| `bin/cast-spec-checker` is moved/renamed or gains import side effects, breaking the importlib bridge | Med | Bridge raises loudly at import with the expected path; CI smoke test (`test_requirement_versions.py` grammar test) fails on the first run; checker docstring already says "Internal use" so moves are unlikely |
| Pinned block counts make parser tests brittle | Low | Fixture is a FROZEN copy under `tests/fixtures/` — the live goal file can evolve freely |
| Migration runs against real user DBs on upgrade | Med | `CREATE TABLE IF NOT EXISTS` everywhere (both schema.sql and `_run_migrations`); covered by `tests/test_migrations.py` fresh + existing paths |
| Later phases re-add anchoring machinery out of habit (the playbooks still describe ULIDs) | Med | The design note (Activity A) + the explicit "deliberately absent" schema comment are the canonical "do not re-inherit" markers |
| Parser scope creep into a comment-anchoring index | Med | HOLD SCOPE: module docstring states "render model, not an anchoring index"; no anchor-shaped fields exist on `Block` to misuse (`ref` is parsed, never stored) |

## Open Questions

**None blocking.** The two decisions this plan had to make beyond the high-level plan were resolved
during planning: (1) grammar reuse mechanism = importlib bridge loading `bin/cast-spec-checker` by
path, checker untouched (owner-approved 2026-06-11); (2) unknown-section handling =
`unrecognized_sections` field rather than a ninth block kind (keeps the locked 8-kind set, zero
silent failures). Everything else was already settled at plan review.

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| `cast-init-conventions.collab.md` | Authorship suffixes (US1/FR-001), date prefixes (FR-003), `_v2` versioning rule | None — design note complies; DB versioning sits outside the filename rule (only current version lives in the folder, FR-011) |
| `cast-delegation-contract.collab.md` | cast-server never writes artifact files | None — `requirement_version_service` writes DB only; the file stays canonical and untouched |

## Canonical Decisions for Downstream Sub-Phases (adopt these names)

| Decision | Canonical value |
|----------|-----------------|
| Parser package | `cast_server.requirements_render` (`cast-server/cast_server/requirements_render/`) |
| Grammar source | `bin/cast-spec-checker` regexes, re-exported via `cast_server.requirements_render.spec_grammar` (importlib bridge; checker never modified) |
| Block kinds | `BlockKind` enum: `intent, user_story, fr, sc, constraint, scope, directional, open_question` (closed set; unknown H2s → `ParsedRequirements.unrecognized_sections`) |
| Block shape | `Block{kind, level, body, heading, ref, line_start, line_end}` — frozen dataclass; `ref` ("FR-007") is parsed at read time and used **in-memory only** — never persisted to a DB column and never used as a comment anchor (the thin-spine decision deleted stored anchors; `requirement_comments` has no `ref`/anchor column) |
| Parse entrypoints | `parse_requirements(text) -> ParsedRequirements`; `parse_requirements_file(path)` (read-only) |
| Content hash | `cast_server.requirements_render.hashing.content_hash(text) -> str` — sha256 hex of UTF-8 bytes; Phase 5 conflict detection MUST use this exact function |
| Tables | `requirement_versions`, `requirement_comments`, `comment_events` (DDL above; in `cast-server/cast_server/db/schema.sql` + `_run_migrations()`) |
| Comment row contract | `{goal_slug, version, quoted_text, section_hint, body, state(open/resolved/orphaned), author, author_kind(human/agent)}` — NO anchor column |
| Version service | `cast_server.services.requirement_version_service` — `create_snapshot / get_current / get_version / list_versions`, `db_path=` injectable, idempotent by content hash |
| Design note | `docs/design/2026-06-11-requirements-files-canonical-thin-spine.collab.md` |
| Test fixture | `tests/fixtures/refine_requirements_v2/refined_requirements.collab.md` (frozen copy) |
| Deferred by design | Routing columns on `goals` → Phase 3b; `change_request*` / `notifications_outbox` → Phase 5; comment CRUD service + API → Phase 4; block-diff engine → Phase 4 |

## Decisions

_Appended by `cast-plan-review` (run_20260611_160312_654fa9). BIG CHANGE scope — all 4 sections; 5 issues raised, 5 resolved, 0 deferred._

- **2026-06-11T16:33:35Z — Issue #1 (Architecture): the version service cites `orchestration_service.py` as its model, but that service is file/manifest-based and never touches the DB. Fix the canonical reference?** — Decision: Opt A — re-point the model to `goal_service.py` / `task_service.py` (the real `get_connection(db_path)` DB house pattern). Rationale: this service is canon that Phase 4's `comment_service` copies; the cited model didn't demonstrate the DB-access shape, risking a file-shaped service propagating across the fan-out.
- **2026-06-11T16:33:35Z — Issue #2 (Code Quality): the canonical table says `Block.ref` is "never stored anywhere", contradicting `ref` being a dataclass field. Fix the wording?** — Decision: Opt A — reword both the canonical table and `blocks.py` to "parsed in-memory only; never persisted to a DB column and never used as a comment anchor". Rationale: the contradiction could lead a downstream implementer to drop the in-memory field or add a `ref` column to `requirement_comments` — reintroducing the stored anchor the thin-spine decision deleted.
- **2026-06-11T16:33:35Z — Issue #3 (Tests): only the empty case (`unrecognized_sections == ()`) is tested; the zero-silent-failure capture path is unproven. Add a positive test?** — Decision: Opt A — add a synthetic-fixture test feeding one unknown H2 (e.g. `## Appendix`) and asserting it appears in `unrecognized_sections` with no block emitted. Rationale: Phase 3a is explicitly told to consume `unrecognized_sections`; an `== ()` assertion passes even if capture is fully broken.
- **2026-06-11T16:33:35Z — Issue #4 (Tests): the multi-line Constraints bullets need continuation lines folded into one block's body, but no test pins this. Add coverage?** — Decision: Opt A — assert a known multi-line Constraint's `Block.body` includes continuation-line text and `line_end > line_start`, and that a nested sub-bullet does not start a new block. Rationale: a naive line-splitter passes the count check (7 markers) while truncating each body to its first line — a body-truncation bug would ship green and surface as missing text in the Phase 3a render.
- **2026-06-11T16:33:35Z — Issue #5 (Performance/Txn): `create_snapshot`'s `version = max + 1` is a read-then-write with an unpinned SQLite locking mode (UNIQUE-violation race under concurrency). How to handle?** — Decision: Opt B — document it as an accepted single-user/local limitation, with `BEGIN IMMEDIATE` recorded as the fix-forward if concurrency ever appears. Rationale: very low probability on a single-user local cast-server; pinning the intended discipline is cheap insurance since Phase 4's `create_next()` gate builds on this service.
