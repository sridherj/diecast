# Decisions So Far — Product Revamp: Diecast Vision Prototype

> Cumulative decision log maintained by the fan-out planning orchestrator
> (run_20260611_174052_9e350b). Each detailed-plan child appends ~10-20 lines.
> Later planning children MUST adopt these naming/interface choices unless they
> document a deviation in "Suggested Revisions to Prior Sub-Phases".

## Run Configuration (owner-approved, 2026-06-11)

- **FULL AUTONOMY MODE**: owner pre-approved all decisions, including the two
  plan-reserved gates (2c stage-spine sign-off, Phase 1 morph feasibility gate).
  Borderline calls documented in `product-revamp-diecast-borderline-calls.md`.
- Plan review: skipped — cross-phase reconciliation only.
- Execution: end-to-end through Phase 6, no human checkpoints.
- Failure policy: retry once; second failure off critical path → log gap and
  continue; on critical path (1 → 2b → 3 → 5 → 6) → stop and report.

## Owner-Locked Inputs (from plan.collab.md / design-decisions)

- Stack: no build step · import maps · htm+Preact (CDN, <15KB) · one in-memory
  JSON state · `location.hash` routing · CSS View Transitions morph ·
  ~50-line scenario engine · 5 typed ops (`morph·nudge·promote·drillInto·pin`)
  through one dispatcher · driver.js overlays · frozen `org.json`.
- Identity: pure Diecast light world — cream `#F5F4F0`, ink `#1A1A28`,
  raspberry `#D6235C`, maker `#3B5BB0`, checker `#6B47B0`,
  IBM Plex Mono + DM Sans.
- E1–E5 evidence catalog: owner-blessed working default, revisit-on-sight.
- Per-family stage vocabulary: research-derived in Phase 2c (exploration's
  illustrative steps explicitly dropped); spine sign-off delegated to
  orchestrator under full autonomy.
- No P2 cut line: US7/US8/US9 ship in v1; extend timeline rather than cut.
- L3 budget: exactly one hard stop per flow.
- **NO TESTS (owner, 2026-06-11):** this deliverable has no concept of tests —
  no pytest, no unit/integration/e2e suites, no test harness, no CI. All
  verification is manual: open `prototype/index.html` from disk, click through,
  observe. Plans must not contain test-writing sub-phases or test files;
  "verification" sections describe human click-through checks only. No review
  agent or reconciliation pass may flag "missing tests" as a finding.
  (Fake test-result *content* rendered inside the prototype UI — e.g. the E1
  acceptance panel's fake test summary or E3 red→green repro — is data/visuals,
  not tests, and stays.)

## Reconciliation Outcome (2026-06-12 — see 2026-06-12-product-revamp-diecast-reconciliation.md)

- Verdict was NEEDS REVISION → both APPLY edits applied by the orchestrator;
  plans are now COHESIVE for execution.
- **F1 (HIGH, fixed):** the `org.js` stageModels rewrite is owned by **2c**, executed
  via 2a's generator, scheduled **after 2a.1 (generator exists) and before Phase 3
  dispatch**. Phase 3 must never build on `placeholder:true` vocabulary.
- **F2 (MED, fixed):** SCRIPTS four-family set is closed; demo-arc keys (5's
  `SCRIPTS.hiring`) are additive; final closure at 5 keys in Phase 6.
- **F3 (execution rule):** serialize the two generator batches — Phase 4.1's batch
  commits `org.js` before Phase 5.0's batch starts (4∥5 parallelism applies to
  everything EXCEPT these two batches).
- **F4 (execution rule):** Phase 3 and Phase 4 generator batches adopt Phase 5.0's
  section-stability invariant — all ORG sections outside the batch's declared
  additions must be byte-identical before/after.
- **F5 (scheduling):** honest totals ≈17–21+ sessions (envelope was 14–18); sanctioned
  by the owner's extend-don't-cut policy.

## Per-Phase Decisions

### Phase 1 — Keystone (2026-06-11-product-revamp-diecast-phase1-keystone.md)

- **HARD CONSTRAINT (affects 2a!):** `file://` pages block local ES-module
  imports AND `fetch()` → prototype is ONE file `prototype/index.html` with
  inline `<style>`/`<script type="module">`. Only https CDN import-map imports
  and classic `<script src>` work from disk. **Phase 2a must NOT plan
  `fetch('data/org.json')`** — use a classic-script `org.js`
  (`window.ORG = {...}`) or inline JSON; authoring source may live in
  `prototype/data/` but ships inlined.
- **appState v1 shape exported** (keys must not be renamed, only extended):
  `route · family · goal{id,title,crumb} · spines{feature,debug} · nudge{who,do,why}
  · receipts[] · pinned[] · drill · chat{messages,scriptIndex}`. 2a adds
  `'spike'|'data'` families and the org data.
