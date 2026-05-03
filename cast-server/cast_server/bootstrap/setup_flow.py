# SPDX-License-Identifier: Apache-2.0
"""Installer orchestration — Python replacement for the bash ``./setup``.

Preserves the exact same step ordering, skip-condition logic, flag semantics,
and output contract as the previous bash ``setup`` script while removing the
bash dependency.  All functions use the stdlib-only helpers from
``cast_server.bootstrap.common`` so the installer can run before ``uv sync``.

Public API
----------
* ``run_setup(argv)`` — full installer flow; called by ``./setup``.

Flags
-----
* ``--dry-run``    — print the action plan without touching the filesystem.
* ``--upgrade``    — rerun path used by ``/cast-upgrade``.
* ``--no-prompt``  — skip the ``$CAST_TERMINAL`` prompt (CI / non-interactive).
* ``--help``       — print usage and exit.
"""
from __future__ import annotations

import json as _json_mod
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from cast_server.bootstrap.common import (
    backup_if_exists,
    backup_root,
    detached_launch,
    fail,
    install_diecast_skill_root,
    log,
    probe_port,
    prune_old_backups,
    run_timestamp,
    warn,
)

# ── Constants ────────────────────────────────────────────────────────────────

_HELP_TEXT = """\
setup — Diecast installer.

Usage:
  ./setup                # full install with $CAST_TERMINAL prompt
  ./setup --dry-run      # print the action plan without touching the filesystem
  ./setup --upgrade      # rerun path used by /cast-upgrade (sp2b)
  ./setup --no-prompt    # skip the $CAST_TERMINAL prompt (CI / non-interactive)
  ./setup --help         # this help

Pre-existing files at install targets are backed up under
~/.claude/.cast-bak-<UTC-timestamp>/ before being overwritten. The 5 newest
backup directories are retained; the rest are pruned. See docs/config.md
for the full ~/.cast/config.yaml schema.
"""

_CONFIG_DEFAULTS: dict[str, object] = {
    "terminal_default": "",
    "host": "localhost",
    "port": 8005,
    "auto_upgrade": False,
    "upgrade_snooze_until": None,
    "upgrade_snooze_streak": 0,
    "upgrade_never_ask": False,
    "last_upgrade_check_at": None,
    "proactive_global": None,
    "proactive_overrides": {},
}

_CONFIG_HEADER = (
    "# ~/.cast/config.yaml — Diecast user-level config.\n"
    "# Schema reference: docs/config.md inside the diecast repo.\n"
    "# Edits here are preserved by ./setup re-runs and /cast-upgrade.\n"
)

# ── Step ordering constant (for test introspection) ──────────────────────────

STEP_ORDER: tuple[str, ...] = (
    "step1_doctor",
    "step2_generate_skills",
    "step2_5_migrations",
    "step3_install_agents",
    "step4_install_skills",
    "step5_remove_legacy_shim",
    "step5a_install_diecast_skill_root",
    "step5b_run_alembic_migrations",
    "step6_write_config",
    "step7_terminal_prompt",
    "prune_old_backups",
    "step8_launch_and_open_browser",
)


# ── Dataclass-like state bag (stdlib-only) ───────────────────────────────────

class SetupState:
    """Mutable state bag for a single installer run.

    Attributes:
        repo_dir: Absolute path to the diecast repository root.
        dry_run: Whether ``--dry-run`` was passed.
        upgrade_mode: Whether ``--upgrade`` was passed.
        no_prompt: Whether ``--no-prompt`` was passed.
        launched: Whether the server was successfully launched.
        bak_root: Backup root for this run.
        timestamp: Shared timestamp for this run.
    """

    def __init__(
        self,
        repo_dir: Path,
        *,
        dry_run: bool = False,
        upgrade_mode: bool = False,
        no_prompt: bool = False,
    ) -> None:
        self.repo_dir = repo_dir
        self.dry_run = dry_run
        self.upgrade_mode = upgrade_mode
        self.no_prompt = no_prompt
        self.launched = False

        # Freeze a single timestamp for the entire run.
        self.timestamp = run_timestamp()
        os.environ.setdefault("RUN_TIMESTAMP", self.timestamp)
        self.bak_root = backup_root(self.timestamp)
        os.environ.setdefault("CAST_BAK_ROOT", str(self.bak_root))


