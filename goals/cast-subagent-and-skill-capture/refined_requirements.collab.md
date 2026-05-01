---
status: refined
confidence:
  intent: high
  behavior: high
  constraints: high
  out_of_scope: high
open_unknowns: 0
questions_asked: 2
revisions:
  - 2026-05-01: Spike A — empirical hook payload capture. parent_session_id
    does not exist; redesigned around session_id (parent main-loop) +
    claude_agent_id (per-subagent). PreToolUse(Skill) uses tool_input.skill
    (singular). claude_session_id renamed back to session_id (sibling
    user_invocation_service already uses session_id correctly). New column is
    claude_agent_id (avoids agent_config.agent_id collision).
    Proof: goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md.
---

# Cast Subagent and Skill Capture

> **Spec maturity:** draft
> **Version:** 0.2.0
> **Linked files:**
> - `docs/plan/2026-05-01-capture-user-invocations-as-runs.collab.md` (sibling — slash command roots)
> - `docs/plan/2026-05-01-cast-runs-threaded-tree.collab.md` (sibling — tree rendering)
> - `cast-server/cast_server/models/agent_run.py` (model under change)
> - `cast-server/cast_server/services/agent_service.py` (parent resolution)
> - `cast-server/cast_server/routes/api_agents.py` (new endpoints)
> - `cast-server/cast_server/cli/_cast_name.py` (shared regex; sp1)
> - `cast-server/cast_server/services/_invocation_sources.py` (source discriminators; sp1)
> - `goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md` (Spike A empirical capture — authoritative)
> - `docs/specs/cast-delegation-contract.collab.md` (parent attribution semantics)

## Intent

When a Claude Code parent agent dispatches a `cast-*` subagent via the harness's
`Task()` tool, no `agent_run` row is created today — the subagent runs and any
HTTP triggers it makes appear orphaned in the runs tree. This goal closes that
gap: every `Task()`-dispatched `cast-*` subagent produces a
top-level-or-attached `agent_run` row with **real parent attribution** sourced
from Claude Code's `SubagentStart` payload, and every skill invoked inside that
run is captured on the row so users can see "what cast-foo actually did" at a
glance.

