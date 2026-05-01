"""Single pytest entry for the Diecast UI e2e harness.

Triggers the orchestrator, polls to terminal, asserts every child completed cleanly.
Per-child failures are surfaced via the orchestrator's structured output.json.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ORCHESTRATOR_TRIGGER_PATH = "/api/agents/cast-ui-test-orchestrator/trigger"
JOBS_POLL_PATH_TEMPLATE = "/api/agents/jobs/{run_id}"
TOTAL_TIMEOUT_S = 1200
POLL_INTERVAL_S = 5
TERMINAL_STATUSES = {"completed", "failed", "cancelled", "partial"}


def _http_post(url: str, body: dict) -> dict:
    req = urllib.request.Request(
        url,
        method="POST",
        headers={"Content-Type": "application/json"},
        data=json.dumps(body).encode(),
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        raise AssertionError(
            f"POST {url} -> {e.code} {e.reason}\nrequest body: {json.dumps(body, indent=2)}\nresponse body: {body_text}"
        ) from None


def _http_get(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, TimeoutError):
        time.sleep(2)
        with urllib.request.urlopen(url, timeout=60) as resp:
            return json.loads(resp.read())


def _poll_to_terminal(base_url: str, run_id: str, total_timeout_s: int) -> dict:
    """Poll a run to terminal status, proactively unblocking the spawn-Enter
    race: cast-server's tmux launcher sometimes types the prompt but doesn't
    submit it, leaving the agent idle. We periodically send Enter to any
    `agent-*` tmux session whose run is still in `pending` or `running` long
    enough to look stuck."""
    import subprocess
    deadline = time.monotonic() + total_timeout_s
    last_status: str | None = None
    seen_running_at: dict[str, float] = {}
    while time.monotonic() < deadline:
        try:
            job = _http_get(f"{base_url}{JOBS_POLL_PATH_TEMPLATE.format(run_id=run_id)}")
        except urllib.error.HTTPError as e:
            pytest.fail(f"polling failed for run_id={run_id}: HTTP {e.code}")
        last_status = job.get("status")
        if last_status in TERMINAL_STATUSES:
            return job
        try:
            sessions = subprocess.check_output(["tmux", "ls"], stderr=subprocess.DEVNULL, timeout=5).decode()
            for line in sessions.splitlines():
                name = line.split(":", 1)[0]
                if not name.startswith("agent-"):
                    continue
                first_seen = seen_running_at.setdefault(name, time.monotonic())
                if time.monotonic() - first_seen >= 15:
                    subprocess.run(["tmux", "send-keys", "-t", name, "Enter"], stderr=subprocess.DEVNULL, timeout=5)
        except Exception:  # noqa: BLE001
            pass
        time.sleep(POLL_INTERVAL_S)
    pytest.fail(
        f"orchestrator did not reach terminal status within {total_timeout_s}s "
        f"(last status: {last_status!r})"
    )


def _read_orchestrator_output(repo_root: Path, goal_slug: str, run_id: str) -> dict:
    """Read the orchestrator's terminal output JSON from its canonical path
    (per docs/specs/cast-output-json-contract.collab.md).

    Fails loudly if the file is missing — that indicates a contract bug, not a
    path-resolution problem.
    """
    path = repo_root / "goals" / goal_slug / f".agent-run_{run_id}.output.json"
    if not path.exists():
        pytest.fail(
            f"Orchestrator output JSON missing at canonical path: {path}\n"
            "This usually means the orchestrator did not finish writing its "
            "output, or the cast-output-json-contract has drifted."
        )
    return json.loads(path.read_text())


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


def test_ui_e2e(test_server: str, seeded_test_goal: str) -> None:
    """End-to-end UI sweep via the cast-ui-test-orchestrator agent."""
    repo_root = Path(__file__).resolve().parents[3]
    test_goal_slug = seeded_test_goal

    trigger_body = {
        "goal_slug": test_goal_slug,
        "delegation_context": {
            "agent_name": "cast-ui-test-orchestrator",
            "instructions": (
                f"Run the full UI test sweep against {test_server}. Trigger "
                "each per-screen child agent (cast-ui-test-{dashboard,agents,"
                "runs,scratchpad,goal-detail,focus,about}) in parallel, poll "
                "all to terminal status, aggregate per-child output.json, "
                "write your own output.json with status=completed if all "
                "children passed, partial if any failed."
            ),
            "context": {
                "goal_title": test_goal_slug,
                "goal_phase": "execution",
                "prior_output": "Test harness booted; orchestrator dispatched.",
            },
            "output": {
                "expected_artifacts": ["per-child output.json"],
            },
        },
    }
    triggered = _http_post(f"{test_server}{ORCHESTRATOR_TRIGGER_PATH}", trigger_body)
    run_id = triggered.get("run_id") or triggered.get("id")
    assert run_id, f"trigger response missing run_id: {triggered}"

    _poll_to_terminal(test_server, run_id, TOTAL_TIMEOUT_S)

    orch_output = _read_orchestrator_output(repo_root, test_goal_slug, run_id)
    status = orch_output.get("status")

    if status != "completed":
        failures = _format_child_failures(orch_output)
        if not failures:
            failures = (
                f"  (no children data — orchestrator failed before fan-out)\n"
                f"  orchestrator full output.json:\n{json.dumps(orch_output, indent=2)}"
            )
        pytest.fail(
            f"UI e2e sweep status={status!r}\n"
            f"summary={orch_output.get('summary')}\n"
            f"errors={orch_output.get('errors')}\n"
            f"failures:\n{failures}"
        )

    summary = orch_output.get("summary") or {}
    assert summary.get("failed", 0) == 0, f"summary indicates failures: {summary}"
    assert summary.get("total", 0) == 7, f"expected 7 children, got {summary.get('total')}"
