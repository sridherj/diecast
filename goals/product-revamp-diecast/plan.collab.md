# High-Level Phasing Plan: Product Revamp — Diecast Vision Prototype

## Overview

Build a self-contained, browser-openable HTML/JS/CSS **clickable prototype** that makes SJ's
product vision feel real: an opinionated, workflow-adaptive canvas steered by chat, with the
**Guide** as a persistent character and agents as hireable peers. The exploration's central
insight shapes the whole plan: the ~35 surfaces are **projections of one fake org through one
`render(appState)` function**, not 35 hand-built pages — so the entire build hinges on getting
the render architecture and the one hero morph right *first*, then mass-producing surfaces as
thin data slices. Identity, the Guide, the canvas anatomy, and the E1–E5 evidence catalog are
owner-locked; this plan sequences the build, front-loads the two highest-risk unknowns (the
View-Transitions morph for SC-003 and the slop-gate aesthetic for SC-004), and marks where the
work parallelizes.

**Stack (locked by exploration):** no build step · native import maps · htm+Preact (~3KB CDN) ·
one in-memory JSON state · `location.hash` routing · CSS View Transitions for the morph · a
~50-line scenario engine · 5 typed chat ops (`morph·nudge·promote·drillInto·pin`) through one
dispatcher · driver.js walkthrough overlays · frozen `org.json` fake-data spine.

**Illustration tooling (owner pointer):** for any visual richer than hand-authored inline SVG, use
`/cast-preso-illustration-creator` (raster via Stitch MCP, or vector SVG) paired with
`/cast-preso-illustration-checker` for verification. Highest-value uses: the **E1 fake "screenshots"**
(US4 fitted proof), **marketplace/agent avatars + the Guide's character**, and the **data-analysis E5
rendered output**. Every generated illustration must clear the hard slop-gate
(`not-generic`/`not-ai-aesthetic`) — the creator→checker pairing enforces exactly that.

**Total estimated effort:** ~7–9 focused days (≈14–18 sessions).

---

## Phase 1: Keystone — Render Architecture & Morph Technique Spike

**Outcome:** `index.html` opens in a browser with **no build step**, `render(appState) → DOM`
drives the screen, hash routing switches surfaces, and a **placeholder hero morph** (a stub
"feature" spine shared-element-morphs into a stub "debug" spine) runs through the CSS View
Transitions API with the locked motion register. The riskiest technical unknown — *can a static
file deliver vision-grade fluidity?* — is answered before any real surface is built.

**Dependencies:** None

**Estimated effort:** 1–1.5 days / 2–3 sessions

**Verification:** Open `index.html` directly from disk (no server, no compile); navigate ≥2 hash
routes; trigger the scripted morph and observe a ~350ms transition with ≥4 persistent anchors and
a working `prefers-reduced-motion` fade fallback; confirm all 5 typed ops dispatch through one
~30-line vanilla-JS dispatcher. **Decision gate:** if View Transitions can't carry the morph
convincingly with placeholders → revisit the morph approach (alternative: keyed CSS panel-swap)
*before* Phase 3 invests in real canvases.

Key activities:
- Stand up single-file `index.html` with import map → preact/htm/driver.js from CDN (<15KB total).
- Implement `render(appState)` + `location.hash` switch (~20 lines) with a minimal nav rail and the
  three-tier shell (nav · CanvasFrame · ChatRail) from `design-samples/app-shell.html` as a starting
  reference (not a boundary — re-derive at the build-phase Steve-Jobs bar).
- Build the scenario engine: ordered `{patch, narration, transition}` steps + `advance()` (~50 lines).
- Build the typed-op dispatcher (`morph·nudge·promote·drillInto·pin`) wrapped in `startViewTransition`.
- **Spike:** placeholder feature-spine → debug-spine morph with `view-transition-name` anchors,
  reduced-motion fallback, and a stub decision receipt — prove the SC-003 technique end-to-end.

