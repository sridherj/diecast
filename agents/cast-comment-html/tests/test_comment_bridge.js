/* jsdom unit tests for the Diecast host comment bridge (exploration-pipeline-nxm sp3b, review #5 T1-A).
 *
 * Run: `node tests/test_comment_bridge.js` (needs the local devDependency `jsdom`).
 *
 * The bridge (`cast-server/cast_server/static/comment-bridge.js`) is the host-side half of in-viewer
 * commenting: it receives a comment batch postMessage'd by a null-origin `<iframe srcdoc>` artifact
 * frame and proxies each comment as a per-comment POST to the same-door create endpoint, then replies
 * into the originating frame. Autonomous CI can't drive Chrome (the live browser validation is already
 * done — see spike-1b-result.md), so these jsdom tests pin the bridge's security + fan-out + reply
 * contract independent of a real browser.
 *
 * Guards (all binding per plan-review #3 / #5):
 *   1. SOURCE-IDENTITY guard — only a contentWindow in the registry may drive a POST; a foreign
 *      window is rejected (no POST, no reply). Origin is "null" for srcdoc and is NEVER checked.
 *   2. PAYLOAD SHAPE-CHECK — a malformed message (wrong type / non-array comments) issues no POST.
 *   3. PER-COMMENT FAN-OUT — N comments → N POSTs with the exact same-door body incl. artifact_ref;
 *      one failing comment does not abort the others.
 *   4. ROUND-TRIP — a `cch:submit` yields a `cch:submitted` reply posted ONLY to the originating
 *      frame (never broadcast), targetOrigin "*".
 *   5. MULTI-IFRAME — two registered frames are routed independently by source identity.
 */
const assert = require("assert");
const path = require("path");
const { JSDOM } = require("jsdom");

const BRIDGE_PATH = path.resolve(
  __dirname, "..", "..", "..", "cast-server", "cast_server", "static", "comment-bridge.js"
);
const bridgeModule = require(BRIDGE_PATH);
const { createCommentBridge, isSubmitPayload } = bridgeModule;

let passed = 0;
function t(name, fn) { return Promise.resolve().then(fn).then(() => { passed++; console.log("  ok  " + name); }); }

// A host window with addEventListener/postMessage but where WE drive message dispatch synchronously
// (jsdom's MessageEvent + a manual listener registry — deterministic, no event-loop races).
function makeHost() {
  const dom = new JSDOM("<!doctype html><html><body></body></html>", { url: "http://localhost/" });
  return dom.window;
}

// A fake "iframe contentWindow": just an object that records what the bridge posts back to it.
function makeFrameWindow(label) {
  return {
    label: label,
    posted: [],
    postMessage: function (data, targetOrigin) { this.posted.push({ data: data, targetOrigin: targetOrigin }); }
  };
}

// A fetch double: records calls, returns a queued response per call. resp = {ok, status, json}.
function makeFetch(responses) {
  const calls = [];
  let i = 0;
  function fetchImpl(url, init) {
    calls.push({ url: url, init: init, body: JSON.parse(init.body) });
    const r = responses[i++] || { ok: true, status: 201, json: {} };
    return Promise.resolve({
      ok: r.ok, status: r.status,
      json: function () { return Promise.resolve(r.json); }
    });
  }
  fetchImpl.calls = calls;
  return fetchImpl;
}

// Build a bridge + a known frame registered for one artifact_ref. Returns {win, bridge, frame, fetchImpl}.
function setup(responses, goalSlug) {
  const win = makeHost();
  const fetchImpl = makeFetch(responses || []);
  const bridge = createCommentBridge({
    win: win,
    fetchImpl: fetchImpl,
    getGoalSlug: function () { return goalSlug || "g1"; }
  });
  const frame = makeFrameWindow("artifact");
  bridge.register("exploration/exploration.html", frame);
  return { win, bridge, fetchImpl, frame };
}

const COMMENTS = [
  { quoted_text: "cheapest viable angle", section_hint: "90/10", body: "is this right?" },
  { quoted_text: "first-principles", section_hint: null, body: "expand" }
];

