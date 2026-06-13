# Product Revamp: Diecast — Phase 1: Keystone — Render Architecture & Morph Technique Spike

## Overview

This phase builds the load-bearing skeleton of the vision prototype and answers its riskiest
technical unknown: **can a static file, opened from disk with no build step, deliver a
vision-grade canvas morph?** The deliverable is `prototype/index.html` — one self-contained
file where `render(appState) → DOM` drives every pixel, `location.hash` routes between
surfaces, all interactivity flows through a ~30-line typed-op dispatcher
(`morph · nudge · promote · drillInto · pin`), and a placeholder feature-spine →
debug-spine **hero morph** runs through the CSS View Transitions API at the locked motion
register (~350ms, ≥4 persistent anchors, reduced-motion fade fallback). The phase ends at a
**decision gate**: View Transitions carries the morph convincingly → Phase 3 builds real
canvases on this technique; it doesn't → switch to the keyed CSS panel-swap contingency
*before* any real canvas is built.

Everything later phases touch is exported here as a contract: the canonical design tokens,
the `appState` shape, the op vocabulary, the scenario-step shape, the anchor names, and the
single-file packaging rule. Get this phase right and every subsequent screen is a ~10-line
data slice; get it wrong and the mockup becomes a project.

## Position in Overall Plan

```
►Phase 1 (THIS PLAN)──► 2a ∥ 2b ∥ 2c ──► Phase 3 ──► 4 ∥ 5 ──► Phase 6
  render arch +          data  kit  spines  real morph             polish
  morph SPIKE
```

Phase 1 has **no dependencies** and **blocks everything**: 2a needs the `appState` shape,
2b needs the render contract and token set, 2c needs the spine/canvas contract, and Phase 3's
real hero morph reuses the technique proven (or replaced) here. It sits on the critical path
(1 → 2b → 3 → 5 → 6).

## Operating Mode

**HOLD SCOPE** — the delegation instruction is explicit ("plan exactly what the high-level
plan section says for this phase"), and the high-level plan bounds Phase 1 to skeleton +
spike: "a **placeholder** hero morph (a stub 'feature' spine shared-element-morphs into a
stub 'debug' spine)". No real surfaces, no real data, no component kit — those are Phases
2–3. Rigor goes into edge cases (file:// constraints, reduced motion, transition failure
modes), not extra features.

## Depends On (from prior plans)

No prior sub-phase plans exist — this is the first planning round. Inputs consumed are the
owner-locked decisions from `product-revamp-diecast-decisions-so-far.md`:

- **Stack:** no build step · import maps · htm+Preact (CDN, <15KB) · one in-memory JSON
  state · `location.hash` routing · CSS View Transitions morph · ~50-line scenario engine ·
  5 typed ops through one dispatcher · frozen `org.json` (Phase 2a).
- **Identity:** Diecast light world — cream `#F5F4F0`, ink `#1A1A28`, raspberry `#D6235C`,
  maker `#3B5BB0`, checker `#6B47B0`, IBM Plex Mono + DM Sans.
- **Motion register** (from playbook 02, locked): morph ~350ms, speed > spectacle, motion
  reveals layout, everything non-morph ≤150ms ease-out, `prefers-reduced-motion` → sub-200ms
  fade. Centralized as CSS custom properties.
- **Canvas anatomy:** three-tier shell (nav · CanvasFrame · ChatRail); canvas two-part
  anatomy (stage navigator + artifacts · work happening). `design-samples/app-shell.html`
  is the starting *reference, not boundary* (Steve-Jobs-bar re-derivation happens in 2b+).
- **Per-family stage vocabulary is NOT decided** — Phase 2c derives it. Phase 1 spine labels
  are throwaway placeholders and must be visibly marked as such in the data.

## Contracts This Phase Exports (downstream phases consume these)

These are the interfaces later planning rounds must adopt (or explicitly revise):