- **Op vocabulary (closed):** `morph:<family>` · `nudge:<id>` · `promote:<artifactId>`
  · `drillInto:<target>` · `pin:<artifactId>`; controls carry `data-op="op:arg"`.
- **Scenario step shape:** `{narration, patch(s), transition?: 'morph'}` + `advance()`;
  index lives at `appState.chat.scriptIndex`.
- **View-transition anchors (prefix vt-):** `vt-goal-header · vt-chat-rail ·
  vt-nudge-card · vt-receipt-trail · vt-nav-rail`; evidence-strip anchor name
  reserved for Phase 3.
- **Design tokens:** `:root` block from `design-samples/app-shell.html` verbatim
  (`--cream --paper --ink --rasp --maker --checker --mono --sans` etc.) +
  motion tokens `--morph-duration:350ms · --ease-morph:cubic-bezier(0.2,0.8,0.2,1)
  · --motion-fast:120ms · reduced-motion fade 180ms` + `--radius-sm/md:4px/8px`.
- Routes so far: `#/` (chooser stub) · `#/goal/CAST-412` · `#/board` (stub).
- Spine labels in Phase 1 are `placeholder:true` + watermarked; 2c owns real vocabulary.
- CDN pins: esm.sh preact@10.26.x, htm@3; driver.js in import map, used in Phase 6.

#### Morph Decision Gate — VERDICT: **PASS** → View Transitions LOCKED for Phase 3 (sub-phase 1.3, 2026-06-12)

Resolved autonomously under FULL AUTONOMY via the pre-written 5-item checklist. **No browser
was connectable** (Claude-in-Chrome extension not connected, same as 1.1/1.2), so items 1–3 & 5
are evaluated on solid technical grounds (Chrome View-Transitions semantics + the actual CSS/DOM
written) and item 4 (the taste call) is recorded **PROVISIONAL pending a human eyeball**. The CSS
View Transitions API is a rendering API and is **not** origin-gated, so `file://` does not block it.

| # | Item | Verdict | Evidence (one line) |
|---|------|---------|---------------------|
| 1 | Anchors **glide**, not crossfade | **PASS** | 5 unique `view-transition-name`s, each on exactly ONE element/snapshot (verified: 1 markup element per anchor class), all 5 mounted across BOTH families → groups form in old+new snapshots → boxes glide/resize; spine zone deliberately unnamed → root crossfade. |
| 2 | No flash/flicker/layout jump | **PASS** | Single **synchronous** `paint()` (Preact `render()`) wrapped inside `startViewTransition(apply)`; no async in the callback, stable anchor identity (no unmount/remount), drill-in panel stays closed during the morph step → canonical no-snapshot-jank pattern. |
| 3 | Runs from `file://` in Chrome | **PASS** | View Transitions is a rendering API, NOT origin-gated; only https-CDN import-map imports + inline module/style used (grep-clean of `fetch(`/local imports); `startViewTransition` feature-detected with a fade fallback so even non-supporting builds degrade, not break. |
| 4 | Feels like ~350ms of **revealed layout**, not spectacle | **PASS (provisional)** | `::view-transition-group(*)` locked to `--morph-duration:350ms` + `--ease-morph:cubic-bezier(0.2,0.8,0.2,1)` (decelerate); glide+crossfade only — no rotate/bounce/overshoot/flash. Matches the Linear/Raycast register **on paper**; the soft/taste item — needs a human eye on the rendered motion (browser unavailable). |
| 5 | Reduced-motion fallback works | **PASS** | `dispatch()` & `advance()` both branch on `matchMedia('(prefers-reduced-motion: reduce)').matches` → `fade(apply)` (state applied + 180ms opacity ramp, **no sliding**) instead of `startViewTransition`; plus a CSS `@media (prefers-reduced-motion: reduce)` guard forcing any VT group/old/new animation to 1ms. |

**Outcome:** 5/5 PASS on static analysis (item 4 provisional). Gate **PASSES** → View Transitions is
the locked morph mechanism for Phase 3; the keyed CSS panel-swap contingency is **NOT** built (one
mechanism ships) and `product-revamp-diecast-borderline-calls.md` is **not** touched. Because the op
grammar + motion tokens are identical across both mechanisms, the fallback stays cheap if a human
later judges item 4 a "spectacle" on sight — that reversal would be a Phase-3-mechanism swap only, no
plan reshape. **Human action:** open `prototype/index.html` from disk in Chrome, click **Next ▸** to
the *"this is actually a bug…"* step, and confirm item 4 by eye (and ideally re-confirm 1–3 & 5).

### Phase 2b — Component Kit & Aesthetic Lock (2026-06-11-product-revamp-diecast-phase2b-component-kit.md)