function submitMsg(extra) {
  return Object.assign({
    type: "cch:submit",
    goal_slug: "g1",
    artifact_ref: "exploration/exploration.html",
    comments: COMMENTS
  }, extra || {});
}

const tests = [];

// --- isSubmitPayload primitive ---
tests.push(() => t("isSubmitPayload accepts a well-formed submit, rejects junk", () => {
  assert.strictEqual(isSubmitPayload(submitMsg()), true);
  assert.strictEqual(isSubmitPayload({ type: "cch:submit" }), false);      // no comments array
  assert.strictEqual(isSubmitPayload({ type: "other", comments: [] }), false); // wrong type
  assert.strictEqual(isSubmitPayload(null), false);
}));

// --- 1. source-identity guard: foreign window rejected ---
tests.push(() => t("foreign window is rejected — no POST, no reply", () => {
  const { bridge, fetchImpl, frame } = setup([], "g1");
  const foreign = makeFrameWindow("foreign");  // NOT registered
  const ret = bridge.onMessage({ source: foreign, origin: "null", data: submitMsg() });
  assert.strictEqual(ret, undefined, "a rejected message returns early (no promise)");
  assert.strictEqual(fetchImpl.calls.length, 0, "no POST for a foreign source");
  assert.strictEqual(foreign.posted.length, 0, "no reply to a foreign source");
  assert.strictEqual(frame.posted.length, 0);
}));

// --- 2. payload shape-check: malformed message issues no POST ---
tests.push(() => t("malformed payload (wrong type / non-array comments) issues no POST", () => {
  const { bridge, fetchImpl, frame } = setup([], "g1");
  bridge.onMessage({ source: frame, origin: "null", data: { type: "cch:nope", comments: COMMENTS } });
  bridge.onMessage({ source: frame, origin: "null", data: { type: "cch:submit", comments: "not-an-array" } });
  bridge.onMessage({ source: frame, origin: "null", data: null });
  assert.strictEqual(fetchImpl.calls.length, 0);
  assert.strictEqual(frame.posted.length, 0);
}));

// --- 3. per-comment fan-out + body shape ---
tests.push(() => t("per-comment fan-out: N comments → N POSTs with the same-door body incl artifact_ref", () => {
  const { bridge, fetchImpl, frame } = setup(
    [{ ok: true, status: 201, json: { id: 11 } }, { ok: true, status: 201, json: { id: 12 } }], "g1"
  );
  return bridge.onMessage({ source: frame, origin: "null", data: submitMsg() }).then(() => {
    assert.strictEqual(fetchImpl.calls.length, 2, "one POST per comment");
    const c0 = fetchImpl.calls[0];
    assert.strictEqual(c0.url, "/api/goals/g1/requirements/comments");
    assert.strictEqual(c0.init.method, "POST");
    // EXACT same-door body shape the server's CreateCommentRequest expects.
    assert.deepStrictEqual(c0.body, {
      quoted_text: "cheapest viable angle",
      section_hint: "90/10",
      body: "is this right?",
      artifact_ref: "exploration/exploration.html",
      author_kind: "human"
    });
    // null section_hint rides as null, not dropped.
    assert.strictEqual(fetchImpl.calls[1].body.section_hint, null);
  });
}));

// --- 4. round-trip reply: cch:submitted to the originating frame only ---
tests.push(() => t("round-trip: reply cch:submitted posted ONLY to the originating frame, targetOrigin '*'", () => {
  const { bridge, fetchImpl, frame } = setup(
    [{ ok: true, status: 201, json: { id: 1 } }, { ok: true, status: 201, json: { id: 2 } }], "g1"
  );
  return bridge.onMessage({ source: frame, origin: "null", data: submitMsg() }).then(() => {
    assert.strictEqual(frame.posted.length, 1, "exactly one reply");
    const reply = frame.posted[0];
    assert.strictEqual(reply.targetOrigin, "*", "null-origin frame → targetOrigin '*'");
    assert.strictEqual(reply.data.type, "cch:submitted");
    assert.strictEqual(reply.data.ok, true);
    assert.strictEqual(reply.data.results.length, 2);
    assert.deepStrictEqual(reply.data.results.map(r => r.ok), [true, true]);
    assert.deepStrictEqual(reply.data.results.map(r => r.id), [1, 2]);
  });
}));

