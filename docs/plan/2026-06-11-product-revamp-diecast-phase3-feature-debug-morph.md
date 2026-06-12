# Product Revamp: Diecast — Phase 3: Feature + Debug Flows & the Real Hero Morph

## Overview

This phase makes the product thesis real: the two most-contrasting workflow families become
clickable end-to-end from the frozen org spine, and the **real** "this is actually a bug, not a
feature" chat morph lands between them. The feature family (`CAST-412 — Add RBAC to checkout`)
runs its Phase-2c-derived stage backbone rendered per the familiar-tool principle — stage
navigator → stage-owned artifacts as familiar surfaces → execution drill-in → E1 acceptance
evidence. The debug family (`CAST-431 — Checkout 500s on coupon apply`) runs its derived loop
shape with an iteration counter, the E2 confirm/refute ledger in the work zone, and the E3
red→green repro. The Phase 1 placeholder morph is replaced by the real feature→debug morph with
its decision receipt (atom `DEC-CAST-412-03`), proving **SC-003 for real** and making **SC-005's
feature-vs-debug contrast obvious at a glance**.

The exploration's build-cost insight governs everything here: the two canvases are **one canvas
grammar with two deviated zones** (spine + evidence), not two bespoke layouts — the shared zones
(header, work-stream frame, drill-in, decision chips, chat rail) are what make the morph cheap
and the product read as one product. Almost every pixel composes from the Phase 2b kit; this
phase's net-new work is the stage-navigator behavior, the execution drill-in (ported from the
`run_node.html` idiom), the two flow scripts, and the morph itself.

## Position in Overall Plan

```
Phase 1 (planned) ──► 2a ∥ 2b ∥ 2c (planned) ──► ►Phase 3 (THIS PLAN)◄ ──► 4 ∥ 5 ──► Phase 6
  render arch +        data  kit  spines           feature + debug +          remaining   polish
  morph SPIKE                                      REAL hero morph            surfaces
                                                   SC-003 · SC-005
```

Phase 3 sits on the **critical path** (1 → 2b → 3 → 5 → 6) and depends on all three Phase 2
streams: 2a's frozen `org.js`, 2b's component kit + aesthetic lock, and 2c's derived stage
vocabulary (consumed strictly as data through the `stageModels` contract). Phase 4 inherits the
canvas grammar, evidence conventions, and scripted-flow pattern established here; Phase 5
inherits the drill-in's maker-checker presentation and reads the same decision atoms.

## Operating Mode

