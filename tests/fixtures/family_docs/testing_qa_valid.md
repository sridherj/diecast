# Testing / QA Fixture

## Intent

Add a regression suite that locks the two-level checker's no-family path so it
can never silently start requiring family sections.

## Evidence

- The no-family corpus comparison currently passes on 28 product specs.
- A pin test already guards the mirrored family mapping.

## Out of Scope

- Rewriting the frozen grammar regexes (re-exported by `spec_grammar.py`).
