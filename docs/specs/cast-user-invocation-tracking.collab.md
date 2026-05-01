---
feature: cast-user-invocation-tracking
module: cast-server
linked_files:
  - docs/plan/2026-05-01-capture-user-invocations-as-runs.collab.md
  - cast-server/cast_server/services/user_invocation_service.py
  - cast-server/cast_server/cli/hook_handlers.py
  - cast-server/cast_server/cli/hook_events.py
  - cast-server/cast_server/cli/hook.py
  - cast-server/cast_server/routes/api_agents.py
  - cast-server/cast_server/db/connection.py
  - cast-server/tests/test_user_invocation_service.py
  - cast-server/tests/test_api_agents.py
  - cast-server/tests/test_cli_hook.py
last_verified: "2026-05-01"
---

# Cast User-Invocation Tracking — Spec

> **Spec maturity:** draft
> **Version:** 1
> **Updated:** 2026-05-01
> **Status:** Draft

## Intent

Cast-server captures every user-typed `/cast-*` slash command as a top-level
`agent_run` row whose `agent_name` matches the slash command. Lifecycle is
bracketed by Claude Code's `UserPromptSubmit` and `Stop` hooks. The Stop endpoint
closes by `session_id` with a 1-hour staleness window — self-healing for orphans
without ghost-running rows. Children of in-turn dispatches are NOT auto-linked
to the user-invocation row in v1; correlation across the threaded runs tree is
by `session_id` plus timestamps only.

The hook installation contract that puts the `cast-hook` listener into the
user's Claude Code settings is a separate spec — see
`cast-hooks.collab.md`. This spec assumes the hooks are present and reachable;
it locks the lifecycle, row shape, and HTTP contract that the hook handlers
drive.

## User Stories

### US1 — Slash-command invocation creates a row (Priority: P1)

**As an** operator running `/cast-plan-review` from Claude Code, **I want** a
top-level `agent_run` row to appear immediately, **so that** the runs tree
shows the human action that initiated downstream work.

**Independent test:** `cast-server/tests/test_user_invocation_service.py`
seeds a user-prompt invocation via `register("cast-plan-review", "<prompt>",
"sess-1")` and asserts a row exists with `agent_name="cast-plan-review"`,
`status="running"`, `input_params.source="user-prompt"`, `session_id="sess-1"`,
`parent_run_id=null`, and `started_at` populated.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN the `UserPromptSubmit` hook fires with a prompt
  matching `^\s*/(cast-[a-z0-9-]+)`, THE SYSTEM SHALL `POST
  /api/agents/user-invocations` with `{agent_name, prompt, session_id}` and
  insert a top-level `agent_run` row whose `agent_name` is the captured slash
  command without the leading `/`.
- **Scenario 2:** WHEN the row is created, THE SYSTEM SHALL set
  `input_params = {"source": "user-prompt", "prompt": "<full prompt text>"}`,
  `goal_slug = "system-ops"`, `parent_run_id = NULL`, `status = "running"`,
  and `started_at` to the current ISO8601 UTC timestamp.

### US2 — Lifecycle closes on Stop (Priority: P1)

**As an** operator, **I want** the user-invocation row to transition to
`completed` as soon as the Claude Code `Stop` hook fires for the session,
**so that** the row does not show as "running" forever after the turn ends.

**Independent test:**
`cast-server/tests/test_user_invocation_service.py` calls `complete("sess-1")`
after `register(...)` and asserts the row's `status="completed"` and
`completed_at` is non-null.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the `Stop` hook fires for a session that has at least
  one running user-prompt row started within the last hour, THE SYSTEM SHALL
  set `status="completed"` and `completed_at=<now>` for every such row in
  that session and return `{"closed": <count>}`.
- **Scenario 2:** WHEN `Stop` fires but no matching row exists, THE SYSTEM
  SHALL return `{"closed": 0}` without raising — Stop is unconditionally safe.

### US3 — Non-cast prompts are ignored (Priority: P1)

