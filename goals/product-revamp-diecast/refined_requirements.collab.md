---
status: refined
confidence:
  intent: high
  behavior: high
  constraints: high
  out_of_scope: high
open_unknowns: 2
questions_asked: 12
---

# Product Revamp: Diecast — Vision Prototype (Clickable Mockup)

> **Spec maturity:** draft
> **Version:** 0.3.0
> **Linked files:** requirements.human.md, goals/revamp-diecast/requirements.human.md,
> goals/refine-requirements-v2/refined_requirements.collab.md,
> /data/workspace/second-brain/taskos/goals/taskos-gtm/presentation_v3/narrative.collab.md

## Intent

**Job statement:** When SJ looks at Diecast today (a tight requirements→exploration→planning→
execution pipeline that "no one understands"), he wants a clickable HTML prototype that makes
his product vision concrete — an opinionated, workflow-adaptive canvas steered by chat, with
agents as hireable first-class citizens — so he can refine the open-ended ideas against
something he can *feel*, show it to peers/companies without apology, and then execute toward a
validated target instead of an abstraction.

**Deliverable (locked):** a navigable, self-contained HTML/JS/CSS prototype with realistic fake
data. No backend, no real agents. Browser-openable. Flows are clickable end-to-end; fluidity is
*demonstrated, not described* (e.g., a chat course-change visibly morphs the canvas).

**Product posture (locked through refinement):**

1. **Opinionated product, meaningful defaults.** The canvas is the opinionated guided
   experience: it always shows where you are and nudges the sensible next step. Chat is the
   power lever — change course, override defaults, ask for things the canvas didn't offer.
   Pure-terminal users bypass the UI entirely via Claude Code + the same skills/agents. One
   substrate, three access tiers: **terminal / chat / canvas**.
2. **Canvas-primary, chat-steered.** A persistent chat rail sits beside a WHAT-first adaptive
   canvas that is the source of truth. Pure chat-first was considered and rejected: it would
   rebuild Claude Code with extra steps, and the WHAT would live in scrollback. Artifacts
   generated in chat (hiring report, spike result) are *promotable/pinnable* onto the canvas.
3. **WHAT-primary, HOW as drill-in.** AI does most of the execution and keeps it somewhat
   blackbox; the product reflects that. Top level is the WHAT (outcome, state, evidence);
   execution detail (runs, dispatch trees, maker-checker loops) lives behind an execution tab.
   Driven by the increased capability of Claude workflow/goal types.
4. **Testing is the outcome of the WHAT.** Output evidence (screenshots, data visualization,
   HTML output) is a first-class surface, not a buried log.
5. **Decisions are first-class records.** Decisions made at any phase are tracked with
   rationale and time, clarified with the user when they exceed the autonomy the user
   expects, and surfaced at the right places in the product.

**Target users:** Eng primary; PM secondary (now or future — the design must be extensible to
PM, the shared board is the main PM-facing surface).

## User Stories

### US1 — Opinionated adaptive canvas + chat steering (Priority: P1)

**As an** engineer working a goal, **I want** a WHAT-first canvas that adapts its shape to my
workflow and a chat rail that can redirect it, **so that** I get guided defaults without losing
control of direction.

**Independent test:** Open a goal mid-flight; the canvas shows current WHAT state + a nudged
next step. Type "this is actually a bug, not a feature" in chat; the canvas visibly morphs from
feature stages to the debug-loop shape without losing goal context.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a goal is opened, THE SYSTEM SHALL render the WHAT-first canvas for its
  workflow family, showing current state and an explicitly nudged next step.
- **Scenario 2:** WHEN the user redirects course via chat, THE SYSTEM SHALL morph the canvas to
  the new workflow family's shape in a visible transition, preserving goal context.
- **Scenario 3:** WHEN chat produces an artifact (e.g., a hiring report), THE SYSTEM SHALL allow
  promoting/pinning it onto the goal's canvas as a persistent object.
- **Scenario 4:** WHEN any canvas screen renders, THE SYSTEM SHALL make the default next action
  visually primary while keeping override paths (chat, manual navigation) available.

### US2 — Four workflow-family clickthroughs (Priority: P1)

