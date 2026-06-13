# Sub-phase 2: `block_diff` pure engine + `diff_render` (the Phase 5 contract)

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase4/_shared_context.md` before starting.

## Objective

Build the **deterministic, pure** diff engine and the tracked-changes renderer. This is **the
cross-phase contract** — Phase 5 imports `block_diff` verbatim for its provenance-badged round-trip
summaries. The change SET is deterministic; an LLM may later *narrate* `summarize()` output but never
*invent* entries (decision #8). This sub-phase is **fully parallel with sp1 from day one** — it
touches only the FastAPI-free `requirements_render` package and its own tests/fixtures.

## Dependencies

- **Requires completed:** None. Depends only on the **landed** Phase 1 parser
  (`requirements_render.parser`, `blocks.Block`/`ParsedRequirements`) and the package Jinja env
  (`requirements_render.templating.get_environment`).
- **Assumed codebase state:** `parse_requirements(text)` returns `ParsedRequirements` with `blocks`
  (each a frozen `Block{kind, level, body, heading, ref, line_start, line_end}`);
  `document.html.j2` + `_theme.css.j2` exist; goldens regenerate via `UPDATE_GOLDENS=1`.

## Scope

**In scope:**
- `cast_server/requirements_render/block_diff.py` — `diff_blocks`, `BlockDiff`, `ModifiedBlock`,
  `summarize`.
- `cast_server/requirements_render/diff_render.py` — `render_diff(old, new, *, base_version,
  head_version) -> RenderResult` (pure; reuses the package theme).
- The diff-view CSS additions in `_theme.css.j2` **scoped to diff classes only** (`.diff-added`,
  `.diff-modified`, `.diff-removed`, `<del>` styling, the What-changed panel) — tokens only.
- Test fixture variant: `tests/fixtures/refine_requirements_v2/refined_requirements.v2-edit.collab.md`
  (one added FR, one reworded FR, one deleted Out-of-Scope bullet, one moved section vs the frozen
  Phase 1 fixture).
- `tests/test_block_diff.py`.

**Out of scope (do NOT do these):**
- The `GET /goals/{slug}/render/diff` route, the `GET …/changes` endpoint, the version toggle in
  `document.html.j2`, and `test_diff_render.py` goldens — **all sp4a** (they need the version
  service + router from sp1/sp3). sp2 ships the pure modules + their unit tests only.
- Any LLM call anywhere (a no-import pin enforces this in sp4a/sp6).
- Storing any `id` on the canonical render (the transient `diff-{n}` ids exist only in `diff_render`
  output, generated per call).

> **File-coordination note:** `_theme.css.j2` is also edited by sp4a (it's the same diff CSS scope)
> and sp5 (comment CSS). sp2 runs **parallel with sp1 only** (sp1 never touches `_theme.css.j2`),
> so adding the diff CSS here is safe. If you prefer to keep sp2 strictly module-only, you MAY defer
> the `_theme.css.j2` diff-class block to sp4a and have `diff_render` reference the classes; either
> is acceptable as long as the classes are token-only and land before sp4a's golden cut. **Default:
> add them here** so `render_diff` is testable end-to-end in sp2.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast_server/requirements_render/block_diff.py` | Create | Does not exist |
| `cast_server/requirements_render/diff_render.py` | Create | Does not exist |
| `cast_server/requirements_render/templates/_theme.css.j2` | Modify (diff classes only) | Phase 3a theme, token-pinned |
| `tests/fixtures/refine_requirements_v2/refined_requirements.v2-edit.collab.md` | Create | Frozen base exists beside it |
| `tests/test_block_diff.py` | Create | Does not exist |

## Detailed Steps

### Step 2.1: `block_diff.py` — the match algorithm + partition invariant

Implement exactly the Naming Contract (`_shared_context.md` → "Diff engine"). Pure: no imports of
FastAPI, DB, or any LLM client. Module docstring MUST contain the verbatim Phase-5 line:
*"Phase 5 imports this engine for round-trip change summaries — extend, never fork. The change SET
is deterministic; LLM narration consumes `summarize()` output and never invents entries."*

Match algorithm (two passes, document-order tie-break):
1. **Normalized-body equality** → `unchanged` (a pure move is `unchanged` — set arithmetic has no
   "moved"). Normalize body for comparison (e.g. strip trailing whitespace per line, collapse final
   newline) — define the normalization once and reuse it.
2. **Key equality with differing body** → `modified`. Key = the heading token for level-2 blocks
   (in-memory `ref` like `FR-007`/`US1` when present, else full `heading` text) and `kind` for
   level-1 blocks. **Duplicate keys pair in document order.**
3. Remainders → `added` (new side) / `removed` (old side).

`summarize(diff) -> dict`: `{counts: {added, modified, removed, unchanged}, items: [{change,
kind, heading_or_ref, excerpt}, ...]}` — `change ∈ added|modified|removed`; `excerpt` a short body
slice. This dict is what `/changes` JSON and the What-changed panel both render from.

### Step 2.2: `diff_render.py` — tracked-changes view

`render_diff(old: ParsedRequirements, new: ParsedRequirements, *, base_version: int,
head_version: int) -> RenderResult` (same `RenderResult` shape Phase 3a's renderer returns — import
it from the renderer module). Use `templating.get_environment()` for templates.

