---
status: refined
confidence:
  intent: high
  behavior: medium
  constraints: medium
  out_of_scope: medium
open_unknowns: 6
questions_asked: 6
---

# Refine Requirements v2 — Workflow-Aware, HTML-First Requirements Refinement

> **Spec maturity:** draft
> **Version:** 0.3.0
> **Linked files:** requirements.human.md, exploration/research_notes.human.md, agents/cast-refine-requirements/cast-refine-requirements.md

## Intent

**Job statement:** When a user finishes dumping raw requirements for a goal, they want the
refinement step to produce an artifact they can grasp in minutes — leading with the WHAT,
shaped to the type of work being done, and visually organized — so they can validate and
iterate on requirements quickly instead of wading through long markdown files.

Three threads are bundled in this goal, and all are in scope:

1. **Faster comprehension** — workflow-aware HTML output with progressive disclosure,
   L1/L2/L3 visual hierarchy, and an up-front classification of what kind of work this is
   ("You are building a new feature for XYZ").
2. **Faster iteration** — inline comments/annotations on the refined document, with
   unresolved comments driving v2/v3 versions until the spec converges, and a change
   summary so each new version can be reviewed as a delta rather than re-read whole.
3. **Workflow routing** — the same classification that shapes the document also routes the
   goal into the right *downstream* workflow (a bug → logs/RCA/confirm/fix-test; a
   prototype → a spike path). This is a first-class, **phase-agnostic** capability: the
   router is designed to be invokable from any phase, not only after requirements.

**The refined file is always a requirements document — never the work product.** A bug-fix
goal's refined output is not the fix; it is the requirements that frame the fix. Workflow
classification therefore has two *separate* effects: (a) it changes how the requirements
*document* is organized per family, and (b) it determines which downstream workflow the
goal routes into next. Do not conflate the artifact with the work that follows it.

**This is product, not personal tooling.** Diecast is an open-source project; broader
adoption is the success measure. Workflow classification and templates must generalize to
arbitrary users' work styles — not be tuned to the maintainer's three workspaces.

**Build for the future.** The design should assume an AI-native world: agents are
first-class producers *and* consumers of requirements. The iteration loop (comments,
versions, resolution) and the workflow router should both be designed so that future agent
participants can use them through the same mechanism as humans — not bolted on later.

## User Stories

### US1 — WHAT/HOW separation (Priority: P1)

**As a** goal owner reviewing refined requirements, **I want to** see the WHAT (outcome,
job, scope) cleanly separated from any HOW (directional implementation ideas), **so that**
I can validate intent quickly without implementation noise, while still capturing useful
direction where it exists.

**Independent test:** Refine a raw writeup that mixes outcome statements with
implementation suggestions; the output's primary view contains only WHAT content, and every
HOW item appears in a clearly-marked, secondary "Directional" section.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the agent refines a raw writeup, THE SYSTEM SHALL lead the output
  with WHAT content (intent, outcomes, scope) before any HOW content.
- **Scenario 2:** WHEN the raw writeup contains implementation suggestions, THE SYSTEM
  SHALL capture them in a visually distinct "Directional ideas" section marked as
  non-binding and subject to change by exploration.
- **Scenario 3:** WHEN a goal's workflow type makes HOW content irrelevant (e.g., pure data
  analysis question), THE SYSTEM SHALL omit the Directional section rather than pad it.

### US2 — Workflow-type classification with family-shaped requirements (Priority: P1)

**As a** goal owner, **I want** the agent to detect what *kind* of work my goal is and shape
the refined requirements document to that family, **so that** a bug-fix goal's requirements
are organized around symptom/repro/expected-vs-actual and a big initiative's around PRD
architecture — instead of every goal getting one shape.

**Clarification (do not conflate the artifact with the work):** the refined requirements
file is *always a requirements document*, never the work product. Classification has two
separate effects: (a) it organizes *this document* per family — the focus of US2 — and
(b) it routes the goal into a family-specific downstream workflow — the focus of US6. US2
is only about how the requirements document is shaped.

**Independent test:** Feed the agent one raw writeup per priority workflow family; each
refined output is organized using that family's document template and displays the detected
classification prominently at the top.

**Priority workflow families (first-class document templates, in order):**

