# Sub-phase 4: Server-log RotatingFileHandler (`server.log` 10MB × 5)

> **Pre-requisite:** Read `docs/execution/cast-server-first-run-launch/_shared_context.md` before starting.

## Objective

Bound the long-running cast-server's disk footprint by configuring Python `logging` with `RotatingFileHandler` writing to `~/.cache/diecast/server.log` (10 MB × 5 backups). The auto-launched daemon (sp8) writes to `bootstrap.log` for pre-logging stdout/stderr; this sub-phase owns `server.log` for structured logs. Decision #13 — two distinct files for two distinct phases — eliminates the rotation-vs-redirect conflict.

## Dependencies

- **Requires completed:** sp1 (port seam — establishes the `cast_server.config` constants pattern this sub-phase extends; also avoids merge-conflict on the same file).
- **Assumed codebase state:** `cast-server/cast_server/config.py` has `DEFAULT_CAST_PORT` / `DEFAULT_CAST_HOST` / `DEFAULT_CAST_BIND_HOST` constants from sp1. Cast-server's logging today either uses uvicorn defaults or a basic `logging.basicConfig` (verify before editing).

## Scope

**In scope:**
- Configure `RotatingFileHandler` writing to `~/.cache/diecast/server.log` (10 MB max, 5 backups).
- Apply the handler to root logger AND `uvicorn.error` / `uvicorn.access` loggers.
- Ensure `~/.cache/diecast/` exists (`mkdir(parents=True, exist_ok=True)` at logging setup).

**Out of scope (do NOT do these):**
- `bootstrap.log` redirect — sp8 owns the `nohup` line that writes to it.
- The launch step (`step8_launch_and_open_browser`) — sp8.
- Any port/host changes — sp1 owns those.
- Logging the *content* of cast-server (formatting, levels, structured fields) — keep current format; only add the handler.

## Files to Create/Modify

| File | Action | Current state |
|------|--------|---------------|
| `cast-server/cast_server/config.py` | Modify | Has the new `DEFAULT_CAST_*` constants from sp1; no `RotatingFileHandler` config yet. |
| `cast-server/cast_server/main.py` | Possibly modify | If cast-server's logging is initialized in `main.py` rather than `config.py`, add the handler attach there. (Read both first; pick the right home.) |

## Detailed Steps

### Step 4.1: Locate where logging is initialized

Search for `logging.basicConfig`, `getLogger`, `dictConfig`, or any custom logger setup:

```bash
grep -rn 'logging\.\(basicConfig\|getLogger\|dictConfig\)' /data/workspace/diecast/cast-server/cast_server/
```

Two likely outcomes:
- **Logging is set up in `config.py`** (or a side-effect of importing it): add the `RotatingFileHandler` there.
- **Logging is set up in `main.py`** at app construction: add it there.
- **No central setup**: add a small module like `cast_server/logging_setup.py` and import it from `main.py`. Don't sprinkle `basicConfig` calls across files.

### Step 4.2: Add the handler config

```python
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path.home() / ".cache" / "diecast"
LOG_DIR.mkdir(parents=True, exist_ok=True)

_handler = RotatingFileHandler(
    LOG_DIR / "server.log",
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
)
_handler.setFormatter(logging.Formatter(
    "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
))

# Apply to root and uvicorn loggers so framework + app + access logs all rotate.
for logger_name in ("", "uvicorn", "uvicorn.error", "uvicorn.access"):
    lg = logging.getLogger(logger_name)
    lg.addHandler(_handler)
    if not lg.level:
        lg.setLevel(logging.INFO)
```

If `cast_server.config` already exports a logger or handler, follow that pattern. Match existing format strings if a custom one is in use.

### Step 4.3: Ensure single-attachment idempotency

If the logging setup module can be imported twice (test discovery, multi-worker reload), the handler will attach twice and every message logs twice. Guard:

```python
_HANDLER_ATTACHED = False

def _attach_once():
    global _HANDLER_ATTACHED
    if _HANDLER_ATTACHED:
        return
    # ... existing handler setup ...
    _HANDLER_ATTACHED = True

_attach_once()
```

Or, more idiomatically, check that `_handler not in lg.handlers` before appending.

### Step 4.4: Confirm `bootstrap.log` is NOT touched

Decision #13 forbids two writers on `server.log`. This sub-phase must not write to `bootstrap.log`, open it, lock it, or rotate it. `bootstrap.log` is owned exclusively by sp8's `nohup` redirect. Add a comment in the logging setup explaining the split:

```python
# bootstrap.log is owned by setup's `nohup ... >bootstrap.log 2>&1` redirect
# (captures uvicorn pre-logging stdout/stderr). This module owns server.log
# and rotates it; the two files do not share writers. — Decision #13
```

## Verification

### Automated Tests (permanent)
- No new automated test required. `uv run pytest` continues to pass.
  - Optional: a smoke test that imports the logging module twice and asserts the handler is only attached once. Skip if it adds noise.

### Validation Scripts (temporary)

```bash
# 1. Confirm server.log exists and rotates after 10MB:
ls -la ~/.cache/diecast/
# Run cast-server, log >10MB by hitting an endpoint in a tight loop:
for i in $(seq 1 20000); do curl -s http://localhost:8005/api/agents/runs?status=running >/dev/null; done
ls -la ~/.cache/diecast/server.log* 
# Expect: server.log + server.log.1 (and possibly .2 etc., capped at .5)

# 2. Confirm bootstrap.log is untouched by this sub-phase:
# (sp8 will create it; this sub-phase must not.)
[ ! -e ~/.cache/diecast/bootstrap.log ] && echo "OK: bootstrap.log not created by sp4"

# 3. Two writers? lsof check post-launch:
lsof ~/.cache/diecast/server.log
# Expect: only the cast-server Python process.
```

### Manual Checks
- Tail `server.log` while running cast-server — confirm structured log lines appear (uvicorn access logs, app logs, errors).
- Inspect rotated files — `server.log.5` is dropped when a sixth rotation occurs.
- Disk footprint stays bounded at ~60 MB (10 MB × 6 files at peak).

### Success Criteria
- [ ] `RotatingFileHandler` configured with `maxBytes=10*1024*1024`, `backupCount=5`.
- [ ] Handler attached to root + uvicorn loggers.
- [ ] `~/.cache/diecast/` is created if missing.
- [ ] Re-import of the logging setup is idempotent (handler not attached twice).
- [ ] `bootstrap.log` is not touched by this sub-phase.
- [ ] `uv run pytest` still green.

## Execution Notes

- If the host has `~/.cache/diecast/` symlinked elsewhere (chezmoi / dotfiles), `mkdir(exist_ok=True)` handles the case gracefully.
- Do NOT use `WatchedFileHandler` — it doesn't rotate by size and is meant for external rotation (logrotate). `RotatingFileHandler` is correct here.
- Cross-platform: `RotatingFileHandler` works identically on macOS and Linux. The plan calls out cross-platform parity explicitly.
- If sp1's edits to `config.py` haven't landed yet (out-of-order execution), do not import the new `DEFAULT_CAST_*` constants — they're not needed here. This sub-phase only touches the logging block.

**Spec-linked files:** None.
