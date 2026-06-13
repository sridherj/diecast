"""Throwaway 1b harness — a byte-faithful Python re-impl of requirements_comments.js
``highlight()`` placement, with intended-container scoping and a split-quote self-test.

NOT a pytest file (named ``spike_*`` and parked under ``spikes/1b/`` so collection skips it).
Run directly (``python spike_mark_placement.py <file.html>``) for the self-test, or import
``MakerDom`` from ``spike_backbone.py``.

Fidelity contract (mirrors the JS exactly — see static/requirements_comments.js ``highlight``):
- The JS walks ``document.querySelector('.rr-document')`` with a ``TreeWalker(SHOW_TEXT)``,
  concatenates every descendant text node's ``nodeValue`` **in document order**, and does
  ``concat.indexOf(quote)``. First match anywhere wins. NO whitespace normalization.
- Browser text-node ``nodeValue`` preserves raw source whitespace (CSS collapses only the
  *render*), so matching stdlib ``HTMLParser`` data verbatim is byte-faithful to the DOM.

What this harness adds (the plan's real test, 1b.4): ``concat.indexOf`` returns the first
match *anywhere*, so a short/generic quote can "place" on the wrong block and still pass a
naive ``find() >= 0`` check. We therefore map the match offset back to the requirement-unit
container it lands in and assert it equals the comment's **intended** container. A hit that
lands outside the intended unit is a placement FAILURE (false placement), not a pass.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

# Tags that never have a close tag / are self-contained text-wise.
_VOID = {"meta", "br", "img", "hr", "input", "link", "source", "area", "base", "col"}


@dataclass
class Node:
    """One DOM node: an element (``tag`` set) or a text node (``text`` set)."""
    tag: str | None = None
    attrs: dict = field(default_factory=dict)
    text: str | None = None
    parent: "Node | None" = None
    children: list = field(default_factory=list)

    @property
    def classes(self) -> set[str]:
        return set((self.attrs.get("class") or "").split())


class _TreeBuilder(HTMLParser):
    """Build a minimal DOM tree, preserving text-node bytes verbatim (convert_charrefs)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node(tag="#document")
        self._stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag=tag, attrs={k: (v or "") for k, v in attrs}, parent=self._stack[-1])
        self._stack[-1].children.append(node)
        if tag not in _VOID:
            self._stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag=tag, attrs={k: (v or "") for k, v in attrs}, parent=self._stack[-1])
        self._stack[-1].children.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self._stack) - 1, 0, -1):
            if self._stack[i].tag == tag:
                del self._stack[i:]
                break

    def handle_data(self, data):
        self._stack[-1].children.append(Node(text=data, parent=self._stack[-1]))


def _find(node: Node, pred) -> Node | None:
    for c in node.children:
        if c.tag and pred(c):
            return c
        hit = _find(c, pred)
        if hit:
            return hit
    return None


def _iter_text_nodes(node: Node):
    """Depth-first descendant text nodes in document order (the TreeWalker SHOW_TEXT order)."""
    for c in node.children:
        if c.text is not None:
            yield c
        else:
            yield from _iter_text_nodes(c)


def _unit_key(text_node: Node) -> str:
    """The requirement-unit container a text node belongs to (intended-container identity).

    Walks ancestors to the nearest landmark: a ``div.rr-unit`` (keyed by its ``.rr-id`` label
    text — the canonical id rendered as VISIBLE TEXT, never an ``id=`` attribute), a list
    ``<li>`` (keyed by a slug of its own text), the ``header.rr-hero``, or a section ``<h2>``.
    Text outside any requirement unit returns a non-id key (HERO / H2:* / OTHER), which can
    never equal a canonical-id intended container — exactly how a false placement is caught.
    """
    el = text_node.parent
    while el is not None and el.tag not in ("#document",):
        if el.tag == "div" and "rr-unit" in el.classes:
            label = _find(el, lambda n: "rr-id" in n.classes)
            if label:
                return "".join(t.text for t in _iter_text_nodes(label)).strip()
            return "UNIT?"
        if el.tag == "li":
            txt = "".join(t.text for t in _iter_text_nodes(el)).strip()
            return "LI:" + " ".join(txt.split())[:40]
        if el.tag == "header" and "rr-hero" in el.classes:
            return "HERO"
        if el.tag == "h2":
            txt = "".join(t.text for t in _iter_text_nodes(el)).strip()
            return "H2:" + txt
        el = el.parent
    return "OTHER"


@dataclass
class Placement:
    found: bool            # quote is a verbatim substring of the whole-doc concat (JS would mark)
    offset: int            # concat.indexOf(quote); -1 when not found
    landed_unit: str | None  # the unit the first match falls into
    in_intended: bool      # landed_unit == intended container (the REAL pass condition)


class MakerDom:
    """The ``.rr-document`` subtree + byte-faithful placement, scoped to intended containers."""

    def __init__(self, html: str):
        b = _TreeBuilder()
        b.feed(html)
        self.doc = _find(b.root, lambda n: "rr-document" in n.classes)
        if self.doc is None:
            raise ValueError("no .rr-document element found")
        # Build the whole-doc concat + per-offset unit map ONCE (mirrors one TreeWalker pass).
        self._concat_parts: list[str] = []
        self._spans: list[tuple[int, int, str]] = []  # (start, end, unit_key)
        pos = 0
        for tn in _iter_text_nodes(self.doc):
            s, e = pos, pos + len(tn.text)
            self._concat_parts.append(tn.text)
            self._spans.append((s, e, _unit_key(tn)))
            pos = e
        self.concat = "".join(self._concat_parts)

    def _unit_at(self, offset: int) -> str | None:
        for s, e, key in self._spans:
            if s <= offset < e:
                return key
        return None

    def place(self, quoted_text: str, intended_unit: str | None = None) -> Placement:
        """Faithful ``concat.indexOf`` + intended-container scoping.

        ``found`` is the raw JS behaviour (would a ``<mark>`` be created somewhere?).
        ``in_intended`` is the spike's real gate: did the FIRST match land inside the
        comment's intended requirement unit? When ``intended_unit`` is None, ``in_intended``
        mirrors ``found`` (no scoping requested).
        """
        at = self.concat.find(quoted_text)   # str.find == JS String.indexOf (first match)
        if at < 0:
            return Placement(found=False, offset=-1, landed_unit=None, in_intended=False)
        landed = self._unit_at(at)
        in_intended = (landed == intended_unit) if intended_unit is not None else True
        return Placement(found=True, offset=at, landed_unit=landed, in_intended=in_intended)


def _self_test(html_path: Path) -> None:
    """Split-across-inline-elements self-test: a quote that straddles a <strong> must still
    place. Proves the cross-text-node concat join works with NO whitespace normalization."""
    dom = MakerDom(html_path.read_text(encoding="utf-8"))
    split_quote = "a recurring cadence for a report export"   # straddles <strong>recurring</strong>
    p = dom.place(split_quote, intended_unit="US1")
    assert p.found, f"split-quote NOT found — cross-node concat join broken: {split_quote!r}"
    assert p.in_intended, f"split-quote landed in {p.landed_unit!r}, expected US1"
    # A whitespace-normalization bug would let a re-spaced quote pass; assert it does NOT.
    respaced = "a  recurring cadence"   # double space — not present verbatim
    assert not dom.place(respaced).found, "respaced quote matched — harness is normalizing whitespace!"
    print(f"[self-test] OK — split quote placed in {p.landed_unit} at offset {p.offset}; "
          f"respaced quote correctly rejected (byte-faithful).")


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).parent / "feature-maker-v1.html")
    _self_test(target)
