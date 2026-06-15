# Code Exploration — Step 6: Phase-Agnostic Workflow Router

**Goal context:** Refine Requirements v2 — Workflow-Aware, HTML-First Requirements Refinement.
Step 6 designs the **phase-agnostic workflow router**: given a goal's classification, resolve a
family-specific *downstream-workflow handle* (bug → logs→RCA→confirm→fix/test; prototype →
spike→demo→learnings), **record the routing decision on the goal** (FR-014), and make the router
invokable from **any phase** without re-running refinement (FR-016). Decide the **seam** — does
classify+route live *inside* `cast-refine-requirements` or get *extracted* as a standalone
agent/service? v2 ships the **seam + named pipeline stubs**, not real pipelines (FR-015);
unimplemented families route to a **named stub**, never a silent generic fallback. Plus
agent-as-caller parity (FR-013).

**Codebase:** `/home/sridherj/workspace/diecast` (same git repo as `/data/workspace/diecast`;
`.cast` symlinks the goal dir). cast-server is the relevant subtree.
**Date:** 2026-06-11
**Method:** GO-BROAD. Direct Glob/Grep/Read across cast-server (config, schema, services,
routes, models) + the agent fleet (`agents/`). The code-review-graph MCP graph was not built
(startup hook reported "No knowledge graph found"), so every file:line below was verified by
direct read. This brief maps where we ARE so the synthesizer understands the starting point and
migration cost — it does **not** constrain recommendations to current code.

---

## TL;DR for the synthesizer

**There is no router, no classifier, and no family concept anywhere in the codebase today. The
*only* "downstream workflow" that exists is a single, hardcoded, family-agnostic task list seeded
at goal acceptance — which is exactly the silent generic fallback FR-015 says to abolish.**

- **The de-facto router is `STARTER_TASKS` + `_create_starter_tasks`.** Every accepted goal —
  regardless of kind — is seeded with the *same* 7-ish tasks (refine → explore → research-notes →
  high-level-plan → detailed-plan), defined as a static list in `config.py:77-97` and inserted by
  `goal_service.py:301` `_create_starter_tasks`. This is the closest thing to "routing a goal into
  a downstream workflow" that exists, and it is **one universal pipeline for all goals**. The spec's
  whole premise (family-specific routing) is a *replacement* for this static seed.
- **The routing decision has nowhere to live (FR-014).** The `goals` table (`schema.sql:1-14`) has
  `slug, title, status, phase, origin, in_focus, dates, tags, folder_path, gstack_dir,
  external_project_dir` — **no `workflow_family`, no `routing_decision`, no classification column.**
  Recording a decision on the goal is net-new schema (or an abuse of the free-form `tags` JSON).
- **`cast-refine-requirements` does not classify.** Grep for `classif|family|workflow|route|pill`
  across the 434-line agent finds only the word "workflow" as a section header ("## Workflow") and
  passing mentions of "downstream agents." It produces a spec-kit doc; it has **zero** family
  detection, no pill, no routing. So "classify+route inside refinement" is a *feature to add*, not a
  thing to extract.
- **The seam decision is strongly pre-disposed toward extraction by the existing dispatch
  architecture.** There is exactly **one dispatch door** — `POST /api/agents/{name}/trigger`
  (`api_agents.py:88`) — used *identically* by the human UI and by a parent agent delegating to a
  child (via `delegation_context`). `AgentConfig` already models agents as first-class addressable
  units (`dispatch_mode: http|subagent`, `trust_level`, `allowed_delegations`). A standalone router
  (agent or service) called through this same door gets **FR-013 agent-parity for free**. Burying it
  inside `cast-refine-requirements` makes it un-callable from planning/execution without re-running
  the entire refinement agent — a direct FR-016 violation.
- **There's a clean precedent for "pure deterministic logic extracted as a service":**
  `orchestration_service.py` is exactly that — DAG/manifest logic with **no** subprocess/Claude
  deps, importable *and* CLI-runnable, fully unit-testable. The deterministic half of the router
  (family → handle resolution + record-on-goal) should mirror it; the *classification* half
  (LLM judgment) is the part that needs an agent.