## Phase 2a: Fake-Org Data Spine (parallel with 2b)

**Outcome:** One coherent fictional org exists as a **frozen `org.json`** that every screen will
read from — CAST-412 (one canonical title everywhere), the agent roster (maker/checker pairs with
cred stats), the 8-agent chain, 12 named contracts, and **5–8 decision atoms per goal** (judgment
calls, exactly one L3 per flow). Canonical vocabulary is verbatim and drift-free.

**Dependencies:** Phase 1 (state shape known)

**Estimated effort:** 0.5–1 day / 1–2 sessions

**Verification:** `org.json` loads into `appState`; a grep confirms zero ad-hoc naming (CAST-412,
M04/S03/R02, rework 1/3, L1/L2/L3, crud-orchestrator, "99.9% compliant across 505 runs" appear only
from the spine); decision-atom budget holds (≤1 L3 per flow); the dial tooltip stats and marketplace
cred read from the same fields.

Key activities:
- Author the org structure with seeded `@faker-js` (build-time only) + hand-tuned LLM prose, then freeze.
- Encode the four family goals (feature/debug/spike/data) with their stages, artifacts, and work-streams.
- Encode 5–8 decision atoms per goal with rationale, timestamp, originating phase/agent, reversibility (L1/L2/L3).
- Encode the marketplace roster, hiring candidates (5–10) with eval data + deep links to fake produced work.
- Encode Layer-2 data: 12 contracts, the 8-agent chain positions, portfolio projects.

## Phase 2b: Component Kit & Aesthetic Lock (parallel with 2a)

**Outcome:** ~8 reusable components exist and **the signature visual language is locked at the
Steve-Jobs bar** — the five-element colleague-card lockup, the E1–E5 EvidenceBlock family, the
escalation rail, the 3B nudge card (with "why now"), the decision-atom disclosure ladder (6A
pill → 6B callout → 6C trail row), the autonomy dial (8A segmented + legend), and the four stage-spine
variants. Building this kit first turns every downstream screen into a ~10-line data slice and
**de-risks SC-004** by proving one screen clears the slop-gate before mass production.

**Dependencies:** Phase 1 (render contract). Consumes `org.json` shape from 2a (can build against a
small stub, then wire to the real spine when 2a lands).

**Estimated effort:** 1.5 days / 3 sessions

**Verification:** Each component renders from a data prop in isolation; the colleague lockup renders
identically (4C density) on a board card and (4B density) inline in an activity log with no field
drift; **both `cast-preso` slop-gate checkers (`not-generic` / `not-ai-aesthetic`) pass** on the
signature screen; the Guide renders as a *visibly distinct character* (own identity in chat voice,
nudge attribution, decision receipts) vs worker agents.

Key activities:
- Build the colleague-card lockup as ONE component, two densities (4C mini-card · 4B paired-avatars line).
- Build the EvidenceBlock family E1–E5 (acceptance panel · confirm/refute ledger · red→green repro ·
  verdict card w/ spike_ref · rendered report + provenance).
- Build the escalation rail (7A ranked hero/outline/ghost — ranked but nothing pre-selected),
  decision disclosure ladder, nudge card, autonomy dial.
- Build the four stage-spine variants (1B segment bar · 2B staged band + ↺ counter · timebox meter · pipeline DAG).
- **Lock the Diecast light-world tokens** (cream `#F5F4F0`, ink `#1A1A28`, raspberry `#D6235C`, maker
  `#3B5BB0` / checker `#6B47B0`, IBM Plex Mono + DM Sans) and **design the Guide's character treatment**
  (see Open Questions) — re-derive layout/spacing from first principles, slop-gate must pass.

## Phase 2c: Stage-Model Research — Derive the Right Per-Family Spines (parallel with 2a/2b)

