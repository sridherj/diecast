"""Pure quote→block resolver for the contract-v2 re-anchor dispatch (Phase 4b, sp4b-2).

`comment_service` displacement is a whole-document string-find — it knows *whether* a comment's
stored quote left the document, never *which* logical block (`FR-008`/`US1`/`SC-003`) it lived in.
The contract-v2 `cast-comment-reanchor` dispatch wants that block ref as an OPTIONAL hint so the
agent can track a heavily-reworded block across the edit. This module derives it deterministically
from the parsed OLD version — there is no other quote→ref resolver in the codebase, so this is the
single implementation.

Discipline (matches `maker_gate.py`'s no-copy rule):
- Reuse `parser.parse_requirements` for the block model — never re-tokenize.
- Reuse `goal_card.strip_inline_markdown` for anchorable text — the SAME stripper 4b-1's survival
  gate uses, never a second one. A quote stored against a `**bold**` span must match the stripped
  block body the maker DOM also carries.

This module is PURE: no I/O, no DB, no LLM. `block_ref` is an in-memory render ref (see
`blocks.py`) — it is a transient dispatch hint, never persisted as a comment anchor.

Render-space sibling (refine-req-v3 sp2 — the crux move). `resolve_render_anchor` is the
render-space counterpart of `resolve_block_ref`: where the source-space resolver walks the parsed
`.collab.md`, the render-space one places a quote against the **served render's container text**
(the SAME `container_text_index` walker `maker_gate.check_html` / the comment-survival gate use) and
bridges the placement back to source space via the enclosing labeled unit's canonical id. It is the
productionized form of the 1b render-anchor dry-run (`spikes/render-anchor/dry_run.py`). The two
resolvers coexist: `'source'`-space comments keep `resolve_block_ref`; `'render'`-space comments use
`resolve_render_anchor`.

Decision #1 (plan-review) is structural here: a quote that places inside a unit container carrying
ZERO anchor labels (a ref-less render — a `pilot_poc`/`random_idea` page by design) yields a
`block_ref` of `None` that is a SUCCESS, never a placement miss. The single-implementation rule holds
— `container_text_index` / `_ID_RE` / `_norm_ref` are imported from `maker_gate`, never re-walked.
"""
from __future__ import annotations

from dataclasses import dataclass

from .goal_card import strip_inline_markdown
from .maker_gate import _ID_RE, _norm_ref, container_text_index
from .parser import parse_requirements

# The deterministic-diff change values that map onto a displaced comment's OLD block. `added` is
# never a disposition for an OLD block (an added block has no old body to hold the quote).
_DISPOSITION_FROM_CHANGE = {"modified": "modified", "removed": "removed"}


def resolve_block_ref(old_content: str, quoted_text: str) -> str | None:
    """Return the `Block.ref` of the OLD block whose anchorable body contains `quoted_text`.

    Anchorable body = `strip_inline_markdown(block.body)` — the same stripped carriage the maker
    DOM places against, so a quote stored against inline markdown still resolves. Only ref-bearing
    blocks (`US*`/`FR-*`/`SC-*`) can yield a ref; a quote inside a ref-less block (a Constraints
    bullet, the Intent prose) returns ``None`` — that is a cross-boundary quote and the caller must
    OMIT `block_ref` rather than guess one (orphan-over-guess at the resolver layer).

    Returns the first matching ref in source order, or ``None`` if no single ref-bearing block
    contains the quote. Pure.
    """
    if not quoted_text:
        return None
    parsed = parse_requirements(old_content)
    for block in parsed.blocks:
        if block.ref is None:
            continue
        if quoted_text in strip_inline_markdown(block.body):
            return block.ref
    return None


def resolve_block_context(
    old_content: str,
    comments: list[dict],
    change_set: dict | None = None,
) -> dict[int, dict]:
    """Per-comment OLD-block context for the contract-v2 reanchor dispatch.

    For each comment (``{id, quoted_text, ...}``) return ``{comment_id: {...}}`` where the inner
    dict carries:

    - ``block_ref`` — the resolved ref, present ONLY when a single ref-bearing block contains the
      quote (cross-boundary quotes get NO ``block_ref`` key — never guessed).
    - ``block_disposition`` — present alongside ``block_ref``: ``modified``/``removed`` when the
      deterministic ``change_set`` lists that ref, else ``unchanged``. Absent when ``block_ref`` is.

    The disposition reads ``change_set.items[*]`` keyed by ``heading_or_ref`` (the same key space
    `block_diff._key` uses). Pure: a function of its arguments only.
    """
    disposition_by_ref: dict[str, str] = {}
    for item in (change_set or {}).get("items", []):
        ref = item.get("heading_or_ref")
        disp = _DISPOSITION_FROM_CHANGE.get(item.get("change"))
        if ref is not None and disp is not None:
            # First disposition wins (summarize() emits added→modified→removed in stable order).
            disposition_by_ref.setdefault(ref, disp)

    out: dict[int, dict] = {}
    for comment in comments:
        ctx: dict = {}
        ref = resolve_block_ref(old_content, comment.get("quoted_text", ""))
        if ref is not None:
            ctx["block_ref"] = ref
            ctx["block_disposition"] = disposition_by_ref.get(ref, "unchanged")
        out[comment["id"]] = ctx
    return out