# ── Individual steps ─────────────────────────────────────────────────────────

def step1_doctor(state: SetupState) -> None:
    """Step 1/8: prerequisite check via bin/cast-doctor.

    Args:
        state: Current installer state.

    Raises:
        SystemExit: When prerequisites are missing.
    """
    log("Step 1/8: prerequisite check (bin/cast-doctor)")
    doctor = state.repo_dir / "bin" / "cast-doctor"
    result = subprocess.run(
        [sys.executable, str(doctor)],
        cwd=str(state.repo_dir),
        check=False,
    )
    if result.returncode != 0:
        fail("Prerequisites missing. Resolve the [RED] items above and re-run ./setup.")


def step2_generate_skills(state: SetupState) -> None:
    """Step 2/8: generate Claude Code skill files.

    Args:
        state: Current installer state.
    """
    log("Step 2/8: generate Claude Code skill files (bin/generate-skills)")
    skills_target = Path.home() / ".claude" / "skills"
    gen = state.repo_dir / "bin" / "generate-skills"
    cmd: list[str] = [sys.executable, str(gen)]
    if state.dry_run:
        cmd.extend(["--dry-run", "--target-dir", str(skills_target)])
    else:
        cmd.extend(["--target-dir", str(skills_target)])
    subprocess.run(cmd, cwd=str(state.repo_dir), check=True)

    # Anti-leak: bail if any generated skill still references 'taskos-'.
    leak_root = state.repo_dir / "skills" / "claude-code"
    if leak_root.is_dir():
        for skill_dir in leak_root.iterdir():
            if not skill_dir.name.startswith("cast-"):
                continue
            for p in skill_dir.rglob("*"):
                if p.is_file():
                    try:
                        if "taskos-" in p.read_text(errors="replace"):
                            fail(
                                "Anonymization leak: generated skills still reference "
                                "'taskos-'. See docs/troubleshooting.md."
                            )
                    except OSError:
                        pass


def step2_5_migrations(state: SetupState) -> None:
    """Step 2.5/8: run schema migrations (upgrade-only).

    Args:
        state: Current installer state.
    """
    if not state.upgrade_mode:
        return
    log("Step 2.5/8: run schema migrations (bin/run-migrations.py)")
    runner = state.repo_dir / "bin" / "run-migrations.py"
    cmd = [sys.executable, str(runner)]
    if state.dry_run:
        cmd.append("--dry-run")
    subprocess.run(cmd, cwd=str(state.repo_dir), check=True)


def step3_install_agents(state: SetupState) -> None:
    """Step 3/8: install agents under ~/.claude/agents/.

    Args:
        state: Current installer state.
    """
    log("Step 3/8: install agents -> ~/.claude/agents/")
    target_root = Path.home() / ".claude" / "agents"
    if state.dry_run:
        log(f"DRY: mkdir -p {target_root}")
    else:
        target_root.mkdir(parents=True, exist_ok=True)

    agents_dir = state.repo_dir / "agents"
    for agent_dir in sorted(agents_dir.iterdir()):
        if not agent_dir.is_dir() or not agent_dir.name.startswith("cast-"):
            continue
        dest = target_root / agent_dir.name
        backup_if_exists(dest, state.bak_root, dry_run=state.dry_run)
        if state.dry_run:
            log(f"DRY: cp -R {agent_dir} {dest}")
        else:
            shutil.copytree(str(agent_dir), str(dest), dirs_exist_ok=True)


