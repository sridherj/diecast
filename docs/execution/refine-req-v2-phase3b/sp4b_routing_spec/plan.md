# Sub-phase 4b: Spec lockstep — `cast-workflow-routing.collab.md`

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase3b/_shared_context.md` before starting.
> Source: Work Package F of `docs/plan/2026-06-11-refine-requirements-v2-phase3b-workflow-router.md`.

## Objective

Author the spec that documents the new user-facing routing contracts so future per-family pipeline
goals have a single source of truth to cite. It records the three `goals` columns (+ `goal.yaml`
render), the `routing_handle` format (`{family}:{status}`) and its documented staleness, the
`WorkflowHandle` JSON shape + status set, the `POST /api/goals/{slug}/route` request/response contract
(including the recording rule: `unmatched`/`needs-classification` never persist), `WORKFLOW_REGISTRY`
semantics, and the single-caller-in-v2 note. Critically, it does NOT restate a separate add-a-family
checklist — it **appends** the routing homes + graduate-a-family steps to the ONE canonical Phase 2
checklist (D3). Documentation lockstep; runs parallel with sp4a.

## Dependencies
- **Requires settled interfaces:** **sp1a** (registry semantics), **sp2** (`WorkflowHandle` shape,
  recorder rule, handle format), **sp3** (route request/response). Author after A–D interfaces settle
  so names match exactly. Does not need sp4a's prompt wiring to be done.
- **Assumed codebase state:** `docs/specs/cast-goal-classification.collab.md` exists (Phase 2 WP-F)
  with an add-a-family checklist + the `WorkFamily` vocabulary. `docs/specs/_registry.md` exists.
  `templates/cast-spec.template.md` exists. `bin/cast-spec-checker` lints `.collab.md` specs.

## Scope

**In scope:**
- → **Delegate:** `/cast-update-spec` (**create mode**) — author
  `docs/specs/cast-workflow-routing.collab.md`.
- Register it in `docs/specs/_registry.md`.
- Append the routing homes (`WORKFLOW_REGISTRY` entry) + graduate-a-family steps (flip `status`, set
  `pipeline_ref` — registry-only diff, FR-015) as a **labeled extension** of the Phase 2
  `cast-goal-classification.collab.md` add-a-family checklist (D3) — do NOT restate a separate list.
- Cross-reference `cast-goal-classification.collab.md` for the family vocabulary (routing cites, never
  redefines).

**Out of scope (do NOT do these):**
- Any code change (`config.py`, the service, the route, models, schema) — documentation only. sp4b
  *reads* those files to copy exact names; it writes neither.
- Redefining the `WorkFamily` vocabulary (cite Phase 2's spec).
- A second, standalone add-a-family checklist (D3 forbids it — append to the canonical one).
- Touching `cast-delegation-contract.collab.md` / `cast-output-json-contract.collab.md` (no conflict —
  `/route` is a plain JSON API, not agent dispatch; note this, change nothing).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `docs/specs/cast-workflow-routing.collab.md` | Create (via `/cast-update-spec`) | Does not exist |
| `docs/specs/_registry.md` | Modify | Exists; register the new spec |
| `docs/specs/cast-goal-classification.collab.md` | Modify (append checklist extension) | Phase 2 WP-F; has the canonical add-a-family checklist |

## Detailed Steps

### Step 4b.1: Author the spec (delegate to `/cast-update-spec`)

→ **Delegate:** `/cast-update-spec` in **create mode** for `docs/specs/cast-workflow-routing.collab.md`.
Provide it these user-facing contracts to document (copy names verbatim from the code — read
`config.py`, `workflow_router_service.py`, `routes/api_goals.py`):

- **The three `goals` columns** `workflow_family`, `routing_handle`, `routed_at` (+ their `goal.yaml`
  render via the conditional includes).
- **`routing_handle` format** `{family}:{status}` (e.g. `bug_fix:stub`) — and its **documented
  staleness** (D1): a point-in-time STAMP that can lag the registry until the goal is re-routed
  (re-route is the refresh mechanism); deriving-on-read was rejected to preserve byte-stability + the
  human-visible stamp.
- **`WorkflowHandle` JSON shape** (`family, status, steps, pipeline_ref, message`) + the status set
  (`implemented | stub | unmatched | needs-classification`).
- **`POST /api/goals/{slug}/route`** request/response contract, including the **recording rule**:
  only valid `WorkFamily` values persist; `unmatched`/`needs-classification` are returned + announced,
  never recorded. With-body (resolve+record) vs no-body (FR-016 re-resolve) paths; 200/404 semantics.
- **`WORKFLOW_REGISTRY` semantics:** string-keyed (one vocabulary, two homes), every value `stub` in
  v2, `bug_fix` steps spec-mandated, `generic` is a named (announced) stub not a silent fallback.
- **Authority (D2):** `goals.workflow_family` is the authoritative routing record; front-matter
  `classification.family` is the document's self-description, reconciled on next refine.
- **Single-caller-in-v2 note:** only `cast-refine-requirements` calls the router in v2.
- → Review `/cast-update-spec` output: names must match `config.py` / `workflow_router_service.py` /
  `api_goals.py` exactly.

### Step 4b.2: Append the graduate/add-a-family extension to the Phase 2 checklist (D3)

In `docs/specs/cast-goal-classification.collab.md`, append a **labeled extension** to its existing
add-a-family checklist — NOT a new list:
- **Routing home:** add a `WORKFLOW_REGISTRY` entry in `config.py` (the registry/enum key-set pin test
  is the CI backstop against a forgotten entry).
- **Graduate a family** (`stub → implemented`): flip the registry value's `status`, set `pipeline_ref`
  — a registry-only diff, no seam change (FR-015).

The routing spec's add-a-family section then *points to* this one canonical list rather than restating
it. Rationale: one list a maintainer follows end-to-end (D3 — DRY).

### Step 4b.3: Register + lint

- Add the new spec to `docs/specs/_registry.md` (follow the registry's existing row format).
- → **Delegate:** `/cast-spec-checker` on `cast-workflow-routing.collab.md` (or run
  `bin/cast-spec-checker`) — must be green.

## Verification

### Automated Tests (permanent)
- `bin/cast-spec-checker` stays green on the new spec file (this is part of the SC-005 phase gate).

### Validation Scripts (temporary)
```bash
bin/cast-spec-checker docs/specs/cast-workflow-routing.collab.md
grep -n "cast-workflow-routing" docs/specs/_registry.md         # registered
# D3: no second add-a-family list — the routing spec cross-references the classification one
grep -ni "add.a.family\|graduate" docs/specs/cast-workflow-routing.collab.md
grep -ni "WORKFLOW_REGISTRY\|graduate" docs/specs/cast-goal-classification.collab.md   # the appended extension
# Names match code exactly:
grep -nE "workflow_family|routing_handle|routed_at|WorkflowHandle|needs-classification|unmatched" docs/specs/cast-workflow-routing.collab.md
```

### Manual Checks
- Spec names match `config.py` (`WORKFLOW_REGISTRY`, `WORKFLOW_FAMILIES`),
  `workflow_router_service.py` (`WorkflowHandle`, `resolve`, `record_routing_decision`, the status
  set, the handle format), and `api_goals.py` (`POST /{slug}/route`, response keys) **exactly**.
- The add-a-family / graduate steps live as an extension of the Phase 2 spec's ONE checklist, not a
  duplicate list.
- The recording rule (`unmatched`/`needs-classification` never persist) is documented.
- The staleness contract (D1) and the authority rule (D2) are documented.

### Success Criteria
- [ ] `docs/specs/cast-workflow-routing.collab.md` created via `/cast-update-spec`, documenting all
      contracts in Step 4b.1.
- [ ] Registered in `docs/specs/_registry.md`.
- [ ] The graduate/add-a-family steps appended as a labeled extension of
      `cast-goal-classification.collab.md`'s checklist (D3) — no second standalone list.
- [ ] Spec names match the code byte-for-name; `bin/cast-spec-checker` green.
- [ ] Cross-references the classification spec for the family vocabulary; notes the
      delegation/output-json contracts do not apply to `/route`.

## Execution Notes
- This spec is the **contract future per-family pipeline goals cite** — get the names exact, because a
  drift here misdirects every downstream pipeline build. The registry/enum pin test (sp2) is the CI
  backstop, but the spec is the human entry point.
- D3 is the subtle one: resist the urge to write a complete, self-contained add-a-family checklist in
  the routing spec. The whole point is ONE list (in the classification spec) that a maintainer follows
  end-to-end, with routing appending its homes. A duplicate list is exactly the drift D3 prevents.
- Document the staleness (D1) and best-effort-yaml (D5) contracts as *intentional*, not as caveats —
  they are accepted designed behavior, pinned by tests in sp2.

**Spec-linked files:** this sub-phase *authors* the spec; once it exists, `workflow_router_service.py`,
`config.py`'s registry, and the `/route` handler become spec-linked — future edits to them must
preserve this spec's behaviors.
