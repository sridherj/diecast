"""Tests for CLAUDECODE env-var stripping from child processes.

Verifies that ``_clean_child_env`` excludes specified keys without mutating
``os.environ``.
"""
from __future__ import annotations

import os
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