- **Component roster (8, all pure `(props)→vdom`, inline in index.html):** `ColleagueCard`
  (`{agent, density:'card'|'line'}`) · `EvidenceBlock` (`{kind:'E1'..'E5', data}`, one
  component + kind switch) · `StageSpine` (`{spine}`, shapes
  `segments|loop|timebox|pipeline`; spike meter reads `spine.timebox.{budget,used}`) ·
  `NudgeCard` (`{nudge:{who,do,why}}` = appState v1 verbatim) · `Decision` ladder
  (`{atom, layer:'pill'|'callout'|'row'}`) · `EscalationRail` · `AutonomyDial`
  (`{value, trust}`) · `GuideMark` + Guide voice CSS.
- **Decision atom = playbook-05 Step-1 schema field names VERBATIM** (`reversibility ·
  options_considered · revisit_if · originating_agent · supersedes/superseded_by ·
  spike_ref · influenced[]` …); Phases 3/5 reuse, never rename.
- **Agent fixture shape** (2a's org.json agents must be supersets): `{id, slug,
  kind:'maker'|'checker'|'human'|'guide', pairedWith, stats:{compliancePct, loops, runs},
  autonomy, rework:{used,budget}, inflight, state}`.
- **Avatar grammar:** human=circle · maker=square `--maker` outline · checker=square
  `--checker` fill · **Guide=diamond** (recommended default; final pick in 2b.1's
  rendered-options pass against pre-written criteria).
- **New tokens (extend-only):** `--fail:#B22439`; L-badges L1=`--ink-35` L2=`--warn`
  L3=`--rasp`; confidence glyphs ●/◐/○ (never percentages).
- **vt- anchors live on shell zone wrappers, NEVER on kit components** (a duplicate name
  on `#/kit` silently kills all transitions).
- **`#/kit` = isolation harness route** (hash-only, hidden from nav); fixtures use canonical
  vocabulary (CAST-412, M04/S03/R02, crud-orchestrator, 99.9%·505 runs) so 2a wiring is a
  data swap. Verification is manual click-through per the NO TESTS rule.
- **Signature screen = upgraded `#/goal/CAST-412`**; slop gate = `/cast-preso-check-visual`
  + `/cast-preso-check-tone` on screenshots, scoped to not-generic/not-ai-aesthetic.
- Escalation rail: ranked structural weight (7A) + nothing pre-selected (reconciles PB-04
  vs PB-05). AutonomyDial ships static (prop-driven); Phase 5 wires the toggle beat.
- Plan review: skipped per run config (Phase 1 precedent).

### Phase 2c — Stage-Model Research (2026-06-11-product-revamp-diecast-phase2c-stage-research.md)

- **Canonical stage definitions land in `docs/plan/product-revamp-diecast-stage-models.md`**
  (2c execution deliverable); Phases 3–4 cite it, never re-derive vocabulary.
- **`stageModels` field contract (2a MUST reserve this org-data slot, plain JSON):**
  `stageModels.<family> = { shape, progression?, loop?{over,budget}, timebox?{budget},
  steps: [{id, label, shortLabel?, does, surface, surfaceWhy, artifacts[], refs[],
  evidence: 'E1'..'E5'|null}] }`. Family keys exactly `feature|debug|spike|data`.
- **appState.spines keeps Phase 1 shape** — `steps` stays `string[]`, derived via
  `stageModels.<f>.steps.map(s => s.shortLabel ?? s.label)`; rich objects live only in
  org data. `placeholder` flips to `false` when 2c vocabulary lands.
- Step ids `<family>-NN` (`feat-01`, `dbg-01`, `spk-01`, `data-01`); 4–7 steps per
  family; labels >18 chars need a `shortLabel`; each step owns ≥1 artifact; E1–E5 each
  get exactly one home step (`evidence` field) in their family.
- Owner sign-off gate → written self-evaluation (5-test practicality rubric, per-family
  verdict, loop-once rework); plan review skipped per run config.
- Conditional flag channel: if research contradicts a locked 2b spine variant
  (segments/loop/timebox/pipeline), the stage-models note flags it for reconciliation —
  no silent shape changes.

#### Phase 2c — Execution Output (sp1→sp2→sp3 complete; canonical note `product-revamp-diecast-stage-models.md`)

Derived per-family spines (adopt these step labels verbatim — Phases 3/4 cite the note,
never re-derive; sp4 encodes §5 of the note into `org.js` via 2a's generator, after 2a.1,
before Phase 3 dispatch — Reconciliation F1). Self-evaluation gate: **all four families PASS**,
no rework loop. Asymmetry intended (SC-005): counts 5/5/4/5, three shapes.

- **feature** (`segments`, `progression:'linear-reentrant'`, 5): Shape the Problem · Commit & Scope ·
  Design the Approach (`Design Approach`) · Build & Ship · Show It's Done. **E1 → feat-05.**
