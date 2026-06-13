"""Conflict predicate for round-trip write-back (Phase 5, sp3a).

Makes silent overwrite **structurally impossible**. A downstream change request carries the
version it assumed (`base_version`); before that change is applied, we ask: *has a human touched
the target region since then?* The answer is a pure, total verdict — ``clean`` | ``conflicted`` |
``orphaned`` — computed by comparing the ``content_hash`` of the located target region at the base
version vs HEAD.

Thin-spine reality (no per-element surrogate IDs): conflict detection **is** quote-location. The
region is found by *quote, never by a stable ID*, using an **injected** ``locate`` resolver (the
``cast-comment-reanchor`` verbatim-substring discipline). Injecting the resolver keeps this module
pure and unit-testable with no DB, no LLM, no file I/O.

The "zero silent overwrites by construction" guarantee:
  - a region a human changed since base  → ``conflicted`` (surface, never overwrite);
  - a quote that no longer locates        → ``orphaned`` (surface, never silently no-op);
  - a pure addition (no target region)    → ``clean`` (nothing to conflict on).
"""
from __future__ import annotations

from typing import Callable, Optional

from cast_server.requirements_render.hashing import content_hash

# An injected quote→region resolver: given the document `content`, the `target_quote`, and an
# optional `section_hint`, return the located region's text, or None if the quote does not locate.
# Production wires the verbatim-substring locator (a non-present quote returns None → orphaned);
# tests inject pure-python stubs. This module never imports a concrete locator — it stays pure.
Locator = Callable[[str, str, Optional[str]], Optional[str]]

# The 3-way conflict-resolution surface vocabulary (data, not an auto-merge). When a verdict is
# `conflicted`, the render/intake layer presents exactly these choices; v2 computes NO merge.
RESOLUTION_CHOICES: tuple[str, ...] = ("accept-incoming", "keep-current", "merge-with-free-edit")

# The three verdicts detect_conflict can return. Total: every input maps to exactly one.
VERDICTS: tuple[str, ...] = ("clean", "conflicted", "orphaned")


def region_hash(
    content: str,
    target_quote: Optional[str],
    section_hint: Optional[str],
    *,
    locate: Locator,
) -> Optional[str]:
    """Hash of the located target region within ``content``; ``None`` if the quote does not locate.

    ``locate(content, target_quote, section_hint) -> str | None`` is INJECTED — the quote→region
    resolver (verbatim-substring first, ``section_hint`` as a tiebreak). Keeping it injected keeps
    this function pure: no DB, no LLM, no I/O.

    A pure addition (``target_quote is None``) has no target region to conflict on → ``None``.
    """
    if target_quote is None:
        return None
    region = locate(content, target_quote, section_hint)
    return content_hash(region) if region is not None else None


def detect_conflict(
    base_content: str,
    head_content: str,
    target_quote: Optional[str],
    section_hint: Optional[str],
    *,
    locate: Locator,
) -> str:
    """Return ``'clean'`` | ``'conflicted'`` | ``'orphaned'``. Pure and total.

    - Pure addition (``target_quote is None``): always ``'clean'`` (nothing to conflict on).
    - Quote does not locate in HEAD: ``'orphaned'`` (→ surface; never silently no-op).
    - ``region_hash(base) == region_hash(HEAD)``: ``'clean'``.
    - else: ``'conflicted'`` (→ surface; never overwrite).

    The caller resolves ``base_content`` from
    ``requirement_version_service.get_version(slug, base_version)["content"]`` and ``head_content``
    from ``get_current(slug)["content"]``.
    """
    if target_quote is None:
        return "clean"
    head = region_hash(head_content, target_quote, section_hint, locate=locate)
    if head is None:
        return "orphaned"
    base = region_hash(base_content, target_quote, section_hint, locate=locate)
    return "clean" if base == head else "conflicted"


class ConflictSurface:
    """The structured 3-way choice presented when a verdict is ``conflicted`` — data, not a merge.

    Mirrors Jama "suspect until cleared" semantics: the change is held until a human picks one of
    ``RESOLUTION_CHOICES``. v2 computes NO auto-textual-merge; ``merge-with-free-edit`` hands the
    human a free-edit surface. Every transition is recorded as a ``change_request_events`` row by
    the service / sp4 apply path — **not** here (this is a pure descriptor).
    """

    __slots__ = ("verdict", "target_quote", "section_hint", "base_version", "proposed_body")

    def __init__(
        self,
        *,
        verdict: str,
        target_quote: Optional[str],
        section_hint: Optional[str],
        base_version: Optional[int],
        proposed_body: str,
    ) -> None:
        if verdict not in VERDICTS:
            raise ValueError(f"unknown verdict {verdict!r}; expected one of {VERDICTS}")
        self.verdict = verdict
        self.target_quote = target_quote
        self.section_hint = section_hint
        self.base_version = base_version
        self.proposed_body = proposed_body

    @property
    def choices(self) -> tuple[str, ...]:
        """Resolution choices to offer; only a ``conflicted`` verdict needs a human choice."""
        return RESOLUTION_CHOICES if self.verdict == "conflicted" else ()

    def to_dict(self) -> dict:
        """Plain-data descriptor the render/intake layer can serialize and present."""
        return {
            "verdict": self.verdict,
            "target_quote": self.target_quote,
            "section_hint": self.section_hint,
            "base_version": self.base_version,
            "proposed_body": self.proposed_body,
            "choices": list(self.choices),
        }
