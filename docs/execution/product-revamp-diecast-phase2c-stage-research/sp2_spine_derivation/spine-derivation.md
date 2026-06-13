# Spine Derivation & Practicality Pressure-Test — Phase 2c sub-phase 2c.2

> **Deliverable of sp2.** Four derived candidate spines (`feature · debug · spike · data`),
> each 4–7 steps, every step scored against the five-test practicality rubric, loop-vs-progress
> decided per family from evidence, every step mapped to a locked working surface and the sp1
> reference(s) it was drawn from. The dropped exploration placeholders **and** the Phase 1/2a
> watermarked stub labels are dispositioned in a single cross-family ledger.
>
> **This sub-phase does NOT** write the canonical note, the paste-ready JSON block, or append to
> decisions-so-far — those are sp3. It does not touch `prototype/`.
>
> **Author:** cast-subphase-runner (run_20260611_223338_877523) · **Date:** 2026-06-12 ·
> **Input:** `sp1_evidence_base/evidence-base.md` (21 refs / 4 families, ≥1 practitioner account each) ·
> **Run mode:** FULL AUTONOMY — every judgment call resolved and documented inline; no user prompts.

---

## Anti-anchoring protocol — order of operations (audited)

The mandatory order is **derive-first, compare-after**. Concretely, the work in this file was
performed in this sequence and is laid out in this sequence:

1. **§1 Derived spines** — drafted **purely from the sp1 evidence keys**, with zero reference to
   the dropped exploration placeholders or the Phase 1/2a stub labels. Each step cites only sp1
   reference keys.
2. **§2 Five-test rubric scorecards** — every candidate step scored; failures renamed/dropped.
3. **§3 Loop-vs-progress calls** — decided per family from evidence, not symmetry.
4. **§4 Renderability + E1–E5 home-step map** — bounds enforced after derivation.
5. **§5 Dropped-placeholder ledger** — **only now** the derived spines are diffed against the
   dropped exploration placeholders (feature 3 + debug 5) **and** the Phase 1/2a watermarked stub
   labels (feat/dbg/spk/data, 18 stub labels total). The ledger existing — and showing the derived
   step already in hand before each placeholder was looked at — is the audited proof the protocol
   held.
6. **§6 Shape-compatibility check** — each spine validated against its locked 2b variant; genuine
   contradictions **flagged**, never redesigned.

Where a derived step happens to rhyme with a placeholder (e.g. debug "Reproduce Reliably" vs the
placeholder "repro"), the convergence is recorded in the ledger as **independent** — the step was
derived from ≥2 practitioner accounts (here `agans` + `julia-evans`), not seeded by the placeholder.

---

## §1 — Derived candidate spines (derived from sp1 evidence only)

Asymmetry is intended (SC-005): **feature 5 · debug 5 · spike 4 · data 5** steps, with three
different progression shapes. No family was padded or trimmed to match another.

### 1.1 `feature` — shape `segments`, progression `linear-reentrant`

A known-path build: a linear backbone from a shaped problem to verified-shipped work, re-entrant
because shipping continuously feeds back into design/build.

