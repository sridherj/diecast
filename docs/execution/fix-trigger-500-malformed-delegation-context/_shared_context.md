# Shared Context: Fix Trigger 500 on Malformed `delegation_context`

## Source Documents

- Plan: `docs/plan/2026-05-01-fix-trigger-500-malformed-delegation-context.collab.md`
- Goal: `goals/improved-first-launch/` (slug `improved-first-launch`, title "Fix 500 on trigger for malformed delegation_context")

## Project Background

A parent agent invoking `cast-orchestrate` → `cast-create-execution-plan` via the `cast-child-delegation` skill POSTed a `delegation_context` payload whose `output` block contained `expected_artifacts` but **no `output_dir`**. Because `DelegationOutputConfig.output_dir` is declared required, pydantic raises `ValidationError`. The route handler does not catch it, so FastAPI surfaces a generic **500 Internal Server Error** with no actionable detail for the calling agent.

The fix has two intertwined goals:

1. **Restore the 422 contract** that `cast-child-delegation` and `docs/specs/cast-delegation-contract.collab.md` already promise — a structured, recoverable response — instead of a 500 traceback.
2. **Adopt the documented fallback** (`docs/specs/cast-delegation-contract.collab.md:66`) where omitted `output_dir` defaults to the goal directory. The spec already says this; only the server and the SKILL.md docs are out of step.

The plan deliberately does NOT chase down the upstream caller that produced the bad shape. The server-side fix is the right place because it makes the API self-documenting and aligns server, spec, and skill in one PR.

## Codebase Conventions

- **MVCS layering**: routes (`cast-server/cast_server/routes/`) → services (`cast-server/cast_server/services/`) → models (`cast-server/cast_server/models/`). Routes return `JSONResponse` for structured error payloads; services raise typed exceptions (e.g., `MissingExternalProjectDirError`) that routes translate.
- **422 for caller-fixable shape errors**: the `trigger_agent` route already returns 422 for `MissingExternalProjectDirError` and bare `ValueError`. New shape errors must follow the same convention — never 400, never 500.
- **`setdefault` for delegation defaults at the route boundary**: the route already calls `setdefault("goal_slug", ...)` and `setdefault("parent_run_id", ...)` on `delegation_context_raw` before constructing the pydantic model (see `cast-server/cast_server/routes/api_agents.py:67-68`). New defaults must extend this pattern, not mutate the pydantic model after construction.
- **Test fixture style**: `cast-server/tests/test_dispatch_precondition.py` already provides an `env` fixture (hermetic DB + `GOALS_DIR` monkeypatched into config and routes) plus an `_insert_goal` helper. New tests in this file MUST reuse them — do not invent a parallel fixture.

## Key File Paths

| File | Role | Touched by |
|------|------|-----------|
| `cast-server/cast_server/routes/api_agents.py` | `trigger_agent` route — constructs `DelegationContext`, returns 422 envelopes | sp1a |
| `cast-server/cast_server/models/delegation.py` | `DelegationOutputConfig` pydantic model — `output_dir` required field | sp1a |
| `cast-server/tests/test_dispatch_precondition.py` | Trigger-route precondition tests, structured 422 contract tests | sp1a |
| `cast-server/cast_server/config.py` | `GOALS_DIR` resolution (line 31-32) — referenced by route default | sp1a (read-only) |
| `cast-server/cast_server/services/agent_service.py` | `artifact_dir = output_dir or goal_dir` at line ~1001 — existing fallback | sp1a (read-only, do not modify) |
| `skills/claude-code/cast-child-delegation/SKILL.md` | Parent-facing delegation docs; line 126 documents `output_dir` as required | sp1b |
| `docs/specs/cast-delegation-contract.collab.md` | Spec; line 66 already documents the goal-dir fallback | reference only — not modified |

## Data Schemas & Contracts

### Current `DelegationOutputConfig` (`cast-server/cast_server/models/delegation.py:16-19`)

```python
class DelegationOutputConfig(BaseModel):
    output_dir: str
    expected_artifacts: list[str] = []
    contract_version: str = "1.0"
```

### Target `DelegationOutputConfig` after sp1a

```python
class DelegationOutputConfig(BaseModel):
    output_dir: str = ""             # Empty = "use goal_dir" (server-side fallback at route boundary)
    expected_artifacts: list[str] = []
    contract_version: str = "1.0"
```

### Existing route construction (`cast-server/cast_server/routes/api_agents.py:65-71`)

```python
delegation_context_raw = data.get("delegation_context")
if delegation_context_raw:
    delegation_context_raw.setdefault("goal_slug", goal_slug)
    delegation_context_raw.setdefault("parent_run_id", parent_run_id or "")
    delegation_context = DelegationContext(**delegation_context_raw)
else:
    delegation_context = None
```

### Target route construction after sp1a

```python
from pydantic import ValidationError

delegation_context_raw = data.get("delegation_context")
if delegation_context_raw:
    delegation_context_raw.setdefault("goal_slug", goal_slug)
    delegation_context_raw.setdefault("parent_run_id", parent_run_id or "")
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

### 422 contract callers consume (existing pattern + new error_code)

```json
{
    "error_code": "invalid_delegation_context",
    "detail": "delegation_context failed validation",
    "errors": [ { "loc": [...], "msg": "...", "type": "..." } ],
    "hint": "See docs/specs/cast-delegation-contract.collab.md ..."
}
```

## Pre-Existing Decisions (from plan, 2026-05-01)

1. **Add a SKILL.md edit to the plan** — aligning server + spec + skill in one PR closes the doc drift; spec already documents the fallback at `docs/specs/cast-delegation-contract.collab.md:66`, so the SKILL.md text was the only outlier.
2. **Inject `output_dir` default before construction via `setdefault`** — mirrors the existing `setdefault('goal_slug', ...)` and `setdefault('parent_run_id', ...)` pattern at `routes/api_agents.py:67-68`; avoids post-construction mutation of the pydantic model.
3. **Add a regression test that an explicit `output_dir` is preserved** — the omitted-case test alone wouldn't catch a future refactor that replaces `setdefault` with hard assignment; the regression test is ~10 lines on the existing fixture.

## Relevant Specs

- `docs/specs/cast-delegation-contract.collab.md` — covers `cast-server/cast_server/routes/api_agents.py` and `cast-server/cast_server/models/delegation.py`. Line 66 already documents the goal-dir fallback for omitted `output_dir`. **No spec edit is required**; the server is being brought into compliance with the existing spec text. Sub-phase agents modifying these files MUST read the spec and verify SAV behaviors are preserved (terminal status set, file-canonical naming, 422 envelope shape).

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|-----------|------|-----------|--------|--------------------|
| sp1a_server_fix | Sub-phase | None | None | sp1b_skill_docs |
| sp1b_skill_docs | Sub-phase | None | None | sp1a_server_fix |

Both sub-phases touch disjoint files (server code+tests vs. one Markdown line); they may execute in parallel without conflict.
