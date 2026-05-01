# sp1.3 — Conftest Wiring (`CAST_TEST_AGENTS_DIR` + `_config_cache.clear()`)

> **Pre-requisite:** Read `goals/child-delegation-integration-tests/execution/_shared_context.md` first.

## Objective

Wire the existing `CAST_TEST_AGENTS_DIR` seam via conftest so T1 resolves all four
fixtures via `load_agent_config(name)` and tests have isolated cache state. T2's
spawned cast-server inherits the env var so live registry includes the fixtures.

This is a small one-liner-style sub-phase, not a code change to production paths.

## Dependencies

- **Requires completed:** sp1.1 (seam confirmed), sp1.2 (fixture configs exist).
- **Assumed codebase state:** seam is at `agent_config.py` per sp1.1 note;
  four config.yaml files exist on disk per sp1.2.

## Scope

**In scope:**
- Create `cast-server/tests/integration/conftest.py` with two autouse fixtures:
  session-scoped env var setter and per-test `_config_cache.clear()`.
- Author the verification test
  `cast-server/tests/integration/test_fixture_agents_load.py`.
- Note the same env-var hand-off mechanism for T2 (used in sp5.1's
  `cast-server/tests/e2e/conftest.py`).

**Out of scope (do NOT do these):**
- Modifying production code (`agent_config.py`, `agent_service.py`).
- Introducing new env vars. The existing seam is the locked decision.
- Authoring T2 conftest — that's sp5.1.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/integration/conftest.py` | Create or extend | Likely does not exist |
| `cast-server/tests/integration/__init__.py` | Create if missing | Likely does not exist |
| `cast-server/tests/integration/test_fixture_agents_load.py` | Create | Does not exist |

## Detailed Steps

### Step 1.3.1: Author the conftest

```python
# cast-server/tests/integration/conftest.py
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
INTEGRATION_AGENTS_DIR = REPO_ROOT / "cast-server" / "tests" / "integration" / "agents"


@pytest.fixture(scope="session", autouse=True)
def _set_test_agents_dir():
    """Point `_candidate_config_paths` at the integration fixture directory.

    Uses os.environ directly (not monkeypatch) because monkeypatch is function-scoped.
    Cleanup on session teardown.
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
    """Clear the mtime-keyed config cache between tests (Review #3 belt-and-suspenders).

    Tests should still prefer monkeypatching `load_agent_config` for non-fixture
    configs; this is the safety net for anything that slips through.
    """
    from cast_server.models import agent_config
    agent_config._config_cache.clear()
    yield
    agent_config._config_cache.clear()
```

### Step 1.3.2: Create `__init__.py` if needed

If `cast-server/tests/integration/__init__.py` does not exist, create it as an empty
file. Pytest discovery may need it depending on the project's pytest config.

### Step 1.3.3: Author `test_fixture_agents_load.py`

```python
# cast-server/tests/integration/test_fixture_agents_load.py
"""Verify all four delegation fixtures load via the public `load_agent_config` seam."""
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
```

### Step 1.3.4: Document the T2 hand-off

Add a comment block at the top of `conftest.py`:

```python
# T2 hand-off: cast-server/tests/e2e/conftest.py (sp5.1) MUST export
# CAST_TEST_AGENTS_DIR into the spawned cast-server subprocess env so the
# running registry includes the four fixtures via get_all_agents() merge.
```

## Verification

### Automated Tests (permanent)

```
pytest cast-server/tests/integration/test_fixture_agents_load.py -v
```
Must exit 0 with 4 parametrized cases passing.

### Validation Scripts (temporary)

```bash
CAST_TEST_AGENTS_DIR=$(pwd)/cast-server/tests/integration/agents \
  python -c "from cast_server.models.agent_config import load_agent_config; \
             [print(load_agent_config(n).dispatch_mode) for n in \
              ['cast-test-parent-delegator','cast-test-child-worker', \
               'cast-test-child-worker-subagent','cast-test-delegation-denied']]"
```
Expected: four lines printing `http`, `http`, `subagent`, `http`.

### Manual Checks

- Confirm `_set_test_agents_dir` is session-scoped + autouse.
- Confirm `_clear_agent_config_cache` is function-scoped + autouse.

### Success Criteria

- [ ] `conftest.py` exists with both autouse fixtures.
- [ ] `test_fixture_agents_load.py` passes (4 parametrized cases).
- [ ] T2 hand-off comment present in conftest.
- [ ] No production code touched.
- [ ] Risk #2 ("registry-discovery seam doesn't have a clean test-fixture-dir hook")
      explicitly retired in the verification note.

## Execution Notes

- **Spec-linked files:** none touched directly. Cross-reference shared context
  for the locked decision on `CAST_TEST_AGENTS_DIR`.
- The autouse cache-clear is belt-and-suspenders. The primary cache-isolation
  pattern in sp2.x is `monkeypatch.setattr(agent_service, "load_agent_config", ...)`.
- If pytest collection complains about the conftest scope, the project may have a
  pre-existing root conftest — check `cast-server/tests/conftest.py` first to
  avoid collisions.
