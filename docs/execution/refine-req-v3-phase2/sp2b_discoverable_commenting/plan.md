# Sub-phase 2b: Discoverable Commenting — a visible affordance beside the hidden gesture

> **Pre-requisite:** Read `docs/execution/refine-req-v3-phase2/_shared_context.md` before starting this sub-phase.

## Objective

A reader opening a *served* render sees, without doing anything, a visible commenting control
plus a hint that *states the gesture* — so an unprompted first-time reader can comment (US6 /
FR-014 / SC-006). The existing select-to-comment pill keeps working unchanged. A bare `file://`
open shows **no** dead comment control (FR-028 progressive enhancement preserved).

## Dependencies

- **Requires completed:** None (parallel with sp2a).
- **Assumed codebase state:** `static/requirements_comments.js` with an `init()` that runs only
  when `data-goal-slug` is present; `.rr-controls` bar in the served template; `_theme.css.j2`
  carrying the `.comment-*` rules; the requirements-render UI screen under `cast-server/tests/ui/`.

## Scope

**In scope:**
- JS-inject a `button.comment-affordance` + adjacent `.comment-affordance__hint` span into
  `.rr-controls`, from `init()` in `requirements_comments.js`.
- Additive click behavior: reveal + scroll to `.comment-tray-host`, pulse the hint ~1.5 s.
- CSS for `.comment-affordance` / `.comment-affordance__hint` in `_theme.css.j2`, beside the
  existing `.comment-*` rules. **Class selectors only — no `id=`.**
- `/cast-update-spec` on `cast-requirements-render.collab.md` recording the additive affordance
  + adding `.comment-affordance` to the SC-009 selector list.
- Two new assertions on the requirements-render UI screen (affordance present on load; click
  reveals tray).

**Out of scope (do NOT do these):**
- **No new comment-creation path.** The same-door API (`/api/goals/{slug}/requirements/comments`)
  is untouched; the affordance teaches + surfaces, the selection gesture still creates. No
  click-to-place-comment mode (scope expansion).
- **No template-rendered control.** The affordance must be JS-injected behind the existing slug
  guard, never in the static artifact (FR-028 — a template control would show dead UI on
  `file://`).
