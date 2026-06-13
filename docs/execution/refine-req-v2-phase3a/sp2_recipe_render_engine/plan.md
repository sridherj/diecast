# Sub-phase 2: Block-Recipe Render Engine (the net-new build) — WP-B

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase3a/_shared_context.md` before starting.

## Objective
Build `render_requirements()` — the pure block-recipe pipeline that turns a `ParsedRequirements`
into a `RenderResult{html, warnings}` by reading the persisted classification, resolving the family
recipe, pulling parser blocks per `RECIPE_REALIZATION`, and rendering each section into the sp1
shell. This is the entire net-new build of Phase 3a. It also lands the stub→prompt-to-begin rescue,
the never-drop-unrecognized-sections rule, density warnings, and strict determinism.

## Dependencies
- **Requires completed:** sp1 (the `document.html.j2` shell + `_theme.css.j2` + package Jinja env).
- **Assumed codebase state:** Phase 1 `ParsedRequirements/Block/BlockKind`, `is_stub` +
  `STUB_WORD_THRESHOLD`, `content_hash`; Phase 2 `WorkFamily/FAMILY_RECIPES/RecipeBlock/
  RECIPE_REALIZATION/FAMILY_PILL_LABELS/modulate()/validate_classification()`. **`BlockKind` must
  include `EVIDENCE` + `DECISION`** (Phase 2 Suggested Revision #1) — verify before starting.

## Scope
**In scope:**
- `requirements_render/renderer.py`: `render_requirements(parsed, *, version=None) -> RenderResult`
  (frozen `RenderResult{html: str, warnings: tuple[str, ...]}`), the recipe→ordered-sections→HTML
  pipeline; **never re-classifies**.
- The `GENERIC`-recipe + "Unclassified" rescue for absent/unparseable classification (+ warning).
- The stub→prompt-to-begin card (imports `is_stub` from Phase 1; never an empty skeleton).
- Per-section markdown→inline-HTML conversion via **one** reused `markdown.Markdown()` instance
  with `.reset()` between sections (plan-review #5).
- `unrecognized_sections` rendered verbatim (per-section) inside an L3 `<details>` "unmodeled
  section", each emitting a warning — zero silent drops.
- Density warnings (not failures); strict determinism (no timestamps; only `source-hash` varies).

**Out of scope (do NOT do these):**
- The Goal Card extraction heuristics (`extract_job_statement`, `derive_l2_assertions`) and the
  scope grid / disclosure-WHAT/HOW grammar — those are **sp3** (`goal_card.py` + WP-D). sp2 may
  render a *placeholder* Goal Card slot; sp3 fills it.
- The service / route / file I/O — that is sp4. `render_requirements()` does **no** I/O or DB.
- Golden snapshot byte-compares + the checker + eval harness — that is sp5a (sp2 writes
  behavioural/pipeline tests only).
- Re-defining `is_stub` / `STUB_WORD_THRESHOLD` locally (import from Phase 1 — plan-review #1).
- Emitting any `id=` / `data-block-anchor` (forbidden).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/requirements_render/renderer.py` | Create | Does not exist |
| `cast-server/cast_server/requirements_render/templates/document.html.j2` | Modify | Created in sp1 — wire recipe-section + unmodeled + Directional slots |
| `cast-server/tests/test_requirements_renderer.py` | Create | Pipeline/behaviour tests (sp5a extends with goldens + structural battery) |

## Detailed Steps

### Step 2.1: `RenderResult` + pipeline skeleton
Define `RenderResult` as a frozen dataclass `{html: str, warnings: tuple[str, ...]}`. Implement
`render_requirements(parsed, *, version=None)`:
1. `raw = parsed.front_matter.get("classification")`.
2. `classification = validate_classification(raw)` (Phase 2; **never crash**). If absent/unparseable
   → `family = GENERIC`, set the "unclassified" flag, append a render warning
   `"unclassified — re-run refinement to classify"`.
3. `recipe = modulate(FAMILY_RECIPES[family], **modifiers)`.
4. For each `RecipeBlock` in `recipe` order: pull matching parser blocks via `RECIPE_REALIZATION`,
   render that section (one canonical treatment — see 2.3). Skip a recipe block with no realized
   content (do not pad).
5. Render `unrecognized_sections` (Step 2.5), then the Directional slot is left for sp3/WP-D (sp2
   wires the slot but the muted-grammar treatment is sp3).
6. Compose into the sp1 shell via the package Jinja env; return `RenderResult`.

### Step 2.2: Stub → prompt-to-begin
At the top of the pipeline, if `is_stub(parsed)` (imported from the Phase 1 parser package): render a
**prompt-to-begin card** (what exists + "refine to build this out") and return — never an empty
skeleton (Template-Enforcer guard at the render layer). Append a warning naming the stub state. Do
NOT re-implement the threshold.

