# cast-preso-check-visual

Evaluates a Stage 3 slide for visual quality: layout specificity, hierarchy clarity, viewport fit, visual toolkit consistency, and whether it avoids the "generic AI slide" aesthetic.

## Type
`taskos-agent`

## I/O Contract
- **Input:**
  - `how/{slide_id}/slide.html` -- the slide to check
  - `how/{slide_id}/brief.collab.md` -- the approach doc
  - `how/{slide_id}/assets/` -- any illustrations or images
  - Visual toolkit skill (`.claude/skills/cast-preso-visual-toolkit/`)
  - Delegation context with `slide_id`
- **Output:**
  - JSON verdict (dimension: "visual") in output.json artifacts
- **Config:** None

## Usage
Called by `cast-preso-check-coordinator` via HTTP delegation.

## Examples
**Input:** Slide with title + 3 equal-size bullets + generic right-aligned image.
**Output:** FAIL -- "not-generic" criterion failed. Evidence: layout matches the default AI pattern (title + bullets + image-right). No specific visual approach. Suggest: use a named archetype (single-stat hero, compare-contrast, etc.) that suits the content.

**Input:** Slide using timeline archetype with progressive fragment reveals, proper whitespace.
**Output:** PASS -- layout is specific (timeline archetype), hierarchy clear (current step highlighted, future steps muted), fits viewport, matches visual toolkit tokens.
