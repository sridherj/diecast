"""Parse scratchpad.md into dated entries."""

import logging
import re
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_scratchpad(scratchpad_path: Path) -> list[dict]:
    """Parse scratchpad.md into a list of entry dicts.

    Returns empty list if file doesn't exist.
    Entries without a date header are skipped with a warning.
    """
    if not scratchpad_path.exists():
        return []

    try:
        content = scratchpad_path.read_text()
    except OSError as e:
        logger.warning("Cannot read scratchpad %s: %s", scratchpad_path, e)
        return []

    entries = []
    current_date = None
    now = datetime.now(timezone.utc).isoformat()
    orphan_count = 0

    for line in content.split("\n"):
        # Date header: ## 2026-02-23
        date_match = re.match(r"^## (\d{4}-\d{2}-\d{2})\s*$", line)
        if date_match:
            current_date = date_match.group(1)
            continue

        # Entry: - Some text here
        entry_match = re.match(r"^- (.+)$", line)
        if entry_match:
            if current_date is None:
                orphan_count += 1
                continue
            content_text = entry_match.group(1).strip()
            entries.append({
                "entry_date": current_date,
                "content": content_text,
                "flagged_as_goal": 0,
                "synced_at": now,
            })

    if orphan_count > 0:
        logger.warning("Scratchpad: skipped %d entries without date header", orphan_count)

    return entries
