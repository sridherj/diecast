// cast-explore-workflow — N×M exploration Workflow engine (JavaScript Workflow script)
//
// THIS IS THE ENGINE. It is the inline-JS `script` the `cast-explore-workflow`
// entrypoint skill passes to the Workflow tool (or saves as a `/named` workflow).
// The G1 live-fire (spike-1a-result.md, run wf_3ae6d3ec-45c) confirmed this exact
// model runs on the real Workflow tool: `agent()`, `parallel()`, `pipeline()`,
// `phase()`, `log()`, `budget`, `args` are the script API the main agent holds.
//
// SUPERSEDES the detailed plan's `workflow.py`: the engine is JavaScript, NOT Python
// (binding G1 correction). This file is the literal script, not a blueprint/prompt.
//
// ───────────────────────────────────────────────────────────────────────────────
// CONTRACT (the interface Phase 4 + the entrypoint skill depend on)
// ───────────────────────────────────────────────────────────────────────────────
// args = the `hat-matrix`:
//   {
//     goal_slug:    "exploration-pipeline-nxm-claude-workflow-9010-angle",
//     goal_context: "<≤280-char step-neutral intent paragraph; passed to every cell>",
//     steps: [
//       { nn:"01", slug:"how-to-...", name:"How to ...?",
//         hats:["contrarian","first-principles","90-10","expert-practitioner","tool-landscape"] },
//       { nn:"02", slug:"...", name:"...",
//         hats:["contrarian","first-principles","90-10"] }   // pure-strategy: gateables omitted
//     ]
//   }
//
// Each (nn, slug, hat_id) triple = exactly ONE fan-out cell → one cast-hat-researcher.
// Outputs (md artifact paths UNCHANGED — the Phase-4 / cast-high-level-planner contract):
//   research/{NN}-{slug}-{hat_id}.ai.md   (one per applicable cell; written by the hat agent)
//   playbooks/{NN}-{slug}.ai.md           (exactly one per step; written by the synthesizer)
//   summary.ai.md                         (one; assembled in this script's final stage)
//
// INVARIANTS (load-bearing — do not weaken):
//  • Angle independence: each cell receives ONLY {step, hat_id, goal_context}. goal_context is the
//    step-neutral intent string — NEVER another hat's note or another step's text. No shared prompt.
//  • Non-interactive: this script NEVER asks the user anything. All human gates (intent, decompose,
//    approve, matrix-confirm) ran in the entrypoint skill BEFORE launch.
//  • Synthesizer UNCHANGED: only its INPUT SET widens (1 file → M surviving hat notes). Its
//    prompt/contract/output path are untouched.
//  • Surface-don't-suppress: dropped cells, queued/over-cap state, and degraded steps are LOGGED
//    and land in summary.ai.md's "Dropped cells / degraded steps" section — never a silent gap.

// The 8 frozen hat_ids (2a vocabulary, verbatim). Used by the barrier glob ∩ intersection
// (review #9) to pin the surviving-note set to EXACTLY {NN}-{slug}-{hat_id}.ai.md and exclude
// `-code.ai.md` contamination + slug-prefix collisions.
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

const ALWAYS_ON = ["contrarian", "first-principles", "90-10"];

// Defense-in-depth: slugs derive from approved step names; sanitize before forming paths.
function safeSlug(s) {
  return String(s).toLowerCase().replace(/[^a-z0-9-]/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "");
}

// Review #7 — all-hats-fail DEGRADED placeholder playbook body. Pure, so it is unit-testable.
// When a step has ZERO surviving notes, the synthesizer is NOT invoked with empty input; instead
// this loud placeholder is written and the step is flagged DEGRADED in summary.ai.md.
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

