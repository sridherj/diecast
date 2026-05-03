# SPDX-License-Identifier: Apache-2.0
"""Stdlib-only prerequisite checker — Python replacement for ``bin/cast-doctor``.

This module implements the same diagnostic checks, exit-code contract, and
``--json`` output shape as the original bash ``bin/cast-doctor``.  It relies
exclusively on the Python standard library so it can run before ``uv sync``
installs project dependencies.

Imported terminal metadata (the ``_SUPPORTED`` table and
``_LINUX_PROBE_ORDER``) is loaded from ``agents/_shared/terminal.py`` via
a bootstrap-safe helper that does not require PyYAML at import time.

Public API
----------
* ``run_doctor(flags)`` — execute all checks and emit output.
* ``run_fix_terminal(...)`` — interactive terminal setup flow.
* ``main(argv)`` — CLI entry point called by ``bin/cast-doctor``.
"""
from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from cast_server.bootstrap.common import is_dry_run


# ── Bootstrap-safe terminal table import ───────────────────────────
# agents/_shared/terminal.py is updated to expose _SUPPORTED and
# _LINUX_PROBE_ORDER without requiring PyYAML at import time.  We add
# the agents directory to sys.path so the import works even before the
# package is installed.

def _load_terminal_table() -> tuple[dict, tuple]:
    """Load the supported-terminals table and Linux probe order.

    Returns a ``(supported_dict, linux_probe_order)`` tuple.  Falls back
    to a hardcoded list when the import fails (e.g., broken Python env).

    Returns:
        Tuple of (supported terminals dict, linux probe order tuple).
    """
    try:
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        agents_parent = str(repo_root)
        if agents_parent not in sys.path:
            sys.path.insert(0, agents_parent)
        from agents._shared.terminal import (  # type: ignore[import-untyped]
            _SUPPORTED,
            _LINUX_PROBE_ORDER,
        )
        return dict(_SUPPORTED), tuple(_LINUX_PROBE_ORDER)
    except Exception:
        # Fallback — matches the keys in terminal.py at time of writing.
        _fb: dict[str, dict[str, str]] = {
            "ptyxis": {}, "gnome-terminal": {}, "konsole": {},
            "kitty": {}, "alacritty": {}, "iterm": {}, "terminal": {},
        }
        _lo = tuple(k for k in _fb if k not in ("iterm", "terminal"))
        return _fb, _lo


_SUPPORTED, _LINUX_PROBE_ORDER = _load_terminal_table()


# ── Finding accumulators ───────────────────────────────────────────

class Findings:
    """Accumulator for red / yellow / green diagnostic findings.

    Attributes:
        red: List of RED (blocking) finding messages.
        yellow: List of YELLOW (warning) finding messages.
        green: List of GREEN (ok) finding messages.
    """

    def __init__(self) -> None:
        self.red: list[str] = []
        self.yellow: list[str] = []
        self.green: list[str] = []

    def note_red(self, msg: str) -> None:
        """Add a RED finding."""
        self.red.append(msg)

    def note_yellow(self, msg: str) -> None:
        """Add a YELLOW finding."""
        self.yellow.append(msg)

    def note_green(self, msg: str) -> None:
        """Add a GREEN finding."""
        self.green.append(msg)

    def has_red(self) -> bool:
        """Return True when at least one RED finding exists."""
        return len(self.red) > 0

    def to_dict(self) -> dict[str, list[str]]:
        """Return the JSON-serialisable ``{red, yellow, green}`` shape."""
        return {"red": list(self.red), "yellow": list(self.yellow), "green": list(self.green)}


# ── Version helpers ────────────────────────────────────────────────

def _version_ge(have: str, want: str) -> bool:
    """Return True when semantic version *have* >= *want*.

    Compares dot-separated integer segments left to right.  Missing
    segments are treated as zero.

    Args:
        have: Version string like ``"3.11.5"``.
        want: Minimum required version like ``"3.11"``.

    Returns:
        ``True`` when *have* >= *want*.
    """
    def _ints(v: str) -> list[int]:
        return [int(re.sub(r"[^0-9]", "", s) or "0") for s in v.split(".")]
    a, b = _ints(have), _ints(want)
    for i in range(max(len(a), len(b))):
        av = a[i] if i < len(a) else 0
        bv = b[i] if i < len(b) else 0
        if av > bv:
            return True
        if av < bv:
            return False
    return True


