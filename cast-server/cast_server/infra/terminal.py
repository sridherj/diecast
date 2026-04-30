"""Vendored terminal resolver for cast-server.

Mirrors the interface of ``agents/_shared/terminal.py`` so cast-server can
honor the user's $CAST_TERMINAL preference without depending on the agents
import path.

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
    """Raised when no terminal can be resolved."""


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
    """Resolve the user's preferred terminal via the documented fallback chain."""
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
