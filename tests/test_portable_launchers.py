"""Portable-launcher contract tests for bin/cast-server and bin/cast-hook.

Proves that the Python-based launchers resolve the repo root without bash
and construct the correct ``uv run`` command line.  Tests run the launcher
scripts in an environment with **no** ``bash`` on ``PATH`` to verify the
bash-free guarantee.
"""
from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

# Ensure tests/ is importable for the shared fake_bin_helper module.
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from fake_bin_helper import make_fake_bin  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
CAST_SERVER = REPO_ROOT / "bin" / "cast-server"
CAST_HOOK = REPO_ROOT / "bin" / "cast-hook"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _make_clean_path(tmp_path: Path, *, include_bash: bool = False) -> str:
    """Build a minimal PATH that has python3 and uv but *not* bash.

    When ``include_bash`` is False (default), bash is intentionally excluded
    so the test proves launcher resolution is bash-free.
    """
    fake_bin = make_fake_bin(
        tmp_path / "fake_bin", include_bash=include_bash,
    )

    # Provide a *fake* uv that just prints the argv it would receive.
    # We do NOT want to actually run the server — only confirm the launcher
    # constructs the right exec call.
    fake_uv = fake_bin / "uv"
    fake_uv.write_text(textwrap.dedent("""\
        #!/bin/sh
        # Echo each argument on its own line so we can assert exact tokens.
        for arg in "$@"; do
            echo "$arg"
        done
    """))
    fake_uv.chmod(0o755)

    return str(fake_bin)


def _launcher_env(tmp_path: Path, *, include_bash: bool = False) -> dict[str, str]:
    """Return an isolated env dict with no bash (unless requested)."""
    path = _make_clean_path(tmp_path, include_bash=include_bash)
    return {
        "HOME": os.environ.get("HOME", str(tmp_path / "home")),
        "PATH": path,
        "LANG": "C.UTF-8",
        # Clear variables the launcher reads so we get deterministic defaults.
        "CAST_BIND_HOST": "",
        "CAST_PORT": "",
    }


def _run_launcher(
    script: Path,
    env: dict[str, str],
    extra_args: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(script), *(extra_args or [])],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(REPO_ROOT),
        timeout=15,
    )


# ---------------------------------------------------------------------------
# bin/cast-server tests
# ---------------------------------------------------------------------------


class TestCastServerLauncher:
    """Tests for the portable bin/cast-server launcher.

    Structural checks (shebang, executable bit, no BASH_SOURCE) are
    covered by ``test_portability_verification.py::TestEntryPointStructure``.
    """

    def test_resolves_repo_dir_without_bash(self, tmp_path):
        """Launcher constructs the correct uv argv without bash on PATH."""
        env = _launcher_env(tmp_path, include_bash=False)
        result = _run_launcher(CAST_SERVER, env)
        lines = result.stdout.strip().splitlines()

        # The fake uv echoes each argument; verify the key tokens.
        assert "run" in lines
        assert "--project" in lines
        project_idx = lines.index("--project")
        assert lines[project_idx + 1] == str(REPO_ROOT)
        assert "uvicorn" in lines
        assert "cast_server.app:app" in lines
        assert "--app-dir" in lines
        app_dir_idx = lines.index("--app-dir")
        assert lines[app_dir_idx + 1] == str(REPO_ROOT / "cast-server")

    def test_default_host_and_port(self, tmp_path):
        """Without env overrides, defaults to 127.0.0.1:8005."""
        env = _launcher_env(tmp_path)
        # Clear to trigger defaults.
        env.pop("CAST_BIND_HOST", None)
        env.pop("CAST_PORT", None)
        result = _run_launcher(CAST_SERVER, env)
        lines = result.stdout.strip().splitlines()

        assert "--host" in lines
        host_idx = lines.index("--host")
        assert lines[host_idx + 1] == "127.0.0.1"

        assert "--port" in lines
        port_idx = lines.index("--port")
        assert lines[port_idx + 1] == "8005"

    def test_env_overrides_host_and_port(self, tmp_path):
        """CAST_BIND_HOST and CAST_PORT are forwarded."""
        env = _launcher_env(tmp_path)
        env["CAST_BIND_HOST"] = "0.0.0.0"
        env["CAST_PORT"] = "9090"
        result = _run_launcher(CAST_SERVER, env)
        lines = result.stdout.strip().splitlines()

        host_idx = lines.index("--host")
        assert lines[host_idx + 1] == "0.0.0.0"

        port_idx = lines.index("--port")
        assert lines[port_idx + 1] == "9090"

    def test_extra_args_forwarded(self, tmp_path):
        """Trailing CLI arguments are appended to the uv command."""
        env = _launcher_env(tmp_path)
        result = _run_launcher(CAST_SERVER, env, extra_args=["--reload", "--workers", "4"])
        lines = result.stdout.strip().splitlines()

        assert "--reload" in lines
        assert "--workers" in lines
        assert "4" in lines

    def test_empty_cast_port_uses_default(self, tmp_path):
        """CAST_PORT='' falls back to default 8005 (bash ${VAR:-default} parity)."""
        env = _launcher_env(tmp_path)
        env["CAST_PORT"] = ""
        result = _run_launcher(CAST_SERVER, env)
        lines = result.stdout.strip().splitlines()

        port_idx = lines.index("--port")
        assert lines[port_idx + 1] == "8005"

    def test_empty_cast_bind_host_uses_default(self, tmp_path):
        """CAST_BIND_HOST='' falls back to default 127.0.0.1 (bash parity)."""
        env = _launcher_env(tmp_path)
        env["CAST_BIND_HOST"] = ""
        result = _run_launcher(CAST_SERVER, env)
        lines = result.stdout.strip().splitlines()

        host_idx = lines.index("--host")
        assert lines[host_idx + 1] == "127.0.0.1"


