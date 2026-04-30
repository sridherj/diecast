"""9-concurrent-children cap regression test.

Phase 3b sp6_5 (Diecast OSS). Honors Q#18 / Q#19 plan-review locks: mock at
the narrowest implementation boundary, never at ``subprocess.Popen``.

Implementation map (located via plan §Step 1):

* Cap constant: ``cast_server.config.MAX_CONCURRENT_AGENTS``
  (``cast-server/cast_server/config.py:101``). Default 7 from the env-var,
  but the locked product spec (phase-3b ``_shared_context.md`` §1.3) is 9 —
  so this test pins the value at 9 via ``monkeypatch`` so the assertion is
  independent of whoever set ``CAST_MAX_CONCURRENT_AGENTS``.
* Spawn-vs-queue branch: ``cast_server.services.agent_service._dispatcher_loop``
  (``cast-server/cast_server/services/agent_service.py:2089``). Each tick:

  1. Promote ``scheduled`` rows whose ``scheduled_at`` has passed.
  2. Count rows with ``status = 'running'``.
  3. If ``running_count < MAX_CONCURRENT_AGENTS``, pick the oldest
     ``slots = MAX_CONCURRENT_AGENTS - running_count`` rows where
     ``status = 'pending'`` (``ORDER BY created_at ASC``) and call
     ``await _launch_agent(row.id)`` for each.

* "Queue" data structure: there is no in-memory queue object. Pending
  ``agent_runs`` rows in ``ORDER BY created_at ASC`` are the queue, and
  the dispatcher re-evaluates from scratch every tick.
* Dequeue trigger: a running run flipping status out of ``'running'``
  (e.g. to ``completed``) creates a free slot; the next dispatcher tick
  fills it from the oldest pending row.

Mock surface (narrowest boundary):

* ``_launch_agent`` is replaced with a synchronous-coroutine helper that
  flips the agent_run row's status to ``'running'``. Same signature, no
  tmux, no subprocess, no ``Popen``.
* ``should_auto_retry`` is forced to True. The real implementation queries
  ``agent_error_memories`` via a connection that does not honour the
  ``isolated_db`` ``DB_PATH`` patch, which would otherwise leak into the
  developer's production DB.
* ``asyncio.sleep`` (the inter-tick sleep at the bottom of the dispatcher
  loop) is replaced with a coroutine that raises ``_StopDispatcherLoop`` —
  a ``BaseException`` subclass that the dispatcher's own
  ``except Exception`` handler deliberately does not catch. Net effect:
  exactly one tick runs per call.
* ``MAX_CONCURRENT_AGENTS`` is monkeypatched to 9 inside the
  ``agent_service`` namespace so the cap test is independent of env-var
  state.
"""

from __future__ import annotations

import asyncio

import pytest

from cast_server.db.connection import get_connection
from cast_server.services import agent_service

from tests.conftest import ensure_goal, make_pending_run


class _StopDispatcherLoop(BaseException):
    """Sentinel raised in place of ``asyncio.sleep`` to break the loop."""


# ---------------------------------------------------------------------------
# Inspection helpers — use the same SQL the dispatcher uses
# ---------------------------------------------------------------------------


def _ids_with_status(db_path, status: str) -> list[str]:
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT id FROM agent_runs WHERE status = ? ORDER BY created_at ASC, id ASC",
            (status,),
        ).fetchall()
    finally:
        conn.close()
    return [r["id"] for r in rows]


def _flip_to_completed(db_path, run_id: str) -> None:
    conn = get_connection(db_path)
    try:
        conn.execute(
            "UPDATE agent_runs SET status = 'completed' WHERE id = ?",
            (run_id,),
        )
        conn.commit()
    finally:
        conn.close()


def _seed_ten_pending(db_path) -> list[str]:
    """Insert 10 pending rows with explicit, monotonically increasing
    ``created_at`` timestamps so the dispatcher's FIFO order is
    deterministic. SQLite ``datetime('now')`` is second-precision and ties
    on rapid inserts.
    """
    ensure_goal(db_path)
    seeded = []
    for i in range(10):
        # 2026-01-01T00:00:0i; trailing-zero seconds keep the strings sortable.
        ts = f"2026-01-01 00:00:{i:02d}"
        seeded.append(make_pending_run(db_path, run_id=f"cap-{i:02d}", created_at=ts))
    return seeded


