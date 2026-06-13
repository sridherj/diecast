# Shared Context: Product Revamp Diecast — Phase 5 (Colleague Surfaces)

> Read this file at the start of **every** sub-phase session, then execute that sub-phase's
> `plan.md`. The binding constraints below are not optional — they are reconciled cross-phase
> contracts. Violating one is a defect, not a judgment call.

## Source Documents
- **Plan (the source of this split):**
  `docs/plan/2026-06-11-product-revamp-diecast-phase5-colleague-surfaces.md`
- **Decisions / run config / cumulative cross-phase contracts:**
  `docs/plan/product-revamp-diecast-decisions-so-far.md`
  (Run Configuration; Owner-Locked Inputs; the Phase 4 close record + decision block)
- **Cross-phase reconciliation (F1–F5; F2 script-set, F3/F4 bind the generator batch):**
  `docs/plan/2026-06-12-product-revamp-diecast-reconciliation.md`
- **Canonical stage vocabulary (THE single source — never re-derive):**
  `docs/plan/product-revamp-diecast-stage-models.md`
- **Borderline-call log (append here if a flagged-but-taken taste call ships):**
  `docs/plan/product-revamp-diecast-borderline-calls.md`

## Project Background

Phase 5 makes the two colleague theses — **"humans + agents on one board"** and **"Hire. Don't
install."** — experienceable as real, clickable DOM, plus the **US7 requirements-doc loop**. It is
the largest re-authoring chunk in the prototype: the preso `a08`–`a13` designs are lifted as
**visual spec only** and rebuilt as navigable HTML (the assignee filter actually filters; the
board → ticket → decision → escalation arc is four connected frames of one story). Because Phases
2a/2b already shipped the data spine and the component kit, almost every surface here is a **thin
data slice**: the board is `ORG.board` through `ColleagueCard`, the trail is `ORG.decisions`
through the `Decision` ladder, the hiring report is `ORG.hiring` through a leaderboard + one
radar-SVG helper.

The phase splits into **three independent sub-streams** —
**5a** board / decisions / autonomy · **5b** hiring / marketplace / ops / Layer-2 · **5c** reqs-doc
loop — bracketed by a thin **shared-rails** sub-phase (**5.0**) and a **stitch-and-gates** sub-phase
(**5.4**), mirroring Phase 4's executed `5.0 → (5a ∥ 5b ∥ 5c) → 5.4` shape.

The exploration's build-cost insight governs everything: each surface is a **projection of `ORG`
through the existing `render(appState)`** — the marginal cost of a surface is data plus a thin
renderer. The canvas grammar, component kit, evidence conventions, scripted-flow pattern, and
stage-navigator behavior were all settled in Phases 1–4. Phase 5's net-new work is ten new routes
rendered as thin data slices, the `DigestNotice` atom, two inline-SVG helpers (`RadarChart`,
`Sparkline`), the autonomy-dial **wiring**, and one additive flow script (`SCRIPTS.hiring`).

