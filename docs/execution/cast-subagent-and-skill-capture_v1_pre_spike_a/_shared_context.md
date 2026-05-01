# Shared Context: cast-subagent-and-skill-capture

## Source Documents

- Plan: `/data/workspace/diecast/docs/plan/2026-05-01-cast-subagent-and-skill-capture.collab.md`
- Sibling shipped: `/data/workspace/diecast/docs/plan/2026-05-01-capture-user-invocations-as-runs.collab.md`
- Sibling shipped: `/data/workspace/diecast/docs/plan/2026-05-01-cast-runs-threaded-tree.collab.md`

## Project Background

This plan closes the third leg of the runs-tree trilogy. Two siblings have already
shipped:

1. User-typed `/cast-*` slash commands now produce top-level `agent_runs` rows
   (`cast-server/cast_server/services/user_invocation_service.py`). These rows carry
   `input_params.source = "user-prompt"`, `goal_slug = "system-ops"`, and a populated
   `agent_runs.session_id`.
2. The `/runs` page renders the threaded parent/child tree.

This plan adds the missing capture path: **`Task()`-dispatched `cast-*` subagents
and the skills they invoke**. Claude Code's `SubagentStart` payload provides an
explicit `parent_session_id`, so parent attribution is a real `session_id`-keyed
lookup against the existing `agent_runs.session_id` column populated by the
sibling — no new attribution columns. The only new column is `skills_used`.
Skills are captured via `PreToolUse` matcher `"Skill"` and surfaced as compact
chips at L2 / detailed list at L3.

## Pre-existing Surface (read before starting)

Sibling work already on disk — extend, never duplicate:

- `cast-server/cast_server/services/user_invocation_service.py` — `register()`
  writes rows with `input_params.source = "user-prompt"`, `goal_slug =
  "system-ops"`, and populates `agent_runs.session_id` with Claude's session id.
  `complete()` closes by `session_id` + JSON discriminator + 1-hour staleness
  window.
- `cast-server/cast_server/cli/hook_events.py` — **canonical** `(event,
  subcommand, handler)` registry. Comment on line 4: "Adding a new hook event =
  one line in this file." Both `install_hooks.py` and `hook.py` iterate from it.
- `cast-server/cast_server/cli/hook.py` — `cast-hook` console-script entry
  point.
- `cast-server/cast_server/cli/hook_handlers.py` — handler implementations.
  Defines `PROMPT_PATTERN = re.compile(r"^\s*/(cast-[a-z0-9-]+)")` and the
  `_post()` / `_read_payload()` helpers. Default port `CAST_PORT=8005`.
- `cast-server/cast_server/cli/install_hooks.py` — idempotent settings.json
  injector iterating `HOOK_EVENTS`; HOOK_MARKER is `"cast-hook "`. Currently
  emits flat entries with no per-event `matcher` support — sp3 extends.
- `cast-server/tests/test_install_hooks.py`, `cast-server/tests/test_cli_hook.py`
  — extend, don't fork.
- HTTP endpoints live under `/api/agents/user-invocations` (POST start, POST
  `/complete`).
