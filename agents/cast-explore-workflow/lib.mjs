// cast-explore-workflow/lib.mjs — PURE helpers for the N×M exploration engine.
//
// These are the canonical, unit-tested definitions (see tests/). They live in a normal ESM module
// (with `export`) so `node` can import them. The Workflow ENGINE (`workflow.mjs`) cannot `import`
// or `export` anything beyond `export const meta` — the current Workflow runtime function-wraps the
// script and rejects other module syntax — so it carries INLINED copies of the small helpers it
// needs at runtime. **Keep the inlined copies in workflow.mjs in sync with these.**

// The 8 frozen hat_ids (2a vocabulary, verbatim). Pin the surviving-note set to EXACTLY
// {NN}-{slug}-{hat_id}.ai.md, excluding `-code.ai.md` contamination + slug-prefix collisions.
export const HAT_VOCAB = [
  "expert-practitioner",
  "tool-landscape",
  "ai-native",
  "community-wisdom",
  "framework-methodology",
  "contrarian",
  "first-principles",
  "90-10",
];

export const ALWAYS_ON = ["contrarian", "first-principles", "90-10"];

// Defense-in-depth: slugs derive from approved step names; sanitize before forming paths.
export function safeSlug(s) {
  return String(s).toLowerCase().replace(/[^a-z0-9-]/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "");
}

// Review #7 — all-hats-fail DEGRADED placeholder playbook body. Pure, so it is unit-testable.
export function degradedPlaceholder(step, droppedHats) {
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

// Review #9 — disk-authoritative barrier note-resolution (glob ∩ hat_id vocab ∩ non-empty/valid).
// CANONICAL SPEC. On the current runtime the live barrier is performed by a fs-capable agent that
// mirrors this exact rule (workflow.mjs delegates it, since the script has no filesystem). Resolves
// a step's surviving hat notes from DISK through injected globals (fileExists/readFile/log).
export function resolveSurvivingNotes(researchDir, step) {
  const nn = step.nn;
  const slug = safeSlug(step.slug);
  const surviving = [];
  for (const hat of step.hats) {
    if (!HAT_VOCAB.includes(hat)) continue; // never spawned / never counted; not in vocab
    const path = `${researchDir}/${nn}-${slug}-${hat}.ai.md`;
    if (!fileExists(path)) continue; // cell dropped (failed → no note written, per 2a contract)
    const body = readFile(path);
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

// Pure: the EXACT per-(matrix hat) candidate note paths for a step. The live barrier agent checks
// ONLY these (never a bare prefix-glob), which is why `-code.ai.md` + slug-prefix collisions are
// structurally impossible.
export function candidateNotePaths(researchDir, step) {
  const nn = step.nn;
  const slug = safeSlug(step.slug);
  const out = [];
  for (const hat of step.hats) {
    if (!HAT_VOCAB.includes(hat)) continue;
    out.push({ hat, path: `${researchDir}/${nn}-${slug}-${hat}.ai.md` });
  }
  return out;
}

// Surface (don't suppress) the dropped/degraded manifest in the summary.
export function dropManifest(dropped, degraded) {
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
