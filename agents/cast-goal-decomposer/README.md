# goal-decomposer

Breaks any goal into structured, dependency-ordered steps with substeps and success criteria.

## Type

Claude Code Skill

## I/O Contract

- **Input:** A goal statement (string), optionally with context about current state
- **Output:** Structured `steps.ai.md` with 3-7 major steps, substeps, dependencies, and 10x thinking

## How It Works

1. Analyzes the goal to identify domain, scope, and success criteria
2. Decomposes into 3-7 major steps with 2-5 substeps each
3. Orders by logical dependencies
4. Applies "10x thinking" — what would the world's best person do differently?
5. Outputs structured markdown

## Usage

```
"break this down: build an AI-powered code review tool"
"decompose this goal: launch a SaaS product in 3 months"
"what are the steps to learn distributed systems?"
```

## Key Files

- `SKILL.md` — Agent instructions
