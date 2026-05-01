---
feature: cast-subagent-and-skill-capture
module: cast-server
linked_files:
  - docs/plan/2026-05-01-cast-subagent-and-skill-capture.collab.md
  - cast-server/cast_server/services/subagent_invocation_service.py
  - cast-server/cast_server/services/_invocation_sources.py
  - cast-server/cast_server/services/agent_service.py
  - cast-server/cast_server/services/user_invocation_service.py
  - cast-server/cast_server/cli/_cast_name.py
  - cast-server/cast_server/cli/hook_handlers.py
  - cast-server/cast_server/cli/hook_events.py
  - cast-server/cast_server/cli/install_hooks.py
  - cast-server/cast_server/cli/hook.py
  - cast-server/cast_server/routes/api_agents.py
  - cast-server/cast_server/routes/pages.py
  - cast-server/cast_server/templates/partials/run_skills_chips.html
  - cast-server/cast_server/templates/partials/run_skills_detail.html
  - cast-server/cast_server/templates/macros/run_node.html
  - cast-server/cast_server/db/connection.py
  - cast-server/cast_server/db/schema.sql
  - cast-server/cast_server/models/agent_run.py
  - cast-server/cast_server/app.py
  - cast-server/tests/test_subagent_invocation_service.py
  - cast-server/tests/test_api_agents.py
  - cast-server/tests/test_cli_hook.py
  - cast-server/tests/test_install_hooks.py
  - cast-server/tests/test_runs_skills_chips.py
  - cast-server/tests/test_schema_migration.py
  - goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md
  - goals/cast-subagent-and-skill-capture/notes/e2e-smoke.ai.md
last_verified: "2026-05-01"
---

# Cast Subagent and Skill Capture — Spec

> **Spec maturity:** draft
> **Version:** 1
> **Updated:** 2026-05-01
> **Status:** Draft

## Intent

Cast-server captures every Claude Code `Task()`-dispatched `cast-*` subagent
as an `agent_runs` row, attributes it to the correct parent in the same
Claude main-loop session, and records every Skill invocation that happens
while a cast-* row is the most-recent running cast-* row in that session.
The tree visible at `/runs` is therefore faithful end-to-end: user-typed
slash command → in-turn Task() subagents (any depth of nesting) →
HTTP-dispatched grandchildren, with skill chips on whichever cast-* row was
running when each Skill fired.

The capture path runs through three Claude Code hook events:

- `SubagentStart` opens a row keyed on `(session_id, claude_agent_id)`.
- `SubagentStop` closes that exact row by `claude_agent_id` exact match.
- `PreToolUse` with matcher `"Skill"` appends `{name, invoked_at}` to the
  most-recent running cast-* row in `session_id`.

This spec is **scoped to subagent + skill capture**. It assumes:

- The polite-citizen install/uninstall surface is locked by
  [`cast-hooks.collab.md`](./cast-hooks.collab.md). This spec extends that
  contract with a per-event `matcher` slot.
- The user-typed `/cast-*` slash-command capture path (top-level rows that
  share `session_id` with subagents) is locked by
  [`cast-user-invocation-tracking.collab.md`](./cast-user-invocation-tracking.collab.md).
- The HTTP-dispatched delegation path (rows that own a contract-v2
  `output.json`) is locked by
  [`cast-delegation-contract.collab.md`](./cast-delegation-contract.collab.md).
  Hook-created rows do NOT write `output.json`; they coexist without
  conflict.

The empirical Claude Code hook payload shapes that this spec relies on are
captured at
[`goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md`](../../goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md)
and are **authoritative** for fields the upstream Claude Code docs leave
unspecified.

## User Stories

### US1 — Task()-dispatched cast-* subagents become agent_run rows (Priority: P1)

**As a** developer reviewing the runs tree, **I want to** see a row for every
`cast-*` subagent dispatched via `Task()`, **so that** I never wonder where an
HTTP-triggered descendant run came from.

