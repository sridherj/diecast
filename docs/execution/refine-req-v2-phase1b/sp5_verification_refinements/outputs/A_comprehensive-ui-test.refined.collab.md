---
status: refined
scope_mode: hold
confidence:
  intent: medium
  behavior: low
  constraints: low
  out_of_scope: low
open_unknowns: 5
questions_asked: 0
---

# Repeatable UI Test Harness for the Diecast Web App

> **Spec maturity:** draft
> **Version:** 0.1.0
> **Linked files:** docs/plan/ (target plan location), http://127.0.0.1:8000/

<!--
Stage detected: VAGUE IDEA (84 words, no scenarios, exploratory). Framework: JTBD +
Impact Mapping — deliberately NOT padded to full EARS depth (Step 1.3 Template-Enforcer
guard). Thin/low-confidence sections below are licensed by the detected stage, not gaps
to be confabulated.

Scope mode: HOLD SCOPE — no scope signals detected. (Searched for the canonical
signal words "MVP"/"minimum"/"spike"/"v0" and "comprehensive"/"full-featured"/"dream"/
"ideal"/"10x"; none present. "across all screens" / "all tabs" describe coverage breadth,
not output ambition, so they do not move the scope dial.)

Reviewer: review skipped: stub-sized input (Decision #6 — <200-word Stage-1 stub; too
little substance for adversarial review to add value).
Auto-persisted: non-interactive run (headless; no human at the HARD GATE — Decision #1).
-->

## Intent

**Job statement:** When I make a change to the Diecast web app, I want to re-run a complete
UI test pass across every screen and tab on demand, so that I can confirm nothing visibly
broke without hand-clicking through the app each time.

The raw ask is a *solution sketch* ("create test agents with delegation", "execute with
playwright") wrapped around a thinner *problem*: there is no repeatable, on-demand UI
regression check. Problem-space framing (per Step 1.2): the durable need is *trustworthy,
re-runnable UI verification I can trigger anytime*; Playwright and delegated test agents are
candidate solutions that belong in the plan, not pinned as requirements here.

## User Stories

### US1 — Run a full UI test pass on demand (Priority: P1)

**As an** engineer iterating on the Diecast UI, **I want to** trigger a complete
screen-and-tab test pass at any time, **so that** I can catch visible regressions before
they ship.

**Independent test:** From a clean checkout with the app running on http://127.0.0.1:8000/,
invoke the harness once and observe a pass/fail result covering every screen.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the engineer triggers the UI test harness, THE SYSTEM SHALL exercise
  every screen and tab of the app and report a per-screen pass/fail result.
- **Scenario 2:** WHEN a test run finishes, IF the run created transient goals, runs, or
  files, THE SYSTEM SHALL remove them so only the reusable test agents/harness remain.

### US2 — Keep the harness, discard the run artifacts (Priority: P2)

**As an** engineer re-running the suite repeatedly, **I want** the test agents and plan to
persist while the per-run goals/runs/files are cleaned up, **so that** repeated runs do not
accumulate throwaway state.

**Independent test:** Run the harness twice; confirm the second run starts from the same
clean baseline and leaves no residue from the first.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a run completes, THE SYSTEM SHALL retain the test agents and the
  stored plan under `docs/plan/`.
- **Scenario 2:** WHEN a run completes, THE SYSTEM SHALL delete the run records, scratch
  goals, and generated files created solely for that run.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | The harness shall drive the live app at a configurable base URL (default http://127.0.0.1:8000/). | URL should not be hard-coded. |
| FR-002 | The harness shall be invokable on demand and produce a per-screen pass/fail summary. | "run this anytime" is the core ask. |
| FR-003 | The harness shall clean up transient run state (goals, runs, files) while preserving the reusable test agents and the plan. | Persist agents + plan; discard run residue. |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | A single invocation exercises every screen and tab and emits a per-screen result. | Run the harness; inspect the summary covers all known screens. |
| SC-002 | Two consecutive runs leave no accumulated throwaway goals/runs/files. | Diff app state before/after two runs. |
| SC-003 | The plan document exists under `docs/plan/`. | File presence check. |

## Constraints

- Targets the live app at http://127.0.0.1:8000/ (the user's stated local instance).
- Playwright is the user's *suggested* driver, not a hard requirement — recorded here as a
  candidate, decided in the plan.

## Out of Scope

- Non-UI (API-only) test coverage — this ask is explicitly about the UI/screens.
- *(Stage-1 stub: Out-of-Scope boundaries are intentionally thin and low-confidence; they
  firm up once the high-risk unknowns in Open Questions are resolved — not padded here.)*

## Decisions

*No decisions recorded this refinement.*

## Open Questions

- **[NEEDS CLARIFICATION: screen inventory]** — what is the authoritative list of "all
  screens" and "all tabs"? Without it, full-coverage cannot be asserted. (User to enumerate,
  or derive from the route table.)
- **[NEEDS CLARIFICATION: pass/fail definition]** — what counts as a UI failure (console
  error, visual diff, broken interaction, HTTP error)? Determines what the harness asserts.
- **[NEEDS CLARIFICATION: operations on screen]** — "do all operations on screen" is broad;
  which interactions are in the must-cover set vs. nice-to-have?
- **[NEEDS CLARIFICATION: delegation requirement]** — are delegated test agents a hard
  requirement or one candidate design? The second-brain reference suggests delegation but
  does not mandate it.
- **[NEEDS CLARIFICATION: cleanup boundary]** — precisely which artifacts are "transient"
  (safe to delete) vs. part of the reusable harness?
