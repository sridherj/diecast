# sp3a Conflict Predicate — Output

**Status:** completed
**Date:** 2026-06-12

## What was built

A pure, total conflict predicate that makes silent overwrite **structurally impossible** for
round-trip write-back. A downstream change request carries the version it assumed (`base_version`);
before apply, `detect_conflict(...)` asks *has a human touched the target region since then?* and
returns exactly one of `clean | conflicted | orphaned` by comparing the `content_hash` of the
located target region at base vs HEAD — located by **quote, never a stable ID**.

## Files created

| File | Role |
|------|------|
| `cast-server/cast_server/requirements_render/conflict.py` | `region_hash(...)`, `detect_conflict(...)`, `ConflictSurface`, `RESOLUTION_CHOICES`, `VERDICTS` |
| `cast-server/tests/test_conflict_predicate.py` | 20 unit tests (verdicts, real-document proof, property, purity, surface) |
| `cast-server/tests/fixtures/refine_requirements_v2/conflict_base.collab.md` | Focused BASE fixture |
| `cast-server/tests/fixtures/refine_requirements_v2/conflict_head.collab.md` | Focused HEAD fixture (region reworded + line deleted) |

## Design decisions (held to plan)

- **`content_hash` reused, never reimplemented** — `conflict.py` imports
  `requirements_render.hashing.content_hash`; `region_hash` is `content_hash` of the located region.
- **`locate` is injected** — the quote→region resolver is a parameter, keeping the module pure: no
  DB, no LLM, no file I/O. Production wires the `cast-comment-reanchor` verbatim-substring locator;
  tests inject pure-python stubs. **No second locator was built.**
- **Region = enclosing line, not just the quote** — returning a region larger than the anchor is
  what lets a reworded-but-still-anchored region read as `conflicted` rather than a false `clean`.
  A trivial "return the quote" locator can only ever yield `clean`/`orphaned`; conflict detection on
  a thin spine genuinely *is* quote-location over a region.
- **Orphan is a first-class verdict** — a quote that no longer locates returns `orphaned` (→ surface
  to a human), never a silent no-op.
- **Pure addition** (`target_quote is None`) → always `clean` (nothing to conflict on).
- **`ConflictSurface`** models the 3-way choice as data (`accept-incoming` / `keep-current` /
  `merge-with-free-edit`) — **no auto-merge**. Event-row writing is left to the service/sp4 apply
  path (out of scope here).
- **`base_version`** is treated as the integer `requirement_versions.version` (decision #2); the
  caller resolves `base_content`/`head_content` from `get_version`/`get_current`.

## Verification

- `uv run pytest tests/test_conflict_predicate.py` → **20 passed**.
- Verdicts proven on the **real frozen doc + human-edited variant**: reworded FR-001 → `conflicted`,
  stable FR-002 → `clean`, deleted Out-of-Scope line → `orphaned`.
- **Property:** `detect_conflict` is never `clean` when HEAD region hash ≠ base region hash
  (parametrized set, stub locate).
- **Purity:** source asserted free of `sqlite`/`get_connection`/`anthropic`/`open(`/`requests`/
  `httpx`/`subprocess`; runs with a one-line lambda locate.
- Validation script `detect_conflict('A FR-1 body','A FR-1 body','FR-1 body',None, locate=...)`
  → `clean`.

## Success criteria

- [x] `detect_conflict` returns the four correct verdicts on the fixture variants.
- [x] Property holds: never `clean` when HEAD hash ≠ base hash.
- [x] Predicate is pure/total: no DB, no LLM, no I/O; `locate` is injected.
- [x] `content_hash` is reused (never reimplemented).
- [x] No second locator built; orphan surfaces (never a silent no-op).
- [x] No file in sp3b's scope touched (only `conflict.py` + tests + fixtures).

## Handoff to sp4 (sole file writer)

- Import `detect_conflict` / `region_hash` from `cast_server.requirements_render.conflict`.
- Resolve `base_content` via `requirement_version_service.get_version(slug, base_version)["content"]`
  and `head_content` via `get_current(slug)["content"]`; pass the production `cast-comment-reanchor`
  locator as `locate`.
- On `conflicted`/`orphaned`: write the `change_request_events` row and surface the
  `ConflictSurface` — do **not** apply. Only `clean` proceeds to surgical apply.
