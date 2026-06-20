/* Diecast host-side comment bridge (exploration-pipeline-nxm sp3b).
 *
 * The dual viewer embeds render-class `.html` artifacts in `<iframe srcdoc sandbox="allow-scripts">`
 * (null origin, NO allow-same-origin). The injected cast-comment-html layer cannot fetch the
 * same-door API from inside that null-origin frame, so on Submit it `postMessage`s the comment batch
 * to the host (this page). This bridge proxies each comment as a per-comment POST to the SAME same-door
 * create endpoint, then replies into the originating frame so the layer can toast success/failure.
 *
 * Security (1b browser-confirmed, plan-review #3 binding):
 *  - srcdoc frames are null-origin → `event.origin === "null"`; we DO NOT check origin.
 *  - We validate SOURCE IDENTITY: the message must come from a `contentWindow` in our iframe registry
 *    (artifact_ref → contentWindow). A foreign window is rejected before any POST.
 *  - The payload shape is checked before any fetch (never echo arbitrary postMessage data into a POST).
 *  - The reply is posted with targetOrigin "*" (a null-origin frame cannot be targeted by URL) and ONLY
 *    to the originating contentWindow — never broadcast. Multiple commentable iframes per tab are
 *    supported (e.g. exploration.html + refined_requirements.html each register their own frame).
 *
 * Structured as a factory (`createCommentBridge`) taking injected `win`/`fetchImpl`/`getGoalSlug` so it
 * is unit-testable under jsdom with no real browser (autonomous CI can't drive Chrome; 1b already did
 * the live validation). The browser auto-init at the bottom wires the real window + fetch.
 */
(function (root) {
  "use strict";

  function isSubmitPayload(d) {
    return !!d && d.type === "cch:submit" && Array.isArray(d.comments);
  }

  function createCommentBridge(opts) {
    opts = opts || {};
    var win = opts.win;                                   // the host window (real or jsdom)
    var fetchImpl = opts.fetchImpl || (win && win.fetch); // injectable for tests
    var getGoalSlug = opts.getGoalSlug || function () { return null; };

    // artifact_ref → contentWindow. Source-identity is validated against the VALUES (the registered
    // contentWindows), so a frame is accepted even if its payload's artifact_ref disagrees with how it
    // was registered — identity, not a client-supplied string, is the trust anchor.
    var registry = Object.create(null);

    function register(artifactRef, contentWindow) {
      if (artifactRef && contentWindow) registry[artifactRef] = contentWindow;
    }
    function unregister(artifactRef) { delete registry[artifactRef]; }
    function knownWindow(w) {
      for (var k in registry) { if (registry[k] === w) return true; }
      return false;
    }

    function postUrl(goalSlug) {
      return "/api/goals/" + encodeURIComponent(goalSlug) + "/requirements/comments";
    }

    // POST one comment through the same-door create endpoint. Returns a promise of {ok, id|error}.
    function postOne(goalSlug, artifactRef, c) {
      var body = {
        quoted_text: c.quoted_text,
        section_hint: c.section_hint || null,
        body: c.body,
        artifact_ref: artifactRef || null,
        author_kind: "human"
      };
      return fetchImpl(postUrl(goalSlug), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      }).then(function (r) {
        return r.json().catch(function () { return {}; }).then(function (j) {
          if (r.ok) return { ok: true, id: (j && j.id) != null ? j.id : null };
          return { ok: false, error: (j && j.detail) || ("HTTP " + r.status) };
        });
      }).catch(function (e) {
        return { ok: false, error: String((e && e.message) || e) };
      });
    }

    // Reply ONLY into the originating frame (never broadcast). targetOrigin "*" — a null-origin srcdoc
    // frame cannot be addressed by a concrete origin.
    function reply(sourceWindow, ok, results) {
      try {
        sourceWindow.postMessage({ type: "cch:submitted", ok: ok, results: results }, "*");
      } catch (e) { /* a torn-down frame: nothing to surface into; drop the reply, never throw */ }
    }

    function onMessage(event) {
      var src = event.source;
      // Guard 1 — SOURCE IDENTITY. Origin is "null" for srcdoc; we never check it. Only a window in
      // the registry may drive a POST. Reject foreign windows silently (no reply, no POST).
      if (!src || !knownWindow(src)) return;
      // Guard 2 — payload shape. Never feed arbitrary postMessage data into a fetch.
      var d = event.data;
      if (!isSubmitPayload(d)) return;

      var goalSlug = d.goal_slug || getGoalSlug();
      if (!goalSlug) { reply(src, false, []); return; }
      var artifactRef = d.artifact_ref || null;

      // Per-comment fan-out — a failure on one comment does NOT abort the others (surface, don't
      // suppress). Each result rides back so the iframe layer can toast per-comment outcomes.
      var jobs = d.comments.map(function (c) { return postOne(goalSlug, artifactRef, c); });
      return Promise.all(jobs).then(function (results) {
        var allOk = results.every(function (r) { return r && r.ok; });
        reply(src, allOk, results);
        return results;
      });
    }

    if (win && win.addEventListener) win.addEventListener("message", onMessage);

    return {
      register: register,
      unregister: unregister,
      knownWindow: knownWindow,
      onMessage: onMessage,
      _registry: registry
    };
  }

  // --- browser auto-init -------------------------------------------------------------------------
  // Build a single bridge bound to the real window, then (re)scan the DOM for commentable artifact
  // iframes after every HTMX swap (phase tabs + the artifact sidebar load via swaps). Each
  // `.artifact-html-frame` is registered by its goal-relative artifact_ref (stamped as a data-attr by
  // the viewer macro) once its contentWindow exists.
  function autoInit(win) {
    if (!win || !win.document) return null;
    var goalSlug = null;
    var bridge = createCommentBridge({
      win: win,
      getGoalSlug: function () { return goalSlug; }
    });

    function scan() {
      var frames = win.document.querySelectorAll("iframe.artifact-html-frame[data-artifact-ref]");
      Array.prototype.forEach.call(frames, function (f) {
        var ref = f.getAttribute("data-artifact-ref");
        var gs = f.getAttribute("data-goal-slug");
        if (gs) goalSlug = gs;
        if (f.contentWindow) bridge.register(ref, f.contentWindow);
        else f.addEventListener("load", function () { bridge.register(ref, f.contentWindow); });
      });
    }

    if (win.document.body) {
      win.document.body.addEventListener("htmx:afterSwap", scan);
    }
    if (win.document.readyState !== "loading") scan();
    else win.document.addEventListener("DOMContentLoaded", scan);
    win.__castCommentBridge__ = bridge;
    return bridge;
  }

  // Export for the node/jsdom test; auto-init in a real browser.
  if (typeof module !== "undefined" && module.exports) {
    module.exports = { createCommentBridge: createCommentBridge, isSubmitPayload: isSubmitPayload, autoInit: autoInit };
  }
  if (typeof window !== "undefined" && window.document) autoInit(window);
})(typeof self !== "undefined" ? self : this);
