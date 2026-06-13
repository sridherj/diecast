# Sub-phase 4a: Diff-view wiring (route + `/changes` + version toggle + diff CSS)

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase4/_shared_context.md` before starting.

## Objective

Wire the pure `block_diff`/`diff_render` engine (sp2) into the live app: the
`GET /goals/{slug}/render/diff` page, the negotiated `GET …/requirements/changes` endpoint (FR-017's
same-door surface), and the version toggle on the render page. This is the "wiring half" of WP-B,
split out so it can serialize correctly after sp3 (it shares `api_requirements.py` and the template
with sp1/sp3/sp5). **Runs parallel with sp4b** (file-disjoint).

## Dependencies

- **Requires completed:** sp2 (`block_diff`, `diff_render`), sp3 (`requirement_version_service`
  with versions in the DB; `api_requirements.py` extended with `/versions`).
- **Assumed codebase state:** `render_diff(old, new, *, base_version, head_version)` works over two
  `ParsedRequirements`; `get_version(slug, n)` returns snapshot content;
  `summarize(diff_blocks(...))` returns the panel JSON; the render route + `document.html.j2` exist.

## Scope

**In scope:**
- `GET /goals/{slug}/render/diff?base=N&head=M` in `cast_server/routes/pages.py`.
- `GET …/requirements/changes?base=N&head=M` in `cast_server/routes/api_requirements.py` (negotiated).
- Version toggle in `requirements_render/templates/document.html.j2` (link to the diff page; renders
  only when ≥2 versions exist).
- Diff goldens + `tests/test_diff_render.py`.
- (If not already added in sp2) the diff-class CSS in `_theme.css.j2`.

**Out of scope (do NOT do these):**
- The comment layer's script tags / tray container / Goal Card fill / `data-goal-slug` — **sp5**
  (it edits `document.html.j2` AFTER this sub-phase; coordinate so the toggle lands first).
- Any commenting on the diff view — it is comment-free and read-only (HOLD SCOPE).
- Re-deriving the diff inside the route — call `diff_render`/`summarize`, never reimplement.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast_server/routes/pages.py` | Modify | Has `GET /goals/{slug}/render` |
| `cast_server/routes/api_requirements.py` | Modify | sp1/sp3 endpoints present |
| `cast_server/requirements_render/templates/document.html.j2` | Modify | Phase 3a doc; has version chip |
| `cast_server/requirements_render/templates/_theme.css.j2` | Modify (if sp2 deferred diff CSS) | diff classes |
| `tests/golden/requirements_render/diff_v1_v2.html` | Create | Does not exist |
| `tests/test_diff_render.py` | Create | Does not exist |

## Detailed Steps

### Step 4a.1: `GET /goals/{slug}/render/diff` (pages.py)
- Validate slug → 404 (the path-traversal rule).
- Params: `base` / `head` default to `head = current version`, `base = head − 1`.
- **< 2 versions** → 200 with a plain "no prior version to compare" card (never an error).
- `base >= head` → **422**.
- Else `render_diff(parse(get_version(base).content), parse(get_version(head).content),
  base_version=base, head_version=head)`; serve the HTML **fresh each request** (derived, never
  written to the goal folder — only the canonical render is a file artifact).
