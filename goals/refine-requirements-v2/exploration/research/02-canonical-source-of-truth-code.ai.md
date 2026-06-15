# Code Exploration: Canonical Source of Truth for Requirements (Step 2 — PRIMARY)

**Goal context:** Refine Requirements v2 — Workflow-Aware, HTML-First Requirements Refinement.
Resolve the keystone architecture question: are requirements **DB entities with auto-generated
HTML + markdown renders** (mirroring Diecast's goal/task pattern) or do **files stay canonical
with a thin DB layer only for comments/versions**? Plus the **stable-ID scheme** (FR-008) and
**archive mechanism** (US5), all while preserving the **spec-kit markdown contract** (FR-007).

**Codebase:** `/home/sridherj/workspace/diecast` (same git repo as `/data/workspace/diecast`;
`.cast` symlinks the goal dir). cast-server is the relevant subtree.
**Date:** 2026-06-11
**Tooling note:** code-review-graph MCP graph was not built (startup hook reported "No knowledge
graph found"), so this exploration used the built-in `Explore` subagent + direct Glob/Grep/Read.
Two `Explore` subagents returned only terse completion stubs without findings, so all citations
below are from direct reads — every file:line was verified firsthand.

---

## TL;DR for the synthesizer

**The "DB-canonical → generated file renders" pattern the spec proposes is not hypothetical —
it already ships in this codebase, in two flavors, and requirements are the conspicuous
exception that was never migrated to it.**

- **Tasks** are *fully* DB-canonical: every field lives in a `tasks` table column, and
  `tasks.md` is a **derived, read-only render** re-emitted from the DB after every mutation
  (`_rerender_tasks_md`, `task_service.py:389`). This is a working, end-to-end precedent for
  exactly the architecture Option A proposes.
- **Goals** are DB-canonical *for metadata only*: `goal.yaml` is a one-way render of DB state
  (`_write_goal_yaml`, `goal_service.py:337`), stamped "Read-only render of DB state. Do not
  edit directly."
- **Requirements content** (`refined_requirements.collab.md`) is the opposite: **files-canonical,
  agent-authored**, with **zero DB representation**. The agent writes the file directly
  (`agents/cast-refine-requirements/...md:305`), the server only **scans the folder** to detect
  it (`pages.py:113-125`), and editing is a plain textarea → `write_text` (`api_artifacts.py:94`).
- **Stable element IDs (FR-008) do not exist.** `FR-001`/`US1`/`SC-001` are *agent-typed text
  labels* in markdown — nothing allocates, persists, or guarantees them across edits. The
  spec-checker can detect duplicates but there is no durable identity an agent rewrite can't
  renumber.
- **Versioning, archival, comments, and diffing are all greenfield** — no tables, no models, no
  routes, no markup.
- **FR-007 is a *structural* markdown contract, not byte-exact.** It's enforced by
  `bin/cast-spec-checker` (section presence + `FR-NNN`/`SC-NNN` regex + EARS patterns), so a
  DB→markdown render only needs to be *structurally faithful*, not byte-identical, to keep
  downstream agents green.

**Migration cost asymmetry:** Option A (DB-canonical requirements) is a *known* pattern here —
the tasks code is a copy-paste-shaped template for it — but it requires (a) a real element-level
data model, (b) rewriting `cast-refine-requirements` to write rows instead of a file, and (c) a
DB→spec-kit-markdown renderer. Option B (files-canonical + thin DB comment/version layer) is a
smaller diff but inherits the **fragile-text-anchor** problem the Multi-Lens insight flagged,
because there is no element identity to key comments to without inventing one anyway.

---

## 1. Data Model & Schema

Canonical schema: `cast-server/cast_server/db/schema.sql` (SQLite). Pydantic mirrors live in
`cast-server/cast_server/models/`.

### Entities

| Table | File:line | What it stores | Canonical for content? |
|-------|-----------|----------------|------------------------|
| `goals` | `schema.sql:1-14` | slug (PK), title, status, phase, origin, in_focus, dates, tags, **folder_path**, gstack_dir, external_project_dir | **Metadata only** — no requirement content |
| `tasks` | `schema.sql:16-39` | id (PK autoincr), goal_slug (FK), phase, parent_id (self-FK), title, outcome, action, task_type, estimate_size, status, sort_order, **task_artifacts** (JSON paths), rationale, is_spike | **Yes — fully DB-canonical** |
| `agent_runs` | `schema.sql:73-92` | id (PK), agent_name, goal_slug (FK), task_id (FK), status, input_params/output/artifacts (JSON), timestamps, skills_used, claude_agent_id | Yes (DB-only, never file-synced) |
| `scratchpad_entries`, `goal_suggestions`, `agents` | `schema.sql:41-70` | misc | Mixed |

```
goals (slug PK) ──1:N── tasks (goal_slug FK, parent_id self-FK for subtasks)
   │                        └── task_artifacts: JSON array of relative file paths
   │                            (the ONLY link from a row to document files)
   └── folder_path ──→ goals/<slug>/   ← requirement DOCUMENTS live here as files
                          ├── goal.yaml                     (DB→file render, metadata)
                          ├── requirements.human.md         (file-canonical, human)
                          ├── refined_requirements.collab.md (file-canonical, agent-authored)
                          ├── tasks.md                      (DB→file render, full content)
                          ├── plan.collab.md
                          └── exploration/…, .context-map.md (file→file render)

agent_runs (id PK) ──N:1── goals, tasks   (execution telemetry, orthogonal to this decision)
```

**Critical observation:** there is **no `requirements` table, no `spec` table, and no
element/section table.** The finest-grained content unit the DB knows about is a *task row*.
A requirement document is, to the database, an opaque file path inside `folder_path`. Any
"requirements as DB entities" design is **net-new schema**, not a migration of existing columns.

The Pydantic models confirm this: `models/goal.py` has no content fields (just metadata, with a
`folder_path: str`); `models/task_v2.py:42-68` is the rich entity (the `Task` is where Diecast's
"structured entity" investment actually went). There is no `Requirement`, `UserStory`, `FR`, or
`SpecElement` model anywhere.

---

## 2. Existing Implementation

### 2a. The reusable precedent — tasks: DB-canonical with `tasks.md` render

This is the single most important asset for Step 2. `task_service.py:389` `_rerender_tasks_md`:

- Reads top-level + subtasks from the DB grouped by phase (`task_service.py:399-418`).
- Renders deterministic markdown lines (`_render_task`, `task_service.py:458`).
- Writes `goals/<slug>/tasks.md` with a header: `"<!-- AUTO-GENERATED: Read-only render of DB
  state. Do not edit directly. -->"` (`task_service.py:427`).
- Is called after **every** task mutation: create (`:173`), batch create (`:206`), update
  (`:385`), status change (`:237`, `:274`), and from `task_suggestion_service.py:109,143`.

This is precisely Option A's render loop — *write rows, regenerate the human-readable file* —
already proven against a real entity. A requirements equivalent would add a second renderer
(`_rerender_requirements_html` + `_rerender_requirements_md`) over a new element table.

### 2b. Goals: DB-canonical metadata with `goal.yaml` render

`goal_service.py:337` `_write_goal_yaml` and `:366` `_update_goal_yaml_fields` render `goal.yaml`
from DB state, same "Read-only render of DB state. Do not edit directly" stamp
(`goal_service.py:359`). Mutations (`create_goal:82`, `update_status:143`, `update_phase:176`,
`update_config:262`, `toggle_focus:296`) write the DB first, then re-render the yaml. **One-way,
DB→file.** Confirms the house style: *DB is truth, files are projections, the projection is
labeled non-authoritative.*

### 2c. Requirements: the un-migrated exception (files-canonical)

- **Authoring:** `agents/cast-refine-requirements/cast-refine-requirements.md:305` — "Step 3.1:
  Write refined_requirements.collab.md … Render the final spec against
  `templates/cast-spec.template.md`. Write to `goals/{goal-slug}/refined_requirements.collab.md`."
  The *agent* hand-writes the file. No service, no DB, no render pipeline.
- **Discovery:** `pages.py:113-125` (`goal_detail`) detects which phases have artifacts by
  **scanning the folder** against `PHASE_ARTIFACTS` glob patterns (`config.py:53-58`:
  `"requirements": ["requirements.human.md", "refined_requirements.collab.md"]`). There is no DB
  registry of documents — the filesystem *is* the index.
- **Viewing:** `api_artifacts.py:110` `artifact_sidebar` reads the file and renders markdown→HTML
  via the Python `markdown` lib (`api_artifacts.py:6,132`) with extensions
  `["fenced_code","tables","toc","codehilite"]` (`:14`). Output is **one opaque HTML blob**
  passed to `artifact_content(html)` (`fragments/artifact_sidebar.html:14`) — no per-element
  wrapping, no `id=` anchors.
- **Editing:** `api_artifacts.py:60` `edit_artifact` returns a textarea of raw file content;
  `:81` `save_artifact` does `resolved.write_text(content)` (`:94`). Whole-file overwrite. Only
  `.human.md`/`.collab.md` are editable (`validate_artifact_path:44`).
- **Rich-HTML precedent:** `pages.py:299` `/preso/review/{goal_slug}` serves a pre-generated
  `presentation/review.html` straight from the goal folder via `HTMLResponse(path.read_text())`.
  Proof the system already serves bespoke generated HTML documents from disk — a cheap path for
  an HTML requirements render even under Option B.

### 2d. The spec-kit markdown contract (what FR-007 must preserve)

- **Shape:** `templates/cast-spec.template.md` defines the canonical structure: `## User Stories`
  → `### US1 — … (Priority: P1)` → `**As a** … **I want to** … **so that** …` →
  `**Independent test:**` → `**Acceptance scenarios:**` (EARS `WHEN …, THE SYSTEM SHALL …`) →
  `## Functional Requirements` table (`| FR-001 | … |`) → `## Success Criteria` table
  (`| SC-001 | … |`) → `## Open Questions`. The current refined spec
  (`refined_requirements.collab.md`) follows it exactly.
- **Enforcement:** `bin/cast-spec-checker` (executable Python; `cast-spec-checker.md:31`) parses
  **structurally** (`cast-spec-checker.md:35-48`): required sections present, each US has a
  Priority + Independent Test + ≥1 EARS scenario, `FR-NNN`/`SC-NNN` present and unique, no orphan
  `[NEEDS CLARIFICATION]`. Output is `<file>:<line>: <severity> <rule_id>: <msg>` (`:55`).
- **Implication for Step 2:** FR-007/SC-004 do **not** require byte-identical output. Any
  canonical store that can emit a *structurally faithful* spec-kit markdown will pass the checker
  and keep planner/task-suggester/spec-checker green. The regression check is concrete and cheap:
  **run `bin/cast-spec-checker` on the rendered file** + run the downstream agent chain.

---

## 3. Gap Analysis

| # | Gap | Severity | Evidence |
|---|-----|----------|----------|
| 1 | **No element-level identity for requirement sub-parts (FR-008).** `FR-001`/`US1`/`SC-001` are agent-typed text, not allocated/persisted IDs. An agent rewrite renumbers freely; comments have nothing durable to anchor to. | **Critical** — this is the keystone the whole goal hangs on | No `Requirement`/`SpecElement` model; `schema.sql` has no element table; checker only dedups text (`cast-spec-checker.md:43-44`) |
| 2 | **No DB representation of requirement content at all.** Requirements are files the DB can't query, version, or relate. | **Critical** for Option A; defines the migration | `schema.sql:1-14` goals = metadata; agent writes file directly (`cast-refine-requirements.md:305`) |
| 3 | **No versioning / archival / diff infrastructure (US5, FR-017).** No version column, no archive table/folder convention, no diff util. | **High** — entirely greenfield either way | grep across `schema.sql`+`models/` finds only `contract_version` fields (unrelated) |
| 4 | **No comment/annotation model or markup (US4, FR-009/010).** No `comments` table; rendered HTML is one blob with no anchors. | **High** — greenfield; depends on gap #1 | `artifact_sidebar.html:14` renders `{{ html }}` blob; no `comments` table |
| 5 | **Editing is whole-file overwrite, last-write-wins.** No structured patching, no conflict detection — directly hostile to round-trip write-back (US7/FR-020). | **High** | `api_artifacts.py:94` `resolved.write_text(content)` |
| 6 | **Artifact discovery is filesystem-scan, not a registry.** Adding versioned/archived documents means either more glob conventions or a real DB index. | **Medium** | `pages.py:113-125` rglob over `PHASE_ARTIFACTS` |
| 7 | **No HTML render of requirements today.** Only generic markdown→HTML in a sidebar; no progressive disclosure, no L1/L2/L3 (US3/FR-005/006). | **Medium** (this is Step 5's job, but the store must feed it) | `api_artifacts.py:132` generic `md.markdown(...)` |
| 8 | **`refined_requirements` authorship is `collab` but there's no machine guard** that downstream-written changes round-trip (US7). Today a downstream agent writing elsewhere leaves the requirements file silently stale. | **Medium** | `config.py:74` `"refined_requirements": "collab"`; no write-back path exists |

---

## 4. Patterns & Conventions

- **Architecture:** lightweight MVCS — `routes/` (FastAPI controllers) → `services/` (business
  logic, raw SQL) → `db/connection.py` (SQLite) → `models/` (Pydantic). Services use **raw SQL via
  `get_connection()`**, not an ORM (`goal_service.py:36`, `task_service.py:399`). No Alembic-driven
  entity churn — one baseline migration (`alembic/versions/cfe1a46fdefc_baseline.py`); `schema.sql`
  is the hand-maintained source of truth.
- **House rule: DB is canonical, files are read-only projections.** Both file renders carry the
  identical "AUTO-GENERATED: Read-only render of DB state. Do not edit directly." stamp
  (`goal_service.py:359`, `task_service.py:427`). A requirements-as-DB design would inherit this
  convention verbatim. **Note the tension:** `refined_requirements.collab.md` is *editable in the
  UI* today (`validate_artifact_path:44`) — moving it under the read-only-render rule changes the
  edit model from "edit the file" to "edit rows, regenerate the file."
- **Render-after-mutate:** every service mutation re-emits its file projection synchronously
  (`task_service.py:173/206/237/274/385`). Simple, no event bus, no async — cheap to extend with a
  second (HTML) renderer.
- **Authorship suffix convention:** `.human.md` / `.collab.md` / `.ai.md` encode who owns a file
  (`config.py:64-76`, `api_artifacts.py:136-143`). `.ai.md` files additionally get a generated
  `.context-map.md` TOC (`context_map.py:87`). Requirements are `collab`.
- **Frontend:** server-rendered Jinja2 + **HTMX** (`base.html:13`) + vanilla CSS
  (`static/style.css`). Markdown editing uses vendored **EasyMDE** wired on `htmx:afterSwap`
  (`base.html:153-168`). **There is no npm/package.json, no React/Vite/webpack build step** —
  confirmed by absence of any `package.json` in-repo. (This is decisive context for Step 4's
  React/Next.js question: the stack is deliberately build-free server-rendered.)
- **Path safety:** `_validate_artifact_path_base` (`api_artifacts.py:20`) restricts file ops to
  `GOALS_DIR` or a goal's `external_project_dir`. Any new render/write path must route through it.

---

## 5. Entry Points & Flow

### Flow A — How a requirement document reaches the human today (files-canonical)

```
cast-refine-requirements agent
  └─ writes goals/<slug>/refined_requirements.collab.md   (cast-refine-requirements.md:305)
        (renders against templates/cast-spec.template.md, by hand)
                       │
browser GET /goals/<slug>  (pages.py:77 goal_detail)
  └─ scans folder for PHASE_ARTIFACTS globs (pages.py:113-125) → has_artifacts flags
                       │
browser opens artifact (HTMX) → GET /api/artifacts/artifact-sidebar (api_artifacts.py:110)
  └─ read_text() → md.markdown(content, extensions) (api_artifacts.py:131-133)
       → ONE html blob → artifact_sidebar.html:14 {{ artifact_content(html) }}
                       │
edit: GET /api/artifacts/edit → textarea (api_artifacts.py:60)
save: PUT /api/artifacts/save → resolved.write_text(content) (api_artifacts.py:94)  ← whole-file
```

### Flow B — How tasks reach the human today (DB-canonical render — the Option A template)

```
/cast-tasks agent or task_service API mutation
  └─ INSERT/UPDATE tasks row(s)  (task_service.py create/update/...)
       └─ _rerender_tasks_md(goal_slug)  (task_service.py:389)   ← runs after EVERY mutation
            ├─ SELECT tasks grouped by phase (task_service.py:399-418)
            ├─ _render_task() → markdown lines (task_service.py:458)
            └─ write goals/<slug>/tasks.md  (task_service.py:451-453)
                 header: "AUTO-GENERATED: Read-only render of DB state"
  UI reads task rows directly from DB (pages.py:87 get_tasks_for_goal) — md is for agents/humans-on-disk
```

**Read this side-by-side:** Flow A is what requirements do now; Flow B is what they'd do under
Option A. The delta is a new element table + a `_rerender_requirements_md` and
`_rerender_requirements_html` modeled on `_rerender_tasks_md`, plus rewriting the refine agent to
emit rows (or structured JSON the service ingests) instead of a finished file.

### Flow C — Rich generated HTML served from disk (already works)

```
GET /preso/review/<slug> (pages.py:299) → read presentation/review.html → HTMLResponse
```
A requirements HTML render could be served the same way regardless of which store wins.

---

## 6. Tests & Coverage

- **Task render is tested** (the precedent is not just code, it's covered): `task_service.py`
  docstrings reference re-render behavior; `cast-server/tests/` has integration + e2e + ui dirs.
- **Spec shape is tested:** `tests/test_us7_spec_kit_shape.py` exercises `bin/cast-spec-checker`
  directly (`cast-spec-checker.md:33`) — this is your **ready-made FR-007/SC-004 regression
  harness**: render → run checker → assert exit 0.
- **Artifact editing:** path-validation logic (`api_artifacts.py:20-57`) is the security-sensitive
  surface; verify it's covered before extending write paths.
- **Gaps in coverage relevant to Step 2:** nothing tests versioning/archival/comments (they don't
  exist), and there is no test asserting "downstream change round-trips into requirements file"
  (US7) — because no such mechanism exists. New work here is greenfield-with-tests, not
  retrofit-into-tested-code.
- **Test DB pattern:** services accept `db_path=` injection throughout (`goal_service.py:33`,
  `task_service.py`) — new requirement services should follow this for testability.

---

## 7. Config & Dependencies

- **Markdown→HTML:** Python `markdown` (`import markdown as md`, `api_artifacts.py:6`) with
  `fenced_code, tables, toc, codehilite`. Server-side, synchronous. (No `mistune`/`markdown-it`.)
- **YAML:** `pyyaml` for `goal.yaml` (`goal_service.py:10`).
- **DB:** stdlib `sqlite3` via `db/connection.py`; schema in `db/schema.sql`; Alembic present but
  single baseline migration.
- **Web:** FastAPI + Jinja2 templates (`deps.templates`) + HTMX (`static/htmx.min.js`). EasyMDE
  vendored (`static/vendor/easymde/`). **No JS build toolchain.**
- **Config surface (`config.py`):** `GOALS_DIR`, `PHASES` (`requirements, exploration, plan,
  execution`), `PHASE_ARTIFACTS` (glob patterns per phase, `:53`), `AUTHORSHIP_TYPES`/
  `ARTIFACT_DEFAULTS` (`:64-76`), `STARTER_TASKS` (`:78`), `STATUS_TRANSITIONS`. Adding a
  requirements entity touches `schema.sql` (+ new table), a new `requirements_service.py`, a new
  route module, and possibly `PHASE_ARTIFACTS` (if archived/versioned files need different globs).
- **External integration contract (the immovable constraint):** downstream agents
  (`cast-high-level-planner`, `cast-task-suggester`, `cast-detailed-plan`, `cast-spec-checker`) all
  read `refined_requirements.collab.md` as **spec-kit markdown** (grep confirmed these files
  reference `refined_requirements`). Whatever becomes canonical, this file must keep appearing,
  structurally valid, at `goals/<slug>/refined_requirements.collab.md`.

---

## Architecture options, grounded in what exists

### Option A — Requirements as DB entities, HTML+markdown both generated (mirrors tasks)

**What it reuses:** the entire render-after-mutate loop is already written for tasks
(`_rerender_tasks_md`); the "Read-only render of DB state" convention; the `db_path`-injectable
service pattern; the structural spec-checker as a regression gate.

**What it costs (named, concrete):**
1. **New schema** — at minimum a `spec_elements` table keyed `(goal_slug, version, element_id,
   kind∈{US,FR,SC,scenario}, ordinal, body, …)`. Net-new; no columns to migrate.
2. **Rewrite `cast-refine-requirements`** to emit structured elements (rows or ingestable JSON)
   instead of hand-writing the file (`cast-refine-requirements.md:305` is the line that changes).
3. **Two renderers** — `_rerender_requirements_md` (spec-kit, must pass `bin/cast-spec-checker`)
   and an HTML renderer (Step 5). Both modeled on `_rerender_tasks_md`.
4. **Change the edit model** — requirements move from "edit the file in a textarea"
   (`api_artifacts.py`) to "edit rows, regenerate file." The current editable-file UX
   (`validate_artifact_path:44`) is repurposed or removed.

**Payoff:** FR-008 stable IDs become *real* (allocated + persisted per element), so comments
(US4), diffs/change-summaries (FR-017), archival (US5), and round-trip provenance (US7) all become
**rows keyed to durable IDs** instead of fragile text-anchor matching. This is the Multi-Lens
"stable identity is the keystone" insight, satisfied structurally.

### Option B — Files stay canonical, thin DB layer only for comments/versions

**What it reuses:** today's authoring + editing path largely unchanged; smaller diff.

**What it costs / risks:** comments still need to anchor to *something stable in a file*. Markdown
headings/line numbers are not stable across edits, so you **end up inventing an element-ID scheme
anyway** (e.g., injected `<a id=…>`/HTML comment sentinels or a sidecar `elements.json`) — i.e.,
Option B does not actually escape gap #1, it just implements identity in files instead of rows,
where it's harder to query and easier to corrupt on whole-file overwrite (`api_artifacts.py:94`).
Versioning/archival become folder/file conventions the filesystem-scan discovery
(`pages.py:113-125`) must learn.

### Stable-ID scheme (FR-008) — what the code implies

- **Tasks** prove integer-autoincrement PKs survive renders fine (`schema.sql:17`), but requirement
  IDs are *human-meaningful* (`FR-001`) and appear in the spec-kit output, so they can't be raw
  autoincrement. Recommended direction (for the synthesizer to confirm): a **stable surrogate**
  (e.g., ULID/short slug per element, persisted) that is *decoupled* from the *display* label
  (`FR-001`), so reordering/renumbering for humans never breaks comment anchors. The display label
  is a render-time projection of `(kind, ordinal)`; the durable anchor is the surrogate.
- **Why decouple:** the spec-checker dedups `FR-NNN` text (`cast-spec-checker.md:43-44`) but
  doesn't guarantee an `FR-001` is the *same requirement* across versions. Only a persisted
  surrogate gives that guarantee — the property comments/diffs/round-trip all depend on.

### Archive mechanism (US5) — what the code implies

- The house style says **DB for structured truth, files for current projection.** That argues for
  **archived versions living as DB rows** (`spec_elements` rows tagged with `version`/`archived`),
  with only the *current* version's file projection in the goal folder (satisfies FR-011 "only
  current version in main folder"). Comments + resolution state then travel automatically because
  they're rows keyed to element surrogates — no file-copy bookkeeping (the US5 Scenario 3
  requirement).
- An archive *folder* of old `.md` files is the Option-B-flavored alternative but reintroduces the
  text-anchor fragility for "retrieve old version *with its comments*."

---

## Key Takeaways

1. **The biggest architectural fact: Option A is a *pattern this codebase already runs*, not a
   leap.** `_rerender_tasks_md` (`task_service.py:389`) + `_write_goal_yaml` (`goal_service.py:337`)
   are working "DB-canonical → read-only file render" implementations. Requirements were simply
   never modeled as entities — they're the lone files-canonical, agent-authored holdout. The
   synthesizer should weigh Option A's cost as "extend a proven pattern to a new entity," not
   "invent a new architecture."

2. **The most expensive thing to get wrong is element identity, and it does not exist today
   (gap #1).** `FR-001`/`US1`/`SC-001` are text the agent types, with no persistence guarantee.
   Every dependent feature (comments US4, diffs FR-017, archival US5, round-trip US7) is a consumer
   of stable identity. **Both options must build it; Option A builds it where it's naturally
   queryable (rows), Option B builds it in files where overwrite-on-save actively threatens it.**

3. **FR-007 is cheaper to honor than it looks — it's a structural contract with a ready-made test
   harness.** `bin/cast-spec-checker` + `tests/test_us7_spec_kit_shape.py` parse structure/regex,
   not bytes (`cast-spec-checker.md:35-48`). A DB→markdown renderer just has to be structurally
   faithful. The regression check is concrete: render → run checker → run downstream agent chain.

4. **What would break under Option A:** the *editable-file* UX. Requirements are editable in the UI
   today (`validate_artifact_path:44`, textarea overwrite `api_artifacts.py:94`); under
   DB-canonical they become a read-only render and edits must go through rows. That's a real UX
   change to design for, not a free win — and it interacts with US7's round-trip write-back, which
   *also* can't survive whole-file last-write-wins overwrite as it stands.

5. **What's surprisingly good and should be preserved:** the build-free server-rendered stack
   (FastAPI + Jinja + HTMX, no npm — `base.html`, no `package.json`), the uniform render-after-mutate
   convention, and the `/preso/review/<slug>` precedent (`pages.py:299`) proving rich generated HTML
   can be served from the goal folder cheaply. None of these force a framework migration; an
   HTML-first requirements render fits the existing stack. (This is strong prior evidence for
   Step 4's "React not required" hypothesis, though Step 4 owns that verdict.)

6. **Greenfield is greenfield:** versioning, archival, comments, and diffing have zero existing
   code (gap #3/#4). This is freedom, not debt — design them once, correctly, keyed to element
   surrogates, rather than retrofitting around legacy structures. There are none.

7. **Migration path is incremental either way.** Because the spec-checker is structural and the
   render-after-mutate loop already exists, Option A can land behind the unchanged
   `refined_requirements.collab.md` file contract: introduce the element table + renderers, point
   `cast-refine-requirements` at them, keep emitting the same file. Downstream agents never notice.

## Key Files

- `cast-server/cast_server/services/task_service.py:389` — `_rerender_tasks_md`: **the Option A
  template** (DB-canonical entity → read-only markdown render after every mutation).
- `cast-server/cast_server/services/goal_service.py:337` — `_write_goal_yaml`: DB→file render
  convention + "Read-only render of DB state" stamp.
- `cast-server/cast_server/db/schema.sql` — full schema; shows tasks are entities, requirements are
  not (no element table).
- `cast-server/cast_server/models/task_v2.py:42` — the rich `Task` entity (where structured-entity
  investment went; the model a `Requirement` entity would mirror).
- `cast-server/cast_server/models/goal.py` — goal = metadata only (`folder_path`, no content).
- `cast-server/cast_server/routes/api_artifacts.py:20,94,132` — path validation, whole-file
  overwrite save, generic markdown→HTML render (today's files-canonical viewing/editing path).
- `cast-server/cast_server/routes/pages.py:113,299` — filesystem-scan artifact discovery; rich
  generated-HTML-from-disk precedent.
- `cast-server/cast_server/services/context_map.py:87` — `ensure_context_map`: a file→file derived
  render (TOC), another projection-generation precedent.
- `templates/cast-spec.template.md` — the spec-kit contract shape requirements must keep emitting
  (FR-007).
- `agents/cast-spec-checker/cast-spec-checker.md:31,35-48` — structural (not byte-exact) enforcement
  of the contract; the FR-007/SC-004 regression gate; `tests/test_us7_spec_kit_shape.py` exercises
  it.
- `agents/cast-refine-requirements/cast-refine-requirements.md:305` — where the requirements file is
  hand-authored today (the line Option A rewrites).
- `cast-server/cast_server/config.py:53-76` — `PHASE_ARTIFACTS` globs + authorship defaults
  (discovery + ownership config a new store touches).
- `cast-server/cast_server/static/` + `templates/base.html:13,153` — the build-free HTMX+EasyMDE
  frontend (no npm/React); context for the "no framework migration needed" thread.
