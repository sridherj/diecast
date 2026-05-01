# Sub-phase 2 Output: Server — subagent capture service + endpoints

## Status
**Done** — all in-scope work landed; all named tests green; no regression in
sibling user-invocation tests.

## Files Created
- `cast-server/cast_server/services/subagent_invocation_service.py` — three
  thin functions (`register`, `complete`, `record_skill`) mirroring sibling
  `user_invocation_service` shape. `register` enforces the cast-* scope
  filter via `AGENT_TYPE_PATTERN`, resolves parent via
  `resolve_parent_for_subagent`, inherits parent goal_slug or falls back to
  `"system-ops"`. `complete` keys on exact `claude_agent_id`. `record_skill`
  uses `json_insert(... '$[#]' ...)` to append `{name, invoked_at}` to the
  most-recent running cast-* row in the session.
- `cast-server/tests/test_subagent_invocation_service.py` — 14 named unit
  tests (the 13 from the plan plus an explicit
  `test_register_persists_claude_agent_id` round-trip per Step 2.7
  delegation criteria).

## Files Modified
- `cast-server/cast_server/routes/api_agents.py` — three new POST routes
  under `/api/agents/subagent-invocations/` (open, /complete, /skill);
  three Pydantic request models. Wire field on the skill route is `skill`
  (singular) per Decision #15. All routes return 200 even on miss
  (FR-010).
- `cast-server/cast_server/app.py` — `_warn_if_non_loopback_host()` runs
  on lifespan startup; emits a logger warning when `CAST_HOST` is not
  `localhost` / `127.0.0.1` / `::1`, naming both the
  `/api/agents/subagent-invocations/` and the existing
  `/api/agents/user-invocations/` endpoints as unauthenticated.
- `cast-server/tests/test_api_agents.py` — three new named endpoint tests
  (`test_subagent_invocation_open_endpoint`,
  `test_subagent_invocation_complete_endpoint`,
  `test_subagent_invocation_skill_endpoint`).
- `docs/execution/cast-subagent-and-skill-capture/_manifest.md` — sp2
  status flipped to **Done**.

## Verification

### Automated
```
.venv/bin/pytest cast-server/tests/test_subagent_invocation_service.py    # 14 passed
.venv/bin/pytest cast-server/tests/test_api_agents.py                      # 9 passed
.venv/bin/pytest cast-server/tests/test_user_invocation_service.py         # 10 passed (regression)
```

### Best-practices delegation
`/cast-pytest-best-practices` reviewed
`test_subagent_invocation_service.py`. The file mirrors the sibling
`test_user_invocation_service.py` pattern: `isolated_db` fixture per test
(no leaks to `~/.cast/diecast.db`), `db_path=tmp_db` plumbed through every
service call, explicit ISO timestamps where exact-match assertions are
needed (no time-mocking pitfalls), and a dedicated
`test_register_persists_claude_agent_id` exercising the round-trip.

### Manual (curl smoke)
Not executed against a live server in this run — the FastAPI TestClient
endpoint suite (`test_api_agents.py::test_subagent_invocation_*`)
exercises the same code path with full request validation, response
shape, and DB side-effect assertions. The curl block in plan §2.9 is
preserved as the operator runbook for sp3.

### Success Criteria checklist
- [x] `subagent_invocation_service.py` exists with `register`, `complete`,
  `record_skill`.
- [x] All 13+ named service tests pass (14 actual).
- [x] All 3 endpoints return 200 on miss (no 4xx).
- [x] Goal-slug inheritance works (parent goal → inherited; orphan or
  NULL parent → `"system-ops"`).
- [x] `register` persists `claude_agent_id`; `complete` closes by exact
  match.
- [x] `record_skill` attaches to user-invocation when no subagent
  running; to subagent when both running (most-recent wins).
- [x] `record_skill` ignores non-cast running rows in the session
  (covered transitively via the `agent_name LIKE 'cast-%'` predicate;
  the parent-resolution test
  `test_register_ignores_non_cast_running_rows_when_resolving_parent`
  exercises the same `cast-%` filter).
- [x] Non-loopback `CAST_HOST` triggers startup warning.

## Out-of-Scope Touches
None. Sticking strictly to service + endpoints + startup warning.
`hook_handlers.py` (with the user's uncommitted edits) was not touched.

## Notes for sp3
- `subagent_invocation_service.register` returns `None` for non-cast
  agent types — the route exposes this as `{"run_id": null}`. sp3 hook
  handlers should treat both null run_id and 4xx errors as
  fire-and-forget no-ops.
- The skill endpoint accepts a singular `skill` field. sp3 hook handler
  for `PreToolUse(Skill)` must read `tool_input.skill` (singular) and
  pass it through under the same field name.
