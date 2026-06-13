# Refine Requirements — Better Rendering (v3): Phase 1 — Validate the Maker & the Anchor Backbone (spikes)

## Overview

This plan details **Phase 1 only** of the v3 high-level plan: two parallel de-risking spikes
that must both pass their gates before Phase 3 (the WHAT→HOW maker pipeline) is built.
Spike **1a** proves by hand that an LLM maker working from the cast-preso visual toolkit can
produce a requirements render that clearly beats the v2 deterministic page for at least two
work families, while emitting the canonical ids verbatim and staying a self-contained single
file. Spike **1b** attaches the *existing, unmodified* v2 comment/version layer to a
hand-crafted, deliberately-varying maker-style HTML and confirms the resolved
logical-backbone + quote-anchored-DOM approach holds — zero new orphans on a
regenerate-with-moved-text, with v2's "NO `id=`" DOM contract intact.

**Key grounding insight (sharpens, does not change, the spike design):** the v2
comment/version machinery anchors to the **canonical markdown source**, not to the HTML.
`relocate_comment`'s verbatim-substring backstop (FR-019), `create_next`'s
`displaced_comment_ids` string-find (FR-022), and `block_diff._key`'s `(kind, ref)` matching
on `US-NN`/`FR-NNN`/`SC-NNN` tokens all run against the `.collab.md` text — and the maker
never writes that file (v3 FR-008). A varying maker render therefore **cannot orphan a
comment at the DB layer by itself**. The genuine risk surfaces 1b must instrument are:

1. **DOM mark placement** — `static/requirements_comments.js` places `<mark>` by tree-walking
   a block container's text nodes and running `indexOf(quoted_text)` on the concatenated
   text. If the maker paraphrases, summarizes, or fragments requirement text, marks silently
   fail to place (the comment demotes to tray-only) — a UX regression the DB never records.
2. **Verbatim-text carriage** — the maker contract implied by (1): each requirement unit's
   anchorable text must appear verbatim and contiguous (within one semantic container) in the
   rendered DOM, even as layout, ordering, and section vocabulary vary per family.
3. **Source-edit regeneration** — moved/reworded *source* text exercises the full v2 chain
   (`create_next` → displaced detection → `cast-comment-reanchor` → same-door `relocate` with
   the verbatim backstop). This chain is already deterministic on the logical id backbone;
   1b replays it with maker-style HTML as the display layer and measures orphan deltas.

Planning only — this document specifies the spikes; it does not execute them.

## Operating Mode

**HOLD SCOPE** — `refined_requirements.collab.md` front-matter pins `scope_mode: hold`, and
the delegation context repeats it ("Honor scope_mode: hold"). Owner-resolved decisions in
`docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md` are binding; 1b
**validates** the anchor-backbone decision and may only surface a revisit-trigger, never
re-decide it.

## Position in Overall Plan

```
Phase 1 (THIS PLAN: 1a ∥ 1b spikes) ──────┐
                                          ├──► Phase 3 ──┬──► Phase 4a ──┐
Phase 2 (comments affordance + fallback   │              └──► Phase 4b ──┴──► Phase 5
         fixes; runs parallel, disjoint) ─┘
```

Phase 1 has no dependencies and gates Phase 3 (both spike gates) and Phase 4b (1b's
backbone validation). Phase 2 runs concurrently and owns `goal_card.py` /
`_first_sentence` / the comment-affordance UI — **this plan must not touch those files**.

## Depends On (from prior plans / seed decisions)

From the binding seed (`refine-requirements-better-rendering-v3-decisions-so-far.md`):

- **Anchor backbone:** canonical ids are a logical backbone only; served DOM keeps v2
  quote/verbatim-substring anchoring, **no** `id=`/`data-block-anchor`. 1b validates this.
- **Page-structure vocabulary:** family-appropriate communication sections, never US/FR/SC
  slots; ids ride along as anchoring metadata. The 1a hand-crafted HTML must demonstrate this.
- **Fallback policy / background-job model / gap-fill door:** owned by Phases 3-5; out of
  scope here except that spike artifacts must not prejudge them.

From v2 (consumed verbatim, never modified in Phase 1):

- `comment_service` flat functions with injectable `db_path` (`create_comment`,
  `relocate_comment`, `orphan_comment`, `open_comment_count`, …) — FR-020.
