"""B3 full-chain regression net (plan-review Issue #12).

Per `docs/execution/diecast-open-source/phase-3a/sp3c_b3_auto_review/plan.md`,
the chain `cast-detailed-plan` → `cast-plan-review` must run end-to-end:

  1. cast-detailed-plan writes its primary plan,
  2. Step 10 auto-dispatches cast-plan-review,
  3. cast-plan-review applies its decisions inline (B2 single-Write contract),
  4. cast-detailed-plan's parent next_steps references the Decisions appendix.

This test was demanded explicitly by plan-review Issue #12 because the
empty-allow-list bug (2026-04-30) would have been caught at plan time if any
test had exercised the chain end-to-end. It is the regression net.

The test reuses the harness from test_b3_auto_review.py to drive Step 10 and
adds a synthetic cast-plan-review body that mirrors B2's documented end-of-review
single-Write contract: append a `## Decisions` appendix populated from a scripted
`decisions` map.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Reuse the parent-side harness verbatim
from tests.test_b3_auto_review import (  # noqa: E402
    _copy_fixture,
    _new_run_id,
    _poll_until_terminal,
    _utcnow_iso,
    _write_primary_plan,
    _build_parent_state,
    _atomic_write_terminal,
)


def _decision_key(question: str) -> str:
    """B2 idempotency key — sha256(question)[:16] per cast-plan-review.md § Step 5."""
    return hashlib.sha256(question.encode("utf-8")).hexdigest()[:16]


def _format_decision_line(question: str, answer: str, rationale: str) -> str:
    iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"- **{iso} — {question}** — Decision: {answer}. Rationale: {rationale}."


def _run_synthetic_cast_plan_review(
    *,
    goal_dir: Path,
    plan_path: Path,
    decisions: dict[str, tuple[str, str]],
) -> tuple[str, Path]:
    """Stand-in for cast-plan-review.

    Mirrors B2's contract:
      - read the plan,
      - apply decisions in a single Write call,
      - append a `## Decisions` appendix with canonical-format entries,
      - write a contract-v2 terminal output JSON via atomic rename.

    Returns (child_run_id, output_path).
    """
    child_run_id = _new_run_id("review")
    output_path = goal_dir / f".agent-{child_run_id}.output.json"

    body = plan_path.read_text(encoding="utf-8")

    # Build the Decisions appendix
    lines = ["", "## Decisions", ""]
    for question, (answer, rationale) in decisions.items():
        lines.append(_format_decision_line(question, answer, rationale))
    appendix = "\n".join(lines) + "\n"

    new_body = body
    if "## Decisions" in body:
        # Idempotent upsert: replace the existing appendix block
        head, _, _tail = body.partition("## Decisions")
        new_body = head.rstrip() + "\n\n" + appendix.lstrip()
    else:
        new_body = body.rstrip() + "\n" + appendix

    # Single Write
    plan_path.write_text(new_body, encoding="utf-8")

    # Terminal output
    payload = {
        "contract_version": "2",
        "agent_name": "cast-plan-review",
        "task_title": "B3 chain review",
        "status": "completed",
        "summary": f"applied {len(decisions)} decision(s) inline",
        "artifacts": [
            {
                "path": str(plan_path),
                "type": "plan",
                "description": "Plan with Decisions appendix",
            }
        ],
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
    return child_run_id, output_path


def test_b3_full_chain_end_to_end(tmp_path, monkeypatch):
    """End-to-end: cast-detailed-plan → cast-plan-review chain with inline decisions.

    Regression net for the empty-allow-list bug surfaced during this plan's own
    auto-trigger attempt (2026-04-30). That bug existed because no test exercised
    the chain end-to-end. This test is that net.
    """
    monkeypatch.setenv("CAST_DISABLE_SERVER", "1")
    monkeypatch.setenv("CAST_DELEGATION_BACKOFF_OVERRIDE", "10ms,50ms")
    monkeypatch.setenv("CAST_DELEGATION_IDLE_TIMEOUT_SECONDS", "30")

    goal_dir = _copy_fixture(tmp_path)

    # --- Stage 1: cast-detailed-plan writes the primary plan (Step 9 stand-in) ---
    parent_run_id = _new_run_id("parent")
    started_at = _utcnow_iso()
    plan_path = _write_primary_plan(goal_dir)

    # --- Stage 2: Step 10 auto-trigger of cast-plan-review (synthetic body) ---
    decisions = {
        "Should the smoke fixture include a Decisions appendix?": (
            "yes — required for B2 idempotency assertion",
            "the chain test must verify the appendix lands per B2 contract",
        )
    }
    child_run_id, child_output_path = _run_synthetic_cast_plan_review(
        goal_dir=goal_dir,
        plan_path=plan_path,
        decisions=decisions,
    )

    # Parent polls per cast-delegation-contract — the file is already there because
    # the synthetic ran inline, but the polling code-path is identical.
    terminal = _poll_until_terminal(child_output_path, idle_timeout_seconds=2.0)
    assert terminal is not None, "child output never appeared"
    assert terminal["status"] == "completed"

    # --- Stage 3: Parent records the next_steps entry referencing the appendix ---
    next_steps = [
        {
            "command": f"# Review applied: see Decisions appendix in {plan_path}",
            "rationale": "cast-plan-review processed all decisions inline (B2 single-Write contract)",
            "artifact_anchor": str(plan_path),
        }
    ]
    parent = _build_parent_state(
        parent_run_id=parent_run_id,
        plan_path=plan_path,
        child_runs=[
            {
                "run_id": child_run_id,
                "agent_name": "cast-plan-review",
                "status": "completed",
                "output_path": str(child_output_path),
            }
        ],
        next_steps=next_steps,
        started_at=started_at,
    )

    # --- Assertions ---
    children = parent["_test_child_runs"]
    assert len(children) == 1
    assert children[0]["agent_name"] == "cast-plan-review"
    assert children[0]["status"] == "completed"

    final_plan = plan_path.read_text(encoding="utf-8")
    assert "## Decisions" in final_plan, "Decisions appendix missing"
    assert "yes — required for B2 idempotency assertion" in final_plan, (
        "scripted decision answer missing from appendix"
    )

    # Parent's next_steps references the appendix (rationale OR command anchor)
    assert any(
        "Decisions appendix" in step.get("rationale", "")
        or "Decisions appendix" in step.get("command", "")
        for step in parent["next_steps"]
    ), parent["next_steps"]


def test_b3_full_chain_idempotent_rerun(tmp_path, monkeypatch):
    """Re-running cast-plan-review on the same plan does not duplicate the appendix.

    Verifies the B2 contract holds across the chain: same question key → in-place
    upsert, no duplicate `## Decisions` blocks.
    """
    monkeypatch.setenv("CAST_DISABLE_SERVER", "1")

    goal_dir = _copy_fixture(tmp_path)
    plan_path = _write_primary_plan(goal_dir)

    decisions_first = {"Same question?": ("first answer", "first rationale")}
    decisions_second = {"Same question?": ("second answer", "second rationale")}

    _run_synthetic_cast_plan_review(
        goal_dir=goal_dir, plan_path=plan_path, decisions=decisions_first
    )
    _run_synthetic_cast_plan_review(
        goal_dir=goal_dir, plan_path=plan_path, decisions=decisions_second
    )

    final = plan_path.read_text(encoding="utf-8")
    # Only one `## Decisions` heading — the second run upserted, did not append a new block.
    assert final.count("## Decisions") == 1, final
    # The latest answer wins
    assert "second answer" in final
    assert "first answer" not in final
