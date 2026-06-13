# Sub-phase 3.3: Debug-Loop Canvas — Investigation Surface, E2 Ledger & E3 Red→Green

> **Pre-requisite:** Read
> `docs/execution/product-revamp-diecast-phase3-feature-debug-morph/_shared_context.md` before
> starting. Every BINDING CONSTRAINT there applies here.

## Objective

`#/goal/CAST-431` becomes the **real debug canvas** and is *obviously a different shape* from the
feature canvas **at a glance**: the 2c-derived `loop` band with the `↺ iter 2/3` badge, an
investigation work zone where iteration history is first-class (refuted hypotheses struck but
visible), the **E2** confirm/refute ledger as the work-zone hero (home `dbg-04`), the **E3**
red→green repro at its home step (`dbg-05`), the debug nudge, the debug L3 moment, and a scripted
debug clickthrough end-to-end. It is built from the **same canvas grammar** as the feature canvas —
**only the spine + evidence/work content deviate** (this is what the morph and SC-002 coherence
depend on; deviation beyond those two zones is a defect).

## Dependencies
- **Requires completed:** **Sub-phase 3.1** (canvas grammar, `StageSurface`, work-stream frame,
  decision-chip plumbing, script plumbing, `scriptKey`/per-goal chat) **and Sub-phase 3.2** (serial —
  the shared Execution-tab shell; the debug canvas inherits it for the thin run-list beat).
- **Assumed codebase state:** `#/goal/CAST-412` is the real feature canvas with the Execution tab;
  `ORG.stageModels.debug` carries the loop vocabulary; `ORG.goals['CAST-431']` carries
  `spine_state.iter {current:2, budget:3}`, the investigation-ledger artifacts, E2 + E3 payloads, a
  nudge object, its L3 atom, and a thin `execution`.

> **Serial-execution note (autonomous override):** the plan calls 3.3 "parallel-capable with 3.2",
> but both edit the same `prototype/index.html` with no merge mechanism. **3.3 runs serially after
> 3.2.** Partition your additions into a clearly-bannered debug-canvas section, disjoint from 3.2's
> `exec-*` section.

**Estimated effort:** 1 session (~3h).

## Scope

**In scope:**
- Compose `#/goal/CAST-431` from the shared grammar; deviate **only** spine + evidence/work zones.
- The investigation ledger work zone: iteration-history rows (collapse, never delete — FR-007),
  experiment rows with `ColleagueCard` attribution, the E2 `EvidenceBlock` as the live pass's hero.
- E3 red→green at its home step (`dbg-05`).
- Debug decision chips: the L3 atom chip + rail; one L1 pill on an investigation artifact.
- `SCRIPTS.debug` (~6 steps), keyed on route entry (per-goal chat per PRF2).
- Surface CAST-431 in the goal/nav list with its family tag.

**Out of scope (do NOT do these):**
- Re-authoring ORG data — CAST-431's debug payloads already exist (2a) + thin `execution` (3.1). If a
  shape mismatch surfaces, **fix in the generator**, never fork the component, never hand-edit `org.js`.
- A deep dispatch tree for CAST-431 — it gets the **thin run list** (Decision 8); the deep tree is
  feature-only (3.2).
- The morph / `vt-evidence-strip` / slop gate / flow stitch — **3.4**.
- Inventing a third spine treatment, or deviating any zone beyond spine + evidence/work.
- Entry-screen `#/` chooser routing (Phase 6). **Any test file, suite, harness, or CI.**

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `prototype/index.html` | Modify | Has 3.1 grammar + 3.2 exec tab; gains the debug canvas (loop band, investigation ledger, E2/E3), `SCRIPTS.debug`, nav-list family tag |

## Detailed Steps

### Step 3.3.1: Compose the debug canvas from the shared grammar
- Same header band, work-stream frame, chips, exec tab, chat rail. **Only spine + evidence/work
  content deviate.** Deviation beyond those two zones is a defect (SC-002 coherence + the morph
  depend on it).
