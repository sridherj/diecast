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

### Sub-phase 2b.3 — Aesthetic Lock (Signature Screen & Slop Gate) — DONE (2026-06-12, run_20260611_230342_b92fb0)

**THE AESTHETIC IS LOCKED.** The signature `#/goal/CAST-412` canvas now composes **entirely from kit
components** and passes both cast-preso slop-gate checkers (provisional, static source review — no browser this
run). This de-risks SC-004 before Phase 3 mass-produces screens.

- **Signature-screen composition — `GoalCanvas` reduced to a data slice + component calls (zero Phase-1 stub
  markup remains):** guide-line → `GuideMark` (locked diamond, real narration) · spine → `StageSpine` (2b.2a) ·
  nudge → `NudgeCard` (2b.2b) · In-flight work → a 3-row stream of **line-density (4B) `ColleagueCard`s**
  (`FIXTURES.CO`/`.CC`/`.YOU`) · Stage artifacts → one **E1 `EvidenceBlock`** · receipt-trail → **6A `Decision`
  pills** (each morph receipt's `{decision_id,label,level}` maps to the pill's `{id,diff,reversibility}`). The
  bespoke `.work-item`/`.panel`/`.receipt` stub markup is gone; the only `.panel` left is the dev-/drill-gated
  Phase-3 execution placeholder (not on the showable canvas).
- **Guide treatment (the 2b deferred craft call) — LOCKED + reconciled to hue-free:** treatment **A (ink diamond
  + mono wordmark)** from 2b.1 stands. 2b.3 removed the residual **checker-purple** Guide marks that contradicted
  the "no new hue" lock — the chat-rail header now renders `GuideMark` (was a bare checker-tinted `◈`), guide chat
  messages carry an **ink left-rule** (`.msg.guide .mtext`) with a hue-neutral `◈ Guide` byline (was
  `color:--checker`), and the canvas guide-line renders `GuideMark`. The Guide's identity is now carried by **shape
  (diamond) + structure (left-rule)**, never color — strengthening the label-free distinctness contract.
- **Density-drift check (2nd surface, after 2b.1):** one **4C (card) `ColleagueCard`** dropped on `#/board`, drawn
  from the **same `FIXTURES.CO` object** the canvas renders at 4B (line) density → no field drift (literally one
  object, two `density` props).
