---
feature: cast-web-researcher
module: cast-agents
linked_files:
  - agents/cast-web-researcher/cast-web-researcher.md
last_verified: "2026-04-30"
---

# Cast Web Researcher — Spec (backfilled)

> **Spec maturity:** draft
> **Version:** 0.1.0
> **Linked files:** agents/cast-web-researcher/cast-web-researcher.md

## Intent

Backfilled spec for the existing cast-web-researcher agent. Documents
current behavior only — no aspirational features. Inferred from the agent
prompt and its existing test fixtures.

## User Stories

### US1 — Operator runs deep web research on a topic (Priority: P1)

**As a** Diecast operator, **I want to** dispatch cast-web-researcher with a
single topic prompt, **so that** I get a 7-angle research bundle without
manually orchestrating the sub-queries.

**Independent test:** Dispatch the agent with topic "feature flag rollouts";
assert the output JSON has 7 artifact entries, each tagged with one of the
documented angles.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the agent receives a topic prompt, THE SYSTEM SHALL
  emit one artifact per documented research angle (expert, tools, AI,
  community, frameworks, contrarian, first principles).
- **Scenario 2:** WHEN the agent runs, IF a sub-query times out, THE SYSTEM
  SHALL emit `status: partial` with the failing angle named in `errors[]`.

### US2 — Output passes the contract-v2 schema (Priority: P1)

**As a** parent agent, **I want to** consume cast-web-researcher's output
without custom parsing, **so that** I can chain it into downstream agents.

**Independent test:** Validate the emitted output JSON against the
`docs/specs/cast-output-json-contract.collab.md` schema.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the agent terminates, THE SYSTEM SHALL write a
  contract-v2 output file to `<goal_dir>/.agent-run_<RUN_ID>.output.json`.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | Each of the 7 angles produces a separate artifact entry. | One per angle. |
| FR-002 | Each artifact has a `description` non-empty string. | Per contract-v2. |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | 7 artifact entries on every `completed` run. | Test fixture. |
| SC-002 | Output JSON parses cleanly under `docs/specs/cast-output-json-contract.collab.md`. | Schema test. |

## Open Questions

(none)
