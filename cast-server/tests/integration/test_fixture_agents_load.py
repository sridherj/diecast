"""Verify all four delegation fixtures load via the public ``load_agent_config`` seam."""
from __future__ import annotations

import pytest

from cast_server.models.agent_config import load_agent_config


FIXTURES = [
    ("cast-test-parent-delegator", "http", ["cast-test-child-worker", "cast-test-child-worker-subagent"]),
    ("cast-test-child-worker", "http", []),
    ("cast-test-child-worker-subagent", "subagent", []),
    ("cast-test-delegation-denied", "http", ["cast-test-child-worker"]),
]


@pytest.mark.parametrize("name,dispatch_mode,allowed_delegations", FIXTURES)
def test_fixture_loads_with_expected_shape(name, dispatch_mode, allowed_delegations):
    cfg = load_agent_config(name)
    assert cfg.dispatch_mode == dispatch_mode, f"{name} dispatch_mode mismatch"
    assert list(cfg.allowed_delegations) == allowed_delegations, f"{name} allowed_delegations mismatch"
    assert cfg.model == "haiku", f"{name} expected model: haiku"
