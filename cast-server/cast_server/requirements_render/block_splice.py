"""Deterministic render splice — the UPDATE-mode page assembler (refine-req-v3 sp3b).

The Sub-phase 1a spike returned **FAIL → deterministic-splice** (`spikes/update-fidelity/
verdict.md`): the production HOW agent paraphrases ~10% of *unchanged* narrative cells even under a
literal copy-exact instruction, and every divergence was a true reword (zero whitespace-only), so a
gate-enforced-LLM-copy mechanism cannot hold a `bug_fix` page byte-identical. The binding
consequence: the **server** keeps the prior render's unchanged unit-container bytes verbatim and
splices in HOW-rendered **changed-block fragments**. Byte-identity of untouched prose is then
guaranteed **by construction** — never trusted from the LLM. This module is that splice.

What HOW emits in UPDATE mode (the fragment sub-contract — see `cast-requirements-how.md` two-mode
section, kept byte-aligned with the parser here): between the render sentinels, ONE
``<!-- RR-FRAGMENT ref="FR-001" -->`` … ``<!-- /RR-FRAGMENT -->`` block per *changed* (added /
modified) requirement unit — the standalone unit-container fragment for that ref, in the prior
page's structure + style. Removed blocks → nothing emitted (the server drops them). Unchanged blocks
→ nothing emitted (the server keeps the prior bytes).

The assembler walks the **prior render** as the structural template:

- an UNCHANGED unit → its prior raw-HTML bytes, verbatim (the byte-identity guarantee);
- a MODIFIED unit → replaced by HOW's fragment for that ref;
- a REMOVED unit → dropped (with its immediately-trailing whitespace filler);
- an ADDED unit → HOW's fragment inserted after the last prior unit sharing its id kind
  (`US`/`FR`/`SC`), else appended after the last unit; best-effort deterministic placement;
- every inter-unit filler region (heads, section headings, `<body>` chrome) → verbatim.

Single-implementation discipline (shared-context HARD edge): the **landmark set** that defines a
"unit" (`_UNIT_TAGS` / `_UNIT_DIV_CLASSES`) and the canonical-id scan (`_ID_RE` / `_norm_ref`) are
imported from `maker_gate` — never re-derived. The byte-faithful *text* walker `container_text_index`
is a TEXT-space index (offsets into the descendant-text concat); the splice needs raw-HTML BYTE
spans of unit elements, a distinct granularity, so this module adds a small offset-tracking
HTML segmenter. It is NOT a second text walker — `check_update_fidelity` (the fidelity gate) still
imports `container_text_index`; this segmenter exists only to slice verbatim HTML bytes.

Pure: no I/O, no DB, no LLM. A function of its string arguments only.
"""
from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser

from .maker_gate import _ID_RE, _UNIT_DIV_CLASSES, _UNIT_TAGS, _VOID_TAGS, _norm_ref

# Fragment delimiters HOW emits in UPDATE mode (byte-aligned with cast-requirements-how.md).
_FRAGMENT_OPEN_PREFIX = "<!-- RR-FRAGMENT"
_FRAGMENT_CLOSE = "<!-- /RR-FRAGMENT -->"


# --------------------------------------------------------------------------------------
# Fragment parsing (HOW UPDATE-mode output → {ref: fragment_html})
# --------------------------------------------------------------------------------------
def parse_fragments(rendered: str) -> dict[str, str]:
    """Parse HOW's UPDATE-mode fragment output (the bytes already extracted from between the render
    sentinels) into ``{canonical_ref: fragment_html}``.

    Each fragment is an ``<!-- RR-FRAGMENT ref="<ID>" -->`` … ``<!-- /RR-FRAGMENT -->`` block; the
    ref is read from the opening delimiter's ``ref="…"`` attribute (normalized via the shared
    `_norm_ref`). A fragment whose delimiter carries no parseable ref is ignored (the gate then sees
    a missing changed-block and fails structurally — never a silent splice of an unkeyed fragment).
    A ref repeated across fragments keeps the FIRST (deterministic). Returns ``{}`` on no fragments.
    """
    fragments: dict[str, str] = {}
    pos = 0
    while True:
        open_at = rendered.find(_FRAGMENT_OPEN_PREFIX, pos)
        if open_at == -1:
            break
        head_end = rendered.find("-->", open_at)
        if head_end == -1:
            break
        header = rendered[open_at + len(_FRAGMENT_OPEN_PREFIX):head_end]
        body_start = head_end + len("-->")
        close_at = rendered.find(_FRAGMENT_CLOSE, body_start)
        if close_at == -1:
            break
        body = rendered[body_start:close_at].strip("\n")
        pos = close_at + len(_FRAGMENT_CLOSE)
        ref = _ref_from_header(header)
        if ref is not None and ref not in fragments:
            fragments[ref] = body
    return fragments


