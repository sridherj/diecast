# Plan: Capture user-typed `/cast-*` slash commands as `agent_run` rows

**Date:** 2026-05-01
**Status:** Reviewed via `/cast-plan-review` BIG (11 decisions); ready for execution
**Related plan (independent, no overlap):** `docs/plan/2026-05-01-cast-runs-threaded-tree.collab.md` (renders the runs tree; this plan adds visibility of the human action that initiated work)

## Context

Today an `agent_run` row only exists when an agent dispatches another agent over HTTP (`POST /api/agents/{name}/trigger`) or via `invoke_agent()`. When the user types `/cast-plan-review` directly into Claude Code, the main loop runs the skill in-process — **no run row at all**. The runs tree shows children, but the human action that started the work is invisible.

We want every user-typed `/cast-*` slash command to produce a top-level `agent_run` row whose `agent_name` is the actual agent (`cast-plan-review`, `cast-detailed-plan`, etc.). Lifecycle is bracketed by Claude Code's `UserPromptSubmit` and `Stop` hooks. Children of in-turn dispatches stay top-level (correlated by timestamp + `session_id` only — see Decision #1).

**Scope (decided):** only `/cast-*` slash commands. Freeform prompts, other skills, and CLI invocations of cast-server are out.

**Non-goals:** transcript capture, output.json synthesis, UI badge for "user prompt" rows, ambient parent linking of children. The win we want today is the *root row* — proof that a user typed `/cast-X` at time T.