def _patch_dispatcher(monkeypatch, *, max_concurrent: int = 9) -> list[str]:
    """Patch ``agent_service`` for a single dispatcher tick. Returns the
    list that the patched ``_launch_agent`` will append to (call order)."""
    launched: list[str] = []

    async def fake_launch(run_id, db_path=None):
        launched.append(run_id)
        agent_service.update_agent_run(run_id, status="running", db_path=db_path)

    async def fake_sleep(_delay):
        raise _StopDispatcherLoop

    monkeypatch.setattr(agent_service, "_launch_agent", fake_launch)
    monkeypatch.setattr(agent_service, "should_auto_retry", lambda _name: True)
    monkeypatch.setattr(agent_service, "MAX_CONCURRENT_AGENTS", max_concurrent)
    monkeypatch.setattr(agent_service.asyncio, "sleep", fake_sleep)

    return launched


async def _run_one_tick(db_path) -> None:
    """Run the real dispatcher loop body exactly once.

    The patched ``asyncio.sleep`` raises a ``BaseException`` after the
    first iteration completes; the dispatcher's outer ``except Exception``
    handler does not catch it, so it propagates and we ``except`` it here.
    """
    try:
        await agent_service._dispatcher_loop(db_path=db_path)
    except _StopDispatcherLoop:
        pass


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_nine_cap_queues_tenth(monkeypatch, isolated_db):
    """Insert 10 pending runs; the first dispatcher tick spawns 9 and
    leaves the 10th pending — proving the cap holds."""
    seeded = _seed_ten_pending(isolated_db)
    launched = _patch_dispatcher(monkeypatch, max_concurrent=9)

    asyncio.run(_run_one_tick(isolated_db))

    running = _ids_with_status(isolated_db, "running")
    pending = _ids_with_status(isolated_db, "pending")

    assert len(running) == 9, (
        f"cap should hold spawn count at 9; got {len(running)} running"
    )
    assert len(pending) == 1, (
        f"the 10th run must remain pending; got {len(pending)} pending"
    )
    assert running == seeded[:9], "FIFO order: oldest 9 pending runs should run first"
    assert pending == seeded[9:], "the youngest pending run should be the queued one"
    assert launched == seeded[:9], (
        "_launch_agent must be called exactly for the first 9 in created_at order"
    )


@pytest.mark.integration
def test_completed_run_unblocks_queued_child(monkeypatch, isolated_db):
    """When one of the 9 running children completes, the next tick spawns
    the queued 10th — the cap is enforced both ways (spawn and dequeue)."""
    seeded = _seed_ten_pending(isolated_db)
    launched = _patch_dispatcher(monkeypatch, max_concurrent=9)

    # Tick 1 — 9 spawn, the youngest stays pending.
    asyncio.run(_run_one_tick(isolated_db))
    assert _ids_with_status(isolated_db, "running") == seeded[:9]
    assert _ids_with_status(isolated_db, "pending") == [seeded[9]]
    assert launched == seeded[:9]

    # Simulate the oldest running child finishing.
    _flip_to_completed(isolated_db, seeded[0])

    # Tick 2 — exactly one slot opened, so exactly one queued run spawns.
    asyncio.run(_run_one_tick(isolated_db))

    running = _ids_with_status(isolated_db, "running")
    pending = _ids_with_status(isolated_db, "pending")
    completed = _ids_with_status(isolated_db, "completed")

    assert len(running) <= 9, "cap must hold even when slots open via completion"
    assert len(running) == 9, (
        "exactly one slot opened, so the queued run should now be running"
    )
    assert seeded[9] in running, "the formerly-queued run must now be running"
    assert pending == [], "no pending rows should remain after the second tick"
    assert completed == [seeded[0]]
    assert launched == seeded[:9] + [seeded[9]], (
        "_launch_agent should have fired exactly once more, for the queued run"
    )


@pytest.mark.integration
def test_no_pending_runs_is_a_noop(monkeypatch, isolated_db):
    """A tick with zero pending rows must not call ``_launch_agent`` and
    must not raise. Guards against regressions where the cap branch is
    re-ordered above the pending-rows fetch."""
    ensure_goal(isolated_db)
    launched = _patch_dispatcher(monkeypatch, max_concurrent=9)

    asyncio.run(_run_one_tick(isolated_db))

    assert launched == [], "no pending rows means no spawns"
    assert _ids_with_status(isolated_db, "running") == []
    assert _ids_with_status(isolated_db, "pending") == []
