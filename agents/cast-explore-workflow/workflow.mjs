// cast-explore-workflow — N×M exploration Workflow engine (JavaScript Workflow script)
//
// THIS IS THE ENGINE. It is the Workflow `script` the `cast-explore-workflow` entrypoint skill
// launches via the Workflow tool (scriptPath: agents/cast-explore-workflow/workflow.mjs).
//
// ───────────────────────────────────────────────────────────────────────────────
// PORTED TO THE CURRENT WORKFLOW API (2026-06-21)
// ───────────────────────────────────────────────────────────────────────────────
// The original engine targeted an older Workflow runtime — object-arg `agent({agentType,prompt})`,
// `pipeline(name,thunk)` / `phase(name,thunk)` that executed their thunks, `readFile/writeFile/
// fileExists` globals, and bottom-of-file `export {…}`. The CURRENT runtime (verified by live probe
// + launch) exposes `agent(prompt, opts)`, `parallel(thunks)`, `pipeline(items,...stages)`,
// `phase(title)` (label only), `log`, `args`, `budget`; has NO script filesystem; and **function-
// wraps the script so the ONLY module syntax allowed is the leading `export const meta`** (any other
// `export`/`import` is a SyntaxError). This file is the faithful port to that surface:
//   • agent calls use `agent(prompt, { agentType, label, schema })`.
//   • steps run as `parallel()` over per-step thunks; the cross-step barrier is the single
//     `await parallel(stepThunks)` before the summary stage.
//   • the disk-authoritative synthesis barrier (review #9) + the all-hats-fail degraded write
//     (review #7) run inside a fs-capable agent, because the script has no filesystem.
//   • the PURE helpers below are INLINED copies of ./lib.mjs (the canonical, unit-tested source —
//     this script cannot `import` it). KEEP THEM IN SYNC WITH lib.mjs.
// Behaviour, the args contract, the output paths, and the invariants are UNCHANGED.
//
// ───────────────────────────────────────────────────────────────────────────────
// CONTRACT (the interface Phase 4 + the entrypoint skill depend on)
// ───────────────────────────────────────────────────────────────────────────────
// args = the `hat-matrix`:
//   {
//     goal_slug:    "exploration-pipeline-nxm-claude-workflow-9010-angle",
//     goal_context: "<≤280-char step-neutral intent paragraph; passed to every cell>",
//     exploration_dir: "<OPTIONAL absolute or relative base dir for outputs; default goals/<goal_slug>/exploration>",
//     steps: [
//       { nn:"01", slug:"how-to-...", name:"How to ...?",
//         hats:["contrarian","first-principles","90-10","expert-practitioner","tool-landscape"] },
//       { nn:"02", slug:"...", name:"...",
//         hats:["contrarian","first-principles","90-10"] }   // pure-strategy: gateables omitted
//     ]
//   }
//
// Outputs (md artifact paths UNCHANGED — the Phase-4 / cast-high-level-planner contract):
//   <exploration_dir>/research/{NN}-{slug}-{hat_id}.ai.md   (one per applicable cell; written by the hat agent)
//   <exploration_dir>/playbooks/{NN}-{slug}.ai.md           (exactly one per step; written by the synthesizer)
//   <exploration_dir>/summary.ai.md                         (one; assembled in this script's final stage)
//
// INVARIANTS (load-bearing — do not weaken): angle independence (each cell gets only
// {step, hat_id, goal_context}); non-interactive; synthesizer UNCHANGED (only its input set widens);
// surface-don't-suppress (dropped cells + degraded steps logged + landed in summary.ai.md).

export const meta = {
  name: "cast-explore-workflow",
  description: "N×M exploration engine — fan research across N steps × M hats, synthesize per step, assemble a summary",
  phases: [
    { title: "Research & synthesis", detail: "one cast-hat-researcher per (step,hat) cell → per-step synthesis barrier" },
    { title: "Summary", detail: "assemble summary.ai.md from the step playbooks" },
  ],
};

// ── INLINED pure helpers (canonical source: ./lib.mjs — keep in sync) ──────────────
const HAT_VOCAB = [
  "expert-practitioner",
  "tool-landscape",
  "ai-native",
  "community-wisdom",
  "framework-methodology",
  "contrarian",
  "first-principles",
  "90-10",
];

function safeSlug(s) {
  return String(s).toLowerCase().replace(/[^a-z0-9-]/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "");
}

function degradedPlaceholder(step, droppedHats) {
  const dropped = droppedHats && droppedHats.length ? droppedHats.join(", ") : "(all applicable hats)";
  return (
    `# ${step.name} — Playbook (DEGRADED)\n\n` +
    `> **No surviving research for this step.** Every hat cell was dropped, so no playbook ` +
    `could be synthesized.\n>\n` +
    `> **Cells dropped:** ${dropped}\n>\n` +
    `> This step is flagged DEGRADED in summary.ai.md. Re-run the exploration (or this step) ` +
    `to recover; the synthesizer was deliberately NOT invoked with empty input.\n`
  );
}

