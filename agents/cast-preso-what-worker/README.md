# cast-preso-what-worker

Stage 2b worker: takes one planner stub and produces the full WHAT doc with curated
resources, data points, and verification criteria for Stage 3.

## Type
`diecast-agent`

## I/O Contract

### Input
- **Required:** `presentation/what/{slide_id}.stub.md` (from the planner)
- **Required:** `presentation/narrative.collab.md` (for arc context)
- **Optional:** Delegation context with `mode: "rework"`, `slide_id`, `feedback`

### Output
- `presentation/what/{slide_id}.md` — finished WHAT doc

### Config
None (stateless).

## Usage

One invocation per slide. The orchestrator fans out N workers in parallel where N is
the number of slides in `_slide_list.md`.

```
POST /api/agents/cast-preso-what-worker/trigger
  { "goal_slug": "...", "delegation_context": {
      "slide_id": "05-agent-resume",
      "stub_path": "presentation/what/05-agent-resume.stub.md",
      "narrative_path": "presentation/narrative.collab.md"
  }}
```

Rework mode (fix one doc based on checker verdict):

```
POST /api/agents/cast-preso-what-worker/trigger
  { "goal_slug": "...", "delegation_context": {
      "mode": "rework",
      "slide_id": "05-agent-resume",
      "feedback": { "failing_checks": [...], "feedback_detail": "...", "what_worked": [...] }
  }}
```

## Examples

- Input: stub for `05-agent-resume` + narrative
- Output: `what/05-agent-resume.md` with 2 concrete local file references, 3 data points
  (exact numbers), 4 verification criteria (checkable)

## Split History

Forked from `cast-preso-what` on 2026-04-21 (see
`docs/decision/2026-04-21-preso-what-fork.md`). The worker is scoped to one slide and
cannot modify planner decisions (outcome, L1/L2) — those come from the stub verbatim.
The planner (`cast-preso-what-planner`) owns cross-slide decisions.
