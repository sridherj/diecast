# Sub-phase 3.4: The Real Hero Morph & Flow Stitch (SC-003)

> **Pre-requisite:** Read
> `docs/execution/product-revamp-diecast-phase3-feature-debug-morph/_shared_context.md` before
> starting. Every BINDING CONSTRAINT there applies here. This is the phase's **headline** sub-phase.

## Objective

The Phase 1 placeholder morph is **replaced**: on the real feature canvas, the scripted chat line
*"this is actually a bug, not a feature"* morphs `#/goal/CAST-412` into the **debug-family shape** in
~350ms with **≥4 anchors gliding** (goal header, chat rail, nudge card, receipt trail, nav rail,
evidence strip), drops the receipt derived from atom `DEC-CAST-412-03`, is **undoable** via the
scripted reverse, and degrades to the ≤200ms fade under reduced motion. Both flows + the morph pass
the **slop gate**; the drift grep is clean; Phase 3's decisions are appended to decisions-so-far.

## Dependencies
- **Requires completed:** **Sub-phases 3.2 + 3.3** — the morph swaps between the two **real**
  canvases (feature ⇄ debug-shape), and reuses both the exec tab (3.2) and the debug spine/evidence
  rendering (3.3).
- **Assumed codebase state:** `#/goal/CAST-412` (feature) and `#/goal/CAST-431` (debug) are both
  real, scripted, and walkable; `ORG.goals['CAST-412'].morph_view` exists (generator-authored in
  3.1); `DEC-CAST-412-03` is in `ORG.decisions`; the six vt- anchor wrappers exist except
  `vt-evidence-strip` (claimed here).

**Estimated effort:** 1 session (~3h), including gate evaluation and slop-gate reruns.

## Scope

**In scope:**
- Claim `vt-evidence-strip` on the evidence zone **wrapper** (never the `EvidenceBlock`).
- The morph data path: `morph:debug` / `morph:feature` on CAST-412 (state kept, not rebuilt).
- Keep the six anchors mounted across both family renders (component identity preserved).
- Stitch `SCRIPTS.feature` so morph + reverse + L3 sit mid-script; confirm `SCRIPTS.debug` walkable;
  delete Phase 1 placeholder script steps + placeholder spine data.
- Run the slop gate (4 surfaces), the Phase 1 gate-checklist re-run on real DOM, the drift grep.
- Append the Phase 3 decision summary to decisions-so-far.

**Out of scope (do NOT do these):**
- Re-shaping the debug canvas (3.3) or the exec tab (3.2) — consume them as-is.
- A reversal atom / second receipt — the undo emits **no second receipt** (Decision 9).
- Morphing *to* CAST-431's canvas — the morph stays on CAST-412 (`morph_view`); morphing to a
  different goal would read as navigation, not reshaping (US1 S2).
- Asset base64-inlining (Phase 6). **Any test file, suite, harness, or CI.**

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `prototype/index.html` | Modify | Has 3.1–3.3; gains `vt-evidence-strip` anchor, morph data path, stitched `SCRIPTS.feature`; loses Phase 1 placeholder morph + spine data |
| `docs/plan/product-revamp-diecast-decisions-so-far.md` | Modify (append ~15 lines) | Gains the Phase 3 decision summary |
| `prototype/data/org.js` | Possibly regenerate (via generator only) | If placeholder spine data must be deleted from data, do it in the generator |

## Detailed Steps

