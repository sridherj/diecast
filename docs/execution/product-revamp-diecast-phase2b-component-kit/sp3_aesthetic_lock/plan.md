# Sub-phase 2b.3: Aesthetic Lock — Signature Screen & the Slop Gate

> **Pre-requisite:** Read `docs/execution/product-revamp-diecast-phase2b-component-kit/_shared_context.md`
> before starting. It carries the inherited Phase 1 contracts, the 9 exported contracts, the
> binding constraints (NO TESTS, file:// legality, single-file packaging, fixture discipline,
> failure policy), and FULL AUTONOMY mode. This plan does not repeat them.

> **FULL AUTONOMY MODE (owner-approved):** never ask the user questions, never pause for approval
> gates, never go idle waiting for input. At decision gates pick the recommended option and
> document it inline in the sub-phase output. **Propagate this exact autonomy directive verbatim
> into the slop-gate checker delegations below** (`/cast-preso-check-visual`,
> `/cast-preso-check-tone`) — they inherit full autonomy.

## Objective

Compose the upgraded `#/goal/CAST-412` canvas **entirely from kit components** (StageSpine,
NudgeCard, line-density ColleagueCard in the work stream, an E1 EvidenceBlock in the stage-
artifacts zone, the 6A Decision pill in the receipt trail, the Guide treatment in the chat rail),
and prove the aesthetic at the Steve-Jobs bar: the signature screen **passes both cast-preso
slop-gate checkers** (`not-generic` / `not-ai-aesthetic`). Record the aesthetic as locked. This
**de-risks SC-004 before Phase 3 mass-produces screens**, and is **on the critical path** (C5: a
second failure stops-and-reports).

## Dependencies
- **Requires completed:** **both** 2b.2a (StageSpine, EvidenceBlock) **and** 2b.2b (Decision
  ladder, NudgeCard, EscalationRail, AutonomyDial). This is the Group 3 convergence sub-phase —
  it cannot start until both Group 2 members are Done.
- **Assumed codebase state:** `prototype/index.html` has the full 8-component kit on `#/kit`, the
  goal-canvas spine zone already swapped to `StageSpine` (2b.2a) and nudge zone to `NudgeCard`
  (2b.2b), token extensions, and the chosen Guide treatment.

## Scope

**In scope:**
- Upgrade `GoalCanvas` zone by zone until **zero Phase 1 stub markup remains** on the goal canvas:
  - spine → `StageSpine` (done in 2b.2a — confirm).
  - nudge stub → `NudgeCard` (done in 2b.2b — confirm).
  - work-happening stub → a 3-row stream of **line-density** `ColleagueCard`s with run-status
    (fixture data).
  - stage-artifacts stub → one **E1** `EvidenceBlock` (placeholder content; real evidence wiring
    is Phase 3).
  - receipt-trail stub → 6A `Decision` pills.
  - chat rail Guide lines → the locked Guide voice treatment.
- Drop one **4C** `ColleagueCard` onto the `#/board` stub route (a single card on a cream board
  frame — just enough for the density-drift verification; the real board is Phase 5).
- First-principles polish pass at the Steve-Jobs bar: spacing rhythm, type hierarchy, hairline
  weights, cream/paper surface tonality — judged against "would I show this without apology"
  (SC-004), gallery samples as reference only.
