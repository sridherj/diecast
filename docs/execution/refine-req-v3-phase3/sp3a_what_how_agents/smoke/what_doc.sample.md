---
contract: cast-requirements-what/v1
goal_slug: refine-requirements-better-rendering-v3
family: new_initiative
source_hash: cb3971de16bc
sections:
  - title: What every reader must get in seconds
    outcome: >-
      L1 — Any reader, in any family, grasps the job, the primary outcome, and what is in and out
      of scope from the above-the-fold view, fast. L2 — The page is shaped to the kind of work, so
      a bug fix reads like a bug fix and an initiative reads like an initiative; a stub renders a
      prompt-to-begin, never a broken page. This is the North Star the whole pipeline serves.
    block_refs: [US1, US2, SC-001, SC-002]
  - title: The bet — a cast-preso-style WHAT-then-HOW maker, not a deterministic renderer
    outcome: >-
      L1 — Replace the plain deterministic render with an LLM maker pipeline split into a WHAT layer
      (decides the information and outcome per block and family) and a HOW maker (cast-requirements-how)
      that picks a representation and emits self-contained, per-family-distinct HTML. L2 — HOW never
      invents the WHAT; it reuses a named cast-preso archetype library rather than improvising; the
      new agent set is WHAT + HOW + one checker + a diff/comment-resolution agent; the page is still
      served through the existing self-healing render loop and the canonical markdown stays the truth.
    block_refs: [FR-001, FR-002, FR-007, FR-008, FR-010, FR-012, FR-013]
  - title: Generated quality is gated, never assumed
    outcome: >-
      L1 — A single comprehension-plus-visual checker grades every generation and drives a
      quality-driven rework loop (bounded only by a high safety ceiling, not a cost cap) so a bad
      page never reaches a reader. L2 — The v2 deterministic golden-snapshot gate is replaced or
      supplemented by LLM-judged checks; a true no-output crash falls back to the deterministic page,
      but non-convergence serves the best-scoring attempt flagged for human review — never the plain
      page.
    block_refs: [US4, FR-004, FR-006, FR-009, SC-004, SC-008]
  - title: Comments and versions survive a render that now varies
    outcome: >-
      L1 — Switching to the maker must orphan zero comments — every comment stays anchored across a
      regenerate. L2 — Stable canonical ids (US-NN / FR-NNN / SC-NNN) are assigned upstream and the
      maker emits them verbatim, keeping the structural version diff deterministic; an LLM re-anchors
      or resolves only the text that genuinely moved or was reworded, and never silently drops a
      comment or invents a change absent from the source.
    block_refs: [US3, FR-003, FR-011, SC-003]
  - title: Generate once per source version, then cache
    outcome: >-
      L1 — The expensive render is produced at most once per source-content hash; an unchanged source
      serves cached HTML with no new model call. L2 — A source change regenerates on the next view
      and replaces the cache, reusing the v2 lazy-regeneration mechanism unchanged. Caching exists
      only to skip identical work — it never rations generation effort.
    block_refs: [US5, FR-005, SC-005]
  - title: Make commenting impossible to miss
    outcome: >-
      L1 — A first-time reader discovers how to comment without being told. L2 — Add a visible
      commenting affordance (hint or control) while keeping today's select-to-comment pill. This is a
      dogfooding fix independent of the maker and may ship ahead of the rest of v3.
    block_refs: [US6, FR-014, SC-006]
  - title: The page never fabricates — comprehension gaps go upstream
    outcome: >-
      L1 — When a detail that would materially help the reader is missing from the source, the page
      asks the upstream WHAT or refine agent for it before finalizing, rather than ship an incomplete
      explanation. L2 — If upstream cannot supply it, the gap is surfaced explicitly on the page, never
      invented; anything obtained is reconciled back to the canonical source so the page shows nothing
      that exists nowhere else.
    block_refs: [US7, FR-015, FR-016, SC-007]
  - title: What's deliberately out of scope
    outcome: >-
      L1 — This initiative does not touch the canonical markdown source or the comment-and-version
      backend, and it is not a from-scratch render-everything effort. L2 — Out: replacing the markdown
      source or comment/version backend, the deferred v2 human timed-read evaluation, rendering
      anything other than refined requirements, and a live always-regenerating render on every view
      (caching is required).
    block_refs: []
  - title: Still open
    outcome: >-
      L1 — Exactly one knob is deliberately deferred: which model tier the maker and checker run on.
      L2 — It is a later tuning decision to settle once the generation-and-check loop works end to
      end; every other design fork raised in refinement was resolved and folded into the decisions and
      requirements above.
    block_refs: []
