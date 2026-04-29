# Test Cases: explore

## Scenario 1: End-to-end exploration
**Input:** "explore how to build an AI-powered code review tool"
**Expected:**
- Interactive phase: asks clarifying questions, presents steps, waits for approval
- Autonomous phase: spawns parallel researchers and synthesizers
- Output: `explorations/YYYY-MM-DD-ai-code-review/` with steps.ai.md, research/, playbooks/, summary.ai.md
- Summary has impact ratings, top 3 recommendations, surprising insights
**Status:** Not tested

## Scenario 2: Goal clarification
**Input:** Vague goal like "explore how to get better at my career"
**Expected:** Asks 2-3 targeted clarifying questions before decomposing
**Status:** Not tested

## Scenario 3: Step modification
**Input:** User modifies proposed steps (add/remove/reorder)
**Expected:** Incorporates feedback, saves updated steps.ai.md, researches the modified list
**Status:** Not tested

## Scenario 4: Partial failure resilience
**Input:** Full exploration where some researcher subagents fail
**Expected:** Summary notes which steps had incomplete research. Other playbooks still generated.
**Status:** Not tested
