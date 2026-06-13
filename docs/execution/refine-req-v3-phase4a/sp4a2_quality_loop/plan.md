# Sub-phase 4a-2: The Loop Reworks on Quality and Lands the Right Terminal State

> **Pre-requisite:** Read `docs/execution/refine-req-v3-phase4a/_shared_context.md` before starting.
> The **OWNER OVERRIDE** section there is load-bearing for this sub-phase — read it twice.

## Objective

Extend Phase 3's `render_job_service` to run the full gated pipeline —
`run_what → gate_what → run_how → gate_html → run_checker → decide_quality → publish` — where
`decide_quality` implements the exhaustive terminal-state policy table (with the **structural
OVERRIDE** baked in): pass → publish clean; fail → rework with provenance-tagged feedback; terminal
→ best-scoring attempt published + `human_review` flag (preferring structurally-valid attempts);
**literal no-output only → deterministic fallback**. Every attempt's verdict is a recorded artifact;
the `render_jobs` row carries the four flag columns; the status endpoint exposes `human_review` read
from the **served-artifact envelope**. All of it proven by deterministic fake-runner tests.

## Dependencies

- **Requires completed:** Phase 3 built (the named stage seam, `AgentRunner`, `maker_gate.py`, the
  `render_jobs` table **incl. `heartbeat_at`**, the per-job thread + reaper + in-flight semaphore,
  the publish/compare-and-publish path, the `served-by` envelope stamp).
- **None within Phase 4a to START** — build against the verdict contract this plan fixes, using
  **fake checker verdicts** (runs in parallel with 4a-1). **The merge gate needs 4a-1's
  `checker_verdict.py`** (`parse_verdict` / `derive_pass` / `canonical_score`) — import it, do not
  re-stub it once 4a-1 has landed.

## Scope

**In scope:**
- `render_job_service.py`: the `run_checker` + `decide_quality` stages inserted at the reserved seam;
  the rework mechanics (provenance-tagged feedback, WHAT-escalation); the attempt history; verdict
  artifacts; the terminal policy table.
- `config.py`: `QUALITY_MAX_ATTEMPTS = 15`, `QUALITY_MAX_WHAT_REWORKS = 2`,
  `QUALITY_STRUCTURAL_STOP = 3`; **register the checker stage timeout in the existing stage-timeout
  list** (so the reaper ceiling extends with zero formula edit).
- `schema.sql` + a migration: **ONLY the four flag columns** (`human_review`, `review_reason`,
  `published_attempt`, `published_score`).
- `routes/pages.py`: add `human_review` to the `/render/status` JSON, **read from the served
  artifact's envelope**.
- The best-attempt publish path: stamp `human-review` + `review-reason` into the served-artifact
  envelope beside `source-hash`.
- `cast-server/tests/test_quality_loop.py` (or extend `test_render_job_service.py`) + the migration
  test + the `test_fr007_readonly_guard.py` maker sweep re-run.

**Out of scope (do NOT do these):**
- Do NOT add `heartbeat_at` — it already ships in Phase 3's CREATE TABLE (reconciliation C4).
- Do NOT write a new reaper formula — Phase 3's ceiling already derives from the configured stage
  list; you only **register** the checker stage (revision a).
- Do NOT create the checker agent or `checker_verdict.py` — that's 4a-1 (import it).
- Do NOT build a flagged-renders list / review dashboard — recording-only; the list is Phase 5d.
- Do NOT edit the spec — 4a-3.
- Do NOT widen `gate_html`'s report (carriage/survival) — that's 4b's disjoint seam (see C3).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/services/render_job_service.py` | Modify | Phase 3 pipeline ending `gate_html → publish` |
| `cast-server/cast_server/config.py` | Modify | Has `RENDER_*` + stage-timeout list; no `QUALITY_*` |
| `cast-server/cast_server/db/schema.sql` | Modify | `render_jobs` has `heartbeat_at`, no flag columns |
| `cast-server/cast_server/routes/pages.py` | Modify | `/render/status` JSON has no `human_review` |
| `cast-server/cast_server/requirements_render/checker_verdict.py` | Import (from 4a-1) | Created by 4a-1 |
| `cast-server/tests/test_quality_loop.py` | Create | Does not exist |
| `cast-server/tests/test_schema_migration.py` | Modify | Covers `schema.sql` changes |
| `cast-server/tests/test_fr007_readonly_guard.py` | Modify (re-run) | Maker sweep exists |

