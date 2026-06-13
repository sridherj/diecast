# Execution Manifest: refine-req-v3-how-update-mode (HOW Two-Mode + Render-Snapshot Anchoring)

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:
1. Start a new Claude session.
2. Tell Claude: "Read `docs/execution/refine-req-v3-how-update-mode/_shared_context.md` then execute
   `docs/execution/refine-req-v3-how-update-mode/spN_name/plan.md`".
3. After completion, update the Status column below.

**Build order:** `1 (1a ∥ 1b) → (2 ∥ 3a) → 3b → 4 → 5`. **Critical path:** 1 → 2 → 3b → 4 → 5
(3a is off the critical path, parallel with 2, but must land before 3b). **Execution-start gate:**
Phase 5d sign-off (the 5c sweep record is provisional until then) — this is an external precondition,
not an orchestrator gate row.

> **No `G`-prefixed decision gates.** Sub-phase 1a's PASS/FAIL verdict selects 3b's UPDATE mechanism and
> is binding, but the owner decided to materialize it as a **recorded verdict** in
> `docs/goal/refine-requirements-better-rendering-v3/spikes/update-fidelity/verdict.md`, NOT an
> orchestrator stop. sp3a and sp3b list "the 1a verdict" as a hard dependency and **must read** that file
> before building the UPDATE prompt section. Sub-phase 5's `/cast-update-spec` is an inline human-approval
> gate handled within that sub-phase.

> **⚠️ Spec version (read before Sub-phase 5):** the plan body says the spec pass is "v6 → v7". That
> numbering is **stale** (drafted before Phase 5 gap-fill bumped the spec). The spec on disk is already
> **v7**; this phase's pass is **v7 → v8**. The shared context + sp5 use **v8** throughout.

## Sub-Phase Overview