- **"Named pipeline behind a handle that enumerates steps" already exists structurally** as the
  orchestration `_manifest.md` Phase Overview table (parsed by `parse_manifest`,
  `orchestration_service.py:51`) and as the `STARTER_TASKS` list-of-step-dicts shape. A family
  **stub** (FR-015) is naturally a named handle that resolves to an enumerated step list that is not
  yet wired to real agents.

**Migration cost shape:** the router is **greenfield** (no code to refactor away), so the cost is
all *new construction* + *one schema column* + *one decision* (where classification is persisted so
re-resolution never re-classifies). The good news: every primitive it needs — a single dispatch
door, a pure-logic-service pattern, a per-family step-list shape, a DB→goal.yaml render for
recording decisions — **already exists and is proven**; the router assembles them rather than
inventing them.

---

## 1. Data Model & Schema

Canonical schema: `cast-server/cast_server/db/schema.sql` (SQLite, raw `sqlite3`, no ORM).
Pydantic mirrors in `cast-server/cast_server/models/`.

### What the goal entity knows (and doesn't)

`goals` (`schema.sql:1-14`) — the entity a routing decision must attach to:

| Column | Relevance to Step 6 |
|--------|---------------------|
| `slug` (PK), `title` | identity |
| `status` (idea/accepted/…) | lifecycle gate (`config.py:43`) |
| **`phase`** (TEXT, nullable) | the field FR-016 is "agnostic" to — one of `requirements/exploration/plan/execution` (`config.py:52`), freely set |
| `origin`, `in_focus`, dates | metadata |
| **`tags`** (TEXT, JSON array) | the *only* free-form, structured-ish field — the sole place a `family:bug` style marker could live without schema change (weak; unstructured; see §3) |
| `folder_path`, `gstack_dir`, `external_project_dir` | filesystem wiring |

**There is no classification/family/routing field.** `Goal` Pydantic model (`models/goal.py:7-20`)
mirrors exactly these columns; `GoalUpdate` (`models/goal.py:30-37`) exposes only
`status, phase, in_focus, tags, gstack_dir, external_project_dir` as mutable. **Recording a routing
decision (FR-014) requires either a new column or repurposing `tags`.**

### Where "downstream workflow" actually lives today

Not in a table — in **config + tasks**:

- `STARTER_TASKS` (`config.py:77-97`): a hardcoded list of step dicts
  `{title, phase, tip, recommended_agent, artifact?}`. **This list shape is, structurally, already a
  "pipeline definition."** It just happens to be (a) singular and (b) family-blind.
- `tasks` rows (`schema.sql:16-39`) carry `phase` and `recommended_agent` — so the seeded pipeline
  becomes a set of phase-tagged task rows each optionally pointing at an agent.

```
goals (slug PK)  ── phase: one of [requirements, exploration, plan, execution]  (single TEXT col)
   │                 (NO family / classification / routing_decision column)
   │
   └─1:N─ tasks (goal_slug FK)
            ├─ phase            ← which phase this step belongs to
            └─ recommended_agent ← the ONLY link from a step to an agent ("the route")

config.STARTER_TASKS  ──(seeded once at acceptance)──▶  the SAME tasks for EVERY goal
                                                         = the de-facto generic pipeline
agent_runs (id PK) ──N:1── goals/tasks   ← execution telemetry (parent_run_id threads delegation)
```

**Critical observation:** the routing primitive the spec wants (classification → family-specific
handle, recorded on the goal) maps onto **two net-new things**: (1) a place on the goal to record
the family + chosen handle, and (2) a per-family replacement for the singular `STARTER_TASKS`. The
DB knows nothing about families today.

---

## 2. Existing Implementation

### 2a. The de-facto router: `_create_starter_tasks` (the thing being replaced)

`goal_service.py:301` `_create_starter_tasks(slug, …)`:
- Called on goal acceptance (`update_status` → `goal_service.py:144`) and `create_goal`
  (`goal_service.py:100`). Idempotent (skips if any task row exists, `:312-317`).
- Reads `config.STARTER_TASKS` and `create_tasks_batch`es them, also stubbing artifact files
  (`:324-330`).
- **Family-blind:** identical output for a bug, a PRD, a spike, a data-analysis question.