def step4_install_skills(state: SetupState) -> None:
    """Step 4/8: install hand-authored skills under ~/.claude/skills/.

    Args:
        state: Current installer state.
    """
    log("Step 4/8: install hand-authored skills -> ~/.claude/skills/")
    source_root = state.repo_dir / "skills" / "claude-code"
    target_root = Path.home() / ".claude" / "skills"
    if not source_root.is_dir():
        log("  (no skills/claude-code/ in repo, skipping)")
        return
    if state.dry_run:
        log(f"DRY: mkdir -p {target_root}")
    else:
        target_root.mkdir(parents=True, exist_ok=True)

    for skill_dir in sorted(source_root.iterdir()):
        if not skill_dir.is_dir() or not skill_dir.name.startswith("cast-"):
            continue
        dest = target_root / skill_dir.name
        backup_if_exists(dest, state.bak_root, dry_run=state.dry_run)
        if state.dry_run:
            log(f"DRY: cp -R {skill_dir} {dest}")
        else:
            shutil.copytree(str(skill_dir), str(dest), dirs_exist_ok=True)


def step5_remove_legacy_shim(state: SetupState) -> None:
    """Step 5/8: remove legacy ~/.local/bin/cast-server shim.

    Args:
        state: Current installer state.
    """
    log("Step 5/8: remove legacy ~/.local/bin/cast-server shim (gstack pattern)")
    legacy = Path.home() / ".local" / "bin" / "cast-server"
    backup_if_exists(legacy, state.bak_root, dry_run=state.dry_run)


def step5a_install_diecast_skill_root(state: SetupState) -> None:
    """Step 5a/8: install ~/.claude/skills/diecast symlink.

    Args:
        state: Current installer state.
    """
    log("Step 5a/8: install ~/.claude/skills/diecast symlink (gstack pattern)")
    install_diecast_skill_root(
        state.repo_dir,
        dry_run=state.dry_run,
        bak_root=state.bak_root,
    )


def step5b_run_alembic_migrations(state: SetupState) -> None:
    """Step 5b/8: run alembic upgrade head.

    Args:
        state: Current installer state.

    Raises:
        SystemExit: When alembic migration fails.
    """
    log("Step 5b/8: run database migrations (alembic upgrade head)")
    if state.dry_run:
        log(f"DRY: (cd {state.repo_dir}/cast-server && uv run alembic upgrade head)")
        return
    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        cwd=str(state.repo_dir / "cast-server"),
        check=False,
    )
    if result.returncode != 0:
        fail("alembic upgrade head failed; refusing to launch with possibly-broken DB")


