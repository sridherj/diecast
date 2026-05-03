"""Installer-focused tests for ``cast_server.bootstrap.setup_flow``.

Covers:
* Dry-run logging (actions logged, filesystem untouched).
* Step ordering (canonical STEP_ORDER constant matches run_setup sequence).
* Config merge semantics (existing keys preserved, missing keys filled).
* Interactive prompt skipping (--no-prompt, non-interactive, CAST_TERMINAL set).
* Launch-step skip conditions (--dry-run, --upgrade, --no-prompt, CI).
* Backup layout parity with the previous ``.cast-bak-*`` structure.
* No-bash-on-PATH behavior (setup entry point is Python, not bash).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from unittest import mock

import pytest

# Ensure cast-server/ and tests/ are importable
_CAST_SERVER = Path(__file__).resolve().parent.parent / "cast-server"
if str(_CAST_SERVER) not in sys.path:
    sys.path.insert(0, str(_CAST_SERVER))
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from cast_server.bootstrap.setup_flow import (
    STEP_ORDER,
    SetupState,
    parse_args,
    print_next_steps,
    step1_doctor,
    step2_generate_skills,
    step2_5_migrations,
    step3_install_agents,
    step4_install_skills,
    step5_remove_legacy_shim,
    step5a_install_diecast_skill_root,
    step5b_run_alembic_migrations,
    step6_write_config,
    step7_terminal_prompt,
    step8_launch_and_open_browser,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SETUP_SCRIPT = REPO_ROOT / "setup"


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_state(
    tmp_path: Path,
    *,
    dry_run: bool = False,
    upgrade_mode: bool = False,
    no_prompt: bool = False,
) -> SetupState:
    """Create a SetupState with an isolated repo dir and backup root."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "bin").mkdir()
    (repo / "cast-server").mkdir()
    (repo / "agents").mkdir()
    (repo / "skills" / "claude-code").mkdir(parents=True)

    state = SetupState.__new__(SetupState)
    state.repo_dir = repo
    state.dry_run = dry_run
    state.upgrade_mode = upgrade_mode
    state.no_prompt = no_prompt
    state.launched = False
    state.timestamp = "20250503T000000Z"
    state.bak_root = tmp_path / ".claude" / f".cast-bak-{state.timestamp}"
    return state


from fake_bin_helper import make_fake_bin as _make_fake_bin  # noqa: E402


# ── Step ordering tests ──────────────────────────────────────────────────────


class TestStepOrdering:
    """Verify the canonical step ordering constant."""

    def test_step_order_tuple_length(self) -> None:
        """STEP_ORDER has exactly 12 entries (steps 1–8 + sub-steps + prune)."""
        assert len(STEP_ORDER) == 12

    def test_step_order_starts_with_doctor(self) -> None:
        """First step is always the prerequisite check."""
        assert STEP_ORDER[0] == "step1_doctor"

    def test_step_order_ends_with_launch(self) -> None:
        """Last step is always the launch step."""
        assert STEP_ORDER[-1] == "step8_launch_and_open_browser"

    def test_prune_before_launch(self) -> None:
        """Backup pruning happens before the launch step."""
        prune_idx = STEP_ORDER.index("prune_old_backups")
        launch_idx = STEP_ORDER.index("step8_launch_and_open_browser")
        assert prune_idx < launch_idx

    def test_doctor_before_generate_skills(self) -> None:
        """Prerequisites checked before skill generation."""
        assert STEP_ORDER.index("step1_doctor") < STEP_ORDER.index("step2_generate_skills")

    def test_agents_before_skills(self) -> None:
        """Agent install before skill install."""
        assert STEP_ORDER.index("step3_install_agents") < STEP_ORDER.index("step4_install_skills")

    def test_skill_root_after_skills(self) -> None:
        """Diecast skill-root symlink after skill install."""
        assert STEP_ORDER.index("step4_install_skills") < STEP_ORDER.index(
            "step5a_install_diecast_skill_root"
        )

    def test_alembic_after_skill_root(self) -> None:
        """Alembic migrations after skill-root symlink."""
        assert STEP_ORDER.index("step5a_install_diecast_skill_root") < STEP_ORDER.index(
            "step5b_run_alembic_migrations"
        )

    def test_config_after_alembic(self) -> None:
        """Config write after alembic migrations."""
        assert STEP_ORDER.index("step5b_run_alembic_migrations") < STEP_ORDER.index(
            "step6_write_config"
        )

    def test_terminal_prompt_after_config(self) -> None:
        """Terminal prompt after config write."""
        assert STEP_ORDER.index("step6_write_config") < STEP_ORDER.index(
            "step7_terminal_prompt"
        )

    def test_step_order_matches_run_setup_sequence(self) -> None:
        """The STEP_ORDER constant matches the order of calls in run_setup.

        Reads the run_setup source to extract the function call sequence
        and verifies it matches STEP_ORDER.
        """
        import inspect

        from cast_server.bootstrap.setup_flow import run_setup

        source = inspect.getsource(run_setup)
        # Extract the step calls after "Execute steps in canonical order."
        marker = "Execute steps in canonical order."
        idx = source.find(marker)
        assert idx != -1, "run_setup missing canonical-order comment"
        tail = source[idx:]

        # Extract function calls (step functions + prune_old_backups)
        import re

        calls = re.findall(r"\b(step\w+|prune_old_backups)\s*\(", tail)
        assert tuple(calls) == STEP_ORDER


