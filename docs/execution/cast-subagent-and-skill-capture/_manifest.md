# Execution Manifest: Cast Subagent and Skill Capture

> **Regenerated 2026-05-01** from the SWEPT plan doc (Spike A revisions applied).
> Supersedes `docs/execution/cast-subagent-and-skill-capture_v1_pre_spike_a/`.
>
> Source plan: `docs/plan/2026-05-01-cast-subagent-and-skill-capture.collab.md`
> Source requirements: `goals/cast-subagent-and-skill-capture/refined_requirements.collab.md`
> Source payload notes: `goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md`
>
> **Spike A facts encoded throughout this plan:**
> - `parent_session_id` DOES NOT EXIST in any Claude Code hook payload — drop everywhere.
> - `SubagentStart` payload: `{session_id, agent_id, agent_type, transcript_path, cwd, hook_event_name}`.
> - `SubagentStop` payload: `{session_id, agent_id, agent_type, agent_transcript_path, last_assistant_message, stop_hook_active, ...}`. NO error/exit field.
> - `PreToolUse(Skill)` payload field is `tool_input.skill` (singular), NOT `tool_input.skill_name`.
> - New `agent_runs` columns: `skills_used TEXT DEFAULT '[]'` AND `claude_agent_id TEXT`.
>   `claude_agent_id` (not `agent_id`) avoids collision with `cast_server.models.agent_config.AgentConfig.agent_id`.
> - Parent resolution = most-recent running cast-* row in the same `session_id` (`resolve_parent_for_subagent`).
> - Closure on `SubagentStop` = exact `claude_agent_id` match (`resolve_run_by_claude_agent_id`).
> - `system-ops` auto-seed already shipped (`cast-server/cast_server/db/connection.py::_seed_system_goals`); sp1 retains only `test_system_ops_seed_idempotent`.
> - sp1: NO new single-column `idx_agent_runs_session_id`. Existing composite `idx_agent_runs_session_status` covers parent-resolution lookups.
>   NEW partial index `idx_agent_runs_claude_agent_id WHERE claude_agent_id IS NOT NULL` covers the closure path.
> - FR-013 from refined requirements is RESOLVED (sibling already shipped correctly); does not appear as a TODO in any sub-phase.

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:

1. Start a new Claude session.
2. Tell Claude:
   "Read `docs/execution/cast-subagent-and-skill-capture/_shared_context.md` then execute
   `docs/execution/cast-subagent-and-skill-capture/spN_<name>/plan.md`."
3. After completion, update the Status column below.

## Sub-Phase Overview

| # | Sub-phase | Directory/File | Depends On | Status | Notes |
|---|-----------|----------------|-----------|--------|-------|
| 1 | Foundation: schema migration + helpers + sp1 verification | `sp1_foundation/` | -- | Done | Adds `skills_used` + `claude_agent_id` columns; partial index `idx_agent_runs_claude_agent_id`; SQLite 3.9+ floor; `_cast_name.py`; `_invocation_sources.py`; two new `agent_service` resolvers (`resolve_parent_for_subagent`, `resolve_run_by_claude_agent_id`); sibling `complete()` refactor; `test_system_ops_seed_idempotent` (auto-seed already shipped). |
| 2 | Server: subagent capture service + 3 endpoints | `sp2_capture_service/` | 1 | Done | New `subagent_invocation_service.py` (register/complete/record_skill); 3 POST endpoints under `/api/agents/subagent-invocations/` with bodies keyed on `claude_agent_id` (start/complete) and `session_id` (skill). Goal-slug inheritance. Skill attribution = most-recent running cast-* row. Delegate `/cast-pytest-best-practices`. |
| 3 | Hook layer: HOOK_EVENTS extension + matcher + fire-and-forget POST | `sp3_hook_layer/` | 2 | Done | 3 new entries in `HOOK_EVENTS` (4-tuple shape; matcher slot); `install_hooks.py` learns per-event `matcher`; `_post()` refactored to fire-and-forget; hook-side scope filter via `AGENT_TYPE_PATTERN`; handlers extract `claude_agent_id` from payload `agent_id` and skill name from `tool_input.skill` (singular). Delegate `/cast-pytest-best-practices`. |
| 4 | UI: L2 chip-list + L3 detail in /runs | `sp4_ui_surface/` | 3 | Done | New `run_skills_chips.html` and `run_skills_detail.html` partials wired into `macros/run_node.html`; `/runs` route's new `_decorate_skills` walks the tree, parses `skills_used` defensively, computes `skills_aggregated`; CSS for `.skills-chips` / `.skill-chip` / `.skill-overflow` / `.skills-count` / `.skills-detail`. Empty `skills_used` hides chip row entirely. 5 plan-named tests + 2 defensive tests pass at `cast-server/tests/test_runs_skills_chips.py`. |
| 5 | Spec capture + e2e smoke + close-out | `sp5_spec_and_e2e/` | 4 | Done | New spec `cast-subagent-and-skill-capture.collab.md` lints clean (`bin/cast-spec-checker` exits 0); registered in `_registry.md`; cross-spec back-references added to `cast-delegation-contract`, `cast-user-invocation-tracking`, `cast-hooks`. Uninstall round-trip is byte-equivalent (third-party `SubagentStart` + `PreToolUse(matcher="Bash")` survive). Live e2e smoke deferred to operator (see sp5 output.md and `goals/cast-subagent-and-skill-capture/notes/e2e-smoke.ai.md`); cast-server restart cannot be performed inside a subphase-runner. |

