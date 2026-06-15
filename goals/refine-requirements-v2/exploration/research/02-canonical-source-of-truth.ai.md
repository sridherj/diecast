# Step 2 Research — Canonical Source of Truth for Requirements (PRIMARY)

> **Exploration step:** Step 2 of `exploration/steps.ai.md` — *Where does truth live, and how do
> requirement elements keep a durable identity across edits, renders, and versions?*
> **Resolves open questions:** canonical store (DB-entities-with-renders vs files-canonical-with-thin-DB),
> stable-ID scheme (FR-008), archive mechanism (US5), spec-kit markdown contract preservation (FR-007).
> **Author:** cast-web-researcher | **Date:** 2026-06-11
> **Audience:** the playbook synthesizer + owner sign-off at plan review. This is a *decision-ready* brief.

---

## TL;DR — Recommendation

**Adopt the DB-canonical pattern Diecast already runs for goals/tasks, extended to a `requirements`
element store, with markdown + HTML as auto-generated read-only renders.** Concretely:

1. **Canonical store = SQLite rows**, one row per requirement *element* (US / FR / SC / scenario),
   not one blob per document. Mirrors the working `goals`/`tasks` precedent
   (`cast-server/cast_server/db/schema.sql:1`, `goal_service.py:337`, `task_service.py:389`).
2. **Renders are generated artifacts, never edited.** `refined_requirements.collab.md` (spec-kit
   markdown, for agents) and the new HTML (for humans) are both emitted from the rows, carrying the
   existing `<!-- AUTO-GENERATED: Read-only render of DB state -->` header convention
   (`task_service.py:428`). This keeps FR-007 a *render target*, not a parse-and-mutate surface.
3. **Stable IDs are surrogate, allocate-once, never-renumbered** — decoupled from the displayed
   `FR-001` ordinal. The display ordinal is a render-time projection; the durable anchor is an
   internal element key (e.g. `req_<goal>_<type>_<counter>` or a UUIDv4). This is the keystone the
   whole goal hangs on (steps.ai.md "Multi-Lens Insights").
