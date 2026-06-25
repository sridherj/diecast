---
status: refined
scope_mode: reduction
classification:
  family: new_initiative
  confidence: 0.95
  confirmed_by: auto
  classified_at: 2026-06-25
  taxonomy_version: 1
  alt_family: refactor_migration
confidence:
  intent: high
  behavior: high
  constraints: high
  out_of_scope: high
open_unknowns: 2
questions_asked: 3
---

# neoorg CRUD Workforce + FastAPI Backend

> **Brief maturity:** draft
> **Version:** 0.1.0
> **Linked files:** `goals/neoorg-crud-workforce-fastapi-backend/requirements.human.md`,
> neoorg `docs/spec/maker-checker.collab.md`, `docs/spec/agent-contract.collab.md`,
> `docs/spec/agent-packaging.collab.md`, `docs/spec/tasks.collab.md`, `docs/spec/spine.collab.md`,
> `docs/design/prototype/app.html`, `docs/design/neoorg-cockpit-design-direction.collab.md`

## Intent

When neoorg needs to generate its own MVCS code and finally stand up as a persistent backend, the
founder wants **a code Workforce of conforming maker/checker Pairs** *and* **a FastAPI
control-plane over the existing PGLite spine** — co-developed against one real entity slice — so
that neoorg can write its own server code (dogfooding the org), restore the diecast-style
"start the server → type commands → it persists" experience, and end neoorg's dependence on
diecast for running its own goals.

The org today is **all brains and no code hands**: the magicwand fleet is full at the Apex / Lead /
Expert / Standing-function layers, but the Workforce maker/checker layer has only
`illustration-builder` and `agent-creator`. There is no schema / entity / repository / service /
controller maker, and `build-lead` already *assumes* a marketplace of code builder/checker Pairs
that does not exist. The Python package `src/neoorg/` is a foundation only (spine + trimmed MVCS
bases + the omnigent-adapter boundary) with **no HTTP surface**. This goal fills both gaps at once.

**This Task slice is the first brick of the cockpit backend, and the workforce is the brick-laying
machine.** The cockpit prototype (`app.html`) reads/writes a far larger entity set than goal / task
/ run — Milestones (the loop-log timeline), the build DAG, Pairs / runs / sessions, Decisions,
Gates, Communications, plus telemetry rollups and the CoS / Goal-Director chat rails. This goal
does **not** stand up the cockpit; it proves the *pattern* and the *workforce* that every cockpit
surface will sit on, with the prototype serving as the enumerated backend-breadth spec for the
follow-on slices (see Directional Ideas).

> **Glossary / spec pointers** (the brief uses neoorg's house terms — each links its owning spec):
> **MVCS** = the Model-View-Controller-Service layering already in `src/neoorg/`
> (BaseEntity / BaseRepository+FilterSpec / BaseService / DbSessionManager). **PGLite** = the
> embedded-Postgres spine (`spine.collab.md`). **leak-guard** = the lint that fails if an omnigent
> `/v1/` wire string appears outside `src/neoorg/adapter/`. **maker/checker Pair**, **maker owns the
> loop**, **dispatcher enforces proof** = `maker-checker.collab.md`. **Manifest / envelope /
> magicwand-\*.md authoring format** = `agent-contract.collab.md` + `agent-packaging.collab.md`.

## User Stories

### US1 — A code-writing Workforce the build layer can actually staff (Priority: P1)

**As** the org's build layer, **I want** neoorg-native maker/checker Pairs that write MVCS code,
**so that** `build-lead` can staff a code milestone from a real marketplace instead of an empty one.

**Independent test:** `build-lead` is handed a milestone, names the code Pairs it needs, and every
named Pair resolves to an installed, conforming agent in `~/.claude/agents/`.

**Acceptance scenarios:**
- **Scenario 1:** WHEN a code Pair is authored, THE SYSTEM SHALL produce both a builder and its
  paired checker, each conforming to agent-contract + maker-checker + agent-packaging.
- **Scenario 2:** WHEN a builder completes its loop, IF any declared checker has not produced proof,
  THE SYSTEM SHALL refuse the builder's output (the dispatcher enforces proof; it never calls the
  checker itself).

### US2 — A neoorg FastAPI backend over the spine (Priority: P1)

**As** the founder, **I want** an HTTP control-plane on top of the existing `src/neoorg/` PGLite
spine exposing full CRUD over the in-scope entities, **so that** state persists and agents and the
future cockpit read/write through one door — the diecast `cast-server` experience, neoorg-native.

