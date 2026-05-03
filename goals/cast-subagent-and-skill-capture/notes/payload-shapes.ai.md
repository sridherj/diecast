# Spike A — empirical payload shapes

Captured 2026-05-01 from a live Claude Code session in `<DIECAST_ROOT>`,
agent_type=`Explore` (built-in) and via Skill tool calling `landing-report`.
Session-id values redacted to `<session_id>` / `<agent_id>` / `<tool_use_id>` for stability.

> Source of truth for sp1–sp3 implementation. Re-run by setting up
> `/tmp/log-payload.sh` + entries in `.claude/settings.local.json` for
> `SubagentStart`, `SubagentStop`, and `PreToolUse` (matchers `Skill` and `Task`).
> Note: settings.local.json is NOT re-read mid-session — restart Claude Code after
> editing it.

## Cross-checked against docs

[code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks) common
input fields list confirms (verbatim):

> **`agent_id`**: Unique identifier for the subagent. Present only when the hook
> fires inside a subagent call.
> **`agent_type`**: Agent name. Present when the session uses `--agent` or the
> hook fires inside a subagent.

The docs do **not** mention `parent_session_id`. The empirical shapes below are
authoritative for fields the docs leave unspecified.

## SubagentStart

```json
{
  "session_id":      "<parent main-loop session_id>",
  "transcript_path": "/home/<user>/.claude/projects/<dashed-cwd>/<session_id>.jsonl",
  "cwd":             "<DIECAST_ROOT>",
  "agent_id":        "<subagent's unique id, e.g. acf8973253da14ff6>",
  "agent_type":      "Explore",
  "hook_event_name": "SubagentStart"
}
```

**Notes**
- `session_id` is the **parent Claude Code session's** id, not the subagent's.
  All subagents in a session share this value.
- `agent_id` is the subagent's unique identity. Use this as the closure key in
  `SubagentStop`, not `session_id`.
- No `parent_session_id` field anywhere. Plan's original design assumption is
  invalidated.
- For nested subagents (subagent dispatches another subagent): per docs,
  `PreToolUse(Task)` fires inside the dispatching subagent's context, so it
  carries the dispatcher's `agent_id`. Empirical confirmation pending — current
  capture only covers top-level dispatch.

## SubagentStop

```json
{
  "session_id":            "<parent main-loop session_id>",
  "transcript_path":       "/home/<user>/.claude/projects/<dashed-cwd>/<session_id>.jsonl",
  "cwd":                   "<DIECAST_ROOT>",
  "permission_mode":       "bypassPermissions",
  "agent_id":              "<matches the SubagentStart agent_id>",
  "agent_type":            "Explore",
  "hook_event_name":       "SubagentStop",
  "stop_hook_active":      false,
  "agent_transcript_path": "/home/<user>/.claude/projects/<dashed-cwd>/<session_id>/subagents/agent-<agent_id>.jsonl",
  "last_assistant_message":"<final text the subagent emitted, full string>"
}
```

**Notes**
- `agent_id` matches the `SubagentStart` event one-to-one — primary closure key.
- No explicit `error`, `exit_code`, or `failed` field. v1 status flips to
  `completed` regardless; failure detection is out of scope.
- `last_assistant_message` could (in v2) be inspected for failure patterns or
  recorded as a result summary, but that is not part of this plan.
- `stop_hook_active` indicates whether a Stop hook is mid-flight; not used by
  cast-server logic.

## PreToolUse — Task (subagent dispatch)

Fired when the main loop or a subagent invokes the `Agent` / `Task` tool.

```json
{
  "session_id":      "<parent main-loop session_id>",
  "transcript_path": "/home/<user>/.claude/projects/<dashed-cwd>/<session_id>.jsonl",
  "cwd":             "<DIECAST_ROOT>",
  "permission_mode": "bypassPermissions",
  "hook_event_name": "PreToolUse",
  "tool_name":       "Agent",
  "tool_input": {
    "description":    "Spike A retry",
    "prompt":         "<verbatim prompt sent to the subagent>",
    "subagent_type":  "Explore"
  },
  "tool_use_id":     "toolu_01D7eSKkC3A2raLu34E8h4ko"
}
```

**Notes**
- `tool_name` is `"Agent"` (the Claude Code tool name), not `"Task"`. For the
  matcher in `.claude/settings.json`, use `"Task"` per docs (or test both —
  matcher value is sometimes the user-facing tool name, sometimes the internal
  one). Empirical: matcher value `"Task"` did fire this hook.
- When fired in **main-loop context**: NO `agent_id`. When fired **inside a
  subagent**: WOULD carry the dispatcher subagent's `agent_id` per docs. (Not
  yet empirically verified.)
