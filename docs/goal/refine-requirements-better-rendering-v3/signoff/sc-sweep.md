# SC-001…SC-018 Sweep & Sign-Off — Refine Requirements Better Rendering v3 (sub-phase 5d, FINAL)

> **Terminal artifact of the whole goal.** This is the full eighteen-criterion sweep against the
> integrated system (gap machinery live), the integration drift sweep, the spec-reconciliation record,
> and the honest carry-forward ledger. The provisional 5c SC-002 note is **superseded** by SC-002 below.
>
> **Mode:** autonomous run — no browser. Every human-eyeball pass (nine golden renders side-by-side,
> the gated un-mark e2e, SC-006 discoverability) is a **static verdict + human-eyeball carry-forward**
> per the project no-browser-visual-gate convention; none blocks. The bar applied: *"put it in front of
> a customer without apologizing — with the apologies that DO remain stated explicitly, never silently
> dropped at the finish line."*

## The eighteen criteria

The unified sweep is **SC-001…SC-018**: the goal's SC-001…SC-008 (`refined_requirements.collab.md`)
∪ the spec criteria SC-009…SC-018 that the render spec accreted across Phases 3/4a/4b (SC-009
commenting e2e; SC-010–013 maker pipeline; SC-014–016 quality gate; SC-017–018 survival + narration).
Gap/family-specific criteria are run **fresh**; the rest cite the named, already-green phase-3/4a/4b
evidence (the sweep re-runs harnesses, it does not re-derive behavior).

