# Sub-phase 5c: Requirements-Doc Loop (US7)

> **Pre-requisite:** Read
> `docs/execution/product-revamp-diecast-phase5-colleague-surfaces/_shared_context.md` before
> starting this sub-phase. The binding constraints there are not optional.

## Objective

`#/reqs/CAST-412` renders the requirements vision: **classification pill** up top, **L1/L2/L3
progressive disclosure** over the element hierarchy, **one anchored inline comment thread** (with the
prototype's single PM-framed moment), a **v1→v2 change summary** anchored to affected elements, and
the **"requirements updated from planning — review the delta" write-back notice** — all reading from
`goals['CAST-412'].requirements_doc`.

## Dependencies
- **Requires completed:** Sub-phase 5.0 (the `requirements_doc` ORG slice, the `#/reqs/CAST-412` route
  stub, the `reqsDoc` appState key, the `DigestNotice` component).
- **Independent of 5a/5b** (parallel-safe — disjoint route + `reqs-*` prefix). See the file-collision
  honesty note in the manifest.

## Estimated effort
0.75–1 session (~2.5–3h).

## Scope
**In scope:** the `#/reqs/CAST-412` renderer; the anchored comment thread; the delta-review toggle;
the write-back `DigestNotice` instance; the decision chip on the REST-over-GraphQL element; the in-flow
entry link from the CAST-412 canvas's requirements stage.
**Out of scope (do NOT do these):** the board arc / trail / dial (5a); hiring/marketplace/ops/Layer-2
(5b); minting a sixth op; defining a second `DigestNotice`; any test file; any hand-edit of `org.js`;
touching the Phase 4 canvas/parity sections.

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `prototype/index.html` | Modify | Carries the 5.0 stub for `#/reqs/CAST-412`; gains the real `reqs-*` renderer + the entry link on the CAST-412 requirements stage |

## Detailed Steps / Key Activities

- **Doc render:** header = workflow **classification pill** ("feature", mono treatment) + version chip
  (v2) + version history popover. Body = the element hierarchy with **L1/L2/L3 progressive disclosure
  via native `<details>`** (Phase 4's notebook-cell precedent): L1 always visible, L2 one disclosure
  in, L3 nested — **hierarchy depth is expressed typographically** (size/indent/weight), explicitly
  **NOT** with the colored L-badges (see design review).
- **Anchored inline comment thread:** exactly one element carries a comment affordance; clicking opens
  the **side-anchored thread** (2–3 messages) where one commenter is the **PM** (circle avatar + role
  tag from `ORG.humans`) — **the one PM-framed moment in the whole prototype**; the thread shows
  open/resolved states. `appState.reqsDoc.openComment` drives it.
- **Version change summary (delta review):** `reqsDoc.deltaView` toggles a **diff-first** change list
  (same row grammar as the decision trail) anchored to affected elements — **review the delta, not
  re-read the doc**.
- **Write-back notice:** `DigestNotice` instance at the top — "↺ requirements updated from planning —
  review the delta", naming the originating phase; opens `deltaView`. **Same component as 5a's L2
  digest by contract.**
- **Decision chip on a requirement element** (the REST-over-GraphQL atom via its `influenced[]`
  anchor) — completing **chip anchor-generality across all three anchor types** (ticket: 5a; canvas
  stage: Phase 3; requirements element: here).
- **Entry links:** nav-rail/goal-header path onto the doc from the CAST-412 canvas's requirements
  stage (an `<a href="#/reqs/CAST-412">` on the stage's doc surface — **no new op**), so the doc is
  reachable in-flow, not only by URL.

## Verification

> **NO TESTS (binding):** every check below is **manual click-through / static observation**. In an
> autonomous run with no browser, satisfy each via the strongest static evidence (`node --check`,
> grep audits, a throwaway `/tmp` logic harness that is never committed) and record a non-blocking
> human-eyeball carry-forward for any rendered-pixel item. **Do not flag missing tests.**

**Verification (manual, from disk) — verbatim from the plan:**
- Open `#/reqs/CAST-412`: pill + version chip visible.
- Collapse/expand L2 and L3 levels via disclosure.
- Click the commented element → the thread opens anchored beside it, the PM commenter visibly
  role-tagged, open→resolved state togglable (display states).
- The write-back notice names the originating phase and clicking it opens the delta view, whose rows
  highlight/scroll to their anchored elements.
- The decision chip on the REST-over-GraphQL element opens its 6B popover and matches the trail row's
  ID on `#/decisions/CAST-412`.
- Delta rows / comments anchoring to a collapsed L3 element auto-expand the disclosure chain on
  navigate (zero silent failures — a highlight inside a closed `<details>` is invisible).

### Success Criteria (binary — every item must pass or carry forward with reason)
- [ ] `#/reqs/CAST-412` renders the classification pill + v2 chip + version-history popover.
- [ ] L1/L2/L3 hierarchy expressed **typographically** via native `<details>`; **no colored L-badges**
      on hierarchy depth.
- [ ] The one anchored comment thread opens side-anchored; the PM commenter is role-tagged (circle
      avatar from `ORG.humans`); open/resolved toggles.
- [ ] `reqsDoc.deltaView` shows a diff-first change list anchored to affected elements.
- [ ] The write-back `DigestNotice` is the **same component** as 5a's (exactly one definition in
      source); opens `deltaView`.
- [ ] The REST-over-GraphQL decision chip opens its 6B popover; ID matches the `#/decisions/CAST-412`
      trail row.
- [ ] Anchoring into a collapsed L3 auto-expands the disclosure chain; closed 5-op set intact; 6×1 vt-
      anchors unchanged; `node --check` clean.

## Design review (verbatim from the plan)
- ⚠ **L1/L2/L3 collision (the sharpest flag in this phase):** US7's L1/L2/L3 are *hierarchy levels*;
  the decision system's L1/L2/L3 are *reversibility*. Both appear on this one screen (hierarchy + a
  decision chip). **Rule:** hierarchy = typographic depth only, **never badges**; reversibility = the
  2b colored badge always prefixed with ⚖ context. Flagged in the table.
- **Reuse integrity:** the write-back notice and the L2 digest are **one component** (PB-05 hand-off
  #3) — verified by there being exactly one `DigestNotice` in the source. ✓
- **Edge:** delta rows / comments anchoring to a collapsed L3 element must auto-expand the disclosure
  chain on navigate (zero silent failures — a highlight inside a closed `<details>` is invisible).

### Design Review Flags (this sub-phase's rows, verbatim from the plan)
| Sub-phase | Flag | Action |
|-----------|------|--------|
| 5c | L1/L2/L3 double meaning (hierarchy vs reversibility) on one screen | Hierarchy = typographic depth, no badges; reversibility = ⚖-prefixed colored badge only |
| 5c | Anchored highlight inside collapsed `<details>` is invisible | Auto-expand the disclosure chain on comment/delta navigation |
| all | New routes could mint duplicate vt- names | No new vt- names; anchors live on shell zone wrappers only (2b rule) |

## Execution Notes
- **One PM-framed moment, prototype-wide:** the single `pm`-role comment author is gate-enforced in
  5.0's generator invariant — render its role tag from `ORG.humans`, never hardcode the persona name.
- The write-back `DigestNotice` and 5a's L2 digest are **the same component, two instantiations** —
  do not define a second; 5.4's drift/slop pass verifies exactly one definition in source.
- **Chip anchor-generality:** this sub-phase completes the third anchor type (requirements element)
  for the decision chip; the ID must match the `#/decisions/CAST-412` trail row (5a) — a cross-stream
  ID-match spot-checked in 5.4.
- **Spec-linked files:** none — greenfield (FR-020); no `/cast-update-spec`.
- **Plan review:** SKIPPED per run config — do not dispatch `/cast-plan-review` or any reconciliation
  pass.
