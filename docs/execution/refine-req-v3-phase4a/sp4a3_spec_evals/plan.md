# Sub-phase 4a-3: The Spec Records the Gate and Fault-Injection Proves Every Branch

> **Pre-requisite:** Read `docs/execution/refine-req-v3-phase4a/_shared_context.md` before starting.
> This sub-phase records the **OWNER OVERRIDE** into the spec — the FR-006 text must reflect the
> override, NOT the source plan's RATIFIED fork.

## Objective

`cast-requirements-render.collab.md` records the checker contract, the quality-driven rework loop,
the ceiling, and the **precise two-branch fallback policy AS OVERRIDDEN**. A live eval harness
(`eval_quality_gate.py`, `eval_` prefix so pytest never collects it) proves the checker
discriminates and the loop converges on a real document. The three high-level verification scenarios
(US4, SC-004, SC-008) are demonstrated live and recorded. The 4b/5 hand-off notes are updated. 4a
ships the human-review flag **recording-only** — the flagged-renders LIST is Phase 5d.

## Dependencies

- **Requires completed:** 4a-1 (`checker_verdict.py` + the checker agent) AND 4a-2 (the loop + the
  flag columns + the status surface). This is the terminal sub-phase.
- **Assumed codebase state:** `parse_verdict`/`derive_pass`/`canonical_score` importable; the loop +
  policy table live in `render_job_service`; the four flag columns + status `human_review` exist;
  `eval_render_checker.py` is the shape to mirror.

## Scope

**In scope:**
- The committed low-quality fixture (`cast-server/tests/fixtures/quality_gate/low_quality_attempt.html`).
- `cast-server/tests/eval_quality_gate.py` (live discriminate + converge harness; gate functions
  imported from production, not copied; gap-amnesty fixtures included).
- Run the three live fault-injection scenarios (US4 / SC-004 / SC-008) against a **scratch goal +
  throwaway `db_path`** (the 1b test-bed discipline) and record results as the Phase-4a gate evidence.
- The checker calibration gate over the eval corpus.
- → `/cast-update-spec` on `cast-requirements-render.collab.md` (inline approval gate).
- 4b/5 hand-off notes in the goal dir.

**Out of scope (do NOT do these):**
- Do NOT modify `render_job_service.py`, `checker_verdict.py`, or the checker agent — 4a-1/4a-2 own
  them; 4a-3 only exercises and records them.
- Do NOT build a flagged-renders list / review UI — that is **Phase 5d** (owner-resolved). 4a is
  recording-only.
- Do NOT weaken the code-side gate to make calibration pass — the **first lever is always the
  checker prompt** (the `eval_render_checker.py` discipline).
