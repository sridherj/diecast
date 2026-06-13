# Sub-phase 3: `POST /api/goals/{slug}/route` — the phase-agnostic surface

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase3b/_shared_context.md` before starting.
> Source: Work Package D of `docs/plan/2026-06-11-refine-requirements-v2-phase3b-workflow-router.md`.

## Objective

Expose the resolver over HTTP as `POST /api/goals/{slug}/route` — the **one door** any caller in any
phase uses. With a `{"family": ...}` body it resolves + records (the refinement path); with no body it
re-resolves from the persisted `goals.workflow_family` column and re-records idempotently (the FR-016
path — any future phase/agent, no re-classification). The handler imports **only** `goal_service` +
`workflow_router_service` — nothing that could re-classify — which is what makes SC-005 (byte-identical
output across a phase flip) true by construction, pinned by a no-reclassify source test.

## Dependencies
- **Requires completed:** **sp2** — `workflow_router_service.resolve` + `record_routing_decision`.
  (Transitively sp1a's registry + sp1b's columns.)
- **Assumed codebase state:** `routes/api_goals.py` exists with the `/api/goals` prefix and the
  `/{slug}/status` (l.101) + `/{slug}/phase` (l.144) `/<verb>` precedents. `goal_service.get_goal`
  exists. `workflow_router_service` exposes `resolve` + `record_routing_decision`. FastAPI TestClient
  precedent: `cast-server/tests/test_api_agents.py`.

## Scope

**In scope:**
- `POST /{slug}/route` in `routes/api_goals.py` (keeps the `/api/goals` prefix; returns **JSON**, not
  an HTMX fragment — agent-facing, like `api_agents.py`).
- Request/response contract per `_shared_context.md` (with-body vs no-body paths; 200/404 semantics).
- `cast-server/tests/test_api_goals_route.py` — the SC-005 trace + edge cases + the no-reclassify
  source pin extended to the **route handler module**.

**Out of scope (do NOT do these):**
- Any agent dispatch, LLM call, or classifier import in the handler (would break FR-016/SC-005 and fail
  the D4 pin). The handler is a thin adapter over the service.
- An HTMX/HTML fragment or a UI routing panel (no v2 requirement consumes it — `goal.yaml` + the
  refinement summary are the v2 surfaces).
- Wiring `cast-refine-requirements` to call this endpoint (sp4a). The spec (sp4b).
- Changing the resolver or recorder logic (sp2) — only call them.

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/routes/api_goals.py` | Modify | Has `/status` (l.101), `/phase` (l.144); no `/route` |
| `cast-server/tests/test_api_goals_route.py` | Create | Does not exist |

## Detailed Steps

### Step 3.1: The route handler

Add to `routes/api_goals.py`, following the existing `/status` / `/phase` handler style (service-call,
JSON return, `404` on unknown slug):

```python
class RouteRequest(BaseModel):
    family: str | None = None

@router.post("/{slug}/route")
def route_goal(slug: str, body: RouteRequest | None = Body(default=None)):
    goal = goal_service.get_goal(slug)
    if goal is None:
        raise HTTPException(status_code=404, detail=f"Unknown goal: {slug}")
    family = (body.family if body else None) or goal.get("workflow_family")
    handle = workflow_router_service.resolve(family)
    meta = {"recorded": False, "changed": False, "previous_family": None,
            "routing_handle": None, "routed_at": goal.get("routed_at")}
    if handle.status in ("stub", "implemented"):          # only routable handles persist
        meta = workflow_router_service.record_routing_decision(slug, family, handle)
    return {
        "family": handle.family, "status": handle.status, "steps": list(handle.steps),
        "pipeline_ref": handle.pipeline_ref, "message": handle.message,
        **{k: meta.get(k) for k in ("recorded", "changed", "previous_family", "routing_handle", "routed_at")},
    }
```

- **With body family** (refinement path): resolve + record.
- **No body** (FR-016 path): `family` falls back to `goal["workflow_family"]`; resolve + idempotent
  re-record (no-op when unchanged — `routed_at` untouched, keeping the response byte-stable for SC-005).
- **Unknown family string** in body → `resolve` returns `unmatched` (status not routable) → NOT
  recorded → 200 with the `unmatched` handle + `recorded: false`. Totality ⇒ the API never 500s on
  content.
- **`None` persisted + no body** → `needs-classification` handle + `recorded: false`.
- Match the file's actual imports/helpers (`Body`, `HTTPException`, the `goal_service`/
  `workflow_router_service` import names, the row-as-dict shape of `get_goal`). Read `api_goals.py`
  first and follow its house style — the snippet is illustrative, not literal.

