# Sub-phase 2: Pytest fixtures + dev dependency + teardown

> **Pre-requisite:** Read `docs/execution/cast-ui-test-harness/_shared_context.md` before starting.

## Objective

Set up the pytest infrastructure that boots/tears down the test cast-server process and
provides shared fixtures for the e2e test. This sub-phase delivers FR-002, FR-006, and FR-008
of the plan: a `conftest.py` for `cast-server/tests/ui/`, the Playwright dev dependency in
`pyproject.toml`, and an autouse session-scoped teardown fixture that leaves no trace.

This is the harness scaffold. The actual e2e test (`test_full_sweep.py`) and the runner
(`runner.py`) come later — this sub-phase only ships fixtures and process management.

## Dependencies
- **Requires completed:** None. Can run in parallel with sp1, sp3.
- **Assumed codebase state:** `cast-server/tests/ui/` may exist (sp1 may have created
  `__init__.py`), but `cast-server/tests/ui/conftest.py` does NOT exist yet. If `__init__.py`
  is missing, create it.

## Scope

**In scope:**
- Create `cast-server/tests/ui/conftest.py` with these session-scoped fixtures:
  - `test_db_path` — temp SQLite DB at `/tmp/diecast-uitest-<pid>.db`.
  - `test_goal_slug` — unique per run, format `ui-test-<unix_ts>-<rand4>`.
  - `test_server` — boots `bin/cast-server` subprocess on `127.0.0.1:8006` with
    `CAST_TEST_AGENTS_DIR` and SQLite path env vars set, polls `GET /api/health` until 200
    (max 30s), yields the base URL, and on teardown SIGTERMs the process group with 5s
    grace + SIGKILL escalation.
  - `_teardown` — autouse session-scoped finalizer that removes the temp DB, removes
    `goals/ui-test-*`, and runs the orphan-Chromium sweep with a clearly-scoped
    pattern that cannot match dev browsers.
  - Port-collision guard: if `:8006` is already bound when fixtures start, fail fast with a
    clear error message naming the conflict.
- Add Playwright as a dev dep under `[project.optional-dependencies] test` in
  `cast-server/pyproject.toml`. (Browser binaries fetched manually via
  `playwright install chromium` — documented in README, NOT auto-run by pytest.)

