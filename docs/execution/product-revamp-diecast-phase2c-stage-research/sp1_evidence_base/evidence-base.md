# Practitioner Evidence Base — Phase 2c sub-phase 2c.1

> **Deliverable of sp1.** Raw, cited evidence for the four workflow families
> (`feature · debug · spike · data`). This sub-phase gathers material only — it does **not**
> derive spines, assign step ids, score against the rubric, or write the canonical note (those are
> sp2/sp3). Reference **keys are stable** — sp2/sp3 cite them by key in `refs[]`.
>
> **Author:** cast-subphase-runner (run_20260611_222030_69bc3b) · **Date:** 2026-06-12 ·
> **Method:** mined the exploration reference set (`03-family-canvases-evidence.ai.md`,
> `05-decisions-autonomy.ai.md` Lens 1) then four timeboxed targeted scans (WebSearch/WebFetch).
> **Run mode:** FULL AUTONOMY — no escalation to `/cast-web-researcher` was needed; every family
> reached ≥3 quality refs with ≥1 hands-on practitioner account inside the timebox.

## Source-quality legend
- **`practitioner-account`** — a practitioner describing their *own* hands-on process (the
  mandatory class; ≥1 required per family).
- **`tool-documented-workflow`** — a tool/product's documented working model that encodes how
  its users actually work.
- **`methodology-text`** — a named methodology / book / framework describing a process abstractly.

## Anti-anchoring note (audit hook for sp2's ledger)
Searches were seeded **by named practitioners and primary sources** (Shape Up / Ryan Singer,
Agans, Zeller, Julia Evans, the C2 XP wiki, Mike Bowler, Hadley Wickham / R4DS) — **never** by the
dropped placeholder vocabulary (feature: *prototype-with-UI-choices → locked design → eng design*;
debug: *repro · RCA · evidence · fix · tests*). Where a derived concept happens to rhyme with a
placeholder (e.g. "reliably reproduce the failure" in debug), it arose **independently from ≥2
practitioner accounts**, not from seeding the placeholder. The formal derive-first/compare-after
diff is performed in sp2's dropped-placeholder ledger; this file does not compare.

---

## Family: `feature` (feature-builders)

> What "where is this?" looks like for a known-path build: a linear-but-re-entrant backbone from a
> shaped problem to shipped, verified work. Spine variant locked as `segments` (2b).

### `shape-up` — *Shape Up* (Ryan Singer / Basecamp) · **practitioner-account**
Basecamp's own internal product method, written up by their Head of Product Strategy.
- **Shape** — "define the key elements of a solution before we consider a project ready to bet on…
  concrete enough that the teams know what to do, yet abstract enough that they have room to work
  out the interesting details themselves." → candidate step: *shape the problem into a pitch*
  (artifact: pitch/brief with appetite + rough solution + rabbit-holes).
- **Bet** — at the "betting table," "shapers submit their pitches to be considered for the cycle";
  leadership bets a fixed appetite (not an estimate). → candidate step: *commit/bet with a fixed
  appetite* (artifact: a placed bet / committed scope).
- **Build** — "the development team is in charge of delivering the project within a fixed time
  box" (six weeks), integrating design+eng and shipping vertical slices. → candidate steps: *build
  in vertical slices*, *ship within the fixed timebox*.
- Source: https://basecamp.com/shapeup/0.3-chapter-01 · https://basecamp.com/shapeup/2.3-chapter-09

### `linear-method` — *Linear Method* (the Linear team) · **practitioner-account**
The Linear team's documented account of how they themselves build software.
- **Set direction / initiative** — "Ambitious goals are the only way to make a significant
  impact"; projects align to a higher-level initiative before work begins. → candidate step:
  *frame the goal/initiative*.
- **Write the project brief/spec** — "Every project should have a named owner who's responsible
  for writing the project brief"; the spec "briefly communicate[s] the 'why', 'what' and 'how'."
  → candidate step: *write a short project brief* (artifact: brief/spec).
- **Scope down into issues** — "Break down work into smaller parts and create an issue for each
  one"; "Projects should be designed so that they can be completed in 1–3 weeks." → candidate
  step: *scope down into shippable issues* (artifact: scoped issue list / board).
