---
id: Q-05
topic: Stale-edit detection after source regeneration
stage: what
blocking: true
---
## Context

If a maker agent regenerates Stage-2 WHAT after SJ has edited a slide, his
saved edits in `localStorage` may no longer map to the regenerated slide
blocks. See `docs/plan/2026-04-17-preso-editable-preview.md:252-258`.

## Recommended

- **Option A — Hash source, offer "carry forward / archive" on mismatch:**
  Cheap (one SHA per input file). SJ keeps control. Matches the user's
  pattern of iterating multiple rounds per stage. Reference:
  `docs/plan/2026-04-17-preso-editable-preview.md:256`.

## Alternatives

- **Option B — Silently discard stale edits:**
- **Option C — Silently keep and re-apply by block ID:**

## References

- `docs/plan/2026-04-17-preso-editable-preview.md:252-258`