# ---------------------------------------------------------------------------
# bin/cast-hook tests
# ---------------------------------------------------------------------------


class TestCastHookLauncher:
    """Tests for the portable bin/cast-hook launcher.

    Structural checks (shebang, executable bit, no BASH_SOURCE) are
    covered by ``test_portability_verification.py::TestEntryPointStructure``.
    """

    def test_resolves_repo_dir_without_bash(self, tmp_path):
        """Launcher constructs the correct uv argv without bash on PATH."""
        env = _launcher_env(tmp_path, include_bash=False)
        result = _run_launcher(CAST_HOOK, env)
        lines = result.stdout.strip().splitlines()

        assert "run" in lines
        assert "--project" in lines
        project_idx = lines.index("--project")
        assert lines[project_idx + 1] == str(REPO_ROOT)
        assert "cast-hook" in lines

    def test_extra_args_forwarded(self, tmp_path):
        """Trailing CLI arguments are appended to the uv command."""
        env = _launcher_env(tmp_path, include_bash=False)
        result = _run_launcher(CAST_HOOK, env, extra_args=["user-prompt-start"])
        lines = result.stdout.strip().splitlines()

        assert "cast-hook" in lines
        assert "user-prompt-start" in lines


# ---------------------------------------------------------------------------
# Hook-install path-shape tests
# ---------------------------------------------------------------------------


class TestHookInstallPathShape:
    """Verify that install_hooks and hook_events still use the correct
    absolute path to cast-hook — the launcher path did not change, only
    the implementation language.
    """

    def test_cast_hook_bin_is_under_diecast_skills(self):
        """CAST_HOOK_BIN resolves through ~/.claude/skills/diecast/bin/cast-hook."""
        from cast_server.cli.hook_events import CAST_HOOK_BIN

        assert CAST_HOOK_BIN.endswith("/bin/cast-hook")
        assert "/.claude/skills/diecast/" in CAST_HOOK_BIN

    def test_command_for_event_shape(self):
        """Each command starts with the absolute CAST_HOOK_BIN prefix."""
        from cast_server.cli.hook_events import CAST_HOOK_BIN, COMMAND_FOR_EVENT

        for event, cmd in COMMAND_FOR_EVENT.items():
            assert cmd.startswith(CAST_HOOK_BIN), (
                f"Event {event!r} command {cmd!r} does not start with CAST_HOOK_BIN"
            )

    def test_hook_events_comment_no_longer_references_lib_sh(self):
        """The _lib.sh reference in hook_events.py should be updated."""
        source = (REPO_ROOT / "cast-server" / "cast_server" / "cli" / "hook_events.py").read_text()
        # The old reference was the sole mention of _lib.sh; we updated it
        # to reference bootstrap/common.py.  Verify the old pattern is gone
        # from the primary comment.
        assert "see bin/_lib.sh::install_diecast_skill_root)" not in source
        # The updated comment references bootstrap/common.py.
        assert "bootstrap/common.py" in source
