# Shared Context: capture-user-invocations-as-runs

## Source Documents
- Plan: `<DIECAST_ROOT>/docs/plan/2026-05-01-capture-user-invocations-as-runs.collab.md`
- Reference settings-injection pattern: `<GSTACK_ROOT>/bin/gstack-settings-hook`

## Project Background

Today, an `agent_run` row only exists when an agent dispatches another agent over HTTP
(`POST /api/agents/{name}/trigger`) or via `invoke_agent()`. When the user types a
`/cast-*` slash command directly into Claude Code, the main loop runs the skill in-process,
producing **no row at all**. The threaded runs tree thus shows children but never the human
action that initiated work.

This project captures every user-typed `/cast-*` slash command as a top-level `agent_run`
row whose `agent_name` matches the actual command (e.g., `cast-plan-review`). Lifecycle is
bracketed by Claude Code's `UserPromptSubmit` and `Stop` hooks. The Stop endpoint closes
matching rows by `session_id` with a 1-hour staleness window — self-healing for orphans
without ghost-running rows.

A second, equally important contract is the **hook installer**: it is one listener among
potentially many in the user's `.claude/settings.json` and MUST NEVER override or replace
third-party / pre-existing user hooks. This polite-citizen behavior is the load-bearing
user-safety property that `docs/specs/cast-hooks.collab.md` will lock in.

## Codebase Conventions

- Cast-server lives at `cast-server/cast_server/`. New modules go under `services/`,
  `routes/`, or a new `cli/` package.
- Tests live at `cast-server/tests/`. Pytest with fixtures from `conftest.py`.
- DB is SQLite, initialized via `db/connection.py`. Indices are added inline (see existing
  precedent at `db/connection.py:137` for `idx_error_memories_agent`).
- The `agent_runs` table already has every column we need: `agent_name`, `session_id`,
  `status`, `input_params`, `started_at`, `completed_at`, `parent_run_id`. **No migration.**
- Console scripts are registered in `pyproject.toml` `[project.scripts]`.

## Key File Paths

| Path | Role |
|------|------|
| `cast-server/cast_server/services/agent_service.py` | `create_agent_run()`, `update_agent_run()`, `get_agent_run()`. **Untouched** by this work. |
| `cast-server/cast_server/db/connection.py` | DB init + index definitions. New index added at line ~137. |
| `cast-server/cast_server/routes/api_agents.py` | Existing trigger endpoint (`:55`). Two new endpoints added here. |
| `cast-server/cast_server/models/agent_run.py` | Run model. Lines 6-44. **Unchanged**. |
| `pyproject.toml` | `[project.scripts]` — register `cast-hook` console_script. |
| `bin/cast-server` | Server launcher. Defaults `CAST_PORT=8005`. |
| `agents/cast-init/cast-init.md` (or wherever `/cast-init` lives) | Add an "install cast-hook entries" final step (sp6). |

## Data Schemas & Contracts

### User-invocation row shape

A user-invocation row is an ordinary `agent_runs` row distinguished by:

```
agent_name      = "<slash-command-name without leading '/'>"   e.g. "cast-plan-review"
input_params    = {"source": "user-prompt", "prompt": "<full prompt text>"}
status          = "running"  (transitions to "completed" on Stop)
session_id      = <Claude Code session_id>
parent_run_id   = NULL       (always top-level — Decision #3)
started_at      = ISO8601 UTC
completed_at    = NULL → ISO8601 UTC (set on Stop)
goal_slug       = "system-ops"  (matches existing CLI invocation default)
```

