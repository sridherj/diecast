# Test Cases: taskos-preso-narrative-checker

## Test 1: Good narrative — should PASS
- Input: narrative-gold-standard.md from references/
- Expected: 14/14 PASS

## Test 2: Vague outcomes — should FAIL checks 3 and 4
- Input: Narrative with outcomes like "understand the product" and "learn about AI"
- Expected: FAIL on checks 3 (concrete) and 4 (verifiable)

## Test 3: Too many slides — should FAIL check 6
- Input: Narrative with 15 core flow slides
- Expected: FAIL on check 6 (≤12 slides)

## Test 4: Missing type annotations — should FAIL check 8
- Input: Narrative with slide types omitted
- Expected: FAIL on check 8 (type annotations present)

## Test 5: All moments, no information — should FAIL check 11
- Input: Narrative where every slide is typed as "moment" or "reveal"
- Expected: FAIL on check 11 (not enough breathing room)

## Test 6: Premature design — should FAIL check 13
- Input: Narrative that says "use a side-by-side comparison layout with watercolor illustration"
- Expected: FAIL on check 13 (premature visual design)
