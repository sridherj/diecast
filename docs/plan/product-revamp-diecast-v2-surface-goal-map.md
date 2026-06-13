# Product Revamp: Diecast - v2 Surface -> Buildable-Goal Map (SC-006)

> **Authored by** sub-phase 6.3b (`cast-subphase-runner`, run `run_20260612_093951_09b9bc`) on
> 2026-06-12, off the Phase 6 critical path, doc-only (touches no `prototype/` file). This is the
> **SC-006 deliverable**: the input document for the **post-mockup v2 planning session**. SC-006 is
> satisfiable the moment that session convenes with this map in hand.

## How to read this map (preamble)

The vision prototype (`prototype/index.html`, content-final after Phase 6.2) is a clickable mockup:
every screen is a pure projection of a frozen fake org (`window.ORG`) through `render(appState)`,
steered by a **scripted** chat engine (`SCRIPTS`). Nothing executes. This map answers the only
question that matters for v2: **for each thing the prototype shows, what is the named, buildable
follow-on goal that makes it real?**

**Column contract (every row obeys it):**

- **Surface / Route** - the hash route as shipped, or the named cross-cutting mechanic.
- **What it proves** - the FR / US / SC references the surface demonstrates in the mockup.
- **Follow-on v2 goal** - a **kebab-case slug** plus a **one-line OUTCOME sentence** stating what is
  true when the goal is done. Never a vague theme ("improve the board" is banned); always a concrete,
  testable end-state.
- **Size** - S (a few days), M (1-2 weeks), L (multi-week / needs its own decomposition). Advisory
  sizing only; each v2 goal runs its own refine -> plan loop.
- **Depends on** - other v2 goal slugs that must land first (build-order edges).
- **Suggested rank** - **ADVISORY ONLY.** The numbers seed the stack-ranking conversation; **the v2
  planning session owns the final order.** Ranks are a single global sequence (1 = earliest) grouped
  into build waves (below). Ties mean "either order is fine."

**Suggested build waves (advisory framing for the rank column):**

| Wave | Theme | Why this order |
|------|-------|----------------|
| **0 - Substrate** | real data layer, workspace shell, decision capture | Nothing renders without real goals to render; everything else hangs off this. |
| **1 - Canvas core** | render engine, the four family canvases, chat + morph | The product *is* the canvas; this is the spine v2 ships on. |
| **2 - Autonomy + colleagues** | autonomy engine, board arc, hiring, agent ops | The differentiators: decisions-as-records and the human+agent workforce. |
| **3 - Evidence + requirements** | E1-E5 real artifact pipelines, the reqs loop | Turns mocked outputs into real evidence; ties in refine-requirements-v2. |
| **4 - Hardening** | three-tier substrate, slop-gate-as-CI | Positioning parity + the showability bar made continuous. |

**Exhaustiveness guarantee.** Every route in the final inventory appears **exactly once** below
(chooser + four goal canvases + ten Phase-5 routes + the hidden `#/kit`), each cross-cutting mechanic
gets its own row, and the **FR/US cross-reference table** (last section) shows every FR-001..023 and
US1..US10 is either mapped to a goal here or explicitly called **demo chrome with no v2 goal**. A cold
reader can build the v2 backlog from this document alone.

**Brand note (FR-018):** this document is authored hyphen-only, em-dash-free, `cast-*` lowercase,
"Layer" not "Tier" for the agent layer (the FR-017 "three access tiers" is the access-mode term, not
the agent-layer term).

---

## Theme 1 - Canvas core & morph

The render architecture, the four workflow-family canvases, and the chat rail that steers them. The
**morph itself** is the headline of this theme but is captured once in the **Cross-cutting mechanics**
table (it spans all four families). Routes here: `#/` + the four `#/goal/*` canvases. The chat rail
and the projection engine are added as architecture rows (not routes, but the most build-relevant
"surfaces" of the theme).

