# Execution Manifest: refine-req-v3-phase4a (The Quality Gate — Checker & Quality-Driven Rework Loop)

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:
1. Start a new Claude session.
2. Tell Claude: "Read `docs/execution/refine-req-v3-phase4a/_shared_context.md` then execute
   `docs/execution/refine-req-v3-phase4a/sp4aN_name/plan.md`".
3. After completion, update the Status column below.

**4a-1 and 4a-2 are independent and parallel** (disjoint output files) — run in either order or
simultaneously. 4a-2 builds against the plan-fixed verdict contract with **fake** verdicts; its
**merge gate** imports 4a-1's `checker_verdict.py`. Then 4a-3 (terminal) runs after both. There are
**no decision gates** (the source plan defines none); 4a-3 contains a single inline
`/cast-update-spec` approval gate handled within that sub-phase. **Execution waits for Phase 3e
green** (the e2e pipeline must be landed before the loop wraps it).

## Sub-Phase Overview

| # | Sub-phase | Directory | Depends On | Status | Notes |
|---|-----------|-----------|-----------|--------|-------|
| 4a-1 | Checker agent + code-side verdict gate | `sp4a1_checker_verdict/` | Phase 3 built | Done | Net-new agent; `opus`; pure `checker_verdict.py`; **gap-amnesty clause** in the prompt |
| 4a-2 | Quality loop + terminal policy in the service | `sp4a2_quality_loop/` | Phase 3 built | Done | **OWNER OVERRIDE** (broken=scoreable/servable+flag); **C4** (four flag columns only); reaper registers checker stage (no formula edit); **C3** merge note; recording-only |
| 4a-3 | Spec records the gate; fault-injection proves every branch | `sp4a3_spec_evals/` | 4a-1, 4a-2 | Done | Single `/cast-update-spec` (FR-006 text = **OVERRIDE**); `eval_quality_gate.py` (+ gap-amnesty fixtures); flagged-renders LIST deferred to Phase 5d |

Status: Not Started → In Progress → Done → Verified → Skipped

No `G`-prefixed gate rows: Phase 4a has no orchestrator decision gates. 4a-3's `/cast-update-spec`
is an inline human-approval gate (review the diff before approval); the human-eyeball browser pass
is a non-blocking carry-forward (no-browser-for-visual-gates rule).

## Dependency Graph

```
  sp4a1 (checker + verdict module) ──┐
                                     ├──► sp4a3 (spec + live evals + fault-injection gate)
  sp4a2 (quality loop in service) ───┘
        (4a-1 ∥ 4a-2: disjoint files; 4a-2's merge gate imports 4a-1's checker_verdict.py)
```

**Parallel-safety check:** sp4a1 writes only `agents/cast-requirements-render-checker/*`,
`checker_verdict.py`, `test_checker_verdict.py` (+ regenerated skills). sp4a2 writes
`render_job_service.py`, `config.py`, `schema.sql`, `pages.py` (status), `test_quality_loop.py`,
migration test, readonly-guard re-run. **No shared files** — safe to run simultaneously. sp4a3
writes only the fixture, the eval, the spec, the registry, and hand-off notes — after both.

