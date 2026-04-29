# cast-preso-compliance-checker

Final verification of the assembled presentation against the Stage 1 narrative spec.
Checks per-slide outcomes, narrative flow, walk-away outcomes, consumption mode fit,
navigation integrity, technical rendering, and planning leakage.

## Type
`taskos-agent`

## I/O Contract

### Input
- **Assembled presentation:** `assembly/index.html` (or `assembly/src/index.html` pre-build)
- **Narrative doc:** `narrative.collab.md` — the Stage 1 spec to verify against
- **Per-slide WHAT docs:** `what/{slide_id}.md` — for per-slide outcome verification
- **Notes summary:** `assembly/notes_summary.collab.md` — assembler's collected notes

### Output
Written to `presentation/assembly/`:
- `compliance_report.collab.md` — Full compliance report with pass/fail per check
- `routing_recommendations.md` — If failures found: specific agent + slide routing instructions

### Config
None (stateless)

## Usage
Dispatched via HTTP delegation from orchestrator:
```
POST /api/agents/cast-preso-compliance-checker/trigger
```

## Delegates To
None (leaf agent — routing recommendations returned to orchestrator for dispatch)

## Examples
Input: assembly/index.html + narrative.collab.md + 10 what/*.md docs
Output: compliance_report.collab.md (8 passes, per-check verdicts), routing_recommendations.md (if failures)
