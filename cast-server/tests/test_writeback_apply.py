"""Apply-path tests for the SOLE file-writer (Phase 5, sp4).

``change_request_service.apply_change_request`` is the one and only code path that mutates a
goal's canonical ``refined_requirements.collab.md``. These tests are the acceptance bar for sp4:

* **Accepted addition** → the new element appears at the file tail; **every other byte is
  identical** (the original content survives as a verbatim prefix). The version is bumped via
  ``create_next``, the change summary carries a provenance badge, and the ``applied`` event +
  ``notifications_outbox`` row are written in one apply transaction.
* **Clean modification** (real ``verbatim_locate``) → exactly the located region is replaced;
  prefix and suffix survive byte-for-byte.
* **Conflicted** (a human changed the target region since ``base_version``) → **refused**,
  surfaced (3-way ``ConflictSurface``), file **untouched**; NO auto-merge.
* **Orphaned** (the target quote no longer locates) → **refused**, surfaced, file untouched.
* **Path-scope** (``goal_dir`` outside the allowed root) → **refused**, no crash, no write, no
  DB mutation.
* **Render never mutates** — rerendering the ``.html`` leaves the ``.collab.md`` byte-identical;
  the writeback agent is the only mutator (the FR-007 guard, extended fully in sp5).

DB isolation follows the house pattern: explicit ``db_path`` injection through the service API
plus a ``goal_dir`` under ``tmp_path`` scoped by an injected ``allowed_root`` (no ``GOALS_DIR``
dependency in the apply path).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CAST_SERVER_DIR = REPO_ROOT / "cast-server"
if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))

FILENAME = "refined_requirements.collab.md"


# --------------------------------------------------------------------------- #
# Fixtures / helpers                                                           #
# --------------------------------------------------------------------------- #

def _seed_goal(db_path: Path, slug: str, folder_path: str) -> None:
    from cast_server.db.connection import get_connection

    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) VALUES (?, ?, ?)",
            (slug, "Round-trip goal", folder_path),
        )
        conn.commit()
    finally:
        conn.close()


def _make_goal_dir(tmp_path: Path, content: str, slug: str = "rt-goal") -> Path:
    goal_dir = tmp_path / "goals" / slug
    goal_dir.mkdir(parents=True)
    (goal_dir / FILENAME).write_text(content, encoding="utf-8")
    return goal_dir


def _snapshot(slug: str, content: str, db_path: Path) -> int:
    """Record ``content`` as the goal's base version; return its integer version."""
    from cast_server.services import requirement_version_service

    row = requirement_version_service.create_snapshot(slug, content, db_path=db_path)
    return row["version"]


def _new_change_request(db_path: Path, slug: str, **overrides) -> dict:
    from cast_server.services import change_request_service

    payload = dict(
        kind="addition",
        proposed_body="| FR-099 | A freshly written requirement. | US9 |",
        base_version=1,
        target_quote=None,
        section_hint="Functional Requirements",
        author="cast-high-level-planner",
        author_type="agent",
        origin_phase="planning",
        origin_artifact_path="plan.collab.md",
        status="applied",
    )
    payload.update(overrides)
    return change_request_service.create(slug, db_path=db_path, **payload)


# A frozen, realistic requirements document with a stable FR table to anchor against. FR ids are
# 3+ digits (the landed grammar: ``\bFR-(\d{3,})\b``).
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
_ADDED_ROW = "| FR-099 | A freshly written requirement. | US9 |"


# --------------------------------------------------------------------------- #
# Accepted addition                                                            #
# --------------------------------------------------------------------------- #

def test_addition_applies_at_tail_byte_identical(isolated_db, tmp_path):
    from cast_server.services import change_request_service

    db = isolated_db
    goal_dir = _make_goal_dir(tmp_path, _DOC)
    _seed_goal(db, "rt-goal", str(goal_dir))
    _snapshot("rt-goal", _DOC, db)

    cr = _new_change_request(db, "rt-goal")
    result = change_request_service.apply_change_request(
        cr["id"], goal_dir=goal_dir, allowed_root=tmp_path, db_path=db)

    after = (goal_dir / FILENAME).read_text(encoding="utf-8")
    # The new FR row appears under Functional Requirements (after FR-002, before Out of Scope).
    assert _ADDED_ROW in after
    assert after.index(_ADDED_ROW) < after.index("## Out of Scope")
    # Every other byte is identical: removing the one inserted line reproduces the original.
    assert after.replace(_ADDED_ROW + "\n", "", 1) == _DOC

    assert result["status"] == "applied"
    assert result["applied_version"] == 2                  # base was version 1
    assert result["change_summary"]["counts"]["added"] == 1
    assert result["change_summary"]["counts"]["removed"] == 0
    badge = result["provenance_badge"]
    assert "FR-099" in badge and "cast-high-level-planner" in badge
    assert "plan.collab.md" in badge