**Outcome:** The **actual stage vocabulary for each of the four families is derived from online
research**, not assumed — and the steps are **extremely practical, reflecting how the best
practitioner in each category actually works** (owner directive). The illustrative steps floated
during exploration (e.g., prototype-with-UI-choices → locked design → eng design for feature; repro ·
RCA · evidence · fix · tests for debug) are **explicitly dropped as placeholders** (owner: "those are
not the right steps — we have to explore online and come up with the right mental models"). This spike
studies the real, hands-on workflow of the best feature-builders, debuggers, spike-runners, and data
analysts — concrete steps a top practitioner would recognize as *their* process — and applies the
locked familiar-tool principle. This is the Guide's "intent → path" composition made concrete, and it
gates every canvas build.

**Dependencies:** Phase 1 (canvas/spine contract). Independent of 2a/2b — runs in parallel.

**Estimated effort:** 0.5–1 day / 1–2 sessions

**Verification:** A short stage-model note names the chosen spine for each family (feature / debug /
spike / data); **each step passes the "would a top practitioner in this category recognize this as
their actual workflow?" test** (concrete and practical, not abstract phase labels); each step maps to
its familiar-tool surface with a one-line rationale and the reference(s) it was drawn from; owner signs
off on the four spines before Phase 3 builds them.

Key activities:
- Research how the **best practitioners** in each category actually work — study real, current
  workflows of top feature-builders, debuggers, spike-runners, and data analysts (mine the exploration
  reference set + a targeted online scan), not generic/abstract phase models.
- Pressure-test each candidate step for practicality: would a top practitioner say "yes, that's a real
  step I do," not "that's a tidy label someone invented." Drop or rename anything that fails.
- Map each derived step to its familiar-tool surface (doc / board / PR-thread / investigation ledger /
  notebook / memo+timebox) per the locked familiar-tool principle.
- Propose the stage spine for each family; flag where a family's spine should iterate/loop vs. progress.
- Capture the result as the canonical per-family stage definition consumed by Phases 3–4 and encoded in `org.json`.

## Phase 3: Feature + Debug Flows & the Real Hero Morph

**Outcome:** The two **most-contrasting** workflow families are clickable end-to-end from real data,
and the real **"this is actually a bug, not a feature"** chat morph lands between them — **SC-003 is
demonstrated for real**, and **SC-005's feature-vs-debug contrast is obvious at a glance**. The feature
family runs its **Phase-2c-derived backbone** (whatever the stage-model research lands on, rendered as
familiar-tool surfaces → execution drill-in → E1 acceptance evidence); the debug family runs its
derived loop shape with an iteration counter and the E2 confirm/refute ledger + E3 red→green repro.

**Dependencies:** Phase 2a + Phase 2b + Phase 2c

**Estimated effort:** 2–2.5 days / 4–5 sessions

**Verification:** Both flows clickable start-to-finish with fake data; feature spine (1B) and debug
spine (2B + "iter 2/3" badge) are visibly different shapes; the scripted morph swaps the real feature
canvas for the real debug canvas (~350ms, 4 anchors, decision receipt, undoable); the feature flow shows
WHAT above the fold and confines runs/dispatch-tree/maker-checker to the execution tab; one L1 decision
chip and one human-needed (L3) moment surface at the WHAT level in these flows.

Key activities:
- Build the feature backbone canvas: the **Guide-composed stage spine as derived in Phase 2c** (not the
  dropped placeholder steps), stage-owned artifacts rendered as their familiar-tool surfaces, and the
  work-happening stream (tickets + `@you` manual items).
- Build the execution drill-in: run list → one run's dispatch tree (~13 sub-agents, lift `run_node.html`
  idiom) → maker-checker iteration with rework budget (1/3) and named exits (fix/retry/escalate).
- Wire the E1 acceptance panel (screenshots + test summary + checker rows + PR link-on-canvas).
- Build the debug-loop canvas: staged band + iteration history, E2 confirm/refute ledger in the work zone,
  E3 red→green repro evidence.