| id | label (shortLabel) | what the practitioner actually does | owned artifact(s) | surface · why | refs |
|----|--------------------|-------------------------------------|-------------------|---------------|------|
| feat-01 | Shape the Problem | Define the problem + appetite + a rough solution + named rabbit-holes; write it up as a pitch/brief before betting | pitch/brief (appetite · rough solution · rabbit-holes) | `doc` · the shaped problem is a written artifact reviewed before commitment | `shape-up`, `linear-method`, `design-docs-google` |
| feat-02 | Commit & Scope | Place a fixed-appetite bet on the pitch, then break the committed work into shippable issues | committed scope / issue board | `board/ticket list` · the bet + scoped issues live on a ticket board | `shape-up`, `linear-method` |
| feat-03 | Design the Approach (Design Approach) | Write a design doc / RFC capturing the implementation strategy, alternatives, and trade-offs; resolve it in review threads | design doc (alternatives + trade-offs) + review thread | `doc` · the design and its review are a document discussion, the org's decision memory | `design-docs-google`, `linear-method` |
| feat-04 | Build & Ship | Build in vertical slices and ship continuously within the fixed timebox/cycle | shipped vertical slice / merged PR | `PR-thread/report` · slices land as reviewed, merged PRs | `shape-up`, `linear-method` |
| feat-05 | Show It's Done | Demonstrate completion via the diff plus an acceptance-evidence bundle (screenshots / proof shots / test summary) | acceptance-evidence bundle (diff + screenshots + summary) — **E1 home** | `PR-thread/report` · "done" is shown on the PR/report as evidence, not asserted | `linear-method`, `proofshot`, `devin-cu` |

### 1.2 `debug` — shape `loop`

"Where is this?" is unknown until found — a search, not a march. A reliable repro opens the loop;
the loop iterates hypothesis → experiment → confirm/refute until the root cause is confirmed; the
spine exits by proving the fix red→green.

| id | label (shortLabel) | what the practitioner actually does | owned artifact(s) | surface · why | refs |
|----|--------------------|-------------------------------------|-------------------|---------------|------|
| dbg-01 | Reproduce Reliably | Move from "saw it a few times" to an on-demand, consistent reproduction (special care for intermittents) | reliable reproduction (recorded repro steps) | `investigation ledger` · the repro recipe is the first ledger entry | `agans`, `julia-evans` |
| dbg-02 | Form a Hypothesis | Invent a falsifiable hypothesis for the failure cause, consistent with the observations so far | hypothesis entry (the "accusation") | `investigation ledger` · each candidate cause is logged in the case file | `zeller`, `uxmag-detective`, `julia-evans` |
| dbg-03 | Run an Experiment | Quit thinking and look: change one thing / bisect, observe actual behavior with tools, get data | experiment result + trace/instrumentation | `investigation ledger` · the experiment and what it showed are logged | `agans`, `zeller`, `julia-evans` |
| dbg-04 | Log Confirm/Refute | Record prediction-vs-observed per hypothesis; mark confirmed/refuted; a refuted prediction spawns the next hypothesis | confirm/refute evidence ledger — **E2 home** | `investigation ledger` · the confirmed/refuted ledger is the loop's memory | `hypothesizer`, `uxmag-detective`, `agans` |
| dbg-05 | Prove the Fix | Prove the fix by making the failure recur, then disappear — a red→green repro (fails, then the same case passes) | red→green repro (failing → passing case) — **E3 home** | `PR-thread/report` · the proof lands on the fix PR/report | `agans`, `undo-replay` |

### 1.3 `spike` — shape `timebox`

A single timeboxed pass whose deliverable is a *decision input*, not shippable code. The timebox is
the dominant status element (the budget meter wraps all four steps).

| id | label (shortLabel) | what the practitioner actually does | owned artifact(s) | surface · why | refs |
|----|--------------------|-------------------------------------|-------------------|---------------|------|
| spk-01 | Frame the Question | Identify the single riskiest unknown and pose it as one answerable technical question | risk question memo | `memo+timebox` · the question opens the spike memo under its budget | `xp-spike`, `mike-bowler` |
| spk-02 | Probe Options | Build quick, throwaway probes to answer the question — quick-and-dirty, explicitly disposable | probes-tried list (throwaway) | `memo+timebox` · probe attempts are logged in the memo, code is dropped | `xp-spike`, `mike-bowler` |
| spk-03 | Evaluate Findings | Evaluate the probes; keep the learning, discard the code; at any point decide "done enough" | findings notes | `memo+timebox` · findings accrue in the memo against the burning budget | `xp-spike`, `agilemania-spike` |
| spk-04 | Land the Verdict | Write a one-line answer and link it to the downstream decision it informs (with a revisit-if trip-wire) | verdict card (`spike_ref` + `revisit_if`) — **E4 home** | `memo+timebox` · the verdict closes the memo and points at its decision record | `mike-bowler`, `agilemania-spike`, `adr-nygard` |

