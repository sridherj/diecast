# Sub-phase 4.1: Spike Flow — Timebox Canvas, Memo Surface & Verdict↔Decision Linkage

> **Pre-requisite:** Read `docs/execution/product-revamp-diecast-phase4-spike-data/_shared_context.md`
> before starting this sub-phase. The binding constraints there are not optional.

## Objective

`#/goal/CAST-452` is the real spike canvas and is *deliberately the lightest surface in the
prototype*: a timebox-meter spine (3h budget · 1h40m used, with the L2 extension recorded on it), a
single probes-tried card as the work zone, the memo familiar surface at the conclusion step, and the
E4 verdict card ("adds 180ms p95 — borderline", ◐ confidence, 3 deciding data points) whose
`spike_ref` linkage to the L3 decision atom is navigable in **both directions in ≤1 click each**
(FR-016 / US2 S3). The spike script walks end-to-end and stops at the family's single L3. **The ORG
data extensions for *both* Phase 4 goals land here via the generator**, so 4.2 and 4.3 never touch
`generate-org.mjs`. This sub-phase is the **root of the critical path** (4.1 → 4.3 → 4.4).

## Dependencies
- **Requires completed:** Phase 3 (canvas grammar, `StageSurface`, script plumbing, `stageFocus`);
  2a/2b/2c (org frozen, kit locked, `stageModels.spike` real, `placeholder: false`).