// ───────────────────────────────────────────────────────────────────────────────
// Barrier note-resolution (review #9 — glob ∩ hat_id intersection)
// ───────────────────────────────────────────────────────────────────────────────
// Resolve a step's surviving hat notes from DISK (the authoritative set), hardening the
// barrier against a child that wrote its note then soft-failed. Then INTERSECT with the
// known hat_id vocabulary so the synthesizer only ever sees {NN}-{slug}-{hat_id}.ai.md:
//   • excludes `…-code.ai.md` (cast-code-explorer output shares the {NN}-{slug}- prefix)
//   • excludes slug-prefix collisions (e.g. `01-auth` vs `01-auth-flow`) — the same exposure
//     Phase 5's SC-001 documents.
// A note also passes a NON-EMPTY + EXPECTED-HAT-HEADING validation (corrupt/empty → treated
// as a dropped cell, never fed to the synthesizer).
function resolveSurvivingNotes(researchDir, step) {
  const nn = step.nn;
  const slug = safeSlug(step.slug);
  const surviving = [];
  for (const hat of step.hats) {
    if (!HAT_VOCAB.includes(hat)) continue; // never spawned / never counted; not in vocab
    const path = `${researchDir}/${nn}-${slug}-${hat}.ai.md`;
    if (!fileExists(path)) continue; // cell dropped (failed → no note written, per 2a contract)
    const body = readFile(path);
    // Validate: non-empty + carries the expected hat front-matter (else corrupt → drop).
    const hasHeading =
      body && body.trim().length > 0 && new RegExp(`(^|\\n)hat:\\s*${hat}\\b`).test(body);
    if (!hasHeading) {
      log(`barrier: step ${nn} hat ${hat} note present but invalid (empty/missing 'hat:' heading) → dropped`);
      continue;
    }
    surviving.push({ hat, path });
  }
  return surviving;
}

// ───────────────────────────────────────────────────────────────────────────────
// The N×M pipeline
// ───────────────────────────────────────────────────────────────────────────────
const goalSlug = args.goal_slug;
const goalContext = args.goal_context;
const explorationDir = `goals/${goalSlug}/exploration`;
const researchDir = `${explorationDir}/research`;
const playbooksDir = `${explorationDir}/playbooks`;

// Run-level bookkeeping for the surface-don't-suppress summary section.
const droppedCells = []; // { nn, slug, hat, reason }
const degradedSteps = []; // { nn, slug, reason }

