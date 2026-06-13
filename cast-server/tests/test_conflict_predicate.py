"""Pin the conflict predicate (Phase 5, sp3a) — "zero silent overwrites by construction".

The load-bearing guarantee: a downstream change request that assumed ``base_version`` can NEVER
silently overwrite a region a human touched since then. ``detect_conflict`` is pure and total —
every (base, head, quote) maps to exactly one of ``clean | conflicted | orphaned`` — and it runs
with an INJECTED ``locate`` resolver, so this whole suite touches no DB, no LLM, no file I/O
beyond reading the checked-in fixtures.

Thin-spine reality: with no stable element IDs, conflict detection *is* quote-location. A region a
human reworded still contains the anchor quote but its enclosing line changed → ``conflicted``. A
quote a human deleted no longer locates → ``orphaned`` (a first-class verdict, never an error).
"""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from cast_server.requirements_render import conflict
from cast_server.requirements_render.conflict import (
    RESOLUTION_CHOICES,
    ConflictSurface,
    detect_conflict,
    region_hash,
)
from cast_server.requirements_render.hashing import content_hash

_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "refine_requirements_v2"

# Focused, purpose-built variants (crisp single-region semantics).
_CB = (_FIXTURES / "conflict_base.collab.md").read_text(encoding="utf-8")
_CH = (_FIXTURES / "conflict_head.collab.md").read_text(encoding="utf-8")

# The real frozen requirements doc + the real human-edited variant (Phase 4's diff fixture pair) —
# proves the predicate works on the actual document, not just toy inputs.
_REAL_BASE = (_FIXTURES / "refined_requirements.collab.md").read_text(encoding="utf-8")
_REAL_EDIT = (_FIXTURES / "refined_requirements.v2-edit.collab.md").read_text(encoding="utf-8")


def _line_locate(content: str, quote: str, section_hint: str | None) -> str | None:
    """A pure-python stand-in for the cast-comment-reanchor verbatim-substring locator.

    Returns the *enclosing line* containing ``quote`` (the region is larger than the anchor), or
    ``None`` if the quote is not a verbatim substring. Returning the enclosing line — not just the
    quote — is what lets a reworded-but-still-anchored region read as ``conflicted`` rather than a
    false ``clean``. No DB, no LLM, no I/O.
    """
    for line in content.splitlines():
        if quote in line:
            return line
    return None


# Anchor quotes present verbatim in both fixture documents.
_Q_REWORDED = "The refined output shall lead with WHAT content"  # enclosing line differs → conflicted
_Q_STABLE = "The agent shall classify each goal into a workflow family"  # line identical → clean
_Q_DELETED = "Changes to the exploration pipeline itself."  # removed in head → orphaned


# --------------------------------------------------------------------------- core verdicts


def test_unchanged_region_since_base_is_clean() -> None:
    assert detect_conflict(_CB, _CH, _Q_STABLE, None, locate=_line_locate) == "clean"


def test_human_edited_region_since_base_is_conflicted() -> None:
    # The anchor quote still locates in HEAD, but its enclosing line was reworded → must surface.
    assert detect_conflict(_CB, _CH, _Q_REWORDED, None, locate=_line_locate) == "conflicted"


def test_quote_deleted_since_base_is_orphaned() -> None:
    # The quote no longer locates in HEAD → orphaned (surface), never a silent no-op.
    assert detect_conflict(_CB, _CH, _Q_DELETED, None, locate=_line_locate) == "orphaned"


def test_pure_addition_is_clean() -> None:
    # target_quote is None ⇒ nothing to conflict on ⇒ clean, regardless of contents.
    assert detect_conflict(_CB, _CH, None, None, locate=_line_locate) == "clean"


# --------------------------------------------------------------------------- real-document proof


def test_real_document_reworded_fr001_is_conflicted() -> None:
    assert detect_conflict(_REAL_BASE, _REAL_EDIT, _Q_REWORDED, None, locate=_line_locate) == "conflicted"


def test_real_document_stable_fr002_is_clean() -> None:
    assert detect_conflict(_REAL_BASE, _REAL_EDIT, _Q_STABLE, None, locate=_line_locate) == "clean"


