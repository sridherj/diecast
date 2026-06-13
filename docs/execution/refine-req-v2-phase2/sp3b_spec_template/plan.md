# Sub-phase 3b: Spec + Template Lockstep

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase2/_shared_context.md` before starting.
> Source: Work Package F of `docs/plan/2026-06-11-refine-requirements-v2-phase2-classification.md`.

## Objective

Author the spec that becomes the contract Phases 3a/3b cite, and add the `## Evidence` stub to the
spec template. The spec — `docs/specs/cast-goal-classification.collab.md` — documents every
user-facing classification contract (the `WorkFamily` enum, the front-matter schema, the gate
thresholds + actions + headless policy, the two-level checker, `FAMILY_RECIPES`/`RECIPE_REALIZATION`
semantics, and the add-a-family checklist). It must match `families.py` names exactly because the
downstream phases will cite it as the source of truth.

## Dependencies
- **Requires completed:** sp1 (`families.py` — the names the spec documents), and the interfaces of
  sp2a/sp2b/sp2c (classifier I/O, gate actions, two-level checker contract) being settled.
- **Assumed codebase state:** `families.py`, `cast-goal-classifier`, `bin/cast-classify-gate`, and the
  `--family` checker exist with stable interfaces. (sp3b documents them; it does not change them.)
- **Parallel with:** sp3a. **No shared files** — sp3b edits `docs/specs/*` + `templates/cast-spec.template.md`.

## Scope

**In scope:**
- `docs/specs/cast-goal-classification.collab.md` via `/cast-update-spec` (create mode).
- Register it in `docs/specs/_registry.md`.
- Add a `## Evidence` section stub + a short "per-family shapes" note to `templates/cast-spec.template.md`.

**Out of scope (do NOT do these):**
- Changing any code (`families.py`, agents, bins) — this is documentation lockstep. If the spec and
  code disagree, the **code is authoritative** (sp1–sp2c already landed); flag the divergence, don't
  silently "fix" code from the spec.
- The Phase 1b `## Decisions` template edit — a different phase also touches
  `templates/cast-spec.template.md`; coordinate (see Execution Notes), don't duplicate.

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `docs/specs/cast-goal-classification.collab.md` | Create (via `/cast-update-spec`) | Does not exist |
| `docs/specs/_registry.md` | Modify (add row) | Exists |
| `templates/cast-spec.template.md` | Modify (add `## Evidence` stub + note) | Exists |

## Detailed Steps

### Step 3b.1: Author the spec
→ **Delegate:** `/cast-update-spec` (create mode) — author `docs/specs/cast-goal-classification.collab.md`.
Pass it the following contracts to document (all sourced from `_shared_context.md` / `families.py`):
- The `WorkFamily` enum + the **LOCKED** family set (all 9 values).
- The `classification.*` front-matter schema, **field by field** (`family, confidence, alt_family,
  reasoning, uncertainty_factors, modifiers, confirmed_by, classified_at, taxonomy_version`).
- Gate thresholds (`GATE_SILENT = 0.9`, `GATE_CONFIRM = 0.5`) + the three actions (auto/confirm/choose)
  + the headless policy (`confirm`→auto, `choose`→random_idea, both append an Open Questions note).
- The two-level checker contract (Level 1 generic always; Level 2 via `--family`; no flag → full-spec).
- `FAMILY_RECIPES` / `RECIPE_REALIZATION` semantics (recipe blocks = semantic doc roles; BlockKinds =
  spec-kit grammar; the two-layer mapping).
- The **add-a-family checklist**: enum value + recipe + profile row + prompt line + pill label +
  fixture — **and bump `taxonomy_version`**.
- **Critical disambiguation:** state that the classifier's subagent dispatch sits OUTSIDE
  `cast-delegation-contract.collab.md` and `cast-output-json-contract.collab.md` — it returns its JSON
  as subagent final text and writes NO `.output.json` envelope. Say this explicitly so nobody "fixes"
  the classifier to emit an output envelope.

→ **Review the `/cast-update-spec` output:** the spec must match `families.py` names **exactly**
(Phases 3a/3b cite it). Cross-check every enum value, dict name, and field name against `families.py`.

### Step 3b.2: Register the spec
Add a row to `docs/specs/_registry.md` for `cast-goal-classification.collab.md` (follow the existing
row format — scope one-liner + linked files).

### Step 3b.3: Template lockstep
- `templates/cast-spec.template.md`: add the `## Evidence` section stub + a short "per-family shapes"
  note pointing at the new spec.
- **Coordinate with Phase 1b's `## Decisions` template edit:** whichever phase lands second rebases
  over the other's template change — do not clobber the other section.

## Verification

### Automated Tests (permanent)
- `bin/cast-spec-checker docs/specs/cast-goal-classification.collab.md` passes (no `--family` flag →
  full-spec profile; the spec itself carries no classification front-matter).
- Registry test (if one exists) stays green with the new row.

### Validation Scripts (temporary)
```bash
bin/cast-spec-checker docs/specs/cast-goal-classification.collab.md ; echo "exit=$?"     # expect PASS
grep -c 'cast-goal-classification' docs/specs/_registry.md                               # expect ≥1
grep -E '^## Evidence' templates/cast-spec.template.md                                    # expect present
# Name-match audit: every WorkFamily value appears in the spec
python -c "from cast_server.requirements_render.families import WorkFamily; print([f.value for f in WorkFamily])"
grep -oE 'new_initiative|pilot_poc|bug_fix|data_analysis|random_idea|testing_qa|refactor_migration|personal_non_eng|generic' docs/specs/cast-goal-classification.collab.md | sort -u
```

### Manual Checks
- Every `families.py` public name (enum values, `FAMILY_RECIPES`, `RECIPE_REALIZATION`,
  `REQUIRED_SECTIONS_BY_FAMILY`, gate constants) appears in the spec with matching spelling.
- The spec explicitly states the classifier is outside the delegation/output-json contracts.
- The add-a-family checklist is complete (6 items + `taxonomy_version` bump).
- `templates/cast-spec.template.md` retains Phase 1b's `## Decisions` section (if already landed).

### Success Criteria
- [ ] `docs/specs/cast-goal-classification.collab.md` exists, passes `cast-spec-checker`, matches
      `families.py` names exactly.
- [ ] Spec documents: enum + locked set, front-matter schema field-by-field, gate thresholds/actions/
      headless policy, two-level checker, recipe semantics, add-a-family checklist.
- [ ] Spec states the classifier sits outside the delegation + output-json contracts.
- [ ] `_registry.md` row added.
- [ ] `templates/cast-spec.template.md` has the `## Evidence` stub + per-family note, without clobbering
      Phase 1b's `## Decisions` edit.

## Execution Notes
- This sub-phase is **documentation lockstep** — the code (sp1–sp2c) is authoritative. The spec records
  what was built; if you find a mismatch, the spec follows the code (or flag it as a real bug for a
  follow-up), never the reverse.
- Parallel-safe with sp3a: sp3a touches `agents/cast-refine-requirements/*`; sp3b touches `docs/specs/*`
  + `templates/cast-spec.template.md`. The only file with multi-phase contention is the template
  (shared with Phase 1b, NOT with sp3a) — rebase, don't clobber.

**Spec-linked files:** This sub-phase *authors* a spec. Run `/cast-spec-checker` on the result as the
acceptance gate.
