---
status: refined
confidence:
  intent: high
  behavior: medium
  constraints: medium
open_unknowns: 2
questions_asked: 3
---

# Spike Source — Export Scheduler (anchor-survival test bed)

> **Spec maturity:** draft
> **Version:** 0.2.0
> **Linked files:** requirements.human.md

## Intent

**Job statement:** When an analyst finishes configuring a report, they want to schedule it to
export automatically on a recurring cadence, so that stakeholders receive fresh data without
anyone re-running the export by hand.

## User Stories

### US1 — Recurring schedule (Priority: P1)

**As an** analyst, **I want to** set a recurring cadence for a report export, **so that**
stakeholders receive the report on schedule without anyone lifting a finger.

### US2 — Failure visibility (Priority: P2)

**As an** analyst, **I want to** be notified when a scheduled export fails, **so that** I can
intervene before stakeholders notice missing data.

## Functional Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| FR-001 | The scheduler shall accept a cron-style cadence expression and validate it before saving | US1 |
| FR-002 | The system shall run each due export within sixty seconds of its scheduled instant | US1 |
| FR-004 | The scheduler shall alert the report owner if a run fails | US2 |
| FR-005 | The system shall expose a read-only history of the last fifty export runs with their outcomes | US2 |
| FR-006 | The scheduler shall let an operator pause and resume a schedule without deleting it | US1 |

## Success Criteria

| ID | Criterion | Source |
|----|-----------|--------|
| SC-001 | A schedule created with a valid cron expression produces its first export within one cadence interval | US1 |
| SC-002 | A failed export run delivers a failure notification to the schedule owner within five minutes | US2 |
| SC-003 | The export history view lists runs newest-first with a status badge per run | US2 |

## Constraints

- The export pipeline shall reuse the existing report-rendering service without modification.
- Cadence expressions shall be limited to a minimum interval of fifteen minutes.

## Out of Scope

- Ad-hoc one-off exports triggered manually outside any schedule.
- Delivery channels other than email such as Slack or webhook in this version.

## Directional Ideas (non-binding HOW)

- A durable job queue such as a DB-backed outbox likely fits the at-least-once delivery need
  better than an in-process timer.
