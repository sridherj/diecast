# cast-preso-check-tone

Evaluates a Stage 3 slide for tone authenticity: does it sound like the user wrote it? Checks against the user's writing tone guide, detects GPT-isms, enforces compression and concreteness.

## Type
`diecast-agent`

## I/O Contract
- **Input:**
  - `how/{slide_id}/slide.html` -- the slide to check
  - `docs/style/writing-tone.md` -- the user's writing tone guide (MUST be loaded as context)
  - Delegation context with `slide_id`
- **Output:**
  - JSON verdict (dimension: "tone") in output.json artifacts
- **Config:** None

## Usage
Called by `cast-preso-check-coordinator` via HTTP delegation.

## Examples
**Input:** Slide with "We're passionate about leveraging AI to drive innovative solutions."
**Output:** FAIL -- "no-gptisms" criterion failed. Evidence: "passionate", "leveraging", "innovative", "drive...solutions" are all GPT-isms. What good looks like: "We use AI to find people. Here's how."

**Input:** Slide with "28 companies. $10M pipeline. Built in 4 months."
**Output:** PASS -- Direct, compressed, concrete. Fragments. Specific numbers. the user voice.
