# Sub-phase 6.1: Front Door — Scenario Chooser & Guided Walkthroughs

> **Pre-requisite:** Read
> `docs/execution/product-revamp-diecast-phase6-polish-showability/_shared_context.md` before
> starting this sub-phase. The binding constraints there are not optional.

## Objective

A stranger can land on `#/`, understand the five things the demo can show, click one, and be carried
through it: the FR-002 scenario chooser is **real** (replacing the Phase 1 stub), each of the five
flows has a **driver.js anatomy tour**, and a **presenter-facing demo-script overlay** shows the
current flow's scripted beats. The demo self-navigates (SC-002 precondition). This is the **root of
the critical path** (6.1 → 6.2 → 6.3a → 6.4) — nothing downstream can start until it lands.

## Dependencies
- **Requires completed:** Phases 4 + 5 executed — all ten Phase-5 routes + the four goal canvases +
  all five `SCRIPTS` (`feature, debug, spike, data, hiring`) exist in `prototype/index.html`.
- **Assumed codebase state:** `prototype/index.html` (~5750 lines as of Phase 5 close) carries the
  full kit, the closed 5-op dispatcher, the `6×1` vt- anchor set, the scenario engine
  (`{narration, patch, transition?}` + `advance()`, index at `appState.chat.scriptIndex`, keyed by
  `appState.chat.scriptKey`), and the Phase 1 **`#/` chooser stub** (bare route, outside the
  three-tier shell). driver.js is **pinned in the import map** but **unused** (Phase 1 deferred all
  usage here); no driver.css `<link>` exists yet.

## Estimated effort
1 session (~3h).

## Scope
**In scope:**
- The real FR-002 chooser screen at `#/` (five scenario cards + standalone-areas row + GuideMark
  intro), replacing the Phase 1 stub.
- driver.js wiring: the CDN `<link>` for driver.css + the mandatory `tour-*` token-override block.
- Five tours (`TOURS` keyed identically to `SCRIPTS`), 5–8 stops each, on new `data-tour` attributes.
- The demo-script overlay (`appState.demoScriptOpen`, `s`-key + nav-footer toggle).

**Out of scope (do NOT do these):**
- The density/consistency pass and the slop-gate sweep (6.2) — author the new surfaces; **6.2 gates
  them**. Do author the new copy em-dash-free per FR-018 (it will be tone-gated in 6.2).
- The single-file inliner / dist (6.3a) and the SC-006 map (6.3b).
- Any ORG generator batch (Phase 6 authors none — chooser/tour/demo copy is presentation chrome);
  any hand-edit of `org.js`; any new op; any new SCRIPTS key; any test file.
- Any new appState key **other than** `demoScriptOpen`; any new top-level ORG key.

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `prototype/index.html` | Modify | Carries the Phase 1 `#/` stub + all Phase 1–5 surfaces; gains the real chooser, the `tour-*`/`choose-*`/`demo-*` sections, the driver.css `<link>`, the `TOURS` map + `data-tour` attributes, the demo-script overlay, and the `demoScriptOpen` appState key |

## Detailed Steps / Key Activities

### Step 6.1.1: The chooser screen (`#/`, bare route — no nav/chat shell)
Replace the Phase 1 stub with five **verb-first scenario cards**:
- "Follow a feature" → CAST-412, `SCRIPTS.feature`
- "Chase a bug" → CAST-431, `SCRIPTS.debug`
- "Run a spike" → CAST-452, `SCRIPTS.spike`
- "Answer a data question" → CAST-461, `SCRIPTS.data`
- "Hire an agent" → `#/hire`, `SCRIPTS.hiring`

Card title / goal-id / one-line hook derive from `ORG.goals` (**drift rule: goal titles never
retyped**). The verb labels and a static `SCENARIOS = [{key, verb, route, scriptKey, blurb}]`
descriptor are **demo chrome — inline in `index.html`**. Each card: the **primary affordance enters
the flow** (sets `chat.scriptKey`, resets `chat.scriptIndex` to 0, navigates — **plain handler, no
new op**); a **secondary "Guided tour" link** enters the flow AND starts that flow's driver.js tour.
CSS prefix `choose-*`. Typographic cards only (mono goal-ids, the family-shape glyph reused from
`StageSpine`); **no new illustrations.**