**Independent test:** start the server, `POST` a Task, `GET` it back, `PUT` an update, `DELETE` it;
restart the server mid-way and confirm the row persisted.

**Acceptance scenarios:**
- **Scenario 1:** WHEN the server is started, THE SYSTEM SHALL expose `POST` / `GET` (one + list) /
  `PUT` / `DELETE` over each in-scope entity and persist writes to the PGLite spine.
- **Scenario 2:** WHEN a write succeeds, THE SYSTEM SHALL survive a server restart with the row
  intact (the spine, not in-memory).
- **Scenario 3:** IF a `GET` / `PUT` / `DELETE` targets a missing id, THEN THE SYSTEM SHALL return
  `404`; IF a `POST` / `PUT` body fails validation, THEN THE SYSTEM SHALL return `422` with the
  field errors (FastAPI/Pydantic default).

### US3 — The Workforce proves itself by building Goal end-to-end against the Task/Run oracle (Priority: P1)

> **Reality check (2026-06-25):** `Task` and `Run` (`AgentRun`) already have entity/repository/
> service/schema + migrations in `src/neoorg/`; the dispatch/proof machinery already exists in
> `contract/`. So the bootstrap is *thin* (the HTTP surface only), and the Workforce's proving slice
> is **`Goal`** — the one trio member with nothing built — not a re-build of the already-built Task.

**As** the build team, **I want** the Workforce to **build `Goal` end-to-end** via `crud-builder`
(the missing trio member), with its craft judged against the existing hand-written Task/Run layers as
the oracle, **so that** the workforce is proven on real, full-stack work against a concrete craft
target — and the trio is completed *by the workforce*.

**Independent test:** the workforce-built `Goal` slice (produced by `crud-builder` dispatched through
the server) passes its generated tests against live PGLite and its craft diffs acceptably against
`task_service.py` / `task_repository.py`.

**Acceptance scenarios:**
- **Scenario 1:** WHEN `crud-builder` builds `Goal`, THE SYSTEM SHALL have each layer produced by its
  builder, verified by that builder's checker (server-enforced), and matching the Task/Run craft oracle.
- **Scenario 2:** WHEN the workforce then builds a further new entity, THE SYSTEM SHALL produce its
  CRUD surface by re-using the proven Pairs, the only new input being the entity's shape.

### US4 — New Pairs are born conforming (Priority: P2)

**As** the org, **I want** each new code Pair authored through the `agent-creator` recruiter and
verified by `agent-checker`, **so that** it joins the roster proven-conforming rather than
hand-rolled and drifting.

**Independent test:** each new Pair has an `agent-checker` pass recorded (the checker's output
envelope) before it is used in the slice.

**Acceptance scenarios:**
- **Scenario 1:** WHEN a code Pair is created, THE SYSTEM SHALL route it through `agent-creator`
  (a maker whose artifact is another agent) and `agent-checker` before first use.

### US5 — Composition under the locked ownership model (Priority: P2)

**As** an architect, **I want** the top-level `crud-builder` to compose the per-layer builders the
way diecast's `cast-crud-orchestrator` composed its chain, **but expressed in neoorg's locked
maker-checker semantics**, **so that** the resolved model — not the diecast one — is what gets baked
into the Pairs.

**Independent test:** `crud-builder` invokes each `mvcs-*-builder` via the Invoke↓ channel; each
sub-builder owns its own loop and declares its own checker; `crud-builder` never calls a sub-layer's
checker; `crud-builder` has its own `crud-checker` (whole-CRUD compliance). No builder calls another
builder's checker.

**Acceptance scenarios:**
- **Scenario 1:** WHEN `crud-builder` runs, THE SYSTEM SHALL dispatch the per-layer builders as
  sub-makers (maker-invokes-maker), each proving its own checker; the dispatcher enforces each
  proof and `crud-builder` proves the whole-CRUD checker.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | Author the neoorg code Workforce as maker/checker Pairs in the `magicwand-*.md` format: the composer **`magicwand-crud-builder`** / `magicwand-crud-checker` plus the per-layer **`magicwand-mvcs-{schema,entity,repository,service,controller}-builder`** / `-checker` and one **`magicwand-mvcs-test-builder`** / `-checker`. | See the naming table in Directional Ideas. Each builder handles BOTH **create** (new entity) and **update** (modify existing) — one agent per layer, not separate create/update agents (see Decisions). |