### 1.4 `data` — shape `pipeline`

A position in a pipeline, not a loop or a path. The frame is linear (sources → answer); an inner
transform↔visualize↔model explore loop lives **inside** one step (data-04), it is **not** a
top-level loop band (see §6).

| id | label (shortLabel) | what the practitioner actually does | owned artifact(s) | surface · why | refs |
|----|--------------------|-------------------------------------|-------------------|---------------|------|
| data-01 | Import Sources | Pull the sources (file / DB / API) that bear on the question into a working frame | loaded dataset | `notebook+chart` · ingestion happens in the analysis notebook | `r4ds`, `dbt-analyst` |
| data-02 | Tidy & Validate | Tidy to one-variable-per-column / one-observation-per-row, then sanity-check: "are you telling me the truth?" — cross-examine outliers before trusting | cleaned + validated frame (sanity notes) | `notebook+chart` · cleaning and the sanity checks are notebook cells/charts | `r4ds`, `data-sanity`, `dbt-analyst` |
| data-03 | Transform / Wrangle (Transform) | Narrow observations, create new variables, compute summary statistics | derived variables / summary tables | `notebook+chart` · transforms are notebook cells | `r4ds`, `dbt-analyst` |
| data-04 | Explore (Viz↔Model) (Explore) | Iterate visualize ↔ model many times to find the answer; disposable charts also catch problems early (visualize-to-validate) | exploratory charts + candidate models | `notebook+chart` · the explore loop is interactive charting in the notebook | `r4ds`, `looks-good-correll` |
| data-05 | Publish + Provenance (Publish) | Publish a clean narrative report (viz as the headline) distinct from the working notebook, with source/transform lineage exposed on demand | rendered report + provenance drill-in — **E5 home** | `PR-thread/report` · the published report is the shareable deliverable | `r4ds`, `hex-deepnote`, `atlan-provenance` |

---

## §2 — Five-test practicality rubric scorecards

Tests: **(1) Verb+artifact** · **(2) Recognition** (≥2 independent sp1 sources, both cited) ·
**(3) Hole** (a top practitioner notices its absence) · **(4) Tidy-label kill** (PASS = it lives in
practitioner accounts, not only textbooks) · **(5) Familiar-surface** (maps to the locked set).
**A step ships only if all five PASS.** Renames/drops are noted.

### 2.1 `feature`

