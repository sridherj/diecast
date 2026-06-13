# Execution Manifest: refine-req-v3-phase4b (Comments & Versions Survive the Maker)

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:
1. Start a new Claude session.
2. Tell Claude: "Read `docs/execution/refine-req-v3-phase4b/_shared_context.md` then execute
   `docs/execution/refine-req-v3-phase4b/spN_name/plan.md`".
3. After completion, update the Status column below.

**4b-1 runs parallel to the 4b-2 → 4b-3 chain.** Critical path: **4b-2 → 4b-3 → 4b-4** (4b-4
depends on all three). There are **no decision gates** (the source plan defines none — "Open
Questions: None blocking"); 4b-4 contains a single inline `/cast-update-spec` approval gate handled
within that sub-phase.

> **Read the DECISION #10 OVERRIDE section of `_shared_context.md` first.** It reshapes 4b-1 (and the
> 4b-4 spec wording + hand-off note) relative to the source-plan body: survival-failing attempts are
> **servable + flagged + badge-surfaced**, never blocked; the deterministic fallback fires only on
> literal no-output. The plan body predates the override; the shared context is authoritative.

## Sub-Phase Overview

| # | Sub-phase | Directory/File | Depends On | Status | Notes |
|---|-----------|----------------|-----------|--------|-------|
| 4b-1 | The survival gate — real comments place; misses surface, never block | `sp4b1_survival_gate/` | Phase 3 | Done | **OVERRIDE-reshaped:** in-block misses merge into the existing structural report → Phase-3 best-attempt+flag serve; `.comment-unplaced` badge covers in-block + cross-boundary; imports `container_text_index` (C2, no-copy) |
| 4b-2 | cast-comment-reanchor contract v2 | `sp4b2_reanchor_v2/` | Phase 3 WHAT-doc id-mapping | Done | Extend-in-place; `resolved` verdict via state machine (Decision #11); reanchor keeps `sonnet` tier (+ `[USER-DEFERRED]` comment); eval gate extended |
| 4b-3 | Narration lands same-door — stored, validated, rendered by attachment | `sp4b3_narration_store/` | **4b-2** | Done | `version_diff_narrations` (schema.sql + connection.py second-lander, additive over 4a-2's flag cols); all-or-nothing 422 listing offending keys; `/changes` sibling `narration` key (counts/items byte-identical); autoescaped `_diff_narration.html` partial (lookup-only); `.diff-narration` CSS appended after 4b-1's `.comment-unplaced`; `block_diff`/`diff_render` byte-untouched. Spec deltas flagged in `sp4b3_narration_store/spec_flags.md` for 4b-4 |
| 4b-4 | The spec records the survival contract; SC-003 proves it e2e | `sp4b4_spec_sc003_gate/` | 4b-1, 4b-2, 4b-3 | Done | Single `/cast-update-spec` (override-aware wording); SC-003 sweep; `render_job_service` C3 merge hand-off |

Status: Not Started → In Progress → Done → Verified → Skipped

No `G`-prefixed gate rows: Phase 4b has no orchestrator decision gates. 4b-4's `/cast-update-spec` is
an inline human-approval gate (review the diff before approval); the human-eyeball browser pass over
the tray badge + narration panel is a non-blocking carry-forward (no-browser-for-visual-gates rule).

## Dependency Graph

```
  sp4b1 (survival gate + tray badge) ──────────────────────────────┐
                                                                    ├──► sp4b4 (spec + SC-003 e2e gate)
  sp4b2 (reanchor contract v2) ──► sp4b3 (narration store/API/render) ──┘

  (4b-1 ∥ 4b-2/4b-3; 4b-1 and 4b-3 share _theme.css.j2 via additive-append)
```

**Parallel-safety check:**
- **4b-1** writes: `maker_gate.py` (adds `check_comment_survival`), `render_job_service.py` (widens
  `gate_html`), `requirements_comments.js` (badge), `_theme.css.j2` (`.comment-unplaced`),
  `test_comment_survival.py`.
- **4b-2** writes: `agents/cast-comment-reanchor/*`, `agents/cast-refine-requirements/*`,
  `tests/eval_reanchor.py`.
- **4b-3** writes: `schema.sql`, `requirement_version_service.py`, `api_requirements.py`,
  `changes_panel.html`, `render_diff` view template, `_theme.css.j2` (`.diff-narration`),
  `test_diff_narration.py`, `test_schema_migration.py`.
- **Only shared file across parallel sub-phases: `_theme.css.j2`** (4b-1 ∥ 4b-3). Resolution:
  **disjoint, additive, non-overlapping CSS blocks** (`.comment-unplaced` vs `.diff-narration`);
  whichever lands second appends after the first — same precedent as the `render_job_service` 4a/4b
  seam discipline. No logical collision.
- **Cross-phase (NOT within 4b): `render_job_service.py`** is also edited by Phase 4a-2 (inserts
  stages after `gate_html`). Disjoint seams; C3 merge note — second-lander does the mechanical merge
  (see 4b-4 hand-off).

## Execution Order

### Parallel Group 1 (run simultaneously)
- **4b-1.** Survival gate + tray badge — `sp4b1_survival_gate/`
- **4b-2.** Reanchor contract v2 — `sp4b2_reanchor_v2/`

### Sequential (after 4b-2)
- **4b-3.** Narration store / API / render — `sp4b3_narration_store/`
  - (May run concurrently with the tail of 4b-1; coordinate `_theme.css.j2` via additive-append.)

### Sequential (after 4b-1, 4b-2, 4b-3) — terminal
- **4b-4.** Spec + SC-003 e2e gate — `sp4b4_spec_sc003_gate/`
  - Inline `/cast-update-spec` approval gate (review the diff before approval).

**Critical path:** 4b-2 → 4b-3 → 4b-4 (4b-1 runs parallel). Total **3.5–4.5 sessions** (matches the
high-level 3–4 estimate). 4b-1 is the heaviest single sub-phase (survival gate + service seam + JS +
its test matrix).

## Applied Owner-Resolved Edits (baked into the sub-phase plans, not open questions)

| Edit | Where applied | Summary |
|------|---------------|---------|
| **DECISION #10 OVERRIDE** | `_shared_context.md` (dedicated section); 4b-1 §4b1.2 + Verification + Execution Notes; 4b-4 delta #1 + hand-off | Survival-failing attempts NO LONGER disqualified from serving. In-block misses merge into the **existing** structural report → Phase-3 `publish()` serves best-attempt + `structural_violation` flag (never deterministic fallback except literal no-output). `.comment-unplaced` badge extends to in-block misses. The 4a seam contract flips: survival-failing = flagged/servable, not a disqualifier. |
| **C2 / revision (b)** | 4b-1 Dependencies + §4b1.1 + Manual Checks | Import the shared `container_text_index(html)` helper from `maker_gate.py` (confirmed live at `maker_gate.py:238`). Hard no-copy; never re-implement the walk or add a second stripper. |
| **C3 merge note** | 4b-1 §4b1.2 (C3 box); 4b-4 §4b4.3 hand-off; `_shared_context.md` Cross-Phase Hard Edges | 4a-2 ∥ 4b-1 both edit `render_job_service.py` at disjoint seams (4b widens `gate_html` report; 4a inserts stages after). Whichever lands second does the mechanical merge, preserving the override. |
| **Extend-in-place (contract v2)** | 4b-2 (whole) | `cast-comment-reanchor` extended, never replaced; verdict safety machinery (orphan-over-guess, 422 backstop, no-op-on-garbage) carried untouched; all new inputs optional so existing call sites stay byte-valid; one dispatch serves narrate + resolve. |
| **`resolved` state-machine guard** | 4b-2 §4b2.3 | `resolved` application respects the v2 `comment_service` state machine — no-op/reject if the comment is not `open` at apply time (Decision #11 / CQ2). |
| **Model tier (reanchor keeps its tier)** | 4b-2 §4b2.2 | `cast-comment-reanchor/config.yaml` stays `model: sonnet` + a `[USER-DEFERRED] tier knob` comment. The reanchor agent is NOT one of the four opus pipeline agents. |
| **block_diff/diff_render NOT modified** | 4b-1 + 4b-3 Scope (out-of-scope) | Logical backbone = the existing `Block.ref` space `_key()` keys on (FR-024 extend-never-fork). Narration is a consumer beside the engine. |
| **Inline spec update (no separate gate)** | 4b-4 §4b4.1 | The `/cast-update-spec` is inline within 4b-4, not a standalone orchestrator gate. |

## Progress Log

<Update after each sub-phase.>
- 2026-06-12: Execution plan created by `cast-create-execution-plan` (run_20260612_124652_f38220),
  applying the DECISION #10 OVERRIDE (survival surfaced-not-blocking), the C2 shared-walker import,
  the C3 `render_job_service` merge note, extend-in-place contract v2 + `resolved` state-machine
  guard, reanchor-keeps-its-tier, and the inline 4b-4 spec pass. Source plan doc NOT modified.
- 2026-06-12: **4b-3 Done** (run_20260612_140353_ad72a7). Shipped `version_diff_narrations`
  (schema.sql + connection.py as the second lander — merged additively, preserving 4a-2's four
  `render_jobs` flag columns + their migration tests; added narration migration-test coverage),
  `save_narration`/`get_narration` (server-side `summarize()` recompute, all-or-nothing 422 with
  offending keys, FR-017 size caps, upsert-on-repost), the same-door narration POST,
  the `/changes` `narration` sibling (counts/items byte-identical), the autoescaped lookup-only
  `_diff_narration.html` partial wired into `changes_panel.html` + the tracked-changes view via the
  route only (`diff_render.py` byte-untouched), and the `.diff-narration` CSS appended after 4b-1's
  `.comment-unplaced`. `tests/test_diff_narration.py` (20) green; default-CI sweep 961 passed / 0
  failed; renderer + diff goldens regenerated for the additive theme-CSS change (no structural
  drift). The 2 pre-existing delegation reds (`tests/integration/test_child_delegation.py`,
  `tests/e2e/test_tier_delegation.py`) live outside default CI and were not touched. Spec deltas
  flagged in `sp4b3_narration_store/spec_flags.md` for 4b-4 (FR-024 re-scope, FR-023 route,
  `linked_files`). Source plan doc NOT modified.

- 2026-06-12: PHASE 4b COMPLETE (4b-1..4b-4). Survival gate + reanchor v2 + narration; spec v5->v6; SC-003 e2e green (live --live: both comments placed, zero orphans). C3 merge coherent.
