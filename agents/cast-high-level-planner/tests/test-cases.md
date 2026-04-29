# Test Cases: cast-high-level-planner

## Scenario 1: Goal with full exploration
**Input:** Goal directory with requirements.human.md, 3 research files, 2 playbooks, summary.ai.md
**Expected:** plan.collab.md with 3-5 meaningful phases, outcomes per phase, build order diagram
**Verify:**
- Phase names are descriptive (not "Phase 1", "Phase 2")
- Every phase has Outcome, Dependencies, Estimated effort, Verification, Key activities
- Build order ASCII diagram present
- Key Risks & Mitigations table present
- Open Questions section present
**Status:** Not tested

## Scenario 2: Goal with requirements only
**Input:** Goal directory with only requirements.human.md
**Expected:** plan.collab.md with 2-3 high-level phases, more open questions, less detail
**Verify:**
- Overview mentions this is a requirements-only plan
- First phase includes exploration/validation activities
- Open Questions section is substantive (reflecting lack of exploration data)
- Far-out phases have "TBD" effort estimates where appropriate
**Status:** Not tested

## Scenario 3: Goal with existing tasks
**Input:** Goal directory with requirements + tasks.md showing some work done
**Expected:** Plan accounts for completed work, doesn't re-plan done phases
**Verify:**
- Plan acknowledges existing progress in the Overview
- Completed work is not duplicated in phase activities
- Remaining phases build on what's already done
**Status:** Not tested

## Scenario 4: Output quality — phase naming
**Input:** Any goal
**Expected:**
- Phase names are meaningful (not "Phase 1", "Phase 2")
- Phase names describe what's achieved, not what's done
- Names are concise (2-5 words)
**Status:** Not tested

## Scenario 5: Output quality — progressive detail
**Input:** Goal with 4+ phases
**Expected:**
- Near-term phases (1-2) have 3-5 detailed activities with context
- Far-out phases (3+) have 2-3 high-level bullets
- Effort estimates get less precise for later phases
**Status:** Not tested

## Scenario 6: Output quality — parallelism
**Input:** Goal with independent work streams
**Expected:**
- Parallel phases marked with letter suffixes (3a, 3b)
- Build order diagram shows parallel tracks side-by-side
- Dependencies between parallel phases explicitly stated (or "None")
**Status:** Not tested

## Scenario 7: Self-containment test
**Input:** Any goal with exploration artifacts
**Expected:** A fresh Claude context with no prior knowledge of the goal can:
- Understand what each phase achieves from the plan alone
- Know how to verify each phase is done
- Understand the dependency order
- Identify open questions that need resolution
**Status:** Not tested
