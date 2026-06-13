# Phase 1 Gate (G1) — Combined Spike Verdict → Phase 3 Entry

> **Decision owner:** human (sridherj) · **Date:** 2026-06-12 · **Gate:** G1 (combined) ·
> **Orchestrator run:** `run_20260612_100911_1ebb28` (cast-orchestrate)
> **Aggregates:** `spikes/1a/spike-results.md` + `spikes/1b/spike-results.md`

## Decision: **GO-TO-PHASE-3** (Gate Option A — both spikes green)

Both Phase-1 de-risking spikes cleared their bars. The maker direction and the
logical-backbone / quote-anchored-DOM approach are **validated**. Phase 3 (the WHAT→HOW maker
pipeline) is unblocked.

## Spike verdicts

| Spike | Verdict | Evidence summary |
|---|---|---|
| **1a — Maker Quality Ceiling** | `BEATS DETERMINISTIC: yes` | `bug_fix`: **strong/structural** — the deterministic recipe renders **0 of 7** canonical FR/SC ids (a reader can't see the fix or its acceptance checks); the maker surfaces all 7. `new_initiative`: **qualified** — id parity, win on hierarchy/scannability (maker keeps the whole WHAT open, 0 `<details>`, in <½ the bytes vs. 13 baseline disclosures). All four audits PASS both families (id set-equality 31/31 & 7/7, FR-003 per-block correspondence, self-containment, zero-`id`). |
| **1b — Quote-Anchored Backbone Survival** | `BACKBONE HOLDS: confirmed` | `cast-comment-reanchor` dispatched **live**; surviving comments relocated to **verbatim** new-source spans, FR-019 backstop clean (0× 422); **zero new orphans** for surviving content (only the genuinely-deleted block orphaned); v2 mark placement 5/5; `diff_blocks` deterministic with partition invariant intact (maker-layout move stayed `unchanged` by id key — backbone needs no new machinery); zero-`id`/FR-028 PASS on both renders. **No revisit-trigger raised.** |

## Why Option A (not B/C)

Neither spike fired a revisit-trigger. sp1a cleared "reachable by hand" for ≥2 families with no
gate regression; sp1b confirmed the quote-anchored backbone survives a varying render without an
id-in-DOM change. The maker-vs-hybrid fork and the id-in-DOM fork both stay closed. HOLD SCOPE
intact — no silent re-scope, no spec change in Phase 1.

## Carry-forwards into Phase 3 (recorded, not yet acted on)

1. **Human-eyeball browser pass (visual/taste gate).** No browser in the autonomous run; sp1a's
   visual-quality rubric rows are structural estimates. A human should open the four maker/baseline
   HTML files side-by-side to confirm at the ceiling level. **Non-blocking** per the
   no-browser-for-visual-gates rule.
2. **Verbatim-carriage maker clause** — the v3 maker contract needs an explicit "anchorable text
   carried verbatim and contiguous in the DOM" clause. Phase 3 `/cast-update-spec` item
   (`cast-requirements-render.collab.md`). No spec edit in Phase 1.
3. **`spike_id_audit.py` is Phase 3's acceptance pattern** — Phase 3 reuses the id set-equality +
   per-block-correspondence audit to gate the agent-generated render.
4. **Generic-anchor hazard** — short/generic quotes (`"the owner"`) false-place; the maker/composer
   should prefer unique, sufficiently-specific anchor spans, and the comment composer may warn on
   quotes with multiple document matches. Phase-3 input.
5. **`section_hint` is a tray/disambiguation hint, not a placement key** — placement is verbatim-quote
   driven, robust to maker section renames. Phase-3 input.
6. **Phase-4a checker anomaly** — the v2 SC-001 checker is necessary-but-not-sufficient (passes the
   baseline; no "beats" axis; blind to dropped depth). Fold source-vs-render id-coverage + a
   comprehension/visual-quality axis into the Phase-4a replacement. **Do not tune the v2 checker.**
7. **Stretch family un-run** — `data_analysis` was descoped (≥2-family bar met). Nine-family breadth
   is formally re-validated in Phase 5 (SC-002).

## Pre-Phase-3 prerequisite (flagged for the next session)

Per the reconciliation report (`docs/plan/2026-06-12-refine-requirements-v3-reconciliation.md`),
Phase 3 / 4a / 4b plan files carry **required pre-execution edits** before orchestration:
- §9.2 **OVERRIDE** — three required edits (Phase 3 §3c Decision #4, Phase 4a Fork Resolution,
  Phase 4b Decision #10): broken attempts are servable best-attempt-plus-flag; deterministic
  fallback fires only on literal no-output.
- Revisions **(a)** reaper ceiling from configured stage list + heartbeat in 3c's CREATE TABLE, and
  **(b)** expose the container-text walker as a shared helper in `maker_gate.py`.

These do **not** affect Phase 1 or Phase 2 (both clean to orchestrate as-is), but must be applied
before Phase 3 sub-phases are dispatched.

## Status

- G1: **Done** (Option A — GO-TO-PHASE-3).
- Orchestrator stopped here per the gate contract; the owner chose **Record GO, then stop**.
- Next session: orchestrate **Phase 2** (clean, independent, ships ahead) and/or begin **Phase 3**
  plan-prep (apply the reconciliation pre-execution edits above), then orchestrate Phase 3.
