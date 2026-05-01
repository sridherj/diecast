# sp3.1 — `TestExternalProjectDirPrecondition` (Additive Only — DRY with Existing Tests)

> **Pre-requisite:** Read `goals/child-delegation-integration-tests/execution/_shared_context.md` first.

## Objective

Per Review #4: `cast-server/tests/test_dispatch_precondition.py` already covers
8+ precondition cases. sp3.1 verifies those still pass under integration-suite env
vars and adds ONLY the genuinely-new cases (depth-4 row-precedence, `/invoke`
carve-out negative test).

## Dependencies

- **Requires completed:** Phase 2 complete (Gate B input prepared).
- **Assumed codebase state:** `cast-server/tests/test_dispatch_precondition.py`
  exists with the 8+ precondition tests.

## Scope

**In scope:**
- Cross-check existing precondition tests under integration-suite env vars.
- Two genuinely-new methods in a new class `TestExternalProjectDirPrecondition`:
  - `test_depth4_dispatch_returns_422_before_row_create` (US2.S7)
  - `test_invoke_route_does_not_422` (`/invoke` carve-out preserved)

**Out of scope (do NOT do these):**
- Re-implement any case already in `test_dispatch_precondition.py`. List them in
  the equivalence-map docstring as "covered elsewhere".

## Already-Covered Cases (cite by name; do NOT duplicate)

- `test_validate_raises_when_goal_has_no_external_project_dir`
- `test_validate_raises_when_external_project_dir_path_missing`
- `test_validate_passes_when_external_project_dir_exists`
- `test_trigger_agent_raises_before_enqueue_when_precondition_fails`
- `test_trigger_route_returns_422_with_structured_payload`
- `test_trigger_route_returns_422_when_path_missing`
- `test_trigger_route_succeeds_when_external_project_dir_set`
- `test_launch_agent_raises_when_external_project_dir_unset`
- `test_trigger_returns_422_on_malformed_delegation_context`

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/integration/test_child_delegation.py` | Append 1 class (2 methods) + docstring entry | Has Phase 2 classes |

## Detailed Steps

### Step 3.1.1: Cross-check existing tests under integration env vars

```
CAST_DISABLE_SERVER=1 \
CAST_DELEGATION_BACKOFF_OVERRIDE=10ms,20ms,50ms \
CAST_DELEGATION_IDLE_TIMEOUT_SECONDS=4 \
pytest cast-server/tests/test_dispatch_precondition.py -v
```
Should be green. If anything regresses under the env-var overrides, that's a real
bug surfaced — escalate to the appropriate sp4 bucket at Gate B (already passed,
but new findings can extend Gate B's list with a note).

### Step 3.1.2: Implement `test_depth4_dispatch_returns_422_before_row_create`

```python
class TestExternalProjectDirPrecondition:
    """Diecast-only precondition checks. Existing cases covered in
    cast-server/tests/test_dispatch_precondition.py — cited in equivalence map.
    """

    def test_depth4_dispatch_returns_422_before_row_create(self, tmp_path, monkeypatch):
        """US2.S7: depth-check happens BEFORE row insertion.
        
        Build a chain run0 → run1 → run2 → run3, attempt the 4th dispatch,
        assert 422 returned AND zero new row in agent_runs for the 4th attempt.
        """
        # Setup: insert 3 rows in agent_runs forming the chain
        # Capture the row count before
        rows_before = count_rows("agent_runs")
        # Attempt the 4th dispatch
        with pytest.raises(<Exception>, match="max delegation depth"):
            trigger_agent(...)
        # Assert: row count is unchanged (4th row was NOT created)
        rows_after = count_rows("agent_runs")
        assert rows_after == rows_before
```

The key assertion is **row-count invariance** across the failed dispatch attempt.
This pins the depth-check-before-insert ordering, which is exactly what US2.S7
asserts.

### Step 3.1.3: Implement `test_invoke_route_does_not_422`

```python
def test_invoke_route_does_not_422(self):
    """Spec carves /invoke out of external_project_dir enforcement.
    
    Dispatch via /invoke route to a goal with no external_project_dir;
    assert NOT 422 (carve-out preserved).
    """
    # Drive whatever the /invoke entry point is — locate in routes/api_agents.py
    # OR services/user_invocation_service.py
    response = invoke_agent_via_invoke_route(goal_with_no_external_project_dir, ...)
    assert response.status_code != 422  # carve-out preserved
```

Note: the `/invoke` route may not return an HTTP response in the testable layer.
Use whatever the in-process equivalent is (call the service function directly).
FR-008 forbids Python HTTP imports — go through the service layer.

### Step 3.1.4: Update equivalence-map docstring

Add an entry under "Diecast-only additions":
```
- TestExternalProjectDirPrecondition (sp3.1) — US2.S3, US2.S7, FR-002.
  Existing cases covered in cast-server/tests/test_dispatch_precondition.py:
  test_validate_raises_when_goal_has_no_external_project_dir,
  test_validate_raises_when_external_project_dir_path_missing,
  ... (full list above).
  New methods: test_depth4_dispatch_returns_422_before_row_create,
  test_invoke_route_does_not_422.
```

## Verification

### Automated Tests (permanent)

```
pytest cast-server/tests/integration/test_child_delegation.py -k "ExternalProjectDirPrecondition"
```
Collects ≥2 methods.

```
pytest cast-server/tests/test_dispatch_precondition.py -v
```
All 9+ existing tests still green.

### Validation Scripts (temporary)

```bash
grep -E "test_depth4|test_invoke_route" cast-server/tests/integration/test_child_delegation.py
```
Should match both methods.

### Manual Checks

- The depth-4 test asserts row-count INVARIANCE, not just exception type.
- The carve-out test does NOT use Python `requests`/`httpx`/`urllib` (FR-008).
- 422 body assertions use exact field names from
  `cast-delegation-contract.collab.md` §Dispatch Precondition.

### Success Criteria

- [ ] One class `TestExternalProjectDirPrecondition` with two methods.
- [ ] Existing `test_dispatch_precondition.py` still green under integration env vars.
- [ ] Equivalence map cites the existing covered cases by name.
- [ ] FR-008 grep clean.
- [ ] No duplication of already-covered cases.

## Execution Notes

- **Spec-linked files:** `cast-delegation-contract.collab.md` §Dispatch Precondition,
  §`/invoke` Carve-Out. Read both before writing assertions.
- The existing precondition suite is the authority for the 8+ covered cases. Do
  not re-implement them — citing them in docstring satisfies SC-006 traceability.
- Per the resolved open question, both new methods live in the SAME class
  (`TestExternalProjectDirPrecondition`), keeping enforcement and carve-out
  visible together.
