# Sub-phase 4.4: Four-Family Stitch, Slop Gate & Drift Sweep

> **Pre-requisite:** Read `docs/execution/product-revamp-diecast-phase4-spike-data/_shared_context.md`
> before starting this sub-phase. The binding constraints there are not optional.

## Objective

All four families are clickable end-to-end from disk — **SC-001 and SC-005 fully met** — with
`SCRIPTS = {feature, debug, spike, data}` complete; the four-spine glance contrast is verified and
captured as a 4-up screenshot; the slop gate is green on the new surfaces; the drift grep is clean;
Phase 4's decisions are appended to decisions-so-far. This is the **terminal sub-phase on the
critical path** (4.1 → 4.3 → 4.4).

## Dependencies
- **Requires completed:** Sub-phases 4.1 + 4.2 + 4.3.
- **Assumed codebase state:** spike canvas + memo + E4 + `SCRIPTS.spike` (4.1); data canvas +
  notebook + E5 + the wired L3 resolution + `SCRIPTS.data` (4.2); the parity beat wired into
  `SCRIPTS.spike` (4.3); the Phase-3 feature/debug/morph surfaces untouched.

## Scope
**In scope:**
- The stitch pass (script-beat ordering, scaffolding-flag removal, `scriptKey` selection on all four
  routes, the Phase-3 morph demo still runs untouched).
- The two slop-gate delegations on the four new/changed surfaces.
- The extended drift grep + moving any stray literal into the generator.
- Capturing the 4-up screenshot evidence; writing the decisions-so-far appendix.

**Out of scope (do NOT do these):**
- Building or reshaping any canvas/surface (that is 4.1/4.2/4.3) — this is stitch + gates only.
- Editing `generate-org.mjs` except to move a stray literal already surfaced by the drift grep.
- Any Phase 5 surface (board/hiring/Layer-2); any test file; any plan-review/reconciliation pass.

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `prototype/index.html` | Modify (stitch only) | All four flows present; remove scaffolding flags, confirm `scriptKey` on all routes |
| `prototype/data/_build/generate-org.mjs` + `org.js` | Modify only if drift grep surfaces a stray literal | Frozen post-4.1; regenerate via the gate if a literal must move |
| `docs/plan/product-revamp-diecast-decisions-so-far.md` | Append (~15 lines) | Cumulative cross-phase log; gains the Phase 4 close record |
| `docs/plan/product-revamp-diecast-borderline-calls.md` | Append (only if a flagged taste call shipped) | Borderline-call log |

## Detailed Steps

### Step 4.4.1: Stitch pass
Confirm script-beat ordering in both new flows; remove any scaffolding flags; confirm `scriptKey`
selection on all four routes; verify the morph demo (Phase 3) still runs untouched — Phase 4 must not
have disturbed the anchor set.

### Step 4.4.2: Slop gate on the four new/changed surfaces
Screenshot the four surfaces — spike canvas, data canvas, parity moment, E5 reconciled-report state.
- → **Delegate: `/cast-preso-check-visual`** — verdict scoped to `not-generic` / `not-ai-aesthetic`;
  ignore slide-specific findings. Pass the FULL AUTONOMY directive to the child.
- → **Delegate: `/cast-preso-check-tone`** on visible copy (narration, nudge text, memo prose,
  reconciliation note — FR-018: no GPT-isms, hyphens not em dashes). Pass FULL AUTONOMY to the child.
- Review checker output, rework, re-run until green; **do not close the phase on a fail.**
- **No-browser note:** if the slop-gate checker agents are not in this runner's allowlist or no
  browser is connectable, perform a best-effort STATIC self-assessment per full-autonomy and record
  a non-blocking human-eyeball carry-forward (re-run on a real 1440px Chrome screenshot). Never block.

### Step 4.4.3: Extended drift grep
Re-run 2a.3's recorded command extended with this phase's tokens
(`CAST-452 · CAST-461 · 180ms · 200ms · 1h40m · 8%` + the source names) across `prototype/`. Every
hit must be in `data/org.js` / `data/_build/`. Move any stray literal into the generator (regenerate
via the gate). The 2b `#/kit` fixture exception, if still live, remains the one sanctioned allowlist
entry.

### Step 4.4.4: Evidence + decisions appendix
Capture the 4-up screenshot evidence; write the ~15-line Phase 4 decision summary into
`decisions-so-far.md`; log any borderline pass to `borderline-calls.md`.

## Verification

> **NO TESTS (binding):** every check below is **manual click-through / static observation**. With no
> browser, satisfy the script-walk and anchor checks statically; the slop gate and the SC-005 4-up
> glance are recorded as non-blocking human-eyeball carry-forwards when no browser is connectable.
> **Do not flag missing tests.** The slop-gate verdicts must still come from the external checker
> agents whenever they are reachable — self-assessment is the fallback, not the default.

