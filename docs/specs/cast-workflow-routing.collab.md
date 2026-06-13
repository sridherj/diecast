---
feature: cast-workflow-routing
module: cast-server
linked_files:
  - cast-server/cast_server/config.py
  - cast-server/cast_server/services/workflow_router_service.py
  - cast-server/cast_server/routes/api_goals.py
  - cast-server/cast_server/services/goal_service.py
  - cast-server/cast_server/db/schema.sql
  - cast-server/cast_server/db/connection.py
  - cast-server/cast_server/models/goal.py
  - cast-server/cast_server/requirements_render/families.py
  - agents/cast-refine-requirements/cast-refine-requirements.md
  - cast-server/tests/test_workflow_router_service.py
  - cast-server/tests/test_api_goals_route.py
last_verified: "2026-06-12"
---

# Cast Workflow Routing — Spec

> **Spec maturity:** draft
> **Version:** 1
> **Updated:** 2026-06-12
> **Status:** Draft

## Intent

Refine Requirements v2 makes a goal **workflow-aware**: once Phase 2 has classified it
into one of the nine `WorkFamily` values, Phase 3b **routes** that family to a
family-specific downstream-workflow **handle** — a named **stub** for every not-yet-built
pipeline. v2 ships the **seam and the stubs, not the pipelines** (FR-015 of the source
plan): every `WORKFLOW_REGISTRY` value is `status="stub"`; flipping one to `"implemented"`
later is a registry-only diff with no seam change.

This spec is the **contract future per-family pipeline goals cite**. It documents the
user-facing routing surface that lives in three code homes — the `WORKFLOW_REGISTRY` in
`cast-server/cast_server/config.py`, the pure resolver + idempotent recorder in
`cast-server/cast_server/services/workflow_router_service.py`, and the
`POST /api/goals/{slug}/route` endpoint in `cast-server/cast_server/routes/api_goals.py`.
The code is authoritative: where this spec and the code ever disagree, the code wins and
this spec is the bug.

The load-bearing design insight (exploration Playbook 06) is that **phase-agnosticism is
not a feature you build — it is a property you fail to destroy.** `resolve` is a PURE +
TOTAL function of the *persisted* family (it takes the family as an argument and never
re-classifies), so any caller in any phase gets the same answer for free. This spec does
**not** redefine the `WorkFamily` vocabulary; it **cites**
[`cast-goal-classification.collab.md`](./cast-goal-classification.collab.md), which owns
the family set and the single add-a-family checklist that this routing layer extends.

Three hard boundaries frame everything below:

- **The router never guesses.** `resolve` is total over its whole domain — the 9
  families, `None`, and any unknown string — but the two non-routable statuses
  (`unmatched`, `needs-classification`) are *returned and announced*, never persisted.
- **`goals.workflow_family` is the single authoritative routing record** — the only
  writer-of-record; front-matter `classification.family` is the document's
  self-description, reconciled to the column on the next refine.
- **In v2 there is exactly one caller** — `cast-refine-requirements`. No planner,
  executor, or other phase is wired to the router; the door is shipped, not its future
  callers.

## User Stories

### US1 — A classified goal resolves to a downstream-workflow handle (Priority: P1)

**As a** caller holding a goal's classified `WorkFamily`, **I want** to resolve it to a
named workflow handle (its status and steps), **so that** I can show the user where the
goal is headed without re-running classification.

**Independent test:**
`cast-server/tests/test_workflow_router_service.py` asserts `resolve` returns a real
`WorkflowHandle` for all nine families plus `None` plus an unknown string — 0 exceptions,
0 `None` returns — and that each of the three edge handles carries the right `status` and
a non-empty `message`.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN `resolve(family)` is called with a registered family, THE SYSTEM
  SHALL return `WorkflowHandle(family, entry["status"], steps=tuple(entry["steps"]),
  pipeline_ref=entry.get("pipeline_ref"), message=...)` with no DB and no LLM access.
- **Scenario 2:** WHEN `resolve(None)` is called, THE SYSTEM SHALL return a
  `WorkflowHandle(None, "needs-classification", ...)` whose message tells the caller to
  run `/cast-refine-requirements` first — the router never guesses.
- **Scenario 3:** WHEN `resolve(family)` is called with a string not in
  `WORKFLOW_FAMILIES`, THE SYSTEM SHALL return a `WorkflowHandle(family, "unmatched", ...)`
  whose message names the registry's known families — a Special Case that announces itself,
  never a silent Null Object.

