# Review Summary: refine-req-v3-phase2

## Review Basis

The source plan (`docs/plan/2026-06-12-refine-requirements-v3-phase2-commenting-fallback.md`)
already carries a **BIG CHANGE** `cast-plan-review` (Architecture 2/2, Code Quality 3/3, Tests
3/3, Performance 2/2 — all resolved, 0 deferred, verdict "sound and implementable as written")
plus the cross-phase reconciliation pass. These three sub-phase files are faithful
decompositions of that reviewed plan, not new design. This summary records a focused
SMALL-CHANGE self-review (≤1 issue per section) confirming the decomposition preserved the
reviewed decisions, rather than re-litigating settled forks.

## Open Questions

**None blocking.** All taste-level forks were auto-decided under the binding seed decisions and
recorded in the source plan (Decisions made autonomously #1–#6) and reconciliation. The
goal-level `[USER-DEFERRED]` model-tier knob does not touch Phase 2 (no LLM in any Phase-2 path).

One **non-blocking carry-forward** (not a question — a project-standard deferral): SC-006
unprompted-usability cannot be verified in an autonomous run (no browser). 2c captures a static
verdict and records "human eyeballs SC-006 on a served render" as an explicit follow-up; the
phase does not block on it.

## Review Notes by Sub-Phase

### sp2a — Honest Fallback
- **Architecture:** helper lives in `goal_card.py`, `renderer.py` imports it — matches the real
  `renderer → goal_card` direction (verified at `renderer.py:41`). No cycle. ✓
- **Code Quality:** the strip-application matrix is fully enumerated (6 `escape()` points) and
  explicitly excludes the markdown pipeline (`_md_to_html`) — plan-review A1 guardrail carried
  into Scope/Out-of-scope. CQ2 (simple link regex + pinned degradation) and CQ3 (leading-punct
  normalization) carried into Steps 2a.1/2a.4. ✓
- **Tests:** T1 edge cases (unbalanced/nested/lone/CQ2-degradation) and T2 (pipeline-still-
  renders negative guard) promoted to named cases in Verification. ✓
- **Performance:** P1 fixpoint cap (≤5 passes) carried into Step 2a.1. ✓
- **Note (not a blocker):** the hard 2a → 3b import contract is called out in both Objective and
  Execution Notes — the single most important thing for an executor not to drift on.

### sp2b — Discoverable Commenting
- **Architecture:** JS-injection behind the slug guard (not template) preserves FR-028 and keeps
  goldens free of served-only chrome — mirrors the convergence-chip pattern. ✓
- **Code Quality:** `.rr-controls`-absent defensive no-op carried into Step 2b.1; class-only
  selectors / no-`id=` repeated in Scope + Success Criteria. ✓
- **Spec:** the `/cast-update-spec` activity is marked **mandatory** (not optional), with a
  bounded diff (FR-028 clause + SC-009 selector) and an explicit check that DOM contract +
  decision-#7 flow stay verbatim. ✓
- **Tests:** T3 mapped to existing slug-free golden coverage for the `file://` negative case;
  the positive case is the new browser UI assertion. ✓

### sp2c — Green Gate
- **Tests/Process:** single reviewed regen; per-family diff review (13 families) with explicit
  "anything else is a regression" discipline; structural battery + `test_fr007_readonly_guard.py`
  re-run; determinism re-run pins byte-stability. ✓
- **Scope guard:** 2c makes no code changes — defects route back to 2a/2b then re-run, never
  patched in 2c. ✓

## Verdict

Decomposition is faithful to the reviewed source plan; no new open questions surfaced; the one
SC-006 carry-forward is a project-standard non-blocking deferral. Ready to execute.