- **Build in cycles, ship continuously** — "Work in n-week cycles" (typically 2 wks); "shipping
  continuously… creates quick feedback loops with customers." → candidate step: *build & ship
  incrementally in a cycle*.
- **Show the diff (verify done)** — "The clearest way to see whether something is complete or not
  is to show the diff in the code or design file." → candidate step: *demonstrate done via the
  diff/PR* (artifact: PR/diff). **Carries E1's home** (acceptance evidence).
- Source: https://linear.app/method/introduction · https://linear.app/method/scope-projects

### `design-docs-google` — *Design Docs at Google* (Malte Ubl, CTO Vercel) · **practitioner-account**
First-person account of the design-doc practice the author ran at Google.
- **Write the design doc** — an informal doc the author writes "before they embark on the coding
  project," documenting "the high level implementation strategy and key design decisions with
  emphasis on the trade-offs… considered." → candidate step: *write a design doc / RFC* (artifact:
  design doc with alternatives + trade-offs).
- **Review phase** — "a design doc gets shared with a wider audience… discussion happening in
  comment threads," up to "formal design review meetings." → candidate step: *review & resolve in
  comment threads* (artifact: review thread). Supports the doc working-surface.
- **Implement, doc as organizational memory** — the doc becomes "the basis of an organizational
  memory around design decisions." → reinforces decision-record linkage at the design stage.
- Source: https://www.industrialempathy.com/posts/design-docs-at-google/

### `proofshot` — *ProofShot* visual proof bundle (open-source, Show HN) · **tool-documented-workflow**
- The "done" artifact is a proof bundle: "synchronized video + key-moment screenshots +
  console/server errors + an interactive action timeline." → evidences the **acceptance-evidence**
  surface (E1 home step): *assemble acceptance evidence* (artifact: screenshots + test summary).
- Source: https://github.com/AmElmo/proofshot · https://news.ycombinator.com/item?id=47499672

### `devin-cu` — *Devin Computer Use* checkpoint screenshots (Cognition) · **tool-documented-workflow**
- The agent "takes screenshots at checkpoints to verify layout/styling, logs each action." →
  reinforces *verify the built UI by screenshot* as a concrete acceptance step (E1).
- Source: https://docs.devin.ai/work-with-devin/computer-use

*(Practitioner-account check: `shape-up`, `linear-method`, `design-docs-google` — 3 hands-on
accounts. ✓)*

---

## Family: `debug` (debuggers)

> "Where is this?" is *unknown until found* — a search, not a march — so the spine is a loop with a
> counter. Variant locked as `loop` (2b). E2 (confirm/refute ledger) + E3 (red→green repro) live
> here.

### `agans` — *Debugging: The 9 Indispensable Rules* (David J. Agans) · **practitioner-account**
A 44-year engineer's war-story account of his own debugging discipline (hardware + software).
- **Understand the system** — know the design before you poke at it. → candidate step:
  *understand the system / read the map*.
- **Make it fail** — get a reliable, on-demand reproduction; special care for intermittents
  ("intermittent problems are usually the hardest to handle"). → candidate step: *make it fail
  reliably* (artifact: a reproduction).
- **Quit thinking and look** — "get data first… see the failure, see the details, build
  instrumentation in… guess only to focus the search." → candidate step: *observe / instrument
  before theorizing* (artifact: logs/instrumentation).
- **Divide and conquer** + **Change one thing at a time** — narrow the search by bisection,
  isolating one variable per experiment. → candidate step: *narrow it down by bisection*.
- **Keep an audit trail** — record what you did, what you saw, in what order. → candidate step:
  *keep an investigation ledger* (artifact: audit trail / ledger). Directly maps the locked
  `investigation ledger` surface.
- **If you didn't fix it, it ain't fixed** — prove the fix by making the failure recur, then
  disappear. → candidate step: *prove the fix* (E3 red→green close).
- Source: https://dwheeler.com/essays/debugging-agans.html · https://embeddedartistry.com/blog/2017/09/06/debugging-9-indispensable-rules/

### `julia-evans` — *How I got better at debugging* (Julia Evans, jvns.ca) · **practitioner-account**
Explicitly first-person ("how I…"); practitioner-loved, concrete.
- **Reject magic, assume a logical cause** — "Everything on a computer does in fact happen for a
  logical reason." → framing, sustains the search.