- `requirement_version_service.create_next(goal_slug, content, created_by, *, db_path=None)`
  → `{version, convergence, open_comments, displaced_comment_ids}` — FR-021/022.
- `block_diff.diff_blocks` / `summarize` — pure, keyed on `(kind, ref)` for US/FR/SC blocks
  (the id backbone already exists, source-side) — FR-024.
- `cast-comment-reanchor` subagent — bare-JSON verdicts, orphan-over-guess — FR-027.
- The Phase-4 DOM contract — US7/FR-012/FR-013 — and FR-028 progressive enhancement
  (`htmx.min.js` + `requirements_comments.js` + `data-goal-slug` are the only sanctioned
  script references in an otherwise self-contained file).
- `extract_zero_click_view` + `cast-requirements-checker` (SC-001 cold-reader gate) — the
  comparison judge 1a reuses.

From cast-preso (reused, not coupled): `~/.claude/skills/cast-preso-visual-toolkit/`
(`visual_toolkit.human.md` style tokens + `templates/slide-archetypes/*.html` — 11 archetypes
including compare-contrast, single-stat-hero, timeline, diagram-annotated) and the
`cast-preso-how` 8-step discipline (brainstorm ≥2-3 approaches → archetype shortlist →
brief → HTML) which 1a follows **manually** — no new agent is built in Phase 1.

---

## Sub-phase 1a: The Maker Quality Ceiling Is Proven By Hand

**Outcome:** For at least two work families (this goal = `new_initiative`, plus one
`bug_fix` or `data_analysis`), a hand-run cast-preso-how-style generation produces a
requirements page that clearly beats the v2 deterministic render on comprehension and
visual quality, carries every canonical id verbatim with none invented or renamed (FR-003),
and is a self-contained single file (FR-007) — or the gate fails and the maker-vs-hybrid
fork is surfaced for revisit before Phase 3 commits.

**Dependencies:** None (parallel with 1b).
**Estimated effort:** 1-2 sessions.

**Verification:**
- `docs/goal/refine-requirements-better-rendering-v3/spikes/1a/spike-results.md` exists and
  records an explicit per-family verdict: `BEATS DETERMINISTIC: yes/no` with evidence.
- One committed maker-style HTML per family under `spikes/1a/` plus the deterministic
  baseline render of the same source for side-by-side comparison.
- An id-audit script run recorded in the results: the set of `US-NN`/`FR-NNN`/`SC-NNN`
  tokens visible in the maker HTML **equals** the set parsed from the source — no missing,
  no invented, no renamed ids. The audit also asserts **id-to-block correspondence** — each
  id label sits on the block whose source text it identifies (FR-003 is per-block, not just
  set-membership) — since Phase 3 reuses this audit as its acceptance pattern and set-equality
  alone would pass even if a label sat on the wrong block.
- A self-containment audit recorded: no external `src`/`href` fetches beyond the FR-028
  sanctioned `/static/htmx.min.js` + `/static/requirements_comments.js`; no CDN fonts; CSS
  inline.
- `cast-requirements-checker` verdicts captured for BOTH the maker HTML and the
  deterministic baseline (run on the zero-click extract of each).

Key activities:

- **Assemble the family corpus.** Doc 1: this goal's own
  `docs/goal/refine-requirements-better-rendering-v3/refined_requirements.collab.md`
  (classified `new_initiative`, the only real classified doc in the repo). Doc 2: author a
  real `bug_fix` requirements doc from the actual v2 dogfooding defect (the `goal_card.py`
  raw-markdown leak — real problem, real evidence, real fix scope), in the standard
  refined-requirements shape with `classification.family: bug_fix` front matter, stored
  under `spikes/1a/fixtures/`. Doc 3 (stretch, only if sessions allow): a `data_analysis`
  doc by the same method. Generate the v2 deterministic baseline for each via
  `render_requirements()` (pure call — do **not** drop files into `goals/{slug}/`).
