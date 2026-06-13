# Sub-phase 6.2: The Gate — Density/Consistency Pass + Full Slop-Gate Sweep

> **Pre-requisite:** Read
> `docs/execution/product-revamp-diecast-phase6-polish-showability/_shared_context.md` before
> starting this sub-phase. The binding constraints there are not optional.

## Objective

Every screen in the prototype — including the three new Phase 6 surfaces (chooser, tour popover,
demo-script overlay) — passes `not-generic` / `not-ai-aesthetic`, and a cross-surface
density/consistency pass has removed the tells that say "mockup": filler text, skeleton corners,
token drift, inconsistent grammar. This is the **SC-004 gate ("showable without apology")** run as a
single full sweep, **superseding the per-phase spot gates** (Phases 2b–5 each gated ≤6 surfaces; this
is the every-screen re-run). On the critical path (6.1 → **6.2** → 6.3a → 6.4).

## Dependencies
- **Requires completed:** Sub-phase **6.1** (the new surfaces — chooser, tours, demo overlay — must
  exist to be gated).
- **Assumed codebase state:** `prototype/index.html` carries every Phase 1–5 surface plus the 6.1
  chooser / `TOURS` / demo overlay / `tour-*` overrides / `data-tour` attributes.

## Estimated effort
1 session (~3h), gate reruns included.

## Scope
**In scope:** the cross-surface density/consistency checklist (one sweep, all routes); the **21-capture**
full slop-gate sweep (delegated visual + tone checks); the tone pass on the new Phase 6 copy.
**Out of scope (do NOT do these):** any new surface or component; any new op; the inliner / dist
(6.3a); the SC-006 map (6.3b); any ORG generator batch or `org.js` hand-edit; any test file; any
plan-review or reconciliation pass. **Density fixes must NOT orphan `data-tour` anchors** (see design
review).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `prototype/index.html` | Modify (fixes only) | Carries all Phase 1–6.1 surfaces; 6.2 fixes density/consistency tells + slop flags surfaced by the sweep, preserving `data-tour` attributes |

## Detailed Steps / Key Activities

### Step 6.2.1: Density + consistency pass (one sweep, all routes) — the checklist
- **Token discipline:** grep `prototype/index.html` for hex literals **outside `:root`** → migrate to
  tokens. (The Phase 4 parity ink-dark pane already uses tokens; it stays the **one sanctioned
  identity exception**.)
- **Rhythm + type:** the 8px spacing scale holds; **mono = machine voice** (ids, stats, logs), **sans
  = human prose**, consistently; label casing and button hierarchy (hero/outline/ghost) match the
  escalation-rail grammar everywhere.
- **Grammar consistency:** avatar shapes (circle / square-outline / square-fill / diamond), L-badge
  colors, ●/◐/○ confidence (**no percentages anywhere**), receipts/pills render identically across
  routes.
- **Density:** every panel carries believable product-grade content — **no empty corners, no one-line
  stubs** left from phase stitching; sweep rendered output for `lorem`, `TODO`, `FIXME`,
  `placeholder`, `stub`, and the **Phase 1 watermark idiom**; confirm `placeholder:false` spine state
  shows no residue.

### Step 6.2.2: Full slop-gate sweep — the 21 captures
Per-phase gates covered ≤6 surfaces; **this is the every-screen re-run** the high-level plan requires.
Capture via the `/browse` headless-browser skill against the `file://` URL (manual Chrome screenshots
are an acceptable fallback; **in a no-browser autonomous run, self-assess against the strongest static
evidence and record a non-blocking human-eyeball carry-forward** — the inherited Phase 2b–5 posture).

**The 21 captures (Decision 12 — fixed list):**
1. `#/` chooser at rest
2. a tour popover open (feature tour, stop ~2)
3. demo-script overlay open over the feature canvas
4. `#/goal/CAST-412` at rest
5. CAST-412 execution drill-in, focus-run tree open
6. CAST-412 post-morph debug-shape state
7. `#/goal/CAST-431` (iteration panel + E2/E3 visible)
8. `#/goal/CAST-452` at rest
9. CAST-452 parity moment open
10. `#/goal/CAST-461` at rest (◐-flagged E5)
11. CAST-461 resolved state (post-L3 re-rendered E5)
12. `#/board`
13. `#/ticket/CAST-412`
14. CAST-417 escalation frame (`#/decision/…`)
15. `#/decisions/CAST-412` (trail + dial)
16. `#/hire` step 3 stack-ranked report (remaining wizard steps eyeballed, **not formally gated**)
17. `#/marketplace`
18. `#/agent/crud-orchestrator` (resume + one ops tab)
19. `#/skills/new`
20. `#/layer2`
21. `#/reqs/CAST-412` (delta view on)

→ **Delegate:** `/cast-preso-check-visual` + `/cast-preso-check-tone` on each capture, scoped (as in
Phases 2b–5) to **`not-generic` / `not-ai-aesthetic`**. **Propagate the FULL-AUTONOMY + no-browser
static directive verbatim to the child checkers.** Review verdicts; **fix flags in
`prototype/index.html`**; **re-capture and re-gate failed surfaces only** (batch captures first, then
run checkers over the batch — Decision 12 / design review).