**Cross-phase parallel (4a ∥ 4b):** both edit `render_job_service.py` at **disjoint seams** (4a
inserts stages after `gate_html`; 4b widens `gate_html`'s report). The second of 4a/4b to land does
the mechanical merge — no logic conflict (C3 merge note in sp4a2 §4a2.10).

## Execution Order

### Parallel Group 1 (run simultaneously, after Phase 3e green)
- **4a-1.** Checker agent + verdict module — `sp4a1_checker_verdict/`
- **4a-2.** Quality loop in the service — `sp4a2_quality_loop/` (build against fake verdicts; merge
  gate imports 4a-1's `checker_verdict.py`)

### Sequential (after both 4a-1 and 4a-2) — terminal
- **4a-3.** Spec + live evals + fault-injection gate — `sp4a3_spec_evals/`
  - Inline `/cast-update-spec` approval gate (review the diff — **FR-006 text must reflect the
    OVERRIDE**).

**Critical path:** 4a-1 ∥ 4a-2 → 4a-3. Total **~3.5 sessions** (inside the high-level 3–4 estimate).
4a-2 is the heaviest (~1.5 sessions; carries the override + the migration + the status surface).
Phase 4b proceeds in parallel throughout — no shared files beyond the disjoint
`render_job_service.py` seam.

## Applied Owner-Resolved Edits (baked into the sub-phase plans, NOT open questions)

| Edit | Where applied | Summary |
|------|---------------|---------|
| **(1) FORK RESOLUTION OVERRIDE** | shared ctx §OWNER OVERRIDE; sp4a2 §4a2.2 / §4a2.8; sp4a3 §4a3.4 / delta #3 | **Supersedes the source plan's "Fork Resolution: RATIFIED" section.** Deterministic page served ONLY on literal no-output; structurally-broken-but-present attempts are **scoreable + servable**, flagged `structural_violation` + `human_review`; the "zero-valid-attempts → deterministic fallback" policy row is **deleted**. |
| **Terminal ranking: prefer valid, then score** (owner-confirmed for this split, 2026-06-12) | shared ctx §OWNER OVERRIDE; sp4a2 §4a2.2 (+ prefer-valid test) | Serve the best-scoring structurally-VALID attempt (`non_convergent`); fall to best-scoring BROKEN attempt (`structural_violation`) only when no valid attempt exists. A broken attempt never outranks a valid one on score. |
| **(2) Gap-amnesty clause** (revision d) | sp4a1 §4a1.1 (checker prompt); sp4a3 §4a3.2 (eval fixtures) | `.rr-gap` markers are honest communication of a source gap, not a comprehension failure of the render — without it the loop fights the Phase-5 gap contract. |
| **(3) C4 — migration scope** | sp4a2 §4a2.7 (+ migration test) | 4a-2's `render_jobs` migration adds **ONLY** the four flag columns; `heartbeat_at` already ships in Phase 3's CREATE TABLE. |
| **(4) Reaper — no formula edit** (revision a) | sp4a2 §4a2.5 / Scope; shared ctx §Cross-Phase Hard Edges | The reaper ceiling already derives from the configured stage-timeout list; 4a only **registers** the checker stage timeout — zero formula edit. |
| **(5) C3 merge note** | sp4a2 §4a2.10; shared ctx §Cross-Phase Hard Edges | 4a/4b edit `render_job_service.py` at disjoint seams; the second lander does the mechanical merge. |
| **(6) Recording-only human-review** | sp4a2 (flag columns + envelope stamp + status JSON); sp4a3 §4a3.7 | 4a ships recording-only; the flagged-renders LIST is **Phase 5d** (owner-resolved 2026-06-12). |
| **Model tier** | sp4a1 §4a1.3 | `opus` for the checker (placeholder + `[USER-DEFERRED]` comment; owner-confirmed 2026-06-12 — zero plan edits). |
| **Deterministic fallback never LLM-gated** | sp4a2 §4a2.2 (+ SC-004 test asserts checker never invoked) | The crash escape hatch is snapshot-tested; the checker is never run over the fallback page. |

## Progress Log

<Update after each sub-phase.>
- 2026-06-12: Execution plan created by `cast-create-execution-plan`
  (run_20260612_124652_160107), applying the six owner-resolved edits + the owner-confirmed
  prefer-valid terminal ranking. **Source plan doc NOT modified.** The single largest deviation
  baked in is the FORK RESOLUTION OVERRIDE (supersedes the source plan's RATIFIED §Fork Resolution).

- 2026-06-12: PHASE 4a COMPLETE (4a-1,4a-2,4a-3). Checker + quality loop + override live; spec v4->v5; eval gate green.
