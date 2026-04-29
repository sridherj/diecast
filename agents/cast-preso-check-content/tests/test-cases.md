# Test Cases: cast-preso-check-content

Six test cases covering the base 8 criteria and slide-type-specific checks.

## Test 1: Clean Pass

**Mock Input:**
- `what/test-01.md`: outcome = "Audience identifies agent capabilities in <5 sec", L1 = ["Capabilities list"], L2 = ["Personalization notes"], slide_type = information, verification = ["takeaway clear in 5 sec"]
- `how/test-01/slide.html`: large heading "What agents can do", 3 bullets (6-10 words each), single muted callout at the bottom for L2 personalization note. Total body text ~35 words.

**Expected Output:**
```json
{
  "dimension": "content",
  "verdict": "PASS",
  "score": 0.90,
  "evidence": "Single clear takeaway (agent capabilities). L1 bullets dominant, L2 present as muted callout. All 8 base criteria + no type-specific check required.",
  "issues": [],
  "checks_performed": [
    {"criterion": "achieves-stated-outcome", "result": "PASS", ...},
    ...
  ]
}
```

Score range: > 0.85.

---

## Test 2: Too Many Ideas

**Mock Input:**
- `what/test-02.md`: outcome = "Audience understands why AI-native agents win", L1 = ["capabilities", "recruitment", "orchestration"] (three equal-weight L1s — a WHAT-doc smell, but happens)
- `how/test-02/slide.html`: title + 3 columns with equal font size, each presenting a different L1 concept with 4-5 bullets. No single hero.

**Expected Output:**
- `verdict`: FAIL
- Issues include:
  - `one-clear-takeaway` — error — "3 competing concepts at equal weight; cannot identify single takeaway in <5 sec"
  - `l1-l2-hierarchy` — error — "All 3 L1s compete for attention; no single one is visually prominent"
  - Possibly `one-idea-per-slide` — warning

Score range: < 0.65.

---

## Test 3: Missing Outcome

**Mock Input:**
- `what/test-03.md`: outcome = "Audience feels the urgency of building now, not later", slide_type = moment
- `how/test-03/slide.html`: well-designed slide but communicates "agent architecture overview" (not urgency). Beautiful visuals, clean hierarchy.

**Expected Output:**
- `verdict`: FAIL
- Primary issue: `achieves-stated-outcome` (error) — "Slide covers agent architecture; WHAT doc asks for urgency of building now. No connection to stated outcome."
- Also fails: `moment-emotional-anchor` (type-specific) — "No emotional pull; reads as information slide."
- `what_worked` field: "Visual design is clean; hierarchy is clear. Content is on a different topic."

Score range: 0.55-0.70.

---

## Test 4: Hook Slide — No Tension

**Mock Input:**
- `what/test-04.md`: slide_type = hook, outcome = "Audience wants to know how to find 28 companies in 4 months"
- `how/test-04/slide.html`: title "Company Research" + bullets listing research methodology. Factual, calm, no tension.

**Expected Output:**
- `verdict`: FAIL
- Primary issue: `hook-creates-tension` (type-specific error) — "Slide states facts about research methodology. No pain point, no question, no curiosity trigger. Audience has no reason to want the next slide."
- May also flag: `achieves-stated-outcome` — "Does not create the desire to know how 28 companies in 4 months happened."

Score range: 0.55-0.70.

---

## Test 5: Body Text Overflow

**Mock Input:**
- `what/test-05.md`: outcome = any, slide_type = information
- `how/test-05/slide.html`: title + 4 bullets where each bullet is a full sentence averaging 20 words. Total body text = 82 words. Speaker notes excluded from count.

**Expected Output:**
- `verdict`: FAIL
- Primary issue: `max-50-words-body` (error) — "Body text word count: 82 (limit: 50). Bullets average 20 words each. Compress or split."
- May also flag: `no-rambling` — "Each bullet restates the same point; 2-3 are redundant."

Score range: 0.65-0.75.

---

## Test 6: Verification Criteria Miss

**Mock Input:**
- `what/test-06.md`: verification_criteria = ["viewer can identify the agent's value proposition in <5 sec"]
- `how/test-06/slide.html`: 2-paragraph text block explaining agent capabilities. Reading time ~25 sec.

**Expected Output:**
- `verdict`: FAIL
- Primary issue: `meets-verification-criteria` (error) — "WHAT doc specifies <5 sec identification. Slide requires ~25 sec to read and extract value proposition. Verification criterion not met."
- `what_good_looks_like`: "Lead with a single-sentence value proposition at hero size. Move the paragraph content to speaker notes or a supporting L2 element."

Score range: 0.70-0.80.

---

## Notes

- Every test should return a valid D1 JSON verdict
- `checks_performed` must list ALL 8 base criteria + the type-specific criterion (if applicable)
- `what_worked` is mandatory when `verdict: "FAIL"` — prevents regression in rework
- Evidence strings should quote from the mock input (or describe the element concretely)
