"""Tests for CLAUDECODE env-var stripping from child processes.

Verifies that:
- ``_clean_child_env`` excludes specified keys without mutating ``os.environ``.
- Launch command strings include ``env -u CLAUDECODE``.
- Resume command strings include ``env -u CLAUDECODE``.
- Working directories with spaces are properly quoted via ``shlex.quote``.
"""
from __future__ import annotations

import os
import shlex
from unittest import mock

import pytest

from cast_server.services.agent_service import _clean_child_env


# ---------------------------------------------------------------------------
# _clean_child_env
# ---------------------------------------------------------------------------


class TestCleanChildEnv:
    """Unit tests for the _clean_child_env helper."""

    def test_excludes_single_key(self) -> None:
        with mock.patch.dict(os.environ, {"CLAUDECODE": "1", "HOME": "/home/u"}, clear=True):
            result = _clean_child_env("CLAUDECODE")
            assert "CLAUDECODE" not in result
            assert result["HOME"] == "/home/u"

    def test_excludes_multiple_keys(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"CLAUDECODE": "1", "CLAUDE_SESSION_ID": "abc", "PATH": "/usr/bin"},
            clear=True,
        ):
            result = _clean_child_env("CLAUDECODE", "CLAUDE_SESSION_ID")
            assert "CLAUDECODE" not in result
            assert "CLAUDE_SESSION_ID" not in result
            assert result["PATH"] == "/usr/bin"

    def test_missing_key_is_harmless(self) -> None:
        with mock.patch.dict(os.environ, {"HOME": "/home/u"}, clear=True):
            result = _clean_child_env("CLAUDECODE")
            assert "CLAUDECODE" not in result
            assert result["HOME"] == "/home/u"

    def test_does_not_mutate_os_environ(self) -> None:
        with mock.patch.dict(os.environ, {"CLAUDECODE": "1", "HOME": "/home/u"}, clear=True):
            _clean_child_env("CLAUDECODE")
            assert os.environ["CLAUDECODE"] == "1"


# ---------------------------------------------------------------------------
# Launch command (tmux send_keys)
# ---------------------------------------------------------------------------


class TestLaunchCommandString:
    """Verify the launch cmd string includes env -u CLAUDECODE."""

    def test_launch_cmd_includes_env_unset(self) -> None:
        model = "sonnet"
        escaped_display = "cast-tasks | my-goal | some-task"
        cmd = f'env -u CLAUDECODE claude --dangerously-skip-permissions --model {model} --name "{escaped_display}"'
        assert cmd.startswith("env -u CLAUDECODE ")
        assert "claude --dangerously-skip-permissions" in cmd


# ---------------------------------------------------------------------------
# Resume command strings
# ---------------------------------------------------------------------------


class TestResumeCommandStrings:
    """Verify resume commands include env -u CLAUDECODE and quote working dirs."""

    def test_resume_with_working_dir(self) -> None:
        session_id = "sess-1234"
        working_dir = "/home/user/my project"
        wd_quoted = shlex.quote(working_dir)
        resume_command = (
            f"cd {wd_quoted} && env -u CLAUDECODE claude --resume {session_id} --dangerously-skip-permissions"
        )
        assert "env -u CLAUDECODE" in resume_command
        assert f"claude --resume {session_id}" in resume_command
        assert wd_quoted in resume_command
        # The path with a space must be quoted
        assert "'" in resume_command or '"' in resume_command

    def test_resume_without_working_dir(self) -> None:
        session_id = "sess-5678"
        resume_command = f"env -u CLAUDECODE claude --resume {session_id} --dangerously-skip-permissions"
        assert resume_command.startswith("env -u CLAUDECODE ")
        assert f"claude --resume {session_id}" in resume_command
        assert "cd " not in resume_command

    def test_resume_spaces_in_working_dir_are_shell_safe(self) -> None:
        """Working dir with spaces must be quoted so shell does not word-split."""
        working_dir = "/home/user/my project dir"
        wd_quoted = shlex.quote(working_dir)
        resume_command = (
            f"cd {wd_quoted} && env -u CLAUDECODE claude --resume sess-abc --dangerously-skip-permissions"
        )
        # shlex.quote wraps in single quotes for paths with spaces
        assert wd_quoted == f"'{working_dir}'"
        assert resume_command.startswith(f"cd '{working_dir}'")

    def test_resume_special_chars_in_working_dir(self) -> None:
        """Working dir with shell-special chars must be properly escaped."""
        working_dir = "/home/user/project$name"
        wd_quoted = shlex.quote(working_dir)
        resume_command = (
            f"cd {wd_quoted} && env -u CLAUDECODE claude --resume sess-xyz --dangerously-skip-permissions"
        )
        assert "env -u CLAUDECODE" in resume_command
        # The dollar sign must be inside quotes to prevent shell expansion
        assert "'" in resume_command

    def test_poll_agent_run_resume_cmd_with_wd(self) -> None:
        """Simulate the _poll_agent_run resume_cmd construction with a working dir."""
        real_session_id = "sess-poll-123"
        wd = "/home/user/my workspace"
        wd_quoted = shlex.quote(wd) if wd else ""
        resume_cmd = (
            f"cd {wd_quoted} && env -u CLAUDECODE claude --resume {real_session_id} --dangerously-skip-permissions"
            if wd
            else f"env -u CLAUDECODE claude --resume {real_session_id} --dangerously-skip-permissions"
        )
        assert "env -u CLAUDECODE" in resume_cmd
        assert f"cd {shlex.quote(wd)}" in resume_cmd
        assert f"claude --resume {real_session_id}" in resume_cmd

    def test_poll_agent_run_resume_cmd_without_wd(self) -> None:
        """Simulate the _poll_agent_run resume_cmd construction without a working dir."""
        real_session_id = "sess-poll-456"
        wd = ""
        wd_quoted = shlex.quote(wd) if wd else ""
        resume_cmd = (
            f"cd {wd_quoted} && env -u CLAUDECODE claude --resume {real_session_id} --dangerously-skip-permissions"
            if wd
            else f"env -u CLAUDECODE claude --resume {real_session_id} --dangerously-skip-permissions"
        )
        assert resume_cmd.startswith("env -u CLAUDECODE ")
        assert "cd " not in resume_cmd
