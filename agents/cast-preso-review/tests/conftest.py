"""Shared pytest fixtures for cast-preso-review.

Later sub-phases (1b, 1c, 1d) add tests on top; this file owns the fixtures
they rely on so the scaffolds stay small.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

AGENT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AGENT_DIR.parents[1]

# Make `import build` work when tests run via pytest (the agent dir uses hyphens,
# so we can't rely on package-style import from the repo root).
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))


@pytest.fixture
def tmp_goal_dir(tmp_path: Path) -> Path:
    """Return a temp dir shaped like a goal dir. Tests populate it with fixtures."""
    goal = tmp_path / "goals" / "fixture-goal"
    goal.mkdir(parents=True)
    return goal


@pytest.fixture
def copy_fixture(tmp_goal_dir: Path):
    """Copy a named fixture from tests/fixtures/ into the tmp goal dir.

    Used by 1b/1c tests — 1a's ``tests/fixtures/`` is empty, so callers skip
    cleanly when their fixture hasn't been added yet.
    """
    fixtures_root = AGENT_DIR / "tests" / "fixtures"

    def _copy(name: str) -> Path:
        src = fixtures_root / name
        if not src.exists():
            pytest.skip(f"fixture '{name}' not present yet (added by later sub-phase)")
        dest = tmp_goal_dir / src.name
        if src.is_dir():
            shutil.copytree(src, dest, dirs_exist_ok=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
        return dest

    return _copy
