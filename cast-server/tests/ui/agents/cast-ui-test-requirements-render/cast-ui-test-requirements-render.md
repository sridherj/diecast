---
name: cast-ui-test-requirements-render
description: >
  Diecast UI e2e: the Phase-4 requirements-render comment flows. Drives
  /goals/<slug>/render in Chromium via Playwright (delegated to runner.py) —
  select→pill→composer→<mark>, resolve from the thread, version toggle→diff,
  and a displaced comment surfacing in the tray after a reword.
tags:
  - test
  - ui
type: test
---

# cast-ui-test-requirements-render

Drive the Phase-4 commenting + version-diff UX on the read-only requirements render in a
Chromium browser via Playwright, asserting the locked UX (decisions #7/#8/#1) against the
real selectors named in the Phase-4 plan.

## Inputs (from delegation_context)

- `goal_slug` (required, string): the shared test goal slug, format
  `ui-test-<unix_ts>-<rand4>`. **Note:** this screen *self-seeds its own* render goal
  (`ui-test-render-<ts>`) inside the runner, because the render requires a
  `refined_requirements.collab.md` + a version snapshot; the shared `goal_slug` is still
  passed (runner.py requires the flag) but is not used by the render assertions.
- `base_url` (optional, string, default `http://127.0.0.1:8006`): test server.

## Output

Write `.agent-<run_id>.output.json` in the goal directory using the cast contract-v2
envelope (see `docs/specs/cast-output-json-contract.collab.md`). The runner's per-screen
detail (assertions, screenshots, console events) is referenced as `artifacts[0]`,
NOT inlined at the top level.

```json
{
  "contract_version": "2",
  "agent_name": "cast-ui-test-requirements-render",
  "task_title": "UI e2e: requirements-render comment flows",
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

1. Read the canonical delegation contract: `/cast-child-delegation`. This child does not
   delegate further.

2. Resolve the runner output path inside this run's goal directory, e.g.:
   `<goal_dir>/runner-output.json`.

3. Invoke the runner via direct script path (DO NOT use the `-m` module flag). Pass the
   dashed screen name — runner.py normalizes the dash to underscore internally:

   ```bash
   "${DIECAST_ROOT}/.venv/bin/python" "${DIECAST_ROOT}/cast-server/tests/ui/runner.py" \
       --screen=requirements-render \
       --base-url="<base_url>" \
       --goal-slug="<goal_slug>" \
       --output="<goal_dir>/runner-output.json"
   ```

   `${DIECAST_ROOT}` is the repo root; if it is not exported by the runtime, resolve it
   to the absolute path of the diecast checkout (the directory containing `cast-server/`).

4. After runner.py exits, read `runner-output.json` and emit the v2 envelope above to
   `<goal_dir>/.agent-<run_id>.output.json` (atomic write: `.tmp` → fsync → rename). Derive
   top-level `status`, `summary`, and `errors[]` from the runner output per the mapping.

5. Exit cleanly. Exit code mirrors runner.py (0 = green, 1 = any failure).

## Screen-specific notes

Covers the Phase-4 render-page flows mandated by `cast-ui-testing.collab.md` US2:

- **Flow A — select → 💬 pill → composer → `<mark>`** (decision #7): selects a stable quote
  in `.rr-document`, asserts `.comment-pill`, opens `.comment-composer`, submits, and waits
  for `mark.comment-mark`.
- **Agent parity (FR-013):** posts a comment through the SAME
  `/api/goals/<slug>/requirements/comments` door an agent curls (`author_kind="agent"`) and
  asserts it also yields a `<mark>` — no privileged UI write path.
- **Flow B — resolve from the thread:** clicks `.comment-resolve-btn` on an open
  `.comment-thread-item`, asserts it swaps to `data-state="resolved"`.
- **Flow D — displaced → tray** (decision #1): rewords the source + `POST …/versions`, then
  asserts the now-displaced comment surfaces under `.comment-tray [data-group="displaced"]`
  with `data-displaced="true"` (never as a body `<mark>`).
- **Flow C — version toggle → diff** (decision #8): clicks `.version-toggle__diff`, lands on
  `/goals/<slug>/render/diff`, asserts the tracked-changes view (`.diff-changed-panel` /
  `.diff-added` / `.diff-removed`).

## Constraints

- Do NOT touch the dev server on `:8000`.
- Per-assertion timeout: 30s (enforced by runner.py).
- This child's wall-clock cap (orchestrator-imposed): 600s.
- Console error policy: `level=='error'` or `level=='pageerror'` fail the run; warnings are
  recorded but do not fail (runner.py enforces).
- The self-seeded render goal is named `ui-test-render-*`, so the harness teardown's
  `goals/ui-test-*` sweep removes its working-tree dir.
- If runner.py exits non-zero, this agent MUST still emit the v2 envelope with
  `status: "failed"` and `errors[]` populated. Do NOT swallow failures.