### Step 3.4.1: Claim `vt-evidence-strip`
- Add the anchor to the evidence zone **wrapper** in the canvas shell (zone wrapper, **never** the
  `EvidenceBlock`). Confirm the name appears on **exactly one element per snapshot** — the `#/kit`
  route must **not** render a wrapper with this name (kit shows bare components; uniqueness rule,
  BINDING #8). A duplicate silently kills **all** transitions.

### Step 3.4.2: Build the morph data path
- `morph:debug` on CAST-412 sets `family = 'debug'`, derives the debug spine from
  `stageModels.debug` + `morph_view.spine_state`, swaps the work zone to `morph_view.work_stream`
  (the just-seeded investigation: symptom row + first hypotheses) and the evidence strip to the E2
  seed; pushes the receipt derived from `ORG.decisions['DEC-CAST-412-03']`.
- `morph:feature` **restores the feature projection from the untouched goal data** (state kept, not
  rebuilt — the undo proof). Goal id, title, crumb, chat history **never change** (same goal, new
  shape).

### Step 3.4.3: Keep anchors mounted
- The six anchor elements keep **component identity** across both family renders (same wrapper
  elements, different inner content) — Phase 1's uniqueness + mounted-across-families rule, now on
  real DOM. The **exec panel stays closed** during the morph step (3.2 note) so tree DOM never
  participates in the transition.

### Step 3.4.4: Stitch the demo flow
- Finalize `SCRIPTS.feature` so the morph + reverse sit mid-script with the **L3 beat after the
  reverse** (the flow ends in the feature world, where CAST-417 lives). Confirm `SCRIPTS.debug` is
  independently walkable.
- **Remove** any Phase 1 placeholder script steps and the placeholder spine data (now fully
  superseded by spine reads — **delete, don't shadow**; if the placeholder data lives in ORG, delete
  it via the generator + regenerate, keeping non-batch sections byte-identical).
- Confirm **PRF2** holds across the morph: chat history is per-goal and survives the morph + reverse
  intact.

### Step 3.4.5: Gates (run all; fix and re-run until green)
- **Slop gate (4 surfaces):** screenshot feature canvas (post-3.1), debug canvas, exec drill-in open,
  mid-demo morphed state →
  → **Delegate: `/cast-preso-check-visual`** (verdict scoped to `not-generic` / `not-ai-aesthetic`;
    ignore slide-specific findings).
  → **Delegate: `/cast-preso-check-tone`** on visible copy (narration, nudge text, evidence labels —
    FR-018: no GPT-isms, hyphens not em dashes).
  Rework and re-run until green; **do not close the phase on a fail**. **Pass the FULL AUTONOMY
  directive down to both checkers.** Retain screenshots + verdicts; log borderline passes to
  `borderline-calls.md`.
- **Phase 1 gate checklist re-run on real DOM** (all five): anchors glide rather than crossfade · no
  flash/flicker/layout jump · runs from `file://` in Chrome · reads as ~350ms of revealed layout, not
  spectacle · reduced-motion works. Record verdict + one-line evidence per item in execution notes.
- **Drift grep re-run** (2a.3's recorded command):
  `grep -rn -e 'CAST-4' -e 'M04\|S03\|R02' -e '99\.9\|99\.4\|505 runs\|312 runs' -e 'crud-orchestrator' -e '1/3' -e 'Northwind\|northwind' prototype/ --include='*.html' --include='*.js'`
  → every canonical-token hit is in `data/org.js` / `data/_build/`; the `#/kit` fixture exception is
  gone if the fixture swap happened, else remains the one sanctioned allowlist entry.
- Append the Phase 3 decision summary (~15 lines) to `decisions-so-far.md`.

## Verification (the phase's headline verification — manual click-through, NO TESTS)

### Manual Checks
- From disk, advance `SCRIPTS.feature` to the morph step: the canvas reshapes feature→debug — segment
  bar out, loop band + `↺ iter 1/3` in; E1 strip content crossfades to the seeded E2 view; goal
  header (`CAST-412 · Add RBAC to checkout`), chat rail, nudge card, receipt trail, nav rail, and the
  **evidence-strip wrapper** persist and glide (DevTools → Animations: ~350ms total; **≥4 named
  groups animating**).
- The receipt pill appears in the trail during/after the morph and renders level/label/time from
  `DEC-CAST-412-03` (`decision_id` populated); clicking opens the 6B callout with rationale +
  revisit_if from the atom.
- The next scripted step **reverses** the morph (`morph:feature`) with **no state loss** — the
  feature canvas returns exactly as it was (stageFocus, pinned items, chat history intact). **No
  second receipt** is emitted.
- DevTools → Rendering → emulate `prefers-reduced-motion: reduce` → the same step is a **≤200ms fade**,
  no sliding motion.
- The morph **never fires unprompted** — exclusively the consequence of the scripted user line.
- **Slop gate:** all four surfaces return `not-generic` / `not-ai-aesthetic` (visual) and clean tone;
  reworked until green.
- **Drift grep:** clean (all canonical-token hits in `data/`).

### Success Criteria (binary — every item must pass)
- [ ] Morph reshapes feature→debug in ~350ms with ≥4 anchors gliding; E1→E2 crossfade; header/crumb/chat unchanged.
- [ ] Receipt derived from `DEC-CAST-412-03` (no morph-local label strings); 6B callout from the atom.
- [ ] Reverse restores feature canvas with no state loss; **no second receipt**.
- [ ] Reduced-motion → ≤200ms fade; morph never fires unprompted.
- [ ] `vt-evidence-strip` on the evidence wrapper only; exactly one per snapshot; `#/kit` doesn't carry it.
- [ ] Phase 1 five-item gate checklist re-run on real DOM — recorded with evidence.
- [ ] Slop gate green on all 4 surfaces (visual + tone), via the checker agents; evidence retained.
- [ ] Drift grep clean; Phase 1 placeholder morph + spine data deleted (not shadowed).
- [ ] **PRF2** holds across the morph (per-goal chat survives morph + reverse).
- [ ] Phase 3 decision summary appended to `decisions-so-far.md`.

## Execution Notes
- **Morph-regression is the load-bearing risk:** real canvases carry far more DOM than the Phase 1
  placeholders — snapshot cost can turn the morph janky. Mitigations are **structural**: exec panel
  closed during morph, older debug passes collapsed by default, screenshots are small thumbs. If jank
  persists, reduce crossfading-zone depth (the *family content*) **before** touching the anchor set;
  if View Transitions still can't carry it, the Phase 1 **panel-swap contingency** applies
  mechanism-only (op grammar unchanged).
- **Receipt provenance:** the receipt must be *derived* from the atom (2a.3 wired this) — no
  morph-local label strings. The undo emits **no second receipt** (Decision 9; reversal-atom question
  deferred to the real product).
- **Gate honesty under full autonomy:** checklist criteria are pre-written (above) before the re-run;
  slop-gate verdicts come from the **external** checker agents; screenshots + verdicts retained;
  borderline passes → `borderline-calls.md`.
- **Naming:** anchor name `vt-evidence-strip` matches Phase 1's reserved-name note verbatim.
- **Spec-linked files:** none (greenfield, FR-020). `decisions-so-far.md` is a planning doc, not a spec.
- **Failure policy:** retry once; on critical path (it is — the phase headline) a second failure →
  **stop and report**.
