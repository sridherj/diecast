# Refine Requirements v2: Phase 4 — Iteration: Annotation & Versioning Engine

## Overview

Phase 4 builds the iteration loop: reviewers (human **or** agent, through the *same* API door)
leave comments anchored to a **stored quote** on the HTML render; open comments mark the spec
**unconverged** and drive new versions; each new version yields a **deterministic block-level
change summary** (the reusable diff engine Phase 5 adopts verbatim); only the current version
lives in the goal folder, older versions archived in the DB **with their comments and resolution
state intact**. The key insight carried from plan review: the only deterministic machinery is the
places where being wrong means silent data loss — comment rows exist, version snapshots, and the
structural change *set* — everything placement-related is a Claude subagent re-locating comments
by their stored quote, with orphaning always surfaced, never silent (decisions #1, #9).

The UX is **LOCKED** from the Phase-0 spike sign-off (owner, 2026-06-11): select text → 💬 pill →
inline composer (below-default, flip-up-when-cramped), `<mark>` highlight, open/resolved state
(decision #7); version toggle revealing a "What changed" panel + inline tracked-changes
green/amber/red (decision #8). Implementation is vanilla JS over the existing Jinja+HTMX stack —
**no framework, no annotation library** (`find cast-server -name package.json` stays empty).

This plan covers ONLY Phase 4 of `goals/refine-requirements-v2/plan.collab.md` and adopts all
prior canon from `docs/plan/refine-requirements-v2-decisions-so-far.md`.

## Position in Overall Plan

```
Phase 1: Parser & Thin Spine ──► Phase 2: Classification ──► Phase 3a: HTML Render ──► Phase 4 (THIS PLAN)
   (requirement_versions/_comments/                              (selectable DOM,            │
    comment_events tables, content_hash,                          quote + nearest-heading    ▼
    requirement_version_service,                                  capture surface)       Phase 5: Round-Trip
    ParsedRequirements block model)                                                  (reuses block_diff engine,
                                                                                      versioning, same-door API,
Phase 3b: Router — independent of this plan (no shared surface)                       comment_events trail)
```

Phase 4 is ON the critical path: Phase 5 consumes its diff engine, versioning gate, same-door API
pattern, and append-only trail. The **`block_diff` module interface below is the key cross-phase
contract** — Phase 5 must import it, never reimplement it.

## Depends On (from prior plans)

| Prior deliverable | Where | How Phase 4 consumes it |
|---|---|---|
| `requirement_comments` table: `{goal_slug, version, quoted_text, section_hint, body, state(open/resolved/orphaned), author, author_kind(human/agent)}` — **NO anchor column** | Phase 1 schema (canonical DDL in `cast-server/cast_server/db/schema.sql` + `_run_migrations()`) | `comment_service` CRUD target; `author_kind` is the ONLY human/agent distinction (FR-013) |
| `comment_events` append-only table (`created/resolved/reopened/orphaned/relocated`) | Phase 1 schema | Every state transition writes an event; US5 S3 as-of reconstruction reads it |
| `requirement_versions` (+ `UNIQUE(goal_slug, version)`, `status current/archived`) | Phase 1 schema | `create_next()` builds on it |
| `requirement_version_service.create_snapshot / get_current / get_version / list_versions` (idempotent by hash, single txn, `BEGIN IMMEDIATE` fix-forward note) | Phase 1 `services/requirement_version_service.py` | `create_next()` wraps `create_snapshot` and adds the comment-aware behavior |
| `content_hash(text)` | Phase 1 `requirements_render/hashing.py` | Staleness/displacement checks; never reimplemented |
| `ParsedRequirements` / `Block{kind, level, body, heading, ref, line_start, line_end}` (`ref` in-memory only) | Phase 1 `requirements_render/blocks.py` | The diff engine's input — `diff_blocks` matches by heading token + content, using `ref`/`heading` **in memory only** |
| Service DB pattern: flat functions, `db_path: Path | None = None` + `get_connection(db_path)` (model: `goal_service.py`/`task_service.py`) | Phase 1 plan-review #1 | `comment_service.py` inherits this exact shape |
| Selectable-DOM contract: every block one contiguous text-selectable unit under a real heading; **zero `id=`, zero `data-block-anchor`** on requirement sections | Phase 3a Naming Contract + WP-G spec | The JS layer captures quote + nearest heading from this DOM; there is nothing else to capture |
| `document.html.j2` + `_theme.css.j2` (standalone document, token-pinned, golden-snapshotted; `[PENDING Phase 4]` comment-count slot on the Goal Card) | Phase 3a WP-A/C | Phase 4 edits the template (toggle, tray, script tags) and fills the Goal Card slot client-side; goldens regenerate via `UPDATE_GOLDENS=1` |
| `GET /goals/{slug}/render` route + `rerender_requirements_html()` lazy regen | Phase 3a WP-E | The comment layer rides this page; the diff view adds a sibling route |
| `HX-Request` content negotiation precedent | `cast_server/routes/api_agents.py:325-345` (`list_runs`) | The exact pattern for every negotiated comment/version handler |
| Subagent-mode agent shape: `config.yaml` `model: sonnet, dispatch_mode: subagent, interactive: false, context_mode: lightweight, timeout_minutes: 10`; bare-JSON verdict, outside the delegation contract | Phase 2 classifier / Phase 3a checker precedent | `cast-comment-reanchor` clones this shape |
| Eval-harness convention: `tests/eval_*.py` excluded from default CI discovery | Phase 2 `eval_classifier_corpus.py` / Phase 3a `eval_render_checker.py` | `tests/eval_reanchor.py` validates the re-anchor agent during build (decision #9) |
| Frozen fixture `tests/fixtures/refine_requirements_v2/refined_requirements.collab.md` | Phase 1 | Base text for diff/displacement fixtures (edited variants checked in beside it) |

**Sequencing note:** fan-out planning — Phases 1/2/3a are planned, not yet executed. If their
implementations land with drifted names, adopt the *landed* names; do not fork the vocabulary.

## Operating Mode

**HOLD SCOPE** — the surface was locked at plan review (owner, 2026-06-11): "Commenting UX =
LOCKED", "Version-diff UX = LOCKED", "~150-line vanilla-JS comment layer … No React, no annotation
library", "no privileged UI write path", "the structural diff is the source of truth; a Claude
subagent may *narrate* it but never *invent* it". This plan's job is rigorous adherence: no extra
comment features (no threads-of-threads, no mentions, no realtime), no diff bells (no word-level
diff, no three-pane merge), no notification surface beyond in-page (the unified `needs_attention`
badge is Phase 5's, decision #4). Every activity traces to the Phase 4 section of `plan.collab.md`
or a locked decision.

## Decisions Made This Session (owner, 2026-06-11, interactive)

1. **Re-anchor-on-save = lazy + surfaced tray.** A human textarea save is a plain server PUT with
   no Claude in the loop, so the subagent cannot run synchronously. Resolution: displacement is a
   **derived, read-time property** — an open comment whose `quoted_text` is found verbatim in the
   current file needs nothing (placement is a trivial string-find; no LLM); one whose quote is NOT
   found shows in a visible **"needs re-anchor" tray** on the render (derived state — never stored,
   no schema change). The re-anchor subagent runs at the next agent touchpoint —
   `create_next()` during the refinement loop, which is when versions actually change. The save
   handler itself gains **zero** new machinery. This is *not* a deterministic anchoring engine
   (decision #1 intact): the string-find only detects *whether* re-location is needed; all
   re-location is the subagent's.
2. **Re-anchor capability = a new 4th agent, `cast-comment-reanchor`.** Standalone subagent-mode
   agent whose only job is relocated/orphaned verdicts. Phase 5's writeback reuses the
   locate-text-by-quote *prompt technique*, not the agent. Deviates from plan.collab.md decision
   #6's "three small first-class agents" count — flagged under Suggested Revisions.

## Naming Contract (Phase 4 sets these; Phase 5 MUST adopt)

- **Diff engine (THE cross-phase contract):** `cast_server.requirements_render.block_diff` —
  ```python
  def diff_blocks(old: ParsedRequirements, new: ParsedRequirements) -> BlockDiff: ...

  @dataclass(frozen=True)
  class BlockDiff:
      added: tuple[Block, ...]          # in new, no match in old
      removed: tuple[Block, ...]        # in old, no match in new
      modified: tuple[ModifiedBlock, ...]  # matched by key, body differs
      unchanged: tuple[ModifiedBlock, ...] # matched, body identical (moves land here)

  @dataclass(frozen=True)
  class ModifiedBlock:
      old: Block
      new: Block
  ```
  Pure function: no I/O, no DB, no LLM, deterministic. **Partition invariant:** every old block
  appears exactly once across `removed ∪ modified.old ∪ unchanged.old`; every new block exactly
  once across `added ∪ modified.new ∪ unchanged.new`. Lives in the `requirements_render` package
  (importable without FastAPI) so Phase 5 imports the SAME engine for provenance-badged summaries.
  Match algorithm (document-order tie-break, two passes): (1) normalized-body equality →
  `unchanged` (a pure move is unchanged — set arithmetic has no "moved"); (2) key equality with
  differing body → `modified`, where key = the heading token for level-2 blocks (the in-memory
  `ref` like `FR-007`/`US1` when present, else full `heading` text) and `kind` for level-1 blocks;
  duplicate keys pair in document order. Remainders → `added`/`removed`.
- **Diff summary:** `block_diff.summarize(diff: BlockDiff) -> dict` — counts + per-item
  `{change, kind, heading_or_ref, excerpt}` rows, the JSON the `/changes` endpoint and the
  "What changed" panel both render from. The subagent may narrate this dict into prose downstream;
  it never produces the dict.
- **Diff view renderer:** `cast_server.requirements_render.diff_render.render_diff(old, new,
  *, base_version: int, head_version: int) -> RenderResult` — same `RenderResult` shape as Phase
  3a's renderer; deterministic; reuses `document.html.j2` theme.
- **Comment service:** `cast_server.services.comment_service` — flat functions, house DB pattern:
  `create_comment(goal_slug, quoted_text, section_hint, body, author, author_kind, *, version=None,
  db_path=None) -> dict` (defaults `version` to the current snapshot, 0 if none) ·
  `list_comments(goal_slug, *, state=None, db_path=None) -> list[dict]` · `get_comment(comment_id)`
  · `resolve_comment(comment_id, actor)` · `reopen_comment(comment_id, actor)` ·
  `relocate_comment(comment_id, new_quoted_text, new_section_hint, actor)` ·
  `orphan_comment(comment_id, actor)` · `open_comment_count(goal_slug) -> int` ·
  `get_comment_events(comment_id) -> list[dict]`. Every transition writes its `comment_events` row
  in the same transaction as the state change.
- **Version gate:** `requirement_version_service.create_next(goal_slug, content, created_by, *,
  db_path=None) -> dict` returning `{version: dict, convergence: "converged"|"unconverged",
  open_comments: list[dict], displaced_comment_ids: list[int]}` — `displaced_comment_ids` = open
  comments whose `quoted_text` is not a verbatim substring of `content` (the deterministic
  needs-LLM detector; the seam the agent loop dispatches `cast-comment-reanchor` over).
- **API router:** `cast_server/routes/api_requirements.py`, prefix
  `/api/goals/{goal_slug}/requirements`:
  - `GET  /comments` (`?state=`) — negotiated: JSON list (each comment carries derived
    `displaced: bool` vs the current file) | HTML comment-tray fragment
  - `POST /comments` — negotiated: JSON 201 | HTML thread-item fragment. **The canonical
    dual-assertion agent-parity handler.**
  - `POST /comments/{comment_id}/resolve` · `/reopen` · `/orphan` — negotiated
  - `POST /comments/{comment_id}/relocate` (body: `new_quoted_text`, `new_section_hint`) —
    server-side validation: `new_quoted_text` MUST be a verbatim substring of the current file,
    else 422 (the deterministic backstop on subagent output)
  - `GET  /versions` — JSON list + `{convergence, open_comment_count}` metadata
  - `GET  /versions/{n}` — version row **with** its comments and as-of resolution state (US5 S3)
  - `POST /versions` — `create_next()` from the current goal file; returns the contract dict above
  - `GET  /changes?base=N&head=M` (default: head = current, base = head−1) — negotiated:
    `summarize()` JSON | "What changed" panel fragment (FR-017's API surface)
- **Diff page route:** `GET /goals/{slug}/render/diff?base=N&head=M` in `routes/pages.py` — the
  tracked-changes view (decision #8). The render page's toggle targets it.
- **Comment layer JS:** `cast_server/static/requirements_comments.js` (~150-line budget, vanilla;
  htmx for transport). Fragment templates under
  `cast_server/templates/fragments/requirements_comments/` (`tray.html`, `thread_item.html`,
  `composer.html`).
- **Re-anchor agent:** `agents/cast-comment-reanchor/` (`cast-comment-reanchor.md` +
  `config.yaml`: `model: sonnet`, `dispatch_mode: subagent`, `interactive: false`,
  `context_mode: lightweight`, `timeout_minutes: 10`). **Verdict schema (canonical):**
  `{verdicts: [{comment_id: int, verdict: "relocated"|"orphaned", new_quoted_text: str|null,
  new_section_hint: str|null, confidence: float, reasoning: str}]}` — EXACTLY ONE bare JSON
  object, no prose, no fences; outside `cast-delegation-contract.collab.md` (classifier/checker
  carve-out — do not "fix" it into an output envelope).
- **Convergence rule (the one sentence):** a goal's requirements are `unconverged` iff
  `open_comment_count(goal_slug) > 0`. Derived, never stored.

## Sub-phase: Phase 4 — Annotation & Versioning Engine

**Outcome:** On `GET /goals/{slug}/render`, a reviewer selects text → 💬 pill → inline composer →
the comment persists with quote + section hint + open state and renders as a `<mark>` highlight;
an agent creates the identical comment via a header-less `POST /comments` (JSON both ways,
`author_kind` the only distinction). Open comments mark the spec unconverged (Goal Card chip);
`create_next()` snapshots a new version, archives the prior, carries open comments forward, and
names exactly which comments need re-anchoring; the `cast-comment-reanchor` subagent's verdicts
apply through the same API door, with unfindable quotes becoming `orphaned` — surfaced in the
tray, never lost. The version toggle reveals the What-changed panel + green/amber/red inline
tracked-changes, both driven by the deterministic `block_diff` engine. Archived versions return
with their comments and as-of resolution state. No `package.json` exists anywhere under
`cast-server/`.

**Dependencies:** Phase 1 (thin spine schema, version service, parser, hashing) + Phase 3a
(selectable DOM, render route, document template). Phase 2/3b: none (the diff engine matches on
parser blocks, not recipes).

**Estimated effort:** 4 sessions (A ≈ 1, B ≈ 1, C ≈ 0.5, D ≈ 1, E ≈ 1, F+G ≈ 0.5 — D and E
parallelizable; the high-level plan's 3-4 band holds if D's eval iteration goes quickly).

**Verification (phase gate):**
- `pytest tests/test_requirements_comments_api.py` — **the dual-assertion agent-parity test
  (FR-013):** one `POST /comments` handler returns JSON 201 to a header-less call and an HTML
  thread-item fragment to an `HX-Request: true` call, with the SAME DB row written either way and
  `author_kind` the only differing input, never a differing code path. Parametrized lighter
  assertions over `resolve`/`reopen`/`orphan`/`relocate`/`GET comments`/`GET changes`. Plus:
  `relocate` with a `new_quoted_text` absent from the current file → 422, no row change; unknown
  slug → 404; empty `quoted_text`/`body` → 422.
- `pytest tests/test_comment_service.py` — CRUD + every transition writes its `comment_events`
  row in-transaction; `open_comment_count`; state machine (resolve→reopen round-trip; orphaned
  comments excluded from displacement checks).
- `pytest tests/test_block_diff.py` — partition invariant (every block exactly once per side);
  added/removed/modified/unchanged cases; a pure move lands in `unchanged`; duplicate headings
  pair in document order; `summarize()` counts match set sizes; determinism (same inputs →
  identical output). Fixture: the frozen Phase 1 fixture vs a checked-in edited variant
  (`refined_requirements.v2-edit.collab.md`) with one added FR, one reworded FR, one deleted
  Out-of-Scope bullet, one moved section.
- `pytest tests/test_requirement_versions.py` (extended) — `create_next()`: new `current` row +
  prior flipped `archived` in one txn; `convergence` flips on open-comment count; open comments
  carry forward (still open, still listed after the bump); `displaced_comment_ids` exactly the
  comments whose quotes were edited away in the fixture variant; identical-content call remains
  idempotent (Phase 1 behavior preserved).
- `pytest tests/test_archive_retrieval.py` — US5 S3: `GET /versions/{n}` on an archived version
  returns its content + the comments left against it with resolution state **as of that version's
  archival**, reconstructed from `comment_events` timestamps; goal folder contains ONLY
  `refined_requirements.collab.md` + `refined_requirements.html` after three version bumps
  (FR-011 — no version-suffixed files ever appear).
- `pytest tests/test_diff_render.py` — tracked-changes goldens for the fixture pair
  (`tests/golden/requirements_render/diff_v1_v2.html`, `UPDATE_GOLDENS=1` regen); structural
  assertions: every `added` block carries `diff-added`, `modified` shows new body + `<del>` prior,
  `removed` renders struck in old-section position; panel counts == `summarize()` counts; panel
  items link to transient `id="diff-{n}"` anchors that exist in the emitted HTML.
- `pytest tests/test_fr007_readonly_guard.py` (extended) — comment CRUD + `create_next()` +
  `render_diff()` leave the fixture `.collab.md` bytes identical; `bin/cast-spec-checker` exit 0.
- `pytest tests/test_no_frontend_framework.py` — `find cast-server -name package.json` (rglob)
  returns nothing; `requirements_comments.js` contains no `import`/`require` of any framework.
- `tests/eval_reanchor.py` (manual/slow, excluded from default CI — `eval_` prefix): dispatch
  `cast-comment-reanchor` over the fixture pair; **gate (decision #9 validated-during-build):**
  the reworded-quote comment → `relocated` with a verbatim-present `new_quoted_text`; the
  deleted-content comment → `orphaned`; zero verdicts inventing text. Run before declaring the
  phase done; tune the prompt on failures (trust + iterate).
- e2e UI harness (`cast-server/tests/ui/`) — per `cast-ui-testing.collab.md` US2: select → pill →
  composer → comment appears with `<mark>`; resolve from the thread; toggle → diff view renders;
  tray shows a displaced comment after an editor save that rewords its quote.
- Manual demo (the SC-002 dry run): leave a comment on this goal's own render, produce a version,
  watch it carry forward.

### Work Package A — Comment service + same-door API (BEFORE ANY UI — the FR-013 forcing function)

- `services/comment_service.py` per the Naming Contract — flat functions, `db_path` injectable,
  `get_connection(db_path)` (model: `goal_service.py`; Phase 1 plan-review #1 canon). Each write
  is one transaction: row change + its `comment_events` append (`created`/`resolved`/`reopened`/
  `orphaned`/`relocated` — the Phase 1 enum, no additions). `relocate_comment` stores the old
  quote in the event `payload` JSON (the audit trail of where the comment used to live).
- Derived displacement: `list_comments` accepts the current file text (or reads it via the goal
  dir) and stamps each open comment `displaced: quoted_text not in current_text`. Orphaned and
  resolved comments are never displacement-checked. **This string-find is a detector, not an
  anchoring engine** — decision #1's deletion of heading-path/ordinal anchors stands; nothing
  positional is ever stored.
- `routes/api_requirements.py` per the Naming Contract. Content negotiation copies
  `api_agents.list_runs` exactly: `request.headers.get("HX-Request")` → fragment via
  `templates.TemplateResponse`, else `JSONResponse`. Slug validated via `goal_service.get_goal()`
  first — unknown → 404 (the Phase 3a path-traversal rule, applied to every endpoint here).
- `author`/`author_kind` come from the request body; `author_kind` defaults `human` (the UI
  composer sends nothing special; agents send `"agent"`). **No privileged UI write path** — the
  composer's hx-post hits the identical endpoint an agent curls.
- Register the router in the app factory beside the existing `api_*` routers.

**Design review (WP-A):** Architecture — mirrors service→route→fragment house pattern ✓; naming
`comment_service`/`api_requirements` follows `{entity}_{layer}` ✓. Error & rescue — resolve on an
already-resolved comment is a 409 (not a silent no-op — state machine violations announce
themselves); relocate-validation failure is 422 with the offending quote echoed; DB row + event
commit atomically (no event-less transitions). Security — slug→404 gate on every route; comment
`body`/`quoted_text` rendered through Jinja autoescape (no raw HTML injection via a malicious
quote); size cap on `quoted_text`/`body` (e.g. 10 KB) → 422.

### Work Package B — `block_diff` engine + diff render + What-changed panel (the Phase 5 contract)

- `requirements_render/block_diff.py` per the Naming Contract — the match algorithm, partition
  invariant, and `summarize()` exactly as specified. Module docstring states: **"Phase 5 imports
  this engine for round-trip change summaries — extend, never fork. The change SET is
  deterministic; LLM narration consumes `summarize()` output and never invents entries"**
  (decision #8's no-invention rule, pinned where Phase 5 will read it).
- `requirements_render/diff_render.py` — `render_diff(old, new, *, base_version, head_version)`:
  parse both snapshots, `diff_blocks`, render the head document's order as the spine with
  per-block treatment: `diff-added` (green accent), `diff-modified` (amber; new body shown,
  prior body as `<del>` inside a closed `<details>`), removed blocks struck red, attached after
  the last surviving block of their old H2 section (whole-section removals render as one struck
  section at the old relative position). The "What changed" panel renders first:
  `+N added · ~N modified · −N removed`, each item a link to a **transient** `id="diff-{n}"`
  anchor. These ids exist ONLY in the diff view — generated per render, never stored, never
  comment anchors; the canonical render's zero-`id` contract (Phase 3a structural test) is
  untouched. Diff-view CSS additions go in `_theme.css.j2` using `var(--color-*)` tokens only.
- The diff view is **comment-free and read-only** (comments live on the current render; HOLD
  SCOPE — no commenting on history).
- `GET /goals/{slug}/render/diff` in `pages.py`: validate slug → 404; fewer than 2 versions →
  200 with a plain "no prior version to compare" card; else `render_diff` over
  `get_version(base)`/`get_version(head)` snapshots, served fresh each request (derived, never
  written to the goal folder — only the canonical render is a file artifact).
- `GET …/requirements/changes` (WP-A router): `summarize()` JSON | panel fragment — FR-017's
  same-door surface; agents read the change set exactly as the panel does.
- Version toggle on the render page (`document.html.j2`): `Current (vN)` / `Changes since
  v(N−1)` pinned beside the Goal Card version chip; the diff option renders only when ≥2 versions
  exist; it is a plain link to `/goals/{slug}/render/diff` (no swap machinery on a standalone
  document — keep the page simple). Goldens regenerate.

**Design review (WP-B):** Spec consistency — decision #8's "deterministic change SET, subagent may
narrate not invent" is enforced structurally: no LLM call exists anywhere in `block_diff`/
`diff_render` (pin with a no-import test like Phase 3b's router source pin). Architecture — both
modules pure over `ParsedRequirements`, in the FastAPI-free package, exactly where Phase 5 can
import them ✓. Error & rescue — unparseable archived snapshot (pre-parser content) → diff page
shows "cannot diff this pair" card + warning, never a 500; `base >= head` → 422. Naming — the
transient-`id` exception to the no-`id` rule is documented in the module docstring AND the spec
update (WP-G) so it never leaks into the canonical render.

### Work Package C — `create_next()` + carry-forward + convergence + archive retrieval

- Extend `services/requirement_version_service.py` with `create_next()` per the Naming Contract:
  wraps Phase 1's `create_snapshot` (inheriting hash idempotency + the txn discipline, including
  the documented `BEGIN IMMEDIATE` fix-forward); after snapshotting, computes `convergence` from
  `open_comment_count`, returns open comments and `displaced_comment_ids` (verbatim string-find
  of each open comment's quote against the new content). **Open comments carry forward by doing
  nothing:** rows keep their original `version` (provenance of where they were left); "current"
  open comments are simply `state='open'` regardless of version — no row copying, no remapping.
- "Gating" semantics, stated precisely: `create_next()` never *refuses* on open comments — open
  comments are what *drive* new versions (US4 S2). The gate is the **convergence signal**: any
  open comment ⇒ `unconverged`; the next version that resolves them flips the report to
  `converged`. The dict return makes the agent loop's next move (dispatch re-anchor for the
  displaced list) explicit rather than implied.
- `POST …/requirements/versions` (WP-A router): reads the goal's current
  `refined_requirements.collab.md` (read-only — the server snapshots INTO the DB; the delegation
  contract's no-artifact-writes rule is untouched), calls `create_next()`, returns the contract
  dict. Missing file → 409 "nothing to snapshot".
- Archive retrieval (US5 S3): `GET …/versions/{n}` joins the version row with comments where
  `version <= n`, each with state **as of** that version's supersession time (the next version's
  `created_at`, or now for current) reconstructed by replaying `comment_events` up to that
  instant — the trail makes this a query, not a feature. FR-011 stays structural: versions are
  rows; the goal folder never gains a second requirements file.

**Design review (WP-C):** Architecture — `create_next` lives in the version service (it is a
version operation that *reads* comments via `comment_service`, one-directional import, no cycle) ✓.
Error & rescue — snapshot + archive-flip remain one transaction (Phase 1 discipline); a crash
between snapshot and the caller's re-anchor dispatch loses nothing (displacement is derived —
the next `GET /comments` recomputes it). Spec consistency — FR-011 verified by the folder-content
assertion, not convention.

### Work Package D — `cast-comment-reanchor` agent + verdict application + eval

- Create `agents/cast-comment-reanchor/cast-comment-reanchor.md` + `config.yaml` per the Naming
  Contract (clone the checker/classifier shape). **Input** (delegation context from the parent):
  the displaced open comments `{id, quoted_text, section_hint, body}`, the old version content,
  the new current content. **Task:** for each comment, find where its commented-on content now
  lives in the new text; return `relocated` with `new_quoted_text` = a **verbatim substring of
  the new document** covering that content + the new nearest heading as `new_section_hint`; if
  the content is genuinely gone, return `orphaned`. Never paraphrase, never invent text, prefer
  `orphaned` over a low-confidence guess (orphaning is surfaced and recoverable; a silent
  mis-placement is not — decision #9's asymmetry, stated in the prompt). **Output:** EXACTLY ONE
  bare JSON object (verdict schema above).
- **Deterministic backstop:** verdicts are applied by the parent through the same-door API —
  `POST /comments/{id}/relocate` validates `new_quoted_text` verbatim-present (422 otherwise) and
  `POST /comments/{id}/orphan` for the rest. A relocate rejection downgrades that verdict to
  orphan (applied by the parent; the comment surfaces in the tray either way — zero silent loss,
  zero invented anchors). Every application lands a `comment_events` row, `author_kind='agent'`.
- **Loop choreography (lean prompt wiring):** add a short "Iteration mode" section (~25 lines,
  API-driven) to `agents/cast-refine-requirements/cast-refine-requirements.md`: when the goal has
  open comments (`GET /comments?state=open`), address them in the new draft, write the
  `.collab.md`, `POST /versions`, dispatch `cast-comment-reanchor` (Agent tool — subagent mode)
  over `displaced_comment_ids`, apply verdicts via relocate/orphan, then resolve the comments the
  new draft addressed (`POST /resolve`) with a body-note pointing at the change. Add
  `cast-comment-reanchor` to its `config.yaml` `allowed_delegations`. Re-run `bin/generate-skills`.
  ⚠️ The ~650-line prompt ceiling (Phase 1b) is already under pressure — if the section doesn't
  fit, move the choreography to a referenced skill doc (the `cast-child-delegation` pattern) and
  keep only the trigger line in the prompt; flag the overage rather than silently trimming 1b/2
  content.
- `tests/eval_reanchor.py` per Verification — the decision-#9 validate-during-build artifact.
  Fixture pair: the frozen fixture + `refined_requirements.v2-edit.collab.md` (reworded FR,
  deleted bullet, moved section) with three pre-seeded comments (one per case).
- After creating the agent: `bin/generate-skills`, then → Delegate: `/cast-agent-compliance`
  (consult `/cast-agent-design-guide`) — validate `config.yaml` fields + the subagent bare-JSON
  carve-out against fleet canon (Phase 3a plan-review #2 precedent). Review output: config keys
  match the Naming Contract exactly.

**Design review (WP-D):** Spec consistency — subagent-mode + bare JSON is the established
classifier/checker carve-out from `cast-delegation-contract.collab.md`; restated in the WP-G spec
update so nobody wraps it in an output envelope. Error & rescue — subagent failure/timeout/garbage
JSON ⇒ parent applies NO verdicts; displaced comments simply stay in the tray (derived state
degrades gracefully; nothing is lost, the next cycle retries). Architecture — the agent never
touches the DB or files; it returns text, the parent writes through the API (same door, FR-013) ✓.
Security — the verdict path cannot write arbitrary state: relocate is substring-validated, orphan
is the only other transition exposed.

### Work Package E — Vanilla-JS comment layer (the locked UX, decision #7)

- `static/requirements_comments.js` (~150-line budget, vanilla, htmx transport), loaded by
  `document.html.j2` via `<script src="/static/htmx.min.js">` + `<script
  src="/static/requirements_comments.js" defer>`. **Progressive enhancement:** opened as a bare
  file from the goal folder, the scripts 404 and the document remains a perfectly readable render
  (the Phase 3a self-contained property degrades to read-only, documented in WP-G). On
  `DOMContentLoaded`: `GET /api/goals/{slug}/requirements/comments` (slug read from a
  `data-goal-slug` attribute on `<body>` — page chrome data, not a block anchor); for each open
  non-displaced comment, locate `quoted_text` in the rendered text (TreeWalker over text nodes
  within requirement sections; quotes are contiguous per the Phase 3a DOM contract), wrap in
  `<mark class="comment-mark" data-comment-id="{id}">`. Displaced + orphaned comments render in
  the **tray** (server fragment `tray.html`, fetched via the negotiated GET): quote + hint + body
  + state, with resolve/reopen buttons — "needs re-anchor" for displaced, "orphaned — triage"
  for orphaned (decision #9: always surfaced).
- Selection flow: `mouseup` within the document container → non-empty selection → float the
  "💬 Comment" pill at the selection rect; click → inline composer (fragment `composer.html`
  fetched or cloned from a `<template>`) anchored below the selection, flipped above when the
  viewport bottom is cramped (the locked GitHub/Docs behavior); composer captures
  `quoted_text = selection.toString()` + `section_hint` = nearest preceding `h2/h3` text (walk up
  /back from the range start — the DOM contract guarantees real heading elements); submit =
  `hx-post` to `POST /comments` → thread-item fragment swaps in beside the new `<mark>`.
  Escape/blur dismisses. Re-bind marks + handlers on `htmx:afterSwap` (resolve/reopen swaps).
- Goal Card wiring: fill Phase 3a's `[PENDING Phase 4]` slot client-side — open-comment count +
  convergence chip (`unconverged · 3 open` / `converged`) from the comments payload. The baked
  HTML stays comment-agnostic (comments must never force a re-render; the artifact's
  `source-hash` staleness model is content-only).
- Click an existing `<mark>` → thread popover: body, author + `author_kind` badge, events trail
  (fetched lazily), resolve button. Resolved comments lose their `<mark>` (no highlight noise);
  they remain in the tray's "resolved" collapse.
- CSS: `.comment-mark`, `.comment-pill`, `.comment-composer`, `.comment-tray` in `_theme.css.j2`
  — tokens only, never hex (FR-012 pin already enforced by the Phase 3a hex-scan test).
- **No framework, no annotation library** — the pin test (Verification) plus the line budget keep
  this honest. If the layer genuinely cannot fit ~150 lines + htmx, that is escalation evidence
  (per the Phase-0 Spike C protocol), not license to add a dependency.

**Design review (WP-E):** Spec consistency — `cast-ui-testing.collab.md` US2 mandates harness
updates for this UI (covered in WP-G; the flag below). Error & rescue — comment POST failure →
composer shows the error inline, selection preserved (no lost draft); marks that fail to locate
(race between load and an edit) degrade to the tray on next refresh — the displaced path catches
them. Security — all comment content enters the DOM via server-rendered autoescaped fragments,
never `innerHTML` of raw API strings (the JS inserts fragments the server built). A11y — pill and
composer are keyboard-reachable (`tabindex`, Enter-to-comment); `<mark>` carries
`title="{author}: {body excerpt}"`.

### Work Package F — Human-edit path + guards (the lazy decision, this session's #1)

- **The save handler changes not at all.** `api_artifacts.save_artifact` already writes the
  `.collab.md`; displacement is derived at read time (WP-A), and the render route's existing
  lazy-regen picks up the new content hash on next view. The "re-anchor on save" promise is
  fulfilled by: save → next render shows displaced comments in the tray → next agent cycle
  (`create_next`) dispatches the subagent. Document this resolution in the WP-G spec (it
  reinterprets plan.collab.md's "on save, the re-anchor subagent re-locates" into the lazy model
  the owner chose this session).
- Extend `tests/test_fr007_readonly_guard.py` per Verification — every Phase 4 operation
  (comment CRUD, `create_next`, `render_diff`) leaves the `.collab.md` bytes identical; checker
  exit 0.
- `tests/test_no_frontend_framework.py` per Verification — the `package.json` absence pin.

**Design review (WP-F):** no flags — this WP deliberately adds nothing; the review point is that
zero save-path machinery is the *designed* outcome, not an omission (recorded in the spec).

### Work Package G — Spec lockstep + e2e harness + compliance

- → Delegate: `/cast-update-spec` (update mode) — extend Phase 3a's
  `docs/specs/cast-requirements-render.collab.md` (created in 3a WP-G; if it hasn't landed yet,
  create mode covering both phases' surface) with: the comment API contract (endpoints,
  negotiation rule, author_kind semantics, the 409/422 state-machine errors), the versions +
  changes endpoints, `create_next()` semantics + the convergence rule, the diff-view route + the
  transient-`id` exception, the tray/displaced derived-state model (this session's decision #1),
  the `cast-comment-reanchor` I/O contract + carve-out, and the FR-011 folder invariant. Bump
  registry row. Review output: names must match this plan's Naming Contract exactly (Phase 5
  will cite it).
- → Delegate: e2e harness update per `cast-ui-testing.collab.md` US2 — extend
  `cast-server/tests/ui/` with the render-page comment flows (Verification list). Review output:
  selectors target the classes this plan names (`.comment-pill`, `.comment-mark`, `.comment-tray`).
- `/cast-agent-compliance` run for `cast-comment-reanchor` (WP-D) and the
  `allowed_delegations` addition to `cast-refine-requirements` (the sp3c allow-list audit
  footgun).

**Design review (WP-G):** Spec consistency — this is the phase's spec-debt settlement; the only
new spec *file* decision is reuse-vs-create depending on 3a's landing order (stated above, no
fork either way).

## Build Order

```
WP-A (service + same-door API) ──┬──► WP-C (create_next + archive) ──► WP-D (reanchor agent + loop + eval)
                                 ├──► WP-E (JS comment layer + tray)
WP-B (block_diff + diff view,    │
      independent — pure over    ┴──► WP-F (guards — after A/B/C land)
      Phase 1 parser)                 WP-G (spec + e2e + compliance — last, after interfaces settle)
```

**Critical path:** WP-A → WP-C → WP-D (the agent loop end-to-end). WP-B is fully parallel from
day one (pure functions over the Phase 1 parser). WP-E parallels WP-C/D after WP-A. The
**API-before-UI ordering inside this phase is the FR-013 forcing function — do not start WP-E
before WP-A's dual-assertion test is green.**

## Design Review Flags

| Item | Flag | Action |
|---|---|---|
| `cast-ui-testing.collab.md` US2 | Phase 4 ships new interactive UI on the render screen — harness update is **mandatory**, not optional | e2e flows in WP-G; PR pairing rule applies |
| Transient `id="diff-{n}"` in the diff view | Looks like drift from the zero-`id` thin-spine contract | Scoped to the derived diff view only; never stored, never a comment anchor; documented in module docstring + spec update; Phase 3a's structural test (canonical render) untouched |
| Phase 3a "self-contained artifact" property | Phase 4 adds `<script src>` tags — file:// viewing loses the comment layer | Progressive enhancement (document still reads perfectly); recorded in spec update; goldens regenerate |
| plan.collab.md "re-anchor on save" wording | Owner re-resolved to lazy + surfaced tray this session | Spec update records the lazy model; Suggested Revision #1 below |
| plan.collab.md decision #6 "three new agents" | Phase 4 adds a 4th (`cast-comment-reanchor`) | Owner-approved this session; Suggested Revision #2 below |
| `cast-refine-requirements` ~650-line prompt ceiling | The iteration-mode section competes with Phase 1b/2 claims | Lean ~25-line section; overflow → referenced skill doc, never silent trimming |
| Comment body/quote into DOM | XSS via crafted comment | Server-rendered autoescaped fragments only; size caps; no client `innerHTML` of raw strings |
| State-machine writes | Silent no-ops hide bugs | Resolve-on-resolved → 409; relocate failing verbatim check → 422; every transition events-logged in-txn |

## Suggested Revisions to Prior Sub-Phases

1. **plan.collab.md Phase 4 bullet (owner annotation, not a plan change):** "Keep the editable
   textarea + re-anchor on save" is implemented as **lazy + surfaced tray** (owner decision this
   session): displacement is derived at read time; the subagent runs at the next
   `create_next()` cycle; the save handler is untouched. Same guarantee (no comment ever
   silently lost), honest mechanics.
2. **plan.collab.md decision #6 (count update):** four small first-class agents now come out of
   this goal — `cast-goal-classifier`, `cast-requirements-checker`, `cast-comment-reanchor`
   (owner-approved this session), and `cast-requirements-writeback` (Phase 5). Phase 5's
   writeback should reuse `cast-comment-reanchor`'s locate-text-by-quote prompt technique
   (lift the prompt section, not the agent).
3. **Phase 3a (template, additive):** `document.html.j2` gains the two script tags, the version
   toggle, the tray container, and `data-goal-slug` on `<body>` — golden snapshots regenerate
   (`UPDATE_GOLDENS=1`). If 3a has already landed when Phase 4 executes, this is a normal
   in-phase edit; if 3a is still in flight, coordinate so 3a's goldens are cut once.
4. **Phase 5 (forward contract, restated):** consume
   `cast_server.requirements_render.block_diff.diff_blocks` + `summarize()` AS-IS for the
   provenance-badged change summary; the unified `needs_attention` notification surface
   (high-level decision #4) is Phase 5's build — Phase 4 deliberately keeps surfacing in-page
   (tray + Goal Card chip) and feeds the badge later.

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Re-anchor subagent relocates a comment to the wrong place (the accepted cost of decision #1) | Med-High | Verbatim-substring validation on every relocate (422 backstop); prompt prefers `orphaned` over low-confidence guesses; `relocated` events keep the old quote in payload (auditable, reversible); `eval_reanchor.py` tunes during build (decision #9); fallback stays: reintroduce a lightweight anchor if real use proves it flaky |
| Re-anchor cost/latency per cycle | Medium | LLM runs ONLY for `displaced_comment_ids` (string-find filter) and only at version-create time — zero LLM on save, render, or unchanged content |
| Quote-location in the DOM misses text split across inline tags (e.g. a quote spanning a `<strong>` boundary) | Medium | TreeWalker concatenates text nodes within a section before matching; covered by an e2e case quoting across bold text; a miss degrades to the tray (visible), never a crash |
| `block_diff` mis-pairs blocks with duplicate headings | Low-Med | Document-order pairing is deterministic and tested; worst case = one modified shows as add+remove — annoying, never lossy (set arithmetic guarantees the partition) |
| JS layer outgrows ~150 lines and tempts a library | Medium | Line budget + `package.json` pin test + Spike C already proved the loop on this stack; overflow is escalation evidence per the spike protocol, not license |
| Comment spam / unbounded growth on a goal | Low | Size caps (WP-A); tray collapses resolved; no further mechanism (HOLD SCOPE — moderation is not a v2 problem) |
| `create_next` race (two concurrent snapshots) | Low | Inherited single-user posture + Phase 1's documented `BEGIN IMMEDIATE` fix-forward; `create_next` adds no new read-then-write beyond the wrapped service |
| Archived-version comment reconstruction is subtly wrong (events replay) | Medium | `test_archive_retrieval.py` pins a three-version scenario with resolve-after-archive; reconstruction is a pure query over the append-only trail — re-derivable, never destructive |

## Open Questions

**None blocking.** The two genuine forks this phase had — the re-anchor-on-save mechanism and
the re-anchor agent's home — were resolved interactively this session (owner, 2026-06-11):
lazy + surfaced tray (zero save machinery, displacement derived at read time), and a standalone
4th agent `cast-comment-reanchor`. Everything else was locked at plan review (decisions #1, #7,
#8, #9) or inherited from prior sub-phase canon.

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|---|---|---|
| `cast-ui-testing.collab.md` | US1 (every screen covered), US2 (UI changes mandate test updates) | 1 — Phase 4's render-page UI requires a paired harness update; resolved by WP-G's e2e activity |
| `cast-delegation-contract.collab.md` | Server-never-writes-artifacts; subagent carve-out precedent | None — server writes DB only (`POST /versions` *reads* the file); `cast-comment-reanchor` is bare-JSON subagent-mode per the classifier/checker carve-out, restated in the spec update |
| *(extends)* `cast-requirements-render.collab.md` (Phase 3a WP-G) | Route semantics, DOM contract, artifact class | n/a — WP-G extends it with the Phase 4 surface; becomes the contract Phase 5 cites |
| `cast-output-json-contract.collab.md` | Contract-v2 envelope | None — Phase 4's HTTP-run output uses it; the reanchor subagent is outside it (carve-out) |
