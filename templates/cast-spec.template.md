# {{Spec Title}}

> **Spec maturity:** draft | accepted | retired
> **Version:** 0.1.0
> **Linked files:** {{path1}}, {{path2}}

This template is the canonical shape for spec documents written by
`cast-refine-requirements` and `cast-update-spec`, and is enforced by
`cast-spec-checker`. It adopts the spec-kit User Story / Priority /
Independent Test / Acceptance Scenarios / `FR-NNN` / `SC-NNN` shape.

## User Stories

### US1 — {{One-line user story}} (Priority: P1)

**As a** {{role}}, **I want to** {{capability}}, **so that** {{benefit}}.

**Independent test:** {{the smallest scenario that proves this user story
works in isolation}}

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN {{trigger}}, THE SYSTEM SHALL {{response}}.
- **Scenario 2:** WHEN {{trigger}}, IF {{precondition}}, THE SYSTEM SHALL {{response}}.

### US2 — {{One-line user story}} (Priority: P2)

**As a** {{role}}, **I want to** {{capability}}, **so that** {{benefit}}.

**Independent test:** {{independent test}}

**Acceptance scenarios:**

- **Scenario 1:** WHEN {{trigger}}, THE SYSTEM SHALL {{response}}.

[NEEDS CLARIFICATION: how should this interact with the auth flow?]

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | {{requirement}} | {{notes}} |
| FR-002 | {{requirement}} | {{notes}} |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | {{measurable success}} | {{test or metric}} |
| SC-002 | {{measurable success}} | {{test or metric}} |

## Open Questions

- **[NEEDS CLARIFICATION: how should this interact with the auth flow?]** — what
  specifically is unclear, and who should resolve it.

---

## Worked Example: P1 User Story (illustrative)

### US-EX1 — Setup completes in under 5 minutes (Priority: P1)

**As a** new contributor, **I want to** clone the repo and run `bin/cast-doctor`,
**so that** I can confirm my environment is ready in under 5 minutes.

**Independent test:** Fresh clone + `bin/cast-doctor` on Ubuntu 24.04 returns 0
within 300s.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `bin/cast-doctor` runs on a fresh clone, THE SYSTEM SHALL
  print a green PASS line within 300s.
- **Scenario 2:** WHEN `bin/cast-doctor` finds a missing dep, THE SYSTEM SHALL
  print the install command and exit non-zero.

### Worked Example: Spec with Open Item (illustrative)

### US-EX2 — Migration retains user data (Priority: P1)

**As a** v0.x user, **I want to** upgrade to v1.0 without losing data, **so that**
I can adopt the new release safely.

**Independent test:** [NEEDS CLARIFICATION: canonical v0.x fixture]

**Acceptance scenarios:**

- **Scenario 1:** WHEN `bin/cast-upgrade` runs against a v0.x install, THE
  SYSTEM SHALL preserve all `~/.cast/state/*` records.

### Open Questions (worked example)

- **[NEEDS CLARIFICATION: canonical v0.x fixture]** — what version range counts
  as "v0.x"? The release lead should specify before v1.0 ships.