## Detailed Steps

### Step 4a2.1: `run_checker` stage

The runner computes `extract_zero_click_view(attempt_html)` (byte-deterministic input, the
eval-harness faithfulness pattern), inlines **zero-click view + full HTML + family** into the user
message, dispatches `cast-requirements-render-checker` through the `AgentRunner` seam (timeout from
the agent config), and parses via `checker_verdict.parse_verdict`. **One retry** on parse/subprocess
failure; a second failure marks the attempt `unscored` (recorded, never silent) and the loop
proceeds. Touch `heartbeat_at` at the `run_checker` and `decide_quality` stage boundaries.

> **Scoreability under the OVERRIDE:** a structurally-broken attempt (failed `gate_html` after its
> one structural retry) is **still sent to `run_checker`** — it is scoreable. It does NOT
> short-circuit to a serve/fallback the way Phase 3's no-loop Branch 2 did; the 4a loop's
> `decide_quality` is the single terminal decision point and supersedes Phase 3's in-loop
> structural-exhaustion serve.

### Step 4a2.2: `decide_quality` stage — the policy table (THE OVERRIDE BAKED IN)

Implement exactly the policy table in `_shared_context.md` ("decide_quality policy table"). The
load-bearing differences from the source plan's text:

- **There is NO "zero structurally-valid attempts → deterministic fallback" row.** The override
  deletes it. If any attempt was extracted (even structurally broken), it is served + flagged.
- **Deterministic fallback fires ONLY on literal no-output** (crash / timeout / zero attempts ever
  extracted) — never LLM-gated.
- **Terminal best-attempt ranking = PREFER VALID, THEN SCORE** (owner-confirmed for this split):
  serve the best-scoring structurally-VALID attempt (`review_reason='non_convergent'`); fall to the
  best-scoring structurally-BROKEN attempt (`review_reason='structural_violation'`,
  `served-by: structural_violation`) **only when no valid attempt exists**. A broken attempt can
  never outrank a valid one on score alone.
- A **clean** publish (`status=published`, no flag, `served-by: maker`) requires BOTH structural
  validity AND `derive_pass(verdict)` true.
- `review_reason` enum: `non_convergent | checker_unavailable | structural_degradation |
  structural_violation`. Tie on score → latest attempt.
- **Prefer-valid precedence (the full ordering, so the mixed case is unambiguous):** a
  structurally-VALID attempt always outranks a structurally-BROKEN one, regardless of score. Among
  valid attempts: prefer scored over unscored, then highest canonical score, then latest. Only when
  **zero valid attempts exist** does ranking fall to broken attempts (highest score, then latest →
  `structural_violation`). So a valid-but-unscored attempt beats a broken-but-scored one and serves
  with `review_reason='checker_unavailable'` (valid, just never scored), NOT `structural_violation`.

### Step 4a2.3: Rework mechanics

