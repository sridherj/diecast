"""T2 live-HTTP E2E for child delegation.

Asserts cast-server boundary contract: ``parent_run_id`` linkage in DB,
tmux session teardown on terminal status, dispatch-precondition 422,
allowlist denial, mid-flight session isolation. The fixture agents under
``cast-server/tests/integration/agents/`` are the SUTs.

Markers and discipline (FR-008 / Review #9 / Review #10):
- ``@pytest.mark.e2e``: PR CI runs T1 only; T2 runs nightly via the
  ``e2e`` marker filter (sp5.4 will wire the workflow YAML).
- ``@pytest.mark.timeout(360)``: per-case ceiling, 300s idle_timeout +
  60s buffer (cast-delegation-contract.collab.md). Production cadence —
  no env-var overrides.
- HTTP via bash curl (``_curl_post`` / ``_curl_get``). NO Python
  ``requests``/``httpx``/``urllib`` imports anywhere in this module
  (FR-008). The grep gate in ``plan.md`` Step 5.1.4 enforces this.

Polling primitive: parent and child terminal-state observation polls
the cast-server SQLite ``agent_runs`` table directly (via
``cast_server.services.agent_service.get_agent_run``). HTTP polling is
not the boundary for state observation; the cast-server is.

sp5.1 status: this is the SKELETON for ``test_parent_delegator_happy_path``
(US3.S1). sp5.2 adds ``test_delegation_denied`` (US3.S2); sp5.3 adds
``test_mid_flight_session_isolation``. The HTTP request bodies for
``trigger`` are placeholders pending the fixture-port reconciliation
documented in ``conftest.py``; see plan §Execution Notes.
"""

from __future__ import annotations

import json
import subprocess
import time
from typing import Any

import pytest

from cast_server.services import agent_service

E2E_GOAL_SLUG = "child-delegation-e2e"

# Terminal states for ``agent_runs.status`` per
# ``docs/specs/cast-delegation-contract.collab.md``.
_TERMINAL_STATUSES = {"completed", "failed", "cancelled", "partial"}


