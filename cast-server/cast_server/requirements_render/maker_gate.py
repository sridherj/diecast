"""The deterministic maker gate — productionizes the Phase 1 spike audits (sp3b).

`check_what_doc` and `check_html` are the **executable definition of "structurally valid
maker output"**. 3c enforces them on every `cast-requirements-what` / `-how` generation; 4a
later wraps its quality loop around the same two functions. Both are pure (no I/O, no DB, no
LLM, no subprocess) and return the frozen `GateReport` shape, whose `violations` are
*prompt-ready strings* — 3c feeds them back to the HOW agent verbatim on retry, 4a appends to
the same channel.

This module productionizes three Phase 1 audits:

- **1a id audit** (`spikes/1a/spike_id_audit.py`): id-token set equality + FR-003 per-block
  correspondence + zero-`id`/self-containment.
- **1b verbatim harness** (`spikes/1b/spike_mark_placement.py`): the byte-faithful
  container-text walker, here exposed as the **public** `container_text_index(html)` helper
  (revision b) so Phase 4b-1 (`cast-comment-reanchor` survival gate) imports it on a proven
  contract instead of re-implementing a second walker.

Single-implementation discipline (shared context): the markdown stripper is **imported** from
Phase 2's `goal_card.strip_inline_markdown` — never re-implemented here. The container-text
walker is defined once, here, and shared.

Reconciliations baked in (where the spikes' hand-crafted maker markup differs from the v2
deterministic substrate the gate must also accept — T1):

- **"each id occurs exactly once" → one *owning container* per id.** The deterministic render
  legitimately echoes a User-Story heading inside its disclosure `<summary>` (the same `US1`
  text appears in the open lead *and* the collapsed summary, both inside the one
  `.user-story` unit). Counting whole-document text occurrences would wrongly fail that and
  break T1. The invariant that actually matters — and that catches a label smeared across two
  *different* blocks — is **exactly one unit container owns each id**.
- **anchorable text is the block's rendered human body, per kind** (the description cell of an
  FR/SC table row; the story prose under a US heading) — never the raw `| FR-001 | … |` row
  syntax, which no reader ever sees and the renderer never carries verbatim.
- **self-containment flags *external* `src`/`href`** (scheme or protocol-relative) — the v2
  substrate legitimately carries internal `/static/...` script `src`s (the two FR-028
  sanctioned scripts) and may carry an internal `/goals/.../render/diff` version-toggle href.
  The threat the gate guards is a CDN font / external script, not internal navigation.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Sequence, TypedDict

import yaml

from .blocks import Block, BlockKind, ParsedRequirements
from .goal_card import strip_inline_markdown  # 2a→3b hard edge: import, never re-implement.

# --------------------------------------------------------------------------------------
# GateReport — the frozen result shape (shared-context contract)
# --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class GateReport:
    """`{"passed": bool, "violations": [str]}` made a frozen value.

    `violations` is a tuple (immutable, order-stable) of **prompt-ready** strings — each is
    safe to hand straight to the HOW agent on retry. `passed` is exactly `not violations`.
    """

    passed: bool
    violations: tuple[str, ...] = ()


def _report(violations: list[str]) -> GateReport:
    """Build a `GateReport` from a (possibly empty) violation list. Empty ⇒ passed."""
    return GateReport(passed=not violations, violations=tuple(violations))


# --------------------------------------------------------------------------------------
# Canonical id tokens (US1 / FR-007 / SC-001)
# --------------------------------------------------------------------------------------
# US ids are `US\S+` in the grammar (`US1`); FR/SC are zero-padded `FR-\d{3,}` / `SC-\d{3,}`.
# A `US-1` spelling normalizes to `US1` so source and HTML compare on one canonical form.
# The id ends on a `(?!\d)` lookahead, NOT a trailing `\b`: a maker that abuts the anchor
# label against the body text (`<span>FR-001</span><span>A …</span>` → concat `FR-001A …`)
# has no word boundary after the digits (digit→letter is not a `\b`), yet `FR-001` is plainly
# the id. The lookahead matches there while still refusing to truncate a longer `FR-0012`.
_ID_RE = re.compile(r"\bUS-?\d+(?!\d)|\bFR-\d{3,}(?!\d)|\bSC-\d{3,}(?!\d)")
# US/FR/SC slot names — section titles a WHAT doc may NEVER be named after (the
# family-communication rule made checkable).
_SLOT_NAMES = frozenset({"User Stories", "Functional Requirements", "Success Criteria"})
_WHAT_CONTRACT = "cast-requirements-what/v1"

# --------------------------------------------------------------------------------------
# Gap contract (refine-requirements-v3 Phase 5a) — activating Phase 3's reserved `gaps[]` seam
# --------------------------------------------------------------------------------------
# The single CLOSED gap-resolution status vocabulary (Plan Review A3): `gaps-state.json`'s
# `status`, 5b's fixed `.rr-gap` marker strings, and the job-row reason codes all map 1:1 to it.
# `maker_gate` rejects any out-of-enum status. In 5a (no CR emitted yet) only the `unfilled-*`
# statuses are reachable; the `cr-*` statuses are reserved for 5b's emitter.
GAP_STATUS_ENUM = frozenset(
    {"cr-proposed", "cr-applied", "unfilled-cannot-supply", "unfilled-declined",
     "unfilled-ask-failed"}
)
# A gap id is `GAP-NN` (sequential per doc). It is NEVER a canonical ref token — the gate rejects
# a `GAP-NN` appearing where a `Block.ref` is expected (id-space collision guard).
_GAP_ID_RE = re.compile(r"^GAP-(\d+)$")
_GAP_TOKEN_RE = re.compile(r"^GAP-\d+$")
# Keys that would mean the WHAT layer smuggled an ANSWER into a gap entry. The WHAT doc names what
# is MISSING; it NEVER supplies the answer (FR-015 structural — that is cast-requirements-gapfill's
# job, gated server-side). Any of these on a gap entry is a loud violation.
_GAP_ANSWER_KEYS = frozenset({"answer", "proposed_answer", "proposed_body", "supplied", "evidence"})


def _norm_ref(ref: str) -> str:
    """Canonicalize an id token: `US-1` → `US1`, surrounding space trimmed, upper-cased."""
    return ref.strip().upper().replace("US-", "US")


def _parsed_ref_set(parsed: ParsedRequirements) -> set[str]:
    """The authoritative assigned-id set, structurally from the parser (never a prose regex —
    so a cross-reference like "(see SC-001)" in body text never inflates the source set)."""
    return {_norm_ref(b.ref) for b in parsed.blocks if b.ref}


# --------------------------------------------------------------------------------------
# container_text_index — the shared, byte-faithful container-text walker (revision b)
# --------------------------------------------------------------------------------------
# Inline elements whose text belongs to their enclosing block — never their own "unit".
_INLINE_TAGS = frozenset(
    {"strong", "em", "b", "i", "u", "a", "span", "code", "mark", "small",
     "sub", "sup", "abbr", "cite", "q", "time", "kbd", "samp", "var", "s", "del", "ins"}
)
# Elements that open a requirement-unit container (the landmark set). A `<div>`/`<aside>`
# qualifies only when its class set names a unit (`user-story`, `rr-unit`, `req-unit`, or any
# `*-unit`). Mirrors the 1b spike's `_unit_key` landmark walk, generalized to the v2 substrate.
_UNIT_TAGS = frozenset({"li", "section", "article"})
_UNIT_DIV_CLASSES = frozenset({"user-story", "rr-unit", "req-unit"})
# Void elements: no close tag, contribute no descendant text.
_VOID_TAGS = frozenset(
    {"meta", "br", "img", "hr", "input", "link", "source", "area", "base", "col", "wbr"}
)


@dataclass(frozen=True)
class Container:
    """One element and the byte-faithful concatenation of its descendant text nodes.

    `text` is `document_text[start:end]` — the same bytes a `TreeWalker(SHOW_TEXT)` over this
    element would concatenate (no whitespace normalization), so `text.find(quote)` matches the
    JS `concat.indexOf(quote)` placement exactly.
    """

    tag: str
    classes: frozenset[str]
    text: str
    start: int
    end: int
    depth: int
    is_unit: bool


@dataclass(frozen=True)
class ContainerTextIndex:
    """The per-container text index — public contract imported by `check_html` AND Phase 4b-1.

    `document_text` is the whole-document descendant-text concatenation scoped to the first
    `.rr-document` element (the node `requirements_comments.js` walks); when no `.rr-document`
    exists it is the whole parsed tree. `containers` carries every element's descendant-text
    span. `find` / `unit_at` mirror the JS placement primitives (first-match `indexOf`, then
    map the offset back to the enclosing requirement unit).
    """

    document_text: str
    containers: tuple[Container, ...]

    def find(self, needle: str) -> int:
        """`document_text.find(needle)` — byte-faithful to the JS `concat.indexOf(quote)`
        (first match anywhere, no normalization). `-1` when absent."""
        return self.document_text.find(needle)

    def unit_at(self, offset: int) -> Container | None:
        """The *innermost* requirement-unit container covering `offset`, or `None` when the
        offset falls outside every unit (e.g. hero / section-heading text). 'Innermost' =
        greatest nesting depth among covering units, so an FR `<li>` wins over its enclosing
        `<section>`."""
        best: Container | None = None
        for c in self.containers:
            if c.is_unit and c.start <= offset < c.end:
                if best is None or c.depth > best.depth:
                    best = c
        return best

    def units(self) -> tuple[Container, ...]:
        """Every requirement-unit container, in document order."""
        return tuple(c for c in self.containers if c.is_unit)


@dataclass
class _Node:
    tag: str | None = None
    attrs: dict = field(default_factory=dict)
    text: str | None = None
    parent: "_Node | None" = None
    children: list = field(default_factory=list)

    @property
    def classes(self) -> frozenset[str]:
        return frozenset((self.attrs.get("class") or "").split())


class _TreeBuilder(HTMLParser):
    """Build a minimal DOM tree, preserving text-node bytes verbatim.

    `convert_charrefs=True` so `&amp;` becomes the `&` a browser `nodeValue` would expose;
    no whitespace normalization (CSS collapses only the *render*, never the text node).
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node(tag="#document")
        self._stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list) -> None:
        node = _Node(tag=tag, attrs={k: (v or "") for k, v in attrs}, parent=self._stack[-1])
        self._stack[-1].children.append(node)
        if tag not in _VOID_TAGS:
            self._stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list) -> None:
        node = _Node(tag=tag, attrs={k: (v or "") for k, v in attrs}, parent=self._stack[-1])
        self._stack[-1].children.append(node)

    def handle_endtag(self, tag: str) -> None:
        for i in range(len(self._stack) - 1, 0, -1):
            if self._stack[i].tag == tag:
                del self._stack[i:]
                break

    def handle_data(self, data: str) -> None:
        self._stack[-1].children.append(_Node(text=data, parent=self._stack[-1]))


