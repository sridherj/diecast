"""Endpoint tests for ``POST /api/goals/{slug}/route`` (Phase 3b, sub-phase 3).

The ``/route`` endpoint is the **one phase-agnostic door** (FR-016): it maps a
goal's persisted ``WorkFamily`` to a downstream-workflow handle and records the
decision. These tests are the SC-005 acceptance bar for the HTTP surface:

* **5-family seed trace** — five seeded goals routed by family, asserting the
  returned handle AND the persisted ``workflow_family``/``routing_handle`` in
  **both** the DB row and the rendered ``goal.yaml``.
* **Phase-flip byte-stability** — the crown jewel: flipping a goal's ``phase``
  (an unrelated state change) must not alter a single byte of the no-body
  ``/route`` response, because the idempotent no-op leaves ``routed_at`` untouched
  and the handler imports nothing that could re-classify.
* **Totality edges** — unknown family → ``unmatched`` (200, not recorded);
  un-routed goal → ``needs-classification`` (200, not recorded); unknown slug →
  404; idempotent re-POST → ``recorded: false`` with ``routed_at`` unchanged.
* **No-reclassify source pin (D4, handler half)** — the ``route_goal`` source
  contains no subprocess/agent-dispatch/classifier machinery. This pins the
  handler module; sp2 pins the service module — together they REPLACE the
  SC-005 "assert by code inspection" step.

Hermetic FastAPI app + ``TestClient`` per the ``test_api_agents.py`` pattern.
``isolated_db`` swaps ``cast_server.config.DB_PATH``; because
``cast_server.db.connection`` binds ``DB_PATH`` at import, the env fixture also
patches ``connection.DB_PATH`` directly so the service-layer reads/writes (which
the handler calls *without* an explicit ``db_path``) land on the test database.
Each goal is seeded with an on-disk ``folder_path`` holding a real ``goal.yaml``
so the best-effort yaml mirror is exercised, not skipped.
"""

from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CAST_SERVER_DIR = REPO_ROOT / "cast-server"

if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))


# The five families the SC-005 trace seeds and routes.
TRACE_FAMILIES = ["bug_fix", "new_initiative", "data_analysis", "random_idea", "testing_qa"]


def _seed_goal(db_path: Path, goals_root: Path, slug: str, title: str = "Routed Goal") -> Path:
    """Insert a goal row whose ``folder_path`` points at a real dir with a goal.yaml.

    The on-disk ``goal.yaml`` lets ``record_routing_decision``'s best-effort mirror
    actually write (``_update_goal_yaml_fields`` is a no-op when the file is absent),
    so the trace can assert the persisted stamp in the rendered yaml. Returns the
    goal directory.
    """
    from cast_server.db.connection import get_connection

    goal_dir = goals_root / slug
    goal_dir.mkdir(parents=True, exist_ok=True)
    (goal_dir / "goal.yaml").write_text(f"slug: {slug}\ntitle: {title}\n")

    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) VALUES (?, ?, ?)",
            (slug, title, str(goal_dir)),
        )
        conn.commit()
    finally:
        conn.close()
    return goal_dir


def _row(db_path: Path, slug: str) -> dict:
    """Return the goal row as a dict (or raise if absent)."""
    from cast_server.db.connection import get_connection

    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM goals WHERE slug = ?", (slug,)).fetchone()
    finally:
        conn.close()
    assert row is not None, f"expected a seeded goal row for {slug!r}"
    return dict(row)


def _yaml(goal_dir: Path) -> dict:
    """Parse the goal's rendered goal.yaml."""
    return yaml.safe_load((goal_dir / "goal.yaml").read_text()) or {}


@pytest.fixture
def env(isolated_db: Path, monkeypatch, tmp_path):
    """TestClient over the api_goals router on a hermetic DB + goals root.

    ``isolated_db`` patches ``config.DB_PATH`` and runs ``init_db``; the handler
    and the service it calls use ``get_connection()`` with no explicit path, which
    binds ``connection.DB_PATH`` at import — so patch that module directly too.
    """
    pytest.importorskip("cast_server.config")

    from cast_server.db import connection as _connection
    monkeypatch.setattr(_connection, "DB_PATH", isolated_db)

    from cast_server.routes import api_goals

    app = FastAPI()
    app.include_router(api_goals.router)

    goals_root = tmp_path / "goals"
    goals_root.mkdir()
    return {
        "client": TestClient(app),
        "db_path": isolated_db,
        "goals_root": goals_root,
    }


