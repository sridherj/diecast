# Shared Context: refine-req-v3-phase4a (The Quality Gate — Checker & Quality-Driven Rework Loop)

> Read this file at session start before executing any sub-phase plan in this project.

## Source Documents

- **Plan (authoritative):** `docs/plan/2026-06-12-refine-requirements-v3-phase4a-quality-gate.md`
- **Reconciliation report:** `docs/plan/2026-06-12-refine-requirements-v3-reconciliation.md`
- **Decisions-so-far (binding owner decisions):** `docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md`
- **Phase-3 execution context (the seams 4a plugs into):** `docs/execution/refine-req-v3-phase3/_shared_context.md`
- **Phase-1 carry-forwards (judge anomalies, calibration corpus):** `docs/goal/refine-requirements-better-rendering-v3/spikes/1a/spike-results.md`

## Project Background

On the happy path, no maker render reaches a reader unless `cast-requirements-render-checker` —
**ONE** thorough agent grading comprehension **and** visual quality in a single pass (the owner
explicitly rejected a multi-checker coordinator) — passes it. The checker drives a
**quality-driven rework loop** inside Phase 3's `render_job_service`, inserted between `gate_html`
and `publish` at the stage seam Phase 3 reserved: the loop reworks until the comprehension bar is
met, guarded only by a HIGH anti-infinite-loop safety ceiling — **loops are never rationed by cost,
latency, or model tier** (owner decision, binding).

The shaping insight (the trust boundary): Phase 3's deterministic `maker_gate` owns **fidelity to
the source** (id parity, verbatim carriage, DOM contract — everything whose failure means silent
data loss); the LLM checker owns **the reader's experience** (can a cold reader state the WHAT; does
the page look like something you'd show a customer). The checker therefore judges only the rendered
artifact + family label — **never the canonical source, never the WHAT doc** — staying the
unfamiliar reader that made SC-001's cold-reader verdict trustworthy in v2.

## ⚠️ OWNER OVERRIDE — supersedes the source plan's "Fork Resolution: RATIFIED" section

**This is the single most important deviation from the source plan. The plan document
(`§Fork Resolution`, `§Decisions Made Autonomously #4`, the policy table's last two rows, and the
Key Risks/Spec-delta text) is written around the older RATIFIED fork (structural violations →
deterministic fallback). That is SUPERSEDED.** Authority: `decisions-so-far.md` lines 104, 107
(owner override, 2026-06-12) + the reconciliation. Implement the OVERRIDE, not the plan's text:

- **The deterministic page is served ONLY on a LITERAL no-output failure** — crash, timeout, or
  nothing produced/extractable at all. This matches FR-006's letter exactly.
- **A structurally-broken-but-present attempt is SCOREABLE and SERVABLE.** It goes through the
  checker like any other attempt and gets a canonical score; at terminal it can be served, flagged
  `structural_violation` + `human_review=1`. The deterministic page is **NEVER** served when any
  attempt was produced.
- **Comment-mark misses must surface visibly, never silently drop.** "Never SILENTLY drop" still
  binds — the degradation is *surfaced* (flag columns + `served-by` envelope stamp + the
  reader-visible badge Phase 3d already derives), not hidden. (Extending 4b's read-time
  `.comment-unplaced` tray badge to in-block misses is a **4b** concern — noted here for the C3
  merge, not built in 4a.)
- **Guiding principle (owner, 2026-06-12): surface, don't suppress.** Prefer the visible-degraded
  state with machine-readable context over the silent-safe swap. Apply it to any future fork of the
  same shape.

**Terminal best-attempt ranking (owner-confirmed for this split, 2026-06-12): PREFER VALID, THEN
SCORE.** At non-convergence, serve the **best-scoring structurally-VALID attempt** (flag
`non_convergent`); fall to the **best-scoring structurally-BROKEN attempt** (flag
`structural_violation`) **only when no structurally-valid attempt exists**. This preserves comment
anchoring whenever possible while still never serving the deterministic page when any attempt
exists. (A structurally-broken attempt can therefore never outrank a valid one purely on score.)

## Operating Mode

**HOLD SCOPE.** `refined_requirements.collab.md` front matter pins `scope_mode: hold`. Owner
decisions in `decisions-so-far.md` are binding and not re-opened. Out of scope (4b/5 territory):
the diff/comment-resolution agent, `block_diff`/reanchor surfaces, gap-fill upstream asks
(`gaps[]` stays a dormant seam), and any human-review **queue/list UI** (4a ships
**recording-only**: flag columns + envelope stamp + status-JSON exposure; the flagged-renders LIST
is **Phase 5d**, owner-resolved 2026-06-12). Building a review dashboard in 4a is silent scope drift.

