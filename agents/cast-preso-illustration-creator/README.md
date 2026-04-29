# cast-preso-illustration-creator

Create illustrations for presentation slides using Stitch MCP (watercolor/raster)
or inline SVG (diagrams/data viz). Uses Style Bible approach for cross-deck consistency.

## Type
`taskos-agent`

## I/O Contract

### Input
- **Required:** Scene brief (7-slot template) from `cast-preso-how`
  - Subject, action/pose, setting, composition, style bible, slide context, exclusions
- **Required:** Style Bible source (from visual toolkit or presentation-specific override)
- **Optional:** Style anchor image path (for consistency comparison after first illustration)
- **Optional:** Checker feedback for rework iterations

### Output
- Illustration file saved to `how/{slide_id}/assets/{filename}.{webp|svg}`
- Generation log at `how/{slide_id}/assets/{filename}.generation-log.md` containing:
  - Exact prompt used (copy-paste reproducible)
  - Tool used (Stitch MCP / inline SVG)
  - Scene brief slots (for traceability)
  - Iteration number (if rework)
  - What changed from previous iteration (if rework)

### Config
None (style configuration comes from the visual toolkit / scene brief)

## Usage
Delegated by `cast-preso-how`. Not invoked directly by SJ.

## Delegates To
- `cast-preso-illustration-checker` — Three-pass verification of generated illustrations

## Examples
Input: Scene brief for a watercolor illustration of agents collaborating
Output: `how/03-model/assets/agent-collaboration.webp` + generation log
