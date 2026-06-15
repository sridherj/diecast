# Code Exploration: Annotation & Iteration Engine (Step 4)

**Goal context:** Refine Requirements v2 — Workflow-Aware, HTML-First Requirements Refinement.
Step 4 designs the **iteration engine**: inline Google-Docs-style comments anchored to
requirement elements, an open/resolved lifecycle with a retained resolution trail (FR-009/010),
version progression where unresolved comments drive v2/v3 (US4/US5), per-version change summaries
that diff stable-ID elements (FR-017), and an agent-callable parity contract (FR-013) — all on the
**lightest stack that actually works**. The headline question this exploration must *kill or
confirm with evidence*: **does any of this require migrating cast-server off FastAPI+Jinja to
React/Next.js?**

**Codebase:** `/home/sridherj/workspace/diecast` (same git repo as `/data/workspace/diecast`;
`.cast` symlinks the goal dir). `cast-server/` is the relevant subtree.
**Date:** 2026-06-11
**Tooling note:** code-review-graph MCP graph was not built (startup hook reported "No knowledge
graph found"). All citations below are from direct Read/Grep firsthand — every file:line verified.
**Relationship to Step 2:** Step 2 (`02-canonical-source-of-truth-code.ai.md`) already mapped the
store, the stable-ID gap, and the build-free stack. This file does **not** re-derive that; it goes
deep on the *comment/version/diff* surfaces and owns the React verdict (Step 2 only flagged it).

---

## TL;DR for the synthesizer — the verdict

**React/Next.js is NOT required. Confirmed with evidence, not assumed.** Three independent facts
settle it:

1. **There is no JS build toolchain to migrate *to* a framework from — and nothing pulls toward
   one.** No `package.json`, no npm/Vite/webpack anywhere in `cast-server/` (the only repo
   `package.json` is a cast-preso *template fixture*, `skills/.../cast-preso-visual-toolkit/base-template/package.json`,
   unrelated). The frontend is `base.html` → vendored **HTMX** (`base.html:13`) + vanilla `<script>`
   + vendored **EasyMDE** (`base.html:153`) + hand-written `style.css` (4156 lines). Adopting React
   would mean *introducing* a build step this project deliberately doesn't have — pure cost, no
   forcing function.

2. **The only thing the Google-Docs UX actually needs is a stable anchor in the DOM — and Step 2's
   stable element IDs supply exactly that.** Annotation is hard *when the document is opaque text*
   and you must re-find a highlight after edits (quote/XPath anchoring — the classic
   annotator.js/Hypothesis problem). But if each US/FR/SC renders as a DOM node carrying
   `data-element-id="<surrogate>"`, a comment is just a DB row keyed to that surrogate, and the
   "anchor" is a CSS selector lookup — no fuzzy text-matching, no framework. The whole React premise
   rested on "comments ⇒ rich client state"; element IDs collapse it to "comments ⇒ rows + a 150-line
   vanilla-JS margin layer."

3. **The agent-parity contract (FR-013) is *already* how this codebase works** — humans drive the UI
   through FastAPI routes via HTMX; agents drive the *same* FastAPI HTTP API directly
   (`routes/api_agents.py`). The proven content-negotiation pattern (`api_agents.py:337` — `HX-Request`
   header → HTML fragment, else JSON) means one comment/version endpoint can serve the human UI *and*
   an agent through the same door. React would actively *fight* this — it would split the human path
   (client JS) from the agent path (API), the exact "build the GUI then bolt on an agent API later"
   anti-pattern the spec warns against.

**Everything in Step 4 is greenfield** — no comment table, no version column, no diff util, no
annotation markup, zero JS doing text selection. That is freedom, not debt: design it once, keyed to
Step 2's element surrogates. The recommended stack is **server-rendered anchored DOM + a thin
vanilla-JS comment layer + plain REST endpoints with HTMX content-negotiation** — no new heavy
dependency, no migration.

---

## 1. Data Model & Schema

Canonical schema: `cast-server/cast_server/db/schema.sql` (SQLite, raw SQL, no ORM). A second tier of
tables is created **programmatically** in `db/connection.py` (e.g. `agent_error_memories`), so the
schema picture spans both files.

### What exists that is relevant to Step 4

| Table | Where | Relevance to the iteration engine |
|-------|-------|-----------------------------------|
| `agent_error_memories` | `db/connection.py` (programmatic) | **The open/resolved-with-trail precedent.** Columns: `resolution_status ∈ {unresolved, escalated, resolved}`, `resolution` (text), `occurrence_count`, `run_ids` (JSON), `last_seen`. `resolve_memory()` flips status + stores resolution text (`error_memory_service.py:173-178`). This is *exactly* the lifecycle a comment needs (open → resolved + retained trail). |
| `goal_suggestions` | `schema.sql:49-58` | Second lifecycle precedent: `status DEFAULT 'pending'`, `resolved_at`, `created_goal_slug`. Open/resolve with a resolution timestamp and a forward-link to what the resolution produced — mirrors "comment resolved → which version addressed it." |
| `agent_runs` | `schema.sql:73-92` | `status` lifecycle + `artifacts`/`output` as JSON + timestamps. The model a *version* row could mirror (a version is a status-bearing, timestamped, artifact-producing record). |
| `tasks` | `schema.sql:16-39` | Has `sort_order`, `parent_id` self-FK, `completion_notes`. The DB-canonical entity whose `_rerender_tasks_md` loop (Step 2) is the render-after-mutate template a version renderer copies. |

### What does NOT exist (the greenfield, confirmed by grep)

- **No `comments` / `annotations` / `notes` table.** Only hit for `comment|annotat|note` in
  `schema.sql` is `tasks.completion_notes` (`schema.sql:31`) — unrelated.
- **No version / diff / archive machinery.** `grep -rinE "\bversion\b|diff|archive"` across all of
  `services/` + `schema.sql` returns only `contract_version` fields (delegation, unrelated) and one
  prose string in `agent_service.py:1237`. No `spec_versions` table, no version column on anything
  requirement-shaped, no diff utility, no archive-folder convention.
- **No element-level identity** (Step 2 gap #1, restated because Step 4 is its first real consumer):
  `FR-001`/`US1`/`SC-001` are agent-typed *text labels* in markdown, with nothing allocating or
  persisting them. **A comment anchored to "FR-001" today would silently re-point to a different
  requirement the moment the agent renumbers on a rewrite.** This is the single dependency Step 4
  inherits from Step 2 and cannot proceed without.

```
                          STEP 4 TARGET DATA MODEL (all net-new — keyed to Step 2's surrogates)

  spec_elements (Step 2)                spec_versions (NEW)            comments (NEW)
  ┌─────────────────────┐               ┌────────────────────┐        ┌───────────────────────────┐
  │ element_uid (ULID) ◄─┼───anchor──────┼ (n/a)              │        │ id                        │
  │ goal_slug           │               │ goal_slug          │        │ element_uid  ───anchor────┘ (FK→spec_elements)
  │ version             │               │ version (v1,v2,…)  │        │ goal_slug                 │
  │ kind (US|FR|SC|scen)│               │ status: current|   │        │ author_kind: human|agent  │  ← FR-013
  │ display_label       │               │   archived         │        │ author_ref (agent_run_id?)│
  │ ordinal, body       │               │ created_at         │        │ body                      │
  └─────────────────────┘               │ change_summary(JSON)│       │ status: open|resolved     │  ← FR-009/010
        ▲                                │ created_by_kind    │       │ resolved_in_version       │  ← drives US4 S3
        │ display_label is a render-time │ created_by_ref     │       │ resolution_trail (JSON)   │  ← retained trail
        │ projection of (kind,ordinal);  └────────────────────┘       │ created_at, resolved_at   │
        │ element_uid is the DURABLE anchor                            └───────────────────────────┘
```

The shape above is the *implication* of the existing precedents (`agent_error_memories` for
status+trail, `goal_suggestions` for resolve+forward-link, `_rerender_tasks_md` for the version
render loop) — it is for the synthesizer to ratify, not a built thing.

---

## 2. Existing Implementation

### 2a. How a requirement document renders today — the surface comments must attach to

`routes/api_artifacts.py:110` `artifact_sidebar` is the only path that turns a requirements file into
HTML:

```
read_text()  →  md.markdown(content, extensions=["fenced_code","tables","toc","codehilite"])  (api_artifacts.py:131-133)
             →  ONE opaque HTML string ("html")
             →  fragments/artifact_sidebar.html:14  {{ artifact_content(html) }}
             →  macros/markdown_viewer.html:27  artifact_content() = <div class="markdown-body">{{ html|safe }}</div>
```

**The blob has no per-element wrapping and no `id=` anchors** — confirmed: grep for
`attr_list|id=|data-element|anchor` in `api_artifacts.py` + `markdown_viewer.html` returns nothing.
So today there is *physically nothing in the DOM* a comment could anchor to. This is the concrete
implementation gap Step 4 closes, and it's small: the `markdown` lib ships an `attr_list` + `toc`
extension that injects `id=` on elements, and (under Step 2's Option A) a bespoke element renderer
emits `<section data-element-id="…">` directly. Either way the fix lives in *one render function*,
not a framework.

### 2b. How editing works today — and why it's hostile to the iteration loop

- `GET /api/artifacts/edit` → textarea of raw file content (`api_artifacts.py:60-78`).
- `PUT /api/artifacts/save` → `resolved.write_text(content)` — **whole-file overwrite,
  last-write-wins** (`api_artifacts.py:94`).
- Only `.human.md`/`.collab.md` are editable (`validate_artifact_path:44-49`).
- EasyMDE is wired *imperatively* on `htmx:afterSwap` (`base.html:155-167`) — a textarea becomes a
  markdown editor with a fixed toolbar (no comment affordance).

Whole-file overwrite is the enemy of both anchored comments (it would clobber any in-file anchor on
every save) and US7 round-trip write-back. This is positive evidence for **moving requirements under
Step 2's DB-canonical model**, where "edit" means "mutate a row + re-render" and comments live in
their own table untouched by edits.

### 2c. The agent-parity door already exists — FR-013 is a *reuse*, not an invention

`routes/api_agents.py` is the proof that **this system was built API-first with the UI as one
consumer.** Every agent lifecycle operation a human triggers from the UI is a plain HTTP endpoint an
agent calls identically:

- `POST /api/agents/{name}/trigger` (`:88`) — dispatch (the very endpoint *this* exploration run was
  launched through; see `.delegation-run_*.json`).
- `GET /api/agents/jobs/{run_id}` (`:232`), `POST .../recheck` (`:284`), `POST /runs/{id}/continue`
  (`:380`), `/complete` (`:390`), `/cancel` (`:415`), `/fail` (`:445`), `DELETE /runs/{id}` (`:433`).
- `POST /api/agents/error-memories/{id}/resolve` (`:455`) — **a resolve endpoint already exists** for
  a different entity; the comment-resolve endpoint is the same shape.

The decisive precedent is `list_runs` (`api_agents.py:325-345`): **one endpoint, content-negotiated**
— `if request.headers.get("hx-request") != "true": return JSONResponse(result)` else return an HTML
fragment. This is the template for the entire Step 4 API: `POST /api/specs/{slug}/comments`,
`POST .../comments/{id}/resolve`, `POST .../versions` each return **JSON to an agent** and an **HTMX
fragment to the browser** from the *same handler*. FR-013 ("agent uses the same mechanism as a
human") is satisfied by following a pattern already in the file, not by new architecture.

### 2d. Rich generated HTML is already served from the goal folder

`pages.py:299` `/preso/review/{goal_slug}` does `HTMLResponse(path.read_text())` over a
pre-generated `presentation/review.html`. Proof the system already serves bespoke, fully-styled HTML
documents straight from disk. A versioned, anchored requirements HTML render can be served the same
way — no SPA needed to deliver a polished document surface.

---

## 3. Gap Analysis

| # | Gap | Severity | Evidence |
|---|-----|----------|----------|
| 1 | **No element identity to anchor comments to** (inherited from Step 2 #1). Comments need a durable target; `FR-001` text is renumber-fragile. Step 4 *cannot* ship before this lands. | **Critical / blocking** | No `spec_elements` table; checker only dedups `FR-NNN` text (`cast-spec-checker.md:43-44`) |
| 2 | **Rendered HTML has zero anchorable DOM nodes.** One opaque blob, no `id=`/`data-*`. Nothing for a comment popover to attach to. | **Critical** | `api_artifacts.py:131-133` blob; `markdown_viewer.html:27` `{{ html\|safe }}`; grep for `id=`/`attr_list` empty |
| 3 | **No comment data model or markup** (US4, FR-009/010). No table, no route, no margin/thread template, no selection JS (`getSelection`/`mouseup` grep empty). | **High — greenfield** | `grep comment\|annotat\|note` → only `completion_notes` |
| 4 | **No version progression** (US4 S2, US5). No version column, no "open comments ⇒ unconverged" gate, no v_n+1 producer. | **High — greenfield** | `grep version` → only `contract_version` |
| 5 | **No change-summary / diff** (FR-017). No diff util anywhere; the render-after-mutate loop produces files but never diffs them. | **High — greenfield** | `grep diff` → none in `services/` |
| 6 | **No archive mechanism** (US5, FR-011). No archive table, no archive-folder convention; artifact discovery is a flat folder rglob (`pages.py:113-125`) that would *show* old versions if they sat in the folder. | **High — greenfield** | `grep archive` → none |
| 7 | **Whole-file overwrite save is hostile to anchored comments + round-trip.** Any in-file anchor or downstream write-back is clobbered last-write-wins. | **Medium (becomes High under Option B)** | `api_artifacts.py:94` `write_text(content)` |
| 8 | **EasyMDE is a markdown-source editor, not a rendered-doc annotator.** The current editing affordance is the wrong primitive for inline comments; comments attach to the *rendered* doc, not the source textarea. | **Medium** | `base.html:155-167` EasyMDE on raw textarea |
| 9 | **No notification surface for "requirements changed"** (feeds US7, but the toast plumbing exists). `showToast` + `HX-Trigger` toast header exist (`base.html:101`, `utils/responses.toast_header`) — a notification *mechanism* is present; a *requirements-changed* event is not. | **Low** | `base.html:101-117`; `api_artifacts.py:106` |

---

## 4. Patterns & Conventions (the ones Step 4 must conform to)

- **API-first, UI-as-consumer.** Every mutation is an HTTP endpoint; the browser reaches it via HTMX,
  agents via raw HTTP. **Content-negotiate on `HX-Request`** to serve both from one handler
  (`api_agents.py:337`). *This is the FR-013 mechanism — adopt it verbatim.*
- **MVCS, raw SQL, `db_path=` injectable services** (`goal_service.py:33`, `task_service.py`). New
  `comment_service.py` / `spec_version_service.py` follow this for testability.
- **DB canonical, files are read-only projections, render-after-mutate.** `_rerender_tasks_md`
  (`task_service.py:389`, runs after *every* mutation) and `_write_goal_yaml` (`goal_service.py:337`)
  carry the "AUTO-GENERATED: Read-only render of DB state. Do not edit directly." stamp. A version
  renderer mirrors this loop.
- **Open/resolved-with-trail is an established lifecycle.** `agent_error_memories.resolution_status`
  (unresolved/escalated/resolved) + `resolution` text (`error_memory_service.py:102-114,173-178`) and
  `goal_suggestions.status`+`resolved_at` (`schema.sql:49-58`). Comments reuse this shape.
- **Build-free frontend.** HTMX + vanilla `<script>` + vendored libs (`static/vendor/easymde/`),
  hand-written CSS. New interaction = a small vendored/inline script + HTMX swaps, **never** a build
  step. Imperative wiring on `htmx:afterSwap` (`base.html:155`) is the established hook for "enhance
  a freshly-swapped fragment with JS" — the comment layer attaches the same way.
- **Toast + `HX-Trigger` for user feedback** (`base.html:101-117`, `toast_header`) — the notification
  channel US7 reuses.
- **Path safety gate.** `_validate_artifact_path_base` (`api_artifacts.py:20`) confines file ops to
  `GOALS_DIR`/`external_project_dir`. Any new render/archive write routes through it.

---

## 5. Entry Points & Flow

### Flow A — Comment lifecycle on the recommended stack (server-rendered anchored DOM + vanilla-JS layer)

```
RENDER (server):
  spec_elements rows ──► requirements render fn ──► HTML where each element is
                                                    <section class="req-el" data-element-id="el_01H…">…</section>
                                                    (vs today's single opaque blob, api_artifacts.py:131)

HUMAN comments (browser):
  user selects text inside .req-el  ──► tiny vanilla JS (window.getSelection → nearest [data-element-id])
        └─► "Add comment" popover ──► POST /api/specs/{slug}/comments {element_uid, body}   (HX-Request:true)
                                          └─► comment_service.add() INSERT comments row (status='open')
                                          └─► returns HTML fragment: margin thread for that element (HTMX swap)

AGENT comments (FR-013, same door):
  agent ──► POST /api/specs/{slug}/comments {element_uid, body, author_kind:"agent", author_ref:run_id}
                (no HX-Request header) └─► SAME handler ──► returns JSON {comment_id, status:"open"}

RESOLVE:
  POST /api/specs/{slug}/comments/{id}/resolve {resolution}  (mirrors error-memories/{id}/resolve, api_agents.py:455)
        └─► status='resolved', resolved_at, resolution_trail appended  (trail retained — FR-010)
```

### Flow B — Version progression driven by unresolved comments (US4 S2, FR-017)

```
"Produce next version" (human button OR agent POST /api/specs/{slug}/versions):
  spec_version_service.create_next():
    ├─ gate: count comments WHERE status='open'        (open comments ⇒ spec is "unconverged")
    ├─ snapshot current spec_elements → version=v_n      (status='current')
    ├─ archive prior current → status='archived'         (US5: only current in main folder)
    ├─ DIFF spec_elements[v_{n-1}] vs [v_n] BY element_uid  ──► change_summary JSON   (FR-017)
    │      (added / removed / modified element_uids — a structural delta, NOT a text diff,
    │       because element_uid gives stable identity across versions — Step 2's payoff)
    ├─ carry comment resolution across versions (resolved_in_version stamped)
    └─ _rerender_requirements_md + _rerender_requirements_html   (render-after-mutate, à la _rerender_tasks_md)
            └─ only the CURRENT version's file projection lands in goals/<slug>/  (FR-011)
```

### Flow C — Today's path, for contrast (what we are replacing)

```
agent hand-writes refined_requirements.collab.md  (cast-refine-requirements.md:305)
  → GET artifact-sidebar → md.markdown() → opaque blob → {{ html|safe }}     (no anchors, no comments)
  → edit = textarea → PUT save → write_text() whole-file overwrite           (no versions, no diff)
```

The delta A+B over C is **additive**: new tables + new endpoints + a richer render fn + a small JS
layer. No existing route is rewritten beyond pointing the render at element rows. The stack does not
change.

---

## 6. Tests & Coverage

- **Render-after-mutate is a tested pattern.** `cast-server/tests/` has `integration/`, `e2e/`, `ui/`
  dirs; task re-render behavior is exercised — the version renderer inherits a tested harness shape.
- **FR-007 regression gate is ready-made.** `tests/test_us7_spec_kit_shape.py` runs
  `bin/cast-spec-checker` against the spec file (Step 2 finding). Version renders must keep passing it:
  *render v_n → run checker → assert exit 0*. Reuse directly.
- **Content-negotiation is testable both ways** — the `list_runs` HTMX-vs-JSON split
  (`api_agents.py:337`) shows the existing test approach (assert HTML for `HX-Request`, JSON
  otherwise). Comment/version endpoints get the same dual assertion, which is *also* the FR-013
  agent-parity test (an agent's JSON call and a human's HTMX call hit one handler).
- **Path-validation is the security-sensitive surface** to keep covered as archive/render write paths
  are added (`api_artifacts.py:20-57`).
- **Everything Step 4 introduces is greenfield-with-new-tests** — there is no comment/version/diff
  test today because there is no such code. Net-new coverage, not retrofit into legacy.
- **No JS test infra exists** (no package.json) — the vanilla-JS comment layer should be kept thin
  enough to verify via the existing Playwright-style `tests/ui/` e2e path rather than unit JS tests,
  reinforcing "keep the client logic minimal."

---

## 7. Config & Dependencies

- **Markdown→HTML:** Python `markdown` (`api_artifacts.py:6`) with `fenced_code, tables, toc,
  codehilite`. **`attr_list` is available in the same library** (not yet enabled) — enabling it lets
  the server inject `id=`/`data-*` on elements with zero new dependency, a cheap path to anchorable
  DOM even under Option B (files-canonical).
- **Frontend libs (all vendored, no build):** HTMX (`static/htmx.min.js`, `base.html:13`), EasyMDE
  (`static/vendor/easymde/`, `base.html:9,153`). Fonts via Google Fonts `<link>`. **No
  package.json / npm / bundler in `cast-server/`** — verified by `find -name package.json`
  (only hit is an unrelated cast-preso template fixture).
- **Annotation-library landscape (external, for the synthesizer's verdict):** the well-known JS
  annotation libs — **annotator.js / Hypothesis client, RecogitoJS, Annotorious, CommentBox** — almost
  all anchor on **text-quote / XPath / CSS-selector ranges** because they're built to annotate
  *immutable* published documents (PDFs, articles, images). Against an *iterating* spec they re-create
  exactly the fragile-text-anchor problem the Multi-Lens insight named: an edit shifts the quote and
  the highlight detaches. **With Step 2's stable element IDs you don't need quote-anchoring at all** —
  anchoring to a stable DOM `data-element-id` is simpler, exact, and survives re-renders. So the
  evidence-based recommendation is: *neither React nor a heavyweight annotation library is warranted*;
  a ~150-line vanilla-JS selection→popover→HTMX layer over anchored DOM is both lighter and more
  robust than adopting a library designed for the wrong (immutable-doc) problem.
- **DB:** stdlib `sqlite3` via `db/connection.py`; `schema.sql` + programmatic tables. New tables
  (`comments`, `spec_versions`) are added the same way; Alembic is present but the team hand-maintains
  `schema.sql` (single baseline migration, per Step 2).
- **Notification plumbing:** `HX-Trigger` toast header (`utils/responses.toast_header`,
  `api_artifacts.py:106`) + `showToast`/`htmx:responseError` listeners (`base.html:101-127`). US7's
  "requirements changed" notice rides this existing channel.

---

## Key Takeaways

1. **The React/Next.js question is settled NO, on three independent legs:** (a) there is no build
   toolchain to migrate to and nothing pulling toward one (no `package.json` in `cast-server/`);
   (b) Step 2's stable element IDs reduce "Google-Docs comments" to "rows keyed to a `data-element-id`
   + a thin vanilla-JS layer," removing the rich-client-state premise React was invoked for; (c)
   migrating would *break* the FR-013 agent-parity model the codebase already embodies by splitting
   the human path from the agent path. The lightest stack that works is the *current* stack.

2. **FR-013 is a reuse, not a build.** `routes/api_agents.py` proves the system is API-first with the
   UI as one consumer, and `list_runs` (`:337`) proves the content-negotiation pattern (one handler →
   HTML for `HX-Request`, JSON otherwise) that lets a single comment/version endpoint serve human and
   agent through the same door. There is even a working `…/resolve` endpoint precedent
   (`error-memories/{id}/resolve`, `:455`). Build comment/version ops as plain REST and the agent
   parity falls out for free.

3. **The hard dependency is Step 2's element identity — Step 4 is its first real consumer and cannot
   ship without it.** Every Step 4 feature (anchor, resolve-trail carry-across-versions, structural
   diff) keys off a durable `element_uid`. Today comments would anchor to renumber-fragile `FR-001`
   text. This is the one thing that must land first.

4. **The change-summary (FR-017) is a *structural* diff, not a text diff — which is only possible
   because of stable IDs.** Diffing `spec_elements` by `element_uid` between versions yields
   added/removed/modified elements precisely; a markdown text-diff would be noise. This is the
   concrete payoff that ties Step 2's keystone decision to Step 4's iteration loop, and it reuses the
   render-after-mutate convention (`_rerender_tasks_md`) for emitting the new version's files.

5. **The current whole-file-overwrite edit path (`api_artifacts.py:94`) is the thing that breaks** if
   you try to bolt comments onto files-canonical (Option B). Last-write-wins clobbers any in-file
   anchor and any downstream round-trip. This is strong corroborating evidence for moving requirements
   under Step 2's DB-canonical model, where comments live in their own table and "edit" is row-mutate +
   re-render — leaving comments untouched.

6. **What's surprisingly good and should be preserved:** the API-first/content-negotiated architecture
   (`api_agents.py`), the established open/resolved-with-trail lifecycle (`agent_error_memories`,
   `goal_suggestions`), the render-after-mutate loop (`_rerender_tasks_md`), the rich-HTML-from-disk
   precedent (`/preso/review`), and the build-free frontend. Step 4 is almost entirely *composition of
   patterns already in the repo* onto net-new tables — the lowest-risk way to ship a Google-Docs-grade
   UX.

7. **Greenfield is total for comments/versions/diff/archive** (gaps #3–#6). No legacy to retrofit:
   design the comment/version/diff schema once, keyed to element surrogates, following the three
   established precedents. The only existing surfaces that change are the *render function* (emit
   anchored DOM, gap #2) and the *edit model* (row-mutate vs file-overwrite, gap #7) — both small,
   localized, and already pointed at by Step 2's Option A.

## Key Files

- `cast-server/cast_server/routes/api_agents.py:337` — **the FR-013 pattern**: one handler,
  content-negotiated HTML (HTMX) vs JSON (agent). The template every comment/version endpoint follows.
- `cast-server/cast_server/routes/api_agents.py:455` — `error-memories/{id}/resolve`: a working
  resolve endpoint; the comment-resolve shape.
- `cast-server/cast_server/routes/api_artifacts.py:110-155` — the *only* requirements→HTML render
  today (opaque blob, no anchors). Where anchored-DOM rendering lands (gap #2).
- `cast-server/cast_server/routes/api_artifacts.py:81-107` — whole-file-overwrite save; the edit model
  hostile to anchored comments (gap #7).
- `cast-server/cast_server/templates/macros/markdown_viewer.html:27` — `artifact_content()` =
  `{{ html|safe }}`; the single render macro to make element-aware.
- `cast-server/cast_server/templates/base.html:13,153-167` — build-free frontend: HTMX + vanilla JS +
  EasyMDE-on-`htmx:afterSwap`. The hook pattern the comment JS layer reuses; the evidence there is no
  framework to migrate from.
- `cast-server/cast_server/services/error_memory_service.py:102-114,173-178` — open/resolved +
  retained `resolution` trail; the comment lifecycle precedent (FR-009/010).
- `cast-server/cast_server/db/schema.sql:49-58` (`goal_suggestions`) & `:73-92` (`agent_runs`) —
  status-lifecycle + resolved_at + JSON-artifact precedents the comment/version tables mirror.
- `cast-server/cast_server/services/task_service.py:389` — `_rerender_tasks_md`: the render-after-mutate
  loop a version renderer copies (also Step 2's Option A template).
- `cast-server/cast_server/routes/pages.py:299` — `/preso/review/{slug}`: rich generated HTML served
  from the goal folder; proof a polished requirements doc surface needs no SPA.
- `cast-server/cast_server/utils/responses.py` (`toast_header`) + `base.html:101-117` — the
  `HX-Trigger` toast channel US7's "requirements changed" notification reuses.
- `cast-server/cast_server/db/connection.py` — where `agent_error_memories` is created
  programmatically; the second place new tables (`comments`, `spec_versions`) could be defined.
- `agents/cast-refine-requirements/cast-refine-requirements.md:305` — where the spec is hand-authored
  today; the agent that learns to write rows + drive the comment/version API (FR-013 producer side).
```