**Independent test:**
`cast-server/tests/test_subagent_invocation_service.py` calls
`register("cast-foo", session_id="sess-1", claude_agent_id="a-1")` and
asserts a row exists with `agent_name="cast-foo"`, `status="running"`,
`session_id="sess-1"`, `claude_agent_id="a-1"`,
`input_params.source="subagent-start"`, and `started_at` populated.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN Claude Code fires `SubagentStart` with
  `agent_type="cast-foo"`, THE SYSTEM SHALL `POST
  /api/agents/subagent-invocations` with `{agent_type, session_id,
  claude_agent_id, transcript_path, prompt}` and create an `agent_runs` row
  with `agent_name="cast-foo"`, `status="running"`, `started_at=<now>`,
  `session_id=payload.session_id`, `claude_agent_id=payload.agent_id`, and
  `input_params.source="subagent-start"`.
- **Scenario 2:** WHEN Claude Code fires `SubagentStart` with `agent_type` NOT
  matching `^cast-[a-z0-9-]+$`, THE SYSTEM SHALL skip row creation and return
  `{"run_id": null}` with HTTP 200 — the hook is dumb, the server is
  authoritative.

### US2 — Children link to their actual parent via most-recent running cast-* row (Priority: P1)

**As a** developer reviewing the runs tree, **I want** each `Task()`-dispatched
`cast-*` row to attach to its true parent, **so that** the tree is faithful
under nested dispatches.

**Independent test:**
`cast-server/tests/test_subagent_invocation_service.py` seeds a running
parent row A, calls `register(...)` for B in the same `session_id`, and
asserts B's `parent_run_id == A.id`. Nesting case: with B still running,
calls `register(...)` for D and asserts D's `parent_run_id == B.id`
(B is more-recently-started than A).

**Acceptance scenarios:**

- **Scenario 1:** WHEN `SubagentStart` arrives with `session_id=S`, IF one or
  more cast-* rows have `session_id=S` AND `status="running"`, THE SYSTEM
  SHALL set the new row's `parent_run_id` to the most-recently-started of
  those rows. Implementation: `SELECT id FROM agent_runs WHERE session_id=?
  AND status='running' AND agent_name LIKE 'cast-%' ORDER BY started_at DESC
  LIMIT 1` (`resolve_parent_for_subagent`).
- **Scenario 2:** WHEN no running cast-* row exists in `session_id`, THE
  SYSTEM SHALL set `parent_run_id` to NULL — orphan, not error.
- **Scenario 3:** WHEN parallel siblings A and B are both running and B then
  dispatches D, THE SYSTEM SHALL resolve D's parent to whichever of A/B was
  most recently started. Documented v1 limitation; v2 may use `tool_use_id`
  for exact attribution.

### US3 — Subagent lifecycle closes cleanly (Priority: P1)

**As a** developer, **I want** completed subagents to transition to terminal
status, **so that** the tree doesn't accumulate stale "running" rows.

**Independent test:**
`cast-server/tests/test_subagent_invocation_service.py` calls
`register(...)` then `complete(claude_agent_id)` and asserts the row's
`status="completed"` and `completed_at` is non-null.

**Acceptance scenarios:**

- **Scenario 1:** WHEN Claude Code fires `SubagentStop` for a tracked
  subagent, THE SYSTEM SHALL `POST
  /api/agents/subagent-invocations/complete` with `{claude_agent_id}` and
  transition the row WHERE `claude_agent_id=?` AND `status='running'` to
  `status="completed"`, `completed_at=<now>`. Single-row exact-match update.
- **Scenario 2:** WHEN `SubagentStop` fires with a `claude_agent_id` that is
  unknown or already closed, THE SYSTEM SHALL return `{"closed": 0}` with
  HTTP 200 and never raise.
- **Scenario 3:** WHEN `SubagentStop` fires, THE SYSTEM SHALL always set
  `status="completed"` regardless of `last_assistant_message` content. v1
  does not detect failure — `SubagentStop` carries no explicit `error` /
  `exit_code` field.

### US4 — Skills used by an agent are captured on the run (Priority: P1)

**As a** developer reviewing a run, **I want to** see which Claude Code skills
the agent invoked during its execution, **so that** I can understand what it
actually did without reading the transcript.

