---
status: refined
scope_mode: hold
confidence:
  intent: high
  behavior: medium
  constraints: medium
  out_of_scope: high
open_unknowns: 1
questions_asked: 6
classification:
  family: "new_initiative"
  confidence: 0.9
  alt_family: "refactor_migration"
  reasoning: "Scoped feature build: a new LLM maker agent for requirements rendering plus revisiting the v2 verification layer."
  uncertainty_factors: []
  modifiers:
    irreversible: false
    unknown_cause: false
  confirmed_by: "manual"
  classified_at: "2026-06-12"
  taxonomy_version: 1
---

<!-- CORPUS-PROVENANCE: family=new_initiative — authored from this goal's own real classified refined_requirements.collab.md (refine-requirements-better-rendering-v3). -->

# Refine Requirements — Better Rendering (v3)

> **Spec maturity:** draft
> **Version:** 0.1.0
> **Linked files:** goals/refine-requirements-better-rendering-v3/requirements.human.md

## Intent

**Job statement:** Replace the plain deterministic requirements render with a cast-preso-style maker agent that generates a beautiful, easy-to-consume HTML per classification, so any reader grasps the job, outcome, and scope in seconds.

Refine-requirements v2 produces `refined_requirements.html` from a deterministic Python and Jinja renderer that borrows cast-preso styling but never lets an LLM craft the page. The result is functional but plain, and dogfooding surfaced two concrete defects (raw markdown leaking onto the Goal Card, and a sentence-splitter that truncates on abbreviations). The owner wants the render to reach cast-preso quality: a bespoke, per-classification layout an LLM maker generates, the way cast-preso-how generates slides.

The chosen direction is the maker agent. The known cost of that choice — giving up render determinism and reproducibility, and the risk to the comment-and-version anchoring that Phase 4 depends on — is accepted and is captured below as constraints and open questions, not waved away.

This is expected to mean revisiting parts of v2, especially the verification layer. The deterministic golden-HTML snapshot gate and the SC-001 checker were built for a render that never changes; a maker render that varies needs different checks. The same applies to the machinery that assumed a stable render — version diffing and comment resolution were deterministic in v2 (set-arithmetic over stable ids; quote-based re-anchoring), and a varying maker render breaks that assumption, so these likely need an LLM that reasons about meaning rather than a fixed algorithm. New LLM agents are explicitly in scope — a maker, one or more LLM checkers, a diff-and-comment-resolution agent, and any helper agents the loop needs — rather than only reusing what exists.

A guiding principle, borrowed from cast-preso: separate what to communicate from how to communicate. A WHAT layer decides, per block and per family, the information and the outcome a reader must take away; a HOW layer (the maker) chooses the representation that lands it, picking from a named library of representation archetypes rather than improvising. cast-preso already ships reusable archetypes (compare-contrast with a code-diff variant, single-stat-hero, timeline, diagram-annotated, and more) and design utilities for diff representation that the version-diff surface should reuse rather than reinvent.

The North Star is the user-facing HTML. Deciding what to build is the most valuable step, so the whole pipeline optimizes for exactly one thing: a reader understanding the requirement quickly and completely. Backend cost, the number of generation-and-check loops, model tier, and latency are explicitly NOT constraints to minimize — spend whatever it takes to make the page land. And when the presenter finds it is missing a detail that would genuinely help the reader but is absent from the requirements file, it asks the upstream WHAT or refine agent for that detail rather than shipping an incomplete page; it never fabricates requirement content.

## User Stories

### US1 — A reader instantly understands any render (Priority: P1)

**As a** reader unfamiliar with a goal, **I want to** open its requirements render and grasp the job, the primary outcome, and what is in and out of scope within seconds, **so that** I can act without reading the whole document or asking the author.

**Independent test:** Open the render for a goal in any family and, from the above-the-fold view alone, restate the job, the outcome, and the scope correctly.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a reader opens a goal's render, THE SYSTEM SHALL present an above-the-fold summary (classification, one-line job statement, and the key outcome and scope assertions) that is readable without scrolling or clicking.
- **Scenario 2:** WHEN the source document is a stub, IF there is not enough content to summarize, THE SYSTEM SHALL render a clear prompt-to-begin state rather than an empty or broken page.

### US2 — The layout is bespoke per classification (Priority: P1)

**As a** reader, **I want to** see a layout shaped to the kind of work, **so that** a bug fix reads like a bug fix and a new initiative reads like an initiative.

