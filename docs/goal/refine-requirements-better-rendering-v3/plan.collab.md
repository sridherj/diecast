# High-Level Phasing Plan: Refine Requirements — Better Rendering (v3)

## Overview

Replace v2's plain deterministic Jinja render with a **cast-preso-style LLM maker
pipeline** (a WHAT agent that decides what to communicate per block/family, then a HOW
maker that generates bespoke, beautiful per-classification HTML), gated by a single
LLM comprehension-plus-visual checker with a **quality-driven (not cost-capped) rework
loop**, cached by source-hash, with the v2 deterministic renderer retained only as a
true-no-output-crash fallback. The whole pipeline optimizes for exactly one thing — a
reader grasping the job, outcome, and scope in seconds.

The shaping insight from the requirements: keep the v2 **deterministic id backbone**
(US-NN / FR-NNN / SC-NNN) so diffs and comment anchoring stay exact, and use LLMs only
where stable structure no longer holds (narrating diffs, re-anchoring genuinely-moved
text, filling comprehension gaps by asking upstream).

**Resolved decision (anchor backbone):** the canonical ids stay a *logical backbone* the
WHAT / diff / comment-resolution agents reason over — the DOM keeps v2's **quote /
verbatim-substring anchoring** rather than reintroducing `id=` attributes. This honors the
v2 render spec's "NO `id=` / superseded-stable-IDs-not-reintroduced" DOM contract (lowest
blast radius: the comment JS and relocate backstop need no contract change; only the diff
agent gains id-awareness, and the maker is free to vary layout without the DOM carrying
ids). Phase 1b now *validates* this approach rather than choosing it.

**Resolved decision (the WHAT layer thinks in communication, not in US/FR/SC):** the page is
NOT organized as a US/FR/SC dump. The WHAT agent decides the *family-appropriate* way to
communicate the work and names the sections accordingly — e.g. a data-analysis render might
lead with "signal sources" and "directional inputs on how to run the analysis"; a
user-facing requirement might lead with "key decisions" and "product principles." The
US/FR/SC ids are purely the behind-the-scenes backbone for anchoring and diffs; they never
dictate the page's structure. The per-family recipes in `families.py`
(`FAMILY_RECIPES`/`RECIPE_REALIZATION`) are the starting vocabulary the WHAT agent builds on.

No exploration/research notes exist (research_notes is a stub), so Phase 1 stays a de-risking
spike phase rather than straight to build.

---

## Phase 1: Validate the Maker & the Anchor Backbone (spikes)
**Outcome:** We know (a) an LLM maker can produce a render that beats the v2 deterministic
page on comprehension *and* beauty for at least two families while emitting the canonical
ids verbatim, and (b) the resolved logical-backbone / quote-anchored-DOM approach actually
holds — the v2 comment/version layer attaches to a *varying* maker render with zero new
orphans without the DOM carrying `id=` attributes.
**Dependencies:** None
**Estimated effort:** 2-3 sessions
**Verification:** Both spike outcomes confirmed in writing (see below); one hand-crafted
maker-style HTML per spike committed as evidence; a written confirmation that the
logical-backbone / quote-anchored-DOM approach attaches with zero new orphans, leaving the
`cast-requirements-render.collab.md` DOM contract intact.

Key activities (1a — maker-quality spike, parallel with 1b):
- Hand-run a cast-preso-how-style generation against 2-3 real family docs (this goal =
  new_initiative; plus one bug_fix and one data_analysis) using the cast-preso visual
  toolkit / style bible — no new agent yet, just prove the ceiling is reachable.
- Confirm the maker can emit US-NN / FR-NNN / SC-NNN verbatim on the right blocks without
  inventing or renaming an id (FR-003), and stay self-contained single-file (FR-007).
- **Decision gate:** quality clearly beats the deterministic page → proceed to Phase 3 as
  planned. If it can't clear the bar even by hand → revisit the maker vs hybrid fork before
  committing.

