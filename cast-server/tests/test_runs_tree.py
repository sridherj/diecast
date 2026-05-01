"""Unit tests for ``get_runs_tree`` (sp1 of runs-threaded-tree).

Covers tree assembly, rollups (descendant_count, failed_descendant_count,
total_cost_usd, status_rollup, ctx_class, wall_duration_seconds), rework
detection + ancestor propagation, depth cap with server-side warning, and
the rollup-aware status filter (Decision #13).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CAST_SERVER_DIR = REPO_ROOT / "cast-server"
if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))

from cast_server.services.agent_service import (  # noqa: E402
    _STATUS_SEVERITY,
    get_runs_tree,
)


def _by_id(runs: list[dict]) -> dict[str, dict]:
    """Flatten a tree to id → node for easy lookups in assertions."""
    out: dict[str, dict] = {}

    def walk(node: dict) -> None:
        out[node["id"]] = node
        for child in node.get("children", []):
            walk(child)

    for r in runs:
        walk(r)
    return out


def _l1_ids(result: dict) -> list[str]:
    return [r["id"] for r in result["runs"]]


def test_returns_only_l1_at_top_level(seeded_runs_tree):
    actual_result = get_runs_tree(db_path=seeded_runs_tree, exclude_test=False)
    expected_l1_ids = {"happy-l1", "preso-l1", "deep-l1", "leaf-l1"}
    assert set(_l1_ids(actual_result)) == expected_l1_ids
    # No top-level entry should have a parent_run_id set.
    for r in actual_result["runs"]:
        assert not r.get("parent_run_id")


def test_children_attached_recursively(seeded_runs_tree):
    result = get_runs_tree(db_path=seeded_runs_tree, exclude_test=False)
    flat = _by_id(result["runs"])
    # 4-deep chain: L1 → L2 → L3 → L4 must all be reachable.
    l1 = flat["deep-l1"]
    assert [c["id"] for c in l1["children"]] == ["deep-l2"]
    assert [c["id"] for c in l1["children"][0]["children"]] == ["deep-l3"]
    assert [c["id"] for c in l1["children"][0]["children"][0]["children"]] == ["deep-l4"]


def test_children_ordered_by_created_at_asc(seeded_runs_tree):
    result = get_runs_tree(db_path=seeded_runs_tree, exclude_test=False)
    flat = _by_id(result["runs"])
    # happy-l1 children were seeded with strictly increasing created_at:
    # happy-c1 (us=1), happy-c2 (us=2), happy-c3 (us=3).
    assert [c["id"] for c in flat["happy-l1"]["children"]] == [
        "happy-c1", "happy-c2", "happy-c3",
    ]


def test_descendant_count_is_subtree_size(seeded_runs_tree):
    result = get_runs_tree(db_path=seeded_runs_tree, exclude_test=False)
    flat = _by_id(result["runs"])
    # deep-l1 has 3 descendants (l2, l3, l4); excludes self.
    assert flat["deep-l1"]["descendant_count"] == 3
    assert flat["deep-l2"]["descendant_count"] == 2
    assert flat["deep-l4"]["descendant_count"] == 0
    # leaf-l1 has zero descendants.
    assert flat["leaf-l1"]["descendant_count"] == 0


def test_failed_descendant_count_includes_stuck(seeded_runs_tree):
    result = get_runs_tree(db_path=seeded_runs_tree, exclude_test=False)
    flat = _by_id(result["runs"])
    # happy-l1 has one failed grandchild (happy-gc1) → count = 1.
    assert flat["happy-l1"]["failed_descendant_count"] == 1
    # preso-l1 has one failed L2 (preso-cc1) → count = 1.
    assert flat["preso-l1"]["failed_descendant_count"] == 1
    # leaf has none.
    assert flat["leaf-l1"]["failed_descendant_count"] == 0


def test_total_cost_includes_self_and_descendants(seeded_runs_tree):
    result = get_runs_tree(db_path=seeded_runs_tree, exclude_test=False)
    flat = _by_id(result["runs"])
    # happy-l1: 0.10 + 0.02 + 0.03 + 0.01 + 0.005 = 0.165
    assert flat["happy-l1"]["total_cost_usd"] == pytest.approx(0.165)
    # leaf has only its own cost.
    assert flat["leaf-l1"]["total_cost_usd"] == pytest.approx(0.01)


def test_wall_duration_seconds_l1_only(seeded_runs_tree):
    result = get_runs_tree(db_path=seeded_runs_tree, exclude_test=False)
    flat = _by_id(result["runs"])
    # happy-l1 spans 42 s wall-clock per the fixture.
    assert flat["happy-l1"]["wall_duration_seconds"] == 42
    # Children must NOT have wall_duration_seconds set.
    assert "wall_duration_seconds" not in flat["happy-c1"]


def test_status_rollup_is_max_severity(seeded_runs_tree):
    result = get_runs_tree(db_path=seeded_runs_tree, exclude_test=False)
    flat = _by_id(result["runs"])
    # happy-l1 (completed) has a failed grandchild → rollup = 'failed'.
    assert flat["happy-l1"]["status_rollup"] == "failed"
    # leaf-l1 (no descendants) → rollup matches own status.
    assert flat["leaf-l1"]["status_rollup"] == "completed"
    # Severity ordering pinned literally.
    assert _STATUS_SEVERITY["failed"] > _STATUS_SEVERITY["stuck"]
    assert _STATUS_SEVERITY["stuck"] > _STATUS_SEVERITY["rate_limited"]
    assert _STATUS_SEVERITY["rate_limited"] > _STATUS_SEVERITY["running"]
    assert _STATUS_SEVERITY["running"] > _STATUS_SEVERITY["pending"]
    assert _STATUS_SEVERITY["pending"] > _STATUS_SEVERITY["scheduled"]
    assert _STATUS_SEVERITY["scheduled"] > _STATUS_SEVERITY["completed"]


def test_ctx_class_low_mid_high_buckets(seeded_runs_tree):
    result = get_runs_tree(db_path=seeded_runs_tree, exclude_test=False)
    flat = _by_id(result["runs"])
    # happy-c1: 30k/200k = 15% → low
    assert flat["happy-c1"]["ctx_class"] == "low"
    # happy-c2: 100k/200k = 50% → mid
    assert flat["happy-c2"]["ctx_class"] == "mid"
    # happy-c3: 160k/200k = 80% → high
    assert flat["happy-c3"]["ctx_class"] == "high"


def test_ctx_class_none_when_context_usage_missing(seeded_runs_tree):
    result = get_runs_tree(db_path=seeded_runs_tree, exclude_test=False)
    flat = _by_id(result["runs"])
    # happy-l1 has no context_usage column populated.
    assert flat["happy-l1"]["ctx_class"] is None


def test_rework_detection_consecutive_siblings_same_agent_task(seeded_runs_tree):
    result = get_runs_tree(db_path=seeded_runs_tree, exclude_test=False)
    flat = _by_id(result["runs"])
    # preso-cc1 is the FIRST instance (not rework); preso-cc2 is rework #2.
    assert flat["preso-cc1"]["is_rework"] is False
    assert flat["preso-cc2"]["is_rework"] is True
    assert flat["preso-cc2"]["rework_index"] == 2


def test_rework_index_increments_per_repeat(seeded_runs_tree):
    result = get_runs_tree(db_path=seeded_runs_tree, exclude_test=False)
    flat = _by_id(result["runs"])
    # Under preso-cc2: preso-l3a is the original, preso-l3b is rework #2.
    assert flat["preso-l3a"]["is_rework"] is False
    assert flat["preso-l3b"]["is_rework"] is True
    assert flat["preso-l3b"]["rework_index"] == 2


def test_rework_count_propagates_to_all_ancestors(seeded_runs_tree):
    result = get_runs_tree(db_path=seeded_runs_tree, exclude_test=False)
    flat = _by_id(result["runs"])
    # preso-l1 has 1 L2 rework (preso-cc2) + 1 L3 rework (preso-l3b) = 2.
    assert flat["preso-l1"]["rework_count"] == 2
    # preso-cc2 has 1 L3 rework underneath.
    assert flat["preso-cc2"]["rework_count"] == 1
    # Trees with no reworks must surface 0, not None.
    assert flat["leaf-l1"]["rework_count"] == 0
    assert flat["happy-l1"]["rework_count"] == 0


def test_pagination_by_l1_only(seeded_runs_tree):
    # 4 L1s seeded; per_page=2 → 2 pages.
    page1 = get_runs_tree(db_path=seeded_runs_tree, page=1, per_page=2,
                          exclude_test=False)
    page2 = get_runs_tree(db_path=seeded_runs_tree, page=2, per_page=2,
                          exclude_test=False)
    assert page1["total"] == 4
    assert page1["pages"] == 2
    assert len(page1["runs"]) == 2
    assert len(page2["runs"]) == 2
    # No L2/L3 leaks into a page's L1 list.
    page1_ids = set(_l1_ids(page1)) | set(_l1_ids(page2))
    assert page1_ids == {"happy-l1", "preso-l1", "deep-l1", "leaf-l1"}


def test_status_filter_uses_status_rollup(seeded_runs_tree):
    # happy-l1 itself is completed, but its grandchild is failed →
    # status_filter='failed' must include it (Decision #13).
    result = get_runs_tree(db_path=seeded_runs_tree, status_filter="failed",
                           exclude_test=False)
    ids = set(_l1_ids(result))
    assert "happy-l1" in ids
    assert "preso-l1" in ids   # has a failed L2
    assert "leaf-l1" not in ids
    assert "deep-l1" not in ids


def test_exclude_test_filter_works(isolated_db):
    """Rows whose agent_name starts with 'test' are filtered when exclude_test=True."""
    from tests.conftest import _seed_run

    _seed_run(isolated_db, run_id="real-l1", agent_name="cast-orchestrate")
    _seed_run(isolated_db, run_id="test-l1", agent_name="test-fake-agent")

    excluded = get_runs_tree(db_path=isolated_db, exclude_test=True)
    included = get_runs_tree(db_path=isolated_db, exclude_test=False)

    assert {r["id"] for r in excluded["runs"]} == {"real-l1"}
    assert {r["id"] for r in included["runs"]} == {"real-l1", "test-l1"}


def test_empty_db_returns_empty(empty_db):
    result = get_runs_tree(db_path=empty_db, exclude_test=False)
    assert result["runs"] == []
    assert result["total"] == 0
    assert result["page"] == 1
    assert result["pages"] == 1


def test_l1_with_no_children_has_descendant_count_zero(seeded_runs_tree):
    result = get_runs_tree(db_path=seeded_runs_tree, exclude_test=False)
    flat = _by_id(result["runs"])
    leaf = flat["leaf-l1"]
    assert leaf["descendant_count"] == 0
    assert leaf["failed_descendant_count"] == 0
    assert leaf["children"] == []


def test_depth_cap_truncates_at_10(deep_chain_db, caplog):
    """A 12-deep linear chain returns at most 11 nodes (depths 0..10)."""
    with caplog.at_level(logging.WARNING,
                         logger="cast_server.services.agent_service"):
        result = get_runs_tree(db_path=deep_chain_db, exclude_test=False)

    assert len(result["runs"]) == 1
    flat = _by_id(result["runs"])

    # The recursive CTE allows depths 0..10 (11 levels). The 12th node is cut.
    max_id = max(int(rid.split("l")[1]) for rid in flat)
    assert max_id <= 10, f"expected max depth ≤ 10, got chain-l{max_id}"

    # Server-side warning was logged because depth-10 nodes have children.
    assert any("tree truncated" in rec.message for rec in caplog.records)