- **Hand-run the preso-how discipline per doc** (manually, in-session — no new agent):
  brainstorm 2-3 visual approaches with slide-specific pros/cons and an honest
  Steve-Jobs-test verdict, shortlist archetypes from the toolkit library, write a short
  brief, then craft the HTML — starting from the visual toolkit's style tokens and
  adapting archetype vocabulary (e.g. single-stat-hero treatment for the Goal Card,
  compare-contrast for decisions, timeline for phases) to a **scrolling document page**,
  not a reveal.js slide. Keep the brief and approach notes as spike evidence.
  *Conscious non-delegation:* `/cast-preso-how` is **not** invoked — it generates reveal.js
  slides, and the net-new requirements agents are Phase-3-owned; only its 8-step *discipline*
  is followed by hand here. (Recording this prevents an execution-time misfire — either
  invoking the slide agent or skipping the discipline.)
- **Honor the resolved page-structure decision:** section names are family-appropriate
  communication ("key decisions", "what broke and the evidence", …) — never US/FR/SC
  slots; the canonical ids appear as small anchoring labels on their blocks (visible text,
  NOT `id=` attributes).
- **Respect the v2 DOM contract while hand-crafting:** each requirement unit one contiguous
  semantic `<section>`/`<li>` under a real `<h2>`/`<h3>`, no span fragmentation, zero `id=`
  and zero `data-block-anchor` anywhere (FR-012/FR-013), FR-028 script tags +
  `data-goal-slug` present so 1b can reuse the same files.
- **Run the audits** (small throwaway scripts under `spikes/1a/`): id-token set equality
  **and per-block correspondence** source↔HTML; self-containment grep; zero-`id` grep.
- **Judge the gate.** → Delegate: `cast-requirements-checker` (subagent, bare-JSON verdict)
  over the zero-click extract of the maker HTML and of the deterministic baseline, per doc.
  Review output for: `can_state_what`, completeness of `restated_job/outcome/scope`,
  `missing[]`. Supplement with a structured rubric self-assessment (hierarchy, scannability,
  family-appropriateness, visual quality) comparing the two side by side. Record
  the human-eyeball browser pass as a carry-forward item (autonomous runs cannot drive a
  browser — static verdicts + carry-forward, never block).
- **Write the decision-gate verdict** in `spike-results.md`: quality clearly beats the
  deterministic page → Phase 3 proceeds as planned; cannot clear the bar even by hand →
  surface the maker-vs-hybrid fork for the owner to revisit (do NOT silently re-scope).

**Design review:**
- **Artifact placement (error/rescue):** spike HTML must live under
  `docs/goal/.../spikes/1a/`, **never** as `goals/{slug}/refined_requirements.html` — that
  filename is a render-class artifact wired to the lazy-regen route and the FR-026 folder
  invariant; a hand-crafted file there would be served live and/or trip
  `test_fr007_readonly_guard.py`. ✓ planned accordingly.
- **Spec consistency:** Phase 1 makes **no** spec changes; the spike consumes
  `cast-requirements-render.collab.md` (DOM contract, zero-click, checker I/O) and
  `cast-goal-classification.collab.md` (families/recipes) read-only. `/cast-update-spec`
  work is owned by Phases 3/4 per the high-level plan. ✓ no `/update-spec` here.
- **Naming:** spike fixture doc must not collide with any live goal slug; keep fixtures
  under `spikes/1a/fixtures/`, no DB rows needed for 1a. ✓
- **Judge validity (error path):** `cast-requirements-checker` was built for the v2 page;
  if its verdict on maker HTML looks anomalous (e.g. fails on a page a human clearly
  comprehends), record the anomaly in spike-results as Phase 4a input — the checker is
  being replaced by a richer one there; do not tune it now.

## Sub-phase 1b: The Quote-Anchored Backbone Survives a Varying Render

**Outcome:** The existing v2 comment/version layer, attached unmodified to a hand-crafted
varying maker-style HTML, demonstrably holds under the resolved logical-backbone +
quote-anchored-DOM approach: every open comment's mark places on the maker DOM; a
regenerate-with-moved-text produces **zero new orphans** (moved-but-surviving content
relocates; orphan verdicts only where content is genuinely gone); `block_diff` stays
deterministic on the id backbone; and the v2 "NO `id=`" DOM contract stays intact — or the
revisit-trigger (quote anchoring insufficient under heavy rewording) is explicitly surfaced
to the owner. **Validate, never re-decide.**

**Dependencies:** None (parallel with 1a; can reuse 1a's hand-crafted HTML if ready, but
must not wait on it — a minimal varying HTML pair suffices).
**Estimated effort:** 1-1.5 sessions.

