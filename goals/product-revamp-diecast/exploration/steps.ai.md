# Exploration Steps: Product Revamp — Diecast Vision Prototype

**Goal:** Build a clickable HTML vision prototype of Diecast (spec: refined_requirements.collab.md v0.3.0)
**Approved:** 2026-06-11 (Q#14, option A)
**Framing (locked):** VISION-FIRST. Quality bar is "software built for the future."
Recommendations are unconstrained — existing code/assets are a terrain map, never an
anchor. If something that exists today is useless to the vision, drop it without ceremony.
**Code exploration:** enabled as terrain-mapping only, for steps 2, 3, 4, 6.

---

## Step 1: What should Diecast look and feel like?

**Problem:** The prototype needs a visual identity, and the owner deferred the
design-language decision to this exploration (Q#11). What are the 2026-grade design
directions for an AI-native, agentic development workspace?

**Why (consequence of skipping):** Without an inspiration-grounded design language, the
prototype defaults to generic-AI aesthetics and undersells the vision it exists to convey.

**Research targets:** 2026 generative-UI and agentic-workspace design patterns; design
languages of standout dev tools (Linear-class craft); the reference repos' UIs
(gastown, openclaw, gbrain, claude-tmux, hermes, gstack); cast-preso visual craft as
prior art; inspiration assets/videos worth collecting.

**Success criteria:** 2-3 named design directions, each with concrete reference
assets/examples, ready for the owner to pick from. Resolves [USER-DEFERRED: design language].

---

## Step 2: How should an opinionated canvas + chat steering actually behave?

**Problem:** The locked interaction model is canvas-primary (WHAT-first, opinionated,
nudged next step) with a chat rail that can visibly morph the canvas, plus promotable
chat artifacts. What are the concrete interaction mechanics that make this feel fluid
rather than gimmicky?

**Why:** This is the core thesis of the product. If the mechanics are hand-wavy, the
prototype cannot demonstrate fluidity — the one thing it must demonstrate, not describe.

**Research targets:** chat-to-UI binding patterns (generative UI, CopilotKit-class
frameworks, Artifacts/Canvas patterns); workspace-morphing transitions; nudge/default
UX in opinionated tools; WHAT-primary layouts with progressive execution drill-in;
the three-access-tiers story (terminal / chat / canvas over one substrate).

**Success criteria:** A concrete interaction model for each mechanic (morph, nudge,
promote, drill-in) with named precedents and anti-patterns.

**Code exploration:** terrain map of current cast-server UI surfaces and the FR-017
side-by-side moment's skill-invocation reality.

---

## Step 3: How should each workflow family's canvas be shaped — and its evidence shown?

**Problem:** Four locked families (new feature / bug-fix+debug loop / spike / data
analysis) each need a distinct canvas shape, stage model, and an output-evidence
treatment (screenshots vs data viz vs rendered HTML vs test summaries). The owner
deferred evidence treatments to this exploration (Q#12).

**Why:** Without per-family shapes, the four flows collapse back into one generic
pipeline — exactly the "today it's very tight" failure the goal exists to escape.

**Research targets:** how 2026 agentic tools present run evidence and outcomes;
debugging-loop UX (hypothesis→experiment→observation); spike/timebox patterns;
data-analysis notebook/report UX; iteration-history presentation; workflow
classification taxonomies (validating the refine-requirements-v2 families externally).

**Success criteria:** A canvas blueprint (stages, layout, iteration treatment) plus a
named evidence treatment per family. Resolves [USER-DEFERRED: evidence patterns].

**Code exploration:** terrain map of how goals/phases/tasks render today and what the
preso flow designs (a08-a11) already solved.

---

## Step 4: How do agents appear as colleagues, not tools?

**Problem:** The most differentiated vision claims — shared board with agent assignees,
ticket-level maker-checker activity, agent hiring (assessment → federation → stacked
report → onboard), marketplace credibility/resumes, skill ops (versions, metrics,
monitoring), public vs private catalogues — all need screen-level design.

**Why:** "Hire. Don't install." is the second aha of the whole thesis; if these surfaces
look like admin CRUD, the aha dies.

**Research targets:** agent marketplace UX (apify-class credibility stats), AI-teammate
products (Devin-class), hiring/evaluation report design, PM-tool board/ticket craft
(Linear-class), ops dashboards for non-human workers, private/public catalogue patterns.

**Success criteria:** Screen-level design references for every agent-colleague surface
in the spec (US5, US6, US8, US9).

**Code exploration:** terrain map of preso v2/v3 board/marketplace/resume slide designs
(a08-a13) — the strongest existing assets; lift only what serves the vision.

---

## Step 5: How should decisions and autonomy surface in the product?

**Problem:** US10 (newest requirement): decisions at every phase tracked with
rationale/time, surfaced in context with cross-phase trails, and an autonomy model of
reversibility-keyed defaults (L1 record / L2 record+notify / L3 ask first) shifted by a
per-goal dial. What does great decision-and-autonomy UX look like?

**Why:** This is the trust mechanism for the AI-blackbox posture. Done wrong it's either
nagging (asks everything) or unaccountable (silent blackbox).

**Research targets:** decision-record patterns (ADRs evolved for agentic work), audit
trails that humans actually read, autonomy/permission dials in agentic products,
escalation UX, notification design that informs without nagging.

**Success criteria:** Decision-surfacing patterns + autonomy-dial precedents concrete
enough to mock the clarify-vs-proceed moment per flow.

---

## Step 6: What's the cheapest credible way to build the prototype?

**Problem:** The deliverable is a self-contained clickable HTML prototype (no backend,
realistic fake data, scripted chat moments, canvas-morph transitions, scenario-chooser
entry). What's the build recipe that hits vision-grade quality in days, not weeks?

**Why:** The 10x lens — the wrong build approach turns a mockup into a project.

**Research targets:** static-prototype engineering patterns (state-as-URL/JSON scenario
scripts, CSS view transitions, no-build-step component patterns), fake-data spine design
(one coherent fictional org reused across all screens), demo-script overlays, what
modern prototype tooling offers vs hand-rolled HTML.

**Success criteria:** A build recipe with named techniques, plus a strictly-optional
reuse list (preso HTML, cast-preso-visual-toolkit) filtered to only what serves the
vision — anything useless dropped.

**Code exploration:** inventory of preso v2/v3 slide HTML and visual toolkit for the
optional-reuse list.

---

## Dispatch plan

| # | Step | Web research | Code exploration |
|---|------|--------------|------------------|
| 1 | Design language | ✅ | — |
| 2 | Canvas + chat mechanics | ✅ | ✅ |
| 3 | Family canvases + evidence | ✅ | ✅ |
| 4 | Agents as colleagues | ✅ | ✅ |
| 5 | Decisions & autonomy | ✅ | — |
| 6 | Prototype build approach | ✅ | ✅ |