### Step 6.1.2: Standalone-areas row
Below the cards, a row linking the non-scenario surfaces: Board (`#/board`) · Marketplace
(`#/marketplace`) · Agent ops (`#/agent/crud-orchestrator`) · Layer-2 (`#/layer2`) · Requirements doc
(`#/reqs/CAST-412`) · Decision trail (`#/decisions/CAST-412`). **`#/kit` stays hidden.** The Guide
opens the screen with one line in its voice (diamond `GuideMark`) — the persistent character is
present at the front door.

### Step 6.1.3: driver.js wiring (the gap no prior phase covered)
- Import driver.js from the **Phase 1 import-map pin**.
- Add the driver.js **v1 stylesheet via CDN `<link>`** (file://-legal — https CDN; see design
  review). **This is consumption of Phase 1's deferral, not a Phase 1 revision.**
- Add a **`tour-*` token-override block** restyling popovers: `--paper` background, `--ink` text, mono
  titles, raspberry progress/active accents, `--radius-sm/md`, no shadows beyond the existing
  elevation idiom. **Stock driver.js styling (white, rounded, generic sans) would fail the slop gate
  on sight** — the override is **mandatory**; a tour-popover-open capture is item #2 in the 6.2 gate
  list.

### Step 6.1.4: Five tours (`TOURS` keyed like `SCRIPTS`)
`TOURS = {feature, debug, spike, data, hiring}`, **5–8 stops each**, anchored on new `data-tour="…"`
attributes added to **shell zone wrappers + key components** (attributes, **not** CSS classes, so
6.2's styling refactors can't silently break tours; and **no `data-tour` carries a vt- name**). Tours
explain **anatomy, not story**: where the WHAT lives, the stage spine + its family shape, evidence,
the chat rail, where decisions surface, the dial/escalation where relevant. **The last stop of every
tour points at the chat advance control** ("the demo advances here") — handing off to the scenario
engine, which owns the narrative. **Tours never call `advance()`.** Set driver.js `animate: false`
under `prefers-reduced-motion`.

> **Builder taste calls (left open per the Phase 6 plan — all reversible in minutes):** exact tour
> stop counts/copy per flow (within the 5–8 band) and the chooser's family-shape glyph treatment on
> cards. Pick either; document the pick in the progress-log line.

### Step 6.1.5: The demo-script overlay (the "both" half of the owner's walkthrough default)
A dismissible presenter panel (`demo-*` prefix; paper surface, ink text) toggled by the **`s` key**
and a small control in the **nav-rail footer**; renders `SCRIPTS[chat.scriptKey]` as a numbered beat
list (narration + a one-line hand-authored talking point per beat) with the `chat.scriptIndex` beat
**highlighted**; advancing chat moves the highlight. State = the new additive
**`appState.demoScriptOpen` boolean**; **plain handler**; reload resets. Positioned **bottom-left** so
it never covers the chat rail. Copy obeys FR-018 (**hyphens not em dashes, no GPT-isms**) — it will be
tone-gated in 6.2.

> **Edge (design review):** the `s` shortcut binds **only outside text inputs** — the prototype has
> none, but the FR-017 parity terminal pane fakes one, so **guard the handler on `event.target`**. A
> tour started on a route whose element set doesn't match (user navigated mid-tour) → driver.js skips
> missing stops natively; verify it degrades quietly rather than erroring.

## Verification

> **NO TESTS (binding):** every check below is **manual click-through / static observation**. In an
> autonomous run with no browser, satisfy each via the strongest static evidence (`node --check` of
> the extracted module, grep audits, a throwaway `/tmp` logic harness that is never committed) and
> record a non-blocking human-eyeball carry-forward for any rendered-pixel item. **Do not flag missing
> tests.**

**Verification (manual, from disk) — verbatim from the plan:** Open `prototype/index.html` via
`file://` in Chrome.
- `#/` shows five scenario cards + a standalone-areas row; **every card and link routes correctly and
  resets the right script** (`scriptKey` set, `scriptIndex` 0).
- Start each of the five tours: popovers appear on the **right elements**, styled in Diecast tokens
  (**visibly NOT stock driver.js**), next/prev work, Esc dismisses.
- Press `s` inside a flow: the demo-script overlay lists that flow's beats with the current beat
  highlighted; advancing chat moves the highlight; `s` again (or ✕) closes it.
- With **reduced-motion emulated**, tour transitions don't animate.
- Reload anywhere → clean reset, **no console errors**.

### Success Criteria (binary — every item must pass or carry forward with reason)
- [ ] `#/` renders five verb-first cards (titles/ids from `ORG.goals`) + the standalone-areas row +
      the GuideMark intro line; the Phase 1 stub is gone.
