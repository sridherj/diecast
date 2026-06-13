# Reconciliation Report — refine-requirements-better-rendering-v3 fan-out planning

**Date:** 2026-06-12
**Scope:** Cross-check of the six sub-phase plans produced by independent child agents.
**Inputs:** `_v3_subphase_extracts.md`, `refine-requirements-better-rendering-v3-decisions-so-far.md`,
`docs/goal/refine-requirements-better-rendering-v3/plan.collab.md`, plus targeted spot-checks of
the individual plan files (cited by line where load-bearing).
**This pass edits no plan file.** Every accepted revision below names the exact file + section an
executor must update when applying it.

---

## 1. Cross-Sub-Phase Interface Table

| Phase | Produces | Consumed By |
|---|---|---|
| 1 (spikes) | Validated quote-anchored logical backbone; 1b mark-placement harness semantics (Python re-impl of `requirements_comments.js` tree-walk + `indexOf`); "clearly beats" rubric; sharpened verbatim-carriage obligation | 3b (productionizes harness in `maker_gate.py`), 4b-1 (placement semantics), 4a (rubric), 3e spec pass (verbatim-carriage clause) |
| 2 | `strip_inline_markdown` (pure, in `goal_card.py`, import-stable); `_split_first_sentence`; hardened deterministic fallback substrate; commenting affordance | 3b (`check_html` verbatim-carriage derivation — **hard dependency, 2a → 3b**); 3c (fallback publishes ungated on the trust the substrate passes `check_html` — pinned by 3b's T1 test) |
| 3 | `cast-requirements-what`/`-how` agents; WHAT-doc contract (YAML front matter: total id-mapping, `unmapped_refs`, reserved `gaps: []`); HOW sentinels contract; `maker_gate.py` (`check_what_doc`, `check_html` → `GateReport`); `render_job_service.py` with named stage seam `run_what → gate_what → run_how → gate_html → publish`; `render_jobs` table; `RENDER_JOBS_DIR` + stage timeouts in `config.py`; generating-state route; `AgentRunner` seam | 4a (inserts `run_checker → decide_quality` between `gate_html` and `publish`; wraps the structural gate; reads `render_jobs`); 4b (widens `gate_html` report; consumes WHAT id-mapping + verbatim-carriage + walker); 5 (activates `gaps[]`; inserts gap stages between `gate_what` and final `run_how`) |
| 4a | `cast-requirements-render-checker`; `checker_verdict.py` (binary PASS + code-side canonical score); quality loop + terminal-state policy table; `render_jobs` flag columns (`human_review`, `review_reason`, `published_attempt`, `published_score`, `heartbeat_at`); served-artifact envelope flag; knobs `QUALITY_MAX_ATTEMPTS=15` / `QUALITY_MAX_WHAT_REWORKS=2` / `QUALITY_STRUCTURAL_STOP=3`; ratified+sharpened fork (no-output classification only while zero structurally-valid attempts) | 5b (checker prompt gains gap amnesty), 5c (reads `human_review` as per-family quality signal — named in 4a's hand-off), 5d (sweep) |
| 4b | `check_comment_survival` (pure, in `maker_gate.py`); widened `gate_html` report (carriage + survival); cast-comment-reanchor CONTRACT V2 (extend-in-place, optional new inputs); narration storage + `/changes` sibling `narration` key; `.comment-unplaced` derived tray badge | 4a's loop (consumes the widened report as the structural gate it wraps — by construction, 4a wraps "whatever `gate_html` reports"); 5b (gap markers must not break survival — 5b verification covers it) |
| 5 | `cast-requirements-gapfill`; gap stages (`ask_what`, `run_gapfill`, `validate_evidence`, `emit_change_requests`) once-per-job pre-loop; `gaps[]` entry schema + HOW `GAPS-DETECTED` trailer (outside sentinels); gap CRs (kind gate-pinned to `addition`) via `change_request_service.create`; `.rr-gap` markers; nine-family corpus; SC-001..SC-008 sweep + final spec reconciliation | Sign-off (5d is terminal) |

**Full reconciled stage order** (all three plans agree, verified against plan text):
`run_what → gate_what → [run_how first/probe + trailer harvest → ask_what (≤GAPFILL_ASK_ROUNDS) → re-gate_what → run_gapfill → validate_evidence → emit_change_requests]₅ → run_how final → gate_html (carriage + gap-marker correspondence + survival₄ᵦ) → [run_checker → decide_quality]₄ₐ loop → publish`

## 2. Canonical Naming Table

**No conflicts found — no table needed.** All shared names are used identically across plans:
`render_job_service.py`, `maker_gate.py`, `render_jobs`, `RENDER_JOBS_DIR`, `strip_inline_markdown`,
`gate_html`, stage-function names, agent names (`cast-requirements-what/-how/-render-checker/-gapfill`,
`cast-comment-reanchor` kept under contract v2), knob names (`QUALITY_*`, `GAPFILL_ASK_ROUNDS`),
marker classes (`.rr-gap`, `.comment-unplaced`). The only near-miss is Phase 2's
`_split_first_sentence` vs the high-level plan's older `_first_sentence` — a refinement of the
high-level sketch, not a cross-sub-phase conflict.

## 3. Conflict List (with recommended resolutions)

Severity counts: **0 critical / 2 major / 4 minor.** All have mechanical resolutions; none
requires re-planning.

| # | Sev | Conflict | Resolution |
|---|---|---|---|
| C1 | Major | **Reaper-ceiling formula too small once the 4a loop exists.** Phase 3 §3c derives the ceiling from `what_timeout + how_timeout` doubled for one structural retry (phase3 plan ~line 322); 4a's worst case is ~10× larger; Phase 5 adds three more stages. A live looping job would be reaped mid-flight. | Apply revision (a): ceiling becomes a function of the **configured stage-timeout list** so 4a/5 extend it by registering stages, zero formula edits. Edit target: phase3 plan, §"Sub-phase 3c", reaper bullet + Plan Review A2 record. |
| C2 | Major | **Container-text walker not exposed as a shared helper.** Phase 3 §3b embeds the HTMLParser descendant-text-concatenation walker inside `check_html` with no named public function (only mention: phase3 ~line 237); 4b-1 declares a hard no-copy prerequisite on importing it. As written, 4b-1 would have to copy it. | Apply revision (b): 3b exposes the walker as a module-level public helper in `maker_gate.py` (e.g. `container_text_index(html) -> …`), unit-tested independently. Edit target: phase3 plan, §"Sub-phase 3b", `check_html` verbatim-carriage bullet + Outcome line. |
| C3 | Minor | **Extract drift:** 4b's extract omits `render_job_service.py` from Files Modified, but the 4b plan edits it at the `gate_html` seam (4b plan lines 198, 236, 503). The 4a∥4b parallel edit to the same file is real. | No plan edit. The collision is already managed by 4b's seam discipline (4b widens `gate_html`'s report only; 4a inserts stages after it) and pinned by 4b's T3 test (line 646). Merge note for the executor of whichever of 4a/4b lands second. |
| C4 | Minor | **`heartbeat_at` ownership wrinkle:** 4a folds the column into "4a-2's `render_jobs` migration" while asking Phase 3's per-job thread to write it — Phase 3 executes first and the column wouldn't exist. | Since Phase 3 *creates* `render_jobs` net-new, put `heartbeat_at` in Phase 3's initial CREATE TABLE (no migration needed) and Phase 3's thread writes it at stage boundaries from day one; 4a-2's migration keeps only the four flag columns. See revision (a) verdict. |
| C5 | Minor | **`GAPFILL_MAX_GAPS` (config, default 5)** appears only in the Phase 5 plan (5a, WHAT gap-detection cap) — invisible to the extracts and other plans. | Purely additive config knob; lands in `config.py` alongside `GAPFILL_ASK_ROUNDS` during 5a. No conflict; recorded here so the 5d drift sweep checks it. |
| C6 | Minor | **Probe-`run_how` attempt accounting:** Phase 5's first/probe `run_how` (trailer harvest) precedes the quality loop; 4a counts attempts via `QUALITY_MAX_ATTEMPTS`. Whether the probe debits the loop budget is unstated. | One clarifying line when 5a is executed: the pre-loop probe `run_how` does **not** debit `QUALITY_MAX_ATTEMPTS` (mirrors the already-ruled `GAPFILL_ASK_ROUNDS` ⊥ `QUALITY_MAX_WHAT_REWORKS` independence, phase5 Plan Review A2). Edit target: phase5 plan §5a pipeline-stages bullet (stage 2). |

## 4. Scope Gaps & Overlaps

**Gaps:** None found. Every later-phase consumption traces to a producer: `strip_inline_markdown`
(2a), walker (3b — after C2's edit), `gaps[]` seam + sentinel rules (3a/3c), structural-gate seam
(3c), flag columns (4a-2), survival report (4b-1), `verbatim_locate` reuse for `validate_evidence`
(existing v2 helper, confirmed by phase5 Plan Review CQ2). The comment-fetch wiring for the
survival gate, which the extracts left ambiguous, is owned: 4b-1 widens the `gate_html` stage and
fetches open comments there (4b plan line 198), keeping `check_comment_survival` pure.

**Overlaps (the three watched files):**
- `maker_gate.py` — 3b creates; 4b-1 adds `check_comment_survival` (pure, additive); 5a/5b add
  gap-marker extensions. Strictly additive, sequential except 4a never touches it. **Clean.**
- `render_job_service.py` — 3c creates; 4a-2 inserts stages after `gate_html`; 4b-1 widens
  `gate_html`'s report (parallel with 4a — disjoint seams, see C3); 5a inserts gap stages between
  `gate_what` and final `run_how`. All stage additions at the documented seam, no rewrites. **Clean
  with the C3 merge note.**
- `config.py` — 3c adds `RENDER_JOBS_DIR` + stage timeouts; 4a adds the three QUALITY knobs;
  5a adds `GAPFILL_ASK_ROUNDS` + `GAPFILL_MAX_GAPS`. Disjoint keys, additive. **Clean.**

**Shared infrastructure — single-implementation discipline holds everywhere checked:** one
markdown stripper (Phase 2's, imported by 3b), one walker (3b's, shared per C2), one locate
(`verbatim_locate` reused by 5a), one reaper/heartbeat mechanism (Phase 3's, formula extended by
config registration per revisions a/e — 4a and 5 both extend the same mechanism the same way,
no competing designs).

## 5. Revision-Request Adjudications (grouped by target phase)

All six were claimed additive by their authors. Verified: (b)–(f) are genuinely additive; **(a) is
a correction** (it changes Phase 3's reaper formula), self-labelled as such by 4a ("correction,
not a decision reversal") — it overturns no owner decision and is safe.

### Target: Phase 3 plan (`2026-06-12-refine-requirements-v3-phase3-maker-pipeline.md`)

- **(a) 4a → 3: reaper ceiling from configured stage list; reaper releases semaphore slot; heartbeat at stage boundaries — ACCEPT-WITH-EDIT.**
  - Ceiling-from-stage-list: ACCEPT as written (4a already specifies "implement the formula as a
    function of the configured stage list so 4a's stages extend it without edits"). Update §3c
    reaper bullet (~line 322) + Plan Review A2 record (~line 610).
  - Semaphore release on reap: ACCEPT. Update §3c (reaper bullet + the P1 in-flight-semaphore
    bullet, ~line 316).
  - Heartbeat: ACCEPT **with this edit** — move `heartbeat_at` into Phase 3's initial
    `render_jobs` CREATE TABLE (the table is net-new in 3c; no migration ordering problem) and
    have the per-job thread write it at every stage boundary from day one. 4a-2's migration then
    adds only `human_review`/`review_reason`/`published_attempt`/`published_score`. Update: phase3
    §3c `render_jobs` bullet; phase4a §"Sub-phase 4a-2" migration bullet (drop `heartbeat_at` from
    the migration, keep the staleness-detector semantics).
- **(b) 4b → 3: container-text walker exposed as shared helper — ACCEPT.** Hard no-copy
  prerequisite for 4b-1; currently unmet (C2). Update phase3 §"Sub-phase 3b": name the walker as a
  public, independently-tested module-level helper in `maker_gate.py`; 4b-1 imports it.
- **(f) 5 → 3: HOW contract gains optional GAPS-DETECTED trailer outside sentinels; WHAT `gaps[]` entry schema at the reserved seam — ACCEPT (zero Phase 3 executor action).**
  Phase 3 reserved exactly these seams: `gaps: []` is already in the front-matter schema, and the
  trailer sits *after* `<!-- END RENDER -->`, outside 3c's strict first-BEGIN→first-END extraction
  window, so Phase 3's code is byte-untouched. Implementation belongs to phase5 §5a (which already
  specifies it). Optional documentation-only edit: one forward-reference line in phase3
  §"Sub-phase 3a" contract bullets noting the seam activates in 5a.

### Target: Phase 4a plan (`2026-06-12-refine-requirements-v3-phase4a-quality-gate.md`)

- **(c) 4b ↔ 4a seam — survival-failing attempt = structurally INVALID, evaluated before `run_checker` — ACCEPT (compatible as written).**
  Verified both sides: 4b pins it explicitly (seam pin + T3 test, 4b plan lines 503/521/646);
  4a never names "survival" but states the binding contract generically — "structural gate every
  attempt must pass BEFORE it is eligible for checker scoring" and "only structurally-valid
  attempts ever reach the checker / 'best-scoring' presupposes a score" (4a plan lines 80,
  136–137). 4a wraps *whatever `gate_html` reports*, so 4b's widened report is absorbed by
  construction. Recommended (non-blocking) one-line edit to phase4a §"Sub-phase 4a-2" loop
  description acknowledging the report is widened by 4b-1 (carriage + survival) when both land.
- **(d) 5 → 4a: checker prompt gains the gap-amnesty clause — ACCEPT.** Additive and necessary:
  without it the loop literally fights the gap contract (a gap-bearing render keeps failing
  comprehension and reworking against gaps the source genuinely has). Update phase4a
  §"Sub-phase 4a-1" (checker prompt definition, ~line 153ff) + the checker eval fixtures in
  `eval_quality_gate.py` so the amnesty is pinned, not just prompted: ".rr-gap markers are honest
  communication of a source gap, not a comprehension failure of the render."
- **(e) 5 → 3/4a: reaper formula + heartbeat include the three gap stages; `GAPFILL_ASK_ROUNDS` ⊥ `QUALITY_MAX_WHAT_REWORKS` — ACCEPT (largely satisfied-by-construction once (a) lands).**
  With the ceiling implemented as a function of the configured stage list, Phase 5 only registers
  its stages (`ask_what` re-run, `run_gapfill`, `validate_evidence`/`emit_change_requests`) in
  that list — phase5 §5a already plans this. Heartbeat-at-each-new-stage-boundary follows from the
  same stage-runner hook. Counter independence is already ruled in phase5 Plan Review A2 and
  recorded in 5a stage 3. Executor updates: phase3 §3c (stage-list comment noting later phases
  register stages), phase4a §4a-2 (same), phase5 §5a (no change — already correct).

### Target: Phase 5 plan — none requested. (C6's clarifying line is this reconciliation's own
minor addition, target phase5 §5a stage 2.)

## 6. Dependency Graph (updated with discovered edges)

```
Phase 1 (1a ∥ 1b spikes) ───────────────┐
                                        ├──► Phase 3 (3a ∥ 3b → 3c → 3d → 3e) ──┬──► 4a (4a-1 → 4a-2 → 4a-3) ──┐
Phase 2 (2a → 2b → 2c, ships ahead) ────┤        ▲                              └──► 4b (4b-1 → … → 4b-4) ─────┴──► Phase 5 (5a → 5b → 5d; 5c ∥ 5a/5b)
              │                         │        │
              └── 2a strip_inline_markdown ──────┘   (HARD edge: 2a → 3b, not just "Phase 2 ∥ Phase 1")
```

Hidden edges surfaced by this pass:
- **2a → 3b** (hard): `strip_inline_markdown` must exist and be import-stable before the maker
  gate's verbatim-carriage check. Phase 2 is "independent / ships ahead" at the phase level, but
  2a specifically is on Phase 3's critical path.
- **3b walker → 4b-1** (hard, after revision b): shared helper, no-copy.
- **4b-1 ∥ 4a-2 on `render_job_service.py`**: disjoint seams (widen `gate_html` vs insert after
  it); the second-lander does the mechanical merge (C3).
- **4a-2 heartbeat semantics → Phase 3 thread**: dissolved by moving `heartbeat_at` into 3c's
  CREATE TABLE (revision a edit).

Critical path unchanged: **1 → 3 → {4a ∥ 4b} → 5**, ≈13–19 sessions. Phase 3 (5–7) is correctly
the heaviest. Mild watch-item: Phase 5 packs a new agent + three pipeline stages + nine-family
corpus + full SC sweep into 3–5 sessions; 5c's parallelism with 5a/5b makes it plausible, but it
is the most likely phase to overrun — no re-scope needed now.

## 7. Verification Chain

Each phase's verification proves its own outcome (spot-checked: 3b's gate↔golden consistency +
the T1 "live deterministic render passes `check_html` in full" pin guarding the ungated fallback;
3c's reaper test; 4a-3's fault-injection of every terminal branch; 4b-1's T3 structural-branch
seam pin; 5a's `validate_evidence` trust boundary with `verbatim_locate`).

SC sweep coverage across phases (5d runs the consolidated sweep):
| SC | Proven by |
|---|---|
| SC-001 cold reader | 4a checker (verdict = strict superset of the v2 cold-reader shape) + Phase 1 rubric; 5d sweep |
| SC-002 nine families distinct | 5c corpus + golden renders, evidence regenerated in 5d |
| SC-003 zero new comment orphans | 4b-4 end-to-end (Phase 1b spike de-risked) |
| SC-004 no-output → deterministic | 4a-3 fault injection (branch built in 3c) |
| SC-005 cache/instant cached views | Phase 3 (source-hash readiness; 3d/3e verification) |
| SC-006 unprompted commenting | Phase 2 (with the no-browser static-verdict + human-eyeball carry-forward, per project note) |
| SC-007 gap marked or supplied, never silent | Phase 5 gap-injection (5a/5b) |
| SC-008 non-convergence → best attempt + flag | 4a-3 (forced never-pass) |

All eight covered; no criterion is orphaned and none is double-owned in conflicting ways.

## 8. Owner-Decision Compliance (spot-check)

| Seed decision | Status |
|---|---|
| Logical backbone + quote-anchored DOM, no `id=` | ✅ 3b enforces zero-`id` in `check_html`; 4b stays in `Block.ref` space; `.rr-gap`/`.comment-unplaced` are class-based, zero `id=` |
| Background job + generating state | ✅ 3c/3d (4s poll, `<noscript>`, stale-render-with-banner) |
| Net-new agents + family-communication sections | ✅ what/how/checker/gapfill all net-new; reanchor extended-in-place (the decision allowed "extends or replaces"); `check_what_doc` makes the no-US/FR/SC-slots rule checkable |
| Gap-fill via the v2 gate unchanged | ✅ with a note: 5b calls `change_request_service.create` directly (create IS the governed write path; the route is the identity door for external actors). Gate flow consumed byte-unchanged. The *policy* interaction is the surfaced taste call (§9) |
| Best-attempt-plus-flag on quality non-convergence | ✅ 4a, ratified + sharpened. The Phase-3 flagged fork (structurally-unusable = no-output branch) is **ratified at this reconciliation too**: it applies only while zero structurally-valid attempts exist; serving a structurally-broken page would violate the harder verbatim-id/anchoring constraints, so this honors the owner decision's intent exactly |
| Deterministic fallback only on true no-output | ✅ (same sharpening; checker-unavailable serves latest valid attempt + flag, never the plain page; fallback page never LLM-gated) |
| Quality loops never cost-capped | ✅ `QUALITY_MAX_ATTEMPTS=15` etc. are the sanctioned high anti-infinite-loop ceiling; Phase 3's in-flight semaphore is explicitly framed (and accepted here) as resource-safety, not a cost cap |
| [USER-DEFERRED] model tier left undecided | ✅ all plans: `model:` read from each agent's `config.yaml` as a placeholder + explicit `[USER-DEFERRED]` tuning-knob comment (phase3 ln 534, phase4a ln 67/593, phase4b ln 531, phase5 5a); no plan decides the tier |

No violations found.

## 9. User Decision Items

1. **Global gate policy for gap change-requests (the Phase 5 residual taste call — surfaced, not
   decided here).** Gap CRs are gate-pinned to `kind: addition` (phase5 Plan Review A1), and under
   the v2 default **gate-except-additions** policy, additions are fast-tracked — meaning an
   approved-by-default gap CR could land in canonical without a human click. That sits in visible
   tension with the seed decision's "propose → notify → human gate" phrasing, even though the gate
   *mechanism* is consumed unchanged. Options: (a) keep the default (gap CRs auto-apply as
   additions; notification still fires; lowest friction), or (b) switch the goal's global policy
   to **gate-all** (every gap CR waits for explicit approval; matches the seed decision's letter;
   adds a human step per gap). This is owner taste — please decide before 5b executes.
   **RESOLVED 2026-06-12 (owner): option (b) — GATE-ALL.** Every gap CR waits for explicit
   approval; recorded in the decisions-so-far log for the 5b executor.
2. **RESOLVED 2026-06-12 (owner): OVERRIDE.** The owner prefers best-attempt-plus-flag even for
   structurally broken attempts — deterministic fallback fires ONLY on literal no-output
   (crash/timeout/nothing), per FR-006's letter. Never-SILENTLY-drop still binds: in-block
   placement misses surface via the read-time `.comment-unplaced` badge instead of blocking.
   This supersedes §8's ratification and adds three REQUIRED pre-execution edits:
   Phase 3 §3c Decision #4 (exhausted structural retry → best attempt + flag, not fallback);
   Phase 4a Fork Resolution (replace ratification with override; broken attempts scoreable,
   flagged `structural_violation`); Phase 4b Decision #10 (survival-failing attempts servable;
   in-block misses surface as unplaced badges). See decisions-so-far for the canonical wording.
   *(Original awareness note follows.)* The Phase-3 structural-violation fork is hereby ratified at
   reconciliation level with 4a's zero-valid-attempts sharpening (§8). If you ever prefer
   best-attempt-plus-flag even for structurally broken first attempts, say so before 4a executes —
   the plans as written never serve a structurally broken page.

---

## Final Verdict

`VERDICT: COHESIVE`

All six plans interlock at the documented seams; the two major findings (reaper-ceiling formula,
shared walker helper) were already self-identified by the plans' own revision requests and have
purely mechanical merges; all six cross-phase revision requests are ACCEPTED (two with small
specified edits); no owner seed decision is violated; one owner-level taste call (gap-CR gate
policy) is queued for the user before 5b.
