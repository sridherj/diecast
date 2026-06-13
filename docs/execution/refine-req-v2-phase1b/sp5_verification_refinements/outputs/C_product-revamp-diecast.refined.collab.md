---
status: refined
scope_mode: expansion
confidence:
  intent: high
  behavior: medium
  constraints: low
  out_of_scope: medium
open_unknowns: 6
questions_asked: 0
---

# Diecast Vision Mockup — Fluid Chat-Guided, WHAT-Primary Workflow Platform

> **Spec maturity:** draft
> **Version:** 0.1.0
> **Linked files:** goals/revamp-diecast/requirements.human.md, goals/refine-requirements-v2/refined_requirements.collab.md

<!--
Stage detected: NEAR-COMPLETE / detailed-with-gaps (738 words, many concrete ideas and
named workflows, but exploratory "grill me" framing). Framework: EARS refinement + gap
analysis.

Scope mode: SCOPE EXPANSION — quoted signal evidence: "don't be constrained with what we
have so far", "represent my vision", "It should be representing a software built for
future", "Is it worth making these workflows top class citizens?". (These are semantic
expansion signals — "dream big / don't constrain" — rather than the literal canonical
tokens; the canonical list is exemplary, not exhaustive. Effect: edge cases and stretch
ideas are captured as Directional/stretch items rather than scoped out.)

