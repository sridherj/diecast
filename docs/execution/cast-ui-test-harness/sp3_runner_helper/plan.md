# Sub-phase 3: Shared Playwright runner.py

> **Pre-requisite:** Read `docs/execution/cast-ui-test-harness/_shared_context.md` before starting.

## Objective

Build the self-contained Playwright-Python helper script that every per-screen test agent
shells out to. The runner takes a `--screen=<name>` arg and dispatches to a per-screen
`_assert_<screen>(page, ctx)` function, captures console messages with severity-only
filtering, writes a structured `output.json`, and exits cleanly even on SIGINT.

This is the single largest deliverable in the plan and the place where flake either lives
or dies. Every assertion uses Playwright's auto-wait with a 30s per-assertion timeout.

This sub-phase delivers FR-005 (and is the substrate for FR-010 flake handling). Adding
a new screen later costs ≤30 LOC inside this file plus one orchestrator child entry —
which is what SC-005 measures.

## Dependencies
- **Requires completed:** None (independent of sp1, sp2). The runner does not import from the
  cast_server package — it speaks HTTP only.
- **Assumed codebase state:** The cast-server templates and routes referenced by the plan's
  US4 scenarios already exist. Verify selectors against the live HTML before locking in
  asserts (use the dev server on `:8000` to spot-check).

## Scope

**In scope:**
- Create `cast-server/tests/ui/runner.py`, a single self-contained script with:
  - argparse CLI: `--screen`, `--base-url`, `--goal-slug`, `--output`.
  - One `_assert_<screen>(page, ctx)` function per screen: `dashboard`, `agents`, `runs`,
    `scratchpad`, `goal_detail`, `focus`, `about`. (Module-internal naming uses underscore;
    external `--screen` arg accepts both `goal-detail` and `goal_detail` for ergonomics.)
  - Console-message capture with severity-only filter: `error`/`pageerror` → fail;
    `warning`/`info`/`debug` → record to `console_warnings[]`.
  - Per-assertion 30s timeout; Playwright auto-wait everywhere else.
  - On any failure, screenshot to `<goal-dir>/screenshots/<screen>-<timestamp>.png`.
  - Browser launch with `--user-data-dir=/tmp/diecast-uitest-<pid>-<screen>` so the
    teardown sweep in sp2 can match the substring `diecast-uitest`.
  - `try/finally` browser close so SIGINT-killed runs don't leak Chromium.
