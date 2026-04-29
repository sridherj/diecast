# Visual Gold Standards — Reference for check-visual

Calibration examples for the check-visual agent. Describe what good looks like so the checker can anchor its quality bar. Updated alongside the visual toolkit.

## Exemplary Slides (Aspirational)

### 1. Apple Keynote — Single-Stat Hero

**Example:** "1 billion active devices." (Tim Cook, 2021)

- Layout: massive number centered, single contextualizing sentence below
- Background: matte black
- Number: huge — fills ~40% of viewport vertically, San Francisco Display typography
- No decoration, no logo, no chrome
- Single takeaway identifiable in <1 second

**Why it works:** Specificity and restraint. One number, one sentence, nothing else. Audience cannot miss the point.

**What to look for in generated slides:** Does the hero element dominate? Is there supporting context that doesn't compete? Is the background clean (no decoration fighting for attention)?

---

### 2. Stripe — Documentation/Product Pages

**Example:** docs.stripe.com API reference pages

- Whitespace: ~50% of viewport — generous, confident
- Typography: monospace code blocks, clean sans-serif prose
- Palette: restrained to 2-3 colors (blurple, near-black, light gray)
- Data tables: minimal borders, tight row spacing, no alternating row colors
- Code samples: syntax-highlighted with muted tones, never rainbow

**Why it works:** Whitespace is the design. Stripe's product pages feel expensive and precise because they resist filling space.

**What to look for:** Is whitespace >30%? Are color choices restrained? Is the palette coherent across elements?

---

### 3. Linear — Changelog / Product Pages

**Example:** linear.app/changelog

- Dark mode with warm dark gray (not pure black)
- Typography hierarchy: bold feature names as headlines, muted descriptions beneath
- Iconography: clean line icons, consistent weight
- Strong vertical rhythm — everything snaps to a baseline grid
- Accent: a single vibrant color (purple) used sparingly for CTAs and highlights

**Why it works:** Typography-first design. Every element has an intentional place in the hierarchy. No decoration.

**What to look for:** Is there a clear typographic hierarchy? Are icons consistent in weight and style? Is the accent color used sparingly or scattered?

---

### 4. derekherman.co — Editorial/Paper Feel

**Example:** derekherman.co's homepage and essays

- Cream/warm off-white background (not pure white) — `#FAFAF7` or similar
- IBM Plex Mono for headings — editorial, typewriter-adjacent
- IBM Plex Sans for body — clean, readable
- Subtle grid overlay — feels like architectural paper
- Asymmetric layouts with intentional negative space
- Warm accent colors (not cool blues) — orange, ochre, muted red

**Why it works:** Editorial rigor. Feels like something printed, not generated. Reads as a designer's work, not a template.

**What to look for:** Warm (not cool) palette? IBM Plex typography? Intentional asymmetry vs. centered/balanced? Grid feel?

---

### 5. Cast v1 Thesis Microsite — Internal Reference

**Example:** `taskos/goals/taskos-gtm/thesis_microsite/index.html` (if available)

- Fly.io-adjacent editorial feel (inspired by Annie Ruygt's illustration style)
- Warm palette with watercolor illustrations
- Single-column flowing layout with occasional full-bleed illustration moments
- Handwritten annotations and editorial accents
- Numbers always concrete, never rounded for effect

**Why it works:** Internal reference point — this is the aesthetic SJ wants the presentation agents to produce by default.

**What to look for:** Watercolor illustration style (Annie Ruygt influence)? Warm palette consistent with the visual toolkit? Concrete numbers? Editorial (not corporate) voice?

---

### 6. Tufte — Information-Dense Without Clutter

**Example:** Edward Tufte's *Visual Display of Quantitative Information* sample pages

- High data-ink ratio — every mark communicates information
- Small multiples: many small charts tiled to enable comparison
- Minimal gridlines, no 3D effects, no unnecessary color
- Sparklines embedded inline with prose

**What to look for:** When the slide shows data, does every mark earn its place? Are gridlines minimal? Is there a clear data-to-chart-junk ratio?

---

### 7. Apple Keynote — The Aha Moment

**Example:** Steve Jobs revealing the original iPhone silhouette (2007)

- Full-bleed image of a single object on a black background
- No chrome, no title, no subtitle — just the image and the pause
- Reveal slides don't need text to deliver the moment

**What to look for:** For reveal-type slides, is the visual doing the talking? Does it create a pause?

---

### 8. Fly.io — Documentation with Illustration

**Example:** fly.io documentation and blog posts

- Annie Ruygt watercolor illustrations at the top of major sections
- Warm palette: burnt orange, cream, charcoal
- Code blocks with restrained syntax highlighting
- Pull-quotes and callouts styled as handwritten notes

**What to look for:** Illustration style consistent with Annie Ruygt watercolor (warm, hand-drawn feel)? Palette warm (not cool)?

---

## Anti-Examples (Generic AI Patterns to FAIL)

### A1: Title + Bullets + Image-Right

- Title bar at top
- 3 equally-sized bullets on the left half
- Stock-style illustration occupying the right half with no relation to the bullets

**Why it fails:** This is the AI default. Every content slide looks the same regardless of content type. No intentional archetype chosen.

---

### A2: Symmetric Icon Grid

- 4 (or 6, or 8) icons arranged in a grid
- Each icon paired with a short label
- All boxes equal size, equal spacing
- Icons in uniform outline style

**Why it fails:** Corporate consultant deck aesthetic. No hierarchy. Every item is given equal weight, so the audience has to guess which matters.

---

### A3: Gradient Buttons + Clip-Art Diagrams

- Beveled/gradient buttons (Material Design excess)
- Generic "Before/After" clip-art diagrams
- Box-and-arrow flowcharts with rounded corners
- Corporate blue/teal palette
- Stock-photo imagery of people in suits

**Why it fails:** Reads as AI-generated or PowerPoint-template. No specificity, no intentional design choices. The opposite of the Annie Ruygt / Fly.io aesthetic.

---

## Calibration Rules for the Checker

When evaluating a slide against these gold standards:

1. **Specificity test:** Does this slide choose a specific archetype and commit to it? If you can't name the archetype, FAIL `not-generic`.
2. **Whitespace test:** Compare to Stripe — does it feel confident (>30% whitespace) or cramped?
3. **Palette test:** Compare to the visual toolkit tokens — warm palette (orange, cream, charcoal), not cool (blue, teal, purple).
4. **Typography test:** Is there a clear hierarchy (like Linear), or do elements compete?
5. **Illustration test:** Does it integrate like Fly.io (functional, on-style), or float like an A1 stock image (decorative, disconnected)?

When in doubt, ask: "Would this slide look out of place at an Apple keynote or on Stripe's product pages?" If yes, FAIL.
