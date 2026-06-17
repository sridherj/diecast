/* cast-comment-html — pure anchoring helpers (no DOM).
 * Shared by the browser layer (comment-layer.js) and the node test (tests/test_anchor.js).
 *
 * The job: when the quoted snippet repeats in the document, anchor a comment to the exact
 * occurrence the reviewer selected. This is a W3C-style anchor pairing two selectors:
 *   1. TextQuoteSelector — quote + surrounding prefix/suffix context (robust to edits).
 *   2. TextPositionSelector — the occurrence ordinal (the deterministic fallback when no
 *      finite context can disambiguate, e.g. two byte-identical paragraphs).
 *
 * Capture (uniqueContext) GROWS the context until prefix+quote+suffix is unique across the
 * document, then adds a buffer — it does not bound context to a fixed guess. Re-anchor
 * (chooseOccurrence) scores by context and breaks ties with the ordinal. */
(function (root) {
  // Number of chars matching from the START of both strings.
  function commonPrefixLen(a, b) {
    var n = Math.min(a.length, b.length), i = 0;
    while (i < n && a.charCodeAt(i) === b.charCodeAt(i)) i++;
    return i;
  }
  // Number of chars matching from the END of both strings.
  function commonSuffixLen(a, b) {
    var n = Math.min(a.length, b.length), i = 0;
    while (i < n && a.charCodeAt(a.length - 1 - i) === b.charCodeAt(b.length - 1 - i)) i++;
    return i;
  }
  // All start indices of `quote` in `text`.
  function occurrences(text, quote) {
    var out = [], from = 0, i;
    if (!quote) return out;
    while ((i = text.indexOf(quote, from)) !== -1) { out.push(i); from = i + 1; }
    return out;
  }

  // Capture just enough context that prefix+quote+suffix is UNIQUE in `text`, then add a buffer.
  // Returns {prefix, suffix, ordinal}. `ordinal` is the 0-based occurrence index of the target —
  // the fallback used when even `max` chars of context cannot disambiguate (truly identical text).
  function uniqueContext(text, start, quoteLen, opts) {
    opts = opts || {};
    var buffer = opts.buffer == null ? 16 : opts.buffer;   // extra context beyond the unique boundary
    var max = opts.max == null ? 400 : opts.max;           // cap so a pathological doc can't blow up the anchor
    var step = opts.step == null ? 8 : opts.step;
    var end = start + quoteLen;
    var quote = text.slice(start, end);
    var occ = occurrences(text, quote);
    var ordinal = occ.indexOf(start);
    if (ordinal < 0) ordinal = 0;

    // Grow a symmetric window until the surrounding context isolates a single occurrence.
    var need = 0;
    if (occ.length > 1) {
      while (need < max) {
        var pre = text.slice(Math.max(0, start - need), start);
        var suf = text.slice(end, end + need);
        var matches = 0;
        for (var k = 0; k < occ.length; k++) {
          var p = occ[k];
          var cpre = text.slice(Math.max(0, p - pre.length), p);
          var csuf = text.slice(p + quoteLen, p + quoteLen + suf.length);
          if (cpre === pre && csuf === suf) matches++;
          if (matches > 1) break;
        }
        if (matches <= 1) break;
        need += step;
      }
    }
    var span = Math.min(max, need + buffer);
    return {
      prefix: text.slice(Math.max(0, start - span), start),
      suffix: text.slice(end, end + span),
      ordinal: ordinal
    };
  }

  // Return the start index in `text` of the occurrence of `quote` that best matches the captured
  // context, breaking ties with `ordinal`. Falls back to the first occurrence when there is no
  // context and no ordinal. Returns -1 when `quote` is absent.
  function chooseOccurrence(text, quote, prefix, suffix, ordinal) {
    if (!quote) return -1;
    var occ = occurrences(text, quote);
    if (occ.length === 0) return -1;
    if (occ.length === 1) return occ[0];

    var maxScore = -1, scored = [];
    for (var i = 0; i < occ.length; i++) {
      var pos = occ[i], score = 0;
      if (prefix) score += commonSuffixLen(text.slice(Math.max(0, pos - prefix.length), pos), prefix);
      if (suffix) { var e = pos + quote.length; score += commonPrefixLen(text.slice(e, e + suffix.length), suffix); }
      scored.push({ pos: pos, idx: i, score: score });
      if (score > maxScore) maxScore = score;
    }
    var top = scored.filter(function (s) { return s.score === maxScore; });
    if (top.length === 1) return top[0].pos;

    // Context tie → fall back to the ordinal (TextPositionSelector).
    if (ordinal != null && ordinal >= 0 && ordinal < occ.length) {
      for (var t = 0; t < top.length; t++) if (top[t].idx === ordinal) return top[t].pos;
      return occ[ordinal];
    }
    return top[0].pos;
  }

  var api = {
    commonPrefixLen: commonPrefixLen,
    commonSuffixLen: commonSuffixLen,
    occurrences: occurrences,
    uniqueContext: uniqueContext,
    chooseOccurrence: chooseOccurrence,
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;   // node test
  root.__CCH_anchor__ = api;                                                    // browser
})(typeof self !== "undefined" ? self : this);