- **Reproduce reliably** — moving "from seeing a bug a few times to being able to reproduce it
  consistently on demand" is treated as the enabling first move. → candidate step: *get a reliable
  repro* (corroborates `agans` "make it fail," independently).
- **Observe actual behavior with tools** — "directly observe what a program is actually doing"
  using strace/tcpdump rather than only reading code. → candidate step: *observe with tools*
  (artifact: traces). Corroborates `agans` "quit thinking and look."
- **Understand exactly what's wrong before fixing** — "leave the bug in place, figure out exactly
  what's gone wrong, and then fix it after understanding what happened." → candidate step:
  *locate root cause before fixing*.
- **Externalize / articulate the unknown** — "ramble into the Slack channel… figure out what I
  don't understand, articulate it, and ask about it." → supporting practice.
- Source: https://jvns.ca/blog/2015/11/22/how-i-got-better-at-debugging/

### `zeller` — *Why Programs Fail: A Guide to Systematic Debugging* (Andreas Zeller) · **methodology-text**
The scientific-method framing, widely applied by practitioners; named here as a methodology text.
- The loop: "(i) Observe a failure, (ii) Invent a hypothesis as to the failure cause… consistent
  with the observations, (iii) Use the hypothesis to make predictions, and (iv) Test the
  hypothesis by experiments and further observations." → candidate steps: *form a hypothesis*,
  *predict → run an experiment → observe*, looping until the cause is found. This is the explicit
  **loop body** the debug spine iterates over.
- Source: https://www.embedded.com/scientific-debugging-finding-out-why-your-code-is-buggy-part-1/ · https://queue.acm.org/detail.cfm?id=1217270

### `uxmag-detective` — *Secrets of Agentic UX* detective/case-file pattern (UX Magazine) · **practitioner-account**
Practitioner write-up of an incident-investigation agent built as a two-panel detective canvas.
- Flow: gather evidence → stream "suggested observations" → human builds a **case file** →
  agent makes an **"accusation" (root-cause hypothesis)** visually elevated above observations →
  closes with **remediation**. → corroborates the symptom→evidence→hypothesis→root-cause→fix arc;
  evidences the **confirm/refute** elevation (E2).
- Source: https://uxmag.com/articles/secrets-of-agentic-ux-emerging-design-patterns-for-human-interaction-with-ai-agents

### `hypothesizer` — *Hypothesizer* hypothesis-based debugger (ACM UIST 2023) · **methodology-text**
- Renders "an investigation plan as a timeline view that summarizes evidence items and marks which
  were confirmed." Controlled study (16 pro devs): 5× fix success, 3× faster. → evidences the
  **confirmed/refuted evidence ledger** as the carrier (E2): per-hypothesis prediction-vs-observed.
- Source: https://dl.acm.org/doi/10.1145/3586183.3606781

### `undo-replay` — agentic / time-travel debugging (Undo.io, Replay.io) · **tool-documented-workflow**
- Reframe: "prove the bug exists, then prove your fix works" — a refuted prediction spawns a new
  hypothesis; the close is a **red→green repro** (failing test, then same test passing). →
  evidences E3 and the loop's exit condition.
- Source: https://undo.io/resources/agentic-debugging-vs-natural-language-interface/

*(Practitioner-account check: `agans`, `julia-evans`, `uxmag-detective` — 3 hands-on accounts. ✓)*

---

## Family: `spike` (spike-runners)

> A single timeboxed pass whose deliverable is a *decision input*, not code. Variant locked as
> `timebox` (2b). E4 (verdict card + `spike_ref`) lives here.

### `xp-spike` — *Spike Solution* (C2 wiki / extremeprogramming.org) · **practitioner-account**
The original XP community describing their own practice.
- **Identify the riskiest unknown** — "The development group identifies which stories are risky to
  complete on time… and does WorstThingsFirst based on a SpikeSolution." → candidate step: *frame
  the risky question*.
- **Timebox (hours)** — spikes were "small timeboxes (typically hours)"; "use a timebox and a
  budget to limit your spike solution." → candidate step: *set the timebox/budget* (the dominant
  status element). Maps the `memo+timebox` surface.