def _ref_from_header(header: str) -> str | None:
    """The canonical ref from a fragment delimiter's ``ref="…"`` attribute, or None. Tolerant of
    single/double quotes and surrounding whitespace; the value is run through the shared id scan so
    only a real canonical id (`US1`/`FR-001`/`SC-003`) is accepted."""
    eq = header.find("ref")
    if eq == -1:
        return None
    rest = header[eq + len("ref"):].lstrip()
    if not rest.startswith("="):
        return None
    rest = rest[1:].lstrip()
    if rest and rest[0] in "\"'":
        quote = rest[0]
        end = rest.find(quote, 1)
        value = rest[1:end] if end != -1 else rest[1:]
    else:
        value = rest.split()[0] if rest.split() else ""
    matches = _ID_RE.findall(value)
    return _norm_ref(matches[0]) if matches else None


# --------------------------------------------------------------------------------------
# Raw-HTML unit segmentation (byte spans of top-level unit containers)
# --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class UnitSegment:
    """One top-level requirement-unit element's verbatim raw-HTML byte span within a render.

    - ``html`` — the exact source bytes ``render_html[start:end]`` of the unit element (open tag
      through its matching close tag), copy-exact for the byte-identity guarantee.
    - ``ref`` — the canonical id labelling the unit (`FR-001`/`US1`/`SC-003`), or ``None`` for a
      ref-less unit (a `pilot_poc`/`random_idea` page by design, or a narrative cell). A ref-less
      unit is keyed only by position — always kept verbatim (treated as unchanged).
    - ``start`` / ``end`` — absolute byte offsets into the render the segment was taken from.
    """

    html: str
    ref: str | None
    start: int
    end: int


def _is_unit_tag(tag: str, attrs: dict[str, str]) -> bool:
    """The unit landmark predicate over a raw (tag, attrs) pair — the same landmark SET
    `maker_gate._is_unit` uses (imported `_UNIT_TAGS` / `_UNIT_DIV_CLASSES`), expressed over the
    live-parser inputs rather than a `_Node` (no second landmark definition)."""
    if tag in _UNIT_TAGS:
        return True
    if tag in ("div", "aside"):
        classes = frozenset((attrs.get("class") or "").split())
        if classes & _UNIT_DIV_CLASSES or any(c.endswith("-unit") for c in classes):
            return True
    return False


class _UnitSpanParser(HTMLParser):
    """Record the absolute byte span of every TOP-LEVEL unit element (a unit nested inside another
    unit is part of its ancestor's span, never its own seam — mirrors the outermost-owner notion).

    Byte-faithful: spans are taken against the original fed string via a (line, col) → absolute
    index table, so a sliced segment is verbatim. Well-formed maker HTML is assumed (it is gated
    output); unbalanced/void tags are handled defensively so a stray tag never throws."""

    def __init__(self, html: str) -> None:
        super().__init__(convert_charrefs=True)
        self._html = html
        self._line_starts = [0]
        for i, ch in enumerate(html):
            if ch == "\n":
                self._line_starts.append(i + 1)
        # Stack of open elements: (tag, abs_start, is_unit). Only the OUTERMOST unit opens a seam.
        self._stack: list[tuple[str, int, bool]] = []
        self._unit_depth = 0  # how many open units are currently on the stack
        self._pending_unit_start: int | None = None
        self.segments: list[UnitSegment] = []

    def _abs(self) -> int:
        line, col = self.getpos()
        return self._line_starts[line - 1] + col

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in _VOID_TAGS:
            return
        attr_map = {k: (v or "") for k, v in attrs}
        is_unit = _is_unit_tag(tag, attr_map)
        start = self._abs()
        if is_unit and self._unit_depth == 0:
            self._pending_unit_start = start
        self._stack.append((tag, start, is_unit))
        if is_unit:
            self._unit_depth += 1

    def handle_startendtag(self, tag: str, attrs: list) -> None:
        # A self-closing element contributes no descendant container span; nothing to seam.
        return

    def handle_endtag(self, tag: str) -> None:
        # Pop to the matching open tag (defensive against unclosed inline tags).
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == tag:
                closed = self._stack[i:]
                del self._stack[i:]
                # End offset = past the '>' terminating this close tag.
                gt = self._html.find(">", self._abs())
                end = (gt + 1) if gt != -1 else len(self._html)
                for entry in closed:
                    if entry[2]:  # was a unit
                        self._unit_depth -= 1
                if self._unit_depth == 0 and self._pending_unit_start is not None:
                    seg_html = self._html[self._pending_unit_start:end]
                    self.segments.append(
                        UnitSegment(
                            html=seg_html,
                            ref=_ref_in(seg_html),
                            start=self._pending_unit_start,
                            end=end,
                        )
                    )
                    self._pending_unit_start = None
                return


