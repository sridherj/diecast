"""B3 auto-review contract tests for cast-detailed-plan.

Per Phase 3a sub-phase sp3c_b3_auto_review (plan in
docs/execution/diecast-open-source/phase-3a/sp3c_b3_auto_review/plan.md),
cast-detailed-plan's Step 10 auto-dispatches cast-plan-review against the plan
file it just wrote, unless the `--no-review` flag is set:

  - default invocation → exactly one child run with agent_name="cast-plan-review",
  - `--no-review` (CLI) or `no_review: true` (delegation context) → zero children,
  - child failure / idle-timeout → parent stays "completed", parent.next_steps
    records a rerun-manually entry pointing at the plan file.

These tests exercise a Python harness that simulates Step 10's documented
workflow against an isolated goal directory. The harness mirrors the prompt-side
contract spelled out in `agents/cast-detailed-plan/cast-detailed-plan.md` § Step 10.
When the live agent is wired to this harness, the tests gate the regression.

Plan-review Issue #2 (resolved 2026-04-30) explicitly dropped the recursive-trigger
guard — `cast-plan-review` has no auto-trigger logic of its own to recurse on. We
do NOT assert on guard logic here. Reinstate guard tests only if that changes.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "b3_minimal_goal"
SYNTHETIC_CHILD = REPO_ROOT / "tests" / "fixtures" / "synthetic_child.py"


# ---------------------------------------------------------------------------
# Harness — mirrors Step 10 of cast-detailed-plan.md
# ---------------------------------------------------------------------------


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_run_id(prefix: str) -> str:
    return f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}_{prefix}"


def _copy_fixture(tmp_path: Path) -> Path:
    """Copy the b3_minimal_goal fixture into tmp_path; returns the copied goal_dir."""
    dst = tmp_path / "b3_minimal_goal"
    shutil.copytree(FIXTURE_ROOT, dst)
    return dst


def _write_primary_plan(goal_dir: Path) -> Path:
    """Stand-in for Step 9: write the detailed plan and return its path.

    Includes one intentionally-questionable decision so cast-plan-review has
    something to surface in the chain test.
    """
    plan_dir = goal_dir / "docs" / "plan"
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plan_dir / "2026-04-30-b3-minimal-goal-fixture.md"
    plan_path.write_text(
        "# B3 Minimal Goal Fixture: Auto-Review Smoke\n\n"
        "## Overview\nDry-run plan for the B3 fixture.\n\n"
        "## Operating Mode\n**HOLD SCOPE** — fixture has no signal words.\n\n"
        "<!-- ISSUE-1-MARKER -->\n"
        "## Sub-phase 1: Wire the Smoke\n"
        "**Outcome:** auto-review fires on default invocation.\n"
        "**Verification:** `pytest tests/test_b3_auto_review.py -v`\n",
        encoding="utf-8",
    )
    return plan_path


def _atomic_write_terminal(output_path: Path, run_id: str, status: str) -> None:
    """Write a contract-v2 terminal payload via tmp+rename (atomic-write contract)."""
    payload = {
        "contract_version": "2",
        "agent_name": "cast-plan-review",
        "task_title": "B3 fixture child",
        "status": status,
        "summary": f"synthetic cast-plan-review (status={status})",
        "artifacts": [],
        "errors": [],
        "next_steps": [],
        "human_action_needed": False,
        "human_action_items": [],
        "started_at": _utcnow_iso(),
        "completed_at": _utcnow_iso(),
    }
    tmp = output_path.with_suffix(output_path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, output_path)


def _dispatch_synthetic_child(
    goal_dir: Path,
    parent_run_id: str,
    *,
    mode: str = "happy",
    delay_seconds: float = 0.05,
    status: str = "completed",
) -> tuple[str, subprocess.Popen | None, Path]:
    """Spawn (or simulate) the cast-plan-review child.

    `mode="happy"` with `status="completed"` uses the synthetic_child fixture so the
    file-based polling path exercises a real subprocess + atomic rename. Other status
    values are written inline (subprocess unnecessary; the test only needs the
    terminal payload to land). `mode="silent"` spawns the silent synthetic_child so
    the parent's idle-timeout path is exercised against a real never-writing child.

    Returns (child_run_id, popen_or_none, output_path). Caller must wait/kill if a
    Popen is returned.
    """
    child_run_id = _new_run_id("child")
    output_path = goal_dir / f".agent-{child_run_id}.output.json"

    if mode == "silent":
        argv = [
            sys.executable,
            str(SYNTHETIC_CHILD),
            "--output-path",
            str(output_path),
            "--run-id",
            child_run_id,
            "--mode",
            "silent",
        ]
        return child_run_id, subprocess.Popen(argv), output_path

    if mode == "happy" and status == "completed":
        argv = [
            sys.executable,
            str(SYNTHETIC_CHILD),
            "--output-path",
            str(output_path),
            "--run-id",
            child_run_id,
            "--mode",
            "happy",
            "--delay",
            str(delay_seconds),
        ]
        return child_run_id, subprocess.Popen(argv), output_path

    if mode == "happy":
        # Non-completed terminal status — inline-write the payload (no subprocess).
        _atomic_write_terminal(output_path, child_run_id, status)
        return child_run_id, None, output_path

    raise ValueError(f"unsupported synthetic_child mode: {mode}")


def _poll_until_terminal(
    output_path: Path,
    *,
    idle_timeout_seconds: float,
    backoff_ladder_seconds: Iterable[float] = (0.01, 0.02, 0.05),
) -> dict | None:
    """File-based polling per cast-delegation-contract spec.

    Returns the terminal payload dict on success, or None on idle-timeout.
    Tracks last-mtime as the heartbeat reset signal (heartbeat-by-mtime).
    """
    start = time.monotonic()
    last_mtime = 0.0
    last_change = start
    ladder = list(backoff_ladder_seconds) or [0.05]
    idx = 0
    while True:
        now = time.monotonic()
        if output_path.exists():
            mtime = output_path.stat().st_mtime
            if mtime != last_mtime:
                last_mtime = mtime
                last_change = now
            try:
                payload = json.loads(output_path.read_text())
            except json.JSONDecodeError:
                # mid-write window — caller must atomic-rename per spec
                payload = None
            if payload and "status" in payload:
                return payload
        # Heartbeat-aware idle timeout
        if now - last_change > idle_timeout_seconds:
            return None
        time.sleep(ladder[min(idx, len(ladder) - 1)])
        idx += 1


def _build_parent_state(
    *,
    parent_run_id: str,
    plan_path: Path,
    child_runs: list[dict],
    next_steps: list[dict],
    started_at: str,
) -> dict:
    """Build the parent's terminal output payload, contract v2."""
    return {
        "contract_version": "2",
        "agent_name": "cast-detailed-plan",
        "task_title": "B3 fixture parent",
        "status": "completed",
        "summary": "B3 dry-run parent",
        "artifacts": [
            {
                "path": str(plan_path),
                "type": "plan",
                "description": "Detailed plan written by Step 9",
            }
        ],
        "errors": [],
        "next_steps": next_steps,
        "human_action_needed": False,
        "human_action_items": [],
        "started_at": started_at,
        "completed_at": _utcnow_iso(),
        # Test-only side-channel — parent_run_id and child_runs are NOT part of the
        # contract; the harness exposes them so tests can assert the chain shape.
        "_test_parent_run_id": parent_run_id,
        "_test_child_runs": child_runs,
    }


