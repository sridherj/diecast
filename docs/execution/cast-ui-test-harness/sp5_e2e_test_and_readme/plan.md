# Sub-phase 5: End-to-end test + README

> **Pre-requisite:** Read `docs/execution/cast-ui-test-harness/_shared_context.md` before starting.

## Objective

Land the single pytest entry point (`test_full_sweep.py::test_ui_e2e`) that ties all prior
sub-phases together, plus the `README.md` that documents how to run the suite, what it does,
and how to add a new screen in <50 LOC (SC-005).

This sub-phase makes `pytest cast-server/tests/ui/` runnable end-to-end. Everything before
this is scaffolding; this is the integration test.

## Dependencies
- **Requires completed:** sp1 (registry merge), sp2 (fixtures), sp3 (runner.py), sp4a
  (orchestrator + noop), sp4b (7 screen agents). All five must land before sp5 runs.
- **Assumed codebase state:** the test server can be booted by sp2's fixture, the runner
  CLI works, all 9 test agents are loadable.

## Scope

**In scope:**
- `cast-server/tests/ui/test_full_sweep.py::test_ui_e2e` — the single pytest entry point.
  It depends on sp2's `test_server`, `test_goal_slug` fixtures, dispatches the orchestrator
  via HTTP, polls `/api/agents/jobs/<run_id>` every 5s up to 240s for terminal status,
  parses the orchestrator's `output.json`, asserts `status: completed`, and surfaces
  per-child failures as readable assertion messages.
