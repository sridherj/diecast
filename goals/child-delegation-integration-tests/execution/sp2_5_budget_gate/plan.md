# sp2.5 — Wall-Clock Budget Gate + Equivalence-Map Completion

> **Pre-requisite:** Read `goals/child-delegation-integration-tests/execution/_shared_context.md` first.

## Objective

Verify FR-003 (full T1 module runs in <30s under spec env vars) and complete
FR-007 (equivalence-map docstring fully populated). Surface the failing-test list
for Gate B.

## Dependencies

- **Requires completed:** sp2.1, sp2.2, sp2.3, sp2.4 (all Phase 2 test classes).
- **Assumed codebase state:** test module has all 11+ second-brain counterparts
  populated; `pytest.ini` has `timeout = 5`.

## Scope

**In scope:**
- Run the full T1 suite under spec env vars; capture timing and failure list.
- Tighten any test that breaks the budget — never skip (Review #6).
- Final pass on equivalence-map docstring: zero `TODO` substrings remain.
- Produce the failing-test list with bucket assignments for Gate B.

**Out of scope (do NOT do these):**
- Skip or `xfail` any test to make budget. If a test cannot run in budget under
  env-var overrides + `pytest-timeout=5`, surface to user — do NOT mask.
- Begin any sp4 fix work. Gate B must pass first.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/integration/test_child_delegation.py` | Final docstring pass | Has all sp2 classes |

## Detailed Steps

### Step 2.5.1: Run the full T1 suite

```
time CAST_DISABLE_SERVER=1 \
     CAST_DELEGATION_BACKOFF_OVERRIDE=10ms,20ms,50ms \
     CAST_DELEGATION_IDLE_TIMEOUT_SECONDS=4 \
     pytest cast-server/tests/integration/test_child_delegation.py -v --durations=10
```

Capture:
- Wall-clock real time.
- Per-test durations.
- The list of failed/errored tests with their failure summaries.

### Step 2.5.2: Budget check

If real time > 30s:
1. Use `--durations=10` output to find the slowest cases.
2. Tighten only — never skip. Common tightening:
   - Reduce loop counts in polling-related tests.
   - Use smaller timeout values (already overridden, but verify they apply).
   - Mock more aggressively (e.g., bypass tmux entirely if a test doesn't need it).
3. If tightening cannot bring the suite under 30s, surface to user — this is a
   plan-revision signal. Do NOT skip the slow test (FR-003 / Review #6).

### Step 2.5.3: Failing-test enumeration

For each failing test, prepare a Gate B entry:
- Test full path (`module::Class::method`).
- One-line failure summary.
- Bucket guess: 4a (parent stall), 4b (cleanup/contract drift), 4c (silent
  violations), or "structural / Risk #1 escalation".

Sample format:
```
- TestMtimeHeartbeatRoundTrip::test_parent_observes_within_one_tick — assertion
  failed: parent took 3 ticks to observe child mtime → bucket 4a
- TestFinalizeCleanup::test_cleanup_via_finalize_run_from_monitor — orphan
  .delegation-*.json after async finalize → bucket 4b
- TestOutputJsonContractV2::test_non_terminal_status_treated_as_malformed —
  parent finalized as completed instead of failed → bucket 4c
```

### Step 2.5.4: Equivalence-map docstring final pass

Replace every remaining `<TODO sp2.x>` marker with the concrete diecast class
name. Mark any second-brain class without a diecast counterpart as
`# justified-skip: <reason>`.

Verify: `! grep -E '<TODO|TBD>' cast-server/tests/integration/test_child_delegation.py`
returns empty.

### Step 2.5.5: Produce Gate B input

Write the failing-test enumeration as your final assistant message text. Do NOT
write it to a file — Gate B is the discussion surface, not a doc artifact.

## Verification

### Automated Tests (permanent)

```
time CAST_DISABLE_SERVER=1 \
     CAST_DELEGATION_BACKOFF_OVERRIDE=10ms,20ms,50ms \
     CAST_DELEGATION_IDLE_TIMEOUT_SECONDS=4 \
     pytest cast-server/tests/integration/test_child_delegation.py
```
Real time < 30s. Some tests may FAIL — that's the Gate B input.

### Validation Scripts (temporary)

```bash
grep -nE '<TODO|TBD>' cast-server/tests/integration/test_child_delegation.py
# returns empty / exit 1
```

### Manual Checks

- Every second-brain class has a counterpart line OR a `# justified-skip:` line.
- No `xfail` markers added (US2 forbids at goal exit; sp3.3 also red-without-xfail).

### Success Criteria

- [ ] Wall-clock < 30s for full module under spec env vars.
- [ ] Zero `<TODO>` / `<TBD>` substrings in docstring.
- [ ] Failing-test enumeration emitted with bucket guesses for Gate B.
- [ ] No tests skipped/xfailed to mask budget violations.

## Execution Notes

- **Spec-linked files:** none directly. The test module only.
- The failing-test list is the Gate B input. Do NOT begin any fix work — Gate B
  must explicitly pass before sp4a/4b/4c can commit.
- If the suite is fully GREEN (no failures), surface this as Gate B Option C
  (no symptoms to convert). Confirm with user before skipping Phase 4.
