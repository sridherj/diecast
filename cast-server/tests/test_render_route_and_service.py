"""Tests for Phase 3a sp4 — serve + regenerate (WP-E).

Two surfaces under test:

* ``services.requirements_render_service.rerender_requirements_html`` — the lazy,
  hash-gated, atomic regenerator. Exercised via explicit ``goals_dir`` / ``db_path``
  injection (no globals, the house DI pattern).
* ``GET /goals/{slug}/render`` in ``routes/pages.py`` — slug-validated (404 on
  unknown, which also kills path traversal), self-healing on view, prompt-to-begin
  on missing requirements.

The generated ``.html`` is an AUTO-GENERATED render of the canonical ``.collab.md``;
the service reads the ``.collab.md`` and never writes it (FR-007, route-level guard).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CAST_SERVER_DIR = REPO_ROOT / "cast-server"
if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))

# A non-stub requirements doc (>200 words) with valid front-matter — the full render input.
FIXTURE_COLLAB = (
    CAST_SERVER_DIR / "tests" / "fixtures" / "refine_requirements_v2" / "refined_requirements.collab.md"
)

AUTO_GENERATED_MARK = "<!-- AUTO-GENERATED: Read-only render of refined_requirements.collab.md."
SOURCE_HASH_MARK = "<!-- source-hash: "


def _seed_collab(goals_dir: Path, slug: str, body: str) -> Path:
    """Write a ``refined_requirements.collab.md`` for ``slug`` under ``goals_dir``."""
    d = goals_dir / slug
    d.mkdir(parents=True, exist_ok=True)
    path = d / "refined_requirements.collab.md"
    path.write_text(body, encoding="utf-8")
    return path


def _full_spec_body() -> str:
    return FIXTURE_COLLAB.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Service-level tests (explicit DI — no globals)                              #
# --------------------------------------------------------------------------- #


def test_rerender_missing_source_returns_none(tmp_path, isolated_db):
    """No ``.collab.md`` → the service returns ``None`` (not an error, not a file)."""
    from cast_server.services import requirements_render_service as svc

    out = svc.rerender_requirements_html("ghost", goals_dir=tmp_path, db_path=isolated_db)
    assert out is None
    assert not (tmp_path / "ghost" / "refined_requirements.html").exists()


def test_rerender_writes_auto_generated_header_and_hash(tmp_path, isolated_db):
    """First render writes the AUTO-GENERATED header + a ``source-hash`` comment."""
    from cast_server.services import requirements_render_service as svc

    _seed_collab(tmp_path, "g1", _full_spec_body())
    out = svc.rerender_requirements_html("g1", goals_dir=tmp_path, db_path=isolated_db)

    assert out is not None and out.exists()
    text = out.read_text(encoding="utf-8")
    assert text.startswith(AUTO_GENERATED_MARK)
    assert SOURCE_HASH_MARK in text
    # The pure render body is present beneath the generated header.
    assert "goal-card" in text


def test_fresh_hash_is_noop(tmp_path, isolated_db):
    """Unchanged source → the ``.html`` is byte-identical and not rewritten (mtime stable)."""
    from cast_server.services import requirements_render_service as svc

    _seed_collab(tmp_path, "g2", _full_spec_body())
    first = svc.rerender_requirements_html("g2", goals_dir=tmp_path, db_path=isolated_db)
    bytes_before = first.read_bytes()
    mtime_before = first.stat().st_mtime_ns

    time.sleep(0.01)  # ensure a rewrite would change mtime_ns
    second = svc.rerender_requirements_html("g2", goals_dir=tmp_path, db_path=isolated_db)

    assert second == first
    assert second.read_bytes() == bytes_before
    assert second.stat().st_mtime_ns == mtime_before  # not rewritten


def test_stale_hash_regenerates(tmp_path, isolated_db):
    """Changing the source → a new ``source-hash`` and fresh bytes."""
    from cast_server.services import requirements_render_service as svc
    from cast_server.requirements_render.hashing import content_hash

    path = _seed_collab(tmp_path, "g3", _full_spec_body())
    out = svc.rerender_requirements_html("g3", goals_dir=tmp_path, db_path=isolated_db)
    hash_before = content_hash(_full_spec_body())
    assert f"{SOURCE_HASH_MARK}{hash_before} -->" in out.read_text(encoding="utf-8")

    changed = _full_spec_body() + "\n\n## Added Section\n\nA brand new requirement paragraph.\n"
    path.write_text(changed, encoding="utf-8")
    out2 = svc.rerender_requirements_html("g3", goals_dir=tmp_path, db_path=isolated_db)

    hash_after = content_hash(changed)
    assert hash_after != hash_before
    assert f"{SOURCE_HASH_MARK}{hash_after} -->" in out2.read_text(encoding="utf-8")


def test_collab_md_never_written(tmp_path, isolated_db):
    """The canonical ``.collab.md`` bytes are identical before/after a render (FR-007)."""
    from cast_server.services import requirements_render_service as svc

    path = _seed_collab(tmp_path, "g4", _full_spec_body())
    before = path.read_bytes()
    svc.rerender_requirements_html("g4", goals_dir=tmp_path, db_path=isolated_db)
    assert path.read_bytes() == before


def test_atomic_write_leaves_no_tmp_and_uses_os_replace(tmp_path, isolated_db, monkeypatch):
    """The write path goes through ``os.replace`` (atomic) and leaves no ``.tmp`` debris."""
    import cast_server.services.requirements_render_service as svc

    calls = {"replace": 0}
    real_replace = svc.os.replace

    def _spy_replace(src, dst):
        calls["replace"] += 1
        return real_replace(src, dst)

    monkeypatch.setattr(svc.os, "replace", _spy_replace)

    _seed_collab(tmp_path, "g5", _full_spec_body())
    out = svc.rerender_requirements_html("g5", goals_dir=tmp_path, db_path=isolated_db)

    assert calls["replace"] == 1
    assert out.exists()
    leftovers = list((tmp_path / "g5").glob("*.tmp"))
    assert leftovers == []


# --------------------------------------------------------------------------- #
# Route-level tests (GET /goals/{slug}/render + /render/status)               #
#                                                                             #
# sp3d inverts the route's happy path: on a stale-or-missing render the route #
# no longer blocks on a synchronous deterministic render — it kicks off the   #
# background maker job and serves a live generating state. Readiness is       #
# derived PURELY from the artifact's embedded source-hash, so the route is a  #
# thin dispatch over ``resolve_render``. These tests inject a fake runner via #
# ``render_job_service.ProductionAgentRunner`` so no real ``claude -p`` fires.#
# --------------------------------------------------------------------------- #


class _FakeRunner:
    """A tool-free-agent stand-in for the route path. Returns canned WHAT/HOW strings; an optional
    ``latch`` blocks every call so a job stays ``running`` for the single-flight / generating asserts.
    Empty strings (the default) drive the literal-no-output → deterministic-fallback branch, which
    always publishes a fresh artifact regardless of gate fixtures."""

    def __init__(self, *, what: str = "", how: str = "", latch=None):
        self.what = what
        self.how = how
        self.latch = latch
        self.calls = 0

    def run_agent(self, agent_name: str, user_msg: str, *, timeout_s: int) -> str:
        self.calls += 1
        if self.latch is not None:
            self.latch.wait(timeout=10)
        return self.what if agent_name == "cast-requirements-what" else self.how


@pytest.fixture
def env(isolated_db, monkeypatch, tmp_path):
    """TestClient over the pages router on a hermetic DB + goals root.

    ``cast_server.db.connection`` binds ``DB_PATH`` at import, so patch it directly
    (``isolated_db`` only swaps ``config.DB_PATH``). Both the render service and the job
    service bind ``GOALS_DIR`` at import — patch both module copies so the route's default-arg
    calls land on the test goals root. ``ProductionAgentRunner`` is swapped for a mutable
    fake-runner box so the background job never spawns a real ``claude -p``; the render-jobs build
    dir is redirected under ``tmp_path`` and the job registry is reset around each test.
    """
    pytest.importorskip("cast_server.config")

    from cast_server.db import connection as _connection
    monkeypatch.setattr(_connection, "DB_PATH", isolated_db)

    goals_root = tmp_path / "goals"
    goals_root.mkdir()

    import cast_server.config as _cfg
    from cast_server.services import requirements_render_service as svc
    from cast_server.services import render_job_service as job_svc

    monkeypatch.setattr(svc, "GOALS_DIR", goals_root)
    monkeypatch.setattr(job_svc, "GOALS_DIR", goals_root)
    monkeypatch.setattr(_cfg, "RENDER_JOBS_DIR", tmp_path / "render-jobs")

    # The route starts jobs with the default runner; inject a fake one via the factory seam.
    runner_box = {"runner": _FakeRunner()}
    monkeypatch.setattr(job_svc, "ProductionAgentRunner", lambda job_dir: runner_box["runner"])

    job_svc._reset_state()

    from cast_server.routes import pages

    app = FastAPI()
    app.include_router(pages.router)
    yield {
        "client": TestClient(app),
        "db_path": isolated_db,
        "goals_root": goals_root,
        "runner_box": runner_box,
        "job_svc": job_svc,
        "svc": svc,
    }
    job_svc._reset_state()


def _seed_goal(db_path: Path, goals_root: Path, slug: str) -> Path:
    """Insert a goal row whose ``folder_path`` points at a real dir under ``goals_root``."""
    from cast_server.db.connection import get_connection

    goal_dir = goals_root / slug
    goal_dir.mkdir(parents=True, exist_ok=True)
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) VALUES (?, ?, ?)",
            (slug, "Render Goal", str(goal_dir)),
        )
        conn.commit()
    finally:
        conn.close()
    return goal_dir


_STUB_BODY = "---\nclassification:\n  family: generic\n---\n# Tiny\n\n## Intent\n\nToo short.\n"


def _job_rows(db_path: Path, slug: str) -> list[dict]:
    from cast_server.db.connection import get_connection

    conn = get_connection(db_path)
    try:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM render_jobs WHERE goal_slug = ? ORDER BY id", (slug,)
        ).fetchall()]
    finally:
        conn.close()


def _wait_terminal(db_path: Path, job_id: int, timeout: float = 5.0) -> dict:
    """Poll a render_jobs row until it leaves ``running`` (the fake runner completes near-instantly)."""
    from cast_server.services import render_job_service as job_svc

    deadline = time.time() + timeout
    while time.time() < deadline:
        row = job_svc.get_job_row(job_id, db_path)
        if row and row["status"] != "running":
            return row
        time.sleep(0.02)
    return job_svc.get_job_row(job_id, db_path)


def test_unknown_slug_404(env):
    """An unknown slug → 404 (also the path-traversal kill)."""
    r = env["client"].get("/goals/no-such-goal/render")
    assert r.status_code == 404


def test_path_traversal_attempt_404(env):
    """A traversal-shaped slug resolves to no goal → 404 (never reads outside the goals dir)."""
    r = env["client"].get("/goals/..%2F..%2F..%2Fetc%2Fpasswd/render")
    assert r.status_code == 404
    assert "root:" not in r.text


def test_fresh_hash_serves_file_untouched_no_job(env):
    """A fresh cached artifact → 200 served byte-identical AND no job started (cached views instant)."""
    _seed_goal(env["db_path"], env["goals_root"], "live")
    _seed_collab(env["goals_root"], "live", _full_spec_body())
    # Pre-seed a fresh deterministic artifact so the hash is already current.
    out = env["svc"].rerender_requirements_html(
        "live", goals_dir=env["goals_root"], db_path=env["db_path"]
    )
    bytes_before = out.read_bytes()

    r = env["client"].get("/goals/live/render")
    assert r.status_code == 200
    assert "goal-card" in r.text
    assert AUTO_GENERATED_MARK in r.text
    assert out.read_bytes() == bytes_before  # byte-untouched
    assert _job_rows(env["db_path"], "live") == []  # NO job started for a fresh view


def test_stale_hash_serves_generating_and_starts_one_job(env):
    """A missing/stale render → 200 generating state AND exactly one background job started."""
    _seed_goal(env["db_path"], env["goals_root"], "gen")
    _seed_collab(env["goals_root"], "gen", _full_spec_body())
    latch = __import__("threading").Event()
    env["runner_box"]["runner"] = _FakeRunner(latch=latch)  # hold the job in ``running``

    try:
        r = env["client"].get("/goals/gen/render")
        assert r.status_code == 200
        assert "Generating your requirements render" in r.text
        assert "/goals/gen/render/status" in r.text  # the poll script is wired
        rows = _job_rows(env["db_path"], "gen")
        assert len(rows) == 1 and rows[0]["status"] == "running"

        # A repeat view while the job runs must NOT start a second job (single-flight).
        r2 = env["client"].get("/goals/gen/render")
        assert r2.status_code == 200
        assert len(_job_rows(env["db_path"], "gen")) == 1
    finally:
        latch.set()
        _wait_terminal(env["db_path"], _job_rows(env["db_path"], "gen")[0]["id"])


def test_generating_completes_then_status_ready_and_reload_serves_render(env):
    """After the fake job completes, the next status poll reports ``ready`` and a reload serves it."""
    _seed_goal(env["db_path"], env["goals_root"], "swap")
    _seed_collab(env["goals_root"], "swap", _full_spec_body())

    # First view kicks off the job (empty runner → no-output → deterministic fallback publish).
    r = env["client"].get("/goals/swap/render")
    assert "Generating your requirements render" in r.text
    job_id = _job_rows(env["db_path"], "swap")[0]["id"]
    row = _wait_terminal(env["db_path"], job_id)
    assert row["status"] == "fallback"  # literal no-output → deterministic page IS the render

    # The poll now reports ready, and a reload (the route again) serves the finished render.
    s = env["client"].get("/goals/swap/render/status")
    assert s.status_code == 200 and s.json()["state"] == "ready"

    r2 = env["client"].get("/goals/swap/render")
    assert r2.status_code == 200
    assert "goal-card" in r2.text  # the published deterministic render, not the generating page
    assert "Generating your requirements render" not in r2.text


def test_stale_render_with_banner_is_response_only(env):
    """A stale render serves WITH a regenerating banner injected on the response; disk stays stable."""
    _seed_goal(env["db_path"], env["goals_root"], "stale")
    path = _seed_collab(env["goals_root"], "stale", _full_spec_body())
    out = env["svc"].rerender_requirements_html(
        "stale", goals_dir=env["goals_root"], db_path=env["db_path"]
    )
    bytes_before = out.read_bytes()

    # Move the source so the cached render is now stale.
    path.write_text(_full_spec_body() + "\n\n## New\n\nA fresh paragraph.\n", encoding="utf-8")
    latch = __import__("threading").Event()
    env["runner_box"]["runner"] = _FakeRunner(latch=latch)
    try:
        r = env["client"].get("/goals/stale/render")
        assert r.status_code == 200
        assert "regenerating" in r.text  # the banner is in the response …
        assert "regenerating" not in out.read_text(encoding="utf-8")  # … but NOT on disk
        assert out.read_bytes() == bytes_before  # cached artifact byte-stable
    finally:
        latch.set()
        _wait_terminal(env["db_path"], _job_rows(env["db_path"], "stale")[0]["id"])


def test_missing_requirements_prompt_to_begin(env):
    """Known goal, no ``.collab.md`` → 200 prompt-to-begin (a product state, not an error)."""
    _seed_goal(env["db_path"], env["goals_root"], "empty")

    r = env["client"].get("/goals/empty/render")
    assert r.status_code == 200
    assert "No requirements yet" in r.text
    assert _job_rows(env["db_path"], "empty") == []  # missing source never starts a job


def test_stub_serves_deterministic_no_job(env):
    """A stub source → 200 deterministic render, the maker never invoked (no job row)."""
    _seed_goal(env["db_path"], env["goals_root"], "stub")
    _seed_collab(env["goals_root"], "stub", _STUB_BODY)

    r = env["client"].get("/goals/stub/render")
    assert r.status_code == 200
    assert AUTO_GENERATED_MARK in r.text
    assert "Generating your requirements render" not in r.text
    assert _job_rows(env["db_path"], "stub") == []


def test_fallback_ready_serves_unstamped_deterministic_page(env):
    """Literal no-output → status ready (deterministic page IS the render), job row ``fallback``."""
    _seed_goal(env["db_path"], env["goals_root"], "fb")
    _seed_collab(env["goals_root"], "fb", _full_spec_body())

    result = env["job_svc"].request_render(
        "fb", runner=_FakeRunner(), goals_dir=env["goals_root"], db_path=env["db_path"], wait=True
    )
    assert result["state"] == "fallback"

    r = env["client"].get("/goals/fb/render")
    assert r.status_code == 200
    assert AUTO_GENERATED_MARK in r.text
    assert "<!-- served-by:" not in r.text  # the deterministic page is unstamped
    assert "Needs review" not in r.text  # no badge for a clean fallback

    s = env["client"].get("/goals/fb/render/status")
    assert s.json()["state"] == "ready"


def test_structural_violation_flagged_serves_ready_with_review_badge(env):
    """OVERRIDE: a flagged best-attempt serves at ``ready`` WITH a response-only needs-review badge."""
    _seed_goal(env["db_path"], env["goals_root"], "flag")
    _seed_collab(env["goals_root"], "flag", _full_spec_body())
    h = env["svc"].current_source_hash("flag", goals_dir=env["goals_root"], db_path=env["db_path"])

    flagged_body = (
        "<!doctype html><html><head><title>Flagged</title></head>"
        '<body data-goal-slug="flag"><main><h2>Best attempt</h2></main></body></html>'
    )
    out = env["svc"].publish_maker_html(
        "flag", flagged_body, source_hash=h, served_by="structural_violation",
        goals_dir=env["goals_root"], db_path=env["db_path"],
    )
    disk_before = out.read_text(encoding="utf-8")

    r = env["client"].get("/goals/flag/render")
    assert r.status_code == 200
    assert "<!-- served-by: structural_violation -->" in r.text  # the served stamp is observable
    assert "Needs review" in r.text  # the badge is injected …
    assert "Needs review" not in disk_before  # … only on the response, not on disk
    assert out.read_text(encoding="utf-8") == disk_before  # artifact byte-stable
    # Status stays a pure artifact-hash derivation (ready) — the badge never leaks into the JSON.
    # The human_review flag (4a-2) is read off the served artifact's envelope; this artifact was
    # published WITHOUT a human-review stamp (publish_maker_html default), so it reports False.
    s = env["client"].get("/goals/flag/render/status")
    assert s.json() == {"state": "ready", "source_hash": h, "human_review": False}


def test_failed_state_status_and_generating_terminal_affordance(env):
    """No servable artifact + a terminal ``failed`` job row → status ``failed``; the generating
    page carries the terminal ``reload to retry`` affordance (the poll stops, never loops)."""
    _seed_goal(env["db_path"], env["goals_root"], "dead")
    _seed_collab(env["goals_root"], "dead", _full_spec_body())
    h = env["svc"].current_source_hash("dead", goals_dir=env["goals_root"], db_path=env["db_path"])

    # A first-generation crash: a terminal ``failed`` row, no artifact published.
    row_id = env["job_svc"]._insert_job("dead", h, env["db_path"])
    env["job_svc"]._update_job(row_id, env["db_path"], status="failed", error="boom")

    s = env["client"].get("/goals/dead/render/status")
    assert s.status_code == 200 and s.json()["state"] == "failed"

    # The generating page (served for the no-artifact view) exposes the terminal affordance.
    from cast_server.routes import pages
    page = pages._generating_page("dead")
    assert "showFailed" in page and "Generation failed" in page
    assert 'data-render-status' in page


def test_status_ready_iff_embedded_hash_matches_current(env):
    """``ready`` exactly when the artifact's embedded source-hash equals the current source hash."""
    _seed_goal(env["db_path"], env["goals_root"], "st")
    path = _seed_collab(env["goals_root"], "st", _full_spec_body())
    env["svc"].rerender_requirements_html("st", goals_dir=env["goals_root"], db_path=env["db_path"])

    assert env["client"].get("/goals/st/render/status").json()["state"] == "ready"

    # Move the source → the embedded hash is now stale → no longer ready.
    path.write_text(_full_spec_body() + "\n\n## Drift\n\nMoves the hash.\n", encoding="utf-8")
    assert env["client"].get("/goals/st/render/status").json()["state"] == "generating"


