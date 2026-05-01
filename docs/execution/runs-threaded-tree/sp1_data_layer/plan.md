# Sub-phase 1: Data Layer — Index + `get_runs_tree` + Unit Tests

> **Pre-requisite:** Read `docs/execution/runs-threaded-tree/_shared_context.md` before starting.

## Objective

Land the entire data layer that the threaded `/runs` redesign depends on: a new index for the recursive-CTE join, a new `get_runs_tree(...)` service function with rollups + rework detection + depth cap + rollup-aware status filter, and the unit-test suite that proves the function's contract. After this sub-phase, every shape claim downstream sub-phases make about the run dict (`children`, `descendant_count`, `status_rollup`, `rework_count`, `wall_duration_seconds`, `ctx_class`, `is_rework`, `rework_index`) is enforced by passing tests — UI sub-phases can rely on the shape without re-validating.

This sub-phase folds source plan **step 0** (the one-line index) into source plan **step 1** because both are pure data-layer changes and shipping them in a single commit keeps the bisect surface clean.

## Dependencies

- **Requires completed:** None.
- **Assumed codebase state:** Pre-change tree at HEAD. `agent_runs` exists with all fields the plan needs (`parent_run_id`, `task_id`, `agent_name`, `status`, `cost_usd`, `started_at`, `completed_at`, `context_usage`). `get_all_runs(top_level_only=True, ...)` exists in `services/agent_service.py` near lines 520–589 and is the model for `_row_to_dict` shape and filter handling.

## Scope

**In scope:**
- `cast-server/cast_server/db/connection.py`: append one `CREATE INDEX IF NOT EXISTS idx_agent_runs_parent ON agent_runs(parent_run_id)` next to the existing `idx_error_memories_agent` precedent at line 137.
- `cast-server/cast_server/services/agent_service.py`: add `get_runs_tree(...)` plus private helpers `_assemble_tree`, `_compute_rollups`, `_propagate_rework`, `_detect_rework`. The tree path must skip parsing of `input_params`, `output`, `artifacts`, `directories` on the row — only `context_usage` is parsed (for `ctx_class`).
- `cast-server/tests/conftest.py`: add `seeded_runs_tree` (4 trees: happy, rework, deep, leaf) and `deep_chain_db` (12-deep linear chain) fixtures.
- `cast-server/tests/test_runs_tree.py`: NEW — 19 unit tests per the plan.
- `cast-server/tests/test_runs_api.py`: extend with `test_list_runs_returns_l1_with_descendants` and `test_list_runs_pagination_by_l1_only`.

**Out of scope (do NOT do these):**
- Any template, route, or CSS edit — sp2 owns route swaps and templates.
- The HTMX `/status_cells` endpoint or `test_runs_template.py` — sp3.
- Inline JS — sp4.
- Deletion of legacy fragments / endpoints / CSS — sp5.
- UI test agent prompt edits or `runner.py` extensions — sp6.
- Spec creation — sp7.
- Editing `get_all_runs` (the existing flat function). Other callers depend on it; leave it alone.

## Files to Create/Modify

| File | Action | Current state |
|------|--------|---------------|
| `cast-server/cast_server/db/connection.py` | Modify | Has `CREATE INDEX IF NOT EXISTS idx_error_memories_agent` at line 137; no `idx_agent_runs_parent`. |
| `cast-server/cast_server/services/agent_service.py` | Modify | `get_all_runs` exists at lines 520–589; no `get_runs_tree`. |
| `cast-server/tests/conftest.py` | Modify | No `seeded_runs_tree` / `deep_chain_db` fixtures yet. |
| `cast-server/tests/test_runs_tree.py` | Create | New file. |
| `cast-server/tests/test_runs_api.py` | Modify | Extend with 2 new test cases. |

## Detailed Steps

### Step 1.1: Add the index in `connection.py`

Locate the `CREATE INDEX IF NOT EXISTS idx_error_memories_agent` statement at `connection.py:137` and append a sibling line:

```sql
CREATE INDEX IF NOT EXISTS idx_agent_runs_parent ON agent_runs(parent_run_id)
```

Match the surrounding execution pattern exactly (same `cursor.execute(...)` style, same `;` placement, same indentation). The index auto-creates on next server start; no Alembic migration is involved.

After the change, restart the server and verify with:

```bash
sqlite3 ~/.cast/diecast.db "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_agent_runs_parent'"
```

Expect one row.

Optional but recommended: run `EXPLAIN QUERY PLAN` against a simple `SELECT * FROM agent_runs WHERE parent_run_id = ?` and confirm the planner uses `idx_agent_runs_parent`.

