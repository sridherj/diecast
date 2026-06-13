# sp1_detection_brain — Output

**Status:** completed
**Edited file:** `agents/cast-refine-requirements/cast-refine-requirements.md` (434 → 459 lines; ceiling 650)

## What was done

Landed the detection-layer edits (plan activities 1, 2, 4). All edits integrated into existing
steps — no new top-level sections. The two checkouts (`/data/workspace/diecast` and
`/home/sridherj/workspace/diecast`) are the same directory via symlink, so the single edit covers
both.

### Step 1.3 — stage framework sharpened + scope-mode table added (activities 1 & 4)
- Stage signal table kept **byte-for-byte unchanged**.
- Added a purpose sentence framing the stage table as the **Template-Enforcer guard at the
  authoring layer** (a vague-stage writeup is never forced to full EARS depth; the stage licenses
  which sections may stay thin/low-confidence without padding).
- Added the cross-link: **stage = how mature the input is; scope mode = how ambitious the output
  should be** — both detected in Phase 1, both stated in Step 2.1.
- Added a **second detection table** immediately after the stage table, using the Garry Tan
  vocabulary verbatim (matches `cast-detailed-plan`): **SCOPE REDUCTION / HOLD SCOPE (default) /
  SCOPE EXPANSION**, with signal words and per-mode draft effects. Conflict rule: reduction +
  expansion words both present → confirming the mode becomes one Phase 2 question (high-risk
  unknown tier, counts against the 7-question budget).

### Step 2.1 — scope mode stated in the draft presentation (activity 4)
Added a presentation line: state the detected scope mode + the verbatim signal words that
triggered it (e.g. `Scope mode: SCOPE REDUCTION — "MVP", "just the happy path"`). HOLD SCOPE with
no signals is stated explicitly (`Scope mode: HOLD SCOPE — no scope signals detected`).

### Step 3.1 — scope_mode front-matter field (activity 4)
Added `scope_mode: reduction | hold | expansion` to the output-template front-matter (just below
`status:`), with a comment noting it is set from the Step 1.3 detection. Additive — the checker
does not lint front-matter keys.

### Step 2.4 — zero-silent-failure invariant (activity 2)
Replaced the soft budget-exhaustion note with the **zero-silent-failure invariant**: on ANY exit,
every section still below medium confidence MUST have a matching `[NEEDS CLARIFICATION: …]` entry
in Open Questions (the shape `cast-spec-checker` already lints). "No silent low-confidence
sections" stated explicitly.

## Verification results
- `grep` validation: scope-mode table OK, front-matter field OK, zero-silent-failure phrasing OK,
  stage purpose sentence OK, NEEDS CLARIFICATION ref OK.
- Line count: **459** (< 650). ✅
- `pytest tests/test_b1_domain_search.py` → **8 passed** (no regression). ✅
- `git diff` hunks land only in Steps 1.3, 2.1, 2.4, 3.1. **Step 2.2.1 (Domain Web Search) shows
  no diff.** Stage signal table unchanged. ✅

## Notes for dependent sub-phases
- `bin/generate-skills` was **NOT** run (deferred to sp4, per plan).
- No template/checker/test files were touched (sp2/sp4 own those).
- sp2 should insert the evidence-quoting mandate at Step 1.5 and `## Decisions` at Step 3.1; the
  `scope_mode:` front-matter line is now present directly above the `confidence:` block — insert
  `## Decisions` between `## Out of Scope` and `## Open Questions` as planned.
