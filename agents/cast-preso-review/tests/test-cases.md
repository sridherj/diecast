# Manual Test Cases: cast-preso-review

Filled in as sub-phases land. 1a provides the outline; 1b/1c/1d add specifics.

## 1. Build against Stage 1 narrative (1b)

_TBD — 1b fills in steps and expected output._

## 2. Build against Stage 2 WHAT dir (1b)

_TBD — 1b fills in steps and expected output._

## 3. Build against a decisions dir (1c)

Pre-req: run `uv run python agents/cast-preso-review/build.py fixture
--source-dir agents/cast-preso-review/tests/fixtures/decisions --stage=decisions`.
Open the generated `review.html` in a browser.

- Sidebar shows **3 rows** (Q-01, Q-02, Q-03) with no group label (decision-
  mode was the primary renderer, so no "Open questions" header).
- Picking the first entry renders a decision card: monospace `Q-01` chip, a
  stage chip, topic heading, context paragraph with backticked paths rendered
  as monospace, a vertical list of options, and a **"Notes / caveat"**
  textarea below.
- The recommended option has an accent border + "Recommended" pill in the
  top-right. Alternatives have no border accent.
- Click the recommended option → radio fills, card gets the `picked`
  highlight, footer flips `saving… → saved`.
- Type "maybe" into the notes textarea → footer flips through `saving… →
  saved` after the 200ms debounce.
- Reload the page → the radio selection **and** the note persist; the
  sidebar row shows the edited-dot marker.
- Click **Export** → a markdown file downloads with sections like
  `## Decision: Hosting for the review surface (Q-01)` containing
  `**Picked:** A — Pure static file per goal`, the `**Note:** maybe` line,
  and an `### Original options` list with all three options and their
  rationales (trimmed to 180 chars).
- Mixed-mode check: run build with
  `--source-dir tests/fixtures/narrative/` after copying
  `tests/fixtures/decisions` into that dir as a `decisions/` child. The
  sidebar now has **two groups**: the narrative slides (no label) and
  "Open questions" with Q-01–Q-03 underneath.
- Malformed check: run with
  `--source-dir tests/fixtures/decisions-malformed --stage=decisions`.
  Each affected slide shows a **"Build warnings"** collapsible above the
  context block; stderr shows `[WARN decision Q-04] ...`, `[WARN decision
  Q-05] ...`, `[WARN decision Q-06] ...`.

## 4. Keyboard navigation (1a)

Open a generated `review.html` in a browser.

- `ArrowRight` advances one slide; header counter updates; sidebar active row moves.
- `ArrowLeft` goes back one; stops at slide 1.
- `Escape` blurs a focused editable block.
- `/` focuses the sidebar search input.

## 5. Sidebar search filter (1a)

- Type a substring of a slide title → only matching rows remain visible.
- Clear the field → every row re-appears.

## 6. Autosave round-trip (1a)

- Edit any `[contenteditable]` block; footer state flips `saved → saving… → saved`.
- Reload the page → the edit persists, the block shows the `edited` highlight,
  the sidebar row shows the edited-dot.
- `localStorage` contains a key matching `{stage}-{goal_slug}-{source_hash}/{slide_id}/{block_id}`.

## 7. Revert-slide / clear-all (1a)

- Make edits on two slides. Click **Revert slide** on slide A → only slide A reverts;
  slide B's edits persist and its sidebar dot stays.
- Click **Clear all** → confirm dialog; accepting wipes every edit and every dot.

## 8. Export — download fallback (1a)

- Make at least one edit, click **Export** → a markdown file downloads with
  filename `review-<stage>-<ISO>.md`.
- File body has the "# Review feedback" header plus a "## Slide:" section per
  edited slide and a **Before / After** pair per edited block.

## 9. Export — server POST round-trip (1d)

Pre-req: run `uv run python agents/cast-preso-review/build.py fixture
--source-dir agents/cast-preso-review/tests/fixtures/narrative --serve
--no-open`. Note the `http://127.0.0.1:<PORT>/` URL printed to stdout.

- Open `http://127.0.0.1:<PORT>/` in a browser (**not** the `file://` path).
- Edit at least one `[contenteditable]` block; the footer flips
  `saved → saving… → saved` (same as case 6).
- Click **Export** → a toast appears in the bottom-right reading
  `Saved → <goal_dir>/presentation/feedback/narrative-<TIMESTAMP>Z.md`.
  **No browser download** fires in this mode.
- `ls <goal_dir>/presentation/feedback/` shows the new `narrative-*Z.md`
  file; `cat` it and confirm the "# Review feedback — narrative — ..."
  markdown body with the edit preserved.
- Repeat against a decisions-mode build (`--stage=decisions`). Pick a radio
  and type into the notes textarea. Within `SAVE_DEBOUNCE_MS` (~200 ms)
  after each change a file lands at
  `<goal_dir>/presentation/decisions/Q-XX.answer.md` whose body starts with
  `## Decision:` and contains `**Picked:** A — ...`.
- Kill the server with Ctrl-C; reopen the same `review.html` via `file://`
  and click Export → the download fallback kicks back in (no toast).

## 10. Server rejects bad Host header (1d)

Pre-req: server running from case 9 with `PORT` captured.

- `curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:$PORT/`
  prints `200`.
- `curl -s -o /dev/null -w "%{http_code}\n" -H "Host: evil.example.com" \
  http://127.0.0.1:$PORT/` prints `403`.
- `curl -s -o /dev/null -w "%{http_code}\n" -H "Host: localhost" \
  http://127.0.0.1:$PORT/` prints `200` (localhost is on the allow-list).
- `curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  -H "Host: evil.example.com" --data "x" http://127.0.0.1:$PORT/feedback`
  prints `403` (POST is also gated). No file lands in the goal dir.

This is the DNS-rebinding defense. Without it, a page the reviewer visits
elsewhere in the browser could script the local server because the TCP
origin is `127.0.0.1` but the `Host` header would say the rebound domain.

## 11. Idempotent build (byte-identical output) (1d)

Pre-req: an untouched narrative fixture goal dir.

- Run the build twice in a row against the same source:

  ```bash
  for _ in 1 2; do
    uv run python agents/cast-preso-review/build.py fixture \
      --source-dir agents/cast-preso-review/tests/fixtures/narrative
  done
  ```

- `sha1sum <goal_dir>/presentation/review.html` matches between the two
  runs. `diff <run1_copy> review.html` shows zero bytes differ.
- Why this matters: feedback collected off a noisy baseline is noisy
  feedback. If two runs produced different bytes, reviewers couldn't
  tell which changes were theirs vs. the tool's. Idempotency is the
  prerequisite for treating `review.html` diffs as signal.
- Negative check: mutate the source (`echo ' ' >>
  <goal_dir>/narrative.collab.md`) and rebuild → the sha1 changes and the
  `storage_key_prefix` hash embedded in the HTML changes with it, which is
  how client-side stale-edit detection works.
