"""Tracked-changes ("what changed") renderer for a pair of requirement versions.

Pure and deterministic, like the Phase 3a canonical renderer: no DB, no LLM, no I/O beyond
loading the package's own Jinja theme. It consumes the deterministic change set from
:mod:`block_diff` and lays the **head document's order** out as the spine, decorating each
block with its change treatment (added / modified / removed) and leading with a "What changed"
panel.

Transient ``id="diff-{n}"`` anchors exist **only** in this diff view — generated per render,
never stored, never used as comment anchors. The canonical render's zero-``id`` contract
(the thin-spine DOM rule) is untouched: diffs are a throwaway, read-only, comment-free view
served fresh each request and never written to the goal folder.
"""
from __future__ import annotations

from collections import defaultdict

from .block_diff import diff_blocks, summarize
from .blocks import Block, ParsedRequirements
from .renderer import RenderResult
from .templating import get_environment

# The diff document shell. Autoescape is on (the env), so every interpolated block body /
# label / meta string is escaped — the renderer never emits raw user HTML. The theme CSS
# (including the Phase-4 diff classes) is inlined so the view is self-contained.
_DIFF_DOCUMENT = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ document_title }} — changes v{{ base_version }} → v{{ head_version }}</title>
<style>
{{ theme_css }}
</style>
</head>
<body>
<main class="rr-document rr-diff">

<!-- The "What changed" panel renders FIRST (FR-017). -->
<section class="diff-changed-panel" aria-label="What changed">
<h2 class="diff-changed-title">What changed: v{{ base_version }} &rarr; v{{ head_version }}</h2>
<p class="diff-changed-counts">+{{ counts.added }} added &middot; ~{{ counts.modified }} modified \
&middot; &minus;{{ counts.removed }} removed</p>
{% if panel %}
<ul class="diff-changed-list">
{% for item in panel %}
<li class="diff-changed-item diff-changed-item--{{ item.change }}"><a href="#diff-{{ item.n }}">\
{{ item.label }}</a></li>
{% endfor %}
</ul>
{% else %}
<p class="diff-changed-empty">No structural changes between these versions.</p>
{% endif %}
</section>

{% for e in spine %}
<section class="diff-block diff-{{ e.change }}" id="diff-{{ e.n }}">
<div class="diff-block-meta">{{ e.meta }}</div>
<div class="diff-block-body">{{ e.body }}</div>
{% if e.old_body is not none %}
<details class="diff-prev"><summary>Previous version</summary><del>{{ e.old_body }}</del></details>
{% endif %}
</section>
{% endfor %}

</main>
</body>
</html>
"""

_CANNOT_DIFF_DOCUMENT = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ document_title }} — changes v{{ base_version }} → v{{ head_version }}</title>
<style>
{{ theme_css }}
</style>
</head>
<body>
<main class="rr-document rr-diff">
<section class="diff-changed-panel diff-cannot" aria-label="Cannot diff">
<h2 class="diff-changed-title">Cannot diff v{{ base_version }} &rarr; v{{ head_version }}</h2>
<p class="diff-changed-empty">{{ reason }}</p>
</section>
</main>
</body>
</html>
"""


def _theme_css() -> str:
    """Render the package theme to inline CSS (includes the Phase-4 diff classes)."""
    return get_environment().get_template("_theme.css.j2").render()


def _meta(block: Block) -> str:
    """A compact label for a block: ``kind`` plus its ref/heading when it has one."""
    parts: list[str] = [block.kind.value]
    if block.ref is not None:
        parts.append(block.ref)
    elif block.heading is not None:
        parts.append(block.heading)
    return " · ".join(parts)


