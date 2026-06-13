"""Pin the requirements parser's typed-block output against a frozen fixture.

The whole of Phase 1's correctness rides on these pins. The counts/order/refs below are
the *spec* (the Phase 1 plan's numbers), confirmed once against the frozen fixture. If a
count drifts, the bug is in the parser's section→kind mapping (sp2a) — fix it there; do NOT
relax the expected number to whatever the parser happens to emit. The pin exists to catch that.

Two plan-review positive tests guard the zero-silent-failure and bullet-grouping paths that a
naive reimplementation would pass on counts alone:
  * Decision #3 — an unknown H2 lands in ``unrecognized_sections`` and emits no block.
  * Decision #4 — a multi-line bullet's body includes its continuation lines, and an indented
    sub-bullet does NOT start a new block.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from cast_server.requirements_render import (
    BlockKind,
    ParsedRequirements,
    parse_requirements,
    parse_requirements_file,
)

FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "refine_requirements_v2"
    / "refined_requirements.collab.md"
)

# The Phase 1 plan's pinned per-kind block counts for the frozen fixture.
EXPECTED_COUNTS = {
    BlockKind.INTENT: 1,
    BlockKind.USER_STORY: 7,
    BlockKind.FR: 20,
    BlockKind.SC: 6,
    BlockKind.CONSTRAINT: 7,
    BlockKind.SCOPE: 6,
    BlockKind.DIRECTIONAL: 1,
    BlockKind.OPEN_QUESTION: 6,
}


@pytest.fixture(scope="module")
def parsed() -> ParsedRequirements:
    """Parse the frozen fixture once per module (parse is read-only and pure)."""
    return parse_requirements_file(FIXTURE)


def _blocks_of(parsed: ParsedRequirements, kind: BlockKind) -> list:
    return [b for b in parsed.blocks if b.kind == kind]


# ---------------------------------------------------------------------------
# Counts
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("kind,expected", list(EXPECTED_COUNTS.items()), ids=lambda v: getattr(v, "name", v))
def test_block_count_per_kind(parsed, kind, expected):
    actual = len(_blocks_of(parsed, kind))
    assert actual == expected, (
        f"{kind.name}: expected {expected} blocks, parser emitted {actual}. "
        f"A drift here means a section→kind mapping bug in the parser (sp2a) — "
        f"fix the parser, do not relax this pin."
    )


def test_total_block_count(parsed):
    assert len(parsed.blocks) == sum(EXPECTED_COUNTS.values())


# ---------------------------------------------------------------------------
# Order + bounds
# ---------------------------------------------------------------------------

def test_blocks_in_source_order(parsed):
    starts = [b.line_start for b in parsed.blocks]
    assert starts == sorted(starts), "blocks must be emitted in source (line) order"


def test_block_bounds_are_well_formed(parsed):
    n_lines = len(parsed.source_text.split("\n"))
    for b in parsed.blocks:
        assert 1 <= b.line_start <= b.line_end <= n_lines, (
            f"{b.kind.name} block has out-of-bounds span "
            f"({b.line_start}, {b.line_end}); file has {n_lines} lines"
        )


# ---------------------------------------------------------------------------
# Refs
# ---------------------------------------------------------------------------

def test_user_story_refs(parsed):
    refs = [b.ref for b in _blocks_of(parsed, BlockKind.USER_STORY)]
    assert refs == [f"US{i}" for i in range(1, 8)]


def test_fr_refs(parsed):
    refs = [b.ref for b in _blocks_of(parsed, BlockKind.FR)]
    assert refs == [f"FR-{i:03d}" for i in range(1, 21)]


def test_sc_refs(parsed):
    refs = [b.ref for b in _blocks_of(parsed, BlockKind.SC)]
    assert refs == [f"SC-{i:03d}" for i in range(1, 7)]


# ---------------------------------------------------------------------------
# Front matter / title / preamble / unrecognized
# ---------------------------------------------------------------------------

def test_front_matter_is_dict_with_header_keys(parsed):
    assert isinstance(parsed.front_matter, dict)
    assert "status" in parsed.front_matter
    assert "confidence" in parsed.front_matter


def test_title_is_h1_text(parsed):
    assert parsed.title.startswith("Refine Requirements v2")


def test_preamble_is_the_spec_maturity_blockquote(parsed):
    assert parsed.preamble.startswith(">")
    assert "Spec maturity" in parsed.preamble


def test_clean_fixture_has_no_unrecognized_sections(parsed):
    assert parsed.unrecognized_sections == ()


# ---------------------------------------------------------------------------
# Decision #3 — unknown H2 is captured, never silently dropped, emits no block
# ---------------------------------------------------------------------------

def test_unknown_h2_is_recorded_and_emits_no_block():
    doc = "# Title\n\n## Intent\n\nthe intent prose\n\n## Appendix\n\nsome appendix text\n"
    parsed = parse_requirements(doc)

    assert "Appendix" in parsed.unrecognized_sections
    # No block was emitted for the unknown section's content.
    assert not any("some appendix text" in b.body for b in parsed.blocks)
    # The recognized section is unaffected.
    assert len(_blocks_of(parsed, BlockKind.INTENT)) == 1


# ---------------------------------------------------------------------------
# Decision #4 — multi-line bullet grouping (continuations in, sub-bullets not split)
# ---------------------------------------------------------------------------

def test_fixture_constraint_body_includes_continuation_lines(parsed):
    constraints = _blocks_of(parsed, BlockKind.CONSTRAINT)
    assert len(constraints) == 7  # the count must not change under grouping

    multiline = [b for b in constraints if b.line_end > b.line_start]
    assert multiline, "fixture Constraints are wrapped — expected at least one multi-line bullet"

    # The first Constraint wraps across lines; its body must carry continuation text,
    # not be truncated to line 1 (guards against a naive line-splitter).
    first = constraints[0]
    assert first.line_end > first.line_start
    assert "\n" in first.body
    body_lines = first.body.split("\n")
    assert len(body_lines) >= 2
    assert body_lines[1].strip(), "continuation line text was dropped from the block body"


def test_indented_sub_bullet_does_not_start_a_new_block():
    doc = (
        "# Title\n\n## Constraints\n\n"
        "- **First:** lead line\n"
        "  wrapped continuation of the first bullet\n"
        "  - indented sub-bullet that must stay inside the first block\n"
        "- **Second:** another top-level bullet\n"
    )
    parsed = parse_requirements(doc)
    constraints = _blocks_of(parsed, BlockKind.CONSTRAINT)

    # Two top-level bullets → exactly two blocks (the sub-bullet is NOT a third).
    assert len(constraints) == 2
    first = constraints[0]
    assert "wrapped continuation" in first.body
    assert "indented sub-bullet" in first.body
    assert first.line_end > first.line_start
