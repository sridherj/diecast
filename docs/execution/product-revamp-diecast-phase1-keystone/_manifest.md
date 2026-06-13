# Execution Manifest: Product Revamp: Diecast — Phase 1 (Keystone)

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:

1. Start a new Claude session in the repo root (`/home/sridherj/workspace/diecast`, which resolves to
   `/data/workspace/diecast`).
2. Tell Claude: "Read `docs/execution/product-revamp-diecast-phase1-keystone/_shared_context.md` then
   execute `docs/execution/product-revamp-diecast-phase1-keystone/spN_<name>/plan.md`."
3. After completion, update the Status column below.

Source plan: `docs/plan/2026-06-11-product-revamp-diecast-phase1-keystone.md`.
Decisions ledger (1.3 appends the morph-gate verdict here):
`docs/plan/product-revamp-diecast-decisions-so-far.md`.

**Run mode: FULL AUTONOMY (owner-approved).** No user questions, no approval gates, no idle waits.
At decision points pick the recommended option and document it. Propagate the directive to any child.

**Binding constraints (full text in `_shared_context.md`):**
- **C1 — NO TESTS** anywhere. Verification is manual click-through only (open `prototype/index.html` from disk in Chrome, observe).
- **C2 — file:// legality.** Single-file inline architecture is forced: no `fetch()`, no local ES-module imports; only https CDN import-map imports, classic `<script src>`, relative `<img>`.
- **C3 — Packaging.** Prototype code root `prototype/`; Phase 1 ships exactly one file, `prototype/index.html`.
- **C4 — Contracts.** The 7 contracts (appState v1, 5-op vocabulary, scenario step shape, `vt-` anchors, design + motion tokens, packaging rule) are encoded verbatim and extended-not-renamed downstream.
- **C5 — Failure policy.** Retry a failed sub-phase once with refined instructions; second failure → mark partial and log the gap.

## Sub-Phase Overview

| #   | Sub-phase                                              | Directory/File          | Depends On | Status      | Notes |
|-----|--------------------------------------------------------|-------------------------|------------|-------------|-------|
| 1.1 | Skeleton — one file, one state, one render             | `sp1_skeleton/`         | —          | Done        | Created `prototype/index.html` (single file): pinned import map (preact 10.26.2 / htm 3.1.1 / driver.js 1.3.1 unimported) + verbatim `:root` tokens + motion/radius tokens + appState v1 (2 placeholder spines) + hash router (`#/`·`#/goal`·`#/board`) + three-tier shell w/ 5 persistent vt-anchor wrappers. Verified statically (JS syntax OK, no `fetch(`/local imports, all 7 contracts encoded). **Live browser click-through NOT run — Chrome extension not connected**; deferred to manual eyeball or 1.2's session. |
| 1.2 | Nervous System — typed-op dispatcher & scenario engine | `sp2_nervous_system/`   | 1.1        | Done        | Added the closed-5-op dispatcher (`dispatch`+`fade` ≈12 lines vanilla, one delegated `[data-op]` listener, unknown-op `console.warn`+no-op, `startViewTransition` guarded by support + `prefers-reduced-motion`), the five op fns (`morph` flips family + pushes the L2 receipt stub; `nudge` cycles two canned nudges; `promote`/`pin` kept DISTINCT — different `kind`; `drillInto` toggles a stub exec panel), the array-walker scenario engine (`advance`, 15 lines, state in `appState.chat.scriptIndex` → reload resets), the 7-step demo script (open → Guide nudge → user line → `morph:debug`+receipt → iter 2/3 bump → reverse `morph:feature` undo proof → promote-the-receipt 6b), ChatRail conversation log + `Next ▸` control, canned reply carries a `data-op` button, and the TEMPORARY dev op-strip (incl. a bad-op button for the unknown-op path) marked `<!-- DEV OP STRIP — remove or gate behind #/dev in 1.3 -->`. **Static-verified** (`node --check` of the inline module passes; grep-clean of `fetch(`/local imports; single delegated listener; one file). **Live browser click-through NOT run — Chrome extension not connected** (same as 1.1); deferred to manual eyeball or 1.3's session. Decision (full autonomy): the optional `console.debug('dispatch',…)` crutch was OMITTED rather than added-then-removed, since its required end-state is "removed" and no browser was available to use it — single-dispatch path verified statically instead. |
| 1.3 | Proof — hero morph spike & decision gate               | `sp3_proof/`            | 1.2        | Done        | Tagged the 5 `vt-` anchors (each unique per snapshot, mounted across both families), added the `::view-transition-group(*)` 350ms register + reduced-motion CSS guard, built the two contrasting watermarked spines (feature segment bar ↔ debug loop band + `↺ iter 2/3`), the 6A receipt pill, gated the dev op-strip behind a `#/dev` suffix, confirmed console-clean + <15KB (preact+htm only; driver.js mapped-not-imported). **Morph gate VERDICT = PASS (5/5 static; item 4 taste-call PROVISIONAL — no browser connectable)** → View Transitions LOCKED for Phase 3; panel-swap contingency NOT built. Verdict recorded in `decisions-so-far.md` + the sub-phase output. **Live click-through NOT run — Chrome extension not connected** (same as 1.1/1.2); item 4 flagged for human eyeball. |

