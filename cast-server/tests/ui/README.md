# Diecast UI E2E Test Harness

A pytest-driven, agent-orchestrated UI test suite. One command exercises every Diecast
screen and tab in a real Chromium browser.

## How to run

```bash
# One-time setup.
cd cast-server
pip install -e ".[test]"
playwright install chromium

# Run.
pytest cast-server/tests/ui/
```

The suite boots a dedicated cast-server on `127.0.0.1:8006` against a temp SQLite DB.
Your dev server on `:8000` is untouched.

## What it does

```text
pytest test_full_sweep.py
        |
        v  (boots cast-server on :8006 with CAST_TEST_AGENTS_DIR set)
   POST /api/agents/cast-ui-test-orchestrator/trigger
        |
        v
   cast-ui-test-orchestrator
   ├─ Phase 1: cast-ui-test-dashboard   (creates shared goal)
   └─ Phase 2 (parallel):
       ├─ cast-ui-test-agents
       ├─ cast-ui-test-runs
       ├─ cast-ui-test-scratchpad
       ├─ cast-ui-test-goal-detail
       ├─ cast-ui-test-focus
       └─ cast-ui-test-about
              ↓
       runner.py --screen=<name>  (Playwright Chromium per child)
              ↓
       output.json per child  → aggregated into orchestrator output.json
                                                    ↓
                              pytest reads + asserts status="completed"
```

After the run, the harness:
- SIGTERMs the test server's process group (5s grace, SIGKILL escalation).
- Deletes `/tmp/diecast-uitest-<pid>.db` (and -wal/-shm).
- Removes `goals/ui-test-*`.
- Sweeps orphan Chromium processes whose `--user-data-dir` contains `diecast-uitest`.

## Architecture at a glance

| Component | Path | Purpose |
|-----------|------|---------|
| Single pytest entry | `test_full_sweep.py` | Triggers orchestrator, polls, asserts. |
| Fixtures + teardown | `conftest.py` | Boots/kills test server, owns cleanup. |
| Shared runner | `runner.py` | Playwright assertions per screen. |
| Test agents | `agents/cast-ui-test-*/` | Orchestrator + 7 screen children + noop. |
| Registry meta-test | `test_registry_visibility.py` | Asserts test agents invisible in dev. |

Test agents are loaded ONLY when `CAST_TEST_AGENTS_DIR` is set — your dev server never
sees them. See `cast-server/cast_server/services/agent_service.py::get_all_agents`.

## Adding a new screen

Target: ≤30 LOC of new code, three edits.

1. **New agent dir** under `agents/cast-ui-test-<screen>/`:
   - `cast-ui-test-<screen>.md` — copy a sibling, change the screen name.
   - `config.yaml` — copy a sibling, change `name`/`description`/`entrypoint`.

2. **New assertion function** in `runner.py`:

   ```python
   def _assert_<screen>(page: Page, ctx: dict) -> None:
       result = ctx["result"]
       page.goto(f"{ctx['base_url']}/<route>")
       with assertion(result, "<screen>: smoke", page, ctx["screenshots_dir"]):
           page.locator("...").wait_for()
   ```

   Then add `"<screen>": _assert_<screen>` to `SCREEN_DISPATCH`.

3. **Orchestrator child list:** add `cast-ui-test-<screen>` to the fan-out list in
   `agents/cast-ui-test-orchestrator/cast-ui-test-orchestrator.md` Phase 2.

That's it. `pytest cast-server/tests/ui/` will pick it up on the next run.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `RuntimeError: Port 8006 is already bound` | Prior run leaked. | `lsof -iTCP:8006 -sTCP:LISTEN`, kill the offender. |
| `playwright._impl._errors.Error: Executable doesn't exist` | Chromium not installed. | `playwright install chromium`. |
| Orphan Chromium after SIGINT | `finally:` browser close didn't fire. | The teardown sweep (`pkill -f diecast-uitest`) catches these on next run. Verify with `pgrep -f diecast-uitest`. |
| `cast-ui-test-*` agents visible in dev `/agents` | `CAST_TEST_AGENTS_DIR` leaked into your dev shell. | `unset CAST_TEST_AGENTS_DIR` and restart your dev server. |

## Constraints

- Chromium only; Firefox/WebKit deferred.
- Desktop viewport only; no responsive testing.
- No screenshot-diff baselines; screenshots are postmortem only, on failure.
- No CI integration (yet); developer-machine tool.
- No mutation of dev state. The harness writes only to `/tmp` and `cast-server/tests/ui/`'s
  own working tree.
