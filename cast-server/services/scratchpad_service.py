"""Scratchpad service — append entries, manage file + DB."""

import logging
from datetime import date, datetime, timezone
from pathlib import Path

from taskos.config import SCRATCHPAD_PATH
from taskos.db.connection import get_connection

logger = logging.getLogger(__name__)


def add_entry(
    content: str,
    scratchpad_path: Path = None,
    db_path=None,
) -> dict:
    """Add a scratchpad entry. Appends to file under today's date header, inserts into DB."""
    scratchpad_path = scratchpad_path or SCRATCHPAD_PATH
    today = str(date.today())
    now = datetime.now(timezone.utc).isoformat()

    # Append to file
    _append_to_file(scratchpad_path, today, content)

    # Insert into DB
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            """INSERT INTO scratchpad_entries (entry_date, content, flagged_as_goal, synced_at)
               VALUES (?, ?, 0, ?)""",
            (today, content, now),
        )
        entry_id = cursor.lastrowid
        conn.commit()

        entry = dict(conn.execute(
            "SELECT * FROM scratchpad_entries WHERE id = ?", (entry_id,)
        ).fetchone())
    finally:
        conn.close()

    return entry


def get_recent_entries(limit: int = 20, db_path=None) -> list[dict]:
    """Get recent scratchpad entries."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM scratchpad_entries ORDER BY entry_date DESC, id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _append_to_file(scratchpad_path: Path, today: str, content: str):
    """Append an entry to scratchpad.md under today's date header.

    If today's header exists, insert after it. Otherwise, add header at top.
    """
    try:
        if not scratchpad_path.exists():
            scratchpad_path.write_text(f"## {today}\n- {content}\n")
            return

        existing = scratchpad_path.read_text()
        header = f"## {today}"

        if header in existing:
            # Insert entry right after the header line
            lines = existing.split("\n")
            new_lines = []
            inserted = False
            for line in lines:
                new_lines.append(line)
                if line.strip() == header and not inserted:
                    new_lines.append(f"- {content}")
                    inserted = True
            scratchpad_path.write_text("\n".join(new_lines))
        else:
            # Add new date header at the top (reverse chronological)
            scratchpad_path.write_text(f"{header}\n- {content}\n\n{existing}")
    except OSError as e:
        logger.error("Failed to write scratchpad: %s", e)
