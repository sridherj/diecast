# Decisions So Far — refine-requirements-better-rendering-v3

Cumulative cross-sub-phase decision log for the fan-out detailed planning run.
Seeded from `docs/goal/refine-requirements-better-rendering-v3/plan.collab.md`
(Resolved Decisions, 2026-06-12). Later sections appended per completed sub-phase plan.

## Seed: Owner decisions locked at high-level planning (binding on ALL sub-phases)

- **Anchor backbone:** canonical ids (US-NN/FR-NNN/SC-NNN) are a LOGICAL backbone only.
  The served DOM keeps v2's quote/verbatim-substring anchoring — NO `id=`/`data-block-anchor`
  attributes (v2 render-spec DOM contract is preserved). Only the diff agent becomes id-aware.
- **Render execution model:** maker generation runs as a BACKGROUND JOB. A view of a changed
  source serves a live "generating…" state immediately and swaps in the finished render when
  ready. The view path never blocks on the maker loop; the comment path is independent and
  always instant.
- **Pipeline agents:** `cast-requirements-what` + `cast-requirements-how` are NET-NEW agents
  (reuse cast-preso visual toolkit + archetype library + the what/how split pattern; do NOT
  extend/couple the preso slide agents). One new checker: `cast-requirements-render-checker`
  (comprehension + visual in one pass). Plus a diff-and-comment-resolution agent (extends or
  replaces `cast-comment-reanchor`).
- **Page structure vocabulary:** the WHAT layer organizes pages by FAMILY-APPROPRIATE
  COMMUNICATION sections (e.g. data_analysis → "signal sources", "directional inputs";
  user-facing → "key decisions", "product principles") — NEVER as US/FR/SC slots. Ids ride
  along only as anchoring metadata. `families.py` FAMILY_RECIPES are starting vocabulary.
- **Gap-fill write-back door:** detail the maker obtains upstream reconciles through the
  EXISTING v2 change-request gate unchanged (propose → notify → human gate, never auto-sync);
  no new writer into the canonical source. The page marks the gap until approval.
- **Fallback policy:** deterministic renderer served ONLY on true no-output crash/timeout.
  On non-convergence: serve best-scoring attempt + human-review flag, never the plain page.
- **Quality loop:** rework until the comprehension bar is met; only a high anti-infinite-loop
  safety ceiling. Cost/latency/model-tier are explicitly NOT constraints. Caching (v2
  source-hash lazy-regen, reused unchanged) only skips identical content.
- **Canonical source:** `refined_requirements.collab.md` stays canonical; HTML is a read-only
  projection; the maker never writes it.
- **[USER-DEFERRED]** maker/checker model tier — later tuning knob, do not decide in sub-phase plans.

---
<!-- Per-sub-phase decision extracts appended below by the orchestrator -->

## Phase 1 (planned): Validate the Maker & the Anchor Backbone — 2026-06-12-refine-requirements-v3-phase1-spikes.md

- Spike evidence lives at `docs/goal/refine-requirements-better-rendering-v3/spikes/{1a,1b}/` (away from render-class filenames + CI collection).
- 1a corpus: this goal (new_initiative) + an AUTHORED bug_fix doc built from the real goal_card.py markdown-leak defect (no real second classified doc exists); data_analysis is a stretch third.
- "Clearly beats" gate operationalized: cast-requirements-checker passes maker render with restatements >= baseline AND rubric majority favors maker AND no gate regression (ids verbatim, self-contained, DOM contract) + human-eyeball carry-forward.
- 1b method: Python re-implementation of requirements_comments.js tree-walk + indexOf semantics (no browser in autonomous runs); reuses the v2 fixture pair (refined_requirements.collab.md + .v2-edit) extended with heavier edits. 1a/1b parallel.
- **SHARPENED RISK (forward to Phases 3/4b):** DB-level comment orphaning CANNOT be caused by render variation alone (anchor validation is source-side; maker never writes source). Real exposure: (a) silent `<mark>`-placement loss on paraphrased maker DOM, (b) the unspec'd maker obligation to carry anchorable text VERBATIM in the DOM. → Phase 3's /update-spec MUST add a "verbatim-carriage clause" to the maker contract.
- Specs: consumes render-spec v2 + classification spec, modifies none.