| Surface / Route | What it proves | Follow-on v2 goal (slug + outcome) | Size | Depends on | Rank |
|---|---|---|---|---|---|
| `#/` (scenario chooser / front door) | FR-002; US2 entry. The stranger-navigable front door routing into the four families + standalone areas. | **`goal-workspace-home`** - When a user opens Diecast they see *their real goals* (not five demo scenarios), can open any one into its family canvas, and create a new goal that gets classified into a family. | M | `org-data-api`, `goal-classification-engine` | 2 |
| `#/goal/CAST-412` (feature canvas - `segments`) | FR-003, FR-006, FR-008; US1, US2, US3. WHAT-first segmented backbone (Shape -> Commit -> Design -> Build -> Show) with a nudged next step + an execution drill-in. | **`feature-family-canvas`** - When an engineer opens a feature goal, a live segmented canvas renders the real current stage, the nudged next action as primary, and a one-click execution drill-in (runs -> dispatch tree -> maker-checker), all from real goal state. | L | `canvas-render-engine`, `org-data-api` | 4 |
| `#/goal/CAST-431` (debug canvas - `loop`) | FR-006, FR-007; US2 (S1/S2). The maximally-different loop shape with a live iteration counter and visible confirm/refute history. | **`debug-loop-canvas`** - When a debug goal is open, the canvas renders a real hypothesis -> experiment -> confirm/refute loop with a live `iter n/budget` counter and the full investigation ledger as first-class history (no hidden passes). | M | `canvas-render-engine` | 7 |
| `#/goal/CAST-452` (spike canvas - `timebox`) | FR-006, FR-016; US2 (S3). The timeboxed-budget shape whose conclusion artifact feeds a decision via `spike_ref`. | **`spike-timebox-canvas`** - When a spike goal runs, the canvas renders a real burning time-budget meter over the four probe steps and lands a verdict card whose `spike_ref` links to the decision it informs. | M | `canvas-render-engine`, `decision-capture-service` | 10 |
| `#/goal/CAST-461` (data canvas - `pipeline`) | FR-006, FR-009; US2 (S4). The pipeline DAG shape ending in a visualized published report. | **`data-pipeline-canvas`** - When a data goal runs, the canvas renders the real import -> tidy -> transform -> explore -> publish pipeline with the answer surfaced as a rendered visualization, not prose. | M | `canvas-render-engine`, `evidence-data-report` | 11 |
| Chat rail / steering (persistent rail; promote-pin) | FR-004, FR-005; US1 (S3). The power-lever rail beside the canvas; chat artifacts are promotable/pinnable onto the canvas. | **`chat-steering-rail`** - When a user types into the rail, a real model call can redirect the active canvas and any chat-produced artifact (hiring report, spike result) can be pinned onto the goal canvas as a persistent object. | M | `real-chat-backend`, `canvas-render-engine` | 8 |
| render(appState) projection engine (architecture) | FR-003, FR-020; SC-005. The single pure-render path every screen is a projection of; the reason "polish is gating, not re-authoring." | **`canvas-render-engine`** - When any goal renders, one declarative render layer maps real goal state to the correct family canvas shape, so a new family is added by data + a spine variant, never a new screen-by-screen build. | L | `org-data-api` | 3 |

---

## Theme 2 - Evidence (E1-E5 as real artifact pipelines)

In the prototype, E1-E5 are fitted-form evidence mocks (a base64 raster, a fake ledger, a fake
red->green strip, a verdict card, an inline-SVG report). v2 turns each into a real artifact pipeline.
These are sub-surfaces of the canvases above (not separate routes), but SC-006 wants each mapped to a
buildable goal. Home steps: E1 -> `feat-05`, E2 -> `dbg-04`, E3 -> `dbg-05`, E4 -> `spk-04`,
E5 -> `data-05`.