| FR-001a | Each builder is **update-safe**: it detects existing artifacts and makes surgical edits that preserve hand-written/custom code, and on update emits **alter-not-recreate** migrations. Each paired checker gates the dangerous cases — clobbered custom code and destructive/data-losing migrations. The create-vs-update divergence is sharpest at the entity/table-migration layer (`CREATE` vs `ALTER`), where the `mvcs-entity-builder` + checker need the most discipline. | Keeps the lean roster while making "update" first-class. |
| FR-002 | Every Pair conforms to agent-contract (Input/Output/Run-time-Config triad + output envelope), maker-checker (maker owns the loop), and agent-packaging (file-driven loader, `~/.claude/agents/`, name + description rules); born-conforming via `agent-creator` + `agent-checker`. | |
| FR-003 | `magicwand-crud-builder` composes a full CRUD implementation by dispatching the per-layer builders **through the neoorg server over HTTP** (see Decisions): the server is the dispatcher. `crud-builder` requests dispatch of each sub-builder; the server enforces each sub-builder's checker proof; `crud-builder` consumes the proven envelopes and never calls a checker; `crud-builder` has its own whole-CRUD `crud-checker` (enforced by the server when `crud-builder` is itself dispatched). | This makes the server the dispatcher the maker-checker contract already names; mirrors diecast's `cast-crud-orchestrator` over `cast-server` HTTP. |
| FR-004 | Stand up a FastAPI app over `src/neoorg/` exposing **full CRUD** (`POST` / `GET` one + list / `PUT` / `DELETE`, with `404` / `422` error semantics) over the in-scope entities; writes persist to the PGLite spine and survive restart, including any table migration the entity needs. | Server entrypoint + migration story is part of this FR (see Constraints). |
| FR-005 | **Bootstrap is thin** — Task/Run already have entity/repo/service/schema + migrations; hand-build only the **HTTP surface** (app + `CRUDRouterFactory` + Task/Run controllers + the dispatch endpoint) to get the server working. **Then** the Workforce **builds `Goal` end-to-end** via `crud-builder` (the proving slice), judged against the existing Task/Run craft; after it matches, `crud-builder` builds the next **new** entities. | Existing Task/Run layers = the craft oracle; the workforce completes the trio by building Goal. |
| FR-009 | The **`Goal` entity** is **lean**: typed columns for identity/lifecycle/routing (`id` `goal_…`, `slug`, `title`, `description`, `status`, `phase`, `workflow_family`, `origin`, `in_focus`, `tags`, timestamps) **plus a JSONB `attributes` slot** holding the nine Project-Attribute dials (`mode`/`fidelity`/`investment`/`pace`/`horizon`/`risk`/`stakes`/`clarity`/`autonomy`). A separate **Project** entity + the project→goal cascade are **deferred** (no `project_id` column yet). **Task gains a `goal_id`** FK (the work-tree root link). | Dials live in JSONB because `project-attributes` is EVOLVING/NOT-BINDING — reshape without migrations. `Goal`-as-entity must reconcile with the unified-Task-primitive model (Open Questions). |
| FR-006 | Workforce output conforms to **neoorg's** stack: the PGLite spine, the trimmed MVCS bases, and the `leak-guard` adapter↔core boundary. `linkedout-oss` is the **craft / quality bar**, NOT the conformance target. | |
| FR-007 | Produce a one-page reconciliation note (owned by the plan, lives at `docs/plan/…` or the goal dir) stating how `crud-builder` composes under the locked ownership model; every authored builder charter references it. | Mostly resolved in-principle by the composition requirement above; the note records it durably. |
| FR-008 | The system is **bootstrapped manually**: the server (trio CRUD + the agent-dispatch surface) is hand-built first — leveraging diecast's agents — to get neoorg working, *before* the Workforce exists. The per-layer builders can run standalone, but **composed builds dispatch through the running server**, so the server is a runtime dependency for composition. No circularity: the server stands before the composer runs. | Supersedes the earlier "no running server" premise (see Decisions). |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | A cold operator can `POST` a Task and `GET` / `PUT` / `DELETE` it through the running neoorg FastAPI app, and a created row survives a server restart. | Manual + integration round-trip against live PGLite. |
| SC-002 | The workforce builds `Goal` end-to-end via `crud-builder`; its craft matches the existing Task/Run oracle and it passes its generated tests; the same composer then produces further new entities. | Diff vs Task/Run craft + `uv run pytest`. |
| SC-003 | Each new Pair has an `agent-checker` pass on record and installs into `~/.claude/agents/`. | Checker output envelope + install check. |
| SC-004 | `leak-guard` passes (no `/v1/` strings outside the adapter) and MVCS-compliance holds on every built slice. | `uv run leak-guard` + MVCS compliance check. |
| SC-005 | `crud-builder` composes the per-layer builders with no builder calling another's checker; `crud-builder` proves its own whole-CRUD checker. | Charter/grep audit + a live composed run. |