### US2 — A routing decision persists once on the goal, idempotently (Priority: P1)

**As a** caller recording where a goal routed, **I want** the family, the
`{family}:{status}` handle, and a `routed_at` stamp written to the goal exactly once per
change, **so that** the decision survives on the goal row and re-recording the same family
is a no-op.

**Independent test:**
`cast-server/tests/test_workflow_router_service.py` records the same family twice and
asserts the second call is a no-op (`recorded: False`, `routed_at` unchanged), then records
a different family and asserts `recorded: True`, `changed: True`, and a `previous_family`.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `record_routing_decision(slug, family, handle)` is called with a
  routable handle (`family in WORKFLOW_FAMILIES` AND `handle.status` in
  `("stub", "implemented")`), THE SYSTEM SHALL `UPDATE goals SET workflow_family=?,
  routing_handle=?, routed_at=?` and return `{"recorded": True, ...}`.
- **Scenario 2:** WHEN the goal already carries the same `workflow_family` and
  `routing_handle`, THE SYSTEM SHALL make no write and return
  `{"recorded": False, "changed": False, ...}` with `routed_at` untouched.
- **Scenario 3:** WHEN the handle is non-routable (`unmatched`/`needs-classification`) or
  the family is unknown, THE SYSTEM SHALL raise `ValueError` — callers must never persist a
  non-routable handle.
- **Scenario 4:** WHEN the goal's `goal.yaml` is absent at record time, THE SYSTEM SHALL
  still write the DB row and SHALL NOT raise — the yaml mirror is best-effort and the DB is
  authoritative (Decision D5).

### US3 — Any phase resolves a goal's route through one HTTP door (Priority: P1)

**As a** future phase or agent, **I want** a single endpoint that resolves (and records) a
goal's route from its persisted family, **so that** I get a phase-agnostic, byte-stable
answer without ever touching a classifier.

**Independent test:**
`cast-server/tests/test_api_goals_route.py` seeds goals, calls `POST /api/goals/{slug}/route`
with and without a body, and asserts the 200 handle JSON, the persisted columns, the 404 on
an unknown slug, and that a no-body call after an unrelated state change returns
byte-identical handle JSON.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `POST /api/goals/{slug}/route` is called with body
  `{"family": "<WorkFamily value>"}`, THE SYSTEM SHALL resolve that family, record it, and
  return **200** with `{family, status, steps, pipeline_ref, message, recorded, changed,
  previous_family, routing_handle, routed_at}`.
- **Scenario 2:** WHEN the same endpoint is called with no body, THE SYSTEM SHALL read
  `goal["workflow_family"]` from the DB, resolve it, and re-record idempotently — a no-op
  when unchanged, leaving `routed_at` untouched (the SC-005 byte-stability path).
- **Scenario 3:** WHEN the slug is unknown, THE SYSTEM SHALL return **404**; WHEN the body
  carries an unknown family string or the persisted family is `None`, THE SYSTEM SHALL
  return **200** with the `unmatched` / `needs-classification` handle and `recorded: false`
  — totality means the API never 500s on content.

### US4 — The routing seam is provably free of re-classification (Priority: P2)

**As a** maintainer relying on phase-agnosticism, **I want** the router and the `/route`
handler proven (by test, not inspection) to contain no classifier, subprocess, or
agent-dispatch imports, **so that** no future edit can quietly re-introduce a
re-classification into the pure-DB path.

**Independent test:**
A source-pin test (Decision D4) reads the `workflow_router_service` module AND the `/route`
handler module source and asserts neither contains agent-dispatch / subprocess / classifier
imports — mirroring the no-`STARTER_TASKS` pin; this REPLACES the SC-005 "assert by code
inspection" step.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the source-pin test runs, THE SYSTEM SHALL fail CI if the router or
  the `/route` handler imports anything that could re-classify (subprocess, agent dispatch,
  the classifier).
- **Scenario 2:** WHEN a goal's unrelated state changes (e.g. a `phase` flip) and the
  no-body `/route` path runs again, THE SYSTEM SHALL return a byte-identical handle with no
  classifier anywhere in the call path.

### US5 — Adding or graduating a family follows one canonical checklist (Priority: P2)

**As a** future maintainer evolving the taxonomy or shipping a pipeline, **I want** the
routing-side edits documented as an extension of the ONE canonical add-a-family checklist,
**so that** I follow a single list end-to-end and the registry never silently drifts.

