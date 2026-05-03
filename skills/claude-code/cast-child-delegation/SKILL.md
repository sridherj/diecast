---
name: cast-child-delegation
description: Comprehensive delegation mechanics for Diecast parent-child agent communication, dispatch, polling, status checks, failure handling, and context passing
---

# Diecast Child Delegation Skill

Complete reference for Diecast agent delegation: parent mechanics (dispatch, polling, status checks, failure handling, async patterns) and child mechanics (reading delegation context, writing output contracts).

> **Canonical specs.** This skill is the runtime encoding of two specs. If the skill and the specs ever diverge, the **specs are canonical** and this skill MUST be patched.
>
> - **Delegation runtime:** [`docs/specs/cast-delegation-contract.collab.md`](../../../docs/specs/cast-delegation-contract.collab.md) — file-based polling, backoff, idle timeout, heartbeat-by-mtime, atomic write, RUN_ID-scoped path validation, test hooks.
> - **Output JSON shape:** [`docs/specs/cast-output-json-contract.collab.md`](../../../docs/specs/cast-output-json-contract.collab.md) — contract-v2 field-by-field schema, allowed status set, artifacts[] item shape.

> **File is canonical.** The child's terminal output JSON file at `<goal_dir>/.agent-run_<RUN_ID>.output.json` is authoritative. cast-server is a read-through HTTP API — it observes the file but never writes it. This skill MUST never `import requests | httpx | urllib` from a Python implementation; bash-based curl is permitted only as a best-effort dispatch primitive. When `CAST_DISABLE_SERVER=1` is set, parents skip HTTP entirely and drive state from the file alone.

---

## PART A: Parent-Side Mechanics

Invoke this skill BEFORE dispatching any child agent. Follow the patterns for your specific use case.

### Section 0: Preflight (external_project_dir)

Every dispatch path on cast-server requires the goal to have a usable `external_project_dir`. The server enforces this at `POST /api/agents/{name}/trigger` and returns **HTTP 422** with `error_code: "missing_external_project_dir"` when it isn't set or the configured path doesn't exist on disk. Resolve it **before** dispatching so the user sees one clean prompt instead of a failed run.

**Check, prompt, set, then dispatch:**

```bash
# Step 1: GET the goal config
GOAL_JSON=$(curl -s "http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}/api/goals/$GOAL_SLUG")
EXT_DIR=$(echo "$GOAL_JSON" | jq -r '.external_project_dir // empty')

# Step 2: If unset or missing on disk, ask the user
NEEDS_PROMPT=false
if [ -z "$EXT_DIR" ]; then
  NEEDS_PROMPT=true
  REASON="not set"
elif [ ! -d "$EXT_DIR" ]; then
  NEEDS_PROMPT=true
  REASON="set to '$EXT_DIR' but that path does not exist"
fi

# Step 3: Resolve via AskUserQuestion (cast-interactive-questions protocol)
#   - Use Option A: current working directory ($PWD)
#   - Option B: user types another absolute path
#   - Option C: cancel
# (These options live in the AskUserQuestion call, not in bash. Bash code below
# runs after the user has chosen and `$NEW_EXT_DIR` is populated.)

# Step 4: Persist the choice
if [ -n "$NEW_EXT_DIR" ]; then
  curl -s -X PATCH "http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}/api/goals/$GOAL_SLUG/config" \
    -F "external_project_dir=$NEW_EXT_DIR" | jq '.status'
fi

# Step 5: Proceed with dispatch (Section 1).
```

**AskUserQuestion shape (canonical):**

> **Question #N: Set the goal's external project directory**
>
> The goal `<slug>` has no external_project_dir configured. Cast-server needs one before dispatching agents.
> *(or: configured to `<path>` but that path no longer exists on disk.)*
>
> - **Option A — Use current directory `<cwd>` (Recommended if cwd is the project root):** keeps the dispatch in the directory the user is operating from.
> - **Option B — Enter a different absolute path:** for goals tied to a project elsewhere on disk.
> - **Option C — Cancel dispatch:** stop and let the user fix it manually.

**Defense in depth — handle the 422 anyway:**

If a dispatch still returns `error_code: missing_external_project_dir` (race, server restart, scheduled run), fall back to the same prompt-and-PATCH flow, then retry the trigger **once**. Never silently retry without the prompt.

