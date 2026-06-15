# Phase-Agnostic Workflow Router — Playbook

> **Step 6 of Refine Requirements v2.** Synthesized from `06-phase-agnostic-router.ai.md` (7-angle web research) + `06-phase-agnostic-router-code.ai.md` (codebase terrain) + `steps.ai.md` + `refined_requirements.collab.md`. GO-BROAD strategy: recommendation is unconstrained by current code; migration cost is noted, not obeyed.

## TL;DR

**Extract the router — but only its deterministic half.** Split Step 6 into two parts the codebase already implies: *classify* (LLM judgment, stays an agent step) and *resolve+record* (a pure, side-effect-light function `(family) → WorkflowHandle`). Ship the resolver as a new `workflow_router_service.py` modeled byte-for-byte on the existing pure-logic `orchestration_service.py`, fronted by one HTTP route and backed by **two new typed columns on `goals`**. The non-obvious key insight: **phase-agnosticism (FR-016) is not a feature you build — it is a property you fail to destroy.** If the resolver is a pure function of a *persisted* family and never re-classifies, then any caller in any phase that can read the goal gets the right answer for free. The entire router is ~5 lines of logic over a total registry dict; everything else is reuse of primitives Diecast already ships. The seam is justified *because FR-016 is real* — confirm that with the owner at plan review, because it is the single load-bearing premise.

## Recommended Stack

