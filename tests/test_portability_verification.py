"""Final portability verification — proves user-facing commands work without bash.

Task 5 of the bash-portability plan.  This module exercises the fully migrated
command surface (``./setup``, ``bin/cast-doctor``, ``bin/cast-server``,
``bin/cast-hook``) in environments with:

1. **No bash on PATH** — verifies every entry point resolves and runs using
   only Python and POSIX ``/bin/sh``.
2. **Clean environment** — system Python exists but project dependencies are
   absent (no ``uv``, or old ``uv``), proving the doctor emits structured
   RED findings instead of crashing.
3. **Controlled fake terminal candidates** — ``--fix-terminal`` exercises the
   interactive picker with deterministic candidate sets and no bash.

These are *subprocess-level* integration tests.  Each test builds a minimal
isolated ``PATH`` that includes only what is strictly required (``python3``,
``env``, ``sh``, and selective shims) and explicitly excludes ``bash``.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

# Ensure tests/ is importable for the shared fake_bin_helper module.
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from fake_bin_helper import make_fake_bin as _make_fake_bin  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
SETUP_SCRIPT = REPO_ROOT / "setup"
CAST_DOCTOR = REPO_ROOT / "bin" / "cast-doctor"
CAST_SERVER = REPO_ROOT / "bin" / "cast-server"
CAST_HOOK = REPO_ROOT / "bin" / "cast-hook"


def _base_env(tmp_path: Path, fake_bin: Path) -> dict[str, str]:
    """Return an isolated env dict — no bash, minimal PATH.

    Args:
        tmp_path: Temporary directory for HOME.
        fake_bin: The fake bin directory to use as PATH.

    Returns:
        Environment dict suitable for subprocess.run.
    """
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    return {
        "HOME": str(home),
        "PATH": str(fake_bin),
        "LANG": "C.UTF-8",
        "CAST_TERMINAL": "",
        "TERMINAL": "",
        "XDG_CURRENT_DESKTOP": "",
    }


def _run_entry_point(
    script: Path,
    args: list[str],
    env: dict[str, str],
    *,
    stdin: str = "",
    timeout: int = 30,
) -> subprocess.CompletedProcess[str]:
    """Run an entry point as a subprocess with the given environment.

    Args:
        script: Path to the entry-point script.
        args: CLI arguments.
        env: Environment dict.
        stdin: Optional stdin text.
        timeout: Subprocess timeout in seconds.

    Returns:
        CompletedProcess result.
    """
    return subprocess.run(
        [sys.executable, str(script)] + args,
        input=stdin,
        text=True,
        capture_output=True,
        env=env,
        cwd=str(REPO_ROOT),
        timeout=timeout,
    )


def _add_version_shims(fake_bin: Path, names: list[str]) -> None:
    """Add executable shims that report a high version number.

    Each shim responds to ``--version`` with ``99.99.99`` so prerequisite
    checks pass.

    Args:
        fake_bin: Directory to add shims to.
        names: Tool names to create version-reporting shims for.
    """
    for name in names:
        shim = fake_bin / name
        shim.write_text(
            '#!/bin/sh\n'
            'case "$1" in --version) echo \'99.99.99\';; esac\n'
        )
        shim.chmod(0o755)


# ═══════════════════════════════════════════════════════════════════
# 1. No-bash-on-PATH — ./setup
# ═══════════════════════════════════════════════════════════════════


class TestSetupNoBash:
    """Verify ``./setup`` runs without bash on PATH."""

    def test_setup_dry_run_no_prompt_no_bash(self, tmp_path: Path) -> None:
        """./setup --dry-run --no-prompt completes without bash on PATH.

        This is the primary end-user portability proof for the installer:
        a fresh clone where bash is absent should still be able to run
        ``./setup --dry-run --no-prompt`` and see dry-run output.
        """
        fake_bin = _make_fake_bin(tmp_path / "bin")
        # Doctor needs version-reporting shims to pass prereqs.
        _add_version_shims(fake_bin, ["uv", "git", "claude", "tmux"])
        # Setup needs a fake uv for generate-skills / alembic steps.
        # Overwrite the version-reporting uv with a noop that handles
        # both --version and run subcommands.
        fake_uv = fake_bin / "uv"
        fake_uv.write_text(textwrap.dedent("""\
            #!/bin/sh
            case "$1" in
                --version) echo 'uv 0.11.8';;
                run) exit 0;;
                *) exit 0;;
            esac
        """))
        fake_uv.chmod(0o755)

        env = _base_env(tmp_path, fake_bin)
        env["CAST_TERMINAL"] = "kitty"  # satisfy terminal check
        env["DRY_RUN"] = ""  # let the flag drive, not env

        result = _run_entry_point(
            SETUP_SCRIPT, ["--dry-run", "--no-prompt"], env,
        )

        # Should not crash; dry-run produces DRY: prefixed log lines.
        assert result.returncode == 0, (
            f"setup --dry-run --no-prompt failed:\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
        assert "DRY:" in result.stdout

    def test_setup_help_no_bash(self, tmp_path: Path) -> None:
        """./setup --help works without bash on PATH."""
        fake_bin = _make_fake_bin(tmp_path / "bin")
        env = _base_env(tmp_path, fake_bin)
        result = _run_entry_point(SETUP_SCRIPT, ["--help"], env)
        assert result.returncode == 0
        assert "--dry-run" in result.stdout
        assert "--upgrade" in result.stdout
        assert "--no-prompt" in result.stdout


# ═══════════════════════════════════════════════════════════════════
# 2. No-bash-on-PATH — bin/cast-doctor
# ═══════════════════════════════════════════════════════════════════


class TestCastDoctorNoBash:
    """Verify ``bin/cast-doctor`` --fix-terminal runs without bash on PATH.

    Basic CLI flag tests (--json, --quiet, --help) are covered by
    ``test_cast_doctor.py``.  This class focuses on the --fix-terminal
    interactive flow in a bash-free environment.
    """

    @pytest.mark.skipif(
        os.uname().sysname != "Linux",
        reason="--fix-terminal probe path is Linux-specific",
    )
    def test_fix_terminal_single_candidate_no_bash(self, tmp_path: Path) -> None:
        """--fix-terminal with one candidate writes config without bash."""
        fake_bin = _make_fake_bin(tmp_path / "bin", names=["alacritty"])
        _add_version_shims(fake_bin, ["uv", "git", "claude", "tmux"])
        env = _base_env(tmp_path, fake_bin)

        result = _run_entry_point(
            CAST_DOCTOR, ["--fix-terminal"], env, stdin="y\n",
        )
        assert result.returncode == 0, (
            f"--fix-terminal failed:\nstdout={result.stdout}\nstderr={result.stderr}"
        )
        cfg = Path(env["HOME"]) / ".cast" / "config.yaml"
        assert cfg.exists()
        assert "alacritty" in cfg.read_text()

    @pytest.mark.skipif(
        os.uname().sysname != "Linux",
        reason="--fix-terminal probe path is Linux-specific",
    )
    def test_fix_terminal_multi_candidate_no_bash(self, tmp_path: Path) -> None:
        """--fix-terminal with multiple candidates picks by number without bash."""
        fake_bin = _make_fake_bin(
            tmp_path / "bin",
            names=["ptyxis", "gnome-terminal", "kitty"],  # diecast-lint: ignore-line
        )
        _add_version_shims(fake_bin, ["uv", "git", "claude", "tmux"])
        env = _base_env(tmp_path, fake_bin)

        # Pick the second candidate.
        result = _run_entry_point(
            CAST_DOCTOR, ["--fix-terminal"], env, stdin="2\n",
        )
        assert result.returncode == 0, (
            f"--fix-terminal multi failed:\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
        cfg = Path(env["HOME"]) / ".cast" / "config.yaml"
        assert cfg.exists()
        # Second candidate in _LINUX_PROBE_ORDER is gnome-terminal.
        assert "gnome-terminal" in cfg.read_text()

    @pytest.mark.skipif(
        os.uname().sysname != "Linux",
        reason="--fix-terminal probe path is Linux-specific",
    )
    def test_fix_terminal_zero_candidates_no_bash(self, tmp_path: Path) -> None:
        """--fix-terminal with no candidates exits non-zero without bash."""
        fake_bin = _make_fake_bin(tmp_path / "bin")
        env = _base_env(tmp_path, fake_bin)

        result = _run_entry_point(
            CAST_DOCTOR, ["--fix-terminal"], env, stdin="\n",
        )
        assert result.returncode != 0
        combined = result.stdout + result.stderr
        assert "No supported terminal" in combined


# NOTE: cast-server and cast-hook no-bash tests are in
# ``test_portable_launchers.py`` (TestCastServerLauncher, TestCastHookLauncher).
# They are not duplicated here — see item #10 of the code-review cleanup.


# ═══════════════════════════════════════════════════════════════════
# 5. Clean-environment tests — missing or old project dependencies
# ═══════════════════════════════════════════════════════════════════


class TestCleanEnvironmentDoctor:
    """Prove the doctor emits structured RED findings in a clean environment.

    A "clean environment" means system Python exists on PATH but project
    dependencies (uv, git, tmux, claude) are absent or too old.  The
    migrated doctor must emit valid JSON with RED findings rather than
    crashing with an import error or unhandled exception.
    """

    def test_missing_uv_emits_red_json(self, tmp_path: Path) -> None:
        """No ``uv`` on PATH → JSON output contains a RED finding for uv."""
        fake_bin = _make_fake_bin(tmp_path / "bin")
        # Only python3 + POSIX essentials; no uv, git, tmux, or claude.
        env = _base_env(tmp_path, fake_bin)

        result = _run_entry_point(CAST_DOCTOR, ["--json"], env)
        data = json.loads(result.stdout)
        assert set(data.keys()) == {"red", "yellow", "green"}
        assert any("uv" in r for r in data["red"])
        assert result.returncode != 0

    def test_missing_git_emits_red_json(self, tmp_path: Path) -> None:
        """No ``git`` on PATH → JSON output contains a RED finding for git."""
        fake_bin = _make_fake_bin(tmp_path / "bin")
        _add_version_shims(fake_bin, ["uv", "tmux", "claude"])
        env = _base_env(tmp_path, fake_bin)

        result = _run_entry_point(CAST_DOCTOR, ["--json"], env)
        data = json.loads(result.stdout)
        assert any("git" in r for r in data["red"])
        assert result.returncode != 0

    def test_missing_tmux_emits_red_json(self, tmp_path: Path) -> None:
        """No ``tmux`` on PATH → JSON output contains a RED finding for tmux."""
        fake_bin = _make_fake_bin(tmp_path / "bin")
        _add_version_shims(fake_bin, ["uv", "git", "claude"])
        env = _base_env(tmp_path, fake_bin)

        result = _run_entry_point(CAST_DOCTOR, ["--json"], env)
        data = json.loads(result.stdout)
        assert any("tmux" in r for r in data["red"])
        assert result.returncode != 0

    def test_old_uv_emits_red_json(self, tmp_path: Path) -> None:
        """Old ``uv`` version → RED finding with the version number."""
        fake_bin = _make_fake_bin(tmp_path / "bin")
        _add_version_shims(fake_bin, ["git", "tmux", "claude"])
        # Create a uv that reports an old version.
        old_uv = fake_bin / "uv"
        old_uv.write_text(
            '#!/bin/sh\n'
            'case "$1" in --version) echo \'uv 0.3.9\';; esac\n'
        )
        old_uv.chmod(0o755)
        env = _base_env(tmp_path, fake_bin)

        result = _run_entry_point(CAST_DOCTOR, ["--json"], env)
        data = json.loads(result.stdout)
        assert any("uv" in r and "0.3" in r for r in data["red"])
        assert result.returncode != 0

    def test_old_python_emits_red_json(self, tmp_path: Path) -> None:
        """Old Python version → RED finding referencing 3.10 and 3.11."""
        fake_bin = _make_fake_bin(tmp_path / "bin")
        _add_version_shims(fake_bin, ["uv", "git", "tmux", "claude"])
        # Overwrite the python3 wrapper to report an old version.
        old_py = fake_bin / "python3"
        old_py.write_text(
            "#!/bin/sh\n"
            "case \"$1\" in\n"
            "  -c) echo '3.10.12'; exit 0;;\n"
            "  *)  echo 'Python 3.10.12'; exit 0;;\n"
            "esac\n"
        )
        old_py.chmod(0o755)
        env = _base_env(tmp_path, fake_bin)

        result = _run_entry_point(CAST_DOCTOR, ["--json"], env)
        data = json.loads(result.stdout)
        assert any("python3" in r and "3.10" in r for r in data["red"])
        assert result.returncode != 0

    def test_all_missing_emits_multiple_reds(self, tmp_path: Path) -> None:
        """All dependencies absent → multiple RED findings in one report."""
        fake_bin = _make_fake_bin(tmp_path / "bin")
        # Only python3 and POSIX essentials; nothing else.
        env = _base_env(tmp_path, fake_bin)

        result = _run_entry_point(CAST_DOCTOR, ["--json"], env)
        data = json.loads(result.stdout)
        red_text = " ".join(data["red"])
        assert "uv" in red_text
        assert "git" in red_text
        assert "tmux" in red_text
        assert len(data["red"]) >= 3
        assert result.returncode != 0

    def test_clean_env_human_output_does_not_crash(self, tmp_path: Path) -> None:
        """Human-readable output (no --json) does not crash in clean env."""
        fake_bin = _make_fake_bin(tmp_path / "bin")
        env = _base_env(tmp_path, fake_bin)

        result = _run_entry_point(CAST_DOCTOR, [], env)
        # Should not crash — exit non-zero with human-readable errors.
        assert result.returncode != 0
        combined = result.stdout + result.stderr
        assert "required prerequisite" in combined.lower() or "[RED]" in combined


# ═══════════════════════════════════════════════════════════════════
# 6. Direct entry-point structural verification
# ═══════════════════════════════════════════════════════════════════


class TestEntryPointStructure:
    """Structural checks across all four user-facing entry points.

    Proves the migration contract: every entry point uses a Python shebang,
    is executable, and contains no BASH_SOURCE in non-comment lines.
    """

    @pytest.mark.parametrize(
        "script", [SETUP_SCRIPT, CAST_DOCTOR, CAST_SERVER, CAST_HOOK],
        ids=["setup", "cast-doctor", "cast-server", "cast-hook"],
    )
    def test_shebang_is_python(self, script: Path) -> None:
        """Entry point uses a python3 shebang."""
        first_line = script.read_text().splitlines()[0]
        assert "python" in first_line, f"Expected python shebang: {first_line}"
        assert "bash" not in first_line

    @pytest.mark.parametrize(
        "script", [SETUP_SCRIPT, CAST_DOCTOR, CAST_SERVER, CAST_HOOK],
        ids=["setup", "cast-doctor", "cast-server", "cast-hook"],
    )
    def test_is_executable(self, script: Path) -> None:
        """Entry point file has the executable bit set."""
        assert os.access(script, os.X_OK)

    @pytest.mark.parametrize(
        "script", [SETUP_SCRIPT, CAST_DOCTOR, CAST_SERVER, CAST_HOOK],
        ids=["setup", "cast-doctor", "cast-server", "cast-hook"],
    )
    def test_no_bash_source_in_code(self, script: Path) -> None:
        """Entry point does not use BASH_SOURCE in executable code."""
        for lineno, line in enumerate(script.read_text().splitlines(), start=1):
            stripped = line.lstrip()
            if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'"):
                continue
            assert "BASH_SOURCE" not in line, (
                f"BASH_SOURCE in {script.name}:{lineno}: {line}"
            )

    def test_lib_sh_does_not_exist(self) -> None:
        """bin/_lib.sh has been removed."""
        assert not (REPO_ROOT / "bin" / "_lib.sh").exists()

    @pytest.mark.parametrize(
        "script", [SETUP_SCRIPT, CAST_DOCTOR, CAST_SERVER, CAST_HOOK],
        ids=["setup", "cast-doctor", "cast-server", "cast-hook"],
    )
    def test_no_source_lib_sh(self, script: Path) -> None:
        """Entry point does not source or reference _lib.sh."""
        content = script.read_text()
        assert "_lib.sh" not in content


# ═══════════════════════════════════════════════════════════════════
# 7. Bootstrap import safety — stdlib-only before project deps
# ═══════════════════════════════════════════════════════════════════


class TestBootstrapImportSafety:
    """Verify bootstrap modules do not import non-stdlib packages at module level.

    The bootstrap cycle constraint requires that ``doctor.py``,
    ``common.py``, and ``setup_flow.py`` use only stdlib at module scope.
    PyYAML and other project dependencies must be behind lazy imports or
    guarded function scope.
    """

    _CAST_SERVER_DIR = REPO_ROOT / "cast-server" / "cast_server" / "bootstrap"

    @pytest.mark.parametrize(
        "module", ["doctor.py", "common.py"],
        ids=["doctor", "common"],
    )
    def test_no_pyyaml_at_module_level(self, module: str) -> None:
        """Module does not ``import yaml`` at module level."""
        src = (self._CAST_SERVER_DIR / module).read_text()
        # Collect lines before first function/class definition.
        module_lines: list[str] = []
        for line in src.splitlines():
            stripped = line.strip()
            if stripped.startswith("def ") or stripped.startswith("class "):
                break
            module_lines.append(stripped)
        module_level = "\n".join(module_lines)
        assert "import yaml" not in module_level, (
            f"{module} must not import yaml at module level — "
            "stdlib-only for bootstrap safety"
        )

    def test_setup_flow_defers_yaml_import(self) -> None:
        """setup_flow.py does not import yaml at module level."""
        src = (self._CAST_SERVER_DIR / "setup_flow.py").read_text()
        module_lines: list[str] = []
        for line in src.splitlines():
            stripped = line.strip()
            if stripped.startswith("def ") or stripped.startswith("class "):
                break
            module_lines.append(stripped)
        module_level = "\n".join(module_lines)
        assert "import yaml" not in module_level, (
            "setup_flow.py must not import yaml at module level"
        )


# ═══════════════════════════════════════════════════════════════════
# 8. Health contract shape — /api/health JSON shape preserved
# ═══════════════════════════════════════════════════════════════════


class TestHealthContractShape:
    """Verify the JSON shape contract is preserved in the doctor output.

    ``/api/health`` shells out to ``bin/cast-doctor --json`` and parses the
    ``{red, yellow, green}`` shape.  These tests prove that exact shape is
    stable across the migration.
    """

    def test_json_keys_exactly_three(self, tmp_path: Path) -> None:
        """JSON output has exactly ``red``, ``yellow``, ``green`` keys."""
        fake_bin = _make_fake_bin(tmp_path / "bin")
        _add_version_shims(fake_bin, ["uv", "git", "claude", "tmux"])
        env = _base_env(tmp_path, fake_bin)
        env["CAST_TERMINAL"] = "kitty"

        result = _run_entry_point(CAST_DOCTOR, ["--json"], env)
        data = json.loads(result.stdout)
        assert sorted(data.keys()) == ["green", "red", "yellow"]

    def test_json_values_are_string_lists(self, tmp_path: Path) -> None:
        """All JSON values are lists of strings."""
        fake_bin = _make_fake_bin(tmp_path / "bin")
        _add_version_shims(fake_bin, ["uv", "git", "claude", "tmux"])
        env = _base_env(tmp_path, fake_bin)
        env["CAST_TERMINAL"] = "kitty"

        result = _run_entry_point(CAST_DOCTOR, ["--json"], env)
        data = json.loads(result.stdout)
        for key, val in data.items():
            assert isinstance(val, list), f"{key} is not a list"
            for item in val:
                assert isinstance(item, str), f"{key} item is not a string: {item!r}"

    def test_exit_code_zero_when_all_green(self, tmp_path: Path) -> None:
        """Exit code is 0 when there are no RED findings."""
        fake_bin = _make_fake_bin(tmp_path / "bin")
        _add_version_shims(fake_bin, ["uv", "git", "claude", "tmux"])
        env = _base_env(tmp_path, fake_bin)
        env["CAST_TERMINAL"] = "kitty"

        result = _run_entry_point(CAST_DOCTOR, ["--json"], env)
        data = json.loads(result.stdout)
        if not data["red"]:
            assert result.returncode == 0
        else:
            # If there are reds (e.g., writable check), exit is non-zero.
            assert result.returncode != 0

    def test_exit_code_nonzero_when_red_present(self, tmp_path: Path) -> None:
        """Exit code is non-zero when RED findings exist."""
        fake_bin = _make_fake_bin(tmp_path / "bin")
        # No uv → guaranteed RED.
        env = _base_env(tmp_path, fake_bin)

        result = _run_entry_point(CAST_DOCTOR, ["--json"], env)
        data = json.loads(result.stdout)
        assert len(data["red"]) > 0
        assert result.returncode != 0