| # | Sub-phase | Directory/File | Depends On | Status | Notes |
|---|-----------|----------------|-----------|--------|-------|
| 1a | UPDATE byte-fidelity spike | `sp1a_update_fidelity_spike/` | — | Done | Read-only; 3 docs incl. a `bug_fix`-class, **≥5 trials/doc** (Decision #4); records the binding PASS/FAIL → mechanism verdict; whitespace-vs-reworded split feeds 3b's normalization layer |
| 1b | Render-anchor dry-run | `sp1b_render_anchor_dryrun/` | — | Done | Read-only; placement + `block_ref`-bridge rate of existing comments vs published render; **sizes** the sp2 migration; no browser (Python dry-run) |
| 2 | Anchor move — comments anchor to the render snapshot | `sp2_anchor_move/` | 1b | Done | `block_ref`/`anchor_space` columns; server-resolved bridge (trust boundary — never client); **ref-less NULL = success** (Decision #1); idempotent migration; reanchor **v3**; verbatim-carriage gate STILL in force |
| 3a | Two-mode plumbing — mode detection & prior-render recovery | `sp3a_two_mode_plumbing/` | 1a | Done | Parallel with 2; pure `decide_mode`; `RENDER_UPDATE_MAX_CHANGED_FRACTION` (0.4) + `RENDER_UPDATE_MAX_PRIOR_BYTES` (Decision #6); UPDATE **skips `emit_change_requests`** (Decision #2); UPDATE path built **INERT** (flag-gated) — production stays CREATE |
| 3b | The flip — readability-first HOW + re-scoped gates | `sp3b_the_flip/` | 2, 3a | Done | Drops blanket verbatim-carriage; `check_update_fidelity` compares **NORMALIZED text** (LLM-copy) / verifies **splice** (Decision #3); survival → render-space; ONE publish-boundary reanchor v3 dispatch; deterministic fallback ONLY on literal no-output |
| 4 | HOW hardening — invented ids & empty shells | `sp4_how_hardening/` | 3b | Done | Zero-ref contract (0 anchor labels, 0 invented ids); deterministic empty-shell `check_html` violation; cold-reader checker UNMODIFIED; runs AFTER 3b so the HOW prompt isn't edited twice |
| 5 | Proof — 3 families clean, survival regression, spec **v8** | `sp5_proof_spec/` | 2, 3b, 4 | Done | 9/9 published 0 flagged; `eval_sc003_survival` (a)–(f) incl. **gap-CR idempotency under UPDATE** (Decisions #2/#5); ONE `/cast-update-spec` **v7→v8**; decisions-so-far + signoff updated |

Status: Not Started → In Progress → Done → Verified → Skipped

## Dependency Graph

```
  sp1a (UPDATE byte-fidelity spike) ──verdict──┬──────────────────► sp3a (two-mode plumbing) ──┐
                                               │                                                ├──► sp3b ──► sp4 ──► sp5
  sp1b (render-anchor dry-run) ──sizes──► sp2 (anchor move) ───────────────────────────────────┘   (the flip) (harden) (proof+spec v8)

  Build order: 1 (1a ∥ 1b) → (2 ∥ 3a) → 3b → 4 → 5
  3b depends on BOTH sp2 AND sp3a AND the sp1a verdict.
```

**Parallel-safety check (the two parallel pairs):**
- **1a ∥ 1b:** disjoint spike dirs (`spikes/update-fidelity/` vs `spikes/render-anchor/`), both read-only
  against production — zero file overlap.
- **2 ∥ 3a:** disjoint code surfaces —
  - **sp2** writes: `comment_service.py`, `comment_anchor.py`, `api_requirements.py`, `db/schema.sql`
    (comment columns), `agents/cast-comment-reanchor/*`, `test_schema_migration.py`, comment-anchor tests.
  - **sp3a** writes: `render_job_service.py`, `config.py`, `db/schema.sql` (`render_jobs.mode`),
    `agents/cast-requirements-how/*` (UPDATE section, inert), `test_render_mode_decision.py`,
    `test_schema_migration.py`.
  - **Shared files:** `db/schema.sql` (sp2 adds comment columns; sp3a adds `render_jobs.mode` — disjoint
    tables, additive) and `test_schema_migration.py` (disjoint assertion blocks). Resolution: **additive,
    non-overlapping** — whichever lands second appends its column + its assertion. No logical collision.
    `agents/cast-requirements-how/*` is touched by sp3a (UPDATE section) but **not** sp2 — no parallel
    HOW-prompt collision (sp3b → sp4 also touch it, but sequentially).
- **Sequential HOW-prompt edits:** `agents/cast-requirements-how/cast-requirements-how.md` is edited by
  sp3a (UPDATE section, inert) → sp3b (the flip) → sp4 (hardening), all on the critical path, **never in
  parallel**. sp4 depends on sp3b precisely so the prompt is not edited twice in flight.
- **Sequential `render_job_service.py`:** sp3a (mode decision + recovery + inert UPDATE) → sp3b (wire
  live + publish-boundary dispatch) — sequential (3b depends on 3a), no collision. sp2 does NOT touch it.

## Execution Order

### Parallel Group 1 (run simultaneously) — read-only spikes
- **1a.** UPDATE byte-fidelity spike — `sp1a_update_fidelity_spike/`
- **1b.** Render-anchor dry-run — `sp1b_render_anchor_dryrun/`

### Parallel Group 2 (after Group 1) — run simultaneously
- **2.** Anchor move — `sp2_anchor_move/` (needs 1b's sizing)
- **3a.** Two-mode plumbing — `sp3a_two_mode_plumbing/` (needs the 1a verdict)

### Sequential (after BOTH 2 and 3a, and the 1a verdict)
- **3b.** The flip — `sp3b_the_flip/`

### Sequential (after 3b)
- **4.** HOW hardening — `sp4_how_hardening/`

### Sequential (after 2, 3b, 4) — terminal
- **5.** Proof + spec v8 — `sp5_proof_spec/`
  - Inline `/cast-update-spec` approval gate (review the diff before approval).

**Critical path:** 1 → 2 → 3b → 4 → 5. 3a runs parallel with 2 but gates 3b. Total estimate from the
plan: ~13–18 sessions (1a∥1b ≈ 2; 2 ≈ 3–4; 3a ≈ 2–3; 3b ≈ 3–4; 4 ≈ 1–2; 5 ≈ 2–3).

## Applied Owner / Plan-Review Refinements (baked into the sub-phase plans, not open questions)

| Refinement | Where applied | Summary |
|------------|---------------|---------|
| **Decision #1 — ref-less NULL is success** | sp2 §2.2/§2.3/§2.4 + shared context | A `pilot_poc`/`random_idea` page has zero anchor labels → `block_ref=NULL` by construction; treated as success in creation, displacement, AND migration — never an unplaced miss to retry/badge. |
| **Decision #2 — UPDATE skips `emit_change_requests`** | sp3a §3a.6 + sp5 regression (f) | The gap-CR dedupe fingerprint is keyed by the current `source_hash[:12]`; an UPDATE's new hash would write a DUPLICATE gap CR. UPDATE reuses `gaps-state.json` + re-emits nothing; pinned by sp5 regression (f). |
| **Decision #3 — normalized-text fidelity compare** | sp3b §3b.2 + shared context | `check_update_fidelity` compares NORMALIZED container text via the shared walker in gate-enforced-LLM-copy mode (raw-byte only in splice mode). Avoids thrashing on serialization noise. |
| **Decision #4 — bug_fix doc + ≥5 trials in 1a** | sp1a (whole) | The spike that selects 3b's mechanism must exercise the failing family; ≥5 trials/doc to resolve a 95% bar. |
| **Decision #5 — gap-CR idempotency regression** | sp5 §5.2 (f) | A behavioral guarantee needs a test pinning it: an UPDATE re-render of a doc with an open gap emits ZERO new gap CRs. |
| **Decision #6 — `RENDER_UPDATE_MAX_PRIOR_BYTES`** | sp3a §3a.1/§3a.4 | Bounds total bytes inlined (changed-fraction bounds only changed work); a huge prior page flips to CREATE to avoid silent context truncation dropping tail unchanged containers. |
| **1a verdict = recorded dependency, not a gate** | shared context + manifest + sp1a/sp3a/sp3b | Owner decision (2026-06-12): no `gate_`/`G` row; sp3a/sp3b read `spikes/update-fidelity/verdict.md`. |
| **Spec v7 → v8 (not v6 → v7)** | shared context + sp5 + manifest | The plan-body numbering predates Phase 5's spec bump; the on-disk spec is v7, so this pass is v7→v8. |

## Progress Log

<Update after each sub-phase.>
- 2026-06-12: Execution plan created by `cast-create-execution-plan` (run_20260612_170235_2e6ddc) from
  `docs/plan/2026-06-12-refine-requirements-v3-how-update-mode-render-anchoring.md`. Preserved the
  build-order DAG `1 → (2 ∥ 3a) → 3b → 4 → 5` (3b on both 2 and 3a). Carried the six plan-review
  Decisions-appendix refinements into their sub-phases. Owner-decided (interactive): the 1a verdict is a
  recorded dependency (no orchestrator gate); the spec pass is corrected to v7 → v8. Source plan doc NOT
  modified.
