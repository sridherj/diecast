# Product Revamp: Diecast — Phase 2a: Fake-Org Data Spine

## Overview

This phase authors the **one coherent fictional org** that every screen of the vision prototype
reads from, and freezes it as a single data spine. The deliverable is
`prototype/data/org.js` — a *classic* script setting `window.ORG = {...}` (the Phase 1
`file://` constraint forbids `fetch('org.json')` and local ES-module imports) — generated once
by a seeded, build-time-only `@faker-js` script plus hand-tuned prose, and then frozen. The
generator is **self-validating**: it refuses to emit `org.js` if any spine invariant is
violated (atom budgets, exactly one L3 per flow, referential integrity), keeping verification
inside the authoring tool per the owner's NO-TESTS rule. The spine carries: the four family
goals (feature / debug / spike / data) with stage models, artifacts, work-streams, and E1–E5
evidence payloads; **5–8 decision atoms per goal with exactly one L3 per flow** (the four
locked demo beats from playbook 05); the agent roster and marketplace (12 agents, 6 archetypes,
maker-checker paired in-card, cred stats); the rbac-agent hiring funnel data (6 candidates with
eval radar + deep links to fake produced work); and the Layer-2 catalogue (12 named contracts,
the 8-agent chain, portfolio). The phase's entire purpose is **drift prevention**: after 2a,
canonical tokens (CAST-412, M04/S03/R02, rework 1/3, L1/L2/L3, crud-orchestrator, "99.9%
compliant … across 505 runs") appear *only* from the spine — never hand-typed in a surface.

## Position in Overall Plan

```
Phase 1 ──►  ►Phase 2a (THIS PLAN)◄  ∥  2b (component kit)  ∥  2c (stage research)  ──► Phase 3 ──► 4 ∥ 5 ──► 6
             frozen org spine            fixtures swap to        rewrites stageModels
             every screen reads it       the spine when 2a       region with derived
                                         lands                   vocabulary
```

Phase 2a depends on Phase 1 (appState shape + packaging contract) and runs **parallel with 2b
and 2c** — both of which have now also planned and exported contracts this plan adopts
(decisions-so-far, 2026-06-11):

- **2b** builds component fixtures using canonical vocabulary "so 2a wiring is a data swap."
  → 2a's `agents` records must be **supersets of 2b's agent fixture shape**
  (`{id, slug, kind, pairedWith, stats:{compliancePct, loops, runs}, autonomy,
  rework:{used,budget}, inflight, state}`), and the decision atom must keep playbook-05 field
  names verbatim (2b locked the same).
- **2c** locked the **`stageModels` org-data slot contract** that 2a MUST reserve:
  `stageModels.<family> = { shape, progression?, loop?{over,budget}, timebox?{budget},
  steps: [{id, label, shortLabel?, does, surface, surfaceWhy, artifacts[], refs[],
  evidence}] }`, family keys exactly `feature|debug|spike|data`, step ids `<family>-NN`
  (`feat-01`, `dbg-01`, `spk-01`, `data-01`). 2a ships this slot with **placeholder content**;
  2c rewrites it once with the derived vocabulary.

Phase 2a is **not** on the critical path (1 → 2b → 3 → 5 → 6), but Phase 3, 4, and 5 all
consume it — slipping it past 2b's finish would stall Phase 3.

## Operating Mode

**HOLD SCOPE** — the delegation instruction is explicit ("plan exactly what the high-level plan
section says for this phase"). The high-level plan bounds 2a to five activities: author + freeze
the org structure; encode the four family goals; encode decision atoms; encode marketplace +
hiring candidates; encode Layer-2 data. No components, no canvases, no scenario scripts, no new
routes — those are 2b/3/4/5. Rigor goes into schema discipline, referential integrity, and the
drift-prevention verification. Per the owner's **NO TESTS** rule, there are no test files or
suites anywhere in this plan; verification is manual click-through plus the self-checking
authoring tool.

## Depends On (from prior plans)

Consumed from `product-revamp-diecast-decisions-so-far.md` (Phase 1 + the parallel 2b/2c
entries):

- **Packaging rule (HARD, Phase 1):** `file://` blocks local ES-module imports and `fetch()`.
  Org data ships as a *classic* script `prototype/data/org.js` setting `window.ORG` — Phase 1's
  Notes for Downstream Phases recommends exactly this (option b). `<script src="data/org.js">`
  is added to `prototype/index.html` *before* the inline module. Phase 6 inlines it regardless.
- **appState v1 keys (Phase 1; extend, never rename):** `route · family · goal{id,title,crumb}
  · spines{feature,debug} · nudge{who,do,why} · receipts[] · pinned[] · drill ·
  chat{messages,scriptIndex}`. 2a adds `'spike' | 'data'` families and the org data.
- **Canonical goal identity (Phase 1):** `goal: { id: 'CAST-412', title: 'Add RBAC to
  checkout', crumb: 'northwind / goals' }` and route `#/goal/CAST-412`. Adopted as THE
  canonical CAST-412 title everywhere (see Decisions #2).
- **`stageModels` contract (2c):** shape quoted above; `appState.spines` keeps Phase 1 shape
  with `steps` derived via `stageModels.<f>.steps.map(s => s.shortLabel ?? s.label)`;
  `placeholder` flips to `false` only when 2c vocabulary lands.
- **Agent fixture shape (2b):** quoted above — 2a agents are supersets; camelCase stat fields
  (`compliancePct`) are 2b's locked names. **Decision atoms stay snake_case playbook-05 names
  verbatim** (`reversibility · options_considered · revisit_if · originating_agent ·
  supersedes/superseded_by · spike_ref · influenced[]`) — also locked by 2b.
- **NudgeCard prop (2b):** `{nudge:{who,do,why}}` = appState v1 shape verbatim — 2a's per-goal
  nudge objects use exactly these keys.
- **AutonomyDial prop (2b):** `{value, trust}` — 2a's per-goal autonomy object supplies both.
- **NO TESTS (owner):** no test-writing sub-phases, no test files, no CI; verification =
  manual click-through. (Fake test-result *content* inside the prototype — E1's "47 passed /
  0 failed", E3's red→green — is data, not tests, and stays.)
- **Phase 1 demo-script stubs** (hardcoded nudge, receipt label, spine arrays in `appState`)
  are explicitly placeholder; 2a.3 refactors them to spine reads.

## Contracts This Phase Exports (downstream phases consume these)

**1. File layout.**

```
prototype/
  index.html                    (Phase 1; 2a.3 adds one <script src> line + spine reads)
  data/
    org.js                      ← THE deliverable: classic script, window.ORG = Object.freeze({...})
    _build/                     ← authoring tooling only; never loaded by the browser
      package.json              (pins @faker-js/faker; node_modules gitignored)
      generate-org.mjs          (seeded faker + hand-tuned prose constants → SELF-VALIDATES → emits ../org.js)
```

**2. `window.ORG` top-level schema (keys frozen):**

```js
window.ORG = Object.freeze({
  meta:        { version: '1.0', seed: 42, frozen_at: '…', owner_notes: '…' },
  org:         { name: 'Northwind', crumb: 'northwind / goals' },
  humans:      [ { id, slug: '@you', kind: 'human', initials: 'SJ', role: 'eng lead', … },
                 { id, slug: '@priya', kind: 'human', initials: 'PK', role: 'PM', … } ], // the ONE PM persona (US7)
  guide:       { id, slug: 'cast-guide', kind: 'guide', name: 'the Guide' },  // NOT a marketplace agent
  agents:      { 'crud-orchestrator': { /* superset of 2b fixture shape: */ id, slug,
                 kind: 'maker'|'checker', pairedWith, stats: { compliancePct, loops, runs },
                 autonomy, rework: { used, budget }, inflight, state,
                 /* 2a superset fields: */ archetype, health, versions[], usage }, … }, // 12, keyed by slug
  stageModels: { feature: { placeholder: true, shape, steps: [{ id: 'feat-01', label, … }] },
                 debug: {…}, spike: {…}, data: {…} },                 // ← 2c-OWNED REGION (contract above)
  goals:       { 'CAST-412': { family, title, status, spine_state, artifacts[], work_stream[],
                 evidence, nudge: { who, do, why }, decisions[], chain_position,
                 autonomy: { value, trust: { compliancePct, runs } } }, … },  // 4, keyed by goal id
  board:       { columns[], tickets[] },
  decisions:   [ /* 5–8 atoms per goal, playbook-05 ADR schema verbatim */ ],
  hiring:      { request, dimensions[], candidates[], report, onboarding },
  layer2:      { contracts[ /*12*/ ], chain[ /*8*/ ], portfolio[ /*6*/ ] },
});
```

**3. The decision atom** — playbook 05 Step 1 schema adopted **verbatim** (id `DEC-<goal>-NN`,
`goal_slug`, `phase`, `title`, `reversibility`, `rationale`, `options_considered[]`,
`consequences`, `revisit_if`, `originating_agent`, `author_type`, `timestamp`, `status`,
`supersedes`/`superseded_by`, `spike_ref`, `influenced[]`) plus a scannable **`diff`** field
(`'classification: feature → bug'`) for the trail's diff-first rows. Reversals are new records,
never edits. L3 atoms carry exactly 3 options with `rank: 1|2|3` and `chosen: false` on all
three at rest (7A ranked rail, nothing pre-selected) plus an evidence pack
(`what_i_want`, `what_i_tried`).

**4. Step-id indirection (the 2c hand-off contract, adopting 2c's id grammar).** Goal
artifacts and work-stream items reference stage steps by **step id** (`feat-01` … never a
label string). Per-goal runtime position lives in `goals[id].spine_state =
{ current: '<step-id>', iter?: { current, budget }, timebox_used?: '1h40m' }`. At boot,
`appState.spines.<family>` is composed from `stageModels.<family>` (shape + derived label
array, per 2c's mapping rule) + the active goal's `spine_state` — preserving Phase 1's
appState spine shape exactly. 2c relabels/restructures `stageModels` only; goals re-map step
ids in the same commit (the generator's referential check holds them to it).

**5. appState v1.1 (extends v1; no renames):** `family` now ranges over
`'feature'|'debug'|'spike'|'data'`; `spines` gains `spike` + `data` keys (all four now
*derived from* `ORG.stageModels` + `spine_state`); `goal` is populated from `ORG.goals[id]`;
new key `org` = `window.ORG`; `receipts[]` items gain a `decision_id` field (keeping Phase 1's
`{level,label,at,rationale}` shape, now derived from the referenced atom).

**6. Canonical vocabulary (single source: `org.js`; grep-enforced).**

| Token | Canonical value (lives only in the spine) |
|-------|-------------------------------------------|
| Org / crumb | `Northwind` · `northwind / goals` |
| Feature goal | `CAST-412` · "Add RBAC to checkout" |
| Checker rule codes | `M04` (convention drift) · `S03` (typing too permissive) · `R02` (missing index on FK) |
| Rework budget | `1/3 used` |
| Reversibility | `L1 / L2 / L3` (reversibility-keyed only; no decision-weight gloss) |
| Canonical agent | `crud-orchestrator`, paired `crud-compliance-checker` |
| Marketplace cred stat | "99.9% compliant code in 2 maker-checker loops across 505 runs" (crud-orchestrator's `stats` fields) |
| Dial trust stat | "99.4% compliance across 312 runs" (feature-goal roster aggregate of the same `stats` fields) |
| PR | `PR #2341` |
| Test summary (E1 data) | `47 passed / 0 failed` |
| 8-agent chain | refine → decompose → research → synthesize → plan → detail → orchestrate → run |
| Archetypes | Maker / Checker / Decision / Spike / Escalation / Mentor |
| Escalation ticket | `CAST-417` — "Migrate roles schema (drops legacy `roles` column)" |

---

## Sub-phase 2a.1: Schema Lock & Self-Validating Generator

**Outcome:** `prototype/data/_build/generate-org.mjs` runs under node and deterministically
emits a schema-complete (content-thin) `org.js`; the generator **refuses to emit** when any
spine invariant is violated, printing the violated rule; the `window.ORG` schema above is real
code, not prose. 2b can swap its fixtures against this skeleton immediately.

**Dependencies:** Phase 1 plan (contracts; Phase 1 execution need not be complete — the only
runtime coupling is one `<script src>` line, deferred to 2a.3)
**Estimated effort:** ~0.5 session

**Verification (manual, per NO-TESTS rule):**
- `cd prototype/data/_build && npm install && node generate-org.mjs` → emits `org.js`; running
  it twice produces a byte-identical file (`git diff --quiet prototype/data/org.js` after a
  re-run — determinism check).
- Authoring sanity check: temporarily add a second L3 atom to one goal's constants in the
  generator → re-run refuses to emit and names the rule; revert.
- `org.js` loads standalone: `node -e "global.window={}; require('…/org.js'); console.log(Object.keys(window.ORG))"`
  prints the eleven top-level keys.
- `prototype/data/_build/node_modules/` is gitignored; `org.js` contains zero
  `require`/`import` and starts with the GENERATED header comment.

Key activities:
- Create `_build/package.json` pinning `@faker-js/faker` to an exact version (same
  pin-for-stability rationale as Phase 1's CDN pins); gitignore `node_modules`. This is
  authoring tooling, not a build step and not a test harness — the browser never touches
  `_build/`, `org.js` is committed, and FR-001's "no build step" governs *opening* the
  prototype, which stays double-clickable.
- Write `generate-org.mjs`: `faker.seed(42)`; **canonical values are hardcoded constants at
  the top of the file, never faker output** (faker supplies only structured filler — portfolio
  person names, commit SHAs, relative timestamps, candidate latency numbers). Hand-tuned prose
  lives in plain string constants alongside (the "LLM prose" of the high-level plan activity =
  authored during 2a.2, committed in this file). Emits
  `window.ORG = Object.freeze(<json>);` with a `// GENERATED by _build/generate-org.mjs — edit
  the generator, not this file. Classic script on purpose: file:// forbids fetch/imports.`
  header.
- Encode all timestamps as a fixed fictional demo timeline (one working day,
  `2026-06-11T09:00Z`–`18:00Z`, matching Phase 1's `17:52` receipt) — derived from seeded
  offsets, never `Date.now()` (determinism).
- Build the **invariant gate inside the generator** (a `check(rules, data)` pass before the
  file write — not a separate test file): per goal 5–8 decision atoms and **exactly one** `L3`;
  every atom's `goal_slug`/`originating_agent`/`influenced[]` resolve; `spike_ref` integrity is
  bidirectional (the E4 verdict references the atom that references it); every L3 has exactly
  3 ranked options, none `chosen`, with an evidence pack; every ticket assignee exists in
  `humans`/`agents`; every artifact/work-stream step reference and every `spine_state.current`
  exists in its family's `stageModels` step ids; supersede links pair correctly; all four
  `stageModels` families carry `placeholder: true` (until 2c); each goal's
  `autonomy.trust` equals the aggregate computed from its roster agents' `stats` fields; every
  atom carries a non-empty `diff`.
- Document the **freeze policy** in the `org.js` header and `meta.owner_notes`: after 2a,
  values are frozen; later phases may *extend* with new keys at designated extension points but
  never mutate existing values — with **one standing exception: the `stageModels` region is
  2c-owned** and will be rewritten once by 2c's derived stage vocabulary (via the generator,
  which re-runs the invariant gate at that moment).

**Design review:**
- **Zero silent failures:** every budget and referential rule from the high-level plan's
  verification is an executable refusal inside the authoring tool — drift cannot be *authored*,
  rather than being caught later by a suite the owner has banned.
- **NO-TESTS compliance:** no test files, no harness, no CI; the gate lives inside the
  generator and runs only when an author regenerates the spine. Flagged explicitly so no
  reviewer mistakes the generator for a test suite.
- **Naming:** decision atoms snake_case (playbook 05 / 2b locked); agent records camelCase
  stat fields (2b locked) — the mixed convention is deliberate and documented in the schema
  comment: atoms follow the ADR artifact idiom, agent records follow 2b's component-prop
  idiom. Everything else: kebab-case slugs, `DEC-<goal>-NN`, `CAST-4xx`, `<family>-NN` step ids.
- **Security:** static fake data, no user input, no network at runtime — no flags.

## Sub-phase 2a.2: Author the Org — Goals, Decisions, Roster, Hiring, Layer-2

**Outcome:** `org.js` is content-complete: one believable org a viewer could explore for ten
minutes without hitting lorem ipsum, a dangling reference, or a vocabulary drift. The four
locked L3 demo beats from playbook 05 are encoded verbatim. The generator still emits cleanly.

**Dependencies:** 2a.1
**Estimated effort:** ~1 session (the bulk of the phase — this is prose + data craft)

**Verification (manual, per NO-TESTS rule):**
- `node generate-org.mjs` emits with zero invariant refusals; its summary printout shows 5–8
  atoms per goal, exactly one L3 each, ≥1 superseded pair org-wide, 12 agents, 6 candidates,
  12 contracts.
- Spot-read `org.js`: every decision atom's `diff` is scannable; zero atoms log mere steps
  ("ran tests") rather than judgment calls between live alternatives; the four L3 atoms match
  playbook 05's locked table (feature: roles-column migration; debug: shared-auth-middleware
  fix scope; spike: 180ms-vs-200ms verdict; data: 8% source disagreement).
- `grep -cin 'lorem\|TODO\|FIXME' prototype/data/org.js` → 0; `grep -c 'placeholder'` hits
  only the four `stageModels` flags and their watermark labels (2c-owned).
- Read the marketplace candidates' pros/cons aloud — no GPT-isms, hyphens not em dashes,
  no mascot theater (FR-018 sanity pass).

Key activities:
- **Four family goals** (ids `CAST-412` feature · `CAST-431` debug · `CAST-452` spike ·
  `CAST-461` data), each with: placeholder `stageModels` entry in 2c's exact shape (feature
  `shape:'segments'`, 5 steps `feat-01…05` with Phase 1's placeholder labels; debug
  `shape:'loop'`, `loop:{over:'hypotheses', budget:3}`; spike `shape:'timebox'`,
  `timebox:{budget:'3h'}`; data `shape:'pipeline'`, 4 steps — all `placeholder: true`,
  labels watermarked); `spine_state` per goal (feature `current:'feat-04'`; debug
  `iter:{current:2,budget:3}`; spike `timebox_used:'1h40m'` after one L2-recorded extension
  from 2h to 3h; data `current:'data-03'`); stage-keyed artifacts per the familiar-tool
  principle (feature: requirements doc v2 → reqs step, plan doc, tickets, E1 panel →
  execution step; debug: investigation ledger; spike: memo; data: notebook + report v1/v2);
  a work-stream (feature: ~5 tickets incl. one `@you` manual item; debug: experiments per
  hypothesis; spike: probes-tried; data: pipeline cells); the current **nudge** (feature:
  `{who:'Guide', do:"Review CAST-412's PR", why:'checker flagged R02 — unblocks 2 queued
  tasks'}` — adopting Phase 1's stub verbatim as canon); `chain_position` (feature: `run`;
  debug: `orchestrate`; spike: `research`; data: `synthesize`); and `autonomy`
  (`{value:'balanced', trust:{…}}` per 2b's dial prop).
- **Story reconciliation (one weave, see Decisions #3–#5):** debug goal = "Checkout 500s on
  coupon apply" whose root cause lands in the shared auth middleware touched by the v4.2 RBAC
  migration — tying the standalone debug story to the CAST-412 feature world; spike goal =
  "Does the vendor checkout SDK fit our 200ms p95 budget?" (E4 verdict: "adds 180ms p95 —
  borderline", confidence M, 3 deciding data points, `spike_ref` both directions); data goal =
  "Which segment drove the Q2 revenue dip?" (E5: bar chart series + table + provenance with
  the two disagreeing sources: finance DB vs billing export, 8% apart).
- **Evidence payloads** as data: E1 (screenshot refs `assets/e1-*.png` + alt text + captions —
  image *files* are Phase 3 work via `/cast-preso-illustration-creator`; the spine owns refs +
  captions so naming can't drift; test summary `47 passed / 0 failed` + coverage delta;
  checker rows `M04 ✓ resolved · S03 ✓ resolved · R02 ⚠ flagged`; `PR #2341`), E2 (H1/H2
  refuted · H3 confirmed, each with prediction → observation), E3 (named repro test red output
  → same test green), E4 + E5 per above. Every treatment carries its confidence/flag field
  (●/◐/○ glyph values per 2b's token decision — never percentages; never a bare pass state).
- **Decision atoms** (~24 org-wide): per goal, the locked L3 + the playbook-05 L1/L2 examples
  + family-true filler to reach 5–8, every one a judgment call with rationale, `revisit_if`,
  and a scannable `diff` (e.g. `classification: feature → bug`). Include: the morph receipt
  atom `DEC-CAST-412-03` "Classify CAST-412 as bug, not feature" (L2 — Phase 1's receipt
  becomes this atom); the dial-demo L2 "Split FR-014 into routing + recording"; **one
  superseded pair** in the feature goal (L1 "Chose GraphQL for the RBAC endpoint" superseded
  by L1 "Chose REST — matches existing API surface") for the trail's strike-through moment;
  the feature L3 attached to ticket `CAST-417` with its three ranked options (additive+90-day /
  drop+snapshot / spike-dual-write) and the evidence pack.
- **Agent roster (12, keyed by slug, superset of 2b's fixture shape, 6 archetypes; makers
  carry `pairedWith`):** Makers — `crud-orchestrator` (canonical; stats 99.9 / 505 runs /
  2 loops), `entity-creation`, `migration-author`, `api-contractor`; Checkers —
  `crud-compliance-checker`, `test-coverage-checker`, `security-checker`; Decision —
  `decision-recorder`; Spike — `spike-runner`; Escalation — `escalation-router`; Mentor —
  `onboarding-mentor`, `repo-cartographer`. Non-maker/checker archetypes get `kind:'maker'`
  (square avatar grammar) with `archetype` carrying the marketplace facet. Each: `stats`
  (compliancePct, loops, runs), health badge (active / checker-flagged / benched — at least
  one of each org-wide), version history (SHA-pinned, faker SHAs), usage metrics. **The
  feature goal's roster aggregate is authored to equal the dial trust stat ("99.4% compliance
  across 312 runs") computed from the same `stats` fields the marketplace cards render** —
  generator-enforced (Decisions #7).
- **Hiring funnel data** (US6, "hire an rbac-agent"): the request; 5 assessment dimensions
  (user scale · internal/external surface · data sensitivity · migration safety · test rigor);
  **6 candidates** (e.g. `rbac-architect`, `access-control-builder`, `policy-gatekeeper`,
  `claims-mapper`, `session-warden`, `grant-auditor`), each with per-dimension radar scores,
  judge-style pros/cons prose, eval-run stats, and **deep links to fake produced work** —
  ≥1 produced-artifact stub per candidate (artifact id + type + content snippet: a code
  excerpt, a migration file, a checker report) so Phase 5b's report can deep-link to something
  real; stack-ranked report order; the hire = winner maker + its checker **together**;
  onboarding checklist (data sources, tastes, autonomy dial initial position).
- **Layer-2 data:** 12 named contracts — 8 chain-aligned (`refine-spec` · `decompose-steps` ·
  `research-notes` · `synthesis-playbook` · `phase-plan` · `detail-plan` · `dispatch-manifest` ·
  `run-envelope`) + 4 cross-cutting (`maker-checker-loop` · `decision-record` ·
  `escalation-handoff` · `evidence-bundle`), each with a one-line purpose and producer/consumer
  chain positions; the 8-node chain with per-node status vocabulary; portfolio of 6 shipped
  projects (faker names, runs/compliance stats — proof by volume).
- **Board data:** 4 columns (Backlog / In progress / In review / Done), ~9 tickets mixing
  human/agent/checker assignees, `CAST-412` in "In review" (agent work done, `@you` review
  pending — consistent with the nudge), `CAST-417` carrying the L3 escalation badge, in-flight
  pills, the "publishes INTO your PM tool" framing line as spine data.
- **US7 surface data (thin):** the feature requirements-doc artifact carries `version: 'v2'`,
  classification pill value, a change-summary delta, one anchored comment thread (author
  `@priya`, the PM persona, open→resolved), and the write-back notice text — ids and named
  values only; Phase 5c authors the full document body against these anchors.

**Design review:**
- **Naming-conflict resolution (the load-bearing review):** playbook 04 picked "Create Invoice
  entity + CRUD stack" as CAST-412's title; Phase 1's exported appState says "Add RBAC to
  checkout". One must lose — this plan adopts **RBAC** (Decisions #2) because Phase 1's
  contract is already exported, and the RBAC story is load-bearing for US6 ("hire an
  rbac-agent"), the locked feature L3 (roles-column migration), and playbook 05's atom
  examples. The maker-checker log content (entity creation via `crud-orchestrator` +
  `entity-creation`, M04/S03/R02 findings) ports unchanged: the RBAC work plausibly creates
  Role/Permission entities + CRUD stack.
- **L3 budget tension (US5 vs US10):** the board-arc escalation and the feature flow's L3 must
  be the **same atom** (budget: one L3 per flow; the board arc lives inside the feature flow's
  execution area). Encoded once on `CAST-417`, projected twice. Playbook 04's illustrative
  "DROP table user_events" escalation is superseded by the locked roles-column moment. ✓
- **Error path — content drift inside 2a itself:** all cross-references are generator-refused;
  prose referencing canonical tokens is interpolated from the constants that own them, never
  retyped.
- **Anthropomorphism check:** roster/candidate prose follows playbook 04's dial — structure of
  employment (track record, versions, pairing), zero mascot theater, no GPT-isms, hyphens not
  em dashes (FR-018).

## Sub-phase 2a.3: Wire, Sweep, Freeze

**Outcome:** `prototype/index.html` loads the spine from disk (`file://`) and every canonical
token it renders comes from `window.ORG`; appState is v1.1 (four families, `org` key, derived
spines); the drift grep is clean; the spine is declared frozen in `meta` and decisions-so-far
is updated.

**Dependencies:** 2a.2 + Phase 1 **execution** (needs the real `index.html` to wire; if Phase 1
execution hasn't landed yet, deliver 2a.1–2a.2 and a ~15-line wiring patch spec, and fold the
wiring into Phase 1's completion — see Risks)
**Estimated effort:** ~0.5 session

**Verification (this is the phase's headline verification, from the high-level plan — all
manual click-through):**
- Open `prototype/index.html` from disk in Chrome → console clean; the goal canvas renders
  CAST-412's title, crumb, nudge, and spine **from `window.ORG`** (verify: edit a title in the
  generator, regenerate, reload, the screen changes).
- `#/goal/CAST-431`, `#/goal/CAST-452`, `#/goal/CAST-461` each render the shell with their
  family's placeholder spine shape (proves all four families load; real canvases are Phase 3/4).
- The Phase 1 demo script still walks end-to-end; the morph receipt now renders from atom
  `DEC-CAST-412-03` (level, label, time all spine-derived) and `advance()` is unbroken.
- **Drift grep (zero ad-hoc naming):**
  `grep -rn -e 'CAST-4' -e 'M04\|S03\|R02' -e '99\.9\|99\.4\|505 runs\|312 runs' -e 'crud-orchestrator' -e '1/3' -e 'Northwind\|northwind' prototype/ --include='*.html' --include='*.js'`
  → every hit is in `data/org.js` or `data/_build/` (zero hits in `index.html`). Record the
  command in the freeze note; it reruns in Phase 6's final sweep.
- `meta.frozen_at` is set; decisions-so-far carries the 2a appendix.

Key activities:
- Add `<script src="data/org.js"></script>` to `index.html` ahead of the inline module
  (classic script — the only `file://`-legal local data path, per Phase 1 contract #1).
- Boot wiring: `appState.org = window.ORG`; populate `appState.goal` from
  `ORG.goals['CAST-412']`; replace Phase 1's inline `spines` literals with all four families
  derived from `ORG.stageModels` + the relevant goal's `spine_state` (2c's mapping rule:
  `steps.map(s => s.shortLabel ?? s.label)`); replace the inline nudge stub with the feature
  goal's nudge; route guard so `#/goal/<id>` resolves any of the four goal ids. Guard: if
  `window.ORG` is missing (script tag deleted / file moved), render a visible one-line error
  banner instead of silently painting stubs — zero silent failures.
- Refactor the Phase 1 demo-script morph step: `morph:debug` pushes a receipt **derived from**
  `ORG.decisions` (`DEC-CAST-412-03`) instead of the hardcoded stub object; receipt shape keeps
  Phase 1's keys + `decision_id`.
- Run the drift grep; hunt down any literal that crept into `index.html` during Phase 1
  (expected: the appState stubs being replaced in this sub-phase) and convert to spine reads.
- Freeze: set `meta.frozen_at`, commit, and append the 2a decision summary (~15 lines: file
  layout, schema keys, canonical-value table pointer, step-id indirection, freeze policy +
  2c exception) to `docs/plan/product-revamp-diecast-decisions-so-far.md`.

**Design review:**
- **Single-global discipline:** `window.ORG` is the only global the spine introduces, and it's
  `Object.freeze`d at the top level — accidental mutation by a later phase's component throws
  in strict mode rather than silently drifting the demo. (Deep-freeze is deliberately skipped:
  one `Object.freeze` per top-level value is enough protection for a demo, and 2c edits the
  generator and regenerates anyway.)
- **Load-order failure path:** classic script before module script guarantees `window.ORG`
  exists when the module runs; the missing-ORG banner covers the remaining failure mode.
- **Naming:** no flags — route grammar and appState keys unchanged from Phase 1.

## Build Order

```
2a.1 (schema + self-validating generator) ──► 2a.2 (author content) ──► 2a.3 (wire into index.html, drift sweep, FREEZE)
                                                                            │
        (2b swaps fixtures for the spine after freeze;  2c rewrites the stageModels region later via the generator)
```

**Critical path within the phase:** strictly sequential — 2a.2 needs 2a.1's invariant gate to
author against; 2a.3 needs full content to sweep. Total 1.5–2 sessions, matching the
high-level 0.5–1 day estimate.

## Design Review Flags

| Sub-phase | Flag | Action |
|-----------|------|--------|
| 2a.1 | npm/node in `_build/` could be mistaken for a runtime build step (FR-001) | Confine to `_build/`, gitignore node_modules, commit generated `org.js`, document in file header |
| 2a.1 | A standalone validator file could be read as a test file under the owner's NO-TESTS rule | Invariant gate folded INTO the generator (refuses to emit); no separate validator, no suite, no CI |
| 2a.1 | Non-deterministic generation (Date.now, unseeded faker) would make the freeze unverifiable | Seed 42, fixed fictional timeline, byte-identical re-run check |
| 2a.2 | CAST-412 title conflict (playbook 04 "Invoice CRUD" vs Phase 1 "Add RBAC to checkout") | Adopt RBAC; port the Invoice activity-log *structure* to RBAC entities; logged in Decisions #2 |
| 2a.2 | Two cred stats in playbooks (99.9/505 marketplace vs 99.4/312 dial) could read as drift | Per-agent `stats` fields (2b's names) are the single source; dial trust = authored roster aggregate; generator-enforced |
| 2a.2 | Board-arc L3 + feature-flow L3 would blow the one-L3-per-flow budget if encoded twice | One atom on CAST-417, two projections; generator counts L3 per goal |
| 2a.2 | Mixed field-name conventions (snake_case atoms vs camelCase agent stats) could confuse later authors | Deliberate: atoms = playbook-05 ADR idiom (2b locked), agents = 2b component-prop idiom (2b locked); documented in the schema comment |
| 2a.2 | Stage labels hardcoded into artifacts would force 2c re-keying | Step-id indirection per 2c's `<family>-NN` grammar (contract #4) |
| 2a.3 | `fetch('org.json')` regression risk when someone "cleans up" later | Classic-script rule restated in org.js header comment + freeze note |
| 2a.3 | Missing `window.ORG` would silently render Phase 1 stubs | Explicit error banner; stubs deleted, not shadowed |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Phase 1 execution hasn't landed when 2a.3 starts (2a runs parallel with 2b; Phase 1 build may still be in flight) | Med | 2a.1–2a.2 have zero runtime dependency; 2a.3 degrades to delivering the wiring patch spec against Phase 1's contracted shapes, folded in when index.html exists |
| 2c's derived vocabulary changes step *counts*, breaking `spine_state.current` and artifact step references | Med | Step-id indirection + the generator's referential refusal; 2c regenerates via the generator, so the gate re-runs at exactly that moment |
| Hand-tuned prose drifts canonical tokens inside org.js itself (e.g., "99.9%" retyped slightly differently in a candidate's pros) | Med | Canonical strings are named constants in the generator, interpolated into prose templates — never retyped |
| Spine over-grows (40 decision atoms, 20 candidates) and the trail becomes audit theater | Med | Generator hard-caps: 5–8 atoms/goal, exactly 1 L3, 6 candidates, 12 agents, 12 contracts |
| 2b's fixture shape evolves during its build (it planned in parallel) and the superset contract drifts | Low–Med | The fixture shape is now in decisions-so-far (locked); any 2b deviation must be flagged there per the log's rules — 2a.3's wiring is the reconciliation checkpoint |
| E1 screenshot refs point at images that never get made (Phase 3 owns them) | Low | Refs + alt text + captions in spine give Phase 3 an explicit work-list; Phase 6 drift sweep catches dead refs |
| faker version drift changes seeded output | Low | Exact version pin + committed output; regeneration is optional, the committed file is canon |

## Open Questions

None blocking — full-autonomy mode resolved all judgment calls (logged below). Deferred items
owned elsewhere, listed for traceability:

- Real per-family stage vocabulary → Phase 2c (spine ships watermarked placeholders inside the
  reserved `stageModels` slot, in 2c's locked shape).
- The Guide's visual treatment → Phase 2b (spine carries only `{id, slug, kind, name}`).
- E1 fake screenshot images → Phase 3 (via `/cast-preso-illustration-creator` +
  `/cast-preso-illustration-checker`); spine owns the refs/captions.
- Full requirements-doc body prose → Phase 5c (spine owns ids, version, classification,
  comment anchors, write-back text).

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| `docs/specs/_registry.md` (re-confirmed against the high-level plan's check) | all 7 specs govern cast-server runtime | None — FR-020: prototype is greenfield; no spec applies, none contradicted |

No `/cast-update-spec` action: the delegation explicitly excludes spec flows for this
deliverable (greenfield design artifact, not product behavior).

## Notes for Downstream Phases

- **2b:** swap fixtures for `window.ORG` after freeze; the colleague-card stat footer, dial
  legend tooltip, and résumé track-record panel must all render from `agents[slug].stats` —
  no local stat literals. The agent records are supersets of your fixture shape; ignore the
  extra fields (`archetype`, `health`, `versions`, `usage`) until Phase 5 needs them.
- **2c:** rewrite ONLY `stageModels` via `generate-org.mjs` (edit the generator's stage-model
  constants, regenerate; the invariant gate re-checks all goal step references). Flip
  `placeholder: false` and drop watermarks at that moment. If step counts change, remap each
  goal's `spine_state.current` and artifact step ids in the same commit — the generator will
  refuse to emit otherwise.
- **Phase 3/4:** scenario scripts reference spine ids (`DEC-…`, `CAST-…`, agent slugs, step
  ids) — narration prose may be authored in scripts, but any canonical token in narration must
  be interpolated from `ORG`. The four L3 demo beats are already encoded as atoms; scripts
  *project* them, never restate them.
- **Phase 5:** hiring report deep-links target the candidate `produced_work` artifact stubs;
  board/ticket/decision/escalation all read the single CAST-417 L3 atom; the dial toggle beat
  re-renders the existing L2 atom "Split FR-014…" under the shifted threshold — no second atom.
- **Phase 6:** inline `data/org.js` into the single file; re-run the 2a.3 drift grep across
  the final artifact as part of the fake-data drift sweep.

## Decisions Made Autonomously

1. **`org.js` classic script over inline JSON block** — Phase 1's Notes recommended exactly
   this (option b: keeps data a separate file during the build; Phase 6 inlines regardless);
   inline JSON would bloat index.html during the highest-churn authoring window.
2. **CAST-412 = "Add RBAC to checkout"**, rejecting playbook 04's "Create Invoice entity +
   CRUD stack" — Phase 1 already exported the RBAC title in appState v1 (a contract this plan
   must not rename), and the RBAC story carries US6's "hire an rbac-agent", the locked feature
   L3, and playbook 05's atom examples. The Invoice pick's *reason* (richest maker-checker log)
   is preserved by porting the CRUD-stack activity-log structure to RBAC entities.
3. **Debug goal woven into the RBAC world** ("Checkout 500s on coupon apply" → root cause in
   shared auth middleware touched by the v4.2 RBAC migration) — reconciles playbook 03's debug
   header with playbook 05's locked debug L3 and makes the org read as one company, not four
   disconnected demos.
4. **Spike goal = vendor-SDK latency question** (180ms vs 200ms budget), adopting playbook 05's
   *locked* L3 beat over playbook 03's illustrative SQLite example — the L3 table is marked
   "hand these to the build step as locked demo beats"; the SQLite question was illustrative.
5. **Data goal = Q2 revenue dip**, adapted from playbook 03's illustrative onboarding-funnel
   question so the analysis question and its locked L3 (8% source disagreement on Q2 revenue)
   belong to the same story.
6. **One L3 atom serves both US5's escalation rail and the feature flow's hard stop**
   (CAST-417, roles-column migration; playbook 04's "DROP table user_events" example
   superseded) — the board arc lives inside the feature flow, so two L3s would break the
   exactly-one-per-flow budget.
7. **Cred-stat unification:** per-agent `stats {compliancePct, loops, runs}` (2b's locked
   names) is the single source; the marketplace canonical line renders crud-orchestrator's
   fields; the dial trust tooltip renders the goal-roster aggregate, authored to equal playbook
   05's "99.4% across 312 runs" and generator-checked — satisfying "dial tooltip stats and
   marketplace cred read from the same fields" without a second stat system.
8. **Adopted 2c's `stageModels` slot + `<family>-NN` step-id grammar mid-planning** (2c's
   contract appeared in decisions-so-far during this planning round), discarding this plan's
   earlier draft `families.*.spine` + `s1…sN` key scheme — same indirection intent, sibling's
   locked names win per the log's adoption rule.
9. **Adopted 2b's agent fixture shape as the agents-record base mid-planning** (same round),
   accepting the mixed snake_case/camelCase convention (atoms = ADR idiom, agents =
   component-prop idiom) rather than forcing one convention and breaking a sibling's locked
   contract.
10. **Invariant gate folded into the generator instead of a standalone validator file** —
    honors the owner's NO-TESTS rule (added to decisions-so-far this round) while keeping the
    high-level plan's verification bullets machine-enforced at authoring time; under full
    autonomy, refuse-to-emit beats vibes-checkable.
11. **Goal ids CAST-431 / CAST-452 / CAST-461** for debug/spike/data — keeps one ticket-grammar
    namespace (`CAST-4xx`) per the preso convention; CAST-412/417 remain the locked feature pair.
12. **12 contract names authored as 8 chain-aligned + 4 cross-cutting** (list in 2a.2) —
    derived from real Diecast vocabulary (delegation/output contracts, maker-checker,
    escalation) so the Layer-2 catalogue reads as enumerable truth, not filler; exploration
    never enumerated the 12, so authoring them is 2a's job.
13. **6 hiring candidates** (range was 5–10) — enough for a credible stack-rank + head-to-head
    while keeping per-candidate eval prose (the expensive part) affordable within the session
    budget.
14. **`Object.freeze` shallow, not deep** — protects the contract surface without blocking
    2c's planned stageModels rewrite; deep mutation risk accepted for a demo artifact.
15. **US7 data encoded thin** (ids, version, classification, comment anchors, notice text;
    no document body) — the spine owns whatever could drift across surfaces; Phase 5c owns
    long-form prose. Keeps 2a inside its 0.5–1 day box.
16. **Superseded-pair placement in the feature goal** (GraphQL → REST) — gives Phase 5a's
    trail its strike-through moment using playbook 05's own L1 example, at zero extra
    story cost.
17. **`cast-plan-review` auto-dispatch skipped** — run configuration in
    `product-revamp-diecast-decisions-so-far.md` states "Plan review: skipped — cross-phase
    reconciliation only" (owner-approved). Recorded here, consistent with Phase 1's decision
    #12 and Phase 2b's closing decision; rerun manually via `/cast-plan-review` against this
    file if wanted.

## Suggested Revisions to Prior Sub-Phases

None required — including for the two siblings that planned in parallel (2b, 2c): their
exported contracts were adopted wholesale (Decisions #8–#9). Two advisory notes rather than
revisions:

- **Phase 1:** its inline data stubs (appState spines, nudge, hardcoded receipt) are consumed
  and replaced by 2a.3 as Phase 1's own plan anticipated ("Phase 2a extends, must not
  rename"). The demo-script receipt stub (`label: 'Reclassified feature→bug — debug loop',
  at: '17:52'`) becomes atom `DEC-CAST-412-03` — if Phase 1 execution lands first, keep the
  stub's wording verbatim so 2a.3's swap is invisible in the demo.
- **Phase 2b:** its `#/kit` fixtures hand-type canonical vocabulary by design ("so 2a wiring
  is a data swap"). After 2a's freeze, those fixture literals are the one *sanctioned*
  exception to the drift grep until the swap happens — the 2a.3 grep allowlist should include
  the `#/kit` fixture block if 2b lands first, and the swap removes the exception.