This is the **single generic fallback** FR-015 names as the anti-pattern. Today it is *the only
pipeline*, applied silently to everything. Step 6's router is the seam that makes this decision
explicit and family-specific (with named stubs where a real pipeline doesn't exist yet).

### 2b. How a "route" surfaces to the user: recommended-agents panel

`agent_service.py:1649` `get_recommended_agents(goal_slug)`:
- `SELECT DISTINCT recommended_agent FROM tasks WHERE goal_slug=? AND … status != 'completed'`,
  joined against the agent registry.
- Surfaced via `GET /api/agents/goals/{slug}/recommendations` (`api_agents.py:76`) into
  `fragments/agent_panel.html`.

So the current "what should I run next on this goal?" answer is **derived from the seeded task
rows' `recommended_agent` fields** — a static projection of the generic pipeline, not a
classification-driven resolution. A real router would either (a) seed family-specific tasks (so this
panel reflects the route) or (b) expose a separate "routed workflow" surface.

### 2c. The single dispatch door (the FR-013 parity surface)

`POST /api/agents/{name}/trigger` (`api_agents.py:88`) is **the** way any agent run starts:
- Accepts `goal_slug, context, task_id, scheduled_at, parent_run_id, delegation_context`
  (`:91-106`).
- The **same endpoint** is used by the human-facing UI *and* by a parent agent delegating to a
  child — the only difference is whether `delegation_context` (a `DelegationContext`,
  `models/delegation.py:23`) is attached. This is the literal "same door for humans and agents"
  that FR-013 demands.
- Delegation context carries `goal_phase` (already present, `delegation.py:9`!), `instructions`,
  `relevant_artifacts`, `constraints`, `output` config. **`model_config = ConfigDict(extra="allow")`
  on `DelegationContextData` (`delegation.py:6`)** means a router could pass a custom field
  (e.g. `workflow_family`, `routing_handle`) through delegation *today* without a model change.
- `agent_service.trigger_agent(...)` enforces the dispatch precondition (external_project_dir set,
  else 422 `missing_external_project_dir`, `api_agents.py:142`).

**Implication for the seam:** an extracted router — whether a `cast-workflow-router` *agent* (dispatched
via this door) or a *service* exposed at a new route — inherits agent-parity by construction. A future
planning/execution agent calls the router exactly as the requirements phase does.

### 2d. Agents are already first-class, addressable, configurable units

`AgentConfig` (`models/agent_config.py:16-31`): `agent_id, model, headless, timeout_minutes,
trust_level (readonly|standard|privileged), allowed_delegations: list[str], context_mode,
interactive, artifact_directory, dispatch_mode (http|subagent)`. Loaded per-agent from YAML
(cached by mtime, `:60`). The fleet (`agents/`) holds ~57 agents, several of which are
orchestrators (`cast-orchestrate`, `cast-create-execution-plan`, `cast-subphase-runner`,
`cast-crud-orchestrator`, `cast-integration-test-orchestrator`, `cast-preso-orchestrator`).

**Two facts matter for the router:**
1. `allowed_delegations` already declares *which* agents an agent may dispatch — the access-control
   primitive for "refinement may call the router," "the router may call a family pipeline."
2. There is precedent for an agent whose whole job is to *dispatch other agents along a plan*
   (`cast-orchestrate`) — the natural future home of a *real* family pipeline.

### 2e. The "named pipeline behind a handle" precedent: orchestration manifest

`orchestration_service.py` is **pure DAG logic, no Claude/subprocess deps** (module docstring
`:1-4`). It parses an `_manifest.md` "Phase Overview" table into `Phase(id, name, file,
depends_on, status, notes)` (`parse_manifest`, `:51`), topo-sorts into parallelizable groups
(`build_execution_groups`, `:163`), and supports `--from-phase` resumption (`:173`). `cast-orchestrate`
then dispatches each phase through the trigger door.

This is the template for FR-015's "named pipeline that enumerates its steps": a family handle →
a manifest-like enumerated step list. A **stub** is simply such a handle whose steps are *named but
not yet wired to agents* — exactly representable as a `Phase`-list (or `STARTER_TASKS`-list) with no
`recommended_agent` resolved.

### 2f. The phase model (what "phase-agnostic" is agnostic *to*)

- `PHASES = [requirements, exploration, plan, execution]` (`config.py:52`) — a **closed set**.
- `update_phase` (`goal_service.py:151`) validates against it and sets a single TEXT column
  (`UPDATE goals SET phase=?`), then re-renders `goal.yaml` (`:176`). "Free-form — any valid phase
  allowed" (docstring `:153`). Blocked only for terminal-status goals (`:161`).
- **Nothing in the codebase varies *behavior* by phase** except artifact-discovery globs
  (`PHASE_ARTIFACTS`, `config.py:53`) and which starter tasks carry which `phase` label. There is no
  phase-state-machine, no per-phase capability gating. **This makes FR-016 cheap:** "phase-agnostic"
  just means the router keys off the goal's *classification* (a recorded value), never off its
  `phase` — and since phase is merely a freely-set string, the router has no phase coupling to break.

---

## 3. Gap Analysis

| # | Gap | Severity | Evidence |
|---|-----|----------|----------|
| 1 | **No classifier / family taxonomy anywhere.** `cast-refine-requirements` doesn't detect family; no enum, no pill, no signals. | **Critical** — the input to the whole router | grep `classif\|family\|workflow.?family` across agent + cast-server finds nothing (only error-classification in `error_memory_service`) |
| 2 | **No place to record the routing decision on the goal (FR-014).** No `workflow_family`/`routing_decision` column; `GoalUpdate` can't carry one. | **Critical** | `schema.sql:1-14`; `models/goal.py:30-37` |
| 3 | **The only downstream "pipeline" is a single hardcoded, family-blind task seed** — i.e. the silent generic fallback FR-015 forbids *is the current default behavior*. | **High** — the thing v2 replaces | `config.py:77-97` STARTER_TASKS; `goal_service.py:301` `_create_starter_tasks` |
| 4 | **No router placement / seam exists** — classify+route is neither inside refinement nor extracted; it's absent. The open question is greenfield. | **High** | no router module/agent/route; `cast-refine-requirements.md` has no routing |
| 5 | **No "named stub" concept.** No way to resolve a family to "steps named, not yet implemented." | **Medium** | no stub registry; STARTER_TASKS has no notion of unimplemented |
| 6 | **No phase-agnostic *invocation* of any capability.** Every agent run is dispatched ad hoc; there's no "resolve X from the goal's current state regardless of phase" call. | **Medium** | dispatch is always explicit agent-name + context (`api_agents.py:88`); no "resolve route" endpoint |
| 7 | **Re-classification has no update/notify path (US6 Scenario 4).** No mechanism to detect classification change and surface a changed downstream workflow. | **Medium** | no classification stored ⇒ nothing to diff; only UI `HX-Trigger` toasts exist for notification |
| 8 | **`recommended_agent` is the only step→agent link, and it's per-task, not per-family.** A family pipeline must either seed tasks or live somewhere new. | **Low/Medium** | `get_recommended_agents` `agent_service.py:1649` derives only from task rows |

---

## 4. Patterns & Conventions (what a router should imitate)

- **MVCS-lite:** `routes/` (thin FastAPI) → `services/` (fat fns, raw SQLite via `get_connection()`)
  → `models/` (Pydantic shapes). No ORM, no BaseRepository. A router service follows
  `goal_service`/`task_service` style.
- **Pure-logic service is an established shape:** `orchestration_service.py` deliberately has *no*
  external deps so it's CLI-runnable and unit-testable (`if __name__ == "__main__"` `:293`). **The
  deterministic resolver half of the router (family → handle, validate, return enumerated steps)
  should be exactly this shape** — pure, testable, importable by any agent or route.
- **DB-canonical → file render:** mutations write the DB then re-render `goal.yaml`
  (`_update_goal_yaml_fields`, `goal_service.py:366`) with an "AUTO-GENERATED: Read-only render"
  stamp. A new `workflow_family`/`routing_decision` column would flow to `goal.yaml` for free via
  this path — making the decision human-visible *and* agent-readable (FR-013) with no extra work.
- **Schema migration style:** `schema.sql` is hand-maintained truth; new columns added via
  `ALTER TABLE … ADD COLUMN` in a try/except `_run_migrations()` (Step-1 brief §A). Adding
  `workflow_family TEXT` / `routing_decision TEXT(JSON)` is a one-line, low-risk migration.
- **Single dispatch door + delegation context:** every agent-to-agent call goes through
  `POST /trigger` with a `DelegationContext`. The router participates as a normal agent — *no special
  transport*. `extra="allow"` on `DelegationContextData` lets a family/handle ride along immediately.
- **`allowed_delegations` in agent config** is the declared call-graph — use it to express
  "refinement → router" and "router → family-pipeline" edges.
- **Idempotent seeding guard** (`_create_starter_tasks` skips if tasks exist) is the pattern a
  router must respect: routing/seeding must be safe to re-run (US6 Scenario 3 re-invocation).

---

## 5. Entry Points & Flow

### Flow A — How a goal gets its (generic) "downstream workflow" today

```
update_status(slug, "accepted")        (goal_service.py:104)
  └─ _create_starter_tasks(slug)        (goal_service.py:301, called :144)
       └─ read config.STARTER_TASKS      (config.py:77)  ← SAME list for every goal
       └─ create_tasks_batch(...)        → tasks rows {phase, recommended_agent}
UI: GET /api/agents/goals/{slug}/recommendations  (api_agents.py:76)
  └─ get_recommended_agents(slug)        (agent_service.py:1649)
       └─ DISTINCT recommended_agent FROM tasks → agent_panel.html
human/agent clicks "run" → POST /api/agents/{name}/trigger  (api_agents.py:88)
```
**No classification anywhere in this chain. The "route" is a static seed.**

### Flow B — The FR-013 "same door" (how a parent agent dispatches a child today)

```
parent agent → POST /api/agents/{name}/trigger
                 body: { goal_slug, parent_run_id, delegation_context:{...} }   (api_agents.py:99)
  └─ DelegationContext validated (api_agents.py:109)  [extra="allow" → custom fields pass]
  └─ agent_service.trigger_agent(...)  (api_agents.py:132)
       └─ precondition: external_project_dir set (else 422)  (api_agents.py:142)
       └─ agent_runs row (parent_run_id threads the tree)
```
A `cast-workflow-router` agent (or a `/api/route` service endpoint) slots into this flow unchanged —
that is the structural argument for **extraction over in-agent embedding**.

### Flow C — Named pipeline behind a handle (the FR-015 stub precedent)

```
cast-orchestrate → orchestration_service.parse_manifest(_manifest.md)  (:51)
  └─ Phase(id, name, file, depends_on, status, notes)
  └─ build_execution_groups(...) → topo-sorted groups  (:163)
  └─ dispatch each phase via POST /trigger
```
A family **handle** = a named manifest/step-list; a **stub** = that list with steps named but not
yet wired (no resolved `recommended_agent`/`file`). Resolving an unimplemented family returns the
stub's enumerated steps — *not* `STARTER_TASKS` (which would be the forbidden silent generic fallback).

---

## 6. Tests & Coverage

- **Greenfield ⇒ no router tests** (the feature doesn't exist). Net-new code with net-new tests, not
  a retrofit.
- **`orchestration_service` is the testability model:** because it's pure logic, its parse/sort
  functions are trivially unit-tested with fixture manifests — the deterministic router resolver
  should be written the same way (pure `classify_result → handle/steps` function, table-driven
  tests over the family enum, including the "unimplemented family → named stub" branch and the
  "no silent generic fallback" assertion).
- **`db_path=` injection is pervasive** (`goal_service.py`, `task_service.py`, agent_service) — a
  routing-decision writer must accept `db_path` for test isolation, matching house style.
- **SC-005 validation harness shape:** "trace routing on 5 goals (one per family) + one cross-phase
  re-invocation." Concretely this is: seed 5 goals with 5 classifications → call the resolver →
  assert each returns the right handle (or named stub) and persists it on the goal → flip the goal's
  `phase` → call the resolver again → assert *same handle, no re-classification*. All achievable with
  the in-process service + `db_path` injection; no agent/tmux needed for the deterministic half.
- **Existing dispatch tests** live under `cast-server/tests/` (integration/e2e/ui) and exercise the
  trigger door + delegation contract (`docs/specs/cast-delegation-contract.collab.md` referenced at
  `api_agents.py:120`). A router-as-agent reuses that harness.

---

## 7. Config & Dependencies

- **`config.py` is where the taxonomy + pipeline registry would naturally live** (it already holds
  `PHASES`, `STARTER_TASKS`, `STATUS_TRANSITIONS`). A `WORKFLOW_FAMILIES` enum + per-family
  step-list/handle registry is the minimal config surface; this keeps families declarative and
  OSS-overridable (FR-012) rather than buried in code.
- **No new runtime dependency required.** Router = config + a pure service + (optionally) one agent +
  one schema column + one route. Everything rides existing FastAPI/sqlite3/Pydantic/delegation infra.
- **Agent registry + `allowed_delegations`** (`models/agent_config.py`) is the dependency-declaration
  surface for the call graph (refinement→router→pipeline).
- **Delegation contract** (`models/delegation.py`, `docs/specs/cast-delegation-contract.collab.md`)
  is the wire format; `extra="allow"` means family/handle fields need no immediate schema bump to
  flow through delegation.
- **The immovable constraint (FR-007, restated for routing):** whatever records the decision, the
  `refined_requirements.collab.md` spec-kit contract is untouched — routing is *additive metadata on
  the goal*, not a change to the requirements artifact. The classification that drives routing is the
  *same* classification that shapes the document (Step 3), but the two effects are recorded/consumed
  separately (US2 vs US6).

---

## Seam options, grounded in what exists

### The two-part decomposition the code implies

The router is **not one thing** — the codebase cleanly splits it:

1. **Classify** (LLM judgment: raw writeup / goal state → family + confidence). Needs a *model* call
   ⇒ belongs to an **agent step** (either a step inside `cast-refine-requirements`, or its own
   `cast-classify` agent). Confirm-on-ambiguity (FR-004) is inherently interactive/agentic.
2. **Resolve + record** (deterministic: family → downstream-workflow handle / named stub; persist on
   goal). No model needed ⇒ belongs to a **pure service** mirroring `orchestration_service`,
   callable from any phase/agent/route.

This split is the key insight: **the part that must be phase-agnostic and agent-callable (FR-016,
FR-013) is the deterministic resolver, and it does not need an LLM at all** — so it can be a plain
service endpoint that *anything* (a human via UI, the requirements agent, a future planning agent)
calls to ask "what workflow does this goal belong in?" without re-running refinement.

### Option A — Extracted standalone router (recommended direction; resolves the open question toward extraction)

- **Resolver = a pure service** (`workflow_router_service.py`) shaped like `orchestration_service`:
  `resolve(family) → {handle, steps[], implemented: bool}` + `record_routing_decision(slug, family,
  handle)` writing a new goal column (rendered into `goal.yaml`). Exposed at e.g.
  `POST /api/goals/{slug}/route` and importable in-process.
- **Classification** stays an agent step (in refinement for v2's single caller) but **writes the
  family to the goal**, so the resolver never needs to re-classify (FR-016 satisfied: any later phase
  reads the recorded family and re-resolves the handle deterministically).
- **FR-013 parity:** the resolve endpoint and the record-decision write are plain HTTP/service calls;
  a future agent calls them identically to a human. If a *router agent* is also wanted, it dispatches
  via the same `POST /trigger` door.
- **Reuses:** single dispatch door, pure-service pattern, DB→goal.yaml render, `config.py` registry,
  `allowed_delegations`. **Costs:** one schema column, one service, one route, a `config.py` family
  registry, and a classification step that persists its result.
- **Why this fits the spec:** phase-agnostic invocation (FR-016) *requires* the resolver be callable
  outside refinement; a pure service is the lowest-coupling way to get that, and extraction is the
  only option that doesn't force re-running refinement from another phase.

### Option B — Router lives inside `cast-refine-requirements`

- **Reuses:** nothing new — classification + routing are just more steps in the existing agent.
- **Fatal cost vs FR-016:** the router is then only reachable by invoking the *entire* refinement
  agent. "Resolve routing from another phase without re-refinement" is impossible without copy-pasting
  the logic — the exact re-litigation FR-015's "stable seam" exists to prevent. Also weak on FR-013
  (an agent wanting *only* the route must run a human-interactive refinement agent).
- **Verdict:** acceptable *only* for the classification step (which is genuinely agentic); the
  *resolve+record* half should still be extracted so it's callable standalone. I.e. even "inside"
  collapses toward Option A for the deterministic half.

### Recording the decision (FR-014) — what the code implies

- **New `goals` column** (`workflow_family TEXT`, optionally `routing_decision TEXT` JSON holding
  `{family, handle, implemented, decided_at, source_phase}`) added via the `ALTER TABLE` migration
  pattern. Flows to `goal.yaml` automatically through `_update_goal_yaml_fields` — human- and
  agent-readable, consistent with house style. **Recommended.**
- **Reuse `tags` JSON** (`family:bug`): zero schema change but unstructured, collides with real tags,
  and can't carry the handle/provenance. **Not recommended** beyond a throwaway prototype.
- **Add to `GoalUpdate`** (`models/goal.py:30`) so the resolver writes through the existing goal
  update path rather than a bespoke writer.

### Named stubs (FR-015) — what the code implies

- Represent each family's pipeline as a **named handle → enumerated step list** in `config.py`
  (shape: `STARTER_TASKS`-like dicts, or `Phase`-like rows). A stub = steps named, `implemented:
  False`, no resolved agent.
- Resolver returns the stub's steps for unimplemented families; **never** falls back to
  `STARTER_TASKS`. The presence of `implemented: False` is the explicit guard against the silent
  generic fallback (gap #3) — make the resolver *raise/return-stub* rather than default.
- A real pipeline lands later by flipping `implemented: True` and wiring steps to agents (eventually a
  `cast-orchestrate` manifest) — **no change to the seam**, which is the whole point of FR-015.

---

## Key Takeaways (opinionated, cross-cutting)

1. **The router is 100% greenfield — but every primitive it needs already ships and is proven.**
   Single dispatch door (`api_agents.py:88`), pure-logic-service pattern (`orchestration_service.py`),
   per-family step-list shape (`STARTER_TASKS`), DB→goal.yaml recording (`goal_service.py:366`),
   first-class configurable agents (`agent_config.py`). The synthesizer should frame the build as
   *assembly of existing patterns*, not invention.

2. **The current "router" is the anti-pattern the spec is killing.** `_create_starter_tasks` seeds
   ONE family-blind pipeline for every goal — literally FR-015's "silent generic fallback." Step 6
   replaces a static seed with a classification-driven, family-specific resolution that names a stub
   when no real pipeline exists.

3. **Extraction wins the seam debate, and the code makes the argument for you.** FR-016
   (phase-agnostic, no re-refinement) is *only* satisfiable if the resolve+record half is callable
   outside the refinement agent. The cleanest realization is the `orchestration_service` shape: a pure
   resolver service callable by UI, by the requirements agent, and by any future phase agent through
   the one dispatch door. Keep *classification* agentic; extract *resolution*.

4. **Split the router into classify (LLM/agent) + resolve (pure/deterministic).** This is the most
   important structural recommendation: the phase-agnostic, agent-callable requirement lands entirely
   on the deterministic half, which needs no model — so it's a trivially-testable service, and
   re-resolution from another phase is just "read recorded family → look up handle," never a
   re-classification.

5. **FR-013 agent-parity is nearly free here.** There is *already* exactly one door
   (`POST /trigger`) used identically by humans and delegating agents, and `DelegationContextData`
   already allows extra fields. A router exposed as a service endpoint and/or an agent is callable by
   a future agent with no new transport — the parity the spec wants later is structurally present now.

6. **Recording the decision is a one-column migration that auto-renders to `goal.yaml`.** Add
   `workflow_family` (+ optional `routing_decision` JSON) to `goals`, thread through `GoalUpdate`, and
   the existing DB-canonical→file-render convention surfaces it to both humans and agents at zero
   extra cost. Avoid stuffing it in `tags`.

7. **"Phase-agnostic" is cheap because phases are inert.** `phase` is a single freely-set TEXT column
   with no behavioral state machine; nothing gates capability by phase. So FR-016 reduces to "key the
   router off the recorded *classification*, never off `phase`" — there is no phase-coupling to
   dismantle.

8. **The real pipeline future already has a home: `cast-orchestrate` + manifests.** When a family
   pipeline graduates from stub to real, it becomes an orchestration manifest dispatched through the
   trigger door. Designing the stub's step-list in the `Phase`/`STARTER_TASKS` shape now means the
   later upgrade is data-wiring, not a seam change (FR-015 delivered).

---

## Key Files (read these to ground Step 6)

- `cast-server/cast_server/config.py:52,77-97` — `PHASES` (closed phase set) + `STARTER_TASKS` (the
  hardcoded family-blind pipeline = de-facto router); natural home for a `WORKFLOW_FAMILIES` registry.
- `cast-server/cast_server/services/goal_service.py:301` — `_create_starter_tasks`: the generic seed
  Step 6 replaces; `:151` `update_phase` (phase model); `:229` `update_config`/`:366`
  `_update_goal_yaml_fields` (where a recorded decision would render to `goal.yaml`).
- `cast-server/cast_server/db/schema.sql:1-14` — `goals` table; shows **no** classification/routing
  column (FR-014 is net-new schema).
- `cast-server/cast_server/models/goal.py:7-37` — `Goal`/`GoalUpdate`; the place to add
  `workflow_family`/`routing_decision`.
- `cast-server/cast_server/routes/api_agents.py:88` — `POST /api/agents/{name}/trigger`: **the single
  dispatch door** (FR-013 parity surface) shared by UI + delegating agents.
- `cast-server/cast_server/models/delegation.py` — `DelegationContext`; `extra="allow"` +
  `goal_phase` already present (custom routing fields can ride along now).
- `cast-server/cast_server/models/agent_config.py:16-31` — agents as first-class units
  (`allowed_delegations`, `dispatch_mode`, `trust_level`) — the call-graph + access primitives.
- `cast-server/cast_server/services/orchestration_service.py:51,163` — pure DAG/manifest logic with
  no Claude deps: **the shape the deterministic resolver should copy**, and the "named pipeline behind
  a handle" precedent for FR-015 stubs.
- `cast-server/cast_server/services/agent_service.py:1649` — `get_recommended_agents`: today's
  task-derived "what to run next" surface (the route's current UI projection).
- `agents/cast-refine-requirements/cast-refine-requirements.md` — the requirements agent that
  **does not classify today**; v2's single router-caller (where the classification *step* lands).
- `agents/cast-orchestrate/`, `agents/cast-create-execution-plan/`, `agents/cast-subphase-runner/` —
  the existing "run a named pipeline / DAG" agents; the future home of *real* family pipelines once
  stubs graduate.
- `docs/specs/cast-delegation-contract.collab.md` (ref'd `api_agents.py:120`) — the delegation wire
  contract a router-as-agent must honor.

---

## Open-Question Coverage from Step 6

| Open question | Step-6 code-exploration contribution |
|---|---|
| **Router placement** — inside `cast-refine-requirements` vs extracted standalone agent/service | Code strongly favors **extraction of the deterministic resolve+record half** (pure service à la `orchestration_service`), with classification kept agentic. FR-016 is only satisfiable extracted; FR-013 parity is free via the single dispatch door. (Final call = synthesizer + owner.) |
| Recording the routing decision (FR-014) | **New `goals` column** (`workflow_family` + optional `routing_decision` JSON) via the `ALTER TABLE` pattern, threaded through `GoalUpdate`, auto-rendered to `goal.yaml`. Avoid `tags`. |
| Named stubs / no silent generic fallback (FR-015) | Represent families as named handle→step-list registry in `config.py`; stub = `implemented:False`; resolver returns the stub (never `STARTER_TASKS`). The current `_create_starter_tasks` *is* the forbidden silent fallback to remove. |
| Phase-agnostic invocation (FR-016) | Cheap: `phase` is an inert TEXT column with no behavioral coupling; router keys off recorded classification, not phase. Persist classification once so re-resolution never re-classifies. |
| Agent-as-caller parity (FR-013) | Structurally present today: one dispatch door (`POST /trigger`) used identically by humans + delegating agents; `DelegationContextData(extra="allow")` lets family/handle ride along now. |