**Independent test:** Render one goal per family and confirm each family's layout is visibly distinct and appropriate to that family's recipe.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the maker renders a document, THE SYSTEM SHALL select a layout and emphasis driven by the document's classified family and its recipe blocks.
- **Scenario 2:** WHEN a family carries no content for a block, THE SYSTEM SHALL omit that block rather than pad it with an empty section.

### US3 — Comments and versions survive the new render (Priority: P1)

**As a** reviewer who has left comments, **I want to** keep my comments anchored after the render changes, **so that** switching to the maker does not orphan my feedback.

**Independent test:** With open comments present, regenerate the render through the maker and confirm every comment stays anchored to its quoted text with zero new orphans.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the maker emits a document, THE SYSTEM SHALL produce stable anchors for each user story, functional requirement, and success criterion so the comment and version layer can attach to them.
- **Scenario 2:** WHEN a regenerated render moves or rewrites anchored text, THE SYSTEM SHALL re-anchor or resolve the affected comments by reasoning about meaning (an LLM resolution agent), rather than relying on the v2 deterministic quote-match alone, and SHALL never silently drop a comment.

### US4 — Generated quality is gated, not assumed (Priority: P2)

**As a** maintainer, **I want to** gate the generated HTML behind a checker with a bounded rework loop, **so that** a bad generation never reaches a reader.

**Independent test:** Force a low-quality generation and confirm the checker fails it and triggers a rework before the page is served.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the maker produces a render, THE SYSTEM SHALL run a comprehension-and-visual checker over it and serve the result only after it passes or the rework budget is exhausted.
- **Scenario 2:** IF the checker cannot reach the bar after sustained rework, THEN THE SYSTEM SHALL serve the best-scoring attempt and flag it for human review, rather than fall back to the plain deterministic page.

### US5 — Renders are cached, not regenerated on every view (Priority: P2)

**As a** cost-conscious owner, **I want to** generate the expensive render at most once per source version, **so that** viewing a page does not repeatedly call a model.

**Independent test:** View an unchanged render twice and confirm the second view serves cached HTML with no new model call.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a render is requested and the source content is unchanged since the last generation, THE SYSTEM SHALL serve the cached HTML without invoking the maker.
- **Scenario 2:** WHEN the source content changes, THE SYSTEM SHALL regenerate on the next view and replace the cached render.

### US6 — Commenting is discoverable (Priority: P2)

**As a** reviewer opening a render for the first time, **I want to** see an obvious way to start a comment, **so that** I can leave feedback without knowing a hidden select-text gesture.

**Independent test:** A first-time reader, given no instructions, leaves a comment on the render.

**Note:** this fix is independent of the maker and applies to today's deterministic render too, so it can ship ahead of the rest of v3.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a reader views a render, THE SYSTEM SHALL show a visible commenting affordance (a hint or control) in addition to the select-to-comment gesture.
- **Scenario 2:** WHEN a reader selects text, THE SYSTEM SHALL continue to offer the inline comment pill it offers today.

### US7 — The presenter fills comprehension gaps by asking upstream (Priority: P1)

**As a** reader, **I want to** get the detail I need to understand a requirement even when the source file left it out, **so that** I am never stuck on a page that explains something incompletely.