## Constraints

- **Stack:** Python ≥3.12; the PGLite embedded-Postgres spine over SQLAlchemy's `postgresql`
  dialect; the trimmed MVCS bases already in `src/neoorg/`. Postgres-isms (JSONB, ARRAY, pgvector)
  are kept.
- **Server:** a single FastAPI entrypoint (launchable like diecast's `bin/cast-server`, e.g. a
  `neoorg` server command / uvicorn target) binding localhost; table creation/migration for the
  in-scope entities is part of standing the server up.
- **Boundary:** `leak-guard` — no omnigent `/v1/` wire strings outside `src/neoorg/adapter/`.
- **Contracts:** every new agent conforms to agent-contract + maker-checker + agent-packaging and
  installs via the file-driven loader into `~/.claude/agents/`.
- **Authoring path:** new Pairs are created through `agent-creator` and verified by `agent-checker`
  — not hand-rolled.
- **Ownership model (locked):** maker owns the loop; the dispatcher enforces proof of ALL declared
  checkers and never calls a checker; Workforce makers-only allow-lists. `crud-builder` composes by
  invoking sub-makers, never by reaching past one to its checker.
- **Server is the dispatcher (decided):** per the locked maker-checker contract the dispatcher
  enforces checker proof and never calls a checker — neoorg's server *is* that dispatcher.
  `crud-builder` dispatches sub-builders via HTTP; the server enforces each one's proof. Composed
  builds therefore depend on the running server (the bootstrap server is hand-built first).
- **Builders are create-or-update and update-safe:** one agent per layer for both create and
  update; surgical edits that preserve custom code; alter-not-recreate migrations; checkers gate
  clobbering + destructive migrations.

## Out of Scope

- The full omnigent runtime / SSE event-ingester / durable-ingest pipeline — this goal builds the
  control-plane CRUD surface, not the omnigent event seam.
- **The rest of the cockpit entity set** — Milestone, Decision, Gate, Communication/Notification,
  the build-DAG/step model, and the loop-log read-model + telemetry rollups the prototype shows are
  **explicit follow-on slices** (the same workforce, run later), not this goal.
- Beyond the chosen trio: only **Task → Goal → Run** are in scope here.
- The fuller cast-crud* family beyond the core chain — `custom-controller`, the seed-db /
  seed-test-db creators, and a separate integration-test-creator are deferred (the core chain +
  one `mvcs-test-builder` is the chosen roster).
- Reworking the existing magicwand brains (Apex/Lead/Expert/Standing) — they are done; this goal
  adds the Workforce layer only.
- Migrating the existing diecast goals or the diecast cast-server itself.
- A mechanical port of the diecast cast-crud* agents (explicitly rejected — author native Pairs).

## Directional Ideas

> Non-binding. The founder's HOW, references, and notes — captured and developed, locked nowhere.

### Naming scheme (founder directive: the cast-* names were ambiguous — `cast-service` didn't say *MVCS service*)

The name should state the **layer** and whether it **builds or checks**; the *composition* is
visible too — the composer is `crud-builder`, and the layers it invokes carry the `mvcs-` prefix,
so a `crud-builder` is legibly assembled *from* `mvcs-*` builders.

| Role | Old cast-* | New neoorg |
|---|---|---|
| Composer (top-level, invokes the chain) | `cast-crud-orchestrator` | **`magicwand-crud-builder`** / `magicwand-crud-checker` |
| Pydantic schemas | `cast-schema-creation` | **`magicwand-mvcs-schema-builder`** / `-checker` |
| SQLAlchemy entity | `cast-entity-creation` | **`magicwand-mvcs-entity-builder`** / `-checker` |
| Repository (+FilterSpec) | `cast-repository` | **`magicwand-mvcs-repository-builder`** / `-checker` |
| Service | `cast-service` | **`magicwand-mvcs-service-builder`** / `-checker` |
| Controller | `cast-controller` | **`magicwand-mvcs-controller-builder`** / `-checker` |
| Wiring tests | `cast-*-test` | **`magicwand-mvcs-test-builder`** / `-checker` (split per-layer only if needed) |

