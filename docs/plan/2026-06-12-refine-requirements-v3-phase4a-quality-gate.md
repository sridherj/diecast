# Refine Requirements — Better Rendering (v3): Phase 4a — The Quality Gate: Checker & Quality-Driven Rework Loop

> ## ✅ RESOLVED — OWNER OVERRIDE (2026-06-12): structural-violation policy is FINAL
> **This supersedes the "Fork Resolution: Structural Violations Stay on the No-Output Branch
> (RATIFIED…)" section below and every "structurally-broken → deterministic page" passage in
> this document.** The earlier section *ratified* the opposite of what the owner ultimately
> chose; treat it as historical context only.
>
> **Rule (binding):** the no-output branch = *literal* no-output ONLY (crash / timeout /
> nothing produced). A structurally-broken-but-present attempt **is scoreable and servable**,
> served as the best attempt with a `structural_violation` + `human_review` flag — **never** the
> deterministic page. Non-convergence on quality (with ≥1 servable attempt) likewise serves the
> best attempt + flag. The deterministic page is reserved for literal no-output. "Never silently
> drop" binds via flags/badges. Principle: **surface, don't suppress.** The 4a executor also
> adds the gap-amnesty clause to the checker prompt + eval fixtures, and ships flag columns
> *recording-only* (the flagged-renders list is Phase 5d). Canonical record:
> `docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md` (§ Post-reconciliation
> owner decisions).

## Overview

This plan details **Phase 4a only** of the v3 high-level plan: no maker render reaches a
reader unless `cast-requirements-render-checker` — ONE thorough agent grading comprehension
**and** visual quality in a single pass (the owner explicitly rejected a multi-checker
coordinator) — passes it. The checker drives a **quality-driven rework loop** inside
Phase 3's `render_job_service`, inserted between `gate_html` and `publish` exactly at the
stage seam Phase 3 reserved: the loop reworks until the comprehension bar is met, guarded
only by a HIGH anti-infinite-loop safety ceiling — loops are never rationed by cost,
latency, or model tier (owner decision, binding). The two-branch fallback policy (FR-006)
is implemented precisely: a **true no-output failure** (crash, timeout, empty/unusable
output, zero structurally-valid attempts ever) serves the deterministic page; **output
that exists but never converges on quality** serves the **best-scoring structurally-valid
attempt** with a human-review flag recorded on the `render_jobs` row — **never** the plain
deterministic page.

The shaping insight: Phase 3's deterministic `maker_gate` and this phase's LLM checker
split cleanly along a trust boundary — **the deterministic gate owns fidelity to the
source** (id parity, verbatim carriage, DOM contract: everything whose failure means
silent data loss), **the LLM checker owns the reader's experience** (can a cold reader
state the WHAT; does the page look like something you'd show a customer). The checker
therefore judges only the rendered artifact, never the canonical source — it stays the
unfamiliar reader that made SC-001's cold-reader verdict trustworthy in v2.

Planning only — this document specifies Phase 4a; it does not implement it. It assumes
Phase 3 is built (the stage seam, `maker_gate.py`, the `render_jobs` table, `AgentRunner`).

## Operating Mode

**HOLD SCOPE** — `refined_requirements.collab.md` front matter pins `scope_mode: hold` and
the delegation context repeats it ("Honor scope_mode: hold"). Owner decisions in
`docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md` are binding and not
re-opened. Explicitly out of scope (4b/5 territory): the diff/comment-resolution agent,
`block_diff`/reanchor surfaces, gap-fill upstream asks (`gaps[]` stays a dormant seam), and
any human-review *queue UI* beyond recording + exposing the flag (the requirements mandate
the flag is recorded, SC-008 — they do not mandate a review dashboard; building one would
be silent scope drift).

## Position in Overall Plan

```
Phase 1 (gates green) ──┐
                        ├──► Phase 3 (maker pipeline) ──┬──► Phase 4a (THIS PLAN) ──┐
Phase 2 (parallel) ─────┘                               └──► Phase 4b (comments)  ──┴──► Phase 5
```

Phase 4a consumes Phase 3's pipeline and seams; it runs **parallel with Phase 4b** (which
owns the diff/comment-resolution agent — zero file overlap by design: 4a touches
`render_job_service`, the new checker agent dir, `render_jobs` schema, and the status
endpoint; 4b touches `block_diff`, `cast-comment-reanchor`'s successor, and the comment
surfaces). Phase 5's gap-fill and nine-family sweep build on the loop this phase lands.

## Depends On (from prior plans / seed decisions)

From the binding seed (`refine-requirements-better-rendering-v3-decisions-so-far.md`):

- **One checker:** `cast-requirements-render-checker`, comprehension + visual in a single
  pass — no multi-checker coordinator, no tone/adversarial passes. The preso
  `cast-preso-check-content`/`check-visual` agents are **pattern reference only** (criterion
  vocabulary, verdict-shape conventions) — never invoked, never extended.
- **Quality loop:** rework until the comprehension bar is met; only a high anti-infinite-loop
  safety ceiling; cost/latency/model-tier explicitly NOT constraints.
- **Fallback policy:** deterministic page ONLY on true no-output failure; non-convergence →
  best-scoring attempt + human-review flag, never the plain page.
- **[USER-DEFERRED]** maker/checker model tier — honored here exactly as in Phase 3:
  `model:` read from the agent's `config.yaml` (placeholder + tuning-knob comment).

From Phase 3 (planned; interfaces adopted as-is):

- **The stage seam:** `render_job_service` pipeline stages as named functions —
  `run_what → gate_what → run_how → gate_html → publish`; Phase 3 designed the seam so
  "4a adds a stage, not a rewrite". This plan adds `run_checker → decide_quality` between
  `gate_html` and `publish`.
- **`AgentRunner`** (`run_agent(agent_name, user_msg, *, timeout_s) -> str`, tool-free
  `claude -p`, `env -u CLAUDECODE` + clean-env hygiene per plan-review A1) — the checker
  dispatches through the same seam; tests inject fakes.
- **`maker_gate.py`** (`check_html`, `GateReport` with prompt-ready violations) — the
  structural gate every attempt must pass BEFORE it is eligible for checker scoring or
  best-attempt publication. The violations channel is the same one checker feedback rides.
- **`render_jobs` table** — Phase 3 left it as the observability surface and "the seam
  where 4a will record its human-review flag". This plan adds the flag columns.
- **Job artifacts** under `build/render-jobs/{slug}/{hash12}/` (`RENDER_JOBS_DIR`):
  `what.md`, `attempt-N.html`, gate reports — extended here with `attempt-N.verdict.json`.
- **Structural-violation policy (the flagged fork):** Phase 3 classified
  structurally-unusable output as the no-output branch → deterministic fallback after one
  bounded structural retry, and flagged it for this phase to ratify or argue. Resolved
  below ("Fork Resolution").
- **Stale-render-with-banner** (3d): readers are never blocked on the loop — a multi-hour
  rework job leaves them on the prior render with the regenerating banner. The status
  endpoint derives `ready` from the artifact's embedded `source-hash`.

From Phase 1 (planned):