def _curl_post(url: str, payload: dict[str, Any]) -> tuple[int, str, str]:
    """Bash-curl POST helper. FR-008-compliant — no Python HTTP clients.

    Returns ``(returncode, stdout, stderr)``. ``-fsS`` keeps curl quiet on
    success, surfaces server errors on stderr, and exits non-zero on
    HTTP >= 400 so callers can assert the trigger contract.
    """
    result = subprocess.run(
        [
            "curl", "-fsS", "-X", "POST", url,
            "-H", "Content-Type: application/json",
            "-d", json.dumps(payload),
        ],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def _curl_get(url: str) -> tuple[int, str, str]:
    """Bash-curl GET helper. FR-008-compliant."""
    result = subprocess.run(
        ["curl", "-fsS", url],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def _wait_for_run_terminal(run_id: str, timeout: int = 300, poll_interval: float = 2.0) -> dict:
    """Poll the agent_runs DB row until status is terminal or timeout fires.

    NOTE: this polls the DB, not HTTP. The cast-server itself is the boundary;
    once the row commits a terminal status, the run is observable from any
    process attached to the same SQLite file.
    """
    deadline = time.monotonic() + timeout
    last_seen: dict | None = None
    while time.monotonic() < deadline:
        row = agent_service.get_agent_run(run_id)
        if row is not None:
            last_seen = row
            if row.get("status") in _TERMINAL_STATUSES:
                return row
        time.sleep(poll_interval)
    raise TimeoutError(
        f"run {run_id} did not reach terminal in {timeout}s "
        f"(last seen status={last_seen.get('status') if last_seen else 'no row'})"
    )


def _children_of(parent_run_id: str) -> list[dict]:
    """All ``agent_runs`` rows whose ``parent_run_id`` matches."""
    return [
        r for r in agent_service.get_runs_for_goal(E2E_GOAL_SLUG)
        if r.get("parent_run_id") == parent_run_id
    ]


def _tmux_session_alive(run_id: str) -> bool:
    """Return True if the per-run tmux session ``agent-<run_id>`` exists."""
    result = subprocess.run(
        ["tmux", "has-session", "-t", f"agent-{run_id}"],
        capture_output=True,
    )
    return result.returncode == 0


@pytest.mark.e2e
@pytest.mark.timeout(360)
def test_parent_delegator_happy_path(
    cast_server_base_url: str, reset_e2e_goal_dir,
) -> None:
    """US3.S1 — parent dispatches child via HTTP, both reach terminal.

    Asserts:
    - Parent run reaches ``completed`` (or terminal).
    - At least one child run exists with ``parent_run_id`` linkage.
    - Child run reaches a terminal status with non-empty ``result_summary``.
    - Child's tmux session ``agent-<child_run_id>`` is torn down after
      finalization (cleanup contract).
    """
    rc, out, err = _curl_post(
        f"{cast_server_base_url}/api/agents/cast-test-parent-delegator/trigger",
        {
            "goal_slug": E2E_GOAL_SLUG,
            "parent_run_id": "",
            "delegation_context": {
                "agent_name": "cast-test-parent-delegator",
                "instructions": "Run the determinism-pinned procedure end-to-end.",
                "context": {"goal_title": "Child Delegation E2E"},
                "output": {
                    "output_dir": str(reset_e2e_goal_dir),
                    "expected_artifacts": [],
                },
            },
        },
    )
    assert rc == 0, f"parent trigger failed: rc={rc} stderr={err!r}"
    parent_run_id = json.loads(out).get("run_id")
    assert parent_run_id, f"trigger response missing run_id: {out!r}"

    parent = _wait_for_run_terminal(parent_run_id)
    assert parent["status"] == "completed", (
        f"parent terminal status was {parent['status']!r}, expected 'completed'"
    )

    children = _children_of(parent_run_id)
    assert children, f"no children linked to parent_run_id={parent_run_id}"
    child = children[0]
    assert child["parent_run_id"] == parent_run_id
    assert child.get("result_summary"), (
        f"child {child['id']} has empty result_summary"
    )

    # Cleanup contract — tmux session torn down after finalize.
    assert not _tmux_session_alive(child["id"]), (
        f"child tmux session agent-{child['id']} still alive post-terminal"
    )


@pytest.mark.e2e
@pytest.mark.timeout(360)
def test_delegation_denied(
    cast_server_base_url: str, reset_e2e_goal_dir,
) -> None:
    """US3.S2 — parent dispatches a non-allowlisted target.

    The ``cast-test-delegation-denied`` fixture's prompt deliberately tries
    to HTTP-trigger ``cast-test-child-worker-subagent``, which is NOT in its
    ``allowed_delegations`` list. The cast-server allowlist check must
    return 422; the parent then surfaces that verdict in its own output JSON.

    Asserts (per plan §sp5.2 / cast-delegation-contract.collab.md §Allowlist
    Validation):
    - Parent reaches a terminal status (graceful — no crash).
    - No child ``agent_runs`` rows linked to the parent (denial fired
      BEFORE row create).
    - Parent's ``result_summary`` contains the byte-stable substring
      ``"422"`` OR ``"denied"`` — pinned to the literal envelope written
      by the sp1.2 fixture prompt (``"denied (422)"``). If this assertion
      fails because the substring is missing, diagnose the fixture's
      prompt determinism (sp1.2 / Review #5), NOT the assertion.
    """
    rc, out, err = _curl_post(
        f"{cast_server_base_url}/api/agents/cast-test-delegation-denied/trigger",
        {
            "goal_slug": E2E_GOAL_SLUG,
            "parent_run_id": "",
            "delegation_context": {
                "agent_name": "cast-test-delegation-denied",
                "instructions": "Run the literal denied-dispatch procedure end-to-end.",
                "context": {"goal_title": "Child Delegation E2E"},
                "output": {
                    "output_dir": str(reset_e2e_goal_dir),
                    "expected_artifacts": [],
                },
            },
        },
    )
    assert rc == 0, f"parent trigger failed: rc={rc} stderr={err!r}"
    parent_run_id = json.loads(out).get("run_id")
    assert parent_run_id, f"trigger response missing run_id: {out!r}"

    parent = _wait_for_run_terminal(parent_run_id)
    assert parent["status"] in _TERMINAL_STATUSES, (
        f"parent terminal status was {parent['status']!r}, expected terminal"
    )

    children = _children_of(parent_run_id)
    assert len(children) == 0, (
        f"no child rows expected for denied dispatch; got {len(children)}: "
        f"{[c.get('id') for c in children]!r}"
    )

    summary = parent.get("result_summary") or ""
    assert "422" in summary or "denied" in summary, (
        f"expected '422' or 'denied' in result_summary, got: {summary!r}"
    )


def _list_tmux_sessions() -> list[str]:
    """Return current tmux session names (empty list if no server running)."""
    result = subprocess.run(
        ["tmux", "list-sessions", "-F", "#{session_name}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [s for s in result.stdout.split("\n") if s]


@pytest.mark.e2e
@pytest.mark.timeout(360)
def test_mid_flight_session_isolation(
    cast_server_base_url: str, reset_e2e_goal_dir,
) -> None:
    """US3.S3 — parent and child run in separate tmux sessions; parent has 1 pane.

    Polls tmux sessions for up to 60s (cast-delegation-contract.collab.md
    §Session Isolation observation window) looking for both
    ``agent-<parent_run_id>`` and ``agent-<child_run_id>`` to be alive at the
    same time. If the child completes before that observation window catches
    both, ``pytest.skip("child too fast to observe mid-flight")`` — the skip
    string is verbatim from second-brain's
    ``test_tier2_delegation.py::test_mid_flight_session_isolation`` and is
    the spec-authorized pattern for this race (plan §Out of Scope: no
    "slow-child" knob).

    Once both sessions are observed alive, asserts:
    - The two session names differ (isolation invariant — separate tmux
      sessions, NOT split panes within one session).
    - The parent session has exactly 1 pane (per
      ``cast-delegation-contract.collab.md`` §Session Isolation: parent
      MUST NOT split its own pane to host the child).
    """
    rc, out, err = _curl_post(
        f"{cast_server_base_url}/api/agents/cast-test-parent-delegator/trigger",
        {
            "goal_slug": E2E_GOAL_SLUG,
            "parent_run_id": "",
            "delegation_context": {
                "agent_name": "cast-test-parent-delegator",
                "instructions": "Run the determinism-pinned procedure end-to-end.",
                "context": {"goal_title": "Child Delegation E2E"},
                "output": {
                    "output_dir": str(reset_e2e_goal_dir),
                    "expected_artifacts": [],
                },
            },
        },
    )
    assert rc == 0, f"parent trigger failed: rc={rc} stderr={err!r}"
    parent_run_id = json.loads(out).get("run_id")
    assert parent_run_id, f"trigger response missing run_id: {out!r}"

    deadline = time.monotonic() + 60
    parent_seen = False
    child_seen = False
    child_run_id: str | None = None

    while time.monotonic() < deadline:
        sessions = _list_tmux_sessions()
        if f"agent-{parent_run_id}" in sessions:
            parent_seen = True
        children = _children_of(parent_run_id)
        if children:
            child_run_id = children[0].get("id")
            if child_run_id and f"agent-{child_run_id}" in sessions:
                child_seen = True
                if parent_seen:
                    break
        time.sleep(0.5)

    if not (parent_seen and child_seen):
        pytest.skip("child too fast to observe mid-flight")

    assert child_run_id is not None
    assert f"agent-{parent_run_id}" != f"agent-{child_run_id}", (
        f"parent and child share session name agent-{parent_run_id} — "
        f"isolation invariant violated"
    )

    pane_result = subprocess.run(
        [
            "tmux", "list-panes", "-t", f"agent-{parent_run_id}",
            "-F", "#{pane_index}",
        ],
        capture_output=True,
        text=True,
    )
    panes = [p for p in pane_result.stdout.strip().split("\n") if p]
    assert len(panes) == 1, (
        f"parent agent-{parent_run_id} has {len(panes)} panes, expected 1; "
        f"raw list-panes output: {pane_result.stdout!r}"
    )
