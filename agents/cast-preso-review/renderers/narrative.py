"""Stage 1 renderer: narrative.collab.md → slides.

One synthetic cover slide (deck title) + one slide per top-level ``## ``
section. Outcomes are extracted from ``**Outcome:** ...`` lines when present.
"""

from __future__ import annotations

import re
from pathlib import Path

from build import (
    BuildResult,
    SidebarEntry,
    Slide,
    compute_source_hash,
    register_renderer,
)

from renderers._markdown import (
    extract_outcome,
    md_to_blocks,
    slugify,
)

_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_DECK_TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def _split_sections(md: str) -> list[tuple[str, str]]:
    """Return [(heading, body), ...] split on ``## `` headings, in order.

    Anything before the first ``## `` (including the deck-title ``# `` line) is
    discarded — the cover slide handles the title on its own.
    """
    matches = list(_SECTION_RE.finditer(md))
    if not matches:
        return []
    sections: list[tuple[str, str]] = []
    for i, match in enumerate(matches):
        heading = match.group(1).strip()
        body_start = match.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        # Trim leading newline(s) after the heading line.
        body = md[body_start:body_end].lstrip("\n").rstrip()
        sections.append((heading, body))
    return sections


def render(goal_dir: Path, stage: str | None) -> tuple[list[Slide], list[SidebarEntry], BuildResult]:
    source = goal_dir / "narrative.collab.md"
    md = source.read_text(encoding="utf-8")

    title_match = _DECK_TITLE_RE.search(md)
    deck_title = title_match.group(1).strip() if title_match else goal_dir.name

    source_rel = source.relative_to(goal_dir).as_posix()

    slides: list[Slide] = [
        Slide(
            id="slide-00-cover",
            title=deck_title,
            outcome=None,
            source_path=source_rel,
            mode="edit",
            blocks=[
                {
                    "id": "slide-00-cover/block-00",
                    "type": "prose",
                    "html": "",
                    "markdown": "",
                }
            ],
        )
    ]
    sidebar: list[SidebarEntry] = [
        SidebarEntry(slide_id="slide-00-cover", label=deck_title, summary=None)
    ]

    for idx, (heading, body) in enumerate(_split_sections(md), start=1):
        slide_id = f"slide-{idx:02d}-{slugify(heading)}"
        outcome = extract_outcome(body)
        slides.append(
            Slide(
                id=slide_id,
                title=heading,
                outcome=outcome,
                source_path=source_rel,
                mode="edit",
                blocks=md_to_blocks(slide_id, body),
            )
        )
        sidebar.append(SidebarEntry(slide_id=slide_id, label=heading, summary=outcome))

    result = BuildResult(
        mode="edit",
        stage="narrative",
        slide_count=len(slides),
        source_files=[source_rel],
        source_hash=compute_source_hash([source]),
    )
    return slides, sidebar, result


register_renderer("narrative", render)
