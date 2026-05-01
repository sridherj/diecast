"""Tests for `cast_server.cli.install_hooks` — the user-safety surface.

The autouse ``_isolate_settings_filesystem`` fixture below MUST stay first in
the file. It structurally prevents any test from touching the developer's real
``~/.claude/settings.json`` by rebinding ``Path.home`` to a tmp directory for
the duration of every test (Decision #8).

If you add a test, add it under the existing fixture — never above it.
"""
from __future__ import annotations

import json
import os
import stat
from collections.abc import Iterator
from pathlib import Path

import pytest

from cast_server.cli import install_hooks


@pytest.fixture(autouse=True)
def _isolate_settings_filesystem(tmp_path_factory, monkeypatch) -> Iterator[None]:
    """SAFETY: structurally prevent any test from touching the dev's real
    ~/.claude/settings.json. Decision #8."""
    tmp_home = tmp_path_factory.mktemp("home")
    monkeypatch.setattr(Path, "home", lambda: tmp_home)
    yield


@pytest.fixture
def tmp_project_root(tmp_path) -> Path:
    """Project-shaped tmp dir: marker file present + .claude/ subdir."""
    (tmp_path / ".git").mkdir()
    (tmp_path / ".claude").mkdir()
    return tmp_path


@pytest.fixture
def tmp_dir_no_markers(tmp_path) -> Path:
    """Empty tmp dir — no project markers at all. Used for warning test."""
    return tmp_path


def _settings(root: Path) -> Path:
    return root / ".claude" / "settings.json"


def _read(path: Path) -> dict:
    return json.loads(path.read_text())


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def _ours_count(bucket: list) -> int:
    return sum(1 for e in bucket if install_hooks._entry_is_ours(e))


# ---------------------------------------------------------------------------
# Paranoid sanity test for the autouse isolation fixture
# ---------------------------------------------------------------------------

def test_user_scope_path_resolves_under_tmp_home(tmp_project_root, tmp_path_factory):
    """If this fails, the autouse fixture is broken — STOP and fix."""
    p = install_hooks._settings_path(user_scope=True, project_root=tmp_project_root)
    assert str(p).startswith(str(tmp_path_factory.getbasetemp()))


# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------

def test_install_creates_settings_file_when_missing(tmp_project_root):
    path = _settings(tmp_project_root)
    assert not path.exists()

    rc = install_hooks.install(tmp_project_root)

    assert rc == 0
    assert path.exists()
    data = _read(path)
    hooks = data["hooks"]
    assert "UserPromptSubmit" in hooks
    assert "Stop" in hooks
    assert _ours_count(hooks["UserPromptSubmit"]) == 1
    assert _ours_count(hooks["Stop"]) == 1


def test_install_preserves_existing_unrelated_hooks(tmp_project_root):
    seed = {
        "hooks": {
            "PostToolUse": [
                {"hooks": [{"type": "command", "command": "echo post-tool", "timeout": 5}]}
            ],
            "SessionStart": [
                {"hooks": [{"type": "command", "command": "echo session", "timeout": 5}]}
            ],
        }
    }
    path = _settings(tmp_project_root)
    _write(path, seed)

    install_hooks.install(tmp_project_root)
    data = _read(path)

    assert data["hooks"]["PostToolUse"] == seed["hooks"]["PostToolUse"]
    assert data["hooks"]["SessionStart"] == seed["hooks"]["SessionStart"]
    assert _ours_count(data["hooks"]["UserPromptSubmit"]) == 1
    assert _ours_count(data["hooks"]["Stop"]) == 1


def test_install_appends_alongside_existing_user_prompt_submit(tmp_project_root):
    third_party = {"hooks": [{"type": "command", "command": "echo third-party", "timeout": 5}]}
    seed = {"hooks": {"UserPromptSubmit": [third_party]}}
    path = _settings(tmp_project_root)
    _write(path, seed)

    install_hooks.install(tmp_project_root)
    data = _read(path)

    bucket = data["hooks"]["UserPromptSubmit"]
    assert bucket[0] == third_party  # third-party preserved AND first
    assert len(bucket) == 2
    assert _ours_count(bucket) == 1


