# sp4a output — diff-view wiring (route + `/changes` + version toggle + diff CSS)

**Status: COMPLETE.** All Detailed Steps executed, all verification run, every success
criterion met. `tests/test_diff_render.py` is green (16 tests); the full non-e2e suite stays
green (781 passed, 7 pre-existing unrelated skips) — no regression.

## What landed

| File | Action | Notes |
|------|--------|-------|
| `cast_server/routes/pages.py` | **modified** | Added `GET /goals/{slug}/render/diff` + `_safe_parse` helper; new imports (`requirement_version_service`, `parse_requirements`, `ParsedRequirements`, `render_diff`). |
| `cast_server/routes/api_requirements.py` | **modified** | Added negotiated `GET …/requirements/changes` + `_resolve_diff_range` helper; imports `parse_requirements`, `diff_blocks`, `summarize`. |
| `cast_server/requirements_render/renderer.py` | **modified** | `render_requirements` + `_compose` thread `goal_slug` + `version_count` → the toggle context (`show_diff_toggle`, `current_version`). Defaults `None`/`0` ⇒ no toggle (golden-safe). |
| `cast_server/services/requirements_render_service.py` | **modified** | Passes `goal_slug` + `version_count = len(list_versions(...))` into the renderer. |
| `cast_server/requirements_render/templates/document.html.j2` | **modified** | Added ONLY the version toggle `<nav>` inside `.rr-controls` (≥2 versions ⇒ link to the diff page). No comment-layer additions (those are sp5). |
| `cast_server/requirements_render/templates/_theme.css.j2` | **modified** | Added the `.version-toggle*` CSS block (token-only). |
| `cast_server/templates/fragments/requirements_comments/changes_panel.html` | **created** | The negotiated "What changed" panel fragment. |
| `tests/test_diff_render.py` | **created** | 16 tests (golden + structural + route + `/changes` negotiation + toggle visibility + zero-id). |
| `tests/golden/requirements_render/diff_v1_v2.html` | **created** | Byte golden for the fixture pair (`UPDATE_GOLDENS=1`). |
| `tests/golden/requirements_render/*.html` (12 renderer goldens) | **regenerated** | Additive theme-CSS delta only (the `.version-toggle` block); no structural drift — confirmed by diff before regen. |

## Step-by-step

### 4a.1 — `GET /goals/{slug}/render/diff` (pages.py)
- Slug-validate → 404 (path-traversal rule). `head` defaults to the current version; `base` to
  `head − 1`.
- **< 2 versions** → 200 with a plain "No prior version to compare" card (never an error).
- **`base >= head`** → 422. Unknown requested version → 404.
- Else `render_diff(parse(base.content), parse(head.content), base_version=base, head_version=head)`,
  served **fresh** (never written to the goal folder — pinned by `test_diff_route_not_written_to_disk`).
- An unparseable archived snapshot is parsed via `_safe_parse` → `None`, which `render_diff`
  turns into a "cannot diff this pair" card (warning surfaced) — never a 500.

### 4a.2 — `GET …/requirements/changes` (api_requirements.py)
- Negotiated (copies the sp1 `_is_hx` pattern): header-less → `summarize(diff_blocks(old, new))`
  JSON; `HX-Request` → the `changes_panel.html` fragment. Default `head = current`,
  `base = head − 1`. Slug → 404; `base >= head` → 422; unknown version → 404; an unparseable
  snapshot → 422 (`cannot diff`), never a 500.
- This is FR-017's same-door surface — `test_changes_json_matches_summarize` asserts the JSON body
  equals `summarize()` byte-for-byte.

### 4a.3 — Version toggle (document.html.j2)
- A `<nav class="version-toggle">` beside the Expand-all control: `Current (vN)` plus a plain link
  `Changes since v(N−1)` → `/goals/{slug}/render/diff`. Renders **only** when `version_count >= 2`.
- **No swap machinery, no `id=`, no script** — the canonical render stays a thin-spine standalone
  doc (`test_canonical_render_stays_zero_id_with_toggle` asserts `id=` absent even with the toggle).
- Threaded purely (renderer stays deterministic): `goal_slug`/`version_count` default to omit the
  toggle, so the family goldens render toggle-free.

### 4a.4 — Diff golden
- `diff_v1_v2.html` cut from the sp2 fixture pair (`refined_requirements.collab.md` vs
  `…v2-edit.collab.md`): counts `+1 ~1 −1` over 52 unchanged; 55 transient `diff-{n}` ids; panel
  anchors `#diff-9 / #diff-29 / #diff-49` all resolve to real ids.

## Verification (all run, all green)
- `uv run pytest tests/test_diff_render.py -q` → **16 passed**.
- Regression: `test_requirements_renderer.py` (87, goldens regenerated) + `test_block_diff.py` (16)
  + `test_render_route_and_service.py` + `test_requirements_parser.py` + `test_requirements_comments_api.py`
  + `test_requirement_versions.py` + `test_archive_retrieval.py` + `test_theme_token_drift.py` → **all green**.
- Full non-e2e suite → **781 passed, 7 skipped** (skips are pre-existing delegation/UI items, unrelated).
- Token-only: no hex near the `.version-toggle` block; `test_theme_token_drift.py` green.
- App import smoke: `cast_server.app` imports clean; both `/render/diff` and `…/changes` routes registered.

### Success criteria — all met
- [x] `/render/diff` renders the fixture pair; `< 2 versions` → 200 card, `base>=head` → 422, unknown slug → 404.
- [x] `GET …/changes` negotiates JSON | panel; JSON == `summarize()`; counts match.
- [x] Version toggle appears only with ≥2 versions; links to the diff page.
- [x] `diff_v1_v2.html` golden cut; structural assertions (added/modified/`<del>`/removed, panel anchors) pass.
- [x] Canonical-render zero-`id` structural test still green; diff/toggle CSS token-only.
- [x] `document.html.j2` got ONLY the toggle (no comment-layer additions — sp5 owns those).

## Notes for dependent sub-phases
- **sp5** edits the SAME `document.html.j2` AFTER this: the toggle is already in `.rr-controls`;
  sp5 adds the script tags / tray / `data-goal-slug` / Goal-Card comment-count fill, then
  regenerates the **render** goldens again (the diff golden is independent and should not move).
- **One scope note on the `/changes` panel fragment links:** each panel item links to the diff
  *page* (`/goals/{slug}/render/diff?base=N&head=M`), NOT a per-item `#diff-{n}` fragment.
  Rationale: `summarize()` orders items added→modified→removed, while `render_diff` numbers
  `diff-{n}` in head-document spine order — so a fabricated `#diff-{n}` would point at the WRONG
  block. The diff page's **own** internal panel (built by `render_diff`) links to its `diff-{n}`
  anchors correctly and is tested; the `/changes` fragment routes the reader to that page rather
  than promising mismatched anchors. The load-bearing contract (counts == `summarize()`) holds.
- **sp7** extends `cast-requirements-render.collab.md` with the diff-view route + the transient-`id`
  exception (not edited here, per the spec-linked-file rule).