- **First-principles deviations from the gallery samples (recorded):** (1) the Part-2 `body` was a `1fr·1fr` grid
  of stub panels → now a **single stacked column** (the E1 block needs full content width; two ~329px columns
  couldn't hold a 460px block). (2) The receipt-trail renders the kit **`Decision` pill** rather than the retired
  Phase-1 `.receipt` chip (the full 6A→6B→6C ladder shipped in 2b.2b). (3) Work-stream colleagues are sourced from
  **`FIXTURES`** (the sanctioned 2b `#/kit` exception, C4) — the real per-goal renderer that reads
  `ORG.goals[id].work_stream` is **Phase 3** (2a.3's own comment defers it there).
- **Slop-gate verdicts (PROVISIONAL — static source review of the rendered component HTML/CSS, NOT a rendered
  1440px screenshot; no browser in autonomous runs):**
  - `/cast-preso-check-visual`: **`not-generic` PASS · `not-ai-aesthetic` PASS.** No rework required. One borderline
    call-out (logged to `borderline-calls.md`): the Phase-1 chat `.opbtn` ghost-pill is the softest generic tell, but
    stays within system tokens and is contextually appropriate — does not fail. (Cited: dot-grid editorial canvas,
    ink-tinted shadows not blue-black, raspberry reserved to needs-you, hue-free Guide identity.)
  - `/cast-preso-check-tone`: first pass **FLAGGED** 3 em-dashes in on-screen copy → reworked (Guide narration split
    into two sentences; receipt-trail empty-state + drill-in stub switched to the UI's own `·` middot — no literal
    `--`) → **re-run verdict CLEAN.** No GPT-isms / hedging / formulaic patterns.
- **Token discipline (grep-clean):** **no raw hex outside `:root`** — 2b.3 removed the last two offenders (the dead
  Phase-1 `.loop-stage.now{color:#fff}` swept with the orphaned spine-stub CSS; `.next-btn` → `var(--paper)`).
  Raspberry remains confined to needs-you semantics (L3 badge, rail hero, dial L3 legend, error fallbacks).
- **Phase-1 morph gate — static re-check PASS (no regression from the re-skin):** vt- anchors unchanged **5×1**;
  `::view-transition-group(*)` 350ms register + reduced-motion guard intact; the receipt-trail/nudge/spine ZONE
  WRAPPERS keep their anchors (only inner content swapped, Contract 9); closed 5-op set + `advance()` whole; demo
  script walks end-to-end by code inspection (`node --check` of the extracted module: PASS).
- **Concurrency note:** the Phase-2a `2a.3` drift-sweep landed in `index.html` mid-sub-phase (ORG-wired appState,
  neutralized work-item stubs). 2b.3 composed against that post-2a.3 state; FIXTURES-sourced kit zones are the
  sanctioned C4 `#/kit` exception, not re-introduced drift.
- **Human-eyeball carry-forwards (browser unavailable — never block, per project posture):** (CF1) re-run BOTH slop
  checkers on a real **1440px Chrome screenshot** to upgrade the provisional verdicts to rendered; (CF2) the Guide
  **label-free flash test** on the rendered screen (PROVISIONAL pass on static grounds: diamond + left-rule +
  `◈` byline read distinct from circle-human / square-agent without labels); (CF3) **runtime/ORG copy not assessed
  by the tone pass** — `FEATURE.nudge.why` (`"…flagged R02 — unblocks…"`) and the Phase-1 chat-script narration
  still contain em-dashes; they are 2a/Phase-1-owned data, so a dedicated copy pass (or 2a) should de-em-dash them.
  The open 2b.1 (P1 Guide flash, P2 avatar optical balance) and 2b.2a/2b.2b visual-taste carry-forwards also remain.
- Plan review: skipped per run config (C7, all-phase precedent).

## Owner Prototype-Review Feedback (2026-06-12 — BINDS Phase 3)

Owner reviewed the cumulative prototype (Phase 1 + 2a + 2b) and raised two issues. Both are
routed to **Phase 3** (owner decision); do NOT hand-patch the frozen artifact out-of-band.

- **PRF1 — Goal-canvas in-flight agents are unrelated to the goal (route to Phase 3).**
  `GoalCanvas` currently renders three **2b kit FIXTURES** (`FIXTURES.CO/CC/YOU`) for the
  "In flight · work" stream, so CAST-412 ("Add RBAC to checkout") shows generic colleagues
  unrelated to the title. The real, RBAC-relevant per-goal work already exists in
  `ORG.goals[id].work_stream` (ticket-shaped `{id,label,assignee,step,kind}`; CAST-412
  assignees resolve to real `ORG.agents`: `entity-creation · api-contractor · migration-author
  · crud-orchestrator`, plus `@you`). **Phase 3 action:** its planned per-goal work renderer
  must read `ORG.goals[id].work_stream` (resolving each `assignee` against `ORG.agents`) and
  replace the kit-fixture ColleagueCards. Owner explicitly chose "leave for Phase 3" over an
  interim patch.

- **PRF2 — ChatRail must be PER-GOAL, not global (contract amendment for Phase 3).**
  Current Phase-1 contract made `appState.chat = { messages, scriptIndex }` a **single global**
  object shared across goals. Owner directive: the right-side chat should be **per-goal only**
  — each goal id carries its own conversation thread (and its own scenario position). **Phase 3
  action:** key chat state by goal id (e.g. `appState.chat.byGoal[goalId] = {messages,
  scriptIndex, scriptKey}` or equivalent), so switching goals shows that goal's thread, not a
  shared one. This refines (does not rename) the Phase-1 `appState.chat` contract and composes
  with Phase 3's planned additive `appState.chat.scriptKey`. The ChatRail header handle (today
  derived from the routed goal title) stays goal-scoped by design — per-goal is the desired
  end state, confirmed by owner.

## Phase 3 — Decision Summary (sub-phase 3.4 close: the Real Hero Morph & Flow Stitch, SC-003)

Phase 3 is COMPLETE. The two most-contrasting workflow families are clickable end-to-end from the
frozen org spine, and the real "this is actually a bug, not a feature" morph lands between them —
SC-003 proven for real, SC-005's feature-vs-debug contrast obvious at a glance.

- **3.1** feature backbone (stage-navigator canvas, PRF1 work_stream from ORG.agents, PRF2 per-goal
  chat, E1 raster); **3.2** execution drill-in (RunNode/IterationPanel/ExecPanel, morph-safe close);
  **3.3** debug-loop canvas (InvestigationLedger, E2 ledger, E3 red→green). All Done + verified.
- **3.4 — the real morph (this close):**
  - **Sixth anchor claimed:** `vt-evidence-strip` lives on the `.evidence-zone` wrapper (the `.body`
    second zone), present in BOTH the feature and morphed renders, so it GLIDES while its EvidenceBlock
    content crossfades (E1 strip ⇄ E2 seed). Uniqueness holds: exactly one element carries the name per
    snapshot; `#/kit` renders bare components and never the zone wrapper. Anchor set is now **6×1**.
  - **Morph data path:** the morph stays on CAST-412 (header/crumb/chat/nudge persist — same goal, new
    shape). When the feature goal is viewed in the debug family, the spine + work stream + evidence read
    `goals['CAST-412'].morph_view` (loop band, iter 1/3, the coupon-apply symptom + first hypotheses,
    the E2 seed) — NOT the real debug goal. Two pure helpers (`deriveMorphSpine`, `deriveMorphInvestigation`)
    build the projection; the real debug goal (CAST-431) and the feature default are unchanged.
  - **Undo = one atom, one receipt (Decision 9):** the forward morph drops the receipt derived from
    `DEC-CAST-412-03` (once, idempotent); the scripted reverse emits NO second receipt and restores the
    feature canvas exactly (stageFocus, pinned, chat intact). `morph()` also force-clears `drill` so the
    exec tree DOM never joins a morph snapshot (morph-safe).
  - **Flow stitch:** `SCRIPTS.feature` now runs open → navigator → promote → evidence → HOW → collapse →
    **morph → reverse → L3 → close**, all via `advance()` + the locked `startViewTransition` path
    (`--morph-duration:350ms`, `--ease-morph`; reduced-motion → 180ms fade). The L3 beat sits AFTER the
    reverse (the flow ends in the feature world, where CAST-417 lives). Reload resets. PRF2 holds across
    the morph. The morph fires ONLY from the scripted user line (never unprompted).
  - **Data:** the only ORG change was an additive `statement` on `morph_view.evidence.E2-seed.hypotheses[0]`
    (via `generate-org.mjs`; gate green, F4: that single line is the only diff) so the LOCKED EvidenceBlock
    E2 renders cleanly on the morphed canvas. No `org.js` hand-edit. No Phase-1 placeholder morph / spine
    data remained to delete (superseded by spine reads in 3.1; placeholder vocabulary lives only in the
    `#/kit` FIXTURES, the sanctioned C4 exception).
- **Verification (static / no-tests, full-autonomy no-browser gate):** `node --check` PASS; C2 (no
  fetch/local imports) PASS; vt- anchors 6×1; `.evidence-zone` mounted at exactly one call-site, absent
  from `#/kit`; drift grep clean (every canonical-token hit is in `data/org.js` or comments or the
  `#/kit`/FIXTURES allowlist — zero new hardcoded tokens in rendered strings); 21/21 pure-logic morph
  assertions pass (forward = 1 receipt + idempotent, reverse = 0 second receipt, morph spine = loop/iter
  1/3, morph investigation = 1 live pass / 3 resolved experiments / E2 seed with statement).
- **Morph gate (Phase-1 5-item re-run, real DOM):** (1) anchors glide — PASS-PROVISIONAL (6 persistent
  anchors, `::view-transition-group(*)` 350ms register; eyeball CF); (2) no flash/jump — PASS-PROVISIONAL
  (synchronous paint inside startViewTransition; exec panel closed; light E2 content; eyeball CF); (3)
  runs from `file://` — **PASS** (static, hard); (4) ~350ms revealed layout, not spectacle —
  PASS-PROVISIONAL (locked tokens, reused path; eyeball CF); (5) reduced-motion — PASS-PROVISIONAL (fade
  branch + CSS guard verified in code; eyeball CF). No panel-swap contingency was needed (real-DOM
  View-Transition path retained); had jank appeared the pre-approved keyed CSS panel-swap was on standby.
- **Slop gate (4 surfaces: feature · debug · drill-in open · morphed):** external checkers
  (`/cast-preso-check-visual`, `/cast-preso-check-tone`) are NOT in this runner's allowlist → best-effort
  STATIC self-assessment per full-autonomy. not-generic / not-ai-aesthetic: PASS-PROVISIONAL on all four
  (the morphed surface reuses the aesthetic-locked InvestigationLedger + E2 block + tokens). Tone: the NEW
  morph narration is em-dash-free and GPT-ism-free; the surrounding 3.1/3.3 narration retains em-dashes
  (CF3) — a single de-em-dash copy pass across all narration is the standing carry-forward.
- **Human-eyeball carry-forwards (browser unavailable — never block):** re-run both slop checkers on a real
  1440px Chrome screenshot of the 4 surfaces to upgrade provisional → rendered; eyeball the morph for
  glide-vs-crossfade, no-flash, ~350ms feel, and the reduced-motion fade; CF3 de-em-dash copy pass.

## Phase 4 — Decision Summary (sub-phase 4.4 close: Four-Family Stitch, Slop Gate & Drift Sweep)

Phase 4 is COMPLETE. The two remaining workflow families are clickable end-to-end from the frozen org
spine, closing **SC-001 (all four families walkable from disk)** and **SC-005 (four-spine glance
contrast)**. `SCRIPTS = {feature, debug, spike, data}` is complete and CLOSED (Reconciliation F2).

- **4.1** spike canvas (timebox meter + 4 substeps + L2-extension chip, `memo` surface, E4 verdict with
  bidirectional `spike_ref`) + the single generator batch for BOTH goals (thin `execution`×2, `parity`,
  `resolved_view`); **4.2** data canvas (pipeline navigator, `notebook` native-`<details>` cells, E5
  inline-`<svg>` report, the one script-wired L3 resolution); **4.3** FR-017 three-access-tiers parity
  moment (ink-dark terminal + light memo + chat rail, same E4 card both panes). All Done + verified.
- **4.4 — stitch + gates + drift (this close), verified on a LIVE browser (`http://127.0.0.1:8799`):**
  - **Stitch:** `scriptKey` is set per-goal by family on every route (`syncGoalFromRoute`): CAST-412→feature,
    CAST-431→debug, CAST-452→spike, CAST-461→data — confirmed in ORG and at runtime. No scaffolding flags
    remained. **Phase-3 morph demo untouched:** walked CAST-412 start-to-finish live — feature → forward
    morph → debug → reverse morph → feature, family correctly restored, console clean. vt- anchors **6×1**
    (static grep + the morph round-trip exercises them; parity layout adds zero, per 4.3).
  - **Live four-script walk (SC-001):** all four routes walked beat-by-beat via `advance()`, **console clean
    (zero errors/warnings) throughout.** Spike parity beat: split mounts, both `.ev--e4` cards carry the
    identical id `E4-CAST-452`, terminal + memo + chat = three tiers, clean single-beat exit. Data L3 beat:
    `dataResolved` flips, the E5 headline re-renders to `resolved_view` (grouped inline-`<svg>`, muted-ink
    finance-DB vs raspberry billing-export, table + Δ + reconciliation note), one receipt carries
    `DEC-CAST-461-03`, ORG unmutated (options stay `chosen:false`, reload resets). E5 is inline `<svg>`,
    never `<img>`. **L3 budget audit:** exactly one rendered needs-you chip per flow (4/4), one L3 atom per
    goal in ORG — no stray chips.
  - **Extended drift grep** (`CAST-452 · CAST-461 · 180ms · 200ms · 1h40m · 8% · finance DB · billing
    export`) across `prototype/`: every token hit is in `data/org.js` / `data/_build/`. The only `index.html`
    hits are non-data: `180ms` = the reduced-motion / `parity-fade` CSS duration (coincidental numeric
    match, not the verdict figure); `1h40m` = a `tbMinutes` parser-format comment; `8%` = a substring of
    skeleton-bar widths (`88%`/`68%`). CLEAN — no stray literal to move; generator untouched.
  - **Slop gate (live screenshots; external `/cast-preso-check-visual` + `/cast-preso-check-tone` NOT in
    this runner's allowlist → rigorous self-assessment against the REAL rendered surfaces):** visual
    not-generic / not-ai-aesthetic **PASS** on all four (spike canvas, data canvas, parity moment, E5
    reconciled) — locked tokens, consistent kit, real domain data, distinctive layouts. Tone (FR-018)
    **PASS with CF3** — no GPT-isms / hedging / formulaic patterns; the verdict + L3-title data use hyphens;
    em-dashes survive in narration + 3 new data strings (`parity.caption`, `parity.transcript[4]`,
    `resolved_view.reconciliation_note`) → folded into the **CF3 standing carry-forward** (one unified
    de-em-dash pass; piecemeal edits to the frozen `org.js` rejected — out of 4.4 stitch scope and voice-
    inconsistent).
  - **Ink-dark parity terminal (Decision 7):** the slop gate AFFIRMED it as the sanctioned, contained
    identity exception (reads as deliberate, not generic-AI) — NO paper-light fallback was needed.
  - **Observation (non-blocking):** the spike needs-you chip reads "CAST-412" because the spike L3
    (`DEC-CAST-452-03`) carries authored `influenced: ["CAST-412"]` and `NeedsYouChip` renders the first
    influenced ticket. Authored-data semantics (the vendor-SDK call influences the checkout feature), within
    the L3 budget, not a drift literal → left as-is (org.js is frozen; not 4.4's to rewrite).
  - **Phase-5 courtesy:** no Phase-5 banner sections present in `index.html` yet → zero collision; Phase 4
    owns its two goal canvases + the parity section + the 4.1 generator batch only.
- **Carry-forwards (non-blocking):** CF3 unified de-em-dash copy pass across ALL narration + the 3 Phase-4
  data strings; a human eyeball on the parity reveal motion (`parity-fade 180ms`, ≤200ms reduced-motion
  guard verified in CSS) and the 4-up glance composite (live-verified that the four spine shapes —
  segment bar / loop band + ↺ / timebox meter / pipeline DAG — are distinct; the committed composite PNG
  was deferred per owner direction, the plan's sanctioned "verified or carry-forward" path).