| SC | Criterion (one-line) | Procedure | Result | Evidence | Residual flag |
|----|----------------------|-----------|--------|----------|---------------|
| **SC-001** | Cold reader can state job/outcome/scope per family | The 4a `cast-requirements-render-checker` verdict (a strict superset of the v2 cold-reader shape) stands in for the human reader; read per-family from the 5c sweep | **PASS** | `eval_quality_gate.py` (pinned by `test_eval_quality_gate.py`, green) + 5c per-family verdicts | Side-by-side human eyeball = carry-forward |
| **SC-002** | Nine families render visibly-distinct, appropriate layouts | Nine-family real-pipeline sweep through the production maker (WHAT → gates → HOW → 4a loop), gap machinery **live**; per-family terminal state + `served_by` + `human_review` + score + `check_html` | **PASS, 6/9 clean** | `eval_family_sweep.py` + `signoff/golden/` (nine renders + index) | **3 HOW-layer flagged** (`bug_fix`, `pilot_poc`, `random_idea`) — see §SC-002 detail + carry-forwards |
| **SC-003** | A regenerate orphans no open comment | 4b survival sweep on a regenerate with open comments through the integrated pipeline, gap markers present on the DOM | **PASS** | `eval_sc003_survival.py` + `test_comment_survival.py` (green in suite) | Browser badge eyeball = carry-forward |
| **SC-004** | True no-output crash → deterministic page served | 3c fault-injection (fake-runner crash/empty) + the structural override assertion (deterministic page reserved for **literal** no-output only) | **PASS** | `test_render_job_service.py::test_no_output_serves_deterministic_fallback` + `test_what_crash_falls_back_without_running_how` (green) | Live kill of a real job = carry-forward (autonomous; fault-injection covers the branch) |
| **SC-005** | Unchanged source serves the cache, no new model call | Repeat-view: the source-hash cache envelope returns the file unchanged, no new `render_jobs` row | **PASS** | `test_render_route_and_service.py` (cache-hit route tests, green) | Live repeat-view observation = carry-forward |
| **SC-006** | First-time reader discovers commenting unprompted | Phase 2 affordance (`.comment-affordance` + hint injected behind the slug guard) | **PASS (static) + carry-forward** | `cast-server/tests/ui/` selector coverage (browser-capable CI) | Unprompted-usability is a human check by nature = carry-forward |
| **SC-007** | Missing detail → ask upstream or mark the gap, never ship silently-incomplete | The 5b gap-reconciliation test, **both arms** (auto-apply mechanism lane + the gated FR-016 lane), + gap-injection on a corpus doc with a deleted detail | **PASS** | `test_gap_reconciliation.py` (green) + `test_fr007_readonly_guard.py` full-gap-fill byte-identical extension | Live deleted-detail e2e = carry-forward |
| **SC-008** | Non-convergence → best-scoring attempt + `human_review`, never the plain page | 4a force-never-pass terminal: best-scoring valid attempt served, `human_review=1`, deterministic page **not** served | **PASS** | `test_quality_loop.py` (every terminal branch, green) | — |
| **SC-009** | Commenting flows e2e-covered on named selectors | Cite the 4b UI-test coverage of `.comment-affordance`/`.comment-pill`/…/`.comment-unplaced`/`.diff-narration` | **PASS (browser-CI)** | `cast-server/tests/ui/` | Browser-capable CI (not the autonomous run) = carry-forward |
| **SC-010** | Two real families render distinct (subsumed by SC-002) | Subsumed + exceeded by the nine-family sweep | **PASS** | `eval_family_sweep.py` (nine ⊃ two) | — |
| **SC-011** | The maker never writes canonical | `--tools ""` makes it structural; read-only-guard maker sweep + 5b full-gap-fill byte-identical extension | **PASS** | `test_fr007_readonly_guard.py` (green) | — |
| **SC-012** | Generating state converges (serves generating, swaps on `ready`) | Fake-runner route tests + the pure status-poll artifact-hash derivation | **PASS** | `test_render_route_and_service.py` (green) | Manual e2e swap = carry-forward |
| **SC-013** | Two-branch degradation surfaced, never silent | Publish-branch tests + badge injection: literal no-output → fallback; structural-gate exhaustion → flagged best attempt (`structural_violation`), never deterministic | **PASS** | `test_render_job_service.py` + `test_render_route_and_service.py` (green) | — |
| **SC-014** | Checker ≠ gate; gap amnesty | `low_quality_attempt.html` passes `check_html` but fails `derive_pass`; a `.rr-gap` page is **not** failed for a missing outcome (5b amnesty line) | **PASS** | `eval_quality_gate.py` (pinned green) + the checker amnesty clause (drift sweep §2) | Live `--live` discrimination = carry-forward |
| **SC-015** | Terminal policy = OWNER OVERRIDE, exhaustive | Every terminal branch; PREFER-VALID-THEN-SCORE; deterministic never served when any attempt exists | **PASS** | `test_quality_loop.py` (green) | — |
| **SC-016** | Human-review flag recording-only in 4a; **the LIST is 5d** | Cite the 4a recording-only coverage **and** record that 5d now adds the minimal flagged-renders list (Step 5d.3) | **PASS + 5d LIST landed** | `test_schema_migration.py` (additive columns) + `test_render_job_service.py::test_list_flagged_renders_*` (new, green) | — |
| **SC-017** | Comment survival / zero new orphans, with gap markers present | 4b survival sweep + per-class gate units; confirm green with `.rr-gap` markers on the rendered DOM (class-based, anchorable text untouched) | **PASS** | `eval_sc003_survival.py` + `test_comment_survival.py` (green) | Browser badge eyeball = carry-forward |
| **SC-018** | Narration trust boundary holds | Trust-boundary block (server-accepted == recomputed `summarize()` set; 422 all-or-nothing) + narration-API tests + schema coverage | **PASS** | `eval_sc003_survival.py` (trust block) + `test_schema_migration.py` (`version_diff_narrations`) + narration-API tests (green) | — |

