# Spike result: live Claude-session "cockpit" in the Diecast UI

**Date:** 2026-06-12 · **Type:** spike (prototype + decision) · **Status:** decided — productionize Tier B
**Related:** [`2026-06-12-cast-stream-live-session-prototype.md`](2026-06-12-cast-stream-live-session-prototype.md) (the prototype plan this validates)
**Prototype code:** `~/cast-stream-proto/` (`proto.py` self-contained; `ttyd` at `/usr/bin/ttyd`)

---

## Question

Can we watch — and *drive* — live Claude agent sessions from the Diecast web UI? Today the UI only
**polls** DB status (`hx-trigger="every 5s"`) and shows the final `.agent-<run_id>.output.json`.
Many sessions are **interactive** (they ask the human via `AskUserQuestion` arrow-key menus,
permission prompts), so read-only is not enough — we need type-back too.

Three fidelity tiers were prototyped end-to-end against real tmux sessions:
- **A** — SSE-tail the run's JSONL transcript into a rendered panel + a "send message" box.
- **B** — point a web terminal (`ttyd` → `xterm.js`) at the run's tmux PTY. Full TUI fidelity.
- **C** — re-launch agents headless as `claude -p --output-format stream-json --input-format stream-json`
  and build a native structured UI.

## What we found

| | A (SSE transcript) | **B (ttyd terminal)** | C (stream-json) |
|---|---|---|---|
| New code | small FastAPI route + HTML | **~none (one `ttyd` invocation)** | large (UI + re-architecture) |
| Interactive fidelity | **fails** — can't drive arrow-menus/permission prompts; free-text only | **complete** — keystrokes, menus, colors, prompts all work | high, but you rebuild every widget |
| Type-back | reuses existing `/continue` send-keys | **native (writable PTY)** | structured stdin |
| New dependency | none (`StreamingResponse`) | `ttyd` binary (already installed) | none |
| Changes how agents launch? | no | **no — attaches to existing tmux** | **yes — replaces interactive REPL** |
| Look | styled, product-native | raw monospace terminal | product-native |

**Evidence from the spike:**
- B served a real `claude` session at its **trust-prompt menu**; we answered it with ↑/↓+Enter
  *from the browser* — full fidelity, zero app code (`ttyd -W -i lo -p 7690 tmux attach -t agent-demo`).
- A streamed live transcripts (incl. the running session itself) cleanly, but the same trust-prompt
  arrow-menu was **undriveable** from A — you can only send free text and hope. The fidelity gap is real.
- C's stream shows the prize for a future native UI (`stream_event` token deltas, structured
  `assistant`/`tool_use`/`result`), but requires launching agents in a wholly different mode.

## Decision

**Ship B as the cockpit.** It is the only tier that makes "watch + intervene on live interactive
sessions" real *now*, with essentially no new code, and it does **not** disturb how agents are
launched (it just attaches to the `agent-<run_id>` tmux sessions that already exist). C remains the
principled long-term path and is **not foreclosed** — structured panels can grow *around* the embedded
terminal later. A is not worth shipping (read-only-ish value, fails the interactive case).

### Constraints that collapse B's usual caveats (user-set)
- **localhost is mandatory.** ttyd binds `127.0.0.1` only. That *is* the security model — no auth, no
  TLS, nothing to build. Remote viewing is delegated to Claude remote control, out of scope here.
- **Bounded concurrency** — a hard cap (≈10) on simultaneously-*viewable* live sessions. Each viewable
  tile = one iframe = one tmux attach, so the cap is a front-end render limit, not backend resource math.
- **Cockpit is embedded** inside existing product features. ttyd owns only the terminal rectangle; the
  surrounding app keeps owning run list, diffs, artifacts, controls. (This is ttyd's designed use — iframe.)

So the earlier "scaling / fleet of daemons / auth" worries **do not apply** at this scale and posture.

## Production shape (small)

**One supervised ttyd sidecar, localhost, writable, session chosen by URL.**

1. **Sidecar supervisor** — start a single `ttyd` in the FastAPI **lifespan** (`cast-server/cast_server/app.py:147`,
   alongside the existing startup posture), bound to `127.0.0.1` on a fixed port, launched with
   `--url-arg` so the command is `tmux attach -t` and the browser selects the run via
   `?arg=agent-<run_id>`. One process serves *all* sessions. Writable (`-W`) so the cockpit can answer
   prompts / unstick agents (safe because localhost-only). Reap on shutdown.
   - One ttyd for everything (not one-per-run) — `--url-arg` is what avoids a port/process per run.
2. **Cockpit view** — a new page/panel rendering ≤N tiles, one per **live** run, where "live" =
   `status='running'` **and** `tmux.session_exists(f"agent-{run_id}")` (the exact predicate already used
   at `agent_service.py:1156`; `TmuxSessionManager` in `cast-server/cast_server/infra/tmux_manager.py`).
   Each tile = `<iframe src="http://127.0.0.1:<ttyd_port>/?arg=agent-{{ run.id }}">`. Click-to-expand.
   Reuse the live-runs query feeding the runs page (`routes/pages.py` `runs_page` / `get_runs_tree`).
3. **Empty / ended state** — when a run's tmux session is gone, the tile shows "run finished → artifacts"
   instead of a dead terminal (cheap `session_exists` check on render / poll).
4. **Embed point** — the cockpit is a fragment droppable into the existing surface; no changes to how
   agents are dispatched, no schema changes, no new Python deps (ttyd is a binary, already at
   `/usr/bin/ttyd`).

### Open decisions (small, defer to build)
- **Tile population:** auto-fill from the live-runs query vs. click-a-run-to-attach. (Lean: auto-fill up
  to the cap, click to swap.)
- **Per-viewer sizing:** plain `tmux attach` mirrors one view across viewers (smaller window clamps).
  Single-user cockpit → ignore. If ever multi-viewer-independent, attach via a grouped session
  (`tmux new-session -t <run>`) per client.
- **ttyd version pin / availability** — doctor check that `/usr/bin/ttyd` exists; degrade cockpit to the
  existing polling view if absent.

## Effort

Roughly a day: lifespan sidecar (~30 lines) + a cockpit route/template with iframe tiles + a
`session_exists`-based live filter + an empty-state + a doctor check. No deps, no schema, no dispatch
changes.

## How to re-run the prototype
```bash
# Tier B (full-fidelity terminal):
tmux new-session -d -s agent-demo -x 200 -y 50 -c /tmp/demo "env -u CLAUDECODE claude"
ttyd -W -i lo -p 7690 tmux attach -t agent-demo        # → http://localhost:7690
# Tier A (SSE transcript + send box):
cd ~/cast-stream-proto && /data/workspace/diecast/.venv/bin/python -m uvicorn proto:app --port 7691
# Leave the systemd ttyd.service on :7681 alone.
```

## Sources
- ttyd (`--url-arg`, `-W`, iframe embedding): https://github.com/tsl0922/ttyd/blob/main/man/ttyd.man.md
- xterm.js: https://github.com/xtermjs/xterm.js/
- Claude Code headless / stream-json (Tier C): https://code.claude.com/docs/en/headless
- Peer patterns: Conductor (embedded per-workspace terminal), Devin (real-time terminal/editor/browser),
  OpenHands (FastAPI + WebSocket + embedded VSCode/VNC), Factory droid (stream-json surfaces).
