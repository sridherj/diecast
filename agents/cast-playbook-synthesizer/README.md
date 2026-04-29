# playbook-synthesizer

Turns raw research into polished, opinionated, actionable playbooks with impact ratings.

## Type

Claude Code Skill

## I/O Contract

- **Input:** Raw research notes + goal context + step name
- **Output:** Structured playbook with 10x approach, step-by-step instructions, tools table, AI approaches, contrarian take, sources, and impact rating

## How It Works

1. Reads and internalizes research from all 7 angles
2. Identifies highest-impact insights and cross-angle agreements
3. Synthesizes into an opinionated playbook (not aggregation)
4. Rates impact as HIGH/MED/LOW with justification

## Quality Bar

"If 10,000 people follow this playbook, they should all succeed."

## Usage

```
"synthesize this research into a playbook"
"build a playbook from these notes"
"create an action plan from this research"
```

## Key Files

- `SKILL.md` — Agent instructions with exact playbook template
