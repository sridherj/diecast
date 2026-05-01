# Sub-phase 2: Layer A2 — Test cast-server stdout capture (FR-002)

> **Pre-requisite:** Read `docs/execution/cast-ui-harness-layered-fixes/_shared_context.md` before starting.

## Objective

Make the test cast-server's stdout/stderr visible when a UI test fails. Currently the
`test_server` fixture in `cast-server/tests/ui/conftest.py` launches the server with
`stdout=subprocess.PIPE, stderr=subprocess.STDOUT` and **never reads the pipe**. So
when a child agent hits a `POST /api/goals` 500, the traceback is buried inside an
unread pipe and pytest reports nothing about why the server returned 500.

This sub-phase pipes the subprocess's combined stdout to a tempfile, then on test
failure (detected via `pytest_runtest_makereport`) prints the last 200 lines under a
clear header. The log file is removed on session-clean exit.

This sub-phase delivers FR-002 and SC-002 of the layered-fixes plan.

## Dependencies
- **Requires completed:** None. Runs in parallel with sp1 and sp3.
- **Assumed codebase state:** `cast-server/tests/ui/conftest.py` exists with the
  `test_server` fixture at line 107 and the `_teardown` autouse fixture at line 185.

## Scope

**In scope:**
- Modify `test_server` fixture to write subprocess stdout/stderr to a tempfile (e.g.,
  `/tmp/diecast-uitest-server-<pid>.log`).
- Add (or extend) a `pytest_runtest_makereport` hook in `conftest.py` that, on test
  failure, prints the last 200 lines of that log to pytest output prefixed with
  `[test-cast-server stdout]:`.
- Remove the log file on session-clean exit (when no tests failed). On failure, leave
  it in place so the user can inspect more context if 200 lines isn't enough.
- Make the log path discoverable: store it on a module-level (or via a fixture) so
  the makereport hook can find it without a global.

