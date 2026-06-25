# Detailed Plan — Phase 1: Server Up & Dispatch Live

> Detailed, spec-aware plan for **Phase 1** of `neoorg-crud-workforce-fastapi-backend`.
> Parent: `plan.collab.md` (high-level phasing). Brief: `refined_requirements.collab.md`.
> **Scope mode:** REDUCTION — thin bootstrap; the lower MVCS stack + dispatch machinery already exist.

## Objective

Get neoorg **running and dispatchable** by hand: a FastAPI server that serves full CRUD over the
**existing** `Task` and `Run` (`AgentRun`) services and exposes the **existing** dispatch/proof
machinery over HTTP — the dispatcher the maker-checker contract names. No Workforce yet; this is the
foundation the Workforce (Phase 2) dispatches through and the surface the cockpit later reads.

**Done when:** `bin/neoorg-server` boots; `POST/GET/PUT/DELETE /tasks` and `/runs` work with
`404`/`422`; a row survives restart; `POST /dispatch` runs the existing canned agent, enforces
declared-checker proof (422 on missing proof, 403 on disallowed target); `leak-guard` + the existing
`pytest -m "not live"` stay green.

## What already exists (do NOT rebuild)

- `Task`: `spine/entities/task.py`, `spine/repositories/task_repository.py`,
  `spine/services/task_service.py`, `spine/schemas/task_schema.py` + migrations `0001–0007`.
- `Run` = `AgentRun`: `contract/entities/agent_run.py`, `…/repositories/agent_run_repository.py`,
  `…/services/agent_run_service.py` (bespoke: `record_run`/`retry_run`/`runs_for_task`/`set_status`/
  `set_output_location`), `…/schemas/agent_run_schema.py`.
- MVCS bases: `shared/infra/db/{base_entity,base_repository,base_service,db_session_manager}.py`.
- Dispatch/proof machinery: `contract/delegation.py` (`dispatch_child`, `check_delegation_allowed`,
  `propagate_child_outcome`, `ChildDispatch`/`DispatchGate` Protocols, `DelegationDenied`),
  `contract/check/proof.py` (`resolve_proof_of_check`), `contract/check/gate.py`,
  `contract/discovery/` (the contract-status seam), `contract/dummy/{canned_agent,roundtrip}.py`
  (test fixtures for dispatch).

## Spec consistency

- **leak-guard:** the server lives outside `src/neoorg/adapter/`; it may import `contract/` and
  `spine/` freely but MUST NOT introduce `/v1/` wire strings (those stay in the adapter). The dispatch
  endpoint wraps `contract/` (above the adapter seam) — clean.
- **maker-checker / agent-communication §8:** sub-phase 1.6 writes the reconciliation note (server =
  dispatcher). It largely *records* existing behavior; flag a follow-up `/cast-update-spec` to make
  the server-as-dispatcher reading explicit. No spec change blocks Phase 1.
- **Service style:** new controllers follow the `cast-service`/`cast-crud-orchestrator` convention
  (schema-in, schema-out). `BaseService.create/update` are entity-in (a known smell) — sub-phase 1.3
  adds an additive schema-in shim; the internal entity-in callers are left for a later sweep.

---

## Sub-phase 1.1 — Server skeleton, deps, launcher, session wiring
**Objective:** A bootable FastAPI app with request-scoped spine sessions and a launcher.
**Files (new):** `pyproject.toml` (+`fastapi`,`uvicorn`); `src/neoorg/server/__init__.py`,
`server/app.py` (app factory), `server/__main__.py` (uvicorn entry), `server/deps.py` (session
dependency); `bin/neoorg-server` (stdlib launcher, mirror diecast `bin/cast-server`).
**Key interfaces:**
- `create_app() -> FastAPI` — assembles routers; `get_session()` FastAPI dependency yields a
  request-scoped session from `DbSessionManager`, commits/rolls-back per request.
- Launcher reads `NEOORG_BIND_HOST`/`NEOORG_PORT` (defaults `127.0.0.1:8000`), `uv run uvicorn`.
**Design review:** Table creation — the spine already has Alembic migrations `0001–0007`; the server
assumes `alembic upgrade head` has been run (the launcher can run it, or document a `bin` step). Do
NOT `create_all` in prod paths (it bypasses migrations); a dev-only `create_all` is acceptable behind
a flag. **Decision:** reuse existing Alembic; launcher runs `upgrade head` on start (dev-friendly).
**Verification:** `bin/neoorg-server` boots; `GET /health` → `200`; `uv run leak-guard` green;
existing `pytest -m "not live"` green.
**Dependencies:** none.

