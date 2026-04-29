# Archetype Treatment Matrix

> Loaded by `taskos-preso-how` at Step 3 (archetype selection).
> Source: `taskos/goals/presentation-agents/exploration/playbooks/04-slide-design-patterns.ai.md` (Parts 1, 2, and Treatment Matrix).
>
> **Usage:** Use the slide-type table as a *starting point*, then refine with the content-characteristics filter. Step 2 may pull in archetypes outside the type's primary list — the matrix is guidance, not a hard filter.

## 1. Slide Type → Archetypes

| Slide Type | Primary Archetypes | Secondary Archetypes |
|------------|-------------------|---------------------|
| `hook` | Single-Stat Hero, One-Statement, Compare/Contrast | Timeline (showing acceleration/trend), Illustrated Section Opener (visual hook) |
| `reveal` | Single-Stat Hero, Compare/Contrast, Code-Snippet Showcase, Diagram-with-Annotations | Build-Up Sequence (progressive reveal of layers) |
| `moment` | Illustrated Section Opener, One-Statement, Single-Stat Hero | (none — moment slides are deliberately simple) |
| `information` | Consulting Exhibit, Diagram-with-Annotations, Code-Snippet Showcase, Build-Up Sequence, Timeline, Compare/Contrast | (none — most archetypes can serve information slides) |

## 2. Content Characteristics Filter

Cross-check the slide's content against this table. A characteristic match can pull an archetype IN even if not in the slide-type primary list.

| If the slide content has... | Strongly consider... |
|-----------------------------|----------------------|
| A single powerful number | Single-Stat Hero |
| A before/after or A vs B comparison | Compare/Contrast |
| A technical architecture or system flow | Diagram-with-Annotations |
| Code to show (snippet, API, config) | Code-Snippet Showcase |
| A sequence, process, or chronological progression | Timeline / Build-Up Sequence |
| A data-driven argument with multiple supporting points | Consulting Exhibit |
| An emotional pause or section break | Illustrated Section Opener / One-Statement |
| A bold thesis statement on its own | One-Statement |

## 3. Archetype Quick-Reference Cards

### Single-Stat Hero
- **What it is:** One enormous number filling most of the slide, with a tight context phrase below.
- **Hard rules:** The stat must occupy 50%+ of slide visual weight. Max 8 words of supporting context. No bullet lists. The stat needs a *source* (footnote or speaker note).
- **Fragment default:** Stat lands first (no fragment), then optional 1-fragment context line.
- **When NOT to use:** Multiple stats need comparison (use Compare/Contrast). Stat needs heavy explanation (use Consulting Exhibit). Stat is contested/needs caveats (use Diagram-with-Annotations).

### Compare/Contrast (Side-by-Side)
- **What it is:** Two columns, equal weight, presenting a contrast (old/new, theirs/ours, before/after).
- **Hard rules:** Strict visual symmetry — same column widths, same heading style. The contrast axis must be obvious in < 3 seconds. Max 5 elements per side.
- **Fragment default:** Reveal both sides simultaneously, OR build left-then-right for "old way / new way" hooks.
- **When NOT to use:** More than 2 things to compare (use Consulting Exhibit table or Build-Up). The two sides aren't actually parallel concepts.
- **Illustration preference:** Prefer SVG illustration for any sub-region with narrative hierarchy; inline HTML only for genuinely flat content (lists, captions, chrome).

### Timeline / Progression
- **What it is:** Horizontal axis of events or stages, with milestones marked along it.
- **Hard rules:** Time/sequence axis must be visually explicit (line, arrow, numbered nodes). Max 6 milestones. Each milestone must be ≤ 6 words.
- **Fragment default:** Build left-to-right, one milestone per fragment.
- **When NOT to use:** Static comparison (use Compare/Contrast). System architecture without temporal sequence (use Diagram-with-Annotations).

