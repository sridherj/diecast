"""Render-space comment anchoring (refine-req-v3 sp2 — the crux move).

Pins the render-space resolver + the creation path + render-space displacement + the one-time
migration. The load-bearing contract across all of them: a comment's lifecycle runs against the
SERVED render's container text (the same ``container_text_index`` space the maker gate walks), with
a server-resolved ``block_ref`` bridge to canonical source space — and a ``block_ref`` of ``None``
on a ref-less render is SUCCESS, never an unplaced miss (plan-review Decision #1).

Branch coverage mirrors the 1b dry-run's miss vocabulary: in-block (unique ref), cross-boundary,
decoration-spanning, ref-less (no anchor label → NULL by construction), and not-on-render.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from cast_server.db.connection import get_connection, init_db
from cast_server.requirements_render.comment_anchor import (
    RENDER_MISS_CROSS_BOUNDARY,
    RENDER_MISS_DECORATION,
    RENDER_MISS_NO_ANCHOR_LABEL,
    RENDER_NOT_ON_PAGE,
    resolve_render_anchor,
)
from cast_server.requirements_render.maker_gate import container_text_index
from cast_server.services import comment_service
from cast_server.services import requirement_version_service as version_service

SLUG = "render-anchor-test"

# A served maker render: a `.rr-document` with a hero (decoration, no unit), a `.rr-unit` user
# story, two ref-bearing FR `<li>` units, and ONE ref-less `<li>` unit (a Not-now bullet with zero
# anchor labels — the ref-less render branch in miniature).
RENDER_HTML = """\
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Export Scheduler</title></head>
<body data-goal-slug="render-anchor-test">
<main class="rr-document">
<h1>Export Scheduler</h1>
<section class="rr-unit">
<h3>US1 — nightly cadence</h3>
<p>As a user I want a recurring nightly export.</p>
</section>
<ul>
<li><strong>FR-001</strong> The system must export nightly and validate it before saving.</li>
<li><strong>FR-002</strong> The system shall run on a fixed schedule.</li>
<li>Ad-hoc one-off exports triggered manually outside any schedule.</li>
</ul>
</main>
<script src="/static/requirements_comments.js" defer></script>
</body>
</html>
"""

_INBLOCK_QUOTE = "The system must export nightly and validate it before saving."
_REFLESS_QUOTE = "Ad-hoc one-off exports triggered manually outside any schedule."
_DECORATION_QUOTE = "Export Scheduler"
_ABSENT_QUOTE = "this phrase appears on no render anywhere"


def _cross_boundary_quote() -> str:
    """A verbatim slice of the document concat that straddles the FR-001→FR-002 unit boundary —
    present in ``document_text`` but contained within neither unit's own text slice."""
    idx = container_text_index(RENDER_HTML)
    units = idx.units()
    fr1 = next(u for u in units if "FR-001" in u.text)
    fr2 = next(u for u in units if "FR-002" in u.text)
    assert fr1.end <= fr2.start  # FR-001 precedes FR-002 in document order
    return idx.document_text[fr1.end - 15:fr2.start + 15]


# ======================================================================================
# Render-space resolver — one fixture per miss class (the productionized 1b dry-run)
# ======================================================================================

def test_resolve_in_block_quote_yields_unique_block_ref():
    anchor = resolve_render_anchor(RENDER_HTML, _INBLOCK_QUOTE)
    assert anchor.placed is True
    assert anchor.in_unit is True
    assert anchor.block_ref == "FR-001"
    assert anchor.miss_class is None


def test_resolve_ref_less_unit_is_null_by_construction_success():
    """A quote inside a unit container with ZERO anchor labels → block_ref NULL, but PLACED and
    in_unit: a SUCCESS (Decision #1), tagged no-anchor-label — never a failure."""
    anchor = resolve_render_anchor(RENDER_HTML, _REFLESS_QUOTE)
    assert anchor.placed is True
    assert anchor.in_unit is True
    assert anchor.block_ref is None
    assert anchor.miss_class == RENDER_MISS_NO_ANCHOR_LABEL


def test_resolve_decoration_spanning_is_null_outside_every_unit():
    anchor = resolve_render_anchor(RENDER_HTML, _DECORATION_QUOTE)
    assert anchor.placed is True
    assert anchor.in_unit is False
    assert anchor.block_ref is None
    assert anchor.miss_class == RENDER_MISS_DECORATION


def test_resolve_cross_boundary_never_guesses_a_ref():
    anchor = resolve_render_anchor(RENDER_HTML, _cross_boundary_quote())
    assert anchor.placed is True
    assert anchor.block_ref is None
    assert anchor.miss_class == RENDER_MISS_CROSS_BOUNDARY


