"""Tests for `/preso/review/{goal_slug}` route (sp9).

Verifies the read-only route serves an existing presentation review
artifact and returns a clear 404 when the artifact is missing.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CAST_SERVER_DIR = REPO_ROOT / "cast-server"

# The package lives at cast-server/cast_server/. The parent directory
# (cast-server/) must be on sys.path so ``import cast_server.*`` works.
if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))


@pytest.fixture
def client(monkeypatch, tmp_path):
    pytest.importorskip("cast_server.config")
    monkeypatch.setattr("cast_server.config.GOALS_DIR", Path(tmp_path))
    from cast_server.routes import pages
    monkeypatch.setattr(pages._config, "GOALS_DIR", Path(tmp_path))
    app = FastAPI()
    app.include_router(pages.router)
    return TestClient(app), tmp_path


def test_preso_review_present(client):
    test_client, tmp_path = client
    goal = tmp_path / "g1" / "presentation"
    goal.mkdir(parents=True)
    (goal / "review.html").write_text("<html><body>HELLO</body></html>")

    r = test_client.get("/preso/review/g1")
    assert r.status_code == 200
    assert "HELLO" in r.text


def test_preso_review_missing_returns_404(client):
    test_client, _ = client
    r = test_client.get("/preso/review/no-such-goal")
    assert r.status_code == 404
    assert "No presentation review" in r.text
