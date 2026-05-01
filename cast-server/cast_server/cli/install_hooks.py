"""Idempotent, polite-citizen settings.json injector / uninstaller.

Writes/removes the cast-hook entries in `.claude/settings.json` *alongside* any
third-party hooks already present. Never overrides or replaces foreign entries.
Atomic write via tempfile + os.replace so a crash mid-write cannot corrupt the
file. See `docs/specs/cast-hooks.collab.md` (sp7) for the locked behaviour.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from cast_server.cli.hook_events import HOOK_EVENTS, COMMAND_FOR_EVENT

HOOK_MARKER = "cast-hook "
HOOK_TIMEOUT_SECONDS = 3
PROJECT_MARKERS = (".git", ".cast", "pyproject.toml", "package.json")


def _settings_path(user_scope: bool, project_root: Path) -> Path:
    if user_scope:
        return Path.home() / ".claude" / "settings.json"
    return project_root / ".claude" / "settings.json"


def _looks_like_project_root(p: Path) -> bool:
    return any((p / marker).exists() for marker in PROJECT_MARKERS)


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"cast-hook: refusing to overwrite malformed settings.json at "
            f"{path}: {exc}. Fix or remove the file and retry."
        )


def _atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp: Path | None = None
    try:
        fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
        tmp = Path(tmp_name)
        with os.fdopen(fd, "w") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
        os.replace(tmp, path)
    except (OSError, PermissionError) as exc:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
        raise SystemExit(
            f"cast-hook: cannot write {path}: {exc}. "
            f"Try `cast-hook install --user` to write to ~/.claude/settings.json instead."
        )
    except BaseException:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
        raise


def _entry_is_ours(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    inner = entry.get("hooks")
    if not isinstance(inner, list):
        return False
    for h in inner:
        if isinstance(h, dict):
            cmd = h.get("command", "")
            if isinstance(cmd, str) and cmd.startswith(HOOK_MARKER):
                return True
    return False


def install(project_root: Path, user_scope: bool = False) -> int:
    if not user_scope and not _looks_like_project_root(project_root):
        print(
            f"cast-hook: warning: {project_root} does not look like a project root "
            f"(no {', '.join(PROJECT_MARKERS)}). Installing anyway.",
            file=sys.stderr,
        )

    path = _settings_path(user_scope, project_root)
    settings = _load(path)
    hooks = settings.setdefault("hooks", {})

    installed: list[str] = []
    skipped: list[str] = []
    for event, _sub, _handler in HOOK_EVENTS:
        cmd = COMMAND_FOR_EVENT[event]
        bucket = hooks.setdefault(event, [])
        if not isinstance(bucket, list):
            raise SystemExit(
                f"cast-hook: settings.json hooks.{event} is not a list "
                f"(got {type(bucket).__name__}); refusing to modify."
            )
        if any(_entry_is_ours(e) for e in bucket):
            skipped.append(event)
            continue
        bucket.append({
            "hooks": [{"type": "command", "command": cmd, "timeout": HOOK_TIMEOUT_SECONDS}]
        })
        installed.append(event)

    _atomic_write(path, settings)

    if installed:
        print(f"cast-hook: installed entries for {', '.join(installed)} in {path}")
    if skipped:
        print(f"cast-hook: already installed for {', '.join(skipped)} in {path}")
    return 0


def uninstall(project_root: Path, user_scope: bool = False) -> int:
    path = _settings_path(user_scope, project_root)
    if not path.exists():
        print(f"cast-hook: nothing to do — {path} does not exist.")
        return 0

    settings = _load(path)
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        print(f"cast-hook: no hooks block in {path}; nothing to remove.")
        return 0

    removed: list[str] = []
    for event, _sub, _handler in HOOK_EVENTS:
        bucket = hooks.get(event)
        if not isinstance(bucket, list):
            continue
        kept = [e for e in bucket if not _entry_is_ours(e)]
        if len(kept) != len(bucket):
            removed.append(event)
        if kept:
            hooks[event] = kept
        else:
            del hooks[event]

    if not hooks:
        del settings["hooks"]

    _atomic_write(path, settings)
    if removed:
        print(f"cast-hook: removed entries for {', '.join(removed)} from {path}")
    else:
        print(f"cast-hook: no cast-hook entries found in {path}")
    return 0