**Operating mode: HOLD SCOPE.** Plan exactly what the high-level Phase 5 section bounds (US5, US6,
US7, US8, US9, US10), at high practical detail. One playbook extra (PB-05 Step 7's "should've
asked" correction loop) is **excluded** as out-of-section scope (Decision 7). No new families, no
new ops, no entry-screen routing or asset inlining (Phase 6).

**FULL AUTONOMY MODE (owner-approved, end-to-end through Phase 6):** never ask the user questions,
never pause for approval gates, never go idle waiting for input. At every decision gate pick the
recommended option and document it. **Propagate this directive verbatim to any child agent you
dispatch** (the slop-gate visual/tone checkers in 5.4).

**No-browser static-verification posture (project-wide, autonomous runs):** autonomous runner
sessions **cannot connect a live browser** (the Claude-in-Chrome extension is not connected — same
as every prior phase). Therefore every "Verification (manual click-through)" item is satisfied by
the strongest **static** evidence available (`node --check` of the extracted module, grep audits,
pure-logic assertion harnesses in `/tmp` that are never committed) **plus** a recorded
**human-eyeball carry-forward** for any item that genuinely needs rendered pixels (glance tests,
chart legibility, motion feel, slop-gate-on-screenshot). Carry-forwards are **non-blocking** — they
never stop the phase; they are logged for a later human pass. This posture is the inherited Phase
1/2a/2b/3/4 precedent, not a Phase 5 invention. (Phase 4's 4.3/4.4 reached a live browser when the
extension happened to be connected; treat a live browser as a bonus, never a precondition.)

## BINDING CONSTRAINTS (carried into every sub-phase; each is a defect if violated)

1. **NO TESTS anywhere.** No test files, suites, harness, or CI in any sub-phase. All verification
   is **manual click-through / static observation only** — open `prototype/index.html` from disk,
   click, observe. Fake test-result *content* rendered as prototype data is fine (the ticket's
   maker-checker findings, the hiring eval scores are data, not tests). **No review pass may flag
   "missing tests" as a finding.**
2. **`file://` legality — ONE inline file.** Everything ships in the single `prototype/index.html`
   (inline `<style>` + inline module). `file://` blocks `fetch()` and **local ES-module imports**.
   Allowed: **https CDN** imports via the import-map, classic `<script src>` (how `org.js` loads),
   and **relative `<img src>`** (assets under `prototype/assets/`). Collapsible disclosure (reqs-doc
   L2/L3, monitoring/provenance) uses **native `<details>`** (`file://`-safe, no JS dependency).
3. **ORG data is FROZEN (2a FREEZE).** All data extensions MUST go through the seeded generator
   `prototype/data/_build/generate-org.mjs`, which re-runs its invariant gate and **refuses to emit
   on violation**. **NEVER hand-edit `prototype/data/org.js`.** Only additive keys; `git diff` must
   show additions only. **The Phase 5 generator batch has a single owner: sub-phase 5.0.** 5a/5b/5c
   never touch `generate-org.mjs`.
4. **Section-stability invariant (Reconciliation F4).** All ORG sections **outside** the batch's
   declared additions must be **byte-identical** before/after regeneration. **CAST-452 / CAST-461
   sections (Phase 4 ownership) must stay byte-identical** — the parallel-phase guard is a generator
   invariant. After regenerating, diff `org.js` and confirm nothing outside the declared additions
   changed.
5. **Generator serialization (Reconciliation F3).** Phase **4.1's** generator batch commits `org.js`
   **before** Phase 5.0's batch (already done — Phase 4 is complete in the working tree). 5.0's batch
   is therefore additive on top of the committed Phase-4 `org.js`; the 4∥5 parallelism is resolved by
   this serialization, so 5.0 simply layers its keys.
6. **2c stage vocabulary is canonical and already in `org.js`** (`placeholder: false`). The Layer-2
   chain pipeline (5b) reuses the existing `StageSpine` `pipeline` shape and reads its stage labels
   from ORG — **any hardcoded stage vocabulary in `index.html` is a defect**.
7. **Closed 5-op vocabulary stays closed** (`morph · nudge · promote · drillInto · pin`). **UI state
   is NOT an op:** the board assignee filter, the trail filter chips, the autonomy dial toggle, the
   reqs-doc disclosure/comment/delta toggles, and the hiring-wizard Next buttons are **plain click
   handlers mutating additive `appState` keys + re-render** — NOT ops (Phase 3's precedent of not
   minting ops for UI state). `SCRIPTS.hiring` patches state directly via the scenario engine; it
   mints **no** op. **No sixth op anywhere in this phase.**
8. **vt- anchors live on shell zone wrappers, NEVER on kit components.** The anchor set is **6×1**
   after Phase 3 (`vt-goal-header · vt-chat-rail · vt-nudge-card · vt-receipt-trail · vt-nav-rail ·
   vt-evidence-strip`). A duplicate `view-transition-name` **silently kills all transitions**. The
   ten new routes introduce **no** element carrying any vt- name — they reuse the existing shell zone
   wrappers (DevTools count unchanged).
9. **L3 budget: exactly one hard stop per flow.** This phase **adds zero new L3 atoms** — the 2a data
   invariant already enforces exactly one L3 per flow. The **CAST-417 escalation rail stays an
   unresolved stop** (options pre-framed but inert — the stop is *shown*, not resolved; Phase 4 locked
   the data-flow L3 as the ONE wired rail resolution prototype-wide). The autonomy dial's promotion of
   the `dial_demo` L2 atom into a stop-and-confirm card is a **scripted presentation illusion** (no
   receipt written, ORG never mutated, reload resets) — not a real L3 resolution.
10. **Failure policy:** retry a failed sub-phase **once** with refined instructions. Second failure
    **off** the critical path → log a gap and continue. Second failure **on** the critical path
    (5.0 → 5b → 5.4) → **stop and report**.

## Codebase Conventions

- **Single-file prototype:** `prototype/index.html` — inline `<style>` + inline `<script type=module>`,
  `render(appState) → DOM` (pure render), htm + preact-style components via https CDN import-map.
- **Banner sections:** partition `index.html` by banner-comment sections (the 2b/3/4 precedent) so the
  growing single file stays navigable and parallel work stays disjoint. Phase 5 owns new sections for
  the board arc (5a), the hiring/marketplace/ops/Layer-2 surfaces (5b), and the reqs-doc (5c). **Do
  NOT touch the CAST-452/CAST-461 canvas sections or the parity section (Phase 4 ownership).**
- **CSS prefixes (greppable, per-surface):** `board-*` / `ticket-*` / `dec-*` (5a) · `hire-*` /
  `mkt-*` / `ops-*` / `l2-*` (5b) · `reqs-*` (5c). Follows the Phase 3/4 per-surface prefix convention.
- **Component naming:** PascalCase — `StageSpine`, `StageSurface`, `EvidenceBlock`, `EscalationRail`,
  `ColleagueCard`, `Decision`, `NudgeCard`, `GuideMark`, `RunNode`, `IterationPanel`, `AutonomyDial`,
  and the Phase 5 net-new `DigestNotice`, `RadarChart`, `Sparkline`.
- **vt- anchors live on shell zone wrappers, NEVER on kit components.**
- **Org-data key convention:** lower_snake_case (e.g. `requirements_doc`, `resolved_view`,
  `dial_demo`, `version_history`).

## Key File Paths

| File | Role |
|------|------|
| `prototype/index.html` | THE single-file prototype — all five sub-phases edit it (see manifest for parallelism + the file-collision note) |
| `prototype/data/org.js` | Frozen `window.ORG` (classic script). **Generated — never hand-edit.** |
| `prototype/data/_build/generate-org.mjs` | The seeded generator + invariant gate; the ONLY sanctioned path to extend ORG. **Single owner this phase = 5.0.** |
| `prototype/assets/` | Raster assets, loaded via relative `<img src>` + `onerror` fallback (no new rasters expected — `RadarChart`/`Sparkline` are inline SVG, not rasters) |
| `docs/plan/product-revamp-diecast-stage-models.md` | Canonical stage vocabulary — the Layer-2 chain pipeline reads from ORG, never hardcodes these |

## Contracts This Phase Exports (Phase 6 consumes these)

- **Route table (final for the prototype, all hash-only):** `#/board` (real, replaces the Phase 1
  stub) · `#/ticket/CAST-412` · `#/decision/:atomId` · `#/decisions/CAST-412` · `#/hire` ·
  `#/marketplace` · `#/agent/:slug` · `#/skills/new` · `#/layer2` · `#/reqs/CAST-412`.
- **appState additive keys (v1 keys untouched):**
  `boardFilter:'any'|'human'|'agent'|'checker'` ·
  `hiring:{step:1..5, expanded:null|candidateId, compare:false}` ·
  `autonomyLevel:'conservative'|'balanced'|'autonomous'` ·
  `reqsDoc:{openComment:null|commentId, deltaView:false}`.
- **`SCRIPTS.hiring`** (additive script key, ~6 beats) — chat-initiated hiring side-arc. After Phase
  5, `SCRIPTS = {feature, debug, spike, data, hiring}`; the four-**family** set stays closed (F2) —
  `hiring` is a demo-arc key, not a family.
- **`DigestNotice` component** — the one inform-without-nagging atom, instantiated for the L2
  decision digest (5a) AND the US7 write-back notice (5c). **Exactly one `DigestNotice` definition in
  source** (PB-05 hand-off #3).
- **Inline-SVG helpers:** `RadarChart` (per-dimension candidate eval; also the resume benchmark) and
  `Sparkline` (monitoring compliance trend) — both data-driven from ORG, the Phase 4 E5/M9 idiom
  (hand-authored `<svg>`, real `<text>` labels, `<title>`/`<desc>`, existing tokens only, never
  rasters).
- **ORG additive extensions** (via the 5.0 generator batch): `goals['CAST-412'].requirements_doc`,
  `agents[].versions/monitoring`, `org.skills`, `dial_demo` atom marker (full schema in 5.0).
- Drift-grep additions and the slop-gate surface list for Phase 6's full re-run.

## Data Schemas & Contracts (copy verbatim into ORG via the generator — 5.0 owns this)

**ORG additive extension this phase authors — ONE generator batch, owned by 5.0 (plan contract):**
```js
// (a) requirements doc — CAST-412 only, the US7 substrate
goals['CAST-412'].requirements_doc = {
  classification: 'feature',
  version: 'v2',
  version_history: [ { v:'v1', date }, { v:'v2', date, summary } ],
  elements: [ { id:'req-NN', level:1|2|3, kind:'intent'|'story'|'fr'|'constraint',
                text, children:[ids], decision_refs:[atomIds] } ],
  comments: [ { id, anchor:'req-NN', author_id, author_role:'pm'|'eng',
                state:'open'|'resolved', thread:[{who, text, time}] } ],   // EXACTLY ONE, one pm author
  delta: [ { anchor:'req-NN', change, origin_phase:'planning' } ],
  writeback: { origin_phase:'planning', summary, anchors:['req-NN'] }
}

// (b) agent-ops fields — on agents[]
agents[].versions   = [ { sha7, date, note } ]                 // ≥1 each; 4–5 on crud-orchestrator, 1–2 elsewhere
agents[].monitoring = { trend:[12 floats], cost_p50_usd, latency_p50_s,
                        recent_runs:[ { id, when, status } ] } // full depth on crud-orchestrator, thin elsewhere

// (c) org skills — nested under the frozen `org` key
org.skills = [ { slug, title, visibility:'private'|'company', owner, created, blurb } ]
             // 3 company-wide + the pre-staged demo skill `cast-export-csv` (private)

// (d) dial-demo marker — on exactly one CAST-412 L2 atom (the planning-phase "split FR-014"-style atom)
dial_demo: true
```

**New generator invariants** (generator refuses to emit on violation): exactly one `dial_demo` atom
org-wide and it is **L2**; `requirements_doc` element ids unique; every comment/delta/writeback anchor
resolves to an element; **exactly one** comment author has role `pm`; every agent has **≥1** version;
skill slugs are lowercase `cast-*`; **CAST-452/CAST-461 sections byte-identical to the Phase 4 batch**
(parallel-phase guard). Regenerate → gate green → `git diff` additive-only → F4 holds.

**Canonical data facts (single source — never re-typed in `index.html`):**
- CAST-412 = `"Add RBAC to checkout"`; **CAST-417 (roles-column drop) is THE single feature L3** atom.
- One superseded L1 pair: **GraphQL → REST** (renders struck-through with a "superseded by →" link).
- Marketplace cred line (crud-orchestrator): **99.9% compliant · 505 runs · 2 loops** — identical
  digits on its resume; **all credibility numbers derive from the same `agent.stats` fields** (single
  source — no second copy).
- Autonomy-dial earned-trust tooltip = feature-roster **aggregate 99.4% · 312 runs** from `agent.stats`.
- Hiring: **6 candidates**, **5 dimensions**, produced-work artifact stubs.
- Layer-2: **12 contracts** (8 chain-aligned + 4 cross-cutting); **8-agent chain**; **6-project**
  portfolio.

**Components consumed AS-IS (Phase 2b/3 — pure props, never modified here):** `ColleagueCard {agent,
density}` (card + line densities) · `Decision {atom, layer}` ladder (`pill`/`callout`/`row` layers,
atom field names verbatim) · `EscalationRail` (ranked structural weight 7A, nothing pre-selected) ·
`AutonomyDial {value, trust}` (shipped static in 2b — **this phase wires the toggle**) · `GuideMark` +
Guide voice · `IterationPanel` (Phase 3 — reused verbatim as the ticket activity log) ·
`StageSpine {spine}` (the `pipeline` shape for the Layer-2 chain). **Avatar grammar:** human = circle ·
maker = square `--maker` outline · checker = square `--checker` fill · Guide = diamond. **L-badges:**
L1 = `--ink-35`, L2 = `--warn`, L3 = `--rasp`; confidence glyphs ●/◐/○. **vt- anchors NEVER on kit
components.**

**Scenario engine (Phase 1, unchanged API):** `{narration, patch, transition?}` steps + `advance()`,
index at `appState.chat.scriptIndex`, keyed by `appState.chat.scriptKey` (the Phase 3 per-goal
contract). Phase 5 adds `SCRIPTS.hiring` (~6 beats) — additive per F2; the four-**family** set stays
closed.

## Pre-Existing Decisions (from the plan's Decisions Made Autonomously + Run Config)

- **Plan review: SKIPPED** per the owner-approved run config (cross-phase reconciliation only;
  Phase 1/2a/2b/2c/3/4 precedent). This split therefore does **not** dispatch `/cast-plan-review`, and
  inserts **no** plan-review or reconciliation sub-phases (NO REVIEWS).
- **NO human-checkpoint gates** in any sub-phase file (FULL AUTONOMY). There are **no decision gates**
  in this phase.
- Sub-phase split `5.0 → (5a ∥ 5b ∥ 5c) → 5.4` (Decision 1); one generator batch owned by 5.0;
  CAST-417's escalation rail stays an unresolved stop (Decision 3); the `AutonomyDial` lives on
  `#/decisions/CAST-412`'s trail header, not the Phase 3 goal canvas (Decision 4); `SCRIPTS.hiring`
  added additively (Decision 5); one route `#/decision/:atomId` serves both decision-artifact and
  escalation frames, branching on status/level (Decision 6); PB-05 Step 7 excluded (Decision 7); a
  minimal L2 digest strip is included in 5a so the dial has a quiet state to promote *from* (Decision
  8); `org.skills` nests under the frozen `org` key (Decision 9); agent ops fold into `#/agent/:slug`
  as tabs (Decision 10); PB-04's stale Invoice-CRUD/avatar grammar treated as superseded (Decision 11);
  marketplace = the unified discover-and-hire browser (Decision 12); federation uses static staggered
  states, no timers (Decision 13); `RadarChart`/`Sparkline` are data-driven inline SVG (Decision 14);
  skillification's terminal snippet reuses Phase 4's parity-pane ink-dark treatment (Decision 15);
  effort stated honestly at ~4.75–5.75 sessions (Decision 16); slop-gate surface list = six (Decision
  17).

## Relevant Specs

`docs/specs/_registry.md` — all existing specs govern the **cast-server runtime**. Per **FR-020 the
prototype is greenfield**: no spec applies, none is contradicted, and **no `/cast-update-spec` action**
is in scope for this phase. The FR-017/US7 surfaces *depict* the real product's concepts as **fake
prototype data**, not spec'd surfaces being modified. **No specs cover files in this plan.**

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|-----------|------|-----------|--------|-------------------|
| 5.0 Shared Rails (`sp5_0_shared_rails`) | Sub-phase | Phases 1, 2a, 2b, 3, 4 done | 5a, 5b, 5c (all) | None (the gate) |
| 5a Board Arc, Trail & Dial (`sp5a_board_arc`) | Sub-phase | **5.0**; Phase 3 (`IterationPanel`) | 5.4 | **5b, 5c** (disjoint routes/prefixes) |
| 5b Hiring / Marketplace / Ops / Layer-2 (`sp5b_hiring_marketplace`) | Sub-phase | **5.0** | 5.4 | **5a, 5c** (disjoint routes/prefixes) |
| 5c Requirements-Doc Loop (`sp5c_reqs_doc`) | Sub-phase | **5.0** | 5.4 | **5a, 5b** (disjoint routes/prefixes) |
| 5.4 Stitch, Slop Gate & Drift Sweep (`sp5_4_stitch_gates`) | Sub-phase | **5a + 5b + 5c** | — | None |

> **Critical path: 5.0 → 5b → 5.4.** 5b is the widest sub-stream (six surfaces) and the greenfield
> concentration (the hiring-funnel middle has no preso reference). 5a ∥ 5b ∥ 5c are fully parallel
> after 5.0 — separate routes, separate CSS prefixes, shared code only through the 2b kit + 5.0's
> `DigestNotice`/`RadarChart`/`Sparkline`.
>
> **File-collision honesty note (mirrors the Phase 3/4 splits):** the plan calls 5a/5b/5c "fully
> parallel" via disjoint routes + CSS prefixes, and the manifest models them as one parallel batch
> (`--max-batch-size 3`, exactly the three members) per the mandated DAG. But all three edit the
> **same single file** `prototype/index.html`, and there is **no merge mechanism** between independent
> `cast-subphase-runner` agents. If the orchestrator dispatches 5a/5b/5c as concurrent independent
> runners, **serialize their `index.html` writes** (each appends its own disjoint banner section; land
> them in sequence) or run them in one session. The generator is single-owned by 5.0 regardless, so
> the `org.js` write is never concurrent. The logical parallelism (disjoint zones, independent data
> slices) is real; the physical serialization is a single-file artifact constraint, not a plan change.
