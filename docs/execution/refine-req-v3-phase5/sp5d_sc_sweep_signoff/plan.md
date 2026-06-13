# Sub-phase 5d: Full SC-001…SC-018 Sweep, Final Spec Reconciliation & Sign-Off

> **Pre-requisite:** Read `docs/execution/refine-req-v3-phase5/_shared_context.md` before starting —
> especially **Applied Owner-Resolved Edits #2 (flagged-renders list)**, **#6 (the SC sweep is
> SC-001…SC-018, NOT SC-001…SC-008)**, the **structural-violation override**, and the **Cross-Phase
> Hard Edges** (the drift-sweep checklist below verifies them landed).

## Objective

Sweep **SC-001…SC-018** against the integrated system with results captured in a sign-off artifact;
verify the accumulated cross-phase coordination notes landed (the integration drift sweep, now
including the 5a gap stages); record the shipped v3 behavior (including gap-fill) in
`cast-requirements-render.collab.md`; give `cast-requirements-roundtrip.collab.md` its one conditional
minimal delta (first real emitter) or a recorded no-change rationale; **add the minimal flagged-renders
list** on an existing screen; and sign the goal off with **every** flag and carry-forward stated, none
suppressed.

## Dependencies

- **Requires completed:** 5a + 5b + 5c (the whole Phase 5 surface: gap machinery live, markers
  rendering, GATE-ALL applied, nine-family corpus + eval harness present).
- **Assumed codebase state:** the spec is at **v6** (SC-001…SC-018 defined; SC-009 commenting e2e,
  SC-010–013 maker pipeline, SC-014–016 quality gate, SC-017–018 survival+narration). `docs/specs/_registry.md`
  carries the render + roundtrip rows. The 4a `render_jobs` flag columns + the served-artifact
  envelope stamp exist (recording-only); an existing screen (`/runs` or goals) is the host for the list.
- **Terminal sub-phase** — nothing depends on 5d.

## Scope

**In scope:**
- The SC-001…SC-018 sweep table in `signoff/sc-sweep.md` (per-SC: procedure, result, evidence link,
  residual flags).
- The integration drift sweep (4a→3 corrections incl. the gap stages; 4b seam pin; single-helper
  checks; checker amnesty line; the C5 `GAPFILL_*` knobs landed + read).
- Two inline `/cast-update-spec` passes (render v6 + conditional roundtrip), under **standing session
  approval**, with `_registry.md` rows bumped.
- The **minimal flagged-renders list** (slug, reason, score, link) on an existing screen — additive,
  read-only.
- The sign-off (`signoff/sc-sweep.md` + a closing note in the goal dir).

**Out of scope (do NOT do these):**
- Do NOT build a human-review **queue UI** (the 4a open question — a future-goal owner call); the
  minimal list is the whole surface.
- Do NOT re-implement verification — the sweep RE-RUNS existing harnesses/tests; eval results are
  committed evidence, not hand-asserted.
- Do NOT change behavior in 5d — it is sweep + spec-record + list + sign-off. Any behavior gap found
  is a finding for a 5a/5b/5c fix, not patched here.
- Do NOT modify the intake/gate/apply contracts in the roundtrip spec (emitter-side delta only).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `docs/goal/refine-requirements-better-rendering-v3/signoff/sc-sweep.md` | Create | Does not exist |
| `docs/goal/refine-requirements-better-rendering-v3/signoff/golden/` | Modify | 5c's provisional renders; SC-002 evidence refreshed post-gap-machinery |
| `docs/specs/cast-requirements-render.collab.md` | Update (via `/cast-update-spec`) | v6 → v7: gap-fill contract, marker vocabulary, nine-family record, flagged-renders list |
| `docs/specs/cast-requirements-roundtrip.collab.md` | Update (conditional, via `/cast-update-spec`) | Draft v1 → narrow the "real emitters deferred" fence, OR record no-change rationale |
| `docs/specs/_registry.md` | Modify | Bump the render (+ conditional roundtrip) rows |
| (existing screen) `cast-server/cast_server/routes/pages.py` + its template (e.g. `/runs` or goals) | Modify | Add the read-only flagged-renders list (slug, reason, score, link) |

> Confirm the flag columns + envelope read-path before wiring the list:
> `grep -rn "human_review\|review_reason\|published_score\|published_attempt" cast-server/cast_server/`.
> Confirm the host screen + its route: `grep -n "def .*runs\|def .*goals" cast-server/cast_server/routes/pages.py`.

## Detailed Steps

### Step 5d.1: The SC sweep — SC-001…SC-018 against the integrated system