**User-safety prime directive (Decision #11):** the hook installer is *one listener among potentially many* in the user's Claude Code settings. It must NEVER override or replace third-party / pre-existing user hooks. This is critical enough to capture in its own dedicated spec — see "Spec capture" below.

## Locked design decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | `agent_name` on the row is the actual agent (`cast-plan-review`), **not** a synthetic name like `claude-code-prompt`. | The user invocation IS that agent running, just in the main loop instead of a subprocess. Same agent, different execution surface. |
| 2 | The discriminator for "user invocation vs. subprocess-spawned" is `input_params.source == "user-prompt"`. **No new model field, no migration.** | `AgentRun` already has every column needed (`agent_name`, `session_id`, `status`, `input_params`, `started_at`, `completed_at`). Adding a column for one bit of semantics is over-engineering. |
| 3 | **No ambient parent linking.** User-invocation rows stay top-level (`parent_run_id=null`). Subsequent in-turn HTTP dispatches stay top-level too. Correlation between them is by `session_id` + timestamps only. | (Locked at review time, replacing earlier ambient-parent design.) Ambient parenting forced trigger_agent to bypass `allowed_delegations` for user-invocation parents — too much risk surface for the visibility benefit. We can add ambient linking later as a strict additive change. |
| 4 | **Stop closes by `session_id`**, not by a marker file. Stop endpoint accepts `{session_id}`; server runs `UPDATE agent_runs SET status='completed' WHERE session_id=? AND status='running' AND json_extract(input_params,'$.source')='user-prompt' AND started_at > ?` (1-hour staleness window — see Decision #5). | No filesystem state to manage. `agent_runs.session_id` column already exists. Self-healing: orphan rows from prior crashes get cleaned up on the next Stop in the same session. Resilient to crash recovery without ever leaving permanently-running ghost rows. |
| 5 | **1-hour staleness window** on the close-by-session query. Rows older than 1h with same session_id are NOT auto-closed by a future Stop. | Hedges against the (currently non-existent) case where Claude Code reuses session_id across separate Claude Code sessions; ancient orphans require manual cleanup but don't get spuriously completed by an unrelated future session. |
| 6 | Hook command is a **new `cast-hook` console_script** with subcommands: `cast-hook user-prompt-start | user-prompt-stop | install | uninstall`. Settings.json line: `"command": "cast-hook user-prompt-start"`. | Daemon binary `cast-server` stays a pure uvicorn launcher. Zero coupling between daemon lifecycle and hook tooling. PATH-resolved (no hardcoded paths in any user's settings). |
| 7 | Settings.json injection follows gstack's `gstack-settings-hook` pattern: read → defensive JSON parse → mutate in memory → atomic write (`.tmp` + `os.replace`). Idempotent dedup via command-substring match. **Never replace existing hooks**; only append our own / surgically remove our own. | Reference: `~/workspace/reference_repos/gstack/bin/gstack-settings-hook`. Battle-tested. We use stdlib Python (no `bun` dep). |
| 8 | Install is invoked from `/cast-init` (default ON, `--no-hooks` opt-out) and exposed standalone as `cast-hook install` / `cast-hook uninstall`. Project-level scope (`<project_root>/.claude/settings.json`), not user-level. | Cast-server is a per-project tool; its hook should not fire in unrelated projects. `--user` flag still available for those who want the global install. |
| 9 | If `.claude/settings.json` is missing → treat as `{}` and create. If malformed → **abort with a clear error**, do not write. **Catch `OSError`/`PermissionError`** and surface a readable message (e.g., "Cannot write <path> (Permission denied). Pass --user to write to ~/.claude/settings.json instead."). Always clean up the `.tmp` file on exception. | Crashing the user's settings file is the worst possible outcome. Better to fail loud than silently overwrite. Tracebacks-as-error-UX is a UX failure. |
| 10 | **Single canonical event/subcommand mapping** in `cast-server/cast_server/cli/hook_events.py`. Both `install_hooks.py` (settings injection) and `hook.py` (subcommand dispatch) import from it. Adding a new hook event = one line in one file. Drift is structurally impossible. | DRY across the install-side and runtime-side mappings. Without this, the install-side could write a settings.json line referencing a subcommand the binary doesn't implement (or vice versa) and the failure mode is silent. |
| 11 | New service file `cast-server/cast_server/services/user_invocation_service.py`. Does **not** add functions to `agent_service.py` (already 1500+ lines). | Layer hygiene — a new lifecycle deserves its own seam. The new service wraps existing `create_agent_run()` / `update_agent_run()` plus a single new SQL query for the close-by-session path. |
| 12 | Two endpoints under `/api/agents/user-invocations/`: `POST /` (open, body: `{agent_name, prompt, session_id}`) and `POST /complete` (close, body: `{session_id}`). | Thin controllers; all logic in service. |
| 13 | Hook detects `/cast-*` via regex `^\s*/(cast-[a-z0-9-]+)`. Server is **agnostic** to the prefix — it accepts any `agent_name`. | Don't push policy to the server; the server records what the hook tells it. Easier to broaden scope later. |
| 14 | `Stop` hook always reports `status=completed`. We don't try to detect user-cancel or interruption in v1. | Claude Code's Stop hook payload doesn't reliably distinguish "finished" from "interrupted." Defer until we have a need. |

## Architecture

### Lifecycle in one diagram

```
user types "/cast-plan-review …"
        │
        ▼
[UserPromptSubmit hook]   cast-hook user-prompt-start
        │   stdin: {"prompt": "...", "session_id": "..."}
        │   regex match /cast-[a-z0-9-]+ ?  if no, exit 0 silently
        ▼
POST /api/agents/user-invocations    body: {agent_name, prompt, session_id}
        │
        ▼
[server]  user_invocation_service.register(...)
            └─ create_agent_run(agent_name="cast-plan-review", session_id=…,
                                input_params={source:"user-prompt", prompt},
                                status="running",
                                parent_run_id=None)
        │
        ▼
returns {run_id}   ◀── hook discards; just exits 0

   …agent runs in main Claude Code loop…
   …may dispatch children — they create their own top-level rows…
   …user's turn ends…

[Stop hook]  cast-hook user-prompt-stop
        │   stdin: {"session_id": "..."}
        ▼
POST /api/agents/user-invocations/complete    body: {session_id}
        │
        ▼
[server] user_invocation_service.complete(session_id):
            └─ UPDATE agent_runs SET status='completed', completed_at=now
                 WHERE session_id=?
                   AND status='running'
                   AND json_extract(input_params,'$.source')='user-prompt'
                   AND started_at > (now - 1h)
            ──── returns count of rows closed (typically 1; 2+ means orphans cleaned)
```

No marker file. No ambient parent. No edits to `agent_service.py`. No edits to `trigger_agent` / `invoke_agent`.

### Code layout

#### New file: `cast-server/cast_server/services/user_invocation_service.py`

```python
"""User-invocation lifecycle. Captures /cast-* prompts as top-level agent_run rows.

Public API:
    register(agent_name, prompt, session_id)  -> run_id
    complete(session_id)                      -> int  (count of rows closed)

No marker file. No filesystem state. Stop's close path is a single SQL UPDATE
that self-heals orphans within a 1-hour staleness window.
"""
from datetime import datetime, timedelta, timezone
from cast_server.db.connection import get_connection
from cast_server.services.agent_service import create_agent_run, update_agent_run

STALENESS_WINDOW = timedelta(hours=1)

def register(agent_name: str, prompt: str, session_id: str | None,
             db_path=None) -> str:
    now = datetime.now(timezone.utc).isoformat()
    run_id = create_agent_run(
        agent_name=agent_name,
        goal_slug="system-ops",      # matches existing CLI invocation default
        task_id=None,
        input_params={"source": "user-prompt", "prompt": prompt},
        session_id=session_id,
        status="running",
        parent_run_id=None,
        db_path=db_path,
    )
    update_agent_run(run_id, started_at=now, db_path=db_path)
    return run_id

def complete(session_id: str | None, db_path=None) -> int:
    if not session_id:
        return 0
    cutoff = (datetime.now(timezone.utc) - STALENESS_WINDOW).isoformat()
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection(db_path)
    cur = conn.execute(
        """UPDATE agent_runs
           SET status='completed', completed_at=?
           WHERE session_id=?
             AND status='running'
             AND json_extract(input_params, '$.source')='user-prompt'
             AND started_at > ?""",
        (now, session_id, cutoff),
    )
    closed = cur.rowcount
    conn.commit()
    conn.close()
    return closed
```

This file uses the existing `get_connection()` for the one bespoke UPDATE (self-contained query that doesn't fit `update_agent_run`'s by-id contract). Otherwise wraps existing service functions; no DB-layer code duplicated.

**Decision #4** justifies the bespoke UPDATE: there is no existing service function for "update many runs by predicate"; adding one to `agent_service.py` would be premature abstraction (no other caller).

#### `cast-server/cast_server/services/agent_service.py`

**No changes.** Decision #3 dropped ambient parenting; `trigger_agent` / `invoke_agent` are untouched.

#### Modify: `cast-server/cast_server/routes/api_agents.py`

Add two endpoints. Thin controllers.

```python
class UserInvocationOpenRequest(BaseModel):
    agent_name: str
    prompt: str
    session_id: str | None = None

class UserInvocationCompleteRequest(BaseModel):
    session_id: str | None = None

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

#### New file: `cast-server/cast_server/cli/hook_events.py`

Single source of truth (Decision #10) for the {Claude Code event → cast-hook subcommand → handler function} mapping.

```python
"""Canonical mapping: Claude Code hook event → cast-hook subcommand → handler.

DO NOT duplicate this list anywhere. Both install_hooks.py (settings injection)
and hook.py (runtime dispatch) import from here. Adding a new hook event = one
line in this file.
"""
from cast_server.cli import hook_handlers as _h

# (claude_code_event, cast_hook_subcommand, handler)
HOOK_EVENTS = [
    ("UserPromptSubmit", "user-prompt-start", _h.user_prompt_start),
    ("Stop",             "user-prompt-stop",  _h.user_prompt_stop),
]

# Derived views — convenience for callers; do not extend this list, extend HOOK_EVENTS.
DISPATCH = {sub: handler for _, sub, handler in HOOK_EVENTS}
COMMAND_FOR_EVENT = {evt: f"cast-hook {sub}" for evt, sub, _ in HOOK_EVENTS}
```

#### New file: `cast-server/cast_server/cli/hook_handlers.py`

The two HTTP-poking functions. Kept separate from `hook_events.py` so the canonical list can import them without circulars.

```python
"""Hook handler implementations. Called by `cast-hook <subcommand>`.

Each handler reads JSON from stdin, posts to cast-server, and returns. Any
network/HTTP failure exits silently — never block the user's prompt.
"""
import json, os, re, sys, urllib.request, urllib.error

PROMPT_PATTERN = re.compile(r"^\s*/(cast-[a-z0-9-]+)")

def _base_url() -> str:
    port = os.environ.get("CAST_PORT", "8005")     # matches bin/cast-server default
    host = os.environ.get("CAST_HOST", "127.0.0.1")
    return f"http://{host}:{port}/api/agents"

def _post(path: str, body: dict) -> None:
    try:
        req = urllib.request.Request(
            f"{_base_url()}{path}",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=2).read()
    except (urllib.error.URLError, TimeoutError, OSError):
        pass  # never block the prompt

def _read_payload() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return {}

def user_prompt_start() -> None:
    payload = _read_payload()
    prompt = payload.get("prompt", "")
    m = PROMPT_PATTERN.match(prompt)
    if not m:
        return
    _post("/user-invocations", {
        "agent_name": m.group(1),
        "prompt": prompt,
        "session_id": payload.get("session_id"),
    })

def user_prompt_stop() -> None:
    payload = _read_payload()
    session_id = payload.get("session_id")
    if not session_id:
        return  # nothing to close without a key
    _post("/user-invocations/complete", {"session_id": session_id})
```

#### New file: `cast-server/cast_server/cli/hook.py`

The `cast-hook` console_script entry. Routes to `hook_events.DISPATCH` for runtime hooks, or to `install_hooks.install` / `... uninstall` for setup.

```python
"""cast-hook CLI. Console_script registered in pyproject.toml.

Subcommands:
  user-prompt-start   (UserPromptSubmit hook)
  user-prompt-stop    (Stop hook)
  install [--user]    (write entries to .claude/settings.json)
  uninstall [--user]  (remove our entries; preserve everything else)
"""
import sys
from pathlib import Path
from cast_server.cli.hook_events import DISPATCH
from cast_server.cli import install_hooks

def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("Usage: cast-hook {user-prompt-start | user-prompt-stop | install | uninstall} [args]", file=sys.stderr)
        return 0
    sub = argv[0]
    if sub in DISPATCH:
        DISPATCH[sub]()
        return 0  # never block the user
    if sub in ("install", "uninstall"):
        user_scope = "--user" in argv
        project_root = Path.cwd()  # caller (e.g. /cast-init) should chdir; cast-hook install --user bypasses
        fn = install_hooks.install if sub == "install" else install_hooks.uninstall
        return fn(project_root=project_root, user_scope=user_scope)
    print(f"Unknown subcommand: {sub}", file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

#### New file: `cast-server/cast_server/cli/install_hooks.py`

Idempotent settings.json injector + uninstaller. Pure stdlib.

```python
"""Install/uninstall cast-server hooks in .claude/settings.json.

Pattern adapted from gstack-settings-hook. Atomic writes, idempotent dedup,
surgical uninstall. NEVER replaces third-party hooks.
"""
import json, os, sys, tempfile
from pathlib import Path
from cast_server.cli.hook_events import HOOK_EVENTS, COMMAND_FOR_EVENT

HOOK_MARKER = "cast-hook "  # trailing space — any command starting "cast-hook <sub>" is ours
HOOK_TIMEOUT_SECONDS = 3
PROJECT_MARKERS = (".git", ".cast", "pyproject.toml", "package.json")

def _settings_path(user_scope: bool, project_root: Path) -> Path:
    return (Path.home() if user_scope else project_root) / ".claude" / "settings.json"

def _looks_like_project_root(p: Path) -> bool:
    return any((p / m).exists() for m in PROJECT_MARKERS)

def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise SystemExit(
            f"\nERROR: {path} contains invalid JSON ({e}).\n"
            f"Refusing to overwrite. Fix or delete the file, then re-run.\n"
        )

def _atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_str = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    tmp = Path(tmp_str)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(json.dumps(data, indent=2) + "\n")
        os.replace(tmp, path)
    except (OSError, PermissionError) as e:
        try: tmp.unlink()
        except OSError: pass
        raise SystemExit(
            f"\nERROR: cannot write {path} ({e.__class__.__name__}: {e}).\n"
            f"Fix permissions, free disk space, or pass --user to write to ~/.claude/settings.json instead.\n"
        )

def install(project_root: Path, user_scope: bool = False) -> int:
    path = _settings_path(user_scope, project_root)
    if not user_scope and not _looks_like_project_root(project_root):
        print(
            f"Warning: {project_root} does not look like a project root "
            f"(no {'/'.join(PROJECT_MARKERS)} found). Pass --project-root or --user to override.",
            file=sys.stderr,
        )
    settings = _load(path)
    settings.setdefault("hooks", {})
    added = []
    for event, _, _ in HOOK_EVENTS:
        cmd = COMMAND_FOR_EVENT[event]
        entries = settings["hooks"].setdefault(event, [])
        already = any(
            (h.get("command") or "").startswith(HOOK_MARKER)
            for entry in entries
            for h in (entry.get("hooks") or [])
        )
        if already:
            continue
        entries.append({"hooks": [{"type": "command", "command": cmd, "timeout": HOOK_TIMEOUT_SECONDS}]})
        added.append(event)
    _atomic_write(path, settings)
    msg = (f"Installed cast-hook entries ({', '.join(added)}) → {path}"
           if added else f"cast-hook entries already installed → {path}")
    print(msg)
    return 0

def uninstall(project_root: Path, user_scope: bool = False) -> int:
    path = _settings_path(user_scope, project_root)
    if not path.exists():
        print(f"No settings file at {path}; nothing to do.")
        return 0
    settings = _load(path)
    hooks = settings.get("hooks") or {}
    removed = []
    for event, _, _ in HOOK_EVENTS:
        entries = hooks.get(event)
        if not entries: continue
        kept = [
            entry for entry in entries
            if not any((h.get("command") or "").startswith(HOOK_MARKER) for h in (entry.get("hooks") or []))
        ]
        if len(kept) != len(entries):
            removed.append(event)
        if kept:
            hooks[event] = kept
        else:
            del hooks[event]
    if not hooks:
        settings.pop("hooks", None)
    _atomic_write(path, settings)
    print(f"Removed cast-hook entries ({', '.join(removed) or 'none found'}) → {path}")
    return 0
```

#### Modify: `pyproject.toml`

Add to `[project.scripts]`:

```toml
[project.scripts]
precommit-tests = "cast_server.dev_tools.precommit_tests:precommit_tests"
cast-hook       = "cast_server.cli.hook:main"
```

After `pip install -e .` (or `uv sync`), `cast-hook` is on the user's PATH.

#### Modify: `cast-server/cast_server/db/connection.py`

Add an index next to the existing `idx_error_memories_agent` precedent at line 137 (Decision in Performance #10):

```python
# Stop's close-by-session query needs this for sub-millisecond filtering as agent_runs grows.
conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_runs_session_status ON agent_runs(session_id, status)")
```

No migration; runs on every server init via the same precedent.

#### Resulting settings.json delta (additive)

```json
"hooks": {
  "UserPromptSubmit": [
    { "hooks": [{ "type": "command", "command": "cast-hook user-prompt-start", "timeout": 3 }] }
  ],
  "Stop": [
    { "hooks": [{ "type": "command", "command": "cast-hook user-prompt-stop", "timeout": 3 }] }
  ]
}
```

Whatever the user already had in `hooks.UserPromptSubmit`, `hooks.Stop`, or any other event remains intact. Our entries get appended to those lists.

#### Wire installer into `/cast-init`

`/cast-init` is the per-project setup skill. Add a final step:

> "Installing cast-hook entries (writes to `<project>/.claude/settings.json`). Skip with `--no-hooks`."

Implementation: invoke `install_hooks.install(project_root=<the goal repo>)` from cast-init's orchestrator. Confirm the actual entry point at impl time (likely a SKILL.md or `bin/cast-init` script).

The bare CLI form `cast-hook install` is also documented for users who want to manage hooks outside `/cast-init`.

#### Settings injection: idempotent + safe (locked properties)

- **Missing file**: created with just our hooks block. Never errors.
- **Malformed JSON**: errors out without writing; surfaces parse error verbatim.
- **`OSError`/`PermissionError` during write**: caught; readable message ("Cannot write … fix permissions or pass --user"); `.tmp` file cleaned up; non-zero exit.
- **Existing hooks for other events** (PostToolUse, SubagentStart, etc.): untouched, byte-for-byte preserved.
- **Existing third-party `UserPromptSubmit` or `Stop` hook**: appended-to, not replaced. Their entry runs; ours runs; both fire.
- **Re-running install**: detects our entries by `HOOK_MARKER = "cast-hook "` prefix; skips re-add.
- **Uninstall**: removes only entries whose `command` starts with the marker; leaves third-party entries verbatim. Empties: empty `hooks[event]` array → key deleted; empty `hooks` dict → key deleted.
- **Atomic write**: `mkstemp + write + os.replace`; `.tmp` cleaned on exception.
- **Project-root detection**: warns (does not block) if cwd lacks `.git`/`.cast`/`pyproject.toml`/`package.json`.
- **Concurrency**: not handled. Matches gstack's stance.

## Files

| Path | Change |
|------|--------|
| `cast-server/cast_server/services/user_invocation_service.py` | NEW — `register()`, `complete(session_id)`. ~50 lines. |
| `cast-server/cast_server/routes/api_agents.py` | EDIT — 2 endpoints, 2 pydantic models. ~30 lines. |
| `cast-server/cast_server/cli/hook_events.py` | NEW — canonical event/subcommand/handler mapping. ~25 lines. |
| `cast-server/cast_server/cli/hook_handlers.py` | NEW — runtime handlers (`user_prompt_start`, `user_prompt_stop`). Stdlib only. ~50 lines. |
| `cast-server/cast_server/cli/hook.py` | NEW — `cast-hook` console_script entry; routes to `hook_events.DISPATCH` or `install_hooks.install`/`uninstall`. ~30 lines. |
| `cast-server/cast_server/cli/install_hooks.py` | NEW — idempotent settings.json injector + uninstaller. Stdlib only. ~120 lines. |
| `cast-server/cast_server/cli/__init__.py` | NEW (empty) — package marker if not already present. |
| `cast-server/cast_server/db/connection.py` | EDIT — add `CREATE INDEX IF NOT EXISTS idx_agent_runs_session_status ON agent_runs(session_id, status)` next to existing index precedent at line 137. |
| `pyproject.toml` | EDIT — add `cast-hook = "cast_server.cli.hook:main"` to `[project.scripts]`. |
| `agents/cast-init/cast-init.md` (or wherever cast-init is defined) | EDIT — add an "Install cast-hook entries" step at the end (`install_hooks.install(project_root)`). Document `--no-hooks` opt-out. |
| `cast-server/tests/test_user_invocation_service.py` | NEW — service unit tests. |
| `cast-server/tests/test_api_agents.py` | EXTEND — 4 new endpoint tests. |
| `cast-server/tests/test_install_hooks.py` | NEW — settings-injection tests with **module-level autouse isolation fixture** (Decision #8). |
| `cast-server/tests/test_cli_hook.py` | NEW — hook handler + CLI dispatch tests with mocked HTTP. |
| `docs/specs/cast-user-invocation-tracking.collab.md` | NEW — spec for the user-invocation lifecycle. |
| `docs/specs/cast-hooks.collab.md` | NEW — **dedicated spec** for the hook-install/uninstall contract (the user-safety surface). |
| `docs/specs/_registry.md` | EDIT — append rows for both new specs. |
| `cast-server/cast_server/models/agent_run.py` | UNCHANGED — confirm no field needed. |
| `cast-server/cast_server/services/agent_service.py` | UNCHANGED — Decision #3 dropped ambient parenting. |
| `.claude/settings.json` (this repo) | UNCHANGED in this repo. The installer writes settings; we test it against tmp project roots, never against this repo's live settings during dev. |

## Implementation order

Each step independently verifiable.

1. **Service + unit tests.** Implement `user_invocation_service.py` (`register`, `complete(session_id)`). Tests use a tmp DB. No HTTP, no hooks. Stop here, all green.
2. **Endpoints.** Wire the two routes. `curl -X POST .../user-invocations -d '{"agent_name":"cast-plan-review","prompt":"/cast-plan-review test","session_id":"S1"}'` returns `{run_id}`; row visible. `POST /complete -d '{"session_id":"S1"}'` closes it; returns `{closed: 1}`.
3. **DB index.** Add `idx_agent_runs_session_status` to `connection.py`. Restart server; verify with `EXPLAIN QUERY PLAN` that the close query uses the index.
4. **Hook events + handlers + console_script.** Add `hook_events.py`, `hook_handlers.py`, `hook.py`, register `cast-hook` in `pyproject.toml`. `pip install -e .`; verify `which cast-hook` and `echo '{"prompt":"/cast-plan-review hi","session_id":"S1"}' | cast-hook user-prompt-start`.
5. **Installer + tests.** Add `install_hooks.py` and `test_install_hooks.py` (with module-level autouse isolation fixture). The tests are the gating bar: third-party preservation (UserPromptSubmit AND Stop, symmetric), malformed-JSON refusal, `OSError`/`PermissionError` paths, atomicity-on-exception, project-marker warning, idempotent re-run, surgical uninstall, round-trip restore. **Delegate: `/cast-pytest-best-practices`** before considering this step done.
6. **Wire into `/cast-init`.** Default ON, `--no-hooks` opt-out. Run `/cast-init` against a tmp project that already has unrelated hooks; verify our entries appear and theirs are byte-for-byte preserved. Then `cast-hook uninstall` against that tmp project; verify ours are gone, theirs remain, empty arrays/keys cleaned.
7. **Spec capture (TWO specs).** See "Spec capture" below. Run only after all preceding steps are green so specs record actual behavior.
8. **End-to-end smoke.** Restart Claude Code in a tmp project. Type `/cast-plan-review`. Verify the row + completed lifecycle. Type a non-`/cast` prompt. Verify no row. Crash-recovery: insert a stale `running` row with the same session_id, fire Stop again, verify the orphan is closed (within 1h window). Run `cast-hook uninstall` — verify hooks gone and Claude Code no longer creates rows on next prompt.

## Spec capture (step 7)

This change has **two distinct contracts** worth locking. Decision #11 splits the spec accordingly.

### Spec A: `docs/specs/cast-user-invocation-tracking.collab.md`

**Invocation:** `/cast-update-spec create cast-user-invocation-tracking`

**Intent (one paragraph):** "Cast-server captures every user-typed `/cast-*` slash command as a top-level `agent_run` row whose `agent_name` matches the slash command. Lifecycle is bracketed by Claude Code's `UserPromptSubmit` and `Stop` hooks. The Stop endpoint closes by `session_id` with a 1-hour staleness window — self-healing for orphans without ghost-running rows. Children of in-turn dispatches are NOT auto-linked to the user-invocation row in v1."

**Linked files:** this plan, `services/user_invocation_service.py`, `cli/hook_handlers.py`, `routes/api_agents.py` (the two endpoints), `db/connection.py` (the index).

**User Stories:**
- **US1:** Slash-command invocation creates a row — `/cast-plan-review` → row with `agent_name="cast-plan-review"`, `status="running"`, `input_params.source="user-prompt"`, `session_id` set, `parent_run_id=null`.
- **US2:** Lifecycle closes — when the assistant turn ends, the row transitions to `status="completed"`, `completed_at` set.
- **US3:** Non-cast prompts are ignored — freeform prompts and non-cast slash commands produce no rows.
- **US4:** Crashed-session orphans self-heal — a Stop firing in a session containing a stale `running` row from a prior crashed turn cleans it up alongside the current row, *only if started within the past hour*.
- **US5:** Multiple invocations per session work — many `/cast-*` invocations in one Claude Code session each get their own row, sequentially opened and closed.
- **US6:** Children stay top-level — agent dispatches that occur during a `/cast-*` turn are NOT auto-linked as children; correlation is by `session_id` + timestamps only.

**Behavior contract:**
- `agent_name` convention: slash command name without the leading slash.
- Discriminator: `input_params.source == "user-prompt"`. No new column.
- Detection regex (hook-side only): `^\s*/(cast-[a-z0-9-]+)`. Server is agnostic to prefix.
- Close-by-session query (Decision #4): `UPDATE agent_runs SET status='completed', completed_at=? WHERE session_id=? AND status='running' AND json_extract(input_params,'$.source')='user-prompt' AND started_at > <now − 1h>`.
- Index: `idx_agent_runs_session_status ON agent_runs(session_id, status)`.
- Stop semantics: `completed` always; v1 does not detect cancellation.
- Endpoint failure semantics: `/complete` with missing/empty `session_id` → `{closed: 0}`, not an error.

**Verification:** cite `tests/test_user_invocation_service.py`, `tests/test_api_agents.py` (the new cases), `tests/test_cli_hook.py`.

**Out of scope:** mirror this plan's "Out of scope" list.

### Spec B: `docs/specs/cast-hooks.collab.md`

**Invocation:** `/cast-update-spec create cast-hooks`

This is the critical user-safety spec. Lead with the polite-citizen framing.

**Intent (one paragraph):** "Cast-server installs Claude Code hooks via the `cast-hook install` command. The installer is a *polite citizen* in the user's `.claude/settings.json` — it is one listener among potentially many. It NEVER replaces or breaks third-party or pre-existing user hooks; it only appends its own entries (idempotent) and surgically removes them on `cast-hook uninstall`. All writes are atomic; malformed JSON refuses to overwrite; permission errors surface a readable message instead of a traceback."

**Linked files:** this plan, `cli/install_hooks.py`, `cli/hook_events.py`, `cli/hook.py`, `pyproject.toml` (`[project.scripts]` entry), reference: `~/workspace/reference_repos/gstack/bin/gstack-settings-hook` (canonical pattern).

**User Stories:**
- **US1: Coexists with third-party `UserPromptSubmit` hooks** — installing into a settings.json that already has a third-party `UserPromptSubmit` entry leaves that entry verbatim; our entry coexists in the same array; both fire on every prompt.
- **US2: Coexists with third-party `Stop` hooks** — symmetric to US1 for Stop.
- **US3: Preserves all unrelated events** — `PostToolUse`, `SubagentStart`, `SessionEnd`, `PreCompact`, etc. are untouched.
- **US4: Idempotent install** — re-running `cast-hook install` is a no-op; never duplicates entries.
- **US5: Surgical uninstall** — `cast-hook uninstall` removes ONLY entries whose `command` starts with `cast-hook ` (the marker). Other entries, other events, and the rest of `settings.json` are byte-for-byte preserved. Newly-empty event arrays are dropped; if `hooks` is now empty, that key is dropped too.
- **US6: Refuses to corrupt malformed settings** — installer aborts with a readable error if `.claude/settings.json` is invalid JSON. Does NOT write. User keeps a chance to inspect/fix.
- **US7: Survives filesystem failures gracefully** — `OSError`/`PermissionError` (read-only fs, disk full, locked file) surfaces a readable message; the `.tmp` file is cleaned up; original settings file is untouched.
- **US8: Atomic on disk** — partial writes never reach the live `settings.json`. mkstemp + write + `os.replace`.
- **US9: Project-aware** — installs to `<project_root>/.claude/settings.json` by default. `--user` flag installs to `~/.claude/settings.json`. Warns (does not block) if cwd lacks `.git`/`.cast`/`pyproject.toml`/`package.json` markers.
- **US10: Single source of truth for hook events** — `cli/hook_events.py` is the only place that knows {event, subcommand, handler}; install-side and runtime-side cannot drift.

**Behavior contract:**
- `HOOK_MARKER = "cast-hook "` (trailing space). Any settings.json `hooks[*].hooks[*].command` starting with this prefix is "ours."
- Hook command shape: `cast-hook <subcommand>`. PATH-resolved. No hardcoded filesystem paths in any user's settings.json.
- Atomic write: `tempfile.mkstemp` + write + `os.replace`. tmp file cleaned on exception (success or failure).
- Failure semantics:
  - Malformed JSON in target → `SystemExit` with readable message; exit non-zero; no write.
  - `OSError`/`PermissionError` → `SystemExit` with readable message naming `--user` as the workaround; exit non-zero.
  - Settings file missing on uninstall → `print "nothing to do"`; exit 0.
- Idempotency marker: any `command` starting with `HOOK_MARKER` is ours. Install dedup, uninstall removal both key off this prefix.
- Concurrency: not handled. Documented limitation.

**Verification:** cite `tests/test_install_hooks.py` (gating coverage). Spec calls out the **module-level autouse isolation fixture** (Decision #8) as a non-negotiable safety property of the test suite.

**Out of scope:**
- File locking on settings.json (matches gstack stance).
- Auto-uninstall on package removal (users explicitly run `cast-hook uninstall`).
- Multi-machine routing.

**Cross-references:** add a back-reference from `cast-user-invocation-tracking.collab.md` → `cast-hooks.collab.md` ("Hook installation contract: see cast-hooks.collab.md") and vice versa.

### After both specs are written

- Confirm `docs/specs/_registry.md` has the two new rows. If not, add manually:
  ```
  | `cast-user-invocation-tracking.collab.md` | cast-user-invocation-tracking | cast-server | User-typed /cast-* slash commands captured as top-level agent_run rows; close-by-session_id with 1h staleness window. Linked plan: `docs/plan/2026-05-01-capture-user-invocations-as-runs.collab.md`. Hook install: see `cast-hooks.collab.md`. | Draft | 1 |
  | `cast-hooks.collab.md`                    | cast-hooks                    | cast-server | Polite-citizen install/uninstall contract for Claude Code settings.json. Additive merge, atomic write, idempotent dedup, surgical uninstall, third-party preservation. Reference pattern: gstack-settings-hook. | Draft | 1 |
  ```
- Run `/cast-spec-checker` against each new spec. Resolve any lint findings.
- Update `cast-delegation-contract.collab.md` (or wherever `trigger_agent` semantics are spec'd) with a back-reference noting that user-invocation rows are now a recognized top-level kind.

## Verification

### Manual end-to-end

After step 8, in a fresh Claude Code session in a **tmp project that already had unrelated hooks** before install:

1. Pre-install: cat existing `.claude/settings.json`. Note any third-party hook entries.
2. Run `cast-hook install` (or `/cast-init` with default `--no-hooks=false`). Verify:
   - Existing hooks preserved byte-for-byte.
   - `UserPromptSubmit` and `Stop` blocks now contain a `cast-hook ...` entry alongside any pre-existing entries.
3. Type `/cast-plan-review some plan path`. Within 1 second:
   - `curl localhost:8005/api/agents/jobs/<run_id>` (or however we lookup) shows `agent_name=cast-plan-review`, `status=running`, `input_params.source=user-prompt`, `session_id` populated, `parent_run_id=null`.
4. After Claude finishes the turn:
   - The user-invocation row has `status=completed`, `completed_at` set.
5. Type a freeform prompt. Confirm no new user-invocation row created.
6. **Self-heal smoke test (orphan cleanup):** before step 7, manually insert a stale `running` row in the same `session_id` (e.g., via `sqlite3` directly), with `started_at = now - 30min`. Type `/cast-plan-review` again. After Stop fires, verify BOTH rows are now `completed` (the orphan + the current one).
7. **Staleness boundary:** repeat step 6 but with `started_at = now - 90min`. After Stop fires, verify the orphan is STILL `running` (older than 1h window) and the current row is `completed`.
8. Run `cast-hook uninstall`. Verify:
   - Our `cast-hook ...` entries removed.
   - Pre-existing third-party entries preserved verbatim.
   - Empty event arrays/`hooks` dict cleaned up.
9. Restart Claude Code. Type `/cast-plan-review`. Confirm no row is created (hooks gone).
10. **Failure-mode probes:**
    - Make `.claude/settings.json` read-only; run `cast-hook install`; expect readable PermissionError message and non-zero exit.
    - Corrupt `.claude/settings.json` to `{not json`; run `cast-hook install`; expect readable JSON parse error and non-zero exit; original file untouched.

### Unit tests (`cast-server/tests/test_user_invocation_service.py`)

```python
def test_register_creates_running_row(tmp_db)
def test_register_input_params_carries_source_and_prompt(tmp_db)
def test_register_session_id_persisted(tmp_db)
def test_complete_marks_running_row_completed(tmp_db)
def test_complete_returns_count_of_rows_closed(tmp_db)
def test_complete_closes_orphans_in_same_session(tmp_db)              # 2 running rows, same session → both close
def test_complete_skips_rows_older_than_staleness_window(tmp_db)      # row started 90min ago stays running
def test_complete_only_touches_user_prompt_rows(tmp_db)               # subprocess-dispatched row with same session_id NOT closed
def test_complete_returns_zero_when_no_session_id(tmp_db)
def test_complete_returns_zero_when_no_matching_running_rows(tmp_db)
```

### API tests (`cast-server/tests/test_api_agents.py`)

```python
def test_open_user_invocation_returns_run_id(client)
def test_open_user_invocation_creates_running_row(client, db)
def test_open_user_invocation_session_id_optional(client, db)
def test_complete_user_invocation_returns_closed_count(client, db)
def test_complete_with_no_session_id_returns_zero(client, db)
def test_complete_does_not_close_subprocess_rows(client, db)            # safety: source filter respected
```

### Hook handler/CLI tests (`cast-server/tests/test_cli_hook.py`)

HTTP layer mocked.

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

### Settings-injection tests (`cast-server/tests/test_install_hooks.py`)

**Module-level autouse isolation fixture (Decision #8) is a non-negotiable safety property.** It monkeypatches `Path.home()` to a tmp dir and forbids any `_settings_path()` resolution outside the tmp sandbox. A runaway test cannot escape and corrupt the developer's real `~/.claude/settings.json`.

```python
# autouse=True, scope="module"
@pytest.fixture(autouse=True)
def _isolate_settings_filesystem(tmp_path_factory, monkeypatch):
    tmp_home = tmp_path_factory.mktemp("home")
    monkeypatch.setattr(Path, "home", lambda: tmp_home)
    # Belt-and-suspenders: a collection hook asserts no install() invocation
    # resolves _settings_path outside tmp_path_factory.getbasetemp().
    yield

# Behavior tests
def test_install_creates_settings_file_when_missing(tmp_project_root)
def test_install_preserves_existing_unrelated_hooks(tmp_project_root)
    # seed PostToolUse + SessionStart user blocks; install; assert byte-for-byte preserved
def test_install_appends_alongside_existing_user_prompt_submit(tmp_project_root)   # third-party UserPromptSubmit
def test_install_appends_alongside_existing_stop(tmp_project_root)                  # third-party Stop (symmetric)
def test_install_is_idempotent(tmp_project_root)                                    # run twice; one entry per event
def test_install_aborts_on_malformed_json(tmp_project_root)                         # SystemExit; file unchanged
def test_install_handles_permission_error_readable_message(tmp_project_root)        # chmod 0o444 then install; SystemExit with readable msg
def test_install_atomic_write_no_partial_on_exception(tmp_project_root, monkeypatch)# json.dumps raises; original untouched, no .tmp
def test_install_warns_when_no_project_markers(tmp_dir_no_markers, capsys)
def test_install_no_warning_when_project_markers_present(tmp_project_root, capsys)
def test_install_user_scope_writes_to_home_settings(tmp_project_root)
def test_uninstall_removes_only_cast_hook_entries(tmp_project_root)
def test_uninstall_preserves_third_party_user_prompt_submit_entry(tmp_project_root)
def test_uninstall_preserves_third_party_stop_entry(tmp_project_root)               # symmetric (Decision #9)
def test_uninstall_deletes_empty_event_arrays(tmp_project_root)
def test_uninstall_deletes_empty_hooks_dict(tmp_project_root)
def test_uninstall_noop_when_settings_file_missing(tmp_project_root)
def test_round_trip_install_then_uninstall_restores_original_shape(tmp_project_root) # JSON-equivalence after re-serialization
```

After green: **`Delegate: /cast-pytest-best-practices`** over all four new test files; act on findings.

## Out of scope

- Capturing freeform (non-slash-command) prompts.
- Capturing other slash skills (`/design-review`, `/ship`, etc.).
- Synthesizing `output.json` for user-invocation rows.
- Capturing Claude Code transcript content into the row (beyond storing `session_id`).
- Distinguishing user-cancelled from completed turns in v1.
- A UI badge marking user-invocation rows in the threaded `/runs` view (cosmetic; follow-up).
- **Ambient parent linking of children** (Decision #3 — deferred; can ship later as a strict additive change, including the allowlist-bypass design that was reviewed and parked).
- File-locking on settings.json writes.
- Auto-uninstall on `cast-server` package uninstall.
- Multi-machine routing.

## Risks and open questions

1. **Hook payload shape** — Claude Code's `UserPromptSubmit` and `Stop` payload formats must include `prompt` and `session_id` respectively. Verify against current harness docs at impl step 4 (a logging stub piped to `/tmp/hook-test.log` is enough). Plan assumes this; if `Stop` payload omits `session_id`, fall back to a marker-file design (which we've already worked through and parked).
2. **CAST_PORT discovery** — handler reads `CAST_PORT` env var, defaults to `8005` (matches `bin/cast-server`). If the server isn't running, the hook silently no-ops. Acceptable.
3. **PATH resolution at hook-fire time** — `cast-hook` works only if it's on the user's PATH at the time Claude Code spawns the hook subprocess. uv/pipx installs put it on PATH; a bare `python -m cast_server` install path may not. Installer detects `cast-hook` on PATH at install time and warns loudly if missing.
4. **Hook event names** — Claude Code currently uses `UserPromptSubmit` and `Stop`. If those names change in a future release, settings.json entries silently stop firing. Defer concrete check until we hit the problem.
5. **`cast-init` install timing** — when a user runs `/cast-init` for the first time, Claude Code is already running; new hooks don't take effect until the user restarts the session. Surface this in cast-init's final output: "Restart Claude Code to activate the hooks."
6. **Concurrent settings.json writers** — gstack accepts this risk; we follow suit. If it ever bites, file-locking via `fcntl.flock` is the v2 fix.
7. **Two prompts in one Claude Code turn** — Claude Code alternates user/assistant strictly per turn, so this shouldn't happen. If multi-prompt turn semantics ever ship, the second `register` would create a second running row, and Stop's session-scope close would close both. Acceptable behavior — better than orphaning one.
8. **Session_id reuse across separate sessions** — currently uuid-grade so this should never happen. The 1h staleness window (Decision #5) protects against the unlikely case.

## Reference

- Run model: `cast-server/cast_server/models/agent_run.py:6-44`
- `create_agent_run`: `cast-server/cast_server/services/agent_service.py:347`
- `update_agent_run`: `cast-server/cast_server/services/agent_service.py:369`
- `get_agent_run`: `cast-server/cast_server/services/agent_service.py:389`
- `get_connection`: `cast-server/cast_server/db/connection.py`
- Existing trigger endpoint: `cast-server/cast_server/routes/api_agents.py:55`
- Existing index precedent: `cast-server/cast_server/db/connection.py:137` (idx_error_memories_agent — same pattern for the new index)
- `bin/cast-server`: defaults `CAST_PORT=8005`
- **Settings injection pattern (canonical reference):** `~/workspace/reference_repos/gstack/bin/gstack-settings-hook` — atomic `.tmp + rename`, idempotent dedup by command substring, surgical uninstall.
- Spec template: `templates/cast-spec.template.md`
- Spec registry: `docs/specs/_registry.md`

## Decisions

- **2026-05-01T00:00:00Z — How should ambient parenting (auto-linking children of the user-typed run) interact with the existing allowed_delegations allowlist?** — Decision: Drop ambient parenting entirely from v1. Rationale: per-user direction at review time; we get the audit/visibility win from the user-invocation row alone; can add ambient linking later as a strict additive change (with the allowlist-bypass design already worked through and parked).
- **2026-05-01T00:00:00Z — Where should the hook entry-point and install/uninstall commands live (binary surface)?** — Decision: New `cast-hook` console_script with subcommands (`user-prompt-start | user-prompt-stop | install | uninstall`). Rationale: keeps daemon binary `cast-server` a pure uvicorn launcher; zero coupling between daemon lifecycle and hook tooling; PATH-resolved (no hardcoded paths in any user's settings).
- **2026-05-01T00:00:00Z — How should the Stop hook know which user-invocation row to close?** — Decision: Match by `session_id` with 1-hour staleness window; use `json_extract(input_params, '$.source')` for the discriminator. No marker file. Rationale: drops filesystem state; self-healing for orphans; 1h window prevents future session_id collisions from spuriously completing ancient rows; `json_extract` is more correct than `LIKE` substring matching.
- **2026-05-01T00:00:00Z — Single source of truth for the {Claude-Code event → cast-hook subcommand → handler function} mapping?** — Decision: One canonical list in `cast_server/cli/hook_events.py`; both install_hooks.py and hook.py import from it. Rationale: drift between install-side and runtime-side becomes structurally impossible; adding a hook event = one line in one file.
- **2026-05-01T00:00:00Z — How carefully should the installer handle filesystem failure modes beyond malformed JSON?** — Decision: Catch `OSError`/`PermissionError`, surface readable message naming `--user` as workaround, clean up `.tmp`, exit non-zero. Rationale: tracebacks-as-error-UX is unacceptable for a user-facing install path; common failure modes (read-only fs, perm denied, disk full) deserve actionable messages.
- **2026-05-01T00:00:00Z — What should `cast-hook install` do when invoked from a directory that doesn't look like a project?** — Decision: Detect markers (`.git`/`.cast`/`pyproject.toml`/`package.json`); warn if absent; proceed. Rationale: never block automation (e.g., /cast-init); /cast-init always passes explicit project_root so the warning never fires from the supported install path; bare CLI users get an actionable hint without losing the ergonomic of `cd ~/myproject && cast-hook install`.
- **2026-05-01T00:00:00Z — When Stop fires for session S and finds 2+ running user-invocation rows in that session (orphans from a prior crash + the current row), what closes?** — Decision: Close all running rows for the session within a 1-hour staleness window. Rationale: self-healing for fresh orphans; ancient orphans (>1h) stay running and require manual cleanup, hedging against the unlikely case of session_id reuse across separate Claude Code sessions.
- **2026-05-01T00:00:00Z — How strict should test isolation be for the install/uninstall test suite?** — Decision: Module-level autouse fixture monkeypatches Path.home() and forbids cwd writes outside tmp; collection hook asserts `_settings_path()` cannot resolve outside the tmp sandbox. Rationale: a runaway test that nukes the developer's real `~/.claude/settings.json` is catastrophic; structural prevention beats author discipline.
- **2026-05-01T00:00:00Z — Cover third-party Stop coexistence symmetrically with the existing third-party UserPromptSubmit coverage?** — Decision: Add `test_install_preserves_third_party_stop_entry` and `test_uninstall_preserves_third_party_stop_entry`. Rationale: asymmetric coverage drifts; UserPromptSubmit and Stop are equally meaningful third-party event surfaces.
- **2026-05-01T00:00:00Z — Index strategy and discriminator for the Stop close-by-session query?** — Decision: Add `idx_agent_runs_session_status` on (session_id, status); query uses `json_extract(input_params, '$.source')` not `LIKE`. Rationale: Stop fires once per turn; without the index, every Stop scans the whole agent_runs table — painful as it grows. `json_extract` is the right SQLite-native discriminator over fragile substring matching. Mirrors the threaded-tree plan's `idx_agent_runs_parent` precedent.
- **2026-05-01T00:00:00Z — Should the spec be split into separate documents for the user-invocation lifecycle vs. the hook-install contract?** — Decision: Yes — two specs: `cast-user-invocation-tracking.collab.md` (the lifecycle) and `cast-hooks.collab.md` (the install/uninstall contract, leading with the polite-citizen / never-override-third-party framing). Rationale: hook installation is critical user-safety surface that deserves its own spec independent of any one feature using it; future cast-server features that add hooks can reference cast-hooks.collab.md as the contract.
