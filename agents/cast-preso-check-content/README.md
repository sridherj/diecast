# cast-preso-check-content

Evaluates a Stage 3 slide against its WHAT doc to verify content achieves the stated outcome, L1/L2 hierarchy is respected, and slide type treatment is appropriate.

## Type
`diecast-agent`

## I/O Contract
- **Input:**
  - `how/{slide_id}/slide.html` -- the slide to check
  - `how/{slide_id}/brief.collab.md` -- the approach doc
  - `what/{slide_id}.md` -- the WHAT doc with outcome, L1/L2, verification criteria
  - `narrative.collab.md` -- for narrative context
  - Delegation context with `slide_id` and `check_mode`
- **Output:**
  - JSON verdict (dimension: "content") in output.json artifacts
  - PASS/FAIL with evidence per criterion
- **Config:** None

## Usage
Called by `cast-preso-check-coordinator` via HTTP delegation. Never invoked directly by the user.

## Examples
**Input:** Slide HTML for "Agent Resume" slide, WHAT doc stating L1: agents have capabilities, L2: agents can be personalized.
**Output:** PASS -- L1 items visually prominent (large headings), L2 items present as muted bullets. Single takeaway clear in <5 seconds.

**Input:** Slide HTML cramming 4 L1 concepts with equal visual weight.
**Output:** FAIL -- criterion "one-clear-takeaway" failed. Evidence: 4 competing L1 items at same font size. What good looks like: promote one to hero position, demote others to supporting.
