"""Grep-sweep test — ensures stale bash/shell references do not survive in active docs.

The migration from bash to Python-based entry points (tasks 1–3) replaced
``bin/_lib.sh``, ``SUPPORTED_TERMINALS_FALLBACK``, and bash-as-requirement
language throughout the active documentation, skill contracts, and code.
This test enforces that none of those stale patterns creep back into the
surfaces end-users and contributors read.

Historical/archived docs (``docs/execution/``, ``docs/plan/``) are excluded
because they are point-in-time records that reference the implementation as
it was at authoring time.  CI shell test files (``tests/*.sh``,
``tests/Dockerfile.*``) are excluded because they are permitted to use bash
internally — they are not user-facing contracts.  Bootstrap code docstrings
that mention ``_lib.sh`` as historical migration context are excluded.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# ── Directories / globs that form the "active surface" ──────────────────────
# These are the files end-users, contributors, and skills actually read.

_ACTIVE_GLOBS: list[str] = [
    "README.md",
    "bin/README.md",
    "docs/troubleshooting.md",
    "docs/reference/*.md",
    "docs/specs/*.md",
    "skills/**/*.md",
    ".github/workflows/*.yml",
]

# Directories / patterns excluded from the sweep.  Anything under these paths
# is either a historical execution record, a CI-only shell script, or Python
# code whose docstrings may legitimately reference ``_lib.sh`` as migration
# context.
_EXCLUDED_PREFIXES: tuple[str, ...] = (
    "docs/execution/",
    "docs/plan/",
    "docs/exploration/",
)


def _active_files() -> list[Path]:
    """Collect every file matching the active-surface globs."""
    files: list[Path] = []
    for glob in _ACTIVE_GLOBS:
        files.extend(REPO_ROOT.glob(glob))
    # De-duplicate and filter exclusions.
    seen: set[Path] = set()
    result: list[Path] = []
    for f in sorted(files):
        if f in seen:
            continue
        seen.add(f)
        rel = f.relative_to(REPO_ROOT).as_posix()
        if any(rel.startswith(pfx) for pfx in _EXCLUDED_PREFIXES):
            continue
        result.append(f)
    return result


# ── Stale-pattern definitions ───────────────────────────────────────────────

# Each entry is (human label, compiled regex).
# The regex is applied line-by-line.  A match on ANY active-surface line is a
# test failure unless the line carries a ``<!-- grep-sweep: ignore -->`` or
# ``# grep-sweep: ignore`` marker.

_STALE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "_lib.sh reference",
        re.compile(r"\b_lib\.sh\b"),
    ),
    (
        "SUPPORTED_TERMINALS_FALLBACK reference",
        re.compile(r"SUPPORTED_TERMINALS_FALLBACK"),
    ),
    (
        "bash >= version requirement",
        re.compile(r"bash\s*>=", re.IGNORECASE),
    ),
    (
        "shell fallback language",
        # Match "shell fallback" as a standalone concept (case-insensitive).
        # Exclude "CLI fallback" / "CLI alternative" which are fine.
        re.compile(r"\bshell\s+fallback\b", re.IGNORECASE),
    ),
]

_IGNORE_MARKER = re.compile(r"grep-sweep:\s*ignore")


# ── Tests ────────────────────────────────────────────────────────────────────


class TestDocGrepSweep:
    """Verify that active docs/skills/contracts contain no stale bash-era references."""

    @pytest.fixture(autouse=True)
    def _files(self) -> None:
        self.files = _active_files()
        # Sanity: we should always find at least the top-level README.
        assert len(self.files) > 0, "Active-surface glob matched zero files"

    @pytest.mark.parametrize(
        "label, pattern",
        [(label, pat) for label, pat in _STALE_PATTERNS],
        ids=[label for label, _ in _STALE_PATTERNS],
    )
    def test_no_stale_pattern_in_active_docs(
        self, label: str, pattern: re.Pattern[str]
    ) -> None:
        """No active doc/skill/contract file should contain *pattern*."""
        violations: list[str] = []
        for fpath in self.files:
            try:
                text = fpath.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if _IGNORE_MARKER.search(line):
                    continue
                if pattern.search(line):
                    rel = fpath.relative_to(REPO_ROOT)
                    violations.append(f"  {rel}:{lineno}: {line.strip()}")
        if violations:
            msg = (
                f"Stale '{label}' found in active docs "
                f"({len(violations)} hit(s)):\n"
                + "\n".join(violations)
                + "\n\nFix the reference or add a "
                "'grep-sweep: ignore' marker if it is intentional."
            )
            pytest.fail(msg)

    def test_no_bash_source_in_active_docs(self) -> None:
        """Active docs should not reference BASH_SOURCE as a live contract.

        Comments in Python launcher files that say "no BASH_SOURCE dependency"
        are fine — they describe the *absence* of the pattern.  Only positive
        references (suggesting users/contributors should use BASH_SOURCE) are
        flagged.
        """
        pattern = re.compile(r"BASH_SOURCE")
        # Lines explicitly noting the absence are fine.
        absence_pattern = re.compile(r"no\s+BASH_SOURCE", re.IGNORECASE)
        violations: list[str] = []
        for fpath in self.files:
            try:
                text = fpath.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if _IGNORE_MARKER.search(line):
                    continue
                if absence_pattern.search(line):
                    continue
                if pattern.search(line):
                    rel = fpath.relative_to(REPO_ROOT)
                    violations.append(f"  {rel}:{lineno}: {line.strip()}")
        if violations:
            msg = (
                f"BASH_SOURCE reference found in active docs "
                f"({len(violations)} hit(s)):\n"
                + "\n".join(violations)
                + "\n\nUpdate the reference or add a "
                "'grep-sweep: ignore' marker if it is intentional."
            )
            pytest.fail(msg)

    def test_active_surface_is_non_empty(self) -> None:
        """Sanity: the active-surface glob should match known key files."""
        rel_names = {f.relative_to(REPO_ROOT).as_posix() for f in self.files}
        expected = {
            "README.md",
            "bin/README.md",
            "docs/troubleshooting.md",
        }
        missing = expected - rel_names
        assert not missing, f"Expected active-surface files not found: {missing}"
