# Sub-phase Extracts — refine-requirements-better-rendering-v3 fan-out planning

Compact per-sub-phase summaries for the reconciliation pass. Source plans in
`docs/plan/2026-06-12-refine-requirements-v3-phase*.md`. Phase 5 extract appended when its
child completes. (Named `_v3_subphase_extracts.md` to avoid colliding with the existing
`_subphase_extracts.md` from the product-revamp-diecast run.)

## Phase 1: Validate the Maker & the Anchor Backbone (spikes)

### Files Created
- `docs/goal/refine-requirements-better-rendering-v3/spikes/1a/spike-results.md`, `spikes/1b/spike-results.md`, `spikes/PHASE1-GATE.md` (evidence; away from CI collection)

### Files Modified
- None (spike phase; hand-run generation, no production code)

### Key Interfaces Produced
- Python re-implementation of `requirements_comments.js` tree-walk + `indexOf` mark-placement semantics (the "1b harness") — later productionized by Phase 3's maker_gate and shared with 4b
- "Clearly beats" rubric: checker pass + rubric majority + zero gate regression + human-eyeball carry-forward

### Naming Choices
- Spike evidence dirs `spikes/{1a,1b}/`; gate doc `PHASE1-GATE.md`

### Config Changes
- None

### Cross-Sub-Phase Dependencies
- Produces: validated quote-anchored logical backbone; the verbatim-carriage obligation (forwarded to Phase 3 spec work); mark-placement harness semantics (consumed by 3b, 4b-1)
- Assumes: nothing prior

### Suggested Revisions to Prior Sub-Phases
- Sharpening only: orphan risk reworded — DB orphaning impossible from render variation (source-side validation); real exposure = silent `<mark>`-placement loss + unspec'd verbatim-carriage; Phase 3 must spec the verbatim-carriage clause. No decision overturned.

## Phase 2: Discoverable Commenting & an Honest Fallback

### Files Created
- `cast-server/tests/test_goal_card.py` (if not present; defect regression tests)

### Files Modified
- `cast_server/requirements_render/goal_card.py` — new pure `strip_inline_markdown` helper; `_split_first_sentence` (token-set abbreviation scan) replaces bare `_SENTENCE_END_RE` split
- `cast_server/requirements_render/renderer.py` — scope-grid path applies strip at production point
- `static/requirements_comments.js` — JS-injected affordance into `.rr-controls` (teach + surface: reveal tray, pulse gesture hint)
- `requirements_render/templates/_theme.css.j2` — affordance CSS beside `.comment-*` rules
- Golden HTML fixtures — ONE gated regeneration (sub-phase 2c), not per-sub-phase

### Key Interfaces Produced
- `strip_inline_markdown` (pure, in goal_card.py) — consumed by Phase 3's maker_gate anchorable-text derivation; must stay import-stable
- `_split_first_sentence` — internal

### Naming Choices
- Strip not convert; affordance JS-injected not template-rendered (FR-028 progressive enhancement)

### Config Changes
- None

### Cross-Sub-Phase Dependencies
- Produces: `strip_inline_markdown` (hard dependency of 3b); hardened deterministic fallback substrate
- Assumes: nothing prior (parallel with Phase 1)

### Suggested Revisions to Prior Sub-Phases
- None

## Phase 3: The WHAT→HOW Maker Pipeline (sub-phases 3a–3e)

### Files Created
- `agents/cast-requirements-what/` + `agents/cast-requirements-how/` (net-new agents + config.yaml)
- `cast_server/services/render_job_service.py` (background job: tool-free `claude -p` subprocesses, `--tools ""`; in-memory single-flight + per-job daemon thread)
- `cast_server/requirements_render/maker_gate.py` (pure structural gate: id parity, per-block correspondence, verbatim carriage via 1b harness + strip_inline_markdown, DOM/self-containment)
- `requirements_render/templates/generating.html.j2` (generating state; 4s poll + reload; `<noscript>` meta-refresh; stale-render-with-banner)
- `render_jobs` DB table (observability, failure reasons, 4a flag seam)
- `build/render-jobs/` job artifacts dir

