# Thesis: Fixes the workflow, not the model

> This file is the **launch blog post outline** for Diecast v1.0.0. The
> finished prose lives on the maintainer's blog, not in the repo. This
> outline is the structural scaffold and the canonical pull quotes.

---

## Why now

The agent ecosystem has spent the last eighteen months treating AI coding
quality as a model problem. Every release cycle promises a stronger base
model, a wider context window, a better tool-use harness — and senior
engineers shipping real code keep hitting the same three walls anyway. The
walls are not in the model. They are in the workflow around the model.

Diecast is the project that takes that observation seriously. It is built
on Claude Code, but the bet is not Claude-specific: any harness that lets
parents dispatch children and read files will benefit from the discipline.
The thesis underneath the project — and the thesis this post argues for —
is that opinionated, file-based, parent-child workflow scaffolding fixes
more of the AI coding pain than any model upgrade has in the last year.

This is being published now because the repo just hit v1.0.0. The
maintainer wanted the workflow runtime tested against real shipping code
for several months before opening it. The plumbing has stopped breaking.
The opinions have stopped changing weekly. The pattern has earned the
"v1" label.

## Three failure modes

The three walls below are what convinced the maintainer to invest in
workflow scaffolding rather than prompt engineering. They show up across
every Claude Code project once it crosses ~5K lines.

### Failure 1: AI writes correct code, but not the way you would

The diff lands green. Tests pass. The reviewer cannot point to a bug. But
six weeks later, when the original author needs to modify the area, the
intuition for *why* the code is shaped the way it is has evaporated. The
agent solved the local problem; the human lost the model of the codebase.
The cost is not in the diff — it is in every future change.

### Failure 2: Junior-member output explodes PR volume

A small team using AI well will out-produce a small team coding by hand.
That is the promise. It is also the trap. PR volume scales linearly with
agent throughput; reviewer attention does not. The codebase becomes a
black box not because the code is bad, but because nobody has the time
to keep the mental model current at the new pace.

### Failure 3: AI still cannot do large, opinionated tasks the way you want

For anything past a self-contained refactor, the agent needs a spec, a
plan, a decomposition, and constant checking. RBAC migrations, schema
changes that touch 40 files, multi-service refactors — these still
demand a human who can hold the whole picture and arbitrate trade-offs.
"Just give the agent the requirements" is an empty promise at this
scale.

## Layer-2 thesis

> "Fixes the workflow, not the model."

What "Layer-2" means in Diecast: the workflow chain — refine, decompose,
explore, plan, orchestrate, run — is the load-bearing structure. The
agents themselves (Layer-1) are interchangeable. The chain is what
turns AI from "powerful junior who needs constant supervision" into
"junior who follows the same shape every time, hands off correctly,
and surfaces decisions you actually need to make."

What gets cast: every step has a known input shape, a known output
file, and a known next-step suggestion. Casting is a forge metaphor on
purpose — the die is the spec, the cast is what comes out of the
agent, and the discipline is that two casts from the same die produce
the same shape. Not bit-identical, but *role*-identical. A
`requirement.collab.md` from one run is interchangeable with a
`requirement.collab.md` from another run downstream.

Why workflow-shaped scaffolds beat prompt-tuning: prompts decay. They
drift across model versions, across context loads, across personal
revision habits. Workflow shape — file paths, contract schemas,
parent-child polling cadence — does not. A workflow scaffold is the
part of the system that survives a model upgrade and survives a
maintainer change. That is why Diecast invests there.

The maker-checker pattern is the reliability spine of Layer-1. Every
maker agent ships paired with a checker that validates the output
against the spec. The chain calls the maker; the chain calls the
checker; if the checker fails, the chain knows to re-run rather than
escalating to the human prematurely. See
[the worked example](./maker-checker.md) for what that looks like in
practice.

## What v1 promises

- **The workflow chain.** `cast-refine` → `cast-goal-decomposer` →
  `cast-explore` → `cast-high-level-planner` → `cast-detailed-plan` →
  `cast-orchestrate` → `cast-subphase-runner`. Every step writes a
  named artifact under `docs/`. Every step suggests the next.
- **Parent-child delegation, server or no server.** Any cast-* agent
  can dispatch a child. The child writes its result to a
  contract-versioned `.agent-run_<RUN_ID>.output.json`. The parent
  polls the file. The local server is optional — useful for the web
  UI and richer dispatch state, but the file-based contract is
  canonical. See [the delegation pattern doc](./delegation-pattern.md)
  for the schema and polling cadence.
- **The `cast-crud` reference family.** A maker chain
  (`cast-crud-orchestrator`, `cast-schema-creation`,
  `cast-entity-creation`, `cast-repository`, `cast-service`,
  `cast-controller`) plus checkers
  (`cast-crud-compliance-checker`, `cast-mvcs-compliance`). This is
  the canonical example of how Layer-1 modules ship in Diecast — a
  paired maker-checker family with a worked walkthrough.

## What v1 deliberately does NOT promise

- **Cross-harness support.** v1 is Claude Code only. Codex / Copilot
  adapters ship only when a non-Claude user opens an issue asking
  for them unprompted. See [multi-harness future state](./multi-harness.md).
- **A solved evals harness.** v1.2 will land a structured evals
  surface for cast-* agents. v1.0.0 ships the discipline (paired
  checkers, named artifacts) but not a benchmark suite. See
  [roadmap](./roadmap.md).
- **PM-tool integrations.** Linear / Jira / GitHub Issues adapters
  are v2 territory. v1 keeps state in markdown files, deliberately,
  so the workflow chain works with no external dependencies.

## Where this goes next

The launch posts the v1 promise and the three commitments above. v1.1
hardens the agent contracts (target ~30 days post-launch), v1.2 ships
the evals harness (target ~60 days), and v2 opens the PM-tool
adapters (target ~90–120 days). The full sequencing — including the
explicit kill criterion — is in [docs/roadmap.md](./roadmap.md).

Diecast is one maintainer's workflow runtime, opened because the
maintainer believes the pattern generalizes and would like to be
proven right by other people running it on different codebases.
That is the v1 invitation: clone, run, push back.
