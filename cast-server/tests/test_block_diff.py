"""Pin the pure block-level diff engine + tracked-changes renderer (Phase 4, sp2).

This engine is the single most reused artifact of the requirements goal — Phase 5 imports it
verbatim. The load-bearing test is the **partition invariant**: every old block lands in
exactly one of ``removed ∪ modified.old ∪ unchanged.old`` and every new block in exactly one
of ``added ∪ modified.new ∪ unchanged.new``. If that holds, no change can be silently dropped
from a summary. The fixture pair seeds exactly one of each bucket (one added FR, one reworded
FR, one deleted Out-of-Scope bullet, one moved section) so the four buckets map 1:1.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from cast_server.requirements_render import diff_render, parser
from cast_server.requirements_render.block_diff import (
    BlockDiff,
    ModifiedBlock,
    diff_blocks,
    summarize,
)
from cast_server.requirements_render.blocks import Block, BlockKind, ParsedRequirements
from cast_server.requirements_render.renderer import RenderResult

_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "refine_requirements_v2"
_BASE = _FIXTURES / "refined_requirements.collab.md"
_EDIT = _FIXTURES / "refined_requirements.v2-edit.collab.md"

_RENDER_PKG = (
    Path(__file__).resolve().parent.parent / "cast_server" / "requirements_render"
)


@pytest.fixture(scope="module")
def base() -> ParsedRequirements:
    return parser.parse_requirements_file(_BASE)


@pytest.fixture(scope="module")
def edit() -> ParsedRequirements:
    return parser.parse_requirements_file(_EDIT)


@pytest.fixture(scope="module")
def diff(base: ParsedRequirements, edit: ParsedRequirements) -> BlockDiff:
    return diff_blocks(base, edit)


# --- Partition invariant (the safety net against silent data loss) ---------------------


def test_partition_invariant_old_side(base: ParsedRequirements, diff: BlockDiff) -> None:
    """Every old block appears exactly once across removed ∪ modified.old ∪ unchanged.old."""
    seen = (
        [id(b) for b in diff.removed]
        + [id(m.old) for m in diff.modified]
        + [id(m.old) for m in diff.unchanged]
    )
    assert len(seen) == len(set(seen)), "an old block appeared in more than one bucket"
    assert set(seen) == {id(b) for b in base.blocks}


def test_partition_invariant_new_side(edit: ParsedRequirements, diff: BlockDiff) -> None:
    """Every new block appears exactly once across added ∪ modified.new ∪ unchanged.new."""
    seen = (
        [id(b) for b in diff.added]
        + [id(m.new) for m in diff.modified]
        + [id(m.new) for m in diff.unchanged]
    )
    assert len(seen) == len(set(seen)), "a new block appeared in more than one bucket"
    assert set(seen) == {id(b) for b in edit.blocks}


# --- The four seeded edits map to the four buckets -------------------------------------


def test_added_bucket(diff: BlockDiff) -> None:
    """The one brand-new FR (FR-021) is the sole `added` entry."""
    assert [b.ref for b in diff.added] == ["FR-021"]


def test_removed_bucket(diff: BlockDiff) -> None:
    """The one deleted Out-of-Scope bullet is the sole `removed` entry."""
    assert len(diff.removed) == 1
    only = diff.removed[0]
    assert only.kind is BlockKind.SCOPE
    assert "cast-explore" in only.body


def test_modified_bucket(diff: BlockDiff) -> None:
    """The one reworded FR (same ref FR-001, changed body) is the sole `modified` entry."""
    assert len(diff.modified) == 1
    mb = diff.modified[0]
    assert mb.old.ref == mb.new.ref == "FR-001"
    assert mb.old.body != mb.new.body


def test_pure_move_lands_in_unchanged(
    base: ParsedRequirements, edit: ParsedRequirements, diff: BlockDiff
) -> None:
    """A whole section relocated with body unchanged is `unchanged` (set arithmetic has no
    'moved'): the Directional section sits at a different index on each side, identical body."""
    moved = [m for m in diff.unchanged if m.old.kind is BlockKind.DIRECTIONAL]
    assert len(moved) == 1
    mb = moved[0]
    assert mb.old.body == mb.new.body
    old_pos = base.blocks.index(mb.old)
    new_pos = edit.blocks.index(mb.new)
    assert old_pos != new_pos, "fixture should relocate the Directional section"


# --- Duplicate keys pair in document order ---------------------------------------------


def _doc(blocks: tuple[Block, ...]) -> ParsedRequirements:
    return ParsedRequirements(
        title="t",
        front_matter={},
        preamble="",
        blocks=blocks,
        unrecognized_sections=(),
        source_text="",
        content_hash="x",
    )


def _fr(ref: str, body: str) -> Block:
    return Block(
        kind=BlockKind.FR,
        level=2,
        body=body,
        heading=None,
        ref=ref,
        line_start=1,
        line_end=1,
    )


def test_duplicate_keys_pair_in_document_order() -> None:
    """Two same-key blocks whose bodies both change pair old[0]↔new[0], old[1]↔new[1]."""
    old = _doc((_fr("FR-001", "old A"), _fr("FR-001", "old B")))
    new = _doc((_fr("FR-001", "new A"), _fr("FR-001", "new B")))
    d = diff_blocks(old, new)
    assert d.added == () and d.removed == ()
    assert [(m.old.body, m.new.body) for m in d.modified] == [
        ("old A", "new A"),
        ("old B", "new B"),
    ]


# --- summarize() -----------------------------------------------------------------------


def test_summarize_counts_match_set_sizes(diff: BlockDiff) -> None:
    s = summarize(diff)
    assert s["counts"] == {
        "added": len(diff.added),
        "modified": len(diff.modified),
        "removed": len(diff.removed),
        "unchanged": len(diff.unchanged),
    }


def test_summarize_items_match_changes(diff: BlockDiff) -> None:
    """Item rows cover exactly the added + modified + removed blocks (not unchanged)."""
    s = summarize(diff)
    changes = [it["change"] for it in s["items"]]
    assert changes.count("added") == len(diff.added)
    assert changes.count("modified") == len(diff.modified)
    assert changes.count("removed") == len(diff.removed)
    assert len(s["items"]) == len(diff.added) + len(diff.modified) + len(diff.removed)
    refs = {it["heading_or_ref"] for it in s["items"] if it["change"] != "removed"}
    assert {"FR-021", "FR-001"} <= refs
    for it in s["items"]:
        assert set(it) == {"change", "kind", "heading_or_ref", "excerpt"}


# --- Determinism -----------------------------------------------------------------------


def test_diff_is_deterministic(base: ParsedRequirements, edit: ParsedRequirements) -> None:
    """Same inputs -> structurally identical BlockDiff + byte-identical summarize() output."""
    d1 = diff_blocks(base, edit)
    d2 = diff_blocks(base, edit)
    assert [b.ref for b in d1.added] == [b.ref for b in d2.added]
    assert [b.body for b in d1.removed] == [b.body for b in d2.removed]
    assert [m.new.ref for m in d1.modified] == [m.new.ref for m in d2.modified]
    assert summarize(d1) == summarize(d2)


# --- diff_render -----------------------------------------------------------------------


def test_render_diff_returns_render_result(
    base: ParsedRequirements, edit: ParsedRequirements
) -> None:
    r = diff_render.render_diff(base, edit, base_version=1, head_version=2)
    assert isinstance(r, RenderResult)
    assert "diff-changed-panel" in r.html
    assert 'id="diff-1"' in r.html  # transient anchors exist only in the diff view
    for cls in ("diff-added", "diff-modified", "diff-removed"):
        assert cls in r.html
    # The theme (with the Phase-4 diff classes) must be inlined — a self-contained view.
    assert ":root" in r.html and "--color-success" in r.html
    assert ".diff-added" in r.html  # the CSS rule, not just the class attribute


def test_render_diff_is_deterministic(
    base: ParsedRequirements, edit: ParsedRequirements
) -> None:
    a = diff_render.render_diff(base, edit, base_version=1, head_version=2).html
    b = diff_render.render_diff(base, edit, base_version=1, head_version=2).html
    assert a == b


def test_render_diff_tolerates_unparseable_side(edit: ParsedRequirements) -> None:
    """An unparseable (None) snapshot must not raise — it returns a 'cannot diff' card."""
    r = diff_render.render_diff(None, edit, base_version=0, head_version=2)
    assert isinstance(r, RenderResult)
    assert "cannot diff" in " ".join(r.warnings).lower()
    assert "diff-cannot" in r.html


# --- Engine-purity source pins (mirrors Phase 3b's router source pin) ------------------

_FORBIDDEN = ("import openai", "anthropic", "import requests", "get_connection", "sqlite")


@pytest.mark.parametrize("module", ["block_diff.py", "diff_render.py"])
def test_engine_modules_have_no_llm_db_or_http_imports(module: str) -> None:
    """The diff engine is pure: no LLM client, no DB, no HTTP in either module's source."""
    src = (_RENDER_PKG / module).read_text()
    for needle in _FORBIDDEN:
        assert needle not in src, f"{module} must not reference {needle!r}"


def test_diff_css_block_is_token_only() -> None:
    """The Phase-4 diff CSS block uses var(--color-*) tokens, never raw hex (FR-012)."""
    css = (_RENDER_PKG / "templates" / "_theme.css.j2").read_text()
    # Everything from the diff marker onward is the sp2 addition; no hex may appear there.
    diff_block = css[css.index("Phase 4 — tracked-changes") :]
    assert not re.findall(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b", diff_block)
