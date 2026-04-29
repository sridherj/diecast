# Test Cases: goal-decomposer

## Scenario 1: Simple project goal
**Input:** "break this down: build a personal blog"
**Expected:** 3-7 steps covering tech stack, design, content, deployment. Each step has substeps and success criteria. 10x section included.
**Status:** Not tested

## Scenario 2: Complex multi-domain goal
**Input:** "decompose this goal: transition from engineer to CTO at a startup"
**Expected:** Steps covering technical leadership, hiring, strategy, culture. Dependencies between steps are explicit. 10x section has genuinely novel insights.
**Status:** Not tested

## Scenario 3: Ambiguous goal triggers clarification
**Input:** "what are the steps to get better?"
**Expected:** Agent asks 1-2 clarifying questions before decomposing
**Status:** Not tested

## Scenario 4: File output when directory provided
**Input:** Goal + output directory path
**Expected:** `steps.ai.md` saved to the specified directory
**Status:** Not tested