**As a** user with different kinds of work, **I want** the prototype to demonstrate four
contrasting workflow families end-to-end, **so that** "the UI adapts per workflow" is proven by
contrast rather than claimed.

**Locked flows:** (1) **New feature / initiative** — richest backbone flow; (2) **Bug fix /
debug loop** — hypothesis→experiment→observation→iterate, maximally different canvas shape;
(3) **Spike / quick conclusion** — time-boxed question → conclusion artifact feeding a
decision (spike_ref); (4) **Data analysis / research** — question → data sources → analysis →
visualized output.

**Independent test:** From the prototype entry screen, each of the four flows is clickable
start-to-finish with realistic fake data; the feature and debug flows have visibly different
stage structures.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a user enters any of the four flows, THE SYSTEM SHALL present a canvas
  whose stages match that family (e.g., debug shows hypothesis→experiment→observation with an
  iteration counter, not req→explore→plan→execute).
- **Scenario 2:** WHEN a flow involves iteration (debug loops, requirement versions), THE
  SYSTEM SHALL display iteration history cleanly (e.g., "iteration 2/3") rather than hiding
  repeat passes.
- **Scenario 3:** WHEN the spike flow concludes, THE SYSTEM SHALL produce a conclusion artifact
  that is referenced from a decision (spike_ref linkage).
- **Scenario 4:** WHEN the data-analysis flow concludes, THE SYSTEM SHALL present the answer as
  visualized output (chart/table/HTML), not prose-only.

### US3 — WHAT-primary with execution drill-in (Priority: P1)

**As a** goal owner in an AI-does-the-execution world, **I want** the top level of every goal
to be the WHAT (outcome, state, evidence) with HOW details behind an execution tab, **so that**
the product reflects how AI-native development actually distributes attention.

**Independent test:** Open the feature flow's goal screen; the first screenful contains only
WHAT content (outcome, progress, evidence, next step). One click into "execution" reveals runs,
agent dispatch, and maker-checker detail.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a goal canvas renders, THE SYSTEM SHALL show WHAT content (outcome,
  status, evidence, next nudge) above the fold and confine HOW detail to an execution tab.
- **Scenario 2:** WHEN the execution tab is opened, THE SYSTEM SHALL reveal progressively
  deeper detail: run list → one run's dispatch tree (e.g., 13 sub-agents) → maker-checker
  iteration with rework budget and named exits (fix / retry / escalate).
- **Scenario 3:** IF execution needs the human (escalation, approval), THEN THE SYSTEM SHALL
  surface that at the WHAT level — the user never has to poll the execution tab to discover
  they are blocked.

### US4 — Test & outcome evidence surfaces (Priority: P1)

**As a** goal owner, **I want** test results and output evidence shown in the richest fitting
form — screenshots, data visualizations, rendered HTML output — **so that** verifying the WHAT
is a glance, not an archaeology session.

**Independent test:** In the feature flow, the "done" state shows embedded visual evidence
(e.g., UI screenshots + test summary); in the data-analysis flow, the output is a rendered
visualization.

**Acceptance scenarios:**

- **Scenario 1:** WHEN work completes in any flow, THE SYSTEM SHALL present outcome evidence in
  a form fitted to the work type (screenshots for UI work, charts for analysis, rendered HTML
  reports for documents, test-run summaries for code).
- **Scenario 2:** WHEN evidence exists for a goal, THE SYSTEM SHALL surface it at the WHAT
  level (canvas/ticket), with drill-in to full detail.
- **Scenario 3:** WHEN a checker validates a maker's output, THE SYSTEM SHALL show the
  compliance evidence (rule checks passed/flagged) alongside the artifact, not only a
  pass/fail badge.

### US5 — Board → ticket → decision → escalation arc (Priority: P1)

**As an** eng lead (and as the PM-extensibility proof), **I want** the four-frame arc from the
vision deck as clickable surfaces, **so that** "humans + agents on one board" is experienced:
shared board → one ticket's maker-checker activity log → decision artifact → escalation rail.

**Independent test:** From the feature flow's execution area, click board → ticket CAST-412 →
its decision artifact → the L3 escalation; the four screens read as frames of one continuous
story with consistent chrome and vocabulary.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the board renders, THE SYSTEM SHALL show humans and agents as peer
  assignees with an assignee filter (any / human / agent / checker) and the "publishes INTO
  your PM tool" framing.