**Verification:**
- `docs/goal/refine-requirements-better-rendering-v3/spikes/1b/spike-results.md` records,
  with numbers: mark-placement rate on maker HTML v1 and v2; displaced-comment count after
  the source edit; per-comment reanchor verdicts; orphan delta (must be 0 new orphans for
  surviving content); `diff_blocks` partition-invariant check result.
- The `section_hint`-mismatch probe's outcome is recorded **explicitly** (places via the
  verbatim quote despite the renamed maker section, **or** degrades to tray-only) as a
  Phase-3 input — a seeded comment with no recorded verdict is not a measured gate.
- The committed evidence pair: maker-style HTML v1 (layout A) and v2 (layout B, regenerated
  against the edited source), plus the source pair (original + moved/reworded edit).
- A zero-`id` audit on both HTML files (the golden structural assertions from
  `test_requirements_renderer.py` replayed: no `id=`, no `data-block-anchor`).
- The throwaway harness script(s) committed under `spikes/1b/` so the run is replayable.

Key activities:

- **Build the test bed (isolated, never the live house DB):** a throwaway SQLite DB via the
  services' injectable `db_path`, and a scratch goal + source document. Source pair: start
  from the existing fixture pair
  `cast-server/tests/fixtures/refine_requirements_v2/refined_requirements.collab.md` +
  `.v2-edit.collab.md`; if the edit doesn't move/reword enough text, author a heavier
  variant that (i) moves a commented block to a different section, (ii) rewords a commented
  sentence while preserving meaning, (iii) deletes one commented block outright (the
  legitimate-orphan control).
- **Seed comments** through `comment_service.create_comment` (same-door, `author_kind`
  varied): ≥6 open comments spanning — a comment on an US/FR/SC block that will move; one
  on text that will be reworded; one on text that stays put; one on the block that will be
  deleted; one with a short/generic quote (the hard reanchor case); one anchored under a
  heading whose maker-HTML section name differs from the canonical heading
  (`section_hint` robustness probe).
- **Hand-craft maker-style HTML v1** for the original source (reuse 1a output if available):
  family-communication section names, varied layout, canonical ids as visible text labels,
  zero `id=`, FR-028 scripts + `data-goal-slug`, and each requirement unit's anchorable
  text carried **verbatim and contiguous** within one semantic container.
- **Measure mark placement on v1:** replicate `requirements_comments.js` placement
  semantics in a small Python harness — per block container, concatenate descendant
  text-node content (stdlib HTMLParser) and run `find(quoted_text)` — asserting every open,
  non-displaced comment's quote is found exactly as the JS would find it. Gate: 100%
  placement for comments whose source text is untouched. **A hit counts only when it lands
  within the comment's intended block container** (not merely `find()` ≥ 0 anywhere in the
  DOM) — `concat.indexOf` returns the first match anywhere, so a generic/short quote could
  "place" on the wrong block and pass; scoping the assertion to the intended container turns
  the already-seeded short/generic-quote comment into a real test. (No browser available in
  autonomous runs; the harness mirrors the JS algorithm and a live-browser eyeball is
  recorded as a carry-forward item.)
- **Regenerate-with-moved-text:** apply the edited source; hand-craft maker-style HTML v2
  with a *deliberately different* layout/section ordering (this is the "varying" in
  varying render); run `requirement_version_service.create_next` with the new content and
  capture `displaced_comment_ids` — assert it equals exactly the moved + reworded +
  deleted comment set (the untouched comment must NOT displace).
- **Run the reanchor chain.** → Delegate: `cast-comment-reanchor` (subagent-mode, bare-JSON
  verdicts) over `{displaced comments, old_content, new_content}` — note `new_content` is
  the **new source markdown**, per the v2 contract. Review output for: relocated verdicts
  whose `new_quoted_text` is verbatim in the new source; the deleted block's comment
  verdict = `orphaned` (correct, not a "new orphan" — its content is genuinely gone);
  orphan-over-guess honored on the generic-quote case. Apply verdicts through the same-door
  `relocate`/`orphan` service calls and confirm the FR-019 verbatim backstop passes every
  relocate.