unmapped_refs: []
gaps: []
---

## What every reader must get in seconds

**L1 takeaway:** the entire pipeline exists to serve one outcome — a reader unfamiliar with a goal
opens its render and, from the above-the-fold view alone, can correctly restate the job, the primary
outcome, and what is in and out of scope, without scrolling, clicking, or asking the author.

**L2 supporting points:** the layout is bespoke per classification, so the kind of work is legible
from the shape of the page (a bug fix reads like a bug fix, an initiative like an initiative); and a
stub or under-filled source renders a clear prompt-to-begin state rather than an empty or broken
page.

**Source content carrying it:** US1 (instant above-the-fold comprehension; stub → prompt-to-begin)
and US2 (bespoke per-family layout, omit empty blocks rather than pad) state the reader experience;
SC-001 (state job/outcome/scope within sixty seconds, cold-reader test) and SC-002 (visibly distinct
appropriate layout across all nine families) are the bar that proves it. The Intent's "North Star is
the user-facing HTML… a reader understanding the requirement quickly and completely" is the framing.

## The bet — a cast-preso-style WHAT-then-HOW maker, not a deterministic renderer

**L1 takeaway:** the chosen direction is to replace the v2 plain deterministic Python/Jinja renderer
with an LLM maker pipeline, split — borrowing cast-preso's guiding principle — into a WHAT layer that
decides the information and outcome to communicate per block and family, and a separate HOW maker
(cast-requirements-how, a cousin of cast-preso-how) that chooses the representation and produces the
self-contained, per-family-distinct HTML. The known cost — giving up render determinism and
reproducibility — is accepted, not waved away.

**L2 supporting points:** HOW never invents the WHAT; the maker selects from a named cast-preso
archetype library (compare-contrast and its code-diff variant, single-stat-hero, timeline,
diagram-annotated, and more) plus cast-preso's diff-representation utilities rather than improvising;
the new agent set is deliberately a WHAT agent + HOW maker + one thorough checker + a
diff-and-comment-resolution agent (chosen over a fuller multi-checker coordinator); the render is
still served through the existing self-healing `GET /goals/{slug}/render` loop and stays
self-contained; and the canonical `refined_requirements.collab.md` remains the source of truth — the
HTML is a generated, read-only projection the maker never writes back to.

**Source content carrying it:** FR-001 (HOW maker consumes WHAT intent + classification, produces the
HTML), FR-002 (selects layout/emphasis from family + recipe), FR-012 (the WHAT/HOW split, HOW never
invents WHAT), FR-013 (named archetype library, reuse over rebuild), FR-010 (the four-agent shape),
FR-007 (served through the existing loop, self-contained), FR-008 (canonical markdown stays, HTML is
read-only). The Decisions table's maker-agent and pipeline-shape rows are the rationale.

## Generated quality is gated, never assumed

**L1 takeaway:** a single new requirements-render checker grades every generated page for
comprehension and visual quality and drives a rework loop that runs until the comprehension bar is
met — quality-driven, with only a high safety ceiling against an infinite loop, not a rationed number
of rounds — so a bad generation never reaches a reader.

**L2 supporting points:** the v2 verification layer is revisited for a render that now varies — the
deterministic golden-HTML snapshot gate is replaced or supplemented by LLM-judged comprehension and
visual checks; and failure handling is split: a true no-output maker failure (crash, timeout) falls
back to the deterministic renderer so a page is never missing, but non-convergence (output produced,
bar never reached) serves the best-scoring attempt flagged for human review — explicitly never the
plain deterministic page.

**Source content carrying it:** US4 (gate the HTML behind a checker with a bounded rework loop),
FR-004 (single checker, quality-driven loop, high ceiling), FR-009 (revisit the verification layer,
LLM-judged checks), FR-006 (no-output → deterministic; non-convergence → best attempt flagged),
SC-004 (no-output fault injection serves deterministic), SC-008 (force-never-pass serves best attempt
with a recorded human-review flag). The non-convergence and single-checker rows in Decisions are the
rationale.

## Comments and versions survive a render that now varies

**L1 takeaway:** moving to the maker must not orphan feedback — with open comments present,
regenerating through the maker leaves every comment anchored to its quoted text, with zero new
orphans.

