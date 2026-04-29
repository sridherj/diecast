# SVG Generation Specification

## ViewBox and Sizing

All SVG illustrations use a standard viewBox for consistency:

```
viewBox="0 0 720 380"
```

- Coordinate grid: X range 0-720, Y range 0-380
- Left margin at x=80, right margin at x=640
- Top margin at y=40, bottom margin at y=340
- Safe content area: 560×300

## Typography

| Element | Font | Size |
|---------|------|------|
| Titles | "IBM Plex Mono", monospace | 18px |
| Labels | "DM Sans", sans-serif | 13px |
| Annotations | "DM Sans", sans-serif | 11px |

Always specify `text-anchor` and `dominant-baseline` on every `<text>` element.

## Stroke and Spacing

- Outlines: 1.5px stroke
- Accent strokes: 2px stroke
- Secondary strokes: 1px stroke
- Minimum spacing: 20px between text elements
- Padding inside rects: 12px minimum

## Color Rules

Use CSS class names ONLY — no inline hex values:
- `fill-bg` — background fill
- `fill-accent` — primary accent
- `fill-secondary` — secondary elements
- `stroke-primary` — primary stroke
- `stroke-muted` — secondary stroke

These map to the visual toolkit's CSS custom properties.

## Structural Rules

- No nested transform groups deeper than 2 levels
- Keep labels under 30 characters (SVG has no line-wrapping)
- Keep distinct visual elements to ≤ 5 per SVG
- If more needed: generate separately and composite, or use grouped sub-elements
- Specify exact coordinates for critical elements (LLMs treat coordinates as characters, not numbers)

## Common Problems and Fixes

| Problem | Fix |
|---------|-----|
| Elements overlap | Increase spacing between coordinates by ≥ 40px |
| Text cut off | Reduce font size or shorten label; check text-anchor alignment |
| Arrows misaligned | Use explicit start/end coordinates, not relative offsets |
| Inconsistent stroke weights | Use CSS classes instead of inline stroke-width |
| Missing viewBox | Always include viewBox="0 0 720 380" on the root `<svg>` |

## Post-Processing

If SVGO is available, optimize with:
- Preserve: `<title>`, `aria-*`, `class` attributes
- Remove: comments, metadata, editor cruft
- Do NOT remove: class names, id attributes used for styling

## SVG Iteration Expectation

Expect 2-5 iterations for ANY SVG. First pass from an LLM almost always needs coordinate corrections. This is normal — do not escalate early for SVG coordinate fixes.
