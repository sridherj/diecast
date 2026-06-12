# Stage Models — Product Revamp: Diecast Vision Prototype (Phase 2c canonical note)

> **THE single source of stage vocabulary** for the four workflow families
> (`feature · debug · spike · data`). Phases 3–4 author their canvases from this note and **never
> re-derive**; Phase 2a's generator encodes the `stageModels` block below into
> `prototype/data/org.js` (the encode is **sp4**, gated on 2a.1 — see Hand-off notes / Reconciliation
> F1). The `appState.spines` render layer derives its flat `steps: string[]` from this block.
>
> **Author:** cast-subphase-runner (sp3, run_20260611_224106_7636b6) · **Date:** 2026-06-12 ·
> **Inputs:** `sp1_evidence_base/evidence-base.md` (21 refs / 4 families) +
> `sp2_spine_derivation/spine-derivation.md` (derived spines + rubric scorecards + dropped-placeholder
> ledger). **Run mode:** FULL AUTONOMY — the written self-evaluation (§6) *replaces* the owner
> sign-off gate; no human checkpoint.

---

## 1. TL;DR — the four spines at a glance

Asymmetry is the design working (SC-005): three progression shapes, step counts 5 / 5 / 4 / 5, one
counted loop (debug), one budget meter (spike), one DAG (data), one segment bar (feature). No family
was padded or trimmed toward another.

| family | shape | progression / dynamic | steps | step shortLabels in order |
|--------|-------|-----------------------|-------|---------------------------|
| `feature` | `segments` | `linear-reentrant` | 5 | Shape the Problem · Commit & Scope · Design Approach · Build & Ship · Show It's Done |
| `debug` | `loop` | loop over `dbg-02..04`, budget 3 | 5 | Reproduce Reliably · Form a Hypothesis · Run an Experiment · Log Confirm/Refute · Prove the Fix |
| `spike` | `timebox` | single timeboxed pass, budget `3h` | 4 | Frame the Question · Probe Options · Evaluate Findings · Land the Verdict |
| `data` | `pipeline` | linear DAG, inner explore loop in `data-04` | 5 | Import Sources · Tidy & Validate · Transform · Explore · Publish |

**E1–E5 home steps:** E1 → `feat-05` · E2 → `dbg-04` · E3 → `dbg-05` · E4 → `spk-04` · E5 → `data-05`.

**Carried flag (Suggested Revisions, §7):** spike's `timebox` band must render its **four sub-steps
beneath the budget meter** — the meter is the wrapper/dominant status element, not the only element
(`spine-variant revision proposed`, from sp2 §6 — *flag, do not redesign*).

---

## 2. Per-family stage definitions

Each family below carries: the spine table (`id · label (+shortLabel) · does · surface · surfaceWhy ·
artifacts · refs · evidence`), the loop/progress semantics, the E1–E5 home step, and the surface
mappings with rationale + refs. All `refs` keys resolve in §4.

### 2.1 `feature` — `segments`, progression `linear-reentrant`

A known-path build: a linear backbone from a shaped problem to verified-shipped work, re-entrant
because shipping continuously feeds back into design/build. **No counted iteration band** — the
re-entrancy is a back-edge, not a budgeted loop.

| id | label (shortLabel) | does | surface · why | artifacts | refs | evidence |
|----|--------------------|------|----------------|-----------|------|----------|
| feat-01 | Shape the Problem | Define problem + appetite + a rough solution + named rabbit-holes; write it up as a pitch/brief before betting | `doc` · the shaped problem is a written artifact reviewed before commitment | pitch/brief (appetite · rough solution · rabbit-holes) | `shape-up`, `linear-method`, `design-docs-google` | null |
| feat-02 | Commit & Scope | Place a fixed-appetite bet on the pitch, then break the committed work into shippable issues | `board` · the bet + scoped issues live on a ticket board | committed scope / issue board | `shape-up`, `linear-method` | null |
| feat-03 | Design the Approach (`Design Approach`) | Write a design doc / RFC capturing implementation strategy, alternatives, and trade-offs; resolve it in review threads | `doc` · the design and its review are a document discussion, the org's decision memory | design doc (alternatives + trade-offs) + review thread | `design-docs-google`, `linear-method` | null |
| feat-04 | Build & Ship | Build in vertical slices and ship continuously within the fixed timebox/cycle | `pr-thread` · slices land as reviewed, merged PRs | shipped vertical slice / merged PR | `shape-up`, `linear-method` | null |
| feat-05 | Show It's Done | Demonstrate completion via the diff plus an acceptance-evidence bundle (screenshots / proof shots / test summary) | `pr-thread` · "done" is shown on the PR/report as evidence, not asserted | acceptance-evidence bundle (diff + screenshots + summary) | `linear-method`, `proofshot`, `devin-cu` | **E1** |

- **Loop/progress:** linear, re-entrant (progress). `shape-up` + `linear-method` describe a forward
  backbone (shape → bet → build → ship); `linear-method`'s "ship continuously… quick feedback loops"
  makes it re-entrant (ship can send you back to design/build), but there is **no counted iteration
  band**. Encoding: `shape:'segments'`, `progression:'linear-reentrant'`.
- **E1 home — `feat-05` (Show It's Done):** the acceptance panel. "Done" is *shown* (diff + proof
  bundle), never asserted — the failure mode the family guards against.
- **Surface mappings:** `doc` for the two written-and-reviewed artifacts (feat-01 brief, feat-03
  design doc — `shape-up`/`design-docs-google` describe both as documents reviewed in threads);
  `board` for feat-02 (the bet + scoped issues are a ticket list — `linear-method` "create an issue
  for each one"); `pr-thread` for feat-04/05 (slices land as merged PRs; the acceptance evidence
  rides the PR/report — `linear-method` "show the diff", `proofshot` proof bundle).

### 2.2 `debug` — `loop`, `loop:{ over:['dbg-02','dbg-03','dbg-04'], budget:3 }`

