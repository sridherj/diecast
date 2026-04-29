# Stitch MCP Patterns

## The Critical Instruction

ALWAYS begin every Stitch MCP prompt with:

```
I want you to create an IMAGE FILE, not a webpage.
```

Without this, Stitch defaults to generating HTML/CSS components instead of images.

## Prompt Template

```
I want you to create an IMAGE FILE, not a webpage.

Create a [subject] [action/pose] [setting].
[composition/camera].
[Style Bible block — verbatim].
[Exclusion block — verbatim].
Aspect ratio: [16:9 or as specified].
```

## Output Extraction

- Save as WebP (lossy, quality 80-85)
- Target file size: 200-400KB
- Dimensions: 1920x1080 for full-bleed (16:9)
- Smaller for inline illustrations (800px+ width minimum)

## Known Limitations

| Limitation | Workaround |
|------------|------------|
| Generates HTML/CSS instead of images | Add "IMAGE FILE, not a webpage" at the start |
| Text rendering unreliable | Never include text in prompts — overlay in HTML |
| Style consistency between runs | Use the full Style Bible block verbatim every time |
| Credit/rate limits | Check response for limit indicators; escalate to SJ |
| Aspect ratio drift | Specify explicitly in the prompt |
| Service unavailability | Fall back to placeholder description + escalate to human |

## When Stitch Is the Right Tool

- Watercolor/painterly illustrations
- Conceptual metaphor scenes
- Atmospheric backgrounds
- UI mockups with visual fidelity
- Any illustration requiring emotion or atmosphere

## When Stitch Is the Wrong Tool

- Technical diagrams/flowcharts (use inline SVG)
- Data visualizations (use inline SVG)
- Architecture diagrams (use inline SVG)
- Icons/badges (use inline SVG)
- Anything requiring precision or exact text

## Failure Handling

If Stitch MCP is unavailable or returns an error:
1. Fall back to a **placeholder description** — a detailed text description of what the illustration should depict
2. Save the placeholder to `how/{slide_id}/assets/{filename}.placeholder.md`
3. Log the error in the generation log
4. **Escalate to human** with the error details and placeholder description
5. Never silently drop a required illustration
