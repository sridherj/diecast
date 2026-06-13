# Sub-phase 2b.1: Grammar — Kit Harness, Avatar Grammar & the Guide's Character

> **Pre-requisite:** Read `docs/execution/product-revamp-diecast-phase2b-component-kit/_shared_context.md`
> before starting. It carries the inherited Phase 1 contracts, the 9 exported contracts, the
> binding constraints (NO TESTS, file:// legality, single-file packaging, fixture discipline,
> failure policy), and FULL AUTONOMY mode. This plan does not repeat them.

> **FULL AUTONOMY MODE (owner-approved):** never ask the user questions, never pause for approval
> gates, never go idle waiting for input. At decision gates pick the recommended option and
> document it inline in the sub-phase output. Propagate this exact autonomy directive verbatim
> into any child agent you dispatch.

## Objective

Lay the grammar foundation every later 2b component reuses: add the `#/kit` harness route, define
the inline `FIXTURES`, build the one `Avatar` primitive (circle/square/diamond), build
`ColleagueCard` (both densities from one fixture, **zero field drift**), add the token extensions
(contract #7), and **make the one USER-DEFERRED craft call this phase owns — the Guide's visible
character treatment** — by rendering three candidates on `#/kit`, judging at the Steve-Jobs bar,
keeping one, deleting the others. This sub-phase is **on the critical path** (C5: a second failure
stops-and-reports).

## Dependencies
- **Requires completed:** Phase 1 — Keystone (BUILT: appState v1, the 5-op dispatcher, the
  scenario engine, the hero morph + gate all PASSED). This plan assumes the Phase 1 skeleton
  exists in `prototype/index.html`. If Phase 1 execution somehow has not run, execute it first
  (`docs/execution/product-revamp-diecast-phase1-keystone/`).
- **Assumed codebase state:** `prototype/index.html` is the built Phase 1 single file with the
  three-tier shell, hash router (`#/` · `#/goal/CAST-412` · `#/board`), the synchronous `paint()`,
  the 5 vt- anchors on zone wrappers, and the dispatcher + scenario engine.

## Scope

**In scope:**
- Add the `#/kit` route (contract #8) to the Phase 1 router: a vertical gallery page — mono
  section headings, each component rendered from named `FIXTURES` entries, caption = fixture key.
  **Gate it out of demo chrome** (no nav-rail link; reachable by hash only).
- Define `FIXTURES` inline (single-file rule, C3): canonical-vocabulary stubs only (`CAST-412`,
  `crud-orchestrator`/`CO`, `crud-compliance-checker`/`CC`, rule codes `M04/S03/R02`, rework
  `1/3`, stat `99.9% · 2 loops · 505 runs`, `@you/SJ`). **No ad-hoc names** (C4 — the 2a swap is
  mechanical).
- Build the `Avatar` primitive: `{kind, initials, glyph?}` → circle (human, `--ink` fill), square
  (maker, `--maker` outline), square (checker, `--checker` fill), diamond (Guide). One component;
  size variants via CSS custom property. Get the **optical sizing** right (diamond and circle read
  as the same visual mass as the square).
- Build `ColleagueCard` (the five-element lockup): `Avatar` + name/slug (mono) · in-card
  paired-checker element (bracket-tie device from preso s8b, **never a second card**) · 3-segment
  rework meter (`rework.used/budget`) · reversibility badge (`L1/L2/L3` mono pill, token mapping
  from contract #7) · in-flight pill. `density: 'card'` adds the stat footer
  (`99.9% compliant · 2 loops · 505 runs`); `density: 'line'` is the same elements compressed to
  one row. **Same field order both densities — one render function with conditional wrappers, not
  two markups.**
- Design the Guide's character (the USER-DEFERRED call): render the three candidates (A diamond /
  B ink monogram seal / C typographic-only) side-by-side on `#/kit`, judge against pre-written
  criteria, keep one, delete the other two. Build the chosen `GuideMark` + the chat-voice / nudge-
  attribution / receipt-attribution treatments.
- Add the token extensions (contract #7) to `:root` with a one-line `/* 2b additions */` comment.
- Re-derive card spacing/type scale from first principles per the build directive (the gallery
  samples are reference, not spec).

**Out of scope (do NOT do these — HOLD SCOPE):**
- `StageSpine`, `EvidenceBlock` — **2b.2a.**
- `Decision` ladder, `NudgeCard` (the real one), `EscalationRail`, `AutonomyDial` — **2b.2b.**
  (2b.1 leaves the Phase 1 nudge stub in place; 2b.2b replaces it.)
- Composing the signature screen / running the slop gate — **2b.3.**
- Real canvases, real org data, real per-family vocabulary, board/marketplace surfaces — Phases 2a/2c/3/5.
- Any test file / harness / CI (C1). Any `fetch()` / local ES-module import (C2).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `prototype/index.html` | Modify (additive) | Built Phase 1 single file |
| `docs/plan/product-revamp-diecast-decisions-so-far.md` | Append | Decisions ledger — record the chosen Guide treatment + any sample deviations |

## Detailed Steps

### Step 2b.1.1: Add the token extensions (contract #7)
- In the `:root` block add, under a `/* --- 2b additions --- */` comment:
  `--fail: #B22439;` (test-red, distinct from raspberry). Define the L-level badge mapping as a
  small convention (L1 → `--ink-35`, L2 → `--warn`, L3 → `--rasp`) — implement via class or a
  tiny lookup, your call; document it. Confidence glyphs `●/◐/○` are a render convention, not a
  token (no percentage anywhere).
- **Accent discipline:** the only new color is `--fail`. The Guide treatment must introduce no new
  hue. Grep the 2b CSS for raw hex — everything except this one `:root` addition goes through tokens.

### Step 2b.1.2: Define `FIXTURES` inline
- Add a `FIXTURES` SCREAMING_SNAKE root object in the inline module. Seed the canonical agent
  fixtures matching contract #2 verbatim:
  - `CO` / `crud-orchestrator` (maker, `pairedWith: 'crud-compliance-checker'`, stats
    `99.9/2/505`, autonomy `L2`, rework `1/3`, `inflight: {label: 'CAST-412 · iteration 2/3'}`,
    state `working`).
  - `CC` / `crud-compliance-checker` (checker).
  - one `human` fixture (`@you`/`SJ`).
  - one **maker-without-`pairedWith`** fixture (to exercise the visible broken-state fallback).
- No ad-hoc names. When 2a's `org.js` lands, wiring is `window.ORG`-for-`FIXTURES` — a data-source
  swap, not a reshape.

### Step 2b.1.3: Build the `Avatar` primitive
- `Avatar({kind, initials, glyph?})` → one component, four kinds:
  - `human` → filled circle, `--ink` fill, initials.
  - `maker` → square, `--maker` outline + glyph.
  - `checker` → square, `--checker` fill.
  - `guide` → diamond (square rotated 45°) — square-family but instantly distinct (contract #6).
- Size variants via a CSS custom property (e.g. `--avatar-size`), not per-call markup.
- **Optical sizing:** the diamond and circle must read as the same visual mass as the square (a
  45°-rotated square has a smaller bounding silhouette — compensate). This is the single most
  reused atom; get it right.

### Step 2b.1.4: Build `ColleagueCard` (one function, two densities)
- `ColleagueCard({agent, density})` with the five-element lockup, same field order both densities:
  avatar+glyph · paired-checker (in-card bracket-tie, never a second card) · 3-segment rework
  meter · reversibility badge · in-flight pill.
- `density: 'card'` adds the stat footer (`99.9% compliant · 2 loops · 505 runs`);
  `density: 'line'` compresses the same elements to one row (for activity logs / dispatch trees).
- **Enforced by one render function with conditional wrappers, not two markups** — a `grep` must
  confirm no second lockup implementation exists.
- **Broken-state fallback (zero-silent-failure):** an agent without `pairedWith` must render a
  *visible* flag (e.g. `→ paired: ⚠ none`), not a silently-solo card (pairing is load-bearing per
  US6.S5). `inflight: null` renders a visible absence, not a blank gap.
- Pure-function rule: reads `props` only, never `appState`.

### Step 2b.1.5: Add the `#/kit` harness route (contract #8)
- Register `#/kit` in the router; render a vertical gallery (`kit-`-prefixed chrome classes):
  mono section headings, each component rendered from named `FIXTURES` entries, caption = fixture
  key. **No nav-rail link** — hash-only reachable, hidden from demo nav.
- Sections this sub-phase fills: **Avatar** (4 kinds) · **ColleagueCard** (card + line densities,
  each shown *in context*: card inside a board-card frame, line inside an activity-row frame) ·
  **GuideMark + the three Guide voice contexts** (chat header, nudge attribution, receipt byline).
- **Contract #9:** components on `#/kit` render twice/many — they must NOT carry
  `view-transition-name`s (those live on shell zone wrappers only). Verify no kit component emits
  an anchor name.

### Step 2b.1.6: Design the Guide's character (the USER-DEFERRED craft call)
- **Write the selection criteria first** (before judging): distinct from worker agents at a glance ·
  no mascot/anthropomorphic theater (playbook 04 pitfall 8) · survives 16px rendering · does not
  spend raspberry (the Guide is persistent; raspberry means needs-you).
- Render three candidates side-by-side on `#/kit`:
  - **A (recommended default): the diamond.** `◈`-shaped ink-filled diamond mark + mono `GUIDE`
    wordmark; chat messages get a hairline left-rule + cream-deep tint (voice = typography +
    structure, not color); nudge card carries `◈ Guide` attribution; receipts get
    `decided with ◈ Guide` byline.
  - **B: ink monogram seal** — circle-with-diamond-knockout mark (a "stamp" reading, diecast metaphor).
  - **C: typographic-only** — no mark; pure mono-voice (`GUIDE ▸`) with a distinctive indent grammar.
- Judge at the Steve-Jobs bar, **keep one, delete the other two**. Default to A unless B or C
  clearly wins against the criteria. Record the pick + the reasoning in `decisions-so-far.md`.
- Build the chosen treatment in all three contexts (chat header, nudge attribution, receipt byline)
  as reusable CSS voice classes + a `GuideMark({size})` component.

## Verification

### Automated Tests (permanent)
- **None.** Constraint C1 forbids tests. Do not create any test file.

### Validation Scripts (temporary)
- None that run code. Static checks: `node --check` of the inline module (extract or eyeball);
  `grep` for raw hex outside `:root`; `grep` confirming a single `ColleagueCard` lockup; `grep`
  confirming no `view-transition-name` on kit components.

### Manual Checks (the only verification — open from disk in Chrome and observe)
1. **Disk open, `#/kit`, clean console:** open `prototype/index.html` from disk → navigate `#/kit`
   → a sectioned gallery renders (Avatar / ColleagueCard / GuideMark). DevTools Console → **zero
   errors**.
2. **Avatar grammar:** all four kinds render; the diamond reads as the same visual mass as the
   circle and square (optical sizing), instantly distinct as "a different kind of agent".
3. **Density-drift check (the high-level plan's explicit check):** the 4C card and the 4B line
   render from the *same* fixture object — visually confirm identical fields in identical order
   (avatar+glyph · paired-checker · rework meter · reversibility badge · in-flight pill). Code-
   structural check: one `ColleagueCard` function, density via prop — `grep` confirms no second
   lockup implementation.
4. **Broken-state fallback:** render the no-`pairedWith` fixture → the card **visibly flags** the
   missing checker (not a silent solo card). `inflight: null` shows a visible absence.
5. **Guide distinctness (the playbook 01 flash test, self-administered):** the chosen Guide
   treatment renders in all three contexts and is distinguishable from maker/checker/human at a
   glance **with no labels**. Survives 16px. Spends no raspberry, introduces no new hue.
6. **Token discipline:** grep the 2b CSS → the only raw hex added is `--fail` in `:root`;
   everything else goes through tokens.
7. **Contract #9:** no kit component carries a `view-transition-name` (grep).

### Success Criteria (binary — every item must pass)
- [ ] `#/kit` route added, hash-only (no nav link), renders Avatar + ColleagueCard + GuideMark sections from `FIXTURES`; console clean from `file://`.
- [ ] `Avatar` is one component, four kinds, size via CSS property; diamond/circle/square optically balanced.
- [ ] `ColleagueCard` renders both densities from one fixture with zero field drift; **one** lockup function (grep-verified).
- [ ] Maker-without-checker fixture renders a **visible** broken-state flag (zero-silent-failure).
- [ ] The Guide's character is chosen from 3 rendered candidates, the other two deleted, the pick + reasoning recorded in `decisions-so-far.md`; treatment renders in chat/nudge/receipt and is label-free distinct.
- [ ] Token extensions (contract #7) added under a `2b additions` comment; no raw hex outside `:root`; no new hue from the Guide.
- [ ] Components read props only (pure-function rule); no kit component carries a `vt-` anchor (contract #9).
- [ ] Phase 1 still works: `#/goal/CAST-412` and the hero morph are unbroken (2b.1 is additive — confirm the keystone didn't regress).

## Execution Notes
- **This is the foundation — 2b.2a, 2b.2b, and 2b.3 all reuse `Avatar`, `ColleagueCard`, the
  tokens, and `FIXTURES`.** Get the prop contracts and the density discipline right here or the
  drift surfaces downstream.
- **The Guide call is the deferred owner decision** — the owner deferred it to "seeing options
  rendered." Supply A as the recommended default; only deviate if B or C clearly beats the
  pre-written criteria. Record the decision; do not leave all three in the file.
- **Pure-function rule is load-bearing:** kit components read props only. A component that reaches
  for `appState` fakes the `#/kit` isolation guarantee and breaks Phase 3 reuse — flag it as a defect.
- **Single-file growth:** use banner comments + `kit-` class prefix so a grep separates harness
  chrome from product styles before Phase 6 packaging.
- **Spec-linked files:** none. This sub-phase modifies only `prototype/index.html` + appends to the
  decisions ledger — greenfield design artifacts covered by no spec.
- **Failure policy (C5 — 2b.1 is CRITICAL):** retry once with refined steps; a **second** failure
  → **stop and report** (do not continue to Group 2 on a broken foundation). Log the exact failure
  + what was tried in the output and the manifest Notes.