- Render the **head document's order** as the spine, per-block treatment:
  - `added` → `class="diff-added"` (green accent).
  - `modified` → `class="diff-modified"` (amber): new body shown; prior body as `<del>` inside a
    **closed** `<details>`.
  - `removed` → struck red, attached after the last surviving block of its old H2 section;
    whole-section removals render as one struck section at the old relative position.
- The **"What changed" panel renders first**: `+N added · ~N modified · −N removed`, each item a
  link to a **transient** `id="diff-{n}"` anchor. **These ids exist ONLY in the diff view** —
  generated per render, never stored, never comment anchors; the canonical render's zero-`id`
  contract is untouched.
- The diff view is **comment-free and read-only**.
- Error tolerance: an unparseable archived snapshot (pre-parser content) must not 500 — return a
  RenderResult carrying a "cannot diff this pair" marker the route renders as a card (sp4a wires the
  route; `diff_render` just must not raise on unparseable input — guard the parse).

### Step 2.3: `_theme.css.j2` diff classes (tokens only)

Add `.diff-added`, `.diff-modified`, `.diff-removed`, `del` styling, and the `.diff-changed-panel`
rules using `var(--color-*)` tokens ONLY — never hex (the Phase 3a hex-scan test will fail on hex).
Keep additions self-contained and clearly commented as the Phase-4 diff block.

### Step 2.4: The fixture variant

Create `refined_requirements.v2-edit.collab.md` by copying the frozen
`tests/fixtures/refine_requirements_v2/refined_requirements.collab.md` and making exactly four
edits, each isolating one diff case:
1. **One added FR** (a brand-new `FR-NNN` element → `added`).
2. **One reworded FR** (same `FR-xxx` ref, changed body → `modified`).
3. **One deleted Out-of-Scope bullet** (→ `removed`).
4. **One moved section** (relocate a whole H2 with body unchanged → lands in `unchanged`).

## Verification

### Automated Tests (permanent)

**`tests/test_block_diff.py`:**
- **Partition invariant:** every old block appears exactly once across
  `removed ∪ modified.old ∪ unchanged.old`; every new block exactly once across
  `added ∪ modified.new ∪ unchanged.new`. Assert by collecting ids/indices.
- Added / removed / modified / unchanged cases via the fixture pair (the four seeded edits map to
  the four buckets).
- **A pure move lands in `unchanged`** (not "moved").
- Duplicate headings pair in document order (construct a small synthetic `ParsedRequirements` with
  two same-key blocks).
- `summarize()` counts == set sizes; item rows match.
- **Determinism:** same inputs → byte-identical `BlockDiff` and `summarize()` output across repeated
  calls.
- **No-LLM / no-IO pin:** `block_diff.py` and `diff_render.py` source contain no `import openai`,
  no `anthropic`, no `requests`, no DB import (a source-scan assertion, mirroring Phase 3b's router
  source pin). (sp6 also pins `package.json` absence; this pin is about the engine purity.)

### Validation Scripts (temporary)
```bash
cd cast-server && python -m pytest tests/test_block_diff.py -q
# Eyeball a render:
python -c "from cast_server.requirements_render import parser, diff_render; \
  o=parser.parse_requirements_file('tests/fixtures/refine_requirements_v2/refined_requirements.collab.md'); \
  n=parser.parse_requirements_file('tests/fixtures/refine_requirements_v2/refined_requirements.v2-edit.collab.md'); \
  print(diff_render.render_diff(o,n,base_version=1,head_version=2).html[:800])"
```

### Manual Checks
- `grep -nE "openai|anthropic|requests|sqlite|get_connection" cast_server/requirements_render/block_diff.py cast_server/requirements_render/diff_render.py` → empty.
- `grep -nE "#[0-9a-fA-F]{3,6}" cast_server/requirements_render/templates/_theme.css.j2` → no NEW hex in the diff block.

### Success Criteria
- [ ] `block_diff.diff_blocks` / `BlockDiff` / `ModifiedBlock` / `summarize` match the Naming Contract exactly.
- [ ] Partition invariant + determinism tests pass; a pure move is `unchanged`.
- [ ] `diff_render.render_diff` returns a `RenderResult`; transient `diff-{n}` ids only in diff output.
- [ ] Module docstring carries the verbatim Phase-5 "extend, never fork" line.
- [ ] No LLM/DB/HTTP import in either module; diff CSS is token-only.
- [ ] `v2-edit` fixture isolates all four diff cases.

## Execution Notes

- This module is the single most reused artifact of the whole goal — invest in the partition
  invariant test; it is the safety net against silent data loss in change summaries.
- Keep `block_diff` importable with zero FastAPI/DB cost (it lives in `requirements_render` for
  exactly this reason). Phase 5 will `from cast_server.requirements_render.block_diff import
  diff_blocks, summarize`.
- `RenderResult` already exists in the Phase 3a renderer — import it, do not redefine it.

**Spec-linked files:** `_theme.css.j2` is part of the Phase 3a render surface covered by
`cast-requirements-render.collab.md`. Read that spec's theming/DOM sections before editing; the diff
classes are additive and must preserve the token-only rule. The transient-`id` exception is recorded
in the spec by sp7 — do not edit the spec here.
