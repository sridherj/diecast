# Sub-phase 3.2: Execution Drill-In — Runs, Dispatch Tree, Maker-Checker Loop

> **Pre-requisite:** Read
> `docs/execution/product-revamp-diecast-phase3-feature-debug-morph/_shared_context.md` before
> starting. Every BINDING CONSTRAINT there applies here.

## Objective

From the feature canvas, one click (`drillInto:execution`) opens the **HOW** panel: a run list;
expanding the focus run reveals its **~13-node dispatch tree** (run_node idiom: status dots, rework
tags, context bars, skill chips, failure rollup) and the **maker-checker iteration panel** (paired
lockups, M04/S03/R02 finding rows, rework meter 1/3, named exits fix/retry/escalate, PR diff stub).
The span tree exists **nowhere else** in the prototype. The two components (`RunNode`,
`IterationPanel`) are built **pure / props-only** so Phase 5a reuses `IterationPanel` on the ticket
view without rework.

## Dependencies
- **Requires completed:** **Sub-phase 3.1** — the `execution` data in ORG (generator-authored,
  gate-green) and the canvas shell that hosts the Execution tab.
- **Assumed codebase state:** `#/goal/CAST-412` is the real feature canvas; `ORG.goals['CAST-412']
  .execution` carries `runs[]`, the ~13-node `focus_run` tree, and `iteration{...}`;
  `ORG.goals['CAST-431'].execution` is thin (2 runs, no deep tree).

> **Serial-execution note (autonomous override):** the plan calls 3.2 "parallel-capable with 3.3",
> but both edit the same `prototype/index.html` with no merge mechanism between runner agents.
> **3.2 runs serially before 3.3.** Partition your additions into a clearly-bannered `exec-*` section
> so 3.3's edits stay disjoint. Do **not** dispatch 3.3 concurrently.

**Estimated effort:** 1 session (~3h).

## Scope

**In scope:**
- `RunNode({node, depth})` — recursive pure htm port of the `run_node.html` *visual idiom*.
- The Execution-tab shell (`drill === 'execution'`) below the canvas zones (shared chrome across
  families — the debug canvas gets it for free in 3.3).
- `IterationPanel` — maker/checker lockups, finding rows, rework meter, named exits.
- The PR diff stub (data from `iteration.pr.diff_stub`), framed as a `pr-thread` surface.
- One scripted feature-script drill beat that opens the tab and expands the focus run.

**Out of scope (do NOT do these):**
- Re-authoring ORG data — the `execution` blocks already exist (3.1). No generator edits here unless
  a data shape bug is found (then fix in the generator, never hand-edit `org.js`).
