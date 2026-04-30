# How Diecast fits together

Diecast ships as two layers stacked: a **workflow chain** (Layer 2) that
parents invoke from the top, and a **reference family of opinionated
agents** (Layer 1) that the chain dispatches into. The chain is what
makes opinionated agents composable across teams; the agents are what
make the chain produce real, reviewable output instead of prose.

## The two layers

### Layer 2 — Workflow chain

Layer 2 is the refine-plan-orchestrate-run sequence. Every step writes a
named artifact and suggests the next command. The shape:

- **`cast-refine`** — turns a rough requirement (`requirements.human.md`)
  into a structured spec (`refined_requirements.collab.md`) by asking
  one focused question at a time.
- **`cast-goal-decomposer` + `cast-explore`** — break the goal into
  sub-steps and run a 7-angle research pass for each. Output lands at
  `docs/exploration/<goal>/`.
- **`cast-playbook-synthesizer`** — turns research notes into an
  opinionated, actionable playbook with impact ratings.
- **`cast-high-level-planner`** — reads the goal artifacts and emits a
  phased execution plan at `docs/plan/<date>-<goal>.collab.md`.
- **`cast-detailed-plan`** (and the fan-out variant) — detailed
  per-phase plans, with inline plan-review.
- **`cast-orchestrate`** — dispatches sub-phases through the
  parent-child contract, handles DAG resolution, gates, and parallel
  fan-out.
- **`cast-subphase-runner`** — the executor for a single sub-phase.
  Reads shared context, runs the work, reports back.

Every step is invokable on its own — drop in at the level the work
demands.

### Layer 1 — Reference family

Layer 1 is what the chain dispatches into when actual code needs to be
produced. The reference family shipped at v1 is **`cast-crud`**: a
maker chain that takes a schema and produces an entity, a repository,
a service, a controller, and the corresponding tests, paired with
compliance checkers that validate the output.

The Layer 1 family demonstrates the **maker-checker discipline**:

- Each maker agent has a paired checker that validates the output
  against the spec.
- The chain calls the maker; the chain calls the checker; if the
  checker fails, the chain re-runs the maker rather than escalating
  to the human prematurely.
- The pattern is what makes Layer 1 modules reliable across runs.

Read [the worked maker-checker walkthrough](./maker-checker.md) for an
end-to-end example using `cast-crud`.

## How they compose

```text
parent (you) ──► Layer 2 chain
                   ├── cast-refine
                   ├── cast-goal-decomposer
                   ├── cast-explore
                   ├── cast-playbook-synthesizer
                   ├── cast-high-level-planner
                   ├── cast-detailed-plan
                   ├── cast-orchestrate
                   └── cast-subphase-runner
                                │
                                ▼
                   Layer 1 reference family
                   ├── cast-crud-orchestrator
                   │     ├── cast-schema-creation
                   │     ├── cast-entity-creation
                   │     ├── cast-repository
                   │     ├── cast-service
                   │     └── cast-controller
                   └── paired checkers
                         ├── cast-crud-compliance-checker
                         └── cast-mvcs-compliance
```

Read top-to-bottom: a parent invokes a Layer 2 step, that step
dispatches into Layer 1 makers, and each maker is paired with a
checker. The whole thing is files-on-disk — no shared in-memory
state, no required server.

## Where parent and child meet

The chain composes via the **parent-child delegation contract**: every
dispatch writes a `.agent-run_<RUN_ID>.prompt` and waits for a
`.agent-run_<RUN_ID>.output.json` to appear. The parent polls the
output file with an exponential backoff cadence. The contract is
canonical; the local cast-server is a read-through. See
[the delegation pattern doc](./delegation-pattern.md) for the schema,
the backoff cadence, and the `human_action_needed` escape hatch.

## Where to go from here

- [Worked example: maker-checker walkthrough](./maker-checker.md) — the
  Phase 5 reference for how Layer 1 modules are structured.
- [Delegation pattern](./delegation-pattern.md) — the file-based
  contract that lets parents dispatch and wait, server or no server.
- [Roadmap](./roadmap.md) — v1.1 → v1.2 → v2 target sequencing and
  the explicit kill criterion.
- [Multi-harness future state](./multi-harness.md) — why v1 ships
  Claude-only and what would change that.
- [Thesis](./thesis.md) — the launch-blog-post outline arguing for
  workflow-over-model investment.