Key activities (1b — anchor-survival spike, parallel with 1a):
- Take a hand-crafted varying maker-style HTML and attach the existing comment/version
  layer (`comment_service`, `requirement_version_service.create_next`, `block_diff`) to it
  using the resolved approach: canonical ids as a *logical backbone*, DOM anchored by
  verbatim quote. Confirm zero new orphans on a regenerate-with-moved-text.
- **Validate (not decide) the logical-backbone approach:** confirm quote/verbatim-substring
  anchoring survives maker layout variation, so v2's "NO `id=`" DOM contract stays intact
  and only the diff agent needs to become id-aware. If quote anchoring proves insufficient
  under heavy rewording, that is the trigger to revisit the id-in-DOM fork — otherwise no
  render-spec DOM change is needed.
- **Gate:** logical-backbone approach confirmed to hold (or the revisit-trigger is hit and
  surfaced to the user).

---

## Phase 2: Discoverable Commenting & an Honest Fallback (ships ahead, parallel with Phase 1)
**Outcome:** A first-time reader discovers how to comment without being told, and the
deterministic renderer (which stays as the crash fallback) no longer leaks raw markdown or
truncates on abbreviations — so the substrate we fall back to is itself clean.
**Dependencies:** None (explicitly independent of the maker — the requirements note US6 can
ship ahead of the rest of v3)
**Estimated effort:** 1-2 sessions
**Verification:** Unprompted usability check — a first-time reader leaves a comment with no
instructions (SC-006); pytest over `goal_card.py` confirms `**bold**`/`` `code` `` render
clean and `vs.`/`e.g.`/`30 min.` no longer truncate the job statement.

Key activities:
- Add a visible commenting affordance (hint/control) alongside the existing select-to-comment
  pill in `static/requirements_comments.js` / the comment fragments (FR-014, US6).
- Fix dogfooding defect #1: make `goal_card.py` markdown-aware (convert/strip inline
  `**bold**` / `` `code` `` before injection in `renderer.py`).
- Fix dogfooding defect #2: teach `_first_sentence` / `_SENTENCE_END_RE` to ignore
  abbreviation periods (`vs.`, `e.g.`, `30 min.`).
- Keep the deterministic golden-snapshot test green for this fallback path even as the
  happy-path gate changes later (Phase 4a).

---

## Phase 3: The WHAT→HOW Maker Pipeline Renders Bespoke HTML
**Outcome:** On the happy path, `GET /goals/{slug}/render` is served by a two-agent
pipeline — a cast-requirements-what agent emits per-block/per-family communication intent,
a cast-requirements-how maker turns it into self-contained beautiful HTML selecting from a
named archetype library — and the output carries the canonical ids verbatim. The
deterministic renderer is still wired as fallback but is no longer the happy path.
**Dependencies:** Phase 1 (both decision gates)
**Estimated effort:** 5-7 sessions (includes the background render-job + status surface)
**Verification:** Render this goal + one other family end-to-end through the pipeline; the
two pages are visibly distinct per family with family-appropriate section names, not US/FR/SC
slots (FR-002); a parser confirms every canonical requirement unit is represented and mapped
to its logical id for anchoring, and no id is invented (FR-003); output is a single
self-contained file (FR-007);
canonical `refined_requirements.collab.md` is never written by the maker (FR-008); opening
`/render` on a changed source serves a "generating…" state immediately (no blocking wait)
and swaps in the finished render when the job completes.

Key activities:
- Build `cast-requirements-what` and `cast-requirements-how` as **net-new** requirements
  agents (reusing the preso visual toolkit, archetype library, and the what/how split, but
  not coupled to the preso slide agents) per cast agent-design conventions (FR-001, FR-010,
  FR-012). The HOW layer never invents the WHAT.
- The WHAT agent decides the **family-appropriate communication structure**, not a US/FR/SC
  layout: it names the sections that best land the work for that family (e.g. data-analysis →
  "signal sources" + "directional inputs"; user-facing requirement → "key decisions" +
  "product principles"), building on the `families.py` recipes as starting vocabulary. The
  US/FR/SC ids ride along only as the logical anchoring backbone.