def test_addition_writes_applied_event_and_outbox(isolated_db, tmp_path):
    from cast_server.services import change_request_service

    db = isolated_db
    goal_dir = _make_goal_dir(tmp_path, _DOC)
    _seed_goal(db, "rt-goal", str(goal_dir))
    _snapshot("rt-goal", _DOC, db)

    cr = _new_change_request(db, "rt-goal")
    change_request_service.apply_change_request(
        cr["id"], goal_dir=goal_dir, allowed_root=tmp_path, db_path=db)

    # status flipped to applied
    assert change_request_service.get(cr["id"], db_path=db)["status"] == "applied"
    # an `applied` event exists
    events = change_request_service.list_events(cr["id"], db_path=db)
    assert any(e["event_type"] == "applied" for e in events)
    # exactly one outbox row carries the apply provenance badge (the apply-txn FYI)
    outbox = change_request_service.list_outbox(cr["id"], db_path=db)
    badged = [o for o in outbox if "provenance_badge" in o["payload"]]
    assert len(badged) == 1
    assert badged[0]["status"] == "pending"


# --------------------------------------------------------------------------- #
# Clean modification — real verbatim locator                                  #
# --------------------------------------------------------------------------- #

def test_clean_modification_is_surgical(isolated_db, tmp_path):
    from cast_server.services import change_request_service

    db = isolated_db
    goal_dir = _make_goal_dir(tmp_path, _DOC)
    _seed_goal(db, "rt-goal", str(goal_dir))
    _snapshot("rt-goal", _DOC, db)   # base == current → region hash matches → clean

    new_row = "| FR-002 | The system MUST notify on apply AND record provenance. | US2 |"
    cr = _new_change_request(
        db, "rt-goal", kind="modification",
        target_quote="The system MUST notify on apply.",
        proposed_body=new_row, status="proposed")

    result = change_request_service.apply_change_request(
        cr["id"], goal_dir=goal_dir, allowed_root=tmp_path,
        locate=change_request_service.verbatim_locate, db_path=db)

    after = (goal_dir / FILENAME).read_text(encoding="utf-8")
    # Only the FR-002 line changed; prefix (through FR-001) and suffix (Out of Scope) identical.
    assert new_row in after
    assert after.startswith(_DOC[: _DOC.index("| FR-002 |")])
    assert after.endswith(_DOC[_DOC.index("\n\n## Out of Scope"):])
    assert result["change_summary"]["counts"]["modified"] == 1


# --------------------------------------------------------------------------- #
# Conflicted → refused, file untouched                                        #
# --------------------------------------------------------------------------- #

def test_conflicted_refused_file_untouched(isolated_db, tmp_path):
    from cast_server.services import change_request_service

    db = isolated_db
    # Base version froze FR-1 with its ORIGINAL wording...
    base_doc = _DOC
    # ...but a human has since edited FR-001 in the live file (region changed since base).
    head_doc = _DOC.replace(
        "| FR-001 | The system MUST record a proposal. | US1 |",
        "| FR-001 | The system MUST record a proposal AND its provenance. | US1 |")
    goal_dir = _make_goal_dir(tmp_path, head_doc)
    _seed_goal(db, "rt-goal", str(goal_dir))
    _snapshot("rt-goal", base_doc, db)  # base_version 1 holds the OLD FR-001 region

    cr = _new_change_request(
        db, "rt-goal", kind="modification",
        target_quote="FR-001",                     # locates in both base and head, hashes differ
        proposed_body="| FR-001 | clobbering text | US1 |", status="proposed")

    before = (goal_dir / FILENAME).read_text(encoding="utf-8")
    with pytest.raises(change_request_service.WritebackRefused) as exc:
        change_request_service.apply_change_request(
            cr["id"], goal_dir=goal_dir, allowed_root=tmp_path,
            locate=change_request_service.verbatim_locate, db_path=db)

    assert exc.value.verdict == "conflicted"
    assert exc.value.surface["choices"]  # the 3-way resolution surface is offered
    # File untouched, byte-for-byte.
    assert (goal_dir / FILENAME).read_text(encoding="utf-8") == before
    # A conflicted audit row was left (never a silent no-op); status flipped to conflicted.
    events = change_request_service.list_events(cr["id"], db_path=db)
    assert any(e["event_type"] == "conflicted" for e in events)
    assert change_request_service.get(cr["id"], db_path=db)["status"] == "conflicted"


