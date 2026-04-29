"""Stage 2 renderer: ``what/*.md`` → one slide per file.

Each file is one slide. Optional YAML-ish frontmatter controls title/outcome.
Without frontmatter, the first ``# `` heading is the title and the first
``**Outcome:**`` line is the outcome.
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
    parse_frontmatter,
    slugify,
)

_HEADING_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_FILENAME_PREFIX_RE = re.compile(r"^\d+[-_]*")
_PHASE_ID_RE = re.compile(r"^([sa])(\d+)")


def _narrative_sort_key(path: Path) -> tuple[int, int, str]:
    """Sort core slides (s01, s02, ...) before appendix (a01, a02, ...).

    Files that don't match the ``[sa]\\d+`` phase-id convention sort last
    alphabetically, so non-standard naming still renders deterministically.
    """
    m = _PHASE_ID_RE.match(path.stem)
    if m:
        group = 0 if m.group(1) == "s" else 1
        return (group, int(m.group(2)), path.stem)
    return (2, 0, path.stem)


def _fallback_title_from_filename(path: Path) -> str:
    stem = path.stem
    stripped = _FILENAME_PREFIX_RE.sub("", stem)
    return stripped.replace("-", " ").replace("_", " ").strip() or stem


def _parse_slide_file(path: Path) -> tuple[str, str | None, str]:
    """Return ``(title, outcome, body)`` for a single WHAT file."""
    text = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)

    if "title" in meta and meta["title"]:
        title = meta["title"]
    else:
        heading = _HEADING_RE.search(body)
        title = heading.group(1).strip() if heading else _fallback_title_from_filename(path)

    outcome = meta.get("outcome") or extract_outcome(body)
    return title, outcome, body


def render(goal_dir: Path, stage: str | None) -> tuple[list[Slide], list[SidebarEntry], BuildResult]:
    what_dir = goal_dir / "what"
    files = sorted(
        (
            p for p in what_dir.iterdir()
            if p.is_file() and p.suffix == ".md" and not p.stem.startswith("_")
        ),
        key=_narrative_sort_key,
    )

    slides: list[Slide] = []
    sidebar: list[SidebarEntry] = []

    for idx, path in enumerate(files, start=1):
        title, outcome, body = _parse_slide_file(path)
        slide_id = f"slide-{idx:02d}-{slugify(path.stem)}"
        source_rel = path.relative_to(goal_dir).as_posix()
        slides.append(
            Slide(
                id=slide_id,
                title=title,
                outcome=outcome,
                source_path=source_rel,
                mode="edit",
                blocks=md_to_blocks(slide_id, body),
            )
        )
        sidebar.append(SidebarEntry(slide_id=slide_id, label=title, summary=outcome))

    result = BuildResult(
        mode="edit",
        stage="what",
        slide_count=len(slides),
        source_files=[p.relative_to(goal_dir).as_posix() for p in files],
        source_hash=compute_source_hash(files),
    )
    return slides, sidebar, result


register_renderer("what", render)