- **debug** (`loop`, `loop:{over:['dbg-02','dbg-03','dbg-04'],budget:3}`, 5): Reproduce Reliably ·
  Form a Hypothesis · Run an Experiment · Log Confirm/Refute · Prove the Fix. dbg-01 opens / dbg-05
  exits. **E2 → dbg-04, E3 → dbg-05.**
- **spike** (`timebox`, `timebox:{budget:'3h'}`, 4): Frame the Question · Probe Options ·
  Evaluate Findings · Land the Verdict. **E4 → spk-04.**
- **data** (`pipeline`, 5; inner explore loop intra-`data-04`, NO top-level loop): Import Sources ·
  Tidy & Validate · Transform / Wrangle (`Transform`) · Explore (Viz↔Model) (`Explore`) ·
  Publish + Provenance (`Publish`). **E5 → data-05.**
- **`stageModels` field contract (final, plain JSON, parses via jq/node):** `stageModels.<family> =
  { shape, progression?, loop?{over,budget}, timebox?{budget}, steps:[{id, label, shortLabel?, does,
  surface(doc|board|pr-thread|ledger|notebook|memo), surfaceWhy, artifacts[≥1], refs[≥2 keys],
  evidence:'E1'..'E5'|null}] }`. `appState.spines.<f>.steps` = `steps.map(s => s.shortLabel ?? s.label)`
  (render layer; rich objects live only in org data).
- **sp4 ids note:** `dbg-05` + `data-05` are NEW ids; stub `dbg-04=fix` is re-tasked to Log
  Confirm/Refute (owner-sanctioned `stageModels` rewrite, not drift).
- **FLAG (carried for 2b/Phase 3, `spine-variant revision proposed` — do not redesign):** spike's
  `timebox` band must render its **four sub-steps beneath the budget meter** (meter = wrapper, not the
  only element). Data inner-loop question RESOLVED (intra-step, no flag).

### Phase 2a — Data Spine (2026-06-11-product-revamp-diecast-phase2a-data-spine.md)

