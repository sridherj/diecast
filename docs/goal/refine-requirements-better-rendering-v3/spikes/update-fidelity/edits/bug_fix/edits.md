# bug_fix — authored source edits (Sub-phase 1a spike)

Three surgical edits to the corpus source, isolated so the *unchanged* surface stays large.
Full edited source: `new.collab.md`. Deterministic changed-set (from `block_diff.summarize`): `changed-set.json`.

block_diff counts: {'added': 1, 'modified': 1, 'removed': 1, 'unchanged': 8}

## Edits

### modified FR/section body
- **find:** while staying a single contiguous `<li>` with no fragmenting spans.
- **replace:** while staying a single contiguous `<li>` with no fragmenting spans. The kicker line directly above the assertions resolves inline markdown t

### added SC / bullet
- **find:** | SC-003 | A markdown-free source renders a byte-identical Goal Card to the pre-fix output. | Golden-snapshot diff on an emphasis-free fixtu
- **replace:** | SC-003 | A markdown-free source renders a byte-identical Goal Card to the pre-fix output. | Golden-snapshot diff on an emphasis-free fixtu

### removed bullet
- **find:** - **[DEFERRED]** Whether the sibling `_first_sentence` abbreviation-truncation defect should be fixed in the same change or tracked as its o
- **replace:** (deleted)

## Changed-set items

- added [sc] SC-004: | SC-004 | The kicker line above the Goal Card assertions renders inline markdo…
- modified [fr] FR-002: | FR-002 | Each L2 assertion on the Goal Card resolves inline markdown the same…
- removed [open_question] - **[DEFERRED]** Whether the sibling `_first_sentence` abbreviation-truncation…: - **[DEFERRED]** Whether the sibling `_first_sentence` abbreviation-truncation…