def test_install_appends_alongside_existing_stop(tmp_project_root):
    third_party = {"hooks": [{"type": "command", "command": "echo my-stop", "timeout": 5}]}
    seed = {"hooks": {"Stop": [third_party]}}
    path = _settings(tmp_project_root)
    _write(path, seed)

    install_hooks.install(tmp_project_root)
    data = _read(path)

    bucket = data["hooks"]["Stop"]
    assert bucket[0] == third_party
    assert len(bucket) == 2
    assert _ours_count(bucket) == 1


def test_install_is_idempotent(tmp_project_root):
    install_hooks.install(tmp_project_root)
    install_hooks.install(tmp_project_root)

    data = _read(_settings(tmp_project_root))
    assert _ours_count(data["hooks"]["UserPromptSubmit"]) == 1
    assert _ours_count(data["hooks"]["Stop"]) == 1


def test_install_aborts_on_malformed_json(tmp_project_root):
    path = _settings(tmp_project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = "{not json"
    path.write_text(raw)

    with pytest.raises(SystemExit):
        install_hooks.install(tmp_project_root)

    assert path.read_text() == raw  # byte-for-byte unchanged


def test_install_handles_permission_error_readable_message(tmp_project_root, capsys):
    path = _settings(tmp_project_root)
    _write(path, {"hooks": {}})
    parent = path.parent
    original_mode = parent.stat().st_mode
    os.chmod(parent, stat.S_IRUSR | stat.S_IXUSR)  # read+execute only — no write
    try:
        with pytest.raises(SystemExit) as exc_info:
            install_hooks.install(tmp_project_root)
        assert "--user" in str(exc_info.value)
        leftover = list(parent.glob(f"{path.name}.*"))
        assert leftover == []
    finally:
        os.chmod(parent, original_mode)


def test_install_atomic_write_no_partial_on_exception(tmp_project_root, monkeypatch):
    path = _settings(tmp_project_root)
    seed = {"hooks": {"PostToolUse": [
        {"hooks": [{"type": "command", "command": "echo pre", "timeout": 5}]}
    ]}}
    _write(path, seed)
    original_bytes = path.read_bytes()

    def boom(*args, **kwargs):
        raise RuntimeError("synthetic dump failure")

    monkeypatch.setattr(install_hooks.json, "dump", boom)

    with pytest.raises(RuntimeError):
        install_hooks.install(tmp_project_root)

    assert path.read_bytes() == original_bytes
    leftover = list(path.parent.glob(f"{path.name}.*"))
    assert leftover == []


def test_install_warns_when_no_project_markers(tmp_dir_no_markers, capsys):
    install_hooks.install(tmp_dir_no_markers)
    err = capsys.readouterr().err
    assert "does not look like a project root" in err
    # Install still proceeded.
    assert _settings(tmp_dir_no_markers).exists()


def test_install_no_warning_when_project_markers_present(tmp_project_root, capsys):
    install_hooks.install(tmp_project_root)
    err = capsys.readouterr().err
    assert "does not look like a project root" not in err


def test_install_user_scope_writes_to_home_settings(tmp_project_root):
    install_hooks.install(tmp_project_root, user_scope=True)
    home_settings = Path.home() / ".claude" / "settings.json"
    assert home_settings.exists()
    project_settings = _settings(tmp_project_root)
    assert not project_settings.exists()


# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------

def test_uninstall_removes_only_cast_hook_entries(tmp_project_root):
    seed = {
        "hooks": {
            "PostToolUse": [
                {"hooks": [{"type": "command", "command": "echo keep", "timeout": 5}]}
            ]
        }
    }
    path = _settings(tmp_project_root)
    _write(path, seed)

    install_hooks.install(tmp_project_root)
    install_hooks.uninstall(tmp_project_root)
    data = _read(path)

    assert "UserPromptSubmit" not in data["hooks"]
    assert "Stop" not in data["hooks"]
    assert data["hooks"]["PostToolUse"] == seed["hooks"]["PostToolUse"]


def test_uninstall_preserves_third_party_user_prompt_submit_entry(tmp_project_root):
    third_party = {"hooks": [{"type": "command", "command": "echo third", "timeout": 5}]}
    seed = {"hooks": {"UserPromptSubmit": [third_party]}}
    path = _settings(tmp_project_root)
    _write(path, seed)

    install_hooks.install(tmp_project_root)
    install_hooks.uninstall(tmp_project_root)
    data = _read(path)

    assert data["hooks"]["UserPromptSubmit"] == [third_party]


def test_uninstall_preserves_third_party_stop_entry(tmp_project_root):
    third_party = {"hooks": [{"type": "command", "command": "echo stop-third", "timeout": 5}]}
    seed = {"hooks": {"Stop": [third_party]}}
    path = _settings(tmp_project_root)
    _write(path, seed)

    install_hooks.install(tmp_project_root)
    install_hooks.uninstall(tmp_project_root)
    data = _read(path)

    assert data["hooks"]["Stop"] == [third_party]


def test_uninstall_deletes_empty_event_arrays(tmp_project_root):
    install_hooks.install(tmp_project_root)
    install_hooks.uninstall(tmp_project_root)
    data = _read(_settings(tmp_project_root))
    assert "UserPromptSubmit" not in data.get("hooks", {})
    assert "Stop" not in data.get("hooks", {})


def test_uninstall_deletes_empty_hooks_dict(tmp_project_root):
    install_hooks.install(tmp_project_root)
    install_hooks.uninstall(tmp_project_root)
    data = _read(_settings(tmp_project_root))
    assert "hooks" not in data


def test_uninstall_noop_when_settings_file_missing(tmp_project_root, capsys):
    path = _settings(tmp_project_root)
    assert not path.exists()
    rc = install_hooks.uninstall(tmp_project_root)
    assert rc == 0
    assert not path.exists()


def test_install_writes_absolute_path_command(tmp_project_root):
    """FR-002 (v2): the command string MUST be the absolute path through the
    diecast skill-root umbrella, never bare `cast-hook <subcommand>`.
    """
    install_hooks.install(tmp_project_root)
    data = _read(_settings(tmp_project_root))
    cmd = data["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
    assert cmd.startswith("/")
    assert "/.claude/skills/diecast/bin/cast-hook " in cmd
    assert cmd.endswith(" user-prompt-start")


def test_install_refuses_when_cast_hook_bin_missing(tmp_project_root, monkeypatch):
    """FR-002 (v2): pre-flight check refuses to write entries that point at a
    non-existent binary. Tells the user to run ./setup --upgrade.
    """
    monkeypatch.setattr(install_hooks, "CAST_HOOK_BIN", "/nonexistent/path/cast-hook")
    with pytest.raises(SystemExit) as exc_info:
        install_hooks.install(tmp_project_root)
    assert "/nonexistent/path/cast-hook" in str(exc_info.value)
    assert "./setup --upgrade" in str(exc_info.value)
    # Pre-flight failed → no settings.json was written.
    assert not _settings(tmp_project_root).exists()


def test_round_trip_install_then_uninstall_restores_original_shape(tmp_project_root):
    seed = {
        "hooks": {
            "UserPromptSubmit": [
                {"hooks": [{"type": "command", "command": "echo third", "timeout": 5}]}
            ],
            "PostToolUse": [
                {"hooks": [{"type": "command", "command": "echo post", "timeout": 5}]}
            ],
        },
        "permissions": {"allow": ["Read", "Bash"]},
    }
    path = _settings(tmp_project_root)
    _write(path, seed)

    install_hooks.install(tmp_project_root)
    install_hooks.uninstall(tmp_project_root)

    assert _read(path) == seed


# ---------------------------------------------------------------------------
# sp3: PreToolUse matcher support + new subagent / skill events
# ---------------------------------------------------------------------------

def test_install_hooks_writes_pretooluse_with_skill_matcher(tmp_project_root):
    """sp3: ``cast-hook install`` writes a ``PreToolUse`` entry with
    ``matcher: "Skill"`` that points at ``cast-hook skill-invoke``."""
    install_hooks.install(tmp_project_root)
    data = _read(_settings(tmp_project_root))
    bucket = data["hooks"]["PreToolUse"]
    assert len(bucket) == 1
    entry = bucket[0]
    assert entry["matcher"] == "Skill"
    cmd = entry["hooks"][0]["command"]
    assert cmd.endswith(" skill-invoke")
    # Sibling entries with no matcher must NOT carry a matcher key.
    assert "matcher" not in data["hooks"]["UserPromptSubmit"][0]
    assert "matcher" not in data["hooks"]["Stop"][0]
    assert "matcher" not in data["hooks"]["SubagentStart"][0]
    assert "matcher" not in data["hooks"]["SubagentStop"][0]


def test_install_preserves_third_party_pretooluse_with_different_matcher(
    tmp_project_root,
):
    """A third-party ``PreToolUse`` entry with matcher ``"Bash"`` must remain
    intact, and ``cast-hook install`` must not duplicate ours on re-run."""
    third_party = {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "echo audit-bash", "timeout": 5}],
    }
    seed = {"hooks": {"PreToolUse": [third_party]}}
    path = _settings(tmp_project_root)
    _write(path, seed)

    install_hooks.install(tmp_project_root)
    install_hooks.install(tmp_project_root)  # idempotent under matcher
    data = _read(path)

    bucket = data["hooks"]["PreToolUse"]
    assert third_party in bucket
    assert _ours_count(bucket) == 1
    # Exactly two entries: third-party Bash + ours Skill.
    assert len(bucket) == 2