- `agent_runs.session_id` column exists and IS populated. The composite
  `idx_agent_runs_session_status ON agent_runs(session_id, status)` already
  exists (`cast-server/cast_server/db/connection.py::_run_migrations()`) and
  fully covers sp1's lookup pattern (`WHERE session_id = ? AND status =
  'running'`). **sp1 does NOT add a new single-column `idx_agent_runs_session_id`.**
- **`system-ops` goal seed has already been landed** in `_run_migrations()` via
  a new `_seed_system_goals(conn)` helper (idempotent `INSERT OR IGNORE`). Live
  DB also has the row inserted out-of-band so the running server doesn't need a
  restart to begin honoring sibling's `register()`. **sp1's auto-seed activity
  is therefore done; sp1 retains only the verification test
  (`test_system_ops_seed_idempotent`) to lock the contract.**

## Codebase Conventions

- Cast-server lives at `cast-server/cast_server/`. New modules go under
  `services/`, `routes/`, or `cli/`.
- Tests live at `cast-server/tests/`. Pytest with fixtures from `conftest.py`.
- DB is SQLite, initialized via `db/connection.py`. Migrations are inline in
  `_run_migrations()` via `try/except sqlite3.OperationalError`.
- The `agent_runs` table currently has every column we need EXCEPT
  `skills_used` — sp1 adds it.
- Console scripts are registered in `pyproject.toml` `[project.scripts]`.

## Key File Paths

| Path | Role |
|------|------|
| `cast-server/cast_server/db/schema.sql` | Add `skills_used TEXT DEFAULT '[]'` to `agent_runs` (sp1). |
| `cast-server/cast_server/db/connection.py` | `_run_migrations()` ALTER for `skills_used`; SQLite 3.9+ floor in `get_connection()` (sp1). `_seed_system_goals()` already lives here. |
| `cast-server/cast_server/models/agent_run.py` | Add `skills_used: list[dict] = []` to `AgentRun` (sp1). |
| `cast-server/cast_server/cli/_cast_name.py` | NEW — single source of truth for cast-name regexes (sp1). |
| `cast-server/cast_server/services/_invocation_sources.py` | NEW — source discriminator constants + filter helper (sp1). |
| `cast-server/cast_server/services/agent_service.py` | Add `resolve_run_by_session_id()` (sp1). Existing `create_agent_run` / `update_agent_run` untouched. |
| `cast-server/cast_server/services/subagent_invocation_service.py` | NEW — `register`, `complete`, `record_skill` (sp2). |
| `cast-server/cast_server/services/user_invocation_service.py` | sp1 refactor: import `USER_PROMPT` + `source_filter_clause` from `_invocation_sources`. Otherwise untouched. |
| `cast-server/cast_server/routes/api_agents.py` | Add 3 new endpoints under `/api/agents/subagent-invocations/` (sp2). |
| `cast-server/cast_server/cli/hook_events.py` | Extend `HOOK_EVENTS` value tuple from 3 to 4 elements (matcher slot); add 3 new entries (sp3). |
| `cast-server/cast_server/cli/hook_handlers.py` | Refactor `_post()` to fire-and-forget; add `subagent_start`, `subagent_stop`, `skill_invoke` handlers; import `AGENT_TYPE_PATTERN` for hook-side scope filter (sp3). |
| `cast-server/cast_server/cli/install_hooks.py` | Per-event matcher key support; idempotency under matcher (sp3). |
| `cast-server/cast_server/templates/partials/run_skills_chips.html` | NEW — L2 partial (sp4). |
| `cast-server/cast_server/templates/partials/run_skills_detail.html` | NEW — L3 partial (sp4). |
| `cast-server/cast_server/routes/pages.py` | `/runs` handler parses `skills_used` JSON and aggregates (sp4). |
| `docs/specs/cast-subagent-and-skill-capture.collab.md` | NEW spec (sp5). |
| `docs/specs/_registry.md` | Register the new spec row (sp5). |
| `docs/specs/cast-delegation-contract.collab.md` | One-line back-reference noting session_id-based hook path (sp5). |
| `goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md` | NEW — verbatim live payload captures from Spike A (sp1). |
| `goals/cast-subagent-and-skill-capture/notes/e2e-smoke.ai.md` | NEW — screenshots + transcript from end-to-end smoke (sp5). |

## Data Schemas & Contracts

### `skills_used` JSON shape

`agent_runs.skills_used` is a JSON array of `{name, invoked_at}` objects. New
column added in sp1. Default `'[]'`.

```
[
  {"name": "cast-detailed-plan", "invoked_at": "2026-05-01T18:00:00Z"},
  {"name": "cast-spec-checker",  "invoked_at": "2026-05-01T18:01:00Z"}
]
```

### Subagent-invocation row shape

```
agent_name      = "<subagent_type>"   e.g. "cast-detailed-plan"
input_params    = {"source": "subagent-start", "prompt": "<…>", "transcript_path": "<…>"}
status          = "running"  → "completed" on SubagentStop
session_id      = <subagent's Claude Code session_id>
parent_run_id   = <resolved via resolve_run_by_session_id(parent_session_id)>
goal_slug       = inherited from parent row, or "system-ops" if orphan
started_at      = ISO8601 UTC
completed_at    = NULL → ISO8601 UTC on SubagentStop
```

### HTTP endpoints (sp2)

```
POST /api/agents/subagent-invocations
  body: {"agent_type": str, "session_id": str, "parent_session_id": str|null,
         "transcript_path": str|null, "prompt": str|null}
  resp: {"run_id": str|null}      # null when agent_type doesn't match cast-*

