# Sub-phase 4: Hook Events, Handlers, and `cast-hook` Console Script

> **Pre-requisite:** Read `docs/execution/capture-user-invocations-as-runs/_shared_context.md` before starting.

## Objective

Stand up the `cast-hook` console_script and its three supporting modules:
- `cli/hook_events.py` — single source of truth (Decision #10) for the
  {event → subcommand → handler} mapping.
- `cli/hook_handlers.py` — `user_prompt_start` / `user_prompt_stop` HTTP-poking
  implementations (stdlib only).
- `cli/hook.py` — the `cast-hook` CLI entry, dispatching to handlers or to
  `install_hooks.install/uninstall` (latter is a no-op stub here; sp5 implements it).
- `pyproject.toml` — register `cast-hook` in `[project.scripts]`.

Author handler/CLI tests (`tests/test_cli_hook.py`) with HTTP mocked.

## Dependencies

- **Requires completed:** sp1 in spirit (so the URL the handler hits actually works during
  smoke), but strictly the only hard prerequisite is the project's pyproject.toml being
  writable.
- **Assumed codebase state:** A `cli/` package does not yet exist under
  `cast-server/cast_server/`. `pyproject.toml` already has at least one console_script
  entry (e.g., `precommit-tests`).

## Scope

**In scope:**
- New package `cast-server/cast_server/cli/` with `__init__.py`, `hook_events.py`,
  `hook_handlers.py`, `hook.py`. ~120 lines total.
- `pyproject.toml` — append `cast-hook = "cast_server.cli.hook:main"`.
- Stub `install_hooks.install` / `uninstall` (defined in sp5; here you only need the
  `cli/hook.py` import to not crash when sp5 lands. Either land a minimal placeholder
  module that raises `NotImplementedError` for install/uninstall paths, or skip the
  install/uninstall branches in tests with `pytest.importorskip`-style guarding.
  **Recommended: land a placeholder `install_hooks.py` so imports don't break.**).
- `cast-server/tests/test_cli_hook.py` — 11 tests with mocked HTTP.

**Out of scope (do NOT do these):**
- The actual settings.json injector logic (sp5).
- Modifying any existing route or service.
- Adding any third-party dependency (`requests`, `httpx`, etc.) — handlers must use
  `urllib.request` per the plan.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/cli/__init__.py` | Create | Does not exist |
| `cast-server/cast_server/cli/hook_events.py` | Create | Does not exist |
| `cast-server/cast_server/cli/hook_handlers.py` | Create | Does not exist |
| `cast-server/cast_server/cli/hook.py` | Create | Does not exist |
| `cast-server/cast_server/cli/install_hooks.py` | Create (placeholder) | Does not exist; sp5 fills in |
| `pyproject.toml` | Modify | Has `[project.scripts]` already |
| `cast-server/tests/test_cli_hook.py` | Create | Does not exist |

## Detailed Steps

### Step 4.1: Create the cli package marker

```bash
mkdir -p cast-server/cast_server/cli
```

Create `cast-server/cast_server/cli/__init__.py` as empty (or a single-line module
docstring).

### Step 4.2: Create `hook_handlers.py` first

Imported by `hook_events.py`, so create it before `hook_events.py` to avoid circulars.

Body verbatim from the plan ("New file: hook_handlers.py"). Key properties:

- `PROMPT_PATTERN = re.compile(r"^\s*/(cast-[a-z0-9-]+)")`. Note: anchored at the start
  with optional whitespace. The capture group is the agent name **without** the leading
  slash.
- `_base_url()`: reads `CAST_PORT` (default `8005`) and `CAST_HOST` (default `127.0.0.1`)
  from env. Returns `f"http://{host}:{port}/api/agents"`.
- `_post(path, body)`: 2-second timeout; swallows `URLError`, `TimeoutError`, `OSError`
  silently. **Never blocks the user prompt.**
- `_read_payload()`: reads stdin, returns `{}` on JSON decode error.
- `user_prompt_start()`: read payload, regex-match `prompt`, on no-match return silently.
  On match, POST `/user-invocations` with `{agent_name, prompt, session_id}`.
- `user_prompt_stop()`: read payload, return silently if `session_id` missing. Otherwise
  POST `/user-invocations/complete` with `{session_id}`.

### Step 4.3: Create `hook_events.py`

Body verbatim from the plan ("New file: hook_events.py"):

```python
from cast_server.cli import hook_handlers as _h

HOOK_EVENTS = [
    ("UserPromptSubmit", "user-prompt-start", _h.user_prompt_start),
    ("Stop",             "user-prompt-stop",  _h.user_prompt_stop),
]

DISPATCH = {sub: handler for _, sub, handler in HOOK_EVENTS}
COMMAND_FOR_EVENT = {evt: f"cast-hook {sub}" for evt, sub, _ in HOOK_EVENTS}
```

This is the canonical mapping referenced by sp5's installer and by `hook.py`'s dispatch
logic. **Do not duplicate the list anywhere else.**

### Step 4.4: Create a placeholder `install_hooks.py`

```python
"""Settings.json injector. Real implementation in sub-phase 5."""

def install(project_root, user_scope: bool = False) -> int:
    raise NotImplementedError("install_hooks.install — implemented in sp5")

def uninstall(project_root, user_scope: bool = False) -> int:
    raise NotImplementedError("install_hooks.uninstall — implemented in sp5")
```

This is enough for `hook.py` to import without crashing. sp5 will rewrite this file
completely.

### Step 4.5: Create `hook.py`

Body verbatim from the plan ("New file: hook.py"). The dispatch flow:

- `argv` empty → print usage, exit 0.
- `argv[0]` in `DISPATCH` → call the handler, exit 0 (never block the prompt).
- `argv[0]` in `("install", "uninstall")` → check for `--user`, call `install_hooks.install`
  or `install_hooks.uninstall` with `project_root=Path.cwd()`. Return its return code.
- Unknown subcommand → print error to stderr, exit 0 (still don't block).

### Step 4.6: Register the console_script

Edit `pyproject.toml` `[project.scripts]`:

```toml
[project.scripts]
precommit-tests = "cast_server.dev_tools.precommit_tests:precommit_tests"
cast-hook       = "cast_server.cli.hook:main"
```

Reinstall:

```bash
cd cast-server && uv sync   # or: pip install -e .
which cast-hook            # should resolve
cast-hook                  # should print usage
```

### Step 4.7: Author the CLI/handler tests

Create `cast-server/tests/test_cli_hook.py` with 11 tests:

```python
def test_user_prompt_start_matches_cast_command(monkeypatch_post)
def test_user_prompt_start_skips_non_cast_prompt(monkeypatch_post)
def test_user_prompt_start_skips_empty_stdin(monkeypatch_post)
def test_user_prompt_start_extracts_agent_name_from_slash(monkeypatch_post)
def test_user_prompt_start_passes_session_id_through(monkeypatch_post)
def test_user_prompt_stop_calls_complete_with_session_id(monkeypatch_post)
def test_user_prompt_stop_skips_when_session_id_missing(monkeypatch_post)
def test_unknown_subcommand_exits_zero_no_post(monkeypatch_post)
def test_server_unreachable_exits_zero(monkeypatch_unreachable)
def test_install_subcommand_dispatches_to_install_hooks(monkeypatch_install)
def test_uninstall_subcommand_dispatches_to_install_hooks(monkeypatch_install)
```

Mocking strategy:

- `monkeypatch_post` fixture: monkeypatch `urllib.request.urlopen` (or, easier, the
  module-level `_post` function in `hook_handlers`) to record `(path, body)` calls. Reset
  between tests.
- `monkeypatch_unreachable` fixture: make `urlopen` raise `URLError`. Assert the test
  function exits 0 and propagates no exception.
- `monkeypatch_install` fixture: monkeypatch `install_hooks.install` and
  `install_hooks.uninstall` to record invocations. The placeholder `NotImplementedError`
  bodies make this monkeypatch necessary for the test to pass at this stage.

For stdin mocking, use `monkeypatch.setattr("sys.stdin", io.StringIO(payload_json))`.

Specific test bodies:

- `test_user_prompt_start_matches_cast_command`:
  stdin = `{"prompt": "/cast-plan-review please", "session_id": "S1"}` → asserts one POST
  to `/user-invocations` with body `{"agent_name": "cast-plan-review", "prompt": "/cast-plan-review please", "session_id": "S1"}`.
- `test_user_prompt_start_skips_non_cast_prompt`:
  stdin = `{"prompt": "what time is it", "session_id": "S1"}` → asserts no POST.
- `test_user_prompt_start_skips_empty_stdin`: stdin empty → no POST.
- `test_user_prompt_start_extracts_agent_name_from_slash`:
  prompt = `/cast-detailed-plan foo` → POST agent_name = `cast-detailed-plan`.
- `test_user_prompt_start_passes_session_id_through`: assert the session_id round-trips.
- `test_user_prompt_stop_calls_complete_with_session_id`:
  stdin = `{"session_id": "S2"}` → POST to `/user-invocations/complete` with
  `{"session_id": "S2"}`.
- `test_user_prompt_stop_skips_when_session_id_missing`:
  stdin = `{}` → no POST.
- `test_unknown_subcommand_exits_zero_no_post`: invoke `main(["nonsense"])` → exit 0,
  no POST made.
- `test_server_unreachable_exits_zero`: with the `urlopen` mock raising `URLError`,
  invoke `user_prompt_start()` with a matching prompt → no exception, exit 0.
- `test_install_subcommand_dispatches_to_install_hooks`: invoke `main(["install"])`,
  assert the patched `install_hooks.install` was called with `project_root=Path.cwd()`,
  `user_scope=False`. With `--user`, assert `user_scope=True`.
- `test_uninstall_subcommand_dispatches_to_install_hooks`: symmetric for `uninstall`.

### Step 4.8: Run the suite

```bash
cd cast-server && uv run pytest tests/test_cli_hook.py -v
```

All 11 tests must pass.

### Step 4.9: Manual end-to-end of the handler

```bash
# With cast-server NOT running (so the POST silently fails):
echo '{"prompt":"/cast-plan-review hi","session_id":"S1"}' | cast-hook user-prompt-start
echo $?   # Must be 0 — handler swallowed the connection error.

# With cast-server running (depends on sp1 + sp2):
bin/cast-server &      # start server
echo '{"prompt":"/cast-plan-review hi","session_id":"S1"}' | cast-hook user-prompt-start
# Inspect agent_runs.db; row should exist with status=running.
echo '{"session_id":"S1"}' | cast-hook user-prompt-stop
# Row should now be status=completed.
```

## Verification

### Automated Tests (permanent)

`cast-server/tests/test_cli_hook.py` — 11 tests as enumerated.

### Validation Scripts (temporary)

The Step 4.6 reinstall + `which cast-hook` check; the Step 4.9 end-to-end with the dev
server.

### Manual Checks

```bash
# Confirm the cli/ package layout
ls cast-server/cast_server/cli/

# Confirm hook_events is the only place the (event, subcommand, handler) tuple lives
grep -rn "UserPromptSubmit\|user-prompt-start" cast-server/cast_server/cli/
# Should appear ONLY in hook_events.py (and string-only references in install_hooks.py
# via HOOK_EVENTS / COMMAND_FOR_EVENT, which is fine because they import the constant).

# Confirm pyproject change
git diff pyproject.toml
```

### Success Criteria

- [ ] `cast-server/cast_server/cli/` package exists with the four files.
- [ ] `hook_events.HOOK_EVENTS` is the single source of truth — no duplicate event lists
      anywhere else in the codebase.
- [ ] `hook_handlers` uses stdlib only (`urllib.request`, `json`, `re`, `sys`, `os`).
- [ ] `cast-hook` is on PATH after `uv sync` / `pip install -e .`.
- [ ] `cast-hook` with no args prints a helpful usage line and exits 0.
- [ ] `cast-hook user-prompt-start` exits 0 even with no server running.
- [ ] All 11 tests in `test_cli_hook.py` pass.
- [ ] Server end-to-end smoke (Step 4.9) creates and closes a row.
- [ ] `install_hooks.py` placeholder is in place and tests cover the dispatch path
      via mocking.

## Execution Notes

- **Decision #6 is the architectural anchor:** `cast-hook` is the dedicated console
  script — daemon binary `cast-server` stays a pure uvicorn launcher, zero coupling.
- **Decision #10 is the structural anchor:** drift between install-side and runtime-side
  must be impossible. If you find yourself typing the string `"user-prompt-start"`
  anywhere outside `hook_events.py`, stop and route it through `HOOK_EVENTS` /
  `DISPATCH` / `COMMAND_FOR_EVENT`.
- The hook timeout of 3 seconds (Decision-locked in plan) is set in settings.json by sp5;
  the handler's internal `urlopen(timeout=2)` is one second tighter so it surfaces
  failures via the silent-fail path before Claude Code times us out at the hook level.
- **Spec-linked files:** None yet. sp7 authors `cast-hooks.collab.md` referencing this
  module.
- **Skill/agent delegation:** `/cast-pytest-best-practices` is recommended for the test
  file before declaring this sub-phase done.
- **PATH risk (Risks #3 in the plan):** `cast-hook` works only if it's on PATH at the
  time Claude Code spawns the hook subprocess. uv/pipx installs put it there; bare
  `python -m` may not. We don't address this here (sp5 will warn at install time), but
  be aware while smoke-testing.
