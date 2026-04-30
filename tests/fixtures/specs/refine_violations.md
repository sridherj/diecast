---
status: refined
---

# Notification System — Refined Requirements (intentionally broken)

> **Spec maturity:** draft
> **Version:** 0.1.0

## Intent

Send notifications to users.

## User Stories

### US1 — User receives a notification when something happens

**As a** product user, **I want to** receive notifications, **so that** I stay
informed.

**Independent test:** trigger an event; user sees a notification within 5s.

**Acceptance scenarios:**

- **Scenario 1:** WHEN an event fires, THE SYSTEM SHALL push a notification.

### US2 — Notifications respect user preferences (Priority: P2)

**As a** product user, **I want to** opt out of notification categories,
**so that** I am not spammed.

[NEEDS CLARIFICATION: which channels are required at v1 — email, in-app, or both?]

(no acceptance scenarios written — intentionally broken)

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | Deliver notifications within 5s of the source event. | Soft cap. |
| FR-001 | Allow opt-out per category. | Duplicate identifier. |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | 99% of notifications deliver within 5s. | Telemetry. |

## Open Questions

(intentionally empty — the [NEEDS CLARIFICATION] above is orphaned)
