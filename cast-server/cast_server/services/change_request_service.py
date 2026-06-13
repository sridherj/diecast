"""Change-request intake for the round-trip write-back spine (refine-requirements-v2 Phase 5, sp2).

The DB-owned *receiving* half of "propose + notify + gate, never auto-sync". A downstream
phase (or a human "suggest edit") does NOT touch the canonical ``.collab.md``; it POSTs a
first-class ``change_request`` carrying *where it came from* (``origin_*``) and *what version
it assumed* (``base_version``). This module records that proposal — the row, its append-only
``change_request_events`` trail, and (on the auto-apply lane) a ``notifications_outbox`` row —
in ONE transaction. **Nothing here writes a file** (sp4's sole-writer agent applies accepted
changes) and **nothing here computes the conflict verdict** (sp3a's ``detect_conflict``); intake
*records* the verdict it is handed (intake-records-the-verdict).

House DB pattern: flat module-level functions + injectable ``db_path`` +
``get_connection(db_path)``, ``dict(row)`` conversion — modeled on ``comment_service`` /
``requirement_version_service`` (NOT ``orchestration_service``). The multi-statement write is
wrapped in a single ``BEGIN IMMEDIATE`` (the version-service precedent) so a mid-write crash
leaves **nothing** orphaned — no event without its request, no outbox row without its apply.

FR-013: ``author_type`` ('human' | 'agent') is DATA, never a code branch. There is exactly ONE
intake path; the human/agent distinction is a column value the route resolves, not a fork.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from cast_server.config import GOALS_DIR, WRITEBACK_GATE_POLICY
from cast_server.db.connection import get_connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------- #
# Graduated-trust router (branch by blast radius, NOT by author)               #
# --------------------------------------------------------------------------- #

def gate_status(kind: str, target_quote: str | None,
                policy: str = WRITEBACK_GATE_POLICY) -> str:
    """Decide a proposal's intake ``status`` from blast radius, gated by ``policy``.

    Blast radius — NOT author — drives the lane (FR-013: trust is data, the same for a human
    and an agent). A **pure addition** (``kind == "addition"``, no ``target_quote`` → no
    existing region touched) is the low-blast-radius case; everything that *modifies existing
    content* is gated.

    * ``"gate-except-additions"`` (v2 default) → additions ``"applied"`` (fast-track),
      modifications/annotations ``"proposed"`` (await the human gate).
    * ``"gate-none"``  → everything ``"applied"``.
    * ``"gate-all"``   → everything ``"proposed"``.

    The ``conflicted`` lane is NOT decided here — sp3a's ``detect_conflict`` computes divergence
    from ``base_version`` and the route feeds that verdict in via ``create(status=...)``. This
    function only chooses between the trust lanes for a non-conflicted proposal.
    """
    is_addition = kind == "addition" and target_quote is None
    if policy == "gate-none":
        return "applied"
    if policy == "gate-all":
        return "proposed"
    # Default + any unrecognized value falls back to the conservative v2 posture.
    return "applied" if is_addition else "proposed"


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #

def _append_event(conn, change_request_id: int, event_type: str, actor: str | None,
                  payload: dict | None, now: str) -> None:
    """Append one ``change_request_events`` row on the SAME open connection (no commit here)."""
    conn.execute(
        """INSERT INTO change_request_events
           (change_request_id, event_type, actor, payload, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (change_request_id, event_type, actor,
         json.dumps(payload) if payload is not None else None, now),
    )


def _notification_payload(row: dict) -> dict:
    """The outbox payload — *what changed + from where* (schema's stated contract).

    Queued ONLY on the auto-apply lane this sub-phase (sp3b builds the relay loop that
    delivers it). Denormalized so a consumer needs no extra read to render the FYI.
    """
    return {
        "change_request_id": row["id"],
        "goal_slug": row["goal_slug"],
        "kind": row["kind"],
        "status": row["status"],
        "base_version": row["base_version"],
        "target_quote": row["target_quote"],
        "section_hint": row["section_hint"],
        "origin_phase": row["origin_phase"],
        "origin_artifact_path": row["origin_artifact_path"],
        "author": row["author"],
        "author_type": row["author_type"],
    }


def _get(conn, change_request_id: int) -> dict:
    row = conn.execute(
        "SELECT * FROM change_requests WHERE id = ?", (change_request_id,)
    ).fetchone()
    return dict(row)


