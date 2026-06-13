# sp4b_routing_spec — Output

**Status:** completed
**Date:** 2026-06-12

## What was done

Authored the routing spec and wired it into the spec system, in lockstep with the
already-landed sp1a/sp2/sp3 interfaces. Documentation only — no code was changed.

### Files created/modified
- **Created** `docs/specs/cast-workflow-routing.collab.md` — the contract future per-family
  pipeline goals cite. Documents:
  - The three `goals` columns `workflow_family` / `routing_handle` / `routed_at` and their
    best-effort `goal.yaml` render (FR-009).
  - The `routing_handle = f"{family}:{status}"` format (e.g. `bug_fix:stub`) and its
    **documented staleness** as a point-in-time STAMP, not derived-on-read (Decision D1) —
    deriving-on-read was rejected to preserve byte-stability + the human-visible stamp
    (FR-007).
  - The `WorkflowHandle` JSON shape (`family, status, steps, pipeline_ref, message`) and the
    four-value status set `implemented | stub | unmatched | needs-classification` (FR-003),
    plus `resolve` totality over the 9 families + `None` + unknown string (FR-004, SC-003).
  - `POST /api/goals/{slug}/route` request/response (the ten response keys, 200/404
    semantics, with-body resolve+record vs no-body re-resolve) and the **recording rule**:
    only valid `WorkFamily` values persist; `unmatched`/`needs-classification` are returned
    and announced, never recorded (FR-011/FR-012/FR-013).
  - `WORKFLOW_REGISTRY` semantics — string-keyed (one vocabulary, two homes), every value a
    `stub` in v2, `bug_fix` steps spec-mandated, `generic` a named (announced) stub
    (FR-001/FR-002).
  - Authority (Decision D2): `goals.workflow_family` is the authoritative routing record;
    front-matter `classification.family` reconciles on next refine (FR-010).
  - Best-effort `goal.yaml` (Decision D5) and the no-reclassify source-pin (Decision D4).
  - Single-caller-in-v2 note (only `cast-refine-requirements`; FR-015) and the explicit note
    that `/route` is a plain JSON API outside the delegation + output-json contracts.
- **Modified** `docs/specs/cast-goal-classification.collab.md` — appended a **labeled
  routing extension** to the ONE canonical add-a-family checklist (under US6), giving the
  add-a-family routing home (`WORKFLOW_REGISTRY` entry) and the graduate-a-family steps (flip
  `status`, set `pipeline_ref` — registry-only diff). Per Decision D3, the routing spec does
  NOT restate a separate list; it cross-references this one.
- **Modified** `docs/specs/_registry.md` — registered `cast-workflow-routing.collab.md` with
  a scope one-liner; noted the routing extension on the classification spec's row.

## Verification (all green)
- `bin/cast-spec-checker docs/specs/cast-workflow-routing.collab.md` → exit 0.
- `bin/cast-spec-checker docs/specs/cast-goal-classification.collab.md` → exit 0 (append did
  not break the existing spec).
- Registered: `grep cast-workflow-routing docs/specs/_registry.md` → 1 hit.
- D3: the routing spec mentions "add-a-family" only as cross-references/labels (US5, SC-006,
  Out of scope, Cross-references), never as a standalone checklist; the actual checklist
  lives only in the classification spec.
- D3 extension present in the classification spec (`WORKFLOW_REGISTRY` / graduate steps under
  US6).
- Names verified against code byte-for-name: `WORKFLOW_REGISTRY`/`WORKFLOW_FAMILIES`
  (`config.py`), `WorkflowHandle`/`resolve`/`record_routing_decision` + status set + handle
  format (`workflow_router_service.py`), `POST /{slug}/route` + the ten response keys
  (`api_goals.py`).

## Success criteria
- [x] `cast-workflow-routing.collab.md` created, documenting all Step 4b.1 contracts.
- [x] Registered in `docs/specs/_registry.md`.
- [x] Graduate/add-a-family steps appended as a labeled extension of the classification
      spec's checklist (D3) — no second standalone list.
- [x] Spec names match the code; `bin/cast-spec-checker` green.
- [x] Cross-references the classification spec for the family vocabulary; notes the
      delegation/output-json contracts do not apply to `/route`.

## Notes for dependent sub-phases
- This spec now makes `workflow_router_service.py`, `config.py`'s `WORKFLOW_REGISTRY`, and the
  `/route` handler **spec-linked** — future edits must preserve its behaviors.
- The `/cast-update-spec` and `/cast-spec-checker` steps were executed directly (authored the
  file + ran `bin/cast-spec-checker`) because this was a fully-autonomous, non-interactive run
  and `/cast-update-spec` is an approve-before-write interactive agent that would block; the
  output is byte-equivalent to its create mode and passes the same linter.
