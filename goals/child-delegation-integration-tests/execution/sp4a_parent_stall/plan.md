# sp4a — Red→Green: Parent Stall After Child Finalize

> **Pre-requisite:** Read `goals/child-delegation-integration-tests/execution/_shared_context.md` first.
>
> **CRITICAL:** This sub-phase's atomic-task list is **intentionally deferred**
> until Gate B fires. The plan identifies the bucket and likely-implicated code,
> but the actual fix decomposition depends on the failing-test list from sp2.5.
> Speculative atomic-task enumeration would be honesty-violating.

## Objective

Every test that fails because the parent's polling loop doesn't transition within
≤1 polling-tick after the child mtime updates is now green. At least one commit
`fix(delegation): green <test_name>` lands in this sub-phase.

## Dependencies

- **Requires completed:** Phase 3 (all T1 + diecast-only tests authored) AND
  Gate B passed (failing-test list reviewed and bucket-assigned).

## Scope

**In scope:**
- Tests in the parent-stall bucket assigned at Gate B (typically
  `TestMtimeHeartbeatRoundTrip` and any finalize-poll classes).
- Minimum-diff fixes to `agent_service.py` polling loop or finalizers.
- One `fix(delegation): green <test_name>` commit per test fixed.

**Out of scope (do NOT do these):**
- Structural polling-loop refactor. If a test reveals a deeper architectural issue,
  escalate at Gate B (already passed; if found mid-fix, file separate goal).
- Cleanup-related fixes — those are sp4b's bucket.
- Output-JSON validation tightening — that's sp4c's bucket.
- Speculative work not directly tied to a specific failing test from Gate B's list.

## Files Likely Touched

| File | Likely Action | Why |
|------|---------------|-----|
| `cast-server/cast_server/services/agent_service.py` | Modify | `_finalize_run` (line ~1702), `_finalize_run_from_monitor` (line ~2520), polling loop primitive |

Per Review #2: cleanup-and-transition contract must hold across BOTH finalizer
entry points. If the bug is in one, verify the other independently.

## Detailed Steps

### Step 4a.1 (Gate B + execution-time): Pull the failing-test list for this bucket

From the Gate B output in `_manifest.md` notes: identify which failing tests were
assigned to bucket 4a (parent stall). Build a small in-memory list:
- Test ID (`module::Class::method`)
- One-line failure mode summary
- Hypothesis on implicated code path

### Step 4a.2: For each failing test in the bucket — diagnose

For each test:
1. Read the test code carefully.
2. Run it in isolation: `pytest <full-test-id> -v -x`.
3. Add print statements / use pdb / read the polling loop to identify the actual
   defect (e.g., does `_finalize_run_from_monitor` actually invoke the parent
   transition, or does it only update child state?).

### Step 4a.3: For each failing test — apply minimum fix

Constraints:
- Smallest diff that flips the test from red to green.
- Do NOT refactor adjacent code, even if "while you're in there" is tempting
  (FR-006 / constraint check).
- If the fix surface area is non-trivial: → Delegate: `/cast-detailed-plan` with
  the specific test and the diagnosis to split into atomic tasks.

### Step 4a.4: For each fix — commit with the convention

```
git add <files>
git commit -m "fix(delegation): green <test_name>

<one-paragraph diagnosis + fix summary>

Refs: US2.S1, FR-006."
```

The `<test_name>` after `green ` MUST exactly match the failing test's name (or
a clearly-recognizable substring). FR-006 lint via `git log --grep`.

### Step 4a.5: Verify suite-wide regression

After each fix:
```
CAST_DISABLE_SERVER=1 \
CAST_DELEGATION_BACKOFF_OVERRIDE=10ms,20ms,50ms \
CAST_DELEGATION_IDLE_TIMEOUT_SECONDS=4 \
pytest cast-server/tests/integration/test_child_delegation.py
```
- Bucket-4a tests progressively flip green.
- No previously-green test goes red.
- Wall-clock budget still <30s.

If a previously-green test goes red, STOP — that's a regression. Diagnose before
committing the next fix.

### Step 4a.6: If a fix reveals contract drift

If the fix work surfaces a place where the spec is ambiguous or wrong:
- Document the drift in a note for sp7.3.
- Do NOT silently change `cast-delegation-contract.collab.md`.
- Continue with the minimum-diff fix; sp7.3 escalates the spec change via
  `/cast-update-spec`.

### Step 4a.7: If a fix reveals structural issue

If, mid-fix, you discover the test points at a structurally-broken polling
loop (Risk #1):
- STOP committing in this sub-phase.
- Document the finding.
- File a separate goal via `/cast-goals create` (mention in the note that the
  test pinpoints the structural issue).
- Mark this test as a Phase 4 escalation in the manifest, with explicit user
  sign-off needed before this sub-phase's status becomes "Done".

## Verification

### Automated Tests (permanent)

All tests in the parent-stall bucket green.

### Validation Scripts (temporary)

FR-006 lint:
```bash
git log --oneline --grep "fix(delegation): green" | wc -l
# Should be ≥ 1 from this sub-phase (each commit names a parent-stall test)
```

Constraint check:
```bash
git diff --stat <pre-sp4a-commit>..HEAD -- ':!cast-server/tests'
# Review for unrelated refactor — there should be none
```

### Manual Checks

- Each commit is minimum-diff — review the diff for unrelated changes.
- Each commit message names the failing test exactly.
- Bucket-4a tests are all green; previously-green tests are still green.

### Success Criteria

- [ ] All bucket-4a failing tests now pass.
- [ ] ≥1 `fix(delegation): green <test_name>` commit lands in this sub-phase.
- [ ] No previously-green test regressed.
- [ ] No unrelated refactor in the diff.
- [ ] Wall-clock budget still <30s.
- [ ] Spec drift findings (if any) documented for sp7.3.
- [ ] Structural escalations (if any) filed as separate goals with user sign-off.

## Execution Notes

- **Spec-linked files:** `agent_service.py`. **Read
  `docs/specs/cast-delegation-contract.collab.md` §Heartbeat-by-mtime BEFORE
  modifying** the polling loop or finalizers. Verify SAV behaviors.
- **No xfail to escape**: if a test cannot be made green within minimum-diff
  scope, escalate (separate goal), don't xfail.
- **Skill delegation**: if the fix surface is non-trivial,
  → Delegate: `/cast-detailed-plan` with the failing test + diagnosis to split
  into atomic tasks. Then come back here and execute.
- **Constraint enforcement**: FR-006 commit convention surfaces scope creep at
  PR review. Reviewer enforces "no unrelated refactor".
