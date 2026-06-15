# Playbook — Annotation & Iteration Engine (Step 4)

**Goal:** Refine Requirements v2 — Workflow-Aware, HTML-First Requirements Refinement.
**Step 4 owns:** inline element-anchored comments, the open/resolved lifecycle with a retained
trail, version progression driven by unresolved comments, the per-version change summary, and the
agent-parity contract (agents comment/resolve/version through the *same door* as humans).
**Synthesized from:** `research/04-annotation-and-iteration.ai.md` (web, 7 lenses) +
`research/04-annotation-and-iteration-code.ai.md` (codebase terrain) + `steps.ai.md` (Step 4) +
`refined_requirements.collab.md` (US4/US5/US7, FR-008–FR-013, FR-017).
**Date:** 2026-06-11 · **Stance:** opinionated, one pick per component, unconstrained by the current
codebase but priced against it.

---

## TL;DR

**Do NOT migrate to React/Next.js. Build element-anchored comments as plain DB rows keyed to Step 2's
stable element surrogate (a ULID), mutated through FastAPI endpoints that content-negotiate HTMX
fragments for the browser and JSON for agents from one handler.** This is settled on three independent
legs: (1) the hard part of "Google-Docs comments" — fuzzy text re-anchoring — *disappears* the moment
elements have durable IDs, so a comment is a foreign key, not a character range; (2) every mature
annotation library (RecogitoJS, Annotorious, Hypothesis) is vanilla-JS-first — React is never required,
and the React-first ones (Velt) are a trap that buys nothing; (3) the only requirement that genuinely
forces an SPA — realtime multi-user co-editing — is *explicitly out of scope* (async, single-writer).

**Don't adopt an annotation library either.** Those libraries solve anchoring free-text selections in
prose you don't control; Step 2's architecture deletes that problem. Pulling one in *re-imports* the
fragile text-anchoring you paid to eliminate. Ship a **~150-line vanilla-JS selection→popover→HTMX
layer** over server-rendered anchored DOM instead.

