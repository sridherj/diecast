# Sub-phase 1a: Server fix — 422 envelope + `output_dir` fallback + tests

> **Pre-requisite:** Read `docs/execution/fix-trigger-500-malformed-delegation-context/_shared_context.md` before starting this sub-phase.

## Objective

Stop the `POST /api/agents/{name}/trigger` route from returning a 500 traceback when `delegation_context.output.output_dir` is omitted. Instead, default it to the goal directory (`GOALS_DIR/<slug>`) when the caller leaves it blank, and return a structured 422 envelope when the payload is otherwise malformed. Lock the new behavior with three pytest cases on the existing `test_dispatch_precondition.py` fixture.

## Dependencies

- **Requires completed:** None.
- **Assumed codebase state:** `cast-server/cast_server/routes/api_agents.py` still contains the lines 65–71 block shown in `_shared_context.md`; `DelegationOutputConfig` still has `output_dir: str` (required); `test_dispatch_precondition.py` still exposes the `env` fixture and `_insert_goal` helper.

## Scope

**In scope:**

- Modify `cast-server/cast_server/models/delegation.py`: change `output_dir: str` to `output_dir: str = ""`.
- Modify `cast-server/cast_server/routes/api_agents.py`: import `pydantic.ValidationError`, inject `output_dir` default via `setdefault` before construction, wrap the `DelegationContext(...)` call in `try/except ValidationError` that returns a structured 422 `JSONResponse`.
- Add three pytest cases to `cast-server/tests/test_dispatch_precondition.py` covering: (a) omitted `output_dir` is defaulted to `GOALS_DIR/slug`; (b) malformed payload returns 422 with `error_code == "invalid_delegation_context"`; (c) explicit `output_dir` is preserved untouched.
- Run `pytest cast-server/tests/test_dispatch_precondition.py` and confirm all tests pass (existing + 3 new).
- Manually replay the failing curl payload (no `output_dir`) against a running server and confirm 200 + delegation file written, no 500 traceback.

**Out of scope (do NOT do these):**

- Editing `skills/claude-code/cast-child-delegation/SKILL.md` (handled by sp1b).
- Editing `docs/specs/cast-delegation-contract.collab.md` (spec already documents the fallback at line 66).
- Editing `agents/cast-orchestrate/cast-orchestrate.md` or other parent agent prompts — the plan explicitly punts on chasing upstream callers.
- Refactoring `agent_service.py:1001` (`artifact_dir = output_dir or goal_dir`); leave the existing service-layer fallback intact as a safety net.
- Mutating the pydantic model after construction (e.g., `delegation_context.output.output_dir = ...` post-build). All defaulting happens BEFORE construction via `setdefault`.
- Returning 400 or 500 for shape errors. The contract is 422; stay consistent with `MissingExternalProjectDirError` and `ValueError` handlers in the same function.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/models/delegation.py` | Modify | Line 17: `output_dir: str` (required) |
| `cast-server/cast_server/routes/api_agents.py` | Modify | Lines 65–71: builds `DelegationContext` without try/except, no `output` setdefault |
| `cast-server/tests/test_dispatch_precondition.py` | Modify | Existing fixture/tests intact; append three new test functions |

## Detailed Steps

### Step 1.1: Make `output_dir` non-required in the pydantic model

Edit `cast-server/cast_server/models/delegation.py`:

```python
class DelegationOutputConfig(BaseModel):
    output_dir: str = ""             # Empty = "use goal_dir" (route layer backfills)
    expected_artifacts: list[str] = []
    contract_version: str = "1.0"
```

The empty-string default is intentional: the server-side default (`GOALS_DIR/<slug>`) is applied at the route boundary via `setdefault` so the value is always populated before it reaches the service layer. Leaving the model permissive means a hand-built `output: {}` no longer triggers `ValidationError`, which is exactly the malformed payload that today causes the 500.

### Step 1.2: Wrap construction in try/except + inject default in the route

Edit `cast-server/cast_server/routes/api_agents.py`. Add the import near the top (after the existing `from pydantic import BaseModel`):

```python
from pydantic import BaseModel, ValidationError
```

Then replace lines 65–71 with:

```python
delegation_context_raw = data.get("delegation_context")
if delegation_context_raw:
    delegation_context_raw.setdefault("goal_slug", goal_slug)
    delegation_context_raw.setdefault("parent_run_id", parent_run_id or "")
    # Default output_dir to <GOALS_DIR>/<slug> when caller omits it.
    # Mirrors the goal_slug / parent_run_id setdefault pattern above; keeps
    # all defaulting in one place and avoids post-construction mutation.
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

Notes:

- Keep the conditional `if delegation_context_raw:` — bare-trigger requests without delegation context (the legacy path) must continue to work and produce `delegation_context = None`.
- `_config.GOALS_DIR` is already imported at module top via `from cast_server import config as _config`. Do not add a duplicate import.
- The existing `MissingExternalProjectDirError` / `ValueError` handlers further down the function are untouched.

### Step 1.3: Add three regression tests

