"""US7 spec-kit shape — cast-spec-checker regression tests.

Covers the shape contract documented in
`agents/cast-spec-checker/cast-spec-checker.md`:

  R1 — required sections present
  R2 — each User Story has Priority
  R3 — each User Story has Independent test (warning)
  R4 — each User Story has at least one EARS-style acceptance scenario
  R5 — duplicate FR/SC identifiers
  R6 — no orphan [NEEDS CLARIFICATION] markers
  R7 — no mixed shape

The fixtures under `tests/fixtures/specs/` exercise both clean and
violation cases for cast-refine-requirements output and
cast-update-spec output.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECKER = REPO_ROOT / "bin" / "cast-spec-checker"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "specs"


def run_checker(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(CHECKER), *args]
    return subprocess.run(cmd, capture_output=True, text=True)


def test_us7_clean_refine_passes():
    """Clean cast-refine output passes the checker with exit 0 and no errors."""
    result = run_checker(str(FIXTURES / "refine_clean.md"))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "error" not in result.stdout.lower()


def test_us7_violations_flagged_with_file_line():
    """Violations are reported as `<file>:<line>: <severity> <rule>: <msg>`."""
    fixture = FIXTURES / "refine_violations.md"
    result = run_checker(str(fixture))
    assert result.returncode != 0
    error_lines = [ln for ln in result.stdout.splitlines() if " error " in ln]
    assert error_lines, f"expected at least one error line; stdout was:\n{result.stdout}"
    for ln in error_lines:
        # Each violation line starts with `<file>:<line>:`
        prefix = f"{fixture}:"
        assert ln.startswith(prefix), f"missing file:line prefix in: {ln}"
        # Confirm the line number is parseable
        rest = ln[len(prefix):]
        line_no, _ = rest.split(":", 1)
        assert line_no.isdigit(), f"non-numeric line in: {ln}"


def test_us7_update_spec_create_clean():
    """cast-update-spec create-mode output passes the checker."""
    result = run_checker(str(FIXTURES / "update_spec_create.md"))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "error" not in result.stdout.lower()


def test_us7_update_spec_backfill_clean():
    """cast-update-spec backfill-mode output passes the checker."""
    result = run_checker(str(FIXTURES / "update_spec_backfill.md"))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "error" not in result.stdout.lower()


def test_us7_orphan_needs_clarification_flagged():
    """Inline [NEEDS CLARIFICATION] without a matching Open Questions entry → error."""
    result = run_checker(str(FIXTURES / "refine_violations.md"))
    assert result.returncode != 0
    # Either an explicit "orphan" R6 line or the marker appears in the output.
    haystack = result.stdout.lower()
    assert (
        "r6" in haystack
        and "needs clarification" in haystack
    ), f"orphan rule not surfaced; stdout was:\n{result.stdout}"


def test_us7_warn_only_mode_exits_zero_on_violations():
    """The --warn-only flag causes exit 0 even when errors are present.

    This is the v1.0 rollout escape hatch documented in the sub-phase 4a
    plan (Risk #4 mitigation). The checker still prints the findings.
    """
    fixture = FIXTURES / "refine_violations.md"
    result = run_checker("--warn-only", str(fixture))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "error" in result.stdout.lower(), (
        "warn-only must still print findings, not silence them"
    )


def test_us7_template_exists_and_has_worked_examples():
    """Both worked examples must be present in the canonical template."""
    template = REPO_ROOT / "templates" / "cast-spec.template.md"
    assert template.is_file()
    text = template.read_text(encoding="utf-8")
    assert "Worked Example: P1 User Story" in text
    assert "Worked Example: Spec with Open Item" in text


def test_us7_producers_reference_template():
    """cast-refine-requirements and cast-update-spec both reference the template."""
    refine = (
        REPO_ROOT
        / "agents"
        / "cast-refine-requirements"
        / "cast-refine-requirements.md"
    )
    update = REPO_ROOT / "agents" / "cast-update-spec" / "cast-update-spec.md"
    for path in (refine, update):
        text = path.read_text(encoding="utf-8")
        assert "templates/cast-spec.template.md" in text, (
            f"{path} missing reference to templates/cast-spec.template.md"
        )


def test_us7_checker_boundary_documented():
    """cast-spec-checker prompt mentions cast-agent-compliance as the boundary."""
    prompt = (
        REPO_ROOT
        / "agents"
        / "cast-spec-checker"
        / "cast-spec-checker.md"
    )
    text = prompt.read_text(encoding="utf-8")
    assert "cast-agent-compliance" in text, (
        "cast-spec-checker must document its boundary vs cast-agent-compliance"
    )


@pytest.mark.parametrize(
    "fixture_name",
    ["refine_clean.md", "update_spec_create.md", "update_spec_backfill.md"],
)
def test_us7_clean_fixtures_have_no_warnings_either(fixture_name: str):
    """The clean fixtures should not trigger R3 warnings either."""
    fixture = FIXTURES / fixture_name
    result = run_checker(str(fixture))
    assert "warning" not in result.stdout.lower(), (
        f"{fixture} produced a warning line:\n{result.stdout}"
    )
