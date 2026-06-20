"""Comment persistence + event trail for the requirements thin spine (Phase 4, WP-A).

The comment layer is the *only* deterministic machinery here — every state transition
writes its ``comment_events`` row in the SAME transaction (decisions #1/#9: where being
wrong means silent data loss). Nothing positional is ever stored: a comment anchors to its
verbatim ``quoted_text``, and "displacement" (the quote no longer appearing in the current
file) is a **derived, read-time** property recomputed on every ``list_comments`` — a
*detector* that the agent loop acts on, NOT an anchoring engine.

House DB pattern: flat module-level functions + injectable ``db_path`` +
``get_connection(db_path)`` in try/finally, ``dict(row)`` conversion — modeled on
``goal_service.py`` / ``requirement_version_service.py`` (NOT ``orchestration_service.py``).

FR-013: ``author_kind`` ('human' | 'agent') is the ONLY human/agent distinction — there is
no separate code path. The same ``create_comment`` runs whether the request came from a
human composer or an agent ``curl``.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from cast_server.config import GOALS_DIR
from cast_server.db.connection import get_connection
from cast_server.requirements_render import comment_anchor


class CommentNotFound(Exception):
    """No comment row for the given id (route maps to 404)."""


class CommentStateError(Exception):
    """A state-machine violation, e.g. resolving an already-resolved comment (route → 409).

    State-machine violations announce themselves; they are never a silent no-op.
    """


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _current_version(goal_slug: str, db_path: Path | None) -> int:
    """The version a new comment is left against — the current snapshot, or 0 if none yet."""
    # Local import avoids a module-level import cycle (version service imports nothing here,
    # but keep the dependency direction one-way and lazy to stay symmetric with the render svc).
    from cast_server.services import requirement_version_service

    current = requirement_version_service.get_current(goal_slug, db_path=db_path)
    return current["version"] if current else 0


def _resolve_current_text(goal_slug: str, db_path: Path | None, goals_dir: Path | None) -> str:
    """Read the goal's current ``refined_requirements.collab.md``, or ``""`` if missing.

    A missing file is NOT an error: every open comment then reads as ``displaced=True``
    (the file vanished out from under them) — we never crash on a read-time detector.
    """
    from cast_server.services import requirements_render_service

    goals_dir = goals_dir or GOALS_DIR
    goal_dir = requirements_render_service._resolve_goal_dir(goal_slug, goals_dir, db_path)
    source = goal_dir / "refined_requirements.collab.md"
    if not source.exists():
        return ""
    return source.read_text(encoding="utf-8")


def _resolve_artifact_path(goal_dir: Path, artifact_ref: str | None) -> Path:
    """Resolve ``artifact_ref`` to a validated, goal-relative ``.html`` path under ``goal_dir``.

    ``artifact_ref=None`` → ``refined_requirements.html`` (the back-compatible default: every
    requirements comment + existing render-space comment keeps resolving byte-for-byte as before).
    A non-empty value is a goal-relative path (e.g. ``exploration/exploration.html``) the bridge
    POST carried; the server is the trust boundary, so this re-validates path shape even though the
    same-door route already validated it: it must stay UNDER ``goal_dir`` (no ``..``/absolute escape)
    and be ``.html``. A violation raises ``ValueError`` — never silently reads the wrong file.

    This is the load-bearing seam of sp3b: it makes the served-render resolver artifact-keyed instead
    of requirements-hardwired, so commenting is Diecast-wide (Phase 4's ``exploration.html`` inherits
    it for free) without any artifact-specific server code.
    """
    if not artifact_ref:
        return goal_dir / "refined_requirements.html"
    ref = str(artifact_ref).strip()
    if not ref.endswith(".html"):
        raise ValueError(f"artifact_ref must be a .html path: {artifact_ref!r}")
    base = goal_dir.resolve()
    candidate = (base / ref).resolve()
    if not candidate.is_relative_to(base):
        raise ValueError(f"artifact_ref escapes the goal directory: {artifact_ref!r}")
    return candidate


def _resolve_served_render_html(goal_slug: str, db_path: Path | None, goals_dir: Path | None,
                                artifact_ref: str | None = None) -> str:
    """Read the goal's SERVED render artifact, or ``""`` if missing.

    ``artifact_ref=None`` → ``refined_requirements.html`` (the back-compatible default); a value →
    the validated goal-relative ``.html`` it names (sp3b: artifact-keyed, so a comment minted against
    ``exploration/exploration.html`` anchors against THAT document, not the requirements render).

    The served `.html` is the text space comments now anchor to (refine-req-v3 sp2 — the crux move:
    a comment's quote is minted from / validated against the published render, not the canonical
    `.collab.md`). A missing render is NOT an error — the read-time detector degrades to the source
    check rather than crashing (see ``_resolve_render_compare_text``). A path-shape violation in
    ``artifact_ref`` is the one hard error (a spoofed traversal must never read off-tree).
    """
    from cast_server.services import requirements_render_service

    goals_dir = goals_dir or GOALS_DIR
    goal_dir = requirements_render_service._resolve_goal_dir(goal_slug, goals_dir, db_path)
    served = _resolve_artifact_path(goal_dir, artifact_ref)
    if not served.exists():
        return ""
    return served.read_text(encoding="utf-8")


def _resolve_render_compare_text(goal_slug: str, db_path: Path | None, goals_dir: Path | None,
                                 artifact_ref: str | None = None) -> str:
    """The displacement-comparison text for a ``'render'``-space comment.

    The served render's container text — extracted via the SHARED ``container_text_index`` walker
    (the same text space ``create_comment``'s resolver and ``maker_gate`` place against — never a
    second tokenizer). ``artifact_ref`` selects WHICH served ``.html`` (sp3b: the comment displaces
    against the artifact it was minted from, never a different document). **No render artifact on
    disk → fall back to the SOURCE check** (Step 2.4: a missing render must never crash the read-time
    detector — degrade, never error).
    """
    from cast_server.requirements_render.maker_gate import container_text_index

    html = _resolve_served_render_html(goal_slug, db_path, goals_dir, artifact_ref)
    if not html:
        return _resolve_current_text(goal_slug, db_path, goals_dir)
    return container_text_index(html).document_text


def _append_event(conn, comment_id: int, event_type: str, actor: str | None,
                  payload: dict | None, now: str) -> None:
    """Append one ``comment_events`` row on the SAME open connection (no commit here)."""
    conn.execute(
        """INSERT INTO comment_events (comment_id, event_type, actor, payload, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (comment_id, event_type, actor, json.dumps(payload) if payload is not None else None, now),
    )


