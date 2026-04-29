# Failure Routing Matrix

| Failure Type | Routes To | Rationale |
|---|---|---|
| Slide doesn't meet stated outcome | `cast-preso-how` for that slide | Content issue — slide needs rework |
| Action title is weak/generic | `cast-preso-how` for that slide | Title is part of slide content |
| Narrative flow breaks between slides | `cast-preso-how` for transition slide | Content doesn't bridge correctly |
| Slide ordering wrong | `cast-preso-assembler` | Assembler controls ordering |
| Walk-away outcome not achieved (slide fix) | `cast-preso-how` for contributing slides | Strengthen specific slides |
| Walk-away outcome not achieved (structural) | **Escalate to the user** | May require narrative-level rethinking |
| Consumption mode mismatch | `cast-preso-how` for specific slides | Detail level needs adjustment |
| Core flow exceeds 12 slides | **Escalate to the user** | Scope decision |
| Deep-dive link broken | `cast-preso-assembler` | Navigation wiring issue |
| Back-link broken | `cast-preso-assembler` | Navigation wiring issue |
| Broken images / paths | `cast-preso-assembler` | Path rewriting issue |
| External CDN reference | `cast-preso-assembler` | Bundling issue |
| SVG rendering issue | `cast-preso-how` for that slide | SVG generated in Stage 3 |
| Planning leakage text | `cast-preso-how` for that slide | Content cleanup |
| Fragment index gaps | `cast-preso-assembler` | Assembly-time issue |

## Rework Budget

Max 3 compliance iterations. After 3 rounds, escalate to the user.
If iteration N finds MORE issues than N-1 (regression), escalate IMMEDIATELY.

## Routing Output Format

Write per-failure rows to `routing_recommendations.md`:

```markdown
| # | Route To | Target (slide_id or "global") | Specific Instruction | Severity |
|---|----------|-------------------------------|-----------------------|----------|
| 1 | cast-preso-how | 02-problem | Rewrite action title as assertion, not label | Critical |
| 2 | cast-preso-assembler | global | Deep-dive link `#/missing-id` resolves nowhere | High |
```

The orchestrator uses this table to dispatch rework agents in parallel where safe.
