# sp3a — `cast-refine-requirements` Integration — Output

**Status:** ✅ Complete. All Detailed Steps executed, all verification run, every success
criterion met. The classify *door* is open for the only v2 caller.

## What landed

A terse **"Step 0 — Classify"** (~55 lines) now runs **first** in
`agents/cast-refine-requirements/cast-refine-requirements.md`, before any drafting. It only
*orchestrates* the upstream pieces (sp1 `families.py`, sp2a classifier, sp2b gate, sp2c checker)
— no logic is duplicated in the prompt.

| File | Action | Notes |
|------|--------|-------|
| `agents/cast-refine-requirements/cast-refine-requirements.md` | Modified | Added Step 0 (between the HARD-GATE note and Phase 1); 548 → 607 lines (≤ ~650 ceiling) |
| `agents/cast-refine-requirements/config.yaml` | Modified | Added `allowed_delegations: [cast-goal-classifier]` with an explanatory comment |
| `~/.claude/skills/cast-refine-requirements/SKILL.md` | Regenerated | `bin/generate-skills` — Step 0 anchors verified present in the regen |
| `tests/test_sp3a_classify_integration_pins.py` | Created | 39 pins (incl. Phase 1b's existing pins still green) |

### Step 0 behavior (the orchestration contract)
1. **Dispatch** `cast-goal-classifier` via the **Agent tool** (subagent — never HTTP) with goal
   **title + raw writeup**; on a re-run also pass the prior `classification` mapping.
2. **Gate in code:** `echo "$RAW_JSON" | bin/cast-classify-gate` → `{classification, action, options}`.
3. **Obey `action`:** `auto` (≥0.9) silent (`confirmed_by: auto`); `confirm` (≥0.5) one pre-filled
   `AskUserQuestion` pill (`confirmed_by: user`); `choose` (<0.5) top-2 + "just notes" escape hatch
   → `random_idea` (`confirmed_by: user`).
4. **Question-budget ordering:** classification asks FIRST; the 1b scope-mode confirm second; worst
   case two one-click questions; `auto` path asks zero; classification does NOT count against the
   7-question budget.
5. **Headless policy:** `confirm`→accept pill (`auto`); `choose`→`random_idea` (`fallback`); BOTH
   append a `[NEEDS CLARIFICATION: classification unconfirmed — <family>]` Open-Questions line.
6. **Fail-soft:** classifier error/timeout/garbage → gate's coercion lands on `random_idea`,
   `confirmed_by: fallback`, same note. Refinement never dies on classification.
7. **Persist once (D3):** resolved mapping (+ `confirmed_by`, `classified_at`, `taxonomy_version: 1`)
   written via `families.py::merge_front_matter()` — `status:`/`confidence:`/Phase-4 keys survive
   byte-for-byte; never re-classify on later render/route.
8. **Recipe-driven emission:** `FAMILY_RECIPES[family]` + `modulate(modifiers)` → emit ONLY the
   `RECIPE_REALIZATION` sections; `random_idea` → `## Intent` only + a "structure is available when
   you're ready" **offer** line; then `bin/cast-spec-checker --family <family> <doc>`.

A blockquote in the prompt states the recipe **overrides** Step 3.1's fixed template for
non-`new_initiative` families (only `new_initiative` emits full US/FR/SC depth) — preventing the
Template-Enforcer padding the checker's Level-2 `F2` guard errors on.

## Verification (all green)

- **Pin tests:** `tests/test_sp3a_classify_integration_pins.py` + `tests/test_phase1b_prompt_pins.py`
  → **39 passed**. Pins: Step 0 heading, `cast-goal-classifier`, `cast-classify-gate`,
  `merge_front_matter`, `FAMILY_RECIPES`, `--family` — in BOTH the source prompt and the regenerated
  skill; Step-0-before-Phase-1 ordering; line ceiling (607 ≤ 660 guard); `config.yaml`
  `allowed_delegations` includes `cast-goal-classifier`.
- **No regressions:** upstream suites green untouched — `test_classify_gate`,
  `test_goal_classifier_prompt`, `test_spec_checker_family`, `test_families` → **151 passed**.
- **End-to-end on a real bug writeup** (deterministic, exercising the full downstream wiring):
  - classifier JSON `bug_fix`@0.82 → `bin/cast-classify-gate` → `action: confirm` + pre-selected pill.
  - `merge_front_matter()` wrote the `classification:` block AND preserved
    `status:`/`scope_mode:`/`confidence:`/`open_unknowns:`/`questions_asked:` byte-for-byte.
  - Refined doc has `## Intent` + `## Evidence` + `## Open Questions`; **NO**
    `## User Stories` / `## Functional Requirements` / `## Success Criteria`.
  - `bin/cast-spec-checker --family bug_fix <doc>` → **exit 0 (PASS)**.
  - No-reclassify read path: `classification.family: bug_fix` re-readable from a second read.
- **Prompt ceiling:** `wc -l` = **607** ≤ ~650.
- **`bin/generate-skills`** run; Step 0 anchors confirmed in `~/.claude/skills/cast-refine-requirements/SKILL.md`.

## Success criteria — all met
- [x] Step 0 — Classify added, runs first, dispatches `cast-goal-classifier` → `bin/cast-classify-gate`.
- [x] auto/confirm/choose obeyed; headless policy + fail-soft both land on recorded `random_idea` + note.
- [x] Persistence is via `merge_front_matter()` only — `status:`/`confidence:` survive a re-run.
- [x] Recipe-driven emission + `--family` checker; `random_idea` emits Intent-only with an offer line.
- [x] `allowed_delegations: [cast-goal-classifier]` in `config.yaml`.
- [x] Prompt ≤ ~650 lines; `bin/generate-skills` run; E2E on a real bug writeup passes.

## Notes for dependent sub-phases (sp4)
- The classify seam is purely subagent-dispatched and writes **no** `.output.json` envelope —
  deliberately outside `cast-delegation-contract`. Do not "fix" that.
- A **live** `cast-goal-classifier` subagent dispatch was NOT run (subagent-only; not in this
  runner's allowlist). The E2E exercised everything *downstream* of the model deterministically;
  **sp4's corpus eval is the live behavioral gate** for the classifier model itself.
- sp4 should drive a real end-to-end refinement (live classifier + gate + recipe + checker) across
  the corpus, including the `generic`↔`random_idea` confusion-pair check (Decision D2).