def _find(node: _Node, pred) -> _Node | None:
    """First descendant element (depth-first) satisfying `pred`, or None."""
    for c in node.children:
        if c.tag and pred(c):
            return c
        hit = _find(c, pred)
        if hit:
            return hit
    return None


def _is_unit(node: _Node) -> bool:
    """Whether `node` opens a requirement-unit container (the landmark set)."""
    if node.tag in _UNIT_TAGS:
        return True
    if node.tag in ("div", "aside"):
        cls = node.classes
        if cls & _UNIT_DIV_CLASSES or any(c.endswith("-unit") for c in cls):
            return True
    return False


def container_text_index(html: str) -> ContainerTextIndex:
    """Walk `html` (stdlib `HTMLParser`), concatenating descendant text-node content per
    container, byte-faithful to `requirements_comments.js`. Returns the per-container text
    index used for verbatim placement checks.

    PUBLIC: imported by `check_html` AND by Phase 4b-1 (`cast-comment-reanchor` survival gate).
    No-copy shared helper — there is exactly one container-text walker, and this is it.

    Whitespace is preserved verbatim (the 1b harness-fidelity rule): a browser text node's
    `nodeValue` keeps raw source whitespace, so matching stdlib `HTMLParser` data byte-for-byte
    reproduces the DOM the comment layer marks against.
    """
    builder = _TreeBuilder()
    builder.feed(html)
    builder.close()

    # Scope the document concat to `.rr-document` (the node the JS TreeWalker walks); fall
    # back to the whole tree when the maker omitted it.
    root = _find(builder.root, lambda n: "rr-document" in n.classes) or builder.root

    containers: list[Container] = []
    parts: list[str] = []
    pos = 0

    def walk(node: _Node, depth: int) -> None:
        nonlocal pos
        for child in node.children:
            if child.text is not None:
                parts.append(child.text)
                pos += len(child.text)
            elif child.tag in ("script", "style"):
                # A TreeWalker over `.rr-document` never reaches head CSS/JS; excluding
                # script/style subtrees keeps the concat content-only so CSS tokens cannot
                # inflate the id scan, and is byte-identical for the real `.rr-document`
                # (which carries no inline script/style).
                continue
            else:
                start = pos
                walk(child, depth + 1)
                end = pos
                containers.append(
                    Container(
                        tag=child.tag or "",
                        classes=child.classes,
                        text="".join(parts)[start:end],
                        start=start,
                        end=end,
                        depth=depth + 1,
                        is_unit=_is_unit(child),
                    )
                )

    walk(root, 0)
    document_text = "".join(parts)
    # `text` slices were taken against the running join; re-slice against the final concat so
    # every Container.text is exactly document_text[start:end] (byte-identical to a TreeWalker).
    containers = [
        Container(
            tag=c.tag, classes=c.classes, text=document_text[c.start : c.end],
            start=c.start, end=c.end, depth=c.depth, is_unit=c.is_unit,
        )
        for c in containers
    ]
    return ContainerTextIndex(document_text=document_text, containers=tuple(containers))


