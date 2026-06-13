# Execution Manifest: refine-req-v3-phase5 (Gap-Fill, Cross-Family Hardening & Sign-Off — FINAL)

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:
1. Start a new Claude session.
2. Tell Claude: "Read `docs/execution/refine-req-v3-phase5/_shared_context.md` then execute
   `docs/execution/refine-req-v3-phase5/spN_name/plan.md`".
3. After completion, update the Status column below.

**5c runs fully parallel to the 5a → 5b chain.** Critical path: **5a → 5b → 5d** (5d depends on all
three). There are **no orchestrator decision gates** (the source plan defines none); 5d contains two
inline `/cast-update-spec` approval gates handled within that sub-phase **under standing session
approval**.

> **Read the "Applied Owner-Resolved Edits" + the two OVERRIDE sections of `_shared_context.md`
> first.** Phase 5's source-plan body predates several owner resolutions: the **GATE-ALL** policy flip
> (5b), the **flagged-renders list** (5d), the **SC-001…SC-018** sweep range (5d, not SC-001…SC-008),
> and the **structural-violation override**. The shared context is authoritative where the plan body
> and a baked-in owner edit disagree.

## Sub-Phase Overview

| # | Sub-phase | Directory/File | Depends On | Status | Notes |
|---|-----------|----------------|-----------|--------|-------|
| 5a | The gap contract & the upstream ask loop | `sp5a_gap_contract/` | Phases 3 + 4a | Done | NET-NEW `cast-requirements-gapfill` (opus, tool-free carve-out); `gaps[]` schema + HOW `GAPS-DETECTED` trailer; new pipeline stages `ask_what`/`run_gapfill`/`validate_evidence`/`emit_change_requests`(stub); server-side evidence validation via shared `verbatim_locate`; `maker_gate` gaps-schema + marker-correspondence; `gaps-state.json` single status enum; **C5** `GAPFILL_MAX_GAPS=5` + `GAPFILL_ASK_ROUNDS=1` in config; **C6** probe `run_how` ⟂ `QUALITY_MAX_ATTEMPTS`. Ends with validated `gaps-state.json`, NO CR emitted. |
| 5b | Reconciliation through the gate & honest page markers | `sp5b_gate_reconciliation/` | 5a | Done | `emit_change_requests` via `change_request_service.create` (consumed byte-unchanged); **GATE-ALL flip** (config default → `"gate-all"`); structural fingerprint dedupe (`_normalize_gap_question`); `.rr-gap` marker (question + fixed status, NEVER `proposed_body`); checker gap-amnesty line; both convergence lanes incl. the gated-lane (T1) + SC-007 gap-injection. |
| 5c | Nine-family corpus & golden renders | `sp5c_nine_family_corpus/` | Phases 3 + 4a | Done* | Authored-not-fiction fixtures in `tests/fixtures/family_corpus/`; `eval_family_sweep.py`; per-family quality read from `human_review`; fix loop at prompt/recipe-wording level only (enum LOCKED). **Parallel with 5a/5b.** SC-002 evidence provisional here, finalized in 5d. |
| 5d | Full SC-001…SC-018 sweep, final spec reconciliation & sign-off | `sp5d_sc_sweep_signoff/` | 5a, 5b, 5c | Done | The **full eighteen**-criterion sweep (not SC-001…SC-008); integration drift sweep (reaper/heartbeat extended for gap stages, single-helper checks, C5 knobs landed); two inline `/cast-update-spec` passes (render v6 + conditional roundtrip) **under standing approval**; the **minimal flagged-renders list** on an existing screen; the sign-off with every flag + carry-forward stated. |

Status: Not Started → In Progress → Done → Verified → Skipped

No `G`-prefixed gate rows: Phase 5 has no orchestrator decision gates. 5d's two `/cast-update-spec`
calls are inline human-approval gates (review the diff before approval) handled within 5d under the
goal's standing additive-spec approval; the human-eyeball browser passes are non-blocking
carry-forwards (no-browser-for-visual-gates rule).

## Dependency Graph

```
  sp5a (gap contract + ask loop) ──► sp5b (gate reconciliation + .rr-gap markers) ──┐
                                                                                     ├──► sp5d (SC-001…SC-018 sweep + spec + flagged list + sign-off)
  sp5c (nine-family corpus + golden renders) ──────────────────────────────────────┘
     (parallel with 5a/5b — gap machinery dormant, gaps[] empty)
```