def _get_row(conn, comment_id: int) -> dict:
    row = conn.execute(
        "SELECT * FROM requirement_comments WHERE id = ?", (comment_id,)
    ).fetchone()
    if row is None:
        raise CommentNotFound(f"comment {comment_id} not found")
    return dict(row)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def create_comment(goal_slug: str, quoted_text: str, section_hint: str | None, body: str,
                   author: str, author_kind: str = "human",
                   *, version: int | None = None, db_path: Path | None = None,
                   goals_dir: Path | None = None,
                   artifact_ref: str | None = None,
                   served_render_html: str | None = None) -> dict:
    """Insert an ``open`` comment + its ``created`` event in ONE transaction; return the row.

    ``version`` defaults to the current snapshot's version (0 if no version exists yet).
    ``author_kind`` defaults to ``'human'`` — the ONLY human/agent distinction (FR-013).

    Render-space anchoring (refine-req-v3 sp2): the comment lives in ``anchor_space='render'`` and
    its ``block_ref`` (the canonical id of the enclosing labeled unit container) is resolved
    SERVER-SIDE from the served render — never accepted from the caller (trust boundary: a spoofed
    ``block_ref`` would mis-route a future change-request). A ``block_ref`` of ``None`` is stored and
    treated as SUCCESS when the render is ref-less (zero anchor labels) or the quote is
    cross-boundary — it is never an unplaced miss to retry/badge (plan-review Decision #1).

    ``artifact_ref`` (sp3b) is the goal-relative ``.html`` the quote was minted against; ``None`` →
    ``refined_requirements.html`` (the requirements default — byte-identical legacy behavior). It is
    stored on the row so future displacement/relocate resolve against the SAME artifact, never a
    different document. Like ``block_ref``, the *resolution* is server-side; the route is the trust
    boundary that validated the path shape before it reached here.
    ``served_render_html`` is a test seam; in production the served `.html` is read off disk.
    """
    if version is None:
        version = _current_version(goal_slug, db_path)

    from cast_server.services import requirements_render_service

    # Resolve the render-space anchor SERVER-SIDE from the served artifact (the crux move). The
    # served render is the text the UI minted this quote against, so the quote places by
    # construction in real use; block_ref bridges it back to source space (NULL = honest).
    # artifact_ref selects WHICH served .html — None keeps the requirements default.
    if served_render_html is None:
        served_render_html = _resolve_served_render_html(goal_slug, db_path, goals_dir, artifact_ref)
    anchor = comment_anchor.resolve_render_anchor(served_render_html, quoted_text)
    source_hash = (
        requirements_render_service._embedded_source_hash(served_render_html)
        if served_render_html else None
    )

    now = _now()
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            """INSERT INTO requirement_comments
               (goal_slug, version, quoted_text, section_hint, body, state,
                author, author_kind, block_ref, anchor_space, artifact_ref, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 'open', ?, ?, ?, 'render', ?, ?, ?)""",
            (goal_slug, version, quoted_text, section_hint, body,
             author, author_kind, anchor.block_ref, artifact_ref, now, now),
        )
        comment_id = cur.lastrowid
        # The served artifact's embedded source-hash rides the created event for forensics (no new
        # column) — it pins exactly which render this anchor was resolved against.
        _append_event(conn, comment_id, "created", author,
                      {"anchor_space": "render", "block_ref": anchor.block_ref,
                       "artifact_ref": artifact_ref,
                       "source_hash": source_hash, "miss_class": anchor.miss_class}, now)
        conn.commit()
        return _get_row(conn, comment_id)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def list_comments(goal_slug: str, *, state: str | None = None,
                  db_path: Path | None = None,
                  current_text: str | None = None,
                  render_text: str | None = None,
                  goals_dir: Path | None = None) -> list[dict]:
    """Return comment row-dicts for the goal, newest first; stamp open comments ``displaced``.

    ``displaced: bool`` = ``quoted_text not in <comparison text>`` is computed ONLY for **open**
    comments (orphaned/resolved are never displacement-checked — ``displaced`` is absent on them).
    The comparison text is chosen per the comment's ``anchor_space`` (refine-req-v3 sp2):

    - ``'render'`` → the SERVED render's container text (the published artifact the quote was minted
      against), supplied via the ``render_text`` test seam else looked up + extracted with the shared
      ``container_text_index`` walker; a missing render degrades to the source check, never a crash.
    - ``'source'`` → the canonical ``refined_requirements.collab.md`` (legacy / not-yet-migrated
      comments), supplied via the ``current_text`` test seam else looked up (``""`` when missing).

    A ref-less-render NULL ``block_ref`` is NEVER special-cased here: displacement is purely "is the
    quote present in the served render text", independent of ``block_ref`` — a placed ref-less
    comment reads ``displaced=False`` like any other (Decision #1).

    The string-find is a detector, not an anchoring engine (decision #1) — nothing positional is
    stored; ``displaced`` is recomputed on every call.
    """
    conn = get_connection(db_path)
    try:
        if state is not None:
            rows = conn.execute(
                """SELECT * FROM requirement_comments
                   WHERE goal_slug = ? AND state = ? ORDER BY id DESC""",
                (goal_slug, state),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM requirement_comments WHERE goal_slug = ? ORDER BY id DESC",
                (goal_slug,),
            ).fetchall()
    finally:
        conn.close()

    comments = [dict(r) for r in rows]
    if not any(c["state"] == "open" for c in comments):
        return comments  # nothing to displacement-check → skip the file read entirely

    # Resolve each comparison space lazily and at most once PER ARTIFACT (a goal may now carry
    # render-space comments minted against several served .html artifacts — sp3b — so the render
    # compare-text is cached keyed by artifact_ref, not as a single string). The ``render_text`` seam
    # still pins the requirements-default render (artifact_ref None) for tests that supply it.
    _source = current_text
    _render_cache: dict[str | None, str] = {}
    if render_text is not None:
        _render_cache[None] = render_text

    def _compare_for(space: str, artifact_ref: str | None) -> str:
        nonlocal _source
        if space == "render":
            if artifact_ref not in _render_cache:
                _render_cache[artifact_ref] = _resolve_render_compare_text(
                    goal_slug, db_path, goals_dir, artifact_ref
                )
            return _render_cache[artifact_ref]
        if _source is None:
            _source = _resolve_current_text(goal_slug, db_path, goals_dir)
        return _source

    for c in comments:
        if c["state"] == "open":
            space = c["anchor_space"] if c["anchor_space"] in ("render", "source") else "source"
            c["displaced"] = c["quoted_text"] not in _compare_for(space, c.get("artifact_ref"))
    return comments