Re-run `run_how` with the failing verdict's `rework_feedback[]` appended through the **same**
`GateReport.violations` transport Phase 3 already uses, plus a one-line score history
(`attempt 3 of N; best so far 0.65 at attempt 2`) so the agent knows regression is visible. Each
rework attempt re-passes `gate_html` (with Phase 3's one structural retry) before it reaches the
checker.

**[CQ1] Provenance-tagged feedback.** Deterministic structural violations (hard, non-negotiable) and
checker `rework_feedback` (subjective quality nudges) ride the **same** transport but each item
carries an explicit provenance tag (`structural` vs `quality`); the rework prompt renders them under
**separate headings** — **"Structural fixes (required)"** vs **"Quality improvements (guidance)"**
— so the HOW agent never treats a taste suggestion as a hard requirement or silently down-weights a
structural correction. Transport stays shared (Phase 3's channel); only the prompt rendering
distinguishes them.

### Step 4a2.4: WHAT-escalation

If **3 consecutive** verdicts name the **same gated `missing[]` token**, the comprehension failure
is intent-level, not representation-level → re-run `run_what` **once** with the accumulated feedback
(then `gate_what`, then resume HOW reworks); at most `QUALITY_MAX_WHAT_REWORKS` (2) WHAT re-runs per
job.

**[CQ2] WHAT-re-run gate failure.** If the forced `run_what` re-gen's own output FAILS `gate_what`:
- the prior **known-good WHAT doc is RETAINED** (the failed re-gen is discarded, NOT the good WHAT);
- the `QUALITY_MAX_WHAT_REWORKS` budget is **still decremented**;
- HOW reworks **resume against the retained WHAT**;
- **no deterministic fallback fires** — a structurally-valid (or at minimum, *present*) attempt
  history already exists, so the literal-no-output branch is inapplicable (the OVERRIDE makes this
  doubly true: even with zero *valid* attempts, a present attempt serves + flags).

### Step 4a2.5: The safety ceiling + companion knobs

`QUALITY_MAX_ATTEMPTS` in `config.py`, default **15** — deliberately high; the **anti-infinite-loop
guard ONLY**, never a cost cap (cost/latency/tier stay unconstrained; the Phase-3 in-flight
semaphore stays the only resource guard). Companion knobs (config, not magic constants):
`QUALITY_MAX_WHAT_REWORKS = 2`; `QUALITY_STRUCTURAL_STOP = 3` (consecutive structural failures →
early terminal: continuing to rework a structurally-degraded maker burns the ceiling for nothing →
best attempt + flag, preferring valid; `review_reason='structural_degradation'`, or
`structural_violation` if the served attempt is itself broken).

### Step 4a2.6: Attempt history & verdict artifacts

In-memory per-job list of `(attempt_no, html_path, gate_report, verdict | unscored,
canonical_score, structurally_valid: bool)`. Every verdict written as `attempt-N.verdict.json` under
`build/render-jobs/{slug}/{hash12}/` (the 3c retention pattern extended) — the non-convergence
post-mortem is fully replayable from disk. The `structurally_valid` flag (from `gate_html`) is what
the "prefer valid" ranking reads.

### Step 4a2.7: `render_jobs` columns — migration (C4: the four flag columns ONLY)

`schema.sql` + a migration adding:

```
human_review      INTEGER NOT NULL DEFAULT 0
review_reason     TEXT        -- non_convergent | checker_unavailable | structural_degradation | structural_violation
published_attempt INTEGER
published_score   REAL
```

**Do NOT add `heartbeat_at`** — Phase 3's CREATE TABLE already ships it. Status enum **unchanged**
(`published` covers flagged publishes; `flagged` already exists from Phase 3). Follow the
`test_schema_migration.py` additive pattern (nullable/defaulted; no row rewrites). **[A2]** these
columns are the **queryable/observability copy** (Phase-5 sweep, post-mortem) — they are **NOT** the
status-poll read path.

### Step 4a2.8: Best-attempt publish path + served-artifact envelope stamp

The chosen attempt's HTML goes through the **same** `publish` stage (compare-and-publish hash
re-check, AUTO-GENERATED header + `source-hash` envelope, atomic write) so caching, status `ready`,
and SC-005 hold identically for flagged publishes. **[A2]** the publish envelope additionally stamps
`human-review` (+ `review-reason`) beside `source-hash`, so the **served artifact is the single
source of truth for the flag** exactly as it already is for readiness ("the artifact IS the state").
Set `served-by: maker` for a clean/non_convergent valid serve, `served-by: structural_violation`
for a broken serve (extends the Phase-3 stamp vocabulary).

### Step 4a2.9: Status endpoint addition

`GET /goals/{slug}/render/status` JSON gains `human_review: bool` **read from the served artifact's
envelope** (the stamp from 4a2.8), **never from "the latest job row for the current hash"** **[A2]**.
Deriving from the latest row is unsafe: while a newer regen job for the same hash is `running` (the
3d stale-render-with-banner state), that row's `human_review` defaults to 0 even though the artifact
actually served is a *prior flagged* publish — a latest-row read would silently clear the flag of the
page the reader is looking at. **[P1]** the 4s poll must NOT add a per-request `render_jobs` read —
it reads the flag off the artifact it already stats for `ready`, so the hot path never regains a DB
round-trip. The page itself is NOT banner-stamped (the artifact stays byte-stable per 3d; a review
surface is Phase 5d).

### Step 4a2.10: C3 merge note (4a ∥ 4b on this file)

4a inserts `run_checker → decide_quality` **after** `gate_html`; 4b widens `gate_html`'s report
(carriage + comment survival). **Disjoint seams.** If 4b has already landed when you execute 4a-2,
do the mechanical merge: treat whatever widened `gate_html` report 4b produced as the structural
gate `run_checker`/`decide_quality` wrap (a survival-failing attempt is just another structural
violation under the OVERRIDE — scoreable/servable + flagged, with in-block comment misses surfacing
as 4b's unplaced badges). If 4a lands first, 4b does the merge. No logic conflict — different lines.

## Verification

### Automated Tests (permanent — all fake-runner, no LLM in default CI)

`pytest cast-server/tests/test_quality_loop.py` green:
- **US4 rework path:** fake checker fails attempt 1 with `rework_feedback`, passes attempt 2 →
  published; assert the attempt-2 HOW prompt contains the attempt-1 feedback strings **verbatim**,
  under the **"Quality improvements (guidance)"** heading (CQ1); assert both
  `attempt-N.verdict.json` artifacts exist.
- **SC-004 unchanged (literal no-output):** fake runner crash/timeout/empty **before any attempt** →
  deterministic fallback published, `status=fallback`, reason recorded; assert the checker stage was
  **never invoked** (the fallback page is NOT LLM-gated).
- **SC-008 non-convergence (valid attempts):** fake checker never passes across attempts with varied
  canonical scores (e.g. attempt 2 scores highest of 4, all structurally valid) → loop runs to the
  ceiling → **attempt 2's HTML is published** (assert content identity), `human_review=1` +
  `review_reason='non_convergent'`, and the published file is **NOT** the deterministic render
  (assert against a real `render_requirements()` output of the same source); status endpoint reports
  `ready` with `human_review: true`.
- **OVERRIDE — broken-only terminal (the deleted-fallback-row replacement):** every attempt fails
  `gate_html` (zero structurally-valid attempts) but attempts WERE extracted → assert the
  best-scoring **broken** attempt is published, `human_review=1`,
  `review_reason='structural_violation'`, `served-by: structural_violation`, and the deterministic
  page is **NOT** served (assert against `render_requirements()`). **This is the load-bearing
  override test** — the source plan would have served the deterministic page here.
- **OVERRIDE — prefer-valid ranking:** mix of attempts where a structurally-BROKEN attempt has a
  higher canonical score than the best structurally-VALID attempt → assert the **valid** attempt is
  served (`review_reason='non_convergent'`), NOT the higher-scoring broken one. Pins the
  owner-confirmed tiebreak.
- **Checker-unavailable terminal:** fake checker raises twice for an attempt → that attempt
  `unscored`; if no scored attempt exists at terminal, the latest valid (else latest) attempt is
  published + `review_reason='checker_unavailable'` — never the plain page while output exists.
- **WHAT-escalation:** fake checker fails 3 consecutive attempts with the same gated `missing[]`
  token → assert the next rework re-runs `run_what` (accumulated feedback) before `run_how`, ≤2×.
- **[T1] WHAT-escalation gate-failure:** a forced WHAT re-run whose `run_what` output FAILS
  `gate_what` → assert the prior known-good WHAT is **retained**, `QUALITY_MAX_WHAT_REWORKS` is
  decremented, HOW reworks resume against the retained WHAT, and **no deterministic fallback fires**.
- **[T2] Served-artifact flag fidelity:** publish a flagged best-attempt for hash `H`
  (`human_review=1`), then open a NEW `running` regen job for the same `H` → assert the status
  endpoint reports `human_review: true` read from the **served-artifact envelope**, NOT `false` from
  the fresh `running` row's default.
- **Ceiling + structural-stop config:** loop stops at exactly `QUALITY_MAX_ATTEMPTS` (config
  override in test); early-stop after `QUALITY_STRUCTURAL_STOP` consecutive structural failures
  asserted.
- **Migration test:** the four new `render_jobs` columns present on a fresh DB and added to an
  existing v3 DB without data loss; assert `heartbeat_at` was NOT re-added (already present).
- **`test_fr007_readonly_guard.py` maker sweep** re-run green with the checker stage active — the
  loop never widens the write surface (still only `RENDER_JOBS_DIR` + the atomic publish).

### Validation Scripts (temporary)

A one-off fake-runner driver printing the job row + served-artifact envelope for each terminal branch
(clean / non_convergent / structural_violation / checker_unavailable / structural_degradation /
fallback). Discardable.

### Manual Checks

- Grep `render_job_service.py`: confirm `decide_quality` has NO "zero-valid → deterministic" path;
  confirm fallback fires only on literal no-output; confirm `parse_verdict`/`derive_pass`/
  `canonical_score` are **imported** from `checker_verdict.py`, not re-implemented.
- Confirm the status poll reads `human_review` from the artifact envelope, not a `render_jobs` query.
- Confirm no `heartbeat_at` in the migration; confirm the checker stage timeout is registered in the
  stage-timeout list (reaper extends automatically).

### Success Criteria

- [ ] Pipeline runs `…→ gate_html → run_checker → decide_quality → publish`; the policy table is
      exhaustive and each row maps to a recorded job state (zero silent failures).
- [ ] **OVERRIDE encoded:** deterministic fallback ONLY on literal no-output; structurally-broken
      present attempts are scored, served, and flagged `structural_violation` — the deterministic
      page is NEVER served when any attempt exists.
- [ ] **Prefer-valid ranking:** best-scoring valid attempt beats a higher-scoring broken one.
- [ ] Provenance-tagged feedback under separate prompt headings (CQ1); WHAT-escalation + its
      gate-failure retention path (CQ2/T1).
- [ ] Migration adds ONLY the four flag columns; `heartbeat_at` untouched (C4).
- [ ] Status JSON exposes `human_review` from the served-artifact envelope (A2/P1); T2 fidelity test
      green.
- [ ] Reaper extended by registering the checker stage — **no formula edit**.
- [ ] All fake-runner tests green; readonly-guard sweep byte-identical; migration test green.

## Execution Notes

- **The OVERRIDE is the single most important deviation from the source plan.** The source plan's
  `§Fork Resolution` (RATIFIED), `§Decisions #4`, the policy table's "zero-valid → deterministic"
  row, and the matching Key-Risks/spec text are **superseded** by `decisions-so-far.md` lines 104/107.
  Implement the override (structurally-broken = scoreable/servable + flagged); deterministic only on
  literal no-output. When in doubt, re-read the `_shared_context.md` OWNER OVERRIDE section.
- **Best-attempt now means best-SCORING (prefer valid).** Phase 3's "best attempt = last extractable
  HTML" was the no-scoring placeholder; 4a introduces scoring and the prefer-valid tiebreak.
- **Spec consistency:** the rework loop, ceiling, flag columns, status-JSON addition, and the
  precise (overridden) FR-006 policy are new spec'd behavior → **flag for 4a-3's
  `/cast-update-spec`; do NOT edit the spec here.**
- **Spec-linked files:** if this sub-phase modifies files covered by
  `cast-requirements-render.collab.md`, read the spec and verify SAV behaviors are preserved; record
  the deltas for 4a-3.
