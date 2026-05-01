# sp4b — Red→Green: Cleanup or Contract Drift

> **Pre-requisite:** Read `goals/child-delegation-integration-tests/execution/_shared_context.md` first.
>
> **CRITICAL:** Atomic-task list **intentionally deferred** until Gate B fires.
> See sp4a's discipline note.

## Objective

Every test that fails because of orphan files (`.delegation-*.json`, `.prompt`,
`.continue`, `.tmp`), malformed 422 body shape, or mixed-transport preamble
emission errors is now green. At least one `fix(delegation): green <test_name>`
commit.

## Dependencies

- **Requires completed:** Phase 3 + Gate B.

## Scope

**In scope:**
- Tests in the cleanup/contract-drift bucket assigned at Gate B.
- Likely targets: orphan files post-finalize, 422 body shape, mixed-transport
  preamble emission count.
- One `fix(delegation): green <test_name>` commit per test fixed.

**Out of scope (do NOT do these):**
- Parent-stall fixes (sp4a's bucket).
- Output-JSON / depth / silent-violation fixes (sp4c's bucket).
- Restructuring `_build_agent_prompt`. If structure is wrong vs spec, escalate
  via sp7.3 — do NOT silently change.

## Files Likely Touched

| File | Likely Action | Why |
|------|---------------|-----|
| `cast-server/cast_server/services/agent_service.py` | Modify | `_finalize_run_from_monitor` cleanup section, `_build_agent_prompt` mixed-transport branch |
| `cast-server/cast_server/routes/api_agents.py` | Modify | Trigger route 422 body shape |

## Detailed Steps

### Step 4b.1: Pull the failing-test list for this bucket

From Gate B output: bucket-4b assignments. Likely buckets:
- **Cleanup**: align finalizer's deletion list with the four-file inventory
  (`.delegation-<run_id>.json`, `.agent-run_<run_id>.prompt`, `.continue*`).
- **422 body**: align trigger-route response shape with
  `cast-delegation-contract.collab.md`.
- **Mixed-transport preamble**: ensure anti-inline phrase emits exactly once
  across both blocks.

### Step 4b.2: For each failing test — diagnose + minimum fix

Same workflow as sp4a:
1. Read test, isolate, identify defect.
2. Apply minimum diff.
3. Commit `fix(delegation): green <test_name>`.

### Step 4b.3: Special case — mixed-transport preamble divergence

Per Review #3 / Risk #3: if the diecast preamble structure has diverged from
second-brain's, sp2.3 already documented this in the equivalence-map docstring
as justified deviation. sp4b's job is to fix the **assertion** (in tests) ONLY
if the assertion is wrong against the diecast preamble structure. If the
diecast structure is wrong against `cast-delegation-contract.collab.md` —
contract drift, escalate via sp7.3.

The decision tree:
- Test asserts something not in the spec → fix the test.
- Test asserts the spec, code violates it → fix the code.
- Spec is ambiguous → document for sp7.3, ship the most-faithful interpretation
  for now.

### Step 4b.4: Verify suite-wide regression after each fix

Same as sp4a: bucket-4b tests progressively flip green; no regressions.

### Step 4b.5: Document any contract drift findings

If sp4b surfaces ambiguity or drift in
`cast-delegation-contract.collab.md`, append a note to a scratch list for sp7.3
(e.g., write to `goals/child-delegation-integration-tests/execution/sp7_3_spec_update/notes.md`
— this file is for in-flight notes, not a final artifact).

## Verification

### Automated Tests (permanent)

All bucket-4b tests green.

### Validation Scripts (temporary)

FR-006 lint same as sp4a. Constraint check (no unrelated refactor) same as sp4a.

### Manual Checks

- Each commit is minimum-diff.
- Spec-drift findings (if any) recorded for sp7.3.

### Success Criteria

- [ ] All bucket-4b failing tests pass.
- [ ] ≥1 `fix(delegation): green <test_name>` commit lands.
- [ ] No regressions.
- [ ] No unrelated refactor.
- [ ] Wall-clock <30s.
- [ ] Spec drift documented for sp7.3 if any surfaced.

## Execution Notes

- **Spec-linked files:** `agent_service.py`, `api_agents.py`. **Read
  `docs/specs/cast-delegation-contract.collab.md` (Cleanup contract, Dispatch
  Precondition, Subagent Dispatch) BEFORE modifying.**
- **No silent contract changes**: if the spec disagrees with observed behavior,
  the resolution policy is align-code-to-spec OR escalate-to-user (sp7.3) —
  never silently change the spec or the code's contract surface.
- **Skill delegation**: same as sp4a — if non-trivial, → Delegate: `/cast-detailed-plan`.