Conventions: `-builder` / `-checker` everywhere (matches `illustration-builder`/`-checker` and the
spec's canonical `crud-builder`/`crud-checker`); `mvcs-` prefix removes the `cast-service`-style
ambiguity; the prefix asymmetry (composer has no `mvcs-`, layers do) encodes the hierarchy.

### Approach

- **Author, don't convert.** The cast-crud* agents are diecast-shaped (cast-server API, diecast
  layout, old orchestrator model). Re-express the *craft* as neoorg-native Pairs via
  `agent-creator`; don't import the obsolete model.
- **The server is the dispatcher (composability via HTTP).** `crud-builder` dispatches the per-layer
  builders **through the neoorg server over HTTP** — the founder's "top-level CRUD orchestrator
  calling other workforce agents." This *is* the reconciliation of `cast-crud-orchestrator` into the
  locked contract: the server is the dispatcher the maker-checker spec names — it enforces each
  sub-builder's checker proof; `crud-builder` consumes proven envelopes and never calls a checker;
  the server enforces `crud-builder`'s own whole-CRUD checker. Mirrors diecast's `cast-server` child
  dispatch; mine diecast's child-delegation subsystem for the mechanism.
- **`linkedout-oss` = quality bar.** `~/workspace/linkedout-oss/backend/` is a shipped MVCS backend
  that followed these agents. Use it for *how good the output should look*; conform to neoorg's
  stack, not linkedout's.
- **Manual bootstrap (thin), then dogfood.** Task/Run MVCS + migrations + the dispatch machinery
  already exist — so the manual bootstrap is just the **HTTP surface** (app + `CRUDRouterFactory` +
  Task/Run controllers + the dispatch endpoint wrapping the existing `dispatch_child` /
  `resolve_proof_of_check`). Then the Workforce **builds `Goal` end-to-end** (proving slice), judged
  against the existing Task/Run layers as the craft oracle, and from there builds new entities.
- **The cockpit prototype is the eventual backend-breadth spec.** `app.html` +
  `neoorg-cockpit-design-direction.collab.md` + `neoorg-flows-for-prototype.collab.md` enumerate the
  full surface (Milestones / DAG / Pairs / runs / Decisions / Gates / Communications / telemetry /
  CoS+GD chat). It's **dated** — a "what must be exposed" guide, not a contract — but it's the map
  for which entities become follow-on slices after the trio.

### References

- `~/workspace/diecast/agents/` — the proven cast-crud* family (craft reference).
- `~/workspace/linkedout-oss/backend/` — a shipped MVCS backend that followed those agents.
- neoorg specs: `maker-checker`, `agent-contract`, `agent-packaging`, `tasks`, `spine`.
- `src/neoorg/` — the existing foundation (spine, MVCS bases, adapter boundary).
- `magicwand-agent-creator` / `magicwand-agent-checker` — the recruiter Pair.
- The cockpit prototype + design docs (above).

### Note

This is the **last** neoorg goal run through diecast — the deliverable is what lets neoorg run its
own goals afterward.

## Decisions