"Where is this?" is *unknown until found* — a search, not a march. A reliable repro **opens** the
loop; the loop iterates hypothesis → experiment → confirm/refute until the root cause is confirmed;
the spine **exits** by proving the fix red→green.

| id | label (shortLabel) | does | surface · why | artifacts | refs | evidence |
|----|--------------------|------|----------------|-----------|------|----------|
| dbg-01 | Reproduce Reliably | Move from "saw it a few times" to an on-demand, consistent reproduction (special care for intermittents) | `ledger` · the repro recipe is the first investigation-ledger entry | reliable reproduction (recorded repro steps) | `agans`, `julia-evans` | null |
| dbg-02 | Form a Hypothesis | Invent a falsifiable hypothesis for the failure cause, consistent with the observations so far | `ledger` · each candidate cause is logged in the case file | hypothesis entry (the "accusation") | `zeller`, `uxmag-detective` | null |
| dbg-03 | Run an Experiment | Quit thinking and look: change one thing / bisect, observe actual behavior with tools, get data | `ledger` · the experiment and what it showed are logged | experiment result + trace/instrumentation | `agans`, `zeller` | null |
| dbg-04 | Log Confirm/Refute | Record prediction-vs-observed per hypothesis; mark confirmed/refuted; a refuted prediction spawns the next hypothesis | `ledger` · the confirmed/refuted ledger is the loop's memory | confirm/refute evidence ledger | `hypothesizer`, `uxmag-detective` | **E2** |
| dbg-05 | Prove the Fix | Prove the fix by making the failure recur, then disappear — a red→green repro (fails, then the same case passes) | `pr-thread` · the proof lands on the fix PR/report | red→green repro (failing → passing case) | `agans`, `undo-replay` | **E3** |

- **Loop/progress:** loop. `zeller` states it explicitly — observe → hypothesis → predict →
  experiment → observe, repeated until the cause is found; `uxmag-detective` and `julia-evans` both
  describe iterative evidence-gathering; a refuted prediction (`undo-replay`) spawns the next
  hypothesis. Encoding: `shape:'loop'`, `loop:{ over:['dbg-02','dbg-03','dbg-04'], budget:3 }`. The
  loop iterates **hypothesis → experiment → confirm/refute**; `dbg-01` (repro) opens it, `dbg-05`
  (prove the fix) is the exit. `budget:3` feeds Phase 1's debug `iter` counter semantics.
- **E2 home — `dbg-04` (Log Confirm/Refute):** the confirm/refute ledger (`hypothesizer`'s
  confirmed/refuted timeline; the `uxmag-detective` "accusation" elevation).
