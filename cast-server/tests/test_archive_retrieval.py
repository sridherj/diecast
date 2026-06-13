"""Pin archive retrieval (US5 S3) — a historical version returned WITH its comments at their
**as-of** resolution state, reconstructed by replaying the append-only ``comment_events`` trail.

The single subtle correctness point of sp3 (per the plan): a comment left on v1 and resolved
*during* v2 must read **open** as of v1's archival and **resolved** as of v2's. That ordering
turns on version-creation timestamps sitting between comment-event timestamps, so the scenario
test drives a deterministic monotonic clock across BOTH services (no wall-clock flakiness).

``_state_as_of`` is also unit-tested directly over hand-built event trails. And FR-011 is pinned
structurally: after three bumps the goal folder still holds ONLY the two canonical files —
versions are DB rows, never version-suffixed files.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from cast_server.db.connection import get_connection, init_db
from cast_server.services import comment_service
from cast_server.services import requirement_version_service as version_service

SLUG = "arch-test"


@pytest.fixture
def db_path(tmp_path) -> Path:
    """A fresh seeded tmp DB (the goals row satisfies the FK on requirement_versions)."""
    path = tmp_path / "archive.db"
    init_db(path)
    conn = get_connection(path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) VALUES (?, ?, ?)",
            (SLUG, "Archive test goal", SLUG),
        )
        conn.commit()
    finally:
        conn.close()
    return path


class _Clock:
    """A monotonic ISO-timestamp source — one tick per call, deterministic ordering."""

    def __init__(self) -> None:
        self._t = 0

    def iso(self, *args, **kwargs) -> str:  # noqa: ANN002, ANN003
        self._t += 1
        return f"2026-06-11T00:00:{self._t:02d}+00:00"


@pytest.fixture
def clock(monkeypatch) -> _Clock:
    """Drive both services off one monotonic clock so event/version ordering is deterministic."""
    c = _Clock()
    # comment_service stamps via its _now() helper.
    monkeypatch.setattr(comment_service, "_now", c.iso)
    # version_service stamps via datetime.now(timezone.utc).isoformat() inline.
    fake_dt = MagicMock()
    fake_dt.now.return_value.isoformat.side_effect = c.iso
    monkeypatch.setattr(version_service, "datetime", fake_dt)
    return c


# ---------------------------------------------------------------------------
# _state_as_of — pure replay helper (fully deterministic, hand-built trails)
# ---------------------------------------------------------------------------

def _ev(event_type: str, created_at: str) -> dict:
    return {"event_type": event_type, "created_at": created_at}


def test_state_as_of_created_only_is_open():
    events = [_ev("created", "...01")]
    assert version_service._state_as_of(events, None) == "open"


def test_state_as_of_before_creation_is_none():
    events = [_ev("created", "...05")]
    assert version_service._state_as_of(events, "...02") is None


def test_state_as_of_cutoff_before_resolution_is_open():
    events = [_ev("created", "...01"), _ev("resolved", "...03")]
    assert version_service._state_as_of(events, "...02") == "open"


def test_state_as_of_cutoff_after_resolution_is_resolved():
    events = [_ev("created", "...01"), _ev("resolved", "...03")]
    assert version_service._state_as_of(events, "...04") == "resolved"


def test_state_as_of_created_resolved_reopened_replay():
    events = [
        _ev("created", "...01"),
        _ev("resolved", "...03"),
        _ev("reopened", "...05"),
    ]
    assert version_service._state_as_of(events, "...02") == "open"
    assert version_service._state_as_of(events, "...04") == "resolved"
    assert version_service._state_as_of(events, "...06") == "open"
    assert version_service._state_as_of(events, None) == "open"


def test_state_as_of_relocated_does_not_change_state():
    events = [
        _ev("created", "...01"),
        _ev("resolved", "...03"),
        _ev("relocated", "...04"),  # re-anchor, not a state transition
    ]
    assert version_service._state_as_of(events, "...05") == "resolved"


# ---------------------------------------------------------------------------
# The resolve-after-archive scenario (US5 S3) — three bumps, one resolve
# ---------------------------------------------------------------------------

def test_resolve_after_archive_reconstructs_as_of_state(db_path, clock):
    """A comment left on v1, resolved during v2: open as of v1, resolved as of v2."""
    version_service.create_next(SLUG, "v1 body", "human", db_path=db_path)  # version 1 @ :01
    c = comment_service.create_comment(                                     # created @ :02
        SLUG, quoted_text="v1 body", section_hint=None, body="left on v1",
        author="human", db_path=db_path,
    )
    version_service.create_next(SLUG, "v2 body", "human", db_path=db_path)  # version 2 @ :03
    comment_service.resolve_comment(c["id"], "human", db_path=db_path)      # resolved @ :04
    version_service.create_next(SLUG, "v3 body", "human", db_path=db_path)  # version 3 @ :05

    v1 = version_service.get_version_with_comments(SLUG, 1, db_path=db_path)
    v2 = version_service.get_version_with_comments(SLUG, 2, db_path=db_path)

    assert [c["id"] for c in v1["comments"]] == [c["id"]]
    assert v1["comments"][0]["state_as_of"] == "open"      # as of v1's supersession (v2's birth)
    assert v2["comments"][0]["state_as_of"] == "resolved"  # as of v2's supersession (v3's birth)


def test_get_version_unknown_returns_none(db_path):
    version_service.create_next(SLUG, "only", "human", db_path=db_path)
    assert version_service.get_version_with_comments(SLUG, 99, db_path=db_path) is None


def test_archived_version_returns_content_and_comments(db_path, clock):
    version_service.create_next(SLUG, "first", "human", db_path=db_path)
    comment_service.create_comment(
        SLUG, quoted_text="first", section_hint=None, body="note",
        author="agent", author_kind="agent", db_path=db_path,
    )
    version_service.create_next(SLUG, "second", "human", db_path=db_path)

    v1 = version_service.get_version_with_comments(SLUG, 1, db_path=db_path)
    assert v1["version"]["content"] == "first"
    assert v1["version"]["status"] == "archived"
    assert len(v1["comments"]) == 1
    assert v1["comments"][0]["state_as_of"] == "open"


def test_comment_left_after_version_is_excluded_from_earlier_version(db_path, clock):
    """A comment created against v2 must not appear in v1's as-of view."""
    version_service.create_next(SLUG, "v1", "human", db_path=db_path)   # version 1
    version_service.create_next(SLUG, "v2", "human", db_path=db_path)   # version 2
    comment_service.create_comment(  # left while v2 current → version=2
        SLUG, quoted_text="v2", section_hint=None, body="on v2",
        author="human", db_path=db_path,
    )

    v1 = version_service.get_version_with_comments(SLUG, 1, db_path=db_path)
    assert v1["comments"] == []


# ---------------------------------------------------------------------------
# FR-011 — versions are rows; the goal folder NEVER gains a second requirements file
# ---------------------------------------------------------------------------

def test_fr011_folder_holds_only_canonical_files_after_three_bumps(db_path, tmp_path):
    """Three create_next bumps write DB rows only — the goal folder is untouched."""
    goal_dir = tmp_path / "goalfolder"
    goal_dir.mkdir()
    (goal_dir / "refined_requirements.collab.md").write_text("body", encoding="utf-8")
    (goal_dir / "refined_requirements.html").write_text("<html></html>", encoding="utf-8")

    version_service.create_next(SLUG, "a", "human", db_path=db_path)
    version_service.create_next(SLUG, "b", "human", db_path=db_path)
    version_service.create_next(SLUG, "c", "human", db_path=db_path)

    assert sorted(p.name for p in goal_dir.iterdir()) == [
        "refined_requirements.collab.md",
        "refined_requirements.html",
    ]
    assert len(version_service.list_versions(SLUG, db_path=db_path)) == 3
