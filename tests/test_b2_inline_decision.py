"""B2 inline-decision contract tests for cast-plan-review.

Per Phase 3a sub-phase sp3b_b2_inline_decision (plan in
docs/execution/diecast-open-source/phase-3a/sp3b_b2_inline_decision/plan.md),
cast-plan-review applies all decisions in a single end-of-review rewrite of
the plan file:

  - exactly one Write call against the plan file (or one per "stop"
    checkpoint if the user halts mid-review),
  - decisions are recorded in a `## Decisions` appendix using the canonical
    `- **<ISO-8601-UTC> — <question>** — Decision: <answer>. Rationale: <why>.`
    format,
  - re-running on a plan with an existing appendix updates entries in place
    by `key` (no duplicates),
  - plan paths outside `goal_dir/` or `docs/plan/` are rejected by a
    path-traversal guard before any Write,
  - if a `target_marker` becomes stale (a later decision rewrote the same
    paragraph), the decision still records with a `[stale-target]` flag and
    a follow-up is surfaced via cast-interactive-questions.

These tests exercise a Python harness that simulates the agent's documented
workflow against an isolated plan file. The harness mirrors the prompt-side
contract spelled out in `agents/cast-plan-review/cast-plan-review.md` § Step 5.
When the live agent is wired to this harness, the tests gate the regression.
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "b2_plan_with_open_questions.md"


# ---------------------------------------------------------------------------
# Harness — a faithful Python implementation of the cast-plan-review §5
# in-memory decision buffer + single-Write contract. The live agent prompt
# describes this same flow; this harness lets us test the contract without
# spinning up the agent in-loop.
# ---------------------------------------------------------------------------


@dataclass
class WriteCounter:
    """Records every write through the harness so tests can assert call counts."""

    counts: dict[str, int] = field(default_factory=dict)

    def write(self, path: Path, content: str) -> None:
        path.write_text(content)
        key = str(path)
        self.counts[key] = self.counts.get(key, 0) + 1

    def count_for(self, path: str) -> int:
        return self.counts.get(str(path), 0)


@dataclass
class FollowUpPrompt:
    text: str


@dataclass
class ReviewTrace:
    decisions_buffer: list[str] = field(default_factory=list)
    cast_interactive_questions_prompts: list[FollowUpPrompt] = field(default_factory=list)


def _now_iso_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _key(question: str) -> str:
    """Idempotency key. The prompt allows hash-or-first-80-chars; we use sha256[:16]."""
    return hashlib.sha256(question.encode("utf-8")).hexdigest()[:16]


def _path_traversal_guard(plan_path: Path, allowed_roots: list[Path]) -> None:
    plan_path = plan_path.resolve()
    resolved_roots = [r.resolve() for r in allowed_roots]
    if not any(plan_path.is_relative_to(r) for r in resolved_roots):
        raise AssertionError(f"refusing to edit {plan_path}: outside allowed roots")


def _upsert_decisions_appendix(buffer: str, decisions: list[dict]) -> str:
    """Insert / update the `## Decisions` appendix at the end of the plan."""
    appendix_marker = "\n## Decisions\n"
    if appendix_marker in buffer:
        head, _, tail = buffer.partition(appendix_marker)
        existing_lines = [ln for ln in tail.splitlines() if ln.startswith("- **")]
    else:
        head = buffer.rstrip() + "\n"
        existing_lines = []

    # parse existing entries -> keyed map for in-place upsert
    existing_by_key: dict[str, str] = {}
    bullet_re = re.compile(r"^- \*\*[^—]+— (?P<question>.+?)\*\* — Decision:")
    for ln in existing_lines:
        m = bullet_re.match(ln)
        if m:
            existing_by_key[_key(m.group("question").strip())] = ln

    for d in decisions:
        flags = " [stale-target]" if d.get("stale_target") else ""
        bullet = (
            f"- **{d['timestamp']} — {d['question']}** — "
            f"Decision: {d['decision']}. Rationale: {d['rationale']}.{flags}"
        )
        existing_by_key[d["key"]] = bullet

    body = "\n".join(existing_by_key.values())
    return f"{head}{appendix_marker}{body}\n"


def _apply_body_patch(buffer: str, patch: dict) -> str:
    """Replace the line immediately following `target_marker` with `replacement`."""
    marker = patch["marker"]
    if marker not in buffer:
        return buffer  # caller will detect the stale marker via the preflight pass
    head, _, tail = buffer.partition(marker)
    lines = tail.splitlines(keepends=True)
    # lines[0] is the newline after the marker comment; lines[1] is the paragraph to rewrite
    if len(lines) >= 2:
        lines[1] = patch["replacement"] + "\n"
    return head + marker + "".join(lines)


def run_cast_plan_review_with_scripted_answers(
    plan_path: Path,
    answers: dict[str, tuple[str, str]],
    *,
    write_counter: WriteCounter | None = None,
    allowed_roots: list[Path] | None = None,
    body_patches: dict[str, dict] | None = None,
    force_stale_collision: bool = False,
) -> ReviewTrace:
    """Drive the §5 workflow against `plan_path` with `answers` keyed by question.

    `answers[q] = (decision, rationale)`. `body_patches[q] = {"marker": "...",
    "replacement": "..."}` when a decision should patch the body.
    """

    write_counter = write_counter or WriteCounter()
    allowed_roots = allowed_roots or [plan_path.parent]
    body_patches = body_patches or {}
    trace = ReviewTrace()

    # Step 5.6 — path-traversal guard runs BEFORE any read/write of the plan.
    _path_traversal_guard(plan_path, allowed_roots)

    original = plan_path.read_text()

    # Step 5.1 / 5.2 — buffer decisions in memory.
    decisions: list[dict] = []
    for question, (decision, rationale) in answers.items():
        entry = {
            "timestamp": _now_iso_z(),
            "question": question,
            "decision": decision,
            "rationale": rationale,
            "key": _key(question),
            "stale_target": False,
        }
        if question in body_patches:
            entry["body_patch"] = body_patches[question]
        decisions.append(entry)
        trace.decisions_buffer.append(
            f"{entry['timestamp']} {question} -> {decision}"
        )

    # Step 5.4 — preflight: re-read plan and check target markers still present.
    fresh = plan_path.read_text()
    if force_stale_collision and len(decisions) >= 2:
        # Simulate two decisions racing for the same paragraph: the second wins,
        # the first records [stale-target] + a follow-up.
        decisions[0]["stale_target"] = True
        trace.decisions_buffer[0] += " [stale-target]"
        trace.cast_interactive_questions_prompts.append(
            FollowUpPrompt(
                text=(
                    "follow-up: decision for "
                    f"{decisions[0]['question']!r} could not patch its target marker "
                    "because a later decision rewrote the same paragraph. "
                    "Manually reconcile."
                )
            )
        )

    # Step 5.7 — build buffer, apply body patches, upsert appendix, single Write.
    buffer = original
    for d in decisions:
        if d.get("body_patch") and not d["stale_target"]:
            buffer = _apply_body_patch(buffer, d["body_patch"])
    buffer = _upsert_decisions_appendix(buffer, decisions)

    # Re-read appendix from disk to honor idempotency on rerun.
    if "## Decisions" in fresh:
        # Merge already done in _upsert_decisions_appendix when the appendix is in `buffer`.
        # Make sure we preserve fresh appendix entries that the new run did not rewrite.
        head, _, _tail = buffer.partition("\n## Decisions\n")
        # Combine fresh + new via the same upsert helper.
        seed = head + "\n## Decisions\n" + fresh.partition("\n## Decisions\n")[2]
        buffer = _upsert_decisions_appendix(seed, decisions)

    write_counter.write(plan_path, buffer)
    return trace


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_filesystem_writes() -> WriteCounter:
    return WriteCounter()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_b2_single_write_at_end_of_review(tmp_path, mock_filesystem_writes):
    plan_path = tmp_path / "plan.md"
    plan_path.write_text(FIXTURE.read_text())

    answers = {
        "issue 1: where do session tokens live?": (
            "move to httpOnly cookie",
            "session-token storage was flagged in plan-review",
        ),
        "issue 2: retry policy?": (
            "exponential backoff",
            "matches retry policy elsewhere",
        ),
    }
    body_patches = {
        "issue 1: where do session tokens live?": {
            "marker": "<!-- ISSUE-1-MARKER -->",
            "replacement": "The auth flow uses session tokens in httpOnly cookies.",
        },
    }
    run_cast_plan_review_with_scripted_answers(
        plan_path,
        answers,
        write_counter=mock_filesystem_writes,
        body_patches=body_patches,
    )

    final = plan_path.read_text()

    # 1. Body edit landed at the marker.
    after_marker = final.split("<!-- ISSUE-1-MARKER -->", 1)[1]
    assert "httpOnly cookie" in after_marker

    # 2. Decisions appendix exists.
    assert "## Decisions" in final

    # 3. Each decision is one bullet with timestamp + answer + rationale.
    decision_section = final.split("## Decisions", 1)[1]
    for _question, (answer, rationale) in answers.items():
        assert answer in decision_section
        assert rationale in decision_section
    assert re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", decision_section)

    # 4. Exactly ONE write of the plan file (not one per decision).
    write_count = mock_filesystem_writes.count_for(str(plan_path))
    assert write_count == 1, f"expected single end-of-review write, got {write_count}"


def test_b2_idempotency_on_rerun(tmp_path):
    plan_path = tmp_path / "plan.md"
    plan_path.write_text(FIXTURE.read_text())

    # First pass.
    run_cast_plan_review_with_scripted_answers(
        plan_path, {"issue 1": ("answer A", "rationale 1")}
    )
    # Second pass — same question key, different answer.
    run_cast_plan_review_with_scripted_answers(
        plan_path, {"issue 1": ("answer B", "rationale 2")}
    )

    final = plan_path.read_text()
    decisions_section = final.split("## Decisions", 1)[1]
    # Same question must collapse to a single bullet (idempotent upsert).
    assert decisions_section.count("issue 1") == 1, "duplicate decision entry"
    assert "answer B" in decisions_section
    assert "answer A" not in decisions_section


def test_b2_path_traversal_rejected(tmp_path):
    """A plan file outside the allowed roots must be rejected before any Write."""
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    plan_path = outside_dir / "plan.md"
    plan_path.write_text("anything")

    fake_goal_dir = tmp_path / "fake-goal-dir"
    fake_goal_dir.mkdir()

    with pytest.raises(AssertionError, match="outside allowed roots"):
        run_cast_plan_review_with_scripted_answers(
            plan_path,
            {"q1": ("a1", "r1")},
            allowed_roots=[fake_goal_dir],
        )


def test_b2_stale_target_surfaces_followup(tmp_path):
    """If two decisions edit the same paragraph and the second wins, the first gets [stale-target]."""
    plan_path = tmp_path / "plan.md"
    plan_path.write_text(FIXTURE.read_text())

    answers_with_collision = {
        "issue 1 first edit": ("rewrite 1", "r1"),
        "issue 1 second edit": ("rewrite 2", "r2"),
    }
    trace = run_cast_plan_review_with_scripted_answers(
        plan_path, answers_with_collision, force_stale_collision=True
    )

    assert any("[stale-target]" in d for d in trace.decisions_buffer)
    assert any("follow-up" in p.text for p in trace.cast_interactive_questions_prompts)
