# Plan: Threaded `/runs` page with recursive parent/child tree

**Date:** 2026-05-01
**Status:** Locked, reviewed (cast-plan-review BIG, 16 issues resolved), ready for execution
**Visual source of truth:** `docs/plan/mockups/runs-threaded.html`

## Context

The current `/runs` page renders only top-level (L1) runs. Children are
lazy-fetched on expand and rendered in a separate flat template
(`run_children.html`), so:

- Multi-level orchestrations (e.g. `cast-preso-orchestrator` →
  `check-coordinator` → `content-checker`) cannot show their structure.
- Rework loops (a child agent re-run after a checker rejection) appear as
  unrelated rows.
- Failed grandchildren are invisible from the L1 row.
- The expand toggle drops collapse state on every 3s HTMX poll because the
  whole row is swapped.
- Parent and child rows look visually identical — hard to scan.
- The row layout is one overloaded flex line; long agent names squeeze the
  goal/task off-screen on narrow viewports.

Second-brain had a similar implementation with all the same defects.

We want **one screen**, **eagerly loaded per page**, that lets you scan
nested orchestrations end-to-end, spot the row that broke, and copy a
resume command without expanding anything.

## Locked design decisions (from design phase)

These were aligned with the user during mockup review. Do not relitigate
during implementation.

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **Threaded layout, single rail per group** — no per-depth horizontal indent of row content. A vertical 2px rail binds parent → children. Recursive children get their own rail nested inside. | Keeps deep trees readable on mobile; avoids `└─` ASCII art. |
| 2 | **Two lines per node.** Line 1 = identity (status dot + agent name + goal · task). Line 2 = telemetry (status pill + ctx pill + rollup + duration + cost + ⧉ + time-ago). | Matches user's "two lines without expansion is fine." |
| 3 | **Eager-load full tree per page** (25 L1 per page; descendants always fetched). | Required for rollups, rework detection, and a coherent L1 line-2. |
| 4 | **Ctx promoted to a pill at status-pill prominence**, sitting *immediately* after the status pill. Thresholds: `<40` green (`low`), `40–70` amber (`mid`), `70+` red (`high`). | "Is the agent in trouble" is as critical as "did it succeed." |
| 5 | **Child agent-name color tracks ctx threshold** (green/amber/red). L1 names stay default (parents have rollup pills + group border for status). | Ambient at-a-distance scanning of hot children in deep trees. |
| 6 | **Copy-resume `⧉` button on every row's line 2**, not gated on status. Click copies `resume_command` to clipboard; brief "copied" flash. | Resume is a routine action, not a failure-recovery one. |
| 7 | **Goal/task crumbs are muted gray**, hover transitions to accent + underline. | Eliminates the red-vs-danger color collision the user flagged. |
| 8 | **Rework detection**: consecutive siblings under the same parent with the same `(agent_name, task_id)` get `↻ rework #N` tag (purple), starting at #2 for the second instance. `rework_count` propagates up to ancestors so L1 sees total reworks anywhere in its tree. | Surfaces preso-style check → reject → re-run loops at any depth. |
| 9 | **L1 rollup pills** show `N steps`, `⚠ K reworked` (amber) or `⚠ K failed` (red), and totals. Children that themselves have descendants also get rollup pills. | Failure visibility on the parent without expansion. |
| 10 | **Group border conveys group status**: solid red = unresolved failure, amber = recovered failure (rework only), none = healthy. | Single-glance group health. |
| 11 | **L3 (expansion)** holds: artifacts, summary, error, full segmented context bar with breakdown, action buttons (`Open run`, `View transcript`, `Recheck`, `Cancel`). The **Resume button is removed** from expansion (replaced by the line-2 `⧉`). | Avoid duplication. |
| 12 | **No Alembic migration**: existing schema covers all fields. One new index (`idx_agent_runs_parent`) added via init-script `CREATE INDEX IF NOT EXISTS` following the existing precedent in `connection.py:137`. All rollups computed at query time. | Required fields already exist; the index closes the real perf gap surfaced in #13 below. |
| 13 | **Status filter uses `status_rollup`, not raw L1 status.** A search for `?status=failed` returns L1s with any failed descendant, not just L1s whose own status is failed. | Without this, the L1 rollup pill would surface failures that the filter cannot find. |
| 14 | **L1 line-2 duration shows wall-clock** (`completed_at − started_at`), not summed active seconds. Children show their own active seconds. | Summing concurrent fan-out double-counts wall time and over-reports orchestrator work. |

## Architecture

### Data layer

Existing schema covers all fields. One new index — added at server init:

```sql
CREATE INDEX IF NOT EXISTS idx_agent_runs_parent ON agent_runs(parent_run_id)
```

Add to `cast-server/cast_server/db/connection.py` next to `idx_error_memories_agent` (line 137). Index auto-creates on next server start; no Alembic migration.

### Backend service: new `get_runs_tree`

**File:** `cast-server/cast_server/services/agent_service.py`