def test_resolve_quote_absent_from_render_is_not_placed():
    anchor = resolve_render_anchor(RENDER_HTML, _ABSENT_QUOTE)
    assert anchor.placed is False
    assert anchor.block_ref is None
    assert anchor.miss_class == RENDER_NOT_ON_PAGE


def test_resolve_empty_quote_is_not_placed():
    anchor = resolve_render_anchor(RENDER_HTML, "")
    assert anchor.placed is False
    assert anchor.block_ref is None


# ======================================================================================
# Creation path — block_ref resolved server-side; anchor_space='render'
# ======================================================================================

@pytest.fixture
def db_path(tmp_path) -> Path:
    """Fresh tmp DB with a goal row + a current snapshot (so create resolves version=1)."""
    path = tmp_path / "render_anchor.db"
    init_db(path)
    conn = get_connection(path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) VALUES (?, ?, ?)",
            (SLUG, "Render anchor test goal", str(tmp_path / SLUG)),
        )
        conn.commit()
    finally:
        conn.close()
    version_service.create_snapshot(SLUG, "the requirements body", db_path=path)
    return path


def test_create_resolves_block_ref_and_sets_render_space(db_path):
    row = comment_service.create_comment(
        SLUG, _INBLOCK_QUOTE, None, "clarify", "alice",
        db_path=db_path, served_render_html=RENDER_HTML,
    )
    assert row["anchor_space"] == "render"
    assert row["block_ref"] == "FR-001"
    # The served artifact context rides the created event for forensics (no new column).
    events = comment_service.get_comment_events(row["id"], db_path=db_path)
    created = next(e for e in events if e["event_type"] == "created")
    import json
    payload = json.loads(created["payload"])
    assert payload["anchor_space"] == "render"
    assert payload["block_ref"] == "FR-001"


def test_create_ref_less_render_stores_null_block_ref_as_success(db_path):
    row = comment_service.create_comment(
        SLUG, _REFLESS_QUOTE, None, "note", "alice",
        db_path=db_path, served_render_html=RENDER_HTML,
    )
    assert row["anchor_space"] == "render"
    assert row["block_ref"] is None  # ref-less → NULL, stored as success
    # A ref-less NULL comment is NOT displaced — it placed on the render.
    rows = comment_service.list_comments(SLUG, db_path=db_path, render_text=container_text_index(RENDER_HTML).document_text)
    assert {r["id"]: r for r in rows}[row["id"]]["displaced"] is False


# ======================================================================================
# Trust boundary — block_ref is server-resolved, NEVER accepted from the client
# ======================================================================================

def _route_env(isolated_db: Path, tmp_path, monkeypatch):
    from cast_server.db import connection as _connection
    monkeypatch.setattr(_connection, "DB_PATH", isolated_db)
    goal_dir = tmp_path / SLUG
    goal_dir.mkdir(parents=True, exist_ok=True)
    (goal_dir / "refined_requirements.html").write_text(RENDER_HTML, encoding="utf-8")
    conn = get_connection(isolated_db)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) VALUES (?, ?, ?)",
            (SLUG, "Render anchor route goal", str(goal_dir)),
        )
        conn.commit()
    finally:
        conn.close()
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from cast_server.routes import api_requirements
    app = FastAPI()
    app.include_router(api_requirements.router)
    return TestClient(app)


def test_create_ignores_spoofed_block_ref_in_body(isolated_db, tmp_path, monkeypatch):
    """A POST body carrying a bogus ``block_ref`` is ignored — the server resolves its own from the
    served render (trust boundary: a spoofed ref would mis-route a future change-request)."""
    client = _route_env(isolated_db, tmp_path, monkeypatch)
    resp = client.post(
        f"/api/goals/{SLUG}/requirements/comments",
        json={"quoted_text": _INBLOCK_QUOTE, "body": "x", "block_ref": "FR-999-SPOOFED"},
    )
    assert resp.status_code == 201
    row = resp.json()
    # The server-resolved ref wins; the spoofed value never lands.
    assert row["block_ref"] == "FR-001"
    assert row["anchor_space"] == "render"


# ======================================================================================
# Displacement — re-targets the served render; missing render falls back to source, no crash
# ======================================================================================

def test_render_space_displacement_against_served_render(db_path):
    render_text = container_text_index(RENDER_HTML).document_text
    present = comment_service.create_comment(
        SLUG, _INBLOCK_QUOTE, None, "b", "u", db_path=db_path, served_render_html=RENDER_HTML)
    absent = comment_service.create_comment(
        SLUG, _ABSENT_QUOTE, None, "b", "u", db_path=db_path, served_render_html=RENDER_HTML)
    rows = comment_service.list_comments(SLUG, db_path=db_path, render_text=render_text)
    by_id = {r["id"]: r for r in rows}
    assert by_id[present["id"]]["displaced"] is False
    assert by_id[absent["id"]]["displaced"] is True


