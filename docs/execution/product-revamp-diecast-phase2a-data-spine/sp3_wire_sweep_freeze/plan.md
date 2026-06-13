# Sub-phase 3 (2a.3): Wire, Sweep, Freeze

> **Pre-requisite:** Read `docs/execution/product-revamp-diecast-phase2a-data-spine/_shared_context.md`
> before starting. It carries the binding constraints (NO TESTS, `file://` legality, F4
> single-source rule), the appState v1.1 contract, and the canonical-vocabulary table.
>
> **Also read first (binding context the runner MUST load):**
> `docs/plan/product-revamp-diecast-decisions-so-far.md` and
> `docs/plan/2026-06-11-product-revamp-diecast-phase2a-data-spine.md`.

## Objective

Make `prototype/index.html` load the spine from disk (`file://`) so **every canonical token
it renders comes from `window.ORG`**. Bring appState to **v1.1** (four families, `org` key,
derived spines). Run the **drift grep** and prove it clean. Declare the spine **frozen** in
`meta` and append the 2a summary to `decisions-so-far`. This is the phase's headline
verification and the freeze that makes the spine the single source of truth for all
downstream phases.

## Dependencies

- **Requires completed:** sp2 (2a.2) — full content-complete `org.js` — **and Phase 1
  execution** (the real `index.html` to wire).
- **DEGRADED PATH (if Phase 1 execution hasn't landed):** 2a runs parallel with 2b and
  Phase 1's build may still be in flight. If `index.html` does not yet have the real Phase 1
  app to wire, **deliver 2a.1–2a.2 plus a ~15-line wiring patch spec** against Phase 1's
  contracted shapes, and **fold the wiring into Phase 1's completion**. Record this as a gap
  and continue (off-critical-path failure policy). Note: at execution time `prototype/index.html`
  **does exist** (~33KB, Phase 1 morph gate PASSED), so the full path is expected.
- **Assumed codebase state:** content-complete `org.js` from 2a.2; Phase 1 `index.html` with
  appState v1, the 5-op dispatcher, the scenario engine, and the morph step.

## Scope

**In scope:**
- Add `<script src="data/org.js"></script>` to `index.html` ahead of the inline module.
- Boot wiring: `appState.org = window.ORG`; populate `appState.goal` from `ORG.goals`;
  derive all four `spines` from `ORG.stageModels` + `spine_state`; replace the inline nudge
  stub; route guard for all four goal ids; missing-`window.ORG` error banner.
- Refactor the morph step to push a receipt **derived from** `ORG.decisions`
  (`DEC-CAST-412-03`) instead of the hardcoded stub.
- Run the drift grep; convert any literal that crept into `index.html` to spine reads.
- Freeze: set `meta.frozen_at` (via the generator), regenerate, commit; append the 2a
  appendix to `decisions-so-far.md`.

**Out of scope (do NOT do these):**
- New routes, components, canvases, or scenario scripts beyond the four-family route guard —
  those are Phase 3/4/5. The non-feature goals render the **shell with placeholder spine
  shape** only.
- Changing `org.js` content (other than `meta.frozen_at`) — author is frozen; only the
  freeze stamp changes, via the generator.
- Real per-family stage vocabulary (2c).
- Any test file, suite, harness, or CI (banned).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `prototype/index.html` | Modify | Phase 1 app; add one `<script src>` line + spine-read boot wiring + morph-receipt refactor |
| `prototype/data/_build/generate-org.mjs` | Modify | Set `meta.frozen_at` constant |
| `prototype/data/org.js` | Regenerate | `meta.frozen_at` stamped |
| `docs/plan/product-revamp-diecast-decisions-so-far.md` | Modify (append) | Add ~15-line 2a appendix |

## Detailed Steps

### Step 3.1: Load the spine (classic script before the module)
Add `<script src="data/org.js"></script>` to `index.html` **ahead of** the inline
`<script type="module">` (classic script — the only `file://`-legal local data path, per
Phase 1 contract #1). Load order guarantees `window.ORG` exists when the module runs.

### Step 3.2: Boot wiring (spine reads replace stubs)
- `appState.org = window.ORG`.
- Populate `appState.goal` from `ORG.goals['CAST-412']`.
- Replace Phase 1's inline `spines` literals with **all four families derived from
  `ORG.stageModels` + the relevant goal's `spine_state`** (2c's mapping rule:
  `stageModels.<f>.steps.map(s => s.shortLabel ?? s.label)`), preserving Phase 1's appState
  spine shape exactly.
- Replace the inline nudge stub with the **feature goal's nudge** (`ORG.goals['CAST-412'].nudge`).
- Route guard so `#/goal/<id>` resolves **any of the four** goal ids
  (`CAST-412 · CAST-431 · CAST-452 · CAST-461`).
- **Guard (zero silent failures):** if `window.ORG` is missing (script tag deleted / file
  moved), render a **visible one-line error banner** instead of silently painting stubs.

### Step 3.3: Refactor the morph-receipt step
The Phase 1 demo-script morph step (`morph:debug`) currently pushes a hardcoded receipt stub.
Refactor it to push a receipt **derived from** `ORG.decisions` (`DEC-CAST-412-03`) — level,
label, time all spine-derived. Receipt shape keeps Phase 1's keys (`{level,label,at,rationale}`)
**plus** `decision_id`. `advance()` must remain unbroken.

> If Phase 1 execution landed first, keep the stub's wording verbatim
> (`label: 'Reclassified feature→bug — debug loop', at: '17:52'`) so this swap is **invisible
> in the demo**.

### Step 3.4: Drift sweep
Run the drift grep and hunt down any literal that crept into `index.html` during Phase 1
(expected: the appState stubs being replaced in this sub-phase) and convert to spine reads:
```bash
grep -rn -e 'CAST-4' -e 'M04\|S03\|R02' -e '99\.9\|99\.4\|505 runs\|312 runs' \
  -e 'crud-orchestrator' -e '1/3' -e 'Northwind\|northwind' \
  prototype/ --include='*.html' --include='*.js'
```
**Every hit must be in `data/org.js` or `data/_build/`** — zero hits in `index.html`.
Record the command in the freeze note; it reruns in Phase 6's final sweep.

> **Sanctioned exception:** if Phase 2b has landed and its `#/kit` fixture block hand-types
> canonical vocabulary (by design, "so 2a wiring is a data swap"), those fixture literals are
> the **one allowlisted** grep exception until the 2b data swap happens. Note the exception in
> the freeze record.

### Step 3.5: Freeze
- Set `meta.frozen_at` (a constant in the generator), regenerate `org.js`, commit.
- Append the **2a decision summary** (~15 lines) to
  `docs/plan/product-revamp-diecast-decisions-so-far.md`: file layout, schema keys,
  canonical-value table pointer, step-id indirection, freeze policy + the 2c `stageModels`
  exception.

## Verification

> This is the **phase's headline verification** (from the high-level plan) — **all manual
> click-through**, per the NO-TESTS rule. No test files, no suite, no CI.

### Manual Click-Through (open from disk in Chrome)
1. **Goal canvas reads from the spine:** open `prototype/index.html` from disk → console
   clean; the goal canvas renders CAST-412's **title, crumb, nudge, and spine from
   `window.ORG`**. Verify the binding: edit a title in the generator, regenerate, reload →
   the screen changes.
2. **All four families load:** `#/goal/CAST-431`, `#/goal/CAST-452`, `#/goal/CAST-461` each
   render the shell with their family's **placeholder spine shape** (proves all four families
   load; real canvases are Phase 3/4).
