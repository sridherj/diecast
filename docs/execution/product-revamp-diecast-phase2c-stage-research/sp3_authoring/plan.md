# Sub-phase 2c.3 (authoring): Canonical Stage-Model Note, Encoding Contract & Self-Evaluation Gate

> **Pre-requisite:** Read `docs/execution/product-revamp-diecast-phase2c-stage-research/_shared_context.md`
> before starting. It carries the FULL-AUTONOMY directive, the `stageModels` field contract, the
> `appState.spines` v1 contract, the `file://` plain-JSON constraint, the five-test rubric, and
> Reconciliation **F1** (which is why authoring and encoding are split into sp3 and sp4).

## Objective

Produce the **single canonical stage-model note** at
`docs/plan/product-revamp-diecast-stage-models.md` from sp2's derivation: four spines with
per-step surface mappings + references, a **paste-ready `stageModels` JSON block** (plain-JSON, the
shape 2a's generator drops in), the dropped-placeholder ledger, and a **written self-evaluation**
that replaces the owner sign-off gate. Then **append the Phase 2c section** to
`docs/plan/product-revamp-diecast-decisions-so-far.md` so 2a/2b/3 adopt the vocabulary without
re-reading the full note. **This sub-phase has NO dependency on Phase 2a** — it is pure document
authoring. The org.js encode step is sp4.

## Dependencies

- **Requires completed:** **sp2** (the derivation at `sp2_spine_derivation/spine-derivation.md`)
  and, transitively, **sp1** (the evidence base — cited in the references table).
- **No Phase 2a dependency.** Runs as soon as sp2 is done. Does **not** wait for
  `generate-org.mjs` or `org.js`.
- **Assumed state:** `docs/plan/product-revamp-diecast-stage-models.md` does **not** exist yet;
  `docs/plan/product-revamp-diecast-decisions-so-far.md` exists (has Phase 1/2a/2b/2c sections).

## Scope

**In scope:**
- Authoring `docs/plan/product-revamp-diecast-stage-models.md` with all seven sections (below).
- Writing the paste-ready `stageModels` JSON encoding block (plain JSON — sp4 pastes it into the
  generator).
- Writing the self-evaluation gate (rubric table from sp2 + per-family verdict paragraph).
- Writing the hand-off notes (to sp4/2a, 2b, Phase 3) — including the F1-corrected ownership.
- Appending ~10–20 lines to `decisions-so-far.md` (Phase 2c spine-labels + field contract + flags).

**Out of scope (do NOT do these):**
- **Editing `prototype/data/_build/generate-org.mjs` or re-emitting `org.js`** — that is **sp4**,
  and it is gated on Phase 2a's generator existing. Do not touch `prototype/` here.
- **Re-deriving vocabulary** — consume sp2's derivation as-is; do not re-open the rubric (unless
  the self-eval verdict triggers the loop-once rework, see Step 3.4).
- **`/cast-update-spec`** — FR-020 greenfield, no spec applies.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `docs/plan/product-revamp-diecast-stage-models.md` | Create | Does not exist |
| `docs/plan/product-revamp-diecast-decisions-so-far.md` | Modify (append) | Exists; has a Phase 2c planning section — append the *execution-output* spine labels + contract |

## Detailed Steps

### Step 3.1: Write the note with this exact section structure
1. **TL;DR** — the four spines at a glance (one compact table: family · shape · progression ·
   step count · the step shortLabels in order).
2. **Per family** (×4): the spine table (`id · label (+shortLabel) · does · surface · surfaceWhy ·
   artifacts · refs · evidence`), the loop/progress semantics (incl. `loop.over`/`timebox.budget`
   where relevant), the E1–E5 evidence home step, and the surface mappings with rationale + refs.
3. **Dropped-placeholder ledger** — verbatim from sp2 (every illustrative + stub step, what
   replaced it, why).
4. **References table** — stable key → full citation, drawn from sp1's evidence base. Every `refs`
   key used in the spines must resolve here.
5. **`stageModels` encoding block** — see Step 3.2.
6. **Self-evaluation** — see Step 3.3.
7. **Hand-off notes** — see Step 3.5.

### Step 3.2: Author the `stageModels` encoding block (plain JSON — the 2a coordination point)
Render the full block in the shape fixed by `_shared_context.md`'s field contract. Every step
carries: `id`, `label` (+ `shortLabel` if `label` > 18 chars), `does`, `surface` (from the
working set), `surfaceWhy`, `artifacts` (≥1), `refs` (≥2 keys into the references table),
`evidence` (`'E1'..'E5'` for exactly one step per family, else `null`). Family-level: `shape`,
`progression?`, `loop?{over,budget}`, `timebox?{budget}`. **Plain-JSON only** — no functions, no
comments inside the value, no computed expressions. Present it as a fenced block sp4 can copy.

Also state the `appState.spines` derivation rule verbatim (render-layer, not duplicated):
```js
// appState.spines.<family> (Phase 1 contract, unrenamed):
//   { placeholder: false, shape: stageModels.<f>.shape,
//     steps: stageModels.<f>.steps.map(s => s.shortLabel ?? s.label), current, iter? }
```

### Step 3.3: Write the self-evaluation gate (replaces the human sign-off)
Render the full five-mark rubric table from sp2 (every step of all four spines), then a
**per-family verdict paragraph** answering *"would a top practitioner in this category recognize
this as their actual workflow?"* — naming the **strongest supporting reference** and the
**weakest step, honestly**. End each family with an explicit **PASS / FAIL** verdict.

