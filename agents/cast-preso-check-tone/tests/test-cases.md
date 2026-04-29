# Test Cases: taskos-preso-check-tone

Eight test cases covering all 10 criteria plus the authorship spectrum meta-test.

## Test 1: Clean SJ Voice

**Mock Input:**
- `how/test-01/slide.html` text: "28 companies. $10M pipeline. Built in 4 months."
- Title (assertion): "28 AI-native companies, one pipeline, 4 months"

**Expected Output:**
- `verdict`: PASS
- Score: > 0.90
- Authorship spectrum placement: "Probably human" or "Obviously human-authored"
- Evidence: "Direct, compressed, concrete. Fragments. Specific numbers. SJ voice."

---

## Test 2: GPT-isms

**Mock Input:**
- Text: "We're passionate about leveraging AI to drive innovative solutions that empower our customers."

**Expected Output:**
- `verdict`: FAIL
- Primary issue: `no-gptisms` (error)
  - Banned words present: "passionate", "leveraging", "innovative", "drive [abstract noun: solutions]", "empower"
- Authorship spectrum: "Obviously AI"
- Score: < 0.30 (5 GPT-isms × -0.2 = -1.0; floored at 0.0)

---

## Test 3: Em Dash

**Mock Input:**
- Text: "The system — which handles 10K requests — is production-ready."

**Expected Output:**
- `verdict`: FAIL
- Primary issue: `no-gptisms` (error) — "2× em dashes detected (`—`). Em dashes are AI tells. Use `--` or split into two sentences."
- `what_good_looks_like`: "'The system handles 10K requests. Production-ready.'"
- Score: 0.60 (2× em dash × -0.2 = -0.4)

---

## Test 4: Hedging

**Mock Input:**
- Text: "It could be said that our approach is arguably more effective in many ways."

**Expected Output:**
- `verdict`: FAIL
- Primary issue: `no-hedging` (error) — "3 hedges: 'it could be said that', 'arguably', 'in many ways'. Remove all hedging."
- `what_good_looks_like`: "'Our approach works better. Here's why.'"

---

## Test 5: Wordy Bullets

**Mock Input:**
- 3 bullets, each ~25 words:
  - "Our system leverages advanced machine learning techniques to process incoming requests at scale while maintaining reliability guarantees"
  - "We built a comprehensive monitoring framework that enables real-time observability across distributed components at any scale"
  - "The architecture supports extensibility through well-defined interfaces allowing future integration with emerging technology stacks"

**Expected Output:**
- `verdict`: FAIL
- Primary issue: `bullet-max-15-words` (error) — "Bullet 1: 19 words. Bullet 2: 20 words. Bullet 3: 17 words. All exceed 15-word limit."
- Also: `no-gptisms` (error) — multiple ("leverages", "advanced", "comprehensive", "scale", "robust"-family words)
- Score: < 0.35

---

## Test 6: Third Person

**Mock Input:**
- Text: "SJ built this system over 4 months. Sridher's approach focused on concrete outcomes."

**Expected Output:**
- `verdict`: FAIL
- Primary issue: `first-person-only` (error) — "Uses 'SJ' and 'Sridher' in third person. Switch to 'I' or 'we'."
- `what_good_looks_like`: "'Built this in 4 months. Focused on concrete outcomes.'"

---

## Test 7: Prose Paragraph

**Mock Input:**
- Information slide (not hero, not close)
- Body: "The system we built handles incoming requests through a multi-stage pipeline. Each stage performs a specific transformation, passing results to the next stage. This architecture allows for modular extension and independent scaling of each stage."

**Expected Output:**
- `verdict`: FAIL
- Primary issue: `bullet-based-not-prose` (error) — "3-sentence paragraph on an information slide. Expected bullets or assertion statements."
- Also: `short-sentences` (warning) — sentences around 15-18 words each

---

## Test 8: Borderline — Textbook Business English

**Mock Input:**
- Text: "This initiative represents a strategic effort to modernize our customer engagement infrastructure. Key benefits include improved response times and enhanced user satisfaction metrics."
- No individually banned words — no "passionate", no "leverage", no em dashes, no hedges

**Expected Output:**
- `verdict`: FAIL (from meta-test, not individual criteria)
- Authorship spectrum: "Probably AI"
- Primary issue: `sj-voice-match` (error) — "No individually banned words. But reads as textbook business English: 'initiative', 'represents', 'strategic effort', 'key benefits include', 'enhanced...metrics'. This is the authorship-spectrum failure mode. Score hit from meta-test, not specific word triggers."
- Score: < 0.55 (authorship spectrum fail adds -0.2 on top of baseline)

---

## Notes

- Tone scoring is harsher than content/visual (-0.2 per GPT-ism / em dash vs -0.15 per error in other checkers)
- Authorship spectrum meta-test overrides individual criterion results when placement is "Probably AI" or worse
- `first-person-only` has an exception for credentials/resume slides where the proper name is intentional — check `brief.collab.md` for intent
- Em dashes (`—`, `–`) are always FAIL on `no-gptisms`, never a warning
