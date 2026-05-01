# Test Cases: cast-preso-check-coordinator

Seven coordinator unit tests + seven integration tests covering the full HOW → check → rework loop.

---

# Part A: Coordinator Unit Tests

These tests stub child checker outputs (or mock dispatch) and verify the coordinator's aggregation, adversarial pass, decision logic, and cross-slide handling.

## Unit Test 1: Full Mode — All Pass

**Input:**
- Clean slide
- `check_mode: full`, `rework_iteration: 0`
- Stubbed checker verdicts: content PASS (0.90), visual PASS (0.88), tone PASS (0.92)

**Expected Behavior:**
- Dispatches 3 children in parallel (check via `/api/agents/jobs/{run_id}?include=children` — assert `len(json.children) == 3`)
- Waits for all 3 output.json files (barrier)
- Runs adversarial pass (4 questions) → PASS
- Decision: APPROVED
- Writes `how/{slide_id}/check-results.json` with `decision: "approved"`
- Does NOT write `checker_feedback.md`

---

## Unit Test 2: Full Mode — Tone Fail

**Input:**
- Slide with GPT-isms (`test-slide-gptisms.html` fixture)
- `check_mode: full`, `rework_iteration: 0`
- Stubbed verdicts: content PASS (0.88), visual PASS (0.85), tone FAIL (0.45 — 3 GPT-isms)

**Expected Behavior:**
- Aggregated verdict: FAIL (tone)
- Decision: REWORK
- Writes `checker_feedback.md` with tone-focused issues
- `what_worked` field lists content and visual as dimensions to preserve
- Rework guidance: "Focus on: remove GPT-isms. Do NOT change: content structure, visual layout."

---

## Unit Test 3: Full Mode — Adversarial Catch

**Input:**
- All 3 checkers PASS (0.85+)
- But the slide is generic AI aesthetic — adversarial pass catches it

**Expected Behavior:**
- Content PASS, visual PASS, tone PASS (all technically clean)
- Adversarial pass question 1 ("What would Steve Jobs reject?") returns damning answer
- Decision: REWORK (adversarial override)
- `checker_feedback.md` lists the adversarial findings

---

## Unit Test 4: Lightweight Mode

**Input:**
- Title slide (`test-slide-title.html` fixture)
- `check_mode: lightweight`

**Expected Behavior:**
- NO child dispatches (verify via `/api/agents/jobs/{coordinator_run_id}?include=children` — assert `json.children == []`)
- Coordinator runs 6 condensed checks itself
- Response time < 5 min (no child dispatch overhead)
- Writes lightweight verdict to output.json
- Does NOT run adversarial pass (skipped for lightweight)

---

## Unit Test 5: Rework Iteration 3 → Escalate

**Input:**
- Slide still failing at iteration 3
- `rework_iteration: 3`, `previous_feedback: path/to/iter2_feedback.md`

**Expected Behavior:**
- Decision: ESCALATE (not REWORK)
- `check-results.json` has `decision: "escalated"`
- `checker_feedback.md` includes:
  - Best version so far (path)
  - What's still failing (specific criteria)
  - What was tried across iterations 0, 1, 2 (summary)
  - One specific question for the user

---

## Unit Test 6: Oscillation Detection

**Input:**
- Iteration 1 scores: content 0.90, visual 0.85, tone 0.80
- Iteration 2 scores: content 0.90, visual 0.70 (regressed!), tone 0.85

**Expected Behavior:**
- current_score (minimum across dimensions) = 0.70
- previous_score = 0.80
- Drop = 0.10 > 0.05 threshold → oscillation detected
- Decision: ESCALATE (oscillation)
- `check-results.json` has `decision: "escalated_oscillation"`
- `checker_feedback.md` notes the regressed dimension (visual) with a specific delta

---

## Unit Test 7: Cross-Slide Consistency