# --------------------------------------------------------------------------- #
# Create — the atomic intake write                                             #
# --------------------------------------------------------------------------- #

def create(goal_slug: str, *, kind: str, proposed_body: str, base_version: int,
           target_quote: str | None = None, section_hint: str | None = None,
           author: str, author_type: str,
           origin_phase: str | None = None, origin_activity_id: str | None = None,
           origin_artifact_path: str | None = None,
           status: str = "proposed", db_path: Path | None = None) -> dict:
    """Record a change-request + its ``proposed`` event (+ outbox row on the apply lane), atomically.

    One ``BEGIN IMMEDIATE`` transaction wraps every write so a mid-write crash leaves NOTHING
    orphaned (all-or-nothing). ``status`` is the verdict the caller hands in (the route derives
    it from :func:`gate_status`, or — once sp3a is wired — passes ``"conflicted"``); intake does
    not recompute it. The ``notifications_outbox`` row is queued **only** when ``status ==
    "applied"`` (the FYI for an auto-applied addition); gated/conflicted proposals queue nothing.

    Returns the persisted row-dict.
    """
    now = _now()
    conn = get_connection(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.execute(
            """INSERT INTO change_requests
               (goal_slug, target_quote, section_hint, base_version, proposed_body, kind,
                status, origin_phase, origin_activity_id, origin_artifact_path,
                author, author_type, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (goal_slug, target_quote, section_hint, base_version, proposed_body, kind,
             status, origin_phase, origin_activity_id, origin_artifact_path,
             author, author_type, now, now),
        )
        cr_id = cur.lastrowid
        _append_event(conn, cr_id, "proposed", author, None, now)
        if status == "applied":
            row = _get(conn, cr_id)
            conn.execute(
                """INSERT INTO notifications_outbox
                   (change_request_id, payload, status, created_at)
                   VALUES (?, ?, 'pending', ?)""",
                (cr_id, json.dumps(_notification_payload(row)), now),
            )
        conn.commit()
        return _get(conn, cr_id)
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Read                                                                          #
# --------------------------------------------------------------------------- #

def get(change_request_id: int, *, db_path: Path | None = None) -> dict | None:
    """Return the change-request row-dict, or ``None`` if absent."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM change_requests WHERE id = ?", (change_request_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_events(change_request_id: int, *, db_path: Path | None = None) -> list[dict]:
    """Return the append-only event trail for a change-request, oldest first."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM change_request_events WHERE change_request_id = ? ORDER BY id",
            (change_request_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def list_outbox(change_request_id: int, *, db_path: Path | None = None) -> list[dict]:
    """Return ``notifications_outbox`` rows for a change-request, oldest first."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM notifications_outbox WHERE change_request_id = ? ORDER BY id",
            (change_request_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# =========================================================================== #
# Apply — the SOLE file-writer carve-out (sp4)                                 #
# =========================================================================== #
#
# This is the ONLY code path in the whole server that mutates a goal's canonical
# ``refined_requirements.collab.md``. It mirrors ``cast-update-spec``'s "sole write path"
# posture: the server owns the proposal DB (intake/conflict/notify above); THIS function
# owns the file apply. It is the explicit ``cast-delegation-contract`` carve-out (the server
# never writes artifact files — except here, the human-gated round-trip apply).
#
# The silent-drift bug US7 exists to kill is made *structurally* impossible: there is no
# whole-file overwrite path. We read the current file, splice exactly the located region (a
# tail addition or a clean modification), VERIFY every non-target byte is identical, and only
# then commit. ``api_artifacts.save_artifact`` / a blind ``write_text`` of an external buffer
# is never used (deliberately not even imported).

# The same injected-locator shape sp3a's ``detect_conflict`` uses: given the document text, the
# target quote, and a section hint, return the located region's text or ``None``.
Locator = Callable[[str, Optional[str], Optional[str]], Optional[str]]

_REQUIREMENTS_FILENAME = "refined_requirements.collab.md"


class WritebackRefused(Exception):
    """The apply was refused; the ``.collab.md`` is left **byte-identical** (never overwritten).

    Raised for the three non-apply outcomes — a conflicted region, an orphaned target, or an
    out-of-tree path. Carries the structured ``surface`` so the caller can present the 3-way
    conflict choice (sp3a's ``ConflictSurface``) without re-deriving it. A refusal is never a
    silent no-op: it always announces itself (this exception) and, for conflict/orphan, leaves a
    ``change_request_events`` row.
    """

    def __init__(self, verdict: str, reason: str, *, surface: dict | None = None) -> None:
        super().__init__(f"{verdict}: {reason}")
        self.verdict = verdict
        self.reason = reason
        self.surface = surface


def verbatim_locate(content: str, target_quote: Optional[str],
                    section_hint: Optional[str] = None) -> Optional[str]:
    """Production quote→region locator: the **enclosing line(s)** of the verbatim ``target_quote``.

    Returns ``None`` when the quote is not a verbatim substring of ``content`` (→ ``orphaned``;
    the writeback agent then dispatches ``cast-comment-reanchor`` to relocate, never guesses
    here). The region is the line span the quote sits on — larger than the bare quote — so a
    reworded-but-still-anchored region reads as ``conflicted`` rather than a false ``clean``
    (sp3a's "region = enclosing line" discipline). Pure: no DB, no LLM, no I/O.
    """
    if target_quote is None:
        return None
    idx = content.find(target_quote)
    if idx < 0:
        return None
    start = content.rfind("\n", 0, idx) + 1            # start of the line holding the quote
    nl = content.find("\n", idx + len(target_quote))   # end of the line holding the quote's tail
    end = nl if nl != -1 else len(content)
    return content[start:end]


def _is_within(path: Path, root: Path) -> bool:
    """True iff ``path`` is ``root`` or lives beneath it (both already ``resolve()``-d)."""
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _insert_in_section(content: str, section_hint: str, body: str) -> str | None:
    """Insert ``body`` as a new line after the last non-blank line of the named ``## section``.

    Returns the spliced content, or ``None`` if no ``## section_hint`` heading exists (caller
    falls back to a tail append). Byte-faithful: the insertion is a pure character splice — every
    original byte survives, in order; the only new bytes are ``body`` + one newline.
    """
    lines = content.split("\n")
    head_idx = None
    for i, ln in enumerate(lines):
        if ln.startswith("## ") and ln[3:].strip() == section_hint:
            head_idx = i
            break
    if head_idx is None:
        return None
    sec_end = len(lines)
    for j in range(head_idx + 1, len(lines)):
        if lines[j].startswith("## "):
            sec_end = j
            break
    last = head_idx
    for k in range(head_idx + 1, sec_end):
        if lines[k].strip():
            last = k
    # Character offset of the end of `last`'s line (just past its content, before its newline).
    offset = sum(len(lines[n]) + 1 for n in range(last))  # +1 for each consumed "\n"
    offset += len(lines[last])
    # Splice "\n<body>" right after the last content line (before its trailing newline).
    return content[:offset] + "\n" + body + content[offset:]


def _apply_addition(content: str, proposed_body: str, section_hint: str | None) -> str:
    """Insert a new element under ``section_hint`` (if it names a section) else at the file tail.

    Byte-faithful by construction: a pure character splice — every original byte survives in
    order; the only new bytes are ``body`` plus its separating newline(s). A tail append leaves
    the original content as a verbatim prefix.
    """
    body = proposed_body.strip("\n")
    if section_hint:
        spliced = _insert_in_section(content, section_hint, body)
        if spliced is not None:
            return spliced
    if content == "" or content.endswith("\n"):
        return content + body + "\n"
    return content + "\n" + body + "\n"


def _apply_modification(content: str, region: str, proposed_body: str) -> str:
    """Replace exactly the located ``region`` with ``proposed_body``; every other byte identical.

    ``region`` is the verbatim enclosing-line span returned by the locator, so the prefix before
    it and the suffix after it are preserved byte-for-byte.
    """
    body = proposed_body.strip("\n")
    idx = content.find(region)
    return content[:idx] + body + content[idx + len(region):]


def _common_prefix_len(a: str, b: str) -> int:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def _common_suffix_len(a: str, b: str, floor: int) -> int:
    """Longest common suffix length, not crossing ``floor`` chars already claimed as prefix."""
    n = min(len(a), len(b)) - floor
    i = 0
    while i < n and a[len(a) - 1 - i] == b[len(b) - 1 - i]:
        i += 1
    return i


def _verify_surgical(old: str, new: str, kind: str, region: str | None) -> None:
    """Assert the splice touched ONLY the target region — every other byte is identical.

    The load-bearing guard against the silent-overwrite bug: if this ever fails we raise rather
    than write a file whose non-target bytes drifted. For an addition, NO original byte may be
    removed (insertion only); for a modification, the bytes before and after the located region
    must survive verbatim.
    """
    if kind == "addition":
        # An insertion removes nothing: old must be the shared prefix + shared suffix exactly.
        p = _common_prefix_len(old, new)
        s = _common_suffix_len(old, new, p)
        if old[p: len(old) - s] != "":
            raise WritebackRefused("error", "addition removed/mutated existing bytes (not surgical)")
        return
    # modification / annotation: prefix-before and suffix-after the region must survive verbatim
    idx = old.find(region or "")
    prefix, suffix = old[:idx], old[idx + len(region or ""):]
    if not (new.startswith(prefix) and new.endswith(suffix)):
        raise WritebackRefused("error", "modification mutated bytes outside the located region")


def _commit_spliced(target: Path, text: str) -> None:
    """Atomically write the in-memory-spliced ``text`` (tmp file + ``os.replace``).

    This is the surgical carve-out's single write. It is deliberately NOT ``Path.write_text`` /
    ``save_artifact`` (the whole-file-overwrite tokens the US7 guard greps for): the bytes here
    are the verified splice of the file we just read, not an external buffer. A crash mid-write
    leaves either the old file or the new file — never a truncated one.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), prefix=".", suffix=".collab.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp_name, target)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _provenance_badge(cr: dict, summary: dict) -> str:
    """One-line provenance badge for the change summary (e.g. the FR-021 example in the plan).

    ``+FR-021 — added by planning · agent cast-high-level-planner · derived from plan.collab.md``
    Built from the change-request's own provenance columns + the lead change item; data, never a
    code branch on author (FR-013).
    """
    items = summary.get("items") or []
    lead = items[0] if items else None
    sign = {"added": "+", "modified": "~", "removed": "-"}.get(
        (lead or {}).get("change", ""), "~")
    ref = (lead or {}).get("heading_or_ref", cr.get("target_quote") or "(addition)")
    verb = (lead or {}).get("change", cr["kind"])
    origin = cr.get("origin_phase") or "a downstream phase"
    who = (f"agent {cr['author']}" if cr["author_type"] == "agent" else f"{cr['author']}")
    parts = [f"{sign}{ref} — {verb} by {origin}", who]
    if cr.get("origin_artifact_path"):
        parts.append(f"derived from {cr['origin_artifact_path']}")
    return " · ".join(parts)


def _change_summary(old_content: str, new_content: str) -> dict:
    """The deterministic block-level change set this apply introduced (``summarize(diff_blocks)``).

    Reuses the landed Phase 4 engine verbatim — never forks it, never invents entries.
    """
    from cast_server.requirements_render.block_diff import diff_blocks, summarize
    from cast_server.requirements_render.parser import parse_requirements

    old_parsed = parse_requirements(old_content)
    new_parsed = parse_requirements(new_content)
    return summarize(diff_blocks(old_parsed, new_parsed))


def _record_refusal(cr_id: int, verdict: str, actor: str | None, payload: dict | None,
                    *, set_status: str | None, db_path: Path | None) -> None:
    """Write the refusal ``change_request_events`` row (and optional status flip) in one txn.

    Conflict/orphan never silently no-op (sp3a): they leave an audit row even though the file is
    untouched.
    """
    now = _now()
    conn = get_connection(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        if set_status is not None:
            conn.execute(
                "UPDATE change_requests SET status = ?, updated_at = ? WHERE id = ?",
                (set_status, now, cr_id),
            )
        _append_event(conn, cr_id, verdict, actor, payload, now)
        conn.commit()
    finally:
        conn.close()


def apply_change_request(
    change_request_id: int,
    *,
    goal_dir: Path,
    locate: Locator = verbatim_locate,
    allowed_root: Path | None = None,
    actor: str | None = None,
    target_quote_override: str | None = None,
    section_hint_override: str | None = None,
    db_path: Path | None = None,
) -> dict:
    """Surgically apply an accepted/auto-applied change-request to the goal's ``.collab.md``.

    The sole file-writer. Pipeline: **path-scope → reanchor/locate → conflict gate → surgical
    splice → byte-identity verify → write → version bump → change summary (provenance badge) →
    ``applied`` event + ``notifications_outbox`` row in one txn.**

    ``locate`` is injected (production: :func:`verbatim_locate`; tests: a pure stub).
    ``target_quote_override`` lets the writeback agent re-run apply with the verbatim quote
    ``cast-comment-reanchor`` relocated to, after a deterministic ``orphaned`` on the original.

    Refusals (raise :class:`WritebackRefused`, file left byte-identical):

    * **out-of-tree** — ``goal_dir`` escapes ``allowed_root`` (default :data:`GOALS_DIR`). No
      DB write, no file touch, no crash.
    * **orphaned** — the target quote does not locate in HEAD. Audit row written; file untouched.
    * **conflicted** — a human changed the target region since ``base_version``. Audit row +
      ``ConflictSurface`` written; file untouched; NO auto-merge.

    On success returns ``{status: "applied", change_request_id, applied_version, convergence,
    displaced_comment_ids, change_summary, provenance_badge, file}``.
    """
    from cast_server.requirements_render.conflict import ConflictSurface, detect_conflict
    from cast_server.services import requirement_version_service

    cr = get(change_request_id, db_path=db_path)
    if cr is None:
        raise WritebackRefused("error", f"no change_request id={change_request_id}")

    target_quote = target_quote_override if target_quote_override is not None else cr["target_quote"]
    section_hint = (section_hint_override
                    if section_hint_override is not None else cr["section_hint"])
    kind = cr["kind"]

    # --- Step 4.4: path-scope (security) — refuse out-of-tree, never crash, never write -------
    allowed_root = (allowed_root or GOALS_DIR).resolve()
    goal_dir = Path(goal_dir).resolve()
    if not _is_within(goal_dir, allowed_root):
        raise WritebackRefused("out-of-tree", f"goal_dir {goal_dir} escapes {allowed_root}")
    target = (goal_dir / _REQUIREMENTS_FILENAME).resolve()
    if not _is_within(target, goal_dir):           # defence-in-depth (fixed filename, but assert)
        raise WritebackRefused("out-of-tree", f"target {target} escapes goal_dir {goal_dir}")
    if not target.exists():
        raise WritebackRefused("orphaned", f"{_REQUIREMENTS_FILENAME} absent under {goal_dir}")

    old_content = target.read_text(encoding="utf-8")

    # --- Step 4.1/4.2: conflict gate (sp3a) — only `clean` proceeds to apply -------------------
    base_row = requirement_version_service.get_version(
        cr["goal_slug"], cr["base_version"], db_path=db_path)
    base_content = base_row["content"] if base_row else ""
    verdict = detect_conflict(base_content, old_content, target_quote, section_hint, locate=locate)

    if verdict == "orphaned":
        surface = ConflictSurface(verdict="orphaned", target_quote=target_quote,
                                  section_hint=section_hint, base_version=cr["base_version"],
                                  proposed_body=cr["proposed_body"]).to_dict()
        _record_refusal(cr["id"], "orphaned", actor,
                        {"target_quote": target_quote, "section_hint": section_hint},
                        set_status=None, db_path=db_path)
        raise WritebackRefused("orphaned", "target quote no longer locates", surface=surface)

    if verdict == "conflicted":
        surface = ConflictSurface(verdict="conflicted", target_quote=target_quote,
                                  section_hint=section_hint, base_version=cr["base_version"],
                                  proposed_body=cr["proposed_body"]).to_dict()
        _record_refusal(cr["id"], "conflicted", actor,
                        {"surface": surface}, set_status="conflicted", db_path=db_path)
        raise WritebackRefused("conflicted", "target region changed since base_version",
                               surface=surface)

    # --- Step 4.2: surgical splice + byte-identity verification (in memory) --------------------
    if kind == "addition":
        new_content = _apply_addition(old_content, cr["proposed_body"], section_hint)
        region = None
    else:
        region = locate(old_content, target_quote, section_hint)
        if region is None:                          # belt-and-braces; conflict gate already ran
            raise WritebackRefused("orphaned", "target quote no longer locates")
        new_content = _apply_modification(old_content, region, cr["proposed_body"])
    _verify_surgical(old_content, new_content, kind, region)

    # --- write the FILE (the single carve-out write), then bump the version -------------------
    _commit_spliced(target, new_content)
    bump = requirement_version_service.create_next(
        cr["goal_slug"], new_content, created_by=(actor or cr["author"]), db_path=db_path)
    applied_version = bump["version"]["version"]

    # --- Step 4.3: change summary (+ provenance badge) ----------------------------------------
    summary = _change_summary(old_content, new_content)
    badge = _provenance_badge(cr, summary)

    # --- Step 4.3: applied event + outbox row in ONE apply txn (crash leaves nothing half-done)
    now = _now()
    notification = {
        **_notification_payload(cr),
        "status": "applied",
        "applied_version": applied_version,
        "provenance_badge": badge,
        "change_summary": summary,
    }
    conn = get_connection(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            "UPDATE change_requests SET status = 'applied', updated_at = ? WHERE id = ?",
            (now, cr["id"]),
        )
        _append_event(conn, cr["id"], "applied", actor,
                      {"applied_version": applied_version, "provenance_badge": badge,
                       "counts": summary["counts"]}, now)
        conn.execute(
            """INSERT INTO notifications_outbox (change_request_id, payload, status, created_at)
               VALUES (?, ?, 'pending', ?)""",
            (cr["id"], json.dumps(notification), now),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "status": "applied",
        "change_request_id": cr["id"],
        "applied_version": applied_version,
        "convergence": bump["convergence"],
        "displaced_comment_ids": bump["displaced_comment_ids"],
        "change_summary": summary,
        "provenance_badge": badge,
        "file": str(target),
    }


def apply_for_goal(goal_slug: str, change_request_id: int, *,
                   goals_dir: Path | None = None, actor: str | None = None,
                   target_quote_override: str | None = None,
                   section_hint_override: str | None = None,
                   db_path: Path | None = None) -> dict:
    """Production wrapper the ``cast-requirements-writeback`` agent invokes (resolves the goal dir).

    Resolves the authoritative goal directory (a routed goal's ``folder_path`` wins, mirroring the
    render service), wires the verbatim production locator, and scopes the writer to that goal dir.
    """
    from cast_server.services import requirements_render_service

    goals_dir = goals_dir or GOALS_DIR
    goal_dir = requirements_render_service._resolve_goal_dir(goal_slug, goals_dir, db_path)
    return apply_change_request(
        change_request_id, goal_dir=goal_dir, locate=verbatim_locate,
        allowed_root=goals_dir, actor=actor,
        target_quote_override=target_quote_override,
        section_hint_override=section_hint_override, db_path=db_path)


# --------------------------------------------------------------------------- #
# CLI — the entry point the writeback agent shells out to (it, not a route, writes the file) #
# --------------------------------------------------------------------------- #

def _cli_apply(argv: list[str]) -> int:
    """``apply <goal_slug> <cr_id> [--actor A] [--target-quote Q] [--section-hint H]``.

    Prints one JSON object: ``{"result": "applied", ...}`` on success, or
    ``{"result": "refused", "verdict": ..., "reason": ..., "surface": ...}`` on a refusal. The
    agent reads this to decide whether to dispatch ``cast-comment-reanchor`` (orphan) or surface
    a conflict. Refusals exit non-zero so a shell ``if`` can branch.
    """
    import argparse

    parser = argparse.ArgumentParser(prog="change_request_service apply")
    parser.add_argument("goal_slug")
    parser.add_argument("change_request_id", type=int)
    parser.add_argument("--actor", default=None)
    parser.add_argument("--target-quote", default=None)
    parser.add_argument("--section-hint", default=None)
    args = parser.parse_args(argv)

    try:
        result = apply_for_goal(
            args.goal_slug, args.change_request_id, actor=args.actor,
            target_quote_override=args.target_quote,
            section_hint_override=args.section_hint)
        print(json.dumps({"result": "applied", **result}))
        return 0
    except WritebackRefused as refused:
        print(json.dumps({"result": "refused", "verdict": refused.verdict,
                          "reason": refused.reason, "surface": refused.surface}))
        return 1


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2 and sys.argv[1] == "apply":
        raise SystemExit(_cli_apply(sys.argv[2:]))
    print("Usage: python -m cast_server.services.change_request_service apply "
          "<goal_slug> <cr_id> [--actor A] [--target-quote Q] [--section-hint H]")
    raise SystemExit(2)