**Top-level suite:** `pytest cast-server/tests/` → **1067 passed, 9 skipped, 1 failed + 1 error**. The
one failure + one error are the **two pre-existing delegation reds** (`test_child_delegation.py::
TestChildLaunchIsolation::test_launch_prompt_uses_routed_context_dir_and_runtime_output_path` and
`test_tier_delegation.py::test_mid_flight_session_isolation`), both `goal.yaml missing` environment-
fixture failures **unrelated to v3** and explicitly out of scope for 5d (do-not-touch). Every gap,
quality, survival, render-job, schema-migration, read-only-guard, and gap-reconciliation test is green.
(The 1067 includes the two new `list_flagged_renders` tests; the pre-additions run was 1065 passed.)

## SC-002 detail — the nine-family record (supersedes the 5c provisional note)

`eval_family_sweep.py` renders one **authored-not-fiction** corpus doc per LOCKED `WorkFamily` value
through the production pipeline. Every family reached terminal **`published`** (never the deterministic
`fallback` — reserved for literal no-output under the structural override — never `failed`/`superseded`),
and the nine section-heading sets are **pairwise distinct**. **6/9 clean; 3 carry HOW-layer findings.**

| family | status | served-by | human_review | score | check_html | finding |
|--------|--------|-----------|:---:|:---:|:---:|---------|
| new_initiative | published | maker | 0 | 0.90 | ✅ | clean |
| pilot_poc | published | **structural_violation** | 1 | 0.95 | ❌ | HOW invented `SC-001`/`SC-002` (0 source refs) |
| bug_fix | published | **structural_violation** | 1 | 0.90 | ❌ | FR-001/SC-001 verbatim-carriage miss + id-in-headings |
| data_analysis | published | maker | 0 | 0.95 | ✅ | clean |
| random_idea | published | maker | 0 | 1.00 | ✅ | HOW over-structured a thin doc → 2 empty shells |
| testing_qa | published | maker | 0 | 0.90 | ✅ | clean |
| refactor_migration | published | maker | 0 | 0.95 | ✅ | clean |
| personal_non_eng | published | maker | 0 | 1.00 | ✅ | clean |
| generic | published | maker | 0 | 0.90 | ✅ | clean |

**Gate model (reconciled with the structural-violation OVERRIDE):** the happy-path tier is blocking —
every family published (not fallback/failed), single self-contained file, canonical `.collab.md` never
written, pinned classification front matter valid, `check_html` green-or-flagged, pairwise distinct. A
flagged `structural_violation` publish is the **correct shipped degraded state** (best-attempt +
`human_review=1`), surfaced via the flagged-renders list (Step 5d.3) — **not** a sweep failure. The
three findings are HOW-layer communication-quality misses, **surfaced, never silently passed**.

### Gap-machinery-live finalization

The three findings are **HOW-layer** misses (`cast-requirements-how`), not WHAT-vocab or recipe-shape
defects, and not gap-machinery effects: the nine corpus docs are authored complete, so `gaps[]` is
empty-or-trivial for them and the gap stages are additive-dormant — the rendered pipeline output is
materially the Phase-3/4a behavior the 5c baseline captured, now **confirmed live under the shipped
(gap-machinery-live) pipeline**.

**Live re-run, gap machinery live — `bug_fix` (the hardest carry-forward family), 5d:** a fresh real
`claude -p` render through the production pipeline reproduced the carry-forward **exactly**:
`terminal_status=published`, `served_by=structural_violation`, `human_review=true`,
`review_reason=structural_violation`, `published_score=0.95`, `ready_hash_matches=true`,
`collab_md_unchanged=true`, `front_matter_shape_ok=true`, `check_html_passed=false` with the **same**
violations — *"FR-001 / SC-001 is not anchored to a container carrying its text (per-block correspondence
failed)"* — i.e. the verbatim-carriage miss the 5c baseline named, stable under gap-live. (Headings were
clean prose with no slot names and **no** empty sections this run; the id-in-headings symptom from the
5c pass did **not** recur — stochastic, the verbatim-carriage miss is the stable defect.) Evidence:
`build/render-jobs/.../bug_fix.result.json` (re-render scratch dir, not committed over the goldens). This
confirms the override behaves correctly gap-live: a structurally-broken best attempt is **served + flagged
+ canonical untouched**, never the deterministic page. The committed `signoff/golden/` set is the SC-002
record; re-running the **full** real-LLM nine-family sweep live is a non-blocking carry-forward (real
`claude` × 9, slow + costly; the project no-expensive-gate-in-autonomous-runs convention — static verdict
+ carry-forward, never a silent pass), with this single-family live confirmation standing in for the
hardest case.