**Independent test:**
`cast-server/tests/test_subagent_invocation_service.py` registers a
running cast-* row, calls `record_skill(session_id, "cast-detailed-plan")`
twice with different timestamps, and asserts the row's `skills_used` JSON
contains exactly two entries in invocation order, each shaped
`{"name": "cast-detailed-plan", "invoked_at": "<iso8601>"}`.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `PreToolUse` fires with `tool_name="Skill"` and
  payload `session_id=S`, THE SYSTEM SHALL `POST
  /api/agents/subagent-invocations/skill` with `{session_id, skill,
  invoked_at}` and append `{name: skill, invoked_at}` to the
  most-recent-running cast-* row's `skills_used` JSON list. Wire field is
  `skill` (singular) — matches `tool_input.skill` per Spike A.
- **Scenario 2:** WHEN the same skill is invoked multiple times in the same
  run, THE SYSTEM SHALL append one entry per invocation, preserving order
  and count.
- **Scenario 3:** WHEN `PreToolUse(Skill)` fires for a `session_id` with no
  running cast-* row, THE SYSTEM SHALL return `{"appended": 0}` with HTTP 200
  and never raise.
- **Scenario 4:** WHEN both a user-invocation row and a subagent row are
  running concurrently in the same session, THE SYSTEM SHALL attach the
  skill to whichever started most recently (`ORDER BY started_at DESC LIMIT
  1`). After the inner subagent's `SubagentStop`, subsequent skills attach
  back to the user-invocation row.

### US5 — Runs UI shows skills at L2/L3 detail (Priority: P2)

**As a** user browsing the runs tree, **I want** skills surfaced compactly at
L2 and in full at L3, **so that** I get a fast overview without losing the
ability to drill in.

**Independent test:**
`cast-server/tests/test_runs_skills_chips.py` seeds a run with five
distinct skills, asserts the L2 row renders the `.skills-chips` container
with first 2 chip names + a `+3` overflow chip + skill count, and asserts
L3 detail renders a `.skills-detail` table with all 5 names, first
`invoked_at` per name, and per-name invocation count.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a row's `skills_used` is non-empty, THE SYSTEM SHALL
  render a chip-row at L2 with the skill count and the first 2 distinct
  skill names plus a `+N` overflow indicator when more exist.
- **Scenario 2:** WHEN a row's L3 expansion is open, THE SYSTEM SHALL render
  a `.skills-detail` block listing every distinct skill with `name`,
  earliest `invoked_at`, and invocation count.
- **Scenario 3:** WHEN `skills_used` is empty (default `'[]'`) or fails to
  parse as JSON, THE SYSTEM SHALL render no skill chip-row at L2 and no
  `.skills-detail` block at L3 — hide entirely, do not render `0 skills`.

### US6 — Non-cast subagents and Bash CLI cast-* are NOT captured (Priority: P2)

**As a** system designer, **I want** the hook + server to be tightly scoped to
`cast-*` subagents only, **so that** unrelated harness activity (`Explore`,
`Plan`, `general-purpose`, Bash CLI) doesn't pollute the runs table.

**Independent test:**
`cast-server/tests/test_cli_hook.py::test_subagent_start_skips_non_cast_agent_type`
asserts no HTTP POST is issued when `agent_type="Explore"`.
`cast-server/tests/test_subagent_invocation_service.py` asserts
`register("Explore", ...)` returns `None` and creates no row even if a
malformed hook ever bypasses the client-side filter.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `agent_type` does not match
  `^cast-[a-z0-9-]+$` (`AGENT_TYPE_PATTERN` from `cli/_cast_name.py`), THE
  SYSTEM SHALL create no row. The filter is enforced both hook-side
  (early return — avoids pointless POSTs) and server-side (authoritative).
- **Scenario 2:** WHEN any binary is invoked via `Bash` (including a `cast-*`
  CLI), THE SYSTEM SHALL NOT create a row. No `PreToolUse(Bash)` matcher is
  registered in v1.