**Out of scope (do NOT do these):**
- Do NOT write `runner.py` here (that's sp3).
- Do NOT write `test_full_sweep.py` here (that's sp5).
- Do NOT create test agent definitions (that's sp4a/sp4b).
- Do NOT add `playwright install chromium` to a setup hook — manual step only.
- Do NOT modify the existing `cast-server/tests/conftest.py` (different file, different scope).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/ui/__init__.py` | Create if missing | May exist from sp1; ensure it exists. |
| `cast-server/tests/ui/conftest.py` | Create | Does not exist. |
| `cast-server/pyproject.toml` | Modify | Has `[project.optional-dependencies]`; verify a `test` extra exists or add it. |

## Detailed Steps

### Step 2.1: Add Playwright to pyproject.toml

Open `cast-server/pyproject.toml`. Find `[project.optional-dependencies]`. If it has a
`test = [...]` list, append `"playwright>=1.45.0"`. If no such extra exists, create it:

```toml
[project.optional-dependencies]
test = [
    "playwright>=1.45.0",
    "pytest-rerunfailures>=14.0",
]
```

(`pytest-rerunfailures` is per FR-010 — opt-in retries for `@pytest.mark.flaky`.)

Document in a comment that browser binaries are NOT installed by `pip install`:

```toml
# NOTE: After `pip install -e ".[test]"`, run `playwright install chromium` once
# to fetch the browser binary. Auto-install is intentionally avoided.
```

### Step 2.2: Ensure the `ui/` package marker

```bash
test -f cast-server/tests/ui/__init__.py || \
    : > cast-server/tests/ui/__init__.py
```

### Step 2.3: Write `conftest.py`

Create `cast-server/tests/ui/conftest.py` with the following structure. Use the canonical
fixture pattern (yield + finalizer) so SIGINT mid-run still runs teardown.

```python
"""Session-scoped fixtures for the Diecast UI e2e harness.

Boots a dedicated cast-server on :8006 against a temp SQLite DB, with
CAST_TEST_AGENTS_DIR pointed at this dir's `agents/` subdirectory. Tears
everything down on session exit, including orphan Chromium processes.
"""
from __future__ import annotations

import os
import random
import signal
import socket
import string
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Iterator

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]  # repo root
TEST_AGENTS_DIR = Path(__file__).resolve().parent / "agents"
TEST_PORT = 8006
TEST_HOST = "127.0.0.1"
HEALTH_URL = f"http://{TEST_HOST}:{TEST_PORT}/api/health"
HEALTH_TIMEOUT_S = 30
SHUTDOWN_GRACE_S = 5


def _port_is_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) != 0


def _wait_for_health(url: str, timeout_s: int) -> None:
    deadline = time.monotonic() + timeout_s
    last_err = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return
        except Exception as e:  # noqa: BLE001
            last_err = e
        time.sleep(0.3)
    raise RuntimeError(
        f"Test server did not become healthy at {url} within {timeout_s}s; last error: {last_err}"
    )


@pytest.fixture(scope="session")
def test_db_path() -> Path:
    return Path(f"/tmp/diecast-uitest-{os.getpid()}.db")


@pytest.fixture(scope="session")
def test_goal_slug() -> str:
    rand4 = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"ui-test-{int(time.time())}-{rand4}"


@pytest.fixture(scope="session")
def test_server(test_db_path: Path) -> Iterator[str]:
    if not _port_is_free(TEST_HOST, TEST_PORT):
        raise RuntimeError(
            f"Port {TEST_PORT} is already bound on {TEST_HOST}. "
            "A prior test run likely leaked a process. "
            f"Find it: `lsof -iTCP:{TEST_PORT} -sTCP:LISTEN`"
        )

    cast_server_bin = REPO_ROOT / "bin" / "cast-server"
    assert cast_server_bin.exists(), f"Missing {cast_server_bin}"
    assert TEST_AGENTS_DIR.exists(), (
        f"Missing test agents dir {TEST_AGENTS_DIR}; expected sp4a/sp4b to have created it."
    )

    env = os.environ.copy()
    env["CAST_TEST_AGENTS_DIR"] = str(TEST_AGENTS_DIR)
    # Point the test server at the temp DB. The exact env var depends on the
    # cast-server entrypoint — check `bin/cast-server` for the canonical name
    # (likely `CAST_DB_PATH` or `DIECAST_DB`). Confirm before merging.
    env["CAST_DB_PATH"] = str(test_db_path)
    env["CAST_HOST"] = TEST_HOST
    env["CAST_PORT"] = str(TEST_PORT)

    proc = subprocess.Popen(
        [str(cast_server_bin)],
        env=env,
        cwd=str(REPO_ROOT),
        start_new_session=True,  # own process group → group-kill on teardown
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        _wait_for_health(HEALTH_URL, HEALTH_TIMEOUT_S)
        yield f"http://{TEST_HOST}:{TEST_PORT}"
    finally:
        # Group SIGTERM, 5s grace, escalate to SIGKILL.
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            proc.wait(timeout=SHUTDOWN_GRACE_S)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait(timeout=2)


@pytest.fixture(scope="session", autouse=True)
def _teardown(test_db_path: Path) -> Iterator[None]:
    yield
    warnings: list[str] = []

    # 1. Temp DB and any -wal/-shm siblings.
    for suffix in ("", "-wal", "-shm", "-journal"):
        p = Path(f"{test_db_path}{suffix}")
        if p.exists():
            try:
                p.unlink()
            except OSError as e:
                warnings.append(f"Could not remove {p}: {e}")

    # 2. goals/ui-test-* working-tree dirs.
    goals_dir = REPO_ROOT / "goals"
    if goals_dir.is_dir():
        for entry in goals_dir.glob("ui-test-*"):
            try:
                if entry.is_dir():
                    import shutil
                    shutil.rmtree(entry)
                else:
                    entry.unlink()
            except OSError as e:
                warnings.append(f"Could not remove {entry}: {e}")

    # 3. Sweep orphan Chromium processes whose remote-debugging-port is in the
    # test range. The pattern MUST be narrow enough to never match a dev browser.
    # Playwright launches Chromium with --remote-debugging-port=<random>, so we
    # match the broader process pattern that includes our test-only user-data-dir.
    # Convention: runner.py launches Playwright with a user-data-dir that contains
    # `diecast-uitest`; sweep on that.
    try:
        subprocess.run(
            ["pkill", "-f", "diecast-uitest"],
            check=False, timeout=5,
        )
    except Exception as e:  # noqa: BLE001
        warnings.append(f"pkill sweep failed: {e}")

    if warnings:
        # Surface warnings loudly so flake debugging is easy.
        for w in warnings:
            print(f"[ui-teardown WARNING] {w}")
```

### Step 2.4: Verify the test server can actually start

Once `cast-server/tests/ui/agents/` exists (sp4a/sp4b), the `test_server` fixture will be
runnable. Until then, you can sanity-check the fixture logic without dispatching agents:

```bash
cd /home/sridherj/workspace/diecast
mkdir -p cast-server/tests/ui/agents  # placeholder; sp4 fills it
pytest cast-server/tests/ui/conftest.py --collect-only
# Expect: no test files collected, but no import errors.
```

To exercise the actual fixture once stub agents exist (sp4a's noop is enough):

```bash
pytest cast-server/tests/ui/ -k 'not registry_visibility' --setup-show -q --collect-only
# Confirms fixtures resolve. A real run blocks until sp5 ships test_full_sweep.py.
```

### Step 2.5: Confirm the `CAST_DB_PATH` / `CAST_HOST` / `CAST_PORT` env var names

Read `bin/cast-server` to verify which env vars the entrypoint actually consumes. Adjust the
fixture's `env[...]` assignments to match. **This is the single most likely place for sp2
to be wrong** — verify before sp5 starts integrating.

If `bin/cast-server` doesn't expose env-var overrides for host/port/db, prefer adding them
there as a tiny shell-level addition rather than rewriting fixture invocation. Document the
addition in a brief inline comment.

## Verification

### Automated Tests (permanent)

This sub-phase ships fixtures, not tests. Verification is by `--collect-only` plus
downstream sub-phases that consume the fixtures. No new test files here.

### Validation Scripts (temporary)

```bash
# 1. Port-collision guard fires when :8006 is bound.
python -c "import socket; s=socket.socket(); s.bind(('127.0.0.1',8006)); s.listen(); input('hit enter to release')" &
SLEEP_PID=$!
sleep 1
pytest cast-server/tests/ui/ --setup-show 2>&1 | grep -i "8006" || echo "NO COLLISION ERROR"
kill $SLEEP_PID
wait $SLEEP_PID 2>/dev/null

# 2. Confirm pip can resolve the test extra.
cd cast-server && pip install -e ".[test]"
python -c "import playwright; print('playwright', playwright.__version__)"
```

### Manual Checks

```bash
# Confirm Playwright dev dep listed.
grep -A 3 'optional-dependencies' cast-server/pyproject.toml

# Confirm conftest is discoverable but doesn't break collection of the existing suite.
pytest cast-server/tests/ -q --collect-only > /tmp/collect.txt
grep -c "test_" /tmp/collect.txt
# Should match (or exceed by registry-visibility tests from sp1) the pre-sp1/sp2 count.
```

### Success Criteria

- [ ] `cast-server/pyproject.toml` lists `playwright` and `pytest-rerunfailures` under `[project.optional-dependencies] test`.
- [ ] `cast-server/tests/ui/conftest.py` defines `test_server`, `test_db_path`, `test_goal_slug`, and `_teardown` (autouse).
- [ ] `pytest cast-server/tests/ --collect-only` reports zero collection errors.
- [ ] Port-collision guard raises a clear `RuntimeError` naming `:8006` when the port is occupied.
- [ ] Teardown deletes the temp DB, removes `goals/ui-test-*`, and runs the `pkill -f diecast-uitest` sweep.
- [ ] `start_new_session=True` is set on the `Popen` call (process-group launch).
- [ ] No mutations to dev state — the fixture only writes under `/tmp` and inside the test repo's working tree.

## Execution Notes

- **The `pkill` sweep pattern is load-bearing.** It MUST NOT match a dev browser. The plan
  uses the substring `diecast-uitest` because sp3 will set `--user-data-dir=/tmp/diecast-uitest-<pid>`
  on every Playwright launch. If sp3 changes that path, update this sweep in lockstep.
- **`REPO_ROOT` calculation:** `Path(__file__).resolve().parents[3]` walks up from
  `cast-server/tests/ui/conftest.py` → `cast-server/tests/ui/` → `cast-server/tests/` →
  `cast-server/` → repo root. Verify the count is right by printing it once.
- **SIGINT safety:** pytest's session-scoped finalizers run even on SIGINT thanks to the
  `finally:` block in the generator fixture. Don't refactor to a teardown-only pattern that
  loses this property.
- **Env var names:** `CAST_DB_PATH`, `CAST_HOST`, `CAST_PORT` are educated guesses — confirm
  by reading `bin/cast-server`. Different names? Adapt and note in a code comment.
- **Health probe is `/api/health`**, not `/healthz`. Plan-review issue #1.
- **`pytest-rerunfailures` is opt-in only:** never blanket-enable retries. Default behavior
  is zero retries. Tag specific tests with `@pytest.mark.flaky(reruns=2)` if they need it.
- **Spec-linked files:** None of the modified files are covered by a spec in `docs/specs/`.
- **No skill delegation needed for this sub-phase.** Standard pytest fixtures and subprocess
  management.
