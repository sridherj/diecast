# cast-preso-what-planner

Stage 2a planner: reads a locked presentation narrative and emits a slide list plus
per-slide outcome stubs that Stage 2b workers fill in.

## Type
`taskos-agent`

## I/O Contract

### Input
- **Required:** `presentation/narrative.collab.md` — locked narrative from Stage 1
- **Optional:** Delegation context with `mode: "rework"` and `feedback` (see agent .md)

### Output
- `presentation/what/_slide_list.md` — slide list manifest (ordering, types, notes)
- `presentation/what/{slide_id}.stub.md` — one stub per slide with type, outcome,
  narrative fit, L1/L2 hierarchy, content pointers

### Config
None (stateless).

## Usage

Invoked by the orchestrator at the start of Stage 2:

```
POST /api/agents/cast-preso-what-planner/trigger
  { "goal_slug": "...", "delegation_context": { "narrative_path": "presentation/narrative.collab.md" } }
```

Rework mode (fix manifest or specific stubs):

```
POST /api/agents/cast-preso-what-planner/trigger
  { "goal_slug": "...", "delegation_context": { "mode": "rework", "feedback": { ... } } }
```

## Examples

- Input: 10-slide narrative
- Output: `_slide_list.md` with 10 rows + 10 `.stub.md` files

## Split History

Forked from `cast-preso-what` on 2026-04-21 (see
`docs/decision/2026-04-21-preso-what-fork.md`). The planner owns cross-slide decisions
(L1/L2 differentiation, arc preservation). The worker (`cast-preso-what-worker`) takes
each stub and produces the full WHAT doc with resources and verification criteria.
