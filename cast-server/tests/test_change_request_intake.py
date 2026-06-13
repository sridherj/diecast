"""Intake tests for ``POST /api/goals/{slug}/change-requests`` (Phase 5, sp2).

The same-door receiving path of "propose + notify + gate, never auto-sync". These tests are
the acceptance bar for sp2's success criteria:

* **Graduated trust by blast radius** — a pure addition fast-tracks to ``applied`` and queues a
  ``pending`` outbox FYI; a modification of existing content lands ``proposed`` (gated) with NO
  outbox row.
* **Malformed / oversized body → 422.**
* **Same-door parity (FR-013)** — a human-shaped (browser/HTMX) body and an agent-shaped (JSON)
  body hit the IDENTICAL handler and persist identical columns except ``author``/``author_type``.
* **Anti-spoof** — a browser-context request claiming ``author_type="human"`` with a forged
  ``author`` gets the server-derived identity, not the posted one.
* **Transactionality** — a failure after the ``change_requests`` insert leaves NOTHING orphaned
  (no event row, no outbox row, no request row) — all-or-nothing.

DB isolation follows the ``test_api_goals_route.py`` pattern: ``isolated_db`` swaps
``config.DB_PATH``; because ``db.connection`` binds ``DB_PATH`` at import, the env fixture
patches ``connection.DB_PATH`` directly too so the handler's no-explicit-path service calls
land on the test database.
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
    """TestClient over the change_requests router on a hermetic DB."""
    pytest.importorskip("cast_server.config")

    from cast_server.db import connection as _connection
    monkeypatch.setattr(_connection, "DB_PATH", isolated_db)

    from cast_server.routes import change_requests

    app = FastAPI()
    app.include_router(change_requests.router)

    _seed_goal(isolated_db)
    return {"client": TestClient(app), "db_path": isolated_db}


def _events(db_path: Path, cr_id: int) -> list[dict]:
    from cast_server.services import change_request_service

    return change_request_service.list_events(cr_id, db_path=db_path)


def _outbox(db_path: Path, cr_id: int) -> list[dict]:
    from cast_server.services import change_request_service

    return change_request_service.list_outbox(cr_id, db_path=db_path)


def _pin_fast_track(monkeypatch) -> None:
    """Pin the gate to ``gate-except-additions`` for the explicit fast-track-lane mechanism tests.

    refine-requirements-v3 (owner decision) flipped the GLOBAL default ``WRITEBACK_GATE_POLICY`` to
    ``gate-all`` — every change-request, additions included, now gates to ``proposed`` by default. The
    addition fast-track is therefore no longer the default; it is the gate's *other* lane, selected
    in-test here. The gate FUNCTION is consumed byte-unchanged — only the policy value differs (this
    is the "set the policy in-test" discipline that keeps the gate-consumed-unchanged guarantee
    provable without resting on the global default)."""
    import functools

    from cast_server.services import change_request_service

    monkeypatch.setattr(
        change_request_service, "gate_status",
        functools.partial(change_request_service.gate_status, policy="gate-except-additions"),
    )


# --------------------------------------------------------------------------- #
# Graduated trust by blast radius                                              #
# --------------------------------------------------------------------------- #

def test_pure_addition_fast_tracks_to_applied_and_queues_outbox(env, monkeypatch):
    """A pure addition (no target_quote) → status ``applied`` + a ``pending`` outbox row.

    The addition fast-track is the gate's ``gate-except-additions`` lane, pinned in-test (the goal's
    global default is now ``gate-all`` — see :func:`_pin_fast_track`). Proves the gate plumbing for
    the auto-apply lane is consumed byte-unchanged; only the policy value selects it."""
    _pin_fast_track(monkeypatch)
    client, db_path = env["client"], env["db_path"]
    resp = client.post(
        "/api/goals/rt-goal/change-requests",
        json={"kind": "addition", "proposed_body": "FR-099 New requirement.",
              "base_version": 1, "author": "cast-planner"},
    )
    assert resp.status_code == 201
    row = resp.json()
    assert row["status"] == "applied"
    assert row["kind"] == "addition"
    assert row["target_quote"] is None

    # The proposed event is recorded...
    events = _events(db_path, row["id"])
    assert [e["event_type"] for e in events] == ["proposed"]
    # ...and exactly one pending outbox FYI is queued (the auto-apply lane).
    outbox = _outbox(db_path, row["id"])
    assert len(outbox) == 1
    assert outbox[0]["status"] == "pending"


def test_pure_addition_is_gated_under_the_gate_all_default(env):
    """The goal's GLOBAL default (refine-requirements-v3 owner decision): a pure addition is ALSO
    gated — it intakes ``proposed`` with NO outbox FYI and awaits explicit human approval. This is
    the live default for this goal (gap-fill additions included); the fast-track lane above is the
    pinned ``gate-except-additions`` mechanism. The gate function is byte-unchanged either way."""
    client, db_path = env["client"], env["db_path"]
    resp = client.post(
        "/api/goals/rt-goal/change-requests",
        json={"kind": "addition", "proposed_body": "FR-098 Gated under gate-all.",
              "base_version": 1, "author": "cast-planner"},
    )
    assert resp.status_code == 201
    row = resp.json()
    assert row["status"] == "proposed"          # gated, not fast-tracked
    assert _outbox(db_path, row["id"]) == []     # a gated proposal queues no FYI


def test_modification_is_gated_to_proposed_with_no_outbox(env):
    """A modification of existing content → status ``proposed`` (gated), NO outbox row."""
    client, db_path = env["client"], env["db_path"]
    resp = client.post(
        "/api/goals/rt-goal/change-requests",
        json={"kind": "modification", "proposed_body": "FR-001 Revised wording.",
              "base_version": 2, "target_quote": "FR-001 Original wording.",
              "author": "cast-planner"},
    )
    assert resp.status_code == 201
    row = resp.json()
    assert row["status"] == "proposed"

    assert [e["event_type"] for e in _events(db_path, row["id"])] == ["proposed"]
    assert _outbox(db_path, row["id"]) == []  # gated lane queues nothing


def test_annotation_is_gated_to_proposed(env):
    """An annotation of existing content is also gated (only additions fast-track)."""
    client, db_path = env["client"], env["db_path"]
    resp = client.post(
        "/api/goals/rt-goal/change-requests",
        json={"kind": "annotation", "proposed_body": "Note: revisit this.",
              "base_version": 1, "target_quote": "FR-002 Some requirement.",
              "author": "cast-planner"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "proposed"


# --------------------------------------------------------------------------- #
# Validation                                                                   #
# --------------------------------------------------------------------------- #

def test_unknown_goal_is_404(env):
    resp = env["client"].post(
        "/api/goals/does-not-exist/change-requests",
        json={"kind": "addition", "proposed_body": "x", "base_version": 1, "author": "a"},
    )
    assert resp.status_code == 404


def test_missing_base_version_is_422(env):
    resp = env["client"].post(
        "/api/goals/rt-goal/change-requests",
        json={"kind": "addition", "proposed_body": "x", "author": "a"},
    )
    assert resp.status_code == 422


def test_empty_proposed_body_is_422(env):
    resp = env["client"].post(
        "/api/goals/rt-goal/change-requests",
        json={"kind": "addition", "proposed_body": "", "base_version": 1, "author": "a"},
    )
    assert resp.status_code == 422


def test_addition_with_target_quote_is_422(env):
    """The kind↔target cross-field rule: an addition must not carry a target_quote."""
    resp = env["client"].post(
        "/api/goals/rt-goal/change-requests",
        json={"kind": "addition", "proposed_body": "x", "base_version": 1,
              "target_quote": "something", "author": "a"},
    )
    assert resp.status_code == 422


def test_modification_without_target_quote_is_422(env):
    """A modification must name the region it changes."""
    resp = env["client"].post(
        "/api/goals/rt-goal/change-requests",
        json={"kind": "modification", "proposed_body": "x", "base_version": 1, "author": "a"},
    )
    assert resp.status_code == 422


def test_oversized_body_is_422(env):
    from cast_server.routes.change_requests import _MAX_BODY_BYTES

    resp = env["client"].post(
        "/api/goals/rt-goal/change-requests",
        json={"kind": "addition", "proposed_body": "x" * (_MAX_BODY_BYTES + 1),
              "base_version": 1, "author": "a"},
    )
    assert resp.status_code == 422


def test_agent_lane_without_author_is_422(env):
    """The agent lane must self-declare a name — an unattributed proposal is rejected."""
    resp = env["client"].post(
        "/api/goals/rt-goal/change-requests",
        json={"kind": "addition", "proposed_body": "x", "base_version": 1},
    )
    assert resp.status_code == 422


# --------------------------------------------------------------------------- #
# Same-door parity (FR-013)                                                    #
# --------------------------------------------------------------------------- #

def test_same_door_parity_human_vs_agent(env):
    """Human-shaped (HTMX) and agent-shaped (JSON) bodies persist identical columns
    except ``author``/``author_type`` — one handler, the distinction is data not a branch."""
    from cast_server.config import WRITEBACK_HUMAN_AUTHOR
    from cast_server.services import change_request_service

    client, db_path = env["client"], env["db_path"]
    shared = {"kind": "modification", "proposed_body": "Shared revised body.",
              "base_version": 3, "target_quote": "Original body.",
              "section_hint": "## Requirements"}

    # Agent lane — plain JSON, self-declared name + author_type="agent".
    agent_resp = client.post(
        "/api/goals/rt-goal/change-requests",
        json={**shared, "author": "cast-detailed-plan"},
    )
    assert agent_resp.status_code == 201
    agent_row = agent_resp.json()

    # Human lane — HTMX/browser context (HX-Request header). Posted author ignored.
    human_resp = client.post(
        "/api/goals/rt-goal/change-requests",
        data={**shared, "author": "ignored-by-server"},
        headers={"HX-Request": "true"},
    )
    assert human_resp.status_code == 200  # HTML fragment, not JSON 201
    assert "text/html" in human_resp.headers["content-type"]

    human_row = change_request_service.get(agent_row["id"] + 1, db_path=db_path)
    assert human_row is not None

    # Both lanes persisted IDENTICAL emitter columns...
    parity_cols = ("goal_slug", "kind", "proposed_body", "base_version",
                   "target_quote", "section_hint", "status")
    for col in parity_cols:
        assert agent_row[col] == human_row[col], f"column {col} should match across lanes"

    # ...and differ ONLY by author / author_type (data, not a code branch).
    assert agent_row["author_type"] == "agent"
    assert human_row["author_type"] == "human"
    assert agent_row["author"] == "cast-detailed-plan"
    assert human_row["author"] == WRITEBACK_HUMAN_AUTHOR


# --------------------------------------------------------------------------- #
# Anti-spoof                                                                   #
# --------------------------------------------------------------------------- #

def test_anti_spoof_browser_cannot_forge_human_author(env):
    """A browser-context request with a forged author gets the server-derived identity."""
    from cast_server.config import WRITEBACK_HUMAN_AUTHOR
    from cast_server.services import change_request_service

    client, db_path = env["client"], env["db_path"]
    resp = client.post(
        "/api/goals/rt-goal/change-requests",
        data={"kind": "addition", "proposed_body": "Sneaky addition.",
              "base_version": 1, "author": "ceo@example.com", "author_type": "human"},
        headers={"HX-Request": "true"},
    )
    assert resp.status_code == 200  # HTML fragment

    # The persisted row carries the server identity, never the forged one.
    rows = _all_requests(db_path)
    assert len(rows) == 1
    assert rows[0]["author"] == WRITEBACK_HUMAN_AUTHOR
    assert rows[0]["author"] != "ceo@example.com"
    assert rows[0]["author_type"] == "human"


def test_agent_cannot_claim_human_author_type(env):
    """A non-HTMX (agent-lane) request is always ``author_type="agent"`` — it cannot claim human."""
    client, db_path = env["client"], env["db_path"]
    resp = client.post(
        "/api/goals/rt-goal/change-requests",
        json={"kind": "addition", "proposed_body": "x", "base_version": 1,
              "author": "cast-x", "author_type": "human"},  # posted author_type ignored
    )
    assert resp.status_code == 201
    assert resp.json()["author_type"] == "agent"


# --------------------------------------------------------------------------- #
# Transactionality                                                             #
# --------------------------------------------------------------------------- #

def test_intake_is_all_or_nothing_on_event_insert_failure(env, monkeypatch):
    """A failure after the change_requests insert leaves NO orphaned rows (single txn)."""
    from cast_server.services import change_request_service

    db_path = env["db_path"]

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated crash after the change_requests insert")

    monkeypatch.setattr(change_request_service, "_append_event", _boom)

    with pytest.raises(RuntimeError):
        change_request_service.create(
            "rt-goal", kind="addition", proposed_body="FR-100 doomed.",
            base_version=1, author="cast-x", author_type="agent", db_path=db_path,
        )

    # Nothing committed anywhere — the request, event, and outbox tables are all empty.
    assert _all_requests(db_path) == []
    assert _count(db_path, "change_request_events") == 0
    assert _count(db_path, "notifications_outbox") == 0


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

def _all_requests(db_path: Path) -> list[dict]:
    from cast_server.db.connection import get_connection

    conn = get_connection(db_path)
    try:
        rows = conn.execute("SELECT * FROM change_requests ORDER BY id").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _count(db_path: Path, table: str) -> int:
    from cast_server.db.connection import get_connection

    conn = get_connection(db_path)
    try:
        return conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
    finally:
        conn.close()
