"""Tests for the cast-hook CLI: handlers, dispatch, and install/uninstall stubs.

HTTP is mocked at the module-level ``_post`` function (or ``urlopen`` for the
unreachable-server test) so no network is touched.
"""
from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from cast_server.cli import hook, hook_handlers, install_hooks


@pytest.fixture
def monkeypatch_post(monkeypatch):
    """Capture calls to ``hook_handlers._post`` instead of issuing HTTP."""
    calls: list[tuple[str, dict]] = []

    def fake_post(path: str, body: dict) -> None:
        calls.append((path, body))

    monkeypatch.setattr(hook_handlers, "_post", fake_post)
    return calls


@pytest.fixture
def monkeypatch_unreachable(monkeypatch):
    """Make urllib.request.urlopen raise URLError to simulate dead server."""
    import urllib.error

    def fake_urlopen(*_args, **_kwargs):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(
        "cast_server.cli.hook_handlers.urllib.request.urlopen", fake_urlopen
    )


@pytest.fixture
def monkeypatch_install(monkeypatch):
    """Capture invocations of install_hooks.install / uninstall."""
    calls: dict[str, list[dict]] = {"install": [], "uninstall": []}

    def fake_install(project_root, user_scope: bool = False) -> int:
        calls["install"].append(
            {"project_root": project_root, "user_scope": user_scope}
        )
        return 0

    def fake_uninstall(project_root, user_scope: bool = False) -> int:
        calls["uninstall"].append(
            {"project_root": project_root, "user_scope": user_scope}
        )
        return 0

    monkeypatch.setattr(install_hooks, "install", fake_install)
    monkeypatch.setattr(install_hooks, "uninstall", fake_uninstall)
    return calls


def _set_stdin(monkeypatch, payload: str) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))


def test_user_prompt_start_matches_cast_command(monkeypatch_post, monkeypatch):
    _set_stdin(
        monkeypatch,
        json.dumps({"prompt": "/cast-plan-review please", "session_id": "S1"}),
    )
    hook_handlers.user_prompt_start()
    assert monkeypatch_post == [
        (
            "/user-invocations",
            {
                "agent_name": "cast-plan-review",
                "prompt": "/cast-plan-review please",
                "session_id": "S1",
            },
        )
    ]


def test_user_prompt_start_skips_non_cast_prompt(monkeypatch_post, monkeypatch):
    _set_stdin(
        monkeypatch,
        json.dumps({"prompt": "what time is it", "session_id": "S1"}),
    )
    hook_handlers.user_prompt_start()
    assert monkeypatch_post == []


def test_user_prompt_start_skips_empty_stdin(monkeypatch_post, monkeypatch):
    _set_stdin(monkeypatch, "")
    hook_handlers.user_prompt_start()
    assert monkeypatch_post == []


def test_user_prompt_start_extracts_agent_name_from_slash(
    monkeypatch_post, monkeypatch
):
    _set_stdin(
        monkeypatch,
        json.dumps({"prompt": "/cast-detailed-plan foo", "session_id": "X"}),
    )
    hook_handlers.user_prompt_start()
    assert len(monkeypatch_post) == 1
    path, body = monkeypatch_post[0]
    assert path == "/user-invocations"
    assert body["agent_name"] == "cast-detailed-plan"


def test_user_prompt_start_passes_session_id_through(
    monkeypatch_post, monkeypatch
):
    _set_stdin(
        monkeypatch,
        json.dumps({"prompt": "/cast-foo bar", "session_id": "session-xyz"}),
    )
    hook_handlers.user_prompt_start()
    assert monkeypatch_post[0][1]["session_id"] == "session-xyz"


def test_user_prompt_stop_calls_complete_with_session_id(
    monkeypatch_post, monkeypatch
):
    _set_stdin(monkeypatch, json.dumps({"session_id": "S2"}))
    hook_handlers.user_prompt_stop()
    assert monkeypatch_post == [
        ("/user-invocations/complete", {"session_id": "S2"})
    ]


def test_user_prompt_stop_skips_when_session_id_missing(
    monkeypatch_post, monkeypatch
):
    _set_stdin(monkeypatch, json.dumps({}))
    hook_handlers.user_prompt_stop()
    assert monkeypatch_post == []


def test_unknown_subcommand_exits_zero_no_post(monkeypatch_post):
    rc = hook.main(["nonsense"])
    assert rc == 0
    assert monkeypatch_post == []


def test_server_unreachable_exits_zero(monkeypatch_unreachable, monkeypatch):
    _set_stdin(
        monkeypatch,
        json.dumps({"prompt": "/cast-plan-review", "session_id": "S1"}),
    )
    # Should not raise; should not exit non-zero.
    hook_handlers.user_prompt_start()


def test_install_subcommand_dispatches_to_install_hooks(monkeypatch_install):
    rc = hook.main(["install"])
    assert rc == 0
    assert len(monkeypatch_install["install"]) == 1
    call = monkeypatch_install["install"][0]
    assert call["project_root"] == Path.cwd()
    assert call["user_scope"] is False

    rc = hook.main(["install", "--user"])
    assert rc == 0
    assert len(monkeypatch_install["install"]) == 2
    assert monkeypatch_install["install"][1]["user_scope"] is True


def test_uninstall_subcommand_dispatches_to_install_hooks(monkeypatch_install):
    rc = hook.main(["uninstall"])
    assert rc == 0
    assert len(monkeypatch_install["uninstall"]) == 1
    call = monkeypatch_install["uninstall"][0]
    assert call["project_root"] == Path.cwd()
    assert call["user_scope"] is False

    rc = hook.main(["uninstall", "--user"])
    assert rc == 0
    assert len(monkeypatch_install["uninstall"]) == 2
    assert monkeypatch_install["uninstall"][1]["user_scope"] is True
