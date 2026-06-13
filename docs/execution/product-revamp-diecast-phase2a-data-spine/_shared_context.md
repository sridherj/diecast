# Shared Context: Product Revamp Diecast — Phase 2a Data Spine

> Read this file at session start **before** executing any sub-phase. It carries the
> binding constraints, schema contracts, and cross-phase decisions every 2a sub-phase
> must honor.

## Source Documents (READ FIRST, in this order)

1. **`docs/plan/product-revamp-diecast-decisions-so-far.md`** — run configuration,
   owner-locked inputs, the NO-TESTS rule, every cross-phase contract, and the
   Reconciliation Outcome (F1–F5). This is the authoritative cross-phase log; later
   phases adopt its naming/interface choices.
2. **`docs/plan/2026-06-11-product-revamp-diecast-phase2a-data-spine.md`** — the Phase 2a
   detailed plan this execution directory splits. Every sub-phase file below carries the
   relevant slice, but the plan doc is the canonical source for any ambiguity.
3. (Reference) `docs/plan/2026-06-12-product-revamp-diecast-reconciliation.md` — the
   COHESIVE verdict and F1–F5 rules summarized below.

## Project Background

This phase authors the **one coherent fictional org** ("Northwind") that every screen of
the Diecast vision prototype reads from, and freezes it as a single data spine. The
deliverable is `prototype/data/org.js` — a *classic* script setting
`window.ORG = Object.freeze({...})` — generated once by a seeded, build-time-only
`@faker-js/faker` script plus hand-tuned prose, then frozen. The generator is
**self-validating**: it refuses to emit `org.js` if any spine invariant is violated (atom
budgets, exactly one L3 per flow, referential integrity, trust-stat aggregation).

The phase's entire purpose is **drift prevention**: after 2a, canonical tokens (CAST-412,
M04/S03/R02, rework 1/3, L1/L2/L3, crud-orchestrator, "99.9% compliant … across 505 runs")
appear *only* from the spine — never hand-typed in a surface.

## BINDING CONSTRAINTS (apply to every sub-phase — non-negotiable)

### NO TESTS anywhere
This deliverable has **no concept of tests** — no pytest, no unit/integration/e2e suites,
no test harness, no CI, no test files of any kind. All verification is **manual
click-through**: open `prototype/index.html` from disk, click, observe. The single
machine-enforced gate is the **self-validating generator's invariant check**, which runs
*inside* `generate-org.mjs` before it writes the file and refuses to emit on violation.
That gate is **NOT a test file** — do not extract it into a standalone validator or suite.
No reviewer or runner may flag "missing tests" as a finding. (Fake test-result *content*
inside the prototype UI — E1's "47 passed / 0 failed", E3's red→green repro — is data, not
tests, and stays.)

### `file://` legality (HARD — Phase 1 contract)
The prototype opens from disk (`file://`). That blocks **`fetch()`** and **local
ES-module imports**. Therefore:
- Org data ships as a **classic script** `prototype/data/org.js` setting
  `window.ORG = Object.freeze({...})`. **Never** `fetch('org.json')`, never
  `import` from a local path.
- Only **https CDN import-map imports**, classic `<script src="...">`, and relative
  `<img src>` are legal from disk.
- `<script src="data/org.js"></script>` is added to `index.html` **before** the inline
  `<script type="module">` (so `window.ORG` exists when the module runs).

### Prototype code root & Phase 1 baseline
- Prototype code root: **`/home/sridherj/workspace/diecast/prototype/`**.
- **Phase 1 is BUILT**: `prototype/index.html` exists (~33KB) with appState v1, the 5-op
  dispatcher, the ~50-line scenario engine, and the View-Transitions morph — the morph gate
  **PASSED** (static analysis, item 4 provisional pending human eyeball).
- Extend Phase 1 **additively**. **Never regress** a Phase 1 contract: appState v1 keys may
  be added to but never renamed; the op vocabulary stays closed at 5; vt- anchors stay on
  shell zones.

### F4 rule — single source of `org.js`
The **generator gate is the single source of `org.js`**. `org.js` is generated, never
hand-edited (it carries a GENERATED header). Later phases (3, 4, 5, and 2c's stageModels
rewrite) **extend it additively only**, by editing the generator's constants and
regenerating — which re-runs the invariant gate at that moment. All ORG sections outside a
batch's declared additions must be byte-identical before/after (F4 section-stability rule).

## Reconciliation Outcome (F1–F5) relevant to 2a

- **F1 (HIGH):** the `org.js` `stageModels` rewrite is owned by **2c**, executed via 2a's
  generator, scheduled **after 2a.1 (generator exists) and before Phase 3 dispatch**. 2a
  ships `stageModels` with `placeholder: true` content; Phase 3 must never build on
  placeholder vocabulary. The `stageModels` region is the **one standing exception** to the
  freeze policy.