| step | 1 Verb+artifact | 2 Recognition (≥2 cited) | 3 Hole | 4 Tidy-label kill | 5 Surface | verdict |
|------|----|----|----|----|----|----|
| feat-01 Shape the Problem | PASS — produces a pitch/brief | PASS — `shape-up` (Shape) + `linear-method` (write brief/spec) [+`design-docs-google`] | PASS — building without a shaped problem is the classic miss | PASS — first-person practitioner method | PASS — `doc` | **SHIP** |
| feat-02 Commit & Scope | PASS — produces a committed scope / issue board | PASS — `shape-up` (Bet, fixed appetite) + `linear-method` (scope down into issues) | PASS — un-bet, un-scoped work has no boundary | PASS — practitioner accounts | PASS — `board/ticket list` | **SHIP** |
| feat-03 Design the Approach | PASS — produces a design doc/RFC | PASS — `design-docs-google` (design doc) + `linear-method` (brief's "how") [+`shape-up` rough solution] | PASS — top eng would notice no design record | PASS — first-person Google practice | PASS — `doc` | **SHIP** |
| feat-04 Build & Ship | PASS — produces merged PRs / shipped slices | PASS — `shape-up` (build in fixed timebox) + `linear-method` (build in cycles, ship continuously) | PASS — obviously load-bearing | PASS — practitioner accounts | PASS — `PR-thread/report` | **SHIP** |
| feat-05 Show It's Done | PASS — produces an acceptance-evidence bundle | PASS — `linear-method` (show the diff) + `proofshot` (proof bundle) [+`devin-cu` checkpoint shots] | PASS — "done" asserted without evidence is the failure mode the family guards against | PASS — tool-documented + practitioner | PASS — `PR-thread/report` | **SHIP** |

### 2.2 `debug`

| step | 1 Verb+artifact | 2 Recognition (≥2 cited) | 3 Hole | 4 Tidy-label kill | 5 Surface | verdict |
|------|----|----|----|----|----|----|
| dbg-01 Reproduce Reliably | PASS — produces an on-demand repro | PASS — `agans` (make it fail) + `julia-evans` (reproduce reliably) | PASS — can't debug what you can't trigger | PASS — two practitioner accounts | PASS — `investigation ledger` | **SHIP** |
| dbg-02 Form a Hypothesis | PASS — produces a logged hypothesis | PASS — `zeller` (invent hypothesis) + `uxmag-detective` (accusation) [+`julia-evans`] | PASS — guessing without a stated hypothesis can't be tested | PASS — practitioner + applied method | PASS — `investigation ledger` | **SHIP** |
| dbg-03 Run an Experiment | PASS — produces an experiment result + trace | PASS — `agans` (quit thinking and look / change one thing) + `zeller` (test by experiment) [+`julia-evans` observe with tools] | PASS — untested hypotheses are just opinions | PASS — practitioner accounts | PASS — `investigation ledger` | **SHIP** |
| dbg-04 Log Confirm/Refute | PASS — produces a confirm/refute ledger | PASS — `hypothesizer` (confirmed/refuted ledger) + `uxmag-detective` (confirmed observations) [+`agans` audit trail] | PASS — without it the loop loses its memory and re-tests dead hypotheses | PASS — tool + practitioner | PASS — `investigation ledger` | **SHIP** |
| dbg-05 Prove the Fix | PASS — produces a red→green repro | PASS — `agans` ("if you didn't fix it, it ain't fixed") + `undo-replay` (red→green) | PASS — a "fix" with no proof is the family's signature failure | PASS — practitioner + tool | PASS — `PR-thread/report` | **SHIP** |

### 2.3 `spike`

| step | 1 Verb+artifact | 2 Recognition (≥2 cited) | 3 Hole | 4 Tidy-label kill | 5 Surface | verdict |
|------|----|----|----|----|----|----|
| spk-01 Frame the Question | PASS — produces a risk-question memo | PASS — `xp-spike` (riskiest unknown / WorstThingsFirst) + `mike-bowler` (one answerable question) | PASS — an unscoped spike is the thing both accounts warn against | PASS — two practitioner accounts | PASS — `memo+timebox` | **SHIP** |
| spk-02 Probe Options | PASS — produces a throwaway probes-tried list | PASS — `xp-spike` (throwaway probe) + `mike-bowler` (throwaway code) | PASS — no probe, no learning | PASS — practitioner accounts | PASS — `memo+timebox` | **SHIP** |
| spk-03 Evaluate Findings | PASS — produces findings notes | PASS — `xp-spike` (evaluate → conclude) + `agilemania-spike` (decide "done enough", document outcome) | PASS — un-evaluated probes leave no learning to keep | PASS — practitioner + method | PASS — `memo+timebox` | **SHIP** |
| spk-04 Land the Verdict | PASS — produces a verdict card w/ `spike_ref` + `revisit_if` | PASS — `mike-bowler` (feeds a decision) + `agilemania-spike` (traceable finding↔decision link) [+`adr-nygard` revisit-if] | PASS — a spike whose answer never reaches a decision was wasted | PASS — practitioner + method | PASS — `memo+timebox` | **SHIP** |

### 2.4 `data`

| step | 1 Verb+artifact | 2 Recognition (≥2 cited) | 3 Hole | 4 Tidy-label kill | 5 Surface | verdict |
|------|----|----|----|----|----|----|
| data-01 Import Sources | PASS — produces a loaded dataset | PASS — `r4ds` (import) + `dbt-analyst` (pull/analyze data) | PASS — no sources, no analysis | PASS — practitioner + tool | PASS — `notebook+chart` | **SHIP** |
| data-02 Tidy & Validate | PASS — produces a cleaned + validated frame | PASS — `r4ds` (tidy) + `data-sanity` (sanity-check before trusting) [+`dbt-analyst` validate source] | PASS — analysts call the un-tidied/un-checked frame the "messiest but most critical" gap | PASS — two practitioner accounts name it explicitly | PASS — `notebook+chart` | **SHIP** |
| data-03 Transform / Wrangle | PASS — produces derived variables / summary tables | PASS — `r4ds` (transform) + `dbt-analyst` (modeling / one-off queries) | PASS — raw tidy data rarely answers the question directly | PASS — practitioner + tool | PASS — `notebook+chart` | **SHIP** |
| data-04 Explore (Viz↔Model) | PASS — produces exploratory charts + candidate models | PASS — `r4ds` (visualize↔model iterate many times) + `looks-good-correll` (visualize-to-validate) | PASS — skipping explore ships unexamined numbers | PASS — two practitioner accounts | PASS — `notebook+chart` | **SHIP** |
| data-05 Publish + Provenance | PASS — produces a rendered report + provenance drill-in | PASS — `r4ds` (communicate) + `hex-deepnote` (report distinct from notebook) [+`atlan-provenance` lineage] | PASS — an answer no one can read or trust is no answer | PASS — practitioner + tool | PASS — `PR-thread/report` | **SHIP** |

**Rubric-driven drops/renames (steps that did NOT survive as standalone):**
- **`data` "Frame the Question" — DROPPED as a standalone step (Recognition fail).** Only
  `dbt-analyst` names a discrete "start with a stakeholder question" step; `r4ds` (the dominant
  practitioner workflow) begins at *import* and folds the question into the implicit setup. With <2
  independent practitioner accounts naming it as a *step*, it fails Recognition. The question is
  retained as the **pipeline's input precondition** (it defines data-05's answer), not a rendered
  step. Documented here so the rubric is visibly doing filtering work.
