# Test Cases: cast-preso-what-checker

## Test 1: Passing WHAT Doc
**Input:** Well-formed what/ doc that meets all 7 criteria
**Expected:** PASS verdict, evidence for each check, "what_worked" populated

## Test 2: Deliberate Defects
**Setup:** Take a passing doc, introduce:
- Defect A: Paragraph as top-level outcome (should fail check 1)
- Defect B: Remove all resources (should fail checks 4, 5)
- Defect C: Vague verification criteria "slide looks good" (should fail check 6)

**Expected:**
- Specific FAIL verdicts with evidence quoting the defective content
- "What worked" still acknowledges passing checks
- Feedback specific enough for maker to fix

## Test 3: Rework Validation
**Input:** Revised doc after rework
**Expected:** Previously failing checks now pass, previously passing checks still pass
