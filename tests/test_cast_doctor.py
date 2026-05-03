"""Tests for ``bin/cast-doctor`` and ``cast_server.bootstrap.doctor``.

Covers:
* --json / --quiet / --help / --fix-terminal CLI flags
* JSON output shape (exact ``{"red":...,"yellow":...,"green":...}`` contract)
* exit-code contract (0 when no RED, 1 when RED present)
* interactive fix-terminal flow (zero/one/multiple candidates)
* idempotent re-runs and YAML round-trip with canonical resolver
* parity check: doctor terminal table matches _SUPPORTED.keys()
* RED-finding tests (missing tmux, old python)
* clean-environment behavior (no project deps — no crash)
* no-bash-on-PATH portability: doctor runs with no bash in PATH
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest
import yaml

from agents._shared.terminal import (
    _SUPPORTED,
    _config_default,
)

# Ensure cast-server/ and tests/ are importable
_CAST_SERVER = Path(__file__).resolve().parent.parent / "cast-server"
if str(_CAST_SERVER) not in sys.path:
    sys.path.insert(0, str(_CAST_SERVER))
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from cast_server.bootstrap.doctor import (
    Findings,
    _extract_version,
    _version_ge,
    check_claude,
    check_git,
    check_python3,
    check_terminal,
    check_tmux,
    check_uv,
    check_writable,
    emit_json,
    emit_human,
    main,
    run_checks,
    run_fix_terminal,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CAST_DOCTOR = REPO_ROOT / "bin" / "cast-doctor"


from fake_bin_helper import make_fake_bin as _make_fake_bin_impl


def _make_fake_bin(dir_: Path, names: list[str]) -> Path:
    """Create a minimal fake bin dir — delegates to shared test helper."""
    return _make_fake_bin_impl(dir_, names)


def _run(
    args: list[str],
    home: Path | None = None,
    fake_bin: Path | None = None,
    stdin: str = "",
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """Run bin/cast-doctor as a subprocess with isolated environment."""
    env: dict[str, str] = {
        "HOME": str(home) if home else os.environ.get("HOME", ""),
        "LANG": "C.UTF-8",
        "CAST_TERMINAL": "",
        "TERMINAL": "",
        "XDG_CURRENT_DESKTOP": "",
    }
    if fake_bin:
        env["PATH"] = str(fake_bin)
    else:
        env["PATH"] = os.environ.get("PATH", "")
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(CAST_DOCTOR)] + args,
        input=stdin,
        text=True,
        capture_output=True,
        env=env,
        cwd=str(REPO_ROOT),
        timeout=30,
    )


# --- Parity test --------------------------------------------------------------


def test_doctor_terminal_table_matches_supported():
    """Doctor's loaded terminal table keys match _SUPPORTED.keys()."""
    from cast_server.bootstrap.doctor import _SUPPORTED as doctor_supported
    assert set(doctor_supported.keys()) == set(_SUPPORTED.keys()), (
        f"doctor terminal table drifted from agents._shared.terminal._SUPPORTED.\n"
        f"  doctor only: {sorted(set(doctor_supported) - set(_SUPPORTED))}\n"
        f"  terminal only: {sorted(set(_SUPPORTED) - set(doctor_supported))}"
    )


# --- Version helpers ----------------------------------------------------------


class TestVersionHelpers:
    """Tests for _version_ge and _extract_version."""

    def test_equal_versions(self) -> None:
        assert _version_ge("3.11.0", "3.11") is True

    def test_higher_major(self) -> None:
        assert _version_ge("4.0.0", "3.11") is True

    def test_lower_minor(self) -> None:
        assert _version_ge("3.10.0", "3.11") is False

    def test_higher_patch(self) -> None:
        assert _version_ge("3.11.5", "3.11.0") is True

    def test_missing_patch(self) -> None:
        assert _version_ge("3.11", "3.11.0") is True

    def test_extract_version_normal(self) -> None:
        assert _extract_version("git version 2.43.0") == "2.43.0"

    def test_extract_version_uv(self) -> None:
        assert _extract_version("uv 0.11.8 (8cafb1c38 2025-04-30)") == "0.11.8"

    def test_extract_version_none(self) -> None:
        assert _extract_version("no version here") is None


