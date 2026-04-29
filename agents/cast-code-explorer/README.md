# cast-code-explorer

Explores a codebase from 7 structured angles, producing research notes
compatible with the web-researcher output format. Maps the current terrain —
what exists, how it's built, what's missing — as honest context for exploration
playbooks.

## Type

cast-agent

## I/O Contract

- **Input:** Step to explore, goal context, codebase directory path, goal directory, output path
- **Output:** Structured research notes (7 sections + Key Takeaways + Key Files) in `.ai.md` format
- **Config:** `config.yaml` — model: opus, context: full, timeout: 60m

## How It Works

1. Reads goal requirements to understand what to look for
2. Orients in the codebase (README, directory structure, tech stack)
3. Explores from 7 angles: Data Model, Implementation, Gaps, Patterns, Flow, Tests, Config
4. Uses tiered tools: code-review-graph MCP → Explore subagent → Grep/Read
5. Synthesizes Key Takeaways (opinionated, architectural)
6. Writes output matching web-researcher format for synthesizer compatibility

## Philosophy

Maps terrain honestly — doesn't defend the status quo. Part of a "go broad" exploration
strategy where code context + web research feed into playbooks that may recommend
anything from incremental fixes to complete rewrites.

## Usage

Typically dispatched by `cast-explore` orchestrator when code exploration is enabled.
Can also be used standalone for codebase analysis.

```
"explore codebase for bug triage patterns"
"code exploration: how is auth implemented?"
"analyze code: data pipeline architecture"
```

## Key Files

- `cast-code-explorer.md` — Agent brain (philosophy, workflow, output format)
- `config.yaml` — Model and timeout settings
- `tests/test-cases.md` — Manual test scenarios
