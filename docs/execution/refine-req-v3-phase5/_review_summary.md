# Review Summary: refine-req-v3-phase5

Review scope: **SMALL CHANGE** (max ~1 issue per section), run as a focused self-review by the
execution-plan author. The **source plan**
(`2026-06-12-refine-requirements-v3-phase5-gapfill-signoff.md`) already passed a BIG-CHANGE
`cast-plan-review` (9 issues / 9 resolved — see its appendix: A1–A3, CQ1–CQ2, T1–T3, P1). This pass
targets only **split-introduced** risks (seam mechanics, the owner-edit application, cross-sub-phase
contracts, the SC-range correction) rather than re-reviewing the design.

## Load-bearing assumptions — VERIFIED against the live codebase (2026-06-12)

These three claims are load-bearing across the split; all confirmed present, so the executors import
rather than assume:

1. **`verbatim_locate` exists** at `cast-server/cast_server/services/change_request_service.py:245`
   (the v2 writeback backstop's locate). 5a's `validate_evidence` **imports it from there** (it is a
   service-layer helper) — single locate implementation (CQ2). Baked into sp5a Step 5a.6 + manual checks.
2. **The four `render_jobs` flag columns exist** (4a-2 migration): `human_review`, `review_reason`
   (vocabulary already includes `structural_violation`), `published_attempt`, `published_score`
   (schema.sql:229–232). 5d's flagged-renders list reads these — **no new column / write path** needed.
3. **The `gaps: []` seam is reserved** in `agents/cast-requirements-what/cast-requirements-what.md:99`
   ("RESERVED Phase-5 seam … ALWAYS empty in Phase 3, zero behavior"). 5a activates it by attaching
   the entry schema + behavior — the seam working exactly as Phase 3 designed.

## Open Questions — NONE BLOCKING (the genuine forks were owner-resolved before the split)

The two judgment calls the split surfaced were put to the owner and **resolved** before authoring:

1. **Sub-phase granularity.** RESOLVED (owner, 2026-06-12): **mirror the source plan's 5a/5b/5c/5d**
   rather than splitting the heavy 5a. Keeps ids stable with the cross-phase decision log (which
   references 5a–5d verbatim) and matches how 4a/4b were split. 5a stays large but cohesive (one agent
   + its stages, sequential-internal — splitting would just create a shared-`maker_gate`/`render_job_service`
   seam with little parallelism gain).
2. **GATE-ALL mechanism.** RESOLVED (owner, 2026-06-12): **flip the `config.py` default** of
   `WRITEBACK_GATE_POLICY` → `"gate-all"` (env override preserved) rather than leaving the default and
   relying on a deployment env var — so the resolved decision is reflected in committed code. The
   convergence tests still set policy explicitly per-lane. Baked into sp5b Step 5b.1.

## Review Notes by Sub-Phase

### 5a (gap contract + ask loop)
- **Architecture:** gap machinery is stage additions at the documented Phase-3 seam (between
  `gate_what` and the FINAL `run_how`); the gapfill agent follows the established tool-free carve-out;
  the service owns all I/O + validation, the agent stays pure text-to-text. The `GAPS-DETECTED` trailer
  lives OUTSIDE the sentinels so strict extraction is byte-untouched. ✓
- **Counters (A2/C6):** the probe `run_how` ⟂ `QUALITY_MAX_ATTEMPTS` and `GAPFILL_ASK_ROUNDS` ⟂
  `QUALITY_MAX_WHAT_REWORKS` are called out in config comments AND pinned by an explicit
  counter-independence test (Verification) — so the executor can't silently collapse them at the merge. ✓
- **Trust boundary:** `validate_evidence` reuses the verified `verbatim_locate`; the T2 parity test
  pins whitespace-tolerant validate vs. substantive demote. ✓
- **Split risk (shared `cast-requirements-what` with 5c):** flagged — 5a owns the gaps-schema +
  gap-detection block; 5c owns the per-family vocabulary block; additive/disjoint; second lander
  mechanically merges. Non-blocking (the two blocks never overlap). ✓
- **Scope discipline:** `emit_change_requests` is explicitly a `gaps-state.json`-only **stub** in 5a;
  `change_request_service` is untouched until 5b — prevents the executor from wiring emission +
  GATE-ALL early. ✓

### 5b (gate reconciliation + markers)
- **Architecture:** no new writer, no lighter path — the emitter calls `create(...)` directly; the
  gate/policy/conflict/writeback/outbox/relay are byte-unchanged (a `git diff --stat` check on
  `change_request_service.py` is in the manual checks). ✓
- **GATE-ALL application:** the flip is one config line; `gate_status` already returns `"proposed"`
  under `gate-all` (verified — no gate edit). The **global blast radius** (all writebacks, not just gap
  CRs) is stated as the owner-chosen behavior, not a surprise. ✓
- **Tests (T1):** the gated-lane convergence test is the PRIMARY regression (it is the live lane under
  GATE-ALL); the fast-track auto-apply convergence is kept as a *parametrized mechanism* test so the
  gate-consumed-unchanged guarantee is still proven. This is the most important split correction vs.
  the source-plan body (which framed auto-apply as the default lane). ✓
- **FR-016 structural:** `proposed_body` never on the page — pinned by a grep in manual checks +
  the marker-vocabulary table (question + fixed status only). ✓
- **Checker amnesty:** flagged to **reconcile with SC-014's existing anticipation** (grep first; don't
  duplicate). ✓

