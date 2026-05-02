"""T2 e2e fixtures for child-delegation live-HTTP suite.

Lifecycle (Review #9):
- ``cast_server_process``: SESSION-scoped — single ``cast-server`` subprocess,
  reused across cases. Health-checked via ``GET /api/agents/runs?status=running``
  (cast-server has no ``/healthz``; this endpoint returns 200 once routes are
  mounted, which is the contract surface the suite cares about).
- ``reset_e2e_goal_dir``: PER-TEST reset of runtime artifacts under the
  ``child-delegation-e2e`` goal directory plus all ``agent_runs`` rows scoped
  to that ``goal_slug``. ``goal.yaml`` and ``requirements.human.md`` (if any)
  are preserved.
- ``CAST_TEST_AGENTS_DIR`` is exported into the spawned cast-server's env so
  the four delegation fixtures under ``cast-server/tests/integration/agents/``
  register via the existing ``_candidate_config_paths`` seam (matches sp1.3
  hand-off note in ``tests/integration/conftest.py``).

Production cadence (spec §Constraints):
- T1's env-var overrides (``CAST_DISABLE_SERVER``,
  ``CAST_DELEGATION_BACKOFF_OVERRIDE``, ``CAST_DELEGATION_IDLE_TIMEOUT_SECONDS``)
  are NOT set here. T2 runs at production timing.

Per-case timeout (Review #10):
- Each test in ``test_tier_delegation.py`` is decorated with
  ``@pytest.mark.timeout(360)``. 360s = idle_timeout (300s default per
  ``docs/specs/cast-delegation-contract.collab.md``) + 60s buffer for
  sequential parent + child runs. ``pytest-timeout`` plugin must be installed
  for the marker to take effect; absence emits an "unknown marker" warning
  but does not fail the suite.

Port note:
- The fixture spawns cast-server on ``CAST_E2E_PORT`` (default 8765) to avoid
  colliding with a developer-local cast-server on the canonical 8005. The
  delegation fixture agent prompts under
  ``cast-server/tests/integration/agents/`` currently hard-code
  ``http://localhost:8005`` for the child-trigger curl. Reconciling that
  hard-coded port with the spawned port is a known follow-up — sp5.4 will
  decide whether to template the fixture prompts or pin the spawn port to
  8005 (with a "port-occupied → fail fast" precondition). For sp5.1 this
  conftest is correct in shape; the fixture-port reconciliation is the only
  blocker between this skeleton and a green ``test_parent_delegator_happy_path``.
"""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
INTEGRATION_AGENTS_DIR = REPO_ROOT / "cast-server" / "tests" / "integration" / "agents"
CAST_SERVER_BIN = REPO_ROOT / "bin" / "cast-server"

E2E_GOAL_SLUG = "child-delegation-e2e"
E2E_HOST = os.environ.get("CAST_E2E_HOST", "127.0.0.1")
E2E_PORT = int(os.environ.get("CAST_E2E_PORT", "8765"))
E2E_BASE_URL = f"http://{E2E_HOST}:{E2E_PORT}"

# Health-check probes the agents listing endpoint — returns 200 with a JSON
# array once routes are mounted. cast-server has no dedicated /healthz; the
# /api/health endpoint shells out to bin/cast-doctor (slow, off-topic for a
# liveness probe), so this is the right surface for a startup gate.
_HEALTH_PROBE_PATH = "/api/agents/runs?status=running"
_HEALTH_TIMEOUT_SECONDS = 30


def _port_is_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
        except OSError:
            return False
    return True


