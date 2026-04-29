# Agent Interdependency Graph (auto-generated)

> Source: `bin/audit-interdependencies --mode=all --json`
> Companion machine-readable file: `agent-interdependency-graph.json`

## Summary

- Nodes: 46 (36 agents, 10 skills)
- Edges: 1866 cross-references
- green: 758 | yellow: 412 | red: 696

## Top-referenced targets (centrality clue)

| Target | Inbound green edges |
|---|---|
| `cast-preso-orchestrator` | 70 |
| `cast-agent-design-guide` | 63 |
| `cast-detailed-plan` | 52 |
| `cast-child-delegation` | 40 |
| `cast-high-level-planner` | 38 |
| `cast-explore` | 33 |
| `cast-preso-how` | 32 |
| `cast-preso-check-coordinator` | 30 |
| `cast-preso-assembler` | 27 |
| `cast-fanout-detailed-plan` | 25 |

## Top-referencing agents (centrality clue)

| Source | Outbound green edges |
|---|---|
| `cast-preso-orchestrator` | 114 |
| `cast-agent-design-guide` | 61 |
| `cast-detailed-plan` | 50 |
| `cast-explore` | 44 |
| `cast-high-level-planner` | 37 |
| `cast-child-delegation` | 37 |
| `cast-fanout-detailed-plan` | 33 |
| `cast-orchestrate` | 32 |
| `cast-preso-check-coordinator` | 32 |
| `cast-preso-visual-toolkit` | 25 |

## Adjacency (per-source)

### `cast-agent-compliance`

- `cast-agent-compliance` × 99
- `cast-agent-design-guide` × 2

### `cast-agent-design-guide`

- `cast-agent-design-guide` × 174

### `cast-asciinema-editor`

- `cast-asciinema-editor` × 2

### `cast-child-delegation`

- `cast-child-delegation` × 135
- `cast-create-execution-plan` × 1
- `cast-detailed-plan` × 2
- `cast-explore` × 1
- `cast-playbook-synthesizer` × 1
- `cast-subphase-runner` × 1
- `cast-task-suggester` × 1
- `cast-web-researcher` × 4

### `cast-code-explorer`

- `cast-code-explorer` × 13

### `cast-create-execution-plan`

- `cast-create-execution-plan` × 71
- `cast-orchestrate` × 1
- `cast-plan-review` × 2

### `cast-detailed-plan`

- `cast-detailed-plan` × 92
- `cast-interactive-questions` × 4
- `cast-refine-requirements` × 1
- `cast-update-spec` × 2

### `cast-docstring-best-practices`

- `cast-docstring-best-practices` × 6

### `cast-explore`

- `cast-child-delegation` × 10
- `cast-code-explorer` × 2
- `cast-explore` × 84
- `cast-goal-decomposer` × 1
- `cast-interactive-questions` × 2
- `cast-playbook-synthesizer` × 1
- `cast-refine-requirements` × 1
- `cast-web-researcher` × 2

### `cast-fanout-detailed-plan`

- `cast-child-delegation` × 4
- `cast-detailed-plan` × 5
- `cast-explore` × 1
- `cast-fanout-detailed-plan` × 52

### `cast-goal-decomposer`

- `cast-goal-decomposer` × 15
- `cast-refine-requirements` × 1

### `cast-goals`

- `cast-goals` × 3

### `cast-high-level-planner`

- `cast-high-level-planner` × 67
- `cast-refine-requirements` × 1

### `cast-interactive-questions`

- `cast-interactive-questions` × 4

### `cast-mvcs-compliance`

- `cast-mvcs-compliance` × 8

### `cast-orchestrate`

- `cast-child-delegation` × 6
- `cast-create-execution-plan` × 4
- `cast-interactive-questions` × 2
- `cast-orchestrate` × 50
- `cast-subphase-runner` × 5

### `cast-plan-review`

- `cast-interactive-questions` × 4
- `cast-plan-review` × 15

### `cast-playbook-synthesizer`

- `cast-playbook-synthesizer` × 1

### `cast-preso-assembler`

- `cast-preso-assembler` × 109

### `cast-preso-check-content`

- `cast-preso-check-content` × 11

### `cast-preso-check-coordinator`

- `cast-preso-check-content` × 3
- `cast-preso-check-coordinator` × 40
- `cast-preso-check-tone` × 3
- `cast-preso-check-visual` × 3

### `cast-preso-check-tone`

- `cast-preso-check-tone` × 7

### `cast-preso-check-visual`

- `cast-preso-check-visual` × 12

### `cast-preso-compliance-checker`

- `cast-preso-assembler` × 5
- `cast-preso-compliance-checker` × 27
- `cast-preso-how` × 7

### `cast-preso-how`

- `cast-preso-how` × 56
- `cast-preso-illustration-creator` × 3

### `cast-preso-illustration-checker`

- `cast-preso-illustration-checker` × 14

### `cast-preso-illustration-creator`

- `cast-preso-how` × 1
- `cast-preso-illustration-checker` × 1
- `cast-preso-illustration-creator` × 42

### `cast-preso-narrative`

- `cast-child-delegation` × 2
- `cast-preso-narrative` × 24
- `cast-preso-narrative-checker` × 2

### `cast-preso-narrative-checker`

- `cast-preso-narrative-checker` × 7

### `cast-preso-orchestrator`

- `cast-child-delegation` × 6
- `cast-interactive-questions` × 2
- `cast-preso-assembler` × 4
- `cast-preso-check-coordinator` × 7
- `cast-preso-compliance-checker` × 4
- `cast-preso-how` × 5
- `cast-preso-orchestrator` × 156
- `cast-preso-what-checker` × 7
- `cast-preso-what-planner` × 5
- `cast-preso-what-worker` × 8

### `cast-preso-review`

- `cast-preso-review` × 4

### `cast-preso-visual-toolkit`

- `cast-preso-visual-toolkit` × 48

### `cast-preso-what-checker`

- `cast-preso-what-checker` × 14

### `cast-preso-what-planner`

- `cast-preso-what-planner` × 32
- `cast-preso-what-worker` × 1

### `cast-preso-what-worker`

- `cast-preso-what-planner` × 1
- `cast-preso-what-worker` × 29
- `cast-web-researcher` × 1

### `cast-pytest-best-practices`

- `cast-pytest-best-practices` × 10

### `cast-python-best-practices`

- `cast-python-best-practices` × 6

### `cast-refine-requirements`

- `cast-interactive-questions` × 4
- `cast-refine-requirements` × 29

### `cast-review-code`

- `cast-review-code` × 17

### `cast-runs`

- `cast-runs` × 3
- `cast-subphase-runner` × 1
- `cast-web-researcher` × 2

### `cast-subphase-runner`

- `cast-orchestrate` × 1
- `cast-subphase-runner` × 9

### `cast-task-suggester`

- `cast-high-level-planner` × 2
- `cast-task-suggester` × 48
- `cast-web-researcher` × 2

### `cast-tasks`

- `cast-tasks` × 5
- `cast-web-researcher` × 2

### `cast-update-spec`

- `cast-interactive-questions` × 2
- `cast-update-spec` × 26
- `cast-web-researcher` × 1

### `cast-web-researcher`

- `cast-web-researcher` × 7

### `cast-wrap-up`

- `cast-wrap-up` × 10
