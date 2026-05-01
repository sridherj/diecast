# Shared Context: Cast-UI Harness Layered Fixes

## Source Documents

- **Plan (do not modify):** `/data/workspace/diecast/docs/plan/2026-05-01-cast-ui-harness-layered-fixes.collab.md`
- **Governing spec:** `/data/workspace/diecast/docs/specs/cast-ui-testing.collab.md`
- **Original harness plan:** `/data/workspace/diecast/docs/plan/2026-05-01-cast-ui-e2e-test-harness.collab.md`
- **Output-filename contract:** `/data/workspace/diecast/docs/specs/cast-output-json-contract.collab.md`
- **Original execution dir (built the harness this plan repairs):** `/data/workspace/diecast/docs/execution/cast-ui-test-harness/`

## Project Background

The cast-UI e2e harness (`pytest cast-server/tests/ui/`) is in place and boots, dispatches,
polls, and tears down cleanly. But running it currently produces 1/7 passing children, and
**most of the 6 failures are NOT real product bugs** — they're harness-layer or
test-assertion bugs that mask whatever's actually wrong.

This execution plan removes the failure modes in strict dependency order:

- **Layer A — test infrastructure (sp1, sp2, sp3):** the harness must report honestly
  before any other fix can be evaluated.
  - sp1 (FR-001): the parent test reads the wrong path for the orchestrator's terminal
    output JSON, so it can't see the orchestrator's true `partial`/`completed`/`failed`
    status. Fix the path; no scan fallback.
  - sp2 (FR-002): the test cast-server's stdout/stderr is captured to `subprocess.PIPE`
    and never read, so any 500 on the server side is invisible. Pipe to a tempfile and
    dump the last 200 lines on failure via `pytest_runtest_makereport`.
  - sp3 (FR-003): every `page.goto` in the runner uses `wait_until="networkidle"`, which
    times out forever against HTMX polling pages. Switch to `domcontentloaded` and rely
    on Playwright's per-assertion auto-wait.

- **Layer B — test assertions (sp4):** once Layer A surfaces real signal, each remaining
  red child likely has assertions targeting selectors or endpoints that don't exist in
  the implementation. Patch the per-screen `_assert_<screen>` functions in `runner.py`
  to reference real selectors/routes. No assertion deletion to make tests green —
  delete only if the feature being tested doesn't exist.

- **Layer C — real bugs (sp5):** whatever's still red after Layer A + Layer B are in
  place is a genuine cast-server bug. File one Diecast task per bug on the existing
  `comprehensive-ui-test` goal (status='suggested' or 'todo'). Tagged with assertion
  name + manual reproduction recipe + root-cause hypothesis. **Bugs themselves are
  fixed in separate plans/tasks downstream — out of scope here.**

## Codebase Conventions

- **Repo root:** `/data/workspace/diecast/`
- **Server package:** `cast-server/cast_server/` (Python). Routes under `routes/api_*.py`,
  services under `services/`, templates under `templates/pages/` and `templates/fragments/`.
- **Test entry:** `cast-server/tests/ui/test_full_sweep.py::test_ui_e2e`.
- **Test harness scaffolding:** `cast-server/tests/ui/conftest.py` (fixtures), `runner.py`
  (Playwright per-screen helper).
- **Test agents:** `cast-server/tests/ui/agents/cast-ui-test-*/` — orchestrator + 7
  per-screen children + a `noop` agent.
- **Test cast-server port:** `127.0.0.1:8006` (dev server stays on `:8000`/`:8005`,
  do NOT touch).
- **Goal-artifact directory contract** (per `cast-output-json-contract.collab.md:35`):
  every agent's terminal output JSON lives at
  `<goal_dir>/.agent-run_<RUN_ID>.output.json`. Where `<goal_dir>` is
  `goals/<goal_slug>/` and `<RUN_ID>` is the run_id returned at trigger time.

## Key File Paths

