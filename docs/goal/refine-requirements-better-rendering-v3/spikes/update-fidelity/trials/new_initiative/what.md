---
contract: cast-requirements-what/v1
goal_slug: spike-new_initiative
family: new_initiative
source_hash: 24cb292cf9bf0bab8b71ab627a34e70a5b4544c9a8991ddac649b55f451ba658
sections:
  - title: What we're building and why
    outcome: >-
      L1: This replaces the plain deterministic requirements render with a cast-preso-style
      maker agent that generates a bespoke, per-classification HTML page so any reader grasps
      the job, outcome, and scope in seconds. L2: The plain v2 render is functional but flat,
      and dogfooding surfaced real defects; the win is comprehension, with a layout shaped to
      the family so a bug fix reads like a bug fix and an initiative like an initiative.
    block_refs: [US1, US2, FR-002, SC-001, SC-002]
  - title: The pipeline shape we committed to
    outcome: >-
      L1: The committed architecture is a WHAT agent that decides per-block information and
      outcome, plus a HOW maker that picks a representation and emits the HTML — the HOW layer
      never invents the WHAT. L2: The maker draws from a named cast-preso archetype library
      rather than improvising, and the agent set was deliberately kept to WHAT + HOW + one
      thorough checker + a diff/comment-resolution agent, not a fuller multi-checker coordinator.
    block_refs: [FR-001, FR-010, FR-012, FR-013]
  - title: Keeping comments and versions anchored
    outcome: >-
      L1: The comment-and-version layer is non-negotiable, so canonical anchor ids stay a
      deterministic backbone the maker must emit verbatim, and the structural diff stays
      deterministic id-based set-arithmetic. L2: An LLM resolution agent reasons about meaning
      only when anchored text genuinely moved or was reworded, never inventing a diff and never
      silently dropping a comment across a regenerate.
    block_refs: [US3, FR-003, FR-011, SC-003]
  - title: Filling comprehension gaps without fabricating
    outcome: >-
      L1: When the presenter finds a detail that would materially help the reader but is absent
      from the source, it asks the upstream WHAT or refine agent rather than shipping an
      incomplete page — and never fabricates requirement content. L2: If the upstream agent
      can't supply it the gap is surfaced explicitly on the page, and any detail obtained is
      reconciled back to the canonical source so the page never shows content that exists nowhere else.
    block_refs: [US7, FR-015, FR-016, SC-007]
  - title: Gating quality and handling failure
    outcome: >-
      L1: A single comprehension-plus-visual checker grades every generation and drives a
      quality-driven rework loop (bounded only by a high safety ceiling, not a cost cap) so a
      bad page never reaches a reader. L2: A true no-output crash falls back to the deterministic
      render; non-convergence instead serves the best-scoring attempt flagged for human review —
      never the plain page — and the v2 deterministic snapshot gate is revisited for a varying render.
    block_refs: [US4, FR-004, FR-006, FR-009, SC-004, SC-008]
  - title: Caching to skip work, never to ration it
    outcome: >-
      L1: The expensive render is cached against the source-content hash and regenerated on
      change, reusing the v2 lazy-regeneration so an unchanged page never re-calls the model.
      L2: The cache key folds in the resolved work-family, so a re-classification forces a fresh
      render even on identical bytes; caching skips redundant work, it never rations generation effort.
    block_refs: [US5, FR-005, SC-005, SC-009]
  - title: Making commenting discoverable
    outcome: >-
      L1: The render must show a visible commenting affordance so a first-time reader can leave
      feedback without knowing the hidden select-text gesture. L2: This is a dogfooding fix
      independent of the maker — it keeps the existing select-to-comment pill and can ship ahead
      of the rest of v3.
    block_refs: [US6, FR-014, SC-006]
  - title: What stays the same and what's out of scope
    outcome: >-
      L1: The render is still served through the existing self-healing GET /goals/{slug}/render
      loop as a self-contained file, and the canonical source stays refined_requirements.collab.md
      with the HTML a read-only projection. L2: Explicitly out of scope are replacing the markdown
      source or comment backend, the deferred v2 timed-read evaluation, and any always-regenerating
      render on every view.
    block_refs: [FR-007, FR-008]
unmapped_refs: []
gaps: []
---

## What we're building and why

**L1 takeaway:** This initiative replaces the plain deterministic requirements render with a cast-preso-style maker agent that produces a beautiful, bespoke HTML page per classification, so any reader grasps the job, the primary outcome, and the scope within seconds.

**L2 supporting points:** The v2 render is a deterministic Python/Jinja page that borrows cast-preso styling but never lets an LLM craft the page — functional but plain, and dogfooding surfaced concrete defects (raw markdown leaking onto the Goal Card, an abbreviation-truncating sentence splitter). The reader payoff is two-fold: instant comprehension from an above-the-fold summary (US1, SC-001), and a layout visibly shaped to the classified family and its recipe so each kind of work reads like itself (US2, FR-002, SC-002), with empty blocks omitted rather than padded.

**Source carrying it:** Intent (job statement and the North Star of reader comprehension), US1, US2, FR-002, SC-001, SC-002.

## The pipeline shape we committed to

**L1 takeaway:** The committed architecture borrows cast-preso's guiding principle — separate *what* to communicate from *how* — into a WHAT agent that decides per-block information and outcome and a separate HOW maker that chooses the representation and emits the HTML; the HOW layer never invents the WHAT.