## Codebase Conventions

- **Pure module vs. service split.** `cast_server/requirements_render/` is pure (no I/O, no DB, no
  LLM). The new `checker_verdict.py` joins the **pure** package beside `maker_gate.py` (same
  no-I/O discipline). All subprocess/DB/orchestration work stays in `render_job_service.py`
  (service layer).
- **The gate is code-owned, never trusted from the agent.** `derive_pass` and `canonical_score`
  live in `checker_verdict.py` and are computed code-side — the FR-010 "the gate is the boolean"
  discipline, now extended to the visual dimension AND to best-attempt ranking. The agent-emitted
  `score` float is advisory only.
- **Subagent bare-output carve-out.** The checker follows the `cast-requirements-checker` /
  `cast-comment-reanchor` precedent: `dispatch_mode: subagent`, `interactive: false`,
  `context_mode: lightweight`, `allowed_delegations: []`, bare-JSON output (no `.output.json`
  envelope, FR-011 carve-out). Registry discovery via `bin/generate-skills`.
- **Tolerant verdict extraction.** Parsing reuses the `eval_render_checker._parse_verdict_json`
  salvage pattern (fenced / chatty wrappers tolerated); genuinely malformed JSON **raises** — the
  parser never coerces garbage into a verdict; the service layer maps the raise to
  checker-unavailable handling.
- **Config knobs, never magic constants.** All loop bounds live in `cast_server/config.py`:
  `QUALITY_MAX_ATTEMPTS = 15`, `QUALITY_MAX_WHAT_REWORKS = 2`, `QUALITY_STRUCTURAL_STOP = 3`.
  Disjoint from Phase 3's `RENDER_*` keys and Phase 5's `GAPFILL_*` keys.
- **Eval mirrors `eval_render_checker.py`** (`eval_` prefix so pytest never collects it; `--live` /
  verdict-replay / `--out-verdicts`; the gate functions imported from production code, not copied).
- **`build/` is a non-goal, non-CI-collected runtime area.** Verdict artifacts
  (`attempt-N.verdict.json`) live under `build/render-jobs/{slug}/{hash12}/`, never inside
  `goals/{slug}/`.
- **DB migration test pattern:** `tests/test_schema_migration.py` covers `schema.sql` changes
  (additive columns nullable/defaulted; no row rewrites).

## Key File Paths

| File | Role |
|------|------|
| `agents/cast-requirements-render-checker/` | **NEW (4a-1)** — checker agent dir (`.md` + `config.yaml`); registry-discoverable |
| `cast-server/cast_server/requirements_render/checker_verdict.py` | **NEW (4a-1)** — pure: `parse_verdict`, `derive_pass`, `canonical_score`; beside `maker_gate.py` |
| `cast-server/cast_server/requirements_render/zero_click.py` | `extract_zero_click_view` — the runner computes the checker's zero-click input deterministically |
| `cast-server/cast_server/requirements_render/maker_gate.py` | Phase 3b: `check_html`, `GateReport`, `container_text_index` — the **structural** gate every attempt passes BEFORE clean publish |
| `cast-server/cast_server/services/render_job_service.py` | Phase 3c: the named stage pipeline + `AgentRunner` + publish + reaper. **4a-2 inserts `run_checker → decide_quality`** between `gate_html` and `publish` |
| `cast-server/cast_server/config.py` | Phase 3 `RENDER_*` keys + stage-timeout list. **4a-2 adds `QUALITY_*` knobs + registers the checker stage** |
| `cast-server/cast_server/db/schema.sql` | Phase 3 `render_jobs` CREATE TABLE (incl. `heartbeat_at`). **4a-2 adds ONLY the four flag columns** |
| `cast-server/cast_server/routes/pages.py` | Phase 3d `/render` + `/render/status`. **4a-2 adds `human_review` to the status JSON (read from the served artifact)** |
| `cast-server/tests/test_render_job_service.py` / `test_quality_loop.py` | 4a-2 fake-runner loop tests |
| `cast-server/tests/test_checker_verdict.py` | 4a-1 parse/PASS/score tests |
| `cast-server/tests/eval_quality_gate.py` | **NEW (4a-3)** — live checker-discriminates + loop-converges harness |
| `cast-server/tests/fixtures/quality_gate/low_quality_attempt.html` | **NEW (4a-3)** — structurally VALID but communicatively bad fixture |
| `cast-server/tests/eval_render_checker.py` | The `claude -p` invocation + `_parse_verdict_json` salvage precedent |
| `agents/cast-requirements-checker/` | v2 SC-001 cold-reader gate — folded as a strict SUPERSET, **not modified or retired** |

