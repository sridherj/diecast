# Phase 4a — Quality-Gate Sign-off Evidence

> Written by sub-phase **4a-3** (terminal). Records the fault-injection evidence that every terminal
> branch of the quality-driven rework loop behaves per the **OWNER OVERRIDE** (decisions-so-far.md
> lines 104/107), and the calibration evidence that the LLM checker measures something the
> deterministic `maker_gate` does not. Spec of record after this sub-phase:
> `docs/specs/cast-requirements-render.collab.md` **v5** (US18, FR-037–FR-040, SC-014–SC-016).
>
> **Run mode: autonomous (no browser, no human, no live LLM).** Per the project's
> no-browser-visual-gate convention, the live-LLM half of each scenario is a **human-eyeball
> carry-forward** (recorded below, never a silent pass); the **deterministic** half is the blocking
> gate and is fully exercised here against scratch goals + throwaway `db_path` (the 1b test-bed
> discipline — never the live house DB, never a real goal's `refined_requirements.html`).

## 1. The two-gates thesis — committed fixture + the calibration eval

The load-bearing Phase-4a claim is that the **structural** gate (`maker_gate.check_html`) and the
**comprehension+visual** gate (`cast-requirements-render-checker` → `checker_verdict.derive_pass`)
measure different things. The committed fixture proves it in one artifact:

| Artifact | Structural gate | Checker gate |
|---|---|---|
| `cast-server/tests/fixtures/quality_gate/low_quality_attempt.html` | **PASS** (`check_html`) | **FAIL** (`derive_pass` False) |

The fixture is structurally clean (every id verbatim once, carriage intact, zero `id=`/anchors,
`data-goal-slug` body, real headings) but communicatively bad: no Goal Card, no job statement above
the fold, the WHAT buried under a generic wall-of-text. Its zero-click surface opens with
"Introduction and Background Information" boilerplate — a cold reader cannot state the WHAT.

`cast-server/tests/eval_quality_gate.py` (the `eval_`-prefixed harness, mirroring
`eval_render_checker.py`) runs the real checker over a calibration corpus and applies the
**production** gate by import (`derive_pass`/`canonical_score` — never a copy). Replay output (the
deterministic, no-LLM CI path):

```
=== Phase-4a quality-gate eval — per-case verdicts ===

[OK ] low_quality                  want=FAIL got=FAIL score=0.70 (blocking) struct=VALID
[OK ] gap_amnesty                  want=PASS got=PASS score=0.95 (blocking) struct=VALID
[OK ] deterministic:bug_fix        want=PASS got=PASS score=1.00 (carry-fwd)
[OK ] maker_evidence:bug_fix       want=PASS got=PASS score=0.95 (carry-fwd)
[OK ] deterministic:new_initiative want=PASS got=PASS score=1.00 (carry-fwd)
[OK ] maker_evidence:new_initiative want=PASS got=PASS score=1.00 (carry-fwd)

BLOCKING gate: PASS — low_quality MUST-fail + gap_amnesty MUST-not-fail (+ structural validity)
```

- **Blocking (deterministic):** `low_quality` MUST fail; `gap_amnesty` MUST NOT fail for a "missing
  outcome" (the revision-d amnesty clause — the `.rr-gap` marker is honest source-gap communication,
  not a render defect, protecting the Phase-5 gap contract). Pinned permanently by
  `cast-server/tests/test_eval_quality_gate.py` (4 tests, CI replay, no LLM).
- **Carry-forward ([T3]):** the per-family `deterministic`/`maker_evidence` cases expect PASS; a live
  FAIL routes to the human-eyeball channel below — never a silent pass, never a hard block. A human
  `--live` run (`eval_quality_gate.py --live --out-verdicts <file>`) exercises the full
  discriminate-both-ways gate. **Calibration discipline: below the bar the first lever is ALWAYS the
  checker prompt — never weakening the code-side gate.**

## 2. Fault-injection — every terminal branch of the loop (deterministic, scratch state)

Each scenario from the plan (US4 / SC-004 / SC-008 / the OVERRIDE broken-only branch) is exercised
end-to-end through `_execute_pipeline` with an **injected fake runner** against a scratch goal +
throwaway `db_path`. These ARE the autonomous-mode counterpart of the "live fault-injection" — the
LLM is replaced by deterministic injected verdicts so every branch is provable without network.