### Files Modified
- `routes/pages.py` (render route → generating state on cache miss), `services/requirements_render_service.py` (orchestrator seam: maker primary, render_requirements() fallback), `cast_server/config.py` (`RENDER_JOBS_DIR`, stage timeouts)

### Key Interfaces Produced
- WHAT-doc contract: markdown body + YAML front matter (total id-mapping, `unmapped_refs`, reserved `gaps[]` for Phase 5)
- HOW output: self-contained HTML between sentinels, archetype-library-driven
- Stage order in render_job_service with reserved seam for 4a checker between gate_html and publish
- Readiness derived from artifact-embedded `source-hash` (v2 cache IS the state)

### Naming Choices
- `cast-requirements-what`, `cast-requirements-how`, `maker_gate.py`, `render_job_service.py`, `render_jobs`, `RENDER_JOBS_DIR`

### Config Changes
- `RENDER_JOBS_DIR`, per-stage timeouts in `cast_server/config.py`; reaper ceiling derived from config (see 4a revision)

### Cross-Sub-Phase Dependencies
- Assumes: Phase 1 gates pass; Phase 2's strip_inline_markdown import-stable
- Produces: pipeline + seams for 4a (checker slot, render_jobs), 4b (WHAT-doc id-mapping, verbatim-carriage guarantee, container-text walker), Phase 5 (gaps[])
- Policy: structurally-unusable output = no-output branch → deterministic fallback after ONE bounded structural retry (flagged → ratified+sharpened by 4a)

### Suggested Revisions to Prior Sub-Phases
- None (one coordination note: strip_inline_markdown dependency import-stability)

## Phase 4a: The Quality Gate — Checker & Rework Loop (sub-phases 4a-1..4a-3)

### Files Created
- `agents/cast-requirements-render-checker/` (one agent, comprehension + visual one pass; input = rendered artifact + family label ONLY)
- `cast_server/requirements_render/checker_verdict.py` (binary PASS + canonical score computed code-side)
- `eval_quality_gate.py` (mirrors eval_render_checker.py conventions)
- `attempt-N.verdict.json` artifacts under build/render-jobs/

### Files Modified
- `render_job_service.py` (loop: gate_html → run_checker → decide_quality → publish; WHAT-escalation), `cast_server/config.py` (knobs), `render_jobs` migration (flag columns + heartbeat_at)

### Key Interfaces Produced
- Verdict = strict superset of v2 SC-001 cold-reader shape (can_state_what + missing[], binary PASS, never agent-side score)
- Terminal-state policy table; flag columns: `human_review`, `review_reason`, `published_attempt`, `published_score`, `heartbeat_at`; flag also stamped in served-artifact envelope beside source-hash (single read-path source of truth)

### Naming Choices
- `QUALITY_MAX_ATTEMPTS=15`, `QUALITY_MAX_WHAT_REWORKS=2`, `QUALITY_STRUCTURAL_STOP=3` in config.py

### Config Changes
- The three knobs above; reaper ceiling formula extended (see revisions)

### Cross-Sub-Phase Dependencies
- Assumes: Phase 3's seam + render_jobs + maker_gate; Phase 1 rubric
- Produces: quality gate; FORK RATIFIED + SHARPENED — no-output classification applies ONLY while zero structurally-valid attempts exist; once one exists, non-convergence serves best-scoring VALID attempt + flag, never the plain page; checker-unavailable = latest valid attempt + flag; deterministic fallback page never LLM-gated

### Suggested Revisions to Prior Sub-Phases
- **Phase 3 (correction):** reaper ceiling must derive from the configured stage list (loop makes worst case ~10× larger); reaper must release the in-flight semaphore slot of a reaped orphan; per-job thread writes `heartbeat_at` at stage boundaries (heartbeat = detector, ceiling = backstop)

## Phase 4b: Comments & Versions Survive the Maker (sub-phases 4b-1..4b-4)

### Files Created
- `tests/eval_reanchor.py`; survival tests (test_block_diff.py/test_diff_render.py extended)

