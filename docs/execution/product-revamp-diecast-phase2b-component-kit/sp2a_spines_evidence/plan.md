# Sub-phase 2b.2a: Shape & Proof — Stage-Spine Variants + the EvidenceBlock Family

> **Pre-requisite:** Read `docs/execution/product-revamp-diecast-phase2b-component-kit/_shared_context.md`
> before starting. It carries the inherited Phase 1 contracts, the 9 exported contracts, the
> binding constraints (NO TESTS, file:// legality, single-file packaging, fixture discipline,
> failure policy), and FULL AUTONOMY mode. This plan does not repeat them.

> **FULL AUTONOMY MODE (owner-approved):** never ask the user questions, never pause for approval
> gates, never go idle waiting for input. At decision gates pick the recommended option and
> document it inline in the sub-phase output. Propagate this exact autonomy directive verbatim
> into any child agent you dispatch.

> **PARALLEL-CAPABLE with 2b.2b.** Both depend only on 2b.1 and touch **disjoint banner sections**
> of `index.html`. This sub-phase owns the **spine + evidence** sections (`spine-*`, `ev-*` class
> prefixes). Do **not** edit 2b.2b's decision/nudge/rail/dial sections. If run as concurrent
> agents, partition by banner comment; if serial, order is irrelevant.

## Objective

Build the two canvas-side components: `StageSpine` (four materially-different shapes from data —
the SC-005 seed) and the `EvidenceBlock` family (E1–E5, one component, per-kind sub-renderers,
**no bare green badge anywhere**). Then swap the Phase 1 placeholder spine markup inside
`GoalCanvas` for `StageSpine` and **re-run the Phase 1 morph gate** to prove 2b didn't break the
keystone.