- All other candidate concepts surfaced in sp1 mapped cleanly onto a surviving step (e.g. debug
  "understand the system" / "read the map" was folded into dbg-01 Reproduce — on its own it fails
  Verb+artifact, producing only a mental model, and risks a tidy-label; the understanding it names
  is exercised in building the repro).

---

## §3 — Loop-vs-progress call, per family (from evidence, not symmetry)

| family | call | evidence | encoding |
|--------|------|----------|----------|
| `feature` | **Linear, re-entrant** (progress) | `shape-up` and `linear-method` describe a forward backbone (shape→bet→build→ship); `linear-method`'s "ship continuously… quick feedback loops" makes it re-entrant (ship can send you back to design/build), but there is no counted iteration band | `shape:'segments'`, `progression:'linear-reentrant'` |
| `debug` | **Loop** | `zeller` states the loop explicitly — observe → hypothesis → predict → experiment → observe, repeated until the cause is found; `uxmag-detective` and `julia-evans` both describe iterative evidence-gathering; a refuted prediction (`undo-replay`) spawns the next hypothesis | `shape:'loop'`, `loop:{ over:['dbg-02','dbg-03','dbg-04'], budget:3 }` — the loop iterates **hypothesis → experiment → confirm/refute**; dbg-01 (repro) opens it, dbg-05 (prove the fix) is the exit |
| `spike` | **Linear, single timeboxed pass** (progress) | `xp-spike` / `mike-bowler`: one short pass, probe → evaluate → drop the code, keep the learning; no iteration band — the *budget* is the dynamic element, not a repeat count | `shape:'timebox'`, `timebox:{ budget:'3h' }` (XP spikes are "typically hours"; both practitioner accounts insist on a strict, short, hours-scale box) |
| `data` | **Linear pipeline with an inner explore loop** | `r4ds` frames a linear pipeline (import→tidy→transform→visualize/model→communicate); the visualize↔model iteration ("iterate between them many times") is **internal to data-04**, not a top-level loop; the spine as a whole flows forward | `shape:'pipeline'` (no top-level `loop`; inner iteration lives inside data-04 — see §6) |

