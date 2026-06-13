# Phase 4b → Phase 5 / Reconciliation Hand-off

> Written by sub-phase **4b-4** (terminal Phase-4b sub-phase). Phase 4b is **complete**: the
> comment-survival gate (4b-1), the `cast-comment-reanchor` contract v2 + refine-loop wiring (4b-2),
> the diff-narration store/API/render (4b-3), and this sub-phase's spec landing (v6) + SC-003 e2e
> proof. Spec of record: `docs/specs/cast-requirements-render.collab.md` **v6**.

## What Phase 4b shipped (the seams Phase 5 consumes)

1. **`check_comment_survival`** (pure, `requirements_render/maker_gate.py`) — `(html, parsed,
   comments) -> SurvivalReport{passed, violations, unplaced, placed}`. Reuses the single
   `container_text_index` walker + `strip_inline_markdown` (no copy). In-block vs cross-boundary
   classification retained; only in-block misses are `violations`.
2. **`gate_html` widened** (`services/render_job_service.py`) — fetches OPEN comments at stage entry
   (re-read per attempt, Decision #9), runs the survival gate, writes
   `build/render-jobs/{slug}/{hash12}/survival.json`, and merges **in-block** violations into the
   **same** `state.html_report.violations` structural channel.
3. **`.comment-unplaced` tray badge** — read-time, derived (`static/requirements_comments.js`
   toggles it on a tray item whose `highlight()` returned `false`); covers both miss classes;
   nothing stored.
4. **`cast-comment-reanchor` contract v2** — backward-compatible superset (optional `change_set` +
   per-comment block context inputs, a `narration` output, the third `resolved` verdict). Legacy
   `{comments, old_content, new_content}` calls are byte-identical to v1. Model tier unchanged
   (`sonnet`); still the bare-JSON subagent carve-out.
5. **Diff narration** — `version_diff_narrations` table + `requirement_version_service.save_narration`
   / `get_narration`; the same-door `POST …/versions/{head}/narration`; `GET …/changes` gains a
   `narration` sibling while `counts`/`items` stay byte-for-byte `summarize()`; the
   `changes_panel.html` panel attaches notes by `(change, heading_or_ref)` and renders via the
   autoescaped template only.

## For Phase 5 (round-trip writeback)

- **The narration POST is the surface Phase 5's round-trip summaries may reuse.** A reconciliation
  round-trip that cuts a version can post a `summarize()`-validated narration through the same
  `POST …/versions/{head}/narration` door — no new surface needed.
- **The writeback dispatch site stays verdicts-only.** `cast-requirements-writeback` /
  `cast-requirements-roundtrip.collab.md` use the `cast-comment-reanchor` verdicts-only call shape;
  contract v2 leaves that byte-valid by construction (every v2 input optional). At reconciliation the
  writeback site **MAY** adopt the `change_set` + block-context inputs (and consume `narration`) — an
  additive opt-in, not a required migration. `cast-requirements-roundtrip.collab.md` was **not
  modified** by Phase 4b (consumed, not modified).

## ⚠️ `render_job_service.py` merge contract (4a + 4b both touched this file) — C3 confirmed coherent

Both Phase 4a-2 and Phase 4b-1 widened `render_job_service.py` on **disjoint** seams; the merge is
**already landed and confirmed coherent** this sub-phase:

- **4b-1** widens `gate_html`'s report (the survival merge).
- **4a-2** inserts `run_checker → decide_quality` **after** `gate_html` in the quality loop.

The live stage order (`_execute_pipeline` → `_quality_loop`) is:

    run_what → gate_what → run_how → gate_html → run_checker → decide_quality → publish

with each rework iteration `run_how → gate_html → run_checker`, then `decide_quality`.

**The override-era ordering contract any future merge MUST preserve:**

- **Survival is evaluated inside the structural gate (`gate_html`), BEFORE `run_checker` scores an
  attempt.** `structurally_valid = state.html_report.passed`, so an in-block survival miss (merged
  into `html_report.violations`) makes the attempt structurally-invalid and the loop treats it as a
  rework candidate.
- **DECISION #10 OVERRIDE (binding):** a survival-failing attempt is a **flagged, servable**
  structural state — it is part of the *surfaced* report `decide_quality` ranks (PREFER VALID, THEN
  SCORE), **not** a disqualifier and **not** a publish-block. On structural-gate exhaustion the best
  attempt is served `human_review=1`, `review_reason='structural_violation'`, `served-by:
  structural_violation` — **never** the deterministic page.
- **The deterministic `render_requirements()` fallback fires ONLY on literal no-output** (WHAT
  produced no doc / per-attempt extraction failure / thread crash). There is **no** survival→block
  and **no** survival→deterministic-fallback path. A future merge that re-introduces either would
  violate the owner override.

## Carry-forwards (non-blocking)

- **Human-eyeball browser pass** over the `.comment-unplaced` tray badge + the `.diff-narration`
  panel (autonomous runs cannot drive a browser). Detail in `phase4b-sc003-evidence.md`.
- **Live `cast-comment-reanchor` v2 verdicts** (the `relocated`/`resolved`/`orphaned` decision + the
  `narration` authoring) — the agent eval gate `tests/eval_reanchor.py` covers the contract; a live
  end-to-end reanchor over a real displaced set is the human carry-forward. (The deterministic
  application of verdicts through the same-door services is proven by SC-003 Block 2.)

## State

- Spec `cast-requirements-render.collab.md` at **v6**; `bin/cast-spec-checker` green; `_registry.md`
  row bumped to v6.
- SC-003 e2e: deterministic blocking gate GREEN (`eval_sc003_survival.py`, 3 blocks); the live `claude
  -p` maker render also ran GREEN this session (carry-forward corroboration).
- Default CI: `pytest cast-server/tests/test_*.py` → **961 passed**. The 2 pre-existing delegation
  reds are outside this sweep and were not touched.
