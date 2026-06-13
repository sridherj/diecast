"""Turn a `refined_requirements.collab.md` file into an ordered, typed block model.

This is a RENDER model, NOT a comment-anchoring index. Deliberate non-goals:

- Blocks do NOT tile the file. Table headers, dividers, and intro prose between landmarks
  live only in `source_text`; they are not emitted as blocks.
- Inline `[NEEDS CLARIFICATION]` markers inside a user story stay inside that USER_STORY
  block's body. Only the Open Questions section emits OPEN_QUESTION blocks.
- `Block.ref` is parsed in memory only — never persisted to a DB column, never used as a
  comment anchor.

Unknown H2 sections are recorded in `ParsedRequirements.unrecognized_sections` (a tuple) and
emit no block — there are zero silent failures.

The grammar (section/US/FR/SC regexes and the section-span algorithm) is bridged from
`bin/cast-spec-checker` via `spec_grammar`, so this parser can never drift from the FR-007
checker. This module is READ-ONLY: it never writes the file.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from . import spec_grammar as g
from .blocks import Block, BlockKind, ParsedRequirements
from .hashing import content_hash

# A top-level (column-0) markdown list marker. Continuation lines, wrapped text, and nested
# (indented) sub-bullets do NOT match — so a bullet block runs from one top-level marker to
# the next, grouping its continuations and nested children (plan-review Decision #4).
_TOP_BULLET_RE = re.compile(r"^[-*]\s+\S")
_H1_RE = re.compile(r"^#\s+(.+?)\s*$")


def _section_spans(lines: list[str]) -> dict[str, tuple[int, int]]:
    """H2 name -> (start_line, end_line) inclusive, 1-indexed. Reuses the checker's
    algorithm when exposed; the inlined fallback is byte-identical to it."""
    if g._section_spans is not None:
        return g._section_spans(lines)
    spans: dict[str, tuple[int, int]] = {}
    current: tuple[str, int] | None = None
    for idx, raw in enumerate(lines, start=1):
        m = g.SECTION_HEADING_RE.match(raw.rstrip())
        if not m:
            continue
        name = m.group(1).strip()
        if current is not None:
            spans[current[0]] = (current[1], idx - 1)
        current = (name, idx)
    if current is not None:
        spans[current[0]] = (current[1], len(lines))
    return spans


def _trim_trailing_blank(lines: list[str], start: int, end: int) -> int:
    """Return the last non-blank line number in [start, end] (1-indexed, inclusive).
    Keeps block bodies from swallowing trailing blank lines that belong to the gap."""
    last = start
    for ln in range(start, end + 1):
        if lines[ln - 1].strip():
            last = ln
    return last


def _slice_body(lines: list[str], start: int, end: int) -> str:
    """Byte-faithful source slice for line range [start, end] inclusive (1-indexed).
    `lines` is `source_text.split("\\n")`, so join-by-"\\n" reproduces the exact substring."""
    return "\n".join(lines[start - 1 : end])


def _parse_front_matter(text: str) -> tuple[dict, int]:
    """Parse a leading `---`-fenced YAML header. Returns (front_matter, body_start_line)
    where body_start_line is the 1-indexed line where content after the header begins
    (1 when there is no header)."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, 1
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            raw = "\n".join(lines[1:idx])
            try:
                parsed = yaml.safe_load(raw) or {}
            except yaml.YAMLError:
                parsed = {}
            if not isinstance(parsed, dict):
                parsed = {}
            return parsed, idx + 2  # line after the closing fence (1-indexed)
    return {}, 1  # unterminated fence — treat as no front matter


def _extract_title_and_preamble(
    lines: list[str], body_start: int, first_section_line: int | None
) -> tuple[str, str]:
    """Title = the H1 text; preamble = the text between the H1 and the first H2 (the
    spec-maturity blockquote etc.), stripped of surrounding blank lines."""
    upper = first_section_line if first_section_line is not None else len(lines) + 1
    title = ""
    h1_line: int | None = None
    for ln in range(body_start, upper):
        m = _H1_RE.match(lines[ln - 1])
        if m:
            title = m.group(1).strip()
            h1_line = ln
            break
    if h1_line is None:
        return title, ""
    preamble = "\n".join(lines[h1_line : upper - 1]).strip()
    return title, preamble


def _emit_user_stories(lines: list[str], start: int, end: int) -> list[Block]:
    """One USER_STORY block per US heading, spanning to the next US heading or section end."""
    heads: list[tuple[int, str, str]] = []  # (line_no, ref, heading_text)
    for ln in range(start + 1, end + 1):
        m = g.US_HEADING_RE.match(lines[ln - 1].rstrip())
        if m:
            heading_text = lines[ln - 1].lstrip("#").strip()
            heads.append((ln, m.group(1), heading_text))
    blocks: list[Block] = []
    for i, (ln, ref, heading_text) in enumerate(heads):
        block_end = (heads[i + 1][0] - 1) if i + 1 < len(heads) else end
        block_end = _trim_trailing_blank(lines, ln, block_end)
        blocks.append(
            Block(
                kind=BlockKind.USER_STORY,
                level=2,
                body=_slice_body(lines, ln, block_end),
                heading=heading_text,
                ref=ref,
                line_start=ln,
                line_end=block_end,
            )
        )
    return blocks