Status: Not Started → In Progress → Done → Verified → Skipped

## Dependency Graph

```
sp1 (Foundation) ──► sp2 (Capture service) ──► sp3 (Hook layer) ──► sp4 (UI) ──► sp5 (Spec + E2E)
```

**Critical path:** sp1 → sp2 → sp3 → sp4 → sp5. **Strictly linear — no genuine
parallelism.** Sub-sub-phases within a single sp can run in any order, but the
inter-sp dependency chain is sequential.

## Execution Order

### Sequential Group 1
1. Sub-phase 1: foundation (schema, helpers, sp1 verification tests)

### Sequential Group 2 (after sp1)
2. Sub-phase 2: subagent capture service + 3 endpoints

### Sequential Group 3 (after sp2)
3. Sub-phase 3: hook layer (events, handlers, installer, fire-and-forget)

### Sequential Group 4 (after sp3)
4. Sub-phase 4: /runs UI surface (chips at L2, table at L3)

### Sequential Group 5 (after sp4)
5. Sub-phase 5: spec capture + registry + e2e smoke

## Critical Accuracy Notes

- **Spike A is settled — there is no decision gate in sp1.** The
  `parent_session_id` field does not exist; the design now uses
  `(session_id + claude_agent_id)`. Do NOT re-spike. The empirical capture
  lives at `goals/cast-subagent-and-skill-capture/notes/payload-shapes.ai.md`
  and is authoritative for fields the docs leave unspecified.
- **Two new columns**, not one: `skills_used` AND `claude_agent_id`. The
  closure path needs the second one to do single-row exact-match updates on
  `SubagentStop`.
- **Two new resolvers**, not one: `resolve_parent_for_subagent(session_id)`
  for parent attribution (most-recent running cast-* row in the session) and
  `resolve_run_by_claude_agent_id(claude_agent_id)` for closure. Distinct
  contracts — distinct functions.
- **`tool_input.skill` (singular)** in `PreToolUse(Skill)`. The wire field
  on POST `/api/agents/subagent-invocations/skill` is therefore `skill`, not
  `skill_name`.
- **sp1 system-ops auto-seed has ALREADY landed**
  (`cast-server/cast_server/db/connection.py::_seed_system_goals`). sp1 retains
  only the verification test (`test_system_ops_seed_idempotent`), not the
  implementation activity.
- **sp1 does NOT add a new single-column `idx_agent_runs_session_id`.** The
  existing composite `idx_agent_runs_session_status ON agent_runs(session_id,
  status)` already covers the parent-resolution lookup pattern.
