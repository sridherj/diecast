# Canonical Source of Truth for Requirements — Playbook

> **Step 2 (PRIMARY) of `exploration/steps.ai.md`** — the keystone architecture decision every
> other step consumes. Synthesized from `research/02-canonical-source-of-truth.ai.md` (web, 7 angles)
> + `research/02-canonical-source-of-truth-code.ai.md` (codebase terrain).
> **Author:** cast-playbook-synthesizer | **Date:** 2026-06-11 | **Audience:** plan-review + owner sign-off.

## TL;DR

**Make requirement *elements* (US/FR/SC/scenario) first-class SQLite rows; emit both the spec-kit
markdown and the human HTML as read-only, auto-generated renders — exactly the pattern `tasks.md`
already runs.** The architecture question ("DB vs files") is a misframe: the real question is *where
does durable element identity live*, and a row has identity for free (its primary key) while a span
of text in a file has identity only by a convention you must never violate. Every downstream feature
in this goal — comments (Step 4), version diffs (Step 4), archival (US5), round-trip provenance
(Step 7) — is a *consumer of stable element identity*; DB rows make them foreign keys, files-canonical
makes them fragile text-anchor matching (the Hypothes.is failure mode). The one real risk — keeping the
generated markdown valid against `bin/cast-spec-checker` — is retired by a single golden-file test.

## Recommended Stack

| Component | Choice | Why (and why not the alternative) |
|-----------|--------|-----------------------------------|
| Canonical store | **SQLite element rows** (`requirements` table, one row per US/FR/SC/scenario) | Mirrors the working `tasks`/`goals` precedent (`task_service._rerender_tasks_md`). Files-canonical caps every dependent feature; hybrid shadow-parser is the worst of both — reject. |
| Persistence layer | **Hand-rolled SQL via `db/connection.get_connection()`** | House style — no ORM anywhere (`goal_service.py`, `task_service.py`). An ORM would be net-new infra for zero gain. |
| Stable ID | **Surrogate `element_id` TEXT PK**, form `req_<goal>_<TYPE>_<counter>` (greppable, slug-style) | Decoupled from the display ordinal `FR-001`. Matches the repo's `run_…`/`slug` TEXT-PK convention. Not UUIDv4 — greppability beats agent-write collision-safety at this scale; counter is DB-allocated so no collisions anyway. |
| Display ordinal | **Render-time projection** (`FR-NNN` from sort order) | The visible number is cosmetic (the requirements-engineering rule: IDs never renumber/reuse). Comments key on `element_id`, never the ordinal, so re-emitting clean ordinals is *safe* and makes the markdown cleaner than today. |
| Versioning | **Append-only `requirement_versions` snapshot table**, keyed `(goal_slug, version)` | Event-sourcing's append-only sub-pattern (not full ES — overkill). Superseding writes v_{n+1}, marks v_n archived, never deletes. Folder-of-frozen-`.md` can't retain comment+resolution state (US5 S3). |
| Comments anchor | **`requirement_comments.element_id` FK** (+ `version`) | US5 S3 ("retrieve old version *with comments intact*") becomes free. Text-offset anchoring would re-import the fuzzy-anchoring engineering Hypothes.is needs only because it has no stable IDs. |
| Markdown render | **Pure `rows → markdown` fn** emitting `templates/cast-spec.template.md` shape | FR-007 is a *structural* contract (`bin/cast-spec-checker` parses sections + `FR-\d{3,}` regex, not bytes). Render just has to be structurally faithful + pass the checker. |
| HTML render | **Jinja template via existing `routes/pages.py` path** | US3's render is the same route→template→entity path as goal-detail. No npm, no React, no build step (confirmed: no `package.json` in repo). |
| Migration | **One-shot backfill importer** parsing existing `refined_requirements.collab.md` → rows | Existing goals migrate cleanly; this goal's own file is the golden fixture. |

## Implementation Steps

### Step 1: Add the schema (three tables + migration)
**Impact: High** | **Effort: 0.5 day**

Add to `cast-server/cast_server/db/schema.sql` and create an Alembic migration in
`cast-server/alembic/versions/`. Three tables — current elements, version snapshots, comments:

