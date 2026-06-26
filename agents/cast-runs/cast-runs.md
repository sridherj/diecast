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

All commands set `PYTHONPATH` to resolve the `cast_server` package **and** pass
`uv run --directory <repo-root>` so the right project environment is used no
matter what the current working directory is (without `--directory`, `uv run`
resolves the venv from the caller's cwd and fails with `ModuleNotFoundError`
when invoked from outside the repo):

```bash
PYTHONPATH=$(cd ~/.claude/skills/diecast && pwd -P)/cast-server uv run --directory "$(cd ~/.claude/skills/diecast && pwd -P)" python -c "..."
```

Run functions live in `cast_server.services.agent_service`. The run dict uses
`id` for the run identifier and `error_message` for the failure string.

## Operations

### List Runs for a Goal

```bash
PYTHONPATH=$(cd ~/.claude/skills/diecast && pwd -P)/cast-server uv run --directory "$(cd ~/.claude/skills/diecast && pwd -P)" python -c "
from cast_server.services.agent_service import get_runs_for_goal
runs = get_runs_for_goal('GOAL_SLUG')
by_parent = {}
for r in runs:
    by_parent.setdefault(r['parent_run_id'], []).append(r)
for r in by_parent.get(None, []):
    print(f'[{r[\"id\"]}] {r[\"status\"]:12s} {r[\"agent_name\"]:30s} {r[\"started_at\"]}')
    for child in by_parent.get(r['id'], []):
        print(f'    [{child[\"id\"]}] {child[\"status\"]:12s} {child[\"agent_name\"]}')
"
```

### List Runs Filtered by Status

```bash
PYTHONPATH=$(cd ~/.claude/skills/diecast && pwd -P)/cast-server uv run --directory "$(cd ~/.claude/skills/diecast && pwd -P)" python -c "
from cast_server.services.agent_service import get_runs_for_goal
runs = [r for r in get_runs_for_goal('GOAL_SLUG') if r['status'] == 'running']
for r in runs:
    print(f'[{r[\"id\"]}] {r[\"status\"]:12s} {r[\"agent_name\"]}')
"
```

### Get a Single Run

```bash
PYTHONPATH=$(cd ~/.claude/skills/diecast && pwd -P)/cast-server uv run --directory "$(cd ~/.claude/skills/diecast && pwd -P)" python -c "
from cast_server.services.agent_service import get_agent_run
import json
r = get_agent_run('RUN_ID')
print(json.dumps(r, indent=2, default=str))
"
```

### Create a Run

`create_agent_run` returns the new `run_id` string. `task_id` and
`input_params` are required positional arguments — pass `None`/`{}` if unused.

```bash
PYTHONPATH=$(cd ~/.claude/skills/diecast && pwd -P)/cast-server uv run --directory "$(cd ~/.claude/skills/diecast && pwd -P)" python -c "
from cast_server.services.agent_service import create_agent_run, get_agent_run
import json
run_id = create_agent_run(
    agent_name='cast-web-researcher',
    goal_slug='GOAL_SLUG',
    task_id=None,
    input_params={'instructions': 'What this run should do', 'phase': 'exploration'},
    parent_run_id=None,
)
print(json.dumps(get_agent_run(run_id), indent=2, default=str))
"
```

### Create a Child Run

Pass the parent's id as `parent_run_id`.

```bash
PYTHONPATH=$(cd ~/.claude/skills/diecast && pwd -P)/cast-server uv run --directory "$(cd ~/.claude/skills/diecast && pwd -P)" python -c "
from cast_server.services.agent_service import create_agent_run, get_agent_run
import json
run_id = create_agent_run(
    agent_name='cast-web-researcher',
    goal_slug='GOAL_SLUG',
    task_id=None,
    input_params={'instructions': 'Sub-task instructions'},
    parent_run_id='PARENT_RUN_ID',
)
print(json.dumps(get_agent_run(run_id), indent=2, default=str))
"
```

### List Child Runs

```bash
PYTHONPATH=$(cd ~/.claude/skills/diecast && pwd -P)/cast-server uv run --directory "$(cd ~/.claude/skills/diecast && pwd -P)" python -c "
from cast_server.services.agent_service import get_agent_run, get_runs_for_goal
parent = get_agent_run('PARENT_RUN_ID')
for r in get_runs_for_goal(parent['goal_slug']):
    if r['parent_run_id'] == 'PARENT_RUN_ID':
        print(f'[{r[\"id\"]}] {r[\"status\"]:12s} {r[\"agent_name\"]}')
"
```