# --- Findings -----------------------------------------------------------------


class TestFindings:
    """Tests for the Findings accumulator."""

    def test_empty_has_no_red(self) -> None:
        f = Findings()
        assert not f.has_red()

    def test_red_flagged(self) -> None:
        f = Findings()
        f.note_red("problem")
        assert f.has_red()

    def test_to_dict_shape(self) -> None:
        f = Findings()
        f.note_red("r")
        f.note_yellow("y")
        f.note_green("g")
        d = f.to_dict()
        assert set(d.keys()) == {"red", "yellow", "green"}
        assert d["red"] == ["r"]
        assert d["yellow"] == ["y"]
        assert d["green"] == ["g"]


# --- JSON output contract -----------------------------------------------------


def test_json_output_shape():
    """--json produces valid JSON with exactly {red, yellow, green} keys."""
    res = _run(["--json"])
    data = json.loads(res.stdout)
    assert set(data.keys()) == {"red", "yellow", "green"}
    assert all(isinstance(v, list) for v in data.values())


def test_json_exit_code_matches_red():
    """Exit code is 1 iff red findings exist."""
    res = _run(["--json"])
    data = json.loads(res.stdout)
    if data["red"]:
        assert res.returncode != 0
    else:
        assert res.returncode == 0


# --- --quiet flag -------------------------------------------------------------


def test_quiet_suppresses_green():
    """--quiet suppresses GREEN lines from stdout."""
    res = _run(["--quiet"])
    assert "[GREEN]" not in res.stdout


def test_quiet_still_shows_red_yellow():
    """--quiet still shows RED/YELLOW on stderr."""
    res = _run(["--quiet"])
    combined = res.stdout + res.stderr
    # We expect at least some output (claude not on PATH in sandbox)
    assert "[RED]" in combined or "[YELLOW]" in combined or res.returncode == 0


# --- --help flag --------------------------------------------------------------


def test_help_exits_zero():
    """--help exits with code 0."""
    res = _run(["--help"])
    assert res.returncode == 0


def test_help_lists_fix_terminal_flag():
    """--help text mentions --fix-terminal."""
    res = _run(["--help"])
    assert "--fix-terminal" in res.stdout


def test_help_lists_json_flag():
    """--help text mentions --json."""
    res = _run(["--help"])
    assert "--json" in res.stdout


# --- Unknown flag error -------------------------------------------------------


def test_unknown_flag_exits_nonzero():
    """An unknown flag produces an error and exits non-zero."""
    res = _run(["--bogus"])
    assert res.returncode != 0
    assert "Unknown flag" in res.stderr


# --- Interactive-flow tests ---------------------------------------------------


@pytest.mark.skipif(shutil.which("python3") is None, reason="needs python3")
def test_zero_candidates_exits_nonzero(tmp_path):
    if os.uname().sysname != "Linux":
        pytest.skip("zero-candidate test runs only on Linux probe path")
    home = tmp_path / "home"
    home.mkdir()
    fake_bin = _make_fake_bin(tmp_path / "bin", names=[])
    res = _run(["--fix-terminal"], home=home, fake_bin=fake_bin)
    assert res.returncode != 0
    assert "No supported terminal" in (res.stdout + res.stderr)
    assert not (home / ".cast" / "config.yaml").exists()


@pytest.mark.skipif(shutil.which("python3") is None, reason="needs python3")
def test_single_candidate_confirm_writes_config(tmp_path):
    if os.uname().sysname != "Linux":
        pytest.skip("Linux probe path only")
    home = tmp_path / "home"
    home.mkdir()
    fake_bin = _make_fake_bin(tmp_path / "bin", names=["alacritty"])
    res = _run(["--fix-terminal"], home=home, fake_bin=fake_bin, stdin="y\n")
    assert res.returncode == 0, res.stderr
    cfg_path = home / ".cast" / "config.yaml"
    assert cfg_path.exists()
    assert _config_default(cfg_path) == "alacritty"


