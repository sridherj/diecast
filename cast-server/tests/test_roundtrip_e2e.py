"""SC-006 — the round-trip write-back end-to-end proof (Phase 5, sp5).

A **simulated** downstream change (``fixtures/synthetic_child.py`` — real emitters are
hard-deferred) traces the *entire* receiving chain green and, more importantly, proves the
**negatives** that are the whole point of Phase 5:

    emit ``requirements_writeback`` → same-door intake (``POST …/change-requests``) →
    ``change_request`` row → conflict verdict → surgical file apply (the sole-writer carve-out) →
    version bump → change summary with a provenance badge → ``notifications_outbox`` row →
    relay drain → de-duplicated notification surfaced.

The three SC-006 assertions:

* **Full happy-path chain green for a pure addition** — every link above produces its artifact.
* **0 ungated modifications** — existing content is NEVER mutated without either passing the
  graduated-trust gate or surfacing a conflict. A modification intakes ``proposed`` (gated, file
  untouched, no FYI queued); an apply over a region a human changed since ``base_version`` is
  *refused* (``conflicted``), file byte-identical, audit row left. The negative, not the happy path.
* **0 lost / 0 duplicate notifications after an injected crash between commit and relay** — a crash
  mid-drain re-delivers nothing already flipped and loses nothing pending (at-least-once), and the
  read surface dedupes on ``change_request_id`` so a change with *two* outbox rows (intake FYI +
  apply FYI) surfaces exactly once.

This test drives **no live subagent** — it exercises the deterministic service + route path with
the pure ``verbatim_locate`` locator, so it stays in the default suite (it is the binary SC-006
gate, not a slow ``eval_`` test). The live-subagent orchestration (``cast-requirements-writeback`` /
``cast-comment-reanchor``) is unit-proven separately; SC-006 proves the *mechanism* closes the loop.

DB isolation follows ``test_change_request_intake.py``: ``isolated_db`` swaps ``config.DB_PATH`` and
this fixture also patches ``connection.DB_PATH`` so the route's no-explicit-path service calls land
on the hermetic test DB. The goal's ``folder_path`` points at a ``tmp_path`` goal dir so the apply
path is scoped there, never at the real ``GOALS_DIR``.
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

from tests.fixtures import synthetic_child  # noqa: E402  (sys.path set just above)

FILENAME = "refined_requirements.collab.md"
SLUG = "rt-e2e-goal"

# A frozen, realistic requirements document with a stable FR table to anchor against. FR ids are
# 3+ digits (the landed grammar ``\bFR-(\d{3,})\b``).
_DOC = (
    "# Refined Requirements\n"
    "\n"
    "## Functional Requirements\n"
    "\n"
    "| ID | Requirement | Source |\n"
    "|----|-------------|--------|\n"
    "| FR-001 | The system MUST record a proposal. | US1 |\n"
    "| FR-002 | The system MUST notify on apply. | US2 |\n"
    "\n"
    "## Out of Scope\n"
    "\n"
    "- Real-time co-editing.\n"
)


# --------------------------------------------------------------------------- #
# Fixtures / helpers                                                           #
# --------------------------------------------------------------------------- #

def _seed_goal(db_path: Path, folder_path: str) -> None:
    from cast_server.db.connection import get_connection

    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) VALUES (?, ?, ?)",
            (SLUG, "Round-trip e2e goal", folder_path),
        )
        conn.commit()
    finally:
        conn.close()


def _snapshot(slug: str, content: str, db_path: Path) -> int:
    from cast_server.services import requirement_version_service

    return requirement_version_service.create_snapshot(slug, content, db_path=db_path)["version"]


@pytest.fixture
def goal_dir(tmp_path: Path) -> Path:
    """A goal dir holding the byte-canonical requirements file under a ``tmp_path`` goals root."""
    d = tmp_path / "goals" / SLUG
    d.mkdir(parents=True)
    (d / FILENAME).write_text(_DOC, encoding="utf-8")
    return d


@pytest.fixture
def goals_root(goal_dir: Path) -> Path:
    return goal_dir.parent


@pytest.fixture
def env(isolated_db: Path, monkeypatch, goal_dir: Path):
    """TestClient over the same-door intake router on a hermetic DB seeded with v1 of the goal."""
    from cast_server.db import connection as _connection
    monkeypatch.setattr(_connection, "DB_PATH", isolated_db)

    from cast_server.routes import change_requests

    app = FastAPI()
    app.include_router(change_requests.router)

    _seed_goal(isolated_db, str(goal_dir))
    _snapshot(SLUG, _DOC, isolated_db)   # base_version 1 == the on-disk content
    return {"client": TestClient(app), "db_path": isolated_db}


def _intake(client: TestClient, proposal: dict) -> dict:
    """POST one extracted write-back proposal through the same-door agent lane; return the row."""
    resp = client.post(f"/api/goals/{SLUG}/change-requests",
                       json={**proposal, "author": "cast-high-level-planner"})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _pin_fast_track(monkeypatch) -> None:
    """Pin the gate to ``gate-except-additions`` for the SC-006 fast-track / auto-apply lane proofs.

    refine-requirements-v3 (owner decision) flipped the GLOBAL default ``WRITEBACK_GATE_POLICY`` to
    ``gate-all`` (every change-request gated, additions included). These SC-006 mechanism tests
    exercise the addition fast-track lane specifically (intake-FYI + the two-outbox-row dedup chain),
    so they select that lane in-test. The gate FUNCTION is consumed byte-unchanged — only the policy
    value differs (the "set the policy in-test" discipline)."""
    import functools

    from cast_server.services import change_request_service

    monkeypatch.setattr(
        change_request_service, "gate_status",
        functools.partial(change_request_service.gate_status, policy="gate-except-additions"),
    )


# --------------------------------------------------------------------------- #
# SC-006 (1): the full happy-path chain is green for a pure addition           #
# --------------------------------------------------------------------------- #

def test_addition_traces_the_whole_chain_green(env, goal_dir, goals_root, monkeypatch):
    """emit → intake → apply → version bump → change summary + provenance → outbox → notification.

    Exercises the addition fast-track lane (pinned ``gate-except-additions``; the goal's global
    default is now ``gate-all`` — see :func:`_pin_fast_track`), so the SC-006 auto-apply chain stays
    proven end-to-end with the gate consumed byte-unchanged."""
    from cast_server.services import change_request_service, notification_service

    _pin_fast_track(monkeypatch)
    client, db = env["client"], env["db_path"]

    # 1. The simulated downstream emitter writes a contract-v2 envelope; we extract the proposal.
    output = synthetic_child.emit_output(
        "run_synthetic_001",
        [synthetic_child.writeback_artifact(
            kind="addition",
            proposed_body="| FR-099 | The system MUST trace provenance end-to-end. | US9 |",
            base_version=1,
            section_hint="Functional Requirements",
            origin_phase="planning",
            origin_artifact_path="plan.collab.md",
        )],
    )
    proposals = synthetic_child.extract_writebacks(output)
    assert len(proposals) == 1

    # 2. Same-door intake — a pure addition fast-tracks to `applied` and queues a FYI outbox row.
    row = _intake(client, proposals[0])
    assert row["status"] == "applied"
    assert row["author_type"] == "agent"            # server-derived, not emitter-stamped (FR-013)
    cr_id = row["id"]

    # 3. The sole-writer carve-out applies the change surgically to the on-disk .collab.md.
    result = change_request_service.apply_for_goal(
        SLUG, cr_id, goals_dir=goals_root, db_path=db)

    assert result["status"] == "applied"
    assert result["applied_version"] == 2                       # base was version 1
    assert result["change_summary"]["counts"]["added"] == 1     # deterministic block diff
    badge = result["provenance_badge"]
    assert "FR-099" in badge
    assert "planning" in badge and "plan.collab.md" in badge    # provenance: what + from where

    # 4. The file carries the new row; every other byte is identical (surgical splice).
    after = (goal_dir / FILENAME).read_text(encoding="utf-8")
    added = "| FR-099 | The system MUST trace provenance end-to-end. | US9 |"
    assert added in after
    assert after.replace(added + "\n", "", 1) == _DOC

    # 5. Relay drains the outbox; the round-trip descriptor surfaces the change exactly once.
    notification_service.drain_outbox(db_path=db)
    writebacks = notification_service.recent_writebacks(SLUG, db_path=db)
    surfaced = [w for w in writebacks if w["change_request_id"] == cr_id]
    assert len(surfaced) == 1
    assert surfaced[0]["origin_phase"] == "planning"
    assert surfaced[0]["origin_artifact_path"] == "plan.collab.md"


# --------------------------------------------------------------------------- #
# SC-006 (2): 0 ungated modifications — existing content is never silently mutated #
# --------------------------------------------------------------------------- #

def test_modification_is_gated_at_intake_file_untouched(env, goal_dir):
    """A modification of existing content intakes ``proposed`` (gated) — never auto-applied.

    The negative: under ``WRITEBACK_GATE_POLICY="gate-except-additions"`` a change that touches an
    existing region must wait for a human gate. Intake records it ``proposed`` with NO FYI outbox
    row, and — critically — the byte-canonical file is untouched (intake writes no file).
    """
    from cast_server.services import change_request_service

    client, db = env["client"], env["db_path"]
    before = (goal_dir / FILENAME).read_text(encoding="utf-8")

    output = synthetic_child.emit_output(
        "run_synthetic_002",
        [synthetic_child.writeback_artifact(
            kind="modification",
            proposed_body="| FR-002 | The system MUST notify on apply AND record provenance. | US2 |",
            base_version=1,
            target_quote="The system MUST notify on apply.",
            section_hint="Functional Requirements",
        )],
    )
    row = _intake(client, synthetic_child.extract_writebacks(output)[0])

    assert row["status"] == "proposed", "a modification must be gated, never auto-applied"
    assert change_request_service.list_outbox(row["id"], db_path=db) == [], \
        "a gated proposal queues NO notification (nothing applied to announce)"
    assert (goal_dir / FILENAME).read_text(encoding="utf-8") == before, \
        "intake must not mutate the byte-canonical file"


def test_conflicted_modification_is_refused_file_untouched(env, goal_dir, goals_root):
    """Applying a modification over a region a human changed since ``base_version`` is REFUSED.

    The load-bearing negative (US7's silent-drift bug): even once a modification is accepted, if the
    target region diverged from the version the change assumed, the apply surfaces a ``conflicted``
    verdict and leaves the file byte-identical — never a silent overwrite. An audit row is left.
    """
    from cast_server.services import change_request_service

    client, db = env["client"], env["db_path"]

    # A human edits FR-001 on disk AFTER base_version 1 was snapshotted (region diverged from base).
    head_doc = _DOC.replace(
        "| FR-001 | The system MUST record a proposal. | US1 |",
        "| FR-001 | The system MUST record a proposal AND its origin. | US1 |")
    (goal_dir / FILENAME).write_text(head_doc, encoding="utf-8")

    output = synthetic_child.emit_output(
        "run_synthetic_003",
        [synthetic_child.writeback_artifact(
            kind="modification",
            proposed_body="| FR-001 | clobbering text | US1 |",
            base_version=1,
            target_quote="FR-001",
            section_hint="Functional Requirements",
        )],
    )
    cr_id = _intake(client, synthetic_child.extract_writebacks(output)[0])["id"]

    before = (goal_dir / FILENAME).read_text(encoding="utf-8")
    with pytest.raises(change_request_service.WritebackRefused) as exc:
        change_request_service.apply_for_goal(SLUG, cr_id, goals_dir=goals_root, db_path=db)

    assert exc.value.verdict == "conflicted"
    assert exc.value.surface["choices"], "the 3-way resolution surface is offered (no auto-merge)"
    assert (goal_dir / FILENAME).read_text(encoding="utf-8") == before, "file left byte-identical"
    events = change_request_service.list_events(cr_id, db_path=db)
    assert any(e["event_type"] == "conflicted" for e in events), "a conflicted audit row was left"


# --------------------------------------------------------------------------- #
# SC-006 (3): 0 lost / 0 duplicate notifications across an injected crash       #
# --------------------------------------------------------------------------- #

def test_crash_between_commit_and_relay_loses_nothing_duplicates_nothing(
    env, goals_root, monkeypatch):
    """A crash mid-drain re-delivers nothing flipped, loses nothing pending, dedupes to one item.

    The addition path queues TWO outbox rows for one change_request — the sp2 intake FYI and the
    sp4 apply FYI. We inject a crash on the FIRST delivery attempt (between the committed outbox
    write and the relay flip), then recover. At-least-once delivery means the crashed row is
    re-delivered on the next pass (0 lost); the ``status='pending'`` filter means an already-flipped
    row is never re-selected (0 duplicate at the relay); and ``recent_writebacks`` dedupes on
    ``change_request_id`` so the change surfaces exactly once even with two outbox rows.

    Exercises the addition fast-track lane (pinned ``gate-except-additions``; the goal's global
    default is now ``gate-all`` — see :func:`_pin_fast_track`) so the two-outbox-row dedup chain is
    still proven.
    """
    from cast_server.services import change_request_service, notification_service

    _pin_fast_track(monkeypatch)
    client, db = env["client"], env["db_path"]

    output = synthetic_child.emit_output(
        "run_synthetic_004",
        [synthetic_child.writeback_artifact(
            kind="addition",
            proposed_body="| FR-100 | The system MUST survive a crash mid-relay. | US10 |",
            base_version=1,
            section_hint="Functional Requirements",
        )],
    )
    cr_id = _intake(client, synthetic_child.extract_writebacks(output)[0])["id"]
    change_request_service.apply_for_goal(SLUG, cr_id, goals_dir=goals_root, db_path=db)

    # Two outbox rows exist for this one change_request (intake FYI + apply FYI).
    assert len(change_request_service.list_outbox(cr_id, db_path=db)) == 2

    delivered_ids: list[int] = []
    crashed = {"done": False}
    real_deliver = notification_service._deliver

    def flaky_deliver(row: dict) -> None:
        # Inject exactly one crash, on the first delivery attempt, BEFORE the relay flip commits.
        if not crashed["done"]:
            crashed["done"] = True
            raise RuntimeError("injected crash between commit and relay")
        delivered_ids.append(row["id"])
        real_deliver(row)

    monkeypatch.setattr(notification_service, "_deliver", flaky_deliver)

    # Pass 1 crashes partway — nothing is lost, the pending rows remain pending.
    with pytest.raises(RuntimeError):
        notification_service.drain_outbox(db_path=db)

    # Pass 2 (recovery) drains cleanly; the relay is at-least-once.
    monkeypatch.setattr(notification_service, "_deliver", real_deliver)
    notification_service.drain_outbox(db_path=db)

    # 0 lost: both outbox rows are delivered after recovery.
    outbox = change_request_service.list_outbox(cr_id, db_path=db)
    assert all(o["status"] == "delivered" for o in outbox)
    # 0 duplicate at the read surface: the change surfaces exactly once despite two outbox rows.
    writebacks = notification_service.recent_writebacks(SLUG, db_path=db)
    surfaced = [w for w in writebacks if w["change_request_id"] == cr_id]
    assert len(surfaced) == 1