- Spine: the `loop` band rendered from `ORG.stageModels.debug` + `spine_state.iter` → `↺ iter 2/3`
  badge. Header reads the symptom-as-question ("Checkout 500s on coupon apply"). **No hardcoded
  vocabulary** (BINDING #5) — all labels/counts from data.

### Step 3.3.2: Work zone = the investigation ledger
- Iteration-history rows (one per pass; older passes **collapsed by default, expandable, never
  removed** — FR-007). Each pass contains its experiment rows (line-density `ColleagueCard`
  attribution where an agent ran the experiment) and the **E2 `EvidenceBlock`** as the live pass's hero.
- E2 ledger rows: per-hypothesis `prediction → observation → verdict`. H1/H2 **refuted** rows struck
  with `--fail` marks **and still visible**; H3 **confirmed** with `--ok`. Pass 1 collapsed (not
  deleted), pass 2 live.
- **Error path:** `iter.current > iter.budget` (data error) renders the counter in `--fail` with a
  `console.warn` rather than clamping silently.

### Step 3.3.3: Place E3 red→green
- Via the `stageModels.debug` `evidence` home step (`dbg-05`): same test name red **then** green,
  mono excerpts, `--fail` / `--ok` headers — **never a bare green badge**. The default view's
  evidence strip summarizes the latest verdict state.

### Step 3.3.4: Debug decision chips
- The debug L3 atom (shared-auth-middleware fix scope) surfaces as the needs-you chip at WHAT with
  its `EscalationRail`; **exactly one L3** in the flow. One L1 pill on an investigation artifact
  (whichever L1 atom 2a authored for CAST-431). Rail options inert (Decision 10).

### Step 3.3.5: Author `SCRIPTS.debug` (~6 steps)
- Keyed on route entry (per-goal chat per PRF2): open → nudge → experiment beat → refute/confirm beat
  → E3 beat → L3 beat. Include the **thin exec-tab beat** so the shared grammar is visibly shared.
  Narration interpolates canonical tokens from `ORG` (the root-cause weave ties to the v4.2 RBAC
  migration — from `ORG`, not retyped).

### Step 3.3.6: Nav rail
- Surface CAST-431 in the goal list with its family tag. (The `#/` chooser stub gains nothing —
  entry-screen routing is Phase 6.)

## Verification (manual click-through — NO TESTS)

### Manual Checks
- `#/goal/CAST-431` from disk: loop-band spine with `↺ iter 2/3` (from `stageModels.debug` +
  `spine_state.iter`), real 2c vocabulary (Reproduce Reliably · Form a Hypothesis · Run an Experiment
  · Log Confirm/Refute · Prove the Fix), no watermark; header reads "Checkout 500s on coupon apply".
- **SC-005 glance test:** screenshot `#/goal/CAST-412` and `#/goal/CAST-431` side by side → a viewer
  names which is which in **<3 seconds** citing the spine shape (segment bar vs loop band + counter).
  **Keep the screenshots as evidence** (3.4's slop gate reuses them).
- E2 ledger in the work zone: per-hypothesis `prediction → observation → verdict` rows; H1/H2 refuted
  rows struck with `--fail` **and still visible**; H3 confirmed with `--ok`. Pass 1 collapsed (not
  deleted), pass 2 live.
- E3 at `dbg-05`: same test name red then green, mono excerpts, `--fail` / `--ok` headers — never a
  bare green badge.
- The debug nudge renders from CAST-431's nudge object; the debug L3 surfaces as the needs-you chip
  at WHAT with its rail; **exactly one L3**; one L1 chip on an investigation artifact.
- "Next ▸" walks `SCRIPTS.debug` start-to-finish: open → nudge → experiment → refute/confirm → E3 →
  L3. The exec tab opens to the **thin run list** (no deep tree).
- Story weave: the root-cause narration ties to the v4.2 RBAC migration (from `ORG`, not retyped) —
  the org reads as one company.
- **Shape-contrast honesty:** the loop band shares the 1B zone grammar while reading as a loop (the
  `↺` badge + counter is the signature); **no third spine treatment invented**. No zone beyond spine
  + evidence/work deviates.

### Success Criteria (binary — every item must pass)
- [ ] `#/goal/CAST-431` loop band + `↺ iter 2/3` from data; real 2c vocabulary; no watermark; symptom-as-question header.
- [ ] SC-005 glance test passes (<3s, citing spine shape); side-by-side screenshots retained.
- [ ] E2 ledger: refuted hypotheses struck **and visible**; confirmed marked; prior pass collapsed not deleted (FR-007).
- [ ] E3 red→green (red then green, never a bare green badge).
- [ ] One L3 chip + rail; one L1 pill; debug nudge from data.
- [ ] `SCRIPTS.debug` walks end-to-end incl. the thin exec-tab beat (no deep tree on CAST-431).
- [ ] Only spine + evidence/work deviate from the feature grammar; no hardcoded vocabulary.
- [ ] `iter.current > iter.budget` → `--fail` counter + `console.warn` (no silent clamp).

## Execution Notes
- **Iteration-visibility is load-bearing** (FR-007): refuted hypotheses and prior passes stay visible
  (collapse, never delete) — the family's whole thesis rests on it.
- **E2/E3 data must match 2b's locked `EvidenceBlock` shapes verbatim** (`hypotheses[].verdict ∈
  confirmed|refuted|open`, `before/after.status`). Any mismatch is a 2a data bug to **fix in the
  generator**, not a component fork.
- Deviation beyond spine + evidence/work content = defect (HOLD SCOPE; 2c's flag channel was the
  place to contest shapes, now closed).
- **Spec-linked files:** none (greenfield, FR-020).
- **Failure policy:** retry once; on critical path (it is) a second failure → **stop and report**.