- **Re-measure mark placement on v2** with the relocated quotes: gate = **zero new
  orphans** (every comment whose content survives the edit ends `open` + mark-placeable on
  the v2 maker DOM; only the deleted-block comment is orphaned) and 100% placement for
  relocated + untouched comments.
- **Confirm the diff stays deterministic:** run `diff_blocks(old_parsed, new_parsed)` +
  `summarize` over the source pair; assert the partition invariant and that the moved
  block lands in `unchanged`/`modified` by its `(kind, ref)` id key — evidence that the id
  backbone needs **no** new machinery and only the Phase-4b *narration* agent becomes
  id-aware. The maker HTML plays no role here; record that explicitly.
- **Write the gate verdict** in `spike-results.md`: `BACKBONE HOLDS: confirmed` with the
  measured numbers, **or** `REVISIT-TRIGGER: quote anchoring insufficient under heavy
  rewording` with the failing cases attached — surfaced to the owner, with no change made
  to the approach, the DOM contract, or any spec (the binding decision stays binding).

**Design review:**
- **Spec consistency:** the spike consumes US7-US13/FR-012-FR-028 of
  `cast-requirements-render.collab.md` verbatim and modifies nothing. The one sharpening
  worth recording for Phase 3/4b spec work (NOT now): the v3 maker contract needs an
  explicit "anchorable text carried verbatim in the DOM" clause — today's spec never needed
  it because the deterministic renderer trivially carried source text. Flagged for the
  Phase 3 `/update-spec` activity. ⚠️ carry-forward, no action in Phase 1.
- **Error & rescue:** `cast-comment-reanchor` dispatch may fail/time out — per FR-027 the
  failure is an explicit no-op (comments stay displaced in the tray); the spike retries
  once, then records the dispatch failure rather than hand-fabricating verdicts. A relocate
  rejected by the 422 backstop downgrades to orphan and counts AGAINST the gate (that is
  precisely the failure the spike exists to catch).
- **Security / data safety:** throwaway `db_path` everywhere; the live house DB and the
  real goal folders are never written. The fixture's `goals/{slug}` is a scratch slug, and
  no file named `refined_requirements.html` is written into any real goal folder. ✓
- **Harness fidelity (named risk):** the Python mark-placement harness re-implements the
  JS walker; a fidelity gap (e.g. whitespace normalization differences across element
  boundaries) could pass the harness yet fail in a browser. Mitigation: keep the harness
  byte-faithful to the JS (`concat.indexOf`, no normalization), include one
  deliberately-split-across-inline-elements quote as a harness self-test, and carry the
  live-browser check forward.

## Build Order

```
Sub-phase 1a (maker quality ceiling) ──┐  (no dependency between them;
                                       ├──► Phase-1 gate review → Phase 3 / Phase 4b
Sub-phase 1b (anchor survival)     ────┘   1b may reuse 1a HTML opportunistically)
```

**Critical path:** whichever spike fails its gate first — both gates must be green (or
their revisit-triggers consciously accepted by the owner) before Phase 3 starts.

**Phase-1 gate artifact:** the two `spike-results.md` verdicts are aggregated into a single
`docs/goal/refine-requirements-better-rendering-v3/spikes/PHASE1-GATE.md` that records
`1a: BEATS DETERMINISTIC yes/no`, `1b: BACKBONE HOLDS / REVISIT-TRIGGER`, and the combined
**go-to-Phase-3 / surface-to-owner** decision. The build-order diagram's "both gates green"
edge needs one owning artifact, not two separate files a reader must reconcile — this makes
the Phase-3 entry condition a single measurable gate.

## Design Review Flags