Add a new function alongside the existing `get_all_runs`:

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
        children: list[run]              # ordered by created_at ASC
        descendant_count: int
        failed_descendant_count: int
        rework_count: int                # propagated up to all ancestors
        status_rollup: str               # max-severity status across self+descendants
        total_cost_usd: float            # self + descendants
        wall_duration_seconds: int | None  # L1 only: completed_at - started_at
        ctx_class: str | None            # 'low' | 'mid' | 'high'
        is_rework: bool                  # set on children only
        rework_index: int | None         # 2,3,... for 2nd+ attempt
    """
```

Implementation:

1. **Page L1 ids**: `SELECT id FROM agent_runs WHERE parent_run_id IS NULL [+ filters that operate on L1's own status, in addition to a tree-wide status_rollup match — see step 7] ORDER BY created_at DESC LIMIT ? OFFSET ?`.
2. **Tree fetch (recursive CTE, depth-capped)**:
   ```sql
   WITH RECURSIVE tree AS (
     SELECT ar.*, 0 AS depth FROM agent_runs ar WHERE ar.id IN (?,?,...)  -- page L1 ids
     UNION ALL
     SELECT ar.*, tree.depth + 1
     FROM agent_runs ar JOIN tree ON ar.parent_run_id = tree.id
     WHERE tree.depth < 10
   )
   SELECT … FROM tree
   ```
   Depth cap of 10 protects against runaway agent loops; beyond 10 is almost certainly a bug. Truncated trees log a server-side warning so we can spot them.
3. **Enrichment**: LEFT JOIN goals + tasks (same as current `get_all_runs`).
4. **Tree assembly (Python)**: build `id → run` dict, attach `children` lists, sort each level by `created_at ASC`.
5. **Trim parsed JSON columns on the tree path.** `_row_to_dict` parses `input_params`, `output`, `artifacts`, `directories`, `context_usage` — but the line-2 row only needs `context_usage` (for `ctx_class`). Defer the others to detail-render or expand. Keeps tree-fetch payload + parse cost lean.
6. **Rollup compute (Python, post-order DFS per L1 root)**:
   - `descendant_count` = sum of subtree sizes
   - `failed_descendant_count` = count where status in (`failed`, `stuck`)
   - `total_cost_usd` = sum of self + descendant `cost_usd`
   - `wall_duration_seconds` (L1 only) = `completed_at − started_at` (None for not-yet-completed L1s; line-2 falls back to "started Xm ago")
   - `status_rollup` = max severity (severity order: `failed` > `stuck` > `rate_limited` > `running` > `pending` > `scheduled` > `completed`)
   - `ctx_class` = bucket of `context_usage.total / context_usage.limit` if both present (None otherwise)
7. **Status-filter on rollup**: when `status_filter` is set, after rollups are computed, filter the L1 list to those with `status_rollup == status_filter`. (Doing it post-rollup is simpler than re-expressing as SQL; cost is bound by 25 L1 per page.)
8. **Rework detection**: per parent, walk children in `created_at ASC` order. For each child, key = `(agent_name, task_id)`. If key seen before, increment counter; set `is_rework=True`, `rework_index=count`. Then post-order DFS sums all descendant `rework_count` into each ancestor so L1's pill reflects the whole tree.

Returns `{"runs": [...L1 with children attached...], "total": int, "page": int, "per_page": int, "pages": int}`.

### Backend routes — both `/runs` and the pagination API

Two routes change. Both use `get_runs_tree`:

1. **`/runs` page route** (`cast-server/cast_server/routes/pages.py:175-191`): replace `get_all_runs(top_level_only=True, ...)` with `get_runs_tree(...)`.
2. **`/api/agents/runs` list endpoint** (`cast-server/cast_server/routes/api_agents.py:222-232`, the HTMX pagination handler called by `runs_list.html`): same swap. Without this, paginating to page 2 silently reverts to flat top-level rendering.

Other context (summary, escalated agents, pagination shape) stays as-is.

**Obsolete endpoints to delete** (in step 5 cleanup, after the new path is shipped):

- `GET /api/agents/runs/{id}/children` (`api_agents.py:211`) — no longer needed; children come pre-loaded.
- `GET /api/agents/runs/{id}/row` (`api_agents.py:234`) — superseded by the new `/status_cells` endpoint below.

### HTMX poll-safe partial endpoint

**Problem:** today the row polls `every 3s` and swaps `outerHTML` of the whole row, wiping expand state.

**Fix:** poll only the mutable line-2 cells.

**New file:** `cast-server/cast_server/templates/fragments/run_status_cells.html`

Renders just the chunk: status pill + ctx pill + rollup + duration + cost + (⧉ static) + time-ago. Wrapper element id = `run-cells-{{ run.id }}`.

**New endpoint:** add `GET /api/agents/runs/{run_id}/status_cells` to `cast-server/cast_server/routes/api_agents.py` (alongside the existing run endpoints — file is already split per-resource; nothing new to register). Returns the partial.

In `run_node.html` (the macro), the `.run-status-cells` div carries:

```jinja
{% if run.status in ('running', 'pending', 'rate_limited') %}
  hx-get="/api/agents/runs/{{ run.id }}/status_cells"
  hx-trigger="every 3s"
  hx-swap="outerHTML"
{% endif %}
```

Group container, expand state, thread rail, and the run-node click handler are untouched by polls. **A markup-shape unit test (see Tests §) asserts these `hx-*` attributes live on the inner cells span, NOT on the outer `.run-node` — guards against future refactors silently regressing the swap target.**

### Templates

**New: `cast-server/cast_server/templates/macros/run_node.html`**

Single recursive Jinja macro. Direct self-recursion within the same file (no self-import).

```jinja
{% macro render_run(run, depth=0) %}
<div class="run-node {{ 'is-child' if depth > 0 }} ctx-{{ run.ctx_class or 'none' }}"
     data-run-id="{{ run.id }}">
  <div class="row-1">…status dot, agent name, crumbs, caret…</div>
  {% include "fragments/run_status_cells.html" %}
</div>

{% if run.children %}
<div class="thread {{ 'has-failure' if run.failed_descendant_count and not run.rework_count }}{{ ' has-warning' if run.rework_count and not run.failed_descendant_count }}">
  {% for child in run.children %}
    {{ render_run(child, depth + 1) }}
  {% endfor %}
</div>
{% endif %}

<div class="detail" id="run-detail-{{ run.id }}">…artifacts, summary, error, full ctx bar, actions…</div>
{% endmacro %}
```

**Update: `cast-server/cast_server/templates/fragments/runs_list.html`**

`{% import "macros/run_node.html" as rn %}` at the top, then `{{ rn.render_run(run) }}` for each L1 inside the list loop.

**Delete (step 5):**
- `cast-server/cast_server/templates/fragments/run_row.html`
- `cast-server/cast_server/templates/fragments/run_children.html`

(Verify no other refs via `grep -rn "run_row\|run_children" cast-server/cast_server/templates/`.)

**Update: `cast-server/cast_server/templates/pages/runs.html`**

Body unchanged in shape (page header, summary cards, list). Add inline `<script>` block at end for collapse persistence + clipboard copy (see JS section).

### CSS additions

**File:** `cast-server/cast_server/static/style.css`

Port the styles from the mockup `<style>` block verbatim. Specifically:

- `.run-group`, `.run-group.has-failure`, `.run-group.has-warning`
- `.run-node`, `.run-node.is-child`, `.run-node.expanded`
- `.row-1`, `.row-2`
- `.status-dot.{completed,running,failed,pending,rate}`
- `.agent-name` and the `is-child.ctx-{low,mid,high} .agent-name` tints
- `.crumbs .goal` (muted, hover accent + underline)
- `.pill.{completed,running,failed,pending,rate}` (keep existing if present, verify)
- `.ctx-pill.{low,mid,high}` (NEW)
- `.rollup`, `.rollup.bad`, `.rollup.warn`
- `.copy-resume`, `.copy-resume.copied`
- `.rework-tag`
- `.thread`, `.thread.has-failure`, thread `::before` connector
- `.detail`, `.ctx-bar`, `.ctx-seg.{system,memory,agents,messages}`, `.ctx-legend`
- Mobile media query (`max-width: 600px` hides `.relative-time` and `.task`)

**Cleanup:** remove old `.run-row*`, `.run-children-container`, `.child-run`, `.child-indent` classes from `style.css` IF nothing else references them. Check first via `grep -rn "run-row\|run-children\|child-run\|child-indent" cast-server/cast_server/templates/`.

### JS (inline in `pages/runs.html`)

Two small modules, no dependencies:

**1. Collapse persistence:**

```javascript
// On click anywhere in a .run-node (but not on .copy-resume or links):
//   toggle .expanded; localStorage.setItem('runs:expanded:' + runId, '1') or removeItem
// On page load AND on htmx:afterSwap event:
//   for each .run-node[data-run-id], if localStorage flag set, add .expanded
```

Survives HTMX polls because `.expanded` lives on `.run-node`, not on the swapped `.run-status-cells` child.

**2. Copy-resume:**

```javascript
// On .copy-resume click:
//   e.stopPropagation();  // don't expand the row
//   navigator.clipboard.writeText(btn.dataset.cmd);
//   btn.classList.add('copied'); setTimeout(remove, 1100);
```

## Files

| Path | Change |
|------|--------|
| `cast-server/cast_server/db/connection.py` | Add `CREATE INDEX IF NOT EXISTS idx_agent_runs_parent` next to existing index pattern at line 137 |
| `cast-server/cast_server/services/agent_service.py` | Add `get_runs_tree(...)` + helpers (`_assemble_tree`, `_compute_rollups`, `_propagate_rework`, `_detect_rework`); ensure tree path skips parsing of `input_params`/`output`/`artifacts`/`directories` on the row |
| `cast-server/cast_server/routes/pages.py` | `runs_page` route uses `get_runs_tree` |
| `cast-server/cast_server/routes/api_agents.py` | (a) `list_runs` (line 222) uses `get_runs_tree`; (b) NEW endpoint `GET /api/agents/runs/{id}/status_cells`; (c) DELETE `/runs/{id}/children` (line 211) and `/runs/{id}/row` (line 234) in step 5 |
| `cast-server/cast_server/templates/pages/runs.html` | Add inline JS for collapse + clipboard |
| `cast-server/cast_server/templates/fragments/runs_list.html` | Import + invoke `render_run` macro |
| `cast-server/cast_server/templates/fragments/run_status_cells.html` | NEW — line-2 cells, HTMX target |
| `cast-server/cast_server/templates/macros/run_node.html` | NEW — recursive node macro (direct self-recursion) |
| `cast-server/cast_server/templates/fragments/run_row.html` | DELETE (after grep confirms no other refs) |
| `cast-server/cast_server/templates/fragments/run_children.html` | DELETE (after grep confirms no other refs) |
| `cast-server/cast_server/static/style.css` | Append threaded styles; remove legacy `.run-row*` if unused |
| `cast-server/tests/test_runs_tree.py` | NEW — unit tests for `get_runs_tree` (incl. rollup, rework propagation, depth cap, status_rollup filter) |
| `cast-server/tests/test_runs_api.py` | EXTEND — `test_list_runs_returns_l1_with_descendants`, `test_list_runs_pagination_by_l1_only` |
| `cast-server/tests/test_runs_template.py` | NEW — markup-shape test asserting HTMX `hx-*` attributes target inner `.run-status-cells`, not outer `.run-node` |
| `cast-server/tests/conftest.py` | Add `seeded_runs_tree` fixture (4 trees: happy, rework, deep, leaf) |
| `cast-server/tests/ui/agents/cast-ui-test-runs/cast-ui-test-runs.md` | UPDATE — replace assertions with the threaded layout: `.run-group`, `.run-node`, `.thread`, `.ctx-pill`, `.copy-resume`, expand persistence, `has-warning` / `has-failure` borders, rework tags |
| `cast-server/tests/ui/runner.py` | Add any new selector helpers needed by the runs-screen agent (clipboard grant, etc.) |
| `docs/specs/cast-runs-screen.collab.md` | NEW — created in step 7 via `/cast-update-spec` (see "Spec capture" section). Locks the threaded /runs contract end-to-end. |
| `docs/specs/_registry.md` | UPDATE — add the new `cast-runs-screen.collab.md` row (handled by `/cast-update-spec`). |
| `docs/specs/cast-ui-testing.collab.md` | UPDATE — add a back-reference to `cast-runs-screen.collab.md` under "Linked files" so the harness spec points to the per-screen contract. |

## Implementation order

Each step independently verifiable; can stop and inspect after each.

0. **Add the `idx_agent_runs_parent` index** to `connection.py`. Restart server; verify with `EXPLAIN QUERY PLAN` against a fresh `agent_runs` query that the index is used.
1. **`get_runs_tree` + unit tests** (no UI changes yet) — `cast-server/tests/test_runs_tree.py` green proves the data layer works (incl. depth cap, rework propagation, status_rollup filter).
2. **Recursive macro + style.css additions + BOTH route swaps** (`/runs` page route AND `list_runs` HTMX pagination handler) — manual visit to `/runs` shows threaded layout; pagination links also produce threaded HTML. Old fragments still on disk.
3. **HTMX status-cells partial endpoint + markup-shape test** — running runs poll without losing expand state; structural test guards target precision.
4. **JS for collapse persistence + clipboard** — refresh persists; `⧉` copies.
5. **Cleanup**: delete legacy fragments (`run_row.html`, `run_children.html`), delete obsolete endpoints (`/runs/{id}/children`, `/runs/{id}/row`), remove unused CSS — only after grep confirms zero refs.
6. **Update `cast-ui-test-runs` agent prompt** with new threaded-layout assertions; verify `cast-server/tests/ui/test_full_sweep.py` passes end-to-end. **Then `Delegate: /cast-pytest-best-practices`** over `test_runs_tree.py`, the new assertions in `test_runs_api.py`, and `test_runs_template.py`; act on findings.
7. **Capture the contract as a spec via `Delegate: /cast-update-spec`** (see "Spec capture" section). Run only after the UI tests are green so the spec records the actually-shipped behavior, not aspirational copy from this plan. The skill produces a diff for review before writing.

## Spec capture (step 7)

Why a spec: this change introduces a non-trivial public contract — the
`get_runs_tree` data shape, rollup semantics, rework detection rules, ctx
threshold buckets, status-rollup filter behavior, depth cap, the HTMX
poll-safety pattern, and the collapse-state localStorage key format. Without
a spec, the next agent that touches the page will guess. With a spec, future
plans can reference it as the source of truth.

**Invocation:**

```
/cast-update-spec create cast-runs-screen
```

(Use `create` — this is a new spec, not an edit to an existing one.)

**Target file:** `docs/specs/cast-runs-screen.collab.md`

**Required sections (per `templates/cast-spec.template.md`):**

1. **Intent** — One paragraph: "the `/runs` page renders a threaded tree of agent runs, eagerly loaded per page, with rollup signals on parents, ctx-aware highlighting on children, and HTMX polling that does not disturb expand state."
2. **Linked files** — `docs/plan/2026-05-01-cast-runs-threaded-tree.collab.md`, `cast-server/cast_server/services/agent_service.py`, `cast-server/cast_server/templates/macros/run_node.html`, `cast-server/cast_server/templates/fragments/run_status_cells.html`, `cast-server/cast_server/static/style.css`, `cast-server/tests/ui/agents/cast-ui-test-runs/`.
3. **User Stories** — at minimum:
   - **US1: Multi-level tree visible without expansion** — a 4-level orchestration renders all four levels on initial load; the user can scan the whole structure without clicking anything.
   - **US2: Failure surfaces from any depth** — a failed grandchild causes the L1 to show `⚠ N failed` rollup, red `has-failure` group border, and the failed-status filter matches the L1.
   - **US3: Rework loops are recognizable** — consecutive same-`(agent_name, task_id)` siblings render `↻ rework #N` tags; their count propagates to the L1 rollup.
   - **US4: Context pressure is scannable** — ctx pill threshold (`<40` green, `40–70` amber, `70+` red) at status-pill prominence; child agent name color tracks the same threshold.
   - **US5: Resume is one click** — every row's line 2 has `⧉` that copies the run's resume command without expanding the row.
   - **US6: Polling preserves user state** — running rows update their status cells every 3s while leaving expand state, thread rail, and group container untouched.
   - **US7: Tree is bounded** — depth cap at 10 prevents runaway-loop trees from DOS-ing the page; truncated trees surface a server-side warning.
4. **Behavior contract (locked by this plan):**
   - `get_runs_tree(...)` return shape (per the function docstring).
   - Severity ordering for `status_rollup`: `failed > stuck > rate_limited > running > pending > scheduled > completed`.
   - Ctx thresholds: `<40 → low`, `40–70 → mid`, `70+ → high`.
   - Rework detection rule: consecutive siblings under the same parent with the same `(agent_name, task_id)`; index starts at 2 for the second instance; counts propagate to all ancestors.
   - HTMX swap-target rule: `hx-*` attributes live on `.run-status-cells`, NEVER on the outer `.run-node`. Outer node carries expand state and must survive polls.
   - Collapse persistence key format: `localStorage["runs:expanded:<run_id>"] = "1"` (presence = expanded; deleted = collapsed).
   - Depth cap: 10 levels; deeper rows are silently dropped + server-warned.
5. **Out of scope** — Mirror the plan's "Out of scope" list. Specifically: width cap, schema-level rollup caching, virtualization, intra-group search.
6. **Verification** — Reference `cast-server/tests/test_runs_tree.py`, `cast-server/tests/test_runs_template.py`, and the `cast-ui-test-runs` agent. Spec doesn't repeat the test list; it cites where the live coverage lives.

**After `/cast-update-spec` completes:**

- Confirm `docs/specs/_registry.md` has a new row (the skill writes it automatically; if not, add manually):
  ```
  | `cast-runs-screen.collab.md` | cast-runs-screen | cast-server | Threaded /runs page contract: tree fetch, rollups, rework, ctx thresholds, HTMX poll-safety, collapse persistence, depth cap. Linked plan: `docs/plan/2026-05-01-cast-runs-threaded-tree.collab.md`. | Draft | 1 |
  ```
- In `docs/specs/cast-ui-testing.collab.md`, add `cast-runs-screen.collab.md` to the "Linked files" list so the harness spec cross-references the per-screen contract.
- Run `/cast-spec-checker docs/specs/cast-runs-screen.collab.md` to validate the new spec against `templates/cast-spec.template.md`. Fix any lint findings before merging.

## Verification (manual)

After step 4, run through this checklist with a populated dev DB.

1. **Index in place**: `sqlite3 ~/.local/share/cast-server/cast.db "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_agent_runs_parent'"` returns one row.
2. **Layout**: visit `http://127.0.0.1:8000/runs`. Confirm two lines per row, status dot + agent name on line 1, status pill + ctx pill paired at start of line 2.
3. **Eager tree**: find a multi-level run (e.g. cast-preso-orchestrator). Confirm L2 and L3 children are visible without clicking expand.
4. **Pagination preserves tree shape**: click "Next" on the pagination footer. Confirm page 2 still renders threaded layout with descendants attached (not flat top-level only).
5. **Thread rail**: confirm a single rail per group; nested groups render their own rail; no per-depth horizontal indent of row content.
6. **Ctx pill colors**: a child with `ctx_class=low` is green; `mid` is amber; `high` is red. The child agent name should also tint to match.
7. **Rework**: locate a preso-style group with re-runs. Confirm `↻ rework #2` tag on the second instance and `⚠ N reworked` rollup pill on the parent. If reworks happen at L3+, L1's pill still reflects them (propagation).
8. **Failed-child rollup**: locate a group with a failed descendant. Group has solid red left border (`has-failure`); parent line 2 shows `⚠ N failed` red rollup.
9. **Recovered-failure border**: locate a group with reworks but no unresolved failures. Group has amber left border (`has-warning`).
10. **Status filter uses rollup**: set the status filter to `failed`. Confirm L1s whose own status is `completed` but with a failed descendant DO appear.
11. **Expand**: click a row; detail panel renders below. Click again; collapses. Click a row inside a thread; only that row expands.
12. **Refresh persistence**: expand 3 rows at different depths; reload; same 3 rows are expanded.
13. **HTMX poll safety**: open a running run's group with children expanded. Wait 6+ seconds. Status cells update without losing expand state of any row in the group.
14. **Copy resume**: click `⧉` on any row. Confirm browser clipboard contains the run's `resume_command`. Button shows "copied" briefly. Click does NOT expand the row.
15. **Goal link**: hover a goal name; confirm it turns accent + underlined. Click navigates to `/goals/{slug}`.
16. **Mobile**: resize viewport to 480px width. Confirm relative-time text and task crumbs hide; layout doesn't break.
17. **Depth cap**: synthetically insert a chain of 12 nested runs in dev DB. Confirm only depths 0–9 render; server log shows a "tree truncated" warning for that L1.
18. **No regression**: page header, summary cards (cost/tokens/dispatcher), pagination at bottom all still work.

## Unit tests (pytest)

**File:** `cast-server/tests/test_runs_tree.py`

```python
def test_returns_only_l1_at_top_level(seeded_runs_tree)
def test_children_attached_recursively(seeded_runs_tree)              # 3+ levels
def test_children_ordered_by_created_at_asc(seeded_runs_tree)
def test_descendant_count_is_subtree_size(seeded_runs_tree)
def test_failed_descendant_count_includes_stuck(seeded_runs_tree)
def test_total_cost_includes_self_and_descendants(seeded_runs_tree)
def test_wall_duration_seconds_l1_only(seeded_runs_tree)              # children don't get wall_duration_seconds
def test_status_rollup_is_max_severity(seeded_runs_tree)              # failed > running > completed
def test_ctx_class_low_mid_high_buckets(seeded_runs_tree)
def test_ctx_class_none_when_context_usage_missing(seeded_runs_tree)
def test_rework_detection_consecutive_siblings_same_agent_task(seeded_runs_tree)
def test_rework_index_increments_per_repeat(seeded_runs_tree)
def test_rework_count_propagates_to_all_ancestors(seeded_runs_tree)   # rework at L3 visible on L1 rollup
def test_pagination_by_l1_only(seeded_runs_tree)                      # children don't count toward limit
def test_status_filter_uses_status_rollup(seeded_runs_tree)           # ?status=failed surfaces L1 with failed descendants
def test_exclude_test_filter_works(seeded_runs_tree)
def test_empty_db_returns_empty(empty_db)
def test_l1_with_no_children_has_descendant_count_zero(seeded_runs_tree)
def test_depth_cap_truncates_at_10(deep_chain_db)                     # 12-deep tree returns at most depth 10
```

**File:** `cast-server/tests/test_runs_api.py` (extend)

```python
def test_list_runs_returns_l1_with_descendants(seeded_runs_tree)
    # GET /api/agents/runs?page=1 — JSON response has `children` arrays populated
def test_list_runs_pagination_by_l1_only(seeded_runs_tree)
    # page=2 returns next 25 L1s, not L2s of page 1
```

**File:** `cast-server/tests/test_runs_template.py` (NEW — markup-shape guard)

```python
def test_status_cells_carry_htmx_attrs(running_run_dict)
    # render macro, parse HTML, assert hx-get/hx-trigger/hx-swap exist on `.run-status-cells`
def test_run_node_does_not_carry_htmx_attrs(running_run_dict)
    # outer `.run-node` MUST NOT have hx-* — that would defeat poll-safety
```

A `seeded_runs_tree` fixture in `cast-server/tests/conftest.py` adds:
- 1 happy-path L1 with 3 successful L2 children
- 1 preso-style L1 with rework loop (check-coordinator fails, then check-coordinator + how re-run as `rework_index=2`); also one rework at L3 to verify ancestor propagation
- 1 4-level deep tree (orchestrate → subphase-runner → controller → controller-test)
- 1 leaf L1 with no children

A separate `deep_chain_db` fixture builds a synthetic 12-deep linear chain to verify the depth cap.

## UI tests — agent-driven

The diecast UI harness is screen-based: `cast-ui-test-orchestrator` dispatches per-screen test agents, each driving Playwright via `cast-server/tests/ui/runner.py`, results aggregated through the structured `output.json` contract by `cast-server/tests/ui/test_full_sweep.py`.

**Update:** `cast-server/tests/ui/agents/cast-ui-test-runs/cast-ui-test-runs.md` — replace the existing flat-runs assertions with the threaded-layout assertions:

- `.run-group`, `.run-node`, `.thread`, `.ctx-pill` markup present.
- Two-line layout: status dot + agent name in `.row-1`; status pill + ctx pill paired at start of `.row-2`.
- Eager tree: a known multi-level seed renders L2/L3 children on initial page load (no HTMX wait).
- Pagination preserves tree shape on page 2.
- Click on a row toggles `.expanded`; detail panel becomes visible.
- Reload → expand state survives (localStorage).
- `.copy-resume` click writes clipboard; row does NOT expand. (Use `context.grant_permissions(['clipboard-read', 'clipboard-write'])`.)
- `ctx_class=low/mid/high` → ctx pill background tint matches; `is-child.ctx-high .agent-name` is danger color.
- Failed-descendant seed → `.run-group.has-failure` (red border).
- **Rework-only seed (no failure) → `.run-group.has-warning` (amber border).** (Symmetric with has-failure; #12 in review.)
- Rework second instance has `.rework-tag`; L1 shows `⚠ N reworked` rollup with propagated count from deep reworks.
- Status filter `?status=failed` returns L1s with any failed descendant (rollup-aware).
- HTMX poll preserves expand state: expand a parent → wait 4s → state intact.
- Mobile viewport (480×800) hides `.relative-time` and `.task` crumbs.

If the agent needs new selectors or helpers (e.g., clipboard grant, viewport resize), extend `cast-server/tests/ui/runner.py` and `runs.md` together — runner is the source of mechanical primitives, the agent prompt drives sequencing.

After the suite is green, **`Delegate: /cast-pytest-best-practices`** over `test_runs_tree.py`, the new `test_runs_api.py` cases, and `test_runs_template.py`; act on findings before merging.

## Out of scope

Explicitly NOT in this plan; defer to follow-up:

- Schema columns to cache rollups (`status_rollup`, `total_cost_usd`, `descendant_count`) on completed runs.
- `MAX_DESCENDANTS_PER_GROUP` width cap (depth cap IS in scope; width cap deferred until observed).
- Virtualization / "show 7 more" affordance for parents with 10+ children.
- Search/filter inside a single group.
- L1 ctx-pill agent-name tinting (children-only for now per design decision).
- Resume-via-action (the `⧉` copies the command; running it stays manual).
- `bin/lint-anonymization` or other CI lint integration.

## Risks and open questions

1. **Recursive CTE on SQLite**: confirmed `sqlite3 3.50.4` in the environment supports `WITH RECURSIVE`. If a deployment ships an older SQLite (<3.8.3), fall back to iterative two-query fetch. Detect at startup via `sqlite3.sqlite_version_info`.
2. **Width of trees per page**: depth is capped at 10 (in-scope). Width is not capped — a single L1 with hundreds of descendants could bloat the page. With current usage (≤25 L1 × ~10 desc avg), payload is ~150 rows; acceptable. Monitor; add `MAX_DESCENDANTS_PER_GROUP=200` later if observed.
3. **Rollup compute budget**: post-order DFS is O(N) over page rows. For 250 rows, expect <5ms. If page exceeds 500 rows we reconsider caching `status_rollup` etc. on completed runs. No action today.
4. **localStorage key explosion**: one key per expanded run. Cap at 500 keys; on overflow, drop oldest (or just clear the namespace). Implement only if it becomes an issue.
5. **HTMX poll target precision**: structural unit test in `test_runs_template.py` guards this; if the test ever needs to be loosened, that's a strong signal to revisit the swap pattern.

## Reference

- Visual mockup (locked): `docs/plan/mockups/runs-threaded.html`
- Existing route: `cast-server/cast_server/routes/pages.py:175-191`
- Existing list endpoint: `cast-server/cast_server/routes/api_agents.py:222-232`
- Endpoints to delete: `cast-server/cast_server/routes/api_agents.py:211, 234`
- Existing data fn: `cast-server/cast_server/services/agent_service.py:520-589`
- Index precedent: `cast-server/cast_server/db/connection.py:137`
- Run model: `cast-server/cast_server/models/agent_run.py:6-44`
- UI harness: `cast-server/tests/ui/test_full_sweep.py`, `cast-server/tests/ui/runner.py`, `cast-server/tests/ui/agents/cast-ui-test-runs/`
- Existing tests pattern: `cast-server/tests/test_runs_api.py`
- Spec template: `templates/cast-spec.template.md`
- Spec registry: `docs/specs/_registry.md`
- Sibling specs to model after: `docs/specs/cast-ui-testing.collab.md`, `docs/specs/cast-delegation-contract.collab.md`

## Decisions

- **2026-05-01T06:11:51Z — Pagination endpoint reverts to flat rendering; how to close?** — Decision: Update list_runs at api_agents.py:222 to also use get_runs_tree. Rationale: only swapping the page route would silently break HTMX pagination links to flat top-level rendering — exactly the regression the redesign is trying to fix.
- **2026-05-01T06:11:51Z — Two existing run endpoints become obsolete after eager-load; delete or keep?** — Decision: Delete both `/runs/{id}/children` and `/runs/{id}/row` in step 5 cleanup. Rationale: dead code rots and invites incorrect future wiring; cleanup is cheap when bundled with the migration.
- **2026-05-01T06:11:51Z — Plan references nonexistent routes/api.py — fix path?** — Decision: Fix to routes/api_agents.py throughout. Rationale: the codebase splits routes per resource; api_agents.py is where every existing run endpoint lives.
- **2026-05-01T06:11:51Z — Status filter on raw L1 status hides failed descendants; change semantics?** — Decision: Filter on status_rollup, not raw status. Rationale: the L1 rollup pill surfaces failures but the filter would be unable to find them — undermines the redesign's whole failure-visibility story.
- **2026-05-01T06:11:51Z — total_active_seconds sum overstates orchestrator wall-time; what to display?** — Decision: Show wall-clock duration of L1 (completed_at − started_at) in line 2. Rationale: summing concurrent fan-out children double-counts time; users want "how long did I wait," answered by wall clock.
- **2026-05-01T06:11:51Z — Does rework_count propagate up through ancestors so L1 sees deep reworks?** — Decision: Yes, propagate via post-order DFS. Rationale: symmetric with failed_descendant_count; preserves the L1 rollup pill as the at-a-glance signal regardless of which depth the rework occurred at.
- **2026-05-01T06:11:51Z — Recursive macro pattern: import-self or direct self-recursion?** — Decision: Direct self-recursion within the same file. Rationale: standard Jinja idiom; the imported-self pattern adds an indirection without value.
- **2026-05-01T06:11:51Z — Lint pass on new test files?** — Decision: Add `Delegate: /cast-pytest-best-practices` to step 6. Rationale: every other diecast test plan does this; without explicit delegation the executor often forgets the lint pass.
- **2026-05-01T06:11:51Z — UI test pattern: pytest-style or agent-driven?** — Decision: Update the existing cast-ui-test-runs agent prompt and any required runner.py helpers; integrate via test_full_sweep.py. Rationale: the diecast UI harness is screen-based by orchestrator dispatch; a parallel pytest path would bifurcate maintenance and bypass structured reporting.
- **2026-05-01T06:11:51Z — list_runs endpoint behavior change is untested; how to cover?** — Decision: Extend test_runs_api.py with `test_list_runs_returns_l1_with_descendants` and `test_list_runs_pagination_by_l1_only`. Rationale: the existing tests would silently pass; pagination is precisely the kind of thing that quietly breaks.
- **2026-05-01T06:11:51Z — HTMX swap target precision currently has only a symptom-level UI test; need structural guard?** — Decision: Add a markup-shape unit test asserting hx-* attributes live on `.run-status-cells` not `.run-node`. Rationale: cause-level guard is faster and never flaky; symptom test passes during the wait window even if a future refactor breaks the target.
- **2026-05-01T06:11:51Z — `.run-group.has-warning` (rework but no failure) is untested while `has-failure` is; symmetric coverage?** — Decision: Add agent assertion for has-warning render to cast-ui-test-runs. Rationale: asymmetric coverage drifts; amber and red are equally meaningful states.
- **2026-05-01T06:11:51Z — No index on agent_runs.parent_run_id; recursive CTE will scan; add index?** — Decision: Add `idx_agent_runs_parent` via connection.py CREATE INDEX IF NOT EXISTS following the existing precedent. Rationale: eager-load means every `/runs` request hits this query; one-line preventive fix beats reactive perf debugging.
- **2026-05-01T06:11:51Z — Recursive CTE has no depth cap; risk of runaway?** — Decision: Add `WHERE depth < 10` to the recursion. Rationale: cheap SQL-level guard; depths beyond 10 are almost certainly bugs; truncated trees log a server-side warning so we can spot them.
- **2026-05-01T06:11:51Z — Per-page rollup compute O(N); optimize now or accept?** — Decision: Accept; surface the budget in Risks. Rationale: <5ms for 250 rows is well within page-load envelope; caching adds schema change and writeback complexity for a non-problem.
- **2026-05-01T06:11:51Z — Per-row JSON parse cost on tree path; optimize?** — Decision: Trim the tree path to parse only context_usage (skip input_params/output/artifacts/directories). Rationale: the line-2 row needs only ctx_class; deferring the rest to detail-render saves both parse cost and payload size.

### Decisions added during execution (sp5-retry)

- **2026-05-01T08:25:00Z — Recheck/Cancel HTMX response shape: legacy `.run-row` or new macro-shaped `.run-group`?** — Decision: Update `recheck_run` + `cancel_run_endpoint` to render via the `run_node` macro and return a `.run-group` fragment matching the macro's `hx-target="closest .run-group"`. Rationale: the buttons are part of the new threaded UI now; returning the legacy shape was a latent bug introduced in sp2/sp4 that surfaced when sp5's grep-gate caught the live reference. Bundled into sp5-retry along with the cleanup it was blocking.
- **2026-05-01T08:25:00Z — How to handle external callers of `/api/agents/runs/{id}/children`?** — Decision: One-time forward-looking migration. Extend `GET /api/agents/jobs/{id}` with optional `?include=children` (uses `get_run_with_rollups`) as the canonical sub-tree fetch surface; migrate the 3 known callers (cast-preso-check-coordinator test cases, runs-api.md docs, agent_service.py prompt-template listing) to the new URL; then delete `/children`. Rationale: user explicitly asked for forward-looking design over a compat shim; the new endpoint reuses sp3's helper and consolidates run-fetching to one canonical surface (`/jobs/{id}` ± descendants).
- **2026-05-01T08:25:00Z — Dead click handler in `templates/pages/runs.html` lines 75-80 (`.run-row-main` / `.run-row` selectors): remove inline as part of sp5 or defer?** — Decision: Remove inline as part of sp5-retry. Rationale: handler is already a no-op against the new DOM; removing alongside the CSS deletion satisfies the grep-gate cleanly and avoids leaving stale code.
- **2026-05-01T08:25:00Z — Should the new endpoint shapes and removed endpoints be reflected in the spec?** — Decision: Yes — sp7 plan extended with US8 (action buttons return macro-shaped fragments), US9 (canonical `/jobs/{id}?include=children` surface; `/children` and `/row` removed), behavior contract bullets covering the HTMX response-shape rule and the canonical sub-tree URL, and a "Removed in this release" subsection. Rationale: spec is the contract of record; without these the next agent that touches the page would re-introduce the bug.
