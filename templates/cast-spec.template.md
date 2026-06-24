# {{Spec Title}}

> **Spec maturity:** draft | accepted | retired
> **Version:** 0.1.0
> **Linked files:** {{path1}}, {{path2}}

This template is the canonical spec-kit shape — User Story / Priority /
Independent Test / Acceptance Scenarios / `FR-NNN` / `SC-NNN` — enforced by
`cast-spec-checker`. Two callers use it differently:

- **`cast-update-spec`** writes a real **product spec** (the durable requirement of
  a product, living in `docs/spec/`) — here the whole document IS this shape.
- **`cast-refine-requirements`** writes a **brief** (the requirement of the *work*),
  and renders this shape as a **spec-formatted SECTION inside that brief** — and only
  for a product-building family. The brief *contains* this section; it never *becomes*
  a spec. Non-product families (research / catch-up / prioritize / loose-idea / go-do)
  carry no US/FR/SC at all (see the per-family note below).

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

<!-- OPTIONAL section. Present for families whose recipe includes the `evidence` block —
     `bug_fix`, `data_analysis`, `testing_qa` (see the per-family shapes note below). Holds
     repro steps, logs, data sources, and links that ground the Intent. Realizes to
     `## Evidence` (parser `BlockKind.EVIDENCE`). Not required by the full-spec
     cast-spec-checker profile; required by the Level-2 `--family` profile for the families
     above. Omit for families whose recipe has no `evidence` block. -->
## Evidence

- {{repro / log / data source / link that grounds the Intent}}

<!-- Per-family shapes: the sections a document carries depend on its classified
     `WorkFamily`. The block-recipe model and per-family required-section profiles are
     specified in `docs/specs/cast-goal-classification.collab.md` (FAMILY_RECIPES /
     RECIPE_REALIZATION / REQUIRED_SECTIONS_BY_FAMILY). `random_idea` is the floor — its
     recipe is `## Intent` only; never pad it with empty spec-kit tables. -->

<!-- No-product brief = specified, not just exempt. For a research / catch-up / "go through
     these resources" / prioritize brief (the *doing* is the requirement), dropping US/FR/SC
     does NOT mean a thin document. Its `## Intent` (plus `## Decisions` / `## Open Questions`
     where the recipe emits them) positively names: the ACTIVITY + its inputs (which resources
     to traverse, what to look for); the DELIVERABLE of the doing (a survey / ranked
     recommendation / decision / notes artifact — not a feature); and what "DONE" means
     (coverage reached, question answered, call made). Same intent / scope / open-question /
     confidence / cold-reader bars — never invent behavior scenarios or quantified constraints
     for a product it does not have. "## Intent: do some research" is a failed no-product brief. -->

<!-- OPTIONAL section. Emit whenever the source writeup carried HOW (proposed approaches,
     reference repos, design instincts). Holds the founder's HOW + one-or-two approach options
     worth exploring — captured and DEVELOPED, never locked (locking the implementation is the
     plan's job). `cast-spec-checker` treats a `## Directional…` H2 as first-class for most
     families (WARNs only for data_analysis / personal_non_eng). Omit only when there is no HOW. -->
## Directional Ideas

- **{{approach the user brought}}** — {{how it serves the WHAT}}.
- **Option A vs Option B** — {{one or two approaches you'd explore, with the trade-off}}.

<!-- OPTIONAL section. Present only when human decisions were recorded during refinement
     (and immediately before Out of Scope / Open Questions when those sections exist). Not
     required by cast-spec-checker; omit when no human decisions were made. -->
## Decisions

| Date | Chose | Over | Because |
|------|-------|------|---------|
| {{YYYY-MM-DD}} | {{option picked}} | {{option(s) rejected}} | {{rationale at decision-time}} |

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
