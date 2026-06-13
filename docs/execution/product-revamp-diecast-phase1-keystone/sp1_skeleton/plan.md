# Sub-phase 1.1: Skeleton — One File, One State, One Render

> **Pre-requisite:** Read `docs/execution/product-revamp-diecast-phase1-keystone/_shared_context.md`
> before starting. It carries the 7 exported contracts, the binding constraints (NO TESTS,
> file:// legality, single-file packaging), and FULL AUTONOMY mode. This plan does not repeat them.

## Objective

Stand up the load-bearing skeleton of the prototype: a single self-contained
`prototype/index.html` that opens directly from disk in Chrome with **zero console errors**,
renders the three-tier shell (nav rail · CanvasFrame · ChatRail) in the Diecast light world,
makes `render(appState) → DOM` the *only* paint path, and proves the `location.hash` router
with ≥2 routes plus a working browser back button. This is the substrate sub-phases 1.2 (the
dispatcher + scenario engine) and 1.3 (the hero morph + gate) build on — get the render spine
and the synchronous-paint rule right here and the rest of the phase is cheap.

## Dependencies
- **Requires completed:** None (this is the first sub-phase).
- **Assumed codebase state:** Clean checkout. `prototype/` does not exist yet — this sub-phase creates it and the single file inside it.

## Scope

**In scope:**
- Create `prototype/` and the single file `prototype/index.html`.
- Import map pinning exact CDN versions for `preact`, `preact/hooks`, `htm/preact`, and a `driver.js` entry (Phase-6 deferred usage, included now for an honest <15KB budget check).
- Google Fonts `<link>` for IBM Plex Mono (400/500/600) + DM Sans (400/500/700).
- The canonical `:root` token block (Contract 7) lifted verbatim from `app-shell.html`, plus the motion tokens (Contract 6) and `--radius-sm/md`.
- `appState` (Contract 2) defined inline with the placeholder spine data (each spine carrying `placeholder: true`).
- The render spine (~20 lines): hash-keyed `routes` map, `App` route resolver, `paint()` = top-level synchronous `render()`, `hashchange` listener + initial paint.
- The three-tier `AppShell`: left nav rail, center `CanvasFrame` slot, right persistent `ChatRail`.
- `GoalCanvas` placeholder content (two-part anatomy stubs), `Home` chooser stub, `BoardStub`.
- A one-line HTML comment noting the network dependency (CDN + Google Fonts until Phase 6 inlines).

**Out of scope (do NOT do these — HOLD SCOPE):**
- The op dispatcher, the 5 op functions, the scenario engine, the "Next ▸" control — **all Phase 1.2.**
- The hero morph, `view-transition-name` tagging, the decision gate — **all Phase 1.3.**
- Any real surfaces, real data, real component kit, real evidence panels — Phases 2–3.
- Any test file / harness / CI (Constraint C1). Any `state.js`, `data/org.json`, separate CSS file, or `fetch()`/local ES-module import (Constraints C2/C3).
- Designing the Guide's visible character (Phase 2b — render a `◈ GUIDE` text stub only) or real per-family stage vocabulary (Phase 2c — placeholders only here).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `prototype/` | Create directory | Does not exist |
| `prototype/index.html` | Create | Does not exist |

## Detailed Steps

### Step 1.1.1: Create the file shell, import map, and fonts
- `mkdir -p prototype`, create `prototype/index.html`.
- Add `<!doctype html>`, `<meta charset>`, `<meta viewport>`, `<title>Diecast — Vision Prototype</title>`.
- Add the **import map** (in `<head>`, before any module script), pinning exact versions:
  ```html
  <script type="importmap">
  {
    "imports": {
      "preact": "https://esm.sh/preact@10.26.2",
      "preact/hooks": "https://esm.sh/preact@10.26.2/hooks",
      "htm/preact": "https://esm.sh/htm@3.1.1/preact?external=preact",
      "driver.js": "https://esm.sh/driver.js@1.3.1"
    }
  }
  </script>
  ```
  (Pin whatever exact patch versions resolve cleanly at build time; the point is *pinned*, not floating. `driver.js` is imported nowhere in Phase 1 — it exists in the map only so the <15KB library-weight check is honest against the high-level plan.)
- Add the Google Fonts `<link>` for IBM Plex Mono (400/500/600) + DM Sans (400/500/700).
- Add a one-line HTML comment near the top: `<!-- Network dependency: CDN imports + Google Fonts required until Phase 6 inlines assets. Acceptable for the dev loop. -->`

### Step 1.1.2: Inline the canonical token block (Contracts 6 + 7)
- Open `goals/product-revamp-diecast/exploration/design-samples/app-shell.html`, find its `:root` block, and copy the token names/values **verbatim** into an inline `<style>`: `--cream --cream-deep --paper --ink --ink-60 --ink-35 --hairline --hairline-soft --rasp --rasp-08 --rasp-15 --maker --checker --ok --warn --mono --sans`.
- Append the motion tokens (Contract 6): `--morph-duration: 350ms; --ease-morph: cubic-bezier(0.2,0.8,0.2,1); --motion-fast: 120ms;` and `--radius-sm: 4px; --radius-md: 8px;`. (The reduced-motion 180ms fade is consumed in 1.2/1.3; you may add a comment placeholder now.)
- Set `body { background: var(--cream); color: var(--ink); font-family: var(--sans); }`, headings `font-family: var(--mono);`.
- Do NOT invent token names. If `app-shell.html` is missing a token referenced by the contract, keep the contract's name and pick a value consistent with the light-world identity, and note the deviation in the sub-phase output.

### Step 1.1.3: Define `appState` inline (Contract 2)
- Paste the Contract-2 object verbatim into the inline `<script type="module">`. Keep `placeholder: true` on both spines and the throwaway labels exactly as specified — later phases rely on the marker to avoid mistaking stub vocabulary for the real Phase-2c set.

### Step 1.1.4: Implement the render spine (~20 lines)
- `import { render } from 'preact'; import { html } from 'htm/preact';`
- ```js
  const routes = { '': Home, '#/goal': GoalCanvas, '#/board': BoardStub };
  function resolve(hash) {                       // key on first two '#/area' segments
    const key = hash.split('/').slice(0, 2).join('/').replace(/^#$/, '');
    return routes[key] || routes[''];
  }
  function App() {
    const View = resolve(location.hash);
    return html`<${AppShell}><${View}/><//>`;
  }
  function paint() {
    appState.route = location.hash || '#/';
    render(html`<${App}/>`, document.getElementById('app'));
  }
  addEventListener('hashchange', paint);
  paint();                                       // initial paint
  ```
- **Critical rule (carried to 1.2/1.3):** every state update goes through this top-level synchronous `paint()`. Do **not** use component-local `useState` for app state — synchronous render is what lets 1.2 wrap `paint()` inside `startViewTransition` without snapshotting stale DOM.
- Add `<div id="app"></div>` in the `<body>`.

### Step 1.1.5: Build the three-tier `AppShell`
- Fresh htm components (do **not** copy `app-shell.html` markup — use it as layout reference only):
  - **Left nav rail:** brand lockup, a stub goal list with family tags, workspace links (Board / Marketplace as dead links for now). Tag the rail's root element so 1.3 can attach `view-transition-name: vt-nav-rail` (Contract 5) — e.g. a stable `class`/wrapper; do NOT add the `view-transition-name` itself yet (that's 1.3).
  - **Center `CanvasFrame`:** a slot that renders the resolved route's view (`children`).
  - **Right `ChatRail`:** fixed, persistent across routes (rendered by `AppShell`, not by individual routes). Stub content only — the "Next ▸" control and message list are 1.2.

### Step 1.1.6: Author the route views (placeholder, HOLD SCOPE)
- **`GoalCanvas`** — the locked two-part anatomy as stubs: goal header (crumb + title + family pill, from `appState.goal`/`appState.family`), a `◈ GUIDE` attribution text stub (no character design — Phase 2b), a spine zone that renders from `appState.spines[family]` (just list the steps + mark `current`; visual shape contrast is 1.3), a nudge card stub (do + why from `appState.nudge`), and a body split into a stage-artifacts panel stub and a work-happening list stub. Give the goal header, nudge card, and a receipt-trail container stable wrappers so 1.3 can attach `vt-goal-header`, `vt-nudge-card`, `vt-receipt-trail` later.
- **`Home`** — bare scenario-chooser stub: a title + one link into `#/goal/CAST-412`.
- **`BoardStub`** — a heading + one-line placeholder. Proves routing, nothing more.

