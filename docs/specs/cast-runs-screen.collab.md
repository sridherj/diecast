# Cast Runs Screen — Threaded Tree

> **Spec maturity:** draft
> **Version:** 1
> **Updated:** 2026-05-01
> **Linked files:**
> - `docs/plan/2026-05-01-cast-runs-threaded-tree.collab.md` (canonical plan + decisions block)
> - `cast-server/cast_server/services/agent_service.py` (`get_runs_tree`, `get_run_with_rollups`)
> - `cast-server/cast_server/routes/api_agents.py` (`list_runs`, `recheck_run`, `cancel_run_endpoint`, `/jobs/{id}?include=children`, `/runs/{id}/status_cells`)
> - `cast-server/cast_server/routes/pages.py` (`runs_page`)
> - `cast-server/cast_server/templates/macros/run_node.html`
> - `cast-server/cast_server/templates/fragments/run_status_cells.html`
> - `cast-server/cast_server/templates/fragments/run_group.html`
> - `cast-server/cast_server/templates/fragments/runs_list.html`
> - `cast-server/cast_server/templates/pages/runs.html`
> - `cast-server/cast_server/static/style.css`
> - `cast-server/docs/runs-api.md`
> - `cast-server/tests/test_runs_tree.py`
> - `cast-server/tests/test_runs_api.py`
> - `cast-server/tests/test_runs_template.py`
> - `cast-server/tests/ui/agents/cast-ui-test-runs/`

## Intent

The `/runs` page renders a threaded tree of agent runs, eagerly loaded per page,
with rollup signals on parents, ctx-aware highlighting on children, and HTMX
polling that does not disturb expand state. One screen lets an operator scan
nested orchestrations end-to-end, spot the row that broke, and copy a resume
command without expanding anything. The contract this spec captures was shipped
across sub-phases sp1–sp6 of `docs/execution/runs-threaded-tree/` and is locked
here so the next agent that touches the page has a source of truth — not just a
plan archive.

## User Stories

### US1 — Multi-level tree visible without expansion (Priority: P1)

**As an** operator triaging a multi-level orchestration, **I want** every level
of a 4-deep run tree to render on initial page load, **so that** I can scan the
whole structure without clicking anything.

**Independent test:** `cast-server/tests/test_runs_tree.py` seeds a 4-level tree
and asserts `get_runs_tree(...)` returns each L1 with its full descendant chain
attached and `descendant_count` matching the seeded count.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `/runs` loads with at least one L1 having descendants,
  THE SYSTEM SHALL render every descendant inside the L1's `.run-group`
  container without requiring an expand click.
- **Scenario 2:** WHEN a tree is deeper than the configured depth cap, THE
  SYSTEM SHALL drop rows past depth 10 and emit a server-side
  `tree truncated` warning naming the L1 run id.

### US2 — Failure surfaces from any depth (Priority: P1)

**As an** operator, **I want** an L1's rollup pill to show the failure count of
its entire subtree, **so that** a failed grandchild is visible without
expanding the L1.

**Independent test:** `cast-server/tests/test_runs_tree.py` seeds an L1 with a
failed grandchild and asserts the L1's `failed_descendant_count >= 1` and
`status_rollup == 'failed'`. The same test asserts `?status=failed` returns the
L1 even though its own `status='completed'`.

**Acceptance scenarios:**

- **Scenario 1:** WHEN any descendant of an L1 has `status in ('failed',
  'stuck')`, THE SYSTEM SHALL set the L1's `status_rollup` to that severity
  and render `⚠ K failed` on the L1's line-2 rollup pill.
- **Scenario 2:** WHEN a status filter `?status=failed` is applied, THE SYSTEM
  SHALL match L1s whose `status_rollup` (NOT raw `status`) equals the filter.
- **Scenario 3:** WHEN any descendant has `status='failed'` and no rework
  recovery exists, THE SYSTEM SHALL render the L1's `.run-group` with the
  `has-failure` class (red border).

### US3 — Rework loops are recognizable (Priority: P1)

**As an** operator, **I want** consecutive same-`(agent_name, task_id)`
siblings to be tagged as rework, **so that** check → reject → re-run loops are
visible at a glance and counted in ancestor rollups.