**Asymmetry is the design working (SC-005):** three different shapes, step counts 5/5/4/5, one
counted loop (debug), one budget meter (spike), one DAG (data), one segment bar (feature). No
family was reshaped toward the others.

---

## §4 — Renderability bounds + E1–E5 home-step map

**Bounds (all enforced):**
- **Step count 4–7:** feature 5 · debug 5 · spike 4 · data 5 — all in range. ✓
- **Labels ≤18 chars, else `shortLabel` ≤18:** longer labels carry a shortLabel (band renders the
  shortLabel):
  - `feat-03` "Design the Approach" (19) → `shortLabel:'Design Approach'` (15) ✓
  - `data-03` "Transform / Wrangle" (19) → `shortLabel:'Transform'` (9) ✓
  - `data-04` "Explore (Viz↔Model)" (>18 / non-ASCII glyph) → `shortLabel:'Explore'` (7) ✓
  - `data-05` "Publish + Provenance" (20) → `shortLabel:'Publish'` (7) ✓
  - All other labels ≤18 chars (e.g. `dbg-01` "Reproduce Reliably" = 18, `spk-01` "Frame the Question" = 18). ✓
- **Each step owns ≥1 concrete artifact:** verified in every row of §1 (artifact column non-empty). ✓

**E1–E5 home-step map (owner-blessed catalog; each gets exactly one home in the correct family):**

