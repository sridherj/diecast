# Test Cases: cast-fanout-detailed-plan

## TC-1: Parse and dispatch 7-phase plan
- **Input:** `build-reference-repo/high_level_plan.collab.md` (7 phases, Phase 1 DONE)
- **Expected:** Skips Phase 1, dispatches 6 children sequentially
- **Verify:** 6 detailed plan files + 1 reconciliation file in `docs/plan/`

## TC-2: Dry run
- **Input:** `--dry-run` flag
- **Expected:** Shows dispatch plan (phases, strategy, grouping) without executing
- **Verify:** No child agents triggered, no plan files created

## TC-3: Max batch size
- **Input:** `--max-batch-size 2` with parallel-safe phases
- **Expected:** Dispatches in groups of 2
- **Verify:** No more than 2 concurrent children at any point

## TC-4: Resume from phase
- **Input:** `--from-phase 4` with existing Phase 2-3 plan files
- **Expected:** Picks up existing plans as prior context, starts dispatching from Phase 4
- **Verify:** Phases 2-3 not re-planned, Phase 4+ get prior context

## TC-5: Resume with missing prior plan
- **Input:** `--from-phase 4` but Phase 3 plan file missing
- **Expected:** Warns user about missing Phase 3 plan, asks to confirm
- **Verify:** Does not proceed without explicit confirmation

## TC-6: Child failure
- **Input:** Phase 4 child times out or fails
- **Expected:** Reports error, suggests `--from-phase 4` to resume
- **Verify:** Earlier phase plans preserved, partial results reported

## TC-7: Cumulative decisions summary
- **Input:** Sequential dispatch of 3+ phases
- **Expected:** `_decisions_so_far.md` grows after each child completes
- **Verify:** Later children receive accumulated decisions from all prior phases

## TC-8: Suggested revisions collected
- **Input:** Phase 4 child includes "Suggested Revisions to Prior Phases" section
- **Expected:** Revision collected but NOT acted on mid-sequence
- **Verify:** Revision appears in reconciliation report, not in earlier plan files

## TC-9: Reconciliation detects naming conflict
- **Input:** Phase 2 uses `TenantEntity`, Phase 3 uses `OrganizationEntity` for same concept
- **Expected:** Reconciliation flags naming inconsistency with canonical naming table
- **Verify:** Reconciliation file contains conflict entry and recommendation

## TC-10: Reconciliation detects scope gap
- **Input:** Phase 6 needs test fixture that Phase 5 doesn't create
- **Expected:** Reconciliation flags missing dependency
- **Verify:** Scope gap listed in reconciliation with recommended resolution

## TC-11: Reconciliation surfaces revision requests
- **Input:** Multiple children flag revisions to Phase 2
- **Expected:** Grouped by target phase in reconciliation report with assessment
- **Verify:** Prior phase revision section present and grouped correctly