- **Scenario 2:** WHEN a ticket is opened, THE SYSTEM SHALL show its activity log as a
  maker-checker iteration: checker rule violations as inline comments (e.g., M04/S03/R02), a
  visible rework budget (e.g., 1/3 used), and the resulting PR link.
- **Scenario 3:** WHEN a non-trivial call is made during a run, THE SYSTEM SHALL capture it as
  a structured decision artifact (id, reversibility level, escalation, spike_ref,
  consequences) attached to the ticket.
- **Scenario 4:** IF a decision carries L3 reversibility, THEN THE SYSTEM SHALL stop the agent
  and hand `@you` exactly three pre-framed options on the same board (escalation rail).

### US6 — Agent hiring & assessment (Priority: P1)

**As a** project owner needing a capability (e.g., RBAC), **I want to** commission an
assessment, federate it across candidate agents, and review a stack-ranked hiring report —
then hire and onboard the winner, **so that** "Hire. Don't install." is a flow I can click,
not a slogan.

**Independent test:** From chat, ask to "hire an rbac-agent"; click through assessment
definition (tasks across product dimensions) → federation to 5-10 candidates → stack-ranked
Google-style hiring report with pros/cons → hire → onboarding (data sources, tastes).

**Acceptance scenarios:**

- **Scenario 1:** WHEN a hire is requested, THE SYSTEM SHALL generate an assessment spanning
  multiple tasks across product dimensions (user scale, internal/external software, ...).
- **Scenario 2:** WHEN the assessment completes, THE SYSTEM SHALL present a stack-ranked hiring
  report with per-candidate pros/cons and links to actual produced output (repo-style).
- **Scenario 3:** WHEN browsing candidates, THE SYSTEM SHALL show marketplace credibility
  (apify-style: "99.9% compliant code in 2 maker-checker loops across 505 runs") and a full
  agent resume (role, I/O contract, autonomy level, paired checker, benchmark, sample output).
- **Scenario 4:** WHEN an agent is hired, THE SYSTEM SHALL present an onboarding step pointing
  it at the org's data sources and tastes before first use.