| File | Role |
|------|------|
| `cast-server/tests/ui/test_full_sweep.py` | Pytest entry. Has `_read_orchestrator_output` (line 86) — sp1 rewrites this. |
| `cast-server/tests/ui/conftest.py` | Fixtures. `test_server` fixture (line 107) currently pipes stdout but never reads it — sp2 fixes this. |
| `cast-server/tests/ui/runner.py` | Playwright helper. Eleven `page.goto(..., wait_until="networkidle")` and two `page.wait_for_load_state("networkidle", ...)` calls — sp3 migrates them. Per-screen `_assert_<screen>` functions — sp4 patches these. |
| `cast-server/tests/ui/agents/cast-ui-test-*/` | Per-screen test agents (do NOT modify in this plan; sp4 only edits `runner.py`). |
| `cast-server/cast_server/routes/api_agents.py` | Real `/api/agents/*` HTML-fragment routes that sp4 may need to verify. |
| `cast-server/cast_server/templates/pages/agents.html` | Agents page template — sp4 reference for selectors. |
| `cast-server/cast_server/templates/pages/scratchpad.html` | Scratchpad page — sp4 reference. |
| `cast-server/cast_server/templates/pages/dashboard.html` | Dashboard page — sp4 reference. |
| `cast-server/cast_server/templates/pages/runs.html` | Runs page — sp4 reference. |
| `cast-server/cast_server/templates/pages/goal_detail.html` | Goal-detail page — sp4 reference. |
| `cast-server/cast_server/templates/pages/focus.html` | Focus page — sp4 reference. |
| `cast-server/cast_server/templates/pages/about.html` | About page — sp4 reference. |
| `docs/specs/cast-output-json-contract.collab.md` | Canonical output-path contract sp1 enforces. |

## Data Schemas & Contracts

### Orchestrator output JSON path (FR-001)

Canonical, deterministic, no fallback:

```
<repo_root>/goals/<orchestrator_goal_slug>/.agent-run_<orchestrator_run_id>.output.json
```

- `<orchestrator_goal_slug>` is the `seeded_test_goal` slug (`ui-test-<unix_ts>-<rand4>`).
- `<orchestrator_run_id>` is the run_id returned by the trigger response in
  `test_full_sweep.py` (currently captured into local `run_id` after the trigger POST).
- If the file is missing, **fail loudly**. Do NOT scan, do NOT fall back to a flat
  `goals/<slug>/output.json`.

### Test cast-server stdout capture (FR-002)

- `test_server` fixture writes the subprocess's combined stdout/stderr to
  `/tmp/diecast-uitest-server-<pid>.log`.
- A `pytest_runtest_makereport` hook (or equivalent) detects test failure and prints
  the last 200 lines of that log to pytest output, prefixed with
  `[test-cast-server stdout]:`.
- The log file is removed on session-clean exit.

### Runner page-load contract (FR-003)

- All `page.goto(...)` calls use `wait_until="domcontentloaded"`.
- All `page.wait_for_load_state(...)` calls switch off `"networkidle"` (use
  `"domcontentloaded"` or rely on per-element `expect(...).to_be_visible(timeout=…)`).
- Per-screen overrides allowed only if a specific screen genuinely requires it (none
  expected today).

## Pre-Existing Decisions (from plan-review pass 2026-05-01)

- **#1 No scan fallback in `_read_orchestrator_output`.** Deterministic path only;
  missing file = real bug, fail loudly.
- **#2 Layer C bugs filed as Diecast tasks** under the existing `comprehensive-ui-test`
  goal — one task per bug, status='suggested' or 'todo'. NOT a separate plan doc;
  NOT an umbrella plan.
- **Layered execution is mandatory.** Do not start sp4 until sp1+sp2+sp3 are merged.
  Do not start sp5 until sp4 is merged AND the human has classified each remaining
  red entry as Layer C (vs. still-mistaken assertion).
- **No new abstractions.** Each fix is a targeted edit to the file named in its FR.
  No new helper modules unless duplication is already 3+ identical lines across files.
- **No assertion deletion to make tests green.** Patch wrong assertions; only delete
  if the feature being tested doesn't exist.
- **No retries to mask flake.** No `pytest-rerunfailures` additions.

## Sub-Phase Dependency Summary

| Sub-phase                                  | Type      | Depends On       | Blocks   | Can Parallel With |
|--------------------------------------------|-----------|------------------|----------|-------------------|
| sp1_layer_a1_orchestrator_output_path      | Sub-phase | --               | sp4, sp5 | sp2, sp3          |
| sp2_layer_a2_server_stdout_capture         | Sub-phase | --               | sp4, sp5 | sp1, sp3          |
| sp3_layer_a3_runner_domcontentloaded       | Sub-phase | --               | sp4, sp5 | sp1, sp2          |
| sp4_layer_b_assertion_fixes                | Sub-phase | sp1, sp2, sp3    | sp5      | --                |
| sp5_layer_c_bug_enumeration                | Sub-phase | sp4 (+ human gate) | --     | --                |

One human gate sits between sp4 and sp5 (Layer C classification). No other gates.