**HOLD SCOPE** — the delegation instruction is explicit ("plan exactly what the high-level plan
section says for this phase, at high practical detail"). The high-level plan bounds Phase 3 to
five activities: feature backbone canvas, execution drill-in, E1 wiring, debug-loop canvas, and
the real morph. No spike/data canvases (Phase 4), no board/hiring/Layer-2 surfaces (Phase 5), no
walkthrough overlays or asset inlining (Phase 6). Rigor goes into morph correctness on real DOM,
data-contract discipline (stage vocabulary from `stageModels`, never hardcoded), the WHAT/HOW
boundary, and the continuous slop gate. Per the owner's **NO TESTS** rule there are no test
files, suites, or CI anywhere in this plan — all verification is manual: open
`prototype/index.html` from disk, click, observe. (The E1 panel's fake test summary and E3's
red→green output are rendered prototype *data*, not tests.)

## Depends On (from prior plans)

Adopted unchanged from `product-revamp-diecast-decisions-so-far.md` and the prior phase plans:

**From Phase 1 (keystone):**
- Packaging: ONE file `prototype/index.html`, inline style + module; `file://` blocks local
  ES-module imports and `fetch()`; classic `<script src>` and https CDN imports only.
- `appState` v1 keys (extend, never rename); the closed op vocabulary
  `morph · nudge · promote · drillInto · pin` via `data-op="op:arg"` through the single
  dispatcher wrapped in `startViewTransition` (or the panel-swap contingency if Phase 1's gate
  took it — only the mechanism inside `dispatch()` differs; this plan is unaffected either way).
- Scenario engine: `{narration, patch, transition?}` steps + `advance()`; index at
  `appState.chat.scriptIndex`.
- vt- anchors (on shell zone wrappers): `vt-goal-header · vt-chat-rail · vt-nudge-card ·
  vt-receipt-trail · vt-nav-rail`; the **evidence-strip anchor name was reserved for this
  phase** — claimed below as `vt-evidence-strip` (contract this phase exports).
- Motion tokens: `--morph-duration: 350ms`, `--ease-morph`, `--motion-fast: 120ms`,
  reduced-motion fade 180ms; uniqueness rule (a duplicate `view-transition-name` silently kills
  the whole transition).

**From Phase 2a (data spine):**
- `window.ORG` (classic script `prototype/data/org.js`, `Object.freeze`d, generator-authored,
  frozen) — top-level keys `meta · org · humans · guide · agents · stageModels · goals · board ·
  decisions · hiring · layer2`. **Freeze policy: additive extensions only, authored via
  `prototype/data/_build/generate-org.mjs`** (which re-runs the invariant gate); never hand-edit
  `org.js`. This phase uses exactly that sanctioned path (see 3.1).
- Goals consumed: `CAST-412` (feature, `spine_state.current: 'feat-04'`, nudge "Review
  CAST-412's PR", artifacts keyed by step id, work_stream with one `@you` manual item, E1
  evidence payload incl. screenshot refs `assets/e1-*.png` + captions, `PR #2341`) and
  `CAST-431` (debug, `iter: {current: 2, budget: 3}`, investigation-ledger artifacts, E2 + E3
  payloads).
- Decision atoms (playbook-05 schema verbatim + `diff` field): `DEC-CAST-412-03` "Classify
  CAST-412 as bug, not feature" (L2 — the morph receipt), the feature L3 on ticket `CAST-417`
  (roles-column migration, 3 ranked options + evidence pack), the debug L3
  (shared-auth-middleware fix scope), the superseded L1 pair (GraphQL→REST) in the feature goal.
- appState v1.1: `family` ∈ 4 values, `org` key, `spines` derived from
  `stageModels.<f>` + the active goal's `spine_state`, receipts carry `decision_id`.
- Scenario scripts reference spine ids; canonical tokens in narration are interpolated from
  `ORG`, never retyped. Drift grep (recorded in 2a.3's freeze note) re-runs at this phase's end.
- E1 screenshot *image files* are explicitly Phase 3 work (2a owns only refs + captions).

**From Phase 2b (component kit):**
- The 8 components, consumed as-is: `StageSpine {spine}` (shapes `segments|loop`),
  `EvidenceBlock {kind, data}` with the locked E1/E2/E3 data shapes, `ColleagueCard {agent,
  density}` (line density for work streams and tree rows), `Decision {atom, layer}` ladder,
  `NudgeCard {nudge}`, `EscalationRail {escalation}`, `GuideMark` + Guide voice treatment.
- Anchor placement rule: vt- names live on shell zone wrappers, **never on kit components**.
- Token extensions: `--fail`, L-badge mapping (L1 `--ink-35` / L2 `--warn` / L3 `--rasp`),
  confidence glyphs ●/◐/○. The `#/kit` harness for verifying any new component states.
- The aesthetic lock: the upgraded `#/goal/CAST-412` signature screen passed the slop gate;
  Phase 3 builds *on* that screen, and every new screen faces the same continuous gate.
- PR placement (owner taste call, locked): link on canvas inside E1; full diff behind the
  execution drill-in.

**From Phase 2c (stage research):**
- Canonical stage vocabulary lands in `docs/plan/product-revamp-diecast-stage-models.md` and is
  encoded into `ORG.stageModels` via the generator (`placeholder: false`, watermarks dropped).
  **This phase renders vocabulary exclusively from `stageModels.<family>.steps[]`** —
  `{id, label, shortLabel?, does, surface, surfaceWhy, artifacts[], refs[], evidence}` — and
  from each goal's `spine_state`. No stage label, step count, or surface kind is hardcoded
  anywhere in Phase 3 code. Each E1–E5 treatment has exactly one home step (`evidence` field).
- Conditional flag channel: if 2c flagged a spine-shape contradiction, reconcile before 3.1.

## Contracts This Phase Exports (Phases 4/5/6 consume these)

1. **`vt-evidence-strip`** — the sixth view-transition anchor, applied by the evidence zone
   *wrapper* in `GoalCanvas` (per 2b contract #9). The wrapper persists across families and
   glides during the morph; the `EvidenceBlock` content inside it crossfades (E1 ↔ E2/E3).
2. **The stage-navigator interaction:** clicking a spine step sets
   `appState.stageFocus = '<step-id>'` (new appState key, additive) and the stage-artifacts
   zone renders that step's artifacts as its familiar-tool surface
   (`stageModels.<f>.steps[].surface` → a `StageSurface` renderer keyed on surface kind:
   `doc | board | pr-thread | ledger | notebook | memo` — the working set from
   design-decisions). `stageFocus: null` means "current step". Phase 4 reuses `StageSurface`
   for memo/notebook; Phase 5c reuses the `doc` surface for the requirements loop.
3. **The execution drill-in grammar:** `drillInto:execution` renders the HOW panel —
   level 1 = run list, level 2 = one expanded run (dispatch tree + maker-checker iteration
   panel + PR diff). Implemented as `RunNode` (recursive htm port of the
   `cast-server/cast_server/templates/macros/run_node.html` idiom: status dot · agent name ·
   `↻ rework #N` tag · context-usage bar · skill chips · failure/warning rollup tint on the
   thread rail) + `IterationPanel` (maker/checker lockups, finding rows, rework meter, named
   exits). Phase 5a's ticket activity log reuses `IterationPanel`'s row treatment.
4. **ORG additive extension (via the 2a generator, gate re-run):**
   `goals[id].execution = { runs: [{id, agent, status, when, summary, rework_count}],
   focus_run: <recursive node tree>, iteration: {maker, checker, findings: [{code, label,
   status, round}], rework: {used: 1, budget: 3}, exits: ['fix','retry','escalate'],
   pr: {id, label, diff_stub}} }` — full depth on CAST-412 (~4 runs; focus run tree of ~13
   sub-agents), thin on CAST-431 (2 runs, no deep tree). Plus
   `goals['CAST-412'].morph_view = { spine_state: {iter: {current: 1, budget: 3}},
   work_stream: [...2-3 experiment rows...], evidence: {E2-seed: first hypotheses} }` — the
   post-reclassification debug-shape state of CAST-412 (see 3.4). New generator invariants:
   every tree node's agent resolves in `ORG.agents`; `focus_run` rework tags consistent with
   `iteration.rework`; exactly one `focus_run` per goal that has `execution`.
5. **Per-family scenario scripts:** `SCRIPTS = { feature: [...], debug: [...] }`;
   `appState.chat` gains `scriptKey` (additive; set on goal-route entry by family). The engine
   API (`advance()`, step shape) is unchanged. Phase 4 adds `spike`/`data` keys.
   - **PRF2 (owner review feedback, 2026-06-12 — see decisions-so-far.md):** the ChatRail must
     be **per-goal**, not global. Phase 1 left `appState.chat = {messages, scriptIndex}` as one
     shared object across goals; scope it by goal id (e.g. `appState.chat.byGoal[goalId] =
     {messages, scriptIndex, scriptKey}` or equivalent) so switching goals shows that goal's
     thread, not a shared one. Refines (does not rename) the Phase-1 `chat` contract; composes
     with the additive `scriptKey` above. (PRF1 — wire the in-flight stream from
     `goal.work_stream` instead of 2b kit fixtures — is already covered by sub-phase 3.1's
     work-happening stream.)
6. **Asset rule for raster evidence:** generated images live in `prototype/assets/` and load
   via relative `<img src>` (relative image loads work from `file://`; only fetch/module
   imports are blocked). Phase 6 inlines them (base64) into the single distributable file.

---

## Sub-phase 3.1: Feature Backbone — Stage-Navigator Canvas & E1 Evidence

**Outcome:** `#/goal/CAST-412` is the real feature canvas: the 2c-derived segment-bar spine
(no watermark, real vocabulary from `stageModels.feature`) acts as a *navigator* — clicking a
step shows that stage's artifacts rendered as its familiar-tool surface; the work-happening
stream renders live tickets + the `@you` manual item; the E1 acceptance panel (real screenshot
images + test summary + checker rows + PR link) sits at its home step; one L1 decision chip and
the CAST-417 L3 needs-you moment surface at the WHAT level. The first screenful is WHAT-only.

**Dependencies:** Phase 2a executed (org.js frozen) + 2b executed (kit + aesthetic lock) + 2c
executed (stageModels rewritten, `placeholder: false`). If 2c's vocabulary hasn't landed,
**stop and resolve 2c first** — building against watermarked placeholders would violate the
owner's directive.
**Estimated effort:** 1.5 sessions (~4h; the illustration delegation runs in parallel with the
canvas work)

**Verification (manual click-through):**
- Open `prototype/index.html` from disk → `#/goal/CAST-412`: console clean; the spine renders
  2c's real step labels (compare against `docs/plan/product-revamp-diecast-stage-models.md`);
  no `PLACEHOLDER` watermark anywhere on the canvas.
- First screenful contains only WHAT content: goal header, spine, nudge, stage artifacts,
  work stream, evidence, decision chips — zero runs/dispatch/log content (US3 S1 check).
- Click each spine step → the stage-artifacts zone swaps to that step's familiar surface
  (e.g. requirements step → doc surface; execution step → ticket-list surface) with its
  artifacts from `ORG`; clicking the current step (or an explicit "current" affordance)
  returns to the default view. Back/forward and re-render preserve `stageFocus`.
- The E1 panel at its home step shows: 2–3 real screenshot images (alt text + captions from
  the spine), `47 passed / 0 failed` + coverage delta, checker rows
  `M04 ✓ · S03 ✓ · R02 ⚠ flagged`, and the `PR #2341` link (link only — no diff on canvas).
  Images load from disk (`file://`) in Chrome.
- One 6A `Decision` pill (the superseded GraphQL→REST L1) renders on its owning artifact;
  clicking opens the 6B callout; the `DEC-…` id matches the atom.
- The CAST-417 L3 renders as a persistent "⚠ needs you" chip at WHAT level; clicking it opens
  the `EscalationRail` (3 ranked options, nothing pre-selected, evidence pack visible) without
  entering the execution tab (US3 S3 check).
- "Next ▸" walks the feature script start-to-finish: open → Guide nudge → stage navigation
  beat → evidence beat → L3 beat. Narration accumulates in the chat rail; reload resets clean.
- Drift spot-check: every canonical token on screen (CAST-412, M04/S03/R02, 1/3, PR #2341,
  agent slugs) is rendered from `ORG` — temporarily edit a value in the generator, regenerate,
  reload, confirm the screen changes; revert.

Key activities:
- **Extend the spine via the generator (the sanctioned path):** add the `execution` blocks
  (CAST-412 full / CAST-431 thin), `morph_view`, and the new invariants (contract #4) to
  `generate-org.mjs`; regenerate; confirm the gate passes and `git diff` shows only additive
  keys. The ~13-node focus-run tree reuses existing roster slugs (crud-orchestrator +
  crud-compliance-checker prominent; depth ≤3) and one `↻ rework #1` node consistent with
  `rework 1/3`.
- **Build `StageSurface({step, artifacts})`:** one renderer keyed on `step.surface` — `doc`
  (rendered document card: title, version chip, body excerpt), `board` (ticket-list rows),
  `pr-thread` (review-thread rows), `ledger`/`notebook`/`memo` (thin Phase 3 versions; Phase 4
  fleshes out notebook/memo). Full-bleed in the stage-artifacts zone per the familiar-tool
  principle; one-line `surfaceWhy` caption ties the surface to the step. Unknown surface kind
  renders a visible `unknown surface` placeholder with console.warn (zero silent failures).
- **Make `StageSpine` a navigator:** wrap each step in a control carrying
  `data-op="drillInto:stage:<step-id>"`? **No** — keep the op vocabulary closed: step clicks
  set `appState.stageFocus` through a scripted-safe local handler that routes through
  `dispatch('drillInto:<step-id>')` — `drillInto`'s argument grammar already supports targets;
  `'execution'` remains the HOW target, step ids are stage targets. One op, two target
  classes; the dispatcher's `drillInto(arg)` branches on `arg === 'execution'`.
- **Work-happening stream:** rows of line-density `ColleagueCard`s from
  `goal.work_stream` (run-status pills from data); the `@you` manual item renders the
  needs-you accent only when blocking. Stream is family-agnostic chrome (the same frame the
  debug canvas fills with experiments).
- **Wire E1:** `EvidenceBlock {kind:'E1', data: goal.evidence}` placed at its home step
  (the step whose `evidence === 'E1'`), also summarized in the default (current-step) view's
  evidence strip. Replace 2b's CSS/SVG placeholder thumbnails with real images:
  → **Delegate: `/cast-preso-illustration-creator`** — brief: 2–3 fake product screenshots for
  the E1 strip (checkout UI before/after RBAC, matching the spine's `assets/e1-*.png` refs,
  alt text + captions supplied from `ORG`), Diecast light-world style tokens, no
  glass/gradient/glow. Output to `prototype/assets/`.
  → **Delegate: `/cast-preso-illustration-checker`** on the results; rework on fail. Review
  output for style-bible consistency with the locked identity before accepting.
- **Decision chips + L3 at WHAT:** render 6A pills for the goal's in-context atoms on their
  owning artifacts; the L3 atom renders the needs-you chip in the header band; chip opens
  `EscalationRail` (rail options stay inert except where the script wires one — see 3.4).
- **Author the feature flow script** (`SCRIPTS.feature`, ~7 steps): open goal → Guide nudge
  (why-line) → click-through beat on the spine navigator → promote/pin beat (reuse Phase 1's
  promote against a real artifact) → evidence beat (E1) → the L3 needs-you beat → close.
  Narration interpolates canonical tokens from `ORG`.

**Design review:**
- **Spec consistency (stage vocabulary):** zero hardcoded stage labels/counts/surfaces — all
  reads from `stageModels` + `spine_state`. A grep for any 2c label string in `index.html`
  must return nothing (labels appear only via data).
- **Architecture (op closure):** the navigator reuses `drillInto` rather than adding a sixth
  op — the closed vocabulary is a Phase 1 contract. Flagged: the dispatcher's `drillInto`
  gains a branch; document it next to the OPS table.
- **Error path:** missing `assets/` images (file moved, creator output rejected) must render
  the 2b CSS/SVG placeholder thumbnail as a visible fallback (`onerror` swap), not a broken
  image icon mid-demo.
- **file:// assumption made explicit:** relative `<img>` loads are allowed from `file://`
  (unlike fetch/modules) — verify in Chrome as the *first* E1 activity; if a quirk surfaces,
  fall back to 2b's CSS/SVG thumbnails and record in borderline-calls.md.
- **Naming:** `StageSurface` / `RunNode` / `IterationPanel` PascalCase; new CSS prefixes
  `surf-*` (stage surfaces), `exec-*` (drill-in) — keeps the inline stylesheet greppable.

## Sub-phase 3.2: Execution Drill-In — Runs, Dispatch Tree, Maker-Checker Loop

**Outcome:** From the feature canvas, one click (`drillInto:execution`) opens the HOW panel:
a run list; expanding the focus run reveals its ~13-node dispatch tree (run_node idiom: status
dots, rework tags, context bars, skill chips, failure rollup) and the maker-checker iteration
panel (paired lockups, M04/S03/R02 finding rows, rework meter 1/3, named exits fix/retry/
escalate, PR diff stub). The span tree exists **nowhere else** in the prototype.

**Dependencies:** Sub-phase 3.1 (execution data in ORG; canvas shell). **Parallel-capable with
3.3** (disjoint zones: 3.2 builds the exec tab, 3.3 builds the debug canvas; both extend
`index.html` in separate banner sections).
**Estimated effort:** 1 session (~3h)

**Verification (manual click-through):**
- From `#/goal/CAST-412`, click the Execution tab → run list renders (~4 runs from
  `goal.execution.runs`); WHAT content above remains untouched; browser back / re-clicking the
  tab toggles `appState.drill` cleanly.
- Expand the focus run → the dispatch tree renders ~13 nodes with: per-node status dot, agent
  name (mono), one `↻ rework #1` tag, context-usage bars, skill chips, and a failure/warning
  tint rolled up the thread rail — squint-comparable to the `/runs` page idiom.
- The iteration panel shows maker + checker as line-density lockups, the three finding rows
  with their per-round status, the 3-segment rework meter at 1/3, and the three named exits
  as visually-complete buttons. Exits are inert (no console errors on click) except any
  script-wired one.
- The PR diff stub renders here, and only here — the canvas carries the link (3.1), the tab
  carries the diff (locked Q#17 call).
- Disclosure depth audit: run list (level 1) → expanded run (level 2) — nothing requires a
  third click to understand (NN/g cap inherited from playbook 02).
- Count check: exactly one element in the DOM ever renders the span tree; `#/goal/CAST-431`'s
  exec tab shows its thin run list with no deep tree.

Key activities:
- **Port the `run_node.html` idiom to `RunNode({node, depth})`** — a recursive pure htm
  component. Lift the *visual logic* (rail-threaded recursion, `has-failure`/`has-warning`
  rollup classes, `↻ rework #N`, ctx-tint classes, status dots, skill chips), not the Jinja
  markup; colors map to the prototype tokens (`--fail` for failure tint, `--warn` for rework,
  maker/checker hues on agent chrome only).
- **Build the exec tab shell:** `drill === 'execution'` renders the panel below the canvas
  zones (shared chrome across families — the debug canvas gets it for free); run list rows
  (status dot · agent · when · one-line summary · rework count); expanding a row swaps in the
  focus-run detail (tree + iteration panel). Only the focus run carries a tree (HOLD SCOPE).
- **Build `IterationPanel`:** maker/checker `ColleagueCard` line-density pair (bracket-tie
  pairing device), finding rows (`code · label · round · status` — resolved ✓ / flagged ⚠),
  rework meter from `iteration.rework`, named-exit buttons (`fix / retry / escalate`) with the
  escalate exit visually tied to the L3 chip's rail (same raspberry needs-you semantics).
- **PR diff stub:** a small mono two-file diff excerpt (data from `iteration.pr.diff_stub`),
  framed as a PR-thread surface — consistent with the `pr-thread` `StageSurface` kind.
- **Wire the feature script's drill beat:** one scripted step opens the exec tab and expands
  the focus run (`drillInto:execution` + patch), so the demo never depends on a human finding
  the tab.

**Design review:**
- **Trace-creep guard (the playbook's #1 pitfall):** the tree renders only inside the exec
  panel component; no summary mini-tree on the WHAT surface. Review check: search for
  `RunNode` call sites — exactly one.
- **Architecture:** `RunNode` and `IterationPanel` are pure `(props) → vdom` kit-style
  components (no appState reads) so Phase 5a can reuse `IterationPanel` on the ticket view.
- **Error path:** a tree node whose agent slug is missing from `ORG.agents` can't happen
  (generator invariant), but `RunNode` still guards: unknown slug renders the slug raw with a
  visible `?` avatar rather than throwing mid-demo.
- **Performance sanity:** ~13 nodes re-render inside `startViewTransition` snapshots during
  morphs — keep the exec panel *closed* during the morph script step (it's a different beat),
  so tree DOM never participates in the transition.

## Sub-phase 3.3: Debug-Loop Canvas — Investigation Surface, E2 Ledger & E3 Red→Green

**Outcome:** `#/goal/CAST-431` is the real debug canvas and is *obviously a different shape*
from the feature canvas at a glance: the 2c-derived loop band with the `↺ iter 2/3` badge, an
investigation work zone where iteration history is first-class (refuted hypotheses struck but
visible), the E2 confirm/refute ledger as the work-zone hero, the E3 red→green repro at its
home step, the debug nudge, the debug L3 moment, and a scripted debug clickthrough end-to-end.

**Dependencies:** Sub-phase 3.1 (canvas grammar, `StageSurface`, script plumbing).
**Parallel-capable with 3.2.**
**Estimated effort:** 1 session (~3h)

**Verification (manual click-through):**
- `#/goal/CAST-431` from disk: loop-band spine with `↺ iter 2/3` (from
  `stageModels.debug` + `spine_state.iter`), real 2c vocabulary, no watermark; the header
  reads the symptom-as-question ("Checkout 500s on coupon apply").
- **The SC-005 glance test:** screenshot `#/goal/CAST-412` and `#/goal/CAST-431` side by side
  → a viewer names which is which in <3 seconds citing the spine shape (segment bar vs loop
  band + counter). Keep the screenshots as evidence.
- E2 ledger in the work zone: per-hypothesis `prediction → observation → verdict` rows;
  H1/H2 refuted rows struck with `--fail` marks **and still visible**; H3 confirmed with
  `--ok`. Iteration history shows pass 1 collapsed (not deleted), pass 2 live.
- E3 at its home step: same test name red then green, mono excerpts, `--fail` / `--ok`
  headers — never a bare green badge.
- The debug nudge renders from CAST-431's nudge object; the debug L3
  (shared-auth-middleware fix scope) surfaces as the needs-you chip at WHAT with its rail;
  exactly one L3 in the flow; one L1 chip on an investigation artifact.
- "Next ▸" walks the debug script start-to-finish: open → nudge → experiment beat →
  refute/confirm beat → E3 beat → L3 beat. The exec tab opens to the thin run list.
- The story weave reads: the root-cause narration ties to the v4.2 RBAC migration (from
  `ORG`, not retyped) — the org reads as one company.

Key activities:
- Compose the debug canvas from the shared grammar: same header band, work-stream frame,
  chips, exec tab, chat rail — **only spine + evidence/work content deviate** (this is what
  the morph and SC-002 coherence depend on; deviation beyond those two zones is a defect).
- Work zone = the investigation ledger: iteration-history rows (one per pass; older passes
  collapsed by default, expandable, never removed — FR-007), each pass containing its
  experiment rows (line-density `ColleagueCard` attribution where an agent ran the
  experiment) and the E2 `EvidenceBlock` as the live pass's hero.
- Place E3 via the `stageModels.debug` `evidence` home step; the default view's evidence
  strip summarizes the latest verdict state.
- Debug decision chips: the L3 atom chip + rail; one L1 pill (e.g. the instrumentation-scope
  call from the goal's atom set — whichever L1 atom 2a authored for CAST-431).
- **Author the debug flow script** (`SCRIPTS.debug`, ~6 steps), keyed on route entry; the
  thin exec-tab beat included so the shared grammar is visibly shared.
- Nav rail: surface CAST-431 in the goal list with its family tag (the chooser stub `#/`
  gains nothing — entry-screen routing is Phase 6).

**Design review:**
- **Shape-contrast honesty:** the loop band must share the 1B zone grammar (2b's locked 2B
  pick) while reading as a loop — the ↺ badge + counter is the signature; do not invent a
  third spine treatment (HOLD SCOPE; 2c's flag channel was the place to contest shapes).
- **Spec consistency (E2/E3 shapes):** data must match 2b's locked `EvidenceBlock` shapes
  verbatim — `hypotheses[].verdict ∈ confirmed|refuted|open`, `before/after.status` — any
  mismatch is a 2a data bug to fix in the generator, not a component fork.
- **Iteration-visibility rule:** refuted hypotheses and prior passes stay visible (collapse,
  never delete) — FR-007 is load-bearing for the family's whole thesis.
- **Error path:** `iter.current > iter.budget` (data error) renders the counter in `--fail`
  with a console.warn rather than clamping silently.

## Sub-phase 3.4: The Real Hero Morph & Flow Stitch (SC-003)

**Outcome:** The Phase 1 placeholder morph is replaced: on the real feature canvas, the
scripted chat line *"this is actually a bug, not a feature"* morphs `#/goal/CAST-412` into the
debug-family shape in ~350ms with ≥4 anchors gliding (goal header, chat rail, nudge card,
receipt trail, nav rail, evidence strip), drops the receipt derived from atom
`DEC-CAST-412-03`, is undoable via the scripted reverse, and degrades to the 180ms fade under
reduced motion. Both flows + the morph pass the slop gate; the drift grep is clean; Phase 3's
decisions are appended to decisions-so-far.

**Dependencies:** Sub-phases 3.2 + 3.3 (the morph swaps between the *real* canvases).
**Estimated effort:** 1 session (~3h), including gate evaluation and slop-gate reruns

**Verification (this is the phase's headline verification — manual click-through):**
- From disk, advance the feature script to the morph step: the canvas reshapes feature→debug
  — segment bar out, loop band + `↺ iter 1/3` in; E1 strip content crossfades to the seeded
  E2 view; goal header (`CAST-412 · Add RBAC to checkout`), chat rail, nudge card, receipt
  trail, nav rail, and the evidence-strip *wrapper* persist and glide (DevTools → Animations:
  ~350ms total; ≥4 named groups animating).
- The receipt pill appears in the trail during/immediately after the morph and renders
  level/label/time from `DEC-CAST-412-03` (`decision_id` populated); clicking it opens the
  6B callout with rationale + revisit_if from the atom.
- The next scripted step reverses the morph (`morph:feature`) with no state loss — the
  feature canvas returns exactly as it was (stageFocus, pinned items, chat history intact).
- DevTools → Rendering → emulate `prefers-reduced-motion: reduce` → the same step is a
  ≤200ms fade, no sliding motion.
- **Phase 1 gate checklist re-run on real DOM** (all five items): anchors glide rather than
  crossfade · no flash/flicker/layout jump · runs from `file://` in Chrome · reads as ~350ms
  of revealed layout, not spectacle · reduced-motion works. Record the verdict + one-line
  evidence per item in execution notes.
- The morph never fires unprompted — it is exclusively the consequence of the scripted user
  line (playbook 02 pitfall 3).
- **Slop gate (continuous, per the high-level risk table):** screenshot the four new/changed
  surfaces — feature canvas (post-3.1), debug canvas, exec drill-in open, mid-demo morphed
  state → **Delegate: `/cast-preso-check-visual`** (verdict scoped to `not-generic` /
  `not-ai-aesthetic`; ignore slide-specific findings) and
  **→ Delegate: `/cast-preso-check-tone`** on visible copy (narration lines, nudge text,
  evidence labels — FR-018: no GPT-isms, hyphens not em dashes). Rework and re-run until
  green; do not close the phase on a fail.
- **Drift grep re-run** (2a.3's recorded command) across `prototype/` → every canonical-token
  hit is in `data/org.js` / `data/_build/`; the 2b `#/kit` fixture exception is gone if the
  fixture swap happened, else remains the one sanctioned allowlist entry.
- Append the Phase 3 decision summary (~15 lines) to
  `docs/plan/product-revamp-diecast-decisions-so-far.md`.

Key activities:
- **Claim `vt-evidence-strip`:** add the anchor to the evidence zone wrapper in the canvas
  shell (zone wrapper, never the `EvidenceBlock`); confirm the name appears on exactly one
  element per snapshot (the `#/kit` route must not render a wrapper with this name — kit
  shows bare components; uniqueness rule).
- **Build the morph data path:** `morph:debug` on CAST-412 sets `family = 'debug'`, derives
  the debug spine from `stageModels.debug` + `morph_view.spine_state`, swaps the work zone to
  `morph_view.work_stream` (the just-seeded investigation: symptom row + first hypotheses)
  and the evidence strip to the E2 seed; pushes the receipt derived from
  `ORG.decisions` (`DEC-CAST-412-03`). `morph:feature` restores the feature projection from
  the untouched goal data (state kept, not rebuilt — undo proof). Goal id, title, crumb,
  chat history never change (same goal, new shape).
- **Keep anchors mounted:** the six anchor elements keep component identity across both
  family renders (same wrapper elements, different inner content) — the Phase 1 uniqueness +
  mounted-across-families rule, now on real DOM. The exec tab stays closed during the morph
  step (3.2 note).
- **Stitch the demo flow:** finalize `SCRIPTS.feature` so the morph + reverse sit mid-script
  with the L3 beat after the reverse (the flow ends in the feature world, where CAST-417
  lives); confirm `SCRIPTS.debug` independently walkable; remove any Phase 1 placeholder
  script steps and the placeholder spine data (now fully superseded by spine reads — delete,
  don't shadow).
- Run the slop gate delegations, the gate-checklist re-run, and the drift grep; fix and
  re-run until green; write the decisions-so-far appendix.

**Design review:**
- **Morph-regression risk (the load-bearing one):** real canvases carry far more DOM than the
  Phase 1 placeholders — snapshot cost can turn the morph janky. Mitigations are structural:
  exec panel closed during morph, older debug passes collapsed by default, screenshots are
  small thumbs. If jank persists, reduce crossfading-zone depth (the family content) before
  touching the anchor set; if View Transitions still can't carry it, the Phase 1 panel-swap
  contingency applies mechanism-only (op grammar unchanged).
- **Receipt provenance:** the receipt must be *derived* from the atom (2a.3 already wired
  this) — no morph-local label strings. The undo emits **no second receipt** (Phase 1's
  scripted-reverse semantic: one decision, demonstrated reversibility — a reversal atom is a
  product-design question deferred to the real product, recorded as a decision below).
- **Gate honesty under full autonomy:** checklist criteria pre-written (above) before the
  re-run; slop-gate verdicts come from the external checker agents; screenshots + verdicts
  retained; borderline passes logged to `borderline-calls.md`.
- **Naming:** anchor name `vt-evidence-strip` matches Phase 1's reserved-name note verbatim.

## Build Order

```
Sub-phase 3.1 ──┬──► Sub-phase 3.2 (exec drill-in) ──┬──► Sub-phase 3.4 ──► SC-003 + SC-005 proven
 (feature canvas │                                    │     (real morph,
  + data extension└──► Sub-phase 3.3 (debug canvas) ──┘      flow stitch,
  + E1 evidence)                                              slop gate)
```

**Critical path:** 3.1 → 3.2/3.3 (either) → 3.4. The two middle sub-phases touch disjoint
surfaces and can run as parallel sessions/agents (partition `index.html` by banner section —
the 2b precedent); serially the phase is 4–4.5 sessions, matching the high-level 2–2.5 day
estimate. The `/cast-preso-illustration-creator` delegation in 3.1 runs concurrently with 3.1's
canvas work (its output is consumed by the E1 wiring step at the end of 3.1).

## Design Review Flags

| Sub-phase | Flag | Action |
|-----------|------|--------|
| 3.1 | Stage vocabulary hardcoded anywhere would violate the 2c contract | All labels/surfaces/counts read from `stageModels` + `spine_state`; grep check in verification |
| 3.1 | A sixth op for stage navigation would break the closed vocabulary | Reuse `drillInto` with step-id targets; dispatcher branch documented |
| 3.1 | Relative `<img>` from `file://` assumed to work | Verify first; `onerror` fallback to 2b CSS/SVG thumbnails; record if the fallback is taken |
| 3.1 | ORG mutation outside the generator would break the freeze policy | All data extensions via `generate-org.mjs` + invariant gate re-run (2a's sanctioned path) |
| 3.2 | Span tree creeping onto the WHAT surface (high-level plan risk) | Tree renders only inside the exec panel; single `RunNode` call-site check |
| 3.2 | Tree DOM participating in morph snapshots → jank | Exec panel closed during the morph script step |
| 3.3 | Debug canvas drifting beyond the two deviated zones | Shared-grammar rule restated; deviation beyond spine+evidence/work content = defect |
| 3.3 | E2/E3 data shape mismatch vs 2b's locked contracts | Fix in the generator, never fork the component |
| 3.4 | Duplicate `vt-evidence-strip` (e.g. via `#/kit`) silently kills all transitions | Anchor on the canvas zone wrapper only; uniqueness check in verification |
| 3.4 | Real-DOM morph jank vs the Phase 1 placeholder result | Structural mitigations + Phase 1 panel-swap contingency (mechanism-only swap) |
| 3.4 | Self-judged taste under full autonomy | External slop-gate checkers + pre-written gate checklist; evidence retained; borderline passes → borderline-calls.md |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| 2c vocabulary lands late or with a flagged shape contradiction | High (blocks 3.1) | Hard dependency stated; reconcile 2c's flag before building; the `stageModels` indirection means a vocabulary *edit* costs zero component work |
| The real morph is less convincing than the placeholder spike (heavier DOM) | High | Structural DOM discipline (closed exec tab, collapsed history); gate checklist re-run; costed panel-swap contingency carried from Phase 1 |
| Illustration-creator output fails the slop gate repeatedly | Med | Checker loop budgeted; hard fallback = 2b's CSS/SVG thumbnails (already aesthetic-locked), so E1 never blocks the phase |
| Generator extension breaks 2a invariants (step refs, L3 budget) | Med | The gate refuses to emit — failures are loud and pre-commit; new invariants added alongside the new data |
| `morph_view` reads as a fake second goal rather than CAST-412 reclassified | Med | Header/crumb/chat never change; the seeded investigation references the coupon-apply symptom + RBAC-migration weave from `ORG` so the story stays one world |
| Single-file `index.html` growth hurts navigability (now canvases + drill-in + scripts) | Low–Med | Banner sections + `surf-*`/`exec-*` class prefixes (2b precedent); Phase 6 owns packaging |
| Scripted beats drift canonical tokens into narration strings | Low | 2a rule enforced: narration interpolates from `ORG`; drift grep re-run at 3.4 |

## Open Questions

None blocking — full-autonomy mode resolved all judgment calls (logged below). For
traceability, items deferred *by design* to later phases:

- Real-capture screenshots inlined into the single file (vs the 3.1 generated rasters) →
  Phase 6 packaging call.
- The reversal-atom question (does an undo emit its own decision record?) → real-product
  design question; the prototype demonstrates reversibility without a second receipt
  (Decision #9).
- Entry-screen routing into these flows (`#/` chooser) → Phase 6 (FR-002).

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| `docs/specs/_registry.md` (re-confirmed against the high-level plan's check) | all seven specs govern cast-server runtime | None — FR-020: the prototype is greenfield; no spec applies, none contradicted; no `/cast-update-spec` action (excluded by delegation instruction) |

Note: `run_node.html` is **lifted as a visual idiom** from the cast-server codebase into
greenfield prototype code — it is reference material, not a spec'd surface being modified;
the `/runs` page itself is untouched.

## Decisions Made Autonomously

1. **Sub-phase split 3.1 → (3.2 ∥ 3.3) → 3.4** — the feature canvas + data extension is the
   backbone everything consumes; drill-in and debug canvas touch disjoint surfaces
   (parallelism as schedule buffer); the morph must come last because it swaps between the
   two *real* canvases. Matches the 4–5 session estimate.
2. **Execution-run data added as an ORG additive extension via the 2a generator**
   (`goals[id].execution`, `goals['CAST-412'].morph_view`) — the high-level plan's drill-in
   needs run/tree/iteration data that 2a never enumerated; the freeze policy's sanctioned
   extend-via-generator path (with new invariants) beats scenario-local literals, which would
   reintroduce exactly the drift 2a exists to prevent.
3. **The morph stays on CAST-412** (goal context preserved: header/crumb/chat never change);
   `morph_view` supplies the post-reclassification debug-shape state (iter 1/3, seeded
   hypotheses referencing the coupon-apply symptom). CAST-431 remains the standalone
   end-to-end debug flow. Morphing *to* CAST-431's canvas would violate "preserving goal
   context" (US1 S2) — it would read as navigation, not reshaping.
4. **Stage navigation reuses `drillInto` with step-id targets** rather than adding a sixth
   op — the closed 5-op vocabulary is a Phase 1 exported contract; `drillInto`'s target
   grammar already accommodates it (`'execution'` = HOW, `<step-id>` = stage focus).
5. **`vt-evidence-strip` claimed on the evidence zone wrapper** (name reserved by Phase 1
   decision #6), bringing the anchor set to six; content inside crossfades while the wrapper
   glides — satisfying playbook 02's "evidence strip is a persistent anchor" with the E1↔E2
   swap intact.
6. **E1 screenshots generated as real raster assets** via `/cast-preso-illustration-creator`
   + `/cast-preso-illustration-checker` (the high-level plan's named highest-value use),
   loaded as relative `<img src="assets/e1-*.png">` — relative image loads are `file://`-legal
   (only fetch/module imports are blocked); 2b's CSS/SVG thumbnails demoted to the `onerror` /
   gate-failure fallback. Phase 6 owns base64 inlining.
7. **Per-family scripts as `SCRIPTS = {feature, debug}` with additive `chat.scriptKey`** —
   Phase 1's single-script engine extends without renaming any key; Phase 4 adds its two
   families the same way.
8. **Full drill-in depth only on the feature flow; CAST-431 gets the thin run list** — the
   high-level verification pins the dispatch tree to the feature flow's drill-in; duplicating
   the deep tree for debug adds build cost with no demo payoff (HOLD SCOPE), while the shared
   tab keeps the grammar identical.
9. **The morph undo emits no second receipt** — one decision atom (`DEC-CAST-412-03`), one
   receipt, demonstrated reversibility via the scripted reverse (Phase 1's semantic). Whether
   a reversal is itself a recorded decision is a real-product question, deferred.
10. **Named exits and rail options render complete but inert except script-wired beats** —
    visually honest controls without inventing unscripted interaction states; the L3 rail's
    *choice* moment is Phase 5a's dial/board arc per the high-level plan, so Phase 3 shows
    the stop, not the resolution.
11. **`RunNode`/`IterationPanel` built as pure kit-style components** (props only) so Phase
    5a's ticket activity log reuses `IterationPanel` without rework — one iteration-row
    treatment org-wide.
12. **Slop gate run on four surfaces** (feature canvas, debug canvas, open drill-in, morphed
    state) — the high-level risk table mandates the continuous gate per screen *as built*;
    these are the four new/changed visual states this phase ships.
13. **`cast-plan-review` auto-dispatch skipped** — the run configuration in
    `product-revamp-diecast-decisions-so-far.md` states "Plan review: skipped — cross-phase
    reconciliation only" (owner-approved; consistent with Phase 1 #12, 2a #17, 2b #17).
    Recorded here; rerun manually via `/cast-plan-review` against this file if wanted.

## Suggested Revisions to Prior Sub-Phases

- **Phase 2a (advisory, non-breaking — uses its own extension mechanism):** Phase 3 extends
  the generator with `goals[id].execution` + `goals['CAST-412'].morph_view` and three new
  invariants (tree-agent referential check, rework-tag consistency, one focus run). This is
  the freeze policy's designed additive path, not a value mutation — but 2a's invariant-gate
  section should be understood as *growing* with later phases; if 2a execution wants to
  pre-reserve the `execution`/`morph_view` keys as documented extension points (empty or
  absent until Phase 3), that would make the contract explicit at zero cost.
- **Phase 1 (clarification only):** Phase 1's anchor decision #6 used the nudge card as a
  stand-in for the evidence strip "until Phase 3 builds real evidence." This plan keeps the
  nudge-card anchor *and* adds `vt-evidence-strip` (six anchors total) rather than swapping —
  both elements are conceptually persistent chrome; no Phase 1 change needed.
- **Phase 2b:** none. If 2b's `#/kit` fixture swap to spine data hasn't happened by 3.4's
  drift grep, the fixture block remains the one sanctioned allowlist exception (2a already
  documented this); 3.4 inherits that allowlist rather than re-deciding.