1. **New initiative / PRD** — big goals needing clean architecture; richest template.
2. **Small pilot feature / POC** — one-screen WHAT, minimal ceremony.
3. **Bug fix / debug** — leads with symptom, repro, expected-vs-actual.
4. **Data analysis / research** — leads with the question, data sources, expected output shape.
5. **Random product ideas + explorations** — fuzzy ideation, pre-goal; the loosest
   template. Structured scenarios are NOT forced onto raw ideas (the "Template Enforcer"
   anti-pattern).

Long tail (later): add tests, heavy UI flow (with mocks organized along user flows),
PRD-only creation.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the agent reads a raw writeup, THE SYSTEM SHALL classify the goal
  into a workflow family and display the classification at the top of the output (e.g., as
  a pill: "You are building a new feature for XYZ").
- **Scenario 2:** WHEN the classification is ambiguous between families, THE SYSTEM SHALL
  ask the user to confirm the workflow type as one of its clarifying questions rather than
  guess silently.
- **Scenario 3:** WHEN a goal is classified into a family, THE SYSTEM SHALL organize the
  refined *document* using that family's template (sections, ordering, visual treatment) —
  independent of the downstream routing in US6.
- **Scenario 4:** WHEN a goal matches no first-class family, THE SYSTEM SHALL fall back to
  the generic spec shape and note the unmatched classification.

### US3 — HTML-first human render (Priority: P1)

**As a** goal owner, **I want to** consume refined requirements as a well-designed HTML
document with progressive disclosure and clear visual hierarchy, **so that** I can grasp
the WHAT within ~2 minutes instead of reading a long markdown file.

**Independent test:** Open the HTML render of a refined goal; a reader unfamiliar with the
goal can state its WHAT (job, outcome, scope) within 2 minutes without opening the raw
writeup or the markdown render.

**Acceptance scenarios:**

- **Scenario 1:** WHEN refinement completes, THE SYSTEM SHALL produce an HTML render of
  the refined requirements as the primary human-consumption artifact.
- **Scenario 2:** WHEN the HTML renders, THE SYSTEM SHALL apply level-based visual
  treatments (L1/L2/L3 hierarchy with distinct color/size/design elements) and progressive
  disclosure (summary first, details expandable).
- **Scenario 3:** WHEN the workflow family calls for it, THE SYSTEM SHALL vary the HTML
  structure per family (e.g., user-flow organization for heavy UI goals).
- **Scenario 4:** WHEN refinement completes, THE SYSTEM SHALL continue to produce the
  machine-readable spec-kit markdown render so downstream agents (planner, task-suggester,
  spec-checker) keep working unchanged.

### US4 — Inline comments and iteration loop (Priority: P2)

**As a** goal owner reviewing a refined spec, **I want to** leave inline comments anchored
to specific requirement elements (Google-Docs-style) and, on each new version, see a clear
summary of what changed, **so that** my feedback drives the next version of the spec and I
can review the delta instead of re-reading the whole document.

**Independent test:** Leave a comment on a specific FR in the rendered document; the
comment persists, is visibly anchored to that FR, and carries an open/resolved state.
Produce the next version; a change summary lists exactly which elements changed and why.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a reviewer selects a requirement element in the HTML render, THE
  SYSTEM SHALL allow attaching a comment anchored to that element.
- **Scenario 2:** WHEN open comments exist on a spec, THE SYSTEM SHALL treat the spec as
  unconverged and support producing a new version (v2, v3, ...) that addresses them.
- **Scenario 3:** WHEN a comment is addressed in a new version, THE SYSTEM SHALL allow
  marking it resolved and retain the resolution trail.
- **Scenario 4:** WHEN a new version is produced, THE SYSTEM SHALL emit a change summary
  describing what changed from the prior version (anchored to the affected elements), so
  the reviewer can review the delta rather than re-read the whole document.

[NEEDS CLARIFICATION: annotation implementation approach — standard JS annotation
libraries vs. element-anchored comments on stable IDs vs. framework migration
(react/nextjs); exploration to research and recommend]

### US5 — Versioning and archival of old versions (Priority: P2)

**As a** goal owner iterating on a spec, **I want to** keep only the current version in
the main goal folder with older versions archived out of the way, **so that** the goal
directory stays clean while history remains recoverable.

**Independent test:** Produce v3 of a spec; the main folder contains only the current
version, and v1/v2 are retrievable from the archive (folder or DB).