**Input:**
- `cross_slide_mode: true`
- `all_slide_ids: ["test-cs-01", "test-cs-02", "test-cs-03", "test-cs-04", "test-cs-05"]`
- Slides 01, 02, 04, 05 all use 42px h2, `#1A1A28` text, watercolor illustrations
- Slide 03 uses 36px h2, `#333` text (typography drift)

**Expected Behavior:**
- Coordinator reads all 5 `how/{slide_id}/slide.html` files
- Extracts per-slide structured summaries (not raw HTML)
- Flags slide test-cs-03: typography drift (36px h2 ≠ 42px deck standard)
- Flags slide test-cs-03: color drift (`#333` ≠ `#1A1A28`)
- Does NOT flag 01, 02, 04, 05
- Writes `cross-slide-results.json` with `drift_flags` array
- Drift flags include specific fix suggestions (not full checker_feedback.md)

---

# Part B: Integration Tests

These tests exercise the full HOW → check → rework loop with real child agents and fixtures.

## Integration Test 1: Happy Path — Single Slide, Full Check

**Setup:**
1. Use a test WHAT doc (from fixtures or Phase 2C)
2. Run HOW maker to produce `how/test-01/slide.html`
3. Trigger check-coordinator with `check_mode: full`, `rework_iteration: 0`

**Verify:**
- [ ] Coordinator dispatched 3 child checkers (visible in `/api/agents/jobs/{coord_run_id}?include=children` — assert `len(json.children) == 3`)
- [ ] All 3 checkers produced verdicts in their respective `.agent-{run_id}.output.json`
- [ ] Coordinator aggregated verdicts into `how/test-01/check-results.json`
- [ ] Adversarial pass ran (4 questions visible in check-results.json)
- [ ] Decision is either APPROVED or REWORK (both valid — testing the pipeline)
- [ ] If REWORK: `how/test-01/checker_feedback.md` exists with structured feedback (D6 format)
- [ ] If APPROVED: no checker_feedback.md written

---

## Integration Test 2: Rework Loop — Deliberate Tone Failure

**Setup:**
1. Create test WHAT doc for an information slide
2. Use `fixtures/test-slide-gptisms.html` as `how/test-02/slide.html`
3. Trigger check-coordinator with `check_mode: full`, `rework_iteration: 0`

**Verify:**
- [ ] Tone checker returns FAIL with specific GPT-isms listed in `issues`
- [ ] Content and visual pass (tone is the only failing dimension)
- [ ] Coordinator writes `checker_feedback.md` with tone-focused rework guidance
- [ ] `what_worked` field mentions content and visual as dimensions to preserve
- [ ] Feed `checker_feedback.md` to HOW maker as `checker_feedback` input
- [ ] HOW maker produces revised slide without GPT-isms
- [ ] Re-trigger coordinator with `rework_iteration: 1`, `previous_feedback: how/test-02/checker_feedback.md`
- [ ] Tone checker now passes on revised slide
- [ ] Tone score in iteration 1 > tone score in iteration 0
- [ ] `check-results.json` records both iterations' scores for comparison

---

## Integration Test 3: Lightweight Mode — Title Slide

**Setup:**
1. Use `fixtures/test-slide-title.html` as `how/test-03/slide.html`
2. Trigger check-coordinator with `check_mode: lightweight`

**Verify:**
- [ ] No child agents dispatched (`/api/agents/jobs/{coord_run_id}?include=children` — assert `json.children == []`)
- [ ] Coordinator ran 6 condensed checks itself
- [ ] Verdict returned in output.json with `mode: "lightweight"` and 6 checks_performed entries
- [ ] No adversarial pass ran (skipped for lightweight)
- [ ] Response time < 5 min (no child dispatch overhead)

---

## Integration Test 4: Cross-Slide Consistency — Typography/Color Drift