- Replace the Phase 1 placeholder morph with the **real** feature→debug morph and its decision receipt (SC-003).

## Phase 4: Spike + Data-Analysis Flows (parallel with Phase 5)

**Outcome:** The remaining two families are clickable end-to-end, completing all four (**SC-001 and
SC-005 fully met**). The spike family runs timebox → conclusion → **E4 verdict card whose `spike_ref`
is referenced by a decision**; the data-analysis family runs question → data sources → analysis →
**E5 rendered visualization** (chart/table/HTML, not prose-only).

**Dependencies:** Phase 3 (canvas grammar, component kit, and evidence conventions settled). Runs in
parallel with Phase 5 — different surfaces, shared components only.

**Estimated effort:** 1–1.5 days / 2–3 sessions

**Verification:** Spike flow produces a verdict artifact linked from a decision (spike_ref linkage visible);
data flow ends in a rendered chart/table, not text; both families render the familiar-tool surface for
their step (memo+timebox for spike, notebook+chart for analysis); iteration/timebox state shown cleanly.

Key activities:
- Build the spike canvas: timebox meter spine, memo surface, E4 verdict card with `spike_ref`.
- Wire the spike conclusion into a decision atom (FR-016 first-class spike → decision linkage).
- Build the data-analysis canvas: pipeline/notebook surface, data-source list, E5 rendered report.
- Build the FR-017 **three-access-tiers side-by-side moment** hosted in the spike flow (terminal pane
  invoking the same skill next to the canvas doing it with defaults — same artifact lands either way).
- Add each family's scripted chat steps + its single L3 moment.

## Phase 5: Colleague Surfaces — Board Arc · Hiring Funnel · Ops · Layer-2 · Reqs-Doc (parallel with Phase 4)

**Outcome:** The "humans + agents on one board" and "Hire. Don't install." theses are experienceable as
clickable surfaces. This is the **largest re-authoring chunk** (lifts preso a08–a13 designs as real DOM)
and splits into three independent sub-streams that can run concurrently.

**Dependencies:** Phase 2a + Phase 2b (component kit + data spine). Largely independent of the four-family
canvases. Runs in parallel with Phase 4.

**Estimated effort:** 1.5–2 days / 3–4 sessions (across the three sub-streams)

**Verification:** Board → ticket CAST-412 → decision artifact → L3 escalation read as four frames of one
story with consistent chrome; assignee filter (any/human/agent/checker) works; ticket shows maker-checker
activity log with inline rule violations (M04/S03/R02) + rework budget (1/3) + PR link; the hiring funnel
clicks assessment → federation → stack-ranked report → hire → onboard; the autonomy dial toggle visibly
promotes an L2 decision to an L3 stop.

Key activities (sub-stream **5a — Board, Decisions & Autonomy**, US5 + US10):
- Board with humans+agents as peer assignees + assignee filter + "publishes INTO your PM tool" framing.
- Ticket activity log (maker-checker, inline violations, rework budget, PR link); decision artifact;
  L3 escalation rail (three pre-framed options, ranked, nothing pre-selected).
- Cross-phase decision trail + the autonomy dial demo (toggle re-keys the reversibility engine).

Key activities (sub-stream **5b — Hiring Funnel & Agent Ops**, US6 + US8 + US9):
- The greenfield **hiring wizard** (5 screens): assessment → federation to 5–10 candidates →
  stack-ranked eval-report-card (per-dimension radar + pros/cons + deep links to real fake work) →
  hire (maker+checker together) → onboarding (data sources, tastes). Never a pricing-grid CRUD.
- Marketplace grid (archetype diversity, in-card maker-checker pairing) + full agent resume.
- Skillification flow (private vs company-wide, near-zero-friction path) + agent detail (versions,
  usage metrics, monitoring).
- Layer-2 surfaces: 12-contract catalogue, 8-agent chain pipeline view, portfolio dashboard.