- Implement the assertions from US4 of the plan, with selector strategies grounded in the
  existing templates (verify selectors live, don't assume).

**Out of scope (do NOT do these):**
- Do NOT define test agent files here (that's sp4a/sp4b).
- Do NOT define the orchestrator behavior — it lives in agent instructions, not in runner.py.
- Do NOT make this a `python -m` module (FR-005 explicitly requires direct script-path).
- Do NOT add visual regression / screenshot diffing — out of scope for the whole plan.
- Do NOT call into cast_server internals — the runner talks HTTP only.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/ui/runner.py` | Create | Does not exist. ~400-600 LOC self-contained. |

## Detailed Steps

### Step 3.1: Establish the runner skeleton

```python
"""Diecast UI test runner. Invoked by per-screen test agents.

Usage:
    python cast-server/tests/ui/runner.py \\
        --screen=<name> \\
        --base-url=http://127.0.0.1:8006 \\
        --goal-slug=<slug> \\
        --output=<absolute-path-to-output.json>

Exit code: 0 on green, 1 on any failed assertion. The output.json is the
source of truth either way.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from playwright.sync_api import (
    Browser, BrowserContext, ConsoleMessage, Page, Playwright,
    TimeoutError as PlaywrightTimeoutError, sync_playwright,
)

ASSERTION_TIMEOUT_MS = 30_000
USER_DATA_DIR_PREFIX = "/tmp/diecast-uitest"  # MUST match sp2's pkill sweep substring


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_screen(s: str) -> str:
    return s.replace("-", "_")
```

### Step 3.2: Result structure and console capture

```python
class Result:
    def __init__(self, screen: str) -> None:
        self.screen = screen
        self.assertions_passed: list[str] = []
        self.assertions_failed: list[dict[str, str]] = []
        self.console_errors: list[str] = []
        self.console_warnings: list[str] = []
        self.screenshots: list[str] = []
        self.started_at = _now_iso()
        self.finished_at: str | None = None

    @property
    def status(self) -> str:
        if self.assertions_failed or self.console_errors:
            return "failed"
        return "completed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "screen": self.screen,
            "status": self.status,
            "assertions_passed": self.assertions_passed,
            "assertions_failed": self.assertions_failed,
            "console_errors": self.console_errors,
            "console_warnings": self.console_warnings,
            "screenshots": self.screenshots,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


def _attach_console_capture(page: Page, result: Result) -> None:
    def on_console(msg: ConsoleMessage) -> None:
        text = f"{msg.type}: {msg.text}"
        if msg.type in ("error",):
            result.console_errors.append(text)
        else:
            result.console_warnings.append(text)

    def on_pageerror(exc: Exception) -> None:
        result.console_errors.append(f"pageerror: {exc}")

    page.on("console", on_console)
    page.on("pageerror", on_pageerror)
```

### Step 3.3: Assertion helper with screenshot-on-fail

```python
@contextmanager
def assertion(result: Result, name: str, page: Page, screenshots_dir: Path):
    try:
        yield
    except (AssertionError, PlaywrightTimeoutError) as e:
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        path = screenshots_dir / f"{result.screen}-{int(time.time()*1000)}.png"
        try:
            page.screenshot(path=str(path), full_page=True)
            result.screenshots.append(str(path))
        except Exception:  # noqa: BLE001
            pass
        result.assertions_failed.append({"name": name, "error": str(e)})
    else:
        result.assertions_passed.append(name)
```

### Step 3.4: Per-screen assertion functions

Implement one `_assert_<screen>(page, ctx)` function per screen. `ctx` is a small dataclass
or dict carrying `base_url`, `goal_slug`, `screenshots_dir`, and the `result` object.

The plan's US4 scenarios are the spec. Highlights below — implement all of them.

**`_assert_dashboard`** (US4 S1, S2, S2b):
- `page.goto(f"{ctx['base_url']}/")` — assert HTTP 200, no console errors.
- Click each of three tabs (`active`, `inactive`, `completed`) — assert HTMX swap completes.
- Submit "Create Goal" form with slug `ctx['goal_slug']` — assert it appears in active list within 5s.
- Create separate `ui-test-delete-<ts>`, click delete, assert it's gone within 5s.
- **DO NOT** delete `ctx['goal_slug']` — the goal_detail child needs it intact.

**`_assert_agents`** (US4 S6):
- Load `/agents`. Assert `/api/agents` returns ≥1 entry.
- Assert at least one card with name matching `cast-ui-test-*` is visible (proves merge worked).
- Click a filter button — assert toggle.
- Click a card details expander — assert details visible.

**`_assert_runs`** (US4 S7, S7b):
- Load `/runs`. Click each of 4 status tabs — assert filter.
- Click a run row — assert detail.
- Trigger `cast-ui-test-noop --sleep=20` (POST to `/api/agents/cast-ui-test-noop/trigger`),
  click cancel button (`run_row.html:219`), assert `cancelled` status within 5s.

**`_assert_scratchpad`** (US4 S8):
- Submit new entry, assert it renders. Delete entry, assert removal.

**`_assert_goal_detail`** (US4 S3, S4, S5, S5b, S5c, S5d, S5e):
- Open `/goals/<slug>` for `ctx['goal_slug']`.
- Assert 5 tabs (overview + 4 phase tabs). Click each — assert HTMX render.
- If status is `idea`, click accept button (`goal_card.html:42`, `hx-vals={"status":"accepted"}`),
  assert transition + phase controls appear within 5s.
- If status is `accepted`, click phase-advance button — assert transition. Else mark assertion as `skipped`.
- Toggle focus, then unfocus — assert state both ways within 5s.
- In a phase tab: submit "create task" form with title `test-task-<ts>` — assert render.
  Cycle status (todo → in_progress → done) — assert each transition. Delete task — assert removal.
  If suggested tasks present: accept exactly one, assert migration `suggested → todo`.
- Open artifact editor (GET `/api/artifacts/edit`), edit content, save (PUT `/api/artifacts/save`).
  Assert clean re-render with new content within 5s.
- Trigger `cast-ui-test-noop` (no sleep) from goal page — assert run row appears on `/runs` within 5s.

**`_assert_focus`** (US4 S9):
- Load `/focus`. Assert no JS errors. If a goal is focused, assert details render; else
  assert empty-state.

**`_assert_about`** (US4 S10):
- Load `/about`. Assert static content + no JS console errors.

For each `page.click(...)` / `page.fill(...)` / `page.locator(...).wait_for(...)` operation,
pass an explicit `timeout=ASSERTION_TIMEOUT_MS` to keep the per-assertion ceiling at 30s.

### Step 3.5: Main entry point

```python
SCREEN_DISPATCH: dict[str, Callable[[Page, dict], None]] = {
    "dashboard": _assert_dashboard,
    "agents": _assert_agents,
    "runs": _assert_runs,
    "scratchpad": _assert_scratchpad,
    "goal_detail": _assert_goal_detail,
    "focus": _assert_focus,
    "about": _assert_about,
}


def _run_screen(screen: str, base_url: str, goal_slug: str, output_path: Path) -> int:
    result = Result(screen=screen)
    screenshots_dir = output_path.parent / "screenshots"
    user_data_dir = Path(f"{USER_DATA_DIR_PREFIX}-{os.getpid()}-{screen}")

    pw: Playwright | None = None
    browser: Browser | None = None
    try:
        pw = sync_playwright().start()
        # Persistent context with our user-data-dir so the sweep pattern matches.
        context: BrowserContext = pw.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=True,
            args=["--no-sandbox"],
        )
        browser = context.browser  # type: ignore[assignment]
        page = context.new_page()
        page.set_default_timeout(ASSERTION_TIMEOUT_MS)
        _attach_console_capture(page, result)

        ctx = {
            "base_url": base_url,
            "goal_slug": goal_slug,
            "screenshots_dir": screenshots_dir,
            "result": result,
            "page": page,
        }
        SCREEN_DISPATCH[screen](page, ctx)
    except Exception as e:  # noqa: BLE001
        result.assertions_failed.append({"name": "runner_internal", "error": repr(e)})
    finally:
        result.finished_at = _now_iso()
        try:
            if browser is not None:
                browser.close()
        except Exception:  # noqa: BLE001
            pass
        try:
            if pw is not None:
                pw.stop()
        except Exception:  # noqa: BLE001
            pass
        # Clean up the per-screen user-data-dir.
        try:
            import shutil
            shutil.rmtree(user_data_dir, ignore_errors=True)
        except Exception:  # noqa: BLE001
            pass
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result.to_dict(), indent=2))
    return 0 if result.status == "completed" else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--screen", required=True)
    p.add_argument("--base-url", default="http://127.0.0.1:8006")
    p.add_argument("--goal-slug", required=True)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args(argv)

    screen = _norm_screen(args.screen)
    if screen not in SCREEN_DISPATCH:
        print(f"unknown screen: {args.screen}", file=sys.stderr)
        return 2
    return _run_screen(screen, args.base_url, args.goal_slug, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
```

### Step 3.6: Verify selectors against live UI

Before merging, run the dev server (`bin/cast-server` on `:8000`) and use the **/browse**
or **/gstack** skill (if convenient) to inspect the actual HTML for each screen. Confirm:

- Tab buttons in dashboard are addressable by an HTMX-aware locator.
- `goal_card.html:42` accept button has stable identifying attributes (e.g. `hx-vals='{"status":"accepted"}'`).
- `run_row.html:219` cancel button likewise.
- The "Create Goal" form has stable input names.
- Artifact editor open/save endpoints respond as expected.

-> Delegate selector verification: `/browse` — open `http://127.0.0.1:8000/`, inspect each
   screen, capture the stable selectors that the runner will use.
-> Follow-up: cross-reference each captured selector against `runner.py` and adjust if the
   live HTML uses different IDs/classes than the plan's references suggest.

### Step 3.7: Smoke-run a single screen end-to-end

Once sp4a's `noop` agent and a minimal stub for the orchestrator exist, you can drive
runner.py against the dev server (NOT during sp3 — defer to sp5 integration):

```bash
# (sp5 will own this — listed here for context only.)
DIECAST_ROOT=$(pwd) python cast-server/tests/ui/runner.py \
    --screen=about --base-url=http://127.0.0.1:8000 \
    --goal-slug=ignored --output=/tmp/about-output.json
cat /tmp/about-output.json
```

For sp3 itself, the runner is verifiable by import + argparse smoke + dispatch lookup.

## Verification

### Automated Tests (permanent)

This sub-phase is mostly UI-driving code; permanent unit tests are a poor fit (each
`_assert_*` requires a live UI). Instead:

- A small `test_runner_dispatch.py` next to `runner.py` that imports `runner` and asserts:
  - `SCREEN_DISPATCH` keys equal the expected 7 screen names.
  - `_norm_screen("goal-detail") == "goal_detail"`.
  - `argparse` rejects an unknown `--screen` with exit 2.

```python
# cast-server/tests/ui/test_runner_dispatch.py
import sys
import pytest

from cast_server_tests_ui import runner  # adjust import path; see Execution Notes
# ^ if direct import is awkward (not a package), use importlib.util.spec_from_file_location
#   to load runner.py from its absolute path.


def test_dispatch_keys_are_seven_screens():
    expected = {"dashboard", "agents", "runs", "scratchpad", "goal_detail", "focus", "about"}
    assert set(runner.SCREEN_DISPATCH.keys()) == expected


def test_norm_screen_dash_to_underscore():
    assert runner._norm_screen("goal-detail") == "goal_detail"
    assert runner._norm_screen("dashboard") == "dashboard"


def test_main_rejects_unknown_screen():
    rc = runner.main(["--screen=nope", "--goal-slug=x", "--output=/tmp/x.json"])
    assert rc == 2
```

### Validation Scripts (temporary)

```bash
# Import smoke.
python -c "import importlib.util, pathlib; \
spec = importlib.util.spec_from_file_location('rn', 'cast-server/tests/ui/runner.py'); \
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); \
print('screens:', sorted(m.SCREEN_DISPATCH.keys()))"

# CLI smoke.
python cast-server/tests/ui/runner.py --help
```

### Manual Checks

- Confirm runner.py is self-contained: no `from cast_server...` imports.
- Confirm the user-data-dir prefix matches the sweep substring in sp2's `_teardown` fixture (`diecast-uitest`).
- Confirm `try/finally` browser close fires even on KeyboardInterrupt (manually run a
  screen, hit Ctrl-C mid-run, verify no `chromium` process remains: `pgrep -f diecast-uitest`).

### Success Criteria

- [ ] `cast-server/tests/ui/runner.py` exists and is self-contained (no cast_server imports).
- [ ] `python runner.py --help` prints the expected CLI.
- [ ] `SCREEN_DISPATCH` contains exactly 7 entries: `dashboard`, `agents`, `runs`, `scratchpad`, `goal_detail`, `focus`, `about`.
- [ ] `--screen=goal-detail` is accepted and dispatches to `_assert_goal_detail` (dash↔underscore).
- [ ] Console capture: `error`/`pageerror` → `console_errors`; `warning`/`info`/`debug` → `console_warnings`.
- [ ] On any failed assertion, a screenshot is written under `<output_dir>/screenshots/`.
- [ ] User-data-dir path includes the substring `diecast-uitest` (matches sp2's sweep).
- [ ] `try/finally` ensures browser close on KeyboardInterrupt.
- [ ] All assertions in the file use a 30s timeout (`ASSERTION_TIMEOUT_MS`).
- [ ] `test_runner_dispatch.py` passes.

## Execution Notes

- **Selector verification is the #1 risk in this sub-phase.** The plan references concrete
  template lines (`goal_card.html:42`, `run_row.html:219`) — confirm these are stable
  identifiers, not just line numbers. Prefer attribute-based locators
  (`hx-vals`, `data-action`, `name=`) over text-based.
- **HTMX swap waits:** after clicking an HTMX-bound button, wait on the swapped element to
  appear (`page.locator(...).wait_for(state="visible", timeout=ASSERTION_TIMEOUT_MS)`),
  not on a fixed sleep.
- **`goal_detail` skip case:** Scenario 5 says skip phase-advance if status isn't `accepted`.
  Use the `Result.assertions_passed` ladder with a `_skipped` suffix in the name to surface
  the skip without failing.
- **`_assert_runs` cancel flow:** triggering `cast-ui-test-noop --sleep=20` from the runs
  child requires POST to `/api/agents/cast-ui-test-noop/trigger` with the right JSON body.
  Use the same shape the orchestrator will use (sp4a establishes the contract).
- **`page.set_default_timeout`** sets the navigation/locator default; explicit `timeout=`
  args on individual operations still override per-call.
- **`launch_persistent_context` vs `launch + new_context`:** persistent context lets us pin
  the `--user-data-dir` so the sweep pattern works. Don't switch to `launch_browser` without
  also updating sp2's sweep.
- **Import path for `test_runner_dispatch.py`:** if a sibling test file can't `import runner`
  directly because `tests/ui/` isn't on `sys.path`, use `importlib.util.spec_from_file_location`
  to load it from absolute path. Don't add path manipulation hacks to runner.py itself.
- **No skill delegation here except Step 3.6** (selector verification via `/browse`) — the
  rest is hand-coded Python.
- **Spec-linked files:** None of the modified files are covered by a spec in `docs/specs/`.
