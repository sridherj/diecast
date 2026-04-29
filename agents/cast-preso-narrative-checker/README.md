# cast-preso-narrative-checker

Validate a narrative document against the 14-item quality checklist.
Stage 1 checker agent for the presentation pipeline.

## Type
`diecast-agent`

## I/O Contract
- **Input:**
  - Path to `narrative.collab.md` (via delegation context)
  - Source material paths (for cross-referencing)
- **Output:**
  - Structured checker result (PASS/FAIL with per-item evidence)
  - On FAIL: structured feedback for the narrative maker
- **Config:** None

## Usage
Dispatched by `cast-preso-narrative` after narrative synthesis.
Not invoked directly by users.

## Examples
Input: narrative.collab.md for Cast v2
Output:
  verdict: FAIL
  score: 11/14
  failures:
    - criterion: "walk-away outcomes concrete"
      evidence: "Outcome 2 says 'understand the platform' — not specific enough"
      suggestion: "Change to 'understand how agents are composed from skills'"