| Surface / Route | What it proves | Follow-on v2 goal (slug + outcome) | Size | Depends on | Rank |
|---|---|---|---|---|---|
| E1 - acceptance-evidence bundle (feature `feat-05`) | FR-009, US4 (S1/S2). "Done" is shown (diff + screenshots + summary), not asserted. | **`evidence-acceptance-bundle`** - When feature work completes, the canvas shows a real captured acceptance bundle (UI screenshots / proof-shots + a run summary) generated from the actual execution, surfaced at the WHAT level. | M | `feature-family-canvas`, `agent-execution-runtime` | 15 |
| E2 - confirm/refute ledger (debug `dbg-04`) | FR-009, FR-007, US4. The investigation ledger as the loop's confirmed/refuted memory. | **`evidence-debug-ledger`** - When a debug loop runs, each hypothesis is recorded with prediction-vs-observed and a confirmed/refuted mark in a real persisted investigation ledger that drives the iteration counter. | M | `debug-loop-canvas`, `agent-execution-runtime` | 16 |
| E3 - red->green repro (debug `dbg-05`) | FR-009, US4 (S3). The fix proven by a failing case that turns passing; checker compliance shown beside the artifact. | **`evidence-redgreen-proof`** - When a fix is proposed, the canvas shows a real captured red->green run (the same case failing then passing) plus the checker's compliance evidence, as the proof-of-fix surface. | M | `evidence-debug-ledger`, `agent-execution-runtime` | 17 |
| E4 - spike verdict card + `spike_ref` (spike `spk-04`) | FR-016, US2 (S3). The conclusion artifact that a decision references. | **`evidence-spike-verdict`** - When a spike concludes, it emits a real verdict artifact (one-line answer + `revisit_if` trip-wire) that is linked from and navigable to the decision record it informs. | S | `spike-timebox-canvas`, `decision-capture-service` | 18 |
| E5 - data report + provenance (data `data-05`) | FR-009, US4. A published narrative report (viz as headline) distinct from the working notebook, with lineage on demand. | **`evidence-data-report`** - When a data goal publishes, it renders a real narrative report with the visualization as the headline and a source/transform provenance drill-in, distinct from the working notebook. | M | `data-pipeline-canvas` | 19 |

---

## Theme 3 - Decisions & autonomy

The decision-record surfaces (routes) live here; the **capture mechanism**, the **L1/L2/L3 autonomy
engine + dial**, and the **escalation rail** are captured in the Cross-cutting mechanics table (they
span every phase and surface). Routes: `#/decision/:atomId` and `#/decisions/CAST-412`.

| Surface / Route | What it proves | Follow-on v2 goal (slug + outcome) | Size | Depends on | Rank |
|---|---|---|---|---|---|
| `#/decision/:atomId` (single decision record; e.g. `#/decision/run-412-a`) | FR-021, FR-023, US10 (S1/S3), US5 (S3). The structured decision artifact (id, reversibility, rationale, time, originating phase/agent, consequences, `spike_ref`, supersedes chain), and the L3 escalation pack rendering. | **`decision-record-view`** - When a user opens any decision id, they see the full real record (rationale, timestamp, originating phase/agent, reversibility, consequences, supersession links), and an L3 record presents the three pre-framed escalation options inline. | M | `decision-capture-service` | 13 |
| `#/decisions/CAST-412` (cross-phase decision trail + dial legend) | FR-023, US10 (S4). The per-goal decision trail across all phases (not only execution), with the autonomy-dial legend. | **`decision-trail-view`** - When a user opens a goal's decision trail, they see every decision across requirements / exploration / planning / execution in time order, filterable by reversibility, with the goal's current autonomy-dial setting shown. | M | `decision-capture-service`, `autonomy-engine` | 13 |

---

## Theme 4 - Colleague surfaces (the human + agent workforce)

The board arc, the hiring funnel, the marketplace, agent ops, skill creation, and Layer-2. This is the
"humans and agents as peers, operated like a workforce" cluster (US5, US6, US8, US9). Routes:
`#/board`, `#/ticket/CAST-412`, `#/hire`, `#/marketplace`, `#/agent/:slug`, `#/skills/new`, `#/layer2`.

