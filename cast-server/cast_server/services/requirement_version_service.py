"""Version snapshots for the requirements thin spine (refine-requirements-v2 Phase 1).

DB-only: writes ``requirement_versions``; NEVER touches goal files (the ``.collab.md``
stays byte-canonical — a snapshot is a *copy into* the DB, per the delegation contract
that cast-server never writes artifact files).

House DB pattern: flat module-level functions + injectable ``db_path`` +
``get_connection(db_path)`` in a try/finally, ``dict(row)`` row→dict conversion — modeled
on ``goal_service.py`` / ``task_service.py`` (NOT ``orchestration_service.py``, which is
file/manifest-based — plan-review Decision #1).

Phase 4's ``comment_service`` inherits this exact shape; Phase 4's ``create_next()``
open-comment gate builds ON ``create_snapshot`` (do not pre-build that gate here).
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from cast_server.db.connection import get_connection
from cast_server.requirements_render import parse_requirements
from cast_server.requirements_render.block_diff import diff_blocks, summarize
from cast_server.requirements_render.hashing import content_hash

# FR-017 size caps for stored narration: overview <= 2 KB, each note <= 2 KB, <= 1 note per item.
_NARRATION_FIELD_MAX_BYTES = 2 * 1024


class NarrationVersionNotFound(Exception):
    """``base`` or ``head`` version absent for the goal (route → 404)."""


class NarrationValidationError(Exception):
    """Narration references a change absent from the recomputed deterministic set, or violates a
    size cap (route → 422). ``offending_keys`` lists the ``[change, heading_or_ref]`` pairs that
    did not match a deterministic item (empty for size-cap / undiffable-snapshot failures)."""

    def __init__(self, message: str, offending_keys: list | None = None) -> None:
        super().__init__(message)
        self.offending_keys = offending_keys or []


def create_snapshot(goal_slug: str, content: str, created_by: str | None = None,
                    *, db_path: Path | None = None) -> dict:
    """Record a content-hash-idempotent snapshot of a goal's requirements file.

    Idempotent: if the current version's hash == ``content_hash(content)``, return that
    row unchanged (no new row). Otherwise insert ``version = (max existing version) + 1``
    as ``'current'`` and flip the prior ``'current'`` row to ``'archived'`` — in ONE
    transaction (single ``commit()``; no window where two rows are ``'current'`` for the
    same goal).

    Concurrency (plan-review Decision #5): ``version = max + 1`` is a read-then-write.
    Under the default deferred BEGIN, two concurrent snapshots for the same goal could
    both read the same max and one insert would hit ``UNIQUE(goal_slug, version)``.
    ACCEPTED as a single-user/local limitation — no locking change now. Fix-forward if
    concurrency ever appears: wrap read+insert+archive-flip in a single ``BEGIN IMMEDIATE``
    so the max-read and insert serialize. Phase 4's ``create_next()`` inherits this discipline.

    Returns the plain row-dict of the current (or unchanged) version.
    """
    h = content_hash(content)
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection(db_path)
    try:
        current = conn.execute(
            "SELECT * FROM requirement_versions WHERE goal_slug = ? AND status = 'current'",
            (goal_slug,),
        ).fetchone()
        if current is not None and current["content_hash"] == h:
            return dict(current)  # idempotent no-op — identical content, no new row

        next_version = conn.execute(
            "SELECT COALESCE(MAX(version), 0) AS m FROM requirement_versions WHERE goal_slug = ?",
            (goal_slug,),
        ).fetchone()["m"] + 1

        # One transaction: archive the prior current, insert the new current, single commit.
        if current is not None:
            conn.execute(
                "UPDATE requirement_versions SET status = 'archived' WHERE id = ?",
                (current["id"],),
            )
        cur = conn.execute(
            """INSERT INTO requirement_versions
               (goal_slug, version, content, content_hash, status, created_at, created_by)
               VALUES (?, ?, ?, ?, 'current', ?, ?)""",
            (goal_slug, next_version, content, h, now, created_by),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM requirement_versions WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


def create_next(goal_slug: str, content: str, created_by: str | None = None,
                *, db_path: Path | None = None) -> dict:
    """Snapshot the next version and report comment convergence + displacement.

    The version *gate* for the iteration loop (sp3, critical path sp1 → sp3 → sp4b). It
    wraps :func:`create_snapshot` — inheriting hash idempotency, the single-txn archive-flip,
    and the documented ``BEGIN IMMEDIATE`` fix-forward note — then layers on the comment
    bookkeeping the agent loop needs:

    * **Convergence** — derived, never stored: ``"unconverged"`` iff
      ``open_comment_count(goal_slug) > 0`` else ``"converged"`` (the one convergence rule).
    * **Carry-forward = do nothing.** Open comment rows keep their original ``version`` (the
      provenance of where they were left). "Current" open comments are simply ``state='open'``
      regardless of version — no row copying, no remapping.
    * **Displacement** — ``displaced_comment_ids`` = open comments whose ``quoted_text`` is NOT
      a verbatim substring of ``content``. This is the deterministic needs-LLM *detector* (a
      pure string-find — no LLM, no subprocess); the seam sp4b dispatches ``cast-comment-reanchor``
      over. Nothing positional is stored: a crash between this snapshot and the caller's
      re-anchor dispatch loses nothing — the next ``list_comments`` recomputes displacement.

    ``create_next`` NEVER refuses on open comments — open comments are what *drive* new
    versions (US4 S2). The convergence value is a signal, not a block.

    Returns::

        {version: dict, convergence: "converged"|"unconverged",
         open_comments: list[dict], displaced_comment_ids: list[int]}
    """
    # Local import keeps the dependency one-directional and lazy (no module-load cycle):
    # comment_service imports this module only inside its own functions.
    from cast_server.services import comment_service

    version = create_snapshot(goal_slug, content, created_by, db_path=db_path)
    open_comments = comment_service.list_comments(
        goal_slug, state="open", current_text=content, db_path=db_path
    )
    convergence = (
        "unconverged"
        if comment_service.open_comment_count(goal_slug, db_path=db_path) > 0
        else "converged"
    )
    displaced_comment_ids = [
        c["id"] for c in open_comments if c["quoted_text"] not in content
    ]
    return {
        "version": version,
        "convergence": convergence,
        "open_comments": open_comments,
        "displaced_comment_ids": displaced_comment_ids,
    }


# Event-type → resulting comment state. ``relocated`` is a re-anchor only — it never changes
# state, so it is absent here (a missing key means "no state transition").
_EVENT_STATE = {
    "created": "open",
    "resolved": "resolved",
    "reopened": "open",
    "orphaned": "orphaned",
}


def _state_as_of(events: list[dict], cutoff: str | None) -> str | None:
    """Replay an append-only ``comment_events`` trail to the comment's state at ``cutoff``.

    Pure + re-derivable (US5 S3 is a query over the trail, never a stored feature). ``events``
    are applied in ``created_at`` order; any event at or before ``cutoff`` counts (``cutoff``
    is the supersession instant — the next version's ``created_at``, or ``None`` for "now",
    which includes every event). Returns the as-of state, or ``None`` if no event had yet
    occurred by ``cutoff`` (the comment did not exist as of that version).
    """
    state: str | None = None
    for e in sorted(events, key=lambda ev: ev["created_at"]):
        if cutoff is not None and e["created_at"] > cutoff:
            break
        state = _EVENT_STATE.get(e["event_type"], state)  # relocated → unchanged
    return state


def get_version_with_comments(goal_slug: str, version: int,
                              *, db_path: Path | None = None) -> dict | None:
    """Return a version row joined with its comments at their **as-of** resolution state (US5 S3).

    The archive-retrieval surface behind ``GET /versions/{n}``. Returns ``None`` if the version
    does not exist (route → 404). Each comment with ``version <= n`` is reconstructed to the
    state it held **as of this version's supersession time** — the next version's ``created_at``,
    or "now" (``cutoff=None``) for the current version — by replaying its ``comment_events``
    trail (:func:`_state_as_of`). Comments that did not yet exist as of that instant are omitted.

    FR-011 stays structural: versions are rows; this never reads or writes a second
    requirements file in the goal folder.
    """
    from cast_server.services import comment_service

    row = get_version(goal_slug, version, db_path=db_path)
    if row is None:
        return None

    # Supersession instant: the created_at of the next-numbered version, else "now" (None).
    nxt = get_version(goal_slug, version + 1, db_path=db_path)
    cutoff = nxt["created_at"] if nxt else None

    comments_as_of: list[dict] = []
    for c in comment_service.list_comments(goal_slug, db_path=db_path):
        if c["version"] > version:
            continue
        state = _state_as_of(
            comment_service.get_comment_events(c["id"], db_path=db_path), cutoff
        )
        if state is None:
            continue  # comment had not been created yet as of this version
        comments_as_of.append({**c, "state_as_of": state})

    comments_as_of.sort(key=lambda c: c["id"])
    return {"version": row, "comments": comments_as_of}


def get_current(goal_slug: str, *, db_path: Path | None = None) -> dict | None:
    """Return the ``status='current'`` version row-dict for the goal, or ``None``."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM requirement_versions WHERE goal_slug = ? AND status = 'current'",
            (goal_slug,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_version(goal_slug: str, version: int, *, db_path: Path | None = None) -> dict | None:
    """Return the row-dict for ``(goal_slug, version)``, or ``None`` if absent."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM requirement_versions WHERE goal_slug = ? AND version = ?",
            (goal_slug, version),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_versions(goal_slug: str, *, db_path: Path | None = None) -> list[dict]:
    """Return all version row-dicts for the goal, ordered by ``version`` ascending.

    Ascending order matches ``task_service``'s ``ORDER BY sort_order`` list idiom (oldest
    first); kept consistent so Phase 4's comment_service list functions read the same way.
    """
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM requirement_versions WHERE goal_slug = ? ORDER BY version",
            (goal_slug,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Same-door version-diff narration (Phase 4b-3)                                #
# --------------------------------------------------------------------------- #

def _deterministic_keys(base_content: str, head_content: str) -> set[tuple[str, str]]:
    """Recompute ``summarize(diff_blocks(old, new))`` and return its valid narration keys.

    The key set is ``{(item["change"], item["heading_or_ref"]) for item in items}`` — the EXACT
    surface a narration note may attach to. Computed server-side from the loaded snapshots, never
    trusting the poster (the structural diff is the source of truth; the agent only decorates).
    """
    old = parse_requirements(base_content)
    new = parse_requirements(head_content)
    items = summarize(diff_blocks(old, new))["items"]
    return {(it["change"], it["heading_or_ref"]) for it in items}


def save_narration(goal_slug: str, base: int, head: int, overview: str,
                   item_notes: list[dict], created_by: str | None,
                   *, db_path: Path | None = None) -> dict:
    """Store one narration per ``(goal_slug, base, head)``, structurally validated.

    Loads both version rows (``NarrationVersionNotFound`` → 404 if either is absent), recomputes
    ``summarize(diff_blocks(old, new))`` server-side, and validates EVERY ``item_note``'s
    ``(change, heading_or_ref)`` against that deterministic key set. ANY mismatch raises
    ``NarrationValidationError`` listing the offending keys — **all-or-nothing**, never a silent
    note-drop. Size caps (FR-017): ``overview`` ≤ 2 KB, each note ≤ 2 KB, ≤ 1 note per item.

    Upsert on ``(goal_slug, base, head)``: a retried loop cycle REPLACES the prior row, never
    duplicating it. Returns the stored narration dict (the :func:`get_narration` shape).
    """
    base_row = get_version(goal_slug, base, db_path=db_path)
    head_row = get_version(goal_slug, head, db_path=db_path)
    if base_row is None or head_row is None:
        raise NarrationVersionNotFound(
            f"version not found for {goal_slug}: base={base} head={head}"
        )

    # Collect EVERY problem first (all-or-nothing — no silent dropping, no partial save).
    size_errors: list[str] = []
    if len(overview.encode("utf-8")) > _NARRATION_FIELD_MAX_BYTES:
        size_errors.append(f"overview exceeds {_NARRATION_FIELD_MAX_BYTES} bytes")

    try:
        valid_keys = _deterministic_keys(base_row["content"], head_row["content"])
    except Exception:  # noqa: BLE001 — a pre-parser snapshot cannot be diffed; never 500
        raise NarrationValidationError(
            "cannot validate narration: one snapshot predates the structured parser"
        )

    offending_keys: list[list[str]] = []
    seen: set[tuple[str, str]] = set()
    duplicate_keys: list[list[str]] = []
    for note in item_notes:
        change = note.get("change")
        heading_or_ref = note.get("heading_or_ref")
        text = note.get("note", "")
        key = (change, heading_or_ref)
        if len(str(text).encode("utf-8")) > _NARRATION_FIELD_MAX_BYTES:
            size_errors.append(
                f"note for {list(key)} exceeds {_NARRATION_FIELD_MAX_BYTES} bytes"
            )
        if key not in valid_keys:
            offending_keys.append([change, heading_or_ref])
        elif key in seen:
            duplicate_keys.append([change, heading_or_ref])
        seen.add(key)

    if offending_keys or duplicate_keys or size_errors:
        parts: list[str] = []
        if offending_keys:
            parts.append(
                "item_notes reference changes absent from the deterministic set: "
                f"{offending_keys}"
            )
        if duplicate_keys:
            parts.append(f"more than one note for the same item: {duplicate_keys}")
        if size_errors:
            parts.append("; ".join(size_errors))
        raise NarrationValidationError("; ".join(parts), offending_keys=offending_keys)

    now = datetime.now(timezone.utc).isoformat()
    notes_json = json.dumps(item_notes)
    conn = get_connection(db_path)
    try:
        existing = conn.execute(
            "SELECT id FROM version_diff_narrations "
            "WHERE goal_slug = ? AND base_version = ? AND head_version = ?",
            (goal_slug, base, head),
        ).fetchone()
        if existing is not None:
            conn.execute(
                "UPDATE version_diff_narrations "
                "SET overview = ?, item_notes = ?, created_by = ?, created_at = ? WHERE id = ?",
                (overview, notes_json, created_by, now, existing["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO version_diff_narrations "
                "(goal_slug, base_version, head_version, overview, item_notes, created_by, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (goal_slug, base, head, overview, notes_json, created_by, now),
            )
        conn.commit()
    finally:
        conn.close()
    return get_narration(goal_slug, base, head, db_path=db_path)


def get_narration(goal_slug: str, base: int, head: int,
                  *, db_path: Path | None = None) -> dict | None:
    """Return the stored narration for ``(goal_slug, base, head)``, or ``None``.

    Shape mirrors the ``cast-comment-reanchor`` narration output plus provenance::

        {overview, item_notes: [{change, heading_or_ref, note}],
         base_version, head_version, created_by, created_at}
    """
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM version_diff_narrations "
            "WHERE goal_slug = ? AND base_version = ? AND head_version = ?",
            (goal_slug, base, head),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return {
        "overview": row["overview"],
        "item_notes": json.loads(row["item_notes"]),
        "base_version": row["base_version"],
        "head_version": row["head_version"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
    }
