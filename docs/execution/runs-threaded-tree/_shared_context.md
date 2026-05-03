# Shared Context: Threaded `/runs` Page (Recursive Parent/Child Tree)

## Source Documents
- Plan: `<DIECAST_ROOT>/docs/plan/2026-05-01-cast-runs-threaded-tree.collab.md`
- Visual mockup (locked source of truth): `<DIECAST_ROOT>/docs/plan/mockups/runs-threaded.html`
- Plan-review verdict: cast-plan-review BIG (16 issues raised, all resolved into the plan's Decisions block). Implementation proceeds without re-litigation.

## Project Background

Today's `/runs` page only renders top-level (L1) runs. Children are lazy-fetched on expand and rendered through a separate flat template (`run_children.html`). This produces five concrete defects:

1. Multi-level orchestrations (e.g. `cast-preso-orchestrator` → `check-coordinator` → `content-checker`) cannot show their structure.
2. Rework loops (a child agent re-run after a checker rejection) appear as unrelated rows.
3. Failed grandchildren are invisible from the L1 row.
4. The 3s HTMX poll swaps the entire row's `outerHTML`, wiping any expand state.
5. The row layout is a single overloaded flex line; long agent names squeeze the goal/task off-screen on narrow viewports.

The redesign delivers **one screen, eagerly loaded per page**, where you can scan nested orchestrations end-to-end, spot the row that broke, and copy a resume command without expanding anything.

## Codebase Conventions

- **Service layer** (`cast-server/cast_server/services/agent_service.py`) holds query functions like `get_all_runs`. Routes are thin wrappers; templates render the dicts produced by services. The new `get_runs_tree` lives next to `get_all_runs` and follows the same `_row_to_dict` shape.
- **Schema-first DB** (`cast-server/cast_server/db/schema.sql`). All required fields for this redesign already exist on `agent_runs`. No Alembic migration. The single new index is added via `CREATE INDEX IF NOT EXISTS` in `connection.py` next to the existing `idx_error_memories_agent` precedent at line 137.
- **Routes split per resource.** Run endpoints live in `cast-server/cast_server/routes/api_agents.py` (NOT `routes/api.py` — the plan's references have been corrected). The page route for `/runs` lives in `cast-server/cast_server/routes/pages.py`.
- **Templates use Jinja with macros and fragments.** `templates/macros/` for re-usable rendering primitives; `templates/fragments/` for HTMX-swappable partials; `templates/pages/` for top-level page templates that include both. The recursive node renderer is a macro using direct self-recursion (no self-import — standard Jinja idiom).
- **HTMX swap-target precision matters.** Polling targets must live on inner state-only spans, never on outer container nodes that carry user-managed state (expand class, focus, etc.). The plan adds a markup-shape unit test as a structural guard.
- **`docs/specs/`** holds Spec-Aligned Verification (SAV) docs. New non-trivial public contracts (data shape, behavior, semantics) get a spec at the end of the implementation. The plan's step 7 captures `cast-runs-screen.collab.md` only after UI tests are green so the spec records actually-shipped behavior.
- **UI tests are agent-driven.** The harness in `cast-server/tests/ui/` is screen-based: `cast-ui-test-orchestrator` dispatches per-screen test agents. Each agent drives Playwright via `cast-server/tests/ui/runner.py`; results aggregate through the structured `output.json` contract by `tests/ui/test_full_sweep.py`. Pytest-style UI tests are NOT used here.

## Key File Paths

| File | Role |
|------|------|
| `cast-server/cast_server/db/connection.py` | Adds `CREATE INDEX IF NOT EXISTS idx_agent_runs_parent` (sp1) at the existing index precedent at line 137. |
| `cast-server/cast_server/services/agent_service.py` | Adds `get_runs_tree(...)` + helpers `_assemble_tree`, `_compute_rollups`, `_propagate_rework`, `_detect_rework` (sp1). Tree path skips parsing of `input_params`/`output`/`artifacts`/`directories` on the row — only `context_usage` is parsed (for `ctx_class`). |
| `cast-server/cast_server/routes/pages.py` | `runs_page` (lines 175–191) swaps `get_all_runs(top_level_only=True, ...)` → `get_runs_tree(...)` (sp2). |
| `cast-server/cast_server/routes/api_agents.py` | (sp2) `list_runs` (line 222) swaps to `get_runs_tree`; (sp3) NEW `GET /api/agents/runs/{id}/status_cells`; (sp5) DELETE `/runs/{id}/children` (line 211) and `/runs/{id}/row` (line 234). |
| `cast-server/cast_server/templates/macros/run_node.html` | NEW (sp2). Single recursive macro `render_run(run, depth=0)` using direct self-recursion. |
| `cast-server/cast_server/templates/fragments/run_status_cells.html` | NEW (sp2). The line-2 cells: status pill + ctx pill + rollup + duration + cost + (⧉ static) + time-ago. Wrapper id = `run-cells-{{ run.id }}`. Carries hx-* attrs conditionally on `run.status in ('running', 'pending', 'rate_limited')`. |
| `cast-server/cast_server/templates/fragments/runs_list.html` | sp2 imports the `run_node` macro and replaces the per-L1 row render. |
| `cast-server/cast_server/templates/pages/runs.html` | sp4 appends inline `<script>` block (collapse persistence + clipboard). No structural changes. |
| `cast-server/cast_server/static/style.css` | sp2 appends threaded styles (port from mockup); sp5 removes unused legacy classes. |
| `cast-server/tests/conftest.py` | sp1 adds `seeded_runs_tree` + `deep_chain_db` fixtures. |
| `cast-server/tests/test_runs_tree.py` | NEW (sp1). 19 unit tests covering get_runs_tree behavior. |
| `cast-server/tests/test_runs_api.py` | sp1 adds 2 new cases for HTMX-pagination behavior. |
| `cast-server/tests/test_runs_template.py` | NEW (sp3). Markup-shape guard. |
| `cast-server/tests/ui/agents/cast-ui-test-runs/cast-ui-test-runs.md` | sp6 replaces flat-runs assertions with threaded-layout assertions. |
| `cast-server/tests/ui/runner.py` | sp6 extends if new selectors / clipboard grant / viewport resize helpers are needed. |
| `docs/specs/cast-runs-screen.collab.md` | NEW (sp7) via `/cast-update-spec create cast-runs-screen`. |
| `docs/specs/_registry.md` | sp7 adds the new spec's row. |
| `docs/specs/cast-ui-testing.collab.md` | sp7 adds `cast-runs-screen.collab.md` to "Linked files". |

**Files to delete in sp5:**
- `cast-server/cast_server/templates/fragments/run_row.html`
- `cast-server/cast_server/templates/fragments/run_children.html`
- `GET /api/agents/runs/{id}/children` (`api_agents.py:211`)
- `GET /api/agents/runs/{id}/row` (`api_agents.py:234`)
- Unused `.run-row*`, `.run-children-container`, `.child-run`, `.child-indent` CSS in `static/style.css` (only after grep confirms zero refs).

## Data Schemas & Contracts

### `get_runs_tree(...)` return shape

```python
def get_runs_tree(
    status_filter: str | None = None,
    page: int = 1,
    per_page: int = 25,
    exclude_test: bool | None = None,
    db_path=None,
) -> dict:
    """Return paginated L1 runs with full descendant trees attached.

    Each run dict includes:
        children: list[run]                # ordered by created_at ASC
        descendant_count: int              # total subtree size (excludes self)
        failed_descendant_count: int       # count where status in (failed, stuck)
        rework_count: int                  # propagated up to all ancestors
        status_rollup: str                 # max-severity status across self+descendants
        total_cost_usd: float              # sum of self + descendants
        wall_duration_seconds: int | None  # L1 only: completed_at - started_at
        ctx_class: str | None              # 'low' | 'mid' | 'high'
        is_rework: bool                    # set on children only
        rework_index: int | None           # 2,3,... for 2nd+ attempt
    """
```

Returns `{"runs": [...L1 with children attached...], "total": int, "page": int, "per_page": int, "pages": int}`.

### Severity ordering for `status_rollup` (Decision #4 in plan; locked)

```
failed > stuck > rate_limited > running > pending > scheduled > completed
```

### Ctx thresholds (Decision #4 in plan; locked)

```
< 40        → 'low'   (green)
40 ≤ x < 70 → 'mid'   (amber)
≥ 70        → 'high'  (red)
```

`ctx_class = None` when `context_usage` is missing or lacks both `total` and `limit`.

### Rework detection rule (Decision #8 in plan; locked)

For each parent, walk children in `created_at ASC`. Per child, key = `(agent_name, task_id)`. If the same key has appeared before in the same parent's children, set `is_rework=True` and `rework_index=count` (starts at 2 for the second instance). After all per-parent detection, run a post-order DFS to sum every descendant's `rework_count` into each ancestor — so an L1's rollup pill reflects reworks anywhere in its tree.

### HTMX swap-target rule (locked)

`hx-*` attributes (`hx-get`, `hx-trigger`, `hx-swap`) live on `.run-status-cells` (the inner span), NEVER on the outer `.run-node`. The outer node carries expand state and must survive 3s polls. The structural unit test in `test_runs_template.py` enforces this and exists *because* the existing flat template regresses on this exact line.

### Collapse persistence key format

`localStorage["runs:expanded:<run_id>"] = "1"` — presence means expanded; absence means collapsed. No JSON serialization. Reapplied on `htmx:afterSwap` for nodes that survive a partial swap (only relevant if a future change widens the swap).

### Depth cap

Recursive CTE has `WHERE depth < 10`. Trees deeper than 10 are silently truncated; server logs a "tree truncated" warning so we can spot runaway agent loops in production.

### Status filter semantics (Decision #13 in plan; locked)

`?status=failed` filters on `status_rollup`, NOT raw L1 `status`. So an L1 whose own `status='completed'` but with a failed descendant DOES match `?status=failed`. Without this rule, the rollup pill would surface failures the filter cannot find.

### Wall-clock duration (Decision #14 in plan; locked)

L1 line-2 duration is wall-clock = `completed_at - started_at` (None for not-yet-completed L1s; line-2 falls back to "started Xm ago"). Children show their own `active_seconds` (existing field). Wall-clock prevents fan-out double-counting.

## Pre-Existing Decisions

(Verbatim from the plan's "Locked design decisions" table and "Decisions" block. Sub-phases reference these by `Decision #N`.)

| # | Decision | Locked Reason |
|---|----------|---------------|
| 1  | Threaded layout, single rail per group; no per-depth horizontal indent of row content | Mobile readability; avoids `└─` ASCII art |
| 2  | Two lines per node: identity (status dot + agent name + crumbs), telemetry (status pill + ctx pill + rollup + duration + cost + ⧉ + time-ago) | "Two lines without expansion is fine" |
| 3  | Eager-load full tree per page (25 L1 / page; descendants always fetched) | Required for rollups, rework detection, coherent line-2 |
| 4  | Ctx promoted to a pill at status-pill prominence, immediately after the status pill; thresholds `<40` low / `40–70` mid / `70+` high | "Is the agent in trouble" is as critical as "did it succeed" |
| 5  | Child agent-name color tracks ctx threshold (children only; L1 names stay default) | Ambient at-a-distance scanning of hot children |
| 6  | Copy-resume `⧉` button on every row's line 2 (not gated on status) | Resume is a routine action, not a failure-recovery one |
| 7  | Goal/task crumbs muted gray, hover → accent + underline | Eliminates red-vs-danger color collision |
| 8  | Rework detection: consecutive same `(agent_name, task_id)` siblings get `↻ rework #N` (purple); count propagates to ancestors | Surfaces preso-style check → reject → re-run loops at any depth |
| 9  | L1 rollup pills show `N steps`, `⚠ K reworked` (amber) / `⚠ K failed` (red), totals; non-leaf children also get rollup pills | Failure visibility on parent without expansion |
| 10 | Group border conveys group status: solid red = unresolved failure, amber = recovered failure (rework only), none = healthy | Single-glance group health |
| 11 | L3 (expansion) holds artifacts, summary, error, full segmented context bar, action buttons; Resume button REMOVED from expansion (replaced by line-2 ⧉) | Avoid duplication |
| 12 | No Alembic migration — existing schema covers all fields. One new index via init-script `CREATE INDEX IF NOT EXISTS` | Required fields exist; index closes the real perf gap |
| 13 | Status filter uses `status_rollup`, not raw L1 status | L1 rollup pill must be findable by the filter |
| 14 | L1 line-2 duration shows wall-clock, NOT summed active seconds | Summing concurrent fan-out double-counts wall time |

## Relevant Specs

| Spec | Linked files overlap | Sub-phase(s) |
|------|---------------------|---------------|
| `docs/specs/cast-ui-testing.collab.md` | `cast-server/tests/ui/runner.py`, `cast-server/tests/ui/agents/cast-ui-test-runs/` | sp6 (UI test agent prompt) and sp7 (cross-link added to "Linked files") |
| `docs/specs/cast-runs-screen.collab.md` | NEW — produced by sp7 | sp7 only |
| (other specs) | None of the targeted files appear in another spec's `linked_files`. |

If a sub-phase modifies `tests/ui/runner.py`, read `docs/specs/cast-ui-testing.collab.md` and verify SAV behaviors are preserved. Sp6 extends runner.py only with additive primitives (clipboard grant, viewport resize) — no semantic changes to existing helpers.

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|-----------|------|-----------|--------|-------------------|
| sp1 — Data layer (index + service + unit tests) | Sub-phase | — | sp2 | — |
| sp2 — Macro + fragment + CSS + route swaps | Sub-phase | sp1 | sp3, sp4 | — |
| sp3 — HTMX status-cells endpoint + markup-shape test | Sub-phase | sp2 | sp5 | sp4 |
| sp4 — Inline JS (collapse + clipboard) | Sub-phase | sp2 | sp5 | sp3 |
| sp5 — Cleanup (legacy fragments / endpoints / CSS) | Sub-phase | sp3, sp4 | sp6 | — |
| sp6 — UI test agent prompt + pytest-best-practices delegation | Sub-phase | sp5 | sp7 | — |
| sp7 — Spec capture + registry + cross-link + spec-checker | Sub-phase | sp6 | (none) | — |

No gates. No skip-conditional sub-phases.

## Open / Deferred Items

- **SQLite version fallback**: if a deployment ships SQLite < 3.8.3 (no `WITH RECURSIVE`), an iterative two-query fetch is the fallback. Detection at startup via `sqlite3.sqlite_version_info`. The current dev environment runs sqlite3 3.50.4; pre-emptive coding is not required.
- **Width cap (`MAX_DESCENDANTS_PER_GROUP`)**: deferred until observed bloat. Depth cap (10) is in scope here; width cap is not.
- **localStorage key explosion**: cap at 500 keys deferred until observed. One key per expanded run.