### Files Modified
- `maker_gate.py` (+ pure `check_comment_survival`; open comments fetched at gate_html stage entry, re-read per attempt)
- `agents/cast-comment-reanchor/` → CONTRACT V2 (extend in place, NOT replace: narrate + resolve at version boundary; all new inputs optional; orphan-over-guess + 422 backstop carry untouched; verdict order relocated > resolved > orphaned-when-unsure)
- `routes/api_requirements.py` (narration POST, all-or-nothing 422, upsert per (goal_slug, base, head)), `/changes` JSON (+ sibling `narration` key; byte-for-byte guarantee re-scoped to counts/items)
- `static/requirements_comments.js` + `_theme.css.j2` (read-time `.comment-unplaced` tray badge, derived, nothing stored)
- `schema.sql` (narration storage)

### Key Interfaces Produced
- Survival gate semantics: in-block placement misses = STRUCTURAL violations (inherit retry-then-fallback); cross-boundary quotes never block (tray surfacing)
- SEAM PIN: survival evaluated INSIDE the structural gate BEFORE 4a's run_checker — a survival-failing attempt is structurally INVALID (never "best-scoring valid")
- Narration posted same-door by the parent that cut the version; server never dispatches LLM on version path

### Naming Choices
- cast-comment-reanchor kept (contract v2), not renamed; `.comment-unplaced` badge; `SurvivalReport` in job artifacts

### Config Changes
- cast-comment-reanchor config.yaml (contract v2 inputs)

### Cross-Sub-Phase Dependencies
- Assumes: Phase 3 verbatim-carriage + WHAT-doc id-mapping + container-text walker; Phase 1b harness semantics
- Produces: survival contract consumed by 4a's structural gate; block_diff/diff_render NOT modified (extend-never-fork)

### Suggested Revisions to Prior Sub-Phases
- None that change a decision. Coordination: (1) Phase 3's 3b must expose its container-text walker as a shared helper — hard no-copy prerequisite for 4b-1; (2) 4a's loop treats the widened gate_html report (carriage + survival) as the structural gate it wraps

## Phase 5: Gap-Filling, Cross-Family Hardening & Sign-Off (sub-phases 5a–5d)

### Files Created
- `agents/cast-requirements-gapfill/` (net-new tool-free helper; grounded-or-refuse)
- `cast-server/tests/fixtures/family_corpus/` (nine-family corpus); goal `signoff/` evidence dir

### Files Modified
- `render_job_service.py` (gap stages: ask_what re-run, run_gapfill, validate_evidence/emit_change_requests — once per job, BEFORE the 4a loop)
- `maker_gate.py` (gap-marker extensions), WHAT contract (`gaps[]` entry schema), HOW contract (optional `GAPS-DETECTED` trailer outside sentinels)
- Gap CR emission via `change_request_service.create` directly (gate consumed unchanged)

### Key Interfaces Produced
- Gap contract: page renders question + fixed status vocabulary only (`.rr-gap` class, no id=); proposed_body never pre-approval; dedupe `#gap=<fp12>` on origin_artifact_path
- Grounding allowlist: the goal's own upstream artifacts only

### Naming Choices
- `cast-requirements-gapfill`, `GAPFILL_ASK_ROUNDS` (independent of QUALITY_MAX_WHAT_REWORKS), `.rr-gap`, `family_corpus/`

### Config Changes
- `GAPFILL_ASK_ROUNDS`; gap stages join the reaper-ceiling stage list

### Cross-Sub-Phase Dependencies
- Assumes: Phase 3 gaps[] seam + sentinel extraction; 4a loop + checker; 4b narration NOT adopted (deliberately closed); roundtrip gate unchanged
- Produces: SC-001..SC-008 sweep + final spec reconciliation (5d)

### Suggested Revisions to Prior Sub-Phases
- 4a checker prompt: gap-amnesty clause (additive, required — loop would fight gap contract)
- Phase 3/4a reaper formula + heartbeat: include the three gap stages
- Phase 3 HOW contract: GAPS-DETECTED trailer at the reserved seam (additive)
- Residual taste call surfaced: global gate policy for gap CRs (gate-except-additions default vs gate-all)