```sql
-- Current requirement elements (one row per US/FR/SC/scenario). The canonical store.
CREATE TABLE requirements (
    element_id        TEXT PRIMARY KEY,           -- req_<goal>_<TYPE>_<counter>, allocate-once, never reused
    goal_slug         TEXT NOT NULL REFERENCES goals(slug) ON DELETE CASCADE,
    element_type      TEXT NOT NULL,              -- 'US' | 'FR' | 'SC' | 'scenario'
    parent_element_id TEXT REFERENCES requirements(element_id),  -- scenario -> its US
    display_order     INTEGER NOT NULL,           -- projection source for FR-NNN ordinal
    body              TEXT NOT NULL,              -- the requirement text (markdown-safe)
    priority          TEXT,                       -- P1/P2 for user stories; NULL otherwise
    status            TEXT NOT NULL DEFAULT 'current',  -- 'current' | 'removed' (soft-delete; IDs never reused)
    origin_phase      TEXT NOT NULL DEFAULT 'requirements',  -- provenance for Step 7 write-back
    version           INTEGER NOT NULL DEFAULT 1, -- current live version number
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
);
CREATE INDEX idx_requirements_goal ON requirements(goal_slug, status, display_order);

-- Append-only snapshots of superseded versions. US5 archival.
CREATE TABLE requirement_versions (
    goal_slug    TEXT NOT NULL REFERENCES goals(slug) ON DELETE CASCADE,
    version      INTEGER NOT NULL,
    element_id   TEXT NOT NULL,                  -- snapshot of the element AS OF this version
    element_type TEXT NOT NULL,
    body         TEXT NOT NULL,
    display_order INTEGER NOT NULL,
    archived_at  TEXT NOT NULL,
    PRIMARY KEY (goal_slug, version, element_id)
);

-- Comments anchored to elements (+ version). US4 / FR-009/010. Agent-callable (FR-013).
CREATE TABLE requirement_comments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    element_id      TEXT NOT NULL,               -- the durable anchor (NOT a text offset)
    version         INTEGER NOT NULL,            -- the version the comment was left against
    goal_slug       TEXT NOT NULL REFERENCES goals(slug) ON DELETE CASCADE,
    body            TEXT NOT NULL,
    state           TEXT NOT NULL DEFAULT 'open',-- 'open' | 'resolved'
    resolution_trail TEXT,                       -- JSON: who/when/which version resolved it
    author          TEXT NOT NULL,               -- human handle OR agent name (FR-013 parity)
    created_at      TEXT NOT NULL
);
CREATE INDEX idx_comments_element ON requirement_comments(element_id, version);
```

`schema.sql` is the hand-maintained source of truth here (only one baseline Alembic migration exists —
`cfe1a46fdefc_baseline.py`); add the table DDL there *and* a forward migration so existing DBs upgrade.

### Step 2: Build `requirement_service.py` (mirror `task_service.py`)
**Impact: High** | **Effort: 1.5 days**

Copy the shape of `task_service.py` exactly — `db_path=`-injectable, raw SQL, render-after-mutate.
Core methods:

```python
class RequirementService:
    def __init__(self, db_path: str | None = None): ...

    def create_element(self, goal_slug, element_type, body, *, priority=None,
                       parent_element_id=None, origin_phase="requirements") -> Requirement:
        element_id = self._allocate_id(goal_slug, element_type)   # monotonic per (goal, type)
        # INSERT ... then:
        self._rerender(goal_slug)
        return ...

    def _allocate_id(self, goal_slug, element_type) -> str:
        # SELECT MAX(counter) WHERE goal_slug=? AND element_type=?  -> +1, zero-pad
        # form: f"req_{goal_slug}_{element_type}_{counter:03d}"
        ...

    def update_element(self, element_id, body, ...):  # text change NEVER changes element_id
        ...; self._rerender(goal_slug)

    def soft_remove(self, element_id):                # status='removed'; id never reused
        ...; self._rerender(goal_slug)

    def new_version(self, goal_slug) -> int:          # snapshot current -> requirement_versions, bump version
        ...

    def _rerender(self, goal_slug):
        self._rerender_requirements_md(goal_slug)     # spec-kit markdown (the FR-007 contract surface)
        self._rerender_requirements_html(goal_slug)   # US3 human render
```