def _extract_version(text: str) -> Optional[str]:
    """Extract the first ``X.Y`` or ``X.Y.Z`` version from *text*.

    Args:
        text: Output from a ``--version`` command.

    Returns:
        The version string, or ``None`` if no match is found.
    """
    m = re.search(r"[0-9]+\.[0-9]+(?:\.[0-9]+)?", text)
    return m.group(0) if m else None


# ── OS-aware install hints ─────────────────────────────────────────

def _install_hint_python3() -> str:
    """Return an OS-appropriate install command for Python 3.11+."""
    if platform.system() == "Darwin":
        return "brew install python@3.11"
    if platform.system() == "Linux":
        try:
            with open("/etc/os-release") as f:
                os_release = f.read()
        except OSError:
            return "install python >= 3.11 via your package manager"
        lower = os_release.lower()
        if "debian" in lower or "ubuntu" in lower:
            return "sudo apt install python3.11"
        if "rhel" in lower or "fedora" in lower or "centos" in lower:
            return "sudo dnf install python3.11"
        if "arch" in lower:
            return "sudo pacman -S python"
    return "install python >= 3.11 via your package manager"


def _install_hint_tmux() -> str:
    """Return an OS-appropriate install command for tmux."""
    if platform.system() == "Darwin":
        return "brew install tmux"
    if platform.system() == "Linux":
        try:
            with open("/etc/os-release") as f:
                os_release = f.read()
        except OSError:
            return "install tmux via your package manager"
        lower = os_release.lower()
        if "debian" in lower or "ubuntu" in lower:
            return "sudo apt install tmux"
        if "rhel" in lower or "fedora" in lower or "centos" in lower:
            return "sudo dnf install tmux"
        if "arch" in lower:
            return "sudo pacman -S tmux"
    return "install tmux via your package manager"


# ── Individual checks ──────────────────────────────────────────────