**Independent test:** `cast-server/tests/test_runs_tree.py` seeds a parent with
three children sharing one `(agent_name, task_id)` and asserts the second is
`is_rework=True, rework_index=2` and the third is `is_rework=True,
rework_index=3`. The L1's `rework_count` reflects the propagated total.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a child shares its `(agent_name, task_id)` with a prior
  sibling under the same parent (ordered by `created_at ASC`), THE SYSTEM
  SHALL set `is_rework=True` and `rework_index=N` (starting at 2 for the
  second instance).
- **Scenario 2:** WHEN any descendant has `is_rework=True`, THE SYSTEM SHALL
  add that count to every ancestor's `rework_count` via post-order DFS so the
  L1 rollup pill renders `⚠ K reworked`.
- **Scenario 3:** WHEN an L1's tree contains rework but no unresolved failures,
  THE SYSTEM SHALL render the `.run-group` with the `has-rework` (amber
  border) class — never `has-failure`.

### US4 — Context pressure is scannable (Priority: P1)

**As an** operator, **I want** ctx pressure to be a pill at status-pill
prominence and child agent names to track the same threshold, **so that**
"is the agent in trouble?" is as scannable as "did it succeed?".

**Independent test:** `cast-server/tests/test_runs_tree.py` asserts
`ctx_class` resolves to `'low'` for `<40`, `'mid'` for `40–70`, `'high'` for
`>=70`, and `None` when `context_usage` is missing or lacks both `total` and
`limit`.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a run's `context_usage` percentage is `<40`, THE SYSTEM
  SHALL render its ctx pill with the `low` (green) class.
- **Scenario 2:** WHEN a run's `context_usage` percentage is `>=70`, THE
  SYSTEM SHALL render its ctx pill with the `high` (red) class AND, on
  non-L1 rows, color the agent-name with the same threshold.
- **Scenario 3:** WHEN `context_usage` is missing or unparseable, THE SYSTEM
  SHALL omit the ctx pill (no neutral fallback) and leave child agent name
  in the default color.

### US5 — Resume is one click (Priority: P1)

**As an** operator, **I want** every row's line 2 to expose a `⧉` button that
copies the run's resume command, **so that** resuming a run is one click and
never requires expanding the row.

**Independent test:** `cast-server/tests/ui/agents/cast-ui-test-runs/` asserts
the `⧉` button is present on every rendered row and clicking it calls
`navigator.clipboard.writeText` with a non-empty string.

**Acceptance scenarios:**

- **Scenario 1:** WHEN any row renders, THE SYSTEM SHALL include the
  `.copy-resume` button (labeled `Resume ⧉`) in its line-2 cells regardless
  of `status`.
- **Scenario 2:** WHEN the user clicks the `Resume` button, THE SYSTEM SHALL
  call `navigator.clipboard.writeText(<resume command>)` and swap the button
  contents to `Copied ✓` with the `.copied` class for ~1.1s, then revert.

### US6 — Polling preserves user state (Priority: P1)

**As an** operator who has expanded several rows, **I want** the 3-second HTMX
poll to update only the status cells, **so that** my expand state, focus, and
group container survive every refresh.

