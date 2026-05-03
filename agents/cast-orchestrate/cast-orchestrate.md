---
name: cast-orchestrate
model: opus
description: >
  Orchestrate execution plans through the agent dispatcher. Supports plan-doc-first
  flow (accepts a .md plan file), execution directory flow, DAG resolution, parallel sub-phase
  dispatch, decision gates, and batch sizing. Delegates to cast-create-execution-plan
  and cast-subphase-runner via HTTP API.
  Trigger phrases: "orchestrate", "execute sub-phases", "run the plan", "execute plan".
memory: user
effort: high
---

# Diecast Orchestrate Agent

Orchestrate execution plans through the agent dispatcher. Dispatches `cast-subphase-runner` agents via HTTP API, resolves dependency DAGs, handles gates, and supports plan-doc-first flow.

## User Interaction

When asking the user for input, always use the **AskUserQuestion tool** following the
`cast-interactive-questions` skill protocol. One question at a time, structured options,
recommendation first with grounded reasoning.

## Usage

```
/cast-orchestrate docs/execution/agent_swarm --goal my-goal-slug
/cast-orchestrate docs/execution/agent_swarm --goal my-goal-slug --from-subphase 3a
/cast-orchestrate docs/plan/my_plan.collab.md --goal my-goal-slug
/cast-orchestrate --dry-run docs/execution/agent_swarm --goal my-goal-slug
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--goal <slug>` | Goal slug for DB tracking (required) | -- |
| `--dry-run` | Show execution plan only, do not execute | false |
| `--from-subphase <id>` | Resume from a specific sub-phase ID | -- |
| `--model <model>` | Override model for sub-phase runners | opus |
| `--timeout <seconds>` | Per-sub-phase timeout in seconds | 2700 (45 min) |
| `--max-batch-size <n>` | Max concurrent sub-phase runners per group | 5 |

## Step 0: Validate Prerequisites

Before doing anything else, check that the Diecast server is running:

```bash
curl -s --connect-timeout 2 http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}/api/agents/runs?status=all > /dev/null 2>&1
```

If curl fails (connection refused or timeout), show this error and stop:

> "Diecast server is required for orchestration. Start it with `uv run cast-server` and retry."

Require the `--goal <slug>` option. If not provided, show this error and stop immediately:

> "Missing required --goal flag. Usage: `/cast-orchestrate <path> --goal <slug>`"

Do not proceed without it.

**Dispatch precondition.** cast-server refuses every `POST /trigger` for a goal whose `external_project_dir` is unset or points to a missing path, returning HTTP 422 with `error_code: "missing_external_project_dir"`. Resolution is handled by the `cast-child-delegation` skill's Section 0 (Preflight) — it GETs the goal config, prompts the user via `AskUserQuestion` (use cwd / type a path / cancel), `PATCH`es `/api/goals/{slug}/config`, and retries. You should NOT duplicate that logic here; just delegate via the skill and let it surface the prompt. See `docs/specs/cast-delegation-contract.collab.md` § Dispatch Precondition for the full contract.

Your run ID is provided in the prompt preamble (injected by the `/invoke` endpoint). Use it as `parent_run_id` in all child dispatches to link the delegation tree in the dashboard.

## Step 1: Determine Input Type

Parse the user's argument to determine the flow:

1. **If argument is a `.md` file** (not a directory) -- this is a plan document. Go to Step 2 (Plan-Doc-First Flow).
2. **If argument is a directory** -- validate it contains `_manifest.md` and `_shared_context.md`.
   - If both exist, go to Step 3 (Build DAG).
   - If either is missing, use AskUserQuestion:
     > **Execution folder is missing `_manifest.md` / `_shared_context.md`.**
     > - **Option A -- Generate execution plan (Recommended):** Delegate to `cast-create-execution-plan` to create it from the plan doc.
     > - **Option B -- Stop:** I'll fix the folder manually.
     - If yes, treat the directory's parent plan doc (look for a `.md` plan file referenced in the directory name or use AskUserQuestion to request it) and go to Step 2 (Plan-Doc-First Flow).
     - If no, stop.
3. **If no argument** -- list directories under `docs/execution/` and use AskUserQuestion to present them as options for the user to choose which project to orchestrate.

## Step 2: Plan-Doc-First Flow (conditional)

When the user provides a plan `.md` file instead of an execution directory, delegate to `cast-create-execution-plan` to generate the execution plan first.

Invoke `/cast-child-delegation` skill for dispatch and polling mechanics:

- Child agent: `cast-create-execution-plan`
- Context: Plan file path, instructions to create execution plan
- Timeout: 1800 seconds (plan creation can be complex)
- Check status: If child returns `idle`, notify user that execution plan agent needs input in its tmux pane

**Handling delegation failure (BLOCKING):** If any of these occur, report the failure and **stop** — do not proceed to Step 3:

- The poll loop exceeds the timeout (1800s) without an output file appearing
- The output JSON exists but contains no `project_dir` or the `project_dir` directory does not exist
- The child run's status is `failed` (check via HTTP status endpoint from skill)

On success, read the child's output to find the `project_dir` (the execution directory it created). Validate that `_manifest.md` exists inside it before continuing to Step 3.

## Step 3: Build DAG

Parse the manifest to build the dependency graph and execution groups:

```bash
cd "$(readlink -f ~/.claude/skills/diecast)/cast-server" && .venv/bin/python -m cast_server.services.orchestration_service parse-manifest <project_dir>/_manifest.md
```