- Wire the maker to select from the named cast-preso archetype library (compare-contrast +
  code-diff variant, single-stat-hero, timeline, diagram-annotated, …) and reuse cast-preso
  diff-representation utilities — reuse over rebuild (FR-013, FR-002).
- Implement the deterministic logical id-backbone (ids assigned upstream by the engine;
  maker emits them verbatim on the right blocks — FR-003) while the served DOM stays
  quote-anchored (no `id=`), per the resolved anchor decision.
- Add an orchestrator seam in the render service so `render_requirements()` becomes
  the fallback branch and the maker pipeline is the primary branch, reusing the v2
  source-hash lazy-regeneration cache unchanged (FR-005, SC-005).
- **Make generation a background job, never blocking the view (resolved decision):** when
  `/render` is hit for a source whose hash has no cached render, kick off the maker pipeline
  as an async job and immediately serve a live "generating…" state that polls/streams and
  swaps in the finished render when ready. Cached views stay instant; leaving/submitting
  comments is on a separate path and never waits on the maker. This adds a small render-job
  + status surface (job state, poll/stream endpoint, generating-state fragment) to this phase.
- Render the prompt-to-begin state for stub sources unchanged (US1 Scenario 2).
- `/update-spec` `cast-requirements-render.collab.md`: the maker is now the happy-path
  render and the pure `render_requirements()` boundary is demoted to fallback; the
  `GET /goals/{slug}/render` route now serves a generating-state + async render job on a
  cache miss instead of regenerating synchronously. The DOM contract is **unchanged** (still
  quote-anchored, no `id=`); the spec adds the logical id-backbone as a maker-emitted,
  non-DOM structure.

---

## Phase 4a: The Quality Gate — Checker & Quality-Driven Rework Loop (parallel with 4b)
**Outcome:** No maker render reaches a reader unless a single comprehension-plus-visual
checker passes it; the loop reworks until the comprehension bar is met (guarded only by a
high anti-infinite-loop ceiling, not a cost cap); on a true no-output crash the deterministic
page is served, and on non-convergence the best-scoring attempt is served and flagged for
human review — never the plain page.
**Dependencies:** Phase 3
**Estimated effort:** 3-4 sessions
**Verification:** Force a low-quality generation → checker fails it and triggers rework
(US4); fault-inject a no-output maker → deterministic page served (SC-004); force the checker
to never pass → best attempt served + human-review flag recorded, deterministic page NOT
served (SC-008).

Key activities:
- Build `cast-requirements-render-checker` — one thorough agent grading comprehension +
  visual quality in a single pass (the owner chose this over a multi-checker coordinator)
  (FR-004, FR-010).
- Implement the quality-driven rework loop with a high safety ceiling only (loops are not
  rationed — cost/latency explicitly not constraints).
- Implement the two-branch fallback policy precisely (FR-006): no-output crash →
  deterministic; output-but-non-convergent → best attempt + human-review flag.
- Reuse the SC-001 cold-reader idea: the checker stands in for the human reader stating job/
  outcome/scope (SC-001), folding in `cast-requirements-checker`'s verdict shape.
- `/update-spec`: replace/supplement the deterministic golden-HTML snapshot gate with the
  LLM-judged comprehension+visual checks (FR-009) and record the new fallback policy.

## Phase 4b: Comments & Versions Survive the Maker (parallel with 4a)
**Outcome:** Regenerating a render through the maker leaves every open comment anchored with
zero new orphans, and the structural version diff stays deterministic (id-based set
arithmetic) while an LLM only narrates the diff and re-anchors text that genuinely moved or
was reworded — never inventing a change absent from the source.
**Dependencies:** Phase 1 (backbone validated) + Phase 3 (maker output exists)
**Estimated effort:** 3-4 sessions
**Verification:** With open comments present, regenerate through the maker → every comment
stays anchored, zero new orphans (SC-003); a moved/reworded block is re-anchored by the LLM,
not dropped; a diff never shows a change not present in the source (trust-boundary check).

Key activities:
- Build the diff-and-comment-resolution agent (extend/replace `cast-comment-reanchor`) that
  reasons about meaning to re-anchor or resolve comments, never silently dropping one
  (FR-011, US3 Scenario 2, decision: orphan-over-guess).
