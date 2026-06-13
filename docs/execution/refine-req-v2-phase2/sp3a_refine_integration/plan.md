# Sub-phase 3a: `cast-refine-requirements` Integration (the only v2 caller)

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase2/_shared_context.md` before starting.
> Source: Work Package E of `docs/plan/2026-06-11-refine-requirements-v2-phase2-classification.md`.

## Objective

Wire classification into `cast-refine-requirements` — the only v2 caller of the classify seam. Add a
"Step 0 — Classify" that runs FIRST (before any drafting): dispatch `cast-goal-classifier`, pipe its
JSON through `bin/cast-classify-gate`, obey the gate `action` (auto/confirm/choose), persist the
`classification` mapping ONCE via `merge_front_matter()`, and emit ONLY the family's recipe sections
(checked with `--family`). This is where the door opens for real users — and where the prompt-budget
and question-budget contracts with Phase 1b must be honored.

## Dependencies
- **Requires completed:** sp2a (`cast-goal-classifier` agent), sp2b (`bin/cast-classify-gate`),
  sp2c (two-level checker `--family` flag). Transitively sp1 (`families.py` functions).
- **Assumed codebase state:** the classifier agent dispatches via the Agent tool; the gate bin reads
  stdin → emits `{classification, action, options}`; the checker accepts `--family <value>`;
  `merge_front_matter()` exists in `families.py`.
- **Parallel with:** sp3b. **No shared files** — sp3a edits `agents/cast-refine-requirements/*`;
  sp3b edits `docs/specs/*` + `templates/cast-spec.template.md`.

## Scope

**In scope:**
- Add "Step 0 — Classify" (~60 lines) to `agents/cast-refine-requirements/cast-refine-requirements.md`.
- The auto/confirm/choose handling, the headless policy, the classifier-failure fail-soft.
- Persist via `merge_front_matter()`; recipe-driven emission; checker run with `--family`.
- `config.yaml`: add `allowed_delegations: [cast-goal-classifier]`.
- Re-run `bin/generate-skills`; verify the ~650-line prompt ceiling holds.

**Out of scope (do NOT do these):**
- Editing `families.py`, the classifier agent, the gate bin, or the checker — they are upstream and
  frozen. This sub-phase only *invokes* them.
- The Phase 1b prompt edits (dated `## Decisions`, evidence-quoting, scope-mode) — a different phase
  sharing this file. **Do not undo or duplicate** 1b's edits; coordinate the question-budget ordering.
- Phase 3a render / Phase 3b routing — they *read* the front-matter this sub-phase writes.

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `agents/cast-refine-requirements/cast-refine-requirements.md` | Modify | Exists; ~650-line ceiling shared with Phase 1b |
| `agents/cast-refine-requirements/config.yaml` | Modify | Exists; `model: opus, interactive: true`; no `allowed_delegations` |
| (generated) `cast-refine-requirements` skill | Regenerate via `bin/generate-skills` | Exists |

## Detailed Steps

### Step 3a.1: "Step 0 — Classify" (runs FIRST, before drafting)
Dispatch `cast-goal-classifier` via the Agent tool (subagent mode) with the goal **title + raw
writeup** → pipe the returned JSON through `bin/cast-classify-gate` → obey `action`:
- `auto` → record silently (`confirmed_by: auto`).
- `confirm` → ONE `AskUserQuestion` (per `/cast-interactive-questions`): pre-filled pill, one-click
  accept, with override options (`confirmed_by: user`).
- `choose` → forced top-2 (`family`, `alt_family`) + the "just notes / not sure yet" escape hatch
  (→ `random_idea`) (`confirmed_by: user`).

→ **Delegate (for the question UX):** `/cast-interactive-questions` conventions — pre-filled
recommendation first, one-click accept.

### Step 3a.2: Question-budget ordering (cross-phase contract with Phase 1b)
Classification asks **FIRST** (it shapes everything downstream); the 1b scope-mode confirm second.
Worst case: two one-click questions per refinement. `auto` (≥0.9) asks nothing — the common path
stays zero-question. Verify Phase 1b's scope-mode question is sequenced after Step 0.

### Step 3a.3: Headless / non-interactive policy (mirrors 1b's auto-persist override)
- `confirm` → accept the pill, `confirmed_by: auto`.
- `choose` → `random_idea` (the loose default), `confirmed_by: fallback`.
- **BOTH** append a line to the doc's Open Questions noting the unconfirmed classification.
- Never block, never guess silently.

### Step 3a.4: Classifier-failure fail-soft
Subagent error / timeout / garbage → `validate_classification` coercion path → `random_idea`,
`confirmed_by: fallback`, Open Questions note. Refinement NEVER dies on classification.

### Step 3a.5: Persist ONCE, consume twice
Write the `classification:` mapping into front-matter via `merge_front_matter()` (Decision D3) — NOT
by hand-editing YAML in the prompt — so `status:`, the existing `confidence:` map, and Phase 4
versioning keys survive byte-for-byte. The refine agent NEVER re-classifies on render/routing.
Re-classification happens only on an explicit re-run (prior mapping passed to the classifier; a
changed family is surfaced to the user).

### Step 3a.6: Recipe-driven emission
Select `FAMILY_RECIPES[family]`, apply `modulate(modifiers)`, emit ONLY the realized sections per
`RECIPE_REALIZATION` (e.g. `random_idea` → Intent only, ending with a "structure is available when
you're ready" offer line — an offer, not empty sections). Run the checker on the output **with
`--family <family>`** so Level 2 applies the right profile; fix errors before persisting.

### Step 3a.7: config + regenerate
- `config.yaml`: add `allowed_delegations: [cast-goal-classifier]` (documents intent; makes a future
  HTTP switch config-only, even though subagent dispatch doesn't consult the allowlist).
- `bin/generate-skills`; verify total prompt length stays **under the ~650-line ceiling**.

## Verification

### Automated Tests (permanent)
- Extend the existing `cast-refine-requirements` prompt-pin test (or add one) asserting Step 0 exists
  and names the classifier + the gate bin + `merge_front_matter`.
- A length guard test: `cast-refine-requirements.md` ≤ ~650 lines (match the existing ceiling-check if
  Phase 1b added one; otherwise add it).
- `config.yaml` parse test: `allowed_delegations` includes `cast-goal-classifier`.

### Validation Scripts (temporary) — End-to-End (the phase-gate E2E)
```bash
# Refine one real bug writeup → assert the doc shape and front-matter:
#   - contains ## Intent + ## Evidence (+ optional ## Open Questions)
#   - classification.family: bug_fix in front-matter
#   - NO ## User Stories / ## Functional Requirements / ## Success Criteria sections
grep -A12 '^classification:' <refined_doc>            # family: bug_fix, confirmed_by, classified_at
grep -E '^## (User Stories|Functional Requirements|Success Criteria)' <refined_doc>   # expect NONE
# Demonstrate the no-reclassify read path from a SECOND shell:
grep -A1 'family:' <refined_doc>
bin/cast-spec-checker --family bug_fix <refined_doc> ; echo "exit=$?"   # expect PASS
wc -l agents/cast-refine-requirements/cast-refine-requirements.md       # ≤ ~650
```

### Manual Checks
- Worst-case question flow is two one-click questions (classification first, scope-mode second);
  `auto` path asks zero.
- A `random_idea` refinement ends with the offer line, **no empty US/FR/SC tables**.
- Headless run records `confirmed_by: auto|fallback` AND appends the Open Questions note.

### Success Criteria
- [ ] Step 0 — Classify added, runs first, dispatches `cast-goal-classifier` → `bin/cast-classify-gate`.
- [ ] auto/confirm/choose obeyed; headless policy + fail-soft both land on recorded `random_idea` + note.
- [ ] Persistence is via `merge_front_matter()` only — `status:`/`confidence:` survive a re-run.
- [ ] Recipe-driven emission + `--family` checker run; `random_idea` emits Intent-only with an offer line.
- [ ] `allowed_delegations: [cast-goal-classifier]` in `config.yaml`.
- [ ] Prompt stays ≤ ~650 lines; `bin/generate-skills` run; E2E on a real bug writeup passes.

## Execution Notes
- **Shared file with Phase 1b** (`cast-refine-requirements.md`): if Phase 1b already landed, rebase
  Step 0 around its edits; if not, leave clean seams. Never duplicate 1b's `## Decisions` / scope-mode
  content — only sequence the question budget.
- Keep Step 0 **terse (~60 lines)**: the gate logic lives in the bin (sp2b), the family logic in
  `families.py` (sp1), the classification in the subagent (sp2a). The prompt only orchestrates.
- Subagent classifier calls are auto-captured as runs (per `cast-subagent-and-skill-capture.collab.md`)
  — free observability; do NOT add duplicate tracking.

**Spec-linked files:** If a spec in `docs/specs/` links `cast-refine-requirements.md`, read it and
verify SAV behaviors are preserved. The new classification contract is specced by sp3b.