# --------------------------------------------------------------------------------------
# check_what_doc — the WHAT-layer gate (Step 3b.1)
# --------------------------------------------------------------------------------------
def _split_front_matter(text: str) -> tuple[dict | None, bool]:
    """Parse a leading `---`-fenced YAML header from a WHAT doc.

    Returns `(front_matter, ok)`. `ok` is False when the header is absent, unterminated, or
    not a YAML mapping — every one of which is a loud gate failure (the maker must emit a
    well-formed `cast-requirements-what/v1` front matter)."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, False
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            raw = "\n".join(lines[1:idx])
            try:
                parsed = yaml.safe_load(raw)
            except yaml.YAMLError:
                return None, False
            if not isinstance(parsed, dict):
                return None, False
            return parsed, True
    return None, False


def check_what_doc(what_doc_text: str, parsed: ParsedRequirements) -> GateReport:
    """Gate a `cast-requirements-what/v1` doc against the parsed source (Step 3b.1).

    Asserts: front matter parses; `contract == cast-requirements-what/v1`; `source_hash`
    matches the parsed content hash; **id-mapping totality** (every `Block.ref` appears in
    exactly one section's `block_refs`, none twice, none invented, `unmapped_refs` empty);
    section titles non-empty and none named after a US/FR/SC slot. Violations are prompt-ready.
    """
    violations: list[str] = []

    front, ok = _split_front_matter(what_doc_text)
    if not ok:
        return _report(
            ["WHAT front matter is missing or not a valid YAML mapping — emit a "
             f"`{_WHAT_CONTRACT}` header fenced by `---` lines."]
        )

    contract = front.get("contract")
    if contract != _WHAT_CONTRACT:
        violations.append(
            f"WHAT contract is {contract!r}, expected {_WHAT_CONTRACT!r}."
        )

    source_hash = front.get("source_hash")
    if source_hash != parsed.content_hash:
        violations.append(
            f"WHAT source_hash {source_hash!r} does not match the parsed source hash "
            f"{parsed.content_hash!r} — the WHAT doc was generated against different source."
        )

    # --- id-mapping totality ---
    parsed_refs = _parsed_ref_set(parsed)
    sections = front.get("sections")
    if not isinstance(sections, list):
        violations.append("WHAT `sections` must be a list of section objects.")
        sections = []

    seen: dict[str, int] = {}
    for section in sections:
        if not isinstance(section, dict):
            violations.append(f"WHAT section is not a mapping: {section!r}.")
            continue
        title = section.get("title")
        if not isinstance(title, str) or not title.strip():
            violations.append("WHAT section has an empty or missing `title`.")
        elif title.strip() in _SLOT_NAMES:
            violations.append(
                f"WHAT section title {title.strip()!r} is a US/FR/SC slot name — name "
                "sections after the family communication intent, never the source slots."
            )
        for ref in section.get("block_refs") or []:
            if _GAP_TOKEN_RE.match(str(ref).strip()):
                violations.append(
                    f"WHAT section block_refs names {str(ref).strip()!r} — a GAP-NN gap id is "
                    "never a canonical ref (id-space collision)."
                )
                continue
            seen[_norm_ref(str(ref))] = seen.get(_norm_ref(str(ref)), 0) + 1

    mapped = set(seen)
    for ref in sorted(parsed_refs - mapped):
        violations.append(f"{ref} is unmapped — every parsed ref must feed exactly one section.")
    for ref in sorted(mapped - parsed_refs):
        violations.append(f"{ref} is mapped in the WHAT doc but no such ref exists in the source.")
    for ref in sorted(r for r, n in seen.items() if n > 1):
        violations.append(f"{ref} appears in more than one section — each ref maps to exactly one.")

    unmapped = front.get("unmapped_refs")
    if unmapped:
        violations.append(
            f"WHAT `unmapped_refs` is non-empty ({unmapped!r}) — every ref must be placed."
        )

    # --- gaps[] schema (Phase 5a — the reserved seam activated) ---
    violations.extend(_check_gaps(front, parsed_refs))

    return _report(violations)


def _check_gaps(front: dict, parsed_refs: set[str]) -> list[str]:
    """Validate the WHAT doc's `gaps[]` entries (Phase 5a). The list may be empty (the common,
    clean-render case) or absent (back-compat — treated as empty). Each entry must:

    - carry a `GAP-NN` `gap_id`, sequential from `GAP-01`, unique by construction;
    - name a non-empty `question`;
    - list `block_refs` whose every member is a parsed source ref (NEVER a `GAP-NN` token);
    - contain NO answer field — the WHAT layer names what is missing, it never supplies it.

    Returns prompt-ready violation strings (the cap `GAPFILL_MAX_GAPS` is a prompt-side detection
    bar, NOT gate-enforced — a page is communication, not an audit)."""
    violations: list[str] = []
    gaps = front.get("gaps")
    if gaps is None:
        return violations
    if not isinstance(gaps, list):
        return ["WHAT `gaps` must be a list of gap entries (or an empty list)."]

    for i, gap in enumerate(gaps):
        if not isinstance(gap, dict):
            violations.append(f"WHAT gap entry {i} is not a mapping: {gap!r}.")
            continue

        smuggled = sorted(set(gap) & _GAP_ANSWER_KEYS)
        if smuggled:
            violations.append(
                f"WHAT gap entry names answer field(s) {smuggled} — the WHAT layer declares what is "
                "MISSING, it NEVER supplies an answer (FR-015 structural)."
            )

        gap_id = gap.get("gap_id")
        m = _GAP_ID_RE.match(str(gap_id)) if gap_id is not None else None
        if not m:
            violations.append(f"WHAT gap `gap_id` {gap_id!r} must match the `GAP-NN` form.")
        elif int(m.group(1)) != i + 1:
            violations.append(
                f"WHAT gap ids must be sequential from GAP-01; {gap_id!r} is out of sequence at "
                f"position {i + 1}."
            )

        question = gap.get("question")
        if not isinstance(question, str) or not question.strip():
            violations.append(f"WHAT gap {gap_id!r} has an empty or missing `question`.")

        refs = gap.get("block_refs")
        if not isinstance(refs, list) or not refs:
            violations.append(
                f"WHAT gap {gap_id!r} must list at least one `block_refs` member (a parsed ref)."
            )
        else:
            for ref in refs:
                if _GAP_TOKEN_RE.match(str(ref).strip()):
                    violations.append(
                        f"WHAT gap {gap_id!r} `block_refs` names {str(ref).strip()!r} — a GAP-NN "
                        "gap id is never a canonical ref."
                    )
                elif _norm_ref(str(ref)) not in parsed_refs:
                    violations.append(
                        f"WHAT gap {gap_id!r} `block_refs` member {str(ref)!r} is not a parsed "
                        "source ref."
                    )
    return violations


def check_gaps_state(state_obj: dict | None) -> GateReport:
    """Gate a `gaps-state.json` object against the closed status vocabulary (Phase 5a / A3).

    `gaps-state.json` is the service-owned per-job resolution record `{"gaps":[{gap_id, status,
    cr_id?}]}`. The ONLY structural rule the pure gate owns is that every `status` is in
    `GAP_STATUS_ENUM` — an out-of-enum status is a loud violation (it would otherwise desync from
    5b's fixed marker strings). Pure, fixture-tested."""
    violations: list[str] = []
    gaps = (state_obj or {}).get("gaps")
    if not isinstance(gaps, list):
        return _report(["gaps-state `gaps` must be a list of resolution entries."])
    for entry in gaps:
        if not isinstance(entry, dict):
            violations.append(f"gaps-state entry is not a mapping: {entry!r}.")
            continue
        status = entry.get("status")
        if status not in GAP_STATUS_ENUM:
            violations.append(
                f"gaps-state status {status!r} is outside the closed enum "
                f"{sorted(GAP_STATUS_ENUM)}."
            )
    return _report(violations)


# --------------------------------------------------------------------------------------
# check_html — the HOW-layer gate (Steps 3b.3–3b.5)
# --------------------------------------------------------------------------------------
# An external (network-fetching) URL: a scheme or a protocol-relative `//host`. Internal
# root-relative (`/static/...`, `/goals/...`) and fragment (`#…`) references are navigation,
# not fetches, and are allowed (the self-containment rule guards CDN fonts / external scripts).
_EXTERNAL_URL_RE = re.compile(r"^\s*(?:[a-zA-Z][a-zA-Z0-9+.\-]*:)?//")


def _anchorable_paragraphs(block: Block) -> list[str]:
    """The block's rendered human body, per kind, inline-markdown stripped, split into
    verbatim-checkable paragraphs.

    - FR/SC: the table row's *description cell* (never the `| FR-001 | … |` row syntax — no
      reader sees the pipes, and the renderer carries only the cell).
    - USER_STORY: the story prose under the heading (heading line dropped — it is the unit's
      visible lead label, checked separately as the id).
    - everything else: the block body as-is.

    Each paragraph is a blank-line-separated run; the renderer wraps each in its own `<p>`, so
    each is contiguous within the unit even when a disclosure `<summary>` interleaves the
    open lead and the collapsed depth.
    """
    if block.kind in (BlockKind.FR, BlockKind.SC) and block.ref:
        body = _row_description(block.body)
    elif block.kind is BlockKind.USER_STORY:
        body = _strip_leading_heading(block.body)
    else:
        body = block.body
    body = strip_inline_markdown(body)
    return [p.strip() for p in body.split("\n\n") if p.strip()]


def _row_description(row: str) -> str:
    """The description cell of an FR/SC markdown table row (`| FR-001 | <desc> | <src> |` →
    `<desc>`). Gate-owned *source* parsing — the row's shape is a property of the source
    markdown, not of any renderer."""
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    cells = [c for c in cells if c]
    if len(cells) >= 2:
        return cells[1]
    return cells[-1] if cells else row.strip()


def _strip_leading_heading(body: str) -> str:
    """Drop a single leading ATX heading line from a block body (the unit already shows it as
    its visible lead)."""
    lines = body.split("\n")
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    if idx < len(lines) and lines[idx].lstrip().startswith("#"):
        idx += 1
    return "\n".join(lines[idx:]).strip()


def check_html(
    html: str, parsed: ParsedRequirements, *, open_gap_questions: Sequence[str] | None = None
) -> GateReport:
    """Gate a HOW-layer HTML document against the parsed source (Steps 3b.3–3b.5).

    Dimensions, each producing prompt-ready violations:

    1. **id parity (set):** the canonical US/FR/SC tokens visible in the HTML equal the parsed
       ref set — none missing, none invented, none renamed.
    2. **per-block correspondence (FR-003 / one-unit-one-container):** each ref labels exactly one
       requirement-unit container. Owner-finding is by ANCHOR LABEL alone.
    3. **DOM + self-containment:** zero `id=` / `data-block-anchor` attributes; no external
       `src`/`href`; `data-goal-slug` on `<body>`; a real `<h2>`/`<h3>` heading hierarchy.

    **Refine-req-v3 sp3b — the blanket verbatim-carriage class is GONE.** CREATE mode now optimizes
    for the most human-readable delivery and may paraphrase/distill leaf requirement text freely; the
    old "every anchorable paragraph appears verbatim within its container" violation class is removed.
    What stays HARD: anchor labels (each canonical id printed verbatim, owned by exactly one unit) and
    the one-unit-one-container DOM rule. The reversal is safe because comments now anchor to the
    PUBLISHED RENDER snapshot (sp2), not the canonical source — so source-leaf verbatim carriage is no
    longer the load-bearing property keeping comments placeable. Owner-finding therefore drops the
    lead-text predicate it used to lean on and keys purely on the visible label.

    Phase 5a adds a further dimension when `open_gap_questions` is supplied (the open gaps the
    service resolved for THIS job): **gap-marker correspondence** — every open gap has exactly one
    `.rr-gap` marker carrying its `question` verbatim, and no `.rr-gap` exists without a matching
    gap (a gap is never silently dropped; a marker is never invented). Markers are class-based
    (the zero-`id` DOM contract above already forbids `id=`/`data-block-anchor` on them).
    """
    violations: list[str] = []
    idx = container_text_index(html)
    parsed_refs = _parsed_ref_set(parsed)

    # --- Dimension 1: id-token set equality ---
    visible_ids = {_norm_ref(t) for t in _ID_RE.findall(idx.document_text)}
    for ref in sorted(parsed_refs - visible_ids):
        violations.append(f"{ref} label missing from the render.")
    invented = sorted(visible_ids - parsed_refs)
    if invented and not parsed_refs:
        # Zero-ref contract (refine-req-v3 sp4 — the pilot_poc root-cause fix): a source with NO
        # canonical ids is a ref-less doc that MUST render with ZERO anchor labels. The gate
        # already flagged invention before this phase, but a per-id "not a source ref" line never
        # told the maker the WHOLE page must drop anchor labels, so the structural retry never
        # converged. Naming every invented id in ONE sharp, contract-stating message is the
        # feedback specificity that makes it converge.
        violations.append(
            "the source has NO canonical US/FR/SC ids — this is a ref-less doc that MUST render "
            f"with ZERO anchor labels and ZERO invented ids. Remove the invented id(s): "
            f"{', '.join(invented)}."
        )
    else:
        for ref in invented:
            violations.append(
                f"{ref} appears in the render but is not a source ref — remove this invented/"
                "renamed id (only canonical source ids may be printed as anchor labels)."
            )

    # --- Dimension 2: per-block correspondence (one-unit-one-container, FR-003) ---
    # Owner-finding is by ANCHOR LABEL alone (sp3b: the verbatim-carriage lead-text predicate is
    # gone — CREATE may paraphrase leaf text). What stays HARD: each canonical id labels exactly one
    # requirement-unit container. This is the same one-id-per-unit invariant the render-space anchor
    # resolver (`resolve_render_anchor`) already assumes, so it is consistent across the phase.
    for ref in sorted(parsed_refs & visible_ids):
        # Keep only the innermost owner of each disjoint region (drop a `<section>` owner when a
        # nested `<li>` owner already shows the id) — dedupe by collapsing ancestors.
        owners = _innermost([c for c in idx.units() if _label_in(ref, c.text)])
        if not owners:
            violations.append(
                f"{ref} is not anchored to a unit container that shows its label "
                "(per-block correspondence / FR-003 failed)."
            )
        elif len(owners) > 1:
            violations.append(
                f"{ref} is anchored to {len(owners)} different containers — each id labels "
                "exactly one block."
            )

    # --- Dimension 3: DOM + self-containment ---
    violations.extend(_check_dom_contract(html))

    # --- Dimension 5 (Phase 5a): gap-marker correspondence (only when gaps are open) ---
    violations.extend(_check_gap_markers(idx, open_gap_questions))

    # --- Dimension 6 (sp4): empty-shell detection (US2 omit-never-pad, deterministic) ---
    violations.extend(_check_empty_shells(idx))

    return _report(violations)


def _check_gap_markers(
    idx: ContainerTextIndex, open_gap_questions: Sequence[str] | None
) -> list[str]:
    """Gap-marker correspondence (Phase 5a): a 1:1 bijection between the open gaps and the page's
    `.rr-gap` markers, keyed on the `question` text.

    Reuses the single `container_text_index` walk (no second walker) — a `.rr-gap` marker is any
    container whose class set names `rr-gap`. Rules:

    - every open-gap `question` appears verbatim in **exactly one** `.rr-gap` container (0 ⇒ a gap
      silently dropped; >1 ⇒ the same gap rendered twice);
    - every `.rr-gap` container carries **exactly one** open-gap question (0 ⇒ an invented marker;
      >1 ⇒ two gaps merged into one marker).

    With no open gaps (the clean-render common case) the only rule that bites is "no stray
    `.rr-gap`" — a marker on a gapless page is an invention."""
    questions = [q for q in (open_gap_questions or []) if q]
    gap_containers = [c for c in idx.containers if "rr-gap" in c.classes]

    violations: list[str] = []
    for q in questions:
        n = sum(1 for c in gap_containers if q in c.text)
        if n == 0:
            violations.append(
                f"open gap question {_clip(q)!r} has no `.rr-gap` marker — a gap is never "
                "silently dropped."
            )
        elif n > 1:
            violations.append(
                f"open gap question {_clip(q)!r} appears in {n} `.rr-gap` markers — each gap is "
                "rendered exactly once."
            )
    for c in gap_containers:
        matched = sum(1 for q in questions if q in c.text)
        if matched == 0:
            violations.append(
                "a `.rr-gap` marker carries no open-gap question verbatim — a marker is never "
                "invented (no matching gap)."
            )
        elif matched > 1:
            violations.append(
                f"a `.rr-gap` marker carries {matched} open-gap questions — two gaps must not be "
                "merged into one marker."
            )
    return violations


# Elements that present a unit/section as a titled block — the "heading" of an empty-shell test.
_HEADING_TAGS = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})
# A word char (letter/digit/underscore) anywhere = real, non-decorative body content. Anything
# else (whitespace, dashes, bullets, ellipses, punctuation) is decoration a padded shell hides
# behind.
_WORD_RE = re.compile(r"\w")