4. **Archive = DB rows, not a folder.** A `requirement_versions` (or `is_current` + version columns)
   model keeps superseded versions queryable with their comments/resolution state attached via FK —
   satisfying US5 Scenario 3 ("retrieve older version *with its comments and resolution state
   intact*") for free, which a folder of frozen `.md` files cannot do.

**Why this wins:** every downstream feature in the goal (comments → Step 4, version diff/change
summary → Step 4, archival → US5, round-trip write-back → Step 7) is a *consumer of stable element
identity*. Files-canonical forces all of them onto fragile text-anchor matching; DB-canonical makes
them plain foreign keys. The architecture decision is really an *identity* decision, and DB rows are
where identity lives natively.

**The one real risk to retire:** byte-stability of the generated markdown against the existing
spec-checker contract. Mitigation is a golden-file regression test (see §FR-007 below). This is
cheap and decisive — it is the gate for sign-off.

---

## The decision framed precisely

Two architectures are on the table (refined_requirements.collab.md → Directional Ideas / Open
Questions):

- **Option A — DB-canonical + generated renders.** Requirement elements are DB rows. HTML (human)
  and spec-kit markdown (agents) are auto-generated, read-only. Comments/versions are native rows.
- **Option B — files-canonical + thin DB layer.** `refined_requirements.collab.md` stays the
  authoritative artifact (human/agent edits it directly); a DB sidecar stores only comments and
  version pointers, anchored back into the file.

There is also a latent **Option C — hybrid / "structured-sidecar"**: the markdown file stays
human-editable, but a parser maintains a shadow element table for IDs/comments, reconciling on every
edit. This is the worst of both (see Contrarian, below) and is called out only to be dismissed.

The rest of this note researches the decision from seven expert angles, then lands a trade-off matrix
and the concrete migration path.

---

## Angle 1 — Expert Practitioner (requirements engineering)

The requirements-engineering discipline has a settled, decades-old answer to the identity question,
and it is unambiguous: **requirement IDs must be stable surrogate keys that never change on reorder,
are never reused, and are never deleted.** Perforce/Stell/Six-Sigma RTM guidance all state the same
rule — "IDs should not change if your requirements are reordered nor should they be reused or
deleted" ([Stell][stell], [Perforce][perforce]). Pro tools (IBM DOORS, RequisitePro, Caliber) are
built around exactly this: a requirement is a *record* with a persistent identity, and the document
view is a projection over those records ([Wikipedia: Requirements traceability][rt-wiki]).

This is the single most load-bearing finding for Step 2. The owner's spec already uses `FR-001`,
`SC-001` as "stable identifiers" (`cast-spec-checker` enforces `FR-(\d{3,})` /`SC-(\d{3,})` —
`bin/cast-spec-checker:41`), **but today those ordinals are positional, not durable**: the
cast-refine-requirements agent emits them sequentially when rendering the markdown
(`agents/cast-refine-requirements/cast-refine-requirements.md:267`, `:354`). Insert a requirement
between FR-002 and FR-003 and a naive renumber shifts every downstream anchor — the exact failure
the discipline warns against. **Whatever store we pick, the display ordinal must be divorced from the
durable anchor.** DB rows make this natural (surrogate PK ≠ render ordinal). A flat markdown file
makes it a manual discipline the agent must never violate — a far weaker guarantee.

**Practitioner verdict:** identity is the requirement, not the file. A store that gives each element a
first-class durable key (Option A) is how the mature tools in this space are built. Files-canonical
(Option B) can *emulate* this only by treating the `FR-NNN` token in the text as the key and praying
nobody renumbers — fragile by construction.

## Angle 2 — Tools & Technologies (what the stack already gives us)

Diecast is **FastAPI + Jinja over SQLite**, and it *already implements Option A for two entity
families*. This is decisive prior art sitting in the repo:

- **DB is canonical; files are read-only renders.** `goals` and `tasks` are SQLite tables
  (`db/schema.sql:1`, `:16`). Every mutation writes the DB first, then re-renders the file:
  `goal_service.update_phase` updates the row then calls `_update_goal_yaml_fields`
  (`goal_service.py:151-178`); `_rerender_tasks_md` rebuilds `tasks.md` wholesale from rows
  (`task_service.py:389`). The generated files carry an explicit contract header:
  `"# AUTO-GENERATED: Read-only render of DB state. Do not edit directly."` (`goal_service.py:359`,
  `task_service.py:428`). **The "DB-canonical, generated file renders" pattern is not hypothetical —
  it is the house style.**
- **Storage is hand-rolled SQL, not an ORM.** Models are Pydantic DTOs (`models/goal.py:7`,
  `models/task.py:10`); persistence is `conn.execute(...)` through `db/connection.get_connection`
  (`goal_service.py:84`). A new `requirements` table + a `requirement_service.py` slots straight into
  this with zero new infrastructure.
- **HTML rendering already exists.** `routes/pages.py` serves Jinja pages
  (`templates/pages/goal_detail.html`, `dashboard.html`, and a `plan_and_progress/` page tree). The
  HTML-first render the goal wants (US3) is the *same* route→template→entity path already used for
  goal detail — no new framework required.
- **Stable string PKs are already in use.** `goals.slug` is a TEXT primary key
  (`db/schema.sql:2`), `agent_runs.id` is a TEXT run-id PK (`db/schema.sql:74`). A
  `requirements.element_id TEXT PRIMARY KEY` is idiomatic here.

The relevant external corroboration: when content is edited and round-tripped, the standard hybrid is
**keep canonical structured data in one place and treat HTML/markdown as a regenerated cache**
([Quora/Markdown-vs-HTML storage][quora]; MarkdownDB indexes markdown into a queryable DB without
making the DB authoritative — the inverse of what we want, but it confirms the "structured layer over
text" tooling exists [MarkdownDB][markdowndb]).

**Tools verdict:** Option A reuses an already-proven path in this exact codebase (SQLite rows →
`# AUTO-GENERATED` render). Option B would require *inventing* a markdown parser that round-trips
edits without corrupting the structure — net-new, fragile tooling the repo does not have.

## Angle 3 — AI / ML Approaches (agents as first-class producers AND consumers — FR-013)

The spec demands agents read *and* write requirements through the same door as humans (FR-013,
US7). This sharpens the store choice more than any human-UX consideration:

- **Agent writes are structured mutations, not text patches.** A downstream planning agent that
  discovers a new constraint (US7 Scenario 1) wants to *append a requirement element* with
  provenance — i.e. `INSERT INTO requirements (...) VALUES (...)` with `origin_phase='planning'`.
  Against Option A that is a one-line, race-safe, atomic operation that auto-allocates a stable ID
  and re-renders both files. Against Option B the agent must locate the FR table in markdown, parse
  it, append a row, renumber-or-not, and rewrite the file — an LLM doing fragile text surgery on the
  source of truth, with no transactional guarantee and high diff-noise.
- **Comments/versions as an API.** FR-013 wants the comment/version mechanism callable by an agent
  identically to the GUI. A DB-backed `POST /api/requirements/{element_id}/comments` is trivially
  agent-callable (the codebase already exposes agent-facing routes — `routes/api_agents.py`,
  `api_tasks.py`). A file-anchored comment requires the agent to compute and persist a text offset
  or selector — see Angle 6.
- **Retrieval / diffing for change summaries (FR-017).** A stable-ID element table makes the
  version change-summary a structured `diff` over rows keyed by `element_id` — deterministic, no
  fuzzy matching. Diffing two markdown blobs to *infer* which FR changed is exactly the
  text-alignment problem stable IDs exist to avoid.

Note the document-processing world independently arrived at "give every element a deterministic/UUID
id so it can be a DB primary key" — Unstructured hashes element text+position into stable IDs, and
offers `unique_element_ids=True` to mint UUIDs precisely so elements can key a database
([Unstructured: document elements][unstructured]). Same instinct, same reason.

**AI verdict:** an AI-native future makes Option A *more* compelling, not less. Agents are better at
emitting structured mutations against an API than at safely editing the canonical markdown in place.
Option B optimizes for a human-with-a-text-editor mental model the spec explicitly says to move past.

## Angle 4 — Community & Open Source (precedents for "block has an ID")

The block/element-with-stable-ID model is the dominant architecture in modern document tools:

- **Notion** — *everything is a block, every block has a UUIDv4*, stored as rows in Postgres; the
  rendered page is a tree-walk over block rows (`loadPageChunk`). Notion deliberately separates the
  content-ordering pointer from the block identity so reorder ≠ re-identify
  ([Notion: data model][notion]). This is precisely the "display ordinal ≠ durable key" split we
  need for FR-008.
- **ProseMirror / collaborative editors** — anchored comments are implemented as *marks with a
  stable `id` attribute persisted in the document model*, not as external text offsets
  ([ProseMirror highlights & comments][prosemirror]). The lesson: even rich-text editors that *could*
  use positions choose to anchor comments to stable element identities because positions don't
  survive edits.
- **Hypothes.is** — the cautionary tale for the *files-canonical* path. Because it annotates
  arbitrary web pages with **no stable IDs**, it needs "fuzzy anchoring": three selectors and four
  re-attachment strategies, and annotations still orphan when documents change
  ([Hypothesis: fuzzy anchoring][hypothesis]). That entire engineering edifice exists *only because
  there are no stable element IDs*. Option B re-signs us up for this problem; Option A deletes it.
- **GitHub spec-kit** (the lineage of our spec-kit markdown contract) keeps each phase as a markdown
  artifact (Spec → Plan → Tasks → Implement) ([spec-kit][speckit]). Important nuance: spec-kit treats
  markdown as the *interchange* format between phases — which is exactly the role FR-007 assigns to
  our generated markdown render. Spec-kit does **not** mandate that markdown be the *mutable canonical
  store*; it is the contract surface. Generating that surface from rows is fully compatible.

**Community verdict:** the entire category — Notion, ProseMirror, Outline, requirements tools — has
converged on "structured store of identified elements; document is a render." Hypothes.is is the
living proof of what files-canonical costs you. The OSS-generalization constraint (FR-012) is *better*
served by Option A: a DB schema is a cleaner public contract than "parse my markdown dialect."

## Angle 5 — Frameworks & Patterns (versioning + archive — US5)

The archive question (US5) and the version-progression engine (Step 4) are storage-pattern questions,
and the patterns literature points the same way:

- **Versions as rows, append-only.** The event-sourcing / append-only-audit literature establishes
  the durable shape: keep a stable entity key + a monotonic version number, write new versions
  without mutating old rows, and project "current" as a view ([Azure: Event Sourcing][azure-es];
  [DesignGurus: append-only audit][designgurus]). We do **not** need full event sourcing — that is
  overkill — but the *append-only versioned-rows* sub-pattern is exactly US5: produce v_n+1, mark
  v_n superseded, never lose v_n.
- **Concrete schema choice.** Two viable shapes:
  - *(a) `is_current` flag + `version` column on a single `requirements` table* — simplest; current
    spec = `WHERE goal_slug=? AND is_current=1`.
  - *(b) separate `requirement_versions` snapshot table* keyed by `(goal_slug, version)` with the
    live `requirements` table holding only current — cleaner archival, easy "give me v2 whole."
  Recommend **(b)** because US5 Scenario 1 ("retain exactly one current version in the main folder")
  maps to "only current renders to a file" and Scenario 3 ("retrieve older version *with comments and
  resolution intact*") maps to "comments FK to the versioned element rows." Folder-of-frozen-md
  (the alternative in the open question) **cannot** satisfy Scenario 3 without *also* freezing a
  comment sidecar per version and re-anchoring it — i.e. you rebuild the DB anyway, badly.
- **Comments travel with versions automatically.** If comments are rows with
  `FK(element_id, version)`, archiving a version is a no-op for comment retention — they're already
  attached. This is the structural reason US5's "DB" lean (stated in the open question) is correct.

**Patterns verdict:** archive = DB rows (Option A, schema (b)). The archive-folder alternative loses
the comment/resolution-state coupling that US5 Scenario 3 explicitly requires, and reintroduces the
"two sources that can disagree" problem.

## Angle 6 — Contrarian View (steelman files-canonical, then refute)

The honest steelman for **Option B (files-canonical)**:

- Markdown files are git-diffable, greppable, portable, and survive the death of cast-server. The
  whole Diecast goal-dir ethos is "files in a folder." Forcing requirements into SQLite makes them
  invisible to `git log` and couples them to a running server.
- The repo *already* has a precedent for files-as-truth: the human-authored `requirements.human.md`
  and `research_notes.human.md` are real files the agent reads (`cast-refine-requirements.md:90`).
- A migration to DB-canonical is genuinely more code than "keep writing the file."

**Why it loses anyway:**

1. **The git argument is weaker than it looks.** Today's `refined_requirements.collab.md` is *already
   a `.collab.md`* — an agent-managed artifact, not a hand-edited file. And the generated renders
   stay in the goal folder (the spec wants exactly that — US5 Scenario 1 keeps the current version in
   the folder), so `git log` on the rendered markdown still works. We keep git-visibility of the
   render *and* gain structured identity. Diecast's goals/tasks already prove you can have both: the
   DB is canonical yet `goal.yaml`/`tasks.md` sit in the folder, committed, diffable.
2. **Option C (hybrid shadow-parser) is a trap.** "Keep the file editable, maintain a shadow element
   table by parsing on save" sounds like the best of both, but it is the worst: now you have two
   sources that drift, a markdown-dialect parser to maintain, and the fuzzy-anchoring problem returns
   the moment a human edits text that a comment was anchored to. This is the Hypothes.is failure mode
   (Angle 4) self-inflicted. Reject Option C explicitly.
3. **Files-canonical caps every dependent feature.** Comments, diffs, change summaries, round-trip
   provenance — all become text-anchoring problems (Angle 1, 4). The contrarian insight in the
   spec's own Multi-Lens notes is the sharper one: *the framework-migration fear is the false
   premise, not the DB-canonical move.* You do NOT need React to get Google-Docs comments — you need
   stable element IDs and server-rendered anchored DOM nodes (steps.ai.md "Multi-Lens Insights";
   confirmed by ProseMirror/Notion using id-attributed nodes). Option A delivers those IDs; Option B
   withholds them.

**Contrarian verdict:** the strongest pro-file argument (git/portability) is preserved by Option A's
*generated* renders, so it is not actually a trade-off. The hybrid (C) is a trap. Files-canonical's
real cost is that it makes every Step-4/5/7 feature fragile.

## Angle 7 — First Principles (reduce to the irreducible primitive)

Strip the goal to its atoms. Steps 4 (comments, diffs, versions), US5 (archive with comments), and 7
(round-trip provenance) **all reduce to one primitive: a requirement element that has a durable
identity independent of its text and its position.** Everything else is a consumer of that primitive
(this is literally the spec's stated keystone — steps.ai.md Multi-Lens insight #1).

From first principles, then, the architecture question is mis-stated as "DB vs files." The real
question is: *where does durable element identity live most naturally?*

- A **row** has identity by construction (its primary key). Identity is free and unbreakable.
- A **span of text in a file** has identity only by convention (a token like `FR-003` you promise not
  to renumber, or a byte-offset that any edit invalidates). Identity is expensive and fragile.

Therefore the store that makes identity *intrinsic* (rows) is the correct canonical store, and text
(markdown/HTML) is correctly a *projection* of identified elements. The markdown contract (FR-007) is
then trivially preserved because rendering is a pure function `rows → markdown` that we control and
can pin with a golden test. Files-canonical inverts this: it makes the fragile thing canonical and
forces the durable thing (identity) to be reconstructed on every read.

**First-principles verdict:** Option A. The canonical store should be whatever makes element identity
intrinsic; that is rows, not text spans.

---

## FR-007 — Preserving the spec-kit markdown contract (the gate for sign-off)

This is the one place Option A carries real risk, so it gets its own treatment. Downstream consumers
read `refined_requirements.collab.md` in spec-kit shape and must keep working unchanged (FR-007,
SC-004). The concrete contract surface is `bin/cast-spec-checker`, which parses the markdown with
regexes:

- `US_HEADING_RE = ^###\s+(US\S+)\s*[—-]\s*(.+)$` (`bin/cast-spec-checker:32`)
- `FR_ID_RE = \bFR-(\d{3,})\b`, `SC_ID_RE = \bSC-(\d{3,})\b` (`:41`,`:42`)
- `EARS_SCENARIO_RE = WHEN ... THE SYSTEM SHALL` (`:37`)
- `PRIORITY_RE`, `INDEPENDENT_TEST_RE`, `ACCEPTANCE_SCENARIO_HEADER_RE`, `NEEDS_CLAR_INLINE_RE`,
  `SECTION_HEADING_RE` (`:31`–`:43`)

And the render template is `templates/cast-spec.template.md`, which the refine agent emits against
(`cast-refine-requirements.md:259`, `:305`). Consumers: planner, task-suggester, spec-checker,
goal-decomposer, code-explorer, detailed-plan, high-level-planner (grep of `agents/` for
`refined_requirements`).

**The requirement on Option A:** the `rows → markdown` renderer must produce output that
(a) re-emits the displayed `FR-NNN`/`SC-NNN` ordinals in the same `\d{3,}` shape the checker expects,
(b) preserves the `### US… —`, EARS, Priority, and section-heading structure, and (c) is
byte-compatible enough that the existing agent chain runs green.

**Mitigation (cheap, decisive):**
1. **Golden-file regression test.** Snapshot a current real `refined_requirements.collab.md` (this
   goal's own file is a perfect fixture), feed its elements through the new renderer, and assert the
   output passes `bin/cast-spec-checker` *and* diffs clean against the snapshot (modulo the
   `# AUTO-GENERATED` header). This is SC-004 turned into a CI gate. Define it as the acceptance
   check for the migration.
2. **Display ordinal = stable render projection.** Render `FR-001, FR-002, …` in element sort order;
   the *durable* key (`element_id`) lives in an HTML `id`/`data-element-id` attribute and an optional
   markdown HTML-comment anchor (`<!-- el:req_… -->`) that the checker's regexes ignore. The checker
   only cares about the visible `FR-\d{3,}` token, so we are free to keep a separate durable key.
3. **Renumber-safe policy.** Because the durable key ≠ the ordinal, we *may* re-emit clean
   sequential ordinals on every render without breaking comment anchors (comments key on
   `element_id`, not ordinal). This actually makes the markdown *cleaner* than today while staying
   safe — a strict improvement.

**Conclusion:** FR-007 is preserved as a *render target*. The risk is bounded and retired by one
golden test. This is the item to put in front of the owner for explicit sign-off.

---

## FR-008 — Stable-ID scheme (design)

| Property | Design |
|---|---|
| **Durable key** | `element_id` — surrogate, allocate-once, never reused, never renumbered. Form: `req_<goal_slug>_<type>_<zeropad_counter>` (human-debuggable) **or** UUIDv4 (Notion-style, collision-free for agent writes). Recommend the prefixed-counter form for greppability, matching the repo's `run_…`/slug conventions. |
| **Display ordinal** | `FR-NNN`/`SC-NNN`/`US-N` rendered from element sort order at render time. A *projection*, not the identity. May be recomputed freely. |
| **Allocation** | Monotonic per (goal, element_type) counter stored in the DB; `INSERT` auto-allocates. Agent and human writes go through the same allocator (FR-013). |
| **Persistence across edits** | Editing an element's *text* never changes its `element_id`. Deleting is a soft-delete (`status='removed'`/`archived`), so IDs are never reused (per requirements-engineering rule — Angle 1). |
| **Use as comment anchor** | Comments (Step 4) carry `FK(element_id)` — and, for versioned views, `FK(element_id, version)`. No text offsets, no fuzzy anchoring. |
| **Use as cross-reference target** | Cross-refs (e.g. FR-009 "enables US4") store `element_id` targets; the render resolves them to current display ordinals. References never break on renumber. |
| **HTML anchor** | Each rendered element gets `id="req_…"` / `data-element-id="req_…"` so the human render's DOM nodes are the comment anchor points (the server-rendered-anchored-DOM approach that kills the React-migration premise — Step 4). |

This scheme is the literal embodiment of the cross-industry rule (Angle 1) and the Notion/ProseMirror
pattern (Angle 4): **identity is a surrogate key; the visible number is cosmetic.**

---

## US5 — Archive mechanism (design)

**Decision: DB rows, not an archive folder.** Recommended schema shape (b) from Angle 5:

- `requirements` — current elements only (`is_current` implicit by presence). Renders to the single
  in-folder current version (US5 Scenario 1).
- `requirement_versions` — append-only snapshots keyed `(goal_slug, version)`; superseding v_n writes
  v_{n+1} and marks v_n archived without deleting (US5 Scenario 2, append-only pattern — Angle 5).
- `comments` — `FK(element_id, version)`, so retrieving an old version returns its comments and
  open/resolved state intact (US5 Scenario 3) with zero extra work.
- Optional: render archived versions to an `archive/` subfolder *as read-only generated artifacts*
  for git-visibility, but the DB remains canonical. This gives the contrarian (Angle 6) their
  git-diffable history *and* the structured retrieval US5 Scenario 3 needs.

A pure archive-folder approach (the alternative in the open question) is rejected: it cannot retain
comment + resolution state coupled to the archived version without a parallel sidecar, which is just a
worse DB.

---

## Trade-off matrix

| Dimension | **A: DB-canonical + renders** (recommended) | **B: files-canonical + thin DB** | **C: hybrid shadow-parser** (rejected) |
|---|---|---|---|
| Element identity (FR-008) | ✅ intrinsic (row PK) | ⚠️ by convention (FR-NNN token); breaks on renumber | ⚠️ reconstructed by parser; drifts |
| Comment anchoring (Step 4) | ✅ FK to element_id | ❌ text offsets / fuzzy anchoring (Hypothes.is problem) | ❌ re-anchors on every human edit |
| Version diff / change summary (FR-017) | ✅ structured row diff, deterministic | ❌ markdown-blob diff, infer-which-FR | ⚠️ depends on parser fidelity |
| Archive with comments (US5 S3) | ✅ FK(element_id, version), free | ❌ needs frozen sidecar per version | ❌ same |
| Agent-writability (FR-013) | ✅ atomic INSERT via API | ❌ LLM text-surgery on canonical file | ❌ same + reconcile |
| Round-trip write-back (Step 7) | ✅ INSERT with provenance cols | ⚠️ append-to-file, parse to attribute | ⚠️ same |
| Downstream md contract (FR-007) | ⚠️ must render byte-stable (golden test) | ✅ file *is* the contract | ⚠️ file editable but parser may reshape |
| Git-diffability / portability | ✅ via generated in-folder renders | ✅ native | ✅ native |
| Implementation cost | ⚠️ new table + service + renderer | ✅ lowest (keep writing file) | ❌ highest (parser + reconcile + DB) |
| Reuses existing Diecast pattern | ✅ exactly mirrors goals/tasks | ❌ no precedent for "file canonical + DB sidecar" | ❌ none |
| **Net** | **Best ceiling; one bounded risk (FR-007)** | Lowest cost, lowest ceiling; fragile for Steps 4/5/7 | Worst of both; reject |

The only column where A is not the winner is implementation cost / FR-007 — and FR-007 is retired by
a golden test, while the cost is *reduced* by reusing the existing goals/tasks machinery rather than
inventing new infrastructure.

---

## Concrete migration path (decision-ready, what changes in the codebase)

1. **Schema** (`cast-server/cast_server/db/schema.sql`): add `requirements` (element rows with
   `element_id` PK, `goal_slug` FK, `element_type` US/FR/SC/scenario, `display_order`, `body`,
   `priority`, `parent_element_id`, `status`, `origin_phase`, `version`, `created_at`, `updated_at`),
   `requirement_versions` (snapshot table), and `requirement_comments`
   (`element_id`+`version` FK, `body`, `state` open/resolved, `resolution_trail`, `author`,
   `created_at`). Plus an alembic migration (`cast-server/alembic/versions/`).
2. **Service** (`requirement_service.py`, mirroring `goal_service.py`/`task_service.py`): CRUD +
   `_rerender_requirements_md()` (emits spec-kit markdown against `templates/cast-spec.template.md`
   with the `# AUTO-GENERATED` header) + `_rerender_requirements_html()` (Jinja). Same write-DB-then-
   render flow as `_rerender_tasks_md` (`task_service.py:389`).
3. **Renderer = pure `rows → markdown`** producing `refined_requirements.collab.md` byte-compatibly;
   gated by the golden-file test against `bin/cast-spec-checker` (FR-007/SC-004).
4. **cast-refine-requirements agent** shifts from *writing the markdown file* to *writing element rows
   via the service API*; the file becomes a generated artifact (matching how /cast-goals and
   /cast-tasks already work — they mutate DB, not the file).
5. **HTML route** (`routes/pages.py` + a `templates/pages/requirements_detail.html`) for US3, reusing
   the existing goal-detail render path.
6. **Backfill**: a one-shot importer parses existing `refined_requirements.collab.md` files into
   element rows (so current goals migrate cleanly).

This is additive — it does not touch downstream agents (they keep reading the generated markdown,
SC-004), satisfying the "downstream contract preserved" constraint.

---

## Open items to flag for plan review (owner sign-off)

1. **FR-007 golden test** — confirm the byte-stability acceptance gate is sufficient assurance, or
   whether the owner wants the full downstream agent chain run green on a migrated goal before
   committing (SC-004 as written).
2. **element_id form** — prefixed-counter (`req_<goal>_FR_007`, greppable) vs UUIDv4 (Notion-style,
   agent-write-safe). Recommend prefixed-counter; flag for preference.
3. **Archive rendering** — DB-canonical is decided; confirm whether superseded versions should *also*
   render to an in-repo `archive/` folder for git-visibility (recommended) or live DB-only.
4. **Scope coupling** — Steps 4 (comments/versions), 5 (HTML render), 7 (round-trip) all consume this
   schema. This note fixes the element/version/comment table shapes they depend on; those steps
   should treat the schema here as the contract.

---

## Sources

**Codebase (primary evidence):**
- `cast-server/cast_server/db/schema.sql:1` (goals), `:16` (tasks), `:73` (agent_runs) — SQLite canonical store
- `cast-server/cast_server/services/goal_service.py:337,359,366` — DB-canonical, `# AUTO-GENERATED` read-only render
- `cast-server/cast_server/services/task_service.py:389,428,458` — `_rerender_tasks_md` rows→markdown render
- `cast-server/cast_server/models/goal.py:7`, `models/task.py:10` — Pydantic DTOs over hand-rolled SQL
- `bin/cast-spec-checker:31-43` — downstream markdown contract (FR/SC/US/EARS regexes)
- `templates/cast-spec.template.md`, `agents/cast-refine-requirements/cast-refine-requirements.md:259,267,305,354` — render template + current file-writing path
- `goals/refine-requirements-v2/exploration/steps.ai.md` (Multi-Lens Insights), `refined_requirements.collab.md` (FR-007/008, US5, Open Questions)

**Web (external corroboration):**
- [Stable requirement IDs never renumber/reuse — Stell Engineering RTM][stell]
- [Requirements traceability matrix best practices — Perforce][perforce]
- [Requirements traceability (DOORS/ReqIF lineage) — Wikipedia][rt-wiki]
- [Notion block model — every block has a UUID, document is a tree of rows][notion]
- [ProseMirror anchored comments as id-attributed marks][prosemirror]
- [Hypothes.is fuzzy anchoring — the cost of no stable IDs][hypothesis]
- [GitHub spec-kit — markdown as phase interchange contract][speckit]
- [Event Sourcing / append-only versioned rows — Azure Architecture Center][azure-es]
- [Append-only audit trail design — DesignGurus][designgurus]
- [Unstructured — deterministic/UUID element IDs as DB primary keys][unstructured]
- [Markdown vs HTML storage — keep canonical structured, regenerate render — Quora][quora]
- [MarkdownDB — structured queryable layer over markdown][markdowndb]

[stell]: https://stell-engineering.com/blog/requirements-traceability-matrix
[perforce]: https://www.perforce.com/blog/alm/how-create-traceability-matrix
[rt-wiki]: https://en.wikipedia.org/wiki/Requirements_traceability
[notion]: https://www.notion.com/blog/data-model-behind-notion
[prosemirror]: https://medium.com/collaborne-engineering/prosemirror-highlights-comments-20ce820149ed
[hypothesis]: https://web.hypothes.is/blog/fuzzy-anchoring/
[speckit]: https://github.com/github/spec-kit
[azure-es]: https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing
[designgurus]: https://www.designgurus.io/answers/detail/how-do-you-enforce-immutability-and-appendonly-audit-trails
[unstructured]: https://docs.unstructured.io/open-source/concepts/document-elements
[quora]: https://www.quora.com/Should-I-store-markdown-instead-of-HTML-into-database-fields
[markdowndb]: https://markdowndb.com/
