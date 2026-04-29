# Test Cases: task-suggester

## Scenario 1: Exploration phase with no existing tasks
**Input:** Goal with requirements.human.md + plan.collab.md, phase=exploration, empty tasks.md
**Expected:** 3-5 research/spike tasks, all with outcomes, effort_estimate 30-60m, recommended_agent where applicable
**Status:** Not tested

## Scenario 2: Execution phase with existing tasks
**Input:** Goal with plan.collab.md showing 3 phases, tasks.md with 5 completed execution tasks
**Expected:** Next batch of execution tasks that DON'T duplicate existing ones, building on completed work
**Status:** Not tested

## Scenario 3: Spike task generation
**Input:** Goal with requirements mentioning "evaluate unknown API X"
**Expected:** At least one task with is_spike=true, effort_estimate=30m, outcome includes "decision on feasibility"
**Status:** Not tested

## Scenario 4: Course correction
**Input:** tasks.md with 3 recent tasks marked moved_toward_goal="no"
**Expected:** Warning/note about course correction, suggests re-evaluation or pivot tasks
**Status:** Not tested

## Scenario 5: Output schema compliance
**Input:** Any goal
**Expected:** Valid JSON array, every object has title+outcome+phase (required fields), effort_estimate is "30m"|"45m"|"60m"
**Status:** Not tested

## Scenario 6: No duplicate suggestions
**Input:** Goal with tasks.md containing "Research auth providers"
**Expected:** No suggestion with title similar to "Research auth providers"
**Status:** Not tested
