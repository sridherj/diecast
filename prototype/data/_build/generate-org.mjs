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
  data: { id: 'CAST-461', title: 'Q2 revenue dip — which segment drove it?' },
  ruleCodes: { M04: 'convention drift', S03: 'typing too permissive', R02: 'missing index on FK' },
  rework: '1/3 used',
  canonicalAgent: 'crud-orchestrator',
  canonicalChecker: 'crud-compliance-checker',
  marketplaceCred: '99.9% compliant code in 2 maker-checker loops across 505 runs',
  dialTrust: '99.4% compliance across 312 runs',
  pr: 'PR #2341',
  testSummary: '47 passed / 0 failed',
  chain: ['refine', 'decompose', 'research', 'synthesize', 'plan', 'detail', 'orchestrate', 'run'],
  archetypes: ['Maker', 'Checker', 'Decision', 'Spike', 'Escalation', 'Mentor'],
};

const FREEZE_POLICY =
  'FROZEN after Phase 2a. Later phases may EXTEND with new keys at designated extension points but ' +
  'never mutate existing values. ONE standing exception: the stageModels region is 2c-owned and is ' +
  'rewritten once by 2c via this generator (which re-runs the invariant gate at that moment). This is ' +
  'the F4 single-source rule: org.js is generated, never hand-edited — edit the generator and regenerate.';

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
  frozen_at: null, // 2a.3 sets this at freeze time
  generated_by: '_build/generate-org.mjs',
  owner_notes: FREEZE_POLICY,
};

// ───────────────────────────────────────────────────────────────────────────
// agents — 12, keyed by slug. Superset of 2b's fixture shape. kind ∈ maker|checker
// (non-maker/checker archetypes get kind:'maker' = square avatar; archetype carries the facet).
// stats are CANON-grade hardcoded numbers (never faker); versions/usage use faker filler.
// ───────────────────────────────────────────────────────────────────────────
const AGENT_DEFS = [
  // slug, kind, archetype, pairedWith, health, stats{compliancePct,loops,runs}, rework{used,budget}, inflight, state
  ['crud-orchestrator', 'maker', 'Maker', 'crud-compliance-checker', 'active', { compliancePct: 99.9, loops: 2, runs: 505 }, { used: 1, budget: 3 }, 2, 'running'],
  ['entity-creation', 'maker', 'Maker', 'test-coverage-checker', 'active', { compliancePct: 99.1, loops: 2, runs: 140 }, { used: 0, budget: 3 }, 1, 'running'],
  ['migration-author', 'maker', 'Maker', 'crud-compliance-checker', 'active', { compliancePct: 98.7, loops: 3, runs: 88 }, { used: 2, budget: 3 }, 0, 'idle'],
  ['api-contractor', 'maker', 'Maker', 'security-checker', 'active', { compliancePct: 99.3, loops: 2, runs: 132 }, { used: 1, budget: 3 }, 0, 'idle'],
  ['crud-compliance-checker', 'checker', 'Checker', 'crud-orchestrator', 'active', { compliancePct: 99.6, loops: 1, runs: 470 }, { used: 0, budget: 3 }, 1, 'running'],
  ['test-coverage-checker', 'checker', 'Checker', 'entity-creation', 'checker-flagged', { compliancePct: 98.9, loops: 1, runs: 210 }, { used: 0, budget: 3 }, 0, 'idle'],
  ['security-checker', 'checker', 'Checker', 'api-contractor', 'active', { compliancePct: 99.4, loops: 1, runs: 175 }, { used: 0, budget: 3 }, 0, 'idle'],
  ['decision-recorder', 'maker', 'Decision', null, 'benched', { compliancePct: 100.0, loops: 1, runs: 96 }, { used: 0, budget: 3 }, 0, 'idle'],
  ['spike-runner', 'maker', 'Spike', null, 'active', { compliancePct: 97.8, loops: 1, runs: 64 }, { used: 0, budget: 3 }, 1, 'running'],
  ['escalation-router', 'maker', 'Escalation', null, 'active', { compliancePct: 99.0, loops: 1, runs: 80 }, { used: 0, budget: 3 }, 0, 'idle'],
  ['onboarding-mentor', 'maker', 'Mentor', null, 'active', { compliancePct: 98.5, loops: 1, runs: 52 }, { used: 0, budget: 3 }, 0, 'idle'],
  ['repo-cartographer', 'maker', 'Mentor', null, 'benched', { compliancePct: 98.2, loops: 1, runs: 70 }, { used: 0, budget: 3 }, 0, 'idle'],
];

