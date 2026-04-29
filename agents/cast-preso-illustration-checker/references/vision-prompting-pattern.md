# Vision-First Prompting Protocol

> The checker's core technique. Follow this EXACT sequence.

## Step 1 — Describe (NO spec context)

Read the illustration. BEFORE seeing the scene brief, describe:
- What is the subject?
- How many distinct elements? List each one.
- What colors are used?
- What is the style/medium?
- What is the composition/layout?
- Is there any text visible? What does it say exactly?

Save this description in the `blind_description` field of the verdict.

## Step 2 — Compare Against Spec

Now read the scene brief. For each requirement, compare Step 1 observations:
- Subject match?
- Element count match?
- Spatial relationships match?
- Style match?
- Any text that shouldn't be there?

## Step 3 — Structured Checklist Evaluation

Run the appropriate pass (1, 2, or 3) from checker-checklist.md. Each check gets PASS or FAIL with specific evidence drawn from Step 1's description.

## Why This Order Matters

Without Step 1, the model "sees" what the prompt told it to expect — text priors override visual analysis. Forcing a blind description first catches real discrepancies that confirmation bias would miss.

## What Vision Models Cannot Reliably Do

- Count objects above ~5
- Verify fine spatial relationships (within ~20px)
- Pixel-level accuracy checks
- Read text smaller than ~12px in images

For these, flag uncertainty and recommend manual verification if critical.