## Phase 2 (planned): Discoverable Commenting & Honest Fallback — 2026-06-12-refine-requirements-v3-phase2-commenting-fallback.md

- 2a naming/interfaces: pure `strip_inline_markdown` helper in goal_card.py, applied at each production point (job statement, assertions, renderer.py scope grid) — strip, not convert; `_split_first_sentence` (token-set abbreviation scan over finditer candidates) replaces the bare `_SENTENCE_END_RE` split.
- 2b: commenting affordance is JS-INJECTED into `.rr-controls` (not template-rendered) per FR-028 progressive enhancement; CSS in `_theme.css.j2`; behavior = teach + surface (reveal tray, pulse gesture hint) — creation stays select->pill->composer via same-door API.
- 2c: ONE gated golden regeneration for both sub-phases (not per-sub-phase).
- Spec deltas: /cast-update-spec in 2b extends recorded commenting UX + SC-009 selector list. DOM contract untouched.
- No suggested revisions to prior phases.

## Phase 3 (planned): WHAT->HOW Maker Pipeline — 2026-06-12-refine-requirements-v3-phase3-maker-pipeline.md

- New agents: `cast-requirements-what` + `cast-requirements-how`. WHAT doc = markdown body + machine-checkable YAML front matter (total id-mapping, `unmapped_refs`, reserved `gaps[]` seam for Phase 5). HOW output = self-contained HTML between sentinels, archetype-library-driven.
- Execution: tool-free `claude -p` subprocesses from a NEW `render_job_service` (NOT the tmux dispatcher — page views must never pop a terminal). `--tools ""` makes never-writes-canonical structural.
- Job state: readiness derived from artifact's embedded `source-hash` (v2 cache IS the state); `render_jobs` DB table for observability/failure/4a human-review-flag seam; in-memory single-flight + per-job daemon thread.
- UX: 4s status poll + reload-on-ready (no SSE); `<noscript>` meta-refresh; STALE-RENDER-WITH-BANNER when a prior render exists (best-available-page applied to waiting state).
- `maker_gate.py` (pure, 3b) productionizes spike audits: id parity + per-block correspondence + verbatim-carriage (anchorable text = block body through Phase 2's `strip_inline_markdown` — single stripper, import-stable dependency) + DOM/self-containment.
- **Structural-violation policy (FLAGGED fork, 4a-adjacent):** structurally-unusable maker output (missing/invented ids, broken carriage) = no-output branch -> deterministic fallback after ONE bounded structural retry with violation feedback. Owner's best-attempt-plus-flag governs the 4a QUALITY bar only. If owner prefers best-attempt even for structural violations, revisit at 4a/reconciliation.
- Job artifacts under `build/render-jobs/` (new `RENDER_JOBS_DIR` in config.py), never in goals/{slug}/.
- Spec: single /cast-update-spec pass in 3e covers happy-path inversion, generating-state route, non-DOM id backbone + verbatim-carriage clause, determinism scope narrowed to fallback.
- Seams left for later phases: 4a checker plugs into render_job_service between HOW and publish; 4b consumes WHAT-doc id-mapping; Phase 5 consumes gaps[].

## Phase 4a (planned): Quality Gate — 2026-06-12-refine-requirements-v3-phase4a-quality-gate.md

- New agent `cast-requirements-render-checker`: one pass, comprehension + visual; verdict = strict superset of v2 SC-001 cold-reader shape; binary PASS + canonical score computed CODE-SIDE in new `checker_verdict.py` (agent never decides its own gate). Checker input = rendered artifact + family label ONLY (never sees source/WHAT doc — cold-reader stays structural; maker_gate already guarantees fidelity).
- Loop at Phase 3's reserved seam: gate_html -> run_checker -> decide_quality -> publish, inside render_job_service. Knobs in config.py: QUALITY_MAX_ATTEMPTS=15, QUALITY_MAX_WHAT_REWORKS=2, QUALITY_STRUCTURAL_STOP=3. WHAT-escalation: 3 consecutive same-missing-token verdicts -> one WHAT re-run w/ feedback (max 2/job).
- **FORK RATIFIED + SHARPENED:** structural violations stay on the no-output branch, but ONLY while zero structurally-valid attempts exist; once any valid attempt exists, non-convergence serves best-scoring VALID attempt + flag — never the plain page. Checker-unavailable terminal = latest valid attempt + flag.
- Flag = columns on render_jobs (human_review, review_reason, published_attempt, published_score, + heartbeat_at); served-artifact envelope stamps the flag beside source-hash (single source of truth for the poll read-path).
- Deterministic fallback page is NEVER LLM-gated (snapshot-tested crash hatch).
- **SUGGESTED REVISION -> Phase 3 (correction, for reconciliation):** reaper ceiling formula must extend for the loop (derive from configured stage list, ~10x larger worst case); reaper must release the in-flight semaphore slot of a reaped orphan; per-job thread writes heartbeat_at at stage boundaries (heartbeat = detector, ceiling = backstop).
- Spec: single /cast-update-spec pass in 4a-3 (gate + loop + precise FR-006 two-branch policy + status/schema additions).

## Phase 4b (planned): Comment Survival — 2026-06-12-refine-requirements-v3-phase4b-comment-survival.md

- **EXTEND cast-comment-reanchor in place (contract v2), not replace:** verdict safety machinery (orphan-over-guess, 422 verbatim backstop, no-op-on-garbage) carries untouched; one dispatch serves narrate + resolve at the version boundary; all new inputs optional so existing call sites stay byte-valid. Verdict order: relocated > resolved > orphaned-when-unsure (`resolved` included under HOLD; state machine owns final transition on races).
- Survival gate: pure `check_comment_survival` in maker_gate.py; open comments fetched at gate_html stage entry, RE-READ PER ATTEMPT. In-block placement misses = structural violations (inherit retry-then-fallback); cross-boundary quotes never block (read-time `.comment-unplaced` tray badge, derived, nothing stored).
- **SEAM PIN (for reconciliation, matches 4a):** survival evaluated INSIDE the structural gate before run_checker; a survival-failing attempt is structurally INVALID and never qualifies for best-scoring-valid serve.
- Narration: posted same-door by the parent that cut the version (server never dispatches LLM on version path); all-or-nothing 422 validation, grounded in the deterministic diff set; stored per (goal_slug, base, head), upsert-on-repost; /changes JSON gains sibling `narration` key — byte-for-byte guarantee re-scoped to counts/items.
- block_diff + diff_render NOT modified (logical backbone = existing Block.ref space; FR-024 extend-never-fork).
- **Coordination notes -> reconciliation:** (1) Phase 3's 3b must expose its container-text walker as a shared helper (hard no-copy prerequisite for 4b-1); (2) 4a's loop treats the widened gate_html report (carriage + survival) as the structural gate it wraps.
- Spec: single /cast-update-spec in 4b-4 (survival contract, FR-024 re-scope, FR-027 contract v2, narration route). Roundtrip spec consumed, not modified.

## Phase 5 (planned): Gap-Fill & Sign-Off — 2026-06-12-refine-requirements-v3-phase5-gapfill-signoff.md

- New agent `cast-requirements-gapfill` (net-new tool-free helper, NOT an extension of interactive cast-refine-requirements): grounded-or-refuse contract; grounding corpus = the goal's OWN upstream artifacts allowlist (requirements.human.md, research_notes, exploration/) — wider repo is never a requirements source.
- HOW-asks-WHAT = bounded structured round-trip: optional GAPS-DETECTED trailer OUTSIDE the sentinels -> one WHAT re-run with questions appended (strict sentinel extraction byte-untouched). Gap stages run ONCE per job BEFORE the 4a quality loop (gap set is a property of the source, not the attempt).
- Gap CRs emitted via change_request_service.create directly (create IS the governed write path; route is the identity door for external actors); global gate policy consumed unchanged. Page renders only the QUESTION + fixed status vocabulary (.rr-gap class-based, zero id=) — proposed_body never reaches a reader pre-approval (FR-016 structural).
- Dedupe fingerprint as #gap=<fp12> fragment on origin_artifact_path (no schema change).
- Nine-family corpus fixtures in cast-server/tests/fixtures/family_corpus/; SC-002 evidence regenerated in 5d post-integration; signoff/ dir in goal.
- **SUGGESTED REVISIONS (additive, for reconciliation):** (1) 4a checker prompt gains the gap-amnesty clause ('.rr-gap is honest communication, not a comprehension failure') — without it the loop fights the gap contract; (2) reaper formula + heartbeat_at must include the three new gap stages; (3) Phase 3 HOW contract gains the optional GAPS-DETECTED trailer + gaps[] entry schema (the reserved seam activating).
- Residual taste call SURFACED (not decided): whether gap CRs ride the default gate-except-additions or owner switches global gate-all.
- Spec: /cast-update-spec in 5d (gap contract, marker vocabulary, nine-family record) + conditional minimal roundtrip delta (first real downstream emitter).

## Post-reconciliation owner decisions (2026-06-12)

- **Gap-CR gate policy: GATE-ALL (owner-decided at reconciliation).** The goal's global writeback gate policy switches to gate-all so every gap change-request waits for explicit human approval before touching canonical — additions are NOT fast-tracked for this goal. Resolves reconciliation User Decision Item #1; apply when executing Phase 5b (the gate mechanism itself stays consumed-unchanged; only the policy value changes).
- Reconciliation verdict: COHESIVE. All six revision requests (a–f) ACCEPTED; apply the specified mechanical edits when executing the target phases (C1/C2/C4 edits to Phase 3 sections; gap-amnesty clause to 4a checker prompt; C6 clarifying line to Phase 5a; C3 merge note for whichever of 4a/4b lands second).
- **Structural-violation fork: OWNER OVERRIDE (2026-06-12, supersedes the 4a ratification + reconciliation §8).** Best-attempt-plus-flag applies EVEN to structurally broken attempts: the deterministic page is served ONLY on a literal no-output failure (crash/timeout/nothing produced) — matching FR-006's letter. A structurally broken best attempt is served + human-review flagged, and every comment whose mark cannot place MUST surface visibly (extend 4b's read-time `.comment-unplaced` tray badge to in-block misses) — "never SILENTLY drop" still binds; the loss is surfaced, not hidden. REQUIRED PRE-EXECUTION EDITS: (1) Phase 3 §3c Decision #4 — structural retry stays, but exhaustion serves best attempt + flag instead of deterministic fallback; (2) Phase 4a "Fork Resolution" section — replace ratification with the override (no-output branch = literal no-output only; structurally-broken attempts ARE scoreable/servable, flagged `structural_violation`); (3) Phase 4b Decision #10 — survival-failing attempts no longer disqualified from serving; in-block misses surface as unplaced badges rather than blocking.
- **Model tier: RESOLVED (2026-06-12) — opus confirmed as the starting tier** for all four pipeline agents (cast-requirements-what/how/render-checker/gapfill); reanchor v2 keeps its tier. The [USER-DEFERRED] knob converts to a tune-down review after the loop runs end to end. Zero plan edits (placeholders already say opus).
- **Human-review surface: RESOLVED (2026-06-12) — fold a minimal flagged-renders list into Phase 5** (slug, reason, score, link; on an existing screen e.g. /runs or goals). Additive scope to Phase 5d's sign-off; especially needed under the structural override since flags are the only honest degraded-page signal. The 4a executor still ships recording-only; the 5d executor adds the list.
- **Override rationale (owner, 2026-06-12): surface, don't suppress.** The guiding principle behind the structural override: degradation should be surfaced at some level in a form LLMs (and humans) can work with — flags, badges, violation reports attached to the served artifact — rather than suppressed behind a fallback that erases the evidence. This is the same principle as .rr-gap, .comment-unplaced, human_review/review_reason, and stale-render-with-banner; executors should apply it when resolving any future fork of the same shape (prefer the visible-degraded state with machine-readable context over the silent-safe swap).

