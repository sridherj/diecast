"""sp3b server-contract tests — the host postMessage bridge's proxied POST body.

Review #5 (T1 B): the host bridge (`static/comment-bridge.js`) proxies each comment a null-origin
srcdoc iframe postMessages it into a per-comment POST to the SAME same-door create endpoint. These
tests pin the SERVER half of that contract independent of any browser:

* the exact body shape the bridge sends — ``{quoted_text, section_hint, body, artifact_ref,
  author_kind}`` — is accepted by ``CreateCommentRequest`` and persists a render-space comment whose
  stored ``artifact_ref`` is the one the bridge supplied;
* ``artifact_ref`` is additive + DEFAULTED — a body WITHOUT it (the requirements composer / a legacy
  agent curl) creates a comment byte-identically to before (``artifact_ref`` NULL = requirements);
* the path-traversal guard rejects a malicious ``artifact_ref`` at the route (422), never reading
  off-tree.

Hermetic FastAPI app + ``TestClient`` over the requirements router, mirroring
``test_requirements_comments_api.py``.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CAST_SERVER_DIR = REPO_ROOT / "cast-server"
if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))


def _seed_goal(db_path: Path, goals_root: Path, slug: str) -> Path:
    from cast_server.db.connection import get_connection

    goal_dir = goals_root / slug
    goal_dir.mkdir(parents=True, exist_ok=True)
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path, phase) VALUES (?, ?, ?, ?)",
            (slug, "Bridge Contract Goal", str(goal_dir), "requirements"),
        )
        conn.commit()
    finally:
        conn.close()
    return goal_dir


@pytest.fixture
def env(isolated_db: Path, monkeypatch, tmp_path):
    pytest.importorskip("cast_server.config")
    from cast_server.db import connection as _connection

    monkeypatch.setattr(_connection, "DB_PATH", isolated_db)

    goals_root = tmp_path / "goals"
    goals_root.mkdir()

    # Point the goal-dir resolvers (used by create_comment's render resolver) at our tmp tree.
    from cast_server.routes import api_artifacts, api_requirements
    from cast_server.services import comment_service, requirements_render_service

    monkeypatch.setattr(api_artifacts, "GOALS_DIR", goals_root)
    monkeypatch.setattr(comment_service, "GOALS_DIR", goals_root)
    monkeypatch.setattr(requirements_render_service, "GOALS_DIR", goals_root, raising=False)

    app = FastAPI()
    app.include_router(api_requirements.router)
    return {
        "client": TestClient(app),
        "db_path": isolated_db,
        "goals_root": goals_root,
    }


def _bridge_body(quoted_text, body, artifact_ref, section_hint=None):
    """The EXACT body shape `static/comment-bridge.js#postOne` builds for each comment."""
    return {
        "quoted_text": quoted_text,
        "section_hint": section_hint,
        "body": body,
        "artifact_ref": artifact_ref,
        "author_kind": "human",
    }


def test_bridge_body_creates_render_space_comment_with_artifact_ref(env):
    """The bridge's per-comment POST body persists a render-space comment keyed to artifact_ref."""
    client, db_path, goals_root = env["client"], env["db_path"], env["goals_root"]
    goal_dir = _seed_goal(db_path, goals_root, "bridge-goal")

    # A served exploration artifact whose container text holds the quote.
    (goal_dir / "exploration").mkdir()
    (goal_dir / "exploration" / "exploration.html").write_text(
        "<!doctype html><html><body><p>The 90/10 hat surfaces the cheapest viable angle.</p>"
        "</body></html>"
    )

    payload = _bridge_body(
        quoted_text="cheapest viable angle",
        body="is this the right framing?",
        artifact_ref="exploration/exploration.html",
    )
    resp = client.post("/api/goals/bridge-goal/requirements/comments", json=payload)
    assert resp.status_code == 201, resp.text
    row = resp.json()

    assert row["anchor_space"] == "render"
    assert row["artifact_ref"] == "exploration/exploration.html"
    assert row["quoted_text"] == "cheapest viable angle"
    assert row["author_kind"] == "human"
    assert row["state"] == "open"


def test_artifact_ref_defaulted_requirements_path_unchanged(env):
    """A body WITHOUT artifact_ref (requirements composer / legacy curl) is byte-compatible:
    artifact_ref stores NULL and the comment anchors against refined_requirements.html."""
    client, db_path, goals_root = env["client"], env["db_path"], env["goals_root"]
    goal_dir = _seed_goal(db_path, goals_root, "reqs-goal")
    (goal_dir / "refined_requirements.html").write_text(
        "<!doctype html><html><body><p>The system MUST converge on zero open comments.</p>"
        "</body></html>"
    )

    # No artifact_ref key at all — the existing requirements contract.
    resp = client.post(
        "/api/goals/reqs-goal/requirements/comments",
        json={"quoted_text": "converge on zero open comments",
              "body": "good", "author_kind": "human"},
    )
    assert resp.status_code == 201, resp.text
    row = resp.json()
    assert row["anchor_space"] == "render"
    assert row["artifact_ref"] is None  # NULL = requirements default
    # And it placed against the requirements render (block_ref resolution ran on that doc).
    assert row["quoted_text"] == "converge on zero open comments"


def test_bridge_body_rejects_traversal_artifact_ref(env):
    """A malicious artifact_ref (path traversal / non-.html / absolute) is 422'd at the route —
    the server never reads off-tree, even though the value arrives from the client."""
    client, db_path, goals_root = env["client"], env["db_path"], env["goals_root"]
    _seed_goal(db_path, goals_root, "guard-goal")

    for bad in ["../../etc/passwd", "../secrets.html", "/etc/passwd.html", "notes.md"]:
        resp = client.post(
            "/api/goals/guard-goal/requirements/comments",
            json=_bridge_body("x quote", "b", bad),
        )
        assert resp.status_code == 422, f"{bad!r} should be rejected, got {resp.status_code}"


def test_per_comment_fanout_each_row_independent(env):
    """The bridge loops per-comment (no batch endpoint). Two POSTs against the same artifact each
    create an independent row carrying the same artifact_ref — the fan-out contract."""
    client, db_path, goals_root = env["client"], env["db_path"], env["goals_root"]
    goal_dir = _seed_goal(db_path, goals_root, "fanout-goal")
    (goal_dir / "exploration").mkdir()
    (goal_dir / "exploration" / "exploration.html").write_text(
        "<!doctype html><html><body><p>alpha angle and beta angle both matter.</p></body></html>"
    )

    ids = []
    for q in ["alpha angle", "beta angle"]:
        r = client.post(
            "/api/goals/fanout-goal/requirements/comments",
            json=_bridge_body(q, "note about " + q, "exploration/exploration.html"),
        )
        assert r.status_code == 201, r.text
        row = r.json()
        assert row["artifact_ref"] == "exploration/exploration.html"
        ids.append(row["id"])

    assert len(set(ids)) == 2  # two independent rows