`_rerender_requirements_md` is modeled line-for-line on `task_service._rerender_tasks_md:389`: SELECT
current rows ordered by `display_order`, render against `templates/cast-spec.template.md`, write
`goals/<slug>/refined_requirements.collab.md` with the existing header
`<!-- AUTO-GENERATED: Read-only render of DB state. Do not edit directly. -->`.

### Step 3: Write the `rows → spec-kit markdown` renderer (FR-007 byte-faithful)
**Impact: High** | **Effort: 1 day**

This is the load-bearing risk. The renderer is a pure function: rows ordered by `display_order` →
the exact spec-kit structure the checker expects. Re-emit `FR-001, FR-002, …` sequentially from sort
order (clean ordinals every render is *safe* because comments key on `element_id`). Embed the durable
key as an HTML-comment anchor the checker's regexes ignore:

```markdown
| FR-001 | The refined output shall lead with WHAT content... | US1 | <!-- el:req_<goal>_FR_001 -->
```

The checker only cares about the visible `FR-\d{3,}` token (`bin/cast-spec-checker:41`), so a parallel
durable key rides along invisibly. HTML render gets `id="req_…"`/`data-element-id="req_…"` on each
element node — those DOM anchors become Step 4's comment attach points (this is what kills the
"comments need React" premise: server-rendered anchored DOM + stable IDs is sufficient).

### Step 4: Lock FR-007 with a golden-file regression test
**Impact: High** | **Effort: 0.5 day**

This is the sign-off gate. Reuse `tests/test_us7_spec_kit_shape.py` as the harness shape:

```python
def test_rendered_md_passes_spec_checker(tmp_path):
    # 1. Backfill this goal's real refined_requirements.collab.md into element rows
    svc = RequirementService(db_path=str(tmp_path / "test.db"))
    import_markdown(svc, FIXTURE_MD)              # the backfill importer (Step 7)
    # 2. Render rows back out
    rendered = svc._rerender_requirements_md("refine-requirements-v2")
    # 3. Assert it passes the structural contract
    result = subprocess.run(["bin/cast-spec-checker", rendered_path], capture_output=True)
    assert result.returncode == 0
    # 4. Assert clean diff vs snapshot (modulo the AUTO-GENERATED header + el: anchors)
    assert normalize(rendered) == normalize(FIXTURE_MD)
```

SC-004 turned into CI. This is the item to put in front of the owner for explicit sign-off.

### Step 5: Repoint `cast-refine-requirements` to write rows, not the file
**Impact: High** | **Effort: 1 day**

`agents/cast-refine-requirements/cast-refine-requirements.md:305` currently hand-writes the markdown
file. Change it to emit structured elements through the service API (or ingestable JSON the service
consumes), exactly as `/cast-goals` and `/cast-tasks` already mutate the DB rather than the file. The
file becomes a generated artifact. This also flips the edit model: requirements move from
"editable textarea" (`api_artifacts.py:94` whole-file overwrite) to "edit rows, regenerate file" —
a real UX change to design for in Step 4/5, not a free win.

