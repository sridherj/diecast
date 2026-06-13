"""Tests for Phase 5b — reconciliation through the v2 gate & honest `.rr-gap` page markers.

5b turns 5a's `emit_change_requests` stub into the FIRST real downstream emitter the roundtrip spec
hard-deferred: a supplied, evidence-validated gap answer becomes a normal `change_request` through
the v2 same-door gate (deduped, provenance-stamped, policy-laned by the now-GATE-ALL global
`WRITEBACK_GATE_POLICY`); the page renders an honest `.rr-gap` marker (question + a FIXED status
string, NEVER the proposed answer) and un-marks naturally once the approved detail lands in canonical
and the next view regenerates.

The gate / policy lanes / conflict predicate / writeback agent / outbox / relay are all consumed
BYTE-UNCHANGED — these tests exercise the *proposer* + the *marker resolver*, never a new writer.
Fake runners + the real service + a real DB (the shared Phase-3 fixtures, imported not forked).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CAST_SERVER_DIR = REPO_ROOT / "cast-server"
if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

import cast_server.config as config  # noqa: E402
from cast_server.db.connection import get_connection  # noqa: E402
from cast_server.requirements_render import maker_gate, parse_requirements  # noqa: E402
from cast_server.services import change_request_service  # noqa: E402
from cast_server.services import render_job_service as svc  # noqa: E402
from cast_server.services import requirement_version_service as version_service  # noqa: E402

# Reuse the proven fixtures/helpers/runner from the Phase-3 + 5a suite (no fork).
from test_render_job_service import (  # noqa: E402
    _CORPUS_TEXT,
    _GAP_MARKED_HTML,
    _GAP_Q,
    _PASS_HTML,
    _gapfill_doc,
    _gapped_what,
    _gaps_state,
    _gf_refused,
    _gf_supplied,
    _good_what,
    _job_state,
    _published_html,
    _request,
    _write_corpus,
    FakeRunner,
    goal,  # noqa: F401  (fixture)
    _reset_module_state,  # noqa: F401  (autouse fixture)
)


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #
_ANSWER_BODY = "The export is sourced from the nightly Postgres replica."


def _crs(g) -> list[dict]:
    conn = get_connection(g.db_path)
    try:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM change_requests ORDER BY id").fetchall()]
    finally:
        conn.close()


def _count_crs(g) -> int:
    return len(_crs(g))


def _set_cr_status(g, cr_id: int, status: str) -> None:
    conn = get_connection(g.db_path)
    try:
        conn.execute("UPDATE change_requests SET status = ? WHERE id = ?", (status, cr_id))
        conn.commit()
    finally:
        conn.close()


def _open_gap(*, gap_id="GAP-01", question=_GAP_Q, block_refs=("FR-001",),
              section_title="Delivery cadence") -> dict:
    return {
        "gap_id": gap_id, "section_title": section_title, "block_refs": list(block_refs),
        "question": question, "why_it_matters": "A reader cannot trust the export without its source.",
    }


def _validated_answer(*, gap_id="GAP-01", body=_ANSWER_BODY, section_hint="Delivery cadence") -> dict:
    """A `supplied` gapfill answer already marked `_validated=True` (as `validate_evidence` would)."""
    return {
        "gap_id": gap_id, "supplied": True, "_validated": True, "answer": body,
        "proposed_change": {"kind": "addition", "section_hint": section_hint, "proposed_body": body},
    }


def _emit(g, open_gaps: list[dict], answers: list[dict], *, row_id=None) -> svc.JobState:
    """Drive ONLY `emit_change_requests` over a JobState with pre-resolved gaps + validated answers
    (the trust boundary already ran) against the real DB — the unit under test for emit/dedupe."""
    st = _job_state(g, FakeRunner(what=[], how=[]))
    if row_id is not None:
        st.row_id = row_id
    st.open_gaps = open_gaps
    st.gapfill_answers = answers
    svc.emit_change_requests(st)
    return st


# --------------------------------------------------------------------------- #
# GATE-ALL flip (the global, owner-resolved policy)                            #
# --------------------------------------------------------------------------- #
def test_gate_all_is_the_default_policy():
    """The goal's resolved global policy: every change-request (gap additions included) is gated."""
    assert config.WRITEBACK_GATE_POLICY == "gate-all"
    # ...and the gate is consumed UNCHANGED — under gate-all every kind lands `proposed`, no FYI.
    assert change_request_service.gate_status("addition", None, "gate-all") == "proposed"
    assert change_request_service.gate_status("modification", "q", "gate-all") == "proposed"