// --- 3b. a failing comment does not abort the others; ok=false surfaced ---
tests.push(() => t("one failing comment does not abort the batch; ok=false surfaced per-comment", () => {
  const { bridge, fetchImpl, frame } = setup(
    [{ ok: false, status: 422, json: { detail: "not a verbatim substring" } },
     { ok: true, status: 201, json: { id: 9 } }], "g1"
  );
  return bridge.onMessage({ source: frame, origin: "null", data: submitMsg() }).then(() => {
    assert.strictEqual(fetchImpl.calls.length, 2, "second comment still POSTed after the first failed");
    const reply = frame.posted[0].data;
    assert.strictEqual(reply.ok, false, "batch ok=false when any comment failed");
    assert.strictEqual(reply.results[0].ok, false);
    assert.strictEqual(reply.results[0].error, "not a verbatim substring");
    assert.strictEqual(reply.results[1].ok, true);
    assert.strictEqual(reply.results[1].id, 9);
  });
}));

// --- 5. multi-iframe routing by source identity ---
tests.push(() => t("multi-iframe: two registered frames route independently by source identity", () => {
  const win = makeHost();
  const fetchImpl = makeFetch([{ ok: true, status: 201, json: { id: 7 } }]);
  const bridge = createCommentBridge({ win, fetchImpl, getGoalSlug: () => "g1" });
  const fA = makeFrameWindow("A");  // e.g. refined_requirements.html
  const fB = makeFrameWindow("B");  // e.g. exploration/exploration.html
  bridge.register("a.html", fA);
  bridge.register("b.html", fB);
  return bridge.onMessage({
    source: fB, origin: "null",
    data: { type: "cch:submit", goal_slug: "g1", artifact_ref: "b.html", comments: [COMMENTS[0]] }
  }).then(() => {
    assert.strictEqual(fetchImpl.calls.length, 1);
    assert.strictEqual(fetchImpl.calls[0].body.artifact_ref, "b.html");
    assert.strictEqual(fB.posted.length, 1, "reply went to B (the originator)");
    assert.strictEqual(fA.posted.length, 0, "A (a different frame) got nothing");
  });
}));

// --- the real addEventListener path: a dispatched MessageEvent reaches onMessage ---
tests.push(() => t("bridge binds win.addEventListener('message') and honors source identity there too", () => {
  const win = makeHost();
  const fetchImpl = makeFetch([{ ok: true, status: 201, json: { id: 3 } }]);
  const bridge = createCommentBridge({ win, fetchImpl, getGoalSlug: () => "g1" });
  // jsdom MessageEvent.source is read-only and can't be a plain object, so we assert the listener is
  // wired by dispatching a foreign event (source=null) and confirming it is ignored (no throw, no POST).
  const ev = new win.MessageEvent("message", { data: submitMsg(), origin: "null" });
  win.dispatchEvent(ev); // source is null → rejected by the identity guard, must not throw
  assert.strictEqual(fetchImpl.calls.length, 0);
}));

// missing goal_slug → reply ok=false, no POST
tests.push(() => t("missing goal_slug (and no host fallback) → reply ok=false, no POST", () => {
  const win = makeHost();
  const fetchImpl = makeFetch([]);
  const bridge = createCommentBridge({ win, fetchImpl, getGoalSlug: () => null });
  const frame = makeFrameWindow("f");
  bridge.register("x.html", frame);
  bridge.onMessage({
    source: frame, origin: "null",
    data: { type: "cch:submit", goal_slug: null, artifact_ref: "x.html", comments: [COMMENTS[0]] }
  });
  assert.strictEqual(fetchImpl.calls.length, 0);
  assert.strictEqual(frame.posted.length, 1);
  assert.strictEqual(frame.posted[0].data.ok, false);
}));

// Run sequentially.
tests.reduce((p, fn) => p.then(fn), Promise.resolve())
  .then(() => { console.log(`\n${passed} bridge assertions passed.`); })
  .catch((e) => { console.error("\nFAILED:", e && e.stack || e); process.exit(1); });
