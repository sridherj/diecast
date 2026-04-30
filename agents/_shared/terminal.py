"""Shared terminal resolver for cast-* agents AND cast-server.

Resolution order (during dispatch — never auto-detects):
    1. $CAST_TERMINAL (preferred, project-scoped)
    2. $TERMINAL (POSIX convention)
    3. ~/.cast/config.yaml: terminal_default (canonical) or terminal (alias)
    4. raise ResolutionError pointing at /cast-doctor (shell fallback:
       bin/cast-doctor --fix-terminal)

Returns: ResolvedTerminal(command, args, flags).

NEVER use shell=True with the returned command. Pass `args=[command, *args]`
as a list to subprocess.Popen — $CAST_TERMINAL is shell-expandable, and
shell=True would open an injection surface.

Auto-detection (`_autodetect`) is consumed only by `bin/cast-doctor
--fix-terminal` at first-run setup. `resolve_terminal()` does NOT call
`_autodetect()` — silent fallback during dispatch is forbidden.
"""
from __future__ import annotations

import os
import platform
import shlex
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import yaml


_SUPPORTED: dict[str, dict[str, str]] = {
    "ptyxis":         {"new_tab_flag": "--new-window",          "cwd_flag": "--working-directory="},  # diecast-lint: ignore-line
    "gnome-terminal": {"new_tab_flag": "--tab",                  "cwd_flag": "--working-directory="},
    "kitty":          {"new_tab_flag": "@launch --type=tab",     "cwd_flag": "--directory="},
    "alacritty":      {"new_tab_flag": "",                       "cwd_flag": "--working-directory"},
    "iterm":          {"new_tab_flag": "",                       "cwd_flag": ""},
    "terminal":       {"new_tab_flag": "",                       "cwd_flag": ""},
}


# Linux probe order — favors GNOME stack, then misc tabbed terminals.
# Re-ordered at probe time per $XDG_CURRENT_DESKTOP.
_LINUX_PROBE_ORDER: tuple[str, ...] = tuple(
    k for k in _SUPPORTED if k not in ("iterm", "terminal")
)


class ResolutionError(RuntimeError):
    """Raised when no terminal can be resolved.

    The error message names every resolution source actually checked and
    points the user at `/cast-doctor` (with `bin/cast-doctor --fix-terminal`
    as the shell fallback) and docs/reference/supported-terminals.md.
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
    # Accept both keys for back-compat. `terminal_default` is canonical and wins
    # when both are present; `terminal:` is the alias originally written by
    # `cast init` and the docs — the mismatch caused a misleading 30s timeout
    # before this fix.
    for key in ("terminal_default", "terminal"):
        value = cfg.get(key)
        if isinstance(value, str) and value:
            return value
    return None


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
            names every source checked and points at ``/cast-doctor`` (with
            ``bin/cast-doctor --fix-terminal`` as the shell fallback).
    """
    cast_term = os.environ.get("CAST_TERMINAL")
    sys_term = os.environ.get("TERMINAL")
    cfg_term = _config_default(config_path)

    raw = cast_term or sys_term or cfg_term
    if not raw:
        cfg_path = config_path or Path.home() / ".cast" / "config.yaml"
        cast_state = f"set: {cast_term}" if cast_term else "unset"
        sys_state = f"set: {sys_term}" if sys_term else "unset"
        cfg_state = (
            "key 'terminal_default' missing"
            if cfg_path.exists()
            else "file missing — would read key 'terminal_default'"
        )
        msg = (
            "no terminal configured.\n"
            f"  tried: $CAST_TERMINAL ({cast_state}), "
            f"$TERMINAL ({sys_state}),\n"
            f"         {cfg_path} ({cfg_state}).\n"
            "  fix:   run `/cast-doctor` from inside Claude Code to auto-detect and configure\n"
            "         (or `bin/cast-doctor --fix-terminal` from a shell as fallback),\n"
            "         or set $CAST_TERMINAL=<your-terminal> manually.\n"
            "         See docs/reference/supported-terminals.md."
        )
        raise ResolutionError(msg)
    parts = shlex.split(raw)
    cmd, *args = parts
    flags = dict(_SUPPORTED.get(Path(cmd).name, {}))
    return ResolvedTerminal(command=cmd, args=args, flags=flags)


def needs_first_run_setup(config_path: Optional[Path] = None) -> bool:
    """Return True iff /cast-setup should prompt the user on this run.

    True when neither $CAST_TERMINAL nor $TERMINAL is set AND
    ~/.cast/config.yaml lacks a non-empty terminal_default/terminal value.
    The /cast-setup script (Phase 4) calls this helper to decide whether to
    prompt.
    """
    if os.environ.get("CAST_TERMINAL") or os.environ.get("TERMINAL"):
        return False
    return _config_default(config_path) is None


def _autodetect(
    *,
    system: Optional[str] = None,
    desktop: Optional[str] = None,
    iterm_app_path: Path = Path("/Applications/iTerm.app"),
    which: Callable[[str], Optional[str]] = shutil.which,
) -> list[str]:
    """Return ordered candidates from `_SUPPORTED.keys()` available on this host.

    Consumed exclusively by `bin/cast-doctor --fix-terminal` at first-run
    setup. `resolve_terminal()` does NOT call this helper — auto-detect during
    dispatch would re-introduce the silent-fallback bug this fix removes.

    Args:
        system: Override `platform.system()`. Tests inject "Darwin" / "Linux".
        desktop: Override `$XDG_CURRENT_DESKTOP`. Tests inject "GNOME" / "KDE".
        iterm_app_path: Override iTerm.app probe path (macOS only).
        which: Override `shutil.which`. Tests inject a fake.

    Returns:
        Ordered candidate keys from `_SUPPORTED`. Empty list when nothing
        matches. First entry is the recommended default; caller (cast-doctor)
        decides whether to confirm-and-write (single candidate) or prompt
        (multiple).
    """
    sys_name = system or platform.system()
    if sys_name == "Darwin":
        candidates: list[str] = []
        if iterm_app_path.exists():
            candidates.append("iterm")
        candidates.append("terminal")  # always present on macOS
        return candidates

    # Linux (and BSD, WSL — anything non-Darwin).
    desktop = desktop if desktop is not None else os.environ.get("XDG_CURRENT_DESKTOP", "")
    desktop = desktop.upper()
    order: list[str] = list(_LINUX_PROBE_ORDER)
    if "GNOME" in desktop:
        # ptyxis already first; gnome-terminal already second — keep as-is.  # diecast-lint: ignore-line
        pass
    elif "KDE" in desktop and "konsole" in _SUPPORTED:
        # konsole bumps to front when KDE is detected (only when konsole is in
        # _SUPPORTED — currently it is not, so this branch is dormant).
        order.remove("konsole")
        order.insert(0, "konsole")
    return [name for name in order if which(name) is not None]
