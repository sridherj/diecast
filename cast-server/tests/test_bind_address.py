"""Regression test: cast-server binds to loopback only, not a wildcard.

Spawns ``bin/cast-server`` and asserts via ``psutil.net_connections()`` that
the listening socket is on 127.0.0.1 / ::1, never 0.0.0.0 / ::. A future
debug edit that changes the default to a wildcard address would fail this
test before reaching review.

Marked ``integration`` because it spawns a real process and binds a port.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = REPO_ROOT / "bin" / "cast-server"


def _wait_for_port(port: int, timeout: float = 10.0) -> bool:
    """Poll until a TCP listener is accepting on ``port`` or timeout elapses."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.25)
            try:
                sock.connect(("127.0.0.1", port))
                return True
            except OSError:
                time.sleep(0.1)
    return False


@pytest.mark.integration
def test_default_bind_is_loopback_only(tmp_path):
    psutil = pytest.importorskip("psutil")
    if shutil.which("uvicorn") is None:
        pytest.skip("uvicorn not installed; preflight would short-circuit launcher")
    if not LAUNCHER.exists():
        pytest.skip(f"launcher not found at {LAUNCHER}")

    # Use a free port + isolated DB so the test never collides with a running server.
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    env = {
        **os.environ,
        "CAST_PORT": str(port),
        "CAST_DB": str(tmp_path / "diecast.db"),
    }

    proc = subprocess.Popen(
        [str(LAUNCHER)],
        cwd=str(REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    try:
        assert _wait_for_port(port), f"server did not start listening on :{port}"

        listening = [
            c for c in psutil.net_connections(kind="inet")
            if c.status == psutil.CONN_LISTEN
            and c.laddr
            and c.laddr.port == port
        ]

        assert listening, f"no LISTEN sockets found on :{port}"
        assert any(c.laddr.ip in ("127.0.0.1", "::1") for c in listening), (
            f"expected loopback bind, got: {[c.laddr for c in listening]}"
        )
        assert not any(c.laddr.ip in ("0.0.0.0", "::") for c in listening), (
            "cast-server bound to a wildcard address — regression!"
        )
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
