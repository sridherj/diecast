# Assembler Test Cases

Manual test scenarios for `taskos-preso-assembler`. Fixtures live in `tests/fixtures/`.

## Scenario 1: Happy Path Assembly

**Setup:** All test fixtures present in `tests/fixtures/`.

**Steps:**
1. Run assembler on test fixtures.
2. Verify `assembly/index.html` exists.
3. Verify 5 core slides as horizontal `<section>` elements (direct children of `.slides`).
4. Verify 1 appendix stack with 2 slides after the core flow.
5. Verify deep-dive link from `02-problem` → `02-problem-detail`.
6. Verify back-links in appendix slides point to `#/02-problem`.
7. Verify version B of `03-solution` lives in a vertical stack with visual markers (`version-available-marker` on primary, `version-marker` on version).
8. Verify `notes_summary.collab.md` has aggregated notes grouped by type (navigation, technical).
9. Verify `remaining_questions.collab.md` has the nice-to-have question from `02-problem`.

**Pass criteria:** All verifications succeed.

## Scenario 2: Vite Build Produces Single File

**Steps:**
1. After assembly, run `cd presentation/assembly && npx vite build`.
2. Verify `dist/index.html` exists.
3. Verify no external `<script src>` or `<link href>` in the output.
4. Verify inline SVG from `04-evidence` preserved in the bundle.
5. Check file size is under 10 MB.

**Pass criteria:** Single-file bundle with no external references, under budget.

## Scenario 3: Navigation Integrity

**Steps:**
1. Parse the assembled HTML (`src/index.html`).
2. Verify every `href="#/{id}"` resolves to an existing `id` attribute.
3. Verify no numeric index references (`#/3/2`).
4. Verify no duplicate `id` attributes.
5. Verify appendix stack nesting is correct (one parent `<section>` wrapping nested `<section>` entries).

**Pass criteria:** All links resolve, no duplicates, nesting correct.

## Scenario 7: Error Handling

**Sub-case (a): Missing slide file**
1. Delete `how/03-solution/slide.html`.
2. Run assembler.
3. Verify failure with the documented error format listing found, missing, and expected slide_ids.

**Sub-case (b): Duplicate IDs**
1. Add duplicate `id="02-problem"` to two fixture slide HTMLs.
2. Run assembler.
3. Verify failure with a list of duplicates and source files.

**Sub-case (c): Malformed HTML**
1. Leave an unclosed `<section>` in one fixture.
2. Run assembler.
3. Verify detection at assembly time OR Vite build time (either is acceptable; assembler should surface both).

**Pass criteria:** All three error paths produce clear, actionable failures.