- Keep `block_diff` structural set-arithmetic deterministic on the logical id backbone; the
  LLM only narrates and handles moved/reworded text (FR-011).
- Guarantee the maker emits the logical per-block ids for every US/FR/SC so the
  quote-anchored comment + version layer attaches (US3 Scenario 1) — scaling up the Phase 1b
  mechanism. No `id=` is added to the DOM.
- `/update-spec`: record that the comment/version layer keeps quote/verbatim-substring
  anchoring under a varying render, the logical id-backbone the diff agent reads, and the
  LLM-resolution trust boundary (narrate/re-anchor only; never invent a change).

---

## Phase 5: Gap-Filling, Cross-Family Hardening & Sign-Off
**Outcome:** The presenter fills genuine comprehension gaps by asking upstream (never
fabricating) and reconciles obtained detail back to the canonical source; and every one of
the nine families renders a visibly distinct, clean, comprehensible page — the "I'd put this
in front of a customer without apologizing" bar.
**Dependencies:** Phase 3, Phase 4a, Phase 4b
**Estimated effort:** 3-5 sessions
**Verification:** Gap-injection test — remove a key detail → the page either supplies it
(sourced upstream) or marks the gap, never silently incomplete (SC-007); one golden render
per family reviewed, all nine visibly distinct and appropriate (SC-002); full SC-001…SC-008
sweep green.

Key activities:
- Implement HOW-asks-WHAT/refine gap-filling: when the maker detects a comprehension gap
  absent from the requirements file, request it upstream before finalizing; surface the gap
  explicitly if upstream can't supply it; never fabricate (FR-015, US7).
- Reconcile obtained detail back to canonical through the **existing v2 change-request gate
  unchanged** (resolved decision): the asked-for detail becomes a normal change-request
  (propose → notify → human gate, never auto-sync) via `cast-requirements-writeback` /
  `change_request_service`; no new writer or bypass. The page marks the gap until the detail
  is approved, so it never shows content that exists nowhere else (FR-016, honoring the v2
  "never auto-sync" rule).
- Generate and review one golden render per family across all nine `WorkFamily` values
  (SC-002); fix any family that looks broken or padded (US2 Scenario 2 — omit empty blocks).
- Run the full success-criteria sweep (SC-001 through SC-008) and capture results.
- Final `/update-spec` pass reconciling `cast-requirements-render.collab.md` (and
  `cast-requirements-roundtrip.collab.md` if the gap-fill writeback path changed) with the
  shipped v3 behavior.

---

## Build Order

```
Phase 1 (spikes: maker + anchor) ─────────┐
                                          ├──► Phase 3 ──┬──► Phase 4a (checker/loop) ──┐
Phase 2 (discoverable comments + fixes) ──┘             └──► Phase 4b (comment survival)┴──► Phase 5
   (parallel with Phase 1, ships ahead)
```

**Critical path:** Phase 1 → Phase 3 → {Phase 4a ∥ Phase 4b} → Phase 5

- Phase 2 runs in parallel with Phase 1 and can **ship independently** ahead of the rest of
  v3 (US6 is decoupled from the maker; the fallback fixes harden the substrate Phase 3 falls
  back to).
