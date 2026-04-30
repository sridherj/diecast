# Multi-harness future state

> **Status:** intent, not capability. Diecast v1.0.0 ships Claude-only.
> Cross-harness adapters ship only when a non-Claude user asks unprompted.

The cast-* workflow chain is harness-agnostic in shape: parent agents
dispatch children, children read prompts and write output JSON, and
every step is a markdown artifact on disk. None of that is unique to
Claude Code. In principle, the same chain could run on Codex, on
Copilot agent mode, or on any future agent harness that supports
named-agent dispatch.

In practice, v1.0.0 is Claude-only. This page documents the future
state and — more importantly — why the project has not opened the
door yet.

## The AGENTS.md plan

Cross-harness portability would land as an **AGENTS.md** convention:
a top-level file in the cast-* repo that other harnesses can read to
discover which agents exist, what each one expects as input, and
where the prompt body lives.

A rough sketch of the convention:

```markdown
# AGENTS.md

## cast-refine
- entrypoint: agents/cast-refine/cast-refine.md
- input: requirements.human.md
- output: refined_requirements.collab.md
- harness: claude-code | codex | copilot

## cast-high-level-planner
- entrypoint: agents/cast-high-level-planner/cast-high-level-planner.md
- ...
```

Each harness would need a small adapter that reads AGENTS.md, loads
the entrypoint prompt, and forwards tool calls. The bulk of the work
is on the harness side; the cast-* agents themselves change very
little.

## Why we don't ship adapters at v1

Four reasons, in priority order:

1. **No demand pull yet.** No non-Claude user has asked for it. v1
   ships when the project finds its actual users; building for
   imagined users wastes runway.
2. **Harness APIs are unstable.** Codex's tool-use surface and
   Copilot's agent mode are both shifting month-over-month. An
   adapter built today is broken next quarter; a convention
   stabilized later costs less to retrofit.
3. **Testing matrix grows quadratically.** Three harnesses × ~14
   cast-* agents × five contract versions is a maintenance burden a
   one-maintainer project will not survive. Adding the second
   harness should follow real users, not speculation.
4. **The v1 wedge is "Claude users with workflow pain."** That is
   one community, with one harness, asking one shape of question.
   Adding harness diversity dilutes the wedge before it has cut.

## What would change our minds

The bar for shipping cross-harness adapters is concrete and
deliberately public:

- **A real Codex or Copilot user opens an issue asking** —
  unprompted, with a specific use case. Not a suggestion in passing,
  not a "would be cool if." A user who would adopt Diecast on their
  preferred harness today if the adapter existed.
- **The AGENTS.md convention stabilizes upstream.** If the broader
  ecosystem converges on a shape, Diecast adopts it; if everyone
  ships their own, Diecast waits.
- **Harness API gaps close.** Today, parent-child file contracts are
  trivial in Claude Code (terminal session per child) and awkward in
  the alternatives. When the gap closes, the cost of supporting a
  second harness drops below the cost of avoiding it.

When two of those three are true, the work moves from "future state"
to a v1.x or v2.x line item on the [roadmap](./roadmap.md). Until
then, this page is the honest answer to the question.