# --------------------------------------------------------------------------- #
# Emit shape + provenance (the FIRST real downstream emitter)                  #
# --------------------------------------------------------------------------- #
def test_emit_creates_one_addition_cr_with_fixed_provenance(goal):
    """A supplied+validated gap → EXACTLY ONE `kind="addition"` CR with the fixed provenance columns,
    `base_version` read at emit time, GATE-ALL intake status `proposed` (no outbox FYI); gaps-state
    `cr-proposed` carries the real cr_id; the answer NEVER reaches the page (FR-016)."""
    version_service.create_snapshot(goal.slug, goal.parsed.source_text,
                                    created_by="seed", db_path=goal.db_path)  # current = v1
    _write_corpus(goal)
    runner = FakeRunner(
        what=[_gapped_what(goal.parsed)],
        how=[_wrap_probe(), _wrap_marked()],
        gapfill=[_gapfill_doc(_gf_supplied())],
    )
    result = _request(goal, runner, wait=True)
    assert result["state"] == "published"

    crs = _crs(goal)
    assert len(crs) == 1
    cr = crs[0]
    assert cr["kind"] == "addition"
    assert cr["target_quote"] is None
    assert cr["base_version"] == 1                       # current requirement_versions.version
    assert cr["author"] == "cast-requirements-gapfill"
    assert cr["author_type"] == "agent"                  # hard-coded at the emitter (no spoof)
    assert cr["origin_phase"] == "render-gapfill"
    assert cr["origin_activity_id"] == str(result["job_id"])
    assert "#gap=" in (cr["origin_artifact_path"] or "")
    assert cr["status"] == "proposed"                    # GATE-ALL lane
    assert _ANSWER_BODY in cr["proposed_body"]           # the validated answer lives on the CR...
    # ...and NO outbox FYI queues under GATE-ALL (a proposed CR notifies nothing).
    assert change_request_service.list_outbox(cr["id"], db_path=goal.db_path) == []

    gs = _gaps_state(goal)
    assert gs["gaps"][0] == {"gap_id": "GAP-01", "status": "cr-proposed", "cr_id": cr["id"]}
    # FR-016 structural: the proposed answer NEVER appears on the page.
    assert "Postgres replica" not in _published_html(goal)


@pytest.mark.parametrize(
    "policy, cr_status, gap_status, expect_fyi, marked",
    [
        ("gate-all", "proposed", "cr-proposed", False, True),
        ("gate-except-additions", "applied", "cr-applied", True, False),
    ],
)
def test_policy_value_drives_the_lane_gate_consumed_unchanged(
    goal, monkeypatch, policy, cr_status, gap_status, expect_fyi, marked
):
    """ONLY the policy value drives the lane (the gate is consumed byte-unchanged). GATE-ALL (the
    goal's live lane) → `proposed`, no FYI, a `.rr-gap` marker on the page. The parametrized
    fast-track mechanism (`gate-except-additions`) still fast-tracks the addition → `applied` + one
    FYI + `cr-applied` (NO marker) — proving the gate plumbing, without resting the goal on it."""
    monkeypatch.setattr(config, "WRITEBACK_GATE_POLICY", policy)
    _write_corpus(goal)
    # A `cr-applied` gap renders NO marker, so the fast-track arm's final HOW must be the CLEAN page
    # (an `.rr-gap` with zero open markers would fail gap-marker correspondence).
    final_how = _wrap_marked() if marked else _wrap_probe()
    runner = FakeRunner(
        what=[_gapped_what(goal.parsed)],
        how=[_wrap_probe(), final_how],
        gapfill=[_gapfill_doc(_gf_supplied())],
    )
    result = _request(goal, runner, wait=True)
    assert result["state"] == "published"

    crs = _crs(goal)
    assert len(crs) == 1 and crs[0]["status"] == cr_status
    outbox = change_request_service.list_outbox(crs[0]["id"], db_path=goal.db_path)
    assert (len(outbox) == 1) is expect_fyi
    assert _gaps_state(goal)["gaps"][0]["status"] == gap_status


