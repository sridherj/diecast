# sp4 — Layer B Assertion Fixes — Verification Log

## Summary

Patched 5 per-screen `_assert_<screen>` functions in
`cast-server/tests/ui/runner.py`. Three classes of drift were repaired:

1. Selectors / classes that don't exist in any template (e.g., `.agent-card`,
   `.tab[data-tab=…]`, `.runs-tab[data-status=…]`, `.empty-state`, `.focus-goal`).
2. JSON endpoints that don't exist in any route file (`GET /api/agents` —
   no route returns a JSON list; the registry is rendered as HTML cards).
3. Features that don't exist anywhere (scratchpad entry deletion — no DELETE
   route, no delete control in the template/fragment).

Class 1 → re-pointed selectors at the real markup.
Class 2 → removed the assertion (B3 — feature does not exist).
Class 3 → removed the assertion (B3 — feature does not exist).

## Per-screen change list (all in `cast-server/tests/ui/runner.py`)

| Function | Assertion | Before (fictional) | After (real, evidence) |
|----------|-----------|--------------------|------------------------|
| `_assert_agents` | `agents_api_returns_entries` | `_http_get_json(f"{base_url}/api/agents")` | **REMOVED (B3)** — `cast_server/routes/api_agents.py` exposes no `GET /api/agents` JSON list (only `/{name}/trigger`, `/jobs/{run_id}`, `/runs`, `/runs/{run_id}/...`). The agent registry is rendered as cards in `templates/pages/agents.html`. |
| `_assert_agents` | `agents_filter_button_toggle` | `["button.filter-btn", "button[data-filter]", ".agents-filters button"]` candidates loop with hidden `clicked = False` flag | `.agents-filters button.filter-btn` (matches `templates/pages/agents.html:12-18`) — direct selector, no candidate fallback. |
| `_assert_agents` | `agents_card_details_expand` → renamed `agents_card_visible` | `.agent-card` (no such class) | `.agents-grid-card` — matches `templates/pages/agents.html:21`. (The `<details>` toggle in the card is conditional on `agent.input/output/last_tested` being set, so dropping the click and just verifying the card is visible is the honest assertion.) |
| `_assert_runs` | `runs_tab_<name>` | `[".runs-tab[data-status=…]", "button[data-status=…]", "a[href*='status=…']", ".tab[data-tab=…]"]` candidates | `.runs-filters button.filter-btn[hx-get*='status=<name>']` — matches `templates/pages/runs.html:33-54` exactly (4 buttons: all/running/completed/failed). |
| `_assert_scratchpad` | `scratchpad_delete_entry` | `button.delete, button:has-text('Delete'), button[hx-delete]` inside `.scratchpad-entry` | **REMOVED (B3)** — `cast_server/routes/api_scratchpad.py` exposes only `GET ""` and `POST ""` (no DELETE route). `templates/pages/scratchpad.html` and `templates/fragments/scratchpad_entry.html` render entries with bullet + content only — no delete control of any kind. |
| `_assert_goal_detail` | `goal_detail_has_tabs` + `goal_detail_tab_click_<n>` | `.phase-tab, .tab, [role='tab']` | `.tab-bar button.tab-btn` — matches `templates/pages/goal_detail.html:93-115` (5 tabs: overview + 4 phases, all rendered as `button.tab-btn[data-tab=…]` inside `.tab-bar`). |
| `_assert_focus` | `focus_renders_content_or_empty_state` | `.focus-task, .focus-goal, .empty-state, main` | `.focus-goal-card, .empty-state-page` — matches `templates/pages/focus.html:12, 47`. The previous `main` fallback always passed (every page has `<main>` in `base.html`), so the assertion was effectively meaningless; the new selector actually exercises the page-specific markup. |

Total assertions: −2 removed (B3), 5 retargeted, 1 renamed.

## What was NOT changed (and why)

- `_assert_dashboard` — selectors already match the real template
  (`.dashboard-tab`, `#create-goal-form`, `button[aria-label='Create new goal']`,
  `#goal-card-{slug}`). The pre-Layer-A run reported a `/api/goals` 500 here;
  that is a Layer C product bug and out of scope.
- `_assert_runs::runs_trigger_and_cancel_noop` — `#run-{run_id}`, `.run-row`,
  `button.cancel-btn`, `data-status` all match `templates/fragments/run_row.html`.
  Whatever this assertion catches now is Layer C territory.
- `_assert_goal_detail::goal_detail_accept_idea` — `button[hx-vals*='"status": "accepted"']`
  matches `templates/pages/goal_detail.html:55-60`.
- `_assert_goal_detail::goal_detail_phase_advance` — only runs when
  `goal_status == "accepted"`. Seeded test goal starts as `idea`, transitions to
  `accepted` via the prior assertion, but the `_assert_goal_detail` flow only
  reads `goal_status` once at the top, so this branch is never reached in a
  single child run. Left as-is; not a Layer B miss.
- `_assert_goal_detail::goal_detail_focus_toggle` — `button.focus-star` matches
  `templates/pages/goal_detail.html:21-31` exactly.
- `_assert_goal_detail::goal_detail_task_create` — `form input[name='title']`
  matches the Add Task form at `templates/pages/goal_detail.html:140-194`.
- `_assert_goal_detail::goal_detail_trigger_noop` — uses the real
  `/api/agents/cast-ui-test-noop/trigger` route. Pre-Layer-A this surfaced an
  empty error; if it still fails post-Layer-A that is a Layer C dispatcher bug.
