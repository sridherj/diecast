# explore

Full exploration pipeline: goal decomposition, 7-angle research, playbook synthesis, and impact summary.

## Type

Claude Code Skill (Orchestrator)

## I/O Contract

- **Input:** A goal statement (e.g., "explore how to build an AI-powered code review tool")
- **Output:** Complete exploration directory with steps, research, playbooks, and impact summary

## How It Works

### Phase 1: Interactive
1. Creates workspace directory under `explorations/`
2. Clarifies goal with 2-3 targeted questions
3. Decomposes goal into 3-7 steps with substeps
4. Gets user approval on steps

### Phase 2: Autonomous (15-30+ min)
5. Spawns parallel researcher subagents (one per step, each doing 7-angle research)
6. Spawns parallel synthesizer subagents (one per step, creating playbooks)

### Phase 3: Summary
7. Creates impact-rated summary with top recommendations
8. Presents results to user

## Output Directory Structure

```
explorations/YYYY-MM-DD-topic-slug/
  steps.ai.md
  research/01-step-slug.md, 02-...
  playbooks/01-step-slug-playbook.md, 02-...
  summary.ai.md
```

## Usage

```
"explore how to build an AI-powered code review tool"
"research and plan: launching a SaaS product"
"deep dive on: transitioning to a CTO role"
```

## Composed Skills

- **goal-decomposer** — Step decomposition (Phase 1)
- **web-researcher** — 7-angle research (Phase 2)
- **playbook-synthesizer** — Research-to-playbook (Phase 2)

## Key Files

- `SKILL.md` — Orchestrator instructions with full pipeline definition
