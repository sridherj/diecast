# cast-update-spec

Single write path for product spec updates. No other agent modifies spec files.

## Type
claude-code-skill

## I/O Contract
- **Input:** Spec name or domain context + change description (natural language)
- **Output:** Updated spec file in docs/specs/ with version bump and changelog
- **Config:** None (reads spec registry from docs/specs/_registry.md)

## Usage
- `/cast-update-spec` or "update spec", "modify spec", "add behavior to spec"

## Tags
[specs] [planning] [taskos]
