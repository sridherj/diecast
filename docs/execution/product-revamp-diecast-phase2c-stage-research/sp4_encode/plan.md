# Sub-phase 2c.4 (encode): Encode the Derived stageModels into org.js via the Generator

> **Pre-requisite:** Read `docs/execution/product-revamp-diecast-phase2c-stage-research/_shared_context.md`
> before starting. It carries the FULL-AUTONOMY directive, the NO-TESTS rule, the `file://`
> plain-JSON constraint, the `stageModels` field contract, and Reconciliation **F1** — the reason
> this sub-phase exists separately and is gated on Phase 2a.

## ⚠ EXTERNAL GATE — DO NOT START UNTIL BOTH FILES EXIST

This sub-phase **parks** until the Phase 2a (separate parallel orchestrate run) artifacts exist:

```
prototype/data/_build/generate-org.mjs   # the seeded self-validating generator (2a.1)
prototype/data/org.js                     # the emitted, committed window.ORG spine (2a)
```

The orchestrator polls Phase 2a and **releases sp4 only once both exist**. sp4 also requires
**sp3** complete (the canonical note + the paste-ready `stageModels` block). sp4 **must complete
before Phase 3 dispatch** — Phase 3 must never build canvases over PLACEHOLDER vocabulary.

**Park check (run first; if it fails, STOP and report "parked — awaiting 2a generator"):**
```bash
test -f prototype/data/_build/generate-org.mjs && test -f prototype/data/org.js \
  && echo "GATE OPEN — 2a artifacts present, proceed" \
  || echo "PARKED — 2a generator/org.js missing; do not start sp4 yet"
```

## Objective

Encode sp3's derived `stageModels` vocabulary into the real org data: edit **only** the
stage-model section of `prototype/data/_build/generate-org.mjs`, re-emit `prototype/data/org.js`,
flip every family's `placeholder` from `true` to `false`, and re-run the generator's built-in
invariant gate. This is the step that makes Phases 3–4 render real spines instead of watermarked
stubs. It is the **one standing exception** to 2a's post-freeze policy (the `stageModels` region
is 2c-owned).

## Dependencies

- **Requires completed:** **sp3** (the canonical note with the paste-ready `stageModels` block).
- **Requires external (Phase 2a, separate run):** `prototype/data/_build/generate-org.mjs` **and**
  `prototype/data/org.js` must both exist. The orchestrator parks this sub-phase until then.
- **Assumed state:** 2a shipped `stageModels` with `placeholder: true` content and `<family>-NN`
  step ids; the generator is **self-validating** (refuses to emit on any invariant violation) and
  carries a GENERATED header — `org.js` is generated, never hand-edited.

## Scope

**In scope:**
- Replacing the generator's `stageModels` region constants with sp3's derived vocabulary.
- Flipping each family's `placeholder` to `false`.
- Re-running the generator to re-emit `org.js`; letting its invariant gate validate.
- Verifying section-stability (F4): every ORG section **outside** `stageModels` is byte-identical
  before/after.

**Out of scope (do NOT do these):**
- **Hand-editing `org.js` directly** — it is generated; edit the generator and regenerate (F4
  single-source rule). `org.js` carries a GENERATED header.
- **Touching any ORG section other than `stageModels`** — no goals, agents, decisions, board,
  hiring, layer2 edits. This is the 2c-owned region only.
- **Renaming any `stageModels` field** — the contract is fixed; you may only fill in derived
  content. (2a reserved the slot verbatim.)
- **Re-deriving or re-authoring vocabulary** — consume sp3's block as-is.
- **Writing tests** — the generator's in-code invariant gate is the only machine check, and it is
  NOT a test file.
- **Touching `index.html` / `appState`** — the render-layer derivation (`steps.map(...)`) is Phase
  1/3 territory; sp4 only changes the org data.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `prototype/data/_build/generate-org.mjs` | Modify (stage-model section only) | Exists (Phase 2a). Holds placeholder `stageModels` constants. |