- **Scenario 5:** WHEN the marketplace renders, THE SYSTEM SHALL show archetype diversity
  (Maker / Checker / Decision / Spike / Escalation / Mentor) with maker-checker pairing shown
  in-card (a maker's checker is never a separate card).

### US7 — Requirements-doc loop (Priority: P2)

**As a** goal owner, **I want** the requirements surfaces from refine-requirements-v2 made
visible in the prototype — HTML render with classification pill, L1/L2/L3 progressive
disclosure, inline comments driving versions, living-source-of-truth notifications — **so
that** the front door of every flow demonstrates the requirements vision.

**Independent test:** In the feature flow, open the requirements doc: classification pill at
top, collapsible L1/L2/L3 hierarchy, an inline comment thread, a v2-with-change-summary
moment, and one "requirements updated from planning — review the delta" notification.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a refined requirements doc renders, THE SYSTEM SHALL show the workflow
  classification prominently (pill) and apply L1/L2/L3 visual treatments with progressive
  disclosure.
- **Scenario 2:** WHEN a reviewer selects a requirement element, THE SYSTEM SHALL show an
  anchored inline comment with open/resolved state.
- **Scenario 3:** WHEN a new version exists, THE SYSTEM SHALL show a change summary anchored to
  affected elements (delta review, not re-read).
- **Scenario 4:** WHEN a downstream phase changes a requirement, THE SYSTEM SHALL show a
  notification naming what changed and the originating phase.

### US8 — Skillification & agent ops (Priority: P2)

**As an** engineer growing a team of agents, **I want** screens for skill creation (private vs
company-wide), agent versions, usage metrics, and monitoring, **so that** operating agents
looks as manageable as operating services.

**Independent test:** Navigate to the agent-ops area: a skill-creation flow distinguishing
private from company-wide skills, an agent detail page with version history, usage metrics,
and a monitoring view.

**Acceptance scenarios:**

- **Scenario 1:** WHEN creating a skill, THE SYSTEM SHALL offer a near-zero-friction path
  (could be as simple as a Claude command) and a private vs company-wide visibility choice.
- **Scenario 2:** WHEN viewing an agent, THE SYSTEM SHALL show version history, usage metrics
  (runs, compliance rate, rework loops), and current monitoring state.
- **Scenario 3:** WHERE an org runs both public and private agents, THE SYSTEM SHALL present
  the two catalogues (open Diecast modules + internal tested modules) behind one
  discover-and-hire mechanism.

### US9 — Layer-2 surfaces (Priority: P2)

**As a** skeptical senior IC, **I want to** see that Layer-2 (workflow) is real and enumerable
— the contract catalogue, the agent-chain pipeline view, and a portfolio dashboard — **so
that** the orchestration claim is backed by visible structure.

**Independent test:** Open the Layer-2 area: a catalogue of 12 named workflow contracts, a
pipeline visualization of an 8-agent chain, and a portfolio dashboard of projects shipped
through the workflow.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the contract catalogue renders, THE SYSTEM SHALL list the named
  contracts (12) as the proof-of-enumerability of Layer-2.
- **Scenario 2:** WHEN a goal is executing, THE SYSTEM SHALL be able to show its position in
  the agent chain (e.g., refine → decompose → research → synthesize → plan → detail →
  orchestrate → run).
- **Scenario 3:** WHEN the portfolio dashboard renders, THE SYSTEM SHALL show multiple projects
  run through the workflow (proof by volume).

### US10 — Decision tracking across phases (Priority: P1)

**As a** goal owner delegating most execution to AI, **I want** decisions made at any phase
tracked with rationale and time, clarified with me when they exceed the autonomy I expect,
and surfaced where I'd look for them, **so that** I can trust the blackbox without losing
the "why" behind what it did.

**Independent test:** Walk any flow; at least one decision record (what was decided,
rationale, time, originating phase/agent) is visible in context, and at least one
autonomy-gated moment shows the system pausing to clarify with the user instead of deciding
silently.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a non-trivial decision is made at any phase (requirements,
  exploration, planning, execution), THE SYSTEM SHALL record it with rationale, timestamp,
  originating phase/agent, and reversibility level.
- **Scenario 2:** WHEN a pending decision exceeds the autonomy the user expects, THE SYSTEM
  SHALL clarify with the user before proceeding; otherwise it SHALL decide, record, and move
  on.
- **Scenario 3:** WHEN viewing a goal surface (canvas, requirements doc, ticket), THE SYSTEM
  SHALL surface the decisions relevant to that context in place, with drill-in to the full
  record.
- **Scenario 4:** WHEN a user reviews a goal's history, THE SYSTEM SHALL provide a decision
  trail across phases (not only execution-phase decision artifacts).

**Relationship to US5:** the execution-phase decision artifact (US5 Scenario 3) is one
instance of this; US10 generalizes decision capture to every phase and adds the
autonomy-gated clarification behavior.

**Locked autonomy model (Q#7):** reversibility-keyed defaults — L1 decide-and-record, L2
decide-record-and-notify, L3 ask first (reuses the US5 escalation-rail mechanism) — with a
per-goal autonomy dial (e.g., conservative / balanced / autonomous) that shifts those
thresholds. Opinionated default, user override on top.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | The deliverable shall be a self-contained, browser-openable HTML/JS/CSS clickable prototype with realistic fake data and no backend | locked deliverable |
| FR-002 | The prototype shall have an entry screen that routes into the four workflow-family flows and the standalone areas (marketplace, agent ops, Layer-2) | demo navigability |
| FR-003 | The canvas shall be the primary surface: WHAT-first, opinionated, always showing current state and a nudged next step | US1/US3 |
| FR-004 | A persistent chat rail shall steer the canvas; at least one scripted chat interaction shall visibly morph the canvas between workflow families | US1; the fluidity demo moment |
| FR-005 | Chat-generated artifacts shall be promotable/pinnable onto the goal canvas | US1 Scenario 3 |
| FR-006 | Each of the four locked workflow families shall have a distinct canvas shape and an end-to-end clickthrough | US2 |
| FR-007 | Iteration (debug loops, requirement versions, re-entered phases) shall be visible as first-class history, not hidden | US2; fluidity principle |
| FR-008 | Execution detail (runs, dispatch trees, maker-checker loops, rework budgets, named exits) shall live behind an execution tab, with human-needed moments surfaced at WHAT level | US3 |
| FR-009 | Outcome evidence shall render in fitted forms: screenshots, data visualizations, rendered HTML, test summaries | US4 |
| FR-010 | The board→ticket→decision→escalation arc shall be four connected clickable screens with continuous chrome and canonical vocabulary (assignee filter any/human/agent/checker; rework budget; reversibility L1/L2/L3; three pre-framed escalation options) | US5; reuse preso a08–a11 designs |
| FR-011 | The agent-hiring flow shall cover assessment → federation → stack-ranked report → hire → onboard, with marketplace credibility stats and full agent resumes | US6 |
| FR-012 | Skill creation shall demonstrate private vs company-wide visibility and a near-zero-friction creation path | US8 |
| FR-013 | Agent detail shall show versions, usage metrics, and monitoring | US8 |
| FR-014 | The requirements doc surface shall show classification pill, L1/L2/L3 progressive disclosure, anchored inline comments, version change summary, and a downstream write-back notification | US7; mocks refine-requirements-v2 |
| FR-015 | Layer-2 surfaces: contract catalogue (12 named), agent-chain pipeline view, portfolio dashboard | US9 |
| FR-016 | Spike tasks shall be first-class: a visible spike type whose conclusion artifact is referenced by decisions (spike_ref) | US2 Scenario 3 |
| FR-017 | The prototype shall demonstrate the three access tiers (terminal / chat / canvas) over one skill/agent substrate via one side-by-side moment: a terminal pane invoking the same skill next to the canvas doing it with defaults, same artifact landing either way; hosted in the spike flow | locked positioning; Q#9 |
| FR-018 | Brand and vocabulary shall follow the locked v3 rules: Diecast product name, lowercase `cast-*` modules, Layer (not Tier), maker-checker pair as the quality unit, no GPT-isms, hyphens not em dashes | continuity with preso v3 |
| FR-019 | Polish bar: consistent design system, realistic fake data, no lorem ipsum; pixel-perfection not required | self-first, showable-second |
| FR-020 | The design shall not be constrained by the current cast-server UI or stack; greenfield design informed by (not bound to) today's tabs | owner principle |
| FR-021 | Decisions at any phase shall be recorded with rationale, timestamp, originating phase/agent, and reversibility level | US10 |
| FR-022 | Decisions exceeding the user's expected autonomy shall pause for clarification; others shall be decided, recorded, and surfaced. Autonomy model: reversibility-keyed defaults (L1 decide-and-record, L2 decide-record-notify, L3 ask first) shifted by a per-goal autonomy dial | US10 Scenario 2; locked Q#7 |
| FR-023 | Decisions shall be surfaced in context on the relevant goal surfaces, with a cross-phase decision trail available per goal | US10 Scenarios 3-4 |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | SJ can click every locked flow end-to-end and judge each vision thread as keep / change / drop | walkthrough session producing a disposition list per thread |
| SC-002 | A viewer unfamiliar with Diecast can state what the product does and how it differs from raw Claude Code within ~3 minutes of guided clickthrough | test on 1-2 peers |
| SC-003 | The fluidity claim is demonstrated, not described: at least one chat interaction visibly reshapes the canvas between workflow families | present in the prototype, shown in walkthrough |
| SC-004 | The prototype is showable to a company/peer without apology (consistent design, realistic data) | SJ self-report after first external showing |
| SC-005 | The four workflow families have visibly distinct canvas shapes (feature vs debug contrast is obvious at a glance) | side-by-side screenshot check |
| SC-006 | The prototype yields an execution roadmap: each surface maps to a buildable follow-on goal, stack-rankable | post-mockup planning session produces the v2 execution backlog |
| SC-007 | Every flow shows at least one in-context decision record (rationale + time) and the prototype contains at least one autonomy-gated clarification moment | walkthrough check across the four flows |

## Constraints

- **Static prototype only:** no backend, no real agent execution; all data fake but realistic
  and internally consistent (the same fake goal/ticket/agents recur across screens).
- **Interaction model locked:** canvas-primary + chat rail; chat morphs canvas; artifacts
  promotable. Pure chat-first explicitly rejected (would duplicate Claude Code terminal).
- **Terminal parity is a positioning constraint:** the UI is a value-add shell over the same
  skills/agents substrate, never a gate (FR-017).
- **Brand/vocabulary continuity** with presentation_v3 locked rules (FR-018); reuse canonical
  examples (CAST-412, M04/S03/R02, rework budget 1/3, crud-orchestrator) where they fit.
- **Inspiration-first:** before designing, exploration must gather inspiration — internet
  assets/videos on generative-UI / agentic-workspace patterns, the reference repos
  (`~/workspace/reference_repos`: gastown, gbrain, gstack, hermes-agent, openclaw, picoclaw,
  CoPaw, claude-tmux ×2, spec-kit, code-review-graph — pull latest), cast-preso* visual craft,
  and the current Diecast UI as a baseline (not a boundary).
- **Personas:** Eng primary; PM secondary. The shared board is the PM surface, plus exactly
  one PM-framed moment: in the requirements-doc loop (US7), one inline commenter is a PM —
  making the secondary persona visible, not just implied (Q#10). No PM-specific flow in v1.
- **Reuse before re-author:** preso v2/v3 already designed several surfaces (board arc,
  marketplace grid, agent resume, contract catalogue, chain viz); the prototype should lift
  and adapt those designs rather than reinvent.

## Out of Scope

- **Working software:** no real backend, agents, chat inference, or persistence; the prototype
  fakes all of it.
- **Setup/installation work** (mac/win/linux, claude/codex/copilot parity) — vision backdrop
  only (a claim on an about/positioning screen), no flow. Confirmed Q#8.
- **Building refine-requirements-v2 itself** — separate goal; this prototype only mocks its
  surfaces.
- **Real marketplace/federation infrastructure** — the hiring flow is fully mocked.
- **Framework/stack decisions for the real product** — the prototype's HTML choices imply
  nothing about production architecture.
- **Mobile layouts** — desktop-first prototype.
- **Long-tail workflow families** (add tests, heavy UI flow, PRD-only) — designed-for in the
  classification model, not mocked in v1.

## Directional Ideas (non-binding HOW)

- Entry screen as a scenario chooser ("Follow a feature" / "Chase a bug" / "Run a spike" /
  "Answer a data question" / "Hire an agent") so demos self-navigate.
- Scripted chat moments per flow (canned exchanges) keep the prototype static while still
  demonstrating steering; a "demo script" overlay could guide external walkthroughs.
- The canvas-morph could be implemented as CSS-transitioned panel swaps keyed to the scripted
  chat steps — cheap, high-impact.
- Fake-data spine: one coherent fictional org/project reused everywhere (its goals on the
  board, its agents in the marketplace, its requirements doc in the loop) so screens feel like
  one product, not disconnected mocks.
- The preso pipeline's HTML/visual toolkit (cast-preso-visual-toolkit) is reusable craft for
  the prototype's design system.
- Generative-UI references for exploration: CopilotKit generative-UI guide, "the AI agent is
  the front end" (InfoWorld), 2026 adaptive-UX trend roundups.

## Open Questions

Resolved in the Q#7-#12 close-out round (2026-06-11): autonomy model (locked into US10/FR-022),
setup representation (backdrop only, Out of Scope), terminal-parity demonstration (locked into
FR-017), PM persona depth (locked into Constraints). Two items remain, both explicitly deferred
by the owner to the exploration phase:

- **[USER-DEFERRED]** [NEEDS CLARIFICATION: design language] — visual identity direction for
  the prototype. Reason: owner chose to have exploration's inspiration scan propose 2-3
  concrete directions with assets before picking (Q#11).
- **[USER-DEFERRED]** [NEEDS CLARIFICATION: evidence presentation patterns per family] — how
  output evidence (screenshots / data viz / rendered HTML / test summaries) is best shown per
  workflow family. Reason: owner chose to have exploration research 2026 agentic-tool evidence
  patterns and propose per-family treatments (Q#12).
