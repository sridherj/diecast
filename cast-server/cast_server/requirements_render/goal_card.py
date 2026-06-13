"""The information-architecture core of the SC-001 surface (Phase 3a, sp3, WP-C).

These two pure heuristics decide what the zero-click Goal Card *says* — the one job
statement and the 3–5 outcome/boundary assertions an unfamiliar reader restates in the
2-minute test. They are deliberately isolated from ``renderer.py`` (plan-review #3): the
SC-001 core must be unit-testable without rendering a full document.

Hard rules (decisions doc + plan):
- **Pure & deterministic.** Functions of ``ParsedRequirements`` only — no I/O, no DB, no
  timestamps. Inline-markdown markers (``**bold**``, ``` `code` ```, ``[t](u)``) are
  **stripped to plain text** for Goal-Card display by ``strip_inline_markdown`` — a pure text
  transform, **never rendered** to HTML. ``renderer.py`` *calls* these functions and owns the
  HTML.
- **Never pad.** ``derive_l2_assertions`` returns *fewer than three* when fewer than three
  exist. A sparse card is honest; an invented assertion is a lie to the reader (Step 3.2).
- **Loud on absence.** ``extract_job_statement`` emits a render warning when it cannot find
  a job statement — that warning is the renderer's only lever on authoring quality.
"""
from __future__ import annotations

import re

from .blocks import Block, BlockKind, ParsedRequirements

# Maximum number of L2 assertions on the Goal Card. Five is the comprehension ceiling — more
# than this stops being a glance and becomes reading (Step 3.2 / objective).
MAX_L2_ASSERTIONS = 5

# The warning emitted when no job statement can be derived — the loud authoring-quality
# signal (Execution Notes). Threaded into ``RenderResult.warnings`` by ``renderer.py`` and
# surfaced per-family by sp5a's eval.
NO_JOB_STATEMENT_WARNING = "no job statement — SC-001 at risk"

# A bolded `**Job statement:** <text>` lead inside the Intent block. DOTALL so the statement
# may wrap onto the next line; `_first_sentence` then trims it to a single sentence.
_BOLD_JOB_RE = re.compile(
    r"\*\*\s*job statement\s*:?\s*\*\*\s*:?\s*(.+)", re.IGNORECASE | re.DOTALL
)
# Sentence boundary: a `.`/`!`/`?` followed by whitespace.
_SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+")
# A top-level enumerated / bulleted list item: `1.`, `2)`, `-`, `*` …
_LIST_ITEM_RE = re.compile(r"^\s*(?:\d+[.)]|[-*])\s+(.+)$")
# A leading list marker to strip from a single line of text.
_LEADING_MARKER_RE = re.compile(r"^\s*(?:\d+[.)]|[-*])\s+")

# Inline-markdown markers are *stripped* (not rendered) for Goal-Card display — see the
# module docstring's purity rule. Paired-delimiter regexes only: a lone `*`/`_`/`` ` `` or an
# unbalanced `**a` passes through untouched. Link parsing is deliberately simple
# (non-greedy) — a parenthesized URL like `[t](http://x(y))` leaves a stray `)`; that is an
# accepted, test-pinned degradation (YAGNI for requirements prose).
_STRIP_PASSES = (
    re.compile(r"\*\*(.+?)\*\*"),
    re.compile(r"__(.+?)__"),
    re.compile(r"\*(.+?)\*"),
    re.compile(r"_(.+?)_"),
    re.compile(r"`(.+?)`"),
    re.compile(r"\[(.+?)\]\((.+?)\)"),
)
# Strong-before-em ordering (`**`/`__` before `*`/`_`) so `**bold**` isn't mis-split by the
# em pass. The link pass keeps only its first group (`\1` = the link text).
_MAX_STRIP_PASSES = 5