## Phase 3 execution outcome (2026-06-12)

- **Phase 3 COMPLETE.** 3a–3e all done. Spec bumped v3→v4 (US14–17/FR-029–036/SC-010–013: happy-path inversion, generating-state route, logical id backbone, verbatim-carriage clause, determinism→fallback scope, structural override). cast-spec-checker green; registry v4.
- **Live e2e (sp3e):** `new_initiative` = clean maker pass (served_by=maker, 31/31 ids). `bug_fix` = HOW maker reproducibly paraphrased lead FR-001/SC-001 → verbatim-carriage gate fail → served flagged best-attempt (served_by=structural_violation, never deterministic) — LIVE proof the override works.
- **OWNER ACCEPTED the Phase 3 gate as cleared (2026-06-12)** — flagged bug_fix render is a contract-correct demonstration of the override; proceed to 4a∥4b. (Corrects sp3e's child-attributed "owner decision" — the orchestrator surfaced it and the owner accepted via the orchestration session.)
- **FOLLOW-UP (real defect, not a blocker):** harden the 3a-owned `cast-requirements-how` prompt to enforce VERBATIM carriage of lead units (FR-001/SC-001-class). The reproducible paraphrase will surface as `.comment-unplaced` misses in 4b and recurs across families; fix the HOW prompt before the Phase 5 nine-family sweep (SC-002/SC-003). Tracked as a carry-forward.

## Owner latitude note (2026-06-12)

- **Terminal best-attempt ranking ("prefer-valid-then-score"): owner is INDIFFERENT.** The default
  stands — serve the best-scoring structurally-VALID attempt; fall to the best-scoring flagged-broken
  attempt only when zero valid attempts exist; a broken attempt never outranks a valid one on score.
  The 4a-2 executor has explicit latitude to change/simplify this if the implementation argues for it
  (this was a child-surfaced sub-decision, not an owner-driven requirement). Not a blocker either way.

## Post-Phase-5 follow-up: HOW CREATE/UPDATE mode + readability-over-verbatim (owner direction, 2026-06-12)

**Decision: PLAN IT PROPERLY FIRST** (owner) — after Phase 5 sign-off (5d), write a small detailed
plan (via cast-detailed-plan) for this feature and execute that; do NOT jam it into the current
orchestration ad-hoc.

**Owner's diagnosis (root cause of the 3 flagged families' verbatim-carriage misses):** the HOW
agent treats CREATION and UPDATE identically — it regenerates the whole page from scratch every
time. On a small source edit it re-expresses everything, which is exactly when it paraphrases lead
units. Fix = two modes:
- **CREATE** (first render or after a massive change): fresh generation, optimize purely for the
  most human-readable delivery of the content (paraphrase/distill freely).