def check_python3(f: Findings) -> None:
    """Check that python3 >= 3.11 is available."""
    python = shutil.which("python3")
    if not python:
        f.note_red(
            f"python3 not found (need >= 3.11). Install: {_install_hint_python3()}"
        )
        return
    try:
        raw = subprocess.run(
            [python, "-c",
             "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except Exception:
        raw = ""
    ver = _extract_version(raw)
    if ver and _version_ge(ver, "3.11"):
        f.note_green(f"python3 {ver}")
    else:
        f.note_red(
            f"python3 {ver or 'unknown'} found (need >= 3.11). "
            f"Install: {_install_hint_python3()}"
        )


def check_tmux(f: Findings) -> None:
    """Check that tmux is available."""
    if not shutil.which("tmux"):
        f.note_red(
            f"tmux not found (required by the dispatcher). Install: {_install_hint_tmux()}"
        )
        return
    try:
        raw = subprocess.run(
            ["tmux", "-V"], capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except Exception:
        raw = ""
    ver = _extract_version(raw)
    f.note_green(f"tmux {ver or 'present'}")


def check_uv(f: Findings) -> None:
    """Check that uv >= 0.4.0 is available."""
    if not shutil.which("uv"):
        f.note_red("uv not found. Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
        return
    try:
        raw = subprocess.run(
            ["uv", "--version"], capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except Exception:
        raw = ""
    ver = _extract_version(raw)
    if ver and _version_ge(ver, "0.4.0"):
        f.note_green(f"uv {ver}")
    else:
        f.note_red(
            f"uv {ver or 'unknown'} found (need >= 0.4.0). "
            "Upgrade uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        )


def check_git(f: Findings) -> None:
    """Check that git >= 2.30 is available."""
    if not shutil.which("git"):
        f.note_red(
            "git not found. Install git >= 2.30 "
            "(apt: sudo apt-get install git; macOS: brew install git)."
        )
        return
    try:
        raw = subprocess.run(
            ["git", "--version"], capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except Exception:
        raw = ""
    ver = _extract_version(raw)
    if ver and _version_ge(ver, "2.30"):
        f.note_green(f"git {ver}")
    else:
        f.note_red(
            f"git {ver or 'unknown'} found (need >= 2.30). "
            "Upgrade git from your package manager."
        )


def check_claude(f: Findings) -> None:
    """Check that claude is on PATH."""
    path = shutil.which("claude")
    if path:
        f.note_green(f"claude on PATH ({path})")
    else:
        f.note_red("claude not on PATH. Install Claude Code from https://claude.com/claude-code")


def check_writable(f: Findings, dir_path: str) -> None:
    """Check that *dir_path* is writable.

    Args:
        f: Findings accumulator.
        dir_path: Directory path to test.
    """
    d = Path(dir_path)
    if is_dry_run():
        f.note_green(f"{dir_path} (DRY: not creating)")
        return
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        f.note_red(f"{dir_path} not writable. chmod/chown so your user can create it.")
        return
    if os.access(d, os.W_OK):
        f.note_green(f"{dir_path} writable")
    else:
        f.note_red(f"{dir_path} not writable. chmod/chown so your user can create it.")


def check_terminal(f: Findings) -> None:
    """Check terminal configuration (yellow-only)."""
    cast = os.environ.get("CAST_TERMINAL", "")
    sysnal = os.environ.get("TERMINAL", "")
    supported_str = " ".join(_SUPPORTED)

    if cast:
        if cast in _SUPPORTED:
            f.note_green(f"$CAST_TERMINAL={cast} (supported)")
            return
        f.note_yellow(
            f"$CAST_TERMINAL={cast} is not a supported terminal. "
            "Run `/cast-doctor` from inside Claude Code to probe and configure "
            "(or `bin/cast-doctor --fix-terminal` as a CLI alternative), "
            f"or set $CAST_TERMINAL to one of: {supported_str}. "
            "See docs/reference/supported-terminals.md."
        )
        return

    if sysnal:
        f.note_green(f"$TERMINAL={sysnal} (will be used as fallback)")
        return

    for t in _SUPPORTED:
        if shutil.which(t):
            f.note_green(f"supported terminal on PATH: {t}")
            return

    f.note_yellow(
        "No supported terminal found. "
        "Run `/cast-doctor` from inside Claude Code to probe and configure "
        "(or `bin/cast-doctor --fix-terminal` as a CLI alternative), "
        f"or set $CAST_TERMINAL manually. (Supported: {supported_str})"
    )


def check_diecast_skill_root(f: Findings) -> None:
    """Check the diecast skill-root symlink (yellow-only)."""
    home = Path.home()
    target = home / ".claude" / "skills" / "diecast"
    hook_bin = target / "bin" / "cast-hook"

    if not target.is_symlink():
        f.note_yellow(
            f"{home}/.claude/skills/diecast is not a symlink. "
            "Run ./setup --upgrade from the diecast repo to install it."
        )
        return
    if not (hook_bin.exists() and os.access(hook_bin, os.X_OK)):
        real = os.readlink(target)
        f.note_yellow(
            f"{hook_bin} is missing or not executable. "
            f"The diecast skill-root symlink points at {real}. "
            "Run ./setup --upgrade to repair."
        )
        return
    real = os.readlink(target)
    f.note_green(f"diecast skill root linked ({target} -> {real})")


def check_cast_hooks(f: Findings) -> None:
    """Check cast-hook installation (yellow-only)."""
    cwd = Path.cwd()
    home = Path.home()
    proj_settings = cwd / ".claude" / "settings.json"
    user_settings = home / ".claude" / "settings.json"
    needle = f"{home}/.claude/skills/diecast/bin/cast-hook "

    proj_has = False
    user_has = False
    try:
        if proj_settings.is_file() and needle in proj_settings.read_text():
            proj_has = True
    except OSError:
        pass
    try:
        if user_settings.is_file() and needle in user_settings.read_text():
            user_has = True
    except OSError:
        pass

    if proj_has:
        f.note_green(f"cast-hook installed at project scope ({proj_settings})")
        return
    if user_has:
        f.note_green(f"cast-hook installed at user scope ({user_settings})")
        return

    # Only flag when cwd looks like a project.
    if any((cwd / marker).exists() for marker in (".claude", ".git", "pyproject.toml", "package.json")):
        f.note_yellow(
            "cast-hook not installed for this project. Without it the /runs page "
            "won't show user-typed /cast-* commands as parent rows. Fix: run "
            "`~/.claude/skills/diecast/bin/cast-hook install` in this directory "
            "(add --user for global scope). Re-run /cast-init also wires this automatically."
        )


# ── Run all checks ─────────────────────────────────────────────────

def run_checks() -> Findings:
    """Execute the full diagnostic check suite.

    Returns:
        A ``Findings`` instance populated with all red/yellow/green results.
    """
    f = Findings()
    check_python3(f)
    check_tmux(f)
    check_uv(f)
    check_git(f)
    check_claude(f)
    check_writable(f, str(Path.home() / ".claude"))
    check_writable(f, str(Path.home() / ".cast"))
    check_terminal(f)
    check_diecast_skill_root(f)
    check_cast_hooks(f)
    return f


# ── Output renderers ──────────────────────────────────────────────

def emit_json(f: Findings) -> str:
    """Render findings as the ``{"red":...,"yellow":...,"green":...}`` JSON string.

    Args:
        f: Populated findings.

    Returns:
        A single-line JSON string.
    """
    return json.dumps(f.to_dict(), ensure_ascii=False)


def emit_human(f: Findings, *, quiet: bool = False) -> None:
    """Print findings in human-readable format.

    GREEN lines go to stdout; YELLOW and RED lines go to stderr.

    Args:
        f: Populated findings.
        quiet: When True, suppress GREEN lines.
    """
    if not quiet:
        for item in f.green:
            print(f"  [GREEN] {item}")
    for item in f.yellow:
        print(f"  [YELLOW] {item}", file=sys.stderr)
    for item in f.red:
        print(f"  [RED] {item}", file=sys.stderr)
    if not f.has_red():
        if not quiet:
            print("\n[cast-doctor] All required prerequisites satisfied.")
    else:
        print(
            f"\n[cast-doctor] {len(f.red)} required prerequisite(s) missing.",
            file=sys.stderr,
        )


# ── fix-terminal flow ─────────────────────────────────────────────

def _autodetect_candidates() -> list[str]:
    """Probe installed terminals, returning ordered candidate keys.

    On macOS, checks ``/Applications/iTerm.app`` and always includes
    ``terminal``.  On Linux, probes ``command -v`` in ``_SUPPORTED``
    table order (skipping macOS-only keys).

    Returns:
        Ordered list of terminal key strings found on this host.
    """
    sys_name = platform.system()
    if sys_name == "Darwin":
        candidates: list[str] = []
        if Path("/Applications/iTerm.app").exists():
            candidates.append("iterm")
        candidates.append("terminal")  # always present on macOS
        return candidates

    # Linux / BSD / WSL
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").upper()
    order: list[str] = list(_LINUX_PROBE_ORDER)
    if "KDE" in desktop and "konsole" in _SUPPORTED:
        if "konsole" in order:
            order.remove("konsole")
        order.insert(0, "konsole")
    return [name for name in order if shutil.which(name) is not None]


def _read_config_yaml(path: Path) -> dict:
    """Read a YAML config file using PyYAML if available, else basic parsing.

    Args:
        path: Path to the YAML config file.

    Returns:
        Parsed dict, or empty dict on failure.
    """
    if not path.exists():
        return {}
    text = path.read_text()
    try:
        import yaml  # noqa: F811
        loaded = yaml.safe_load(text)
        if isinstance(loaded, dict):
            return loaded
        return {}
    except ImportError:
        # Stdlib-only fallback: parse simple ``key: value`` lines.
        data: dict[str, str] = {}
        for line in text.splitlines():
            line = line.strip()
            if ":" in line and not line.startswith("#"):
                k, _, v = line.partition(":")
                data[k.strip()] = v.strip()
        return data
    except Exception:
        return {}


def _write_config_yaml(path: Path, data: dict) -> None:
    """Write a config dict to a YAML file, using PyYAML if available.

    Args:
        path: Path to write the config file.
        data: Configuration dictionary to serialize.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import yaml  # noqa: F811
        path.write_text(yaml.safe_dump(data, default_flow_style=False, sort_keys=True))
    except ImportError:
        # Minimal stdlib-only write: one key per line.
        lines = [f"{k}: {v}\n" for k, v in sorted(data.items())]
        path.write_text("".join(lines))


def run_fix_terminal(*, input_fn=None) -> int:
    """Interactive first-run terminal setup.

    Probes installed terminals, prompts when multiple candidates exist,
    and writes ``terminal_default`` to ``~/.cast/config.yaml``.

    Args:
        input_fn: Override for ``input()``. Used by tests.

    Returns:
        Exit code: 0 on success, 1 on abort or no candidates.
    """
    if input_fn is None:
        input_fn = input

    sys_name = platform.system()
    print("[cast-doctor] Probing supported terminals on PATH...")

    candidates = _autodetect_candidates()
    if sys_name == "Darwin":
        for c in candidates:
            if c == "iterm":
                print(f"  found: iterm (/Applications/iTerm.app)")
            elif c == "terminal":
                print("  found: terminal (built-in)")
    else:
        for c in candidates:
            path = shutil.which(c) or ""
            print(f"  found: {c} ({path})")

    if not candidates:
        print("\n[cast-doctor] No supported terminal found on PATH.")
        supported_str = " ".join(_SUPPORTED)
        if sys_name == "Darwin":
            print("  install iTerm2: brew install --cask iterm2")
        else:
            print(f"  install one of: {supported_str}")
            print("  e.g. on Debian/Ubuntu: sudo apt install gnome-terminal")
        return 1

    if len(candidates) == 1:
        print(f"\n[cast-doctor] One candidate found: {candidates[0]}")
        try:
            raw = input_fn(
                f"Write ~/.cast/config.yaml with terminal_default: {candidates[0]}? [Y/n] "
            )
        except EOFError:
            raw = "n"
        choice_str = (raw or "y").strip()
        if choice_str.lower() in ("y", "yes"):
            choice = candidates[0]
        else:
            print("[cast-doctor] Aborted, no changes written.")
            return 1
    else:
        print("\nMultiple candidates. Pick one:")
        for i, c in enumerate(candidates, 1):
            print(f"  {i}) {c}")
        try:
            raw = input_fn("\nChoice [1]: ")
        except EOFError:
            raw = "1"
        choice_str = (raw or "1").strip()
        if not choice_str.isdigit() or int(choice_str) < 1 or int(choice_str) > len(candidates):
            print(f"[cast-doctor] Invalid choice: {choice_str}")
            return 1
        choice = candidates[int(choice_str) - 1]

    cfg_file = Path.home() / ".cast" / "config.yaml"
    data = _read_config_yaml(cfg_file)
    data["terminal_default"] = choice
    _write_config_yaml(cfg_file, data)

    print(f"\n[cast-doctor] Wrote {cfg_file}: terminal_default: {choice}")
    print("[cast-doctor] Done. Verify with: cast-doctor")
    return 0


# ── CLI help ───────────────────────────────────────────────────────

_HELP_TEXT = """\
bin/cast-doctor — Diecast prerequisite checker.

Internal: invoked by `setup`'s `step1_doctor` and CI. Post-install diagnosis
happens via `/cast-doctor` from inside Claude Code.
Exits 0 when no RED findings; non-zero with per-issue actionable messages otherwise.

Usage:
  bin/cast-doctor                # human-readable output, exit 0/1
  bin/cast-doctor --json         # minimal JSON: {"red":[...],"yellow":[...],"green":[...]}
  bin/cast-doctor --quiet        # suppress GREEN lines; print RED/YELLOW only
  bin/cast-doctor --fix-terminal # internal: invoked by `setup` and the `/cast-doctor`
                                 # skill; users should run `/cast-doctor` from inside
                                 # Claude Code.
  bin/cast-doctor --help         # this help text

Required green prerequisites:
  * uv   >= 0.4.0        (curl -LsSf https://astral.sh/uv/install.sh | sh)
  * git  >= 2.30
  * claude on PATH       (https://claude.com/claude-code)
  * write access to ~/.claude/ and ~/.cast/

Yellow (warn-only) checks:
  * $CAST_TERMINAL set to a value not in the supported list (soft-fallback per Decision #3)
  * $CAST_TERMINAL empty, $TERMINAL empty, no supported terminal on PATH

Direct callability (Decision #2): this script is intentionally usable post-install
as a fallback — it's the gate ./setup runs in Step 1, and it backs the
`/cast-doctor` skill when cast-server is down.
"""


# ── CLI entry point ────────────────────────────────────────────────

def main(argv: Optional[list[str]] = None) -> None:
    """CLI entry point for ``bin/cast-doctor``.

    Parses ``--json``, ``--quiet``, ``--fix-terminal``, and ``--help``
    flags and dispatches to the appropriate handler.  Exits with code 0
    when no RED findings exist, 1 otherwise.

    Args:
        argv: Command-line arguments. When ``None``, reads from
            ``sys.argv[1:]``.
    """
    args = argv if argv is not None else sys.argv[1:]

    json_output = False
    quiet = False
    fix_terminal = False

    for arg in args:
        if arg == "--json":
            json_output = True
        elif arg == "--quiet":
            quiet = True
        elif arg == "--fix-terminal":
            fix_terminal = True
        elif arg in ("-h", "--help"):
            print(_HELP_TEXT)
            sys.exit(0)
        else:
            print(f"[cast] ERROR: Unknown flag: {arg} (try --help)", file=sys.stderr)
            sys.exit(1)

    if fix_terminal:
        sys.exit(run_fix_terminal())

    findings = run_checks()

    if json_output:
        print(emit_json(findings))
    else:
        emit_human(findings, quiet=quiet)

    sys.exit(1 if findings.has_red() else 0)


if __name__ == "__main__":
    main()
