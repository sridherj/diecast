---
name: cast-preso-visual-toolkit
description: Shared visual toolkit for presentation agents — style tokens, slide archetypes, HTML/CSS templates, and conventions
---

# Presentation Visual Toolkit

A shared style reference and template library for all `cast-preso-*` agents. This is a **skill** (passive reference), NOT an agent. Every presentation agent reads this toolkit to produce visually consistent output.

## How to Reference Style Tokens

Load `visual_toolkit.human.md` (in this skill directory) for:
- CSS custom property color tokens and their default values
- Typography scale (font families, sizes, weights)
- Content density rules and slide dimension constraints
- Slide archetype catalog with when-to-use guidance
- Illustration style guide (Annie Ruygt watercolor default)

## How to Use Templates

Copy from `templates/slide-archetypes/{archetype}.html` and replace `{{PLACEHOLDER}}` values manually. Placeholders are for **agent copy-paste only** — they are NOT processed by any template engine (not Jinja, not Handlebars, not Mustache).

Available archetypes: `single-stat-hero`, `compare-contrast`, `timeline`, `diagram-annotated`, `code-showcase`, `consulting-exhibit`, `one-statement`, `illustrated-section-opener`, `build-up-sequence`, `title-slide`, `close-cta`.

## How to Use CSS

Reference `templates/css/` for consistent styling:
- `typography.css` — font families, sizes, weights, scale classes
- `grid-background.css` — subtle engineering-notebook grid overlay
- `components.css` — callout boxes, question annotations, nav elements, fragment animations

All CSS uses `var(--color-*)` tokens defined in `:root`. Override tokens per-presentation to change the color scheme globally.

## How to Use the Base Template

The assembler copies `base-template/` to the presentation's `assembly/` directory. It contains:
- `index.html` — HTML skeleton referencing theme.css and main.js
- `theme.css` — single source of truth for all CSS (tokens + typography + grid + components)
- `main.js` — Vite entry point (reveal.js init, callout mode logic, FOUC prevention)
- `vite.config.js` — Vite + vite-plugin-singlefile for self-contained HTML output
- `package.json` — dependencies (reveal.js ^5.1.0, vite ^6.0.0)

## Hard Rules

- **NEVER** hardcode hex color values — always use `var(--color-*)` tokens
- **NEVER** improvise a slide layout — pick a named archetype from the catalog in `visual_toolkit.human.md`
- **ALWAYS** use components from `templates/components/` for callouts and question annotations
- **NEVER** put template engine processing logic on `{{PLACEHOLDER}}` syntax — they are for manual agent copy-paste only
- **NEVER** drop `.reveal { font-size: 42px; }` from `theme.css`. Reveal.js core CSS does not set a base font-size — the `42px` default lives in `reveal.js/dist/theme/*.css`, which we do not import (it would clobber our design tokens). Without this declaration, `.reveal` inherits the browser default `16px` and every em-based slide value renders ~2.6× smaller than authored. All slide content in `templates/slide-archetypes/` is authored against the `42px` base.
- **NEVER** drop the section height + flex-center block from `theme.css` (the `.reveal .slides section.present { display: flex !important }` and `.reveal .slides section { height: 100%; flex-direction: column; justify-content: center; }` rules). Reveal.js core CSS leaves section height at `auto` (content-based). Any slide that uses percentage-based inner heights (`height: 70%`, `top: 62%`, etc.) assumes the section fills the 1920×1080 design canvas. Without these rules, the section collapses to content height and every percentage resolves relative to that collapsed box — causing content to overlap, clip, or drift. The `display: flex !important` on `.present` is required because reveal inline-sets `display: block`; the `!important` is the only way to override it. Natural-flow slides (no absolute positioning) get vertical centering from the flex column; positioned slides are unaffected because `position: absolute` children ignore the flex axis.

## Overflow Fixes: Content-First, Never Just Shrink Fonts

When a slide overflows the 1080px canvas, fix in this priority order. **Shrinking fonts below the floor is the last resort, not the first move.**

