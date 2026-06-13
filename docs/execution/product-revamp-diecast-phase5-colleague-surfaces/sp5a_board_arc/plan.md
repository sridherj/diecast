# Sub-phase 5a: Board Arc, Decision Trail & the Autonomy Dial (US5 + US10)

> **Pre-requisite:** Read
> `docs/execution/product-revamp-diecast-phase5-colleague-surfaces/_shared_context.md` before
> starting this sub-phase. The binding constraints there are not optional.

## Objective

Board → ticket CAST-412 → decision artifact → L3 escalation read as **four frames of one story** with
consistent chrome and canonical vocabulary; the assignee filter **actually filters** (4 working
states); the ticket shows the maker-checker activity log with inline M04/S03/R02 violations, rework
1/3, and the PR link; the cross-phase decision trail renders **diff-first** with the superseded
GraphQL→REST pair struck through; and the autonomy dial toggle **visibly promotes an L2 decision into
an L3-style stop** (SC-007's autonomy-gated moment, shown live).

## Dependencies
- **Requires completed:** Sub-phase 5.0 (the ORG batch, the route stubs, the appState keys,
  `DigestNotice`); **Phase 3 executed** (`IterationPanel` + `goals['CAST-412'].execution` data).
- **Parallel-safe with:** 5b, 5c (disjoint routes + CSS prefixes; shared code only through the 2b kit
  and 5.0's `DigestNotice`). See the file-collision honesty note in the manifest.

## Estimated effort
1.25–1.5 sessions (~4–4.5h).

## Scope
**In scope:** the four route renderers `#/board`, `#/ticket/CAST-412`, `#/decision/:atomId`,
`#/decisions/CAST-412`; the assignee-filter handler; the `AutonomyDial` wiring; the L2 digest strip.
**Out of scope (do NOT do these):** any hiring/marketplace/ops/Layer-2 surface (5b); the reqs-doc
(5c); minting a sixth op; resolving the CAST-417 escalation (stays inert); any test file; any
hand-edit of `org.js`; touching the Phase 4 canvas/parity sections.

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `prototype/index.html` | Modify | Carries the 5.0 stubs for these four routes; gains the real `board-*`/`ticket-*`/`dec-*` renderers + the dial wiring + the L2 digest |

## Detailed Steps / Key Activities

- **Real `#/board`** (re-author preso a08/s8a as DOM; **lift layout/vocabulary only, zero SVG
  geometry**): four columns (Backlog · In progress · In review · Done) rendered from `ORG.board`;
  humans and agents in the **same assignee stack** — same card format, same columns, distinguished
  **only** by the 2b avatar grammar (**no "Automations" lane, ever**). Ticket cards carry the
  `ColleagueCard` line density + in-flight pill (work visible without opening the ticket). Header:
  assignee filter chip row `Any · Human · Agent · Checker` driven by `appState.boardFilter` (plain
  click handlers + re-render — **not ops**; the op vocabulary stays closed at 5), the framing line
  **"Publishes INTO your PM tool. It does not replace Linear / Jira / GitHub Projects."**, and an
  escalation inbox badge `@you · 1` (top-right) linking to the CAST-417 decision frame.
- **`#/ticket/CAST-412`** (re-author a09): header = ticket title + maker-checker paired lockup +
  3-segment rework meter (1/3). Body = **Phase 3's `IterationPanel` reused verbatim**, fed by
  `goals['CAST-412'].execution.iteration` — iteration bands as first-class history, checker findings
  inline with rule codes **M04/S03/R02** (the compliance *checklist*, never a lone pass/fail badge),
  named exits, and the resulting **PR #-link in the footer** (link on surface, diff behind the
  execution drill-in, per the locked PR-placement call). Decision `pill` chips render on log entries
  whose atoms list them in `influenced[]`, opening the 6B callout popover; one entry carries the
  **"next › decision"** link into the artifact frame.
- **`#/decision/:atomId`** — the decision artifact frame: the `Decision` ladder's full record (6C
  layer, full-frame) rendering **every atom field verbatim** (id, reversibility badge, decision,
  rationale, options_considered, consequences, revisit_if, originating agent/phase, timestamp,
  supersedes/superseded_by links, spike_ref when present, `diff` line). **Branch:** when the atom is
  L3 + `awaiting_human` (CAST-417, roles-column drop), the frame additionally renders the
  **`EscalationRail`** — three pre-framed options with consequence lines, ranked as structural weight
  (hero/outline/ghost), **nothing pre-selected**, evidence pack ("what I want / what I tried"), expiry
  line. The rail is an **unresolved stop** — options don't wire (only Phase 4's data L3 resolves,
  prototype-wide consistency); the frame's **"escalated to me →"** link loops back to `#/board` with
  `boardFilter` applied.
- **`#/decisions/CAST-412`** — the cross-phase trail: one **diff-first** row per atom
  (`time · phase · L-badge · title · who · diff`), filter chips for phase / actor (any·human·agent —
  same chrome as the board filter) / L-level; the superseded **GraphQL→REST** pair renders
  struck-through with a "superseded by →" link; row click navigates to `#/decision/:atomId`. The
  trail proves chip↔row ID-match: same atoms as the ticket chips.
- **`AutonomyDial` wiring** (the 2b component, static until now) at the **trail header**: segmented
  Conservative / ●Balanced / Autonomous + the teaching legend + earned-trust tooltip reading the
  feature-roster aggregate (**99.4% · 312 runs**) from `agent.stats` (single source). Toggling sets
  `appState.autonomyLevel` and re-renders: **under Conservative**, the `dial_demo` L2 atom leaves the
  digest/trail flow and renders as a **pinned stop-and-confirm card** at the top of the trail
  (escalation-card treatment + "now requires your OK" line) and its L2 badge re-tints — the visible
  threshold shift (a dial that only changes ping frequency is a gimmick). **No receipt is written; ORG
  is never mutated; reload resets.**