## Verification

### Automated Tests (permanent)
- **None.** Constraint C1 forbids tests. Do not create any test file.

### Validation Scripts (temporary)
- None that run code. The only "script" is opening the file in a browser (below).

### Manual Checks (the only verification — open from disk in Chrome and observe)
1. **Disk open, clean console:** Double-click `prototype/index.html` (no server, no compile). The three-tier shell renders. Open DevTools → Console → **zero errors**.
2. **Routing + back button:** Navigate `#/` → `#/goal/CAST-412` → `#/board` and back via the browser **back button**. Each route paints a *distinct* surface; `appState.route` tracks `location.hash` (confirm by typing `appState.route` in the console after each navigation).
3. **No build, no local imports:** View source / DevTools → Sources: the only dependencies are CDN `<script>`/import-map URLs + Google Fonts. No `npm install`, no `import './…'`, no `fetch(`. (Search the file for `fetch(` and for `import './` / `import "../` — there must be none.)
4. **Library weight <15KB:** DevTools → Network → filter to the preact + htm modules → confirm transferred (gzipped) total is under 15KB. (`driver.js` is in the map but never imported, so it must NOT appear in the Network tab — confirm it is absent.)
5. **Identity applied:** Cream `#F5F4F0` background visible, headings in IBM Plex Mono, body in DM Sans (DevTools → Computed → `font-family`).

