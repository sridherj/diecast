# `cast-preso-how` — Manual Test Cases

> 12 core scenarios + 1 cross-slide isolation test. These are **manual** test cases — run when the agent is invoked and inspect outputs for the expected behaviors listed.

## Test Case Index

| # | Test Case | Mode | Focus |
|---|-----------|------|-------|
| 1 | Hook slide — Single-Stat Hero | normal | Archetype selection, no illustration |
| 2 | Information slide — Consulting Exhibit with illustration | normal | Watercolor delegation, asset wiring |
| 3 | Reveal slide — Code-Snippet with auto-animate | normal | Multi-section output, `data-auto-animate` pairing |
| 4 | Rework mode — tone checker failure | rework | Feedback reading, version preservation |
| 5 | Regeneration mode — the user edits brief | regenerate | Skip Steps 2-5, respect edited brief |
| 6 | One-idea validation failure | normal | Blocking open question, proceed with primary |
| 7 | Illustration delegation with inline SVG | normal | SVG element substitution (not `<img>`) |
| 8 | Illustration delegation failure/timeout | normal | Graceful fallback, placeholder preservation |
| 9 | Version A/B end-to-end | normal | Two HTML files + recommended copy |
| 10 | Moment slide with no fragments | normal | Slide type determines fragment strategy |
| 11 | Open questions + assembler notes | normal | Both log files populated with correct format |
| 12 | Context loading failure | normal | Fast-fail with no partial output |

Plus: **Cross-slide isolation** — `slide-01` and `slide-02` run in parallel, each reads only its own WHAT doc, writes only its own `how/{slide_id}/`.

---

## Test 1: Hook slide — Single-Stat Hero

**Input:**
- `what/02-staleness-pain.md` — slide_type=`hook`, Top-Level Outcome: "Audience recognizes how quickly LinkedIn connections go stale — 73% within 2 years." L1: "73% staleness" + "pain is invisible until you need an intro."
- `narrative.collab.md` — 02-staleness-pain is slide 2 of 10, paired with reveal at slide 4.
- No illustration required in WHAT doc.

**Expected behavior:**
- Step 3 shortlists Single-Stat Hero, One-Statement, Compare/Contrast (primary for hook).
- Step 4 brainstorms all 3 approaches with slide-specific pros/cons and honest Steve Jobs tests.
- Step 4 selects Single-Stat Hero with the "73%" stat — rationale references the stat's narrative role.
- Step 5 brief has all sections, L1 "73% staleness" mapped to hero stat, L2 mapped to subtitle line.
- Step 6 HTML: `<section id="02-staleness-pain">`, `<h2>` is a complete-sentence action title, 70%+ whitespace, no bullets, no illustration.
- Step 7 skipped — no illustration.
- Step 8: `open_questions.md` and `notes_for_assembler.md` both created (likely both say "_No ..._").

**Failure criteria:**
- `<h2>` is a label (e.g., "Staleness"). Test fails.
- More than 8 words of supporting context below the stat. Test fails.
- Any fragments used (hook default is minimal; stat should land immediately). Test fails.

---

## Test 2: Information slide — Consulting Exhibit with illustration

**Input:**
- `what/06-agent-marketplace.md` — slide_type=`information`, Top-Level Outcome: "Audience sees what an agent marketplace looks like as a concrete product surface." L1: 3 data points about the marketplace.
- WHAT doc explicitly lists "illustration of agent profile card" as a required asset.
- `cast-preso-illustration-creator` is available (dispatch returns 200).

**Expected behavior:**
- Step 3 shortlists Consulting Exhibit, Diagram-with-Annotations, Build-Up Sequence.
- Step 4 selects Consulting Exhibit — action title is the finding, exhibit is the illustration + 3 data callouts.
- Step 5 brief has `Illustration Needed: Yes`, `Type: Watercolor`, scene brief with subject/composition/elements/mood/size/text=NONE.
- Step 6 HTML has `<img src="assets/06-agent-marketplace-hero.webp">` placeholder inside the exhibit layout.
- Step 7 dispatches illustration-creator via HTTP POST, polls every 10s, receives asset filename.
- Step 7 updates `slide.html` `<img src=>` to the returned filename (still under `assets/`).
- Final `slide.html` references the real asset, not the placeholder name.

**Failure criteria:**
- HOW agent re-runs illustration quality checks (should NOT — illustration-creator owns that).
- Asset path becomes absolute or uses external URL. Test fails.
- Consulting Exhibit without an action title sentence in `<h2>`. Test fails.

---

## Test 3: Reveal slide — Code-Snippet with auto-animate

**Input:**
- `what/04-nl-query-reveal.md` — slide_type=`reveal`, paired with hook at slide 3.
- WHAT doc has before/after code snippets (200-line SQL → 1-line NL query).
- Narrative notes that slide 3 and 4 should feel like a single morph.

