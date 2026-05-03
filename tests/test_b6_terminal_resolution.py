"""Tests for B6 terminal portability — agents/_shared/terminal.py.

Covers the four-source resolution order, the ResolutionError contract, and
the /cast-setup first-run prompt trigger.
"""
from __future__ import annotations

import pytest
import yaml

from agents._shared.terminal import (
    ResolutionError,
    _autodetect,
    needs_first_run_setup,
    resolve_terminal,
    _SUPPORTED,
)


@pytest.fixture
def clean_env(monkeypatch):
    monkeypatch.delenv("CAST_TERMINAL", raising=False)
    monkeypatch.delenv("TERMINAL", raising=False)


def test_cast_terminal_wins(clean_env, monkeypatch, tmp_path):
    monkeypatch.setenv("CAST_TERMINAL", "foo")
    monkeypatch.setenv("TERMINAL", "bar")
    assert resolve_terminal(tmp_path / "missing.yaml").command == "foo"


def test_terminal_fallback(clean_env, monkeypatch, tmp_path):
    monkeypatch.setenv("TERMINAL", "bar")
    assert resolve_terminal(tmp_path / "missing.yaml").command == "bar"


def test_config_fallback(clean_env, tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump({"terminal_default": "baz"}))
    assert resolve_terminal(cfg).command == "baz"


def test_unset_raises_with_docs_link(clean_env, tmp_path):
    with pytest.raises(ResolutionError) as exc:
        resolve_terminal(tmp_path / "missing.yaml")
    message = str(exc.value)
    assert "supported-terminals.md" in message
    assert "CAST_TERMINAL" in message
    assert "TERMINAL" in message
    assert "terminal_default" in message


def test_first_run_prompt_trigger(clean_env, tmp_path):
    assert needs_first_run_setup(tmp_path / "missing.yaml") is True


def test_first_run_prompt_skipped_when_env_set(clean_env, monkeypatch, tmp_path):
    monkeypatch.setenv("CAST_TERMINAL", "alacritty")
    assert needs_first_run_setup(tmp_path / "missing.yaml") is False


def test_first_run_prompt_skipped_when_config_set(clean_env, tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump({"terminal_default": "kitty"}))
    assert needs_first_run_setup(cfg) is False


def test_args_split_via_shlex(clean_env, monkeypatch, tmp_path):
    monkeypatch.setenv("CAST_TERMINAL", "kitty --single-instance --title=cast")
    resolved = resolve_terminal(tmp_path / "missing.yaml")
    assert resolved.command == "kitty"
    assert resolved.args == ["--single-instance", "--title=cast"]


def test_flags_preset_for_known_terminal(clean_env, monkeypatch, tmp_path):
    monkeypatch.setenv("CAST_TERMINAL", "alacritty")
    resolved = resolve_terminal(tmp_path / "missing.yaml")
    assert resolved.flags == _SUPPORTED["alacritty"]


def test_flags_empty_for_unknown_terminal(clean_env, monkeypatch, tmp_path):
    monkeypatch.setenv("CAST_TERMINAL", "obscure-tty")
    resolved = resolve_terminal(tmp_path / "missing.yaml")
    assert resolved.flags == {}


def test_malformed_config_yields_error_not_crash(clean_env, tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("not: valid: yaml: [unclosed")
    with pytest.raises(ResolutionError):
        resolve_terminal(cfg)


@pytest.mark.parametrize("name", sorted(_SUPPORTED))
def test_supported_table_drives_resolution(clean_env, monkeypatch, tmp_path, name):
    """Every entry in _SUPPORTED is reachable by name and exposes both flag keys."""
    monkeypatch.setenv("CAST_TERMINAL", name)
    resolved = resolve_terminal(tmp_path / "missing.yaml")
    assert resolved.command == name
    assert "new_tab_flag" in resolved.flags
    assert "cwd_flag" in resolved.flags


# --- terminal_default vs terminal alias -------------------------------------


def test_config_alias_terminal_key_accepted(clean_env, tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump({"terminal": "ptyxis"}))  # diecast-lint: ignore-line
    assert resolve_terminal(cfg).command == "ptyxis"  # diecast-lint: ignore-line


def test_config_canonical_wins_over_alias(clean_env, tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump({
        "terminal_default": "kitty",
        "terminal": "ptyxis",  # diecast-lint: ignore-line
    }))
    assert resolve_terminal(cfg).command == "kitty"


def test_first_run_prompt_skipped_when_alias_set(clean_env, tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump({"terminal": "kitty"}))
    assert needs_first_run_setup(cfg) is False


# --- Improved ResolutionError message ---------------------------------------


def test_resolution_error_points_at_fix_terminal(clean_env, tmp_path):
    with pytest.raises(ResolutionError) as exc:
        resolve_terminal(tmp_path / "missing.yaml")
    msg = str(exc.value)
    assert "/cast-doctor" in msg
    assert "supported-terminals.md" in msg
    # Existing assertions still hold:
    assert "$CAST_TERMINAL" in msg
    assert "$TERMINAL" in msg
    assert "terminal_default" in msg


# --- _autodetect probe order ------------------------------------------------


def test_autodetect_macos_with_iterm(clean_env, tmp_path):
    fake_iterm = tmp_path / "iTerm.app"
    fake_iterm.mkdir()
    candidates = _autodetect(
        system="Darwin",
        iterm_app_path=fake_iterm,
        which=lambda _name: "/usr/bin/anything",
    )
    assert candidates == ["iterm", "terminal"]


def test_autodetect_macos_without_iterm(clean_env, tmp_path):
    candidates = _autodetect(
        system="Darwin",
        iterm_app_path=tmp_path / "missing.app",
        which=lambda _name: "/usr/bin/anything",
    )
    assert candidates == ["terminal"]


def test_autodetect_linux_gnome_prefers_gnome_stack(clean_env):
    fake_path = {
        "ptyxis": "/usr/bin/ptyxis",  # diecast-lint: ignore-line
        "gnome-terminal": "/usr/bin/gnome-terminal",
    }
    candidates = _autodetect(
        system="Linux",
        desktop="GNOME",
        which=lambda name: fake_path.get(name),
    )
    # ptyxis first (GNOME-native), gnome-terminal second.  # diecast-lint: ignore-line
    assert candidates[:2] == ["ptyxis", "gnome-terminal"]  # diecast-lint: ignore-line


def test_autodetect_linux_no_terminals_returns_empty(clean_env):
    assert _autodetect(system="Linux", desktop="", which=lambda _n: None) == []


def test_autodetect_excludes_macos_only_keys_on_linux(clean_env):
    """`iterm` and `terminal` are macOS-only and must never appear in the Linux probe."""
    candidates = _autodetect(
        system="Linux",
        desktop="",
        which=lambda _name: "/usr/bin/anything",
    )
    assert "iterm" not in candidates
    assert "terminal" not in candidates


def test_autodetect_linux_kde_prefers_konsole(clean_env):
    fake_path = {"konsole": "/usr/bin/konsole", "alacritty": "/usr/bin/alacritty"}
    candidates = _autodetect(
        system="Linux",
        desktop="KDE",
        which=lambda name: fake_path.get(name),
    )
    assert candidates[0] == "konsole"