- **Build a throwaway probe** — "Spike solution is design prototype… implemented and evaluated. It
  can be dropped." "Spike solutions are meant to be quick and dirty, not perfect and polished." →
  candidate step: *probe options (throwaway)* (artifact: probes-tried list).
- **Evaluate → conclude** — the probe is "evaluated"; you keep the *learning*, drop the code. →
  candidate step: *land a verdict*.
- Source: http://c2.com/xp/SpikeSolution.html · http://www.extremeprogramming.org/rules/spike.html

### `mike-bowler` — *Why we should stop using spikes* (Mike Bowler) · **practitioner-account**
First-person practitioner critique that restates the discipline by negation.
- **A specific technical question** — "We don't know if it's even possible to implement a specific
  thing in the browser or if we will need to do that on the backend." → candidate step: *pose one
  answerable question*.
- **Strict, short timebox** — original spikes were hours; the lost discipline is the blowout
  (week-long spikes writing production code). → reinforces *hard timebox*.
- **Throwaway code** — "any code done during the spike was throwaway"; separation prevents
  learning from masquerading as delivery. → reinforces *disposable probe*.
- **Feeds a decision** — spikes let teams "make a decision about future work." → candidate step:
  *verdict feeds a downstream decision* (the `spike_ref` linkage; E4).
- Source: https://blog.mikebowler.ca/2023/04/29/spikes/

### `agilemania-spike` — Agile spike stories (Agilemania) · **methodology-text**
- "A timeboxed experiment meant to gather information to reduce risk"; "a time-box should be set,
  and at any point the team can decide they've done enough"; **document the outcome as
  comments/findings linked to the product decision it informs** — "create traceable connections
  between spike findings and related product decisions." → directly evidences the **Verdict Card +
  `spike_ref`** (E4): one-line answer documented and linked to its decision.
- Source: https://agilemania.com/agile-spike-story-what-is-a-spike-in-agile

### `adr-nygard` — Architecture Decision Records (Nygard lineage; MS Well-Architected) · **methodology-text**
The *consumption* end of a spike — where the verdict lands.
- An ADR records "context (the forces), options considered, the decision, the rationale/
  trade-offs, and the consequences"; mature ADRs "record the conditions under which you'd revisit
  a decision" (the **revisit-if** trip-wire). → evidences the verdict's *destination*: the spike's
  conclusion is consumed by a decision record carrying `revisit_if` + `spike_ref`. (Per
  `05-decisions-autonomy.ai.md` Lens 1.)
- Source: https://adr.github.io/ · https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record

*(Practitioner-account check: `xp-spike`, `mike-bowler` — 2 hands-on accounts. ✓)*

---

## Family: `data` (data analysts)

> "Where is this?" is a position in a *pipeline*, not a loop or a path. Variant locked as
> `pipeline` (2b). E5 (rendered report + provenance) lives here. Research note: an inner
> transform↔visualize loop sits inside the linear question→communicate frame (flag for sp2).

### `r4ds` — *R for Data Science* import→tidy→transform→visualize/model→communicate (Hadley Wickham) · **practitioner-account**
The most widely-recognized practitioner workflow; Wickham describing the process he built and uses.
- **Import** — "take data stored in a file, database, or web API and load it into a data frame." →
  candidate step: *import / pull sources* (artifact: loaded dataset).
- **Tidy** — structure so "each column is a variable and each row is an observation." → candidate
  step: *tidy/clean the data*.
- **Transform** — "narrowing… observations, creating new variables… and computing summary
  statistics" (tidy+transform = "wrangling"). → candidate step: *transform/wrangle*.
- **Visualize ↔ Model (the explore loop)** — visualize: "a good visualization will show you things
  you did not expect"; model "cannot fundamentally surprise you"; the two "have complementary
  strengths… so any real data analysis will iterate between them many times." → candidate steps:
  *explore (visualize ↔ model)* — **the inner loop** the pipeline hosts.
- **Communicate** — "an absolutely critical part of any data analysis project" where results are
  conveyed to others. → candidate step: *communicate the answer* (artifact: report/chart). **E5
  home.**
- Source: https://r4ds.hadley.nz/intro · https://r4ds.hadley.nz/

