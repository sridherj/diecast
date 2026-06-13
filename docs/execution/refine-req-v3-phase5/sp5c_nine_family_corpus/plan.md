# Sub-phase 5c: Nine-Family Corpus & Golden Renders (parallel with 5a/5b)

> **Pre-requisite:** Read `docs/execution/refine-req-v3-phase5/_shared_context.md` before starting —
> especially the **Structural-Violation OVERRIDE** (it shapes the terminal-state assertions below) and
> the manifest's `cast-requirements-what` additive-prompt seam note (5c ∥ 5a).

## Objective

Author a representative, **authored-not-fiction** requirements document for every one of the nine
**LOCKED** `WorkFamily` values; render each end-to-end through the full pipeline (WHAT → gates → HOW →
4a quality loop); prove the nine pages are deterministically distinct (pairwise-different
section-heading sets, no US/FR/SC slot headings, no padded empty blocks); read per-family quality from
the `human_review` flag (4a's hand-off); and fix any family that renders broken or padded **at the
WHAT-prompt / recipe-vocabulary level only**. SC-002's evidence is captured **provisionally** here and
**finalized in 5d** (re-run after gap machinery lands).

## Dependencies

- **Requires completed:** Phases 3 + 4a (the full pipeline + quality loop + `human_review` flag).
- **Independent of 5a/5b:** with gap machinery dormant (`gaps[]` empty), the pipeline is exactly
  Phase 3/4a behavior, so 5c runs **fully parallel** to the 5a → 5b chain.
- **Assumed codebase state:** `families.py` carries `FAMILY_RECIPES` (the 6-block recipe vocabulary)
  and the nine-value `WorkFamily` enum (LOCKED, `taxonomy_version: 1`); the `eval_` harness pattern
  exists (3e/4a); `bin/cast-spec-checker`-adjacent shape checks for classification front matter.
- **Shared file with 5a:** `agents/cast-requirements-what/*` — 5c tunes the **per-family
  communication-section vocabulary** block; 5a adds the **gaps-schema + gap-detection** block.
  Disjoint additive concerns; whichever lands second does a mechanical merge of the two blocks (no
  logical collision). See the manifest seam note.

## Scope

**In scope:**
- Nine authored-not-fiction corpus docs at
  `cast-server/tests/fixtures/family_corpus/{family}/refined_requirements.collab.md`, each with pinned
  classification front matter + a one-line provenance header.
- `eval_family_sweep.py` (`eval_`-prefixed real-pipeline harness) running all nine and asserting the
  distinctness + terminal-state + per-family quality criteria.
- The bounded fix loop at **prompt/recipe-wording level only** (`cast-requirements-what` per-family
  guidance + `FAMILY_RECIPES` wording in `families.py`), with a before/after note per fixed family.
- Golden renders + verdicts copied to `docs/goal/.../signoff/golden/{family}.html` (+ a one-page index).

**Out of scope (do NOT do these):**
- Do NOT add or rename a `WorkFamily` value (enum LOCKED); do NOT redesign the 6-block recipe *shape*
  (tuning its *wording* is in scope, not its structure).
- Do NOT build a test-only render path — the sweep exercises production code paths via the eval harness.
- Do NOT touch the classifier (`cast-goal-classification.collab.md` scope — consumed, not tested; the
  pinned front matter means the sweep never depends on classifier agreement).
- Do NOT pad a thin family's render — padding fixes flow through US2 Scenario 2 (omit, never pad).
- Do NOT suppress a `human_review` flag — a family that converges only with a flag is a **finding**.
- Do NOT touch gap machinery (5a/5b) — `gaps[]` stays empty for the 5c sweep; SC-002 re-runs in 5d
  with gap machinery live.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/fixtures/family_corpus/new_initiative/refined_requirements.collab.md` | Create | (use this goal's own real `refined_requirements.collab.md`) |
| `cast-server/tests/fixtures/family_corpus/bug_fix/refined_requirements.collab.md` | Create | (the Phase-1a authored `goal_card.py` markdown-leak doc, `spikes/1a/`) |
| `cast-server/tests/fixtures/family_corpus/data_analysis/refined_requirements.collab.md` | Create | (Phase-1a stretch doc, else author from the dispatcher slot-saturation analysis) |
| `cast-server/tests/fixtures/family_corpus/refactor_migration/refined_requirements.collab.md` | Create | (author from the per-goal `.cast` namespacing change, commit `b2e9661`) |
| `cast-server/tests/fixtures/family_corpus/testing_qa/refined_requirements.collab.md` | Create | (author from the real UI-test sweep / runner-dispatch hardening work) |
| `cast-server/tests/fixtures/family_corpus/pilot_poc/refined_requirements.collab.md` | Create | (author from the Phase-1 maker spike itself) |
| `cast-server/tests/fixtures/family_corpus/random_idea/refined_requirements.collab.md` | Create | (author from a real captured one-paragraph idea — the structural floor, honest about thinness) |
| `cast-server/tests/fixtures/family_corpus/personal_non_eng/refined_requirements.collab.md` | Create | (author from a real personal/non-engineering owner task) |
| `cast-server/tests/fixtures/family_corpus/generic/refined_requirements.collab.md` | Create | (a deliberately family-ambiguous doc — the unmatched-fallback path) |
| `cast-server/tests/eval_family_sweep.py` | Create | Does not exist |
| `agents/cast-requirements-what/cast-requirements-what.md` | Modify (append vocab block) | Per-family communication-section guidance (additive, disjoint from 5a's gaps block) |
| `cast-server/cast_server/.../families.py` | Modify | `FAMILY_RECIPES` recipe *wording* tuning (enum/shape LOCKED) |
| `docs/goal/refine-requirements-better-rendering-v3/signoff/golden/{family}.html` (+ `index.html`) | Create | SC-002 evidence trail |

> Confirm the `families.py` path + the `WorkFamily` enum + `FAMILY_RECIPES` keys:
> `grep -rn "FAMILY_RECIPES\|class WorkFamily\|taxonomy_version" cast-server/cast_server/`.
> Confirm the eval-harness pattern: `ls cast-server/tests/eval_*.py`.

## Detailed Steps

### Step 5c.1: Author the nine corpus docs (authored, not fiction)

Each doc is derived from **named real work** (the provenance table above), with a one-comment
provenance header naming what real work it was authored from, and **pinned classification front
matter**: `family: <value>`, `confirmed_by: "manual"`, `taxonomy_version: 1`. Non-stub content. The
`random_idea` doc is deliberately thin (one-paragraph source is fine) — it IS the structural floor;
its render must be **honest about thinness, not padded**. The `generic` doc is deliberately
family-ambiguous to exercise the model-selected unmatched-fallback path.

### Step 5c.2: `eval_family_sweep.py` (the real-pipeline harness)

Extend the 3e/4a `eval_` pattern. Run all nine corpus docs through the **full** pipeline and assert:
- pipeline terminal state ∈ {`published`, `published`+`human_review`} — **never** the deterministic
  fallback, **never** `failed`. (Under the structural override the fallback is reserved for literal
  no-output; a family reaching it in the sweep is a hard finding — the happy path must work for every
  family.)
- pairwise **section-heading sets differ** (deterministic distinctness);
- **no heading equals a US/FR/SC slot name**;
- **no empty section shells** (US2 Scenario 2 — omit, never pad);
- `check_html` green per family;
- per-family checker verdict + score recorded;
- per-family `human_review` flag read + recorded (the 4a hand-off — the per-family quality signal).

Corpus docs also pass `bin/cast-spec-checker`-adjacent shape checks (valid pinned classification front
matter, non-stub content).

### Step 5c.3: Run the sweep; fix the broken-or-padded (vocabulary/prompt level ONLY)

The fix loop operates ONLY at the vocabulary/prompt level: per-family guidance in the
`cast-requirements-what` prompt (the additive vocabulary block — disjoint from 5a's gaps block) and
`FAMILY_RECIPES` recipe *wording* in `families.py` (starting vocabulary — tuning its wording is in
scope; the nine-value enum + the 6-block recipe shape are LOCKED). Record a **before/after note per
fixed family**. Padding fixes flow through US2 Scenario 2 (omit, never pad).

> **Carry-forward (from decisions-so-far Phase-3 follow-up):** the `cast-requirements-how` prompt's
> reproducible lead-unit paraphrase (FR-001/SC-001-class) surfaces as `.comment-unplaced` misses and
> recurs across families. If a family's render shows this, the **HOW-prompt verbatim-carriage
> hardening** is the fix lever — note it; it may already be hardened (Phase 4b carriage work). Do NOT
> redesign the recipe to work around it.

### Step 5c.4: Capture golden renders + verdicts

Copy each family's rendered HTML + verdict to `docs/goal/.../signoff/golden/{family}.html` (+ a
one-page index). This is the SC-002 evidence trail. Fixtures live in `tests/fixtures/family_corpus/`
(importable by the 5b gap-injection test + the eval harness); only the **rendered evidence** is copied
to the goal's `signoff/` dir (keeps `goals/{slug}/` runtime dirs + the FR-026 invariant untouched).

### Step 5c.5: Read `human_review` as the per-family quality signal

A family that converges only with a flag is a **finding** — fix its vocabulary, or carry the flag into
5d's sign-off as an honest open item. **Never suppress the flag.**

## Verification

### Automated Tests (eval harness — NOT default CI)
- `eval_family_sweep.py` green on all nine: terminal state ∈ {published, published+human_review};
  pairwise heading-set distinctness; no US/FR/SC slot headings; no empty shells; `check_html` green
  per family; per-family verdict + score + `human_review` recorded.
- Corpus docs pass the classification-front-matter shape checks (`family` pinned,
  `confirmed_by: "manual"`, `taxonomy_version: 1`, non-stub).

### Validation Scripts (temporary)
- One-off: print the nine section-heading sets side by side to eyeball-confirm distinctness before
  committing the golden renders. Discardable.

### Manual Checks
- `grep -rn "family:\|confirmed_by:\|taxonomy_version:" cast-server/tests/fixtures/family_corpus/` →
  all nine have pinned front matter.
- Confirm the `WorkFamily` enum + recipe **shape** are unchanged (`git diff cast-server/cast_server/.../families.py`
  touches only recipe *wording*, not the enum or block count).
- Confirm each fixture has a one-line provenance header naming its real-work source.

### Static / carry-forward (no browser in autonomous runs)
- The side-by-side **human-eyeball** browser pass over the nine golden renders is recorded as a
  **static verdict + human-eyeball carry-forward** (autonomous runs cannot drive a browser; static
  verdicts never block). Carried into 5d's sign-off.

### Success Criteria
- [ ] Nine corpus docs exist, each authored from named real work with a provenance header + pinned
      classification front matter (`taxonomy_version: 1`).
- [ ] `eval_family_sweep.py` green: every family reaches published (± `human_review`), never fallback,
      never failed.
- [ ] Pairwise section-heading sets differ; no US/FR/SC slot headings; no empty shells.
- [ ] Per-family checker verdict + score + `human_review` flag recorded.
- [ ] Any broken/padded family fixed at prompt/recipe-**wording** level only (enum/shape LOCKED), with
      a before/after note.
- [ ] Golden renders + index copied to `signoff/golden/`.
- [ ] No `human_review` flag suppressed; any flagged family carried into 5d's sign-off.

## Execution Notes

- **Authored-not-fiction is the integrity bar.** Every corpus doc must trace to named real work, or
  SC-002's evidence is hollow. The provenance header makes a future reader trust the fixtures are
  representative, not synthetic noise.
- **`gaps[]` stays empty for the 5c sweep.** 5c is the Phase-3/4a behavior baseline; SC-002's FINAL
  evidence is re-run in 5d after gap machinery lands, so the sign-off reflects the shipped pipeline.
- **The flag is a signal, not a failure to hide.** Reading `human_review` per family is the whole
  point of the 4a hand-off — surface it, fix the vocabulary, or carry it forward; never paper over it.
- **Coordinate the `cast-requirements-what` prompt with 5a.** Your vocabulary block and 5a's gaps
  block are disjoint and additive; if you land second, mechanically merge the two blocks (no overlap).
- **Spec-linked files:** the nine-family verification realizes SC-002 (the render spec). **Flag for
  5d's `/cast-update-spec` pass — do not edit the spec here.** SC-002's evidence procedure (corpus +
  `eval_family_sweep.py` + `human_review` signal) is recorded by 5d.