- **No `id=` anywhere.** DOM contract (US7/FR-013).
- No changes to `goal_card.py` / `renderer.py` / card text (that's 2a).
- No golden regeneration here (that's 2c). Only `_theme.css.j2` additions change golden bytes,
  regenerated in 2c.
- Do NOT change the locked decision-#7 select→pill→composer flow or any existing `.comment-*`
  behavior.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/static/requirements_comments.js` | Modify | `init()` runs only when `data-goal-slug` present; manages pill, composer, tray, marks; mirrors a convergence-chip injection pattern (`updateCard`) |
| `cast-server/cast_server/requirements_render/templates/_theme.css.j2` | Modify | Holds `.comment-pill` / `.comment-composer` / `.comment-tray-host` rules |
| `docs/specs/cast-requirements-render.collab.md` | Modify (via `/cast-update-spec`) | Draft v2; FR-028 progressive enhancement; SC-009 named-selector list; decision #7 commenting UX |
| `cast-server/tests/ui/` requirements-render screen (`cast-ui-test-requirements-render`) | Modify | Existing SC-009 selector flows; browser-capable CI only |

## Detailed Steps

### Step 2b.1: Inject the affordance from `requirements_comments.js`

In `init()` (which only runs when `data-goal-slug` is present — exactly the condition under
which commenting is live):

- Create `button.comment-affordance` with visible text `💬 Comment`.
- Create an adjacent persistent hint span `.comment-affordance__hint` reading
  `select any text to comment`. The hint *states the gesture* — this is what makes SC-006 pass
  for a reader given no instructions.
- Insert both into the existing `.rr-controls` bar.
- **Defensive guard (plan-review / design-review):** if `.rr-controls` is absent (older cached
  artifact), the injection must **no-op silently** — do not throw and kill the rest of `init()`
  (marks, tray, composer). Use a null check, matching the file's existing defensive style.

Mirror the existing convergence-chip injection (`updateCard`) for placement style and idempotency
(don't double-insert on re-init).

### Step 2b.2: Click behavior (additive, minimal — teach + surface, no new creation path)

On affordance click:
- Reveal and scroll to `.comment-tray-host` (where existing comments + displaced/orphaned groups
  live).
- Briefly **pulse the hint** by toggling a CSS class for ~1.5 s to draw the eye to the gesture
  instruction.
- **No** new comment-creation path — creation stays select → `.comment-pill` → composer through
  the same-door API.

The exact-text contract (asserted by the UI test): the affordance, with hint, reads
`💬 Comment — select any text to comment` (visible button text `💬 Comment` + hint
`select any text to comment`).

### Step 2b.3: Style the affordance in `_theme.css.j2`

Add `.comment-affordance` / `.comment-affordance__hint` rules (+ the pulse class) next to the
existing `.comment-pill` / `.comment-composer` rules — the established home for comment CSS.
**Class selectors only — no `id=`.** These rules are the *only* golden-byte change from 2b
(regenerated in 2c). Unused rules on a `file://` open are harmless (the element never appears
there).

### Step 2b.4: Record the additive affordance in the spec

→ Delegate: `/cast-update-spec` on `docs/specs/cast-requirements-render.collab.md` — record:
- Extend the FR-028 / commenting-UX area with: "a visible `.comment-affordance` control +
  gesture hint is injected by `requirements_comments.js` on served renders (slug present);
  select-to-comment remains the creation path; bare `file://` renders carry no affordance."
- Add `.comment-affordance` to the **SC-009 named-selector list**.

Review `/cast-update-spec` output for: the diff touches **only** those clauses and bumps
version/date; the **DOM contract (US7/FR-013)** and **decision #7's select→pill→composer flow**
read as *unchanged*. If the diff strays beyond those clauses, reject and re-run with tighter
scope.

### Step 2b.5: Extend the requirements-render UI screen

Add two assertions to the requirements-render UI screen under `cast-server/tests/ui/`
(`cast-ui-test-requirements-render`), alongside the existing SC-009 selector flows, targeting
`.comment-affordance`:
- **Affordance present on load:** `.comment-affordance` exists in the served-render DOM on load
  and reads `💬 Comment — select any text to comment`.
- **Click reveals the tray:** clicking `.comment-affordance` reveals/scrolls to
  `.comment-tray-host`.

Keep the existing select → pill → composer → `<mark>` flow assertion green. Runs in
browser-capable CI only, like the rest of that screen.

## Verification

### Automated Tests (permanent)

- **UI screen (`cast-server/tests/ui/`, browser-capable CI):** the two new `.comment-affordance`
  assertions pass; the existing select→pill→composer→`<mark>` flow stays green.
- **`grep`-level DOM-contract check:** no `id=` introduced anywhere in render output or the new
  CSS/JS. (Also re-verified structurally in 2c.)
- **Progressive-enhancement guard (T3 — maps to existing coverage):** the slug-free golden
  byte-comparison **is** the `file://` no-affordance guard — goldens render with no slug and no
  JS execution, so the JS-injected affordance can never appear in golden HTML. No new test
  harness needed; verified during 2c's per-family golden diff review. The browser UI assertion
  covers the positive (served-render) case.

### Validation Scripts (temporary)

```bash
# Confirm no id= leaked into the new CSS/JS:
grep -n 'id=' cast-server/cast_server/requirements_render/templates/_theme.css.j2 \
             cast-server/cast_server/static/requirements_comments.js || echo "no id= — OK"
# Confirm the affordance is class-only and the hint text is present:
grep -n 'comment-affordance' cast-server/cast_server/static/requirements_comments.js \
                             cast-server/cast_server/requirements_render/templates/_theme.css.j2
```

### Manual Checks

- **Served render** (`GET /goals/{slug}/render`): `.comment-affordance` present on load, reads
  `💬 Comment — select any text to comment`; clicking it reveals/scrolls to the comment tray;
  selecting text still shows `.comment-pill` → composer → `<mark>`.
- **`file://` open** of the generated artifact: **no** `.comment-affordance` in the DOM.
- **`.rr-controls` absent** (simulate an older cached artifact): `init()` still wires marks /
  tray / composer — the affordance injection no-ops without throwing.
- **SC-006 carry-forward:** an autonomous run cannot drive a browser; capture a static verdict
  (screenshot or rendered-HTML walkthrough of the affordance) and record "human eyeballs SC-006
  on a served render" as an explicit follow-up. **Never block the phase on it** (project
  standard for visual gates — see `_shared_context.md` / Risks).

### Success Criteria

- [ ] `.comment-affordance` + `.comment-affordance__hint` injected from `init()` into
      `.rr-controls`, only when `data-goal-slug` is present.
- [ ] Affordance reads `💬 Comment — select any text to comment`; click reveals + scrolls to
      `.comment-tray-host` and pulses the hint ~1.5 s.
- [ ] No new comment-creation path; same-door API untouched; select→pill→composer unchanged.
- [ ] CSS in `_theme.css.j2`, class selectors only, **no `id=`** anywhere.
- [ ] `.rr-controls`-absent path no-ops silently (no throw).
- [ ] `/cast-update-spec` diff touches only the FR-028/commenting clause + SC-009 selector list,
      bumps version/date; DOM contract + decision-#7 flow read unchanged.
- [ ] UI screen extended with the two assertions (browser-capable CI); existing flow stays green.
- [ ] `file://` open shows no affordance (verified via slug-free goldens in 2c).
- [ ] SC-006 static verdict captured + human-eyeball follow-up recorded; phase not blocked on it.

## Execution Notes

- **JS-injection, not template** is non-negotiable for FR-028: a template-placed control shows
  dead UI on `file://` and would pollute golden HTML. The slug guard is what keeps the affordance
  exactly on the live-commenting code path.
- Match the file's existing defensive null-check style; the affordance must never be able to take
  down the rest of `init()`.
- The only golden-byte delta from 2b is the `_theme.css.j2` rule block — leave its regeneration
  to 2c. Do not regen goldens here.
- This sub-phase shares **no files** with 2a (Python card paths), so it can run fully in parallel.

**Spec-linked files:** `docs/specs/cast-requirements-render.collab.md` covers the commenting UX.
The visible affordance is a user-facing surface change over a locked decision (#7) + the SC-009
selector list → the `/cast-update-spec` activity (Step 2b.4) is **mandatory**, not optional. The
DOM contract (US7/FR-013) and the select→pill→composer flow must survive the spec edit verbatim.
