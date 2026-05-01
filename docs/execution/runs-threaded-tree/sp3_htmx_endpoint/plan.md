# Sub-phase 3: HTMX Status-Cells Partial Endpoint + Markup-Shape Test

> **Pre-requisite:** Read `docs/execution/runs-threaded-tree/_shared_context.md` and confirm sp2 is committed (`run_node.html` macro and `run_status_cells.html` fragment exist; both routes use `get_runs_tree`).

## Objective

Close the HTMX poll loop and lock the swap-target precision with a structural unit test. After this sub-phase, running rows poll the new `/api/agents/runs/{id}/status_cells` endpoint every 3s and update only the inner `.run-status-cells` span — the outer `.run-node` (carrying expand state) survives every poll. The new `test_runs_template.py` enforces this rule structurally so a future refactor cannot silently regress the swap target.

## Dependencies

- **Requires completed:** sp2 (macro + fragment + route swaps).
- **Assumed codebase state:** Pre-sp3 tree at HEAD + sp1 + sp2 commits. The fragment `run_status_cells.html` already carries conditional `hx-get="/api/agents/runs/{id}/status_cells"` — the URL exists in markup but the endpoint returns 404 on running rows.

## Scope

**In scope:**
- ADD `GET /api/agents/runs/{run_id}/status_cells` route to `cast-server/cast_server/routes/api_agents.py`. Uses the existing `get_run` service function (or whatever single-row helper is the canonical lookup) plus `_compute_rollups` / `_propagate_rework` over a one-row tree, then renders the existing `fragments/run_status_cells.html` with that single run dict. Returns 404 if the run id doesn't exist.
- NEW `cast-server/tests/test_runs_template.py` — markup-shape guard. Two tests:
  - `test_status_cells_carry_htmx_attrs(running_run_dict)` — render macro, parse HTML, assert `hx-get` / `hx-trigger` / `hx-swap` exist on `.run-status-cells`.
  - `test_run_node_does_not_carry_htmx_attrs(running_run_dict)` — outer `.run-node` MUST NOT have any `hx-*` attrs.

**Out of scope (do NOT do these):**
- The macro / fragment / CSS / route swaps — sp2 owns those.
- Inline JS — sp4.
- Deletion of the obsolete `/runs/{id}/row` endpoint — sp5 owns deletions even though `/status_cells` supersedes it functionally.
- UI test agent prompt edits — sp6.
- Spec capture — sp7.

## Files to Create/Modify

| File | Action | Current state |
|------|--------|---------------|
| `cast-server/cast_server/routes/api_agents.py` | Modify | Has `/runs/{id}/row` (line 234) and `/runs/{id}/children` (line 211); no `/runs/{id}/status_cells`. |
| `cast-server/tests/test_runs_template.py` | Create | Does not exist. |

## Detailed Steps

### Step 3.1: Add the `/status_cells` endpoint

Insert near the existing per-run endpoints in `routes/api_agents.py`. The exact position: alongside `/runs/{id}/row` (which sp5 will delete). Skeleton:

```python
@router.get("/runs/{run_id}/status_cells", response_class=HTMLResponse)
def status_cells(run_id: str, request: Request):
    """Render only the line-2 status cells for a single run.
    Used by the HTMX 3s poll on running rows so expand state on the outer .run-node
    is not disturbed.
    """
    run = get_run_with_rollups(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return templates.TemplateResponse(
        "fragments/run_status_cells.html",
        {"request": request, "run": run},
    )
```

Implementation choices:

- **Helper `get_run_with_rollups(run_id)`** in `services/agent_service.py`: fetches a single run + its descendants (the same recursive CTE from `get_runs_tree` parameterized by a single id), runs the same `_compute_rollups` and rework propagation, and returns the L1 run dict with `children` attached. Reuses sp1's helpers; no duplication. Add it next to `get_runs_tree`.
- **Why include rollups for a single-row poll?** The fragment renders `descendant_count`, `failed_descendant_count`, `rework_count`, etc. These can change between polls (a child finished, a rework was triggered). The cost is bounded — single-tree subset of the same query.
- **Cache headers:** none — explicitly cacheless, the whole point is fresh data every 3s.

### Step 3.2: Write `test_runs_template.py`