**Independent test:** `cast-server/tests/test_runs_template.py` parses the
rendered HTML and asserts `hx-get`, `hx-trigger`, `hx-swap` attributes appear
ONLY on `.run-status-cells` spans and NEVER on the outer `.run-node` element.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a row's `status in ('running', 'pending',
  'rate_limited')`, THE SYSTEM SHALL emit the polling `hx-*` attributes on
  the inner `.run-status-cells` span only.
- **Scenario 2:** WHEN a row's status is terminal (`completed`, `failed`,
  `stuck`, etc.), THE SYSTEM SHALL omit the polling attributes entirely.
- **Scenario 3:** WHEN a status-cells poll fires, THE SYSTEM SHALL replace
  only the inner cells via `GET /api/agents/runs/{id}/status_cells` and leave
  the outer `.run-node`, the thread rail, and the `.run-group` container
  untouched.

### US7 — Tree is bounded (Priority: P1)

**As a** site operator, **I want** runaway-loop trees to be silently bounded,
**so that** a buggy agent cannot DOS the page by spawning thousands of nested
descendants.

**Independent test:** `cast-server/tests/test_runs_tree.py` seeds a
12-deep linear chain and asserts `get_runs_tree(...)` returns at most 10
levels for that L1 and that the server log captured a `tree truncated`
warning.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a recursive descendant chain exceeds depth 10, THE
  SYSTEM SHALL drop rows past depth 10 from the response.
- **Scenario 2:** WHEN truncation happens, THE SYSTEM SHALL log a server-side
  `tree truncated` warning naming the L1 run id so runaway loops are
  diagnosable in production.

### US8 — Action buttons return macro-shaped fragments (Priority: P1)

**As an** operator clicking Recheck or Cancel from a tree row, **I want** the
HTMX swap to land a `.run-group`-shaped fragment, **so that** the macro's
`hx-target="closest .run-group"` swap target receives markup of the same shape
it removed.

**Independent test:** `cast-server/tests/test_runs_api.py` asserts
`POST /api/agents/jobs/{id}/recheck` and `POST /api/agents/runs/{id}/cancel`
both return HTML beginning with `<div class="run-group ...">` (the
`run_node`-rendered shape) — never a `.run-row` fragment.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `POST /api/agents/jobs/{id}/recheck` returns to an
  HTMX caller, THE SYSTEM SHALL render the response via the `run_node` macro
  wrapped in `fragments/run_group.html` so the swap target receives a
  `.run-group` fragment.
- **Scenario 2:** WHEN `POST /api/agents/runs/{id}/cancel` returns to an HTMX
  caller, THE SYSTEM SHALL render the response via the same macro path with
  the same `.run-group` shape.
- **Scenario 3:** No HTMX handler invoked from a `run_node`-rendered button
  MAY return a `.run-row` fragment — that legacy shape no longer exists in
  the templates after sp5.

### US9 — Sub-tree fetch is canonical at `/jobs/{id}?include=children` (Priority: P1)

**As an** agent or external client that needs a single run with its descendant
tree, **I want** one canonical JSON endpoint, **so that** I am not forced to
parse HTML or compose multiple requests.

**Independent test:** `cast-server/tests/test_runs_api.py` asserts
`GET /api/agents/jobs/{id}?include=children` returns JSON with the run's
fields plus a `children` array shaped by `get_run_with_rollups` (depth-capped,
rollups attached). The same endpoint without `?include=children` returns the
existing single-run shape with no `children` key.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `GET /api/agents/jobs/{id}?include=children` is
  called, THE SYSTEM SHALL return the merged run JSON with a `children`
  array carrying the depth-capped descendant tree (each entry rollup-attached
  via `get_run_with_rollups`).
- **Scenario 2:** WHEN `?include=children` is omitted, THE SYSTEM SHALL
  return the existing single-run shape unchanged — backward-compatible with
  callers that do not need descendants.
- **Scenario 3:** Legacy callers MUST migrate to this endpoint; the prior
  HTML fragment endpoint `GET /api/agents/runs/{id}/children` is removed
  (see "Removed in this release").

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | `get_runs_tree(status_filter, page, per_page, exclude_test, db_path)` returns `{runs, total, page, per_page, pages}` where each L1 run dict carries `children`, `descendant_count`, `failed_descendant_count`, `rework_count`, `status_rollup`, `total_cost_usd`, `wall_duration_seconds`, `ctx_class`, `is_rework`, `rework_index`. | Source of truth for the rollup contract. Field-by-field matches the docstring in `services/agent_service.py`. |
| FR-002 | `status_rollup` is computed by max severity over `{self} ∪ descendants` using the order `failed > stuck > rate_limited > running > pending > scheduled > completed`. | Locked decision #4 in plan. |
| FR-003 | `ctx_class` is `'low'` when `context_usage_percent < 40`, `'mid'` when `40 <= percent < 70`, `'high'` when `percent >= 70`, and `None` when `context_usage` is missing or lacks both `total` and `limit`. | Locked decision #4 in plan. |
| FR-004 | Rework detection: under each parent, walk children in `created_at ASC`; for each child key `(agent_name, task_id)`, the second and later occurrence sets `is_rework=True` and `rework_index=N` (starting at 2). After per-parent detection, run a post-order DFS so every ancestor's `rework_count` includes all descendant reworks. | Locked decision #8 in plan. |
| FR-005 | HTMX poll attributes (`hx-get`, `hx-trigger`, `hx-swap`) live ONLY on `.run-status-cells` (inner span) and NEVER on `.run-node` (outer container). The structural guard in `tests/test_runs_template.py` enforces this. | Locked. The legacy flat template regressed on this exact line; the test exists to prevent recurrence. |
| FR-006 | Status cells are emitted with `hx-*` attributes only when `run.status in ('running', 'pending', 'rate_limited')`. Terminal-status rows are static. | Avoids unnecessary polls on completed runs. |
| FR-007 | Collapse persistence uses `localStorage["runs:expanded:<run_id>"] = "1"`. Presence means expanded; absence means collapsed. No JSON serialization. State is reapplied on `htmx:afterSwap` for nodes that survive a partial swap. | Locked. Format chosen so individual entries can be cleared without re-serializing a single blob. |
| FR-008 | Recursive descendant fetch is depth-capped at 10. Trees deeper than 10 are silently truncated and the server logs a `tree truncated` warning naming the L1 run id. | Locked decision; protects the page from runaway agent loops. |
| FR-009 | Status filter `?status=<value>` filters on `status_rollup`, NOT raw L1 `status`. An L1 whose own status is `completed` but whose subtree contains a `failed` row matches `?status=failed`. | Locked decision #13 in plan. Without this rule the rollup pill could surface failures the filter cannot find. |
| FR-010 | L1 line-2 duration shows wall-clock = `completed_at - started_at` (or `None` while in flight; UI falls back to "started Xm ago"). Children show their existing `active_seconds`. | Locked decision #14 in plan. Wall-clock prevents fan-out double-counting. |
| FR-011 | Any HTMX handler whose only HTMX caller is a `run_node`-rendered button MUST return a `.run-group` fragment via the `run_node` macro (wrapped by `fragments/run_group.html`). Returning a `.run-row` fragment is a bug — that legacy shape no longer exists in the templates. | Added by sp5 retry. Recheck and Cancel handlers were latently broken in sp2; this rule locks the fix. |
| FR-012 | Canonical sub-tree fetch URL is `GET /api/agents/jobs/{run_id}?include=children`. Returns the existing single-run JSON augmented with a `children` array shaped by `get_run_with_rollups`. When `?include=children` is omitted, the response is unchanged from the pre-sp5 single-run shape. | Backward-compatible. Replaces the removed `/runs/{id}/children` HTML endpoint. |
| FR-013 | The Resume button on the L3 expansion area is REMOVED; resume is exclusively the line-2 `⧉` clipboard button. | Locked decision #11 in plan. Avoids duplication. |

### Removed in this release

These endpoints existed in the pre-sp5 implementation and are GONE. Migration
paths are mandatory for any caller that still references them.

| Removed endpoint | Replacement | Migration notes |
|------------------|-------------|-----------------|
| `GET /api/agents/runs/{run_id}/children` (HTML fragment) | `GET /api/agents/jobs/{run_id}?include=children` (JSON) | Sub-tree fetch is now JSON. Three known callers (`agents/cast-preso-check-coordinator/tests/test-cases.md`, `cast-server/docs/runs-api.md`, `cast-server/cast_server/services/agent_service.py` prompt-template listing) were migrated in sp5. No compatibility shim. |
| `GET /api/agents/runs/{run_id}/row` (HTML fragment) | `GET /api/agents/runs/{run_id}/status_cells` (HTML fragment of inner cells only) | The 3s HTMX poll target moved from the outer row to the inner status-cells span (see HTMX swap-target rule above). The new endpoint returns just the cells, never the full row. |
| `cast-server/cast_server/templates/fragments/run_row.html` | `templates/macros/run_node.html` (macro) + `fragments/run_group.html` (wrapper) | All row rendering goes through the recursive macro. |
| `cast-server/cast_server/templates/fragments/run_children.html` | Inline rendering inside the `run_node` macro's recursive call | No separate child template. |

## Out of scope

The following items are explicitly NOT covered by this spec; they are
deferred to future sub-phases.

- Schema columns to cache rollups (DB-side denormalization of
  `descendant_count` / `failed_descendant_count` / `rework_count`).
- `MAX_DESCENDANTS_PER_GROUP` width cap (depth cap is in scope; width cap is
  not).
- Virtualization or "show 7 more" affordance for very wide groups.
- Search / filter inside a single group.
- L1 ctx-pill agent-name tinting (children-only for now).
- Resume-as-action (the `⧉` copies the resume command; running it stays
  manual).
- `bin/lint-anonymization` integration.
- `cast-server-stopped` runs queryable via the HTTP API (file-only runs are
  still file-only at v1; see `docs/runs-api.md` "Server-dispatched-only
  carve-out").
- Promotion of `/api/agents/{name}/invoke` to the dispatch precondition gate
  in `cast-delegation-contract.collab.md`.

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | A 4-level orchestration renders all four levels on initial `/runs` load with no expand-click required. | `cast-server/tests/ui/agents/cast-ui-test-runs/` asserts depth-4 visibility against the seeded fixture. |
| SC-002 | A failed grandchild causes the L1's rollup pill to render `⚠ N failed` and the L1 matches `?status=failed`. | `cast-server/tests/test_runs_tree.py` rollup tests + the UI agent's filter assertion. |
| SC-003 | Consecutive same-`(agent_name, task_id)` siblings render `↻ rework #N` and the count propagates to all ancestors. | `cast-server/tests/test_runs_tree.py` rework-detection and propagation tests. |
| SC-004 | Ctx pill at `<40`/`40-70`/`>=70` thresholds; child name color tracks the same threshold. | `cast-server/tests/test_runs_tree.py` `ctx_class` tests + UI agent visual assertion. |
| SC-005 | Every row's line 2 has a working `⧉` resume-copy button regardless of status. | UI agent asserts presence on every row and clipboard write on click. |
| SC-006 | Running rows update their status cells every 3s while leaving expand state, thread rail, and group container untouched. | `cast-server/tests/test_runs_template.py` markup-shape guard + UI agent's expand-survives-poll assertion. |
| SC-007 | A 12-deep linear chain renders at most 10 levels and surfaces a `tree truncated` server warning. | `cast-server/tests/test_runs_tree.py` depth-cap test against the `deep_chain_db` fixture. |
| SC-008 | Recheck and Cancel HTMX handlers return `.run-group` fragments — never `.run-row`. | `cast-server/tests/test_runs_api.py` assertions on the recheck and cancel response shape. |
| SC-009 | `GET /api/agents/jobs/{id}?include=children` returns the merged run with a depth-capped `children` array; the same endpoint without the param returns the existing single-run JSON unchanged. | `cast-server/tests/test_runs_api.py` cases for both branches. |