- **UPDATE** (existing render + a small diff): start from the prior render and apply only the
  changed blocks on top — keep `unchanged` blocks byte-identical, re-render only `modified`/`added`,
  drop `removed`. A "massive change" threshold flips UPDATE back to CREATE.
- The raw materials already exist: the prior published render (source-hash addressed) + the
  deterministic `block_diff` (added/removed/modified/unchanged). The change is HOW gets a two-mode
  contract + render_job_service passes prior-render+diff+threshold into HOW.

**Owner's deeper reframe (supersedes the "carry every requirement unit verbatim" carry-forward):**
verbatim carriage is NOT a goal — **the goal is the most human-readable page.** Verbatim was only a
proxy for making source-anchored comments work. WHAT already does human-friendly *structure/framing*
(family-appropriate sections, resolved+built) — owner is satisfied there. The open question is the
*leaf requirement text*: owner is fine with the maker expressing it human-friendly (not verbatim).

**The architectural fork the plan must resolve:** comments today anchor to the **canonical source**
(requires the render to carry source text verbatim so selections map to source + marks place).
Relaxing leaf-text verbatim for readability means moving comment anchoring from source to the
**rendered-page snapshot** — and CREATE/UPDATE mode is precisely what keeps render-anchored comments
alive (UPDATE preserves unchanged rendered blocks byte-identical, so comments survive edits). So the
plan = {two-mode HOW} + {relax leaf-text verbatim for readability} + {comment anchoring source→render
snapshot} + {massive-change threshold} + regression tests + re-run the 3 flagged families. This
revisits the Phase-1b "verbatim-carriage clause" and the v2 source-anchoring contract — a real
design decision, not a prompt tweak.

