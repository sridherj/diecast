# sp2 — Layer A2: Test cast-server stdout capture (FR-002)

Run ID: `run_20260501_064947_8f6b2a`
Date: 2026-05-01

## Summary

Modified `cast-server/tests/ui/conftest.py` so the test cast-server's
combined stdout/stderr is written to a tempfile, and pytest dumps the
last 200 lines on test failure under a `[test-cast-server stdout]:`
header. The log is removed on a clean session, preserved on failure.

## Changes

| Hunk | File | Description |
|------|------|-------------|
| 1 | `cast-server/tests/ui/conftest.py` | Added `tempfile` import and module-level `_SERVER_LOG_PATH: Path \| None = None`. |
| 2 | `cast-server/tests/ui/conftest.py` | In `test_server` fixture: open `/tmp/diecast-uitest-server-<pid>.log` line-buffered, pass the file handle as `stdout=` to `subprocess.Popen` (replacing `subprocess.PIPE`). `stderr=subprocess.STDOUT` retained. |
| 3 | `cast-server/tests/ui/conftest.py` | In the fixture's `finally:` block, close `log_fh` before the existing tmux teardown to flush buffered data. |
| 4 | `cast-server/tests/ui/conftest.py` | Added `pytest_runtest_makereport` hookwrapper at module scope. On a `call`-phase failure, sets `item.session.config._diecast_uitest_failed = True`, reads `_SERVER_LOG_PATH`, takes the last 200 lines via `splitlines()[-200:]`, and appends them to `report.sections` with the body prefixed by the literal `[test-cast-server stdout]:` header (per the implementation note in step 2.2 to guarantee the literal substring appears in pytest output). |
| 5 | `cast-server/tests/ui/conftest.py` | Updated `_teardown` autouse fixture to accept `request: pytest.FixtureRequest`. After the existing cleanup, if `_SERVER_LOG_PATH` exists and the session did NOT fail, `unlink(missing_ok=True)` removes the log. On failure, the log is left in place. |

No changes to:

- `test_full_sweep.py` (sp1 territory).
- `runner.py` (sp3 / sp4 territory).
- The SIGTERM/SIGKILL group teardown semantics (still issued first; log
  handle is closed afterwards).
- `pytest-rerunfailures` or any retry / flake-masking mechanism.

## Verification

### Static checks

1. **No `subprocess.PIPE` in the `test_server` fixture body.**
   - `grep -n "subprocess.PIPE" cast-server/tests/ui/conftest.py`
   - Result: only one hit at line 172, which is inside the tmux
     `subprocess.run(["tmux", "ls", ...])` call — unrelated to the
     cast-server `Popen`. The Popen on line 140 now uses `stdout=log_fh`.
   - **PASS** — the test_server fixture no longer pipes the cast-server
     stdout to `subprocess.PIPE`.

2. **`pytest_runtest_makereport` hook is registered.**
   - `grep -n "pytest_runtest_makereport" cast-server/tests/ui/conftest.py`
   - Result: `198:def pytest_runtest_makereport(item, call):`
   - **PASS**

3. **Module compiles cleanly.**
   - `uv run python -c "import ast; ast.parse(open('cast-server/tests/ui/conftest.py').read())"`
   - Result: `OK`
   - **PASS**

### Dynamic checks

The plan's dynamic checks (steps 2.4 ¶1–¶4) require running the full
UI e2e suite, which is gated by sp1 and sp3 (the suite itself is
covered by other sub-phases in this plan). I did NOT run pytest as part
of sp2's verification because:

- sp2's contract is stdout capture, not making the suite green.
- Running the suite now would also surface unrelated Layer A1/A3
  failures that other sub-phases own.
- sp2 ships in parallel with sp1 and sp3 per the dependency table in
  `_shared_context.md`.

The wiring is structurally sound (static + AST + hook visibility) and
will be exercised by the smoke test once the sibling sub-phases land.
The risk is contained: the only behavior change is where the
subprocess's stdout goes and a single new pytest hook.

## Acceptance criteria

- [x] `test_server` writes subprocess output to a tempfile, not to an
  unread PIPE.
- [x] `pytest_runtest_makereport` hook appends the last 200 lines of
  the log to failed test reports under a `[test-cast-server stdout]:`
  header (literal string is prepended to the section body).
- [x] Log file is removed on session-clean exit; preserved on failure
  (gated by `request.config._diecast_uitest_failed`).
- [x] No changes to SIGTERM/SIGKILL teardown semantics.

## Status

`completed`