// pipeline() per step. Steps may run concurrently subject to the global cap — a fast step's
// synthesis need not wait on a slow step's hats. The Workflow tool enforces min(16, cores−2)
// natively and AUTO-QUEUES excess cells; this script hand-rolls NO queue (FR-015).
const stepStages = args.steps.map((rawStep) => {
  const step = { ...rawStep, slug: safeSlug(rawStep.slug) };

  return pipeline(`step-${step.nn}-${step.slug}`, async () => {
    // ── Fan-out: parallel() over M_applicable(step) hats. One clean-context cast-hat-researcher
    //    per (step, hat) cell. The hats list comes from the matrix arg — a gated-out hat is never
    //    spawned. Each cell gets ONLY {step, hat_id, goal_context} (angle independence by
    //    construction). cast-hat-researcher writes its own note + contract-v2 terminal JSON.
    const hatCells = step.hats
      .filter((h) => HAT_VOCAB.includes(h))
      .map((hat) =>
        agent({
          agentType: "cast-hat-researcher",
          // The ONLY three inputs a cell receives — no other hat's framing, no sibling output.
          prompt:
            `Research ONE step wearing ONE hat. Write your note + contract-v2 terminal JSON.\n` +
            `step: {"index":"${step.nn}","slug":"${step.slug}","statement":${JSON.stringify(step.name)}}\n` +
            `hat_id: ${hat}\n` +
            `goal_context: ${JSON.stringify(goalContext)}\n` +
            `output_dir: ${explorationDir}/`,
        })
      );

    // ── Synthesis barrier: parallel() JOIN. Synthesis for THIS step starts only when every one
    //    of its hat cells has terminated (succeeded → note; failed → null). This join IS the barrier.
    const cellResults = await parallel(hatCells);

    // Failure isolation (FR-016, US12): a cell that failed (non-zero terminal / timeout / missing
    //    or `status:"failed"` output JSON) wrote NO note → it surfaces as a dropped cell. We don't
    //    trust the in-memory return for the note SET; we re-derive it from disk (review #9 glob ∩).
    cellResults.forEach((res, i) => {
      const hat = step.hats.filter((h) => HAT_VOCAB.includes(h))[i];
      const ok = res && res.status === "completed";
      if (!ok) {
        const reason = (res && res.errors && res.errors[0]) || "cell failed (no terminal note)";
        droppedCells.push({ nn: step.nn, slug: step.slug, hat, reason });
        log(`DROPPED cell: step ${step.nn} hat ${hat} — ${reason}`);
      }
    });

    // Authoritative surviving set = disk glob ∩ hat_id vocab ∩ non-empty/valid (review #9).
    const surviving = resolveSurvivingNotes(researchDir, step);

    // ── Edge case (review #7): ALL of a step's hats failed → zero surviving notes. Do NOT invoke
    //    the synthesizer with empty input. Write a PLACEHOLDER degraded playbook and flag the step.
    //    A run with all-dropped cells is a LOUD failure, never a silent empty playbook.
    if (surviving.length === 0) {
      const droppedHats = droppedCells.filter((d) => d.nn === step.nn).map((d) => d.hat);
      writeFile(
        `${playbooksDir}/${step.nn}-${step.slug}.ai.md`,
        degradedPlaceholder(step, droppedHats)
      );
      degradedSteps.push({ nn: step.nn, slug: step.slug, reason: `all ${step.hats.length} hat cells dropped` });
      log(`DEGRADED step ${step.nn}-${step.slug}: all hats failed → placeholder playbook written`);
      return { nn: step.nn, slug: step.slug, degraded: true, surviving: 0 };
    }

    // ── Per-step synthesis: the UNCHANGED cast-playbook-synthesizer, fed the M surviving hat notes
    //    for THIS step (its input set widened from 1 file to M; prompt/contract/output untouched).
    await agent({
      agentType: "cast-playbook-synthesizer",
      prompt:
        `Synthesize ONE opinionated playbook for this step from its research notes.\n` +
        `step_name: ${JSON.stringify(step.name)}\n` +
        `goal_context: ${JSON.stringify(goalContext)}\n` +
        `research_notes (read ALL of these — they are this step's surviving hat notes):\n` +
        surviving.map((s) => `  - ${s.path}`).join("\n") +
        `\noutput: ${playbooksDir}/${step.nn}-${step.slug}.ai.md`,
    });

    return { nn: step.nn, slug: step.slug, degraded: false, surviving: surviving.length };
  });
});

// ───────────────────────────────────────────────────────────────────────────────
// Final stage: assemble summary.ai.md (in-script — the G1-confirmed location).
// ───────────────────────────────────────────────────────────────────────────────
// Summary assembly LIVES in the workflow's final stage (live-confirmed at G1), NOT in the
// launching skill. The terminal result returns to the launching session as a message.
phase("summary", async () => {
  const stepResults = await parallel(stepStages); // barrier across all steps

  // Reuse cast-explore's Phase-3 summary SHAPE verbatim (impact ratings, top recommendations,
  // stack, architecture, build order, risks). summary.ai.md FORMAT is Out-of-Scope to change so
  // cast-high-level-planner consumes it unchanged. The Dropped-cells section is ADDITIVE,
  // appended AFTER the consumed sections.
  await agent({
    agentType: "cast-playbook-synthesizer",
    prompt:
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
  });

  // Terminal signal: the result/summary lands back in the launching session as a message.
  log(`exploration complete: ${stepResults.length} steps, ` +
      `${droppedCells.length} dropped cell(s), ${degradedSteps.length} degraded step(s).`);
  return {
    goal_slug: goalSlug,
    steps: stepResults,
    dropped_cells: droppedCells,
    degraded_steps: degradedSteps,
    summary_path: `${explorationDir}/summary.ai.md`,
  };
});

// Surface (don't suppress) the dropped/degraded manifest in the summary.
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

export { HAT_VOCAB, ALWAYS_ON, safeSlug, resolveSurvivingNotes, degradedPlaceholder };
