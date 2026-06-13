"""Tests for Phase 4 sp4a — diff-view wiring (route + ``/changes`` + version toggle).

Three surfaces under test:

* ``requirements_render.diff_render.render_diff`` — the pure tracked-changes renderer, pinned
  by a byte golden (``diff_v1_v2.html``) plus structural assertions over the fixture pair.
* ``GET /goals/{slug}/render/diff`` (``routes/pages.py``) — slug-validated, version-defaulted,
  served fresh; ``<2 versions`` → a plain card (200), ``base >= head`` → 422.
* ``GET …/requirements/changes`` (``routes/api_requirements.py``) — FR-017's same-door
  surface: ``summarize()`` JSON header-less, the "What changed" panel fragment on ``HX-Request``.

The diff view is derived and NEVER written to the goal folder (FR-011) — these tests render it
straight from two DB version snapshots. The transient ``id="diff-{n}"`` anchors live ONLY in
this throwaway view; the canonical render's zero-``id`` contract is checked separately.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CAST_SERVER_DIR = REPO_ROOT / "cast-server"
if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))

from cast_server.requirements_render import parse_requirements_file  # noqa: E402
from cast_server.requirements_render.block_diff import diff_blocks, summarize  # noqa: E402
from cast_server.requirements_render.diff_render import render_diff  # noqa: E402

FIXTURE_DIR = CAST_SERVER_DIR / "tests" / "fixtures" / "refine_requirements_v2"
V1_FIXTURE = FIXTURE_DIR / "refined_requirements.collab.md"
V2_FIXTURE = FIXTURE_DIR / "refined_requirements.v2-edit.collab.md"

GOLDEN_DIR = Path(__file__).resolve().parent / "golden" / "requirements_render"


def _check_golden(name: str, html: str) -> None:
    """Byte-compare ``html`` against ``golden/requirements_render/{name}.html``.

    ``UPDATE_GOLDENS=1`` regenerates the golden instead of asserting (the documented
    intentional-change path) — mirrors ``test_requirements_renderer._check_golden``.
    """
    path = GOLDEN_DIR / f"{name}.html"
    if os.environ.get("UPDATE_GOLDENS"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
        return
    assert path.is_file(), (
        f"missing golden {path} — regenerate with `UPDATE_GOLDENS=1 pytest "
        f"tests/test_diff_render.py`"
    )
    assert html == path.read_text(encoding="utf-8"), (
        f"golden mismatch for {name!r}. If intentional, regenerate with UPDATE_GOLDENS=1 "
        f"and review the diff; otherwise diff_render drifted."
    )


def _render_fixture_pair() -> str:
    old = parse_requirements_file(V1_FIXTURE)
    new = parse_requirements_file(V2_FIXTURE)
    return render_diff(old, new, base_version=1, head_version=2).html


# --------------------------------------------------------------------------- #
# Pure renderer — golden + structural assertions                              #
# --------------------------------------------------------------------------- #


def test_diff_golden_fixture_pair():
    """The tracked-changes render of the fixture pair matches its byte golden."""
    _check_golden("diff_v1_v2", _render_fixture_pair())


def test_diff_structural_treatments():
    """Each change bucket carries its class: added → ``diff-added``; modified shows the new
    body + a ``<del>`` of the prior; removed renders struck (``diff-removed``)."""
    html = _render_fixture_pair()
    assert 'class="diff-block diff-added"' in html
    assert 'class="diff-block diff-modified"' in html
    assert 'class="diff-block diff-removed"' in html
    # modified shows the prior body inside a <del> disclosure.
    assert "<del>" in html and "</del>" in html
    # The added FR-021 and the modified FR-001 are both labelled in the spine.
    assert "FR-021" in html
    assert "FR-001" in html


def test_diff_panel_counts_match_summarize():
    """The panel's ``+N · ~N · −N`` line equals ``summarize()`` counts."""
    old = parse_requirements_file(V1_FIXTURE)
    new = parse_requirements_file(V2_FIXTURE)
    counts = summarize(diff_blocks(old, new))["counts"]
    assert counts == {"added": 1, "modified": 1, "removed": 1, "unchanged": 52}
    html = render_diff(old, new, base_version=1, head_version=2).html
    expected = (
        f"+{counts['added']} added &middot; ~{counts['modified']} modified "
        f"&middot; &minus;{counts['removed']} removed"
    )
    assert expected in html