**Empirical payload model (Spike A, 2026-05-01).** `SubagentStart` carries
`session_id` (the parent main-loop's Claude session id, shared by every
subagent in the session), `agent_id` (the subagent's unique runtime id), and
`agent_type`. There is **no `parent_session_id`** field. Parent attribution is
therefore "most-recent running cast-* row in the same session_id" — exact for
top-level-and-nested-cast-* dispatches; coincidence-correct for parallel
siblings (acceptable v1). Closure on `SubagentStop` keys off the subagent's
`agent_id` exactly. See
`goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md` for verbatim
shapes.

**Job statement:** When a parent agent dispatches a cast-* subagent through the
Task tool, I want a faithful row in the runs tree with the right parent and a
visible record of which skills it invoked, so I can audit and debug the run
without reading transcripts.

## User Stories

### US1 — Task()-dispatched cast-* subagents become agent_run rows (Priority: P1)

**As a** developer reviewing the runs tree, **I want to** see a row for every
`cast-*` subagent dispatched via `Task()`, **so that** I never wonder where an
HTTP-triggered descendant run came from.

**Independent test:** From a parent Claude session, dispatch
`Task({subagent_type: "cast-foo"})`. A new `agent_run` row exists with
`agent_name="cast-foo"`, `status="running"`, `session_id` equal to the parent
main-loop's session id, and `claude_agent_id` equal to the subagent's
`agent_id` from the SubagentStart payload.

**Acceptance scenarios:**

- **Scenario 1:** WHEN Claude Code fires `SubagentStart` with
  `agent_type="cast-foo"`, THE SYSTEM SHALL create an `agent_run` row with
  `agent_name="cast-foo"`, `status="running"`, `started_at=now`,
  `session_id=payload.session_id`, `claude_agent_id=payload.agent_id`, and
  `input_params.source="subagent-start"`.
- **Scenario 2:** WHEN Claude Code fires `SubagentStart` with `agent_type` NOT
  matching `^cast-[a-z0-9-]+$`, THE SYSTEM SHALL create no row and return 200
  no-op.

### US2 — Children link to their actual parent via most-recent running cast-* row (Priority: P1)

**As a** developer reviewing the runs tree, **I want** each `Task()`-dispatched
`cast-*` row to attach to its true parent, **so that** the tree is faithful
under nested dispatches.

**Independent test:** A parent run A (already tracked, `status="running"`)
dispatches B via `Task()`; B has `parent_run_id` equal to A's id. B then nests
by dispatching D via `Task()`; D has `parent_run_id` equal to B's id (not A's,
because B is the most-recent running cast-* row when D's SubagentStart fires).

**Acceptance scenarios:**

- **Scenario 1:** WHEN `SubagentStart` arrives with `session_id=S`, IF one or
  more cast-* rows have `session_id=S` AND `status="running"`, THE SYSTEM SHALL
  set the new row's `parent_run_id` to the **most-recent-started** of those
  rows. (Implementation: `agent_name LIKE 'cast-%'` filter + `ORDER BY
  started_at DESC LIMIT 1`.)
- **Scenario 2:** WHEN no running cast-* row exists in `session_id`, THE SYSTEM
  SHALL set `parent_run_id` to NULL (orphan), not raise.
- **Scenario 3:** WHEN parallel siblings A and B are both running and B then
  dispatches D, THE SYSTEM resolves D's parent to whichever of A/B was most
  recently started. (Documented limitation; v2 may use `tool_use_id`
  correlation for exact attribution. v1 acceptable because the parallel-siblings
  case is rare under cast-* usage patterns.)

### US3 — Subagent lifecycle closes cleanly (Priority: P1)

**As a** developer, **I want** completed subagents to transition to terminal
status, **so that** the tree doesn't accumulate stale "running" rows.

**Independent test:** After a `cast-*` subagent's `SubagentStop` hook fires,
the row matched by exact `claude_agent_id` is in `status="completed"` with
`completed_at` set.

**Acceptance scenarios:**

- **Scenario 1:** WHEN Claude Code fires `SubagentStop` for a tracked
  `agent_id=A`, THE SYSTEM SHALL transition the row WHERE `claude_agent_id=A`
  to `status="completed"`, `completed_at=now`. Single-row update.
- **Scenario 2:** WHEN `SubagentStop` fires with an `agent_id` not in our DB
  (filtered out at start, or already closed), THE SYSTEM SHALL no-op silently
  with HTTP 200.
- **Scenario 3:** v1 always sets `status="completed"` regardless of
  `last_assistant_message` content. (Empirical: SubagentStop carries no
  explicit error/exit field; failure detection deferred to v2.)

### US4 — Skills used by an agent are captured on the run (Priority: P1)

**As a** developer reviewing a run, **I want to** see which Claude Code skills
the agent invoked during its execution, **so that** I can understand what it
actually did without reading the transcript.

**Independent test:** A `cast-*` run that invokes `/cast-detailed-plan` and
`/cast-spec-checker` shows
`skills_used=[{"name":"cast-detailed-plan","invoked_at":"…"},
{"name":"cast-spec-checker","invoked_at":"…"}]` on its `agent_run` row.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `PreToolUse` fires with `tool_name="Skill"` and
  payload `session_id=S`, THE SYSTEM SHALL append `{name: tool_input.skill,
  invoked_at: now}` to the **most-recent-running cast-\* row** in
  `session_id=S`. (Note: payload field is `tool_input.skill` singular —
  empirical capture confirmed; was incorrectly assumed `skill_name` in v0.1.)
- **Scenario 2:** WHEN the same skill is invoked multiple times in the same
  run, THE SYSTEM SHALL append one entry per invocation (preserving order and
  count).
- **Scenario 3:** WHEN `PreToolUse` fires for a `session_id` with no running
  cast-* row, THE SYSTEM SHALL no-op silently.
- **Scenario 4:** WHEN both a user-invocation row and a subagent row are
  running concurrently in the same session, THE SYSTEM SHALL attach the skill
  to whichever started most recently (most-recent-running rule). After the
  inner subagent's `SubagentStop`, subsequent skills attach back to the
  user-invocation row.

### US5 — Runs UI shows skills at L2/L3 detail (Priority: P2)

**As a** user browsing the runs tree, **I want** skills surfaced compactly at
L2 and in full at L3, **so that** I get a fast overview without losing the
ability to drill in.

**Independent test:** In `/runs`, expand a cast-* run with three distinct
skills used: L2 line shows a compact chip-list ("3 skills: detailed-plan,
spec-checker, +1"); L3 expansion shows the full list with timestamps and
invocation counts.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a row's `skills_used` is non-empty, THE SYSTEM SHALL
  render a chip-row at L2 with a count and the first 2-3 skill names plus a
  `+N` overflow indicator.
- **Scenario 2:** WHEN a row's L3 expansion is open, THE SYSTEM SHALL render a
  full table or list of skills with `name`, first-invocation time, and
  invocation count.
- **Scenario 3:** WHEN `skills_used` is empty, THE SYSTEM SHALL render no skill
  chip-row at L2 (hide entirely, do not render "0 skills").

### US6 — Non-cast subagents and Bash CLI cast-* are NOT captured (Priority: P2)

**As a** system designer, **I want** the hook + server to be tightly scoped to
`cast-*` subagents only, **so that** unrelated harness activity (Explore, Plan,
general-purpose, Bash CLI) doesn't pollute the runs table.

**Independent test:** Dispatch `Task({subagent_type: "Explore"})` — no row
created. Run `Bash("bin/cast-foo …")` — no row created. Dispatch
`Task({subagent_type: "cast-foo"})` — exactly one row created.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `agent_type` does not match `^cast-[a-z0-9-]+$`, THE
  SYSTEM SHALL create no row.
- **Scenario 2:** Bash invocations of any binary (cast-* CLI included) SHALL
  NOT trigger row creation. (No Bash matcher is installed in v1.)

### US7 — Hook installation is idempotent, atomic, and surgical (Priority: P1)

**As a** user, **I want** install/uninstall to add/remove only my hook
entries, leaving any existing third-party hooks untouched, with safe atomic
settings.json writes, **so that** my Claude Code config never gets clobbered.

**Independent test:** Seed `.claude/settings.json` with a third-party
`SubagentStart` entry; install our hooks; verify both entries present.
Uninstall; verify the third-party entry remains and ours is gone, with empty
arrays/keys cleaned up.

**Acceptance scenarios:**

- **Scenario 1:** WHEN install runs against settings.json that already has
  third-party entries on `SubagentStart`, `SubagentStop`, or `PreToolUse`, THE
  SYSTEM SHALL append our entry alongside without modifying or removing
  others.
- **Scenario 2:** WHEN install runs twice, THE SYSTEM SHALL detect existing
  entries by command-substring marker (`cast-server hook`) and not duplicate.
- **Scenario 3:** WHEN settings.json is malformed JSON, THE SYSTEM SHALL
  abort with a readable error and NOT write.
- **Scenario 4:** WHEN uninstall runs, THE SYSTEM SHALL remove only entries
  whose `hooks[].command` contains the marker; empty arrays/keys are deleted;
  the rest of the file is preserved verbatim.

### US8 — Stale parents never poison new runs (Priority: P2)

**As a** system designer, **I want** parent resolution to fall back to orphan
when no candidate is currently running, **so that** a crashed or completed
prior cast-* row can never silently re-parent new work.

**Independent test:** Create a cast-* row with `session_id=S`,
`status="completed"`. Fire a new `SubagentStart` with `session_id=S`. The new
row has `parent_run_id=NULL` (no running cast-* row to attach to).

**Acceptance scenarios:**

- **Scenario 1:** WHEN no cast-* row in `session_id` is `status="running"`,
  THE SYSTEM SHALL set `parent_run_id=NULL`.
- **Scenario 2:** WHEN only non-cast running rows exist in `session_id` (e.g.,
  user manually dispatched `Explore`), THE SYSTEM SHALL set `parent_run_id=NULL`
  (the `agent_name LIKE 'cast-%'` filter excludes them — non-cast subagents are
  never parents).

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | `SubagentStart` hook POSTs `{agent_type, session_id, claude_agent_id, transcript_path}` to cast-server. (`claude_agent_id` is the payload's `agent_id` renamed for the wire to avoid collision with `agent_config.agent_id`.) | Hook is dumb — server filters and decides. Empirical payload shape: see `notes/payload-shapes.ai.md`. |
| FR-002 | Server creates an `agent_run` row with `agent_name=agent_type`, `session_id=payload.session_id`, `claude_agent_id=payload.claude_agent_id`, `status="running"`, `input_params.source="subagent-start"`, `goal_slug=parent_goal_slug or "system-ops"`, and resolves `parent_run_id` to the most-recent running cast-* row in `session_id` (or NULL if none). | The core capture path. |
| FR-003 | Server filters: only create rows when `agent_type` matches `^cast-[a-z0-9-]+$`. Hook-side filter is the first line of defense; server-side is defense in depth. | Single regex sourced from `cli/_cast_name.py`. |
| FR-004 | `SubagentStop` hook POSTs `{claude_agent_id}` to cast-server; server transitions the row WHERE `claude_agent_id=?` AND `status='running'` to `status="completed"`, `completed_at=now`. | Single-row exact-match update. If no matching row, no-op (200). |
| FR-005 | `PreToolUse` matcher `"Skill"` POSTs `{session_id, skill, invoked_at}` to cast-server; server appends `{name, invoked_at}` to the most-recent-running cast-* row's `skills_used` JSON list. | Append-only; multiple invocations preserved. Payload field is `tool_input.skill` (singular). |
| FR-006 | `agent_runs` gains two new columns: `skills_used TEXT DEFAULT '[]'` and `claude_agent_id TEXT`. New partial index `idx_agent_runs_claude_agent_id ON agent_runs(claude_agent_id) WHERE claude_agent_id IS NOT NULL` for SubagentStop's exact-match closure. The pre-existing composite `idx_agent_runs_session_status (session_id, status)` covers parent-resolution lookups. | No `claude_session_id` column — `session_id` IS the Claude main-loop session id, populated by sibling `user_invocation_service.register()`. |
| FR-007 | Server resolves parent: `SELECT id FROM agent_runs WHERE session_id=? AND status='running' AND agent_name LIKE 'cast-%' ORDER BY started_at DESC LIMIT 1`. NULL if none. | `agent_name LIKE 'cast-%'` excludes non-cast running subagents from being incorrectly chosen as parents. |
| FR-008 | Hook entry points are `cast-hook` console-script subcommands: `cast-hook subagent-start`, `cast-hook subagent-stop`, `cast-hook skill-invoke`. | Mirrors sibling's `cast-hook user-prompt-{start,stop}` pattern. Console-script registration is in `cast-server` pyproject.toml. |
| FR-009 | Install/uninstall is idempotent, atomic (`mkstemp + os.replace`), surgical (substring marker `cast-hook `), and additive (never replaces third-party entries). PreToolUse entries support per-event `matcher` keys (matcher: `"Skill"` for ours; matcher-aware identity check). | Reuses sibling `install_hooks.py`; tuple shape extended to 4-tuple to carry matcher. |
| FR-010 | All hook scripts MUST exit 0 on any failure (server down, network, malformed payload). User prompts are never blocked. `_post()` is fire-and-forget — does NOT block on response body. | HTTP timeout 2s, hook timeout 3s. |
| FR-011 | Runs UI L2 row renders a chip-row when `skills_used` is non-empty: `"N skills: <first 2-3 names> +K"`. L3 expansion renders the full list with timestamps and counts. | Hides entirely when empty (no "0 skills" placeholder). |
| FR-012 | New spec `docs/specs/cast-subagent-and-skill-capture.collab.md` is created via `/cast-update-spec` and registered in `docs/specs/_registry.md`. | Documents the contract for future plans. |
| FR-013 | ~~Sibling user-invocation writer also populates `claude_session_id`.~~ **RESOLVED.** Sibling already populates `agent_runs.session_id` from the `UserPromptSubmit` payload's `session_id` (verified at `cast-server/cast_server/services/user_invocation_service.py:49`). No cross-plan change needed. | Original FR-013 was based on a misread; sibling shipped correctly. |
| FR-014 | The `system-ops` goal is auto-seeded by `_run_migrations()._seed_system_goals()` (`INSERT OR IGNORE`) so sibling and this plan's orphan-fallback inserts never violate the FK. | Already landed 2026-05-01; sp1 retains the idempotency test. |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | 100% of `cast-*` Task() dispatches in a session produce a corresponding `agent_run` row. | Manual: dispatch 5 different cast-* subagents in one session; query `agent_runs` and confirm 5 new rows with matching `agent_name`. |
| SC-002 | Parent attribution correct under parallel and nested dispatch. | Manual: parent dispatches 2 children in parallel + 1 grandchild; verify tree topology in `/runs` matches dispatch order. Automated: API test seeds a session graph and asserts `parent_run_id` correctness. |
| SC-003 | Hook adds <100ms p95 latency to `SubagentStart`/`SubagentStop`/`PreToolUse` events. | Time the hook subprocess on a warm cast-server; report p95 over 50 invocations. |
| SC-004 | Round-trip install + uninstall on a seeded settings.json is byte-equivalent (modulo JSON re-serialization). | `test_round_trip_install_then_uninstall_restores_original` (mirrors sibling plan's coverage). |
| SC-005 | `/runs` page renders skills chips for ≥3 cast-* runs without overflow on a 1280px viewport. | Screenshot UI test — fixture seeds a run with 5 skills, asserts chip-row presence and overflow indicator. |
| SC-006 | Stale-parent guard: a `SubagentStart` arriving in a session where the only cast-* row is `status="completed"` produces an orphan (NULL parent), not a re-attached child. | Unit test in `test_subagent_invocation_service.py::test_register_returns_orphan_when_no_running_cast_row_in_session`. |
| SC-007 | The new spec passes `cast-spec-checker` with zero findings. | `/cast-spec-checker docs/specs/cast-subagent-and-skill-capture.collab.md` clean. |

## Constraints

- **Local single-tenant cast-server.** No concurrent server writers; SQLite is fine.
- **Project-scoped hooks.** Install writes to `<project>/.claude/settings.json`, not `~/.claude/settings.json` (matches sibling plan default).
- **No env-var dependence.** `CLAUDE_SESSION_ID` is unreliable in hook subprocesses (verified via claude-code-guide); use stdin JSON only.
- **No new tools.** Implementation uses Python stdlib + cast-server's existing FastAPI/SQLite stack. No new dependencies.
- **Backward compatible.** Existing `agent_run` rows (without `claude_agent_id` or `skills_used`) MUST keep working. Migration adds columns with defaults (`skills_used DEFAULT '[]'`, `claude_agent_id DEFAULT NULL`); no row rewriting.
- **Hook contract stability.** The hook script accepts whatever Claude Code sends on stdin and never errors on extra fields. Future Claude Code payload additions are forward-compatible.
- **Performance.** Skill capture is high-frequency (every Skill invocation in every cast-* run). The append must not require re-reading the row server-side (use SQLite JSON1 `json_insert` or atomic UPDATE).
- **No transcript ingestion.** `transcript_path` is captured but contents are NOT read or stored. Future work.

## Out of Scope

- **User-typed `/cast-*` slash command capture.** Covered by sibling plan `2026-05-01-capture-user-invocations-as-runs.collab.md` (already shipped). Sibling already populates `agent_runs.session_id` correctly; no cross-plan coupling needed (FR-013 was based on a misread; resolved).
- **Bash invocations of `cast-*` CLI binaries.** Rare and likely a delegation-contract violation. Out of scope for capture; address by enforcing HTTP path in agent design guide.
- **Non-`cast-*` subagent capture** (`Explore`, `Plan`, `general-purpose`, custom user agents). Server-side filter excludes them.
- **Capturing PreToolUse for non-Skill tools** (Bash, Read, Write, etc.). Future work if needed for security audit; out of scope here.
- **Capturing skill arguments.** Privacy/redaction concerns make this v2. Store skill name + invoked_at only.
- **Real-time WebSocket push of skill events to the runs UI.** Polling at L3-expand time is sufficient.
- **Backfill of historical Claude Code sessions** before this feature ships. New sessions only.
- **Multi-machine / multi-host attribution.** Same-machine assumption (matches sibling plan).
- **Output.json synthesis for hook-created rows.** They're tracking artifacts, not delegation outputs. The contract-v2 schema in `cast-output-json-contract.collab.md` is for HTTP-dispatched runs.
- **Detection of subagent cancellation vs completion.** v1: every `SubagentStop` → `status=completed`. Same call as sibling plan made for `Stop`.

## Open Questions

- **[RESOLVED 2026-05-01: claude_session_id column vs reuse session_id field]** —
  Resolved by Spike A. `agent_runs.session_id` is reused as-is — it carries the
  Claude main-loop session id (populated by sibling `user_invocation_service.register()`).
  No `claude_session_id` column added. Instead, a new `claude_agent_id` column
  carries Claude Code's per-subagent runtime id from `SubagentStart.agent_id`.
  Naming `claude_agent_id` (not `agent_id`) avoids collision with
  `cast_server.models.agent_config.AgentConfig.agent_id` (config folder name).

- **[RESOLVED 2026-05-01: skills_used JSON column vs agent_run_skills relational table]** —
  Decision unchanged: JSON column for v1 (`skills_used TEXT DEFAULT '[]'`).
  Promote to relational table only when an aggregate query becomes required.

- **[RESOLVED 2026-05-01: cross-plan coupling with sibling slash-command plan]** —
  Sibling plan shipped (commit `6d73e0b feat(server): capture user-typed /cast-*
  slash commands as agent_run rows`). `user_invocation_service.register()`
  already writes `agent_runs.session_id` correctly. No coupling fix needed.

- **[RESOLVED 2026-05-01: SubagentStop payload exit signaling]** — Resolved by
  Spike A. SubagentStop carries no `error`, `exit_code`, or `failed` field.
  v1 always sets `status="completed"`. `last_assistant_message` is present
  and could feed v2 failure detection.

- **[USER-DEFERRED: skills chip-list overflow + interactivity at L2]** —
  How many chips before the `+N` overflow shows? Should the chip be
  click-through to filter `/runs` by that skill? **Pre-decision:** show first 2
  chips + count, no click-through in v1. Resolver: design pass during the UI
  sub-phase.

- **[USER-DEFERRED: full skill-arguments capture and display]** — Capturing
  arguments would expose user prompts and may include secrets; redaction is its
  own design problem. Punt to v2 with explicit user request.
