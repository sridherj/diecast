"""Unit tests for the sp4 HOW-hardening gate additions (refine-req-v3 sub-phase 4).

Two root-cause fixes, both pinned here:

1. **Zero-ref contract (pilot_poc invented ids).** A source with NO canonical US/FR/SC ids is a
   ref-less doc: `check_what_doc` accepts it cleanly (sections with empty `block_refs`), and
   `check_html` accepts a render with ZERO anchor labels while failing — with a message that
   NAMES the invented ids and states the zero-label contract — any render that invents ids.

2. **Empty-shell deterministic gate (random_idea padding).** A unit/section container that shows
   a heading but has no non-decorative body content is an empty placeholder shell → a prompt-ready
   `check_html` violation (US2 omit-never-pad made deterministic; the cold-reader checker stays
   unmodified).
"""
from __future__ import annotations

import pytest

from cast_server.requirements_render.maker_gate import (
    _parsed_ref_set,
    check_html,
    check_what_doc,
)
from cast_server.requirements_render.parser import parse_requirements


# ======================================================================================
# Ref-less (zero-ref) source — pilot_poc / random_idea shape: no US/FR/SC ids at all
# ======================================================================================
_REFLESS_SOURCE = """\
---
classification:
  family: random_idea
  confidence: 0.9
---
# Nightly export idea

## The idea

It would be nice if reports exported themselves overnight so the data is fresh by morning.
"""

# A ref-less render: real heading hierarchy, body content, NO anchor labels, NO invented ids.
_REFLESS_PASS_HTML = """\
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Nightly export idea</title>
<style>.rr-unit{margin:0}</style></head>
<body data-goal-slug="nightly-export-idea">
<main class="rr-document">
<h2>The idea</h2>
<section class="rr-unit">
<h3>Reports that export themselves overnight</h3>
<p>It would be nice if reports exported themselves overnight so the data is fresh by morning.</p>
</section>
</main>
<script src="/static/requirements_comments.js" defer></script>
</body>
</html>
"""


@pytest.fixture
def refless():
    return parse_requirements(_REFLESS_SOURCE)


def test_refless_source_has_no_canonical_refs(refless):
    """Pre-condition the rest of the file leans on: the source genuinely carries zero refs."""
    assert _parsed_ref_set(refless) == set()


# --- check_what_doc: a zero-ref WHAT doc (empty block_refs) is accepted CLEANLY ---------
def _refless_what_doc(refless, *, block_refs="[]"):
    return (
        "---\n"
        "contract: cast-requirements-what/v1\n"
        "goal_slug: nightly-export-idea\n"
        "family: random_idea\n"
        f"source_hash: {refless.content_hash}\n"
        "sections:\n"
        "  - title: What I'm thinking\n"
        "    outcome: Readers grasp the overnight-export idea.\n"
        f"    block_refs: {block_refs}\n"
        "unmapped_refs: []\n"
        "gaps: []\n"
        "---\n\n"
        "The idea is an overnight self-exporting report.\n"
    )


def test_check_what_doc_accepts_zero_ref_source_cleanly(refless):
    """A ref-less source → a section with empty `block_refs` and empty `unmapped_refs` is a clean
    pass: there is nothing to map, and emptiness is NOT a false emptiness violation."""
    rep = check_what_doc(_refless_what_doc(refless), refless)
    assert rep.passed, rep.violations


def test_check_what_doc_zero_ref_no_false_unmapped(refless):
    """No parsed ref exists, so neither an `unmapped` nor a `no such ref` violation may fire."""
    rep = check_what_doc(_refless_what_doc(refless), refless)
    assert not any("unmapped" in v or "no such ref" in v for v in rep.violations)


# --- check_html: ZERO anchor labels is correct for a ref-less render --------------------
def test_check_html_refless_render_with_no_anchor_labels_passes(refless):
    """A ref-less doc rendered with NO anchor labels at all is correct, not broken (block_ref is
    NULL by construction; the comment layer anchors to render text directly)."""
    assert check_html(_REFLESS_PASS_HTML, refless).passed


def test_check_html_refless_render_flags_invented_ids_naming_them(refless):
    """A ref-less render that invents `SC-001`/`SC-002` fails with ONE sharp message that NAMES the
    invented ids and states the zero-anchor-label contract — the feedback specificity that makes
    the structural retry converge (the pilot_poc finding)."""
    invented = _REFLESS_PASS_HTML.replace(
        "<h3>Reports that export themselves overnight</h3>",
        "<h3>Reports that export themselves overnight</h3>\n"
        "<p><strong>SC-001</strong> exports complete overnight.</p>\n"
        "<p><strong>SC-002</strong> the data is fresh by morning.</p>",
    )
    rep = check_html(invented, refless)
    assert not rep.passed
    # Exactly one consolidated zero-ref violation, naming BOTH invented ids.
    zero_ref_msgs = [v for v in rep.violations if "ZERO anchor labels" in v]
    assert len(zero_ref_msgs) == 1
    assert "SC-001" in zero_ref_msgs[0] and "SC-002" in zero_ref_msgs[0]