- `cast-server/tests/ui/README.md` — documents:
  - How to run (`pip install -e ".[test]"`, `playwright install chromium`, `pytest cast-server/tests/ui/`).
  - What it does (architecture diagram pointing at orchestrator + 7 children + runner.py + harness).
  - Where the agent definitions live.
  - How to add a new screen (≤30 LOC: one new agent dir + one `_assert_<screen>` function +
    one entry in orchestrator's child list + one entry in `SCREEN_DISPATCH`).
  - Troubleshooting: port collision, orphan Chromium, browser-binary missing.

**Out of scope (do NOT do these):**
- Do NOT modify runner.py, agent definitions, or fixtures (sp1-sp4 own those).
- Do NOT add a wiring layer for CI — out of scope per plan's "Out of Scope" section.
- Do NOT add screenshot-diff baselines.
- Do NOT add visual regression checks.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/ui/test_full_sweep.py` | Create | Does not exist. |
| `cast-server/tests/ui/README.md` | Create | Does not exist. |

## Detailed Steps

### Step 5.1: Read sp2's conftest fixtures

Open `cast-server/tests/ui/conftest.py` (sp2's deliverable) to confirm exact fixture names
and signatures:
- `test_server` — yields the base URL (e.g., `http://127.0.0.1:8006`).
- `test_goal_slug` — yields the unique slug for this run.

If names diverged from the plan, follow the actual fixture names.

### Step 5.2: Author `test_full_sweep.py`

```python
"""Single pytest entry for the Diecast UI e2e harness.

Triggers the orchestrator, polls to terminal, asserts every child completed cleanly.
Per-child failures are surfaced via the orchestrator's structured output.json.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
import urllib.request
import urllib.error

ORCHESTRATOR_TRIGGER_PATH = "/api/agents/cast-ui-test-orchestrator/trigger"
JOBS_POLL_PATH_TEMPLATE = "/api/agents/jobs/{run_id}"
TOTAL_TIMEOUT_S = 240
POLL_INTERVAL_S = 5
TERMINAL_STATUSES = {"completed", "failed", "cancelled", "partial"}


def _http_post(url: str, body: dict) -> dict:
    req = urllib.request.Request(
        url, method="POST",
        headers={"Content-Type": "application/json"},
        data=json.dumps(body).encode(),
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def _http_get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read())


def _poll_to_terminal(base_url: str, run_id: str, total_timeout_s: int) -> dict:
    deadline = time.monotonic() + total_timeout_s
    last_status = None
    while time.monotonic() < deadline:
        try:
            job = _http_get(f"{base_url}{JOBS_POLL_PATH_TEMPLATE.format(run_id=run_id)}")
        except urllib.error.HTTPError as e:
            pytest.fail(f"polling failed for run_id={run_id}: HTTP {e.code}")
        last_status = job.get("status")
        if last_status in TERMINAL_STATUSES:
            return job
        time.sleep(POLL_INTERVAL_S)
    pytest.fail(
        f"orchestrator did not reach terminal status within {total_timeout_s}s "
        f"(last status: {last_status!r})"
    )


def _read_orchestrator_output(job: dict, repo_root: Path) -> dict:
    """Locate output.json from the job record. The job record should expose the goal dir
    or output path; if not, fall back to scanning goals/ui-test-* for a recent file.
    """
    for key in ("output_path", "output_json_path"):
        if job.get(key):
            return json.loads(Path(job[key]).read_text())
    goal_slug = job.get("goal_slug") or job.get("slug")
    if goal_slug:
        candidate = repo_root / "goals" / goal_slug / "output.json"
        if candidate.exists():
            return json.loads(candidate.read_text())
    pytest.fail(f"could not locate orchestrator output.json from job: {job}")


def _format_child_failures(orch_output: dict) -> str:
    lines: list[str] = []
    for name, child in (orch_output.get("children") or {}).items():
        status = child.get("status")
        if status == "completed":
            continue
        out_path = child.get("output_path")
        detail: dict | None = None
        if out_path and Path(out_path).exists():
            try:
                detail = json.loads(Path(out_path).read_text())
            except Exception:  # noqa: BLE001
                detail = None
        lines.append(f"  {name}: status={status} output={out_path}")
        if detail:
            for f in detail.get("assertions_failed", []) or []:
                lines.append(f"    - assertion {f.get('name')!r}: {f.get('error')}")
            for ce in detail.get("console_errors", []) or []:
                lines.append(f"    - console_error: {ce}")
    return "\n".join(lines)


def test_ui_e2e(test_server: str, test_goal_slug: str) -> None:
    """End-to-end UI sweep via the cast-ui-test-orchestrator agent."""
    repo_root = Path(__file__).resolve().parents[3]

    trigger_body = {
        "goal_slug": test_goal_slug,
        "delegation_context": {
            "goal_slug": test_goal_slug,
            "base_url": test_server,
        },
    }
    triggered = _http_post(f"{test_server}{ORCHESTRATOR_TRIGGER_PATH}", trigger_body)
    run_id = triggered.get("run_id") or triggered.get("id")
    assert run_id, f"trigger response missing run_id: {triggered}"

    job = _poll_to_terminal(test_server, run_id, TOTAL_TIMEOUT_S)

    orch_output = _read_orchestrator_output(job, repo_root)
    status = orch_output.get("status")

    if status != "completed":
        failures = _format_child_failures(orch_output)
        pytest.fail(
            f"UI e2e sweep status={status!r}\n"
            f"summary={orch_output.get('summary')}\n"
            f"failures:\n{failures or '  (no per-child detail captured)'}"
        )

    summary = orch_output.get("summary") or {}
    assert summary.get("failed", 0) == 0, f"summary indicates failures: {summary}"
    assert summary.get("total", 0) == 7, f"expected 7 children, got {summary.get('total')}"
```

### Step 5.3: Write the README

Create `cast-server/tests/ui/README.md`:

```markdown
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
```

### Step 5.4: Run the suite end-to-end

```bash
cd /home/sridherj/workspace/diecast
pip install -e "cast-server[test]"
playwright install chromium

# First run — should be green, <120s.
time pytest cast-server/tests/ui/ -v

# Run thrice in a row — assert no leakage, all green.
for i in 1 2 3; do pytest cast-server/tests/ui/ -q; done

# Confirm cleanliness.
ls /tmp/diecast-uitest-* 2>/dev/null && echo "LEAK: temp dbs"
ls goals/ui-test-* 2>/dev/null && echo "LEAK: goal dirs"
lsof -iTCP:8006 -sTCP:LISTEN 2>/dev/null && echo "LEAK: port 8006"
pgrep -f diecast-uitest && echo "LEAK: orphan chromium"
```

### Step 5.5: Manual fault-injection smoke (per Decision #10)

SC-004 was dropped, but a one-off manual fault-injection still gives confidence the suite
catches regressions. After landing sp5:
1. Edit `cast_server/routes/api_goals.py` to make `POST /api/goals` return 422.
2. Run the suite — confirm `cast-ui-test-dashboard` fails specifically, with the new-goal-not-appearing assertion message.
3. Revert.

## Verification

### Automated Tests (permanent)

- `cast-server/tests/ui/test_full_sweep.py::test_ui_e2e` — the canonical e2e gate.
- `cast-server/tests/ui/test_registry_visibility.py` (from sp1) — fast meta-test, runs alongside.

### Validation Scripts (temporary)

```bash
# SC-001: <120s wall-clock.
time pytest cast-server/tests/ui/ -q

# SC-002: 3 consecutive runs leave no trace.
for i in 1 2 3; do pytest cast-server/tests/ui/ -q || exit 1; done
test -z "$(ls /tmp/diecast-uitest-* 2>/dev/null)" && echo "SC-002 temp dbs OK"
test -z "$(ls goals/ui-test-* 2>/dev/null)" && echo "SC-002 goal dirs OK"
test -z "$(lsof -iTCP:8006 -sTCP:LISTEN 2>/dev/null)" && echo "SC-002 port OK"

# SC-003: meta-test green.
pytest cast-server/tests/ui/test_registry_visibility.py -q
```

### Manual Checks

- README rendering: open `cast-server/tests/ui/README.md` in a markdown previewer, confirm
  the architecture diagram and "Adding a new screen" section read well.
- Inject a regression per Step 5.5, confirm the right child fails with a useful message.

### Success Criteria

- [ ] `pytest cast-server/tests/ui/` exits 0 in <120s on a clean checkout (SC-001).
- [ ] 3 consecutive runs leave no `/tmp/diecast-uitest-*`, no `goals/ui-test-*`,
      and `:8006` is free (SC-002).
- [ ] `test_registry_visibility.py` is green (SC-003).
- [ ] README documents how to run, what it does, and how to add a screen.
- [ ] When a regression is injected, the right child fails with a readable message
      (manual fault-injection check).
- [ ] No mutations to the dev DB or dev server during a run.

## Execution Notes

- **`run_id` field name** in the trigger response and job poll endpoint may not match the
  template here verbatim. Inspect a real trigger response from the cast-server during
  development and adjust `_http_post` / `_poll_to_terminal` keys.
- **`output_path` discovery:** the most robust strategy is for the job-poll endpoint to
  expose the orchestrator's output.json path directly. If it doesn't, the fallback is
  `goals/<slug>/output.json` — the implementation handles both.
- **240s outer timeout** is the pytest-side cap. The orchestrator's per-child cap is 90s
  (Decision #12), so 240s is a comfortable upper bound for the parent poll loop.
- **Polling cadence:** 5s. Don't go below 1s (server load) or above 10s (latency to
  terminal status).
- **`@pytest.mark.flaky`:** do NOT mark `test_ui_e2e` flaky by default. Per FR-010,
  retries are opt-in only. If a known-racy assertion surfaces in practice, isolate it to
  a finer-grained test and tag that one — don't blanket-retry the entire e2e.
- **Skill delegation:** -> Use `/qa` to spot-check a manual run end-to-end against the
  test server before declaring sp5 done. Optional but provides confidence.
- **Spec-linked files:** None of the modified files are covered by a spec in `docs/specs/`.