### Success Criteria (binary — every item must pass)
- [ ] `prototype/index.html` exists and is the **only** file in `prototype/` (Constraint C3).
- [ ] Opens from `file://` in Chrome with a **clean console** (zero errors).
- [ ] `render(appState)` via top-level `paint()` is the only paint path; no component-local `useState` holds app state.
- [ ] ≥2 hash routes switch surfaces; browser back button works; `appState.route` mirrors `location.hash`.
- [ ] No `fetch(`, no local ES-module import anywhere in the file (Constraint C2).
- [ ] Library payload (preact + htm) <15KB gzipped; `driver.js` present in the import map but not loaded.
- [ ] Cream background, IBM Plex Mono headings, DM Sans body visibly applied.
- [ ] Both placeholder spines carry `placeholder: true`; nav-rail / goal-header / nudge-card / receipt-trail / chat-rail have stable wrappers ready for 1.3's anchor tagging.

## Execution Notes
- **The synchronous-paint rule is the whole point of this sub-phase, not a detail.** 1.2 wraps `paint()` in `startViewTransition`; if app state lives in Preact hooks, the transition snapshots stale DOM and 1.3's morph silently breaks. Keep all app state in the single `appState` object and repaint via `paint()`.
- **Mount, don't conditionally remove, the future anchor elements.** The nav rail, goal header, nudge card, receipt trail, and chat rail must stay mounted across routes/families (Contract 5 uniqueness + mounted-across-families rule). Build them into `AppShell`/`GoalCanvas` as persistent structure now so 1.3 only has to add CSS `view-transition-name`.
- **Pin CDN versions.** Floating versions are the #1 way a working demo breaks a week later (Risk register, plan). Pin exact patch versions in the import map.
- **Do not over-build.** `BoardStub` is one line. `Home` is a title + one link. Resist fleshing them out — Phases 5/6 own those surfaces.
- **Spec-linked files:** none. This sub-phase creates only `prototype/index.html`, a greenfield design artifact covered by no spec (`_shared_context.md` → Relevant Specs).
- **Failure policy (C5):** if disk-open shows console errors you can't resolve in one focused pass, retry once with refined steps; second failure → mark partial, log the exact error + what was tried in the output and manifest Notes.
