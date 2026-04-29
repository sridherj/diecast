# Brief Template

> Loaded by `cast-preso-how` at Step 5 (brief creation).
> The brief is the **regeneration blueprint** — editing it and re-running with `regenerate: true` produces a predictable new slide.
>
> Fill in EVERY section. Mark optional sections (illustration, version A/B, appendix link) as "N/A" when not applicable rather than omitting them — the structure must stay stable across slides for downstream agents.

```markdown
# Brief: {Slide Title}

## Slide Identity
- **Slide ID:** {slide_id}
- **Slide Type:** {hook | reveal | moment | information}
- **Position in Deck:** Slide {N} of {total}, between "{prev}" and "{next}"

## Chosen Archetype
**{Archetype Name}** — {one-sentence rationale for choice}

## Content Hierarchy

### L1 (Primary — visually prominent)
- {L1 outcome 1} → [visual treatment: size, color, position]
- {L1 outcome 2} → [visual treatment]

### L2 (Supporting — present but secondary)
- {L2 outcome 1} → [visual treatment: fragment, muted, smaller]
- {L2 outcome 2} → [visual treatment]

## Action Title
"{Complete sentence with a verb — the slide's assertion}"

## Fragment / Animation Plan
1. [Initially visible]: {what's on screen when slide appears}
2. [Fragment 1]: {what appears, how it appears}
3. [Fragment 2]: {what appears}
...
Max 6 fragment steps.

## Illustration Requirements
**Needed:** Yes by default. Justify 'No' only when the slide is a single statement, a pure quote, or a flat list of equally-weighted items.
**Justification (if No):** {which exception applies — single statement | pure quote | flat list of equally-weighted items | title slide | pure code block}
**Type:** Watercolor (Stitch MCP) / Inline SVG / None
**Scene brief (if Yes):**
  Subject: {what the illustration depicts}
  Composition: {framing, camera angle, spatial arrangement}
  Key elements: {must-have elements, max 5}
  Mood: {emotional tone}
  Size on slide: {full-bleed 80%+ | half-width | inline small}
  Text in image: NONE (all text in HTML overlay)

## Visual Toolkit Tokens Used
- Background: {token, e.g., var(--color-bg-paper)}
- Accent color: {token, e.g., var(--color-accent)}
- Callout style: {if using callouts}
- Grid background: {yes/no}

## Speaker Notes Outline
{2-3 bullet points for what the presenter would say}
{Timing estimate: ~N seconds}

## Approaches Considered

### Approach 1: {Name} ← SELECTED
{Full brainstorm from Step 4 — layout, L1/L2 treatment, fragment plan, illustration needs,
hook/reveal technique, pros, cons, Steve Jobs test result}

### Approach 2: {Name}
{Full brainstorm from Step 4}

### Approach 3: {Name} (if applicable)
{Full brainstorm from Step 4}

**Selection rationale:** {Why Approach 1 won — be specific about the trade-offs}

## Version A/B (if applicable)
**Version A (Recommended):** {Approach 1 — brief description}
**Version B:** {Approach 2 — brief description}
**the user decides:** {What specifically differs between A and B}

## Rework History
- v1: Initial brief (created {date})
- v2: {criterion} failed — changed {what} because {why}
```

## How to Fill This Out

- **Slide Identity:** Pull `slide_id` from delegation context. `Position in Deck` comes from the narrative flow table.
- **Chosen Archetype:** Use exact archetype name from the visual toolkit catalog. Rationale must reference the WHAT doc's content, not generic reasoning.
- **Content Hierarchy:** Quote L1/L2 outcomes verbatim from the WHAT doc. Visual treatment notes go inside `[brackets]` after each item.
- **Action Title:** Must be a complete sentence with a verb. "Three-Stage Pipeline" is not a title; "Three stages turn raw research into shipping decks" is.
- **Fragment Plan:** Number each step. Max 6 steps. For `moment` slides, plan should be one line: "1. Whole slide visible — no fragments."
- **Illustration Requirements:** If "Needed: No," still fill out "Type: None" — don't omit the section.
- **Visual Toolkit Tokens:** Reference CSS variables, never hex codes. If unsure, default to `var(--color-bg-paper)` and `var(--color-accent)`.
- **Speaker Notes Outline:** 2-3 bullets max. Timing target: ~30-60 seconds for most slides, ~90 for moment slides.
- **Approaches Considered:** ALWAYS include 2-3 distinct approaches, even if obviously losing approaches. The evidence of consideration matters for the user to trust the selection. Mark winner with "← SELECTED."
- **Version A/B:** Use ONLY when two approaches scored within ~10% on the Steve Jobs test. Otherwise pick one and move on.
- **Rework History:** Add a new line per rework iteration. Quote the failing checker criterion verbatim.
