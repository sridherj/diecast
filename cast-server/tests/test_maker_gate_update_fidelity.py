"""Unit tests for the refine-req-v3 sp3b gate changes (the flip + UPDATE splice).

Covers, against the PURE functions (no DB, no LLM, no subprocess):

- ``block_splice`` — fragment parsing, raw-HTML unit segmentation, and the splice (keep unchanged
  bytes verbatim, swap modified, drop removed, insert added);
- ``check_update_fidelity`` — raw-byte identity of unchanged unit containers (the splice-construction
  guarantee, 1a verdict FAIL → deterministic-splice);
- ``check_comment_survival`` render-space reorientation — unchanged-block miss = structural violation,
  changed-block miss = expected, ref-less / cross-boundary miss = badge-only;
- the ``check_html`` re-scope (paraphrase allowed) is in ``test_maker_gate.py``.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CAST_SERVER_DIR = REPO_ROOT / "cast-server"
if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))

from cast_server.requirements_render import block_splice as bs  # noqa: E402
from cast_server.requirements_render import parse_requirements  # noqa: E402
from cast_server.requirements_render.maker_gate import (  # noqa: E402
    check_comment_survival,
    check_update_fidelity,
)

# A small, gated-shape prior render: three labeled units (US1 section, FR-001 li, SC-001 li).
_PRIOR = """\
<!doctype html><html><head><meta charset="utf-8"></head>
<body data-goal-slug="demo">
<main class="rr-document">
<h2>Stories</h2>
<section class="rr-unit"><h3>US1 — cadence</h3><p>As a user I want a nightly export.</p></section>
<h2>Requirements</h2>
<ul>
<li><strong>FR-001</strong> The system must export nightly.</li>
<li><strong>FR-002</strong> The system must alert on failure.</li>
</ul>
<h2>Criteria</h2>
<ul>
<li><strong>SC-001</strong> Exports complete within ten minutes.</li>
</ul>
</main></body></html>
"""


def _frag(ref: str, inner: str) -> str:
    return f'<!-- RR-FRAGMENT ref="{ref}" -->\n{inner}\n<!-- /RR-FRAGMENT -->'


# ======================================================================================
# block_splice.parse_fragments
# ======================================================================================
def test_parse_fragments_keys_by_ref():
    out = bs.parse_fragments(
        _frag("FR-001", "<li><strong>FR-001</strong> new.</li>")
        + "\n"
        + _frag("SC-002", "<li><strong>SC-002</strong> added.</li>")
    )
    assert set(out) == {"FR-001", "SC-002"}
    assert "new." in out["FR-001"] and "added." in out["SC-002"]


def test_parse_fragments_empty_on_no_delimiters():
    assert bs.parse_fragments("<li><strong>FR-001</strong> a full page, no fragments.</li>") == {}


def test_parse_fragments_ignores_unkeyed_fragment():
    # A delimiter with no parseable ref is dropped (the gate then sees a missing changed-block).
    assert bs.parse_fragments("<!-- RR-FRAGMENT -->\n<li>x</li>\n<!-- /RR-FRAGMENT -->") == {}


# ======================================================================================
# block_splice.segment_units — byte-faithful raw-HTML spans
# ======================================================================================
def test_segment_units_extracts_verbatim_spans_keyed_by_ref():
    segs = bs.segment_units(_PRIOR)
    by_ref = {s.ref: s for s in segs}
    assert set(by_ref) >= {"US1", "FR-001", "FR-002", "SC-001"}
    # Each segment's html is exactly the prior bytes at its span (byte-faithful slice).
    for s in segs:
        assert _PRIOR[s.start:s.end] == s.html
    assert by_ref["FR-001"].html == "<li><strong>FR-001</strong> The system must export nightly.</li>"


# ======================================================================================
# block_splice.splice_update — the assembler
# ======================================================================================
def test_splice_modify_keeps_unchanged_verbatim_swaps_changed():
    frags = bs.parse_fragments(_frag("FR-001", "<li><strong>FR-001</strong> CHANGED nightly export.</li>"))
    res = bs.splice_update(
        _PRIOR, frags,
        modified_refs=frozenset({"FR-001"}), added_refs=frozenset(), removed_refs=frozenset(),
    )
    assert res.missing_refs == () and res.spliced_refs == ("FR-001",)
    assert "CHANGED nightly export" in res.html
    assert "The system must export nightly." not in res.html        # the modified bytes are gone
    # Unchanged units kept byte-identical.
    assert "<li><strong>FR-002</strong> The system must alert on failure.</li>" in res.html
    assert "<li><strong>SC-001</strong> Exports complete within ten minutes.</li>" in res.html


def test_splice_remove_drops_unit_and_add_inserts_by_kind():
    frags = bs.parse_fragments(_frag("SC-002", "<li><strong>SC-002</strong> a fresh criterion.</li>"))
    res = bs.splice_update(
        _PRIOR, frags,
        modified_refs=frozenset(), added_refs=frozenset({"SC-002"}), removed_refs=frozenset({"FR-002"}),
    )
    assert "alert on failure" not in res.html                       # FR-002 dropped
    assert "a fresh criterion" in res.html                          # SC-002 added
    assert res.html.index("SC-002") > res.html.index("SC-001")      # after the last SC unit
    assert "The system must export nightly." in res.html           # FR-001 untouched


def test_splice_missing_fragment_for_modified_ref_is_reported():
    res = bs.splice_update(
        _PRIOR, {},  # HOW emitted nothing
        modified_refs=frozenset({"FR-001"}), added_refs=frozenset(), removed_refs=frozenset(),
    )
    assert "FR-001" in res.missing_refs
    # The unit keeps its prior bytes (the gate surfaces the miss; never a silent stale publish).
    assert "The system must export nightly." in res.html


# ======================================================================================
# check_update_fidelity — raw-byte identity of unchanged containers
# ======================================================================================
def test_fidelity_passes_on_a_correct_splice():
    frags = bs.parse_fragments(_frag("FR-001", "<li><strong>FR-001</strong> reworded export.</li>"))
    res = bs.splice_update(
        _PRIOR, frags,
        modified_refs=frozenset({"FR-001"}), added_refs=frozenset(), removed_refs=frozenset(),
    )
    # FR-002, SC-001, US1 are unchanged → byte-identical by construction.
    rep = check_update_fidelity(res.html, _PRIOR, ["US1", "FR-002", "SC-001"])
    assert rep.passed


def test_fidelity_flags_a_reworded_unchanged_container():
    # Simulate a BAD splice: an unchanged unit's bytes drifted (the 1a paraphrase failure mode).
    tampered = _PRIOR.replace(
        "<li><strong>SC-001</strong> Exports complete within ten minutes.</li>",
        "<li><strong>SC-001</strong> Exports finish in under ten minutes.</li>",
    )
    rep = check_update_fidelity(tampered, _PRIOR, ["SC-001"])
    assert not rep.passed
    assert any("SC-001" in v and "byte-identical" in v for v in rep.violations)


def test_fidelity_flags_a_missing_unchanged_container():
    dropped = _PRIOR.replace(
        "<li><strong>SC-001</strong> Exports complete within ten minutes.</li>", ""
    )
    rep = check_update_fidelity(dropped, _PRIOR, ["SC-001"])
    assert not rep.passed
    assert any("SC-001" in v and "missing" in v for v in rep.violations)


def test_fidelity_skips_a_ref_absent_from_the_prior_render():
    # A ref that was never a labeled unit on the prior render → nothing to hold identical.
    assert check_update_fidelity(_PRIOR, _PRIOR, ["FR-999"]).passed


# ======================================================================================
# check_comment_survival — render-space reorientation
# ======================================================================================
_SRC = """\
# Demo
## Functional Requirements
| ID | Requirement | Source |
|---|---|---|
| FR-001 | The system must export nightly. | US1 |
| FR-002 | The system must alert on failure. | US1 |
## Success Criteria
| ID | Criterion | Measure |
|---|---|---|
| SC-001 | Exports complete within ten minutes. | timed |
"""
_PARSED = parse_requirements(_SRC)


def _rc(cid, quote, block_ref):
    return {"id": cid, "quoted_text": quote, "block_ref": block_ref, "anchor_space": "render"}


def test_survival_render_unchanged_block_miss_is_structural_violation():
    rep = check_comment_survival(
        _PRIOR, _PARSED,
        [_rc(1, "text that is not on the render", "SC-001")],
        changed_refs=frozenset({"FR-001"}),   # SC-001 NOT changed → unchanged-block miss
    )
    assert not rep["passed"]
    assert 1 in rep["unplaced"] and rep["expected_misses"] == []
    assert any("SC-001" in v and "unchanged block" in v for v in rep["violations"])


def test_survival_render_changed_block_miss_is_expected_not_violation():
    rep = check_comment_survival(
        _PRIOR, _PARSED,
        [_rc(2, "text no longer on the render", "FR-001")],
        changed_refs=frozenset({"FR-001"}),   # FR-001 changed → expected miss, route to reanchor
    )
    assert rep["passed"]                       # an expected miss never flips passed
    assert rep["expected_misses"] == [2] and 2 in rep["unplaced"]
    assert rep["violations"] == []


def test_survival_render_in_block_places():
    rep = check_comment_survival(
        _PRIOR, _PARSED,
        [_rc(3, "The system must export nightly.", "FR-001")],
        changed_refs=frozenset(),
    )
    assert rep["passed"] and rep["placed"] == [3]


def test_survival_render_refless_miss_is_badge_only_not_violation():
    # block_ref=None (cross-boundary / displaced render-space comment): a miss is best-effort only.
    rep = check_comment_survival(
        _PRIOR, _PARSED,
        [{"id": 4, "quoted_text": "absent quote", "block_ref": None, "anchor_space": "render"}],
        changed_refs=frozenset(),
    )
    assert rep["passed"] and 4 in rep["unplaced"]
    assert rep["violations"] == [] and rep["expected_misses"] == []


def test_survival_legacy_source_space_unchanged_behaviour():
    # A comment with no anchor_space='render' keeps the legacy source-space classification.
    rep = check_comment_survival(
        _PRIOR, _PARSED,
        [{"id": 5, "quoted_text": "The system must export nightly."}],
    )
    assert rep["passed"] and rep["placed"] == [5]