const agents = {};
let agentOffset = 60;
for (const [slug, kind, archetype, pairedWith, health, stats, rework, inflight, state] of AGENT_DEFS) {
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
    versions: [{ sha: sha(), at: t(agentOffset), note: '[2a.2] version note' }],
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
// stageModels — 2c-OWNED region. placeholder:true everywhere; watermarked labels; <family>-NN ids.
// (2a ships the slot; 2c rewrites it once with derived vocabulary via this generator.)
// ───────────────────────────────────────────────────────────────────────────
function step(id, surface, label) {
  return {
    id,
    label: `[2c] ${label}`,
    shortLabel: `[2c] ${id}`,
    does: '[2c] placeholder — derived stage vocabulary lands in Phase 2c',
    surface, // doc|board|pr-thread|ledger|notebook|memo
    surfaceWhy: '[2c] placeholder',
    artifacts: [],
    refs: [],
    evidence: null,
  };
}

const stageModels = {
  feature: {
    placeholder: true,
    shape: 'segments',
    steps: [
      step('feat-01', 'doc', 'requirements'),
      step('feat-02', 'doc', 'plan'),
      step('feat-03', 'board', 'tickets'),
      step('feat-04', 'pr-thread', 'execution'),
      step('feat-05', 'pr-thread', 'review'),
    ],
  },
  debug: {
    placeholder: true,
    shape: 'loop',
    loop: { over: 'hypotheses', budget: 3 },
    steps: [
      step('dbg-01', 'ledger', 'reproduce'),
      step('dbg-02', 'ledger', 'hypothesize'),
      step('dbg-03', 'ledger', 'experiment'),
      step('dbg-04', 'pr-thread', 'fix'),
    ],
  },
  spike: {
    placeholder: true,
    shape: 'timebox',
    timebox: { budget: '3h' },
    steps: [
      step('spk-01', 'memo', 'frame'),
      step('spk-02', 'memo', 'probe'),
      step('spk-03', 'memo', 'measure'),
      step('spk-04', 'memo', 'verdict'),
    ],
  },
  data: {
    placeholder: true,
    shape: 'pipeline',
    steps: [
      step('data-01', 'notebook', 'extract'),
      step('data-02', 'notebook', 'transform'),
      step('data-03', 'notebook', 'analyze'),
      step('data-04', 'memo', 'report'),
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

// exactly-3 ranked options for an L3 (none chosen at rest)
function rankedOptions(labels) {
  return labels.map((label, i) => ({ label, rank: i + 1, chosen: false, note: '[2a.2] option note' }));
}

const decisions = [
  // ── CAST-412 feature (5 atoms; one superseded L1 pair; L3 = -04 on CAST-417) ──
  atom({ id: 'DEC-CAST-412-01', goal_slug: 'CAST-412', title: 'Use GraphQL for the RBAC permissions endpoint', reversibility: 'L1', originating_agent: 'api-contractor', timestamp: t(70), superseded_by: 'DEC-CAST-412-02', status: 'superseded', diff: 'endpoint style: (none) → GraphQL' }),
  atom({ id: 'DEC-CAST-412-02', goal_slug: 'CAST-412', title: 'Use REST for the RBAC permissions endpoint — matches existing API surface', reversibility: 'L1', originating_agent: 'api-contractor', timestamp: t(95), supersedes: 'DEC-CAST-412-01', influenced: ['DEC-CAST-412-01'], diff: 'endpoint style: GraphQL → REST' }),
  atom({ id: 'DEC-CAST-412-03', goal_slug: 'CAST-412', title: 'Classify CAST-412 as bug, not feature', reversibility: 'L2', originating_agent: 'crud-compliance-checker', timestamp: t(532), diff: 'classification: feature → bug' }),
  atom({
    id: 'DEC-CAST-412-04', goal_slug: 'CAST-412', reversibility: 'L3', originating_agent: 'migration-author', timestamp: t(300),
    title: 'Migrate roles schema (drops legacy roles column) — CAST-417',
    options_considered: rankedOptions([
      'Additive migration + 90-day legacy-column retention',
      'Drop column + pre-migration snapshot',
      'Spike a dual-write window before dropping',
    ]),
    influenced: ['DEC-CAST-412-03'],
    diff: 'roles schema: legacy column retained → migration pending (L3 hard stop)',
    what_i_want: '[2a.2] the safe path to drop the legacy roles column without breaking checkout',
    what_i_tried: '[2a.2] reviewed read paths; legacy column still referenced by one report',
  }),
  atom({ id: 'DEC-CAST-412-05', goal_slug: 'CAST-412', title: 'Reuse existing auth middleware for permission checks', reversibility: 'L1', originating_agent: 'crud-orchestrator', timestamp: t(120), diff: 'permission check: new layer → reuse shared middleware' }),

  // ── CAST-431 debug (5 atoms; L3 = -03) ──
  atom({ id: 'DEC-CAST-431-01', goal_slug: 'CAST-431', title: 'Reproduce the 500 against a seeded coupon fixture', reversibility: 'L1', originating_agent: 'crud-orchestrator', timestamp: t(140), diff: 'repro: none → seeded coupon fixture' }),
  atom({ id: 'DEC-CAST-431-02', goal_slug: 'CAST-431', title: 'Treat shared auth middleware as the prime suspect', reversibility: 'L2', originating_agent: 'crud-compliance-checker', timestamp: t(165), influenced: ['DEC-CAST-412-05'], diff: 'suspect: coupon code → shared auth middleware' }),
  atom({
    id: 'DEC-CAST-431-03', goal_slug: 'CAST-431', reversibility: 'L3', originating_agent: 'crud-orchestrator', timestamp: t(190),
    title: 'Scope the shared-auth-middleware fix to the coupon path only',
    options_considered: rankedOptions([
      'Narrow guard on the coupon-apply path',
      'Refactor the shared middleware for all callers',
      'Hotfix now, schedule a broader refactor',
    ]),
    diff: 'fix scope: shared middleware (all callers) → coupon path only (L3 hard stop)',
    what_i_want: '[2a.2] stop the 500s without destabilizing other middleware callers',
    what_i_tried: '[2a.2] traced the null-role path introduced by the v4.2 RBAC migration',
  }),
  atom({ id: 'DEC-CAST-431-04', goal_slug: 'CAST-431', title: 'Add a regression guard for null-role coupon requests', reversibility: 'L1', originating_agent: 'test-coverage-checker', timestamp: t(210), diff: 'guard: none → null-role coupon case' }),
  atom({ id: 'DEC-CAST-431-05', goal_slug: 'CAST-431', title: 'Backfill missing role rows from the v4.2 migration', reversibility: 'L2', originating_agent: 'migration-author', timestamp: t(230), diff: 'data: missing role rows → backfilled' }),

  // ── CAST-452 spike (5 atoms; L3 = -03, carries spike_ref ↔ E4) ──
  atom({ id: 'DEC-CAST-452-01', goal_slug: 'CAST-452', title: 'Frame the spike around the 200ms p95 checkout budget', reversibility: 'L1', originating_agent: 'spike-runner', timestamp: t(250), diff: 'spike frame: open → 200ms p95 budget' }),
  atom({ id: 'DEC-CAST-452-02', goal_slug: 'CAST-452', title: 'Extend the timebox from 2h to 3h to finish the p95 measurement', reversibility: 'L2', originating_agent: 'spike-runner', timestamp: t(270), diff: 'timebox: 2h → 3h' }),
  atom({
    id: 'DEC-CAST-452-03', goal_slug: 'CAST-452', reversibility: 'L3', originating_agent: 'spike-runner', timestamp: t(300),
    title: 'Vendor SDK adds 180ms p95 (borderline vs 200ms) — adopt, reject, or negotiate?',
    options_considered: rankedOptions([
      'Adopt the SDK and absorb the 180ms',
      'Reject and build in-house',
      'Negotiate an async/batched mode with the vendor',
    ]),
    spike_ref: 'E4-CAST-452',
    diff: 'vendor SDK: unmeasured → +180ms p95 borderline (L3 hard stop)',
    what_i_want: '[2a.2] a checkout SDK that fits the 200ms p95 budget',
    what_i_tried: '[2a.2] measured p95 across 3 deciding data points; landed at 180ms',
  }),
  atom({ id: 'DEC-CAST-452-04', goal_slug: 'CAST-452', title: 'Measure p95 under warm-cache conditions only', reversibility: 'L1', originating_agent: 'spike-runner', timestamp: t(285), diff: 'measurement: cold+warm → warm-cache only' }),
  atom({ id: 'DEC-CAST-452-05', goal_slug: 'CAST-452', title: 'Record the SDK version pinned for the measurement', reversibility: 'L1', originating_agent: 'decision-recorder', timestamp: t(295), diff: 'sdk version: floating → pinned for measurement' }),

  // ── CAST-461 data (5 atoms; L3 = -03) ──
  atom({ id: 'DEC-CAST-461-01', goal_slug: 'CAST-461', title: 'Scope the dip analysis to Q2 by acquisition segment', reversibility: 'L1', originating_agent: 'decision-recorder', timestamp: t(320), diff: 'analysis scope: all → Q2 by acquisition segment' }),
  atom({ id: 'DEC-CAST-461-02', goal_slug: 'CAST-461', title: 'Treat the finance DB as the primary source pending reconciliation', reversibility: 'L2', originating_agent: 'repo-cartographer', timestamp: t(340), diff: 'primary source: undecided → finance DB (provisional)' }),
  atom({
    id: 'DEC-CAST-461-03', goal_slug: 'CAST-461', reversibility: 'L3', originating_agent: 'decision-recorder', timestamp: t(360),
    title: 'Reconcile the 8% Q2 revenue gap: finance DB vs billing export',
    options_considered: rankedOptions([
      'Trust the finance DB and footnote the billing delta',
      'Trust the billing export and re-derive finance figures',
      'Hold the report until a reconciled third source exists',
    ]),
    diff: 'Q2 revenue: two sources 8% apart → reconciliation pending (L3 hard stop)',
    what_i_want: '[2a.2] one defensible Q2 revenue number to attribute the dip',
    what_i_tried: '[2a.2] aligned date windows; an 8% gap persists between the two sources',
  }),
  atom({ id: 'DEC-CAST-461-04', goal_slug: 'CAST-461', title: 'Exclude refunded orders from the segment totals', reversibility: 'L1', originating_agent: 'repo-cartographer', timestamp: t(335), diff: 'totals: gross → net of refunds' }),
  atom({ id: 'DEC-CAST-461-05', goal_slug: 'CAST-461', title: 'Annotate each series point with its source provenance', reversibility: 'L2', originating_agent: 'decision-recorder', timestamp: t(350), diff: 'series: bare values → source-annotated' }),
];

// ───────────────────────────────────────────────────────────────────────────
// goals — 4, keyed by goal id. agent_roster (added field, documented) drives the trust aggregate.
// artifacts / work_stream items reference stage steps by step id; spine_state.current is a step id.
// ───────────────────────────────────────────────────────────────────────────
const goalDecisionIds = (goalId) => decisions.filter((a) => a.goal_slug === goalId).map((a) => a.id);

const featureRoster = ['crud-orchestrator', 'entity-creation', 'migration-author', 'crud-compliance-checker'];
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
    nudge: { who: 'Guide', do: "Review CAST-412's PR", why: 'checker flagged R02 — unblocks 2 queued tasks' },
    artifacts: [
      { id: 'art-reqs-412', type: 'requirements-doc', step: 'feat-01', version: 'v2', classification: 'feature → bug' },
      { id: 'art-plan-412', type: 'plan-doc', step: 'feat-02' },
      { id: 'art-tickets-412', type: 'tickets', step: 'feat-03' },
      { id: 'art-e1-412', type: 'e1-panel', step: 'feat-04' },
    ],
    work_stream: [
      { id: 'ws-412-1', label: '[2a.2] create Role/Permission entities + CRUD stack', assignee: 'crud-orchestrator', step: 'feat-03', kind: 'ticket' },
      { id: 'ws-412-2', label: "Review CAST-412's PR", assignee: '@you', step: 'feat-04', kind: 'manual' },
    ],
    evidence: {
      E1: {
        id: 'E1-CAST-412', kind: 'E1', test_summary: CANON.testSummary, coverage_delta: '+2.1%', pr: CANON.pr,
        checker_rows: [
          { code: 'M04', label: CANON.ruleCodes.M04, state: 'resolved', glyph: '●' },
          { code: 'S03', label: CANON.ruleCodes.S03, state: 'resolved', glyph: '●' },
          { code: 'R02', label: CANON.ruleCodes.R02, state: 'flagged', glyph: '◐' },
        ],
        shots: [{ ref: 'assets/e1-acceptance.png', alt: '[2a.2] acceptance panel', caption: '[2a.2] caption' }],
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
    nudge: { who: 'Guide', do: 'Confirm the coupon-path repro', why: 'hypothesis H3 confirmed — ready to scope the fix' },
    artifacts: [{ id: 'art-ledger-431', type: 'investigation-ledger', step: 'dbg-02' }],
    work_stream: [{ id: 'ws-431-1', label: '[2a.2] run experiment for hypothesis H3', assignee: 'crud-orchestrator', step: 'dbg-03', kind: 'experiment' }],
    evidence: {
      E2: {
        id: 'E2-CAST-431', kind: 'E2',
        hypotheses: [
          { id: 'H1', verdict: 'refuted', prediction: '[2a.2]', observation: '[2a.2]' },
          { id: 'H2', verdict: 'refuted', prediction: '[2a.2]', observation: '[2a.2]' },
          { id: 'H3', verdict: 'confirmed', prediction: '[2a.2]', observation: '[2a.2]' },
        ],
      },
      E3: { id: 'E3-CAST-431', kind: 'E3', repro: '[2a.2] named repro', red: '[2a.2] red output', green: '[2a.2] green output' },
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
    nudge: { who: 'Guide', do: 'Decide on the vendor SDK', why: 'p95 measured at 180ms — borderline against the 200ms budget' },
    artifacts: [{ id: 'art-memo-452', type: 'memo', step: 'spk-03' }],
    work_stream: [{ id: 'ws-452-1', label: '[2a.2] probe SDK p95 under warm cache', assignee: 'spike-runner', step: 'spk-02', kind: 'probe' }],
    evidence: {
      E4: {
        id: 'E4-CAST-452', kind: 'E4',
        verdict: 'adds 180ms p95 — borderline', confidence: '◐',
        atom_ref: 'DEC-CAST-452-03',
        data_points: [{ label: '[2a.2] p95 run 1', ms: faker.number.int({ min: 170, max: 190 }) }, { label: '[2a.2] p95 run 2', ms: faker.number.int({ min: 170, max: 190 }) }, { label: '[2a.2] p95 run 3', ms: faker.number.int({ min: 170, max: 190 }) }],
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
      { id: 'art-notebook-461', type: 'notebook', step: 'data-03' },
      { id: 'art-report-461', type: 'report', step: 'data-04', version: 'v1' },
    ],
    work_stream: [{ id: 'ws-461-1', label: '[2a.2] align date windows across sources', assignee: 'decision-recorder', step: 'data-03', kind: 'cell' }],
    evidence: {
      E5: {
        id: 'E5-CAST-461', kind: 'E5', gap: '8%',
        sources: ['finance DB', 'billing export'],
        series: [
          { segment: '[2a.2] segment A', finance: faker.number.int({ min: 80, max: 120 }), billing: faker.number.int({ min: 80, max: 120 }) },
          { segment: '[2a.2] segment B', finance: faker.number.int({ min: 80, max: 120 }), billing: faker.number.int({ min: 80, max: 120 }) },
        ],
        reconciliation_note: '[2a.2] reconciliation note',
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
    { id: 'CAST-412', title: CANON.feature.title, column: 'In review', assignee: '@you', inflight: false },
    { id: 'CAST-417', title: CANON.escalationTicket.title, column: 'Backlog', assignee: 'escalation-router', badge: 'L3', inflight: false },
    { id: 'CAST-431', title: CANON.debug.title, column: 'In progress', assignee: 'crud-orchestrator', inflight: true },
    { id: 'CAST-452', title: CANON.spike.title, column: 'In progress', assignee: 'spike-runner', inflight: true },
    { id: 'CAST-461', title: CANON.data.title, column: 'In progress', assignee: 'decision-recorder', inflight: true },
  ],
};

// ───────────────────────────────────────────────────────────────────────────
// hiring — US6 funnel. THIN: structure complete, prose deferred to 2a.2.
// ───────────────────────────────────────────────────────────────────────────
const DIMENSIONS = ['user scale', 'internal/external surface', 'data sensitivity', 'migration safety', 'test rigor'];
const CANDIDATE_SLUGS = ['rbac-architect', 'access-control-builder', 'policy-gatekeeper', 'claims-mapper', 'session-warden', 'grant-auditor'];
const candidates = CANDIDATE_SLUGS.map((slug) => ({
  id: `cand-${slug}`,
  slug,
  name: personName(),
  pitch: '[2a.2] candidate pitch',
  radar: Object.fromEntries(DIMENSIONS.map((d) => [d, faker.number.int({ min: 2, max: 5 })])),
  pros: ['[2a.2] pro'],
  cons: ['[2a.2] con'],
  eval_runs: faker.number.int({ min: 8, max: 40 }),
  produced_work: [{ id: `pw-${slug}-1`, type: 'code-excerpt', snippet: '[2a.2] produced-work snippet' }],
}));
const hiring = {
  request: 'Hire an rbac-agent to own RBAC permission modeling for checkout.',
  dimensions: DIMENSIONS,
  candidates,
  report: { ranked: CANDIDATE_SLUGS.slice(), note: '[2a.2] stack-ranked report — winner maker + paired checker hire together' },
  onboarding: { data_sources: [], tastes: [], autonomy_initial: 'balanced' },
};

// ───────────────────────────────────────────────────────────────────────────
// layer2 — 12 contracts (8 chain-aligned + 4 cross-cutting), 8-node chain, 6-project portfolio.
// Names are structural canon; purposes are THIN placeholders (2a.2 authors prose).
// ───────────────────────────────────────────────────────────────────────────
const CHAIN_CONTRACTS = ['refine-spec', 'decompose-steps', 'research-notes', 'synthesis-playbook', 'phase-plan', 'detail-plan', 'dispatch-manifest', 'run-envelope'];
const CROSSCUT_CONTRACTS = ['maker-checker-loop', 'decision-record', 'escalation-handoff', 'evidence-bundle'];
const layer2 = {
  contracts: [
    ...CHAIN_CONTRACTS.map((name, i) => ({ name, kind: 'chain-aligned', chain_position: CANON.chain[i], purpose: '[2a.2] contract purpose' })),
    ...CROSSCUT_CONTRACTS.map((name) => ({ name, kind: 'cross-cutting', purpose: '[2a.2] contract purpose' })),
  ],
  chain: CANON.chain.map((node) => ({ node, status: 'idle' })),
  portfolio: Array.from({ length: 6 }, () => ({ name: `${faker.company.name()}`, runs: faker.number.int({ min: 40, max: 900 }), compliancePct: faker.number.int({ min: 970, max: 999 }) / 10 })),
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

  // Rule 8: all four stageModels families carry placeholder:true.
  for (const fam of ['feature', 'debug', 'spike', 'data']) {
    if (!data.stageModels[fam] || data.stageModels[fam].placeholder !== true) {
      errors.push(`[stagemodels-placeholder] stageModels.${fam} must carry placeholder:true (2c-owned region) until Phase 2c`);
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
  '// GENERATED by _build/generate-org.mjs — edit the generator, not this file.\n' +
  '// Classic script on purpose: file:// forbids fetch/imports.\n' +
  `// FREEZE POLICY: ${FREEZE_POLICY}\n` +
  '// Object.freeze is SHALLOW (top-level only) — deliberate; protects the contract surface\n' +
  "// without blocking 2c's stageModels rewrite.\n";

const body = `window.ORG = Object.freeze(${JSON.stringify(ORG, null, 2)});\n`;

writeFileSync(OUT_PATH, header + body, 'utf8');
console.log(`OK — emitted ${OUT_PATH}`);
console.log(`  ${Object.keys(ORG).length} top-level keys · ${Object.keys(ORG.agents).length} agents · ${ORG.decisions.length} decision atoms · ${Object.keys(ORG.goals).length} goals`);
for (const gid of Object.keys(ORG.goals)) {
  const list = ORG.decisions.filter((a) => a.goal_slug === gid);
  console.log(`  ${gid}: ${list.length} atoms, ${list.filter((a) => a.reversibility === 'L3').length} L3`);
}
