"""Pin the same-door version-diff narration store / API / render (Phase 4b-3).

The load-bearing guarantee: the UI can NEVER show a change absent from the deterministic set.
This is structural at three layers — a prompt rule in the agent (4b-2), the **422 all-or-nothing
gate** here (``save_narration`` recomputes ``summarize(diff_blocks(old, new))`` server-side and
rejects any note whose ``(change, heading_or_ref)`` is not a deterministic item), and the
**lookup-only render** here (the panel iterates the deterministic items, so a note with no
matching item renders nothing). FR-024 re-scoped: ``/changes`` ``counts``/``items`` stay
byte-for-byte ``summarize()``; ``narration`` is a sibling key.

Hermetic FastAPI app + ``TestClient`` per the ``test_requirements_comments_api.py`` pattern; the
real diff fixtures (one added / one modified / one removed) supply true narration keys.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from cast_server.db.connection import get_connection
from cast_server.deps import templates
from cast_server.requirements_render import parser
from cast_server.requirements_render.block_diff import diff_blocks, summarize
from cast_server.services import requirement_version_service as version_service
from cast_server.services.requirement_version_service import (
    NarrationValidationError,
    NarrationVersionNotFound,
    get_narration,
    save_narration,
)

SLUG = "narration-test"

_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "refine_requirements_v2"
_BASE_FILE = _FIXTURES / "refined_requirements.collab.md"
_EDIT_FILE = _FIXTURES / "refined_requirements.v2-edit.collab.md"

# The true deterministic keys for the fixture pair (verified against summarize()):
_ADDED_KEY = ("added", "FR-021")
_MODIFIED_KEY = ("modified", "FR-001")


def _note(change: str, heading_or_ref: str, note: str = "a decorating note") -> dict:
    return {"change": change, "heading_or_ref": heading_or_ref, "note": note}


@pytest.fixture
def env(isolated_db: Path, monkeypatch, tmp_path):
    """TestClient over api_requirements with two real version snapshots (base=1, head=2)."""
    from cast_server.db import connection as _connection
    monkeypatch.setattr(_connection, "DB_PATH", isolated_db)

    base_content = _BASE_FILE.read_text(encoding="utf-8")
    edit_content = _EDIT_FILE.read_text(encoding="utf-8")

    goal_dir = tmp_path / SLUG
    goal_dir.mkdir(parents=True, exist_ok=True)
    (goal_dir / "refined_requirements.collab.md").write_text(edit_content, encoding="utf-8")

    conn = get_connection(isolated_db)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) VALUES (?, ?, ?)",
            (SLUG, "Narration test goal", str(goal_dir)),
        )
        conn.commit()
    finally:
        conn.close()

    version_service.create_snapshot(SLUG, base_content, db_path=isolated_db)  # version 1
    version_service.create_snapshot(SLUG, edit_content, db_path=isolated_db)  # version 2

    from cast_server.routes import api_requirements
    app = FastAPI()
    app.include_router(api_requirements.router)
    return {
        "client": TestClient(app),
        "db_path": isolated_db,
        "base_content": base_content,
        "edit_content": edit_content,
    }


def _base_url(slug: str = SLUG) -> str:
    return f"/api/goals/{slug}/requirements"


def _summary(env) -> dict:
    old = parser.parse_requirements(env["base_content"])
    new = parser.parse_requirements(env["edit_content"])
    return summarize(diff_blocks(old, new))


# --------------------------------------------------------------------------- #
# Service: save / get round-trip + upsert                                      #
# --------------------------------------------------------------------------- #

def test_save_get_roundtrip(env):
    db = env["db_path"]
    notes = [_note(*_ADDED_KEY, "FR-021 is the new safety net")]
    saved = save_narration(SLUG, 1, 2, "Tightened the spec.", notes, "cast-refine-requirements",
                           db_path=db)
    assert saved["overview"] == "Tightened the spec."
    assert saved["item_notes"] == notes
    assert saved["created_by"] == "cast-refine-requirements"

    fetched = get_narration(SLUG, 1, 2, db_path=db)
    assert fetched == saved


def test_get_narration_absent_returns_none(env):
    assert get_narration(SLUG, 1, 2, db_path=env["db_path"]) is None


def test_upsert_on_repost_no_duplicate_row(env):
    db = env["db_path"]
    save_narration(SLUG, 1, 2, "first overview", [_note(*_ADDED_KEY)], "agent-a", db_path=db)
    save_narration(SLUG, 1, 2, "second overview", [_note(*_MODIFIED_KEY)], "agent-b", db_path=db)

    conn = get_connection(db)
    try:
        rows = conn.execute(
            "SELECT * FROM version_diff_narrations WHERE goal_slug = ? AND base_version = ? "
            "AND head_version = ?",
            (SLUG, 1, 2),
        ).fetchall()
    finally:
        conn.close()
    assert len(rows) == 1, "re-post must upsert, never duplicate"
    fetched = get_narration(SLUG, 1, 2, db_path=db)
    assert fetched["overview"] == "second overview"
    assert fetched["created_by"] == "agent-b"


# --------------------------------------------------------------------------- #
# Service: all-or-nothing validation                                          #
# --------------------------------------------------------------------------- #

def test_422_on_item_note_not_in_deterministic_set(env):
    db = env["db_path"]
    bad = [_note("added", "FR-999-invented"), _note(*_MODIFIED_KEY)]
    with pytest.raises(NarrationValidationError) as exc:
        save_narration(SLUG, 1, 2, "ov", bad, "agent", db_path=db)
    assert ["added", "FR-999-invented"] in exc.value.offending_keys
    # All-or-nothing: nothing is persisted on a rejected save.
    assert get_narration(SLUG, 1, 2, db_path=db) is None


def test_422_lists_every_offending_key(env):
    db = env["db_path"]
    bad = [_note("added", "FR-999"), _note("removed", "never-removed-this")]
    with pytest.raises(NarrationValidationError) as exc:
        save_narration(SLUG, 1, 2, "ov", bad, "agent", db_path=db)
    keys = exc.value.offending_keys
    assert ["added", "FR-999"] in keys
    assert ["removed", "never-removed-this"] in keys


def test_422_on_overview_over_size_cap(env):
    db = env["db_path"]
    with pytest.raises(NarrationValidationError):
        save_narration(SLUG, 1, 2, "x" * (2 * 1024 + 1), [], "agent", db_path=db)
    assert get_narration(SLUG, 1, 2, db_path=db) is None


def test_422_on_note_over_size_cap(env):
    db = env["db_path"]
    big = [_note(*_ADDED_KEY, "y" * (2 * 1024 + 1))]
    with pytest.raises(NarrationValidationError):
        save_narration(SLUG, 1, 2, "ov", big, "agent", db_path=db)


def test_422_on_more_than_one_note_per_item(env):
    db = env["db_path"]
    dup = [_note(*_ADDED_KEY, "note one"), _note(*_ADDED_KEY, "note two")]
    with pytest.raises(NarrationValidationError):
        save_narration(SLUG, 1, 2, "ov", dup, "agent", db_path=db)


def test_version_not_found_raises(env):
    db = env["db_path"]
    with pytest.raises(NarrationVersionNotFound):
        save_narration(SLUG, 1, 99, "ov", [], "agent", db_path=db)


# --------------------------------------------------------------------------- #
# Route: POST narration + 404/422 semantics                                   #
# --------------------------------------------------------------------------- #

def test_post_narration_valid_200(env):
    client = env["client"]
    body = {"base": 1, "overview": "Tightened the spec.",
            "item_notes": [_note(*_ADDED_KEY, "the new safety net")],
            "created_by": "cast-refine-requirements"}
    resp = client.post(f"{_base_url()}/versions/2/narration", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["overview"] == "Tightened the spec."
    assert data["created_by"] == "cast-refine-requirements"
    # Stamped on the row and readable back.
    assert get_narration(SLUG, 1, 2, db_path=env["db_path"])["created_by"] == "cast-refine-requirements"


def test_post_narration_actor_alias_accepted(env):
    client = env["client"]
    body = {"base": 1, "overview": "ov", "item_notes": [], "actor": "cast-refine-requirements"}
    resp = client.post(f"{_base_url()}/versions/2/narration", json=body)
    assert resp.status_code == 200
    assert resp.json()["created_by"] == "cast-refine-requirements"


def test_post_narration_bad_key_422_echoes_offending(env):
    client = env["client"]
    body = {"base": 1, "overview": "ov", "item_notes": [_note("added", "FR-INVENTED")]}
    resp = client.post(f"{_base_url()}/versions/2/narration", json=body)
    assert resp.status_code == 422
    assert ["added", "FR-INVENTED"] in resp.json()["offending_keys"]


def test_post_narration_unknown_version_404(env):
    client = env["client"]
    body = {"base": 1, "overview": "ov", "item_notes": []}
    resp = client.post(f"{_base_url()}/versions/99/narration", json=body)
    assert resp.status_code == 404


def test_post_narration_unknown_slug_404(env):
    client = env["client"]
    body = {"base": 1, "overview": "ov", "item_notes": []}
    resp = client.post(f"{_base_url('no-such-goal')}/versions/2/narration", json=body)
    assert resp.status_code == 404


# --------------------------------------------------------------------------- #
# /changes: counts/items byte-identical; narration sibling                    #
# --------------------------------------------------------------------------- #

def test_changes_counts_items_byte_identical_with_and_without_narration(env):
    client = env["client"]
    before = client.get(f"{_base_url()}/changes?base=1&head=2")
    assert before.status_code == 200
    before_json = before.json()
    assert before_json["narration"] is None

    save_narration(SLUG, 1, 2, "ov", [_note(*_ADDED_KEY)], "agent", db_path=env["db_path"])

    after = client.get(f"{_base_url()}/changes?base=1&head=2")
    after_json = after.json()

    # counts/items are byte-for-byte identical (FR-024 re-scoped to those keys).
    assert json.dumps(before_json["counts"]) == json.dumps(after_json["counts"])
    assert json.dumps(before_json["items"]) == json.dumps(after_json["items"])
    # The narration sibling is the ONLY addition.
    assert after_json["narration"]["overview"] == "ov"


def test_changes_items_byte_identical_to_raw_summarize(env):
    client = env["client"]
    resp = client.get(f"{_base_url()}/changes?base=1&head=2")
    summary = _summary(env)
    assert json.dumps(resp.json()["counts"]) == json.dumps(summary["counts"])
    assert json.dumps(resp.json()["items"]) == json.dumps(summary["items"])


# --------------------------------------------------------------------------- #
# Fragment render: labelled, lookup-only, autoescaped                         #
# --------------------------------------------------------------------------- #

def _render_panel(env, narration: dict | None) -> str:
    return templates.get_template(
        "fragments/requirements_comments/changes_panel.html"
    ).render(goal_slug=SLUG, base=1, head=2, summary=_summary(env), narration=narration)


def test_panel_renders_overview_labelled_and_matching_note(env):
    narration = {
        "overview": "Tightened the spec for safety.",
        "item_notes": [_note(*_ADDED_KEY, "FR-021 closes the orphan gap")],
    }
    html = _render_panel(env, narration)
    assert "Agent narration" in html
    assert "Tightened the spec for safety." in html
    assert "FR-021 closes the orphan gap" in html


def test_panel_lookup_only_note_with_no_matching_item_renders_nothing(env):
    # A note whose key matches NO deterministic item must render nothing (lookup-only render).
    narration = {
        "overview": "An overview.",
        "item_notes": [_note("added", "FR-PHANTOM", "this note should never appear")],
    }
    html = _render_panel(env, narration)
    assert "this note should never appear" not in html
    # The overview still renders (it is not item-scoped).
    assert "An overview." in html


def test_panel_byte_identical_when_no_narration(env):
    without = _render_panel(env, None)
    # The deterministic panel must be byte-identical to the legacy render when narration is absent.
    legacy = templates.get_template(
        "fragments/requirements_comments/changes_panel.html"
    ).render(goal_slug=SLUG, base=1, head=2, summary=_summary(env))
    assert without == legacy
    assert "diff-narration" not in without


def test_panel_autoescapes_narration_html(env):
    narration = {
        "overview": "<script>alert('xss')</script> & <b>bold</b>",
        "item_notes": [_note(*_ADDED_KEY, "<img src=x onerror=alert(1)>")],
    }
    html = _render_panel(env, narration)
    # Metacharacters are escaped — no raw tag survives (autoescape proof; never innerHTML/| safe).
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "<img src=x" not in html
    assert "&lt;img" in html
