"""Thin wrapper around tmux subprocess commands."""

import shutil
import subprocess
import time
import logging

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
        self._ptyxis_available: bool | None = None  # Lazy-checked

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

    def _has_ptyxis(self) -> bool:
        """Check if ptyxis binary is available (cached)."""
        if self._ptyxis_available is None:
            self._ptyxis_available = shutil.which("ptyxis") is not None
            if not self._ptyxis_available:
                logger.warning("ptyxis binary not found — visible terminals disabled")
        return self._ptyxis_available

    def open_terminal(self, session_name: str, title: str | None = None) -> None:
        """Open a ptyxis terminal window attached to this tmux session.

        Args:
            session_name: tmux session to attach to.
            title: Optional window title (uses ptyxis --new-window -T flag).
        """
        if not self._has_ptyxis():
            return
        cmd = ["ptyxis", "--new-window"]
        if title:
            cmd.extend(["-T", title])
        cmd.extend(["--", "tmux", "attach-session", "-t", session_name])
        subprocess.Popen(cmd, start_new_session=True)

    def open_terminal_tab(self, session_name: str, title: str | None = None) -> None:
        """Open a ptyxis terminal tab attached to this tmux session.

        Uses --tab to open in the active ptyxis window. If no ptyxis window
        exists yet, ptyxis creates a new window with this tab.

        Args:
            session_name: tmux session to attach to.
            title: Optional tab title (uses ptyxis --tab -T flag).
        """
        if not self._has_ptyxis():
            return
        cmd = ["ptyxis", "--tab"]
        if title:
            cmd.extend(["-T", title])
        cmd.extend(["--", "tmux", "attach-session", "-t", session_name])
        subprocess.Popen(cmd, start_new_session=True)

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
