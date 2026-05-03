"""Shared test fixtures for the bash-portability test suite."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def make_fake_bin(
    dir_: Path,
    names: list[str] | None = None,
    *,
    include_bash: bool = False,
) -> Path:
    """Create a minimal PATH directory with python3 and POSIX essentials.

    ``bash`` is excluded unless *include_bash* is True — this is the key
    property that all no-bash tests depend on.

    Args:
        dir_: Directory to create/populate.
        names: Additional executable shim names to create.
        include_bash: Whether to include bash on PATH.

    Returns:
        The *dir_* path (created if it did not exist).
    """
    dir_.mkdir(parents=True, exist_ok=True)

    # python3 wrapper — exec's the current interpreter so venv packages
    # remain importable.
    py_wrapper = dir_ / "python3"
    py_wrapper.write_text(f'#!/bin/sh\nexec {sys.executable} "$@"\n')
    py_wrapper.chmod(0o755)

    # POSIX essentials used by shebangs and shims.
    for tool in (
        "env", "sh", "uname", "mkdir", "date", "dirname",
        "tr", "grep", "head", "cat", "rm",
    ):
        real = shutil.which(tool)
        if real and not (dir_ / tool).exists():
            (dir_ / tool).symlink_to(real)

    # Extra named shims (e.g. "uv", "git", "tmux", terminal executables).
    for name in (names or []):
        shim = dir_ / name
        if not shim.exists():
            shim.write_text("#!/bin/sh\nexit 0\n")
            shim.chmod(0o755)

    if include_bash:
        real_bash = shutil.which("bash")
        if real_bash and not (dir_ / "bash").exists():
            (dir_ / "bash").symlink_to(real_bash)
    else:
        # Ensure bash is absent.
        bash_path = dir_ / "bash"
        if bash_path.exists() or bash_path.is_symlink():
            bash_path.unlink()

    return dir_