def test_five_family_seed_trace(env):
    """Each of the 5 families routes to the right handle, stamped in DB + goal.yaml."""
    from cast_server.config import WORKFLOW_REGISTRY

    client, db_path, goals_root = env["client"], env["db_path"], env["goals_root"]

    for family in TRACE_FAMILIES:
        slug = f"goal-{family}"
        goal_dir = _seed_goal(db_path, goals_root, slug)

        resp = client.post(f"/api/goals/{slug}/route", json={"family": family})

        assert resp.status_code == 200
        payload = resp.json()
        expected_steps = WORKFLOW_REGISTRY[family]["steps"]
        assert payload["family"] == family
        assert payload["status"] == "stub"
        assert payload["steps"] == list(expected_steps)
        assert payload["recorded"] is True
        assert payload["routing_handle"] == f"{family}:stub"

        # Persisted to the authoritative DB row...
        row = _row(db_path, slug)
        assert row["workflow_family"] == family
        assert row["routing_handle"] == f"{family}:stub"
        assert row["routed_at"] == payload["routed_at"]

        # ...and mirrored into the rendered goal.yaml (best-effort, DB authoritative).
        data = _yaml(goal_dir)
        assert data["workflow_family"] == family
        assert data["routing_handle"] == f"{family}:stub"


def test_bug_fix_steps_are_spec_mandated(env):
    """``bug_fix`` carries the spec-mandated logs→RCA→confirm→fix/test steps."""
    client, db_path, goals_root = env["client"], env["db_path"], env["goals_root"]
    _seed_goal(db_path, goals_root, "goal-bug")

    resp = client.post("/api/goals/goal-bug/route", json={"family": "bug_fix"})

    assert resp.status_code == 200
    assert resp.json()["steps"] == ["logs", "RCA", "confirm", "fix/test"]


def test_phase_flip_byte_stability(env):
    """A phase flip must not change one byte of the no-body /route response (SC-005)."""
    client, db_path, goals_root = env["client"], env["db_path"], env["goals_root"]
    slug = "goal-stable"
    _seed_goal(db_path, goals_root, slug)

    # Establish the routing, then capture the idempotent no-body response.
    client.post(f"/api/goals/{slug}/route", json={"family": "bug_fix"})
    before = client.post(f"/api/goals/{slug}/route")
    assert before.status_code == 200
    assert before.json()["recorded"] is False  # no-op: the family is unchanged

    # Flip the phase via the real endpoint — an unrelated state change.
    flip = client.put(f"/api/goals/{slug}/phase", data={"phase": "exploration"})
    assert flip.status_code == 200
    assert _row(db_path, slug)["phase"] == "exploration"

    after = client.post(f"/api/goals/{slug}/route")
    assert after.status_code == 200
    # Byte-identical: full raw body, not just the handle fields. routed_at must be
    # untouched by the idempotent no-op (the SC-005 crown-jewel assertion).
    assert after.content == before.content


def test_unknown_slug_is_404(env):
    """An unknown slug is the only 404 — content edges stay 200 (totality)."""
    resp = env["client"].post("/api/goals/no-such-goal/route", json={"family": "bug_fix"})
    assert resp.status_code == 404


def test_unmatched_family_not_recorded(env):
    """An unknown family string → 200 unmatched handle, nothing persisted."""
    client, db_path, goals_root = env["client"], env["db_path"], env["goals_root"]
    _seed_goal(db_path, goals_root, "goal-unmatched")

    resp = client.post("/api/goals/goal-unmatched/route", json={"family": "nonsense"})

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "unmatched"
    assert payload["family"] == "nonsense"
    assert payload["recorded"] is False
    assert payload["message"]  # the special case announces itself
    # The DB column is left untouched — no garbage routing record.
    assert _row(db_path, "goal-unmatched")["workflow_family"] is None