def test_real_document_deleted_scope_line_is_orphaned() -> None:
    real_deleted = "Changes to the exploration pipeline (cast-explore) itself."
    assert detect_conflict(_REAL_BASE, _REAL_EDIT, real_deleted, None, locate=_line_locate) == "orphaned"


# --------------------------------------------------------------------------- region_hash helper


def test_region_hash_none_for_pure_addition() -> None:
    assert region_hash(_CB, None, None, locate=_line_locate) is None


def test_region_hash_none_when_quote_absent() -> None:
    assert region_hash(_CB, "no such quote anywhere", None, locate=_line_locate) is None


def test_region_hash_reuses_content_hash() -> None:
    # Never reimplement sha256 — region_hash must equal content_hash of the located region.
    located = _line_locate(_CB, _Q_STABLE, None)
    assert located is not None
    assert region_hash(_CB, _Q_STABLE, None, locate=_line_locate) == content_hash(located)


# --------------------------------------------------------------------------- property + purity


@pytest.mark.parametrize(
    "base_region,head_region",
    [
        ("alpha", "ALPHA"),
        ("the quick brown fox", "the quick red fox"),
        ("FR-1 body v1", "FR-1 body v2"),
        ("x", "xy"),
        ("same", "same"),  # equal pair must read clean — the only clean case in this set
    ],
)
def test_never_clean_when_head_hash_differs_from_base(base_region: str, head_region: str) -> None:
    """Property: detect_conflict is never 'clean' when the HEAD region hash != base region hash.

    A stub locate that returns a fixed region per document lets us drive the hashes directly.
    """
    quote = "anchor"
    base_doc = f"prefix {quote} :: {base_region}"
    head_doc = f"prefix {quote} :: {head_region}"

    def stub_locate(content: str, q: str, s: str | None) -> str | None:
        # Locate the enclosing "region" (everything after '::') if the anchor is present.
        return content.split("::", 1)[1].strip() if q in content else None

    verdict = detect_conflict(base_doc, head_doc, quote, None, locate=stub_locate)
    if content_hash(base_region) != content_hash(head_region):
        assert verdict != "clean"
        assert verdict == "conflicted"
    else:
        assert verdict == "clean"


def test_predicate_is_pure_no_db_llm_or_io_imports() -> None:
    """The predicate module must import no DB, no agent/LLM, and do no file I/O."""
    src = inspect.getsource(conflict)
    for forbidden in ("sqlite", "get_connection", "anthropic", "open(", "requests", "httpx", "subprocess"):
        assert forbidden not in src, f"conflict.py must not reference {forbidden!r}"


def test_predicate_runs_with_trivial_pure_stub() -> None:
    # The plan's validation example: a one-line lambda locate, no DB/LLM/I/O.
    verdict = detect_conflict(
        "A FR-1 body", "A FR-1 body", "FR-1 body", None,
        locate=lambda c, q, s: q if q in c else None,
    )
    assert verdict == "clean"


# --------------------------------------------------------------------------- resolution surface


def test_conflict_surface_offers_three_choices_only_when_conflicted() -> None:
    surface = ConflictSurface(
        verdict="conflicted", target_quote=_Q_REWORDED, section_hint=None,
        base_version=3, proposed_body="new body",
    )
    assert surface.choices == RESOLUTION_CHOICES
    assert RESOLUTION_CHOICES == ("accept-incoming", "keep-current", "merge-with-free-edit")
    assert surface.to_dict()["choices"] == list(RESOLUTION_CHOICES)


def test_conflict_surface_offers_no_choices_when_clean() -> None:
    surface = ConflictSurface(
        verdict="clean", target_quote=None, section_hint=None,
        base_version=3, proposed_body="addition",
    )
    assert surface.choices == ()


def test_conflict_surface_rejects_unknown_verdict() -> None:
    with pytest.raises(ValueError):
        ConflictSurface(
            verdict="merged", target_quote=None, section_hint=None,
            base_version=1, proposed_body="x",
        )
