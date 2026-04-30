"""Sync engine — rebuilds SQLite cache from markdown/YAML files."""

import logging
import os
from datetime import datetime
from pathlib import Path

from taskos.config import GOALS_DIR, SCRATCHPAD_PATH, REGISTRY_PATH
from taskos.db.connection import get_connection
from taskos.sync.parsers.scratchpad_parser import parse_scratchpad
from taskos.sync.parsers.registry_parser import parse_registry

logger = logging.getLogger(__name__)

# Module-level mtime cache for incremental sync
_file_mtimes: dict[str, float] = {}
_last_sync: float = 0
SYNC_DEBOUNCE_SECONDS = 30


def full_sync(
    goals_dir: Path | None = None,
    scratchpad_path: Path | None = None,
    registry_path: Path | None = None,
    db_path: Path | None = None,
) -> dict:
    """Full sync: scan all files, rebuild DB.

    Returns a summary dict with counts.
    Goals are DB-managed — not synced from files.
    """
    scratchpad_path = scratchpad_path or SCRATCHPAD_PATH
    registry_path = registry_path or REGISTRY_PATH

    conn = get_connection(db_path)
    summary = {"scratchpad_entries": 0, "agents": 0}

    try:
        # Clear file-synced data (agent_runs preserved — FK uses ON DELETE SET NULL)
        # Goals and tasks are DB-managed — never sync from files
        conn.execute("DELETE FROM scratchpad_entries")
        conn.execute("DELETE FROM agents")

        # Sync scratchpad
        entries = parse_scratchpad(scratchpad_path)
        for entry in entries:
            _insert_scratchpad_entry(conn, entry)
            summary["scratchpad_entries"] += 1

        # Sync agent registry
        agents = parse_registry(registry_path)
        for agent in agents:
            _upsert_agent(conn, agent)
            summary["agents"] += 1

        conn.commit()
        logger.info(
            "Full sync complete: %d entries, %d agents",
            summary["scratchpad_entries"], summary["agents"],
        )

    except Exception:
        conn.rollback()
        logger.exception("Full sync failed, rolled back")
        raise
    finally:
        conn.close()

    return summary


def _insert_scratchpad_entry(conn, data: dict) -> None:
    """Insert a scratchpad entry."""
    conn.execute(
        """INSERT INTO scratchpad_entries
           (entry_date, content, flagged_as_goal, synced_at)
           VALUES (?, ?, ?, ?)""",
        (data["entry_date"], data["content"], data["flagged_as_goal"], data["synced_at"]),
    )


def _upsert_agent(conn, data: dict) -> None:
    """Insert or replace an agent record."""
    conn.execute(
        """INSERT OR REPLACE INTO agents
           (name, type, description, input, output, tags, triggers, last_tested, synced_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data["name"], data.get("type", ""), data["description"],
            data.get("input", ""), data.get("output", ""),
            data["tags"], data["triggers"], data["last_tested"], data["synced_at"],
        ),
    )


def incremental_sync(
    goals_dir: Path | None = None,
    scratchpad_path: Path | None = None,
    registry_path: Path | None = None,
    db_path: Path | None = None,
) -> dict | None:
    """Check file mtimes, only re-parse changed files. Debounced to 30s."""
    global _last_sync

    now = datetime.now().timestamp()
    if now - _last_sync < SYNC_DEBOUNCE_SECONDS:
        return None  # Too soon

    scratchpad_path = scratchpad_path or SCRATCHPAD_PATH
    registry_path = registry_path or REGISTRY_PATH
    changed = False
    summary = {"scratchpad_updated": False, "agents_updated": False}

    # Check scratchpad
    if scratchpad_path.exists():
        mtime = os.path.getmtime(scratchpad_path)
        cached = _file_mtimes.get(str(scratchpad_path), 0)
        if mtime > cached:
            _sync_scratchpad(scratchpad_path, db_path)
            _file_mtimes[str(scratchpad_path)] = mtime
            summary["scratchpad_updated"] = True
            changed = True

    # Check agent registry
    if registry_path.exists():
        mtime = os.path.getmtime(registry_path)
        cached = _file_mtimes.get(str(registry_path), 0)
        if mtime > cached:
            _sync_registry(registry_path, db_path)
            _file_mtimes[str(registry_path)] = mtime
            summary["agents_updated"] = True
            changed = True

    _last_sync = now

    if changed:
        logger.info("Incremental sync: %s", summary)
        return summary

    return None


def _sync_scratchpad(scratchpad_path: Path, db_path: Path | None = None) -> None:
    """Re-sync scratchpad entries."""
    conn = get_connection(db_path)
    try:
        conn.execute("DELETE FROM scratchpad_entries")
        entries = parse_scratchpad(scratchpad_path)
        for entry in entries:
            _insert_scratchpad_entry(conn, entry)
        conn.commit()
        logger.info("Incremental sync: re-synced scratchpad (%d entries)", len(entries))
    except Exception:
        conn.rollback()
        logger.exception("Incremental sync failed for scratchpad")
    finally:
        conn.close()


def _sync_registry(registry_path: Path, db_path: Path | None = None) -> None:
    """Re-sync agent registry."""
    conn = get_connection(db_path)
    try:
        conn.execute("DELETE FROM agents")
        agents = parse_registry(registry_path)
        for agent in agents:
            _upsert_agent(conn, agent)
        conn.commit()
        logger.info("Incremental sync: re-synced agents (%d agents)", len(agents))
    except Exception:
        conn.rollback()
        logger.exception("Incremental sync failed for agent registry")
    finally:
        conn.close()