- **Run the slop gate** (the phase's headline verification — delegations below), rework, re-run
  until green.
- Append the **aesthetic-lock record** (chosen Guide treatment, any sample deviations, checker
  verdicts) to `product-revamp-diecast-decisions-so-far.md`. Append to `borderline-calls.md` only
  if a verdict is a borderline pass.

**Out of scope (do NOT do these — HOLD SCOPE):**
- Real spine vocabulary (Phase 2c — watermarked placeholders stay), real evidence content (Phase 3
  — E1 stub content stays), real org data (Phase 2a), the full board / marketplace (Phase 5).
- New components — the kit is closed at 8. If `GoalCanvas` still needs bespoke markup after wiring,
  **fix the kit, not the screen** (playbook 06's success metric: `GoalCanvas` should reduce to ~a
  data slice + component calls).
- Any test file / harness / CI (C1). Any `fetch()` / local ES-module import (C2).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `prototype/index.html` | Modify (compose `GoalCanvas` from kit; one card on `#/board`) | Has the full 8-component kit |
| `docs/plan/product-revamp-diecast-decisions-so-far.md` | Append | Aesthetic-lock record + checker verdicts |
| `docs/plan/product-revamp-diecast-borderline-calls.md` | Append (conditional) | Only if a slop-gate verdict is a borderline pass |

## Detailed Steps

### Step 2b.3.1: Compose the signature screen
- Wire `GoalCanvas` zone by zone per the Scope list. After this step, `GoalCanvas` should be
  ~a data slice + component calls — **zero bespoke stub markup**. The demo script must still walk
  end-to-end (morph included) from a disk-open.

### Step 2b.3.2: Density-drift check on two surfaces
- Render the colleague lockup at **4C density on `#/board`** (one board card) and **4B density in
  the goal-canvas work stream** — **same fixture, no field drift** (the high-level plan's explicit
  check; this is the second place the drift is checked, after 2b.1).

### Step 2b.3.3: First-principles polish pass (Steve-Jobs bar)
- Spacing rhythm, type hierarchy, hairline weights, cream/paper tonality. Judge "would I show this
  without apology" (SC-004). Gallery samples are reference only; if a cleaner rhythm beats them,
  take it and record the deviation.

### Step 2b.3.4: Run the slop gate (the headline verification — DELEGATE)
- Screenshot the signature screen (full canvas + chat rail, 1440px Chrome).
- **→ Delegate `/cast-preso-check-visual`** with the screenshot + a one-paragraph WHAT context,
  instructing it to verdict **specifically on the `not-generic` and `not-ai-aesthetic`
  dimensions**. Propagate FULL AUTONOMY into the delegation. **Adaptation note (pass it in the
  delegation context):** the checkers were built for slides; their slop dimensions — generic AI
  aesthetic, gradient-glass, template-feel — apply to app screens directly. **Ignore slide-specific
  findings** like "viewport fit for projection." A **fail on either dimension = rework the flagged
  element and re-run**; do not ship the phase on a fail.
- **→ Delegate `/cast-preso-check-tone`** on the signature screen's **visible copy** (nudge text,
  chat lines, evidence labels) — GPT-isms / em-dashes in UI copy are slop too (FR-018). Review and
  fix flagged copy.
- If a checker proves unusable on app screens in practice, fall back to its checklist applied
  manually and record the substitution in `borderline-calls.md`.

### Step 2b.3.5: Guide-distinctness flash test + token grep
- On the signature screen, confirm the Guide is identifiable as a distinct character in chat voice,
  nudge attribution, and the decision receipt **without reading labels** (self-administered flash
  test); record a screenshot as evidence.
- Token-discipline grep: **no raw hex values outside the `:root` block**; raspberry usage audited
  (needs-you semantics only).

### Step 2b.3.6: Record the lock
- Append the aesthetic-lock record to `decisions-so-far.md`: chosen Guide treatment, any sample
  deviations, the two checker verdicts (+ screenshots retained as evidence). Flag anything 2c/3
  must know (e.g. if a spine shape was adjusted during polish). If a verdict was a borderline pass,
  log it to `borderline-calls.md`.

## Verification

### Automated Tests (permanent)
- **None.** Constraint C1 forbids tests. Do not create any test file. The externalized judgment is
  the **checker-agent verdict**, not a test.

### Validation Scripts (temporary)
- None that run code. Static checks: grep for raw hex outside `:root`; grep confirming `GoalCanvas`
  contains no bespoke stub markup (only component calls); confirm the demo script array is intact.

