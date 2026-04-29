# HTML Generation Rules

> Loaded by `cast-preso-how` at Step 6 (HTML generation).
> Source: `docs/exploration/playbooks/02-revealjs-implementation.ai.md` (HTML patterns) + `04-slide-design-patterns.ai.md` (density rules, fragment strategy).
>
> **Starting point:** Always copy from `.claude/skills/cast-preso-visual-toolkit/templates/slide-archetypes/{archetype}.html`. Never write reveal.js from scratch.

## 1. Mandatory `<section>` Structure

```html
<section id="{slide_id}" data-state="{optional}">
  <h2>{Action title — complete sentence from the brief}</h2>
  <div class="slide-content">
    <!-- Content following archetype layout -->
    <!-- Fragments with data-fragment-index matching the brief's plan -->
  </div>
  <!-- Deep-dive link if this slide has appendix content -->
  <a href="#/{slide_id}-detail" class="deep-dive-link">Deep-dive: {topic} ></a>
  <aside class="notes">
    {Speaker notes from the brief}
    Timing: ~{N} seconds.
  </aside>
</section>
```

## 2. Hard Rules

1. **No hardcoded colors.** Use CSS variables from the visual toolkit (`var(--color-accent)`, `var(--r-heading-font)`). If a needed token doesn't exist, log an open question — do not invent one.
2. **Callout boxes use `class="fragment custom callout-appear"`** so they animate in via the toolkit's `components.css` rules.
3. **Default fragment class is `fade-in-then-semi-out`** for build-up lists. This matches the toolkit's components.css.
4. **Inline SVG sizing.** Use `viewBox` with percentage widths. NEVER fixed pixel dimensions on the SVG element. Wrap in `<div class="r-stretch">` for full-height SVG.
5. **Image references** use `assets/{filename}` with relative paths. Never absolute paths or external URLs (would break self-contained bundling).
6. **Single-screen rule.** Every slide must fit 1920×1080 without scrolling. If content overflows, the slide has too much — split it or move detail to the appendix.
7. **Action title required.** `<h2>` must be a complete sentence with a verb. Labels like "Architecture" or "Overview" are forbidden (see action title examples below).
8. **Density limits.** Max 50 words of body text per slide. Max 6 content elements (cards, callouts, list items). Max 6 fragment steps.

## 3. Illustration Placeholder Pattern

When the brief says illustration is needed but the asset hasn't been generated yet (or when illustration-creator isn't available), use this placeholder so the slide renders with a visible TODO marker:

```html
<!-- Placeholder: illustration-creator will generate this -->
<img src="assets/{slide_id}-hero.webp"
     alt="{description from brief}"
     style="width: 80%; height: auto; display: block; margin: 0 auto;">
```

After illustration-creator returns:
- For watercolor (raster): leave the `<img>` element, point `src` at the generated file.
- For inline SVG: replace the entire `<img>` element with the returned `<svg>` markup. Preserve the parent positioning wrapper.

## 4. Version A/B Rules

When the brief contains a Version A/B section:
- Write `versions/version-a.html` and `versions/version-b.html` (full `<section>` for each).
- Copy the recommended version (Version A) verbatim to `slide.html`.
- Add a comment at the top of `slide.html`: `<!-- Recommended Version A. See versions/ for alternatives. -->`

## 5. Fragment Strategy Defaults by Slide Type

| Slide Type | Fragment Strategy | Rationale |
|-----------|-------------------|-----------|
| `hook` | Minimal (1-2 max) | Land the hook fast — anticipation comes from CONTENT, not animation |
| `reveal` | Fragment the reveal itself | Build anticipation, then show — the click IS the moment |
| `moment` | NO fragments | The whole slide IS the message — fragments break the pause |
| `information` | `fade-in-then-semi-out` for build-up; progressive build for diagrams | Walk the audience through; previous items stay visible but recede |

## 6. Action Title Enforcement

| BAD (label) | GOOD (action title) |
|-------------|---------------------|
| "Overview" | "Three patterns explain 90% of agent failures" |
| "Key Metrics" | "Latency dropped 4x after migration" |
| "Architecture" | "The orchestrator routes requests to the right agent in < 10ms" |
| "Agent Resume" | "Every agent has a resume — capabilities, contract, performance" |
| "Results" | "Conversion lifted 23% across all 4 funnels" |
| "Background" | "Manual outreach takes 12 hours per qualified lead" |

**Self-check before writing `<h2>`:**
1. Does the title contain a verb?
2. Could a reader infer the slide's claim from JUST the title?
3. Would removing the title leave a generic stock-photo deck?

If any answer is no, the title is a label, not an action title. Rewrite it.

## 7. Auto-Animate Pattern (Hook → Reveal Pairs)

For hook/reveal pairs that morph (e.g., old code → new code), use two consecutive `<section>` elements with matching `data-id` attributes:

```html
<section data-auto-animate id="hook-old-code">
  <h2>Manual SQL queries took 200 lines and 4 hours</h2>
  <pre data-id="code-block"><code data-trim>
  SELECT * FROM connections WHERE ...
  -- 200 more lines
  </code></pre>
</section>

<section data-auto-animate id="reveal-new-code">
  <h2>Natural language now does the same in 1 line</h2>
  <pre data-id="code-block"><code data-trim>
  /search "Show me ML engineers in SF I've worked with"
  </code></pre>
</section>
```

Reveal.js animates between them automatically. The matching `data-id` is what triggers the morph.

## 8. Deep-Dive Link Placement

If the brief indicates this slide has appendix content:
- Add the deep-dive link AFTER `.slide-content` and BEFORE `<aside class="notes">`.
- Link target uses the slide-detail naming convention: `href="#/{slide_id}-detail"`.
- Link text format: `"Deep-dive: {topic} >"` — the `>` arrow signals navigation.
- Style class is `deep-dive-link` (defined in toolkit `components.css`).
