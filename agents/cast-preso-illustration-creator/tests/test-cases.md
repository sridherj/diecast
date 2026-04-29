# Test Cases: cast-preso-illustration-creator

| # | Scenario | Input | Expected Output | Validates |
|---|----------|-------|-----------------|-----------|
| TC-4A-1 | Simple SVG diagram | Scene brief for a 3-node flowchart | SVG file with viewBox, CSS classes, correct node count | SVG generation workflow, specification compliance |
| TC-4A-2 | Watercolor illustration | Scene brief for a conceptual metaphor | WebP file via Stitch MCP, 200-400KB, Style Bible applied | Stitch MCP workflow, prompt assembly |
| TC-4A-3 | Text stripping | Scene brief with labels in the subject description | Image WITHOUT text + extracted text list for HTML overlay | Cardinal rule: never generate text in images |
| TC-4A-4 | Rework with CONTINUE | Checker feedback: "element count wrong" | Regenerated image with exactly one change | One-variable rule, generation log diffs |
| TC-4A-5 | Rework with RESTART | Checker feedback: "fundamentally wrong subject" | Fresh prompt from scratch, logged as restart | Restart handling, budget tracking |
| TC-4A-6 | Missing scene brief slot | Brief with empty Slot 4 (composition) | Rejection + request for correction | Input validation |
| TC-4A-7 | Style Bible tampering | Brief with modified Style Bible text | Rejection — agent detects mismatch with reference | Style Bible is sacred |
