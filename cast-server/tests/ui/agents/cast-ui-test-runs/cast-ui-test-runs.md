---
name: cast-ui-test-runs
description: >
  Diecast UI e2e: threaded /runs screen. Drives the recursive parent/child
  tree layout in Chromium via Playwright (delegated to runner.py) — exercises
  threaded-layout markup, ctx pills, rework propagation, group borders,
  collapse persistence, clipboard, HTMX-poll expand stability, mobile
  breakpoints, and the trigger-and-cancel flow.
tags:
  - test
  - ui
type: test
---

# cast-ui-test-runs

Drive the threaded `/runs` page of the Diecast UI in a Chromium browser via
Playwright, asserting smoke + threaded-layout + functional behaviors.

## Inputs (from delegation_context)

- `goal_slug` (required, string): shared test goal slug, format `ui-test-<unix_ts>-<rand4>`.
- `base_url` (optional, string, default `http://127.0.0.1:8006`): test server.

## Output

Write `.agent-<run_id>.output.json` in the goal directory using the cast contract-v2
envelope (see `docs/specs/cast-output-json-contract.collab.md`). The runner's per-screen
detail (assertions, screenshots, console events) is referenced as `artifacts[0]`,
NOT inlined at the top level — top-level fields belong to the v2 contract.

```json
{
  "contract_version": "2",
  "agent_name": "cast-ui-test-runs",
  "task_title": "UI e2e: runs screen",
  "status": "completed | failed",
  "summary": "<N> assertions passed, <M> failed; <K> console errors. See artifact for detail.",
  "artifacts": [
    {
      "path": "runner-output.json",
      "type": "data",
      "description": "Per-screen runner detail: assertions_passed/failed, console_errors/warnings, screenshots, screen, started_at, finished_at"
    }
  ],
  "errors": [],
  "next_steps": [],
  "human_action_needed": false,
  "human_action_items": [],
  "started_at": "ISO8601 (matches runner)",
  "completed_at": "ISO8601 (when this file was written)"
}
```

Status mapping:
- `completed` — runner exit code 0 AND empty `assertions_failed` AND empty `console_errors`
- `failed` — runner exit code non-zero OR any `assertions_failed` entry OR any `console_errors`

`errors[]` mirrors the runner's `assertions_failed` list (verbatim strings). Leave empty
on success.

## Procedure

1. Read the canonical delegation contract: `/cast-child-delegation`. Apply it for any
   future sub-delegation; this child does not delegate further.

2. Resolve the runner output path inside this run's goal directory, e.g.:
   `<goal_dir>/runner-output.json`.

3. Invoke the runner via direct script path (DO NOT use the `-m` module flag):

   ```bash
   "${DIECAST_ROOT}/.venv/bin/python" "${DIECAST_ROOT}/cast-server/tests/ui/runner.py" \
       --screen=runs \
       --base-url="<base_url>" \
       --goal-slug="<goal_slug>" \
       --output="<goal_dir>/runner-output.json"
   ```

   `${DIECAST_ROOT}` is the repo root; if it is not exported by the runtime, resolve it
   to the absolute path of the diecast checkout (the directory containing `cast-server/`).
   The `CAST_DB` env var is propagated by the test cast-server fixture and is read by
   `runner.py` to seed threaded-layout fixtures directly into the test SQLite DB.

4. After runner.py exits, read `runner-output.json` and emit the v2 envelope above to
   `<goal_dir>/.agent-<run_id>.output.json`. The `<run_id>` is provided in the runtime
   prompt preamble (`Your run ID: <run_id>`). Use the atomic-write pattern from
   `docs/specs/cast-delegation-contract.collab.md` § Atomic Write Contract (write to
   `.tmp` first, fsync, rename). Top-level `status`, `summary`, and `errors[]` are
   derived from the runner's output per the mapping in the Output section.

5. Exit cleanly. Exit code mirrors runner.py (0 = green, 1 = any failure).

## Screen-specific assertions (threaded layout)

Covers **US4 S7, S7b** plus the threaded-layout assertions locked by the
`cast-runs-threaded-tree` plan. The runner seeds five trees via direct SQLite
write to `CAST_DB` before any navigation; each assertion below references the
seeded run by `data-run-id`.

