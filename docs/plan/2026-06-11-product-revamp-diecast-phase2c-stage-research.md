# Product Revamp: Diecast — Phase 2c: Stage-Model Research — Derive the Right Per-Family Spines

## Overview

This phase is a **research spike, not code**. It derives the actual stage vocabulary for the
four workflow families (feature / debug / spike / data-analysis) from how the **best
practitioners in each category actually work** — studied via the exploration reference set plus
a targeted online scan — and captures the result as the canonical per-family stage definition
that Phases 3–4 build and Phase 2a encodes into the org data. The exploration's illustrative
steps (feature: prototype-with-UI-choices → locked design → eng design; debug: repro · RCA ·
evidence · fix · tests) are **explicitly dropped as placeholders** (owner: "those are not the
right steps — we have to explore online and come up with the right mental models"). Every
derived step must pass the test: *would a top practitioner in this category recognize this as
their actual workflow?* — concrete verb+artifact steps, not tidy phase labels someone invented.

**Primary deliverable:** `docs/plan/product-revamp-diecast-stage-models.md` — the stage-model
note naming the chosen spine per family, each step's familiar-tool surface mapping with
rationale + references, a ready-to-encode JSON block for 2a, and a written self-evaluation
against the practitioner-recognition test (which replaces the owner sign-off gate under the
run's full-autonomy configuration).

## Position in Overall Plan

```
                 Phase 1  (DONE — render arch, appState/spine contract, placeholder morph)
                    │
    ┌───────────────┼────────────────┐
    ▼               ▼                ▼
 Phase 2a        Phase 2b      ► Phase 2c ◄  (THIS PLAN — research, parallel with 2a/2b)
 (org data)   (component kit)   stage-model note ──► consumed by Phase 3/4 canvases
    ▲                                │                and encoded into org data by 2a
    └── shape-coordination only ─────┘
```

Phase 2c is on nobody's critical path for chrome, but it **gates every canvas build**: Phase 3
cannot author the feature/debug canvases until the spines are derived, and 2a needs the
`stageModels` data shape before freezing `org.json`. It runs fully in parallel with 2a/2b —
the only coordination point is the encoding shape (Sub-phase 2c.3).

## Operating Mode

**HOLD SCOPE** — instructed by the delegation context ("plan exactly what the high-level plan
section says for this phase"), and the high-level plan bounds the phase tightly ("0.5–1 day /
1–2 sessions", a "short stage-model note" as the verification artifact). No expansion signals.
Concretely: four families, one note, one encoding contract, one self-evaluation — no extra
families, no speculative future-family research, no UI work (that is Phase 2b/3 territory).

## Depends On (from prior plans)

From **Phase 1 — Keystone** (`docs/plan/2026-06-11-product-revamp-diecast-phase1-keystone.md`)
and the decisions-so-far log:

- **`appState.spines` v1 contract** (keys must not be renamed, only extended):
  `spines.<family> = { placeholder, shape, steps: string[], current, iter?: {current, budget} }`.
  Phase 1 labels carry `placeholder: true` + a visible PLACEHOLDER watermark; 2c's output is
  what flips that flag. The derived vocabulary must be expressible such that `steps` **remains
  a flat label array** at the appState level (rich per-step data lives in the org data — see
  Sub-phase 2c.3).
- **Spine shape vocabulary** from the component picks (design-decisions + 2b's brief):
  feature = `segments` (1B labeled segment bar) · debug = `loop` (2B staged band + ↺ iter
  counter) · spike = `timebox` (budget meter) · data = `pipeline` (DAG). Research validates or
  *flags* these shapes; it does not silently change them.
- **Familiar-tool principle + working surface set** (design-decisions, owner-locked): doc ·
  board/ticket list · PR-thread/report · investigation ledger · notebook+chart · memo+timebox.
  Every derived step maps to one of these (or explicitly proposes an addition — a flag, not a
  silent invention).
- **Canvas anatomy principle:** each stage owns its artifacts; the spine is a navigator. So
  every derived step must name **at least one concrete artifact** it owns.
- **E1–E5 evidence catalog** (owner-blessed): E1 acceptance panel (feature) · E2 confirm/refute
  ledger + E3 red→green repro (debug) · E4 verdict card w/ spike_ref (spike) · E5 rendered
  report + provenance (data). Each treatment must have a named **home step** in its family's
  derived spine.
- **`file://` single-file constraint** (Phase 1 hard constraint): org data ships as a classic
  script (`window.ORG`) or inline JSON — the stage-model encoding must be plain JSON-compatible
  data (no functions, no module imports).

---

## Sub-phase 2c.1: Practitioner Evidence Base — Mine + Targeted Scan (×4 families, parallel)

**Outcome:** For each of the four families there is a logged evidence base of **3–6
practitioner-grade references** with extracted candidate steps and supporting quotes — enough
raw material that the spine derivation in 2c.2 cites sources instead of inventing labels.

**Dependencies:** None (Phase 1 contracts already absorbed).

**Estimated effort:** 0.5–1 session (four ~60–75-minute timeboxed mini-scans; the four family
scans are independent and parallelizable).

**Verification:** A working-notes section (drafted directly into the stage-models note or a
scratch appendix) lists per family: ≥3 references with author/source named, the concrete steps
each source evidences (with a short quote or paraphrase), and a source-quality mark. At least
one reference per family is a **hands-on practitioner account** (a practitioner describing
their own process), not a methodology textbook or consulting framework.

Key activities:

- **Mine the exploration reference set first** (cheap, already curated): deep-read
  `exploration/research/03-family-canvases-evidence.ai.md` §"Expert-Practitioner Insights" and
  §"The Four Family Blueprints" + its Consolidated Sources / Reference-Link Map; skim
  `research/05-decisions-autonomy.ai.md` Lens 1 for how decisions punctuate workflows. Extract
  every practitioner-workflow claim relevant to stage vocabulary, with its citation.
- **Targeted online scan per family** (WebSearch/WebFetch directly; timebox ~60–75 min each).
  Seed targets — validate, extend, or replace these; they are starting points, not the answer:
  - **Feature-builders:** Shape Up (Basecamp — shaping/betting/building, vertical slices),
    the Linear Method (project briefs, scope cuts), design-engineering prototype-first practice
    (Vercel/Figma design-eng writing), eng design-doc/RFC culture (Stripe/Google), trunk-based
    development + feature flags + incremental rollout/verification (DORA, "ship small" practice).
  - **Debuggers:** David Agans *Debugging: The 9 Indispensable Rules* ("make it fail", "quit
    thinking and look"), Andreas Zeller's scientific debugging (hypothesis → prediction →
    experiment → observation), Julia Evans' debugging zines/posts (practitioner-loved, concrete),
    `git bisect` / minimal-repro culture (SSCCE), SRE incident response + blameless postmortems.
  - **Spike-runners:** XP spike solutions (C2 wiki / Extreme Programming sources), timeboxed
    research practice, ADR practice (Nygard) as the consumption end of a spike, memo-culture
    conclusion write-ups (one-pager findings memos).
  - **Data analysts:** Hadley Wickham's import→tidy→transform/visualise/model→communicate loop
    (R4DS — a real practitioner workflow, widely recognized), notebook-to-report practice
    (Hex/Deepnote/Observable workflows), analytics-engineering source-validation practice (dbt
    culture), published "how I actually analyze data" practitioner accounts (sanity checks,
    data-cleaning reality).
- **Source-quality filter:** prefer practitioner-authored books/posts/talks describing their own
  process; reject SEO listicles and consultant lifecycle diagrams. Mark each reference
  practitioner-account / tool-documented-workflow / methodology-text.
- **Escalation hatch (bounded):** if a family's scan comes back thin (<3 quality references),
  → Delegate: `/cast-web-researcher` — one targeted dispatch scoped to that single family's
  practitioner workflow, with the seed list above as starting context. Review output for
  source quality before admitting it to the evidence base. Do not run it by default — HOLD
  SCOPE; the targeted scan should suffice for most families.

**Design review:**
- **Source-quality gate is the review:** the owner's directive fails exactly when the evidence
  base is built from abstract methodology texts. The "≥1 hands-on practitioner account per
  family" check is mandatory, not advisory.
- **Anchoring hazard:** the dropped placeholder steps must NOT be used as search queries or
  candidate lists during the scan — gather evidence fresh; comparison happens only in 2c.2.
- No spec or naming concerns (research-only sub-phase).

## Sub-phase 2c.2: Spine Derivation & Practicality Pressure-Test

**Outcome:** Each family has a derived candidate spine of **4–7 steps**, every step scored
against an explicit practicality rubric, loop-vs-progress semantics decided per family, and
every step mapped to its familiar-tool surface with a one-line rationale and the reference(s)
it was drawn from. The exploration's dropped placeholders are explicitly dispositioned in a
ledger (what replaced each, and why).

**Dependencies:** Sub-phase 2c.1 (evidence base).

**Estimated effort:** 0.5 session.

**Verification:** For each family: a candidate spine table exists (step id, label, what the
practitioner actually does, owned artifact(s), surface + rationale, refs); every step carries
pass marks on all five rubric tests below (or was renamed/dropped with a note); the
dropped-placeholder ledger covers every illustrative step from the exploration; the
loop/progress call is stated per family with its evidence.

Key activities:

- **Derive first, compare after:** draft each family's spine purely from the 2c.1 evidence.
  Only then diff against (a) the dropped exploration placeholders and (b) Phase 1's watermarked
  stub labels — record the diff in the dropped-placeholder ledger. This ordering is the
  anti-anchoring protocol.
- **Run every candidate step through the practicality rubric** (all five must pass):
  1. **Verb+artifact test** — the step names something a practitioner *does* that yields a
     tangible artifact ("Get a failing repro", not "Analysis").
  2. **Recognition test** — the step appears (under any name) in ≥2 independent 2c.1 sources;
     cite both.
  3. **Hole test** — a top practitioner would notice its absence from the spine.
  4. **Tidy-label kill test** — if it only appears in textbooks/consulting frameworks and never
     in practitioner accounts, kill or rename it (this is the owner's directive, mechanized).
  5. **Familiar-surface test** — it maps to a surface in the locked working set (doc · board ·
     PR-thread/report · investigation ledger · notebook+chart · memo+timebox), or it raises an
     explicit new-surface flag for 2b/Phase 3 (never a silent invention).
- **Decide loop vs progress per family**, from evidence not symmetry: e.g., debug is expected
  to confirm as a loop (hypothesis↔experiment↔observation), feature as linear-but-re-entrant,
  spike as a single timebox, data-analysis likely an inner transform↔visualize loop inside a
  linear question→communicate frame — but the *research decides*; do not force the expected
  answer. Record which steps the loop iterates over (this feeds the `iter` counter semantics
  from Phase 1's debug spine stub).
- **Enforce prototype renderability constraints** (these are spine-band realities, not taste):
  4–7 steps per family; labels that fit a segment bar (≤ ~18 chars, with an optional short
  variant if the honest practitioner name is longer); each step owns ≥1 artifact (canvas
  anatomy); E1–E5 each get a named home step in their family.
- **Check shape compatibility:** confirm each derived spine still fits its locked shape variant
  (segments / loop band / timebox meter / pipeline DAG). If research genuinely contradicts a
  shape (e.g., spike turns out to need visible sub-steps, not just a meter), do NOT redesign —
  record a flag for the "Suggested Revisions" channel and proceed with the best fit.

**Design review:**
- **Naming convention:** step ids `<family>-NN` (`feat-01`, `dbg-01`, `spk-01`, `data-01`);
  labels Title Case. Family keys remain exactly `feature | debug | spike | data` (matches
  Phase 1 `appState.family` values — `data`, not `analysis`).
- **Anchoring bias** is the top failure mode of this sub-phase; the derive-first protocol above
  is the mitigation — verify the ledger shows derivation preceded comparison.
- **Asymmetry is a feature:** if families land on different step counts and different loop
  shapes, that is SC-005 working. Reject any pressure to make the four spines symmetric.

## Sub-phase 2c.3: Canonical Stage-Model Note, Encoding Contract & Self-Evaluation Gate

**Outcome:** The stage-model note exists at
`docs/plan/product-revamp-diecast-stage-models.md` as the single canonical per-family stage
definition: four spines with per-step surface mappings and references, a paste-ready
`stageModels` JSON block whose shape 2a can drop into the org data, the dropped-placeholder
ledger, and a written self-evaluation that replaces the owner sign-off gate (per the
full-autonomy run configuration). Phases 3–4 and 2a consume this note; nothing else needs
re-reading to build the spines.

**Dependencies:** Sub-phase 2c.2.

**Estimated effort:** 0.5 session.

**Verification:**
- Note exists at the path above with all sections listed below.
- The `stageModels` JSON block **parses** (paste into `node -e` or `jq` to confirm) and is
  plain-JSON (no functions — `file://` classic-script constraint).
- Every step has: id, label (+ shortLabel if >18 chars), `does` one-liner, `surface` from the
  working set, `surfaceWhy` one-liner, `artifacts` (≥1), `refs` (≥2 keys into the references
  table).
- E1–E5 each appear as an `evidence` home-step annotation in the right family.
- The self-evaluation table covers every step of all four spines with all five rubric marks,
  and ends in an explicit per-family verdict.
- A grep of the note shows the canonical family keys (`feature|debug|spike|data`) and no stray
  vocabulary drift (e.g., "bug-fix family", "analysis family" as keys).

Key activities:

- **Write the note** with this structure: (1) TL;DR — the four spines at a glance; (2) per
  family: the spine table, loop/progress semantics, evidence home steps, surface mappings with
  rationale + refs; (3) the dropped-placeholder ledger; (4) the references table (stable keys →
  full citation); (5) the `stageModels` encoding block; (6) the self-evaluation; (7) hand-off
  notes to 2a / 2b / Phase 3.
- **Author the encoding contract** (the 2a coordination point). Canonical rich data lives in
  the org data; `appState.spines` keeps its Phase 1 key shape with labels derived, not duplicated:

  ```js
  // org data (window.ORG.stageModels) — canonical, authored by 2c, encoded by 2a
  stageModels: {
    feature: {
      shape: 'segments', progression: 'linear-reentrant',   // illustrative values
      steps: [
        { id: 'feat-01', label: '…', shortLabel: '…',        // shortLabel optional
          does: 'one-line practitioner description',
          surface: 'doc',  surfaceWhy: 'one-line rationale',
          artifacts: ['…'], refs: ['shape-up'], evidence: null },
        // … 4–7 steps; exactly one step in the family carries evidence: 'E1'
      ]
    },
    debug: { shape: 'loop', loop: { over: ['dbg-02','dbg-03','dbg-04'], budget: 3 }, steps: [/*…*/] },
    spike: { shape: 'timebox', timebox: { budget: '3h' }, steps: [/*…*/] },
    data:  { shape: 'pipeline', steps: [/*…*/] },
  }
  // appState.spines.<family> (Phase 1 contract, unrenamed):
  //   { placeholder: false, shape: stageModels.<f>.shape,
  //     steps: stageModels.<f>.steps.map(s => s.shortLabel ?? s.label), current, iter? }
  ```

  The block above fixes the **shape**; the step *content* is 2c.2's derived output. Field names
  here are the contract — 2a must not rename them, and may extend.
- **Write the self-evaluation gate** (replaces the human sign-off per run config): the full
  rubric table from 2c.2 rendered in the note, plus a per-family verdict paragraph answering
  "would a top practitioner in this category recognize this as their actual workflow?" with the
  strongest supporting reference and the weakest step named honestly. The parent orchestrator
  accepts on all-pass; any fail loops once through 2c.2 for that family.
- **Write the hand-off notes:** 2c (this phase, final step — runs after 2a.1's generator
  exists): edit the generator's stage-model section in `prototype/data/_build/generate-org.mjs`
  with the derived vocabulary and re-emit `org.js` per 2a's "2c: rewrite ONLY `stageModels`"
  instructions; this flips `placeholder` to `false` and re-runs the invariant gate. If 2a has
  not yet landed the generator when 2c.3 completes, the encoding step parks until 2a.1 and
  MUST complete before Phase 3 dispatch. `appState.spines` derivation stays in the render
  layer. *(Ownership corrected by reconciliation F1, 2026-06-12 — was "2a — paste
  stageModels into the org data".)* 2b — confirm
  the four spine variants against the derived shapes (plus any new-surface flags); Phase 3 —
  remove the PLACEHOLDER watermark when rendering from `stageModels`.
- **Append ~10–20 lines to
  `docs/plan/product-revamp-diecast-decisions-so-far.md`** (Phase 2c section): the four spine
  step-label lists, the `stageModels` field contract, and any flags — so 2a/2b/3 planning and
  execution children adopt them without re-reading the full note.

**Design review:**
- **Spec consistency:** FR-020 — greenfield; no cast-server specs govern this deliverable; no
  `/cast-update-spec` action (the stage-model note itself is the canonical definition for the
  prototype's scope).
- **Phase 1 contract safety:** `appState.spines` keys are extended, never renamed; `steps`
  stays `string[]` at appState level (rich objects live only in `stageModels`). This avoids
  breaking Phase 1's render and morph code.
- **Drift guard:** the note is the *single* source for stage vocabulary — Phase 3/4 plans must
  cite it, not re-derive. The decisions-so-far append is the enforcement vehicle.

## Build Order

```
Sub-phase 2c.1 ──► Sub-phase 2c.2 ──► Sub-phase 2c.3
(evidence base,     (derivation +       (canonical note + JSON
 4 parallel scans)   pressure-test)      contract + self-eval gate)
```

**Critical path:** 2c.1 → 2c.2 → 2c.3 (strictly sequential; within 2c.1 the four family scans
run in parallel). Total fits the 1–2-session budget.

## Design Review Flags

| Sub-phase | Flag | Action |
|-----------|------|--------|
| 2c.1 | Evidence base could skew to methodology texts (the exact owner-flagged failure) | Mandatory ≥1 hands-on practitioner account per family; source-quality marks |
| 2c.1 / 2c.2 | Anchoring on dropped placeholder steps | Placeholders banned as search seeds; derive-first-compare-after protocol + ledger |
| 2c.2 | Derived spine may contradict a locked 2b shape variant | Flag, don't redesign — record in Suggested Revisions channel, proceed with best fit |
| 2c.3 | `steps: string[]` (Phase 1) vs rich step objects | Resolved: rich data in `stageModels` (org data), appState keeps label arrays — no key renames |
| 2c.3 | Parallel 2a may freeze org data before 2c lands | `stageModels` field contract published in this plan (above) + decisions-so-far append; 2a reserves the slot |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Research converges on tidy textbook phase models — owner's explicit failure mode | High | Rubric tests 1/2/4 (verb+artifact, ≥2-source recognition, tidy-label kill); practitioner-account source requirement |
| Honest practitioner steps don't fit the spine band (too many, too long) | Med | 4–7 step bound + ≤18-char shortLabel convention enforced in 2c.2, not discovered in Phase 3 |
| A derived spine breaks its locked shape variant (e.g., spike needs visible sub-steps) | Med | Shape-compatibility check in 2c.2; conditional revision flag to 2b rather than silent change |
| 2a freezes `org.json` without a `stageModels` slot (parallel-phase race) | Med | Field contract is in this plan now; 2c.3 appends it to decisions-so-far; 2a's plan reads both |
| Research timebox blowout (classic spike failure) | Med | Hard 60–75 min per family scan; `/cast-web-researcher` escalation only on thin results |
| Four spines drift symmetric (same count, same rhythm), muting SC-005 contrast | Low | "Asymmetry is a feature" review check in 2c.2; loop/progress decided per family from evidence |

## Open Questions

- None requiring user input. The one plan-reserved human gate for this phase (owner sign-off on
  the four spines) is delegated to the parent orchestrator under the approved full-autonomy run
  configuration and replaced by the written self-evaluation gate in Sub-phase 2c.3 (loop-once
  rework on failure). Content-level unknowns (the actual step vocabulary) are exactly what this
  phase's execution resolves — they are the work, not open questions.

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| `docs/specs/_registry.md` (checked) | All seven registered specs govern cast-server runtime/infrastructure | None — FR-020: prototype is greenfield; no spec applies, none contradicted, no `/cast-update-spec` step needed |

## Decisions Made Autonomously

1. **Skip the Step-10 auto-dispatch of `cast-plan-review`.** The run configuration in
   decisions-so-far is explicit: "Plan review: skipped — cross-phase reconciliation only."
   Adopted over the agent-default auto-review; reconciliation happens at the orchestrator.
2. **Stage-model note location:** `docs/plan/product-revamp-diecast-stage-models.md` —
   alongside decisions-so-far and the phase plans, since it is a design source-of-truth
   document consumed by later planning/execution, not shipped prototype data (which lives in
   `prototype/`).
3. **Encoding split:** rich step objects live in org data (`stageModels`); `appState.spines`
   keeps Phase 1's `steps: string[]` shape with labels derived via `map`. Rationale: Phase 1's
   contract says keys may be extended but not renamed, and its render already consumes label
   arrays — changing the element type would be a silent break.
4. **Family keys locked to `feature | debug | spike | data`** (not `analysis`), matching
   Phase 1's `appState.family` values and the morph op vocabulary (`morph:<family>`).
5. **Owner sign-off gate replaced by a written self-evaluation** (rubric table + per-family
   verdict, loop-once rework on failure), per the delegation context's explicit instruction
   that the gate is delegated to the orchestrator under full autonomy.
6. **Targeted scan over full `/cast-web-researcher` fan-out** as the default research method
   (escalation only on thin results). Rationale: HOLD SCOPE + the 1–2-session budget; the
   exploration already did 7-angle research, and 2c needs depth on one narrow question per
   family, not another broad survey.
7. **Step-count bound 4–7 and ≤18-char shortLabel convention** — not in any prior artifact;
   derived from spine-band renderability (1B segment bar) and the Phase 1 placeholder spines
   (5 and 4 steps). Honest longer names keep their full form in `label`; the band renders
   `shortLabel`.
8. **Practicality rubric (the five tests)** authored here to mechanize the owner's
   "top practitioner would recognize this" directive into checkable criteria — the directive
   itself gave the test, this plan makes it gateable.
9. **Seed reference lists per family** (Shape Up, Agans/Zeller/Evans, XP spikes/ADR, R4DS/
   notebook practice) are starting points only, marked as validate-extend-or-replace, kept out
   of the derivation step to respect the anti-anchoring protocol.

## Suggested Revisions to Prior Sub-Phases

- **None required.** Phase 1's contracts accommodate this phase as-is (decision #3 resolves
  the only tension — `steps` element type — without touching Phase 1).
- **Conditional flag to Phase 2b (not a revision yet):** if 2c.2's shape-compatibility check
  finds a derived spine that genuinely contradicts its locked variant (segments / loop band /
  timebox meter / pipeline DAG), the stage-model note will carry a "spine-variant revision
  proposed" flag for 2b/Phase 3 reconciliation. Until evidence forces it, the four locked
  variants stand.
- **Note to Phase 2a (coordination, not revision):** reserve a `stageModels` top-level slot in
  the org data using the field contract in Sub-phase 2c.3; do not freeze `org.json` step
  vocabulary from the Phase 1 placeholders.