@pytest.mark.skipif(shutil.which("python3") is None, reason="needs python3")
def test_single_candidate_decline_does_not_write(tmp_path):
    if os.uname().sysname != "Linux":
        pytest.skip("Linux probe path only")
    home = tmp_path / "home"
    home.mkdir()
    fake_bin = _make_fake_bin(tmp_path / "bin", names=["alacritty"])
    res = _run(["--fix-terminal"], home=home, fake_bin=fake_bin, stdin="n\n")
    assert res.returncode != 0
    assert not (home / ".cast" / "config.yaml").exists()


@pytest.mark.skipif(shutil.which("python3") is None, reason="needs python3")
def test_multiple_candidates_pick_second(tmp_path):
    if os.uname().sysname != "Linux":
        pytest.skip("Linux probe path only")
    home = tmp_path / "home"
    home.mkdir()
    fake_bin = _make_fake_bin(
        tmp_path / "bin",
        names=["ptyxis", "gnome-terminal", "kitty"],  # diecast-lint: ignore-line
    )
    res = _run(["--fix-terminal"], home=home, fake_bin=fake_bin, stdin="2\n")
    assert res.returncode == 0, res.stderr
    cfg_path = home / ".cast" / "config.yaml"
    # _SUPPORTED order on Linux is ptyxis, gnome-terminal, kitty, ...; with all  # diecast-lint: ignore-line
    # three on PATH the second candidate is gnome-terminal.
    assert _config_default(cfg_path) == "gnome-terminal"


@pytest.mark.skipif(shutil.which("python3") is None, reason="needs python3")
def test_invalid_selection_exits_nonzero(tmp_path):
    """Invalid number input to the multi-candidate picker exits non-zero."""
    if os.uname().sysname != "Linux":
        pytest.skip("Linux probe path only")
    home = tmp_path / "home"
    home.mkdir()
    fake_bin = _make_fake_bin(
        tmp_path / "bin",
        names=["ptyxis", "gnome-terminal"],  # diecast-lint: ignore-line
    )
    res = _run(["--fix-terminal"], home=home, fake_bin=fake_bin, stdin="99\n")
    assert res.returncode != 0
    assert "Invalid choice" in (res.stdout + res.stderr)


@pytest.mark.skipif(shutil.which("python3") is None, reason="needs python3")
def test_idempotent_rerun(tmp_path):
    if os.uname().sysname != "Linux":
        pytest.skip("Linux probe path only")
    home = tmp_path / "home"
    home.mkdir()
    fake_bin = _make_fake_bin(tmp_path / "bin", names=["alacritty"])
    _run(["--fix-terminal"], home=home, fake_bin=fake_bin, stdin="y\n")
    _run(["--fix-terminal"], home=home, fake_bin=fake_bin, stdin="y\n")
    cfg_path = home / ".cast" / "config.yaml"
    cfg_text = cfg_path.read_text()
    parsed = yaml.safe_load(cfg_text)
    assert parsed == {"terminal_default": "alacritty"}
    assert cfg_text.count("terminal_default") == 1


@pytest.mark.skipif(shutil.which("python3") is None, reason="needs python3")
def test_preserves_unrelated_config_keys(tmp_path):
    if os.uname().sysname != "Linux":
        pytest.skip("Linux probe path only")
    home = tmp_path / "home"
    (home / ".cast").mkdir(parents=True)
    (home / ".cast" / "config.yaml").write_text(
        yaml.safe_dump({"some_other_key": "value", "terminal_default": "old"})
    )
    fake_bin = _make_fake_bin(tmp_path / "bin", names=["alacritty"])
    _run(["--fix-terminal"], home=home, fake_bin=fake_bin, stdin="y\n")
    parsed = yaml.safe_load((home / ".cast" / "config.yaml").read_text())
    assert parsed == {
        "some_other_key": "value",
        "terminal_default": "alacritty",
    }


# --- RED-list prerequisite tests ----------------------------------------------


def _isolated_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {
        "HOME": os.environ.get("HOME", ""),
        "LANG": "C.UTF-8",
        "DRY_RUN": "1",  # don't touch real ~/.claude / ~/.cast
    }
    if extra:
        env.update(extra)
    return env


