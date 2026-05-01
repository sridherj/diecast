# Cast UI Test Children Completion

## Context

Discovered while running the post-sp4 dynamic verification for goal
`cast-ui-harness-layered-fixes` on 2026-05-01.

After the Layer A regressions in that goal were fixed (alembic
`disable_existing_loggers=False`, `PYTHONUNBUFFERED=1` in conftest), the test
harness `cast-server/tests/ui/test_full_sweep.py::test_ui_e2e` is now able to:

- Boot the test cast-server cleanly on :8006
- Trigger `cast-ui-test-orchestrator` (200 OK, run_id returned)
- Watch the orchestrator dispatch all 7 per-screen children (200 OK each):
  - `cast-ui-test-dashboard`
  - `cast-ui-test-agents`
  - `cast-ui-test-runs`
  - `cast-ui-test-scratchpad`
  - `cast-ui-test-goal-detail`
  - `cast-ui-test-focus`
  - `cast-ui-test-about`
- Observe each child making real HTTP requests to the test server
  (`GET /dashboard`, `/runs`, `/focus`, etc.)
- Poll `/api/agents/jobs/{orchestrator_run_id}` indefinitely with 200 OK responses

…but the test still fails because **no child writes its `output.json`** within
the test's 1200-second `TOTAL_TIMEOUT_S`. After 8+ minutes:

- Orchestrator status remains non-terminal
- Child delegation files (`.delegation-run_*.json`) are present in goal_dir
- Child `.agent-run_*.output.json` files are absent
- Child tmux sessions are still alive (until pytest teardown SIGKILLs them)

## What needs investigating

1. Why the per-screen children don't complete. Capture pane content while
   they're running. Likely one of:
   - Stuck waiting for a Claude permission prompt that the orchestrator's
     "send Enter every 15s" trick doesn't satisfy.
   - Playwright browser hung / awaiting a selector that doesn't resolve.
   - Child agent prompt asks for input that nobody answers.
   - Resource contention (7 Chromium processes + 7 Claude sessions on one host).
2. Whether the children should actually be running 7-wide in parallel, or
   sequentially. The orchestrator currently fan-outs all 7 simultaneously.
3. What signal a child should write before navigating the browser, so a stuck
   child can be distinguished from a slow child.

## Reference

- Plan that surfaced this: `docs/plan/2026-05-01-cast-ui-harness-layered-fixes.collab.md`
- Execution dir: `docs/execution/cast-ui-harness-layered-fixes/`
- sp4 verification log: `docs/execution/cast-ui-harness-layered-fixes/sp4_layer_b_assertion_fixes/verification_log.md`
- Layer A fixes (already shipped):
  - `cast-server/alembic/env.py:24-25` — `disable_existing_loggers=False`
  - `cast-server/tests/ui/conftest.py:135-138` — `PYTHONUNBUFFERED=1`

## Repro

```bash
uv run pytest cast-server/tests/ui/test_full_sweep.py -v --tb=short
# Watch /tmp/diecast-uitest-server-<pid>.log for the per-child trigger 200 OKs.
# Observe `tmux ls | grep agent-run_` for the live child sessions.
# After 8+ min, the test will time out without any child output.json being written.
```