- `tool_use_id` correlates this PreToolUse with the subsequent `SubagentStart`,
  but cast-server doesn't currently use that linkage.
- **Not currently captured by this plan's hooks.** sp2 only wires
  `SubagentStart` → server, not `PreToolUse(Task)`. If future work wants exact
  nested attribution beyond the most-recent-running heuristic, capture this
  event too and store `tool_use_id` alongside `agent_id`.

## PreToolUse — Skill

Fired when any Skill is invoked.

```json
{
  "session_id":      "<parent main-loop session_id>",
  "transcript_path": "/home/<user>/.claude/projects/<dashed-cwd>/<session_id>.jsonl",
  "cwd":             "<DIECAST_ROOT>",
  "permission_mode": "bypassPermissions",
  "hook_event_name": "PreToolUse",
  "tool_name":       "Skill",
  "tool_input": {
    "skill":         "landing-report"
  },
  "tool_use_id":     "toolu_01An1WNYRgKRApxnKcgAXa3Q"
}
```

**Notes**
- `tool_input.skill` (singular) is the skill name. **NOT** `tool_input.skill_name`
  as the original plan assumed. sp3's `skill_invoke` handler must use `skill`.
- `tool_input` may include `args` for skills invoked with arguments — not yet
  captured (landing-report was invoked without args).
- `session_id` is the calling context's session — same as the main loop. If a
  subagent invokes a Skill, the PreToolUse hook fires inside the subagent's
  context, which would add `agent_id` per the docs. Currently
  `record_skill`'s "most-recent running cast-* row" heuristic doesn't depend on
  `agent_id`, but capturing it would let us attribute skills to the exact
  dispatching subagent.

## Field summary table

| Field | SubagentStart | SubagentStop | PreToolUse(Task) | PreToolUse(Skill) |
|-------|:-------------:|:------------:|:----------------:|:-----------------:|
| `session_id`             | ✓ (parent)   | ✓ (parent)   | ✓ (parent)       | ✓ (parent)        |
| `agent_id`               | ✓ (subagent) | ✓ (subagent) | conditional¹     | conditional¹      |
| `agent_type`             | ✓            | ✓            | (in tool_input)  | —                 |
| `transcript_path`        | ✓            | ✓            | ✓                | ✓                 |
| `agent_transcript_path`  | —            | ✓            | —                | —                 |
| `cwd`                    | ✓            | ✓            | ✓                | ✓                 |
| `permission_mode`        | —            | ✓            | ✓                | ✓                 |
| `hook_event_name`        | ✓            | ✓            | ✓                | ✓                 |
| `tool_name`              | —            | —            | ✓ ("Agent")      | ✓ ("Skill")       |
| `tool_input.subagent_type` | —          | —            | ✓                | —                 |
| `tool_input.skill`       | —            | —            | —                | ✓                 |
| `tool_use_id`            | —            | —            | ✓                | ✓                 |
| `last_assistant_message` | —            | ✓            | —                | —                 |
| `stop_hook_active`       | —            | ✓            | —                | —                 |
| `parent_session_id`      | **DOES NOT EXIST** | **DOES NOT EXIST** | **DOES NOT EXIST** | **DOES NOT EXIST** |

¹ "conditional" = present only when the hook fires inside a subagent call (per docs).
  In main-loop context, absent.

## Implications for the plan

1. **Drop all `parent_session_id` references.** The field doesn't exist.
2. **`session_id` is the parent main-loop session**, shared by all subagents in
   that session. Use it to **scope to the parent session**, not to identify a
   specific subagent.
3. **`agent_id` is the subagent's identity** and the canonical key for matching
   `SubagentStart` ↔ `SubagentStop`. Add as a column on `agent_runs` (or store
   in `input_params.agent_id`).
4. **Parent resolution for subagent rows** = "most-recent running cast-* row in
   `session_id`." This is what the plan originally called the "fallback" — it
   is now the **primary** path. Works correctly for top-level Task() under a
   slash-command root, and for nested subagents under another cast-* (the outer
   is the most-recent running when the inner starts).
5. **For exact nested attribution** (beyond most-recent-running): capture
   `PreToolUse(Task)` too and use the `tool_use_id` ↔ next `SubagentStart`
   correlation. Defer to v2 unless required.
6. **`record_skill` reads `tool_input.skill`** (singular) — NOT `skill_name`.
7. **No exit/error signal** in `SubagentStop`. v1 status is always `completed`.
   `last_assistant_message` could feed v2 failure detection.
8. **Hook matcher for Task tool**: empirically `"Task"` works in
   `.claude/settings.json`'s PreToolUse matcher, even though the runtime
   `tool_name` reads as `"Agent"`.
