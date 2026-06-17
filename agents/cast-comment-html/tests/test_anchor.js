/* Pure unit tests for the anchoring helpers — run with `node tests/test_anchor.js`.
 *
 * The defect class these guard: when the quoted text repeats, a comment must re-anchor to the
 * occurrence the reviewer actually selected. A FIXED-WIDTH context window does NOT guarantee that
 * — if the difference between two occurrences lies beyond the window, it picks the wrong one.
 * The fix is uniqueContext(), which grows context until the anchor is unique, with an ordinal
 * fallback for genuinely identical blocks. These tests assert exactly that. */
const assert = require("assert");
const A = require("../assets/anchor.js");
const { chooseOccurrence, uniqueContext, occurrences, commonPrefixLen, commonSuffixLen } = A;

let passed = 0;
function t(name, fn) { fn(); passed++; console.log("  ok  " + name); }

// --- the common-affix primitives ---
t("commonPrefixLen counts leading matches", () => {
  assert.strictEqual(commonPrefixLen("closed section", "closed bracket"), 7);
  assert.strictEqual(commonPrefixLen("", "abc"), 0);
});
t("commonSuffixLen counts trailing matches", () => {
  assert.strictEqual(commonSuffixLen("the Status", "old Status"), 7);
});

// --- basic context disambiguation ---
const text = "Status: open. Later the Status: closed section.";
const firstIdx = text.indexOf("Status:");
const secondIdx = text.indexOf("Status:", firstIdx + 1);
t("no context → first occurrence (back-compat)", () => {
  assert.strictEqual(chooseOccurrence(text, "Status:", "", ""), firstIdx);
});
t("prefix selects the second occurrence", () => {
  assert.strictEqual(chooseOccurrence(text, "Status:", "Later the ", ""), secondIdx);
});
t("suffix selects the first occurrence", () => {
  assert.strictEqual(chooseOccurrence(text, "Status:", "", " open"), firstIdx);
});

// === THE BREAK: a fixed window is NOT enough; uniqueContext must grow past the filler ===
// Two "TOTAL"s, each wrapped in 60 identical filler chars; they differ only FAR away (>48).
const fill = "-".repeat(60);
const farDoc = "Section ALPHA " + fill + " TOTAL " + fill + " endA. Section BETA " + fill + " TOTAL " + fill + " endB.";
const totals = occurrences(farDoc, "TOTAL");
assert.strictEqual(totals.length, 2);

t("REGRESSION: a fixed 48-char window picks the WRONG occurrence", () => {
  const target = totals[1]; // the BETA one
  const pre48 = farDoc.slice(target - 48, target);
  const suf48 = farDoc.slice(target + 5, target + 5 + 48);
  // both occurrences see identical 48-char filler context → tie → falls to first. Demonstrates the bug.
  assert.notStrictEqual(chooseOccurrence(farDoc, "TOTAL", pre48, suf48), target);
});

t("uniqueContext grows past the filler so the anchor is unique", () => {
  const target = totals[1];
  const uc = uniqueContext(farDoc, target, "TOTAL".length, { buffer: 8, max: 400 });
  // the grown context must actually isolate the target — re-anchor lands on it
  assert.strictEqual(chooseOccurrence(farDoc, "TOTAL", uc.prefix, uc.suffix, uc.ordinal), target);
  // and it must have grown beyond the 60-char filler to reach the distinguishing "BETA"/"endB"
  assert.ok(uc.prefix.length > 60 || uc.suffix.length > 60, "expected context to grow past the 60-char filler");
});

t("uniqueContext also pins the FIRST occurrence correctly", () => {
  const target = totals[0];
  const uc = uniqueContext(farDoc, target, "TOTAL".length, { buffer: 8, max: 400 });
  assert.strictEqual(chooseOccurrence(farDoc, "TOTAL", uc.prefix, uc.suffix, uc.ordinal), target);
});

// === THE HARD FLOOR: two byte-identical blocks — no finite context can disambiguate ===
// Only the ordinal (TextPositionSelector) can. uniqueContext returns the right ordinal; chooseOccurrence uses it.
const block = "Acceptance criteria: the system MUST respond within 200ms under load.";
const dup = block + "\n\n" + block; // the SAME sentence twice, verbatim
const dups = occurrences(dup, "MUST respond within 200ms");
assert.strictEqual(dups.length, 2);

t("identical blocks → uniqueContext records the ordinal", () => {
  const target = dups[1];
  const uc = uniqueContext(dup, target, "MUST respond within 200ms".length, { buffer: 8, max: 400 });
  assert.strictEqual(uc.ordinal, 1);
});
t("identical blocks → ordinal fallback picks the right occurrence under a full context tie", () => {
  const target = dups[1];
  const uc = uniqueContext(dup, target, "MUST respond within 200ms".length, { buffer: 8, max: 400 });
  assert.strictEqual(chooseOccurrence(dup, "MUST respond within 200ms", uc.prefix, uc.suffix, uc.ordinal), target);
});

// --- edge cases ---
t("single occurrence ignores context", () => {
  assert.strictEqual(chooseOccurrence("only here once", "once", "wrong ", " wrong"), "only here ".length);
});
t("absent quote → -1", () => {
  assert.strictEqual(chooseOccurrence(text, "nope", "", ""), -1);
});
t("uniqueContext on a unique quote still returns a buffer", () => {
  const uc = uniqueContext("a UNIQUE thing here", 2, "UNIQUE".length, { buffer: 5, max: 100 });
  assert.ok(uc.prefix.length <= 5 && uc.suffix.length <= 5);
  assert.strictEqual(uc.ordinal, 0);
});

console.log(`\n${passed} assertions passed.`);
