# Execution Manifest: Product Revamp Diecast — Phase 2c Stage-Model Research

## How to Execute

Each sub-phase runs in a **separate Claude context**. The four sub-phases are **strictly
sequential** on the critical path (2c.1 → 2c.2 → 2c.3-authoring → 2c.4-encode) — never run them in
parallel. For each sub-phase:
1. Start a new Claude session (or dispatch a `cast-subphase-runner`).
2. Tell Claude: "Read `docs/execution/product-revamp-diecast-phase2c-stage-research/_shared_context.md`,
   then execute `docs/execution/product-revamp-diecast-phase2c-stage-research/spN_name/plan.md`."
3. After completion, update the Status column below.

**This is a RESEARCH spike — output is a markdown note, not code** (the one exception is sp4, the
org.js encode). **FULL AUTONOMY (owner-approved):** no user questions, no approval gates, no idle
waits; pick the recommended option at every gate and propagate the directive to any child agent.

**Binding constraints (carried in `_shared_context.md` and every sub-phase file):**
- **NO TESTS** anywhere — no test files, suites, harnesses, or CI in any sub-phase. Verification
  is manual file-inspection / click-through only, plus (sp4 only) the generator's in-code
  invariant gate (NOT a test file) and a JSON-parse check.
- **Derive-first, compare-after** (anti-anchoring): dropped placeholder steps are banned as search
  seeds (sp1) and as derivation inputs (sp2); comparison happens only in sp2's ledger.
- **≥1 hands-on practitioner account per family** is mandatory (sp1) — the owner's failure mode is
  an evidence base built from methodology texts.
- **`file://` plain-JSON constraint:** the `stageModels` encoding is plain-JSON data (no functions)
  so `org.js` loads as a frozen classic script from disk.
