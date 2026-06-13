# Plan: Prototype live Claude-session streaming in the Diecast UI

> Recovered from Claude session `0f2e118b-eaf4-45b8-82f2-a8fdda566fe9` (ExitPlanMode @ 2026-06-12T04:23Z).
> The throwaway prototype was built and demonstrated (all three tiers) before logoff; code backed up to
> `~/cast-stream-proto/` (originally `/tmp/cast-stream-proto/`). Resume the session to continue:
> `cd /data/workspace/diecast && claude --resume 0f2e118b-eaf4-45b8-82f2-a8fdda566fe9`

## Context

Today the Diecast UI surfaces agent runs by **HTMX polling** (`hx-trigger="every 5s"`) of
DB-backed status + the final `.agent-<run_id>.output.json`. There is **no SSE, no WebSocket, no
StreamingResponse** anywhere. The user wants to *watch live Claude sessions in the browser*, and —
crucially — many sessions are **interactive** (they ask the human questions via `AskUserQuestion`
arrow-key menus, permission prompts, etc.), so a read-only stream is not enough; a **type-back**
channel is also needed.

Goal of THIS plan: stand up **throwaway prototypes** of the two cheapest fidelity tiers (A and B)
against a **real live tmux session**, so the user can feel the difference hands-on before committing
to a production architecture. Nothing here is wired into cast-server; it's a playground.

### What already exists (reuse, don't rebuild)
- **Live transcript source:** every run writes `~/.claude/projects/<project>/<session_id>.jsonl`.
  cast-server already resolves it (`_find_claude_session_id`, `_resolve_jsonl_dir`,
  `_resolve_jsonl_file` in `cast-server/cast_server/services/agent_service.py`).
- **Type-back channel:** `continue_agent_run(run_id, message)` (`agent_service.py:2095`, exposed at
  `POST /api/agents/runs/{run_id}/continue`) writes a `.continue` file and `tmux send-keys` + Enter
  into the live `agent-<run_id>` session. Same mechanism used manually to notify agents.
- **Live sessions:** agents run as interactive `claude` REPLs inside tmux sessions named
  `agent-<run_id>` (e.g. `agent-run_20260612_035244_794efa` was live).

### Fidelity tiers (the real decision this prototype informs)
- **A — message-level (SSE down + existing POST up):** fits FastAPI+HTMX, no WebSocket; low fidelity
  for TUI menus/permission prompts.
- **B — terminal-grade (xterm.js/ttyd over the tmux PTY):** full TUI fidelity, minimal code, reuses
  existing tmux sessions; WebSocket under the hood; raw-terminal look.
- **C — headless stream-json (`claude -p --input/--output-format stream-json`):** best data+fidelity,
  but re-architects how every agent is launched. Out of scope for the prototype (peek only).

### How peers do it (informs the eventual choice)
- **Conductor:** embedded per-workspace terminal + chat + diff  → essentially productized **B**.
- **Devin:** real-time terminal/editor/browser, <50ms, replay timeline → high-fidelity embedded.
- **OpenHands:** FastAPI + **WebSocket** event streaming + embedded VSCode/VNC → **C** + terminals.
- **Factory droid:** synced surfaces driven by **stream-json/stream-jsonrpc** → **C**.
- Takeaway: serious harnesses use embedded-terminal (B) and/or structured event-stream over WS (C);
  they explicitly avoid the polling model cast-server uses today. Transcript-only (A) is a stepping
  stone, not an endpoint.

## Prototype plan (throwaway — `/tmp/cast-stream-proto/`, not in the repo)

### Tier B prototype — ttyd web terminal (~5 min, zero app code) — DO THIS FIRST
1. Install ttyd (`apt-get install ttyd` or `brew install ttyd`; or download the static binary).
2. Pick a live session: `tmux ls | grep agent-` → choose a running one (or
   `tmux new -s agent-demo 'claude'` for a throwaway interactive session).
3. Run writable (interactive) terminal-over-web:
   `ttyd -W -p 7681 tmux attach -t <session-name>`
   - `-W` = writable (lets you type back, drive arrow-key menus, answer AskUserQuestion).