| `prototype/data/org.js` | Regenerate (via the generator — never hand-edit) | Exists (Phase 2a). Holds `window.ORG` with placeholder `stageModels`. |

## Detailed Steps

### Step 4.1: Confirm the gate is open
Run the park check (top of this file). If either file is missing → **STOP**, report
`status: parked`, and let the orchestrator re-release sp4 after 2a lands. Do not proceed.

### Step 4.2: Locate the generator's stage-model section
Open `prototype/data/_build/generate-org.mjs`. Find the `stageModels` region — 2a authored it as
named constants with placeholder content and `<family>-NN` step ids, per 2a's "the `stageModels`
region is 2c-owned and will be rewritten once by 2c's derived stage vocabulary" note. Read 2a's
in-file instructions ("2c: rewrite ONLY `stageModels` via `generate-org.mjs`") and follow them
exactly. **Do not** alter generator logic elsewhere, the seed (`42`), or other sections' constants.

### Step 4.3: Replace placeholder content with sp3's derived vocabulary
Paste the derived per-family `steps` arrays and family-level `shape`/`progression`/`loop`/`timebox`
from sp3's `stageModels` block into the generator's stage-model constants. Each step gets `id`,
`label`, `shortLabel?`, `does`, `surface`, `surfaceWhy`, `artifacts[]`, `refs[]`, `evidence`. Set
each family's **`placeholder: false`**. Keep the data **plain-JSON-compatible** (no functions) so
the emitted `org.js` stays a frozen classic-script value loadable from `file://`.

### Step 4.4: Re-emit and let the invariant gate validate
Re-run the generator exactly as 2a documents (e.g. `node prototype/data/_build/generate-org.mjs`).
The generator **self-validates and refuses to emit** on any violation (referential integrity,
step-id references, atom budgets, trust-stat aggregation). If it refuses, fix the `stageModels`
content (most likely a `<family>-NN` id referenced by a `spine_state.current` or artifact that no
longer exists, or a step count outside 4–7) and re-run until it emits clean. **Do not** disable or
weaken the gate.

### Step 4.5: Confirm placeholder flip + section stability
Confirm the emitted `org.js` has all four families at `placeholder: false`, and that **no ORG
section outside `stageModels` changed** (F4 section-stability — guards against seeded-RNG stream
shifts perturbing frozen values).

## Verification

> **NO TESTS.** Verification is the generator's **in-code invariant gate** (NOT a test file), a
> **JSON/parse spot-check**, a **byte-diff** for section stability, and a **manual disk-open** of
> the prototype. ~40% of this sub-phase is verification.

### Validation Scripts (temporary — delete after)
- **Generator emits clean** (the invariant gate passed):
  ```bash
  node prototype/data/_build/generate-org.mjs && echo "GENERATOR EMITTED — invariant gate green"
  ```
- **org.js loads & stageModels is real, plain data, placeholder flipped:**
  ```bash
  node -e "
    globalThis.window={};
    require('./prototype/data/org.js');           // classic script sets window.ORG
    const sm = window.ORG.stageModels;
    for (const f of ['feature','debug','spike','data']) {
      if (!sm[f]) throw new Error('missing family '+f);
      if (sm[f].placeholder !== false) throw new Error(f+' still placeholder:true');
      const n = sm[f].steps.length;
      if (n < 4 || n > 7) throw new Error(f+' step count '+n+' out of 4-7');
      for (const s of sm[f].steps) {
        if (!/^(feat|dbg|spk|data)-\d\d$/.test(s.id)) throw new Error('bad id '+s.id);
        if (!(s.artifacts && s.artifacts.length>=1)) throw new Error(s.id+' has no artifact');
        if (!(s.refs && s.refs.length>=2)) throw new Error(s.id+' has <2 refs');
        if (typeof s.surface!=='string') throw new Error(s.id+' missing surface');
        if (typeof s !== 'object') throw new Error('non-object step');
      }
      const ev = sm[f].steps.filter(s=>s.evidence).map(s=>s.evidence);
      if (ev.length !== (f==='debug'?2:1)) throw new Error(f+' wrong evidence count '+JSON.stringify(ev));
    }
    // E1..E5 each present exactly once across all families
    const all = ['feature','debug','spike','data'].flatMap(f=>sm[f].steps.map(s=>s.evidence)).filter(Boolean).sort();
    if (JSON.stringify(all)!==JSON.stringify(['E1','E2','E3','E4','E5'])) throw new Error('E1-E5 not 1:1: '+all);
    console.log('ok: 4 families, placeholder=false, ids/artifacts/refs valid, E1-E5 each once');
  "
  ```
  (No function values can survive the `file://` classic-script load — if any `does`/`surfaceWhy`
  is accidentally a template that references a binding, the generator or this load fails.)

