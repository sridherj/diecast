"""Notification outbox relay + round-trip descriptor (refine-requirements-v2 Phase 5, sp3b).

The *delivery* half of the transactional outbox that fixes the dual-write trap. sp2 writes a
``notifications_outbox`` row **in the same transaction** as the auto-applied ``change_request``
(so the change and its alert commit atomically — no alert without its change, no change without
its alert). This module **drains** that outbox: a lifespan-managed polling relay reads
``status='pending'`` rows and flips them to ``'delivered'``, **at-least-once**.

"Delivery" is deliberately a *status flip*, not a side-effecting push: the human Goal-Card badge
and the agent ``/inbox`` both *read* the round-trip descriptor (:func:`recent_writebacks`), which
is sourced from ``delivered`` outbox rows joined to their ``change_requests``. This makes the
whole path naturally idempotent — re-running the relay after a crash re-delivers nothing already
flipped, and the read surface **dedupes on ``change_request_id``** so a change surfaces exactly
once even if two outbox rows ever pointed at it (0 lost / 0 duplicate, SC-006).

This does **not** stand up a parallel notifier: the descriptor rides the **existing** structured
``{convergence, open_comment_count}`` surface that Phase 4 landed (owner decision #4 — extend,
never structure-from-boolean). House DB pattern: flat module-level functions + injectable
``db_path`` + ``get_connection(db_path)`` + ``dict(row)`` — modeled on ``comment_service`` /
``change_request_service``.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from cast_server.db.connection import get_connection

logger = logging.getLogger(__name__)

# Polling cadence for the relay loop. A constant (with an env override) rather than a config.py
# entry — sp3b's touch-set is intentionally narrow. Polling is the right weight at SQLite scale
# (no CDC/Debezium); the relay is at-least-once, so a slightly stale poll never loses an alert.
NOTIFICATION_RELAY_INTERVAL = int(os.environ.get("CAST_NOTIFICATION_RELAY_INTERVAL", "5"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------- #
# Drain — the at-least-once relay step                                          #
# --------------------------------------------------------------------------- #

def _deliver(row: dict) -> None:
    """Deliver one outbox notification.

    Delivery here is the *status flip* (done by the caller); the human badge + agent ``/inbox``
    read the descrip­tor from ``delivered`` rows. This hook exists so the surface is observable
    (and extensible to a real push later) without changing the at-least-once contract.
    """
    logger.info(
        "Notification delivered: change_request_id=%s outbox_id=%s",
        row.get("change_request_id"), row.get("id"),
    )


def drain_outbox(*, db_path: Path | None = None) -> list[dict]:
    """Deliver every ``pending`` outbox row and mark it ``delivered``. At-least-once, idempotent.

    Reads ``notifications_outbox WHERE status='pending'`` oldest-first, calls :func:`_deliver`,
    and flips each to ``delivered`` with a ``delivered_at`` stamp. Each flip is its own committed
    write, so a crash mid-drain leaves already-delivered rows delivered and the rest ``pending``
    for the next poll (a re-run delivers them — the alert is never lost). Re-running with no
    ``pending`` rows is a clean no-op. Returns the rows delivered on this pass (the pre-flip
    snapshots).
    """
    conn = get_connection(db_path)
    try:
        pending = conn.execute(
            "SELECT * FROM notifications_outbox WHERE status='pending' ORDER BY id"
        ).fetchall()
        delivered: list[dict] = []
        for row in pending:
            rowd = dict(row)
            _deliver(rowd)
            with conn:
                conn.execute(
                    "UPDATE notifications_outbox SET status='delivered', delivered_at=? WHERE id=?",
                    (_now(), rowd["id"]),
                )
            delivered.append(rowd)
        return delivered
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Round-trip descriptor — what the badge + /inbox read (the EXTENDED surface)   #
# --------------------------------------------------------------------------- #

def _summarize(payload: dict, kind: str) -> str:
    """"What changed + from where", from the denormalized outbox payload (FR-019)."""
    origin = payload.get("origin_phase") or "a downstream phase"
    return f"requirements updated from {origin}: {kind}"


def recent_writebacks(goal_slug: str, *, limit: int = 20,
                      db_path: Path | None = None) -> list[dict]:
    """The round-trip / provenance descriptor for ``goal_slug`` — newest first, deduped.

    Sourced from **delivered** outbox rows joined to their ``change_requests`` (so it surfaces a
    write-back only once the relay has delivered it). Dedupes on ``change_request_id`` — a change
    surfaces exactly once even if more than one outbox row ever pointed at it (the SC-006
    0-duplicate guarantee). Each item is the FR-019 shape the human badge and the agent ``/inbox``
    both consume:

        {change_request_id, summary, origin_phase, origin_artifact_path, applied_at}
    """
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            """SELECT o.change_request_id AS change_request_id,
                      o.payload           AS payload,
                      o.delivered_at      AS delivered_at,
                      cr.kind             AS kind,
                      cr.origin_phase     AS origin_phase,
                      cr.origin_artifact_path AS origin_artifact_path
               FROM notifications_outbox o
               JOIN change_requests cr ON cr.id = o.change_request_id
               WHERE cr.goal_slug = ? AND o.status = 'delivered'
               ORDER BY o.id DESC""",
            (goal_slug,),
        ).fetchall()
    finally:
        conn.close()

    out: list[dict] = []
    seen: set[int] = set()
    for row in rows:
        cr_id = row["change_request_id"]
        if cr_id in seen:                      # dedupe on change_request_id (0-duplicate)
            continue
        seen.add(cr_id)
        try:
            payload = json.loads(row["payload"]) if row["payload"] else {}
        except (json.JSONDecodeError, TypeError):
            payload = {}
        out.append({
            "change_request_id": cr_id,
            "summary": _summarize(payload, row["kind"]),
            "origin_phase": row["origin_phase"],
            "origin_artifact_path": row["origin_artifact_path"],
            "applied_at": row["delivered_at"],
        })
        if len(out) >= limit:
            break
    return out


# --------------------------------------------------------------------------- #
# The lifespan-managed relay loop (app.py starts/cancels this)                  #
# --------------------------------------------------------------------------- #

async def run_relay(db_path: Path | None = None) -> None:
    """Poll-drain the outbox forever. Mirrors the dispatcher/monitor loop precedent in app.py.

    One bad iteration is logged and swallowed so the loop never dies. Cancelled on app shutdown.
    """
    logger.info("Notification relay started")
    while True:
        try:
            drain_outbox(db_path=db_path)
        except Exception:
            logger.exception("Notification relay iteration failed")
        await asyncio.sleep(NOTIFICATION_RELAY_INTERVAL)