- **Scenario 3:** WHEN `PreToolUse` fires with `tool_name != "Skill"` (the
  matcher does not actually narrow inside Claude Code), THE SYSTEM SHALL
  early-return in the hook handler before issuing the POST. Two-layer
  defense: settings.json matcher + handler-side `tool_name` check.

### US7 — Hook installation is idempotent, atomic, and surgical (Priority: P1)

**As a** user, **I want** install/uninstall to add/remove only my hook
entries, leaving any existing third-party hooks untouched, with safe atomic
settings.json writes, **so that** my Claude Code config never gets clobbered.

**Independent test:**
`cast-server/tests/test_install_hooks.py::test_round_trip_install_uninstall_byte_equivalent`
seeds a settings.json with third-party entries on `SubagentStart` and
`PreToolUse(matcher=Bash)`, runs install then uninstall, and asserts
byte-equivalence to the seed (modulo JSON re-serialization). Companion
tests cover the `matcher: "Skill"` write
(`test_install_hooks_writes_pretooluse_with_skill_matcher`),
matcher-aware idempotency
(`test_install_preserves_third_party_pretooluse_with_different_matcher`),
and surgical uninstall
(`test_uninstall_removes_ours_regardless_of_matcher`).

**Acceptance scenarios:**

- **Scenario 1:** WHEN install runs against settings.json that already has
  third-party entries on `SubagentStart`, `SubagentStop`, or `PreToolUse`
  (any matcher), THE SYSTEM SHALL append our entry alongside without
  modifying or removing them.
- **Scenario 2:** WHEN install runs twice, THE SYSTEM SHALL detect existing
  entries by `HOOK_MARKER` substring on the inner `command` and not
  duplicate. The matcher key is irrelevant to ours-vs-theirs identity.
- **Scenario 3:** WHEN install writes the `PreToolUse` skill-invoke entry,
  THE SYSTEM SHALL emit `{"matcher": "Skill", "hooks": [{"type":"command",
  "command":"<CAST_HOOK_BIN> skill-invoke", "timeout":3}]}`. Sibling entries
  (`SubagentStart`, `SubagentStop`, `UserPromptSubmit`, `Stop`) MUST NOT
  carry a `matcher` key.
- **Scenario 4:** WHEN uninstall runs, THE SYSTEM SHALL remove ONLY entries
  whose inner `command` starts with `HOOK_MARKER`, drop empty arrays/keys,
  and preserve everything else verbatim. Third-party `PreToolUse` entries
  with different matchers (e.g., `"Bash"`) MUST survive.

### US8 — Stale parents never poison new runs (Priority: P2)

**As a** system designer, **I want** parent resolution to fall back to orphan
when no candidate is currently running, **so that** a crashed or completed
prior cast-* row can never silently re-parent new work.

**Independent test:**
`cast-server/tests/test_subagent_invocation_service.py::test_register_returns_orphan_when_no_running_cast_row_in_session`
seeds a `status="completed"` cast-* row in session S, calls `register` for
a new subagent in S, and asserts `parent_run_id` is NULL.

**Acceptance scenarios:**

- **Scenario 1:** WHEN no cast-* row in `session_id` is `status="running"`,
  THE SYSTEM SHALL set `parent_run_id=NULL`.
- **Scenario 2:** WHEN only non-cast running rows exist in `session_id`
  (e.g., user manually dispatched `Explore` via Task()), THE SYSTEM SHALL
  set `parent_run_id=NULL`. The `agent_name LIKE 'cast-%'` filter excludes
  non-cast subagents from being incorrectly chosen as parents.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | The `SubagentStart` hook handler POSTs `{agent_type, session_id, claude_agent_id, transcript_path, prompt}` to `POST /api/agents/subagent-invocations`. `claude_agent_id` is the wire-side rename of the empirical payload's `agent_id` (avoids collision with `cast_server.models.agent_config.AgentConfig.agent_id`). | Hook is dumb; server filters and decides. Empirical payload shape: see `notes/payload-shapes.ai.md`. |
