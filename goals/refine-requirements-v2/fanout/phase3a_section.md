## Phase 3a: Comprehension — HTML-First Render (parallel with Phase 3b)
**Outcome:** Refinement emits a well-designed, read-only HTML render as the primary human-consumption
artifact: an above-the-fold **Goal Card** (pill + one-sentence job statement + 3-5 outcome/scope
assertions, all WHAT, zero clicks), L1/L2/L3 visual hierarchy, progressive disclosure of depth, HOW
quarantined to a bottom "Directional" section, and per-family structural variation. **This is the
headline thread and the goal's only measurable headline criterion (SC-001).**
**Dependencies:** Phase 1 (parser/block model) + Phase 2 (taxonomy + block recipes).
**Estimated effort:** 3-5 sessions
**Verification (v2):** **A `cast-requirements-checker` agent is the SC-001 gate** (owner decision at
plan review). The agent opens the HTML render as an *unfamiliar reader* and, from the Goal Card +
headings alone, restates the job, primary outcome, and in/out scope — failing the render if it can't.
It reuses cast-preso's `one-clear-takeaway` + `l1-l2-hierarchy` rubric and runs in CI per family, with
one golden HTML snapshot per family. The **human timed-read with outside readers is deferred** for v2
(addable later as a confirmation increment).

Key sub-deliverable — **build the `cast-requirements-checker` agent**: a checker agent in the
`cast-spec-checker` / `cast-preso-check-*` lineage that takes a rendered requirements HTML and returns
a structured verdict `{can_state_what: bool, restated_job, missing[], score}`. It is reusable beyond
CI: a human (or another agent) can run it on demand to sanity-check any goal's render, and it doubles
as the FR-013 "agent-as-consumer" demonstration.

Key activities:
- **Build the block-recipe render engine** (`family → ordered blocks → HTML`) as a thin Jinja engine,
  data-driven off Phase 2's `FAMILY_RECIPES` so adding a family is a config change. Each block has
  **one** canonical visual treatment (consulting-exhibit shape: assertion heading → bold-lead bullets
  → source line). Include a generic fallback recipe and a **stub → prompt-to-begin** render.
- **Lift the cast-preso visual toolkit nearly verbatim** (`theme.css` tokens are already byte-identical
  to `style.css` `:root`): `.slide-title / .l1-body / .l2-body / .source-citation / .callout /
  .question-annotation`. **Hard rule: never hardcode hex — always `var(--color-*)`** (one-line rebrand
  = FR-012 win). Assign **level by importance** (L1 = survives a 90% cut = job statement; L2 = survives
  50% = outcomes/scope; L3 = acceptance detail/EARS/rationale).
- **Render the Goal Card + classification pill** as the entire SC-001 surface, always open, zero
  clicks. Scope renders **open, side-by-side** (in vs out is a comparison, never collapsed).
- **Wire the progressive-disclosure boundary:** only *depth* (acceptance scenarios, EARS, symptom/repro,
  constraints, rationale) wraps in `<details>` closed-by-default; **the WHAT is never collapsed**.
  `@media print` forces all open; add an "expand all" for deep review.
- **WHAT-before-HOW (FR-001):** HOW confined to a muted/italic "Directional ideas" section, **omitted
  entirely** when the family makes HOW irrelevant (e.g. data-analysis) — never padded.
- **Serve + regenerate:** clone the `/preso/review/{goal_slug}` serving precedent → `GET
  /goals/{slug}/render`; add `_rerender_requirements_html()` mirroring `_rerender_tasks_md()` with the
  `<!-- AUTO-GENERATED -->` header. Markdown stays the edit + agent source; HTML is generated read-only.
- **Selectable DOM for Phase 4:** render each block as a clean, text-selectable unit so the vanilla-JS
  comment layer can capture the reviewer's selection (the **quote**) and nearest section heading (the
  **hint**) — there is **no** `data-block-anchor`/`id="fr-007"` to emit (the thin-spine decision deleted
  stored anchors; placement is re-derived by a subagent from the stored quote). **Illustrations: none
  in v2** (resolved — decorative SVG fails the cast-preso visual checker and slows the scan).

