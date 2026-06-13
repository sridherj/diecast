# Sub-phase 1: Comment service + same-door API (the FR-013 forcing function)

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase4/_shared_context.md` before starting.

## Objective

Build the comment persistence layer (`comment_service.py`) and the same-door HTTP API
(`api_requirements.py`) **before any UI**. This is the FR-013 forcing function: a human composer
and an agent `curl` hit the *identical* endpoint, with `author_kind` the only distinction — never a
differing code path. When this sub-phase's dual-assertion test is green, the parity contract is
proven and the UI (sp5) may build on it.

## Dependencies

- **Requires completed:** None. Phases 1/3a are landed (schema tables, `goal_service`, `deps.templates`).
- **Assumed codebase state:** `requirement_comments` / `comment_events` tables exist;
  `goal_service.get_goal(slug)` works; `routes/api_agents.py` shows the HX negotiation pattern;
  `cast_server/app.py` registers routers ~line 186.

## Scope

**In scope:**
- `cast_server/services/comment_service.py` — all flat functions per the Naming Contract.
- `cast_server/routes/api_requirements.py` — the comment endpoints + `GET /versions` (list only).
- Register `api_requirements_router` in `cast_server/app.py`.
- Negotiated fragments: `cast_server/templates/fragments/requirements_comments/tray.html` +
  `thread_item.html` (the HTML half of the negotiated `GET /comments` and `POST /comments`).
- Tests: `tests/test_comment_service.py`, `tests/test_requirements_comments_api.py`.

**Out of scope (do NOT do these):**
- `create_next()` / `POST /versions` / `GET /versions/{n}` body — sp3 (this sub-phase ships only
  `GET /versions` *list*, reading existing rows via `requirement_version_service.list_versions`).
- `GET /changes` and the diff route — sp4a.
- Any JS, the composer fragment, `<mark>` rendering, Goal Card wiring — sp5.
- The `cast-comment-reanchor` agent — sp4b.
- Touching `document.html.j2` / `_theme.css.j2` — those belong to sp4a/sp5.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast_server/services/comment_service.py` | Create | Does not exist |
| `cast_server/routes/api_requirements.py` | Create | Does not exist |
| `cast_server/app.py` | Modify | Registers routers ~L186–193 |
| `cast_server/templates/fragments/requirements_comments/tray.html` | Create | Dir does not exist |
| `cast_server/templates/fragments/requirements_comments/thread_item.html` | Create | Dir does not exist |
| `tests/test_comment_service.py` | Create | Does not exist |
| `tests/test_requirements_comments_api.py` | Create | Does not exist |

## Detailed Steps

### Step 1.1: `comment_service.py` — flat functions, house DB pattern

Mirror `goal_service.py`'s shape: `from cast_server.db.connection import get_connection`, flat
module functions, `db_path: Path | None = None`, `conn = get_connection(db_path)`. Use
`datetime.now(timezone.utc).isoformat()` for timestamps (match `requirement_version_service`).

Implement exactly the signatures in `_shared_context.md` → "Comment service". Key behaviors:

- **`create_comment(...)`:** `version` defaults to the current snapshot's version
  (`requirement_version_service.get_current(goal_slug)`; `0` if no version exists yet). Insert the
  `requirement_comments` row (`state='open'`, `author_kind` defaulting `'human'`) **and** a
  `comment_events` row (`event_type='created'`, `actor=author`) in **one transaction** (single
  `commit()`). Return the row dict (include the new `id`).
- **`list_comments(goal_slug, *, state=None, db_path=None)`:** return row dicts. Stamp each **open**
  comment with derived `displaced: bool` = `quoted_text not in current_file_text`. Read the current
  file via the goal dir (use `requirements_render_service._resolve_goal_dir` +
  `/refined_requirements.collab.md`; if the file is missing, treat current text as `""` → every
  open comment is `displaced=True`, never crash). **Orphaned and resolved comments are never
  displacement-checked** (`displaced` absent or `False`). The string-find is a *detector*, not an
  anchoring engine — store nothing positional.
