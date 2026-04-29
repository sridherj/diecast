# Presentation Visual Toolkit

> The single authoritative style reference for all `cast-preso-*` agents.
> The maintainer owns this file. All agents read it. Do not edit programmatically.

---

## Section 1: Style Tokens

Every color in the system is a CSS custom property. Override `:root` to theme a presentation.

| Token | Default Value | Usage |
|-------|---------------|-------|
| `--color-bg` | `#F5F4F0` | Warm cream paper background |
| `--color-text` | `#1A1A28` | Deep navy-black primary text |
| `--color-muted` | `#4A4860` | Grey secondary text |
| `--color-surface` | `#ECEAE4` | Slightly darker cream for cards/boxes |
| `--color-accent` | `#D6235C` | Raspberry accent (configurable per presentation) |
| `--color-callout-bg` | `rgba(214, 35, 92, 0.06)` | Accent at 6% opacity |
| `--color-callout-border` | `var(--color-accent)` | Accent color |
| `--color-question-bg` | `rgba(74, 72, 96, 0.06)` | Muted at 6% opacity |
| `--color-question-border` | `var(--color-muted)` | Muted color |
| `--color-selection-bg` | `var(--color-accent)` | Text selection background |
| `--color-selection-text` | `#FFFFFF` | Text selection foreground |
| `--color-link` | `var(--color-accent)` | Link color |
| `--color-link-hover` | darkened accent | Link hover color |

---

## Section 2: Typography

**Font stacks:**
- Headings: `'IBM Plex Mono', 'SF Mono', 'Fira Code', monospace`
- Body: `'DM Sans', system-ui, sans-serif`

**Base font size:** 32px (reveal.js default)

**Typography scale:**

| Element | Font Stack | Size | Weight | Color Token |
|---------|-----------|------|--------|-------------|
| Slide title | Heading | 1.6em | 700 | `--color-text` |
| L1 body | Body | 1.1em | 600 | `--color-text` |
| L2 body | Body | 0.9em | 400 | `--color-muted` |
| Callout number | Heading | 1.3em | 700 | `--color-accent` |
| Callout text | Body | 0.9em | 500 | `--color-text` |
| Source/citation | Body | 0.5em | 400 | `--color-muted` |
| Nav marker | Heading | 0.5em | 400 | `--color-muted` |

**Notes:**
- Use `r-fit-text` (reveal.js built-in) for auto-scaling large text (hero stats, one-statement slides)
- All heading sizes: h1 = 2.5em, h2 = 1.6em, h3 = 1.3em, h4 = 1.0em
- Letter-spacing on headings: -0.02em for tighter monospace tracking

---

## Section 3: Grid Background

Subtle grid lines inspired by derekherman.co — engineering notebook feel.

- Grid line color: `var(--color-muted)` at 3–4% opacity
- Grid spacing: 40px
- Implementation: two overlapping `linear-gradient` on `.reveal`
- Print override: `background-image: none` for clean PDF export

The grid creates a sense of precision and structure without competing with content. It should be barely perceptible — if someone asks "is there a grid?", you got it right.

---

## Section 4: Navigation Conventions

- **Core flow:** horizontal (left/right arrows)
- **Appendix:** vertical stacks (down to enter appendix, right to skip past it)
- **Deep-dive links:** `href="#/{id}"` — NEVER use numeric indices (they break when slides are reordered)
- **Back-links:** every appendix slide links back to its parent core slide
- **Nav marker:** terminal-style cursor (e.g., `>cast_`) positioned bottom-right, using heading font at 0.5em, muted color at 50% opacity

---

## Section 5: Slide Dimensions & Content Rules

- Author at **1920×1080**, reveal.js scales automatically to viewport
- Every slide fits one viewport without scrolling
- Bullet-based content, not prose (exceptions: hero stat context line, close/CTA)
- **One idea per slide**

