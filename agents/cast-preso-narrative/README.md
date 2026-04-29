# cast-preso-narrative

Interview user, synthesize inputs into a locked narrative document for a presentation deck.
Stage 1 of the 4-stage presentation process (Narrative Lock -> WHAT -> HOW -> Assembly).

## Type
`diecast-agent`

## I/O Contract
- **Input:**
  - Raw requirements/writeup for the presentation
  - Source material (thesis docs, existing decks, reference files)
  - User interview answers (gathered via AskUserQuestion during execution)
- **Output:**
  - `{presentation_dir}/narrative.collab.md` — locked narrative document
  - Dispatches `cast-preso-narrative-checker` on completion
- **Config:** None

## Usage
Invoke via HTTP delegation or directly:
```
POST /api/agents/cast-preso-narrative/trigger
```
Provide `delegation_context.context.source_materials` with paths to input files.

## Examples
Input: Cast thesis doc + v1 presentation + raw requirements
Output: narrative.collab.md with TG, outcomes, consumption mode, narrative flow (10 slides),
        aha progression (3 moments), appendix structure
