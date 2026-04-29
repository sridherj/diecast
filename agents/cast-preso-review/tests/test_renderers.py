"""Unit tests for the 1b edit-mode renderers (narrative + what).

These tests exercise only the renderer modules — not ``build.main``. That's
reserved for 1d's E2E tests. Here we want fast, hermetic checks that each
renderer parses its fixture into the expected slide shape.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pytest

import build


@pytest.fixture(autouse=True)
def _load_renderers():
    """Make sure renderers are registered for each test."""
    build._import_renderers()
    yield


# ---------------------------------------------------------------------------
# Narrative renderer
# ---------------------------------------------------------------------------

NARRATIVE_SECTION_HEADINGS = [
    "Opening: why agents now",
    "What changed in the tooling",
    "The review gap",
    "Three design principles",
    "Roadmap",
    "Closing",
]


def test_narrative_renderer_slide_count(copy_fixture, tmp_goal_dir: Path):
    copy_fixture("narrative/narrative.collab.md")

    slides, sidebar, result = build.RENDERER_REGISTRY["narrative"](tmp_goal_dir, None)

    # cover + one per ## section
    assert result.mode == "edit"
    assert result.stage == "narrative"
    assert result.slide_count == len(slides)
    assert result.slide_count == 1 + len(NARRATIVE_SECTION_HEADINGS)
    assert len(sidebar) == len(slides)
    # Every slide points at narrative.collab.md
    assert all(s.source_path.endswith("narrative.collab.md") for s in slides)


def test_narrative_renderer_cover_slide(copy_fixture, tmp_goal_dir: Path):
    copy_fixture("narrative/narrative.collab.md")

    slides, sidebar, _ = build.RENDERER_REGISTRY["narrative"](tmp_goal_dir, None)

    assert slides[0].id == "slide-00-cover"
    assert slides[0].title == "Agent-Driven Development 101"
    assert slides[0].outcome is None
    assert sidebar[0].slide_id == "slide-00-cover"
    assert sidebar[0].label == "Agent-Driven Development 101"


def test_narrative_renderer_section_titles(copy_fixture, tmp_goal_dir: Path):
    copy_fixture("narrative/narrative.collab.md")

    slides, _, _ = build.RENDERER_REGISTRY["narrative"](tmp_goal_dir, None)

    non_cover_titles = [s.title for s in slides[1:]]
    assert non_cover_titles == NARRATIVE_SECTION_HEADINGS


def test_narrative_renderer_outcome_extraction(copy_fixture, tmp_goal_dir: Path):
    copy_fixture("narrative/narrative.collab.md")

    slides, _, _ = build.RENDERER_REGISTRY["narrative"](tmp_goal_dir, None)

    by_title = {s.title: s for s in slides}
    # Sections with **Outcome:** lines
    assert by_title["Opening: why agents now"].outcome and "durable workflow shift" in (
        by_title["Opening: why agents now"].outcome
    )
    assert by_title["The review gap"].outcome and "bottleneck" in (
        by_title["The review gap"].outcome
    )
    # Sections without
    assert by_title["What changed in the tooling"].outcome is None
    assert by_title["Roadmap"].outcome is None


def test_narrative_renderer_block_ids_and_markdown(copy_fixture, tmp_goal_dir: Path):
    copy_fixture("narrative/narrative.collab.md")

    slides, _, _ = build.RENDERER_REGISTRY["narrative"](tmp_goal_dir, None)

    for slide in slides:
        assert slide.blocks, f"slide {slide.id} has no blocks"
        for idx, block in enumerate(slide.blocks):
            assert block["id"] == f"{slide.id}/block-{idx:02d}"
            assert "markdown" in block
            assert "html" in block
            assert "type" in block
    # A section with a table should produce at least one "table" block.
    tooling = next(s for s in slides if s.title == "What changed in the tooling")
    assert any(b["type"] == "table" for b in tooling.blocks)
    # A section with a bullet list should produce a "list" block.
    opening = next(s for s in slides if s.title == "Opening: why agents now")
    assert any(b["type"] == "list" for b in opening.blocks)


def test_narrative_renderer_is_deterministic(copy_fixture, tmp_goal_dir: Path):
    copy_fixture("narrative/narrative.collab.md")

    first = build.RENDERER_REGISTRY["narrative"](tmp_goal_dir, None)
    second = build.RENDERER_REGISTRY["narrative"](tmp_goal_dir, None)

    def _dump(triple):
        slides, sidebar, result = triple
        return json.dumps(
            {
                "slides": [asdict(s) for s in slides],
                "sidebar": [asdict(e) for e in sidebar],
                "result": asdict(result),
            },
            sort_keys=True,
        )

    assert _dump(first) == _dump(second)


# ---------------------------------------------------------------------------
# WHAT renderer
# ---------------------------------------------------------------------------


def test_what_renderer_one_slide_per_file(copy_fixture, tmp_goal_dir: Path):
    copy_fixture("what")

    slides, sidebar, result = build.RENDERER_REGISTRY["what"](tmp_goal_dir, None)

    assert result.mode == "edit"
    assert result.stage == "what"
    assert result.slide_count == 3
    assert [s.id for s in slides] == [
        "slide-01-01-intro",
        "slide-02-02-architecture",
        "slide-03-03-roadmap",
    ]
    assert len(sidebar) == len(slides)


def test_what_renderer_frontmatter_title_wins(copy_fixture, tmp_goal_dir: Path):
    copy_fixture("what")

    slides, _, _ = build.RENDERER_REGISTRY["what"](tmp_goal_dir, None)

    by_id = {s.id: s for s in slides}
    # 01-intro has frontmatter title "Why this deck exists"
    assert by_id["slide-01-01-intro"].title == "Why this deck exists"
    # 03-roadmap frontmatter title should beat the body heading
    assert by_id["slide-03-03-roadmap"].title == "P1 now, P2-P4 later"


def test_what_renderer_falls_back_to_body_heading(copy_fixture, tmp_goal_dir: Path):
    copy_fixture("what")

    slides, _, _ = build.RENDERER_REGISTRY["what"](tmp_goal_dir, None)

    # 02-architecture has no frontmatter; title comes from its `# ` heading
    by_id = {s.id: s for s in slides}
    assert by_id["slide-02-02-architecture"].title == "Shared shell, pluggable renderers"


def test_what_renderer_outcome_sources(copy_fixture, tmp_goal_dir: Path):
    copy_fixture("what")

    slides, _, _ = build.RENDERER_REGISTRY["what"](tmp_goal_dir, None)

    by_id = {s.id: s for s in slides}
    # Frontmatter outcome
    assert (
        by_id["slide-01-01-intro"].outcome
        == "Reader understands the scope and non-goals of the P1 review tool."
    )
    # Body outcome (no frontmatter)
    assert by_id["slide-02-02-architecture"].outcome and "two-layer" in (
        by_id["slide-02-02-architecture"].outcome
    )


def test_what_renderer_skips_non_md_files(tmp_goal_dir: Path):
    (tmp_goal_dir / "what").mkdir()
    (tmp_goal_dir / "what" / "01-only.md").write_text("# hi\n", encoding="utf-8")
    (tmp_goal_dir / "what" / "notes.txt").write_text("skip me", encoding="utf-8")
    (tmp_goal_dir / "what" / "README").write_text("no ext", encoding="utf-8")

    slides, _, result = build.RENDERER_REGISTRY["what"](tmp_goal_dir, None)

    assert len(slides) == 1
    assert result.slide_count == 1
    assert slides[0].title == "hi"


def test_what_renderer_preserves_filename_order(tmp_goal_dir: Path):
    what = tmp_goal_dir / "what"
    what.mkdir()
    # Create in reverse order to prove we sort, not rely on directory iteration.
    for name, title in [
        ("03-third.md", "Third"),
        ("01-first.md", "First"),
        ("02-second.md", "Second"),
    ]:
        (what / name).write_text(f"# {title}\n", encoding="utf-8")

    slides, _, _ = build.RENDERER_REGISTRY["what"](tmp_goal_dir, None)

    assert [s.title for s in slides] == ["First", "Second", "Third"]


def test_what_renderer_is_deterministic(copy_fixture, tmp_goal_dir: Path):
    copy_fixture("what")

    first = build.RENDERER_REGISTRY["what"](tmp_goal_dir, None)
    second = build.RENDERER_REGISTRY["what"](tmp_goal_dir, None)

    def _dump(triple):
        slides, sidebar, result = triple
        return json.dumps(
            {
                "slides": [asdict(s) for s in slides],
                "sidebar": [asdict(e) for e in sidebar],
                "result": asdict(result),
            },
            sort_keys=True,
        )

    assert _dump(first) == _dump(second)


# ---------------------------------------------------------------------------
# Decisions renderer (1c)
# ---------------------------------------------------------------------------


def test_decisions_renderer_registers_at_import():
    assert "decisions" in build.RENDERER_REGISTRY


def test_decisions_renderer_parses_well_formed(copy_fixture, tmp_goal_dir: Path):
    copy_fixture("decisions")
    slides, sidebar, result = build.RENDERER_REGISTRY["decisions"](tmp_goal_dir, None)

    assert result.mode == "decision"
    assert result.stage == "decisions"
    assert result.slide_count == 3
    assert len(slides) == 3
    assert all(s.mode == "decision" for s in slides)

    q01 = next(s for s in slides if s.blocks[0]["id"] == "Q-01")
    payload = q01.blocks[0]
    assert payload["kind"] == "decision"
    assert payload["id"] == "Q-01"
    assert payload["options"][0]["recommended"] is True
    assert len(payload["options"]) >= 2
    assert payload["warnings"] == []
    assert payload["context_references"], "Q-01 context must cite artifacts"

    assert [e.slide_id for e in sidebar] == [s.id for s in slides]
    assert all(e.group is None for e in sidebar)


MALFORMED_DIR = Path(__file__).resolve().parent / "fixtures" / "decisions-malformed"


def test_decisions_renderer_flags_ungrounded_option(
    capsys: pytest.CaptureFixture[str],
):
    slides, _, _ = build.RENDERER_REGISTRY["decisions"](MALFORMED_DIR, None)
    captured = capsys.readouterr()

    q04 = next(s for s in slides if s.blocks[0]["id"] == "Q-04")
    warnings = q04.blocks[0]["warnings"]
    assert any("ungrounded option" in w for w in warnings)
    assert "[WARN decision Q-04" in captured.err


def test_decisions_renderer_flags_leading_question(
    capsys: pytest.CaptureFixture[str],
):
    slides, _, _ = build.RENDERER_REGISTRY["decisions"](MALFORMED_DIR, None)
    captured = capsys.readouterr()

    q05 = next(s for s in slides if s.blocks[0]["id"] == "Q-05")
    warnings = q05.blocks[0]["warnings"]
    assert any("leading question" in w for w in warnings)
    assert "[WARN decision Q-05" in captured.err


def test_decisions_renderer_flags_premature_question(
    capsys: pytest.CaptureFixture[str],
):
    slides, _, _ = build.RENDERER_REGISTRY["decisions"](MALFORMED_DIR, None)
    captured = capsys.readouterr()

    q06 = next(s for s in slides if s.blocks[0]["id"] == "Q-06")
    warnings = q06.blocks[0]["warnings"]
    assert any("premature question" in w for w in warnings)
    assert "[WARN decision Q-06" in captured.err


def test_decisions_refuses_to_group_questions(tmp_goal_dir: Path):
    dec_dir = tmp_goal_dir / "decisions"
    dec_dir.mkdir()
    (dec_dir / "Q-bad.md").write_text(
        "---\n"
        "id: Q-A\n"
        "topic: First\n"
        "---\n"
        "## Context\nfoo `path/a.md`\n\n"
        "## Recommended\n- **Option A — X:** y `ref.md`\n\n"
        "## Alternatives\n- **Option B — Z:** q `ref2.md`\n\n"
        "---\n"
        "id: Q-B\n"
        "topic: Second\n"
        "---\n"
        "## Context\nbar\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit) as excinfo:
        build.RENDERER_REGISTRY["decisions"](tmp_goal_dir, None)
    msg = str(excinfo.value)
    assert "frontmatter fences" in msg or "multiple '---'" in msg


def test_decisions_refuses_missing_required_section(tmp_goal_dir: Path):
    dec_dir = tmp_goal_dir / "decisions"
    dec_dir.mkdir()
    (dec_dir / "Q-99.md").write_text(
        "---\nid: Q-99\ntopic: No recommended\n---\n## Context\nx `y/z.md`\n",
        encoding="utf-8",
    )
    with pytest.raises(SystemExit) as excinfo:
        build.RENDERER_REGISTRY["decisions"](tmp_goal_dir, None)
    assert "recommended" in str(excinfo.value).lower()


def test_decisions_fold_sidebar_grouping(copy_fixture, tmp_goal_dir: Path):
    copy_fixture("decisions")
    from renderers import decisions as decisions_module

    merged_slides, merged_sidebar = decisions_module.fold_into(
        tmp_goal_dir, [], []
    )
    assert len(merged_slides) == 3
    assert all(e.group == "Open questions" for e in merged_sidebar)


def test_decisions_folded_into_edit_mode(copy_fixture, tmp_goal_dir: Path):
    copy_fixture("narrative/narrative.collab.md")
    copy_fixture("decisions")

    out = build.build([
        "fixture",
        "--source-dir", str(tmp_goal_dir),
        "--output-dir", str(tmp_goal_dir / "out"),
    ])
    html = out.read_text(encoding="utf-8")
    assert "Q-01" in html
    assert "Open questions" in html


def test_decisions_options_extract_references(copy_fixture, tmp_goal_dir: Path):
    copy_fixture("decisions")
    slides, _, _ = build.RENDERER_REGISTRY["decisions"](tmp_goal_dir, None)
    q01 = next(s for s in slides if s.blocks[0]["id"] == "Q-01")
    for opt in q01.blocks[0]["options"]:
        assert opt["references"], (
            f"Q-01 option {opt['letter']} should have >= 1 reference extracted"
        )


def test_decisions_renderer_is_deterministic(copy_fixture, tmp_goal_dir: Path):
    copy_fixture("decisions")

    first = build.RENDERER_REGISTRY["decisions"](tmp_goal_dir, None)
    second = build.RENDERER_REGISTRY["decisions"](tmp_goal_dir, None)

    def _dump(triple):
        slides, sidebar, result = triple
        return json.dumps(
            {
                "slides": [asdict(s) for s in slides],
                "sidebar": [asdict(e) for e in sidebar],
                "result": asdict(result),
            },
            sort_keys=True,
        )

    assert _dump(first) == _dump(second)