## Sub-phase 1.2 — `CRUDRouterFactory` (schema-in / schema-out)
**Objective:** A reusable factory turning a service + schemas into a CRUD `APIRouter` — the foundation
the future `mvcs-controller-builder` emits against.
**Files (new):** `src/neoorg/server/crud_router.py`.
**Key interface:**
```
make_crud_router(*, prefix, tags, service_factory, read_schema,
                 create_model, update_model, to_create_kwargs=None) -> APIRouter
# POST /         body=create_model  -> 201 read_schema
# GET  /{id}                        -> 200 read_schema | 404
# GET  /          ?limit&offset&…    -> 200 {items: [read_schema], total}
# PUT  /{id}      body=update_model  -> 200 read_schema | 404 | 422
# DELETE /{id}                       -> 204 | 404
```
**Design review:** Follows **cast styling — schema-in, schema-out**. Because `BaseService.create`
is entity-in today, the factory calls a **schema-in** service method (added in 1.3), NOT building
ORM entities in the handler. `404` from `get_by_id is None`; `422` is Pydantic-default on the
request model. Keep the factory thin; entities with bespoke services (Run) use a custom controller
instead (1.4) — the same `cast-controller` vs `cast-custom-controller` split.
**Verification:** a throwaway/dummy service round-trips all five verbs through the factory router.
**Dependencies:** 1.1.

## Sub-phase 1.3 — Task controller (+ additive schema-in shim)
**Objective:** `/tasks` CRUD over the existing `TaskService`, schema-in.
**Files:** new `server/routers/task_router.py`; edit `shared/infra/db/base_service.py` (additive
schema-in `create_from`/`update_from`, non-breaking) or `spine/services/task_service.py` (a
`create(data: TaskCreate)` override).
**Design review:** `TaskService(session, *, criterion_verdict_resolver=None)` — Phase-1 default
`None` keeps the four-eyes `done` guard inert (fine). The schema-in create maps `TaskCreate` →
`TaskEntity` **inside the service** (id-gen `task_…`, defaults, the §5 authz gate), honoring the
locked Task shape (`tasks.collab.md`: lifecycle, `visibility`, `parent_id`, `blocked_by`,
Task↔Run join). **Open:** under localhost-no-auth, who is the acting caller for the authz gate? →
a default/system actor for v1 (Open Items).
**Verification:** `POST/GET/PUT/DELETE /tasks` with `404`/`422`; create a Task, restart server, `GET`
it back; live PGLite round-trip (`bin/test-live`).
**Dependencies:** 1.2.

## Sub-phase 1.4 — Run (`AgentRun`) controller (custom)
**Objective:** Expose the `Run` surface — read + the bespoke domain transitions.
**Files:** new `server/routers/run_router.py`.
**Key endpoints:** `GET /runs/{id}`, `GET /runs?task_id=…` (`runs_for_task`),
`POST /runs` (`record_run`), `PUT /runs/{id}/status` (`set_status`),
`PUT /runs/{id}/output-location` (`set_output_location`).
**Design review:** `AgentRunService` is NOT vanilla CRUD (`record_run`, not `create`) → a **custom
controller**, not the factory (the `cast-custom-controller` case). Keep verbs aligned to the
service's real methods; don't force a generic CRUD shape onto a domain service.
**Verification:** record a run, read it by id + by task_id, transition status; restart persistence.
**Dependencies:** 1.1 (independent of 1.2/1.3 — can run parallel to 1.3).