### Diagram-with-Annotations
- **What it is:** Central inline SVG diagram with numbered callouts pointing at parts.
- **Hard rules:** Diagram occupies 60%+ of slide. Callouts use `class="fragment custom callout-appear"`. Max 6 callouts. Callouts use CSS variables, never hardcoded colors.
- **Fragment default:** Diagram visible immediately, callouts appear one-at-a-time as numbered.
- **When NOT to use:** No system or structure to visualize (use Consulting Exhibit). The diagram would be more text than image.
- **Illustration preference:** Prefer SVG illustration for any sub-region with narrative hierarchy; inline HTML only for genuinely flat content (lists, captions, chrome).

### Code-Snippet Showcase
- **What it is:** Code block as the centerpiece, with optional inline annotations or a question annotation.
- **Hard rules:** Use reveal.js highlight.js classes. Max 12 lines visible. Highlight specific lines with `data-line-numbers`. Use `data-auto-animate` to morph between code states (before/after pattern).
- **Fragment default:** Code lands as a unit; use `data-line-numbers="1-3|4-6|7-12"` to walk through it.
- **When NOT to use:** Code is incidental, not central (put in speaker notes). Code is too long to fit (split into multiple slides with auto-animate).
- **Illustration preference:** Prefer SVG illustration for any sub-region with narrative hierarchy; inline HTML only for genuinely flat content (lists, captions, chrome).

### Consulting Exhibit (Action Title + Evidence)
- **What it is:** Action-title sentence at top, supporting evidence (chart, table, or 2-3 grouped facts) below. McKinsey/BCG/Bain pattern.
- **Hard rules:** Title is a complete sentence asserting a finding (verb required). Evidence directly supports the title — no orphan data. Source line at bottom (small).
- **Fragment default:** Title fades in, then evidence chart, then optional callout(s).
- **When NOT to use:** No data-driven argument (use One-Statement or Hero). Single stat dominates (use Single-Stat Hero).
- **Illustration preference:** Prefer SVG illustration for any sub-region with narrative hierarchy; inline HTML only for genuinely flat content (lists, captions, chrome).

### One-Statement Slide (Takahashi/Apple)
- **What it is:** A single sentence, very large type, alone on the slide.
- **Hard rules:** Max 12 words. Sentence must be complete (subject + verb). 70%+ whitespace. No bullets. No image.
- **Fragment default:** No fragments. The whole slide IS the message.
- **When NOT to use:** Anything else needs to be on screen. Statement isn't strong enough to stand alone.

### Illustrated Section Opener
- **What it is:** Full-bleed watercolor illustration with overlay text (section name + one phrase).
- **Hard rules:** Illustration is full-bleed (80-100% width). Text overlay uses high-contrast box or outlined type. NO body text, NO bullets — this is a beat, not a slide.
- **Fragment default:** No fragments — the slide IS a pause.
- **When NOT to use:** Information needs to be conveyed (use Consulting Exhibit). No visual budget for illustration (use One-Statement instead).
- **Note:** "Use Consulting Exhibit" refers to the LAYOUT archetype (action title + evidence grid), not a rendering mandate. Consulting Exhibit slides can — and often should — embed inline SVG for their hero panels when those panels carry narrative hierarchy (primary/secondary/tertiary roles, product-mock chrome, decision panels). The archetype name refers to layout, not rendering.

### Build-Up Sequence
- **What it is:** A list (3-5 items) that appears one item at a time, with previous items fading semi-out.
- **Hard rules:** Use `class="fragment fade-in-then-semi-out"` on each item. Max 5 items. Each item ≤ 8 words. Final state must still be readable.
- **Fragment default:** One item per fragment, in narrative order.
- **When NOT to use:** All items need to be visible together (use Consulting Exhibit table). Items aren't sequential — they're parallel facts (use grouped layout).
- **Illustration preference:** Prefer SVG illustration for any sub-region with narrative hierarchy; inline HTML only for genuinely flat content (lists, captions, chrome).

### Title Slide / Close-CTA
- **What it is:** Deck opening or closing slide. Title slide = presentation title + author. Close = single CTA + contact.
- **Hard rules:** Title slide includes presentation title (required), subtitle (optional), author (required), date (optional). Close-CTA includes ONE call to action (no menu of options) and contact link.
- **Fragment default:** No fragments.
- **When NOT to use:** Mid-deck slides (these archetypes are for opening/closing only).