Key activities (sub-stream **5c — Requirements-Doc Loop**, US7):
- Requirements doc render: classification pill + L1/L2/L3 progressive disclosure.
- Anchored inline comment thread (one commenter is a **PM** — the one PM-framed moment), version
  change-summary (delta review), and a "requirements updated from planning — review the delta" write-back notice.

## Phase 6: Polish & Showability — Slop-Gate, Walkthrough, Single-File

**Outcome:** The prototype is **showable to a peer/company without apology** (**SC-004**): a scenario-chooser
entry screen self-navigates the demo, driver.js overlays guide external walkthroughs, the density/consistency
pass is done, the slop-gate passes on **every** screen, and the whole thing is inlined into a single
distributable file. The prototype also **yields the v2 execution roadmap** (**SC-006**): each surface maps to a
buildable follow-on goal.

**Dependencies:** Phase 4 + Phase 5

**Estimated effort:** 1 day / 2 sessions

**Verification:** Fresh viewer unfamiliar with Diecast can state what the product does within ~3 min of the
guided clickthrough (SC-002); every screen passes `not-generic` / `not-ai-aesthetic`; no lorem ipsum / no
fake-data drift across all surfaces; single file opens from disk; a surface→follow-on-goal map exists (SC-006).

Key activities:
- Build the FR-002 scenario-chooser entry screen ("Follow a feature / Chase a bug / Run a spike / Answer a
  data question / Hire an agent") routing into all flows + standalone areas.
- Author driver.js walkthrough overlays + an optional demo-script overlay per flow.
- Density + consistency pass; run the slop-gate over every screen and fix flags.
- Inline all assets into the single self-contained file; final cross-surface fake-data drift sweep.
- Produce the surface→buildable-goal map for the post-mockup v2 planning session (SC-006).

## Build Order

```
                       Phase 1
              (render arch + morph SPIKE)
                    SC-003 technique
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
      Phase 2a        Phase 2b        Phase 2c
    (data spine)  (component kit   (stage-model
                   + aesthetic      research →
                   lock)            per-family spines)
                   SC-004 de-risk
          └───────────────┼───────────────┘
                          ▼
                       Phase 3
            (feature + debug + REAL hero morph)
                   SC-003 · SC-005
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
          Phase 4                 Phase 5
       (spike + data)      (colleague surfaces)
        SC-001/005          5a board+decisions
                            5b hiring+ops+layer2
                            5c reqs-doc loop
              └───────────┬───────────┘
                          ▼
                       Phase 6
            (polish · slop-gate · walkthrough)
                   SC-002 · SC-004 · SC-006
```

**Critical path:** Phase 1 → Phase 2b → Phase 3 → Phase 5 → Phase 6
(2b is longer than 2a; Phase 5 is the larger of the two parallel mid-build streams.)

**Parallelism opportunities:**
- **2a ∥ 2b ∥ 2c** — data authoring, component building, and stage-model research are independent
  (2b builds against a stub until 2a freezes; 2c is research that feeds Phase 3's spines).
- **Phase 4 ∥ Phase 5** — distinct surfaces sharing only the component kit.
- **5a ∥ 5b ∥ 5c** — three independent surface clusters within Phase 5.

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| 2026 AI-slop aesthetic (glass/gradient/glow/orb) sinks "showable without apology" (SC-004) | High | Hard slop-gate as a **continuous** gate — `not-generic`/`not-ai-aesthetic` checkers pass/fail every screen as built (Phase 2b onward), not only at Phase 6 |
| Per-screen hand-building blows the ~7–9 day budget (the cardinal sin) | High | Data-driven `render(state)`; any chrome that appears twice becomes a component immediately (Phase 2b kit is the lever) |
| The hero morph (SC-003) proves infeasible late, after canvases are built | High | **Spike it in Phase 1** with placeholders; decision gate before Phase 3 commits real canvases |
| L3 over-asking reads as a nagging tool and kills the colleague thesis | High | Hard budget in `org.json`: exactly 1 L3 per flow; L1 silent chips, L2 batched digest |
| Embedding preso SVGs as live UI ("comps ≠ components") | Med | Mine preso a08–a13 for layout/vocabulary only; re-author as real clickable DOM (Phase 5) |
| Fake-data drift across ~35 screens (the preso already drifted CAST-412) | Med | One frozen `org.json` spine; zero ad-hoc naming; final drift sweep in Phase 6 |
| Hiring funnel (the one greenfield concentration) lands as a pricing-grid CRUD | Med | Eval-report-card shape: per-dimension radar + pros/cons + deep links to real fake work (Phase 5b) |
| Execution trace-tree creeps onto the WHAT and turns Diecast into an observability dashboard | Med | Span/dispatch tree lives **only** behind the execution tab; WHAT stays outcome+evidence |
| P2 scope (US7/US8/US9) overruns the budget | Med | Owner decision: no cut line — all P2 ships in v1; if budget tightens, **extend the timeline, don't cut**. Data-driven render keeps marginal surface cost low; build P1 flows complete first, then the P2 surfaces |

## Open Questions

- **RESOLVED — E1–E5 evidence catalog is owner-blessed.** `design-decisions.ai.md` records the owner
  blessing E1–E5 as working defaults ("this Diecast design system as starting point is correct"), with
  **revisit-on-sight** (they are mockup-cheap to change once rendered in the flows). Phase 2b builds them
  as the default; refinements welcome during the build.
- **[USER-DEFERRED]** The Guide's visible character treatment (avatar/lockup; how it reads in chat vs
  nudges vs decision receipts vs the worker-agent square/circle grammar). Reason: name and concept are
  locked, but the *visual* design is a build-phase craft call delegated to the Steve-Jobs-bar pass in
  Phase 2b per the owner's build directive — best decided by seeing options rendered, not on paper.
- **RESOLVED (owner, 2026-06-11) — per-family stage vocabulary is research-derived, not assumed.** The
  illustrative steps floated during exploration are dropped as placeholders ("those are not the right steps —
  we have to explore online and come up with the right mental models"). **Phase 2c** now owns deriving the
  right stage spine for each family from online research before Phase 3 builds the canvases; the owner signs
  off on the four spines at the end of 2c.
- **RESOLVED (owner, 2026-06-11) — no P2 cut line; all surfaces ship in v1.** US7 (reqs-doc loop), US8
  (skillification/agent ops), and US9 (Layer-2) all ship in v1. If the budget tightens, **extend the
  timeline rather than cut scope.** The data-driven render keeps the marginal cost of each surface low,
  which is what makes a no-cut v1 feasible.
- **[USER-DEFERRED]** Walkthrough format for external showings — driver.js overlays vs. a separate
  "demo script" overlay vs. both. Reason: low-stakes Phase 6 detail; default is both (driver.js overlay
  + optional demo-script overlay), revisable when the flows are clickable and the showing context is known.

## Spec References

- **Spec registry checked** (`docs/specs/_registry.md`). All seven existing specs govern the **cast-server
  runtime/infrastructure** (delegation contract, output-json contract, init conventions, UI-testing harness,
  runs screen, user-invocation tracking, subagent/skill capture). **None govern this deliverable.**
- **No spec applies and none is contradicted.** FR-020 is explicit: the prototype is greenfield, *not*
  constrained by the current cast-server UI or stack. Its HTML choices imply nothing about production
  architecture (Out of Scope). No `/cast-update-spec` action is required by this plan.
- **Forward note:** the prototype is intended to become a *design source of truth* (SC-006 maps each surface
  to a buildable follow-on goal). When those follow-on goals are planned, new product specs will likely be
  authored then — but that is downstream of this prototype, not part of it.