Reviewer: independent adversarial reviewer DISPATCHED on this draft (non-stub, fresh-
context general-purpose Agent tool, draft-only). Rubric scores —
Completeness 4 / Consistency 5 / Clarity 3 / Scope 7 / Feasibility 3 — 16 specific issues
returned across the four <7 dimensions. Disposition (convergence guard, single pass then
log): consistency/clarity contradictions FIXED inline below (HOW≡execution equivalence
stated; FR detection softened to reference the open detection mechanism; Constraints marked
directional/unquantified; a redirect work-preservation criterion added as SC-005). The
remaining user-resolvable findings (autonomy model, workflow taxonomy/detection, outcome-
artifact format, spike lifecycle, assistant-agnostic abstraction) are LOGGED to Open
Questions — none silently dropped. (Two findings — "FR run-on line", "single semicolon
line" — were artifacts of the condensed draft sent to the reviewer; the persisted file uses
a proper FR table, so they do not apply to this artifact.)
Auto-persisted: non-interactive run (headless; Decision #1).
-->

## Intent

**Job statement:** When I want to evolve Diecast beyond its current tight requirements →
exploration → planning → execution flow, I want a fluid, chat-guided mockup where the
interface adapts to the *kind* of work (feature vs. bug-fix vs. debugging-loop) and surfaces
WHAT at the top with HOW available on demand, so that I can experience and refine my product
vision before committing to a build.

The writeup is explicitly a vision/exploration artifact ("Create a mock up version of
Diecast that will represent my vision", "Grill me on this") — so Intent is high-confidence on
*direction* and the spec's job is to convert sprawling ideas into named, testable pillars
while honestly parking the unresolved ones.

## User Stories

### US1 — Chat-guided fluid UI that adapts to workflow type (Priority: P1)

**As an** engineer using Diecast, **I want** a chat interface paired with a UI that nudges me
through the right next steps for *this kind* of work, **so that** the tool stops forcing one
rigid requirements→execution path onto every task.

**Independent test:** Start a "bug fix" intent and a "user-facing feature" intent; confirm
the guided steps / surfaced UI differ between them.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the user states an intent, THE SYSTEM SHALL select and display a
  workflow shape appropriate to that intent (e.g. feature vs. bug-fix vs. debugging loop).
- **Scenario 2:** WHEN the user redirects mid-flow via chat, IF the new intent implies a
  different workflow, THE SYSTEM SHALL update what the UI surfaces without losing prior work.

### US2 — WHAT-primary presentation with HOW on demand (Priority: P1)

**As an** engineer in an AI-heavy workflow, **I want** the top level to show WHAT (intent,
outcomes, tests) with execution detail tucked into a drill-down, **so that** the product
reflects AI doing most of the execution as a semi-blackbox. *(Terminology: "HOW" and the
"execution view"/"execution tab" refer to the **same** drill-down surface — reviewer
consistency fix.)*

**Independent test:** Open a goal; confirm the default view leads with WHAT/outcomes and HOW
lives behind an "execution" affordance.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a goal is opened, THE SYSTEM SHALL present WHAT-level content first and
  expose execution detail through a secondary "execution" view.
- **Scenario 2:** WHEN a task completes, THE SYSTEM SHALL surface its *outcome* (test results
  as screenshots / data viz / HTML output) as the primary artifact.

### US3 — First-class decision tracking across phases (Priority: P2)

**As a** user with varying autonomy preferences, **I want** decisions tracked at each phase
with rationale and timestamp and surfaced where they matter, **so that** I retain provenance
of why the product is the way it is.

**Independent test:** Make a decision in one phase; confirm it is recorded with rationale +
time and is visible at the relevant downstream point.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a decision is made at any phase, THE SYSTEM SHALL record it with its
  rationale and timestamp.
- **Scenario 2:** WHEN autonomy settings require confirmation, IF a decision exceeds the
  user's autonomy threshold, THE SYSTEM SHALL clarify with the user before proceeding.

### US4 — Spike tasks as first-class citizens (Priority: P3)

**As an** engineer resolving open-ended questions, **I want** spike tasks treated as a
first-class task type, **so that** quick conclusion-driving investigations are modeled
natively rather than shoehorned into feature tasks.

**Independent test:** Create a spike task; confirm it has a distinct type/lifecycle from a
standard implementation task.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the user creates a spike, THE SYSTEM SHALL model it as a distinct
  first-class task type whose outcome is a conclusion/decision rather than shipped code.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | The system shall pair a chat surface with a UI that adapts surfaced steps to the workflow type. | Detection mechanism is unresolved — see Open Questions (workflow detection); not presumed settled. |
| FR-002 | The system shall support multiple workflow shapes (at minimum: feature, bug-fix, debugging hypothesis→experiment→observation loop). | Canonical taxonomy still open — see Open Questions. |
| FR-003 | The system shall present WHAT-level content as primary and execution detail as a secondary drill-down. | "WHAT as primary … execution tab". |
| FR-004 | The system shall render task outcomes as visual artifacts (screenshots, data viz, HTML). | "Testing is the outcome of WHAT". |
| FR-005 | The system shall record phase decisions with rationale and timestamp and surface them contextually. | Decision Tracking addition. |
| FR-006 | The system shall model spike tasks as a first-class task type. | Stretch/expansion pillar. |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | Two different stated intents produce demonstrably different guided UIs. | Mockup walkthrough of feature vs. bug-fix. |
| SC-002 | The default goal view leads with WHAT; execution detail is one drill-down away. | Inspect default view. |
| SC-003 | A made decision appears with rationale + timestamp at its relevant surface. | Create decision; inspect record + surface. |
| SC-004 | A spike task is creatable with a distinct lifecycle. | Create spike; inspect type. |
| SC-005 | Redirecting intent mid-flow updates the surfaced UI while prior work is preserved (not discarded). | Start a flow, produce an artifact, redirect; confirm the artifact survives. (Reviewer completeness fix — US1's hardest promise now has a criterion.) |

## Constraints

> These constraints are **directional and not yet quantified** (reviewer feasibility finding —
> they are honestly unmeasured at vision stage; quantification is tracked in Open Questions
> rather than asserted as firm).

- This is a **mockup** to represent and refine a vision — not a production build; fidelity of
  *experience* matters more than backend completeness.
- Setup must remain simple across mac/windows/linux and be assistant-agnostic
  (copilot/claude/codex) — carried from the writeup, though its impact on the vision is
  flagged uncertain by the user ("not sure if this has any effect on vision").
- Should draw inspiration from existing tools / the second-brain GTM presentation rather than
  being constrained by today's Diecast UI.

## Out of Scope

- **Agent hiring / assessment marketplace** and **agent credibility-advertising (apify-like
  stats)** — captured as Directional/stretch ideas (expansion mode keeps them visible) but
  excluded from the first mockup's must-build set; they are large enough to be their own goals.
- Production-grade implementation of any pillar (this is a vision mockup).
- Private-vs-company skill separation mechanics beyond acknowledging the need.

## Decisions

| Date | Chose | Over | Because |
|------|-------|------|---------|
| 2026-06-11 | Adopt first-class decision tracking with rationale + timestamp, surfaced in-product | Leaving decisions implicit / undocumented | User added it explicitly during refinement: "track decisions at various phases … document/surface them at right places in product along with rationale/time" |
| 2026-06-11 | Treat WHAT as the primary top-level mode, HOW behind an execution view | Keeping HOW co-equal at the top level | User: "moving towards WHAT as primary … AI does most of the execution and to some extent keeps it as a blackbox" |

## Open Questions

- **[NEEDS CLARIFICATION: workflow taxonomy]** — what is the canonical set of workflow types
  to model in the mockup (feature, bug-fix, debugging-loop, spike, …) and how is the type
  detected from chat?
- **[NEEDS CLARIFICATION: tabs vs fluid surfaces]** — do the existing phase tabs stay, or does
  the UI become fully fluid/chat-driven? The user is explicitly undecided ("not sure if the
  tabs need to change").
- **[NEEDS CLARIFICATION: inspiration assets]** — which external tools/videos are the agreed
  inspiration references before mockup work starts?
- **[NEEDS CLARIFICATION: constraints quantified]** — the Constraints section is qualitative;
  no measurable targets (setup time, performance) are stated. (Reviewer Feasibility finding —
  logged rather than invented.)
- **[NEEDS CLARIFICATION: assessment/hiring scope]** — are agent assessment, hiring, and
  credibility-advertising part of *this* vision mockup or a separate downstream goal?
- **[NEEDS CLARIFICATION: skill privacy model]** — how should private vs. company-wide skills
  differ, and is "just a claude command" the intended mechanism?
- **[NEEDS CLARIFICATION: workflow detection]** — how is workflow type detected from chat
  (classifier, heuristic, explicit pick)? Needs a confidence/misclassification-recovery story.
  (Reviewer: feasibility + consistency — FR-001/FR-002 depend on this.)
- **[NEEDS CLARIFICATION: autonomy model]** — define "autonomy settings", the threshold scale,
  and how a decision is judged to "exceed" it (US3 / FR-005). No data model exists yet.
  (Reviewer: completeness.)
- **[NEEDS CLARIFICATION: outcome artifact contract]** — FR-004's outcome artifacts
  (screenshots / data viz / HTML) need a source/format and an empty/error fallback state.
  (Reviewer: completeness.)
- **[NEEDS CLARIFICATION: spike lifecycle]** — the spike task type (US4 / FR-006) needs
  explicit states/transitions beyond "distinct lifecycle". (Reviewer: completeness.)
- **[NEEDS CLARIFICATION: assistant-agnostic abstraction]** — "assistant-agnostic
  (copilot/claude/codex)" needs an integration surface / capability-parity assumption.
  (Reviewer: feasibility.)
