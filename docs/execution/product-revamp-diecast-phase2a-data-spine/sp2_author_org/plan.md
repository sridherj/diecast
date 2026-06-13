# Sub-phase 2 (2a.2): Author the Org — Goals, Decisions, Roster, Hiring, Layer-2

> **Pre-requisite:** Read `docs/execution/product-revamp-diecast-phase2a-data-spine/_shared_context.md`
> before starting. It carries the binding constraints (NO TESTS, `file://` legality, F4
> single-source rule), the full `window.ORG` schema, the decision-atom schema, and the
> canonical-vocabulary table.
>
> **Also read first (binding context the runner MUST load):**
> `docs/plan/product-revamp-diecast-decisions-so-far.md` and
> `docs/plan/2026-06-11-product-revamp-diecast-phase2a-data-spine.md` (the L3 demo-beat
> details and per-goal content live in the plan doc's 2a.2 section).

## Objective

Make `org.js` **content-complete**: one believable org a viewer could explore for ten
minutes without hitting lorem ipsum, a dangling reference, or a vocabulary drift. The four
locked **L3 demo beats** from playbook 05 are encoded verbatim. The generator still emits
cleanly (zero invariant refusals). This is the bulk of Phase 2a — prose + data craft on top
of 2a.1's schema + gate.

## Dependencies

- **Requires completed:** sp1 (2a.1) — the schema lock and the in-generator invariant gate.
- **Assumed codebase state:** `prototype/data/_build/generate-org.mjs` exists and emits a
  schema-complete (content-thin) `org.js` that passes the gate. You grow the content inside
  the same generator constants, keeping the gate green.

## Scope

**In scope (author inside `generate-org.mjs`'s constants/prose, then regenerate):**
- Four family goals (`CAST-412` feature, `CAST-431` debug, `CAST-452` spike, `CAST-461`
  data) — full per-goal content.
- ~24 decision atoms org-wide (5–8 per goal, exactly one L3 each), incl. the four locked L3
  beats and one superseded pair.
- Agent roster (12, 6 archetypes, supersets of 2b's fixture shape) with the
  generator-enforced trust-stat aggregation.
- Hiring funnel data (US6): request, 5 dimensions, 6 candidates with radar + pros/cons +
  produced-work stubs, report, onboarding.
- Layer-2 data: 12 contracts, 8-node chain, 6-project portfolio.
- Board data (~9 tickets), placeholder `stageModels` content in 2c's exact shape, evidence
  payloads E1–E5 as data, thin US7 surface data.

**Out of scope (do NOT do these):**
- Wiring into `index.html`, the drift grep, or the freeze — that is **2a.3**.
- Editing `org.js` directly — author in the **generator**, then regenerate (F4).
- Real per-family stage vocabulary — `stageModels` stays `placeholder:true`, watermarked
  labels (2c owns the rewrite).
- E1 screenshot **image files** — the spine owns refs + alt text + captions only; the
  rasters are Phase 3 work (`/cast-preso-illustration-creator`).
- Full requirements-doc **body prose** — US7 data stays thin (Phase 5c owns the body).
- Any test file, suite, harness, or CI (banned).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `prototype/data/_build/generate-org.mjs` | Modify | Schema-complete from 2a.1; grow content constants/prose |
| `prototype/data/org.js` | Regenerate | Content-thin from 2a.1; becomes content-complete |

## Detailed Steps

### Step 2.1: Four family goals
Author each goal in 2c's exact `stageModels` shape (placeholder content) + per-goal runtime
state:
- **Goal ids & families:** `CAST-412` feature · `CAST-431` debug · `CAST-452` spike ·
  `CAST-461` data.
- **Placeholder `stageModels` entries** (all `placeholder:true`, labels watermarked):
  feature `shape:'segments'`, 5 steps `feat-01…05` (Phase 1 placeholder labels); debug
  `shape:'loop'`, `loop:{over:'hypotheses', budget:3}`; spike `shape:'timebox'`,
  `timebox:{budget:'3h'}`; data `shape:'pipeline'`, 4 steps `data-01…04`.
- **`spine_state` per goal:** feature `current:'feat-04'`; debug `iter:{current:2,budget:3}`;
  spike `timebox_used:'1h40m'` (after one L2-recorded extension from 2h to 3h); data
  `current:'data-03'`.
- **Stage-keyed artifacts** (familiar-tool principle, referenced by step id): feature —
  requirements doc v2 → reqs step, plan doc, tickets, E1 panel → execution step; debug —
  investigation ledger; spike — memo; data — notebook + report v1/v2.
- **Work-stream** per goal: feature ~5 tickets incl. one `@you` manual item; debug
  experiments per hypothesis; spike probes-tried; data pipeline cells.
- **Nudge** (feature, adopting Phase 1's stub verbatim as canon):
  `{who:'Guide', do:"Review CAST-412's PR", why:'checker flagged R02 — unblocks 2 queued tasks'}`.
- **`chain_position`:** feature `run`; debug `orchestrate`; spike `research`; data `synthesize`.
- **`autonomy`:** `{value:'balanced', trust:{…}}` per 2b's dial prop.

### Step 2.2: Story reconciliation (one weave — read as one company)
- **Debug goal** `CAST-431` = "Checkout 500s on coupon apply" whose root cause lands in the
  **shared auth middleware** touched by the v4.2 RBAC migration — ties the debug story to the
  CAST-412 feature world.
- **Spike goal** `CAST-452` = "Does the vendor checkout SDK fit our 200ms p95 budget?"
  (E4 verdict: "adds 180ms p95 — borderline", confidence M, 3 deciding data points,
  `spike_ref` wired **both directions**).
- **Data goal** `CAST-461` = "Which segment drove the Q2 revenue dip?" (E5: bar-chart series
  + table + provenance with the two disagreeing sources — finance DB vs billing export, 8%
  apart).

### Step 2.3: Evidence payloads (E1–E5 as data)
- **E1:** screenshot refs `assets/e1-*.png` + alt text + captions (image *files* are Phase 3;
  the spine owns refs + captions so naming can't drift); test summary `47 passed / 0 failed`
  + coverage delta; checker rows `M04 ✓ resolved · S03 ✓ resolved · R02 ⚠ flagged`;
  `PR #2341`.
- **E2:** H1/H2 refuted · H3 confirmed, each with prediction → observation.
- **E3:** named repro test red output → same test green.
- **E4 / E5:** per Step 2.2.
- Every treatment carries its **confidence/flag** field (●/◐/○ glyph values per 2b's token
  decision — never percentages; never a bare pass state).

### Step 2.4: Decision atoms (~24 org-wide)
Per goal: the locked L3 + the playbook-05 L1/L2 examples + family-true filler to reach 5–8.
Every atom is a **judgment call** with rationale, `revisit_if`, and a scannable `diff` (e.g.
`classification: feature → bug`). Include specifically:
- **`DEC-CAST-412-03`** "Classify CAST-412 as bug, not feature" (**L2** — Phase 1's morph
  receipt becomes this atom).
- The **dial-demo L2** "Split FR-014 into routing + recording".
- **One superseded pair** in the feature goal (L1 "Chose GraphQL for the RBAC endpoint"
  superseded by L1 "Chose REST — matches existing API surface") — for the trail's
  strike-through moment.
- The **feature L3** attached to ticket **`CAST-417`** with its three ranked options
  (additive+90-day / drop+snapshot / spike-dual-write) and the evidence pack.
- **The four locked L3 beats** (playbook 05): feature = roles-column migration; debug =
  shared-auth-middleware fix scope; spike = 180ms-vs-200ms verdict; data = 8% source
  disagreement.

### Step 2.5: Agent roster (12, keyed by slug, supersets of 2b's fixture shape, 6 archetypes)
- **Makers:** `crud-orchestrator` (canonical; stats 99.9 / 505 runs / 2 loops),
  `entity-creation`, `migration-author`, `api-contractor`.
- **Checkers:** `crud-compliance-checker`, `test-coverage-checker`, `security-checker`.
- **Decision:** `decision-recorder`. **Spike:** `spike-runner`. **Escalation:**
  `escalation-router`. **Mentor:** `onboarding-mentor`, `repo-cartographer`.
- Non-maker/checker archetypes get `kind:'maker'` (square avatar grammar) with `archetype`
  carrying the marketplace facet. Makers carry `pairedWith`.
- Each: `stats` (compliancePct, loops, runs), health badge (active / checker-flagged /
  benched — **at least one of each** org-wide), version history (SHA-pinned, faker SHAs),
  usage metrics.
- **The feature goal's roster aggregate is authored to equal the dial trust stat
  ("99.4% compliance across 312 runs")** computed from the same `stats` fields the
  marketplace cards render — **generator-enforced**.

### Step 2.6: Hiring funnel data (US6 — "hire an rbac-agent")
- The request; 5 assessment dimensions (user scale · internal/external surface · data
  sensitivity · migration safety · test rigor).
- **6 candidates** (e.g. `rbac-architect`, `access-control-builder`, `policy-gatekeeper`,
  `claims-mapper`, `session-warden`, `grant-auditor`), each with per-dimension radar scores,
  judge-style pros/cons prose, eval-run stats, and **deep links to fake produced work** —
  ≥1 produced-artifact stub per candidate (artifact id + type + content snippet: a code
  excerpt, a migration file, a checker report) so Phase 5b's report can deep-link to
  something real.
- Stack-ranked report order; the hire = **winner maker + its checker together**; onboarding
  checklist (data sources, tastes, autonomy dial initial position).

### Step 2.7: Layer-2 data
- **12 named contracts** — 8 chain-aligned (`refine-spec · decompose-steps · research-notes
  · synthesis-playbook · phase-plan · detail-plan · dispatch-manifest · run-envelope`) + 4
  cross-cutting (`maker-checker-loop · decision-record · escalation-handoff ·
  evidence-bundle`), each with a one-line purpose and producer/consumer chain positions.
- The **8-node chain** with per-node status vocabulary.
- **Portfolio of 6** shipped projects (faker names, runs/compliance stats — proof by volume).

### Step 2.8: Board data
- 4 columns (Backlog / In progress / In review / Done), ~9 tickets mixing human/agent/checker
  assignees.
- `CAST-412` in **"In review"** (agent work done, `@you` review pending — consistent with
  the nudge); `CAST-417` carrying the **L3 escalation badge**; in-flight pills; the
  "publishes INTO your PM tool" framing line as spine data.

### Step 2.9: US7 surface data (thin)
The feature requirements-doc artifact carries `version:'v2'`, classification pill value, a
change-summary delta, **one anchored comment thread** (author `@priya`, the PM persona,
open→resolved), and the write-back notice text — **ids and named values only**; Phase 5c
authors the full document body against these anchors.

### Step 2.10: Regenerate and confirm the gate stays green
Re-run `node generate-org.mjs`. It must emit with **zero invariant refusals**, and its
summary printout must show 5–8 atoms per goal, exactly one L3 each, ≥1 superseded pair
org-wide, 12 agents, 6 candidates, 12 contracts.

## Verification

> Per the NO-TESTS rule: **no test files, no suite, no CI.** Manual click-through + the
> generator's own gate + spot-reads.

### Validation Commands (run by hand)
1. **Gate green + summary:**
   ```bash
   cd prototype/data/_build && node generate-org.mjs
   ```
   Emits with zero invariant refusals; summary shows 5–8 atoms/goal, exactly one L3 each,
   ≥1 superseded pair org-wide, 12 agents, 6 candidates, 12 contracts.
2. **No filler:**
   ```bash
   grep -cin 'lorem\|TODO\|FIXME' prototype/data/org.js   # → 0
   grep -c 'placeholder' prototype/data/org.js            # hits ONLY the 4 stageModels flags + watermark labels
   ```
3. **Determinism preserved:** a second `node generate-org.mjs` produces a byte-identical
   `org.js` (`git diff --quiet prototype/data/org.js`).

### Manual Spot-Reads
- Every decision atom's `diff` is scannable; **zero** atoms log mere steps ("ran tests")
  rather than judgment calls between live alternatives.
- The **four L3 atoms** match playbook 05's locked table (feature: roles-column migration;
  debug: shared-auth-middleware fix scope; spike: 180ms-vs-200ms verdict; data: 8% source
  disagreement).
- Read the marketplace candidates' pros/cons aloud — **no GPT-isms, hyphens not em dashes,
  no mascot theater** (FR-018 sanity pass).

### Success Criteria (binary — every item must pass)
- [ ] `node generate-org.mjs` emits cleanly (zero refusals) with the expected summary counts.
- [ ] `grep -cin 'lorem\|TODO\|FIXME'` on `org.js` → 0.
- [ ] `grep -c 'placeholder'` hits only the 4 `stageModels` flags + their watermark labels.
- [ ] All four locked L3 atoms encoded verbatim per playbook 05.
- [ ] Exactly one superseded pair (GraphQL → REST) in the feature goal.
- [ ] `CAST-417` carries the single feature L3, badged on the board.
- [ ] Roster = 12 agents / 6 archetypes, ≥1 each of active/checker-flagged/benched health.
- [ ] Feature-roster `stats` aggregate equals the dial trust stat (99.4% / 312 runs),
      generator-enforced.
- [ ] 6 hiring candidates, each with ≥1 produced-work stub; 12 Layer-2 contracts; 6-project
      portfolio.
- [ ] Re-run is byte-identical (determinism holds).

## Design Review

- **Naming-conflict resolution (the load-bearing review):** playbook 04 picked "Create
  Invoice entity + CRUD stack" as CAST-412's title; Phase 1's exported appState says
  "Add RBAC to checkout". One must lose — this plan adopts **RBAC** (Phase 1's contract is
  already exported, and the RBAC story is load-bearing for US6, the locked feature L3, and
  playbook 05's atom examples). The maker-checker log content (entity creation via
  `crud-orchestrator` + `entity-creation`, M04/S03/R02 findings) **ports unchanged**: the
  RBAC work plausibly creates Role/Permission entities + CRUD stack.
- **L3 budget tension (US5 vs US10):** the board-arc escalation and the feature flow's L3
  must be the **same atom** (budget: one L3 per flow; the board arc lives inside the feature
  flow's execution area). Encoded once on `CAST-417`, **projected twice**. Playbook 04's
  illustrative "DROP table user_events" escalation is superseded by the locked roles-column
  moment.
- **Error path — content drift inside 2a itself:** all cross-references are generator-refused;
  prose referencing canonical tokens is **interpolated from the constants that own them**,
  never retyped.
- **Anthropomorphism check:** roster/candidate prose follows playbook 04's dial — structure
  of employment (track record, versions, pairing), zero mascot theater, no GPT-isms, hyphens
  not em dashes (FR-018).

## Design Review Flags (from the plan)

| Flag | Action |
|------|--------|
| CAST-412 title conflict (PB-04 "Invoice CRUD" vs Phase 1 "Add RBAC to checkout") | Adopt RBAC; port the Invoice activity-log *structure* to RBAC entities |
| Two cred stats (99.9/505 marketplace vs 99.4/312 dial) could read as drift | Per-agent `stats` (2b's names) single source; dial trust = authored roster aggregate; generator-enforced |
| Board-arc L3 + feature-flow L3 would blow the one-L3-per-flow budget if encoded twice | One atom on CAST-417, two projections; generator counts L3 per goal |
| Mixed field-name conventions (snake_case atoms vs camelCase agent stats) | Deliberate; documented in the schema comment (ADR idiom vs component-prop idiom) |
| Stage labels hardcoded into artifacts would force 2c re-keying | Step-id indirection per 2c's `<family>-NN` grammar |

## Execution Notes

- **Author in the generator, never in `org.js`.** Editing `org.js` directly violates F4 and
  will be overwritten on the next regenerate.
- **Canonical tokens are constants, interpolated into prose** — never retype "99.9%" or
  "M04" inside a candidate's pros; reference the constant. This is how 2a prevents drift
  *inside* its own prose.
- The four L3 beats are **locked demo beats** — encode them verbatim from playbook 05; do
  not improvise alternatives.
- This is the heavy session (~1 session of prose + data craft). The gate is your safety net:
  if a reference dangles, the generator refuses to emit and names the rule — fix and re-run.
- **Spec-linked files:** none (FR-020 greenfield).
