---
name: cast-runs
description: >
  Create, list, update, and manage Diecast agent runs via service layer.
  Trigger phrases: "list runs", "show run", "cancel run", "complete run",
  "run status", "recheck run", "show child runs", "run CRUD".
memory: user
effort: medium
---

# Diecast Runs — Service Layer Reference

Manage Diecast agent runs directly via `uv run python -c` commands from the `diecast/` directory.

> **ERROR HANDLING:** If any `uv run python -c` command fails (import error, service exception, DB error, etc.), **STOP immediately** and tell the user: "Human intervention required: [error details]". Do NOT attempt to fix, retry, or work around the issue.

## Environment

All commands must set PYTHONPATH to resolve the diecast package:

```bash
PYTHONPATH=$(readlink -f ~/.claude/skills/diecast)/cast-server/src uv run python -c "..."
```

## Operations

### List Runs for a Goal

```bash
PYTHONPATH=$(readlink -f ~/.claude/skills/diecast)/cast-server/src uv run python -c "
from diecast.services.run_service import get_runs_for_goal
import json
runs = get_runs_for_goal('GOAL_SLUG')
for r in runs:
    print(f'[{r[\"run_id\"]}] {r[\"status\"]:12s} {r[\"agent_name\"]:30s} {r[\"started_at\"]}')
    for child in r.get('children', []):
        print(f'    [{child[\"run_id\"]}] {child[\"status\"]:12s} {child[\"agent_name\"]}')
"
```

### List Runs Filtered by Status

```bash
PYTHONPATH=$(readlink -f ~/.claude/skills/diecast)/cast-server/src uv run python -c "
from diecast.services.run_service import get_runs_for_goal
runs = get_runs_for_goal('GOAL_SLUG', status='running')
for r in runs:
    print(f'[{r[\"run_id\"]}] {r[\"status\"]:12s} {r[\"agent_name\"]}')
"
```

### Get a Single Run

```bash
PYTHONPATH=$(readlink -f ~/.claude/skills/diecast)/cast-server/src uv run python -c "
from diecast.services.run_service import get_run
import json
r = get_run('RUN_ID')
print(json.dumps(r, indent=2, default=str))
"
```

### Create a Run

```bash
PYTHONPATH=$(readlink -f ~/.claude/skills/diecast)/cast-server/src uv run python -c "
from diecast.services.run_service import create_run
import json
r = create_run(
    agent_name='cast-web-researcher',
    goal_slug='GOAL_SLUG',
    parent_run_id=None,
    task_id=None,
    instructions='What this run should do',
    context={'phase': 'exploration'},
)
print(json.dumps(r, indent=2, default=str))
"
```

All parameters except `agent_name` and `goal_slug` are optional.

### Create a Child Run

```bash
PYTHONPATH=$(readlink -f ~/.claude/skills/diecast)/cast-server/src uv run python -c "
from diecast.services.run_service import create_run
import json
r = create_run(
    agent_name='cast-web-researcher',
    goal_slug='GOAL_SLUG',
    parent_run_id='PARENT_RUN_ID',
    instructions='Sub-task instructions',
)
print(json.dumps(r, indent=2, default=str))
"
```

Children inherit goal context from the parent run.

### List Child Runs

```bash
PYTHONPATH=$(readlink -f ~/.claude/skills/diecast)/cast-server/src uv run python -c "
from diecast.services.run_service import get_child_runs
for r in get_child_runs('PARENT_RUN_ID'):
    print(f'[{r[\"run_id\"]}] {r[\"status\"]:12s} {r[\"agent_name\"]}')
"
```

### Change Run Status

```bash
PYTHONPATH=$(readlink -f ~/.claude/skills/diecast)/cast-server/src uv run python -c "
from diecast.services.run_service import update_run_status
import json
r = update_run_status('RUN_ID', 'running')
print(json.dumps(r, indent=2, default=str))
"
```

### Complete a Run (with output)

```bash
PYTHONPATH=$(readlink -f ~/.claude/skills/diecast)/cast-server/src uv run python -c "
from diecast.services.run_service import complete_run
import json
r = complete_run(
    'RUN_ID',
    output_path='goals/GOAL_SLUG/run-output.json',
    summary='What this run accomplished',
)
print(json.dumps(r, indent=2, default=str))
"
```

### Fail a Run (with error)

```bash
PYTHONPATH=$(readlink -f ~/.claude/skills/diecast)/cast-server/src uv run python -c "
from diecast.services.run_service import fail_run
import json
r = fail_run('RUN_ID', error='Stack trace or message describing the failure')
print(json.dumps(r, indent=2, default=str))
"
```

### Cancel a Run

```bash
PYTHONPATH=$(readlink -f ~/.claude/skills/diecast)/cast-server/src uv run python -c "
from diecast.services.run_service import cancel_run
import json
r = cancel_run('RUN_ID')
print(json.dumps(r, indent=2, default=str))
"
```

### Recheck a Completed/Failed Run

```bash
PYTHONPATH=$(readlink -f ~/.claude/skills/diecast)/cast-server/src uv run python -c "
from diecast.services.run_service import recheck_run
import json
r = recheck_run('RUN_ID')
print(json.dumps(r, indent=2, default=str))
"
```

### Delete a Terminal Run

```bash
PYTHONPATH=$(readlink -f ~/.claude/skills/diecast)/cast-server/src uv run python -c "
from diecast.services.run_service import delete_run
delete_run('RUN_ID')
print('Deleted')
"
```

Only runs in a terminal status (`completed`, `failed`, `cancelled`) may be deleted.

## Run Schema

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | Stable identifier, e.g., `run_20260429_231041_e737a7` |
| `parent_run_id` | string \| null | Parent run that spawned this child (null for top-level runs) |
| `agent_name` | string | Agent that owns this run, e.g., `cast-subphase-runner` |
| `goal_slug` | string | Goal this run belongs to |
| `task_id` | int \| null | Optional task this run is executing |
| `status` | enum | See valid values below |
| `started_at` | timestamp | ISO 8601 UTC timestamp when the run was dispatched |
| `completed_at` | timestamp \| null | ISO 8601 UTC timestamp when the run reached a terminal state |
| `error` | string \| null | Error message if `status == failed` |

## Valid Enum Values

| Field | Values |
|-------|--------|
| `status` | `pending`, `running`, `idle`, `completed`, `failed`, `cancelled` |

## Constraints
- `run_id` is immutable after creation
- `parent_run_id` cannot be changed after creation (lineage is fixed)
- Only terminal runs (`completed`, `failed`, `cancelled`) may be deleted
- `complete_run`, `fail_run`, and `cancel_run` set `completed_at` automatically
- `error` is only meaningful when `status == failed`
- Child runs are auto-cancelled when their parent is cancelled