| Surface / Route | What it proves | Follow-on v2 goal (slug + outcome) | Size | Depends on | Rank |
|---|---|---|---|---|---|
| `#/board` (shared human + agent board) | FR-010, US5 (S1). Humans and agents as peer assignees with an any/human/agent/checker filter and the "publishes INTO your PM tool" framing. | **`shared-agent-board`** - When the board renders, real goals/tickets show human and agent assignees as peers with a working assignee filter and a one-way publish-out integration into an external PM tool. | L | `org-data-api`, `agent-execution-runtime` | 21 |
| `#/ticket/CAST-412` (ticket maker-checker activity log) | FR-010, FR-008, US5 (S2), US4 (S3). The maker-checker iteration: checker rule violations as inline comments (M04/S03/R02), a visible rework budget (1/3), the resulting PR link. | **`ticket-maker-checker-log`** - When a ticket is open, its activity log shows the real maker-checker iteration with inline checker-rule comments, a live rework-budget meter, and links to the produced PR and decision atoms. | M | `shared-agent-board`, `agent-execution-runtime` | 22 |
| `#/hire` (hiring funnel: assess -> federate -> report -> hire -> onboard) | FR-011, US6 (S1/S2/S4). "Hire. Don't install." as a clickable funnel ending in onboarding to org data + tastes. | **`agent-hiring-funnel`** - When an owner needs a capability, they can commission a real assessment, federate it to candidate agents, review a stack-ranked report with links to produced output, hire the winner, and onboard it onto org data sources and tastes. | L | `agent-marketplace`, `agent-execution-runtime` | 23 |
| `#/marketplace` (agent marketplace grid) | FR-011, US6 (S3/S5). Marketplace credibility stats (apify-style compliance/runs) + archetype diversity with maker-checker pairing shown in-card. | **`agent-marketplace`** - When the marketplace renders, it lists real agents with live credibility stats (compliance rate, runs, rework loops), full resumes, and in-card maker-checker pairing, behind one discover-and-hire mechanism over public + private catalogues. | L | `agent-registry`, `org-data-api` | 12 |
| `#/agent/:slug` (agent resume / versions / monitoring) | FR-013, US8 (S2), US6 (S3). The full agent resume + version history + usage metrics + monitoring state. | **`agent-ops-detail`** - When a user opens an agent, they see its real resume (role, I/O contract, autonomy level, paired checker, benchmark, sample output), version history, live usage metrics, and current monitoring state. | M | `agent-registry`, `agent-execution-runtime` | 24 |
| `#/skills/new` (skill creation - private vs company-wide) | FR-012, US8 (S1). A near-zero-friction creation path with a private vs company-wide visibility choice. | **`skill-creation-flow`** - When a user creates a skill, a near-zero-friction path (as simple as a `cast-*` command) registers it with a real private vs company-wide visibility setting and it appears in the matching catalogue. | M | `agent-registry` | 25 |
| `#/layer2` (Layer-2: contract catalogue + chain + portfolio) | FR-015, US9 (S1/S2/S3). 12 named workflow contracts, the 8-agent chain pipeline view, the portfolio dashboard. | **`layer2-workflow-surfaces`** - When the Layer-2 area renders, the contract catalogue, an executing goal's live position in its agent chain, and a real portfolio of goals shipped through the workflow are all backed by real orchestration data. | L | `agent-execution-runtime`, `org-data-api` | 26 |

---

## Theme 5 - Platform substrate (making the fakes real)

The infrastructure rows: the scripted chat engine becomes real inference, the frozen `org.js` becomes
a real API + persistence, and the three access tiers become one real skill/agent substrate. None are
routes; they are the foundation everything above depends on (Wave 0 + late hardening).

| Surface / Mechanic | What it proves | Follow-on v2 goal (slug + outcome) | Size | Depends on | Rank |
|---|---|---|---|---|---|
| Frozen `org.js` -> real API + persistence | FR-001 (inverted), FR-020. The fake-data spine (`window.ORG`, one coherent org reused everywhere) that every screen projects. | **`org-data-api`** - When a screen needs data, it reads from a real Diecast API + datastore (goals, tickets, agents, decisions, requirements) instead of a frozen `org.js`, with the same coherent-org shape the prototype proved out. | L | (none - foundation) | 1 |
| Scripted `SCRIPTS` engine -> real chat backend | FR-004; SC-003. The scripted advance() narrative that drives the morph + chat beats today. | **`real-chat-backend`** - When a user chats, a real Claude-backed conversation (not a canned `SCRIPTS` array) drives canvas changes and produces artifacts, with the scripted beats retired. | L | `org-data-api`, `canvas-render-engine` | 6 |
| Three access tiers parity (terminal / chat / canvas) - FR-017 moment | FR-017; positioning constraint. The side-by-side proof that a terminal pane and the canvas invoke the same skill, same artifact landing either way. | **`three-access-tiers-substrate`** - When a user runs a `cast-*` skill from the terminal, from chat, or from a canvas default, the same agent substrate executes and the same artifact lands, proving the UI is a value-add shell over (never a gate to) the terminal. | L | `real-chat-backend`, `agent-execution-runtime` | 14 |
| (foundational dependency referenced throughout) agent execution runtime | FR-008, US3 (S2). Real runs, dispatch trees, maker-checker loops behind the canvases, board, hiring, evidence. | **`agent-execution-runtime`** - When a goal executes, real agents run with dispatch trees, maker-checker loops, rework budgets, and named exits (fix / retry / escalate), surfaced through the execution drill-in and the board. | L | `org-data-api`, `agent-registry` | 5 |