POST /api/agents/subagent-invocations/complete
  body: {"session_id": str}
  resp: {"closed": int}

POST /api/agents/subagent-invocations/skill
  body: {"session_id": str, "skill_name": str, "invoked_at": str|null}
  resp: {"appended": int}
```

All endpoints return 200 on miss (FR-010 — hook scripts MUST exit 0 and never
retry). 4xx tempts a future hook author to retry.

### Source discriminators (sp1 — `_invocation_sources.py`)

```python
USER_PROMPT     = "user-prompt"
SUBAGENT_START  = "subagent-start"

def source_filter_clause() -> str:
    return "json_extract(input_params, '$.source') = ?"
```

Used by `complete()` of each service ONLY (not by `record_skill`). Sibling's
`user_invocation_service.complete()` is refactored to use this helper.

### Cast-name regexes (sp1 — `_cast_name.py`)

```python
CAST_NAME_BODY = r"cast-[a-z0-9-]+"
PROMPT_PATTERN     = re.compile(rf"^\s*/({CAST_NAME_BODY})")   # slash-prefixed
AGENT_TYPE_PATTERN = re.compile(rf"^{CAST_NAME_BODY}$")        # bare subagent_type
```

`hook_handlers.py` imports `PROMPT_PATTERN` from here (deletes its local
definition). `subagent_invocation_service.py` (sp2) and the new hook handler
`subagent_start()` (sp3) both import `AGENT_TYPE_PATTERN`. Defense in depth:
hook-side filter avoids pointless POSTs; server-side filter is the
authoritative gate.

### Skill attribution rule (sp2 — `record_skill`)

The most-recent running cast-* row in the session wins. SQL:

```sql
UPDATE agent_runs
   SET skills_used = json_insert(skills_used, '$[#]',
                                 json_object('name', ?, 'invoked_at', ?))
 WHERE id = (
   SELECT id FROM agent_runs
    WHERE session_id = ?
      AND status = 'running'
      AND agent_name LIKE 'cast-%'
    ORDER BY started_at DESC
    LIMIT 1
 )