def test_uninstall_removes_ours_regardless_of_matcher(tmp_project_root):
    """``cast-hook uninstall`` must remove our ``PreToolUse`` entry by HOOK_MARKER
    on the inner command, even when a third-party entry with a different matcher
    sits beside it."""
    third_party = {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "echo audit-bash", "timeout": 5}],
    }
    seed = {"hooks": {"PreToolUse": [third_party]}}
    path = _settings(tmp_project_root)
    _write(path, seed)

    install_hooks.install(tmp_project_root)
    install_hooks.uninstall(tmp_project_root)
    data = _read(path)

    assert data["hooks"]["PreToolUse"] == [third_party]


def test_round_trip_install_uninstall_byte_equivalent(tmp_project_root):
    """A fresh ``install`` followed by ``uninstall`` on a settings file with
    third-party PreToolUse / SubagentStart / SubagentStop / UserPromptSubmit
    / Stop entries must restore the original shape exactly."""
    seed = {
        "hooks": {
            "UserPromptSubmit": [
                {"hooks": [{"type": "command", "command": "echo up", "timeout": 5}]}
            ],
            "Stop": [
                {"hooks": [{"type": "command", "command": "echo stop", "timeout": 5}]}
            ],
            "SubagentStart": [
                {"hooks": [{"type": "command", "command": "echo ss", "timeout": 5}]}
            ],
            "SubagentStop": [
                {"hooks": [{"type": "command", "command": "echo ss-stop", "timeout": 5}]}
            ],
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [{"type": "command", "command": "echo bash", "timeout": 5}],
                }
            ],
            "PostToolUse": [
                {"hooks": [{"type": "command", "command": "echo post", "timeout": 5}]}
            ],
        },
        "permissions": {"allow": ["Read", "Bash"]},
    }
    path = _settings(tmp_project_root)
    _write(path, seed)

    install_hooks.install(tmp_project_root)
    install_hooks.uninstall(tmp_project_root)

    assert _read(path) == seed