**Independent test:** Given a requirements file missing a detail that materially aids comprehension, the rendered page either supplies it (sourced by asking the upstream agent) or clearly marks the gap — it never silently ships an incomplete explanation.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the presenter detects a comprehension gap the requirements file does not cover, THE SYSTEM SHALL request the missing detail from the upstream WHAT or refine agent before finalizing the render.
- **Scenario 2:** WHEN the upstream agent cannot supply the detail, THE SYSTEM SHALL surface the gap explicitly on the page rather than fabricate an answer.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | A HOW maker agent (a cast-requirements-how cousin of cast-preso-how) consumes the per-section communication intent produced by the WHAT agent plus the confirmed classification and produces the self-contained HTML render. | The HOW layer; replaces the single deterministic renderer on the happy path. |
| FR-002 | The maker selects layout and emphasis from the document's family and recipe blocks, producing a visibly distinct render per family. | Per-classification bespoke output. |
| FR-003 | Canonical anchor ids (US-NN, FR-NNN, SC-NNN) are assigned upstream by the deterministic engine, and the maker must emit them verbatim on the corresponding blocks; it never invents or renames an id. An LLM re-anchors a comment only when its target text genuinely moved or was reworded. | Deterministic id backbone; the maker decorates, it does not own identity. |
| FR-004 | A single new requirements-render checker agent grades the generated HTML for comprehension and visual quality and drives a rework loop that continues until the comprehension bar is met — quality-driven, not a cost-capped number of rounds (only a high safety ceiling guards against an infinite loop). | The page quality is the objective, so loops are not rationed. |
| FR-005 | The generated render is cached against the source content hash and regenerated when the source changes, reusing the v2 embedded-source-hash lazy-regeneration mechanism unchanged. The cache key additionally folds in the resolved work-family so a re-classification forces a fresh render. | Caching only skips re-rendering identical content; it does not ration generation effort. |
| FR-006 | On a true maker failure (crash, timeout, no output at all) the deterministic renderer is served. On non-convergence (output was produced but the checker never reached the bar) the best-scoring attempt is served and flagged for human review — never the plain deterministic page. | The reader always gets the best available page; the plain fallback is only for a no-output crash. |
| FR-007 | The render is served through the existing self-healing `GET /goals/{slug}/render` loop and remains self-contained. | No change to how humans reach the page. |
| FR-008 | The canonical source stays `refined_requirements.collab.md`; the HTML is a generated, read-only projection. | The maker never writes the canonical markdown. |
| FR-009 | The v2 verification layer is revisited for a non-deterministic render: the deterministic golden-HTML snapshot gate is replaced or supplemented by LLM-judged comprehension and visual checks. | New LLM checker agents are expected, not just reuse of the deterministic gate. |
| FR-010 | The new agents are a WHAT agent, a HOW maker, a single thorough comprehension-plus-visual checker, and a diff-and-comment-resolution agent (plus helpers as needed), following the cast agent-design conventions. | The owner chose a WHAT-plus-HOW-plus-one-checker shape over a fuller multi-checker coordinator. |
| FR-011 | Because anchor ids are stable (the deterministic backbone above), the structural version diff stays deterministic (id-based set-arithmetic, as in v2); an LLM is used only to narrate the diff and to re-anchor or resolve comments whose text genuinely moved or was reworded, never inventing a change absent from the source. | The deterministic-backbone decision keeps diffs deterministic; the LLM handles only moved or reworded text. |
| FR-012 | The pipeline is split into two agents: a WHAT agent decides, per block and family, the information and outcome to communicate; a separate HOW maker chooses the representation and generates the HTML. The HOW layer never invents the WHAT. | Mirrors the cast-preso what-planner-then-how split, the structure that makes its output good. |
| FR-013 | The maker selects representations from a named archetype library rather than improvising, reusing cast-preso archetypes (compare-contrast and its code-diff variant, single-stat-hero, timeline, diagram-annotated, and others) and cast-preso's diff-representation utilities for the version-diff surface. | Variety of representation forms; reuse over rebuild. |
| FR-014 | The render exposes a discoverable way to comment — a visible affordance, not selection-only with no hint — while keeping the existing select-to-comment path. | Dogfooding finding: today the comment pill appears only on text selection, so the feature reads as absent. |
| FR-015 | When the presenter finds a comprehension gap — a detail that would materially help the reader but is absent from the requirements file — it requests that detail from the upstream WHAT or refine agent before finalizing, rather than rendering an incomplete page; it never fabricates requirement content. | HOW asks WHAT; the page is the objective, the source stays the truth. |
| FR-016 | Detail obtained by such a request is reconciled upstream (written back to or flagged on the canonical requirements) so the page never shows requirement content that exists nowhere else. | No silent invention; the canonical source stays complete. |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | A first-time reader can state the job, the primary outcome, and the scope within sixty seconds of opening any family render. | Cold-reader test (the cast-requirements-checker agent stands in for the human reader). |
| SC-002 | Every work family renders a visibly distinct and appropriate layout, confirmed across all nine families. | One golden render per family, reviewed. |
| SC-003 | Regenerating a render leaves every open comment anchored, with zero orphans introduced by the render change. | Comment-survival check across a regenerate. |
| SC-004 | On a true maker crash or timeout (no output), the deterministic render is served, so a render is never missing. | Fault-injection of the maker (no-output). |
| SC-005 | An unchanged source serves the cached render with no new model call. | Cache-hit observation on a repeat view. |
| SC-006 | A first-time reader discovers how to leave a comment without being told. | Unprompted usability check on the render. |
| SC-007 | When the requirements omit a detail needed to understand a block, the page supplies it (sourced upstream) or marks the gap, never shipping a silently incomplete explanation. | Gap-injection test: remove a key detail and confirm the render asks upstream or flags it. |
| SC-008 | On non-convergence, the reader is served the best-scoring attempt with a human-review flag recorded, never the plain deterministic page. | Force the checker to never pass; confirm best-attempt is served and a flag is raised. |
| SC-009 | A re-classification of a goal's work family invalidates its cached render and forces a regenerate, even when the source bytes are unchanged. | Re-classify a fixture and confirm a fresh maker call. |

