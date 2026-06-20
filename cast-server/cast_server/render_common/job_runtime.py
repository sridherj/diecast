"""The single-flight registry + in-flight semaphore + lazy reaper + `render_jobs` row I/O.

The shared concurrency mechanism both render-jobs run on. A render-job supplies its job-state
objects (anything matching `JobSlot` — a `key`, a `slot_held` flag, an optional `thread`); this
module owns the registry, the bounded in-flight semaphore, the per-slot accounting, the row I/O
against the `render_jobs` observability table, and the lazy reaper that declares a stale `running`
row orphaned (heartbeat past the derived ceiling AND no live thread) and releases its leaked slot.

Generic by construction: nothing here imports a render-job module or any requirements-specific
type. The `render_jobs` table is the shared observability surface (never the readiness key — the
published artifact's embedded digest is that). A render-job instantiates ONE `JobRegistry` and
exposes its members under whatever module names its existing callers/tests expect.
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Protocol

from cast_server.db.connection import get_connection

logger = logging.getLogger(__name__)


# ======================================================================================
# Time helpers
# ======================================================================================
def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def utcnow_iso() -> str:
    return utcnow().isoformat()


def age_seconds(ts: str | None, now: datetime) -> float | None:
    """Seconds between an ISO timestamp and `now`, or None if unparseable/absent."""
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (now - dt).total_seconds()


# ======================================================================================
# render_jobs row I/O (the observability surface — never the readiness key)
# ======================================================================================
def insert_job(goal_slug: str, source_hash: str, db_path) -> int:
    now = utcnow_iso()
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO render_jobs (goal_slug, source_hash, status, attempts, "
            "started_at, heartbeat_at) VALUES (?, ?, 'running', 0, ?, ?)",
            (goal_slug, source_hash, now, now),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def update_job(row_id: int | None, db_path, **fields) -> None:
    if not fields or row_id is None:
        return
    cols = ", ".join(f"{k} = ?" for k in fields)
    vals = [*fields.values(), row_id]
    conn = get_connection(db_path)
    try:
        conn.execute(f"UPDATE render_jobs SET {cols} WHERE id = ?", vals)
        conn.commit()
    finally:
        conn.close()


def get_job_row(row_id: int, db_path=None) -> dict | None:
    """Fetch a render_jobs row as a dict (status surface for the route + tests)."""
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM render_jobs WHERE id = ?", (row_id,)).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def latest_job_row(goal_slug: str, source_hash: str, db_path=None) -> dict | None:
    """The most recent render_jobs row for ``(goal_slug, source_hash)``, or None."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM render_jobs WHERE goal_slug = ? AND source_hash = ? "
            "ORDER BY id DESC LIMIT 1",
            (goal_slug, source_hash),
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def heartbeat(row_id: int | None, db_path, attempts: int) -> None:
    """Stamp `heartbeat_at` (+ the running attempt count) at a stage boundary (the reaper's
    staleness detector). Shared by both render-jobs' `_heartbeat`."""
    if row_id is not None:
        update_job(row_id, db_path, heartbeat_at=utcnow_iso(), attempts=attempts)


def write_artifact(job_dir, name: str, content: str) -> None:
    """Persist a job working artifact under the job dir (best-effort; never raises)."""
    try:
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / name).write_text(content, encoding="utf-8")
    except OSError as exc:
        logger.warning("could not write job artifact %s: %s", name, exc)


def stage_timeout(stage: str, stage_timeouts: list, default: int = 60) -> int:
    """The configured per-stage subprocess timeout (seconds). Reads the passed stage list so tests
    can monkeypatch it."""
    for name, secs in stage_timeouts:
        if name == stage:
            return secs
    return default


def finalize_job(row_id: int | None, db_path, status: str, *, error: str | None,
                 attempts: int, human_review: int = 0, review_reason: str | None = None,
                 published_attempt: int | None = None, published_score: float | None = None) -> None:
    """Record a terminal render_jobs row — every terminal state is a row with a reason (zero silent
    failures). Shared by both render-jobs' `_finalize`."""
    now = utcnow_iso()
    update_job(row_id, db_path, status=status, error=error, attempts=attempts,
               finished_at=now, heartbeat_at=now, human_review=human_review,
               review_reason=review_reason, published_attempt=published_attempt,
               published_score=published_score)


