"""Smoke test for the Phase-1 `bin/audit-interdependencies` no-op skeleton."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIT = REPO_ROOT / "bin" / "audit-interdependencies"


def test_audit_stub_exits_zero_on_clean_tree(tmp_path: Path) -> None:
    """Phase-1 stub is a no-op that prints a marker and exits 0."""
    result = subprocess.run(
        [sys.executable, str(AUDIT)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "audit-interdependencies stub" in result.stdout