- Unparseable archived snapshot (pre-parser content) → "cannot diff this pair" card + warning,
  never a 500 (sp2's `diff_render` already guards the parse; surface its marker here).

### Step 4a.2: `GET …/requirements/changes` (api_requirements.py)
- Negotiated (copy the sp1 pattern): `summarize(diff_blocks(old, new))` JSON | "What changed" panel
  fragment. Default `head = current`, `base = head − 1`. Slug → 404; `base >= head` → 422.
- This is FR-017's same-door surface — agents read the change set exactly as the panel renders it.
- Panel fragment: `cast_server/templates/fragments/requirements_comments/changes_panel.html` (or a
  `requirements_render` panel fragment — keep it beside the other negotiated fragments). It renders
  `+N added · ~N modified · −N removed` and links to the transient `diff-{n}` anchors in the diff
  page.

### Step 4a.3: Version toggle (document.html.j2)
- Beside the Goal Card version chip, add: `Current (vN)` / `Changes since v(N−1)`.
- The diff option renders **only when ≥2 versions exist** — a plain link to
  `/goals/{slug}/render/diff` (no swap machinery on a standalone document; keep the page simple).
- **Coordinate with sp5:** sp5 adds the script tags, tray, and `data-goal-slug` to the same
  template AFTER this sub-phase. Add ONLY the toggle here. Regenerate goldens once
  (`UPDATE_GOLDENS=1`); sp5 will regenerate again after its additions.

### Step 4a.4: Diff goldens
- `tests/golden/requirements_render/diff_v1_v2.html` from the sp2 fixture pair
  (`refined_requirements.collab.md` vs `refined_requirements.v2-edit.collab.md`). Regen via
  `UPDATE_GOLDENS=1 pytest tests/test_diff_render.py`.

## Verification

### Automated Tests (permanent)

**`tests/test_diff_render.py`:**
- Tracked-changes golden for the fixture pair (`diff_v1_v2.html`).
- Structural assertions: every `added` block carries `diff-added`; `modified` shows the new body +
  `<del>` prior; `removed` renders struck in old-section position.
- Panel counts == `summarize()` counts.
- Panel items link to transient `id="diff-{n}"` anchors that **exist** in the emitted HTML.
- Route tests (TestClient): `< 2 versions` → "no prior version" card (200); `base >= head` → 422;
  unknown slug → 404; a valid pair → 200 with the panel + tracked changes.
- `GET …/changes` negotiation: header-less → `summarize()` JSON; `HX-Request` → panel fragment.

### Validation Scripts (temporary)
```bash
cd cast-server && UPDATE_GOLDENS=1 python -m pytest tests/test_diff_render.py -q   # cut goldens
git diff --stat tests/golden/requirements_render/                                  # review the golden
python -m pytest tests/test_diff_render.py -q                                      # green against goldens
```

### Manual Checks
- Open `GET /goals/<slug>/render/diff` in a browser after two versions exist — panel first, then
  green/amber/red tracked changes; the `diff-{n}` links jump.
- Confirm the canonical render (`/render`) still has **zero `id=`** on requirement blocks (the
  Phase 3a structural test must remain green — the transient ids are diff-view only).

### Success Criteria
- [ ] `/render/diff` renders the fixture pair; `< 2 versions` and `base>=head` handled (200 card / 422).
- [ ] `GET …/changes` negotiates JSON | panel; counts match `summarize()`.
- [ ] Version toggle appears only with ≥2 versions; links to the diff page.
- [ ] `diff_v1_v2.html` golden committed; structural assertions pass.
- [ ] Canonical-render zero-`id` structural test still green; diff CSS token-only.
- [ ] `document.html.j2` got ONLY the toggle (no comment-layer additions — those are sp5).

## Execution Notes

- The diff view is **served fresh, never persisted** — do not write it to the goal folder (FR-011).
- The transient-`id` exception is the one documented deviation from the zero-`id` thin-spine
  contract; it is scoped to the derived diff view and recorded in the module docstring (sp2) + the
  spec (sp7). Do not let `diff-{n}` ids leak into the canonical render.
- Golden discipline: cut the golden once here; if sp5 changes `document.html.j2`, the **render**
  goldens (not the diff golden) regenerate in sp5. Keep the two golden sets separate.

**Spec-linked files:** `document.html.j2`, `_theme.css.j2`, and the render route are covered by
`cast-requirements-render.collab.md`. Read it before editing; preserve the token-only rule, the
zero-`id` canonical-render contract, and the artifact class. sp7 extends the spec with the diff-view
route + transient-`id` exception — do not edit the spec here.