**Independent test:**
`cast-server/tests/test_workflow_router_service.py` asserts
`set(WORKFLOW_REGISTRY) == {f.value for f in WorkFamily}` — the registry/enum key-set pin —
so a forgotten `WORKFLOW_REGISTRY` entry for a newly added family fails CI.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a new family is added, THE SYSTEM SHALL require a matching
  `WORKFLOW_REGISTRY` entry in `config.py` (the routing home), recorded as a labeled
  extension of the canonical checklist in `cast-goal-classification.collab.md`, not as a
  second standalone list.
- **Scenario 2:** WHEN a family graduates from `stub` to `implemented`, THE SYSTEM SHALL
  require only a registry-only diff — flip the entry's `status` and set its `pipeline_ref`
  — with no change to the resolver, the recorder, the route, or the schema (FR-015).

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | `WORKFLOW_REGISTRY: dict[str, dict]` lives in `cast-server/cast_server/config.py` beside `STARTER_TASKS`. Keys are `WorkFamily` **string** values (one vocabulary, two homes) so `config.py` stays the dependency-free bottom layer (no `requirements_render` import). `WORKFLOW_FAMILIES = frozenset(WORKFLOW_REGISTRY)` is the derived closed set. | A pin test asserts `set(WORKFLOW_REGISTRY) == {f.value for f in WorkFamily}` — drift fails CI. |
| FR-002 | Every registry value is `status="stub"` with a non-empty `steps` list in v2 (the seam-not-pipelines rule). `bug_fix`'s steps are spec-mandated (`logs → RCA → confirm → fix/test`); all other step wordings are owner-editable copy that render into `goal.yaml` + the refinement summary, not contracts. | `generic` gets a *named* stub like every other family — an announced decision, never a silent fallback. |
| FR-003 | `WorkflowHandle` (a frozen dataclass in `workflow_router_service.py`) has fields `family: str \| None`, `status: str`, `steps: tuple[str, ...] = ()`, `pipeline_ref: str \| None = None`, `message: str = ""`. `status` is one of `implemented \| stub \| unmatched \| needs-classification`. | `pipeline_ref` is reserved for when a family graduates (the agent/orchestration target). |
| FR-004 | `resolve(family: str \| None) -> WorkflowHandle` is PURE + TOTAL — no DB, no LLM, no `db_path` parameter. `None` → `needs-classification`; an unknown string → `unmatched` (message names `sorted(WORKFLOW_FAMILIES)`); a registered family → a `stub`/`implemented` handle carrying `steps` and `pipeline_ref`. It returns a real handle for every input (0 exceptions, 0 `None` returns). | The two edge handles announce themselves; `unmatched` is a Special Case, never a silent Null Object. |
| FR-005 | `record_routing_decision(slug, family, handle, goals_dir=None, db_path=None) -> dict` is the ONLY writer of the routing columns. It uses the house DB pattern (`get_connection(db_path)`, try/finally close). It guards `family in WORKFLOW_FAMILIES` AND `handle.status in ("stub", "implemented")`, raising `ValueError` otherwise. | Callers must never persist `unmatched`/`needs-classification`. |
| FR-006 | Recording is idempotent: if the goal's current `workflow_family == family` AND `routing_handle == f"{family}:{handle.status}"`, the call is a no-op returning `{"recorded": False, "changed": False, "previous_family": <prior>, "routing_handle": <handle>}` with `routed_at` untouched. Otherwise it `UPDATE goals SET workflow_family=?, routing_handle=?, routed_at=?` (ISO-8601 UTC) and returns `{"recorded": True, "changed": <prior family existed and differed>, "previous_family", "routing_handle", "routed_at"}`. | First-ever routing → `changed: False`, `previous_family: None`. |
| FR-007 | The stored handle format is `goals.routing_handle = f"{family}:{status}"` (e.g. `bug_fix:stub`). It is a point-in-time **STAMP**, not derived-on-read (Decision D1): it can lag the registry — when a family graduates `stub → implemented`, an already-routed goal keeps its old `{family}:stub` handle until re-routed. Re-route IS the refresh mechanism. | Deriving-on-read was rejected to preserve byte-stability + the human-visible `goal.yaml` stamp. Accepted, documented staleness, not a bug. |
| FR-008 | The recorder mirrors the stamp to `goal.yaml` via `goal_service._update_goal_yaml_fields(_resolve_goal_dir(...), {...})` best-effort: the DB is authoritative and a missing/unreadable `goal.yaml` is logged, not raised (Decision D5). | Same resolve-dir path `update_status` uses, so externally-routed goals render correctly. |
| FR-009 | The `goals` table carries three routing columns: `workflow_family TEXT`, `routing_handle TEXT`, `routed_at TEXT`. They render into `goal.yaml` via conditional includes in `goal_service._write_goal_yaml` (the `gstack_dir` precedent), so a full re-render preserves them. `GoalUpdate` gains `workflow_family` and `routing_handle` (NOT `routed_at` — server-set). | Schema edited in the canonical `cast-server/cast_server/db/schema.sql` + an idempotent `ALTER TABLE` in `_run_migrations()`. |
| FR-010 | `goals.workflow_family` is the AUTHORITATIVE routing record and single writer-of-record (Decision D2). Front-matter `classification.family` is the document's self-description, reconciled to the column on the next refine (Step 0 re-writes both). The divergence must NOT be "fixed" by making front-matter authoritative — that re-introduces a parser read into the pure-DB path. | Authority lives on the DB column; the front-matter is descriptive. |
| FR-011 | `POST /api/goals/{slug}/route` is the one phase-agnostic door (JSON in/out, agent-facing like `api_agents.py`). **With body** `{"family": ...}` (the refinement path): resolve that family, then record it. **No body** (the phase-agnostic path, any future phase/agent): `family` falls back to the persisted `goal["workflow_family"]`; resolve + idempotent re-record. | Optional body via `RouteRequest(BaseModel)` with `family: str \| None = None`. |
| FR-012 | The `/route` response is **200** with `{family, status, steps, pipeline_ref, message, recorded, changed, previous_family, routing_handle, routed_at}`. An unknown *slug* is **404**. An unknown family string in the body → **200** with the `unmatched` handle + `recorded: false`; a `None` persisted family + no body → **200** with `needs-classification` + `recorded: false`. Totality ⇒ the API never 500s on content. | The no-op no-body path leaves `routed_at` at the goal's existing stamp (the byte-stability guarantee). |
| FR-013 | The recording rule: only valid `WorkFamily` values ever persist. `unmatched` and `needs-classification` handles are returned and announced, never recorded — no garbage in `goal.yaml`. The `/route` handler records only when `handle.status in ("stub", "implemented")`. | The recorder's `ValueError` guard is the backstop if a caller violates this. |
| FR-014 | The `/route` handler imports nothing that could re-classify — it calls only `goal_service.get_goal` + `workflow_router_service.{resolve, record_routing_decision}`. A source-pin test (Decision D4) enforces that on both the handler module and the router module, replacing the phase-gate "assert by code inspection" step. | No agent dispatch, no LLM, no subprocess in the routing path. |
| FR-015 | In v2 the router has exactly one caller: `cast-refine-requirements`. No planner, executor, UI routing panel, rules engine, or `goal_routing` history table is wired (HOLD SCOPE — ship the door, not the future callers). | Future callers adopt the interfaces in this spec verbatim. |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | This spec passes `bin/cast-spec-checker docs/specs/cast-workflow-routing.collab.md` (no `--family` → full-spec profile) with zero error findings. | `bin/cast-spec-checker docs/specs/cast-workflow-routing.collab.md` exits 0. |
| SC-002 | Every name in this spec matches the code byte-for-name: `WORKFLOW_REGISTRY`, `WORKFLOW_FAMILIES` (`config.py`); `WorkflowHandle`, `resolve`, `record_routing_decision`, the four-value status set, the `{family}:{status}` handle format (`workflow_router_service.py`); `POST /{slug}/route` + the ten response keys (`api_goals.py`). | Name-match audit: `grep -nE "workflow_family\|routing_handle\|routed_at\|WorkflowHandle\|needs-classification\|unmatched"` over the spec vs. the three code files. |
| SC-003 | `resolve` totality is documented exactly as implemented: 9 families + `None` + unknown string → a real handle, 0 exceptions, 0 `None`; the three edge handles carry the right status + a non-empty message. | `cast-server/tests/test_workflow_router_service.py` totality tests are green; the resolve-totality requirement matches. |
| SC-004 | The idempotency, recording rule, staleness (D1), authority (D2), and best-effort-yaml (D5) contracts are documented as intentional behavior, matching the recorder + the `/route` handler. | `cast-server/tests/test_workflow_router_service.py` + `test_api_goals_route.py` are green; the idempotency / staleness / yaml-mirror / authority / recording-rule requirements match the code. |
| SC-005 | The spec is registered in `docs/specs/_registry.md` with a scope one-liner and linked files. | `grep -c 'cast-workflow-routing' docs/specs/_registry.md` ≥ 1. |
| SC-006 | The add-a-family / graduate-a-family routing steps live as a labeled extension of the ONE canonical checklist in `cast-goal-classification.collab.md` — this spec cross-references it and does NOT restate a separate list (Decision D3). | Manual check: this spec's US5 / Cross-references point to the classification spec; `grep -ni "add.a.family" docs/specs/cast-workflow-routing.collab.md` finds only the cross-reference, not a standalone list. |

