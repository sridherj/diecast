# Gate B: Failing-Test Enumeration

> **Context:** Read sp2.5's full T1 run output before reviewing this gate.

## Decision Criteria

This gate converts the user's "feels broken in several ways" vibe into an enumerated
list of concrete failing tests. **No fix work commits until this list is reviewed.**

US2 explicitly hangs on this conversion: every test that flips green inside this
goal must trace back to a symptom bucket identified at this gate.

## Surface to User

### 1. Full failing-test list

Run under spec env vars and capture:

```
CAST_DISABLE_SERVER=1 \
CAST_DELEGATION_BACKOFF_OVERRIDE=10ms,20ms,50ms \
CAST_DELEGATION_IDLE_TIMEOUT_SECONDS=4 \
pytest cast-server/tests/integration/test_child_delegation.py -v
```

Group failures by symptom bucket:

| Bucket | Symptom | Tests likely here |
|--------|---------|-------------------|
| 4a | Parent stall after child finalize | `TestMtimeHeartbeatRoundTrip*`, `TestResultSummary` (timing-related), `TestFinalizeCleanup*` (if parent doesn't observe child's terminal state) |
| 4b | Cleanup or contract drift | `TestFinalizeCleanup*` (orphan files), `TestMixedTransportPreamble` (anti-inline phrase emit count), 422-body-shape tests |
| 4c | Allowlist/depth/output-JSON silent violations | `TestOutputJsonContractV2*` (non-terminal status, untagged Open Questions), `TestExternalProjectDirPrecondition::test_depth4_*` (4th-depth row precedence) |

### 2. One-line hypothesis per failing test

For each failing test, propose which bucket (4a / 4b / 4c) it maps to and a
one-line guess at the implicated code path.

### 3. Out-of-scope check (Risk #1)

Any failure that points at a STRUCTURAL issue (e.g., the polling loop is
fundamentally racy, not just buggy) MUST be escalated at this gate — file a
separate goal, do NOT push to Phase 4.

Phase 4's contract is "minimum-diff fixes only". If a test reveals a deeper
architectural bug, the Phase 4 fix would be too large. Surface it now.

## Options

### Option A: All failures are Phase 4-tractable (minimum-diff fixes)
- **Condition:** Every failing test fits into bucket 4a / 4b / 4c with a small,
  targeted fix.
- **Action:** Mark `GB` Done, dispatch sp4a / sp4b / sp4c in parallel with the
  bucket assignments.

### Option B: One or more failures reveal structural issues
- **Condition:** At least one test surfaces a bug too large for "minimum diff".
- **Action:** File a separate goal for each structural issue. Mark those tests
  `xfail` in this goal's CI ONLY at the spec author's discretion (US2 forbids
  `xfail` at goal exit, so this requires explicit user sign-off and reduces this
  goal's scope). Mark `GB` Done with the escalation noted in Notes.

### Option C: No failures at all
- **Condition:** Phase 2 + Phase 3 produce a fully-green T1 suite — no symptoms
  to convert.
- **Action:** Skip sp4a / sp4b / sp4c entirely; mark them Skipped in `_manifest.md`
  with a note that Phase 2+3 already exercised the contract. Continue to Phase 5.
  **WARNING:** This conflicts with the user's reported "feels broken" symptom;
  surface to the user explicitly and confirm the suite actually exercises the
  reported behaviors before skipping.

## How to Proceed

1. Capture sp2.5's failing-test list with bucket assignments.
2. Surface to user (one batch) with options A / B / C.
3. Update `_manifest.md`: set `GB` status to `Done`, write decision in Notes.
4. If Option C: mark sp4a / sp4b / sp4c as Skipped with rationale.
5. Continue: orchestrator advances per option chosen.