Append to `cast-server/tests/test_dispatch_precondition.py` (after the last existing test). Reuse the `env` fixture and `_insert_goal` helper. Use a `TestClient` POST to `/api/agents/cast-create-execution-plan/trigger`. Assert against the on-disk `.delegation-<run_id>.json` file written under `<external_project_dir>/.cast/` (or wherever the goal's delegation file lands; cross-check `agent_service.trigger_agent` if the file location has shifted).

```python
# ---------------------------------------------------------------------------
# delegation_context shape — output_dir default + 422 envelope
# ---------------------------------------------------------------------------

def _delegation_payload(**output_overrides):
    """Minimal valid delegation_context with overrideable output block."""
    return {
        "agent_name": "cast-create-execution-plan",
        "instructions": "stub",
        "context": {"goal_title": "stub"},
        "output": {"expected_artifacts": ["x.md"], **output_overrides},
    }


def _read_delegation_file(env, slug, run_id):
    """Locate and read the .delegation-<run_id>.json file written by trigger."""
    import json
    # The file is under the goal's external_project_dir, in the .cast subdir.
    # Adjust the lookup to wherever trigger_agent writes the delegation JSON.
    goal_root = env["tmp_path"] / f"proj-{slug}"
    cast_dir = goal_root / ".cast"
    delegation_files = list(cast_dir.glob(f".delegation-{run_id}.json"))
    assert delegation_files, f"no delegation file for run {run_id} under {cast_dir}"
    return json.loads(delegation_files[0].read_text())


def test_trigger_defaults_output_dir_to_goal_dir(env, tmp_path):
    """When delegation_context.output omits output_dir, the server backfills
    GOALS_DIR/<slug> before constructing the pydantic model."""
    real_dir = tmp_path / "proj-default-out"
    real_dir.mkdir()
    _insert_goal(env["db_path"], "default-out", external_project_dir=str(real_dir))

    resp = env["client"].post(
        "/api/agents/cast-create-execution-plan/trigger",
        json={
            "goal_slug": "default-out",
            "delegation_context": _delegation_payload(),  # no output_dir
        },
    )

    assert resp.status_code == 200, resp.text
    run_id = resp.json()["run_id"]

    from cast_server import config as _config
    expected = str(_config.GOALS_DIR / "default-out")

    body = _read_delegation_file(env, "default-out", run_id)
    assert body["output"]["output_dir"] == expected


def test_trigger_returns_422_on_malformed_delegation_context(env, tmp_path):
    """Missing required fields (no instructions, no context) → 422 envelope
    with error_code='invalid_delegation_context' and a non-empty errors list."""
    real_dir = tmp_path / "proj-malformed"
    real_dir.mkdir()
    _insert_goal(env["db_path"], "malformed", external_project_dir=str(real_dir))

    resp = env["client"].post(
        "/api/agents/cast-create-execution-plan/trigger",
        json={
            "goal_slug": "malformed",
            "delegation_context": {"agent_name": "cast-create-execution-plan"},
        },
    )

    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["error_code"] == "invalid_delegation_context"
    assert body["detail"] == "delegation_context failed validation"
    assert isinstance(body.get("errors"), list) and body["errors"], body
    assert "cast-delegation-contract" in body["hint"]


def test_trigger_preserves_explicit_output_dir(env, tmp_path):
    """Regression for Issue #3: explicit output_dir must NOT be clobbered by
    the setdefault default. Locks down semantics so a future refactor
    replacing setdefault with hard assignment fails this test."""
    real_dir = tmp_path / "proj-explicit"
    real_dir.mkdir()
    _insert_goal(env["db_path"], "explicit-out", external_project_dir=str(real_dir))

    explicit = "/some/explicit/path"
    resp = env["client"].post(
        "/api/agents/cast-create-execution-plan/trigger",
        json={
            "goal_slug": "explicit-out",
            "delegation_context": _delegation_payload(output_dir=explicit),
        },
    )

    assert resp.status_code == 200, resp.text
    run_id = resp.json()["run_id"]
    body = _read_delegation_file(env, "explicit-out", run_id)
    assert body["output"]["output_dir"] == explicit
```

**Implementation note for the executing context:** the exact location of the `.delegation-<run_id>.json` file depends on `agent_service.trigger_agent`'s write path. Before finalizing the tests, grep for `delegation-` write sites (`grep -rn "\.delegation-" cast-server/cast_server/services/`) and adjust `_read_delegation_file` to match. If the file is written under a path that depends on `external_project_dir`, the helper above already accounts for that via the `tmp_path / f"proj-{slug}"` convention; otherwise adjust accordingly.

If the delegation file is not written synchronously during the request (e.g., it's written by the launcher subprocess), the `_read_delegation_file` approach won't work in unit tests. In that case, fall back to asserting on the in-memory `DelegationContext` by making the route briefly testable: e.g., monkeypatch `agent_service.trigger_agent` to capture the `delegation_context` argument. Use whichever approach matches the actual code path.

### Step 1.4: Run the test suite

```bash
cd <DIECAST_ROOT>
pytest cast-server/tests/test_dispatch_precondition.py -v
```

Expected: all existing tests pass + the three new tests pass. If a new test fails because `_read_delegation_file` is looking in the wrong directory, fix the helper rather than weakening the assertion.

### Step 1.5: Manual reproduction of the original 500

Start the server (`cd cast-server && python -m cast_server.main` or whatever the project's run command is — confirm via `cast-server/README` or `cast-server/cast_server/main.py`). With a goal `improved-first-launch` whose `external_project_dir` is set, replay the exact failing payload:

```bash
curl -i -X POST http://localhost:8000/api/agents/cast-create-execution-plan/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "goal_slug": "improved-first-launch",
    "delegation_context": {
      "agent_name": "cast-create-execution-plan",
      "instructions": "smoke test",
      "context": {"goal_title": "smoke"},
      "output": {"expected_artifacts": ["_manifest.md", "_shared_context.md"]}
    }
  }'
```

Expected:

- HTTP 200 with `{"run_id": "...", "status": "pending"}`.
- Server log shows no 500 traceback.
- The on-disk `.delegation-<run_id>.json` contains `output.output_dir == "<GOALS_DIR>/improved-first-launch"`.

Then verify the 422 path with a payload missing `instructions`:

```bash
curl -i -X POST http://localhost:8000/api/agents/cast-create-execution-plan/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "goal_slug": "improved-first-launch",
    "delegation_context": {"agent_name": "cast-create-execution-plan"}
  }'
```

Expected: HTTP 422 with `error_code == "invalid_delegation_context"` and a populated `errors` array.

## Verification

### Automated Tests (permanent)

In `cast-server/tests/test_dispatch_precondition.py`:

- `test_trigger_defaults_output_dir_to_goal_dir` — asserts omitted `output_dir` becomes `GOALS_DIR/<slug>`.
- `test_trigger_returns_422_on_malformed_delegation_context` — asserts 422 envelope shape, `error_code`, populated `errors`, and `hint`.
- `test_trigger_preserves_explicit_output_dir` — asserts caller-supplied `output_dir` is not clobbered.

### Validation Scripts (temporary)

The two manual `curl` invocations from Step 1.5. They are not committed; they're a one-time confirmation that the live server matches the test bed.

### Manual Checks

1. `pytest cast-server/tests/test_dispatch_precondition.py -v` exits 0 with all tests passing (existing + 3 new).
2. The 200-path curl in Step 1.5 returns `{"run_id": "...", "status": "pending"}` and the server log contains no `Internal Server Error` line.
3. The 422-path curl in Step 1.5 returns the documented envelope.
4. `git diff cast-server/cast_server/models/delegation.py` shows only the `output_dir: str = ""` change.
5. `git diff cast-server/cast_server/routes/api_agents.py` shows: import update, `output` setdefault block, try/except wrapping the `DelegationContext(...)` call. No other lines.

### Success Criteria

- [ ] `DelegationOutputConfig.output_dir` is `str = ""` (no longer required).
- [ ] Route handler imports `ValidationError` from pydantic.
- [ ] Route handler injects `output_dir` default via `setdefault` before constructing `DelegationContext`.
- [ ] Route handler wraps `DelegationContext(...)` construction in try/except returning 422 with `error_code: "invalid_delegation_context"`, populated `errors`, and `hint`.
- [ ] `pytest cast-server/tests/test_dispatch_precondition.py` passes including all 3 new tests.
- [ ] Manual curl with `output: {expected_artifacts: [...]}` returns 200 (no 500 traceback).
- [ ] Manual curl with malformed `delegation_context` returns 422 with the new envelope.
- [ ] No edits made to `skills/claude-code/cast-child-delegation/SKILL.md` (sp1b owns that file).
- [ ] No edits made to `docs/specs/cast-delegation-contract.collab.md`.
- [ ] No edits made to `agent_service.py` (`artifact_dir = output_dir or goal_dir` left intact).

## Execution Notes

- **Spec-linked files:** Both `routes/api_agents.py` and `models/delegation.py` are covered by `docs/specs/cast-delegation-contract.collab.md`. Read it (especially lines 56–66 and the terminal-status section) before editing and confirm: (1) the file-canonical naming `<goal_dir>/.agent-run_<RUN_ID>.output.json` is unchanged, (2) the goal-dir fallback at line 66 is now actually implemented, (3) the terminal-status set is unchanged. No spec edit is required because the spec already documents the desired behavior.
- **Do not regress the legacy path.** When `data.get("delegation_context")` is falsy/missing, `delegation_context` must remain `None` and the route must continue to enqueue a non-delegation run. The existing tests cover this; do not break them.
- **`include_url=False` matters.** Pydantic's default error format includes a `url` field pointing at https://errors.pydantic.dev/.../v1.x — those URLs leak the pydantic version and are noisy for parent agents. Pass `include_url=False`.
- **Don't catch `ValidationError` too broadly.** Only wrap the `DelegationContext(**delegation_context_raw)` line. Wrapping the whole function would mask unrelated bugs.
- **Test isolation.** Each new test creates its own goal slug (`default-out`, `malformed`, `explicit-out`) so they don't share DB rows with the existing tests or each other.
- **Avoid scope creep.** Resist the urge to also fix `agent_service.py:1001` or refactor `DelegationContext` field ordering. The plan is deliberately minimal.
