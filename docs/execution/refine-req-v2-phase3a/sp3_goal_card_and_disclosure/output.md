# sp3 Output — Goal Card + Pill + Disclosure Boundary + WHAT-before-HOW (WP-C + WP-D)

**Status:** ✅ Complete. All Detailed Steps executed, all verification run, every success
criterion met. `pytest tests/test_goal_card.py tests/test_requirements_renderer.py` = **34
passed**; the broader render-layer suite (families, parser, fr007 guard, versions,
spec-checker, theme-drift) = **160 passed**, no regressions.

## What landed

### New file — `cast_server/requirements_render/goal_card.py` (the SC-001 IA core)
Two **pure, deterministic** heuristics over `ParsedRequirements` (no I/O, no markdown render),
isolated from `renderer.py` so the 2-minute-test core is unit-testable without a full render
(plan-review #3):

- `extract_job_statement(parsed) -> tuple[str, str | None]` — Step 3.1 priority:
  1. bolded `**Job statement:**` lead inside the `Intent` block;
  2. else the Intent's first sentence;
  3. else **emit `NO_JOB_STATEMENT_WARNING`** (`"no job statement — SC-001 at risk"`) and fall
     back to the H1 title. Returns the statement + any warning so `renderer.py` threads it into
     `RenderResult.warnings` (the renderer's only lever on authoring quality).
- `derive_l2_assertions(parsed) -> list[str]` — Step 3.2 priority, concatenated and capped at
  `MAX_L2_ASSERTIONS = 5`, **never padded**: SC criterion rows (outcomes) → Out-of-Scope
  bullet leads (framed `Out of scope: …`) → only when neither exists (the `bug_fix`/
  `random_idea` shape) the Intent's enumerated/numbered thread. Fewer than 3 available ⇒
  returns what exists (a sparse card is honest).

### Modified — `cast_server/requirements_render/renderer.py`
- **Goal Card** (`_render_goal_card`, Step 3.3): now renders the full zero-click surface —
  pill (`family-pill--{value}` + `title="{reasoning}"` hover; `family-pill--unclassified`
  rescue text), version chip (omitted when `version is None`), the inert
  `<!-- open-comment-count: [PENDING Phase 4] -->` slot, the L1 job statement
  (`<p class="goal-card__job-text l1-body">`), the 3–5 L2 assertions
  (`<ul class="goal-card__assertions"> <li class="l2-body">`), and the scope-compare grid —
  all inside `<section class="goal-card">`, **outside any `<details>`**.
- **Scope compare** (`_render_scope_grid`, Step 3.4): open, side-by-side `.scope-grid` — left
  `.callout` accent = primary outcomes (SC criteria); right muted = Out-of-Scope boundaries.
  **Omitted entirely** when the (modulated) family recipe has no `SCOPE` block.
- **Disclosure boundary** (Step 3.5): only *depth* collapses, the WHAT is always open. Recipe
  sections now branch by kind:
  - `INTENT` → flowing prose, always open (pure WHAT);
  - `EVIDENCE`/`DECISION` → lead paragraph open, the rest (evidence-beyond-lead / rationale)
    in a closed `<details>`;
  - `USER_STORY` → heading + story sentence open (L2), acceptance/EARS depth collapsed (L3);
  - `FR`/`SC`/`CONSTRAINT` → the table/constraint detail collapsed under the open `<h2>`
    heading (SC *outcomes* are promoted, open, to the Goal Card);
  - `SCOPE` (Out of Scope) / `OPEN_QUESTION` → short boundary/open lists, left open.
  Every `<summary>` carries a non-empty label (the assertion heading) via the single
  `_details()` primitive — the a11y/print rule.
- **WHAT-before-HOW** (`_render_directional`, Step 3.6): Directional renders **last**, in the
  muted/italic `.question-annotation` grammar, marked
  `"Non-binding — subject to change by exploration."` **Omit-not-pad** — `""` when no
  Directional block exists; rendered when an author wrote genuine HOW.
- The family recipe is now modulated **once** in `render_requirements` and shared by the Goal
  Card (scope-grid gate) and the recipe pipeline, so they can never disagree on SCOPE
  presence. `_render_recipe_sections` signature changed accordingly (internal callers only).

### New file — `tests/test_goal_card.py` (7 tests, IA core in isolation)
`test_job_statement_prefers_bold_lead` / `…_falls_back_to_first_sentence` /
`…_warns_and_uses_title_when_absent`; `test_l2_assertions_priority_order` / `…_caps_at_5` /
`…_never_pads_when_sparse` / `…_intent_thread_fallback`.

### Modified — `tests/test_requirements_renderer.py` (8 structural additions)
`test_goal_card_outside_details`, `test_what_never_collapsed`, `test_pill_has_family_class`,
`test_pill_carries_reasoning_title`, `test_unclassified_pill_state`,
`test_scope_grid_open_or_omitted`, `test_directional_muted_last_or_omitted`,
`test_every_summary_has_text`. All 20 pre-existing sp2 behavioural tests remain green.

## Validation (temporary scripts, per plan)
Rendered three inputs to confirm the IA holds without a browser (autonomous run — no Chrome):
- **Full-spec fixture** (`tests/fixtures/refine_requirements_v2/…`): it carries **no**
  `classification` front-matter → unclassified rescue pill + GENERIC recipe (no SCOPE → no
  grid, correct). The Goal Card states the job (Intent first sentence) + SC outcomes
  zero-click; warnings include the unclassified rescue + density flags.
- **Classified `new_initiative`** doc (SC + Out of Scope): pill 🚀 + `v2` chip + bold job
  statement + 4 assertions + open `.scope-grid` (In focus | Out of scope); no `<details>` in
  the card.
- **Sparse `random_idea`** (Intent only, above stub threshold): pill 💡 + job statement, **zero
  assertions, no grid** — honest degradation, nothing invented.

## Notes / carry-forward
- **Human eyeball deferred (carry-forward):** the manual "state the WHAT in 2 minutes without
  clicking" dry-run could not run live (autonomous run can't connect Chrome). Static inspection
  of the stripped Goal Card text confirms job + outcomes + in/out scope are all zero-click. The
  authoritative SC-001 gate is sp5a's checker eval.
- **Minor redundancy (intentional, spec-faithful):** when a doc has both SC and Out-of-Scope,
  the Out-of-Scope items appear in the L2 assertions *and* in the scope grid. This follows the
  Step 3.2 priority order verbatim; not changed.
- **No spec-linked files modified** (the plan confirms none here).
- **Out of Scope recipe section stays open** (it is a scope boundary / WHAT, not "depth").
  Depth = FR/SC tables, US acceptance/EARS, constraint detail, evidence-beyond-lead, rationale.

## For dependent sub-phases
- **sp4** (serve + regenerate): `render_requirements(parsed, *, version)` and
  `RenderResult{html, warnings}` are unchanged at the public boundary; the Goal Card markup
  contract (`.goal-card`, `.goal-card__job`, `.goal-card__assertions`, `.scope-grid`,
  `.family-pill`, `.version-chip`, `.directional`) is now fully realized.
- **sp5a** (goldens + checker eval): the disclosure DOM is stable — WHAT in `.goal-card`
  (open), depth in `<details>` with non-empty `<summary>`, Directional last in
  `.question-annotation`. No element `id=`/`data-block-anchor` (thin-spine contract held).
  `goal_card.extract_job_statement`/`derive_l2_assertions` are the per-family weak-card signal
  the eval should surface.