### Step 6: Add the HTML route (US3 seam)
**Impact: Medium** | **Effort: 0.5 day** (full render design is Step 5's job)

Add `routes/pages.py` route + `templates/pages/requirements_detail.html`, reusing the goal-detail
render path. v2 only needs the *seam* wired to the element rows; the L1/L2/L3 progressive-disclosure
design lands in exploration Step 5, which consumes this store.

### Step 7: One-shot backfill importer
**Impact: Medium** | **Effort: 0.5 day**

Parse existing `refined_requirements.collab.md` files into element rows so current goals migrate
cleanly. Reuse the spec-checker's own regexes (`US_HEADING_RE`, `FR_ID_RE`, `SC_ID_RE`,
`EARS_SCENARIO_RE`) as the parser — they already define the grammar. Idempotent: re-running detects
existing rows and no-ops (per the maintainer's kill-before-rebind / idempotency discipline).

## Architecture / Process Flow

```
  ┌─────────────────────────────────────────────────────────────────────┐
  │  WRITERS (same door — FR-013)                                        │
  │   human (HTML edit)   cast-refine-requirements   downstream agent    │
  │        │                      │                    (Step 7 write-back)│
  └────────┼──────────────────────┼────────────────────────┼────────────┘
           │   structured mutations (INSERT/UPDATE rows via API)
           ▼                      ▼                         ▼
  ╔═══════════════════════════════════════════════════════════════════╗
  ║  requirement_service.py   (raw SQL, render-after-mutate)           ║
  ║   _allocate_id ─ create/update/soft_remove ─ new_version ─ _rerender║
  ╚═══════════════════════════════════════════════════════════════════╝
           │ writes rows                          │ reads rows
           ▼                                       ▼
  ┌──────────────────────────┐         ╔══════════════════════════════╗
  │  SQLite (CANONICAL)       │         ║  PURE RENDERERS (read-only)  ║
  │  requirements   ──PK──┐   │         ║                              ║
  │  requirement_versions │   │ ─rows→  ║  rows → spec-kit markdown ───╫─→ refined_requirements.collab.md
  │  requirement_comments─┘   │         ║         (FR-007, golden test)║    (downstream agents: planner,
  │  element_id = durable     │         ║  rows → HTML (Jinja) ────────╫─→  task-suggester, spec-checker)
  │  identity (the keystone)  │         ║         (US3 human render) ──╫─→ requirements_detail.html
  └──────────────────────────┘         ╚══════════════════════════════╝     (id="req_…" anchors → Step 4 comments)

  CONSUMERS of element_id:  comments (Step 4) · version diff (Step 4) · archival (US5) · round-trip (Step 7)
  ── all become FK lookups, not text-anchor matching ──
```

## Key Decisions

| Decision | Recommendation | Rationale (and the trade-off) |
|----------|----------------|-------------------------------|
| DB-canonical vs files-canonical vs hybrid | **DB-canonical (Option A)** | Best ceiling; reuses an in-repo proven pattern. Trades a known, bounded FR-007 risk (retired by one test) for durable identity. Hybrid (shadow-parser) is the worst of both — reject explicitly. |
| Durable key form | **Prefixed counter `req_<goal>_<TYPE>_<NNN>`** | Greppable, matches `run_…`/slug conventions. Trades UUID collision-safety (irrelevant — DB allocates) for debuggability. |
| Display ordinal vs identity | **Separate them** — ordinal is a render projection | The single most load-bearing finding (Angle 1, Notion/ProseMirror). Lets us re-emit clean ordinals freely without breaking comment anchors. |
| Archive shape | **`requirement_versions` snapshot table (shape b)**, not `is_current` flag, not a folder | Maps US5 S1 (current→file) + S3 (old version *with comments*) cleanly. A folder can't retain comment/resolution coupling without becoming a worse DB. |
| Delete semantics | **Soft-delete (`status='removed'`)** | Requirements-engineering rule: IDs never reused. Cross-refs and historical comments stay valid. |
| Markdown fidelity bar | **Structural (pass checker) + snapshot diff**, not byte-identical | The checker parses structure/regex, not bytes (`cast-spec-checker:31-43`). Lower bar, fully sufficient, cheaper to hit. |
| Edit model under DB-canonical | **Edit rows → regenerate file** (drop textarea overwrite) | Required for US7 round-trip (whole-file last-write-wins is hostile to write-back). A real UX change to own, flagged for Step 4/5. |
| Git-visibility of history | **Optionally render archived versions to `archive/` as read-only artifacts** | Gives the contrarian their git-diffable history while DB stays canonical. Confirm with owner (open item). |
| Agent vs human write path | **Identical API door (FR-013)** | `POST /api/requirements/{element_id}/comments` is agent-callable as-is; the codebase already exposes agent routes (`api_agents.py`). Designing human-first-then-bolt-on-agent gets rebuilt. |

## Pitfalls to Avoid

1. **Coupling the durable key to the display ordinal.** The tempting shortcut is "just use `FR-001`
   as the primary key." The moment an element is inserted or reordered and the renderer renumbers,
   every comment, cross-ref, and diff anchored to the old number silently points at the wrong
   requirement. Keep `element_id` surrogate and the `FR-NNN` purely cosmetic — this is the whole game.

2. **Building the hybrid shadow-parser (Option C).** "Keep the file editable, maintain a shadow
   element table by parsing on save" sounds like the best of both worlds. It is the worst: two sources
   that drift, a markdown-dialect parser to maintain forever, and the fuzzy-anchoring problem returns
   the instant a human edits text a comment was anchored to. Reject it by name.

3. **Chasing byte-identical markdown.** FR-007 reads scarier than it is. The checker is *structural* —
   don't burn days matching whitespace. Pass `bin/cast-spec-checker` + a normalized snapshot diff and
   you're done. Over-engineering byte-stability is wasted effort.

4. **Re-importing the Hypothes.is problem.** If you anchor comments to text offsets or markdown line
   numbers "to keep files canonical," you've signed up for three selectors and four re-attachment
   strategies, and comments still orphan on edit. The entire reason that machinery exists is the
   absence of stable IDs. You have stable IDs — use them; comments are plain FK rows.

5. **Forgetting the edit-model flip.** Moving requirements under the read-only-render rule means the
   current editable textarea (`api_artifacts.py:94`) must be repurposed or removed. If you leave it,
   a human edits the file, the next mutation regenerates it, and their edit vanishes — a silent
   data-loss bug. Decide the edit path before flipping the switch.

6. **Treating the markdown render as optional.** Downstream agents (planner, task-suggester,
   spec-checker, goal-decomposer, detailed-plan) all read `refined_requirements.collab.md` as spec-kit
   markdown. The render is not a nice-to-have — it's a hard contract (SC-004). The DB being canonical
   does not relieve you of always emitting a structurally-valid file at the same path.

7. **Hard-coding the maintainer's families into the schema.** FR-012 demands generalization. Keep
   `element_type` and `origin_phase` open string columns, not enums tuned to three workspaces. The
   schema is a public OSS contract — a clean table is a better one than "parse my markdown dialect."

8. **Skipping the backfill idempotency check.** Re-running the importer must not duplicate rows or
   error. Detect existing `(goal_slug, element_id)` and no-op. (Matches the kill-before-rebind /
   re-runnable discipline the repo's seed scripts already follow.)

## Success Metrics

- **FR-007 gate green:** `bin/cast-spec-checker` exits 0 on the rendered `refined_requirements.collab.md`,
  and the full downstream agent chain (planner, task-suggester, spec-checker) runs green on a
  migrated goal. Target: 100% pass before merge (SC-004).
- **Render fidelity:** normalized snapshot diff between the original fixture and the rows→markdown
  render is empty (modulo the AUTO-GENERATED header + `el:` anchors). Target: 0 unexpected diff lines.
- **Stable-ID survival:** after inserting an element between two existing FRs and re-rendering, every
  pre-existing `element_id` is unchanged and every comment still resolves to its original element.
  Target: 0 orphaned comments across an insert/reorder/edit cycle.
- **Archive integrity (US5 S3):** retrieving version N returns its elements *and* their comments +
  resolution state. Target: comment count and open/resolved state for v_N match what was recorded at
  the time v_N was current.
- **Agent-write parity (FR-013):** an agent creates an element and leaves a comment through the same
  API a human uses, with no human-only path. Target: 1 end-to-end agent-authored element+comment with
  correct provenance (`origin_phase`, `author`).
- **Migration coverage:** the backfill importer round-trips every existing goal's
  `refined_requirements.collab.md` into rows and back to a checker-valid file. Target: 100% of existing
  goals migrate without manual fixup; re-run is a no-op.

## Impact Rating: 10

**Justification:** This is the explicit keystone — `steps.ai.md` and the spec both name stable element
identity as the primitive that Steps 4 (comments/diffs/versions), 5 (HTML render), US5 (archival), and
7 (round-trip provenance) all consume. Getting it right makes those features plain foreign keys;
getting it wrong forces a re-architecture of every dependent feature, which is the single most
expensive mistake to reverse in this goal. The recommendation is unusually low-risk for a 10 because it
*extends a pattern the codebase already runs* (`_rerender_tasks_md`) rather than inventing one, and its
lone real risk (FR-007 byte-fidelity) is bounded and retired by one golden test.
