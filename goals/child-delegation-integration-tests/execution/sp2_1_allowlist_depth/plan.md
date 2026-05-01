# sp2.1 — Port Allowlist + Depth + Child-Launch + Terminal-Title Classes + Suite Timeout

> **Pre-requisite:** Read `goals/child-delegation-integration-tests/execution/_shared_context.md` first.

## Objective

Wire five test classes against the diecast file-canonical contract, mirroring the
second-brain test_delegation.py classes 1:1 in behavior (not in code). Establish
the suite-wide `pytest-timeout = 5` defense per Review #7.

## Dependencies

- **Requires completed:** Phase 1 complete + Gate A passed (fixture path,
  dispatch_mode declarations, seam confirmed).
- **Assumed codebase state:** test module exists with equivalence-map docstring
  (sp1.4); conftest sets `CAST_TEST_AGENTS_DIR` and clears `_config_cache` (sp1.3);
  fixtures exist (sp1.2).

## Scope

**In scope:**
- Five test classes appended to `test_child_delegation.py`:
  - `TestAllowlistValidation` (US1.S2)
  - `TestDelegationDepthEnforcement` (US1.S3)
  - `TestDepthCalculation` (US1.S3, mocks `_get_delegation_depth`)
  - `TestChildLaunchIsolation` (US1.S1)
  - `TestTerminalTitleFormatting`
- Suite-wide `pytest.ini` with `timeout = 5`.
- Equivalence-map docstring entries replaced with concrete class names.

**Out of scope (do NOT do these):**
- Re-test B5 / B3 / B4 primitive behaviors. Compose only.
- Mutate `_config_cache` directly. Use `monkeypatch.setattr(agent_service, "load_agent_config", ...)`.
- Test against HTTP. T1 is file-canonical. No `requests`/`httpx`/`urllib` imports.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/integration/test_child_delegation.py` | Append 5 classes; update docstring | Stub from sp1.4 |
| `cast-server/tests/integration/pytest.ini` | Create | Does not exist |

## Detailed Steps

### Step 2.1.1: Read second-brain reference for the five classes

For each of the five classes, read the corresponding class in
`~/workspace/second-brain/taskos/tests/test_delegation.py` to understand the test
intent. **Do NOT copy code.** Adapt the behavior to diecast's symbols.

### Step 2.1.2: Create suite-wide pytest.ini

```ini
# cast-server/tests/integration/pytest.ini
[pytest]
# Belt-and-suspenders FR-003 defense: any single hung test fails as "timed out"
# instead of stalling the suite. Wall-clock budget is <30s overall.
timeout = 5
```

If a project-level `pytest.ini` already exists, add a `[pytest]` section here OR
extend the existing config — choose the smallest-diff option.

### Step 2.1.3: Implement `TestAllowlistValidation` (US1.S2)

Drive `trigger_agent` with a parent whose `allowed_delegations=[child]`:
- positive: dispatching `child` succeeds (asserts allowlist passes).
- negative: dispatching `other` (NOT in allowlist) raises before run-creation;
  exception message names the disallowed target.

Cache-isolation pattern:
```python
def test_allowlist_denies_non_member(monkeypatch, tmp_path):
    parent_cfg = AgentConfig(agent_id="parent", allowed_delegations=["child"], ...)
    child_cfg = AgentConfig(agent_id="other", allowed_delegations=[], ...)
    def fake_load(name):
        return {"parent": parent_cfg, "other": child_cfg}[name]
    monkeypatch.setattr("cast_server.services.agent_service.load_agent_config", fake_load)
    # ... drive trigger_agent and assert
```

### Step 2.1.4: Implement `TestDelegationDepthEnforcement` (US1.S3)

Build a chain `run0 → run1 → run2 → run3`; the 4th dispatch raises with a
"max delegation depth" error. Use the in-memory DB or test DB — see existing
`tests/test_*` for patterns.

### Step 2.1.5: Implement `TestDepthCalculation` (US1.S3)

Pure-function test of `_get_delegation_depth`. Mock the run-row fetcher and assert
depth math is correct for various chain shapes.

### Step 2.1.6: Implement `TestChildLaunchIsolation` (US1.S1)

Assert `_launch_agent` for a child run produces a child with its OWN tmux session
(not splitting the parent's). Mock the tmux launcher; assert the session name
and pane shape.

### Step 2.1.7: Implement `TestTerminalTitleFormatting`

Find the terminal-title helper (likely in `agent_service.py` or a small module).
Assert: `[Child]` / `[Diecast]` prefixes, 80-char truncation. Check `tests/`
for existing helpers/imports.

### Step 2.1.8: Update equivalence-map docstring

Replace `<TODO sp2.1>` markers for these five classes with the actual diecast
class names just authored.

## Verification

### Automated Tests (permanent)

```
CAST_DISABLE_SERVER=1 \
CAST_DELEGATION_BACKOFF_OVERRIDE=10ms,20ms,50ms \
CAST_DELEGATION_IDLE_TIMEOUT_SECONDS=4 \
pytest cast-server/tests/integration/test_child_delegation.py \
       -k "Allowlist or Depth or ChildLaunch or TerminalTitle"
```
Collects ≥5 classes; total time <10s. Some tests may FAIL — that's expected and
counts toward Gate B's failing-test enumeration.

### Validation Scripts (temporary)

FR-008 lint:
```bash
! grep -nE '^(import|from)\s+(requests|httpx|urllib)' \
  cast-server/tests/integration/test_child_delegation.py
```

### Manual Checks

- Each of the five classes has at least one method.
- All tests use `tmp_path` for any goal directory (constraint compliance).
- Cache isolation pattern: `monkeypatch.setattr(..., load_agent_config, ...)`,
  not `_config_cache.clear()` directly.

### Success Criteria

- [ ] Five classes exist in the module.
- [ ] `pytest.ini` has `timeout = 5`.
- [ ] FR-008 grep returns no lines.
- [ ] Equivalence map updated.
- [ ] Suite runs (failures OK) in <10s for these five classes.

## Execution Notes

- **Spec-linked files:** `agent_service.py`, `agent_config.py`. If you touch these
  in any way (you shouldn't — this sub-phase is tests-only), read
  `docs/specs/cast-delegation-contract.collab.md` first and verify SAV behaviors.
- US1.S3 (depth) overlaps with sp3.1's "depth-4 422 BEFORE row creation" test.
  This sub-phase covers the EXCEPTION raise; sp3.1 covers the row-precedence
  guarantee. Don't duplicate.
- If the diecast `_get_delegation_depth` signature differs from second-brain's,
  adapt the mock — document the divergence in equivalence-map docstring as
  justified deviation.
