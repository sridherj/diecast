# sp1 output — Comment service + same-door API (DONE)

**Status:** completed. All Detailed Steps executed, all verification run, every success
criterion met. 30/30 sub-phase tests green; related render/version tests still green (no
regression). No forbidden file touched (`document.html.j2` / `_theme.css.j2` / any `.js`).

## What landed (exact names dependent sub-phases must use)

### `cast_server/services/comment_service.py` (CREATED)
Flat house-DB functions, injectable `db_path`, every transition events-logged in ONE txn.
Module exceptions: `CommentNotFound` (→404), `CommentStateError` (→409).

```python
create_comment(goal_slug, quoted_text, section_hint, body, author, author_kind="human",
               *, version=None, db_path=None) -> dict        # version defaults to current snapshot, 0 if none
list_comments(goal_slug, *, state=None, db_path=None,
              current_text=None, goals_dir=None) -> list[dict] # stamps `displaced: bool` on OPEN comments only
get_comment(comment_id, *, db_path=None) -> dict              # raises CommentNotFound
get_comment_events(comment_id, *, db_path=None) -> list[dict] # append-only, oldest first
open_comment_count(goal_slug, *, db_path=None) -> int
resolve_comment(comment_id, actor, *, db_path=None) -> dict   # CommentStateError if already resolved
reopen_comment(comment_id, actor, *, db_path=None) -> dict    # CommentStateError if already open
relocate_comment(comment_id, new_quoted_text, new_section_hint, actor, *, db_path=None) -> dict
                                                              # event payload = {"old_quoted_text": ...}
orphan_comment(comment_id, actor, *, db_path=None) -> dict
```

**Notes for downstream:**
- `list_comments` gained two **optional** keyword args beyond the Naming Contract —
  `current_text` (test/agent seam: bypass the file read) and `goals_dir` (test injection).
  Both default to lookup-from-disk behavior; the contract signature is unchanged for callers.
- Displacement is **derived, read-time only**. Open comments get `displaced: bool`; orphaned
  and resolved comments are NOT stamped (key absent). Missing goal file → current text `""`
  → all open comments `displaced=True` (never crashes).
- `relocate_comment` does NOT validate substring — that backstop is the **route's** job
  (sp4b relies on the route's 422).

### `cast_server/routes/api_requirements.py` (CREATED), prefix `/api/goals/{goal_slug}/requirements`
Same-door content negotiation via `_is_hx(request)` (`HX-Request: true`). Validation in
Pydantic request models (route layer, service stays thin). Slug validated first on every
handler (`goal_service.get_goal` → 404). Accepts JSON **or** form bodies (composer posts form).

Endpoints shipped this sub-phase:
- `GET  /comments` (`?state=`) — JSON `{comments:[...]}` (open carry `displaced`) | `tray.html`
- `POST /comments` — **THE dual-assertion handler.** ONE `create_comment` call; JSON 201 (row)
  | `thread_item.html`. Body: `{quoted_text, body, section_hint?, author?, author_kind?}`.
- `POST /comments/{id}/resolve|reopen|orphan` — negotiated; resolve→409 if already resolved.
- `POST /comments/{id}/relocate` — `{new_quoted_text, new_section_hint?, actor?}`; **422** if
  `new_quoted_text` is not a verbatim substring of the current goal file (no row change).
- `GET  /versions` — JSON `{versions:[...], convergence, open_comment_count}`;
  `convergence = "unconverged" if open_comment_count > 0 else "converged"`.

Validation contract: empty (post-strip) or >10 KB `quoted_text`/`body` → **422**.

### Registered in `cast_server/app.py`
`from cast_server.routes.api_requirements import router as api_requirements_router` +
`app.include_router(api_requirements_router)` (beside `api_artifacts_router`).

### Fragments (CREATED) — `cast_server/templates/fragments/requirements_comments/`
- `thread_item.html` — one thread item: `.comment-thread-item` with `data-state`,
  `data-author-kind`, `data-displaced`; author-kind + state badges; resolve/reopen buttons
  `hx-post` to the matching endpoint. Autoescaped throughout.
- `tray.html` — `.comment-tray` grouped open / displaced ("Needs re-anchor") / orphaned
  ("Triage") / resolved (`<details>` collapsed). Includes `thread_item.html` per comment.
- Styling (`.comment-tray*`, `.comment-thread-item*`, badges) is **sp5's CSS** — only class
  names + structure exist here.

## Tests (permanent)
- `tests/test_comment_service.py` — 17 tests: create+created-event-in-one-txn, version
  default (current / 0), author_kind default+override, resolve↔reopen roundtrip with event
  ordering, double-resolve / reopen-open → `CommentStateError`, orphan, relocate (old quote in
  payload), unknown-id → `CommentNotFound`, `open_comment_count` excludes resolved/orphaned,
  displacement detector (supplied text, file lookup, missing file, orphaned/resolved skipped),
  state filter.
- `tests/test_requirements_comments_api.py` — 13 tests: **dual-assertion parity** (same row
  modulo id/author_kind, one code path), displaced in list, tray HTMX, resolve/orphan parity,
  reopen, relocate success (substring) + 422 (non-substring, no change), unknown-slug→404 on
  all 7 endpoints, empty/oversize→422, double-resolve→409, versions convergence metadata.

## Hand-off to dependents
- **sp3** adds `create_next()` + `POST /versions` + `GET /versions/{n}` (this sub-phase shipped
  `GET /versions` list-only, reading via `requirement_version_service.list_versions`).
- **sp4a** adds `GET /changes` and the diff route — do NOT edit the comment endpoints' shape.
- **sp4b** dispatches `cast-comment-reanchor` and relies on the **relocate 422 substring
  backstop** already enforced here.
- **sp5** (UI) builds on the now-green dual-assertion parity contract; adds `composer.html`,
  `<mark>` rendering, JS, and all the CSS the fragments reference.
