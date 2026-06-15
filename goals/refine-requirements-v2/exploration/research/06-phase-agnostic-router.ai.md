# Research: Phase-Agnostic Workflow Router — Where the Seam Lives, How a Goal Routes from Any Phase

**Goal context:** Refine Requirements v2 — Workflow-Aware, HTML-First Requirements Refinement (Step 6 of the exploration). Design the **phase-agnostic workflow router**: given a goal's classification (family), resolve a family-specific downstream-workflow handle (bug → logs→RCA→confirm→fix/test; prototype → spike→demo→learnings), **record the routing decision on the goal** (FR-014), and make the router invokable from **any phase** without re-running refinement (FR-016). Decide the **seam**: does classify+route live *inside* `cast-refine-requirements` or get *extracted* as a standalone agent/service? v2 ships the **seam + named pipeline STUBS**, not real pipelines (FR-015). Unimplemented families route to a **named stub**, never a silent generic fallback. Agent-as-caller parity (FR-013).
**Date:** 2026-06-11
**Researcher:** cast-web-researcher (7-angle research, code-grounded)

> **Scope discipline — read this first.** Step 3 already validated the *taxonomy* and designed the *classifier* + per-family **document** shaping (see `03-workflow-classification-taxonomy.ai.md`). **This note does NOT re-litigate classification.** It takes the family label as an *input* and answers the *routing* half of US2's two-effects split: **same classification, second effect = route the goal into downstream work (US6), not shape the document (US2).** The hard problems here are *placement* (where the router lives), *recording* (how the decision persists on the goal), *phase-agnostic invocation* (resolve from any phase without re-refinement), and *stub discipline* (named stub, never silent fallback). Classification confidence/confirm-on-ambiguity is Step 3's; routing consumes whatever family Step 3 emits.

---

## TL;DR for the synthesizer

1. **EXTRACT the router. The seam decision is already over-determined — by FR-016, by the contrarian's own YAGNI test, and by an existing precedent in this very codebase.** Phase-agnostic invocation (FR-016) is logically incompatible with burying classify+route inside `cast-refine-requirements`: a router that only the refinement agent can call is, by definition, not phase-agnostic. The router is a **pure resolution function** — `(family[, phase]) → workflow_handle` — with no LLM call, no conversation, no I/O beyond a registry lookup and a write to the goal. That is the same shape as the *already-extracted* `orchestration_service.py` (pure DAG logic, "No subprocess/Claude/tmux dependencies", `orchestration_service.py:1-3`). Mirror it: a `routing_service.py` + a thin agent/skill wrapper.

2. **The codebase already runs a primitive, static version of this router — generalize it, don't invent it.** `STARTER_TASKS` in `config.py:77-96` is a hardcoded **phase → `recommended_agent`** table (`"plan" → "cast-high-level-planner"`, `"exploration" → "cast-explore"`, etc.); `tasks.recommended_agent` (`schema.sql:35`, `models/task.py:29`) persists the resolved handle per task; `agent_service.get_recommended_agents(slug)` (`api_agents.py:78-79`) reads it back. **Today's routing key is `phase`; the v2 router adds `family` as a second key.** The architecture — a static map from a goal/task attribute to a named agent handle, persisted on a row, rendered as a UI badge — is *exactly* what FR-014 asks for. The router is a *generalization* of an existing pattern, which is the strongest possible de-risking argument.

3. **The routing decision has nowhere to live on the goal today — this is the one real schema gap.** The `goals` table (`schema.sql:1-13`) is metadata-only: `slug, title, status, phase, origin, in_focus, tags, folder_path, gstack_dir, external_project_dir`. **No JSON/metadata column, no `workflow_family`, no `routing_decision`.** Recording FR-014 needs either (a) two typed columns `workflow_family TEXT, routing_handle TEXT` on `goals` (cleanest, queryable, mirrors how `phase` already lives there), or (b) a small `goal_routing` table if you want decision *history* (re-classification audit trail for US6 Scenario 4). Recommend (a) for v2 + a `routed_at` timestamp; promote to (b) only if reclassification history is needed. **Do not abuse `tags`** — it's a flat list, not a typed decision record.

