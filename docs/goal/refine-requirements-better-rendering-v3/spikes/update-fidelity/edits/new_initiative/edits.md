# new_initiative — authored source edits (Sub-phase 1a spike)

Three surgical edits to the corpus source, isolated so the *unchanged* surface stays large.
Full edited source: `new.collab.md`. Deterministic changed-set (from `block_diff.summarize`): `changed-set.json`.

block_diff counts: {'added': 1, 'modified': 1, 'removed': 1, 'unchanged': 46}

## Edits

### modified FR/section body
- **find:** reusing the v2 embedded-source-hash lazy-regeneration mechanism unchanged.
- **replace:** reusing the v2 embedded-source-hash lazy-regeneration mechanism unchanged. The cache key additionally folds in the resolved work-family so a

### added SC / bullet
- **find:** | SC-008 | On non-convergence, the reader is served the best-scoring attempt with a human-review flag recorded, never the plain deterministi
- **replace:** | SC-008 | On non-convergence, the reader is served the best-scoring attempt with a human-review flag recorded, never the plain deterministi

### removed bullet
- **find:** - Rendering documents other than refined requirements.
- **replace:** (deleted)

## Changed-set items

- added [sc] SC-009: | SC-009 | A re-classification of a goal's work family invalidates its cached r…
- modified [fr] FR-005: | FR-005 | The generated render is cached against the source content hash and r…
- removed [scope] - Rendering documents other than refined requirements.: - Rendering documents other than refined requirements.