| Date | Chose | Over | Because |
|------|-------|------|---------|
| 2026-06-25 | Control-plane trio: **Task → Goal → Run** (Task = proving slice) | Task-only · the full cockpit entity set | The Dashboard's basic read needs the trio, and a reusable composer makes Goal/Run cheap after Task; the full cockpit is unbounded for a first cut. |
| 2026-06-25 | **Core MVCS chain** (schema/entity/repository/service/controller + one test builder) | The full cast-crud* family (custom-controller, seeders, separate integration-test-creator) | The minimum to build a CRUD slice end-to-end; defer the rest Pair-by-Pair. |
| 2026-06-25 | **Per-layer builder Pairs + a composing `crud-builder` Pair** (Workforce, not Lead) | One `crud-builder` doing everything inline · per-layer Pairs sequenced by a Lead | Mirrors `cast-crud-orchestrator` in neoorg semantics; the composer is a maker that invokes per-layer makers, which resolves the reconciliation seam under the locked ownership model. |
| 2026-06-25 | New naming scheme (`magicwand-crud-builder` + `magicwand-mvcs-{layer}-builder/-checker`) | The cast-* names | cast names were ambiguous (e.g. `cast-service`); neoorg names encode layer + maker/checker and make the composition legible. |
| 2026-06-25 | **HTTP dispatch via the neoorg server** for crud-builder→sub-builder composition (server = the dispatcher) | Skill-in-own-context · nested subagents | Makes the server the dispatcher the maker-checker contract already names (enforces proof, never calls a checker); mirrors diecast's `cast-crud-orchestrator`; accepts that composed builds depend on the running server. |
| 2026-06-25 | **Manual bootstrap first** — hand-build the server (trio CRUD + dispatch surface) to get neoorg working, then leverage the Workforce from there on | Workforce-builds-everything-from-the-start | Required by the dispatch decision (the server must exist before the composer can dispatch); removes the bootstrap circularity; pragmatic path to a working system. |
| 2026-06-25 | **One builder per layer for both create and update** (update-safe) | Separate create-vs-update agents | Same craft whether net-new or edited; keeps the lean roster; update-safety (surgical edits, alter-not-recreate migrations, checker-gated) is a charter requirement, not a second agent. |
| 2026-06-25 | **Bootstrap is thin** — hand-build only the HTTP surface (Task/Run MVCS + migrations + dispatch machinery already exist in `src/neoorg/`) | Hand-build the whole trio MVCS from scratch | Discovered the lower stack already exists; re-building it would be wasted work — the existing Task/Run layers are the craft oracle instead. |
| 2026-06-25 | **Workforce's proving slice = build `Goal` end-to-end** (the missing trio member), judged vs the existing Task/Run craft | Re-build Task (now near-fully built) · re-build the whole trio | Task is already built; "re-building" it tests one layer. Building `Goal` is a full-stack proof on real, needed work and completes the trio via the workforce. |
| 2026-06-25 | **`Goal` is its own top-level entity**, kept **lean** — typed lifecycle/routing columns + a JSONB `attributes` slot for the 9 dials; Project entity + cascade **deferred**; Task gains `goal_id` | Goal = a top-level Task (unified primitive) · full Goal+Project with typed dial columns now | Founder: Goal is a top-level entity for sure. JSONB dials because `project-attributes` is EVOLVING/NOT-BINDING — avoid freezing it; defer Project until the cascade firms up. |
| 2026-06-25 | **Canonical service style = the `cast-service`/`cast-crud-orchestrator` convention: schema-in, schema-out**; that styling is the craft oracle, not TaskService's current shape | Treating the existing TaskService as-is as the oracle | `BaseService.create/update` take an ORM **entity** (schema-out but entity-in) — a layering smell, likely "written to go past" (all current callers are internal + already hold entities). The workforce's `mvcs-service-builder` encodes cast styling; TaskService's entity-in is a **fix-candidate**, not a pattern to emulate. New controllers + the `CRUDRouterFactory` are schema-in via an additive shim; refactoring the internal entity-in callers is a later sweep ("we can always fix"). |

## Open Questions

- **[NEEDS CLARIFICATION: server transport/auth for v1]** Is the FastAPI app localhost-only with no
  auth for now (like diecast's dev cast-server), or does it need an auth/token surface from day one?
  Founder to confirm; assumed localhost-only, no auth, unless told otherwise.
- **[NEEDS CLARIFICATION: test-builder granularity]** Ship one `magicwand-mvcs-test-builder` for all
  layer wiring tests, or split per-layer (`-repository-test-builder`, `-service-test-builder`, …) as
  cast did? Assumed single test-builder; split only if the per-layer tests prove too divergent.
- **[NEEDS CLARIFICATION: `Goal` vs the unified-Task primitive]** `Goal` is its own entity (decided),
  but `tasks.collab.md` locks "Task is one unified primitive." Does `Goal` join the spine as a sibling
  of Task, or reference a root Task? Settle at the top of Phase 3 (workforce builds `Goal`) and
  reconcile `tasks.collab.md` via `/cast-update-spec`.
- **[NEEDS CLARIFICATION: exact `Goal` field set]** The lean column list + the nine `attributes` dial
  keys above are the working shape; confirm the precise fields against the cockpit prototype + spine
  when Phase 3 builds `Goal`.
