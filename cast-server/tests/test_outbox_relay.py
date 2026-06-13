"""Notification outbox relay tests (Phase 5, sp3b).

The *delivery* half of the transactional outbox. sp2 writes the ``notifications_outbox`` row in
the SAME transaction as the auto-applied ``change_request``; sp3b drains it at-least-once and
surfaces it on the EXISTING structured ``{convergence, open_comment_count}`` rail (owner decision
#4 — one surface, not a parallel notifier). These tests are the acceptance bar:

* **Relay drains** ``pending`` → ``delivered`` and returns the delivered rows; idempotent re-run.
* **SC-006 crash assertion (unit-level):** a crash *between the commit and the relay* still
  delivers on re-run — and the descriptor surfaces the change **once** (0 lost / 0 duplicate
  after dedupe on ``change_request_id``), even with a duplicate outbox row.
* **Surface extension, not duplication:** ``GET .../requirements/versions`` still returns the
  landed ``{versions, convergence, open_comment_count}`` keys unchanged **plus** the new
  ``recent_writebacks`` round-trip descriptor.
* **/inbox parity:** ``GET .../inbox`` returns the SAME item shape the badge consumes.

DB isolation follows ``test_change_request_intake.py``: ``isolated_db`` swaps ``config.DB_PATH``
and the env fixture patches ``connection.DB_PATH`` so no-explicit-path service calls land on the
test DB.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CAST_SERVER_DIR = REPO_ROOT / "cast-server"
if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))


def _seed_goal(db_path: Path, slug: str = "rt-goal", title: str = "Round-trip goal") -> None:
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


@pytest.fixture
def env(isolated_db: Path, monkeypatch):
    """TestClient over the change_requests + requirements routers on a hermetic DB."""
    pytest.importorskip("cast_server.config")

    from cast_server.db import connection as _connection
    monkeypatch.setattr(_connection, "DB_PATH", isolated_db)

    from cast_server.routes import api_requirements, change_requests

    app = FastAPI()
    app.include_router(change_requests.router)
    app.include_router(api_requirements.router)

    _seed_goal(isolated_db)
    return {"client": TestClient(app), "db_path": isolated_db}


def _make_applied_change(db_path: Path, *, slug: str = "rt-goal",
                         origin_phase: str = "planning",
                         origin_artifact_path: str = "plan.collab.md") -> dict:
    """Create a fast-tracked (``applied``) addition → one ``pending`` outbox row in one txn.

    Exercises sp2's real auto-apply lane (the same-txn outbox insert) so the relay drains a row
    that was committed exactly the way production commits it.
    """
    from cast_server.services import change_request_service

    return change_request_service.create(
        slug, kind="addition", proposed_body="FR-021 New requirement.",
        base_version=1, author="cast-planner", author_type="agent",
        origin_phase=origin_phase, origin_artifact_path=origin_artifact_path,
        status="applied", db_path=db_path,
    )


def _outbox_rows(db_path: Path) -> list[dict]:
    from cast_server.db.connection import get_connection

    conn = get_connection(db_path)
    try:
        rows = conn.execute("SELECT * FROM notifications_outbox ORDER BY id").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Drain — at-least-once, idempotent                                            #
# --------------------------------------------------------------------------- #

def test_drain_marks_pending_delivered_and_returns_them(env):
    from cast_server.services import notification_service

    db_path = env["db_path"]
    cr = _make_applied_change(db_path)

    before = _outbox_rows(db_path)
    assert [r["status"] for r in before] == ["pending"]

    delivered = notification_service.drain_outbox(db_path=db_path)
    assert len(delivered) == 1
    assert delivered[0]["change_request_id"] == cr["id"]

    after = _outbox_rows(db_path)
    assert [r["status"] for r in after] == ["delivered"]
    assert after[0]["delivered_at"] is not None


def test_drain_is_idempotent_on_rerun(env):
    """Re-running the relay over already-delivered rows delivers nothing new (no-op)."""
    from cast_server.services import notification_service

    db_path = env["db_path"]
    _make_applied_change(db_path)

    first = notification_service.drain_outbox(db_path=db_path)
    second = notification_service.drain_outbox(db_path=db_path)
    assert len(first) == 1
    assert second == []  # nothing pending → clean no-op
    assert [r["status"] for r in _outbox_rows(db_path)] == ["delivered"]


# --------------------------------------------------------------------------- #
# SC-006 — crash between commit and relay; 0 lost / 0 duplicate after dedupe   #
# --------------------------------------------------------------------------- #

def test_crash_between_commit_and_relay_still_delivers_once(env):
    """The outbox row is committed (the change's txn); the relay 'never ran' (crash). Re-running
    the relay still delivers — and the descriptor surfaces the change exactly once, even with a
    duplicate outbox row pointing at the same change_request_id (0 lost / 0 duplicate)."""
    from cast_server.db.connection import get_connection
    from cast_server.services import notification_service

    db_path = env["db_path"]
    cr = _make_applied_change(db_path)

    # Simulate a duplicate outbox row for the SAME change_request_id (e.g. an at-least-once
    # re-queue on a partial-failure path). The dedupe must still surface ONE notification.
    conn = get_connection(db_path)
    try:
        conn.execute(
            """INSERT INTO notifications_outbox (change_request_id, payload, status, created_at)
               VALUES (?, ?, 'pending', ?)""",
            (cr["id"], "{}", "2026-06-12T00:00:00+00:00"),
        )
        conn.commit()
    finally:
        conn.close()

    # The relay had not run (crash). Re-run it now — at-least-once delivery.
    notification_service.drain_outbox(db_path=db_path)
    assert all(r["status"] == "delivered" for r in _outbox_rows(db_path))

    # 0 lost: the change surfaces. 0 duplicate: deduped to a single descriptor item.
    descriptor = notification_service.recent_writebacks("rt-goal", db_path=db_path)
    matching = [d for d in descriptor if d["change_request_id"] == cr["id"]]
    assert len(matching) == 1
    assert matching[0]["origin_phase"] == "planning"
    assert matching[0]["origin_artifact_path"] == "plan.collab.md"


def test_recent_writebacks_only_surfaces_delivered(env):
    """A queued-but-undelivered (``pending``) change is NOT yet on the descriptor."""
    from cast_server.services import notification_service

    db_path = env["db_path"]
    _make_applied_change(db_path)

    # Before draining: pending, so nothing surfaced.
    assert notification_service.recent_writebacks("rt-goal", db_path=db_path) == []

    notification_service.drain_outbox(db_path=db_path)
    assert len(notification_service.recent_writebacks("rt-goal", db_path=db_path)) == 1


# --------------------------------------------------------------------------- #
# Surface extension — landed keys intact + new descriptor                      #
# --------------------------------------------------------------------------- #

def test_versions_payload_extends_landed_surface(env):
    """``GET /versions`` keeps ``{versions, convergence, open_comment_count}`` AND adds
    ``recent_writebacks`` (extend, never structure-from-boolean / never a parallel endpoint)."""
    from cast_server.services import notification_service

    client, db_path = env["client"], env["db_path"]
    _make_applied_change(db_path)
    notification_service.drain_outbox(db_path=db_path)

    resp = client.get("/api/goals/rt-goal/requirements/versions")
    assert resp.status_code == 200
    body = resp.json()

    # Landed keys unchanged (no regression).
    assert set(body) >= {"versions", "convergence", "open_comment_count"}
    assert body["convergence"] in ("converged", "unconverged")
    assert isinstance(body["open_comment_count"], int)

    # New round-trip descriptor, with the FR-019 item shape.
    assert "recent_writebacks" in body
    assert len(body["recent_writebacks"]) == 1
    item = body["recent_writebacks"][0]
    assert set(item) == {
        "change_request_id", "summary", "origin_phase",
        "origin_artifact_path", "applied_at",
    }
    assert "planning" in item["summary"]


def test_versions_recent_writebacks_empty_without_delivery(env):
    """No delivered write-backs → the descriptor is an empty list (surface still present)."""
    resp = env["client"].get("/api/goals/rt-goal/requirements/versions")
    assert resp.status_code == 200
    assert resp.json()["recent_writebacks"] == []


# --------------------------------------------------------------------------- #
# /inbox — the agent companion, same shape as the badge                        #
# --------------------------------------------------------------------------- #

def test_inbox_returns_same_shape_as_badge(env):
    """``GET /inbox`` returns the SAME item shape the ``versions`` round-trip descriptor uses."""
    from cast_server.services import notification_service

    client, db_path = env["client"], env["db_path"]
    _make_applied_change(db_path)
    notification_service.drain_outbox(db_path=db_path)

    versions = client.get("/api/goals/rt-goal/requirements/versions").json()
    inbox = client.get("/api/goals/rt-goal/inbox").json()

    assert "notifications" in inbox
    assert inbox["notifications"] == versions["recent_writebacks"]


def test_inbox_unknown_goal_is_404(env):
    assert env["client"].get("/api/goals/nope/inbox").status_code == 404


def test_inbox_post_accepts_ldn_notification(env):
    """``POST /inbox`` is a minimal LDN sink — accepts and acknowledges (202)."""
    resp = env["client"].post(
        "/api/goals/rt-goal/inbox",
        json={"type": "Announce", "object": "change_request/1"},
    )
    assert resp.status_code == 202
    assert resp.json()["status"] == "accepted"


def test_inbox_post_unknown_goal_is_404(env):
    assert env["client"].post("/api/goals/nope/inbox", json={}).status_code == 404