- Do NOT run any live LLM in default CI — live scenarios are `eval_`-prefixed and scratch-only.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/fixtures/quality_gate/low_quality_attempt.html` | Create | Does not exist |
| `cast-server/tests/eval_quality_gate.py` | Create | Does not exist |
| `cast-server/cast_server/specs/.../cast-requirements-render.collab.md` (via `/cast-update-spec`) | Modify | Draft v3 after Phase 3e |
| `docs/specs/_registry.md` | Modify (via the skill) | Has the render-spec row |
| 4b/5 hand-off notes (goal dir) | Modify | Extends 3e's hand-off |
| Phase-4a gate evidence (goal dir) | Create | Does not exist |

## Detailed Steps

### Step 4a3.1: Author the low-quality fixture

`low_quality_attempt.html`: structurally **VALID** (passes `maker_gate.check_html` — ids verbatim,
carriage intact, DOM contract clean) but communicatively **bad** (WHAT buried below the fold,
wall-of-text, generic undifferentiated layout). The fixture proves the two gates measure different
things — the whole Phase-4a thesis. It MUST fail the checker (`derive_pass` False) while passing the
structural gate.

### Step 4a3.2: Build `eval_quality_gate.py`

Mirror the `eval_render_checker.py` shape (`--live`, `--verdicts` replay, `--out-verdicts`; per-case
report; binary gate per case). Cases = the calibration corpus: Phase-1a maker-evidence HTML (per
family), the v2 deterministic render, and the low-quality fixture. **The harness reuses
`checker_verdict.derive_pass` / `canonical_score` by IMPORT** — eval and production share one gate
implementation, never a copy.

**Gap-amnesty fixtures (owner edit, revision d):** include at least one eval case whose HTML carries
a `.rr-gap` marker (a question + fixed status vocabulary). Assert the checker does NOT fail it for a
"missing outcome" — the gap is honest communication, not a comprehension defect. This pins the
gap-amnesty clause from the 4a-1 prompt at the eval layer so the Phase-5 gap contract is protected.

### Step 4a3.3: The checker calibration gate

Over the eval corpus, the checker PASSES the 1a evidence (or its failures are judged legitimate on
human review) and FAILS the low-quality fixture. If it cannot discriminate, **the first lever is the
checker prompt, never weakening the code-side gate.**

**[T3] Autonomous-mode handling:** the "judged legitimate on human review" branch cannot execute in
an autonomous (no-browser, no-human) run. In that mode a 1a-evidence FAIL is recorded as a
**human-eyeball carry-forward item** (never a silent pass, never a hard block — the project's
no-browser-visual-gate convention). The only **blocking** half of the calibration gate in autonomous
mode is the **low-quality-fixture MUST-fail** assertion, which is fully deterministic. A human-run
eval still exercises the full discriminate-both-ways gate.

### Step 4a3.4: Run the three live fault-injection scenarios

Against a scratch goal + throwaway `db_path` (never the live house DB, never a real goal's
`refined_requirements.html`); record results + artifacts in the goal dir as the Phase-4a gate
evidence:

- **US4 live:** feed the committed low-quality fixture through the real checker → FAIL verdict with
  non-empty `rework_feedback`; feed that feedback + fixture into a real HOW rework → improved
  attempt. (CI keeps the deterministic fake-runner equivalent from 4a-2.)
- **SC-004 live:** fault-inject a no-output maker (env-killed subprocess / forced timeout via config)
  → deterministic page served, `status=fallback`.
- **SC-008 live:** force the checker to never pass (a test-only always-fail checker prompt injected
  through the `AgentRunner` seam) → best attempt served, `human_review=1`, deterministic page **NOT**
  served.
- **OVERRIDE live (record it):** also exercise the broken-only terminal — force every attempt to fail
  `gate_html` while still producing extractable HTML → best **broken** attempt served,
  `review_reason='structural_violation'`, deterministic page NOT served. This is the live counterpart
  of 4a-2's load-bearing override test; record it in the gate evidence.

### Step 4a3.5: Record the spec via `/cast-update-spec`

→ **Delegate: `/cast-update-spec`** on `cast-requirements-render.collab.md` with these deltas
(**review the diff before approval**, per the skill's gate):

1. **The maker-path quality gate:** `cast-requirements-render-checker` (verdict schema verbatim from
   4a-1; subagent bare-JSON carve-out, sibling of FR-011) gates every maker publish; the binary PASS
   rule is computed code-side (`checker_verdict.py`) — `can_state_what` + gated `missing[]` tokens +
   zero error-severity issues; the score float never gates; canonical score recomputed from issue
   counts.
2. **The quality-driven rework loop:** rework-until-bar with provenance-tagged feedback through the
   violations channel; WHAT-escalation; `QUALITY_MAX_ATTEMPTS` as the only loop bound, recorded
   explicitly as the **owner-sanctioned anti-infinite-loop ceiling, NOT a cost cap**; attempt
   artifacts under `RENDER_JOBS_DIR`.
3. **The two-branch fallback policy — AS OVERRIDDEN (record the override, NOT the source plan's
   RATIFIED fork):** the deterministic page is served **ONLY on a literal no-output failure** (crash
   / timeout / nothing produced); a **structurally-broken-but-present** attempt is **scoreable and
   servable**, flagged `structural_violation` + `human_review` — **never** the deterministic page;
   non-convergence with valid attempts → best-scoring valid attempt + `non_convergent` flag;
   checker-unavailable → latest valid attempt + `checker_unavailable` flag. Record the
   **surface-don't-suppress** rationale and the prefer-valid tiebreak.
4. **`render_jobs` columns + status surface:** `human_review`/`review_reason`/`published_attempt`/
   `published_score` (the four added by 4a-2; `heartbeat_at` is Phase 3's); status JSON exposes
   `human_review` **read from the served-artifact envelope** (A2), with the columns the queryable
   observability copy.
5. **Verification layer (FR-009):** the happy-path gate is the LLM-judged comprehension+visual check
   (completing the seam 3e left as "recorded as Phase-4a scope"); the deterministic golden-HTML
   snapshot gate continues to cover the fallback substrate + cache envelope (SC-002 as narrowed by
   3e — restated, not re-narrowed); SC-001's cold-reader criterion is now satisfied on the maker path
   by the new checker (the v2 `cast-requirements-checker` + `eval_render_checker.py` remain the
   deterministic-substrate gate, unmodified).
6. **`linked_files` appended:** the checker agent dir, `checker_verdict.py`, `eval_quality_gate.py`,
   the low-quality fixture.

### Step 4a3.6: Spec checker + registry

After the spec edit: `bin/cast-spec-checker` green on the updated spec; `docs/specs/_registry.md`
row bumped (the skill handles the version/date bump).

### Step 4a3.7: 4b/5 hand-off notes

Update the 4b/5 hand-off notes in the goal dir (extending 3e's):
- the flag lives on `render_jobs` + the status JSON + the served-artifact envelope; anything 4b's
  regenerate flow publishes follows the same policy table (and a survival-failing attempt is a
  structural violation under the OVERRIDE — scoreable/servable + flagged, in-block misses surface as
  4b's unplaced badges; C3 merge note);
- **Phase 5d adds the flagged-renders LIST** (slug, reason, score, link, on an existing screen) +
  the gap stages register in the stage-timeout list; Phase 5's nine-family sweep runs each family
  render through the full loop and reads `human_review` as its per-family quality signal.

## Verification

### Automated Tests (permanent)

- `eval_quality_gate.py` runs in **replay mode** (`--verdicts`) in CI without an LLM and asserts the
  per-case binary gate (incl. the low-quality MUST-fail and the gap-amnesty MUST-not-fail cases).
- `bin/cast-spec-checker` green on the updated `cast-requirements-render.collab.md`.

### Validation Scripts (temporary)

- `eval_quality_gate.py --live` over the calibration corpus → discrimination report (live LLM,
  human/scratch only).

### Manual Checks

- → **Delegate: `/cast-update-spec`** — review the diff covers all six deltas, **the FR-006 text
  reflects the OVERRIDE** (literal-no-output-only; structurally-broken servable+flagged), and the
  version/date/registry bump landed.
- Human-eyeball browser pass over one flagged-publish and one converged-publish recorded as the
  standing carry-forward item (visual gates never block autonomous runs) — the same carry-forward
  channel the T3 calibration-failure case feeds into.
- Confirm the live fault-injection ran against scratch state only (no live house DB, no real goal's
  `refined_requirements.html` touched).

### Success Criteria

- [ ] Low-quality fixture: structurally valid, checker-failing — committed and asserted in the eval.
- [ ] `eval_quality_gate.py` imports the production gate functions; CI replay green; gap-amnesty
      case asserts the `.rr-gap` page is NOT failed for "missing outcome".
- [ ] Calibration gate: low-quality MUST-fail is the deterministic blocking half; 1a-evidence FAIL
      routes to human-eyeball carry-forward in autonomous mode (T3).
- [ ] US4 / SC-004 / SC-008 **+ the OVERRIDE broken-only branch** demonstrated live and recorded in
      the goal dir as the Phase-4a gate evidence.
- [ ] `/cast-update-spec` recorded all six deltas with the **FR-006 text reflecting the OVERRIDE**;
      `bin/cast-spec-checker` green; registry row bumped.
- [ ] 4b/5 hand-off notes updated; the flagged-renders LIST explicitly deferred to Phase 5d.

## Execution Notes

- **Record the OVERRIDE in the spec, not the source plan's RATIFIED fork.** The source plan's
  FR-006/Fork-Resolution prose pre-dates the owner override (`decisions-so-far.md` 104/107). The
  spec must record the override: deterministic only on literal no-output; structurally-broken
  servable + flagged. If `/cast-update-spec` proposes the old RATIFIED text, correct the delta before
  approving.
- **The eval and production share ONE gate.** Import `derive_pass`/`canonical_score`; a second copy
  is drift by construction (the `eval_render_checker.py` discipline).
- **Calibration failure routes to the prompt, never to gate-weakening** — record this in the eval
  docstring exactly as `eval_render_checker.py` does.
- **Recording-only:** 4a ships the flag + envelope stamp + status exposure. The flagged-renders LIST
  is Phase 5d (owner-resolved 2026-06-12) — building it here is silent scope drift.