**Model the data on the W3C Web Annotation Data Model (schema north star) and GitHub PR-review-comments
(versioning + bot-parity reference) — not Google Docs** (that's only the UX reference). A version is an
*immutable snapshot* of element rows; comments key to the **element**, not the version, so an open
comment rides from v2→v3 automatically if its element still exists, and orphans surface for triage
instead of vanishing. The change summary (FR-017) is **structural set arithmetic over surrogates**
(added/removed/modified/unchanged) — deterministic truth — optionally *narrated* by an LLM, never
*invented* by one.

**The forcing function for FR-013:** build the JSON/REST comment+version API **first**, then build the
HTMX UI as a client of it. If the UI ever writes to the DB through a path an agent can't call, agent
parity is already broken.

**Hard dependency:** this entire step sits on Step 2's `spec_elements` table with a persisted surrogate
per US/FR/SC. Step 4 *cannot ship before that lands*, and the surrogate should be fine-grained
(scenario/clause level) so comments can point at something meaningful.

---

## Recommended Stack

| Component | Pick | Why this, not the alternative |
|-----------|------|-------------------------------|
| **Frontend framework** | **None — stay on HTMX + vanilla JS** (already vendored, `base.html:13`) | React/Next.js solves realtime co-editing (out of scope). Nothing else here needs a vDOM or client state lib. No `package.json` exists to migrate from — adopting React is pure cost. |
| **Comment anchor** | **Foreign key to `spec_elements.element_uid` (ULID)** | Step 2 hands us durable IDs. Anchoring to a row key beats TextQuote/XPath/offset selectors — no fuzzy matching, no orphan-recovery engine, exact and re-render-proof. |
| **Annotation library** | **None — ~150-line vanilla-JS layer** | RecogitoJS/Hypothesis exist to anchor selections in *immutable* prose; against an *iterating* spec they re-create the fragile-anchor problem. Element IDs make a library negative-value. |
| **Comment/version data model** | **W3C Web Annotation Data Model shape** (`body` + `target{selector}`), borrowed not literal JSON-LD | Standards-aligned, forward-compatible: start with an element-ID `FragmentSelector`, add a `TextQuoteSelector` for sub-spans later *without schema change*. |
| **Versioning model** | **GitHub PR-review-comment pattern**: anchor to stable unit + version, re-map between versions, "outdated/orphaned" is first-class | Proven for *editable, versioned, bot-participating* document review — exactly our shape. Strictly easier than GitHub because our unit is explicitly persistent. |
| **Persistence** | **stdlib `sqlite3` + raw SQL** via `db/connection.py`; new `comments`, `comment_events`, `spec_versions` tables | Matches the repo's no-ORM convention; comment/version/diff are textbook relational CRUD. |
| **HTML render → anchored DOM** | **Python `markdown` + `attr_list` extension** (already a dep, `api_artifacts.py:6`) emitting `data-element-id` per element; or Step 2's bespoke `<section>` renderer | `attr_list` is in the lib, not yet enabled — anchorable DOM with **zero new dependency**. |
| **API surface** | **FastAPI routes, content-negotiated on `HX-Request`** (verbatim from `api_agents.py:337`) | One handler → HTML fragment for HTMX, JSON for agents. This *is* the FR-013 mechanism; it already ships in this codebase. |
| **Stable-ID generation** | **`python-ulid`** for `element_uid` (Step 2 seam) | Sortable, collision-free, opaque — decoupled from the human-facing `FR-001` display label which is a render-time projection. |
| **Change-summary narration** | **Deterministic structural diff first; LLM as optional *renderer* second** | Never let the LLM invent the diff (hallucinated changelogs). Diff = source of truth; prose = view over it. |
| **Notification channel** | **Existing `HX-Trigger` toast header** (`utils/responses.toast_header`, `base.html:101`) | US7 "requirements changed" reuses plumbing already present; no new channel. |

---

## Architecture

```
                          ELEMENT-ANCHORED, API-FIRST, BUILD-FREE

  ┌──────────────── canonical store (Step 2) ────────────────┐
  │  spec_elements(element_uid ULID PK, goal_slug, version_id,│
  │                kind∈US|FR|SC|scenario, display_label,     │
  │                ordinal, body, prev_uid?)  ◄── durable anchor
  └───────────────────────────┬──────────────────────────────┘
                              │ FK (element_uid)
        ┌─────────────────────┼─────────────────────────┐
        ▼                     ▼                         ▼
  ┌───────────┐        ┌──────────────┐          ┌─────────────────┐
  │ comments  │        │comment_events│          │ spec_versions   │
  │ id        │        │ (append-only │          │ id              │
  │ element_uid───anchor│  trail FR-010│          │ goal_slug       │
  │ goal_slug │        │ comment_id   │          │ version_no      │
  │ version_opened      │ event∈opened/│          │ status∈draft|   │
  │ author_kind∈human|agent replied/   │          │  unconverged|   │
  │ author_ref(run_id?) │  resolved/   │          │  converged|     │
  │ body              │ │  reopened/   │          │  archived       │
  │ state∈open|resolved│ │  orphaned    │          │ change_summary  │
  │  |orphaned        │ │ actor,_kind  │          │   (JSON)        │
  │ resolved_in_version│ │ version_id   │          │ created_by_kind │
  │ sub_selector?(W3C)│ │ note, at     │          │ created_at      │
  │ created_at,resolved_at└──────────────┘          └─────────────────┘
  └───────────┘

  ── ONE DOOR (FastAPI, content-negotiated on HX-Request — api_agents.py:337) ──
     POST /api/specs/{slug}/comments              {element_uid, body, author_kind}
     GET  /api/specs/{slug}/elements/{uid}/comments
     POST /api/specs/{slug}/comments/{id}/resolve {resolution}
     POST /api/specs/{slug}/versions              → snapshot + diff + archive prior
     GET  /api/specs/{slug}/versions/{n}/diff     → change_summary
        │
        ├── HX-Request:true  ──► Jinja HTML fragment ──► browser (HTMX swap)
        └── no HX-Request    ──► JSON                ──► agent (FR-013, free)

  ── BROWSER (build-free) ──
     render fn emits <section class="req-el" data-element-id="el_…">…</section>
        │ (vs today's single opaque blob, api_artifacts.py:131)
        ▼
     ~150-line vanilla JS: getSelection → nearest [data-element-id] → "comment" popover
        │ wired on htmx:afterSwap (same hook as EasyMDE, base.html:155)
        ▼
     hx-post comment / hx-post resolve → server fragment swaps margin thread
```

---

## Implementation Steps

> Sequence is deliberate: the API contract is built **before** the UI (FR-013 forcing function), and
> everything gates on Step 2's surrogate landing first.

### Step 1 — Land the three net-new tables keyed to `element_uid`
Create `comments`, `comment_events`, `spec_versions` in `schema.sql` (or programmatically in
`db/connection.py`, matching `agent_error_memories`). Reuse the open/resolved-with-trail shape from
`agent_error_memories.resolution_status` and `goal_suggestions.status`+`resolved_at`. `comments.state ∈
{open,resolved,orphaned}`; `comment_events` is append-only (the retained trail, FR-010). Include
`sub_selector` JSON now (unused) for forward-compat.
**Impact: 9** (every later feature keys off these) · **Effort: S** (raw SQL, established precedents).

### Step 2 — Build the comment API *before any UI* (the FR-013 forcing function)
`comment_service.py` (MVCS, `db_path=` injectable) + routes `POST /api/specs/{slug}/comments`,
`GET …/elements/{uid}/comments`, `POST …/comments/{id}/resolve`. Content-negotiate on `HX-Request`
verbatim from `api_agents.py:337` — JSON for agents, HTML fragment for HTMX. `author_kind` is the *only*
field distinguishing a human from an agent comment. **Write the agent-parity test here**: assert the
same handler returns JSON to a header-less call and HTML to an `HX-Request` call.
**Impact: 10** (this *is* agent parity; build UI-first and it gets rebuilt) · **Effort: M**.

### Step 3 — Emit anchored DOM from the render function
Make the requirements render emit `<section class="req-el" data-element-id="<uid>">` per element. Enable
the `markdown` lib's `attr_list` extension (already present, `api_artifacts.py:6`) or use Step 2's
bespoke element renderer. This is the *one* change to an existing surface (`markdown_viewer.html:27`'s
`{{ html|safe }}`), localized to a single render fn. Carry element IDs in the markdown render as trailing
`<!-- elem:<uid> -->` sentinels so the spec-checker (FR-007) still passes byte-compatibly.
**Impact: 8** (no anchor target exists in the DOM today) · **Effort: S**.

### Step 4 — The ~150-line vanilla-JS comment layer
`window.getSelection()` → walk to nearest `[data-element-id]` → show an "Add comment" popover →
`hx-post` to the comment endpoint → server returns the margin-thread fragment which HTMX swaps. Wire it
on `htmx:afterSwap` (the same hook EasyMDE uses, `base.html:155`). Keep it thin enough to verify via the
existing `tests/ui/` e2e path — no JS unit infra exists, and that's fine.
**Impact: 7** (the human affordance) · **Effort: M**.

### Step 5 — Version snapshot + comment carry-over
`spec_version_service.create_next()`: gate on `count(comments WHERE state='open')` (open ⇒ unconverged);
snapshot current `spec_elements` to a new `version_id`; mark prior `archived`. For each open comment,
re-map via the element's `prev_uid` chain — element still exists ⇒ comment rides along; element deleted
⇒ `state='orphaned'`, surfaced for triage (never silently dropped). Mirror `_rerender_tasks_md`
(`task_service.py:389`) for render-after-mutate; only the *current* version's files land in the goal
folder (FR-011, US5).
**Impact: 9** (the iteration loop core, US4/US5) · **Effort: M**.

### Step 6 — Structural change summary (FR-017)
Diff `spec_elements[v_n]` vs `[v_{n+1}]` by `element_uid`: `added / removed / modified / unchanged` as
set arithmetic. Store as `spec_versions.change_summary` JSON; render "v3: +2 FRs (FR-021, FR-022), 1
modified (US6: +Scenario 5), 0 removed". This is the *same engine* Step 7 reuses for round-trip
provenance — build it reusable. Optional second layer: LLM narrates the deterministic diff into prose;
the diff stays source of truth.
**Impact: 8** (review-as-delta, SC-002; shared with Step 7) · **Effort: M**.

### Step 7 — Archive retrieval with comments intact (US5 Scenario 3)
`GET /api/specs/{slug}/versions/{n}` returns an archived snapshot *with its comments and resolution
state* (the `comment_events` trail makes this free). Confirm path-safety via
`_validate_artifact_path_base` (`api_artifacts.py:20`) on any archive read/write.
**Impact: 6** (history recoverability) · **Effort: S**.

### Step 8 (optional, deferred) — Sub-span anchoring via W3C `TextQuoteSelector`
Only if element-level proves too coarse for wall-of-text elements. Populate `comments.sub_selector` with
a W3C `TextQuoteSelector` (quote + 32-char prefix/suffix). Schema already supports it; **don't build the
fuzzy-match client in v2.** The better fix is finer-grained elements in Step 2.
**Impact: 4** (progressive enhancement) · **Effort: L** (re-imports the anchoring tax — resist).

---

## Key Decisions

| Decision | Verdict | One-line rationale |
|----------|---------|--------------------|
| React/Next.js migration? | **NO** | Forced only by realtime co-editing, which is out of scope; nothing else needs an SPA. |
| Annotation library (RecogitoJS/Hypothesis)? | **NO** | Solves text-anchoring that stable IDs delete; adopting one re-imports fragility. |
| Anchor granularity | **Element-level first** (FK to `element_uid`), sub-span deferred | Requirement element is the legible reviewable unit; matches GitHub-line-comment intuition. |
| Comment keyed to… | **Element, not version** | Open comment auto-carries across versions if its element survives (GitHub re-map). |
| Version semantics | **Immutable element snapshot** | Makes diffs well-defined, archival trivial, audit possible; mutable-in-place can't be diffed. |
| Change summary | **Structural set-diff over surrogates** (LLM optional renderer) | Deterministic, auditable; markdown text-diff is noise. |
| API vs UI build order | **API first, UI as a client** | If the UI writes through a path agents can't call, FR-013 is already violated. |
| "Outdated/orphaned" comment | **First-class state, surfaced for triage** | Never silently lose feedback; doubles as resolution-trail (FR-010). |
| Data-model north star | **W3C Web Annotation** (shape) + **GitHub** (versioning) | Machine-readable + plain REST = "same door" by construction. |
| Storage of old versions | **DB rows; only current version projected to folder** | Owner leans DB; keeps goal dir clean (FR-011), comments travel with archive. |

---

## Pitfalls to Avoid

1. **Building the human UI first, then bolting on an agent API.** This is the v2-vs-v4 split. Build the
   JSON/REST contract first; the HTMX UI is a client of it. The moment the UI has a privileged DB path,
   FR-013 is dead.
2. **Reaching for an annotation library "to be safe."** RecogitoJS/Hypothesis re-introduce fuzzy
   text-anchoring, orphan recovery, and selector cascades — the exact machinery stable IDs eliminate.
   Negative value here.
3. **Anchoring comments to the display label (`FR-001`) instead of the surrogate.** The agent renumbers
   on rewrite and every comment silently re-points to a different requirement. Anchor to `element_uid`.
4. **Letting the LLM generate the diff.** Hallucinated changelogs. The deterministic structural diff is
   truth; the LLM only narrates it.
5. **Embedding-based semantic re-anchoring as the primary anchor.** Non-deterministic, unauditable for a
   source-of-truth doc. Acceptable *only* as a human/agent-confirmed suggestion for orphan re-attach.
6. **Keeping the whole-file-overwrite save (`api_artifacts.py:94`).** Last-write-wins clobbers anchors
   and round-trip write-backs. Move requirements under Step 2's DB-canonical model where "edit" =
   row-mutate + re-render, leaving comments untouched.
7. **Coarse element granularity in Step 2.** Element-level comments are only as precise as the rows are
   fine. Push Step 2 to scenario/clause-level surrogates, or you'll be forced into the sub-span escape
   hatch prematurely.
8. **Gold-plating character-range precision before the loop works.** Ship element-level first; offer
   sub-span as progressive enhancement only if real use demands it.

---

## Success Metrics

- **Agent parity proven (FR-013):** one comment-creation handler returns JSON to a header-less (agent)
  call and an HTML fragment to an `HX-Request` (human) call — verified by a single dual-assertion test.
  An agent can post, resolve, and version with no human-only pathway.
- **Anchor stability (FR-008):** a comment opened on `el_X` in v2 is still attached to `el_X` in v3
  after an unrelated edit, with zero fuzzy matching — and becomes `orphaned` (not lost) if `el_X` is
  deleted.
- **Retained trail (FR-010, US5 S3):** retrieving an archived version returns its comments *and*
  resolution history intact from `comment_events`.
- **Convergence gate (US4 S2):** a spec with any `state='open'` comment reports `unconverged`; producing
  the next version that resolves them flips it to `converged` — a one-line query, observable.
- **Delta review (FR-017, SC-002):** each new version emits a structural change summary
  (`+/−/~ elements`) so reviewers review the delta, not the whole doc.
- **Downstream contract intact (FR-007, SC-004):** `bin/cast-spec-checker` exits 0 on every version
  render; planner/task-suggester run unchanged.
- **No framework added:** `find cast-server -name package.json` stays empty; the comment layer remains a
  thin vanilla-JS file verifiable through `tests/ui/`.

---

## Impact Rating

**9 / 10** — This is the iteration engine (US4/US5) and a load-bearing input to Step 7's round-trip; it
turns requirements from a static snapshot into a converging, reviewable, agent-participable artifact —
and it does so on the existing stack at near-greenfield-low risk by composing patterns already proven in
the repo (content-negotiated API, open/resolved-with-trail, render-after-mutate). Held back from 10 only
because it cannot ship until Step 2's stable-element-identity keystone lands, and its precision ceiling
is capped by how fine-grained those surrogates are.