function candidateNotePaths(researchDir, step) {
  const nn = step.nn;
  const slug = safeSlug(step.slug);
  const out = [];
  for (const hat of step.hats) {
    if (!HAT_VOCAB.includes(hat)) continue;
    out.push({ hat, path: `${researchDir}/${nn}-${slug}-${hat}.ai.md` });
  }
  return out;
}

function dropManifest(dropped, degraded) {
  let out = "";
  if (degraded.length) {
    out += `\n**Degraded steps** (all hats failed — placeholder playbook):\n`;
    out += `| Step | Reason |\n|---|---|\n`;
    for (const d of degraded) out += `| ${d.nn}-${d.slug} | ${d.reason} |\n`;
  }
  if (dropped.length) {
    out += `\n**Dropped cells** (in the matrix, but failed — distinct from GATED-OUT hats, which were never in the matrix):\n`;
    out += `| Step | Hat | Reason |\n|---|---|---|\n`;
    for (const d of dropped) out += `| ${d.nn}-${d.slug} | ${d.hat} | ${d.reason} |\n`;
  }
  return out;
}

// The structured result the per-step resolver agent returns (the disk-authoritative barrier).
const RESOLVER_SCHEMA = {
  type: "object",
  additionalProperties: false,
  properties: {
    surviving: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        properties: { hat: { type: "string" }, path: { type: "string" } },
        required: ["hat", "path"],
      },
    },
    degraded: { type: "boolean" },
  },
  required: ["surviving", "degraded"],
};

// ───────────────────────────────────────────────────────────────────────────────
// The N×M pipeline (current-API live execution)
// ───────────────────────────────────────────────────────────────────────────────
// Defensive: the Workflow tool may deliver `args` as a JSON string rather than a parsed object.
let A = (typeof args !== "undefined" && args) ? args : {};
if (typeof A === "string") { try { A = JSON.parse(A); } catch (e) { A = {}; } }

const goalSlug = A.goal_slug;
const goalContext = A.goal_context;
const steps = Array.isArray(A.steps) ? A.steps : [];

// Output base dir: caller may pass `exploration_dir` (absolute or relative) to write anywhere
// — e.g. straight into a neoorg goal tree. Defaults to the Diecast convention (backward-compatible).
const explorationDir = A.exploration_dir
  ? String(A.exploration_dir).replace(/\/+$/, "")
  : `goals/${goalSlug}/exploration`;
const researchDir = `${explorationDir}/research`;
const playbooksDir = `${explorationDir}/playbooks`;

const droppedCells = []; // { nn, slug, hat, reason }
const degradedSteps = []; // { nn, slug, reason }

phase("Research & synthesis");