### Manual Checks
- **Section stability (F4):** diff `org.js` against its pre-edit version; confirm **only the
  `stageModels` region changed**:
  ```bash
  git diff -- prototype/data/org.js     # every changed line is inside stageModels; nothing else moved
  ```
- **No hand-edit of org.js:** the only human edit was to `generate-org.mjs`; `org.js` was produced
  by re-running the generator (its GENERATED header is intact).
- **Disk-open smoke:** open `prototype/index.html` from disk in a browser (if a browser is
  available — see the prototype's "no browser for visual gates" carry-forward); confirm the four
  family spines render **without the PLACEHOLDER watermark** and labels match the derived
  `shortLabel ?? label`. If no browser is connectable, record a static-analysis verdict + a
  human-eyeball carry-forward (do not block — full autonomy).
- **Vocabulary match:** the rendered/loaded labels match sp3's canonical note (the note is the
  single source).

### Success Criteria
- [ ] Park gate was open (both 2a artifacts existed) before any edit.
- [ ] Only `generate-org.mjs`'s `stageModels` section was edited; `org.js` regenerated, not hand-edited.
- [ ] Generator emitted clean — invariant gate green.
- [ ] All four families `placeholder: false`; step ids `<family>-NN`; 4–7 steps each; ≥1 artifact
      + ≥2 refs per step; E1–E5 each present exactly once (debug hosts E2 **and** E3).
- [ ] `stageModels` is plain-JSON data (no functions); loads from the classic script.
- [ ] Section stability (F4): no ORG section outside `stageModels` changed (byte-diff clean).
- [ ] Disk-open shows real spines, no PLACEHOLDER watermark (or static verdict + eyeball
      carry-forward if no browser).
- [ ] sp4 completed **before** Phase 3 dispatch.

## Execution Notes
- **This is the only sub-phase that touches `prototype/`** — and only the org data, via the
  generator. If you find yourself editing `index.html`, `appState`, or any non-`stageModels` ORG
  section, stop: that is out of scope.
- **The generator gate is the safety net, not an obstacle.** A refusal means the derived
  vocabulary broke a referential invariant (usually a `spine_state.current` step id that the new
  spine no longer contains). Fix the content; never weaken the gate (NO TESTS, but the gate stays).
- **F4 / seeded-RNG:** if a re-emit perturbs values *outside* `stageModels`, the `stageModels`
  edit accidentally shifted the faker stream — confirm the edit is data-only and additive within
  the region, and that 2a's stage-model constants are not interleaved with seeded calls.
- **Parking is a valid terminal state for a poll cycle**, not a failure: if 2a hasn't landed,
  report `status: parked, awaiting prototype/data/_build/generate-org.mjs + org.js` and let the
  orchestrator re-dispatch. Do **not** stub a fake generator to unblock.
- **Spec-linked files:** none (FR-020 greenfield). No `/cast-update-spec`.
- **FULL AUTONOMY:** never wait for a human; the generator gate + the JSON/byte-diff checks are
  the acceptance criteria.