# ======================================================================================
# Empty-shell deterministic gate (random_idea padding)
# ======================================================================================
# A source WITH refs, so the empty-shell check is exercised independently of the zero-ref path.
_SOURCE = """\
---
classification:
  family: new_initiative
  confidence: 0.95
---
# Demo Goal

## Intent

The team wants a dependable nightly report export so downstream data lands on time.

## Functional Requirements

| ID | Requirement | Source |
|---|---|---|
| FR-001 | The system must export nightly. | intent |

## Success Criteria

| ID | Criterion | Measure |
|---|---|---|
| SC-001 | Exports complete within ten minutes. | timed |
"""

_PASS_HTML = """\
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Demo Goal</title>
<style>.rr-unit{margin:0}</style></head>
<body data-goal-slug="demo-goal">
<main class="rr-document">
<h2>What it must do</h2>
<ul>
<li><strong>FR-001</strong> The system must export nightly.</li>
</ul>
<h2>How we will know</h2>
<ul>
<li><strong>SC-001</strong> Exports complete within ten minutes.</li>
</ul>
</main>
<script src="/static/requirements_comments.js" defer></script>
</body>
</html>
"""


@pytest.fixture
def parsed():
    return parse_requirements(_SOURCE)


def test_check_html_passes_clean_page_with_no_empty_shells(parsed):
    """Baseline: FR/SC list items label with `<strong>` (no heading inside the `<li>`), so the
    empty-shell check never fires on a clean render."""
    assert check_html(_PASS_HTML, parsed).passed


def test_check_html_flags_heading_only_empty_shell(parsed):
    """A titled `<section>` with a heading but NO body content is an empty placeholder shell."""
    bad = _PASS_HTML.replace(
        "<h2>How we will know</h2>",
        "<h2>How we will know</h2>\n"
        '<section class="rr-unit"><h3>Decisions already made</h3></section>',
    )
    rep = check_html(bad, parsed)
    assert not rep.passed
    assert any("empty shell" in v and "Decisions already made" in v for v in rep.violations)


def test_check_html_flags_decorative_only_empty_shell(parsed):
    """A titled block whose only body is decorative (an em-dash placeholder) is still an empty
    shell — decoration is not content."""
    bad = _PASS_HTML.replace(
        "<h2>How we will know</h2>",
        "<h2>How we will know</h2>\n"
        '<section class="rr-unit"><h3>Out of scope</h3><p>—</p></section>',
    )
    rep = check_html(bad, parsed)
    assert not rep.passed
    assert any("empty shell" in v and "Out of scope" in v for v in rep.violations)


def test_check_html_titled_block_with_real_body_is_not_a_shell(parsed):
    """A titled `<section>` carrying real prose under its heading is NOT flagged (the gate must
    not fire on genuine content)."""
    ok = _PASS_HTML.replace(
        "<h2>How we will know</h2>",
        "<h2>How we will know</h2>\n"
        '<section class="rr-unit"><h3>Why it matters</h3>'
        "<p>Stale data breaks the morning reports downstream.</p></section>",
    )
    assert check_html(ok, parsed).passed


def test_check_html_wrapper_section_of_real_units_is_not_a_shell(parsed):
    """A wrapper `<section>` whose own direct text is empty but which contains real nested units
    keeps those units' body text in its span, so it is NOT a shell — only a genuinely empty titled
    block is flagged."""
    wrapped = _PASS_HTML.replace(
        "<h2>How we will know</h2>\n"
        "<ul>\n"
        "<li><strong>SC-001</strong> Exports complete within ten minutes.</li>\n"
        "</ul>",
        '<section class="rr-group"><h2>How we will know</h2>\n'
        "<ul>\n"
        "<li><strong>SC-001</strong> Exports complete within ten minutes.</li>\n"
        "</ul></section>",
    )
    assert check_html(wrapped, parsed).passed


def test_empty_shell_violation_is_prompt_ready_string(parsed):
    """The empty-shell violation is a plain non-empty string (fed back to the HOW agent verbatim)."""
    bad = _PASS_HTML.replace(
        "<h2>How we will know</h2>",
        "<h2>How we will know</h2>\n<section><h3>Still open</h3></section>",
    )
    rep = check_html(bad, parsed)
    shell = [v for v in rep.violations if "empty shell" in v]
    assert shell and all(isinstance(v, str) and v for v in shell)