- `_assert_about` — `main, body` is fine; about page is essentially static.

## Spot check (static cross-reference)

Every CSS selector and URL in the post-sp4 `_assert_<screen>` functions was
matched against `cast-server/cast_server/templates/{pages,fragments,components}/`
and `cast-server/cast_server/routes/api_*.py`. No remaining selector references
a `data-testid`, class, or route that doesn't appear in the source.

Specifically grep-verified:

```
$ grep -rn 'class="agents-grid-card"' cast-server/cast_server/templates/pages/agents.html
21:        <div class="agents-grid-card" ...

$ grep -rn 'class="filter-btn' cast-server/cast_server/templates/pages/runs.html
34: <button class="filter-btn ..." hx-get="/api/agents/runs?status=all"
39: <button class="filter-btn ..." hx-get="/api/agents/runs?status=running"
44: <button class="filter-btn ..." hx-get="/api/agents/runs?status=completed"
49: <button class="filter-btn ..." hx-get="/api/agents/runs?status=failed"

$ grep -rn 'class="tab-btn' cast-server/cast_server/templates/pages/goal_detail.html
95: <button class="tab-btn active" data-tab="overview" ...
99: <button class="tab-btn" data-tab="{{ phase }}" ...

$ grep -rn 'class="focus-goal-card\|class="empty-state-page"' cast-server/cast_server/templates/pages/focus.html
12: <div class="focus-goal-card">
47: <div class="empty-state-page">

$ grep -nE '@router\.(get|post|put|delete|patch)' cast-server/cast_server/routes/api_scratchpad.py
15:@router.get("")
24:@router.post("")
```

## Dynamic verification — BLOCKED (environment, not test code)

Per the sub-phase plan, after the static fixes we attempted to re-run the
harness:

```
KEEP_UITEST_ARTIFACTS=1 uv run pytest cast-server/tests/ui/test_full_sweep.py -v --tb=short
```

Two attempts, two distinct environmental failures:

1. **First attempt (12:25 local)** — health check passed, orchestrator was
   triggered (`run_id=run_20260501_065536_980e8b`), but the very first
   `GET /api/agents/jobs/{run_id}` poll timed out twice in a row at 60s each.
   The test cast-server's stdout log only contained Alembic stamp output and
   never any `Application startup complete` line or any HTTP-request log,
   suggesting the server was wedged behind something heavy (likely the
   orchestrator's child-fan-out spawning seven tmux+claude subprocesses). Test
   exited with `TimeoutError: timed out` after 213s.

2. **Second attempt (12:35 local)** — `_wait_for_health` itself failed in
   30s. The server was started but did not pass the `/api/health` probe
   in its 30s window.

3. **Third attempt (12:45 local)** — `uv run` errored out before pytest
   even started:
   ```
   warning: Ignoring existing virtual environment linked to non-existent Python interpreter: .venv/bin/python3 -> python
   error: failed to remove directory `<DIECAST_ROOT>/.venv/lib64`: Permission denied (os error 13)
   ```
   The repo's `.venv/` is now owned by `root`, and `uv` cannot rebuild it
   without elevated privileges. Inspecting:
   ```
   $ ls -la <DIECAST_ROOT>/.venv/
   drwxr-xr-x 5 root root ... .venv/
   ```
   The `python` symlink inside also dangles (`-> /usr/local/bin/python3`,
   which does not exist on this host). This is a host/env issue from a prior
   process running with elevated perms; it is not produced by this sub-phase.

None of these three failure modes is in `runner.py` or in any file sp4 is
allowed to edit. They are Layer A / harness / environment issues. Per the
sub-phase plan's explicit scope (`Edit only runner.py _assert_<screen>
functions`), they are out of scope here.

## Acceptance Criteria Status

| AC | Status | Evidence |
|----|--------|----------|
| Every remaining `assertions_failed[]` references a real selector/endpoint | **PASS (static)** | Cross-referenced every CSS selector & URL in every `_assert_<screen>` function against `templates/` and `routes/`. Each one resolves. |
| No assertion deleted to make tests green except where feature doesn't exist | **PASS** | The two deletions (`agents_api_returns_entries`, `scratchpad_delete_entry`) are documented above and in inline comments in `runner.py` with B3 rationale (feature/route does not exist). |
| Re-running the harness produces a strictly smaller red list, every remaining failure is reproducible by manual click-through | **DEFERRED** | Dynamic re-run blocked by `.venv/lib64` permission failure under `uv run` and prior server-startup flake. Patches are static-verified; pending a clean harness boot for live confirmation. |
| Only `runner.py` changed in this sub-phase | **PASS** | `git status` shows `runner.py` is the only file in `cast-server/tests/ui/` touched by sp4. |

## Human action needed before sp5

Two unblockers, both outside sp4 scope:

1. Restore ownership of `<DIECAST_ROOT>/.venv/` to the user account
   (or wipe and let `uv sync` rebuild it as the user). After that, re-run
   `uv run pytest cast-server/tests/ui/test_full_sweep.py` to capture the
   post-sp4 red list.
2. Once the red list is captured, classify each remaining
   `assertions_failed[]` entry as Layer C (real product bug → sp5 ticket on
   `comprehensive-ui-test`) or Layer B (still a wrong assertion → another sp4
   pass).