**1. File layout & packaging rule.** Build root `prototype/`; Phase 1 ships exactly one
file, `prototype/index.html`, with inline `<style>` and inline `<script type="module">`.
**Hard constraint discovered in planning:** `file://` pages block local ES-module imports
*and* `fetch()` (CORS origin `null`), so "opens from disk" forbids `import './state.js'`
and `fetch('data/org.json')`. Only CDN (https) imports via the import map, inline modules,
and *classic* `<script src>` tags work from disk. Downstream consequence flagged for
Phase 2a below.

**2. `appState` shape (v1 — Phase 2a extends, must not rename existing keys):**

```js
const appState = {
  route:   '#/goal/CAST-412',        // mirror of location.hash, set by router
  family:  'feature',                // 'feature' | 'debug'  (2a adds: 'spike' | 'data')
  goal:    { id: 'CAST-412', title: 'Add RBAC to checkout', crumb: 'northwind / goals' },
  spines:  {                         // PLACEHOLDER labels — Phase 2c replaces vocabulary
    feature: { placeholder: true, shape: 'segments',
               steps: ['Requirements','Exploration','Plan','Execution','Ship'], current: 3 },
    debug:   { placeholder: true, shape: 'loop', iter: { current: 2, budget: 3 },
               steps: ['Reproduce','Hypothesize','Experiment','Observe'], current: 1 },
  },
  nudge:   { who: 'Guide', do: 'Review CAST-412’s PR', why: 'checker flagged R02 — unblocks 2 queued tasks' },
  receipts: [],                      // decision receipt stubs, pushed by morph op
  pinned:  [],                       // canvas objects created by promote/pin ops
  drill:   null,                     // 'execution' | null — drillInto target
  chat:    { messages: [], scriptIndex: 0 },
};
```

**3. Op vocabulary (closed set, all changes route through one dispatcher):**
`morph:<family>` · `nudge:<id>` · `promote:<artifactId>` · `drillInto:<target>` ·
`pin:<artifactId>`. Chat/canvas controls carry `data-op="op:arg"`.

**4. Scenario step shape:** `{ narration: string, patch: (s) => void, transition?: 'morph' }`
walked by `advance()`; engine state lives in `appState.chat.scriptIndex` (replayable).

**5. View-transition anchor names (the persistent chrome set, prefix `vt-`):**
`vt-goal-header` · `vt-chat-rail` · `vt-nudge-card` · `vt-receipt-trail` · `vt-nav-rail`
(5 anchors; the ≥4 requirement with one spare).

**6. Motion tokens:** `--morph-duration: 350ms` · `--ease-morph: cubic-bezier(0.2,0.8,0.2,1)`
· `--motion-fast: 120ms` · reduced-motion fade `180ms`.

**7. Design tokens:** the `:root` block from `design-samples/app-shell.html` adopted
verbatim as the canonical names (`--cream --cream-deep --paper --ink --ink-60 --ink-35
--hairline --hairline-soft --rasp --rasp-08 --rasp-15 --maker --checker --ok --warn
--mono --sans`) plus the motion tokens above and `--radius-sm/md: 4px/8px`.

---

## Sub-phase 1.1: Skeleton — One File, One State, One Render

**Outcome:** `prototype/index.html` opens directly from disk in Chrome with zero console
errors; the three-tier shell (nav rail · CanvasFrame · ChatRail) renders in the Diecast
light world; `render(appState)` is the only paint path; ≥2 hash routes switch surfaces and
the back button works.

**Dependencies:** None
**Estimated effort:** 1 session (~2-3h)

**Verification:**
- Double-click `prototype/index.html` (no server, no compile) in Chrome → shell renders,
  DevTools console clean.
- Navigate `#/` → `#/goal/CAST-412` → `#/board` and back via browser back button; each
  route paints a distinct surface; `appState.route` tracks `location.hash`.
- View source: the only dependencies are CDN `<script>`/import-map URLs + Google Fonts;
  no `npm install`, no local file imports. Library payload <15KB (check Network tab,
  preact+htm gzipped).
- Cream `#F5F4F0` background, IBM Plex Mono headings, DM Sans body visibly applied.

