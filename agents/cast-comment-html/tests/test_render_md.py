"""Tests for cast-comment-html server-side feedback rendering.

The defect these guard against: when a comment quotes text that repeats in the document, the
exported Markdown must show enough surrounding context that a reader knows *which* instance the
comment was on — not just a bare quote under a heading.
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

AGENT_DIR = Path(__file__).resolve().parent.parent
MODULE_PATH = AGENT_DIR / "comment_html.py"

_spec = importlib.util.spec_from_file_location("comment_html", MODULE_PATH)
comment_html = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(comment_html)


def _comment(**kw):
    base = {"id": "c1", "quoted_text": "", "section_hint": "Document", "body": "note", "state": "open", "ts": "2026-06-17 11:00"}
    base.update(kw)
    return base


class TestContextQuote:
    def test_wraps_selection_in_brackets(self):
        c = _comment(quoted_text="Status")
        assert comment_html.context_quote(c) == "⟪Status⟫"

    def test_includes_prefix_and_suffix_with_ellipses(self):
        c = _comment(quoted_text="Status", prefix="Later the ", suffix=": closed section")
        out = comment_html.context_quote(c)
        assert out == "…Later the ⟪Status⟫: closed section…"

    def test_collapses_whitespace_but_keeps_boundary_space(self):
        # internal whitespace runs collapse to one space; the single boundary space is preserved
        c = _comment(quoted_text="the  value", prefix="row\nB |  ", suffix="  | row C")
        out = comment_html.context_quote(c)
        assert out == "…row B | ⟪the value⟫ | row C…"

    def test_no_context_is_just_the_quote(self):
        # back-compat: legacy comments without prefix/suffix still render
        c = _comment(quoted_text="Status")
        assert comment_html.context_quote(c) == "⟪Status⟫"

    def test_long_unique_context_is_truncated_for_display(self):
        # the capture side may store long context (grown to uniqueness); the MD shows only the
        # DISPLAY window nearest the quote — full context still lives in the JSON.
        long_pre = "A" * 200
        long_suf = "B" * 200
        c = _comment(quoted_text="Q", prefix=long_pre, suffix=long_suf)
        out = comment_html.context_quote(c)
        shown_pre = "A" * comment_html._DISPLAY_CTX
        shown_suf = "B" * comment_html._DISPLAY_CTX
        assert out == f"…{shown_pre}⟪Q⟫{shown_suf}…"
        assert "A" * (comment_html._DISPLAY_CTX + 1) not in out  # really truncated


class TestRenderMdDisambiguates:
    def test_two_comments_on_same_repeated_text_are_distinguishable(self):
        # same quoted_text "value", different surrounding context → reader can tell them apart
        comments = [
            _comment(id="a", section_hint="Table", quoted_text="value", prefix="row A | ", suffix=" | row B", body="first cell wrong"),
            _comment(id="b", section_hint="Table", quoted_text="value", prefix="row B | ", suffix=" | row C", body="second cell wrong"),
        ]
        md = comment_html.render_md("grid.html", comments)
        assert "…row A | ⟪value⟫ | row B…" in md
        assert "…row B | ⟪value⟫ | row C…" in md
        # the two anchors are NOT identical strings — that's the whole point
        assert md.count("⟪value⟫") == 2
        assert "first cell wrong" in md and "second cell wrong" in md

    def test_grouped_by_section(self):
        comments = [
            _comment(id="a", section_hint="Intro", quoted_text="x"),
            _comment(id="b", section_hint="Body", quoted_text="y"),
        ]
        md = comment_html.render_md("doc.html", comments)
        assert "## Intro" in md and "## Body" in md

    def test_empty_is_safe(self):
        assert "no comments yet" in comment_html.render_md("doc.html", [])


@pytest.mark.skipif(not Path("/usr/bin/node").exists() and not subprocess.run(["which", "node"], capture_output=True).returncode == 0, reason="node not available")
def test_pure_anchor_js_passes():
    """Run the node anchoring suite as part of the pytest gate."""
    result = subprocess.run(
        ["node", str(AGENT_DIR / "tests" / "test_anchor.js")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"node anchor tests failed:\n{result.stdout}\n{result.stderr}"