def build_envelope(header: str, *, digest_line: str, served_by: str,
                   human_review: bool, review_reason: str | None,
                   served_by_prefix: str = "<!-- served-by: ", served_by_suffix: str = " -->",
                   human_review_prefix: str = "<!-- human-review: ",
                   human_review_suffix: str = " -->",
                   review_reason_prefix: str = "<!-- review-reason: ",
                   review_reason_suffix: str = " -->") -> list[str]:
    """The shared published-page envelope lines: AUTO-GENERATED header + a digest line + served-by
    (+ optional human-review / review-reason). A clean publish omits the human-review lines."""
    lines = [header, digest_line, f"{served_by_prefix}{served_by}{served_by_suffix}"]
    if human_review:
        lines.append(f"{human_review_prefix}1{human_review_suffix}")
        if review_reason:
            lines.append(f"{review_reason_prefix}{review_reason}{review_reason_suffix}")
    return lines


# ======================================================================================
# JobSlot protocol — the minimal shape the registry / reaper key on
# ======================================================================================
class JobSlot(Protocol):
    key: tuple[str, str]
    slot_held: bool
    thread: threading.Thread | None


# ======================================================================================
# JobRegistry — the single-flight registry + in-flight semaphore + lazy reaper
# ======================================================================================
class JobRegistry:
    """One instance of the shared concurrency mechanism for a render-job.

    Owns the `(slug, hash) → JobSlot` registry, a bounded in-flight semaphore, the held-slot set,
    and the lazy reaper. A render-job creates ONE of these and re-exports its bound methods/fields
    under the module names its callers and tests use (`_registry`, `_acquire_slot`, …).
    """

    def __init__(self, max_inflight: int) -> None:
        self.registry: dict[tuple[str, str], JobSlot] = {}
        self.registry_lock = threading.Lock()
        self._inflight = threading.BoundedSemaphore(max_inflight)
        self._slot_lock = threading.Lock()
        self._slots_held: set[tuple[str, str]] = set()

    def acquire_slot(self, state: JobSlot) -> None:
        """Block until an in-flight slot is free, then mark it held."""
        self._inflight.acquire()
        with self._slot_lock:
            state.slot_held = True
            self._slots_held.add(state.key)

    def release_slot(self, state: JobSlot) -> None:
        """Release a held in-flight slot exactly once (idempotent via the `slot_held` flag)."""
        with self._slot_lock:
            if not state.slot_held:
                return
            state.slot_held = False
            self._slots_held.discard(state.key)
            self._inflight.release()

    def reset(self, *, max_inflight: int) -> None:
        """Test hook: clear the registry + held-slot set and rebuild the semaphore."""
        with self.registry_lock:
            self.registry.clear()
        with self._slot_lock:
            self._slots_held.clear()
            self._inflight = threading.BoundedSemaphore(max_inflight)

    def slots_held(self) -> frozenset[tuple[str, str]]:
        """The set of (slug, hash) keys currently holding an in-flight slot."""
        with self._slot_lock:
            return frozenset(self._slots_held)

    def reap_stale_jobs(self, *, ceiling: int, db_path=None) -> list[int]:
        """Mark every orphaned `running` render_jobs row `failed` and release any slot it leaked.

        An orphan is a `running` row whose `heartbeat_at` is older than `ceiling` AND has no live
        thread (after a restart the in-memory registry is empty, so the ceiling is the real guard).
        A job blocked on a slot has a *live* thread and is never reaped. The reaper MUST release the
        in-flight slot of a reaped orphan — else a crashed-thread orphan leaks a slot permanently.
        Returns the reaped row ids.
        """
        now = utcnow()
        conn = get_connection(db_path)
        try:
            rows = conn.execute(
                "SELECT id, goal_slug, source_hash, heartbeat_at, started_at "
                "FROM render_jobs WHERE status = 'running'"
            ).fetchall()
        finally:
            conn.close()

        reaped: list[int] = []
        for row in rows:
            age = age_seconds(row["heartbeat_at"] or row["started_at"], now)
            if age is None or age <= ceiling:
                continue
            key = (row["goal_slug"], row["source_hash"])
            with self.registry_lock:
                state = self.registry.get(key)
                live = state is not None and state.thread is not None and state.thread.is_alive()
                if live:
                    continue  # genuinely running (e.g. blocked on a slot) — not an orphan
                if state is not None:
                    self.release_slot(state)  # free the leaked slot
                    self.registry.pop(key, None)
            update_job(
                row["id"], db_path, status="failed",
                error=f"reaped: stale heartbeat past ceiling ({int(age)}s > {ceiling}s, "
                      "no live thread)",
                finished_at=utcnow_iso(),
            )
            reaped.append(row["id"])
        return reaped