def test_status_failed_only_when_no_servable_artifact(env):
    """A fresh artifact wins over a ``failed`` row — readiness derives from the artifact, not the table."""
    _seed_goal(env["db_path"], env["goals_root"], "win")
    _seed_collab(env["goals_root"], "win", _full_spec_body())
    env["svc"].rerender_requirements_html("win", goals_dir=env["goals_root"], db_path=env["db_path"])
    h = env["svc"].current_source_hash("win", goals_dir=env["goals_root"], db_path=env["db_path"])

    # Insert a terminal failed row for the SAME hash; the fresh artifact must still report ready.
    row_id = env["job_svc"]._insert_job("win", h, env["db_path"])
    env["job_svc"]._update_job(row_id, env["db_path"], status="failed", error="ignored")

    assert env["client"].get("/goals/win/render/status").json()["state"] == "ready"


def test_render_exception_returns_500_and_keeps_existing(env, monkeypatch):
    """A resolve/serve exception → plain 500; never a stack trace to the user."""
    _seed_goal(env["db_path"], env["goals_root"], "boom")
    _seed_collab(env["goals_root"], "boom", _full_spec_body())

    from cast_server.routes import pages

    def _explode(*_a, **_k):
        raise RuntimeError("render kaboom")

    monkeypatch.setattr(pages.requirements_render_service, "resolve_render", _explode)

    r = env["client"].get("/goals/boom/render")
    assert r.status_code == 500
    assert "kaboom" not in r.text
    assert "Traceback" not in r.text


# --------------------------------------------------------------------------- #
# "View render" link on the goal page (SC-003)                                #
# --------------------------------------------------------------------------- #


def test_goal_page_has_view_render_link():
    """The goal detail template links to the render route (one line, no new surface)."""
    template = (
        CAST_SERVER_DIR / "cast_server" / "templates" / "pages" / "goal_detail.html"
    ).read_text(encoding="utf-8")
    assert "/goals/{{ goal.slug }}/render" in template
    assert "View requirements render" in template