### 5c (nine-family corpus + golden renders)
- **Architecture:** the sweep exercises production code paths via the established eval-harness pattern;
  no test-only render path. Gap machinery stays dormant (`gaps[]` empty) so 5c is genuinely parallel to
  5a/5b. ✓
- **Override coupling:** the terminal-state assertion (∈ {published, published+human_review}; never
  fallback) is written through the structural override — a family reaching the deterministic page is a
  hard finding, not a pass. ✓
- **Integrity:** authored-not-fiction rule + per-fixture provenance header; the `random_idea` floor is
  honest-about-thinness (not padded); `human_review` is a finding to surface, never suppressed. ✓
- **Carry-forward:** the Phase-3 HOW-prompt lead-unit paraphrase follow-up is flagged as the fix lever
  if a family shows `.comment-unplaced` misses (don't redesign the recipe around it). ✓

### 5d (SC sweep + spec + flagged list + sign-off)
- **THE split correction:** the sweep is **SC-001…SC-018**, not the source-plan body's SC-001…SC-008
  (the spec grew to v6 across 3/4a/4b). The eighteen-row table cites the existing named test/eval for
  SC-009…SC-018 and runs the gap/family ones fresh — flagged in Execution Notes as the easiest way to
  under-deliver. ✓
- **Flagged-renders list:** the owner-resolved 5d deliverable — read-only, on an existing screen, from
  the verified 4a flag columns (no new write path/column). The one additive-behavior exception in an
  otherwise sweep-and-record sub-phase. ✓
- **Drift sweep:** extends the reaper-ceiling + heartbeat checks to the new gap stages; verifies the
  C5 knobs are read (not dead config), the single-helper discipline holds, the amnesty line is present,
  and GATE-ALL is applied. ✓
- **Spec consistency:** all 5a/5b flags resolve in one render-spec pass; the roundtrip touch is minimal
  + conditional (or a recorded no-change rationale); two `/cast-update-spec` passes under standing
  approval (diff still shown). SC-016's "that is Phase 5d" pointer is reconciled by the update. ✓
- **Process:** the sign-off enumerates every flag + carry-forward + deferred item — the override makes
  the flagged-list + the enumerated flags load-bearing ("surface, don't suppress"). ✓

## Verdict

**4 sub-phases / 2 forks (both owner-RESOLVED + baked in) / 0 blocking.** The split is faithful to the
source plan and correctly applies the owner-resolved edits: **GATE-ALL** (config flip, 5b),
**flagged-renders list** (5d), **C5** `GAPFILL_MAX_GAPS` (5a), **C6** probe-`run_how` independence
(5a), the **SC-001…SC-018** sweep-range correction (5d), the **opus** gapfill tier (5a), and the
**structural-violation override** (throughout). Three load-bearing helpers/columns/seams were verified
present in the live codebase. Ready for execution.