def run_cast_detailed_plan(
    *,
    goal_dir: Path,
    cli_args: list[str] | None = None,
    delegation_context: dict | None = None,
    child_mode: str = "happy",
    child_delay_seconds: float = 0.05,
    child_status: str = "completed",
    idle_timeout_seconds: float = 5.0,
) -> dict:
    """Drive Step 10 end-to-end against the b3_minimal_goal fixture.

    Mirrors the pseudocode block in cast-detailed-plan.md § Step 10:
      1. Step 9: write the primary plan (stand-in here).
      2. Resolve `no_review` from delegation context OR cli_args.
      3. If not no_review: dispatch cast-plan-review (synthetic_child stand-in),
         poll until terminal, append the right next_steps[] entry by status.
      4. Build the contract-v2 parent payload and return it.
    """
    cli_args = list(cli_args or [])
    delegation_context = delegation_context or {}
    parent_run_id = _new_run_id("parent")
    started_at = _utcnow_iso()

    # Step 9 stand-in
    plan_path = _write_primary_plan(goal_dir)

    # Step 10 — read --no-review from delegation context OR CLI
    no_review = bool(delegation_context.get("no_review", False)) or "--no-review" in cli_args

    child_runs: list[dict] = []
    next_steps: list[dict] = []

    if not no_review:
        child_run_id, proc, output_path = _dispatch_synthetic_child(
            goal_dir,
            parent_run_id,
            mode=child_mode,
            delay_seconds=child_delay_seconds,
            status=child_status,
        )
        try:
            terminal = _poll_until_terminal(
                output_path, idle_timeout_seconds=idle_timeout_seconds
            )
        finally:
            if proc is not None:
                try:
                    proc.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()

        child_record = {
            "run_id": child_run_id,
            "agent_name": "cast-plan-review",
            "status": (terminal or {}).get("status", "timeout"),
            "output_path": str(output_path),
        }
        child_runs.append(child_record)

        if terminal and terminal.get("status") == "completed":
            next_steps.append(
                {
                    "command": f"# Review applied: see Decisions appendix in {plan_path}",
                    "rationale": "cast-plan-review processed all decisions inline (B2 single-Write contract)",
                    "artifact_anchor": str(plan_path),
                }
            )
        else:
            # status in {partial, failed} or idle-timeout (terminal is None)
            next_steps.append(
                {
                    "command": f"/cast-plan-review {plan_path}",
                    "rationale": "auto-review did not complete; rerun manually",
                    "artifact_anchor": str(plan_path),
                }
            )

    return _build_parent_state(
        parent_run_id=parent_run_id,
        plan_path=plan_path,
        child_runs=child_runs,
        next_steps=next_steps,
        started_at=started_at,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_b3_auto_review_fires_by_default(tmp_path, monkeypatch):
    """Default CLI invocation → exactly one cast-plan-review child."""
    monkeypatch.setenv("CAST_DISABLE_SERVER", "1")
    monkeypatch.setenv("CAST_DELEGATION_BACKOFF_OVERRIDE", "10ms,20ms")
    monkeypatch.setenv("CAST_DELEGATION_IDLE_TIMEOUT_SECONDS", "30")

    goal_dir = _copy_fixture(tmp_path)
    parent = run_cast_detailed_plan(goal_dir=goal_dir, cli_args=[])

    children = parent["_test_child_runs"]
    assert len(children) == 1, f"expected 1 child, got {len(children)}"
    assert children[0]["agent_name"] == "cast-plan-review"
    assert children[0]["status"] == "completed"
    assert parent["status"] == "completed"
    # Default-completed branch references the Decisions appendix
    assert any(
        "Decisions appendix" in step.get("rationale", "")
        or "Decisions appendix" in step.get("command", "")
        for step in parent["next_steps"]
    ), parent["next_steps"]


def test_b3_no_review_flag_suppresses(tmp_path, monkeypatch):
    """`--no-review` CLI arg → zero children dispatched."""
    monkeypatch.setenv("CAST_DISABLE_SERVER", "1")
    goal_dir = _copy_fixture(tmp_path)

    parent = run_cast_detailed_plan(goal_dir=goal_dir, cli_args=["--no-review"])

    assert parent["_test_child_runs"] == []
    assert parent["status"] == "completed"
    # No "rerun manually" entry — there was no failed child
    assert not any("rerun manually" in step.get("rationale", "") for step in parent["next_steps"])


def test_b3_no_review_via_delegation_context(tmp_path, monkeypatch):
    """`no_review: true` in delegation context also suppresses (covers child-mode)."""
    monkeypatch.setenv("CAST_DISABLE_SERVER", "1")
    goal_dir = _copy_fixture(tmp_path)

    parent = run_cast_detailed_plan(
        goal_dir=goal_dir,
        cli_args=[],
        delegation_context={"no_review": True},
    )

    assert parent["_test_child_runs"] == []
    assert parent["status"] == "completed"


def test_b3_child_failure_does_not_fail_parent(tmp_path, monkeypatch):
    """Child idle-timeout → parent stays completed; next_steps has rerun-manually."""
    monkeypatch.setenv("CAST_DISABLE_SERVER", "1")
    monkeypatch.setenv("CAST_DELEGATION_IDLE_TIMEOUT_SECONDS", "1")  # force timeout

    goal_dir = _copy_fixture(tmp_path)

    parent = run_cast_detailed_plan(
        goal_dir=goal_dir,
        cli_args=[],
        child_mode="silent",
        idle_timeout_seconds=0.3,
    )

    assert parent["status"] == "completed"  # parent still succeeds
    children = parent["_test_child_runs"]
    assert len(children) == 1
    assert children[0]["status"] == "timeout"
    assert any(
        "rerun manually" in step.get("rationale", "") for step in parent["next_steps"]
    ), parent["next_steps"]
    # Rerun command points at the plan file we wrote in Step 9
    plan_step = next(
        s for s in parent["next_steps"] if "rerun manually" in s.get("rationale", "")
    )
    assert plan_step["artifact_anchor"].endswith("2026-04-30-b3-minimal-goal-fixture.md")
    assert plan_step["command"].startswith("/cast-plan-review ")


def test_b3_child_failed_status_records_rerun(tmp_path, monkeypatch):
    """Child writes status=failed → parent records rerun-manually but stays completed."""
    monkeypatch.setenv("CAST_DISABLE_SERVER", "1")
    goal_dir = _copy_fixture(tmp_path)

    parent = run_cast_detailed_plan(
        goal_dir=goal_dir,
        cli_args=[],
        child_status="failed",
    )

    assert parent["status"] == "completed"
    children = parent["_test_child_runs"]
    assert len(children) == 1
    assert children[0]["status"] == "failed"
    assert any(
        "rerun manually" in step.get("rationale", "") for step in parent["next_steps"]
    )


def test_b3_no_self_trigger_guard_logic_in_prompt():
    """Regression guard for plan-review Issue #2.

    Issue #2 dropped the recursive auto-trigger guard (YAGNI: cast-plan-review has
    no auto-trigger to recurse on). The Step 10 documentation may *mention* that
    the guard was dropped, but the dispatch pseudocode must NOT contain branch
    logic that filters by agent_name to skip cast-plan-review.

    Detect regression: scan the pseudocode block for guard-shaped conditionals
    referencing the agent name. Mention of the dropped decision in prose is fine.
    """
    prompt = (REPO_ROOT / "agents" / "cast-detailed-plan" / "cast-detailed-plan.md").read_text()
    forbidden_patterns = [
        'if agent_name == "cast-plan-review"',
        "if target == \"cast-plan-review\"",
        "skip cast-plan-review",
        "prevent recursion",
    ]
    for pat in forbidden_patterns:
        assert pat not in prompt.lower(), (
            f"Recursive-guard logic regression: '{pat}' found in cast-detailed-plan.md "
            "(plan-review Issue #2 dropped this guard intentionally)."
        )