## Integration drift sweep (Step 5d.2 — the deferred coordination notes landed)

| Drift item | Verified | Evidence |
|------------|:---:|----------|
| Reaper ceiling derives from the full stage list **incl. the gap stages** | ✅ | `reaper_ceiling_seconds()` sums `config.RENDER_STAGE_TIMEOUTS`, which registers `ask_what`/`run_gapfill`/`validate_evidence`/`emit_change_requests` — ceiling extends with **zero** formula edit |
| Heartbeats fire at **each new gap-stage** boundary | ✅ | `_heartbeat(state, "ask_what"/"run_gapfill"/"validate_evidence"/"emit_change_requests")` present in `render_job_service.py` |
| `GAPFILL_ASK_ROUNDS` ⟂ `QUALITY_MAX_WHAT_REWORKS` (A2) | ✅ | `ask_what` uses its own `GAPFILL_ASK_ROUNDS` (default 1); the in-loop WHAT-escalation reads `QUALITY_MAX_WHAT_REWORKS` (default 2) — separate counters |
| Probe `run_how` ⟂ `QUALITY_MAX_ATTEMPTS` (C6) | ✅ | the pre-loop trailer-harvest `run_how` does not increment `how_attempts`; documented in config.py + the stage comment |
| C5 knobs landed **and read** | ✅ | `config.py`: `GAPFILL_MAX_GAPS=5`, `GAPFILL_ASK_ROUNDS=1` (`CAST_*` overrides); read by the WHAT prompt cap + the `ask_what` stage (not dead config) |
| 4b seam pin: survival inside `gate_html` before `run_checker`, surfaced not silent | ✅ | `gate_html` runs `check_comment_survival`, merges in-block violations into the structural channel; survival-failing = flagged + servable under the override |
| Single `verbatim_locate` (5a evidence reuses it) | ✅ | one def in `change_request_service.py`; `validate_evidence` imports + reuses it (no second locate) |
| Single `strip_inline_markdown` | ✅ | one def in `goal_card.py`; gap code adds no second stripper |
| Single `container_text_index` | ✅ | one def in `maker_gate.py`; gap-marker correspondence reuses it |
| Checker gap-amnesty line present | ✅ | `cast-requirements-render-checker.md` GAP-AMNESTY CLAUSE (binding), reconciled with SC-014 |
| GATE-ALL applied; `change_request_service` byte-unchanged | ✅ | `config.WRITEBACK_GATE_POLICY` default `"gate-all"` (`CAST_*` override preserved); the gate/lanes/conflict/writeback/outbox/relay consumed unchanged |

Greps + the green `test_gap_reconciliation.py` / `test_render_job_service.py` / `test_maker_gate.py`
suites are the standing evidence.

## Roundtrip-spec decision (Step 5d.4 — written down, not silent)

The conditional roundtrip delta **was applied** (not deferred to a no-change rationale): render gap-fill
is the **first real downstream emitter** the roundtrip spec hard-deferred, and recording it is the honest
move. `cast-requirements-roundtrip.collab.md` v1 → **v2**: the Out-of-Scope "real emitters deferred"
fence is **narrowed** to record the one realized emitter (`render_job_service.emit_change_requests`,
`kind="addition"`, `origin_phase="render-gapfill"`), **emitter-side only** — the intake/gate/conflict/
sole-writer-apply/outbox/relay are consumed **byte-unchanged** (every roundtrip test stays green; no
intake/gate/apply contract edit). `bin/cast-spec-checker` exits 0.

