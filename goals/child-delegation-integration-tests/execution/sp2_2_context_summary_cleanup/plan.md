# sp2.2 — Port DelegationContextFile + ResultSummary + FinalizeCleanup (BOTH Finalizers)

> **Pre-requisite:** Read `goals/child-delegation-integration-tests/execution/_shared_context.md` first.

## Objective

Three test classes covering: delegation-context file write+JSON shape, result_summary
populate/None/truncate-at-300, finalizer cleanup invariant across BOTH `_finalize_run`
AND `_finalize_run_from_monitor` entry points (Review #2).

## Dependencies

- **Requires completed:** sp2.1 (test module scaffolding present).
- **Assumed codebase state:** `_finalize_run` near `agent_service.py:1702`,
  `_finalize_run_from_monitor` near `agent_service.py:2520`.

## Scope

**In scope:**
- `TestDelegationContextFile` (US1.S4) — file written BEFORE `trigger_agent` returns,
  contains `agent_name`, `parent_run_id`, `context.*`, `output.*` verbatim.
- `TestResultSummary` (US1.S6) — populate / None / 350→300 truncate.
- `TestFinalizeCleanup` (US1.S5) with TWO methods (one per finalizer entry point).

**Out of scope (do NOT do these):**
- Re-architect `trigger_agent` to expose a hook. Use second-brain's monkeypatch
  interception pattern verbatim.
- Test other cleanup variants (`.tmp` from crashed children — out of scope per spec).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/integration/test_child_delegation.py` | Append 3 classes | Has sp2.1 classes |

## Detailed Steps

### Step 2.2.1: `TestDelegationContextFile` (US1.S4)

Drive `trigger_agent` with a `DelegationContext`. The file
`<goal_dir>/.delegation-<run_id>.json` must exist BEFORE `trigger_agent` returns.

Approach: monkeypatch a downstream symbol called within `trigger_agent` (e.g., the
DB-insert call) to assert the file is on disk at that point.

Assertions on the JSON:
- `agent_name` matches the dispatched child name.
- `parent_run_id` matches the parent run.
- `context.*` and `output.*` echo the verbatim model fields (no rewriting/normalization).

### Step 2.2.2: `TestResultSummary` (US1.S6)

Three methods:
- `test_populated_summary_under_300`: child output `summary` is 50 chars; assert
  `result_summary` field == those 50 chars.
- `test_missing_summary_yields_none`: child output omits `summary`; assert
  `result_summary` is `None`.
- `test_summary_over_300_is_truncated`: child output `summary` is 350 chars; assert
  `result_summary` is exactly 300 chars and equals the first 300 of the input.

Drive each via `_finalize_run_from_monitor` with a synthesized child output JSON.

### Step 2.2.3: `TestFinalizeCleanup` (US1.S5) — TWO methods (Review #2)

Pre-create four files in `tmp_path`:
- `.delegation-<run_id>.json`
- `.agent-run_<run_id>.prompt`
- `.agent-run_<run_id>.continue` (one or more)
- `.agent-run_<run_id>.output.json`

Methods:
- `test_cleanup_via_finalize_run` — drive the sync entry (`_finalize_run`, ~line 1702).
- `test_cleanup_via_finalize_run_from_monitor` — drive the async entry
  (`_finalize_run_from_monitor`, ~line 2520).

For BOTH: post-finalize, assert `.delegation`, `.prompt`, `.continue` are deleted;
`.output.json` is retained.

Both methods run independently. If they diverge, that's a real bug surfaced —
report as a Gate B candidate for sp4b (cleanup contract drift).

### Step 2.2.4: Update equivalence-map docstring

Replace `<TODO sp2.2>` markers with the actual class names.

## Verification

### Automated Tests (permanent)

```
pytest cast-server/tests/integration/test_child_delegation.py \
       -k "DelegationContextFile or ResultSummary or FinalizeCleanup"
```
Collects 3 classes (5+ methods total).

Cumulative T1 wall-clock still <30s.

### Validation Scripts (temporary)

```bash
grep -E "class Test(DelegationContextFile|ResultSummary|FinalizeCleanup)" \
  cast-server/tests/integration/test_child_delegation.py
```
Should return 3 lines.

### Manual Checks

- `TestFinalizeCleanup` HAS two test methods, one per finalizer entry point.
- The "WRITE BEFORE RETURNING" assertion uses monkeypatch interception, not a
  hook injected into `trigger_agent`.

### Success Criteria

- [ ] 3 classes present.
- [ ] `TestFinalizeCleanup` has both `test_cleanup_via_finalize_run` and
      `test_cleanup_via_finalize_run_from_monitor`.
- [ ] All tests use `tmp_path`-scoped goal directories.
- [ ] FR-008 grep clean.
- [ ] Equivalence map updated.

## Execution Notes

- **Spec-linked files:** `agent_service.py`. Read
  `docs/specs/cast-delegation-contract.collab.md` §Cleanup contract before writing
  cleanup assertions — the four-file inventory is spec-defined.
- **The "WRITE BEFORE RETURNING" assertion** is non-trivial. Second-brain's pattern
  is the canonical solution: monkeypatch a downstream symbol (e.g., the DB
  insert), and inside the patch's body, assert the file is on disk. When
  `trigger_agent` calls the patched symbol, the assertion runs at the right
  moment.
- If `_finalize_run` and `_finalize_run_from_monitor` exhibit different cleanup
  behaviors, **do not paper over it**. The two-method design is intentional — a
  red signal here is a real bug for Gate B / sp4b.
