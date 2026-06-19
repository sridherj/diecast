# cast-comment-html — Manual Test Cases

Automated coverage: `test_anchor.js` (pure anchoring) + `test_render_md.py` (MD rendering, runs the
node suite too) + `run_layout_test.sh` (DOM wrap-layout regression in headless Chrome; skips when no
browser is installed). The scenarios below cover the browser-interactive path that pytest can't drive.

## TC0 — Highlighting must not change layout (regression: grid/flex columns)
1. Serve an HTML file whose content uses a CSS **grid** or **flex** container (e.g. a two-column card).
2. Select text that spans BOTH columns → "+ Comment" → Add comment.
3. **Expect:** both columns stay side-by-side and in their box; no column drops to a new row. The
   selection is highlighted in place. (Covered automatically by `run_layout_test.sh`: a `<mark>` must
   never be wrapped around inter-element whitespace, which would become a stray grid/flex item.)

## TC1 — Happy path: comment on unique text
1. `uv run python agents/cast-comment-html/comment_html.py <file>.html --port 8077`
2. Open the URL, select a unique sentence → "+ Comment" → type → Add comment → Submit.
3. **Expect:** `<file>.feedback.json` has one entry with `quoted_text`, `prefix`, `suffix`, `ordinal: 0`;
   `<file>.feedback.md` shows `…prefix⟪quote⟫suffix…` under the nearest heading.

## TC2 — Repeated text disambiguation (the core guarantee)
1. Serve an HTML file where the same word/phrase appears 3+ times (e.g. a table column).
2. Comment on the 2nd occurrence, then the 3rd.
3. **Expect:** both anchors are distinguishable in the MD (different prefix/suffix); reload the page
   and confirm each highlight lands on the occurrence you actually selected (not the first match).

## TC3 — Identical blocks (ordinal fallback)
1. Serve an HTML file with two byte-identical paragraphs.
2. Comment on the second paragraph's text.
3. **Expect:** JSON records `ordinal: 1`; on reload the highlight is on the second block.

## TC4 — Relative assets load
1. Serve an HTML file that references `tokens.css` / a relative `<img>` / a webfont.
2. **Expect:** the page renders styled with images visible (server serves assets from the HTML's dir).

## TC5 — file:// fallback
1. Open the *unserved* HTML directly via `file://` (no server).
2. Comment + Submit.
3. **Expect:** Submit falls back to a browser download of `feedback.json` (no server write).

## TC6 — Port already in use
1. Start the server on a port, then start a second instance on the same port.
2. **Expect:** the agent frees the port first (Step 2 kill-before-bind); no phantom bind.

## TC7 — Empty submit
1. Open, submit with zero comments.
2. **Expect:** agent reports "No comments were submitted"; MD renders the empty placeholder.