### Step 6.2.3: Tone pass on the new copy
Chooser blurbs, tour stop text, demo-script talking points run through the tone check with the
captures; **FR-018 vocabulary rules** (Diecast, `cast-*`, Layer not Tier, maker-checker, **hyphens
not em dashes, no GPT-isms**) applied. Any em-dash / AI-slop residue surfaced across older copy joins
the **standing CF3 de-em-dash carry-forward** (the unified pass folds into Phase 6 — non-blocking; the
new 6.1 copy should already be em-dash-free).

## Verification

> **NO TESTS (binding):** every check below is **manual click-through / static observation**. In an
> autonomous run with no browser, satisfy each via the strongest static evidence (grep audits,
> `node --check`, slop-gate self-assessment on the best available evidence) and record a non-blocking
> human-eyeball carry-forward for any rendered-pixel item. **Do not flag missing tests.**

**Verification (manual) — verbatim from the plan:**
- The consistency checklist (6.2.1) has **every box checked**.
- All **21 gate captures** have **passing verdicts from both checkers**; every flagged surface was
  fixed and re-gated.
- **Zero hardcoded hex outside `:root`.**
- **Zero** `lorem` / `TODO` / `FIXME` / `placeholder` strings render anywhere (including the retired
  Phase 1 spine watermark).

### Success Criteria (binary — every item must pass or carry forward with reason)
- [ ] Density/consistency checklist (token discipline · rhythm+type · grammar · density) fully passes
      across all routes.
- [ ] 21 captures gated by `/cast-preso-check-visual` + `/cast-preso-check-tone`; each passes
      `not-generic` / `not-ai-aesthetic` — or each residual flag is a recorded non-blocking
      carry-forward with reason (no-browser posture).
- [ ] New Phase 6 copy passes the tone check (FR-018; em-dash-free); older-copy em-dash residue folded
      into the standing CF3 carry-forward.
- [ ] Zero hex outside `:root` (the Phase 4 parity pane the one sanctioned identity exception); zero
      lorem/TODO/FIXME/placeholder/stub strings render; Phase 1 watermark gone.
- [ ] **All `data-tour` attributes preserved** through every density fix (no orphaned tour anchors —
      6.4 audits this); `node --check` clean; vt- anchors `6×1`; closed 5-op set intact; no new op; no
      ORG batch; `org.js` untouched.

## Design review (verbatim from the plan)
- ⚠ **Gate volume:** 21 captures × 2 checkers is the **largest gate run of the project** — batch the
  captures first, then run checkers over the batch; **re-gate only failures** (activities reflect
  this). Budgeted inside the session estimate.
- ⚠ **Fixes can move tour anchors:** density fixes that restructure DOM can **orphan `data-tour`
  stops**. Rule: **6.2 fixes preserve `data-tour` attributes**; a post-fix tour click-through is part
  of 6.4's final checklist.
- **NO TESTS compliance:** everything here is screenshots + human checklist; no harness. ✓

### Design Review Flags (this sub-phase's rows, verbatim from the plan's consolidated table)
| Sub-phase | Flag | Action |
|-----------|------|--------|
| 6.2 | Largest gate run of the project (21 × 2 checkers) | Batch captures, then checkers; re-gate failures only |
| 6.2 | Density fixes can orphan `data-tour` anchors | Fixes preserve `data-tour`; post-fix tour audit in 6.4 |

## Execution Notes
- **Delegated child agents** (`/cast-preso-check-visual`, `/cast-preso-check-tone`) MUST receive the
  full-autonomy directive verbatim — no approval gates, pick the recommended option, return findings.
  In a no-browser run they self-assess against the best available evidence; rendered-pixel residue is
  a non-blocking carry-forward.
- **Fix the component, not the screen** (Key Risks): because the render is data-driven, a structural
  fix at the kit/component level propagates everywhere — prefer it over per-screen patches. A late
  structural failure should be drift-sized, not design-sized (the per-phase gates already passed these
  surfaces; 6.2 is a regression re-run).
- **Hiring wizard:** formally gate the **report-card step only** (capture #16); the remaining wizard
  steps are eyeballed, not formally gated (they share one layout family) — escalate into the gate list
  only if the eyeball is doubtful (Phase 6 plan Open Questions).
- **Spec-linked files:** none — greenfield (FR-020); no `/cast-update-spec`.
- **Plan review:** SKIPPED per run config — do not dispatch `/cast-plan-review` or any reconciliation
  pass.
- **Failure policy (critical path):** 6.2 is a critical-path node — a second failure is
  **stop-and-report**.
- **Record borderline calls:** any slop-gate verdict taken as a borderline pass (not a clean pass, not
  reworked) → append a numbered entry to `docs/plan/product-revamp-diecast-borderline-calls.md`
  (continuing from #15), as 2b.3 did (#6).
