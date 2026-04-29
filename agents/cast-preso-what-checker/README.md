# cast-preso-what-checker

Stage 2 checker: validates WHAT docs against a 7-item checklist. Runs per what/ doc.

## Type
`taskos-agent`

## I/O Contract

### Input
- **Required:** One `presentation/what/{slide_id}.md` file to check
- **Required:** `presentation/narrative.collab.md` — for cross-reference
- **Optional:** Checker feedback from prior iteration (if rework cycle)

### Output
- **PASS:** Structured verdict JSON with evidence per criterion
- **FAIL:** Structured feedback with specific issues, evidence, and guidance

### Config
None (stateless).

## Usage

```
POST /api/agents/cast-preso-what-checker/trigger
  { "goal_slug": "...", "delegation_context": { "slide_id": "05-agent-resume" } }
```

## Examples

Input: what/05-agent-resume.md
Output: JSON verdict with 7 checks, overall PASS/FAIL, human-readable feedback if FAIL
