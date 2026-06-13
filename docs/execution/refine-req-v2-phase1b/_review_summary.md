# Review Summary: refine-req-v2-phase1b

## Review Mode

This execution plan was split **fully autonomously** (delegated, headless run — the delegation
context directs: "PROCEED FULLY AUTONOMOUSLY … do NOT ask the user any questions, do NOT pause at
AskUserQuestion gates; make sensible defaults and record them"). A self-review pass (SMALL CHANGE
discipline — at most one finding per section) was applied instead of dispatching five child
`/cast-plan-review` runs, because:
- The source plan was already plan-reviewed (it carries a six-item Decisions appendix from the
  2026-06-11 review), so the design forks are resolved upstream.
- All five sub-phases edit one prompt file (plus, in sp2, the template + checker doc); they are
  thin, sequential, and low-risk — not the multi-file architectural surface that warrants a fresh
  reviewer per sub-phase.

## Open Questions

**None blocking.** The source plan's Open Questions are "None blocking"; every planning fork was
resolved in its Decisions appendix (#1–#6) and adopted verbatim here. One non-blocking watch-item
carried from the plan: whether the HARD GATE's mandatory draft-review feels like friction in daily
use — revisit after the sp5 re-refinements.

## Defaults Recorded (autonomous decisions)

1. **5 sub-phases, all sequential, no gates.** The plan is "one session" but its Build Order has
   clean internal seams (detect → quote/decide → review/gate → regen/pin → verify). Split along
   those seams for focused, separately-verifiable contexts (skill bar: "prefer more focused
   sub-phases"). No parallelism — sp1–sp3 mutate the same agent prompt, so concurrent edits would
   conflict. No decision gates — the plan defines none.
2. **Output checkout = `/home/sridherj/workspace/diecast`.** The run preamble pins the working
   directory there and the plan states "All Phase 1b edits land in the external project checkout";
   the `/data/workspace/diecast` twin is left to the owner's usual reconcile-to-main.
3. **sp2 owns the template + checker-doc edits** (not sp4) — they are lockstep with the
   `## Decisions` prompt edit and share the additive-optional contract reasoning; keeping them in
   one context avoids a split-brain edit.
4. **sp4 owns regen + both prompt-pinning tests; sp5 owns the live re-refinements.** Separating the
   automated tripwire (cheap, deterministic) from the live LLM verification (slow, variance-prone)
   keeps each context's success criteria binary.

## Review Notes by Sub-Phase

### sp1_detection_brain
- Scope-mode vocabulary pinned to `cast-detailed-plan`'s exact tokens; plan instructs grepping
  that file before writing — carried into the sub-phase Execution Notes. No issue.

### sp2_evidence_and_decisions
- One finding (addressed in-plan): the checker-untouched invariant is load-bearing — added an
  explicit `REQUIRED_SECTIONS` assertion to the validation script so an accidental checker edit is
  caught, not assumed.

### sp3_reviewer_and_gate
- One finding (addressed in-plan): the meta-pass-stays-cut and no-HTTP-child constraints are easy
  to violate by over-building — added negative validation checks (`! grep meta-pass`, no
  `allowed_delegations`) and the prompt-size ceiling note, since the reviewer rubric is the
  largest single addition.

### sp4_regen_and_pins
- One finding (addressed in-plan): pins must assert on the **regenerated skill**, not just the
  source prompt, to catch regen drift (the plan's stated purpose). Made regen-survival an explicit
  pin requirement and success criterion.

### sp5_verification_refinements
- One finding (addressed in-plan): live LLM runs vary — instructed asserting on structure (a quote
  exists, a dated row exists, the mode is stated), not exact strings, to avoid flaky verification.
