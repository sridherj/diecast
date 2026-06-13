# Sub-phase 3a: Conflict Predicate — three-way content-hash check against base version

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase5/_shared_context.md` before starting.

## Objective

Make silent overwrite **structurally impossible**. A pure, total `detect_conflict(...)` returns
`clean | conflicted | orphaned` by comparing the target region's `content_hash` at `base_version`
vs HEAD — located by **quote, never by a stable ID**. A region a human touched since `base_version`
returns `conflicted` (→ surface, never overwrite); a quote that no longer locates returns `orphaned`
(→ surface). Zero silent overwrites by construction.

## Dependencies

- **Requires completed:** sp1 (the `change_request` shape; `base_version`).
- **Consumes (landed):** `requirements_render/hashing.py:content_hash`; the `cast-comment-reanchor`
  locator subagent; `requirement_version_service.get_version` / `list_versions` for the stored
  `content` at a given version.
- **Parallel with sp3b** — disjoint files (sp3a touches `requirements_render/`, sp3b touches
  routes/services/lifespan). Do not edit each other's files.

## Scope

**In scope:**
- A pure `detect_conflict(...)` + a `region_hash(...)` helper that locates a quote→region within a
  stored version's content and hashes it.
- The conflict-resolution **surface** model (the rendered 3-way choice), as data — not an auto-merge.
- Unit tests over the frozen fixture + checked-in edited variants.

**Out of scope (do NOT do these):**
- **No auto-textual-merge** in v2. The surface offers accept-incoming / keep-current /
  merge-with-free-edit — it does not compute a merge.
- Do **not** build a second quote→region locator. Reuse `cast-comment-reanchor`'s locator logic /
  the same verbatim-substring discipline; inject the resolver so the predicate stays pure.
- Do **not** write the file, the DB, or call an LLM **inside** the predicate (resolution is injected).
- Do **not** touch sp3b's outbox/notification files.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/requirements_render/conflict.py` | Create | Does not exist |
| `cast-server/tests/test_conflict_predicate.py` | Create | Does not exist |
| `cast-server/tests/fixtures/refine_requirements_v2/` | Use/extend | Frozen `refined_requirements.collab.md` fixture + add checked-in edited variants |

## Detailed Steps

### Step 3a.1: `region_hash(...)` — locate then hash

`requirements_render/conflict.py`:

```python
from cast_server.requirements_render.hashing import content_hash

def region_hash(content: str, target_quote: str | None, section_hint: str | None,
                *, locate) -> str | None:
    """Hash of the located target region within `content`. None if the quote does not locate.

    `locate(content, target_quote, section_hint) -> str | None` is INJECTED — it is the
    quote→region resolver (the cast-comment-reanchor locator discipline: verbatim-substring first,
    section_hint as a tiebreak). Keeping it injected keeps this function pure and unit-testable
    with no DB, no LLM, no I/O.
    """
    if target_quote is None:                 # pure addition has no target region to conflict on
        return None
    region = locate(content, target_quote, section_hint)
    return content_hash(region) if region is not None else None
```

> The default `locate` for production is the verbatim-substring resolver the `cast-comment-reanchor`
> server-side backstop already implies (a non-present quote returns None → `orphaned`). The
> *judgement* relocation (reword detection) is the subagent's job at apply time (sp4); the predicate
> only needs the deterministic locate-or-None.

### Step 3a.2: `detect_conflict(...)` — pure, total

```python
def detect_conflict(base_content: str, head_content: str,
                    target_quote: str | None, section_hint: str | None,
                    *, locate) -> str:
    """Return 'clean' | 'conflicted' | 'orphaned'. Pure and total.

    - Pure addition (target_quote is None): always 'clean' (nothing to conflict on).
    - Quote does not locate in HEAD: 'orphaned' (→ surface; never silently no-op).
    - region_hash(base) == region_hash(HEAD): 'clean'.
    - else: 'conflicted' (→ surface; never overwrite).
    """
    if target_quote is None:
        return "clean"
    head = region_hash(head_content, target_quote, section_hint, locate=locate)
    if head is None:
        return "orphaned"
    base = region_hash(base_content, target_quote, section_hint, locate=locate)
    return "clean" if base == head else "conflicted"
```

The caller resolves `base_content` / `head_content` from
`requirement_version_service.get_version(slug, base_version)["content"]` and `get_current(slug)["content"]`.

### Step 3a.3: Conflict-resolution surface (data, not merge)

Model the 3-way choice as a structured descriptor the render layer/intake can present
(Jama "suspect until cleared" semantics): `accept-incoming` / `keep-current` / `merge-with-free-edit`.
Every transition is recorded as a `change_request_events` row (`conflicted`, then `accepted`/
`rejected`/`superseded`) — **the event writing happens in the service/sp4 apply path**, not inside
the pure predicate. sp3a only defines the verdict + the choice vocabulary.

## Verification

### Automated Tests (permanent)
`cast-server/tests/test_conflict_predicate.py` over the frozen fixture + checked-in edited variants:
- **unchanged-since-base** → `clean`.
- **human edited the region since base** → `conflicted`.
- **quote deleted since base** → `orphaned`.
- **pure addition** (`target_quote=None`) → `clean`.
- **Property:** `detect_conflict` never returns `clean` when the HEAD region hash ≠ base region
  hash (assert across a small generated set of (base, head) pairs with a stub `locate`).
- **Purity:** the predicate runs with a pure-python stub `locate` and **no** DB, LLM, or I/O.

### Validation Scripts (temporary)
- `uv run python -c "from cast_server.requirements_render.conflict import detect_conflict; print(detect_conflict('A FR-1 body', 'A FR-1 body', 'FR-1 body', None, locate=lambda c,q,s: q if q in c else None))"` → `clean`.

### Manual Checks
- `grep -rn "import" cast-server/cast_server/requirements_render/conflict.py` → no `sqlite`, no
  agent/LLM import, no `open(`/file I/O in the predicate module.

### Success Criteria
- [ ] `detect_conflict` returns the four correct verdicts on the fixture variants.
- [ ] Property holds: never `clean` when HEAD hash ≠ base hash.
- [ ] Predicate is pure/total: no DB, no LLM, no I/O; `locate` is injected.
- [ ] `content_hash` is reused (never reimplemented).
- [ ] No second locator built; orphan surfaces (never a silent no-op).
- [ ] No file in sp3b's scope touched.

## Execution Notes
- Keep the predicate pure/total mirroring Phase 3b's `resolve` discipline — it must be unit-testable
  without a DB or model. This is the load-bearing "zero silent overwrites by construction" guarantee.
- The thin-spine fragility: with no stable IDs, conflict detection **is** quote-location. The orphan
  case is not an error — it is a first-class verdict that must surface to a human.
- **Spec-linked files:** `conflict.py` lands in `requirements_render/`, covered by
  `cast-requirements-render.collab.md`. You are adding a new pure module, not changing the render or
  comment behavior — no SAV regression. The conflict *semantics* are documented in the new roundtrip
  spec (sp5).