Build `signoff/sc-sweep.md` with one row per criterion: procedure run, result, evidence link,
residual flags. **The full sweep is the eighteen criteria the spec carries at v6** (the source plan
body says SC-001…SC-008 because it predates the spec growth — sweep all eighteen).

| SC | Procedure | Evidence source |
|----|-----------|-----------------|
| **SC-001** (cold reader) | The 4a checker verdicts from the 5c sweep, per family — the checker stands in for the human reader (its verdict shape is a strict superset of v2 SC-001 by 4a design). | 5c per-family verdicts |
| **SC-002** (nine distinct families) | **RE-RUN** `eval_family_sweep.py` after 5a/5b land (gap machinery live) so the final evidence reflects the shipped pipeline; refresh `signoff/golden/`. | `eval_family_sweep.py` (re-run) |
| **SC-003** (comment survival) | Re-run 4b's SC-003 eval sweep on a regenerate with open comments through the integrated pipeline. | `eval_sc003_survival.py` |
| **SC-004** (no-output crash → deterministic) | Re-run 3c's fault-injection (fake-runner crash) + one live kill of a real job. (Under the override the deterministic page is reserved for literal no-output — assert that.) | `test_render_job_service.py` + live kill |
| **SC-005** (cache hit) | Repeat-view observation — second view serves the cached file, `render_jobs` shows no new row. | live observation |
| **SC-006** (discoverable commenting) | Phase 2's affordance — static verdict + human-eyeball carry-forward (unprompted usability is a human check by nature). | static + carry-forward |
| **SC-007** (gap injection) | The 5b gap-injection test, **both arms**, plus one **live** e2e run against a corpus doc with a deleted detail. | `test_gap_reconciliation.py` + live e2e |
| **SC-008** (non-convergence → best-attempt + flag) | Re-run 4a's force-never-pass eval; assert best-scoring valid attempt served, `human_review` recorded, deterministic page NOT served. | `test_quality_loop.py` / quality eval |
| **SC-009** (commenting e2e) | Cite the Phase-4b UI-test coverage of the named selectors (`.comment-affordance`/`.comment-pill`/…/`.comment-unplaced`/`.diff-narration`). | `cast-server/tests/ui/` (browser-capable CI) |
| **SC-010** (two real families distinct) | Subsumed + exceeded by SC-002's nine-family sweep; cite the eval-harness green. | `eval_family_sweep.py` |
| **SC-011** (maker never writes canonical) | Cite `test_fr007_readonly_guard.py` (the maker read-only sweep) + 5b's full-gap-fill byte-identical extension. | `test_fr007_readonly_guard.py` |
| **SC-012** (generating state converges) | Cite the fake-runner route tests + the status-poll hash derivation. | `test_render_route_and_service.py` |
| **SC-013** (two-branch degradation surfaced) | Cite the publish-branch tests + badge injection (literal no-output → fallback; structural-gate exhaustion → flagged best attempt, never deterministic). | `test_render_job_service.py` + `test_render_route_and_service.py` |
| **SC-014** (checker ≠ gate; gap amnesty) | Cite `eval_quality_gate.py` (the `low_quality_attempt.html` passes `check_html` but fails `derive_pass`; a `.rr-gap` page is NOT failed for a missing outcome — the 5b amnesty line realizes this). | `eval_quality_gate.py` + 5b amnesty |
| **SC-015** (terminal policy = OWNER OVERRIDE, exhaustive) | Cite `test_quality_loop.py` (every terminal branch; PREFER-VALID; deterministic never served when any attempt exists). | `test_quality_loop.py` |
| **SC-016** (human-review flag recording-only in 4a; LIST is 5d) | Cite the 4a recording-only coverage AND record that **5d adds the minimal flagged-renders list** (Step 5d.3) — the spec update reflects the list now exists. | `test_schema_migration.py` + Step 5d.3 |
| **SC-017** (comment survival / zero new orphans) | Cite `eval_sc003_survival.py` + `test_comment_survival.py`; confirm green with gap markers present on the rendered DOM. | `eval_sc003_survival.py` + `test_comment_survival.py` |
| **SC-018** (narration trust boundary) | Cite `eval_sc003_survival.py` (trust-boundary block) + the narration-API tests + `test_schema_migration.py`. | `eval_sc003_survival.py` + narration tests |

Plus the top-level test suite (`pytest cast-server/tests/`) green and the eval-harness results recorded.

### Step 5d.2: Integration drift sweep (verify the deferred coordination notes landed; fix residue)

