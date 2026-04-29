# task-suggester

Generates atomic task suggestions for Diecast goals based on plan, requirements, and current progress. Creates suggestions directly as tasks with `status='suggested'` via the Diecast HTTP API.

## Type
claude-code-agent (interactive)

## I/O Contract
- **Input:** Goal directory context via `context_mode: full` (goal.yaml, plan.collab.md, tasks.md, requirements.human.md) + current phase
- **Output:** Tasks created in DB with `status='suggested'` via `POST /api/goals/{slug}/tasks` (JSON) + `.agent-{run_id}.output.json`

## How It Works
1. Reads goal context from directory artifacts
2. Analyzes current phase and existing tasks
3. Generates 3-5 outcome-first, atomic (30-60 min) task suggestions
4. Creates each suggestion via HTTP POST to Diecast API with `status='suggested'`
5. Handles parent/child groups sequentially (parent first, then children with `parent_id`)
6. Writes output.json with created task IDs and status

## Configuration
- `interactive: true` — runs in a visible terminal so the user can watch and intervene
- `context_mode: full` — reads all goal artifacts
- `model: opus` — uses Opus for high-quality suggestions

## Key Files
- `SKILL.md` — Suggestion rules, HTTP API instructions, output contract
- `config.yaml` — Agent configuration

## Related
- `cast-high-level-planner` — Creates the phased plan that this agent decomposes into tasks
- `10xme` — Similar atomic task philosophy, different scope (personal productivity)