3. **Demo script still walks end-to-end:** the Phase 1 demo script walks through; the morph
   receipt now renders from atom `DEC-CAST-412-03` (level, label, time all spine-derived) and
   `advance()` is unbroken.

### Drift Grep (zero ad-hoc naming)
```bash
grep -rn -e 'CAST-4' -e 'M04\|S03\|R02' -e '99\.9\|99\.4\|505 runs\|312 runs' \
  -e 'crud-orchestrator' -e '1/3' -e 'Northwind\|northwind' \
  prototype/ --include='*.html' --include='*.js'
```
Every hit is in `data/org.js` or `data/_build/` (zero hits in `index.html`, modulo the
sanctioned `#/kit` exception if 2b landed first).

### Success Criteria (binary — every item must pass)
- [ ] `index.html` loads `data/org.js` via a classic `<script src>` before the inline module.
- [ ] Console is clean on open from disk.
- [ ] CAST-412 canvas renders title/crumb/nudge/spine from `window.ORG` (edit-regenerate-reload
      changes the screen).
- [ ] `#/goal/CAST-431|452|461` each render the shell with their placeholder spine shape.
- [ ] The demo script walks end-to-end; the morph receipt derives from `DEC-CAST-412-03`;
      `advance()` unbroken.
- [ ] Missing-`window.ORG` renders a visible error banner (not silent stubs).
- [ ] Drift grep: zero canonical-token hits in `index.html` (only `org.js`/`_build/`, plus the
      sanctioned `#/kit` exception if applicable).
- [ ] `meta.frozen_at` is set in `org.js`.
- [ ] `decisions-so-far.md` carries the 2a appendix.

## Design Review

- **Single-global discipline:** `window.ORG` is the only global the spine introduces, and
  it's `Object.freeze`d at the top level — accidental mutation by a later phase's component
  throws in strict mode rather than silently drifting the demo. (Deep-freeze is deliberately
  skipped: one `Object.freeze` per top-level value is enough for a demo, and 2c edits the
  generator and regenerates anyway.)
- **Load-order failure path:** classic script before module script guarantees `window.ORG`
  exists when the module runs; the missing-ORG banner covers the remaining failure mode.
- **Naming:** no flags — route grammar and appState keys unchanged from Phase 1 (only
  extended).

## Design Review Flags (from the plan)

| Flag | Action |
|------|--------|
| `fetch('org.json')` regression risk when someone "cleans up" later | Classic-script rule restated in `org.js` header comment + freeze note |
| Missing `window.ORG` would silently render Phase 1 stubs | Explicit error banner; stubs deleted, not shadowed |

## Execution Notes

- **Do not regress Phase 1 contracts:** appState v1 keys may be **added to** but never
  renamed; the op vocabulary stays closed at 5; vt- anchors stay on shell zones. appState
  v1.1 only *extends* v1.
- **Classic script must precede the module** — if it loads after, `window.ORG` is undefined
  when the module runs and the banner fires. Verify ordering.
- The morph-receipt swap must be **invisible in the demo** — keep the Phase 1 stub's wording
  verbatim in the atom if Phase 1 landed first.
- **DEGRADED PATH:** if `index.html` isn't wireable yet, deliver the ~15-line wiring patch
  spec instead and fold it into Phase 1's completion; log the gap, do not block.
- **Freeze is the deliverable's seal** — after this sub-phase, `org.js` values are frozen;
  downstream phases extend additively via the generator only (F4). The `stageModels` region
  is the sole exception (2c).
- **Spec-linked files:** none (FR-020 greenfield). No `/cast-update-spec` action.
