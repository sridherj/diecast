# Refactor / Migration Fixture

## Intent

Migrate the checker's required-section handling to a two-level model without
changing the no-family behaviour for existing product specs.

## Decisions

| Date | Chose | Over | Because |
|------|-------|------|---------|
| 2026-06-11 | mirror the mapping | importing families.py | the linter must stay stdlib-only |

## Out of Scope

- Touching the re-exported grammar regexes or `_section_spans`.