def _ref_in(unit_html: str) -> str | None:
    """The single canonical id labelling a unit's raw HTML, or None. Zero ids → ref-less unit;
    exactly one → that ref; more than one → ambiguous, treated as ref-less (kept verbatim). The
    one-unit-one-container `check_html` gate makes the >1 case a separate structural failure, so the
    splice never has to resolve it — it just declines to key the unit."""
    ids = {_norm_ref(t) for t in _ID_RE.findall(unit_html)}
    return next(iter(ids)) if len(ids) == 1 else None


def segment_units(render_html: str) -> list[UnitSegment]:
    """Every top-level requirement-unit segment of ``render_html``, in document order. The seams the
    splice keeps / swaps / drops; the inter-unit filler is whatever lies between consecutive
    segments (and before the first / after the last)."""
    parser = _UnitSpanParser(render_html)
    parser.feed(render_html)
    parser.close()
    return parser.segments


# --------------------------------------------------------------------------------------
# The splice — assemble the UPDATE render from prior bytes + changed fragments
# --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class SpliceResult:
    """The assembled UPDATE render plus what the assembler could/could not place.

    - ``html`` — the spliced page (prior bytes for unchanged units, fragments for changed).
    - ``missing_refs`` — modified/added refs with NO emitted fragment (a fragment-contract miss —
      the caller surfaces it as a structural violation; the unit keeps its prior bytes / is absent).
    - ``spliced_refs`` — refs whose fragment was actually placed (modified + added).
    """

    html: str
    missing_refs: tuple[str, ...]
    spliced_refs: tuple[str, ...]


def _id_kind(ref: str) -> str:
    """The id kind of a canonical ref — its alpha prefix (`US`/`FR`/`SC`) — used only to place an
    added fragment after the last prior unit of the same kind (best-effort deterministic position)."""
    i = 0
    while i < len(ref) and ref[i].isalpha():
        i += 1
    return ref[:i] or ref


def splice_update(
    prior_html: str,
    fragments: dict[str, str],
    *,
    modified_refs: frozenset[str],
    added_refs: frozenset[str],
    removed_refs: frozenset[str],
) -> SpliceResult:
    """Assemble the UPDATE render. ``prior_html`` is the structural template; ``fragments`` is
    ``{ref: html}`` from `parse_fragments`. The three disposition sets are canonical-ref strings
    (the same `_norm_ref` space the segments carry).

    Construction guarantee: every unit NOT in ``modified_refs ∪ removed_refs`` (including every
    ref-less unit) is copied **byte-for-byte** from ``prior_html`` — so `check_update_fidelity`'s
    raw-byte identity on unchanged containers holds by construction, never by trusting the LLM.
    """
    segments = segment_units(prior_html)
    out: list[str] = []
    cursor = 0
    spliced: list[str] = []
    missing: list[str] = []

    # Where to drop each added fragment: after the LAST prior unit of the same id kind, else after
    # the last unit overall (index into `segments`); -1 ⇒ no units → append before the cursor tail.
    last_unit_by_kind: dict[str, int] = {}
    for i, seg in enumerate(segments):
        if seg.ref is not None:
            last_unit_by_kind[_id_kind(seg.ref)] = i
    last_unit_idx = len(segments) - 1
    added_after: dict[int, list[str]] = {}
    for ref in sorted(added_refs):
        frag = fragments.get(ref)
        if frag is None:
            missing.append(ref)
            continue
        anchor_idx = last_unit_by_kind.get(_id_kind(ref), last_unit_idx)
        added_after.setdefault(anchor_idx, []).append(frag)
        spliced.append(ref)

    for i, seg in enumerate(segments):
        # Verbatim filler before this unit (heads, section headings, prior inter-unit chrome).
        out.append(prior_html[cursor:seg.start])
        if seg.ref is not None and seg.ref in removed_refs:
            pass  # drop the unit; trailing whitespace filler is absorbed by the next slice
        elif seg.ref is not None and seg.ref in modified_refs:
            frag = fragments.get(seg.ref)
            if frag is None:
                missing.append(seg.ref)
                out.append(seg.html)  # no fragment → keep prior bytes (gate will fail id/text)
            else:
                out.append(frag)
                spliced.append(seg.ref)
        else:
            out.append(seg.html)  # unchanged (or ref-less) → verbatim, the byte-identity guarantee
        cursor = seg.end
        for frag in added_after.get(i, []):
            out.append("\n" + frag)

    out.append(prior_html[cursor:])  # the tail (closing `</main></body></html>` chrome)
    # An added fragment with no prior unit of any kind (anchor_idx == -1 on an empty page) appends
    # at the very end, before nothing — handled by the -1 bucket here.
    for frag in added_after.get(-1, []):
        out.append("\n" + frag)

    return SpliceResult(
        html="".join(out),
        missing_refs=tuple(missing),
        spliced_refs=tuple(spliced),
    )