Key activities:
- Create `prototype/index.html` with: import map pinning exact CDN versions
  (`https://esm.sh/preact@10.26.2`, `preact/hooks`, `htm@3/preact` — pin so a CDN bump
  can't break the demo mid-walkthrough), Google Fonts `<link>` for IBM Plex Mono
  (400/500/600) + DM Sans (400/500/700), and a `driver.js` import-map entry (usage deferred
  to Phase 6; included now so the <15KB budget is honest).
- Inline the canonical `:root` token block (contract #7) — lift names and values from
  `goals/product-revamp-diecast/exploration/design-samples/app-shell.html` verbatim, add
  the motion tokens (contract #6).
- Define `appState` (contract #2) inline with the placeholder spine data, each placeholder
  spine carrying `placeholder: true` so later phases can't mistake stub vocabulary for the
  Phase 2c-derived real thing.
- Implement the render spine (~20 lines): `routes = { '': Home, '#/goal': GoalCanvas,
  '#/board': BoardStub }` keyed on the first two hash segments; `App` resolves the route;
  `paint() = render(html`<${App}/>`, #app)`; `hashchange` listener + initial paint. All
  state updates go through explicit `paint()` calls (no component-local `useState` for
  app state) — this keeps the render synchronous inside `startViewTransition` later.
- Build the three-tier `AppShell`: left nav rail (brand lockup, stub goal list with family
  tags, workspace links — Board / Marketplace as dead links for now), center `CanvasFrame`
  slot, right `ChatRail` (fixed, persistent across routes). Use `app-shell.html` as layout
  reference only — markup is fresh htm components, not copied HTML.
- `GoalCanvas` placeholder content per the locked two-part anatomy: goal header (crumb +
  title + family pill), Guide attribution line stub (`◈ GUIDE` text treatment only — visual
  character design is 2b's deferred call), spine zone (renders from
  `appState.spines[family]`), nudge card stub (do + why-line), body split into
  stage-artifacts panel stub and work-happening list stub. `Home` = bare scenario-chooser
  stub (title + one link into the goal); `BoardStub` = heading + one-line placeholder
  (proves routing, nothing more — HOLD SCOPE).

**Design review:**
- **file:// constraint (architecture):** single-file inline is *forced*, not stylistic —
  local ES-module imports and `fetch()` fail from `file://`. The playbook 06 Step 1 snippet
  (`import { state } from './state.js'`) would break the disk-open verification; this plan
  deviates deliberately. Flagged for downstream phases (see Notes for Downstream Phases).
- **Network dependency:** CDN imports + Google Fonts require internet until Phase 6 inlines
  assets. Acceptable for the dev loop; add a one-line HTML comment in the file noting it.
- **Naming:** components PascalCase (`AppShell`, `CanvasFrame`, `ChatRail`), ops camelCase
  verbs, tokens kebab-case, route grammar `#/area/id` — consistent with playbook 06.
- **Security:** static file, no user input, no fetch — no flags.

## Sub-phase 1.2: Nervous System — Typed-Op Dispatcher & Scenario Engine

**Outcome:** All five typed ops (`morph · nudge · promote · drillInto · pin`) dispatch
through one ~30-line vanilla-JS dispatcher that wraps repaints in
`document.startViewTransition` (with support + reduced-motion guards), and a ~50-line
scenario engine walks an ordered `{narration, patch, transition}` script from the ChatRail's
"Next ▸" control. No canvas change happens outside the dispatcher.

**Dependencies:** Sub-phase 1.1
**Estimated effort:** 1 session (~2-3h)

**Verification:**
- Trigger each of the 5 ops (via chat-script buttons and/or a temporary dev strip of
  `data-op` buttons) — each visibly mutates the canvas and routes through the single
  `dispatch()` (verify with one `console.debug` line in dispatch; remove after).
- Count the dispatcher: ~30 lines of vanilla JS (excluding the op implementations).
- Click "Next ▸" repeatedly: the scenario walks start-to-finish, narration lines accumulate
  in the ChatRail, each step's patch applies, no broken intermediate state; reloading the
  page resets cleanly (engine state lives in `appState`).
- The morph script step includes its reverse ("treat it as a feature again") proving the
  morph is undoable via the same op.

Key activities:
- Implement the dispatcher (vanilla, ~30 lines) per playbook 02's keystone:

  ```js
  const OPS = { morph, nudge, promote, drillInto, pin };          // closed set
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  function dispatch(opStr) {                                       // "morph:debug"
    const [op, arg] = opStr.split(':');
    const apply = () => { OPS[op](arg, appState); paint(); };
    if (!document.startViewTransition || reduced.matches) return fade(apply);
    document.startViewTransition(apply);                           // shared-element morph
  }
  ```

  `fade(apply)` = the fallback path: apply synchronously, then a 180ms opacity ramp on the
  canvas container via `element.animate` (sub-200ms per the locked register). Event wiring:
  one delegated click listener on `[data-op]` (survives re-renders — don't bind per-element).
- Implement the five op functions as minimal-but-visible state mutations:
  - `morph(family)` — set `appState.family`, push a receipt stub onto `appState.receipts`
    (`{ level: 'L2', label: 'Reclassified feature→bug — debug loop', at: '17:52',
    rationale: '…' }`). The visual transition itself is 1.3's job.
  - `nudge(id)` — swap the nudge card's `do`/`why` content (stub: cycles between two canned
    nudges) proving the card re-renders from state.
  - `promote(artifactId)` — clone a stub chat artifact card into `appState.pinned` with the
    provenance line `from chat · Guide · <time>`; chat keeps a "Pinned ✓" back-stub.
  - `drillInto(target)` — toggle `appState.drill = 'execution'` rendering a stub execution
    panel (a labeled empty panel — the real drill-in lifts `run_node.html` in Phase 3).
  - `pin(artifactId)` — same mechanics as promote against a canvas-local stub object (kept
    as a distinct op because the real product distinguishes chat-artifact promotion from
    canvas pinning; here it proves the vocabulary is closed and complete).
- Build the scenario engine (~50 lines, an array walker — explicitly NOT a state machine):
  `script[]` of `{narration, patch, transition?}`; `advance()` bumps
  `appState.chat.scriptIndex`, appends the narration as a chat message, applies the patch,
  and repaints through `dispatch`-equivalent transition logic (steps with
  `transition: 'morph'` go through `startViewTransition`, others paint plain).
- Author the Phase-1 demo script (~6 steps): open goal → Guide nudge → user line *"this is
  actually a bug, not a feature"* → `morph:debug` + receipt (the SC-003 stand-in) →
  iteration badge bump (`iter 2/3`) → reverse morph (undo proof) → promote-the-receipt step.
- ChatRail: renders `chat.messages` + the "Next ▸" scripted-send control; canned agent
  replies carry `data-op` buttons so op-dispatch and scenario-advance are visibly the same
  grammar.

**Design review:**
- **Synchronous paint inside `startViewTransition` (correctness):** the callback must
  complete the DOM update before the transition snapshots. Preact's top-level `render()` is
  synchronous; component-local async state (hooks/setState) would not be. The 1.1 rule
  ("all app state updates via explicit `paint()`") exists exactly for this — keep it.
- **Error path — unknown op:** `dispatch` guards `OPS[op]` existence; unknown op logs a
  console warning and no-ops (zero silent failures, but a typo in a `data-op` attribute
  must not throw mid-demo).
- **Re-entrancy:** rapid double-clicks during an active transition — `startViewTransition`
  auto-skips the old transition; verify no visual glitch, otherwise debounce "Next ▸" for
  the transition duration.
- Naming: no flags — op set matches playbook 02 verbatim.

## Sub-phase 1.3: Proof — Hero Morph Spike & Decision Gate

**Outcome:** The placeholder feature-spine → debug-spine morph runs as a ~350ms
shared-element transition with ≥4 persistent anchors gliding (not crossfading), the
family-specific spine content crossfades between visibly different shapes (segment bar vs
loop band + `↺ iter 2/3` badge), a stub decision receipt appears, and
`prefers-reduced-motion` degrades to a 180ms fade. The **decision gate verdict is recorded**:
View Transitions carries the morph → locked for Phase 3; it can't → the keyed CSS panel-swap
contingency is adopted and documented.

**Dependencies:** Sub-phase 1.2
**Estimated effort:** 1 session (~2-3h), including gate evaluation

**Verification (this is the phase's headline verification):**
- Open `index.html` from disk; advance the script to the *"this is actually a bug…"* step;
  observe: goal header, chat rail, nudge card, receipt trail, nav rail **persist and
  glide/resize**; feature segment bar crossfades out, debug loop band + iteration badge
  crossfade in; total ~350ms (confirm in DevTools → Animations panel).
- The receipt pill (`L2 · Reclassified feature→bug`) appears in the receipt trail during/
  immediately after the morph; the reverse step morphs back without state loss.
- DevTools → Rendering → Emulate `prefers-reduced-motion: reduce` → the same step produces
  a ≤200ms fade, no sliding motion.
- Goal title and context never disappear mid-transition (reads as "same goal, new shape",
  not "new page").
- **Gate checklist** (all must pass to lock View Transitions for Phase 3):
  1. Anchors glide rather than crossfade (shared-element identity is real).
  2. No flash/flicker/layout jump at transition start or end.
  3. Runs from `file://` in Chrome (primary demo browser) — no protocol-specific breakage.
  4. Feels like ~350ms of *revealed layout*, not spectacle (the Linear/Raycast register).
  5. Reduced-motion fallback works.
- Verdict + evidence (a one-line note per checklist item) recorded in this plan's execution
  notes and appended to `product-revamp-diecast-decisions-so-far.md` (and
  `borderline-calls.md` if the fallback is taken).

Key activities:
- Tag the five anchors (contract #5) with `view-transition-name` in CSS. **Uniqueness rule:**
  each name must appear on exactly one rendered element per snapshot — a duplicate silently
  skips the whole transition. The placeholder canvases must therefore keep anchor elements
  mounted across both families (same component identity, different content).
- Style the transition at the locked register:

  ```css
  ::view-transition-group(*) {
    animation-duration: var(--morph-duration);
    animation-timing-function: var(--ease-morph);
  }
  ```

  Family-specific spine zones carry no `view-transition-name` → they get the root
  crossfade. Verify the default old/new crossfade reads cleanly; only add per-zone names
  if it doesn't.
- Make the two placeholder spines *visually contrasting shapes* (the SC-005 seed): feature =
  1B-style labeled segment bar (5 segments, accent-filled current); debug = 2B-style staged
  band with `↺ iter 2/3` badge. Placeholder labels rendered with a small `PLACEHOLDER`
  watermark tag so screenshots can't be mistaken for 2c-derived vocabulary.
- Render the stub decision receipt as a 6A-style pill in the receipt-trail anchor zone
  (pill + label + timestamp only; the 6B/6C disclosure ladder is Phase 2b's component).
- Run the gate checklist, record the verdict. **Contingency branch (if gate fails):** keyed
  CSS panel-swap — `data-family` attribute on `CanvasFrame`; family panels stacked in a CSS
  grid cell with opacity/transform transitions at the same motion tokens; the 4-5 anchors
  animated via FLIP (measure → mutate → invert → play with `element.animate`). Same
  dispatcher, same ops — only the transition mechanism inside `dispatch()` changes
  (~1 extra session). The op-vocabulary contract makes this swap cheap, which is why the
  gate is safe to resolve autonomously.
- Tidy for handoff: remove the dev op-button strip (or gate it behind `#/dev`), final
  console-clean pass, confirm library weight <15KB.

**Design review:**
- **Gate honesty:** the checklist criteria are written *before* running the spike (above),
  so the autonomous verdict is checkable rather than vibes. Item 4 (taste) is the soft one —
  judged against the "motion reveals layout, never performs" register, with the screenshot/
  recording kept as evidence.
- **Fallback parity:** the contingency keeps the identical op grammar and motion tokens, so
  no downstream phase plan changes shape either way — only Phase 3's "real morph" activity
  swaps its mechanism. Zero silent failure: the verdict is recorded in two places.
- **Anchor-count discipline:** 5 named anchors max in Phase 1. Naming everything makes
  everything glide and nothing read (playbook 02 pitfall 13).

## Build Order

```
Sub-phase 1.1 ──► Sub-phase 1.2 ──► Sub-phase 1.3 ──► GATE: morph verdict
 (skeleton)        (dispatcher +      (hero morph        ├─ pass → Phase 2a/2b/2c proceed
                    scenario engine)   spike)             └─ fail → adopt panel-swap, then proceed
```

**Critical path:** all three sub-phases, strictly sequential (1.2 needs 1.1's render spine;
1.3 needs 1.2's dispatcher). No parallelism inside this phase — it's 2-3 sessions of one
keystone. Total: 1–1.5 days, matching the high-level estimate.

## Design Review Flags

| Sub-phase | Flag | Action |
|-----------|------|--------|
| 1.1 | `file://` blocks local ES-module imports + `fetch()` — playbook 06's `./state.js` snippet would fail disk-open | Single-file inline architecture (locked); note carried to Phase 2a for `org.json` (see Notes for Downstream Phases) |
| 1.1 | CDN + Google Fonts require network until Phase 6 inlines | Accept; HTML comment in file; Phase 6 owns inlining |
| 1.1 | Unpinned CDN versions could break the demo later | Pin exact versions in the import map |
| 1.2 | Async renders inside `startViewTransition` would snapshot stale DOM | All app-state paints via synchronous top-level `render()`; no hooks for app state |
| 1.2 | Unknown/typo'd `data-op` mid-demo | Dispatcher guards + console.warn, no throw |
| 1.3 | Duplicate `view-transition-name` silently skips the transition | Uniqueness rule documented; anchors stay mounted across families |
| 1.3 | Subjective gate criterion ("convincing") under full autonomy | Pre-written 5-item checklist + recorded evidence; verdict logged in decisions-so-far |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| View Transitions can't deliver shared-element identity convincingly with this DOM structure | High | That's the spike's purpose: placeholder content, pre-written gate checklist, panel-swap contingency costed (~1 session) and decided *before* Phase 3 builds canvases |
| `file://` quirks surface late (module CORS, fetch) and force rework in Phase 2a+ | High | Constraint identified now and encoded as the packaging contract; disk-open is a verification step in every sub-phase |
| Placeholder spine labels leak downstream as "real" vocabulary, contradicting the owner's 2c directive | Med | `placeholder: true` in data + visible PLACEHOLDER watermark on the rendered spines |
| esm.sh outage during a demo/walkthrough | Low | Pinned versions cache well; Phase 6 inlining removes the dependency entirely; if it bites earlier, vendoring = paste the ~12KB preact+htm builds inline (1h) |
| Dispatcher/scenario engine over-engineering (XState creep) | Low | Hard line-budget targets in verification (~30-line dispatcher, ~50-line engine) |

## Open Questions

None blocking — full-autonomy mode resolved all judgment calls (logged below). Two items
remain deferred *by prior owner decision*, owned by later phases, listed for traceability:

- The Guide's visible character treatment → Phase 2b (USER-DEFERRED; Phase 1 renders a text
  stub only).
- Real per-family stage vocabulary → Phase 2c (owner directive; Phase 1 uses watermarked
  placeholders).

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| `docs/specs/_registry.md` (checked by high-level plan, re-confirmed) | all 7 specs govern cast-server runtime | None — FR-020: prototype is greenfield; no spec applies, none contradicted |

No `/cast-update-spec` action: the delegation explicitly excludes spec flows for this
deliverable, and the prototype is a design artifact, not product behavior (new product specs
are SC-006 downstream work, post-prototype).

## Notes for Downstream Phases

- **Phase 2a (`org.json`):** `fetch('data/org.json')` will NOT work from `file://`. Freeze
  the spine either as (a) an inline `<script type="application/json" id="org">` block in
  `index.html`, or (b) a *classic* script `prototype/org.js` setting `window.ORG = {...}`
  (classic `<script src>` works from disk; ES-module imports don't). Option (b) keeps the
  data file separate during the build and is the recommended default; Phase 6 inlines it
  regardless.
- **Phase 2b:** the token block, anchor names, motion tokens, and `appState` keys above are
  the canonical contract — extend, don't rename. The shell markup from 1.1 is explicitly
  *re-derivable* at the Steve-Jobs bar; the contracts are not.
- **Phase 3:** if the gate took the panel-swap contingency, only the transition mechanism
  inside `dispatch()` changes — the real-morph activity is otherwise unaffected.

## Decisions Made Autonomously

1. **Single-file inline `index.html` (no `state.js`, no fetched JSON)** — `file://` CORS
   blocks local module imports and fetch; deviates deliberately from playbook 06's snippet.
   Alternative (multi-file + local server) would violate the "opens from disk" verification.
2. **Phase-1 routes: `#/` (chooser stub) · `#/goal/CAST-412` · `#/board` (stub)** — minimal
   set proving the router (≥2 routes) without building Phase 5/6 surfaces.
3. **driver.js included in the import map now, usage deferred to Phase 6** — keeps the
   <15KB budget verification honest against the high-level plan's activity wording.
4. **`app-shell.html` `:root` token names adopted verbatim as the canonical token set** —
   it already encodes the owner-locked identity; inventing new names would create drift.
5. **Motion tokens fixed:** `--morph-duration: 350ms`, `--ease-morph:
   cubic-bezier(0.2,0.8,0.2,1)`, `--motion-fast: 120ms`, reduced-motion fade 180ms —
   composite of the locked register (02) and app-shell's easing.
6. **Anchor set = 5:** playbook 02's four (goal header, receipt/decision trail, chat rail,
   + nudge card standing in for the evidence strip until Phase 3 builds real evidence) +
   nav rail. Evidence-strip anchor name reserved for Phase 3.
7. **Placeholder spine labels:** feature = current 5-phase Diecast labels, debug =
   Reproduce→Hypothesize→Experiment→Observe — chosen for visual-shape contrast only, tagged
   `placeholder: true` + watermarked, honoring the owner's "2c derives the real vocabulary"
   directive.
8. **`pin` kept as a distinct op from `promote`** (not aliased) — the closed 5-op vocabulary
   is itself the contract being proven; collapsing them would change the grammar Phase 3+
   inherits.
9. **Undo = scripted reverse morph** (`morph:feature` step in the demo script) — satisfies
   playbook 02's "morph is undoable" cheaply; full undo semantics are not a Phase 1
   requirement (HOLD SCOPE).
10. **Exact CDN versions pinned** (esm.sh preact@10.26.x, htm@3) — demo stability over
    auto-upgrades.
11. **Morph decision gate resolved autonomously** per run config (owner pre-approved);
    objectivity preserved via the pre-written 5-item checklist, evidence retention, and
    verdict logging to decisions-so-far + borderline-calls.
12. **`cast-plan-review` auto-dispatch skipped** — the run configuration in
    `product-revamp-diecast-decisions-so-far.md` states "Plan review: skipped — cross-phase
    reconciliation only" (owner-approved). Recorded here instead of dispatching; rerun
    manually via `/cast-plan-review` against this file if wanted.
13. **Dev op-button strip allowed during 1.2, removed (or gated behind `#/dev`) in 1.3** —
    fastest way to verify all 5 ops without authoring extra script steps; must not survive
    into the showable artifact.

## Suggested Revisions to Prior Sub-Phases

None — this is the first detailed plan of the run. (The playbook-06 `./state.js` deviation
is recorded in Decisions #1 and Notes for Downstream Phases rather than here, since
playbooks are exploration inputs, not sub-phase plans.)