- **F4 (execution rule):** Phase 3/4 generator batches adopt the section-stability
  invariant (above).
- F2, F3, F5 govern later phases (SCRIPTS closure, generator-batch serialization, schedule)
  — listed for traceability, not 2a-blocking.

## Codebase Conventions

- **Naming (deliberately mixed, documented in the schema comment):**
  - Decision atoms use **snake_case** playbook-05 ADR field names verbatim
    (`reversibility · options_considered · revisit_if · originating_agent ·
    supersedes/superseded_by · spike_ref · influenced[]`). Locked by playbook 05 + 2b.
  - Agent records use **camelCase** stat fields (`compliancePct`). Locked by 2b's
    component-prop idiom.
  - Everything else: kebab-case slugs, `DEC-<goal>-NN` atom ids, `CAST-4xx` ticket ids,
    `<family>-NN` step ids (`feat-01`, `dbg-01`, `spk-01`, `data-01`).
- **Determinism:** `faker.seed(42)`; canonical values are hardcoded constants at the top of
  the generator (never faker output — faker supplies only structured filler: portfolio
  names, commit SHAs, relative timestamps, candidate latency numbers). All timestamps derive
  from a fixed fictional demo timeline (one working day, `2026-06-11T09:00Z`–`18:00Z`,
  matching Phase 1's `17:52` receipt) — never `Date.now()`.

## Key File Paths

| File | Role |
|------|------|
| `prototype/index.html` | Phase 1 app (BUILT). 2a.3 adds one `<script src>` line + spine reads. |
| `prototype/data/org.js` | **THE deliverable** — classic script, `window.ORG = Object.freeze({...})`. Generated, committed, never hand-edited. |
| `prototype/data/_build/package.json` | Pins `@faker-js/faker` exact version; `node_modules` gitignored. Authoring tooling only — the browser never loads `_build/`. |
| `prototype/data/_build/generate-org.mjs` | Seeded faker + hand-tuned prose constants → SELF-VALIDATES → emits `../org.js`. |
| `docs/plan/product-revamp-diecast-decisions-so-far.md` | Cross-phase decision log; 2a.3 appends the 2a freeze appendix. |

## Data Schemas & Contracts (copy these verbatim into the generator)

### `window.ORG` top-level schema — 11 frozen keys
```js
window.ORG = Object.freeze({
  meta:        { version: '1.0', seed: 42, frozen_at: '…', owner_notes: '…' },
  org:         { name: 'Northwind', crumb: 'northwind / goals' },
  humans:      [ { id, slug:'@you', kind:'human', initials:'SJ', role:'eng lead', … },
                 { id, slug:'@priya', kind:'human', initials:'PK', role:'PM', … } ], // ONE PM persona (US7)
  guide:       { id, slug:'cast-guide', kind:'guide', name:'the Guide' },            // NOT a marketplace agent
  agents:      { 'crud-orchestrator': { id, slug, kind:'maker'|'checker', pairedWith,
                 stats:{compliancePct, loops, runs}, autonomy, rework:{used,budget},
                 inflight, state, /* 2a superset: */ archetype, health, versions[], usage }, … }, // 12, keyed by slug
  stageModels: { feature:{ placeholder:true, shape, steps:[{id:'feat-01',label,…}] },
                 debug:{…}, spike:{…}, data:{…} },                                    // 2c-OWNED region
  goals:       { 'CAST-412': { family, title, status, spine_state, artifacts[], work_stream[],
                 evidence, nudge:{who,do,why}, decisions[], chain_position,
                 autonomy:{value, trust:{compliancePct, runs}} }, … },                // 4, keyed by goal id
  board:       { columns[], tickets[] },
  decisions:   [ /* 5–8 atoms per goal, playbook-05 ADR schema verbatim */ ],
  hiring:      { request, dimensions[], candidates[], report, onboarding },
  layer2:      { contracts[/*12*/], chain[/*8*/], portfolio[/*6*/] },
});
```

### Decision atom — playbook-05 Step-1 schema VERBATIM
`id` (`DEC-<goal>-NN`) · `goal_slug` · `phase` · `title` · `reversibility` (`L1|L2|L3`) ·
`rationale` · `options_considered[]` · `consequences` · `revisit_if` · `originating_agent` ·
`author_type` · `timestamp` · `status` · `supersedes`/`superseded_by` · `spike_ref` ·
`influenced[]` **plus** a scannable **`diff`** field (e.g. `'classification: feature → bug'`).
Reversals are **new records, never edits**. L3 atoms carry exactly **3** options with
`rank:1|2|3` and `chosen:false` on all three at rest, plus an evidence pack
(`what_i_want`, `what_i_tried`).

### `stageModels.<family>` slot contract (2c-owned; 2a ships placeholder)
`{ shape, progression?, loop?{over,budget}, timebox?{budget}, steps:[{id, label, shortLabel?,
does, surface, surfaceWhy, artifacts[], refs[], evidence:'E1'..'E5'|null}] }`. Family keys
exactly `feature|debug|spike|data`; step ids `<family>-NN`. All four carry
`placeholder:true` (watermarked labels) until 2c.

### Step-id indirection (the 2c hand-off)
Goal artifacts and work-stream items reference stage steps by **step id** (`feat-01`),
never a label string. Per-goal runtime position lives in
`goals[id].spine_state = { current:'<step-id>', iter?:{current,budget}, timebox_used?:'1h40m' }`.
At boot, `appState.spines.<family>` is composed from `stageModels.<family>` (shape + derived
label array via `steps.map(s => s.shortLabel ?? s.label)`) + the active goal's `spine_state`
— preserving Phase 1's appState spine shape exactly.

### appState v1.1 (extends v1; no renames)
`family` now ∈ `'feature'|'debug'|'spike'|'data'`; `spines` gains `spike`+`data` keys (all
four derived from `ORG.stageModels` + `spine_state`); `goal` populated from `ORG.goals[id]`;
new key `org = window.ORG`; `receipts[]` items gain a `decision_id` field (keeping Phase 1's
`{level,label,at,rationale}` shape, now derived from the referenced atom).

### Canonical vocabulary table (single source: `org.js`; grep-enforced)
| Token | Canonical value |
|-------|-----------------|
| Org / crumb | `Northwind` · `northwind / goals` |
| Feature goal | `CAST-412` · "Add RBAC to checkout" |
| Checker rule codes | `M04` (convention drift) · `S03` (typing too permissive) · `R02` (missing index on FK) |
| Rework budget | `1/3 used` |
| Reversibility | `L1 / L2 / L3` (reversibility-keyed only; no decision-weight gloss) |
| Canonical agent | `crud-orchestrator`, paired `crud-compliance-checker` |
| Marketplace cred stat | "99.9% compliant code in 2 maker-checker loops across 505 runs" |
| Dial trust stat | "99.4% compliance across 312 runs" (feature-roster aggregate) |
| PR | `PR #2341` |
| Test summary (E1 data) | `47 passed / 0 failed` |
| 8-agent chain | refine → decompose → research → synthesize → plan → detail → orchestrate → run |
| Archetypes | Maker / Checker / Decision / Spike / Escalation / Mentor |
| Escalation ticket | `CAST-417` — "Migrate roles schema (drops legacy `roles` column)" |

## Pre-Existing Decisions (from the plan doc's "Decisions Made Autonomously")

Key ones that constrain implementation:
- **CAST-412 = "Add RBAC to checkout"** (playbook-04 "Invoice" pick rejected; Phase 1
  already exported RBAC). Invoice activity-log *structure* ported to RBAC entities.
- Goal ids: `CAST-412` feature · `CAST-431` debug · `CAST-452` spike · `CAST-461` data.
- **`CAST-417` (roles-column drop) is THE single feature L3**, shared by board arc + canvas
  beat — encoded **once**, projected twice (one-L3-per-flow budget).
- One **superseded pair** in the feature goal (GraphQL → REST) for the trail's strike-through.
- Cred stats unified via per-agent `stats`; dial trust = authored roster aggregate
  (99.4% / 312 runs), generator-enforced to equal the computed aggregate.
- Roster: 12 agents / 6 archetypes; hiring: 6 candidates / 5 dimensions; Layer-2: 12
  contracts (8 chain-aligned + 4 cross-cutting) / 8-node chain / 6-project portfolio.
- `Object.freeze` is **shallow** (top-level only) — deliberate; protects the contract
  surface without blocking 2c's stageModels rewrite.
- US7 data encoded **thin** (ids, version, classification, comment anchors, notice text);
  Phase 5c owns long-form prose.
- **Plan review skipped** per run config (Phase 1/2b/2c precedent). No `/cast-update-spec` —
  FR-020 greenfield, no spec applies.

## Relevant Specs

No specs cover files in this plan. `docs/specs/_registry.md`'s 7 specs all govern the
**cast-server runtime**; the prototype is greenfield (FR-020). None apply, none contradicted.
No `/cast-update-spec` action for this deliverable.

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|-----------|------|-----------|--------|-------------------|
| sp1 — Schema Lock & Self-Validating Generator (2a.1) | Sub-phase | None (Phase 1 *plan* only) | sp2 | None |
| sp2 — Author the Org (2a.2) | Sub-phase | sp1 | sp3 | None |
| sp3 — Wire, Sweep, Freeze (2a.3) | Sub-phase | sp2 + Phase 1 *execution* | (Phase 3/4/5 consume) | None |

**Strictly sequential** — no parallel group, no decision gates. 2a.2 needs 2a.1's invariant
gate to author against; 2a.3 needs full content to sweep. (All judgment-call gates were
resolved at planning time under full autonomy — see the plan doc's "Decisions Made
Autonomously".)
