# Sub-phase 2: Server — subagent capture service + endpoints

> **Pre-requisite:** Read
> `docs/execution/cast-subagent-and-skill-capture/_shared_context.md` and
> complete sp1 before starting.

## Outcome

Three new HTTP endpoints under `/api/agents/subagent-invocations/` accept hook
payloads, server-side filter to `cast-*` agents via the shared
`AGENT_TYPE_PATTERN`, create rows with correct `parent_run_id` AND inherited
`goal_slug`, transition them on stop, and append skill invocations to whichever
cast-* row (user-invocation OR subagent) is the most-recent running in that
session. Every endpoint exits 200 even on misses (hook scripts must never
block).

## Dependencies

- **Requires completed:** sub-phase 1 (schema column, helpers, sibling
  refactor).
- **Assumed codebase state:** `_cast_name.py` exports `AGENT_TYPE_PATTERN`;
  `_invocation_sources.py` exports `USER_PROMPT`, `SUBAGENT_START`,
  `source_filter_clause()`; `agent_service.resolve_run_by_session_id` exists;
  `agent_runs.skills_used` column exists.

## Estimated effort

1 session.

## Scope

**In scope:**

- New `cast-server/cast_server/services/subagent_invocation_service.py` with
  three functions: `register`, `complete`, `record_skill`.
- Three new HTTP endpoints in `cast-server/cast_server/routes/api_agents.py`
  under `/api/agents/subagent-invocations/`.
- Pydantic request models mirroring `UserInvocationOpenRequest` style.
- Test file `cast-server/tests/test_subagent_invocation_service.py` covering
  every named test in the Verification list.
- Endpoint tests added to `cast-server/tests/test_api_agents.py`.
- Startup warning when `CAST_HOST` is non-loopback (auth gap on hook
  endpoints).

**Out of scope (do NOT do):**

- Hook handlers (sp3).
- `install_hooks.py` matcher support (sp3).
- `_post()` fire-and-forget refactor (sp3).
- UI work (sp4).
- Spec authoring (sp5).
- Modifying sibling `user_invocation_service.py` further (sp1 already
  refactored its `complete()` to use the helper).

## Files to Create/Modify

| File | Action | Notes |
|------|--------|-------|
| `cast-server/cast_server/services/subagent_invocation_service.py` | Create | Three thin functions: `register`, `complete`, `record_skill`. |
| `cast-server/cast_server/routes/api_agents.py` | Modify | Add 3 POST endpoints under `/api/agents/subagent-invocations/`. Add Pydantic models. |
| `cast-server/cast_server/main.py` (or wherever startup runs) | Modify | Startup warning when `CAST_HOST` is non-loopback. |
| `cast-server/tests/test_subagent_invocation_service.py` | Create | 11 named unit tests below. |
| `cast-server/tests/test_api_agents.py` | Modify | Add `test_subagent_invocation_endpoints` covering the 3 routes. |

## Detailed Steps

### Step 2.1: New service `subagent_invocation_service.py`

Parallel naming to `user_invocation_service.py`. Three functions, each thin:

#### `register(...)`

```python
def register(
    agent_type: str,
    session_id: str,
    parent_session_id: str | None,
    transcript_path: str | None = None,
    prompt: str | None = None,
    db_path: str | None = None,
) -> str | None:
    ...
```

Steps:
1. `if not AGENT_TYPE_PATTERN.match(agent_type): return None`.
2. `parent_run_id = resolve_run_by_session_id(parent_session_id, db_path)` if
   `parent_session_id` is non-None, else `None`.
3. **Inherit goal_slug from parent.** If `parent_run_id` is non-None,
   `goal_slug = SELECT goal_slug FROM agent_runs WHERE id = ?`; if SELECT
   returns NULL or no row, `goal_slug = "system-ops"`. If `parent_run_id` is
   None, `goal_slug = "system-ops"`.
4. Call `agent_service.create_agent_run` with:
   - `agent_name=agent_type`
   - `goal_slug=goal_slug`
   - `task_id=None`
   - `session_id=session_id`
   - `status="running"`
   - `input_params={"source": SUBAGENT_START, "prompt": prompt, "transcript_path": transcript_path}`
   - `parent_run_id=parent_run_id`
   - `db_path=db_path`
5. `update_agent_run(run_id, started_at=now)` — mirrors sibling pattern
   (`user_invocation_service.py` line 56).
6. Return `run_id`.

#### `complete(...)`

```python
def complete(session_id: str, db_path: str | None = None) -> int:
    ...
```