**Acceptance scenarios:**

- **Scenario 1:** WHEN a new spec version is produced, THE SYSTEM SHALL retain exactly one
  current version in the main goal folder.
- **Scenario 2:** WHEN a version is superseded, THE SYSTEM SHALL move it to the archive
  mechanism (archive folder or DB) without data loss.
- **Scenario 3:** WHEN a user requests an older version, THE SYSTEM SHALL retrieve it with
  its comments and resolution state intact.

[NEEDS CLARIFICATION: archive mechanism — archive folder vs. DB storage for old versions;
owner leans DB; depends on the canonical-source architecture decision]

### US6 — Phase-agnostic workflow routing (Priority: P1)

**As a** goal owner (or a future agent acting on the goal), **I want** the classification to
hand the goal into the right family-specific downstream workflow — and to be able to invoke
that router from any phase, not only after requirements — **so that** the work that follows
requirements (a bug's logs→RCA→confirm→fix/test; a prototype's spike path) matches the kind
of goal instead of defaulting to one pipeline.

**Build boundary (v2):** v2 builds the classifier, the router mechanism, and a clean
seam/interface plus **stubs** for each family pipeline. The downstream pipelines themselves
are designed-for and built incrementally per family in later goals (see Out of Scope). The
router is built phase-agnostic even though only the requirements phase invokes it today.

**Independent test:** Classify a bug-fix goal; the router resolves to the bug-fix pipeline
handle (a stub is acceptable) and records the routing decision on the goal. Invoking the
same router later from a non-requirements phase resolves the same handle without re-running
refinement.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a goal is classified, THE SYSTEM SHALL resolve a family-specific
  downstream-workflow handle and record the routing decision on the goal.
- **Scenario 2:** IF a family pipeline is not yet implemented, THEN THE SYSTEM SHALL route
  to a stub that names the intended workflow steps rather than failing or silently
  falling back to a generic pipeline.
- **Scenario 3:** WHERE the router is invoked from a phase other than requirements, THE
  SYSTEM SHALL resolve routing from the goal's current classification without requiring
  re-refinement.
- **Scenario 4:** WHEN classification changes on a re-run, THE SYSTEM SHALL update the
  routing decision and surface that the downstream workflow has changed.

### US7 — Requirements files as living source of truth (Priority: P1)

**As a** goal owner, **I want** the requirements files to remain the canonical source of
truth, so that when downstream phases (exploration, planning, execution) surface changes
that affect requirements, those changes are written back into the requirements files and
I'm notified, **so that** the requirements never silently drift out of date relative to the
work.

**Note on canonical store:** "source of truth" is about the *requirements artifact*, not a
specific storage choice. Whether requirements stay file-canonical or move to a DB with
generated file renders (see Open Questions), the human-facing requirements files MUST always
reflect current truth — downstream changes round-trip back into them either way.

**Independent test:** Simulate a downstream change that affects a requirement (e.g., a
planning agent discovers a new constraint); the requirements file is updated (e.g., a new
requirement appended at the end) and the user receives a notification describing what
changed and which phase it originated from.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a downstream phase produces a change that affects requirements, THE
  SYSTEM SHALL write the change back into the requirements files (e.g., appended additions
  or annotated edits) rather than leaving it only in downstream artifacts.
- **Scenario 2:** WHEN the requirements files are updated from a downstream source, THE
  SYSTEM SHALL notify the user that requirements changed, including what changed and which
  phase/source originated it.
- **Scenario 3:** WHEN a downstream change is written back, THE SYSTEM SHALL preserve
  provenance (which phase/agent originated it) and present it in the version change summary
  (US4 Scenario 4), so the write-back is reviewable as a delta.
- **Scenario 4:** IF a downstream change conflicts with an existing requirement, THEN THE
  SYSTEM SHALL surface the conflict for the user rather than silently overwriting.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | The refined output shall lead with WHAT content (intent, outcomes, scope) at the top of the document; all HOW content shall be confined to a clearly-marked, non-binding "Directional ideas" section rendered last | US1; reworded v2 |
