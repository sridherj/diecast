# Sub-phase 2b.2b: Judgment — Decision Ladder, Nudge Card, Escalation Rail & Autonomy Dial

> **Pre-requisite:** Read `docs/execution/product-revamp-diecast-phase2b-component-kit/_shared_context.md`
> before starting. It carries the inherited Phase 1 contracts, the 9 exported contracts, the
> binding constraints (NO TESTS, file:// legality, single-file packaging, fixture discipline,
> failure policy), and FULL AUTONOMY mode. This plan does not repeat them.

> **FULL AUTONOMY MODE (owner-approved):** never ask the user questions, never pause for approval
> gates, never go idle waiting for input. At decision gates pick the recommended option and
> document it inline in the sub-phase output. Propagate this exact autonomy directive verbatim
> into any child agent you dispatch.

> **PARALLEL-CAPABLE with 2b.2a.** Both depend only on 2b.1 and touch **disjoint banner sections**
> of `index.html`. This sub-phase owns the **decision / nudge / rail / dial** sections (`dec-*`,
> `nudge-*`, `rail-*`, `dial-*` class prefixes) plus the `GoalCanvas` **nudge zone**. Do **not**
> edit 2b.2a's spine/evidence sections or the `GoalCanvas` spine zone. If run as concurrent agents,
> partition by banner comment; if serial, order is irrelevant.

## Objective

Build the four judgment-side components: the `Decision` disclosure ladder (one atom → three
projections: 6A pill / 6B callout / 6C trail row), the 3B `NudgeCard` (with Guide attribution),
the 7A `EscalationRail` (three ranked options, **nothing pre-selected**), and the 8A
`AutonomyDial` (three positions + teaching legend + earned-trust stat line, static). Replace the
Phase 1 nudge stub in `GoalCanvas` with the real `NudgeCard`.

## Dependencies
- **Requires completed:** 2b.1 (harness, tokens, `GuideMark` for attributions, the L-badge mapping).
- **Assumed codebase state:** `prototype/index.html` has the `#/kit` route, `FIXTURES`, the token
  extensions (incl. the L-badge mapping `L1 → --ink-35 · L2 → --warn · L3 → --rasp`), and the
  chosen Guide treatment.

## Scope