def _check_empty_shells(idx: ContainerTextIndex) -> list[str]:
    """Empty-shell detection (refine-req-v3 sp4 — the random_idea root-cause fix, US2 omit-never-
    pad made DETERMINISTIC).

    The contract has always said "a block with no source content is OMITTED, never padded" (US2
    Scenario 2), but nothing structural enforced it — a `random_idea` render padded thin sources
    with heading-only placeholder shells and the cold-reader checker scored the padded page 1.00.
    This gate makes the rule enforceable WITHOUT touching the cold-reader checker: a unit/section
    container that presents a heading (`<h1>`–`<h6>`) but has **no non-decorative text content
    beyond that heading** is an empty placeholder shell → a prompt-ready structural violation.

    Reuses the single `container_text_index` walk (no second container-text walker): headings are
    just containers whose `tag` is `h1`–`h6`; a unit's non-heading body is its `text` with every
    enclosed heading span removed. A unit with no heading is not a "titled section" and is skipped
    (FR/SC list items label with `<strong>`, not a heading — they never trip this). A wrapper
    section whose only content is real nested units keeps those units' body text and so is never
    flagged; only a genuinely empty titled block is."""
    violations: list[str] = []
    headings = [c for c in idx.containers if c.tag in _HEADING_TAGS]
    for unit in idx.units():
        inner = sorted(
            (h for h in headings if unit.start <= h.start and h.end <= unit.end),
            key=lambda h: h.start,
        )
        if not inner:
            continue  # not a titled section — nothing claiming to be a heading-led block
        # Body = the unit's text with every enclosed heading span carved out (offsets are relative
        # to the unit's own slice). `cursor`/`max` collapses nested or adjacent heading spans.
        base = unit.start
        parts: list[str] = []
        cursor = 0
        for h in inner:
            s, e = h.start - base, h.end - base
            if s > cursor:
                parts.append(unit.text[cursor:s])
            cursor = max(cursor, e)
        parts.append(unit.text[cursor:])
        body = "".join(parts)
        if not _WORD_RE.search(body):
            title = _clip(inner[0].text) or unit.tag
            violations.append(
                f"empty shell: the `{unit.tag}` block titled {title!r} has a heading but no "
                "non-decorative body content — omit an empty block, never pad it with a "
                "placeholder section (US2)."
            )
    return violations


