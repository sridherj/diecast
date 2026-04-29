---
id: Q-04
topic: Export format for annotations (P2 pins)
stage: how
blocking: false
---
## Context

Pin exports in P2 could be freeform markdown or structured JSON. Evidence:
`docs/plan/2026-04-17-preso-editable-preview.md:244-251`.

## Recommended

- **Option A — Markdown in P2, JSON layered in by P4:** Ship the readable form
  when the user is the consumer. Matches `docs/plan/2026-04-17-preso-editable-preview.md:248`.

## Alternatives

- **Option B — JSON from day one, render markdown from JSON:** Generally
  better for machine-consumption but slower to ship. Rationale intentionally
  omits any reference — should trigger the "ungrounded option" warning.
- **Option C — Both formats from P2:** Doubles the export surface. See
  `docs/plan/2026-04-17-preso-editable-preview.md:250`.

## References

- `docs/plan/2026-04-17-preso-editable-preview.md:244-251`
