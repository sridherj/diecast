# Shared Context: refine-req-v2-phase4 (Annotation & Versioning Engine)

> **Read this file at the start of every sub-phase session.** It is the DRY reference
> for cross-cutting context. Each `spN_*/plan.md` assumes you have read it.

## Source Documents
- **Plan:** `docs/plan/2026-06-11-refine-requirements-v2-phase4-annotation-versioning.md` (THE authority — this execution plan is a faithful split of it)
- **Cross-phase canon:** `docs/plan/refine-requirements-v2-decisions-so-far.md`
- **Spec (extended in sp7):** `docs/specs/cast-requirements-render.collab.md`
- **High-level goal plan:** `goals/refine-requirements-v2/plan.collab.md` (Phase 4 section)

## Project Background

Phase 4 builds the **iteration loop** for the requirements-refinement system. Reviewers
(human **or** agent, through the *same* API door) leave comments anchored to a **stored quote**
on the HTML render. Open comments mark the spec **unconverged** and drive new versions. Each new
version yields a **deterministic block-level change summary** (the diff engine Phase 5 adopts
verbatim). Only the current version lives in the goal folder; older versions are archived in the
DB **with their comments and resolution state intact**.

The load-bearing design insight (plan review, decisions #1/#9): **the only deterministic machinery
is where being wrong means silent data loss** — comment rows, version snapshots, and the structural
change *set*. Everything placement-related is a Claude subagent re-locating comments by their stored
quote, **with orphaning always surfaced, never silent**.

**Operating mode: HOLD SCOPE.** The commenting UX and version-diff UX are LOCKED (owner,
2026-06-11). No extra comment features (no threads-of-threads, mentions, realtime), no diff bells
(no word-level diff, no three-pane merge), no notification surface beyond in-page. Every activity
traces to the Phase 4 plan or a locked decision. **No `package.json` may exist anywhere under
`cast-server/`** — the comment layer is ~150 lines of vanilla JS over the existing Jinja+HTMX stack.

## Landed State — Phases 1/2/3a Are BUILT (verified against real code, 2026-06-12)

Phases 1–3a have **landed** in `cast-server/`. This plan adopts the **landed** names, not any
drifted plan vocabulary. Verified facts you can rely on:

| Landed deliverable | Exact location / name |
|---|---|
| Parser package | `cast_server/requirements_render/` (importable without FastAPI) |
| Parser | `requirements_render/parser.py` → `parse_requirements(text)`, `parse_requirements_file(path)` |
| Block model | `requirements_render/blocks.py` → `BlockKind`, `Block{kind, level, body, heading, ref, line_start, line_end}` (`ref` in-memory ONLY), `ParsedRequirements{title, front_matter, preamble, blocks, unrecognized_sections, source_text, content_hash}` |
| Hashing | `requirements_render/hashing.py` → `content_hash(text) -> str` (sha256 hex) |
| Version service | `services/requirement_version_service.py` → `create_snapshot(goal_slug, content, created_by=None, *, db_path=None)`, `get_current`, `get_version(goal_slug, version, *, db_path=None)`, `list_versions(goal_slug, *, db_path=None)`. **`create_next()` does NOT exist yet — sp3 adds it.** |
| Render service | `services/requirements_render_service.py` → `rerender_requirements_html(goal_slug, *, goals_dir=None, db_path=None)`; `_resolve_goal_dir(...)`; goal file at `{goal_dir}/refined_requirements.collab.md`, html at `refined_requirements.html` |
| Render route | `GET /goals/{slug}/render` in `routes/pages.py` (handler `requirements_render(slug)`) |
| Document template | `requirements_render/templates/document.html.j2` + `_theme.css.j2` (token-pinned, golden-snapshotted) |
| Package Jinja env | `requirements_render/templating.py` → `get_environment()` (PackageLoader; autoescape on) — use this for `diff_render.py`, NOT `deps.templates` |
| Goal Card | `requirements_render/goal_card.py` (has the `[PENDING Phase 4]` comment-count slot to fill client-side) |
| Zero-click extractor | `requirements_render/zero_click.py` → `extract_zero_click_view(html)` |
| Classifier / recipes (Phase 2) | `requirements_render/families.py` (`WorkFamily`, `RecipeBlock`, `FAMILY_RECIPES`) — **Phase 4 does not touch these** (diff matches on parser blocks, not recipes) |

**Schema (LANDED — `cast-server/cast_server/db/schema.sql`, mirrored in `db/connection.py` `_run_migrations()`):**
The three Phase-4 tables already exist. Do NOT re-create them; Phase 4 only reads/writes rows.
- `requirement_versions(id, goal_slug, version, content, content_hash, status['current'|'archived'], created_at, created_by, UNIQUE(goal_slug, version))`
- `requirement_comments(id, goal_slug, version, quoted_text, section_hint, body, state['open'|'resolved'|'orphaned'], author, author_kind['human'|'agent'], created_at, updated_at)` — **NO anchor/ref column** (thin spine)
- `comment_events(id, comment_id, event_type['created'|'resolved'|'reopened'|'orphaned'|'relocated'], actor, payload[JSON], created_at)` — append-only
- Indexes: `idx_req_versions_goal_status`, `idx_req_comments_goal_state`, `idx_comment_events_comment`

## Codebase Conventions (canon for every sub-phase)

- **Service DB pattern (MUST follow):** flat module functions, `db_path: Path | None = None`
  injectable, `conn = get_connection(db_path)`. Model on `goal_service.py` / `task_service.py` —
  **NOT** `orchestration_service.py` (file/manifest-based). Each write is ONE transaction
  (single `commit()`); state change + its `comment_events` append commit atomically.
- **Content negotiation (the same-door pattern):** copy `routes/api_agents.py` exactly. The
  request-bound templates object is `cast_server.deps.templates` (`Jinja2Templates`, dir =
  `cast_server/templates/`). Pattern: `if request.headers.get("HX-Request"): return
  templates.TemplateResponse(request, "fragments/...", {...})` else `return JSONResponse(...)`.
  **`author_kind` is the ONLY human/agent distinction — never a differing code path** (FR-013).
- **Slug validation:** every requirements endpoint validates the slug via
  `goal_service.get_goal(slug)` first; unknown → 404 (the Phase 3a path-traversal rule).
- **App factory:** routers register in `cast_server/app.py` (lines ~186–193, `app.include_router(...)`).
- **Templates:** package-local document/theme templates live in `requirements_render/templates/`
  (PackageLoader). Request-bound web fragments live in `cast_server/templates/fragments/`.
- **Tokens only, never hex:** all CSS uses `var(--color-*)` tokens (Phase 3a hex-scan test enforces).
- **Goldens:** `tests/golden/requirements_render/`; regenerate with `UPDATE_GOLDENS=1 pytest ...`.
- **Eval harnesses:** `tests/eval_*.py` are excluded from default CI discovery (manual/slow).
- **Subagent-mode agents** (classifier/checker precedent): `config.yaml` `model: sonnet`,
  `dispatch_mode: subagent`, `interactive: false`, `context_mode: lightweight`,
  `timeout_minutes: 10`; emit EXACTLY ONE bare JSON verdict (no prose, no fences) — this is the
  documented carve-out from `cast-delegation-contract.collab.md`, NOT a violation to "fix".

## Key File Paths

| Path | Role | Phase-4 action |
|---|---|---|
| `cast_server/services/comment_service.py` | Comment CRUD + events | **CREATE** (sp1) |
| `cast_server/routes/api_requirements.py` | `/api/goals/{slug}/requirements/*` | **CREATE** (sp1); sp3 + sp4a add endpoints |
| `cast_server/requirements_render/block_diff.py` | Pure diff engine (Phase 5 contract) | **CREATE** (sp2) |
| `cast_server/requirements_render/diff_render.py` | Tracked-changes renderer | **CREATE** (sp2) |
| `cast_server/services/requirement_version_service.py` | + `create_next()` | **MODIFY** (sp3) |
| `cast_server/routes/pages.py` | + `GET /goals/{slug}/render/diff` | **MODIFY** (sp4a) |
| `cast_server/requirements_render/templates/document.html.j2` | toggle (sp4a) + scripts/tray/goal-card (sp5) | **MODIFY** (sp4a → sp5, sequential) |
| `cast_server/requirements_render/templates/_theme.css.j2` | diff CSS (sp4a) + comment CSS (sp5) | **MODIFY** (sp4a → sp5, sequential) |
| `cast_server/static/requirements_comments.js` | ~150-line vanilla JS layer | **CREATE** (sp5) |
| `cast_server/templates/fragments/requirements_comments/` | `tray.html`, `thread_item.html` (sp1), `composer.html` (sp5) | **CREATE** (sp1 + sp5) |
| `agents/cast-comment-reanchor/` | 4th subagent (`.md` + `config.yaml`) | **CREATE** (sp4b) |
| `agents/cast-refine-requirements/cast-refine-requirements.md` + `config.yaml` | + Iteration-mode wiring, `allowed_delegations` | **MODIFY** (sp4b) |
| `cast_server/app.py` | register `api_requirements_router` | **MODIFY** (sp1) |

## Data Schemas & Contracts (the Naming Contract — copy verbatim, Phase 5 MUST adopt)

### Diff engine — `cast_server.requirements_render.block_diff` (THE cross-phase contract)
```python
def diff_blocks(old: ParsedRequirements, new: ParsedRequirements) -> BlockDiff: ...

@dataclass(frozen=True)
class BlockDiff:
    added: tuple[Block, ...]            # in new, no match in old
    removed: tuple[Block, ...]          # in old, no match in new
    modified: tuple[ModifiedBlock, ...] # matched by key, body differs
    unchanged: tuple[ModifiedBlock, ...]# matched, body identical (pure moves land here)

@dataclass(frozen=True)
class ModifiedBlock:
    old: Block
    new: Block

def summarize(diff: BlockDiff) -> dict: ...  # counts + per-item {change, kind, heading_or_ref, excerpt}
```
Pure function: **no I/O, no DB, no LLM, deterministic.** **Partition invariant:** every old block
appears exactly once across `removed ∪ modified.old ∪ unchanged.old`; every new block exactly once
across `added ∪ modified.new ∪ unchanged.new`. Match algorithm (two passes, document-order
tie-break): (1) normalized-body equality → `unchanged` (a pure move is unchanged — set arithmetic
has no "moved"); (2) key equality with differing body → `modified`, where key = the heading token
for level-2 blocks (the in-memory `ref` like `FR-007`/`US1` when present, else full `heading`
text) and `kind` for level-1 blocks; duplicate keys pair in document order. Remainders →
`added`/`removed`. Module docstring MUST state: *"Phase 5 imports this engine for round-trip change
summaries — extend, never fork. The change SET is deterministic; LLM narration consumes
`summarize()` output and never invents entries."*

### Diff view renderer — `cast_server.requirements_render.diff_render`
```python
def render_diff(old, new, *, base_version: int, head_version: int) -> RenderResult: ...
```
Same `RenderResult` shape as Phase 3a's renderer; deterministic; reuses `document.html.j2` theme via
`templating.get_environment()`. Transient `id="diff-{n}"` anchors exist ONLY in the diff view —
generated per render, never stored, never comment anchors.

### Comment service — `cast_server.services.comment_service` (flat fns, house DB pattern)
```python
create_comment(goal_slug, quoted_text, section_hint, body, author, author_kind,
               *, version=None, db_path=None) -> dict   # version defaults to current snapshot, 0 if none
list_comments(goal_slug, *, state=None, db_path=None) -> list[dict]   # stamps derived `displaced: bool` vs current file
get_comment(comment_id, *, db_path=None) -> dict
resolve_comment(comment_id, actor, *, db_path=None) -> dict           # 409 if already resolved
reopen_comment(comment_id, actor, *, db_path=None) -> dict
relocate_comment(comment_id, new_quoted_text, new_section_hint, actor, *, db_path=None) -> dict
orphan_comment(comment_id, actor, *, db_path=None) -> dict
open_comment_count(goal_slug, *, db_path=None) -> int
get_comment_events(comment_id, *, db_path=None) -> list[dict]
```
Every transition writes its `comment_events` row in the SAME transaction. `relocate_comment` stores
the old quote in the event `payload` JSON.

### Version gate — `requirement_version_service.create_next`
```python
create_next(goal_slug, content, created_by, *, db_path=None) -> dict
# returns {version: dict, convergence: "converged"|"unconverged",
#          open_comments: list[dict], displaced_comment_ids: list[int]}
```
`displaced_comment_ids` = open comments whose `quoted_text` is NOT a verbatim substring of `content`
(the deterministic needs-LLM detector; the seam the agent loop dispatches `cast-comment-reanchor`
over). Wraps `create_snapshot` (inherits hash idempotency + txn discipline + `BEGIN IMMEDIATE`
fix-forward note). Open comments carry forward by doing nothing (rows keep their original `version`).

### API router — `cast_server/routes/api_requirements.py`, prefix `/api/goals/{goal_slug}/requirements`
- `GET  /comments` (`?state=`) — negotiated: JSON list (each carries derived `displaced: bool`) | HTML tray fragment
- `POST /comments` — negotiated: JSON 201 | HTML thread-item fragment. **THE canonical dual-assertion agent-parity handler.**
- `POST /comments/{comment_id}/resolve` · `/reopen` · `/orphan` — negotiated
- `POST /comments/{comment_id}/relocate` (body: `new_quoted_text`, `new_section_hint`) — server validates `new_quoted_text` is a verbatim substring of the current file, else **422**
- `GET  /versions` — JSON list + `{convergence, open_comment_count}` metadata
- `GET  /versions/{n}` — version row **with** its comments + as-of resolution state (US5 S3)
- `POST /versions` — `create_next()` from the current goal file; returns the contract dict
- `GET  /changes?base=N&head=M` (default head=current, base=head−1) — negotiated: `summarize()` JSON | "What changed" panel fragment (FR-017)

### Diff page route — `routes/pages.py`
`GET /goals/{slug}/render/diff?base=N&head=M` — tracked-changes view (decision #8); the render
page's toggle targets it. Served fresh each request (never written to the goal folder).

### Re-anchor agent — `agents/cast-comment-reanchor/` (verdict schema, canonical)
```json
{"verdicts": [{"comment_id": 0, "verdict": "relocated|orphaned",
  "new_quoted_text": "str|null", "new_section_hint": "str|null",
  "confidence": 0.0, "reasoning": "str"}]}
```
EXACTLY ONE bare JSON object, no prose, no fences. `config.yaml`: `model: sonnet`,
`dispatch_mode: subagent`, `interactive: false`, `context_mode: lightweight`, `timeout_minutes: 10`.

### Convergence rule (the one sentence)
A goal's requirements are `unconverged` **iff** `open_comment_count(goal_slug) > 0`. Derived, never stored.

## Pre-Existing Decisions (constrain implementation — do not relitigate)

- **#1 Re-anchor-on-save = lazy + surfaced tray.** Displacement is a **derived, read-time
  property** (open comment whose `quoted_text` isn't found verbatim in the current file). The save
  handler gains **zero** new machinery. The re-anchor subagent runs at the next agent touchpoint
  (`create_next()`), never on a human save. The string-find only detects *whether* re-location is
  needed; all re-location is the subagent's. **Nothing positional is ever stored.**
- **#2 Re-anchor = a new 4th agent `cast-comment-reanchor`** (deviates from plan.collab.md #6's
  "three agents" — owner-approved). Phase 5 reuses its *prompt technique*, not the agent.
- **#7 Commenting UX LOCKED:** select text → 💬 pill → inline composer (below-default,
  flip-up-when-cramped) → `<mark>` highlight, open/resolved state.
- **#8 Version-diff UX LOCKED:** version toggle revealing a "What changed" panel + inline
  tracked-changes green/amber/red; **the structural diff is the source of truth — a Claude subagent
  may *narrate* it but never *invent* it.**
- **#9 Orphaning is always surfaced, never silent;** prefer `orphaned` over a low-confidence guess;
  `eval_reanchor.py` validates the agent *during build*.
- **FR-013:** human/agent parity through ONE door; `author_kind` the only distinction.
- **FR-011:** the goal folder NEVER gains a second requirements file; versions are DB rows.
- **No privileged UI write path:** the composer's `hx-post` hits the identical endpoint an agent curls.

## Relevant Specs

- `docs/specs/cast-requirements-render.collab.md` — Phase 3a render contract (route semantics, DOM
  contract, artifact class). **sp7 extends it** with the Phase 4 surface. When modifying
  spec-linked files (the render route, the document template, the renderer package), read this spec
  and preserve its SAV behaviors.
- `cast-ui-testing.collab.md` — US1 (every screen covered), US2 (UI changes mandate paired harness
  updates). Phase 4's render-page UI makes the e2e harness update **mandatory** (sp7).
- `cast-delegation-contract.collab.md` — server never writes artifacts (Phase 4 server writes DB
  only; `POST /versions` *reads* the goal file). Subagent bare-JSON carve-out applies to
  `cast-comment-reanchor`.

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|---|---|---|---|---|
| sp1 comment_service + same-door API | Sub-phase | — | sp3, sp4a, sp5, sp6, sp7 | **sp2** (file-disjoint) |
| sp2 block_diff engine (pure) | Sub-phase | — | sp4a | **sp1** (file-disjoint) |
| sp3 versions + archive (`create_next`) | Sub-phase | sp1 | sp4a, sp4b, sp6, sp7 | — |
| sp4a diff-view wiring | Sub-phase | sp2, sp3 | sp5, sp6, sp7 | **sp4b** (file-disjoint) |
| sp4b reanchor agent + loop + eval | Sub-phase | sp1, sp3 | sp7 | **sp4a**, sp5 (file-disjoint) |
| sp5 vanilla-JS comment layer | Sub-phase | sp1, sp4a | sp6, sp7 | sp4b (file-disjoint) |
| sp6 guards + pins (tests only) | Sub-phase | sp1, sp3, sp4a, sp5 | sp7 | sp4b |
| sp7 spec + e2e + compliance | Sub-phase | ALL | — | — |

**No decision gates** — the plan's Open Questions are "None blocking" (both forks resolved
interactively 2026-06-11). Execution is fully linear-with-two-parallel-pairs; no human pause points.

**Critical path (from the plan):** sp1 → sp3 → sp4b (the agent loop end-to-end). sp2 is fully
parallel with sp1 from day one (pure functions over the landed Phase 1 parser). **The
API-before-UI ordering is the FR-013 forcing function — do NOT start sp5 (UI) before sp1's
dual-assertion test is green.**

## Note on WP→sub-phase mapping (one deviation from 1:1)

The plan has Work Packages A–G. This split maps A→sp1, C→sp3, D→sp4b, E→sp5, F→sp6, G→sp7, and
**splits WP-B into sp2 (pure engine: `block_diff.py` + `diff_render.py`) and sp4a (wiring: diff
route, `/changes` endpoint, template toggle, diff CSS)**. Rationale: the plan calls WP-B "fully
parallel from day one," but its template/`api_requirements.py` edits collide with sp1/sp3/sp5. The
split lets the genuinely-pure engine run parallel to sp1 while the shared-file wiring serializes
correctly after sp3.
