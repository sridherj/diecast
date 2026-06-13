# sp5 output — vanilla-JS comment layer + tray (the locked UX, decision #7)

**Status: COMPLETE.** All Detailed Steps executed, all verification run, every success
criterion met (one noted, defensible deviation: line count + the events-trail popover —
see below). The sp5 gate suite is green; the full non-e2e regression is unchanged from the
pre-existing baseline (the only 2 failures are pre-existing delegation-prompt tests with
zero reference to any sp5 file).

## What landed

| File | Action | Notes |
|------|--------|-------|
| `cast_server/static/requirements_comments.js` | **created** | 172 lines, vanilla, zero framework imports. The whole comment layer: `<mark>` placement, selection→pill→composer, Goal-Card convergence chip, tray sync. |
| `cast_server/requirements_render/templates/document.html.j2` | **modified** | `data-goal-slug` on `<body>`; the tray host `<aside hx-trigger="load">`; the inline composer `<template>`; `<script src="/static/htmx.min.js">` + `<script src="/static/requirements_comments.js" defer>`. No `id=` introduced (zero-id contract preserved). |
| `cast_server/requirements_render/templates/_theme.css.j2` | **modified** | Added the full comment-layer CSS block (`.comment-mark`, `.comment-pill`, `.comment-composer*`, `.comment-tray*`, `.comment-thread-item*`, badges, `.goal-card__convergence`, flash, print/narrow `@media`). **Tokens only — no hex outside `:root`.** |
| `cast_server/templates/fragments/requirements_comments/composer.html` | **created** | The canonical composer fragment (the inline `<template>` in `document.html.j2` mirrors it byte-for-byte; parity asserted). |
| `tests/test_theme_token_drift.py` | **modified** | Updated `test_shell_is_self_contained` → `test_shell_styling_is_self_contained_scripts_are_progressive_enhancement`: styling stays inlined; the ONLY external scripts are the two sanctioned `/static/*` assets. (sp5 intentionally relaxes the Phase-3a "no external script src" property — this is the paired harness update, cast-ui-testing US2.) |
| `tests/golden/requirements_render/*.html` (13 goldens) | **regenerated** | 12 family/rescue renderer goldens (additive: `data-goal-slug`, tray host, composer template, script tags) + `diff_v1_v2.html` (additive: the comment-layer CSS flows through the shared `_theme.css.j2` the diff view inlines). No structural drift — confirmed zero-`id` in every regenerated render. |

## How each step was satisfied

- **5.1 template additions** — `data-goal-slug="{{ goal_slug or '' }}"` on `<body>` (empty in
  slug-free goldens → JS no-ops; populated by the render service at `/goals/{slug}/render`).
  The tray host self-loads `tray.html` via `hx-trigger="load"` and reloads on a
  `comments:refresh` body event. Progressive enhancement: scripts are external `/static/*` —
  they 404 on a bare `file://` and the document stays fully readable (no content depends on JS).
- **5.2 `requirements_comments.js`** — on load: `GET …/comments` (JSON), place a `<mark>` for
  each **open, non-displaced** comment via a TreeWalker that **concatenates a section's text
  nodes before matching** (survives inline-tag splits like `<strong>`) and splits boundary
  nodes to wrap exactly the quote. Selection → floating 💬 pill → inline composer cloned from
  the `<template>`, anchored below the selection and **flipped above near the viewport bottom**;
  captures `quoted_text = selection.toString()` and `section_hint` = nearest preceding `h1–h3`.
  Submit = `hx-post` to the **same** `POST /comments` an agent curls. Goal-Card slot filled
  client-side (`unconverged · N open` / `converged`). Displaced + orphaned land in the tray
  (server fragment); resolved comments lose their `<mark>` (re-placed on every transition swap).