def test_cast_doctor_red_on_missing_tmux(tmp_path):
    """RED finding when tmux is absent from PATH; install hint surfaces."""
    fake_bin = tmp_path / "bin"
    _make_fake_bin(fake_bin, names=[])
    for name in ("uv", "git", "claude"):
        shim = fake_bin / name
        shim.write_text('#!/bin/sh\ncase "$1" in --version) echo \'99.99.99\';; esac\n')
        shim.chmod(0o755)

    env = _isolated_env({"PATH": str(fake_bin)})
    res = subprocess.run(
        [sys.executable, str(CAST_DOCTOR)],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(REPO_ROOT),
        timeout=15,
    )
    combined = res.stdout + res.stderr
    assert res.returncode != 0, combined
    assert "tmux not found" in combined
    assert any(
        token in combined
        for token in ("brew install tmux", "apt install tmux", "dnf install tmux",
                      "pacman -S tmux", "package manager")
    ), combined


def test_cast_doctor_red_on_old_python(tmp_path):
    """Inject a fake python3 reporting 3.10 -> cast-doctor flags it RED."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_python = fake_bin / "python3"
    fake_python.write_text(
        "#!/bin/sh\n"
        "case \"$1\" in\n"
        "  -c) echo '3.10.12'; exit 0;;\n"
        "  *)  echo 'Python 3.10.12'; exit 0;;\n"
        "esac\n"
    )
    fake_python.chmod(0o755)

    for tool in ("env", "sh", "uname", "mkdir", "tr", "grep", "head",
                 "cat", "dirname", "tmux", "uv", "git", "claude"):
        real = shutil.which(tool)
        if real and not (fake_bin / tool).exists():
            (fake_bin / tool).symlink_to(real)

    env = _isolated_env({"PATH": str(fake_bin)})
    res = subprocess.run(
        [sys.executable, str(CAST_DOCTOR)],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(REPO_ROOT),
        timeout=15,
    )
    combined = res.stdout + res.stderr
    assert res.returncode != 0, combined
    assert "python3" in combined and "3.10" in combined
    assert "3.11" in combined  # the required-version mention
    assert any(
        token in combined
        for token in ("brew install python", "apt install python",
                      "dnf install python", "pacman -S python", "package manager")
    ), combined


# --- Unit tests for individual checks -----------------------------------------


class TestCheckPython3:
    """Unit tests for check_python3."""

    def test_missing_python3(self) -> None:
        f = Findings()
        with mock.patch("cast_server.bootstrap.doctor.shutil.which", return_value=None):
            check_python3(f)
        assert any("python3 not found" in r for r in f.red)

    def test_old_python3(self) -> None:
        f = Findings()
        with mock.patch("cast_server.bootstrap.doctor.shutil.which", return_value="/usr/bin/python3"):
            fake_result = mock.Mock(stdout="3.10.0\n")
            with mock.patch("cast_server.bootstrap.doctor.subprocess.run", return_value=fake_result):
                check_python3(f)
        assert any("3.10" in r for r in f.red)

    def test_good_python3(self) -> None:
        f = Findings()
        with mock.patch("cast_server.bootstrap.doctor.shutil.which", return_value="/usr/bin/python3"):
            fake_result = mock.Mock(stdout="3.12.3\n")
            with mock.patch("cast_server.bootstrap.doctor.subprocess.run", return_value=fake_result):
                check_python3(f)
        assert any("python3 3.12.3" in g for g in f.green)
        assert not f.red


class TestCheckUv:
    """Unit tests for check_uv."""

    def test_missing_uv(self) -> None:
        f = Findings()
        with mock.patch("cast_server.bootstrap.doctor.shutil.which", return_value=None):
            check_uv(f)
        assert any("uv not found" in r for r in f.red)

    def test_old_uv(self) -> None:
        f = Findings()
        with mock.patch("cast_server.bootstrap.doctor.shutil.which", return_value="/usr/bin/uv"):
            fake_result = mock.Mock(stdout="uv 0.3.9\n")
            with mock.patch("cast_server.bootstrap.doctor.subprocess.run", return_value=fake_result):
                check_uv(f)
        assert any("0.3.9" in r for r in f.red)


class TestCheckGit:
    """Unit tests for check_git."""

    def test_missing_git(self) -> None:
        f = Findings()
        with mock.patch("cast_server.bootstrap.doctor.shutil.which", return_value=None):
            check_git(f)
        assert any("git not found" in r for r in f.red)


class TestCheckTerminal:
    """Unit tests for check_terminal."""

    def test_supported_cast_terminal(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CAST_TERMINAL", "kitty")
        f = Findings()
        check_terminal(f)
        assert any("kitty" in g and "supported" in g for g in f.green)

    def test_unsupported_cast_terminal(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CAST_TERMINAL", "obscure-tty")
        f = Findings()
        check_terminal(f)
        assert any("obscure-tty" in y and "not a supported" in y for y in f.yellow)

    def test_terminal_env_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CAST_TERMINAL", raising=False)
        monkeypatch.setenv("TERMINAL", "xterm")
        f = Findings()
        check_terminal(f)
        assert any("$TERMINAL=xterm" in g for g in f.green)

    def test_no_terminal_yellow(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CAST_TERMINAL", raising=False)
        monkeypatch.delenv("TERMINAL", raising=False)
        f = Findings()
        with mock.patch("cast_server.bootstrap.doctor.shutil.which", return_value=None):
            check_terminal(f)
        assert any("No supported terminal" in y for y in f.yellow)


# --- Unsupported terminal warning test ----------------------------------------


def test_unsupported_terminal_in_json(tmp_path):
    """An unsupported $CAST_TERMINAL value shows up as yellow in JSON."""
    res = _run(["--json"], extra_env={"CAST_TERMINAL": "weird-term"})
    data = json.loads(res.stdout)
    assert any("weird-term" in y for y in data["yellow"])


# --- Clean-environment (no project deps) test ---------------------------------


def test_clean_env_doctor_json_does_not_crash(tmp_path):
    """In a clean environment, cast-doctor --json emits structured findings
    instead of crashing — even when uv is missing."""
    fake_bin = tmp_path / "bin"
    _make_fake_bin(fake_bin, names=[])
    # No uv, no git, no claude — just python3 and essentials
    env = {
        "HOME": str(tmp_path / "home"),
        "PATH": str(fake_bin),
        "LANG": "C.UTF-8",
        "CAST_TERMINAL": "",
        "TERMINAL": "",
        "XDG_CURRENT_DESKTOP": "",
    }
    (tmp_path / "home").mkdir()
    res = subprocess.run(
        [sys.executable, str(CAST_DOCTOR), "--json"],
        capture_output=True, text=True, env=env,
        cwd=str(REPO_ROOT), timeout=15,
    )
    # Should produce valid JSON, not crash
    data = json.loads(res.stdout)
    assert set(data.keys()) == {"red", "yellow", "green"}
    # uv missing should be in red
    assert any("uv" in r for r in data["red"])
    assert res.returncode != 0


# --- No-bash-on-PATH portability test ----------------------------------------


def test_no_bash_on_path_json(tmp_path):
    """cast-doctor --json works even with no bash on PATH."""
    fake_bin = tmp_path / "bin"
    _make_fake_bin(fake_bin, names=[])
    # Explicitly do NOT add bash to the fake bin
    if (fake_bin / "bash").exists():
        (fake_bin / "bash").unlink()

    for name in ("uv", "git", "claude", "tmux"):
        shim = fake_bin / name
        if not shim.exists():
            shim.write_text('#!/bin/sh\ncase "$1" in --version) echo \'99.99.99\';; esac\n')
            shim.chmod(0o755)

    env = {
        "HOME": str(tmp_path / "home"),
        "PATH": str(fake_bin),
        "LANG": "C.UTF-8",
        "CAST_TERMINAL": "kitty",
        "TERMINAL": "",
        "XDG_CURRENT_DESKTOP": "",
        "DRY_RUN": "1",
    }
    (tmp_path / "home").mkdir()
    res = subprocess.run(
        [sys.executable, str(CAST_DOCTOR), "--json"],
        capture_output=True, text=True, env=env,
        cwd=str(REPO_ROOT), timeout=15,
    )
    data = json.loads(res.stdout)
    assert set(data.keys()) == {"red", "yellow", "green"}
    # bash is NOT a required check in the Python doctor
    # so there should be no red finding about bash


def test_no_bash_on_path_quiet(tmp_path):
    """cast-doctor --quiet works even with no bash on PATH."""
    fake_bin = tmp_path / "bin"
    _make_fake_bin(fake_bin, names=[])
    if (fake_bin / "bash").exists():
        (fake_bin / "bash").unlink()

    env = {
        "HOME": str(tmp_path / "home"),
        "PATH": str(fake_bin),
        "LANG": "C.UTF-8",
        "CAST_TERMINAL": "kitty",
        "TERMINAL": "",
        "XDG_CURRENT_DESKTOP": "",
        "DRY_RUN": "1",
    }
    (tmp_path / "home").mkdir()
    res = subprocess.run(
        [sys.executable, str(CAST_DOCTOR), "--quiet"],
        capture_output=True, text=True, env=env,
        cwd=str(REPO_ROOT), timeout=15,
    )
    # Should not crash, and should not show GREEN lines
    assert "[GREEN]" not in res.stdout


# --- run_fix_terminal unit tests with mock input ─────────────────────────────


class TestRunFixTerminal:
    """Unit tests for run_fix_terminal with mocked input/probing."""

    def test_single_candidate_confirm(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        if os.uname().sysname != "Linux":
            pytest.skip("Linux probe path only")
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("XDG_CURRENT_DESKTOP", "")
        monkeypatch.delenv("CAST_TERMINAL", raising=False)
        monkeypatch.delenv("TERMINAL", raising=False)
        with mock.patch(
            "cast_server.bootstrap.doctor._autodetect_candidates",
            return_value=["alacritty"],
        ):
            result = run_fix_terminal(input_fn=lambda _prompt: "y")
        assert result == 0
        cfg = tmp_path / ".cast" / "config.yaml"
        assert cfg.exists()

    def test_no_candidates_returns_1(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HOME", str(tmp_path))
        with mock.patch(
            "cast_server.bootstrap.doctor._autodetect_candidates",
            return_value=[],
        ):
            result = run_fix_terminal(input_fn=lambda _prompt: "")
        assert result == 1

    def test_multiple_candidates_pick_first(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        if os.uname().sysname != "Linux":
            pytest.skip("Linux probe path only")
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("XDG_CURRENT_DESKTOP", "")
        with mock.patch(
            "cast_server.bootstrap.doctor._autodetect_candidates",
            return_value=["ptyxis", "kitty"],  # diecast-lint: ignore-line
        ):
            result = run_fix_terminal(input_fn=lambda _prompt: "1")
        assert result == 0

    def test_invalid_choice_string(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HOME", str(tmp_path))
        with mock.patch(
            "cast_server.bootstrap.doctor._autodetect_candidates",
            return_value=["ptyxis", "kitty"],  # diecast-lint: ignore-line
        ):
            result = run_fix_terminal(input_fn=lambda _prompt: "abc")
        assert result == 1


# --- emit_json / emit_human ---------------------------------------------------


class TestEmitJson:
    """Tests for emit_json output."""

    def test_valid_json(self) -> None:
        f = Findings()
        f.note_red("r1")
        f.note_yellow("y1")
        f.note_green("g1")
        data = json.loads(emit_json(f))
        assert data == {"red": ["r1"], "yellow": ["y1"], "green": ["g1"]}

    def test_empty_findings(self) -> None:
        f = Findings()
        data = json.loads(emit_json(f))
        assert data == {"red": [], "yellow": [], "green": []}


class TestEmitHuman:
    """Tests for emit_human output."""

    def test_green_shown_by_default(self, capsys) -> None:
        f = Findings()
        f.note_green("ok")
        emit_human(f, quiet=False)
        assert "[GREEN] ok" in capsys.readouterr().out

    def test_quiet_hides_green(self, capsys) -> None:
        f = Findings()
        f.note_green("ok")
        emit_human(f, quiet=True)
        out = capsys.readouterr()
        assert "[GREEN]" not in out.out

    def test_red_shows_count(self, capsys) -> None:
        f = Findings()
        f.note_red("problem1")
        f.note_red("problem2")
        emit_human(f)
        err = capsys.readouterr().err
        assert "2 required prerequisite(s) missing" in err

    def test_all_satisfied_message(self, capsys) -> None:
        f = Findings()
        f.note_green("ok")
        emit_human(f)
        assert "All required prerequisites satisfied" in capsys.readouterr().out
