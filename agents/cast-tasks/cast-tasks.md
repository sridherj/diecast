---
name: cast-tasks
description: >
  Create, list, update, and manage Diecast tasks via service layer.
  Trigger phrases: "create task", "list tasks", "update task",
  "complete task", "task status", "add tasks", "batch create tasks",
  "show tasks for goal", "task CRUD".
memory: user
effort: medium
---

# Diecast Tasks — Service Layer Reference

Manage Diecast tasks directly via `uv run python -c` commands from the `second-brain/` directory.

> **ERROR HANDLING:** If any `uv run python -c` command fails (import error, service exception, DB error, etc.), **STOP immediately** and tell SJ: "Human intervention required: [error details]". Do NOT attempt to fix, retry, or work around the issue.

## Environment

All commands must set PYTHONPATH to resolve the taskos package:

```bash
PYTHONPATH=/home/sridherj/workspace/second-brain/taskos/src uv run python -c "..."
```

## Operations

### List Tasks for a Goal

```bash
PYTHONPATH=/home/sridherj/workspace/second-brain/taskos/src uv run python -c "
from taskos.services.task_service import get_tasks_for_goal
import json
tasks = get_tasks_for_goal('GOAL_SLUG')
for t in tasks:
    print(f'[{t[\"id\"]:4d}] {t[\"status\"]:12s} {t[\"phase\"]:15s} {t[\"title\"]}')
    for sub in t.get('subtasks', []):
        print(f'       [{sub[\"id\"]:4d}] {sub[\"status\"]:12s} {sub[\"title\"]}')
"
```

### List Tasks Filtered by Phase

```bash
PYTHONPATH=/home/sridherj/workspace/second-brain/taskos/src uv run python -c "
from taskos.services.task_service import get_tasks_for_goal
tasks = get_tasks_for_goal('GOAL_SLUG', phase='execution')
for t in tasks:
    print(f'[{t[\"id\"]:4d}] {t[\"status\"]:12s} {t[\"title\"]}')
"
```

### Get a Single Task

```bash
PYTHONPATH=/home/sridherj/workspace/second-brain/taskos/src uv run python -c "
from taskos.services.task_service import get_task
import json
t = get_task(TASK_ID)
print(json.dumps(t, indent=2, default=str))
"
```

### Create a Task

```bash
PYTHONPATH=/home/sridherj/workspace/second-brain/taskos/src uv run python -c "
from taskos.services.task_service import create_task
import json
t = create_task(
    goal_slug='GOAL_SLUG',
    title='TITLE',
    outcome='What success looks like',
    action='Concrete next action',
    task_type='build',
    estimated_time='30m',
    energy='medium',
    assigned_to='ai',
    phase='execution',
    tip='Helpful hint',
    recommended_agent='cast-web-researcher',
    task_artifacts=['path/to/artifact.md'],
)
print(json.dumps(t, indent=2, default=str))
"
```

All parameters except `goal_slug` and `title` are optional.

### Create a Sub-Task

```bash
PYTHONPATH=/home/sridherj/workspace/second-brain/taskos/src uv run python -c "
from taskos.services.task_service import create_task
import json
t = create_task(
    goal_slug='GOAL_SLUG',
    title='Sub-task title',
    parent_id=PARENT_TASK_ID,
    phase='execution',
)
print(json.dumps(t, indent=2, default=str))
"
```

Only 1 level of nesting allowed (sub-tasks cannot have sub-tasks).

### Batch Create Tasks

```bash
PYTHONPATH=/home/sridherj/workspace/second-brain/taskos/src uv run python -c "
from taskos.services.task_service import create_tasks_batch
create_tasks_batch('GOAL_SLUG', [
    {'title': 'Task 1', 'phase': 'execution', 'tip': 'hint'},
    {'title': 'Task 2', 'phase': 'execution', 'recommended_agent': 'cast-web-researcher'},
])
print('Done')
"
```

Batch fields: `title`, `phase` (required), `tip`, `recommended_agent`, `task_artifacts` (optional).

### Update a Task

```bash
PYTHONPATH=/home/sridherj/workspace/second-brain/taskos/src uv run python -c "
from taskos.services.task_service import update_task
import json
t = update_task(TASK_ID, title='New title', outcome='New outcome', phase='plan')
print(json.dumps(t, indent=2, default=str))
"
```

Editable fields: `title`, `outcome`, `action`, `task_type`, `estimated_time`, `energy`, `assigned_to`, `phase`, `tip`, `recommended_agent`, `task_artifacts`.

### Change Task Status

```bash
PYTHONPATH=/home/sridherj/workspace/second-brain/taskos/src uv run python -c "
from taskos.services.task_service import update_task_status
import json
t = update_task_status(TASK_ID, 'in_progress')
print(json.dumps(t, indent=2, default=str))
"
```

### Complete a Task (with metadata)

```bash
PYTHONPATH=/home/sridherj/workspace/second-brain/taskos/src uv run python -c "
from taskos.services.task_service import complete_task
import json
t = complete_task(
    TASK_ID,
    actual_time='25m',
    moved_toward_goal='yes',
    notes='Completed successfully',
)
print(json.dumps(t, indent=2, default=str))
"
```

## Valid Enum Values

| Field | Values |
|-------|--------|
| `task_type` | `build`, `research`, `spike`, `decision`, `write`, `review`, `refactor`, `test`, `ops` |
| `energy` | `low`, `medium`, `high` |
| `assigned_to` | `human`, `ai`, `pair` |
| `phase` | `requirements`, `exploration`, `plan`, `execution` |
| `status` | `pending`, `in_progress`, `completed` |

## Constraints
- All operations auto-rerender `tasks.md` in the goal directory
- Sub-tasks: max 1 level deep (parent must not be a sub-task itself)
- `task_artifacts` paths must be relative to goal dir (no `..` traversal, no absolute paths)
- Pass `""` (empty string) to clear an optional field via `update_task`