| Sub-phase | Flag | Action |
|-----------|------|--------|
| 1a | Spike HTML named/placed as a render-class artifact would be served live and trip FR-026/readonly-guard tests | Keep all spike artifacts under `docs/goal/.../spikes/`; never write `goals/{slug}/refined_requirements.html` |
| 1a | `cast-requirements-checker` may judge maker HTML anomalously (built for the v2 page) | Record anomalies as Phase 4a input; do not tune the checker in Phase 1 |
| 1b | Maker contract gap: "anchorable text verbatim in DOM" is implied by quote anchoring but unspec'd | Carry forward to the Phase 3 `/cast-update-spec` activity (logical-backbone addition) |
| 1b | Python mark-placement harness may diverge from browser JS semantics | Byte-faithful re-implementation + split-quote self-test + human browser pass carried forward |
| 1b | Reanchor dispatch failure could stall the spike | One retry, then record as dispatch failure (explicit no-op per FR-027), never fabricate verdicts |
| both | Live house DB / real goal folders must stay untouched | Injectable `db_path` + scratch slug + fixtures dir, asserted in the harness |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Quote anchoring fails under heavy rewording (marks unplaceable / relocates degrade to orphans) | High | This IS the 1b gate: measured, and on failure the revisit-trigger (id-in-DOM fork) is surfaced to the owner — never silently worked around |
| Hand-crafted "maker-style" HTML flatters the maker (a human crafts better than an agent will) | Med | Treat 1a as a *ceiling* proof only — the gate wording is "reachable by hand"; Phase 3 verification re-proves it agent-generated. Record hand-effort honestly in spike-results |
| Only one real classified doc exists; the bug_fix doc is authored for the spike | Med | Author it from a real defect (the goal_card markdown leak) with real evidence, in the standard refined shape — and note in spike-results that family breadth is re-validated across all nine families in Phase 5 (SC-002) |
| No browser in autonomous runs → visual "beats" judgment is partially static | Med | Checker verdict + structured rubric now; human-eyeball pass recorded as an explicit carry-forward item (per project convention, visual gates never block autonomously) |
| Spike scripts rot or get mistaken for CI tests | Low | Keep them under `spikes/`, not `cast-server/tests/`; name them `spike_*.py`; pytest never collects them |

## Open Questions