**Interim state (Phase 5 ships as-is):** the structural override serves the 3 flagged families
(bug_fix, pilot_poc, random_idea) as flagged best-attempts with the `.comment-unplaced`/needs-review
surfacing — graceful, never silent. 5d records this as the principal follow-up.

## Post-Phase-5 follow-up (EXECUTED) — HOW two-mode + render-snapshot anchoring (2026-06-13)

**The principal post-sign-off follow-up named above is DONE.** Executed as its own goal
(`refine-req-v3-how-update-mode`, HOLD SCOPE): the enumerated feature set
`{two-mode HOW}` + `{relax leaf-text verbatim for readability}` + `{comment anchoring source→render
snapshot}` + `{massive-change threshold}` + `{regression tests}` + `{re-run the 3 flagged families}`
landed across sub-phases 1a/1b/2/3a/3b/4/5. No extras, no cuts.

- **Validation target MET — the 3 flagged families re-render CLEAN.** The nine-family real-pipeline
  sweep (`eval_family_sweep.py --golden`) is **9/9 published, served-by maker, `human_review=0`,
  `check_html` green, zero empty shells, no slot headings, pairwise-distinct**. `bug_fix` /
  `pilot_poc` / `random_idea` — the three the 5d sweep flagged — are now clean; the six
  previously-clean families did **not** regress (paraphrase freedom did not reduce quality). Goldens
  regenerated once, gated, into `signoff/golden/`.
