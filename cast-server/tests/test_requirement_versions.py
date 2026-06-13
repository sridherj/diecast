"""Pin the version-snapshot service, content-hash determinism, and the grammar bridge.

The snapshot service is the conflict-detection spine: monotonic versions, a single 'current'
row per goal, content-hash idempotency, and a hard ``UNIQUE(goal_slug, version)`` guarantee.
The grammar smoke test fails loudly if ``bin/cast-spec-checker`` is moved/renamed and the
importlib bridge in ``spec_grammar`` breaks (the documented Med risk).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from cast_server.db.connection import get_connection, init_db
from cast_server.requirements_render import spec_grammar
from cast_server.requirements_render.hashing import content_hash
from cast_server.services import comment_service
from cast_server.services import requirement_version_service as version_service

SLUG = "ver-test"

_FIXTURES = Path(__file__).parent / "fixtures" / "refine_requirements_v2"
V1_TEXT = (_FIXTURES / "refined_requirements.collab.md").read_text(encoding="utf-8")
V2_EDIT_TEXT = (_FIXTURES / "refined_requirements.v2-edit.collab.md").read_text(encoding="utf-8")

# A line present in v1 but DELETED in the v2 edit (→ a displaced quote) and one that SURVIVES.
DELETED_QUOTE = "Changes to the exploration pipeline (cast-explore) itself."
SURVIVING_QUOTE = "Faster comprehension"


@pytest.fixture
def db_path(tmp_path) -> Path:
    """A fresh, seeded tmp DB. The goals row is required by the FK on requirement_versions."""
    path = tmp_path / "versions.db"
    init_db(path)
    conn = get_connection(path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) VALUES (?, ?, ?)",
            (SLUG, "Version test goal", SLUG),
        )
        conn.commit()
    finally:
        conn.close()
    return path


# ---------------------------------------------------------------------------
# Snapshot semantics
# ---------------------------------------------------------------------------

def test_first_snapshot_is_version_1_current(db_path):
    row = version_service.create_snapshot(SLUG, "A", db_path=db_path)
    assert row["version"] == 1
    assert row["status"] == "current"
    assert row["content"] == "A"
    assert row["content_hash"] == content_hash("A")


def test_identical_content_is_idempotent_noop(db_path):
    first = version_service.create_snapshot(SLUG, "A", db_path=db_path)
    again = version_service.create_snapshot(SLUG, "A", db_path=db_path)

    assert again["version"] == first["version"] == 1
    assert len(version_service.list_versions(SLUG, db_path=db_path)) == 1


def test_changed_content_creates_v2_and_archives_v1(db_path):
    version_service.create_snapshot(SLUG, "A", db_path=db_path)
    v2 = version_service.create_snapshot(SLUG, "B", db_path=db_path)

    assert v2["version"] == 2
    assert v2["status"] == "current"

    current = version_service.get_current(SLUG, db_path=db_path)
    assert current["version"] == 2

    v1 = version_service.get_version(SLUG, 1, db_path=db_path)
    assert v1["status"] == "archived"

    # Exactly one 'current' row for the goal.
    rows = version_service.list_versions(SLUG, db_path=db_path)
    assert [r["status"] for r in rows] == ["archived", "current"]


def test_unique_goal_version_violation_raises(db_path):
    version_service.create_snapshot(SLUG, "A", db_path=db_path)

    conn = get_connection(db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """INSERT INTO requirement_versions
                   (goal_slug, version, content, content_hash, status, created_at)
                   VALUES (?, 1, 'dup', 'deadbeef', 'archived', '2026-06-11T00:00:00+00:00')""",
                (SLUG,),
            )
            conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# create_next() — the version gate (sp3, critical path sp1 → sp3 → sp4b)
# ---------------------------------------------------------------------------

def test_create_next_snapshots_and_archives_in_one_txn(db_path):
    version_service.create_next(SLUG, "A", "human", db_path=db_path)
    result = version_service.create_next(SLUG, "B", "human", db_path=db_path)

    assert result["version"]["version"] == 2
    assert result["version"]["status"] == "current"

    rows = version_service.list_versions(SLUG, db_path=db_path)
    assert [r["status"] for r in rows] == ["archived", "current"]


def test_create_next_wraps_create_snapshot_idempotently(db_path):
    first = version_service.create_next(SLUG, "A", "human", db_path=db_path)
    again = version_service.create_next(SLUG, "A", "human", db_path=db_path)

    assert again["version"]["version"] == first["version"]["version"] == 1
    assert len(version_service.list_versions(SLUG, db_path=db_path)) == 1


def test_convergence_converged_when_no_open_comments(db_path):
    result = version_service.create_next(SLUG, "A", "human", db_path=db_path)
    assert result["convergence"] == "converged"
    assert result["open_comments"] == []
    assert result["displaced_comment_ids"] == []


def test_convergence_unconverged_with_open_comment(db_path):
    version_service.create_next(SLUG, "A", "human", db_path=db_path)
    comment_service.create_comment(
        SLUG, quoted_text="A", section_hint=None, body="clarify", author="human",
        db_path=db_path,
    )
    result = version_service.create_next(SLUG, "A2", "human", db_path=db_path)

    assert result["convergence"] == "unconverged"
    assert len(result["open_comments"]) == 1


def test_open_comments_carry_forward_unchanged(db_path):
    """Carry-forward = do nothing: open rows keep their original version, stay open + listed."""
    version_service.create_next(SLUG, "A", "human", db_path=db_path)  # version 1
    c = comment_service.create_comment(
        SLUG, quoted_text="A", section_hint=None, body="left on v1", author="human",
        db_path=db_path,
    )
    assert c["version"] == 1

    version_service.create_next(SLUG, "B", "human", db_path=db_path)  # bump to version 2

    still_open = comment_service.list_comments(SLUG, state="open",
                                               current_text="B", db_path=db_path)
    assert len(still_open) == 1
    assert still_open[0]["id"] == c["id"]
    assert still_open[0]["version"] == 1  # provenance unchanged — no row copying / remapping


def test_displaced_comment_ids_is_verbatim_string_find(db_path):
    """displaced_comment_ids == exactly the open comments whose quotes were edited away."""
    version_service.create_next(SLUG, V1_TEXT, "human", db_path=db_path)
    displaced = comment_service.create_comment(
        SLUG, quoted_text=DELETED_QUOTE, section_hint="Out of scope",
        body="this line went away", author="human", db_path=db_path,
    )
    surviving = comment_service.create_comment(
        SLUG, quoted_text=SURVIVING_QUOTE, section_hint="Intent",
        body="still here", author="human", db_path=db_path,
    )

    result = version_service.create_next(SLUG, V2_EDIT_TEXT, "human", db_path=db_path)

    assert result["displaced_comment_ids"] == [displaced["id"]]
    assert surviving["id"] not in result["displaced_comment_ids"]


def test_create_next_runs_no_llm_or_subprocess(db_path, monkeypatch):
    """Displacement is a pure string-find — create_next must never shell out or call an LLM."""
    import subprocess

    def _boom(*a, **k):  # noqa: ANN002, ANN003
        raise AssertionError("create_next must not spawn a subprocess")

    monkeypatch.setattr(subprocess, "run", _boom)
    monkeypatch.setattr(subprocess, "Popen", _boom)

    result = version_service.create_next(SLUG, "A", "human", db_path=db_path)
    assert result["convergence"] == "converged"


# ---------------------------------------------------------------------------
# Content hash determinism
# ---------------------------------------------------------------------------

def test_content_hash_is_deterministic_and_distinguishing():
    assert content_hash("X") == content_hash("X")
    assert content_hash("X") != content_hash("Y")
    # Canonical sha256 hex of UTF-8 bytes (64 lowercase hex chars).
    digest = content_hash("X")
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


# ---------------------------------------------------------------------------
# Grammar bridge smoke test (fails loudly if the checker is moved/renamed)
# ---------------------------------------------------------------------------

def test_grammar_bridge_exposes_working_us_heading_regex():
    assert spec_grammar.US_HEADING_RE.match("### US1 — Foo")


def test_grammar_bridge_exposes_all_canonical_regexes():
    for name in (
        "US_HEADING_RE",
        "FR_ID_RE",
        "SC_ID_RE",
        "EARS_SCENARIO_RE",
        "SECTION_HEADING_RE",
        "NEEDS_CLAR_INLINE_RE",
    ):
        assert getattr(spec_grammar, name) is not None, f"{name} missing from grammar bridge"
