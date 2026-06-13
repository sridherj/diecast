# Execution Manifest: refine-req-v3-phase3 (The WHAT→HOW Maker Pipeline Renders Bespoke HTML)

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:
1. Start a new Claude session.
2. Tell Claude: "Read `docs/execution/refine-req-v3-phase3/_shared_context.md` then execute
   `docs/execution/refine-req-v3-phase3/spN_name/plan.md`".
3. After completion, update the Status column below.

**3a and 3b are independent and parallel** (disjoint output files) — run in either order or
simultaneously. Then 3c → 3d → 3e are strictly sequential. There are **no decision gates** (the source
plan defines none); 3e contains a single inline `/cast-update-spec` approval gate handled within that
sub-phase.

## Sub-Phase Overview

| # | Sub-phase | Directory/File | Depends On | Status | Notes |
|---|-----------|----------------|-----------|--------|-------|
| 3a | WHAT + HOW agents exist & speak a checkable contract | `sp3a_what_how_agents/` | Phase 1 green | Done | Net-new agents; opus tier; revision (f) doc-only `GAPS-DETECTED`/`gaps[]` seam |
| 3b | Deterministic maker gate productionizes the spike audits | `sp3b_maker_gate/` | Phase 1 green; **Phase 2 `strip_inline_markdown` (HARD)** | Done | Pure `maker_gate.py`; revision (b) shared `container_text_index` helper; T1 fallback-passes-gate pin |
| 3c | Render service runs the maker as a background job | `sp3c_render_job_service/` | 3a, 3b | Done | **OVERRIDE** (flagged best-attempt) + **revision (a)** (reaper-from-stage-list, semaphore release, `heartbeat_at` in CREATE TABLE) |
| 3d | Route serves a live generating state, swaps in render | `sp3d_route_generating_state/` | 3c | Done | Override ripple: flagged page is `ready` + "needs review" badge; `failed` only = no servable artifact |
| 3e | Spec records the maker happy path; pipeline proves itself e2e | `sp3e_spec_e2e_gate/` | 3a, 3b, 3c, 3d | Done* | Single `/cast-update-spec` pass (incl. override + verbatim-carriage); two-family e2e gate |

Status: Not Started → In Progress → Done → Verified → Skipped

No `G`-prefixed gate rows: Phase 3 has no orchestrator decision gates. 3e's `/cast-update-spec` is an
inline human-approval gate (review the diff before approval); the human-eyeball browser pass is a
non-blocking carry-forward.

## Dependency Graph

```
  sp3a (WHAT/HOW agents) ──┐
                           ├──► sp3c (render job service) ──► sp3d (route + generating state) ──► sp3e (spec + e2e gate)
  sp3b (maker gate)     ───┘
        (3a ∥ 3b: disjoint files; 3b additionally has a HARD edge on Phase 2's strip_inline_markdown)
```

**Parallel-safety check:** sp3a writes only under `agents/cast-requirements-what|how/` (+ regenerated
skills); sp3b writes only `maker_gate.py` + `test_maker_gate.py`. **No shared files** — safe to run
simultaneously. 3c/3d both touch `requirements_render_service.py` but run **sequentially** (3d after
3c), so no parallel collision.

## Execution Order

### Parallel Group 1 (run simultaneously)
- **3a.** WHAT + HOW agents — `sp3a_what_how_agents/`
- **3b.** Deterministic maker gate — `sp3b_maker_gate/`

### Sequential (after both 3a and 3b)
- **3c.** Render job service — `sp3c_render_job_service/`

### Sequential (after 3c)
- **3d.** Route + generating state — `sp3d_route_generating_state/`

### Sequential (after 3d) — terminal
- **3e.** Spec + e2e gate — `sp3e_spec_e2e_gate/`
  - Inline `/cast-update-spec` approval gate (review the diff before approval).

**Critical path:** 3a/3b (parallel) → 3c → 3d → 3e. Total **5.5–7 sessions** (matches the high-level
estimate). 3c is the heaviest (~2 sessions; carries both major reconciliation edits).

## Applied Reconciliation Edits (owner-resolved — baked into the sub-phase plans, not open questions)

| Edit | Where applied | Summary |
|------|---------------|---------|
| **(1) Structural-violation OVERRIDE** | 3c §3c.4, 3d §3d.4, 3e delta #6 | Structural-retry exhaustion serves **best attempt + `structural_violation` flag**, NOT the deterministic page. Deterministic fallback fires ONLY on literal no-output. Surface via `flagged` status + `served-by` stamp + reader badge. |
| **Phase-3 flag mechanism (owner-confirmed for this split)** | 3c §3c.4 / §3c.7, 3d §3d.4 | Minimal signal: `flagged` status + reason in `error` + `served-by: structural_violation` artifact stamp + 3d badge. The four rich 4a flag columns layer on top later. |
| **(2) Revision (a)** | 3c §3c.7 / §3c.8 | Reaper ceiling = function of the **configured stage-timeout list** (4a/5 extend by registering stages); reaper **releases the semaphore slot** of a reaped orphan; `heartbeat_at` in the **initial** CREATE TABLE, written at every stage boundary; 4a-2 adds only the four flag columns. |
| **(3) Revision (b)** | 3b §3b.2 | Container-text walker exposed as the public, independently-unit-tested `container_text_index(html)` in `maker_gate.py`; 4b-1 imports it (hard no-copy). |
| **(4) Revision (f)** | 3a §3a.3 (+ shared context) | HOW contract documents an OPTIONAL `GAPS-DETECTED` trailer OUTSIDE the sentinels; WHAT keeps reserved `gaps: []`. **Documentation-only forward reference — Phase 3 code byte-untouched.** |
| **Model tier** | 3a §3a.4 | `opus` for both agents (placeholder + `[USER-DEFERRED]` comment; runner reads from config). |
| **2a → 3b hard edge** | 3b Dependencies / §3b.4 | 3b imports Phase 2's import-stable `strip_inline_markdown`; blocks/lifts if absent — never copies. |

## Progress Log

<Update after each sub-phase.>
- 2026-06-12: Execution plan created by `cast-create-execution-plan` (run_20260612_104757_c60a2f),
  applying the four owner-resolved reconciliation edits + the owner-confirmed Phase-3 flag mechanism
  (status + note + artifact stamp). Source plan doc NOT modified.
- 2026-06-12: 3a..3e all DONE -> PHASE 3 COMPLETE. Spec v3->v4 (override+verbatim-carriage). Live e2e: new_initiative clean, bug_fix flagged (override proven). Owner accepted gate; cast-requirements-how verbatim-carriage hardened (follow-up done). Override baked into source plan docs (phase3/4a/4b banners).
