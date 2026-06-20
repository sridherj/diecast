# sp3b — post-execution review followup

## B4 classification
**CODING** (classifier rule 1: edits source files `comment_service.py`, `api_requirements.py`,
`api_goals.py`, `api_artifacts.py`, `db/connection.py`, `db/schema.sql`; creates
`comment_layer_inject.py`, `static/comment-bridge.js`; authors pytest + jsdom tests).

## cast-review-code dispatch — UNAVAILABLE in this run
Attempted HTTP dispatch via `/cast-child-delegation` (server reachable, HTTP 200). The trigger
returned **422 "Parent run sp3b not found"**: this sub-phase was executed **directly** (not through
the cast-orchestrate dispatcher), so neither the goal
(`exploration-pipeline-nxm-claude-workflow-9010-angle`) nor the `parent_run_id` is registered in the
cast-server DB. `cast-review-code` also launches an independent terminal-tab session that needs
`external_project_dir` (also unset for this on-disk-only goal). Per the sp-runner Step R.4 contract,
review failure is **recorded, not blocking**.

**Action for a human / orchestrated re-run:** manually run
`/cast-review-code` over the touched files (listed below), or re-run sp3b under `cast-orchestrate`
so a real `parent_run_id` + DB-registered goal exist for HTTP dispatch.

## Files to review
- `cast-server/cast_server/services/comment_service.py` — artifact-keyed resolver
  (`_resolve_artifact_path`, `_resolve_served_render_html`, `_resolve_render_compare_text`),
  `artifact_ref` threaded through `create_comment` / `list_comments` (per-ref cache) / relocate.
- `cast-server/cast_server/routes/api_requirements.py` — optional `artifact_ref` field +
  `_validate_artifact_ref` (route-level traversal/`.html`/absolute guard).
- `cast-server/cast_server/routes/api_goals.py`, `api_artifacts.py` — layer injection + goal-relative ref.
- `cast-server/cast_server/requirements_render/comment_layer_inject.py` (NEW) — pure injector.
- `cast-server/cast_server/static/comment-bridge.js` (NEW) — host bridge (source-identity guard,
  iframe registry, per-comment fan-out, `cch:submit`/`cch:submitted`).
- `agents/cast-comment-html/assets/comment-layer.js` — bridge-mode `submit()` transport.
- `cast-server/cast_server/db/schema.sql` + `db/connection.py` — additive nullable `artifact_ref` column.
- Templates: `markdown_viewer.html` (data-attrs), `base.html` (bridge script), `phase_tab_content.html`,
  `artifact_sidebar.html`.

## Compensating verification performed inline (no browser, no reviewer)
- **Security (source-identity guard):** jsdom test asserts foreign-window rejection, origin NOT
  checked, payload shape-check, reply-to-originator-only — `agents/cast-comment-html/tests/test_comment_bridge.js` (9 assertions green).
- **Path traversal (defense in depth):** route guard + service `_resolve_artifact_path` containment
  both reject `..`/absolute/non-`.html` — server-contract test `test_html_comment_bridge_contract.py::test_bridge_body_rejects_traversal_artifact_ref` (422 on 4 payloads) + a direct service-level traversal assertion.
- **Backward-compat (byte-identical):** `artifact_ref=None` → `refined_requirements.html`; the
  existing 55 comment regression tests + `test_artifact_ref_defaulted_requirements_path_unchanged` are green.
- **Schema migration:** additive nullable column verified via both DB-init paths (init_db split +
  fresh get_connection) and `test_schema_migration.py` (33 green).
- Full suite: **1149 passed** (the only 2 failures — `test_child_delegation` launch-prompt +
  `test_tier_delegation` tmux — fail on the clean tree too; pre-existing, unrelated).