- **E3 home — `dbg-05` (Prove the Fix):** the red→green repro (`undo-replay`; `agans` "if you didn't
  fix it, it ain't fixed"). Debug correctly hosts **both** E2 and E3 on distinct steps.
- **Surface mappings:** `ledger` for dbg-01..04 (the repro recipe, the logged hypotheses, the
  experiment results, and the confirm/refute marks are all entries in one investigation ledger —
  `agans` "keep an audit trail", `hypothesizer`'s evidence timeline); `pr-thread` for dbg-05 (the
  proof of the fix rides the fix PR).

### 2.3 `spike` — `timebox`, `timebox:{ budget:'3h' }`

A single timeboxed pass whose deliverable is a *decision input*, not shippable code. The timebox is
the **dominant status element** — the budget meter wraps all four steps. **(See §7 flag: the four
sub-steps render *beneath* the meter.)**

| id | label (shortLabel) | does | surface · why | artifacts | refs | evidence |
|----|--------------------|------|----------------|-----------|------|----------|
| spk-01 | Frame the Question | Identify the single riskiest unknown and pose it as one answerable technical question | `memo` · the question opens the spike memo under its budget | risk-question memo | `xp-spike`, `mike-bowler` | null |
| spk-02 | Probe Options | Build quick, throwaway probes to answer the question — quick-and-dirty, explicitly disposable | `memo` · probe attempts are logged in the memo, code is dropped | probes-tried list (throwaway) | `xp-spike`, `mike-bowler` | null |
| spk-03 | Evaluate Findings | Evaluate the probes; keep the learning, discard the code; at any point decide "done enough" | `memo` · findings accrue in the memo against the burning budget | findings notes | `xp-spike`, `agilemania-spike` | null |
| spk-04 | Land the Verdict | Write a one-line answer and link it to the downstream decision it informs (with a revisit-if trip-wire) | `memo` · the verdict closes the memo and points at its decision record | verdict card (`spike_ref` + `revisit_if`) | `mike-bowler`, `agilemania-spike`, `adr-nygard` | **E4** |

- **Loop/progress:** linear, single timeboxed pass (progress). `xp-spike` / `mike-bowler`: one short
  pass, probe → evaluate → drop the code, keep the learning; no iteration band — the *budget* is the
  dynamic element, not a repeat count. Encoding: `shape:'timebox'`, `timebox:{ budget:'3h' }` (XP
  spikes are "typically hours"; both practitioner accounts insist on a strict, short, hours-scale
  box).
- **E4 home — `spk-04` (Land the Verdict):** the verdict card carrying `spike_ref` (→ the decision it
  informs) + `revisit_if` (the trip-wire) — `mike-bowler` "feeds a decision", `agilemania-spike`
  traceable finding↔decision link, `adr-nygard` revisit-if.
- **Surface mappings:** all four → `memo` (the memo+timebox surface). The question, the probes-tried
  list, the findings, and the verdict all accrue in **one timeboxed memo** against the burning budget
  — `xp-spike` "use a timebox and a budget", `agilemania-spike` "document the outcome as
  comments/findings linked to the product decision".

### 2.4 `data` — `pipeline`

A position in a pipeline, not a loop or a path. The frame is linear (sources → answer); an inner
transform↔visualize↔model **explore loop lives *inside* `data-04`**, it is **not** a top-level loop
band (resolved in sp2 §6 — honors the locked `pipeline` variant).

| id | label (shortLabel) | does | surface · why | artifacts | refs | evidence |
|----|--------------------|------|----------------|-----------|------|----------|
| data-01 | Import Sources | Pull the sources (file / DB / API) that bear on the question into a working frame | `notebook` · ingestion happens in the analysis notebook | loaded dataset | `r4ds`, `dbt-analyst` | null |
| data-02 | Tidy & Validate | Tidy to one-variable-per-column / one-observation-per-row, then sanity-check: "are you telling me the truth?" — cross-examine outliers before trusting | `notebook` · cleaning and the sanity checks are notebook cells/charts | cleaned + validated frame (sanity notes) | `r4ds`, `data-sanity` | null |
| data-03 | Transform / Wrangle (`Transform`) | Narrow observations, create new variables, compute summary statistics | `notebook` · transforms are notebook cells | derived variables / summary tables | `r4ds`, `dbt-analyst` | null |
| data-04 | Explore (Viz↔Model) (`Explore`) | Iterate visualize ↔ model many times to find the answer; disposable charts also catch problems early (visualize-to-validate) | `notebook` · the explore loop is interactive charting in the notebook | exploratory charts + candidate models | `r4ds`, `looks-good-correll` | null |
| data-05 | Publish + Provenance (`Publish`) | Publish a clean narrative report (viz as the headline) distinct from the working notebook, with source/transform lineage exposed on demand | `pr-thread` · the published report is the shareable deliverable | rendered report + provenance drill-in | `r4ds`, `hex-deepnote`, `atlan-provenance` | **E5** |

- **Loop/progress:** linear pipeline with an **inner** explore loop. `r4ds` frames a linear pipeline
  (import → tidy → transform → visualize/model → communicate); the visualize↔model iteration
  ("iterate between them many times") is **internal to `data-04`**, not a top-level loop. Encoding:
  `shape:'pipeline'` (no top-level `loop`, no `loop.over`). The intra-step iteration is made explicit
  in `data-04`'s label and `does`.
- **E5 home — `data-05` (Publish + Provenance):** the rendered report (viz as headline, distinct from
  the working notebook — `hex-deepnote`) + the provenance drill-in (source/transform lineage on
  demand — `atlan-provenance`). `r4ds` "communicate" is the practitioner anchor.
- **Surface mappings:** `notebook` for data-01..04 (import, tidy/validate, transform, and the explore
  loop are all notebook cells/charts — `r4ds`, `data-sanity` sanity charts, `looks-good-correll`
  disposable validation viz); `pr-thread` for data-05 (the published report is the shareable
  deliverable, distinct from the notebook).

---

## 3. Dropped-placeholder ledger (verbatim from sp2 §5 — proof of derive-first ordering)

This ledger was written **after** the spines were derived (sp2 §1–§4), then diffed against the priors.
It covers **both** sources: (A) the dropped exploration placeholders (owner-directed drop), and (B)
the Phase 1/2a watermarked stub labels in `generate-org.mjs`.

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

| family | stub labels (Phase 1/2a) | derived labels (sp2/sp3) | net change |
|--------|--------------------------|--------------------------|------------|
| feature | requirements · plan · tickets · execution · review | Shape the Problem · Commit & Scope · Design the Approach · Build & Ship · Show It's Done | same count (5); stubs were generic SDLC nouns → replaced with practitioner verbs+artifacts; ids feat-01..05 preserved |
| debug | reproduce · hypothesize · experiment · fix | Reproduce Reliably · Form a Hypothesis · Run an Experiment · Log Confirm/Refute · Prove the Fix | **4 → 5 steps**: the stub's single "fix" splits into **dbg-04 Log Confirm/Refute (E2)** + **dbg-05 Prove the Fix (E3)**, giving both debug evidence treatments distinct homes. New id **dbg-05**. |
| spike | frame · probe · measure · verdict | Frame the Question · Probe Options · Evaluate Findings · Land the Verdict | same count (4); "measure" → "Evaluate Findings" (evaluation is the evidenced act, not just measurement); ids spk-01..04 preserved |
| data | extract · transform · analyze · report | Import Sources · Tidy & Validate · Transform / Wrangle · Explore (Viz↔Model) · Publish + Provenance | **4 → 5 steps**: stub lacked an explicit **Tidy & Validate** step that two practitioner accounts (`r4ds` + `data-sanity`) insist on; inserted as data-02. "analyze" → "Explore (Viz↔Model)"; "report" → "Publish + Provenance" (E5). New id **data-05**. |

> **ID-collision note for sp4:** the derived **dbg-05** and **data-05** are *new* step ids not present
> in the current 2a stub block; the existing stub `dbg-04 = fix` is **re-tasked** to `Log
> Confirm/Refute` and "Prove the Fix" becomes the new `dbg-05`. sp4's generator edit must add these
> ids when it rewrites `stageModels` — the one standing, owner-sanctioned exception to 2a's
> post-freeze policy. Not drift.

**Rubric-driven drop (from sp2 §2, recorded so the rubric is visibly filtering):** `data` "Frame the
Question" was **dropped as a standalone step** (Recognition fail — only `dbt-analyst` names it as a
discrete step; `r4ds`, the dominant workflow, begins at *import*). The question is retained as the
pipeline's **input precondition** (it defines `data-05`'s answer), not a rendered step.

---

## 4. References table (stable key → full citation)

Every `refs` key used in §2 resolves here. Source classes: **`practitioner-account`** (a practitioner
describing their own hands-on process — ≥1 mandatory per family) · **`tool-documented-workflow`** · 
**`methodology-text`**. Drawn from sp1's evidence base.

