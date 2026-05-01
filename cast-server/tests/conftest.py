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


def _seed_run(db_path: Path, *, run_id: str, agent_name: str,
              goal_slug: str = "tree-goal",
              parent_run_id: str | None = None,
              status: str = "completed",
              task_id: int | None = None,
              cost_usd: float | None = None,
              context_usage: str | None = None,
              created_at: str = "2026-04-30T00:00:00+00:00",
              started_at: str | None = "2026-04-30T00:00:00+00:00",
              completed_at: str | None = "2026-04-30T00:00:10+00:00") -> str:
    """Insert one agent_runs row with full control over rollup-relevant fields.

    Used by ``seeded_runs_tree`` and ``deep_chain_db`` fixtures. Kept private
    so test modules go through the high-level fixtures, not raw seeding.
    """
    from cast_server.db.connection import get_connection

    ensure_goal(db_path, slug=goal_slug)
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO agent_runs "
            "(id, agent_name, goal_slug, task_id, parent_run_id, status, "
            " cost_usd, context_usage, created_at, started_at, completed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (run_id, agent_name, goal_slug, task_id, parent_run_id, status,
             cost_usd, context_usage, created_at, started_at, completed_at),
        )
        conn.commit()
    finally:
        conn.close()
    return run_id


@pytest.fixture
def empty_db(isolated_db):
    """Alias for an isolated DB with no agent_runs rows seeded."""
    return isolated_db


@pytest.fixture
def seeded_runs_tree(isolated_db):
    """Seed four trees that exercise every rollup / rework path.

    Tree 1 (happy):       L1 ``happy-l1`` with three completed L2 children.
    Tree 2 (rework):      L1 ``preso-l1`` (cast-preso-orchestrator) with
                          a check-coordinator pair (rework loop) plus a
                          how-maker child. The 2nd check-coordinator owns
                          two L3 children sharing (agent_name, task_id) so
                          rework propagation reaches L1.
    Tree 3 (4-deep):      ``deep-l1`` → ``deep-l2`` → ``deep-l3`` →
                          ``deep-l4``, all completed.
    Tree 4 (leaf):        ``leaf-l1`` with no children.

    Sibling ``created_at`` differs by 1+ microseconds so the ASC sort is
    deterministic. Tree 1 has a ``running`` child to exercise severity
    rollup; one of its grandchildren is ``failed`` to test
    ``failed_descendant_count`` and ``status_rollup``.
    """
    from datetime import datetime, timedelta, timezone

    db_path = isolated_db
    base = datetime(2026, 4, 30, tzinfo=timezone.utc)

    def iso(offset_us: int) -> str:
        return (base + timedelta(microseconds=offset_us)).isoformat()

    # ---- Tree 1: happy + one running + one failed grandchild ----
    _seed_run(db_path, run_id="happy-l1", agent_name="cast-orchestrate",
              status="completed", cost_usd=0.10,
              created_at=iso(0),
              started_at=iso(0),
              completed_at=(base + timedelta(seconds=42)).isoformat())
    _seed_run(db_path, run_id="happy-c1", agent_name="cast-controller",
              parent_run_id="happy-l1", status="completed", cost_usd=0.02,
              context_usage='{"total": 30000, "limit": 200000}',
              created_at=iso(1))
    _seed_run(db_path, run_id="happy-c2", agent_name="cast-service",
              parent_run_id="happy-l1", status="running", cost_usd=0.03,
              context_usage='{"total": 100000, "limit": 200000}',
              created_at=iso(2))
    _seed_run(db_path, run_id="happy-c3", agent_name="cast-repository",
              parent_run_id="happy-l1", status="completed", cost_usd=0.01,
              context_usage='{"total": 160000, "limit": 200000}',
              created_at=iso(3))
    # A failed grandchild under happy-c1 to test failed_descendant_count
    # and status_rollup max-severity.
    _seed_run(db_path, run_id="happy-gc1", agent_name="cast-controller-test",
              parent_run_id="happy-c1", status="failed", cost_usd=0.005,
              created_at=iso(4))

    # ---- Tree 2: preso rework loop (L1 + L2 pair + L3 pair) ----
    _seed_run(db_path, run_id="preso-l1",
              agent_name="cast-preso-orchestrator",
              status="completed", cost_usd=0.20,
              created_at=iso(10),
              started_at=iso(10),
              completed_at=(base + timedelta(seconds=120)).isoformat())
    _seed_run(db_path, run_id="preso-cc1",
              agent_name="cast-preso-check-coordinator",
              parent_run_id="preso-l1", status="failed",
              cost_usd=0.04, created_at=iso(11))
    # Same (agent_name, task_id) → rework #2.
    _seed_run(db_path, run_id="preso-cc2",
              agent_name="cast-preso-check-coordinator",
              parent_run_id="preso-l1", status="completed",
              cost_usd=0.05, created_at=iso(12))
    _seed_run(db_path, run_id="preso-how",
              agent_name="cast-preso-how",
              parent_run_id="preso-l1", status="completed",
              cost_usd=0.03, created_at=iso(13))
    # L3 rework under preso-cc2 — rework_count must propagate to preso-l1.
    _seed_run(db_path, run_id="preso-l3a",
              agent_name="cast-preso-check-content",
              parent_run_id="preso-cc2", status="completed",
              cost_usd=0.01, created_at=iso(14))
    _seed_run(db_path, run_id="preso-l3b",
              agent_name="cast-preso-check-content",
              parent_run_id="preso-cc2", status="completed",
              cost_usd=0.01, created_at=iso(15))

    # ---- Tree 3: 4-level linear chain, all completed ----
    _seed_run(db_path, run_id="deep-l1", agent_name="cast-orchestrate",
              status="completed", cost_usd=0.05,
              created_at=iso(20),
              started_at=iso(20),
              completed_at=(base + timedelta(seconds=30)).isoformat())
    _seed_run(db_path, run_id="deep-l2", agent_name="cast-subphase-runner",
              parent_run_id="deep-l1", status="completed", cost_usd=0.04,
              created_at=iso(21))
    _seed_run(db_path, run_id="deep-l3", agent_name="cast-controller",
              parent_run_id="deep-l2", status="completed", cost_usd=0.03,
              created_at=iso(22))
    _seed_run(db_path, run_id="deep-l4", agent_name="cast-controller-test",
              parent_run_id="deep-l3", status="completed", cost_usd=0.02,
              created_at=iso(23))

    # ---- Tree 4: leaf L1 with no children ----
    _seed_run(db_path, run_id="leaf-l1", agent_name="cast-doctor",
              status="completed", cost_usd=0.01,
              created_at=iso(30),
              started_at=iso(30),
              completed_at=(base + timedelta(seconds=5)).isoformat())

    return db_path


@pytest.fixture
def deep_chain_db(isolated_db):
    """Seed a 12-deep linear chain (one child per level) for depth-cap test.

    The recursive CTE caps tree depth at 10, so the bottom 2 nodes of the
    12-deep chain must be silently truncated and a server-side warning
    must be logged.
    """
    from datetime import datetime, timedelta, timezone

    db_path = isolated_db
    base = datetime(2026, 4, 30, tzinfo=timezone.utc)
    parent: str | None = None
    for level in range(12):
        run_id = f"chain-l{level}"
        _seed_run(
            db_path,
            run_id=run_id,
            agent_name="cast-chain-agent",
            parent_run_id=parent,
            status="completed",
            cost_usd=0.001,
            created_at=(base + timedelta(microseconds=level)).isoformat(),
        )
        parent = run_id
    return db_path


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
