# Sub-phase 6.4: Showability Sign-Off — SC-002 Dry Run & Final Checklist

> **Pre-requisite:** Read
> `docs/execution/product-revamp-diecast-phase6-polish-showability/_shared_context.md` before
> starting this sub-phase. The binding constraints there are not optional.

## Objective

The phase gate passes end-to-end on the **dist file**: the high-level Phase 6 verification paragraph
holds, and the one item no machine can verify — a fresh viewer stating what the product does within
~3 minutes (SC-002) — is staged as a concrete human action with the artifact ready to hand over. This
is the **terminal node of the critical path** (6.1 → 6.2 → 6.3a → **6.4**) and **the project gate**.

## Dependencies
- **Requires completed:** Sub-phases **6.3a + 6.3b** (the dist file exists; the SC-006 map exists).
- **Blocks:** nothing (terminal). Only the post-mockup v2 planning session follows, consuming 6.3b's
  map.
- **Assumed codebase state:** `prototype/dist/diecast-prototype.html` is generated and content-final;
  `docs/plan/product-revamp-diecast-v2-surface-goal-map.md` exists.

## Estimated effort
0.25–0.5 session (~1h).

## Scope
**In scope:** the five-scenario click-through on the **dist file**; the post-fix `data-tour` audit
(all five tours); the SC-001/SC-007 final cross-check; staging the SC-002 fresh-viewer test; appending
the Phase 6 close note to `decisions-so-far.md`.
**Out of scope (do NOT do these):** any new surface/component/op; any data change; any new artifact
(the close note appends to `decisions-so-far.md` — it is **not** a new file); any test file; any
plan-review or reconciliation pass. **This sub-phase creates nothing new** — it executes checklists
defined above and records a verdict.

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `prototype/index.html` / `prototype/dist/diecast-prototype.html` | Modify (fixes only, if a gate item fails) | Content-final; 6.4 fixes only a genuine gate failure (then re-run `inline.mjs` for the dist) |
| `docs/plan/product-revamp-diecast-decisions-so-far.md` | Modify (append) | Append the Phase 6 close note + per-criterion SC-001/SC-007 verdicts (one paragraph, not a new artifact) |

## Detailed Steps / Key Activities

- **Five-scenario full click-through on the dist file** (not the dev file — **the distributable is
  what gets shown**): each of the five chooser scenarios walks start-to-finish.
- **Post-fix tour audit:** every `data-tour` stop in all five tours **still resolves** post-6.2 (6.2's
  flagged risk, closed here) — density fixes must not have orphaned any anchor.
- **SC-001/SC-007 final cross-check** against the refined requirements' success-criteria table: every
  flow shows ≥1 in-context decision record, and the prototype contains the autonomy-gated stop (SC-007
  final cross-check); record the **per-criterion verdicts** in a short closing note **appended to the
  decisions-so-far doc** (one paragraph, not a new artifact).
- **Stage the SC-002 showing:** hand the owner the **dist file path** + the suggested **3-minute path**
  (chooser → "Follow a feature" tour → morph beat → board). Recording the peer's statement is the
  owner's action, outside this plan's execution — **the one human action item this plan leaves open**
  (Decision 14).

## Verification

> **NO TESTS (binding):** every check below is **manual click-through / static observation**. In an
> autonomous run with no browser, satisfy each via the strongest static evidence (`node --check` of
> the dist module, grep/tour-anchor audits, a throwaway `/tmp` logic harness that is never committed)
> and record a non-blocking human-eyeball carry-forward for any rendered-pixel item. **Do not flag
> missing tests.** **This sub-phase IS the phase and project gate.**

**Verification (manual, from disk — this IS the phase and project gate) — verbatim from the plan:** On
`prototype/dist/diecast-prototype.html` from disk:
- each of the five chooser scenarios walks **start-to-finish**;
- each tour click-through **still anchors correctly** post-6.2 fixes;
- every flow shows **≥1 in-context decision record** and the prototype contains the autonomy-gated stop
  (**SC-007** final cross-check);
- **feature-vs-debug side-by-side contrast obvious** (SC-005 spot-check);
- the **SC-006 map exists and is exhaustive**;
- the slop-gate and drift-sweep results from 6.2 / 6.3a are **on record**.
- **SC-002 itself:** owner shows the dist file to 1–2 fresh peers using the chooser + tours and records
  whether they can state what the product does within ~3 minutes — **the one human action item.**

### Success Criteria (binary — every item must pass or carry forward with reason)
- [ ] All five chooser scenarios walk start-to-finish **on the dist file**; the morph plays; tours +
      demo overlay work; console clean.
- [ ] Every `data-tour` stop in all five tours resolves (no orphans from 6.2's density fixes).
- [ ] SC-001 (all flows walkable from disk) + SC-007 (autonomy-gated stop present; ≥1 in-context
      decision record per flow) cross-checked; per-criterion verdicts recorded in the close note.
- [ ] SC-005 feature-vs-debug contrast obvious (spot-check); SC-006 map exists + exhaustive (6.3b);
      6.2 slop-gate + 6.3a drift-sweep results on record.
- [ ] The Phase 6 close note (incl. SC verdicts + carry-forwards + the SC-002 staging) is **appended
      to `decisions-so-far.md`** — not a new artifact.
- [ ] SC-002 staged: dist file path + the suggested 3-minute path handed to the owner as the **single
      open human action item** (`human_action_needed: true`).

## Design review (verbatim from the plan)
- **No flags** — this sub-phase creates nothing new; it executes checklists defined above. The only
  output is the verdict note appended to decisions-so-far.

### Design Review Flags (carried, verbatim from the plan's consolidated table)
| Sub-phase | Flag | Action |
|-----------|------|--------|
| 6.2 → 6.4 | Density fixes can orphan `data-tour` anchors | Post-fix tour audit (all five tours) closed here |

## Execution Notes
- **Gate on the dist file, not the dev file** — the distributable is what gets shown; if a gate item
  fails, fix the dev `index.html`, **re-run `inline.mjs`**, and re-gate the dist.
- **SC-002 is, by definition, outside an autonomous run** (Decision 14) — stage it (artifact + 3-minute
  path) and mark it the single human action item; do not attempt to fake a fresh-viewer verdict. If
  SC-002 later fails with a fresh peer, **that outcome feeds the v2 map's rankings rather than blocking
  this phase** (Key Risk).
- **CF3 (de-em-dash):** confirm the standing unified de-em-dash carry-forward is recorded in the close
  note as resolved-or-carried (the new Phase 6 copy is em-dash-free; older copy folds into the unified
  pass per the owner direction).
- **Carry-forwards:** roll up every non-blocking human-eyeball carry-forward from 6.1–6.3a (slop-gate
  rendered re-checks, tour-popover styling, chart legibility, motion feel) into the close note as the
  single human-eyeball pass.
- **Spec-linked files:** none — greenfield (FR-020); no `/cast-update-spec`.
- **Plan review:** SKIPPED per run config — do not dispatch `/cast-plan-review` or any reconciliation
  pass. (Phase 6 plan Decision 16 records a **manual** `/cast-plan-review` as a user next-step instead
  — note it in the close.)
- **Failure policy (critical path):** 6.4 is the terminal critical-path node — a second failure here is
  **stop-and-report**, not log-and-continue.
- **Record borderline calls:** any final-gate judgment call → append a numbered entry to
  `docs/plan/product-revamp-diecast-borderline-calls.md` (continuing from #15).
