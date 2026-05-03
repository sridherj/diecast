"""Tests for macOS-native terminal dispatch in tmux_manager.py.

Covers:
- _normalize_macos_terminal name resolution
- _run_osascript osascript dispatch (window and tab)
- _env_without helper excludes CLAUDECODE
- Session names with quotes/spaces are properly escaped
- Linux terminals still use flag-based dispatch
- macOS terminal aliases bypass shutil.which in _resolved_terminal
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from cast_server.infra.terminal import ResolvedTerminal
from cast_server.infra.tmux_manager import (
    TmuxSessionManager,
    _env_without,
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
# _env_without tests
# ---------------------------------------------------------------------------


class TestEnvWithout:
    """Unit tests for the _env_without helper."""

    @patch.dict(os.environ, {"CLAUDECODE": "1", "PATH": "/usr/bin"}, clear=True)
    def test_excludes_specified_key(self) -> None:
        result = _env_without("CLAUDECODE")
        assert "CLAUDECODE" not in result
        assert result["PATH"] == "/usr/bin"

    @patch.dict(os.environ, {"A": "1", "B": "2", "C": "3"}, clear=True)
    def test_excludes_multiple_keys(self) -> None:
        result = _env_without("A", "B")
        assert "A" not in result
        assert "B" not in result
        assert result["C"] == "3"

    @patch.dict(os.environ, {"PATH": "/usr/bin"}, clear=True)
    def test_missing_key_is_harmless(self) -> None:
        result = _env_without("NONEXISTENT")
        assert result == {"PATH": "/usr/bin"}


# ---------------------------------------------------------------------------
# Helper: create a TmuxSessionManager without tmux binary check
# ---------------------------------------------------------------------------


def _make_manager() -> TmuxSessionManager:
    """Create a TmuxSessionManager bypassing the __init__ tmux binary check."""
    mgr = object.__new__(TmuxSessionManager)
    mgr._terminal = None
    return mgr


# ---------------------------------------------------------------------------
# _run_osascript tests (window mode, tab=False)
# ---------------------------------------------------------------------------


class TestRunOsascriptWindow:
    """Tests for the _run_osascript helper method in window mode (tab=False)."""

    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_iterm_calls_osascript_with_correct_script(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._run_osascript("my-session", "iterm")

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
        mgr._run_osascript("my-session", "terminal")

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
        mgr._run_osascript("my session with spaces", "iterm")

        mock_popen.assert_called_once()
        script = mock_popen.call_args[0][0][2]
        # shlex.quote wraps strings with spaces in single quotes
        assert "'my session with spaces'" in script

    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_session_name_with_quotes_is_escaped(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._run_osascript('session"with"quotes', "terminal")

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
        mgr._run_osascript("test-session", "iterm")

        mock_popen.assert_called_once()
        env = mock_popen.call_args[1]["env"]
        assert "CLAUDECODE" not in env
        assert "PATH" in env
        assert "HOME" in env

    @patch.dict(os.environ, {"PATH": "/usr/bin", "HOME": "/home/test"}, clear=True)
    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_env_works_when_claudecode_not_set(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._run_osascript("test-session", "terminal")

        mock_popen.assert_called_once()
        env = mock_popen.call_args[1]["env"]
        assert "CLAUDECODE" not in env
        assert "PATH" in env


# ---------------------------------------------------------------------------
# _run_osascript tests (tab mode, tab=True)
# ---------------------------------------------------------------------------


class TestRunOsascriptTab:
    """Tests for the _run_osascript helper method in tab mode (tab=True)."""

    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_iterm_tab_calls_osascript(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._run_osascript("my-session", "iterm", tab=True)

        mock_popen.assert_called_once()
        script = mock_popen.call_args[0][0][2]
        assert 'tell application "iTerm"' in script
        assert "create tab with default profile" in script
        assert "tmux attach-session -t" in script

    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_terminal_tab_calls_osascript(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._run_osascript("my-session", "terminal", tab=True)

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
        mgr._run_osascript("test-session", "iterm", tab=True)

        env = mock_popen.call_args[1]["env"]
        assert "CLAUDECODE" not in env


# ---------------------------------------------------------------------------
# _resolved_terminal: macOS alias bypass for shutil.which (Review #1)
# ---------------------------------------------------------------------------


class TestResolvedTerminalMacosAlias:
    """macOS terminal aliases bypass shutil.which since they are app names,
    not executables on PATH."""

    @patch("cast_server.infra.tmux_manager.resolve_terminal")
    @patch("cast_server.infra.tmux_manager.shutil.which", return_value=None)
    def test_terminal_alias_bypasses_which(self, mock_which: MagicMock,
                                            mock_resolve: MagicMock) -> None:
        """'terminal' resolves even when shutil.which returns None."""
        mock_resolve.return_value = ResolvedTerminal(command="terminal")
        mgr = _make_manager()

        result = mgr._resolved_terminal()

        assert result.command == "terminal"
        # shutil.which should NOT have been called to gate this
        mock_which.assert_not_called()

    @patch("cast_server.infra.tmux_manager.resolve_terminal")
    @patch("cast_server.infra.tmux_manager.shutil.which", return_value=None)
    def test_iterm_alias_bypasses_which(self, mock_which: MagicMock,
                                         mock_resolve: MagicMock) -> None:
        """'iterm' resolves even when shutil.which returns None."""
        mock_resolve.return_value = ResolvedTerminal(command="iterm")
        mgr = _make_manager()

        result = mgr._resolved_terminal()

        assert result.command == "iterm"
        mock_which.assert_not_called()

    @patch("cast_server.infra.tmux_manager.resolve_terminal")
    @patch("cast_server.infra.tmux_manager.shutil.which", return_value=None)
    def test_non_macos_terminal_still_checks_which(self, mock_which: MagicMock,
                                                     mock_resolve: MagicMock) -> None:
        """Non-macOS terminals still require shutil.which to succeed."""
        from cast_server.infra.terminal import ResolutionError

        mock_resolve.return_value = ResolvedTerminal(command="ptyxis")
        mgr = _make_manager()

        with pytest.raises(ResolutionError, match="not on PATH"):
            mgr._resolved_terminal()

        mock_which.assert_called_once_with("ptyxis")


# ---------------------------------------------------------------------------
# open_terminal / open_terminal_tab macOS dispatch tests
# ---------------------------------------------------------------------------


class TestOpenTerminalMacosDispatch:
    """open_terminal and open_terminal_tab branch into macOS path when
    the resolved terminal command is a macOS terminal."""

    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_open_terminal_dispatches_to_macos_for_iterm(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._terminal = ResolvedTerminal(command="/Applications/iTerm.app")
        mgr.open_terminal("agent-123")

        mock_popen.assert_called_once()
        cmd_list = mock_popen.call_args[0][0]
        assert cmd_list[0] == "osascript"
        script = cmd_list[2]
        assert 'tell application "iTerm"' in script

    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_open_terminal_dispatches_to_macos_for_terminal(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._terminal = ResolvedTerminal(command="/usr/bin/Terminal.app")
        mgr.open_terminal("agent-456")

        mock_popen.assert_called_once()
        cmd_list = mock_popen.call_args[0][0]
        assert cmd_list[0] == "osascript"
        script = cmd_list[2]
        assert 'tell application "Terminal"' in script

    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_open_terminal_tab_dispatches_to_macos_for_iterm2(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._terminal = ResolvedTerminal(command="/Applications/iTerm2.app")
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
        mgr._terminal = ResolvedTerminal(
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
        mgr._terminal = ResolvedTerminal(
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
        mgr._terminal = ResolvedTerminal(command="ptyxis")
        mgr.open_terminal("agent-clean")

        env = mock_popen.call_args[1]["env"]
        assert "CLAUDECODE" not in env
        assert "PATH" in env

    @patch.dict(os.environ, {"PATH": "/usr/bin"}, clear=True)
    @patch("cast_server.infra.tmux_manager.subprocess.Popen")
    def test_linux_open_terminal_tab_ptyxis_uses_tab_flag(self, mock_popen: MagicMock) -> None:
        mgr = _make_manager()
        mgr._terminal = ResolvedTerminal(
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
        mgr._terminal = ResolvedTerminal(
            command="gnome-terminal",
            args=[],
            flags={"new_tab_flag": "--tab"},
        )
        mgr.open_terminal_tab("agent-tab-clean")

        env = mock_popen.call_args[1]["env"]
        assert "CLAUDECODE" not in env
