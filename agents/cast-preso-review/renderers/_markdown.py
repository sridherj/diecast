"""Shared markdown helpers for renderers.

Kept stdlib-only. 1b (narrative + what) and 1c (decisions) both reuse
``_slugify``, ``md_to_blocks``, and ``parse_frontmatter``.
"""

from __future__ import annotations

import html as html_lib
import re
from typing import Any

try:  # Optional: use the ``markdown`` package if the repo already has it.
    import markdown as _markdown_lib  # type: ignore

    def _md_to_html(text: str) -> str:
        return _markdown_lib.markdown(text, extensions=["tables", "fenced_code"])

except ImportError:  # Fallback: preserve structure inside <pre> for readability.

    def _md_to_html(text: str) -> str:
        return f"<pre class=\"md-fallback\">{html_lib.escape(text)}</pre>"


SLUG_STRIP_RE = re.compile(r"[^\w\s-]")
SLUG_DASH_RE = re.compile(r"[\s_-]+")


def slugify(text: str, *, max_len: int = 60) -> str:
    slug = SLUG_STRIP_RE.sub("", text.lower()).strip()
    slug = SLUG_DASH_RE.sub("-", slug)
    return slug[:max_len].strip("-") or "section"


def render_markdown(text: str) -> str:
    return _md_to_html(text)


# --- Block splitter --------------------------------------------------------
#
# Split a markdown body into block-sized chunks:
#   - Fenced code blocks (``` ... ```) kept whole.
#   - Tables (a run of lines starting with ``|``) kept whole.
#   - Lists (a run of lines starting with ``- ``, ``* ``, or ``N.``) kept whole.
#   - Everything else: paragraphs split on blank lines.


_FENCE_RE = re.compile(r"^```")
_TABLE_LINE_RE = re.compile(r"^\s*\|")
_LIST_LINE_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+\.\s+)")


def _block_type(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return "blank"
    if _FENCE_RE.match(stripped):
        return "fence"
    if _TABLE_LINE_RE.match(line):
        return "table"
    if _LIST_LINE_RE.match(line):
        return "list"
    return "prose"


def _split_raw_blocks(body: str) -> list[tuple[str, str]]:
    """Return a list of (block_type, raw_markdown) tuples.

    Preserves source ordering. Skips the body-leading blank lines.
    """
    blocks: list[tuple[str, str]] = []
    lines = body.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        btype = _block_type(line)
        if btype == "blank":
            i += 1
            continue
        if btype == "fence":
            start = i
            i += 1
            while i < n and not _FENCE_RE.match(lines[i].strip()):
                i += 1
            if i < n:
                i += 1  # include closing fence
            blocks.append(("code", "\n".join(lines[start:i])))
            continue
        if btype in ("table", "list"):
            start = i
            while i < n and _block_type(lines[i]) == btype:
                i += 1
            blocks.append((btype, "\n".join(lines[start:i]).rstrip()))
            continue
        # prose paragraph — accumulate until blank or a non-prose line
        start = i
        while i < n and _block_type(lines[i]) == "prose":
            i += 1
        blocks.append(("prose", "\n".join(lines[start:i]).rstrip()))
    return blocks


def md_to_blocks(slide_id: str, body: str) -> list[dict[str, Any]]:
    """Split body into block dicts.

    Each block: ``{"id": f"{slide_id}/block-NN", "type": ..., "html": ..., "markdown": ...}``.
    Empty bodies produce a single placeholder block so the shell renders a box.
    """
    raw = _split_raw_blocks(body)
    if not raw:
        return [
            {
                "id": f"{slide_id}/block-00",
                "type": "prose",
                "html": "",
                "markdown": "",
            }
        ]
    return [
        {
            "id": f"{slide_id}/block-{idx:02d}",
            "type": btype,
            "html": render_markdown(md),
            "markdown": md,
        }
        for idx, (btype, md) in enumerate(raw)
    ]


# --- Frontmatter parser ----------------------------------------------------


_FRONTMATTER_FENCE = "---"


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse a minimal ``---`` fenced YAML-ish header.

    Supports ``key: value`` lines only (no nested structures, no lists). Values
    are stripped and optional quotes removed. Returns ``(meta, body)``. If no
    valid frontmatter is present, returns ``({}, text)`` unchanged.
    """
    if not text.startswith(_FRONTMATTER_FENCE):
        return {}, text
    # Require a newline right after the opening fence.
    after_open = text[len(_FRONTMATTER_FENCE):]
    if not after_open.startswith("\n"):
        return {}, text
    rest = after_open[1:]
    closing_idx = rest.find(f"\n{_FRONTMATTER_FENCE}")
    if closing_idx == -1:
        return {}, text
    header = rest[:closing_idx]
    body_start = closing_idx + 1 + len(_FRONTMATTER_FENCE)
    # Skip one newline after the closing fence if present.
    if body_start < len(rest) and rest[body_start] == "\n":
        body_start += 1
    body = rest[body_start:]
    meta: dict[str, str] = {}
    for raw_line in header.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        if key:
            meta[key] = value
    return meta, body


# --- Outcome extraction ---------------------------------------------------

OUTCOME_RE = re.compile(r"^\s*\*\*Outcome:\*\*\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)


def extract_outcome(text: str) -> str | None:
    match = OUTCOME_RE.search(text)
    return match.group(1).strip() if match else None