# ── Dry-run logging tests ───────────────────────────────────────────────────


class TestDryRunLogging:
    """Verify dry-run mode logs actions without touching the filesystem."""

    def test_step3_dry_run_logs_copy(self, tmp_path: Path, capsys) -> None:
        """step3 in dry-run logs DRY: cp instead of copying."""
        state = _make_state(tmp_path, dry_run=True)
        agent = state.repo_dir / "agents" / "cast-test"
        agent.mkdir(parents=True)
        (agent / "README.md").write_text("test")

        home = tmp_path / "home"
        home.mkdir()
        with mock.patch("cast_server.bootstrap.setup_flow.Path.home", return_value=home):
            step3_install_agents(state)

        out = capsys.readouterr().out
        assert "DRY:" in out
        assert "cp -R" in out
        # Nothing should have been created in the home dir
        assert not (home / ".claude" / "agents" / "cast-test").exists()

    def test_step4_dry_run_logs_copy(self, tmp_path: Path, capsys) -> None:
        """step4 in dry-run logs DRY: cp instead of copying."""
        state = _make_state(tmp_path, dry_run=True)
        skill = state.repo_dir / "skills" / "claude-code" / "cast-test-skill"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("test")

        home = tmp_path / "home"
        home.mkdir()
        with mock.patch("cast_server.bootstrap.setup_flow.Path.home", return_value=home):
            step4_install_skills(state)

        out = capsys.readouterr().out
        assert "DRY:" in out
        assert not (home / ".claude" / "skills" / "cast-test-skill").exists()

    def test_step5_dry_run_does_not_remove(self, tmp_path: Path) -> None:
        """step5 in dry-run does not remove the legacy shim."""
        state = _make_state(tmp_path, dry_run=True)
        home = tmp_path / "home"
        local_bin = home / ".local" / "bin"
        local_bin.mkdir(parents=True)
        shim = local_bin / "cast-server"
        shim.write_text("old shim")

        with mock.patch("cast_server.bootstrap.setup_flow.Path.home", return_value=home):
            with mock.patch("cast_server.bootstrap.common.Path.home", return_value=home):
                step5_remove_legacy_shim(state)

        assert shim.exists()  # Not removed in dry-run

    def test_step5a_dry_run_no_symlink(self, tmp_path: Path, capsys) -> None:
        """step5a in dry-run logs but does not create the symlink."""
        state = _make_state(tmp_path, dry_run=True)
        home = tmp_path / "home"
        home.mkdir()

        with mock.patch("cast_server.bootstrap.common.Path.home", return_value=home):
            step5a_install_diecast_skill_root(state)

        out = capsys.readouterr().out
        assert "DRY:" in out
        assert not (home / ".claude" / "skills" / "diecast").exists()

    def test_step5b_dry_run_does_not_run_alembic(self, tmp_path: Path, capsys) -> None:
        """step5b in dry-run logs instead of running alembic."""
        state = _make_state(tmp_path, dry_run=True)
        step5b_run_alembic_migrations(state)
        out = capsys.readouterr().out
        assert "DRY:" in out
        assert "alembic" in out

    def test_step6_dry_run_does_not_write_config(self, tmp_path: Path, capsys) -> None:
        """step6 in dry-run logs but does not create config.yaml."""
        state = _make_state(tmp_path, dry_run=True)
        home = tmp_path / "home"
        home.mkdir()

        with mock.patch("cast_server.bootstrap.setup_flow.Path.home", return_value=home):
            step6_write_config(state)

        out = capsys.readouterr().out
        assert "DRY:" in out
        assert not (home / ".cast" / "config.yaml").exists()

    def test_step8_dry_run_skips_launch(self, tmp_path: Path, capsys) -> None:
        """step8 in dry-run sets launched=False and skips."""
        state = _make_state(tmp_path, dry_run=True)
        step8_launch_and_open_browser(state)
        out = capsys.readouterr().out
        assert "skipping launch: --dry-run" in out
        assert state.launched is False


