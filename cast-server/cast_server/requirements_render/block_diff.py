"""Deterministic, pure block-level diff engine for requirement versions.

Phase 5 imports this engine for round-trip change summaries — extend, never fork. The change
SET is deterministic; LLM narration consumes `summarize()` output and never invents entries.

This module is the single most reused artifact of the requirements-refinement goal: Phase 5
will ``from cast_server.requirements_render.block_diff import diff_blocks, summarize`` verbatim.
It is therefore intentionally **pure** — no FastAPI, no DB, no LLM client, no I/O of any kind.
It operates only over the landed Phase 1 ``Block`` / ``ParsedRequirements`` model.

Match algorithm (two passes, document-order tie-break):

1. **Normalized-body equality** → ``unchanged``. A pure move is ``unchanged`` — set arithmetic
   has no "moved" bucket. Bodies are normalized once (trailing per-line whitespace stripped,
   trailing newlines collapsed) and that normalization is reused everywhere.
2. **Key equality with differing body** → ``modified``. The key is the heading token for
   level-2 blocks (the in-memory ``ref`` like ``FR-007`` / ``US1`` when present, else the full
   ``heading`` text, else the bullet's own identity) and ``kind`` for level-1 blocks. The block
   ``kind`` is folded into the key so unmatched bullets in different sections never cross-pair.
   Duplicate keys pair in document order (first-unused old with first-unused new).
3. Remainders → ``added`` (new side) / ``removed`` (old side).

**Partition invariant** (the load-bearing guarantee against silent data loss): every old block
appears exactly once across ``removed ∪ modified.old ∪ unchanged.old``; every new block exactly
once across ``added ∪ modified.new ∪ unchanged.new``.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass

from .blocks import Block, ParsedRequirements


@dataclass(frozen=True)
class ModifiedBlock:
    """A matched pair: the same logical block on each side of the diff.

    Used for both ``modified`` (bodies differ) and ``unchanged`` (bodies identical — a pure
    move lands here, since the engine has no positional notion).
    """

    old: Block
    new: Block


@dataclass(frozen=True)
class BlockDiff:
    """The deterministic change set between two parsed requirement documents.

    The four tuples partition the old and new block sets (see the module docstring's partition
    invariant). ``unchanged`` carries pure moves; there is deliberately no ``moved`` bucket.
    """

    added: tuple[Block, ...]            # in new, no match in old
    removed: tuple[Block, ...]          # in old, no match in new
    modified: tuple[ModifiedBlock, ...]  # matched by key, body differs
    unchanged: tuple[ModifiedBlock, ...]  # matched, body identical (pure moves land here)


def _normalize_body(body: str) -> str:
    """Normalize a block body for equality comparison.

    Strips trailing whitespace on each line and collapses trailing newlines so cosmetic
    whitespace churn never reads as a content change. Defined once and reused by both passes.
    """
    return "\n".join(line.rstrip() for line in body.split("\n")).rstrip("\n")


def _key(block: Block) -> tuple:
    """The match key for pass 2 (key equality with differing body).

    Level-1 (whole-section) blocks key on ``kind`` alone — there is at most one per kind.
    Level-2 (element) blocks key on ``(kind, token)`` where ``token`` is the in-memory ``ref``
    (``FR-007`` / ``US1`` / ``SC-001``) when present, else the full ``heading`` text, else the
    block's own identity (so anonymous bullets only ever pair within their kind, by document
    order — never across sections).
    """
    if block.level == 1:
        return ("L1", block.kind)
    if block.ref is not None:
        token: object = block.ref
    elif block.heading is not None:
        token = block.heading
    else:
        # Anonymous bullet: no stable token. Use identity so it never key-matches a *different*
        # bullet; such bullets only reach ``modified`` via the same-kind document-order pairing
        # below when their bodies both changed in the same relative slot.
        token = id(block)
    return ("L2", block.kind, token)


def diff_blocks(old: ParsedRequirements, new: ParsedRequirements) -> BlockDiff:
    """Compute the deterministic block-level change set from ``old`` to ``new``.

    Pure and deterministic: same inputs always yield a byte-identical ``BlockDiff``. See the
    module docstring for the two-pass algorithm and the partition invariant.
    """
    old_blocks = old.blocks
    new_blocks = new.blocks
    old_used = [False] * len(old_blocks)
    new_used = [False] * len(new_blocks)

    # --- Pass 1: normalized-body equality -> unchanged (pure moves included) ---
    old_by_body: dict[str, deque[int]] = defaultdict(deque)
    for i, b in enumerate(old_blocks):
        old_by_body[_normalize_body(b.body)].append(i)

    unchanged: list[ModifiedBlock] = []
    for j, nb in enumerate(new_blocks):
        bucket = old_by_body.get(_normalize_body(nb.body))
        if bucket:
            i = bucket.popleft()
            old_used[i] = True
            new_used[j] = True
            unchanged.append(ModifiedBlock(old=old_blocks[i], new=nb))

    # --- Pass 2: key equality among the remainder -> modified (document order) ---
    old_by_key: dict[tuple, deque[int]] = defaultdict(deque)
    for i, b in enumerate(old_blocks):
        if not old_used[i]:
            old_by_key[_key(b)].append(i)

    modified: list[ModifiedBlock] = []
    for j, nb in enumerate(new_blocks):
        if new_used[j]:
            continue
        bucket = old_by_key.get(_key(nb))
        if bucket:
            i = bucket.popleft()
            old_used[i] = True
            new_used[j] = True
            modified.append(ModifiedBlock(old=old_blocks[i], new=nb))

    # --- Remainders ---
    removed = tuple(b for i, b in enumerate(old_blocks) if not old_used[i])
    added = tuple(b for j, b in enumerate(new_blocks) if not new_used[j])

    return BlockDiff(
        added=added,
        removed=removed,
        modified=tuple(modified),
        unchanged=tuple(unchanged),
    )


_EXCERPT_LEN = 80


def _excerpt(body: str) -> str:
    """A short, single-line excerpt of a block body for the change summary."""
    flat = " ".join(_normalize_body(body).split())
    return flat if len(flat) <= _EXCERPT_LEN else flat[: _EXCERPT_LEN - 1].rstrip() + "…"


def _heading_or_ref(block: Block) -> str:
    """The human label for a block: its ref, else its heading, else its excerpt."""
    if block.ref is not None:
        return block.ref
    if block.heading is not None:
        return block.heading
    return _excerpt(block.body)


def _item(change: str, block: Block) -> dict:
    return {
        "change": change,
        "kind": block.kind.value,
        "heading_or_ref": _heading_or_ref(block),
        "excerpt": _excerpt(block.body),
    }


def summarize(diff: BlockDiff) -> dict:
    """Reduce a ``BlockDiff`` to the JSON-able change summary the UI + ``/changes`` render from.

    Shape: ``{"counts": {added, modified, removed, unchanged}, "items": [{change, kind,
    heading_or_ref, excerpt}, ...]}`` where ``change ∈ {added, modified, removed}``. Items are
    emitted in a stable order (added, then modified, then removed) so the summary is
    deterministic. ``unchanged`` blocks are counted but never itemized (they are not changes).

    This dict is the cross-phase narration input: an LLM may *narrate* these entries but the
    set itself is fixed here — narration never invents items not present in ``items``.
    """
    items: list[dict] = []
    items.extend(_item("added", b) for b in diff.added)
    items.extend(_item("modified", mb.new) for mb in diff.modified)
    items.extend(_item("removed", b) for b in diff.removed)
    return {
        "counts": {
            "added": len(diff.added),
            "modified": len(diff.modified),
            "removed": len(diff.removed),
            "unchanged": len(diff.unchanged),
        },
        "items": items,
    }
