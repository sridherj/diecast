// test_all_hats_fail_placeholder.mjs — review #7 unit test.
//
// Pins the all-hats-fail edge case: when a step has ZERO surviving notes, the engine writes a
// LOUD DEGRADED placeholder playbook and NEVER invokes cast-playbook-synthesizer with empty input.
//
// Run: node agents/cast-explore-workflow/tests/test_all_hats_fail_placeholder.mjs
// Exit 0 = pass; non-zero = fail.

import assert from "node:assert";

// Inject benign runtime-global stubs so the module body loads without the Workflow tool.
globalThis.fileExists = () => false;
globalThis.readFile = () => "";
globalThis.writeFile = () => {};
globalThis.log = () => {};
globalThis.agent = () => ({ status: "completed" });
globalThis.parallel = async (xs) => (Array.isArray(xs) ? xs : []);
globalThis.pipeline = (_n, _f) => ({});
globalThis.phase = (_n, _f) => ({});
globalThis.args = { goal_slug: "g", goal_context: "c", steps: [] };

const { degradedPlaceholder } = await import("../lib.mjs");

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

const step = { nn: "02", slug: "pick-a-strategy", name: "Pick a strategy?" };

check("placeholder is clearly marked DEGRADED", () => {
  const body = degradedPlaceholder(step, ["contrarian", "first-principles", "90-10"]);
  assert.ok(/Playbook \(DEGRADED\)/.test(body), "missing DEGRADED marker in heading");
  assert.ok(/No surviving research for this step/.test(body), "missing loud failure statement");
});

check("placeholder lists the dropped hats (surface, don't suppress)", () => {
  const body = degradedPlaceholder(step, ["contrarian", "90-10"]);
  assert.ok(/Cells dropped:\*\* contrarian, 90-10/.test(body), "dropped hats not surfaced");
});

check("placeholder asserts the synthesizer was NOT called with empty input", () => {
  const body = degradedPlaceholder(step, ["contrarian"]);
  assert.ok(
    /NOT invoked with empty input/.test(body),
    "placeholder must record that synthesizer was skipped on empty input"
  );
});

check("placeholder degrades gracefully with no recorded dropped-hat list", () => {
  const body = degradedPlaceholder(step, []);
  assert.ok(/Cells dropped:\*\* \(all applicable hats\)/.test(body), "empty dropped list not handled");
});

check("placeholder carries the step name + the playbook path keyed by NN-slug", () => {
  const body = degradedPlaceholder(step, ["contrarian"]);
  assert.ok(body.startsWith("# Pick a strategy? — Playbook (DEGRADED)"), "step name not in heading");
});

if (failures) {
  console.error(`\n${failures} check(s) failed.`);
  process.exit(1);
}
console.log("\nAll all-hats-fail placeholder checks passed.");