**Hard limits:**
- Max 50 words body text per slide
- Max 15 words per bullet
- Max 6 visual elements per slide (Miller's Law)
- Max 6 fragment steps per slide
- Min 30% whitespace per slide
- Min 18pt font equivalent (WCAG 2.1 AA)

**Action titles:** Complete sentences with verbs, not labels. "Revenue grew 47% — 3x our forecast" not "Q3 Revenue". The validation test: can someone read ONLY the titles and understand the full argument?

---

## Section 6: Callout Box Styles

Numbered callout boxes with accent-colored left border. Used for presenter assertions/facts.

**Visual spec:**
- Flex layout, 16px gap between number badge and text
- 4px left border in `var(--color-callout-border)`
- Background: `var(--color-callout-bg)`
- 8px border-radius on right side (0 on left, flush with border)
- Padding: 16px 20px
- Number badge: 28px circle, `var(--color-accent)` background, white text, heading font, weight 700
- Text: body font, 0.85em, weight 500, line-height 1.4

**Three animation modes:**

| Mode | Trigger | Behavior | CSS Class |
|------|---------|----------|-----------|
| `manual` (default) | Click/spacebar | Callouts appear as standard reveal.js fragments | (none — default fragment behavior) |
| `automatic` | Timer | Callouts auto-advance on 2s intervals | `body.timed-animations` (JS-driven) |
| `none` | Instant | All callouts visible immediately | `body.no-animations` |

**Mode selection:** Set via URL parameter `?callout=manual|automatic|none` or JavaScript variable `CALLOUT_MODE`.

**Automatic mode implementation:**
- Primary: set `data-autoslide="2000"` on callout fragment elements
- Fallback (if `data-autoslide` per-fragment not supported in reveal.js 5.x): use `Reveal.on('fragmentshown')` callback with `setTimeout(() => deck.next(), 2000)` for callout fragments
- The `.timed-animations` body class is JS-driven only — no CSS visual indicator needed

---

## Section 7: Question Annotation Styles

Similar to callouts but for audience perspective — "you might be wondering..." or pain-point probes.

**Visual spec:**
- Flex layout, 12px gap
- 4px left border in `var(--color-question-border)`
- Background: `var(--color-question-bg)`
- 8px border-radius on right side
- Padding: 12px 16px
- Icon: `?` character, 1.2em, `var(--color-muted)`, flex-shrink: 0
- Text: body font, 0.8em, italic, `var(--color-muted)`, line-height 1.4

**When to use questions vs callouts:**
- Callouts = assertions/facts the presenter makes
- Questions = audience perspective / pain-point probes
- Questions are visually quieter (muted border, italic text) — they voice the audience's internal monologue

**Same three animation modes as callouts** (manual/automatic/none), controlled by the same URL parameter.

---

## Section 8: Illustration Style Guide

**Default style:** Annie Ruygt watercolor (as seen on Fly.io blog)

**Style Bible approach:** A fixed style prefix is prepended verbatim to every image generation prompt. This prevents style drift across illustrations in a deck.

**Style Bible template** (fill per-presentation):
```
Style: [e.g., "Warm watercolor illustration in the style of Annie Ruygt.
Soft washes of color with visible brush strokes. Muted earth tones with
pops of [accent color]. Hand-painted feel, slightly loose edges.
Editorial illustration style, not photorealistic."]
```

**Fixed exclusions** (always appended):
```
DO NOT include: photorealistic rendering, 3D effects, glossy surfaces,
stock photo aesthetic, clip art style, corporate Memphis style,
text/words/labels within the illustration.
```

**Image format:**
- Watercolor/raster: WebP lossy (quality 80–85)
- Diagrams/technical: SVG
- File budget: 200–400KB per image, under 10MB total deck

**Text in illustrations:** Prefer overlay text in HTML. Never ask the image generator to render text — it will fail or look bad.

**Stitch MCP rule:** When using Stitch to generate images, ALWAYS include "create an IMAGE FILE, not a webpage" in the prompt. Stitch defaults to generating web pages otherwise.

---

## Section 9: Slide Archetype Catalog

Every content slide MUST use a named archetype from this catalog. No improvised layouts.

### Archetype 1: Single-Stat Hero

**When to use:** Hook or Reveal slides. One massive number tells the entire story. Opening a section for emotional impact, or landing a punchline after a complex sequence.

**Density limits:** Exactly 1 metric/number. 1 context sentence. Zero bullets, diagrams, or images. Min 60% whitespace.

**Template:** `templates/slide-archetypes/single-stat-hero.html`

**Checker criteria:**
- Exactly one metric/number on slide
- Number font size >= 3x body text (uses `r-fit-text` or ~8em)
- Context sentence is "so what" not label (contains comparison, delta, or implication)
- >= 60% whitespace

### Archetype 2: Compare/Contrast

**When to use:** Reveal or Information slides. Side-by-side comparison — before/after, problem/solution, old/new. The contrast IS the insight.

**Density limits:** Strict visual symmetry. Max 5 attributes per side. Action title states conclusion.

**Template:** `templates/slide-archetypes/compare-contrast.html`

**Checker criteria:**
- Exactly two visual columns (or clear binary structure)
- Visual symmetry between columns (same element count, same sizing)
- Color coding: warm=problem/before, cool=solution/after
- Action title states conclusion, not topic

### Archetype 3: Timeline/Progression

**When to use:** Information or Hook slides. Temporal sequences — roadmaps, evolution, phased rollouts. Hook variant: timeline reveals a surprising trajectory.

**Density limits:** Max 5–7 milestones. Each milestone has a brief label, not a paragraph.

**Template:** `templates/slide-archetypes/timeline.html`

**Checker criteria:**
- <= 7 milestones visible at once
- Clear temporal direction (left-to-right)
- Each milestone is a brief label
- Phase states are visually distinguishable (color/opacity)

### Archetype 4: Diagram-with-Annotations

**When to use:** Information or Reveal slides. Architecture walkthroughs, system diagrams, any complex visual needing guided interpretation.

**Density limits:** Diagram occupies 60–70% of slide. Max 6–8 annotations at 5–10 words each.

**Template:** `templates/slide-archetypes/diagram-annotated.html`

**Checker criteria:**
- Diagram fills >= 60% of slide area
- Each annotation is <= 10 words
- Annotations numbered and match fragment order
- No more than 6–8 annotations
- Build-up sequence is logical

### Archetype 5: Code-Snippet Showcase

**When to use:** Information or Reveal slides. API usage, implementation patterns, before/after refactoring. The code itself may be the surprise.

**Density limits:** Max 15 lines visible. Dark code theme. Line highlighting used to focus on key lines.

**Template:** `templates/slide-archetypes/code-showcase.html`

**Checker criteria:**
- Code block uses dark background theme
- <= 15 lines visible
- Line highlighting is used (not just a wall of code)
- Action title explains what the code demonstrates
- If step-through: each highlighted section is a coherent thought

### Archetype 6: Consulting Exhibit

**When to use:** Information or Reveal slides. Executive audiences, data-driven arguments. McKinsey/BCG/Bain convention: action title + evidence body + source line.

**Density limits:** Title max 15 words (complete sentence). Body: chart/table/structured bullets with bold leads. Source line required for data claims.

**Template:** `templates/slide-archetypes/consulting-exhibit.html`

**Checker criteria:**
- Title is a complete sentence (contains a verb)
- Title makes a claim, not a label
- Body provides evidence supporting the title claim
- Source line present for any data claim
- <= 15 words in the title

### Archetype 7: One-Statement (Takahashi)

**When to use:** Hook, Moment, or Reveal slides. Single bold phrase fills the viewport. Section openers, thesis statements, emotional anchors, breathing moments after dense content.

**Density limits:** Exactly one sentence/phrase. Zero supporting elements. Text fills 50–80% of viewport. Optional small muted subtitle.

**Template:** `templates/slide-archetypes/one-statement.html`

**Checker criteria:**
- Exactly one sentence or phrase
- No supporting elements (bullets, images, diagrams)
- Text fills >= 50% of viewport width (uses `r-fit-text`)
- Statement is specific, not generic

### Archetype 8: Illustrated Section Opener

**When to use:** Moment slides. Full-bleed illustration as section divider. Creates a breathing moment and sets emotional tone. Use sparingly (3–5 per deck).

**Density limits:** Illustration >= 80% of slide. Text overlay <= 5 words. Illustration must be thematically specific, not decorative generic.

**Template:** `templates/slide-archetypes/illustrated-section-opener.html`

**Checker criteria:**
- Illustration fills >= 80% of slide
- Text overlay is <= 5 words
- Illustration is thematically connected (not decorative generic)
- Style is consistent with other illustrations in the deck

### Archetype 9: Build-Up Sequence

**When to use:** Information or Reveal slides. Arguments that build on each other, process steps, ordered lists. The final element may be the surprise.

**Density limits:** Max 5–6 fragment steps. Each fragment is a complete thought. Uses `fade-in-then-semi-out` for all but last item.

**Template:** `templates/slide-archetypes/build-up-sequence.html`

**Checker criteria:**
- Uses `fade-in-then-semi-out` (not plain fragment) for all but last item
- <= 6 fragment steps
- Each fragment is a complete thought
- Final state (all visible) makes sense as a static slide

### Additional Templates (not archetypes, but needed)

**Title Slide** — `templates/slide-archetypes/title-slide.html`
Opening slide with presentation title, subtitle, nav marker. Left-aligned, full-height flex.

**Close/CTA Slide** — `templates/slide-archetypes/close-cta.html`
Closing slide with CTA text and contact info. Center-aligned, accent-colored monospace for contact.

---

## Section 10: Design Token Override Pattern

Each presentation can customize the color scheme by overriding `:root` CSS variables. The toolkit provides structure and patterns, not hardcoded values.

**Override example:**
```css
:root {
  --color-accent: #2563EB;  /* Switch from raspberry to blue */
  --color-callout-bg: rgba(37, 99, 235, 0.06);
  --color-callout-border: var(--color-accent);
}
```

**How it works:**
1. `theme.css` defines default token values in `:root`
2. The assembler inserts a presentation-specific `<style>` block AFTER the theme
3. CSS cascade ensures overrides win
4. All components use `var(--color-*)` so they update automatically

**What can be overridden:** Any token in Section 1. Most common: `--color-accent` (per-brand color).

**What should NOT be overridden:** `--color-bg`, `--color-text` (the warm cream + dark navy is the design identity). Override these only for a fundamentally different aesthetic.