## Dependencies
- **Requires completed:** 2b.1 (harness, tokens, `Avatar`, `ColleagueCard` line-density — E1's
  checker-compliance rows and E2's attribution reuse the line-density lockup).
- **Assumed codebase state:** `prototype/index.html` has the `#/kit` route, `FIXTURES`, the
  `Avatar` primitive, `ColleagueCard`, the token extensions (incl. `--fail`), and the chosen Guide
  treatment.

## Scope

**In scope:**
- Build `StageSpine({spine})` dispatching on `spine.shape`, four shapes:
  - `segments` (1B): labeled segment bar — accent-filled current, completed ink-tinted, future
    hollow; segment count from data.
  - `loop` (2B): staged band sharing 1B's zone grammar + the `↺ iter 2/3` badge from `spine.iter`
    (the loop glyph is the signature; counter is mono).
  - `timebox`: a single horizontal budget meter (`3h box · 1h 40m used`, from
    `spine.timebox.{budget,used}`) — deliberately **lighter** than a spine, no phase nodes (a
    spike must never look like a mini-feature; playbook 03).
  - `pipeline`: 4-node data-stage chain (`Question → Sources → Analysis → Answer` placeholder),
    nodes hollow/filled by `current`.
  - All four read Phase 1's `spines.<family>` shape (contract #5). `timebox`/`pipeline` fixtures
    live in `FIXTURES` until 2a adds the `spike`/`data` families to `appState`. Labels stay
    `placeholder: true` + watermarked.
- Build `EvidenceBlock({kind, data})` — one component, one switch, five per-kind sub-renderers
  (contract #4):
  - **E1 Acceptance Panel** (5B): stat tiles (`47 passed / 0 failed`, coverage delta) + screenshot
    strip (2–3 hand-drawn CSS/SVG placeholder thumbnails — `file://` forbids external fetches) +
    checker-compliance rows (`M04 ✓ resolved · S03 ✓ resolved · R02 ⚠ flagged`, reusing the
    line-density lockup for attribution) + `PR #2341` pointer (link on canvas; diff behind the
    execution drill-in, per the locked Q#17 call).
  - **E2 Confirm/Refute Ledger:** per-hypothesis rows `prediction → observation → verdict`;
    confirmed = `--ok` mark, refuted = struck + `--fail` mark, **refuted rows stay visible**.
  - **E3 Red→Green Repro:** two stacked test-run excerpts, **same test name**, `--fail` red header
    then `--ok` green header; mono excerpt body.
  - **E4 Verdict Card:** one-line answer + `H/M/L` confidence glyph (`●/◐/○`) + 2–3 deciding data
    points + first-class `spike_ref` link row.
  - **E5 Rendered Report + Provenance:** headline inline-SVG chart (hand-rolled, M9 idiom — **no
    chart library**) or table + a `show provenance` disclosure (sources, query) + dated version
    chip (`Report v2 · re-run on fresh data`).
- Add spine + evidence fixtures and gallery sections to `#/kit` (captions = fixture keys).
- **Swap the goal-canvas spine zone:** replace the Phase 1 placeholder spine markup inside
  `GoalCanvas` with `StageSpine` (data unchanged) — keep the **zone wrapper + any anchor placement
  identical** (only inner content changes).

**Out of scope (do NOT do these — HOLD SCOPE):**
- `Decision` ladder, `NudgeCard`, `EscalationRail`, `AutonomyDial` — **2b.2b** (do not touch its
  banner sections).
- Composing the full signature screen / running the slop gate — **2b.3.**
- Real per-family stage vocabulary (Phase 2c — placeholders + watermark only here), real evidence
  content / real screenshots (Phase 3/6), real org data (Phase 2a).
- Any test file / harness / CI (C1). Any `fetch()` / local ES-module import or external image fetch
  (C2 — E1 thumbnails are hand-drawn CSS/SVG).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `prototype/index.html` | Modify (additive — `spine-*` / `ev-*` sections only) | Has 2b.1's Avatar/ColleagueCard/tokens/`#/kit` |

## Detailed Steps

### Step 2b.2a.1: Build `StageSpine`
- Implement the four-way `spine.shape` switch (segments / loop / timebox / pipeline) per the Scope
  shapes above. The four must be **materially different silhouettes** (bar / loop band / single
  meter / node chain), not four colorings of one stepper.
- Each carries the `PLACEHOLDER` watermark (Phase 1 convention) while `placeholder: true`.
- `spine-*` class prefix throughout. Pure-function rule: reads `{spine}` prop only.

### Step 2b.2a.2: Build `EvidenceBlock` (one component, five sub-renderers)
- One `EvidenceBlock({kind, data})` with a `kind` switch and five sub-renderers (E1–E5) per
  contract #4 + the Scope detail. The family must **share one visual vocabulary** (shared padding
  rhythm, shared header treatment, mono for machine values) while the proof forms differ.
- **Every block carries a confidence or flag signal — no bare green badge anywhere** (outcome first,
  proof one click in, trace two clicks in; never a bare green badge).
- **Error path:** an unknown `kind` renders a visible `unknown evidence kind` placeholder
  (`console.warn`, **no throw**) — same zero-silent-failure posture as the Phase 1 dispatcher.
- `ev-*` class prefix throughout. Hand-rolled inline SVG for E5 (no chart library — keeps the
  <15KB budget honest).

### Step 2b.2a.3: Add gallery sections to `#/kit`
- Add a `StageSpine` section showing all four shapes side-by-side, and an `EvidenceBlock` section
  showing E1–E5 from fixtures. Captions = fixture keys. Contract #9: no `vt-` anchors on these.

### Step 2b.2a.4: Swap the goal-canvas spine zone + re-run the Phase 1 morph gate
- Replace the Phase 1 placeholder spine markup inside `GoalCanvas` with `StageSpine` (the
  `appState.spines.<family>` data is unchanged). **Keep the spine zone's wrapper element and any
  `view-transition-name` placement identical** — only the inner content changes (contract #9; the
  anchor lives on the wrapper, never on `StageSpine`).
- **Re-run the Phase 1 morph gate checklist** (the regression check that 2b didn't break the
  keystone): anchors glide, ~350ms, reduced-motion fade intact, feature↔debug morph still passes.

## Verification

### Automated Tests (permanent)
- **None.** Constraint C1 forbids tests. Do not create any test file.

### Validation Scripts (temporary)
- None that run code. Static checks: `node --check` of the inline module; grep for raw hex outside
  `:root`; grep confirming `spine-*` / `ev-*` prefixes; confirm no external image `src` /
  `fetch(` / local import added.

### Manual Checks (the only verification — open from disk in Chrome and observe)
1. **Four spine silhouettes (squint test):** `#/kit` shows the four spine renders side-by-side —
   **four obviously different silhouettes** (bar / loop band / single meter / node chain), not four
   colorings of one stepper. Each carries the `PLACEHOLDER` watermark.
2. **Morph regression (the keystone check):** `#/goal/CAST-412` now renders its spine zone through
   `StageSpine` (Phase 1 stub markup gone) **and the Phase 1 hero morph still passes its gate
   checklist** — anchors glide, ~350ms, reduced-motion fade intact. (This is the explicit "2b
   didn't break Phase 1" check.)
3. **All five EvidenceBlocks** render from fixtures; per-block checklist: outcome visible first ·
   proof elements present (screenshots / ledger / red→green / verdict / chart) · confidence or flag
   signal present · **zero bare pass-fail badges**. E2 shows refuted hypotheses still visible
   (struck, not removed); E3 shows the same test name red then green; E4's `spike_ref` renders as a
   navigable-looking link both directions (stub href); E5's chart is inline SVG from fixture data.
4. **Unknown-kind error path:** an `EvidenceBlock` with an unknown `kind` renders a visible
   placeholder + `console.warn`, no throw.
5. **Disk-open, console clean,** no new network dependencies beyond Phase 1's CDN set (E5 uses no
   chart library; E1 thumbnails are hand-drawn).

### Success Criteria (binary — every item must pass)
- [ ] `StageSpine` renders all four shapes from data as materially different silhouettes; placeholders watermarked; `spine-*` prefixed; pure function of `{spine}`.
- [ ] `EvidenceBlock` is **one** component with a five-way `kind` switch (E1–E5); every block carries a confidence/flag signal; no bare green badge; `ev-*` prefixed.
- [ ] E2 keeps refuted rows visible (struck); E3 reuses the same test name red→green; E4 has the `H/M/L` glyph + first-class `spike_ref`; E5 chart is hand-rolled inline SVG (no library).
- [ ] Unknown `kind` → visible placeholder + `console.warn`, no throw.
- [ ] `GoalCanvas` spine zone now renders through `StageSpine`; **the Phase 1 morph gate re-passes** (zone wrapper + anchor placement unchanged).
- [ ] Disk-open clean console; no new network deps; no `fetch(` / local import / external image added.
- [ ] No edits to 2b.2b's decision/nudge/rail/dial sections (parallel-safety).

## Execution Notes
- **Morph-regression risk is the headline risk:** replacing stub spine markup changes the DOM
  inside the transition. Keep the spine zone's wrapper element (and its anchor placement) byte-for-
  byte identical; only inner content changes. The verification explicitly re-runs the Phase 1 gate
  — treat a morph regression as a hard fail, not a cosmetic note.
- **E1–E5 are revisit-on-sight defaults:** if a treatment looks wrong once rendered, refine it and
  record the refinement; do **not** silently diverge from the catalog's named structure (the names
  are load-bearing for Phase 3).
- **No browser available?** If Chrome can't be connected this session (per the prototype's known
  constraint), run the static checks, do the morph-gate as a static structural re-check (anchor
  uniqueness, wrapper identity, 350ms register intact), mark the live taste/squint items
  PROVISIONAL, and flag them for a human eyeball in the output — same posture Phase 1 used. Do not
  block.
- **Parallel safety:** this sub-phase touches only `spine-*` / `ev-*` sections + the `GoalCanvas`
  spine zone. 2b.2b touches the nudge zone + decision/rail/dial sections. If a merge conflict
  arises on `GoalCanvas`, the nudge zone is 2b.2b's and the spine zone is yours — partition cleanly.
- **Failure policy (C5 — 2b.2a is NOT critical):** retry once with refined steps; a **second**
  failure → **log the gap and continue** (off critical path). Record the exact failure + what
  remains in the output and manifest Notes.
- **Spec-linked files:** none (greenfield prototype, FR-020).
