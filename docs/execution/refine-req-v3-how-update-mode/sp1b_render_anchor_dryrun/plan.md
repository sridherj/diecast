# Sub-phase 1b: Evidence — Render-Anchor Dry-Run

> **Pre-requisite:** Read `docs/execution/refine-req-v3-how-update-mode/_shared_context.md` before
> starting — especially the Crux Decision (render-snapshot anchoring) and the `block_ref` bridge contract.

## Objective

Measure the **placement and `block_ref`-bridge rate** of real existing comments against published
render text — productionizing the exact procedure Sub-phase 2's migration + creation path will use.
This **sizes the Sub-phase 2 migration**: how many existing comments place cleanly, how many resolve a
unique `block_ref`, and how the misses classify (cross-boundary / decoration-spanning). Read-only
against production code; **no production edits in this sub-phase.**

## Dependencies

- **Requires completed:** None. Runs in parallel with Sub-phase 1a (disjoint outputs, no shared files).
- **Assumed codebase state:** `container_text_index` (`maker_gate.py:259`), `Container.unit_at`
  (`maker_gate.py:175`), `comment_anchor.resolve_block_ref` (`comment_anchor.py:29`) /
  `resolve_block_context` (`:52`) exist; the v2 fixture pair (`refined_requirements.collab.md` +
  `.v2-edit`) and any live comments on the v3 goal are available; a published render artifact
  (`goals/{slug}/refined_requirements.html`) exists to validate against.

## Scope

**In scope:**
- Re-validate **every existing open comment** (the v2 fixture pair + any live v3-goal comments) against
  the corresponding **published render text** (not the `.collab.md`).
- For each comment, measure: does the quote **place** (`container_text_index.find` over the rendered
  DOM)? Does it resolve to a **single labeled unit container** (`unit_at` + the anchor label →
  the `block_ref` bridge)?
- Compute **placement rate** and **cross-boundary rate**; classify every miss.
- A Python re-implementation dry-run — **no browser** (autonomous runs can't connect Chrome; per
  project convention the visual half is a static verdict + human-eyeball carry-forward).
- An explicit PASS/FAIL verdict + a **migration-sizing table** written to
  `spikes/render-anchor/verdict.md`.

**Out of scope (do NOT do these):**
- NO production code edits — measurement only. The render-space resolver this dry-run prototypes is
  productionized in Sub-phase 2, not here.
- Do NOT reopen the anchoring decision (it is locked); 1b **sizes** the migration, it does not decide it.
- Do NOT drive a browser; the placement check is the Python `container_text_index.find` re-implementation
  of what `requirements_comments.js` already does on the rendered DOM.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `docs/goal/refine-requirements-better-rendering-v3/spikes/render-anchor/verdict.md` | Create | Does not exist — PASS/FAIL + migration-sizing table |
| `docs/goal/refine-requirements-better-rendering-v3/spikes/render-anchor/measurements/*.json` | Create | Per-comment placement + `block_ref` + miss-class records |

## Detailed Steps

### Step 1b.1: Gather the existing open comments + the render to validate against

- Pull the v2 fixture pair comments (`refined_requirements.collab.md` + `.v2-edit`) and any live open
  comments on the v3 goal (`comment_service.list_comments(slug, state="open")` read-only).
- Identify the **published render artifact** each comment should validate against
  (`goals/{slug}/refined_requirements.html` — the served render).

### Step 1b.2: Re-implement the render-space placement + `block_ref` resolution

For each open comment, run the exact procedure Sub-phase 2 will productionize:
1. `idx = container_text_index(render_html)` (import the shared walker — never re-walk by hand).
2. **Place:** does `quoted_text` appear in the rendered container text (`idx.find` semantics)?
3. **Bridge:** if it places, take the **enclosing labeled unit container** (`idx.unit_at(offset)` +
   the anchor label visible in that container) → resolve the canonical id = `block_ref`.
4. **Classify a miss:** cross-boundary (spans containers) / decoration-spanning (quotes render
   decoration absent from any unit) / no-anchor-label (ref-less container → `block_ref` would be NULL).

Record per comment: `{id, placed: bool, block_ref: str|null, miss_class: str|null}`.

### Step 1b.3: Aggregate + write the verdict + migration-sizing table

`spikes/render-anchor/verdict.md` ends with:

```
VERDICT: PASS | FAIL
PLACEMENT_RATE: <placed / total>
BLOCK_REF_UNIQUE_RATE: <in-block comments resolving a unique block_ref / in-block total>
MISS_BREAKDOWN: cross-boundary=<n>, decoration-spanning=<n>, no-anchor-label=<n>
MIGRATION_SIZING: <#flip-to-render, #stay-source (badge), #ref-less-NULL-by-construction>
```

- **PASS** iff **every comment minted via the page UI places, and in-block quotes resolve a unique
  `block_ref`; misses are classifiable** (cross-boundary / decoration-spanning), not mysterious.
- A `no-anchor-label` miss on a ref-less render is **expected and NOT a failure** — record it as
  `block_ref=NULL by construction` (plan-review Decision #1); it feeds Sub-phase 2's "ref-less NULL is
  success" handling, not the failure count.

## Verification

### Validation Scripts (temporary — this whole sub-phase is a spike)
- The dry-run harness is the validation: every existing open comment processed, each producing a
  measurement record under `measurements/`.
- A one-off aggregation prints placement rate, `block_ref`-unique rate, the miss breakdown, and the
  migration-sizing table; emits the `VERDICT` line.

### Manual Checks
- `grep -c "container_text_index\|unit_at" <dry-run harness>` — confirm the placement + bridge reuse
  the shared walker + `Container.unit_at`, never a hand-rolled walk.
- Confirm **zero** production files changed: `git status --short cast-server/ agents/` is clean.
- Confirm every miss carries a `miss_class` (no "mysterious" unplaced comment).

### Success Criteria
- [ ] Every existing open comment (v2 fixture pair + live v3 comments) validated against published
      render text.
- [ ] Placement rate, `block_ref`-unique rate, and a classified miss breakdown recorded.
- [ ] `block_ref=NULL`-by-construction (ref-less render) recorded as **success**, not a miss.
- [ ] `verdict.md` ends with an explicit `VERDICT` + a `MIGRATION_SIZING` table Sub-phase 2 consumes.
- [ ] Placement/bridge reuse `container_text_index` + `unit_at`; no second walker.
- [ ] No production code edited.

## Execution Notes

- **This verdict sizes Sub-phase 2's migration**, it does not gate it (the anchoring decision is
  locked). Make the `MIGRATION_SIZING` numbers concrete — Sub-phase 2's migration is the productionized
  version of this exact dry-run.
- The miss classification carries forward verbatim into Sub-phase 2's creation path: cross-boundary →
  `block_ref=NULL` (never guessed — `resolve_block_ref` orphan-over-guess discipline); ref-less render
  → `block_ref=NULL` by construction (success, not a miss).
- **No browser** — the visual confirmation that a UI-minted quote highlights is a static verdict +
  human-eyeball carry-forward (project convention), never a blocking gate in an autonomous run.