Status: Not Started → In Progress → Done → Verified → Skipped

**No decision-gate (`gate_*`) files.** The phase's only gate — the morph verdict — is resolved
**inside sub-phase 1.3**, autonomously, via a pre-written 5-item checklist (FULL AUTONOMY is in
effect; it is explicitly *not* modeled as a separate human `G`-node). A "fail" verdict is a
successful recorded outcome that triggers the in-1.3 panel-swap contingency — not a sub-phase failure.

## Dependency Graph

```
sp1_skeleton ──▶ sp2_nervous_system ──▶ sp3_proof ──▶ [morph verdict, resolved inside 1.3]
 (1.1)            (1.2)                  (1.3)            ├─ pass → Phases 2a/2b/2c build on View Transitions
                                                         └─ fail → adopt keyed CSS panel-swap (inside 1.3), then proceed
```

**Strictly sequential — no parallelism inside this phase.** 1.2 needs 1.1's render spine and the
synchronous-`paint()` rule; 1.3 needs 1.2's dispatcher + scenario engine. All three sub-phases edit
the **same single file** (`prototype/index.html`) in order, which is itself why they cannot run in
parallel. Total: ~2–3 sessions (1–1.5 days), matching the high-level estimate.

## Execution Order

### Sequential Group 1
1.1 **sp1_skeleton** — `prototype/index.html` opens clean from disk; three-tier shell in the Diecast
   light world; `render(appState)` the only paint path; ≥2 hash routes + back button; library <15KB.

### Sequential Group 2 (after 1.1)
1.2 **sp2_nervous_system** — all 5 ops route through one ~30-line dispatcher (with
   `startViewTransition` + reduced-motion guards); ~50-line scenario engine walks the ~6-step demo
   script (incl. `morph:debug` + reverse `morph:feature` undo proof) from the "Next ▸" control.

### Sequential Group 3 (after 1.2)
1.3 **sp3_proof** — the placeholder feature→debug hero morph as a ~350ms shared-element transition
   (≥4 gliding anchors, contrasting watermarked spine shapes, receipt pill, reduced-motion fade);
   run the 5-item gate checklist, record the verdict in the sub-phase output + `decisions-so-far.md`;
   on fail, build the panel-swap contingency; tidy for handoff (remove dev op-strip, console clean, <15KB).

## Files Touched by More Than One Sub-Phase

Unlike a multi-file phase, **all three sub-phases build up the same single file** — this is forced by
the file:// single-file constraint (C2/C3), and it is exactly why the sub-phases are strictly
sequential (they cannot be parallelized without colliding).

