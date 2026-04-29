---
name: cast-goals
description: >
  Create, list, update, and manage Diecast goals via service layer.
  Trigger phrases: "create goal", "list goals", "update goal status",
  "change goal phase", "focus goal", "unfocus goal", "show goal",
  "delete goal", "goal CRUD".
memory: user
effort: medium
---

# Diecast Goals — Service Layer Reference

Manage Diecast goals directly via `uv run python -c` commands from the `second-brain/` directory.

> **ERROR HANDLING:** If any `uv run python -c` command fails (import error, service exception, DB error, etc.), **STOP immediately** and tell SJ: "Human intervention required: [error details]". Do NOT attempt to fix, retry, or work around the issue.

## Environment

All commands must set PYTHONPATH to resolve the taskos package:

```bash
PYTHONPATH=/home/sridherj/workspace/second-brain/taskos/src uv run python -c "..."
```

## Operations

### List All Goals

```bash
PYTHONPATH=/home/sridherj/workspace/second-brain/taskos/src uv run python -c "
from taskos.services.goal_service import get_all_goals
goals = get_all_goals()
for g in goals:
    print(f'{g[\"slug\"]:40s} status={g[\"status\"]:10s} phase={g[\"phase\"] or \"\":15s} focus={bool(g[\"in_focus\"])}')
"
```

### Get a Single Goal

```bash
PYTHONPATH=/home/sridherj/workspace/second-brain/taskos/src uv run python -c "
from taskos.services.goal_service import get_goal
import json
g = get_goal('SLUG_HERE')
print(json.dumps(g, indent=2, default=str))
"
```

### Create a Goal

```bash
PYTHONPATH=/home/sridherj/workspace/second-brain/taskos/src uv run python -c "
from taskos.services.goal_service import create_goal
import json
g = create_goal(title='TITLE_HERE', tags=['tag1', 'tag2'], in_focus=False)
print(json.dumps(g, indent=2, default=str))
"
```

Creates directory, goal.yaml, DB record, and starter tasks. Status starts as `accepted`, phase as `requirements`.

### Update Status

```bash
PYTHONPATH=/home/sridherj/workspace/second-brain/taskos/src uv run python -c "
from taskos.services.goal_service import update_status
import json
g = update_status('SLUG_HERE', 'TARGET_STATUS')
print(json.dumps(g, indent=2, default=str))
"
```

### Update Phase

```bash
PYTHONPATH=/home/sridherj/workspace/second-brain/taskos/src uv run python -c "
from taskos.services.goal_service import update_phase
import json
g = update_phase('SLUG_HERE', 'TARGET_PHASE')
print(json.dumps(g, indent=2, default=str))
"
```

### Toggle Focus

```bash
PYTHONPATH=/home/sridherj/workspace/second-brain/taskos/src uv run python -c "
from taskos.services.goal_service import toggle_focus
import json
g = toggle_focus('SLUG_HERE', True)   # or False to unfocus
print(json.dumps(g, indent=2, default=str))
"
```

## Valid Values

### Statuses
| Status | Description |
|--------|-------------|
| `idea` | Initial capture, not yet committed |
| `accepted` | Active goal, being worked on |
| `completed` | Done |
| `declined` | Dropped / won't do |

### Status Transitions
| From | Allowed Targets |
|------|----------------|
| `idea` | `accepted`, `declined` |
| `accepted` | `completed` |

> `completed` and `declined` are terminal — no transitions out.

### Phases (free-form, any valid phase allowed)
| Phase | Description |
|-------|-------------|
| `requirements` | Gathering requirements |
| `exploration` | Research and exploration |
| `plan` | Planning execution |
| `execution` | Building / implementing |

## Constraints
- Cannot change phase of a terminal-status goal (`completed` / `declined`)
- `create_goal` always starts as `accepted` + `requirements` phase
- Slug is auto-generated from title (lowercase, hyphenated)
- Creating a goal also creates starter tasks and artifact stub files
