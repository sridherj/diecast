"""Pin the same-door requirements comment API (Phase 4, WP-A / sp1).

THE load-bearing test is the dual-assertion agent-parity test (FR-013): ``POST /comments``
with and without ``HX-Request`` writes the SAME DB row via ONE ``create_comment`` code path;
only the response *shape* differs. The rest pins status-code contracts: relocate→422,
unknown-slug→404, empty/oversize→422, double-resolve→409.

Hermetic FastAPI app + ``TestClient`` per the ``test_api_goals_route.py`` pattern.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from cast_server.db.connection import get_connection
from cast_server.services import comment_service
from cast_server.services import requirement_version_service as version_service

SLUG = "api-comment-test"
CURRENT_FILE_TEXT = "the requirements mention an anchored slice and a second slice"


@pytest.fixture
def env(isolated_db: Path, monkeypatch, tmp_path):
    """TestClient over api_requirements on a hermetic DB + a real goal file on disk."""
    from cast_server.db import connection as _connection
    monkeypatch.setattr(_connection, "DB_PATH", isolated_db)

    # Seed a goal whose folder_path holds a real refined_requirements.collab.md so the
    # displacement detector + relocate substring backstop read real text.
    goal_dir = tmp_path / SLUG
    goal_dir.mkdir(parents=True, exist_ok=True)
    (goal_dir / "refined_requirements.collab.md").write_text(CURRENT_FILE_TEXT, encoding="utf-8")

    conn = get_connection(isolated_db)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) VALUES (?, ?, ?)",
            (SLUG, "API comment test goal", str(goal_dir)),
        )
        conn.commit()
    finally:
        conn.close()
    version_service.create_snapshot(SLUG, CURRENT_FILE_TEXT, db_path=isolated_db)

    from cast_server.routes import api_requirements
    app = FastAPI()
    app.include_router(api_requirements.router)
    return {"client": TestClient(app), "db_path": isolated_db, "goal_dir": goal_dir}


def _base(slug: str = SLUG) -> str:
    return f"/api/goals/{slug}/requirements"


# --------------------------------------------------------------------------- #
# THE dual-assertion agent-parity test (FR-013)                                #
# --------------------------------------------------------------------------- #

def test_post_comments_same_row_json_vs_htmx(env):
    """JSON and HTMX POSTs write structurally identical rows — one code path, two shapes."""
    client, db_path = env["client"], env["db_path"]
    payload = {"quoted_text": "anchored slice", "section_hint": "Intro", "body": "clarify please"}

    # JSON branch → 201 + the row.
    json_resp = client.post(f"{_base()}/comments", json={**payload, "author_kind": "human"})
    assert json_resp.status_code == 201
    json_row = json_resp.json()
    assert json_row["author_kind"] == "human"

    # HTMX branch → HTML thread-item fragment (same create path).
    hx_resp = client.post(
        f"{_base()}/comments",
        json={**payload, "author_kind": "agent"},
        headers={"HX-Request": "true"},
    )
    assert hx_resp.status_code == 200
    assert "text/html" in hx_resp.headers["content-type"]
    assert "comment-thread-item" in hx_resp.text
    assert "agent" in hx_resp.text  # the author_kind badge

    # Read both rows back via the service: identical modulo id / author_kind / timestamps.
    rows = comment_service.list_comments(SLUG, db_path=db_path)
    assert len(rows) == 2
    a, b = rows
    ignore = {"id", "author_kind", "created_at", "updated_at", "displaced"}
    assert {k: v for k, v in a.items() if k not in ignore} == \
           {k: v for k, v in b.items() if k not in ignore}
    # author_kind is the ONLY differing input.
    assert {a["author_kind"], b["author_kind"]} == {"human", "agent"}


def test_json_post_carries_displaced_in_list(env):
    """An open comment whose quote is absent from the current file reads displaced=True."""
    client, db_path = env["client"], env["db_path"]
    client.post(f"{_base()}/comments", json={"quoted_text": "anchored slice", "body": "x"})
    client.post(f"{_base()}/comments", json={"quoted_text": "vanished slice", "body": "y"})

    resp = client.get(f"{_base()}/comments")
    assert resp.status_code == 200
    by_quote = {c["quoted_text"]: c for c in resp.json()["comments"]}
    assert by_quote["anchored slice"]["displaced"] is False
    assert by_quote["vanished slice"]["displaced"] is True


def test_get_comments_htmx_returns_tray(env):
    client = env["client"]
    client.post(f"{_base()}/comments", json={"quoted_text": "anchored slice", "body": "x"})
    resp = client.get(f"{_base()}/comments", headers={"HX-Request": "true"})
    assert resp.status_code == 200
    assert "comment-tray" in resp.text


# --------------------------------------------------------------------------- #
# Transition parity (resolve / reopen / orphan / relocate)                     #
# --------------------------------------------------------------------------- #

def _new_comment(client, quoted="anchored slice") -> int:
    return client.post(f"{_base()}/comments", json={"quoted_text": quoted, "body": "b"}).json()["id"]


@pytest.mark.parametrize("action", ["resolve", "orphan"])
def test_transition_json_and_htmx_parity(env, action):
    client = env["client"]
    cid_json = _new_comment(client)
    cid_hx = _new_comment(client)

    j = client.post(f"{_base()}/comments/{cid_json}/{action}")
    assert j.status_code == 200 and j.headers["content-type"].startswith("application/json")

    h = client.post(f"{_base()}/comments/{cid_hx}/{action}", headers={"HX-Request": "true"})
    assert h.status_code == 200 and "comment-thread-item" in h.text


def test_reopen_after_resolve(env):
    client = env["client"]
    cid = _new_comment(client)
    client.post(f"{_base()}/comments/{cid}/resolve")
    resp = client.post(f"{_base()}/comments/{cid}/reopen")
    assert resp.status_code == 200
    assert resp.json()["state"] == "open"


def test_relocate_success_substring_of_current_file(env):
    client = env["client"]
    cid = _new_comment(client, quoted="anchored slice")
    resp = client.post(
        f"{_base()}/comments/{cid}/relocate",
        json={"new_quoted_text": "second slice", "new_section_hint": "Body"},
    )
    assert resp.status_code == 200
    assert resp.json()["quoted_text"] == "second slice"


# --------------------------------------------------------------------------- #
# Status-code contracts                                                        #
# --------------------------------------------------------------------------- #

def test_relocate_non_substring_returns_422_no_change(env):
    client, db_path = env["client"], env["db_path"]
    cid = _new_comment(client, quoted="anchored slice")
    resp = client.post(
        f"{_base()}/comments/{cid}/relocate",
        json={"new_quoted_text": "text not in the file at all"},
    )
    assert resp.status_code == 422
    # No row change — the quote is unchanged.
    assert comment_service.get_comment(cid, db_path=db_path)["quoted_text"] == "anchored slice"


def test_unknown_slug_404_on_every_endpoint(env):
    client = env["client"]
    ghost = "/api/goals/does-not-exist/requirements"
    assert client.get(f"{ghost}/comments").status_code == 404
    assert client.post(f"{ghost}/comments", json={"quoted_text": "x", "body": "y"}).status_code == 404
    assert client.post(f"{ghost}/comments/1/resolve").status_code == 404
    assert client.post(f"{ghost}/comments/1/reopen").status_code == 404
    assert client.post(f"{ghost}/comments/1/orphan").status_code == 404
    assert client.post(f"{ghost}/comments/1/relocate", json={"new_quoted_text": "z"}).status_code == 404
    assert client.get(f"{ghost}/versions").status_code == 404


def test_empty_quoted_text_returns_422(env):
    client = env["client"]
    resp = client.post(f"{_base()}/comments", json={"quoted_text": "   ", "body": "y"})
    assert resp.status_code == 422


def test_empty_body_returns_422(env):
    client = env["client"]
    resp = client.post(f"{_base()}/comments", json={"quoted_text": "anchored slice", "body": ""})
    assert resp.status_code == 422


def test_oversize_field_returns_422(env):
    client = env["client"]
    huge = "x" * (10 * 1024 + 1)
    resp = client.post(f"{_base()}/comments", json={"quoted_text": huge, "body": "y"})
    assert resp.status_code == 422


def test_double_resolve_returns_409(env):
    client = env["client"]
    cid = _new_comment(client)
    assert client.post(f"{_base()}/comments/{cid}/resolve").status_code == 200
    assert client.post(f"{_base()}/comments/{cid}/resolve").status_code == 409


def test_resolve_unknown_comment_returns_404(env):
    client = env["client"]
    assert client.post(f"{_base()}/comments/999999/resolve").status_code == 404


# --------------------------------------------------------------------------- #
# Versions list + convergence metadata                                         #
# --------------------------------------------------------------------------- #

def test_versions_list_reports_convergence(env):
    client = env["client"]
    # No open comments yet → converged.
    resp = client.get(f"{_base()}/versions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["open_comment_count"] == 0
    assert data["convergence"] == "converged"
    assert len(data["versions"]) == 1  # the seeded snapshot

    # An open comment flips it unconverged.
    _new_comment(client)
    data2 = client.get(f"{_base()}/versions").json()
    assert data2["open_comment_count"] == 1
    assert data2["convergence"] == "unconverged"


# --------------------------------------------------------------------------- #
# POST /versions + GET /versions/{n} (sp3)                                      #
# --------------------------------------------------------------------------- #

def test_post_versions_returns_contract_dict(env):
    """POST snapshots from the on-disk file and returns the create_next contract dict (JSON)."""
    client = env["client"]
    resp = client.post(f"{_base()}/versions")
    assert resp.status_code == 200
    data = resp.json()
    assert set(data) >= {"version", "convergence", "open_comments", "displaced_comment_ids"}
    assert data["convergence"] == "converged"  # no open comments seeded
    assert data["displaced_comment_ids"] == []


def test_post_versions_unconverged_with_open_comment(env):
    client = env["client"]
    _new_comment(client)  # open comment quoting text present in the current file
    data = client.post(f"{_base()}/versions").json()
    assert data["convergence"] == "unconverged"
    assert len(data["open_comments"]) == 1


def test_post_versions_missing_file_returns_409(env):
    """The server READS the goal file; if it is absent there is nothing to snapshot → 409."""
    client = env["client"]
    (env["goal_dir"] / "refined_requirements.collab.md").unlink()
    resp = client.post(f"{_base()}/versions")
    assert resp.status_code == 409


def test_get_version_returns_row_and_comments_as_of(env):
    client = env["client"]
    cid = _new_comment(client)  # left on the current (v1) snapshot
    resp = client.get(f"{_base()}/versions/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"]["version"] == 1
    ids = [c["id"] for c in data["comments"]]
    assert cid in ids
    as_of = next(c["state_as_of"] for c in data["comments"] if c["id"] == cid)
    assert as_of == "open"


def test_get_unknown_version_returns_404(env):
    assert env["client"].get(f"{_base()}/versions/99").status_code == 404


def test_versions_endpoints_unknown_slug_404(env):
    client = env["client"]
    ghost = "/api/goals/does-not-exist/requirements"
    assert client.post(f"{ghost}/versions").status_code == 404
    assert client.get(f"{ghost}/versions/1").status_code == 404