def get_comment(comment_id: int, *, db_path: Path | None = None) -> dict:
    """Return the comment row-dict, or raise ``CommentNotFound`` (route → 404)."""
    conn = get_connection(db_path)
    try:
        return _get_row(conn, comment_id)
    finally:
        conn.close()


def get_comment_events(comment_id: int, *, db_path: Path | None = None) -> list[dict]:
    """Return the append-only event trail for a comment, oldest first."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM comment_events WHERE comment_id = ? ORDER BY id",
            (comment_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def open_comment_count(goal_slug: str, *, db_path: Path | None = None) -> int:
    """Count of ``open`` comments — the sole input to the convergence rule (>0 ⇒ unconverged)."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM requirement_comments WHERE goal_slug = ? AND state = 'open'",
            (goal_slug,),
        ).fetchone()
        return row["n"]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# State transitions — each appends its event in the SAME transaction
# ---------------------------------------------------------------------------

def resolve_comment(comment_id: int, actor: str | None, *, db_path: Path | None = None) -> dict:
    """Mark a comment ``resolved`` + append a ``resolved`` event. 409 if already resolved."""
    now = _now()
    conn = get_connection(db_path)
    try:
        row = _get_row(conn, comment_id)
        if row["state"] == "resolved":
            raise CommentStateError(f"comment {comment_id} is already resolved")
        conn.execute(
            "UPDATE requirement_comments SET state = 'resolved', updated_at = ? WHERE id = ?",
            (now, comment_id),
        )
        _append_event(conn, comment_id, "resolved", actor, None, now)
        conn.commit()
        return _get_row(conn, comment_id)
    finally:
        conn.close()