| FR-002 | The agent shall classify each goal into a workflow family and surface the classification at the top of the refined document | US2 |
| FR-003 | The system shall organize the refined *document* using a first-class template per priority workflow family (5 families) | US2; document shape, distinct from routing; long tail later |
| FR-004 | When classification is ambiguous, the agent shall confirm the workflow type with the user instead of guessing | US2 Scenario 2 |
| FR-005 | The system shall produce an HTML render as the primary human-consumption artifact | US3 |
| FR-006 | The HTML render shall use progressive disclosure and L1/L2/L3 level-based visual treatments | US3 |
| FR-007 | The system shall continue producing the spec-kit markdown render consumed by downstream agents (planner, task-suggester, spec-checker) | preserves existing contract |
| FR-008 | Requirement elements (US/FR/SC) shall carry stable identifiers usable as anchors for comments and cross-references | enables US4 regardless of architecture choice |
| FR-009 | Reviewers shall be able to attach comments anchored to requirement elements, with open/resolved state | US4 |
| FR-010 | Open comments shall drive new spec versions; resolution trails shall be retained | US4/US5 |
| FR-011 | Only the current spec version shall live in the main goal folder; older versions shall be archived | US5 |
| FR-012 | Workflow classification, templates, and routing shall generalize to arbitrary users (open-source product), with no hardcoding to the maintainer's workspaces | OSS constraint |
| FR-013 | The iteration loop (comments, versions, resolution) shall be designed so agent participants can use it through the same mechanism as humans | future-facing constraint |
| FR-014 | The system shall provide a router that resolves a classified goal to a family-specific downstream-workflow handle and records the routing decision on the goal | US6 |
| FR-015 | Each family's downstream pipeline shall sit behind a stable seam; v2 shall ship stubs that name the intended steps, with real pipelines added per family later | US6 build boundary |
| FR-016 | The router shall be invokable from any phase (not only post-requirements) and resolve from the goal's current classification without requiring re-refinement | US6; phase-agnostic |
| FR-017 | When a new spec version is produced, the system shall emit a change summary describing what changed from the prior version | US4 Scenario 4 |
| FR-018 | The requirements artifact shall be the canonical source of truth for the goal; downstream changes affecting requirements shall be round-tripped into the requirements files (whatever the underlying store) so the files always reflect current truth | US7 |
| FR-019 | When requirements are updated from a downstream source, the system shall notify the user with what changed and the originating phase/source | US7 Scenario 2 |
| FR-020 | Downstream write-backs shall preserve provenance and appear in the version change summary; conflicting changes shall be surfaced to the user, not silently overwritten | US7 Scenarios 3-4 |
| FR-021 | The system shall expose a deterministic block-level change summary between two versions, listing each added, modified, and removed element | US4 Scenario 4; added v2 |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | A reader can state a goal's WHAT within 2 minutes of opening the HTML render, without reading the raw writeup | timed read test on 3+ real goals across workflow families |
| SC-002 | Requirement iteration happens through in-doc comments → new versions with change summaries, not through manual md edits or chat re-explanations | observe N consecutive real goals refined via the comment loop |
| SC-003 | The HTML render fully replaces markdown for human consumption; md is read only by agents | owner self-report after 2+ weeks of real use |
| SC-004 | Downstream agents (planner, task-suggester, spec-checker) work unchanged against v2 output | existing agent chain runs green on a v2-refined goal |
| SC-005 | A classified goal resolves to the correct family pipeline handle (or named stub), the routing decision is recorded, and re-invoking the router from another phase yields the same handle | trace routing on 5 goals, one per family, plus one cross-phase re-invocation |
| SC-006 | A downstream-originated requirement change appears in the requirements files and triggers a user notification; no requirement change lives only in a downstream artifact | trace one downstream change end-to-end into the files + notification |

(Open-source adoption is the long-horizon success signal, noted as direction rather than a
verifiable criterion for this goal.)

## Directional Ideas (non-binding HOW, captured from the raw writeup and refinement)

- **Candidate architecture (owner deferred decision to exploration):** requirements as
  structured DB entities — matching Diecast's existing goal/tasks pattern of
  "DB-canonical, auto-generated file renders" — with HTML (human) and markdown (agents)
  both generated. Makes annotations rows-on-stable-IDs instead of fragile text anchoring,
  and makes versioning/archival natural. Alternative: files stay canonical with a DB layer
  only for comments/versions.