def test_diff_panel_anchors_exist():
    """Every panel ``#diff-{n}`` link targets an ``id="diff-{n}"`` that exists in the HTML."""
    html = _render_fixture_pair()
    ids = set(re.findall(r'id="(diff-\d+)"', html))
    anchors = set(re.findall(r'href="#(diff-\d+)"', html))
    assert anchors, "expected the panel to link at least one changed block"
    assert anchors.issubset(ids), f"dangling panel anchors: {anchors - ids}"


def test_diff_render_unparseable_side_is_card_not_crash():
    """A ``None`` side (unparseable archived snapshot) → a 'cannot diff' card, never a raise."""
    new = parse_requirements_file(V2_FIXTURE)
    result = render_diff(None, new, base_version=1, head_version=2)
    assert "Cannot diff" in result.html
    assert result.warnings  # surfaced, never silent


# --------------------------------------------------------------------------- #
# Route: GET /goals/{slug}/render/diff                                         #
# --------------------------------------------------------------------------- #


def _seed_goal(db_path: Path, slug: str) -> None:
    from cast_server.db.connection import get_connection

    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) VALUES (?, ?, ?)",
            (slug, "Diff Goal", slug),
        )
        conn.commit()
    finally:
        conn.close()


def _seed_versions(db_path: Path, slug: str, *, n: int) -> None:
    """Snapshot ``n`` versions (1 = v1 fixture only; 2 = v1 then v2-edit)."""
    from cast_server.services import requirement_version_service as vsvc

    vsvc.create_snapshot(slug, V1_FIXTURE.read_text(encoding="utf-8"), db_path=db_path)
    if n >= 2:
        vsvc.create_snapshot(slug, V2_FIXTURE.read_text(encoding="utf-8"), db_path=db_path)


@pytest.fixture
def pages_client(isolated_db, monkeypatch):
    """TestClient over the pages router on a hermetic DB (route reads versions from the DB)."""
    from cast_server.db import connection as _connection
    monkeypatch.setattr(_connection, "DB_PATH", isolated_db)

    from cast_server.routes import pages
    app = FastAPI()
    app.include_router(pages.router)
    return TestClient(app), isolated_db


def test_diff_route_valid_pair_200(pages_client):
    client, db_path = pages_client
    _seed_goal(db_path, "two")
    _seed_versions(db_path, "two", n=2)

    r = client.get("/goals/two/render/diff")
    assert r.status_code == 200
    assert "diff-changed-panel" in r.text
    assert 'class="diff-block diff-added"' in r.text  # tracked changes present
    assert "FR-021" in r.text


def test_diff_route_fewer_than_two_versions_card(pages_client):
    client, db_path = pages_client
    _seed_goal(db_path, "one")
    _seed_versions(db_path, "one", n=1)

    r = client.get("/goals/one/render/diff")
    assert r.status_code == 200
    assert "No prior version to compare" in r.text


def test_diff_route_base_ge_head_422(pages_client):
    client, db_path = pages_client
    _seed_goal(db_path, "rng")
    _seed_versions(db_path, "rng", n=2)

    r = client.get("/goals/rng/render/diff?base=2&head=1")
    assert r.status_code == 422


def test_diff_route_unknown_slug_404(pages_client):
    client, _ = pages_client
    r = client.get("/goals/ghost/render/diff")
    assert r.status_code == 404


