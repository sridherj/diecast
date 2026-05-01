# sp3.3 — `TestMtimeHeartbeatRoundTrip` (EXPECTED RED Until sp4a)

> **Pre-requisite:** Read `goals/child-delegation-integration-tests/execution/_shared_context.md` first.

## Objective

Cover US2.S1: parent transitions to terminal within ≤1 polling-tick after the
child's mtime update is observed. File-canonical only (HTTP mocked/disabled).

This test is **EXPECTED to fail** initially — that's the parent-stall symptom
bucket from US2. NO `xfail` marker (US2 disallows at goal exit). It flips green
in sp4a.

## Dependencies

- **Requires completed:** Phase 2.
- **Assumed codebase state:** polling loop primitive exists in `agent_service.py`;
  `CAST_DELEGATION_BACKOFF_OVERRIDE` env-var hook is operative (per US6).

## Scope

**In scope:**
- `TestMtimeHeartbeatRoundTrip` test class with assertion that parent observes
  child mtime within one tick of the override schedule.

**Out of scope (do NOT do these):**
- Add `xfail` marker. US2 explicitly disallows at goal exit; the test is red →
  green via sp4a, never xfailed.
- Test the polling primitive's internals (covered by B5 primitive tests; out of
  scope per spec).
- Fix any failures here. That's sp4a.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/integration/test_child_delegation.py` | Append 1 class | Has prior classes |

## Detailed Steps

### Step 3.3.1: Locate the polling primitive

Find the function that drives parent-side polling for child terminal state.
Likely `_poll_for_child_terminal_state` or similar in `agent_service.py`. This
is the tick-counting target.

### Step 3.3.2: Implement the test

```python
class TestMtimeHeartbeatRoundTrip:
    """US2.S1: parent observes child's mtime update within ≤1 polling-tick.
    
    EXPECTED RED until sp4a flips it green.
    NO xfail marker — US2 disallows at goal exit.
    """

    def test_parent_observes_child_mtime_within_one_tick(self, tmp_path, monkeypatch):
        """Set up parent run polling with 10ms/20ms/50ms ladder, simulate child
        writing valid contract-v2 output.json + touching mtime, assert parent
        transitions within one tick of the override schedule.
        """
        # Set up tick counter
        ticks_observed = []
        original_sleep = <polling_sleep_target>
        def counting_sleep(delay):
            ticks_observed.append(delay)
            return original_sleep(delay)
        monkeypatch.setattr(<polling_sleep_target>, counting_sleep)

        # Pre-create parent run; spawn (or simulate) child writing valid output.json
        # to <goal_dir>/.agent-run_<child_id>.output.json with terminal status
        # Touch mtime to "now"

        # Drive parent polling loop
        # Assert: parent transitions to terminal AND ticks_observed has length 1
        # (one tick after mtime update)
        
        assert parent_run.status in ("completed", "failed"), \
            "parent did not transition to terminal"
        # Slack: allow up to 1 tick of poll wait
        ticks_after_mtime_update = <count ticks observed after the mtime touch>
        assert ticks_after_mtime_update <= 1, \
            f"parent took {ticks_after_mtime_update} ticks to transition; spec says ≤1"
```

Adapt mock targets to actual diecast symbol names. The test design is:
1. Inject a tick-counting wrapper around the polling sleep.
2. Synthesize a child terminal output write at a known time.
3. Assert tick-count after the write is ≤ 1.

### Step 3.3.3: Update equivalence-map docstring

Add the entry under "Diecast-only additions":
```
- TestMtimeHeartbeatRoundTrip (sp3.3) — US2.S1, FR-002.
  EXPECTED red until sp4a; NO xfail per US2.
```

## Verification

### Automated Tests (permanent)

```
pytest cast-server/tests/integration/test_child_delegation.py -k "MtimeHeartbeatRoundTrip"
```
Collects the class. **Failure here is EXPECTED initially** — this is the red
baseline for sp4a. The test exists to convert the parent-stall vibe to a
concrete signal.

### Validation Scripts (temporary)

```bash
grep -E "@pytest.mark.xfail" cast-server/tests/integration/test_child_delegation.py
# expected: empty / exit 1 (NO xfail markers anywhere)
```

### Manual Checks

- No `@pytest.mark.xfail` anywhere in the module.
- Test docstring explicitly says "EXPECTED RED until sp4a".

### Success Criteria

- [ ] One class with the assertion.
- [ ] No `xfail` marker.
- [ ] Test docstring documents red-until-sp4a status.
- [ ] Equivalence map updated.

## Execution Notes

- **Spec-linked files:** `cast-delegation-contract.collab.md` §Heartbeat-by-mtime.
  Read this section to understand the ≤1-tick contract.
- If the test happens to PASS at first try (parent stall is not actually broken),
  that's a Gate B Option C signal — no symptoms to convert. Surface to user.
- Per the locked decision, `xfail` is forbidden. The test is red → green via
  sp4a. If sp4a determines the bug is structural (Risk #1), escalate at Gate B
  for a separate goal — do NOT introduce `xfail` to make this goal close.
