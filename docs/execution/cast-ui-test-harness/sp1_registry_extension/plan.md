# Sub-phase 1: Registry env-var merge + visibility meta-test

> **Pre-requisite:** Read `docs/execution/cast-ui-test-harness/_shared_context.md` before starting.

## Objective

Extend `get_all_agents()` in `cast-server/cast_server/services/agent_service.py` so that when
the env var `CAST_TEST_AGENTS_DIR` is set, the function ALSO loads agents from that directory
and merges them into the production registry. The production code path (env var unset) MUST
remain bit-identical — no extra walks, no env var reads in the cache hot path.

Add a fast meta-test (`test_registry_visibility.py`, <1s, no browser) that gates the
SC-003 success criterion: dev calls return zero `cast-ui-test-*` entries; calls with the
env var set return all 9 expected names.

This sub-phase is foundational and ships the smallest, easiest-to-review change in the plan.

## Dependencies
- **Requires completed:** None.
- **Assumed codebase state:** `agent_service.py` is unchanged from main. `cast-server/tests/`
  is the existing test root.

## Scope

**In scope:**
- Extend `get_all_agents()` (around `agent_service.py:1191`) to merge a second registry
  when `CAST_TEST_AGENTS_DIR` is set.
- Preserve the existing single-root caching behavior of `_load_agent_registry()` (around line :1148).
- Implement collision policy: log a warning and prefer the production entry.
- Create `cast-server/tests/ui/__init__.py` and `cast-server/tests/ui/test_registry_visibility.py`.
- The meta-test creates a temporary directory containing 9 stub agent dirs (each with a minimal
  `<name>.md` and `config.yaml`) and asserts the registry merge.

**Out of scope (do NOT do these):**
- Do NOT modify `_load_agent_registry()` to take multiple roots; merge happens at the
  `get_all_agents` call site.
- Do NOT add the env var read inside `_load_agent_registry`'s cache hot path.
- Do NOT modify `cast-server/tests/conftest.py` (the existing one) — the new UI test conftest
  is sp2's deliverable. (`__init__.py` for `cast-server/tests/ui/` is fine.)
- Do NOT create `runner.py`, agent definitions, or any Playwright code here.
- Do NOT touch `pyproject.toml`.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/services/agent_service.py` | Modify | `get_all_agents` at :1191 calls `_load_agent_registry` once. |
| `cast-server/tests/ui/__init__.py` | Create | Does not exist. Empty file. |
| `cast-server/tests/ui/test_registry_visibility.py` | Create | Does not exist. |

## Detailed Steps

### Step 1.1: Read the current implementation

Open `cast-server/cast_server/services/agent_service.py` and read lines 1140-1230 to confirm
the exact shape of `_load_agent_registry()` and `get_all_agents()`. The line numbers in the
plan are approximate — match by symbol name, not line.

Key things to confirm before editing:
- The signature of `_load_agent_registry()` (does it take a root path or read it from config?)
- How `get_all_agents()` currently obtains the production root.
- Whether there's an existing module-level cache dict and what its key shape is.

### Step 1.2: Extend `get_all_agents()` with the env-var merge

Implement merging at the `get_all_agents()` call site. Pseudocode:

```python
import os
import logging
log = logging.getLogger(__name__)

def get_all_agents() -> dict[str, AgentDefinition]:
    prod_registry = _load_agent_registry(<production_root>)
    test_dir = os.environ.get("CAST_TEST_AGENTS_DIR")
    if not test_dir:
        return prod_registry  # bit-identical to today
    test_registry = _load_agent_registry(Path(test_dir))
    merged: dict[str, AgentDefinition] = {}
    for name, agent in test_registry.items():
        merged[name] = agent
    for name, agent in prod_registry.items():
        if name in merged:
            log.warning(
                "Test agent %r collides with production agent of the same name; "
                "preferring production entry.", name,
            )
        merged[name] = agent  # production wins on collision
    return merged
```

**Critical:** keep the early-return when the env var is unset so the production path runs
exactly the same code as today. The test root MUST be loaded through the same
`_load_agent_registry` function so its mtime cache works automatically (one cache keyed by
absolute root path → independent caches per root, naturally).

**If `_load_agent_registry` is not currently keyed by root path:** adapt it minimally so the
cache key is the resolved absolute root (`Path(root).resolve()`). Verify this does not
regress the current single-root caller.

### Step 1.3: Create the UI test package marker

Create `cast-server/tests/ui/__init__.py` as an empty file. This makes `cast-server/tests/ui/`
a package so pytest discovers tests there.

### Step 1.4: Write `test_registry_visibility.py`

Create `cast-server/tests/ui/test_registry_visibility.py`. Use `pytest`'s `tmp_path` and
`monkeypatch` fixtures.

Test outline:

```python
import os
from pathlib import Path
import pytest

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
    (d / f"{name}.md").write_text(f"# {name}\nstub instructions\n")
    (d / "config.yaml").write_text(f"name: {name}\nentrypoint: stub\n")


def test_dev_registry_excludes_test_agents(monkeypatch):
    monkeypatch.delenv("CAST_TEST_AGENTS_DIR", raising=False)
    registry = get_all_agents()
    leaked = [n for n in registry if n.startswith("cast-ui-test-")]
    assert leaked == [], f"Test agents leaked into prod registry: {leaked}"


