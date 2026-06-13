# Sub-phase 2c.2: Spine Derivation & Practicality Pressure-Test

> **Pre-requisite:** Read `docs/execution/product-revamp-diecast-phase2c-stage-research/_shared_context.md`
> before starting. It carries the FULL-AUTONOMY directive, the five-test rubric, the
> derive-first/anti-anchoring protocol, the renderability bounds (4–7 steps, ≤18-char shortLabel),
> the locked shape variants, the familiar-surface set, and the E1–E5 home-step requirement.

## Objective

Turn sp1's evidence base into **four derived candidate spines** — each **4–7 steps**, every step
scored against the five-test practicality rubric, loop-vs-progress decided per family from
evidence, every step mapped to a familiar-tool surface with a one-line rationale and the
reference(s) it was drawn from. The exploration's dropped placeholders are explicitly
dispositioned in a ledger. This sub-phase produces the *derivation*, not the final note — its
single deliverable is `sp2_spine_derivation/spine-derivation.md`, which sp3 composes into the
canonical note.

## Dependencies

- **Requires completed:** **sp1** (the evidence base at `sp1_evidence_base/evidence-base.md`).
- **Assumed state:** every family has ≥3 cited references with evidenced steps and a
  `practitioner-account`. No prototype code exists or is needed.

## Scope

**In scope:**
- Drafting each family's candidate spine **purely from sp1 evidence** (derive-first).
- Scoring **every** candidate step against all five rubric tests; renaming/dropping failures.
- Deciding loop-vs-progress per family from evidence; recording `loop.over` for the looped family.
- Mapping each step to a familiar-tool surface with rationale + refs.
- Enforcing renderability bounds (4–7 steps; ≤18-char labels w/ `shortLabel`; ≥1 artifact/step;
  E1–E5 each get a home step).
- Checking each derived spine against its locked shape variant; **flagging** (not redesigning)
  any genuine contradiction.
- Writing the **dropped-placeholder ledger** (what replaced each illustrative step, and why) —
  the audited proof that derivation preceded comparison.

**Out of scope (do NOT do these):**
- **Writing `docs/plan/product-revamp-diecast-stage-models.md`** or the paste-ready JSON block —
  that is sp3.
- **Appending to decisions-so-far.md** — that is sp3.
- **Touching `prototype/`** — no code in this phase.
- **Redesigning a locked 2b shape variant** — flag it, proceed with best fit.
- **Forcing the four spines symmetric** — asymmetry is SC-005 working.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `docs/execution/product-revamp-diecast-phase2c-stage-research/sp2_spine_derivation/spine-derivation.md` | Create | Does not exist |

## Detailed Steps

### Step 2.1: Derive first (the anti-anchoring protocol — order is mandatory)
Draft each family's candidate spine **purely from the sp1 evidence**, with **zero** reference to
the dropped placeholders or Phase 1's watermarked stubs. Write the draft spines into
`spine-derivation.md` first.

### Step 2.2: Compare after, and build the dropped-placeholder ledger
**Only now** diff each draft spine against (a) the dropped exploration placeholders
(feature: prototype-with-UI-choices → locked design → eng design; debug: repro · RCA · evidence ·
fix · tests) and (b) Phase 1's watermarked stub labels. Record the diff in a **dropped-placeholder
ledger**: every illustrative/placeholder step listed, what replaced it (or that it survived under
a new name), and why. The ledger covering *every* placeholder is the proof the protocol held.

### Step 2.3: Score every candidate step against the five-test rubric (all five must pass)
For each step record explicit pass/fail on:
1. **Verb+artifact** — names a practitioner *action* yielding a tangible artifact.
2. **Recognition** — appears (any name) in **≥2 independent sp1 sources**; **cite both** keys.
3. **Hole** — its absence would be noticed by a top practitioner.
4. **Tidy-label kill** — if it only lives in textbooks/consulting frameworks and never in
   practitioner accounts, **kill or rename**.
5. **Familiar-surface** — maps to `doc · board · PR-thread/report · investigation ledger ·
   notebook+chart · memo+timebox`, or raises an explicit new-surface flag.

A step that fails any test is **renamed or dropped with a note** — never silently kept.

