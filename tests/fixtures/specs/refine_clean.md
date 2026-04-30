---
status: refined
confidence:
  intent: high
  behavior: high
  constraints: high
  out_of_scope: high
open_unknowns: 0
questions_asked: 3
---

# Cast Doctor — Refined Requirements

> **Spec maturity:** draft
> **Version:** 0.1.0
> **Linked files:** bin/cast-doctor

## Intent

Provide a one-shot environment self-check so a new contributor can confirm
their machine is ready to run the Diecast test suite.

## User Stories

### US1 — Self-check passes on a healthy machine (Priority: P1)

**As a** new contributor, **I want to** run a single command and see green,
**so that** I trust my environment before hitting the test suite.

**Independent test:** Fresh clone on Ubuntu 24.04 + `bin/cast-doctor` returns 0
within 300s.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `bin/cast-doctor` runs on a healthy machine, THE SYSTEM
  SHALL print a single PASS line and exit 0.
- **Scenario 2:** WHEN `bin/cast-doctor` runs, IF Python 3.11+ is available,
  THE SYSTEM SHALL skip the install hint.

### US2 — Missing dep prints actionable hint (Priority: P2)

**As a** new contributor, **I want to** see exactly which command to run when
something is missing, **so that** I don't have to read internal docs.

**Independent test:** Stub PATH so `uv` is missing; run `bin/cast-doctor`;
output contains the documented install command.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `bin/cast-doctor` finds a missing dep, THE SYSTEM SHALL
  print the install command and exit non-zero.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | Self-check completes within 300s on a healthy machine. | Hard cap. |
| FR-002 | Each missing dep is reported with a copy-paste install command. | One per dep. |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | 95% of new contributors pass `cast-doctor` on first run. | Onboarding survey. |
| SC-002 | The script exits non-zero on every documented failure mode. | Pytest matrix. |

## Constraints

- Must run on Linux + macOS.
- No network calls (offline-friendly).

## Out of Scope

- Auto-installing missing deps.
- Windows native (WSL only).

## Open Questions

(none)