def _label_in(ref: str, text: str) -> bool:
    """Whether the canonical id `ref` appears as a token in `text` (US-1/US1 tolerant)."""
    return any(_norm_ref(t) == ref for t in _ID_RE.findall(text))


def _innermost(owners: list[Container]) -> list[Container]:
    """Collapse owner containers that nest inside another owner — keep only the innermost of
    each nesting chain so a unit `<li>` inside a unit `<section>` counts as one owner."""
    kept: list[Container] = []
    for c in owners:
        if any(o is not c and c.start <= o.start and o.end <= c.end and o.depth > c.depth
               for o in owners):
            continue  # c is an ancestor of a deeper owner — drop it
        # also skip exact-duplicate spans
        if any(k.start == c.start and k.end == c.end for k in kept):
            continue
        kept.append(c)
    return kept


# --------------------------------------------------------------------------------------
# check_update_fidelity — the UPDATE-splice fidelity gate (refine-req-v3 sp3b)
# --------------------------------------------------------------------------------------
def check_update_fidelity(
    html: str, prior_html: str, unchanged_refs: Sequence[str]
) -> GateReport:
    """Verify the UPDATE render kept every UNCHANGED unit container byte-identical to the prior
    render (1a verdict: **FAIL → deterministic-splice**, `spikes/update-fidelity/verdict.md`).

    The 1a spike proved the production HOW agent paraphrases ~10% of *unchanged* narrative cells even
    under a literal copy-exact instruction — and every divergence was a true reword (whitespace-only
    = 0), so a gate-enforced-LLM-copy mechanism could not converge and a NORMALIZED-text comparison
    could not rescue it. The binding consequence: the SERVER keeps the prior render's unchanged
    unit-container bytes verbatim and splices in HOW-rendered changed fragments (`block_splice`).
    Byte-identity is then a **construction** guarantee, not an LLM obligation — and this gate
    VERIFIES the construction: it catches a splice BUG, never a paraphrase.

    Comparison granularity (plan-review Decision #3): **RAW unit-element bytes**, because raw-byte
    identity is precisely what the splice guarantees — the comparison holds the server's own assembly
    to its contract. (The unreachable gate-enforced-LLM-copy branch — 1a PASS — would instead compare
    NORMALIZED container text via `container_text_index`; 1a returned FAIL, so that branch is dead and
    a raw-byte gate here does NOT thrash on LLM serialization noise, since the bytes are the server's.)

    `unchanged_refs` is the canonical-id set of units NOT in the changed-set. For each labeled unit on
    BOTH renders, the raw HTML must be identical. A ref absent from the prior render (never a labeled
    unit there) is skipped — nothing to hold identical. Pure; violations are prompt-ready.
    """
    from .block_splice import segment_units  # lazy: block_splice imports this module (avoid cycle)

    prior_by_ref = {s.ref: s.html for s in segment_units(prior_html) if s.ref is not None}
    new_by_ref = {s.ref: s.html for s in segment_units(html) if s.ref is not None}
    violations: list[str] = []
    for ref in sorted({_norm_ref(r) for r in unchanged_refs}):
        prior_seg = prior_by_ref.get(ref)
        if prior_seg is None:
            continue  # not a labeled unit on the prior render — nothing to hold byte-identical
        new_seg = new_by_ref.get(ref)
        if new_seg is None:
            violations.append(
                f"update fidelity: unchanged unit {ref} is missing from the spliced render."
            )
        elif new_seg != prior_seg:
            violations.append(
                f"update fidelity: unchanged unit {ref} was not kept byte-identical to the prior "
                "render (splice construction failed)."
            )
    return _report(violations)


