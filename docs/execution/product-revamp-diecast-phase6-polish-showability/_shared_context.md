# Shared Context: Product Revamp Diecast — Phase 6 (Polish & Showability — terminal)

> Read this file at the start of **every** sub-phase session, then execute that sub-phase's
> `plan.md`. The binding constraints below are not optional — they are reconciled cross-phase
> contracts carried forward from Phases 1–5. Violating one is a defect, not a judgment call.
> Phase 6 is the **last phase on the critical path** (1 → 2b → 3 → 5 → 6); nothing depends on it
> except the post-mockup v2 planning session, which consumes 6.3b's SC-006 map.

## Read FIRST, in this order (the runner MUST read these before touching anything)

1. **The Phase 6 plan (the source of this split):**
   `docs/plan/2026-06-11-product-revamp-diecast-phase6-polish-showability.md`
2. **Decisions / run config / cumulative cross-phase contracts + the Phase 1–5 close records + canon:**
   `docs/plan/product-revamp-diecast-decisions-so-far.md`
   (Run Configuration; Owner-Locked Inputs; NO-TESTS; the Phase 1/2a/2b/2c/3/4/5 decision blocks +
   Execution Records / Decision Summaries — these hold the canonical vocabulary, the drift-grep
   canon, and every prior gate's outcome.)
3. **Borderline-call log (prior gate resolutions; the runner APPENDS new ones here):**
   `docs/plan/product-revamp-diecast-borderline-calls.md`
   (Entry **#11** is the binding single-file serialization precedent for this phase — read it.)
4. **Cross-phase reconciliation (F1–F5; F2 closed-script-set, F3/F4 generator rules):**
   `docs/plan/2026-06-12-product-revamp-diecast-reconciliation.md`
5. **Canonical stage vocabulary (THE single source — never re-derive):**
   `docs/plan/product-revamp-diecast-stage-models.md`

## Project Background

Phase 6 turns a complete-but-raw prototype into a **showable artifact**. Every flow, surface, and
script already exists from Phases 1–5 — **nothing new is *demonstrated* in this phase.** Phase 6
makes the prototype *navigable by a stranger* (the FR-002 scenario chooser + driver.js guided
walkthroughs + a presenter demo-script overlay), *defensible to a peer* (SC-004 — the every-screen
slop-gate re-run + density/consistency pass), and *portable as one file* (the single distributable
that opens from disk), and it converts the prototype into the **v2 execution roadmap** (the SC-006
surface→buildable-goal map). The key inherited insight: because every screen is a projection of
`ORG` through `render(appState)`, "polish" here is mostly **gating and packaging**, not
re-authoring.

The phase splits into five sub-phases on the DAG **6.1 → 6.2 → {6.3a ∥ 6.3b} → 6.4**, critical path
**6.1 → 6.2 → 6.3a → 6.4**:

- **6.1** Front Door — the FR-002 scenario chooser (`#/` made real, replacing the Phase 1 stub) +
  five driver.js anatomy tours (`TOURS` keyed like `SCRIPTS`) + the presenter demo-script overlay.
- **6.2** The Gate — the cross-surface density/consistency pass + the full **21-capture** slop-gate
  sweep over **every** screen (supersedes the per-phase spot gates).
- **6.3a** Distributable — `prototype/_build/inline.mjs` → `prototype/dist/diecast-prototype.html`
  (single file, base64 E1 rasters, CDN-stays-CDN) + the final cross-surface drift sweep + disk
  smoke test. **Touches `index.html`** (the drift sweep edits it).
- **6.3b** The Map — `docs/plan/product-revamp-diecast-v2-surface-goal-map.md` (SC-006). **Touches
  NO `index.html`** — the one truly parallel-safe sub-phase.
- **6.4** Showability Sign-Off — the SC-002 dry run on the **dist file** + the final SC-001/SC-007
  cross-check, appended as a closing note to `decisions-so-far.md`.

**Operating mode: HOLD SCOPE.** Plan and execute exactly the five Phase 6 activities, no extras. The
one nice-to-have that surfaced during planning — a **standalone written demo-runbook** — is
**EXCLUDED** (the demo-script overlay already serves that job; Phase 6 plan Decision 15).

## FULL AUTONOMY (owner-approved, end-to-end through Phase 6)

Never ask the user questions, never pause for approval gates, never go idle waiting for input.
**There are no user gates and no `gate_*` files in this phase.** At every decision gate pick the
recommended option and document it (in this `_shared_context`'s lineage of decisions, the
sub-phase's progress-log line, and — for any flagged-but-taken taste call — a new numbered entry
**appended** to `docs/plan/product-revamp-diecast-borderline-calls.md`). **Propagate this directive
verbatim to any child agent you dispatch** (the slop-gate visual/tone checkers in 6.2 / 6.4).

## No-browser static-verification posture (project-wide, autonomous runs)

Autonomous runner sessions **cannot connect a live browser** (the Claude-in-Chrome extension is not
connected — same as every prior phase). Therefore every "Verification (manual click-through)" item
is satisfied by the strongest **static** evidence available (`node --check` of the extracted module,
grep audits, pure-logic assertion harnesses in `/tmp` that are **never committed**) **plus** a
recorded **human-eyeball carry-forward** for any item that genuinely needs rendered pixels (glance
tests, popover styling, chart legibility, motion feel, slop-gate-on-screenshot). **Carry-forwards
are non-blocking** — they never stop the phase; they are logged for a later human pass. This posture
is the inherited Phase 1/2a/2b/3/4/5 precedent, not a Phase 6 invention. (Phase 4's 4.3/4.4 reached
a live browser when the extension happened to be connected; treat a live browser as a bonus, never a
precondition. If a browser *is* connected, prefer the rendered-pixel evidence and upgrade the
carry-forwards to confirmed.)

## BINDING CONSTRAINTS (carried into every sub-phase; each is a defect if violated)

1. **NO TESTS anywhere — owner-locked.** No test files, suites, harness, or CI in any sub-phase.
   All verification is **manual click-through / static observation only** — open
   `prototype/index.html` (or the dist file) from disk, click, observe. Fake test-result *content*
   rendered as prototype UI data (E1 acceptance panel, E3 red→green) is **data, not tests**, and
   stays. **No review pass may flag "missing tests" as a finding.** The `inline.mjs` build script
   (6.3a) is packaging tooling (the 2a generator precedent), **not** a test harness — its only check
   is refuse-on-missing-`src`.

2. **`file://` legality — ONE inline dev file + a generated dist.** The dev prototype ships in the
   single `prototype/index.html` (inline `<style>` + inline module). `file://` blocks `fetch()` and
   **local ES-module imports**. Allowed from disk: **https CDN** imports via the import-map (preact /
   htm / driver.js), classic `<script src>` (how `org.js` loads), **relative `<img src>`** (E1
   rasters under `prototype/assets/` with the 2b CSS/SVG `onerror` fallback), and the new **driver.css
   CDN `<link>`**. Collapsible disclosure uses **native `<details>`**. The dist file (6.3a) replaces
   the local `<script src>` and `<img src>` with inline-classic-script + base64 data-URIs — both
   `file://`-legal forms Phase 1 established; **the inliner introduces no `fetch`.** **CDN
   stays CDN** in the dist (libs + fonts); "opens from disk" has meant "one local file + https CDN"
   since Phase 1's file:// analysis. Re-verify file:// legality post-inline (6.3a).

3. **ORG is FROZEN — and Phase 6 authors NO generator batch.** `prototype/data/org.js` is generated
   by the seeded `prototype/data/_build/generate-org.mjs`; **NEVER hand-edit `org.js`.** **Phase 6
   adds NO ORG generator batch** (Phase 6 plan Decision 7): chooser / tour / demo-script copy is
   **presentation chrome inline in `index.html`**, not org data. The one sanctioned data-side touch
   is **completing the `#/kit` fixture→ORG data swap** if execution hasn't already (6.3a, constraint
   #11 below) — and that is done via the generator/render path, never by hand-editing `org.js`. Card
   titles/ids on the chooser render from `ORG.goals` (drift rule: goal titles never retyped).

4. **Closed 5-op vocabulary stays closed** (`morph · nudge · promote · drillInto · pin`). **UI state
   is NOT an op:** the chooser card handlers (set `chat.scriptKey` + reset `chat.scriptIndex` +
   navigate), the demo-script overlay toggle (`s` key / nav-footer control), and driver.js tour
   start/stop are **plain click handlers** (+ the one additive appState key below). **No sixth op
   anywhere in this phase.** Tours **never call `advance()`** — the scenario engine owns the
   narrative; tours teach anatomy.

5. **SCRIPTS keys closed at 5** (`feature, debug, spike, data, hiring` — F2; the four **family** set
   is closed, `hiring` is a demo-arc key). Phase 6 adds **no new SCRIPTS key**. The new **`TOURS`
   map is keyed *identically* to `SCRIPTS`** (`{feature, debug, spike, data, hiring}`) so the five
   chooser scenarios map 1:1 onto the five script keys.

6. **appState additive keys only — exactly ONE new key this phase: `demoScriptOpen: boolean`**
   (the presenter overlay). No other new top-level appState key; no new top-level ORG key. All v1 /
   Phase 3 / Phase 4 / Phase 5 keys are untouched.

7. **vt- anchors live on shell zone wrappers, NEVER on kit components — set is `6×1`** after Phase 3
   (`vt-goal-header · vt-chat-rail · vt-nudge-card · vt-receipt-trail · vt-nav-rail ·
   vt-evidence-strip`). A duplicate `view-transition-name` **silently kills all transitions.** The
   chooser stays a **bare route** (Phase 1 "Home = bare scenario-chooser" precedent — no nav/chat
   shell), so it renders no shell zone wrapper and introduces **no vt- duplication risk.** `data-tour`
   anchors are **attributes, not CSS classes** (so 6.2's density/styling refactors can't silently
   break tours) and carry **no** vt- name.

8. **L3 budget: exactly one hard stop per flow — unchanged.** Phase 6 adds ZERO new L3 atoms. The
   data flow's L3 stays the ONE script-wired rail resolution (Phase 4); CAST-417's rail stays an
   unresolved stop; the dial's L2→stop promotion stays a scripted illusion (ORG unmutated). Tours and
   the demo overlay touch none of this.

9. **CRITICAL — single-file serialization (per borderline-calls #11; Phase 3/4/5 precedent).**
   `prototype/index.html` is **one file**, and HTTP-dispatched `cast-subphase-runner` agents have
   **NO merge mechanism**. Therefore **any sub-phases that touch `index.html` MUST run strictly
   serial.** In this phase **6.1, 6.2, and 6.3a all edit `index.html`** → they are serial on the
   critical path (6.1 → 6.2 → 6.3a → 6.4) regardless of how the DAG is drawn. **6.3b is the
   exception:** it creates ONLY `docs/plan/product-revamp-diecast-v2-surface-goal-map.md` and touches
   **NO `index.html`**, so it **truly parallelizes** with 6.3a (no serialization needed — this is the
   first genuinely-parallel-safe sub-phase since Phase 1, because every prior "parallel" group shared
   the single file). See the file-collision honesty note in `_manifest.md`.

10. **Failure policy:** retry a failed sub-phase **once** with refined instructions. Second failure
    **off** the critical path (only 6.3b is off-path) → log a gap and continue. Second failure **on**
    the critical path (6.1 → 6.2 → 6.3a → 6.4) → **stop and report.**

## Codebase Conventions

- **Single-file dev prototype:** `prototype/index.html` — inline `<style>` + inline
  `<script type=module>`, `render(appState) → DOM` (pure render), htm + preact-style components via
  https CDN import-map. **Banner-comment sections** partition the file (the 2b/3/4/5 precedent) —
  Phase 6 adds new sections for the chooser (6.1), the tours + demo overlay (6.1), and the `tour-*`
  driver.css override block (6.1). Do **not** restructure existing Phase 1–5 sections beyond the
  density/consistency fixes 6.2 sanctions.
- **CSS prefixes (greppable, per-surface):** `choose-*` (chooser) · `tour-*` (driver.js popover token
  overrides) · `demo-*` (demo-script overlay) — following the per-surface prefix convention
  (`board-*`/`hire-*`/`reqs-*` etc. from Phase 5).
- **Component naming:** PascalCase (`StageSpine`, `ColleagueCard`, `GuideMark`, `DigestNotice`,
  `RadarChart`, `Sparkline`, …); Phase 6 net-new presentation components inline in `index.html`.
- **driver.js:** the **module** was pinned in the Phase 1 import map and all usage **deferred to this
  phase**. Phase 6 imports it and adds its **v1 stylesheet via CDN `<link>`** (a gap no prior phase
  covered) **plus a mandatory `tour-*` token-override block** — stock driver.js popovers (white,
  rounded, generic sans) would fail the slop gate on sight.
- **Org-data key convention:** lower_snake_case. (No new ORG keys this phase.)

## Key File Paths

| File | Role |
|------|------|
| `prototype/index.html` | THE single-file dev prototype (5750 lines as of Phase 5 close) — 6.1/6.2/6.3a edit it **serially**; 6.3b never touches it |
| `prototype/data/org.js` | Frozen `window.ORG` (classic script). **Generated — never hand-edit. No Phase 6 batch.** |
| `prototype/data/_build/generate-org.mjs` | The seeded generator + invariant gate. **Not edited in Phase 6** (no batch); only re-run if completing the `#/kit` data swap requires it (6.3a) |
| `prototype/assets/e1-acceptance.png` | The E1 acceptance raster (relative `<img>` + onerror fallback in dev; **base64-inlined** in the dist by 6.3a) |
| `prototype/assets/fr017-parity-three-tiers.png` | The FR-017 parity raster (same packaging treatment as E1 in 6.3a) |
| `prototype/_build/inline.mjs` | **Created by 6.3a** — zero-dep Node one-shot that emits the dist file. Build-time only; never part of the runtime/dev loop |
| `prototype/dist/diecast-prototype.html` | **Created by 6.3a** — the single distributable (generated; header-marked; never hand-edited; regenerate via `inline.mjs`) |
| `docs/plan/product-revamp-diecast-v2-surface-goal-map.md` | **Created by 6.3b** — the SC-006 surface→buildable-goal map; input to the v2 planning session |
| `docs/plan/product-revamp-diecast-decisions-so-far.md` | **Appended by 6.4** — the Phase 6 close note + per-criterion SC verdicts (one paragraph, not a new artifact) |
| `docs/plan/product-revamp-diecast-borderline-calls.md` | **Appended by any sub-phase** that ships a flagged-but-taken taste call (numbered entries continue from #15) |

## Contracts This Phase Exports (final — the project terminal)

- **`prototype/dist/diecast-prototype.html`** — the single distributable file (the SC-004 artifact).
- **`docs/plan/product-revamp-diecast-v2-surface-goal-map.md`** — the SC-006 surface→buildable-goal
  map, input to the post-mockup v2 planning session.
- **`TOURS` map** (`{feature, debug, spike, data, hiring}`) keyed identically to `SCRIPTS`;
  `data-tour="…"` anchor attributes on shell zones + key components.
- **appState additive key** `demoScriptOpen: boolean`.
- **CSS prefixes** `choose-*` · `tour-*` · `demo-*`.
- The full **21-capture slop-gate surface list** + the **consolidated drift-grep canon** (Phase
  3+4+5 sets unified), and the **`#/kit` exception RETIRED** (zero sanctioned grep exceptions at
  project end).

## Carry-Forward Constraints Inherited from Phase 5 (still binding in Phase 6)

- **`file://` legality** — one inline dev file; no `fetch`, no local ES-module imports; only https
  CDN imports + classic `<script src>` + relative `<img>`; native `<details>` for disclosure.
- **ORG frozen via the generator** — additive keys only; never hand-edit `org.js`. (Phase 6 adds no
  batch.)
- **Closed 5-op vocabulary** — UI state = plain handlers + additive appState; no sixth op.
- **vt- anchors `6×1`, shell-zone-wrappers only** — no duplicate `view-transition-name`.
- **L3 budget** — exactly one hard stop per flow; the data L3 is the one wired rail resolution.
- **Canonical vocabulary single-sourced from `org.js`** (drift rule): CAST-412 "Add RBAC to
  checkout" · CAST-431 · CAST-452 · CAST-461 · CAST-417 (THE feature L3) · M04/S03/R02 · rework 1/3 ·
  99.9%·505 runs·2 loops (crud-orchestrator) · 99.4%·312 runs (dial aggregate) · GraphQL→REST
  superseded pair · 6 candidates · 5 dimensions · 12 contracts · 8-agent chain · 6-project portfolio ·
  PM persona (Priya Kannan) · `cast-export-csv`. Every canonical literal in `index.html` must come
  from `ORG` rendering, not retyped strings.

## Phase 6 Additions (new this phase — the binding deltas)

- **driver.css** via CDN `<link>` + the mandatory **`tour-*` token-override block** (paper bg, ink
  text, mono titles, raspberry progress/active accents, `--radius-sm/md`, no shadows beyond the
  existing elevation idiom). Stock styling fails the gate — the override is mandatory, and a
  tour-popover-open capture is item #2 in the 6.2 gate list.
- **`data-tour` attributes** on shell-zone wrappers + key components (attributes, not classes).
- **`appState.demoScriptOpen`** additive boolean (presenter overlay; `s`-key + nav-footer toggle;
  guard the `s` handler on `event.target` so it never fires inside the parity fake-terminal pane).
- **`TOURS` keyed to `SCRIPTS`** — five tours, 5–8 stops each, anatomy-not-story, last stop points at
  the chat advance control; `animate:false` under `prefers-reduced-motion`.
- **`prototype/_build/inline.mjs`** — the zero-dep single-file build (6.3a), 2a-generator precedent.
- **base64 E1 (and FR-017 parity) rasters** in the dist; **CDN stays CDN**; ≤~5MB guard with WebP
  recompression fallback.
- **`#/kit` exception RETIRED** in the final drift sweep (6.3a); `#/kit` ships hidden inside the dist
  (hash-only, harmless) rather than being stripped.
- **CF3 de-em-dash unified copy pass folds into Phase 6** — the standing carry-forward (em-dashes in
  prior-phase narration + the 3 Phase-4 data strings + Phase-5 microcopy) is resolved by the 6.2
  tone pass over the new copy **plus** acknowledging the unified pass; new Phase 6 copy (chooser
  blurbs, tour text, demo talking points) is authored em-dash-free per FR-018 from the start.

## Pre-Existing Decisions (from the Phase 6 plan's Decisions Made Autonomously + Run Config)

- **Plan review: SKIPPED** per the owner-approved run config (cross-phase reconciliation only;
  Phase 1/2a/2b/2c/3/4/5 precedent). This split does **not** dispatch `/cast-plan-review`, inserts
  **no** review or reconciliation sub-phases, and writes **no** `_review_summary.md`. A manual
  `/cast-plan-review` is recorded in the run's next_steps instead (Phase 6 plan Decision 16).
- **No human-checkpoint gates** in any sub-phase file (FULL AUTONOMY). No decision gates in this
  phase.
- Sub-phase split `6.1 → 6.2 → {6.3a ∥ 6.3b} → 6.4` (Decision 1); walkthrough = **BOTH** driver.js
  tours + demo-script overlay (Decision 2); tours keyed to `SCRIPTS`, teach anatomy, never
  `advance()` (Decision 3); tour anchors = `data-tour` attributes (Decision 4); driver.css via CDN
  `<link>` + mandatory token restyle (Decision 5); demo overlay = `appState.demoScriptOpen` + plain
  handler + `s` key (Decision 6); chooser stays a bare route, **no ORG batch** (Decision 7);
  single-file = zero-dep Node `inline.mjs` → dist (Decision 8); E1 rasters base64-inlined in the dist
  (Decision 9); CDN libs/fonts stay CDN, offline fallback documented-not-built (Decision 10); `#/kit`
  exception retired, ships hidden (Decision 11); gate fixed at 21 captures, hiring gated on the
  report-card step only (Decision 12); honest effort ~2.75–3.25 sessions vs the 2-session envelope,
  extend-don't-cut (Decision 13); SC-002 fresh-viewer test = the single human action item (Decision
  14); no standalone demo-runbook (Decision 15); plan review skipped (Decision 16).

## Relevant Specs

`docs/specs/_registry.md` — all existing specs govern the **cast-server runtime**. Per **FR-020 the
prototype is greenfield**: no spec applies, none is contradicted, and **no `/cast-update-spec`
action** is in scope for this phase. (Forward note, unchanged from the high-level plan: when 6.3b's
v2 goals are planned, *those* plans author product specs — downstream of this one.) **No specs cover
files in this plan.**

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|-----------|------|-----------|--------|-------------------|
| 6.1 Front Door — Chooser & Walkthroughs (`sp6_1_chooser_walkthroughs`) | Sub-phase | Phases 1–5 done (all routes + all 5 SCRIPTS) | 6.2 | None (root; edits `index.html`) |
| 6.2 The Gate — Density + Full Slop Sweep (`sp6_2_density_slop_gate`) | Sub-phase | **6.1** (the new surfaces must exist to be gated) | 6.3a, 6.3b | None (edits `index.html`) |
| 6.3a Distributable — Inline + Drift + Smoke (`sp6_3a_inline_drift`) | Sub-phase | **6.2** (inline after content is final) | 6.4 | **6.3b** (6.3b touches no `index.html`) |
| 6.3b The Map — SC-006 Surface→Goal (`sp6_3b_surface_goal_map`) | Sub-phase | **6.2** (surfaces final) | 6.4 | **6.3a** (truly parallel — doc-only, no `index.html`) |
| 6.4 Showability Sign-Off (`sp6_4_showability_signoff`) | Sub-phase | **6.3a + 6.3b** | — | None (terminal) |

> **Critical path: 6.1 → 6.2 → 6.3a → 6.4.** 6.3b is **off** the critical path; it can also absorb
> idle time during 6.2's checker runs.
>
> **File-collision honesty note (the Phase 6 refinement of the Phase 3/4/5 serial override):** the
> DAG models 6.3a ∥ 6.3b as a parallel group. Unlike every prior phase's "parallel" group — where
> all members edited the single `index.html` and therefore had to be **physically serialized** — here
> **6.3b creates ONLY `docs/plan/product-revamp-diecast-v2-surface-goal-map.md` and touches NO
> `index.html`.** So 6.3a ∥ 6.3b is the **first genuinely parallel-safe group in the project**: dispatch
> them concurrently with zero merge risk. **6.1, 6.2, and 6.3a all edit `index.html` and have no merge
> mechanism between HTTP-dispatched runners**, so they run **strictly serial** (the critical path
> already serializes them: 6.1 before 6.2 before 6.3a). The generator is untouched this phase, so
> `org.js` is never written concurrently. This is the honest physical-artifact reading of the logical
> DAG, mirroring borderline-calls #11.