# --------------------------------------------------------------------------- #
# Structural fingerprint dedupe (no CR spam)                                   #
# --------------------------------------------------------------------------- #
def test_dedupe_rerender_same_source_creates_no_new_cr(goal):
    """Re-emitting the SAME gap (same fingerprint, a live `proposed` CR) creates ZERO new CRs and
    re-uses the standing cr_id."""
    gaps, answers = [_open_gap()], [_validated_answer()]
    st1 = _emit(goal, gaps, answers)
    first_id = st1.gaps_state[0]["cr_id"]
    st2 = _emit(goal, gaps, answers)
    assert _count_crs(goal) == 1
    assert st2.gaps_state[0] == {"gap_id": "GAP-01", "status": "cr-proposed", "cr_id": first_id}


def test_dedupe_is_stable_across_question_rewording(goal):
    """CQ1: the WHAT agent re-words the question (case / whitespace / trailing punctuation) for the
    SAME block_refs+section → same structural fingerprint → ZERO new CR."""
    answers = [_validated_answer()]
    _emit(goal, [_open_gap(question="What is the upstream data source for the export?")], answers)
    _emit(goal, [_open_gap(question="  what is the upstream data source for the EXPORT???  ")], answers)
    assert _count_crs(goal) == 1


def test_dedupe_rejected_match_maps_to_unfilled_declined(goal):
    """A `rejected` fingerprint match is "asked and answered" — the gap maps to `unfilled-declined`
    (the marker reads "declined"), and NO new CR is proposed (never re-ask the human)."""
    gaps, answers = [_open_gap()], [_validated_answer()]
    st1 = _emit(goal, gaps, answers)
    _set_cr_status(goal, st1.gaps_state[0]["cr_id"], "rejected")
    st2 = _emit(goal, gaps, answers)
    assert _count_crs(goal) == 1
    assert st2.gaps_state[0]["status"] == "unfilled-declined"
    assert st2.open_gap_markers[0]["status"] == "missing — a proposed detail was declined"


def test_dedupe_superseded_match_frees_reproposal(goal):
    """Only a `superseded` match frees re-proposal — a new CR IS created on the next emit."""
    gaps, answers = [_open_gap()], [_validated_answer()]
    st1 = _emit(goal, gaps, answers)
    _set_cr_status(goal, st1.gaps_state[0]["cr_id"], "superseded")
    st2 = _emit(goal, gaps, answers)
    assert _count_crs(goal) == 2
    assert st2.gaps_state[0]["status"] == "cr-proposed"


# --------------------------------------------------------------------------- #
# Convergence lanes                                                            #
# --------------------------------------------------------------------------- #
def test_gated_lane_convergence_marker_clears_on_human_approval(goal):
    """T1 — the FR-016 headline (under GATE-ALL this is the LIVE lane). Emit a gated gap CR (marker
    visible), approve it in-test via the SOLE writer (`apply_for_goal`), re-render → the marker is
    GONE, the detail renders as normal canonical content, and NO new CR is created."""
    version_service.create_snapshot(goal.slug, goal.parsed.source_text,
                                    created_by="seed", db_path=goal.db_path)  # current = v1
    _write_corpus(goal)
    runner = FakeRunner(
        what=[_gapped_what(goal.parsed)],
        how=[_wrap_probe(), _wrap_marked()],
        gapfill=[_gapfill_doc(_gf_supplied())],
    )
    _request(goal, runner, wait=True)
    cr_id = _gaps_state(goal)["gaps"][0]["cr_id"]
    assert _GAP_Q in _published_html(goal)               # the marker is on the page

    # Approve the proposal — the cast-requirements-writeback apply is the ONLY canonical writer.
    applied = change_request_service.apply_for_goal(
        goal.slug, cr_id, goals_dir=goal.goals_dir, actor="human", db_path=goal.db_path)
    assert applied["status"] == "applied"
    updated_source = goal.source_path.read_text(encoding="utf-8")
    assert _ANSWER_BODY in updated_source                # the detail is now canonical

    # Re-render: the WHAT now reads complete source → declares NO gap → no marker, no new CR.
    parsed2 = parse_requirements(updated_source)
    detail_html = _PASS_HTML.replace("</main>", f"<p>{_ANSWER_BODY}</p>\n</main>")
    runner2 = FakeRunner(what=[_good_what(parsed2)], how=[_wrap_probe(), _wrap(detail_html)])
    _request(goal, runner2, wait=True)

    html2 = _published_html(goal)
    assert _GAP_Q not in html2                            # marker GONE (un-marked by regeneration)
    assert "rr-gap" not in html2
    assert _ANSWER_BODY in html2                          # detail renders as normal canonical content
    assert _count_crs(goal) == 1                          # NO new CR


