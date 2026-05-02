"""Integration-suite conftest for child-delegation tests.

Wires the existing ``CAST_TEST_AGENTS_DIR`` seam (see
``cast_server.models.agent_config._candidate_config_paths``) so the four
delegation fixtures under ``cast-server/tests/integration/agents/`` resolve
through the public ``load_agent_config`` entrypoint, and provides a
per-test ``_config_cache.clear()`` safety net.

T2 hand-off: ``cast-server/tests/e2e/conftest.py`` (sp5.1) MUST export
``CAST_TEST_AGENTS_DIR`` into the spawned cast-server subprocess env so the
running registry includes the four fixtures via ``get_all_agents()`` merge.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
INTEGRATION_AGENTS_DIR = REPO_ROOT / "cast-server" / "tests" / "integration" / "agents"


@pytest.fixture(scope="session", autouse=True)
def _set_test_agents_dir():
    """Point ``_candidate_config_paths`` at the integration fixture directory.

    Uses ``os.environ`` directly because ``monkeypatch`` is function-scoped
    and this fixture must persist for the whole session. Cleanup on
    teardown restores any prior value.
    """
    prev = os.environ.get("CAST_TEST_AGENTS_DIR")
    os.environ["CAST_TEST_AGENTS_DIR"] = str(INTEGRATION_AGENTS_DIR)
    try:
        yield
    finally:
        if prev is None:
            os.environ.pop("CAST_TEST_AGENTS_DIR", None)
        else:
            os.environ["CAST_TEST_AGENTS_DIR"] = prev


@pytest.fixture(autouse=True)
def _clear_agent_config_cache():
    """Belt-and-suspenders cache clear between tests.

    The primary cache-isolation pattern in sp2.x is
    ``monkeypatch.setattr(agent_service, "load_agent_config", ...)``; this
    autouse fixture is the safety net for anything that slips through.
    """
    from cast_server.models import agent_config

    agent_config._config_cache.clear()
    yield
    agent_config._config_cache.clear()
