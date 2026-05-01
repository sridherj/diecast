"""Sub-phase 4 (cast-subagent-and-skill-capture) — /runs UI surface tests.

Five named tests verify the L2 chip row + L3 detail table for skills_used
on the threaded /runs page. Pattern mirrors ``test_runs_template.py`` —
render the macro / partials directly via ``templates.get_template`` and
assert on parsed HTML; route-level decoration is unit-tested via
``_decorate_skills``. Hermetic: no DB writes, no real server, no I/O.

Test signatures use the cleaner ``(macro_renderer)`` shape rather than
the ``(client, db)`` shape sketched in the source plan: the chip layer
is pure presentation given a parsed ``skills_used`` list, so a TestClient
+ DB seed adds nothing the macro render path doesn't already cover, and
keeps the tests outside the heavy ``tests/ui/`` real-server harness
(which is currently blocked by venv ownership in this workspace per
the parent run's error memory). Decoration logic is exercised end-to-end
via ``_decorate_skills`` so JSON parsing, defensiveness, and
aggregation are covered without spinning up FastAPI.
"""

from __future__ import annotations

import pytest
from bs4 import BeautifulSoup

from cast_server.deps import templates
from cast_server.routes.pages import _decorate_skills


def _base_run(**overrides: object) -> dict:
    """Hand-built run dict that satisfies macro / fragment expectations.

    Defaults shape a completed L1 cast-* row with no children. Tests
    override individual fields (``skills_used``, ``skills_aggregated``,
    ``agent_name``, ``input_params``, ...) per scenario.
    """
    base = {
        "id": "run_test_skills_001",
        "agent_name": "cast-detailed-plan",
        "status": "completed",
        "ctx_class": None,
        "descendant_count": 0,
        "failed_descendant_count": 0,
        "rework_count": 0,
        "total_cost_usd": 0.0,
        "wall_duration_seconds": 5,
        "active_execution_seconds": None,
        "children": [],
        "is_rework": False,
        "rework_index": None,
        "created_at": "2026-05-01T12:00:00+00:00",
        "started_at": "2026-05-01T12:00:00+00:00",
        "completed_at": "2026-05-01T12:00:05+00:00",
        "resume_command": "",
        "session_id": None,
        "goal_slug": "system-ops",
        "goal_title": "System ops",
        "task_id": None,
        "task_title": None,
        "cost_usd": 0.0,
        "context_usage": None,
        "artifacts": [],
        "output": None,
        "error_message": None,
        "skills_used": [],
        "skills_aggregated": [],
    }
    base.update(overrides)
    return base


def _render_node(run: dict) -> BeautifulSoup:
    """Render the ``run_node`` macro for ``run`` and return parsed soup."""
    macro = templates.get_template("macros/run_node.html").module
    html = macro.render_run(run)
    return BeautifulSoup(html, "html.parser")


# ---------------------------------------------------------------------------
# Test 1: User-invocation row (slash command, no Task() subagent) shows chips.
# Decision #1 — record_skill attaches to most-recent running cast-* row;
# user-invocation rows must therefore receive chips just like subagent rows.
# ---------------------------------------------------------------------------
def test_skills_chip_row_renders_for_user_invocation_with_skills():
    # Arrange — slash-command user-invocation row with one captured skill.
    run = _base_run(
        agent_name="cast-detailed-plan",
        input_params={"source": "user-prompt"},
        skills_used=[
            {"name": "cast-detailed-plan", "invoked_at": "2026-05-01T12:00:00Z"},
        ],
    )
    expected_chip_names = ["cast-detailed-plan"]
    expected_count_label = "1 skill:"

    # Act
    soup = _render_node(run)
    chips = soup.select_one(".skills-chips")

    # Assert
    assert chips is not None, (
        "user-invocation rows must render .skills-chips when skills_used is "
        "populated (Decision #1: no source filter on attribution)"
    )
    actual_chip_names = [c.get_text(strip=True) for c in chips.select(".skill-chip")]
    assert actual_chip_names == expected_chip_names
    actual_count_label = chips.select_one(".skills-count")
    assert actual_count_label is not None
    assert actual_count_label.get_text(strip=True) == expected_count_label


# ---------------------------------------------------------------------------
# Test 2: Subagent row (cast-* dispatched via Task()) shows chips.
# ---------------------------------------------------------------------------
def test_skills_chip_row_renders_for_subagent_with_skills():
    # Arrange — Task()-dispatched cast-* subagent row with two skills.
    run = _base_run(
        agent_name="cast-spec-checker",
        input_params={"source": "subagent-start"},
        claude_agent_id="agent_xyz_001",
        skills_used=[
            {"name": "cast-spec-checker", "invoked_at": "2026-05-01T12:01:00Z"},
            {"name": "cast-update-spec", "invoked_at": "2026-05-01T12:01:30Z"},
        ],
    )
    expected_chip_names = ["cast-spec-checker", "cast-update-spec"]
    expected_count_label = "2 skills:"

    # Act
    soup = _render_node(run)
    chips = soup.select_one(".skills-chips")

    # Assert
    assert chips is not None
    actual_chip_names = [c.get_text(strip=True) for c in chips.select(".skill-chip")]
    assert actual_chip_names == expected_chip_names
    actual_count_label = chips.select_one(".skills-count")
    assert actual_count_label.get_text(strip=True) == expected_count_label
    # Two chips ≤ 2 threshold → no overflow badge.
    assert chips.select_one(".skill-overflow") is None


