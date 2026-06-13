# sp2 — Block-Recipe Render Engine (WP-B) — Output

**Status:** ✅ Complete. All success criteria met. `pytest tests/test_requirements_renderer.py`
green (20 passed); full render-package suite green (154 passed, no regressions).

## What was built (the contract sp3/sp4 consume)

### 1. `render_requirements()` — the pure pipeline
`cast-server/cast_server/requirements_render/renderer.py`
- `render_requirements(parsed: ParsedRequirements, *, version: int | None = None) -> RenderResult`
  where `RenderResult` is a **frozen** dataclass `{html: str, warnings: tuple[str, ...]}`.
- **Pure & deterministic:** no I/O, no DB, no timestamps. Templates load via the sp1
  package Jinja env (`get_environment()`); the only thing the renderer reads is its own
  package templates. Byte-stable output (`test_render_is_deterministic`).
- Pipeline: read persisted `classification` (read-only; **never re-classifies**) →
  resolve `FAMILY_RECIPES[family]` → `modulate(...)` for `irreversible`/`unknown_cause`
  modifiers → for each `RecipeBlock`, pull parser blocks per `RECIPE_REALIZATION`
  (skipping empties — never pads) → render each section → compose into the sp1
  `document.html.j2` shell.

### 2. Rendering behaviours (all tested)
- **Stub gate (Step 2.2):** `is_stub(parsed)` short-circuits to a **prompt-to-begin card**
  (names what exists + "Refine this goal to build it out") and returns — never an empty
  skeleton. Emits a stub warning. No recipe sections rendered.
- **Classification rescue (Step 2.1/2.4):** absent OR unparseable (`family` coerced, or
  `classification` not a dict) ⇒ `GENERIC` recipe + the distinct **`family-pill--unclassified`**
  pill ("Unclassified — re-run refinement to classify") + a warning. Never crashes.
- **One canonical treatment (Step 2.3):** assertion `<h2 class="slide-title">` heading →
  prose (whole-section blocks: Intent/Evidence/Decisions/Directional) or bold-lead `<li>`
  bullets (US/FR/SC/Constraints/Scope/Open Questions). Contiguous text under real headings.
- **Never drop unrecognized (Step 2.5):** each `unrecognized_sections` entry is rendered
  **verbatim** (body re-derived from `source_text` by reusing the Phase 1 parser's own
  `_section_spans` grammar — no drift) inside an L3 `<details>` "Unmodeled section: {name}",
  plus a warning naming it. Zero silent drops.
- **Density warnings + determinism (Step 2.6):** warnings (not failures) for >50 words/block,
  >15 words/bullet, >6 elements/unit. No timestamps; `source-hash` is left to the service (sp4).
- **Thin spine:** zero `id=`, zero `data-block-anchor` on rendered blocks
  (`test_no_ids_or_anchors`). markdown extensions are minimal (`sane_lists` only) so no
  `footnotes`/`attr_list` `id=` injection is possible — id-free **by construction**.
