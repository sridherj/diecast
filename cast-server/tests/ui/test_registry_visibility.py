"""Meta-test: SC-003 registry visibility gate.

Verifies the `CAST_TEST_AGENTS_DIR` env-var merge in
`cast_server.services.agent_service.get_all_agents`:

* Dev calls (env unset) MUST return zero `cast-ui-test-*` entries.
* Calls with the env var set MUST return all 9 expected test-agent names
  alongside the production registry.
* On a name collision the production entry MUST win and a warning MUST be logged.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cast_server.services import agent_service
from cast_server.services.agent_service import get_all_agents

EXPECTED_TEST_AGENTS = [
    "cast-ui-test-orchestrator",
    "cast-ui-test-dashboard",
    "cast-ui-test-agents",
    "cast-ui-test-runs",
    "cast-ui-test-scratchpad",
    "cast-ui-test-goal-detail",
    "cast-ui-test-focus",
    "cast-ui-test-about",
    "cast-ui-test-noop",
]


def _make_stub_agent(parent: Path, name: str) -> None:
    d = parent / name
    d.mkdir(parents=True)
    (d / f"{name}.md").write_text(
        f"---\nname: {name}\ndescription: stub\n---\n# {name}\nstub instructions\n"
    )
    (d / "config.yaml").write_text(f"name: {name}\nentrypoint: stub\n")


@pytest.fixture(autouse=True)
def _reset_registry_cache():
    """Clear the per-root mtime cache so tests don't see stale fixture data."""
    agent_service._AGENT_REGISTRY_CACHE.clear()
    yield
    agent_service._AGENT_REGISTRY_CACHE.clear()


def _names(registry: list[dict]) -> list[str]:
    return [agent["name"] for agent in registry]


def test_dev_registry_excludes_test_agents(isolated_db, monkeypatch):
    monkeypatch.delenv("CAST_TEST_AGENTS_DIR", raising=False)
    registry = get_all_agents(db_path=isolated_db)
    leaked = [n for n in _names(registry) if n.startswith("cast-ui-test-")]
    assert leaked == [], f"Test agents leaked into prod registry: {leaked}"


def test_test_registry_includes_test_agents(isolated_db, tmp_path, monkeypatch):
    for name in EXPECTED_TEST_AGENTS:
        _make_stub_agent(tmp_path, name)
    monkeypatch.setenv("CAST_TEST_AGENTS_DIR", str(tmp_path))

    registry = get_all_agents(db_path=isolated_db)
    names = _names(registry)
    for name in EXPECTED_TEST_AGENTS:
        assert name in names, f"Missing {name} in merged registry"


def test_production_collision_prefers_prod(isolated_db, tmp_path, monkeypatch, caplog):
    monkeypatch.delenv("CAST_TEST_AGENTS_DIR", raising=False)
    prod_names = _names(get_all_agents(db_path=isolated_db))
    if not prod_names:
        pytest.skip("No production agents available for collision test")
    collision_name = prod_names[0]

    _make_stub_agent(tmp_path, collision_name)
    monkeypatch.setenv("CAST_TEST_AGENTS_DIR", str(tmp_path))

    with caplog.at_level("WARNING", logger="cast_server.services.agent_service"):
        merged = get_all_agents(db_path=isolated_db)

    assert collision_name in _names(merged)

    matching = [a for a in merged if a["name"] == collision_name]
    assert len(matching) == 1
    # Production entry wins — its source_root must NOT be the temp dir.
    assert matching[0]["source_root"] != str(tmp_path.resolve())

    assert any("collides" in rec.message for rec in caplog.records), (
        "Expected a collision warning but none was logged: "
        f"{[rec.message for rec in caplog.records]}"
    )
