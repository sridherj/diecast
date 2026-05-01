# Cast Subagent and Skill Capture — raw idea

## What I want

Hooks that detect `cast-*` subagent invocations and skill invocations and
capture them in `agent_runs` with proper parent attribution. Skills used
by an agent should be a list on the agent run row (DB change likely
needed). The runs UI should surface skill usage at L2 or L3 detail in a
clean way. Specs may need updates.

## Why

Today a row in `agent_runs` only exists when an agent dispatches another
agent over the cast-server HTTP API (`POST /api/agents/{name}/trigger`)
or via `invoke_agent()`. When the harness uses Claude Code's `Task()`
tool to spawn a `cast-*` subagent directly, no row is created — the
subagent runs in its own session, and any HTTP triggers it makes show up
as orphaned roots in the runs tree.

Sibling work in flight covers two adjacent gaps but not this one:

- `docs/plan/2026-05-01-capture-user-invocations-as-runs.collab.md` —
  captures user-typed `/cast-*` slash commands as roots.
- `docs/plan/2026-05-01-cast-runs-threaded-tree.collab.md` — renders the
  threaded tree assuming the rows exist.

This goal closes the third leg: capture `Task()`-dispatched subagents
and the skills they invoke.

## Verified design constraints (from claude-code-guide)

- `SubagentStart` hook payload includes BOTH `session_id` (child's) and
  `parent_session_id` (explicit parent reference), plus `transcript_path`,
  `agent_type`, `prompt`. Real parent attribution is possible without
  marker-file games.
- `CLAUDE_SESSION_ID` env var is unreliable in hook subprocesses; trust
  the stdin JSON only.
- Skill invocations fire `PreToolUse` with `tool_name = "Skill"` and
  `tool_input = {skill_name, arguments}`. Deterministic capture.

## Out of scope (decided)

- User-typed `/cast-*` slash-command capture (covered by sibling plan).
- Bash invocations of `cast-*` CLI binaries (`bin/cast-foo` shelled out
  by an agent) — rare and likely a contract violation; address by
  enforcing HTTP path, not by capturing.
- Tracking non-`cast-*` subagents (Explore, Plan, general-purpose, etc.)
  even though their `SubagentStart` events fire too. Server-side filter.

## Open questions for refinement

- New `claude_session_id` column vs reuse existing `session_id` field.
- Skills as JSON column vs separate `agent_run_skills` table.
- Behavior when a `cast-*` subagent's parent is a non-`cast-*` subagent
  (parent unknown to cast-server): orphan row, or attach to nearest
  cast-ancestor via `parent_session_id` chain walk?
- Skill arguments: store full args, or skill name + count only? Privacy
  vs forensic value tradeoff.
- Display granularity: L2 chip-list vs L3 detailed list with timestamps.
