# cast-preso-how

Create a single presentation slide: brainstorm visual approaches, write a design brief,
generate reveal.js HTML, and delegate illustration creation if needed.

## Type
`diecast-agent`

## I/O Contract

### Input
- **WHAT doc:** `what/{slide_id}.md` — the slide's communication requirements (L1/L2 outcomes, resources, verification criteria)
- **Narrative doc:** `narrative.collab.md` — for narrative context and slide type annotation
- **Visual toolkit:** `.claude/skills/cast-preso-visual-toolkit/` — style tokens, archetype templates, design conventions
- **Tone guide:** `docs/style/writing-tone.md` — the user's writing voice
- **Delegation context:** slide_id, check_mode (full/lightweight), regenerate flag, checker feedback (if rework)

### Output
All files written to `how/{slide_id}/`:
- `brief.collab.md` — Design rationale and regeneration blueprint
- `slide.html` — Reveal.js `<section>` HTML
- `versions/` — A/B versions if multiple approaches kept; previous versions on regeneration
- `assets/` — Illustrations and images (populated by illustration-creator)
- `open_questions.md` — Questions for human resolution
- `notes_for_assembler.md` — Cross-slide notes for Stage 4

### Config
- `regenerate: true|false` — If true, execute Step 1 (context), skip Steps 2-5, rebuild HTML from existing brief
- `checker_feedback` — Structured feedback from check-coordinator (if rework iteration)

## Usage
Dispatched via HTTP delegation from orchestrator or manual invocation:
POST /api/agents/cast-preso-how/trigger

## Delegates To
- `cast-preso-illustration-creator` — For watercolor illustrations and complex SVG diagrams