| Scenario | Branch proven | Test (scratch goal + throwaway db) |
|---|---|---|
| **US4 live** | quality FAIL with non-empty `rework_feedback` → rework → clean publish; CQ1 provenance-separated feedback carried verbatim | `test_quality_loop.py::test_rework_path_passes_on_second_attempt_with_verbatim_quality_feedback` |
| **SC-004 live** | LITERAL no-output (crash/empty/sentinel-failure) → deterministic `fallback`; **checker NEVER invoked** (the no-LLM path stays no-LLM) | `test_quality_loop.py::test_literal_no_output_falls_back_and_never_invokes_checker` + `test_render_job_service.py::test_no_output_serves_deterministic_fallback[crash|empty|sentinel-failure]` |
| **SC-008 live** | checker never passes, attempts structurally VALID → best-scoring VALID attempt served, `human_review=1`, `review_reason=non_convergent`; **deterministic page NOT served** | `test_quality_loop.py::test_non_convergence_publishes_best_scoring_valid_attempt_not_deterministic` |
| **OVERRIDE broken-only** | every attempt fails `gate_html` but produces extractable HTML → best **broken** attempt served, `served-by: structural_violation`, `review_reason=structural_violation`; **deterministic page NOT served** | `test_quality_loop.py::test_zero_valid_attempts_serves_best_broken_not_deterministic` |
| Prefer-valid tiebreak | a valid attempt outranks a higher-scoring broken one (PREFER VALID, THEN SCORE) | `test_quality_loop.py::test_prefer_valid_beats_higher_scoring_broken` |
| Checker-unavailable | every checker call raises → latest valid-but-unscored served, `review_reason=checker_unavailable`, never the plain page | `test_quality_loop.py::test_checker_unavailable_serves_latest_valid_attempt` |
| Ceiling / structural-stop | loop stops at exactly `QUALITY_MAX_ATTEMPTS`; early-stop at `QUALITY_STRUCTURAL_STOP` consecutive structural failures | `test_quality_loop.py::test_loop_stops_at_exactly_quality_max_attempts`, `::test_loop_early_stops_after_consecutive_structural_failures` |
| WHAT-escalation (CQ2) | 3 consecutive same-gated-token misses → one forced `run_what`; a failed re-gen retains the prior good WHAT, budget still decremented, no fallback | `test_quality_loop.py::test_what_escalation_reruns_what_after_three_consecutive_missing_token`, `::test_what_escalation_gate_failure_retains_prior_what` |

Full run: **49 passed** across `test_quality_loop.py` (11), `test_checker_verdict.py` (17),
`test_render_job_service.py` (17), `test_eval_quality_gate.py` (4):

```
uv run --project cast-server python -m pytest \
  cast-server/tests/test_quality_loop.py cast-server/tests/test_checker_verdict.py \
  cast-server/tests/test_render_job_service.py cast-server/tests/test_eval_quality_gate.py
# 49 passed
```

The OVERRIDE is baked in and pinned: the deterministic page is served **only** on a literal
no-output failure; any extracted attempt is scoreable, servable, and flagged — never the silent swap.

## 3. Human-eyeball carry-forward (the standing, non-blocking channel)

These are recorded for a human pass; per the no-browser-visual-gate convention they **never block** an
autonomous run and are **never** silently marked pass:

1. **`--live` discrimination run** of `eval_quality_gate.py` over the calibration corpus (real opus
   checker): confirm the per-family `deterministic`/`maker_evidence` cases PASS and `low_quality`
   FAILs. If a 1a-evidence case FAILs live, the first lever is the checker prompt
   (`cast-requirements-render-checker.md`), never the code-side gate.
2. **Browser eyeball** over one **flagged** publish (`served-by: structural_violation` / "needs review"
   badge) and one **converged** clean publish (`served-by: maker`), confirming the reader-visible flag
   surfaces and the converged page reads as a customer-grade artifact.

## 4. Scope confirmation (recording-only)

4a ships the human-review flag as the four `render_jobs` columns + the served-artifact envelope stamp
+ the status-JSON exposure — **recording only**. The **flagged-renders LIST** (slug, reason, score,
link, on an existing screen) is **Phase 5d** (owner-resolved 2026-06-12); building it here would be
silent scope drift. No review dashboard, no diff/reanchor surface, no gap-fill upstream ask was built.