def reopen_comment(comment_id: int, actor: str | None, *, db_path: Path | None = None) -> dict:
    """Reopen a comment (→ ``open``) + append a ``reopened`` event. 409 if already open."""
    now = _now()
    conn = get_connection(db_path)
    try:
        row = _get_row(conn, comment_id)
        if row["state"] == "open":
            raise CommentStateError(f"comment {comment_id} is already open")
        conn.execute(
            "UPDATE requirement_comments SET state = 'open', updated_at = ? WHERE id = ?",
            (now, comment_id),
        )
        _append_event(conn, comment_id, "reopened", actor, None, now)
        conn.commit()
        return _get_row(conn, comment_id)
    finally:
        conn.close()


def relocate_comment(comment_id: int, new_quoted_text: str, new_section_hint: str | None,
                     actor: str | None, *, db_path: Path | None = None) -> dict:
    """Re-anchor a comment to a new verbatim quote + append a ``relocated`` event.

    The event ``payload`` stores the OLD quote (``{"old_quoted_text": ...}``) so the trail
    preserves where the comment used to live. Substring validation against the current file
    is the ROUTE's job (Step 1.3 / sp4b backstop), not the service's.
    """
    now = _now()
    conn = get_connection(db_path)
    try:
        row = _get_row(conn, comment_id)
        old_quoted_text = row["quoted_text"]
        conn.execute(
            """UPDATE requirement_comments
               SET quoted_text = ?, section_hint = ?, updated_at = ? WHERE id = ?""",
            (new_quoted_text, new_section_hint, now, comment_id),
        )
        _append_event(conn, comment_id, "relocated", actor,
                      {"old_quoted_text": old_quoted_text}, now)
        conn.commit()
        return _get_row(conn, comment_id)
    finally:
        conn.close()


