# sp1 — Visual Theme + Document Template (WP-A) — Output

**Status:** ✅ Complete. All success criteria met; `tests/test_theme_token_drift.py` green (6 passed); no regressions in the render package (125 parser/family tests still pass).

## What was built (the contract sp2/sp3 render into)

### 1. Package-local Jinja environment
`cast-server/cast_server/requirements_render/templating.py`
- `get_environment() -> jinja2.Environment` built on
  `PackageLoader("cast_server.requirements_render", "templates")`, `autoescape=True`,
  `trim_blocks=True`, `lstrip_blocks=True`.
- **Imports and renders without FastAPI** (verified: `fastapi` not in `sys.modules` after a render).
  Deliberately NOT reusing the app's request-bound `Jinja2Templates` from `deps.py`.

### 2. `document.html.j2` — the five-layer standalone shell
`cast-server/cast_server/requirements_render/templates/document.html.j2`
- Standalone `<!doctype html>` (does **not** extend `base.html`), inline
  `<style>{% include "_theme.css.j2" %}</style>`.
- **Stable named blocks (do not rename — sp2/sp3 fill these):**
  | Block name | Layer | Notes |
  |---|---|---|
  | `{% block title %}` | `<title>` | defaults to `document_title` var |
  | `{% block goal_card %}` | Layer 1 — Goal Card | always open, outside any `<details>` |
  | `{% block recipe_sections %}` | Layer 2 — recipe sections | ordered per family |
  | `{% block unmodeled_sections %}` | Layer 3 — unmodeled | rendered before Directional |
  | `{% block directional %}` | Layer 4 — Directional | muted, last |
- HTML comment landmarks `<!-- LAYER 1: GOAL CARD ... -->` … mark each region (order-tested).
- The **one** permitted inline `<script>`: an "expand all" toggle (`[data-expand-all]` button)
  that flips `open` on every `<details>` and relabels to "Collapse all". No framework, no `src`.
- **Thin spine honored:** emits NO element `id=` and NO `data-block-anchor` (verified).

### 3. `_theme.css.j2` — the lifted toolkit (inlined)
`cast-server/cast_server/requirements_render/templates/_theme.css.j2`
- `:root` design tokens **copied verbatim** from `static/style.css` `:root` (pin-tested byte-match).
- Lifted cast-preso classes **verbatim by name** (reveal `em`→document `rem`):
  `.slide-title`, `.l1-body`, `.l2-body`, `.source-citation`, `.callout`, `.question-annotation`,
  `.muted`. L1/L2/L3 sized by **importance**: `--rr-l1-size: 1.35rem` (600 wt) deliberately
  out-weighs `--rr-l2-size: 1.05rem` (400 wt, muted) — L2 never out-weighs L1.
- **Family pill idiom** cloned from `.phase-badge`: `.family-pill` base + one
  `.family-pill--<value>` per `WorkFamily` (all 9 values), plus the distinct dashed-border
  **`.family-pill--unclassified`** rescue state for sp2/sp3's "Unclassified — re-run refinement".
  Tints use `rgba()` literals (the `.phase-badge` precedent), so FR-012's hex ban holds.
- `<details>/<summary>` styling: closed-by-default, `▸`→rotate affordance, hover→accent,
  marker hidden.
- `.scope-grid` two-column side-by-side scope layout (renders open; collapses to 1-col < 640px).
- `.goal-card`, `.version-chip` (for the `v{n}` chip), `.recipe-section`, `.directional`,
  `.rr-controls .expand-all-btn` scaffolding.
- `@media print { details > * { display: block } }` force-opens disclosure on paper; also hides
  controls and drops the grid background.

### 4. Tests (permanent) — `cast-server/tests/test_theme_token_drift.py`
- `test_theme_tokens_match_style_css` — **the anti-drift invariant** (replaces Playbook 05's
  "single copy"): every `:root` token in `static/style.css` is preserved with an identical value
  in the rendered theme. Edit a token in `style.css` → this goes red until the theme matches.
- `test_no_hardcoded_hex_outside_root` — FR-012: strips every `:root { … }` block, asserts no
  `#hex` literal remains in the emitted shell.
- `test_shell_is_self_contained` — doctype + inline `<style>`, no `<link rel=stylesheet>`, no
  external `<script src>`.
- `test_shell_has_four_body_regions_in_order` — smoke render asserts the four layers appear in
  fixed order + exactly one inline script.
- `test_lifted_class_names_present_verbatim`, `test_print_forces_details_open`.

## Conventions / decisions for downstream sub-phases
- **Render-local tokens** (`--color-on-accent`, `--rr-content-max`, `--rr-l1/2/3-size`) live in a
  **second `:root` block** in the theme. The drift test only asserts style.css⊆theme, so these
  extras are allowed; defining them on `:root` keeps the hex-scan happy (`#FFFFFF` is inside `:root`).
- The theme is static CSS in a `.j2` file (no Jinja logic, no timestamps) — determinism for goldens.
- sp2 should `extend "document.html.j2"` (or render it with the blocks filled) and rely on the
  block names above; the comment landmarks are stable too.

## Deferred / carry-forward
- The temporary visual eyeball (Validation Scripts) was substituted with structural assertions
  (autonomous run — no browser for visual gates). **Human-eyeball carry-forward:** open a real
  render in a browser once sp3 produces content to confirm L1 > L2 > L3 reads and pill tints land.