| key | citation | class | source |
|-----|----------|-------|--------|
| `shape-up` | *Shape Up* — Ryan Singer / Basecamp (shape · bet · build · ship in a fixed appetite) | practitioner-account | https://basecamp.com/shapeup/0.3-chapter-01 · https://basecamp.com/shapeup/2.3-chapter-09 |
| `linear-method` | *The Linear Method* — the Linear team (initiative → brief → scope into issues → build in cycles → show the diff) | practitioner-account | https://linear.app/method/introduction · https://linear.app/method/scope-projects |
| `design-docs-google` | *Design Docs at Google* — Malte Ubl (write a design doc with trade-offs, review in comment threads, doc as org memory) | practitioner-account | https://www.industrialempathy.com/posts/design-docs-at-google/ |
| `proofshot` | *ProofShot* — open-source visual proof bundle (video + key-moment screenshots + console/server errors + action timeline) | tool-documented-workflow | https://github.com/AmElmo/proofshot · https://news.ycombinator.com/item?id=47499672 |
| `devin-cu` | *Devin Computer Use* — Cognition (checkpoint screenshots verify layout/styling; logs each action) | tool-documented-workflow | https://docs.devin.ai/work-with-devin/computer-use |
| `agans` | *Debugging: The 9 Indispensable Rules* — David J. Agans (make it fail · quit thinking and look · divide and conquer · keep an audit trail · if you didn't fix it, it ain't fixed) | practitioner-account | https://dwheeler.com/essays/debugging-agans.html · https://embeddedartistry.com/blog/2017/09/06/debugging-9-indispensable-rules/ |
| `julia-evans` | *How I got better at debugging* — Julia Evans, jvns.ca (reproduce reliably · observe with tools · understand exactly what's wrong before fixing) | practitioner-account | https://jvns.ca/blog/2015/11/22/how-i-got-better-at-debugging/ |
| `zeller` | *Why Programs Fail: A Guide to Systematic Debugging* — Andreas Zeller (observe → hypothesize → predict → experiment → observe, looping) | methodology-text | https://www.embedded.com/scientific-debugging-finding-out-why-your-code-is-buggy-part-1/ · https://queue.acm.org/detail.cfm?id=1217270 |
| `uxmag-detective` | *Secrets of Agentic UX* detective/case-file pattern — UX Magazine (evidence → case file → "accusation" root-cause → remediation) | practitioner-account | https://uxmag.com/articles/secrets-of-agentic-ux-emerging-design-patterns-for-human-interaction-with-ai-agents |
| `hypothesizer` | *Hypothesizer* hypothesis-based debugger — ACM UIST 2023 (investigation plan timeline; evidence items marked confirmed/refuted) | methodology-text | https://dl.acm.org/doi/10.1145/3586183.3606781 |
| `undo-replay` | Agentic / time-travel debugging — Undo.io, Replay.io (prove the bug, then prove the fix; red→green repro as the close) | tool-documented-workflow | https://undo.io/resources/agentic-debugging-vs-natural-language-interface/ |
| `xp-spike` | *Spike Solution* — C2 wiki / extremeprogramming.org (riskiest unknown · small timebox in hours · throwaway probe · evaluate → conclude) | practitioner-account | http://c2.com/xp/SpikeSolution.html · http://www.extremeprogramming.org/rules/spike.html |
| `mike-bowler` | *Why we should stop using spikes* — Mike Bowler (a specific technical question · strict short timebox · throwaway code · feeds a decision) | practitioner-account | https://blog.mikebowler.ca/2023/04/29/spikes/ |
| `agilemania-spike` | *Agile spike stories* — Agilemania (timeboxed risk-reduction experiment; document the outcome linked to the product decision it informs) | methodology-text | https://agilemania.com/agile-spike-story-what-is-a-spike-in-agile |
| `adr-nygard` | Architecture Decision Records — Nygard lineage / MS Well-Architected (context · options · decision · rationale · consequences · revisit-if) | methodology-text | https://adr.github.io/ · https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record |
| `r4ds` | *R for Data Science* — Hadley Wickham (import → tidy → transform → visualize↔model → communicate) | practitioner-account | https://r4ds.hadley.nz/intro · https://r4ds.hadley.nz/ |
| `dbt-analyst` | Analyst workflow — dbt Labs developer hub (start from a stakeholder question · validate source data · promote one-off into a shareable model/report) | tool-documented-workflow | https://docs.getdbt.com/guides/analyze-your-data · https://www.getdbt.com/resources/analysts-guide-to-working-with-data-engineering |
| `data-sanity` | *A Data Sanity Check Survival Guide* — Manojkumar Marri (cleaning + sanity-checking as the messiest/most critical phase; "are you telling me the truth?") | practitioner-account | https://medium.com/@manojkumar.marri26/climbing-the-right-data-ladder-a-data-sanity-check-survival-guide-b7a91bb3180c |
| `looks-good-correll` | *Looks Good To Me: Visualizations As Sanity Checks* — Michael Correll (disposable charts as validation, not just output) | practitioner-account | https://mcorrell.medium.com/looks-good-to-me-visualizations-as-sanity-checks-6fd1ffa37ab9 |
| `hex-deepnote` | Notebook→report split — Hex / Deepnote (published narrative report distinct from the working notebook; viz as headline) | tool-documented-workflow | https://deepnote.com/compare/hex-vs-deepnote |
| `atlan-provenance` | Data lineage / provenance — Atlan ("lineage is about flow, provenance is about proof"; which sources/transforms produced the number) | methodology-text | https://atlan.com/know/data-lineage-tracking/ |

---

## 5. `stageModels` encoding block (plain JSON — the 2a coordination point; sp4 pastes this)

**Plain-JSON only** — no functions, no comments inside the value, no computed expressions; parses via
`JSON.parse` / `jq` / `node -e` (the `file://` plain-JSON guarantee; sp4's generator gate). Field
names are **the contract** (2a/2c must not rename them; may extend). This is the canonical,
comment-free copy.

```json
{
  "feature": {
    "shape": "segments",
    "progression": "linear-reentrant",
    "steps": [
      { "id": "feat-01", "label": "Shape the Problem", "does": "Define problem + appetite + a rough solution + named rabbit-holes; write it up as a pitch/brief before betting", "surface": "doc", "surfaceWhy": "the shaped problem is a written artifact reviewed before commitment", "artifacts": ["pitch/brief (appetite, rough solution, rabbit-holes)"], "refs": ["shape-up", "linear-method", "design-docs-google"], "evidence": null },
      { "id": "feat-02", "label": "Commit & Scope", "does": "Place a fixed-appetite bet on the pitch, then break the committed work into shippable issues", "surface": "board", "surfaceWhy": "the bet plus scoped issues live on a ticket board", "artifacts": ["committed scope / issue board"], "refs": ["shape-up", "linear-method"], "evidence": null },
      { "id": "feat-03", "label": "Design the Approach", "shortLabel": "Design Approach", "does": "Write a design doc / RFC capturing implementation strategy, alternatives, and trade-offs; resolve it in review threads", "surface": "doc", "surfaceWhy": "the design and its review are a document discussion, the org's decision memory", "artifacts": ["design doc (alternatives + trade-offs)", "review thread"], "refs": ["design-docs-google", "linear-method"], "evidence": null },
      { "id": "feat-04", "label": "Build & Ship", "does": "Build in vertical slices and ship continuously within the fixed timebox/cycle", "surface": "pr-thread", "surfaceWhy": "slices land as reviewed, merged PRs", "artifacts": ["shipped vertical slice / merged PR"], "refs": ["shape-up", "linear-method"], "evidence": null },
      { "id": "feat-05", "label": "Show It's Done", "does": "Demonstrate completion via the diff plus an acceptance-evidence bundle (screenshots / proof shots / test summary)", "surface": "pr-thread", "surfaceWhy": "done is shown on the PR/report as evidence, not asserted", "artifacts": ["acceptance-evidence bundle (diff + screenshots + summary)"], "refs": ["linear-method", "proofshot", "devin-cu"], "evidence": "E1" }
    ]
  },
  "debug": {
    "shape": "loop",
    "loop": { "over": ["dbg-02", "dbg-03", "dbg-04"], "budget": 3 },
    "steps": [
      { "id": "dbg-01", "label": "Reproduce Reliably", "does": "Move from saw-it-a-few-times to an on-demand, consistent reproduction (special care for intermittents)", "surface": "ledger", "surfaceWhy": "the repro recipe is the first investigation-ledger entry", "artifacts": ["reliable reproduction (recorded repro steps)"], "refs": ["agans", "julia-evans"], "evidence": null },
      { "id": "dbg-02", "label": "Form a Hypothesis", "does": "Invent a falsifiable hypothesis for the failure cause, consistent with the observations so far", "surface": "ledger", "surfaceWhy": "each candidate cause is logged in the case file", "artifacts": ["hypothesis entry (the accusation)"], "refs": ["zeller", "uxmag-detective"], "evidence": null },
      { "id": "dbg-03", "label": "Run an Experiment", "does": "Quit thinking and look: change one thing / bisect, observe actual behavior with tools, get data", "surface": "ledger", "surfaceWhy": "the experiment and what it showed are logged", "artifacts": ["experiment result + trace/instrumentation"], "refs": ["agans", "zeller"], "evidence": null },
      { "id": "dbg-04", "label": "Log Confirm/Refute", "does": "Record prediction-vs-observed per hypothesis; mark confirmed/refuted; a refuted prediction spawns the next hypothesis", "surface": "ledger", "surfaceWhy": "the confirmed/refuted ledger is the loop's memory", "artifacts": ["confirm/refute evidence ledger"], "refs": ["hypothesizer", "uxmag-detective"], "evidence": "E2" },
      { "id": "dbg-05", "label": "Prove the Fix", "does": "Prove the fix by making the failure recur, then disappear - a red-to-green repro (fails, then the same case passes)", "surface": "pr-thread", "surfaceWhy": "the proof lands on the fix PR/report", "artifacts": ["red-to-green repro (failing then passing case)"], "refs": ["agans", "undo-replay"], "evidence": "E3" }
    ]
  },
  "spike": {
    "shape": "timebox",
    "timebox": { "budget": "3h" },
    "steps": [
      { "id": "spk-01", "label": "Frame the Question", "does": "Identify the single riskiest unknown and pose it as one answerable technical question", "surface": "memo", "surfaceWhy": "the question opens the spike memo under its budget", "artifacts": ["risk-question memo"], "refs": ["xp-spike", "mike-bowler"], "evidence": null },
      { "id": "spk-02", "label": "Probe Options", "does": "Build quick, throwaway probes to answer the question - quick-and-dirty, explicitly disposable", "surface": "memo", "surfaceWhy": "probe attempts are logged in the memo, code is dropped", "artifacts": ["probes-tried list (throwaway)"], "refs": ["xp-spike", "mike-bowler"], "evidence": null },
      { "id": "spk-03", "label": "Evaluate Findings", "does": "Evaluate the probes; keep the learning, discard the code; at any point decide done-enough", "surface": "memo", "surfaceWhy": "findings accrue in the memo against the burning budget", "artifacts": ["findings notes"], "refs": ["xp-spike", "agilemania-spike"], "evidence": null },
      { "id": "spk-04", "label": "Land the Verdict", "does": "Write a one-line answer and link it to the downstream decision it informs (with a revisit-if trip-wire)", "surface": "memo", "surfaceWhy": "the verdict closes the memo and points at its decision record", "artifacts": ["verdict card (spike_ref + revisit_if)"], "refs": ["mike-bowler", "agilemania-spike", "adr-nygard"], "evidence": "E4" }
    ]
  },
  "data": {
    "shape": "pipeline",
    "steps": [
      { "id": "data-01", "label": "Import Sources", "does": "Pull the sources (file / DB / API) that bear on the question into a working frame", "surface": "notebook", "surfaceWhy": "ingestion happens in the analysis notebook", "artifacts": ["loaded dataset"], "refs": ["r4ds", "dbt-analyst"], "evidence": null },
      { "id": "data-02", "label": "Tidy & Validate", "does": "Tidy to one-variable-per-column / one-observation-per-row, then sanity-check: are you telling me the truth? - cross-examine outliers before trusting", "surface": "notebook", "surfaceWhy": "cleaning and the sanity checks are notebook cells/charts", "artifacts": ["cleaned + validated frame (sanity notes)"], "refs": ["r4ds", "data-sanity"], "evidence": null },
      { "id": "data-03", "label": "Transform / Wrangle", "shortLabel": "Transform", "does": "Narrow observations, create new variables, compute summary statistics", "surface": "notebook", "surfaceWhy": "transforms are notebook cells", "artifacts": ["derived variables / summary tables"], "refs": ["r4ds", "dbt-analyst"], "evidence": null },
      { "id": "data-04", "label": "Explore (Viz<->Model)", "shortLabel": "Explore", "does": "Iterate visualize and model many times to find the answer; disposable charts also catch problems early (visualize-to-validate)", "surface": "notebook", "surfaceWhy": "the explore loop is interactive charting in the notebook", "artifacts": ["exploratory charts + candidate models"], "refs": ["r4ds", "looks-good-correll"], "evidence": null },
      { "id": "data-05", "label": "Publish + Provenance", "shortLabel": "Publish", "does": "Publish a clean narrative report (viz as the headline) distinct from the working notebook, with source/transform lineage exposed on demand", "surface": "pr-thread", "surfaceWhy": "the published report is the shareable deliverable", "artifacts": ["rendered report + provenance drill-in"], "refs": ["r4ds", "hex-deepnote", "atlan-provenance"], "evidence": "E5" }
    ]
  }
}
```

**`appState.spines` derivation rule (render-layer, Phase 1 contract — keys unrenamed, NOT duplicated
into appState):**

```js
// appState.spines.<family> (Phase 1 contract, unrenamed):
//   { placeholder: false, shape: stageModels.<f>.shape,
//     steps: stageModels.<f>.steps.map(s => s.shortLabel ?? s.label), current, iter? }
```

So `appState.spines.feature.steps` = `['Shape the Problem','Commit & Scope','Design Approach','Build &
Ship',"Show It's Done"]`; debug's `iter` reads `stageModels.debug.loop.budget` (3); spike's meter
reads `stageModels.spike.timebox.budget` ('3h'). Rich per-step objects live **only** in `stageModels`.

> **JSON-parse spot-check (sp3 ran this; record):** the block above was extracted to `/tmp/sm.json`
> and verified — `jq -e 'keys == ["data","debug","feature","spike"]'` → true; `node -e` confirmed all
> four families present with 4–7 steps each (feature 5 · debug 5 · spike 4 · data 5), function-free,
> parses clean. The non-ASCII `↔` glyph in `data-04` was rendered as ASCII `<->` in the JSON to keep
> the encoded value plain-ASCII-safe for the generator (the human-facing label in §2.4 keeps the
> glyph; sp4 may restore the glyph in the generator if desired — both are valid JSON).

---

## 6. Self-evaluation gate (replaces the owner sign-off — full autonomy)

The five-test rubric (from sp2 §2), every step of all four spines, then a per-family verdict naming
the **strongest supporting reference** and the **weakest step (honestly)**, ending in an explicit
**PASS / FAIL**. Tests: **(1) Verb+artifact** · **(2) Recognition** (≥2 independent sp1 sources, both
cited) · **(3) Hole** · **(4) Tidy-label kill** · **(5) Familiar-surface**. A step ships only if all
five PASS.

### 6.1 `feature`

| step | 1 Verb+artifact | 2 Recognition (≥2 cited) | 3 Hole | 4 Tidy-label kill | 5 Surface | verdict |
|------|----|----|----|----|----|----|
| feat-01 Shape the Problem | PASS — pitch/brief | PASS — `shape-up` (Shape) + `linear-method` (write brief/spec) | PASS — building unshaped is the classic miss | PASS — first-person method | PASS — `doc` | **SHIP** |
| feat-02 Commit & Scope | PASS — committed scope / issue board | PASS — `shape-up` (Bet, fixed appetite) + `linear-method` (scope into issues) | PASS — un-bet, un-scoped work has no boundary | PASS — practitioner accounts | PASS — `board` | **SHIP** |
| feat-03 Design the Approach | PASS — design doc/RFC | PASS — `design-docs-google` (design doc) + `linear-method` (the "how") | PASS — top eng notices no design record | PASS — first-person Google practice | PASS — `doc` | **SHIP** |
| feat-04 Build & Ship | PASS — merged PRs / shipped slices | PASS — `shape-up` (fixed-timebox build) + `linear-method` (cycles, ship continuously) | PASS — load-bearing | PASS — practitioner accounts | PASS — `pr-thread` | **SHIP** |
| feat-05 Show It's Done | PASS — acceptance-evidence bundle | PASS — `linear-method` (show the diff) + `proofshot` (proof bundle) | PASS — "done" without evidence is the guarded failure | PASS — tool + practitioner | PASS — `pr-thread` | **SHIP** |

**Verdict — would a top feature-builder recognize this as their actual workflow?** Yes. The shape →
bet/scope → design → build/ship → show-done backbone is exactly how `shape-up` and `linear-method`
describe their own practice, with a design-doc step grounded in `design-docs-google`. **Strongest ref:
`linear-method`** — it independently corroborates four of the five steps (brief, scope-into-issues,
ship-in-cycles, show-the-diff) end to end. **Weakest step (honest): `feat-02 Commit & Scope`** — it
fuses two practitioner acts (the appetite *bet* from `shape-up` and *scoping into issues* from
`linear-method`) into one segment; defensible because both are pre-build commitment moves that share
the `board` surface, but a Shape-Up purist might want the bet visibly distinct from the scope-down.
Holds under the 4–7 bound; not split. **PASS.**

### 6.2 `debug`

| step | 1 Verb+artifact | 2 Recognition (≥2 cited) | 3 Hole | 4 Tidy-label kill | 5 Surface | verdict |
|------|----|----|----|----|----|----|
| dbg-01 Reproduce Reliably | PASS — on-demand repro | PASS — `agans` (make it fail) + `julia-evans` (reproduce reliably) | PASS — can't debug what you can't trigger | PASS — two practitioner accounts | PASS — `ledger` | **SHIP** |
| dbg-02 Form a Hypothesis | PASS — logged hypothesis | PASS — `zeller` (invent hypothesis) + `uxmag-detective` (accusation) | PASS — guessing without a stated hypothesis can't be tested | PASS — practitioner + applied method | PASS — `ledger` | **SHIP** |
| dbg-03 Run an Experiment | PASS — experiment result + trace | PASS — `agans` (quit thinking and look) + `zeller` (test by experiment) | PASS — untested hypotheses are opinions | PASS — practitioner accounts | PASS — `ledger` | **SHIP** |
| dbg-04 Log Confirm/Refute | PASS — confirm/refute ledger | PASS — `hypothesizer` (confirmed/refuted) + `uxmag-detective` (confirmed observations) | PASS — without it the loop loses memory and re-tests dead hypotheses | PASS — tool + practitioner | PASS — `ledger` | **SHIP** |
| dbg-05 Prove the Fix | PASS — red→green repro | PASS — `agans` ("if you didn't fix it, it ain't fixed") + `undo-replay` (red→green) | PASS — a "fix" with no proof is the family's signature failure | PASS — practitioner + tool | PASS — `pr-thread` | **SHIP** |

**Verdict — would a top debugger recognize this as their actual workflow?** Yes. Repro-opens →
hypothesis↔experiment↔confirm/refute loop → prove-the-fix is the scientific-debugging discipline
named by `agans`, `julia-evans`, and `zeller`, with the confirm/refute ledger grounded in a
controlled study (`hypothesizer`). **Strongest ref: `agans`** — *9 Indispensable Rules* maps directly
onto four steps (make it fail, quit thinking and look, change one thing / divide and conquer, if you
didn't fix it it ain't fixed). **Weakest step (honest): `dbg-03 Run an Experiment`** — `agans`'s
"divide and conquer" + "change one thing" + "quit thinking and look" are arguably *three* micro-rules
compressed into one loop step; the compression is deliberate (the loop band can't render three sub-
steps per turn within the 4–7 bound) and every compressed rule still appears in the `does`, but it is
the densest step. **PASS.**

### 6.3 `spike`

| step | 1 Verb+artifact | 2 Recognition (≥2 cited) | 3 Hole | 4 Tidy-label kill | 5 Surface | verdict |
|------|----|----|----|----|----|----|
| spk-01 Frame the Question | PASS — risk-question memo | PASS — `xp-spike` (riskiest unknown) + `mike-bowler` (one answerable question) | PASS — an unscoped spike is what both accounts warn against | PASS — two practitioner accounts | PASS — `memo` | **SHIP** |
| spk-02 Probe Options | PASS — throwaway probes-tried list | PASS — `xp-spike` (throwaway probe) + `mike-bowler` (throwaway code) | PASS — no probe, no learning | PASS — practitioner accounts | PASS — `memo` | **SHIP** |
| spk-03 Evaluate Findings | PASS — findings notes | PASS — `xp-spike` (evaluate → conclude) + `agilemania-spike` (decide "done enough") | PASS — un-evaluated probes leave no learning | PASS — practitioner + method | PASS — `memo` | **SHIP** |
| spk-04 Land the Verdict | PASS — verdict card w/ `spike_ref` + `revisit_if` | PASS — `mike-bowler` (feeds a decision) + `agilemania-spike` (traceable finding↔decision) | PASS — a spike whose answer never reaches a decision was wasted | PASS — practitioner + method | PASS — `memo` | **SHIP** |

**Verdict — would a top spike-runner recognize this as their actual workflow?** Yes. Frame one risky
question → throwaway probe → evaluate (keep learning, drop code) → land a verdict that feeds a
decision is the original XP spike discipline, restated by negation in `mike-bowler`'s critique.
**Strongest ref: `xp-spike`** — the C2/extremeprogramming.org source defines the timebox, the
throwaway probe, and the evaluate→conclude close directly. **Weakest step (honest): `spk-03 Evaluate
Findings`** — its boundary with `spk-04 Land the Verdict` is the softest in any spine (evaluating the
probes and writing the one-line verdict can blur into a single act for a short spike); kept distinct
because the *verdict card* (E4, with `spike_ref` + `revisit_if`) is a separable artifact from the raw
findings notes, and `agilemania-spike`/`adr-nygard` treat the decision-linked record as its own thing.
**Note the carried §7 flag** (sub-steps render beneath the meter) is a *rendering* concern, not a
content failure. **PASS.**

### 6.4 `data`

| step | 1 Verb+artifact | 2 Recognition (≥2 cited) | 3 Hole | 4 Tidy-label kill | 5 Surface | verdict |
|------|----|----|----|----|----|----|
| data-01 Import Sources | PASS — loaded dataset | PASS — `r4ds` (import) + `dbt-analyst` (pull/analyze data) | PASS — no sources, no analysis | PASS — practitioner + tool | PASS — `notebook` | **SHIP** |
| data-02 Tidy & Validate | PASS — cleaned + validated frame | PASS — `r4ds` (tidy) + `data-sanity` (sanity-check before trusting) | PASS — the un-checked frame is the "messiest but most critical" gap | PASS — two practitioner accounts name it | PASS — `notebook` | **SHIP** |
| data-03 Transform / Wrangle | PASS — derived variables / summary tables | PASS — `r4ds` (transform) + `dbt-analyst` (modeling / one-off queries) | PASS — raw tidy data rarely answers the question | PASS — practitioner + tool | PASS — `notebook` | **SHIP** |
| data-04 Explore (Viz↔Model) | PASS — exploratory charts + candidate models | PASS — `r4ds` (visualize↔model iterate) + `looks-good-correll` (visualize-to-validate) | PASS — skipping explore ships unexamined numbers | PASS — two practitioner accounts | PASS — `notebook` | **SHIP** |
| data-05 Publish + Provenance | PASS — rendered report + provenance drill-in | PASS — `r4ds` (communicate) + `hex-deepnote` (report distinct from notebook) | PASS — an answer no one can read or trust is no answer | PASS — practitioner + tool | PASS — `pr-thread` | **SHIP** |

**Verdict — would a top data analyst recognize this as their actual workflow?** Yes. Import → tidy &
validate → transform → explore (viz↔model) → publish is `r4ds` almost verbatim, with the explicit
*Tidy & Validate* step that practitioners (`data-sanity`) insist on but textbooks fold away.
**Strongest ref: `r4ds`** — Wickham's import→tidy→transform→visualize/model→communicate pipeline is
the most widely-recognized practitioner workflow in the family and corroborates all five steps.
**Weakest step (honest): `data-03 Transform / Wrangle`** — `r4ds` itself bundles tidy+transform as
"wrangling" and transform+model shade into each other, so data-03's boundaries with data-02 and
data-04 are the least crisp; kept as a distinct step because the *artifact* differs (derived
variables / summary tables vs. cleaned frame vs. exploratory charts) and dropping it would force a
4-step pipeline that hides the wrangling practitioners spend most of their time in. **PASS.**

### 6.5 Gate outcome

**All four families PASS.** No FAIL → **no sp2 rework loop triggered** (Step 3.4). Under full
autonomy the self-evaluation *is* the gate; the parent orchestrator accepts on all-pass. The single
carried flag (spike sub-step rendering, §7) is a 2b/Phase-3 *rendering* confirmation, not a content
failure, and does not block acceptance.

---

## 7. Hand-off notes (carry the F1-corrected ownership verbatim)

### To sp4 (2c.4 encode — runs after 2a.1's generator exists; Reconciliation F1)

- **Ownership (F1):** the `org.js` `stageModels` rewrite is owned by **2c itself, executed via 2a's
  generator** — *not* "2a pastes it." sp4 edits **only** the stage-model section of
  `prototype/data/_build/generate-org.mjs` with the §5 vocabulary, then re-emits `org.js` via the
  generator (which re-runs its invariant gate). This flips `placeholder:true → false`. Scheduled
  **after 2a.1 (the generator exists) and before Phase 3 dispatch**; the `stageModels` region is the
  one standing exception to 2a's post-freeze policy.
- **Paste the §5 comment-free JSON block** as the stage-model data. **New ids to add:** `dbg-05` and
  `data-05`; **re-task** the existing stub `dbg-04 = fix` to `Log Confirm/Refute`. Do not treat the
  extra ids as drift (ID-collision note, §3.B).
- If 2a has **not** landed the generator when sp3 completes, sp4 **parks** (polls Phase 2a) and **must
  complete before Phase 3 dispatch**. `appState.spines` derivation stays in the **render layer** (§5
  rule) — do not duplicate rich step objects into appState.
- **Plain-JSON guarantee:** keep the encoded value function-free and comment-free; the generator emits
  `window.ORG = Object.freeze({...})` plain frozen data (`file://` contract).

### To 2b (component kit)

- Confirm the four spine variants against the derived shapes: `feature=segments` (`linear-reentrant`,
  5 segs) · `debug=loop` (`over:['dbg-02','dbg-03','dbg-04']`, budget 3; dbg-01 opens, dbg-05 exits) ·
  `spike=timebox` (budget `3h`) · `data=pipeline` (5-step DAG; inner explore loop intra-`data-04`, no
  top-level loop band). All four match 2b's locked picks.
- **Suggested Revisions — carried flag (`spine-variant revision proposed`, from sp2 §6, DO NOT
  redesign here):** spike derives **four ordered sub-steps** (Frame → Probe → Evaluate → Verdict), but
  2b locked the variant as a **budget meter**. If the `timebox` band renders *only* a gauge, the four
  sub-steps have nowhere to show. **Proposed:** the `timebox` band renders the four sub-steps
  **beneath** the budget meter (the meter is the wrapper / dominant status element, not the only
  element). Proceeding with `timebox` as the best fit; 2b/Phase 3 to confirm the band layout.
- **Resolved (no flag):** the `data` inner transform↔visualize↔model loop surfaces as **one step**
  (`data-04`), top-level shape stays `pipeline` — honors the locked variant; no `loop.over` for data.

### To Phase 3 (and Phase 4)

- Author the feature/debug (Phase 3) and spike/data (Phase 4) canvases from §2/§5 — **cite this note,
  never re-derive vocabulary** (drift guard; the decisions-so-far append is the enforcement vehicle).
- **Remove the PLACEHOLDER watermark** when rendering from `stageModels` (the flag is `false` once sp4
  lands).
- `StageSurface` renders keyed on each step's `surface` (`doc|board|pr-thread|ledger|notebook|memo`) —
  the §2 surface column is the authoritative per-step mapping. E1→feat-05, E2→dbg-04, E3→dbg-05,
  E4→spk-04, E5→data-05 are the EvidenceBlock home steps.

---

*End of canonical note. Single source of stage vocabulary for Phases 3–6. sp4 encodes §5 into
`org.js` via 2a's generator (gated on 2a.1, before Phase 3 dispatch). `prototype/` untouched by sp3.*