## Decisions

| Date | Chose | Over | Because |
|------|-------|------|---------|
| 2026-06-11 | `routing_handle` is STORED (a point-in-time stamp) | Derived-on-read | Preserves the byte-stability test and the human-visible `goal.yaml` stamp; documented staleness until re-route, not a bug (Decision D1). |
| 2026-06-11 | `goals.workflow_family` is the authoritative routing record | Front-matter `classification.family` authoritative | Keeps the phase-agnostic pure-DB path free of a parser read; front-matter reconciles to the column on next refine (Decision D2). |
| 2026-06-11 | One canonical add-a-family checklist (in the classification spec), routing appends its homes | A second standalone checklist in this spec | One list a maintainer follows end-to-end — DRY; a duplicate is exactly the drift this prevents (Decision D3). |
| 2026-06-11 | No-reclassify guarantee is an automated source-pin test | "Assert by code inspection" | A test asserting the router + `/route` handler source contain no agent-dispatch/subprocess/classifier imports cannot rot (Decision D4). |
| 2026-06-11 | Missing-`goal.yaml` recording is pinned best-effort | Raising on a missing yaml | The DB is authoritative; a missing yaml is logged, not raised, and a test pins it (Decision D5). |

## Out of scope

The following are explicitly NOT covered by this spec.