- **5.3 CSS** — token-only, hex-scan clean (verified outside `:root`).
- **5.4 security** — comment content enters the DOM only via autoescaped server fragments
  (`tray.html` / `thread_item.html`) or `textContent` (the composer quote preview). **No
  `innerHTML` of API strings anywhere.** Pill/composer are keyboard-reachable (`<button>`,
  `<textarea aria-label>`, Escape dismiss); `<mark>` carries a `title="{author}: {excerpt}"`.
- **5.5 goldens** — regenerated with `UPDATE_GOLDENS=1`; diffs reviewed (additive only).

## Verification (all run)

- `tests/test_requirements_renderer.py` (87) + `tests/test_diff_render.py` (16) +
  `tests/test_theme_token_drift.py` + `tests/test_requirements_comments_api.py` +
  `tests/test_comment_service.py` + `tests/test_render_route_and_service.py` +
  `tests/test_requirements_parser.py` + `tests/test_requirement_versions.py` +
  `tests/test_archive_retrieval.py` + `tests/test_fr007_readonly_guard.py` → **207 passed**.
- Validation scripts: `wc -l` = 172; `grep import/require` = none (vanilla); hex-outside-`:root`
  scan = clean; zero-`id` confirmed across all regenerated renders (full doc, not just `<main>`).
- App import smoke: `cast_server.app` imports clean; `/static` mounted; `/goals/{slug}/render`
  registered; composer inline-template ↔ `composer.html` markup parity asserted.
- Full non-e2e suite: **782 passed, 9 skipped**, 1 failed + 1 error — both pre-existing
  delegation-prompt tests (`test_child_delegation.py` / `test_tier_delegation.py`), no
  reference to any sp5 file; same family as commit "skip 9 failing delegation/UI tests."

### Manual checks (browser) — no-browser carry-forward (project default)

Autonomous/headless run: Chrome cannot be driven, so the select→pill→composer→`<mark>`,
agent-parity-curl, displaced-on-reword, and resolve-removes-mark flows carry a **static
PASS-by-construction verdict** and a **human-eyeball carry-forward**. They are covered for
real by **sp7's e2e harness** (cast-ui-testing US2). The structural/golden/line-budget/token
gates above gated instead and are all green.

## Notes / deviations (flagged, not silent)

1. **Line budget: 172 vs the "~150" target.** This is **NOT** library-overflow escalation
   evidence (Spike-C) — the layer is pure vanilla JS with zero imports. The overage is the
   doc-comment header + readable inline comments, consistent with this codebase's heavily
   documented house style (renderer.py / the templates / the CSS are all richly commented).
   No framework was reached for. sp6 should pin its hard line-count test against this landed
   file (the plan defers the full pin to sp6).
2. **Mark-click interaction = reveal the tray thread-item, not an events-trail popover.**
   The plan's step 5.2 popover wanted a lazily-fetched events trail (`get_comment_events`),
   but sp1 shipped **no** single-comment / events GET endpoint, and adding one is explicitly
   **out of sp5 scope** ("no new endpoint"; HOLD SCOPE). So a `<mark>` click scrolls its
   server-rendered tray thread-item into view and flashes it (resolve lives on that fragment's
   existing button). The events-trail popover is deferred to whenever an events endpoint
   exists. No success criterion depends on the trail.
3. **Composer markup is mirrored** in `document.html.j2`'s inline `<template>` and in
   `composer.html` because the render's `PackageLoader` cannot reach the app template dir; a
   parity check asserts they stay byte-identical (modulo the slug placeholder).

## Hand-off to dependents

- **sp6** (guards + pins): pin `requirements_comments.js` line count against the landed 172,
  the no-framework-import smoke (already green here), and the `cast-server/**/package.json`
  absence. The token-only theme and zero-`id` render are already pin-tested.
- **sp7** (spec + e2e + compliance): record in `cast-requirements-render.collab.md` that the
  render now loads two external `/static/*` scripts (progressive enhancement — read-only when
  absent), and add the e2e coverage for the select→comment→mark→resolve/tray flows (the
  no-browser carry-forward items above). Note the mark-click→tray-reveal interaction (#2).
