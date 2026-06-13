"""Wiring pins for the `cast-refine-requirements` routing tail (Phase 3b, sp4a).

sp4a appends a routing call to the tail of Step 0: after the family is confirmed and merged via
``merge_front_matter``, the prompt POSTs to ``/api/goals/{slug}/route`` (the single door) so the
service — never the agent — writes the goal columns. These pins make that wiring a CI invariant:

- the prompt cites the **endpoint**, not a direct DB write (single-writer discipline);
- the routing call sits **after** the ``merge_front_matter`` step (recipe order);
- the read-only ``/cast-router`` companion ships subagent-mode with no delegations.

Precedent: ``test_goal_classifier_prompt.py`` (prompt-section pins). REPO_ROOT is ``parents[2]``
from ``cast-server/tests/`` — [0]=tests, [1]=cast-server, [2]=repo.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
REFINE_PROMPT = REPO_ROOT / "agents" / "cast-refine-requirements" / "cast-refine-requirements.md"
ROUTER_PROMPT = REPO_ROOT / "agents" / "cast-router" / "cast-router.md"
ROUTER_CONFIG = REPO_ROOT / "agents" / "cast-router" / "config.yaml"


@pytest.fixture(scope="module")
def refine_text() -> str:
    return REFINE_PROMPT.read_text(encoding="utf-8")


def test_refine_prompt_cites_route_endpoint(refine_text: str) -> None:
    """Step 0 tail must POST to the single door, not write columns directly."""
    assert "/api/goals/{slug}/route" in refine_text, (
        "routing tail must cite POST /api/goals/{slug}/route — the single writer-of-record door"
    )


def test_routing_call_comes_after_merge_front_matter(refine_text: str) -> None:
    """Recipe order: route only after the family is confirmed and merged."""
    mf = refine_text.rfind("merge_front_matter")
    route = refine_text.find("/api/goals/{slug}/route")
    assert mf != -1 and route != -1
    assert route > mf, "the routing curl must appear AFTER the merge_front_matter step"


def test_refine_prompt_has_no_direct_db_write(refine_text: str) -> None:
    """Single-writer discipline: the agent never touches the goal columns/SQLite directly."""
    assert not re.search(r"UPDATE goals|workflow_family\s*=|sqlite", refine_text, re.IGNORECASE), (
        "refine prompt must not write the goal columns directly — the service owns that write"
    )


def test_cast_router_ships_read_only() -> None:
    """The companion resolver ships subagent-mode with NO allowed_delegations (read-only)."""
    assert ROUTER_PROMPT.is_file(), f"missing {ROUTER_PROMPT}"
    config = ROUTER_CONFIG.read_text(encoding="utf-8")
    assert "dispatch_mode: subagent" in config
    assert not re.search(r"^\s*allowed_delegations:", config, re.MULTILINE), (
        "/cast-router is read-only by contract — it must declare no allowed_delegations"
    )