- **Code changes to `config.py`, the resolver, the route, models, or schema.** This spec is
  documentation lockstep; sp1a–sp3 already landed and are authoritative. If the spec and
  code disagree, the code wins and the spec is the bug — never silently "fix" code from the
  spec.
- **Redefining the `WorkFamily` vocabulary.** The family set is owned by
  [`cast-goal-classification.collab.md`](./cast-goal-classification.collab.md); routing
  cites it, never redefines it.
- **A second, standalone add-a-family checklist** (Decision D3 forbids it — the routing
  homes are appended to the ONE canonical list in the classification spec).
- **Future callers and pipelines.** In v2 only `cast-refine-requirements` calls the router,
  and every registry value is a `stub`; wiring planners/executors and implementing the
  per-family pipelines are out of scope (HOLD SCOPE).
- **The delegation + output-json contracts.** `POST /api/goals/{slug}/route` is a plain JSON
  API, not agent dispatch — it produces no `.output.json` envelope and no
  output-file/polling semantics, so `cast-delegation-contract.collab.md` and
  `cast-output-json-contract.collab.md` do not apply and are untouched.

## Cross-references

- Naming-contract source of truth: `cast-server/cast_server/services/workflow_router_service.py`
  (`WorkflowHandle`, `resolve`, `record_routing_decision`), `cast-server/cast_server/config.py`
  (`WORKFLOW_REGISTRY`, `WORKFLOW_FAMILIES`), `cast-server/cast_server/routes/api_goals.py`
  (`POST /{slug}/route`).
- Family vocabulary + the single canonical add-a-family checklist this routing layer extends:
  [`cast-goal-classification.collab.md`](./cast-goal-classification.collab.md). Routing cites
  the vocabulary, never redefines it.
- `/route` is a plain JSON API, NOT agent dispatch — the delegation + output-json contracts
  do not apply: [`cast-delegation-contract.collab.md`](./cast-delegation-contract.collab.md),
  [`cast-output-json-contract.collab.md`](./cast-output-json-contract.collab.md).

## Open Questions

- **[USER-DEFERRED]** Whether a graduated family should trigger an automatic re-route of
  every already-routed goal (so stored `{family}:stub` stamps refresh to `:implemented`).
  v2 keeps the stamp stale until the goal is re-routed (re-route is the refresh). Resolver:
  a future pass once the first family graduates.
- **[USER-DEFERRED]** Whether to add a human-facing UI routing panel beyond the single
  `cast-refine-requirements` caller (the thin read-only `/cast-router` resolve-and-show
  skill already ships in v2). Out of v2 scope (HOLD SCOPE — ship the door, not the future
  callers).