### Step 2.3: One canonical visual treatment per block
Consulting-exhibit shape per section: assertion heading → bold-lead bullets → `.source-citation`
line. Convert block bodies markdown→inline HTML with **one** module-level configured
`markdown.Markdown()` instance, calling `.reset()` between sections (plan-review #5) — never
module-level `markdown.markdown()` per block, and never a whole-document `md.markdown()` dump (the
structure-blind path this phase replaces). Every block renders as one semantic `<section>`/`<li>`
with **contiguous** text under a real heading (`<h2>`/`<h3>`) — the Phase 4 DOM contract. **No
`id=`, no `data-block-anchor`.**

### Step 2.4: GENERIC / unclassified rescue
Absent or unparseable `classification` ⇒ `GENERIC` recipe + the **"Unclassified — re-run refinement
to classify"** pill state (visually distinct from a model-selected `generic`, using
`.family-pill--unclassified` from sp1) + a `RenderResult.warnings` entry. The render NEVER
re-classifies.

### Step 2.5: Never drop `unrecognized_sections`
Render each `unrecognized_sections` entry verbatim (its own `md` conversion) at the bottom, before
Directional, inside an L3 `<details>` labelled "unmodeled section", and append a warning naming it.
Zero silent drops.

### Step 2.6: Density warnings + determinism
Emit `RenderResult.warnings` entries (not failures) for: >50 words/block, >15 words/bullet,
>6 elements/unit. **Determinism:** no timestamps anywhere; the only run-varying value is the
`source-hash` comment (a pure function of input) — and even that is emitted by the service (sp4),
not the renderer. Goldens (sp5a) depend on byte-stable output.

## Verification

### Automated Tests (permanent) — `cast-server/tests/test_requirements_renderer.py`
(sp2 creates this file with behavioural tests; sp5a extends it with golden byte-compares + the full
structural battery + rescue goldens.)
- `test_renders_each_family_in_recipe_order`: for each `tests/fixtures/family_docs/` fixture, the
  rendered sections appear in `FAMILY_RECIPES[family]` order; the family pill carries
  `family-pill--{value}`.
- `test_stub_renders_prompt_to_begin`: a stub doc ⇒ prompt-to-begin card (not an empty skeleton) +
  a warning; assert no recipe sections rendered.
- `test_missing_classification_falls_back_generic`: absent `classification` ⇒ `GENERIC` recipe +
  `family-pill--unclassified` + a `RenderResult.warnings` entry.
- `test_garbage_classification_falls_back_generic`: unparseable classification ⇒ same as above
  (never crashes).
- `test_unrecognized_sections_rendered_and_warned`: a doc with an unmodeled section ⇒ section present
  inside a `<details>` "unmodeled section" + a warning naming it; zero silent drops.
- `test_render_is_deterministic`: two renders of the same input produce byte-identical HTML (no
  timestamps).
- `test_markdown_instance_reused`: assert a single `markdown.Markdown()` instance is used with
  `.reset()` (e.g. via a spy/patch on the module-level instance) — guards the perf decision.
- `test_no_ids_or_anchors`: emitted HTML contains zero `id=` and zero `data-block-anchor` on
  requirement sections.

### Validation Scripts (temporary)
- `cd cast-server && python -c "from cast_server.requirements_render.renderer import render_requirements; from cast_server.requirements_render.parser import parse_requirements_file; print(render_requirements(parse_requirements_file('tests/fixtures/refine_requirements_v2/refined_requirements.collab.md')).warnings)"`.

### Manual Checks
- Render the frozen full-spec fixture to `/tmp/spec.html`, open it: sections in recipe order, no
  timestamps, HOW not yet styled (that is sp3).

### Success Criteria
- [ ] `render_requirements(parsed, *, version=None) -> RenderResult` is pure (no I/O/DB), deterministic.
- [ ] Each family fixture renders sections in recipe order with the correct pill class.
- [ ] Stub ⇒ prompt-to-begin (+warning); absent/garbage classification ⇒ GENERIC + unclassified pill
      (+warning); never crashes.
- [ ] `unrecognized_sections` rendered + warned (zero silent drops).
- [ ] One reused `markdown.Markdown()` with `.reset()`; density warnings emitted; no timestamps.
- [ ] Zero `id=` / `data-block-anchor`; contiguous text under real headings.
- [ ] `cd cast-server && pytest tests/test_requirements_renderer.py` passes.

## Execution Notes
- If `BlockKind.EVIDENCE`/`DECISION` are missing, **stop** — `bug_fix`/`pilot_poc` recipe sections
  will silently fall into `unrecognized_sections`. That is the Phase 2 Suggested Revision #1
  precondition; flag it rather than work around it.
- The Goal Card slot rendered here is a placeholder; sp3 replaces its contents. Keep the slot name
  stable.
- Keep `renderer.py` a thin pipeline — resist inlining IA heuristics; they belong in `goal_card.py`
  (sp3) by plan-review #3.

**Spec-linked files:** none modified here are spec-linked.
