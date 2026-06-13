# Product Revamp: Diecast — Phase 2b: Component Kit & Aesthetic Lock

## Overview

This phase builds the ~8 reusable components every downstream screen is assembled from, and
**locks the signature visual language at the Steve-Jobs bar**: the five-element colleague-card
lockup (one component, two densities), the E1–E5 EvidenceBlock family, the 3B nudge card, the
6A→6B→6C decision disclosure ladder, the 7A escalation rail, the 8A autonomy dial, the four
stage-spine shapes, and — the one USER-DEFERRED craft call this phase owns — **the Guide's
visible character treatment**. The phase ends with an **aesthetic lock**: one composed signature
screen (the upgraded `#/goal/CAST-412` canvas) passes both cast-preso slop-gate checkers
(`not-generic` / `not-ai-aesthetic`), de-risking SC-004 before any mass screen production in
Phases 3–5.

The key insight carried from exploration: build the kit once and every downstream screen becomes
a ~10-line data slice (playbook 06); the components are *forced by the owner's locked picks*
(design-decisions.ai.md), so this phase is execution craft — re-deriving layout/spacing from
first principles per the owner's build directive — not component invention.

## Position in Overall Plan

```
Phase 1 (DONE: planned) ──► 2a ∥ ►2b (THIS PLAN)∥ 2c ──► Phase 3 ──► 4 ∥ 5 ──► Phase 6
  render arch + morph        data  component kit  spines  real canvases        polish
```

Phase 2b sits on the **critical path** (1 → 2b → 3 → 5 → 6). It runs parallel with 2a (data
spine) and 2c (stage-vocabulary research): components are built against small inline stub
fixtures matching `appState` v1, then wired to the real `org.json` when 2a lands (a data-source
swap, not a reshape — see the fixture discipline in 2b.1). Phase 3 consumes every component
here; Phase 5 reuses the lockup, decision ladder, escalation rail, and dial on the
board/ticket/marketplace surfaces.

## Operating Mode