def test_needs_classification_when_unrouted_and_no_body(env):
    """An un-routed goal with no body → 200 needs-classification, not recorded."""
    client, db_path, goals_root = env["client"], env["db_path"], env["goals_root"]
    _seed_goal(db_path, goals_root, "goal-unrouted")

    resp = client.post("/api/goals/goal-unrouted/route")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "needs-classification"
    assert payload["family"] is None
    assert payload["recorded"] is False
    assert payload["message"]
    assert _row(db_path, "goal-unrouted")["workflow_family"] is None


def test_idempotent_repost_is_noop(env):
    """Re-routing the same family is a no-op: recorded/changed false, routed_at frozen."""
    client, db_path, goals_root = env["client"], env["db_path"], env["goals_root"]
    slug = "goal-idem"
    _seed_goal(db_path, goals_root, slug)

    first = client.post(f"/api/goals/{slug}/route", json={"family": "data_analysis"}).json()
    assert first["recorded"] is True
    routed_at = first["routed_at"]

    second = client.post(f"/api/goals/{slug}/route", json={"family": "data_analysis"}).json()
    assert second["recorded"] is False
    assert second["changed"] is False
    assert second["routed_at"] == routed_at  # the stamp did not churn
    assert _row(db_path, slug)["routed_at"] == routed_at


def test_changed_family_reports_previous(env):
    """Re-routing to a *different* family updates the row and reports the prior one."""
    client, db_path, goals_root = env["client"], env["db_path"], env["goals_root"]
    slug = "goal-changed"
    _seed_goal(db_path, goals_root, slug)

    client.post(f"/api/goals/{slug}/route", json={"family": "bug_fix"})
    resp = client.post(f"/api/goals/{slug}/route", json={"family": "new_initiative"}).json()

    assert resp["recorded"] is True
    assert resp["changed"] is True
    assert resp["previous_family"] == "bug_fix"
    assert _row(db_path, slug)["workflow_family"] == "new_initiative"


def test_no_reclassify_source_pin(env):
    """D4 (handler half): the /route handler source carries no re-classify machinery.

    The handler must import nothing that could re-classify — only ``goal_service``
    and ``workflow_router_service``. Pinning the *function* source (not the whole
    module, which legitimately imports ``agent_service`` for other handlers) makes
    FR-016/SC-005 true by construction.
    """
    from cast_server.routes import api_goals

    full_source = inspect.getsource(api_goals.route_goal)
    # Scan the *code*, not the prose: the docstring legitimately says "re-classify"
    # and "needs-classification". Drop the docstring's line span (ast.get_docstring
    # dedents, so a substring replace won't match) and scan what remains.
    func = ast.parse(full_source).body[0]
    doc_node = func.body[0]
    lines = full_source.splitlines()
    if isinstance(doc_node, ast.Expr) and isinstance(doc_node.value, ast.Constant):
        lines = lines[: doc_node.lineno - 1] + lines[doc_node.end_lineno :]
    code = "\n".join(lines)

    forbidden = ["subprocess", "cast_goal_classifier", ".trigger", "/trigger",
                 "anthropic", "openai", "classify", "dispatch", "tmux"]
    for token in forbidden:
        assert token not in code, f"/route handler code must not reference {token!r}"

    # Positive pin: it calls only the two whitelisted services.
    assert "goal_service.get_goal" in code
    assert "workflow_router_service.resolve" in code
    assert "workflow_router_service.record_routing_decision" in code


# ---------------------------------------------------------------------------
# GET /api/goals/{slug}/config — JSON read-counterpart to PATCH (inline-caller path)
# ---------------------------------------------------------------------------

def test_get_goal_config_returns_json(env):
    """The JSON read endpoint returns the goal dict so inline callers can confirm
    existence and read external_project_dir before dispatch — no HTML parsing."""
    client, db_path, goals_root = env["client"], env["db_path"], env["goals_root"]
    _seed_goal(db_path, goals_root, "goal-readable")

    resp = client.get("/api/goals/goal-readable/config")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["slug"] == "goal-readable"
    assert "external_project_dir" in body
    assert "title" in body


def test_get_goal_config_404_on_missing_goal(env):
    """A missing goal returns a plain 404 — callers must NOT read this as a signal
    to create the goal."""
    resp = env["client"].get("/api/goals/ghost-goal/config")

    assert resp.status_code == 404, resp.text
    assert "not found" in resp.json()["detail"].lower()