```python
"""Markup-shape guard for the threaded /runs page.

Asserts that HTMX swap-target attributes (hx-get/hx-trigger/hx-swap) live on the
INNER .run-status-cells span, NEVER on the outer .run-node container. The outer
node carries expand state (.expanded class set by inline JS) and must survive 3s
polls. This is a CAUSE-LEVEL guard — symptom-level UI tests pass during the wait
window even if a future refactor breaks the target.
"""

from __future__ import annotations

import pytest
from bs4 import BeautifulSoup

from cast_server.app import templates  # or wherever the Jinja env lives


@pytest.fixture
def running_run_dict() -> dict:
    return {
        "id": "run_test_running_001",
        "agent_name": "cast-preso-how",
        "status": "running",
        "ctx_class": "mid",
        "descendant_count": 0,
        "failed_descendant_count": 0,
        "rework_count": 0,
        "total_cost_usd": 0.0,
        "wall_duration_seconds": None,
        "active_seconds": 42,
        "children": [],
        "is_rework": False,
        "rework_index": None,
        "created_at": "2026-05-01T12:00:00+00:00",
        "resume_command": "diecast resume run_test_running_001",
        "goal_slug": "preso-test",
        "task_id": None,
        "task_title": None,
    }


def _render_node(run: dict) -> BeautifulSoup:
    macro = templates.get_template("macros/run_node.html").module
    html = macro.render_run(run)
    return BeautifulSoup(html, "html.parser")


def test_status_cells_carry_htmx_attrs(running_run_dict):
    soup = _render_node(running_run_dict)
    cells = soup.select_one(".run-status-cells")
    assert cells is not None, "fragment should render a .run-status-cells span"
    assert cells.get("hx-get"), ".run-status-cells must carry hx-get on running runs"
    assert cells.get("hx-trigger") == "every 3s"
    assert cells.get("hx-swap") == "outerHTML"
    assert "/status_cells" in cells["hx-get"]


def test_run_node_does_not_carry_htmx_attrs(running_run_dict):
    soup = _render_node(running_run_dict)
    node = soup.select_one(".run-node")
    assert node is not None, "macro should render a .run-node container"
    for attr in ("hx-get", "hx-post", "hx-trigger", "hx-swap"):
        assert not node.has_attr(attr), (
            f".run-node must NOT carry {attr}; "
            f"that would defeat poll-safety on expand state"
        )


def test_completed_run_status_cells_have_no_hx_attrs(running_run_dict):
    """Completed runs don't poll. The conditional in the fragment must hold."""
    completed = {**running_run_dict, "status": "completed"}
    soup = _render_node(completed)
    cells = soup.select_one(".run-status-cells")
    assert cells is not None
    for attr in ("hx-get", "hx-trigger", "hx-swap"):
        assert not cells.has_attr(attr), f"completed runs must not carry {attr}"
```

Notes:
- `bs4` (BeautifulSoup) is already a dev-dep in the cast-server test layer — verify with `uv pip list | grep beautifulsoup4`. If not, add it to `pyproject.toml`'s test extras.
- Three tests, not two. Plan called for two; the third (`test_completed_run_status_cells_have_no_hx_attrs`) closes the negative case the conditional fragment depends on. Kept inside this sub-phase because it's part of the same structural guard.
- The fixture is a hand-built dict that satisfies the macro's expectations. Don't reach into the database — this is a markup test, not a service test.

### Step 3.3: Manual sanity-check of the new endpoint

```bash
# Find a running run id (or trigger a long-running agent if none exists).
sqlite3 ~/.cast/diecast.db "SELECT id FROM agent_runs WHERE status='running' LIMIT 1"

# Hit the endpoint:
curl -s http://127.0.0.1:8000/api/agents/runs/<id>/status_cells | head -50

# Expect: a <span class="run-status-cells row-2" id="run-cells-<id>" ... > with the cells inside.
```

In the browser, expand a running run's row, wait 6+ seconds, and confirm the cells refresh without losing the expand state.

## Verification

### Automated Tests (permanent)
- `uv run pytest cast-server/tests/test_runs_template.py` — 3/3 green.
- Full suite `uv run pytest` — no regressions.

### Validation Scripts (temporary)

```bash
# 1. Endpoint exists in the route module:
grep -n 'status_cells' cast-server/cast_server/routes/api_agents.py
# Expect: route definition + path string.

# 2. Endpoint returns the fragment and 404s on missing id:
curl -sw '%{http_code}\n' -o /dev/null http://127.0.0.1:8000/api/agents/runs/nonexistent/status_cells
# Expect: 404

# 3. The structural guard catches a regression — proof exercise:
#    Temporarily move hx-get from the inner span to the outer node in run_node.html;
#    re-run pytest; confirm test_run_node_does_not_carry_htmx_attrs FAILS.
#    Then revert.
```

### Manual Checks
- Browser: expand a running row at depth 2 inside an L1 group. Wait 9 seconds (3 polls). Confirm the row stays expanded throughout AND the status pill / duration / cost values update if the underlying run state changed.
- Open DevTools → Network. Confirm the polling target is `/api/agents/runs/{id}/status_cells` and returns ~1 KB of HTML (not the entire row).

### Success Criteria
- [ ] `GET /api/agents/runs/{id}/status_cells` returns the rendered fragment with rollups.
- [ ] 404 on missing id.
- [ ] `test_runs_template.py` exists with 3 passing tests.
- [ ] Manually verified: running row polls without losing expand state.
- [ ] Network panel confirms the inner-span swap (target is `.run-status-cells`, not `.run-node`).
- [ ] Full suite green.

## Execution Notes

- The endpoint is intentionally additive — sp5 will delete the now-superseded `/runs/{id}/row`. Do NOT delete it here; that's outside scope and bundling it conflicts with sp5's grep gate.
- `get_run_with_rollups` should reuse `_compute_rollups`, `_detect_rework`, and `_propagate_rework` from sp1 — do not re-implement them.
- If `bs4` isn't already a test dep, prefer adding it (it's a small, well-understood lib used elsewhere in the codebase) over hand-rolling regex parsing of HTML.
- The fragment polls itself: `hx-swap="outerHTML"` replaces the span with a fresh render that ALSO carries the same hx-* attrs. The conditional fires anew on each render, so the moment a run transitions to `completed`/`failed` etc., the next swap will return a span without hx-* and the polling stops.
- The L3 expand panel (`<div class="detail">`) is OUTSIDE the swapped span — its visibility (controlled by sp4's JS via `.expanded` on `.run-node`) is preserved.

**Spec-linked files:** None this sub-phase.