# --------------------------------------------------------------------------- #
# Orphaned → refused, file untouched                                          #
# --------------------------------------------------------------------------- #

def test_orphaned_refused_file_untouched(isolated_db, tmp_path):
    from cast_server.services import change_request_service

    db = isolated_db
    goal_dir = _make_goal_dir(tmp_path, _DOC)
    _seed_goal(db, "rt-goal", str(goal_dir))
    _snapshot("rt-goal", _DOC, db)

    cr = _new_change_request(
        db, "rt-goal", kind="modification",
        target_quote="A requirement that was deleted long ago",   # not in the document
        proposed_body="| FR-9 | never lands |", status="proposed")

    before = (goal_dir / FILENAME).read_text(encoding="utf-8")
    with pytest.raises(change_request_service.WritebackRefused) as exc:
        change_request_service.apply_change_request(
            cr["id"], goal_dir=goal_dir, allowed_root=tmp_path,
            locate=change_request_service.verbatim_locate, db_path=db)

    assert exc.value.verdict == "orphaned"
    assert (goal_dir / FILENAME).read_text(encoding="utf-8") == before
    events = change_request_service.list_events(cr["id"], db_path=db)
    assert any(e["event_type"] == "orphaned" for e in events)


# --------------------------------------------------------------------------- #
# Path-scope → refused, no write, no crash                                     #
# --------------------------------------------------------------------------- #

def test_path_scope_refuses_out_of_tree(isolated_db, tmp_path):
    from cast_server.services import change_request_service

    db = isolated_db
    allowed_root = tmp_path / "root"
    allowed_root.mkdir()
    evil_dir = tmp_path / "evil"            # NOT under allowed_root
    evil_dir.mkdir()
    _seed_goal(db, "rt-goal", str(evil_dir))
    _snapshot("rt-goal", _DOC, db)

    cr = _new_change_request(db, "rt-goal")

    with pytest.raises(change_request_service.WritebackRefused) as exc:
        change_request_service.apply_change_request(
            cr["id"], goal_dir=evil_dir, allowed_root=allowed_root, db_path=db)

    assert exc.value.verdict == "out-of-tree"
    # No file was created under the evil dir, and no apply/conflict event was written.
    assert not (evil_dir / FILENAME).exists()
    events = change_request_service.list_events(cr["id"], db_path=db)
    assert [e for e in events if e["event_type"] in ("applied", "conflicted", "orphaned")] == []


# --------------------------------------------------------------------------- #
# The writer is the ONLY mutator — render leaves the .collab.md byte-identical #
# --------------------------------------------------------------------------- #

def test_render_never_mutates_collab_md(isolated_db, tmp_path):
    from cast_server.services import change_request_service, requirements_render_service

    db = isolated_db
    goal_dir = _make_goal_dir(tmp_path, _DOC)
    _seed_goal(db, "rt-goal", str(goal_dir))
    _snapshot("rt-goal", _DOC, db)

    cr = _new_change_request(db, "rt-goal")
    change_request_service.apply_change_request(
        cr["id"], goal_dir=goal_dir, allowed_root=tmp_path, db_path=db)

    applied = (goal_dir / FILENAME).read_text(encoding="utf-8")
    # Rerendering the HTML reads the .collab.md but must never write it back.
    requirements_render_service.rerender_requirements_html(
        "rt-goal", goals_dir=tmp_path / "goals", db_path=db)
    assert (goal_dir / FILENAME).read_text(encoding="utf-8") == applied


# --------------------------------------------------------------------------- #
# Production wrapper resolves the goal dir end-to-end                          #
# --------------------------------------------------------------------------- #

def test_apply_for_goal_resolves_folder_path(isolated_db, tmp_path):
    from cast_server.services import change_request_service

    db = isolated_db
    goal_dir = _make_goal_dir(tmp_path, _DOC)
    _seed_goal(db, "rt-goal", str(goal_dir))   # folder_path → goal_dir (routed-goal precedent)
    _snapshot("rt-goal", _DOC, db)

    cr = _new_change_request(db, "rt-goal")
    result = change_request_service.apply_for_goal(
        "rt-goal", cr["id"], goals_dir=tmp_path / "goals", db_path=db)

    assert result["status"] == "applied"
    after = (goal_dir / FILENAME).read_text(encoding="utf-8")
    assert after.replace(_ADDED_ROW + "\n", "", 1) == _DOC   # only the new row was inserted