### Change Run Status

`update_agent_run` returns `None`; re-read the run to confirm.

```bash
PYTHONPATH=$(cd ~/.claude/skills/diecast && pwd -P)/cast-server uv run --directory "$(cd ~/.claude/skills/diecast && pwd -P)" python -c "
from cast_server.services.agent_service import update_agent_run, get_agent_run
import json
update_agent_run('RUN_ID', status='running')
print(json.dumps(get_agent_run('RUN_ID'), indent=2, default=str))
"
```

### Complete a Run (with output)

```bash
PYTHONPATH=$(cd ~/.claude/skills/diecast && pwd -P)/cast-server uv run --directory "$(cd ~/.claude/skills/diecast && pwd -P)" python -c "
from cast_server.services.agent_service import update_agent_run, get_agent_run
from datetime import datetime, timezone
import json
update_agent_run(
    'RUN_ID',
    status='completed',
    result_summary='What this run accomplished',
    completed_at=datetime.now(timezone.utc).isoformat(),
)
print(json.dumps(get_agent_run('RUN_ID'), indent=2, default=str))
"
```

### Fail a Run

```bash
PYTHONPATH=$(cd ~/.claude/skills/diecast && pwd -P)/cast-server uv run --directory "$(cd ~/.claude/skills/diecast && pwd -P)" python -c "
from cast_server.services.agent_service import fail_run
import json
r = fail_run('RUN_ID')
print(json.dumps(r, indent=2, default=str))
"
```

### Cancel a Run

```bash
PYTHONPATH=$(cd ~/.claude/skills/diecast && pwd -P)/cast-server uv run --directory "$(cd ~/.claude/skills/diecast && pwd -P)" python -c "
from cast_server.services.agent_service import cancel_run
import json
r = cancel_run('RUN_ID')
print(json.dumps(r, indent=2, default=str))
"
```

### Recheck a Failed/Stuck Run

Re-examines a run stuck in `failed`, `running`, or `pending` by reading its
on-disk dot-files. Returns `None` if recovery isn't possible.

```bash
PYTHONPATH=$(cd ~/.claude/skills/diecast && pwd -P)/cast-server uv run --directory "$(cd ~/.claude/skills/diecast && pwd -P)" python -c "
from cast_server.services.agent_service import recheck_failed_run
import json
r = recheck_failed_run('RUN_ID')
print(json.dumps(r, indent=2, default=str))
"
```

### Delete a Terminal Run

```bash
PYTHONPATH=$(cd ~/.claude/skills/diecast && pwd -P)/cast-server uv run --directory "$(cd ~/.claude/skills/diecast && pwd -P)" python -c "
from cast_server.services.agent_service import delete_run
delete_run('RUN_ID')
print('Deleted')
"
```

Only runs not in an active status (`running`, `pending`, `scheduled`) may be deleted.

## Run Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable identifier, e.g., `run_20260429_231041_e737a7` |
| `parent_run_id` | string \| null | Parent run that spawned this child (null for top-level runs) |
| `agent_name` | string | Agent that owns this run, e.g., `cast-subphase-runner` |
| `goal_slug` | string | Goal this run belongs to |
| `task_id` | int \| null | Optional task this run is executing |
| `status` | enum | See valid values below |
| `started_at` | timestamp | ISO 8601 UTC timestamp when the run was dispatched |
| `completed_at` | timestamp \| null | ISO 8601 UTC timestamp when the run reached a terminal state |
| `error_message` | string \| null | Error message if `status == failed` |
| `result_summary` | string \| null | Summary of what the run accomplished |

## Valid Enum Values

| Field | Values |
|-------|--------|
| `status` | `pending`, `scheduled`, `running`, `idle`, `completed`, `failed` |

## Constraints
- `id` is immutable after creation
- `parent_run_id` cannot be changed after creation (lineage is fixed)
- Only runs not in an active status (`running`, `pending`, `scheduled`) may be deleted — cancel first
- `fail_run` and `cancel_run` set `completed_at` automatically
- `error_message` is only meaningful when `status == failed`
- `cancel_run` kills the run's tmux session and marks it `failed`