- **L2 digest strip** above the trail via `DigestNotice`: "⚖ 2 decisions made while you were away",
  rows expanding to the 6B callout. This is the minimal substrate the dial promotion needs (the L2
  must visibly come *from* a quiet digest), and it instantiates the **same component** 5c uses for the
  write-back notice — one inform-without-nagging atom, twice.

## Verification

> **NO TESTS (binding):** every check below is **manual click-through / static observation**. In an
> autonomous run with no browser, satisfy each via the strongest static evidence (`node --check`,
> grep audits, a throwaway `/tmp` logic harness that is never committed) and record a non-blocking
> human-eyeball carry-forward for any rendered-pixel item. **Do not flag missing tests.**

**Verification (manual, from disk) — verbatim from the plan:**
- Click the four-frame arc end-to-end: `#/board` → ticket card CAST-412 → `#/ticket/CAST-412` → a log
  entry's **"next › decision"** → `#/decision/DEC-CAST-412-NN` → from the trail, open the CAST-417 L3
  → escalation rail with three ranked options, **nothing pre-selected** → **"escalated to me"** link
  loops back to the board with the filter applied.
- Click all four filter chips — each hides exactly the wrong cards.
- On `#/decisions/CAST-412`, flip the dial **Balanced→Conservative** and watch the `dial_demo` L2 row
  promote into a pinned stop-and-confirm card; flip back and it demotes. **Reload resets everything
  (ORG unmutated).**
- The superseded GraphQL→REST pair renders struck-through with a "superseded by →" link.
- The L2 digest strip renders above the trail; rows expand to the 6B callout.
- Unknown `:atomId` or ticket id in the hash → render the board/trail with a muted "not found" strip,
  never a blank canvas.

### Success Criteria (binary — every item must pass or carry forward with reason)
- [ ] Four-frame arc clicks end-to-end with consistent chrome; the "escalated to me →" loop-back lands
      on `#/board` with `boardFilter` applied.
- [ ] All four assignee filter chips filter correctly (humans + agents in one stack, no Automations
      lane).
- [ ] Ticket shows the `IterationPanel` activity log with inline M04/S03/R02 violations, rework 1/3,
      and the PR #-link in the footer.
- [ ] `#/decision/:atomId` renders every atom field verbatim; the CAST-417 branch shows the inert
      `EscalationRail` (3 options, nothing pre-selected).
- [ ] Trail is diff-first; GraphQL→REST struck-through; row↔chip↔frame IDs match.
- [ ] Dial Balanced→Conservative promotes the `dial_demo` L2 into a pinned stop card; reload resets;
      ORG unmutated; the earned-trust tooltip reads 99.4% · 312 from `agent.stats`.
- [ ] L2 digest strip uses the shared `DigestNotice`; closed 5-op set intact; 6×1 vt- anchors
      unchanged; `node --check` clean.

## Design review (verbatim from the plan)
- **Op-vocabulary discipline:** filter chips, dial, trail filters are plain handlers mutating additive
  appState keys — the closed 5-op set is for scripted chat actions only. ✓ (matches Phase 3's
  precedent of not minting ops for UI state).
- **Escalation consistency:** CAST-417 rail = unresolved stop, reusing the single `EscalationRail`
  component (US5 and US10 are the same mechanism — a second escalation UI is forbidden). ✓
- **Error/edge:** unknown `:atomId` or ticket id in the hash → render the board/trail with a muted
  "not found" strip, never a blank canvas (zero silent failures).
- ⚠ **Dial-demo honesty:** promoting an already-`recorded` atom into a "stop" is a scripted illusion —
  keep the card's copy in the conditional voice the legend establishes and reset on reload, so it
  reads as a live policy shift, not falsified history. Flagged in the table.

### Design Review Flags (this sub-phase's rows, verbatim from the plan)
| Sub-phase | Flag | Action |
|-----------|------|--------|
| 5a | UI state (filter/dial) could tempt new ops | Plain handlers + additive appState keys only; op vocabulary stays closed at 5 |
| 5a | Dial demo promotes a `recorded` atom — scripted illusion | Conditional-voice copy, pinned-card treatment, reload resets, ORG unmutated |
| 5a | Second escalation UI risk (US5 vs US10) | One `EscalationRail`, two instantiations; CAST-417 stays an unresolved stop |
| all | New routes could mint duplicate vt- names | No new vt- names; anchors live on shell zone wrappers only (2b rule) |

## Execution Notes
- **Single route `#/decision/:atomId` serves both the decision-artifact and escalation frames**,
  branching on status/level (Decision 6) — four story frames with shared chrome beats two
  near-identical routes.
- **`AutonomyDial` lives on `#/decisions/CAST-412`'s trail header** (Decision 4), not the Phase 3 goal
  canvas — keeps the demo self-contained and avoids re-opening a Phase 3-owned screen during a
  parallel phase.
- The L2 digest strip is the substrate the dial promotion needs — without a quiet digest to promote
  *from*, the threshold shift has no visible source (Decision 8).
- **Spec-linked files:** none — greenfield (FR-020); no `/cast-update-spec`.
- **Plan review:** SKIPPED per run config — do not dispatch `/cast-plan-review` or any reconciliation
  pass.
