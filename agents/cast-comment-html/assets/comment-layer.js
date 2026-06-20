/* cast-comment-html — annotation layer.
 * Select text -> quoted comment + nearest-heading section_hint + body. Tray, inline highlight,
 * re-anchor by verbatim quote on reload (mirrors cast-refine-requirements). Submit -> POST to the
 * local server (writes the output file); falls back to download when opened over file://.
 * All UI is built here; the server only injects this script + the CSS + a window.__CCH__ config. */
(function () {
  var CFG = window.__CCH__ || {};
  var KEY = 'cch::' + (CFG.file || location.pathname);
  var root = document.body;
  var ANCHOR = window.__CCH_anchor__ || {
    chooseOccurrence: function (t, q) { return q ? t.indexOf(q) : -1; },
    uniqueContext: function (t, s, n) { return { prefix: t.slice(Math.max(0, s - 48), s), suffix: t.slice(s + n, s + n + 48), ordinal: 0 }; }
  };
  var DISP = 40; // chars of context shown in the tray / MD (the full unique context is stored in JSON)
  var comments = [];
  try { comments = JSON.parse(localStorage.getItem(KEY) || '[]'); if (!Array.isArray(comments)) comments = []; } catch (e) { comments = []; }

  function el(t, c) { var e = document.createElement(t); if (c) e.className = c; return e; }
  function $all(s) { return [].slice.call(document.querySelectorAll(s)); }
  function clean(t) { return (t || '').replace(/\s+/g, ' ').trim(); }
  function esc(t) { var d = document.createElement('div'); d.textContent = t; return d.innerHTML; }
  function uid() { return 'c' + Math.random().toString(36).slice(2, 9); }
  function stamp() { var d = new Date(), p = function (n) { return (n < 10 ? '0' : '') + n; }; return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + ' ' + p(d.getHours()) + ':' + p(d.getMinutes()); }
  function inUI(node) { var e = node && node.nodeType === 1 ? node : (node && node.parentElement); return !!(e && e.closest('.cch-tray,.cch-bar,.cch-pop,.cch-toast')); }

  // ---- build UI ----
  var pop = el('div', 'cch-pop'); pop.innerHTML = '<button type="button">+ Comment</button>';
  var tray = el('aside', 'cch-tray'); tray.innerHTML = '<div class="cch-th"><span>Feedback &middot; <b class="cch-count">0</b></span><span class="cch-x" title="close">&times;</span></div><div class="cch-body"></div>';
  var bar = el('div', 'cch-bar'); bar.innerHTML = '<span class="cch-cnt"><b class="cch-count">0</b> comments</span>' +
    '<button type="button" data-a="tray">Tray</button>' +
    '<button type="button" data-a="submit" class="cch-primary">Submit</button>' +
    '<button type="button" data-a="md">Export MD</button>' +
    '<button type="button" data-a="json">Export JSON</button>' +
    '<button type="button" data-a="clear">Clear</button>';
  var toast = el('div', 'cch-toast');
  [pop, tray, bar, toast].forEach(function (n) { document.body.appendChild(n); });
  var trayBody = tray.querySelector('.cch-body');
  var popBtn = pop.querySelector('button');

  function sectionHint(node) {
    var e = node.nodeType === 1 ? node : node.parentElement; if (!e) return 'Document';
    var c = e.closest('[data-section],.spec,.opt-set,section,article');
    if (c) { var h = c.querySelector('h1,h2,h3,h4,h5,h6,.spec-n,.opt-label,[data-section-label]'); if (h && clean(h.textContent)) return clean(h.textContent).slice(0, 120); }
    var heads = $all('h1,h2,h3,h4,h5,h6,.spec-n,.opt-label'), best = 'Document';
    heads.forEach(function (h) { if (h.closest && h.closest('.cch-tray,.cch-bar,.cch-pop')) return; if (h.contains(e) || (h.compareDocumentPosition(e) & Node.DOCUMENT_POSITION_FOLLOWING)) { var t = clean(h.textContent); if (t) best = t; } });
    return best.slice(0, 120);
  }

  // ---- selection -> popover ----
  var pending = null;
  document.addEventListener('mouseup', function (e) {
    if (e.target.closest && e.target.closest('.cch-pop,.cch-tray,.cch-bar')) return;
    setTimeout(function () {
      var sel = window.getSelection();
      if (!sel || sel.isCollapsed) { hidePop(); return; }
      var raw = sel.toString(); if (clean(raw).length < 2) { hidePop(); return; }
      var a = sel.anchorNode; if (!a || !root.contains(a) || inUI(a)) { hidePop(); return; }
      var range = sel.getRangeAt(0), rect = range.getBoundingClientRect();
      var ctx = contextFor(range);
      pending = ctx
        ? { range: range.cloneRange(), quoted_text: ctx.quoted_text, section_hint: sectionHint(a), prefix: ctx.prefix, suffix: ctx.suffix, ordinal: ctx.ordinal }
        : { range: range.cloneRange(), quoted_text: raw, section_hint: sectionHint(a), prefix: '', suffix: '', ordinal: 0 };
      pop.style.left = (rect.left + window.scrollX) + 'px';
      pop.style.top = (rect.top + window.scrollY - 34) + 'px';
      pop.classList.add('cch-show');
    }, 1);
  });
  function hidePop() { pop.classList.remove('cch-show'); }
  popBtn.onclick = function () { if (!pending) return; openTray(); showNewForm(pending); hidePop(); };
  document.addEventListener('mousedown', function (e) { if (!e.target.closest('.cch-pop')) hidePop(); });

  // ---- text map (shared by context capture + re-anchor) ----
  function txtFilter(n) { if (!n.nodeValue) return NodeFilter.FILTER_REJECT; var p = n.parentElement; if (!p || p.closest('.cch-tray,.cch-bar,.cch-pop,.cch-toast') || p.closest('mark.cch-hl')) return NodeFilter.FILTER_REJECT; var s = p.nodeName; if (s === 'SCRIPT' || s === 'STYLE') return NodeFilter.FILTER_REJECT; return NodeFilter.FILTER_ACCEPT; }
  function buildMap() {
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, { acceptNode: txtFilter });
    var map = [], text = '', n; while (n = walker.nextNode()) { map.push({ node: n, start: text.length }); text += n.nodeValue; }
    return { map: map, text: text };
  }
  function absOffset(map, node, offset) { for (var i = 0; i < map.length; i++) { if (map[i].node === node) return map[i].start + offset; } return -1; }
  // Capture a unique anchor for a selection: the quote (taken from the search text so re-anchor can
  // always find it), enough surrounding context to be unique in the doc, plus the occurrence ordinal.
  function contextFor(range) {
    var b = buildMap(), s = absOffset(b.map, range.startContainer, range.startOffset), e = absOffset(b.map, range.endContainer, range.endOffset);
    if (s < 0 || e < 0 || e <= s) return null;
    var uc = ANCHOR.uniqueContext(b.text, s, e - s, { buffer: 16, max: 400 });
    return { quoted_text: b.text.slice(s, e), prefix: uc.prefix, suffix: uc.suffix, ordinal: uc.ordinal };
  }

  // ---- highlight wrap + re-anchor ----
  // Wrap a selection without restructuring the document: highlight EACH intersected text node's
  // segment in its own <mark>, never the whole multi-element range. The old code wrapped the range
  // wholesale and, when the selection crossed an element boundary (surroundContents throws there),
  // fell back to extractContents()+insertNode() — which re-parents block-level content inside one
  // inline <mark>, collapsing the layout. Per-text-node wrapping always succeeds (each sub-range
  // sits inside a single text node) and leaves block structure untouched. One comment id may now
  // map to several <mark>s; unwrap/resolve/scroll iterate all of them.
  function wrapRange(range, id) {
    if (range.collapsed) return false;
    var sc = range.startContainer, so = range.startOffset, ec = range.endContainer, eo = range.endOffset;
    var rootEl = range.commonAncestorContainer;
    if (rootEl.nodeType !== 1) rootEl = rootEl.parentNode;
    if (!rootEl) return false;
    var walker = document.createTreeWalker(rootEl, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        if (txtFilter(n) !== NodeFilter.FILTER_ACCEPT) return NodeFilter.FILTER_REJECT;
        return range.intersectsNode(n) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      }
    });
    var nodes = [], n; while (n = walker.nextNode()) nodes.push(n);
    var wrapped = false;
    nodes.forEach(function (tn) {
      var start = (tn === sc) ? so : 0;
      var endOff = (tn === ec) ? eo : tn.nodeValue.length;
      if (endOff <= start) return;
      // Skip whitespace-only segments. Inter-element whitespace (e.g. the gap between two grid/flex
      // items) is its own text node; wrapping it in a <mark> turns that whitespace into a real
      // element — a stray grid/flex/flow child that breaks the container's layout. It carries
      // nothing visible to highlight, so there is no reason to wrap it.
      if (!/\S/.test(tn.nodeValue.slice(start, endOff))) return;
      var r = document.createRange();
      try { r.setStart(tn, start); r.setEnd(tn, endOff); } catch (e) { return; }
      var m = el('mark', 'cch-hl'); m.dataset.cid = id;
      try { r.surroundContents(m); } catch (e) { return; }
      m.addEventListener('click', function () { openTray(); focusComment(id); });
      wrapped = true;
    });
    return wrapped;
  }
  // Re-anchor a comment to the occurrence whose surrounding context matches (ordinal breaks ties).
  function findAndWrap(c) {
    var b = buildMap(), quote = c.quoted_text;
    var idx = ANCHOR.chooseOccurrence(b.text, quote, c.prefix || '', c.suffix || '', c.ordinal);
    if (idx < 0) return false;
    var end = idx + quote.length;
    function locate(pos) { for (var i = 0; i < b.map.length; i++) { var s = b.map[i].start, e = s + b.map[i].node.nodeValue.length; if (pos >= s && pos <= e) return { node: b.map[i].node, offset: pos - s }; } return null; }
    var A = locate(idx), B = locate(end); if (!A || !B) return false;
    var r = document.createRange(); try { r.setStart(A.node, A.offset); r.setEnd(B.node, B.offset); } catch (e) { return false; }
    return wrapRange(r, c.id);
  }
  // Display helpers: the stored context can be long (grown to uniqueness), so show only the DISP
  // chars nearest the quote — enough for a reader to place it, full context stays in the JSON.
  function dispPre(s) { s = clean(s || ''); return s.length > DISP ? s.slice(-DISP) : s; }
  function dispSuf(s) { s = clean(s || ''); return s.length > DISP ? s.slice(0, DISP) : s; }
  // Render a context line: …prefix⟪quote⟫suffix… so a reader sees exactly which spot was commented on.
  function ctxText(c) {
    var pre = dispPre(c.prefix), suf = dispSuf(c.suffix), q = clean(c.quoted_text || '');
    return (pre ? '…' + pre : '') + '⟪' + q + '⟫' + (suf ? suf + '…' : '');
  }
  function ctxHTML(c) {
    var pre = esc(dispPre(c.prefix)), suf = esc(dispSuf(c.suffix)), q = esc(clean(c.quoted_text || ''));
    return (pre ? '…' + pre : '') + '<mark class="cch-qmark">' + q + '</mark>' + (suf ? suf + '…' : '');
  }

  // ---- tray ----
  function openTray() { tray.classList.add('cch-open'); }
  function closeTray() { tray.classList.remove('cch-open'); }
  tray.querySelector('.cch-x').onclick = closeTray;

  function showNewForm(p) {
    renderTray();
    var box = el('div', 'cch-new');
    box.innerHTML = '<div class="cch-nq"></div><textarea placeholder="your feedback…"></textarea><div class="cch-row"><button type="button" class="cch-save">Add comment</button><button type="button" class="cch-cancel">Cancel</button></div>';
    box.querySelector('.cch-nq').innerHTML = ctxHTML(p) + '<span class="cch-nqsec">  ·  ' + esc(p.section_hint) + '</span>';
    trayBody.insertBefore(box, trayBody.firstChild);
    var ta = box.querySelector('textarea'); ta.focus();
    box.querySelector('.cch-save').onclick = function () { var v = ta.value.trim(); if (!v) return; var id = uid(); comments.push({ id: id, quoted_text: p.quoted_text, section_hint: p.section_hint, prefix: p.prefix || '', suffix: p.suffix || '', ordinal: p.ordinal || 0, body: v, state: 'open', ts: stamp() }); save(); if (p.range) wrapRange(p.range, id); pending = null; renderTray(); focusComment(id); };
    box.querySelector('.cch-cancel').onclick = function () { pending = null; renderTray(); };
    ta.addEventListener('keydown', function (e) { if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') box.querySelector('.cch-save').click(); });
  }

  function renderTray() {
    trayBody.innerHTML = '';
    if (!comments.length) { trayBody.innerHTML = '<div class="cch-empty">No comments yet. Select any text → “+ Comment”.</div>'; updateCount(); return; }
    var order = [], groups = {};
    comments.forEach(function (c) { if (!groups[c.section_hint]) { groups[c.section_hint] = []; order.push(c.section_hint); } groups[c.section_hint].push(c); });
    order.forEach(function (sec) {
      var h = el('div', 'cch-sec'); h.textContent = sec; trayBody.appendChild(h);
      groups[sec].forEach(function (c) {
        var displaced = c.quoted_text && !document.querySelector('mark.cch-hl[data-cid="' + c.id + '"]');
        var box = el('div', 'cch-com' + (c.state === 'resolved' ? ' cch-resolved' : '') + (displaced ? ' cch-displaced' : '')); box.dataset.cid = c.id;
        var q = c.quoted_text ? '<div class="cch-q">' + ctxHTML(c) + '</div>' : '';
        box.innerHTML = q + '<div class="cch-b"></div><div class="cch-f">' + (displaced ? '<span class="cch-dsp">displaced</span>' : '') + '<button type="button" data-act="resolve">' + (c.state === 'resolved' ? 'reopen' : 'resolve') + '</button><button type="button" data-act="del">delete</button><span class="cch-ts">' + c.ts + '</span></div>';
        box.querySelector('.cch-b').textContent = c.body;
        box.onclick = function (e) { if (e.target.dataset.act) return; scrollToComment(c.id); };
        box.querySelector('[data-act="resolve"]').onclick = function (e) { e.stopPropagation(); c.state = (c.state === 'resolved' ? 'open' : 'resolved'); $all('mark.cch-hl[data-cid="' + c.id + '"]').forEach(function (m) { m.classList.toggle('cch-resolved', c.state === 'resolved'); }); save(); renderTray(); };
        box.querySelector('[data-act="del"]').onclick = function (e) { e.stopPropagation(); unwrap(c.id); comments = comments.filter(function (x) { return x.id !== c.id; }); save(); renderTray(); };
        trayBody.appendChild(box);
      });
    });
    updateCount();
  }
  function scrollToComment(id) { var ms = $all('mark.cch-hl[data-cid="' + id + '"]'); if (ms.length) { ms[0].scrollIntoView({ behavior: 'smooth', block: 'center' }); ms.forEach(function (m) { m.classList.add('cch-flash'); }); setTimeout(function () { ms.forEach(function (m) { m.classList.remove('cch-flash'); }); }, 1200); } }
  function focusComment(id) { var box = trayBody.querySelector('.cch-com[data-cid="' + id + '"]'); if (box) box.scrollIntoView({ block: 'nearest' }); scrollToComment(id); }
  function unwrap(id) { $all('mark.cch-hl[data-cid="' + id + '"]').forEach(function (m) { var par = m.parentNode; if (!par) return; while (m.firstChild) par.insertBefore(m.firstChild, m); par.removeChild(m); par.normalize(); }); }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(comments)); } catch (e) {} updateCount(); }
  function updateCount() { $all('.cch-count').forEach(function (n) { n.textContent = comments.length; }); }

  // ---- export / submit ----
  function toMD() {
    if (!comments.length) return '# Feedback\n\n_(no comments yet)_\n';
    var lines = ['# Feedback', '', '_' + (CFG.file || location.pathname) + ' · ' + stamp() + '_', ''];
    var order = [], groups = {};
    comments.forEach(function (c) { if (!groups[c.section_hint]) { groups[c.section_hint] = []; order.push(c.section_hint); } groups[c.section_hint].push(c); });
    order.forEach(function (sec) { lines.push('## ' + sec); groups[sec].forEach(function (c) { if (c.quoted_text) lines.push('> ' + ctxText(c)); lines.push('- ' + c.body + (c.state === 'resolved' ? ' _(resolved)_' : '') + '  `' + c.ts + '`'); lines.push(''); }); });
    return lines.join('\n');
  }
  function download(name, text, type) { var b = new Blob([text], { type: type }); var a = el('a'); a.href = URL.createObjectURL(b); a.download = name; document.body.appendChild(a); a.click(); a.remove(); }
  function toast_(m) { toast.textContent = m; toast.classList.add('cch-show'); setTimeout(function () { toast.classList.remove('cch-show'); }, 1800); }

  // --- bridge transport (Diecast in-viewer commenting, exploration-pipeline-nxm sp3b) ---
  // When CFG.bridge is set, this layer runs inside a null-origin <iframe srcdoc> embedded in the
  // Diecast dual viewer. A direct fetch() to the same-door API is blocked (null origin), so Submit
  // postMessages the batch to the host (window.parent), which proxies the per-comment POSTs and
  // replies with a `cch:submitted` envelope. 1b proved this is the clean path — a direct transport
  // replacement, NOT a fetch shim. The reply round-trips per-comment results into a visible toast so
  // failures are surfaced, never silently dropped.
  function submitViaBridge() {
    if (!comments.length) { toast_('no comments to submit'); return; }
    var payload = {
      type: 'cch:submit',
      goal_slug: CFG.goal_slug || null,
      artifact_ref: CFG.artifact_ref || null,
      comments: comments
    };
    try {
      window.parent.postMessage(payload, CFG.targetOrigin || '*');
      toast_('submitting ' + comments.length + ' comment(s)…');
    } catch (e) {
      download('feedback.json', JSON.stringify(comments, null, 2), 'application/json');
      toast_('bridge unavailable — downloaded JSON');
    }
  }
  // Host → layer reply. Accept only the host frame (window.parent) and the expected envelope shape;
  // an ok=false or per-comment error becomes a visible toast and the comments stay in the local list.
  window.addEventListener('message', function (e) {
    if (e.source !== window.parent) return;
    var d = e.data;
    if (!d || d.type !== 'cch:submitted') return;
    var results = Array.isArray(d.results) ? d.results : [];
    var ok = 0, fail = 0;
    results.forEach(function (r) { if (r && r.ok) ok++; else fail++; });
    if (d.ok && fail === 0) toast_('submitted ' + ok + ' comment(s) ✓');
    else if (ok > 0) toast_('submitted ' + ok + ', ' + fail + ' failed — kept locally');
    else toast_('submit failed (' + fail + ') — kept locally');
  });

  function submit() {
    if (CFG.bridge) { submitViaBridge(); return; }
    if (!CFG.submit) { download('feedback.json', JSON.stringify(comments, null, 2), 'application/json'); toast_('no server — downloaded JSON'); return; }
    fetch(CFG.submit, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ file: CFG.file || location.pathname, out: CFG.out || null, comments: comments }) })
      .then(function (r) { return r.json().catch(function () { return { ok: r.ok }; }); })
      .then(function (j) { toast_(j && j.ok ? ('submitted → ' + (j.json || CFG.out || 'output')) : 'submit failed'); })
      .catch(function () { download('feedback.json', JSON.stringify(comments, null, 2), 'application/json'); toast_('submit failed — downloaded JSON'); });
  }

  var armed = false, armT;
  bar.addEventListener('click', function (e) {
    var a = e.target.dataset.a; if (!a) return;
    if (a === 'tray') tray.classList.toggle('cch-open');
    else if (a === 'submit') submit();
    else if (a === 'md') { download('feedback.md', toMD(), 'text/markdown'); toast_('feedback.md'); }
    else if (a === 'json') { download('feedback.json', JSON.stringify(comments, null, 2), 'application/json'); toast_('feedback.json'); }
    else if (a === 'clear') {
      var b = e.target; if (!armed) { armed = true; b.textContent = 'Sure?'; armT = setTimeout(function () { armed = false; b.textContent = 'Clear'; }, 2500); return; }
      clearTimeout(armT); armed = false; b.textContent = 'Clear'; comments.slice().forEach(function (c) { unwrap(c.id); }); comments = []; save(); renderTray();
    }
  });

  // ---- init: re-anchor existing comments by quote + surrounding context ----
  comments.forEach(function (c) { if (c.quoted_text) findAndWrap(c); });
  renderTray();
})();
