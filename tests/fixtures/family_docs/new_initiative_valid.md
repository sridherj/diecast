# New Initiative Fixture

## Intent

We are starting a new initiative to ship a workflow-aware refinement surface
because today every goal is forced through one rigid template.

## User Stories

### US1 — Core capability (Priority: P1)

**As a** goal owner, **I want to** classify my writeup into a work family, **so
that** the document I get back is shaped for the work I am actually doing.

**Independent test:** Refine a bug-report writeup and confirm the output is
shaped as a bug_fix document rather than a full initiative spec.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the agent refines a raw writeup, THE SYSTEM SHALL select
  exactly one work family before rendering the document.

## Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-001 | The system shall classify each writeup into one work family. |

## Success Criteria

| ID | Criterion |
|----|-----------|
| SC-001 | At least 90% of writeups are classified into the expected family. |

## Out of Scope

- A lexical fast-path classifier (deferred past v2).
