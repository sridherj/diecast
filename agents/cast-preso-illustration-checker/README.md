# cast-preso-illustration-checker

Three-pass verification for AI-generated illustrations. Evaluates against scene brief,
Style Bible, and cross-deck style consistency. Returns structured verdicts with specific
feedback for rework.

## Type
`diecast-agent`

## I/O Contract

### Input
- **Required:** Illustration file path (WebP or SVG)
- **Required:** Scene brief (7-slot template) that the illustration was generated from
- **Required:** Generation log (prompt used, tool used, iteration number)
- **Required:** Iteration budget context (complexity level, current iteration count, max allowed)
- **Optional:** Style anchor image path (for cross-deck consistency — empty for first illustration)
- **Optional:** Previous checker feedback (for tracking regression/oscillation)

> **Note:** For Pass 3 check 3.4 (communication value), the Checker evaluates the illustration
> against the scene brief's Slot 6. The illustration is judged in the context of the slide's
> message, not in isolation.

### Output
Structured verdict JSON written to `how/{slide_id}/assets/{filename}.checker-verdict.json`:

```json
{
  "verdict": "STOP | CONTINUE | BACKTRACK | RESTART | ESCALATE",
  "blind_description": "Raw description of the image before evaluation",
  "pass_reached": 1 | 2 | 3,
  "iteration": 2,
  "checks": {
    "pass1": { "1.1": "PASS", "1.2": "PASS" },
    "pass2": { "2.1": "PASS", "2.2": "FAIL" },
    "pass3": { "3.1": "PASS" }
  },
  "blocking_issues": [{
    "dimension": "accuracy",
    "check_id": "2.2",
    "description": "Diagram shows 3 nodes but spec requires 4",
    "severity": "critical",
    "fix_hint": "Add fourth node labeled 'Validator' between 'Checker' and 'Output'"
  }],
  "suggestions": [{
    "dimension": "style",
    "description": "Arrow style is angular; other diagrams use curved arrows"
  }],
  "what_worked": [
    "Layout and composition are strong — keep the left-to-right flow"
  ],
  "escalation_reason": null,
  "quality_score": 0.72
}
```

**Quality score formula:** `(checks_passed / total_checks_run) × (pass_reached / 3)`

### Config
None

## Usage
Delegated by `cast-preso-illustration-creator` after generating an illustration.
Not invoked directly by the user.

## Examples
Input: Watercolor illustration + scene brief + style anchor
Output: Verdict JSON with CONTINUE, feedback on element count mismatch, praise for color palette