```

The `agent_name LIKE 'cast-%'` filter ensures attachment to a cast-* row
(user-invocation OR subagent), never to an unrelated row that shares the
session. The "most-recent" rule means a subagent supersedes its slash-command
parent for skill attribution while running, then skills naturally flow back to
the parent after the subagent's `complete()` flips its status to `completed`.
**No source filter** on `record_skill` — slash commands without Task() subagents
must still show their skills.

### Goal-slug inheritance rule (sp2 — `register`)

If `parent_run_id` resolves to a row, `goal_slug = SELECT goal_slug FROM
agent_runs WHERE id = ?`. If the SELECT returns NULL or no row, `goal_slug =
"system-ops"`. The orphan fallback prevents NOT-NULL insert failure when a
parent's goal was deleted (FK cascade SET NULL) or when no parent was provided.

### settings.json entry shape (sp3, with matcher support)

```json
"hooks": {
  "UserPromptSubmit": [
    {"hooks": [{"type": "command", "command": "cast-hook user-prompt-start", "timeout": 3}]}
  ],
  "Stop": [
    {"hooks": [{"type": "command", "command": "cast-hook user-prompt-stop", "timeout": 3}]}
  ],
  "SubagentStart": [
    {"hooks": [{"type": "command", "command": "cast-hook subagent-start", "timeout": 3}]}
  ],
  "SubagentStop": [
    {"hooks": [{"type": "command", "command": "cast-hook subagent-stop", "timeout": 3}]}
  ],
  "PreToolUse": [
    {"matcher": "Skill",
     "hooks": [{"type": "command", "command": "cast-hook skill-invoke", "timeout": 3}]}
  ]
}
```

Five entries. `cast-hook install` writes all five; `cast-hook uninstall` removes
only ours. HOOK_MARKER (`"cast-hook "` substring on the inner `command`) is the
only ours-vs-theirs signal — matcher key is irrelevant to identity.

### Single source of truth for hook events (sp3)

`cast-server/cast_server/cli/hook_events.py` extends to 4-tuple:

```python
HOOK_EVENTS = [
    ("UserPromptSubmit", "user-prompt-start", _h.user_prompt_start, None),
    ("Stop",             "user-prompt-stop",  _h.user_prompt_stop,  None),
    ("SubagentStart",    "subagent-start",    _h.subagent_start,    None),
    ("SubagentStop",     "subagent-stop",     _h.subagent_stop,     None),
    ("PreToolUse",       "skill-invoke",      _h.skill_invoke,      "Skill"),
]
```

Both `install_hooks.py` (write side) and `hook.py` (runtime dispatch) import
from here. **Drift is structurally impossible.**

## Pre-Existing Decisions (locked at plan-review HOLD SCOPE)

| # | Decision |
|---|----------|
| 1 | `record_skill` does NOT filter by `source`; it attaches to most-recent running cast-* row. |
| 2 | Cast-* scope filter lives BOTH on hook side (early-return) AND server side (authoritative). |
| 3 | Subagent rows inherit `goal_slug` from parent; fall back to `"system-ops"` when orphan. |
| 4 | `system-ops` goal is auto-created in `_run_migrations()` via `_seed_system_goals()`. (Already shipped.) |
| 5 | Source discriminator constants + filter helper extracted to `_invocation_sources.py`; sibling refactored. |
| 6 | SQLite 3.9+ is a hard contract; startup `SystemExit` on older versions; no fallback. |
| 7 | Verification lists enumerate one named test per decision. |
| 8 | No upgrade-from-partial-sibling-install test (diecast is too new). |
| 9 | Hook `_post()` is fire-and-forget (no `.read()` on response body). |
| 10 | Build order is strictly LINEAR: sp1 → sp2 → sp3 → sp4 → sp5. No parallelism. |
| 11 | sp1 does NOT add `idx_agent_runs_session_id` (composite `idx_agent_runs_session_status` already covers). |
| 12 | sp1 does NOT implement `_seed_system_goals` (already shipped); sp1 retains only the idempotency test. |

## Relevant Specs

- `docs/specs/cast-delegation-contract.collab.md` — adds back-reference in sp5
  noting the parallel session_id-based hook path; no behavioral conflict (hook
  rows don't write delegation output files).
- `docs/specs/cast-output-json-contract.collab.md` — no impact (hook-created
  rows have no output.json).
- `docs/specs/cast-user-invocation-tracking.collab.md` (sibling) — sp5 adds a
  back-reference noting that subagent rows ride the same `session_id` field but
  use a different `source` discriminator and that source constants live in
  `_invocation_sources.py`.
- `docs/specs/cast-hooks.collab.md` (sibling) — sp3's per-event matcher
  extension is a contract change; sp5 should ensure the new spec covers it.
- `docs/specs/cast-subagent-and-skill-capture.collab.md` — NEW spec authored
  in sp5 via `/cast-update-spec`.

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|-----------|------|-----------|--------|-------------------|
| sp1 | Foundation | -- | sp2, sp3, sp4, sp5 | -- |
| sp2 | Server | sp1 | sp3, sp4, sp5 | -- |
| sp3 | Hook layer | sp1, sp2 | sp4, sp5 | -- |
| sp4 | UI | sp1, sp2, sp3 | sp5 | -- |
| sp5 | Spec + E2E | sp1-sp4 | -- | -- |

**No genuine parallelism.** Each sp builds on the previous one's contract:
sp2 needs sp1's schema + helpers, sp3 needs sp2's endpoints, sp4 needs the
data flowing for visual verification, sp5 documents the shipped behavior.
Sub-sub-phases within a single sp can run in any order.

## Risks & Mitigations Summary

See the source plan's "Key Risks & Mitigations" table for the full catalog.
Highest-impact items:

- **Spike A may surface that `parent_session_id` is missing/renamed** (sp1
  decision gate). Fallback: "find most-recent running cast-* row whose
  session_id matches the current Claude session" — works for top-level Task()
  dispatches, fails for nested.
- **Hook endpoints have no auth.** sp2 adds a startup warning when CAST_HOST is
  non-loopback. Document in sp5 spec.
- **Skill attribution dual-running case.** sp2 must test both "no subagent
  running" and "both running" cases explicitly so the rule is contract.
- **Goal_slug inheritance under deleted parent goal.** sp2 must fall back to
  `"system-ops"` when SELECT returns NULL/no row.