**Discriminator (Decision #2):** `json_extract(input_params, '$.source') = 'user-prompt'`.
No new column. No migration.

### HTTP endpoints

```
POST /api/agents/user-invocations
  body: {"agent_name": str, "prompt": str, "session_id": str | null}
  resp: {"run_id": str}

POST /api/agents/user-invocations/complete
  body: {"session_id": str | null}
  resp: {"closed": int}     # count of rows closed (typically 1; 2+ = orphans cleaned)
```

### Stop close-by-session SQL (Decision #4 + #5)

```sql
UPDATE agent_runs
   SET status='completed', completed_at=?
 WHERE session_id=?
   AND status='running'
   AND json_extract(input_params,'$.source')='user-prompt'
   AND started_at > ?               -- now − 1h staleness window
```

### Hook detection

- Regex: `^\s*/(cast-[a-z0-9-]+)`
- Matched in the **hook handler only** (client side). The server is agnostic to the
  prefix — it accepts any `agent_name`.

### settings.json entry shape (additive)

```json
"hooks": {
  "UserPromptSubmit": [
    { "hooks": [{ "type": "command", "command": "cast-hook user-prompt-start", "timeout": 3 }] }
  ],
  "Stop": [
    { "hooks": [{ "type": "command", "command": "cast-hook user-prompt-stop", "timeout": 3 }] }
  ]
}
```

### Single source of truth for hook events (Decision #10)

`cast-server/cast_server/cli/hook_events.py` exposes:

```python
HOOK_EVENTS = [
    ("UserPromptSubmit", "user-prompt-start", _h.user_prompt_start),
    ("Stop",             "user-prompt-stop",  _h.user_prompt_stop),
]
DISPATCH = {sub: handler for _, sub, handler in HOOK_EVENTS}
COMMAND_FOR_EVENT = {evt: f"cast-hook {sub}" for evt, sub, _ in HOOK_EVENTS}
```

Both `install_hooks.py` (write side) and `hook.py` (runtime dispatch) import from here.
**Drift is structurally impossible.**

## Pre-Existing Decisions (locked at plan-review BIG)

| # | Decision |
|---|----------|
| 1 | `agent_name` is the actual agent (`cast-plan-review`), not a synthetic name. |
| 2 | Discriminator is `input_params.source == "user-prompt"`. No new model field. |
| 3 | **No ambient parent linking.** User-invocation rows stay top-level. |
| 4 | Stop closes by `session_id` (no marker file). |
| 5 | 1-hour staleness window on the close-by-session query. |
| 6 | New `cast-hook` console_script with subcommands. |
| 7 | settings.json injection follows gstack's atomic `.tmp + os.replace` pattern. |
| 8 | Install invoked from `/cast-init` (default ON, `--no-hooks` opt-out); standalone `cast-hook install`. Project-level scope by default. |
| 9 | Missing settings.json → create. Malformed → abort. `OSError`/`PermissionError` → readable error. Cleanup `.tmp` always. |
| 10 | Single canonical event/subcommand mapping in `cli/hook_events.py`. |
| 11 | New service file `services/user_invocation_service.py` (does NOT extend agent_service.py). |
| 12 | Two endpoints under `/api/agents/user-invocations/`. |
| 13 | Hook detects `/cast-*` via regex. Server is agnostic to prefix. |
| 14 | `Stop` always reports `status=completed`. v1 doesn't detect cancellation. |

## Relevant Specs

No existing specs cover the files this plan creates. Two new specs will be authored in
sub-phase 7:
- `docs/specs/cast-user-invocation-tracking.collab.md` — lifecycle contract.
- `docs/specs/cast-hooks.collab.md` — polite-citizen install/uninstall contract.

Cross-reference: `docs/specs/cast-delegation-contract.collab.md` should later get a
back-reference noting that user-invocation rows are now a recognized top-level kind
(handled in sp7).

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|-----------|------|-----------|--------|-------------------|
| sp1 | Sub-phase | -- | sp2, sp3, sp7, sp8 | -- |
| sp2 | Sub-phase | sp1 | sp7, sp8 | sp3, sp4 |
| sp3 | Sub-phase | sp1 | sp7, sp8 | sp2, sp4 |
| sp4 | Sub-phase | sp1 (service exists for handler tests' realism); strictly only needs `pyproject.toml` writable | sp5, sp6, sp7, sp8 | sp2, sp3 |
| sp5 | Sub-phase | sp4 | sp6, sp7, sp8 | -- |
| sp6 | Sub-phase | sp5 | sp7, sp8 | -- |
| sp7 | Sub-phase | sp1-sp6 (specs reflect actual behavior) | sp8 | -- |
| sp8 | Sub-phase | sp1-sp7 | -- | -- |

**Parallel safety:** sp2, sp3, and sp4 touch disjoint files:
- sp2 → `routes/api_agents.py`, `tests/test_api_agents.py`
- sp3 → `db/connection.py`
- sp4 → new `cli/` package, `pyproject.toml`, new `tests/test_cli_hook.py`

These three can run in parallel **after** sp1 lands. (Plan author may still prefer
sequential — that's fine, just slower.)
