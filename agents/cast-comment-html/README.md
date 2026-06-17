# cast-comment-html

Annotate any standalone HTML file with feedback. Launches a local server with an injected
annotation layer, waits for the user to submit, then reads and presents the feedback.

## Type

cast-agent (interactive)

## I/O Contract

- **Input:** Path to an HTML file (required). Optional: `--out <feedback.json>`, `--port <N>` (default 8077).
- **Output:**
  - `<input>.feedback.json` — array of `{id, quoted_text, section_hint, prefix, suffix, ordinal, body, state, ts}`
  - `<input>.feedback.md` — same, grouped by section, human-readable, each anchor rendered as a
    truncated `…prefix⟪quoted⟫suffix…` so repeated text is unambiguous
  - `prefix`/`suffix`/`ordinal` are additive (the `cast-refine-requirements` shape is a subset).
    `prefix`/`suffix` are grown until `prefix+quote+suffix` is unique in the document (not a fixed
    window); `ordinal` is the occurrence-index fallback for genuinely identical blocks. Together
    they re-anchor a comment to the exact spot it was placed, even when the snippet repeats.
  - Inline summary of comments in the Claude session
- **Config:** None — all options are per-invocation flags.

## How It Works

1. Kills any existing process on the target port (prevents phantom-bind bugs).
2. Starts `tools/comment-html/comment_html.py` in the background.
3. Prints the local URL and instructs the user to annotate and click Submit.
4. Waits for the user to signal completion (say "done").
5. Reads the output `.json` and surfaces a structured summary.
6. Suggests next steps (e.g. `/cast-comment-reanchor` if this is a requirements render).

## Usage

```
/cast-comment-html docs/design/prototype/app.html
/cast-comment-html path/to/render.html --out reviews/sprint3.json --port 8099
```

## Key Files

- `cast-comment-html.md` — Agent brain (workflow, output format, quality bar)
- `config.yaml` — Model and timeout settings
- `comment_html.py` — Python server (stdlib only, no deps)
- `assets/` — Injected CSS + JS annotation layer (`cch-*` namespace)