```bash
RESP=$(curl -s -w "\n%{http_code}" -X POST "http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}/api/agents/$AGENT/trigger" -H "Content-Type: application/json" -d "$BODY")
CODE=$(echo "$RESP" | tail -1)
BODY_JSON=$(echo "$RESP" | sed '$d')
if [ "$CODE" = "422" ] && [ "$(echo "$BODY_JSON" | jq -r '.error_code // empty')" = "missing_external_project_dir" ]; then
  # → run the Section 0 prompt-and-PATCH flow above, then retry once
  :
fi
```

---

### Section 1: Dispatch

Dispatch a child agent via HTTP. Replace placeholders with actual values.

**Basic trigger:**

```bash
CHILD_RUN_ID=$(curl -s -X POST http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}/api/agents/{agent-name}/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "goal_slug": "'"$GOAL_SLUG"'",
    "parent_run_id": "'"$PARENT_RUN_ID"'",
    "delegation_context": {
      "agent_name": "{agent-name}",
      "instructions": "What the child should do — be specific, include constraints",
      "context": {
        "goal_title": "...",
        "goal_phase": "...",
        "relevant_artifacts": ["list of relevant artifact paths from goal_dir"],
        "prior_output": "summary of your work so far if relevant",
        "constraints": ["do not delete files", "read-only run"]
      },
      "output": {
        "output_dir": "where the child should write artifacts",
        "expected_artifacts": ["artifact1.md", "artifact2.json"]
      }
    }
  }' | jq -r '.run_id')
```

**Key fields:**
- `goal_slug` (string): The goal this work belongs to. From your prompt preamble. Auto-injected into `delegation_context` if missing there.
- `parent_run_id` (string): Your run_id, injected in prompt preamble. Links delegation tree. Auto-injected into `delegation_context` if missing there.
- `delegation_context.agent_name` (string): The agent to invoke (e.g., "cast-detailed-plan").
- `delegation_context.instructions` (string): Detailed task description for the child. Include what success looks like.
- `delegation_context.context.relevant_artifacts` (array): List artifact paths relative to `goal_dir` that the child should read.
- `delegation_context.context.prior_output` (string): Summarize what you've done so far, so child understands context.
- `delegation_context.context.constraints` (array of strings): Any constraints on the work (e.g., ["do not modify existing configs"]).
- `delegation_context.context` also accepts **custom fields** (e.g., `phase_section`, `decisions_so_far`) — any extra keys are preserved and written to the delegation JSON file.
- `delegation_context.output.output_dir` (string, **optional**): Directory where child should write artifacts. Defaults to the goal directory (`<goals>/<goal_slug>`) when omitted — see `docs/specs/cast-delegation-contract.collab.md:66`. Pass `{output_dir}` from your preamble explicitly when you need a non-default location (e.g., a sub-phase under `docs/execution/<project>`).
- `delegation_context.output.expected_artifacts` (array): What you expect the child to produce (e.g., `["enrichment_result.json"]`).

**Tip:** Use `{output_dir}` and `{goal_dir}` from your prompt preamble — these are injected at runtime.

---

### Section 2: Poll with Timeout

> **DANGER — Never glob `*.output` in the tasks directory.**
> Claude Code writes each Bash task's stdout to a `.output` file in `/tmp/claude-*/tasks/`. If you glob `*.output` to inspect running tasks, you will read your own output file, write more content to stdout, which appends to the file, which gets read again — exponential feedback loop, 3.5GB+ files, system crash.
>
> **Wrong (causes crash):**
> ```bash
> for f in /tmp/claude-*/tasks/*.output; do echo "=== $(basename $f) ==="; tail -3 "$f"; done
> ```
> **Right — only reference specific known run IDs:**
> ```bash
> for RUN_ID in "${CHILD_RUN_IDS[@]}"; do
>   cat "{goal_dir}/.agent-$RUN_ID.output.json" | jq -c '{status, summary}'
> done
> ```

After dispatch, poll for the child's output file using a **3-tier system**. **Always use a timeout** — never infinite loops.

**Tier overview:**

