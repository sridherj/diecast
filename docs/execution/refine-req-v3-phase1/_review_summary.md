# Review Summary: refine-req-v3-phase1

Lightweight SMALL-CHANGE self-review of the split. The **source plan was already
plan-reviewed** (`2026-06-12-refine-requirements-v3-phase1-spikes.md` appendix: 5 issues found /
5 resolved), and the reconciliation verdict is COHESIVE, so this pass only checks that the split
faithfully preserves the source's gates, scope discipline, and verification rigor — it does not
re-open spike design.

## Open Questions

None blocking. The single goal-level open item is the **[USER-DEFERRED]** maker/checker model
tier, which Phase 1 deliberately does not touch (hand-run generation uses the session's own
model). Recorded in the source plan's Open Questions; no Phase-1 action.

## Review Notes by Sub-Phase

### sp1a — Maker Quality Ceiling
- **Scope/altitude:** ✓ — in/out-of-scope explicit; the conscious `/cast-preso-how`
  non-delegation is carried into Step 1a.2 and the success criteria, preventing the two named
  execution-time misfires (invoking the slide agent / skipping the discipline).
- **Verification (FR-003 faithfulness):** ✓ — the id-audit encodes **both** set-equality and
  per-block correspondence, per the source plan's Code-Quality resolution; called out as the
  pattern Phase 3 reuses.
- **One watch item (no edit):** "clearly beats" is partly static without a browser. Mitigated as
  the source plan prescribes — checker + rubric now, human-eyeball as an explicit carry-forward
  that never blocks an autonomous run.

### sp1b — Quote-Anchored Backbone Survival
- **Test rigor:** ✓ — mark-placement hit is scoped to the **intended block container** (source
  plan Tests resolution), turning the short/generic-quote comment into a real test; the
  `section_hint`-mismatch probe has an explicit recorded-outcome requirement (source plan Tests
  resolution).
- **Error/rescue:** ✓ — reanchor dispatch failure = one retry then record (FR-027 no-op, never
  fabricate); the 422 verbatim backstop counts against the gate.
- **Data safety:** ✓ — injectable `db_path` + scratch slug + `spikes/1b/` scratch DB asserted in
  the harness; no live house DB / real goal folder written.
- **Framing fidelity:** ✓ — the "DB-level orphaning cannot be caused by render variation alone"
  grounding insight is preserved so the executor measures the *real* exposure (silent mark loss +
  verbatim-carriage), not a phantom DB-orphan risk.

### G1 — Combined Phase-1 Gate
- **Gate preserved, not collapsed:** ✓ — G1 is a non-executable `gate_`-prefixed file; the
  per-spike forks (maker-vs-hybrid, id-in-DOM revisit-trigger) are surfaced to the owner, never
  silently re-scoped. Option C handles the one-green/one-triggered case so a green spike's
  independent downstream value (1b also gates Phase 4b) is not needlessly blocked.
- **Single owning artifact:** ✓ — G1 writes `spikes/PHASE1-GATE.md`, satisfying the source
  plan's Architecture resolution (the "both gates green → Phase 3" edge gets one owning artifact).

## Carry-Forwards Recorded (no Phase-1 action)

1. Maker-contract **"anchorable text carried verbatim in the DOM"** clause → Phase 3
   `/cast-update-spec` activity (logical-backbone addition).
2. Human-eyeball **browser pass** for both 1a quality and 1b mark placement → carried forward;
   never blocks an autonomous run.
3. Any **`cast-requirements-checker` anomaly** on maker HTML → recorded as Phase-4a input; the
   checker is replaced by a richer one there and must not be tuned in Phase 1.
