# SC-006 Static Verdict — Discoverable Commenting Affordance (sp2b)

> **Mode:** Autonomous run — no browser available (project standard for visual/taste gates:
> emit a static verdict + a human-eyeball carry-forward; never block the phase).

## What was built

On a **served** render (`GET /goals/{slug}/render`, where `<body data-goal-slug>` is present),
`requirements_comments.js` `init()` now calls `injectAffordance()`, which appends two siblings
to the existing `.rr-controls` bar:

1. `button.comment-affordance` — visible text **`💬 Comment`**.
2. `span.comment-affordance__hint` — text **`select any text to comment`** (a `::before` in
   `_theme.css.j2` renders the ` — ` separator, kept out of `textContent`).

Rendered, the affordance reads: **`💬 Comment — select any text to comment`** — the hint
*states the gesture*, which is what lets a reader given no instructions discover commenting
(US6 / FR-014 / SC-006).

Clicking the affordance scrolls to / surfaces `.comment-tray-host` and pulses the hint
(`.comment-affordance__hint--pulse`, ~1.5 s). It opens **no** new creation path — selection →
`.comment-pill` → `.comment-composer` through the same-door API stays the only way to create
(locked decision #7).

## Static trace (verified without a browser)

- **Injection is behind the slug guard.** `init()` runs only after `var slug = …; if (!slug) return;`
  near the top of the IIFE. A bare `file://` open (scripts 404, no slug) never reaches
  `injectAffordance()` → **no affordance in the standalone artifact** (FR-028). Confirmed by
  reading the guard order in `requirements_comments.js`.
- **Defensive no-op.** `injectAffordance()` returns early if `.rr-controls` is absent (older
  cached artifact) and is idempotent (`if (controls.querySelector('.comment-affordance')) return`),
  so it can never throw and take down the rest of `init()` (marks / tray / composer).
- **DOM contract intact.** `grep -n 'id=' _theme.css.j2 requirements_comments.js` → **none**.
  The affordance is class-only (`.comment-affordance`, `.comment-affordance__hint`).
- **Token discipline.** No hex in the new CSS block — only `var(--…)` tokens (Phase 3a hex-scan).
- **JS / Python valid.** `node --check requirements_comments.js` OK; `py_compile runner.py` OK.

## Browser-gated checks (deferred — cannot run autonomously)

The two new UI assertions live in `cast-server/tests/ui/runner.py`
(`_assert_requirements_render`) and run in **browser-capable CI only**:

- `render_affordance_present_on_load` — `.comment-affordance` visible; combined text equals
  `💬 Comment — select any text to comment`.
- `render_affordance_click_reveals_tray` — clicking `.comment-affordance` reveals
  `.comment-tray-host`.

The existing `select → pill → composer → <mark>` flow assertions are unchanged and stay green.

## Carry-forward (human action — non-blocking)

- [ ] **Human eyeballs SC-006 on a served render:** open `GET /goals/{slug}/render` in a browser,
      confirm the `💬 Comment — select any text to comment` affordance is visible on load and that
      clicking it surfaces the comment tray + pulses the hint, then confirm a bare `file://` open of
      the generated artifact shows **no** affordance.
- [ ] **Run the requirements-render UI screen** in browser-capable CI (`runner.py --screen=requirements-render`)
      to exercise the two new assertions live.

**This gate does not block Phase 2.** Golden bytes change only via the `_theme.css.j2` rule block;
golden regeneration is consolidated into sub-phase 2c.
