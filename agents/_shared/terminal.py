"""Shared terminal resolver for cast-* agents AND cast-server.

Resolution order:
    1. $CAST_TERMINAL (preferred, project-scoped)
    2. $TERMINAL (POSIX convention)
    3. ~/.cast/config.yaml:terminal_default
    4. raise ResolutionError pointing at supported-terminals docs

Returns: ResolvedTerminal(command, args, flags).

NEVER use shell=True with the returned command. Pass `args=[command, *args]`
as a list to subprocess.Popen — $CAST_TERMINAL is shell-expandable, and
shell=True would open an injection surface.
"""
from __future__ import annotations

import os
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


_SUPPORTED: dict[str, dict[str, str]] = {
    "ptyxis":         {"new_tab_flag": "--new-window",          "cwd_flag": "--working-directory="},  # diecast-lint: ignore-line
    "gnome-terminal": {"new_tab_flag": "--tab",                  "cwd_flag": "--working-directory="},
    "kitty":          {"new_tab_flag": "@launch --type=tab",     "cwd_flag": "--directory="},
    "alacritty":      {"new_tab_flag": "",                       "cwd_flag": "--working-directory"},
    "iterm":          {"new_tab_flag": "",                       "cwd_flag": ""},
    "terminal":       {"new_tab_flag": "",                       "cwd_flag": ""},
}


class ResolutionError(RuntimeError):
    """Raised when no terminal can be resolved.

    The error message links to docs/reference/supported-terminals.md and
    names all three resolution sources so the user can fix it.
    """


@dataclass(frozen=True)
class ResolvedTerminal:
    command: str
    args: list[str] = field(default_factory=list)
    flags: dict[str, str] = field(default_factory=dict)


def _config_default(config_path: Optional[Path] = None) -> Optional[str]:
    path = config_path or Path.home() / ".cast" / "config.yaml"
    if not path.exists():
        return None
    try:
        cfg = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(cfg, dict):
        return None
    value = cfg.get("terminal_default")
    return value if isinstance(value, str) and value else None


def resolve_terminal(config_path: Optional[Path] = None) -> ResolvedTerminal:
    """Resolve the user's preferred terminal via the documented fallback chain.

    Args:
        config_path: Optional explicit path to a config file. When omitted,
            falls back to ``~/.cast/config.yaml``. Tests pass a tmp path.

    Returns:
        ResolvedTerminal with the executable name, any extra args parsed from
        the env-var/config string, and the per-terminal flag preset (if known).

    Raises:
        ResolutionError: if no source provides a terminal name. The message
            links to docs/reference/supported-terminals.md.
    """
    raw = (
        os.environ.get("CAST_TERMINAL")
        or os.environ.get("TERMINAL")
        or _config_default(config_path)
    )
    if not raw:
        raise ResolutionError(
            "No terminal configured. Set $CAST_TERMINAL, $TERMINAL, or "
            "terminal_default in ~/.cast/config.yaml. "
            "See docs/reference/supported-terminals.md for the supported list."
        )
    parts = shlex.split(raw)
    cmd, *args = parts
    flags = dict(_SUPPORTED.get(Path(cmd).name, {}))
    return ResolvedTerminal(command=cmd, args=args, flags=flags)


def needs_first_run_setup(config_path: Optional[Path] = None) -> bool:
    """Return True iff /cast-setup should prompt the user on this run.

    True when neither $CAST_TERMINAL nor $TERMINAL is set AND
    ~/.cast/config.yaml lacks a non-empty terminal_default. The /cast-setup
    script (Phase 4) calls this helper to decide whether to prompt.
    """
    if os.environ.get("CAST_TERMINAL") or os.environ.get("TERMINAL"):
        return False
    return _config_default(config_path) is None