def _merge_config(cfg_path: Path, terminal_seed: str = "") -> None:
    """Merge default config keys with existing config, preserving user values.

    Uses ``uv run`` to access PyYAML from the project venv.  This mirrors
    the bash setup's approach of writing a temp Python script.

    .. note::

       This intentionally uses the ``uv run`` inline-script approach rather
       than the stdlib-safe ``_read_config_yaml`` / ``_write_config_yaml``
       helpers in ``doctor.py``.  The setup runs *after* ``uv sync`` has
       installed project dependencies, so PyYAML is guaranteed to be
       available.  The doctor, by contrast, runs *before* ``uv sync`` and
       must fall back to stdlib-only parsing.

    Args:
        cfg_path: Path to ``~/.cast/config.yaml``.
        terminal_seed: Value for the ``terminal_default`` key when empty.
    """
    # Inline merger using project's PyYAML (same approach as the bash version).
    # DEFAULTS and HEADER are generated from the module-level constants so the
    # inline script and _CONFIG_DEFAULTS / _CONFIG_HEADER can never drift apart.
    defaults_repr = _json_mod.dumps(_CONFIG_DEFAULTS)
    header_repr = repr(_CONFIG_HEADER)
    script = (
        "import sys, json\n"
        "from pathlib import Path\n"
        "import yaml\n"
        "\n"
        f"DEFAULTS = json.loads({defaults_repr!r})\n"
        f"HEADER = {header_repr}\n"
        "\n"
        "def main(path, terminal_seed=''):\n"
        "    p = Path(path)\n"
        "    if p.exists():\n"
        "        raw = yaml.safe_load(p.read_text()) or {}\n"
        "        if not isinstance(raw, dict):\n"
        "            raw = {}\n"
        "    else:\n"
        "        raw = {}\n"
        "    merged = {}\n"
        "    for key, default in DEFAULTS.items():\n"
        "        if key == 'terminal_default' and 'terminal_default' not in raw and 'terminal' in raw:\n"
        "            merged[key] = raw['terminal']\n"
        "        elif key in raw:\n"
        "            merged[key] = raw[key]\n"
        "        else:\n"
        "            merged[key] = default\n"
        "    if terminal_seed and not merged.get('terminal_default'):\n"
        "        merged['terminal_default'] = terminal_seed\n"
        "    merged.pop('terminal', None)\n"
        "    p.write_text(HEADER + yaml.safe_dump(merged, sort_keys=False))\n"
        "\n"
        "main(*sys.argv[1:])\n"
    )

    repo_dir = os.environ.get("REPO_DIR", "")
    cmd_args = [cfg_path]
    if terminal_seed:
        cmd_args.append(terminal_seed)

    result = subprocess.run(
        ["uv", "run", "--project", repo_dir, "python", "-c", script]
        + [str(a) for a in cmd_args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        fail(
            f"Failed to write {cfg_path}. Check that uv + pyyaml are available. "
            f"stderr: {result.stderr.strip()}"
        )


def step6_write_config(state: SetupState) -> None:
    """Step 6/8: write/merge ~/.cast/config.yaml.

    Args:
        state: Current installer state.
    """
    log("Step 6/8: ~/.cast/config.yaml")
    cfg_dir = Path.home() / ".cast"
    cfg_file = cfg_dir / "config.yaml"

    if state.dry_run:
        log(f"DRY: mkdir -p {cfg_dir}")
        if cfg_file.exists():
            log(f"DRY: merge missing default keys into {cfg_file}")
        else:
            log(f"DRY: write canonical schema to {cfg_file}")
        return

    cfg_dir.mkdir(parents=True, exist_ok=True)
    os.environ["REPO_DIR"] = str(state.repo_dir)
    detected_terminal = os.environ.get("CAST_TERMINAL", "")
    if not detected_terminal:
        detect_script = state.repo_dir / "bin" / "cast-detect-terminal"
        result = subprocess.run(
            ["uv", "run", "--project", str(state.repo_dir), "python", str(detect_script)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            detected_terminal = result.stdout.strip()
    _merge_config(cfg_file, detected_terminal)
    log(f"  wrote/merged {cfg_file}")


def _persist_terminal_choice(choice: str, state: SetupState) -> None:
    """Write the ``terminal_default`` key into ``~/.cast/config.yaml``.

    Removes any legacy ``terminal`` key and writes ``terminal_default``
    as the canonical config key.

    Args:
        choice: Terminal name or empty/"skip" for no-op.
        state: Current installer state.
    """
    if not choice or choice == "skip":
        return
    if state.dry_run:
        log(f"DRY: persist terminal_default={choice} into ~/.cast/config.yaml")
        return

    cfg_file = Path.home() / ".cast" / "config.yaml"
    script = (
        "import sys\n"
        "from pathlib import Path\n"
        "import yaml\n"
        "\n"
        "p = Path(sys.argv[1])\n"
        "choice = sys.argv[2]\n"
        "data = {}\n"
        "if p.exists():\n"
        "    data = yaml.safe_load(p.read_text()) or {}\n"
        "    if not isinstance(data, dict):\n"
        "        data = {}\n"
        "data.pop('terminal', None)\n"
        "data['terminal_default'] = choice\n"
        "p.write_text(yaml.safe_dump(data, sort_keys=False))\n"
    )
    result = subprocess.run(
        [
            "uv", "run", "--project", str(state.repo_dir),
            "python", "-c", script,
            str(cfg_file), choice,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        warn(f"Failed to persist terminal={choice}")


def step7_terminal_prompt(state: SetupState) -> None:
    """Step 7/8: $CAST_TERMINAL preference prompt.

    Args:
        state: Current installer state.
    """
    log("Step 7/8: $CAST_TERMINAL preference")
    cast_terminal = os.environ.get("CAST_TERMINAL", "")
    if cast_terminal:
        log(f"  $CAST_TERMINAL already set to '{cast_terminal}' — skipping prompt.")
        return
    if state.no_prompt:
        log("  --no-prompt: leaving terminal preference empty.")
        return
    if not sys.stdin.isatty():
        warn(
            "Non-interactive shell — terminal preference left empty. "
            "Override via CAST_TERMINAL=... ./setup."
        )
        return

    cast_interactive = os.environ.get("CAST_INTERACTIVE", "0")
    if cast_interactive == "1" and shutil.which("claude"):
        log("  Claude Code branch: invoke /cast-interactive-questions for terminal selection.")
        log("  (Setup defers — the host runs the AskUserQuestion prompt separately.)")
        return

    # Pure shell branch: prompt via input().
    print("\n[cast] Select default terminal for child agent dispatch:", file=sys.stderr)
    print(
        "  Options: gnome-terminal, iterm2, kitty, alacritty, wezterm, ptyxis, skip",
        file=sys.stderr,
    )
    try:
        choice = input("Choice [skip]: ").strip() or "skip"
    except EOFError:
        choice = "skip"
    _persist_terminal_choice(choice, state)


def _open_browser(url: str) -> None:
    """Open *url* in the default browser (best-effort, never fails).

    Args:
        url: URL to open.
    """
    sys_name = platform.system()
    if sys_name == "Darwin":
        try:
            subprocess.run(["open", url], check=False, capture_output=True)
        except OSError:
            pass
    elif sys_name == "Linux":
        has_display = bool(
            os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
        )
        if has_display and shutil.which("xdg-open"):
            try:
                subprocess.Popen(
                    ["xdg-open", url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
            except OSError:
                pass
        else:
            log(f"  no display detected — visit {url} manually")
    else:
        log(f"  unsupported OS for browser open — visit {url} manually")


def _identify_port_owner(port: int) -> tuple[str, str]:
    """Try to identify what process owns *port*.

    Args:
        port: TCP port number.

    Returns:
        Tuple of (pid, command_name), both may be ``"?"`` on failure.
    """
    pid = "?"
    cmd = "?"
    for finder in (
        lambda: subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True, text=True, check=False,
        ).stdout.strip().splitlines()[0],
        lambda: subprocess.run(
            ["ss", "-tlnp", f"sport = :{port}"],
            capture_output=True, text=True, check=False,
        ).stdout.strip(),
        lambda: subprocess.run(
            ["fuser", f"{port}/tcp"],
            capture_output=True, text=True, check=False,
        ).stdout.strip().split()[0],
    ):
        try:
            candidate = finder()
            if candidate and candidate.isdigit():
                pid = candidate
                break
        except (IndexError, OSError, FileNotFoundError):
            continue

    if pid != "?":
        try:
            result = subprocess.run(
                ["ps", "-p", pid, "-o", "comm="],
                capture_output=True, text=True, check=False,
            )
            cmd = result.stdout.strip() or "?"
        except (OSError, FileNotFoundError):
            pass
    return pid, cmd


def step8_launch_and_open_browser(state: SetupState) -> None:
    """Step 8/8: launch cast-server and open the dashboard.

    Args:
        state: Current installer state.
    """
    log("Step 8/8: launch cast-server + open dashboard")

    host = os.environ.get("CAST_HOST") or "localhost"
    # Use ``or`` so CAST_PORT="" falls back to the default — matches the
    # bash ``${CAST_PORT:-8005}`` semantics.
    port_str = os.environ.get("CAST_PORT") or "8005"
    try:
        port = int(port_str)
        if not (1 <= port <= 65535):
            raise ValueError(f"out of range: {port}")
    except ValueError:
        warn(f"CAST_PORT={port_str!r} is not a valid port number; skipping launch step")
        state.launched = False
        return
    url = f"http://{host}:{port}/"

    # Skip conditions (any one short-circuits this step).
    if state.upgrade_mode:
        log("  skipping launch: --upgrade mode")
        state.launched = False
        return
    if state.dry_run:
        log("  skipping launch: --dry-run")
        state.launched = False
        return
    if state.no_prompt or os.environ.get("CI"):
        log("  skipping launch: non-interactive (--no-prompt or CI)")
        state.launched = False
        return

    # Port pre-flight probe.
    if probe_port(host, port, timeout=1.0):
        # Something is bound.  Determine whether it is our cast-server.
        try:
            probe = subprocess.run(
                ["curl", "-s", "--max-time", "1", f"{url}api/agents/runs?status=running"],
                capture_output=True,
                text=True,
                check=False,
            )
            if probe.returncode == 0:
                log(f"  cast-server already running on {host}:{port}; opening browser only")
                state.launched = True
                _open_browser(url)
                return
        except (OSError, FileNotFoundError):
            pass

        pid, cmd = _identify_port_owner(port)
        warn(f"port {port} in use by PID {pid} ({cmd}).")
        warn(f"       set CAST_PORT=<n> ./setup, or stop the process and re-run.")
        warn("       (skipping launch — install otherwise complete)")
        state.launched = False
        return

    # Happy path: nothing on the port.  Touch the cache dir only here.
    cache_dir = Path.home() / ".cache" / "diecast"
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Detached background launch.
    server_bin = str(Path.home() / ".claude" / "skills" / "diecast" / "bin" / "cast-server")
    log_path = cache_dir / "bootstrap.log"
    detached_launch(
        [server_bin],
        log_path=log_path,
    )

    # Readiness poll: 30 × 0.5s = 15s.
    for _ in range(30):
        if probe_port(host, port, timeout=0.5):
            state.launched = True
            break
        time.sleep(0.5)

    if not state.launched:
        warn("cast-server did not become ready within 15s.")
        warn(f"       check {Path.home()}/.cache/diecast/bootstrap.log for startup errors.")
        state.launched = False
        return  # never fail setup over the launch step

    # Terminal wire-up.
    doctor = state.repo_dir / "bin" / "cast-doctor"
    if doctor.exists() and os.access(doctor, os.X_OK):
        result = subprocess.run(
            [sys.executable, str(doctor), "--fix-terminal"],
            check=False,
        )
        if result.returncode != 0:
            warn("  bin/cast-doctor --fix-terminal returned non-zero (continuing)")

    _open_browser(url)


def print_next_steps(state: SetupState) -> None:
    """Print the post-install summary.

    Args:
        state: Current installer state.
    """
    host = os.environ.get("CAST_HOST", "localhost")
    port = os.environ.get("CAST_PORT", "8005")
    url = f"http://{host}:{port}"

    if state.launched:
        print(f"""
[cast] Install complete. cast-server is running at {url}
       (logs: ~/.cache/diecast/server.log; bootstrap: ~/.cache/diecast/bootstrap.log)

Binaries (no PATH pollution; reach via the diecast skill-root symlink):
  ~/.claude/skills/diecast/bin/cast-server
  ~/.claude/skills/diecast/bin/cast-hook

To restart cast-server later (e.g. after reboot):
  ~/.claude/skills/diecast/bin/cast-server                            # background-friendly defaults
  CAST_PORT=8080 ~/.claude/skills/diecast/bin/cast-server             # custom port
  CAST_BIND_HOST=0.0.0.0 ~/.claude/skills/diecast/bin/cast-server     # bind for LAN access (server side)

Next steps:
  1. /cast-init   — scaffold a new project (writes CLAUDE.md + cast-* dirs)
  2. /cast-runs   — open the dashboard you just launched

Docs: docs/config.md (config keys) · docs/troubleshooting.md (recovery & FAQ)""")
    else:
        print(f"""
[cast] Install complete. To start the server:
  ~/.claude/skills/diecast/bin/cast-server

Next steps:
  1. /cast-init   — scaffold a new project (writes CLAUDE.md + cast-* dirs)
  2. /cast-runs   — open the dashboard once cast-server is up

Docs: docs/config.md (config keys) · docs/troubleshooting.md (recovery & FAQ)""")


# ── Parse flags ──────────────────────────────────────────────────────────────

def parse_args(argv: list[str]) -> dict[str, bool]:
    """Parse installer flags from *argv*.

    Args:
        argv: Command-line arguments (excluding the script name).

    Returns:
        Dict with ``dry_run``, ``upgrade_mode``, and ``no_prompt`` booleans.

    Raises:
        SystemExit: On ``--help`` or unknown flag.
    """
    dry_run = os.environ.get("DRY_RUN", "0") == "1"
    upgrade_mode = False
    no_prompt = False

    for arg in argv:
        if arg == "--dry-run":
            dry_run = True
        elif arg == "--upgrade":
            upgrade_mode = True
        elif arg == "--no-prompt":
            no_prompt = True
        elif arg in ("-h", "--help"):
            print(_HELP_TEXT)
            sys.exit(0)
        else:
            fail(f"Unknown flag: {arg} (try --help)")

    return {
        "dry_run": dry_run,
        "upgrade_mode": upgrade_mode,
        "no_prompt": no_prompt,
    }


# ── Main entry point ─────────────────────────────────────────────────────────

def run_setup(argv: Optional[list[str]] = None, repo_dir: Optional[Path] = None) -> None:
    """Full installer flow.

    Parses flags, creates installer state, and executes the step sequence
    in the same order as the previous bash ``./setup``.

    Args:
        argv: Command-line arguments. When ``None``, reads ``sys.argv[1:]``.
        repo_dir: Override the repository root. When ``None``, resolved from
            the script location.
    """
    if argv is None:
        argv = sys.argv[1:]
    flags = parse_args(argv)

    if repo_dir is None:
        # Resolve from this file: cast-server/cast_server/bootstrap/setup_flow.py
        # -> repo root is 4 levels up.
        repo_dir = Path(__file__).resolve().parent.parent.parent.parent

    state = SetupState(
        repo_dir,
        dry_run=flags["dry_run"],
        upgrade_mode=flags["upgrade_mode"],
        no_prompt=flags["no_prompt"],
    )

    # Export state to env for subprocess visibility.
    os.environ["DRY_RUN"] = "1" if state.dry_run else "0"
    os.environ["UPGRADE_MODE"] = "1" if state.upgrade_mode else "0"
    os.environ["NO_PROMPT"] = "1" if state.no_prompt else "0"
    os.environ["REPO_DIR"] = str(state.repo_dir)

    if state.upgrade_mode:
        log("Upgrade run (called by /cast-upgrade or rerun).")
    else:
        log("First install (or manual rerun).")
    if state.dry_run:
        log("Dry-run mode — no filesystem changes.")

    # Execute steps in canonical order.
    step1_doctor(state)
    step2_generate_skills(state)
    step2_5_migrations(state)
    step3_install_agents(state)
    step4_install_skills(state)
    step5_remove_legacy_shim(state)
    step5a_install_diecast_skill_root(state)
    step5b_run_alembic_migrations(state)
    step6_write_config(state)
    step7_terminal_prompt(state)
    prune_old_backups(dry_run=state.dry_run)
    step8_launch_and_open_browser(state)
    print_next_steps(state)
