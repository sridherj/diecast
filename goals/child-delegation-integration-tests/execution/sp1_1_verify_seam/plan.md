# sp1.1 — Verify `CAST_TEST_AGENTS_DIR` Seam Supports Four-Fixture Layout

> **Pre-requisite:** Read `goals/child-delegation-integration-tests/execution/_shared_context.md` first.

## Objective

The detailed plan's Review #1 found that the test-agent registry seam already exists
in production code. This sub-phase is a **read-only audit + 5-line note** confirming
the seam works for our four-fixture layout. Output is the verification note that
sp1.3 and the Gate A discussion will reference.

## Dependencies

- **Requires completed:** None.
- **Assumed codebase state:** `cast-server/cast_server/models/agent_config.py` and
  `cast-server/cast_server/services/agent_service.py` exist at lines documented in
  shared context.

## Scope

**In scope:**
- Confirm `_candidate_config_paths()` (around `agent_config.py:62`) appends
  `<CAST_TEST_AGENTS_DIR>/<agent_id>/config.yaml` after the production path.
- Confirm `get_all_agents()` (around `agent_service.py:1614-1631`) merges the
  test-registry with collision-warn behavior.
- Document `_config_cache` (around `agent_config.py:59`) mtime-invalidation
  contract: tests must monkeypatch `load_agent_config` (the public seam) OR call
  `_config_cache.clear()`. sp2.x will use the monkeypatch route per Review #3.

**Out of scope (do NOT do these):**
- Editing any production code. This is read-only.
- Introducing a new env var (e.g., `CAST_AGENT_FIXTURE_DIRS`). Existing seam wins.
- Writing any test code yet (sp1.4 stubs the test module).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| (none) | Read-only | -- |

Output: a 5-line note (delivered as your final assistant message text, not as a
written file) summarizing the three confirmations.

## Detailed Steps

### Step 1.1.1: Read the seam in `agent_config.py`

Open `cast-server/cast_server/models/agent_config.py` and locate `_candidate_config_paths`
near line 62. Confirm it consults `os.environ["CAST_TEST_AGENTS_DIR"]` and yields
`<that-dir>/<agent_id>/config.yaml` AFTER the production candidate path.

### Step 1.1.2: Read the registry merge in `agent_service.py`

Open `cast-server/cast_server/services/agent_service.py` and locate `get_all_agents`
near line 1614. Confirm lines ~1618-1631 merge the production registry with the
test-agents directory, warning on name collisions.

### Step 1.1.3: Read the cache contract in `agent_config.py`

Locate `_config_cache` near line 59. Confirm the cache is keyed by config-file mtime
so external file changes are picked up automatically. Note that sp2.x prefers
`monkeypatch` of the public `load_agent_config` (per Review #3) rather than direct
cache mutation; this avoids implicit dependencies on cache internals.

### Step 1.1.4: Compose the 5-line note

Output text in this shape:

```
sp1.1 verification:
1. Seam: `CAST_TEST_AGENTS_DIR` env var, set before tests import `load_agent_config`.
2. Path appended: `<env>/<agent_id>/config.yaml` (`agent_config.py:~62`).
3. Registry merge: `get_all_agents()` includes test-agent dir with collision-warn (`agent_service.py:~1618-1631`).
4. Cache: `_config_cache` mtime-keyed; tests monkeypatch `load_agent_config` (public seam, Review #3) — do not mutate `_config_cache` directly.
5. No production code changes required; sp1.3 wires via conftest one-liner.
```

Adjust line numbers if they have drifted, but keep the structure.

## Verification

### Automated Tests (permanent)

None this sub-phase.

### Validation Scripts (temporary)

```
grep -n 'CAST_TEST_AGENTS_DIR' cast-server/cast_server/models/agent_config.py cast-server/cast_server/services/agent_service.py
```
should return at least one hit per file. If the seam has been renamed or removed,
STOP and surface to the user — Phase 1 plan needs revision.

### Manual Checks

- Read the three locations above with the Read tool.
- Confirm the seam matches the description.

### Success Criteria

- [ ] `CAST_TEST_AGENTS_DIR` confirmed at `agent_config.py:~62`.
- [ ] `get_all_agents()` merge-and-warn confirmed at `agent_service.py:~1618-1631`.
- [ ] `_config_cache` mtime-key contract confirmed at `agent_config.py:~59`.
- [ ] 5-line note emitted as final assistant message text.

## Execution Notes

Spec-linked files: `agent_config.py` and `agent_service.py` are linked from
`docs/specs/cast-delegation-contract.collab.md`. Read-only here, but the contract
context matters: collision-warn behavior is the spec-mandated way of handling
test-overlay agents.

If line numbers have drifted significantly, document the new locations in the note
— don't fail the sub-phase over cosmetic drift.