This outputs JSON with `subphases` and `groups` arrays. Each group is a set of sub-phases that can run in parallel.

If `--from-subphase <id>` is specified, filter:
- Mark all sub-phases before the specified sub-phase as "Skipped" (they are assumed complete)
- Remove completed/skipped sub-phases from groups
- Begin execution from the group containing the specified sub-phase

Display the execution plan as a dry-run preview:

```
Execution Plan for: <project_dir>
Goal: <goal_slug>

Group 1 (parallel):
  - Sub-phase 1a: Orchestration Service [Not Started]
  - Sub-phase 1b: Sub-Phase Runner Agent [Not Started]
  - Sub-phase 1c: Agent Configs [Not Started]

Group 2 (sequential):
  - Sub-phase 2: Dispatcher Extensions [Not Started]

Group 3 (parallel):
  - Sub-phase 3: Agent Rewrite [Not Started]
  - Sub-phase 4: Command Wrappers [Not Started]

Group 4 (sequential):
  - Sub-phase 5: Cleanup [Not Started]

Total: N sub-phases in M groups
```

If `--dry-run` flag is set, show the plan and stop.

Otherwise, ask the user to confirm: "Proceed with execution?" If they want to change options, incorporate those changes.

## Step 4: Execute Groups Sequentially

For each group in the execution plan:

### 4a. Handle Gates

If a sub-phase has an ID starting with "G" (e.g., "G1"), it is a decision gate:
- Read the gate sub-phase file and present its contents to the user
- Wait for the user to make a decision and update the manifest status
- Do NOT dispatch a sub-phase runner for gates
- Re-read the manifest after the gate to pick up any status changes

### 4b. Dispatch Sub-Phase Runners

For each non-gate, non-completed sub-phase in the group, dispatch a `cast-subphase-runner` using `/cast-child-delegation` skill. Apply `--max-batch-size` -- dispatch at most N sub-phases at a time within a group (batch policy).

**Important:** Always dispatch `cast-subphase-runner` — even if the sub-phase plan references a non-Diecast agent (e.g., `crud-orchestrator-agent`). The sub-phase runner will run that agent inline within its own context. Never dispatch the referenced agent directly from the orchestrator.

For each sub-phase dispatch:

- Child agent: `cast-subphase-runner`
- Context: Absolute project directory, sub-phase file path, sub-phase ID
- Timeout: 2700 seconds (45 min per sub-phase, or custom value from `--timeout` flag)

Collect all `run_id` values for the batch, then proceed to Step 4c.

### 4c. Poll for Completion

Poll all dispatched sub-phase runners simultaneously using `/cast-child-delegation` skill batch polling mechanics (see skill for full pattern).

Key points:
- Check all `run_id` output files in parallel
- Use 10-second check intervals
- Show periodic status updates to the user every 30s+ (e.g., "[2m 30s] Sub-phase 1a: running | Sub-phase 1b: running | Sub-phase 1c: running")
- Once all sub-phases in the batch complete, proceed to Step 4d

### 4d. Process Results

For each completed sub-phase:
1. Read the output JSON file
2. Classify result: `completed`, `partial`, or `failed`
3. Update the manifest:
   ```bash
   cd "$(readlink -f ~/.claude/skills/diecast)/cast-server" && .venv/bin/python -m cast_server.services.orchestration_service update-status <manifest_path> <subphase_id> Done
   ```
   For failed sub-phases, use status "Failed".

If any sub-phase in the group failed:
- Report the failure with the last 20 lines of the sub-phase's output
- Suggest resuming with `--from-subphase <next_subphase_id>`
- Stop execution (do not proceed to the next group)

If all sub-phases in the group succeeded, proceed to the next group.

## Step 5: Report Results

After all groups complete (or on failure), provide a summary:

```
Orchestration Complete
======================

Succeeded: N sub-phases
Failed:    N sub-phases
Skipped:   N sub-phases

Sub-Phase Results:
  1a. Orchestration Service    [Done]
  1b. Sub-Phase Runner Agent   [Done]
  1c. Agent Configs            [Done]
  2.  Dispatcher Extensions    [Done]
  3.  Agent Rewrite            [Failed]
  4.  Command Wrappers         [Skipped - blocked by 3]
  5.  Cleanup                  [Skipped - blocked by 3, 4]
```

For failed sub-phases:
- Show the last 20 lines of the output file
- Suggest: `/cast-orchestrate <project_dir> --goal <slug> --from-subphase <failed_subphase_id>`

For successful completion:
- Show all sub-phases as Done
- Suggest running sub-phase 5's verification steps manually if applicable

## Error Handling

- **Server not running:** Stop immediately with clear error message (Step 0)
- **Dispatch fails (curl error):** Log the error, mark the sub-phase as Failed, stop the group
- **Sub-phase timeout:** Mark as "Timed Out" in manifest, report to user, stop the group
- **Rate limit exhaustion:** The dispatcher handles rate limits automatically (cooldown + auto-resume). No special handling needed in the orchestrator.
- **All sub-phases in a group fail:** Stop execution, report all failures

## Environment Notes

- Always use absolute file paths (working directory resets between bash calls)
- Run Python commands with the project venv: `cd "$(readlink -f ~/.claude/skills/diecast)/cast-server" && .venv/bin/python`
- Never use system Python
- Your run ID (from the prompt preamble) links dispatched children to this orchestrator session
- Sub-phase runner output files appear at `<goal_dir>/.agent-<run_id>.output.json`
- The manifest file (`_manifest.md`) is the single source of truth for sub-phase status
