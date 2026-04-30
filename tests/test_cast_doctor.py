"""Subprocess tests for `bin/cast-doctor --fix-terminal`.

Covers the interactive flow (zero/one/multiple candidates), idempotent re-runs,
yaml-round-trip with the canonical resolver, and a parity check between the
bash hardcoded fallback list and `_SUPPORTED.keys()`.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from agents._shared.terminal import (
    _SUPPORTED,
    _config_default,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CAST_DOCTOR = REPO_ROOT / "bin" / "cast-doctor"


def _make_fake_bin(dir_: Path, names: list[str]) -> Path:
    """Create empty executable shims for each name; return the dir path.

    Also symlinks essentials (python3, env, sh, bash, mkdir, uname, grep, tr,
    head, dirname, cat, command) so the test PATH can be set to the fake_bin
    alone — that prevents host-installed terminals on /usr/bin from leaking
    into the candidate probe and turning a "single candidate" test into a
    multi-candidate one.
    """
    dir_.mkdir(parents=True, exist_ok=True)
    for name in names:
        shim = dir_ / name
        shim.write_text("#!/bin/sh\nexit 0\n")
        shim.chmod(0o755)
    # Wrap python3 in a shell script that exec's pytest's interpreter via its
    # absolute path — symlinking the venv interpreter into a path outside the
    # venv breaks prefix detection (pyyaml import fails). The wrapper keeps
    # the venv's site-packages reachable while leaving PATH otherwise clean.
    if not (dir_ / "python3").exists():
        wrapper = dir_ / "python3"
        wrapper.write_text(f'#!/bin/sh\nexec {sys.executable} "$@"\n')
        wrapper.chmod(0o755)
    for tool in (
        "env", "sh", "bash", "uname", "mkdir", "date",
        "dirname", "tr", "grep", "head", "cat",
    ):
        real = shutil.which(tool)
        if real and not (dir_ / tool).exists():
            (dir_ / tool).symlink_to(real)
    return dir_


def _run(home: Path, fake_bin: Path, stdin: str = "") -> subprocess.CompletedProcess:
    # Isolated PATH: only fake_bin. We symlink python3/env/etc. into fake_bin
    # in _make_fake_bin so the script still finds essentials, but no
    # host-installed terminal can sneak into the candidate probe.
    env = {
        "HOME": str(home),
        "PATH": str(fake_bin),
        "CAST_TERMINAL": "",
        "TERMINAL": "",
        "XDG_CURRENT_DESKTOP": "",
        "LANG": "C.UTF-8",
    }
    return subprocess.run(
        [str(CAST_DOCTOR), "--fix-terminal"],
        input=stdin,
        text=True,
        capture_output=True,
        env=env,
        cwd=str(REPO_ROOT),
        timeout=30,
    )


# --- Parity test --------------------------------------------------------------


def test_fallback_list_matches_supported():
    """Bash hardcoded fallback list is in sync with _SUPPORTED.keys().

    CI guard against drift — fail fast when someone adds a key to _SUPPORTED
    but forgets to update bin/cast-doctor.
    """
    text = CAST_DOCTOR.read_text()
    match = re.search(
        r"SUPPORTED_TERMINALS_FALLBACK=\(([^)]*)\)",
        text,
    )
    assert match, "SUPPORTED_TERMINALS_FALLBACK array not found in bin/cast-doctor"
    bash_keys = set(match.group(1).split())
    py_keys = set(_SUPPORTED)
    assert bash_keys == py_keys, (
        f"bin/cast-doctor fallback list drifted from _SUPPORTED.\n"
        f"  bash only: {sorted(bash_keys - py_keys)}\n"
        f"  python only: {sorted(py_keys - bash_keys)}"
    )


# --- Interactive-flow tests ---------------------------------------------------


@pytest.mark.skipif(shutil.which("python3") is None, reason="needs python3")
def test_zero_candidates_exits_nonzero(tmp_path):
    if os.uname().sysname != "Linux":
        pytest.skip("zero-candidate test runs only on Linux probe path")
    home = tmp_path / "home"
    home.mkdir()
    fake_bin = _make_fake_bin(tmp_path / "bin", names=[])
    res = _run(home, fake_bin)
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
    res = _run(home, fake_bin, stdin="y\n")
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
    res = _run(home, fake_bin, stdin="n\n")
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
    res = _run(home, fake_bin, stdin="2\n")
    assert res.returncode == 0, res.stderr
    cfg_path = home / ".cast" / "config.yaml"
    # _SUPPORTED order on Linux is ptyxis, gnome-terminal, kitty, ...; with all  # diecast-lint: ignore-line
    # three on PATH the second candidate is gnome-terminal.
    assert _config_default(cfg_path) == "gnome-terminal"


@pytest.mark.skipif(shutil.which("python3") is None, reason="needs python3")
def test_idempotent_rerun(tmp_path):
    if os.uname().sysname != "Linux":
        pytest.skip("Linux probe path only")
    home = tmp_path / "home"
    home.mkdir()
    fake_bin = _make_fake_bin(tmp_path / "bin", names=["alacritty"])
    _run(home, fake_bin, stdin="y\n")
    _run(home, fake_bin, stdin="y\n")
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
    _run(home, fake_bin, stdin="y\n")
    parsed = yaml.safe_load((home / ".cast" / "config.yaml").read_text())
    assert parsed == {
        "some_other_key": "value",
        "terminal_default": "alacritty",
    }


# --- --help wiring ------------------------------------------------------------


def test_help_lists_fix_terminal_flag():
    res = subprocess.run(
        [str(CAST_DOCTOR), "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert res.returncode == 0
    assert "--fix-terminal" in res.stdout


# --- RED-list prerequisite tests ---------------------------------------------


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
    # Provide every essential the script needs EXCEPT tmux.
    _make_fake_bin(fake_bin, names=[])
    # Install host tools the script depends on (uv, git, claude shims so the
    # other RED checks don't bail before we evaluate tmux output).
    for name in ("uv", "git", "claude"):
        shim = fake_bin / name
        shim.write_text("#!/bin/sh\ncase \"$1\" in --version) echo '99.99.99';; esac\n")
        shim.chmod(0o755)

    env = _isolated_env({"PATH": str(fake_bin)})
    res = subprocess.run(
        [str(CAST_DOCTOR)],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(REPO_ROOT),
        timeout=15,
    )
    combined = res.stdout + res.stderr
    assert res.returncode != 0, combined
    assert "tmux not found" in combined
    # Hint should reference some installer (brew/apt/dnf/pacman/package manager).
    assert any(
        token in combined
        for token in ("brew install tmux", "apt install tmux", "dnf install tmux",
                      "pacman -S tmux", "package manager")
    ), combined


def test_cast_doctor_red_on_old_python(tmp_path):
    """Inject a fake python3 reporting 3.10 → cast-doctor flags it RED."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    # Fake python3 that responds to `-c '...'` with a hardcoded 3.10 triple,
    # mimicking the real interpreter's output shape.
    fake_python = fake_bin / "python3"
    fake_python.write_text(
        "#!/bin/sh\n"
        "case \"$1\" in\n"
        "  -c) echo '3.10.12'; exit 0;;\n"
        "  *)  echo 'Python 3.10.12'; exit 0;;\n"
        "esac\n"
    )
    fake_python.chmod(0o755)

    # Add real essentials so the script runs at all.
    for tool in ("env", "sh", "bash", "uname", "mkdir", "tr", "grep", "head",
                 "cat", "dirname", "tmux", "uv", "git", "claude"):
        real = shutil.which(tool)
        if real and not (fake_bin / tool).exists():
            (fake_bin / tool).symlink_to(real)

    env = _isolated_env({"PATH": str(fake_bin)})
    res = subprocess.run(
        [str(CAST_DOCTOR)],
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