### Step 2.4: Decide loop vs progress per family (from evidence, not symmetry)
State, per family, whether it is a loop or a linear/progress spine, **with its evidence**. For the
looped family, record **which steps the loop iterates over** (becomes `loop.over`) and the budget
(becomes `loop.budget` / `timebox.budget`). Do not force the expected answer — the research decides.

### Step 2.5: Enforce renderability bounds
- **4–7 steps** per family.
- Each label **≤ ~18 chars**, or carry a **`shortLabel` ≤18 chars** alongside the honest full
  `label`.
- Each step **owns ≥1 concrete artifact** (canvas anatomy).
- **E1–E5 each get a named home step** in their family (feature→E1; debug→E2 *and* E3; spike→E4;
  data→E5). Note which step id hosts each.

### Step 2.6: Shape-compatibility check (flag, don't redesign)
Confirm each derived spine still fits its locked variant (`segments` / `loop` band / `timebox`
meter / `pipeline` DAG). If research genuinely contradicts a shape, **do not redesign** — write a
"spine-variant revision proposed" flag (for sp3 to carry into the note's Suggested Revisions
channel) and proceed with the best fit.

### Step 2.7: Write `spine-derivation.md`
Per family: a candidate-spine table (`step id · label (+shortLabel) · what the practitioner
actually does · owned artifact(s) · surface + one-line rationale · refs`), the rubric scorecard
(five marks/step), the loop/progress call + evidence, and the E1–E5 home-step mapping. Plus the
single cross-family **dropped-placeholder ledger** and any **shape-variant flags**.

## Verification

> **NO TESTS.** Verification is **manual file-inspection** of `spine-derivation.md`.

### Manual Checks
- **Step ids & keys:** every step id matches `<family>-NN` (`feat-01`, `dbg-01`, `spk-01`,
  `data-01`); family keys are exactly `feature|debug|spike|data` (grep for stray `analysis` /
  `bug-fix` — must be absent as keys).
- **Bounds:** each family has **4–7** steps; every label is ≤18 chars **or** carries a ≤18-char
  `shortLabel`; every step lists **≥1 artifact**.
- **Rubric coverage:** every step has **all five** rubric marks; every surviving step passes all
  five (or there is a rename/drop note for any that didn't).
- **Recognition citations:** every step's Recognition mark cites **≥2** distinct sp1 reference
  keys that actually exist in `evidence-base.md`.
- **E1–E5:** each of E1, E2, E3, E4, E5 has exactly one named home step in the right family.
- **Loop/progress:** stated per family with evidence; the looped family names its `loop.over`
  step ids and budget.
- **Ledger:** the dropped-placeholder ledger covers **every** illustrative step from the
  exploration (feature 3 + debug 5) and Phase 1's stub labels — proving derive-first ordering.
- **Surfaces:** every step's `surface` is from the locked working set, or carries an explicit
  new-surface flag.

### Success Criteria
- [ ] Four candidate-spine tables exist, each 4–7 steps, ids `<family>-NN`.
- [ ] Every step passes all five rubric tests (or was renamed/dropped with a note).
- [ ] Every Recognition mark cites ≥2 real sp1 sources.
- [ ] E1–E5 each have one named home step in the correct family.
- [ ] Loop-vs-progress decided per family from evidence; `loop.over` recorded for the looped one.
- [ ] Dropped-placeholder ledger covers every illustrative + stub step.
- [ ] Shape-compatibility checked; any contradiction is a flag, not a redesign.
- [ ] No canonical note, no JSON block, no decisions-so-far append (that is sp3).

## Execution Notes
- **Anchoring bias is the top failure mode of this sub-phase.** The mitigation is the *order* in
  Steps 2.1→2.2: derive into the file first, compare second. A reviewer verifies the ledger shows
  this ordering.
- **Asymmetry is a feature.** Different step counts and loop shapes across families = SC-005
  contrast working. Reject any urge to make the four spines symmetric.
- **Naming convention:** step ids `<family>-NN`; labels Title Case.
- **Spec-linked files:** none (FR-020 greenfield).
- **FULL AUTONOMY:** never pause for input; resolve every judgment call and document it inline.