def _emit_id_rows(
    lines: list[str], start: int, end: int, kind: BlockKind, id_re: re.Pattern, prefix: str
) -> list[Block]:
    """One block per table row matching `id_re` (FR / SC). body = the row line."""
    blocks: list[Block] = []
    for ln in range(start + 1, end + 1):
        m = id_re.search(lines[ln - 1])
        if m:
            blocks.append(
                Block(
                    kind=kind,
                    level=2,
                    body=lines[ln - 1],
                    heading=None,
                    ref=f"{prefix}-{m.group(1)}",
                    line_start=ln,
                    line_end=ln,
                )
            )
    return blocks


def _emit_bullets(lines: list[str], start: int, end: int, kind: BlockKind) -> list[Block]:
    """One block per top-level bullet, grouping continuation lines and nested sub-bullets
    (plan-review Decision #4). Intro prose before the first bullet stays only in source_text."""
    marker_lines = [
        ln for ln in range(start + 1, end + 1) if _TOP_BULLET_RE.match(lines[ln - 1])
    ]
    blocks: list[Block] = []
    for i, ln in enumerate(marker_lines):
        block_end = (marker_lines[i + 1] - 1) if i + 1 < len(marker_lines) else end
        block_end = _trim_trailing_blank(lines, ln, block_end)
        blocks.append(
            Block(
                kind=kind,
                level=2,
                body=_slice_body(lines, ln, block_end),
                heading=None,
                ref=None,
                line_start=ln,
                line_end=block_end,
            )
        )
    return blocks


def _emit_whole_section(
    lines: list[str], start: int, end: int, kind: BlockKind, heading: str
) -> list[Block]:
    """ONE level-1 block covering the whole section (Intent, Directional)."""
    block_end = _trim_trailing_blank(lines, start, end)
    return [
        Block(
            kind=kind,
            level=1,
            body=_slice_body(lines, start, block_end),
            heading=heading,
            ref=None,
            line_start=start,
            line_end=block_end,
        )
    ]


def parse_requirements(text: str) -> ParsedRequirements:
    lines = text.split("\n")
    front_matter, body_start = _parse_front_matter(text)
    spans = _section_spans(lines)

    # Sections in source order.
    ordered = sorted(spans.items(), key=lambda kv: kv[1][0])
    first_section_line = ordered[0][1][0] if ordered else None
    title, preamble = _extract_title_and_preamble(lines, body_start, first_section_line)

    blocks: list[Block] = []
    unrecognized: list[str] = []
    for name, (start, end) in ordered:
        if name == "Intent":
            blocks += _emit_whole_section(lines, start, end, BlockKind.INTENT, name)
        elif name == "User Stories":
            blocks += _emit_user_stories(lines, start, end)
        elif name == "Functional Requirements":
            blocks += _emit_id_rows(lines, start, end, BlockKind.FR, g.FR_ID_RE, "FR")
        elif name == "Success Criteria":
            blocks += _emit_id_rows(lines, start, end, BlockKind.SC, g.SC_ID_RE, "SC")
        elif name == "Evidence":
            blocks += _emit_whole_section(lines, start, end, BlockKind.EVIDENCE, name)
        elif name == "Decisions":
            blocks += _emit_whole_section(lines, start, end, BlockKind.DECISION, name)
        elif name == "Constraints":
            blocks += _emit_bullets(lines, start, end, BlockKind.CONSTRAINT)
        elif name == "Out of Scope":
            blocks += _emit_bullets(lines, start, end, BlockKind.SCOPE)
        elif name.startswith("Directional"):
            blocks += _emit_whole_section(lines, start, end, BlockKind.DIRECTIONAL, name)
        elif name == "Open Questions":
            blocks += _emit_bullets(lines, start, end, BlockKind.OPEN_QUESTION)
        else:
            unrecognized.append(name)

    return ParsedRequirements(
        title=title,
        front_matter=front_matter,
        preamble=preamble,
        blocks=tuple(blocks),
        unrecognized_sections=tuple(unrecognized),
        source_text=text,
        content_hash=content_hash(text),
    )


def parse_requirements_file(path: Path) -> ParsedRequirements:
    """Read `path` (UTF-8) and parse it. READ-ONLY — never writes."""
    text = Path(path).read_text(encoding="utf-8")
    return parse_requirements(text)