- **4a→3 corrections, EXTENDED for the 5a gap stages:** the reaper ceiling is derived from the full
  configured stage list (quality-loop-sized) AND now includes `gapfill_timeout` + the ask-round WHAT
  re-run; the reaper releases the in-flight semaphore slot of a reaped orphan; `heartbeat_at` is
  written at stage boundaries, **including each new gap stage boundary** (5a landed the heartbeats —
  verify the ceiling formula counts the new stages). The `GAPFILL_ASK_ROUNDS` counter stays SEPARATE
  from the in-loop `QUALITY_MAX_WHAT_REWORKS` (A2), and the probe `run_how` does NOT debit
  `QUALITY_MAX_ATTEMPTS` (C6) — confirm the merge did not collapse any counter.
- **C5 knobs landed:** `GAPFILL_MAX_GAPS` (default 5) + `GAPFILL_ASK_ROUNDS` (default 1) present in
  `config.py` AND actually read by the WHAT prompt cap + the `ask_what` stage (not dead config).
- **4b seam pin:** survival evaluated inside `gate_html` before `run_checker`; a survival-failing
  attempt is part of the *surfaced* structural report (servable + flagged under the override), not a
  silent disqualifier — confirm the merged loop honors it **with gap markers present**.
- **Single-helper discipline:** one `verbatim_locate` (the 5a evidence check reuses it — CQ2), one
  `strip_inline_markdown` (no second stripper in gap code), one `container_text_index` (marker
  correspondence reuses it). Grep to prove no second implementation crept in.
- **Checker amnesty line present** in the `cast-requirements-render-checker` prompt (5b), reconciled
  with SC-014.
- **GATE-ALL applied:** `WRITEBACK_GATE_POLICY` default is `"gate-all"`; `change_request_service` is
  byte-unchanged.

### Step 5d.3: The minimal flagged-renders list (owner-resolved human-review surface)

On an **existing** screen (e.g. `/runs` or goals), add a **read-only** list of flagged renders: one
row per render with `human_review=1`, showing **slug, reason (`review_reason`), score
(`published_score`), and a link**. Source the data from the existing `render_jobs` flag columns + the
served-artifact envelope (4a recording-only — no new write path, no new column). Additive scope; no
queue/triage UI. This is the honest degraded-page signal the structural override makes load-bearing
("surface, don't suppress"). The 4a executor shipped recording-only; 5d adds the list.

### Step 5d.4: Final spec reconciliation (two `/cast-update-spec` passes, standing approval)

→ Delegate: `/cast-update-spec` on `cast-requirements-render.collab.md` (review the diff before
approval, under standing session approval) with these deltas:
1. **Gap-fill contract (FR-015/FR-016 realized):** the activated `gaps[]` schema; the HOW trailer
   ask-channel + the bounded ask loop (`GAPFILL_ASK_ROUNDS`, `GAPFILL_MAX_GAPS`); the
   `cast-requirements-gapfill` agent (tool-free subagent carve-out, grounded-or-refuse, corpus
   allowlist, server-side verbatim evidence validation via the shared `verbatim_locate`); gap CRs
   gate-pinned to `kind="addition"`; the `.rr-gap` marker contract (question + fixed status
   vocabulary, NEVER the proposed answer) + the page-renders-only-canonical invariant with its
   un-mark-via-regeneration mechanism; gap CRs as normal change-requests (provenance values recorded);
   **the GATE-ALL policy value for this goal** (every gap CR human-gated).
2. **Nine-family verification record:** SC-002's evidence procedure (corpus + `eval_family_sweep.py` +
   `human_review` signal) recorded as the standing verification for the happy path.
3. **The flagged-renders list:** update SC-016's "no list — that is Phase 5d" pointer to record that
   the minimal list now exists (Step 5d.3).
4. New surfaces appended to `linked_files`: the gapfill agent dir, the gap additions in
   `maker_gate.py` / `render_job_service.py`, the `gaps-state.json` shape, `test_gap_reconciliation.py`,
   the corpus fixtures dir, the flagged-renders list route/template.

→ Delegate: `/cast-update-spec` on `cast-requirements-roundtrip.collab.md` — **conditional minimal
delta:** narrow the Out-of-Scope "real downstream emitters" fence to record the first real emitter
(render gap-fill; **emitter-side only** — intake/gate/apply contracts unchanged), add the emitter to
`linked_files`. If the diff review concludes even this is over-reach, record the explicit no-change
rationale in `sc-sweep.md` instead — either way the decision is **written down, not silent**.

Bump `docs/specs/_registry.md` rows for both specs touched.

### Step 5d.5: Write the sign-off