- The debug canvas (`#/goal/CAST-431`) — that is **3.3** (it merely *inherits* this exec tab).
- The morph / `vt-evidence-strip` / slop gate — **3.4**.
- Any summary mini-tree on the WHAT surface (trace-creep — the #1 pitfall).
- **Any test file, suite, harness, or CI.**

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `prototype/index.html` | Modify | Has 3.1's feature canvas; gains `RunNode`, `IterationPanel`, exec-tab shell (`exec-*` section), the drill script beat |
| `cast-server/cast_server/templates/macros/run_node.html` | **Read only (reference)** | The visual idiom to lift — **do not modify** |

## Detailed Steps

### Step 3.2.1: Port the `run_node.html` idiom to `RunNode({node, depth})`
- A **recursive pure htm component**. Lift the *visual logic* — rail-threaded recursion,
  `has-failure`/`has-warning` rollup classes, `↻ rework #N`, ctx-tint classes, status dots, skill
  chips — **not** the Jinja markup.
- Colors map to prototype tokens: `--fail` for failure tint, `--warn` for rework, maker/checker hues
  on agent chrome only.
- **Guard:** an unknown agent slug (can't happen given the 3.1 generator invariant, but guard anyway)
  renders the slug raw with a visible `?` avatar rather than throwing mid-demo.
- **No appState reads** — props only (so Phase 5a can reuse it).

### Step 3.2.2: Build the Execution-tab shell
- `drill === 'execution'` renders the panel **below** the canvas zones (shared chrome across
  families). Run-list rows: `status dot · agent · when · one-line summary · rework count`.
- Expanding a row swaps in the focus-run detail (tree + iteration panel). **Only the focus run
  carries a tree** (HOLD SCOPE). Toggling the tab / browser-back flips `appState.drill` cleanly; the
  WHAT content above remains untouched.
- New CSS prefix `exec-*`. Keep this in its own banner section.

### Step 3.2.3: Build `IterationPanel`
- Maker/checker `ColleagueCard` line-density pair (bracket-tie pairing device).
- Finding rows: `code · label · round · status` — resolved ✓ / flagged ⚠ (M04 ✓ · S03 ✓ · R02 ⚠).
- Rework meter from `iteration.rework` (3-segment, at 1/3).
- Named-exit buttons (`fix / retry / escalate`) — visually complete but **inert** (no console errors
  on click) except any script-wired one; the **escalate** exit is visually tied to the L3 chip's rail
  (same raspberry needs-you semantics).
- **Pure / props-only** (no appState reads) — Phase 5a reuses it.

### Step 3.2.4: PR diff stub
- A small mono two-file diff excerpt (data from `iteration.pr.diff_stub`), framed as a `pr-thread`
  surface — consistent with the `pr-thread` `StageSurface` kind. **This renders here, and only here**
  — the canvas carries the PR *link* (3.1), the tab carries the *diff* (locked Q#17 call).

### Step 3.2.5: Wire the feature script's drill beat
- One scripted step opens the Execution tab and expands the focus run (`drillInto:execution` +
  patch), so the demo never depends on a human finding the tab.

## Verification (manual click-through — NO TESTS)

### Manual Checks
- From `#/goal/CAST-412`, click the Execution tab → run list renders (~4 runs from
  `goal.execution.runs`); WHAT content above remains untouched; browser-back / re-clicking the tab
  toggles `appState.drill` cleanly.
- Expand the focus run → the dispatch tree renders **~13 nodes** with: per-node status dot, agent
  name (mono), one `↻ rework #1` tag, context-usage bars, skill chips, and a failure/warning tint
  rolled up the thread rail — **squint-comparable to the `/runs` page idiom**.
- The iteration panel shows maker + checker as line-density lockups, the three finding rows with
  per-round status, the 3-segment rework meter at **1/3**, and the three named exits as
  visually-complete buttons. Exits are **inert** (no console errors on click) except any script-wired one.
- The PR diff stub renders **here, and only here**.
- **Disclosure depth audit:** run list (level 1) → expanded run (level 2) — nothing requires a third
  click to understand (NN/g cap).
- **Count check:** exactly **one** element in the DOM ever renders the span tree; search `RunNode`
  call sites → **exactly one**. `#/goal/CAST-431`'s exec tab shows its thin run list with **no deep
  tree** (verify after 3.3 lands the debug route; for now confirm the thin `execution` data exists).

### Success Criteria (binary — every item must pass)
- [ ] Execution tab opens from the feature canvas; WHAT content above untouched; `drill` toggles cleanly.
- [ ] Focus run expands to ~13-node tree with status dots, `↻ rework #1`, ctx bars, skill chips, failure rollup.
- [ ] `IterationPanel`: maker/checker lockups, M04/S03/R02 rows, rework meter 1/3, three inert named exits.
- [ ] PR diff stub renders only in the exec tab.
- [ ] **Trace-creep guard:** exactly one `RunNode` call site; no mini-tree on the WHAT surface.
- [ ] `RunNode` + `IterationPanel` are pure props-only (no appState reads).
- [ ] Scripted drill beat opens the tab + expands the focus run.

## Execution Notes
- **Trace-creep is the #1 pitfall:** the tree renders only inside the exec panel — no summary
  mini-tree on the WHAT surface. Review: search `RunNode` call sites → exactly one.
- **Performance sanity:** ~13 nodes re-render inside `startViewTransition` snapshots during morphs.
  Keep the exec panel **closed** during the morph script step (it's a different beat in 3.4), so tree
  DOM never participates in the transition. Architect for this now (the tab's open/closed state is
  `appState.drill`).
- If a data-shape bug surfaces (e.g. a tree node's agent missing from `ORG.agents`), **fix it in the
  generator and regenerate** — never hand-edit `org.js`; keep additions byte-stable (F4).
- **Naming:** `RunNode` / `IterationPanel` PascalCase; CSS `exec-*`.
- **Spec-linked files:** none (greenfield, FR-020). `run_node.html` is read-only reference.
- **Failure policy:** retry once; on critical path (it is) a second failure → **stop and report**.
