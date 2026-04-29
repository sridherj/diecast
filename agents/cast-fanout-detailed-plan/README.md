# cast-fanout-detailed-plan

**Type:** orchestrator (cast-agent)

Fan-out orchestrator that reads a high-level plan, identifies phases, and dispatches
an independent `cast-detailed-plan` child agent per phase. Collects results and
reconciles cross-phase conflicts.

## I/O Contract
- **Input:** Path to a high-level plan file (e.g., `high_level_plan.collab.md`) + `--goal <slug>`
- **Output:** One detailed plan file per phase in `docs/plan/`, plus a reconciliation summary
- **Config:** None

## Usage
```
/cast-fanout-detailed-plan goals/build-reference-repo/high_level_plan.collab.md --goal build-reference-repo
/cast-fanout-detailed-plan goals/build-reference-repo/high_level_plan.collab.md --goal build-reference-repo --max-batch-size 2
```

## Options
| Option | Description | Default |
|--------|-------------|---------|
| `--goal <slug>` | Goal slug (required) | -- |
| `--max-batch-size <n>` | Max concurrent child planners | 3 |
| `--from-phase <N>` | Resume from phase N (assumes earlier plans exist) | -- |
| `--dry-run` | Show dispatch plan only | false |
