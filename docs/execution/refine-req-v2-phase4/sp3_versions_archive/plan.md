# Sub-phase 3: `create_next()` + carry-forward + convergence + archive retrieval

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase4/_shared_context.md` before starting.

## Objective

Add the **version gate** to the system: `create_next()` snapshots a new version, archives the prior,
carries open comments forward (by doing nothing), computes convergence from the open-comment count,
and names exactly which comments need re-anchoring (`displaced_comment_ids`). Plus the archive
retrieval that returns a historical version **with its comments and as-of resolution state**
reconstructed from the append-only `comment_events` trail. This is on the **critical path**
(sp1 → sp3 → sp4b).

## Dependencies

- **Requires completed:** sp1 (`comment_service` — for `open_comment_count`, `list_comments`,
  `get_comment_events`; `api_requirements.py` router exists to extend).
- **Assumed codebase state:** `requirement_version_service.create_snapshot/get_current/get_version/
  list_versions` landed (Phase 1); `comment_events` rows are written on every transition (sp1).

## Scope

**In scope:**
- Extend `cast_server/services/requirement_version_service.py` with `create_next(...)`.
- Add to `cast_server/routes/api_requirements.py`: `POST /versions`, `GET /versions/{n}`
  (the `GET /versions` *list* already exists from sp1 — extend its metadata if needed).
- Tests: extend `tests/test_requirement_versions.py`; create `tests/test_archive_retrieval.py`.

**Out of scope (do NOT do these):**
- `GET /changes` / the diff route / the version toggle — sp4a.
- Dispatching `cast-comment-reanchor` or applying verdicts — sp4b (sp3 only *returns* the displaced
  list; it never calls an LLM).
- Any save-path change — that is deliberately nothing (sp6/WP-F documents it).
- Touching the comment service's internals (sp1 owns `comment_service.py`); sp3 only *calls* it.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast_server/services/requirement_version_service.py` | Modify | Has `create_snapshot`/`get_*`/`list_versions` |
| `cast_server/routes/api_requirements.py` | Modify | sp1 created it with comment endpoints + `GET /versions` |
| `tests/test_requirement_versions.py` | Modify | Phase 1 idempotency tests exist |
| `tests/test_archive_retrieval.py` | Create | Does not exist |

## Detailed Steps

### Step 3.1: `create_next()` in the version service

```python
def create_next(goal_slug, content, created_by, *, db_path=None) -> dict:
    """Snapshot the next version and report comment convergence + displacement.

    Wraps create_snapshot (inherits hash idempotency + single-txn archive-flip + the
    BEGIN IMMEDIATE fix-forward note). Returns:
      {version: dict, convergence: "converged"|"unconverged",
       open_comments: list[dict], displaced_comment_ids: list[int]}
    """
```
- Call `create_snapshot(goal_slug, content, created_by, db_path=db_path)` → the new (or unchanged,
  if idempotent) version row.
- `open_comments = comment_service.list_comments(goal_slug, state="open", db_path=db_path)`.
- `convergence = "unconverged" if comment_service.open_comment_count(goal_slug, db_path=db_path) > 0
  else "converged"`.
- `displaced_comment_ids = [c["id"] for c in open_comments if c["quoted_text"] not in content]`
  (the deterministic verbatim string-find — the needs-LLM detector; the seam sp4b dispatches over).
- **Carry-forward = do nothing:** open comment rows keep their original `version` (provenance of
  where they were left). "Current" open comments are simply `state='open'` regardless of version —
  no row copying, no remapping.
- **Gating semantics, stated precisely:** `create_next()` NEVER refuses on open comments — open
  comments are what *drive* new versions (US4 S2). The gate is the convergence *signal*, not a block.

**Import direction:** the version service imports `comment_service` (one-directional; no cycle —
`comment_service` does not import the version service except `get_current` for the default version
in `create_comment`; confirm no import cycle at module load).

### Step 3.2: `POST /versions` and `GET /versions/{n}` in the router

- **`POST /versions`** — validate slug → 404. Read the goal's current
  `refined_requirements.collab.md` (via `requirements_render_service._resolve_goal_dir`); missing
  file → **409** "nothing to snapshot". Call `create_next(slug, content, created_by="human" or the
  request actor)`. Return the contract dict (JSON). (No negotiation needed for POST /versions — it's
  an agent/loop surface; JSON only is fine. Keep slug-404 consistent.) The server READS the file
  only — it never writes the artifact (delegation contract intact).