# Trailing dotted tokens that look like a sentence boundary but are not. Compared against the
# full whitespace-delimited token ending at the candidate period, lowercased, with leading
# bracket/quote punctuation trimmed (so `(e.g.` matches `e.g.`). Easily extended; frozen so
# goldens stay byte-stable run-to-run. A sentence genuinely ending in one of these (e.g.
# `... etc.`) runs long into the next sentence — an over-long statement is honest; a truncated
# one is wrong (accepted tradeoff).
_ABBREVIATIONS = frozenset({
    "vs.", "e.g.", "i.e.", "etc.", "cf.", "ca.", "approx.",
    "min.", "hr.", "hrs.", "sec.", "no.", "fig.", "al.",
})
_LEADING_TOKEN_PUNCT = "([{\"'"


def strip_inline_markdown(text: str) -> str:
    """Strip inline-markdown markers for Goal-Card plain-text display (pure).

    Removes paired ``**bold**`` / ``__bold__`` / ``*em*`` / ``_em_`` / ``` `code` ``` markers
    and rewrites ``[text](url)`` to ``text``, keeping the inner text. A lone or unbalanced
    marker (``a * b``, ``**a``) passes through unchanged. Nested markers
    (``**a *b* c**`` → ``a b c``) are handled by iterating to a fixpoint, capped at
    ``_MAX_STRIP_PASSES`` passes (negligible cost at card-text scale).

    This is a *pure* function of its argument — no I/O, no state — and an import-stable public
    contract for downstream phases (``maker_gate.py``). Do not make it depend on render state.
    """
    for _ in range(_MAX_STRIP_PASSES):
        before = text
        for pattern in _STRIP_PASSES:
            text = pattern.sub(r"\1", text)
        if text == before:
            break
    return text


# --- Public heuristic #1: the L1 job statement ----------------------------------------
def extract_job_statement(parsed: ParsedRequirements) -> tuple[str, str | None]:
    """Derive the one-sentence job statement for the Goal Card (Step 3.1).

    Deterministic priority:
      1. the bolded ``**Job statement:**`` lead inside the ``Intent`` block, if present;
      2. else the Intent's first sentence;
      3. else **emit a warning** and fall back to the H1 title.

    Returns ``(statement, warning_or_None)`` so ``renderer.py`` can thread any warning into
    ``RenderResult.warnings`` (the renderer's only lever on authoring quality).
    """
    intent = _intent_block(parsed)
    if intent is not None:
        body = _strip_leading_heading(intent.body)
        match = _BOLD_JOB_RE.search(body)
        if match:
            statement = _first_sentence(match.group(1))
            if statement:
                return strip_inline_markdown(statement), None
        statement = _first_sentence(body)
        if statement:
            return strip_inline_markdown(statement), None

    title = parsed.title or "Untitled goal"
    return title, NO_JOB_STATEMENT_WARNING


# --- Public heuristic #2: the 3–5 L2 assertions ---------------------------------------
def derive_l2_assertions(parsed: ParsedRequirements) -> list[str]:
    """Derive up to five L2 assertions for the Goal Card — **never padded** (Step 3.2).

    Deterministic priority order, concatenated and capped at five:
      1. Success-Criteria rows (the criterion text — the *outcomes*);
      2. Out-of-Scope bullets (the lead phrase, framed as *boundaries*);
      3. only when neither of the above exists (the ``bug_fix`` / ``random_idea`` shape):
         the Intent's enumerated thread / numbered-list items.

    Fewer than three available ⇒ return what exists. A sparse card is honest.
    """
    assertions: list[str] = []

    for block in _blocks_of_kind(parsed, BlockKind.SC):
        criterion = _table_cell(block.body, 1)
        if criterion:
            assertions.append(strip_inline_markdown(criterion))

    for block in _blocks_of_kind(parsed, BlockKind.SCOPE):
        lead = _first_sentence(_strip_leading_marker(block.body))
        if lead:
            assertions.append(f"Out of scope: {strip_inline_markdown(lead)}")

    # The intent-thread fallback fires only for families whose recipe carries neither SC nor
    # Out-of-Scope (bug_fix, random_idea): when nothing has been collected yet.
    if not assertions:
        intent = _intent_block(parsed)
        if intent is not None:
            assertions.extend(
                strip_inline_markdown(item)
                for item in _enumerated_items(_strip_leading_heading(intent.body))
            )

    return assertions[:MAX_L2_ASSERTIONS]