UPDATE rows where:
- `session_id=?`
- `status='running'`
- `source_filter_clause()` bound to `SUBAGENT_START`
- `started_at > cutoff` (1-hour staleness window mirroring sibling)

Set `status='completed'` and `completed_at=now`. Return `cur.rowcount`.

Close connection in `try/finally`.

#### `record_skill(...)`

```python
def record_skill(
    session_id: str,
    skill_name: str,
    invoked_at: str | None = None,
    db_path: str | None = None,
) -> int:
    ...
```

**NO source filter** (per Decision #1). Append `{name, invoked_at}` to
whichever cast-* row is the most-recent running in this session:

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
(user-invocation OR subagent), never to an unrelated row that happens to
share the session. The "most-recent" rule means a Task()-dispatched subagent
supersedes its slash-command parent for skill attribution while running, then
skills naturally flow back to the parent after the subagent's `complete()`
flips its status to `completed`.

`invoked_at` defaults to `now_iso()` if absent. Return `cur.rowcount`.

### Step 2.2: HTTP endpoints in `routes/api_agents.py`

Mirror sibling shape (find `UserInvocationOpenRequest` and follow the same
conventions).

```
POST /api/agents/subagent-invocations
  body: {agent_type, session_id, parent_session_id?, transcript_path?, prompt?}
  resp: {"run_id": <uuid> | null}

POST /api/agents/subagent-invocations/complete
  body: {session_id}
  resp: {"closed": <int>}

POST /api/agents/subagent-invocations/skill
  body: {session_id, skill_name, invoked_at?}
  resp: {"appended": <int>}
```

`invoked_at` defaults to `now_iso()` server-side if absent.

**All endpoints return 200 on miss** (hook scripts must exit 0 — FR-010 — and
4xx tempts a future hook author to retry).

### Step 2.3: Pydantic request models

Add to `routes/api_agents.py` mirroring sibling style. Suggested names:
- `SubagentInvocationOpenRequest`
- `SubagentInvocationCompleteRequest`
- `SubagentInvocationSkillRequest`

### Step 2.4: Source-discriminator scope

Now used by `complete()` of each service ONLY (not by `record_skill`). The two
services don't cross-contaminate each other's `complete()` operations:
- Sibling `user_invocation_service.complete()` closes `source = USER_PROMPT`.
- Our `subagent_invocation_service.complete()` closes `source = SUBAGENT_START`.

Constants live in `_invocation_sources.py` from sp1.

### Step 2.5: Non-loopback CAST_HOST startup warning

In the cast-server startup (e.g., `main.py` or wherever `CAST_HOST` is read),
emit a warning when `CAST_HOST` is non-loopback:

```
WARNING: CAST_HOST is bound to <host>; hook endpoints under
/api/agents/subagent-invocations/ and /api/agents/user-invocations/ are
unauthenticated. Do not expose cast-server publicly.
```

Document this in the spec (sp5).

### Step 2.6: Tests

Create `cast-server/tests/test_subagent_invocation_service.py` with the
following named tests (each MUST exist as a named test, not folded into a
parametric):

```python
def test_register_creates_running_row_for_cast_agent(tmp_db)
def test_register_returns_null_for_non_cast_agent_type(tmp_db)
def test_register_resolves_parent_via_session_id(tmp_db)
def test_register_falls_back_to_orphan_when_parent_session_stale(tmp_db)
def test_subagent_register_inherits_parent_goal_slug(tmp_db)
def test_subagent_register_falls_back_to_system_ops_when_orphan(tmp_db)
def test_complete_closes_only_subagent_rows_in_same_session(tmp_db)
def test_complete_leaves_user_invocation_rows_alone(tmp_db)
def test_record_skill_attaches_to_user_invocation_when_no_subagent_running(tmp_db)
def test_record_skill_attaches_to_subagent_when_both_running(tmp_db)  # most-recent wins
def test_record_skill_appends_in_invocation_order(tmp_db)
```

In `cast-server/tests/test_api_agents.py`, add:

```python
def test_subagent_invocation_endpoints(client)
```

— covers all 3 routes returning 200 + correct JSON shape, including the
`agent_type=Explore` (non-cast) case returning `{"run_id": null}` and creating
no row.

### Step 2.7: Best-practices delegation

→ Delegate: `/cast-pytest-best-practices` over
`test_subagent_invocation_service.py`. Verify:
- in-memory DB per test (mirror sibling fixtures),
- no time-mocking pitfalls in staleness tests,
- no leaking writes to `~/.cast/diecast.db`.

### Step 2.8: Run the test suite

```bash
cd cast-server && uv run pytest \
  tests/test_subagent_invocation_service.py \
  tests/test_api_agents.py \
  -v
```

All listed tests must pass.

### Step 2.9: Curl smoke

With cast-server running on `CAST_PORT=8005`:

```bash
# cast-* agent → returns run_id
curl -sX POST localhost:8005/api/agents/subagent-invocations \
  -H 'Content-Type: application/json' \
  -d '{"agent_type":"cast-foo","session_id":"S1","parent_session_id":null}'
# → {"run_id": "<uuid>"}

# Second call with parent_session_id=S1 → child whose parent_run_id matches
curl -sX POST localhost:8005/api/agents/subagent-invocations \
  -H 'Content-Type: application/json' \
  -d '{"agent_type":"cast-bar","session_id":"S2","parent_session_id":"S1"}'
# → {"run_id": "<uuid>"}    (parent_run_id resolves to first call)

# Non-cast agent → returns null, creates no row
curl -sX POST localhost:8005/api/agents/subagent-invocations \
  -H 'Content-Type: application/json' \
  -d '{"agent_type":"Explore","session_id":"S3","parent_session_id":null}'
# → {"run_id": null}
```

## Verification

### Automated Tests (permanent)

- `pytest cast-server/tests/test_subagent_invocation_service.py` — all 11
  named tests green (see Step 2.6).
- `pytest cast-server/tests/test_api_agents.py::test_subagent_invocation_endpoints`
  green: 3 endpoints return 200 + correct JSON shape.

### Manual Checks

- Curl smoke (Step 2.9) returns expected JSON for each case.
- Sibling user-invocation `complete()` does NOT touch our subagent rows; our
  `complete()` does NOT touch user-invocation rows.

### Success Criteria

- [ ] `subagent_invocation_service.py` exists with `register`, `complete`,
      `record_skill`.
- [ ] All 11 named service tests pass.
- [ ] All 3 endpoints return 200 on miss (no 4xx).
- [ ] Goal-slug inheritance works (parent goal → inherited; orphan →
      `"system-ops"`).
- [ ] `record_skill` attaches to user-invocation when no subagent running;
      to subagent when both running (most-recent wins).
- [ ] Source discriminators prevent cross-contamination between sibling and
      our `complete()`.
- [ ] Non-loopback `CAST_HOST` triggers startup warning.

## Design Review

- **Architecture:** service → route mirrors sibling layering exactly. ✓
- **Naming:** `subagent_invocation_service` reads as the subagent counterpart
  to `user_invocation_service`. ✓
- **Concurrency:** `record_skill` uses SQLite `json_insert(... '$[#]' ...)` —
  single UPDATE statement, no read-modify-write. SQLite 3.9+ is enforced at
  startup (sp1) so no fallback path exists. ✓
- **Error & rescue:** every endpoint's "no matching row" returns 200 with
  `{run_id: null}` or `{closed: 0}` or `{appended: 0}` rather than 404 — hook
  scripts MUST exit 0 (FR-010), and 4xx tempts a future hook author to retry.
- **Spec consistency:** terminal status is `completed | partial | failed` per
  `cast-delegation-contract`. We use `completed` only on `SubagentStop`; never
  `partial`. ✓
- **Security:** hook endpoints have NO auth. cast-server binds 127.0.0.1 by
  default but `CAST_HOST` is configurable. Add a startup warning when
  CAST_HOST is non-loopback ("hook endpoints are unauthenticated; do not
  expose cast-server publicly"). Document in spec (sp5).
- **Skill-attribution rule (Decision #1):** the most-recent running cast-* row
  in a session wins. Test the dual-running case explicitly so the rule is
  contract, not coincidence.

## Execution Notes

- **Spec-linked files:** none yet — sp5 authors the new spec.
- **Live-DB caution:** all tests use in-memory or tmp DBs. Verify the
  `db_path` plumbing reaches every UPDATE/SELECT.
- **Sibling regression risk:** sp1's refactor of sibling `complete()` to use
  `source_filter_clause()` + `USER_PROMPT` should already be tested — re-run
  sibling tests as part of sp2 verification:

  ```bash
  cd cast-server && uv run pytest tests/test_user_invocation_service.py -v
  ```
- **`json_insert` semantics:** `'$[#]'` appends to a JSON array. Requires
  SQLite 3.9+ (enforced at startup in sp1). The existing column default
  `'[]'` ensures the array is never NULL — no need to `COALESCE`.
- **Most-recent disambiguation under parallel siblings (Open Question O5):**
  rely on `parent_session_id` from `SubagentStart` payload (validated in sp1
  Spike A) to route to the immediate parent. If Spike A revealed the
  payload uses the root's session_id instead, escalate to user before
  continuing.
