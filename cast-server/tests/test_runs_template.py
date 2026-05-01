"""Markup-shape guard for the threaded /runs page (sp3).

Asserts that HTMX swap-target attributes (hx-get/hx-trigger/hx-swap) live on
the INNER ``.run-status-cells`` span, NEVER on the outer ``.run-node``
container. The outer node carries expand state (``.expanded`` class set by
inline JS) and must survive every 3s poll. This is a CAUSE-LEVEL guard —
symptom-level UI tests pass during the wait window even if a future refactor
breaks the swap target.
"""

from __future__ import annotations

import pytest
from bs4 import BeautifulSoup

from cast_server.deps import templates


@pytest.fixture
def running_run_dict() -> dict:
    """Hand-built run dict that satisfies the macro / fragment expectations."""
    return {
        "id": "run_test_running_001",
        "agent_name": "cast-preso-how",
        "status": "running",
        "ctx_class": "mid",
        "descendant_count": 0,
        "failed_descendant_count": 0,
        "rework_count": 0,
        "total_cost_usd": 0.0,
        "wall_duration_seconds": None,
        "active_execution_seconds": 42,
        "children": [],
        "is_rework": False,
        "rework_index": None,
        "created_at": "2026-05-01T12:00:00+00:00",
        "started_at": "2026-05-01T12:00:00+00:00",
        "completed_at": None,
        "resume_command": "diecast resume run_test_running_001",
        "session_id": None,
        "goal_slug": "preso-test",
        "goal_title": "Preso test",
        "task_id": None,
        "task_title": None,
        "cost_usd": 0.0,
        "context_usage": {"total": 100000, "limit": 200000},
        "artifacts": [],
        "output": None,
        "error_message": None,
    }


def _render_node(run: dict) -> BeautifulSoup:
    """Render the ``run_node`` macro for ``run`` and return the parsed soup."""
    macro = templates.get_template("macros/run_node.html").module
    html = macro.render_run(run)
    return BeautifulSoup(html, "html.parser")


def test_status_cells_carry_htmx_attrs(running_run_dict):
    soup = _render_node(running_run_dict)
    cells = soup.select_one(".run-status-cells")
    assert cells is not None, "fragment should render a .run-status-cells span"
    assert cells.get("hx-get"), ".run-status-cells must carry hx-get on running runs"
    assert cells.get("hx-trigger") == "every 3s"
    assert cells.get("hx-swap") == "outerHTML"
    assert "/status_cells" in cells["hx-get"]
    # Swap target lands on the inner cells span by id (own outerHTML swap).
    assert cells.get("id") == f"run-cells-{running_run_dict['id']}"


def test_run_node_does_not_carry_htmx_attrs(running_run_dict):
    soup = _render_node(running_run_dict)
    node = soup.select_one(".run-node")
    assert node is not None, "macro should render a .run-node container"
    forbidden_attrs = ("hx-get", "hx-post", "hx-trigger", "hx-swap")
    for attr in forbidden_attrs:
        assert not node.has_attr(attr), (
            f".run-node must NOT carry {attr}; "
            f"that would defeat poll-safety on expand state"
        )


def test_completed_run_status_cells_have_no_hx_attrs(running_run_dict):
    """Completed runs don't poll. The conditional in the fragment must hold."""
    completed_run = {**running_run_dict, "status": "completed"}
    soup = _render_node(completed_run)
    cells = soup.select_one(".run-status-cells")
    assert cells is not None
    forbidden_attrs = ("hx-get", "hx-trigger", "hx-swap")
    for attr in forbidden_attrs:
        assert not cells.has_attr(attr), f"completed runs must not carry {attr}"