### Step 1.2: Add `get_runs_tree` to `services/agent_service.py`

Insert directly after `get_all_runs` (which currently lives near lines 520–589). Reuse `_row_to_dict` for the per-row hydration but **trim parsed JSON columns on the tree path** — only `context_usage` is parsed; `input_params`, `output`, `artifacts`, and `directories` are deferred to the detail-render path.

The function signature, docstring, and return shape are locked in `_shared_context.md` § "`get_runs_tree(...)` return shape". Do not deviate.

Implementation sequence (matches plan §"Backend service: new `get_runs_tree`"):

**1. Page L1 ids.** Pre-filter L1s by raw status (so pagination is bounded by L1s only):

```sql
SELECT id FROM agent_runs
WHERE parent_run_id IS NULL
  [+ exclude_test filter]
  [+ raw status pre-filter — see step 7 below for why this is NOT the same as the rollup filter]
ORDER BY created_at DESC
LIMIT ? OFFSET ?
```

The `total` for pagination is the count of L1s, not of all rows.

**2. Tree fetch (recursive CTE, depth-capped at 10).**

```sql
WITH RECURSIVE tree AS (
  SELECT ar.*, 0 AS depth FROM agent_runs ar WHERE ar.id IN (?, ?, ...)
  UNION ALL
  SELECT ar.*, tree.depth + 1
  FROM agent_runs ar
  JOIN tree ON ar.parent_run_id = tree.id
  WHERE tree.depth < 10
)
SELECT … FROM tree
```

When the recursion would have returned a row at depth ≥ 10, log a server-side warning (use the existing logger: `logger.warning("tree truncated at depth 10 for L1 run_id=%s", l1_id)`). The truncation check can be inferred by counting whether any row at depth == 10 was actually reached and would have had children — pragmatic implementation: after assembly, walk the tree; if any node at depth 10 has `children` per the database (run a probe `SELECT 1 FROM agent_runs WHERE parent_run_id IN (depth-10 ids) LIMIT 1`), warn.

**3. Enrichment.** LEFT JOIN goals + tasks the same way `get_all_runs` does today.

**4. Tree assembly (Python).** Build `id → run` dict, attach `children` lists, sort each level by `created_at ASC`. Helper: `_assemble_tree(rows: list[dict]) -> list[dict]`.

**5. JSON-parse trim.** In the tree-path `_row_to_dict` (or a new variant `_row_to_tree_dict`), parse only `context_usage`. Leave other JSON columns as raw strings (or omit them entirely from the dict — downstream templates reference only the trimmed shape on tree rows). Document the difference inline.

**6. Rollup compute.** Helper: `_compute_rollups(roots: list[dict]) -> None` — mutates each tree in place using post-order DFS:
- `descendant_count` = sum of subtree sizes (not counting self).
- `failed_descendant_count` = count of descendants where `status in ('failed', 'stuck')`.
- `total_cost_usd` = sum of `cost_usd` over self + descendants (treat `None` as `0.0`).
- `wall_duration_seconds` (L1 only — depth 0): `int((completed_at - started_at).total_seconds())` if both present; else `None`. Do NOT set this field on children.
- `status_rollup`: max severity over self + descendants per the locked ordering `failed > stuck > rate_limited > running > pending > scheduled > completed`. Centralize the severity lookup in a module-level `_STATUS_SEVERITY` dict.
- `ctx_class`: bucket of `context_usage["total"] / context_usage["limit"] * 100` if both present; `< 40` → `'low'`, `< 70` → `'mid'`, `>= 70` → `'high'`. None when either field missing.

