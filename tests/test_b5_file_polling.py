"""B5 file-based polling integration tests.

Exercises the file-based parent polling primitive against the synthetic
child fixture. Three test cases cover the happy path, idle timeout, and
mtime-based heartbeat. The fourth test (atomic write under partial-write
race) lives in `test_b5_atomic_write.py`.

Per spec `docs/specs/cast-delegation-contract.collab.md`:
  - parent reads only the final output path (never `.tmp`)
  - terminal statuses: completed | partial | failed
  - idle timeout resets on output-file mtime change
  - HTTP API is best-effort; tests run with CAST_DISABLE_SERVER=1

Per Q#21: per-PR CI uses CAST_DISABLE_SERVER=1; nightly CI uses real pkill.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNTHETIC_CHILD = REPO_ROOT / "tests" / "fixtures" / "synthetic_child.py"

# Make the in-repo agents/_shared module importable.
sys.path.insert(0, str(REPO_ROOT))

from agents._shared.polling import poll_for_terminal_output  # noqa: E402


def _spawn_child(
    output_path: Path,
    run_id: str,
    mode: str,
    delay: float = 0.0,
) -> subprocess.Popen:
    """Launch synthetic_child.py as a subprocess (returns Popen handle)."""
    args = [
        sys.executable,
        str(SYNTHETIC_CHILD),
        "--output-path",
        str(output_path),
        "--run-id",
        run_id,
        "--mode",
        mode,
        "--delay",
        str(delay),
    ]
    return subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _no_http_traffic_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail loudly if the polling primitive ever reaches for HTTP libs.

    The spec mandates `cast-child-delegation` (and its Python encoding in
    `agents._shared.polling`) MUST never `import requests | httpx | urllib`.
    We can't easily intercept module-level imports, but we can poison the
    network surface so any actual call would raise.
    """
    import socket

    def _no_socket(*args, **kwargs):
        raise RuntimeError("polling primitive attempted network I/O — spec violation")

    monkeypatch.setattr(socket, "create_connection", _no_socket, raising=False)


def test_b5_happy_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Parent observes status=completed within 12s; zero HTTP calls; payload matches fixture shape."""
    monkeypatch.setenv("CAST_DISABLE_SERVER", "1")
    monkeypatch.setenv("CAST_DELEGATION_BACKOFF_OVERRIDE", "10ms,20ms,50ms,100ms")
    monkeypatch.setenv("CAST_DELEGATION_IDLE_TIMEOUT_SECONDS", "30")
    _no_http_traffic_guard(monkeypatch)

    run_id = "run_test_b5_happy"
    output_path = tmp_path / f".agent-run_{run_id}.output.json"

    child = _spawn_child(output_path, run_id, mode="happy", delay=2.0)
    try:
        start = time.monotonic()
        result = poll_for_terminal_output(str(output_path))
        elapsed = time.monotonic() - start
    finally:
        child.wait(timeout=10)

    assert elapsed < 12.0, f"polling took too long: {elapsed:.2f}s"
    assert result["status"] == "completed"
    assert result["agent_name"] == "synthetic-child"
    assert result["contract_version"] == "2"
    assert isinstance(result["artifacts"], list)
    assert isinstance(result["errors"], list)


def test_b5_idle_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Parent marks failed with human_action_needed=True after idle timeout; clear error."""
    monkeypatch.setenv("CAST_DISABLE_SERVER", "1")
    monkeypatch.setenv("CAST_DELEGATION_IDLE_TIMEOUT_SECONDS", "3")
    monkeypatch.setenv("CAST_DELEGATION_BACKOFF_OVERRIDE", "10ms,20ms,50ms,100ms,200ms")
    _no_http_traffic_guard(monkeypatch)

    run_id = "run_test_b5_idle"
    output_path = tmp_path / f".agent-run_{run_id}.output.json"

    child = _spawn_child(output_path, run_id, mode="silent")
    try:
        start = time.monotonic()
        result = poll_for_terminal_output(str(output_path))
        elapsed = time.monotonic() - start
    finally:
        child.terminate()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()

    assert result["status"] == "failed"
    assert result["human_action_needed"] is True
    assert result["errors"], "expected non-empty errors[]"
    assert any("idle" in err.lower() for err in result["errors"]), result["errors"]
    # Idle window is 3s; allow generous upper bound for backoff-jitter and CI clock skew.
    assert 2.5 <= elapsed <= 8.0, f"idle-timeout elapsed window violated: {elapsed:.2f}s"


def test_b5_heartbeat(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Heartbeat resets idle countdown — parent waits past nominal timeout, then sees completed."""
    # Idle timeout shorter than total child runtime; only mtime heartbeats keep the parent alive.
    monkeypatch.setenv("CAST_DISABLE_SERVER", "1")
    monkeypatch.setenv("CAST_DELEGATION_IDLE_TIMEOUT_SECONDS", "4")
    monkeypatch.setenv("CAST_DELEGATION_BACKOFF_OVERRIDE", "100ms,200ms,500ms")
    _no_http_traffic_guard(monkeypatch)

    run_id = "run_test_b5_heartbeat"
    output_path = tmp_path / f".agent-run_{run_id}.output.json"

    # Heartbeat for 8s (well past 4s idle timeout); ticks every 2s.
    child = _spawn_child(output_path, run_id, mode="heartbeat", delay=8.0)
    try:
        start = time.monotonic()
        result = poll_for_terminal_output(str(output_path))
        elapsed = time.monotonic() - start
    finally:
        child.wait(timeout=15)

    assert result["status"] == "completed", f"heartbeat path returned {result.get('status')}: {result}"
    # Total runtime should exceed nominal idle timeout (proves heartbeat reset worked).
    assert elapsed >= 6.0, f"completed too early — heartbeat may not have engaged: {elapsed:.2f}s"
    assert elapsed <= 14.0, f"runtime exceeds expected ceiling: {elapsed:.2f}s"
