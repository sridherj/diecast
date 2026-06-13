# sp2 output — `block_diff` pure engine + `diff_render` (the Phase 5 contract)

**Status: COMPLETE.** All Detailed Steps executed, all verification run, every success
criterion met. `tests/test_block_diff.py` is green (16 tests); no existing suite regressed
(renderer + parser + render-route + theme-drift all green).

## What landed

| File | Action | Notes |
|------|--------|-------|
| `cast-server/cast_server/requirements_render/block_diff.py` | **created** | Pure engine: `diff_blocks`, `BlockDiff`, `ModifiedBlock`, `summarize`. Zero FastAPI/DB/LLM imports. |
| `cast-server/cast_server/requirements_render/diff_render.py` | **created** | `render_diff(old, new, *, base_version, head_version) -> RenderResult`. Self-contained tracked-changes view. |
| `cast-server/cast_server/requirements_render/templates/_theme.css.j2` | **modified** | Appended the Phase-4 diff-class block (token-only) after the existing rules. |
| `cast-server/tests/fixtures/refine_requirements_v2/refined_requirements.v2-edit.collab.md` | **created** | Fixture variant isolating all four diff cases. |
| `cast-server/tests/test_block_diff.py` | **created** | 16 tests incl. the partition invariant. |
| `cast-server/tests/golden/requirements_render/*.html` (12 files) | **regenerated** | `UPDATE_GOLDENS=1` — additive theme-CSS delta only; renderer code untouched. |

## The cross-phase contract (Phase 5 imports this verbatim — do NOT fork)

```python
from cast_server.requirements_render.block_diff import (
    diff_blocks, summarize, BlockDiff, ModifiedBlock,
)
diff_blocks(old: ParsedRequirements, new: ParsedRequirements) -> BlockDiff
summarize(diff: BlockDiff) -> dict
```

- `BlockDiff(added, removed, modified, unchanged)` — `added`/`removed` are `tuple[Block, ...]`;
  `modified`/`unchanged` are `tuple[ModifiedBlock, ...]` where `ModifiedBlock(old, new)`.
- **Pure move ⇒ `unchanged`** (set arithmetic has no "moved" bucket).
- **Partition invariant** (tested): every old block appears exactly once across
  `removed ∪ modified.old ∪ unchanged.old`; every new block exactly once across
  `added ∪ modified.new ∪ unchanged.new`.
- `summarize()` →
  `{"counts": {added, modified, removed, unchanged}, "items": [{change, kind, heading_or_ref, excerpt}, ...]}`
  — `change ∈ {added, modified, removed}`; `unchanged` is counted but never itemized. Items are
  emitted in a stable order (added → modified → removed) so the dict is byte-deterministic. This
  is the narration input: an LLM may narrate these rows but never invents entries not present.

### Match algorithm (as built)
Two passes, document-order tie-break:
1. Normalized-body equality (per-line trailing whitespace stripped, trailing newlines collapsed)
   → `unchanged`.
2. Among the remainder, key equality with differing body → `modified`. Key = `("L1", kind)` for
   level-1 whole-section blocks; `("L2", kind, token)` for level-2 elements where `token` is the
   in-memory `ref` (`FR-007`/`US1`/`SC-001`) when present, else the full `heading`, else the
   block's identity (anonymous bullets never cross-pair). Duplicate keys pair in document order.
3. Remainders → `added` (new) / `removed` (old).

> **Note for sp4a / Phase 5:** `kind` is folded into the level-2 key (the prose contract said
> "heading token"). This is a *safe superset* — it prevents unmatched bullets in different
> sections (e.g. a Constraint vs. an Out-of-Scope bullet) from wrongly pairing, and is a no-op
> for ref/heading-bearing blocks. The partition invariant is preserved regardless.

## `diff_render` (for sp4a wiring)

`render_diff(old, new, *, base_version, head_version) -> RenderResult` (same `RenderResult`
imported from `renderer.py`). Self-contained HTML; theme inlined via `templating.get_environment()`.

- The **"What changed" panel renders first**: `+N added · ~N modified · −N removed`, each item a
  link to a **transient** `id="diff-{n}"` anchor. These ids exist **only** in the diff view —
  generated per render, never stored, never comment anchors. The canonical render's zero-`id`
  contract is untouched.
- Head-document order is the spine: `added` → `class="diff-added"`; `modified` → `diff-modified`
  with the prior body in a **closed** `<details><del>`; `removed` → `diff-removed` (struck),
  attached after the last surviving block of its old section (leading removals head the spine).
- Read-only and comment-free.
- **Error tolerance:** `render_diff(None, new, ...)` / `render_diff(old, None, ...)` returns a
  "cannot diff this pair" card (with a `cannot diff` warning) instead of raising — so sp4a's route
  can pass `None` for an unparseable archived snapshot without a 500.

### CSS (sp4a / sp5 coordination)
The diff classes (`.diff-added/.diff-modified/.diff-removed`, `<del>`, `.diff-changed-panel` and
friends) are already in `_theme.css.j2`, **token-only** (green/amber/red = `--color-success` /
`--color-warning` / `--color-danger`), appended **after** the `:root` blocks so the token-drift
pin and the hex-scan both stay green. sp4a does **not** need to re-add them; its golden cut will
inherit them. **The 12 renderer goldens were already regenerated for this delta.**

## Fixture variant (the four buckets, 1:1)
`refined_requirements.v2-edit.collab.md` vs the frozen base produces exactly:
- **added:** `FR-021` (new row).
- **modified:** `FR-001` (same ref, reworded body).
- **removed:** the `- Changes to the exploration pipeline (cast-explore) itself.` Out-of-Scope bullet.
- **unchanged (pure move):** the whole `## Directional Ideas` section relocated (old block index
  47 → new index 35, body byte-identical). 52 unchanged blocks total.

## Verification run
- `uv run pytest tests/test_block_diff.py -q` → **16 passed**.
- `grep -nE "openai|anthropic|requests|sqlite|get_connection"` over both engine modules → **empty**.
- Hex scan over the diff CSS block → **no hex** (tokens only).
- Regression: `test_requirements_renderer.py` (87) + `test_requirements_parser.py` +
  `test_render_route_and_service.py` + `test_theme_token_drift.py` → **all green** (136 + 6).

## Out of scope (left for sp4a, as planned)
`GET /goals/{slug}/render/diff`, `GET …/changes`, the version toggle in `document.html.j2`, and
`test_diff_render.py` goldens — they depend on the version service + router from sp1/sp3.
