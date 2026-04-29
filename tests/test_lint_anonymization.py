"""Tests for `bin/lint-anonymization`.

Per Phase-1.3 D9: no per-pattern-fires tests, no false-positive corpus.
The four cases below cover the structural guarantees only.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import List

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
LINT = REPO_ROOT / "bin" / "lint-anonymization"

# Constructed from two halves so this test file doesn't itself contain the
# literal forbidden token (which would trip the lint that runs in CI).
SJ_LITERAL = "S" + "J"


def _run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    cmd: List[str] = [sys.executable, str(LINT), *args]
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def _git_init(path: Path) -> None:
    """Initialize a quiet git repo so `git ls-files` enumerates the tree."""
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "test"], check=True)
    subprocess.run(["git", "-C", str(path), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(path), "commit", "-q", "-m", "init"],
        check=True,
    )


def test_clean_tree_exits_zero(tmp_path: Path) -> None:
    """A tree with no forbidden patterns exits 0."""
    (tmp_path / "README.md").write_text("Just a normal readme.\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def main():\n    return 0\n")
    _git_init(tmp_path)

    result = _run(cwd=tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_default_excludes_forbidden_fixture_dir(tmp_path: Path) -> None:
    """`tests/fixtures/forbidden/` is not scanned without --include-fixtures.

    The fixture file contains a deliberate forbidden token (an initials
    leak); the default scan must still exit clean because the directory is
    excluded.
    """
    fixtures = tmp_path / "tests" / "fixtures" / "forbidden"
    fixtures.mkdir(parents=True)
    (fixtures / "leak.md").write_text(f"{SJ_LITERAL} shipped this.\n")
    (tmp_path / "README.md").write_text("normal\n")
    _git_init(tmp_path)

    default = _run(cwd=tmp_path)
    assert default.returncode == 0, default.stdout + default.stderr

    included = _run("--include-fixtures", cwd=tmp_path)
    assert included.returncode == 1
    assert "leak.md" in included.stdout


def test_exemption_marker_skips_line(tmp_path: Path) -> None:
    """Any line carrying `# diecast-lint: ignore-line` is skipped, even if it
    contains an otherwise-forbidden token."""
    src = tmp_path / "notes.md"
    src.write_text(
        f"{SJ_LITERAL} should fire on this line\n"
        f"{SJ_LITERAL} should NOT fire here  <!-- diecast-lint: ignore-line -->\n"
    )
    _git_init(tmp_path)

    result = _run(cwd=tmp_path)
    assert result.returncode == 1
    # First line fires, second does not.
    assert "notes.md:1:" in result.stdout
    assert "notes.md:2:" not in result.stdout


def test_performance_under_5_seconds(tmp_path: Path) -> None:
    """Scanning a 100-file synthetic tree completes in under 5 seconds."""
    pkg = tmp_path / "agents"
    pkg.mkdir()
    body = (
        "# Sample agent doc\n"
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n"
        "Pretty harmless content with no forbidden tokens.\n" * 6
    )
    for i in range(100):
        (pkg / f"agent_{i:03d}.md").write_text(body)
    _git_init(tmp_path)

    import time

    started = time.monotonic()
    result = _run(cwd=tmp_path)
    elapsed = time.monotonic() - started

    assert result.returncode == 0, result.stdout + result.stderr
    assert elapsed < 5.0, f"lint took {elapsed:.2f}s on a 100-file tree"


@pytest.fixture(autouse=True)
def _ensure_lint_executable() -> None:
    if not LINT.exists():
        pytest.fail(f"lint script missing: {LINT}")
    if shutil.which("git") is None:
        pytest.skip("git not available")
