# sp4 (2c.4 encode) — COMPLETE

**Run:** run_20260611_225945_ce40b0 · **Date:** 2026-06-12 · **Status:** completed (full autonomy)

Encoded the §5 derived `stageModels` vocabulary into `prototype/data/_build/generate-org.mjs`
(stageModels region only; retired the `[2c]` `step()` placeholder helper for inlined full per-step
objects) and re-emitted `prototype/data/org.js` via the generator — **invariant gate green**.

- **placeholder:false** on all four families; counts feature=5 · debug=5 (dbg-05 NEW; dbg-04 re-tasked
  to *Log Confirm/Refute*) · spike=4 · data=5 (data-05 NEW). E-homes E1→feat-05 · E2→dbg-04 · E3→dbg-05
  · E4→spk-04 · E5→data-05 (debug hosts both E2 & E3). Plain-JSON (function-free) load verified.
- **F4 section-stability:** byte-diff vs pre-edit org.js shows changes confined to the stageModels
  region only — meta (incl. frozen_at), org, humans, guide, agents, goals, board, decisions, hiring,
  layer2 all byte-identical; seeded seed(42) RNG unperturbed.
- **Gate note:** the gate's Rule 8 (`stagemodels-placeholder`) was advanced from its pre-2c assertion
  (`placeholder===true` "until Phase 2c") to its post-2c state (`placeholder===false`). This is the
  gate evolving with the phase as its own comment anticipated — NOT a weakening: it still hard-refuses
  to emit if any family is left on the watermark. This was the only edit outside the data region and
  is part of the 2c-owned stageModels contract surface.

Phase 3 dispatch is unblocked.