### Step 3.4: Self-eval gate outcome (loop-once on failure — full autonomy)
- **All four families PASS** → proceed to Step 3.5. (The parent orchestrator accepts on all-pass;
  no human sign-off under full autonomy.)
- **Any family FAILs** → loop **once** back through sp2's derivation **for that family only**
  (re-run Steps 2.1–2.6 of sp2 scoped to the failing family), then re-author its section here and
  re-evaluate. Document the loop inline. Do not loop a second time — if it still fails, record the
  honest residual weakness in the verdict and proceed (full autonomy: no blocking gate).

### Step 3.5: Write the hand-off notes (carry the F1-corrected ownership verbatim)
- **2c (sp4 — runs after 2a.1's generator exists):** edit the generator's stage-model section in
  `prototype/data/_build/generate-org.mjs` with the derived vocabulary and re-emit `org.js` per
  2a's "2c: rewrite ONLY `stageModels`" instructions; this flips `placeholder` to `false` and
  re-runs the invariant gate. If 2a has not landed the generator when sp3 completes, sp4 **parks**
  until 2a.1 and **must complete before Phase 3 dispatch**. `appState.spines` derivation stays in
  the render layer.
- **2b:** confirm the four spine variants against the derived shapes (plus any new-surface /
  spine-variant flags).
- **Phase 3:** remove the PLACEHOLDER watermark when rendering from `stageModels`.

### Step 3.6: Append the Phase 2c execution output to `decisions-so-far.md`
Append ~10–20 lines (under the existing Phase 2c section, or a clearly marked "Phase 2c —
Execution Output" subsection): the four spines' step-label lists (in order), the `stageModels`
field contract recap, the E1–E5 home steps, and any flags — so 2a/2b/3 planning and execution
children adopt them without re-reading the full note. Do not duplicate the full note; this is the
adopt-without-re-reading summary.

## Verification

> **NO TESTS.** Verification is **manual file-inspection** plus a JSON-parse spot-check on the
> encoding block. ~35% of this sub-phase is verification — invest here.

### Validation Scripts (temporary — delete after)
- **JSON-parse the encoding block** (the `file://` plain-JSON guarantee). Extract the
  `stageModels` value and confirm it parses and is function-free:
  ```bash
  # paste the stageModels object value into /tmp/sm.json (must be valid JSON, no JS comments)
  jq -e 'keys == ["data","debug","feature","spike"]' /tmp/sm.json   # all four family keys present
  node -e "const o=require('/tmp/sm.json'); for(const f of ['feature','debug','spike','data']){const s=o[f]; if(!(s.steps.length>=4&&s.steps.length<=7))throw new Error(f+' step count '+s.steps.length);} console.log('ok: 4 families, 4-7 steps each, parses clean');"
  ```
  (If the block is authored with `//` comments for readability, keep a comment-free copy for this
  check — the version sp4 encodes must be comment-free.)

### Manual Checks
- **Note exists** at `docs/plan/product-revamp-diecast-stage-models.md` with **all seven** sections.
- **Every step** has: `id` (`<family>-NN`), `label` (+ `shortLabel` if >18 chars), `does`,
  `surface` (from the working set), `surfaceWhy`, `artifacts` (≥1), `refs` (≥2 keys), `evidence`.
- **E1–E5** each appear as an `evidence` home-step annotation in the right family (feature→E1;
  debug→E2 + E3; spike→E4; data→E5).
- **Self-evaluation table** covers **every step of all four spines** with all five rubric marks
  and ends in an explicit per-family PASS/FAIL verdict.
- **References table** resolves **every** `refs` key used anywhere in the spines.
- **Canonical-key grep:** the note uses `feature|debug|spike|data` as family keys and shows **no
  stray vocabulary drift** (`grep -nE 'bug-fix family|analysis family|family: *analysis'` → empty).
- **decisions-so-far append:** the four spine step-label lists + field contract + flags are present.
- **F1 ownership:** the hand-off note assigns the org.js rewrite to **2c via 2a's generator,
  after 2a.1, before Phase 3** (not "2a pastes it").

### Success Criteria
- [ ] `product-revamp-diecast-stage-models.md` exists with all seven sections.
- [ ] The `stageModels` block **parses as plain JSON** (jq/node), four family keys, 4–7 steps each.
- [ ] Every step has all required fields; refs resolve; E1–E5 each have one home step.
- [ ] Self-eval covers every step (five marks) + per-family PASS/FAIL verdict.
- [ ] Any self-eval FAIL triggered exactly one sp2 rework loop (documented), or all PASS.
- [ ] `decisions-so-far.md` appended with the execution-output summary.
- [ ] Hand-off note carries the F1-corrected ownership.
- [ ] `prototype/` untouched (encode is sp4).

## Execution Notes
- **This sub-phase writes documents only.** It must run even if Phase 2a has not started — that is
  the whole point of the authoring/encode split (Reconciliation F1). Do not block on `org.js`.
- The **encoding block is a contract, not a suggestion** — sp4 pastes its *content* into the
  generator; 2a must not rename its field names (may extend).
- Keep the JSON block **comment-free in at least one copy** so sp4's `JSON.parse` / generator gate
  succeeds; `file://` forbids functions and the generator emits plain frozen data.
- **Drift guard:** this note is the *single* source for stage vocabulary. The decisions-so-far
  append is the enforcement vehicle — Phase 3/4 cite the note, never re-derive.
- **Spec-linked files:** none (FR-020 greenfield). No `/cast-update-spec`.
- **FULL AUTONOMY:** the self-evaluation *is* the gate — never wait for a human sign-off.