def _clip(text: str, limit: int = 60) -> str:
    """Trim a violation excerpt so the prompt-ready string stays short."""
    flat = " ".join(text.split())
    return flat if len(flat) <= limit else flat[: limit - 1] + "…"


class _AttrScanner(HTMLParser):
    """Collect the attribute-level DOM facts the self-containment contract turns on: real
    `id`/`data-block-anchor` attributes (NOT prose mentions), every `src`/`href` URL, the
    `<body>` `data-goal-slug` presence, and whether any `<h2>`/`<h3>` exists."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.id_attrs = 0
        self.block_anchor_attrs = 0
        self.urls: list[str] = []
        self.body_has_slug = False
        self.has_heading = False

    def _scan(self, tag: str, attrs: list) -> None:
        names = {k for k, _ in attrs}
        if "id" in names:
            self.id_attrs += 1
        if "data-block-anchor" in names:
            self.block_anchor_attrs += 1
        for k, v in attrs:
            if k in ("src", "href") and v:
                self.urls.append(v)
        if tag == "body" and "data-goal-slug" in names:
            self.body_has_slug = True
        if tag in ("h2", "h3"):
            self.has_heading = True

    def handle_starttag(self, tag: str, attrs: list) -> None:
        self._scan(tag, attrs)

    def handle_startendtag(self, tag: str, attrs: list) -> None:
        self._scan(tag, attrs)


def _check_dom_contract(html: str) -> list[str]:
    """The zero-`id` / self-containment / `data-goal-slug` / heading checks (Step 3b.5).

    Attribute-based (parse tree), so escaped requirement text quoting `id=` or
    `data-block-anchor` as *content* (FR-003's own source) is never mistaken for an attribute.
    """
    violations: list[str] = []
    scanner = _AttrScanner()
    scanner.feed(html)
    scanner.close()

    if scanner.id_attrs:
        violations.append(
            f"{scanner.id_attrs} element(s) carry an `id=` attribute — the canonical render "
            "has none (logical id backbone is visible text, never a DOM id)."
        )
    if scanner.block_anchor_attrs:
        violations.append(
            f"{scanner.block_anchor_attrs} element(s) carry a `data-block-anchor` attribute — "
            "the render must not use block-anchor attributes."
        )
    for url in scanner.urls:
        if _EXTERNAL_URL_RE.match(url):
            violations.append(
                f"external resource {url!r} — the page must be self-contained (no CDN fonts / "
                "external scripts; CSS inline)."
            )
    if not scanner.body_has_slug:
        violations.append("`<body>` is missing the `data-goal-slug` attribute.")
    if not scanner.has_heading:
        violations.append("no `<h2>`/`<h3>` heading hierarchy — units must sit under real headings.")

    return violations


# --------------------------------------------------------------------------------------
# check_comment_survival — the comment-survival gate (Phase 4b-1, pure)
# --------------------------------------------------------------------------------------
class SurvivalReport(TypedDict):
    """The frozen comment-survival result shape (shared-context contract).

    - ``passed`` — ``False`` IFF >=1 **structural** miss (an unchanged-block render miss, or a
      legacy in-block source miss). An EXPECTED miss (render comment on a changed block) and a
      cross-boundary miss never flip it.
    - ``violations`` — prompt-ready strings, structural misses only (the service merges these into
      the existing `html_report.violations` structural channel).
    - ``unplaced`` — comment ids that did NOT place (structural + expected + cross-boundary misses).
    - ``placed`` — comment ids that placed.
    - ``expected_misses`` — render-space comment ids that missed on a CHANGED (modified/removed)
      block: expected by construction (the block was re-rendered / dropped), NEVER a violation,
      routed to the publish-boundary `cast-comment-reanchor` v3 dispatch (refine-req-v3 sp3b).
    """

    passed: bool
    violations: list[str]
    unplaced: list[int]
    placed: list[int]
    expected_misses: list[int]


def _classify_owner_ref(quote: str, anchorable: dict[str, list[str]]) -> str | None:
    """The canonical ref of the block whose **anchorable text** contains `quote`, or None when
    the quote is not within any single block's anchorable body (⇒ cross-boundary).

    Source-side classification (the `anchorable` map is precomputed from `parsed`, never the
    candidate DOM): a quote that is a substring of one block's anchorable paragraph is **in-block**
    — by the verbatim-carriage clause that paragraph is carried contiguously inside the owning
    unit, so any substring of it MUST place. A quote spanning the heading↔body seam, two blocks,
    a markdown-strip seam, or render decoration is **cross-boundary** (best-effort, never a
    violation — it can fail on the deterministic substrate too)."""
    if not quote:
        return None
    for ref, paragraphs in anchorable.items():
        if any(quote in para for para in paragraphs):
            return ref
    return None


def _places_in_owner(idx: ContainerTextIndex, quote: str, ref: str) -> bool:
    """1b placement semantics for an in-block quote: does `quote` appear in the candidate DOM
    inside a unit container that shows `ref`'s label? Scans every occurrence (first-match
    `indexOf`, byte-faithful) — a hit is valid only when it lands in `ref`'s own container, so a
    coincidental echo of the same text in a different unit never counts as placement."""
    start = 0
    while True:
        at = idx.document_text.find(quote, start)
        if at == -1:
            return False
        unit = idx.unit_at(at)
        if unit is not None and _label_in(ref, unit.text):
            return True
        start = at + 1


def _places_in_render(idx: ContainerTextIndex, quote: str, block_ref: str | None) -> bool:
    """Render-space placement (refine-req-v3 sp3b). A render-space comment survives iff its quote
    places inside the SAME labeled unit container its `block_ref` named — or, for a ref-less render
    anchor (`block_ref is None`, the `pilot_poc`/`random_idea` ref-less page, Decision #1), iff the
    quote places anywhere on the served render. Reuses the 1b `_places_in_owner` byte-faithful scan
    for the ref-bearing case (no second walker)."""
    if not quote:
        return False
    if block_ref is None:
        return idx.find(quote) != -1
    return _places_in_owner(idx, quote, block_ref)


def check_comment_survival(
    html: str,
    parsed: ParsedRequirements,
    comments: Sequence[dict],
    *,
    changed_refs: Sequence[str] = (),
) -> SurvivalReport:
    """Pure: does each OPEN comment's verbatim quote place on this candidate maker DOM?

    `comments` is a plain sequence of `{id, quoted_text, block_ref?, anchor_space?}` (the gate stays
    I/O-free — the service fetches the open comments and maps them). `changed_refs` is the canonical
    id set of CHANGED (added/modified/removed) units this UPDATE re-rendered (empty on a CREATE).
    Returns the `SurvivalReport`.

    **Render-space classification (sp3b — the reorientation).** A comment with `anchor_space='render'`
    survives iff its quote places inside the same `block_ref` container on the candidate render:
    - **unchanged block** (`block_ref` not in `changed_refs`) — UPDATE byte-identity makes a miss
      impossible on the happy path, so a miss is a real **structural violation** (`passed=False`).
    - **changed block** (`block_ref` in `changed_refs`) — the block was re-rendered or dropped, so a
      miss is **expected**: recorded in `expected_misses` + `unplaced`, NEVER a violation, routed to
      the publish-boundary re-anchor dispatch.
    - **ref-less render anchor** (`block_ref is None`) — places anywhere on the render (Decision #1);
      a miss is best-effort (cross-boundary / displaced), recorded in `unplaced` + badged read-time,
      NEVER a structural violation and never routed to re-anchor (there is no bridge ref to key on).

    **Legacy source-space classification** (a comment not yet migrated, `anchor_space != 'render'`)
    keeps the prior behaviour exactly: in-block (substring of a block's source anchorable text) MUST
    place → a miss is a violation; cross-boundary is best-effort, never a violation.

    Single-walk discipline (P1): walk the candidate HTML **once** via `container_text_index`;
    precompute each block's anchorable paragraphs **once per pass** for the legacy path.
    """
    idx = container_text_index(html)
    anchorable = {
        _norm_ref(b.ref): _anchorable_paragraphs(b) for b in parsed.blocks if b.ref
    }
    changed = {_norm_ref(r) for r in changed_refs}

    violations: list[str] = []
    unplaced: list[int] = []
    placed: list[int] = []
    expected_misses: list[int] = []

    for comment in comments:
        cid = comment["id"]
        quote = comment.get("quoted_text") or ""

        if comment.get("anchor_space") == "render":
            block_ref = comment.get("block_ref")
            norm_ref = _norm_ref(block_ref) if block_ref else None
            if _places_in_render(idx, quote, norm_ref):
                placed.append(cid)
                continue
            unplaced.append(cid)
            if norm_ref is None:
                # No resolved bridge ref (a cross-boundary / decoration-spanning / displaced quote).
                # Best-effort, never a structural violation — surfaced read-time via the badge only
                # (the render-space analogue of the legacy cross-boundary class; Decision #1).
                pass
            elif norm_ref in changed:
                # CHANGED (modified/removed) block → expected miss; never a violation, routed to
                # the publish-boundary re-anchor dispatch.
                expected_misses.append(cid)
            else:
                # Resolved ref on an UNCHANGED block that missed → a real structural failure (UPDATE
                # byte-identity makes this impossible on the happy path).
                violations.append(
                    f"comment {cid}'s render anchor {_clip(quote)!r} did not survive on "
                    f"{block_ref}'s container (unchanged block)."
                )
            continue

        # --- Legacy source-space path (unchanged behaviour) ---
        owner_ref = _classify_owner_ref(quote, anchorable)
        if owner_ref is not None:
            if _places_in_owner(idx, quote, owner_ref):
                placed.append(cid)
            else:
                unplaced.append(cid)
                violations.append(
                    f"comment {cid}'s anchor {_clip(quote)!r} missing from "
                    f"{owner_ref}'s container"
                )
        else:
            if quote and idx.find(quote) != -1:
                placed.append(cid)
            else:
                unplaced.append(cid)

    return SurvivalReport(
        passed=not violations, violations=violations, unplaced=unplaced, placed=placed,
        expected_misses=expected_misses,
    )