**Verification (manual click-through — the phase's headline checks) — verbatim from the plan:**
- From disk: each of the four goal routes (`CAST-412 / 431 / 452 / 461`) walks its script
  start-to-finish with "Next ▸", console clean throughout; the nav rail lists all four with
  family tags.
- **The 4-up glance test (SC-005):** screenshot all four canvases side by side — a viewer
  names each family in <3 seconds citing the spine shape (segment bar / loop band + ↺ /
  timebox meter / pipeline DAG). Keep the composite as evidence.
- **High-level plan verification restated and checked:** the spike flow produces a verdict
  artifact linked from a decision (`spike_ref` linkage visible both directions); the data
  flow ends in a rendered chart/table, not text; both families render the familiar-tool
  surface for their step (memo+timebox for spike, notebook+chart for analysis);
  iteration/timebox state shown cleanly (meter + extension chip; collapsed-not-deleted
  cells/versions).
- L3 budget audit: exactly one L3 per flow across all four flows (the 2a gate guarantees
  the data; this checks the *rendering* — no stray needs-you chips).
- **Slop gate (continuous, per the high-level risk table):** screenshot the four new/changed
  surfaces — spike canvas, data canvas, parity moment, E5 reconciled-report state →
  **Delegate: `/cast-preso-check-visual`** (verdict scoped to `not-generic` /
  `not-ai-aesthetic`; ignore slide-specific findings) and
  **Delegate: `/cast-preso-check-tone`** on visible copy (narration, nudge text, memo prose,
  reconciliation note — FR-018: no GPT-isms, hyphens not em dashes). Review checker output,
  rework, re-run until green; do not close the phase on a fail.
- **Drift grep re-run** (2a.3's recorded command, extended with this phase's tokens:
  `CAST-452 · CAST-461 · 180ms · 200ms · 1h40m · 8%` and the source names) across
  `prototype/` → every hit is in `data/org.js` / `data/_build/`; the 2b `#/kit` fixture
  exception, if still live, remains the one sanctioned allowlist entry.
- Reduced-motion pass over the parity reveal and any new transitions (≤200ms fades).
- Append the Phase 4 decision summary (~15 lines) to
  `docs/plan/product-revamp-diecast-decisions-so-far.md`.

### Success Criteria (binary — every item must pass or carry forward with reason)
- [ ] All four goal routes walk their scripts end-to-end; console clean; nav rail lists all four.
- [ ] 4-up glance contrast verified (or recorded eyeball carry-forward); composite kept as evidence.
- [ ] `spike_ref` both-directions, E5 inline-`<svg>` terminal state, familiar-tool surfaces, clean
      iteration/timebox state all restated and confirmed.
- [ ] Exactly one L3 rendered per flow; no stray needs-you chips.
- [ ] Slop gate green on the four surfaces (external checkers where reachable; static self-assessment
      + carry-forward otherwise).
- [ ] Extended drift grep clean (every hit in `data/`); any stray literal moved via the generator.
- [ ] Phase-3 morph demo still runs untouched; 6×1 vt- anchors intact; reduced-motion fades ≤200ms.
- [ ] Phase 4 decision summary appended to `decisions-so-far.md`; borderline pass logged if taken.

## Design review (verbatim from the plan)
- **Gate honesty under full autonomy:** checklist criteria pre-written (above) before the
  run; slop-gate verdicts come from the external checker agents; screenshots + verdicts
  retained; borderline passes logged to `borderline-calls.md`.
- **Parallel-phase courtesy (Phase 5):** before closing, confirm no collisions with Phase 5's
  in-flight banner sections of `index.html` (Phase 4 owns the two goal canvases + parity;
  Phase 5 owns board/hiring/layer2 sections; the generator batch was 4.1-only). If a merge
  conflict surfaces, the section-partition rule resolves it — no shared-zone edits without
  reconciliation.

### Design Review Flags (this sub-phase's rows, verbatim from the plan)
| Sub-phase | Flag | Action |
|-----------|------|--------|
| 4.4 | Self-judged taste under full autonomy | External slop-gate checkers + pre-written checklist; evidence retained |
| 4.4 | Parallel Phase 5 editing the same `index.html` | Banner-section partition (2b/3 precedent); Phase 4 owns its sections + the 4.1 generator batch |

## Execution Notes
- The slop-gate checklist criteria are **pre-written above** — judge against them before the run, not
  after, to keep the gate honest under full autonomy.
- The drift grep is the **extended** 2a.3 command — include this phase's new tokens.
- **Phase 5 courtesy:** confirm no collisions with Phase 5's banner sections before closing; Phase 4
  owns the CAST-452/CAST-461 canvases + the parity section + the 4.1 generator batch only.
- **Spec-linked files:** none — greenfield prototype (FR-020); no `/cast-update-spec`.
- **Plan review:** SKIPPED per run config — do not dispatch `/cast-plan-review` or any reconciliation
  pass; this sub-phase is stitch + slop-gate + drift only.