4. Open `http://localhost:7681` → you now have the full TUI in the browser; interact with it.
5. "Embedded in app" feel: drop `<iframe src="http://localhost:7681" style="width:100%;height:80vh">`
   into a one-off HTML file and open it. This is the Conductor/Devin experience.
   - Observe: full fidelity (colors, menus, prompts), but it's a raw terminal, and ttyd is one
     process per port → for N sessions you'd multiplex (base-path routing) or spawn per-run.

### Tier A prototype — SSE transcript tail + send box (~30–60 min, small code)
Single throwaway FastAPI app `proto.py` (separate venv or the repo `.venv`), ~80 lines:
1. `GET /stream/{run_id}` → `StreamingResponse(media_type="text/event-stream")` that:
   - resolves the JSONL via the same logic as agent_service (project-dir name-mangling +
     symlink-resolution — see `agent_service.py:82` comment "Claude Code resolves symlinks when
     naming project dirs, so we must too"); for the prototype, hardcode/glob
     `~/.claude/projects/*/<session>.jsonl` by newest mtime for the run's working dir.
   - async `tail -f`: seek to end (or replay last N lines), then poll for new lines, `yield
     f"data: {json.dumps(parsed_event)}\n\n"`. Emit a final event + close when the run completes.
2. `GET /` → one HTML page: `new EventSource('/stream/<run_id>')`, append rendered events
   (assistant text, `tool_use`, `tool_result`) to a `<div>`; plus a text input that
   `fetch('/send/<run_id>', {method:'POST', body})`.
3. `POST /send/{run_id}` → for the prototype, shell out to `tmux send-keys -t agent-<run_id> -l <msg>`
   then `Enter` (mirrors what `continue_agent_run` does), so you can feel type-back latency/UX.
   - Observe: clean rendered transcript, but the AskUserQuestion arrow-menu does NOT render as a
     clickable widget — you reply with free text. This is the fidelity gap, made tangible.

### Tier C peek (optional, no UI) — see the data you'd build on
Run one throwaway agent headless and watch the structured stream:
`claude -p "say hi then list files" --output-format stream-json --include-partial-messages | jq -c .`
Confirms the event shape (and `--input-format stream-json` + `--replay-user-messages` for bidi) that
a native structured UI would consume — to judge whether C is worth the re-architecture later.

## Files (all throwaway, outside the repo)
- `/tmp/cast-stream-proto/proto.py` — tiny FastAPI SSE+send app (Tier A). **Backed up to `~/cast-stream-proto/proto.py`.**
- `/tmp/cast-stream-proto/index.html` — EventSource client (Tier A) and/or ttyd iframe (Tier B).
  (In practice `proto.py` serves its own HTML at `GET /`, so no separate file was needed.)
- No cast-server files touched. If a tier is chosen later, a separate production plan will wire it in
  (reusing the JSONL resolvers and `/continue` endpoint above).

## Verification
1. **B:** browser at `:7681` mirrors the live tmux pane; typing in the browser drives the agent
   (answer an `AskUserQuestion` menu with arrow keys + Enter from the browser). Full fidelity ✓.
2. **A:** browser shows the transcript updating live as the agent works; the send box delivers a
   message that appears in the session and the response streams back. Note where TUI widgets fail to
   render. ✓ proves SSE pipe + type-back, exposes the fidelity gap.
3. **Decision:** with both in front of you, pick the production tier (B for fastest full-fidelity,
   A as a light add-on, or commit to C). A follow-up plan implements the chosen tier inside
   cast-server.

## Sources
- ttyd: https://github.com/tsl0922/ttyd/blob/main/man/ttyd.man.md
- xterm.js: https://github.com/xtermjs/xterm.js/
- Claude Code headless / stream-json: https://code.claude.com/docs/en/headless
- Conductor: https://www.conductor.build/docs/guides/parallel-agents/run-multiple-claude-code-sessions
- Devin session tools: https://docs.devin.ai/work-with-devin/devin-session-tools
- OpenHands SDK (FastAPI+WebSocket): https://docs.openhands.dev/sdk/guides/agent-server/local-server
- Factory droid architecture: https://deepwiki.com/factory-ai/factory/3.1-droid-agent-architecture
