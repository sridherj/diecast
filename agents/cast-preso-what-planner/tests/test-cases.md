# Test Cases — taskos-preso-what-planner

## TC-1: Happy path — 8-slide narrative

**Input:** Narrative with 8 slides (hook / reveal / information alternating).

**Expected output:**
- `_slide_list.md` with 8 rows (one per slide).
- 8 `{slide_id}.stub.md` files, each with L1/L2 hierarchy and content pointers.
- No two stubs share a near-identical top-level outcome.
- Coverage check passes: every slide in narrative has a stub.

**Pass criteria:**
- `_slide_list.md` manifest table is well-formed Markdown.
- Every stub has exactly one top-level outcome sentence.
- Every stub has ≥2 L1 items and ≤5 L1 items.

## TC-2: Happy path — narrative with appendix

**Input:** 10 core slides + 5 appendix slides (annotated as such in the narrative).

**Expected output:**
- `_slide_list.md` has both Core and Appendix tables.
- 15 stubs total (one per slide, core + appendix).
- Appendix rows include `Linked From` column showing which core slide they deep-dive into.

**Pass criteria:** Appendix table rows are distinct from core table rows; Linked From
column is populated.

## TC-3: Malformed narrative — missing type annotations

**Input:** Narrative with slide list but no `Slide Type` column in the flow table.

**Expected output:**
- Agent FAILs with error: `"Narrative flow table missing slide type annotations — return to Stage 1."`
- Output contract status = `"failed"`, no partial stubs written.

**Pass criteria:** No `.stub.md` files created. `_slide_list.md` not written.

## TC-4: Missing narrative

**Input:** `presentation/narrative.collab.md` does not exist.

**Expected output:**
- Agent FAILs with error:
  `"Cannot find presentation/narrative.collab.md — Stage 1 must complete first."`
- Output contract status = `"failed"`.

**Pass criteria:** No files written to `presentation/what/`.

## TC-5: Rework — update manifest

**Input:** Existing `_slide_list.md` with 8 slides. Delegation context:
`{"mode": "rework", "feedback": {"manifest": "Add slide 09-close between 08 and the appendix"}}`.

**Expected output:**
- `_slide_list.md` updated: 9 rows, with 09-close inserted in the correct position.
- New stub written for 09-close; existing stubs untouched.

**Pass criteria:** Manifest reflects feedback. Untargeted stubs not rewritten (compare
mtimes).

## TC-6: Rework — fix specific stub

**Input:** Delegation context: `{"mode": "rework", "feedback": {"stub_02-pain":
{"failing_checks": ["outcome_uniqueness"], "feedback_detail": "Too similar to 01-opening"}}}`.

**Expected output:**
- Only `02-pain.stub.md` rewritten. Other stubs and `_slide_list.md` untouched.
- New top-level outcome is materially different from `01-opening.stub.md`'s.

**Pass criteria:** mtimes of other files unchanged. New outcome passes uniqueness check.