- **One reused `markdown.Markdown()`** (plan-review #5): module-level `_MD`, `.reset()` between
  sections via `_md_to_html`. Guarded by `test_markdown_instance_reused` (spies on `_MD.reset`/
  `_MD.convert` and fails if a new `markdown.Markdown` instance is built mid-render).

### 3. Template wiring
`cast-server/cast_server/requirements_render/templates/document.html.j2` (modified)
- The four sp1 named blocks now emit pre-built HTML fragments: `goal_card_html`,
  `recipe_sections_html`, `unmodeled_html`, `directional_html` (each `| safe`, guarded by
  `{% if %}`). The block names and LAYER comment landmarks are **unchanged** — sp3 may still
  override the blocks via template inheritance or keep passing fragments.
- The **Goal Card here is a placeholder** (pill + title + version chip + an empty
  `.goal-card__job` slot). sp3 (`goal_card.py` + WP-D) fills the job statement and the L2
  assertions; the slot/markup contract is stable.

### 4. Tests (permanent)
`cast-server/tests/test_requirements_renderer.py` — 20 behavioural tests:
recipe-order-per-family (parametrized over all 9 `WorkFamily`), stub→prompt-to-begin,
missing/garbage/non-dict classification rescue, unrecognized-rendered-and-warned,
determinism, markdown-instance-reuse, density warnings, no-ids/anchors, frozen result,
version chip. **Inputs are built programmatically** (see precondition note below).

## ⚠️ Preconditions I had to land / work around

Phases 1/2 landed the `requirements_render` package, but **two declared preconditions were
missing**. Handled autonomously per the plan's "adopt the landed names / don't fork" guidance:

1. **`is_stub` + `STUB_WORD_THRESHOLD` did not exist anywhere.** The shared context names the
   Phase 1 parser package as their canonical home (plan-review #1), and sp2's plan forbids
   redefining them *locally in the renderer*. I landed them in their canonical home —
   **new file `cast-server/cast_server/requirements_render/stub.py`** (`STUB_WORD_THRESHOLD = 200`;
   `is_stub(parsed)` = visible-content word count < threshold over preamble + block bodies +
   unrecognized-section names) — and exported them from the package `__init__`. The renderer
   *imports* it; it is **not** redefined in `renderer.py`. **If Phase 1 later lands its own
   `is_stub`, reconcile to one definition** (this one is import-light and pure).
2. **`tests/fixtures/family_docs/` (Phase 2 WP-D) does not exist.** sp2's recipe-order test was
   specced to iterate that fixture set. To avoid blocking on an unlanded Phase 2 deliverable —
   and to avoid forging Phase 2's authored fixtures — the behavioural tests **build a recognized-
   section document per family programmatically** (classification front matter + every realized
   H2). **sp5a still needs the real `family_docs/` fixtures** for its per-family golden snapshots.

`BlockKind.EVIDENCE` + `BlockKind.DECISION` (the Execution-Notes stop condition) **are present** —
no workaround needed there.

## Determinism / verification evidence
- `pytest tests/test_requirements_renderer.py` → 20 passed.
- Full render-package suite (`test_families`, `test_requirements_parser`,
  `test_theme_token_drift`, `test_fr007_readonly_guard`, this file) → 154 passed.
- Validation script (full-spec fixture, which has **no** classification ⇒ unclassified):
  warnings = `unclassified`, Intent density, 6× Open-Questions bullet density, Directional
  density. Rendered to `/tmp/spec.html` (18,589 bytes): no timestamps, no `id=` in `<main>`.

## For downstream sub-phases
- **sp3 (Goal Card + WP-D):** fill `_render_goal_card`'s placeholder — the job statement +
  L2 assertions belong in `goal_card.py` (keep `renderer.py` a thin pipeline, plan-review #3).
  The Directional slot currently gets a minimal `<aside class="directional">` render; sp3 owns
  the muted HOW-quarantine grammar.
- **sp4 (service/route):** `render_requirements()` does no I/O. The service adds the
  `<!-- AUTO-GENERATED -->` + `<!-- source-hash: … -->` header (the renderer emits neither).
- **sp5a (goldens/checker):** extend `test_requirements_renderer.py` with golden byte-compares
  + the structural battery; author the missing `tests/fixtures/family_docs/` set first.

## Files created/modified
| File | Action |
|---|---|
| `cast-server/cast_server/requirements_render/renderer.py` | **Create** — the engine |
| `cast-server/cast_server/requirements_render/stub.py` | **Create** — landed missing precondition (`is_stub`/`STUB_WORD_THRESHOLD`) |
| `cast-server/cast_server/requirements_render/__init__.py` | Modify — export `is_stub`/`STUB_WORD_THRESHOLD` |
| `cast-server/cast_server/requirements_render/templates/document.html.j2` | Modify — wire the four fragment slots |
| `cast-server/tests/test_requirements_renderer.py` | **Create** — 20 behavioural tests |