- **Router as a separate capability:** because routing must be callable from any phase, the
  classify+route logic likely wants to live behind its own seam (a standalone
  agent/service) that refine-requirements invokes — rather than being buried inside the
  refinement agent. Pipeline stubs could simply name their steps (bug:
  logs→RCA→confirm→fix/test; prototype: spike→demo→learnings) until the real pipeline lands.
- cast-preso* skills carry reusable presentation ideas (visual hierarchy, progressive
  disclosure, slide-archetype thinking) — inspiration for the HTML templates.
- Workflow classification could surface as standard pills at the top of the document.
- Per-family inspiration templates may be worth researching online before designing.
- Change summaries could be generated by diffing stable-ID elements between versions
  (another reason to favor stable identifiers / structured storage).

## Constraints

- **Downstream contract preserved:** planner, task-suggester, and cast-spec-checker
  consume `refined_requirements.collab.md` in spec-kit shape today; v2 must keep that
  render working (FR-007) regardless of what becomes canonical.
- **Open-source product:** all classification, templates, routing, and UI must generalize
  beyond the maintainer's own workflows (FR-012).
- **Phase-agnostic router seam:** classification/routing is a capability behind a clean
  seam, designed to be invokable from any phase; v2 builds the seam even though only the
  requirements phase calls it today (FR-016).
- **Pipelines stubbed:** v2 ships family-pipeline *stubs* (named steps) behind the seam,
  not the pipelines themselves; real pipelines are later per-family goals (FR-015).
- **Current stack:** cast-server is FastAPI + Jinja server-rendered. A framework migration
  (react/nextjs) is not a goal in itself — it is only acceptable if exploration shows the
  annotation UX genuinely requires it.
- **Requirements are the source of truth:** downstream phases must round-trip requirement
  changes back into the requirements files with user notification; requirements must not
  drift out of date relative to the work (FR-018).
- **Future-facing:** design for agents as first-class participants in both the
  requirements loop and the workflow router (FR-013).

## Out of Scope

- **Building the family-specific downstream pipelines themselves** (the RCA/fix flow, the
  prototype spike flow, etc.) — v2 ships only the router seam + named stubs; each real
  pipeline is a later, per-family goal.
- **Wiring the router into phases other than requirements** — the seam is built
  phase-agnostic, but only the requirements phase invokes it in v2.
- Multi-user / realtime collaborative editing (Google-Docs-style *simultaneous* editing).
  Comments and versions are asynchronous, single-writer.
- Rewriting downstream agents (planner, task-suggester, spec-checker) — they continue
  consuming the markdown render.
- Long-tail workflow templates (add tests, heavy UI flow, PRD-only) — designed-for but not
  built in v2's first pass.

## Open Questions

- **[NEEDS CLARIFICATION: canonical source of truth — DB-entities-with-generated-renders
  vs. files-canonical-with-DB-comment-layer]** — owner explicitly deferred this to
  exploration ("let exploration decide"). Primary exploration target; both options and
  trade-offs are captured in Directional Ideas. Resolver: cast-explore + owner decision at
  plan review.
- **[NEEDS CLARIFICATION: router placement — does the classify+route capability live inside
  cast-refine-requirements, or is it extracted as a standalone phase-agnostic agent/service
  that refine-requirements (and later, other phases) call?]** — phase-agnostic invocation
  (FR-016) implies extraction eventually; decide the seam boundary at exploration/plan
  review. Resolver: cast-explore + owner.
- **[NEEDS CLARIFICATION: annotation implementation approach — standard JS annotation
  libraries vs. element-anchored comments on stable IDs vs. framework migration
  (react/nextjs); exploration to research and recommend]** — owner asked whether standard
  libraries exist and whether react/nextjs is required. Resolver: cast-explore.
- **[NEEDS CLARIFICATION: archive mechanism — archive folder vs. DB storage for old
  versions; owner leans DB; depends on the canonical-source architecture decision]** —
  resolve together with the architecture question. Resolver: cast-explore.
- **[NEEDS CLARIFICATION: gbrain improvements]** — owner asked "any improvements to
  refine-requirements from gbrain?"; nothing reviewed yet. Resolver: exploration to survey
  gbrain's requirements handling for portable ideas.
- **[NEEDS CLARIFICATION: classification taxonomy validation]** — the five priority
  families come from the owner's experience; as an OSS product, the taxonomy should be
  validated against external users' workflow types during exploration. Resolver:
  cast-explore (online research + inspiration templates).
