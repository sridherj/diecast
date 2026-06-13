# Phase 4a → Phase 4b / 5 Hand-off

> Written by sub-phase **4a-3** (terminal). Extends `phase3-handoff.md` (3e). Phase 4a landed the
> **LLM quality gate** (`cast-requirements-render-checker`) + the **quality-driven rework loop**
> inside `render_job_service`, completing the two v4 forward pointers. Spec of record:
> `docs/specs/cast-requirements-render.collab.md` **v5** (US18, FR-037–FR-040, SC-014–SC-016).
> Read 3e's hand-off first — the five seams there (the checker stage insertion point, the
> `render_jobs` flag landing, the WHAT-doc id mapping, the `container_text_index` walker, the
> reserved `gaps[]`/`GAPS-DETECTED` seam) are unchanged; this note records what 4a *filled in* and
> what 4b/5 still plug into.

## 1. The flag now lives in three places — the policy table is the contract

After 4a the human-review flag is a single policy applied at one decision point
(`render_job_service.decide_quality`) and surfaced in three coordinated places:

| Surface | Mechanism | Read by |
|---|---|---|
| `render_jobs` columns | `human_review`, `review_reason`, `published_attempt`, `published_score` | Phase-5 sweep / post-mortem (the **queryable** copy) |
| Served-artifact envelope | `served-by: maker \| structural_violation` + `human-review: 1` stamp beside `source-hash` | the `/render/status` poll + the `/render` badge (the **read-path** truth) |
| Status JSON | `human_review` read **from the envelope**, never from a newer running row | the poller / 4b regenerate UI |

**Anything 4b's regenerate flow publishes follows the same policy table** (shared-context
`decide_quality` table, OWNER OVERRIDE baked in):

- deterministic page **only** on literal no-output (crash / timeout / nothing extractable);
- a structurally-broken-but-present attempt is **scoreable, servable, flagged** `structural_violation`
  — **never** the silent deterministic swap;
- non-convergence serves the best attempt **PREFER VALID, THEN SCORE** (`non_convergent` /
  `checker_unavailable` / `structural_degradation` / `structural_violation`).

A **survival-failing attempt is a structural violation under the OVERRIDE** (4b widens `gate_html`
with carriage + comment survival — an **in-block** miss merges into the existing
`html_report.violations` structural channel, so it is just another rework the loop wraps; a
**cross-boundary** miss surfaces read-time as 4b's `.comment-unplaced` tray badge, never flips
`passed`). The C3 merge note still holds: 4a inserts `run_checker → decide_quality` **after**
`gate_html`; 4b widens `gate_html`'s report; the seams are disjoint by design, and whichever of
4a/4b lands second does the mechanical (no-logic) merge.

## 2. The checker is the in-loop quality bar 4b's regenerate must clear

4b's "regenerate" (post-comment, post-version) goes through the **same** `_execute_pipeline` →
`_quality_loop` → `decide_quality`, so a regenerated render is held to the **same** comprehension +
visual bar and the **same** terminal policy. 4b adds no second gate — it widens the structural one
(`gate_html`) and re-uses the quality loop verbatim. The checker (`cast-requirements-render-checker`,
`model: opus`, tool-free, bare-JSON `cast-requirements-render-checker/v1`) and the **pure**
`checker_verdict.derive_pass` / `canonical_score` are the importable contract; the agent `score`
float is advisory only.

## 3. The gap contract is now protected at the eval layer (Phase 5 reads this)

The **gap-amnesty clause** (revision d) is pinned both in the checker prompt and in
`eval_quality_gate.py`: a `.rr-gap` marker is **honest source-gap communication, not a comprehension
failure of the render** — the checker must NOT fail a render for a surfaced gap. The committed
`fixtures/quality_gate/gap_amnesty_attempt.html` + its replay verdict assert this. **Phase 5 must keep
this contract** when it activates the reserved `gaps[]` WHAT-doc field + the `GAPS-DETECTED` HOW
trailer: the loop must never fight a render that honestly surfaces a gap. Register any new gap stages
in `config.RENDER_STAGE_TIMEOUTS` (the reaper ceiling extends automatically, as the checker stage
already does).

## 4. Phase 5d — the flagged-renders LIST (the only deferred consumption surface)

4a is **recording-only**. Phase 5d adds the **flagged-renders LIST** (slug, `review_reason`,
`published_score`, link — on an existing screen), reading the four `render_jobs` columns 4a populates.
Phase 5's nine-family sweep runs each family render through the **full** quality loop and reads
`human_review` as its per-family quality signal. Building the list / a review dashboard **before**
Phase 5d is silent scope drift (owner-resolved 2026-06-12).

## 5. The eval discipline 5 inherits

`eval_quality_gate.py` (mirrors `eval_render_checker.py`: `--live` / `--verdicts` replay /
`--out-verdicts`) **imports** the production gate (`derive_pass`/`canonical_score`) — a second copy is
drift by construction. **Below the bar the first lever is ALWAYS the checker prompt**
(`cast-requirements-render-checker.md`), never weakening the code-side gate. The blocking, no-LLM CI
path is `test_eval_quality_gate.py` (low-quality MUST-fail + gap-amnesty MUST-not-fail + structural
validity); a `--live` discrimination run + a browser eyeball over a flagged vs. converged publish are
the standing **human-eyeball carry-forward** (autonomous runs never block on visual gates).

## Quick reference — the v5 files 4b/5 return to

| File | Why 4b/5 returns to it |
|---|---|
| `cast_server/services/render_job_service.py` | `_quality_loop` + `decide_quality` (the policy table 4b's regenerate obeys); 4b widens `gate_html` upstream of it |
| `cast_server/requirements_render/checker_verdict.py` | the pure `derive_pass`/`canonical_score` contract — import, never copy |
| `agents/cast-requirements-render-checker/` | the in-loop quality gate (prompt is the first lever below the bar) |
| `cast_server/config.py` | `QUALITY_*` knobs + the stage-timeout list (Phase 5 registers gap stages here) |
| `cast_server/db/schema.sql` + `tests/test_schema_migration.py` | the four flag columns (Phase 5d reads them for the LIST) |
| `cast-server/tests/eval_quality_gate.py` + `fixtures/quality_gate/` | the calibration corpus + gap-amnesty contract Phase 5 must preserve |
| `docs/specs/cast-requirements-render.collab.md` **v5** | the recorded contract 4b/5 cite verbatim |