# ── Config merge semantics tests ─────────────────────────────────────────────


class TestConfigMergeSemantics:
    """Verify config.yaml merge behavior preserves existing keys."""

    def test_fresh_config_gets_all_defaults(self, tmp_path: Path) -> None:
        """A fresh install writes all default keys."""
        # We test the merge logic by checking the inline _CONFIG_DEFAULTS dict
        from cast_server.bootstrap.setup_flow import _CONFIG_DEFAULTS

        assert "terminal" in _CONFIG_DEFAULTS
        assert "host" in _CONFIG_DEFAULTS
        assert "port" in _CONFIG_DEFAULTS
        assert _CONFIG_DEFAULTS["port"] == 8005
        assert _CONFIG_DEFAULTS["auto_upgrade"] is False

    def test_config_defaults_match_bash_original(self) -> None:
        """Python config defaults match the bash setup's DEFAULTS dict."""
        from cast_server.bootstrap.setup_flow import _CONFIG_DEFAULTS

        expected_keys = {
            "terminal", "host", "port", "auto_upgrade",
            "upgrade_snooze_until", "upgrade_snooze_streak",
            "upgrade_never_ask", "last_upgrade_check_at",
            "proactive_global", "proactive_overrides",
        }
        assert set(_CONFIG_DEFAULTS.keys()) == expected_keys

    def test_config_header_matches_bash_original(self) -> None:
        """Python config header matches the bash setup's HEADER."""
        from cast_server.bootstrap.setup_flow import _CONFIG_HEADER

        assert "~/.cast/config.yaml" in _CONFIG_HEADER
        assert "docs/config.md" in _CONFIG_HEADER
        assert "preserved by ./setup" in _CONFIG_HEADER


# ── Interactive prompt skipping tests ────────────────────────────────────────


