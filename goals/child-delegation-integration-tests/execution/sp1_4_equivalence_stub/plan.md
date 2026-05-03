# sp1.4 — Equivalence-Map Docstring Stub at Top of T1 Module

> **Pre-requisite:** Read `goals/child-delegation-integration-tests/execution/_shared_context.md` first.

## Objective

Create `cast-server/tests/integration/test_child_delegation.py` as an empty test
module containing only the FR-007 equivalence-map docstring. Phase 2 sub-phases
will populate the TODO markers as each diecast counterpart class lands.

## Dependencies

- **Requires completed:** None (parallel-safe with sp1.1, sp1.2, sp1.3).
- **Assumed codebase state:** the second-brain reference suite is at
  `<SECOND_BRAIN_ROOT>/taskos/tests/test_delegation.py`. If that path differs
  on the executor's host, locate it via `find <SECOND_BRAIN_ROOT> -name test_delegation.py`.

## Scope

**In scope:**
- Create the test module file with module-level docstring listing all 11
  second-brain test classes.
- Each line: `<second-brain class name> → <diecast counterpart TBD> | <US/scenario citation>`.
- Add a final paragraph mapping to plan §Phase 2 Key Activities.

**Out of scope (do NOT do these):**
- Writing any test code yet. The file MUST collect as 0 tests.
- Reading second-brain test bodies — only class names. Coverage decisions live
  in Phase 2 sub-phases, not here.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/integration/test_child_delegation.py` | Create | Does not exist |

## Detailed Steps

### Step 1.4.1: Enumerate second-brain test classes

Read `<SECOND_BRAIN_ROOT>/taskos/tests/test_delegation.py` and extract ONLY
the class names (e.g., grep for `^class Test`). Do not copy implementation.

Expected ~11 classes, matching the plan §Phase 2 list:
- `TestAllowlistValidation`
- `TestDelegationDepthEnforcement`
- `TestDepthCalculation`
- `TestDelegationContextFile`
- `TestResultSummary`
- `TestChildLaunchIsolation`
- `TestTerminalTitleFormatting`
- `TestContinueAgentRun`
- `TestFinalizeCleanup`
- `TestPreambleAntiInline`
- `TestPromptBuilder`
- `TestMixedTransportPreamble`

(Exact name list comes from second-brain; if it differs, use what's there.)

### Step 1.4.2: Write the docstring stub

```python
# cast-server/tests/integration/test_child_delegation.py
"""T1 integration suite — child delegation contract.

Coverage parity with second-brain's `taskos/tests/test_delegation.py` is the floor.
Diecast-only contract checks (external_project_dir 422, output-JSON v2, mtime
heartbeat) are the additions.

## Equivalence map (second-brain → diecast)

Each line: <second-brain class> → <diecast counterpart class> | <spec citation>
Populated by Phase 2 / Phase 3 / Phase 6 sub-phases. TODO markers replaced as
diecast counterparts land.

- TestAllowlistValidation → <TODO sp2.1> | US1.S2, FR-001
- TestDelegationDepthEnforcement → <TODO sp2.1> | US1.S3, FR-001
- TestDepthCalculation → <TODO sp2.1> | US1.S3, FR-001
- TestDelegationContextFile → <TODO sp2.2> | US1.S4, FR-001
- TestResultSummary → <TODO sp2.2> | US1.S6, FR-001
- TestChildLaunchIsolation → <TODO sp2.1> | US1.S1, FR-001
- TestTerminalTitleFormatting → <TODO sp2.1> | FR-001
- TestContinueAgentRun → <TODO sp2.4> | US1.S10, FR-001
- TestFinalizeCleanup → <TODO sp2.2> | US1.S5, FR-001
- TestPreambleAntiInline → <TODO sp2.3> | US1.S7, FR-001
- TestPromptBuilder → <TODO sp2.3> | US1.S7+S8, FR-001
- TestMixedTransportPreamble → <TODO sp2.3> | US1.S9, SC-004, FR-001

## Diecast-only additions (no second-brain counterpart)

- TestDispatchModeValidator (sp2.3) — pins agent_config.py:36-41 silent fallback
- TestExternalProjectDirPrecondition (sp3.1) — US2.S3, US2.S7, FR-002
- TestOutputJsonContractV2 (sp3.2) — US2.S4-S6, FR-002
- TestMtimeHeartbeatRoundTrip (sp3.3) — US2.S1, FR-002
- TestSubagentOnlyPreamble (sp6.1) — US4.S2, FR-005

## Test-environment expectations (FR-003)

This module runs under:
    CAST_DISABLE_SERVER=1
    CAST_DELEGATION_BACKOFF_OVERRIDE=10ms,20ms,50ms
    CAST_DELEGATION_IDLE_TIMEOUT_SECONDS=4

Wall-clock budget: <30s for the full module (including failing tests pre-Phase-4).
Per-test pytest-timeout=5 enforced via cast-server/tests/integration/pytest.ini.

Registry discovery: CAST_TEST_AGENTS_DIR seam (set by conftest.py).

NO Python imports of `requests`, `httpx`, `urllib` (FR-008).
"""
```

### Step 1.4.3: Confirm syntactic validity + zero tests collected

The file must be valid Python and pytest-discoverable but collect 0 tests.

## Verification

### Automated Tests (permanent)

The module itself is the artifact. No tests yet.

### Validation Scripts (temporary)

```bash
python -c "import ast; ast.parse(open('cast-server/tests/integration/test_child_delegation.py').read())"
# exit 0

pytest cast-server/tests/integration/test_child_delegation.py --collect-only
# exit 0; "0 tests collected" or equivalent
```

### Manual Checks

- Read the file. Confirm docstring contains 11+ TODO entries (one per second-brain
  class) and the diecast-only additions list.
- No `def test_` or `class Test` definitions yet.

### Success Criteria

- [ ] File exists and parses as valid Python.
- [ ] `pytest --collect-only` reports 0 tests.
- [ ] Docstring contains all 11 second-brain class TODO entries.
- [ ] Diecast-only additions enumerated.
- [ ] FR-007 satisfied: equivalence map IS the test module's docstring.

## Execution Notes

- **Spec-linked files:** none. The file is brand new.
- FR-007 is unambiguous: equivalence map lives in the test module's docstring,
  NOT a separate `.md` file. Resist the urge to factor it out.
- If second-brain's test class list has more or fewer than 11 classes, use the
  actual count and adjust.