// One thunk per step. Steps run concurrently subject to the global cap (min(16, cores−2), enforced
// natively). The only cross-step barrier is the single `await parallel(stepThunks)` below.
const stepThunks = steps.map((rawStep) => {
  const step = { ...rawStep, slug: safeSlug(rawStep.slug) };
  const matrixHats = step.hats.filter((h) => HAT_VOCAB.includes(h));
  const candidates = candidateNotePaths(researchDir, step);
  const playbookPath = `${playbooksDir}/${step.nn}-${step.slug}.ai.md`;
  const placeholderBody = degradedPlaceholder(step, matrixHats);

  return async () => {
    // ── Fan-out: one clean-context cast-hat-researcher per (step, hat) cell. Angle independence by
    //    construction — each cell receives ONLY {step, hat_id, goal_context}. The cell writes its
    //    own note + contract-v2 terminal JSON, and returns its summary text (or null on failure).
    const cellThunks = matrixHats.map((hat) => () =>
      agent(
        `Research ONE step wearing ONE hat. Write your note + contract-v2 terminal JSON.\n` +
        `step: {"index":"${step.nn}","slug":"${step.slug}","statement":${JSON.stringify(step.name)}}\n` +
        `hat_id: ${hat}\n` +
        `goal_context: ${JSON.stringify(goalContext)}\n` +
        `output_dir: ${explorationDir}/`,
        { agentType: "cast-hat-researcher", label: `${step.nn}-${step.slug}:${hat}` }
      )
    );

    // ── Synthesis barrier: this parallel() JOIN is the barrier — synthesis for THIS step starts
    //    only when every one of its hat cells has terminated.
    const cellResults = await parallel(cellThunks);
    cellResults.forEach((res, i) => {
      if (res === null) log(`cell returned null (failed/skipped): step ${step.nn} hat ${matrixHats[i]}`);
    });

    // ── Disk-authoritative surviving set (review #9), run by a fs-capable agent because the script
    //    has no filesystem. It checks ONLY the exact per-hat candidate paths (so `-code.ai.md` and
    //    slug-prefix collisions are structurally impossible), requires the `hat:` heading, and —
    //    iff NONE survive — writes the LOUD degraded placeholder (review #7).
    const resolved = await agent(
      `You are the synthesis-barrier resolver for ONE exploration step. The research cells (one per ` +
      `hat) just ran; each should have written a note file. Decide which notes are VALID + surviving.\n\n` +
      `Step: nn=${step.nn} slug=${step.slug} name=${JSON.stringify(step.name)}.\n` +
      `Candidate note paths — check ONLY these EXACT paths, never glob the directory:\n` +
      candidates.map((c) => `  - ${c.hat}: ${c.path}`).join("\n") + `\n\n` +
      "A candidate SURVIVES iff the file exists, is non-empty, and contains a line matching " +
      "`hat: <that-hat>`. Otherwise it is a dropped cell.\n" +
      `- If at least one survives: return its {hat, path} list (degraded=false) and write NOTHING.\n` +
      `- If NONE survive: write this EXACT content to ${playbookPath} (create parent dirs), then ` +
      `return degraded=true with an empty surviving list. The content to write is BETWEEN the ` +
      `markers (write what is between them, not the markers):\n` +
      `<<<PLACEHOLDER\n${placeholderBody}\nPLACEHOLDER>>>\n\n` +
      `Use your Read / Bash / Write tools. Return only the structured result.`,
      { agentType: "general-purpose", model: "haiku", effort: "low", label: `barrier:${step.nn}-${step.slug}`, schema: RESOLVER_SCHEMA }
    );

    const surviving = (resolved && Array.isArray(resolved.surviving)) ? resolved.surviving : [];
    const survivingHats = surviving.map((s) => s.hat);
    const droppedHats = matrixHats.filter((h) => !survivingHats.includes(h));
    for (const hat of droppedHats) {
      droppedCells.push({ nn: step.nn, slug: step.slug, hat, reason: "cell dropped (no valid note)" });
      log(`DROPPED cell: step ${step.nn} hat ${hat}`);
    }

    // ── Edge case (review #7): ALL hats failed → the resolver already wrote the placeholder. Flag
    //    the step DEGRADED and do NOT invoke the synthesizer with empty input.
    if (!surviving.length || (resolved && resolved.degraded)) {
      degradedSteps.push({ nn: step.nn, slug: step.slug, reason: `all ${matrixHats.length} hat cells dropped` });
      log(`DEGRADED step ${step.nn}-${step.slug}: all hats failed → placeholder playbook written`);
      return { nn: step.nn, slug: step.slug, degraded: true, surviving: 0 };
    }

    // ── Per-step synthesis: the UNCHANGED cast-playbook-synthesizer, fed the M surviving hat notes
    //    for THIS step (its input set widens from 1 file to M; prompt/contract/output untouched).
    await agent(
      `Synthesize ONE opinionated playbook for this step from its research notes.\n` +
      `step_name: ${JSON.stringify(step.name)}\n` +
      `goal_context: ${JSON.stringify(goalContext)}\n` +
      `research_notes (read ALL of these — they are this step's surviving hat notes):\n` +
      surviving.map((s) => `  - ${s.path}`).join("\n") +
      `\noutput: ${playbookPath}`,
      { agentType: "cast-playbook-synthesizer", label: `synth:${step.nn}-${step.slug}` }
    );

    return { nn: step.nn, slug: step.slug, degraded: false, surviving: surviving.length };
  };
});

const stepResults = await parallel(stepThunks); // barrier across all steps

// ── Final stage: assemble summary.ai.md via the UNCHANGED cast-playbook-synthesizer.
phase("Summary");
await agent(
  `Assemble the exploration summary.ai.md from all step playbooks.\n` +
  `Read every playbook in ${playbooksDir}/ and write ${explorationDir}/summary.ai.md using ` +
  `cast-explore's Phase-3 summary shape VERBATIM (Impact Ratings table sorted by impact, ` +
  `Top Recommendations, Recommended Technology Stack, Architecture Overview, Build Order, ` +
  `Key Risks & Mitigations, Reference Implementations, All Files). Do NOT change that format.\n\n` +
  `THEN append this additive run-metadata section AFTER all the above (never interleaved):\n\n` +
  `## Dropped cells / degraded steps\n` +
  (droppedCells.length === 0 && degradedSteps.length === 0
    ? `(none — every applicable cell produced a note.)\n`
    : dropManifest(droppedCells, degradedSteps)) +
  `\n_Observed concurrency cap on this run machine: min(16, cores−2)._\n`,
  { agentType: "cast-playbook-synthesizer", label: "summary" }
);

log(
  `exploration complete: ${stepResults.length} steps, ` +
  `${droppedCells.length} dropped cell(s), ${degradedSteps.length} degraded step(s). ` +
  `summary: ${explorationDir}/summary.ai.md`
);

return {
  goal_slug: goalSlug,
  steps: stepResults,
  dropped_cells: droppedCells,
  degraded_steps: degradedSteps,
  summary_path: `${explorationDir}/summary.ai.md`,
};