### Manual Checks (the only verification — open from disk in Chrome and observe)
1. **Composed from the kit:** every zone of `#/goal/CAST-412` renders through a kit component;
   **zero Phase 1 stub markup remains** on the goal canvas; the demo script still walks end-to-end
   (morph included) from a disk-open.
2. **Density-drift (two surfaces):** 4C on `#/board` + 4B in the goal-canvas work stream render
   from the **same fixture with no field drift**.
3. **Slop gate GREEN (the headline):** `/cast-preso-check-visual` passes on both `not-generic` and
   `not-ai-aesthetic`; `/cast-preso-check-tone` clean (or flagged copy fixed and re-run). Verdicts
   + screenshots retained as evidence. **A fail on either visual dimension is reworked and re-run —
   the phase does not ship on a fail.**
4. **Guide distinctness:** label-free flash test passes on the signature screen (chat voice + nudge
   attribution + decision receipt); screenshot retained.
5. **Token discipline:** no raw hex outside `:root`; raspberry confined to needs-you semantics.
6. **Lock recorded:** the aesthetic-lock entry is in `decisions-so-far.md`; borderline passes (if
   any) in `borderline-calls.md`.

### Success Criteria (binary — every item must pass)
- [ ] `#/goal/CAST-412` is composed entirely from kit components; zero Phase 1 stub markup remains; `GoalCanvas` reduces to ~a data slice + component calls.
- [ ] The Phase 1 morph still walks end-to-end from a disk-open (no regression while re-skinning).
- [ ] Density-drift check passes on both surfaces (4C on `#/board`, 4B in the work stream, same fixture).
- [ ] `/cast-preso-check-visual` verdict is PASS on `not-generic` **and** `not-ai-aesthetic` (slide-specific findings ignored); any fail reworked and re-run; verdict + screenshot retained.
- [ ] `/cast-preso-check-tone` clean or flagged copy fixed; verdict retained.
- [ ] Guide label-free distinctness flash test passes; screenshot retained.
- [ ] No raw hex outside `:root`; raspberry audited (needs-you only).
- [ ] Aesthetic-lock record appended to `decisions-so-far.md`; borderline passes (if any) logged.

## Execution Notes
- **Gate honesty under full autonomy:** the slop-gate verdict comes from the **checker agents**,
  not self-assessment — this is the one externalized judgment in the phase. Retain verdicts +
  screenshots as evidence; a borderline pass is recorded in `borderline-calls.md`, not waved through.
- **Scope guard:** the signature screen uses placeholder spine vocabulary and stub evidence content
  — **that is correct** (2c/3 own the real content). The lock is *aesthetic*, not informational.
  **Watermarks stay.**
- **Architecture check:** after this sub-phase, if `GoalCanvas` still contains bespoke markup, the
  kit is incomplete — **fix the kit, not the screen** (playbook 06's success metric). Do not add a
  9th component to paper over a gap; extend an existing component's props.
- **No browser available?** This sub-phase's headline gate needs a screenshot. If Chrome can't be
  connected this session (per the prototype's known constraint — autonomous runs can't connect
  Chrome for visual gates), the slop-gate delegations get a **static verdict** based on the
  rendered HTML/CSS + a **human-eyeball carry-forward** flagged in the output; **do not block the
  phase**. Record the deferral explicitly in the aesthetic-lock entry and the output's
  `human_action_items`. (This matches the project's established no-browser-visual-gate posture.)
- **Failure policy (C5 — 2b.3 is CRITICAL):** retry once with refined steps; a **second** failure
  (e.g. the screen can't pass the slop gate after rework) → **stop and report** (do not ship a
  failed aesthetic lock — it would poison every Phase 3 screen built on it). Log the exact failure
  + what was tried in the output and manifest Notes.
- **Spec-linked files:** none (greenfield prototype, FR-020). Appends to plan-ledger docs only.
