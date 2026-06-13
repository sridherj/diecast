# Sub-phase 5: Vanilla-JS comment layer + tray (the locked UX, decision #7)

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase4/_shared_context.md` before starting.

## Objective

Build the locked commenting UX as **~150 lines of vanilla JS** over the existing Jinja+HTMX stack —
**no framework, no annotation library**. Select text → 💬 pill → inline composer → the comment
persists via the SAME `POST /comments` an agent curls → renders as a `<mark>` highlight. Displaced
and orphaned comments surface in a tray (decision #9: always surfaced, never lost). The Goal Card
shows the open-comment count + convergence chip, filled client-side.

## Dependencies

- **Requires completed:** sp1 (the comment API + negotiated fragments), sp4a (the version toggle is
  already in `document.html.j2`; this sub-phase adds the comment-layer markup to the same template
  AFTER sp4a so the two template edits serialize).
- **Assumed codebase state:** `GET /comments` returns JSON (open comments carry `displaced`) and an
  `HX-Request` tray fragment; `POST /comments` returns a `thread_item.html` fragment to HTMX; the
  Phase 3a DOM contract holds (every requirement block is ONE contiguous text-selectable unit under
  a real heading; **zero `id=`, zero `data-block-anchor`**); `static/htmx.min.js` is served.

## Scope

**In scope:**
- `cast_server/static/requirements_comments.js` (~150-line vanilla budget, htmx transport).
- `document.html.j2` additions: `<script>` tags, the tray container, `data-goal-slug` on `<body>`,
  the Goal Card comment-count/convergence slot wiring (fill the Phase 3a `[PENDING Phase 4]` slot
  client-side).
- `_theme.css.j2` additions: `.comment-mark`, `.comment-pill`, `.comment-composer`, `.comment-tray`
  (tokens only).
- `cast_server/templates/fragments/requirements_comments/composer.html` (the inline composer
  fragment; `tray.html`/`thread_item.html` already exist from sp1).
- Regenerate the render goldens (`UPDATE_GOLDENS=1`).

**Out of scope (do NOT do these):**
- Any new endpoint or service change (sp1/sp3/sp4a own the server). The JS only consumes existing
  negotiated endpoints.
- Commenting on the diff view (read-only; HOLD SCOPE).
- A framework or annotation library — if the layer genuinely can't fit ~150 lines + htmx, that is
  **escalation evidence** (Phase-0 Spike C protocol), NOT license to add a dependency.
- Re-rendering the baked HTML on comment change — comments must never force a re-render (the
  artifact's `source-hash` staleness model is content-only).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast_server/static/requirements_comments.js` | Create | Does not exist |
| `cast_server/requirements_render/templates/document.html.j2` | Modify | Has version toggle (sp4a) |
| `cast_server/requirements_render/templates/_theme.css.j2` | Modify | Has diff CSS (sp2/sp4a) |
| `cast_server/templates/fragments/requirements_comments/composer.html` | Create | sp1 made the dir |
| `tests/golden/requirements_render/{family}.html` | Modify (regen) | Phase 3a goldens |

## Detailed Steps

### Step 5.1: Template additions (document.html.j2)
- `data-goal-slug="{{ slug }}"` on `<body>` (page chrome data — NOT a block anchor).
- `<script src="/static/htmx.min.js"></script>` + `<script src="/static/requirements_comments.js"
  defer></script>`.
- A tray container element (e.g. `<aside class="comment-tray" hx-get=".../comments"
  hx-trigger="load">`) the negotiated GET fills with `tray.html`.
- **Progressive enhancement:** opened as a bare file from the goal folder, the scripts 404 and the
  document remains a perfectly readable render (the Phase 3a self-contained property degrades to
  read-only — document this in the sp7 spec note). Do NOT make content depend on JS.

### Step 5.2: `requirements_comments.js` (~150 lines, vanilla)
On `DOMContentLoaded`:
- Read slug from `<body data-goal-slug>`. `GET /api/goals/{slug}/requirements/comments` (JSON).
- For each **open, non-displaced** comment: locate `quoted_text` in the rendered text via a
  TreeWalker over text nodes **within requirement sections** (quotes are contiguous per the DOM
  contract; concatenate text nodes within a section before matching to survive inline-tag splits
  like `<strong>`), wrap the match in `<mark class="comment-mark" data-comment-id="{id}">`.
- Displaced + orphaned comments render in the **tray** (server fragment `tray.html`, via the
  negotiated GET): quote + hint + body + state, with resolve/reopen buttons — "needs re-anchor" for
  displaced, "orphaned — triage" for orphaned.

