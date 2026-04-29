# Test Cases: web-researcher

## Scenario 1: Research a well-known topic
**Input:** "research this topic: building a SaaS product"
**Expected:** 7 angle sections, each with real URLs and specific insights. Not generic advice — named tools, specific frameworks, actual Reddit threads.
**Status:** Not tested

## Scenario 2: Research a niche topic
**Input:** "research this topic: building LLM evaluation pipelines"
**Expected:** Still produces 7 angles. Some angles may be thinner for niche topics but should still have substance.
**Status:** Not tested

## Scenario 3: Subagent failure resilience
**Input:** Research with simulated rate limiting
**Expected:** Failed angles are noted, remaining angles still complete. No crash.
**Status:** Not tested

## Scenario 4: File output with directory
**Input:** Topic + output directory path
**Expected:** Research saved as markdown file in the specified directory
**Status:** Not tested

## Scenario 5: WebFetch blocked on research source, fallback to resilient-browser
**Input:** Research topic where a high-value source returns 403
**Expected:**
- WebFetch returns 403 on the source URL
- Agent invokes `/resilient-browser` via haiku subagent (NOT in main agent context)
- Content is extracted and used in the relevant angle
- If resilient-browser also fails, source is noted as unavailable (not silently dropped)
- Other angles continue normally
**Status:** Not tested