**As an** operator, **I want** freeform prompts and non-cast slash commands
to leave no rows behind, **so that** the runs tree is not polluted by every
user keystroke.

**Independent test:** `cast-server/tests/test_cli_hook.py` feeds a non-cast
prompt (e.g., `"hello world"` and `"/help"`) into the
`user-prompt-start` handler and asserts that no HTTP POST is issued.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the `UserPromptSubmit` payload's `prompt` does NOT
  match `^\s*/(cast-[a-z0-9-]+)`, THE SYSTEM SHALL skip the HTTP call
  entirely and return without side effects.
- **Scenario 2:** WHEN the prompt is a non-cast slash command (e.g.,
  `/help`, `/clear`), THE SYSTEM SHALL treat it as non-matching — the regex
  is anchored to the `cast-` prefix.

### US4 — Crashed-session orphans self-heal (Priority: P1)

**As an** operator whose previous turn crashed mid-execution, **I want** the
next `Stop` in the same `session_id` to close the orphan row alongside the
current one (provided it is fresh), **so that** the runs tree does not
accumulate ghost-running rows.

**Independent test:** `cast-server/tests/test_user_invocation_service.py`
seeds two running rows in the same session with `started_at` within the
1-hour window, calls `complete(session_id)`, and asserts both transitioned
to `completed`.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `Stop` fires in a session with multiple running
  user-prompt rows whose `started_at > now − 1h`, THE SYSTEM SHALL close
  every such row in a single `UPDATE` and report the row count.
- **Scenario 2:** WHEN a session has a running user-prompt row whose
  `started_at <= now − 1h`, THE SYSTEM SHALL leave it untouched. Stale
  orphans are out of scope for the close-by-session sweep.

### US5 — Multiple invocations per session each get their own row (Priority: P1)

**As an** operator running multiple `/cast-*` commands in one Claude Code
session, **I want** each invocation to open and close its own row, **so that**
the runs tree shows the actual sequence of turns rather than a single
collapsed row.

**Independent test:** `cast-server/tests/test_user_invocation_service.py`
calls `register(...)` then `complete(...)` then `register(...)` then
`complete(...)` against the same `session_id` and asserts two distinct
completed rows exist with non-overlapping `started_at`/`completed_at`.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the same `session_id` invokes `/cast-*` N times, THE
  SYSTEM SHALL produce N rows, each opened by its own
  `UserPromptSubmit` and closed by the matching `Stop`.
- **Scenario 2:** WHEN turn K's `Stop` fires, THE SYSTEM SHALL close only
  rows whose `status='running'` at that moment — already-completed rows
  from earlier turns are unaffected.

### US6 — Children stay top-level (Priority: P1)

**As a** runs-tree consumer, **I want** the user-invocation row to remain
top-level (`parent_run_id = NULL`) even when the slash command's skill
dispatches sub-agents during the turn, **so that** v1 does not promise
ambient parent-linking we have not built.

**Independent test:** `cast-server/tests/test_api_agents.py` registers a
user-invocation row, dispatches a child agent, and asserts the
user-invocation row's `parent_run_id` remains `NULL` and the child's
`parent_run_id` is whatever the dispatcher passed (NOT the user-invocation
row id).

**Acceptance scenarios:**

- **Scenario 1:** WHEN a `/cast-*` skill dispatches a child via
  `POST /api/agents/{name}/trigger` during the same turn, THE SYSTEM SHALL
  NOT auto-link the child to the user-invocation row.
- **Scenario 2:** WHEN downstream UI needs to correlate the user-invocation
  row with its in-turn dispatches, THE SYSTEM SHALL rely on `session_id` +
  timestamp overlap. v1 does not introduce a parent-linking column.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | `agent_name` MUST equal the slash-command name without the leading `/` (e.g., `/cast-plan-review` → `"cast-plan-review"`). | Decision #1. No synthetic name. |