**L2 supporting points:** The maker selects from a *named* archetype library (compare-contrast and its code-diff variant, single-stat-hero, timeline, diagram-annotated, and cast-preso's diff-representation utilities) rather than improvising per render — reuse over rebuild (FR-013). The owner deliberately chose a lean agent set — a WHAT agent, a HOW maker, one thorough comprehension-plus-visual checker, and a diff-and-comment-resolution agent (plus helpers) — over a full cast-preso-depth multi-checker coordinator (FR-001, FR-010, FR-012).

**Source carrying it:** Intent (the what/how split and archetype library), Decisions table (pipeline-shape and what/how-split rows), FR-001, FR-010, FR-012, FR-013.

## Keeping comments and versions anchored

**L1 takeaway:** The comment-and-version layer is non-negotiable, so identity stays a deterministic backbone: canonical anchor ids (US-NN, FR-NNN, SC-NNN) are assigned upstream and the maker must emit them verbatim, never inventing or renaming an id, and the structural version diff stays deterministic id-based set-arithmetic as in v2.

**L2 supporting points:** A varying maker render breaks v2's assumption that comment-anchoring and diffs can be purely deterministic, so an LLM resolution agent re-anchors or resolves a comment *only* when its target text genuinely moved or was reworded — reasoning about meaning, never relying on quote-match alone, and never silently dropping a comment (US3, FR-003, FR-011). The trust boundary stays tight: the LLM may narrate and re-anchor, but a diff must never invent a change absent from the source. Verification: regenerate with open comments present and confirm zero new orphans (SC-003).

**Source carrying it:** US3, FR-003, FR-011, SC-003, plus the deterministic-id-backbone decision and the anchoring/trust-boundary constraints.

## Filling comprehension gaps without fabricating

**L1 takeaway:** When the presenter detects a comprehension gap — a detail that would materially help the reader but is absent from the requirements file — it requests that detail from the upstream WHAT or refine agent before finalizing, rather than shipping an incomplete page, and it never fabricates requirement content.

**L2 supporting points:** If the upstream agent cannot supply the detail, the gap is surfaced explicitly on the page rather than answered (US7 Scenario 2, FR-015). Anything obtained this way is reconciled back to or flagged on the canonical requirements, so the page never displays requirement content that exists nowhere else (FR-016). Verification is a gap-injection test: remove a key detail and confirm the render asks upstream or marks the gap, never a silently incomplete explanation (SC-007).

**Source carrying it:** US7, FR-015, FR-016, SC-007, and the Intent/Decisions statements that the page is the objective but the source stays the truth.

## Gating quality and handling failure

**L1 takeaway:** A single comprehension-plus-visual checker grades every generation and drives a quality-driven rework loop — continuing until the comprehension bar is met, bounded only by a high safety ceiling rather than a cost-capped number of rounds — so a bad generation never reaches a reader.

**L2 supporting points:** Failure modes are split deliberately. A *true* maker failure (crash, timeout, no output at all) falls back to the deterministic renderer so a render is never missing (FR-006, SC-004). *Non-convergence* (output produced but the checker never reached the bar) instead serves the best-scoring attempt with a recorded human-review flag — never the plain deterministic page, because the reader should never be downgraded when a better attempt exists (FR-006, SC-008). This is why the v2 deterministic golden-HTML snapshot gate is revisited and supplemented by LLM-judged checks for a render that now varies (FR-009).

**Source carrying it:** US4, FR-004, FR-006, FR-009, SC-004, SC-008, plus the non-convergence and single-checker decision rows.

## Caching to skip work, never to ration it

**L1 takeaway:** The expensive render is generated at most once per source version: it is cached against the source-content hash and regenerated when the source changes, reusing the v2 embedded-source-hash lazy-regeneration mechanism unchanged, so viewing an unchanged page makes no new model call.

**L2 supporting points:** The cache key additionally folds in the resolved work-family, so a re-classification forces a fresh render even when the source bytes are identical (FR-005, SC-009). The framing matters: caching exists only to skip re-rendering identical content — it does *not* ration generation effort, which is governed entirely by page quality (US5, SC-005).

**Source carrying it:** US5, FR-005, SC-005, SC-009, the caching decision row, and the Intent/constraint that cost and loops are explicitly not minimized.

## Making commenting discoverable

**L1 takeaway:** The render must expose a discoverable way to comment — a visible affordance or hint, not selection-only — so a first-time reader leaves feedback without knowing the hidden select-text gesture.

**L2 supporting points:** This is a dogfooding finding (today the comment pill appears only on text selection, so the feature reads as absent) and the fix keeps the existing select-to-comment path intact (US6, FR-014). It is independent of the maker and applies to today's deterministic render too, so it can ship ahead of the rest of v3. Verification is an unprompted usability check (SC-006).

**Source carrying it:** US6 (including its "ship ahead" note), FR-014, SC-006.

## What stays the same and what's out of scope

**L1 takeaway:** The boundaries are explicit: the render is still served through the existing self-healing `GET /goals/{slug}/render` loop as a self-contained single file (FR-007), and the canonical source stays `refined_requirements.collab.md` with the HTML a generated, read-only projection the maker never writes (FR-008).

**L2 supporting points:** Deliberately out of scope — replacing the canonical markdown source or the comment-and-version backend, the deferred v2 human timed-read evaluation, and a live always-regenerating render on every view (caching is required). One tuning knob is openly deferred, not missing: which model tier the maker and checker run on, parked until the generate-and-check loop works end to end.

**Source carrying it:** FR-007, FR-008, the Out of Scope section, and the single USER-DEFERRED open question.
