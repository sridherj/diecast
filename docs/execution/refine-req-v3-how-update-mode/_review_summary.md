# Review Summary: refine-req-v3-how-update-mode

The source plan was already through a **BIG CHANGE `cast-plan-review`** (its end-of-file Decisions
appendix — six executor-level refinements applied inline). The split into sub-phases is mechanical and
preserves the reviewed plan verbatim, so this summary consolidates (1) the two reconciliations resolved
interactively at split time, and (2) the plan's own Open Questions, re-homed to the sub-phase that owns
each as an execution-time decision. No new design issues were introduced by the split.

## Resolved at split time (owner-decided, interactive)

1. **1a verdict materialization** — RESOLVED: a **recorded verdict** in
   `spikes/update-fidelity/verdict.md`, NOT a `gate_`/`G` orchestrator stop. sp3a/sp3b list it as a hard
   dependency and read the file. (Matches the phase-4b precedent of no orchestrator gates.)
2. **Spec version target** — RESOLVED: **v7 → v8** (the on-disk spec is already v7 after Phase 5
   gap-fill; the plan body's "v6 → v7" is stale numbering). The contract content is unchanged; only the
   version label is corrected. Flagged in shared context, sp5, and the manifest.

## Open Questions (carried from the plan — execution-time decisions, NOT blocking the split)

1. **Meaning-fidelity guard** (sp3b) — should a future phase add a dedicated paraphrase-fidelity check
   (a second, source-seeing LLM pass over modified/created units)? **Deferred under HOLD SCOPE.** sp3b
   ships the bounded guard (WHAT id-mapping totality + HOW never-invent + 4a cold-reader checker) and the
   spec v8 known-limitation note is the honest placeholder. Revisit only on evidence of real drift.
2. **Version-boundary vs publish-boundary re-anchor convergence** (sp3b / sp5) — 4b dispatches at version
   cuts (source space); this phase adds publish-boundary dispatch (render space). Two dispatch points,
   one agent — fine short-term. **Decide whether to merge after Sub-phase 5 evidence**, not now.
3. **Threshold default (0.4) + the changed-fraction formula** (sp3a) — starting values. The sp3a executor
   has latitude to adjust the **formula** if the corpus argues for it; the **knob name** and the
   **flip-to-CREATE semantics** are fixed. `RENDER_UPDATE_MAX_PRIOR_BYTES` default is likewise a tune knob.
4. **Prior-WHAT reuse edge** (sp3a) — how much WHAT-doc id-mapping patching is "trivial" before UPDATE
   falls back to CREATE? **Default conservative: any ambiguity → CREATE.** sp3a detail.

## Review Notes by Sub-Phase

### sp1a (UPDATE byte-fidelity spike)
- Verification is measurement-heavy by design (≥15 trials). The binding artifact is `verdict.md`'s
  greppable `VERDICT`/`MECHANISM` lines — sp3a/sp3b depend on reading them. No issues.

### sp1b (render-anchor dry-run)
- The `MIGRATION_SIZING` table is the consumed output; the ref-less-NULL-is-success classification is
  pre-wired to match sp2. No issues.

### sp2 (anchor move)
- The most subtle invariant: **anchoring moves before the carriage flip** (verbatim-carriage gate stays
  in force here). The ref-less-NULL trap and the `block_ref` trust boundary are both called out in
  Execution Notes + Success Criteria. No issues.

### sp3a (two-mode plumbing)
- The UPDATE-skips-`emit_change_requests` rule is load-bearing (not an optimization) and is both a
  detailed step and a success criterion. Production-stays-CREATE (inert path) is the headline invariant.
  No issues.

### sp3b (the flip)
- The NORMALIZED-vs-raw-byte distinction (Decision #3) and the override discipline (deterministic
  fallback only on literal no-output) are the two traps; both are in Execution Notes + Success Criteria.
  The splice-bends-the-one-page-contract note is flagged for the spec pass. No issues.

### sp4 (HOW hardening)
- Sequenced after 3b to avoid double-editing the HOW prompt. Deterministic-gate-over-checker-tweak keeps
  the cold-reader checker unmodified. No issues.

### sp5 (proof + spec v8)
- The v7→v8 correction and the mandatory gap-CR-idempotency regression (f) are the two easy-to-miss
  items; both are in Success Criteria + Execution Notes. The `/cast-update-spec` inline approval gate is
  the one human gate in the whole phase. No issues.

## Open Questions needing user input before execution

**None block the split.** The four plan-level Open Questions above are execution-time latitude items,
each homed to its sub-phase with a conservative default. The two split-time reconciliations are resolved.
