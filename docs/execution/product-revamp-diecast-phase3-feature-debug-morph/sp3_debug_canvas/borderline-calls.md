# Sub-phase 3.3 — Borderline Calls & Documented Decisions

> Full-autonomy mode: at every judgment gate, pick the recommended option and document it.
> This file records the non-obvious calls made while executing `sp3_debug_canvas/plan.md`.

## 1. CAST-431 E2/E3 shapes RESHAPED in the generator (the sanctioned mismatch-fix path)

The 2a-authored `CAST-431.evidence.E2/E3` did **not** match the LOCKED 2b `EvidenceBlock` contracts —
3.3 is their first consumer, so the mismatch surfaced now:

- **E2** hypotheses carried `{id, verdict, prediction, observation}` but **no `statement`** — yet
  `EvidenceE2` renders (and strikes-when-refuted) `h.statement`. Without it the ledger rows would be
  blank and the "refuted struck-but-visible" signal would have nothing to strike.
- **E3** carried `{repro, red, green}` (flat strings) but `EvidenceE3` reads the red→green shape
  `{test.name, before.{status,excerpt}, after.{status,excerpt}}`.

**Decision (per the plan's explicit DATA RULE):** *"fix in the generator, never fork the component,
never hand-edit org.js."* Added `statement` to each E2 hypothesis and reshaped E3 to the locked
`{test, before, after}` shape in `generate-org.mjs`. The `EvidenceBlock` component is untouched
(no fork). The H3 statement weaves the **v4.2 RBAC migration** root cause (the same story the L3 atom
and the morph carry), so the org reads as one company.

**F4 section-stability:** the change is confined to the `CAST-431` block (the batch's declared
section). Verified by diff vs the pre-edit baseline — only `CAST-431` lines changed; `CAST-412`,
`CAST-452`, `CAST-461`, `stageModels`, `agents`, `decisions` are **byte-identical**. Gate green,
deterministic (re-run → byte-identical). `CAST-412.morph_view.evidence['E2-seed']` is left untouched
(it carries the same statement-less shape) — **carry-forward for 3.4**, which owns the morph evidence.

## 2. `investigation` is a NEW additive key on CAST-431 (the FR-007 iteration-history surface)

The plan's investigation-ledger work zone (passes that *collapse, never delete*) needs pass-level
data that 2a did not author. **Decision:** add `goals['CAST-431'].investigation = { passes: [...] }`
via the generator (additive; only `CAST-431` touched). Two passes — pass 1 **closed** (H1/H2 refuted),
pass 2 **live** (H3 confirmed) — consistent with `spine_state.iter 2/3`. Each pass lists its
experiments (assignee resolves in `ORG.agents` → line-density `ColleagueCard` attribution) and the
hypothesis ids it weighed (resolve into `evidence.E2`). A new **invariant Rule 15** gates it (exactly
one live pass; statuses ∈ live|closed; hypothesis ids + experiment assignees resolve; E2 statement +
verdict shape; E3 red→green shape) — drift cannot be authored.

## 3. The investigation ledger renders ONLY at the default (unfocused) debug view

**Shared-grammar discipline (SC-005):** the deviation is confined to **spine + evidence/work**. The
debug canvas swaps the feature's "Stage artifacts" surface for the **InvestigationLedger** *only* when
`isDebug && !stageFocus`. The stage **navigator** is unchanged — clicking a loop step focuses it and
routes through the *same* shared `StageSurface` + `EvidenceBlock` path the feature canvas uses, so
**E2 @ dbg-04** and **E3 @ dbg-05** are reachable identically. Header, spine zone, nudge, work-stream
frame, exec tab, chat rail are all the shared grammar. Nothing beyond spine + evidence/work deviates.

## 4. The Guide narration + nudge are now PER-GOAL (shared grammar, goal-correct content)

3.1 left the header `guide-line` hardcoded to the **feature's** flagged rule (`FLAGGED_RULE`) and the
`appState.nudge` pinned to `FEATURE.nudge` across route changes — both would bleed feature content
onto the debug canvas. **Decision:** make both goal-aware (the same posture as the per-goal title /
crumb / work-stream):

- `syncGoalFromRoute` now sets `appState.nudge = { ...g.nudge }` on route entry (debug nudge for
  CAST-431, feature nudge for CAST-412). On CAST-412 entry this equals boot (`FEATURE.nudge`) →
  **byte-identical, no feature regression**. The morph (3.4) flips family without a hashchange, so it
  never fires on a morph.
- The `guide-line` branches on `isDebug`: the feature string is the **exact** prior literal
  (byte-identical); the debug line narrates this goal's own loop signal (iteration + the confirmed
  hypothesis), derived from ORG.