# ----------------------------------------------------------------------------------------------
# Render-space resolver (refine-req-v3 sp2) — comments anchor to the published render snapshot
# ----------------------------------------------------------------------------------------------

# Miss classifications a placed-but-unbridged quote can land in (forensics + the migration's
# place/no-place decision). NONE of these is a hard failure: cross-boundary / decoration-spanning
# quotes simply yield block_ref=NULL (orphan-over-guess), and `no_anchor_label` is the ref-less
# render SUCCESS state (Decision #1). Mirrors the 1b dry-run's miss_class vocabulary.
RENDER_MISS_CROSS_BOUNDARY = "cross-boundary"
RENDER_MISS_DECORATION = "decoration-spanning"
RENDER_MISS_NO_ANCHOR_LABEL = "no-anchor-label"  # ref-less unit → NULL by construction (success)
RENDER_NOT_ON_PAGE = "not-on-render"             # the quote is absent from the served render


@dataclass(frozen=True)
class RenderAnchor:
    """The render-space placement + ``block_ref`` bridge for one quote against one served render.

    - ``placed`` — the quote is a verbatim substring of the served render's container text (the
      JS ``concat.indexOf`` placement parity). When ``False`` the quote is not on this render at
      all (a displaced / paraphrased quote) — the displacement/re-anchor route, not an anchor.
    - ``block_ref`` — the canonical id of the *innermost enclosing labeled unit container* the
      quote landed in, or ``None``. ``None`` is honest in three cases: a cross-boundary quote
      (spans containers / resolves >1 label — never guessed), a decoration-spanning quote (placed
      outside every unit), and a **ref-less unit** (the unit carries zero anchor labels). The last
      is a SUCCESS by construction (Decision #1), distinguished by ``in_unit=True``.
    - ``in_unit`` — the quote placed inside some labeled unit container (even a ref-less one).
    - ``miss_class`` — forensic tag; ``None`` only on a clean ref-bearing resolution.
    """

    placed: bool
    block_ref: str | None
    in_unit: bool
    miss_class: str | None


def resolve_render_anchor(render_html: str, quoted_text: str) -> RenderAnchor:
    """Place ``quoted_text`` against the served ``render_html`` and bridge it to a ``block_ref``.

    The single render-space resolver (the productionized 1b dry-run). Uses the shared
    ``container_text_index`` walker — never a second walk — and the same ``_ID_RE`` / ``_norm_ref``
    canonical-id scan ``check_html`` uses to bridge a render container back to a source ref.

    Resolution (mirrors ``dry_run.resolve``):
      offset = idx.find(quote)              # absent → not placed (displacement route)
      unit   = idx.unit_at(offset)          # None → decoration-spanning (block_ref NULL)
      quote ⊄ unit.text                     # spans the container boundary → cross-boundary (NULL)
      ids in unit                           # exactly one → that id; zero → ref-less NULL (success);
                                            #   more than one → ambiguous cross-boundary (NULL)

    Pure: a function of its two string arguments only. NULL ``block_ref`` is NEVER guessed.
    """
    if not quoted_text:
        return RenderAnchor(placed=False, block_ref=None, in_unit=False,
                            miss_class=RENDER_NOT_ON_PAGE)
    idx = container_text_index(render_html)
    offset = idx.find(quoted_text)
    if offset < 0:
        return RenderAnchor(placed=False, block_ref=None, in_unit=False,
                            miss_class=RENDER_NOT_ON_PAGE)

    unit = idx.unit_at(offset)
    if unit is None:
        # Placed only in non-unit text (hero / section heading / render decoration).
        return RenderAnchor(placed=True, block_ref=None, in_unit=False,
                            miss_class=RENDER_MISS_DECORATION)
    if quoted_text not in unit.text:
        # The quote runs past the enclosing unit → it crosses a container boundary.
        return RenderAnchor(placed=True, block_ref=None, in_unit=True,
                            miss_class=RENDER_MISS_CROSS_BOUNDARY)

    ids = sorted({_norm_ref(t) for t in _ID_RE.findall(unit.text)})
    if len(ids) == 1:
        return RenderAnchor(placed=True, block_ref=ids[0], in_unit=True, miss_class=None)
    if len(ids) == 0:
        # Ref-less unit container → NULL BY CONSTRUCTION (Decision #1): a placed comment whose
        # source has no canonical id to bridge to. Success — never retried, never badged.
        return RenderAnchor(placed=True, block_ref=None, in_unit=True,
                            miss_class=RENDER_MISS_NO_ANCHOR_LABEL)
    # >1 distinct anchor label inside the innermost unit → ambiguous: a cross-boundary quote.
    return RenderAnchor(placed=True, block_ref=None, in_unit=True,
                        miss_class=RENDER_MISS_CROSS_BOUNDARY)
