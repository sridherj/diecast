# Sub-phase 2: User-Invocation API Endpoints + Tests

> **Pre-requisite:** Read `docs/execution/capture-user-invocations-as-runs/_shared_context.md` before starting.

## Objective

Add two thin HTTP endpoints under `/api/agents/user-invocations/` to `routes/api_agents.py`:
`POST /` (open) and `POST /complete` (close). All logic delegates to
`user_invocation_service` from sp1. Author 6 endpoint tests covering happy path, optional
session_id, and the safety property that subprocess-dispatched rows are never closed.

## Dependencies

- **Requires completed:** sp1 (the service must exist).
- **Assumed codebase state:** `services/user_invocation_service.py` exposes `register` and
  `complete`. The existing FastAPI router pattern in `routes/api_agents.py` is in use.

## Scope

**In scope:**
- Two pydantic request models: `UserInvocationOpenRequest`, `UserInvocationCompleteRequest`.
- Two endpoints in `routes/api_agents.py`.
- 6 new tests in `cast-server/tests/test_api_agents.py`.

**Out of scope (do NOT do these):**
- Changes to `agent_service.py`.
- Hook-side regex / prompt parsing — server is **agnostic** to the prefix (Decision #13).
- DB index — that's sp3.
- Auth / rate limiting — out of scope for this plan entirely.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/routes/api_agents.py` | Modify | Has trigger endpoint at line 55; add ~30 lines |
| `cast-server/tests/test_api_agents.py` | Modify | Existing tests; append 6 new |

## Detailed Steps

### Step 2.1: Read existing router conventions

```bash
grep -n "router\|@router\|APIRouter\|prefix=" cast-server/cast_server/routes/api_agents.py | head -20
```

Confirm the router prefix (likely `/api/agents`). The new endpoints append:
- `POST /user-invocations`
- `POST /user-invocations/complete`

Examine an existing endpoint (e.g., the trigger handler at `:55`) to match the project's
import order, response shape, and error-handling conventions.

### Step 2.2: Add pydantic models

Append near other models in `routes/api_agents.py` (or wherever models live in this file):

```python
class UserInvocationOpenRequest(BaseModel):
    agent_name: str
    prompt: str
    session_id: str | None = None

class UserInvocationCompleteRequest(BaseModel):
    session_id: str | None = None
```

### Step 2.3: Add endpoint handlers

```python
@router.post("/user-invocations")
async def open_user_invocation(req: UserInvocationOpenRequest):
    run_id = user_invocation_service.register(
        agent_name=req.agent_name,
        prompt=req.prompt,
        session_id=req.session_id,
    )
    return {"run_id": run_id}

@router.post("/user-invocations/complete")
async def complete_user_invocation(req: UserInvocationCompleteRequest):
    closed = user_invocation_service.complete(req.session_id)
    return {"closed": closed}
```

Add the import at the top:

```python
from cast_server.services import user_invocation_service
```

(Match the existing import style — if other services are imported with `from
cast_server.services.foo import bar`, follow suit.)

### Step 2.4: Author the endpoint tests

Append to `cast-server/tests/test_api_agents.py`:

```python
def test_open_user_invocation_returns_run_id(client)
def test_open_user_invocation_creates_running_row(client, db)
def test_open_user_invocation_session_id_optional(client, db)
def test_complete_user_invocation_returns_closed_count(client, db)
def test_complete_with_no_session_id_returns_zero(client, db)
def test_complete_does_not_close_subprocess_rows(client, db)
```

Reuse the `client` and DB fixture from existing `test_api_agents.py` tests. Each test:

- `test_open_user_invocation_returns_run_id`: POST a valid body; assert HTTP 200 and the
  response contains a non-empty `run_id`.
- `test_open_user_invocation_creates_running_row`: POST then read the row back via the DB
  fixture; assert `agent_name`, `status="running"`, `input_params.source="user-prompt"`,
  `parent_run_id=None`.
- `test_open_user_invocation_session_id_optional`: POST without `session_id`; assert 200
  and the row's `session_id` is null/empty (whatever the existing model contract is).
- `test_complete_user_invocation_returns_closed_count`: register, then POST `/complete`;
  assert `{"closed": 1}` and the row is `completed`.
- `test_complete_with_no_session_id_returns_zero`: POST `/complete` with empty body or
  `session_id=null`; assert `{"closed": 0}` (this is **not** an error per the contract).
- `test_complete_does_not_close_subprocess_rows`: insert a `running` row with the same
  session_id but `input_params.source != 'user-prompt'`; POST `/complete`; assert the
  subprocess row remains `running`. **This is the key safety test.**

### Step 2.5: Run the suite

```bash
cd cast-server && uv run pytest tests/test_api_agents.py -v -k "user_invocation"
```

All 6 new tests must pass; existing tests must continue to pass.

## Verification

### Automated Tests (permanent)

`cast-server/tests/test_api_agents.py` — 6 new tests as enumerated.

### Validation Scripts (temporary)

Spin up the dev server and exercise the endpoints:

```bash
# In one terminal:
bin/cast-server   # default :8005

# In another:
curl -X POST http://127.0.0.1:8005/api/agents/user-invocations \
  -H "Content-Type: application/json" \
  -d '{"agent_name":"cast-plan-review","prompt":"/cast-plan-review test","session_id":"S1"}'
# Expect: {"run_id":"<uuid>"}

curl -X POST http://127.0.0.1:8005/api/agents/user-invocations/complete \
  -H "Content-Type: application/json" \
  -d '{"session_id":"S1"}'
# Expect: {"closed":1}

# Idempotency: a second POST should return {"closed":0}
curl -X POST http://127.0.0.1:8005/api/agents/user-invocations/complete \
  -H "Content-Type: application/json" \
  -d '{"session_id":"S1"}'
# Expect: {"closed":0}
```

Inspect the row in `agent_runs.db` (path from existing project conventions) and confirm
shape.

### Manual Checks

```bash
git diff cast-server/cast_server/services/agent_service.py
# Must show zero changes (Decision #11 + #3).

git status cast-server/cast_server/routes/ cast-server/tests/
# Should show only api_agents.py and test_api_agents.py modified.
```

### Success Criteria

- [ ] Two pydantic models defined exactly as in plan.
- [ ] Both endpoints added under `/user-invocations`.
- [ ] Endpoints are thin: each is one call into `user_invocation_service`.
- [ ] No business logic in routes — just request → service → response.
- [ ] All 6 new tests pass.
- [ ] Existing tests in `test_api_agents.py` still pass.
- [ ] `agent_service.py` shows zero git diff.
- [ ] curl smoke against `bin/cast-server` round-trips correctly.

## Execution Notes

- **Decision #13 is critical:** the server is agnostic to the `/cast-` prefix. Do not add
  any regex validation server-side. Any non-empty `agent_name` is acceptable; the hook
  handler is responsible for filtering.
- The `/complete` endpoint with missing `session_id` returns `{"closed": 0}`, **not** an
  HTTP error. Don't reject the request.
- Watch the existing `test_api_agents.py` for fixture patterns. If it uses a `client`
  fixture from FastAPI's `TestClient` and a `db` fixture — reuse, don't reinvent.
- **Spec-linked files:** None yet. Specs are authored in sp7.
- This sub-phase can run in parallel with sp3 and sp4 once sp1 lands. The test runs are
  sensitive to having the index in place only for performance, not correctness.