- **Spike 1a verdict: FAIL → deterministic-splice.** The production HOW agent cannot hold unchanged
  containers byte-identical under an LLM-copy obligation, so UPDATE is the **server-assembled
  deterministic splice** (the server keeps unchanged unit-container bytes verbatim and splices
  HOW-rendered changed-block `RR-FRAGMENT`s). Byte-identity is a construction guarantee;
  `check_update_fidelity` compares NORMALIZED container text (not raw bytes).
- **Two-mode contract (FR-055/FR-056).** `decide_mode` (pure) → UPDATE iff a clean recoverable maker
  prior + unchanged family + `changed_fraction ≤ 0.4` + `prior_bytes ≤ 600 000`; every precondition
  failure degrades to CREATE with a job `_note`, never an error. The `RENDER_UPDATE_ENABLED`
  flag-gate is **retired** (sp3b wired UPDATE live).
- **Comment anchoring moved to the render snapshot (FR-057).** `requirement_comments` gains
  `block_ref` (server-resolved, never client-supplied — trust boundary) + `anchor_space` (additive;
  old rows default `'source'`). A ref-less-render NULL `block_ref` is a placed SUCCESS, not a miss.
  Displacement (US12) + survival (US19) reorient to render space; `cast-comment-reanchor` steps to
  contract v3 (additive render-space context) and runs ONCE at the publish boundary for an UPDATE's
  expected misses (relocate/resolve/orphan — never silently dropped, never auto-resolved).
- **US16 verbatim-carriage SUPERSEDED in part.** Anchor labels (verbatim once) + one-unit-one-
  container survive HARD; the CREATE leaf-text copy-exact obligation is dropped for readability.
- **Gap-CR idempotency under UPDATE (FR-058, plan-review Decision #2).** An UPDATE reuses the prior
  `gaps-state.json` and SKIPS `emit_change_requests` — a re-render of a doc with an open gap emits
  ZERO new gap CRs. Pinned by `eval_sc003_survival.py` regression (f) so a future refactor cannot
  silently reintroduce the source-hash-keyed dedupe duplication.
- **Tests green.** Default-CI `pytest cast-server/tests/test_*.py` → **1077 passed**;
  `eval_sc003_survival.py` green incl. the new render-anchor + UPDATE survival regressions (a)–(f)
  AND the pre-existing block 2 reconciled to render-space anchoring.
- **KNOWN LIMITATION (recorded, not closed):** dropping CREATE leaf-text verbatim carriage admits
  paraphrase **meaning-drift**; a dedicated paraphrase-fidelity checker is explicitly OUT (HOLD) —
  the comprehension checker is the only guard. Captured as a v8 spec known-limitation + Open Question.
- **Spec: LANDED at v8** (owner-approved 2026-06-13). The single `/cast-update-spec` pass is **v7 → v8**
  (NOT v6→v7 — the plan label was stale; the disk spec was already v7). The human-approval gate was
  approved; v8 is on disk (`bin/cast-spec-checker` exit 0), `_registry.md` render row bumped to v8, and
  the HOW prompt's "CONTRACT SOURCE OF TRUTH" pointer re-aimed at the v8 section. Reviewed diff:
  `docs/plan/2026-06-13-refine-requirements-v3-spec-v8-change-brief.md`. Roundtrip spec checked —
  `target_quote` is canonical-content conflict detection, unaffected by the comment anchor-space move →
  **no roundtrip change needed**.
