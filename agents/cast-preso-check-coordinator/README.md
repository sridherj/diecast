# cast-preso-check-coordinator

Dispatches the 3 specialized checkers for a slide, aggregates their verdicts, runs an adversarial pass, and determines next action (approve, rework, or escalate). Supports full and lightweight check modes. After all slides pass, runs cross-slide consistency.

## Type
`taskos-agent`

## I/O Contract
- **Input:**
  - `how/{slide_id}/slide.html` -- the slide to check
  - `how/{slide_id}/brief.collab.md` -- approach doc
  - `what/{slide_id}.md` -- WHAT doc
  - `narrative.collab.md` -- narrative context
  - Delegation context with:
    - `slide_id`: which slide to check
    - `check_mode`: "full" | "lightweight"
    - `rework_iteration`: 0-3 (current iteration count)
    - `previous_feedback`: path to prior checker_feedback.md (if rework)
    - `cross_slide_mode`: false (default) | true (run cross-slide consistency pass)
    - `all_slide_ids`: list of all slide IDs (only when `cross_slide_mode: true`)
- **Output:**
  - Aggregated verdict in output.json
  - `how/{slide_id}/checker_feedback.md` -- written ONLY on FAIL, structured rework guidance for HOW maker
  - `how/{slide_id}/check-results.json` -- full audit: all 3 verdicts + adversarial pass + final decision
- **Config:** None persistent

## Usage
Called by `cast-preso-orchestrator` (or manually during testing) via HTTP delegation.

## Delegates To
- `cast-preso-check-content`
- `cast-preso-check-visual`
- `cast-preso-check-tone`
