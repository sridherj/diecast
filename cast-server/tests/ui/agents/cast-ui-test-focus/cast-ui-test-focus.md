---
name: cast-ui-test-focus
description: >
  Diecast UI e2e: focus screen. Drives /focus in Chromium via Playwright
  (delegated to runner.py) — covers empty-state vs focused-goal branching.
tags:
  - test
  - ui
type: test
---

# cast-ui-test-focus

Drive the `focus` page of the Diecast UI in a Chromium browser via Playwright,
asserting smoke + functional behaviors.

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
  "agent_name": "cast-ui-test-focus",
  "task_title": "UI e2e: focus screen",
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
       --screen=focus \
       --base-url="<base_url>" \
       --goal-slug="<goal_slug>" \
       --output="<goal_dir>/runner-output.json"
   ```

   `${DIECAST_ROOT}` is the repo root; if it is not exported by the runtime, resolve it
   to the absolute path of the diecast checkout (the directory containing `cast-server/`).

4. After runner.py exits, read `runner-output.json` and emit the v2 envelope above to
   `<goal_dir>/.agent-<run_id>.output.json`. The `<run_id>` is provided in the runtime
   prompt preamble (`Your run ID: <run_id>`). Use the atomic-write pattern from
   `docs/specs/cast-delegation-contract.collab.md` § Atomic Write Contract (write to
   `.tmp` first, fsync, rename). Top-level `status`, `summary`, and `errors[]` are
   derived from the runner's output per the mapping in the Output section.

5. Exit cleanly. Exit code mirrors runner.py (0 = green, 1 = any failure).

## Screen-specific notes

Covers **US4 S9**.

- Asserts `/focus` loads and renders **either** a focused-goal block **or** a clean
  empty-state — both branches must be navigable without console errors.

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
