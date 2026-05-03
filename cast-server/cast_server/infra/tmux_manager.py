"""Thin wrapper around tmux subprocess commands."""

import os
import shutil
import subprocess
import time
import logging

from cast_server.infra.terminal import (
    ResolutionError,
    ResolvedTerminal,
    resolve_terminal,
)


def _basename(cmd: str) -> str:
    return os.path.basename(cmd)


_MACOS_TERMINAL_ALIASES: frozenset[str] = frozenset({
    "iterm", "iterm.app", "iterm2", "iterm2.app",
    "terminal", "terminal.app",
})


def _normalize_macos_terminal(name: str) -> str | None:
    """Normalize macOS terminal names to canonical 'iterm' or 'terminal'.
    Returns None if not a macOS terminal."""
    lower = name.lower().removesuffix(".app")
    if lower in ("iterm", "iterm2"):
        return "iterm"
    if lower == "terminal":
        return "terminal"
    return None


logger = logging.getLogger(__name__)


class TmuxError(Exception):
    """Raised when a tmux command fails."""


class TmuxSessionManager:
    def __init__(self):
        """Verify tmux is available on init."""
        try:
            result = subprocess.run(
                ["tmux", "-V"], capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                raise TmuxError("tmux not available")
            logger.info("tmux available: %s", result.stdout.strip())
        except FileNotFoundError:
            raise TmuxError("tmux binary not found")
        # Lazy-resolved on first successful resolution. Failures re-raise so the
        # dispatcher can fail the run with a structured message — no more silent
        # "visible terminals disabled" fallback that produced a 30s readiness timeout.
        self._terminal: ResolvedTerminal | None = None

    def _run(self, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(
                ["tmux"] + args,
                capture_output=True, text=True, timeout=10
            )
        except FileNotFoundError:
            raise TmuxError("tmux binary not found")
        except subprocess.TimeoutExpired:
            raise TmuxError(f"tmux command timed out: {args}")

    def create_session(self, session_name: str, command: str, working_dir: str) -> str:
        result = self._run([
            "new-session", "-d", "-s", session_name,
            "-x", "200", "-y", "50",
            "-c", working_dir,
        ])
        if result.returncode != 0:
            raise TmuxError(f"Failed to create session: {result.stderr}")
        self.send_keys(session_name, command)
        time.sleep(0.1)
        self.send_enter(session_name)
        return session_name

    def capture_pane(self, target: str, lines: int = 50) -> list[str]:
        result = self._run(["capture-pane", "-p", "-J", "-e", "-t", target], check=False)
        if result.returncode != 0:
            return []  # Pane may have closed
        all_lines = [l for l in result.stdout.splitlines() if l.strip()]
        return all_lines[-lines:]

    def send_keys(self, target: str, keys: str) -> None:
        self._run(["send-keys", "-t", target, keys, ""])

    def send_enter(self, target: str) -> None:
        self._run(["send-keys", "-t", target, "Enter"])

    def _resolved_terminal(self) -> ResolvedTerminal:
        """Resolve $CAST_TERMINAL once and cache.

        Raises:
            ResolutionError: when no terminal is configured, or when the
                configured command is not on PATH. Callers (agent_service)
                catch this and fail the run with the structured message —
                no more silent fallback into a 30s readiness timeout.
        """
        if self._terminal is not None:
            return self._terminal
        resolved = resolve_terminal()
        if shutil.which(resolved.command) is None:
            raise ResolutionError(
                f"configured terminal '{resolved.command}' is not on PATH. "
                f"fix: install {resolved.command} or run "
                "`bin/cast-doctor --fix-terminal` to pick a different one. "
                "See docs/reference/supported-terminals.md."
            )
        self._terminal = resolved
        return self._terminal

    @staticmethod
    def _split_flag(flag: str) -> list[str]:
        return flag.split() if flag else []

    def _open_macos_terminal(self, session_name: str, terminal_name: str,
                             title: str | None = None) -> None:
        """Open a macOS terminal window attached to a tmux session via osascript."""
        import shlex
        tmux_target = shlex.quote(session_name)
        tmux_cmd = f"tmux attach-session -t {tmux_target}"
        # Escape for AppleScript string literal (backslash and double-quote)
        as_safe = tmux_cmd.replace("\\", "\\\\").replace('"', '\\"')

        if terminal_name == "iterm":
            script = f'''
            tell application "iTerm"
                activate
                set newWindow to (create window with default profile)
                tell current session of newWindow
                    write text "{as_safe}"
                end tell
            end tell
            '''
        else:  # terminal_name == "terminal"
            script = f'''
            tell application "Terminal"
                activate
                do script "{as_safe}"
            end tell
            '''
        clean_env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
        subprocess.Popen(["osascript", "-e", script], start_new_session=True, env=clean_env)

    def _open_macos_terminal_tab(self, session_name: str, terminal_name: str,
                                  title: str | None = None) -> None:
        """Open a macOS terminal tab attached to a tmux session via osascript."""
        import shlex
        tmux_target = shlex.quote(session_name)
        tmux_cmd = f"tmux attach-session -t {tmux_target}"
        as_safe = tmux_cmd.replace("\\", "\\\\").replace('"', '\\"')

        if terminal_name == "iterm":
            script = f'''
            tell application "iTerm"
                activate
                tell current window
                    create tab with default profile
                    tell current session
                        write text "{as_safe}"
                    end tell
                end tell
            end tell
            '''
        else:  # terminal_name == "terminal"
            script = f'''
            tell application "Terminal"
                activate
                tell application "System Events" to keystroke "t" using command down
                do script "{as_safe}" in front window
            end tell
            '''
        clean_env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
        subprocess.Popen(["osascript", "-e", script], start_new_session=True, env=clean_env)

    def open_terminal(self, session_name: str, title: str | None = None) -> None:
        """Open a new terminal window attached to this tmux session.

        Uses the configured $CAST_TERMINAL (or $TERMINAL / config default).

        Raises:
            ResolutionError: propagated from `_resolved_terminal()` when no
                terminal is configured or the configured command is not on
                PATH. Callers in agent_service catch this and fail the run.
        """
        resolved = self._resolved_terminal()
        mac_name = _normalize_macos_terminal(_basename(resolved.command))

        if mac_name is not None:
            self._open_macos_terminal(session_name, mac_name, title)
            return

        # Linux terminals: existing flag-based dispatch
        cmd = [resolved.command, *resolved.args]
        cmd.extend(self._split_flag(resolved.flags.get("new_tab_flag", "")))
        if title and _basename(resolved.command) == "ptyxis":  # diecast-lint: ignore-line
            # Only ptyxis honors -T; other terminals ignore unknown flags or error.  # diecast-lint: ignore-line
            cmd.extend(["-T", title])
        cmd.extend(["--", "tmux", "attach-session", "-t", session_name])
        clean_env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
        subprocess.Popen(cmd, start_new_session=True, env=clean_env)

    def open_terminal_tab(self, session_name: str, title: str | None = None) -> None:
        """Open a new terminal tab attached to this tmux session.

        For ptyxis, opens via --tab in the active window. For other terminals,  # diecast-lint: ignore-line
        falls back to the same new-window flag as ``open_terminal``.

        Raises:
            ResolutionError: propagated from `_resolved_terminal()` when no
                terminal is configured or the configured command is not on
                PATH.
        """
        resolved = self._resolved_terminal()
        mac_name = _normalize_macos_terminal(_basename(resolved.command))

        if mac_name is not None:
            self._open_macos_terminal_tab(session_name, mac_name, title)
            return

        # Linux terminals: existing flag-based dispatch (unchanged)
        cmd = [resolved.command, *resolved.args]
        if _basename(resolved.command) == "ptyxis":  # diecast-lint: ignore-line
            cmd.append("--tab")
            if title:
                cmd.extend(["-T", title])
        else:
            cmd.extend(self._split_flag(resolved.flags.get("new_tab_flag", "")))
        cmd.extend(["--", "tmux", "attach-session", "-t", session_name])
        clean_env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
        subprocess.Popen(cmd, start_new_session=True, env=clean_env)

    def get_pane_command(self, target: str) -> str:
        result = self._run([
            "display-message", "-p", "-t", target,
            "#{pane_current_command}"
        ], check=False)
        return result.stdout.strip() if result.returncode == 0 else ""

    def list_all_pane_commands(self) -> dict[str, str]:
        """Batch check: one subprocess call for all panes. Returns {session_name: command}."""
        result = self._run([
            "list-panes", "-a",
            "-F", "#{session_name} #{pane_current_command}"
        ], check=False)
        if result.returncode != 0:
            return {}
        mapping = {}
        for line in result.stdout.splitlines():
            parts = line.split(" ", 1)
            if len(parts) == 2:
                mapping[parts[0]] = parts[1]
        return mapping

    def kill_session(self, session_name: str) -> None:
        self._run(["kill-session", "-t", session_name], check=False)

    def session_exists(self, session_name: str) -> bool:
        result = self._run(["has-session", "-t", session_name], check=False)
        return result.returncode == 0

    def wait_for_ready(self, session_name: str, timeout_seconds: int = 30) -> bool:
        """Poll for input field (border-adjacency check). Returns True when ready."""
        start = time.time()
        while time.time() - start < timeout_seconds:
            lines = self.capture_pane(session_name, lines=15)
            found, _ = _has_input_field(lines)
            if found:
                return True
            time.sleep(0.5)
        return False


def _has_input_field(pane_lines: list[str]) -> tuple[bool, int]:
    """Shared helper: check for ❯ prompt with ─ border on line above.

    Returns (has_field, line_index_of_prompt).
    """
    for i, line in enumerate(pane_lines):
        if "❯" in line:
            if i > 0 and "─" in pane_lines[i - 1]:
                return True, i
    return False, -1
