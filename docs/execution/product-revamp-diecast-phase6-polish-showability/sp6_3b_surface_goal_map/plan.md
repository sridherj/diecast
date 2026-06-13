# Sub-phase 6.3b: The Map — Surface→Buildable-Goal Roadmap (SC-006) (parallel with 6.3a)

> **Pre-requisite:** Read
> `docs/execution/product-revamp-diecast-phase6-polish-showability/_shared_context.md` before
> starting this sub-phase. The binding constraints there are not optional.

## Objective

`docs/plan/product-revamp-diecast-v2-surface-goal-map.md` exists: every prototype surface maps to a
named, buildable, stack-rankable follow-on v2 goal — the **input document for the post-mockup v2
planning session**. SC-006 is satisfiable the moment that session convenes. This sub-phase is **OFF
the critical path** and is the **one truly parallel-safe member** of its group (it writes only this one
doc; it never touches `prototype/index.html`).

## Dependencies
- **Requires completed:** Sub-phase **6.2** (surfaces final — the map describes **what actually
  shipped**).
- **Independent of 6.3a; runs in parallel** (disjoint files — 6.3a edits `index.html` + creates the
  dist; 6.3b creates only this map doc). No serialization needed.
- **Assumed codebase state:** the full final route inventory exists and is content-final post-6.2.

## Estimated effort
0.5 session (~1.5h).

## Scope
**In scope:** authoring `docs/plan/product-revamp-diecast-v2-surface-goal-map.md` — per-theme tables of
surfaces → v2 goals + cross-cutting-mechanic rows + the FR/US cross-reference + the demo-chrome
exclusions note.
**Out of scope (do NOT do these):** **any touch of `prototype/index.html`** or any other code file;
the inliner / dist (6.3a); any new surface/component/op; any ORG change; any test file; duplicating
the separate refine-requirements-v2 goal (reference it, don't duplicate).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `docs/plan/product-revamp-diecast-v2-surface-goal-map.md` | Create | Does not exist — the SC-006 deliverable, sibling to `decisions-so-far.md` in `docs/plan/` |

## Detailed Steps / Key Activities

### Step 6.3b.1: One table per theme group
Rows = surfaces; columns: **Surface/Route** · **What it proves** (FR/US/SC refs) · **Follow-on v2
goal** (kebab slug + one-line outcome) · **Size** (S/M/L) · **Depends on** (other v2 goals) ·
**Suggested rank**. Theme groups:
- **canvas core & morph** — render architecture, family canvases, chat steering
- **evidence** — E1–E5 as real artifact pipelines
- **decisions & autonomy** — atom capture, trail, dial, escalation
- **colleague surfaces** — board, ticket, hiring, marketplace, agent ops
- **platform substrate** — scenario-engine→real chat, `org.js`→real API, three access tiers
- **requirements loop** — ties to the **separate refine-requirements-v2 goal** (reference, don't
  duplicate)

### Step 6.3b.2: Cross-cutting mechanics get rows too
The morph itself, the decision-receipt mechanism, the L1/L2/L3 autonomy engine, the slop-gate-as-CI
idea — SC-006 says *each surface maps to a buildable goal*, and **the mechanics are the most
build-relevant "surfaces" of all.**

### Step 6.3b.3: Advisory rank + exhaustiveness
- **Suggested rank is advisory:** the column seeds the stack-ranking conversation; **the v2 planning
  session owns the final order.** State this in the doc's preamble.
- Cross-reference each row against the **refined requirements' FR/US table** so no FR lands unmapped;
  note explicitly which v1 prototype elements are **demo chrome with no v2 goal** (tours, demo overlay,
  inliner) so the map is **exhaustive rather than silently partial**.

> **Route inventory the map must cover exactly once each:** `#/` (chooser) + the four goal canvases
> (`#/goal/CAST-412|431|452|461`) + the 10 Phase-5 routes (`#/board · #/ticket/CAST-412 ·
> #/decision/:atomId · #/decisions/CAST-412 · #/hire · #/marketplace · #/agent/:slug · #/skills/new ·
> #/layer2 · #/reqs/CAST-412`) + the cross-cutting mechanics. (`#/kit` is the hidden harness — list it
> as demo chrome, no v2 goal.)

## Verification

> **NO TESTS (binding):** this sub-phase produces a document. Verification is **reading the document
> against the route inventory + the FR/US table.** **Do not flag missing tests.**

**Verification (manual) — verbatim from the plan:**
- Every route in the final inventory (chooser + 4 goal canvases + 10 Phase-5 routes + the
  cross-cutting mechanics) **appears exactly once**.
- Every row names a **concrete goal slug** with an **outcome sentence**, a **size**, **dependencies**,
  and a **suggested rank**.
- **A cold reader could create the v2 goal backlog from this document alone.**

### Success Criteria (binary — every item must pass or carry forward with reason)
- [ ] The doc exists at `docs/plan/product-revamp-diecast-v2-surface-goal-map.md` with a preamble
      stating that rank is advisory (the v2 session owns final order).
- [ ] One table per theme group (canvas core & morph · evidence · decisions & autonomy · colleague
      surfaces · platform substrate · requirements loop); every route in the inventory appears exactly
      once.
- [ ] Cross-cutting mechanics (morph, decision-receipt, L1/L2/L3 autonomy, slop-gate-as-CI) each get a
      row.
- [ ] Every row has a kebab goal slug + a one-line outcome (what is true when done) + S/M/L + deps +
      suggested rank — **no vague "improve the board"-style goals.**
- [ ] Every FR/US in the refined-requirements table is mapped or explicitly noted as demo chrome with
      no v2 goal (tours, demo overlay, inliner); the requirements loop references — not duplicates —
      the separate refine-requirements-v2 goal.
- [ ] **`prototype/index.html` and all other code files are untouched** (this sub-phase is doc-only).

## Design review (verbatim from the plan)
- ⚠ **Vague-goal risk:** "improve the board" is not buildable. Rule in activities: **every row's goal
  has a one-line *outcome*** (what is true when done), same discipline as the Phase 6 plan's
  sub-phases.
- **Location/naming:** `docs/plan/` beside the decisions-so-far doc, project-prefixed name —
  consistent with the planning artifact convention. ✓

### Design Review Flags (this sub-phase's rows, verbatim from the plan's consolidated table)
| Sub-phase | Flag | Action |
|-----------|------|--------|
| 6.3b | Map rows degenerate into vague themes | Every row needs a one-line outcome, same bar as sub-phase outcomes |

## Execution Notes
- **Truly parallel-safe (the project first):** this sub-phase **never opens `prototype/index.html`** —
  it writes one new doc in `docs/plan/`. Dispatch it concurrently with 6.3a with zero merge risk.
- **Off the critical path:** failure policy here is **log-a-gap-and-continue** on a second failure
  (the critical path is 6.1 → 6.2 → 6.3a → 6.4). It can also absorb idle time during 6.2's checker
  runs.
- **Reference, don't duplicate** the separate refine-requirements-v2 goal — the requirements loop row
  points at it.
- **Spec-linked files:** none — greenfield (FR-020); no `/cast-update-spec`. (Forward note: the v2
  goals this map names will author product specs when *they* are planned — downstream of this map.)
- **Plan review:** SKIPPED per run config — do not dispatch `/cast-plan-review` or any reconciliation
  pass.