- The **"clearly beats" operationalization** (1a, autonomous decision #4): checker
  restatement completeness + structured rubric (hierarchy, scannability,
  family-appropriateness, visual quality) + no structural-gate regression + human-eyeball
  carry-forward. The 4a quality bar is the productionized form of exactly this rubric.
- The **judge-validity flag** (1a design review): anomalous `cast-requirements-checker`
  verdicts on maker HTML were to be recorded as Phase 4a input — execution must read
  `spikes/1a/spike-results.md` for recorded anomalies before finalizing the checker prompt.

From v2 (consumed verbatim):

- **`cast-requirements-checker`** — the SC-001 cold-reader verdict shape this checker folds
  in as a strict superset: `can_state_what`, `restated_job`, `restated_outcome`,
  `restated_scope{in,out}`, `missing[]`, `score`, `issues[]`; the binary PASS rule
  (boolean + `missing[]`, never the `score` float — render-spec FR-010); the subagent-mode
  bare-JSON carve-out (FR-011). The v2 agent itself is **not modified or retired** — it
  remains the SC-001 gate for the deterministic substrate (`eval_render_checker.py`).
- **`extract_zero_click_view`** — the runner computes the checker's zero-click input
  deterministically (the `eval_render_checker.py` faithfulness pattern: input
  byte-deterministic, only the judgement varies).
- The **rubric criterion vocabulary** shared with the preso fleet: `one-clear-takeaway`,
  `l1-l2-hierarchy`, `restate-test` — reused verbatim so the fleet keeps one vocabulary.

## Fork Resolution: Structural Violations Stay on the No-Output Branch (RATIFIED, with one sharpening)

> **⛔ SUPERSEDED — historical only. See the OWNER OVERRIDE banner at the top of this doc
> (2026-06-12).** The owner reversed this section: structurally-broken-but-present attempts are
> served (best attempt + `structural_violation` flag), and the deterministic page is reserved
> for *literal* no-output. The "stay on the no-output branch" framing below no longer holds.

Phase 3 flagged this fork explicitly: it classifies structurally-unusable maker output
(missing/invented ids, broken verbatim carriage, DOM-contract violations) as the
**no-output branch** → deterministic fallback after one bounded structural retry — and
asked this phase to assess that against the owner's best-attempt-plus-flag decision.

**Verdict: RATIFIED.** Structural integrity is a hard gate protecting comment anchoring,
and the owner's best-attempt decision governs the *quality* bar, not the structural one:

1. **The owner's own words scope the decision to quality.** FR-006/SC-008 define
   non-convergence as "output was produced but the **checker** never reached the bar" and
   the decision rationale is "a reader should never be down-graded to the plain render
   **when a better attempt exists**." A structurally-broken page is not a *better attempt*
   — it is a page on which `<mark>` placement silently fails and the comment layer
   detaches. Serving it would trade a P2 cosmetic upgrade (US4) against P1 invariants
   (US3 Scenario 1 stable anchors; FR-003 ids verbatim; the constraints section's "the
   comment and version layer is non-negotiable").
2. **"Best-scoring" presupposes a score.** Only structurally-valid attempts ever reach the
   checker (the gate precedes scoring in the stage order), so a structurally-broken attempt
   has no score and cannot be "best-scoring" — the owner's decision is literally
   inapplicable to it.
3. **The v2 load-bearing rule applies verbatim:** "deterministic machinery where being
   wrong means silent data loss." Mark-placement loss is the silent data loss Phase 1b
   sharpened; the deterministic gate is the machinery.

**One sharpening (this is the part Phase 3 could not see):** inside the 4a loop, the
no-output classification applies **only when the job has produced ZERO structurally-valid
attempts**. Once any structurally-valid attempt exists in the attempt history, a *later*
rework attempt failing the structural gate consumes loop budget but can never trigger the
deterministic fallback — terminal non-convergence then serves the best-scoring
**structurally-valid** attempt + flag, honoring the owner decision exactly where it
applies. The two policies are therefore not in tension: deterministic fallback fires only
when there is literally nothing structurally safe to serve.

## Sub-phase 4a-1: The Checker Speaks a Folded, Code-Gateable Verdict

**Outcome:** `agents/cast-requirements-render-checker/` exists as a net-new,
registry-discoverable agent (`.md` + `config.yaml`, picked up by `bin/generate-skills`),
runnable tool-free via the Phase 3 `AgentRunner`; it grades comprehension + visual quality
in ONE pass and emits ONE bare JSON verdict that is a strict superset of the v2 SC-001
cold-reader shape; a pure module `cast_server/requirements_render/checker_verdict.py`
parses the verdict and **computes the binary PASS and the canonical score code-side** —
the agent never decides its own gate.

**Dependencies:** None within Phase 4a (parallel with 4a-2 — the verdict contract is fixed
by this plan, not discovered from the prompt). Phase 3 built.
**Estimated effort:** 1 session.

**Verification:**
- Agent dir passes `/cast-agent-compliance` (allow-list, directory conventions, config shape).
- `pytest cast-server/tests/test_checker_verdict.py` green: parse + PASS derivation + score
  recomputation covered with at least one fixture per outcome (pass; fail-on-missing-gated;
  fail-on-error-issue; warnings-only passes; malformed JSON raises; fenced/chatty output
  tolerated by the `_parse_verdict_json` salvage pattern).
- A hand-run of the agent over the Phase 1a maker-evidence HTML and over a deliberately
  low-quality fixture produces verdicts that **discriminate** (evidence HTML passes or
  near-passes; low-quality fixture fails with non-empty `rework_feedback`) — recorded as a
  smoke-run note, not a CI test.
- `bin/generate-skills` regenerated; the skill appears without manual registry edits.

Key activities:

- **Author `agents/cast-requirements-render-checker/cast-requirements-render-checker.md`.**
  Philosophy: you are an **unfamiliar reader with taste** — the SC-001 cold reader and the
  design reviewer in one pass. Input (all inlined in the user message by the runner — the
  agent is tool-free and physically cannot fetch anything else), in this order:
  1. the **zero-click view** (the exact `extract_zero_click_view` output — the restate test
     is performed on THIS SECTION ALONE, before reading further; the prompt states this
     ordering as a hard rule);
  2. the **full candidate HTML** (for visual quality + below-the-fold comprehension);
  3. the **family label** (e.g. `new_initiative`) — so family-appropriateness is judgeable;
  4. NOTHING else: **never the canonical source, never the WHAT doc** (see Decisions Made
     Autonomously #2 — fidelity to source is `maker_gate`'s job; the checker judges only
     what a reader experiences).
- **Comprehension criteria** (the SC-001 fold-in + document-depth additions):
  `restate-test` (state job / primary outcome / in-out scope from the zero-click surface
  alone — the gated core), `one-clear-takeaway`, `l1-l2-hierarchy` (both reused verbatim
  from the fleet vocabulary), `section-outcomes-land` (each section communicates one clear
  takeaway, not a reformatted dump), `scannable-not-wall` (a scrolling reader can navigate
  by headings; no wall-of-text blocks).
- **Visual criteria** (adapted from the preso check-visual vocabulary to a scrolling
  document page — pattern reference, not invocation): `not-generic` (layout is intentional
  and archetype-driven, not "title + bullets" homogeneity), `hierarchy-clear` (traceable
  eye path), `toolkit-consistent` (visual-toolkit style tokens), `whitespace-breathes`,
  `not-ai-aesthetic` (no symmetric icon grids, uniform boxes, gradient slop),
  `family-appropriate-structure` (sections read as family communication — "what broke and
  the evidence", "signal sources" — never US/FR/SC slots), `anchor-labels-unobtrusive`
  (the visible id labels stay small metadata, warning-only). Viewport-fit and the three
  image/screenshot criteria are **dropped** — this is a scrolling document and autonomous
  runs cannot drive a browser (per project convention: static verdicts + human-eyeball
  carry-forward, never block).
- **Verdict schema** (ONE bare JSON object, no prose, no fences — the FR-011 carve-out):

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

  The v2 fields (`can_state_what`, `restated_*`, `missing`, `score`, `issues`) keep their
  exact names and semantics — the fold-in is a strict superset; `issues[]` gains
  `dimension` + `evidence`; `rework_feedback[]` is new (every `error` issue MUST contribute
  at least one feedback string — a fail with no actionable feedback is a prompt bug).
- **`checker_verdict.py`** (pure, I/O-free, beside `maker_gate.py`):
  `parse_verdict(raw: str) -> CheckerVerdict` (frozen dataclass; tolerant extraction per
  the `eval_render_checker._parse_verdict_json` salvage precedent; malformed → raises, the
  service layer maps that to checker-failure handling) and
  `derive_pass(v) -> bool` — **the binary PASS rule, computed code-side**:
  `can_state_what == true` AND no `missing[]` entry containing a gated token
  (`job`/`outcome`/`scope`) AND **zero `severity: "error"` issues in either dimension**.
  Warnings never block (judge taste-variance must not churn the loop); the agent-emitted
  `score` is advisory only. `canonical_score(v) -> float` **recomputes** the score
  deterministically from issue counts (the preso convention: 1.0 − 0.15·errors −
  0.05·warnings, floored at 0) so best-attempt ranking can never be skewed by a judge that
  emits a flattering float. This extends render-spec FR-010's "the gate is the boolean"
  discipline: the gate AND the ranking are both code-owned.
- **`config.yaml`** per the carve-out precedent (`cast-requirements-checker` /
  `cast-comment-reanchor`): `dispatch_mode: subagent`, `interactive: false`,
  `context_mode: lightweight`, `allowed_delegations: []`, `timeout_minutes: 15`;
  `model:` set to the `opus` placeholder with the
  `# [USER-DEFERRED] tier knob — placeholder, do not tune here` comment (Phase 3a
  convention, adopted verbatim).
- **Read `spikes/1a/spike-results.md` for recorded judge anomalies** (the 1a carry-forward)
  and fold any lesson into the prompt (e.g. if the v2 checker mis-judged a
  family-restructured page, the new prompt must explicitly allow family vocabulary).
- → Delegate: `/cast-agent-compliance` over the new agent dir — review output for
  allow-list, naming, and directory-convention violations.
- → Delegate: consult `/cast-agent-design-guide` (I/O contract section) while authoring —
  the verdict contract above goes in the agent `.md` as the contract block.

**Design review:**
- **Spec consistency ⚠️** — the checker's I/O is new spec'd behavior under
  `cast-requirements-render.collab.md` (sibling to FR-009/FR-010/FR-011); contract text is
  fixed here and recorded verbatim by 4a-3's `/cast-update-spec` (same discipline as
  Phase 3a→3e).
- **Architecture ✓** — gate computed in `checker_verdict.py`, not trusted from the agent;
  mirrors the FR-010 "binary and code-checkable" precedent exactly; pure module beside
  `maker_gate.py`, same no-I/O discipline.
- **Naming ✓** — `cast-requirements-render-checker` per the seed decision (verbatim);
  criterion IDs reuse the fleet vocabulary where they overlap.
- **Error & rescue:** malformed/fenced verdict output raises in `parse_verdict`; the
  service layer (4a-2) owns retry + the checker-unavailable terminal policy — the parser
  never silently coerces garbage into a verdict.
- **Security ✓** — tool-free subprocess; the checker cannot read the canonical source *by
  construction* (the runner inlines only the rendered artifact + family), which is also
  what keeps the cold-reader property structural rather than disciplinary.

## Sub-phase 4a-2: The Loop Reworks on Quality and Lands the Right Terminal State

**Outcome:** `render_job_service` runs the full gated pipeline —
`run_what → gate_what → run_how → gate_html → run_checker → decide_quality → publish` —
where `decide_quality` implements: pass → publish; fail → rework with feedback; ceiling
reached → best-scoring structurally-valid attempt published + human-review flag; zero
structurally-valid attempts ever → deterministic fallback. Every attempt's verdict is a
recorded artifact; the `render_jobs` row carries the flag; the status endpoint exposes it.
All of it proven by deterministic fake-runner tests.

**Dependencies:** None within Phase 4a to *start* (parallel with 4a-1 — the loop is built
against the verdict contract this plan fixes, with fake checker verdicts); merging requires
4a-1's `checker_verdict.py`.
**Estimated effort:** 1.5 sessions.

**Verification (all fake-runner, no LLM in default CI — extends `test_render_job_service.py`
or a new `test_quality_loop.py`):**
- **US4 rework path:** fake checker fails attempt 1 with `rework_feedback`, passes
  attempt 2 → published; assert the attempt-2 HOW prompt contains the attempt-1 feedback
  strings verbatim; assert both `attempt-N.verdict.json` artifacts exist.
- **SC-004 unchanged:** fake runner crash/timeout/empty before any attempt → deterministic
  fallback published, `status=fallback`, reason recorded; assert the checker stage was
  **never invoked** (the fallback page is not LLM-gated — it is the crash escape hatch,
  snapshot-tested per Phase 2/SC-002).
- **SC-008 non-convergence:** fake checker never passes across attempts with varied
  canonical scores (e.g. attempt 2 scores highest of 4) → loop runs to the ceiling →
  **attempt 2's HTML is published** (assert content identity), `human_review=1` +
  `review_reason='non_convergent'` on the row, and the published file is **NOT** the
  deterministic render (assert against a real `render_requirements()` output of the same
  source); status endpoint reports `ready` with `human_review: true`.
- **Fork sharpening, both halves:** (a) structural-gate exhaustion with zero valid
  attempts → deterministic fallback (Phase 3 behavior preserved, now asserted with the
  checker stage wired); (b) a structural failure occurring AFTER a valid scored attempt
  exists → no fallback: loop continues / terminates per policy and the best valid attempt
  + flag is served.
- **Checker-unavailable terminal:** fake checker raises (malformed JSON / subprocess error)
  twice for the same attempt → that attempt is recorded `unscored`; if no scored attempt
  ever exists at terminal time, the LAST structurally-valid attempt is published +
  `review_reason='checker_unavailable'` — never the plain page (structurally-valid output
  exists, so FR-006's no-output branch does not apply).
- **WHAT-escalation:** fake checker fails 3 consecutive attempts with the same gated
  `missing[]` token → assert the next rework re-runs `run_what` (with accumulated
  feedback) before `run_how`, at most twice per job.
- **WHAT-escalation gate-failure (plan-review CQ2/T1):** a forced WHAT re-run whose
  `run_what` output FAILS `gate_what` → assert the prior known-good WHAT doc is retained
  (the failed re-gen is discarded, NOT the good WHAT), the `QUALITY_MAX_WHAT_REWORKS`
  budget is still decremented, HOW reworks resume against the retained WHAT, and **no
  deterministic fallback fires** (a structurally-valid attempt history already exists, so
  the no-output branch does not apply).
- **Served-artifact flag fidelity (plan-review A2/T2):** publish a flagged best-attempt for
  hash `H` (`human_review=1`), then open a NEW `running` regen job for the same `H` (a
  stale-render-with-banner state) → assert the status endpoint reports `human_review: true`
  read from the **served artifact's envelope**, NOT `false` derived from the fresh
  `running` row's default. Guards the A2 envelope-stamp against regressing to a
  latest-row read.
- **Ceiling config:** loop stops at exactly `QUALITY_MAX_ATTEMPTS` (config override in
  test); early-stop after 3 consecutive post-valid structural failures asserted.
- **Migration test** (`test_schema_migration.py` pattern): new `render_jobs` columns
  present on a fresh DB and added to an existing v3 DB without data loss.
- `test_fr007_readonly_guard.py` maker sweep re-run green with the checker stage active
  (the loop never widens the write surface: still only `RENDER_JOBS_DIR` + the atomic
  publish).

Key activities:

- **`run_checker` stage:** runner computes `extract_zero_click_view(attempt_html)`
  (byte-deterministic input, the eval-harness faithfulness pattern), inlines
  zero-click view + full HTML + family into the user message, dispatches
  `cast-requirements-render-checker` through the `AgentRunner` seam
  (timeout from agent config), parses via `parse_verdict`. One retry on parse/subprocess
  failure; a second failure marks the attempt `unscored` (recorded, never silent) and the
  loop proceeds.
- **`decide_quality` stage — the policy table, exhaustive over terminal states:**

  | Condition | Action | Job row |
  |---|---|---|
  | `derive_pass(verdict)` true | publish this attempt | `published` |
  | fail, attempts < ceiling | rework (below) | still `running`, `attempts` incremented |
  | ceiling reached, ≥1 scored attempt | publish best canonical-score attempt (tie → latest) | `published`, `human_review=1`, `review_reason='non_convergent'`, `published_attempt`, `published_score` |
  | ceiling reached, valid-but-unscored attempts only | publish latest valid attempt | `published`, `human_review=1`, `review_reason='checker_unavailable'` |
  | terminal with ZERO structurally-valid attempts (incl. Phase 3 structural-retry exhaustion on attempt 1) | deterministic fallback | `fallback` + reason (FR-006 no-output branch, ratified fork) |
  | crash/timeout/no-output before any attempt | deterministic fallback | `fallback` (unchanged Phase 3) |

- **Rework mechanics:** re-run `run_how` with the failing verdict's `rework_feedback[]`
  appended to the prompt through the **same channel** `GateReport.violations` already rides
  (Phase 3 designed that channel for exactly this: "4a will append checker findings to the
  same channel"), plus a one-line score history (`attempt 3 of N; best so far 0.65 at
  attempt 2`) so the agent knows regression is visible. Each rework attempt re-passes
  `gate_html` (with Phase 3's one structural retry) before it reaches the checker.
  **[plan-review CQ1] Provenance-tagged feedback:** because deterministic structural
  violations (hard, non-negotiable corrections) and checker `rework_feedback` (subjective
  quality nudges) ride the **same** `GateReport.violations` transport, each item carries an
  explicit provenance tag (`structural` vs `quality`) and the rework prompt renders them
  under **separate headings** — "Structural fixes (required)" vs "Quality improvements
  (guidance)" — so the HOW agent never treats a taste suggestion as a hard requirement or
  silently down-weights a structural correction. The transport is shared (Phase 3's
  channel); the semantics are kept visibly distinct in the prompt.
  **WHAT-escalation:** if 3 consecutive verdicts name the same gated `missing[]` token, the
  comprehension failure is intent-level, not representation-level — re-run `run_what` once
  with the accumulated feedback (then `gate_what`, then resume HOW reworks); at most 2 WHAT
  re-runs per job. **[plan-review CQ2] WHAT-re-run gate failure:** if the WHAT re-run's own
  output fails `gate_what`, the prior known-good WHAT doc is **retained** (never discarded
  for a failed regeneration), the `QUALITY_MAX_WHAT_REWORKS` budget is still consumed, HOW
  reworks resume against the retained WHAT, and the failed re-gen alone **never** triggers
  the deterministic fallback (a structurally-valid attempt history already exists, so the
  no-output branch is inapplicable — Fork Resolution sharpening).
- **The safety ceiling:** `QUALITY_MAX_ATTEMPTS` in `cast_server/config.py` beside
  `RENDER_JOBS_DIR`, default **15** — deliberately high; it exists ONLY as the
  anti-infinite-loop guard the owner sanctioned, never as a cost cap (cost/latency/tier
  remain unconstrained, and the Phase 3 in-flight semaphore stays the only resource guard).
  Companion knobs, all config not magic constants: `QUALITY_MAX_WHAT_REWORKS = 2`,
  `QUALITY_STRUCTURAL_STOP = 3` (consecutive post-valid structural failures → early
  terminal: continuing to rework a maker that has degraded structurally burns the ceiling
  for nothing — best valid attempt + flag, `review_reason='structural_degradation'`).
- **Attempt history & artifacts:** in-memory per-job list of
  `(attempt_no, html_path, gate_report, verdict | unscored, canonical_score)`;
  every verdict written as `attempt-N.verdict.json` under
  `build/render-jobs/{slug}/{hash12}/` (the 3c retention pattern extended) — the
  non-convergence post-mortem is fully replayable from disk.
- **`render_jobs` columns** (schema.sql + migration): `human_review INTEGER NOT NULL
  DEFAULT 0`, `review_reason TEXT` (`non_convergent` | `checker_unavailable` |
  `structural_degradation`), `published_attempt INTEGER`, `published_score REAL`. Status
  enum **unchanged** (`published` covers flagged publishes — the page IS served; the flag
  is orthogonal), readiness still derived from the artifact hash, never from the table
  (Phase 3 architecture preserved). **[plan-review A2]** these columns are the
  **queryable/observability copy** of the flag (Phase-5 sweep input, post-mortem) — they
  are **not** the read path the status poll hits; the served-artifact envelope is (below).
- **Status endpoint addition:** `GET /goals/{slug}/render/status` JSON gains
  `human_review: bool` **read from the served artifact's envelope** (stamped beside
  `source-hash` — see Best-attempt publish path), **never from "the latest job row for the
  current hash"** **[plan-review A2]**. Deriving from the latest row is unsafe: while a
  newer regen job for the same hash is `running` (the stale-render-with-banner state from
  3d), that row's `human_review` defaults to 0 even though the artifact actually being
  served is a *prior flagged* publish — a latest-row read would silently clear the flag of
  the page the reader is looking at. Reading from the served artifact keeps the flag and
  readiness derived from the **same** source of truth (the artifact), exactly as Phase 3
  mandated for readiness. The page itself is NOT banner-stamped (the artifact stays
  byte-stable per 3d; a review surface is Phase 5+/owner-call, see Open Questions).
- **Best-attempt publish path:** the chosen attempt's HTML goes through the **same**
  `publish` stage — compare-and-publish hash re-check, AUTO-GENERATED header +
  `source-hash` envelope, atomic write — so caching, status `ready`, and SC-005 hold
  identically for flagged publishes. **[plan-review A2]** the publish envelope additionally
  stamps `human-review` (+ `review-reason`) alongside `source-hash`, so the **served
  artifact is the single source of truth for the flag** exactly as it already is for
  readiness ("the artifact IS the state", Phase 3) — the status poll reads the flag off the
  artifact it already stats for `ready`, and the `render_jobs` columns stay the observability
  copy, not the hot-path read.

**Design review:**
- **Architecture ✓** — adds two named stages at the reserved seam; no rewrite of Phase 3
  machinery; terminal-state matrix is exhaustive (every row of the policy table maps to a
  recorded job state — zero silent failures).
- **Error & rescue:** checker failure is survivable at every point (retry → unscored →
  ordinal best-attempt + flag); the only path to the plain page remains genuine
  no-usable-output. The policy table IS the FR-006 implementation — reviewed against the
  requirement text clause by clause.
- **Spec consistency ⚠️** — render-spec currently records the Phase 3 fallback semantics;
  the rework loop, ceiling, flag columns, and status-JSON addition are new spec'd behavior
  → single `/cast-update-spec` pass in 4a-3.
- **Schema migration ⚠️** — `render_jobs` gains columns; follow the
  `test_schema_migration.py` additive pattern (new columns nullable/defaulted; no row
  rewrites).
- **Performance:** worst-case job wall-clock grows to ~`QUALITY_MAX_ATTEMPTS × (HOW +
  checker timeouts)` — readers are insulated by the 3d stale-render-with-banner design,
  but **Phase 3's reaper-ceiling formula must be extended** to include the loop's worst
  case, else a long legitimate rework job gets reaped mid-flight (see Suggested Revisions —
  this is a real cross-phase correction). **[plan-review P1]** the 4s status poll must NOT
  add a per-request `render_jobs` read for `human_review`: Phase 3 deliberately kept the
  poll path off the table (readiness is artifact-derived) for poll throughput, and the A2
  envelope-stamp preserves that — the poll reads the flag from the artifact it already
  stats, so the hot path never regains a DB round-trip.
- **Disk:** 15 attempts × (HTML + verdict) per job under `build/render-jobs/` is bounded
  and inspectable; no retention policy needed now (build/ is non-CI, non-goal runtime
  area) — noted, not actioned (HOLD scope).

## Sub-phase 4a-3: The Spec Records the Gate and Fault-Injection Proves Every Branch

**Outcome:** `cast-requirements-render.collab.md` records the checker contract, the
quality-driven rework loop, the ceiling, and both fallback branches; a live eval harness
(`eval_quality_gate.py`, `eval_` prefix so pytest never collects it) proves the checker
discriminates and the loop converges on a real document; the three high-level verification
scenarios (US4, SC-004, SC-008) are demonstrated and recorded; hand-off notes for 4b/5
updated.

**Dependencies:** 4a-1 + 4a-2.
**Estimated effort:** 1 session.

**Verification (the phase gate, from the high-level plan):**
- **US4 live:** force a low-quality generation — feed the committed low-quality fixture
  through the real checker → FAIL verdict with non-empty `rework_feedback`; feed that
  feedback + fixture into a real HOW rework → improved attempt; recorded in the eval
  output. (CI keeps the deterministic fake-runner equivalent from 4a-2.)
- **SC-004 live:** fault-inject a no-output maker (env-killed subprocess / forced timeout
  via config) on a scratch goal → deterministic page served, `status=fallback`.
- **SC-008 live:** force the checker to never pass (a test-only always-fail checker prompt
  injected through the `AgentRunner` seam) → best attempt served, `human_review=1`,
  deterministic page NOT served.
- **Checker calibration gate:** over the eval corpus — Phase 1a maker-evidence HTML
  (per family), the v2 deterministic render, and the low-quality fixture — the checker
  PASSES the 1a evidence (or its failures are judged legitimate on human review) and FAILS
  the low-quality fixture. If it cannot discriminate, the **first lever is the checker
  prompt, never weakening the code-side gate** (the eval_render_checker.py discipline,
  carried forward). **[plan-review T3]** the "judged legitimate on human review" branch
  cannot execute in an autonomous (no-browser, no-human) eval run; in that mode a
  1a-evidence FAIL is recorded as a **human-eyeball carry-forward item** (never a silent
  pass, never a hard block — the project's no-browser-visual-gate convention), so the only
  **blocking** half of the calibration gate in autonomous mode is the low-quality fixture
  MUST-fail assertion, which is fully deterministic. A human-run eval still exercises the
  full discriminate-both-ways gate.
- `bin/cast-spec-checker` green on the updated spec; `docs/specs/_registry.md` row bumped.
- Human-eyeball browser pass over one flagged-publish and one converged-publish recorded as
  the standing carry-forward item (visual gates never block autonomous runs) — this is the
  same carry-forward channel the T3 calibration-failure case feeds into.

Key activities:

- **Author the low-quality fixture** (`cast-server/tests/fixtures/quality_gate/
  low_quality_attempt.html`): structurally VALID (passes `maker_gate.check_html` — ids
  verbatim, carriage intact, DOM contract clean) but communicatively bad (WHAT buried
  below the fold, wall-of-text, generic undifferentiated layout) — the fixture proves the
  two gates measure different things, which is the whole Phase 4a thesis.
- **Build `eval_quality_gate.py`** mirroring the `eval_render_checker.py` shape (`--live`,
  `--verdicts` replay, `--out-verdicts`; per-case report; binary gate per case): cases =
  calibration corpus above. The harness reuses `checker_verdict.derive_pass` /
  `canonical_score` — the eval and production share one gate implementation by import, not
  by copy.
- **Run the three live fault-injection scenarios** (US4/SC-004/SC-008 above) against a
  scratch goal + throwaway `db_path` (the 1b test-bed discipline: never the live house DB,
  never a real goal's `refined_requirements.html`); record results + artifacts in the goal
  dir as the Phase 4a gate evidence.
- → Delegate: `/cast-update-spec` on `cast-requirements-render.collab.md` with these deltas
  (review the diff before approval, per the skill's gate):
  1. **The maker-path quality gate:** `cast-requirements-render-checker` (verdict schema
     verbatim from 4a-1; subagent bare-JSON carve-out, sibling of FR-011) gates every
     maker publish; the binary PASS rule is computed code-side (`checker_verdict.py`) —
     `can_state_what` + gated `missing[]` tokens + zero error-severity issues; the score
     float never gates, and the canonical score is recomputed from issue counts.
  2. **The quality-driven rework loop:** rework-until-bar with feedback through the
     violations channel; WHAT-escalation rule; `QUALITY_MAX_ATTEMPTS` as the only loop
     bound, recorded explicitly as the owner-sanctioned anti-infinite-loop ceiling, NOT a
     cost cap; attempt artifacts under `RENDER_JOBS_DIR`.
  3. **The two-branch fallback policy, precisely (FR-006):** true no-output (crash /
     timeout / empty / malformed sentinels / **zero structurally-valid attempts ever** —
     the ratified fork, with the rationale: structural integrity protects comment
     anchoring) → deterministic page; non-convergence with ≥1 structurally-valid attempt →
     best-canonical-score attempt published + `human_review` flag — **never the plain
     page**; checker-unavailable → latest valid attempt + flag.
  4. **`render_jobs` columns + status surface:** `human_review`/`review_reason`/
     `published_attempt`/`published_score`; status JSON exposes `human_review` **read from
     the served-artifact envelope** (plan-review A2), with the `render_jobs` columns the
     queryable observability copy.
  5. **Verification layer (FR-009 of the v3 requirements):** the happy-path gate is the
     LLM-judged comprehension+visual check above (completing the seam 3e left as "recorded
     as Phase 4a scope"); the deterministic golden-HTML snapshot gate continues to cover
     the fallback substrate and the cache envelope (SC-002 as narrowed by 3e — restated,
     not re-narrowed); SC-001's cold-reader criterion is now satisfied on the maker path by
     the new checker (the v2 `cast-requirements-checker` + `eval_render_checker.py` remain
     the deterministic-substrate gate, unmodified).
  6. New surfaces appended to `linked_files`: the checker agent dir,
     `checker_verdict.py`, `eval_quality_gate.py`, the fixture.
- **Update the 4b/5 hand-off notes** in the goal dir (extending 3e's): the flag lives on
  `render_jobs` + status JSON (anything 4b's regenerate flow publishes follows the same
  policy table); Phase 5's nine-family sweep should run each family render through the
  full loop and read `human_review` as its per-family quality signal.

**Design review:**
- **Spec consistency ✓ (this IS the spec work)** — all flags from 4a-1/4a-2 resolve in one
  `/cast-update-spec` pass; clause texts were fixed by this plan up front (the 3e
  discipline: the spec records behavior, it does not retro-discover it).
- **Tests ✓** — eval imports the production gate functions (one implementation); CI never
  shells out to an LLM; live scenarios run against scratch state only.
- **Process:** calibration failure routes to the prompt, never to gate-weakening — recorded
  in the eval docstring exactly as `eval_render_checker.py` does.

## Build Order

```
Sub-phase 4a-1 (checker agent + verdict module) ──┐
                                                  ├──► Sub-phase 4a-3 (spec + live evals + fault-injection gate)
Sub-phase 4a-2 (quality loop in the service) ─────┘
```

**Critical path:** 4a-1 ∥ 4a-2 → 4a-3. Total **3.5 sessions**, inside the high-level 3-4
estimate. (4a-2 can start against the plan-fixed verdict contract with fake verdicts;
its merge gate needs 4a-1's `checker_verdict.py`.) Phase 4b proceeds in parallel
throughout — no shared files.

## Design Review Flags

| Sub-phase | Flag | Action |
|-----------|------|--------|
| 4a-1 | Checker I/O is new spec'd behavior; contract text must match the spec | Contract fixed in this plan; `/cast-update-spec` delta #1 in 4a-3 records it verbatim |
| 4a-1 | Agent allow-list/conventions drift | `/cast-agent-compliance` audit in 4a-1 verification |
| 4a-1 | Judge variance could flip the gate | Gate computed code-side from boolean + missing + error-issues; warnings never block; canonical score recomputed from issue counts |
| 4a-2 | `render_jobs` schema change | Additive migration per `test_schema_migration.py` pattern; columns defaulted |
| 4a-2 | Long rework jobs vs Phase 3's reaper ceiling | Reaper formula MUST be extended for the loop's worst case + release the held semaphore slot + add a liveness heartbeat (plan-review A1) — Suggested Revisions below |
| 4a-2 | Fallback could leak past FR-006 (plain page on non-convergence) | The `decide_quality` policy table is exhaustive and each row is a CI assertion (SC-008 test asserts NOT-the-deterministic-page directly) |
| 4a-2 | Status-JSON gains a field | `/cast-update-spec` delta #4 in 4a-3; flag read from the served-artifact envelope, not the latest job row (plan-review A2) |
| 4a-3 | Spec version bump + registry row | Included in the `/cast-update-spec` activity |
| 4a-3 | Checker can't discriminate good from bad | Calibration gate over 1a evidence + low-quality fixture; first lever is the prompt, never the gate; autonomous-mode 1a-evidence failure routes to human-eyeball carry-forward, never a silent pass/block (plan-review T3) |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Checker too harsh — nothing ever converges, every render ships flagged | Med | Calibration gate in 4a-3 (1a evidence must pass); warnings excluded from the gate; WHAT-escalation attacks intent-level failures instead of churning HOW; flagged publishes still serve the best page, so the reader never loses |
| Checker too lenient — rubber-stamps bad pages | Med | Low-quality fixture MUST fail in the eval; error-severity criteria are concrete and evidence-required; human-eyeball carry-forward on published renders |
| Rework oscillation (fixing visual breaks comprehension and vice versa) | Med | Feedback includes score history + best-so-far; canonical score makes regression visible; ceiling terminates; best-attempt selection means oscillation still ships the peak, not the last, attempt |
| Worst-case job wall-clock (~15 × HOW+checker timeouts) trips Phase 3's reaper | High (if unaddressed) | Suggested Revision below: reaper ceiling derives from the full loop worst case; the reaper releases the orphan's semaphore slot and a daemon-thread heartbeat detects dead loops before the full ceiling (plan-review A1); readers insulated by stale-render-with-banner |
| Checker subprocess flakiness poisons the loop | Med | One retry per attempt → `unscored` recorded → ordinal best-attempt + `checker_unavailable` flag; never the plain page while valid output exists |
| Best-attempt ranking skewed by judge-emitted scores | Low | Canonical score recomputed code-side from issue counts; tie → latest attempt |
| Flag is recorded but nobody ever looks | Low | `human_review` exposed in status JSON + job row queryable; Phase 5 sweep consumes it; a dedicated review surface deliberately deferred (Open Questions) |
| Served-page flag misreported while a newer regen is in flight | Med | Flag stamped into the served-artifact envelope and read from there, never from the latest job row (plan-review A2); CI fidelity test asserts a flagged stale render keeps `human_review: true` under an in-flight regen |

## Open Questions

- None blocking. Two deliberate deferrals, recorded so they are decisions-not-omissions:
  - **[USER-DEFERRED]** maker/checker model tier — honored as in Phase 3: `model:` read
    from `config.yaml` (placeholder + tuning-knob comment); the later decision is a config
    edit.
  - **Human-review consumption surface** (a queue/list UI for flagged renders): the
    requirements mandate recording the flag (SC-008), not a review workflow. Recording +
    status-JSON exposure ships in 4a; whether a review UI is wanted is an owner call for
    Phase 5+/a future goal — flagged here rather than silently built (HOLD scope).

## Decisions Made Autonomously (per the autonomous-run instruction)

1. **Fork resolution — structural violations stay on the no-output branch (Phase 3
   RATIFIED), sharpened with the zero-valid-attempts qualifier.** Full reasoning in the
   "Fork Resolution" section: the owner's best-attempt decision governs the quality bar and
   presupposes a scoreable (= structurally-valid) attempt; structural integrity is the hard
   gate protecting comment anchoring (the v2 "silent data loss" rule); deterministic
   fallback fires ONLY when zero structurally-valid attempts exist — once one exists,
   non-convergence always serves it + flag, never the plain page.
2. **The checker never sees the canonical source or the WHAT doc** — input is the rendered
   artifact (zero-click view first, then full HTML) + family label only. Grounds: the
   cold-reader property is the value of SC-001 and must stay structural (the v2 checker's
   own hard rule); fidelity-to-source is already deterministically guaranteed by
   `maker_gate` (id totality + verbatim carriage), so the checker judging "what a reader
   experiences" loses nothing — the division of labor IS the design.
3. **Binary PASS extended code-side: zero error-severity issues (both dimensions) on top
   of the v2 boolean + gated-missing rule; warnings never gate; canonical score recomputed
   from issue counts.** Grounds: FR-010's "the gate is the boolean" discipline extended to
   the visual dimension; warnings-don't-gate prevents taste-variance churn; recomputed
   score keeps SC-008's "best-scoring" deterministic and un-gameable.
4. **Checker-unavailable terminal = latest structurally-valid attempt + flag
   (`checker_unavailable`), not the deterministic page.** Grounds: FR-006's plain-page
   branch requires NO usable output; here usable output exists and the owner's "reader is
   never down-graded when a better attempt exists" applies; the flag keeps it honest.
5. **WHAT-escalation rule:** 3 consecutive verdicts naming the same gated `missing[]`
   token → one WHAT re-run with accumulated feedback (max 2 per job). Grounds: a missing
   outcome/scope in the zero-click surface is usually an intent-planning failure HOW cannot
   fix; bounded so the loop stays convergent and testable.
6. **Ceiling value and knobs:** `QUALITY_MAX_ATTEMPTS = 15` (high; anti-runaway only),
   `QUALITY_MAX_WHAT_REWORKS = 2`, `QUALITY_STRUCTURAL_STOP = 3` — all in
   `cast_server/config.py`, never magic constants (the A2 discipline). 15 ≈ 4× the point
   where rework feedback empirically stops helping in the preso fleet's experience, and
   wall-clock stays inside a generous reaper bound; explicitly NOT a cost number.
7. **Flag lives as columns on `render_jobs` (`human_review`, `review_reason`,
   `published_attempt`, `published_score`); status enum unchanged; status JSON exposes
   `human_review`.** Grounds: Phase 3 reserved exactly this seam; `published` stays
   truthful (the page IS served); readiness stays artifact-derived. **[plan-review A2]**
   the columns are the queryable/observability copy; the status poll's read path is the
   served-artifact envelope (the flag is stamped beside `source-hash` at publish), so the
   flag and readiness share one source of truth and a newer in-flight regen never
   misreports the served page's flag.
8. **The deterministic fallback page is never LLM-gated.** It is the crash escape hatch,
   snapshot-tested (SC-002 as narrowed); running the checker over it would re-introduce an
   LLM dependency on the no-LLM path.
9. **Eval harness mirrors `eval_render_checker.py`** (`eval_` prefix, `--live`/replay,
   gate imported from production code) — one gate implementation, one fleet convention.

## Suggested Revisions to Prior Sub-Phases

- **Phase 3 — reaper-ceiling formula must extend for the quality loop (correction, not a
  decision reversal).** Phase 3 derived the orphaned-`running`-row reaper ceiling from
  "`what_timeout + how_timeout`, doubled for the one structural retry" (plan-review A2).
  With the 4a loop, a legitimate job's worst case becomes
  `(1 + QUALITY_MAX_WHAT_REWORKS)·what_timeout + QUALITY_MAX_ATTEMPTS·(2·how_timeout +
  2·checker_timeout)` — an order of magnitude larger. The A2 *principle* (derive from
  config, ≥2× worst case, never a magic constant) stands unchanged; only the summed-term
  list grows. If Phase 3 is executed before 4a, implement the formula as a function of the
  configured stage list so 4a's stages extend it without edits.
  **[plan-review A1] Because the worst-case ceiling is now ~10× larger**, the reaper must
  also (a) **release the in-flight semaphore slot** a reaped orphan holds — otherwise one
  crashed-process job blocks every new render of that source for the full multi-hour
  ceiling (the Phase 3 P1 semaphore + the now-huge ceiling interact); and (b) the per-job
  daemon thread must write a **liveness heartbeat** (e.g. touch `render_jobs.heartbeat_at`
  at each stage boundary) so a dead loop is reaped on a short staleness bound rather than
  only at the full worst-case ceiling. The heartbeat is the orphan *detector*; the
  config-derived ceiling stays the backstop for a process that dies between heartbeats.
  `heartbeat_at` is an additive column folded into 4a-2's `render_jobs` migration.
- **Phase 3 — no other changes.** The stage seam, violations channel, `render_jobs` design,
  and artifact retention are consumed exactly as planned; the flagged structural-violation
  fork is ratified (with the zero-valid-attempts sharpening recorded above), so Phase 3's
  Decision #4 needs no rewrite.

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| `cast-requirements-render.collab.md` (Draft, v3 after Phase 3e) | US6/FR-009/FR-010/FR-011 (SC-001 checker verdict schema + binary PASS rule + subagent carve-out — folded into the new checker as a strict superset, v2 agent untouched); SC-001 (cold-reader criterion — maker path now satisfied by the new checker); SC-002 (determinism narrowed to fallback by 3e — restated, fallback stays snapshot-tested); Phase 3e's fallback/`render_jobs`/status-endpoint sections (extended with the loop, flag columns, `human_review` in status JSON) | 3 — all resolved by the single `/cast-update-spec` pass in 4a-3 (quality gate + loop recorded; FR-006 two-branch policy made precise incl. the ratified fork; status/schema surface additions) |
| `cast-goal-classification.collab.md` (Draft v1) | Nine-value `WorkFamily` enum (the family label inlined to the checker; `family-appropriate-structure` criterion judges against family communication vocabulary) | None — consumed, not modified |

## Plan Review Decisions (cast-plan-review, BIG CHANGE scope — autonomous)

Reviewed under HOLD scope; every fork auto-decided against the binding owner decisions in
`docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md`. **None of the
findings re-open an owner-resolved decision** (one checker agent — no multi-checker
coordinator; quality-driven loop bounded only by a high anti-infinite-loop ceiling, never
by cost/latency/model-tier; best-attempt-plus-flag on non-convergence; deterministic
fallback only on true no-output; the structural-violation fork RATIFIED with the
zero-valid-attempts sharpening). The plan's ratification reasoning was reviewed and the
owner-decision boundary stands. All eight findings sharpen cross-phase robustness
(reaper/semaphore liveness), flag-read consistency, feedback-channel clarity, an
unspecified escalation edge case, test coverage of those edges, and the autonomous-mode
calibration gate — entirely *within* the existing Phase-4a design. None weakens the
code-side gate, rations the loop by cost, adds a second checker, or serves the plain page
on non-convergence. Planning-only: no implementation exists to review (the plan assumes
Phase 3 is built). Per the B2 single-Write contract this appendix and the inline body
sharpenings above were committed in one write. Mirrors the depth and appendix format of the
Phase 3 review.

Summary: 8 issues found / 8 resolved / 0 deferred (Architecture 2, Code Quality 2,
Tests 3, Performance 1).

- **2026-06-12T08:53:00Z — A1 — Architecture: does the reaper-ceiling extension also bound how long a crashed loop holds its in-flight semaphore slot?** — Decision: Sharpen — extend the Suggested Revision so the reaper (a) releases the orphan's Phase-3 P1 semaphore slot and (b) the per-job daemon thread writes a `heartbeat_at` touch at each stage boundary; the heartbeat is the orphan detector, the config-derived ceiling the backstop. Rationale: with `QUALITY_MAX_ATTEMPTS=15` the worst-case ceiling is ~10× Phase 3's, so a crashed-process orphan would otherwise hold a concurrency slot and block every new render of that source for multiple hours; the heartbeat bounds detection to a short staleness window without reaping slow-but-live jobs, and `heartbeat_at` is an additive column folded into 4a-2's existing migration. Cost/latency stay unconstrained (this is a resource-safety guard, not a cost cap — owner boundary intact). (Body patched: Suggested Revisions reaper bullet, Design Review Flags + Key Risks reaper rows.)
- **2026-06-12T08:53:00Z — A2 — Architecture: is the status endpoint's `human_review` read consistent with the served artifact while a newer regen is in flight?** — Decision: Sharpen — stamp `human-review`/`review-reason` into the served-artifact envelope (beside `source-hash`) and have the status JSON read the flag from THAT artifact, never from "the latest job row for the current hash"; the `render_jobs` columns remain the queryable observability copy. Rationale: during the 3d stale-render-with-banner state a newer `running` regen row defaults `human_review=0` while the artifact actually served is a prior *flagged* publish — a latest-row read would silently clear the flag of the page the reader is looking at. Reading from the served artifact keeps the flag and readiness derived from the same source of truth (the artifact), exactly as Phase 3 mandated for readiness, and changes no owner decision (SC-008's "flag recorded" mandate is honored more faithfully). (Body patched: 4a-2 status-endpoint bullet, `render_jobs` columns bullet, best-attempt publish-path bullet, Decision #7, spec delta #4, Design Review Flags + Key Risks.)
- **2026-06-12T08:53:00Z — CQ1 — Code Quality: are deterministic structural violations and subjective checker feedback distinguishable when they share the `GateReport.violations` transport?** — Decision: Sharpen — tag each rework-feedback item with provenance (`structural` vs `quality`) and render them under separate prompt headings ("Structural fixes (required)" vs "Quality improvements (guidance)"). Rationale: the plan routes checker `rework_feedback` through the same channel as hard structural corrections; without a visible distinction the HOW agent can treat a taste nudge as a non-negotiable requirement or silently down-weight a structural fix — explicit-over-clever and reduces rework oscillation. Transport stays shared (Phase 3's channel, unchanged); only the prompt rendering distinguishes them. (Body patched: 4a-2 Rework mechanics.)
- **2026-06-12T08:53:00Z — CQ2 — Code Quality: what happens when a WHAT-escalation re-run's own output fails `gate_what`?** — Decision: Sharpen — specify that a failed WHAT re-gen retains the prior known-good WHAT doc (never discards it), still consumes the `QUALITY_MAX_WHAT_REWORKS` budget, resumes HOW reworks against the retained WHAT, and never on its own triggers the deterministic fallback (a structurally-valid attempt history already exists → no-output branch inapplicable). Rationale: the plan defined the escalation trigger but left the re-gen-failure path unstated, an unhandled edge case that could either discard a good WHAT or mis-route to the plain page; this resolution is the only one consistent with the Fork Resolution sharpening. (Body patched: 4a-2 Rework mechanics / WHAT-escalation.)
- **2026-06-12T08:53:00Z — T1 — Tests: is the WHAT-re-run gate-failure path (CQ2) covered?** — Decision: Sharpen — add a fake-runner test: a forced WHAT re-run that fails `gate_what` asserts the prior WHAT is retained, the WHAT-rework budget is decremented, HOW reworks continue, and no deterministic fallback fires. Rationale: the CQ2 edge case is exactly the kind of error path that rots silently without a test; well-tested code is non-negotiable and the assertion is deterministic under the fake runner. (Body patched: 4a-2 Verification.)
- **2026-06-12T08:53:00Z — T2 — Tests: is the served-artifact flag fidelity (A2) asserted?** — Decision: Sharpen — add a test that publishes a flagged best-attempt for hash H, opens a new `running` regen job for the same H, and asserts the status endpoint still reports `human_review: true` (read from the served-artifact envelope), not `false` from the fresh running row. Rationale: A2 is a correctness fix on a reader-visible field; a regression test pins the artifact-envelope read so a future refactor cannot quietly revert to a latest-row read. (Body patched: 4a-2 Verification, Key Risks.)
- **2026-06-12T08:53:00Z — T3 — Tests: can the calibration gate's "judged legitimate on human review" branch execute in an autonomous run?** — Decision: Sharpen — in autonomous (no-browser, no-human) mode a 1a-evidence FAIL is recorded as a human-eyeball carry-forward item (never a silent pass, never a hard block), so the only blocking half of the calibration gate is the low-quality-fixture MUST-fail assertion (fully deterministic); a human-run eval still exercises the full discriminate-both-ways gate. Rationale: the branch as written is unreachable headless and would otherwise force either a false block or a silent pass; routing it to the existing no-browser-visual-gate carry-forward convention keeps the gate honest without weakening the code-side gate (first lever stays the prompt). (Body patched: 4a-3 Verification calibration gate + human-eyeball bullet, Design Review Flags.)
- **2026-06-12T08:53:00Z — P1 — Performance: does exposing `human_review` reintroduce a per-poll DB read on the hot 4s status path Phase 3 kept off the table?** — Decision: Sharpen — the status poll must read the flag from the served-artifact envelope (the A2 stamp), not via a per-request `render_jobs` query, preserving Phase 3's deliberate "the poll path never touches the table" property. Rationale: readiness is artifact-derived for poll throughput; adding a DB round-trip per 4s poll per active reader would regress that, and the A2 envelope-stamp resolves correctness and performance with one mechanism (the poll reads the flag off the artifact it already stats). (Body patched: 4a-2 Design review Performance bullet; consequent of A2.)