- **`GET /versions/{n}`** — validate slug → 404; unknown version → 404. Return the version row
  **with** its comments and as-of resolution state (Step 3.3).

### Step 3.3: Archive retrieval (US5 S3) — as-of reconstruction

`GET /versions/{n}` joins the version row with comments where `version <= n`, each rendered with its
state **as of that version's supersession time** — the next version's `created_at`, or "now" for the
current version — reconstructed by **replaying `comment_events` up to that instant**:

- For each candidate comment, walk its `comment_events` (via
  `comment_service.get_comment_events`) ordered by `created_at`, applying transitions up to the
  cutoff timestamp; the resulting state is the as-of state. This makes US5 S3 a **query over the
  append-only trail, not a stored feature**.
- **FR-011 stays structural:** versions are rows; the goal folder never gains a second requirements
  file. (sp6's guard test asserts the folder contents.)

Keep the reconstruction in a small pure helper (e.g. `_state_as_of(events, cutoff) -> str`) so it's
unit-testable and re-derivable.

## Verification

### Automated Tests (permanent)

**`tests/test_requirement_versions.py` (extended):**
- `create_next()`: a new `current` row + the prior flipped `archived` in ONE txn.
- `convergence` flips on open-comment count (0 → `converged`; ≥1 → `unconverged`).
- Open comments carry forward: still `open`, still listed after the bump (their `version` unchanged).
- `displaced_comment_ids` == exactly the comments whose quotes were edited away in the fixture
  variant (seed open comments quoting the reworded/deleted content from
  `refined_requirements.v2-edit.collab.md`).
- Idempotent identical-content call: same hash → no new row (Phase 1 behavior preserved).

**`tests/test_archive_retrieval.py` (US5 S3):**
- Three version bumps with a resolve-after-archive scenario: a comment left on v1, resolved during
  v2 — `GET /versions/1` shows it **open** (its state as of v1's archival), `GET /versions/2` shows
  it **resolved**.
- `GET /versions/{n}` on an archived version returns its content + its comments with as-of state.
- **FR-011 folder assertion:** after three bumps, the goal folder contains ONLY
  `refined_requirements.collab.md` + `refined_requirements.html` (no version-suffixed files ever).
- `_state_as_of` pure-helper unit cases (created→resolved→reopened replay at varying cutoffs).

### Validation Scripts (temporary)
```bash
cd cast-server && python -m pytest tests/test_requirement_versions.py tests/test_archive_retrieval.py -q
curl -s -XPOST localhost:8005/api/goals/<slug>/requirements/versions | python -m json.tool
```

### Manual Checks
- Confirm `create_next` calls `create_snapshot` (not a reimplemented insert) — inherits the txn
  discipline and the documented `BEGIN IMMEDIATE` fix-forward.
- Confirm no LLM/subprocess in `create_next` — displacement is pure string-find.

### Success Criteria
- [ ] `create_next` returns the exact contract dict; snapshot + archive-flip in one txn.
- [ ] `displaced_comment_ids` is the verbatim string-find result over the new content.
- [ ] Carry-forward = no row copying; open comments keep their original `version`.
- [ ] `GET /versions/{n}` reconstructs as-of resolution state from `comment_events`.
- [ ] FR-011 folder assertion passes (no second requirements file ever).
- [ ] `POST /versions` reads the file only; missing file → 409.

## Execution Notes

- **The crash-safety property:** a crash between snapshot and the caller's re-anchor dispatch loses
  nothing — displacement is derived; the next `GET /comments` (sp1) recomputes it. Do not add
  durable "displaced" state.
- `create_next` lives in the version service (it is a version operation that *reads* comments via
  `comment_service` — one-directional import, no cycle).
- The as-of reconstruction is the single subtle correctness point — pin it with the three-version
  resolve-after-archive scenario; it is a re-derivable query, never destructive.

**Spec-linked files:** none of this sub-phase's files are covered by
`cast-requirements-render.collab.md` (render route/template/renderer untouched). The `create_next`
semantics + convergence rule are recorded in the spec by sp7.