def test_test_registry_includes_test_agents(tmp_path, monkeypatch):
    for name in EXPECTED_TEST_AGENTS:
        _make_stub_agent(tmp_path, name)
    monkeypatch.setenv("CAST_TEST_AGENTS_DIR", str(tmp_path))

    registry = get_all_agents()
    for name in EXPECTED_TEST_AGENTS:
        assert name in registry, f"Missing {name} in merged registry"


def test_production_collision_prefers_prod(tmp_path, monkeypatch, caplog):
    # Create one stub with a colliding production name (use any real prod name available).
    # If determining a real prod name dynamically is fragile, use a known stable name from
    # an existing agent dir — read one off `get_all_agents()` first with env unset.
    monkeypatch.delenv("CAST_TEST_AGENTS_DIR", raising=False)
    prod_names = list(get_all_agents().keys())
    assert prod_names, "Expected at least one prod agent for collision test"
    collision_name = prod_names[0]

    _make_stub_agent(tmp_path, collision_name)
    monkeypatch.setenv("CAST_TEST_AGENTS_DIR", str(tmp_path))

    with caplog.at_level("WARNING"):
        merged = get_all_agents()

    assert collision_name in merged
    # Production entry wins — the merged value's instruction file or config should match prod,
    # not the stub. A robust check: the merged agent's source path (if exposed) is NOT tmp_path.
    # If AgentDefinition exposes `source_path`/`directory`/etc, assert it's not under tmp_path.
    # Otherwise, settle for the warning being logged.
    assert any("collides" in rec.message for rec in caplog.records)
```

Adjust attribute names (`source_path`, etc.) to match the real `AgentDefinition` shape — check
the dataclass at the top of `agent_service.py` first.

### Step 1.5: Run the meta-test locally

```bash
cd /home/sridherj/workspace/diecast
pytest cast-server/tests/ui/test_registry_visibility.py -v
```

Expect three tests passing in <1s. If `test_production_collision_prefers_prod` is flaky
because the prod registry happens to be empty in some configurations, gate it with
`@pytest.mark.skipif` on `not prod_names`.

## Verification

### Automated Tests (permanent)

- `cast-server/tests/ui/test_registry_visibility.py::test_dev_registry_excludes_test_agents`
- `cast-server/tests/ui/test_registry_visibility.py::test_test_registry_includes_test_agents`
- `cast-server/tests/ui/test_registry_visibility.py::test_production_collision_prefers_prod`

All three must pass with the `cast_server` package importable. None of them should require
a running server, a browser, or Playwright.

### Validation Scripts (temporary)

```bash
# Confirm the production path is unchanged when env var is unset.
unset CAST_TEST_AGENTS_DIR
python -c "from cast_server.services.agent_service import get_all_agents; \
           names = sorted(get_all_agents().keys()); \
           print(len(names), 'agents'); print('\n'.join(names))"

# Confirm the merge picks up a temp dir.
mkdir -p /tmp/diecast-merge-check/cast-ui-test-noop
echo "# noop" > /tmp/diecast-merge-check/cast-ui-test-noop/cast-ui-test-noop.md
echo "name: cast-ui-test-noop" > /tmp/diecast-merge-check/cast-ui-test-noop/config.yaml
CAST_TEST_AGENTS_DIR=/tmp/diecast-merge-check python -c "
from cast_server.services.agent_service import get_all_agents
names = list(get_all_agents().keys())
print('cast-ui-test-noop in merged:', 'cast-ui-test-noop' in names)
"
rm -rf /tmp/diecast-merge-check
```

### Manual Checks

- Diff `agent_service.py` — confirm only `get_all_agents` (and possibly the cache key in
  `_load_agent_registry`) changed. No incidental refactors.
- Run the full existing test suite to confirm no regressions:
  ```bash
  pytest cast-server/tests/ -q
  ```

### Success Criteria

- [ ] `get_all_agents()` returns identical results to `main` when `CAST_TEST_AGENTS_DIR` is unset.
- [ ] `get_all_agents()` returns the union of prod + test agents when the env var points at a dir.
- [ ] Collision logs a warning AND production entry wins.
- [ ] `_load_agent_registry` still takes one root and uses one mtime-keyed cache (per-root cache is fine).
- [ ] All three meta-tests pass.
- [ ] Existing pytest suite still green.

## Execution Notes

- **Do not introduce a process-wide cache reset.** Per-root caching keyed on `Path.resolve()`
  gives independent caches naturally.
- **Logger name matters.** Use `logging.getLogger(__name__)` so log noise is namespaced.
- **AgentDefinition dataclass shape:** check whether it has a `source_path` / `directory` /
  `root` field that survives the merge. If so, the collision test can assert the prod entry
  by comparing source paths. If not, just assert the warning fires.
- **`Path` imports:** `from pathlib import Path` — don't sprinkle string-based path joins.
- **No skill delegation needed for this sub-phase.** It's a small, targeted Python change
  paired with a fast meta-test.
- **Spec-linked files:** None of the modified files are covered by a spec in `docs/specs/`.