## Carry-forward ledger (every flag stated; none suppressed)

**Flagged family renders (3 — the honest shipped degraded state, now on the flagged-renders list):**

1. **`bug_fix` — verbatim-carriage miss (stable) + id-in-headings (intermittent).** The fixture's
   FR-001/SC-001 bodies literally contain `**bold**`/`` `code` ``/`_emphasis_` (it is *about* markdown
   leaking); the HOW agent formats those tokens, so rendered container text no longer matches the source
   span verbatim → `check_html` per-block correspondence fails. The **verbatim-carriage miss reproduced
   in the 5d gap-live re-run** (FR-001/SC-001, score 0.95). The id-prefixed-subheadings symptom seen in
   the 5c pass did **not** recur in the 5d re-run (stochastic, not the stable defect). Fix lever:
   HOW-prompt verbatim-carriage hardening. **Routes to the principal follow-up (below).**
2. **`pilot_poc` — HOW invented success-criteria ids.** The spike doc has **zero** US/FR/SC refs; the HOW
   agent invented `SC-001`/`SC-002` labels → `check_html` "appears in render, not a source ref".
   HOW-layer fabrication discipline. **Routes to the principal follow-up.**
3. **`random_idea` — HOW over-structured a thin section → empty shells.** A single clean WHAT section was
   expanded into subsections, two left empty (an omit-never-pad / US2-S2 miss the gates did not catch:
   published `served-by: maker`, `human_review=0`, score 1.0). HOW-prompt discipline. **Routes to the
   principal follow-up.**

**Human-eyeball carry-forwards (non-blocking, autonomous-run convention):** the nine golden renders
side-by-side; the gated un-mark e2e (deleted-detail → CR → approve → regenerate → marker clears);
SC-006 unprompted commenting discoverability; the `.comment-unplaced` / "needs review" badge eyeball;
SC-009 browser-CI commenting flows; SC-004 live job-kill; SC-005 live repeat-view; SC-012 manual swap.

**Deferred (out of 5d scope, explicitly):**
- **`[USER-DEFERRED]` model-tier tune-down** for the four pipeline agents (`opus` is the confirmed
  starting tier; a tune-down review converts the knob after the loop runs e2e).
- **The human-review queue/triage UI** — the 4a open question, a future-goal owner call. The minimal
  read-only flagged-renders list is the **whole** 5d surface.
- **The v2 human timed-read evaluation** — out of scope under HOLD.

**Principal post-sign-off follow-up (owner-recorded in `decisions-so-far.md`):** the HOW-layer
**CREATE/UPDATE-mode + readability-over-verbatim rework**. The three flagged families all originate in
the HOW layer's verbatim-carriage / invented-id / padding behavior; the owner's direction is to
**plan-it-properly-first** (detail-plan, then execute as its own goal), **not** patch it inside the 5d
sign-off (5d records behavior, it does not build it). This is the single most material open item and it
is stated here, not buried.

## Disposition

Sweep complete. Sixteen criteria fully green; SC-002 green with three honestly-surfaced HOW-layer
flags; SC-016 advanced (the 5d flagged-renders list landed). The integration drift sweep confirms every
deferred coordination note landed. Both specs reconciled (`cast-requirements-render` v6→v7,
`cast-requirements-roundtrip` v1→v2; `_registry.md` bumped; `bin/cast-spec-checker` green on both). The
two delegation reds are pre-existing and out of scope. **The goal ships — with its apologies stated
explicitly: three HOW-layer flagged families, the human-eyeball carry-forwards, and the principal
CREATE/UPDATE-mode + readability follow-up — none suppressed.**

_Golden renders + a one-page index: `signoff/golden/index.html`._