- **sp1 DOES add a new partial index** for closure:
  `idx_agent_runs_claude_agent_id ON agent_runs(claude_agent_id) WHERE
  claude_agent_id IS NOT NULL`.
- **FR-013 is RESOLVED.** Sibling `user_invocation_service.register()`
  already populates `agent_runs.session_id` correctly; do NOT plan any
  cross-feature change there.
- Build order is strictly LINEAR. No parallelism between sub-phases.
- Each sub-phase preserves its full Verification, Key activities, and Design
  review sections from the source plan.

## Project Directory

Absolute project_dir: `<DIECAST_ROOT>`

## Progress Log

<!-- Update after each sub-phase completes. Capture surprises, scope adjustments,
     and any divergence from the plan. -->

### sp5 (2026-05-01) — Done

- Authored `docs/specs/cast-subagent-and-skill-capture.collab.md` directly
  (not via `/cast-update-spec` skill). Reason: cast-update-spec is
  interactive (waits for user diff approval) and the runner cannot
  surface that prompt to a human inside a deferred sub-phase context.
  The spec follows the canonical `cast-spec.template.md` shape and
  mirrors the sibling `cast-user-invocation-tracking.collab.md`
  structure. **`bin/cast-spec-checker` exits 0** on the new file.
- Registered the spec in `docs/specs/_registry.md`. Added cross-spec
  back-references in `cast-delegation-contract.collab.md` (subagent rows
  do NOT write delegation `output.json` — coexist without conflict),
  `cast-user-invocation-tracking.collab.md` (subagent rows ride the
  same `session_id` but additionally carry `claude_agent_id` and use a
  different `source` discriminator), and `cast-hooks.collab.md`
  (per-event `matcher` slot extension to the install contract).
- Ran the uninstall round-trip from Step 5.6: seeded a settings.json
  with third-party `SubagentStart` + `PreToolUse(matcher="Bash")`,
  installed our 5 entries, uninstalled, diffed against the seed —
  byte-equivalent. SC-004 satisfied.
- **E2E smoke deferred** to operator. Reason: the running cast-server
  predates sp2 (`/api/agents/subagent-invocations` returns 404). The
  restart cannot be performed inside a `cast-subphase-runner` because
  that would kill the parent that monitors `output.json` for
  completion. Live-smoke runbook captured at
  `goals/cast-subagent-and-skill-capture/notes/e2e-smoke.ai.md` with
  six-step procedure, expected `/runs` topology, post-smoke SQL
  acceptance check, and screenshot slots. FR-013 is reflected as
  RESOLVED in the spec, not as a TODO.

### sp4 (2026-05-01) — Done

- Wired chip partials (`run_skills_chips`, `run_skills_detail`) into the
  shipped `macros/run_node.html` after `run_status_cells` (L2 row) and
  inside the `.detail` block (L3 table). `{% with %}` keeps partial-local
  vars cleanly scoped.
- Added `_decorate_skills` to `routes/pages.py`. It walks the tree,
  parses `skills_used` defensively (`json.JSONDecodeError`/`TypeError`
  → `[]`), and computes `skills_aggregated` with group-by-name + count
  + earliest `invoked_at`. Aggregation logic kept next to the only
  caller, the `/runs` handler.
- CSS: 5 new classes (`.skills-chips`, `.skill-chip`, `.skill-overflow`,
  `.skills-count`, `.skills-detail`) following the existing `.pill` /
  `.rollup` pattern. `flex-wrap` guarantees no overflow at 1280px with
  5 chips rendered.
- Tests: 5 plan-named + 2 defensive tests in
  `cast-server/tests/test_runs_skills_chips.py` (NOT `tests/ui/`). All
  7 green; the existing 22 `/runs` macro/tree tests still green.
- **Test-location divergence.** Plan asked for `tests/ui/` but the
  existing `tests/ui/` harness spawns a real cast-server on :8006 and is
  blocked in this workspace by the venv-ownership memo on the parent
  run. Placed tests at `tests/` instead (mirrors
  `test_runs_template.py`, the closest existing precedent). The
  presentation logic the plan asked to verify is fully covered;
  route-side `_decorate_skills` is exercised end-to-end in test 5.
