"""Tests for macOS-native terminal dispatch in tmux_manager.py.

Covers:
- _normalize_macos_terminal name resolution
- _open_macos_terminal osascript dispatch (window)
- _open_macos_terminal_tab osascript dispatch (tab)
- env= parameter excludes CLAUDECODE
- Session names with quotes/spaces are properly escaped
- Linux terminals still use flag-based dispatch
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CAST_SERVER_DIR = REPO_ROOT / "cast-server"
if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))

from cast_server.infra.tmux_manager import (
    TmuxSessionManager,
    _normalize_macos_terminal,
)


# ---------------------------------------------------------------------------
# _normalize_macos_terminal tests
# ---------------------------------------------------------------------------


class TestNormalizeMacosTerminal:
    """Unit tests for the module-level terminal name normalizer."""

    @pytest.mark.parametrize("name", ["iterm", "iTerm.app", "iTerm2", "iTerm2.app"])
    def test_returns_iterm_for_iterm_variants(self, name: str) -> None:
        assert _normalize_macos_terminal(name) == "iterm"

    @pytest.mark.parametrize("name", ["terminal", "Terminal.app"])
    def test_returns_terminal_for_terminal_variants(self, name: str) -> None:
        assert _normalize_macos_terminal(name) == "terminal"

    @pytest.mark.parametrize("name", ["ptyxis", "gnome-terminal", "alacritty", "kitty"])
    def test_returns_none_for_non_macos_terminals(self, name: str) -> None:
        assert _normalize_macos_terminal(name) is None

    def test_returns_none_for_empty_string(self) -> None:
        assert _normalize_macos_terminal("") is None


# ---------------------------------------------------------------------------
# Helper: create a TmuxSessionManager without tmux binary check
# ---------------------------------------------------------------------------


def _make_manager() -> TmuxSessionManager:
    """Create a TmuxSessionManager bypassing the __init__ tmux binary check."""
    mgr = object.__new__(TmuxSessionManager)
    mgr._terminal = None
    return mgr


# ---------------------------------------------------------------------------
# _open_macos_terminal tests
# ---------------------------------------------------------------------------


class TestOpenMacosTerminal:
    """Tests for the _open_macos_terminal helper method."""

    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_iterm_calls_osascript_with_correct_script(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._open_macos_terminal("my-session", "iterm")

        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        cmd_list = args[0]
        assert cmd_list[0] == "osascript"
        assert cmd_list[1] == "-e"
        script = cmd_list[2]
        assert 'tell application "iTerm"' in script
        assert "create window with default profile" in script
        assert "tmux attach-session -t" in script
        assert kwargs["start_new_session"] is True

    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_terminal_app_calls_osascript_with_correct_script(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._open_macos_terminal("my-session", "terminal")

        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        cmd_list = args[0]
        script = cmd_list[2]
        assert 'tell application "Terminal"' in script
        assert "do script" in script
        assert "tmux attach-session -t" in script

    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_session_name_with_spaces_is_escaped(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._open_macos_terminal("my session with spaces", "iterm")

        mock_popen.assert_called_once()
        script = mock_popen.call_args[0][0][2]
        # shlex.quote wraps strings with spaces in single quotes
        assert "'my session with spaces'" in script

    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_session_name_with_quotes_is_escaped(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._open_macos_terminal('session"with"quotes', "terminal")

        mock_popen.assert_called_once()
        script = mock_popen.call_args[0][0][2]
        # The session name should be shell-quoted by shlex.quote and then
        # AppleScript-escaped (double quotes escaped)
        assert "tmux attach-session -t" in script
        # The quote character should not appear unescaped in the AppleScript string
        assert 'session"with"quotes' not in script

    @patch.dict(os.environ, {"CLAUDECODE": "1", "PATH": "/usr/bin", "HOME": "/home/test"})
    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_env_excludes_claudecode(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._open_macos_terminal("test-session", "iterm")

        mock_popen.assert_called_once()
        env = mock_popen.call_args[1]["env"]
        assert "CLAUDECODE" not in env
        assert "PATH" in env
        assert "HOME" in env

    @patch.dict(os.environ, {"PATH": "/usr/bin", "HOME": "/home/test"}, clear=True)
    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_env_works_when_claudecode_not_set(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._open_macos_terminal("test-session", "terminal")

        mock_popen.assert_called_once()
        env = mock_popen.call_args[1]["env"]
        assert "CLAUDECODE" not in env
        assert "PATH" in env


# ---------------------------------------------------------------------------
# _open_macos_terminal_tab tests
# ---------------------------------------------------------------------------


class TestOpenMacosTerminalTab:
    """Tests for the _open_macos_terminal_tab helper method."""

    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_iterm_tab_calls_osascript(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._open_macos_terminal_tab("my-session", "iterm")

        mock_popen.assert_called_once()
        script = mock_popen.call_args[0][0][2]
        assert 'tell application "iTerm"' in script
        assert "create tab with default profile" in script
        assert "tmux attach-session -t" in script

    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_terminal_tab_calls_osascript(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._open_macos_terminal_tab("my-session", "terminal")

        mock_popen.assert_called_once()
        script = mock_popen.call_args[0][0][2]
        assert 'tell application "Terminal"' in script
        assert 'keystroke "t" using command down' in script
        assert "do script" in script
        assert "in front window" in script

    @patch.dict(os.environ, {"CLAUDECODE": "1", "PATH": "/usr/bin"})
    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_tab_env_excludes_claudecode(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._open_macos_terminal_tab("test-session", "iterm")

        env = mock_popen.call_args[1]["env"]
        assert "CLAUDECODE" not in env


# ---------------------------------------------------------------------------
# open_terminal / open_terminal_tab macOS dispatch tests
# ---------------------------------------------------------------------------


@dataclass
class _FakeResolvedTerminal:
    command: str
    args: list[str] = field(default_factory=list)
    flags: dict[str, str] = field(default_factory=dict)


class TestOpenTerminalMacosDispatch:
    """open_terminal and open_terminal_tab branch into macOS path when
    the resolved terminal command is a macOS terminal."""

    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_open_terminal_dispatches_to_macos_for_iterm(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._terminal = _FakeResolvedTerminal(command="/Applications/iTerm.app")
        mgr.open_terminal("agent-123")

        mock_popen.assert_called_once()
        cmd_list = mock_popen.call_args[0][0]
        assert cmd_list[0] == "osascript"
        script = cmd_list[2]
        assert 'tell application "iTerm"' in script

    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_open_terminal_dispatches_to_macos_for_terminal(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._terminal = _FakeResolvedTerminal(command="/usr/bin/Terminal.app")
        mgr.open_terminal("agent-456")

        mock_popen.assert_called_once()
        cmd_list = mock_popen.call_args[0][0]
        assert cmd_list[0] == "osascript"
        script = cmd_list[2]
        assert 'tell application "Terminal"' in script

    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_open_terminal_tab_dispatches_to_macos_for_iterm2(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._terminal = _FakeResolvedTerminal(command="/Applications/iTerm2.app")
        mgr.open_terminal_tab("agent-789")

        mock_popen.assert_called_once()
        cmd_list = mock_popen.call_args[0][0]
        assert cmd_list[0] == "osascript"
        script = cmd_list[2]
        assert "create tab with default profile" in script


class TestOpenTerminalLinuxDispatch:
    """Linux terminals still use flag-based dispatch when the resolved
    terminal is not a macOS terminal."""

    @patch.dict(os.environ, {"PATH": "/usr/bin"}, clear=True)
    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_ptyxis_uses_flag_based_dispatch(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._terminal = _FakeResolvedTerminal(
            command="ptyxis",
            args=[],
            flags={"new_tab_flag": "--new-window"},
        )
        mgr.open_terminal("agent-linux", title="My Title")

        mock_popen.assert_called_once()
        cmd_list = mock_popen.call_args[0][0]
        assert cmd_list[0] == "ptyxis"
        assert "--new-window" in cmd_list
        assert "-T" in cmd_list
        assert "My Title" in cmd_list
        assert "tmux" in cmd_list
        assert "attach-session" in cmd_list
        assert "-t" in cmd_list
        assert "agent-linux" in cmd_list

    @patch.dict(os.environ, {"PATH": "/usr/bin"}, clear=True)
    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_gnome_terminal_uses_flag_based_dispatch(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._terminal = _FakeResolvedTerminal(
            command="gnome-terminal",
            args=[],
            flags={"new_tab_flag": "--window"},
        )
        mgr.open_terminal("agent-gnome")

        mock_popen.assert_called_once()
        cmd_list = mock_popen.call_args[0][0]
        assert cmd_list[0] == "gnome-terminal"
        assert "--window" in cmd_list
        assert "tmux" in cmd_list

    @patch.dict(os.environ, {"CLAUDECODE": "secret", "PATH": "/usr/bin"}, clear=True)
    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_linux_dispatch_env_excludes_claudecode(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._terminal = _FakeResolvedTerminal(command="ptyxis")
        mgr.open_terminal("agent-clean")

        env = mock_popen.call_args[1]["env"]
        assert "CLAUDECODE" not in env
        assert "PATH" in env

    @patch.dict(os.environ, {"PATH": "/usr/bin"}, clear=True)
    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_linux_open_terminal_tab_ptyxis_uses_tab_flag(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._terminal = _FakeResolvedTerminal(
            command="ptyxis",
            args=[],
            flags={},
        )
        mgr.open_terminal_tab("agent-tab", title="Tab Title")

        mock_popen.assert_called_once()
        cmd_list = mock_popen.call_args[0][0]
        assert cmd_list[0] == "ptyxis"
        assert "--tab" in cmd_list
        assert "-T" in cmd_list
        assert "Tab Title" in cmd_list

    @patch.dict(os.environ, {"CLAUDECODE": "1", "PATH": "/usr/bin"}, clear=True)
    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_linux_open_terminal_tab_env_excludes_claudecode(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._terminal = _FakeResolvedTerminal(
            command="gnome-terminal",
            args=[],
            flags={"new_tab_flag": "--tab"},
        )
        mgr.open_terminal_tab("agent-tab-clean")

        env = mock_popen.call_args[1]["env"]
        assert "CLAUDECODE" not in env
