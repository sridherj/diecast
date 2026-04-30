# Execution Manifest: Fix Trigger 500 on Malformed `delegation_context`

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:

1. Start a new Claude session.
2. Tell Claude: "Read `docs/execution/fix-trigger-500-malformed-delegation-context/_shared_context.md` then execute `docs/execution/fix-trigger-500-malformed-delegation-context/<spX_name>/plan.md`."
3. After completion, update the Status column below.

sp1a and sp1b touch disjoint files — they may be executed in parallel by two simultaneous Claude sessions. Either order of landing also works (no merge conflict possible).

## Sub-Phase Overview

| #   | Sub-phase                                | Directory/File          | Depends On | Status      | Notes                                                                 |
|-----|------------------------------------------|-------------------------|-----------|-------------|------------------------------------------------------------------------|
| 1a  | Server fix — 422 + `output_dir` fallback | `sp1a_server_fix/`      | --        | Done        | 11/11 tests pass; needs server restart to take effect. |
| 1b  | SKILL.md doc reword                      | `sp1b_skill_docs/`      | --        | Done        | Single-line edit at `cast-child-delegation/SKILL.md:126`.              |

Status: Not Started → In Progress → Done → Verified → Skipped

## Dependency Graph

```
        ┌────────────────────────┐
        │ sp1a_server_fix         │
   ┌────┤ (model + route + tests)│
   │    └────────────────────────┘
START ──┤
   │    ┌────────────────────────┐
   └────┤ sp1b_skill_docs         │
        │ (SKILL.md line 126)    │
        └────────────────────────┘
```

Both sub-phases start from `START`; neither blocks the other.

## Execution Order

### Parallel Group 1 (run simultaneously)

- **sp1a_server_fix** — server-side resilience: pydantic default + 422 envelope + 3 regression tests + manual curl verification.
- **sp1b_skill_docs** — parent-facing docs: reword `output_dir` line as optional with goal-dir fallback reference.

There is no Sequential Group 2; the work is fully parallel.

## Progress Log

<!-- Update after each sub-phase. -->