# ---------------------------------------------------------------------------
# Test 3: Empty skills_used hides the chip row entirely (no "0 skills"
# placeholder, no empty container).
# ---------------------------------------------------------------------------
def test_skills_chip_row_hidden_when_skills_used_empty():
    run = _base_run(skills_used=[])
    soup = _render_node(run)
    assert soup.select_one(".skills-chips") is None, (
        "empty skills_used must hide the chip row entirely — no placeholder, "
        "no empty .skills-chips container"
    )


# ---------------------------------------------------------------------------
# Test 4: Overflow badge "+N" appears once skills_used exceeds 2 entries.
# Anchors at the exact threshold: 2 chips → no badge; 3+ → +N badge.
# ---------------------------------------------------------------------------
def test_skills_chip_overflow_indicator_shows_plus_n_after_two_chips():
    # Arrange — five skills, deterministic insertion order, fixed timestamps.
    run = _base_run(
        skills_used=[
            {"name": "cast-detailed-plan", "invoked_at": "2026-05-01T12:00:00Z"},
            {"name": "cast-spec-checker", "invoked_at": "2026-05-01T12:01:00Z"},
            {"name": "cast-update-spec", "invoked_at": "2026-05-01T12:02:00Z"},
            {"name": "cast-plan-review", "invoked_at": "2026-05-01T12:03:00Z"},
            {"name": "cast-pytest-best-practices", "invoked_at": "2026-05-01T12:04:00Z"},
        ],
    )
    expected_chip_names = ["cast-detailed-plan", "cast-spec-checker"]
    expected_overflow_text = "+3"

    # Act
    soup = _render_node(run)
    chips = soup.select_one(".skills-chips")

    # Assert — first two chips render inline; remaining 3 collapse to "+3".
    assert chips is not None
    actual_chip_names = [c.get_text(strip=True) for c in chips.select(".skill-chip")]
    assert actual_chip_names == expected_chip_names
    actual_overflow = chips.select_one(".skill-overflow")
    assert actual_overflow is not None, "overflow badge required when skills_used > 2"
    assert actual_overflow.get_text(strip=True) == expected_overflow_text

    # Threshold check: with exactly 2 skills, no overflow badge appears.
    run_two = _base_run(
        skills_used=[
            {"name": "cast-detailed-plan", "invoked_at": "2026-05-01T12:00:00Z"},
            {"name": "cast-spec-checker", "invoked_at": "2026-05-01T12:01:00Z"},
        ],
    )
    soup_two = _render_node(run_two)
    chips_two = soup_two.select_one(".skills-chips")
    assert chips_two is not None
    assert chips_two.select_one(".skill-overflow") is None


# ---------------------------------------------------------------------------
# Test 5: L3 detail aggregates repeated skill invocations into a single row
# with the correct count and earliest invoked_at. Drives _decorate_skills
# (the route-side aggregator) end-to-end and asserts the rendered table.
# ---------------------------------------------------------------------------
def test_l3_detail_aggregates_repeated_skill_invocations_into_count():
    # Arrange — repeats of cast-detailed-plan + a single cast-spec-checker.
    # Pass through JSON-string form (DB shape) to also exercise json.loads.
    import json
    run = _base_run(
        skills_used=json.dumps([
            {"name": "cast-detailed-plan", "invoked_at": "2026-05-01T12:00:00Z"},
            {"name": "cast-spec-checker", "invoked_at": "2026-05-01T12:01:00Z"},
            {"name": "cast-detailed-plan", "invoked_at": "2026-05-01T12:02:00Z"},
            {"name": "cast-detailed-plan", "invoked_at": "2026-05-01T12:03:00Z"},
        ]),
    )
    expected_aggregated = {
        "cast-detailed-plan": ("2026-05-01T12:00:00Z", "3"),
        "cast-spec-checker": ("2026-05-01T12:01:00Z", "1"),
    }

    # Act — drive the route-side decorator the same way /runs does, then
    # render the macro so the L3 detail partial reaches the DOM.
    _decorate_skills(run)
    soup = _render_node(run)

    # Assert — aggregation contract: by-name grouping with count + earliest invoked_at.
    actual_by_name = {row["name"]: row for row in run["skills_aggregated"]}
    assert actual_by_name["cast-detailed-plan"]["count"] == 3
    assert actual_by_name["cast-detailed-plan"]["first_invoked"] == "2026-05-01T12:00:00Z"
    assert actual_by_name["cast-spec-checker"]["count"] == 1
    assert actual_by_name["cast-spec-checker"]["first_invoked"] == "2026-05-01T12:01:00Z"

    # And the L3 detail partial renders one <tr> per distinct skill.
    detail = soup.select_one(".detail .skills-detail")
    assert detail is not None, "L3 .skills-detail table must render when aggregated rows exist"
    rows = detail.select("tbody tr")
    assert len(rows) == 2, "one row per distinct skill name"
    actual_rows = {
        cells[0].get_text(strip=True): (cells[1].get_text(strip=True), cells[2].get_text(strip=True))
        for cells in (r.find_all("td") for r in rows)
    }
    assert actual_rows == expected_aggregated


# ---------------------------------------------------------------------------
# Defensive parsing: malformed skills_used JSON falls back to empty list
# and the page still renders without a chip row. Locks the try/except
# contract documented in sp4 plan step 4.4.
# ---------------------------------------------------------------------------
def test_decorate_skills_handles_malformed_json_without_crashing():
    run = _base_run(skills_used="{not: valid json,,,")
    _decorate_skills(run)
    assert run["skills_used"] == []
    assert run["skills_aggregated"] == []


def test_decorate_skills_handles_none_without_crashing():
    run = _base_run(skills_used=None)
    _decorate_skills(run)
    assert run["skills_used"] == []
    assert run["skills_aggregated"] == []
