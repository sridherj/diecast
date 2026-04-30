# Delegation pattern

In Diecast, parent agents wait for children **via files, not RPC**. A
parent dispatches a child by writing a prompt file, then polls a
deterministic output-JSON path until the child terminates. The
cast-server can be running, or stopped, or restarted mid-run — the
contract holds either way. This page documents the contract, the
polling cadence, the timeout behavior, and the escape hatch a child
uses when something needs human attention.

## Why files, not RPC

The file-based contract is the single biggest reliability decision in
Diecast. Three concrete payoffs:

- **Server-stopped resilience.** Children are full Claude Code
  sessions. They keep running even when cast-server is not. A parent
  that polls a file does not care whether the server is up; it cares
  whether the file exists yet.
- **Restart-tolerant.** Crash the parent, crash the server, restart
  the laptop — the child keeps writing toward the same output path.
  When the parent comes back up, it polls again and picks up where
  it left off.
- **Trivially debuggable.** When a delegation behaves strangely, the
  forensic surface is two files: the `.prompt` and the
  `.output.json`. Both are plain text. No log spelunking, no
  in-memory tracing.

The cast-server gives a richer experience — a web UI at
`http://localhost:8000`, the HTTP API for dispatch state, the
rate-limit auto-restart loop. But it is a read-through over the
file-based truth. Removing the server does not remove the
delegation.

## The contract

### `.agent-run_<RUN_ID>.prompt`

The parent writes this file to dispatch a child. Path convention:

```
<goal_dir>/.agent-run_<RUN_ID>.prompt
```

The file is plain markdown. The parent encodes:

- Which agent the child should be (`taskos-subphase-runner`,
  `cast-detailed-plan`, etc.).
- Where to find the delegation context (typically a sibling
  `.delegation-run_<RUN_ID>.json` with structured fields).
- Where to write the output JSON when finished.
- Any constraints — "unattended, do not pause for human input,"
  "skip-compliance-checker," etc.

The parent does not specify the child's model, temperature, or tools.
Those are owned by the child agent's own definition.

### `.agent-run_<RUN_ID>.output.json`

The child writes this file as its **last action**. Schema sketch:

```json
{
  "contract_version": "2",
  "agent_name": "taskos-subphase-runner",
  "task_title": "Phase 6.2: docs/ set authorship",
  "status": "completed | partial | failed",
  "summary": "One paragraph describing what was accomplished",
  "artifacts": [
    {
      "path": "docs/thesis.md",
      "type": "research|playbook|plan|code|data",
      "description": "Launch blog post outline"
    }
  ],
  "errors": [],
  "next_steps": ["Run sp3 to record GIFs"],
  "human_action_needed": false,
  "human_action_items": [],
  "started_at": "2026-04-30T06:10:41Z",
  "completed_at": "2026-04-30T06:32:18Z"
}
```

Field semantics:

- `contract_version` — bumped when the schema changes
  incompatibly. v1.0 ships `"2"`. Parents check the version before
  parsing.
- `status` — the only allowed values are `completed`, `partial`,
  `failed`. `partial` means some work shipped; `summary` and
  `errors` together must explain what is missing.
- `next_steps` — strings. Not command objects, not nested dicts.
  Each entry is one suggested follow-up the parent (or a human)
  could take.
- `human_action_needed` — the escape hatch. See below.
- `started_at` / `completed_at` — ISO-8601 with timezone. The
  child writes both itself.

The output file is the **single source of truth** for whether the
delegation succeeded. The parent does not ask cast-server, does not
re-prompt the child, does not infer status from file mtimes — it
reads the JSON.

## Polling backoff

The parent polls the output JSON path on an exponential cadence:

```
poll wait #1: 1s
poll wait #2: 2s
poll wait #3: 5s
poll wait #4: 10s
poll wait #5+: 30s
```

Rationale: most cast-* agents finish their first heartbeat in seconds
(skill load, context read), so the first two polls are tight. Real
work then takes minutes — the cadence relaxes to 30s steady-state so
a long child does not generate hundreds of useless filesystem reads.

The polling loop is **side-effect-free until the file appears**. The
parent reads, sleeps, reads, sleeps. No locks. No partial-write
races — children write atomically (write-temp + rename).

## The 5-minute idle timeout

A child is considered *idle* if its terminal session has not produced
new tool calls or text output for **5 minutes**. The dispatcher (when
running) treats idle children as candidates for cancellation. Without
the dispatcher, the parent's own polling loop can apply the same
heuristic — but typically does not, because the absence of an output
JSON is the only signal the parent needs.

If a child legitimately needs more than 5 idle minutes (long-running
download, blocked on external API), it should heartbeat by writing
status updates to the same output JSON with `status: "partial"` and
keep going. Once the long step completes, the child overwrites the
JSON with the final `status: "completed"`.

## The `human_action_needed` escape hatch

A child sets `human_action_needed: true` when:

- It needs human approval before changes take effect.
- It found data issues that must be manually corrected.
- It has open questions that block completion (and the dispatch
  was attended).
- It completed the work but something needs human verification
  (e.g., "GIF #3 recorded but voice-pass-leak suspected — review
  before commit").

When the child sets the flag, it MUST also populate
`human_action_items` with specific, actionable strings — what
exactly the human should do.

The parent reacts by:

- Surfacing the `human_action_items` to whoever invoked the chain.
- **Not auto-retrying.** A flagged child is one whose output is
  intentional, not a transient failure.
- Optionally writing a follow-up `.continue` message back to the
  child once the human has resolved the issue.

The flag is what keeps the parent-child contract honest. Without it,
children either silently swallow ambiguity or fail loudly when they
should have asked. With it, the chain has a clean third option.

## Worked example

The walkthrough below traces what happens when a parent dispatches
`taskos-subphase-runner` to execute Phase 6 sp2 of the Diecast OSS
plan. The cast-server is **stopped** — the example is the file
contract proving itself.

<!-- GIF #3 embedded in sp3 - placeholder retained for that sub-phase to fill in -->

The flow the GIF will show:

1. The parent writes `.agent-run_<RUN_ID>.prompt` and
   `.delegation-run_<RUN_ID>.json` into the goal directory.
2. The parent kicks off a fresh Claude Code terminal pointed at
   the prompt file.
3. The parent polls the output JSON path on the 1s/2s/5s/10s/30s
   cadence. cast-server is not running — `curl
   http://localhost:8000` would return connection refused.
4. The child runs to completion in its own terminal, writes
   markdown artifacts, and finally writes
   `.agent-run_<RUN_ID>.output.json` atomically.
5. The parent's next poll sees the file, reads
   `status: "completed"`, parses the artifacts list, and continues
   the chain.

The point of the demonstration: the server's absence is a
non-event. The contract is the file. The agent ran. The parent woke
up and read the result.