| FR-002 | The discriminator for user-invocation rows is `json_extract(input_params, '$.source') = 'user-prompt'`. No new column on `agent_runs`. | Decision #2. Avoids a migration. |
| FR-003 | User-invocation rows MUST have `parent_run_id = NULL`. v1 does not promote ambient parent linking. | Decision #3. |
| FR-004 | The hook handler detects user-invocations via the regex `^\s*/(cast-[a-z0-9-]+)` applied to the `UserPromptSubmit` payload's `prompt` field. The server is agnostic to the prefix and accepts any non-empty `agent_name`. | Decision #13. Server-side prefix filtering is intentionally rejected — keeps the route reusable. |
| FR-005 | `Stop` closes by `session_id` using `UPDATE agent_runs SET status='completed', completed_at=? WHERE session_id=? AND status='running' AND json_extract(input_params,'$.source')='user-prompt' AND started_at > <now − 1h>`. | Decisions #4 + #5. No marker file; close-by-session keys off the natural Claude Code identifier. |
| FR-006 | Stop's staleness window is exactly 1 hour. Rows older than 1 hour with `status='running'` are NEVER closed by the close-by-session sweep. | Decision #5. Bounded blast radius. |
| FR-007 | An index `idx_agent_runs_session_status ON agent_runs(session_id, status)` MUST exist to keep the close-by-session UPDATE O(matches), not O(table). | Created at `db/connection.py:141`. |
| FR-008 | `POST /api/agents/user-invocations` accepts `{agent_name: str, prompt: str, session_id: str | null}` and returns `{run_id: str}`. The route MUST NOT validate the `cast-` prefix on `agent_name` — that is the hook's job. | Decision #12. Two endpoints under `/api/agents/user-invocations/`. |
| FR-009 | `POST /api/agents/user-invocations/complete` accepts `{session_id: str | null}` and returns `{closed: int}`. A missing or empty `session_id` MUST return `{closed: 0}` without raising — the Stop hook fires unconditionally. | Decision #14 + endpoint failure semantics. |
| FR-010 | Stop status is always `completed`. v1 does not detect cancellation; a turn killed mid-flight still closes as `completed`. | Decision #14. Cancellation detection is a future concern. |
| FR-011 | `register` writes `started_at` explicitly to the current ISO8601 UTC timestamp because the runs tree uses `started_at` (not `created_at`) for chronological ordering and rollups. | Implementation note locked in `services/user_invocation_service.py:register`. |
| FR-012 | User-invocation rows MUST have `goal_slug = "system-ops"`, matching the existing CLI invocation default in `agent_service.invoke_agent`. | Decision #1 echoed at the storage layer. |
| FR-013 | The hook handler MUST NEVER block the user prompt: HTTP failures (timeout, connection refused, 5xx) are swallowed silently. | Implementation in `cli/hook_handlers.py`'s `_post`. |
| FR-014 | The canonical mapping of Claude Code event → hook subcommand → handler lives in `cli/hook_events.py` (`HOOK_EVENTS`, `DISPATCH`, `COMMAND_FOR_EVENT`). Both install-side and runtime-side dispatch import from this module. | Decision #10. Drift between install and dispatch is structurally impossible. |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | A `/cast-plan-review` invocation creates exactly one `agent_runs` row with the locked shape (agent_name without leading slash, parent_run_id null, started_at populated, goal_slug system-ops). | `cast-server/tests/test_user_invocation_service.py` `test_register_*` cases. |
| SC-002 | The matching `Stop` transitions that row to `completed` with a populated `completed_at`. | `cast-server/tests/test_user_invocation_service.py` `test_complete_*` cases. |
| SC-003 | Non-cast prompts and non-cast slash commands produce zero rows. | `cast-server/tests/test_cli_hook.py` `test_user_prompt_start_ignores_non_cast`. |
| SC-004 | Two running user-prompt rows in one session (both within the 1-hour window) close in a single `Stop` and the rowcount is 2. | `cast-server/tests/test_user_invocation_service.py` orphan-cleanup case. |
| SC-005 | A running user-prompt row whose `started_at > 1h ago` is NOT closed by `Stop` and remains `running`. | `cast-server/tests/test_user_invocation_service.py` staleness-window case. |
| SC-006 | `POST /api/agents/user-invocations/complete` with `session_id=null` or omitted returns `{"closed": 0}` and 200, never 4xx/5xx. | `cast-server/tests/test_api_agents.py` complete-with-null-session case. |
| SC-007 | The runs tree query `get_runs_tree` does NOT auto-link sub-agents to the user-invocation row. The user-invocation row appears as L1 with whatever children the dispatcher explicitly attached. | `cast-server/tests/test_api_agents.py` covering parent-id semantics + the existing `tests/test_runs_tree.py` rollup contract. |

