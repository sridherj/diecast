# cast-preso-review

Deterministic CLI tool that emits a self-contained `review.html` for human
review of the presentation pipeline. **Not an LLM agent** — no reasoning,
no agent dispatch: it reads source files and renders HTML.

**Type:** `python-script` (per `agents/agent-design-guide/SKILL.md` §1).

**Scope of P1 (this iteration):**

- Edit mode for Stage 1 (narrative) and Stage 2 (WHAT docs)
- Decision mode for open questions
- `--serve` local server for export round-trip to goal dir
- Deferred to P2/P3/P4: annotate mode, assembly-mode deck review, orchestrator round-trip

## I/O contract

| Facet      | Value |
|------------|-------|
| **Input**  | Positional `goal_slug`; optional `--stage=narrative\|what\|decisions`, `--source-dir PATH`, `--output-dir PATH` (default: `<goal_dir>/presentation/`), `--serve`, `--port N`, `--no-open` |
| **Output** | `<output_dir>/review.html` (self-contained — all CSS/JS inlined); `runs/latest.md` (invocation summary); with `--serve`: feedback/decision POSTs land under `<goal_dir>/presentation/{feedback,decisions}/` |
| **Config** | `config.json` alongside the script (empty object by default) |

## CLI usage

```bash
uv run python agents/cast-preso-review/build.py <goal_slug>
uv run python agents/cast-preso-review/build.py <goal_slug> --stage=what
uv run python agents/cast-preso-review/build.py <goal_slug> --source-dir path/to/dir
uv run python agents/cast-preso-review/build.py <goal_slug> --output-dir path/to/output

# Build and serve — Export button POSTs back into the goal dir instead of
# falling through to a browser download.
uv run python agents/cast-preso-review/build.py <goal_slug> --serve
uv run python agents/cast-preso-review/build.py <goal_slug> --serve --port 8765
uv run python agents/cast-preso-review/build.py <goal_slug> --serve --no-open
```

### `--serve` flags

| Flag         | Default | Purpose |
|--------------|---------|---------|
| `--serve`    | off     | After building, start a loopback-only stdlib `http.server` and block until Ctrl-C. |
| `--port N`   | `0`     | TCP port to bind. `0` = OS-picked ephemeral port; printed at startup. |
| `--no-open`  | off     | Skip auto-opening the browser when `--serve` is on. |

Server posture: binds `127.0.0.1` only; rejects non-localhost `Host` headers
with 403 (DNS-rebinding defense); no auth. Intentional — this is local-only
tooling, never a daemon, never off-host.

### Server endpoints

| Method + path          | Writes to                                                       |
|------------------------|-----------------------------------------------------------------|
| `GET /`                | Serves `review.html` from `<output_dir>/`                       |
| `POST /feedback`       | `<goal_dir>/presentation/feedback/<stage>-<ISO8601>Z.md`        |
| `POST /decisions/<id>` | `<goal_dir>/presentation/decisions/<id>.answer.md` (`id` matches `[A-Za-z0-9\-_.]{1,64}`) |

The client (`review.js`) capability-probes `window.location.protocol`. On
`http://` it POSTs directly and shows a toast on success. On `file://` it
falls back to the 1a download path — same behavior you'd see if the server
happened to be down.

## Mode detection

The tool resolves `goal_slug` to `cast/goals/<slug>/` (relative to the repo
root) and walks the directory for mode markers:

| Marker                                | Mode key     | Stage                  |
|---------------------------------------|--------------|------------------------|
| `narrative.collab.md` present         | `narrative`  | Stage 1 (narrative)    |
| `what/` directory present             | `what`       | Stage 2 (WHAT docs)    |
| `decisions/` directory present        | `decisions`  | Decision slides        |

Pass `--stage=<name>` to force a specific renderer. Pass `--source-dir` to
point at an arbitrary directory instead of resolving through `goal_slug`.

**1a note:** no renderers are registered yet, so every invocation currently
exits with a clear "no renderable content" message. Sub-phase 1b registers
`narrative` and `what`; 1c registers `decisions`.

## Storage key format (client-side)

Edits are persisted in `localStorage` under:

```
{stage}-{goal_slug}-{source_hash}/{slide_id}/{block_id}
```

`source_hash` is a SHA1 prefix (10 hex chars) of the concatenated source files,
embedded in the generated HTML at build time. When the sources change, the
hash changes, the key changes, and old edits stay under the old key — which is
how Q-04 stale-edit detection works even at P1.

## Files in this directory

```
cast-preso-review/
├── README.md           — this file
├── __init__.py
├── build.py            — CLI entry point, mode dispatch, template inlining
├── template.html       — HTML shell with {{CSS}}/{{JS}}/{{SLIDES_JSON}}/{{SIDEBAR_JSON}}/{{META}} markers
├── static/
│   ├── review.css      — shared shell styles (Cast palette)
│   └── review.js       — shared shell runtime (window.TPR)
├── renderers/          — populated by 1b/1c
├── runs/               — per-invocation summaries (latest.md)
├── config.json         — future palette/storage overrides (empty {} for now)
└── tests/
    ├── conftest.py     — shared fixtures (tmp_goal_dir, copy_fixture)
    ├── fixtures/       — populated by 1b/1c
    └── test-cases.md   — manual browser-level scenarios
```

## Invocation conventions

- Run from repo root `$(readlink -f ~/.claude/skills/diecast)`.
- The tool resolves `goal_slug` under `cast/goals/` relative to the repo root,
  discovered via `REPO_ROOT = Path(__file__).resolve().parents[2]` in `build.py`.
- The slash wrapper `.claude/commands/cast-preso-review.md` (wired in 1d)
  will shell out to this script — no DB run record, no LLM dispatch.

## Non-goals

- Not a daemon; `--serve` (1d) is a foreground `http.server`, Ctrl-C stops.
- No authentication on the server — localhost-only, DNS-rebinding defense.
- No slide rendering engine — renders plain HTML blocks, not reveal.js decks.
- No authoring, no multi-user, no persistence server-side beyond feedback files.