## 5. Loop-band iter-overflow guard added to `SpineLoop`

The plan requires `iter.current > iter.budget` → `--fail` counter + `console.warn` (no silent clamp).
Added the guard to `SpineLoop` (the only 2b component touched). It is purely defensive: for valid
counters (`current ≤ budget`, e.g. CAST-431's 2/3) the render is **byte-identical** to before; the
`--fail` tint + warn fire only on bad data. Zero-silent-failure posture, consistent with
`ev-unknown` / `spine-unknown`. Not a component fork — an additive error path.

## 6. LIVE-VERIFIED (the user reconnected the Chrome extension after the static pass)

The sub-phase was first completed + statically verified under the no-browser autonomy gate; the user
then reconnected the Chrome extension, so the deferred visual carry-forwards were **driven live**
(prototype served over `http://localhost:8123`; the `file://` scheme is mangled by the navigate
tool, and http is a sanctioned verification surface per the 3.1 precedent):

- **Console: clean** — zero errors/warnings across load, the full `SCRIPTS.debug` walk, every stage
  focus, the exec tab, and (deliberately) the nudge-op cycle. No unresolved-agent / unknown-kind warns.
- **SC-005 glance test: PASS.** Captured `#/goal/CAST-412` (feature) and `#/goal/CAST-431` (debug)
  side-by-side — feature renders the **boxed segment bar** (`01 Shape the Problem … 04 Build & Ship`,
  no counter), debug renders the **rounded loop band + `↺ iter 2/3`**. The shape is nameable in well
  under 3s. **Resolved, not a carry-forward.**
- **InvestigationLedger / E2:** pass 1 **closed/collapsed**, pass 2 **live/open** (FR-007); the E2
  hero shows H2 **refuted struck-but-visible** + H3 **confirmed** (green) with the v4.2 weave; the L1
  pill renders below.
- **E3 @ dbg-05:** `test_coupon_apply_null_role_500` renders **FAIL · before** (red) then **PASS ·
  after** (green) — red precedes green, never a bare green badge.
- **`SCRIPTS.debug` walk:** all 9 beats fire in order with the correct focus/drill transitions
  (dbg-03 → dbg-04 → dbg-05 → L3 → `drill:execution` → close) and ORG-derived narration.
- **Thin exec tab:** CAST-431 opens a **2-run flat list + a 2-node shallow tree** ("2 sub-agents") —
  no deep dispatch tree (Decision 8), vs the feature's 13-node tree.
- **Feature un-regressed:** the feature guide-line ("…flagged RO2 on the open PR…") + nudge render
  byte-identical; the segment spine + feature roster work-stream are intact.

- **Nudge-op cycle on the debug canvas (still a non-blocking note):** the `NudgeCard` do-line carries
  the Phase-1 `data-op="nudge:n2"`, whose `nudge()` cycles the two feature-canned `NUDGES`. The
  *initial* debug nudge renders from data and the SCRIPTS.debug walk never fires the cycle; a manual
  click on the do-line cycles to the feature-canned nudge (pre-existing Phase-1 demo quirk). Confirmed
  live that a **reload restores the data nudge** ("Confirm the coupon-path repro"). Out of 3.3's
  scope; non-blocking.