- **Assumed codebase state:** `prototype/index.html` carries the Phase-3 feature + debug canvases,
  the kit, the closed 5-op dispatcher, the 6×1 vt- anchor set, and `SCRIPTS = {feature, debug}`.
  `prototype/data/org.js` carries the frozen 2a spine + 2c vocabulary. If 2c vocabulary hasn't
  landed (`placeholder: true`), **stop and resolve first** (Phase 3's inherited rule).

## Scope
**In scope:**
- The one generator-extension batch for **both** Phase 4 goals (thin `execution` ×2, `parity`,
  `resolved_view`) + the four new gate invariants.
- The spike canvas composed from the shared grammar (deviated zones: timebox meter spine + single
  Timebox/probes-tried card).
- Fleshing out `StageSurface`'s `memo` kind (Phase 3 shipped the thin version).
- Wiring E4 (`EvidenceBlock {kind:'E4'}`) + the evidence-strip summary + bidirectional `spike_ref`
  navigation as local disclosure.
- Decision chips (L1 pill, L2 extension chip on the meter, L3 needs-you chip → `EscalationRail`).
- `SCRIPTS.spike` (~6–7 steps) with an explicit reserved beat slot for 4.3's parity step.

**Out of scope (do NOT do these):**
- The data-analysis canvas / `notebook` kind / E5 chart (4.2).
- Building the parity terminal pane (4.3) — only **reserve the script beat slot** here.
- Resolving the spike L3 — it stays an unresolved stop (options complete but inert).
- Any colleague/board/hiring surface (Phase 5), entry-screen routing or asset inlining (Phase 6).
- Any test file, suite, or harness; any new op; any hand-edit of `org.js`.

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `prototype/data/_build/generate-org.mjs` | Modify | Seeded self-validating generator; **this sub-phase is the sole Phase-4 owner** |
| `prototype/data/org.js` | Regenerate (never hand-edit) | Frozen `window.ORG`; gains the four additive keys |
| `prototype/index.html` | Modify | Phase-3 prototype; gains the spike canvas section + `memo` flesh-out + `SCRIPTS.spike` |

## Detailed Steps

### Step 4.1.1: The single generator-extension batch (both goals)
Extend `generate-org.mjs` with three additive payloads, then regenerate and gate:
- **(a) thin `execution`** on both goals: `{runs: [{id, agent, status, when, summary,
  rework_count}]}`, 1–2 runs each, **no `focus_run` tree** (Decision 10 — playbook 03 says the spike
  has no dispatch tree; thin mirrors Phase 3's thin-CAST-431).
- **(b) `goals['CAST-452'].parity`** `= {command, transcript: [...lines], artifact_id, caption}` —
  the FR-017 terminal text lives in the spine so skill names and artifact ids can't drift (consumed
  by 4.3).
- **(c) `goals['CAST-461'].evidence.resolved_view`** `= {series: [...both sources...],
  reconciliation_note}` — consumed by 4.2's L3-resolution beat; **the authored report v1/v2 version
  semantics stay untouched** (freeze policy).
- **New gate invariants:** `parity.artifact_id` resolves to the E4 verdict artifact; `transcript`
  non-empty and contains the artifact line; `resolved_view.series` covers exactly the two
  disagreeing sources; thin `execution.runs` agents resolve in `ORG.agents`.
- Regenerate (`node generate-org.mjs`); gate green; `git diff org.js` additive-only; F4
  byte-identical outside the four declared keys.

### Step 4.1.2: Compose the spike canvas from the shared grammar
Identical header band, decision chips, exec tab, chat rail; **deviated zones only** — spine zone
renders `StageSpine` with the 2b `timebox` shape (meter reads `spine.timebox.{budget, used}`, the
four sub-steps render beneath the meter per the 2c FLAG); work zone renders the single Timebox Card
(probes-tried rows). **No stage-artifacts grid, no ticket stream — the lightness *is* the design**
(contrarian §6: a spike must never look like a mini-feature).

### Step 4.1.3: Flesh out `StageSurface`'s `memo` kind
One-pager memo treatment — dated mono header, the probes summary, the conclusion line, the timebox
stamp — full-bleed in the stage zone per the familiar-tool principle, with its `surfaceWhy` caption.
(Phase 3 shipped the thin version and explicitly assigned this flesh-out to Phase 4.)

### Step 4.1.4: Wire E4 + bidirectional `spike_ref`
`EvidenceBlock {kind:'E4', data: goal.evidence}` at the step whose `evidence === 'E4'` (`spk-04`),
plus the evidence-strip summary in the default view. Implement the bidirectional `spike_ref`
navigation as **local disclosure** (the existing chip→callout mechanism + scroll/highlight), **not a
new op** — the closed vocabulary stands (Decision 11).

### Step 4.1.5: Decision chips + L3 at WHAT
L1 pill (the "timeboxed to 2h; p95 only" atom on its owning artifact); the L2 extension chip
("extended 2h→3h") on/adjacent to the meter, opening the 6B callout with rationale + `revisit_if`;
the L3 needs-you chip in the header band opening `EscalationRail` (3 ranked options
proceed / self-host / renegotiate, **nothing pre-selected, options inert** per Phase 3 decision #10).

### Step 4.1.6: Author `SCRIPTS.spike` (~6–7 steps)
Keyed on route entry by family; narration interpolates canonical tokens from `ORG`. Beat order:
open → Guide nudge → probe beat → timebox/L2-extension beat → verdict (E4) beat →
**[parity beat slot — leave explicit, filled by 4.3]** → L3 stop → close.

## Verification

> **NO TESTS (binding):** every check below is **manual click-through / static observation**. In an
> autonomous run with no browser, satisfy each via the strongest static evidence (`node --check`,
> grep audits, a throwaway `/tmp` logic harness that is never committed) and record a non-blocking
> human-eyeball carry-forward for any rendered-pixel item. **Do not flag missing tests.**

**Verification (manual click-through) — verbatim from the plan:**
- Open `prototype/index.html` from disk → `#/goal/CAST-452`: console clean; the timebox meter
  renders from `stageModels.spike.timebox` + `spine_state.timebox_used` (3h budget, 1h40m
  used, proportional fill); real 2c vocabulary, no `PLACEHOLDER` watermark; the header reads the
  question-as-L1 ("Does the vendor checkout SDK fit our 200ms p95 budget?") with the
  spike pill and the nudge from the goal's nudge object.
- **The lightness glance test (playbook 03 pitfall #3):** side-by-side with
  `#/goal/CAST-412`, the spike canvas reads materially lighter — a meter, not a segment bar;
  one card, not a work stream + stage artifacts grid. If it reads as a shrunk feature
  backbone, that is a defect.
- The probes-tried card lists each probe + one-line result from the work stream, with
  line-density `ColleagueCard` attribution where an agent ran the probe.
- The L2 extension chip ("extended 2h→3h") renders on/adjacent to the meter; clicking opens
  the 6B callout with rationale + `revisit_if` from its atom. One L1 chip (the "timeboxed to
  2h; p95 only" atom) renders on its owning artifact.
- Clicking the conclusion step on the spine (`drillInto:<spk-NN>`) renders the **memo
  surface**: one-pager findings memo (dated, mono header, probes summary, conclusion line)
  with its `surfaceWhy` caption. Back/forward and re-render preserve `stageFocus`.
- The E4 verdict card renders at its home step and summarized in the evidence strip:
  one-line answer + ◐ (M) confidence glyph + the 3 deciding data points + the `spike_ref`
  link. **Never a bare pass state.**
- **`spike_ref` both directions, ≤1 click each:** clicking `spike_ref` on the verdict opens
  the L3 decision (rail/callout view, evidence pack visible); from the decision, the
  `spike_ref` field links back to the verdict card (scroll + highlight). Ids match the atom.
- The L3 needs-you chip renders at WHAT level; the `EscalationRail` shows the 3 ranked
  options (proceed / self-host / renegotiate), nothing pre-selected; options are inert
  (the stop is shown, not resolved — see Decisions #4).
- "Next ▸" walks `SCRIPTS.spike` start-to-finish: open → Guide nudge → probe beat →
  timebox/L2-extension beat → verdict (E4) beat → [parity beat slot, filled by 4.3] → L3
  stop → close. Narration interpolates canonical tokens from `ORG`; reload resets clean.
- Exec tab: thin run list (1–2 runs, **no dispatch tree**); `appState.drill` toggles cleanly.
- Generator check: `git diff` on `data/org.js` shows only additive keys; the invariant gate
  passes; drift spot-check (edit a value in the generator, regenerate, reload, observe,
  revert).

### Success Criteria (binary — every item must pass or carry forward with reason)
- [ ] Generator regenerates `org.js` deterministically; gate green; `git diff` additive-only; F4 holds.
- [ ] Spike canvas renders the timebox meter + single probes card; lightness glance test passes
      (or is a recorded eyeball carry-forward).
- [ ] `memo` `StageSurface` kind renders at the conclusion step with `surfaceWhy`.
- [ ] E4 verdict card + evidence-strip summary render; `spike_ref` navigates both directions ≤1 click.
- [ ] L1 pill, L2 extension chip (on meter), L3 chip → inert `EscalationRail` all render.
- [ ] `SCRIPTS.spike` walks end-to-end with the parity beat slot reserved; reload resets.
- [ ] Closed 5-op set intact; 6×1 vt- anchors unchanged; `node --check` clean.

## Design review (verbatim from the plan)
- **Spec consistency (stage vocabulary):** zero hardcoded stage labels/surfaces/budgets —
  meter math reads `timebox.budget` + `spine_state.timebox_used`; grep for any 2c label
  string in `index.html` must return nothing.
- **Spike-as-mini-feature is the family-killing pitfall:** the review check is the
  side-by-side lightness glance in verification; deviation beyond "meter + one card" toward
  feature-canvas density is a defect, not polish.
- **Error path:** `timebox_used` exceeding `budget` (data error) renders the meter overrun
  segment in `--fail` with a `console.warn` rather than clamping silently (mirrors 3.3's
  iter guard). Unparseable duration strings render the raw string + warn.
- **ORG freeze discipline:** all three data extensions go through the generator with new
  invariants; `resolved_view` is additive on the evidence payload — **no mutation of the
  authored report v1/v2 values** (freeze policy).
- **Naming:** `parity` block keys lower_snake (org-data convention); spike canvas classes
  stay under `surf-*` / existing kit classes — no new prefix needed in 4.1.

### Design Review Flags (this sub-phase's rows, verbatim from the plan)
| Sub-phase | Flag | Action |
|-----------|------|--------|
| 4.1 | Spike canvas drifting heavy (mini-feature pitfall kills the family thesis) | Lightness glance test in verification; "meter + one card" is the spec, density is a defect |
| 4.1 | ORG mutation outside the generator | All three data extensions via `generate-org.mjs` + new invariants; diff additive-only |
| 4.1 | `spike_ref` navigation tempting a sixth op | Local disclosure (chip→callout + scroll/highlight); closed vocabulary stands |
| 4.1 | Timebox overrun / unparseable duration | `--fail` render + console.warn; never silent clamp |

## Execution Notes
- **Generator single-owner:** 4.1 is the *only* Phase-4 sub-phase that edits `generate-org.mjs`.
  Commit the regenerated `org.js` before any parallel 4.2 work touches `index.html` data reads
  (Reconciliation F3 / F4).
- The `timebox` and `pipeline` `StageSpine` shapes **already exist** (2b) — do not re-author them;
  the spike meter just reads `spine.timebox.{budget, used}`.
- `spike_ref` is **bidirectional and gate-enforced** in the data; the UI nav is local disclosure
  only — adding an op here is a defect.
- **Spec-linked files:** none — the prototype is greenfield (FR-020); no `/cast-update-spec` action.
- **Plan review:** SKIPPED per run config — do not dispatch `/cast-plan-review` or any reconciliation
  pass.