- Phase 4a and Phase 4b are independent (checker vs comment-survival) and run concurrently
  once the maker (Phase 3) exists.

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Quote/verbatim-substring anchoring proves insufficient under heavy maker rewording, forcing a late switch to ids-in-DOM (which would overturn v2's "NO `id=`" contract and ripple into writeback/routing specs) | Med | Resolved approach keeps the DOM contract intact; Phase 1b *validates* quote-anchoring holds before any build — if it doesn't, the revisit-trigger surfaces the id-in-DOM fork to the user early, not mid-Phase-4b |
| Varying render orphans open comments on regenerate | High | Deterministic id backbone + LLM resolver with never-silently-drop / orphan-over-guess invariant; Phase 1b spike + SC-003 gate |
| Maker fabricates requirement content or can't hit the quality bar | High | WHAT/HOW split (HOW never invents WHAT) + checker gate + gap-fill asks upstream rather than inventing; Phase 1a spike |
| Checker is an unreliable gate (passes bad pages, or loops forever) | Med | High anti-infinite-loop ceiling + best-attempt-plus-flag on non-convergence; tune in Phase 4a; cost is explicitly not a constraint |
| Non-determinism breaks v2 golden-snapshot tests / CI | Med | Replace happy-path snapshot gate with LLM-judged checks (FR-009); keep deterministic fallback snapshot-tested (Phase 2) |
| Self-contained single-file constraint vs inlining the full preso visual toolkit | Low | Reuse cast-preso's existing self-contained slide approach; verify in Phase 1a |
| Autonomous runs can't drive a browser for visual/taste gates | Low | Per project note, visual gates get a static verdict + human-eyeball carry-forward; never block on them |

## Resolved Decisions

- **Anchor backbone (resolved 2026-06-12):** canonical ids stay a *logical backbone*; the DOM
  keeps v2's quote/verbatim-substring anchoring (no `id=`). Honors the v2 render-spec DOM
  contract; only the diff agent becomes id-aware. Phase 1b validates rather than chooses.
- **Render execution model (resolved 2026-06-12):** the maker runs as a background job. A
  view of a changed source serves a live "generating…" state immediately and swaps in the
  finished render when ready — the page never blocks on the multi-minute loop, and the
  comment path is unaffected. Adds a render-job + status surface to Phase 3.
- **Pipeline agents + section vocabulary (resolved 2026-06-12):** `cast-requirements-what` and
  `cast-requirements-how` are net-new requirements agents (reusing preso toolkit/archetypes,
  not the preso slide agents). The WHAT layer organizes the page by family-appropriate
  communication (e.g. "signal sources", "directional inputs", "key decisions", "product
  principles") rather than US/FR/SC slots; ids are anchoring-only.
- **Gap-fill write-back door (resolved 2026-06-12):** detail the maker obtains upstream is
  reconciled through the existing v2 change-request gate unchanged (propose → notify → human
  gate); no new writer into the canonical source. The page marks the gap until approval.

## Open Questions

- **[USER-DEFERRED]** Maker and checker model tier (which model each runs on) — deferred as a
  later tuning knob once the generation-and-check loop works end to end (carried from
  refined_requirements Open Questions).
_All design forks raised during planning were resolved interactively (see Resolved
Decisions). The only remaining open item is the user-deferred model-tier knob above._

## Spec References

Loaded specs (top matches by domain):
- **`cast-requirements-render.collab.md` (Draft v2)** — the v2 render + comment/version
  contract this goal directly modifies. **Consistency flags:** (1) v2's Phase-4 DOM contract
  states "NO `id=` / `data-block-anchor` — superseded stable-IDs not reintroduced". *Resolved:*
  the v3 FR-003 ids stay a logical (non-DOM) backbone and the DOM stays quote-anchored, so the
  DOM contract is **preserved**; `/update-spec` adds the logical backbone + diff-agent
  id-awareness rather than overturning the contract (Phase 3/4b). (2) v2's deterministic
  golden-HTML snapshot gate is replaced/supplemented by
  LLM-judged checks (FR-009) → `/update-spec` Phase 4a. (3) The pure `render_requirements()`
  boundary moves from happy-path to fallback, and the fallback policy changes (FR-006) →
  `/update-spec` Phase 3/4a.
- **`cast-goal-classification.collab.md` (Draft v1)** — supplies the LOCKED nine-value
  `WorkFamily` enum and `FAMILY_RECIPES`/`RECIPE_REALIZATION` block semantics the maker reads
  to choose per-family layout (FR-002, SC-002). No change expected — consumed, not modified.
- **`cast-requirements-roundtrip.collab.md` (Draft v1)** — Phase 5's gap-fill reconciliation
  (FR-016) routes through the existing change-request write-back gate **unchanged** (resolved
  decision), so no `/update-spec` is expected here — the gate is consumed, not modified.