## Data Schemas & Contracts (fixed by the plan, not discovered at exec — copy verbatim)

### Pipeline stage seam after 4a (the insertion)

```
run_what → gate_what → run_how → gate_html → run_checker → decide_quality → publish
                                  └─ structural gate ─┘   └──── the 4a quality loop ────┘
```

### Checker verdict (`cast-requirements-render-checker/v1`) — ONE bare JSON object, no prose, no fences

```json
{
  "contract": "cast-requirements-render-checker/v1",
  "can_state_what": true,
  "restated_job": "…", "restated_outcome": "…",
  "restated_scope": {"in": ["…"], "out": ["…"]},
  "missing": [],
  "issues": [
    {"dimension": "comprehension|visual", "criterion": "<id>",
     "severity": "error|warning", "description": "…", "evidence": "…"}
  ],
  "score": 1.0,
  "rework_feedback": ["prompt-ready instruction for the HOW agent", "…"]
}
```

- The v2 fields (`can_state_what`, `restated_*`, `missing`, `score`, `issues`) keep their **exact**
  names and semantics — the fold-in is a strict **superset**. `issues[]` gains `dimension` +
  `evidence`; `rework_feedback[]` is new. **Every `error` issue MUST contribute ≥1 feedback
  string** (a fail with no actionable feedback is a prompt bug).

### Code-side gate (`checker_verdict.py`) — the agent NEVER decides its own gate

- `parse_verdict(raw: str) -> CheckerVerdict` — frozen dataclass; tolerant extraction (the
  `eval_render_checker._parse_verdict_json` salvage precedent); malformed → **raises**.
- `derive_pass(v) -> bool` = `can_state_what == True` **AND** no `missing[]` entry containing a
  gated token (`job`/`outcome`/`scope`) **AND** zero `severity:"error"` issues in either dimension.
  Warnings **never** block. (A *clean* publish additionally requires structural validity — see the
  policy table.)
- `canonical_score(v) -> float` = **recomputed** code-side from issue counts (preso convention:
  `1.0 − 0.15·errors − 0.05·warnings`, floored at 0) — so best-attempt ranking can never be skewed
  by a judge that emits a flattering float.

### `render_jobs` columns — 4a-2 migration adds ONLY these four (C4)

```
human_review     INTEGER NOT NULL DEFAULT 0
review_reason    TEXT        -- non_convergent | checker_unavailable | structural_degradation | structural_violation
published_attempt INTEGER
published_score  REAL
```

- **`heartbeat_at` is NOT added here — it already ships in Phase 3's INITIAL CREATE TABLE**
  (reconciliation C4). 4a-2's migration touches only the four flag columns.
- Status enum **unchanged** (`published` covers flagged publishes — the page IS served; the flag is
  orthogonal). `flagged` already exists from Phase 3 for the no-scoring structural-override serve;
  4a's richer flag columns + scoring layer on top.
- These columns are the **queryable/observability copy** (Phase-5 sweep input, post-mortem). They
  are **NOT** the status-poll read path — the served-artifact envelope is (below).

### `decide_quality` policy table (exhaustive over terminal states — THE OVERRIDE BAKED IN)

| Condition | Action | Job row |
|---|---|---|
| structurally valid **AND** `derive_pass(verdict)` true | publish clean | `published`, no flag, `served-by: maker` |
| fail (quality **or** structural), attempts < ceiling, structural-stop not hit | rework with provenance-tagged feedback | `running`, `attempts++`, `heartbeat_at` touched |
| terminal, ≥1 scored **structurally-valid** attempt | publish best-scoring VALID attempt (tie → latest) | `published`, `human_review=1`, `review_reason='non_convergent'`, `published_attempt`, `published_score`, `served-by: maker` |
| terminal, scored attempts exist but **none structurally valid** | publish best-scoring BROKEN attempt (tie → latest) | `published`, `human_review=1`, `review_reason='structural_violation'`, `served-by: structural_violation` |
| terminal, attempts exist but all **unscored** (checker unavailable) | publish latest valid-if-any-else-latest attempt | `published`, `human_review=1`, `review_reason='checker_unavailable'` |
| `QUALITY_STRUCTURAL_STOP` consecutive structural failures | early terminal → apply the two rows above by validity | `published`, `human_review=1`, `review_reason='structural_degradation'` (or `structural_violation` if served attempt is broken) |
| **LITERAL no-output**: crash / timeout / zero attempts ever extracted | deterministic fallback (NEVER LLM-gated) | `fallback` + reason |

