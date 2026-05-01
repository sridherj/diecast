"""Session-scoped fixtures for the Diecast UI e2e harness.

Boots a dedicated cast-server on :8006 against a temp SQLite DB, with
CAST_TEST_AGENTS_DIR pointed at this dir's `agents/` subdirectory. Tears
everything down on session exit, including orphan Chromium processes.
"""
from __future__ import annotations

import os
import random
import shutil
import signal
import socket
import string
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Iterator

import pytest

_SERVER_LOG_PATH: Path | None = None

# cast-server/tests/ui/conftest.py
#   parents[0] = cast-server/tests/ui
#   parents[1] = cast-server/tests
#   parents[2] = cast-server
#   parents[3] = repo root
REPO_ROOT = Path(__file__).resolve().parents[3]
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
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return
        except Exception as e:  # noqa: BLE001
            last_err = e
        time.sleep(0.3)
    raise RuntimeError(
        f"Test server did not become healthy at {url} within {timeout_s}s; "
        f"last error: {last_err}"
    )


@pytest.fixture(scope="session")
def test_db_path() -> Path:
    return Path(f"/tmp/diecast-uitest-{os.getpid()}.db")


@pytest.fixture(scope="session")
def test_goal_slug() -> str:
    rand4 = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"ui-test-{int(time.time())}-{rand4}"


@pytest.fixture(scope="session")
def seeded_test_goal(test_server: str, test_goal_slug: str) -> str:
    """Create the goal on the test server with external_project_dir set,
    so trigger_agent passes the dispatch precondition."""
    import urllib.parse

    title = test_goal_slug
    body = urllib.parse.urlencode({"title": title}).encode()
    req = urllib.request.Request(
        f"{test_server}/api/goals",
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    import re
    m = re.search(r'id="goal-card-([a-z0-9-]+)"', html)
    assert m, f"could not extract slug from goal-card response:\n{html[:500]}"
    slug = m.group(1)

    patch_body = urllib.parse.urlencode({"external_project_dir": str(REPO_ROOT)}).encode()
    req = urllib.request.Request(
        f"{test_server}/api/goals/{slug}/config",
        data=patch_body,
        method="PATCH",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        assert resp.status in (200, 204), f"PATCH config -> {resp.status}"

    return slug


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
        f"Missing test agents dir {TEST_AGENTS_DIR}; "
        "expected sp4a/sp4b to have created it."
    )

    fixture_start_ts = time.time()
    env = os.environ.copy()
    env["CAST_TEST_AGENTS_DIR"] = str(TEST_AGENTS_DIR)
    env["CAST_DB"] = str(test_db_path)
    env["CAST_BIND_HOST"] = TEST_HOST
    env["CAST_PORT"] = str(TEST_PORT)
    env["DIECAST_ROOT"] = str(REPO_ROOT)
    # Force unbuffered child stdout so post-startup uvicorn/app logs land in the
    # log file before SIGTERM. Without this Python block-buffers (~4KB) when
    # stdout is a regular file, and we lose everything after the Alembic stamp.
    env["PYTHONUNBUFFERED"] = "1"
    venv_bin = Path(sys.executable).parent
    env["PATH"] = f"{venv_bin}{os.pathsep}{env.get('PATH', '')}"

    global _SERVER_LOG_PATH
    log_path = Path(tempfile.gettempdir()) / f"diecast-uitest-server-{os.getpid()}.log"
    log_fh = log_path.open("w", buffering=1)  # line-buffered
    _SERVER_LOG_PATH = log_path

    proc = subprocess.Popen(
        [str(cast_server_bin)],
        env=env,
        cwd=str(REPO_ROOT),
        start_new_session=True,  # own process group → group-kill on teardown
        stdout=log_fh,
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
        try:
            log_fh.close()
        except Exception:  # noqa: BLE001
            pass
        try:
            result = subprocess.run(
                ["tmux", "ls", "-F", "#{session_name} #{session_created}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            for line in result.stdout.decode().splitlines():
                parts = line.strip().split()
                if len(parts) != 2:
                    continue
                name, created = parts
                if not name.startswith("agent-"):
                    continue
                try:
                    creation_ts = int(created)
                except ValueError:
                    continue
                if creation_ts >= fixture_start_ts:
                    subprocess.run(
                        ["tmux", "kill-session", "-t", name],
                        stderr=subprocess.DEVNULL,
                        timeout=5,
                    )
        except Exception:  # noqa: BLE001
            pass


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        item.session.config._diecast_uitest_failed = True

        log_path = _SERVER_LOG_PATH
        if log_path is None or not log_path.exists():
            return
        try:
            tail = log_path.read_text().splitlines()[-200:]
        except Exception:  # noqa: BLE001
            return
        body = "[test-cast-server stdout]:\n" + "\n".join(tail)
        report.sections.append(("[test-cast-server stdout]", body))


@pytest.fixture(scope="session", autouse=True)
def _teardown(
    test_db_path: Path, request: pytest.FixtureRequest
) -> Iterator[None]:
    yield
    warnings: list[str] = []

    # 0. If KEEP_UITEST_ARTIFACTS=1 is set, snapshot artifacts to a debug dir
    #    BEFORE we delete them. Useful for postmortem on failures.
    if os.environ.get("KEEP_UITEST_ARTIFACTS") == "1":
        debug_dir = Path(f"/tmp/diecast-uitest-debug-{int(time.time())}")
        debug_dir.mkdir(exist_ok=True)
        try:
            if test_db_path.exists():
                shutil.copy2(test_db_path, debug_dir / test_db_path.name)
            goals_dir = REPO_ROOT / "goals"
            if goals_dir.is_dir():
                for entry in goals_dir.glob("ui-test-*"):
                    if entry.is_dir():
                        shutil.copytree(entry, debug_dir / entry.name, dirs_exist_ok=True)
            print(f"\n[teardown] Snapshotted artifacts to {debug_dir}")
        except Exception as e:  # noqa: BLE001
            warnings.append(f"snapshot failed: {e}")

    # 1. Temp DB and any -wal/-shm/-journal siblings.
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
                    shutil.rmtree(entry)
                else:
                    entry.unlink()
            except OSError as e:
                warnings.append(f"Could not remove {entry}: {e}")

    # 3. Sweep orphan Chromium processes whose user-data-dir contains the
    # test-only marker `diecast-uitest`. sp3's runner.py is required to launch
    # Playwright with --user-data-dir=/tmp/diecast-uitest-<pid> so this pattern
    # matches ONLY test browsers, never a developer's Chromium session.
    try:
        subprocess.run(
            ["pkill", "-f", "diecast-uitest"],
            check=False,
            timeout=5,
        )
    except Exception as e:  # noqa: BLE001
        warnings.append(f"pkill sweep failed: {e}")

    # 4. Conditionally remove the test cast-server stdout log. On failure,
    #    leave it so the user can grep beyond the 200-line tail in the report.
    log_path = _SERVER_LOG_PATH
    if log_path is not None and log_path.exists():
        failed = getattr(request.config, "_diecast_uitest_failed", False)
        if not failed:
            try:
                log_path.unlink(missing_ok=True)
            except OSError as e:
                warnings.append(f"Could not remove {log_path}: {e}")

    if warnings:
        for w in warnings:
            print(f"[ui-teardown WARNING] {w}")