## Sub-phase 1.5 — The agent-dispatch surface (the dispatcher over HTTP)
**Objective:** Expose the existing dispatcher over HTTP — the seam the Phase-2 `crud-builder` calls.
**Files:** new `server/routers/dispatch_router.py` (+ a thin `ChildDispatch` binding if needed).
**Key endpoint:** `POST /dispatch` — body: `{parent_run_id|parent_manifest, target_agent_name,
task_id, inputs}`. Flow: `check_delegation_allowed(parent_manifest, target)` (→ `403` on
`DelegationDenied`) → `dispatch_child(...)` → capture the child envelope →
`resolve_proof_of_check(envelope, …)` → return the proven `ChildOutcome` (or `422` if a declared
checker has no proof). The **server is the dispatcher**: it enforces proof; it never calls a checker.
**Design review — the one real risk in Phase 1:** wrapping the *proof-enforcement* seam is
straightforward (reuse `dispatch_child` + `resolve_proof_of_check` + `contract/dummy` to test). The
**heavier, riskier piece is actually *running a real builder agent*** (spawning a Claude session) —
that binding sits behind the `ChildDispatch` Protocol and may need a subprocess/session adapter mined
from diecast's `cast-server` child dispatch. **Scope decision:** Phase 1 proves the HTTP seam +
proof-enforcement + allow-list using the **canned/dummy agent**; the real session-spawning binding is
flagged and may extend into Phase 2 (it's exactly what the Workforce needs). Surface this honestly —
do not claim a live builder runs end-to-end in Phase 1 unless the session adapter lands.
**Verification:** dispatch `contract/dummy` canned agent → proven outcome; force a missing-proof
envelope → `422`; disallowed target → `403`; uses `contract/dummy/roundtrip` as the harness.
**Dependencies:** 1.1.

## Sub-phase 1.6 — Reconciliation note
**Objective:** Record that the neoorg server *is* the dispatcher the maker-checker contract names.
**Files:** new `docs/plan/2026-06-25-server-as-dispatcher-note.md` (or goal dir).
**Content:** map `check_delegation_allowed` → allow-list enforcement, `dispatch_child` → the dispatch
seam, `resolve_proof_of_check` → proof enforcement; state the HTTP `POST /dispatch` contract; note
that `crud-builder` (Phase 2) is a maker that calls this endpoint to dispatch sub-makers and consumes
proven envelopes. Flag the `/cast-update-spec` follow-up for `agent-communication` §8 / `maker-checker`.
**Verification:** note exists; every Phase-2 builder charter will reference it.
**Dependencies:** conceptually after 1.5 (documents its contract); can draft anytime.

---

## Build order (within Phase 1)

```
1.1 skeleton ─┬─► 1.2 factory ──► 1.3 Task controller ─┐
              ├─► 1.4 Run controller ───────────────────┤
              └─► 1.5 dispatch surface ─────────────────┴─► 1.6 reconciliation note
```
**Critical path:** 1.1 → 1.2 → 1.3. 1.4 and 1.5 parallel after 1.1. 1.6 documents 1.5.
**Estimated effort:** 2–4 sessions total (much already exists; 1.5's real-session binding is the swing).

## Phase-level verification

- `bin/neoorg-server` boots; `GET /health` 200.
- `/tasks` + `/runs`: full CRUD / domain verbs with `404`/`422`; create-then-restart persistence (live PGLite via `bin/test-live`).
- `POST /dispatch`: canned-agent proven outcome; missing-proof → 422; disallowed → 403.
- `uv run leak-guard` green; existing `pytest -m "not live"` green; new router tests pass.

## Open items (Phase 1)

- **[NEEDS CLARIFICATION: server auth]** localhost-only, no auth assumed for v1 (it's load-bearing for
  the Workforce, but a dev server). Confirm if that changes.
- **[NEEDS CLARIFICATION: authz actor under no-auth]** the §5 Task authz gate needs an acting caller;
  v1 uses a default/system actor — confirm.
- **[NEEDS CLARIFICATION: real builder-agent execution]** Phase 1 proves dispatch with the dummy
  agent; the subprocess/session adapter that runs a *real* builder (mined from `cast-server`) may slip
  into Phase 2. Flagged, not hidden.
- **[USER-DEFERRED]** full refactor of the entity-in `BaseService.create/update` internal callers —
  Phase 1 adds an additive schema-in shim only; the cleanup sweep is later ("we can always fix").

## Decisions (Phase 1)

| Date | Chose | Over | Because |
|------|-------|------|---------|
| 2026-06-25 | Reuse the existing Alembic migrations; launcher runs `upgrade head` on start | `create_all` in the app | Migrations `0001–0007` already define the schema; `create_all` bypasses them. |
| 2026-06-25 | Schema-in controllers + factory (cast styling); additive schema-in shim on services | Build ORM entities in handlers · refactor `BaseService` signature now | Keeps the layering clean without disturbing the internal entity-in callers (deferred sweep). |
| 2026-06-25 | Custom controller for `Run` (bespoke `AgentRunService`); factory for `Task` | Force the factory onto `AgentRun` | `record_run`/`set_status`/… aren't vanilla CRUD — the `cast-custom-controller` case. |
| 2026-06-25 | Phase 1 proves dispatch with the `contract/dummy` canned agent | Block Phase 1 on the real session-spawning adapter | Proves the proof-enforcement seam now; defers the heavier real-agent binding (likely Phase 2). |