**Expected behavior:**
- Step 3 shortlists Code-Snippet Showcase, Compare/Contrast.
- Step 4 selects Code-Snippet with `data-auto-animate` pairing to the hook.
- Step 6 writes TWO `<section>` elements in `slide.html` (or coordinates with slide 3 via assembler note).
- Both sections carry `data-auto-animate` on the section and matching `data-id="code-block"` on the `<pre>`.
- `notes_for_assembler.md` includes a dependency note: "This slide pairs with 03-manual-sql via data-auto-animate. Keep adjacent in deck order. Preserve data-id."

**Failure criteria:**
- `data-id` attributes don't match between the two sections. Test fails.
- No assembler note about the pairing. Test fails.

---

## Test 4: Rework mode — tone checker failure

**Input:**
- Existing `how/05-agent-resume/brief.collab.md` and `slide.html` from a prior run.
- Delegation context includes `checker_feedback` path pointing to a file that says: "GPT-isms detected: 'leverage,' 'unlock value.' Bullets too long (average 14 words; target ≤ 8)."

**Expected behavior:**
- Agent enters Rework Mode — skips brainstorming.
- Ranks failures: tone issues (GPT-isms + bullet length). Both tone dimension — treated as one rework pass.
- Edits text in the brief and HTML to replace GPT-isms and shorten bullets.
- Moves the old `slide.html` to `versions/v1.html` before writing the new one.
- Updates the brief's Rework History section with: failed criterion verbatim, what changed, why.
- Does NOT re-run archetype selection or change layout.

