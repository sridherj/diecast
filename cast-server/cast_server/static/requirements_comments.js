/* requirements_comments.js — Phase 4 (sp5): the locked commenting UX (decision #7) in
   vanilla JS. NO framework/library. htmx is the transport (hx-* on the tray host, composer,
   thread items); selection + <mark> placement are plain DOM. ALL comment content reaches the
   DOM via server-rendered autoescaped fragments (tray.html / thread_item.html) or textContent
   — never innerHTML of raw API strings. Progressive enhancement: a bare file:// (no slug,
   scripts 404) no-ops and the render stays a readable read-only document. */
(function () {
  "use strict";
  var slug = document.body.getAttribute("data-goal-slug");
  if (!slug) return;                       // bare-file render ⇒ stay read-only
  var apiBase = "/api/goals/" + slug + "/requirements";
  var doc = document.querySelector(".rr-document");
  if (!doc) return;

  // --- <mark> placement ----------------------------------------------------------------
  function clearMarks() {
    document.querySelectorAll("mark.comment-mark").forEach(function (m) {
      var p = m.parentNode;
      while (m.firstChild) p.insertBefore(m.firstChild, m);
      p.removeChild(m); p.normalize();
    });
  }
  // Wrap the first occurrence of `quote` within `container` in <mark>, splitting boundary
  // text nodes so a quote that straddles inline tags (e.g. <strong>) still highlights.
  function highlight(container, quote, id, title) {
    var walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, null);
    var nodes = [], concat = "", n;
    while ((n = walker.nextNode())) {
      var start = concat.length; concat += n.nodeValue;
      nodes.push({ node: n, start: start, end: concat.length });
    }
    var at = concat.indexOf(quote);
    if (at < 0) return false;              // not found verbatim ⇒ surfaces in the tray
    var end = at + quote.length;
    nodes.forEach(function (e) {
      if (e.end <= at || e.start >= end) return;          // no overlap with the quote
      var node = e.node;
      var ls = Math.max(0, at - e.start);
      var le = Math.min(node.nodeValue.length, end - e.start);
      if (ls > 0) { node = node.splitText(ls); le -= ls; }
      if (le < node.nodeValue.length) node.splitText(le);
      var mark = document.createElement("mark");
      mark.className = "comment-mark";
      mark.setAttribute("data-comment-id", id);
      if (title) mark.setAttribute("title", title);
      node.parentNode.insertBefore(mark, node);
      mark.appendChild(node);
    });
    return true;
  }
  // Toggle the read-time `.comment-unplaced` badge on a tray item whose open, non-displaced
  // quote did NOT place on this served DOM (highlight()→false). Derived, nothing stored —
  // surfaces BOTH in-block (override: served+flagged) and cross-boundary misses uniformly.
  // Idempotent; clears (badge removed) when `on` is false so a later fixed render drops it.
  function setUnplacedBadge(id, on) {
    var item = document.getElementById("comment-" + id);
    if (!item) return;                                    // tray not rendered yet ⇒ no-op
    item.classList.toggle("comment-unplaced", on);
    var meta = item.querySelector(".comment-meta");
    var badge = item.querySelector(".comment-unplaced-badge");
    if (on) {
      if (!badge && meta) {
        badge = document.createElement("span");
        badge.className = "comment-unplaced-badge";
        badge.setAttribute("title", "This comment's quote is not visible on the current render");
        badge.textContent = "not visible on this render";
        meta.appendChild(badge);
      }
    } else if (badge) {
      badge.remove();
    }
  }
  function placeMarks(comments) {
    clearMarks();
    comments.forEach(function (c) {
      if (c.state !== "open" || c.displaced) return;      // displaced/orphaned ⇒ tray only
      var title = c.author + ": " + String(c.body || "").slice(0, 80);
      var placed = highlight(doc, c.quoted_text, c.id, title);
      setUnplacedBadge(c.id, !placed);                    // surface a non-displaced open miss
    });
  }

  // --- Goal Card convergence chip (fills the Phase 3a [PENDING Phase 4] slot) -----------
  function updateCard(comments) {
    var card = document.querySelector(".goal-card");
    if (!card) return;
    var open = comments.filter(function (c) { return c.state === "open"; }).length;
    var chip = card.querySelector(".goal-card__convergence");
    if (!chip) {
      chip = document.createElement("span");
      chip.className = "goal-card__convergence";
      card.insertBefore(chip, card.querySelector(".goal-card__job"));   // fills the [PENDING Phase 4] slot
    }
    var converged = open === 0;
    chip.setAttribute("data-convergence", converged ? "converged" : "unconverged");
    chip.textContent = converged ? "converged" : "unconverged · " + open + " open";
  }

  // --- refresh: re-read comments, re-place marks, refresh the card ----------------------
  function refresh() {
    fetch(apiBase + "/comments", { headers: { Accept: "application/json" } })
      .then(function (r) { return r.ok ? r.json() : { comments: [] }; })
      .then(function (data) {
        var comments = data.comments || [];
        placeMarks(comments);
        updateCard(comments);
      })
      .catch(function () { /* network blip — keep the last good render */ });
  }
  function reloadTray() { document.body.dispatchEvent(new CustomEvent("comments:refresh")); }

  // --- selection → 💬 pill → inline composer -------------------------------------------
  var pill = null, composer = null;
  function removePill() { if (pill) { pill.remove(); pill = null; } }
  function closeComposer() { if (composer) { composer.remove(); composer = null; } }
  function nearestHeading(node) {
    var el = node.nodeType === 1 ? node : node.parentNode;
    while (el && el !== doc) {
      var h = el.previousElementSibling;
      while (h) {
        if (/^H[1-3]$/.test(h.tagName)) return h.textContent.trim();
        h = h.previousElementSibling;
      }
      el = el.parentNode;
    }
    return "";
  }
  function showComposer(range, quote) {
    closeComposer(); removePill();
    var tpl = document.querySelector(".comment-composer-template");
    if (!tpl) return;
    composer = tpl.content.firstElementChild.cloneNode(true);
    composer.querySelector("[data-role='quote']").textContent = quote;
    composer.querySelector("[data-role='quoted-text']").value = quote;
    composer.querySelector("[data-role='section-hint']").value = nearestHeading(range.startContainer);
    document.body.appendChild(composer);
    var r = range.getBoundingClientRect();
    var below = r.bottom + 8;
    var flip = below + composer.offsetHeight > window.innerHeight;   // flip up near the viewport bottom
    composer.style.top = (window.scrollY + (flip ? Math.max(0, r.top - 8 - composer.offsetHeight) : below)) + "px";
    composer.style.left = (window.scrollX + r.left) + "px";
    composer.querySelector("[data-role='cancel']").addEventListener("click", closeComposer);
    if (window.htmx) window.htmx.process(composer);
    composer.querySelector("textarea").focus();
  }
  function onMouseUp(e) {
    if (composer && composer.contains(e.target)) return;
    removePill();
    var sel = window.getSelection();
    var quote = sel && sel.toString().trim();
    if (!quote || !sel.rangeCount) return;
    var range = sel.getRangeAt(0);
    if (!doc.contains(range.startContainer)) return;
    var rect = range.getBoundingClientRect();
    pill = document.createElement("button");
    pill.type = "button";
    pill.className = "comment-pill";
    pill.textContent = "💬 Comment";
    pill.style.top = (window.scrollY + rect.top - 34) + "px";
    pill.style.left = (window.scrollX + rect.left) + "px";
    pill.addEventListener("mousedown", function (ev) { ev.preventDefault(); showComposer(range, quote); });
    document.body.appendChild(pill);
  }

  // --- discoverable commenting affordance (US6 / FR-014 / SC-006) -----------------------
  // A visible control + a hint that *states* the otherwise-hidden select gesture, injected
  // into the .rr-controls bar so an unprompted first-time reader can comment without guessing.
  // Mirrors the convergence-chip injection (updateCard): idempotent, defensively no-ops if the
  // bar is absent on an older cached artifact, and NEVER a new creation path — the click teaches
  // + surfaces the tray; selection → pill → composer stays the only way to create (decision #7).
  // Lives behind the slug guard above, so a bare file:// render (scripts 404) never shows it.
  function injectAffordance() {
    var controls = document.querySelector(".rr-controls");
    if (!controls) return;                                  // older cached artifact ⇒ no-op
    if (controls.querySelector(".comment-affordance")) return;  // idempotent on re-init
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "comment-affordance";
    btn.textContent = "💬 Comment";
    var hint = document.createElement("span");
    hint.className = "comment-affordance__hint";
    hint.textContent = "select any text to comment";       // states the gesture (SC-006)
    btn.addEventListener("click", function () {
      var host = document.querySelector(".comment-tray-host");
      if (host) host.scrollIntoView({ block: "start", behavior: "smooth" });   // reveal + scroll
      hint.classList.add("comment-affordance__hint--pulse");                    // draw the eye ~1.5s
      setTimeout(function () { hint.classList.remove("comment-affordance__hint--pulse"); }, 1500);
    });
    controls.appendChild(btn);
    controls.appendChild(hint);
  }

  // --- click a <mark> → reveal its thread item in the tray (the autoescaped fragment) ---
  function onClick(e) {
    var m = e.target.closest && e.target.closest("mark.comment-mark");
    if (!m) { if (pill && !(e.target.closest && e.target.closest(".comment-pill"))) removePill(); return; }
    var item = document.getElementById("comment-" + m.getAttribute("data-comment-id"));
    if (!item) return;
    item.scrollIntoView({ block: "center" });
    item.classList.add("comment-thread-item--flash");
    setTimeout(function () { item.classList.remove("comment-thread-item--flash"); }, 1200);
  }

  function init() {
    refresh();
    injectAffordance();
    doc.addEventListener("mouseup", onMouseUp);
    document.addEventListener("click", onClick);
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") { closeComposer(); removePill(); } });
    // A successful composer POST: close the draft, re-sync marks, reload the tray.
    document.body.addEventListener("htmx:afterRequest", function (e) {
      if (composer && composer.contains(e.target) && e.detail && e.detail.successful) {
        closeComposer(); refresh(); reloadTray();
      }
    });
    // A tray reload or a resolve/reopen swap changes state → re-place marks (resolved loses its <mark>).
    document.body.addEventListener("htmx:afterSwap", function (e) {
      var t = e.target;
      if (t.closest && (t.closest(".comment-tray-host") || (t.classList && t.classList.contains("comment-thread-item")))) refresh();
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