**HOLD SCOPE** — the delegation instruction is explicit ("plan exactly what the high-level plan
section says for this phase, at high practical detail"). The high-level plan bounds 2b to the
eight named components + token/Guide lock + slop-gate proof on one screen. No real canvases
(Phase 3), no real spine vocabulary (Phase 2c), no org data authoring (Phase 2a), no board/
marketplace surfaces (Phase 5). Rigor goes into prop contracts, density-drift prevention, accent
discipline, and the slop gate — not extra components.

## Depends On (from prior plans)

From **Phase 1 — Keystone** (`docs/plan/2026-06-11-product-revamp-diecast-phase1-keystone.md`),
adopted unchanged:

- **Packaging:** one file, `prototype/index.html`, inline `<style>` + inline
  `<script type="module">`; only https CDN import-map imports work from disk (`file://` blocks
  local module imports and `fetch()`). **All 2b components live inline in `index.html`.**
- **Design tokens (canonical names, extend-don't-rename):** `--cream --cream-deep --paper --ink
  --ink-60 --ink-35 --hairline --hairline-soft --rasp --rasp-08 --rasp-15 --maker --checker
  --ok --warn --mono --sans` + motion tokens (`--morph-duration: 350ms`,
  `--ease-morph`, `--motion-fast: 120ms`, reduced-motion fade 180ms) + `--radius-sm/md`.
- **`appState` v1 keys** (must not rename): `route · family · goal · spines · nudge{who,do,why}
  · receipts[] · pinned[] · drill · chat`. The 2b NudgeCard consumes `nudge{who,do,why}` as-is;
  the StageSpine consumes the `spines.<family>` shape (`{placeholder, shape, steps, current,
  iter?}`).
- **Op vocabulary (closed):** `morph · nudge · promote · drillInto · pin` via `data-op="op:arg"`.
  Kit components that carry actions emit `data-op` attributes; they never call `dispatch()`
  directly.
- **vt- anchors:** `vt-goal-header · vt-chat-rail · vt-nudge-card · vt-receipt-trail ·
  vt-nav-rail`; uniqueness rule (a duplicate name silently kills the whole transition).
- **Render rule:** components are pure functions of props; all paints go through the top-level
  synchronous `paint()`.
- Routes so far: `#/` · `#/goal/CAST-412` · `#/board` (stub).

From **owner-locked decisions** (`product-revamp-diecast-decisions-so-far.md` +
`design-decisions.ai.md`):

- Identity: Diecast light world; raspberry is the *single* status accent meaning needs-you;
  maker `#3B5BB0` / checker `#6B47B0` on **agent chrome only**; IBM Plex Mono + DM Sans.
- Component picks 1B · 2B · 3B · 4C+4B · 5B · 6A→6B→6C ladder · 7A · 8A
  (`design-samples/component-gallery.html` is the canonical visual reference — inspiration,
  not spec, per the build directive).
- E1–E5 evidence catalog blessed as working defaults, revisit-on-sight; rule: outcome first,
  proof one click in, trace two clicks in; never a bare green badge.
- The Guide: name locked ("the Guide", slug `cast-guide`); must read as a visibly distinct
  character vs worker agents; **visual treatment is this phase's deferred craft call**.
- Avatar grammar constraint: "humans=circles, agents=squares — or better, if a better idea
  preserves the same legibility."
- Hard slop-gate: no glass/gradient/glow/orb; `not-generic` / `not-ai-aesthetic` checkers gate
  the signature screen.
- L3 budget discipline and "ranked but nothing pre-selected" escalation guardrail.

## Contracts This Phase Exports (Phases 2a/2c/3/4/5 consume these)

**1. The component roster (8 components, all pure `(props) → vdom` functions inside
`index.html`):**

| # | Component | Pick | Prop contract (summary) |
|---|-----------|------|-------------------------|
| 1 | `ColleagueCard` | 4C card + 4B line | `{ agent, density: 'card'\|'line' }` — same fields, same order, both densities |
| 2 | `EvidenceBlock` | E1–E5 | `{ kind: 'E1'..'E5', data }` — one component, per-kind sub-renderer |
| 3 | `StageSpine` | 1B/2B + timebox + pipeline | `{ spine }` where `spine.shape: 'segments'\|'loop'\|'timebox'\|'pipeline'` |
| 4 | `NudgeCard` | 3B with why-line | `{ nudge: {who, do, why} }` — appState v1 shape verbatim |
| 5 | `Decision` ladder | 6A pill → 6B callout → 6C trail row | `{ atom, layer: 'pill'\|'callout'\|'row' }` — one decision atom, three projections |
| 6 | `EscalationRail` | 7A hero/outline/ghost | `{ escalation }` — ranked weight, nothing pre-selected |
| 7 | `AutonomyDial` | 8A segmented + legend | `{ value, trust: {compliancePct, runs} }` |
| 8 | `GuideMark` / Guide voice treatment | (this phase's design call) | `{ size }` + CSS voice treatment classes for chat/nudge/receipt contexts |

**2. The agent fixture shape** (what `ColleagueCard` renders from; 2a's `org.json` agents must
be supersets of this):

```js
{ id: 'CO', slug: 'crud-orchestrator', kind: 'maker',     // 'maker'|'checker'|'human'|'guide'
  pairedWith: 'crud-compliance-checker',                   // makers carry their checker
  stats: { compliancePct: 99.9, loops: 2, runs: 505 },
  autonomy: 'L2',                                          // reversibility badge
  rework: { used: 1, budget: 3 },                          // 3-segment meter
  inflight: { label: 'CAST-412 · iteration 2/3' } | null,  // in-flight pill
  state: 'working' }                                       // 'working'|'idle'|'blocked'
```

**3. The decision atom** — playbook 05 Step 1 schema adopted **verbatim** (field names
`id · phase · title · reversibility · rationale · options_considered[] · consequences ·
revisit_if · originating_agent · author_type · timestamp · status · supersedes/superseded_by ·
spike_ref · influenced[]`). All three ladder layers render from one atom. Phase 5's trail and
Phase 3's chips reuse this shape unchanged.

**4. EvidenceBlock per-kind data shapes:**

```js
E1: { screenshots: [{label}], tests: {passed, failed, coverageDelta},
      checks: [{code: 'M04', label, status: 'resolved'|'flagged'}], pr: {id, label} }
E2: { hypotheses: [{id, statement, prediction, observation, verdict: 'confirmed'|'refuted'|'open'}] }
E3: { test: {name}, before: {status: 'fail', excerpt}, after: {status: 'pass', excerpt} }
E4: { answer, confidence: 'H'|'M'|'L', dataPoints: [], spike_ref: {decisionId, label} }
E5: { headline: {kind: 'chart'|'table', svg|rows}, provenance: {sources[], query}, version: {n, date} }
```

**5. Spine shape extension:** Phase 1's `spines.<family>` gains two `shape` values —
`'timebox'` (`{timebox: {budget: '3h', used: '1h 40m'}}` — field name aligned with 2c's
`stageModels` contract) and `'pipeline'` (data-stage nodes). Labels remain `placeholder: true`
+ watermarked until 2c delivers real vocabulary; per the Phase 2c plan's contract,
`appState.spines.<family>.steps` stays `string[]` (rich step objects live only in
`stageModels` org data), so 2c's vocabulary lands as a data edit, zero component change. 2c's
flag channel applies in reverse too: if 2c research contradicts one of the four locked shape
variants, it flags for reconciliation rather than silently changing shape.

**6. Avatar grammar (locked by this phase):** human = filled circle (initials) · maker agent =
square, `--maker` outline + glyph · checker agent = square, `--checker` fill · **the Guide =
diamond (square rotated 45°)** — square-family ("an agent") but instantly distinct ("a different
kind of agent"). Recommended default, subject to the 2b.1 rendered-options pass.

**7. Token extensions (extend, never rename):** `--fail: #B22439` (test-red for E3/E2 —
semantic red, distinct from raspberry which stays the needs-you accent) · L-level badge mapping
`L1 → --ink-35 · L2 → --warn · L3 → --rasp` · confidence glyph convention `● high / ◐ med /
○ low` (never a percentage).

**8. The `#/kit` harness route** — the component gallery inside the prototype (see 2b.1).
Downstream phases verify new component states by adding fixtures here.

**9. vt- anchor placement rule:** `view-transition-name`s are applied **by the shell's zone
wrappers, never by kit components**. A kit component rendered twice (as on `#/kit`) must not
carry an anchor name, or the duplicate silently kills every morph.

---

## Sub-phase 2b.1: Grammar — Kit Harness, Avatar Grammar & the Guide's Character

**Outcome:** `#/kit` renders every component slot from inline fixtures with a clean console
from `file://`; the avatar grammar (circle/square/diamond) is implemented as one `Avatar`
primitive; `ColleagueCard` renders both densities from the same fixture object with zero field
drift; the Guide has a chosen, rendered character treatment (mark + chat voice + nudge
attribution + receipt attribution) selected from 3 rendered candidates at the Steve-Jobs bar.

**Dependencies:** Phase 1 (sub-phases 1.1–1.3 executed; if Phase 1 execution hasn't run yet,
2b.1 starts by executing it — this plan assumes the Phase 1 skeleton exists)
**Estimated effort:** 1 session (~3h)

**Verification:**
- Open `prototype/index.html` from disk → navigate `#/kit` → a sectioned gallery renders:
  Avatar (4 kinds), ColleagueCard (card + line densities, each shown *in context*: card inside
  a board-card frame, line inside an activity-row frame), GuideMark + the three Guide voice
  contexts. Console clean.
- **Density-drift check:** the 4C card and 4B line render from the *same* fixture object;
  visually confirm identical fields in identical order (avatar+glyph · paired-checker ·
  rework meter · reversibility badge · in-flight pill). Code-structural check: one
  `ColleagueCard` function, density via prop — `grep` confirms no second lockup implementation.
- The Guide treatment renders in all three contexts (chat message header, nudge card
  attribution, decision receipt byline) and is distinguishable from maker/checker/human at a
  glance with no labels (the playbook 01 flash test, self-administered).
- A maker card always shows its paired checker (`→ paired: <checker>`) — render a fixture
  without `pairedWith` and confirm the card visibly flags it rather than silently omitting
  (zero-silent-failure: pairing is load-bearing per US6.S5).

Key activities:
- Add the `#/kit` route to the Phase 1 router: a vertical gallery page — mono section headings,
  each component rendered from named `FIXTURES` entries, caption = fixture key. Gate it out of
  demo chrome (no nav-rail link; reachable by hash only). This is the "renders from a data prop
  in isolation" harness the high-level plan requires, with no build step.
- Define `FIXTURES` inline (single-file rule): canonical-vocabulary stubs only — `CAST-412`,
  `crud-orchestrator`/`CO`, `crud-compliance-checker`/`CC`, rule codes `M04/S03/R02`, rework
  `1/3`, stat line `99.9% · 2 loops · 505 runs`, `@you/SJ`. **No ad-hoc names** — when 2a's
  `org.json` lands, wiring is a data-source swap.
- Build the `Avatar` primitive: `{kind, initials, glyph?}` → circle (human, `--ink` fill),
  square (maker, `--maker` outline), square (checker, `--checker` fill), diamond (Guide). One
  component; size variants via CSS custom property. This is the single most reused atom — get
  the optical sizing right (diamond and circle must read as the same visual mass as the square).
- Build `ColleagueCard` with the five-element lockup: `Avatar` + name/slug (mono) ·
  paired-checker element (in-card, bracket-tie device from preso s8b — never a second card) ·
  3-segment rework meter (`rework.used/budget`) · reversibility badge (`L1/L2/L3` mono pill,
  token mapping from contract #7) · in-flight pill. `density: 'card'` adds the stat footer
  (`99.9% compliant · 2 loops · 505 runs`); `density: 'line'` is the same elements compressed
  to one row for activity logs/dispatch trees. Same field order both densities — enforced by
  one render function with conditional wrappers, not two markups.
- **Design the Guide's character (the USER-DEFERRED call):** render three candidates on `#/kit`
  side-by-side, judge at the Steve-Jobs bar, keep one, delete the others:
  - **A (recommended default): the diamond.** `◈`-shaped ink-filled diamond mark, mono `GUIDE`
    wordmark; chat messages from the Guide get a hairline left-rule + cream-deep tint (voice =
    typography + structure, not color); nudge card carries `◈ Guide` attribution; receipts get
    `decided with ◈ Guide` byline.
  - **B: ink monogram seal** — circle-with-diamond-knockout mark (a "stamp" reading, diecast
    metaphor).
  - **C: typographic-only** — no mark; the Guide is pure mono-voice (`GUIDE ▸`) with a
    distinctive indent grammar.
- Selection criteria (write before judging): distinct from worker agents at a glance ·
  no mascot/anthropomorphic theater (playbook 04 pitfall 8) · survives 16px rendering ·
  doesn't spend raspberry (the Guide is persistent; raspberry means needs-you).
- Add the token extensions (contract #7) to the `:root` block; add a one-line comment marking
  the 2b additions.
- Re-derive spacing/type scale for cards from first principles per the build directive — the
  gallery samples are reference, not spec; if a cleaner rhythm beats `component-gallery.html`,
  take it (document in the decisions appendix at execution time).

**Design review:**
- **Naming:** components PascalCase, fixtures SCREAMING_SNAKE for the root object, kebab-case
  CSS classes prefixed `kit-` for harness-only chrome (so a grep separates harness from product
  styles before Phase 6 packaging). Consistent with Phase 1.
- **Architecture:** pure-function rule — kit components read **props only**, never `appState`
  directly. This is what makes `#/kit` honest isolation and Phase 3 reuse trivial. Flag any
  component that reaches for global state as a defect.
- **Accent discipline (the playbook 01 hard rule):** maker/checker hues on agent chrome only;
  raspberry only where it means needs-you (L3 badge, blocked-state pill). The Guide treatment
  must not introduce a new hue. Check: grep the 2b CSS for raw hex values — everything goes
  through tokens.
- **Error path:** missing fixture fields (no `pairedWith`, `inflight: null`) render visible
  fallbacks, not blank gaps — a maker without a checker is a *broken state* and must look like
  one.

## Sub-phase 2b.2a: Shape & Proof — Stage-Spine Variants + the EvidenceBlock Family

**Outcome:** `StageSpine` renders all four shapes from data (1B segment bar · 2B staged band +
↺ iter counter · timebox meter · pipeline DAG) with watermarked placeholder labels;
`EvidenceBlock` renders all five treatments (E1–E5) from fixtures on `#/kit`; the four spine
shapes are *materially* different silhouettes (the SC-005 seed), and every evidence treatment
carries a confidence/flag signal (no bare green badge anywhere).

**Dependencies:** Sub-phase 2b.1 (harness, tokens, Avatar — E1's checker rows and E2's
attribution reuse the lockup's line density)
**Estimated effort:** 1 session (~3h). Parallel-capable with 2b.2b (no shared files beyond
additive sections of `index.html`; if run as parallel agents, partition by banner section).

**Verification:**
- `#/kit` shows four spine renders side-by-side; squint test: four obviously different
  silhouettes (bar / loop band / single meter / node chain), not four colorings of one stepper.
  Each carries the `PLACEHOLDER` watermark from Phase 1's convention.
- The existing `#/goal/CAST-412` canvas now renders its spine zone through `StageSpine`
  (replacing the Phase 1 stub markup) and the Phase 1 hero morph still passes its gate
  checklist — anchors glide, ~350ms, reduced-motion fade intact. **This is the regression
  check that 2b didn't break the keystone.**
- All five EvidenceBlocks render from fixtures; checklist per block: outcome visible first ·
  proof elements present (screenshots/ledger/red→green/verdict/chart) · confidence or flag
  signal present · zero bare pass-fail badges. E2 shows refuted hypotheses still visible
  (struck, not removed); E3 shows the same test name red then green; E4's `spike_ref` renders
  as a navigable-looking link both directions (stub href); E5's chart is inline SVG drawn from
  fixture data points.
- Disk-open, console clean, no new network dependencies beyond Phase 1's CDN set.

Key activities:
- Build `StageSpine` dispatching on `spine.shape`:
  - `segments` (1B): labeled segment bar, accent-filled current segment, completed segments
    ink-tinted, future hollow; segment count from data.
  - `loop` (2B): staged band sharing 1B's zone grammar + the `↺ iter 2/3` badge rendered from
    `spine.iter` — the loop glyph is the signature; counter is mono.
  - `timebox`: a single horizontal budget meter (`3h box · 1h 40m used`, from
    `spine.timebox.{budget,used}`), deliberately lighter than a spine — no phase nodes at all
    (playbook 03: a spike must never look like a mini-feature).
  - `pipeline`: 4-node data-stage chain (`Question → Sources → Analysis → Answer` as
    placeholder), nodes hollow/filled by `current`.
  - All four read Phase 1's `spines.<family>` shape; `timebox`/`pipeline` fixtures live in
    `FIXTURES` until 2a adds the `spike`/`data` families to `appState`.
- Build `EvidenceBlock({kind, data})` with five per-kind sub-renderers (one component, one
  switch — the family must share one visual vocabulary):
  - **E1 Acceptance Panel** (5B): stat tiles (`47 passed / 0 failed`, coverage delta) +
    screenshot strip (2–3 hand-drawn CSS/SVG placeholder thumbnails — `file://` forbids
    external image fetches; Phase 6 may inline real captures) + checker-compliance rows
    (`M04 ✓ resolved · S03 ✓ resolved · R02 ⚠ flagged` — reuses the line-density lockup for
    attribution) + `PR #2341` pointer (link on canvas, diff behind execution drill-in, per the
    locked Q#17 call).
  - **E2 Confirm/Refute Ledger:** per-hypothesis rows `prediction → observation → verdict`;
    confirmed = `--ok` mark, refuted = struck + `--fail` mark, **refuted rows stay visible**.
  - **E3 Red→Green Repro:** two stacked test-run excerpts, same test name, `--fail` red header
    then `--ok` green header; mono excerpt body.
  - **E4 Verdict Card:** one-line answer + `H/M/L` confidence glyph + 2–3 deciding data points
    + first-class `spike_ref` link row.
  - **E5 Rendered Report + Provenance:** headline inline-SVG chart (hand-rolled, M9 idiom — no
    chart library) or table + a `show provenance` disclosure (sources, query) + dated version
    chip (`Report v2 · re-run on fresh data`).
- Swap the Phase 1 placeholder spine markup inside `GoalCanvas` for `StageSpine` (data
  unchanged) and re-run the Phase 1 morph gate checklist.
- Spacing/density pass at the Steve-Jobs bar: the five treatments must read as one family
  (shared padding rhythm, shared header treatment, mono for machine values) while their proof
  forms differ.

**Design review:**
- **Morph-regression risk (architecture):** replacing stub spine markup changes the DOM inside
  the transition. Keep the spine zone's wrapper element (and any anchor placement) identical;
  only inner content changes. Verification explicitly re-runs the Phase 1 gate.
- **Spec consistency (E1–E5):** owner blessed E1–E5 as *revisit-on-sight* defaults — if a
  treatment looks wrong once rendered, refine it and record the refinement; do not silently
  diverge from the catalog's named structure (the names are load-bearing for Phase 3).
- **Error path:** `EvidenceBlock` with an unknown `kind` renders a visible `unknown evidence
  kind` placeholder (console.warn, no throw) — same zero-silent-failure posture as the Phase 1
  dispatcher.
- **Naming:** evidence CSS classes `ev-*`, spine classes `spine-*` — keeps the inline stylesheet
  greppable as it grows.

## Sub-phase 2b.2b: Judgment — Decision Ladder, Nudge Card, Escalation Rail & Autonomy Dial

**Outcome:** the decision atom (playbook 05 schema) renders through all three ladder layers
(6A pill → 6B callout popover → 6C diff-first trail row) from one fixture record; the 3B nudge
card renders `{who, do, why}` with Guide attribution; the 7A escalation rail renders three
ranked option cards (hero/outline/ghost) with evidence pack and **nothing pre-selected**; the
8A autonomy dial renders three positions with its teaching legend and earned-trust stat line
wired to the same fixture stat the colleague card shows.

**Dependencies:** Sub-phase 2b.1 (harness, tokens, GuideMark for attributions)
**Estimated effort:** 1 session (~3h). Parallel-capable with 2b.2a.

**Verification:**
- `#/kit` renders the full disclosure ladder from **one** fixture atom: the pill shows
  `⚖ classification: feature → bug · L2`; clicking opens the 6B callout (rationale ·
  options-considered with chosen mark · revisit-if · byline + timestamp) as a popover, not a
  navigation; the 6C row leads with the field diff, not prose. ID-match check: all three layers
  display the same `DEC-…` id.
- The L-badge color mapping holds: L1 muted, L2 `--warn`, L3 `--rasp` — and raspberry appears
  nowhere else on these components except the rail's hero card and the dial's L3 legend entry.
- Escalation rail: three options with visibly ranked structural weight (A accent-filled hero +
  RECOMMENDED tag, B outline, C ghost/dashed), each carrying its consequence line; evidence
  pack ("what I want / what I tried") present; **no option carries a selected/checked state**;
  keyboard focus order A→B→C.
- Autonomy dial: three named positions, Balanced marked as default, plain-language legend for
  all three lines, trust line `ⓘ 99.4% compliance across 312 runs` rendered from the fixture
  (same object shape the marketplace résumé will read in Phase 5).
- NudgeCard renders from `appState.nudge` verbatim on the goal canvas (replacing the Phase 1
  stub) and the `nudge:<id>` op still cycles its content; the why-line is visually subordinate
  to the do-line but always present (3B's thesis — the product justifies, not just points).

Key activities:
- Author the decision-atom fixture exactly on the playbook 05 schema (field names verbatim,
  contract #3) — one L2 record (`Classify CAST-412 as bug, not feature`) plus one superseded
  record to prove the strike-through + `superseded_by` rendering in the 6C row.
- Build the `Decision` ladder as one component with a `layer` prop (`pill | callout | row`):
  - 6A pill: `⚖` + diff + L-badge, inline-sized so Phase 3 can drop it on artifacts and Phase 1's
    receipt trail can adopt it (the Phase 1 receipt stub upgrades to this pill — see Suggested
    Revisions note).
  - 6B callout: popover anchored to the pill (CSS positioning, no portal library); rationale ·
    options-considered (chosen ✓) · revisit-if · `open full record →` stub link.
  - 6C row: `time · phase · ⚖L · title · who · diff` columns; diff is the scan-line, mono;
    superseded rows struck with a link.
- Build `NudgeCard` (3B): do-line (the only visually-primary CTA in its context, accent-filled
  per the playbook 03 `.nudge-primary` rule) + why-line + `◈ Guide` attribution + the
  `data-op="nudge:<id>"` action. Replace the Phase 1 stub in `GoalCanvas`.
- Build `EscalationRail` (7A): header (escalation title + L3 badge + the `@you` route line) ·
  evidence pack block · three option cards with rank-as-structural-weight; options carry
  `data-op` stubs (real wiring is Phase 3/5's scripted moments). Include the policy-provenance
  line (`policy: decisions/escalation-policy.md`) from playbook 04.
- Build `AutonomyDial` (8A): segmented control (3 positions) + legend block + earned-trust stat
  line. Static in 2b (state wiring is Phase 5's scripted dial-toggle beat); positions render
  from the `value` prop so the future toggle is a data flip.
- Add all fixtures to `#/kit` with captions.

**Design review:**
- **Resolved tension (documented, not silent):** playbook 05 pitfall 2 says "make the three
  options equally weighted"; playbook 04 and the owner's 7A pick say "rank as structural
  weight." The owner's design-decisions entry reconciles them: **rank is visible, but nothing
  is pre-selected** — weight guides, a real click on a real consequence decides. This plan
  follows the owner's reading.
- **Spec consistency:** decision-atom field names must match playbook 05 verbatim — Phase 5's
  trail and Phase 3's chips read the same atoms; a renamed field here forks the schema.
- **Security/a11y:** popover (6B) needs `aria-expanded` + escape-to-close; the rail's options
  are buttons, not divs (keyboard reachable). Static prototype, but the demo is driven live —
  focus states must exist.
- **Error path:** an atom with `status: 'awaiting_human'` renders the pill in its L-color with
  a pulsing-free (no animation slop) `awaiting` tag — visible, not modal.

## Sub-phase 2b.3: Aesthetic Lock — Signature Screen & the Slop Gate

**Outcome:** the upgraded `#/goal/CAST-412` canvas — composed entirely from kit components
(StageSpine, NudgeCard, ColleagueCard line-density in the work stream, an E1 EvidenceBlock in
the stage-artifacts zone, the 6A pill in the receipt trail, the Guide treatment in the chat
rail) — **passes both cast-preso slop-gate checkers (`not-generic` / `not-ai-aesthetic`)**, and
the aesthetic is recorded as locked: tokens final, component kit final, deviations from the
design samples documented. SC-004 is de-risked before Phase 3 mass-produces screens.

**Dependencies:** Sub-phases 2b.2a + 2b.2b
**Estimated effort:** 0.5–1 session (~2h)

**Verification (this is the phase's headline verification):**
- Compose the signature screen: every zone of `#/goal/CAST-412` renders through a kit
  component; zero Phase 1 stub markup remains on the goal canvas; the demo script still walks
  end-to-end (morph included) from a disk-open.
- The colleague lockup renders 4C density on the `#/board` stub (one board card is enough —
  full board is Phase 5) and 4B density in the goal canvas work stream — **same fixture, no
  field drift** (the high-level plan's explicit check).
- Screenshot the signature screen (full canvas + chat rail, 1440px Chrome) →
  **→ Delegate: `/cast-preso-check-visual`** with the screenshot + a one-paragraph WHAT
  context, instructing it to verdict specifically on the `not-generic` and `not-ai-aesthetic`
  dimensions. Review output: a fail on either dimension = rework the flagged element and
  re-run; do not ship the phase on a fail. (Adaptation note: the checkers were built for
  slides; their slop dimensions — generic AI aesthetic, gradient-glass, template-feel — apply
  to app screens directly. Ignore slide-specific findings like "viewport fit for projection.")
- **→ Delegate: `/cast-preso-check-tone`** on the signature screen's visible copy (nudge text,
  chat lines, evidence labels) — GPT-isms/em-dashes in UI copy are slop too (FR-018). Review
  and fix flagged copy.
- Guide-distinctness check (the high-level plan's second verification): on the signature
  screen, the Guide is identifiable as a distinct character in chat voice, nudge attribution,
  and the decision receipt **without reading labels** — self-administered flash test + record
  a screenshot as evidence.
- Token-discipline grep: no raw hex values outside the `:root` block; raspberry usage audited
  (needs-you semantics only).
- Append the aesthetic-lock record (chosen Guide treatment, any sample deviations, checker
  verdicts) to `product-revamp-diecast-decisions-so-far.md`.

Key activities:
- Upgrade `GoalCanvas` zone by zone: spine → `StageSpine` (done in 2b.2a) · nudge stub →
  `NudgeCard` (done in 2b.2b) · work-happening stub → a 3-row stream of line-density
  `ColleagueCard`s with run-status (fixture data) · stage-artifacts stub → one `E1`
  EvidenceBlock (placeholder content; real evidence wiring is Phase 3) · receipt-trail stub →
  6A `Decision` pills · chat rail Guide lines → the locked Guide voice treatment.
- Drop one 4C `ColleagueCard` onto the `#/board` stub route (a single card on a cream board
  frame — just enough for the density-drift verification; the real board is Phase 5).
- First-principles polish pass at the Steve-Jobs bar: spacing rhythm, type hierarchy, hairline
  weights, the cream/paper surface tonality — judged against "would I show this without
  apology" (SC-004), with the gallery samples as reference only.
- Run the slop gate (delegations above), rework, re-run until green.
- Write the aesthetic-lock entry into decisions-so-far; flag anything 2c/3 must know (e.g., if
  a spine shape was adjusted during polish).

**Design review:**
- **Gate honesty under full autonomy:** the slop-gate verdict comes from the *checker agents*,
  not self-assessment — the one externalized judgment in this phase. Verdicts + screenshots
  retained as evidence; a borderline pass is recorded in `borderline-calls.md`.
- **Scope guard:** the signature screen uses placeholder spine vocabulary and stub evidence
  content — that is correct (2c/3 own the real content). The lock is *aesthetic*, not
  informational. Watermarks stay.
- **Architecture:** after this sub-phase, `GoalCanvas` should be ~a data slice + component
  calls. If it still contains bespoke markup, the kit is incomplete — fix the kit, not the
  screen (playbook 06's success metric).

## Build Order

```
Sub-phase 2b.1 ──┬──► Sub-phase 2b.2a (spines + evidence) ──┬──► Sub-phase 2b.3 ──► AESTHETIC LOCK
 (harness,       └──► Sub-phase 2b.2b (decision/nudge/      ┘     (signature screen      │
  avatar grammar,       rail/dial)                                  + slop gate)          ▼
  Guide character)                                                              Phase 3 consumes kit
```

**Critical path:** 2b.1 → (2b.2a ∥ 2b.2b) → 2b.3. The two middle sub-phases touch disjoint
component sets and can run as parallel sessions/agents (partition `index.html` by banner
section to avoid merge friction); serially it's ~3–3.5 sessions, matching the high-level
1.5-day estimate with the parallel option as buffer.

## Design Review Flags

| Sub-phase | Flag | Action |
|-----------|------|--------|
| 2b.1 | Kit components reading `appState` directly would fake the isolation guarantee | Pure-function rule stated in activities; flagged as defect in review |
| 2b.1 | Guide treatment could spend raspberry or drift into mascot theater | Pre-written selection criteria; raspberry excluded; no anthropomorphic marks |
| 2b.1 | Maker card without paired checker silently renders as a solo card | Visible broken-state fallback required (US6.S5 is load-bearing) |
| 2b.2a | Swapping stub spine markup can silently break the Phase 1 morph (anchor/DOM identity) | Keep zone wrapper + anchor placement identical; re-run Phase 1 gate checklist as verification |
| 2b.2a | E1 screenshot strip can't fetch external images from `file://` | Hand-drawn CSS/SVG placeholder thumbnails; Phase 6 may inline real captures |
| 2b.2b | Decision-atom field drift vs playbook 05 schema would fork the schema Phases 3/5 reuse | Field names adopted verbatim; listed in exported contracts |
| 2b.2b | PB-05 "equal options" vs 7A "ranked weight" conflict | Owner reading adopted: ranked weight, nothing pre-selected; documented |
| 2b.3 | cast-preso checkers were built for slides, not app screens | Adapted use: verdict only on not-generic/not-ai-aesthetic dimensions; slide-specific findings ignored; noted in delegation context |
| 2b.3 | Self-judged taste under full autonomy | External checker verdicts are the gate; evidence retained; borderline passes logged to borderline-calls.md |
| all | Single-file `index.html` growth (now ~8 components + fixtures + kit route) | Banner-comment sections, `kit-`/`ev-`/`spine-` class prefixes, token-only colors — keeps the file navigable and Phase 6 packaging mechanical |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Slop-gate failure on the signature screen late in the phase | High | The gate is the *point* of 2b (de-risk SC-004 now, not in Phase 3); rework loop is budgeted in 2b.3; hard rules (no glass/gradient/glow/orb, token discipline) enforced from 2b.1 so failure modes can't accumulate |
| Lockup density drift (the exact failure the high-level plan names) | High | One component, one fixture, density prop; in-context renders on `#/kit`; drift check in 2b.1 and again on the signature screen in 2b.3 |
| Component props shaped wrong for 2a's `org.json` (parallel-phase mismatch) | Med | Prop contracts exported in this plan + appended to decisions-so-far *before* 2a finalizes; fixtures use canonical vocabulary so the swap is mechanical |
| Phase 1 morph regression while re-skinning the goal canvas | Med | Explicit gate-checklist re-run in 2b.2a and 2b.3; vt- anchors owned by zone wrappers (contract #9) |
| The Guide treatment reads as anonymous UI or as mascot cosplay | Med | Three rendered candidates judged against pre-written criteria; distinctness verified label-free on the signature screen |
| 2c's real vocabulary won't fit the spine components | Low | `StageSpine` renders shape from data; labels are data; 2c lands as a data edit — only a *new shape* (not new labels) would need component work |

## Open Questions

None blocking — full-autonomy mode resolved all judgment calls (logged below). For
traceability:

- The Guide's final visual treatment is decided **inside 2b.1's rendered-options pass** (the
  plan supplies the recommended default and the selection criteria; the pick is an execution-
  time craft call, recorded in decisions-so-far per the aesthetic-lock activity).
- Whether the cast-preso checkers' verdicts transfer cleanly to app screens is assumed yes
  (their slop dimensions are medium-independent); if a checker proves unusable in practice,
  fall back to its checklist applied manually and record the substitution in
  borderline-calls.md.

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| `docs/specs/_registry.md` (re-confirmed) | all seven specs govern cast-server runtime | None — FR-020: the prototype is greenfield; no spec applies, none contradicted; no `/cast-update-spec` action (excluded by delegation instruction) |

## Decisions Made Autonomously

1. **Sub-phase split 2b.1 → (2b.2a ∥ 2b.2b) → 2b.3** — grammar foundations first (everything
   reuses Avatar/tokens/harness), canvas-side and judgment-side components in parallel
   (disjoint files-sections), aesthetic lock last. Matches the 3-session estimate with
   parallelism as buffer.
2. **`#/kit` dev route as the isolation harness** — satisfies "each component renders from a
   data prop in isolation" with no build step and no extra files (single-file contract);
   hash-only reachable, hidden from demo nav; Phase 6 decides keep-or-strip.
3. **Components stay inline in `index.html`** — forced by Phase 1's `file://` packaging
   contract; organized by banner comments + class prefixes rather than splitting files.
4. **Avatar grammar: human=circle · maker=square (`--maker` outline) · checker=square
   (`--checker` fill) · Guide=diamond** — honors the owner's "humans=circles, agents=squares —
   or better"; the diamond keeps the Guide square-family (an agent) while instantly distinct (a
   different kind). Supersedes playbook 04's all-circles grammar (older than the owner
   directive).
5. **Guide treatment process: 3 rendered candidates, pre-written criteria, pick at the bar** —
   the owner deferred this to "seeing options rendered"; recommended default is the diamond ◈ +
   mono wordmark + structural (not color) chat-voice treatment, because raspberry is reserved
   and a persistent character must not shout.
6. **Decision atom adopts playbook 05's schema field names verbatim** — Phases 3/5 read the
   same atoms; one schema, three projections (6A/6B/6C as a `layer` prop on one component).
7. **vt- anchor names are applied by shell zone wrappers, never by kit components** — a
   component rendered twice on `#/kit` with an anchor name would silently kill every view
   transition (Phase 1's uniqueness rule). New contract #9.
8. **Token extensions: `--fail: #B22439`, L-badge mapping (L1 muted / L2 `--warn` / L3
   `--rasp`), confidence glyphs ●/◐/○** — extend-don't-rename per Phase 1; semantic test-red is
   distinct from brand raspberry so the needs-you signal stays unique; glyphs not percentages
   per playbook 01.
9. **`EvidenceBlock` is one component with a `kind` switch, not five components** — the E1–E5
   family must share one visual vocabulary; per-kind sub-renderers keep the proof forms
   distinct inside one frame.
10. **E1 screenshots are hand-drawn CSS/SVG placeholder thumbnails** — `file://` forbids
    fetching image assets and the single-file rule discourages base64 bloat during dev; Phase 6
    owns real-capture inlining if wanted.
11. **E5 charts are hand-rolled inline SVG (M9 idiom), no chart library** — keeps the <15KB
    library budget intact and matches the proven precedent.
12. **Escalation rail: ranked structural weight + nothing pre-selected** — adopts the owner's
    7A entry as the reconciliation of the playbook 04 (rank) vs playbook 05 (equal-weight)
    tension.
13. **The signature screen is the upgraded `#/goal/CAST-412`, not a new route** — proves the
    kit composed in situ (where Phase 3 will actually use it), exercises the morph-regression
    check, and avoids building a throwaway showcase screen (HOLD SCOPE).
14. **Slop gate delegated to `/cast-preso-check-visual` + `/cast-preso-check-tone` on
    screenshots, adapted to app screens** — the high-level plan mandates these named checkers;
    playbook 06's "they validate decks, not apps" caveat is handled by scoping the ask to the
    two slop dimensions and ignoring slide-specific findings.
15. **AutonomyDial ships static (value from prop)** — the dial-toggle demo beat is Phase 5's
    scripted moment; building toggle wiring now would be premature (HOLD SCOPE), but rendering
    from a `value` prop makes Phase 5's wiring a data flip.
16. **One superseded decision fixture included in 2b.2b** — the 6C strike-through +
    `superseded_by` rendering is part of the ladder's contract (playbook 05's "watch the
    product change its mind" payoff); cheaper to prove now than to retrofit in Phase 5.
17. **`cast-plan-review` auto-dispatch skipped** — the run configuration in
    `product-revamp-diecast-decisions-so-far.md` states "Plan review: skipped — cross-phase
    reconciliation only" (owner-approved; same precedent as Phase 1 decision #12). Rerun
    manually via `/cast-plan-review` against this file if wanted.

## Suggested Revisions to Prior Sub-Phases

- **Phase 1, minor (non-breaking):** Phase 1 renders the receipt stub as "a 6A-style pill" and
  applies `vt-nudge-card`/`vt-receipt-trail` anchors. Two clarifications this plan adds on top:
  (a) when 2b.2b's real `Decision` pill replaces the stub, the **anchor must sit on the trail's
  zone wrapper, not on the pill component** (contract #9) — if Phase 1's execution placed the
  anchor on the pill element itself, move it to the wrapper during 2b.2b (visual result
  identical, prevents the `#/kit` duplicate-name hazard); same for the nudge card. (b) No
  appState changes are needed by 2b — `receipts[]` entries should migrate to the full decision-
  atom shape in Phase 3/5, not now; Phase 1's stub receipt shape (`{level, label, at,
  rationale}`) remains valid as a subset. No change to Phase 1's plan document is required —
  this is execution guidance, recorded here and in decisions-so-far.