> **Note on `agent-registry`:** several colleague-surface goals depend on a real registry of agents
> (resumes, versions, pairings, catalogues). It is introduced here as the dependency behind
> `agent-marketplace` / `agent-ops-detail` / `skill-creation-flow`; the v2 session may choose to split
> it out as its own Wave-0/1 goal (`agent-registry` - "a real catalogue of agents with resumes,
> versions, paired checkers, and public/private visibility"). Flagged for the session to rank.

---

## Theme 6 - Requirements loop (references the separate refine-requirements-v2 goal)

| Surface / Route | What it proves | Follow-on v2 goal (slug + outcome) | Size | Depends on | Rank |
|---|---|---|---|---|---|
| `#/reqs/CAST-412` (requirements doc surface) | FR-014, US7 (S1-S4). Classification pill, L1/L2/L3 progressive disclosure, anchored inline comments (one PM commenter), version change summary, downstream write-back notification. | **`reqs-loop-integration`** - When a goal's requirements doc renders, it is the live surface of the **separate `refine-requirements-v2` product** (classification pill, L1/L2/L3 disclosure, anchored comments, version deltas, downstream write-back notices), embedded as the front door of every flow. **This goal integrates with, and does not rebuild, `refine-requirements-v2`** - that product is owned and built under its own goal (see Out of Scope, refined requirements). | M | `refine-requirements-v2` (external goal), `org-data-api` | 20 |

> **Reference, not duplication (binding):** `refine-requirements-v2` is a **separate, already-scoped
> goal** (refined requirements, Out of Scope: "Building refine-requirements-v2 itself - separate goal;
> this prototype only mocks its surfaces"). This map **points at it** as the dependency; it does not
> restate its backlog. The only v2 goal this map adds is the **integration** of that product's surface
> into the Diecast canvas front door.

---

## Cross-cutting mechanics (each gets a row - the most build-relevant "surfaces")

SC-006 maps each *surface* to a buildable goal, and the mechanics are the most build-relevant surfaces
of all. These span families and routes, so they are listed once here rather than per-route.

| Mechanic | What it proves | Follow-on v2 goal (slug + outcome) | Size | Depends on | Rank |
|---|---|---|---|---|---|
| **The morph** (chat-driven canvas family transition) | FR-004; SC-003; US1 (S2). The signature fluidity moment: a chat course-change visibly reshapes the canvas from one family to another without losing goal context. | **`canvas-morph-engine`** - When chat reclassifies a goal's family, the canvas animates a real transition from the old family shape to the new one (view-transition driven), preserving goal context, as a genuine state change rather than a scripted panel swap. | M | `canvas-render-engine`, `real-chat-backend`, `goal-classification-engine` | 9 |
| **Decision-receipt mechanism** (structured atom capture) | FR-021; US10 (S1); US5 (S3). Any non-trivial call at any phase becomes a structured decision atom (id, reversibility, rationale, time, phase/agent, consequences, links). | **`decision-capture-service`** - When any agent or phase makes a non-trivial call, the system writes a real structured decision atom (rationale, timestamp, originating phase/agent, reversibility, consequences, `spike_ref`/supersession links) that the decision surfaces read from. | M | `org-data-api` | 5 |
| **L1/L2/L3 autonomy engine + per-goal dial** (incl. the escalation rail) | FR-022; US10 (S2); US5 (S4). Reversibility-keyed defaults (L1 decide-record, L2 decide-record-notify, L3 ask-first) shifted by a per-goal autonomy dial; L3 stops the agent and hands `@you` three pre-framed options on the board. | **`autonomy-engine`** - When a decision is reached, the system applies the goal's autonomy-dial threshold to its reversibility level, auto-deciding-and-recording at L1, notifying at L2, and stopping for human input with three pre-framed options at L3 (the escalation rail), all configurable per goal. | L | `decision-capture-service`, `agent-execution-runtime` | 12 |
| **Slop-gate-as-CI** (the 21-capture visual/tone gate, continuous) | FR-018, FR-019; SC-004. The every-screen "not-generic / not-ai-aesthetic" gate + the brand/vocabulary rules that keep the product showable without apology. | **`slop-gate-ci`** - When a UI change is proposed, an automated visual + tone gate (the `cast-preso-check-visual` / `-tone` checkers wired into CI) flags generic / AI-aesthetic / em-dash / vocabulary-drift regressions before merge, keeping the real product showable without apology. | M | (none - tooling; runs against the real app) | 27 |

---

## FR / US cross-reference (every requirement mapped or marked demo chrome)

Every functional requirement and user story is either mapped to a v2 goal above or explicitly named
**demo chrome with no v2 goal**. No FR/US is left unmapped.

### Functional requirements

| FR | Mapped to v2 goal(s) | Notes |
|----|----------------------|-------|
| FR-001 (self-contained prototype) | `org-data-api` (inverted) | The prototype *is* the FR-001 artifact; v2 inverts the fake-data spine into a real API. |
| FR-002 (entry / chooser) | `goal-workspace-home` | |
| FR-003 (WHAT-first opinionated canvas) | `canvas-render-engine`, the four `*-family-canvas` goals | |
| FR-004 (chat steers; morph) | `chat-steering-rail`, `real-chat-backend`, `canvas-morph-engine` | |
| FR-005 (promote/pin chat artifacts) | `chat-steering-rail` | Pin is a canvas-core affordance, not a sixth op. |
| FR-006 (four distinct canvas shapes) | the four `*-family-canvas` goals | SC-005 contrast. |
| FR-007 (iteration visible) | `debug-loop-canvas`, `evidence-debug-ledger` | |
| FR-008 (execution tab / drill-in) | `feature-family-canvas` (drill-in), `ticket-maker-checker-log`, `agent-execution-runtime` | |
| FR-009 (evidence fitted forms) | `evidence-acceptance-bundle`, `-debug-ledger`, `-redgreen-proof`, `-data-report` | E1-E5 pipelines. |
| FR-010 (board arc: 4 connected screens) | `shared-agent-board`, `ticket-maker-checker-log`, `decision-record-view`, `decision-trail-view` | |
| FR-011 (hiring funnel) | `agent-hiring-funnel`, `agent-marketplace` | |
| FR-012 (skill creation) | `skill-creation-flow` | |
| FR-013 (agent detail) | `agent-ops-detail` | |
| FR-014 (requirements doc surface) | `reqs-loop-integration` (-> external `refine-requirements-v2`) | |
| FR-015 (Layer-2 surfaces) | `layer2-workflow-surfaces` | |
| FR-016 (spike first-class, `spike_ref`) | `spike-timebox-canvas`, `evidence-spike-verdict` | |
| FR-017 (three access tiers) | `three-access-tiers-substrate` | |
| FR-018 (brand / vocabulary) | `slop-gate-ci` | Enforced as the tone/vocab half of the CI gate. |
| FR-019 (polish bar) | `slop-gate-ci` | The visual/density half of the CI gate. |
| FR-020 (greenfield, stack-free) | `canvas-render-engine`, `org-data-api` | A design principle realized by the v2 architecture, not bound to today's cast-server UI. |
| FR-021 (decisions recorded) | `decision-capture-service`, `decision-record-view` | |
| FR-022 (autonomy model) | `autonomy-engine` | |
| FR-023 (decisions surfaced + trail) | `decision-record-view`, `decision-trail-view` | |

### User stories

| US | Mapped to v2 goal(s) |
|----|----------------------|
| US1 (adaptive canvas + chat steering) | `canvas-render-engine`, the `*-family-canvas` goals, `chat-steering-rail`, `canvas-morph-engine` |
| US2 (four family clickthroughs) | the four `*-family-canvas` goals, `goal-workspace-home` |
| US3 (WHAT-primary + execution drill-in) | `feature-family-canvas`, `agent-execution-runtime`, `ticket-maker-checker-log` |
| US4 (evidence surfaces) | the four `evidence-*` goals |
| US5 (board -> ticket -> decision -> escalation) | `shared-agent-board`, `ticket-maker-checker-log`, `decision-record-view`, `autonomy-engine` |
| US6 (agent hiring & assessment) | `agent-hiring-funnel`, `agent-marketplace`, `agent-ops-detail` |
| US7 (requirements-doc loop) | `reqs-loop-integration` (references external `refine-requirements-v2`) |
| US8 (skillification & agent ops) | `skill-creation-flow`, `agent-ops-detail`, `agent-registry` |
| US9 (Layer-2 surfaces) | `layer2-workflow-surfaces` |
| US10 (decision tracking across phases) | `decision-capture-service`, `decision-record-view`, `decision-trail-view`, `autonomy-engine` |

### Success criteria (these are demo-validation gates, not v2 build goals)

| SC | Disposition |
|----|-------------|
| SC-001 (SJ clicks every flow, keep/change/drop) | Walkthrough gate (Phase 6.4). Not a v2 build goal; the keep/change/drop dispositions become *inputs* that the v2 session uses to prune/confirm the rows above. |
| SC-002 (fresh viewer states what it does in ~3 min) | Walkthrough gate (Phase 6.4 human action item). Not a build goal. |
| SC-003 (fluidity demonstrated) | Proven by the morph; the build goal is `canvas-morph-engine`. |
| SC-004 (showable without apology) | The standing bar; the continuous-enforcement build goal is `slop-gate-ci`. |
| SC-005 (distinct canvas shapes) | Proven by the four `*-family-canvas` goals + `canvas-render-engine`. |
| SC-006 (this roadmap) | **Satisfied by this document.** |
| SC-007 (in-context decision + autonomy moment) | Proven by `decision-record-view` + `autonomy-engine`. |

---

## Demo chrome with NO v2 goal (explicit exclusions - so the map is exhaustive, not silently partial)

These prototype elements exist purely to make the mockup navigable and presentable. They are **not**
buildable v2 product goals; they have no follow-on goal and are listed here so the map is provably
complete rather than silently dropping them.

| Element | Why it has no v2 goal |
|---|---|
| The five `driver.js` anatomy tours (`TOURS`) | Demo-walkthrough chrome for strangers; the real product teaches via the live UI, not scripted anatomy tours. |
| The presenter demo-script overlay (`appState.demoScriptOpen`, `s`-key) | Presenter aid for guided walkthroughs; no place in the shipped product. |
| The single-file inliner (`prototype/_build/inline.mjs`) + `prototype/dist/diecast-prototype.html` | Packaging tooling for the mockup distributable; v2 ships a real app, not a one-file HTML dump. |
| `#/kit` (hidden component-kit harness) | Internal component/shape demo harness; ships hidden inside the dist (hash-only, harmless), never a product surface. The prototype's last sanctioned grep exception, retired at project close. |
| The scripted `SCRIPTS` advance engine (the canned beats) | The *scripting* is chrome; its **replacement** (`real-chat-backend`) is the v2 goal. The surfaces it drives are real; the canned narrative is not. |
| Family-shape glyphs / chooser tour buttons / `tour-*` styling | Presentation styling for the chooser and tours; subsumed by the real design system, not a standalone goal. |

> **Note on setup/installation (refined requirements Out of Scope):** mac/win/linux + claude/codex/
> copilot parity is **vision backdrop only** (a positioning claim), not a prototype flow and not a v2
> goal in this map. If the v2 session wants it, it is a net-new goal outside the prototype's surfaces.

---

## Coverage checklist (route inventory - each appears exactly once above)

- [x] `#/` (chooser) - Theme 1
- [x] `#/goal/CAST-412` (feature) - Theme 1
- [x] `#/goal/CAST-431` (debug) - Theme 1
- [x] `#/goal/CAST-452` (spike) - Theme 1
- [x] `#/goal/CAST-461` (data) - Theme 1
- [x] `#/board` - Theme 4
- [x] `#/ticket/CAST-412` - Theme 4
- [x] `#/decision/:atomId` - Theme 3
- [x] `#/decisions/CAST-412` - Theme 3
- [x] `#/hire` - Theme 4
- [x] `#/marketplace` - Theme 4
- [x] `#/agent/:slug` - Theme 4
- [x] `#/skills/new` - Theme 4
- [x] `#/layer2` - Theme 4
- [x] `#/reqs/CAST-412` - Theme 6
- [x] `#/kit` (hidden) - Demo chrome (no v2 goal)
- [x] Cross-cutting mechanics: morph, decision-receipt, L1/L2/L3 autonomy engine, slop-gate-as-CI - dedicated table

**16 routes + 4 cross-cutting mechanics, each mapped exactly once.** Every FR-001..023 and US1..US10
is mapped or marked demo chrome. The v2 backlog is buildable from this document alone.

---

*End of the SC-006 surface -> buildable-goal map. Input to the post-mockup v2 planning session, which
owns the final stack-rank. Authored off the Phase 6 critical path by sub-phase 6.3b; no
`prototype/index.html` (or any code file) was touched.*