| Tier | Interval | Check | Purpose |
|------|----------|-------|---------|
| Regular | 10s | Output file exists? | Fast completion detection |
| Deep | 60s | HTTP status + terminal hash | Detect stuck children early |
| Distress | After 5 no-progress deep polls | Desktop notification | Alert user without blocking |

```bash
TRACKING_DIR="$GOAL_DIR"  # or from delegation context output.tracking_dir
TIMEOUT=${TIMEOUT:-2700}   # Use per-agent value from your instructions
ELAPSED=0
DEEP_POLL_INTERVAL=60
NO_PROGRESS_COUNT=0
LAST_CONTENT_HASH=""

while [ $ELAPSED -lt $TIMEOUT ]; do
  # Layer-1: Regular polling (every 10s) — output file check
  if [ -f "$TRACKING_DIR/.agent-$CHILD_RUN_ID.output.json" ]; then
    break
  fi

  # Layer-2: Deep polling (every 60s) — HTTP status + progress detection
  if [ $((ELAPSED % DEEP_POLL_INTERVAL)) -eq 0 ] && [ $ELAPSED -gt 0 ]; then
    STATUS=$(curl -s "http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}/api/agents/jobs/$CHILD_RUN_ID" | jq -r '.status // empty')

    # If terminal state but file missing, break out
    if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
      echo "Child status is $STATUS but output file missing — treating as failed"
      break
    fi

    # Terminal content hash for progress detection
    CONTENT_HASH=$(tmux capture-pane -p -t "agent-$CHILD_RUN_ID" 2>/dev/null | md5sum | cut -d' ' -f1)

    if [ -n "$CONTENT_HASH" ] && [ "$CONTENT_HASH" = "$LAST_CONTENT_HASH" ]; then
      NO_PROGRESS_COUNT=$((NO_PROGRESS_COUNT + 1))
    else
      NO_PROGRESS_COUNT=0
      LAST_CONTENT_HASH="$CONTENT_HASH"
    fi

    # Layer-3: Distress notification (5+ consecutive no-progress = 5+ min stuck)
    if [ $NO_PROGRESS_COUNT -ge 5 ]; then
      if command -v notify-send >/dev/null 2>&1; then
        notify-send "Diecast: Child Agent Stuck" \
          "Agent $CHILD_RUN_ID no progress for $((NO_PROGRESS_COUNT * DEEP_POLL_INTERVAL / 60))min"
      fi
    fi

    echo "[$((ELAPSED / 60))m] Child status: $STATUS | no-progress streak: $NO_PROGRESS_COUNT"
  fi

  sleep 10
  ELAPSED=$((ELAPSED + 10))
done

if [ ! -f "$TRACKING_DIR/.agent-$CHILD_RUN_ID.output.json" ]; then
  echo "Child timed out after $TIMEOUT seconds"
  # Try Recovery Flow (Section 8) before killing and restarting
fi
```

**Timeout values by agent:**

| Agent | Timeout | Reason |
|-------|---------|--------|
| cast-task-suggester | 120s | Quick data lookup |
| cast-create-execution-plan | 1800s | Plan analysis + phase file creation |
| cast-subphase-runner | 2700s | Full sub-phase execution (up to 45 min) |
| cast-explore | 2400s | Research + playbook synthesis |
| cast-detailed-plan | 1800s | Multi-step plan generation |
| cast-web-researcher | 600s | Single angle research |

Use the timeout from your own agent instructions, not this table.

**Key rules:**
- `TRACKING_DIR` comes from delegation context `output.tracking_dir` (defaults to `GOAL_DIR`)
- Deep poll catches stuck children before timeout expires
- Distress notifications alert user without blocking the loop
- If `notify-send` unavailable, distress tier is silently skipped
- If tmux pane doesn't exist (child launched independently), hash comparison is skipped

**Tip:** If a child appears stuck (5+ no-progress), try the Recovery Flow (Section 8) before killing and restarting.

---

### Section 2b: File-Based Polling Loop (canonical)

The bash polling loop in Section 2 is a convenience wrapper over the canonical algorithm encoded below. Any non-bash parent (e.g., a Python orchestrator) MUST implement the algorithm in this section verbatim. The HTTP status check in Section 3 is best-effort augmentation; it MUST NOT be a precondition for terminal-state recognition.

