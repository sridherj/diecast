# Review Summary: refine-req-v3-phase3

## Review approach

The source plan (`2026-06-12-refine-requirements-v3-phase3-maker-pipeline.md`) already carries a full
**cast-plan-review BIG-CHANGE appendix** — 9 issues found / 9 resolved (Architecture 3, Code Quality 2,
Tests 3, Performance 1) — and those resolutions are baked into the sub-phase plans (A1 env hygiene, A2
reaper ceiling, A3 `failed`-state handling, CQ1 strip-import, CQ2 strict extraction, T1 fallback-passes-
gate, T2 latch-deterministic races, T3 reaper test, P1 in-flight semaphore). The reconciliation edits
applied during this split are **owner-resolved decisions**, not open questions. A fresh per-sub-phase
`/cast-plan-review` (SMALL-CHANGE) would re-derive the same resolved findings, so this is a self-review
pass over split fidelity and cross-sub-phase consistency instead.

## Open Questions

1. **RESOLVED during this run (owner, interactive):** how Phase 3 records/surfaces the
   `structural_violation` flag given 4a owns the four rich flag columns and Phase 3 has no scoring.
   **Decision: minimal signal — `flagged` status + reason in the existing `error` field + a
   `served-by: structural_violation` artifact stamp that 3d turns into a "needs review" badge; the four
   4a columns layer on top later.** No remaining open question.

(No other open questions block execution.)

## Review Notes by Sub-Phase

### Sub-phase 3a (WHAT/HOW agents)
- Clean. Verbatim-carriage + DOM rules in the HOW contract must match 3b's gates exactly — flagged in
  both files as a fixed-by-plan contract, so drift between them is the one thing to watch at exec.
- Revision (f) is documentation-only: ensure NO trailer/`gaps[]` handling code is written (called out
  in Scope + Success Criteria).

### Sub-phase 3b (maker gate)
- The 2a→3b hard edge is the only real build-order risk; the plan forbids copying the stripper and
  requires block-or-lift. Good.
- Revision (b) `container_text_index` gets its own independent test class so 4b-1 imports it on a
  proven contract — verified present in Verification.

### Sub-phase 3c (render job service)
- Carries the OVERRIDE (the single largest deviation from the source plan text) + revision (a). Both
  are spelled out with explicit "this supersedes the source plan" notes so an executor doesn't
  accidentally implement the old fallback-on-structural-exhaustion behavior.
- Column ownership is explicit: `heartbeat_at` here, the four flag columns NOT here (4a-2). Success
  Criteria asserts the absence.
- Watch: "best attempt" in Phase 3 = last extractable HTML (no scoring). Called out so the executor
  doesn't pull 4a scoring forward.

### Sub-phase 3d (route + generating state)
- Override ripple correctly distinguishes `flagged`→`ready`+badge from `failed`→terminal affordance.
  The badge is response-layer (artifact stays byte-stable) — asserted in tests.

### Sub-phase 3e (spec + e2e gate)
- The `/cast-update-spec` pass gains delta #6 (the override) beyond the source plan's five deltas.
- Inline approval gate (review diff before approval) is the one human-approval point in Phase 3.

## Cross-sub-phase consistency check

- `render_jobs` status vocabulary is consistent across 3c (defines `flagged`) and 3d (serves it as
  `ready` + badge).
- The `served-by` artifact stamp is created in 3c and consumed in 3d; 3e records it in the spec and the
  hand-off notes — single mechanism, no divergence.
- The stage-timeout list (3c) is the seam 4a/5 extend; the reaper reads it; documented in the hand-off.
- No two parallel sub-phases (3a ∥ 3b) write the same file. 3c/3d share
  `requirements_render_service.py` but run sequentially.