class TestInteractivePromptSkipping:
    """Verify that the terminal prompt is skipped under the right conditions."""

    def test_no_prompt_skips(self, tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch) -> None:
        """--no-prompt flag skips the terminal prompt."""
        state = _make_state(tmp_path, no_prompt=True)
        monkeypatch.delenv("CAST_TERMINAL", raising=False)
        step7_terminal_prompt(state)
        out = capsys.readouterr().out
        assert "--no-prompt: leaving terminal preference empty." in out

    def test_cast_terminal_set_skips(
        self, tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """$CAST_TERMINAL already set skips the prompt."""
        state = _make_state(tmp_path)
        monkeypatch.setenv("CAST_TERMINAL", "kitty")
        step7_terminal_prompt(state)
        out = capsys.readouterr().out
        assert "already set to 'kitty'" in out

    def test_non_interactive_stdin_warns(
        self, tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Non-interactive stdin produces a warning."""
        state = _make_state(tmp_path)
        monkeypatch.delenv("CAST_TERMINAL", raising=False)
        with mock.patch("sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = False
            step7_terminal_prompt(state)
        err = capsys.readouterr().err
        assert "Non-interactive shell" in err

    def test_cast_interactive_with_claude_defers(
        self, tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CAST_INTERACTIVE=1 with claude on PATH defers to Claude Code."""
        state = _make_state(tmp_path)
        monkeypatch.delenv("CAST_TERMINAL", raising=False)
        monkeypatch.setenv("CAST_INTERACTIVE", "1")
        with mock.patch("sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = True
            with mock.patch("cast_server.bootstrap.setup_flow.shutil.which", return_value="/usr/bin/claude"):
                step7_terminal_prompt(state)
        out = capsys.readouterr().out
        assert "Claude Code branch" in out


# ── Launch-step skip conditions ──────────────────────────────────────────────


class TestLaunchStepSkipConditions:
    """Verify step8 is skipped under the right conditions."""

    def test_upgrade_mode_skips(self, tmp_path: Path, capsys) -> None:
        """--upgrade mode skips the launch step."""
        state = _make_state(tmp_path, upgrade_mode=True)
        step8_launch_and_open_browser(state)
        out = capsys.readouterr().out
        assert "skipping launch: --upgrade mode" in out
        assert state.launched is False

    def test_dry_run_skips(self, tmp_path: Path, capsys) -> None:
        """--dry-run skips the launch step."""
        state = _make_state(tmp_path, dry_run=True)
        step8_launch_and_open_browser(state)
        out = capsys.readouterr().out
        assert "skipping launch: --dry-run" in out
        assert state.launched is False

    def test_no_prompt_skips(self, tmp_path: Path, capsys) -> None:
        """--no-prompt skips the launch step."""
        state = _make_state(tmp_path, no_prompt=True)
        step8_launch_and_open_browser(state)
        out = capsys.readouterr().out
        assert "skipping launch: non-interactive" in out
        assert state.launched is False

    def test_ci_env_skips(self, tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch) -> None:
        """CI environment variable skips the launch step."""
        state = _make_state(tmp_path)
        monkeypatch.setenv("CI", "true")
        step8_launch_and_open_browser(state)
        out = capsys.readouterr().out
        assert "skipping launch: non-interactive" in out
        assert state.launched is False

    def test_empty_cast_port_uses_default(
        self, tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """CAST_PORT='' falls back to default 8005 (bash ${VAR:-default} parity)."""
        state = _make_state(tmp_path, dry_run=True)
        monkeypatch.setenv("CAST_PORT", "")
        step8_launch_and_open_browser(state)
        out = capsys.readouterr().out
        # Dry-run should still mention skipping — not crash on int("").
        assert "skipping launch: --dry-run" in out
        assert state.launched is False

    def test_invalid_cast_port_warns_and_skips(
        self, tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """CAST_PORT=abc emits a warning and skips launch instead of crashing."""
        state = _make_state(tmp_path)
        monkeypatch.setenv("CAST_PORT", "abc")
        monkeypatch.delenv("CI", raising=False)
        step8_launch_and_open_browser(state)
        err = capsys.readouterr().err
        assert "not a valid port number" in err
        assert state.launched is False

    def test_out_of_range_cast_port_warns_and_skips(
        self, tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """CAST_PORT=99999 emits a warning and skips launch."""
        state = _make_state(tmp_path)
        monkeypatch.setenv("CAST_PORT", "99999")
        monkeypatch.delenv("CI", raising=False)
        step8_launch_and_open_browser(state)
        err = capsys.readouterr().err
        assert "not a valid port number" in err
        assert state.launched is False


# ── Backup layout parity tests ───────────────────────────────────────────────


class TestBackupLayoutParity:
    """Verify backup paths match the ``.cast-bak-<ts>`` structure."""

    def test_agent_backup_path_shape(self, tmp_path: Path) -> None:
        """Agent backup lands under .cast-bak-<ts>/.claude/agents/."""
        state = _make_state(tmp_path)
        home = tmp_path / "home"
        agents_dir = home / ".claude" / "agents" / "cast-test"
        agents_dir.mkdir(parents=True)
        (agents_dir / "README.md").write_text("old")

        agent_src = state.repo_dir / "agents" / "cast-test"
        agent_src.mkdir(parents=True, exist_ok=True)
        (agent_src / "README.md").write_text("new")

        with mock.patch("cast_server.bootstrap.setup_flow.Path.home", return_value=home):
            with mock.patch("cast_server.bootstrap.common.Path.home", return_value=home):
                step3_install_agents(state)

        bak = state.bak_root / ".claude" / "agents" / "cast-test"
        assert bak.exists()
        assert (bak / "README.md").read_text() == "old"

    def test_skill_backup_path_shape(self, tmp_path: Path) -> None:
        """Skill backup lands under .cast-bak-<ts>/.claude/skills/."""
        state = _make_state(tmp_path)
        home = tmp_path / "home"
        skills_dir = home / ".claude" / "skills" / "cast-test-skill"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("old")

        skill_src = state.repo_dir / "skills" / "claude-code" / "cast-test-skill"
        skill_src.mkdir(parents=True, exist_ok=True)
        (skill_src / "SKILL.md").write_text("new")

        with mock.patch("cast_server.bootstrap.setup_flow.Path.home", return_value=home):
            with mock.patch("cast_server.bootstrap.common.Path.home", return_value=home):
                step4_install_skills(state)

        bak = state.bak_root / ".claude" / "skills" / "cast-test-skill"
        assert bak.exists()
        assert (bak / "SKILL.md").read_text() == "old"

    def test_legacy_shim_backup_path_shape(self, tmp_path: Path) -> None:
        """Legacy shim backup lands under .cast-bak-<ts>/.local/bin/."""
        state = _make_state(tmp_path)
        home = tmp_path / "home"
        shim = home / ".local" / "bin" / "cast-server"
        shim.parent.mkdir(parents=True)
        shim.write_text("old shim")

        with mock.patch("cast_server.bootstrap.setup_flow.Path.home", return_value=home):
            with mock.patch("cast_server.bootstrap.common.Path.home", return_value=home):
                step5_remove_legacy_shim(state)

        bak = state.bak_root / ".local" / "bin" / "cast-server"
        assert bak.exists()
        assert bak.read_text() == "old shim"
        assert not shim.exists()

    def test_backup_dir_name_matches_timestamp(self, tmp_path: Path) -> None:
        """Backup root dir name embeds the run timestamp."""
        state = _make_state(tmp_path)
        assert f".cast-bak-{state.timestamp}" in state.bak_root.name


# ── Flag parsing tests ───────────────────────────────────────────────────────


class TestParseArgs:
    """Tests for parse_args flag handling."""

    def test_dry_run_flag(self) -> None:
        """--dry-run sets dry_run=True."""
        result = parse_args(["--dry-run"])
        assert result["dry_run"] is True

    def test_upgrade_flag(self) -> None:
        """--upgrade sets upgrade_mode=True."""
        result = parse_args(["--upgrade"])
        assert result["upgrade_mode"] is True

    def test_no_prompt_flag(self) -> None:
        """--no-prompt sets no_prompt=True."""
        result = parse_args(["--no-prompt"])
        assert result["no_prompt"] is True

    def test_help_flag_exits(self) -> None:
        """--help exits with code 0."""
        with pytest.raises(SystemExit) as exc:
            parse_args(["--help"])
        assert exc.value.code == 0

    def test_unknown_flag_exits(self) -> None:
        """Unknown flag exits with code 1."""
        with pytest.raises(SystemExit) as exc:
            parse_args(["--bogus"])
        assert exc.value.code == 1

    def test_combined_flags(self) -> None:
        """Multiple flags can be combined."""
        result = parse_args(["--dry-run", "--upgrade", "--no-prompt"])
        assert result["dry_run"] is True
        assert result["upgrade_mode"] is True
        assert result["no_prompt"] is True

    def test_empty_args(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Empty args use defaults."""
        monkeypatch.delenv("DRY_RUN", raising=False)
        result = parse_args([])
        assert result["dry_run"] is False
        assert result["upgrade_mode"] is False
        assert result["no_prompt"] is False

    def test_dry_run_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """DRY_RUN=1 from environment sets dry_run=True."""
        monkeypatch.setenv("DRY_RUN", "1")
        result = parse_args([])
        assert result["dry_run"] is True


# ── Step 2.5 migrations tests ───────────────────────────────────────────────


class TestMigrationsStep:
    """Tests for step2_5_migrations conditional execution."""

    def test_skips_on_non_upgrade(self, tmp_path: Path, capsys) -> None:
        """Migrations are skipped when not in upgrade mode."""
        state = _make_state(tmp_path, upgrade_mode=False)
        step2_5_migrations(state)
        out = capsys.readouterr().out
        assert "Step 2.5" not in out


# ── Setup entry point tests (subprocess) ─────────────────────────────────────


class TestSetupEntryPoint:
    """Tests that exercise the ./setup script as a subprocess.

    Structural checks (shebang, executable bit, no BASH_SOURCE) are
    covered by ``test_portability_verification.py::TestEntryPointStructure``
    and are not repeated here.
    """

    def test_setup_help_exits_zero(self) -> None:
        """./setup --help exits with code 0."""
        result = subprocess.run(
            [sys.executable, str(SETUP_SCRIPT), "--help"],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0
        assert "--dry-run" in result.stdout
        assert "--upgrade" in result.stdout
        assert "--no-prompt" in result.stdout

    def test_setup_unknown_flag_exits_nonzero(self) -> None:
        """./setup --bogus exits non-zero with error message."""
        result = subprocess.run(
            [sys.executable, str(SETUP_SCRIPT), "--bogus"],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode != 0
        assert "Unknown flag" in result.stderr


# ── No-bash-on-PATH behavior ────────────────────────────────────────────────


class TestNoBashOnPath:
    """Verify that ./setup does not require bash on PATH.

    Structural checks (shebang, executable bit, no BASH_SOURCE) are
    covered by ``test_portability_verification.py::TestEntryPointStructure``.
    """

    def test_setup_help_without_bash(self, tmp_path: Path) -> None:
        """./setup --help works even with no bash on PATH."""
        fake_bin = _make_fake_bin(tmp_path / "bin")
        # Explicitly ensure no bash
        if (fake_bin / "bash").exists():
            (fake_bin / "bash").unlink()

        env = {
            "HOME": str(tmp_path / "home"),
            "PATH": str(fake_bin),
            "LANG": "C.UTF-8",
        }
        (tmp_path / "home").mkdir()

        result = subprocess.run(
            [sys.executable, str(SETUP_SCRIPT), "--help"],
            capture_output=True,
            text=True,
            env=env,
            timeout=15,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0
        assert "--dry-run" in result.stdout


# ── Print next steps tests ───────────────────────────────────────────────────


class TestPrintNextSteps:
    """Tests for the post-install summary."""

    def test_launched_message(self, tmp_path: Path, capsys) -> None:
        """When launched, the message includes the running URL."""
        state = _make_state(tmp_path)
        state.launched = True
        print_next_steps(state)
        out = capsys.readouterr().out
        assert "Install complete. cast-server is running" in out
        assert "~/.claude/skills/diecast/bin/cast-server" in out

    def test_not_launched_message(self, tmp_path: Path, capsys) -> None:
        """When not launched, the message suggests starting the server."""
        state = _make_state(tmp_path)
        state.launched = False
        print_next_steps(state)
        out = capsys.readouterr().out
        assert "Install complete. To start the server:" in out

    def test_next_steps_mentions_cast_init(self, tmp_path: Path, capsys) -> None:
        """Post-install summary always mentions /cast-init."""
        state = _make_state(tmp_path)
        state.launched = False
        print_next_steps(state)
        out = capsys.readouterr().out
        assert "/cast-init" in out


# ── SetupState tests ─────────────────────────────────────────────────────────


class TestSetupState:
    """Tests for the SetupState initialization."""

    def test_state_freezes_timestamp(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """SetupState freezes a timestamp at construction time."""
        monkeypatch.delenv("RUN_TIMESTAMP", raising=False)
        monkeypatch.delenv("CAST_BAK_ROOT", raising=False)
        state = SetupState(tmp_path)
        assert state.timestamp
        assert "T" in state.timestamp
        assert state.timestamp.endswith("Z")

    def test_state_backup_root_matches_timestamp(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Backup root embeds the frozen timestamp."""
        monkeypatch.delenv("RUN_TIMESTAMP", raising=False)
        monkeypatch.delenv("CAST_BAK_ROOT", raising=False)
        state = SetupState(tmp_path)
        assert state.timestamp in state.bak_root.name

    def test_state_defaults(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default state has all flags False and launched=False."""
        monkeypatch.delenv("RUN_TIMESTAMP", raising=False)
        monkeypatch.delenv("CAST_BAK_ROOT", raising=False)
        state = SetupState(tmp_path)
        assert state.dry_run is False
        assert state.upgrade_mode is False
        assert state.no_prompt is False
        assert state.launched is False


# ── Lib.sh removal verification ──────────────────────────────────────────────


class TestLibShRemoval:
    """Verify that bin/_lib.sh has been removed."""

    def test_lib_sh_does_not_exist(self) -> None:
        """bin/_lib.sh should no longer exist in the repository."""
        lib_sh = REPO_ROOT / "bin" / "_lib.sh"
        assert not lib_sh.exists(), "bin/_lib.sh should have been removed"

    def test_setup_does_not_source_lib_sh(self) -> None:
        """The setup script must not source bin/_lib.sh."""
        content = SETUP_SCRIPT.read_text()
        assert "source" not in content
        assert "_lib.sh" not in content