def render_diff(
    old: ParsedRequirements | None,
    new: ParsedRequirements | None,
    *,
    base_version: int,
    head_version: int,
) -> RenderResult:
    """Render a tracked-changes view of the change set from ``old`` to ``new``.

    Returns the same :class:`RenderResult` shape the Phase 3a renderer returns. Deterministic.

    Error tolerance: if either side is ``None`` (the route could not parse an archived,
    pre-parser snapshot), this returns a "cannot diff this pair" card rather than raising — a
    500 here would lose the rest of the version history view.
    """
    if old is None or new is None:
        html = get_environment().from_string(_CANNOT_DIFF_DOCUMENT).render(
            document_title="Requirements",
            theme_css=_theme_css(),
            base_version=base_version,
            head_version=head_version,
            reason=(
                "One of these snapshots predates the structured parser and cannot be "
                "diffed block-by-block."
            ),
        )
        return RenderResult(html=html, warnings=("cannot diff: unparseable snapshot",))

    diff = diff_blocks(old, new)
    summary = summarize(diff)

    # Identity maps over the *actual* block instances the diff returned (diff_blocks never
    # copies blocks, so `id()` is a safe handle back into the source documents).
    old_index = {id(b): i for i, b in enumerate(old.blocks)}
    added_ids = {id(b) for b in diff.added}
    modified_by_new = {id(mb.new): mb for mb in diff.modified}

    # old-document-index -> the new block that carries it forward (unchanged or modified).
    survivor_new_for_old_idx: dict[int, Block] = {}
    for mb in diff.unchanged:
        survivor_new_for_old_idx[old_index[id(mb.old)]] = mb.new
    for mb in diff.modified:
        survivor_new_for_old_idx[old_index[id(mb.old)]] = mb.new

    # Anchor each removed block after the new block of its nearest preceding surviving sibling
    # (decision #8: a removal renders attached after the last surviving block of its old
    # section). Removals with no preceding survivor lead the spine.
    removed_after: dict[int, list[Block]] = defaultdict(list)
    leading_removed: list[Block] = []
    for rb in diff.removed:
        ri = old_index[id(rb)]
        anchor_old_idx = next(
            (k for k in range(ri - 1, -1, -1) if k in survivor_new_for_old_idx), None
        )
        if anchor_old_idx is None:
            leading_removed.append(rb)
        else:
            removed_after[id(survivor_new_for_old_idx[anchor_old_idx])].append(rb)

    # Build the ordered render list, assigning the transient diff-{n} ids as we go.
    spine: list[dict] = []
    counter = 0

    def _emit(block: Block, change: str, *, old_body: str | None = None) -> None:
        nonlocal counter
        counter += 1
        spine.append(
            {
                "n": counter,
                "change": change,
                "meta": _meta(block),
                "body": block.body,
                "old_body": old_body,
            }
        )

    for rb in leading_removed:
        _emit(rb, "removed")

    for nb in new.blocks:
        if id(nb) in added_ids:
            _emit(nb, "added")
        elif id(nb) in modified_by_new:
            _emit(nb, "modified", old_body=modified_by_new[id(nb)].old.body)
        else:
            _emit(nb, "unchanged")
        for rb in removed_after.get(id(nb), ()):
            _emit(rb, "removed")

    # The panel links only the *changed* blocks (added / modified / removed), in spine order.
    panel = [
        {
            "n": e["n"],
            "change": e["change"],
            "label": _panel_label(e),
        }
        for e in spine
        if e["change"] in ("added", "modified", "removed")
    ]

    html = get_environment().from_string(_DIFF_DOCUMENT).render(
        document_title=new.title or "Requirements",
        theme_css=_theme_css(),
        base_version=base_version,
        head_version=head_version,
        counts=summary["counts"],
        panel=panel,
        spine=spine,
    )
    return RenderResult(html=html, warnings=())


def _panel_label(entry: dict) -> str:
    """Derive the panel link text from a spine entry's meta/body."""
    # `meta` is "kind" or "kind · ref/heading"; prefer the ref/heading part when present.
    meta = entry["meta"]
    if " · " in meta:
        return meta.split(" · ", 1)[1]
    flat = " ".join(entry["body"].split())
    return flat if len(flat) <= 60 else flat[:59].rstrip() + "…"
