"""Tests for Phase 4a-2 — the quality-driven rework loop in render_job_service.

The full gated pipeline — ``run_what → gate_what → run_how → gate_html → run_checker →
decide_quality → publish`` — is exercised with the **injected fake runner** (no LLM in default CI;
the checker is just another agent on the runner seam). These tests pin the OWNER OVERRIDE
(decisions-so-far.md lines 104/107): the deterministic page is served ONLY on a literal no-output;
a structurally-broken-but-present attempt is scoreable, servable, and flagged; best-attempt ranking
is PREFER VALID, THEN SCORE.

Fixtures + the proven gate-passing source/HTML + the FakeRunner are shared with
``test_render_job_service`` (imported, not forked) so source and maker markup stay under one set of
test control. A verdict helper (`_verdict`) emits the bare-JSON checker contract.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CAST_SERVER_DIR = REPO_ROOT / "cast-server"
if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))
# The sibling Phase-3 suite is imported for its proven fixtures/helpers/runner (no fork).
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

import cast_server.config as config  # noqa: E402
from cast_server.services import render_job_service as svc  # noqa: E402
from cast_server.services import requirements_render_service  # noqa: E402

# Reuse the proven fixtures/helpers/runner from the Phase-3 suite (no fork).
from test_render_job_service import (  # noqa: E402
    _FLAGGED_HTML,
    _PASS_HTML,
    _good_what,
    _published_html,
    _request,
    _survival_json,  # noqa: F401  (kept for parity / ad-hoc debugging)
    _verdict,
    _wrap,
    FakeRunner,
    goal,  # noqa: F401  (fixture)
    _reset_module_state,  # noqa: F401  (autouse fixture)
)


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #
def _job_dir(g) -> Path:
    return g.jobs_dir / g.slug / g.source_hash[:12]


def _verdict_artifact(g, n: int) -> dict | None:
    p = _job_dir(g) / f"attempt-{n}.verdict.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _make_state(g, runner) -> svc.JobState:
    """Build a JobState wired to the test goal so introspective tests can drive _execute_pipeline
    directly and assert on the in-memory loop state (what_doc retention, budgets, terminal)."""
    row_id = svc._insert_job(g.slug, g.source_hash, g.db_path)
    return svc.JobState(
        key=(g.slug, g.source_hash), goal_slug=g.slug, source_hash=g.source_hash,
        parsed=g.parsed, goal_dir=g.goals_dir / g.slug, goals_dir=g.goals_dir, db_path=g.db_path,
        runner=runner, job_dir=_job_dir(g), row_id=row_id,
    )


def _deterministic_html(g) -> str:
    """A real deterministic render of the same source — the page the OVERRIDE must NOT serve."""
    requirements_render_service.rerender_requirements_html(
        g.slug, goals_dir=g.goals_dir, db_path=g.db_path
    )
    return _published_html(g)


# --------------------------------------------------------------------------- #
# US4 — rework on quality feedback (CQ1: provenance-separated headings)        #
# --------------------------------------------------------------------------- #
def test_rework_path_passes_on_second_attempt_with_verbatim_quality_feedback(goal):
    feedback = "Add a one-line summary of the outcome at the very top of the page."
    runner = FakeRunner(
        what=[_good_what(goal.parsed)],
        how=[_wrap(_PASS_HTML), _wrap(_PASS_HTML)],
        # attempt 1 fails on a quality error (with actionable feedback), attempt 2 is clean.
        checker=[
            _verdict(issues=[{"dimension": "visual", "criterion": "summary-first",
                              "severity": "error", "description": "No summary up top.",
                              "evidence": "first screen"}],
                     rework_feedback=[feedback], score=0.85),
            _verdict(),  # PASS
        ],
    )
    result = _request(goal, runner, wait=True)

    assert result["state"] == "published"
    row = svc.get_job_row(result["job_id"], goal.db_path)
    assert row["status"] == "published" and row["human_review"] == 0  # clean publish, no flag
    html = _published_html(goal)
    assert "<!-- served-by: maker -->" in html and "<!-- human-review:" not in html

    # CQ1: the attempt-2 HOW prompt carries the attempt-1 feedback VERBATIM, under the quality
    # heading. prompts["how"][0] is the 5a gap-probe (not a quality attempt); the loop's two attempts
    # are [1] (no feedback) and [2] (the rework carrying the feedback).
    second_how = runner.prompts["how"][2]
    assert "Quality improvements (guidance)" in second_how
    assert feedback in second_how
    # And the structural heading is NOT spuriously present (attempt 1 was structurally valid).
    assert "Structural fixes (required)" not in second_how

    # Both verdicts are recorded artifacts (replayable post-mortem).
    assert _verdict_artifact(goal, 1) is not None
    assert _verdict_artifact(goal, 2) is not None
    assert runner.how_calls == 3 and runner.checker_calls == 2  # 1 gap-probe + 2 loop attempts


# --------------------------------------------------------------------------- #
# SC-004 — literal no-output → deterministic fallback (checker NEVER invoked)  #
# --------------------------------------------------------------------------- #
def test_literal_no_output_falls_back_and_never_invokes_checker(goal):
    runner = FakeRunner(
        what=[_good_what(goal.parsed)],
        how=[svc.AgentRunError("boom"), svc.AgentRunError("boom"), svc.AgentRunError("boom")],
    )
    result = _request(goal, runner, wait=True)

    assert result["state"] == "fallback"
    row = svc.get_job_row(result["job_id"], goal.db_path)
    assert row["status"] == "fallback" and row["error"]
    assert row["human_review"] == 0  # the fallback page is not flagged
    # The deterministic (LLM-free) page must never be LLM-gated.
    assert runner.checker_calls == 0
    html = _published_html(goal)
    assert "<!-- served-by:" not in html and "AUTO-GENERATED" in html


# --------------------------------------------------------------------------- #
# SC-008 — non-convergence with structurally-VALID attempts                    #
# --------------------------------------------------------------------------- #
def test_non_convergence_publishes_best_scoring_valid_attempt_not_deterministic(goal, monkeypatch):
    monkeypatch.setattr(config, "QUALITY_MAX_ATTEMPTS", 4)
    monkeypatch.setattr(config, "QUALITY_STRUCTURAL_STOP", 9)  # never structural-stop (all valid)

    # All four attempts structurally valid (_PASS_HTML) but the checker never passes (each carries an
    # error). Scores vary; attempt 2 (one error → 0.85) is the highest.
    def err(n):  # n error issues → canonical score 1 - 0.15n
        return _verdict(issues=[{"dimension": "comprehension", "criterion": "c",
                                 "severity": "error", "description": "d", "evidence": "e"}] * n)
    runner = FakeRunner(
        what=[_good_what(goal.parsed)],
        how=[_wrap(_PASS_HTML)] * 4,
        checker=[err(2), err(1), err(2), err(3)],  # scores 0.70, 0.85, 0.70, 0.55
    )
    deterministic = _deterministic_html(goal)  # compute BEFORE the maker publish overwrites it

    result = _request(goal, runner, wait=True)

    assert result["state"] == "published"
    row = svc.get_job_row(result["job_id"], goal.db_path)
    assert row["status"] == "published"
    assert row["human_review"] == 1 and row["review_reason"] == "non_convergent"
    assert row["published_attempt"] == 2 and abs(row["published_score"] - 0.85) < 1e-9

    html = _published_html(goal)
    assert "<!-- served-by: maker -->" in html and "<!-- human-review: 1 -->" in html
    assert "Delivery story" in html              # the maker's own markup was served …
    assert html != deterministic                 # … NOT the deterministic page
    assert runner.how_calls == 5                 # 1 gap-probe + 4 loop attempts to the ceiling


# --------------------------------------------------------------------------- #
# OVERRIDE — broken-only terminal (the deleted-fallback-row replacement)       #
# --------------------------------------------------------------------------- #
def test_zero_valid_attempts_serves_best_broken_not_deterministic(goal, monkeypatch):
    monkeypatch.setattr(config, "QUALITY_STRUCTURAL_STOP", 9)
    monkeypatch.setattr(config, "QUALITY_MAX_ATTEMPTS", 3)

    # Every attempt fails gate_html (id= leak) → zero structurally-valid attempts, but all extracted.
    runner = FakeRunner(
        what=[_good_what(goal.parsed)],
        how=[_wrap(_FLAGGED_HTML)] * 3,
        checker=[_verdict(), _verdict(), _verdict()],  # scored, but structurally broken
    )
    deterministic = _deterministic_html(goal)

    result = _request(goal, runner, wait=True)

    assert result["state"] == "published"
    row = svc.get_job_row(result["job_id"], goal.db_path)
    assert row["status"] == "published" and row["human_review"] == 1
    assert row["review_reason"] == "structural_violation"

    html = _published_html(goal)
    assert "<!-- served-by: structural_violation -->" in html
    assert "<!-- human-review: 1 -->" in html
    assert 'id="leak"' in html          # the degraded maker markup was served …
    assert html != deterministic        # … the deterministic page was NOT served (the OVERRIDE)


# --------------------------------------------------------------------------- #
# OVERRIDE — prefer-valid ranking beats a higher-scoring broken attempt        #
# --------------------------------------------------------------------------- #
def test_prefer_valid_beats_higher_scoring_broken(goal, monkeypatch):
    monkeypatch.setattr(config, "QUALITY_MAX_ATTEMPTS", 4)
    monkeypatch.setattr(config, "QUALITY_STRUCTURAL_STOP", 9)  # alternating; never 3 consecutive

    # Interleave valid (lower score) and broken (higher score) attempts. Prefer-valid must serve a
    # VALID attempt even though a broken one scored higher.
    def err(n):
        return _verdict(issues=[{"dimension": "visual", "criterion": "c",
                                 "severity": "error", "description": "d", "evidence": "e"}] * n)
    runner = FakeRunner(
        what=[_good_what(goal.parsed)],
        # how[0] is consumed by the 5a gap-probe (no trailer); the loop sees the interleave that
        # follows. The probe is never checked, so the checker list maps 1:1 to the loop attempts.
        how=[_wrap(_PASS_HTML),  # gap-probe
             _wrap(_PASS_HTML), _wrap(_FLAGGED_HTML), _wrap(_PASS_HTML), _wrap(_FLAGGED_HTML)],
        checker=[err(2), err(1), err(3), err(0)],  # valid:0.70/0.55  broken:0.85/1.0
    )
    result = _request(goal, runner, wait=True)

    assert result["state"] == "published"
    row = svc.get_job_row(result["job_id"], goal.db_path)
    assert row["human_review"] == 1 and row["review_reason"] == "non_convergent"
    # The best VALID attempt (#1, 0.70) is served, NOT the higher-scoring broken #4 (1.0).
    assert row["published_attempt"] == 1
    html = _published_html(goal)
    assert "<!-- served-by: maker -->" in html
    assert 'id="leak"' not in html  # a broken (id=) attempt was NOT served


# --------------------------------------------------------------------------- #
# Checker-unavailable terminal — valid-but-unscored served, never the plain page
# --------------------------------------------------------------------------- #
def test_checker_unavailable_serves_latest_valid_attempt(goal, monkeypatch):
    monkeypatch.setattr(config, "QUALITY_MAX_ATTEMPTS", 2)
    monkeypatch.setattr(config, "QUALITY_STRUCTURAL_STOP", 9)

    # The checker raises on every call → each attempt is `unscored` after its one retry. The HTML is
    # structurally valid, so the attempts are VALID-but-unscored.
    runner = FakeRunner(
        what=[_good_what(goal.parsed)],
        how=[_wrap(_PASS_HTML), _wrap(_PASS_HTML)],
        checker=[svc.AgentRunError("checker down")],  # repeats → always raises
    )
    deterministic = _deterministic_html(goal)

    result = _request(goal, runner, wait=True)

    assert result["state"] == "published"
    row = svc.get_job_row(result["job_id"], goal.db_path)
    assert row["status"] == "published" and row["human_review"] == 1
    assert row["review_reason"] == "checker_unavailable"
    assert row["published_score"] is None  # unscored

    html = _published_html(goal)
    assert "<!-- served-by: maker -->" in html  # a valid attempt, just never scored
    assert html != deterministic                # never the plain page while output exists
    # Two checker tries per attempt (one retry) × 2 attempts = 4 calls; an unscored artifact each.
    assert runner.checker_calls == 4
    assert _verdict_artifact(goal, 1)["unscored"] is True
    assert _verdict_artifact(goal, 2)["unscored"] is True


# --------------------------------------------------------------------------- #
# WHAT-escalation — 3 consecutive same gated token → re-run run_what before how
# --------------------------------------------------------------------------- #
def test_what_escalation_reruns_what_after_three_consecutive_missing_token(goal, monkeypatch):
    monkeypatch.setattr(config, "QUALITY_MAX_ATTEMPTS", 4)
    monkeypatch.setattr(config, "QUALITY_STRUCTURAL_STOP", 9)
    monkeypatch.setattr(config, "QUALITY_MAX_WHAT_REWORKS", 2)

    # Each verdict names the SAME gated token ("outcome") → after 3 consecutive, escalate run_what.
    miss = _verdict(missing=["the outcome is not stated"], score=0.7)
    runner = FakeRunner(
        what=[_good_what(goal.parsed), _good_what(goal.parsed)],  # initial + escalation re-gen (both good)
        how=[_wrap(_PASS_HTML)] * 4,
        checker=[miss, miss, miss, _verdict()],
    )
    state = _make_state(goal, runner)
    svc._execute_pipeline(state)

    assert state.what_reworks == 1               # exactly one forced WHAT re-run (≤ budget)
    assert runner.what_calls == 2                # initial + the one escalation
    # The escalation run_what fired AFTER the 3rd HOW and BEFORE the 4th (intent-level, not layout).
    third_how = [i for i, a in enumerate(runner.order) if a == "how"][2]
    escalation_what = [i for i, a in enumerate(runner.order) if a == "what"][1]
    assert escalation_what > third_how
    # The escalation prompt carries the gated-token feedback as quality guidance.
    assert "outcome" in runner.prompts["what"][1]


# --------------------------------------------------------------------------- #
# [T1] WHAT-escalation gate-failure → retain prior good WHAT, no fallback      #
# --------------------------------------------------------------------------- #
def test_what_escalation_gate_failure_retains_prior_what(goal, monkeypatch):
    monkeypatch.setattr(config, "QUALITY_MAX_ATTEMPTS", 4)
    monkeypatch.setattr(config, "QUALITY_STRUCTURAL_STOP", 9)
    monkeypatch.setattr(config, "QUALITY_MAX_WHAT_REWORKS", 2)

    good = _good_what(goal.parsed)
    bad = good.replace("cast-requirements-what/v1", "cast-requirements-what/v2")  # fails gate_what
    miss = _verdict(missing=["the outcome is not stated"], score=0.7)
    runner = FakeRunner(
        what=[good, bad],                 # initial good; the escalation re-gen FAILS its gate
        how=[_wrap(_PASS_HTML)] * 4,
        checker=[miss, miss, miss, miss],
    )
    state = _make_state(goal, runner)
    svc._execute_pipeline(state)

    # CQ2/T1: the failed re-gen is discarded, the prior known-good WHAT is RETAINED …
    assert state.what_doc == good
    # … the budget is STILL decremented …
    assert state.what_reworks == 1
    # … HOW reworks resumed against the retained WHAT (the loop kept going past the escalation) …
    assert runner.how_calls == 5  # 1 gap-probe + 4 loop attempts
    # … and NO deterministic fallback fired (a present, structurally-valid attempt history exists).
    assert state.terminal == "published"
    assert state.terminal != "fallback"
    html = _published_html(goal)
    assert "<!-- served-by: maker -->" in html


# --------------------------------------------------------------------------- #
# [T2] Served-artifact flag fidelity — read off the artifact, not the latest row
# --------------------------------------------------------------------------- #
def test_served_artifact_flag_survives_a_fresh_running_regen_row(goal, monkeypatch):
    monkeypatch.setattr(config, "QUALITY_STRUCTURAL_STOP", 9)
    monkeypatch.setattr(config, "QUALITY_MAX_ATTEMPTS", 2)

    # Land a flagged best-attempt (human_review=1) for hash H.
    runner = FakeRunner(
        what=[_good_what(goal.parsed)],
        how=[_wrap(_FLAGGED_HTML), _wrap(_FLAGGED_HTML)],
        checker=[_verdict(), _verdict()],
    )
    result = _request(goal, runner, wait=True)
    assert result["state"] == "published"
    assert svc.get_job_row(result["job_id"], goal.db_path)["human_review"] == 1

    # Now open a NEW `running` regen job row for the SAME hash (its human_review defaults to 0).
    fresh_row = svc._insert_job(goal.slug, goal.source_hash, goal.db_path)
    assert svc.get_job_row(fresh_row, goal.db_path)["human_review"] == 0

    # resolve_render reads the flag off the SERVED artifact's envelope — NOT the fresh running row —
    # so the page the reader is actually looking at keeps its flag (A2/P1).
    resolution = requirements_render_service.resolve_render(
        goal.slug, goals_dir=goal.goals_dir, db_path=goal.db_path
    )
    assert resolution.state == "ready"
    assert resolution.human_review is True


# --------------------------------------------------------------------------- #
# Ceiling + structural-stop config knobs                                        #
# --------------------------------------------------------------------------- #
def test_loop_stops_at_exactly_quality_max_attempts(goal, monkeypatch):
    monkeypatch.setattr(config, "QUALITY_MAX_ATTEMPTS", 5)
    monkeypatch.setattr(config, "QUALITY_STRUCTURAL_STOP", 99)  # never structural-stop

    # Valid attempts that never pass (each carries an error) → the loop runs to the ceiling.
    err = _verdict(issues=[{"dimension": "comprehension", "criterion": "c",
                            "severity": "error", "description": "d", "evidence": "e"}])
    runner = FakeRunner(
        what=[_good_what(goal.parsed)], how=[_wrap(_PASS_HTML)] * 8, checker=[err] * 8,
    )
    result = _request(goal, runner, wait=True)

    assert result["state"] == "published"
    # 1 gap-probe (never checked) + exactly QUALITY_MAX_ATTEMPTS=5 loop attempts.
    assert runner.how_calls == 6 and runner.checker_calls == 5  # stopped at exactly the ceiling


def test_loop_early_stops_after_consecutive_structural_failures(goal, monkeypatch):
    monkeypatch.setattr(config, "QUALITY_STRUCTURAL_STOP", 2)
    monkeypatch.setattr(config, "QUALITY_MAX_ATTEMPTS", 15)

    runner = FakeRunner(
        what=[_good_what(goal.parsed)],
        how=[_wrap(_FLAGGED_HTML)] * 15,
        checker=[_verdict()] * 15,
    )
    result = _request(goal, runner, wait=True)

    assert result["state"] == "published"
    row = svc.get_job_row(result["job_id"], goal.db_path)
    assert row["human_review"] == 1 and row["review_reason"] == "structural_violation"
    # Early-stopped at QUALITY_STRUCTURAL_STOP (2) consecutive structural failures — NOT the ceiling.
    assert runner.how_calls == 3  # 1 gap-probe + 2 loop attempts to the structural-stop
