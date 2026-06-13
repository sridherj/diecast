# Review Summary: Refine Requirements v2 — Phase 3b (Routing)

> **Mode:** This execution plan was produced **fully autonomously** (per the delegation: "PROCEED
> FULLY AUTONOMOUSLY — all design decisions are already resolved; do NOT ask the user any questions;
> make sensible defaults and record them"). The source plan was already taken through
> `cast-plan-review` (BIG-CHANGE pass, 5 issues, all resolved — see its `## Decisions` section), so no
> per-sub-phase child review agents were dispatched. Instead a self-review pass over the six
> sub-phases is recorded below. Nothing here blocks execution.

## Open Questions

**None block execution.** The source plan's two open questions are resolved as recorded defaults:

1. **`/cast-router` skill — ship or cut?** → **DEFAULT: SHIP** (sp4a, Step 4a.5). Near-zero cost,
   completes the FR-013 surface, and the high-level plan says "optionally ship." It is the **single
   designated cuttable item** if the 1–2 session budget runs short — in which case the executing
   context must **flag it in the run summary, never silently skip**. The refine-prompt wiring
   (sp4a.1–4a.4) is NOT cuttable.
2. **Stub `steps` wording per family** (except `bug_fix`, spec-mandated) → **DEFAULT: adopt the WP-A
   strings verbatim** (in sp1a / `_shared_context.md`). They are owner-editable copy at execution time
   (they render into `goal.yaml` + the refinement summary); editing them changes data only, not the
   plan or any test except the `bug_fix` spec-mandated assertion.

## Decisions Carried From the Source Plan (binding — D1–D5, all final)

These were resolved by `cast-plan-review` (2026-06-11) and are threaded into the sub-phases:

| ID | Decision | Lands in |
|----|----------|----------|
| D1 | `routing_handle` is a **stored** point-in-time stamp (documented staleness), not derived-on-read | sp2 (recorder), sp4b (spec) |
| D2 | `goals.workflow_family` is the **authoritative** routing record; front-matter reconciles on next refine | sp4a (wiring), sp4b (spec) |
| D3 | **One** add-a-family checklist (Phase 2 spec is canonical); routing spec appends its homes by cross-reference | sp4b (spec) |
| D4 | No-reclassify guarantee is an **automated source-pin test** (router module + `/route` handler), not manual inspection | sp2 + sp3 (pins) |
| D5 | Missing-`goal.yaml` recording is **best-effort** (DB written, no raise) — pinned by test + recorder docstring | sp1b + sp2 |

## Self-Review Notes by Sub-Phase

### sp1a_family_registry (WP A)
- Registry is string-keyed in `config.py` (bottom layer, no `families.py` import) — the deliberate
  duplication mitigated by the key-set pin test. The pin test is **intentionally co-located in sp2**
  (the one Phase-3b `families.py` import, tests-only), so sp1a is independently verifiable via its own
  status/`steps` validity test without importing the enum. ✓ No issue.

### sp1b_recording_columns (WP C)
- Mirrors the `gstack_dir` precedent exactly (canonical schema + idempotent migration + conditional
  `goal.yaml` render). Explicit guard against editing the **legacy root** `db/schema.sql`. `GoalUpdate`
  threading flagged as contract-completeness only (no second write path). ✓ No issue.
- **Sequencing note (the one real refinement over the source plan's build order):** the source plan
  lists WP-C as "parallel from the start" with WP-A/B, both feeding WP-D. That is true for *writing*
  code, but WP-B's **recorder tests** (idempotency, change-path, `goal.yaml` round-trip, missing-yaml)
  need WP-C's columns to be green. So this execution plan makes **sp2 depend on BOTH sp1a and sp1b**
  (not sp1a alone). sp1a ∥ sp1b still holds (disjoint files); the join moves from WP-D to sp2. This is
  a faithful tightening of the dependency graph for independent green verification, not a scope change.

### sp2_resolver_service (WP B)
- Largest sub-phase (~30–40% of effort is the test module, as the quality bar requires). Holds the two
  load-bearing source pins (no-`STARTER_TASKS`, no-reclassify) + the registry/enum pin. "Structure from
  `orchestration_service`, persistence from `goal_service`" needle is called out explicitly so the
  executor does not copy orchestration_service's file persistence. ✓ No issue.

### sp3_route_endpoint (WP D)
- Thin adapter; carries the SC-005 phase-flip byte-stability trace and the handler-half of the D4
  no-reclassify pin. Body-parsing gotcha (bodyless POST must not 422) is flagged. The handler snippet
  is marked illustrative — executor reads `api_goals.py` for the literal house style. ✓ No issue.

### sp4a_refine_wiring (WP E)
- Shares the `cast-refine-requirements.md` prompt with Phase 2 WP-E and Phase 1b — the manifest's
  "Files Touched by More Than One Sub-Phase" table and this sub-phase both stress: **append the routing
  tail, never clobber/duplicate** Phase 2/1b content, and respect the ~650-line ceiling + the shared
  question budget. The US6 S4 surfacing rides the existing classification confirm (no new question
  slot). ✓ No issue, but this is the highest-coordination sub-phase — execute it in a context that has
  Phase 2 WP-E already landed.

### sp4b_routing_spec (WP F)
- Doc-only; delegates authoring to `/cast-update-spec` (create mode) and linting to
  `/cast-spec-checker`. D3 (no duplicate add-a-family list) is the subtle constraint, flagged twice.
  Runs parallel with sp4a (disjoint: `docs/specs/` vs `agents/`). ✓ No issue.

## Parallel-Safety Verification (file-disjointness)

| Parallel pair | sp X files | sp Y files | Disjoint? |
|---|---|---|---|
| sp1a ∥ sp1b | `config.py` (+ its test) | `schema.sql`, `connection.py`, `goal.py`, `goal_service.py` (+ tests) | ✓ |
| sp4a ∥ sp4b | `agents/cast-refine-requirements/*`, `agents/cast-router/*` (+ `generate-skills`) | `docs/specs/*` | ✓ (sp4b reads code, writes none) |

No decision gates (HOLD SCOPE). Critical path: sp1a → sp2 → sp3 → sp4a.