- [ ] Each card's primary affordance enters its flow (sets `chat.scriptKey`, resets `scriptIndex` 0,
      navigates) and the secondary "Guided tour" link also starts that flow's tour — both via **plain
      handlers, no sixth op**.
- [ ] driver.css `<link>` present (https CDN); the `tour-*` token-override block restyles popovers so
      they read Diecast, not stock.
- [ ] `TOURS = {feature, debug, spike, data, hiring}` (keyed = `SCRIPTS`), 5–8 stops each, anchored on
      `data-tour` **attributes**; the last stop of each points at the chat advance control; **tours
      never call `advance()`**; `animate:false` under reduced motion.
- [ ] The demo-script overlay toggles via `s` + the nav-footer control, renders
      `SCRIPTS[chat.scriptKey]` with the current beat highlighted, reload-resets; `s` handler guarded
      on `event.target`.
- [ ] Exactly **one** new appState key (`demoScriptOpen`); no new op; no new SCRIPTS key; no ORG batch;
      `org.js` untouched.
- [ ] `data-tour` attributes carry **no** vt- name; vt- anchors unchanged (`6×1`); the chooser stays a
      **bare route** (no shell wrapper); `node --check` clean.

## Design review (verbatim from the plan)
- ⚠ **driver.css was never planned by any prior phase:** Phase 1 pinned the driver.js *module* but no
  phase added its stylesheet. Action (in activities): CDN `<link>` + token override block. **Not a
  prior-phase revision** — Phase 1 explicitly deferred all usage here.
- ⚠ **Stock-tour slop risk:** default driver.js popovers (white, rounded, generic sans) are exactly
  the generic aesthetic the gate exists to kill. The `tour-*` override block is **mandatory**, and one
  tour-popover-open capture is in the 6.2 gate list.
- **Naming:** `data-tour` attributes, `TOURS` keyed = `SCRIPTS` keys, `choose-*`/`tour-*`/`demo-*`
  prefixes — all follow established conventions. ✓
- **Architecture:** no new ops, no new script keys, one additive appState key; chooser stays a bare
  route (Phase 1 precedent), so no vt- anchor duplication risk (anchors live on shell zone wrappers,
  which the chooser doesn't render). ✓
- **Edge:** keyboard `s` only binds outside text inputs (guard on `event.target`); tour start on a
  route whose element set doesn't match → driver.js skips missing stops natively (verify it degrades
  quietly).

### Design Review Flags (this sub-phase's rows, verbatim from the plan's consolidated table)
| Sub-phase | Flag | Action |
|-----------|------|--------|
| 6.1 | driver.css never planned by any prior phase | Add CDN `<link>` + `tour-*` token override block (in 6.1 activities) |
| 6.1 | Stock driver.js popover styling = instant slop-gate failure | Token override mandatory; tour-popover capture #2 in the 6.2 gate list |
| 6.1 | `s` shortcut could fire inside the parity fake-terminal | Guard handler on `event.target` |

## Execution Notes
- **No ORG batch:** chooser/tour/demo copy is **presentation chrome inline in `index.html`** (Phase 6
  plan Decision 7). The only ORG reads are goal titles/ids on the chooser cards (drift rule). Do not
  touch `generate-org.mjs` or `org.js`.
- **Tours teach anatomy; scripts carry the story** (Decision 3) — keeps one narrative engine (the
  Phase 1 scenario engine) and makes tours safe to run at any script index.
- **`data-tour` not classes** (Decision 4) — 6.2 *will* cause styling refactors; attributes survive
  them. Preserving `data-tour` through 6.2's density fixes is a 6.2 rule and a 6.4 audit item.
- **CF3 (de-em-dash):** author all new copy (chooser blurbs, tour stop text, demo talking points)
  **em-dash-free from the start** (FR-018) so 6.2's tone pass finds nothing new to fix.
- **Spec-linked files:** none — greenfield (FR-020); no `/cast-update-spec`.
- **Plan review:** SKIPPED per run config — do not dispatch `/cast-plan-review` or any reconciliation
  pass.
- **Failure policy (critical path):** 6.1 is the root critical-path node — a second failure here is
  **stop-and-report**, not log-and-continue.
- **If a flagged-but-taken taste call ships** (e.g. an unusual glyph treatment), append a numbered
  entry to `docs/plan/product-revamp-diecast-borderline-calls.md` (continuing from #15).
