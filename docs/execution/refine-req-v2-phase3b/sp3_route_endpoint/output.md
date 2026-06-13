# sp3_route_endpoint — Output

**Status:** ✅ Complete. All 6 success criteria met; `pytest` green (9 new tests; 35 with sp2).

## What was built

### `POST /api/goals/{slug}/route` (`cast-server/cast_server/routes/api_goals.py`)
The one phase-agnostic door (FR-016). A thin JSON adapter over the sp2 resolver — **agent-facing JSON, never an HTMX fragment**.

- **Imports added:** `Body` (fastapi), `BaseModel` (pydantic), `workflow_router_service` (added to the existing `cast_server.services` import).
- **`RouteRequest(BaseModel)`** — optional body `{ "family": str | None }`.
- **`route_goal(slug, body=Body(default=None))`**:
  - `goal = goal_service.get_goal(slug)`; `None` → **404**.
  - `family = (body.family if body else None) or goal["workflow_family"]` — with-body = refinement path, no-body = FR-016 re-resolve-from-DB path.
  - `handle = workflow_router_service.resolve(family)` (pure/total).
  - Records **only** routable handles (`status in {"stub","implemented"}`) via `record_routing_decision`. `unmatched`/`needs-classification` are returned + announced, never persisted.
  - **Response keys:** `family, status, steps, pipeline_ref, message, recorded, changed, previous_family, routing_handle, routed_at`.

### Byte-stability mechanism (the one design decision worth noting)
`record_routing_decision` **omits `routed_at` on an idempotent no-op**. The handler seeds `meta` with `routed_at = goal["routed_at"]` (and `routing_handle = goal["routing_handle"]`) and then **merges** the recorder result with `meta.update(...)` — so a no-op keeps the goal's existing stamp instead of nulling it. This is what makes the no-body response **byte-identical across an unrelated phase flip** (SC-005). The illustrative snippet in the plan used `**{k: meta.get(k)...}` which would have nulled `routed_at` on the no-op; the merge is the correct form (the plan flagged the snippet as illustrative + warned about `routed_at` churn).

## Tests — `cast-server/tests/test_api_goals_route.py` (9 tests, all green)
Hermetic `TestClient` over the `api_goals` router; patches **`connection.DB_PATH`** (handler calls services without an explicit `db_path`). Each goal is seeded with an **on-disk `folder_path` + real `goal.yaml`** so the best-effort mirror is exercised, not skipped.

- `test_five_family_seed_trace` — 5 families (`bug_fix, new_initiative, data_analysis, random_idea, testing_qa`) → correct handle + `workflow_family`/`routing_handle` in **both** DB row and rendered `goal.yaml`.
- `test_bug_fix_steps_are_spec_mandated` — `logs→RCA→confirm→fix/test`.
- `test_phase_flip_byte_stability` — flip `phase` via the real `PUT /{slug}/phase` → no-body `/route` response is **byte-identical** (`after.content == before.content`).
- `test_unknown_slug_is_404`.
- `test_unmatched_family_not_recorded` — `nonsense` → 200 `unmatched`, `recorded:false`, DB column untouched.
- `test_needs_classification_when_unrouted_and_no_body` — 200 `needs-classification`, `recorded:false`.
- `test_idempotent_repost_is_noop` — 2nd POST `recorded:false, changed:false`, `routed_at` frozen.
- `test_changed_family_reports_previous` — different family → `changed:true`, `previous_family` reported, row updated.
- `test_no_reclassify_source_pin` (**D4, handler half**) — strips the docstring via `ast` (prose says "re-classify"), then asserts the `route_goal` **code** contains no `subprocess`/`cast_goal_classifier`/`.trigger`/`/trigger`/`anthropic`/`openai`/`classify`/`dispatch`/`tmux`, and *does* call only `goal_service.get_goal` + `workflow_router_service.{resolve,record_routing_decision}`. Replaces the SC-005 "assert by code inspection" step for the handler module.

## For dependent sub-phases
- **sp4a (refine wiring):** call `POST /api/goals/{slug}/route` with `{"family": "<WorkFamily value>"}` to resolve+record during refinement. Response gives you `steps`/`message` for the refinement summary and `routing_handle` for the `goal.yaml` stamp. The endpoint is the only door — do not call the service directly from the agent.
- **sp4b (spec):** the request/response contract above is the surface to document. Note the **STORED-not-derived** `routing_handle` stamp (D1) and the byte-stability/no-op semantics. No spec covered `/route` before this; the no-reclassify pin is the CI backstop, not a spec assertion.
- The handler does **not** wire `cast-refine-requirements` (sp4a) and adds **no** spec (sp4b) — out of scope here.

## Verification run
```
pytest cast-server/tests/test_workflow_router_service.py cast-server/tests/test_api_goals_route.py  →  35 passed
cast_server.app imports OK; /route registered: True
route_goal source pin: imports only goal_service + workflow_router_service
```