## Constraints

- Reuse the cast-preso visual toolkit and style bible rather than building a new visual system.
- Separate what to communicate from how to communicate (the cast-preso what-then-how split): a WHAT layer owns the information and outcome per block; the HOW maker owns the representation and must never invent the WHAT.
- Pick representations from a named archetype library (reuse cast-preso archetypes and its diff-representation utilities) rather than improvising a layout per render.
- Commenting must be discoverable: keep select-to-comment, but add a visible affordance so a reader knows comments exist without being told.
- Keep the server-served, self-healing regenerate-on-view loop and the self-contained single-file output.
- The maker output must carry stable per-block anchors; the comment and version layer is non-negotiable.
- The deterministic renderer stays in the codebase as the fallback substrate.
- Correctness still matters most for comment anchoring and version diffs, but a varying maker render breaks the v2 assumption that these can stay purely deterministic; an LLM-assisted diff and comment-resolution approach is in scope where stable structure no longer holds. The trust boundary must stay tight: the LLM may narrate and re-anchor, but a diff must never invent a change that is not in the source.
- Optimize for one thing above all: the comprehensibility of the user-facing HTML. Backend cost, loop count, model tier, and latency are explicitly NOT constraints to minimize — spend whatever it takes to make the page land. Caching exists only to skip re-rendering unchanged content, never to ration generation effort.
- The presenter may ask the upstream WHAT or refine agent for a missing-but-useful detail rather than ship an incomplete page; it never invents requirement content, and anything it obtains is reconciled back to the canonical source.

## Out of Scope

- Replacing the canonical markdown source or the comment and version backend.
- The deferred human timed-read evaluation from v2.
- A live, always-regenerating render on every page view (caching is required).

## Decisions

| Date | Chose | Over | Because |
|------|-------|------|---------|
| 2026-06-12 | A preso-style maker agent (a cast-requirements-how cousin of cast-preso-how) | A hybrid deterministic-plus-LLM render (recommended); deterministic polish only | Want maximum, preso-grade beauty per classification, and accept giving up render determinism and reproducibility to get it. |
| 2026-06-12 | Optimize for the comprehensibility of the user-facing HTML above all; cost, loops, and latency are not constraints, and the presenter may ask upstream for missing-but-useful detail | Treating cost/loop-count as constraints; rendering only what is literally in the file | Deciding what to build is the highest-value step; the holy grail is the page the reader understands, so everything else is subordinate. |
| 2026-06-12 | LLM anchoring on a deterministic id backbone | LLM end-to-end anchoring (no ids); deterministic post-process id injection | Stable ids make anchoring exact and prevent silent orphans (a comment is never lost); the LLM reasons only when text genuinely moved. |
| 2026-06-12 | Pipeline shape: a WHAT agent plus a HOW maker plus one thorough checker | A full cast-preso-depth pipeline (multi-checker coordinator with content, visual, and tone plus an adversarial pass); a single monolithic maker | Keep the what/how split that makes preso output good, without the overhead of a multi-checker coordinator. |
| 2026-06-12 | On non-convergence, serve the best-scoring attempt and flag it for human review | Falling back to the deterministic render; blocking the page until a human intervenes | The page is the holy grail; a reader should never be down-graded to the plain render when a better attempt exists. Deterministic fallback is kept only for a true no-output crash. |
| 2026-06-12 | A single new requirements-render checker (comprehension plus visual in one pass), rework until the comprehension bar is met, deterministic fallback only on genuine failure | Composing the existing cast-requirements-checker plus cast-preso-check-*; the full preso check-coordinator | Simpler to tune for requirement renders, and loops are driven by page quality rather than a cost cap. |
| 2026-06-12 | Cache by source-content hash, regenerate on change (reuse the v2 lazy-regeneration) | Hash cache plus a manual regenerate control; hash cache plus staleness expiry | Caching only skips re-rendering unchanged content; it does not ration generation effort, which is governed by quality. |

## Open Questions

All design forks raised during refinement were resolved interactively and folded into the
Decisions table and the functional requirements above. One tuning knob is deliberately deferred:

- **[USER-DEFERRED]** Maker and checker model tier (which model each runs on). Reason: deferred as a later tuning knob once the generation-and-check loop works end to end.