**In scope:**
- Author the decision-atom fixture **exactly on the playbook 05 schema** (field names verbatim,
  contract #3): one L2 record (`Classify CAST-412 as bug, not feature`) **plus one superseded
  record** (to prove the 6C strike-through + `superseded_by` rendering).
- Build the `Decision` ladder as **one component with a `layer` prop** (`pill | callout | row`):
  - **6A pill:** `⚖` + diff + L-badge, inline-sized so Phase 3 can drop it on artifacts and Phase
    1's receipt trail can adopt it.
  - **6B callout:** popover anchored to the pill (CSS positioning, **no portal library**);
    rationale · options-considered (chosen ✓) · revisit-if · `open full record →` stub link.
  - **6C row:** `time · phase · ⚖L · title · who · diff` columns; **diff is the scan-line** (mono,
    leads the row, not prose); superseded rows struck with a link.
- Build `NudgeCard` (3B): do-line (the only visually-primary CTA in its context, accent-filled per
  the `.nudge-primary` rule) + why-line (visually subordinate but **always present** — 3B's thesis:
  the product justifies, not just points) + `◈ Guide` attribution + the `data-op="nudge:<id>"`
  action. **Replace the Phase 1 nudge stub in `GoalCanvas`.**
- Build `EscalationRail` (7A): header (escalation title + L3 badge + the `@you` route line) ·
  evidence-pack block ("what I want / what I tried") · three option cards with **rank as structural
  weight** (A accent-filled hero + RECOMMENDED tag, B outline, C ghost/dashed), each carrying its
  consequence line; **no option carries a selected/checked state**; keyboard focus order A→B→C.
  Options carry `data-op` stubs (real wiring is Phase 3/5). Include the policy-provenance line
  (`policy: decisions/escalation-policy.md`).
- Build `AutonomyDial` (8A): segmented control (3 positions, Balanced marked default) + plain-
  language legend for all three + earned-trust stat line (`ⓘ 99.4% compliance across 312 runs`,
  rendered from the fixture — **same object shape the marketplace résumé reads in Phase 5**).
  Static: positions render from the `value` prop (Phase 5's toggle is then a data flip).
- Add all four components' fixtures + gallery sections to `#/kit` with captions.

**Out of scope (do NOT do these — HOLD SCOPE):**
- `StageSpine`, `EvidenceBlock` — **2b.2a** (do not touch its banner sections or the spine zone).
- Composing the full signature screen / running the slop gate — **2b.3.**
- Wiring the autonomy dial's live state toggle — **Phase 5** (static `value` prop only here).
- Wiring the escalation options to real scripted moments — **Phase 3/5** (`data-op` stubs only here).
- Migrating `appState.receipts[]` to the full decision-atom shape — **Phase 3/5** (Phase 1's stub
  shape stays valid as a subset).
- Any test file / harness / CI (C1). Any `fetch()` / local ES-module import (C2).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `prototype/index.html` | Modify (additive — `dec-*`/`nudge-*`/`rail-*`/`dial-*` sections + `GoalCanvas` nudge zone) | Has 2b.1's Avatar/ColleagueCard/tokens/Guide/`#/kit` |

## Detailed Steps

### Step 2b.2b.1: Author the decision-atom fixtures (contract #3, verbatim field names)
- One L2 record (`Classify CAST-412 as bug, not feature`) with **all** contract-#3 fields:
  `id · phase · title · reversibility · rationale · options_considered[] · consequences ·
  revisit_if · originating_agent · author_type · timestamp · status · supersedes/superseded_by ·
  spike_ref · influenced[]`.
- One **superseded** record so the 6C strike-through + `superseded_by` link renders.
- Field names are load-bearing — Phases 3/5 read the same atoms; **a renamed field forks the schema.**

### Step 2b.2b.2: Build the `Decision` ladder (one component, `layer` prop)
- `Decision({atom, layer})` with three projections (6A pill / 6B callout / 6C row) per the Scope
  detail. All three render from **one** atom; the `DEC-…` id must match across all three layers.
- 6B is a CSS-positioned popover (no portal library) with `aria-expanded` + escape-to-close.
- `dec-*` class prefix. Pure-function rule: reads `{atom, layer}` only.

### Step 2b.2b.3: Build `NudgeCard` (3B) + replace the Phase 1 stub
- `NudgeCard({nudge})` consuming `appState.nudge` `{who, do, why}` verbatim: accent-filled do-line
  (the only visually-primary CTA in its context) + subordinate-but-always-present why-line + `◈
  Guide` attribution + `data-op="nudge:<id>"`.
- **Replace the Phase 1 nudge stub in `GoalCanvas`** with this component — keep the nudge zone
  wrapper + any `vt-nudge-card` anchor placement identical (anchor on the wrapper, never on the
  component; contract #9). Confirm the `nudge:<id>` op still cycles its content.

### Step 2b.2b.4: Build `EscalationRail` (7A)
- `EscalationRail({escalation})` per the Scope detail: header + evidence pack + three rank-weighted
  option cards (hero/outline/ghost), each with a consequence line, **nothing pre-selected**, focus
  order A→B→C, options are `<button>`s (keyboard reachable) carrying `data-op` stubs, plus the
  policy-provenance line. `rail-*` class prefix.

### Step 2b.2b.5: Build `AutonomyDial` (8A, static)
- `AutonomyDial({value, trust})` per the Scope detail: 3-position segmented control (Balanced
  default) + legend + trust stat line from `trust.{compliancePct, runs}`. Renders from the `value`
  prop (no live toggle wiring). `dial-*` class prefix.

### Step 2b.2b.6: Add gallery sections to `#/kit`
- Add `Decision` (all three layers from one atom + the superseded record), `NudgeCard`,
  `EscalationRail`, and `AutonomyDial` sections with captions. Contract #9: no `vt-` anchors on
  kit renders.

## Verification

### Automated Tests (permanent)
- **None.** Constraint C1 forbids tests. Do not create any test file.

### Validation Scripts (temporary)
- None that run code. Static checks: `node --check` of the inline module; grep for raw hex outside
  `:root`; grep confirming `dec-*`/`nudge-*`/`rail-*`/`dial-*` prefixes; grep confirming
  decision-atom field names match contract #3 verbatim.

### Manual Checks (the only verification — open from disk in Chrome and observe)
1. **Disclosure ladder from one atom:** `#/kit` renders all three layers from **one** fixture atom
   — the pill shows `⚖ classification: feature → bug · L2`; clicking opens the 6B callout
   (rationale · options-considered with chosen mark · revisit-if · byline + timestamp) **as a
   popover, not a navigation**; the 6C row **leads with the field diff, not prose**. ID-match: all
   three layers display the same `DEC-…` id.
2. **L-badge color mapping:** L1 muted, L2 `--warn`, L3 `--rasp` — and raspberry appears **nowhere
   else** on these components except the rail's hero card and the dial's L3 legend entry.
3. **Escalation rail:** three options with visibly ranked structural weight (A accent-filled hero +
   RECOMMENDED tag, B outline, C ghost/dashed), each with its consequence line; evidence pack
   present; **no option carries a selected/checked state**; keyboard focus order A→B→C; options are
   buttons (keyboard reachable).
4. **Autonomy dial:** three named positions, Balanced default, plain-language legend for all three,
   trust line `ⓘ 99.4% compliance across 312 runs` rendered from the fixture.
5. **NudgeCard on the goal canvas:** renders from `appState.nudge` verbatim (replacing the Phase 1
   stub); the `nudge:<id>` op still cycles its content; the why-line is visually subordinate to the
   do-line but **always present**.
6. **Error path:** an atom with `status: 'awaiting_human'` renders the pill in its L-color with a
   **non-animated** `awaiting` tag — visible, not modal.
7. **a11y:** the 6B popover has `aria-expanded` + escape-to-close; rail options are focusable
   buttons. (Static prototype, but the demo is driven live — focus states must exist.)
8. **Disk-open, console clean,** no new network deps.

### Success Criteria (binary — every item must pass)
- [ ] `Decision` is **one** component with a `layer` prop; all three projections render from one atom; the `DEC-…` id matches across layers; 6C leads with the diff; superseded record renders struck + linked.
- [ ] Decision-atom field names match contract #3 (playbook 05) **verbatim** (grep-verified — no fork).
- [ ] L-badge mapping holds (L1 muted / L2 `--warn` / L3 `--rasp`); raspberry confined to needs-you semantics (rail hero + dial L3 legend only).
- [ ] `EscalationRail` renders three rank-weighted options with **nothing pre-selected**; focus order A→B→C; options are buttons; policy-provenance line present.
- [ ] `AutonomyDial` renders three positions (Balanced default) + legend + trust stat from the fixture; static (renders from `value` prop).
- [ ] `NudgeCard` (3B) replaces the Phase 1 stub in `GoalCanvas`; `{who, do, why}` verbatim; `◈ Guide` attribution; `nudge:<id>` op still cycles; why-line subordinate but always present.
- [ ] 6B popover has `aria-expanded` + escape-to-close; `awaiting_human` atom renders a visible non-animated tag.
- [ ] Disk-open clean console; no new network deps; no edits to 2b.2a's spine/evidence sections or the `GoalCanvas` spine zone (parallel-safety).

## Execution Notes
- **The resolved tension (document, don't silently resolve):** playbook 05 pitfall 2 says "make the
  three options equally weighted"; playbook 04 + the owner's 7A pick say "rank as structural
  weight." The owner's design-decisions entry reconciles them: **rank is visible, but nothing is
  pre-selected** — weight guides, a real click on a real consequence decides. Follow the owner's
  reading; note it in the output.
- **Decision-atom field drift forks the schema** — Phase 5's trail and Phase 3's chips read the
  same atoms. Adopt the field names verbatim from playbook 05 / contract #3; do not "improve" them.
- **The superseded fixture is part of the ladder's contract** (playbook 05's "watch the product
  change its mind" payoff) — cheaper to prove now than to retrofit in Phase 5. Don't skip it.
- **Contract #9:** the `vt-nudge-card` anchor lives on the `GoalCanvas` nudge **zone wrapper**,
  never on `NudgeCard` — a kit render of `NudgeCard` must not carry the anchor name or it kills the
  morph.
- **No browser available?** If Chrome can't be connected this session, run the static checks, mark
  the live a11y/taste items (popover behavior, focus order, flash-test) PROVISIONAL, flag them for
  a human eyeball in the output — same posture Phase 1 used. Do not block.
- **Parallel safety:** this sub-phase touches only `dec-*`/`nudge-*`/`rail-*`/`dial-*` sections +
  the `GoalCanvas` **nudge zone**. 2b.2a touches the spine/evidence sections + the spine zone.
  Partition cleanly; if a `GoalCanvas` conflict arises, the spine zone is 2b.2a's and the nudge
  zone is yours.
- **Failure policy (C5 — 2b.2b is NOT critical):** retry once with refined steps; a **second**
  failure → **log the gap and continue** (off critical path). Record the exact failure + what
  remains in the output and manifest Notes.
- **Spec-linked files:** none (greenfield prototype, FR-020).
