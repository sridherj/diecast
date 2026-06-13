# Sub-phase 1.2: Nervous System — Typed-Op Dispatcher & Scenario Engine

> **Pre-requisite:** Read `docs/execution/product-revamp-diecast-phase1-keystone/_shared_context.md`
> before starting. It carries the 7 exported contracts (especially Contract 3 — the closed op
> vocabulary, and Contract 4 — the scenario step shape), the binding constraints (NO TESTS,
> file:// legality, single-file packaging), and FULL AUTONOMY mode. This plan does not repeat them.

## Objective

Give the skeleton a nervous system: all five typed ops (`morph · nudge · promote · drillInto ·
pin`) dispatch through **one** ~30-line vanilla-JS dispatcher that wraps repaints in
`document.startViewTransition` (with support + reduced-motion guards), and a ~50-line scenario
engine walks an ordered `{narration, patch, transition}` script from the ChatRail's "Next ▸"
control. **No canvas change happens outside the dispatcher.** This proves the closed op
grammar Phase 3+ inherits and the replayable scripted-demo spine — without yet doing the
visual hero morph (that's 1.3; here `morph` just mutates state + pushes a receipt stub).

## Dependencies
- **Requires completed:** Sub-phase 1.1.
- **Assumed codebase state:** `prototype/index.html` exists and opens clean from disk. It has `appState` (Contract 2), the hash router, the three-tier `AppShell`, and the synchronous top-level `paint()` rule (no component-local `useState` for app state). The nav rail, goal header, nudge card, receipt trail, and chat rail are mounted as persistent structure.

## Scope

**In scope (edit the single file `prototype/index.html` only):**
- The dispatcher (~30 lines vanilla JS): `dispatch(opStr)` splits `"op:arg"`, looks up a closed `OPS` map, applies the op + `paint()`, wrapped in `startViewTransition` with support + reduced-motion guards; a `fade(apply)` fallback path; one **delegated** click listener on `[data-op]`.
- The five op functions (`morph · nudge · promote · drillInto · pin`) as minimal-but-visible state mutations.
- The scenario engine (~50 lines): an array walker (`advance()`), NOT a state machine; engine state in `appState.chat.scriptIndex`.
- The Phase-1 demo `script[]` (~6 steps) including the `morph:debug` step, the receipt, the iteration-badge bump, and a **reverse** `morph:feature` step (undo proof).
- ChatRail wiring: render `chat.messages` + the "Next ▸" scripted-send control; canned agent replies carry `data-op` buttons.
- A **temporary** dev strip of `data-op` buttons (one per op) to verify all five ops directly. (Removed/gated in 1.3 — see Execution Notes.)
- A single `console.debug` line inside `dispatch` for the verification (removed after).

**Out of scope (do NOT do these — HOLD SCOPE):**
- `view-transition-name` CSS tagging of the anchors, the *visual* glide/crossfade, the contrasting spine **shapes** (segment bar vs loop band), the `PLACEHOLDER` watermark, the decision-gate checklist + verdict — **all Phase 1.3.** Here `morph` only flips `appState.family` + pushes a receipt; whatever the existing 1.1 spine renderer shows is fine.
- Real undo semantics beyond the scripted reverse step. Full undo is not a Phase 1 requirement.
- Any state machine / XState. Hard line-budget: ~30-line dispatcher, ~50-line engine.
- Tests / harness / CI (C1). `fetch()` / local imports / extra files (C2/C3).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `prototype/index.html` | Modify | Exists from 1.1: appState + router + AppShell + synchronous paint. Add the dispatcher, ops, scenario engine, demo script, ChatRail send control, temporary dev op-strip. |

## Detailed Steps

### Step 1.2.1: Implement the dispatcher (~30 lines, vanilla)
```js
const OPS = { morph, nudge, promote, drillInto, pin };          // closed set (Contract 3)
const reduced = matchMedia('(prefers-reduced-motion: reduce)');

function dispatch(opStr) {                                       // e.g. "morph:debug"
  const [op, arg] = opStr.split(':');
  if (!OPS[op]) { console.warn('unknown op:', opStr); return; } // guard — no throw mid-demo
  const apply = () => { OPS[op](arg, appState); paint(); };
  console.debug('dispatch', opStr);                             // REMOVE after verification
  if (!document.startViewTransition || reduced.matches) return fade(apply);
  document.startViewTransition(apply);                          // shared-element morph (visuals in 1.3)
}

function fade(apply) {                                          // fallback: apply then 180ms opacity ramp
  apply();
  const frame = document.getElementById('canvas-frame');       // the CanvasFrame container
  frame && frame.animate([{ opacity: 0.0 }, { opacity: 1 }], { duration: 180, easing: 'ease-out' });
}
```
- **Event wiring — exactly one delegated listener** (survives re-renders; do NOT bind per element):
  ```js
  document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-op]');
    if (el) dispatch(el.getAttribute('data-op'));
  });
  ```
- Keep the dispatcher body ~30 lines excluding the op implementations. If it grows, you're over-engineering.

### Step 1.2.2: Implement the five op functions (minimal but visible)
- **`morph(family)`** — set `appState.family = family`; push a receipt stub onto `appState.receipts`:
  `{ level: 'L2', label: 'Reclassified feature→bug — debug loop', at: '17:52', rationale: '…' }`.
  (The *visual* transition is 1.3's job. Here, the family flip + receipt push is all.)
- **`nudge(id)`** — swap the nudge card's `do`/`why` content (cycle between two canned nudges) to prove the card re-renders from state.
- **`promote(artifactId)`** — clone a stub chat artifact card into `appState.pinned` with provenance `from chat · Guide · <time>`; the chat keeps a `Pinned ✓` back-stub.
- **`drillInto(target)`** — toggle `appState.drill = 'execution'`, rendering a stub execution panel (a labeled empty panel — the real drill-in lifts `run_node.html` in Phase 3).
- **`pin(artifactId)`** — same mechanics as `promote` but against a canvas-local stub object. Keep it a **distinct** op (Contract 3 — not aliased; the closed vocabulary is the contract being proven).

### Step 1.2.3: Build the scenario engine (~50 lines, an array walker)
- `script` is an array of `{ narration, patch, transition? }` (Contract 4).
- ```js
  function advance() {
    const i = appState.chat.scriptIndex;
    if (i >= script.length) return;
    const step = script[i];
    appState.chat.messages.push({ from: 'narration', text: step.narration });
    appState.chat.scriptIndex = i + 1;
    const apply = () => { step.patch(appState); paint(); };
    if (step.transition === 'morph' && document.startViewTransition && !reduced.matches) {
      document.startViewTransition(apply);
    } else if (step.transition === 'morph') {
      fade(apply);
    } else {
      apply();
    }
  }
  ```
- Engine state lives **only** in `appState.chat.scriptIndex` → reloading the page resets cleanly. Explicitly NOT a state machine.

### Step 1.2.4: Author the Phase-1 demo `script[]` (~6 steps)
1. **Open goal** — narration sets the scene; patch is a no-op or focuses the goal.
2. **Guide nudge** — narration from the Guide; patch swaps the nudge card (calls the `nudge` mutation or sets it directly).
3. **User line** — *"this is actually a bug, not a feature"* (narration only).
4. **`morph:debug` + receipt** — `transition: 'morph'`; patch calls `morph('debug', s)` (flips family, pushes the receipt — the SC-003 stand-in).
5. **Iteration badge bump** — patch sets `appState.spines.debug.iter = { current: 2, budget: 3 }` (shows `iter 2/3`).
6. **Reverse morph (undo proof)** — `transition: 'morph'`; patch calls `morph('feature', s)`. Then a final **promote-the-receipt** step (patch calls `promote` against the receipt) is acceptable as step 6b if you want the 6th visible op exercised in-script.
- The reverse step is mandatory: it proves the morph is undoable *via the same op* (verification item below).

### Step 1.2.5: ChatRail send control + canned replies
- Render `appState.chat.messages` in the ChatRail.
- Add the **"Next ▸"** control wired to `advance()` (a `data-op` is fine, or a direct `onClick={advance}` — but if you use `data-op`, route it through the same delegated listener for grammar consistency; "Next ▸" is scenario-advance, ops are state ops — keep them visibly the *same grammar* per the plan).
- Canned agent replies in the script carry `data-op="op:arg"` buttons so op-dispatch and scenario-advance read as one grammar.

### Step 1.2.6: Temporary dev op-strip (verification aid)
- Add a small strip of five buttons, each `data-op="morph:debug"` / `nudge:n2` / `promote:a1` / `drillInto:execution` / `pin:c1`, so each of the five ops can be triggered directly without authoring extra script steps.
- **This strip must not survive into the showable artifact** — 1.3 removes it or gates it behind `#/dev`. Mark it in the source with a clear comment: `<!-- DEV OP STRIP — remove or gate behind #/dev in 1.3 -->`.

## Verification

### Automated Tests (permanent)
- **None.** Constraint C1. Do not create any test file.

### Validation Scripts (temporary)
- The `console.debug('dispatch', opStr)` line inside `dispatch` is the only instrumentation — used in manual check #1, then removed.

### Manual Checks (open from disk in Chrome and observe)
1. **All 5 ops route through `dispatch`:** Trigger each op (dev strip and/or chat-script buttons). Each **visibly mutates** the canvas, and each logs one `dispatch …` line — confirming a single dispatch path. (Then remove the `console.debug` line.)
2. **Dispatcher size:** Count the `dispatch` + `fade` + delegated-listener code — ~30 lines of vanilla JS excluding the op implementations. The scenario engine ~50 lines. If materially larger, simplify (no state machine).
3. **Scenario walks start-to-finish:** Click "Next ▸" repeatedly → the script walks to the end, narration lines accumulate in the ChatRail, each step's patch applies, no broken intermediate state. **Reload the page → resets cleanly** (scriptIndex back to 0, messages cleared).
4. **Morph is undoable via the same op:** The script's `morph:debug` step and its reverse `morph:feature` step both run through the same `morph` op — confirm the canvas returns to the feature state with no state loss.
5. **Error path — unknown op:** Click a button with a typo'd `data-op` (e.g. `data-op="morf:debug"`) → console **warns**, no throw, demo continues. (Add a throwaway button to test, then remove it.)
6. **Re-entrancy:** Rapidly double-click "Next ▸" / a morph button during an active transition → `startViewTransition` auto-skips the stale transition; confirm no visual glitch. If a glitch appears, debounce "Next ▸" for `--morph-duration`.
7. **Console still clean** (besides the intentional `dispatch` debug line, which you then remove) and **no app state in Preact hooks** — confirm the dispatcher's `paint()` is the only repaint trigger.

### Success Criteria (binary — every item must pass)
- [ ] All 5 ops (`morph · nudge · promote · drillInto · pin`) dispatch through the **one** `dispatch()`; nothing mutates the canvas outside it.
- [ ] Dispatcher ~30 lines vanilla; scenario engine ~50 lines; neither is a state machine.
- [ ] `dispatch` guards unknown ops with `console.warn` + no-op (no throw).
- [ ] `startViewTransition` is used when supported and not reduced-motion; `fade()` (180ms opacity ramp) is the fallback.
- [ ] One **delegated** `[data-op]` click listener (not per-element bindings) — survives re-renders.
- [ ] "Next ▸" walks the ~6-step demo script start-to-finish; narration accumulates; reload resets cleanly (state in `appState.chat.scriptIndex`).
- [ ] The script includes the `morph:debug` step **and** the reverse `morph:feature` step (undo proof).
- [ ] The `console.debug` instrumentation line is **removed** after verification; the dev op-strip is clearly marked for removal/gating in 1.3.
- [ ] Console clean; no app state held in component-local hooks.

## Execution Notes
- **Synchronous paint inside `startViewTransition` (the correctness keystone, carried from 1.1):** the callback must finish the DOM update before the transition snapshots. Preact's top-level `render()` is synchronous; component-local async state (hooks/setState) is not. Keep every app-state update flowing through the explicit `paint()`. If you ever feel tempted to add a `useState` for app data, that's the bug 1.3 will pay for.
- **One delegated listener, not per-element.** Re-renders replace DOM nodes; per-element handlers leak and break. The single delegated `[data-op]` listener is deliberate.
- **The dev op-strip is a verification crutch, not a deliverable.** Mark it loudly; 1.3 removes or gates it. The showable artifact must not ship a raw op-button strip.
- **Receipt stub timestamps:** hard-code (e.g. `'17:52'`) — there is no clock requirement and `Date.now()`-style nondeterminism only makes screenshots noisy.
- **Spec-linked files:** none. Only `prototype/index.html` is touched (greenfield, no spec).
- **Failure policy (C5):** retry once with refined instructions on failure; second failure → mark partial, log the exact gap (which op/engine behavior failed, what was tried) in the output and manifest Notes.