**Out of scope (do NOT do these):**
- Do NOT touch `test_full_sweep.py` (sp1's territory).
- Do NOT touch `runner.py` (sp3 / sp4's territory).
- Do NOT change the existing process-group SIGTERM/SIGKILL teardown logic — only the
  stdout-capture configuration.
- Do NOT add `pytest-rerunfailures` retries or any flake-masking infrastructure.
- Do NOT introduce a new logging library; plain file IO is fine.
- Do NOT make the dump conditional on env vars or pytest options. Always dump on
  failure; that's the whole point.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/ui/conftest.py` | Modify | `test_server` fixture at :107 currently uses `stdout=subprocess.PIPE`. The autouse `_teardown` is at :185. No `pytest_runtest_makereport` hook today. |

## Detailed Steps

### Step 2.1: Open the log file in `test_server`

In the `test_server` fixture body (around the `subprocess.Popen` call at line 132),
open a tempfile and pass it to `Popen`:

```python
log_path = Path(tempfile.gettempdir()) / f"diecast-uitest-server-{os.getpid()}.log"
log_fh = log_path.open("w", buffering=1)  # line-buffered
proc = subprocess.Popen(
    [str(cast_server_bin)],
    env=env,
    cwd=str(REPO_ROOT),
    start_new_session=True,
    stdout=log_fh,
    stderr=subprocess.STDOUT,
)
```

Add `tempfile` to the existing imports (`os`, `signal`, etc. are already imported).

Stash `log_path` somewhere the makereport hook can find it. A module-level
`_SERVER_LOG_PATH: Path | None = None` set inside the fixture is the simplest;
clear it back to None after teardown.

In the `finally` block, after the process is reaped:
- Close `log_fh` (so any buffered data is flushed).
- Leave `log_path` on disk for now — `_teardown` decides whether to remove it.

### Step 2.2: Add `pytest_runtest_makereport` hook

At module scope in `conftest.py`:

```python
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        # Mark a session-level flag so _teardown keeps the log around.
        item.session.config._diecast_uitest_failed = True

        log_path = _SERVER_LOG_PATH
        if log_path is None or not log_path.exists():
            return
        try:
            tail = log_path.read_text().splitlines()[-200:]
        except Exception:  # noqa: BLE001
            return
        report.sections.append(
            ("test-cast-server stdout", "\n".join(tail))
        )
```

Pytest renders sections appended this way under the test-failure output, prefixed
with the section name. The exact `[test-cast-server stdout]:` header text from FR-002
should appear (use `("[test-cast-server stdout]", ...)` as the section tuple key
verbatim — pytest will surround it with its own framing but the literal string remains
visible).

> **Implementation note:** if the section-tuple title alone isn't enough to make the
> exact string `[test-cast-server stdout]:` appear, prepend the header inside the
> body: `"[test-cast-server stdout]:\n" + "\n".join(tail)`. SC-002 requires that the
> header be visible in pytest output.

### Step 2.3: Conditional cleanup in `_teardown`

In the `_teardown` autouse fixture (around line 185), after the existing cleanup work:

```python
log_path = _SERVER_LOG_PATH
if log_path is not None and log_path.exists():
    failed = getattr(request.config, "_diecast_uitest_failed", False)
    if not failed:
        log_path.unlink(missing_ok=True)
    # On failure, leave the log on disk for post-mortem.
```

If `_teardown` doesn't already accept `request: pytest.FixtureRequest`, add it.

### Step 2.4: Smoke-test the wiring

Manually break a test (e.g., assert False) and run
`pytest cast-server/tests/ui/test_full_sweep.py::test_ui_e2e`. Confirm:

1. Pytest output contains the literal substring `[test-cast-server stdout]:`.
2. The 200-line tail follows the header and matches the actual server output.
3. The log file remains on `/tmp/diecast-uitest-server-<pid>.log` after the failed
   run (you should be able to `cat` it).
4. After a passing run (revert your forced-failure), the log file is gone.

## Verification

1. **Static check:** `grep -n "subprocess.PIPE" cast-server/tests/ui/conftest.py`
   shows zero hits in the `test_server` fixture body. (PIPE is no longer used; stdout
   goes to a file handle.)
2. **Static check:** `grep -n "pytest_runtest_makereport" cast-server/tests/ui/conftest.py`
   shows the new hook.
3. **Dynamic check:** with the server killed mid-poll (e.g., via `os.kill(proc.pid, ...)`
   inside the test, or by adding an `assert False` to `test_ui_e2e`), pytest output
   contains the `[test-cast-server stdout]:` header followed by recognizable server
   log lines.
4. **Dynamic check:** on a clean pass (no failure), `/tmp/diecast-uitest-server-*.log`
   is removed.

## Acceptance Criteria

- `test_server` fixture writes subprocess output to a tempfile, not to an unread PIPE.
- `pytest_runtest_makereport` hook appends the last 200 lines of that file to failed
  test reports, with a clear `[test-cast-server stdout]:` header.
- Log file is removed on session-clean exit; preserved on failure.
- No changes to the SIGTERM/SIGKILL teardown semantics.

## Risk / Notes

- **Hook scope.** `pytest_runtest_makereport` runs per-test. The `test_server` fixture
  is session-scoped, so the log file persists across tests. The hook just reads the
  current tail; that's fine.
- **The "200 lines" cap.** Use `splitlines()[-200:]`. Don't try to re-implement
  `tail -n 200` — file is small, in-memory read is fine for a test log.
- **Module-level state.** A `_SERVER_LOG_PATH` module global is acceptable here;
  conftest.py is already the orchestration seam. Don't over-engineer.
- **Pytest's section rendering** sometimes elides the literal string if the section
  title contains brackets. If SC-002's literal-header check fails after your first
  pass, prepend the header inside the body string instead of relying on the section
  title alone (Step 2.2 already notes this).