**Setup:**
1. Place `fixtures/test-slide-drift-{01,02,03}.html` into `how/test-cs-{01,02,03}/slide.html`
2. Slides 01, 02: 42px h2, `#1A1A28` text (consistent toolkit tokens)
3. Slide 03: deliberately drifted — 36px h2, `#333` text
4. Trigger coordinator with `cross_slide_mode: true`, `all_slide_ids: ["test-cs-01", "test-cs-02", "test-cs-03"]`

**Verify:**
- [ ] Coordinator reads all 3 slide HTML files
- [ ] Extracts per-slide structured summaries (D5 format, not raw HTML comparison)
- [ ] Flags test-cs-03: typography drift (36px h2 ≠ deck standard 42px)
- [ ] Flags test-cs-03: color drift (`#333` ≠ `#1A1A28`)
- [ ] Does NOT flag test-cs-01 or test-cs-02
- [ ] Drift flags include specific fix suggestions (e.g., "Change h2 to 42px")
- [ ] `cross-slide-results.json` written with the drift_flags array

---

## Integration Test 4B: Cross-Slide — Illustration Style Drift (Targeted Rework)

**Setup:**
1. Place `fixtures/test-slide-illust-{wc-01,wc-02,vector-03}.html` into `how/test-id-{01,02,03}/slide.html`
2. Slides 01, 02: watercolor illustrations with warm palette (Annie Ruygt style)
3. Slide 03: flat vector illustration with cool palette (different style)
4. Trigger coordinator with `cross_slide_mode: true`, `all_slide_ids: ["test-id-01", "test-id-02", "test-id-03"]`

**Verify:**
- [ ] Coordinator flags test-id-03 for `illustration_style` drift
- [ ] Drift feedback is dimension-specific (illustration style only) — NOT a full checker_feedback.md
- [ ] Targeted rework guidance says to match watercolor style of slides 01-02
- [ ] Non-drifted dimensions (typography, colors, layout) are NOT flagged for test-id-03
- [ ] Route to HOW maker targets ONLY the illustration regeneration, not full slide rebuild

---

## Integration Test 5: Max Rework Escalation

**Setup:**
1. Use a slide that consistently fails one criterion (e.g., GPT-isms that keep returning)
2. Simulate 3 prior iterations with scores: 0.55 → 0.60 → 0.62 (improving but still failing)
3. Trigger coordinator with `rework_iteration: 3`, `previous_feedback: path/to/iter2_feedback.md`

**Verify:**
- [ ] Coordinator returns ESCALATE decision (not REWORK, not another iteration)
- [ ] `checker_feedback.md` includes:
  - Best version so far (path to iteration 2 version)
  - What's still failing (the persistent criterion)
  - What was tried (summary of all 3 attempts)
  - Specific question for the user (one decision needed)
- [ ] `check-results.json` has `decision: "escalated"`

---

## Integration Test 6: Mixed-Mode Batch — Lightweight + Full in Same Run

**Setup:**
1. Create 2 test slides:
   - `how/test-mix-title/slide.html` (title slide, use `fixtures/test-slide-title.html`)
   - `how/test-mix-info/slide.html` (information slide, use `fixtures/test-slide-clean.html`)
2. Trigger coordinator for both in sequence or parallel:
   - title: `check_mode: lightweight`
   - info: `check_mode: full`

**Verify:**
- [ ] Coordinator handles both modes without interference between runs
- [ ] Title slide: 6 condensed checks, no child dispatch (verify empty children list)
- [ ] Information slide: 3 child checkers dispatched + adversarial pass
- [ ] Cross-slide consistency (if run after) works across both despite different check modes
- [ ] Both slides get verdicts in their respective check-results.json

---

## Notes

- Integration tests should produce real agent dispatches; do not stub the child checkers
- Fixtures are stored in `tests/fixtures/` — see the fixture files for content specifications
- Manual validation for now (no automated CI test runner in this sub-phase)
- Record test execution results in a sibling `tests/test-results.md` file after each run