- None blocking for Phase 1 execution. The single goal-level open item remains the
  **[USER-DEFERRED]** maker/checker model tier, which Phase 1 deliberately does not touch
  (hand-run generation uses the session's own model; tier choice is a later tuning knob).

## Decisions Made Autonomously (per the autonomous-run instruction)

1. **Second family doc is authored, not found:** no real `bug_fix`/`data_analysis`
   classified doc exists in the repo (all other goals' refined requirements are stubs or
   unclassified). 1a authors a `bug_fix` doc from the real `goal_card.py` markdown-leak
   defect rather than synthesizing fiction; `data_analysis` is a stretch third doc.
2. **Spike evidence location:** `docs/goal/refine-requirements-better-rendering-v3/spikes/{1a,1b}/`
   — keeps evidence with goal artifacts and away from render-class filenames and CI test
   collection.
3. **Mark-placement verification method:** a Python re-implementation of the
   `requirements_comments.js` tree-walk + `indexOf` semantics (no browser in autonomous
   runs), with a split-quote self-test and a human browser pass carried forward.
4. **"Clearly beats" operationalized as:** `cast-requirements-checker` passes the maker
   render with restatements at least as complete as the baseline's, AND the structured
   rubric favors the maker on a majority of dimensions, AND no gate regression (ids
   verbatim, self-contained, DOM contract) — plus the human-eyeball carry-forward.
5. **1b source pair:** reuse the existing v2 fixture pair
   (`refined_requirements.collab.md` + `.v2-edit.collab.md`), extended with a heavier
   moved/reworded/deleted edit if needed — real fixture over invented content.
6. **1b does not wait on 1a:** parallel per the high-level plan; 1b hand-crafts a minimal
   varying HTML pair if 1a's richer pages aren't ready.

## Suggested Revisions to Prior Sub-Phases

- **Sharpening only (no decision overturned):** the high-level plan's risk table frames 1b
  as "varying render orphans open comments on regenerate." Code grounding shows DB-level
  orphaning cannot be caused by render variation alone — all anchor validation is
  source-side, and the maker never writes the source. The real exposure is (a) silent
  `<mark>`-placement loss on paraphrased maker DOM and (b) the unspec'd
  "anchorable-text-verbatim-in-DOM" maker obligation. The seed decision (logical backbone +
  quote-anchored DOM) stands unchanged; recommend the orchestrator note this sharpened risk
  wording when Phase 3/4b are planned, and that Phase 3's `/cast-update-spec` activity
  include the verbatim-carriage clause in the maker contract.

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| `cast-requirements-render.collab.md` (Draft v2) | US7 DOM contract; FR-012/FR-013 (zero-`id`); FR-019 relocate backstop; FR-021/022 `create_next`/displaced; FR-024 `block_diff`; FR-026 folder invariant; FR-027 reanchor carve-out; FR-028 progressive enhancement; SC-001 checker gate | None — Phase 1 consumes, never modifies. One carry-forward gap flagged for Phase 3's `/update-spec` (verbatim-carriage clause) |
| `cast-goal-classification.collab.md` (Draft v1) | `WorkFamily` nine-value enum; `FAMILY_RECIPES`/`RECIPE_REALIZATION` (starting vocabulary for family-appropriate sections) | None — consumed, not modified |

---

## Plan Review Decisions (cast-plan-review, BIG CHANGE scope — autonomous)

Reviewed under HOLD scope; every fork auto-decided against the binding owner decisions in
`docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md`. **None of the
findings re-open an owner-resolved decision** (anchor backbone, background-job render,
net-new agents, family-communication page structure, gap-fill door); all sharpen gate
measurability and audit precision *within* the existing spike design. Weighting: spike design
soundness, gate measurability, constraint compliance (planning-only — no implementation
reviewed). Per the B2 single-Write contract this appendix and the inline body sharpenings
above were committed in one write.

Summary: 5 issues found / 5 resolved / 0 deferred (Architecture 2, Code Quality 1, Tests 2,
Performance 0).

- **2026-06-12T08:15:36Z — Architecture: does the "both gates green → Phase 3" edge have an owning artifact?** — Decision: No — add `spikes/PHASE1-GATE.md` aggregating both spike verdicts plus the combined go/revisit decision. Rationale: the build-order diagram implies a single combined gate but each spike only writes its own results file; one artifact makes the Phase-3 entry condition measurable and unambiguous instead of leaving a reader to reconcile two files. (Body patched: Build Order section.)
- **2026-06-12T08:15:36Z — Architecture/Delegation: should `/cast-preso-how` be delegated to in 1a, per the plan-review delegation check?** — Decision: No — record the conscious non-delegation. Rationale: cast-preso-how generates reveal.js slides and the net-new requirements agents are Phase-3-owned; hand-running only the 8-step *discipline* is correct. Documenting it prevents an execution-time misfire (invoking the slide agent, or skipping the discipline). The two actual delegations (`cast-requirements-checker`, `cast-comment-reanchor`) are already named with `→ Delegate:`. (Body patched: 1a "Hand-run the preso-how discipline" activity.)
- **2026-06-12T08:15:36Z — Code Quality: is the 1a id-audit (set-equality only) a true FR-003 check?** — Decision: No — strengthen to id-to-block correspondence. Rationale: FR-003 is per-block ("emit ids verbatim on the corresponding blocks"); set-equality passes even if a label sits on the wrong block, and Phase 3 reuses this audit as its acceptance pattern, so the ceiling proof must encode FR-003 faithfully. Hand-crafted risk is low but the gate must still be correct. (Body patched: 1a Verification + "Run the audits" activity.)
- **2026-06-12T08:15:36Z — Tests: can a generic/short quote register a false-positive mark placement?** — Decision: Yes — require the hit to land in the comment's *intended block container*, not merely `find()` ≥ 0 anywhere. Rationale: `concat.indexOf` returns the first match in the whole DOM, so a generic quote can "place" on the wrong block and pass; scoping the assertion to the intended container turns the already-seeded short/generic-quote comment into a real test and tightens the named harness-fidelity mitigation. (Body patched: 1b "Measure mark placement on v1" activity.)
- **2026-06-12T08:15:36Z — Tests: does the seeded `section_hint`-mismatch probe have a recorded expected outcome?** — Decision: No — add an explicit expected verdict to the 1b verification list. Rationale: the comment is seeded but the gate never states what success looks like for it; a seeded comment with no recorded outcome is not a measured gate. Record places-despite-rename vs degrades-to-tray as an explicit Phase-3 input. (Body patched: 1b Verification.)
- **2026-06-12T08:15:36Z — Performance: any performance findings for this phase?** — Decision: None — N/A. Rationale: planning-only, hand-run spikes over a throwaway SQLite DB (`db_path` injection) and pure `render_requirements()` calls; there are no query/caching/memory paths to review, and the background-job render-performance model is owner-resolved and out of Phase-1 scope.