| # | Assertion | Selector | Expected | Seed |
|---|-----------|----------|----------|------|
| 1 | Threaded markup classes are present | `.run-group`, `.run-node`, `.thread`, `.ctx-pill` | At least one node of each is attached | any seed |
| 2 | Two-line layout | `.run-node .row-1 .status-dot`, `.row-1 .agent-name`, `.row-2 .pill` | All three exist on the first run-node | any seed |
| 3 | Eager tree (no HTMX wait for descendants) | `[data-run-id='thread-deeprework-l3a']` | Attached on initial page load | tree C (deep rework) |
| 4 | Pagination preserves tree shape on page 2 | `.pagination .pagination-btn:has-text('Next')` | If present, click and verify `.run-group .thread` still attached | runtime-only — skipped when ≤25 L1 |
| 5 | Click row toggles `.expanded` | `[data-run-id='thread-failed-l1']` | After click, `class` includes `expanded` | tree B (has-failure) |
| 6 | Reload preserves expand via localStorage | `localStorage["runs:expanded:thread-failed-l1"] === "1"` and class `.expanded` re-applies after reload | Survives full page reload | tree B (after #5) |
| 7 | `.copy-resume` writes clipboard, no expand | `.copy-resume` inside `[data-run-id='thread-warning-l1']` | Clipboard contains `thread-warning-l1`; row class does NOT include `expanded` | tree A; uses `grant_clipboard` |
| 8 | `ctx_class` pill tints + high-ctx child name colored | `.ctx-pill.low/.mid/.high`, `.run-node.is-child.ctx-high .agent-name` | Each pill class has ≥1 element; high-ctx child name node exists | tree D (ctx pills) |
| 9 | Failed-descendant border | ancestor `.run-group` of `[data-run-id='thread-failed-l1']` | Class includes `has-failure` | tree B |
| 10 | Rework-only border (closes asymmetric coverage gap) | ancestor `.run-group` of `[data-run-id='thread-warning-l1']` | Class includes `has-warning` | tree A |
| 11 | `.rework-tag` on second instance + L1 rollup propagates from deep rework | `[data-run-id='thread-warning-c2'] .rework-tag`, `[data-run-id='thread-deeprework-l1'] .rollup.warn` | First exists; rollup text contains `reworked` | trees A + C |
| 12 | Status filter `?status=failed` is rollup-aware | After `GET /runs?status=failed`, `[data-run-id='thread-failed-l1']` | Attached (Decision #13: rollup-aware filter surfaces L1 whose own status is `completed` but with a failed descendant) | tree B |
| 13 | HTMX poll preserves parent expand state | Expand `[data-run-id='thread-running-l1']`, then `wait_for_htmx_settle(4000)` | Expanded class still present after the 3s poll cycle on the running child | tree E (running child) |
| 14 | Mobile viewport (480×800) hides chrome | After `resize_viewport(480, 800)`, `.run-node .relative-time`, `.run-node .crumbs .task` | Both not visible (display: none via media query) | any seed |

Plus the existing trigger-and-cancel flow (US4 S7), updated for the new
`[data-run-id]` markup:

- Trigger `cast-ui-test-noop --sleep=20` via `POST /api/agents/.../trigger`.
- Click `[data-run-id="<run_id>"]` to expand the run-node.
- Click the cancel button (`button[hx-post='/api/agents/runs/<run_id>/cancel']`)
  inside `.detail .actions`.
- Poll `GET /api/agents/jobs/<run_id>` and assert `status == "cancelled"`
  within 8s.

### runner.py helpers used

The runner exposes additive primitives that this agent prompt depends on:

- `grant_clipboard(context)` — wraps `context.grant_permissions([…])` for
  assertion #7. Called once before any `.copy-resume` click.
- `resize_viewport(page, width, height)` — wraps
  `page.set_viewport_size({…})` for assertion #14.
- `read_clipboard(page)` — `page.evaluate("navigator.clipboard.readText()")`.
- `read_localstorage(page, key)` —
  `page.evaluate("localStorage.getItem(<key>)")` for assertion #6.
- `wait_for_htmx_settle(page, timeout_ms=4000)` — resolves on
  `htmx:afterSwap` or after the timeout, used by assertion #13.

Seed data is keyed by `THREADED_SEED_GOAL_SLUG=ui-test-runs-threaded` and uses
stable ids prefixed `thread-`. INSERT OR IGNORE keeps the seed idempotent
across re-runs of the harness.

## Constraints

- Do NOT touch the dev server on `:8000`.
- Per-assertion timeout: 30s (enforced by runner.py).
- This child's wall-clock cap (orchestrator-imposed): 600s.
- Console error policy: `level=='error'` or `level=='pageerror'` fail the run; warnings
  are recorded but do not fail (Decision #6, runner.py enforces).
- If runner.py exits non-zero, this agent MUST still emit the v2 envelope with
  `status: "failed"` and `errors[]` populated from the runner's `assertions_failed`.
  The runner's full output remains available via `artifacts[0].path`. Do NOT swallow
  failures.