**L2 supporting points:** the mechanism is a deterministic id backbone — canonical anchor ids
(US-NN, FR-NNN, SC-NNN) are assigned upstream by the deterministic engine and the maker emits them
verbatim, never inventing or renaming an id; because the ids are stable the structural version diff
stays deterministic (id-based set-arithmetic, as in v2); an LLM is used only to narrate the diff and
to re-anchor or resolve comments whose target text genuinely moved or was reworded — it never invents
a change absent from the source and never silently drops a comment.

**Source content carrying it:** US3 (comments stay anchored across a maker regenerate; LLM resolution
reasons about meaning, never drops a comment), FR-003 (ids assigned upstream, maker emits verbatim,
LLM re-anchors only on genuine movement), FR-011 (stable ids → deterministic diff, LLM narrates and
re-anchors only moved/reworded text), SC-003 (comment-survival check across a regenerate, zero
orphans). The "LLM anchoring on a deterministic id backbone" decision row carries the why.

## Generate once per source version, then cache

**L1 takeaway:** the expensive render is generated at most once per source content version — an
unchanged source serves the cached HTML on a repeat view with no new model call.

**L2 supporting points:** the render is cached against the source content hash and regenerated on the
next view when the source changes, replacing the cached render, reusing the v2 embedded-source-hash
lazy-regeneration mechanism unchanged; and caching is scoped strictly to skipping re-render of
identical content — it never rations generation effort, which is governed by quality alone.

**Source content carrying it:** US5 (generate at most once per source version; second view is a cache
hit), FR-005 (cache by source hash, regenerate on change, reuse v2 mechanism, caching does not ration
effort), SC-005 (cache-hit observation on a repeat view, no new model call). The cache-by-hash
decision row is the rationale.

## Make commenting impossible to miss

**L1 takeaway:** a first-time reader, given no instructions, can discover how to leave a comment —
the feature must not read as absent.

**L2 supporting points:** add a visible commenting affordance (a hint or control) alongside the
existing select-to-comment pill, which stays; and this fix is independent of the maker and applies to
today's deterministic render too, so it can ship ahead of the rest of v3.

**Source content carrying it:** US6 (visible affordance in addition to the select-to-comment gesture;
the maker-independent note), FR-014 (discoverable affordance, keep the existing select-to-comment
path; dogfooding finding that the pill appears only on selection), SC-006 (unprompted usability check
— a reader discovers commenting without being told).

## The page never fabricates — comprehension gaps go upstream

**L1 takeaway:** when the presenter finds a detail that would genuinely help the reader but is absent
from the requirements file, it requests that detail from the upstream WHAT or refine agent before
finalizing the render — it never ships a silently incomplete explanation and never fabricates
requirement content.

**L2 supporting points:** if the upstream agent cannot supply the detail, the gap is surfaced
explicitly on the page rather than papered over with an invented answer; and any detail obtained this
way is reconciled upstream — written back to or flagged on the canonical requirements — so the page
never shows requirement content that exists nowhere else.

**Source content carrying it:** US7 (fill comprehension gaps by asking upstream, or clearly mark the
gap, never silently incomplete), FR-015 (request the missing detail before finalizing, never
fabricate), FR-016 (reconcile obtained detail back to the canonical source), SC-007 (gap-injection
test: render asks upstream or flags the gap). The "ask upstream for missing-but-useful detail"
decision row carries the rationale.

## What's deliberately out of scope

**L1 takeaway:** this is a render-quality initiative with a tight boundary — it does not touch the
canonical markdown source or the comment-and-version backend, and it is not an everything-renders,
always-fresh effort.

**L2 supporting points:** explicitly out of scope are replacing the canonical markdown source or the
comment/version backend, the deferred human timed-read evaluation carried over from v2, rendering
documents other than refined requirements, and a live always-regenerating render on every page view —
caching is required, not optional.

**Source content carrying it:** the Out of Scope section enumerates all four exclusions; the Intent's
"accepted… constraints" framing and the Constraints' "deterministic renderer stays as the fallback
substrate" reinforce the boundary. No canonical block ids attach to this section — it is scope
framing for the HOW layer, not a US/FR/SC block.

## Still open

**L1 takeaway:** exactly one knob remains open and is deliberately deferred — the model tier the
maker and the checker each run on.

**L2 supporting points:** it is a later tuning decision, to be settled once the generation-and-check
loop works end to end; every other design fork raised during refinement was resolved interactively
and folded into the Decisions table and the functional requirements, so this is the single live
unknown.

**Source content carrying it:** the Open Questions section's single `[USER-DEFERRED]` item (maker and
checker model tier) and the front matter's `open_unknowns: 1`. No canonical block ids attach to this
section — it briefs the HOW layer on the one acknowledged gap, not a US/FR/SC block.