def test_diff_route_not_written_to_disk(pages_client, tmp_path):
    """The diff view is derived — the route must not create any file artifact."""
    client, db_path = pages_client
    _seed_goal(db_path, "fresh")
    _seed_versions(db_path, "fresh", n=2)

    before = set(tmp_path.rglob("*"))
    client.get("/goals/fresh/render/diff")
    assert set(tmp_path.rglob("*")) == before  # no goal-folder write


# --------------------------------------------------------------------------- #
# Route: GET …/requirements/changes (negotiated)                              #
# --------------------------------------------------------------------------- #


@pytest.fixture
def api_client(isolated_db, monkeypatch):
    """TestClient over the api_requirements router on a hermetic DB."""
    from cast_server.db import connection as _connection
    monkeypatch.setattr(_connection, "DB_PATH", isolated_db)

    from cast_server.routes import api_requirements
    app = FastAPI()
    app.include_router(api_requirements.router)
    return TestClient(app), isolated_db


def _changes_url(slug: str) -> str:
    return f"/api/goals/{slug}/requirements/changes"


def test_changes_json_matches_summarize(api_client):
    client, db_path = api_client
    _seed_goal(db_path, "g")
    _seed_versions(db_path, "g", n=2)

    r = client.get(_changes_url("g"))
    assert r.status_code == 200
    assert "application/json" in r.headers["content-type"]
    payload = r.json()

    old = parse_requirements_file(V1_FIXTURE)
    new = parse_requirements_file(V2_FIXTURE)
    summary = summarize(diff_blocks(old, new))
    # FR-024 re-scoped (Phase 4b-3): `counts`/`items` stay byte-for-byte `summarize()`; the
    # `narration` sibling key is the only addition (None when no narration was posted).
    assert payload["counts"] == summary["counts"]
    assert payload["items"] == summary["items"]
    assert payload["narration"] is None


def test_changes_htmx_returns_panel_fragment(api_client):
    client, db_path = api_client
    _seed_goal(db_path, "g")
    _seed_versions(db_path, "g", n=2)

    r = client.get(_changes_url("g"), headers={"HX-Request": "true"})
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "diff-changed-panel" in r.text
    assert "What changed" in r.text
    assert "+1 added" in r.text


def test_changes_base_ge_head_422(api_client):
    client, db_path = api_client
    _seed_goal(db_path, "g")
    _seed_versions(db_path, "g", n=2)

    r = client.get(_changes_url("g"), params={"base": 2, "head": 1})
    assert r.status_code == 422


def test_changes_unknown_slug_404(api_client):
    client, _ = api_client
    r = client.get(_changes_url("ghost"))
    assert r.status_code == 404


# --------------------------------------------------------------------------- #
# Canonical render: zero-id contract + toggle visibility                      #
# --------------------------------------------------------------------------- #


def test_canonical_render_stays_zero_id_with_toggle():
    """The version toggle adds NO ``id=`` to the canonical render — the diff ids are
    diff-view only. The toggle links to the diff page when ≥2 versions exist."""
    from cast_server.requirements_render import parse_requirements
    from cast_server.requirements_render.renderer import render_requirements

    parsed = parse_requirements(V1_FIXTURE.read_text(encoding="utf-8"))
    html = render_requirements(parsed, version=2, goal_slug="demo", version_count=2).html

    # The rendered <nav> markup — distinct from the `.version-toggle {` CSS rule.
    assert '<nav class="version-toggle"' in html
    assert "/goals/demo/render/diff" in html
    assert "Changes since v1" in html
    # The thin-spine contract: no element id= anywhere in the canonical render.
    assert "id=" not in html


def test_canonical_render_no_toggle_with_single_version():
    """One version ⇒ no toggle (nothing to compare against)."""
    from cast_server.requirements_render import parse_requirements
    from cast_server.requirements_render.renderer import render_requirements

    parsed = parse_requirements(V1_FIXTURE.read_text(encoding="utf-8"))
    html = render_requirements(parsed, version=1, goal_slug="demo", version_count=1).html
    assert '<nav class="version-toggle"' not in html