def orphan_comment(comment_id: int, actor: str | None, *, db_path: Path | None = None) -> dict:
    """Mark a comment ``orphaned`` + append an ``orphaned`` event (decision #9: always surfaced)."""
    now = _now()
    conn = get_connection(db_path)
    try:
        _get_row(conn, comment_id)  # raise CommentNotFound on unknown id
        conn.execute(
            "UPDATE requirement_comments SET state = 'orphaned', updated_at = ? WHERE id = ?",
            (now, comment_id),
        )
        _append_event(conn, comment_id, "orphaned", actor, None, now)
        conn.commit()
        return _get_row(conn, comment_id)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# One-time render-space migration (refine-req-v3 sp2, Step 2.7)
# ---------------------------------------------------------------------------

def migrate_comments_to_render_space(
    goal_slug: str, *, actor: str = "render-anchor-migration",
    db_path: Path | None = None, goals_dir: Path | None = None,
    served_render_html: str | None = None,
) -> dict:
    """Productionize 1b's render-anchor dry-run: flip placeable open comments to render space.

    For every OPEN ``'source'``-space comment of the goal, attempt render-space placement +
    ``block_ref`` resolution against the served render (the SAME resolver ``create_comment`` uses):

    - **places** → flip ``anchor_space='render'`` and backfill ``block_ref`` (``NULL`` allowed and
      honest for a ref-less render — Decision #1), recording an ``anchor_migrated`` disposition event.
    - **doesn't place** → leave it in ``'source'`` space, surfaced by the existing
      ``.comment-unplaced`` tray badge. NEVER resolve / orphan / delete (surface, don't suppress).

    **Idempotent.** Only ``'source'``-space comments are examined, and an event is written ONLY on an
    actual source→render flip — so a second run touches nothing already in render space, re-resolves
    the non-placing remainder identically, and writes no duplicate ``comment_events``.

    Returns a disposition summary ``{examined, flipped, ref_less_null, stayed_source}``.
    """
    if served_render_html is None:
        served_render_html = _resolve_served_render_html(goal_slug, db_path, goals_dir)

    now = _now()
    summary = {"examined": 0, "flipped": 0, "ref_less_null": 0, "stayed_source": 0}
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM requirement_comments "
            "WHERE goal_slug = ? AND state = 'open' AND anchor_space = 'source' ORDER BY id",
            (goal_slug,),
        ).fetchall()
        source_hash = (
            _embedded_source_hash(served_render_html) if served_render_html else None
        )
        for row in rows:
            summary["examined"] += 1
            anchor = comment_anchor.resolve_render_anchor(served_render_html, row["quoted_text"])
            if not anchor.placed:
                # Stays source-space; the existing badge surfaces it. No state change → no event,
                # so a re-run never accumulates a duplicate disposition row.
                summary["stayed_source"] += 1
                continue
            conn.execute(
                "UPDATE requirement_comments "
                "SET anchor_space = 'render', block_ref = ?, updated_at = ? WHERE id = ?",
                (anchor.block_ref, now, row["id"]),
            )
            _append_event(
                conn, row["id"], "anchor_migrated", actor,
                {"from": "source", "to": "render", "block_ref": anchor.block_ref,
                 "miss_class": anchor.miss_class, "source_hash": source_hash}, now,
            )
            summary["flipped"] += 1
            if anchor.block_ref is None:
                summary["ref_less_null"] += 1
        conn.commit()
    finally:
        conn.close()
    return summary


def _embedded_source_hash(served_render_html: str) -> str | None:
    """Thin lazy bridge to the render service's embedded source-hash reader (forensics only)."""
    from cast_server.services import requirements_render_service

    return requirements_render_service._embedded_source_hash(served_render_html)
