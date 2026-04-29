---
id: Q-06
topic: Color palette for the decision card accent
stage: any
blocking: false
---
## Context

We haven't decided what accent color the decision card should use. Is Cast
magenta too loud for a review surface? This paragraph deliberately references
no artifact files, so the "premature question" warning should fire: the
framing was done before anyone read the existing styles.

## Recommended

- **Option A — Cast magenta accent:** Matches the P0 preview look.
  Reference: `agents/cast-preso-review/static/review.css:5-22`.

## Alternatives

- **Option B — Muted slate accent:** Would fade into the page surface.
  Reference: `agents/cast-preso-review/static/review.css:14-16` (neutral
  surface tokens already defined).
- **Option C — Keep neutral (no accent):** Consistent with a "review, not
  present" surface. Reference: `agents/cast-preso-review/template.html`.

## References

- `agents/cast-preso-review/static/review.css`
- `agents/cast-preso-review/template.html`
