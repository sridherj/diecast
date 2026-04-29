# cast-preso-assembler

Assemble all per-slide HTML into a single self-contained reveal.js presentation
with correct navigation, bundled assets, and no external dependencies.

## Type
`taskos-agent`

## I/O Contract

### Input
- **Slide HTML files:** `how/{slide_id}/slide.html` — one per slide, each a `<section>` element
- **A/B versions:** `how/{slide_id}/versions/` — if present, alternative versions to include
- **Narrative doc:** `narrative.collab.md` — for slide ordering, appendix structure, deck title
- **Notes for assembler:** `how/{slide_id}/notes_for_assembler.md` — cross-slide notes
- **Open questions:** `how/{slide_id}/open_questions.md` — should be resolved; collect any remaining
- **Visual toolkit:** `.claude/skills/cast-preso-visual-toolkit/` — base template, theme CSS
- **Base template:** `.claude/skills/cast-preso-visual-toolkit/base-template/` — Vite scaffold from Phase 0C
- **Slide assets:** `how/{slide_id}/assets/` — illustrations, images per slide

### Output
All files written to `presentation/assembly/`:
- `index.html` — Complete self-contained reveal.js presentation (after Vite build)
- `assets/` — All illustrations and media (copied from per-slide directories)
- `src/index.html` — Pre-build template with assembled slides (Vite input)
- `notes_summary.collab.md` — Aggregated notes from all Stage 3 agents
- `remaining_questions.collab.md` — Any unresolved nice-to-have questions (should be near-empty)

### Config
None (stateless — reads all input fresh each run)

## Usage
Dispatched via HTTP delegation from orchestrator:
```
POST /api/agents/cast-preso-assembler/trigger
```

## Delegates To
None (leaf agent)

## Examples
Input: 10 slide HTML files + narrative doc + notes + visual toolkit
Output: assembly/index.html (single self-contained file, ~2-5 MB)
