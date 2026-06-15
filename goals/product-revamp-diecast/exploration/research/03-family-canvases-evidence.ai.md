# Research: Per-Family Canvas Shapes & Output-Evidence Treatments

> **Exploration step:** Step 3 of `exploration/steps.ai.md` — *How should each workflow family's
> canvas be shaped, and how should its output evidence be shown?*
> **Resolves / serves:** US2 (four distinct family clickthroughs), US3 (WHAT-primary, execution
> drill-in), US4 (test & outcome evidence surfaces), FR-006/007/009/016, SC-005 (visibly distinct
> shapes). **Closes the second USER-DEFERRED open question** (evidence presentation patterns per
> family, Q#12).
> **Author:** cast-web-researcher | **Date:** 2026-06-11 | **Method:** 7-angle web research,
> VISION-FIRST (existing Diecast UI is terrain, not anchor).
> **Audience:** the playbook synthesizer + the prototype designer. This is a *design-ready* brief —
> opinionated, cited, ready to mock.

> **Scope discipline:** This note shapes the *interactive canvas* (the live workspace surface) and
> the *output-evidence treatment* per family. It is **separate** from
> `03-workflow-classification-taxonomy.ai.md`, which shaped the *requirements document* per family
> for the refine-requirements-v2 goal. Same four families, two different surfaces: that note answers
> "what does the spec doc look like"; this note answers "what does the working canvas look like and
> how does it prove the WHAT is done."

---

## TL;DR — Recommendation

**Do not build four hand-drawn layouts. Build one canvas *grammar* and let the family deviate it.**
Every family shares the same six zones (header → stage spine → work/iteration zone → **evidence
surface** → execution drill-in → decision chips). What changes per family is (a) the **shape of the
stage spine**, (b) the **iteration treatment**, and (c) the **fitted evidence surface**. This is the
generative-UI consensus for 2026: the UI is "a dynamic output of the system… able to adapt,
reorganize, and respond to user intent and application context" ([CopilotKit][gen-ui]) — but the
*frame* stays constant so the four flows still read as one product (SC-002/SC-004).

**The single most important finding for the prototype:** the contrast SJ needs to demonstrate
(SC-005, "feature vs debug obvious at a glance") is carried almost entirely by **two elements — the
stage spine and the evidence surface.** A feature spine is a *linear backbone* (req→explore→plan→
execute) ending in an **Acceptance Evidence Panel**; a debug spine is a *loop counter* over a
**Confirm/Refute Ledger**. Get those two right per family and the "UI adapts per workflow" claim
proves itself; everything else (chat rail, chrome, vocabulary) is shared and should look identical.

**The four named evidence treatments (resolves Q#12):**

| Family | Canvas codename | Stage spine | Iteration treatment | **Named evidence treatment** |
|---|---|---|---|---|
| **New feature / initiative** | **Backbone Canvas** | Linear phase spine: Requirements → Exploration → Plan → Execution → Done | Phase re-entry stamped on the spine ("Requirements v2 — updated from planning") | **Acceptance Evidence Panel** — UI screenshots + test-run summary + checker-compliance rows, pinned above the fold |
| **Bug fix / debug loop** | **Investigation Board** | Loop spine: Symptom → Hypothesis → Experiment → Observation → (loop) → Root cause → Fix | **Iteration ledger** ("iteration 2/3"), each pass a row of confirmed/refuted hypotheses | **Confirm/Refute Ledger + Red→Green Repro** — predicted vs observed per hypothesis; the failing→passing test is the closing proof |
| **Spike / quick conclusion** | **Timebox Card** | Compressed spine: Question → (timebox meter) → Options probed → Conclusion | Probes-tried list inside one card; no phase re-entry | **Verdict Card** — one-line answer + confidence + the 2-3 data points that decided it + `spike_ref` link to the decision it feeds |
| **Data analysis / research** | **Notebook→Report** | Pipeline spine: Question → Sources → Analysis → Visualized answer | Re-runs as dated report versions; analysis steps collapsible | **Rendered Report + Provenance** — chart/table/HTML answer up top, "show the query/source lineage" drill-in below |

**The single biggest mistake to avoid:** rendering all four as the same generic "agent run timeline"
(the LangSmith/Langfuse trace-tree shape). That trace view is the *execution drill-in* (US3's HOW
tab) — correct for debugging the agent, wrong as the WHAT-level canvas. If the spike and the feature
both open to a span-tree, the contrast dies and the product looks like an observability dashboard,
not an opinionated workspace.

---

## The Shared Canvas Grammar (build once, deviate per family)

All four families render the same six-zone frame. The prototype implements this as one component
with family-keyed slots — cheap to build, and it makes the morph moment (FR-004: chat reshapes the
canvas) a *zone swap*, not a page reload.

1. **Header band (identical chrome).** Classification **pill** (the family name) + **L1 line**
   (the job statement for feature/initiative; the *question* for debug/spike/analysis) + status +
   the **nudged next step rendered as the visually-primary action** (FR-003, US1 S4). Same band in
   all four flows — this is what makes them one product.
2. **Stage spine (the per-family differentiator #1).** A linear backbone, a loop counter, a timebox
   meter, or a pipeline — see each family below. This zone alone carries most of SC-005.
3. **Work / iteration zone.** Where the live or last pass lives, and where **iteration history**
   renders as first-class (FR-007) — never hidden repeat passes.
4. **Evidence surface (the per-family differentiator #2).** The fitted output-evidence treatment
   (US4). First-class, above the fold, not a buried log.
5. **Execution drill-in (shared, WHAT-primary).** One tab into the HOW: run list → dispatch tree →
   maker-checker loop with rework budget (US3 S2). This is where the generic agent trace lives, and
   it's the same component for all families.
6. **Decision chips (shared).** In-context decision records (US10) — small chips on the relevant
   zone, drill-in to the full record; L3 reversibility surfaces the escalation rail at WHAT level.

**Why a shared grammar is the right call (2026 evidence):** CopilotKit's three generative-UI
patterns — *static component selection* (frontend owns architecture, agent fills slots),
*declarative spec rendering*, and *embedded surface* — all assume a host frame the agent populates,
not a free-redrawn page ([CopilotKit guide][gen-ui-2026]). For a static prototype, **static
component selection** is exactly right: we author the six zones and the four family variants, and the
"agent" just picks which variant + fills fake data. The AG-UI lifecycle (started → streaming →
finished/failed) is the progress vocabulary to mimic in the stage spine ([CopilotKit][gen-ui-2026]).

---

## 1. Expert-Practitioner Insights

**The detective/case-file model is the single best-validated pattern for the debug family.** UX
Magazine's "Secrets of Agentic UX" describes an incident-investigation agent built exactly as a
*two-panel detective canvas*: workers gather evidence asynchronously and stream "suggested
observations" into a right-side panel; the human marks relevant ones, building a **case file on the
left**; the agent then makes an **"accusation" (root-cause hypothesis)** visually distinguished from
routine suggestions, and closes with **remediation recommendations** — a sequential card flow
*diagnosis → hypothesis → recommendation*, plus persistent **start/stop/pause** controls to prevent
"Sorcerer's Apprentice" runaway ([UX Magazine][uxmag]). This is a ready-made blueprint for the
**Investigation Board**: evidence accumulates, hypotheses are visually elevated above observations,
and the resolution is a distinct card — not a log line.

**Hypothesis-based debugging has measured UX wins — and a timeline is the carrier.** *Hypothesizer*
(UIST 2023) is a hypothesis-driven debugger: it surfaces candidate hypotheses, identifies code
evidence to test each, and renders an **investigation plan as a timeline view that summarizes
evidence items and marks which were confirmed in the recording.** A controlled study (16 pro devs)
found it improved defect-fix success **5×** and cut debugging time **3×** vs traditional tools
([Hypothesizer, ACM UIST][hypothesizer]). Takeaway: the debug canvas's spine should be a
**confirmed/refuted evidence timeline**, not a flat step log — the confirm/refute marking is the
mechanism that produces the trust and speed.

**The scientific-debugging reframe — "prove the bug exists, then prove the fix works."** The
agentic-debugging literature frames the loop as closed-loop validation: a hypothesis *generates a
prediction*, execution *validates or refutes* it, and a refuted prediction spawns a new hypothesis —
the shift is from "what do you think is wrong?" to **"prove the bug exists, then prove your fix
works"** ([Undo.io agentic debugging][undo], [Replay time-travel][replay]). For the canvas this
means the close of a debug loop is a **Red→Green repro** (failing test → same test passing), and each
hypothesis row carries an explicit **prediction vs observation** pair.

**Spikes are timeboxed risk-burn-down whose deliverable is a *decision input*, not code.** The Agile
canon is unanimous: a spike is "a timeboxed experiment meant to gather information to reduce risk,"
keep it small (hours to ≤1-2 sprints), "a time-box should be set, and at any point the team can
decide they've done enough," and **document the outcome as comments/findings linked to the product
decision it informs** — "create traceable connections between spike findings and related product
decisions" ([Agilemania][spike-agilemania], [Hello Bonsai][spike-bonsai]). This is the literal
spec for `spike_ref` (FR-016): the spike canvas is a **timebox meter + a Verdict Card that a decision
links back to.**

**Data analysis has split into four lanes — pick the *notebook→report* lane.** The 2026 landscape
divides into chat-first analysts (ChatGPT/Claude), notebook/workspace tools (Hex, Deepnote),
spreadsheet-first (Julius, Rows), and warehouse/BI-native (BigQuery/Power BI Copilot)
([BuildMVPFast][data-lanes]). For Diecast's canvas the relevant model is **notebook-to-report**: an
analysis *workspace* (steps you can inspect) that **publishes a clean, narrative report with the
viz as the headline** — Hex's defining move is "data app/report" output distinct from the working
notebook ([Deepnote vs Hex][hex-deepnote]). The canvas should mirror this: a collapsible analysis
spine, a **pinned visualized answer**, and provenance on demand.

**Synthesis:** each family has a *native* expert UX that is decades-validated — feature work →
phase/backbone (RFC→design→build→verify); debug → detective case-file + hypothesis timeline; spike →
timebox + decision memo; analysis → notebook→report. The prototype should adopt the *native* shape
per family, not impose the feature backbone on all four.

**Sources:** [UX Magazine — Secrets of Agentic UX][uxmag] · [Hypothesizer (UIST 2023)][hypothesizer]
· [Undo.io — agentic debugging][undo] · [Replay — time-travel debugging][replay] ·
[Agilemania — spike stories][spike-agilemania] · [Hello Bonsai — Kanban spike][spike-bonsai] ·
[BuildMVPFast — best AI for data analysis 2026][data-lanes] · [Deepnote vs Hex 2026][hex-deepnote]

---

## 2. Tool / Product Landscape (how 2026 tools present run evidence)

| Tool (2026) | Native work-type | How outcome/evidence is shown | Lift for Diecast |
|---|---|---|---|
| **Devin / Codex Cloud / Cursor Cloud** | Async coding task | Returns a **PR as the artifact**; PR diff + auto code-review comments are the evidence ([Totalum][totalum], [ToolChase][toolchase]) | The feature family's "done" state = PR link + diff, but Diecast elevates **screenshots + tests** above the PR |
| **Devin Computer Use** | UI/browser verification | Agent **takes screenshots at checkpoints** to verify layout/styling, logs each action ([Devin docs][devin-cu]) | Source of the **Acceptance Evidence Panel** screenshot strip |
| **ProofShot** | Visual proof bundle | Records the browser session → **synchronized video + key-moment screenshots + console/server errors + an interactive action timeline**, in a standalone HTML viewer ([ProofShot][proofshot], [HN][proofshot-hn]) | The canonical "evidence bundle" UX; the feature family's evidence surface is a static mock of this |
| **Hex / Deepnote / Julius** | Data analysis | Notebook of steps → **published report/data-app with charts as headline**; conversational query → chart you can reuse ([Hex-Deepnote][hex-deepnote], [BuildMVPFast][data-lanes]) | The **Notebook→Report** canvas + Rendered-Report evidence |
| **LangSmith / Langfuse / Laminar** | Agent run trace | **Trajectory/span tree**: nested tool calls, reasoning steps, timeline replay, agent-graph view; "the full sequence of tool calls and decisions" ([Braintrust][braintrust], [Langfuse][langfuse]) | This is the **execution drill-in (HOW tab)**, *not* the WHAT canvas — reuse for US3 S2 only |
| **Replay / Hypothesizer / TTD** | Debug session | **Time-travel timeline**: rewind execution, evidence items marked confirmed; hypothesis timeline ([Replay][replay], [Hypothesizer][hypothesizer]) | The **Investigation Board** spine + Confirm/Refute Ledger |
| **Jira / Linear** | Spike issue type | Timeboxed issue; **findings documented as comments linked to the decision** ([Agilemania][spike-agilemania]) | The **Timebox Card** + `spike_ref` linkage |

**The crucial distinction this table makes explicit:** the observability tools (LangSmith/Langfuse)
and the outcome tools (ProofShot/Hex/PRs) answer *different questions*. Observability = "what did the
agent do?" (process, HOW). Outcome tools = "is the work good?" (result, WHAT). **Diecast's canvas is
a WHAT surface; the trace tree belongs behind the execution tab.** Putting a span-tree on the canvas
is the #1 mistake (TL;DR). The four families differ precisely in their *outcome* tool analog, which
is why each gets a different evidence surface.

**Sources:** [Totalum — best AI coding agents 2026][totalum] · [ToolChase — Codex vs Devin vs Cursor][toolchase]
· [Devin — Computer Use][devin-cu] · [ProofShot][proofshot] · [ProofShot HN][proofshot-hn] ·
[Braintrust — best LLM tracing 2026][braintrust] · [Langfuse — agent observability][langfuse] ·
[Hex vs Deepnote 2026][hex-deepnote]

---

## 3. AI/ML Approaches (the loop these surfaces are presenting)

The underlying engine for every family is the **agentic loop**: perceive → reason → act → observe →
repeat ([ikangai][agentic-loop]). The families differ in *how many loops are exposed and what closes
them*:

- **Feature** hides most loops (maker-checker runs behind the execution tab) and exposes **phase
  progression** — the loop is the rework budget, surfaced only on drill-in.
- **Debug** *makes the loop the whole point* — hypothesis→experiment→observation→hypothesis is
  surfaced as the spine, because the value is watching the search converge ([Undo][undo]).
- **Spike** runs a **bounded loop** (try options until timebox or confidence) and exposes only the
  *count of probes* + the verdict.
- **Analysis** runs a **DAG, not a loop** (question → sources → transforms → viz) and exposes the
  pipeline with the answer pinned.

**Trust calibration is the design constraint that decides how much loop to show.** The research is
sharp here: "confident explanations can *increase* overreliance precisely because they reduce
friction and critical reflection"; good systems "help people recognize ambiguity, compare
alternatives, and know when intervention is necessary," using **uncertainty/confidence indicators**
and **stepwise, adaptive rationales** ([Designative — trust calibration][trust-calib]). Concretely:
the Verdict Card carries a **confidence level**; the Confirm/Refute Ledger shows **alternatives
considered and rejected**; the Acceptance Panel shows **checker flags, not just a green badge** (US4
S3). Trust comes from *showing what was ruled out*, not from a confident summary.

**Sources:** [ikangai — the agentic loop][agentic-loop] · [Undo.io][undo] ·
[Designative — trust calibration in agentic AI (2026)][trust-calib]

---

## 4. Community & Open Source

- **ProofShot** (open-source CLI, HN Show 2026): the community's answer to "give agents eyes" — a
  proof bundle of **video + screenshots + errors + action timeline** in a standalone HTML viewer
  ([ProofShot][proofshot], [HN][proofshot-hn]). Directly mockable as the feature-family evidence
  surface; its "synchronized timeline + key-moment screenshots" is the exact layout to fake.
- **Chrome DevTools MCP** and QA-agent patterns: independent black-box QA agents "treat deployed apps
  like real users — clicking, navigating, verifying — and return QA snapshots, visual bug reports,
  and logs back into the chat" ([DEV — vibe code with confidence][devto-qa]). Supports the pattern
  of **promoting a chat-produced QA snapshot onto the canvas** (US1 S3, FR-005).
- **AG-UI / A2UI / Open-JSON-UI** (CopilotKit-stewarded protocols): the open standards for
  agent→frontend UI, defining tool lifecycles and state updates ([CopilotKit generative-ui repo][gen-ui-repo]).
  Validates the "static component selection" build choice for the prototype.
- **Spike practice (Agile community):** the canonical "document findings as comments, link to the
  decision" workflow is the open consensus the Timebox Card formalizes ([Agilemania][spike-agilemania]).
- **Jupyter/notebook lineage:** the notebook→published-report split is community-standard (Hex data
  apps, Deepnote, Observable) — the analysis canvas should not invent a new shape here.

**Sources:** [ProofShot][proofshot] · [ProofShot HN][proofshot-hn] · [DEV — QA agents][devto-qa] ·
[CopilotKit generative-ui repo][gen-ui-repo] · [Agilemania — spikes][spike-agilemania]

---

## 5. Frameworks & Patterns (the reusable primitives)

**Progressive disclosure is the master pattern — three tiers, outcome-first.** The agentic-design
canon specifies exactly three disclosure layers: **Summary** (the result/recommendation only) →
**Detailed** (reasoning steps, decision factors) → **Technical** (full trace, tokens, internals),
with rules: *lead with the final answer*, expandable supporting data, consistent expand/collapse
iconography, **max 3-4 nesting depths**, never hide critical info behind multiple clicks
([Agentic Design — progressive disclosure][agentic-pd]). This maps 1:1 onto Diecast's US3:
**Summary = the WHAT canvas; Detailed = the evidence surface; Technical = the execution tab.** The
same three tiers apply *inside* each evidence treatment (e.g., Acceptance Panel: green summary →
screenshots+test counts → full test log).

**API-agent vs GUI-agent visibility framing.** The literature contrasts API agents (outcome-only,
"final outcome without knowing which endpoints were invoked") with GUI agents (every action visible)
([API vs GUI agents][api-gui]). Diecast's families pick deliberately per type: **feature/spike are
API-agent-like** (show outcome, hide the loop); **debug is GUI-agent-like** (show every
observation). The canvas grammar lets each family choose its visibility default while keeping
drill-in available.

**The generative-UI binding pattern (for the morph).** Task type → UI variant is the core 2026
generative-UI move: "travel queries → itinerary cards + map; comparison queries → sortable tables;
contact workflows → forms" ([CopilotKit guide][gen-ui-2026]). Diecast's analog: "feature → backbone
spine; bug → loop ledger; spike → timebox card; analysis → notebook→report." The chat-morph (FR-004)
is implemented as **re-binding the canvas to a different family variant** — CSS-transitioned zone
swaps keyed to scripted chat steps (matches the spec's directional idea).

**Sources:** [Agentic Design — progressive disclosure patterns][agentic-pd] ·
[API Agents vs GUI Agents (arXiv 2503.11069)][api-gui] · [CopilotKit — generative UI 2026][gen-ui-2026]

---

## 6. Contrarian View

**"Four distinct canvases" risks four maintenance burdens and a disoriented user.** The contrarian
read: most successful agent products (Devin, Cursor, ChatGPT) ship **one** surface and let *content*
vary, not *chrome*. If Diecast's four canvases diverge too much, (a) the prototype is 4× the build,
and (b) a user who learns the feature flow is lost in the debug flow. **Counter-design:** this is why
the recommendation is a *shared grammar with two deviating zones*, not four bespoke layouts. The
header, drill-in, decision chips, and chat rail are pixel-identical across families; only the stage
spine and evidence surface change. That preserves contrast (SC-005) *and* coherence (SC-002/004).

**"Show your work" can backfire — more transparency ≠ more trust.** Confident, detailed explanations
can *increase* overreliance ([Designative][trust-calib]); and a 2,000-span agent trace is "slower to
read" even for experts ([Braintrust][braintrust]). So the contrarian warning is real: **do not make
the trace the hero.** The product's posture (WHAT-primary, "AI keeps execution somewhat blackbox" —
spec Intent §3) is *correct* and trust-research-aligned: lead with outcome + evidence, keep the
process one click away. The debug family is the deliberate exception — there the *process is the
product*, so it gets the loop on the spine.

**Spikes shouldn't look like mini-features.** A contrarian failure mode is rendering the spike with
the feature backbone (req→explore→plan→execute) shrunk down. That destroys the "this is timeboxed,
disposable, decision-feeding" signal. The Timebox Card must look *materially lighter* — a single card
with a budget meter, not a phase spine — or the family collapses back into the feature pipeline (the
exact "everything is one tight pipeline" failure the goal exists to escape).

**Sources:** [Designative — trust calibration][trust-calib] · [Braintrust — tracing 2026][braintrust]

---

## 7. First Principles

Strip to fundamentals: **a canvas exists to answer two questions at a glance — "where is this?" and
"is it good?"** "Where is this?" is the **stage spine**; "is it good?" is the **evidence surface**.
Everything else is secondary. The families differ because *the shape of "where" and the form of
"good" are intrinsically different per work type*:

- A **feature**'s "where" is a position on a known path (you know the phases in advance) → a
  **linear spine**. Its "good" is "does it do what was asked and not break things" → **screenshots +
  passing tests + checker compliance** (acceptance evidence).
- A **bug**'s "where" is *unknown until found* (you're searching, not progressing) → a **loop with a
  counter**, because there's no fixed number of steps. Its "good" is "the bug is gone *and we can
  prove the fix*" → **the failing test now passes** (red→green is the only honest proof a bug is
  fixed).
- A **spike**'s "where" is "how much budget is left" → a **timebox meter**. Its "good" is "we can now
  make the decision" → **a verdict the decision links to** (the answer's value is *external*, in the
  decision it unblocks).
- An **analysis**'s "where" is a position in a *data pipeline* → a **DAG/notebook spine**. Its "good"
  is "the answer is visible and you can check where it came from" → **a rendered viz + provenance**.

From first principles, then, the four evidence treatments are not stylistic choices — they're forced
by what "done well" *means* for each work type. This is the deep reason the contrast is legible: a
viewer feels the difference because the *proof of done is genuinely different*. That is the
defensible answer to Q#12.

---

## The Four Family Blueprints (the deliverable)

Each blueprint = stage model + canvas layout (the six zones, family-specialized) + iteration
treatment + named evidence treatment. All reuse the canonical fake-data spine (CAST-412,
M04/S03/R02, rework budget 1/3, crud-orchestrator) where it fits.

### Family 1 — New Feature / Initiative → **Backbone Canvas**

**Stage model (linear spine):** `Requirements → Exploration → Plan → Execution → Done`. The richest
flow; this is the backbone the other three contrast against. Current phase highlighted; completed
phases checked; the **nudged next step** is the primary CTA in the header.

**Canvas layout:**
- *Header:* feature pill + job statement (L1) + "Execution · 2 of 5 tickets done" + primary nudge
  ("Review CAST-412's PR").
- *Stage spine:* horizontal 5-node backbone across the top; each node clickable to that phase's
  surface.
- *Work zone:* WHAT content — outcome, progress, the requirements doc surface (US7) reachable here.
- *Evidence surface:* **Acceptance Evidence Panel** (below).
- *Execution drill-in:* "Execution" tab → run list → one run's 13-sub-agent dispatch tree →
  maker-checker loop with rework budget 1/3 and named exits (fix/retry/escalate) (US3 S2). **This is
  where the LangSmith-style trace tree lives.**
- *Decision chips:* on the requirements doc and on tickets; L3 surfaces the escalation rail.

**Iteration treatment:** phase **re-entry stamped on the spine** — e.g., "Requirements v2 · updated
from planning" with the living-source-of-truth notification (US7 S4). Re-entered phases show a small
version badge, not a reset.

**Named evidence treatment — Acceptance Evidence Panel.** A pinned, above-the-fold panel with three
fitted rows (modeled on ProofShot's bundle + Devin computer-use screenshots):
1. **UI screenshots strip** — key-moment screenshots of the built UI (before/after where relevant),
   like Devin's checkpoint screenshots ([Devin CU][devin-cu]) and ProofShot's key frames
   ([ProofShot][proofshot]).
2. **Test-run summary** — "47 passed / 0 failed", coverage delta, link to full log (progressive
   disclosure: badge → counts → log).
3. **Checker compliance rows** — the maker-checker rule checks passed/flagged (M04/S03/R02 shown as
   resolved/flagged), *not just a pass badge* (US4 S3) — the trust-calibration "show what was
   checked" principle.
   Plus the **PR link** (the Devin/Codex outcome convention) as the artifact pointer.

---

### Family 2 — Bug Fix / Debug Loop → **Investigation Board**

**Stage model (loop spine):** `Symptom → Hypothesis → Experiment → Observation → ↺ → Root cause →
Fix`. Maximally different from the backbone *on purpose* (SC-005). The spine is a **loop with an
iteration counter**, not a linear path — because the number of passes is unknown until the bug is
found (first-principles §7).

**Canvas layout (detective case-file, per [UX Magazine][uxmag]):**
- *Header:* bug pill + the *symptom as the L1 question* ("Checkout 500s on coupon apply") +
  "Iteration 2/3" + nudge ("Run experiment for H3").
- *Stage spine:* the loop, with a prominent **iteration counter** (FR-007, US2 S2).
- *Work zone — two panels:* **left = evidence/case-file** (observations the run has accepted);
  **right = live hypotheses** streaming in. Hypotheses are *visually elevated* above observations
  (the "accusation" treatment).
- *Evidence surface:* **Confirm/Refute Ledger + Red→Green Repro** (below).
- *Execution drill-in:* the agent trace for the experiment runs (time-travel/replay analog).
- *Decision chips:* "ruled out caching (H1) — see decision."

**Iteration treatment — the hero of this family.** An **iteration ledger**: each pass is a row, each
hypothesis carries **prediction vs observation** and a **confirmed/refuted** mark (the Hypothesizer
timeline, [UIST 2023][hypothesizer]). Refuted hypotheses stay visible (you learn from the search) —
"iteration 2/3" with H1 refuted, H2 refuted, H3 confirmed. This is the maximally-different shape that
proves the canvas adapts.

**Named evidence treatment — Confirm/Refute Ledger + Red→Green Repro.** Two parts:
1. **Confirm/Refute Ledger** — per hypothesis: *what we predicted* → *what we observed* →
   confirmed/refuted, with alternatives ruled out shown (trust calibration, §3).
2. **Red→Green Repro** — the closing proof: the failing repro test, then the *same test passing*
   after the fix ("prove the bug exists, then prove your fix works", [Undo][undo]). A green badge
   alone is insufficient — the honest proof is the formerly-red test now green.

---

### Family 3 — Spike / Quick Conclusion → **Timebox Card**

**Stage model (compressed):** `Question → (timebox) → Options probed → Conclusion`. Deliberately
*lighter* than every other family — one card, not a spine (contrarian §6: a spike must not look like
a mini-feature).

**Canvas layout:**
- *Header:* spike pill + the *question as L1* ("Can we use SQLite for the event store?") + a
  **timebox/budget meter** ("3h box · 1h 40m used") as the dominant status element.
- *Work zone — single card:* the **probes-tried list** (options explored with a one-line result
  each), inline. No phase re-entry, no dispatch tree by default.
- *Evidence surface:* **Verdict Card** (below).
- *Execution drill-in:* optional, minimal — a spike usually doesn't warrant the full trace.
- *Decision chips:* the spike's conclusion is *referenced by* a decision elsewhere — the
  **`spike_ref` linkage** is shown both directions (US2 S3, FR-016).
- *Terminal-parity host:* per FR-017, the spike flow hosts the one side-by-side terminal/canvas
  moment — a terminal pane invoking the same skill next to the canvas doing it with defaults.

**Iteration treatment:** *none in the heavy sense* — a spike is one timeboxed pass. "Iteration" here
is the **list of probes tried within the box** (which approaches were spiked), not re-entered phases.

**Named evidence treatment — Verdict Card.** A single decision-memo card (the Agile "document
findings, link to the decision" pattern, [Agilemania][spike-agilemania]):
- **One-line answer** ("Yes — SQLite is sufficient to 10k events/s; revisit at sharding").
- **Confidence level** (high/medium/low — the trust-calibration indicator, §3).
- **The 2-3 data points that decided it** (the minimum evidence, not a report).
- **`spike_ref` link** to the decision/ticket it feeds — the spike's value is *external*, so the link
  is first-class, not a footnote.

---

### Family 4 — Data Analysis / Research → **Notebook→Report**

**Stage model (pipeline/DAG):** `Question → Sources → Analysis → Visualized answer`. A pipeline, not
a loop — mirrors the Hex/Deepnote notebook→report split ([Hex-Deepnote][hex-deepnote]).

**Canvas layout:**
- *Header:* analysis pill + the *question as L1* ("Which onboarding step drops the most users?") +
  status + nudge.
- *Stage spine:* the pipeline — Sources → Analysis → Answer; each node opens its detail.
- *Work zone:* the **analysis steps as collapsible cells** (notebook lane) — query/transform steps
  inspectable but collapsed by default (progressive disclosure).
- *Evidence surface:* **Rendered Report + Provenance** (below) — the headline.
- *Execution drill-in:* the agent's analysis run.
- *Decision chips:* findings that fed a decision.

**Iteration treatment:** re-runs render as **dated report versions** ("Report v2 · re-run on fresh
data"), analysis cells collapsible so the history doesn't bury the answer (US4 S1 — "visualized
output, not prose-only").

**Named evidence treatment — Rendered Report + Provenance.** Two layers:
1. **The visualized answer up top** — chart/table/rendered HTML as the headline (US2 S4, US4 S1), the
   Hex "data app / report" convention. Never prose-only.
2. **Provenance on demand** — "show the query / source lineage": which sources, which transforms,
   the SQL/code that produced the number ([Atlan — lineage][lineage]; "lineage is about flow,
   provenance is about proof"). This is the analysis family's trust mechanism — the analog of the
   debug family's confirm/refute and the feature family's checker rows.

---

## Named Evidence-Treatment Catalog (one-glance reference)

| # | Name | Family | What it shows | Closest 2026 precedent |
|---|---|---|---|---|
| E1 | **Acceptance Evidence Panel** | Feature | UI screenshots + test summary + checker-compliance rows + PR link | ProofShot bundle + Devin computer-use screenshots |
| E2 | **Confirm/Refute Ledger** | Debug | Per-hypothesis prediction vs observation, confirmed/refuted, alternatives ruled out | Hypothesizer evidence timeline (UIST 2023) |
| E3 | **Red→Green Repro** | Debug (close) | The failing repro test, then the same test passing post-fix | Scientific-debugging "prove bug, prove fix" (Undo/Replay) |
| E4 | **Verdict Card** | Spike | One-line answer + confidence + 2-3 deciding data points + `spike_ref` | Agile spike findings → decision linkage |
| E5 | **Rendered Report + Provenance** | Analysis | Headline viz/table/HTML + show-the-query lineage drill-in | Hex/Deepnote report + data-lineage trust views |

These five (E1-E5) are the concrete answer to the deferred Q#12. They share one rule — **outcome
first, proof one click in, full trace two clicks in** (progressive disclosure, §5) — and differ only
in the *form of proof*, which is forced by the work type (§7).

---

## Cross-Family Synthesis & Anti-Patterns

**What's shared (build once):** header band, decision chips, execution drill-in (the trace tree),
chat rail, the three-tier progressive-disclosure rule, and the canonical fake-data spine.

**What deviates (the contrast, build four variants):** the **stage spine** (linear backbone / loop
counter / timebox meter / pipeline) and the **evidence surface** (E1-E5). These two zones carry
SC-005 almost entirely.

**The morph moment (FR-004):** "this is actually a bug, not a feature" re-binds the canvas from the
Backbone variant to the Investigation Board variant — a CSS-transitioned **zone swap** (header stays,
spine morphs linear→loop, evidence surface morphs E1→E2), goal context preserved. Because it's one
component with family-keyed slots, the morph is cheap and visibly dramatic — exactly the "fluidity
demonstrated, not described" requirement.

**Anti-patterns to avoid (each tied to a source):**
- **Trace-tree-as-canvas** — putting the LangSmith/Langfuse span tree on the WHAT surface. It's the
  HOW tab. ([Braintrust][braintrust]: 2,000-span runs are slow even for experts.)
- **Green-badge-only done** — a pass/fail badge with no checker rows / no red→green repro. Violates
  US4 S3 and trust calibration ([Designative][trust-calib]).
- **Spike-as-mini-feature** — shrinking the backbone spine for spikes; destroys the timebox signal.
- **Prose-only analysis** — an analysis answer as text without the viz (US2 S4 explicitly bans this).
- **Hidden iterations** — collapsing debug passes or report re-runs into a single "latest" with no
  history (violates FR-007; Hypothesizer's whole value is the visible confirmed/refuted history).
- **Confidence theater** — a confident summary with no uncertainty indicator or alternatives;
  *increases* overreliance ([Designative][trust-calib]). Every evidence treatment carries a
  confidence/flag signal.

---

## Open Questions / Hand-off Notes

- **Resolves [USER-DEFERRED: evidence presentation patterns per family] (Q#12)** with the E1-E5
  catalog above. Recommend the playbook synthesizer lock these names into the design system so the
  four flows mock consistently.
- **One genuinely-open sub-choice for the owner:** for the **feature family**, whether the PR/diff is
  shown *on the canvas* (Devin/Codex convention) or confined to the execution tab. Recommendation:
  **link on canvas, diff in the tab** — keeps the WHAT surface about acceptance evidence (screenshots
  + tests), not raw code. Flagging as a taste call, not a blocker.
- **Dependency on Step 2 (canvas + chat mechanics):** the zone-swap morph mechanic is specified there;
  this note assumes the six-zone grammar is the swap unit. Keep them consistent.
- **Reuse note:** preso a08-a11 (board/ticket/decision/escalation) feed the *execution drill-in* and
  decision chips, not the evidence surfaces — the evidence treatments (E1-E5) are net-new design.

---

## Consolidated Sources

- UX Magazine — Secrets of Agentic UX (detective/case-file pattern): https://uxmag.com/articles/secrets-of-agentic-ux-emerging-design-patterns-for-human-interaction-with-ai-agents
- Hypothesizer — hypothesis-based debugger, evidence timeline (ACM UIST 2023): https://dl.acm.org/doi/10.1145/3586183.3606781
- Undo.io — agentic debugging vs natural-language interface (prove bug / prove fix): https://undo.io/resources/agentic-debugging-vs-natural-language-interface/
- Replay.io — time-travel debugging + Replay MCP: https://blog.replay.io/replay-time-travelogue:-improving-nadia's-%22debugging-with-ai%22-results-using-replay-mcp
- Agilemania — Agile spike stories (timebox + decision linkage): https://agilemania.com/agile-spike-story-what-is-a-spike-in-agile
- Hello Bonsai — Kanban spike / timeboxing: https://www.hellobonsai.com/blog/what-is-spike-in-agile
- BuildMVPFast — Best AI for Data Analysis June 2026 (four lanes): https://www.buildmvpfast.com/articles/best-llms-2026-guide/data-analysis-ai
- Deepnote — Hex vs Deepnote 2026 (notebook→report): https://deepnote.com/compare/hex-vs-deepnote
- ProofShot — visual proof bundle for AI-built code: https://github.com/AmElmo/proofshot · https://proofshot.argil.io/
- ProofShot — Show HN: https://news.ycombinator.com/item?id=47499672
- Devin — Computer Use (checkpoint screenshots): https://docs.devin.ai/work-with-devin/computer-use
- Totalum — Best AI Coding Agents 2026: https://www.totalum.app/blog/best-ai-coding-agents-2026
- ToolChase — Codex vs Devin vs Cursor vs Claude Code 2026: https://toolchase.com/blog/ai-coding-agents-2026/
- Braintrust — Best LLM tracing tools for multi-agent systems 2026: https://www.braintrust.dev/articles/best-llm-tracing-tools-2026
- Langfuse — AI agent observability/tracing: https://langfuse.com/blog/2024-07-ai-agent-observability-with-langfuse
- CopilotKit — Generative UI (overview): https://www.copilotkit.ai/generative-ui
- CopilotKit — Developer's Guide to Generative UI in 2026: https://www.copilotkit.ai/blog/the-developer-s-guide-to-generative-ui-in-2026
- CopilotKit — generative-ui repo (AG-UI / A2UI / MCP Apps): https://github.com/CopilotKit/generative-ui
- Agentic Design — Progressive Disclosure UI patterns: https://agentic-design.ai/patterns/ui-ux-patterns/progressive-disclosure-patterns
- Designative — Trust Calibration in Agentic AI (2026): https://www.designative.info/2026/05/21/trust-calibration-in-agentic-ai-designing-for-appropriate-reliance-not-blind-trust/
- API Agents vs GUI Agents (arXiv 2503.11069): https://arxiv.org/pdf/2503.11069
- ikangai — The Agentic Loop Explained: https://www.ikangai.com/the-agentic-loop-explained-what-every-pm-should-know-about-how-ai-agents-actually-work/
- DEV — Vibe Code with Confidence: Testing AI-Built Apps with QA Agents: https://dev.to/appdeploy/vibe-code-with-confidence-testing-ai-built-apps-with-qa-agents-2e14
- Atlan — Data Lineage Tracking Guide 2026 (provenance vs lineage): https://atlan.com/know/data-lineage-tracking/

---

## Reference-Link Map

[gen-ui]: https://www.copilotkit.ai/generative-ui
[gen-ui-2026]: https://www.copilotkit.ai/blog/the-developer-s-guide-to-generative-ui-in-2026
[gen-ui-repo]: https://github.com/CopilotKit/generative-ui
[uxmag]: https://uxmag.com/articles/secrets-of-agentic-ux-emerging-design-patterns-for-human-interaction-with-ai-agents
[hypothesizer]: https://dl.acm.org/doi/10.1145/3586183.3606781
[undo]: https://undo.io/resources/agentic-debugging-vs-natural-language-interface/
[replay]: https://blog.replay.io/replay-time-travelogue:-improving-nadia's-%22debugging-with-ai%22-results-using-replay-mcp
[spike-agilemania]: https://agilemania.com/agile-spike-story-what-is-a-spike-in-agile
[spike-bonsai]: https://www.hellobonsai.com/blog/what-is-spike-in-agile
[data-lanes]: https://www.buildmvpfast.com/articles/best-llms-2026-guide/data-analysis-ai
[hex-deepnote]: https://deepnote.com/compare/hex-vs-deepnote
[proofshot]: https://github.com/AmElmo/proofshot
[proofshot-hn]: https://news.ycombinator.com/item?id=47499672
[devin-cu]: https://docs.devin.ai/work-with-devin/computer-use
[totalum]: https://www.totalum.app/blog/best-ai-coding-agents-2026
[toolchase]: https://toolchase.com/blog/ai-coding-agents-2026/
[braintrust]: https://www.braintrust.dev/articles/best-llm-tracing-tools-2026
[langfuse]: https://langfuse.com/blog/2024-07-ai-agent-observability-with-langfuse
[agentic-pd]: https://agentic-design.ai/patterns/ui-ux-patterns/progressive-disclosure-patterns
[trust-calib]: https://www.designative.info/2026/05/21/trust-calibration-in-agentic-ai-designing-for-appropriate-reliance-not-blind-trust/
[api-gui]: https://arxiv.org/pdf/2503.11069
[agentic-loop]: https://www.ikangai.com/the-agentic-loop-explained-what-every-pm-should-know-about-how-ai-agents-actually-work/
[devto-qa]: https://dev.to/appdeploy/vibe-code-with-confidence-testing-ai-built-apps-with-qa-agents-2e14
[lineage]: https://atlan.com/know/data-lineage-tracking/
