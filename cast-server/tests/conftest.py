"""Shared fixtures for cast-server tests.

Authored as part of Phase 3b sp6 (rate-limit recovery test) and extended
by Phase 3b sp6_5 (9-concurrent-children cap regression test). Helpers are
deliberately generic so further regression tests can reuse them.

Test-ordering note: the repo-root `cast-server/conftest.py` puts the
`cast-server/` directory on ``sys.path`` so ``cast_server.*`` imports resolve
without an editable install. This file is the inner ``tests/`` conftest;
fixtures defined here apply only to modules under ``cast-server/tests/``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Defensive: ensure ``cast_server`` is importable even if pytest is invoked
# directly inside ``cast-server/tests/`` and the parent conftest hasn't run.
_CAST_SERVER_DIR = Path(__file__).resolve().parent.parent
if str(_CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(_CAST_SERVER_DIR))


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    """Provision a fresh SQLite DB for tests that touch ``agent_runs``.

    The fixture rewrites ``cast_server.config.DB_PATH`` so any code that
    calls ``get_connection()`` without an explicit ``db_path`` lands on the
    test database. Returns the ``Path`` to the DB file. Tests that prefer
    explicit dependency injection can ignore the fixture and pass
    ``db_path=...`` directly through the service-layer API.
    """
    db_path = tmp_path / "cast_server_test.db"

    from cast_server import config as cast_config
    monkeypatch.setattr(cast_config, "DB_PATH", db_path)

    from cast_server.db.connection import init_db
    init_db(db_path)
    return db_path


@pytest.fixture
def fake_tmux(monkeypatch):
    """Replace the ``agent_service`` tmux singleton with a ``MagicMock``.

    The real ``TmuxSessionManager`` shells out to ``tmux`` on construction
    (``tmux -V``) and on every method call. CI does not need a live tmux
    binary — every test that drives the dispatcher should patch the
    singleton via this fixture.

    Provides three pre-wired defaults:
    * ``list_all_pane_commands`` returns ``{}`` so callers can populate it.
    * ``capture_pane`` returns ``[]``.
    * ``session_exists`` returns ``True``.

    Each test customises these via ``fake_tmux.<attr>.return_value = ...``.
    The fixture also clears ``agent_service`` rate-limit bookkeeping dicts
    before and after the test so module-level state from one test cannot
    leak into the next (sp6_5 will rely on the same isolation).
    """
    from cast_server.services import agent_service

    tmux = MagicMock()
    tmux.list_all_pane_commands.return_value = {}
    tmux.capture_pane.return_value = []
    tmux.session_exists.return_value = True

    monkeypatch.setattr(agent_service, "_get_tmux", lambda: tmux)

    # Clear module state that other tests might have populated.
    agent_service._cooldown_until.clear()
    agent_service._current_pause.clear()
    agent_service._idle_since.clear()
    agent_service._total_paused.clear()
    agent_service._session_id_resolved.clear()

    yield tmux

    # Symmetric teardown: tests should not see leftover bookkeeping.
    agent_service._cooldown_until.clear()
    agent_service._current_pause.clear()
    agent_service._idle_since.clear()
    agent_service._total_paused.clear()
    agent_service._session_id_resolved.clear()


def ensure_goal(db_path: Path, slug: str = "test-goal", title: str = "Test goal") -> None:
    """Insert a parent ``goals`` row so ``agent_runs.goal_slug`` FK resolves.

    ``agent_runs.goal_slug`` is a foreign key to ``goals.slug`` with
    ``ON DELETE SET NULL``; foreign keys are enforced (PRAGMA in
    ``db.connection``) so the parent row must exist before any
    ``agent_runs`` row can be inserted. Idempotent — safe to call from
    multiple fixtures.
    """
    from cast_server.db.connection import get_connection

    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) VALUES (?, ?, ?)",
            (slug, title, slug),
        )
        conn.commit()
    finally:
        conn.close()


def make_running_run(db_path: Path, *,
                     run_id: str = "rl-test-run",
                     agent_name: str = "test-agent",
                     goal_slug: str = "test-goal") -> str:
    """Insert a single ``running`` row into ``agent_runs`` and return its id.

    Helper, not a fixture — sp6_5 reuses this for its concurrency-cap seed
    step (multiple rows). Kept deliberately minimal: no ``started_at`` so
    ``_check_all_agents`` skips the Claude session-id discovery branch.
    """
    from cast_server.db.connection import get_connection

    ensure_goal(db_path, slug=goal_slug)
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO agent_runs (id, agent_name, goal_slug, status, created_at) "
            "VALUES (?, ?, ?, 'running', datetime('now'))",
            (run_id, agent_name, goal_slug),
        )
        conn.commit()
    finally:
        conn.close()
    return run_id


def make_pending_run(db_path: Path, *,
                     run_id: str,
                     agent_name: str = "test-agent",
                     goal_slug: str = "test-goal",
                     created_at: str | None = None) -> str:
    """Insert a single ``pending`` row into ``agent_runs`` and return its id.

    Companion to :func:`make_running_run` for the concurrency-cap regression
    test (sp6_5). When seeding multiple rows the caller should pass an
    explicit ``created_at`` so the dispatcher's ``ORDER BY created_at ASC``
    queue is deterministic — SQLite ``datetime('now')`` only has
    second-level precision and otherwise ties on rapid inserts.
    """
    from cast_server.db.connection import get_connection

    ensure_goal(db_path, slug=goal_slug)
    conn = get_connection(db_path)
    try:
        if created_at is None:
            conn.execute(
                "INSERT INTO agent_runs (id, agent_name, goal_slug, status, created_at) "
                "VALUES (?, ?, ?, 'pending', datetime('now'))",
                (run_id, agent_name, goal_slug),
            )
        else:
            conn.execute(
                "INSERT INTO agent_runs (id, agent_name, goal_slug, status, created_at) "
                "VALUES (?, ?, ?, 'pending', ?)",
                (run_id, agent_name, goal_slug, created_at),
            )
        conn.commit()
    finally:
        conn.close()
    return run_id