# --- Small pure helpers ----------------------------------------------------------------
def _intent_block(parsed: ParsedRequirements) -> Block | None:
    """The first ``INTENT`` block, or ``None`` when the document has no Intent section."""
    for block in parsed.blocks:
        if block.kind is BlockKind.INTENT:
            return block
    return None


def _blocks_of_kind(parsed: ParsedRequirements, kind: BlockKind) -> list[Block]:
    """Every block of ``kind`` in source order."""
    return [block for block in parsed.blocks if block.kind is kind]


def _strip_leading_heading(body: str) -> str:
    """Drop a single leading ATX heading line (`## Intent`) — the section already carries it
    as its heading. Mirrors ``renderer._strip_leading_heading`` (kept local to avoid a cycle:
    ``renderer`` imports this module, never the reverse)."""
    lines = body.split("\n")
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    if idx < len(lines) and lines[idx].lstrip().startswith("#"):
        idx += 1
    return "\n".join(lines[idx:]).strip()


def _strip_leading_marker(text: str) -> str:
    """Strip a single leading list marker (`- `, `* `, `1. `) from a bullet body."""
    return _LEADING_MARKER_RE.sub("", text.strip(), count=1)


def _first_sentence(text: str) -> str:
    """The first sentence of ``text`` (first paragraph, list marker stripped, whitespace
    collapsed). Returns ``""`` when there is nothing usable."""
    text = text.strip()
    if not text:
        return ""
    paragraph = text.split("\n\n", 1)[0].strip()
    paragraph = _strip_leading_marker(paragraph)
    paragraph = " ".join(paragraph.split())
    if not paragraph:
        return ""
    return _split_first_sentence(paragraph)


def _split_first_sentence(paragraph: str) -> str:
    """Return ``paragraph`` up to its first *real* sentence boundary, skipping boundaries that
    fall after a known abbreviation (``vs.``, ``e.g.``, ``30 min.``).

    Pure candidate-scan over ``_SENTENCE_END_RE``: for each ``.``/``!``/``?`` boundary, take the
    whitespace-delimited token ending at it, lowercase it, strip leading bracket/quote
    punctuation (so ``(e.g.`` normalizes to ``e.g.``), and skip the boundary when the result is
    in ``_ABBREVIATIONS``. The first non-skipped boundary ends the sentence; if none is found,
    the whole paragraph is returned (over-long-but-honest, never truncated mid-abbreviation).
    """
    for match in _SENTENCE_END_RE.finditer(paragraph):
        head = paragraph[: match.start()]
        token = head.split()[-1] if head.split() else ""
        normalized = token.lower().lstrip(_LEADING_TOKEN_PUNCT)
        if normalized in _ABBREVIATIONS:
            continue
        return head.strip()
    return paragraph.strip()


def _table_cell(row: str, index: int) -> str:
    """The ``index``-th non-empty cell of a markdown table row, or ``""``.

    ``| SC-001 | <criterion> | <measure> |`` with ``index=1`` → the criterion cell.
    """
    cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
    cells = [cell for cell in cells if cell]
    if 0 <= index < len(cells):
        return cells[index]
    return ""


def _enumerated_items(text: str) -> list[str]:
    """Every top-level enumerated / bulleted list item in ``text``, first sentence each, in
    source order. The Intent-thread fallback for SC-less, scope-less families (Step 3.2)."""
    items: list[str] = []
    for line in text.split("\n"):
        match = _LIST_ITEM_RE.match(line)
        if match:
            sentence = _first_sentence(match.group(1))
            if sentence:
                items.append(sentence)
    return items
