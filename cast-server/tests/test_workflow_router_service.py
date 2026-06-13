"""Tests for workflow_router_service — the pure resolver + idempotent recorder.

Headline SC-005 gate assertions live here: totality, stub discipline, the
registry↔WorkFamily key-set pin, recorder idempotency, the no-reclassify /
no-STARTER_TASKS source pins (D4), and the missing-goal.yaml best-effort pin (D5).
This is the ONE place Phase 3b imports families.py (in tests only).
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest
import yaml

from cast_server.config import WORKFLOW_FAMILIES, WORKFLOW_REGISTRY
from cast_server.requirements_render.families import WorkFamily
from cast_server.services import workflow_router_service as wr


def _init_db_and_create_goal(
    tmp_path: Path, slug: str = "my-goal", title: str = "My Goal"
) -> tuple[Path, Path, Path]:
    """Bootstrap a test DB + goals_dir and create a goal.

    Returns (db_path, goals_dir, goal_dir). Mirrors test_goal_service_ext_routing.py.
    """
    from cast_server.db.connection import init_db
    from cast_server.services.goal_service import create_goal

    db_path = tmp_path / "test.db"
    goals_dir = tmp_path / "goals"
    goals_dir.mkdir()
    init_db(db_path)
    create_goal(title, goals_dir=goals_dir, db_path=db_path)
    return db_path, goals_dir, goals_dir / slug


def _row(db_path: Path, slug: str) -> dict:
    """Fetch a goal row as a dict from the test DB."""
    from cast_server.db.connection import get_connection

    conn = get_connection(db_path)
    try:
        return dict(conn.execute("SELECT * FROM goals WHERE slug = ?", (slug,)).fetchone())
    finally:
        conn.close()


class TestResolveTotality:
    """resolve(family) is PURE + TOTAL over 9 families + None + unknown string."""

    @pytest.mark.parametrize("family", sorted(WORKFLOW_FAMILIES))
    def test_each_family_resolves_to_registry_status(self, family):
        handle = wr.resolve(family)
        assert handle.family == family
        assert handle.status == WORKFLOW_REGISTRY[family]["status"]
        assert handle.steps, "registered family must carry non-empty steps"
        assert handle.message, "registered family must carry a non-empty message"

    def test_none_returns_needs_classification(self):
        handle = wr.resolve(None)
        assert handle.family is None
        assert handle.status == "needs-classification"
        assert handle.message, "needs-classification handle must announce itself"

    def test_unknown_string_returns_unmatched(self):
        handle = wr.resolve("nonsense")
        assert handle.family == "nonsense"
        assert handle.status == "unmatched"
        assert handle.message, "unmatched handle must announce itself"

    def test_totality_no_exceptions_no_none(self):
        """All 9 families + None + unknown → a real handle, 0 exceptions, 0 None."""
        cases = list(WORKFLOW_FAMILIES) + [None, "nonsense"]
        for family in cases:
            handle = wr.resolve(family)
            assert handle is not None
            assert isinstance(handle, wr.WorkflowHandle)

    def test_resolve_has_no_db_path_parameter(self):
        """Purity-by-shape: resolve takes only the family, never a db_path."""
        params = inspect.signature(wr.resolve).parameters
        assert "db_path" not in params
        assert list(params) == ["family"]


class TestRegistryDiscipline:
    """The WP-A pins, co-located: registry↔enum key-set + stub discipline."""

    def test_registry_keyset_matches_workfamily(self):
        """set(WORKFLOW_REGISTRY) == {f.value for f in WorkFamily} — drift fails CI."""
        assert set(WORKFLOW_REGISTRY) == {f.value for f in WorkFamily}
        assert set(WORKFLOW_FAMILIES) == {f.value for f in WorkFamily}

    def test_every_registry_value_is_stub_with_steps(self):
        """FR-015: every registry value status='stub' with non-empty steps."""
        for family, entry in WORKFLOW_REGISTRY.items():
            assert entry["status"] == "stub", f"{family} must ship as a stub in v2"
            assert entry["steps"], f"{family} must carry non-empty steps"


class TestSourcePins:
    """D4 / FR-015 source pins — the load-bearing invariants live in CI, not the spec."""

    def _source(self) -> str:
        return inspect.getsource(wr)

    def test_no_starter_tasks_reference(self):
        """The silent generic fallback is structurally unreachable."""
        assert "STARTER_TASKS" not in self._source()

    def test_no_reclassify_imports(self):
        """No subprocess / agent-dispatch / classifier / LLM-client in the resolver.

        Targets the import/dispatch tokens themselves (not docstring prose, which is
        free to *describe* what the module avoids) — same mechanism as the
        STARTER_TASKS pin, just scoped to import-form so it can't false-positive on
        the module's own no-reclassify contract statement.
        """
        src = self._source()
        for forbidden in (
            "import subprocess",
            "cast_goal_classifier",
            "/trigger",
            "import anthropic",
            "from anthropic",
            "import openai",
            "from openai",
        ):
            assert forbidden not in src, f"resolver must not reference {forbidden!r}"


class TestRecordRoutingDecision:
    """record_routing_decision — the ONLY writer; idempotent; best-effort yaml."""

    def test_first_record_reports_recorded_not_changed(self, tmp_path):
        db_path, goals_dir, _ = _init_db_and_create_goal(tmp_path)
        result = wr.record_routing_decision(
            "my-goal", "bug_fix", wr.resolve("bug_fix"),
            goals_dir=goals_dir, db_path=db_path,
        )
        assert result["recorded"] is True
        assert result["changed"] is False
        assert result["previous_family"] is None
        assert result["routing_handle"] == "bug_fix:stub"
        assert "routed_at" in result

        row = _row(db_path, "my-goal")
        assert row["workflow_family"] == "bug_fix"
        assert row["routing_handle"] == "bug_fix:stub"
        assert row["routed_at"]

    def test_idempotent_rerecord_is_noop_routed_at_unchanged(self, tmp_path):
        db_path, goals_dir, _ = _init_db_and_create_goal(tmp_path)
        wr.record_routing_decision(
            "my-goal", "bug_fix", wr.resolve("bug_fix"),
            goals_dir=goals_dir, db_path=db_path,
        )
        first_routed_at = _row(db_path, "my-goal")["routed_at"]

        result = wr.record_routing_decision(
            "my-goal", "bug_fix", wr.resolve("bug_fix"),
            goals_dir=goals_dir, db_path=db_path,
        )
        assert result["recorded"] is False
        assert result["changed"] is False
        assert _row(db_path, "my-goal")["routed_at"] == first_routed_at

    def test_change_path_reports_changed_and_previous_family(self, tmp_path):
        db_path, goals_dir, _ = _init_db_and_create_goal(tmp_path)
        wr.record_routing_decision(
            "my-goal", "bug_fix", wr.resolve("bug_fix"),
            goals_dir=goals_dir, db_path=db_path,
        )
        result = wr.record_routing_decision(
            "my-goal", "data_analysis", wr.resolve("data_analysis"),
            goals_dir=goals_dir, db_path=db_path,
        )
        assert result["recorded"] is True
        assert result["changed"] is True
        assert result["previous_family"] == "bug_fix"

        row = _row(db_path, "my-goal")
        assert row["workflow_family"] == "data_analysis"
        assert row["routing_handle"] == "data_analysis:stub"

    def test_goal_yaml_round_trip(self, tmp_path):
        db_path, goals_dir, goal_dir = _init_db_and_create_goal(tmp_path)
        wr.record_routing_decision(
            "my-goal", "bug_fix", wr.resolve("bug_fix"),
            goals_dir=goals_dir, db_path=db_path,
        )
        data = yaml.safe_load((goal_dir / "goal.yaml").read_text())
        assert data["workflow_family"] == "bug_fix"
        assert data["routing_handle"] == "bug_fix:stub"

    def test_missing_goal_yaml_records_without_raising(self, tmp_path):
        """D5: a goal whose goal.yaml is absent still writes the DB row, no raise."""
        db_path, goals_dir, goal_dir = _init_db_and_create_goal(tmp_path)
        (goal_dir / "goal.yaml").unlink()

        result = wr.record_routing_decision(
            "my-goal", "bug_fix", wr.resolve("bug_fix"),
            goals_dir=goals_dir, db_path=db_path,
        )
        assert result["recorded"] is True
        assert _row(db_path, "my-goal")["workflow_family"] == "bug_fix"
        assert not (goal_dir / "goal.yaml").exists()


class TestRecordGuards:
    """ValueError guards — non-routable handles and unknown slugs are refused."""

    def test_needs_classification_handle_raises(self, tmp_path):
        db_path, goals_dir, _ = _init_db_and_create_goal(tmp_path)
        with pytest.raises(ValueError):
            wr.record_routing_decision(
                "my-goal", "bug_fix", wr.resolve(None),
                goals_dir=goals_dir, db_path=db_path,
            )

    def test_unmatched_handle_raises(self, tmp_path):
        db_path, goals_dir, _ = _init_db_and_create_goal(tmp_path)
        with pytest.raises(ValueError):
            wr.record_routing_decision(
                "my-goal", "nonsense", wr.resolve("nonsense"),
                goals_dir=goals_dir, db_path=db_path,
            )

    def test_unknown_family_raises(self, tmp_path):
        db_path, goals_dir, _ = _init_db_and_create_goal(tmp_path)
        # A status that is routable but a family not in the registry.
        handle = wr.WorkflowHandle("not_a_family", "stub", steps=("x",))
        with pytest.raises(ValueError):
            wr.record_routing_decision(
                "my-goal", "not_a_family", handle,
                goals_dir=goals_dir, db_path=db_path,
            )

    def test_unknown_slug_raises(self, tmp_path):
        db_path, goals_dir, _ = _init_db_and_create_goal(tmp_path)
        with pytest.raises(ValueError):
            wr.record_routing_decision(
                "ghost-goal", "bug_fix", wr.resolve("bug_fix"),
                goals_dir=goals_dir, db_path=db_path,
            )
