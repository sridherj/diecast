# 7-Slot Scene Brief Template

## Template

| Slot | Content | Rules |
|------|---------|-------|
| 1. Subject | What to depict | ≥ 5 words. Specific objects, people, concepts. |
| 2. Action/Pose | What's happening | Active verbs. Not static descriptions. |
| 3. Setting/Environment | Background/context | Ground the scene. Even abstract concepts need a "where." |
| 4. Composition/Camera | Framing, angle, focal point, aspect ratio | Default 16:9 for full-bleed. Specify for inline. |
| 5. Style Bible | FIXED block from style-bible-watercolor.md | VERBATIM. Never edit. |
| 6. Slide Context | Communication role on the slide | What the viewer should understand/feel. Never empty. |
| 7. Exclusions | FIXED block from style-bible-exclusions.md | VERBATIM. Never edit. |

## Prompt Assembly

Assemble the final prompt in this exact order:

```
I want you to create an IMAGE FILE, not a webpage.

Create a [Slot 1: Subject] [Slot 2: Action/Pose] [Slot 3: Setting].
[Slot 4: Composition/Camera].
[Slot 5: Style Bible — full fixed block, verbatim].
[Slot 7: Exclusions — full fixed block, verbatim].
Aspect ratio: [from Slot 4, default 16:9].
```

Keep variable section (Slots 1-4) at 25-40 words. Under 10 = unpredictable defaults. Over 75 = competing instructions.

## Example 1: Watercolor Hero Illustration (Section Opener)

**Slot 1 (Subject):** Three friendly robots of different sizes gathered around a glowing blueprint
**Slot 2 (Action/Pose):** Leaning in together studying the document, one pointing at a detail
**Slot 3 (Setting):** Cozy workshop with wooden shelves and warm afternoon light through a window
**Slot 4 (Composition):** Wide shot, eye-level, robots centered, warm light from upper right. Aspect ratio: 16:9.
**Slot 5 (Style Bible):** [verbatim watercolor block]
**Slot 6 (Slide Context):** This is the section opener for "Building the Agent Team." The illustration must convey collaboration and shared purpose — the robots are working TOGETHER, not alone. The viewer should feel warmth and trust.
**Slot 7 (Exclusions):** [verbatim exclusion block]

**Expected output:** WebP via Stitch MCP, 16:9, ~300KB

## Example 2: SVG Architecture Diagram

**Slot 1 (Subject):** Four connected nodes labeled Maker, Checker, Orchestrator, and Human Gate
**Slot 2 (Action/Pose):** Data flowing left-to-right through the pipeline with arrows between nodes
**Slot 3 (Setting):** Clean white background with subtle grid
**Slot 4 (Composition):** Horizontal layout, nodes evenly spaced, arrows showing flow direction. Aspect ratio: 16:9.
**Slot 5 (Style Bible):** [not used for SVG — use CSS class names from visual toolkit]
**Slot 6 (Slide Context):** This diagram explains the maker+checker pattern. The viewer must immediately see the flow direction and understand that the Checker evaluates the Maker's output before it reaches the Human Gate.
**Slot 7 (Exclusions):** [not used for SVG]

**Expected output:** Inline SVG, viewBox="0 0 720 380", CSS classes only

## Example 3: Watercolor Metaphor (Abstract Concept)

**Slot 1 (Subject):** A gardener carefully pruning a bonsai tree whose branches are shaped like a neural network
**Slot 2 (Action/Pose):** Thoughtfully trimming one specific branch while other branches flourish
**Slot 3 (Setting):** Serene Japanese garden with raked gravel and soft morning mist
**Slot 4 (Composition):** Medium shot, slightly low angle to make the tree prominent, gardener at right third. Aspect ratio: 16:9.
**Slot 5 (Style Bible):** [verbatim watercolor block]
**Slot 6 (Slide Context):** This illustrates "fine-tuning" as a concept — careful, skilled adjustment rather than brute-force change. The viewer should feel precision and patience.
**Slot 7 (Exclusions):** [verbatim exclusion block]

**Expected output:** WebP via Stitch MCP, 16:9, ~350KB