**Parallel-safety check (5c ∥ 5a/5b):**
- **5a** writes: `agents/cast-requirements-gapfill/*`, `agents/cast-requirements-what/*`,
  `agents/cast-requirements-how/*`, `maker_gate.py`, `render_job_service.py`, `config.py`
  (`GAPFILL_*`), `tests/test_maker_gate.py`, `tests/test_render_job_service.py`.
- **5b** writes: `render_job_service.py` (`emit_change_requests` body), `config.py`
  (`WRITEBACK_GATE_POLICY` flip), `agents/cast-requirements-how/*` (`.rr-gap` rendering),
  `agents/cast-requirements-render-checker/*` (amnesty line), `_theme.css.j2` (`.rr-gap`),
  `tests/test_gap_reconciliation.py`, `tests/test_fr007_readonly_guard.py`.
- **5c** writes: `cast-server/tests/fixtures/family_corpus/*`, `tests/eval_family_sweep.py`,
  `agents/cast-requirements-what/*` (per-family prompt vocab), `cast_server/.../families.py`
  (`FAMILY_RECIPES` wording), `docs/goal/.../signoff/golden/*`.
- **Shared file across the parallel boundary: `agents/cast-requirements-what/*`** (5a adds the
  `gaps[]` schema + gap-detection rule; 5c tunes per-family *section vocabulary*). **Disjoint
  concerns, but the same prompt file.** Resolution: **5a and 5b are sequential (5a → 5b), and 5c is
  the long pole running parallel to BOTH.** Coordinate the `cast-requirements-what` prompt as
  **additive, non-overlapping sections** — 5a owns the gaps-schema + gap-detection block; 5c owns the
  per-family communication-section vocabulary block. Whichever lands second appends its block; no
  logical collision (same additive-append discipline as the 4b `_theme.css.j2` seam). **If 5a and 5c
  run truly concurrently, the second lander does a mechanical merge of the two disjoint prompt
  blocks.** Flagged in both 5a and 5c plans.
- **`render_job_service.py` is edited by BOTH 5a and 5b** — but they are **sequential** (5b depends on
  5a), so 5b extends 5a's `emit_change_requests` stub in place. No parallel conflict.

## Execution Order

### Parallel Group 1 (run simultaneously)
- **5a.** Gap contract + ask loop — `sp5a_gap_contract/`
- **5c.** Nine-family corpus + golden renders — `sp5c_nine_family_corpus/`
  - (Coordinate the `cast-requirements-what` prompt via additive, disjoint blocks; second lander merges.)

### Sequential (after 5a)
- **5b.** Gate reconciliation + `.rr-gap` markers — `sp5b_gate_reconciliation/`
  - Applies the **GATE-ALL** config flip; fills 5a's `emit_change_requests` stub.

### Sequential (after 5a, 5b, 5c) — terminal
- **5d.** SC-001…SC-018 sweep + spec + flagged-renders list + sign-off — `sp5d_sc_sweep_signoff/`
  - Two inline `/cast-update-spec` approval gates (review the diff before approval), under standing approval.

**Critical path:** 5a → 5b → 5d (≈ 4–4.5 sessions). 5c (≈ 1.5 sessions) runs fully in parallel, so
wall-clock stays within the high-level 3–5 session estimate; total effort is 5.5–6 sessions serially.

## Applied Owner-Resolved Edits (baked into the sub-phase plans, not open questions)

