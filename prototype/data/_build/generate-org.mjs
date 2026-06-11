// generate-org.mjs — seeded, self-validating generator for the Diecast vision-prototype data spine.
//
// WHAT THIS IS: build-time AUTHORING TOOLING. It deterministically emits the committed classic
// script ../org.js (window.ORG = Object.freeze({...})). The browser NEVER loads _build/. This is
// NOT a build step (FR-001 governs *opening* the prototype, which stays double-clickable because
// org.js is committed) and NOT a test harness (the owner's NO-TESTS rule bans test files/suites/CI).
//
// THE GATE: the only machine-enforced check in this deliverable lives INSIDE this file — check()
// runs before the file write and REFUSES TO EMIT (exits non-zero, prints the violated rule) on any
// spine-invariant violation. Drift cannot be *authored*. Do NOT extract it into a standalone
// validator: a separate validator would read as a banned test artifact.
//
// DETERMINISM: faker.seed(42); canonical values are hardcoded constants (CANON) — NEVER faker output;
// faker supplies only structured filler (person names, commit SHAs, usage numbers). All timestamps
// derive from a fixed fictional one-day demo timeline (2026-06-11T09:00Z–18:00Z) via t() — never
// Date.now(). Stable key order + JSON.stringify → byte-identical re-runs.
//
// SCOPE (2a.1): SCHEMA LOCK + the gate. Content is intentionally THIN — atoms/roster/hiring/layer2
// carry skeletal '[2a.2]'/'[2c]' placeholders that already satisfy the gate. 2a.2 grows the prose
// while keeping the gate green; 2c rewrites ONLY the stageModels region (the one freeze exception).
//
// NAMING (deliberate, documented here per the schema comment): decision atoms use snake_case
// playbook-05 ADR field names verbatim; agent records use camelCase stat fields (2b component-prop
// idiom). Everything else: kebab-case slugs, DEC-<goal>-NN atom ids, CAST-4xx tickets, <family>-NN
// step ids.

import { writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { faker } from '@faker-js/faker';

faker.seed(42);

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT_PATH = join(__dirname, '..', 'org.js');

// ───────────────────────────────────────────────────────────────────────────
// CANON — canonical values (the single source of every grep-enforced token).
// Hardcoded on purpose: faker NEVER produces a canonical value.
// ───────────────────────────────────────────────────────────────────────────
const CANON = {
  org: { name: 'Northwind', crumb: 'northwind / goals' },
  feature: { id: 'CAST-412', title: 'Add RBAC to checkout' },
  escalationTicket: { id: 'CAST-417', title: 'Migrate roles schema (drops legacy roles column)' },
  debug: { id: 'CAST-431', title: 'Checkout 500s on coupon apply' },
  spike: { id: 'CAST-452', title: 'Vendor checkout SDK latency spike (180ms vs 200ms p95)' },
  data: { id: 'CAST-461', title: 'Q2 revenue dip: which segment drove it?' },
  ruleCodes: { M04: 'convention drift', S03: 'typing too permissive', R02: 'missing index on FK' },
  rework: '1/3 used',
  canonicalAgent: 'crud-orchestrator',
  canonicalChecker: 'crud-compliance-checker',
  marketplaceCred: '99.9% compliant code in 2 maker-checker loops across 505 runs',
  dialTrust: '99.4% compliance across 312 runs',
  // parsed twin of dialTrust - the [dial-trust] gate rule enforces the feature roster aggregate equals this.
  dialTrustParsed: { compliancePct: 99.4, runs: 312 },
  pr: 'PR #2341',
  testSummary: '47 passed / 0 failed',
  chain: ['refine', 'decompose', 'research', 'synthesize', 'plan', 'detail', 'orchestrate', 'run'],
  archetypes: ['Maker', 'Checker', 'Decision', 'Spike', 'Escalation', 'Mentor'],
};

const FREEZE_POLICY =
  'FROZEN after Phase 2a. Later phases may EXTEND with new keys at designated extension points but ' +
  'never mutate existing values. ONE standing exception: the stageModels region is 2c-owned and is ' +
  'rewritten once by 2c via this generator (which re-runs the invariant gate at that moment). This is ' +
  'the F4 single-source rule: org.js is generated, never hand-edited - edit the generator and regenerate.';

// ───────────────────────────────────────────────────────────────────────────
// Fixed fictional demo timeline: one working day, 2026-06-11T09:00Z–18:00Z.
// t(offsetMinutes) maps an offset (0..540) into that day. Phase 1's 17:52 receipt = t(532).
// ───────────────────────────────────────────────────────────────────────────
const DAY_START_MS = Date.parse('2026-06-11T09:00:00.000Z'); // parse of a literal — deterministic, not Date.now()
function t(offsetMinutes) {
  return new Date(DAY_START_MS + offsetMinutes * 60_000).toISOString();
}

// faker filler helpers (deterministic given the fixed call order under seed 42)
const sha = () => faker.git.commitSha().slice(0, 7);
const personName = () => faker.person.fullName();

// ───────────────────────────────────────────────────────────────────────────
// humans · guide · org · meta
// ───────────────────────────────────────────────────────────────────────────
const humans = [
  { id: 'h-you', slug: '@you', kind: 'human', initials: 'SJ', role: 'eng lead', name: 'you' },
  { id: 'h-priya', slug: '@priya', kind: 'human', initials: 'PK', role: 'PM', name: 'Priya Kannan' },
];

const guide = { id: 'g-guide', slug: 'cast-guide', kind: 'guide', name: 'the Guide' };

const org = { name: CANON.org.name, crumb: CANON.org.crumb };

const meta = {
  version: '1.0',
  seed: 42,
  // 2a.3 FREEZE STAMP: a fixed constant on the demo timeline (t(540) = 2026-06-11T18:00:00.000Z,
  // the end of the fictional one-day demo). Deterministic on purpose — never Date.now() — so the
  // frozen spine re-generates byte-identically. After this stamp, org.js values are frozen (F4);
  // later phases extend additively via the generator, the stageModels region being the sole 2c exception.
  frozen_at: t(540),
  generated_by: '_build/generate-org.mjs',
  owner_notes: FREEZE_POLICY,
};

// ───────────────────────────────────────────────────────────────────────────
// agents — 12, keyed by slug. Superset of 2b's fixture shape. kind ∈ maker|checker
// (non-maker/checker archetypes get kind:'maker' = square avatar; archetype carries the facet).
// stats are CANON-grade hardcoded numbers (never faker); versions/usage use faker filler.
// ───────────────────────────────────────────────────────────────────────────
// Each agent record is the structure of an employment record, not a mascot: a track record
// (stats), a pairing (pairedWith), a version history, and a health state. NO anthropomorphism,
// NO mascot theater (FR-018). version notes describe shipped behavior changes, like a changelog.
//
// FEATURE-ROSTER STATS ARE LOAD-BEARING: entity-creation (96 runs), migration-author (120),
// api-contractor (96) are the three makers staffed on CAST-412's RBAC build. Their runs-weighted
// aggregate is authored to land EXACTLY on the canonical dial-trust stat (99.4% / 312 runs):
//   99.1*96 + 99.6*120 + 99.4*96 = 31008 ; 31008/312 = 99.384.. -> rounds to 99.4 ; runs 96+120+96 = 312.
// crud-orchestrator (99.9 / 505) is the canonical MARKETPLACE exemplar and the goal's orchestrator,
// shown on the board and in the nudge; it is deliberately NOT in the dial roster because its 505-run
// lifetime record alone exceeds the 312-run goal aggregate. The split is the two-scope design from
// decisions-so-far #7 (marketplace = lifetime crud-orchestrator; dial = this goal's staffed makers).
// The [dial-trust] gate rule below enforces the 99.4/312 landing.
const AGENT_DEFS = [
  // slug, kind, archetype, pairedWith, health, stats{compliancePct,loops,runs}, rework{used,budget}, inflight, state, versionNotes[]
  ['crud-orchestrator', 'maker', 'Maker', 'crud-compliance-checker', 'active', { compliancePct: 99.9, loops: 2, runs: 505 }, { used: 1, budget: 3 }, 2, 'running',
    ['cut the maker-checker handoff to a single envelope; loops dropped 3 to 2', 'added rework-budget guard so a third loop escalates instead of retrying silently']],
  ['entity-creation', 'maker', 'Maker', 'test-coverage-checker', 'active', { compliancePct: 99.1, loops: 2, runs: 96 }, { used: 0, budget: 3 }, 1, 'running',
    ['scaffolds Role and Permission entities with the CRUD stack ported from the invoice template']],
  ['migration-author', 'maker', 'Maker', 'crud-compliance-checker', 'active', { compliancePct: 99.6, loops: 3, runs: 120 }, { used: 2, budget: 3 }, 0, 'idle',
    ['emits reversible up/down pairs by default; legacy-column drops now require an explicit snapshot step']],
  ['api-contractor', 'maker', 'Maker', 'security-checker', 'active', { compliancePct: 99.4, loops: 2, runs: 96 }, { used: 1, budget: 3 }, 0, 'idle',
    ['generates REST handlers against the existing API surface; GraphQL path retired after CAST-412']],
  ['crud-compliance-checker', 'checker', 'Checker', 'crud-orchestrator', 'active', { compliancePct: 99.6, loops: 1, runs: 470 }, { used: 0, budget: 3 }, 1, 'running',
    ['rule set now flags M04 convention drift, S03 over-permissive typing, and R02 missing FK indexes']],
  ['test-coverage-checker', 'checker', 'Checker', 'entity-creation', 'checker-flagged', { compliancePct: 98.9, loops: 1, runs: 210 }, { used: 0, budget: 3 }, 0, 'idle',
    ['flagged itself: branch-coverage threshold drifted below the 90% gate on the coupon path']],
  ['security-checker', 'checker', 'Checker', 'api-contractor', 'active', { compliancePct: 99.4, loops: 1, runs: 175 }, { used: 0, budget: 3 }, 0, 'idle',
    ['adds an authz-boundary check to every endpoint that touches a permission table']],
  ['decision-recorder', 'maker', 'Decision', null, 'benched', { compliancePct: 100.0, loops: 1, runs: 96 }, { used: 0, budget: 3 }, 0, 'idle',
    ['writes ADR atoms with reversibility and revisit-if; never edits a record, supersedes it']],
  ['spike-runner', 'maker', 'Spike', null, 'active', { compliancePct: 97.8, loops: 1, runs: 64 }, { used: 0, budget: 3 }, 1, 'running',
    ['time-boxes probes and reports p95 only; extends a box once before forcing a verdict']],
  ['escalation-router', 'maker', 'Escalation', null, 'active', { compliancePct: 99.0, loops: 1, runs: 80 }, { used: 0, budget: 3 }, 0, 'idle',
    ['raises exactly three pre-framed options with an evidence pack; no pre-selected default']],
  ['onboarding-mentor', 'maker', 'Mentor', null, 'active', { compliancePct: 98.5, loops: 1, runs: 52 }, { used: 0, budget: 3 }, 0, 'idle',
    ['pairs a new hire with its checker and seeds the autonomy dial at balanced for the first goal']],
  ['repo-cartographer', 'maker', 'Mentor', null, 'benched', { compliancePct: 98.2, loops: 1, runs: 70 }, { used: 0, budget: 3 }, 0, 'idle',
    ['maps read paths before a migration; surfaced the one report still reading the legacy roles column']],
];

const agents = {};
let agentOffset = 60;
for (const [slug, kind, archetype, pairedWith, health, stats, rework, inflight, state, versionNotes] of AGENT_DEFS) {
  // newest version first; SHAs are faker filler (sanctioned), notes are authored changelog lines.
  const versions = versionNotes.map((note, i) => ({
    sha: sha(),
    at: t(agentOffset - i * 6),
    note,
  }));
  agents[slug] = {
    id: `agent-${slug}`,
    slug,
    kind,
    pairedWith,
    stats,
    autonomy: 'balanced',
    rework,
    inflight,
    state,
    archetype,
    health,
    versions,
    usage: { last_30d: faker.number.int({ min: 12, max: 240 }), avg_latency_ms: faker.number.int({ min: 90, max: 320 }) },
  };
  agentOffset += 7;
}

// runs-weighted trust aggregate over a goal's roster (single source: agents[].stats).
function aggregateTrust(slugs) {
  let totRuns = 0;
  let weighted = 0;
  for (const s of slugs) {
    const a = agents[s];
    totRuns += a.stats.runs;
    weighted += a.stats.compliancePct * a.stats.runs;
  }
  return { compliancePct: Math.round((weighted / totRuns) * 10) / 10, runs: totRuns };
}

// ───────────────────────────────────────────────────────────────────────────
// stageModels — 2c-OWNED region. ENCODED by Phase 2c (sp4) from the canonical derived vocabulary
// (docs/plan/product-revamp-diecast-stage-models.md §5). placeholder:false on all four families now;
// rich per-step objects inlined as plain JSON (no functions) per the file:// classic-script contract.
// (2a shipped the slot with placeholder:true watermarks; 2c rewrites it once — the one freeze
// exception. The step() helper is retired: derived steps carry full per-step shape, inlined.)
// NOTE: the literal word 'placeholder' is intentionally kept OUT of does/surfaceWhy so that
// `grep -c 'placeholder' org.js` still resolves to exactly the four `placeholder` family flags.
const stageModels = {
  feature: {
    placeholder: false,
    shape: 'segments',
    progression: 'linear-reentrant',
    steps: [
      { id: 'feat-01', label: 'Shape the Problem', does: 'Define problem + appetite + a rough solution + named rabbit-holes; write it up as a pitch/brief before betting', surface: 'doc', surfaceWhy: 'the shaped problem is a written artifact reviewed before commitment', artifacts: ['pitch/brief (appetite, rough solution, rabbit-holes)'], refs: ['shape-up', 'linear-method', 'design-docs-google'], evidence: null },
      { id: 'feat-02', label: 'Commit & Scope', does: 'Place a fixed-appetite bet on the pitch, then break the committed work into shippable issues', surface: 'board', surfaceWhy: 'the bet plus scoped issues live on a ticket board', artifacts: ['committed scope / issue board'], refs: ['shape-up', 'linear-method'], evidence: null },
      { id: 'feat-03', label: 'Design the Approach', shortLabel: 'Design Approach', does: 'Write a design doc / RFC capturing implementation strategy, alternatives, and trade-offs; resolve it in review threads', surface: 'doc', surfaceWhy: 'the design and its review are a document discussion, the org\'s decision memory', artifacts: ['design doc (alternatives + trade-offs)', 'review thread'], refs: ['design-docs-google', 'linear-method'], evidence: null },
      { id: 'feat-04', label: 'Build & Ship', does: 'Build in vertical slices and ship continuously within the fixed timebox/cycle', surface: 'pr-thread', surfaceWhy: 'slices land as reviewed, merged PRs', artifacts: ['shipped vertical slice / merged PR'], refs: ['shape-up', 'linear-method'], evidence: null },
      { id: 'feat-05', label: 'Show It\'s Done', does: 'Demonstrate completion via the diff plus an acceptance-evidence bundle (screenshots / proof shots / test summary)', surface: 'pr-thread', surfaceWhy: 'done is shown on the PR/report as evidence, not asserted', artifacts: ['acceptance-evidence bundle (diff + screenshots + summary)'], refs: ['linear-method', 'proofshot', 'devin-cu'], evidence: 'E1' },
    ],
  },
  debug: {
    placeholder: false,
    shape: 'loop',
    loop: { over: ['dbg-02', 'dbg-03', 'dbg-04'], budget: 3 },
    steps: [
      { id: 'dbg-01', label: 'Reproduce Reliably', does: 'Move from saw-it-a-few-times to an on-demand, consistent reproduction (special care for intermittents)', surface: 'ledger', surfaceWhy: 'the repro recipe is the first investigation-ledger entry', artifacts: ['reliable reproduction (recorded repro steps)'], refs: ['agans', 'julia-evans'], evidence: null },
      { id: 'dbg-02', label: 'Form a Hypothesis', does: 'Invent a falsifiable hypothesis for the failure cause, consistent with the observations so far', surface: 'ledger', surfaceWhy: 'each candidate cause is logged in the case file', artifacts: ['hypothesis entry (the accusation)'], refs: ['zeller', 'uxmag-detective'], evidence: null },
      { id: 'dbg-03', label: 'Run an Experiment', does: 'Quit thinking and look: change one thing / bisect, observe actual behavior with tools, get data', surface: 'ledger', surfaceWhy: 'the experiment and what it showed are logged', artifacts: ['experiment result + trace/instrumentation'], refs: ['agans', 'zeller'], evidence: null },
      { id: 'dbg-04', label: 'Log Confirm/Refute', does: 'Record prediction-vs-observed per hypothesis; mark confirmed/refuted; a refuted prediction spawns the next hypothesis', surface: 'ledger', surfaceWhy: 'the confirmed/refuted ledger is the loop\'s memory', artifacts: ['confirm/refute evidence ledger'], refs: ['hypothesizer', 'uxmag-detective'], evidence: 'E2' },
      { id: 'dbg-05', label: 'Prove the Fix', does: 'Prove the fix by making the failure recur, then disappear - a red-to-green repro (fails, then the same case passes)', surface: 'pr-thread', surfaceWhy: 'the proof lands on the fix PR/report', artifacts: ['red-to-green repro (failing then passing case)'], refs: ['agans', 'undo-replay'], evidence: 'E3' },
    ],
  },
  spike: {
    placeholder: false,
    shape: 'timebox',
    timebox: { budget: '3h' },
    steps: [
      { id: 'spk-01', label: 'Frame the Question', does: 'Identify the single riskiest unknown and pose it as one answerable technical question', surface: 'memo', surfaceWhy: 'the question opens the spike memo under its budget', artifacts: ['risk-question memo'], refs: ['xp-spike', 'mike-bowler'], evidence: null },
      { id: 'spk-02', label: 'Probe Options', does: 'Build quick, throwaway probes to answer the question - quick-and-dirty, explicitly disposable', surface: 'memo', surfaceWhy: 'probe attempts are logged in the memo, code is dropped', artifacts: ['probes-tried list (throwaway)'], refs: ['xp-spike', 'mike-bowler'], evidence: null },
      { id: 'spk-03', label: 'Evaluate Findings', does: 'Evaluate the probes; keep the learning, discard the code; at any point decide done-enough', surface: 'memo', surfaceWhy: 'findings accrue in the memo against the burning budget', artifacts: ['findings notes'], refs: ['xp-spike', 'agilemania-spike'], evidence: null },
      { id: 'spk-04', label: 'Land the Verdict', does: 'Write a one-line answer and link it to the downstream decision it informs (with a revisit-if trip-wire)', surface: 'memo', surfaceWhy: 'the verdict closes the memo and points at its decision record', artifacts: ['verdict card (spike_ref + revisit_if)'], refs: ['mike-bowler', 'agilemania-spike', 'adr-nygard'], evidence: 'E4' },
    ],
  },
  data: {
    placeholder: false,
    shape: 'pipeline',
    steps: [
      { id: 'data-01', label: 'Import Sources', does: 'Pull the sources (file / DB / API) that bear on the question into a working frame', surface: 'notebook', surfaceWhy: 'ingestion happens in the analysis notebook', artifacts: ['loaded dataset'], refs: ['r4ds', 'dbt-analyst'], evidence: null },
      { id: 'data-02', label: 'Tidy & Validate', does: 'Tidy to one-variable-per-column / one-observation-per-row, then sanity-check: are you telling me the truth? - cross-examine outliers before trusting', surface: 'notebook', surfaceWhy: 'cleaning and the sanity checks are notebook cells/charts', artifacts: ['cleaned + validated frame (sanity notes)'], refs: ['r4ds', 'data-sanity'], evidence: null },
      { id: 'data-03', label: 'Transform / Wrangle', shortLabel: 'Transform', does: 'Narrow observations, create new variables, compute summary statistics', surface: 'notebook', surfaceWhy: 'transforms are notebook cells', artifacts: ['derived variables / summary tables'], refs: ['r4ds', 'dbt-analyst'], evidence: null },
      { id: 'data-04', label: 'Explore (Viz<->Model)', shortLabel: 'Explore', does: 'Iterate visualize and model many times to find the answer; disposable charts also catch problems early (visualize-to-validate)', surface: 'notebook', surfaceWhy: 'the explore loop is interactive charting in the notebook', artifacts: ['exploratory charts + candidate models'], refs: ['r4ds', 'looks-good-correll'], evidence: null },
      { id: 'data-05', label: 'Publish + Provenance', shortLabel: 'Publish', does: 'Publish a clean narrative report (viz as the headline) distinct from the working notebook, with source/transform lineage exposed on demand', surface: 'pr-thread', surfaceWhy: 'the published report is the shareable deliverable', artifacts: ['rendered report + provenance drill-in'], refs: ['r4ds', 'hex-deepnote', 'atlan-provenance'], evidence: 'E5' },
    ],
  },
};

// ───────────────────────────────────────────────────────────────────────────
// decisions — playbook-05 ADR atoms (snake_case names verbatim). 5 per goal, exactly one L3.
// L3 atoms carry exactly 3 ranked options (chosen:false at rest) + an evidence pack
// (what_i_want, what_i_tried). Reversals are NEW records (supersedes/superseded_by), never edits.
// Content is THIN here ('[2a.2]') — 2a.2 authors the full bodies; the shape & gate are locked now.
// ───────────────────────────────────────────────────────────────────────────
function atom(o) {
  const base = {
    id: o.id,
    goal_slug: o.goal_slug,
    phase: o.phase ?? 'execution',
    title: o.title,
    reversibility: o.reversibility,
    rationale: o.rationale ?? '[2a.2] rationale',
    options_considered: o.options_considered ?? [],
    consequences: o.consequences ?? '[2a.2] consequences',
    revisit_if: o.revisit_if ?? '[2a.2] revisit condition',
    originating_agent: o.originating_agent,
    author_type: o.author_type ?? 'agent',
    timestamp: o.timestamp,
    status: o.status ?? 'accepted',
    supersedes: o.supersedes ?? null,
    superseded_by: o.superseded_by ?? null,
    spike_ref: o.spike_ref ?? null,
    influenced: o.influenced ?? [],
    diff: o.diff,
  };
  if (o.reversibility === 'L3') {
    base.what_i_want = o.what_i_want ?? '[2a.2] what I want';
    base.what_i_tried = o.what_i_tried ?? '[2a.2] what I tried';
  }
  return base;
}

// exactly-3 ranked options for an L3 (none chosen at rest). Each pair is [label, consequence];
// the consequence is what the human is choosing between - the 10-30s decide shape from playbook 05.
function rankedOptions(pairs) {
  return pairs.map(([label, consequence], i) => ({ label, consequence, rank: i + 1, chosen: false }));
}

const decisions = [
  // ── CAST-412 feature (6 atoms; superseded L1 pair -01/-02; L3 = -04 on CAST-417; dial-demo L2 = -06) ──
  atom({
    id: 'DEC-CAST-412-01', goal_slug: CANON.feature.id, phase: 'requirements', reversibility: 'L1',
    title: 'Use GraphQL for the RBAC permissions endpoint',
    rationale: 'A single GraphQL query could fetch a role and its nested permissions in one round trip, which read well for the permissions-matrix screen.',
    options_considered: [
      { option: 'GraphQL endpoint', consequence: 'one query for nested permissions; a new schema surface to maintain', chosen: true },
      { option: 'REST endpoints', consequence: 'matches the existing API surface; multiple calls for nested reads', chosen: false },
    ],
    consequences: 'Stood up a GraphQL schema and resolver for the permissions tree.',
    revisit_if: 'If the RBAC reads turn out flat enough that REST matches the existing API surface with no extra round trips.',
    originating_agent: 'api-contractor', timestamp: t(70), status: 'superseded', superseded_by: 'DEC-CAST-412-02',
    diff: 'endpoint style: (none) → GraphQL',
  }),
  atom({
    id: 'DEC-CAST-412-02', goal_slug: CANON.feature.id, phase: 'requirements', reversibility: 'L1',
    title: 'Chose REST over GraphQL for the RBAC endpoint - matches existing API surface',
    rationale: 'The RBAC reads are flat (a role maps to a permissions list), so REST against the existing API surface needs no new schema and adds no round trips.',
    options_considered: [
      { option: 'GraphQL endpoint', consequence: 'one query for nested permissions; a new schema surface to maintain', chosen: false },
      { option: 'REST endpoints', consequence: 'matches the existing API surface; no new schema', chosen: true },
    ],
    consequences: 'Retired the GraphQL resolver; permissions ship as REST handlers on the existing surface.',
    revisit_if: 'If a later screen needs deeply nested permission graphs that REST would over-fetch.',
    originating_agent: 'api-contractor', timestamp: t(95), supersedes: 'DEC-CAST-412-01', influenced: ['DEC-CAST-412-01'],
    diff: 'endpoint style: GraphQL → REST',
  }),
  atom({
    id: 'DEC-CAST-412-03', goal_slug: CANON.feature.id, phase: 'execution', reversibility: 'L2',
    title: `Classify ${CANON.feature.id} as bug, not feature`,
    rationale: 'The failing behavior is a regression from the v4.2 RBAC migration, not new scope, so it routes to the debug loop and skips a planning re-estimate.',
    options_considered: [
      { option: 'Treat as feature', consequence: 'new FR plus an estimate; re-enters planning', chosen: false },
      { option: 'Treat as bug', consequence: 'hotfix lane, no re-scope; routes to the debug-loop canvas', chosen: true },
    ],
    consequences: `Routes ${CANON.feature.id} to the debug-loop canvas; skips the planning re-estimate.`,
    revisit_if: 'If the regression bisect lands outside the v4.2 migration commit range.',
    originating_agent: 'crud-compliance-checker', timestamp: t(532), influenced: [CANON.debug.id],
    diff: 'classification: feature → bug',
  }),
  atom({
    id: 'DEC-CAST-412-04', goal_slug: CANON.feature.id, phase: 'execution', reversibility: 'L3', originating_agent: 'migration-author', timestamp: t(300),
    title: `Migrate roles schema (drops legacy roles column) - ${CANON.escalationTicket.id}`,
    rationale: 'Dropping the legacy roles column is irreversible on prod data, and one report still reads it, so the path has to protect that read before any drop.',
    options_considered: rankedOptions([
      ['Additive migration, keep the legacy column for 90 days', 'reversible; carries a dead column and a cleanup task for a quarter'],
      ['Drop the column now with a backup snapshot', 'smallest schema, but irreversible on prod; restore means a full snapshot reload'],
      ['Spike a dual-write window before dropping', 'safest cutover; costs a spike and a temporary dual-write path'],
    ]),
    consequences: `The roles-column drop is held as the single hard stop on ${CANON.escalationTicket.id} until the owner picks a path.`,
    revisit_if: 'If the one report still reading the legacy column is retired or repointed.',
    influenced: [CANON.escalationTicket.id],
    diff: 'roles schema: legacy column retained → migration pending (L3 hard stop)',
    what_i_want: 'a path to drop the legacy roles column without breaking checkout or the one report still reading it',
    what_i_tried: 'mapped every read of the legacy column; repo-cartographer found one report still bound to it, so a clean drop is not yet safe',
  }),
  atom({
    id: 'DEC-CAST-412-05', goal_slug: CANON.feature.id, phase: 'planning', reversibility: 'L1',
    title: 'Reuse the shared auth middleware for permission checks',
    rationale: 'The shared auth middleware already resolves the caller, so hanging permission checks off it avoids standing up a parallel auth path.',
    consequences: 'Permission checks live in the shared middleware; this couples checkout to that middleware\'s behavior.',
    revisit_if: 'If a caller needs a permission rule the shared middleware cannot express without a fork.',
    originating_agent: 'crud-orchestrator', timestamp: t(120),
    diff: 'permission check: new layer → reuse shared middleware',
  }),
  atom({
    id: 'DEC-CAST-412-06', goal_slug: CANON.feature.id, phase: 'planning', reversibility: 'L2',
    title: 'Split FR-014 into routing + recording',
    rationale: 'FR-014 bundled two independent concerns; splitting routing from recording lets each ship and be verified on its own lane.',
    options_considered: [
      { option: 'Keep FR-014 as one requirement', consequence: 'one ticket, but routing and recording block each other', chosen: false },
      { option: 'Split into FR-014a routing and FR-014b recording', consequence: 'two lanes that ship independently', chosen: true },
    ],
    consequences: 'FR-014 becomes FR-014a (routing) and FR-014b (recording).',
    revisit_if: 'If routing and recording end up sharing enough state that one ticket is simpler.',
    originating_agent: 'decision-recorder', timestamp: t(185),
    diff: 'FR-014 → FR-014a, FR-014b',
  }),

  // ── CAST-431 debug (5 atoms; L3 = -03 shared-auth-middleware fix scope) ──
  atom({
    id: 'DEC-CAST-431-01', goal_slug: CANON.debug.id, phase: 'execution', reversibility: 'L1',
    title: 'Ruled out hypothesis A (cache) - repro persists with cache off',
    rationale: 'Reran the coupon-apply repro with the cache disabled; the 500 still fires, so the cache is not the cause.',
    consequences: 'Drops hypothesis A; iteration 1 of 3 closes on the cache path.',
    revisit_if: 'If the 500 stops reproducing once the cache layer is reintroduced under load.',
    originating_agent: 'crud-orchestrator', timestamp: t(140),
    diff: 'hypothesis A (cache): open → refuted',
  }),
  atom({
    id: 'DEC-CAST-431-02', goal_slug: CANON.debug.id, phase: 'execution', reversibility: 'L2',
    title: 'Switch the repro from the unit harness to the integration harness',
    rationale: 'The unit harness stubs the auth middleware, which is exactly where the fault seems to live; the integration harness exercises the real middleware.',
    options_considered: [
      { option: 'Stay on the unit harness', consequence: 'fast, but stubs the suspect middleware', chosen: false },
      { option: 'Move to the integration harness', consequence: 'slower, but exercises the real shared auth path', chosen: true },
    ],
    consequences: 'The repro now runs against the integration harness, where the 500 reproduces with the real middleware.',
    revisit_if: 'If the integration repro turns out to depend on a fixture the unit harness can mimic.',
    originating_agent: 'test-coverage-checker', timestamp: t(160), influenced: ['DEC-CAST-412-05'],
    diff: 'repro harness: unit → integration',
  }),
  atom({
    id: 'DEC-CAST-431-03', goal_slug: CANON.debug.id, phase: 'execution', reversibility: 'L3', originating_agent: 'crud-orchestrator', timestamp: t(190),
    title: 'Scope the shared-auth-middleware fix - it changes behavior for 4 other callers',
    rationale: 'The root cause is a null-role path in the shared auth middleware introduced by the v4.2 RBAC migration; any fix there changes behavior for 4 other services.',
    options_considered: rankedOptions([
      ['Narrow fix behind a feature flag', 'unblocks coupon-apply now; leaves the shared bug live for other callers until the flag rolls out'],
      ['Fix the middleware and notify the 4 owners', 'one correct fix; needs sign-off from 4 service owners before it ships'],
      ['Escalate to the auth team', 'the right owner for shared middleware; adds a handoff and waits on their queue'],
    ]),
    consequences: 'The fix is held as the debug flow\'s single hard stop until the scope is chosen.',
    revisit_if: 'If the null-role path turns out to be unreachable by the other 4 callers in practice.',
    influenced: ['DEC-CAST-412-05'],
    diff: 'fix scope: shared middleware (4 callers) → pending (L3 hard stop)',
    what_i_want: 'stop the coupon-apply 500s without changing behavior for the other 4 services on the shared middleware',
    what_i_tried: 'traced the null-role path the v4.2 RBAC migration introduced; confirmed 4 other callers reach the same code',
  }),
  atom({
    id: 'DEC-CAST-431-04', goal_slug: CANON.debug.id, phase: 'execution', reversibility: 'L1',
    title: 'Add a regression guard for null-role coupon requests',
    rationale: 'A null role on a coupon-apply request is the exact trigger, so a guard pins the regression and makes it fail loud instead of returning a 500.',
    consequences: 'Adds a guard on the null-role coupon case; it fails loud rather than 500.',
    revisit_if: 'If the role backfill makes null-role requests impossible and the guard becomes dead weight.',
    originating_agent: 'test-coverage-checker', timestamp: t(210),
    diff: 'guard: none → null-role coupon case',
  }),
  atom({
    id: 'DEC-CAST-431-05', goal_slug: CANON.debug.id, phase: 'execution', reversibility: 'L2',
    title: 'Backfill the missing role rows from the v4.2 migration',
    rationale: 'The v4.2 migration left some accounts without a role row; backfilling removes the null-role trigger at the source rather than only guarding against it.',
    options_considered: [
      { option: 'Guard only', consequence: 'stops the 500 but leaves accounts roleless', chosen: false },
      { option: 'Backfill the missing role rows', consequence: 'removes the trigger at the source; a one-time data migration', chosen: true },
    ],
    consequences: 'Backfills role rows for the accounts the v4.2 migration missed.',
    revisit_if: 'If the backfill query finds accounts whose correct role is ambiguous.',
    originating_agent: 'migration-author', timestamp: t(230),
    diff: 'data: missing role rows → backfilled',
  }),

  // ── CAST-452 spike (5 atoms; L3 = -03, carries spike_ref <-> E4) ──
  atom({
    id: 'DEC-CAST-452-01', goal_slug: CANON.spike.id, phase: 'research', reversibility: 'L1',
    title: 'Time-box the latency spike to 2h and measure p95 only',
    rationale: 'The only question that gates the feature is whether the vendor SDK fits the 200ms p95 budget; a 2h box measuring p95 answers it without a full benchmark.',
    consequences: 'The spike is scoped to a 2h box, p95 only.',
    revisit_if: 'If 2h proves too short to get a stable p95.',
    originating_agent: 'spike-runner', timestamp: t(250),
    diff: 'spike box: open → 2h, p95 only',
  }),
  atom({
    id: 'DEC-CAST-452-02', goal_slug: CANON.spike.id, phase: 'research', reversibility: 'L2',
    title: 'Spike inconclusive at 2h - extend once to 3h',
    rationale: 'At 2h the p95 had not stabilized; one 3h extension gets a defensible number, and the budget allows exactly one extension.',
    options_considered: [
      { option: 'Call it at 2h', consequence: 'ships an unstable p95; risks a wrong go/no-go', chosen: false },
      { option: 'Extend once to 3h', consequence: 'one more hour for a stable p95; uses the single allowed extension', chosen: true },
    ],
    consequences: 'The timebox extends from 2h to 3h; the one allowed extension is used.',
    revisit_if: 'If p95 is still drifting at 3h, the spike fails closed rather than extending again.',
    originating_agent: 'spike-runner', timestamp: t(270),
    diff: 'timebox: 2h → 3h',
  }),
  atom({
    id: 'DEC-CAST-452-03', goal_slug: CANON.spike.id, phase: 'research', reversibility: 'L3', originating_agent: 'spike-runner', timestamp: t(300),
    title: 'Vendor SDK adds 180ms p95 against a 200ms budget - adopt, self-host, or renegotiate?',
    rationale: 'Measured p95 is 180ms, inside the 200ms budget but with almost no headroom; this gates the feature go/no-go, so the call is not the agent\'s to make alone.',
    options_considered: rankedOptions([
      ['Proceed and accept the 180ms', 'ships now with about 20ms of headroom against the 200ms budget'],
      ['Self-host the call', 'reclaims latency headroom; costs build and ongoing maintenance'],
      ['Renegotiate the budget with @you', 'keeps the SDK; needs an explicit budget change from the owner'],
    ]),
    consequences: 'The go/no-go is held as the spike\'s single hard stop, spike_ref-linked to the E4 verdict.',
    revisit_if: 'If a newer SDK build or a warm-path change moves p95 clear of 200ms.',
    spike_ref: 'E4-CAST-452', influenced: [CANON.feature.id],
    diff: 'vendor SDK: unmeasured → +180ms p95 borderline (L3 hard stop)',
    what_i_want: 'a checkout SDK that fits the 200ms p95 budget with real headroom',
    what_i_tried: 'measured p95 across 3 warm-cache runs on a pinned SDK build; landed at 180ms, inside budget but tight',
  }),
  atom({
    id: 'DEC-CAST-452-04', goal_slug: CANON.spike.id, phase: 'research', reversibility: 'L1',
    title: 'Measure p95 under warm-cache conditions only',
    rationale: 'Production checkout runs warm, so a cold-cache p95 would overstate the latency the feature actually sees.',
    consequences: 'The p95 numbers are warm-cache; cold-start is out of scope for the budget call.',
    revisit_if: 'If a meaningful share of checkout traffic hits a cold cache.',
    originating_agent: 'spike-runner', timestamp: t(282),
    diff: 'measurement: cold + warm → warm-cache only',
  }),
  atom({
    id: 'DEC-CAST-452-05', goal_slug: CANON.spike.id, phase: 'research', reversibility: 'L1',
    title: 'Pin the SDK version used for the measurement',
    rationale: 'A floating SDK version would make the 180ms number unreproducible; pinning it ties the verdict to a specific build.',
    consequences: 'The 180ms p95 is recorded against a pinned SDK build.',
    revisit_if: 'If the vendor ships a version with a different latency profile.',
    originating_agent: 'decision-recorder', timestamp: t(290),
    diff: 'sdk version: floating → pinned for measurement',
  }),

  // ── CAST-461 data (5 atoms; L3 = -03, 8% source disagreement) ──
  atom({
    id: 'DEC-CAST-461-01', goal_slug: CANON.data.id, phase: 'synthesize', reversibility: 'L1',
    title: 'Exclude the 1.2% null-region rows from the cohort - documented in method',
    rationale: 'Rows with a null region cannot be attributed to a segment; at 1.2% they do not move the headline, and dropping them keeps the segment split clean.',
    consequences: 'The cohort excludes null-region rows; the exclusion is noted in the method section.',
    revisit_if: 'If the null-region share grows past a few percent or clusters in one segment.',
    originating_agent: 'repo-cartographer', timestamp: t(320),
    diff: 'cohort: all rows → exclude 1.2% null-region',
  }),
  atom({
    id: 'DEC-CAST-461-02', goal_slug: CANON.data.id, phase: 'synthesize', reversibility: 'L2',
    title: 'Choose median over mean for the skewed per-account set',
    rationale: 'Per-account revenue is right-skewed by a few large accounts; the median represents the typical account, while the mean tracks the outliers.',
    options_considered: [
      { option: 'Report the mean', consequence: 'pulled up by a few large accounts', chosen: false },
      { option: 'Report the median', consequence: 'represents the typical account; less sensitive to outliers', chosen: true },
    ],
    consequences: 'Per-account figures report the median; the mean is footnoted.',
    revisit_if: 'If the question shifts to total revenue, where the mean times the count is what matters.',
    originating_agent: 'decision-recorder', timestamp: t(340),
    diff: 'central tendency: mean → median',
  }),
  atom({
    id: 'DEC-CAST-461-03', goal_slug: CANON.data.id, phase: 'synthesize', reversibility: 'L3', originating_agent: 'decision-recorder', timestamp: t(360),
    title: 'Two sources disagree on Q2 revenue by 8% - which one drives the headline?',
    rationale: 'The finance DB and the billing export are 8% apart on Q2, and the dip\'s headline depends on which one the chart trusts, so the call is escalated rather than silently chosen.',
    options_considered: rankedOptions([
      ['Use the source-of-record (finance DB)', 'one clean headline; footnotes an unexplained 8% billing gap'],
      ['Show both with a reconciliation note', 'honest about the gap; a busier chart and a softer headline'],
      ['Flag for analyst review before publishing', 'most defensible; delays the report on an analyst handoff'],
    ]),
    consequences: 'The headline source is held as the data flow\'s single hard stop until the owner picks.',
    revisit_if: 'If a reconciled third source closes the 8% gap on its own.',
    diff: 'Q2 revenue: two sources 8% apart → reconciliation pending (L3 hard stop)',
    what_i_want: 'one defensible Q2 revenue number to attribute the dip to a segment',
    what_i_tried: 'aligned the date windows and excluded refunds; an 8% gap between the finance DB and the billing export still persists',
  }),
  atom({
    id: 'DEC-CAST-461-04', goal_slug: CANON.data.id, phase: 'synthesize', reversibility: 'L1',
    title: 'Exclude refunded orders from the segment totals',
    rationale: 'A refunded order is not realized revenue, so counting it inflates the segment that generated the refund.',
    consequences: 'Segment totals are net of refunds.',
    revisit_if: 'If the question becomes gross bookings rather than realized revenue.',
    originating_agent: 'repo-cartographer', timestamp: t(335),
    diff: 'totals: gross → net of refunds',
  }),
  atom({
    id: 'DEC-CAST-461-05', goal_slug: CANON.data.id, phase: 'synthesize', reversibility: 'L2',
    title: 'Annotate each series point with its source provenance',
    rationale: 'With two disagreeing sources in play, every plotted point has to say which source it came from so the reconciliation stays auditable.',
    options_considered: [
      { option: 'Plot bare values', consequence: 'a cleaner chart; hides which source each point came from', chosen: false },
      { option: 'Annotate each point with its source', consequence: 'auditable; every point carries finance-vs-billing provenance', chosen: true },
    ],
    consequences: 'Each series point carries a finance-or-billing source tag.',
    revisit_if: 'If the two sources are reconciled into one and provenance no longer differs.',
    originating_agent: 'decision-recorder', timestamp: t(350),
    diff: 'series: bare values → source-annotated',
  }),
];

// ───────────────────────────────────────────────────────────────────────────
// goals — 4, keyed by goal id. agent_roster (added field, documented) drives the trust aggregate.
// artifacts / work_stream items reference stage steps by step id; spine_state.current is a step id.
// ───────────────────────────────────────────────────────────────────────────
const goalDecisionIds = (goalId) => decisions.filter((a) => a.goal_slug === goalId).map((a) => a.id);

// featureRoster = the three makers STAFFED on CAST-412's RBAC build. Their aggregate is the dial
// trust stat (99.4% / 312 runs) - see the AGENT_DEFS note and the [dial-trust] gate rule.
// crud-orchestrator (orchestrator, 505 lifetime runs) and crud-compliance-checker drive the work
// and the marketplace card, but are not in the dial roster (their lifetime runs exceed 312).
const featureRoster = ['entity-creation', 'migration-author', 'api-contractor'];
const debugRoster = ['crud-orchestrator', 'crud-compliance-checker', 'test-coverage-checker'];
const spikeRoster = ['spike-runner', 'api-contractor'];
const dataRoster = ['decision-recorder', 'repo-cartographer'];

const goals = {
  'CAST-412': {
    family: 'feature',
    title: CANON.feature.title,
    status: 'in_review',
    spine_state: { current: 'feat-04' },
    agent_roster: featureRoster,
    chain_position: 'run',
    // nudge kept verbatim from Phase 1's appState stub (em dash + apostrophe match) so 2a.3's
    // swap from the inline stub to this spine value is invisible in the demo.
    nudge: { who: 'Guide', do: "Review CAST-412's PR", why: 'checker flagged R02 — unblocks 2 queued tasks' },
    artifacts: [
      {
        id: 'art-reqs-412', type: 'requirements-doc', step: 'feat-01', version: 'v2',
        caption: 'RBAC checkout requirements, v2 - reclassified to a bug after the regression bisect.',
        // US7 thin data (ids + named values only; Phase 5c authors the document body).
        us7: {
          classification_pill: 'bug',
          change_summary: 'v1 → v2: reclassified feature → bug; FR-014 split into FR-014a (routing) + FR-014b (recording).',
          comments: [
            {
              id: 'cmt-412-1', author: '@priya', anchor: 'FR-014', status: 'resolved',
              text: 'Routing and recording are two concerns - should these be separate requirements?',
              opened_at: t(150), resolved_at: t(186),
            },
          ],
          writeback_notice: 'Requirements updated from planning - synced to your PM tool.',
        },
      },
      { id: 'art-plan-412', type: 'plan-doc', step: 'feat-02', caption: 'Phase plan for the RBAC permissions work, decomposed into the entity, endpoint, and migration lanes.' },
      { id: 'art-tickets-412', type: 'tickets', step: 'feat-03', caption: 'The five-ticket build lane for CAST-412, one item still owned by @you.' },
      { id: 'art-e1-412', type: 'e1-panel', step: 'feat-04', caption: 'Acceptance panel for the permissions PR - test summary plus the checker run.' },
    ],
    work_stream: [
      { id: 'ws-412-1', label: 'Scaffold the Role and Permission entities with the CRUD stack', assignee: 'entity-creation', step: 'feat-03', kind: 'ticket' },
      { id: 'ws-412-2', label: 'Generate the REST permissions handlers on the existing API surface', assignee: 'api-contractor', step: 'feat-03', kind: 'ticket' },
      { id: 'ws-412-3', label: 'Author the roles-schema migration (held at the L3 stop)', assignee: 'migration-author', step: 'feat-04', kind: 'ticket' },
      { id: 'ws-412-4', label: 'Run the maker-checker loop on the permissions PR', assignee: 'crud-orchestrator', step: 'feat-04', kind: 'ticket' },
      { id: 'ws-412-5', label: "Review CAST-412's PR", assignee: '@you', step: 'feat-05', kind: 'manual' },
    ],
    evidence: {
      E1: {
        id: 'E1-CAST-412', kind: 'E1', confidence: '●', test_summary: CANON.testSummary, coverage_delta: '+2.1%', pr: CANON.pr,
        checker_rows: [
          { code: 'M04', label: CANON.ruleCodes.M04, state: 'resolved', glyph: '●' },
          { code: 'S03', label: CANON.ruleCodes.S03, state: 'resolved', glyph: '●' },
          { code: 'R02', label: CANON.ruleCodes.R02, state: 'flagged', glyph: '◐' },
        ],
        shots: [{
          ref: 'assets/e1-acceptance.png',
          alt: 'Acceptance panel for the RBAC permissions PR: a green test summary above three checker rows.',
          caption: `${CANON.canonicalChecker} on ${CANON.pr}: M04 and S03 resolved, R02 still flagged.`,
        }],
      },
    },
    decisions: goalDecisionIds('CAST-412'),
    autonomy: { value: 'balanced', trust: aggregateTrust(featureRoster) },
  },
  'CAST-431': {
    family: 'debug',
    title: CANON.debug.title,
    status: 'in_progress',
    spine_state: { current: 'dbg-02', iter: { current: 2, budget: 3 } },
    agent_roster: debugRoster,
    chain_position: 'orchestrate',
    nudge: { who: 'Guide', do: 'Confirm the coupon-path repro', why: 'hypothesis H3 confirmed - ready to scope the fix' },
    artifacts: [{ id: 'art-ledger-431', type: 'investigation-ledger', step: 'dbg-02', caption: 'Investigation ledger: three hypotheses, two refuted, H3 confirmed on the integration harness.' }],
    work_stream: [
      { id: 'ws-431-1', label: 'Experiment: disable the cache and rerun the coupon repro (H1)', assignee: 'crud-orchestrator', step: 'dbg-03', kind: 'experiment' },
      { id: 'ws-431-2', label: 'Experiment: rerun on the integration harness with the real middleware (H3)', assignee: 'test-coverage-checker', step: 'dbg-03', kind: 'experiment' },
      { id: 'ws-431-3', label: 'Backfill the missing role rows from the v4.2 migration', assignee: 'migration-author', step: 'dbg-04', kind: 'ticket' },
    ],
    evidence: {
      E2: {
        id: 'E2-CAST-431', kind: 'E2', confidence: '●',
        hypotheses: [
          { id: 'H1', verdict: 'refuted', prediction: 'If a stale cached coupon serves the 500, disabling the cache stops it.', observation: 'With the cache off, the 500 still fires on coupon apply.' },
          { id: 'H2', verdict: 'refuted', prediction: 'If the coupon validator rejects the code, the request 400s, not 500s.', observation: 'The validator returns a clean 400; the 500 comes later in the request.' },
          { id: 'H3', verdict: 'confirmed', prediction: 'If a null role reaches the shared auth middleware, the permission check throws.', observation: 'On the integration harness, a null-role account throws in the shared middleware - that is the 500.' },
        ],
      },
      E3: {
        id: 'E3-CAST-431', kind: 'E3', confidence: '●',
        repro: 'test_coupon_apply_null_role_500',
        red: 'AuthMiddlewareError: role is null (HTTP 500) at apply_coupon',
        green: 'test_coupon_apply_null_role_500 passed - returns HTTP 422 with a typed error',
      },
    },
    decisions: goalDecisionIds('CAST-431'),
    autonomy: { value: 'balanced', trust: aggregateTrust(debugRoster) },
  },
  'CAST-452': {
    family: 'spike',
    title: CANON.spike.title,
    status: 'in_progress',
    spine_state: { current: 'spk-03', timebox_used: '1h40m' },
    agent_roster: spikeRoster,
    chain_position: 'research',
    nudge: { who: 'Guide', do: 'Decide on the vendor SDK', why: 'p95 measured at 180ms - borderline against the 200ms budget' },
    artifacts: [{ id: 'art-memo-452', type: 'memo', step: 'spk-03', caption: 'Spike memo: vendor SDK p95 over three warm-cache runs, against the 200ms budget.' }],
    work_stream: [
      { id: 'ws-452-1', label: 'Probe the SDK p95 under warm cache (2h box)', assignee: 'spike-runner', step: 'spk-02', kind: 'probe' },
      { id: 'ws-452-2', label: 'Re-probe p95 after the one-time 3h extension', assignee: 'spike-runner', step: 'spk-03', kind: 'probe' },
    ],
    evidence: {
      E4: {
        id: 'E4-CAST-452', kind: 'E4',
        verdict: 'adds 180ms p95 - borderline', confidence: '◐',
        budget_ms: 200, p95_ms: 180,
        atom_ref: 'DEC-CAST-452-03',
        caption: 'p95 holds at ~180ms across three warm-cache runs - inside the 200ms budget, but tight.',
        data_points: [
          { label: 'p95 run 1 (warm)', ms: 178 },
          { label: 'p95 run 2 (warm)', ms: 181 },
          { label: 'p95 run 3 (warm)', ms: 180 },
        ],
      },
    },
    decisions: goalDecisionIds('CAST-452'),
    autonomy: { value: 'balanced', trust: aggregateTrust(spikeRoster) },
  },
  'CAST-461': {
    family: 'data',
    title: CANON.data.title,
    status: 'in_progress',
    spine_state: { current: 'data-03' },
    agent_roster: dataRoster,
    chain_position: 'synthesize',
    nudge: { who: 'Guide', do: 'Reconcile the two revenue sources', why: 'finance DB and billing export disagree by 8% on Q2' },
    artifacts: [
      { id: 'art-notebook-461', type: 'notebook', step: 'data-03', caption: 'Analysis notebook: Q2 revenue by acquisition segment, computed from both sources.' },
      { id: 'art-report-461', type: 'report', step: 'data-04', version: 'v1', pending_version: 'v2', caption: 'Draft report v1 - the headline is blocked on the 8% source reconciliation; v2 lands once the L3 source call is made.' },
    ],
    work_stream: [
      { id: 'ws-461-1', label: 'Align the date windows across the finance DB and the billing export', assignee: 'decision-recorder', step: 'data-02', kind: 'cell' },
      { id: 'ws-461-2', label: 'Compute per-segment Q2 revenue from both sources', assignee: 'repo-cartographer', step: 'data-03', kind: 'cell' },
    ],
    evidence: {
      E5: {
        id: 'E5-CAST-461', kind: 'E5', gap: '8%', confidence: '◐', unit: '$k',
        sources: ['finance DB', 'billing export'],
        // Hardcoded canonical series (faker NEVER supplies a headline number): billing totals 2,803k vs
        // finance 2,595k => +8.0% (208/2595), the gap holding across all four segments.
        series: [
          { segment: 'new', finance: 412, billing: 446 },
          { segment: 'returning', finance: 905, billing: 951 },
          { segment: 'reactivated', finance: 188, billing: 205 },
          { segment: 'enterprise', finance: 1090, billing: 1201 },
        ],
        reconciliation_note: 'Finance DB totals Q2 at 2,595k; the billing export totals 2,803k - an 8% gap that holds across all four segments. The headline is pending the L3 source call.',
      },
    },
    decisions: goalDecisionIds('CAST-461'),
    autonomy: { value: 'balanced', trust: aggregateTrust(dataRoster) },
  },
};

// ───────────────────────────────────────────────────────────────────────────
// board — columns + tickets (every assignee resolves to a human/agent/guide slug).
// ───────────────────────────────────────────────────────────────────────────
const board = {
  columns: ['Backlog', 'In progress', 'In review', 'Done'],
  note: 'publishes INTO your PM tool',
  tickets: [
    { id: 'CAST-405', title: 'Seed the Permission lookup table', column: 'Done', assignee: 'migration-author', inflight: false },
    { id: 'CAST-408', title: 'Role CRUD endpoints', column: 'Done', assignee: 'entity-creation', inflight: false },
    { id: CANON.feature.id, title: CANON.feature.title, column: 'In review', assignee: '@you', inflight: false },
    { id: CANON.debug.id, title: CANON.debug.title, column: 'In progress', assignee: 'crud-orchestrator', inflight: true },
    { id: 'CAST-423', title: 'Close the coverage gap on the coupon path', column: 'In progress', assignee: 'test-coverage-checker', inflight: true },
    { id: CANON.spike.id, title: CANON.spike.title, column: 'In progress', assignee: 'spike-runner', inflight: true },
    { id: CANON.data.id, title: CANON.data.title, column: 'In progress', assignee: 'decision-recorder', inflight: true },
    { id: CANON.escalationTicket.id, title: CANON.escalationTicket.title, column: 'Backlog', assignee: 'escalation-router', badge: 'L3', inflight: false },
    { id: 'CAST-419', title: 'Audit log for permission changes', column: 'Backlog', assignee: 'api-contractor', inflight: false },
  ],
};

// ───────────────────────────────────────────────────────────────────────────
// hiring — US6 funnel. THIN: structure complete, prose deferred to 2a.2.
// ───────────────────────────────────────────────────────────────────────────
const DIMENSIONS = ['user scale', 'internal/external surface', 'data sensitivity', 'migration safety', 'test rigor'];

// Candidate prose is a JUDGE'S read of a track record - structure of employment (what they shipped,
// where they're deep, where they're thin), NOT a mascot bio (FR-018). Radar scores are authored,
// not faker, so the stack-rank is intentional: rbac-architect is the clear winner. Per-dimension
// keys match DIMENSIONS exactly (the radar component reads them in order). Hyphens, no em dashes.
const CANDIDATE_DATA = [
  {
    slug: 'rbac-architect',
    pitch: 'Designs role and permission models for checkout-scale systems.',
    radar: [5, 5, 5, 4, 5],
    eval: { runs: 38, compliancePct: 99.5 },
    pros: [
      'Has modeled role hierarchies on three prior checkout systems at comparable user scale',
      'Every produced PR shipped with a green run from its paired checker',
    ],
    cons: ['Defaults to additive migrations, so legacy columns retire about a quarter slower than a drop-first approach'],
    produced_work: [
      { id: 'pw-rbac-architect-1', type: 'migration-file', title: '0042_add_roles_permissions.sql', snippet: 'create table role_permissions (role_id, permission_id); backfill from the legacy roles column' },
      { id: 'pw-rbac-architect-2', type: 'code-excerpt', title: 'permission_check.py', snippet: 'def can(actor, action, resource): return actor.role in resource.allowed_roles(action)' },
    ],
  },
  {
    slug: 'access-control-builder',
    pitch: 'Builds the permission-check middleware and the CRUD stack behind it.',
    radar: [4, 4, 4, 5, 4],
    eval: { runs: 31, compliancePct: 99.2 },
    pros: [
      'Cleanest migration record of the six - every change shipped with a reversible down step',
      'Carries its own integration harness for the auth path',
    ],
    cons: ['Narrower on external-surface design; defers the API shape to a contractor'],
    produced_work: [
      { id: 'pw-access-control-builder-1', type: 'code-excerpt', title: 'rbac_middleware.py', snippet: 'resolves the actor role once and attaches it to the request context' },
    ],
  },
  {
    slug: 'policy-gatekeeper',
    pitch: 'Specializes in data-sensitivity boundaries and authz enforcement.',
    radar: [4, 3, 5, 3, 5],
    eval: { runs: 29, compliancePct: 99.0 },
    pros: [
      'Strongest data-sensitivity record - gates PII reads behind a permission check by default',
      'High test rigor; coverage never dropped below the gate across its runs',
    ],
    cons: ['Mid-pack on migration safety; prefers to hand schema drops to a migration specialist'],
    produced_work: [
      { id: 'pw-policy-gatekeeper-1', type: 'checker-report', title: 'authz-boundary-report.md', snippet: '3 endpoints read a permission table without an authz check - all 3 gated before merge' },
    ],
  },
  {
    slug: 'claims-mapper',
    pitch: 'Maps external identity claims onto internal roles.',
    radar: [3, 5, 4, 3, 3],
    eval: { runs: 24, compliancePct: 98.6 },
    pros: [
      'Best external-surface design of the six; handles federated claims without a custom schema',
      'Reads cleanly against an existing REST surface',
    ],
    cons: [
      'Lighter test rigor; two prior runs needed a second checker loop',
      'Less migration experience on prod data',
    ],
    produced_work: [
      { id: 'pw-claims-mapper-1', type: 'code-excerpt', title: 'claims_to_roles.py', snippet: 'maps an OIDC claim set to the internal role list, defaulting unknown claims to no role' },
    ],
  },
  {
    slug: 'session-warden',
    pitch: 'Owns session and token lifecycle around the permission check.',
    radar: [4, 3, 4, 4, 4],
    eval: { runs: 27, compliancePct: 98.9 },
    pros: [
      'Solid all-round record with no dimension below mid-pack',
      'Handles token-revocation paths the others skip',
    ],
    cons: ['No standout dimension; a generalist where this hire wants depth on role modeling'],
    produced_work: [
      { id: 'pw-session-warden-1', type: 'code-excerpt', title: 'session_revoke.py', snippet: 'revokes a session token and clears the cached role on the next request' },
    ],
  },
  {
    slug: 'grant-auditor',
    pitch: 'Audits grant changes and produces the permission-change trail.',
    radar: [3, 3, 5, 4, 5],
    eval: { runs: 22, compliancePct: 99.1 },
    pros: [
      'Highest test-rigor and data-sensitivity scores; built for the audit-log requirement',
      'Pairs naturally with a decision recorder',
    ],
    cons: [
      'Lowest user-scale record; has not worked a checkout-sized permission set',
      'Read-heavy; defers most write paths to a builder',
    ],
    produced_work: [
      { id: 'pw-grant-auditor-1', type: 'checker-report', title: 'grant-change-audit.md', snippet: 'every grant and revoke in the window, with actor, before, and after - no unexplained changes' },
    ],
  },
];

const candidates = CANDIDATE_DATA.map((c) => ({
  id: `cand-${c.slug}`,
  slug: c.slug,
  name: personName(), // faker filler (sanctioned) - the human-readable name on the resume card
  pitch: c.pitch,
  radar: Object.fromEntries(DIMENSIONS.map((d, i) => [d, c.radar[i]])),
  pros: c.pros,
  cons: c.cons,
  eval_runs: c.eval.runs,
  eval_compliance_pct: c.eval.compliancePct,
  produced_work: c.produced_work,
}));

// Stack-ranked, strongest first. The hire is the winner MAKER plus its paired CHECKER, onboarded
// together (the maker-checker loop is the unit of work, not a lone agent).
const hiring = {
  request: 'Hire an rbac-agent to own RBAC permission modeling for checkout.',
  dimensions: DIMENSIONS,
  candidates,
  report: {
    ranked: ['rbac-architect', 'access-control-builder', 'policy-gatekeeper', 'grant-auditor', 'session-warden', 'claims-mapper'],
    winner: 'rbac-architect',
    paired_checker: 'security-checker',
    note: 'Stack-ranked on the five dimensions. The hire is rbac-architect (winner maker) plus its paired checker, security-checker - they onboard as one maker-checker loop.',
  },
  onboarding: {
    data_sources: ['the existing roles and permissions tables', 'the v4.2 RBAC migration history', 'the checkout authz middleware'],
    tastes: ['additive migrations with a reversible down step', 'permission checks on the shared middleware, not a parallel path', 'a green checker run on every PR before review'],
    autonomy_initial: 'balanced',
  },
};

// ───────────────────────────────────────────────────────────────────────────
// layer2 — 12 contracts (8 chain-aligned + 4 cross-cutting), 8-node chain, 6-project portfolio.
// Names are structural canon; purposes are THIN placeholders (2a.2 authors prose).
// ───────────────────────────────────────────────────────────────────────────
// 8 chain-aligned contracts: each is the artifact one chain node hands to the next. producer/consumer
// are chain-node names from CANON.chain, so the Layer-2 page reads as the chain's own data contract.
const CHAIN_CONTRACT_DATA = [
  { name: 'refine-spec', purpose: 'The refined spec a goal is decomposed against.', producer: 'refine', consumer: 'decompose' },
  { name: 'decompose-steps', purpose: 'The ordered step list each research pass expands.', producer: 'decompose', consumer: 'research' },
  { name: 'research-notes', purpose: 'Per-step research notes the synthesis pass turns into a playbook.', producer: 'research', consumer: 'synthesize' },
  { name: 'synthesis-playbook', purpose: 'The opinionated playbook the phase plan is built from.', producer: 'synthesize', consumer: 'plan' },
  { name: 'phase-plan', purpose: 'The phased plan each sub-phase is detailed against.', producer: 'plan', consumer: 'detail' },
  { name: 'detail-plan', purpose: 'The detailed sub-phase plan the orchestrator dispatches.', producer: 'detail', consumer: 'orchestrate' },
  { name: 'dispatch-manifest', purpose: 'The ordered sub-phase manifest the runner executes.', producer: 'orchestrate', consumer: 'run' },
  { name: 'run-envelope', purpose: 'The result envelope a completed run reports back.', producer: 'run', consumer: '@you' },
];
// 4 cross-cutting contracts: not a chain step, but the protocols every node speaks.
const CROSSCUT_CONTRACT_DATA = [
  { name: 'maker-checker-loop', purpose: 'The two-agent loop every maker runs against its checker before a PR merges.', producer: 'any maker', consumer: 'any checker' },
  { name: 'decision-record', purpose: 'The ADR atom an agent emits when it reaches a judgment call.', producer: 'any agent', consumer: 'decision trail' },
  { name: 'escalation-handoff', purpose: 'The three-option, evidence-packed handoff an L3 stop raises.', producer: 'any agent', consumer: '@you' },
  { name: 'evidence-bundle', purpose: 'The E1-E5 evidence pack attached to a result or a decision.', producer: 'any agent', consumer: 'the goal canvas' },
];
// Per-node chain status (vocabulary: done | active | queued | idle) + how many goals sit on the node.
const CHAIN_STATUS = {
  refine: 'done', decompose: 'done', research: 'active', synthesize: 'active',
  plan: 'queued', detail: 'queued', orchestrate: 'active', run: 'active',
};
const CHAIN_INFLIGHT = { refine: 0, decompose: 0, research: 1, synthesize: 1, plan: 0, detail: 0, orchestrate: 1, run: 1 };
const layer2 = {
  contracts: [
    ...CHAIN_CONTRACT_DATA.map((c, i) => ({ name: c.name, kind: 'chain-aligned', chain_position: CANON.chain[i], purpose: c.purpose, producer: c.producer, consumer: c.consumer })),
    ...CROSSCUT_CONTRACT_DATA.map((c) => ({ name: c.name, kind: 'cross-cutting', purpose: c.purpose, producer: c.producer, consumer: c.consumer })),
  ],
  chain: CANON.chain.map((node) => ({ node, status: CHAIN_STATUS[node], inflight: CHAIN_INFLIGHT[node] })),
  // Portfolio: 6 shipped projects - faker names (sanctioned filler), real-looking volume stats. Proof
  // by volume for the marketplace, not a per-project story.
  portfolio: Array.from({ length: 6 }, () => ({
    name: faker.company.name(),
    status: 'shipped',
    runs: faker.number.int({ min: 40, max: 900 }),
    compliancePct: faker.number.int({ min: 970, max: 999 }) / 10,
  })),
};

// ───────────────────────────────────────────────────────────────────────────
// Assemble window.ORG — 11 top-level keys, fixed order (frozen).
// ───────────────────────────────────────────────────────────────────────────
const ORG = {
  meta,
  org,
  humans,
  guide,
  agents,
  stageModels,
  goals,
  board,
  decisions,
  hiring,
  layer2,
};

// ───────────────────────────────────────────────────────────────────────────
// THE INVARIANT GATE — runs before the write; refuses to emit on any violation.
// (Folded into the generator on purpose: NO standalone validator, NO test file — owner's NO-TESTS rule.)
// ───────────────────────────────────────────────────────────────────────────
function check(data) {
  const errors = [];
  const TOP_KEYS = ['meta', 'org', 'humans', 'guide', 'agents', 'stageModels', 'goals', 'board', 'decisions', 'hiring', 'layer2'];

  // Rule 0: exactly the 11 top-level keys.
  const keys = Object.keys(data);
  if (keys.length !== TOP_KEYS.length || TOP_KEYS.some((k) => !keys.includes(k))) {
    errors.push(`[top-level-keys] expected exactly 11 keys [${TOP_KEYS.join(', ')}], got [${keys.join(', ')}]`);
  }

  const agentSlugs = new Set(Object.keys(data.agents));
  const humanSlugs = new Set(data.humans.map((h) => h.slug));
  const goalIds = new Set(Object.keys(data.goals));
  const atomIds = new Set(data.decisions.map((a) => a.id));
  const ticketIds = new Set(data.board.tickets.map((tk) => tk.id));
  const knownEntities = new Set([...agentSlugs, ...humanSlugs, data.guide.slug, ...goalIds, ...atomIds, ...ticketIds]);
  const assigneeOk = (s) => agentSlugs.has(s) || humanSlugs.has(s) || s === data.guide.slug;
  const agentOriginOk = (s) => agentSlugs.has(s) || humanSlugs.has(s) || s === data.guide.slug;

  // Collect every evidence object across goals (for spike_ref bidirectionality).
  const evidenceById = new Map();
  for (const g of Object.values(data.goals)) {
    for (const ev of Object.values(g.evidence ?? {})) {
      if (ev && ev.id) evidenceById.set(ev.id, ev);
    }
  }

  // Rule 8: all four stageModels families carry placeholder:false — Phase 2c (sp4) has ENCODED the
  // derived vocabulary. (Pre-2c this rule asserted placeholder:true "until Phase 2c"; sp4 advanced it
  // to its post-2c state when it flipped the flags. Still a hard invariant — the gate is not weakened,
  // it now refuses to emit a half-encoded region that left any family on the placeholder watermark.)
  for (const fam of ['feature', 'debug', 'spike', 'data']) {
    if (!data.stageModels[fam] || data.stageModels[fam].placeholder !== false) {
      errors.push(`[stagemodels-placeholder] stageModels.${fam} must carry placeholder:false (2c-encoded region)`);
    }
  }
  const stepIdsByFamily = {};
  for (const fam of ['feature', 'debug', 'spike', 'data']) {
    stepIdsByFamily[fam] = new Set((data.stageModels[fam]?.steps ?? []).map((s) => s.id));
  }

  // Rule 1 + 10 + 2 + 4 + 7: decision atoms.
  const byGoal = {};
  for (const a of data.decisions) {
    (byGoal[a.goal_slug] ??= []).push(a);

    // Rule 10: non-empty diff.
    if (typeof a.diff !== 'string' || a.diff.trim() === '') {
      errors.push(`[atom-diff] atom ${a.id} must carry a non-empty diff`);
    }
    // Rule 2: goal_slug / originating_agent / influenced[] resolve.
    if (!goalIds.has(a.goal_slug)) errors.push(`[atom-ref] atom ${a.id} goal_slug '${a.goal_slug}' does not resolve to a goal`);
    if (!agentOriginOk(a.originating_agent)) errors.push(`[atom-ref] atom ${a.id} originating_agent '${a.originating_agent}' does not resolve to an agent/human/guide`);
    for (const inf of a.influenced ?? []) {
      if (!knownEntities.has(inf)) errors.push(`[atom-ref] atom ${a.id} influenced[] entry '${inf}' does not resolve to a known entity`);
    }
    // Rule 4: every L3 has exactly 3 ranked options (none chosen) + evidence pack.
    if (a.reversibility === 'L3') {
      const opts = a.options_considered ?? [];
      if (opts.length !== 3) {
        errors.push(`[l3-options] L3 atom ${a.id} must have exactly 3 options, has ${opts.length}`);
      } else {
        const ranks = opts.map((o) => o.rank).sort((x, y) => x - y);
        if (ranks.join(',') !== '1,2,3') errors.push(`[l3-options] L3 atom ${a.id} options must be ranked exactly 1,2,3 (got ${ranks.join(',')})`);
        if (opts.some((o) => o.chosen !== false)) errors.push(`[l3-options] L3 atom ${a.id} must have chosen:false on all options at rest`);
      }
      if (!a.what_i_want || !a.what_i_tried) errors.push(`[l3-evidence-pack] L3 atom ${a.id} must carry a non-empty evidence pack (what_i_want, what_i_tried)`);
    }
    // Rule 3: spike_ref bidirectionality.
    if (a.spike_ref != null) {
      const ev = evidenceById.get(a.spike_ref);
      if (!ev) errors.push(`[spike-ref] atom ${a.id} spike_ref '${a.spike_ref}' does not resolve to an evidence object`);
      else if (ev.atom_ref !== a.id) errors.push(`[spike-ref] spike_ref not bidirectional: atom ${a.id} → ${a.spike_ref}, but evidence.atom_ref = '${ev.atom_ref}'`);
    }
  }
  // Rule 7: supersede links reciprocal.
  const atomById = new Map(data.decisions.map((a) => [a.id, a]));
  for (const a of data.decisions) {
    if (a.supersedes != null) {
      const other = atomById.get(a.supersedes);
      if (!other) errors.push(`[supersede] atom ${a.id} supersedes '${a.supersedes}' which does not exist`);
      else if (other.superseded_by !== a.id) errors.push(`[supersede] not reciprocal: ${a.id} supersedes ${a.supersedes}, but ${a.supersedes}.superseded_by = '${other.superseded_by}'`);
    }
    if (a.superseded_by != null) {
      const other = atomById.get(a.superseded_by);
      if (!other) errors.push(`[supersede] atom ${a.id} superseded_by '${a.superseded_by}' which does not exist`);
      else if (other.supersedes !== a.id) errors.push(`[supersede] not reciprocal: ${a.id} superseded_by ${a.superseded_by}, but ${a.superseded_by}.supersedes = '${other.supersedes}'`);
    }
  }
  // Rule 1: per goal 5–8 atoms, exactly one L3.
  for (const gid of goalIds) {
    const list = byGoal[gid] ?? [];
    if (list.length < 5 || list.length > 8) errors.push(`[atom-budget] goal ${gid} must have 5–8 decision atoms, has ${list.length}`);
    const l3s = list.filter((a) => a.reversibility === 'L3');
    if (l3s.length !== 1) errors.push(`[one-l3-per-flow] goal ${gid} must have exactly one L3 atom, has ${l3s.length} (${l3s.map((a) => a.id).join(', ')})`);
  }

  // Rule 5: every ticket assignee resolves.
  for (const tk of data.board.tickets) {
    if (!assigneeOk(tk.assignee)) errors.push(`[ticket-assignee] ticket ${tk.id} assignee '${tk.assignee}' does not resolve to a human/agent/guide`);
  }

  // Rule 6 + 9: per-goal step references and trust aggregate.
  for (const [gid, g] of Object.entries(data.goals)) {
    const fam = g.family;
    const validSteps = stepIdsByFamily[fam] ?? new Set();
    const refs = [
      ...(g.artifacts ?? []).map((x) => ({ where: `artifact ${x.id}`, step: x.step })),
      ...(g.work_stream ?? []).map((x) => ({ where: `work_stream ${x.id}`, step: x.step })),
      { where: 'spine_state.current', step: g.spine_state?.current },
    ];
    for (const r of refs) {
      if (r.step != null && !validSteps.has(r.step)) {
        errors.push(`[step-ref] goal ${gid} ${r.where} references step '${r.step}' not in stageModels.${fam} step ids`);
      }
    }
    // Rule 9: autonomy.trust equals the aggregate computed from the goal's roster agents' stats.
    const roster = g.agent_roster ?? [];
    const unknown = roster.filter((s) => !agentSlugs.has(s));
    if (unknown.length) {
      errors.push(`[roster-ref] goal ${gid} agent_roster has unknown agents: ${unknown.join(', ')}`);
    } else {
      const computed = aggregateTrust(roster);
      const stored = g.autonomy?.trust ?? {};
      if (stored.compliancePct !== computed.compliancePct || stored.runs !== computed.runs) {
        errors.push(`[trust-aggregate] goal ${gid} autonomy.trust {compliancePct:${stored.compliancePct}, runs:${stored.runs}} != computed roster aggregate {compliancePct:${computed.compliancePct}, runs:${computed.runs}}`);
      }
    }
  }

  // Rule 11: the FEATURE goal's dial trust MUST land on the canonical dial-trust stat (99.4% / 312
  // runs). This binds the authored marketplace/dial story to a generator-enforced number so the
  // feature-roster stats can never silently drift away from playbook 05's "99.4% across 312 runs".
  const featureTrust = data.goals['CAST-412']?.autonomy?.trust ?? {};
  if (featureTrust.compliancePct !== CANON.dialTrustParsed.compliancePct || featureTrust.runs !== CANON.dialTrustParsed.runs) {
    errors.push(`[dial-trust] CAST-412 autonomy.trust {compliancePct:${featureTrust.compliancePct}, runs:${featureTrust.runs}} must equal the canonical dial-trust stat {compliancePct:${CANON.dialTrustParsed.compliancePct}, runs:${CANON.dialTrustParsed.runs}} ('${CANON.dialTrust}')`);
  }

  return errors;
}

const violations = check(ORG);
if (violations.length > 0) {
  console.error('REFUSING TO EMIT org.js — spine invariant(s) violated:');
  for (const v of violations) console.error('  ✗ ' + v);
  console.error(`\n${violations.length} violation(s). org.js NOT written. Fix the generator constants and re-run.`);
  process.exit(1);
}

// ───────────────────────────────────────────────────────────────────────────
// Emit — classic script, deterministic serialization, GENERATED header.
// ───────────────────────────────────────────────────────────────────────────
const header =
  '// GENERATED by _build/generate-org.mjs - edit the generator, not this file.\n' +
  '// Classic script on purpose: file:// forbids fetch/imports.\n' +
  `// FREEZE POLICY: ${FREEZE_POLICY}\n` +
  '// Object.freeze is SHALLOW (top-level only) - deliberate; protects the contract surface\n' +
  "// without blocking 2c's stageModels rewrite.\n";

const body = `window.ORG = Object.freeze(${JSON.stringify(ORG, null, 2)});\n`;

writeFileSync(OUT_PATH, header + body, 'utf8');
const supersededPairs = ORG.decisions.filter((a) => a.supersedes != null).length;
console.log(`OK - emitted ${OUT_PATH}`);
console.log(`  ${Object.keys(ORG).length} top-level keys · ${Object.keys(ORG.agents).length} agents · ${ORG.decisions.length} decision atoms · ${Object.keys(ORG.goals).length} goals`);
for (const gid of Object.keys(ORG.goals)) {
  const list = ORG.decisions.filter((a) => a.goal_slug === gid);
  console.log(`  ${gid}: ${list.length} atoms, ${list.filter((a) => a.reversibility === 'L3').length} L3`);
}
console.log(`  superseded pairs: ${supersededPairs} · agents: ${Object.keys(ORG.agents).length} · hiring candidates: ${ORG.hiring.candidates.length} · layer2 contracts: ${ORG.layer2.contracts.length} · portfolio: ${ORG.layer2.portfolio.length}`);
console.log(`  feature dial trust: ${ORG.goals['CAST-412'].autonomy.trust.compliancePct}% / ${ORG.goals['CAST-412'].autonomy.trust.runs} runs (canonical: '${CANON.dialTrust}')`);
