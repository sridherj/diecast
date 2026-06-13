# Sub-phase 5.4: Stitch, Cross-Links, Slop Gate & Drift Sweep

> **Pre-requisite:** Read
> `docs/execution/product-revamp-diecast-phase5-colleague-surfaces/_shared_context.md` before
> starting this sub-phase. The binding constraints there are not optional.

## Objective

The three sub-streams read as **one product**: every cross-surface link lands, the phase's surfaces
pass the slop gate, the drift grep is clean, and the **Phase 5 verification paragraph from the
high-level plan passes as one continuous click-through**. This sub-phase introduces no new design —
**it exists to enforce the earlier ones**. It is the **terminal node of the critical path**
(5.0 → 5b → 5.4).

## Dependencies
- **Requires completed:** Sub-phases **5a + 5b + 5c** (all three sub-streams landed in `index.html`).
- **Blocks:** nothing (terminal). Phase 6 consumes this phase's routes afterward.

## Estimated effort
0.5–0.75 session (~2h), including gate reruns.

## Scope
**In scope:** the cross-link audit; the slop gate on six surfaces (delegated visual + tone checks);
the extended drift grep; the script/state/reload sanity pass.
**Out of scope (do NOT do these):** any new surface or component; any new op; any data change (no
generator touch — 5.0 owns it); any test file/suite/harness; any plan-review or reconciliation pass;
touching the Phase 4 canvas/parity sections beyond the read-only vt- spot-check.

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `prototype/index.html` | Modify (fixes only) | Carries all three sub-streams; 5.4 fixes broken links / slop flags surfaced by the audit |
| `docs/plan/product-revamp-diecast-decisions-so-far.md` | Modify (append) | Append the Phase 5 close record / decision summary (mirrors Phase 4's close) |

## Detailed Steps / Key Activities

- **Cross-link audit (the colleague-thesis glue):** every agent avatar → `#/agent/:slug` (**an avatar
  that goes nowhere is a tool icon**); board escalation badge → CAST-417 frame → "escalated to me" →
  board (the loop-back); ticket PR link present; trail row ↔ decision frame ↔ ticket chip ID-match
  spot-check; onboarding's dial link; reqs-doc ↔ canvas entry link; marketplace "Hire for a
  capability" → `#/hire`.
- **Slop gate** on **six surfaces**: board · ticket log · CAST-417 escalation frame · stack-ranked
  report · agent resume · reqs-doc.
  → **Delegate:** `/cast-preso-check-visual` + `/cast-preso-check-tone` on screenshots of the six
  surfaces, scoped (as in Phases 2b–4) to **not-generic / not-ai-aesthetic**. Review output; fix flags
  and re-run failed surfaces. **Propagate the FULL-AUTONOMY directive to the child checkers** (no user
  questions, pick the recommended option). In a no-browser autonomous run, the checkers self-assess
  against the strongest available static evidence and any rendered-pixel residue is a non-blocking
  human-eyeball carry-forward (the inherited Phase 2b–4 posture).
- **Drift grep extension + re-run:** add `CAST-417 · PR #<the generator's actual PR number> · 99.4 ·
  312 · 6 candidates · 12 contracts · 8-agent chain · the 5 dimension names · the PM persona's name ·
  cast-export-csv` to the Phase 3/4 grep set; **all canonical strings must originate from `org.js`
  only** (2b's `#/kit` fixtures remain the one sanctioned exception until its data swap).
- **Script + state sanity:** `SCRIPTS.hiring` advances cleanly alongside direct wizard clicks;
  dial/filters/disclosures all **reset on reload** (no persistence, ORG unmutated); vt- transition
  spot-check on `#/board` ↔ goal routes (**no duplicate-anchor regressions** from new routes).

## Verification

> **NO TESTS (binding):** every check below is **manual click-through / static observation**. In an
> autonomous run with no browser, satisfy each via the strongest static evidence (`node --check`,
> grep audits, a throwaway `/tmp` logic harness that is never committed, slop-gate self-assessment on
> the best available evidence) and record a non-blocking human-eyeball carry-forward for any
> rendered-pixel item. **Do not flag missing tests.** **This sub-phase IS the phase gate.**

**Verification (manual, from disk — this IS the phase gate) — verbatim from the plan:** The
high-level Phase 5 verification, verbatim:
- the four-frame arc reads as one story with consistent chrome;
- the assignee filter works;
- the ticket shows the activity log with inline violations + rework 1/3 + PR link;
- the hiring funnel clicks assessment → federation → stack-ranked report → hire → onboard;
- the dial toggle visibly promotes an L2 to an L3 stop.

**Plus:**
- **every avatar** on board, ticket log, hiring report, marketplace, and trail opens the right resume;
- **both slop-gate checkers pass** on all six gated surfaces;
- the **drift grep returns hits only from `org.js`**.

### Success Criteria (binary — every item must pass or carry forward with reason)
- [ ] Four-frame arc + assignee filter + ticket activity log + hiring funnel + dial L2→L3 promotion all
      pass as one continuous click-through.
- [ ] Every agent avatar on every gated surface opens the correct `#/agent/:slug` resume (no dead
      avatars).
- [ ] The loop-back (board badge → CAST-417 → "escalated to me" → board with filter) closes; all
      cross-links land; ID-match spot-checks pass.
- [ ] Slop gate (visual + tone) passes on all six surfaces — or each residual flag is a recorded
      non-blocking carry-forward with reason.
- [ ] Extended drift grep clean — every canonical string originates from `org.js` (only `#/kit`
      fixtures exempt).
- [ ] `SCRIPTS.hiring` + wizard clicks stay in sync; dial/filters/disclosures reset on reload (ORG
      unmutated); 6×1 vt- anchors intact (no duplicate-anchor regression); `node --check` clean.
- [ ] Phase 5 close record appended to `decisions-so-far.md`.

## Design review (verbatim from the plan)
**No new flags — this sub-phase exists to enforce the earlier ones.**

(The only standing cross-phase flag the runner should remain aware of: any em-dash / AI-slop tone
residue surfaced by `/cast-preso-check-tone` joins the standing de-em-dash carry-forward from Phase 4
— a unified pass is deferred, non-blocking, per the owner direction.)

### Design Review Flags (carried, verbatim from the plan's consolidated table)
| Sub-phase | Flag | Action |
|-----------|------|--------|
| all | New routes could mint duplicate vt- names | No new vt- names; anchors live on shell zone wrappers only (2b rule) — spot-checked here |

## Execution Notes
- **Slop-gate surface list = six** (board, ticket, escalation, report, resume, reqs-doc) — Decision 17;
  the per-phase-gates precedent (Phases 3/4 gated 4 surfaces each) scaled to this phase's surface
  count; Phase 6 re-gates everything anyway.
- **Delegated child agents** (`/cast-preso-check-visual`, `/cast-preso-check-tone`) MUST receive the
  full-autonomy directive verbatim — no approval gates, pick the recommended option, return findings.
- **Failure policy (critical path):** 5.4 is the terminal critical-path node — a second failure here
  is **stop-and-report**, not log-and-continue.
- **Phase 6 hand-off:** after 5.4, the complete route table, the `DigestNotice`/`RadarChart`/`Sparkline`
  helpers, `SCRIPTS.hiring`, and the extended drift-grep / slop-gate surface list are all exported for
  Phase 6's polish + full re-run.
- **Spec-linked files:** none — greenfield (FR-020); no `/cast-update-spec`.
- **Plan review:** SKIPPED per run config — do not dispatch `/cast-plan-review` or any reconciliation
  pass.