**Selection flow:** `mouseup` within the document container → non-empty selection → float the
"💬 Comment" pill at the selection rect → click → inline composer (`composer.html`, fetched or
cloned from a `<template>`) anchored **below** the selection, **flipped above** when the viewport
bottom is cramped (the locked GitHub/Docs behavior). The composer captures
`quoted_text = selection.toString()` and `section_hint` = nearest preceding `h2/h3` text (walk
up/back from the range start — the DOM contract guarantees real heading elements). Submit =
`hx-post` to `POST /comments` → the `thread_item.html` fragment swaps in beside the new `<mark>`.
Escape/blur dismisses (preserving the selection on POST failure — show the error inline, no lost
draft). Re-bind marks + handlers on `htmx:afterSwap`.

**Goal Card wiring:** fill the Phase 3a `[PENDING Phase 4]` slot client-side: open-comment count +
convergence chip (`unconverged · 3 open` / `converged`) from the comments payload. The baked HTML
stays comment-agnostic.

**Click an existing `<mark>`** → thread popover: body, author + `author_kind` badge, events trail
(fetched lazily via `get_comment_events`), resolve button. Resolved comments lose their `<mark>`
(no highlight noise); they remain in the tray's "resolved" collapse.

### Step 5.3: CSS (_theme.css.j2)
`.comment-mark`, `.comment-pill`, `.comment-composer`, `.comment-tray` — `var(--color-*)` tokens
only, never hex (the Phase 3a hex-scan test enforces).

### Step 5.4: Security discipline
All comment content enters the DOM via **server-rendered autoescaped fragments**, never
`innerHTML` of raw API strings. The pill and composer are keyboard-reachable (`tabindex`,
Enter-to-comment); `<mark>` carries `title="{author}: {body excerpt}"`.

### Step 5.5: Regenerate render goldens
`UPDATE_GOLDENS=1 pytest tests/test_requirements_renderer.py` (and any render-route golden test) —
the template now has the script tags / tray / data-goal-slug. Review the diff before committing.

## Verification

### Automated Tests (permanent)
- The interactive behavior is covered by the **e2e harness (sp7)**, per `cast-ui-testing.collab.md`
  US2. This sub-phase's automated coverage:
  - Render-route golden refresh (template additions present; tokens only).
  - A line-count / no-framework smoke (the full pin test is sp6): `requirements_comments.js`
    contains no `import`/`require` of any framework.
- Defer the select→pill→composer→`<mark>` and resolve/toggle/tray flows to sp7's e2e suite (they
  need a real browser harness).

### Validation Scripts (temporary)
```bash
cd cast-server
UPDATE_GOLDENS=1 python -m pytest tests/test_requirements_renderer.py -q && git diff --stat tests/golden/
wc -l cast_server/static/requirements_comments.js     # ~150-line budget
grep -nE "import |require\(" cast_server/static/requirements_comments.js   # no framework imports
grep -nE "#[0-9a-fA-F]{3,6}" cast_server/requirements_render/templates/_theme.css.j2  # no new hex
```

### Manual Checks (browser; carry-forward if no browser available)
- Select text on `/goals/<slug>/render` → pill → composer (flips up near viewport bottom) → submit →
  `<mark>` + thread item appears.
- An agent `POST /comments` (curl) produces the identical visible comment on next load.
- Edit the `.collab.md` to reword a quoted span → reload → that comment moves to the tray as "needs
  re-anchor" (displaced).
- Resolve from the thread → `<mark>` disappears, comment drops to the resolved collapse.

> **No-browser note (project default):** autonomous/headless runs can't drive Chrome. Record a
> static verdict + a human-eyeball carry-forward for the visual checks above; never block the
> sub-phase on them. The structural/golden/line-budget checks gate instead.

### Success Criteria
- [ ] `requirements_comments.js` exists, ≤ ~150 lines, vanilla, zero framework imports.
- [ ] `document.html.j2` has script tags, tray container, `data-goal-slug`; Goal Card slot filled client-side.
- [ ] Composer captures `quoted_text` + nearest-heading `section_hint`; submits to the SAME `POST /comments`.
- [ ] Displaced/orphaned comments render in the tray; resolved comments lose their `<mark>`.
- [ ] CSS token-only; content enters DOM via autoescaped fragments (no raw `innerHTML`).
- [ ] Render goldens regenerated; progressive-enhancement (file:// read-only) preserved.

## Execution Notes

- **The ~150-line budget + the `package.json` pin (sp6) keep this honest.** Overflow is escalation
  evidence per the spike protocol — flag it, don't add a library.
- Marks that fail to locate (a race between load and an edit) degrade to the tray on next refresh —
  the displaced path catches them; never crash on a missed locate.
- Comments must never trigger a re-render of the baked artifact — the staleness model is
  content-only. The Goal Card count is purely client-side decoration.

**Spec-linked files:** `document.html.j2`, `_theme.css.j2` are covered by
`cast-requirements-render.collab.md` (Phase 3a render surface). Read the spec; preserve the
token-only rule, the zero-`id` canonical DOM contract (the `<mark>` wraps text in-place; it does not
add `id=` to requirement blocks), and the self-contained-artifact property (now progressive
enhancement). sp7 records the script-tag / progressive-enhancement change in the spec.
