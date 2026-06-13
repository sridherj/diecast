# sp3 — `create_next()` + carry-forward + convergence + archive retrieval — OUTPUT

**Status:** ✅ COMPLETE — all Detailed Steps executed, all verification run, every success criterion met.
**Tests:** 46 sp3-relevant tests pass; 123 broader requirements tests stay green (no regressions).

## What landed

### Step 3.1 — `create_next()` + as-of helpers (`services/requirement_version_service.py`)
- **`create_next(goal_slug, content, created_by, *, db_path=None) -> dict`** — wraps
  `create_snapshot` (inherits hash idempotency, single-txn archive-flip, the `BEGIN IMMEDIATE`
  fix-forward note). Returns the contract dict verbatim:
  `{version: dict, convergence: "converged"|"unconverged", open_comments: list[dict], displaced_comment_ids: list[int]}`.
  - Convergence derived from `comment_service.open_comment_count` (>0 ⇒ unconverged). Never stored.
  - Carry-forward = **do nothing**: open comment rows keep their original `version`.
  - `displaced_comment_ids` = open comments whose `quoted_text` is NOT a verbatim substring of
    the new `content` (pure string-find; **no LLM, no subprocess** — pinned by a test that bombs
    `subprocess.run`/`Popen`). This is the seam sp4b dispatches `cast-comment-reanchor` over.
  - NEVER refuses on open comments (open comments *drive* new versions — US4 S2).
- **`_state_as_of(events, cutoff) -> str | None`** — pure replay of the append-only
  `comment_events` trail to a comment's state at `cutoff`. `relocated` is a re-anchor only (no
  state change). Returns `None` if no event occurred by `cutoff` (comment didn't exist yet).
- **`get_version_with_comments(goal_slug, version, *, db_path=None) -> dict | None`** — the
  archive-retrieval surface. Joins the version row with comments (`version <= n`), each stamped
  with `state_as_of` reconstructed via `_state_as_of` at this version's supersession instant
  (next version's `created_at`, or "now"=`None` for the current version). Returns `None` if the
  version is absent. Comments that didn't exist as of that instant are omitted.
- One-directional import: version service imports `comment_service` **lazily** inside the two
  functions — no module-load cycle (confirmed by a clean import smoke test).

### Step 3.2 / 3.3 — router endpoints (`routes/api_requirements.py`)
- **`POST /versions`** — slug-404; reads the goal's `refined_requirements.collab.md` via
  `requirements_render_service._resolve_goal_dir`; **missing file → 409** ("nothing to snapshot");
  calls `create_next(slug, content, created_by=actor or "human")`; returns the contract dict
  (JSON-only — agent/loop surface, no HTMX negotiation). Server **reads** the file, never writes
  the artifact (delegation contract / FR-011 intact).
- **`GET /versions/{version}`** — slug-404; unknown version → 404; returns
  `{version: row, comments: [...with state_as_of...]}` (US5 S3 as-of reconstruction).

## Verification (all run, all green)
- `tests/test_requirement_versions.py` (extended): create_next snapshot+archive in one txn;
  idempotent identical-content; convergence flips on open-comment count; open comments carry
  forward unchanged (version provenance preserved); `displaced_comment_ids` == verbatim
  string-find over the `refined_requirements.v2-edit.collab.md` fixture (deleted quote displaced,
  surviving quote not); no-subprocess pin.
- `tests/test_archive_retrieval.py` (created): `_state_as_of` unit cases
  (created→resolved→reopened replay at varying cutoffs; relocate-is-inert; pre-creation→None);
  the **resolve-after-archive** three-bump scenario (open as of v1, resolved as of v2) driven by a
  deterministic monotonic clock across both services; unknown version → None; archived version
  returns content+comments; comment-left-on-v2 excluded from v1; **FR-011 folder assertion** (only
  the two canonical files after three bumps).
- `tests/test_requirements_comments_api.py` (extended): POST /versions contract dict + convergence;
  unconverged-with-open-comment; missing-file→409; GET /versions/{n} row+comments-as-of;
  unknown-version→404; unknown-slug→404 on both new endpoints.

### Success criteria — all ✅
- [x] `create_next` returns the exact contract dict; snapshot + archive-flip in one txn.
- [x] `displaced_comment_ids` is the verbatim string-find result over the new content.
- [x] Carry-forward = no row copying; open comments keep their original `version`.
- [x] `GET /versions/{n}` reconstructs as-of resolution state from `comment_events`.
- [x] FR-011 folder assertion passes (no second requirements file ever).
- [x] `POST /versions` reads the file only; missing file → 409.

## Notes for dependent sub-phases
- **sp4a** can add `GET /changes` + the diff route alongside these endpoints — the version list
  metadata (`convergence`, `open_comment_count`) is already in `GET /versions`.
- **sp4b** consumes `create_next`'s `displaced_comment_ids` as the dispatch seam for
  `cast-comment-reanchor`; relocate's 422 substring backstop (sp1) is the deterministic guard on
  the subagent's output. sp3 returns the displaced list only — it never calls an LLM.
- **Crash-safety preserved:** nothing positional/"displaced" is durably stored; the next
  `GET /comments` (sp1) recomputes displacement. No save-path change was made (sp6/WP-F documents
  the deliberate no-op).

## Not run (out of scope / environment-dependent)
- The temporary live-`curl` validation script (needs the server on :8005 + a seeded goal) was not
  executed; the FastAPI `TestClient` API tests exercise the identical router stack end-to-end.
