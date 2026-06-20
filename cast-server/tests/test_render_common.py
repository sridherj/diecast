"""Unit tests for the extracted shared render core (`cast_server.render_common`).

Covers the primitives (sentinel extraction), the verdict base (coercers, canonical_score,
derive_pass over a generic gated-token vocabulary), and the quality-loop skeleton + decide_quality
terminal branches with injected fakes (mirrors the FakeRunner style of test_render_job_service).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CAST_SERVER_DIR = REPO_ROOT / "cast-server"
if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))

from cast_server.render_common import quality_loop as ql  # noqa: E402
from cast_server.render_common import verdict as rv  # noqa: E402
from cast_server.render_common.sentinel import extract_render  # noqa: E402

BEGIN = "<!-- BEGIN RENDER -->"
END = "<!-- END RENDER -->"


# --------------------------------------------------------------------------- #
# extract_render edge cases                                                    #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("raw,expected", [
    (None, None),
    ("", None),
    ("no sentinels here", None),
    (f"{END}<p>x</p>{BEGIN}", None),                      # END before BEGIN
    (f"{BEGIN}{END}", None),                              # empty window
    (f"{BEGIN}\n   \n{END}", None),                       # whitespace-only window
    (f"{BEGIN}\njust prose no markup\n{END}", None),      # no '<' → not a render
    (f"lead\n{BEGIN}\n<p>hi</p>\n{END}\ntrailer", "<p>hi</p>"),
    (f"{BEGIN}\n<div>a</div>\n{END}\n{BEGIN}\n<div>b</div>\n{END}", "<div>a</div>"),  # first pair
])
def test_extract_render_edge_cases(raw, expected):
    assert extract_render(raw) == expected


# --------------------------------------------------------------------------- #
# verdict base: coercers + canonical_score + derive_pass over gated_tokens     #
# --------------------------------------------------------------------------- #
def _verdict(*, can_state_what=True, missing=(), issues=()):
    return rv.BaseVerdict(
        can_state_what=can_state_what, missing=tuple(missing), issues=tuple(issues),
        score=1.0, rework_feedback=(),
    )


def _issue(severity, dimension="visual"):
    return rv.CheckerIssue(dimension=dimension, criterion="c", severity=severity, description="d")


def test_canonical_score_recomputes_from_issue_counts():
    v = _verdict(issues=[_issue("error"), _issue("warning"), _issue("warning")])
    # 1.0 - 0.15*1 - 0.05*2 = 0.75
    assert rv.canonical_score(v) == pytest.approx(0.75)


def test_canonical_score_floored_at_zero():
    v = _verdict(issues=[_issue("error")] * 10)
    assert rv.canonical_score(v) == 0.0


def test_canonical_score_ignores_agent_score():
    v = rv.BaseVerdict(can_state_what=True, missing=(), issues=(_issue("warning"),),
                       score=0.01, rework_feedback=())
    assert rv.canonical_score(v) == pytest.approx(0.95)  # the agent float (0.01) is ignored


GATED = ("pov", "distinctness", "hat_coverage", "visual")


def test_derive_pass_clean():
    assert rv.derive_pass(_verdict(), GATED) is True


def test_derive_pass_false_when_cannot_state():
    assert rv.derive_pass(_verdict(can_state_what=False), GATED) is False


def test_derive_pass_false_on_gated_missing_token():
    assert rv.derive_pass(_verdict(missing=["hat_coverage missing for step 2"]), GATED) is False
    # a non-gated token in missing[] does NOT fail
    assert rv.derive_pass(_verdict(missing=["some unrelated note"]), GATED) is True


def test_derive_pass_false_on_error_issue_but_warnings_ok():
    assert rv.derive_pass(_verdict(issues=[_issue("error")]), GATED) is False
    assert rv.derive_pass(_verdict(issues=[_issue("warning")]), GATED) is True


# --------------------------------------------------------------------------- #
# best_attempt: prefer valid (scored over unscored), then score, then latest   #
# --------------------------------------------------------------------------- #
def _rec(no, *, valid=True, unscored=False, score=None):
    return ql.AttemptRecord(attempt_no=no, html=f"<p>{no}</p>", gate_report=None, what_ok=True,
                            structurally_valid=valid, verdict=None, unscored=unscored,
                            canonical_score=score)


def test_best_attempt_scored_over_unscored():
    chosen = ql.best_attempt([_rec(1, unscored=False, score=0.5), _rec(2, unscored=True, score=None)])
    assert chosen.attempt_no == 1


def test_best_attempt_highest_score_then_latest():
    chosen = ql.best_attempt([_rec(1, score=0.7), _rec(2, score=0.9), _rec(3, score=0.9)])
    assert chosen.attempt_no == 3  # tie on 0.9 → latest


# --------------------------------------------------------------------------- #
# Quality loop + decide_quality terminal branches (injected fake ops)          #
# --------------------------------------------------------------------------- #
@dataclass
class _FakeState:
    how_attempts: int = 0
    consecutive_structural: int = 0

    def __post_init__(self):
        self.attempts_history = []


class _FakeOps(ql.LoopOpsBase):
    """A minimal ops over _FakeState. `how_outputs` is a list consumed per run_how call; an item of
    None is a no-extract attempt. `valid`/`passes` control the gate + checker decisions."""

    def __init__(self, state, *, how_outputs, valid=True, passes=True, unscored=False,
                 max_attempts=15, structural_stop=3):
        super().__init__(state)
        self._how = list(how_outputs)
        self._valid = valid
        self._passes = passes
        self._unscored = unscored
        self._max = max_attempts
        self._stop = structural_stop
        self.published = None  # ("clean"|"flagged"|"fallback", payload)

    @property
    def max_attempts(self):
        return self._max

    @property
    def structural_stop(self):
        return self._stop

    def run_how(self, feedback, score_history):
        self.state.how_attempts += 1
        out = self._how[min(self.state.how_attempts, len(self._how)) - 1] if self._how else None
        self._last = out
        return out

    def gate_html(self):
        pass

    def run_checker(self, html):
        return (None, True) if self._unscored else (object(), False)

    def structurally_valid(self):
        return self._valid

    def what_ok(self):
        return True

    def derive_pass(self, verdict):
        return self._passes

    def canonical_score(self, verdict):
        return 0.9

    def gate_report(self):
        return None

    def rework_feedback(self, verdict):
        return [ql.FeedbackItem("rework", "quality")]

    def score_history(self):
        return "history"

    def maybe_escalate(self, verdict):
        pass

    def heartbeat(self, stage):
        pass

    def compare_and_publish(self, html, *, served_by, human_review, review_reason):
        self.published = ("flagged" if human_review else "clean",
                          {"html": html, "served_by": served_by, "reason": review_reason})
        return True

    def finalize_published(self, record, *, human_review, review_reason, error):
        pass

    def publish_fallback(self, reason):
        self.published = ("fallback", {"reason": reason})


def test_loop_clean_publish_on_valid_passing_attempt():
    ops = _FakeOps(_FakeState(), how_outputs=["<p>ok</p>"], valid=True, passes=True)
    ql.run_quality_loop(ops)
    assert ops.published[0] == "clean"
    assert ops.published[1]["served_by"] == "maker"


def test_decide_no_output_falls_back():
    # All attempts no-extract → no history → fallback (the ONLY fallback trigger).
    ops = _FakeOps(_FakeState(), how_outputs=[None, None, None], structural_stop=3)
    ql.run_quality_loop(ops)
    assert ops.published[0] == "fallback"


def test_decide_valid_nonconvergent_serves_flagged_maker():
    # Valid but never passing → flagged best-attempt, served_by maker, non_convergent.
    ops = _FakeOps(_FakeState(), how_outputs=["<p>x</p>"] * 5, valid=True, passes=False,
                   max_attempts=2, structural_stop=99)
    ql.run_quality_loop(ops)
    assert ops.published[0] == "flagged"
    assert ops.published[1]["served_by"] == "maker"
    assert ops.published[1]["reason"] == "non_convergent"


def test_decide_broken_serves_structural_violation():
    # Zero valid attempts but attempts extracted → structural_violation served-by.
    ops = _FakeOps(_FakeState(), how_outputs=["<p>broken</p>"], valid=False, passes=False,
                   max_attempts=1, structural_stop=99)
    ql.run_quality_loop(ops)
    assert ops.published[0] == "flagged"
    assert ops.published[1]["served_by"] == "structural_violation"
    assert ops.published[1]["reason"] == "structural_violation"


def test_decide_checker_unavailable_when_all_valid_unscored():
    ops = _FakeOps(_FakeState(), how_outputs=["<p>x</p>"], valid=True, passes=False, unscored=True,
                   max_attempts=1, structural_stop=99)
    ql.run_quality_loop(ops)
    assert ops.published[0] == "flagged"
    assert ops.published[1]["reason"] == "checker_unavailable"


def test_run_checker_with_retry_one_retry_then_unscored():
    class _Boom(Exception):
        pass

    calls = {"n": 0}

    class _R:
        def run_agent(self, name, msg, *, timeout_s):
            calls["n"] += 1
            raise _Boom("down")

    v, unscored, raw = ql.run_checker_with_retry(
        _R(), "agent", "prompt", timeout_s=1, parse=lambda r: r,
        run_error=_Boom, parse_error=_Boom)
    assert v is None and unscored is True
    assert calls["n"] == 2  # exactly one retry
