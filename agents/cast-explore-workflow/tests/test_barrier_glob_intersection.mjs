// test_barrier_glob_intersection.mjs — review #9 unit test.
//
// Pins the synthesis-barrier surviving-note resolution: glob ∩ hat_id vocabulary, pinned to the
// exact {NN}-{slug}-{hat_id}.ai.md set, EXCLUDING `-code.ai.md` contamination and slug-prefix
// collisions, AND treating empty/corrupt notes (missing the `hat:` heading) as dropped.
//
// Run: node agents/cast-explore-workflow/tests/test_barrier_glob_intersection.mjs
// Exit 0 = pass; non-zero = fail.
//
// workflow.mjs references Workflow-tool runtime globals (fileExists/readFile/writeFile/log/
// agent/parallel/pipeline/phase/args). We inject benign stubs for the module-load side effects
// and a controllable virtual filesystem for the pure helper under test.

import assert from "node:assert";

// ── Virtual filesystem the helper reads through the injected globals. ──────────────
let VFS = {};
globalThis.fileExists = (p) => Object.prototype.hasOwnProperty.call(VFS, p);
globalThis.readFile = (p) => VFS[p];
globalThis.writeFile = () => {};
globalThis.log = () => {};
// Stubs so the module body (which builds pipeline stages at import) doesn't throw.
globalThis.agent = () => ({ status: "completed" });
globalThis.parallel = async (xs) => (Array.isArray(xs) ? xs : []);
globalThis.pipeline = (_name, _fn) => ({ _name });
globalThis.phase = (_name, _fn) => ({ _name });
globalThis.args = { goal_slug: "g", goal_context: "c", steps: [] };

const mod = await import("../lib.mjs");
const { resolveSurvivingNotes, safeSlug, HAT_VOCAB } = mod;

let failures = 0;
function check(name, fn) {
  try {
    fn();
    console.log("OK   " + name);
  } catch (e) {
    failures++;
    console.error("FAIL " + name + " — " + e.message);
  }
}

function validNote(hat) {
  return `---\nstep_index: "01"\nstep_slug: alpha\nhat: ${hat}\n---\n# ${hat}: Alpha\nbody\n`;
}

const researchDir = "goals/g/exploration/research";
const step = {
  nn: "01",
  slug: "alpha",
  name: "Alpha?",
  hats: ["contrarian", "first-principles", "90-10", "tool-landscape"],
};

check("intersects to exactly the matrix hats present on disk", () => {
  VFS = {
    [`${researchDir}/01-alpha-contrarian.ai.md`]: validNote("contrarian"),
    [`${researchDir}/01-alpha-first-principles.ai.md`]: validNote("first-principles"),
    [`${researchDir}/01-alpha-90-10.ai.md`]: validNote("90-10"),
    // tool-landscape cell DROPPED (no file) → must not appear.
  };
  const surviving = resolveSurvivingNotes(researchDir, step);
  const hats = surviving.map((s) => s.hat).sort();
  assert.deepStrictEqual(hats, ["90-10", "contrarian", "first-principles"]);
});

check("excludes -code.ai.md contamination (cast-code-explorer shares the prefix)", () => {
  VFS = {
    [`${researchDir}/01-alpha-contrarian.ai.md`]: validNote("contrarian"),
    // a code-explorer note with the same NN-slug prefix must NEVER be counted:
    [`${researchDir}/01-alpha-code.ai.md`]: "# code map\nstuff\n",
  };
  const surviving = resolveSurvivingNotes(researchDir, step);
  assert.deepStrictEqual(surviving.map((s) => s.hat), ["contrarian"]);
  assert.ok(
    !surviving.some((s) => s.path.endsWith("-code.ai.md")),
    "code note leaked into surviving set"
  );
});

check("excludes slug-prefix collisions (01-alpha vs 01-alpha-flow)", () => {
  // A sibling step `01-alpha-flow` whose contrarian note shares the `01-alpha-` prefix must
  // NOT be globbed into step `01-alpha`'s surviving set. Because we build the path per
  // (matrix hat) rather than a bare prefix-glob, the collision is structurally impossible.
  VFS = {
    [`${researchDir}/01-alpha-contrarian.ai.md`]: validNote("contrarian"),
    [`${researchDir}/01-alpha-flow-contrarian.ai.md`]: validNote("contrarian"),
  };
  const surviving = resolveSurvivingNotes(researchDir, step);
  assert.deepStrictEqual(surviving.map((s) => s.path), [
    `${researchDir}/01-alpha-contrarian.ai.md`,
  ]);
});

check("treats empty / heading-less note as dropped (corrupt → null cell)", () => {
  VFS = {
    [`${researchDir}/01-alpha-contrarian.ai.md`]: validNote("contrarian"),
    [`${researchDir}/01-alpha-90-10.ai.md`]: "", // empty → corrupt
    [`${researchDir}/01-alpha-first-principles.ai.md`]: "# no front-matter\nbody\n", // missing hat: heading
  };
  const surviving = resolveSurvivingNotes(researchDir, step);
  assert.deepStrictEqual(surviving.map((s) => s.hat), ["contrarian"]);
});

check("never counts a hat outside the frozen vocabulary", () => {
  const weirdStep = { ...step, hats: ["contrarian", "not-a-real-hat"] };
  VFS = {
    [`${researchDir}/01-alpha-contrarian.ai.md`]: validNote("contrarian"),
    [`${researchDir}/01-alpha-not-a-real-hat.ai.md`]: "---\nhat: not-a-real-hat\n---\nx\n",
  };
  const surviving = resolveSurvivingNotes(researchDir, weirdStep);
  assert.deepStrictEqual(surviving.map((s) => s.hat), ["contrarian"]);
  assert.ok(HAT_VOCAB.length === 8, "expected 8 frozen hats");
});

check("safeSlug strips path-traversal / unsafe chars", () => {
  assert.strictEqual(safeSlug("../../etc/passwd"), "etc-passwd");
  assert.strictEqual(safeSlug("How To X?"), "how-to-x");
});

if (failures) {
  console.error(`\n${failures} check(s) failed.`);
  process.exit(1);
}
console.log("\nAll barrier glob∩hat_id checks passed.");
