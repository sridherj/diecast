"""Planted-fixture regression tests for `bin/audit-interdependencies`.

Each fixture under `tests/fixtures/audit-interdependencies/` is a self-contained
mini-fleet that the script scans via `--fixture-dir`. The `green-baseline`
fixture must exit 0; every `should-fail-*` fixture must exit 1 under
`--fail-on=red` AND surface the documented marker reason in its JSON output.

If the script regresses (e.g. naming check stops flagging missing targets),
the matching fixture flips, pytest fails, and CI blocks the merge.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIT = REPO_ROOT / "bin" / "audit-interdependencies"
FIXTURES_BASE = REPO_ROOT / "tests" / "fixtures" / "audit-interdependencies"


def _run(fixture: Path, *, json_mode: bool = False) -> subprocess.CompletedProcess:
    args = [
        sys.executable,
        str(AUDIT),
        "--fail-on=red",
        "--fixture-dir",
        str(fixture),
    ]
    if json_mode:
        args.append("--json")
    return subprocess.run(args, capture_output=True, text=True)


def test_audit_script_help_runs() -> None:
    """`--help` must succeed and document the locked flag surface."""
    result = subprocess.run(
        [sys.executable, str(AUDIT), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--mode" in result.stdout
    assert "--json" in result.stdout
    assert "--fail-on" in result.stdout
    assert "--fixture-dir" in result.stdout


def test_green_baseline_exits_zero() -> None:
    fixture = FIXTURES_BASE / "green-baseline"
    assert fixture.is_dir(), f"missing fixture: {fixture}"
    result = _run(fixture)
    assert result.returncode == 0, (
        f"green-baseline expected exit 0, got {result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


# Each row: (fixture name, expected reason substring in a red finding).
FAIL_FIXTURES = [
    ("should-fail-naming", "target not found in fleet"),
    ("should-fail-folder", "User-home Claude config; violates US2"),
    ("should-fail-recovery", "No fallback / no early-exit / no user prompt"),
    ("should-fail-cross-skill", "target not found in fleet"),
]


@pytest.mark.parametrize("fixture_name,expected_reason", FAIL_FIXTURES)
def test_should_fail_fixture_exits_one_with_marker(
    fixture_name: str, expected_reason: str
) -> None:
    fixture = FIXTURES_BASE / fixture_name
    assert fixture.is_dir(), f"missing fixture: {fixture}"

    # Exit code gate.
    result = _run(fixture)
    assert result.returncode == 1, (
        f"{fixture_name}: expected exit 1, got {result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )

    # JSON marker gate — guards against the wrong-reason failure mode flagged
    # in the sub-phase Risks section.
    json_result = _run(fixture, json_mode=True)
    payload = json.loads(json_result.stdout)
    red_reasons = {f["reason"] for f in payload["findings"] if f["status"] == "red"}
    assert expected_reason in red_reasons, (
        f"{fixture_name}: expected red reason {expected_reason!r} not found.\n"
        f"observed red reasons: {sorted(red_reasons)}"
    )


def test_fixture_dir_resolves_relative_paths(tmp_path: Path) -> None:
    """`--fixture-dir` must accept relative paths (used by CI invocations)."""
    fixture = FIXTURES_BASE / "green-baseline"
    rel = fixture.relative_to(REPO_ROOT)
    result = subprocess.run(
        [sys.executable, str(AUDIT), "--fail-on=red", "--fixture-dir", str(rel)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_missing_fixture_dir_returns_two() -> None:
    """Script must surface a clear error (exit 2) when the fixture dir is absent."""
    result = subprocess.run(
        [sys.executable, str(AUDIT), "--fixture-dir", "/nonexistent/path/abc123"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "fixture-dir not found" in result.stderr
