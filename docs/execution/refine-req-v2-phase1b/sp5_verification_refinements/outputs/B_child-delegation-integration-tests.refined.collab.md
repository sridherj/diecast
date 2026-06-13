---
status: refined
scope_mode: hold
confidence:
  intent: high
  behavior: medium
  constraints: medium
  out_of_scope: high
open_unknowns: 2
questions_asked: 0
---

# Child-Delegation Integration Tests (HTTP + Subagent), with Fixes

> **Spec maturity:** draft
> **Version:** 0.1.0
> **Linked files:** docs/specs/cast-delegation-contract.collab.md, skills/claude-code/cast-child-delegation/SKILL.md

<!--
Stage detected: SPECIFIC FEATURE with strong detail (275 words, explicit resolved Q&A,
named reference material and counterparts). Framework: Example Mapping (rules + examples +
questions) → EARS acceptance scenarios.

Scope mode: HOLD SCOPE — no scope signals detected. (No "MVP"/"spike"/"v0" and no
"comprehensive"/"dream"/"10x" tokens. "BOTH transports (HTTP + subagent)" describes
coverage breadth, not output ambition — it does not move the scope dial.)

Reviewer: independent review skipped: Agent tool unavailable (reviewer dispatch denied on
this run — fail-soft per Step 2.5 / Decision #3). Refinement completed without the
adversarial pass; the evidence-quoting mandate and the zero-silent-failure Open-Questions
invariant still hold.
Auto-persisted: non-interactive run (headless; Decision #1).
-->

## Intent

**Job statement:** When I rely on parent→child agent delegation as a core Diecast feature, I
want the integration-test discipline that worked in second-brain re-established against
diecast's file-canonical contract — red tests that pin the currently-suspected breakages,
then the fixes shipped in the same goal — so that I can trust delegation actually works across
both transports instead of failing silently.

Intent is HIGH confidence: the user stated the need and the desired outcome verbatim —
"it was very useful to confirm this important feature worked. Right now I feel its breaking in
quite a few ways" and "Re-establish the test discipline that worked in second-brain … adapted
to diecast's file-canonical contract."

## User Stories

### US1 — Pin delegation contract violations with red tests (Priority: P1)

**As a** Diecast maintainer, **I want** integration tests that fail loudly on allowlist,
depth, and output-JSON contract violations, **so that** silent contract drift is caught
instead of slipping through.

**Independent test:** Run the suite against a deliberately allowlist-violating delegation;
confirm a test fails with a clear contract-violation message.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a child is dispatched to an agent outside the parent's allowlist, THE
  SYSTEM SHALL reject it and a test SHALL assert the rejection (no silent pass-through).
- **Scenario 2:** WHEN delegation depth exceeds the configured limit, THE SYSTEM SHALL refuse
  the dispatch and a test SHALL assert the refusal.
- **Scenario 3:** IF a child writes a malformed or missing output.json, THEN the parent SHALL
  surface a contract error and a test SHALL assert it (not a mis-finalized success).

### US2 — Cover both transports (HTTP + subagent) (Priority: P1)

**As a** Diecast maintainer, **I want** the suite to exercise both the HTTP and subagent
delegation transports, **so that** a regression in either is caught.

**Independent test:** Run the HTTP E2E tier and the subagent manual checklist; confirm both
transports are exercised.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the test suite runs, THE SYSTEM SHALL exercise HTTP delegation via a
  live T2 E2E path and subagent delegation via a manual checklist.
- **Scenario 2:** WHEN a run completes, THE SYSTEM SHALL leave no orphan `.delegation`,
  `.prompt`, or `.tmp` artifacts, and a test SHALL assert cleanup.

### US3 — Ship fixes for the pinned breakages in the same goal (Priority: P2)

**As a** Diecast maintainer, **I want** the suspected breakages fixed in the same goal once
red tests pin them, **so that** the feature is verified working end-to-end, not just measured.

**Independent test:** After fixes, the previously-red tests pass and the feature works on a
live delegation.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the red tests exist and the fixes land, THE SYSTEM SHALL make the
  previously-failing tests pass without weakening their assertions.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | The suite shall assert allowlist enforcement on child dispatch. | Q4 observed symptom: allowlist violations get through silently. |
| FR-002 | The suite shall assert delegation depth-limit enforcement. | Q4 symptom: depth violations. |
| FR-003 | The suite shall assert output.json contract validity (shape + presence) and correct parent finalization. | Q4: 422 shape; parent stalls/mis-finalizes. |
| FR-004 | The suite shall assert post-run cleanup of orphan `.delegation`/`.prompt`/`.tmp` files. | Q4: orphan-artifact symptom. |
| FR-005 | The suite shall cover both HTTP (T1 mocked + T2 live E2E) and subagent (manual checklist) transports. | Q2 + Q3 decisions. |
| FR-006 | The pinned breakages shall be fixed within the same goal. | Q1 decision. |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | Allowlist, depth, and output-json violations each cause a test failure when present. | Inject each violation; observe red. |
| SC-002 | Both transports are exercised by the suite. | Run T2 E2E + subagent checklist. |
| SC-003 | No orphan `.delegation`/`.prompt`/`.tmp` files remain after a run. | Filesystem diff post-run. |
| SC-004 | After fixes, previously-red tests pass with unchanged assertions. | Re-run suite. |

## Constraints

- Use diecast's **file-canonical** contract — do NOT copy second-brain's changed contract
  details; reuse only intent/behaviors/quality-bar as reference.
- Test tiers fixed by the user: T1 mocked + T2 live HTTP E2E + manual subagent checklist.

## Out of Scope

- Re-deriving the delegation contract itself — `docs/specs/cast-delegation-contract.collab.md`
  is canonical; this goal tests and fixes against it, it does not redefine it.
- Primitive-level coverage already held by `tests/test_b3_*/b4_*/b5_*` — this goal adds the
  missing *feature-level* tests, not duplicates of the primitives.

## Decisions

| Date | Chose | Over | Because |
|------|-------|------|---------|
| 2026-05-01 | Tests AND fixes for the broken behaviors in the same goal | Tests-only (defer fixes to a later goal) | Q1 — re-establishing the discipline only matters if the feature is confirmed working, so fixes ship alongside the red tests |
| 2026-05-01 | A new goal covering BOTH transports (HTTP + subagent) | Extending an existing goal / a single transport | Q2 — both transports are suspected broken, so both must be in scope from the start |
| 2026-05-01 | T1 mocked + T2 live HTTP E2E + manual subagent checklist | Mocked-only tests | Q3 (Recommended) — live E2E + a manual checklist catch the integration/contract drift that mocks miss |

## Open Questions

- **[NEEDS CLARIFICATION: subagent E2E automation]** — the subagent transport is covered by a
  *manual* checklist (Q3); is automating it in scope later, or permanently manual?
- **[NEEDS CLARIFICATION: fix boundary]** — which of the Q4 symptoms are in-scope to fix in
  this goal vs. filed as follow-ups if they prove deep (e.g. mixed-transport preamble
  malformation)?