4. **Stub discipline = fail loud, named, never silent. The canonical idiom is the registry miss that returns a *named "not-implemented" handle*, not `None` and not a generic default.** Every routing source converges here: a Content-Based Router must route to "the correct recipient" and a misroute is a defect, not a fallback ([Hohpe EIP](https://www.enterpriseintegrationpatterns.com/patterns/messaging/ContentBasedRouter.html)); strategy-registry implementations validate against a whitelist and the *absence* of a strategy is an explicit error, not a default branch ([Mark Torres — Registry Pattern](https://markptorres.com/ai_workflows/2025-12-02-registry-pattern); [GeeksforGeeks — Registry Pattern](https://www.geeksforgeeks.org/system-design/registry-pattern/)). For v2: the registry maps **every** family to a `WorkflowHandle` that is *always present* but whose `status ∈ {implemented, stub}`. A stub handle carries its **named steps** (bug: `logs→RCA→confirm→fix/test`) and a `status: "stub"` flag the UI/agent surfaces as "planned, not built yet." This satisfies US6 Scenario 2 (route to a stub that *names* the steps) and the FR-015 "never silent generic fallback" rule structurally — there is no generic bucket to fall into because the map is total.

5. **FR-013 agent-as-caller parity is nearly free once the router is a service.** A pure `(family) → handle` function exposed as (a) a Python service call, (b) an HTTP route (`POST /api/goals/{slug}/route` or a `cast-router` agent trigger via the existing `/api/agents/{name}/trigger`), and (c) a `/cast-router` skill is callable identically by a human (button in the goal UI), the requirements agent (in-process or HTTP), and any *future* phase agent (HTTP/skill). The existing `allowed_delegations` whitelist in agent `config.yaml` (`cast-explore/config.yaml:4-9`) is the exact mechanism by which a future planning/execution agent would be granted the right to call `cast-router`. **No new plumbing — the dispatch substrate already exists.**

6. **Contrarian, steelmanned and resolved by Fowler's own rule.** The sharpest objection (do NOT build a router seam now — YAGNI) is *correct about the pipelines and wrong about the seam*, and Fowler draws exactly this line: *"Yagni only applies to capabilities built into the software to support a presumptive feature, it does not apply to effort to make the software easier to modify"* ([Fowler, Yagni](https://martinfowler.com/bliki/Yagni.html)). The downstream **pipelines** are presumptive capabilities → YAGNI → **stub them** (which is precisely FR-015). The **seam** is malleability — "effort to make the software easier to modify" — which YAGNI explicitly *exempts*. The honest contrarian residue: keep the seam *minimal* (a dict + a persisted decision + a thin wrapper), resist building a "configurable rules engine" (the EIP over-engineering trap) until the rule of three fires.

---

## 1. Expert Practitioner Insights

**The dominant production pattern for "decide which downstream worker handles this" is the supervisor/router topology, and the 2026 consensus is that the routing decision is a first-class component separate from the workers.** The multi-agent-framework landscape converged on this: *"Supervisor is the 2026 production default, with Claude Code subagents, LangGraph Supervisor, and OpenAI Agents SDK handoffs all converging on the supervisor topology"* ([Multi-Agent Orchestration: 5 Patterns That Work in 2026](https://www.digitalapplied.com/blog/multi-agent-orchestration-5-patterns-that-work)). The deciding axis maps directly onto Step 6's seam question: *"whether you want the user to 'talk to' a specialist directly (handoff) or always talk to one orchestrator that delegates (supervisor)"* ([CallSphere — LangGraph Supervisor 2026](https://callsphere.ai/blog/langgraph-supervisor-multi-agent-orchestration-2026)). A phase-agnostic router that *any* phase consults is the **supervisor/orchestrator** shape, not the inline-handoff shape — the router retains the decision; the phases are the specialists it points at.

**Crucial nuance for the seam: there are two legitimate places to put routing, and the trade-off is exactly the inside-vs-extracted question.** LangChain's own handoff docs show both: routing can be *embedded in the agent's tools* (the agent decides when to hand off by calling a handoff tool) **or** centralized in a supervisor node ([LangChain — Handoffs](https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs)). Embedded handoff "decouples routing from a centralized decision-maker — the agent determines when to handoff." That is the *inside cast-refine-requirements* option. The supervisor option centralizes it. **The literature's tie-breaker is reuse-from-many-callers:** OpenAI's embedded-handoff style *"can become unwieldy with more than 8–10 agent types"* and is best "when you want one agent to fully take over," whereas the supervisor "works when you need an orchestrator that retains control" ([gurusup — Best Multi-Agent Frameworks 2026](https://gurusup.com/blog/best-multi-agent-frameworks-2026)). FR-016 demands *many* callers (every phase) → supervisor/extracted wins. Embedded routing is only superior when exactly one agent ever routes — which FR-016 explicitly forbids.

**Durable-workflow engines reinforce "resolve the route from persisted state, not from a live conversation."** Temporal's whole thesis is *durable execution — long-running workflows that survive crashes and pick up exactly where they left off* ([xgrid — Temporal vs Airflow vs Argo](https://www.xgrid.co/resources/temporal-vs-airflow-vs-argo-workflow-orchestration/)). The transferable principle for FR-016: the routing decision must be **reconstructable from durable goal state** (the persisted family/handle), so a planning-phase invocation six weeks later re-resolves the *same* handle without replaying the refinement conversation. This is the architectural meaning of "phase-agnostic without re-refinement" — routing reads state, it does not re-derive it.

**Synthesis for the feature design:**
- The router is an **orchestrator/supervisor**, not an inline handoff — because many phases must call it (FR-016).
- Routing must resolve **from persisted goal state**, not from the refinement conversation — that *is* phase-agnosticism.
- Keep the worker pipelines behind the seam as named handles; the router knows *handles*, not pipeline internals — the EIP "easy to maintain" mandate (§5).

**Sources**
- https://www.digitalapplied.com/blog/multi-agent-orchestration-5-patterns-that-work
- https://callsphere.ai/blog/langgraph-supervisor-multi-agent-orchestration-2026
- https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs
- https://gurusup.com/blog/best-multi-agent-frameworks-2026
- https://www.xgrid.co/resources/temporal-vs-airflow-vs-argo-workflow-orchestration/

---

## 2. Tool/Product Landscape

| System | Routing primitive | Where the route is decided | Recording / persistence | Stub / unmatched behavior |
|--------|-------------------|----------------------------|--------------------------|---------------------------|
| **LangGraph (supervisor)** | Conditional edges + a supervisor node returning a `Command` | **Centralized** in the supervisor node; workers are graph nodes | Routing state in the graph checkpoint (durable, time-travel) | Edge to a default/END node; you define the fallback node explicitly |
| **LangGraph/LangChain (handoff)** | Handoff *tool* returning `Command.PARENT` | **Embedded** in each agent's tools | Persistent state variable updated by the tool | Agent simply doesn't call a handoff tool |
| **OpenAI Agents SDK** | `handoffs=[...]` list on an agent | Embedded in the agent; "fully take over" | Ephemeral context vars | Unwieldy past ~8–10 agent types |
| **Temporal** | Workflow code dispatches activities/child workflows | In workflow code (durable) | Event-sourced history; survives crashes | Explicit error/compensation; no silent default |
| **Argo Workflows** | DAG/steps templates (K8s CRDs) | Declarative YAML, container-native | Workflow CRD status | `when:` conditions; unmatched step is skipped |
| **n8n** | Switch / IF nodes, visual | In the canvas, per-flow | Per-execution data | A "fallback" output branch you wire by hand |
| **Hohpe Content-Based Router (EIP)** | Examine message → pick channel | A dedicated **router component** between sender and recipients | Stateless; routes per-message | "route to the *correct* recipient" — misroute is a bug; invalid-message channel is explicit |
| **Diecast today (`STARTER_TASKS`)** | Static `phase → recommended_agent` dict | `config.py:77-96` (data, not code branches) | `tasks.recommended_agent` column; UI badge | `recommended_agent: None` → no badge, manual |

### Deep dives on the most relevant references

**Content-Based Router (Hohpe & Woolf, EIP) — the canonical name for exactly this component, and its two load-bearing warnings.** The pattern: *"Use a Content-Based Router to route each message to the correct recipient based on message content"* — routing on "existence of fields, specific field values etc." ([enterpriseintegrationpatterns.com](https://www.enterpriseintegrationpatterns.com/patterns/messaging/ContentBasedRouter.html)). Two warnings transfer directly: (1) **maintainability** — *"special caution should be taken to make the routing function easy to maintain as the router can become a point of frequent maintenance."* The router is a *hub*; every new family touches it, so keep the rule set declarative (a dict/registry), not buried in branching code. (2) **escalation path, not a license** — *"In more sophisticated integration scenarios, the Content-Based Router can take on the form of a configurable rules engine."* This is the future state if rules get complex — explicitly **not** what v2 needs (the contrarian's over-engineering trap). v2 is the simplest CBR: a total map from family to handle.

**LangGraph supervisor vs embedded handoff — the cleanest articulation of Step 6's seam fork.** Embedded handoff (routing in agent tools) "decouples routing from a centralized decision-maker"; the supervisor centralizes it and "retains control" ([LangChain handoffs](https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs); [CallSphere 2026](https://callsphere.ai/blog/langgraph-supervisor-multi-agent-orchestration-2026)). Diecast's `cast-orchestrate` / `cast-crud-orchestrator` are already supervisor-shaped (they dispatch a maker chain), so the house idiom for "one component dispatches many workers" exists. The router is a *degenerate supervisor*: it doesn't run the workflow, it just *names which workflow* — a resolver, not an executor (the executor is a later per-family goal).

**Diecast's own `STARTER_TASKS` — the precedent that makes this low-risk.** `config.py:77-96` is a static routing table keyed by phase; the resolved handle persists on `tasks.recommended_agent`; the UI renders it as an agent badge with a "Run now" affordance (`task_item.html:40,73-81`). The v2 router is this same machine with **`family` as an additional key** and **the goal (not a task) as the persistence target**. This is a generalization, not a new subsystem — the strongest de-risking signal in the whole step.

### Synthesis for the feature
- The router has a **canonical name and decades of prior art**: it is a Content-Based Router / supervisor resolver. Don't invent terminology; cite EIP.
- **Keep the rule set declarative** (a registry/dict), per the EIP maintainability warning — this also makes it data, testable, and agent-readable.
- **Diecast already ships a static phase-keyed router** — generalize it to family-keyed and move the persisted decision from the task to the goal.

### Sources
- https://www.enterpriseintegrationpatterns.com/patterns/messaging/ContentBasedRouter.html
- https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs
- https://callsphere.ai/blog/langgraph-supervisor-multi-agent-orchestration-2026
- https://reference.langchain.com/python/langgraph-supervisor
- https://www.xgrid.co/resources/temporal-vs-argo-workflows-architecture-comparison/
- https://kestra.io/resources/infrastructure/argo-workflows-alternatives

---

## 3. AI-Native Approaches

**The router should be deterministic code, not an LLM call — and that is the AI-native best practice, not a compromise.** The classification (Step 3) is the LLM-shaped problem (fuzzy text → family). The *routing* (family → handle) is a pure table lookup with a finite, known key space. The 2026 agent-routing literature is explicit that you separate the two: a "router" that maps an already-decided intent to a handler should be cheap and deterministic; semantic/LLM routing is for the *classification* upstream. Aurelio `semantic-router` embodies the split — it returns a `Route` *name* (or `None` to abstain), and the application maps that name to behavior; the routing-to-behavior step is plain code ([semantic-router GitHub](https://github.com/aurelio-labs/semantic-router), cited in Step 3). **Implication:** don't make the router an agent that "thinks." Make it a service. The only LLM in the loop is the Step 3 classifier whose output the router consumes.

**Persist the routing decision as machine-readable state so *agents* route on it, not just humans (FR-013 + FR-014 fused).** Step 3's research already recommends emitting `{family, confidence, reasoning}` as front-matter / a structured field. The router's job is to turn that into a persisted `routing_handle` on the goal. Spec-driven AI tooling does exactly this: AWS Kiro forces an upfront **mode** that becomes a routing key for downstream generation ([AWS Builder — Kiro](https://builder.aws.com/content/31u60Xzm1ymjMpCi5kTmFutCyiN/hands-on-project-using-kiro-spec-driven-development), cited in Step 3). For Diecast, the persisted `(workflow_family, routing_handle)` on the goal *is* the machine-readable routing key — a future planning agent reads the goal row, finds `routing_handle = "bug-fix-pipeline"`, and dispatches accordingly without re-running anything. This is the concrete meaning of "agents are first-class consumers of the routing decision."

**Agent-as-caller parity is a solved shape in this codebase: the same trigger door for human and agent.** Diecast's dispatch substrate already gives three equivalent entry points to any agent: the HTTP `POST /api/agents/{name}/trigger`, the parent→child delegation JSON (`.delegation-*.json` + `.prompt`, the exact mechanism *this* run uses), and the `/cast-*` skill. A `cast-router` agent (or a `routing_service` fronted by `POST /api/goals/{slug}/route`) is callable identically by: a human clicking a goal-page button, `cast-refine-requirements` (in-process service call or HTTP), and a *future* `cast-high-level-planner` (HTTP trigger gated by `allowed_delegations`). The FR-013 "same mechanism as humans" requirement is satisfied by *not inventing a new mechanism* — reuse the trigger/delegation rail.

**Caution from the AI-routing field: don't let the router re-classify.** A subtle failure mode in agentic routers is the router silently re-running classification with a different prompt/context and producing a *different* family than Step 3's confirmed one — destroying the "no re-refinement" guarantee (FR-016) and the user's confirmed label. The router must be a **pure consumer** of the persisted family. If the family is absent (goal never refined), the router returns a `needs-classification` handle (a *named* state), not a guess — same fail-loud discipline as the stub.

**Net recommendation for AI-native fit:** router = deterministic `routing_service.resolve(family) → WorkflowHandle`; the LLM lives only in Step 3's classifier; the decision persists as typed goal columns the next agent reads; exposure via the existing trigger/delegation/skill rail gives human+agent parity for free; the router never re-classifies — absent family → named `needs-classification` handle.

**Sources**
- https://github.com/aurelio-labs/semantic-router
- https://builder.aws.com/content/31u60Xzm1ymjMpCi5kTmFutCyiN/hands-on-project-using-kiro-spec-driven-development
- https://www.digitalapplied.com/blog/multi-agent-orchestration-5-patterns-that-work
- https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs

---

## 4. Community Wisdom

**The strongest community consensus relevant to Step 6 is the registry/strategy pattern as the cure for "dispatch by if/else," and it maps one-to-one onto the router.** Practitioner writing is emphatic: a registry "maintains a lookup (usually a Map) of available strategies keyed by some identifier, and instead of using if/else or switch statements, you fetch the strategy from the registry" — turning the architecture "into a plugin-based one where core dispatch logic doesn't change and no more 'elif' branches are added" ([DEV — Strategy + Factory](https://dev.to/tamerardal/dont-use-if-else-blocks-anymore-use-strategy-and-factory-pattern-together-4i77); [Medium — Strategy + Registry in Spring](https://medium.com/@sarathesid/strategy-pattern-with-a-registry-pattern-using-springboot-0aa46b1743e9)). The directly-applicable framing: *"Input data flows to the registry, which automatically routes it to the right transformer, then returns the clean output"* ([Valentino — Strategy in JS](https://www.valentinog.com/blog/strategy-pattern-javascript/)). For v2: the **family registry** is a dict `{family: WorkflowHandle}`; adding a real pipeline later is registering a new handle, "core dispatch logic doesn't change." This is the community's exact prescription for a maintainable router and satisfies the EIP "easy to maintain" warning from §2.

**On the registry *miss* — the community is clear it should be explicit, not a silent default.** The registry pattern writeups treat an unknown key as an error condition to validate, and combine the registry with a strict whitelist so "anything off-schema falls back to sensible defaults rather than crashing" *at the classification layer* — but the *routing* layer's missing-handler case is handled by making the map total or raising ([Mark Torres — Registry](https://markptorres.com/ai_workflows/2025-12-02-registry-pattern); [GeeksforGeeks — Registry](https://www.geeksforgeeks.org/system-design/registry-pattern/)). The v2 translation: the map is **total** (every family present), so there is no miss for *known* families; the only "miss" is an *unknown* family, which routes to a named `generic`/`unmatched` handle that *announces itself* (US2 Scenario 4's "note the unmatched classification") — distinct from FR-015's prohibition on silently routing an *implemented-family* goal into a generic pipeline.

**Feature-flag practitioners supply the "stub must be visibly off, and the off-path must be real" wisdom.** The most-cited failure mode: *"Many teams only test the new path (flag on) and neglect the old path (flag off). When the flag is toggled off in an emergency, the fallback is broken because no one tested it"* ([Growthbook — 12 mistakes](https://www.growthbook.io/blog/12-common-feature-flag-mistakes-to-avoid)). Transferred to stubs: a stub handle is the "flag off" path — it must be a *first-class, tested* state (the router returns it, the UI renders it, an agent can read `status: "stub"`), not an afterthought that throws an unhandled error. Martin Fowler's feature-toggle taxonomy reinforces keeping the toggle point *narrow and visible* ([Fowler — Feature Toggles](https://martinfowler.com/articles/feature-toggles.html)). The stub is a release toggle: each family pipeline flips from `stub → implemented` in one place (the registry) as its later goal lands.

### Common mistakes practitioners call out (and the v2 guard)
- **Routing logic as scattered `if/elif`** → registry/dict, single dispatch point (Strategy+Registry).
- **Silent default on unknown key** → total map + named `unmatched`/`needs-classification` handle that announces itself.
- **Stub/"flag-off" path untested** → stub is a first-class returned value with a `status` field, covered by a test asserting "bug family → stub handle with named steps."
- **Router that re-derives instead of reads** → consume persisted family; never re-classify (FR-016).
- **Router becomes a god-object rules engine too early** → keep it a flat map until rule-of-three (EIP "configurable rules engine" is the *later* state, not v2).

### Sources
- https://dev.to/tamerardal/dont-use-if-else-blocks-anymore-use-strategy-and-factory-pattern-together-4i77
- https://medium.com/@sarathesid/strategy-pattern-with-a-registry-pattern-using-springboot-0aa46b1743e9
- https://www.valentinog.com/blog/strategy-pattern-javascript/
- https://markptorres.com/ai_workflows/2025-12-02-registry-pattern
- https://www.geeksforgeeks.org/system-design/registry-pattern/
- https://www.growthbook.io/blog/12-common-feature-flag-mistakes-to-avoid
- https://martinfowler.com/articles/feature-toggles.html

---

## 5. Frameworks & Methodologies

The router sits at the intersection of three named patterns. Each contributes one design constraint.

| Pattern | What it contributes to the router | Canonical guidance | v2 application |
|---|---|---|---|
| **Content-Based Router** ([Hohpe/Woolf EIP](https://www.enterpriseintegrationpatterns.com/patterns/messaging/ContentBasedRouter.html)) | The *component identity*: a dedicated router between the classifier and the workers | "route each message to the correct recipient"; keep "the routing function easy to maintain"; escalate to a "configurable rules engine" only when sophisticated | A dedicated `routing_service`, declarative map, NOT a rules engine yet |
| **Strategy + Registry** ([refs in §4](https://markptorres.com/ai_workflows/2025-12-02-registry-pattern)) | The *implementation*: a keyed lookup of handlers, no if/else | register strategies by key; "core dispatch logic doesn't change" as you add handlers | `{family: WorkflowHandle}`; new pipeline = register a handle |
| **Feature Toggle (release flag)** ([Fowler](https://martinfowler.com/articles/feature-toggles.html)) | The *stub lifecycle*: a visible on/off per family | keep toggle points narrow; test the off-path | `WorkflowHandle.status ∈ {stub, implemented}`; flip in one place |
| **Null Object vs Special Case** (Fowler PoEAA) | The *anti-pattern boundary*: a Null Object that silently no-ops is wrong here | a Null Object is for "do nothing safely"; a *Special Case* object can carry meaning | The stub is a **Special Case**, not a Null Object — it *announces* "not built, here are the steps" |

**The decisive methodological distinction for FR-015 — Special Case, not Null Object.** A Null Object "absorbs" the missing behavior silently (the exact silent-fallback FR-015 forbids). A **Special Case object** is a polymorphic stand-in that *carries explicit meaning* — here, `WorkflowHandle(status="stub", steps=[...], message="Bug-fix pipeline not yet implemented")`. The router always returns a *real, informative* handle; the difference between implemented and stub is a *field on the handle*, not the presence/absence of a return value. This is what makes "route to a stub that names the steps rather than failing or silently falling back" (US6 Scenario 2) a structural property rather than a runtime check.

**Reversibility framing (from Step 3's Type-1/Type-2 lens) applies to the seam decision itself.** Extracting the router is a *two-way door*: if it's wrong, the pure function folds back into the agent cheaply. *Not* extracting it and later needing phase-agnostic invocation is a *one-way-ish door* — you've coupled routing to the refinement conversation and every future phase re-litigates the boundary. The asymmetry favors extraction (cheap to undo, expensive to retrofit), independent of the FR-016 mandate.

**Where the routing decision lives — schema methodology.** The house style (`02-canonical-source-of-truth-code.ai.md`, Key Takeaway 1) is "DB is canonical, files are read-only projections." `phase` already lives as a typed column on `goals` (`schema.sql:5`). The routing decision is *the same kind of thing as phase* — a small, queryable, enumerable goal attribute that drives downstream behavior. **Therefore model it the same way: typed columns on `goals` (`workflow_family`, `routing_handle`, `routed_at`), projected into `goal.yaml` by the existing `_write_goal_yaml` render** (`goal_service.py:337`). A separate `goal_routing` history table is the upgrade path *if* US6 Scenario 4 (reclassification surfacing) needs an audit trail of prior decisions — defer unless required.

### Sources
- https://www.enterpriseintegrationpatterns.com/patterns/messaging/ContentBasedRouter.html
- https://martinfowler.com/articles/feature-toggles.html
- https://martinfowler.com/eaaCatalog/specialCase.html
- https://markptorres.com/ai_workflows/2025-12-03-strategy-pattern
- https://lostechies.com/derickbailey/2012/10/31/abstraction-the-rule-of-three/

---

## 6. Contrarian Perspectives

**The sharpest objection: building a phase-agnostic router seam now is textbook speculative generality — YAGNI says don't.** Only the requirements phase calls it today (the spec admits this in Out of Scope: "only the requirements phase invokes it in v2"). Building extraction + a registry + persisted columns + an agent wrapper to support phases that don't yet call it is "building infrastructure for needs that haven't materialized" — the precise definition of the YAGNI violation ([aipatternbook — YAGNI](https://aipatternbook.com/yagni); [Fowler — Yagni](https://martinfowler.com/bliki/Yagni.html)). Fowler's four costs all apply: cost of build (the seam), cost of delay (time not spent on the headline comprehension thread, Step 5), cost of carry (every reader now navigates router indirection), cost of repair (the seam is likely *wrong* — designed before any real pipeline exists to inform it). And the deeper cut: *"Too General Too Soon"* warns the danger "hides deep under the surface and only becomes apparent once it's too late… code becomes fragile as modifications in one consumption path unexpectedly break another" ([Frontend at Scale](https://frontendatscale.com/issues/15/)). A router abstraction designed against *zero* real consumers is the highest-risk possible abstraction — you're guessing the interface from one usage.

**The Rule of Three sharpens it: you have exactly *one* consumer, not three.** *"Wait until you see a pattern three times before extracting it… Code can be copied once but the third time you need it, you should abstract it"* ([Los Techies — Rule of Three](https://lostechies.com/derickbailey/2012/10/31/abstraction-the-rule-of-three/)). The router has one caller (requirements). Extracting now crystallizes "a misunderstanding into code structure" before the second and third phase-callers exist to reveal what the interface actually needs.

**The router-as-bottleneck warning is real and self-inflicted.** Hohpe's own caution — the router "can become a point of frequent maintenance" — means a *premature* router becomes a hub everyone must edit, designed against guesses. Worse, every routing source notes routers tend to grow into "configurable rules engines" ([EIP](https://www.enterpriseintegrationpatterns.com/patterns/messaging/ContentBasedRouter.html)); a v2 team eager to "do it right" may build that engine for five families, four of which are stubs — overhead with no payoff.

### The honest resolution (steelman → synthesis)

The contrarian is **right about the pipelines and wrong about the seam**, and Fowler himself draws the exact line that resolves it:

> *"Yagni only applies to capabilities built into the software to support a presumptive feature, it does not apply to effort to make the software easier to modify."* — [Fowler, Yagni](https://martinfowler.com/bliki/Yagni.html)

- The downstream **pipelines** = presumptive *capabilities* → YAGNI applies → **stub them** (this is literally FR-015; the spec already agrees with the contrarian here).
- The **seam** = "effort to make the software easier to modify" → YAGNI explicitly *exempts* it. *"Yagni requires (and enables) malleable code."*

And Fowler's no-cost exception nails the v2 case: *"If you do something for a future need that doesn't actually increase the complexity of the software, then there's no reason to invoke yagni"* — his example is a lookup table for messages to ease future translation. **The v2 router IS a lookup table (`{family: handle}`).** It barely increases complexity over the inline `if family == "bug"` the agent would otherwise contain — and it's a *generalization of `STARTER_TASKS`, a lookup table this codebase already ships*. The honest contrarian residue, which the synthesizer should bake in as guardrails:

1. **Keep the seam minimal** — a dict, a persisted decision, a thin service/skill wrapper. **No rules engine, no workflow DSL, no plugin-loading framework.** Resist the "do it properly" gold-plating.
2. **Don't build the phase-agnostic *wiring* into non-requirements phases** — the spec already scopes this out. Build the *callable surface* (it costs ~nothing: an HTTP route + skill), not the callers.
3. **The strongest defense isn't "we'll need it later" — it's "it's nearly free *and* it removes a worse alternative."** The alternative to the seam is inline routing inside `cast-refine-requirements`, which *violates FR-016 by construction* and re-couples routing to the conversation. The seam isn't speculative generality; it's the *simplest* design that satisfies a stated requirement.

**When the contrarian would be right (the kill condition):** if FR-016 (phase-agnostic) were dropped and routing were truly forever single-caller, inline routing inside the agent would be correct and the seam would be pure YAGNI. The seam's entire justification rests on FR-016 being a real, owner-confirmed requirement. **Flag for plan review: confirm FR-016 is genuinely wanted, not aspirational** — it is the load-bearing premise for extraction.

### Sources
- https://martinfowler.com/bliki/Yagni.html
- https://frontendatscale.com/issues/15/
- https://lostechies.com/derickbailey/2012/10/31/abstraction-the-rule-of-three/
- https://aipatternbook.com/yagni
- https://www.enterpriseintegrationpatterns.com/patterns/messaging/ContentBasedRouter.html

---

## 7. First Principles Analysis

**The irreducible core.** Routing is *late binding*: deferring the choice of "what work follows" from authoring-time to a decision keyed on data that exists at decision-time. Strip Step 6 to atoms and it is one pure function plus one fact:

- **The function:** `resolve(family) → handle`. Total, deterministic, side-effect-free. Given the same family it always returns the same handle. This is the entire router.
- **The fact:** the goal *has a family* (a durable attribute), and the resolution is *recorded* so it need not be recomputed. This is FR-014.

Everything else — phase-agnosticism, stubs, agent parity, the seam — is a *consequence* of getting those two atoms right, not additional machinery.

**Why phase-agnosticism is free once the atoms are right.** If `resolve` is a pure function of `family`, and `family` is persisted on the goal, then *any* caller in *any* phase that can read the goal can call `resolve` and get the right answer. Phase-agnosticism is not a feature you *build*; it is a property you *fail to destroy*. You destroy it by (a) making the router depend on conversation state only present during refinement, or (b) re-deriving the family instead of reading it. Avoid both and FR-016 is automatic. This is why "where the router lives" matters: inside the refinement agent, temptation (a) and (b) are ever-present; as a standalone pure service, they're structurally impossible.

**Why the decision must be recorded, from first principles.** A route that isn't persisted must be *recomputed* on every invocation. Recomputation either (a) replays the (expensive, possibly LLM-driven) classification — violating "no re-refinement" — or (b) risks a *different* answer than the user confirmed — violating consistency. The only way to guarantee "re-invoking from another phase yields the same handle" (SC-005) is to **store the handle and read it back**. Recording isn't bookkeeping; it's the mechanism that makes phase-agnostic invocation *correct*, not merely *possible*.

**Why a stub is a Special Case, not an absence.** The function is *total* — defined for every family — because partiality is the silent-fallback bug. A partial function (defined only for implemented families) forces every caller to handle "undefined," and the cheapest handler is a silent default → exactly FR-015's prohibition. Make it total by returning, for unimplemented families, a handle that *is a real value carrying its own meaning* (`status="stub"`, `steps=[...]`). Totality is the first-principles statement of "named stub, never silent fallback": **there is no undefined case to fall through, so there is nothing to fall back to.**

**The minimum viable router (what v2 actually is).**
```
WorkflowHandle = { family, status: "implemented"|"stub"|"unmatched"|"needs-classification",
                   steps: [...], pipeline_ref: str|null, message: str }

REGISTRY = {                                  # the whole router, as data
  "bug-fix":      Handle(stub,  steps=["logs","RCA","confirm","fix/test"]),
  "prototype":    Handle(stub,  steps=["spike","demo","learnings"]),
  "new-initiative":Handle(stub, steps=["PRD","architecture","plan"]),
  "data-analysis":Handle(stub,  steps=["question","sources","analysis","writeup"]),
  "exploration":  Handle(stub,  steps=["frame","probe","synthesize"]),
}
def resolve(family):
  if family is None:        return Handle("needs-classification", ...)   # never guess
  return REGISTRY.get(family, Handle("unmatched", family=family, ...))   # announces itself
```
Five lines of logic. The rest is (1) two columns on `goals` + the existing `goal.yaml` render, (2) one HTTP route / skill / agent wrapper reusing the existing trigger rail, (3) a UI badge generalizing the existing `recommended_agent` badge. **Essential:** the pure `resolve`, the persisted decision, totality. **Convention:** that it's exposed as an "agent" vs a "service" (it's a service with thin wrappers), the exact family names, whether history is a table or a column.

**Essential vs convention summary.** *Essential:* late binding (resolve at decision-time), a total function (no silent fallback), persisted decision (phase-agnostic correctness), pure consumption of the family (no re-classify). *Convention:* the registry living in `config.py` vs a DB table, the handle being an agent name vs a pipeline ref, five families vs N, calling the wrapper `cast-router`. Build the *essentials* as the seam; keep the *conventions* soft so the real pipelines (later goals) can reshape them without re-opening the interface.

**Sources**
- https://martinfowler.com/bliki/Yagni.html
- https://martinfowler.com/eaaCatalog/specialCase.html
- https://www.enterpriseintegrationpatterns.com/patterns/messaging/ContentBasedRouter.html
- https://github.com/aurelio-labs/semantic-router

---

## Code-Grounding Appendix (this codebase, verified file:line)

Citations gathered firsthand from `/home/sridherj/workspace/diecast` to ground the placement/recording/seam claims. (Complements `02-canonical-source-of-truth-code.ai.md`, which covers the requirements store.)

- **Existing static router precedent:** `cast-server/cast_server/config.py:77-96` — `STARTER_TASKS` is a hardcoded `phase → recommended_agent` map (`"exploration"→"cast-explore"`, `"plan"→"cast-high-level-planner"`, `"requirements"→"cast-refine-requirements"`). **This is a primitive workflow router keyed on phase.**
- **Resolved-handle persistence precedent:** `tasks.recommended_agent` column (`db/schema.sql:35`; `models/task.py:29,46`); read back via `agent_service.get_recommended_agents(slug)` (`routes/api_agents.py:78-79`); rendered as a badge + "Run now" button (`templates/fragments/task_item.html:40,73-81`, `task_edit.html:47-50`). **The "record the handle, surface it, make it runnable" loop already exists — for tasks.**
- **The recording gap (FR-014):** `goals` table is metadata-only — `slug, title, status, phase, origin, in_focus, created_at, accepted_at, tags, folder_path, gstack_dir, external_project_dir` (`db/schema.sql:1-13`). **No JSON/metadata column, no `workflow_family`/`routing_handle`.** Recording the routing decision on the *goal* needs new typed columns (or a `goal_routing` table). `phase` (`schema.sql:5`) is the model to mirror.
- **DB-canonical → file-render convention** (how a new goal column reaches `goal.yaml`): `goal_service.py:337` `_write_goal_yaml`, stamped read-only (`02-…-code.ai.md` §2b). New routing columns project into `goal.yaml` via this existing render.
- **Pure-logic-service precedent for an extracted router:** `services/orchestration_service.py:1-3` — "Orchestration service — pure DAG logic… No subprocess/Claude/tmux dependencies." **The router is the same shape: a pure resolver with no LLM/IO.** Model `routing_service.py` on it.
- **Agent registry (how a `cast-router` becomes known/callable):** `agents` table — `name (PK), type, description, input, output, tags, triggers` (`db/schema.sql:60-70`); per-agent `config.yaml` with `model, timeout_minutes, context_mode, allowed_delegations, proactive` (`agents/cast-explore/config.yaml:1-9`). **`allowed_delegations` is the mechanism by which a future phase agent is granted permission to call `cast-router`.**
- **Dispatch / agent-as-caller rail (FR-013):** `routes/api_agents.py` (`POST /api/agents/{name}/trigger`); parent→child delegation via `.delegation-*.json` + `.prompt` (the mechanism this very run uses); `services/agent_service.py`, `subagent_invocation_service.py`, `user_invocation_service.py`, `_invocation_sources.py`. **Human, requirements-agent, and future-phase-agent all reach an agent through this one rail — no new mechanism needed for parity.**
- **Phase model:** `config.py:52` `PHASES = ["requirements","exploration","plan","execution"]`; `config.py:45` `STATUS_TRANSITIONS`; `goals.phase` column (`schema.sql:5`). Phase advancement is goal-state, not conversation-state — the router reads it.
- **Classification lives elsewhere (Step 3), router consumes it:** `cast-refine-requirements.md:305` is where the spec (and today, any family signal) is authored; the router must read the *persisted* family, not re-run this.

---

## Key Takeaways

1. **EXTRACT the router as a pure service + thin wrappers — the decision is over-determined.** FR-016 (phase-agnostic, many callers) logically requires it; the contrarian's own YAGNI rule *exempts* malleability seams; and `orchestration_service.py` proves the house already extracts pure-logic resolvers. Inside-the-agent placement violates FR-016 by construction.

2. **Generalize `STARTER_TASKS`, don't invent a router.** This codebase already ships a static `phase → recommended_agent` table, a persisted resolved-handle column, and a UI badge. v2 adds `family` as a routing key and moves the persisted decision from the task to the goal. Frame the cost as "extend a proven pattern," not "build a subsystem."

3. **The one real schema gap is *where the decision lives*.** `goals` is metadata-only — no place for `workflow_family`/`routing_handle`. Add two typed columns (mirroring `phase`) + `routed_at`, projected into `goal.yaml` by the existing render. A `goal_routing` history table is the upgrade path only if US6 Scenario 4 needs an audit trail.

4. **Stub = total function + Special Case object, never Null Object.** Make `resolve` defined for *every* family; unimplemented families return a real handle with `status="stub"` and named steps; unknown families return a self-announcing `unmatched` handle; absent family returns `needs-classification` (never a guess). Totality is the structural guarantee of "named stub, never silent fallback" (FR-015).

5. **Keep it a lookup table — resist the rules engine.** EIP, registry-pattern, and YAGNI all warn the router becomes a maintenance hub that grows into a configurable engine. v2 is ~5 lines of logic over a dict. The "configurable rules engine" is a *later* state gated by the rule of three, not v2.

6. **Agent-as-caller parity is free.** Expose the router via the existing trigger/delegation/skill rail; `allowed_delegations` gates future-phase callers. Human, requirements agent, and future planner all call the same door — no new mechanism (FR-013).

7. **Router never re-classifies.** It is a pure *consumer* of the persisted family. Re-deriving the family would replay refinement (violating FR-016) or diverge from the user's confirmed label (violating SC-005 consistency). Read state; don't recompute it.

8. **Plan-review flag:** the entire extraction rests on FR-016 being genuinely wanted. Confirm phase-agnostic invocation is a real owner requirement, not aspirational — if routing is forever single-caller, inline placement is correct and the seam is YAGNI. (All sources agree the seam is justified *given* FR-016.)

## Open Questions for the synthesizer / plan review

- **Recording shape:** two columns on `goals` (v2 recommendation) vs a `goal_routing` table (needed only if reclassification *history* must be surfaced for US6 Scenario 4). Decide at plan review against whether Scenario 4 needs an audit trail or just "current vs previous."
- **Handle identity:** is a `routing_handle` an *agent name* (reusing the `agents` registry + `recommended_agent` precedent) or an abstract *pipeline ref* that later resolves to an agent/orchestration? Leaning agent-name for v2 (maximal reuse), abstract ref if pipelines become multi-agent.
- **Registry location:** `config.py` (like `STARTER_TASKS`, simplest, code-reviewed) vs a DB table (queryable, agent-editable). Leaning `config.py` for v2; the EIP "configurable rules engine" (DB/rules) is the deferred upgrade.
- **Reclassification UX (US6 Scenario 4):** when family changes on re-run, *how* is "the downstream workflow has changed" surfaced — a notification (reuse Step 7's FR-019 notification rail?) or a goal-page diff badge? Cross-references Step 7.
- **`cast-router` as agent vs service-only:** does v2 ship a user-invocable `/cast-router` skill + agent, or only the `routing_service` + an HTTP route the requirements agent calls? Minimal v2 = service + route; the skill/agent wrapper is cheap and enables the human button + future-phase parity. Recommend shipping the wrapper (near-zero cost, completes FR-013 surface).