| File | 1.1 | 1.2 | 1.3 | Owner notes |
|------|-----|-----|-----|-------------|
| `prototype/index.html` | Create | Modify | Modify | Built additively: skeleton → dispatcher+engine → morph+gate. Each sub-phase assumes the prior one's structure (see each `plan.md` Dependencies). |
| `docs/plan/product-revamp-diecast-decisions-so-far.md` | — | — | Append | 1.3 appends the morph-gate verdict + 5-item evidence. |
| `docs/plan/product-revamp-diecast-borderline-calls.md` | — | — | Append (conditional) | 1.3 only, **only if** the gate verdict is "fail" (panel-swap taken). |

## Out-of-Manifest (intentionally NO sub-phase, NO gate file)

- **A separate human decision-gate (`gate_*` / `G`-node)** → not modeled. FULL AUTONOMY resolves the morph verdict inside 1.3 via the pre-written checklist.
- **Real surfaces / real data / component kit / per-family vocabulary / Guide character** → Phases 2a/2b/2c/3 (HOLD SCOPE).
- **`org.json` / data spine** → Phase 2a (and note: `fetch()` won't work from `file://` — freeze as an inline `<script type="application/json">` or a classic `prototype/org.js` setting `window.ORG`).
- **Any test file / harness / CI** → none, ever (Constraint C1).
- **`/cast-update-spec` or a new `docs/specs/` entry** → none this phase. The prototype is a greenfield design artifact; no spec applies (FR-020). New product specs are downstream, post-prototype.
- **`/cast-plan-review` auto-dispatch** → skipped per the run config in `product-revamp-diecast-decisions-so-far.md` ("Plan review: skipped — cross-phase reconciliation only", owner-approved). See `_review_summary.md`.

## Progress Log

<!-- Update after each sub-phase completes. -->
- **1.2 Nervous System — Done (2026-06-12).** Extended `prototype/index.html` additively (no rewrite, no key/token/anchor renames). Added the closed-5-op dispatcher + delegated listener, the five op fns, the array-walker scenario engine, the 7-step demo script (with the `morph:debug` / reverse `morph:feature` undo proof and a promote-the-receipt 6b step), ChatRail conversation log + `Next ▸`, and the temporary marked dev op-strip. Line budgets met (dispatcher ≈12, engine 15). Verified statically (`node --check` passes, file:// grep-clean, single delegated listener, single file). Live click-through deferred — Chrome extension not connected. Next: **1.3** adds `view-transition-name` anchor tagging, contrasting watermarked spine shapes, the receipt pill, removes/gates the dev op-strip, and runs the 5-item morph-gate checklist.
- **1.3 Proof — Hero Morph Spike & Gate — Done (2026-06-12).** Extended `prototype/index.html` additively (no key/token/anchor/op renames). (1) Tagged all five `vt-` anchors with `view-transition-name` in CSS — each unique per snapshot (verified 1 markup element per anchor class), all mounted across both families so groups form and glide. (2) Added `::view-transition-group(*)` at the locked 350ms / `--ease-morph` register + a `@media (prefers-reduced-motion: reduce)` 1ms-animation guard. (3) Built two visually contrasting watermarked placeholder spines — feature = raspberry-accent **segment bar**, debug = checker-tinted **loop band** with a `↺ iter 2/3` badge (`PLACEHOLDER` watermark on each). (4) Reworked the decision receipt into a 6A-style **pill** (L-badge + label + timestamp) stacked in the `vt-receipt-trail` zone. (5) Reduced-motion path = JS `fade()` (180ms, no slide) + the CSS guard. (6) **Gate run autonomously: VERDICT = PASS (5/5 static analysis; item 4 taste-call PROVISIONAL — no browser connectable)** → View Transitions LOCKED for Phase 3; panel-swap contingency NOT built; `borderline-calls.md` untouched. (7) Handoff tidy: dev op-strip now gated behind a `#/dev` hash suffix (clean on the showable `#/goal/CAST-412`), console clean (only the unknown-op `console.warn` guard remains), library weight <15KB (preact 10.26.2 + htm 3.1.1 only; driver.js mapped-not-imported). `node --check` passes; file:// grep-clean; still one file. **Phase 1 (Keystone) is COMPLETE.** Carry-forward: the morph item-4 taste call needs a human eyeball in Chrome (browser was unavailable this session).