This is the runtime encoding of `docs/specs/cast-delegation-contract.collab.md` — the spec is authoritative.

**Env-var contract** (from the spec's "Test Hooks" subsection):

| Variable | Default | Effect |
|----------|---------|--------|
| `CAST_DELEGATION_IDLE_TIMEOUT_SECONDS` | `300` | Idle timeout before parent returns synthetic `failed` with `human_action_needed=true`. |
| `CAST_DELEGATION_BACKOFF_OVERRIDE` | (unset → use `1,2,5,10,30`) | CSV polling ladder. Suffixes `ms`, `s` recognized; bare numbers default to seconds. Final value of CSV is steady-state. |
| `CAST_DISABLE_SERVER` | (unset) | When `1`, parent skips HTTP-API attempts; file path drives all state. |

**Pseudocode** (parent-side, post-dispatch):

```python
# Polling loop (executed by parent agent after dispatch)
backoff = parse_backoff_or_default(env.CAST_DELEGATION_BACKOFF_OVERRIDE, [1, 2, 5, 10, 30])
idle_timeout = int(env.CAST_DELEGATION_IDLE_TIMEOUT_SECONDS or 300)
output_path = f"{goal_dir}/.agent-run_{run_id}.output.json"
last_mtime = None
last_progress = time.now()
i = 0

while True:
    if exists(output_path):
        try:
            data = json.load(output_path)
        except JSONDecodeError as e:
            return {"status": "failed", "errors": [f"malformed child output: {e}"]}
        if data.status in {"completed", "partial", "failed"}:
            return data

        # Heartbeat: mtime changed → child still alive
        mtime = stat(output_path).mtime
        if mtime != last_mtime:
            last_mtime = mtime
            last_progress = time.now()

    if cancellation_requested():
        return {"status": "failed", "errors": ["cancelled"]}

    if time.now() - last_progress > idle_timeout:
        return {
            "status": "failed",
            "human_action_needed": True,
            "errors": [f"child idle for {idle_timeout}s; check {output_path}"]
        }

    sleep(backoff[min(i, len(backoff) - 1)])
    i += 1
```

**Heartbeat contract for long-running children.** A child that holds the run open for >150s without writing any progressive partial output MUST `os.utime`-touch the output file (or write a `status="running"`-equivalent partial JSON only as a last resort — note that `running` is a non-terminal value the parent will treat as malformed if it sees it, so prefer mtime touch). Default cadence: at least once per `idle_timeout / 2` seconds.

**Atomic write reminder.** Children write to `<output_path>.tmp` then `os.rename` to `<output_path>`. Parents never read `*.tmp`. See spec § Atomic Write Contract.

**RUN_ID scoping.** Parent reads only the exact `output_path` it constructed from its own dispatched RUN_ID. Never glob `*.output.json` — see Section 2's DANGER block.

---

### Section 3: HTTP Status Check

When the output file doesn't appear, check the child's status to understand what happened.

```bash
STATUS=$(curl -s "http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}/api/agents/jobs/$CHILD_RUN_ID" \
  | jq -r '.status // empty')

echo "Status: $STATUS"
```

**Status values:**

| Status | Meaning | Action |
|--------|---------|--------|
| `pending` | Child hasn't started yet | Wait longer, rerun polling loop |
| `running` | Child is working | Wait longer, rerun polling loop |
| `completed` | Child finished (see output file) | Read output.json, verify artifacts |
| `failed` | Child encountered an error | Read output.json for error details, decide stop vs continue |
| `idle` | Child waiting for human input | Check tmux pane (user must provide input), use `/continue` endpoint |
| (file missing, no response) | Server unreachable or run_id invalid | Check server health, verify run_id from dispatch response |

---

### Section 4: Failure Handling

Interpret the output.json and decide how to proceed.

**Read the output contract:**

```bash
cat "{goal_dir}/.agent-$CHILD_RUN_ID.output.json" | jq .
```

**Classify the result:**

```
status: "completed"
  → Artifacts produced successfully. Read {goal_dir}/.artifacts/* and verify against expected_artifacts.

status: "partial"
  → Some work done, not everything. Read summary and artifacts, decide:
    - Fix remaining work yourself? Or re-delegate with refined instructions?

status: "failed"
  → Child encountered an error. Read errors[] and summary.
    - Is this a blocking failure? (yes → stop execution, report to user)
    - Is this optional? (yes → note it, continue)

HTTP status "idle"
  → Child is paused waiting for human input. Do NOT auto-continue.
  → Notify user: "Child agent waiting for input in tmux pane. Address it before continuing."
  → If human provides input, use /continue endpoint (see Section 7)
```

**CRITICAL:** Always verify the work, not just the status:

1. Read actual artifacts the child produced (not just output.json summary)
2. Cross-reference against specs, requirements, and decisions you already have
3. Check for gaps, stale assumptions, or missed edge cases
4. If you find issues: fix yourself, re-delegate with refined instructions, or flag as open questions

---

### Section 5: Batch/Parallel Polling

When dispatching multiple children that can run in parallel, collect run_ids and poll them together.

```bash
# Dispatch multiple children, store run_ids
CHILD_RUN_IDS=()
for agent in cast-web-researcher cast-playbook-synthesizer; do
  RUN_ID=$(curl -s -X POST http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}/api/agents/$agent/trigger \
    -H "Content-Type: application/json" \
    -d '{"goal_slug":"...","parent_run_id":"...","delegation_context":{...}}' \
    | jq -r '.run_id')
  CHILD_RUN_IDS+=("$RUN_ID")
done

# Poll until all complete
declare -A statuses
for RUN_ID in "${CHILD_RUN_IDS[@]}"; do
  statuses[$RUN_ID]="pending"
done

TIMEOUT=2700; ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
  all_done=true
  for RUN_ID in "${!statuses[@]}"; do
    if [ "${statuses[$RUN_ID]}" != "done" ]; then
      if [ -f "{goal_dir}/.agent-$RUN_ID.output.json" ]; then
        statuses[$RUN_ID]="done"
      else
        all_done=false
      fi
    fi
  done

  # Show status every 30s
  if [ $((ELAPSED % 30)) -eq 0 ]; then
    echo "[$ELAPSED seconds] Status: $(declare -p statuses | tr '\n' ' ')"
  fi

  $all_done && break
  sleep 10
  ELAPSED=$((ELAPSED + 10))
done

# Process results
for RUN_ID in "${CHILD_RUN_IDS[@]}"; do
  echo "=== Result for $RUN_ID ==="
  cat "{goal_dir}/.agent-$RUN_ID.output.json" | jq -c '{status, summary}'
done
```

**Key pattern:**
- Dispatch all children → collect run_ids
- Poll all run_ids in a loop, storing status for each
- Show periodic status updates (every 30s or longer)
- Process results once all done

---

### Section 6: Async Overlap

Dispatch a child early, do independent work while it runs, then read the result later.

**Pattern:**

```bash
# Step 1: Dispatch child at START of phase
CHILD_RUN_ID=$(curl -s -X POST http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}/api/agents/cast-web-researcher/trigger ...)

# Step 2: Do independent work (phases N.1, N.2, N.3)
#         These steps don't depend on the child's output
echo "Working on phase N.1..."
echo "Working on phase N.2..."

# Step 3: Before step N.4 (which needs the child's research), read the child's result
while [ ! -f "{goal_dir}/.agent-$CHILD_RUN_ID.output.json" ]; do sleep 10; done
RESEARCH=$(cat "{goal_dir}/.agent-$CHILD_RUN_ID.output.json" | jq .artifacts[0].path)

# Step 4: Use child's output
echo "Research artifact: $RESEARCH"
```

**Benefit:** Overlaps I/O (child running) with local work (your steps), reducing total time.

**Use when:**
- Child work is independent of next N local steps
- Child likely to complete while you work (see timeout values in Section 2)
- Steps are ordered: dispatch → local work → read result

---

### Section 7: Continue vs. New Trigger

When a child is in `idle` state (waiting for input), decide whether to send input (continue) or start fresh (new trigger).

**Rule:**

| Situation | Action | Why |
|-----------|--------|-----|
| Child status is `idle` (waiting for user) | POST `/continue` → send message | Preserves context window, resumes session |
| Child status is `completed` or `failed` | POST `/trigger` → new agent | Previous run ended; need fresh session |
| You've never triggered before | POST `/trigger` | Always new for first trigger |

**Continue (send input to idle child):**

```bash
STATUS=$(curl -s "http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}/api/agents/jobs/$CHILD_RUN_ID" | jq -r '.status')

if [ "$STATUS" = "idle" ]; then
  # Child is waiting for input
  curl -s -X POST "http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}/api/agents/jobs/$CHILD_RUN_ID/continue" \
    -H "Content-Type: application/json" \
    -d '{
      "message": "User has decided to proceed with option A. Continue with sub-phases X, Y, Z."
    }'

  # Re-enter polling loop
  while [ ! -f "{goal_dir}/.agent-$CHILD_RUN_ID.output.json" ]; do sleep 10; done
fi
```

**New trigger (start fresh):**

```bash
NEW_RUN_ID=$(curl -s -X POST http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}/api/agents/cast-subphase-runner/trigger \
  -H "Content-Type: application/json" \
  -d '{"goal_slug":"...","parent_run_id":"...","delegation_context":{...}}' \
  | jq -r '.run_id')

# Poll the new run_id
while [ ! -f "{goal_dir}/.agent-$NEW_RUN_ID.output.json" ]; do sleep 10; done
```

---

### Terminal Resolution

When dispatching a child agent that spawns a new terminal tab, the dispatcher MUST resolve the terminal binary via `agents/_shared/terminal.py:resolve_terminal()`. Never hardcode a specific terminal binary in a cast-* agent or in cast-server.

**Env-var contract (resolution order):**

1. `$CAST_TERMINAL` — preferred. Project-scoped override.
2. `$TERMINAL` — POSIX convention.
3. `~/.cast/config.yaml:terminal_default` — written by `/cast-setup` on first run.
4. `ResolutionError` — raised when all three are empty.

**Usage:**

```python
from agents._shared.terminal import resolve_terminal, ResolutionError

try:
    term = resolve_terminal()
except ResolutionError as exc:
    # Surface the error to the user with the docs link from the message.
    # NEVER fall back to xterm or any "safe default" silently.
    raise SystemExit(str(exc))

# term.command, term.args, term.flags drive the spawn.
# Pass as a list — NEVER use shell=True.
subprocess.Popen([term.command, *term.args, *spawn_args])
```

If `resolve_terminal()` raises, surface the error to the user with the link to `docs/reference/supported-terminals.md` (already embedded in the error message). Do **not** fall back to a hardcoded terminal silently — that produces a confusing UX and hides the missing configuration.

**Security:** the resolved command is always passed as `args=[...]` to `subprocess.Popen`. NEVER use `shell=True` — both env vars and the config file are user-writable, and `shell=True` would expand them through the shell, opening an injection surface.

**First-run prompt:** `agents/_shared/terminal.needs_first_run_setup()` returns `True` when none of the three sources is set. The `/cast-setup` script (Phase 4) calls this helper to decide whether to prompt the user.

See `docs/reference/supported-terminals.md` for the per-terminal flag table, supported-platform notes, and contributor instructions for adding a new terminal.

---

## PART B: Child-Side Mechanics

When YOU are invoked as a child agent, follow these patterns to read parent context and write output back.

### Reading Delegation Context (as a Child)

When invoked as a child, a delegation context file exists in your goal_dir with instructions and context from the parent.

**At session start, read it:**

```bash
GOAL_DIR="{goal_dir}"    # injected in your prompt preamble
RUN_ID="{run_id}"        # your run_id from prompt preamble

DELEGATION_FILE="$GOAL_DIR/.delegation-$RUN_ID.json"
cat "$DELEGATION_FILE" | jq .
```

**File structure:**

```json
{
  "agent_name": "cast-web-researcher",
  "instructions": "Research 5 candidate frameworks with latest release info...",
  "context": {
    "goal_title": "Framework Selection",
    "goal_phase": "Phase 1: Discovery",
    "artifacts": [
      "docs/execution/my_plan/_shared_context.md",
      "candidates.json"
    ],
    "prior_output": "Already researched 3 candidates; need 2 more from the long-tail list.",
    "constraints": "Do not modify candidate names; only add release data."
  },
  "output": {
    "output_dir": "<DIECAST_ROOT>/docs/execution/my_plan",
    "expected_artifacts": ["research_result.json"]
  }
}
```

**Use the context fields:**
- `instructions` — what the parent wants you to do
- `context.artifacts` — files to read for context
- `context.prior_output` — what parent has done so far
- `context.constraints` — what NOT to do
- `output.output_dir` — where to write artifacts
- `output.expected_artifacts` — what parent expects back

---

### Writing Output Back (as a Child)

At the end of your work, write the standard output contract to `{goal_dir}/.agent-{run_id}.output.json`. This is how the parent knows you're done.

**Template:**

```json
{
  "contract_version": "2",
  "agent_name": "{agent_name}",
  "task_title": "{task_title}",
  "status": "completed | partial | failed",
  "summary": "One paragraph describing what you accomplished",
  "artifacts": [
    {
      "path": "relative/to/goal/dir/file.md",
      "type": "research|playbook|plan|code|data",
      "description": "What this file contains"
    }
  ],
  "errors": [],
  "next_steps": ["Suggested follow-up actions"],
  "human_action_needed": false,
  "human_action_items": [],
  "started_at": "2026-03-24T10:30:00Z",
  "completed_at": "2026-03-24T11:15:00Z"
}
```

**Status values:**
- `"completed"` — all requested work done successfully
- `"partial"` — some work done, but not everything (explain in summary)
- `"failed"` — could not accomplish the task (explain in errors[])

**human_action_needed:**
- `true` when: need approval, found data issues, open questions, need verification
- `false` when: work is complete and independent

**errors:**
- Empty array if successful
- List of error messages if failures occur (be specific)

**Example:**

```bash
cat > "{goal_dir}/.agent-{run_id}.output.json" << 'EOF'
{
  "contract_version": "2",
  "agent_name": "cast-web-researcher",
  "task_title": "Research candidate frameworks",
  "status": "completed",
  "summary": "Researched 5 frameworks and added release history (latest minor + major) for the last 2 years. All data current as of March 2026.",
  "artifacts": [
    {
      "path": "docs/execution/my_plan/research_result.json",
      "type": "data",
      "description": "5 frameworks with release_history array, latest_version, last_release_date"
    }
  ],
  "errors": [],
  "next_steps": ["Review release data for accuracy before selection"],
  "human_action_needed": false,
  "human_action_items": [],
  "started_at": "2026-03-24T10:30:00Z",
  "completed_at": "2026-03-24T11:15:00Z"
}
EOF
```

---

### Section 8: Recovery Flow (Before Restart)

When a child appears stuck (distress notification fired, or timeout expired), follow this 4-step recovery before killing and restarting. **Never kill and restart without attempting recovery first.**

```
Step 1: DIAGNOSE — Read the child's terminal to understand WHY it's stuck
Step 2: NUDGE   — If idle/waiting, send a continue message
Step 3: WAIT    — Give the nudge 60s to take effect
Step 4: RESTART — Only if nudge failed and situation is unrecoverable
```

**Step 1: Diagnose**

```bash
# Read child's terminal output
PANE_CONTENT=$(tmux capture-pane -p -t "agent-$CHILD_RUN_ID" 2>/dev/null | tail -30)
echo "$PANE_CONTENT"

# Also check HTTP status
STATUS=$(curl -s "http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}/api/agents/jobs/$CHILD_RUN_ID" | jq -r '.status // empty')
echo "HTTP status: $STATUS"
```

Interpret what you see:
- **Permission prompt** (y/n, allow/deny) → Child needs user input. Nudge with approval.
- **Waiting for input** (blank prompt, `>`) → Child is idle. Nudge with continuation message.
- **Error loop** (same error repeated) → Child is stuck in a retry loop. Restart with refined instructions.
- **Active work** (tool calls, file reads) → Child is just slow. Extend timeout.

**Step 2: Nudge (if idle/waiting)**

```bash
# Option A: Send continuation via HTTP (preferred — uses Diecast continue endpoint)
if [ "$STATUS" = "idle" ]; then
  curl -s -X POST "http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}/api/agents/jobs/$CHILD_RUN_ID/continue" \
    -H "Content-Type: application/json" \
    -d '{"message": "Continue with the task. Do not wait for user input unless absolutely necessary."}'
fi

# Option B: Send keys directly to tmux pane (fallback)
tmux send-keys -t "agent-$CHILD_RUN_ID" "Continue with the task. Do not wait for user input." Enter
```

**Step 3: Wait for effect (60s)**

```bash
sleep 60
NEW_HASH=$(tmux capture-pane -p -t "agent-$CHILD_RUN_ID" 2>/dev/null | md5sum | cut -d' ' -f1)
if [ "$NEW_HASH" != "$LAST_CONTENT_HASH" ]; then
  echo "Nudge worked — child is progressing again"
  # Resume normal polling loop (Section 2)
else
  echo "Nudge had no effect — proceeding to restart"
fi
```

**Step 4: Restart (last resort only)**

```bash
# Cancel the stuck run
curl -s -X POST "http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}/api/agents/runs/$CHILD_RUN_ID/cancel"

# Re-dispatch with refined instructions that address the stuck reason
NEW_RUN_ID=$(curl -s -X POST http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}/api/agents/{agent-name}/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "goal_slug": "'"$GOAL_SLUG"'",
    "parent_run_id": "'"$PARENT_RUN_ID"'",
    "delegation_context": {
      "instructions": "REFINED: Previous attempt got stuck because [reason]. This time: [specific guidance to avoid the issue].",
      "context": {
        "error_memories": ["Previous run stuck at [description]. Avoid [pattern]."],
        ...
      }
    }
  }' | jq -r '.run_id')

# Update tracking to use new run_id
CHILD_RUN_ID="$NEW_RUN_ID"
# Resume polling (Section 2)
```

**Key rules:**
- Steps 1-3 are mandatory before Step 4
- Never auto-continue interactive agents (those with `interactive: true` in config)
- Include `error_memories` in retry context so child doesn't repeat the same mistake
- If restart also fails, escalate to user — do not retry indefinitely

---

## Checklists

### Before Dispatching a Child

- [ ] Diecast cast-server is running (`curl -s http://${CAST_HOST:-localhost}:${CAST_PORT:-8005}/api/agents/runs?status=running | head -1`)
- [ ] Child agent exists in registry (check `/agents/*/config.yaml`)
- [ ] Instructions are specific and include success criteria
- [ ] Context artifacts are relevant and paths are correct (relative to goal_dir)
- [ ] output_dir is set correctly (usually `{output_dir}` from preamble)
- [ ] expected_artifacts lists what you actually need back
- [ ] Parent config.yaml lists this child in allowed_delegations
- [ ] Timeout value is appropriate for the agent (see Section 2 table)

### While Polling

- [ ] Using timeout-bounded loop (never infinite)
- [ ] Sleeping 10s between checks (don't hammer server)
- [ ] Using `$TRACKING_DIR` (not hardcoded `$GOAL_DIR`) for output file path
- [ ] Deep polling active (HTTP status + terminal hash every 60s)
- [ ] Distress notification fires after 5+ no-progress deep polls
- [ ] Have a fallback if output file never appears (HTTP status check)
- [ ] Showing periodic status updates to user (every 30s+ for long operations)
- [ ] Recovery flow (Section 8) attempted before killing stuck children

### After Receiving Output

- [ ] Read output.json contract, verify status field
- [ ] Read actual artifacts (don't just trust the status)
- [ ] Cross-reference against specs, requirements, decisions
- [ ] Check for gaps or stale assumptions
- [ ] Decide: accept, fix yourself, re-delegate, or escalate
- [ ] Never relay child's "completed" without verifying yourself

---

## Troubleshooting

| Problem | Diagnosis | Fix |
|---------|-----------|-----|
| Output file never appears | Dispatch failed, child never started, or timed out | Check HTTP status (Section 3), check server logs |
| `"curl: command not found"` in output | Child attempted dispatch without bash | Ensure child agent has bash available (not Python-only) |
| `jq: command not found"` | JSON parsing failed | Check if jq is available in agent environment |
| Child status is `idle` but you expected `completed` | Child waiting for user input | Check tmux pane for user prompt, use `/continue` endpoint |
| Child output.json has `"status": "partial"` | Child did some work but not all | Read summary and artifacts, decide re-delegate or fix yourself |
| Timeout expired, file still missing | Child crashed, network issue, or time budget exceeded | Check HTTP status, check server for error logs, consider longer timeout |