## Verification

Live coverage for this spec is asserted by:

- `cast-server/tests/test_user_invocation_service.py` — service-layer tests
  for `register`, `complete`, the staleness window, and the JSON
  discriminator. Includes orphan-cleanup and same-session multi-invocation
  cases.
- `cast-server/tests/test_api_agents.py` — HTTP route tests for the two new
  endpoints under `/api/agents/user-invocations/`, including the
  null-`session_id` complete case (FR-009 / SC-006).
- `cast-server/tests/test_cli_hook.py` — CLI-side tests covering the regex
  filter, the silent-on-network-failure contract (FR-013), and the
  subcommand dispatch through `cli/hook_events.py`.

This spec does not enumerate test cases inline; it cites where the live
coverage lives. The plan
(`docs/plan/2026-05-01-capture-user-invocations-as-runs.collab.md`) is the
rationale archive — read it for the "why" behind the locked decisions
referenced above.

## Out of scope

The following items are explicitly NOT covered by this spec; they are
deferred to future sub-phases.

- **Ambient parent linking** of in-turn child dispatches to the
  user-invocation row. Decision #3 keeps user-invocation rows top-level in
  v1.
- **Cancellation detection.** Decision #14: `Stop` always reports
  `completed`. Distinguishing user-cancelled from naturally-completed turns
  is a future concern.
- **Stale-orphan reaper.** Rows older than the 1-hour staleness window stay
  `running` forever in v1; a separate cleanup job is out of scope.
- **Pre-existing user hooks.** The polite-citizen install/uninstall contract
  for `.claude/settings.json` is the subject of `cast-hooks.collab.md`.
- **Capturing non-cast slash commands** (e.g., `/help`, custom user
  commands). The detection regex is intentionally cast-prefixed.
- **Promoting `agent_name` filter** into a server-side allow/deny list. The
  server is agnostic to the prefix; only the hook filters.

## Cross-references

- Hook installation contract: see
  [`cast-hooks.collab.md`](./cast-hooks.collab.md).
- Task()-dispatched `cast-*` subagent capture: see
  [`cast-subagent-and-skill-capture.collab.md`](./cast-subagent-and-skill-capture.collab.md).
  Subagent rows ride the same `session_id` field but additionally carry
  `claude_agent_id` and use a different `source` discriminator
  (`subagent-start` vs. `user-prompt`). Source constants live in
  `cast-server/cast_server/services/_invocation_sources.py`.
- Top-level run kinds and the `parent_run_id=NULL` invariant: see the
  back-reference in
  [`cast-delegation-contract.collab.md`](./cast-delegation-contract.collab.md).
- Install surface: `/cast-init` Step 4 in
  [`skills/claude-code/cast-init/SKILL.md`](../../skills/claude-code/cast-init/SKILL.md)
  is the canonical entry point that wires `cast-hook install` into a fresh
  project (default ON; opt out with `--no-hooks`).

## Open Questions

- **[USER-DEFERRED]** Whether to add a `kind` column or a top-level
  `parent_user_invocation_id` to lift the discriminator out of `input_params`.
  Reason: deferred until the runs-tree UI demands first-class filtering;
  the JSON-extract discriminator is fast enough at current row counts and
  avoids a migration.
- **[USER-DEFERRED]** Whether to cap `input_params.prompt` length on the
  server side. Reason: deferred until observed bloat; user prompts in
  practice are short and SQLite's TEXT column has no practical ceiling for
  this workload.
