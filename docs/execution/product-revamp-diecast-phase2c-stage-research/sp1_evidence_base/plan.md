# Sub-phase 2c.1: Practitioner Evidence Base — Mine + Targeted Scan (×4 families)

> **Pre-requisite:** Read `docs/execution/product-revamp-diecast-phase2c-stage-research/_shared_context.md`
> before starting. It carries the FULL-AUTONOMY directive, the NO-TESTS rule, the
> derive-first/anti-anchoring protocol, the practitioner-account source requirement, and the
> family keys (`feature|debug|spike|data`).

## Objective

Build a logged, cited **evidence base** for each of the four families — **3–6 practitioner-grade
references per family** with extracted candidate steps and supporting quotes — so that the spine
derivation in sp2 *cites sources instead of inventing labels*. This sub-phase gathers raw
material only; it does **not** derive spines, score steps, or write the canonical note. Its
single deliverable is `sp1_evidence_base/evidence-base.md`.

## Dependencies

- **Requires completed:** None. (Phase 1's `appState.spines` contract and the locked shape
  variants are already absorbed into `_shared_context.md`.)
- **Assumed state:** the exploration reference set exists under the goal artifacts dir
  (`/data/workspace/diecast/goals/product-revamp-diecast/exploration/`). No prototype code is
  touched by this sub-phase.

## Scope

**In scope:**
- Mining the exploration reference set for practitioner-workflow claims (cheap, pre-curated).
- Four timeboxed (~60–75 min each) targeted online scans — one per family — that can run in
  parallel (they touch independent reference material; they all append to disjoint sections of
  one scratch file).
- Logging each reference with: source/author named, the concrete candidate steps it evidences
  (with a short quote/paraphrase), and a source-quality mark.

**Out of scope (do NOT do these):**
- **Deriving spines, choosing step ids, or scoring against the rubric** — that is sp2.
- **Writing `docs/plan/product-revamp-diecast-stage-models.md`** — that is sp3.
- **Touching `prototype/`** — no code in this phase at all.
- **Using the dropped placeholder steps as search queries or candidate lists** — banned by the
  anti-anchoring protocol. Gather fresh; comparison happens only in sp2.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `docs/execution/product-revamp-diecast-phase2c-stage-research/sp1_evidence_base/evidence-base.md` | Create | Does not exist |

## Detailed Steps

### Step 1.1: Mine the exploration reference set first (cheap, already curated)
Deep-read, under `/data/workspace/diecast/goals/product-revamp-diecast/`:
- `exploration/research/03-family-canvases-evidence.ai.md` — §"Expert-Practitioner Insights",
  §"The Four Family Blueprints", and its Consolidated Sources / Reference-Link Map.
- Skim `exploration/research/05-decisions-autonomy.ai.md` Lens 1 (how decisions punctuate
  workflows).

Extract **every practitioner-workflow claim relevant to stage vocabulary**, each with its
citation. These are free evidence — log them before spending any online-scan timebox.

### Step 1.2: Run four targeted online scans (parallel; ~60–75 min each, HARD timebox)
Use `WebSearch` / `WebFetch` directly. **Seed targets are starting points — validate, extend, or
replace; they are not the answer.** Do NOT search for the dropped placeholder vocabulary.

- **`feature` (feature-builders):** Shape Up (Basecamp — shaping/betting/building, vertical
  slices); the Linear Method (project briefs, scope cuts); design-engineering prototype-first
  practice (Vercel/Figma design-eng writing); eng design-doc/RFC culture (Stripe/Google);
  trunk-based development + feature flags + incremental rollout/verification (DORA, "ship small").
- **`debug` (debuggers):** David Agans *Debugging: The 9 Indispensable Rules* ("make it fail",
  "quit thinking and look"); Andreas Zeller scientific debugging (hypothesis → prediction →
  experiment → observation); Julia Evans debugging zines/posts (practitioner-loved, concrete);
  `git bisect` / minimal-repro culture (SSCCE); SRE incident response + blameless postmortems.
