# Execution Manifest: Threaded `/runs` Page (Recursive Parent/Child Tree)

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:

1. Start a new Claude session in `/data/workspace/diecast`.
2. Tell Claude: "Read `docs/execution/runs-threaded-tree/_shared_context.md` then execute `docs/execution/runs-threaded-tree/spN_<name>/plan.md`."
3. After completion, update the Status column below and commit.

Each sub-phase corresponds to a step from the source plan's "Implementation order" (steps 0–7). Step 0 (one-line `CREATE INDEX`) folds into sp1's data-layer work — index, service function, and unit tests land together so the data layer is shippable in one commit. The full plan ships as one PR.

## Sub-Phase Overview

| #  | Phase                                                                          | File                                | Depends On     | Status      | Notes |
|----|--------------------------------------------------------------------------------|-------------------------------------|----------------|-------------|-------|
| 1  | Data layer: `idx_agent_runs_parent` + `get_runs_tree` + unit tests             | `sp1_data_layer/plan.md`            | —              | Done        | Source steps 0 + 1. Folds the one-line index into the service work. New `test_runs_tree.py`, extended `test_runs_api.py`, `seeded_runs_tree` + `deep_chain_db` fixtures. |
| 2  | Recursive macro + fragment + CSS + BOTH route swaps                            | `sp2_macro_and_routes/plan.md`      | 1              | Done        | Source step 2. New `run_node.html` macro, new `run_status_cells.html` fragment (carries hx-* attrs conditionally), CSS port from mockup, `runs_page` + `list_runs` both call `get_runs_tree`. `list_runs` also negotiates JSON for non-HTMX callers (test compatibility). xfail markers removed; both API tests green. |
| 3  | HTMX status-cells partial endpoint + markup-shape test                         | `sp3_htmx_endpoint/plan.md`         | 2              | Done        | Source step 3. `GET /api/agents/runs/{id}/status_cells` + `test_runs_template.py` (asserts hx-* live on inner cells, not outer node). bs4 added as dev dep. |
| 4  | Inline JS for collapse persistence + clipboard copy                            | `sp4_js_collapse_clipboard/plan.md` | 2              | Done        | Source step 4. `pages/runs.html` only. localStorage key `runs:expanded:<id>`; `⧉` writeText + brief `.copied` flash. |
| 5  | Cleanup: delete legacy fragments / endpoints / unused CSS                      | `sp5_cleanup/plan.md`               | 3, 4           | Done        | Source step 5. DELETE `run_row.html`, `run_children.html`, `/runs/{id}/children`, `/runs/{id}/row`, unused `.run-row*` CSS. **sp5 retry: + recheck/cancel macro fix + `/children` → `/jobs?include=children` migration** (recheck_run + cancel_run_endpoint now render via `run_node` macro returning `.run-group` fragments matching the macro's `hx-target`; legacy `/children` HTML endpoint replaced by JSON `?include=children` query param on `/jobs/{id}`; 3 external callers migrated; dead click handler in `pages/runs.html` lines 75-80 removed). |
| 6  | UI test agent prompt update + `Delegate: /cast-pytest-best-practices`          | `sp6_ui_tests/plan.md`              | 5              | Done | Source step 6. Replace `cast-ui-test-runs` assertions; extend `runner.py` if needed; run `test_full_sweep.py`; lint pass on the new pytest files. |
| 7  | Spec capture via `/cast-update-spec` + registry + cross-link + spec-checker    | `sp7_spec_capture/plan.md`          | 6              | Done | Source step 7. NEW `docs/specs/cast-runs-screen.collab.md` (US1–US9, FR-001..FR-013, SC-001..SC-009, "Removed in this release" subsection); `_registry.md` row added; `cast-ui-testing.collab.md` cross-link added + version bumped 1→2; `bin/cast-spec-checker` clean for both specs; `uv run precommit-tests --suite unit` passes (136 + 96). |

Status: Not Started → In Progress → Done → Verified → Skipped

## Dependency Graph

```
sp1 ──▶ sp2 ──┬──▶ sp3 ──┐
              │           │
              └──▶ sp4 ──┴──▶ sp5 ──▶ sp6 ──▶ sp7
```

No gates. No skip-conditional branches.

## Execution Order

### Sequential Group 1
1. **sp1_data_layer** — index + `get_runs_tree` + unit tests. Pure backend; no UI changes. Independently verifiable: `pytest cast-server/tests/test_runs_tree.py` green proves rollups, rework propagation, depth cap, and rollup-aware status filter work without any template change.

### Sequential Group 2 (after sp1)
2. **sp2_macro_and_routes** — Recursive Jinja macro, status-cells fragment, CSS port from mockup, swap `/runs` page route AND `/api/agents/runs` HTMX list endpoint to `get_runs_tree`. Manual visit shows threaded layout on page 1 AND page 2.

### Parallel Group 3 (after sp2 — independent files)
3. **sp3_htmx_endpoint** — Adds `GET /api/agents/runs/{id}/status_cells` endpoint and `test_runs_template.py` markup-shape guard. Touches `routes/api_agents.py` only (additive) and a new test file.
4. **sp4_js_collapse_clipboard** — Inline JS in `pages/runs.html` only. No overlap with sp3.

### Sequential Group 4 (after sp3 AND sp4)
5. **sp5_cleanup** — Delete legacy fragments + obsolete endpoints + unused CSS. Grep-gated; only proceeds when zero references found.

### Sequential Group 5 (after sp5)
6. **sp6_ui_tests** — Update `cast-ui-test-runs` agent prompt with threaded-layout assertions; run `cast-server/tests/ui/test_full_sweep.py`; then `Delegate: /cast-pytest-best-practices` over `test_runs_tree.py`, the new `test_runs_api.py` cases, and `test_runs_template.py`. Only runs after cleanup so the agent asserts the actually-shipped DOM, not transitional state.

### Sequential Group 6 (after sp6)
7. **sp7_spec_capture** — `Delegate: /cast-update-spec create cast-runs-screen`; verify `_registry.md` row; cross-link from `cast-ui-testing.collab.md`; run `/cast-spec-checker`. Spec is captured AFTER UI tests are green so it records actual shipped behavior.

## Files Touched by More Than One Sub-Phase

| File | Sub-phases | Region split |
|------|-----------|---------------|
| `cast-server/cast_server/routes/api_agents.py` | sp2, sp3, sp5 | sp2 owns the `list_runs` line 222 swap (`get_all_runs` → `get_runs_tree`); sp3 owns the NEW `/runs/{id}/status_cells` endpoint (additive, no edits to existing routes); sp5 deletes the obsolete `/runs/{id}/children` (line 211) and `/runs/{id}/row` (line 234). Sequential dep enforces clean diffs. |
| `cast-server/cast_server/static/style.css` | sp2, sp5 | sp2 appends new threaded styles (`.run-group`, `.run-node`, `.thread`, `.ctx-pill`, `.copy-resume`, etc.); sp5 removes legacy `.run-row*`, `.run-children-container`, `.child-run`, `.child-indent` ONLY after grep confirms zero refs. Sequential dep. |
| `cast-server/cast_server/services/agent_service.py` | sp1 only | sp1 adds `get_runs_tree` + helpers (`_assemble_tree`, `_compute_rollups`, `_propagate_rework`, `_detect_rework`). Existing `get_all_runs` left untouched (other callers remain). |
| `cast-server/cast_server/templates/macros/run_node.html` | sp2 only | NEW file. |
| `cast-server/cast_server/templates/fragments/run_status_cells.html` | sp2 only | NEW file with hx-* attrs (conditional on `run.status in ('running','pending','rate_limited')`). The endpoint that serves this fragment is added in sp3, but the fragment lives with the macro because the macro `{% include %}`s it. |
| `cast-server/cast_server/templates/pages/runs.html` | sp4 only | sp4 appends inline `<script>` block at end of body. No structural changes (header / summary / list shape unchanged). |
| `cast-server/cast_server/templates/fragments/runs_list.html` | sp2 only | sp2 imports `run_node` macro and replaces the per-L1 row rendering. |
| `cast-server/cast_server/templates/fragments/run_row.html` | sp5 only | DELETE after grep confirms zero refs. |
| `cast-server/cast_server/templates/fragments/run_children.html` | sp5 only | DELETE after grep confirms zero refs. |
| `cast-server/cast_server/db/connection.py` | sp1 only | sp1 appends `CREATE INDEX IF NOT EXISTS idx_agent_runs_parent` next to existing `idx_error_memories_agent` at line 137. |
| `cast-server/cast_server/routes/pages.py` | sp2 only | sp2 swaps `runs_page` (lines 175–191) from `get_all_runs(top_level_only=True, ...)` to `get_runs_tree(...)`. |
| `cast-server/tests/conftest.py` | sp1 only | Adds `seeded_runs_tree` (4 trees: happy, rework, deep, leaf) and `deep_chain_db` (12-deep linear chain) fixtures. |
| `cast-server/tests/test_runs_tree.py` | sp1 only | NEW file with 19 unit tests. |
| `cast-server/tests/test_runs_api.py` | sp1 only | EXTENDED with 2 new cases (`test_list_runs_returns_l1_with_descendants`, `test_list_runs_pagination_by_l1_only`). |
| `cast-server/tests/test_runs_template.py` | sp3 only | NEW file (markup-shape guard). |
| `cast-server/tests/ui/agents/cast-ui-test-runs/cast-ui-test-runs.md` | sp6 only | UPDATED with threaded-layout assertions. |
| `cast-server/tests/ui/runner.py` | sp6 only | EXTENDED if the new agent assertions need new selector helpers (clipboard grant, viewport resize). |
| `docs/specs/cast-runs-screen.collab.md` | sp7 only | NEW file produced by `/cast-update-spec`. |
| `docs/specs/_registry.md` | sp7 only | UPDATED row added by `/cast-update-spec` (or manually if not). |
| `docs/specs/cast-ui-testing.collab.md` | sp7 only | UPDATED — adds `cast-runs-screen.collab.md` to "Linked files" cross-reference. |

## Out-of-Manifest

The following plan items intentionally have **no sub-phase**:

- "Out of scope" items (schema columns to cache rollups, `MAX_DESCENDANTS_PER_GROUP` width cap, virtualization, intra-group search, L1 ctx-pill agent-name tinting, action-button `Resume` re-add, `bin/lint-anonymization`) — deferred to follow-up plans.
- Fall-back path for SQLite < 3.8.3 (no `WITH RECURSIVE`) — listed under Risks and triggered only on detection at startup; the plan does not require pre-emptive coding.

## Progress Log

<!-- Update after each sub-phase completes. -->

### 2026-05-01 — sp5 retry (expanded scope)

The initial sp5 run halted at the grep-gate because three live references blocked deletion of `run_row.html` and the `/children` endpoint. The retry resolved all three blockers in a single dispatch:

1. **Recheck/cancel macro fix.** `recheck_run` (`routes/api_agents.py:~207`) and `cancel_run_endpoint` (`~358`) now reuse `get_run_with_rollups` and render via a new thin `fragments/run_group.html` wrapper around the `run_node` macro, matching the macro buttons' `hx-target="closest .run-group"` swap target. This was a latent bug carried forward from sp2/sp4.
2. **`/children` → `/jobs?include=children` migration.** `GET /api/agents/jobs/{id}` accepts an optional `?include=children` query that augments the merged JSON response with the descendant tree (rollups attached) shaped by `get_run_with_rollups`. The 3 legacy callers were migrated: agent test cases (`agents/cast-preso-check-coordinator/tests/test-cases.md` 4 refs), public docs (`cast-server/docs/runs-api.md`), and the prompt-template API listing (`cast-server/cast_server/services/agent_service.py:~1423`). No compatibility shim — one-time migration.
3. **Original sp5 cleanup.** `run_row.html`, `run_children.html`, `GET /runs/{id}/children`, `GET /runs/{id}/row`, the dead click handler in `pages/runs.html` lines 75-80, and the legacy `.run-row*` / `.run-children-container` / `.child-run` / `.child-indent` CSS blocks were all deleted. Orphaned helper `get_children_runs` removed (no remaining callers).

Verification: `uv run precommit-tests --suite unit` — 136 passed, 1 skipped (server-side suite); 96 passed, 7 deselected (cast-server suite).