| Edit | Where applied | Summary |
|------|---------------|---------|
| **GATE-ALL gap-CR policy** | 5b §emit + config flip; `_shared_context.md` Applied Edits #1 | Every gap CR (`kind="addition"`) intakes `proposed` and awaits explicit human approval — additions NOT fast-tracked for this goal. **Mechanism:** flip `config.py` `WRITEBACK_GATE_POLICY` default → `"gate-all"` (env override preserved). Gate function/lanes/conflict/writeback/outbox **byte-unchanged** — only the policy value. Global by design. **Supersedes** the source plan's "keep `gate-except-additions`" taste call + Decision #1's fast-track framing. |
| **Flagged-renders LIST** | 5d §flagged-list; `_shared_context.md` Applied Edits #2 | Minimal list (slug, reason, score, link) on an existing screen (`/runs` or goals); additive, read-only. 4a shipped recording-only (SC-016); 5d adds the list. Needed under the structural override (flags are the only honest degraded-page signal). |
| **C5 — `GAPFILL_MAX_GAPS` knob** | 5a §config; 5d drift sweep | `GAPFILL_MAX_GAPS` (default 5) lands in `config.py` during 5a alongside `GAPFILL_ASK_ROUNDS` (default 1); 5d's drift sweep verifies both landed and are read. |
| **C6 — probe `run_how` ⟂ `QUALITY_MAX_ATTEMPTS`** | 5a §pipeline stages; 5d drift sweep | The pre-loop trailer-harvest `run_how` does NOT debit the quality-attempt ceiling (mirrors `GAPFILL_ASK_ROUNDS`'s independence). |
| **SC sweep range = SC-001…SC-018** | 5d §SC sweep | The full sweep is the **eighteen** criteria the spec carries at v6, not the source-plan body's SC-001…SC-008. 5d runs the gap/family-specific ones fresh and cites existing phase-3/4a/4b evidence for SC-009…SC-018. |
| **Model tier opus (gapfill)** | 5a §agent config | `cast-requirements-gapfill/config.yaml` is `model: opus` + a `[USER-DEFERRED] tier knob` comment (one of the four opus pipeline agents). |
| **Structural-violation OVERRIDE** | `_shared_context.md` dedicated section; 5c terminal-state assertions; 5d SC-004/008/013/015 | Best-attempt+flag even for structurally broken attempts; deterministic page only on literal no-output. Gap markers + flagged renders are the same honest-degraded-state family. |
| **Gap stages run once-per-job before the loop** | 5a §pipeline stages | The gap set is a property of the source, not the rendering attempt; honors FR-015's "before finalizing". |

## Progress Log

<Update after each sub-phase.>
- 2026-06-12: Execution plan created by `cast-create-execution-plan` (run_20260612_144431_fecea9),
  mirroring the source plan's 5a/5b/5c/5d split (owner-confirmed) and baking in the GATE-ALL config
  flip (owner-confirmed mechanism: config default → `"gate-all"`), the 5d flagged-renders list, the
  C5 `GAPFILL_MAX_GAPS` knob, the C6 probe-`run_how` independence, the SC-001…SC-018 sweep range, the
  opus gapfill tier, and the structural-violation override. Source plan doc NOT modified.
- 2026-06-12: **5a DONE** (run_20260612_152639_784dda). Activated the dormant `gaps[]` seam end-to-
  end on the agent side: net-new `cast-requirements-gapfill` (opus, tool-free subagent carve-out,
  grounded-or-refuse, corpus = the goal's OWN upstream allowlist only); WHAT `gaps[]` schema + "would
  materially help the reader" detection bar; HOW `GAPS-DETECTED` trailer OUTSIDE the sentinels; new
  `render_job_service` stages `run_how`(probe)/`ask_what`/`run_gapfill`/`validate_evidence`/
  `emit_change_requests`(STUB — gaps-state.json only, **no CR**) running ONCE per job before the 4a
  loop; server-side `validate_evidence` REUSING the shared `verbatim_locate` (no second locate;
  whitespace/smart-quote tolerance folded onto inputs); `maker_gate` gaps-schema + gap-marker
  correspondence (incl. T3) + GAP-NN/out-of-enum rejection + `check_gaps_state`; `gaps-state.json`
  single closed status enum; C5 knobs (`GAPFILL_MAX_GAPS=5`, `GAPFILL_ASK_ROUNDS=1`) + gap stages
  registered in `RENDER_STAGE_TIMEOUTS` so the reaper ceiling extends. Counter independence (C6 probe
  ⟂ `QUALITY_MAX_ATTEMPTS`; A2 `ask_what` ⟂ `QUALITY_MAX_WHAT_REWORKS`) proven by unit test.
  `cast-requirements-what` prompt: 5a appended its gaps block AFTER 5c's per-family vocabulary block
  (second-lander mechanical merge — both blocks present and intentional). Tests: +18 maker_gate, +13
  render_job_service, 6 quality-loop assertions updated for the new probe call. Full suite 1049
  passed; only the 2 pre-existing delegation reds remain (NOT 5a's). The 2 pre-existing delegation
  reds were left untouched.

- 2026-06-12: PHASE 5 COMPLETE (5a,5b,5c,5d). Gap machinery live; GATE-ALL; nine-family sweep 6/9 clean + 3 flagged (HOW-layer, served per override); flagged-renders list on /runs; specs render v7 + roundtrip v2; SIGNOFF.md written; suite 1067 passed. WHOLE GOAL DELIVERED.