| Component | Choice | Why |
|-----------|--------|-----|
| **Seam placement** | **Extract `resolve+record` as a pure service; keep `classify` as an agent step inside `cast-refine-requirements` (v2's only caller)** | FR-016 (many future callers) is *only* satisfiable extracted; classification is genuinely agentic so it stays in the agent. Burying resolve inside the agent violates FR-016 by construction (`06-...-router-code.ai.md` §Option B). |
| **Resolver shape** | **Pure Python service `workflow_router_service.py`, modeled on `orchestration_service.py`** | Existing house precedent: "pure DAG logic… No subprocess/Claude/tmux dependencies" (`orchestration_service.py:1-4`). Importable in-process, CLI-runnable, table-driven testable, zero LLM. |
| **Routing pattern** | **Content-Based Router + Strategy/Registry — a *total* `{family: WorkflowHandle}` dict** | Canonical named prior art (Hohpe EIP); registry pattern is the community-blessed cure for `if/elif` dispatch. Total map = structural guarantee against silent fallback (FR-015). |
| **Registry location** | **`config.py`, beside `STARTER_TASKS` / `PHASES` / `STATUS_TRANSITIONS`** | Already the home of declarative routing data; code-reviewed, diffable, OSS-overridable (FR-012). DB-table registry is the *deferred* upgrade, not v2. |
| **Decision recording** | **Two typed columns on `goals`: `workflow_family TEXT`, `routing_handle TEXT` (+ `routed_at`)** | Mirrors how `phase` already lives on `goals`; auto-renders to `goal.yaml` via `_update_goal_yaml_fields` (`goal_service.py:366`) — human- *and* agent-readable for free. NOT `tags` (flat, unstructured, collides). |
| **Stub representation** | **Special Case object: `WorkflowHandle(status="stub", steps=[...])`, never a Null Object** | A Null Object silently absorbs the missing case (= the forbidden silent fallback). A Special Case *announces* "not built, here are the steps" (FR-015, US6 Scenario 2). |
| **Agent-as-caller parity** | **Reuse the single dispatch door `POST /api/agents/{name}/trigger` + `allowed_delegations`** | FR-013 parity is structurally present today: one door used identically by humans and delegating agents; `DelegationContextData(extra="allow")` lets `workflow_family` ride along now. No new transport. |
| **Router wrapper** | **Ship a thin `/api/goals/{slug}/route` HTTP route + (optional, recommended) `/cast-router` skill/agent** | Near-zero cost, completes the FR-013 surface: human button, in-process agent call, and future-phase HTTP trigger all hit the same resolver. |

Opinionated picks only. No rules engine, no workflow DSL, no plugin-loader — those are the EIP "configurable rules engine" *later* state, gated by the rule of three.

## Implementation Steps

Ordered by dependency, not impact.

### Step 1: Add the family registry to `config.py`
**Impact: High** | **Effort: ~1 hour**

The registry IS the router. Define a closed family enum and a *total* map from every family to a `WorkflowHandle`. Place it beside `STARTER_TASKS` so it reads as "the family-keyed generalization of the phase-keyed table we already have."

```python
# config.py — beside STARTER_TASKS / PHASES

WORKFLOW_FAMILIES = [
    "new-initiative", "pilot-poc", "bug-fix", "data-analysis", "exploration",
]  # closed set; long-tail families (add-tests, heavy-ui, prd-only) flagged out of v2 scope

# Each family → its named downstream pipeline, steps enumerated, status flagged.
WORKFLOW_REGISTRY = {
    "new-initiative": {"status": "stub", "steps": ["PRD", "architecture", "plan"]},
    "pilot-poc":      {"status": "stub", "steps": ["one-screen-WHAT", "spike", "demo"]},
    "bug-fix":        {"status": "stub", "steps": ["logs", "RCA", "confirm", "fix/test"]},
    "data-analysis":  {"status": "stub", "steps": ["question", "sources", "analysis", "writeup"]},
    "exploration":    {"status": "stub", "steps": ["frame", "probe", "synthesize"]},
}
```

Every family present, every value `status="stub"` for v2. Flipping one to `"implemented"` (and wiring `steps` to agents) is how a real pipeline lands later — *no seam change* (FR-015).

### Step 2: Build the pure resolver `workflow_router_service.py`
**Impact: High** | **Effort: ~2-3 hours incl. tests**

Mirror `orchestration_service.py`: pure logic, no Claude/subprocess deps, `db_path=` injectable, `if __name__ == "__main__"` CLI hook. The resolver is **total** — defined for every input including `None` and unknown families — so there is no undefined case for a caller to silently default on.

```python
"""Workflow router — pure resolution logic. No subprocess/Claude/tmux deps."""
from dataclasses import dataclass, field
from . import config

@dataclass
class WorkflowHandle:
    family: str | None
    status: str               # "implemented" | "stub" | "unmatched" | "needs-classification"
    steps: list[str] = field(default_factory=list)
    pipeline_ref: str | None = None
    message: str = ""

def resolve(family: str | None) -> WorkflowHandle:
    if family is None:
        return WorkflowHandle(None, "needs-classification",
                              message="Goal not yet classified — refine first; never guessing.")
    entry = config.WORKFLOW_REGISTRY.get(family)
    if entry is None:                                    # unknown family → announces itself
        return WorkflowHandle(family, "unmatched",
                              message=f"No pipeline registered for '{family}'.")
    return WorkflowHandle(family, entry["status"], steps=entry["steps"],
                          message=f"{family} pipeline ({entry['status']}).")
```

Five lines of branching. Table-driven tests assert one handle per family + the three edge handles. **The resolver never calls an LLM and never re-classifies** — it is a pure consumer of the persisted family.

### Step 3: Add the recording columns + thread through `GoalUpdate`
**Impact: High** | **Effort: ~1-2 hours**

This is the one real schema gap — `goals` has nowhere to record the decision (FR-014). Add two typed columns via the established `ALTER TABLE … ADD COLUMN` migration pattern in `_run_migrations()`.

```sql
-- schema.sql, mirroring how `phase` lives on goals
ALTER TABLE goals ADD COLUMN workflow_family TEXT;     -- the recorded classification
ALTER TABLE goals ADD COLUMN routing_handle  TEXT;     -- the resolved handle name
ALTER TABLE goals ADD COLUMN routed_at        TEXT;     -- ISO timestamp of the decision
```

Add the three fields to the `Goal` Pydantic model and expose `workflow_family`/`routing_handle` on `GoalUpdate` (`models/goal.py:30`) so the recorder writes through the existing goal-update path. The columns auto-render into `goal.yaml` via `_update_goal_yaml_fields` (`goal_service.py:366`) — making the decision human-visible *and* agent-readable at zero extra cost.

> **Defer:** a `goal_routing` *history* table (re-classification audit trail). Add it only if US6 Scenario 4 needs prior-decision history rather than just "current vs previous." Two columns is the v2 recommendation.

### Step 4: Write `record_routing_decision(slug, family, handle)`
**Impact: Medium** | **Effort: ~1 hour**

A thin service function that calls `resolve(family)`, then persists `workflow_family`, `routing_handle`, `routed_at` through the goal-update path. Idempotent and re-runnable (US6 Scenario 3) — re-recording the same family yields the same row. This is the *only* part of the router that writes; keep it separate from the pure `resolve` so the resolver stays side-effect-free and trivially testable.

### Step 5: Expose the resolver at one HTTP route
**Impact: Medium** | **Effort: ~1 hour**

`POST /api/goals/{slug}/route` reads the goal's recorded `workflow_family`, calls `resolve`, optionally records, returns the handle as JSON. This is the phase-agnostic surface: a future planning agent six weeks later hits this route, the resolver reads the *persisted* family, and returns the *same* handle — no refinement replay (FR-016, SC-005).

```python
# routes/api_goals.py
@router.post("/api/goals/{slug}/route")
def route_goal(slug: str):
    goal = goal_service.get_goal(slug)
    handle = workflow_router_service.resolve(goal.workflow_family)
    workflow_router_service.record_routing_decision(slug, goal.workflow_family, handle)
    return handle
```

### Step 6: Wire the classify step into `cast-refine-requirements`
**Impact: High** | **Effort: ~2-3 hours (agent prompt + persistence call)**

The refinement agent gains a classification step (this is Step 3's classifier; Step 6 only *consumes* its output). On classifying, the agent writes `workflow_family` to the goal via `GoalUpdate`, then calls `record_routing_decision`. Confirm-on-ambiguity (FR-004) stays in the agent — the resolver never sees ambiguity, only a confirmed label. **The agent is the only v2 caller; do not wire non-requirements phases (out of scope).**

### Step 7: Surface the route in the UI + (optional) ship `/cast-router`
**Impact: Low/Medium** | **Effort: ~2 hours**

Generalize the existing `recommended_agent` badge pattern (`task_item.html:40,73-81`) into a goal-level "Routed workflow: bug-fix (stub) — steps: logs → RCA → confirm → fix/test" panel that renders `WorkflowHandle.status` and `steps`. Optionally register a `/cast-router` skill + agent (dispatched via the existing trigger door, gated by `allowed_delegations`) so a human button and future-phase agents share the door — completing the FR-013 surface at near-zero cost.

## Architecture

```
                 ┌─────────────────────────────────────────────────────────┐
                 │  CALLERS (FR-013 parity — one door)                       │
                 │   • human: goal-page "Route" button                       │
                 │   • cast-refine-requirements (in-process or HTTP)         │
                 │   • future cast-high-level-planner (HTTP, allowed_deleg.) │
                 └───────────────┬─────────────────────────────────────────┘
                                 │  POST /api/goals/{slug}/route
                                 ▼
        ┌────────────────────────────────────────────────────────────────┐
        │  workflow_router_service.py   (PURE — no LLM, no subprocess)     │
        │                                                                  │
        │   resolve(family) ──────────────► WorkflowHandle                 │
        │      │   reads config.WORKFLOW_REGISTRY  (total map)             │
        │      │   None → needs-classification (never guess)               │
        │      │   miss → unmatched (announces itself)                     │
        │      │   hit  → {status: stub|implemented, steps:[...]}          │
        │      ▼                                                            │
        │   record_routing_decision(slug, family, handle)  ── writes ──┐   │
        └──────────────────────────────────────────────────────────────│──┘
                                 ▲ reads persisted family               │ writes
   classification (LLM)          │                                      ▼
   lives in cast-refine-    ┌────┴───────────────────────────────────────────┐
   requirements; writes     │  goals table  (+ workflow_family, routing_handle,│
   workflow_family ────────►│                 routed_at)                       │
   to the goal              │     └─ auto-renders → goal.yaml (read-only stamp) │
                            └──────────────────────────────────────────────────┘

   Late binding: classification happens once (authoring time); the route is
   re-resolved deterministically from persisted state at ANY later decision time.
```

## Key Decisions

| Decision | Recommendation | Rationale |
|----------|---------------|-----------|
| Inside-agent vs extracted | **Extract the resolve+record half; keep classify in the agent** | FR-016 demands many callers → supervisor/extracted shape. Inside-agent placement is reachable only by re-running refinement (FR-016 violation). Classify is genuinely agentic. |
| Router = agent or service? | **Service (pure) + thin wrappers (route, optional skill)** | The phase-agnostic, agent-callable requirement lands entirely on the *deterministic* half, which needs no model. Wrappers give human+agent parity cheaply. |
| Registry: `config.py` vs DB table | **`config.py` for v2** | Simplest, code-reviewed, OSS-overridable, mirrors `STARTER_TASKS`. DB/rules-engine is the EIP "configurable rules engine" deferred upgrade (rule of three). |
| Recording: columns vs `goal_routing` table vs `tags` | **Two typed columns on `goals` (+ `routed_at`)** | Mirrors `phase`; queryable; auto-renders to `goal.yaml`. History table only if Scenario 4 needs an audit trail. `tags` is unstructured and collides — rejected. |
| Handle identity: agent-name vs abstract ref | **Abstract `routing_handle` string for v2; resolves to agent/orchestration later** | Stubs have no agent yet. Keep it abstract so a multi-agent pipeline can land without reshaping the handle. (Agent-name reuse is fine if a stub graduates to a single agent.) |
| Stub: Null Object vs Special Case | **Special Case** (`status="stub"`, `steps=[...]`, `message`) | Null Object silently no-ops = the forbidden silent fallback. Special Case announces itself = FR-015 as a structural property, not a runtime check. |
| Function totality | **Total — defined for every family + `None` + unknown** | A partial function forces callers to handle "undefined," and the cheapest handler is a silent default (FR-015 violation). Totality means there is nothing to fall back *to*. |
| Absent family behavior | **Return `needs-classification`, never re-classify** | Re-deriving family replays refinement (FR-016 violation) or diverges from the user's confirmed label (SC-005 violation). Read state; never recompute. |

## Pitfalls to Avoid

1. **The router silently re-classifies.** The subtlest failure: a future agentic router re-runs classification with a different prompt and produces a *different* family than the user confirmed — destroying both "no re-refinement" (FR-016) and consistency (SC-005). **Guard:** the resolver is a pure consumer of the persisted family; absent family → `needs-classification` handle, never a guess.

2. **Gold-plating into a "configurable rules engine."** Every routing source (EIP, registry pattern, YAGNI) warns the router grows into a hub that becomes a rules engine for five families, four of which are stubs — overhead with no payoff. **Guard:** keep it a flat dict + ~5 lines until the rule of three fires.

3. **The stub path is untested ("flag-off" neglect).** Feature-flag practitioners' most-cited failure: teams test only the on-path; the off-path is broken when it's finally hit. A stub is the "flag-off" path. **Guard:** a test asserting "bug-fix family → stub handle with named steps `logs→RCA→confirm→fix/test`" is first-class, not an afterthought.

4. **Recording the decision in `tags`.** Tempting (zero schema change), but `tags` is a flat list — it can't carry the handle, status, or provenance, and it collides with real tags. **Guard:** typed columns mirroring `phase`. The migration is one `ALTER TABLE` line.

5. **Falling back to `STARTER_TASKS`.** The current `_create_starter_tasks` seeds ONE family-blind pipeline for every goal — *that is literally the silent generic fallback FR-015 abolishes*. An unimplemented family must return its named stub, **never** the generic seed. **Guard:** the resolver has no reference to `STARTER_TASKS`; unknown → `unmatched`, not generic.

6. **Building the phase-agnostic *wiring* into other phases.** The spec scopes this out — only requirements invokes the router in v2. Building the *callable surface* (route + skill) costs ~nothing; building the *callers* in planning/execution is out-of-scope speculative work. **Guard:** ship the door, not the future callers.

7. **Extracting before confirming FR-016 is real.** The entire extraction rests on FR-016 being a genuine, owner-confirmed requirement. If routing is forever single-caller, inline placement is correct and the seam is pure YAGNI. **Guard:** flag FR-016 for explicit owner confirmation at plan review (see Success Metrics).

8. **Coupling the router to `phase`.** "Phase-agnostic" tempts a `phase`-keyed lookup. But `phase` is an inert freely-set TEXT column with no behavioral state machine. **Guard:** key the router off the recorded *classification*, never off `phase` — there is no phase-coupling to dismantle, so don't introduce one.

## Success Metrics

- **Routing correctness (SC-005):** seed 5 goals (one per family) → call `resolve` → assert each returns the correct handle (or named stub) and persists `workflow_family`/`routing_handle` on the goal. **Target: 5/5 correct.**
- **Phase-agnostic stability (SC-005):** flip a goal's `phase`, call `resolve` again → assert the *same* handle returns with *no* re-classification. **Target: byte-identical handle across phases.**
- **Stub discipline (FR-015):** for every family with `status="stub"`, assert the returned handle carries named `steps` and a `status` field — and that no unimplemented family ever resolves to `STARTER_TASKS` or a generic bucket. **Target: 0 silent fallbacks; 100% of stubs name their steps.**
- **Totality (first-principles):** assert `resolve` returns a real `WorkflowHandle` for every family + `None` + an unknown string. **Target: 0 `None`/exception returns; 3/3 edge handles correct.**
- **Recording round-trips to `goal.yaml`:** after `record_routing_decision`, assert `workflow_family`/`routing_handle` appear in both the DB row and the rendered `goal.yaml`. **Target: present in both.**
- **Agent-parity (FR-013):** assert a human (UI button), the requirements agent (in-process), and a simulated future agent (HTTP `POST /trigger` or `/route`) all reach the resolver through the existing door with no new transport. **Target: 3 callers, 1 door, 0 new mechanisms.**
- **Seam stability under graduation (FR-015):** flip one family `stub → implemented` in the registry and assert no caller signature or schema changes. **Target: registry-only diff.**

## Impact Rating: 8/10

**Justification:** Step 6 is the most architecturally future-loaded of the three threads — it sets the seam every later per-family pipeline drops into, so getting it right is leverage and getting it wrong re-litigates the boundary forever. The rating is 8 not 10 because v2 ships only stubs (the user-visible payoff is deferred to later pipeline goals) and the whole extraction rests on FR-016 being a genuinely-wanted requirement — a premise that must be owner-confirmed at plan review before the seam earns its 8. The de-risking is unusually strong: every primitive (pure-logic service, total registry, DB→goal.yaml render, single dispatch door) already ships and is proven, so this is assembly of known patterns, not invention — which is exactly why the seam is "nearly free *and* removes a worse alternative" rather than speculative generality.
