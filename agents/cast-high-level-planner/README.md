# cast-high-level-planner

Reads a goal's exploration output and generates a high-level phased execution plan.

## Type
claude-code-skill

## I/O Contract
- **Input:** Goal directory with `requirements.human.md` (or legacy `writeup.md`) and optional exploration artifacts (research, playbooks, summary)
- **Output:** `plan.collab.md` in the goal directory

## How It Works
1. Reads all available artifacts from the goal directory (requirements, research, playbooks, tasks)
2. Identifies the core outcome and major work areas
3. Maps dependencies between work areas
4. Groups into meaningful phases with outcomes, verification, and effort estimates
5. Generates `plan.collab.md` with progressive detail (near-term detailed, far-out high-level)

## Usage
```
# In Claude Code, while in the goal's context:
/cast-high-level-planner
```

Or triggered from the Diecast UI "Generate Phased Plan" button in the Plan tab.

## Key Files
- `SKILL.md` — Agent instructions, workflow, output format, and quality bar
- `runs/` — Execution logs
- `tests/test-cases.md` — Manual test scenarios

## Related
- `goal-decomposer` — Breaks goals into steps (pre-requisite, feeds into exploration)
- `explore` — Full exploration pipeline (pre-requisite, produces research + playbooks)
- `task-suggester` — Generates atomic tasks FROM the plan (post-requisite)
- `/phase-plan` — Generic plan splitter (different purpose: splits existing plans into execution phases)