- **State transitions** (`resolve`/`reopen`/`relocate`/`orphan`): each updates `state`/fields,
  bumps `updated_at`, and appends its `comment_events` row in the **same transaction**.
  - `resolve_comment` on an already-`resolved` comment → raise a domain error the route maps to
    **409** (state-machine violations announce themselves; never a silent no-op).
  - `relocate_comment(comment_id, new_quoted_text, new_section_hint, actor)` → sets
    `quoted_text`/`section_hint`, event `relocated` with the **old quote** in `payload` JSON
    (`{"old_quoted_text": ...}`). (Substring validation is the route's job — see Step 1.3.)
  - `orphan_comment` → `state='orphaned'`, event `orphaned`.
- **`open_comment_count(goal_slug)`** → `SELECT COUNT(*) ... WHERE goal_slug=? AND state='open'`.
- **`get_comment` / `get_comment_events`** → simple selects; `get_comment` on unknown id raises the
  not-found domain error (route → 404).

Use a small module-level exception pair (e.g. `CommentNotFound`, `CommentStateError`) so the route
maps them to 404/409 without leaking SQL. Follow whatever error idiom `goal_service`/`task_service`
already use if one exists; otherwise define these locally.

### Step 1.2: Validation helpers

- `quoted_text` and `body` are required and non-empty after strip → else the route returns **422**.
- Size cap: `quoted_text` and `body` ≤ 10 KB each → **422** (the WP-A design-review guard).
- These checks live in the route layer (Pydantic request models) so the service stays a thin DB
  layer; keep the service tolerant but the API strict.

### Step 1.3: `api_requirements.py` — the same-door router

```python
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from cast_server.deps import templates
from cast_server.services import goal_service, comment_service, requirement_version_service

router = APIRouter(prefix="/api/goals/{goal_slug}/requirements", tags=["requirements"])
```

For **every** handler: validate the slug first via `goal_service.get_goal(goal_slug)`; `None` → 404.
Negotiate exactly like `api_agents.list_runs`:

```python
if request.headers.get("HX-Request"):
    return templates.TemplateResponse(request, "fragments/requirements_comments/thread_item.html",
                                      {"comment": row})
return JSONResponse(status_code=201, content=row)
```

Endpoints (this sub-phase): `GET /comments` (`?state=`), `POST /comments`,
`POST /comments/{comment_id}/resolve|reopen|orphan|relocate`, `GET /versions` (list).

- **`POST /comments`** — THE canonical dual-assertion handler. Body model:
  `{quoted_text, section_hint?, body, author?, author_kind?}`. `author` defaults to something
  sensible (e.g. `"human"`); `author_kind` defaults `"human"`. The SAME `comment_service.create_comment`
  call runs regardless of header; only the *response shape* differs. HTML branch → `thread_item.html`;
  JSON branch → 201 + the row.
- **`GET /comments`** — JSON → list of rows (open ones carry `displaced`); HTML → `tray.html` with
  the comment list grouped (open/displaced/orphaned/resolved-collapse).
- **`relocate`** — server-side: `new_quoted_text` MUST be a verbatim substring of the current file
  (`new_quoted_text in current_text`), else **422** with the offending quote echoed; no row change.
  This is the deterministic backstop on subagent output (sp4b relies on it).
- **`resolve`** on a resolved comment → map `CommentStateError` → **409**.
- **`GET /versions`** — JSON list from `requirement_version_service.list_versions` + a metadata
  object `{convergence, open_comment_count}` where `convergence = "unconverged" if
  open_comment_count(goal_slug) > 0 else "converged"`. (Full `POST`/`GET /{n}` land in sp3.)

### Step 1.4: Register the router

In `cast_server/app.py`, beside the other `api_*` imports/registrations (~L181/L190):
```python
from cast_server.routes.api_requirements import router as api_requirements_router
...
app.include_router(api_requirements_router)
```

### Step 1.5: Fragments

- `fragments/requirements_comments/thread_item.html` — one comment thread item: `body`,
  `author` + `author_kind` badge, `state`, resolve/reopen buttons (hx-post to the matching
  endpoint). All content via Jinja autoescape — never raw HTML.
- `fragments/requirements_comments/tray.html` — the tray: iterate comments, grouped by
  open/displaced ("needs re-anchor") / orphaned ("triage") / resolved (collapsed). Buttons
  hx-post to resolve/reopen. (The composer fragment is sp5.)

Keep both minimal — the visual styling (`.comment-tray`, etc.) is sp5's CSS; here just emit the
class names and structure the negotiated responses need.

## Verification

### Automated Tests (permanent)

**`tests/test_comment_service.py`** — use a temp `db_path` fixture (seed a goal row + a
`requirement_versions` current row so `create_comment` resolves a version):
- `create_comment` writes a row AND a `created` event in one txn; returns the id; `author_kind`
  defaults `human`; explicit `agent` honored.
- Every transition (`resolve`/`reopen`/`relocate`/`orphan`) writes exactly one matching
  `comment_events` row; `relocate` event payload contains the old quote.
- `resolve` then `reopen` round-trips state open↔resolved; a second `resolve` raises
  `CommentStateError`.
- `open_comment_count` reflects open rows only (resolved/orphaned excluded).
- `list_comments` stamps `displaced=True` when the quote is absent from supplied/looked-up current
  text, `False` when present; **orphaned and resolved comments are not displacement-checked**.

**`tests/test_requirements_comments_api.py`** — FastAPI `TestClient`, temp db:
- **THE dual-assertion agent-parity test (FR-013):** call `POST /comments` once with NO `HX-Request`
  header (→ JSON 201) and once with `HX-Request: true` (→ HTML thread-item fragment). Assert the
  **same DB row is written either way** (same fields, `author_kind` the only differing *input*),
  and that there is one `create_comment` code path — not two handlers. (Pattern: post both, read
  back via `list_comments`, assert structural equality modulo `author_kind`/`id`.)
- Parametrized lighter parity assertions over `resolve`/`reopen`/`orphan`/`relocate`/`GET /comments`.
- `relocate` with `new_quoted_text` absent from the current file → **422**, no row change.
- Unknown slug on every endpoint → **404**.
- Empty `quoted_text` / empty `body` / >10 KB → **422**.
- `resolve` on an already-resolved comment → **409**.

### Validation Scripts (temporary)
```bash
cd cast-server && python -m pytest tests/test_comment_service.py tests/test_requirements_comments_api.py -q
# Smoke the same-door parity by hand:
curl -s -XPOST localhost:8005/api/goals/<slug>/requirements/comments \
  -H 'content-type: application/json' \
  -d '{"quoted_text":"<verbatim slice>","body":"hi","author_kind":"agent"}' | head
```

### Manual Checks
- `grep -n "HX-Request" cast_server/routes/api_requirements.py` — negotiation present on every
  user-facing handler.
- Confirm NO second write path: the POST handler calls `comment_service.create_comment` exactly once.

### Success Criteria
- [ ] `comment_service.py` exists with all Naming-Contract functions; every transition is
  events-logged in-transaction.
- [ ] `api_requirements.py` registered; all comment endpoints + `GET /versions` list respond.
- [ ] `test_requirements_comments_api.py` dual-assertion test passes (same row, one code path).
- [ ] `test_comment_service.py` passes (CRUD + events + state machine + displacement detector).
- [ ] relocate→422 / unknown-slug→404 / empty/oversize→422 / double-resolve→409 all asserted.
- [ ] No file under `document.html.j2` / `_theme.css.j2` / any `.js` was touched.

## Execution Notes

- **The string-find displacement check is a detector, not an anchoring engine** (decision #1).
  Store nothing positional. `displaced` is recomputed on every `GET /comments`.
- Read `cast_server/routes/api_agents.py` for the exact `TemplateResponse(request, name, ctx)` /
  `JSONResponse` negotiation — copy it, don't invent.
- `goal_service.get_goal(slug)` takes a positional `db_path` (`get_goal(slug, db_path=None)`).
- Do not add an `anchor`/`ref` column or any positional storage — the schema is thin-spine by design.

**Spec-linked files:** This sub-phase does not modify files covered by
`cast-requirements-render.collab.md` (it adds new `/api/...` routes; the render route/template are
untouched). The spec extension for the comment API is sp7's job — do not edit the spec here.