| evidence | treatment | family | home step |
|----------|-----------|--------|-----------|
| **E1** | acceptance panel | `feature` | **feat-05** (Show It's Done) |
| **E2** | confirm/refute ledger | `debug` | **dbg-04** (Log Confirm/Refute) |
| **E3** | red→green repro | `debug` | **dbg-05** (Prove the Fix) |
| **E4** | verdict card w/ `spike_ref` | `spike` | **spk-04** (Land the Verdict) |
| **E5** | rendered report + provenance | `data` | **data-05** (Publish + Provenance) |

All five homed; debug correctly hosts both E2 and E3 on distinct steps. ✓

---

## §5 — Dropped-placeholder ledger (compare-after — proof of derive-first ordering)

This ledger is written **after** §1–§4. For each placeholder it records the **already-derived**
step it maps to and why — demonstrating the derivation existed before the comparison. It covers
**both** sources of priors: (A) the dropped exploration placeholders (owner-directed drop:
feature 3 + debug 5), and (B) the Phase 1/2a watermarked stub labels in `generate-org.mjs`
(feature 5 + debug 4 + spike 4 + data 4 = 17 stub labels).

### A) Dropped exploration placeholders (owner directive — "those are not the right steps")

**feature** — placeholder chain *prototype-with-UI-choices → locked design → eng design*:

| placeholder | disposition | derived step it maps to | why |
|-------------|-------------|-------------------------|-----|
| prototype-with-UI-choices | **DROPPED** | (none — split across feat-01 / feat-03) | No practitioner account starts feature work from a UI prototype; `shape-up`/`linear-method`/`design-docs-google` all begin from a written brief, then a design doc. Tidy-label/illustrative guess — killed. |
| locked design | **RENAMED** | feat-03 Design the Approach | A design step is real (`design-docs-google` + `linear-method`), but practitioners describe a **reviewed, re-entrant** design doc, not a one-time "locked" gate. "Locked" framing dropped; the artifact survives. |
| eng design | **FOLDED** | feat-03 Design the Approach | Practitioners write **one** design doc covering implementation strategy + trade-offs; the placeholder's design/eng-design split is not evidenced. Merged. |

**debug** — placeholder chain *repro · RCA · evidence · fix · tests*:

| placeholder | disposition | derived step it maps to | why |
|-------------|-------------|-------------------------|-----|
| repro | **SURVIVES (independent)** | dbg-01 Reproduce Reliably | Convergence is **independent** — dbg-01 was derived from `agans` (make it fail) + `julia-evans` (reproduce reliably), not seeded by the placeholder. |
| RCA | **RENAMED → the loop** | dbg-02 → dbg-03 → dbg-04 | "RCA" is a tidy consulting label that names no practitioner action. Practitioners describe an **iterative hypothesis↔experiment↔confirm/refute loop** (`zeller`/`uxmag-detective`), so RCA is replaced by the loop body — tidy-label kill. |
| evidence | **RENAMED** | dbg-04 Log Confirm/Refute | Real, but vague. The evidenced artifact is a **confirm/refute ledger** (`hypothesizer` + `uxmag-detective`), which is E2's home. Renamed to the concrete artifact. |
| fix | **RENAMED** | dbg-05 Prove the Fix | Practitioners reject "fix" as the close — `agans` "if you didn't fix it, it ain't fixed". The step is **proving** the fix red→green (`undo-replay`), so "fix" is renamed accordingly. |
| tests | **DROPPED** | (none) | NO-TESTS rule. Independently, practitioners frame the close as a **red→green repro** (proof), already homed at dbg-05 (E3) — not a "write tests" step. Killed. |

### B) Phase 1 / 2a watermarked stub labels (`prototype/data/_build/generate-org.mjs`)

These were Phase-1 placeholders (each carries a `[2c]`/PLACEHOLDER watermark in `org.js`); 2c owns
the real vocabulary that replaces them. The derived spine **flips `placeholder:true → false`**.

| family | stub labels (Phase 1/2a) | derived labels (sp2) | net change |
|--------|--------------------------|----------------------|------------|
| feature | requirements · plan · tickets · execution · review | Shape the Problem · Commit & Scope · Design the Approach · Build & Ship · Show It's Done | same count (5); stubs were generic SDLC nouns → replaced with practitioner verbs+artifacts; ids feat-01..05 preserved |
| debug | reproduce · hypothesize · experiment · fix | Reproduce Reliably · Form a Hypothesis · Run an Experiment · Log Confirm/Refute · Prove the Fix | **4 → 5 steps**: the stub's single "fix" splits into **dbg-04 Log Confirm/Refute (E2)** + **dbg-05 Prove the Fix (E3)**, giving both debug evidence treatments distinct homes. New id **dbg-05**. |
| spike | frame · probe · measure · verdict | Frame the Question · Probe Options · Evaluate Findings · Land the Verdict | same count (4); "measure" → "Evaluate Findings" (evaluation is the evidenced act, not just measurement); ids spk-01..04 preserved |
| data | extract · transform · analyze · report | Import Sources · Tidy & Validate · Transform / Wrangle · Explore (Viz↔Model) · Publish + Provenance | **4 → 5 steps**: stub "extract→transform→analyze→report" lacked an explicit **Tidy & Validate** step that two practitioner accounts (`r4ds` + `data-sanity`) insist on; inserted as data-02. "analyze" → "Explore (Viz↔Model)"; "report" → "Publish + Provenance" (E5). New id **data-05**. |

> **ID-collision note for sp3/sp4:** the derived **dbg-05** and **data-05** are *new* step ids not
> present in the current 2a stub block; the existing stub `dbg-04 = fix` is **re-tasked** to
> `Log Confirm/Refute` and "Prove the Fix" becomes the new `dbg-05`. sp4's generator edit must add
> these ids when it rewrites `stageModels` (this is the expected, owner-sanctioned `stageModels`
> rewrite — the one standing exception to 2a's post-freeze policy). Not a contradiction; flagged so
> sp4 doesn't treat the extra ids as drift.

---

## §6 — Shape-compatibility check (flag, don't redesign)

| family | locked 2b variant | derived spine fits? | action |
|--------|-------------------|---------------------|--------|
| `feature` | `segments` (labeled segment bar, `linear-reentrant`) | **Yes** — 5 linear segments, re-entrant | none |
| `debug` | `loop` (staged band + ↺ iter counter, `loop:{over,budget}`) | **Yes** — loop over dbg-02..04, budget 3; dbg-01 opens / dbg-05 exits | none |
| `spike` | `timebox` (budget meter) | **Partial — FLAG raised** (see below) | proceed with `timebox`; revision flag for sp3 |
| `data` | `pipeline` (DAG) | **Yes** — linear forward pipeline; inner explore loop is internal to data-04, not a top-level loop | none (resolves sp1's open question) |

### Flags for sp3's "Suggested Revisions" channel

- **FLAG (spike-timebox sub-step rendering) — `spine-variant revision proposed`.** Evidence derives
  **four ordered sub-steps** for spike (Frame → Probe → Evaluate → Verdict), but 2b locked the
  variant as a **budget meter**. If the `timebox` band renders *only* a gauge with no sub-steps,
  the four derived steps have nowhere to show. **Proposed (do not redesign here):** the `timebox`
  band should render the four sub-steps **beneath** the budget meter (the meter is the wrapper /
  dominant status element, not the only element). Proceeding with `timebox` as the best fit; sp3
  carries this into the note's Suggested Revisions channel for 2b/Phase 3 to confirm.

- **RESOLVED (data inner loop) — no flag.** sp1 flagged that `data` shows an inner
  transform↔visualize↔model loop inside the linear `pipeline` frame and asked sp2 to decide whether
  it surfaces as a step or stays implicit. **Decision:** surface it as **one step (data-04 "Explore
  (Viz↔Model)")** whose label and `does` make the iteration explicit, while the **top-level shape
  stays `pipeline`** (no top-level `loop` band, no `loop.over`). This honors the locked variant and
  sp1's recommendation — the iteration is intra-step, not a spine-level loop. No
  `spine-variant revision proposed` flag raised for `data`.

---

## §7 — Handoff to sp3

sp3 composes the canonical note `docs/plan/product-revamp-diecast-stage-models.md` and the
paste-ready `stageModels` JSON block from §1 (step rows), §3 (shape/loop/timebox encodings), §4
(E-home map + shortLabels), and carries the two §6 entries into the note's Suggested Revisions
channel. Key encodings sp3 will need:

- `feature`: `shape:'segments'`, `progression:'linear-reentrant'`, 5 steps, E1→feat-05.
- `debug`: `shape:'loop'`, `loop:{ over:['dbg-02','dbg-03','dbg-04'], budget:3 }`, 5 steps, E2→dbg-04, E3→dbg-05.
- `spike`: `shape:'timebox'`, `timebox:{ budget:'3h' }`, 4 steps, E4→spk-04 — **+ spike-timebox sub-step revision flag.**
- `data`: `shape:'pipeline'`, 5 steps, E5→data-05 (inner explore loop intra-step; no top-level loop).
- New ids for sp4 to add: **dbg-05**, **data-05** (and re-task stub `dbg-04`→Log Confirm/Refute).

**Out of scope, confirmed not done here:** no canonical note, no JSON block, no decisions-so-far
append, no `prototype/` edit, no locked-variant redesign, no symmetry forced. All deferred to sp3.
