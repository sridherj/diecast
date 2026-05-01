# Diecast Scope-Prune

> Status: complete. Second pass (sp13) executed 2026-04-30 — stubs deleted, callers fixed.

## 1. Why

Diecast scope (per Phase 3b plan §7 outcome) excludes the following surfaces inherited from the upstream fork:

- News pipeline (digest generation, news page, news API).
- Goal Detector (scratchpad → goal-suggestion subprocess loop).
- File-based sync engine (full + incremental sync of scratchpad and agent registry into SQLite).
- Cron, hooks, n8n, RemoteTrigger, startup pipeline, LinkedIn, reachout.

The first scope-prune pass (this sub-phase, sp2) replaces these surfaces with `NotImplementedError` stubs and removes their wiring from `app.py`. Import statements remain live so any forgotten caller fails loudly with a clear error rather than silently no-opping. The second pass (sp13) deletes the files and folders entirely once the brand sweep, import rename, and feature work have all moved past them.

## 2. First pass (sp2 — stub)

These files keep their public symbol names but every public function raises:

```
NotImplementedError("removed in Diecast scope-prune; see docs/scope-prune.md")
```

Stubbed files:

- `cast-server/routes/api_news.py` — `router` symbol still exported; `generate_digest`, `digest_status` raise.
- `cast-server/sync/engine.py` — `full_sync`, `incremental_sync` raise.
- `cast-server/news_digest/__init__.py` — empty marker.
- `cast-server/news_digest/runner.py` — `run_digest_generator`, `get_digest_status` raise.
- `cast-server/goal_detector/__init__.py` — left empty (no public symbols imported externally).
- `cast-server/goal_detector/runner.py` — `run_detector`, `get_detector_status` raise.
- `cast-server/goal_detector/detector.py` — `slugify`, `extract_intent_lines`, `build_detector_prompt`, `parse_detector_output`, `ensure_intent_suggestions` raise.

`app.py` changes in sp2:

- `FastAPI(title="Task OS"...)` → `FastAPI(title="Diecast"...)`.
- Lifespan no longer calls `full_sync()`.
- Lifespan log strings rebranded ("Starting Task OS" → "Starting Diecast").
- `sync_middleware` removed entirely (no per-request `incremental_sync()` hook).
- `from cast_server.routes.api_news import router as api_news_router` import removed.
- `app.include_router(api_news_router)` removed.

Templates / page routes:

- `cast-server/templates/base.html` — News `<li>` removed from the nav (anchored by `href="/news"`).
- `cast-server/routes/pages.py` — `/news` GET handler removed; `DIGESTS_DIR` import dropped.

Stale callers that still reference stubbed modules (and will therefore raise `NotImplementedError` at runtime if exercised, by design):

- `cast-server/routes/api_sync.py` — `POST /api/sync` calls `full_sync()`.
- `cast-server/routes/api_goals.py` — goal-detector trigger + status endpoints call `run_detector`/`get_detector_status`.

These callers stay untouched in sp2 to keep imports parsing cleanly. sp13 deletes them along with the stubs.

## 3. Second pass (sp13 — delete)

When sp13 runs, delete these files and folders entirely. Update all callers in the same change so no stale imports remain:

- `cast-server/routes/api_news.py`
- `cast-server/routes/api_sync.py`
- `cast-server/sync/` (directory — `engine.py`, `parsers/`, `__init__.py`)
- `cast-server/news_digest/` (directory)
- `cast-server/goal_detector/` (directory)
- `cast-server/templates/pages/news.html`
- `cast-server/templates/fragments/news_status.html`

In `cast-server/routes/api_goals.py`:

- Remove `from cast_server.goal_detector.runner import run_detector, get_detector_status`.
- Remove the goal-detector trigger endpoint and `detector_status` endpoint.

In `cast-server/app.py`:

- Remove `from cast_server.routes.api_sync import router as api_sync_router` and the corresponding `app.include_router(...)`.

## 4. Pin-to-zero list

After Diecast Phase 3b ships, none of these strings may reappear inside `cast-server/` (CI lint enforces):

- `news`
- `cron`
- `n8n`
- `RemoteTrigger`
- `linkedin`
- `reachout`
- `hook`

Exceptions are documented in §5 (anonymization lint exception window) and removed by sp13.

## 5. Anonymization lint exception window

`bin/anonymization-lint` (Phase 2) currently flags any non-public name in committed artifacts. During the sp2 → sp13 window, these stubbed modules legitimately carry the strings "news", "goal_detector", "sync", etc. in module docstrings and the `_REMOVED_MSG` constant. Add the following entries to the lint exception list during this window:

- `cast-server/routes/api_news.py`
- `cast-server/sync/`
- `cast-server/news_digest/`
- `cast-server/goal_detector/`

sp13 removes these exception entries explicitly when the corresponding files are deleted (per CQ2 / risk row 7 plan-review fix).

## 6. References

- Phase 3b detailed plan (upstream-private — not shipped in this repo).
- Phase 3b shared context: `docs/execution/diecast-open-source/phase-3b/_shared_context.md`
- Sub-phase 2 plan: `docs/execution/diecast-open-source/phase-3b/sp2_stub_prune/plan.md`
- Sub-phase 13 plan: `docs/execution/diecast-open-source/phase-3b/sp13_second_prune/plan.md`

## 7. Final delete pass (sp13 — 2026-04-30)

Deleted in this pass:

- `cast-server/cast_server/news_digest/` (directory + contents).
- `cast-server/cast_server/goal_detector/` (directory + contents).
- `cast-server/cast_server/sync/` (directory + contents — `engine.py`, `parsers/`, `__init__.py`).
- `cast-server/cast_server/routes/api_news.py`.
- `cast-server/cast_server/routes/api_sync.py`.
- `cast-server/cast_server/templates/pages/news.html`.
- `cast-server/cast_server/templates/fragments/news_status.html`.

Caller fixes:

- `cast-server/cast_server/app.py` — removed `api_sync_router` import + `app.include_router(api_sync_router)`.
- `cast-server/cast_server/routes/api_goals.py` — removed `from cast_server.goal_detector.runner import run_detector, get_detector_status`, the unused `asyncio` import, the `POST /api/goals/detector/run` endpoint, and the `GET /api/goals/detector/status` endpoint.
- `cast-server/cast_server/templates/pages/dashboard.html` — removed the "Detect Goals" button and `#detector-status` placeholder div from the Goal Suggestions sidebar section. The section continues to render any pending suggestions persisted in `goal_suggestions` (which are no longer auto-generated; the table stays for backward compatibility with any legacy rows and for future manual seeding).

Lint exceptions removed:

- §5 documented entries for `cast-server/news_digest/`, `goal_detector/`, `sync/`, `routes/api_news.py` were never wired into `bin/lint-anonymization` (the script ships a closed `FORBIDDEN_PATTERNS` list with no per-path exclusions), so there is nothing to remove here. The pin-to-zero list (§4) is now enforced solely via grep sweep — see Phase 3b sp13 verification.

Pin-to-zero list (§4) remains active forever:

- `news`, `cron`, `n8n`, `RemoteTrigger`, `linkedin`, `reachout`, `hook`.
