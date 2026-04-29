# Compliance Checker Test Cases

Manual test scenarios for `taskos-preso-compliance-checker`. Uses assembled output from the assembler test fixtures.

## Scenario 4: Compliance Pass Case

**Setup:** Run the assembler on its test fixtures. Use the resulting `assembly/` as input here.

**Steps:**
1. Run checker on assembled test deck + test narrative.
2. All 8 passes should PASS.
3. Verify the report format matches the template in the brain.
4. Verify no `routing_recommendations.md` is written (no failures).

**Pass criteria:** Clean compliance report, no routing file.

## Scenario 5: Deliberate Failures

**Setup:** Create a variant narrative with a stricter walk-away outcome:
> "Audience can name 3 specific technical advantages"

The test slides don't satisfy this (they only mention 2 advantages, and not by name).

**Steps:**
1. Run checker with the stricter narrative.
2. Verify Pass 3 (Walk-Away Outcomes) FAILs.
3. Verify routing points to the specific slides that should carry the third advantage.
4. Verify classified as "route to `taskos-preso-how`" (not "escalate to SJ" — content fix, not structural).

**Pass criteria:** Failure surfaced on Pass 3, routing to HOW for named slides.

## Scenario 6: Print-PDF Export (Manual)

**Steps:**
1. Open `assembly/index.html?print-pdf` in Chrome.
2. Verify fragments visible (not hidden).
3. Verify nav markers and back-links hidden (via print CSS).
4. Verify one slide per page.
5. Document outcomes in `tests/print-pdf-results.md`.

**Pass criteria:** Readable print-to-PDF output with no nav chrome.

## Scenario 8: Routing Differentiation

**Setup:** Create a fixture variant with a broken deep-dive link (`href="#/nonexistent-id"`).

**Steps:**
1. Run compliance checker.
2. Verify Pass 6 (Navigation Integrity) fails.
3. Verify routing points to `taskos-preso-assembler` (not `taskos-preso-how`) — broken nav is a wiring issue, not a content issue.

**Pass criteria:** Routing differentiation works — the checker distinguishes content failures from assembly failures.