### Step 3.2: Tests — `cast-server/tests/test_api_goals_route.py`

FastAPI TestClient (precedent: `test_api_agents.py`). Cases:
- **5-family seed trace (SC-005):** seed 5 goals (`bug_fix`, `new_initiative`, `data_analysis`,
  `random_idea`, `testing_qa`) → `POST /route` with each family → assert the correct handle returned
  AND `workflow_family`/`routing_handle` present in **both** the DB row and the rendered `goal.yaml`.
- **Phase-flip byte-stability (SC-005):** flip one goal's `phase` via the existing phase endpoint →
  `POST /route` with **no body** → assert the response body is **byte-identical** to the pre-flip
  route response (assert the FULL body, not just handle fields — `routed_at` must be untouched by the
  idempotent no-op).
- **404** unknown slug.
- **Unmatched-not-recorded:** `POST /route` body `{"family": "nonsense"}` → 200, `status: "unmatched"`,
  `recorded: false`; DB `workflow_family` unchanged.
- **Needs-classification:** un-routed goal, `POST /route` no body → 200, `status:
  "needs-classification"`, `recorded: false`.
- **Idempotent re-POST:** same family twice → second response `recorded: false, changed: false`,
  `routed_at` unchanged.
- **No-reclassify source pin (D4, handler half):** assert the **`api_goals.py` module source** (or the
  route function's source) contains no `subprocess`, no Agent/`/trigger` dispatch, no
  `cast_goal_classifier`, no LLM client import on the `/route` path. (sp2 pins the service module; this
  pins the handler module — together they REPLACE the SC-005 "assert by code inspection" step.)

→ **Delegate:** apply `/cast-pytest-best-practices`; review output.

## Verification

### Automated Tests (permanent) — `cast-server/tests/test_api_goals_route.py`
All cases in Step 3.2. Gate: the 5-family seed trace + the phase-flip byte-stability assertion + the
handler no-reclassify source pin are the SC-005 headline checks.

### Validation Scripts (temporary)
```bash
uv run --project cast-server pytest cast-server/tests/test_api_goals_route.py -v
# Live smoke (server up): seed/known slug
curl -s -X POST http://localhost:8005/api/goals/<slug>/route -H 'Content-Type: application/json' -d '{"family":"bug_fix"}' | python -m json.tool
curl -s -X POST http://localhost:8005/api/goals/<slug>/route | python -m json.tool   # no body → re-resolve
# Handler source pin:
grep -nE "subprocess|cast_goal_classifier|/trigger|anthropic|openai" cast-server/cast_server/routes/api_goals.py && echo "inspect /route path" || echo "no classifier machinery"
```

### Manual Checks
- `/route` returns JSON, not an HTMX fragment.
- The handler calls only `goal_service.get_goal` + `workflow_router_service.{resolve,record_routing_decision}`.
- Unknown family → 200 (not 500); unknown slug → 404.

### Success Criteria
- [ ] `POST /api/goals/{slug}/route` present, JSON in/out, with-body + no-body paths working.
- [ ] 5-family seed trace: correct handle + `workflow_family`/`routing_handle` in DB row AND `goal.yaml`.
- [ ] Phase-flip → byte-identical response body (full body), no classifier in the path.
- [ ] 404 unknown slug; unmatched-not-recorded; needs-classification; idempotent re-POST.
- [ ] Handler no-reclassify source pin green.
- [ ] `pytest cast-server/tests/test_api_goals_route.py` green.

## Execution Notes
- The byte-stability test is the crown jewel: a phase flip must not change one byte of the `/route`
  response. The mechanism is the idempotent no-op in `record_routing_decision` (leaves `routed_at`
  untouched) + the registry being unchanged. If the test sees drift, suspect `routed_at` churn or a
  non-deterministic field ordering — not a resolver bug.
- Body parsing: `POST` with an empty body must yield the no-body path, not a 422. Use
  `Body(default=None)` (or the file's existing optional-body idiom) so a bodyless POST is valid.
- Do NOT add the handler to any router that re-classifies or dispatches agents. The whole point is that
  this door imports no agent/LLM machinery (FR-016 by construction).

**Spec-linked files:** No spec covers `/route` yet — sp4b documents the request/response contract +
the recording rule. The no-reclassify source pin is the CI backstop, not a spec assertion.