- **Spine ships as classic script `prototype/data/org.js`** → `window.ORG =
  Object.freeze({...})` (Phase 1 file:// contract; NEVER fetch). Authored by a seeded
  (`seed(42)`) **self-validating** generator in `prototype/data/_build/` (build-time only,
  node_modules gitignored, output committed; refuses to emit on any invariant violation —
  5–8 atoms/goal, exactly 1 L3/flow, referential integrity, trust-stat aggregation). No
  separate validator/test file, per the NO-TESTS rule.
- **ORG top-level keys (frozen):** `meta · org · humans · guide · agents · stageModels ·
  goals · board · decisions · hiring · layer2`. 2c's `stageModels` contract reserved
  verbatim (placeholder content, `<family>-NN` step ids); agents are supersets of 2b's
  fixture shape (`stats:{compliancePct,loops,runs}`, `pairedWith`, `kind`); decision atoms
  = playbook-05 ADR schema verbatim + a scannable `diff` field (`DEC-<goal>-NN`,
  supersede-not-edit).
- **CAST-412 canonical title = "Add RBAC to checkout"** (playbook 04's Invoice pick
  rejected — Phase 1 appState already exported RBAC; activity-log structure ported). Goal
  ids: CAST-412 feature · CAST-431 debug ("Checkout 500s on coupon apply" ← v4.2 RBAC
  migration) · CAST-452 spike (vendor SDK 180ms vs 200ms p95) · CAST-461 data (Q2 revenue
  dip, sources disagree 8%). **CAST-417 (roles-column drop) is THE single feature L3**,
  shared by board arc + canvas beat; one superseded L1 pair (GraphQL→REST) in feature.
- **Cred stats unified:** per-agent `stats` single source; marketplace line =
  crud-orchestrator (99.9% · 505 runs · 2 loops); dial trust = feature-roster aggregate
  (99.4% · 312 runs), generator-tied. Roster: 12 agents / 6 archetypes; hiring: 6
  candidates, 5 dimensions, produced-work artifact stubs; Layer-2: 12 contracts (8
  chain-aligned + 4 cross-cutting), 8-chain, 6-project portfolio.
- **appState v1.1:** `family` ∈ 4 values; `spines` derived from stageModels + per-goal
  `spine_state` (Phase 1 shape preserved); new key `org`; receipts gain `decision_id`
  (morph receipt = atom `DEC-CAST-412-03`). Goal route resolves all four goal ids.
- Freeze policy: values frozen after 2a, additive extensions only; `stageModels` region
  2c-owned (rewritten via the generator). Drift grep recorded for Phase 6 re-run; 2b's
  `#/kit` fixture literals are the one sanctioned grep exception until its data swap.
- Plan review: skipped per run config (Phase 1/2b precedent).

### Phase 3 — Feature + Debug Flows & Real Morph (2026-06-11-product-revamp-diecast-phase3-feature-debug-morph.md)

- **`vt-evidence-strip` claimed** (Phase 1's reserved name) on the evidence ZONE WRAPPER —
  anchor set is now 6; wrapper glides in the morph, EvidenceBlock content crossfades (E1↔E2).
- **ORG additive extension via the 2a generator (never hand-edit):** `goals[id].execution =
  {runs[], focus_run (tree ~13 nodes), iteration {findings, rework 1/3, exits, pr+diff_stub}}`
  — full on CAST-412, thin on CAST-431 — plus `goals['CAST-412'].morph_view` (post-reclass
  debug-shape state: iter 1/3, seeded E2). New invariants: tree agents resolve, rework-tag
  consistency, one focus_run per goal with execution data.
- **Morph stays on CAST-412** (header/crumb/chat never change); CAST-431 is the standalone
  debug flow. Undo emits NO second receipt (one atom DEC-CAST-412-03, one receipt).
- **Stage navigation reuses `drillInto`** with step-id targets (`'execution'` = HOW, step id =
  stage focus) — op vocabulary stays closed at 5. New components: `StageSurface` (familiar-tool
  renderer keyed on `stageModels.steps[].surface`: doc|board|pr-thread|ledger|notebook|memo),
  `RunNode` (run_node.html idiom port), `IterationPanel` — all pure props-only; Phase 5a reuses
  IterationPanel (ticket activity log), Phase 4 reuses StageSurface (memo/notebook).
- **Scripts: `SCRIPTS = {feature, debug}` + additive `appState.chat.scriptKey`** (Phase 4 adds
  spike/data keys). New additive appState key `stageFocus`. CSS prefixes `surf-*`/`exec-*`.
- **E1 screenshots = real rasters** via /cast-preso-illustration-creator + checker into
  `prototype/assets/`, loaded by relative `<img>` (file://-legal); 2b CSS/SVG thumbs = onerror
  fallback. Exec panel stays CLOSED during the morph step (snapshot-jank guard).
- Slop gate on 4 surfaces (feature, debug, drill-in open, morphed state); drift grep re-run at
  3.4. Plan review: skipped per run config (Phase 1/2a/2b precedent).

### Phase 4 — Spike + Data-Analysis Flows (2026-06-11-product-revamp-diecast-phase4-spike-data.md)

- **Sub-phase shape: 4.1 spike ∥ 4.2 data → 4.3 FR-017 parity → 4.4 stitch+gates.** ONE
  generator batch (owned by 4.1) covers both goals: thin `goals[id].execution` (run list,
  NO tree) for CAST-452/461, `goals['CAST-452'].parity = {command, transcript, artifact_id,
  caption}`, `goals['CAST-461'].evidence.resolved_view = {series(both sources),
  reconciliation_note}` + 4 new gate invariants. Phase 5 must NOT touch these goals/sections.
- **SCRIPTS complete: `{feature, debug, spike, data}`** (additive scriptKey per Phase 3
  contract); no further script keys planned. Spike ~6–7 beats (parity slot after verdict,
  before L3 stop); data ~7 beats ending on the reconciled report.
- **E5 chart = hand-authored data-driven inline SVG (M9 idiom) inside EvidenceBlock's E5
  branch** — never a raster (drift rule: numbers render from ORG); existing tokens only;
  one renderer, two states (at-rest ◐-flagged vs resolved_view).
- **The data L3 is the ONE script-wired rail resolution in the prototype** (option b →
  chart re-renders to resolved_view + one receipt with the atom's decision_id; ORG
  unmutated, reload resets). Spike L3 stays an unresolved stop (Phase 3 #10 consistency).
- **FR-017 parity:** script-patch-driven reveal via additive `appState.parityOpen` flag —
  no sixth op; terminal pane ink-dark (deliberate identity exception, slop-gate checked,
  light-paper fallback costed); chat tier = the existing rail; `parity-*` CSS prefix.
- **`spike_ref` navigation = local disclosure** (chip→callout + scroll/highlight), both
  directions ≤1 click; L2 timebox-extension chip ("2h→3h") renders on the meter.
- StageSurface `memo`/`notebook` kinds fleshed in place (as Phase 3 assigned); notebook
  cells use native `<details>`. Slop gate on 4 surfaces (spike canvas, data canvas, parity
  moment, reconciled E5); drift grep extended with `CAST-452 · CAST-461 · 180ms · 1h40m ·
  8%` + source names. Plan review: skipped per run config (all-phase precedent).

### Phase 5 — Colleague Surfaces (2026-06-11-product-revamp-diecast-phase5-colleague-surfaces.md)

- **Shape: 5.0 shared-rails → 5a ∥ 5b ∥ 5c → 5.4 stitch+gates.** 5.0 owns the ONE generator
  batch: `goals['CAST-412'].requirements_doc` (elements w/ L1-3 hierarchy, ONE comment thread w/
  ONE PM commenter, delta, writeback) · `agents[].versions/monitoring` (deep on crud-orchestrator)
  · `org.skills` (nested — top-level keys frozen) · `dial_demo:true` on exactly one CAST-412 L2
  atom; new invariant: CAST-452/461 sections byte-identical (Phase 4 parallel guard).
- **Routes (final 10):** `#/board` (real) · `#/ticket/CAST-412` · `#/decision/:atomId` (artifact
  + escalation frames in ONE route, branches on L3+awaiting_human) · `#/decisions/CAST-412`
  (trail + AutonomyDial header + L2 digest) · `#/hire` · `#/marketplace` (= the unified
  catalogue, scope badges) · `#/agent/:slug` (resume + Versions/Monitoring tabs = agent ops) ·
  `#/skills/new` · `#/layer2` (one page, 3 sections) · `#/reqs/CAST-412`.
- **appState additive:** `boardFilter · hiring{step,expanded,compare} · autonomyLevel ·
  reqsDoc{openComment,deltaView}`. **`SCRIPTS.hiring` added** (additive; revises Phase 4's "no
  further script keys" → four-family set stays closed). UI state = plain handlers, ops closed at 5.
- **CAST-417 rail stays an unresolved stop** (only Phase 4's data L3 resolves). Dial demo lives
  on the trail page: Conservative pins the dial_demo L2 as a stop-and-confirm card; reload resets.
- **New helpers:** `DigestNotice` (one component = 5a L2 digest + 5c US7 write-back),
  `RadarChart`/`Sparkline` (data-driven inline SVG, E5 idiom). CSS prefixes `hire-*/mkt-*/ops-*/l2-*`.
- **L1/L2/L3 collision rule (reqs-doc):** hierarchy = typographic depth only; reversibility =
  ⚖-prefixed colored badge only. PB-05 "should've asked" loop EXCLUDED (hold scope).
- Slop gate on 6 surfaces; effort honest at ~4.75–5.75 sessions (> envelope; owner: extend, not
  cut). Plan review: skipped per run config (all-phase precedent).

### Phase 6 — Polish & Showability (2026-06-11-product-revamp-diecast-phase6-polish-showability.md)

- **Shape: 6.1 chooser+walkthroughs → 6.2 density+full slop gate → {6.3a inline+drift ∥ 6.3b
  SC-006 map} → 6.4 dist-file sign-off.** Honest effort ~2.75–3.25 sessions (> 2-session
  envelope; extend-not-cut).
- **Walkthroughs = BOTH (owner default):** `TOURS = {feature,debug,spike,data,hiring}` keyed
  like SCRIPTS, 5–8 stops on new `data-tour` attributes, anatomy-not-story, never call
  `advance()`; + demo-script overlay (additive `appState.demoScriptOpen`, `s` key, renders
  SCRIPTS beats w/ current index highlighted). driver.css added via CDN `<link>` + mandatory
  `tour-*` token restyle (stock popovers fail the gate). Ops stay closed at 5; script keys
  closed at 5; NO ORG generator batch in Phase 6 (chooser/tour copy = demo chrome).
- **Chooser:** `#/` stays a bare route (Phase 1 precedent), 5 verb-first cards (titles/ids
  render from ORG.goals) + standalone-areas row + GuideMark intro; CSS `choose-*`/`tour-*`/`demo-*`.
- **Single file = generated dist:** zero-dep Node one-shot `prototype/_build/inline.mjs` →
  `prototype/dist/diecast-prototype.html` (inline org.js + base64 E1 rasters, ≤~5MB guard w/
  WebP recompress; generated-header, never hand-edit; dev files stay canonical). CDN libs/fonts
  stay CDN (file:// contract = local file + https CDN since Phase 1); offline fallback
  (one-shot vite-plugin-singlefile) documented, not built.
- **Full slop gate = 21 captures** (every screen incl. tour popover, demo overlay, morphed
  CAST-412, resolved CAST-461; hiring gated on report-card step only). Final drift sweep =
  Phase 3+4+5 grep canon consolidated + Phase 6 copy; **`#/kit` exception RETIRED** (data swap
  completed; zero sanctioned exceptions at project end).
- **SC-006 map → `docs/plan/product-revamp-diecast-v2-surface-goal-map.md`** (rows = surfaces +
  cross-cutting mechanics; outcome-sentence goals, S/M/L, deps, advisory rank). SC-002
  fresh-peer test = the single human action item. Plan review: skipped per run config
  (all-phase precedent).

## Execution Records

### Sub-phase 2b.1 — Grammar (Avatar · ColleagueCard · Guide character) — DONE (2026-06-12, run_20260611_221313_b4091e)

Built additively into `prototype/index.html` (Phase 1 untouched — appState v1, the closed
5-op set, the dispatcher/scenario engine, and all 5 vt- anchors verified unchanged). Added:
the `#/kit` harness route (hash-only, hidden from nav), inline `FIXTURES` (canonical
vocabulary only — `CO`/`crud-orchestrator`, `CC`/`crud-compliance-checker`, `YOU`/`@you`/`SJ`,
`GUIDE`, plus a `CO_SOLO` broken-state stub = CO with `pairedWith:null`), the `Avatar`
primitive (one component, four kinds), `ColleagueCard` (one function, two densities), the
token extensions (Contract 7), and the Guide character treatment.

**The USER-DEFERRED Guide call → treatment A (the diamond) KEPT; B and C deleted.**
Pre-written selection criteria (judged before picking): (1) distinct from worker agents at a
glance; (2) no mascot/anthropomorphic theater (playbook 04 pitfall 8); (3) survives 16px
rendering; (4) spends no raspberry (the Guide is persistent; raspberry means needs-you);
(5) introduces no new hue. Verdict against the rubric:

| Cand. | Treatment | Verdict | Reasoning |
|-------|-----------|---------|-----------|
| **A** | **Diamond mark (ink-filled, square-family rotated 45°) + mono `GUIDE` wordmark; voice = typography + structure (chat left-rule + cream-deep tint · `◈ Guide` nudge attribution · "decided with ◈ Guide" receipt byline)** | **KEPT** | Square-family ("an agent") yet instantly distinct ("a different kind of agent") — exactly the Contract 6 grammar. Reuses the Avatar diamond, so one mark covers avatar + all three voices. No new hue; survives 16px; spends no raspberry. |
| B | Ink monogram seal (circle-with-diamond knockout — "stamp"/diecast metaphor) | rejected | The stamp reads decorative and muddies the human=circle grammar at 16px (a circle outline = human); decode cost over a glanceable shape. |
| C | Typographic-only (`GUIDE ▸`, no mark) | rejected | No glanceable mark — fails criterion 1 (the label-free flash test) the moment the Guide sits beside worker avatars in chat/nudge/receipt. |

Treatment A is built in all three voice contexts (rendered on `#/kit` under "GuideMark + voice
contexts") + a `GuideMark({size, wordmark?})` component. The three candidate marks are rendered
once on `#/kit` ("Guide character — candidates judged") as the documented judgment record so a
human can override the provisional taste call on sight (the owner deferred this "to seeing
options rendered"); only A is built into any product voice — B and C are not live treatments.

**Deviations from the gallery samples (reference, not spec — recorded per the build directive):**
- ColleagueCard re-derived as a **CSS-grid mini-card** (head spans the top, the other four
  lockup fields flow into a four-column row beneath, footer last) rather than the sample's ad-hoc
  flex stack — this enforces *identical field order across both densities from one `slots`
  fragment* (the zero-drift guarantee), which the two separate gallery markups (4B vs 4C) did not.
- **Optical avatar sizing** added (square inset to ~0.88, circle ~0.98, diamond bumped via
  `rotate(45deg) scale(.62)` to fill its rotated silhouette) so circle/square/diamond read as the
  same visual mass — the flat gallery `.av` had no optical compensation.
- The Guide mark is **ink-filled, not checker-violet** (the Phase 1 chat-header `◈` is tinted
  `--checker`); per accent discipline the Guide introduces no hue and checker-violet is reserved
  for checker agent chrome. The live Phase 1 chat header is left as-is by 2b.1 (additive, no
  regression); aligning it to the ink GuideMark is folded into 2b.3's signature-screen composition.

**Verification (NO TESTS — C1; manual click-through is the only verification):** browser was
**not connectable** in this autonomous run, so static verification was performed —
`node --check` of the extracted inline module (PASS), grep-clean of `fetch()`/local imports
(C2 PASS — only the two CDN bare-specifier imports), grep confirming **one** `ColleagueCard`
lockup (PASS), grep confirming **no** `view-transition-name` on any kit/`av-`/`cc-`/`gm-`/`gv-`
component (Contract 9 PASS — the 5 names are shell-zone-only), and token-discipline grep (PASS —
the only raw hex added is `--fail:#B22439` in `:root`). Two items are **PROVISIONAL pending a
human eyeball** (browser unavailable, per the prototype's no-browser-for-visual-gates posture):
**(P1)** the Guide label-free flash test (does A read as "a different kind of agent" beside
maker/checker/human at a glance, incl. at 16px?), and **(P2)** the optical avatar balance (do
diamond/circle/square actually read as equal mass on screen?). **Human action:** open
`prototype/index.html` from disk in Chrome, navigate `#/kit`, confirm a clean console and
eyeball P1 + P2; if A is judged wrong on sight, the swap is CSS-only (`GuideMark` + `gv-*`
classes) with no plan reshape.

### Sub-phase 2a.3 — Wire, Sweep, FREEZE — DONE (2026-06-12, run_20260611_225407_8becfb)

The data spine is wired into the real Phase-1 app and **frozen**. Summary of the 2a contract as sealed:

- **File layout:** `prototype/data/org.js` (THE deliverable — classic script `window.ORG = Object.freeze({…})`,
  GENERATED header, never hand-edited) ← `prototype/data/_build/generate-org.mjs` (seeded, self-validating
  generator; `node_modules` gitignored). `index.html` loads the spine via one classic `<script src="data/org.js">`
  placed **before** the inline module (the only `file://`-legal local data path; no `fetch`, no local imports).
- **Schema keys (11, frozen):** `meta · org · humans · guide · agents · stageModels · goals · board · decisions ·
  hiring · layer2`. Mixed-case is deliberate (atoms = snake_case playbook-05 ADR names; agents = camelCase 2b
  stat names). **Canonical-value table:** single source is `org.js`; the grep-enforced token list lives in the
  Phase 2a plan (Contract #6) and the 2a `_shared_context.md`.
- **Step-id indirection:** goals reference stage steps by **step id** (`feat-04`, `dbg-02`, …); `appState.spines.<family>`
  is composed at boot from `ORG.stageModels.<f>` (`steps.map(s => s.shortLabel ?? s.label)`) + the family goal's
  `spine_state` (step id → numeric index), preserving Phase 1's spine shape exactly.
- **appState v1.1** (extends v1, zero renames): `family` ∈ feature|debug|spike|data; `spines` gains spike+data (all
  four derived); new key `org = window.ORG`; `goal` from `ORG.goals[id]`; receipts gain `decision_id`. The morph
  receipt now DERIVES from atom **DEC-CAST-412-03** (level/label/`at`=17:52 from the atom timestamp + `decision_id`).
  Route guard resolves all four goal ids (`#/goal/<id>`); a missing `window.ORG` paints a visible error banner
  (stubs deleted, not shadowed). Phase-1 contracts intact: op set closed at 5, vt- anchors unchanged, `advance()` whole.
- **Drift sweep (recorded for Phase 6 re-run):**
  `grep -rn -e 'CAST-4' -e 'M04\|S03\|R02' -e '99\.9\|99\.4\|505 runs\|312 runs' -e 'crud-orchestrator' -e '1/3' -e 'Northwind\|northwind' prototype/ --include='*.html' --include='*.js'`
  → in `index.html` the Phase-1 app surface is **zero canonical-token hits**; the only remaining `index.html` hits
  are the **sanctioned 2b `#/kit` exception** (the `FIXTURES` block + the 2b kit/Evidence components, lines ~1050–1573)
  which hand-type canonical vocabulary by design "so 2a wiring is a data swap" — that exception is retired when 2b's
  data swap lands (and finally in Phase 6's sweep). All other hits are in `data/org.js` and `data/_build/` (expected).
- **FREEZE policy + 2c exception:** `meta.frozen_at = '2026-06-11T18:00:00.000Z'` (a fixed constant `t(540)` in the
  generator — never `Date.now()`; byte-identical re-runs verified). After 2a, values are frozen; later phases extend
  additively via the generator only (F4). The **one standing exception is the `stageModels` region**, owned by 2c —
  which **landed concurrently with this sub-phase**: the generator + `org.js` now carry 2c's derived vocabulary
  (`placeholder:false`; feature *Shape the Problem · Commit & Scope · Design Approach · Build & Ship · Show It's Done*;
  debug/spike/data per the stage-models note). The generator is the merged single source (my freeze + 2c vocab),
  the invariant gate is green, and `node generate-org.mjs` reproduces `org.js` byte-identically. The wiring is
  vocabulary-agnostic, so it renders the real 2c labels with no change.
- **Verification (NO TESTS — manual click-through only; this autonomous run has no browser):** static checks performed
  on technical grounds — `index.html` parses (`node --check` of the extracted module: PASS); classic `<script src>`
  precedes the module (load order verified); `file://` legality (no `fetch`/local imports; only the 3 CDN bare
  specifiers; `window.ORG` the only spine global); a throwaway node boot-harness confirmed appState boots from
  `window.ORG` (FEATURE_ID→CAST-412, FLAGGED_RULE→R02, MORPH_ATOM→DEC-CAST-412-03 @ L2/17:52, all four spines derive
  with correct shape + current index) — the harness lives in `/tmp`, never committed (NO-TESTS). **PROVISIONAL (human
  eyeball, browser unavailable):** open `prototype/index.html` from disk in Chrome → (V1) the CAST-412 canvas renders
  title/crumb/nudge/spine from the spine and the console is clean; (V2) `#/goal/CAST-431|452|461` each render the shell
  with their family's spine; (V3) the demo script walks end-to-end and the morph receipt reads `DEC-CAST-412-03`.
- Plan review: skipped per run config (all-phase precedent).
