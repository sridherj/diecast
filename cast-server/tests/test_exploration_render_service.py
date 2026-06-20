"""Tests for the exploration WHAT→HOW→checker render-job (exploration_render_service).

Exercised with an injected FakeRunner (no LLM in CI) over a tmp `goals/{slug}/exploration/` 3a
substrate. Mirrors the test_render_job_service.FakeRunner style. Branches under test:

* happy path → clean maker publish at the canonical path with AUTO-GENERATED + source-digest +
  served-by envelope (atomic), all 4 FR-017 criteria passing;
* a `null`/absent always-on hat cell → the step still renders, that hat surfaced as dropped, and the
  checker's criterion-1 judges against the APPLICABLE set;
* literal no-output (HOW emits no sentinels across all attempts) → deterministic fallback,
  status=fallback, served-by deterministic;
* BINDING review #7 — a fully degraded step (placeholder playbook + ZERO hat notes) renders an
  explicit degraded marker, and a checker verdict naming `hat_coverage` in missing[] fails
  derive_pass (no false-pass of criterion-1).
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

from cast_server.services import exploration_render_service as svc  # noqa: E402
from cast_server.exploration_render import verdict as ev  # noqa: E402

BEGIN = "<!-- BEGIN RENDER -->"
END = "<!-- END RENDER -->"

_PLAYBOOK = (
    "# Step playbook\n\nThis is a substantial opinionated playbook for the step describing the one "
    "POV the reader must take away from this exploration step in detail and at length.\n"
)
_RESEARCH = (
    "# Hat research note\n\nThis is a real, substantial research note in this hat's distinct voice "
    "with enough content to clear the placeholder threshold and carry a genuine take.\n"
)
_SUMMARY = "# Summary\n\nThe exploration summary spanning the whole goal in adequate detail here.\n"


# --------------------------------------------------------------------------- #
# A self-contained HOW page carrying every present hat_id (passes gate_html)   #
# --------------------------------------------------------------------------- #
def _how_page(hat_ids) -> str:
    cards = (
        '<section class="rr-step"><h2>Step One</h2>'
        '<p class="rr-pov">The opinionated POV.</p>'
        + "".join(f'<div class="rr-hat" data-hat="{h}"><strong>{h}</strong><p>take</p></div>'
                  for h in hat_ids)
        + "</section>"
    )
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Exploration</title>"
        "<style>.rr-hat{margin:0}</style></head><body><main class='rr-document'>"
        f"<h1>Exploration</h1>{cards}</main></body></html>"
    )


def _wrap(html: str) -> str:
    return f"Here is the render:\n{BEGIN}\n{html}\n{END}\n"


def _what_doc(steps_hats: dict, *, degraded_note: bool = False) -> str:
    """A WHAT doc naming every step + every present hat id + a degraded status when needed."""
    lines = ["---", "contract: cast-exploration-what/v1", "steps:"]
    for slug, hats in steps_hats.items():
        lines.append(f"  - slug: {slug}")
        lines.append(f"    name: {slug.replace('-', ' ').title()}")
        lines.append("    pov_outcome: The one opinionated POV.")
        lines.append("    hats:")
        for hid, status in hats:
            lines.append(f"      - hat_id: {hid}")
            lines.append(f"        take: a distinct {hid} take")
            lines.append(f"        status: {status}")
    if degraded_note:
        lines.append("notes: this step is degraded / dropped")
    lines.append("---")
    lines.append("Communication-intent prose, distinct per hat.")
    return "\n".join(lines)


def _verdict(*, can_state_what=True, missing=None, hat=True, pov=True, distinct=True, visual=True):
    return json.dumps({
        "contract": "cast-exploration-render-checker/v1",
        "can_state_what": can_state_what,
        "missing": missing or [],
        "issues": [],
        "rework_feedback": [],
        "score": 1.0,
        "hat_coverage_ok": hat, "pov_legible": pov, "distinctness_ok": distinct, "visual_ok": visual,
    })


_PASS_VERDICT = _verdict()


class FakeRunner:
    """Inject deterministic WHAT/HOW/CHECKER outputs (one list each, last value repeats); an
    exception instance is raised. Mirrors test_render_job_service.FakeRunner."""

    def __init__(self, *, what, how, checker=None):
        self._what = list(what)
        self._how = list(how)
        self._checker = list(checker) if checker is not None else [_PASS_VERDICT]
        self.what_calls = self.how_calls = self.checker_calls = 0

    def run_agent(self, agent_name, user_msg, *, timeout_s):
        if agent_name == "cast-exploration-what":
            self.what_calls += 1
            return self._resolve(self._what, self.what_calls)
        if agent_name == "cast-exploration-render-checker":
            self.checker_calls += 1
            return self._resolve(self._checker, self.checker_calls)
        self.how_calls += 1
        return self._resolve(self._how, self.how_calls)

    @staticmethod
    def _resolve(seq, n):
        item = seq[min(n, len(seq)) - 1] if seq else ""
        if isinstance(item, BaseException):
            raise item
        return item


# --------------------------------------------------------------------------- #
# Substrate fixture                                                            #
# --------------------------------------------------------------------------- #
@pytest.fixture
def goal(tmp_path, isolated_db, monkeypatch):
    slug = "demo-explore"
    goals_dir = tmp_path / "goals"
    expl = goals_dir / slug / "exploration"
    (expl / "playbooks").mkdir(parents=True)
    (expl / "research").mkdir(parents=True)

    from cast_server.db.connection import get_connection
    conn = get_connection(isolated_db)
    try:
        conn.execute("INSERT OR IGNORE INTO goals (slug, title, folder_path) VALUES (?, ?, ?)",
                     (slug, "Demo Explore", str(goals_dir / slug)))
        conn.commit()
    finally:
        conn.close()

    import cast_server.config as config
    monkeypatch.setattr(config, "RENDER_JOBS_DIR", tmp_path / "render-jobs")

    class _G:
        pass
    g = _G()
    g.slug = slug
    g.goals_dir = goals_dir
    g.db_path = isolated_db
    g.expl = expl
    return g


def _write_step(g, nn, slug, hats, *, playbook=_PLAYBOOK, research=_RESEARCH):
    """Write a step: one playbook + one research cell per hat-id in `hats`."""
    (g.expl / "playbooks" / f"{nn}-{slug}.ai.md").write_text(playbook, encoding="utf-8")
    for hid in hats:
        (g.expl / "research" / f"{nn}-{slug}-{hid}.ai.md").write_text(research, encoding="utf-8")
    (g.expl / "summary.ai.md").write_text(_SUMMARY, encoding="utf-8")


def _published(g) -> str:
    return (g.expl / "exploration.html").read_text(encoding="utf-8")


def _request(g, runner):
    return svc.request_exploration_render(g.slug, runner=runner, goals_dir=g.goals_dir,
                                          db_path=g.db_path, wait=True)


# --------------------------------------------------------------------------- #
# Happy path                                                                   #
# --------------------------------------------------------------------------- #
def test_happy_path_publishes_clean_maker_render(goal):
    hats = ["contrarian", "first-principles", "90-10"]
    _write_step(goal, "01", "step-one", hats)
    runner = FakeRunner(
        what=[_what_doc({"step-one": [(h, "present") for h in hats]})],
        how=[_wrap(_how_page(hats))],
    )
    result = _request(goal, runner)

    assert result["state"] == "published"
    row = svc.get_job_row(result["job_id"], goal.db_path)
    assert row["status"] == "published" and row["human_review"] == 0

    html = _published(goal)
    assert "<!-- AUTO-GENERATED:" in html
    assert f"<!-- source-digest: {result['source_digest']} -->" in html
    assert "<!-- served-by: maker -->" in html
    assert html.count("<!-- AUTO-GENERATED:") == 1  # exactly one envelope (atomic, no double-wrap)
    assert runner.what_calls == 1 and runner.how_calls == 1 and runner.checker_calls == 1


def test_missing_exploration_tree_returns_missing(goal):
    import shutil
    shutil.rmtree(goal.expl)
    assert _request(goal, FakeRunner(what=[], how=[]))["state"] == "missing"


# --------------------------------------------------------------------------- #
# A null/absent always-on hat cell still renders the step (hat surfaced dropped)#
# --------------------------------------------------------------------------- #
def test_absent_always_on_hat_still_renders_step_dropped(goal):
    # Only 2 of the 3 always-on hats have a research cell → 90-10 is an absent (dropped) cell.
    present = ["contrarian", "first-principles"]
    _write_step(goal, "01", "step-one", present)

    steps, hat_matrix, _, _ = svc.load_exploration_corpus(goal.goals_dir / goal.slug)
    # The corpus marks 90-10 applicable (always-on) but dropped (no present cell).
    assert "90-10" in hat_matrix["step-one"]
    step = steps[0]
    nine_ten = next(h for h in step["hat_notes"] if h["hat_id"] == "90-10")
    assert nine_ten["status"] == "dropped"

    hats_what = [(h, "present") for h in present] + [("90-10", "dropped")]
    # The page surfaces the dropped hat explicitly + the present hats' containers.
    page = _how_page(present).replace(
        "</section>",
        '<div class="rr-hat rr-dropped" data-hat="90-10">90-10 attempted, dropped</div></section>')
    runner = FakeRunner(
        what=[_what_doc({"step-one": hats_what}, degraded_note=True)],
        how=[_wrap(page)],
    )
    result = _request(goal, runner)
    assert result["state"] == "published"
    html = _published(goal)
    assert "90-10" in html and "dropped" in html.lower()  # the dropped hat is surfaced, not omitted


# --------------------------------------------------------------------------- #
# Literal no-output → deterministic fallback                                   #
# --------------------------------------------------------------------------- #
def test_no_sentinels_across_all_attempts_serves_deterministic_fallback(goal):
    hats = ["contrarian", "first-principles", "90-10"]
    _write_step(goal, "01", "step-one", hats)
    runner = FakeRunner(
        what=[_what_doc({"step-one": [(h, "present") for h in hats]})],
        how=["no sentinels here", "still none", "and again"],
    )
    result = _request(goal, runner)

    assert result["state"] == "fallback"
    row = svc.get_job_row(result["job_id"], goal.db_path)
    assert row["status"] == "fallback" and row["error"]

    html = _published(goal)
    assert "<!-- served-by: deterministic -->" in html
    assert "Step One" in html  # the deterministic md-to-HTML still renders the step


def test_what_crash_falls_back_without_running_how(goal):
    _write_step(goal, "01", "step-one", ["contrarian", "first-principles", "90-10"])
    runner = FakeRunner(what=[svc.AgentRunError("what down")], how=[_wrap(_how_page(["contrarian"]))])
    result = _request(goal, runner)
    assert result["state"] == "fallback"
    assert runner.how_calls == 0  # no WHAT doc → HOW never runs


# --------------------------------------------------------------------------- #
# BINDING review #7 — a FULLY degraded step (placeholder playbook + 0 hats)    #
# --------------------------------------------------------------------------- #
def test_fully_degraded_step_renders_marker_and_checker_does_not_false_pass(goal):
    """A step with a placeholder playbook AND zero hat notes is DEGRADED. The page renders an
    explicit degraded marker, AND a checker verdict honestly naming `hat_coverage` in missing[]
    fails derive_pass (criterion-1 is judged against the applicable set — no false-pass)."""
    # The degraded step: placeholder playbook, NO research cells written.
    (goal.expl / "playbooks" / "01-degraded-step.ai.md").write_text("(placeholder)", encoding="utf-8")
    (goal.expl / "summary.ai.md").write_text(_SUMMARY, encoding="utf-8")

    steps, hat_matrix, _, _ = svc.load_exploration_corpus(goal.goals_dir / goal.slug)
    step = steps[0]
    # (a) the corpus marks the step degraded, and the always-on hats are present-but-dropped cells.
    assert step["degraded"] is True
    assert all(h["status"] == "dropped" for h in step["hat_notes"])
    assert set(hat_matrix["degraded-step"]) == set(ev.GATED_TOKENS) - {"pov", "distinctness", "visual"} \
        or set(hat_matrix["degraded-step"]) == {"contrarian", "first-principles", "90-10"}

    # (b) a checker verdict honestly reporting the degradation (hat_coverage missing) → derive_pass False.
    honest = ev.parse_exploration_verdict(_verdict(missing=["hat_coverage for degraded-step"], hat=False))
    assert ev.derive_pass(honest) is False  # the checker does NOT false-pass criterion-1

    # The page (HOW) renders the degraded marker; the WHAT doc carries the degraded status. The HOW
    # attempt has no present hats to require containers, so gate_html passes structurally; the checker
    # honestly fails it → flagged best-attempt (surface, don't suppress), NEVER a silent clean pass.
    degraded_page = _how_page([]).replace(
        "</main>",
        '<div class="rr-dropped">degraded-step: this step is degraded (attempted, dropped)</div></main>')
    runner = FakeRunner(
        what=[_what_doc({"degraded-step": [("contrarian", "dropped"),
                                           ("first-principles", "dropped"),
                                           ("90-10", "dropped")]}, degraded_note=True)],
        how=[_wrap(degraded_page)] * 5,
        checker=[_verdict(missing=["hat_coverage for degraded-step"], hat=False)],
    )
    result = _request(goal, runner)

    assert result["state"] == "published"  # served, but flagged (surface, don't suppress)
    row = svc.get_job_row(result["job_id"], goal.db_path)
    assert row["human_review"] == 1  # the honest checker fail flags it — no false clean publish
    html = _published(goal)
    assert "degraded-step" in html and "degraded" in html.lower()  # the marker is rendered
    assert "<!-- served-by: maker -->" in html or "<!-- served-by: structural_violation -->" in html


# --------------------------------------------------------------------------- #
# Verdict / corpus units                                                       #
# --------------------------------------------------------------------------- #
def test_derive_pass_requires_all_four_criteria(goal):
    assert ev.derive_pass(ev.parse_exploration_verdict(_verdict())) is True
    for kw in ("hat", "pov", "distinct", "visual"):
        v = ev.parse_exploration_verdict(_verdict(**{kw: False}))
        assert ev.derive_pass(v) is False, f"criterion {kw} must gate"


def test_source_digest_stable_and_changes_with_content(goal):
    _write_step(goal, "01", "step-one", ["contrarian"])
    _, _, _, d1 = svc.load_exploration_corpus(goal.goals_dir / goal.slug)
    _, _, _, d2 = svc.load_exploration_corpus(goal.goals_dir / goal.slug)
    assert d1 == d2  # deterministic
    (goal.expl / "playbooks" / "01-step-one.ai.md").write_text(_PLAYBOOK + "\nextra", encoding="utf-8")
    _, _, _, d3 = svc.load_exploration_corpus(goal.goals_dir / goal.slug)
    assert d3 != d1  # content change moves the digest
