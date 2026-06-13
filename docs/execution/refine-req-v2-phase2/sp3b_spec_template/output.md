# sp3b_spec_template — Output

**Status:** completed
**Date:** 2026-06-12

## What was done

Documentation lockstep for Phase 2 classification. Authored the contract spec that Phases
3a (HTML render) and 3b (router) cite, registered it, and added the `## Evidence` stub to
the spec template. No code was changed — the code (sp1–sp2c, already landed) is
authoritative; the spec records what was built.

### Files created / modified
| File | Action |
|------|--------|
| `docs/specs/cast-goal-classification.collab.md` | **Created** — the classification contract spec |
| `docs/specs/_registry.md` | Modified — added the registry row |
| `templates/cast-spec.template.md` | Modified — added `## Evidence` stub + per-family shapes note |

### Spec coverage (`cast-goal-classification.collab.md`)
Documents, matched name-for-name against `cast_server/requirements_render/families.py`:
- The **LOCKED nine-value** `WorkFamily` enum (`new_initiative`, `pilot_poc`, `bug_fix`,
  `data_analysis`, `random_idea`, `testing_qa`, `refactor_migration`, `personal_non_eng`,
  `generic`), with `random_idea` as the default/structural floor and `generic` as
  model-selected-only.
- The `classification.*` front-matter schema **field by field** (`family`, `confidence`,
  `alt_family`, `reasoning`, `uncertainty_factors`, `modifiers`, `confirmed_by`,
  `classified_at`, `taxonomy_version`), persisted via `merge_front_matter()`.
- The **code-side gate** (`GATE_SILENT = 0.9`, `GATE_CONFIRM = 0.5`, `gate()`), the three
  actions (auto/confirm/choose), and the **headless policy** (`confirm`→auto,
  `choose`→`random_idea`/fallback, both append an Open-Questions clarification line;
  classifier-failure fail-soft).
- The **two-level checker** contract (Level 1 generic always; Level 2 via `--family`; no
  flag → unchanged full-spec; mirrored `REQUIRED_SECTIONS_BY_FAMILY` with pin test; D1/D5).
- `FAMILY_RECIPES` / `RECIPE_REALIZATION` block-recipe semantics (recipe blocks = semantic
  doc roles; parser `BlockKind`s = spec-kit grammar; `modulate()` for the D4 modifiers).
- The **add-a-family checklist** — six co-located edits (enum, recipe, profile row, prompt
  line, pill label, fixture) **plus** a `taxonomy_version` bump.
- **Critical disambiguation:** the classifier is `dispatch_mode: subagent` and sits
  **outside** `cast-delegation-contract.collab.md` and `cast-output-json-contract.collab.md`
  — returns bare JSON as final message, writes no `.output.json`. Stated in US7, FR-015, the
  Intent, Out of scope, and Cross-references so nobody "fixes" it to emit an envelope.

## Verification (all green)
- `bin/cast-spec-checker docs/specs/cast-goal-classification.collab.md` → **exit 0** (full-spec
  profile; the spec itself carries no classification front-matter). Two rounds of fixes were
  needed: R5 (FR cross-refs inside table rows re-worded to non-`FR-NNN` prose) and R6
  (the example clarification marker re-worded out of the literal `[NEEDS CLARIFICATION: …]`
  bracket form so it is not treated as an orphan).
- `grep -c 'cast-goal-classification' docs/specs/_registry.md` → **1**.
- `grep -E '^## Evidence' templates/cast-spec.template.md` → present; `^## Decisions`
  (Phase 1b's edit) **retained** — not clobbered.
- Name-match audit: all 9 `WorkFamily` values + every public name (`FAMILY_RECIPES`,
  `RECIPE_REALIZATION`, `REQUIRED_SECTIONS_BY_FAMILY`, `FAMILY_PILL_LABELS`, `GATE_SILENT`,
  `GATE_CONFIRM`, `gate`, `validate_classification`, `merge_front_matter`, `modulate`,
  `taxonomy_version`) appear in the spec with matching spelling.
- `pytest tests/test_spec_checker_family.py tests/test_families.py` → **123 passed** (the
  mirror pin test confirms the checker's `REQUIRED_SECTIONS_BY_FAMILY` still matches
  `families.py`).

## Success criteria — all met
- [x] Spec exists, passes `cast-spec-checker`, matches `families.py` names exactly.
- [x] Spec documents enum+locked set, front-matter schema field-by-field, gate
      thresholds/actions/headless policy, two-level checker, recipe semantics, add-a-family
      checklist.
- [x] Spec states the classifier sits outside the delegation + output-json contracts.
- [x] `_registry.md` row added.
- [x] `templates/cast-spec.template.md` has the `## Evidence` stub + per-family note,
      without clobbering Phase 1b's `## Decisions` edit.

## Notes for dependent sub-phases
- sp3b has no downstream blockers (it is a leaf). Phases 3a/3b should cite
  `docs/specs/cast-goal-classification.collab.md` as the contract source of truth, with
  `families.py` as the authoritative code.
- **Deviation from plan, intentional:** Step 3b.1 says "Delegate `/cast-update-spec` (create
  mode)". That agent is interactive (shows a diff and waits for human approval via
  `AskUserQuestion`) and cannot run under the mandated headless/autonomous mode. The spec was
  therefore authored directly to the same `docs/specs/*.collab.md` shape and gated by
  `bin/cast-spec-checker` (the acceptance gate the plan defines). No approval gate was
  available to honour headlessly; the deterministic checker stands in for it.
