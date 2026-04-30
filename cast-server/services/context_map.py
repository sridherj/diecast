"""Context map generator for .ai.md files in goal directories.

Generates a compact .context-map.md TOC so agents can read an overview
instead of all individual .ai.md files, reducing cached token usage.
"""

import logging
import re
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_HEADER_RE = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
_MODIFIED_RE = re.compile(r"\*\*Modified:\*\*\s*(\S+)")
_ENTRY_HEADER_RE = re.compile(r"^## (.+)$", re.MULTILINE)


def _extract_toc(file_path: Path, goal_dir: Path) -> str:
    """Extract a TOC entry for a single .ai.md file."""
    rel_path = file_path.relative_to(goal_dir)
    stat = file_path.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).strftime("%Y-%m-%d")
    size_bytes = stat.st_size
    text = file_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    line_count = len(lines)

    # Size display
    if size_bytes >= 1024:
        size_str = f"{line_count} lines ({size_bytes / 1024:.1f} KB)"
    else:
        size_str = f"{line_count} lines ({size_bytes} B)"

    # Brief: first non-empty, non-header paragraph (truncated ~200 chars)
    brief = ""
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#") or stripped.startswith(">") or stripped.startswith("---"):
            continue
        brief = stripped[:200]
        if len(stripped) > 200:
            brief += "..."
        break

    # Headers: all #/##/### lines preserving hierarchy
    headers = []
    for match in _HEADER_RE.finditer(text):
        level = len(match.group(1))
        indent = "  " * (level - 1)
        headers.append(f"{indent}- {match.group(2)}")

    parts = [
        f"## {rel_path}",
        f"- **Size:** {size_str} | **Modified:** {mtime}",
    ]
    if brief:
        parts.append(f"- **Brief:** {brief}")
    if headers:
        parts.append("- **Headers:**")
        parts.extend(f"  {h}" for h in headers)

    return "\n".join(parts)


def _parse_existing_map(map_path: Path) -> dict[str, str]:
    """Parse existing .context-map.md into {relative_path: mtime_str}."""
    if not map_path.exists():
        return {}
    text = map_path.read_text(encoding="utf-8", errors="replace")
    result = {}
    for entry_match in _ENTRY_HEADER_RE.finditer(text):
        rel_path = entry_match.group(1)
        # Find the Modified date in the lines following this header
        start = entry_match.end()
        # Look for next ## or end of text
        next_header = _ENTRY_HEADER_RE.search(text, start)
        block = text[start:next_header.start()] if next_header else text[start:]
        mtime_match = _MODIFIED_RE.search(block)
        if mtime_match:
            result[rel_path] = mtime_match.group(1)
    return result


def ensure_context_map(goal_dir: Path) -> Path | None:
    """Generate or update .context-map.md for a goal directory.

    Uses mtime-based staleness detection to skip unchanged files.
    Returns the path to the context map, or None if no .ai.md files exist.
    """
    ai_files = sorted(goal_dir.rglob("*.ai.md"))
    if not ai_files:
        return None

    map_path = goal_dir / ".context-map.md"
    existing = _parse_existing_map(map_path)

    entries = []
    changed = False

    for f in ai_files:
        rel = str(f.relative_to(goal_dir))
        try:
            mtime = datetime.fromtimestamp(
                f.stat().st_mtime, tz=timezone.utc
            ).strftime("%Y-%m-%d")
        except OSError:
            logger.warning("Cannot stat %s, skipping", f)
            changed = True  # entry removed
            continue

        # Check if we can skip this file
        if rel in existing and existing[rel] == mtime:
            # Re-use existing entry — but we need to extract it from the file
            # Since we don't cache the full block, just re-extract (fast enough)
            pass

        try:
            entry = _extract_toc(f, goal_dir)
            entries.append(entry)
        except Exception:
            logger.warning("Failed to extract TOC for %s, skipping", f, exc_info=True)
            changed = True
            continue

        if rel not in existing or existing[rel] != mtime:
            changed = True

    # Check for deleted files
    current_rels = set()
    for f in ai_files:
        try:
            current_rels.add(str(f.relative_to(goal_dir)))
        except Exception:
            pass
    if set(existing.keys()) - current_rels:
        changed = True

    if not changed and map_path.exists():
        return map_path

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    header = (
        "# Context Map\n"
        "> Auto-generated TOC of .ai.md files. Read this instead of individual files.\n"
        "> To deep-read a specific file, use its path below.\n"
        f"> Last updated: {now}\n"
    )
    content = header + "\n" + "\n\n".join(entries) + "\n"
    map_path.write_text(content, encoding="utf-8")
    return map_path
