# Test Cases: cast-preso-narrative

## Test 1: Happy path — Cast v2 narrative
- Input: Cast thesis doc + v1 presentation + raw requirements
- Expected: narrative.collab.md with all required sections
- Verify: TG is explicit, outcomes are concrete, ≤12 core slides, aha progression present

## Test 2: Interview skip mode
- Input: Same as Test 1, with skip_interview: true
- Expected: narrative.collab.md synthesized from source material alone
- Verify: Document is complete but may have less the user-specific nuance

## Test 3: Checker rework loop
- Input: Deliberately weak source material (no clear TG)
- Expected: Checker fails, maker revises, re-checks
- Verify: Rework produces improved narrative, max 2 iterations

## Test 4: Missing source files
- Input: delegation_context with non-existent file paths
- Expected: Agent logs missing files, continues with available material
- Verify: Output notes which files were unavailable
