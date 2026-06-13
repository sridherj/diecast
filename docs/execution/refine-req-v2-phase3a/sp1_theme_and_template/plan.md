# Sub-phase 1: Visual Theme + Document Template (the lifted toolkit) — WP-A

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase3a/_shared_context.md` before starting.

## Objective
Build the self-contained HTML5 document shell that every later sub-phase renders into: a standalone
`document.html.j2` template plus an inline `_theme.css.j2` partial that lifts the cast-preso visual
toolkit (tokens + typography classes) **verbatim** and adds `<details>` styling, the family-pill
tint idiom, the side-by-side scope grid, and print rules. This is the visual foundation — no content
logic yet. It is built first because B/C/D render *into* this shell.

## Dependencies
- **Requires completed:** External preconditions only (Phase 1 parser package exists — the template
  is parameterized but does not yet require live parser output). See `_shared_context.md` →
  "External Preconditions".
- **Assumed codebase state:** `cast_server/requirements_render/` package exists (Phase 1). This
  sub-phase **creates** the `templates/` subdir and the package-local Jinja `Environment`.

## Scope
**In scope:**
- `requirements_render/templates/document.html.j2` — standalone HTML5 doc (NOT extending the app's
  `base.html`): title, inline `<style>` from `_theme.css.j2`, the five-layer body skeleton
  (Goal Card → recipe sections → unmodeled sections → Directional), and the ONE allowed inline
  "expand all" script (toggles `open` on all `<details>`; no framework, no library).
- `requirements_render/templates/_theme.css.j2` — the lifted token + typography CSS.
- The package-local `jinja2.Environment(PackageLoader(...), autoescape=True)` wiring (so the package
  renders without FastAPI).
- The token-drift pin test + the hex-literal scan test (verification below).

**Out of scope (do NOT do these):**
- Any content/recipe logic, Goal Card extraction, or `render_requirements()` body — that is sp2/sp3.
- Editing `static/style.css` or the app's `base.html` (the artifact is **self-contained** — inline
  only; documented deviation from Playbook 05 Step 2).
- Emitting any element `id=` or `data-block-anchor` (thin spine — forbidden everywhere).
- Adding illustrations (HOLD SCOPE: none in v2).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/requirements_render/templates/document.html.j2` | Create | Does not exist |
| `cast-server/cast_server/requirements_render/templates/_theme.css.j2` | Create | Does not exist |
| `cast-server/cast_server/requirements_render/templating.py` (or `_env.py`) | Create | Package-local Jinja `Environment` factory |
| `cast-server/tests/test_theme_token_drift.py` | Create | Token-drift pin + hex-literal scan |

## Detailed Steps

### Step 1.1: Package-local Jinja environment
Create a small module (e.g. `requirements_render/templating.py`) exposing a single
`get_environment() -> jinja2.Environment` built with
`PackageLoader("cast_server.requirements_render", "templates")` and `autoescape=True`. Keep it
importable without FastAPI — the app's `Jinja2Templates` in `deps.py` stays request-bound and is NOT
reused here (deliberate, documented in the module docstring).

### Step 1.2: `_theme.css.j2` — lift the toolkit verbatim
- Copy the `:root` tokens. They are already byte-identical between `static/style.css` (`:root`,
  ≈ lines 2–48) and the preso toolkit `theme.css` (≈ 12–31). Copy them into a `:root { ... }` block.
- Lift `.slide-title / .l1-body / .l2-body / .source-citation / .callout / .question-annotation`
  from `skills/claude-code/cast-preso-visual-toolkit/base-template/theme.css` (≈ 100–192),
  **keeping the class names verbatim** (the checker rubric language transfers directly). Adapt
  reveal.js `em`-scaling → document `rem`-scaling.
- Add `<details>/<summary>` styling (closed-by-default affordance, hover cue, discernible summary).
- Add the `.family-pill` + `.family-pill--{value}` tint idiom by cloning `.phase-badge`
  (`static/style.css` ≈ 1979–1992). Include a visually distinct `.family-pill--unclassified` state
  (used by sp2/sp3 for the "Unclassified — re-run refinement" rescue).
- Add the side-by-side scope grid (a two-column layout; renders open, never collapsed).
- Add `@media print { details > * { display: block } }` to force-open on print.
- **HARD RULE (FR-012):** never hardcode a hex colour outside the `:root` token block — always
  `var(--color-*)`. (Enforced by the test in Step 1.5.)