def test_auto_apply_mechanism_applied_match_no_marker_no_reproposal(goal):
    """Auto-apply convergence (mechanism). Once a gap addition is APPLIED (the fast-track lane), its
    fingerprint resolves `cr-applied` → NO marker, and a re-emit never re-proposes: the loop
    terminates (no propose-regen-propose cycle)."""
    gaps, answers = [_open_gap()], [_validated_answer()]
    st1 = _emit(goal, gaps, answers)
    _set_cr_status(goal, st1.gaps_state[0]["cr_id"], "applied")
    st2 = _emit(goal, gaps, answers)
    assert _count_crs(goal) == 1
    assert st2.gaps_state[0]["status"] == "cr-applied"
    assert st2.open_gap_markers == []                    # cr-applied → no marker (detail is canonical)


# --------------------------------------------------------------------------- #
# SC-007 gap-injection — never an unmarked, silently-incomplete render          #
# --------------------------------------------------------------------------- #
def test_sc007_gap_injection_answerable_arm_emits_cr_and_marks(goal):
    """Answerable arm (the detail is present in raw upstream): a gap is declared AND a CR exists, and
    the render carries the marker — never an unmarked, silently-incomplete publish."""
    _write_corpus(goal, text=_CORPUS_TEXT)
    runner = FakeRunner(
        what=[_gapped_what(goal.parsed)],
        how=[_wrap_probe(), _wrap_marked()],
        gapfill=[_gapfill_doc(_gf_supplied())],
    )
    result = _request(goal, runner, wait=True)
    assert result["state"] == "published"
    assert _count_crs(goal) == 1
    assert _gaps_state(goal)["gaps"][0]["status"] == "cr-proposed"
    assert _GAP_Q in _published_html(goal)               # surfaced, never silently dropped


def test_sc007_gap_injection_unanswerable_arm_marks_without_cr(goal):
    """Unanswerable arm (the detail is nowhere in upstream → gapfill REFUSES): NO CR is created, but
    the render still carries an explicit `.rr-gap` marker — the loss is surfaced, never hidden."""
    _write_corpus(goal, text="Unrelated upstream content that never names a data source.\n")
    runner = FakeRunner(
        what=[_gapped_what(goal.parsed)],
        how=[_wrap_probe(), _wrap_marked()],
        gapfill=[_gapfill_doc(_gf_refused())],
    )
    result = _request(goal, runner, wait=True)
    assert result["state"] == "published"
    assert _count_crs(goal) == 0                          # nothing answerable → no CR door reached
    assert _gaps_state(goal)["gaps"][0]["status"] == "unfilled-cannot-supply"
    assert _GAP_Q in _published_html(goal)               # the gap is SURFACED


# --------------------------------------------------------------------------- #
# Survival + carriage on a MARKED render (markers sit between block containers)  #
# --------------------------------------------------------------------------- #
def test_marked_render_passes_check_html_carriage(goal):
    """A render carrying a `.rr-gap` marker still passes check_html — the marker sits BETWEEN block
    containers, so per-block correspondence + verbatim carriage are untouched (gates stay green)."""
    report = maker_gate.check_html(_GAP_MARKED_HTML, goal.parsed, open_gap_questions=[_GAP_Q])
    assert report.passed, report.violations


def test_marked_render_publishes_as_clean_maker_not_flagged(goal):
    """A marked render publishes through the CLEAN maker lane (`served-by: maker`) — a gap marker is
    honest communication, not a structural violation."""
    _write_corpus(goal)
    runner = FakeRunner(
        what=[_gapped_what(goal.parsed)],
        how=[_wrap_probe(), _wrap_marked()],
        gapfill=[_gapfill_doc(_gf_supplied())],
    )
    result = _request(goal, runner, wait=True)
    assert result["state"] == "published"
    html = _published_html(goal)
    assert "<!-- served-by: maker -->" in html            # clean — NOT structural_violation
    assert _GAP_Q in html


# --------------------------------------------------------------------------- #
# Local sentinel wrappers (kept tiny so the gap fixtures read clearly)          #
# --------------------------------------------------------------------------- #
def _wrap(html: str) -> str:
    return f"<!-- BEGIN RENDER -->\n{html}\n<!-- END RENDER -->\n"


def _wrap_probe() -> str:
    """The pre-loop gap-probe HOW render (no trailer harvested here — gaps come from the WHAT doc)."""
    return _wrap(_PASS_HTML)


def _wrap_marked() -> str:
    """The final, gap-aware HOW render carrying the open gap's `.rr-gap` marker."""
    return _wrap(_GAP_MARKED_HTML)
