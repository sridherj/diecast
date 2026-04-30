# Fix 500 on `/api/agents/{name}/trigger` for malformed `delegation_context`

## Context

Server log shows:

```
POST /api/agents/cast-create-execution-plan/trigger HTTP/1.1 500 Internal Server Error
...
File ".../routes/api_agents.py", line 69, in trigger_agent
    delegation_context = DelegationContext(**delegation_context_raw)
pydantic ValidationError: output.output_dir Field required
input_value={'expected_artifacts': ['..., '_shared_context.md']}
```

A caller (a parent agent invoking `cast-orchestrate` → `cast-create-execution-plan` via the `cast-child-delegation` skill) POSTed a payload whose `delegation_context.output` block had `expected_artifacts` but **no `output_dir`**. `DelegationOutputConfig.output_dir` is declared required, so pydantic raises `ValidationError`. The route handler does not catch it, so FastAPI surfaces a generic **500 Internal Server Error**.

Two problems compound:

1. **Wrong status code & no actionable message.** The skill (`cast-child-delegation`) and the contract spec both expect a structured **422** with a `detail` so a child-delegation parent can recover. A 500 stack-trace is opaque to the parent agent and no recovery path is documented.
2. **Caller resilience.** Several places in the docs say `output.output_dir` is required, but a sensible default exists: when omitted, it should resolve to the goal directory (parent's `goal_dir` for the slug). That matches the spec lines such as `cast-delegation-contract.collab.md:66` ("If unset, parent's own `goal_dir` is used.") and the existing service code around `agent_service.py:1001` that already does `artifact_dir = output_dir or goal_dir`.

## Recommended fix (minimal, resilient)

Three changes in the repo:

### 1. Catch pydantic `ValidationError` at the route boundary → 422

`cast-server/cast_server/routes/api_agents.py` around lines 65–71:

```python
from pydantic import ValidationError

delegation_context_raw = data.get("delegation_context")
if delegation_context_raw:
    delegation_context_raw.setdefault("goal_slug", goal_slug)
    delegation_context_raw.setdefault("parent_run_id", parent_run_id or "")
    # Inject default output_dir BEFORE construction (mirrors the goal_slug /
    # parent_run_id setdefault pattern above; keeps the model immutable
    # post-construction).
    output_block = delegation_context_raw.setdefault("output", {})
    output_block.setdefault("output_dir", str(_config.GOALS_DIR / goal_slug))

    try:
        delegation_context = DelegationContext(**delegation_context_raw)
    except ValidationError as e:
        return JSONResponse(
            status_code=422,
            content={
                "error_code": "invalid_delegation_context",
                "detail": "delegation_context failed validation",
                "errors": e.errors(include_url=False),
                "hint": (
                    "See docs/specs/cast-delegation-contract.collab.md and "
                    "skills/claude-code/cast-child-delegation/SKILL.md for the "
                    "expected shape."
                ),
            },
        )
else:
    delegation_context = None
```

Why 422 (not 400): the existing `MissingExternalProjectDirError` and `ValueError` handlers in this same function already use 422 for caller-fixable shape errors. Stay consistent.

Why **inject before construction** (Issue #2 decision): mirrors the existing `setdefault` pattern at lines 67–68 for `goal_slug` and `parent_run_id`. Avoids mutating the pydantic model after build, keeps all defaulting in one place, and eliminates a code-smell pattern.

### 2. Make `output_dir` default to the goal directory when omitted

`cast-server/cast_server/models/delegation.py`:

```python
class DelegationOutputConfig(BaseModel):
    output_dir: str = ""             # was: required. Empty = "use goal_dir".
    expected_artifacts: list[str] = []
    contract_version: str = "1.0"
```

Combined with the route-layer `setdefault` above, the practical effect is:

- Caller sends explicit `output_dir`  → that value is preserved untouched.
- Caller sends `output: {}` or omits `output_dir` → server backfills `str(GOALS_DIR / goal_slug)`.
- Caller sends garbage `output: {output_dir: 123}` → pydantic raises, route returns 422.

This matches the spec's stated fallback ("If unset, parent's own `goal_dir` is used", `docs/specs/cast-delegation-contract.collab.md:66`) and the existing `output_dir or goal_dir` pattern at `services/agent_service.py:1001`.

### 3. Update `cast-child-delegation` SKILL.md so docs match server behavior

`skills/claude-code/cast-child-delegation/SKILL.md` line 126 currently reads:

> `delegation_context.output.output_dir` (string): Directory where child should write artifacts (typically `{output_dir}` from your preamble).

Reword to flag it as optional and reference the fallback, so parent-facing docs, the contract spec, and the server are in agreement (closes the doc-drift flagged in Issue #1):

> `delegation_context.output.output_dir` (string, **optional**): Directory where child should write artifacts. Defaults to the goal directory (`<goals>/<goal_slug>`) when omitted — see `docs/specs/cast-delegation-contract.collab.md:66`. Pass `{output_dir}` from your preamble explicitly when you need a non-default location (e.g., a sub-phase under `docs/execution/<project>`).

### Files touched

- `cast-server/cast_server/routes/api_agents.py` — wrap pydantic construction; inject `output_dir` default before build.
- `cast-server/cast_server/models/delegation.py` — `output_dir: str = ""`.
- `skills/claude-code/cast-child-delegation/SKILL.md` — reword line 126 to mark `output_dir` optional with the fallback.

### Files NOT changed (explicit non-goals)

- `agents/cast-orchestrate/cast-orchestrate.md` — no curl examples to fix; it points at the skill.
- `docs/specs/cast-delegation-contract.collab.md` — fallback already documented at line 66; no spec drift.

## Verification

1. **Unit tests in `cast-server/tests/test_dispatch_precondition.py`** (extends existing `env` fixture + `_insert_goal` helper):
   - **a) Omitted `output_dir` is defaulted.** POST with `delegation_context.output = {"expected_artifacts": ["x.md"]}` against a goal whose `external_project_dir` exists → assert 200 AND that `goal_dir/.delegation-<run_id>.json` contains `output.output_dir == str(GOALS_DIR / slug)`.
   - **b) Malformed payload returns 422.** POST with `delegation_context = {"agent_name": "x"}` (missing `instructions`/`context`) → assert 422, `error_code == "invalid_delegation_context"`, and `errors` is non-empty.
   - **c) Explicit `output_dir` is preserved (regression for Issue #3).** POST with `delegation_context.output = {"output_dir": "/some/explicit/path", "expected_artifacts": ["x.md"]}` → assert 200 AND that `.delegation-<run_id>.json` contains `output.output_dir == "/some/explicit/path"` (NOT the default). Locks down the `setdefault` semantics so a future refactor can't silently clobber caller-supplied values.
2. **Manual reproduction.** Replay the failing curl with the original payload (no `output_dir`) and confirm 200 + a delegation file is written. Tail the server log for absence of a 500 traceback.
3. **Existing tests.** Run `pytest cast-server/tests/test_dispatch_precondition.py` to confirm no regression on the existing precondition contract.

## Out of scope / open question

I am NOT also fixing the upstream caller (whoever sent the malformed body). The three changes above make the server resilient, self-documenting, and aligned across server + spec + skill — which is the right place to fix this. If you want me to also chase down which parent prompt produced the bad shape, say so and I'll grep `agents/` for callers that hand-build delegation JSON without `output_dir`.

## Decisions

- **2026-05-01T00:00:00Z — How should the plan handle the SKILL.md / server contract drift on `output_dir`?** — Decision: A — Add a SKILL.md edit to the plan. Rationale: aligning server + spec + skill in one PR closes the drift; spec already documents the fallback at `cast-delegation-contract.collab.md:66`, so the SKILL.md text was the only outlier.
- **2026-05-01T00:00:00Z — Where should the `output_dir` default be applied?** — Decision: A — Inject before construction via `setdefault`. Rationale: mirrors the existing `setdefault('goal_slug', ...)` and `setdefault('parent_run_id', ...)` pattern at `routes/api_agents.py:67–68`; avoids post-construction mutation of the pydantic model.
- **2026-05-01T00:00:00Z — Should the plan add a regression test that an explicit `output_dir` is preserved?** — Decision: A — Add the third test. Rationale: the omitted-case test alone wouldn't catch a future refactor that replaces `setdefault` with hard assignment; the regression test is ~10 lines on the existing fixture.