- **Reconciliation F1 (binding):** the org.js `stageModels` rewrite is owned by **2c**, executed
  via 2a's generator, scheduled **after 2a.1 (generator exists) and before Phase 3 dispatch** —
  hence the authoring/encode split (sp3 has no 2a dependency; sp4 is gated on 2a's artifacts).
- Binding context docs the runner MUST read first:
  `docs/plan/product-revamp-diecast-decisions-so-far.md` (run config, owner-locked inputs,
  NO-TESTS, cross-phase contracts, Reconciliation F1–F5),
  `docs/plan/2026-06-11-product-revamp-diecast-phase2c-stage-research.md` (the plan), and
  `docs/plan/2026-06-12-product-revamp-diecast-reconciliation.md` (F1).

## Sub-Phase Overview

| # | Sub-phase | Directory/File | Depends On | Status | Notes |
|---|-----------|----------------|-----------|--------|-------|
| 1 | Practitioner Evidence Base — mine + 4 parallel scans (2c.1) | `sp1_evidence_base/` | — | Done | Output: `sp1_evidence_base/evidence-base.md`. 4 family scans parallel internally; ≥3 refs + ≥1 practitioner-account each |
| 2 | Spine Derivation & Practicality Pressure-Test (2c.2) | `sp2_spine_derivation/` | 1 | Done | Output: `sp2_spine_derivation/spine-derivation.md`. 4–7 steps/family, five-test rubric, dropped-placeholder ledger |
| 3 | Canonical Note + Encoding Contract + Self-Eval Gate (2c.3 authoring) | `sp3_authoring/` | 2 | Done | Output: `docs/plan/product-revamp-diecast-stage-models.md` + decisions-so-far append. **NO Phase 2a dependency** |
| 4 | Encode stageModels into org.js via the generator (2c.4 encode) | `sp4_encode/` | 3 **AND** external 2a artifacts | Done | **PARKED until** `prototype/data/_build/generate-org.mjs` + `prototype/data/org.js` exist. Edits generator's stageModels section, re-emits org.js, flips placeholder→false, re-runs invariant gate. **Must finish before Phase 3 dispatch** |

Status: Not Started → In Progress → Done → Verified → Skipped → **Parked** (sp4 only, awaiting 2a)

No decision gates: the one plan-reserved human gate (owner sign-off on the four spines) is
**replaced by the written self-evaluation gate inside sp3** (five-test rubric + per-family
verdict, loop-once rework on failure) under the full-autonomy run configuration. No parallel
sub-phase groups (the parallelism in 2c.1 is *internal* to that one sub-phase).

## Dependency Graph

```
sp1 (2c.1 evidence base — 4 parallel family scans)
   │
   ▼
sp2 (2c.2 derive spines + five-test rubric + dropped-placeholder ledger)
   │
   ▼
sp3 (2c.3 AUTHORING — canonical note + JSON contract + self-eval gate
   │   + decisions-so-far append)          ◄── NO dependency on Phase 2a
   │
   ▼
sp4 (2c.4 ENCODE — generator stageModels edit + org.js re-emit + invariant gate)
   ▲
   └── EXTERNAL GATE (Phase 2a, separate parallel orchestrate run):
       requires prototype/data/_build/generate-org.mjs AND prototype/data/org.js to exist.
       Orchestrator PARKS sp4 (polling 2a) until both land; sp4 MUST complete before Phase 3.
```

## Execution Order

### Sequential Group 1
1. **sp1 — Practitioner Evidence Base (2c.1)** (~0.5–1 session; four ~60–75-min parallel scans)

### Sequential Group 2 (after Group 1)
2. **sp2 — Spine Derivation & Pressure-Test (2c.2)** (~0.5 session)

### Sequential Group 3 (after Group 2)
3. **sp3 — Canonical Note + Self-Eval (2c.3 authoring)** (~0.5 session) — **runs independent of 2a**

### Sequential Group 4 (after Group 3 AND the external 2a gate)
4. **sp4 — Encode into org.js (2c.4 encode)** (~0.25 session of active work; may park arbitrarily
   long waiting on 2a.1) — **gated on `generate-org.mjs` + `org.js` existing; blocks Phase 3 dispatch**

Total active work fits the 1–2-session budget (sp4's wall-clock can stretch while parked on 2a).

## Key Risks & Mitigations (from the plan)

| Risk | Impact | Mitigation |
|------|--------|------------|
| Research converges on tidy textbook phase models — owner's explicit failure mode | High | sp1 ≥1 practitioner-account/family + source-quality marks; sp2 rubric tests 1/2/4 (verb+artifact, ≥2-source recognition, tidy-label kill) |
| Anchoring on dropped placeholder steps | High | Placeholders banned as sp1 search seeds; sp2 derive-first-compare-after protocol + dropped-placeholder ledger as audited proof |
| Honest steps don't fit the spine band (too many/too long) | Med | 4–7 step bound + ≤18-char shortLabel convention enforced in sp2, not discovered in Phase 3 |
| A derived spine breaks its locked shape variant | Med | sp2 shape-compatibility check → conditional "spine-variant revision proposed" flag to 2b/3, not a silent redesign |
| 2a freezes org data before 2c lands; nobody encodes stageModels | High (F1) | Authoring/encode split: sp3 publishes the field contract + decisions-so-far append; sp4 owns the generator rewrite, gated on 2a.1, before Phase 3 |
| sp4 starts before 2a's generator exists | Med | sp4 park check (top of its file); orchestrator polls 2a and releases sp4 only when both artifacts exist; parking is a valid terminal poll state, not a failure |
| seeded-RNG stream shift perturbs frozen values outside stageModels | Med | sp4 F4 section-stability byte-diff: every line changed must be inside the stageModels region |
| Research timebox blowout (classic spike failure) | Med | Hard 60–75 min per family scan (sp1); `/cast-web-researcher` escalation only on a thin (<3-ref) family |
| Four spines drift symmetric, muting SC-005 contrast | Low | "Asymmetry is a feature" check in sp2; loop/progress decided per family from evidence |

## Plan Review

**Skipped** per the run configuration in `product-revamp-diecast-decisions-so-far.md` ("Plan
review: skipped — cross-phase reconciliation only", owner-approved; consistent with Phase
1/2a/2b/2c precedent). See `_review_summary.md`. Rerun manually via `/cast-plan-review` against any
sub-phase file if wanted.

## Progress Log

<Update after each sub-phase.>
- sp1 (evidence base) — **Done/Verified**: evidence-base.md, 21 refs/4 families, ≥1 practitioner account each.
- sp2 (spine derivation) — **Done/Verified**: spine-derivation.md, spines feature5/debug5/spike4/data5, five-test rubric all pass, dropped-placeholder ledger, spike spine-variant flag carried.
- sp3 (authoring) — **Done/Verified**: docs/plan/product-revamp-diecast-stage-models.md (7 sections, stageModels JSON parses), decisions-so-far appended; self-eval gate ALL FOUR FAMILIES PASS.
- sp4 (encode) — **Done/Verified**: generate-org.mjs stageModels region rewritten, org.js re-emitted with placeholder:false ×4, E1→feat-05/E2→dbg-04/E3→dbg-05/E4→spk-04/E5→data-05; generator deterministic (byte-identical re-run), invariant gate green, F4 section-stability confirmed. **Phase 3 dispatch unblocked.**