1. **Trim content** (first choice). The 6-element per-slide limit exists because the audience can't absorb more. Count elements in `slide.html` and drop the weakest ones. Fold two adjacent code panels into one with a dashed separator. Move supporting detail into `<aside class="notes">`.
2. **Split into two slides** (second choice). If trimming would damage the argument, make two slides. Prefer clarity over slide count.
3. **Tighten spacing** (third choice). Reduce padding and gaps 30–50% before touching fonts. Cards typically author at 14–16px padding but can render at 8–10px on appendix slides.
4. **Shrink fonts** (last resort). Only inside the floor rules in the next section.

## Font-Size Floors (WCAG + appendix waiver)

- **Core slides (s01–s11)**: minimum `0.57em` (≈24px ≈ 18pt, WCAG 2.1 AA). Non-negotiable — these are the body of the talk.
- **Appendix-density slides (a-prefix)**: minimum `0.5em` (≈21px ≈ 16pt). Waiver justified when the brief or an open-question artifact explicitly cites appendix-density precedent (a04, a12, a13 established this). The slide HTML must carry a header comment documenting the waiver: `<!-- Appendix density waiver: 0.5em floor (vs. 0.57em toolkit default) justified by a04/a12/a13 precedent. -->`.
- **Never below `0.5em`.** Anything smaller is unreadable on a projector at 20 feet.

### Nested-em trap

`font-size` is relative to the **parent's computed size**, not the `.reveal` base. `font-size: 0.85em` inside a `font-size: 0.5em` parent renders at `0.425em` against the base — below the floor. When authoring, compute the product against `.reveal`'s `42px` base before shipping. For nested spans that carry important text (badges, labels, inline pills), prefer absolute em values (`font-size: 1.0em` inside the 0.5em parent to stay at the floor) rather than relative shrinks.

## Recurring Overflow Patterns (checklist)

Four patterns cause most overflow bugs. Check these before shipping any text-heavy slide:

- **`position: absolute` source citations and footer strips overlap flex-centered content.** Switch to in-flow with `margin-top`. Absolute positioning assumes the section is a fixed 1080 box but the flex column rearranges natural-flow children above it. Seen in a09, a13.
- **Default `h2` (`1.6em` = 67px) wraps slide titles on text-heavy slides.** Override to `font-size: 1.0em`–`1.1em` with tight `line-height: 1.15`–`1.25` on the `.slide-title` element. Any title longer than ~8 words at `1.6em` is a candidate.
- **Card and grid padding authored for print renders too generous on 1920×1080.** Tune down 30–50% on appendix slides (e.g., `padding: 16px` → `10px`; `gap: 16px` → `10px`).
- **`grid-template-columns: 1fr 1fr` allows children to push out on long content.** Use `minmax(0, 1fr)` on every column to clip overflow at the column edge rather than the slide edge. Seen in a08.

## Authoring Scale (Critical)

All em-based font-sizes in slide HTML are relative to the `42px` base on `.reveal`. Examples:
- `font-size: 0.55em` → 23.1px at design scale (code/captions)
- `font-size: 0.85em` → 35.7px (callout body text)
- `font-size: 1.25em` → 52.5px (emphasized statement lines)
- `font-size: 2.5em` → 105px (slide-title h1)

When authoring or debugging a slide, verify in a browser that `.reveal { font-size }` is `42px` and `.reveal .slides` inherits it. If either is `16px`, the base is missing and every em-declaration is silently wrong.

## Directory Layout

```
.claude/skills/cast-preso-visual-toolkit/
  SKILL.md                          ← you are here
  visual_toolkit.human.md           ← style tokens + archetype catalog
  templates/
    css/
      typography.css
      grid-background.css
      components.css
    components/
      callout-box.html
      question-annotation.html
    slide-archetypes/
      single-stat-hero.html
      compare-contrast.html
      timeline.html
      diagram-annotated.html
      code-showcase.html
      consulting-exhibit.html
      one-statement.html
      illustrated-section-opener.html
      build-up-sequence.html
      title-slide.html
      close-cta.html
  base-template/
    index.html
    theme.css
    main.js
    vite.config.js
    package.json
```