`signoff/sc-sweep.md` + a closing note in the goal dir: what's green, what's flagged (every
`human_review`-flagged family render from 5c; every human-eyeball carry-forward — the nine-family
visual review, the gated un-mark e2e, SC-006), what stays deferred (**[USER-DEFERRED]** model-tier
tune-down review; the human-review **queue** UI from 4a's open questions; the v2 timed-read
evaluation). The bar: "put in front of a customer without apologizing" — with the apologies that DO
remain **stated explicitly**, never silently dropped at the finish line.

## Verification

### Automated Tests (permanent + eval)
- Full default-CI suite green: `pytest cast-server/tests/`.
- Eval harnesses re-run + results recorded: `eval_family_sweep.py` (SC-002), `eval_sc003_survival.py`
  (SC-003/017/018), `eval_quality_gate.py` (SC-014), the quality-loop terminal tests (SC-008/015), the
  gap-reconciliation suite (SC-007).
- `bin/cast-spec-checker` green on **both** updated specs; `docs/specs/_registry.md` rows bumped.

### Manual Checks
- `signoff/sc-sweep.md` has a row for **each** of SC-001…SC-018 (eighteen rows) with procedure,
  result, evidence link, residual flags.
- The sign-off lists **every** `human_review`-flagged family render AND **every** human-eyeball
  carry-forward as explicit open items (cross-check against 5c's recorded flags).
- The flagged-renders list renders on the host screen from existing flag columns (no new write path /
  column) — `git diff` shows no `render_jobs` schema change in 5d.
- Drift-sweep greps confirm: single `verbatim_locate`/`strip_inline_markdown`/`container_text_index`;
  the reaper ceiling formula references the gap stages; `GAPFILL_*` knobs are read (not dead); the
  checker amnesty line is present; `WRITEBACK_GATE_POLICY` default is `"gate-all"`.

### Static / carry-forward (no browser in autonomous runs)
- The human-eyeball browser passes (nine golden renders side-by-side; the gated un-mark e2e; SC-006
  discoverability) are static verdicts + carry-forwards recorded in the sign-off; they never block.

### Success Criteria
- [ ] `signoff/sc-sweep.md` exists with all eighteen SC rows (procedure / result / evidence / residual flags).
- [ ] SC-002 re-run post-gap-machinery; `signoff/golden/` refreshed to the shipped pipeline.
- [ ] Integration drift sweep complete: reaper ceiling + heartbeats include the gap stages; counters
      independent (A2/C6); C5 knobs landed + read; single-helper discipline holds; amnesty line
      present; GATE-ALL applied; `change_request_service` byte-unchanged.
- [ ] The minimal flagged-renders list renders read-only on an existing screen from the 4a flag columns
      (no new write path / column).
- [ ] `/cast-update-spec` landed on `cast-requirements-render.collab.md` (gap contract + marker
      vocabulary + nine-family record + flagged-list pointer + new `linked_files`); conditional
      roundtrip delta landed OR a no-change rationale recorded in `sc-sweep.md`; `_registry.md` bumped;
      `bin/cast-spec-checker` green on both.
- [ ] Full test suite + eval harnesses green/recorded.
- [ ] Sign-off states every flag + carry-forward + deferred item explicitly; none suppressed.

## Execution Notes

- **Sweep eighteen, not eight.** The single easiest way to under-deliver this sub-phase is to copy the
  source plan's "SC-001…SC-008" literally. The spec grew to v6; the goal is signed off against ALL of
  SC-001…SC-018. Most of SC-009…SC-018 are already proven by named phase-3/4a/4b tests — cite the
  evidence, don't re-derive.
- **5d records, it does not build behavior.** If the sweep surfaces a real behavior gap, that is a
  finding routed back to 5a/5b/5c — do not patch behavior inside the sign-off sub-phase (the one
  additive exception is the flagged-renders list, which is the owner-resolved 5d deliverable).
- **The override makes flags load-bearing.** Under "best-attempt+flag even for structural violations,"
  the flagged-renders list is the only honest signal that a degraded page shipped — that is why it
  lands here and why the sign-off must enumerate every flag.
- **Standing approval ≠ unattended.** The two `/cast-update-spec` passes still show the diff and use
  the skill's gate; standing approval means the owner pre-authorized the additive spec edits, not that
  the diff is skipped.
- **Spec-linked files:** this sub-phase IS the spec work — all 5a/5b flags resolve in the single
  render-spec pass; the roundtrip touch is minimal and conditional; clause texts were fixed by the
  source plan up front (the 3e discipline — the spec records behavior, never retro-discovers it).