@pytest.fixture(scope="session")
def cast_server_process():
    """Spawn cast-server on E2E_PORT; tear down at session end (SIGTERM).

    Fails fast and clearly if:
    - bin/cast-server is missing (developer host without diecast checkout).
    - The port is already in use (another cast-server instance or stale process).
    - The server does not respond within _HEALTH_TIMEOUT_SECONDS.
    """
    if not CAST_SERVER_BIN.exists():
        raise RuntimeError(
            f"cast-server bin not found at {CAST_SERVER_BIN}. "
            "T2 e2e suite requires the diecast checkout layout."
        )
    if not _port_is_free(E2E_HOST, E2E_PORT):
        raise RuntimeError(
            f"Port {E2E_HOST}:{E2E_PORT} is already in use. "
            "Stop any pre-existing cast-server before running the T2 suite "
            "(or set CAST_E2E_PORT to a free port — but be aware the "
            "delegation fixture agents hardcode http://localhost:8005)."
        )

    env = {
        **os.environ,
        "CAST_TEST_AGENTS_DIR": str(INTEGRATION_AGENTS_DIR),
        "CAST_PORT": str(E2E_PORT),
        "CAST_BIND_HOST": E2E_HOST,
    }

    # bin/cast-server execs uvicorn; --port arg is forwarded via "$@" and wins
    # over CAST_PORT, so pass it explicitly to be unambiguous.
    proc = subprocess.Popen(
        [str(CAST_SERVER_BIN), "--port", str(E2E_PORT), "--host", E2E_HOST],
        env=env,
        # New process group so we can SIGTERM the whole tree on teardown.
        preexec_fn=os.setsid,
    )

    deadline = time.monotonic() + _HEALTH_TIMEOUT_SECONDS
    last_err: str = ""
    while time.monotonic() < deadline:
        # Poll process liveness — if the server crashed during startup, fail
        # immediately rather than burning the full 30s on retries.
        if proc.poll() is not None:
            raise RuntimeError(
                f"cast-server exited with code {proc.returncode} during startup."
            )
        result = subprocess.run(
            ["curl", "-fsS", "-o", "/dev/null", f"{E2E_BASE_URL}{_HEALTH_PROBE_PATH}"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            break
        last_err = result.stderr.strip() or "(no stderr)"
        time.sleep(0.5)
    else:
        # Timed out without ever hitting the probe.
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass
        raise RuntimeError(
            f"cast-server did not become healthy at {E2E_BASE_URL} within "
            f"{_HEALTH_TIMEOUT_SECONDS}s. Last curl stderr: {last_err}"
        )

    yield proc

    # Teardown — SIGTERM the process group, then SIGKILL after a grace period.
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait(timeout=10)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass


@pytest.fixture(scope="session")
def cast_server_base_url(cast_server_process) -> str:
    """Base URL for the spawned cast-server. Curl helpers prepend this."""
    return E2E_BASE_URL


@pytest.fixture
def reset_e2e_goal_dir(cast_server_process):
    """Per-test reset of runtime artifacts and DB rows for the e2e goal.

    Ensures the goal directory exists with an ``external_project_dir``
    pointing at itself (FR-008 / cast-delegation-contract precondition).
    Clears all runtime artifacts (``.agent-*``, ``.delegation-*``,
    ``*.prompt``, ``*.continue``) plus all ``agent_runs`` rows scoped to
    ``E2E_GOAL_SLUG`` between tests so each case starts from a known state.
    """
    from cast_server.config import GOALS_DIR
    from cast_server.services import goal_service

    goal_dir = GOALS_DIR / E2E_GOAL_SLUG
    goal_dir.mkdir(parents=True, exist_ok=True)

    # Idempotently ensure the goal row exists with external_project_dir set
    # to the goal directory itself — dispatch precondition (sp3.1, US2.S7).
    if not goal_service.get_goal(E2E_GOAL_SLUG):
        # _slugify("Child Delegation E2E") == "child-delegation-e2e"
        goal_service.create_goal(title="Child Delegation E2E")
    goal_service.update_config(
        E2E_GOAL_SLUG, external_project_dir=str(goal_dir),
    )

    _purge_goal_dir_runtime_artifacts(goal_dir)
    _delete_runs_for_goal(E2E_GOAL_SLUG)

    yield goal_dir

    # Post-test: same purge so a follow-on `pytest -x` rerun is also clean.
    _purge_goal_dir_runtime_artifacts(goal_dir)
    _delete_runs_for_goal(E2E_GOAL_SLUG)


def _purge_goal_dir_runtime_artifacts(goal_dir: Path) -> None:
    """Delete delegation/run runtime files; preserve goal.yaml + human-authored docs."""
    if not goal_dir.exists():
        return
    preserved = {"goal.yaml", "requirements.human.md"}
    for entry in goal_dir.iterdir():
        if entry.name in preserved:
            continue
        if entry.is_dir():
            # Subdirectories (exploration/, plan/, etc.) are author state.
            continue
        if (
            entry.name.startswith(".agent-")
            or entry.name.startswith(".delegation-")
            or entry.name.endswith(".prompt")
            or entry.name.endswith(".continue")
            or entry.name.endswith(".output.json")
            or entry.name.endswith(".output.json.tmp")
        ):
            try:
                entry.unlink()
            except FileNotFoundError:
                pass


def _delete_runs_for_goal(goal_slug: str) -> None:
    """Drop all agent_runs rows for ``goal_slug``. Fast — no FK cascade needed."""
    from cast_server.db.connection import get_connection

    conn = get_connection()
    try:
        conn.execute("DELETE FROM agent_runs WHERE goal_slug = ?", (goal_slug,))
        conn.commit()
    finally:
        conn.close()