**7. Rollup-aware status filter (Decision #13).** If `status_filter` is set, after rollups are computed, filter the L1 list to those with `status_rollup == status_filter`. Apply this AFTER rollup computation, not in SQL — cost is bounded by 25 L1 per page. Note: this changes pagination semantics slightly (the L1 query in step 1 still applies a raw status pre-filter for `failed`/`stuck` to keep the page bounded; the post-filter then prunes any L1s whose own status matched but whose tree rollup doesn't — and the count returned in `total` reflects the post-filter). For the simple v1, run the L1 query WITHOUT the raw status filter and post-filter on rollup; this is exact at the cost of a slightly larger fetch when filtering. **Pick the simpler approach: no raw status pre-filter; rollup is the only filter applied.** This matches the plan's "post-rollup is simpler than re-expressing as SQL" decision.

**8. Rework detection.** Helper: `_detect_rework(parent: dict) -> None` walks `parent["children"]` in order; per child, key = `(agent_name, task_id)`; if seen before, set `is_rework=True` and `rework_index=count`; else first sighting (no flag). Helper: `_propagate_rework(roots) -> None` runs post-order DFS that sets each node's `rework_count` to the sum of its own rework events + all descendants' `rework_count`.

**Returns:** `{"runs": [...L1 with children attached...], "total": int, "page": int, "per_page": int, "pages": int}`.

### Step 1.3: Add `seeded_runs_tree` and `deep_chain_db` fixtures to `conftest.py`

Place near the existing test-DB fixtures. The fixture seeds four trees in a fresh in-memory (or temp) DB:

1. **Happy-path L1** with 3 successful L2 children (all `status='completed'`).
2. **Preso-style L1** with rework loop:
   - Parent `cast-preso-orchestrator` (completed).
   - L2 `cast-preso-check-coordinator` first instance (failed).
   - L2 `cast-preso-check-coordinator` second instance — same `(agent_name, task_id)` (completed). → expect `is_rework=True, rework_index=2` on the second instance.
   - L2 `cast-preso-how` (completed).
   - Inside the second `check-coordinator`, an L3 with two siblings of same `(agent_name, task_id)` to verify ancestor rework propagation reaches L1.
3. **4-level deep tree**: `cast-orchestrate` → `cast-subphase-runner` → `cast-controller` → `cast-controller-test`. All completed. Used by `test_children_attached_recursively` and `test_descendant_count_is_subtree_size`.
4. **Leaf L1** with no children. Used by `test_l1_with_no_children_has_descendant_count_zero`.

`seeded_runs_tree` yields the test DB. Helper assertions in tests can `get_runs_tree(db_path=...)` and inspect the returned dicts.

`deep_chain_db` builds a separate fixture with a 12-deep linear chain (one child per level). Used by `test_depth_cap_truncates_at_10`.

Use deterministic UUIDs (or sequential ids) so tests can address specific runs.

### Step 1.4: Author `cast-server/tests/test_runs_tree.py`

Tests, all listed in the source plan §"Unit tests (pytest)":

```python
def test_returns_only_l1_at_top_level(seeded_runs_tree)
def test_children_attached_recursively(seeded_runs_tree)              # 3+ levels
def test_children_ordered_by_created_at_asc(seeded_runs_tree)
def test_descendant_count_is_subtree_size(seeded_runs_tree)
def test_failed_descendant_count_includes_stuck(seeded_runs_tree)
def test_total_cost_includes_self_and_descendants(seeded_runs_tree)
def test_wall_duration_seconds_l1_only(seeded_runs_tree)              # children don't get the field
def test_status_rollup_is_max_severity(seeded_runs_tree)              # failed > running > completed
def test_ctx_class_low_mid_high_buckets(seeded_runs_tree)
def test_ctx_class_none_when_context_usage_missing(seeded_runs_tree)
def test_rework_detection_consecutive_siblings_same_agent_task(seeded_runs_tree)
def test_rework_index_increments_per_repeat(seeded_runs_tree)
def test_rework_count_propagates_to_all_ancestors(seeded_runs_tree)   # rework at L3 visible on L1 rollup
def test_pagination_by_l1_only(seeded_runs_tree)                      # children don't count toward limit
def test_status_filter_uses_status_rollup(seeded_runs_tree)           # ?status=failed surfaces L1s with failed descendants
def test_exclude_test_filter_works(seeded_runs_tree)
def test_empty_db_returns_empty(empty_db)
def test_l1_with_no_children_has_descendant_count_zero(seeded_runs_tree)
def test_depth_cap_truncates_at_10(deep_chain_db)                     # 12-deep tree returns at most depth 10
```

`empty_db` is an existing fixture (or the seeded fixture parameterized to "no rows"). Reuse what's there; don't add a new helper fixture if one already exists.

For `test_depth_cap_truncates_at_10`: assert that the deepest descendant returned has `depth ≤ 9` (zero-indexed) AND that a server-warning was logged. Capture log output via the standard `caplog` fixture.

### Step 1.5: Extend `cast-server/tests/test_runs_api.py`

Add two cases:

```python
def test_list_runs_returns_l1_with_descendants(seeded_runs_tree)
    # GET /api/agents/runs?page=1
    # JSON response: top-level entries have populated `children` arrays
    # (Implementation note: this test will still pass even before sp2's route swap if
    #  the API serializer happens to surface the new shape — but the canonical signal
    #  comes after sp2 ships. Run this test green after sp1 by directly invoking the
    #  service in the test, OR mark with `pytest.mark.xfail(strict=True, reason="route
    #  swap lands in sp2")` and remove the xfail in sp2. Pick the latter — it documents
    #  the dependency.)
def test_list_runs_pagination_by_l1_only(seeded_runs_tree)
    # page=2 returns next 25 L1s, not L2s of page 1
    # Same xfail-on-sp1, clear-on-sp2 pattern.
```

**Decision for sp1:** Add the two cases with `pytest.mark.xfail(strict=True, reason="awaits sp2 route swap")` so the suite is green here and turns green-without-xfail in sp2. Sp2's plan includes "remove xfail markers" as an explicit step.

## Verification

### Automated Tests (permanent)
- `uv run pytest cast-server/tests/test_runs_tree.py` — all 19 cases green.
- `uv run pytest cast-server/tests/test_runs_api.py` — pre-existing cases still green; the 2 new cases xfail (strict).
- Full suite `uv run pytest` — no regressions.

### Validation Scripts (temporary)

```bash
# 1. Index exists in dev DB after server restart:
sqlite3 ~/.cast/diecast.db "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_agent_runs_parent'"
# Expect: idx_agent_runs_parent

# 2. EXPLAIN QUERY PLAN uses the index:
sqlite3 ~/.cast/diecast.db "EXPLAIN QUERY PLAN SELECT * FROM agent_runs WHERE parent_run_id = 'foo'"
# Expect: row mentioning USING INDEX idx_agent_runs_parent

# 3. get_runs_tree shape sanity (Python REPL or one-off script):
python3 -c "from cast_server.services.agent_service import get_runs_tree; \
            from pprint import pprint; \
            pprint(get_runs_tree()['runs'][0].keys() if get_runs_tree()['runs'] else 'empty')"
# Expect: keys include children, descendant_count, failed_descendant_count, rework_count,
#         status_rollup, total_cost_usd, wall_duration_seconds, ctx_class

# 4. Trimmed JSON columns (input_params/output/artifacts/directories absent or unparsed):
python3 -c "from cast_server.services.agent_service import get_runs_tree; \
            r = get_runs_tree()['runs'][0] if get_runs_tree()['runs'] else None; \
            print('input_params parsed?', isinstance(r.get('input_params'), dict) if r else 'no rows')"
# Expect: False (or KeyError) — confirming trim
```

### Manual Checks
- Restart the server. `tail -f` the server log; trigger a `/runs` page load. Confirm no truncation warnings unless you've intentionally seeded a deep chain.
- Run `pytest --co -q cast-server/tests/test_runs_tree.py` and confirm 19 tests are collected.

### Success Criteria
- [ ] `idx_agent_runs_parent` exists in `~/.cast/diecast.db`.
- [ ] `get_runs_tree` exists in `services/agent_service.py` and returns the documented dict shape.
- [ ] Tree-path rows parse only `context_usage` (other JSON columns NOT parsed).
- [ ] Severity ordering and ctx thresholds match `_shared_context.md`.
- [ ] Rework detection on consecutive siblings; `rework_count` propagates to ancestors.
- [ ] Depth cap truncates at 10 with a server-side warning.
- [ ] `status_filter=failed` returns L1s with failed descendants (rollup-aware).
- [ ] `seeded_runs_tree` and `deep_chain_db` fixtures committed to `conftest.py`.
- [ ] `test_runs_tree.py` 19/19 green.
- [ ] `test_runs_api.py` 2 new cases marked `xfail(strict=True)` with reason "awaits sp2 route swap".
- [ ] Full suite has no regressions.

## Execution Notes

- The recursive CTE is the riskiest piece. Test it early in isolation before plumbing rollups.
- `cost_usd` is nullable in `agent_runs`; treat `None` as `0.0` in sums.
- `started_at` and `completed_at` are stored as text in SQLite; parse with the existing helper used by `get_all_runs` (likely `datetime.fromisoformat`).
- The post-order DFS for rollups should be implemented as one walk that produces all rollup fields together — don't write four separate walks.
- The `_STATUS_SEVERITY` dict must include all known statuses; missing statuses default to lowest severity (e.g., `'completed'`). A test should pin the ordering literally.
- When seeding rework children, ensure `created_at` differs by at least 1 microsecond between siblings so the `ASC` sort is deterministic. Use `datetime.now(UTC) + timedelta(microseconds=N)`.
- The xfail markers in `test_runs_api.py` MUST set `strict=True` so they fail loudly if the bug accidentally fixes itself before sp2's intentional change.

**Spec-linked files:** None. This sub-phase touches `services/agent_service.py`, but the spec that links it (`cast-delegation-contract.collab.md`) covers `get_all_runs`-adjacent behaviors which this sub-phase does not modify.