**Failure criteria:**
- Layout changes alongside tone fix (that's a dimension violation). Test fails.
- Old `slide.html` is overwritten without being archived to `versions/`. Test fails.
- Rework History section not updated. Test fails.

---

## Test 5: Regeneration mode — the user edits brief

**Input:**
- Existing `how/07-orchestrator/brief.collab.md` with archetype set to Single-Stat Hero (from prior run).
- the user manually edited the brief: Chosen Archetype now reads "Compare/Contrast" with different L1 treatment notes.
- Delegation context: `regenerate: true`. Also carries pending `checker_feedback` from an incomplete rework loop.

**Expected behavior:**
- Step 1 validates inputs.
- Steps 2-5 SKIPPED entirely.
- Reads the edited brief as source of truth — detects new archetype.
- Step 6 generates new HTML using `compare-contrast.html` template, NOT the prior hero layout.
- Moves prior `slide.html` to `versions/pre-regen-{timestamp}.html`.
- `checker_feedback` file renamed with `.archived` suffix — IGNORED in this run.
- Output acknowledges regen mode in summary; no rework history entry added (this is regen, not rework).

**Failure criteria:**
- Agent reruns brainstorming. Test fails.
- `checker_feedback` is applied alongside regen. Test fails.
- New HTML still uses the old archetype layout. Test fails.

---

## Test 6: One-idea validation failure

**Input:**
- `what/09-problem-and-solution.md` — Top-Level Outcome: "Audience understands the manual pain AND sees the solution." L1 has 4 entries spanning both problem and solution.

**Expected behavior:**
- Step 1 detects "and" joining two distinct concepts + L1 count > 3.
- Logs blocking open question `OQ-3-09-problem-and-solution-01` with severity=blocking, category=scope, recommendation="split into two slides: 09-pain and 09-solution."
- Agent proceeds with the primary idea (first L1 entry) — does NOT block on resolution.
- Brief and HTML reflect the primary idea only. A note in the brief's Selection Rationale explicitly flags the split recommendation.
- `human_action_needed: true` in output contract; `human_action_items` includes "Review OQ-3-09-... and decide whether to split slide 09."

**Failure criteria:**
- Agent blocks or fails without producing artifacts. Test fails (should proceed with primary).
- Open question not logged. Test fails.

---

## Test 7: Illustration delegation with inline SVG

**Input:**
- `what/08-architecture.md` — requires a diagram of the orchestrator-to-agents flow.
- Brief's Illustration Requirements: `Type: Inline SVG`, subject="3-node orchestrator with arrows to 5 leaf agents."
- illustration-creator returns `<svg viewBox=...>...</svg>` markup (not a file).

**Expected behavior:**
- Step 6 writes `slide.html` with an `<img>` placeholder inside a positioning wrapper (`<div>` with width/margin style).
- Step 7 dispatches illustration-creator; receives SVG markup in output.
- Agent REPLACES the `<img>` element with the returned `<svg>` markup, preserving the parent wrapper's positioning styles.
- Final `slide.html` contains an inline `<svg>` with `viewBox` and percentage widths — no fixed pixels.

**Failure criteria:**
- `<img>` still present alongside `<svg>`. Test fails.
- SVG has hardcoded `width=` and `height=` in pixels. Test fails.
- Parent wrapper removed, SVG dropped naked into the slide. Test fails.

---

## Test 8: Illustration delegation failure / timeout

**Input:**
- Slide requires watercolor illustration.
- illustration-creator dispatch times out (no output JSON after 30 minutes) OR returns HTTP 500 twice after retry.

**Expected behavior:**
- Step 7 respects the 30-min timeout and stops polling.
- Placeholder `<img>` preserved in `slide.html` with the planned filename — slide still renders.
- `open_questions.md` logs: "Illustration for {slide_id} not generated — illustration-creator timed out. Placeholder image in place. Needs human attention to re-run or substitute."
- `status: "partial"` in output contract, `human_action_needed: true`.
- Agent does NOT fail — partial output is valid.

**Failure criteria:**
- Agent fails outright. Test fails (should produce partial output).
- Placeholder removed, slide broken. Test fails.

---

## Test 9: Version A/B end-to-end

**Input:**
- Step 4 produces two approaches (Single-Stat Hero and One-Statement) that score within 10% on the Steve Jobs test.

**Expected behavior:**
- Brief contains both approaches in "Approaches Considered" + populated Version A/B section with explicit "the user decides" note.
- Step 6 writes `versions/version-a.html` (Single-Stat Hero) and `versions/version-b.html` (One-Statement).
- Step 6 copies Version A (the recommended one) to `slide.html` with a comment marker: `<!-- Recommended Version A. See versions/ for alternatives. -->`.
- `open_questions.md` logs a nice-to-have question: "the user: pick Version A or B. Differs in [concrete difference]."

**Failure criteria:**
- Only one HTML file written. Test fails.
- `slide.html` lacks the version marker comment. Test fails.
- No open question flagging the user decision. Test fails.

---

## Test 10: Moment slide with no fragments

**Input:**
- `what/10-pause.md` — slide_type=`moment`. Top-Level Outcome: "Audience feels the weight of the before/after transformation."

**Expected behavior:**
- Step 3 shortlists Illustrated Section Opener, One-Statement.
- Step 4 selects one, Steve Jobs tested.
- Step 6 HTML contains ZERO `class="fragment"` elements — whole slide is the message.
- Brief's Fragment / Animation Plan reads: "1. Whole slide visible — no fragments."

**Failure criteria:**
- Any `class="fragment"` in output HTML. Test fails.
- Brief lists 2+ fragment steps for a moment slide. Test fails.

---

## Test 11: Open questions + assembler notes

**Input:**
- Slide has an ambiguous illustration requirement (WHAT doc says "illustration of the system" with no subject details) AND the brief uses `data-auto-animate` linking to the next slide.

**Expected behavior:**
- `open_questions.md` contains at least one entry with full format (ID, From, Severity, Category, Question, Context, Recommendation).
- `notes_for_assembler.md` contains at least one entry with format (Note title, From, Type, Note, Action).
- Both files parse (valid markdown headers, all fields present).
- Each entry is categorized correctly (open question = `technical`, assembler note = `dependency`).

**Failure criteria:**
- Missing field in either log format. Test fails.
- Empty file where entries expected. Test fails.

---

## Test 12: Context loading failure

**Input:**
- Delegation references `slide_id="12-missing"` but `what/12-missing.md` does NOT exist.

**Expected behavior:**
- Step 1 detects missing WHAT doc immediately.
- Output contract written with `status: "failed"`, errors array includes the missing path.
- NO `how/12-missing/` directory created — no partial artifacts.
- No assumptions made (no default outcomes, no placeholder content).

**Failure criteria:**
- Any artifact written under `how/12-missing/`. Test fails.
- Agent proceeds past Step 1 with made-up content. Test fails.
- Error message doesn't include the missing path. Test fails.

---

## Cross-Slide Isolation Test

**Input:** Dispatch two HOW agent runs in parallel:
- Run A: `slide_id=01-opening`, reads `what/01-opening.md`, writes `how/01-opening/`.
- Run B: `slide_id=02-staleness-pain`, reads `what/02-staleness-pain.md`, writes `how/02-staleness-pain/`.

**Expected behavior:**
- Each run only reads its own WHAT doc (verifiable via file-access logs).
- Each run only writes to its own `how/{slide_id}/` directory — no cross-pollination.
- No shared state between runs (no global open-questions file, no shared assets dir).
- Both runs can complete in parallel with no locking, no interference.

**Failure criteria:**
- Run A writes to `how/02-staleness-pain/` or vice versa. Test fails.
- Either run reads the other's WHAT doc. Test fails.
- Any shared-state contention (file lock, partial overwrite). Test fails.