## Verification

Live coverage for this spec is asserted by:

- `cast-server/tests/test_runs_tree.py` — 19 unit tests for `get_runs_tree`
  covering rollups, rework propagation, ctx classification, depth cap, and
  rollup-aware status filter.
- `cast-server/tests/test_runs_api.py` — HTTP route tests including
  `?include=children`, recheck/cancel response shape, and HTMX-pagination
  behavior.
- `cast-server/tests/test_runs_template.py` — markup-shape guard that
  asserts `hx-*` attributes live on `.run-status-cells` and never on
  `.run-node`.
- `cast-server/tests/ui/agents/cast-ui-test-runs/` — end-to-end agent that
  drives the threaded `/runs` page in a real browser and asserts US1–US7
  against the live DOM.

This spec does not enumerate test cases; it cites where the live coverage
lives. The plan
(`docs/plan/2026-05-01-cast-runs-threaded-tree.collab.md`) is the rationale
archive — read it for the "why" behind the locked decisions referenced above.

## Open Questions

- **[USER-DEFERRED]** Whether to add a `MAX_DESCENDANTS_PER_GROUP` width
  cap. Reason: deferred until observed bloat in production; depth cap is
  sufficient for the runaway-loop case the page actually faces today.
- **[USER-DEFERRED]** Whether to cap `localStorage` keys at 500 entries.
  Reason: deferred until observed bloat; one key per expanded run is the
  current shape and naturally trims as runs are deleted.
- **[USER-DEFERRED]** SQLite `< 3.8.3` (no `WITH RECURSIVE`) fallback path.
  Reason: dev environment runs `sqlite3 3.50.4`; pre-emptive coding is not
  required. A startup-time version probe will trigger the iterative
  two-query fallback if and when an old SQLite ships.