- L1/L2/L3 are assigned by **importance, not heading depth**: L1 = survives a 90% cut
  (`.l1-body`/`.slide-title`); L2 = survives a 50% cut (`.l2-body` + `.callout` accent for decided
  WHAT); L3 = detail inside `<details>`; `.question-annotation` muted/italic = tentative HOW;
  `.source-citation` = provenance. **L2 must never visually out-weigh L1** — set sizes accordingly.

### Step 1.3: `document.html.j2` — five-layer skeleton
A standalone `<!doctype html>` document with `<style>{{ theme_css }}</style>` (or
`{% include "_theme.css.j2" %}`) in the head. Body skeleton, in order, with named template
blocks/slots that sp2/sp3 fill:
1. **Goal Card** slot (always open, outside any `<details>`).
2. **Recipe sections** slot (ordered per family).
3. **Unmodeled sections** slot (rendered before Directional).
4. **Directional** slot (muted, last).
Plus the single inline "expand all" `<script>` that sets `open` on every `<details>` (the only
inline JS permitted). Keep slot names stable — sp2/sp3 depend on them.

### Step 1.4: Smoke-render the empty shell
Render `document.html.j2` with empty/placeholder slot values through `get_environment()` and assert
it produces a valid standalone document (has `<!doctype html>`, a `<style>` block, the four body
regions in order). This proves the env + template wire up before any content logic exists.

### Step 1.5: Tests — token-drift pin + hex scan
See Verification.

## Verification

### Automated Tests (permanent) — `cast-server/tests/test_theme_token_drift.py`
- `test_theme_tokens_match_style_css`: parse the `:root { ... }` token block from the rendered
  `_theme.css.j2` output and assert each token name/value **equals** the corresponding `:root` value
  in `cast-server/cast_server/static/style.css`. This makes the byte-identical premise a CI
  invariant (replaces Playbook 05's "single copy" property).
- `test_no_hardcoded_hex_outside_root`: render the document shell; scan the emitted HTML/CSS for hex
  colour literals (`#[0-9a-fA-F]{3,8}`) occurring **outside** the `:root` token definition block;
  assert none (FR-012). A one-line OSS rebrand must stay a one-line `:root` override.
- `test_shell_is_self_contained`: rendered output contains `<!doctype html>`, an inline `<style>`,
  and **no** `<link rel="stylesheet">` or external `<script src=...>` (self-contained artifact).

### Validation Scripts (temporary)
- Render the shell to `/tmp/shell.html` and open it; eyeball that typography hierarchy reads (L1 >
  L2 > L3) and the pill tints render. Delete after.

### Manual Checks
- `cd cast-server && python -c "from cast_server.requirements_render.templating import get_environment; print(get_environment().get_template('document.html.j2'))"` — template loads.

### Success Criteria
- [ ] `document.html.j2` + `_theme.css.j2` exist and render a valid standalone HTML5 document.
- [ ] Package-local Jinja `Environment` imports and renders **without** importing FastAPI.
- [ ] `:root` tokens in `_theme.css.j2` byte-match `static/style.css` `:root` (pin test green).
- [ ] No hex literal outside `:root` (scan test green).
- [ ] Lifted class names (`.slide-title/.l1-body/.l2-body/.source-citation/.callout/.question-annotation`)
      preserved verbatim; `.family-pill--{value}` + `.family-pill--unclassified` present.
- [ ] `@media print` forces `<details>` open; one inline "expand all" script present; no external
      assets.
- [ ] `cd cast-server && pytest tests/test_theme_token_drift.py` passes.

## Execution Notes
- The token-drift test is the load-bearing safety net for the inlining deviation — write it
  *with* the CSS, not after.
- Confirm the exact `static/style.css` `:root` line range and the preso `theme.css` class range at
  build time (they may have shifted); the line numbers above are guides, not guarantees.
- Keep `_theme.css.j2` free of Jinja logic where possible — it is mostly static CSS; the `.j2`
  suffix exists so tokens *could* be templated, but determinism (no timestamps) is mandatory.

**Spec-linked files:** none in this sub-phase modify spec-linked files. (`static/style.css` is not
edited here.)