### `dbt-analyst` — analyst workflow (dbt Labs developer hub) · **tool-documented-workflow**
- "Start with a stakeholder question and analyze data to answer that question"; explore/validate
  ("validate shape, quality, and semantics before deeper modeling"); when "analysts identify
  patterns in one-off queries, they can turn them into full dbt models so the work can be shared."
  → candidate steps: *start from a stakeholder question*, *validate source data*, *promote the
  one-off into a shareable report/model* (the notebook→report move).
- Source: https://docs.getdbt.com/guides/analyze-your-data · https://www.getdbt.com/resources/analysts-guide-to-working-with-data-engineering

### `data-sanity` — *A Data Sanity Check Survival Guide* (Manojkumar Marri, Medium) · **practitioner-account**
First-person analyst account of the unglamorous reality.
- Treats cleaning + sanity-checking as "the messiest, but most critical phase"; the analyst's job
  is to "look at data and ask, 'Are you telling me the truth?'" by **validating assumptions and
  cross-examining outliers**. → candidate step: *sanity-check / validate before trusting* — a
  named, real step that R4DS folds into tidy/transform but practitioners call out explicitly.
- Source: https://medium.com/@manojkumar.marri26/climbing-the-right-data-ladder-a-data-sanity-check-survival-guide-b7a91bb3180c

### `looks-good-correll` — *Looks Good To Me: Visualizations As Sanity Checks* (Michael Correll) · **practitioner-account**
Data-viz practitioner on using disposable charts as validation, not just output.
- Sanity checks "rely on a combination of summary statistics and simple visualizations like
  histograms, dot plots, and box-and-whiskers plots" to catch problems early. → reinforces
  *visualize-to-validate* as distinct from *visualize-to-communicate* (informs the inner loop vs
  the E5 headline split).
- Source: https://mcorrell.medium.com/looks-good-to-me-visualizations-as-sanity-checks-6fd1ffa37ab9

### `hex-deepnote` — notebook→report split (Hex / Deepnote, 2026) · **tool-documented-workflow**
- The defining move is "data app/report" output **distinct from** the working notebook: a
  collapsible analysis workspace that **publishes a clean narrative report with the viz as the
  headline.** → evidences the *publish a rendered report* step and the E5 surface shape.
- Source: https://deepnote.com/compare/hex-vs-deepnote

### `atlan-provenance` — data lineage / provenance (Atlan, 2026) · **methodology-text**
- "Lineage is about flow, provenance is about proof" — show "which sources, which transforms, the
  SQL/code that produced the number." → evidences the **provenance drill-in** half of E5 (the
  trust mechanism): *expose source/transform lineage on demand*.
- Source: https://atlan.com/know/data-lineage-tracking/

*(Practitioner-account check: `r4ds`, `data-sanity`, `looks-good-correll` — 3 hands-on accounts. ✓)*

---

## Coverage summary (verification aid — not a derivation)

| Family | Total refs | Practitioner-accounts (≥1 required) | Surfaces touched |
|---|---|---|---|
| `feature` | 5 | 3 (`shape-up`, `linear-method`, `design-docs-google`) | doc · board/ticket · PR-thread/report |
| `debug` | 6 | 3 (`agans`, `julia-evans`, `uxmag-detective`) | investigation ledger · PR-thread/report |
| `spike` | 4 | 2 (`xp-spike`, `mike-bowler`) | memo+timebox |
| `data` | 6 | 3 (`r4ds`, `data-sanity`, `looks-good-correll`) | notebook+chart · PR-thread/report |

**E1–E5 home-step evidence is present** for each family (E1→feature acceptance; E2/E3→debug
ledger+red→green; E4→spike verdict/`spike_ref`; E5→data rendered report+provenance) — sp2 assigns
the single home step per family.

**Flag for sp2 (not a shape change):** the `data` evidence shows an inner transform↔visualize↔model
*loop* nested inside the linear question→communicate `pipeline` frame (R4DS "iterate between them
many times"). This does not contradict the locked `pipeline` variant — it is internal iteration,
not a top-level loop — but sp2 should decide whether the inner loop surfaces as a step or stays
implicit. No `spine-variant revision proposed` flag raised at sp1.

**Out of scope, confirmed not done here:** no spines derived, no step ids assigned, no rubric
scoring, no dropped-placeholder comparison, no canonical note, no `prototype/` touched.