> The source plan's row *"terminal with ZERO structurally-valid attempts → deterministic fallback"*
> is **DELETED by the override**. If any attempt was extracted, it is served + flagged; the
> deterministic page fires only on literal no-output.

## Pre-Existing Decisions (binding — from decisions-so-far.md)

- **One checker**, comprehension + visual in a single pass — no coordinator, no tone/adversarial
  passes. The preso `check-content`/`check-visual` agents are **pattern reference only** (criterion
  vocabulary) — never invoked, never extended.
- **Quality loop** rationed ONLY by the high anti-infinite-loop ceiling; cost/latency/tier NOT
  constraints. The Phase-3 in-flight semaphore stays the only resource guard.
- **Fork OVERRIDE** (above) — deterministic only on literal no-output; structurally-broken =
  scoreable/servable + flagged.
- **Flag** = the four `render_jobs` columns + the served-artifact envelope stamp (single source of
  truth for the status-poll read), beside `source-hash`.
- **Deterministic fallback is NEVER LLM-gated** — the crash escape hatch, snapshot-tested
  (SC-002 as narrowed by 3e). Running the checker over it would re-introduce an LLM dependency on
  the no-LLM path.
- **Model tier = `opus`** for `cast-requirements-render-checker` (RESOLVED 2026-06-12; placeholder
  already says opus; the `[USER-DEFERRED]` knob is a later tune-down review, not a 4a decision —
  zero plan edits needed).
- **Human-review consumption surface deferred to Phase 5d** — 4a records the flag only.
- **Gap-amnesty clause (revision d):** the checker prompt AND the eval fixtures gain
  *".rr-gap markers are honest communication of a source gap, not a comprehension failure of the
  render."* — without it the loop fights the Phase-5 gap contract.

## Relevant Specs

- **`cast-requirements-render.collab.md` (Draft, v3 after Phase 3e)** — `linked_files` overlap with
  4a. Sub-phase **4a-3** runs the single `/cast-update-spec` pass (checker contract, quality loop +
  ceiling, the precise FR-006 two-branch policy **as overridden**, the four flag columns +
  status-JSON addition, verification-layer FR-009). Sub-phases 4a-1/4a-2 **flag** spec deltas but do
  not edit the spec — 4a-3 records them. The v2 `cast-requirements-checker` +
  `eval_render_checker.py` remain the deterministic-substrate SC-001 gate, **unmodified**.
- **`cast-goal-classification.collab.md` (Draft v1)** — nine-value `WorkFamily` enum (the family
  label inlined to the checker; the `family-appropriate-structure` criterion judges against family
  communication vocabulary). **Consumed, not modified.**

## Cross-Phase Hard Edges (do not violate)

- **C3 merge note (4a ∥ 4b on `render_job_service.py`):** 4a inserts `run_checker → decide_quality`
  **after** `gate_html`; 4b widens `gate_html`'s report (carriage + comment survival). The seams are
  **disjoint by design** and pinned by 4b's T3 test. **Whichever of 4a / 4b lands SECOND does the
  mechanical merge** (no logic conflict — different lines of the same file). 4a's loop treats the
  widened `gate_html` report (whatever 4b adds) as the structural gate it wraps.
- **Reaper (revision a — no formula edit in 4a):** Phase 3's reaper ceiling already derives from the
  **configured stage-timeout list**. 4a only **REGISTERS** the checker stage timeout in that list;
  the ceiling extends automatically. Do **not** write a new reaper formula. `heartbeat_at` is
  touched by the per-job thread at the new stage boundaries (`run_checker`, `decide_quality`) too.
- **Checker input is structural, not disciplinary:** the runner inlines ONLY the rendered artifact
  (zero-click view first, then full HTML) + the family label. The checker is tool-free (`--tools ""`)
  and physically cannot fetch the canonical source or the WHAT doc — the cold-reader property is
  guaranteed by construction.

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|-----------|------|-----------|--------|-------------------|
| 4a-1 (checker + verdict module) | Sub-phase | Phase 3 built | 4a-3 | 4a-2 |
| 4a-2 (quality loop in the service) | Sub-phase | Phase 3 built | 4a-3 | 4a-1 |
| 4a-3 (spec + live evals + fault-injection gate) | Sub-phase | 4a-1, 4a-2 | — (terminal) | — |

No decision gates: the source plan defines none. 4a-3's `/cast-update-spec` is an inline
human-approval gate (review the diff before approval). The human-eyeball browser pass over a
flagged-publish + a converged-publish is a non-blocking carry-forward (no-browser-for-visual-gates
rule); a 1a-evidence calibration FAIL in autonomous mode is recorded as a human-eyeball
carry-forward item, never a silent pass or a hard block.