| FR-002 | `subagent_invocation_service.register` creates an `agent_runs` row with `agent_name=agent_type`, `session_id=payload.session_id`, `claude_agent_id=payload.claude_agent_id`, `status="running"`, `input_params={"source":"subagent-start","prompt":...,"transcript_path":...}`, `goal_slug=<inherited from parent or "system-ops">`, `parent_run_id=resolve_parent_for_subagent(session_id)`, and `started_at=<now>`. | The core capture path. Single source of source constants is `services/_invocation_sources.py`. |
| FR-003 | The cast-* scope filter is the regex `^cast-[a-z0-9-]+$` (`AGENT_TYPE_PATTERN`). Single source of truth lives at `cli/_cast_name.py`. The filter is enforced BOTH hook-side (early return — avoids pointless POSTs) AND server-side (authoritative gate). | Defense in depth. |
| FR-004 | The `SubagentStop` hook handler POSTs `{claude_agent_id}` to `POST /api/agents/subagent-invocations/complete`. Server transitions the row WHERE `claude_agent_id=?` AND `status='running'` to `status="completed"`, `completed_at=<now>`. Single-row exact match. Returns `{"closed": 0|1}` and 200 even on miss. | Closure path. No staleness window — `claude_agent_id` is unique per Claude subagent. |
| FR-005 | The `PreToolUse` hook handler with matcher `"Skill"` POSTs `{session_id, skill, invoked_at}` to `POST /api/agents/subagent-invocations/skill`. Wire field is `skill` (singular) — matches `tool_input.skill` per Spike A. The handler MUST defensively early-return when `tool_name != "Skill"` (the settings.json matcher does NOT reliably narrow at the Claude Code layer). | Two-layer defense: matcher + handler check. |
| FR-006 | `record_skill` appends `{name, invoked_at}` to the most-recent-running cast-* row's `skills_used` JSON array. SQL: `UPDATE agent_runs SET skills_used = json_insert(skills_used, '$[#]', json_object('name', ?, 'invoked_at', ?)) WHERE id = (SELECT id FROM agent_runs WHERE session_id=? AND status='running' AND agent_name LIKE 'cast-%' ORDER BY started_at DESC LIMIT 1)`. **No source filter.** | Decision #1: a slash-command row without subagents must still record its skills. Subagent supersedes parent for skill attribution while running; skills naturally flow back after `complete()`. |
| FR-007 | Parent resolution on `SubagentStart` uses `resolve_parent_for_subagent(session_id)`: `SELECT id FROM agent_runs WHERE session_id=? AND status='running' AND agent_name LIKE 'cast-%' ORDER BY started_at DESC LIMIT 1`. Returns NULL when no candidate exists. | The `agent_name LIKE 'cast-%'` filter is contract — non-cast subagents (e.g., `Explore`, `Plan`, `general-purpose`) MUST NOT become parents. |
| FR-008 | Closure on `SubagentStop` uses `resolve_run_by_claude_agent_id(claude_agent_id)`: `SELECT id FROM agent_runs WHERE claude_agent_id=? ORDER BY started_at DESC LIMIT 1`. The closure path is exact-match on a unique-per-subagent id; no source filter, no staleness window. | User-invocation rows do not populate `claude_agent_id`, so cross-contamination is structurally impossible. |
| FR-009 | The `agent_runs` table has two columns supporting this contract: `skills_used TEXT NOT NULL DEFAULT '[]'` (JSON array of `{name, invoked_at}`) and `claude_agent_id TEXT` (nullable). Migration is additive in `db/connection.py::_run_migrations()` via `try/except sqlite3.OperationalError`. New partial index `idx_agent_runs_claude_agent_id ON agent_runs(claude_agent_id) WHERE claude_agent_id IS NOT NULL` covers the closure path. The pre-existing composite `idx_agent_runs_session_status (session_id, status)` covers the parent-resolution path. | No new single-column `idx_agent_runs_session_id`. |
| FR-010 | All hook scripts MUST exit 0 on any failure (server down, network error, malformed payload). User prompts are never blocked. `_post()` is fire-and-forget — does NOT call `.read()` on the response body. HTTP timeout 2s; hook timeout 3s. | Hook handlers are silent on failure; the server side returns 200 even on miss to remove any temptation to retry. |
| FR-011 | Hook entry points are `cast-hook` console-script subcommands: `cast-hook subagent-start`, `cast-hook subagent-stop`, `cast-hook skill-invoke`. The canonical `(event, subcommand, handler, matcher)` mapping lives in `cli/hook_events.py::HOOK_EVENTS` (4-tuple). Both `cli/install_hooks.py` (write side) and `cli/hook.py` (runtime dispatch) iterate from this single source. Drift is structurally impossible. | Adding a new event = one line in `HOOK_EVENTS`. Tuple slot 4 is the matcher (or `None`). |
| FR-012 | `cli/install_hooks.py` supports per-event `matcher` keys: emits `{"matcher": <m>, "hooks": [...]}` when `matcher is not None`, else flat `{"hooks": [...]}`. The matcher is irrelevant to ours-vs-theirs identity — `HOOK_MARKER` substring on the inner `command` is the sole identity check. Idempotency under matcher: a third-party `PreToolUse(matcher="Bash")` survives any number of installs and uninstalls of our `PreToolUse(matcher="Skill")` entry. | Extends the contract in `cast-hooks.collab.md` (per-event matcher slot) without changing the polite-citizen guarantees. |
| FR-013 | `goal_slug` on a subagent row equals the parent row's `goal_slug` when `parent_run_id` resolves to a row with a non-NULL `goal_slug`; otherwise `"system-ops"`. The `"system-ops"` goal is auto-seeded in `db/connection.py::_seed_system_goals()` (idempotent `INSERT OR IGNORE`) so the FK never violates. The system-ops auto-seed is shipped jointly with the sibling user-invocation tracking spec; this spec only inherits it. | Inheritance + orphan fallback. |
| FR-014 | The Pydantic models for the three new endpoints accept `Optional` fields where appropriate: `transcript_path` and `prompt` on the open endpoint, `invoked_at` on the skill endpoint. All three endpoints return HTTP 200 even on miss (no row created, nothing closed, nothing appended) — never 4xx. The hook contract requires that hook scripts never have a reason to retry. | Endpoint failure semantics. |
| FR-015 | When `CAST_HOST` is non-loopback (i.e., not `localhost`, `127.0.0.1`, or `::1`), `cast_server.app` lifespan startup MUST emit a logger warning naming both `/api/agents/subagent-invocations/` and `/api/agents/user-invocations/` as unauthenticated. | Hook endpoints have no auth; explicit warning when bound non-loopback. |
| FR-016 | The cast-server SQLite connection layer requires SQLite ≥ 3.9 (JSON1 support). `db/connection.py::get_connection` raises `SystemExit` on older versions with a readable upgrade message. | JSON1 is load-bearing for `record_skill`'s `json_insert` and for `_decorate_skills`'s presentation-layer parsing. |
| FR-017 | The L2 chip presentation logic lives in `templates/partials/run_skills_chips.html` and the L3 detail in `templates/partials/run_skills_detail.html`. Both partials are no-ops when `skills_used` is empty or missing. The `/runs` route handler walks the tree and computes `skills_aggregated` (group-by-name, count, earliest `invoked_at`) via `_decorate_skills` in `routes/pages.py`; the macro `macros/run_node.html` renders both partials at the appropriate L2 / L3 slots. | Defensive `json.JSONDecodeError`/`TypeError` handling: malformed `skills_used` is treated as empty, never raises in a request. |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | 100% of `cast-*` Task() dispatches in a session produce a corresponding `agent_runs` row. | `cast-server/tests/test_subagent_invocation_service.py` (unit-level) and end-to-end manual smoke (`goals/cast-subagent-and-skill-capture/notes/e2e-smoke.ai.md`): dispatch ≥3 distinct cast-* subagents and confirm a row per dispatch with matching `agent_name` and `claude_agent_id`. |
| SC-002 | Parent attribution is correct under both nested and parallel-sibling dispatch. Nested: D's parent is B (the inner running cast-* row), not A. Parallel-siblings: D attaches to whichever of A/B was most-recently started (documented v1 limitation). | `cast-server/tests/test_subagent_invocation_service.py` covers `test_register_resolves_parent_to_most_recent_running_cast_row` and `test_register_ignores_non_cast_running_rows_when_resolving_parent`. |
| SC-003 | The new spec passes `bin/cast-spec-checker docs/specs/cast-subagent-and-skill-capture.collab.md` with zero error findings. | `bin/cast-spec-checker docs/specs/cast-subagent-and-skill-capture.collab.md` exits 0. |
| SC-004 | Round-trip install + uninstall on a settings.json seeded with third-party `SubagentStart` and `PreToolUse(matcher="Bash")` entries is byte-equivalent to the seed (modulo JSON re-serialization). | `cast-server/tests/test_install_hooks.py::test_round_trip_install_uninstall_byte_equivalent`. |
| SC-005 | The `/runs` page renders the skill chip-row with `+N` overflow for ≥3 distinct skills on a 1280px viewport without overflow; L3 detail enumerates every distinct skill with count and earliest `invoked_at`. | `cast-server/tests/test_runs_skills_chips.py` — five plan-named tests plus two defensive (malformed JSON / missing field) tests. |
| SC-006 | Stale-parent guard: a `SubagentStart` arriving in a session whose only cast-* row is `status="completed"` produces an orphan row (`parent_run_id=NULL`), not a re-attached child. | `cast-server/tests/test_subagent_invocation_service.py::test_register_returns_orphan_when_no_running_cast_row_in_session`. |
| SC-007 | The L2 chip-row hides entirely when `skills_used` is empty or fails to JSON-parse — never renders a "0 skills" placeholder. | `cast-server/tests/test_runs_skills_chips.py::test_skills_chips_hide_when_empty` plus the defensive `_decorate_skills` parse test. |

## Verification

Live coverage for this spec is asserted by:

- `cast-server/tests/test_subagent_invocation_service.py` — service-layer
  tests for `register`, `complete`, `record_skill`, parent resolution
  (cast-* filter, ordering, orphan fallback), `claude_agent_id`
  round-trip, goal-slug inheritance + system-ops fallback, and the
  `record_skill` "user-invocation alone vs. user-invocation + subagent both
  running" attribution rule.
- `cast-server/tests/test_api_agents.py` — HTTP route tests for the three
  new endpoints under `/api/agents/subagent-invocations/`, including
  no-row-created return shape on a non-cast `agent_type`, complete-on-miss
  return shape, and skill append.
- `cast-server/tests/test_cli_hook.py` — CLI-side tests for the three new
  hook handlers: cast-* scope filter on `subagent_start`, defensive
  early-returns on missing `agent_id` / `session_id` / non-`Skill`
  `tool_name`, exit-0-on-server-unreachable, and the fire-and-forget
  contract (`_post` does not call `.read()` on the response body).
- `cast-server/tests/test_install_hooks.py` — installer tests covering the
  `matcher: "Skill"` write, third-party `PreToolUse(matcher="Bash")`
  preservation, surgical uninstall regardless of matcher, and the
  byte-equivalent round-trip.
- `cast-server/tests/test_runs_skills_chips.py` — `/runs` rendering tests
  for L2 chip-row, L3 detail, overflow behavior, hide-when-empty, plus
  defensive JSON parsing.
- `cast-server/tests/test_schema_migration.py` — asserts the
  `skills_used` and `claude_agent_id` migrations are idempotent and the
  partial index `idx_agent_runs_claude_agent_id` exists.

This spec does not enumerate test cases inline; it cites where the live
coverage lives. The plan
(`docs/plan/2026-05-01-cast-subagent-and-skill-capture.collab.md`) is the
rationale archive — read it for the "why" behind the locked decisions
referenced above. The empirical hook payload capture
(`goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md`) is
authoritative for any field shape disputes.

## Out of scope

The following items are explicitly NOT covered by this spec; they are
deferred to future sub-phases.

- **User-typed `/cast-*` slash command capture.** Owned by sibling
  [`cast-user-invocation-tracking.collab.md`](./cast-user-invocation-tracking.collab.md).
  Subagent rows ride the same `session_id` field but additionally carry
  `claude_agent_id` and use a different `source` discriminator
  (`subagent-start` vs. `user-prompt`). Source constants live in
  `cast-server/cast_server/services/_invocation_sources.py`.
- **Bash invocations of `cast-*` CLI binaries.** Rare and likely a
  delegation-contract violation. Address by enforcing the HTTP path in the
  agent-design guide.
- **Non-`cast-*` subagent capture** (`Explore`, `Plan`, `general-purpose`,
  custom user agents). The server-side filter excludes them.
- **`PreToolUse` capture for non-`Skill` tools** (`Bash`, `Read`, `Write`,
  etc.). Future work for security audit; not in v1 scope.
- **Capturing skill arguments.** Privacy and redaction concerns make this a
  v2 feature. v1 stores `name` + `invoked_at` only.
- **Real-time WebSocket push of skill events to the runs UI.** Polling at
  L3-expand time is sufficient.
- **Backfill of historical Claude Code sessions** before this feature
  ships. New sessions only.
- **Multi-machine / multi-host attribution.** Same-machine assumption
  matches the sibling spec.
- **`output.json` synthesis for hook-created rows.** They are tracking
  artifacts, not delegation outputs. The contract-v2 schema in
  [`cast-output-json-contract.collab.md`](./cast-output-json-contract.collab.md)
  is for HTTP-dispatched runs.
- **Cancellation-vs-completion detection on `SubagentStop`.** v1 sets
  `status="completed"` unconditionally. `SubagentStop` carries no
  `error` / `exit_code` field.
- **Exact-attribution under parallel siblings.** v1 uses the
  most-recently-started heuristic. v2 may use `tool_use_id` correlation.

## Cross-references

- Polite-citizen install/uninstall surface (per-event `matcher` slot
  added by this spec): see [`cast-hooks.collab.md`](./cast-hooks.collab.md).
- User-typed slash-command capture (top-level rows that share `session_id`
  with subagents): see
  [`cast-user-invocation-tracking.collab.md`](./cast-user-invocation-tracking.collab.md).
- HTTP-dispatched delegation contract (rows that own a contract-v2
  `output.json`; this spec's hook-created rows do not):
  see [`cast-delegation-contract.collab.md`](./cast-delegation-contract.collab.md).
- `output.json` schema for delegation rows (unrelated to hook-created
  rows): see
  [`cast-output-json-contract.collab.md`](./cast-output-json-contract.collab.md).
- Threaded `/runs` rendering surface that consumes `skills_used`:
  see [`cast-runs-screen.collab.md`](./cast-runs-screen.collab.md).
- Empirical Claude Code hook payload capture (authoritative for field
  names the upstream docs leave unspecified):
  [`goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md`](../../goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md).

## Open Questions

- **[USER-DEFERRED]** Skill chip-list overflow and click-through behavior
  at L2: how many chips before the `+N` overflow shows, and should chips
  filter `/runs` by skill name on click? v1 ships with 2 chips + count + no
  click-through. Resolver: design pass once usage data exists.
- **[USER-DEFERRED]** Capturing full skill arguments and rendering them at
  L3. Reason: argument values can include user prompts and may carry
  secrets; redaction is its own design problem. v1 stores name +
  `invoked_at` only.
- **[USER-DEFERRED]** Promoting `skills_used` from a JSON column to a
  relational `agent_run_skills` table. Reason: deferred until aggregation
  queries (e.g., "skills used across all runs of cast-foo this week")
  become a UI requirement. JSON1 + presentation-layer aggregation is fast
  enough at current row counts.
- **[USER-DEFERRED]** Exact parent attribution under parallel-sibling
  dispatch via `tool_use_id` correlation. Reason: parallel cast-*
  dispatches in a single session are rare in practice; the
  most-recently-started heuristic is acceptable for v1.