- **`spike` (spike-runners):** XP spike solutions (C2 wiki / Extreme Programming sources);
  timeboxed research practice; ADR practice (Nygard) as the *consumption* end of a spike;
  one-pager findings-memo culture.
- **`data` (data analysts):** Hadley Wickham import→tidy→transform/visualise/model→communicate
  (R4DS — a real, widely-recognized practitioner workflow); notebook-to-report practice
  (Hex/Deepnote/Observable); analytics-engineering source-validation (dbt culture); published
  "how I actually analyze data" accounts (sanity checks, data-cleaning reality).

### Step 1.3: Apply the source-quality filter as you log
Prefer practitioner-authored books/posts/talks describing their *own* process. Reject SEO
listicles and consultant lifecycle diagrams. Mark each reference one of:
`practitioner-account` · `tool-documented-workflow` · `methodology-text`.

### Step 1.4: Escalation hatch (bounded — do NOT run by default)
If and only if a family's scan comes back **thin (<3 quality references)**:
- → **Delegate: `/cast-web-researcher`** — ONE targeted dispatch scoped to *that single family's*
  practitioner workflow, passing the seed list above as starting context **and the FULL-AUTONOMY
  directive verbatim**.
- Then: **Review the `/cast-web-researcher` output for source quality** (practitioner-account vs
  methodology-text) before admitting any reference to the evidence base.
- HOLD SCOPE: the targeted scan should suffice for most families. Do not fan out by default.

### Step 1.5: Write `evidence-base.md`
One section per family. Per reference: a stable key (e.g. `shape-up`, `agans`, `zeller`,
`julia-evans`, `r4ds`), source/author, type mark, the concrete candidate steps it evidences, and
a short quote or paraphrase per step. Keep these keys — sp2/sp3 cite them in `refs[]`.

## Verification

> **NO TESTS.** Verification here is **manual file-inspection** of `evidence-base.md` only.

### Manual Checks
- Open `sp1_evidence_base/evidence-base.md`. For **each** of `feature`, `debug`, `spike`, `data`:
  - Count references: **≥3** present, each with author/source **named**.
  - Confirm **≥1 reference marked `practitioner-account`** (a practitioner describing their own
    process — not a methodology textbook or consulting framework). **This check is mandatory.**
  - Confirm each reference lists the **concrete steps it evidences** with a short quote/paraphrase.
  - Confirm each reference carries a **source-quality mark**
    (`practitioner-account` / `tool-documented-workflow` / `methodology-text`).
- Grep the file for the dropped placeholder vocabulary (e.g. `RCA`, `prototype-with-UI-choices`,
  `eng design` as a *step label* used as a search seed): confirm they appear **only** as
  evidence-derived findings if at all, **never** as the query that produced a result. (The
  anti-anchoring audit; the real proof lands in sp2's ledger.)

### Success Criteria
- [ ] `evidence-base.md` exists with one section per family (`feature|debug|spike|data`).
- [ ] Every family has **≥3** named references.
- [ ] Every family has **≥1** `practitioner-account` reference.
- [ ] Every reference has a stable key, a type mark, and ≥1 evidenced step with a quote/paraphrase.
- [ ] No placeholder step was used as a search seed (anti-anchoring honored).
- [ ] No spines derived, no rubric scoring, no canonical note written (that is sp2/sp3).

## Execution Notes
- **Timebox is hard.** 60–75 min per family scan — classic spike failure is the blowout. When a
  family hits ≥3 quality refs with evidenced steps, **stop scanning it**.
- The four scans are **independent** — you may interleave them, but each appends to its own
  family section. No two scans contend for the same text.
- **Source quality is the whole game.** The owner's directive fails precisely when this base is
  built from methodology texts. The `practitioner-account` requirement is the gate, not advice.
- Keep reference **keys stable and short** — sp2 and sp3 cite them by key in `refs[]`, and the
  encoding block's `refs` arrays become part of the org data.
- **Spec-linked files:** none. No spec covers this sub-phase (FR-020 greenfield).
- **FULL AUTONOMY:** never pause for input; if you delegate to `/cast-web-researcher`, pass the
  autonomy directive down verbatim.
