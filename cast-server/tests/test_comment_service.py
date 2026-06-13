"""Pin the comment service — CRUD, the in-transaction event trail, the state machine, and
the read-time displacement detector (Phase 4, WP-A / sp1).

The comment layer is the only deterministic machinery in Phase 4 (decisions #1/#9): every
state transition MUST write its ``comment_events`` row in the same transaction, and nothing
positional is ever stored — ``displaced`` is recomputed on every ``list_comments``.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from cast_server.db.connection import get_connection, init_db
from cast_server.services import comment_service
from cast_server.services import requirement_version_service as version_service
from cast_server.services.comment_service import CommentNotFound, CommentStateError

SLUG = "comment-test"


@pytest.fixture
def db_path(tmp_path) -> Path:
    """Fresh tmp DB seeded with a goal row + a current requirement_versions snapshot."""
    path = tmp_path / "comments.db"
    init_db(path)
    conn = get_connection(path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) VALUES (?, ?, ?)",
            (SLUG, "Comment test goal", str(tmp_path / SLUG)),
        )
        conn.commit()
    finally:
        conn.close()
    # A current version so create_comment resolves version=1 (not 0).
    version_service.create_snapshot(SLUG, "the requirements body", db_path=path)
    return path


def _events(comment_id: int, db_path: Path) -> list[dict]:
    return comment_service.get_comment_events(comment_id, db_path=db_path)


# --------------------------------------------------------------------------- #
# Create + the created event                                                   #
# --------------------------------------------------------------------------- #

def test_create_writes_row_and_created_event_one_txn(db_path):
    row = comment_service.create_comment(
        SLUG, quoted_text="body", section_hint="Intro", body="please clarify",
        author="alice", db_path=db_path,
    )
    assert row["id"] > 0
    assert row["state"] == "open"
    assert row["version"] == 1  # resolved from the current snapshot
    assert row["author_kind"] == "human"  # default

    events = _events(row["id"], db_path)
    assert len(events) == 1
    assert events[0]["event_type"] == "created"
    assert events[0]["actor"] == "alice"


def test_create_defaults_version_zero_when_no_snapshot(tmp_path):
    path = tmp_path / "novers.db"
    init_db(path)
    conn = get_connection(path)
    try:
        conn.execute(
            "INSERT INTO goals (slug, title, folder_path) VALUES (?, ?, ?)",
            ("ns", "No snap", str(tmp_path / "ns")),
        )
        conn.commit()
    finally:
        conn.close()
    row = comment_service.create_comment(
        "ns", quoted_text="q", section_hint=None, body="b", author="x", db_path=path,
    )
    assert row["version"] == 0


def test_create_honors_explicit_agent_author_kind(db_path):
    row = comment_service.create_comment(
        SLUG, quoted_text="body", section_hint=None, body="agent note",
        author="cast-refine-requirements", author_kind="agent", db_path=db_path,
    )
    assert row["author_kind"] == "agent"


# --------------------------------------------------------------------------- #
# State machine + one event per transition                                     #
# --------------------------------------------------------------------------- #

def test_resolve_then_reopen_roundtrips_with_events(db_path):
    c = comment_service.create_comment(SLUG, "body", None, "b", "a", db_path=db_path)
    cid = c["id"]

    resolved = comment_service.resolve_comment(cid, "alice", db_path=db_path)
    assert resolved["state"] == "resolved"

    reopened = comment_service.reopen_comment(cid, "alice", db_path=db_path)
    assert reopened["state"] == "open"

    types = [e["event_type"] for e in _events(cid, db_path)]
    assert types == ["created", "resolved", "reopened"]


def test_double_resolve_raises_state_error(db_path):
    c = comment_service.create_comment(SLUG, "body", None, "b", "a", db_path=db_path)
    comment_service.resolve_comment(c["id"], "a", db_path=db_path)
    with pytest.raises(CommentStateError):
        comment_service.resolve_comment(c["id"], "a", db_path=db_path)


def test_reopen_open_comment_raises_state_error(db_path):
    c = comment_service.create_comment(SLUG, "body", None, "b", "a", db_path=db_path)
    with pytest.raises(CommentStateError):
        comment_service.reopen_comment(c["id"], "a", db_path=db_path)


def test_orphan_marks_state_and_event(db_path):
    c = comment_service.create_comment(SLUG, "body", None, "b", "a", db_path=db_path)
    out = comment_service.orphan_comment(c["id"], "system", db_path=db_path)
    assert out["state"] == "orphaned"
    types = [e["event_type"] for e in _events(c["id"], db_path)]
    assert types == ["created", "orphaned"]


def test_relocate_updates_quote_and_stores_old_in_payload(db_path):
    c = comment_service.create_comment(SLUG, "old quote", "Intro", "b", "a", db_path=db_path)
    out = comment_service.relocate_comment(
        c["id"], "new quote", "Updated Section", "agent", db_path=db_path,
    )
    assert out["quoted_text"] == "new quote"
    assert out["section_hint"] == "Updated Section"

    reloc = [e for e in _events(c["id"], db_path) if e["event_type"] == "relocated"]
    assert len(reloc) == 1
    import json
    assert json.loads(reloc[0]["payload"])["old_quoted_text"] == "old quote"


def test_transition_on_unknown_id_raises_not_found(db_path):
    for fn in (
        lambda: comment_service.resolve_comment(9999, "a", db_path=db_path),
        lambda: comment_service.reopen_comment(9999, "a", db_path=db_path),
        lambda: comment_service.orphan_comment(9999, "a", db_path=db_path),
        lambda: comment_service.relocate_comment(9999, "x", None, "a", db_path=db_path),
        lambda: comment_service.get_comment(9999, db_path=db_path),
    ):
        with pytest.raises(CommentNotFound):
            fn()


# --------------------------------------------------------------------------- #
# open_comment_count                                                           #
# --------------------------------------------------------------------------- #

def test_open_comment_count_excludes_resolved_and_orphaned(db_path):
    a = comment_service.create_comment(SLUG, "qa", None, "b", "u", db_path=db_path)
    b = comment_service.create_comment(SLUG, "qb", None, "b", "u", db_path=db_path)
    comment_service.create_comment(SLUG, "qc", None, "b", "u", db_path=db_path)
    assert comment_service.open_comment_count(SLUG, db_path=db_path) == 3

    comment_service.resolve_comment(a["id"], "u", db_path=db_path)
    comment_service.orphan_comment(b["id"], "u", db_path=db_path)
    assert comment_service.open_comment_count(SLUG, db_path=db_path) == 1


# --------------------------------------------------------------------------- #
# Displacement detector (read-time, derived, never stored)                     #
# --------------------------------------------------------------------------- #

def test_list_stamps_displaced_based_on_supplied_text(db_path):
    # refine-req-v3 sp2: created comments are render-space, so the comparison text comes from the
    # ``render_text`` seam (the served render), not ``current_text`` (the source seam).
    present = comment_service.create_comment(SLUG, "anchored slice", None, "b", "u", db_path=db_path)
    absent = comment_service.create_comment(SLUG, "vanished slice", None, "b", "u", db_path=db_path)

    rows = comment_service.list_comments(
        SLUG, db_path=db_path, render_text="here is an anchored slice in the file",
    )
    by_id = {r["id"]: r for r in rows}
    assert by_id[present["id"]]["displaced"] is False
    assert by_id[absent["id"]]["displaced"] is True


def test_list_source_space_comment_uses_source_seam(db_path):
    """A legacy ``'source'``-space comment (not yet migrated) still displacement-checks against the
    source ``current_text`` seam — the render move does not strand pre-migration comments."""
    row = comment_service.create_comment(SLUG, "legacy slice", None, "b", "u", db_path=db_path)
    # Demote it to source space to simulate a pre-migration / pre-v3 comment.
    conn = get_connection(db_path)
    try:
        conn.execute(
            "UPDATE requirement_comments SET anchor_space = 'source' WHERE id = ?", (row["id"],)
        )
        conn.commit()
    finally:
        conn.close()
    rows = comment_service.list_comments(
        SLUG, db_path=db_path, current_text="here is a legacy slice in the file",
    )
    assert {r["id"]: r for r in rows}[row["id"]]["displaced"] is False


def test_orphaned_and_resolved_not_displacement_checked(db_path):
    resolved = comment_service.create_comment(SLUG, "gone", None, "b", "u", db_path=db_path)
    orphaned = comment_service.create_comment(SLUG, "also gone", None, "b", "u", db_path=db_path)
    comment_service.create_comment(SLUG, "open one", None, "b", "u", db_path=db_path)
    comment_service.resolve_comment(resolved["id"], "u", db_path=db_path)
    comment_service.orphan_comment(orphaned["id"], "u", db_path=db_path)

    rows = comment_service.list_comments(SLUG, db_path=db_path, current_text="nothing matches")
    by_id = {r["id"]: r for r in rows}
    assert "displaced" not in by_id[resolved["id"]]
    assert "displaced" not in by_id[orphaned["id"]]


def test_list_looks_up_goal_file_when_text_not_supplied(db_path, tmp_path):
    # Seed the goal file the service reads via _resolve_goal_dir.
    goal_dir = tmp_path / SLUG
    goal_dir.mkdir(parents=True, exist_ok=True)
    (goal_dir / "refined_requirements.collab.md").write_text(
        "the live file mentions a stored quote", encoding="utf-8",
    )
    present = comment_service.create_comment(SLUG, "stored quote", None, "b", "u", db_path=db_path)
    absent = comment_service.create_comment(SLUG, "missing quote", None, "b", "u", db_path=db_path)

    rows = comment_service.list_comments(SLUG, db_path=db_path)
    by_id = {r["id"]: r for r in rows}
    assert by_id[present["id"]]["displaced"] is False
    assert by_id[absent["id"]]["displaced"] is True


def test_list_missing_file_marks_all_open_displaced(db_path):
    # No goal file on disk → current text "" → every open comment is displaced (never crash).
    comment_service.create_comment(SLUG, "anything", None, "b", "u", db_path=db_path)
    rows = comment_service.list_comments(SLUG, db_path=db_path)
    assert all(r["displaced"] is True for r in rows if r["state"] == "open")


def test_list_filters_by_state(db_path):
    a = comment_service.create_comment(SLUG, "qa", None, "b", "u", db_path=db_path)
    comment_service.create_comment(SLUG, "qb", None, "b", "u", db_path=db_path)
    comment_service.resolve_comment(a["id"], "u", db_path=db_path)

    resolved = comment_service.list_comments(SLUG, state="resolved", db_path=db_path)
    assert len(resolved) == 1 and resolved[0]["id"] == a["id"]