def test_render_space_displacement_missing_render_falls_back_to_source(db_path, tmp_path):
    # No served render on disk → render-space displacement degrades to the SOURCE check (never crash).
    goal_dir = tmp_path / SLUG
    goal_dir.mkdir(parents=True, exist_ok=True)
    (goal_dir / "refined_requirements.collab.md").write_text(
        "the source still mentions a kept slice", encoding="utf-8")
    present = comment_service.create_comment(
        SLUG, "kept slice", None, "b", "u", db_path=db_path, served_render_html="")
    absent = comment_service.create_comment(
        SLUG, "vanished slice", None, "b", "u", db_path=db_path, served_render_html="")
    rows = comment_service.list_comments(SLUG, db_path=db_path)  # no seam → on-disk lookup
    by_id = {r["id"]: r for r in rows}
    assert by_id[present["id"]]["displaced"] is False
    assert by_id[absent["id"]]["displaced"] is True


# ======================================================================================
# One-time idempotent migration
# ======================================================================================

def _seed_source_comment(db_path: Path, quoted_text: str) -> int:
    """Insert an OPEN 'source'-space comment directly (a pre-v3 / pre-migration row)."""
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO requirement_comments "
            "(goal_slug, version, quoted_text, section_hint, body, state, author, author_kind, "
            " anchor_space, created_at) "
            "VALUES (?, 1, ?, NULL, 'b', 'open', 'u', 'human', 'source', '2026-06-12T00:00:00+00:00')",
            (SLUG, quoted_text),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def _event_count(db_path: Path, comment_id: int) -> int:
    return len(comment_service.get_comment_events(comment_id, db_path=db_path))


def test_migration_flips_placeable_backfills_ref_leaves_rest(db_path):
    placeable = _seed_source_comment(db_path, _INBLOCK_QUOTE)        # → render, FR-001
    ref_less = _seed_source_comment(db_path, _REFLESS_QUOTE)         # → render, NULL (success)
    non_placing = _seed_source_comment(db_path, _ABSENT_QUOTE)       # → stays source, badged

    summary = comment_service.migrate_comments_to_render_space(
        SLUG, db_path=db_path, served_render_html=RENDER_HTML)
    assert summary == {"examined": 3, "flipped": 2, "ref_less_null": 1, "stayed_source": 1}

    by_id = {r["id"]: r for r in comment_service.list_comments(
        SLUG, db_path=db_path, render_text=container_text_index(RENDER_HTML).document_text)}
    assert by_id[placeable]["anchor_space"] == "render"
    assert by_id[placeable]["block_ref"] == "FR-001"
    assert by_id[ref_less]["anchor_space"] == "render"
    assert by_id[ref_less]["block_ref"] is None
    # The non-placing comment is LEFT in source space (surfaced by the badge), never deleted/orphaned.
    assert by_id[non_placing]["anchor_space"] == "source"
    assert by_id[non_placing]["state"] == "open"


def test_migration_is_idempotent(db_path):
    placeable = _seed_source_comment(db_path, _INBLOCK_QUOTE)
    non_placing = _seed_source_comment(db_path, _ABSENT_QUOTE)

    first = comment_service.migrate_comments_to_render_space(
        SLUG, db_path=db_path, served_render_html=RENDER_HTML)
    events_after_first = _event_count(db_path, placeable)
    non_placing_events_first = _event_count(db_path, non_placing)

    second = comment_service.migrate_comments_to_render_space(
        SLUG, db_path=db_path, served_render_html=RENDER_HTML)

    # Second run examines only the still-source remainder; it flips nothing and writes no events.
    assert second == {"examined": 1, "flipped": 0, "ref_less_null": 0, "stayed_source": 1}
    assert first["flipped"] == 1
    # No duplicate disposition events on the already-migrated comment, none added to the laggard.
    assert _event_count(db_path, placeable) == events_after_first
    assert _event_count(db_path, non_placing) == non_placing_events_first


# ======================================================================================
# Step 2.8: the client JS makes no source-substring assumption (verify only — no code change)
# ======================================================================================

def test_client_js_places_against_rendered_dom_not_source():
    """``requirements_comments.js`` already places against the rendered DOM (``concat.indexOf``);
    it must carry NO assumption that quotes are substrings of the canonical source `.collab.md`."""
    js = (Path(__file__).resolve().parents[1] / "cast_server" / "static"
          / "requirements_comments.js").read_text(encoding="utf-8")
    # Places against the rendered-DOM text concatenation, not a source file.
    assert "concat.indexOf" in js
    # No source-file coupling: the placement layer never names the canonical markdown.
    assert ".collab.md" not in js
    assert "collab.md" not in js
