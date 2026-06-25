# neoorg CRUD Workforce + FastAPI Backend

## Where we are

neoorg today has all the *brains* of the org and none of the *code hands*. The magicwand-*
fleet is fully populated at the Apex / Lead / Expert / Standing-function layers (chief-of-staff,
goal-director, the six leads, ~11 experts, hr/ops/finance). But the **Workforce maker/checker**
layer has only two members — `illustration-builder` and `agent-creator`. There is **no
schema / entity / repository / service / controller maker**. `build-lead`'s charter already
*assumes* it can "staff the milestone with marketplace builder/checker Pairs" — that marketplace
doesn't exist for code yet.

The Python package `src/neoorg/` is a foundation only (entities, the PGlite spine, the trimmed
MVCS bases, the omnigent-adapter boundary with `leak-guard`). There is **no FastAPI app, no HTTP
surface** — the README says so plainly. That's why, unlike diecast, you can't "start a server and
type commands and have it just work."

## What I want

Two things, co-developed, not sequenced one-then-the-other:

1. **A code Workforce** — the missing maker/checker Pairs that actually write MVCS code, born
   into neoorg conforming to our locked contracts (agent-contract, maker-checker, agent-packaging).
   These are the neoorg analogues of diecast's proven `cast-crud*` agents
   (schema → entity → repository → service → controller → tests).

2. **The neoorg FastAPI backend** — the HTTP control-plane on top of the existing `src/neoorg/`
   spine, the thing that restores the diecast "start server → commands persist" experience for
   neoorg. The first real surface is CRUD over the spine primitives (goal / task / run).

## How I think about it (direction, not locked)

- **Don't "convert" the cast-crud* agents.** They are diecast-shaped: they assume cast-server's
  HTTP API, diecast's file layout, and the *old* orchestrator-dispatches-the-chain model. neoorg
  has since **locked a different maker-checker contract** — maker owns the loop, the dispatcher
  enforces proof of all declared checkers and never calls a checker itself. A mechanical port
  would re-import a model we've moved past. Instead **author neoorg-native Pairs via the
  `agent-creator` recruiter**, mining cast-crud* and linkedout-oss for *craft*.

- **linkedout-oss is the quality bar, not the conformance target.** `~/workspace/linkedout-oss`
  is a full MVCS backend that followed these agents (it has real repository/service/controller/
  schema agent-memory and a shipped backend). Use it for *how polished the output should look*.
  But the workforce must conform to **neoorg's** stack — the PGlite spine, the trimmed MVCS bases,
  and the `leak-guard` adapter↔core boundary — not linkedout's stack.

- **The FastAPI is the forcing function, not a dependent phase.** The backend is itself a CRUD
  surface, so building it is the perfect *first job* for the new workforce: it's real, it dogfoods
  the org, and it's exactly the shape these agents are good at. There's no blocking circularity —
  the magicwand agents run as plain Claude Code subagents today with zero server dependency, so
  using them to build the server is fine.

- **Vertical slice first.** Don't build all the Pairs in the abstract then turn to the server.
  Pick **one real entity** (Task — its spec is locked) and drive it end-to-end — schema → entity →
  repository → service → controller → tests — authoring the first cut of each Pair *as* it produces
  real server code. One slice proves every agent against neoorg's real rails AND ships a working
  piece of the FastAPI. Then iterate Pair-by-Pair on the next entities.

- **One design reconciliation up front, before authoring any maker:** how diecast's
  `cast-crud-orchestrator` "dispatch the maker chain" maps onto neoorg's locked maker-checker
  ownership (maker owns the loop; dispatcher only enforces checker proof, never calls one). Settle
  that on paper — it's the one seam where the diecast model and the neoorg contract actually
  disagree, and it's cheaper to settle before it's baked into seven agents.

## References

- `~/workspace/diecast/agents/` — the proven cast-crud* maker/checker family:
  cast-schema-creation, cast-entity-creation, cast-repository, cast-service, cast-controller,
  cast-custom-controller, cast-crud-orchestrator, plus the test makers (cast-repository-test,
  cast-service-test, cast-controller-test, cast-integration-test-creator) and the seeders.
- `~/workspace/linkedout-oss/backend/` — a shipped MVCS backend that followed those agents (the
  craft / quality bar).
- neoorg specs: `docs/spec/maker-checker.collab.md`, `docs/spec/agent-contract.collab.md`,
  `docs/spec/agent-packaging.collab.md`, `docs/spec/tasks.collab.md`, `docs/spec/spine.collab.md`.
- `src/neoorg/` — the existing foundation (spine, MVCS bases, adapter boundary).
- `magicwand-agent-creator` / `magicwand-agent-checker` — the recruiter Pair that authors new
  conforming agents.

## Note

This is the *last* goal we run through diecast for neoorg. The whole point is to give neoorg its
own backend + workforce so it can run its own goals after this.
