"""Two-level (generic + family) checker tests for ``bin/cast-spec-checker`` (sub-phase 2c).

These guard the v2 family-aware additions WITHOUT regressing the no-family path:

  * A minimal VALID doc per ``WorkFamily`` passes ``--family <value>`` with zero errors.
  * The Template-Enforcer guard: a padded ``random_idea`` doc with an empty Success
    Criteria table FAILS under ``--family random_idea`` (permanent regression test).
  * A ``bug_fix`` doc with no ``## Evidence`` FAILS under ``--family bug_fix``.
  * A ``data_analysis`` doc with a ``## Directional`` section WARNs (does not error).
  * No-``--family`` is byte-for-byte today's behaviour on a real product spec.
  * Pin test (Decision D5): the checker's MIRRORED ``REQUIRED_SECTIONS_BY_FAMILY`` equals
    ``families.py``'s as a FULL mapping — any drift in section *content* fails CI.
  * The Phase-1 ``spec_grammar`` importlib bridge still imports cleanly (frozen grammar).

The checker is invoked as a subprocess (its real CLI surface) so the no-family byte-for-byte
guarantee is exercised end-to-end, exactly as CI / pre-commit run it.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import ModuleType

import pytest

from cast_server.requirements_render.families import (
    REQUIRED_SECTIONS_BY_FAMILY as FAMILIES_MAPPING,
    WorkFamily,
)

# cast-server/tests/<file> -> parents[0]=tests, [1]=cast-server, [2]=repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKER = REPO_ROOT / "bin" / "cast-spec-checker"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "family_docs"
# A real product spec with no classification front matter — the no-family path subject.
PRODUCT_SPEC = REPO_ROOT / "docs" / "specs" / "cast-hooks.collab.md"

# The valid doc for each family value (each must pass `--family <value>` cleanly).
VALID_FIXTURE_BY_FAMILY = {
    "new_initiative": "new_initiative_valid.md",
    "pilot_poc": "pilot_poc_valid.md",
    "bug_fix": "bug_fix_valid.md",
    "data_analysis": "data_analysis_valid.md",
    "random_idea": "random_idea_valid.md",
    "testing_qa": "testing_qa_valid.md",
    "refactor_migration": "refactor_migration_valid.md",
    "personal_non_eng": "personal_non_eng_valid.md",
    "generic": "generic_valid.md",
}


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CHECKER), *args],
        capture_output=True,
        text=True,
    )


def _load_checker_module() -> ModuleType:
    """Load ``bin/cast-spec-checker`` as a module (no ``.py`` suffix → explicit loader).

    Same importlib pattern as ``cast_server.requirements_render.spec_grammar``; used here
    only to read the checker's MIRRORED mapping for the pin test.
    """
    loader = SourceFileLoader("cast_spec_checker_under_test", str(CHECKER))
    spec = importlib.util.spec_from_file_location(
        "cast_spec_checker_under_test", CHECKER, loader=loader
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["cast_spec_checker_under_test"] = module
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------- #
# Setup sanity
# --------------------------------------------------------------------------- #
def test_checker_and_fixtures_exist():
    assert CHECKER.exists(), f"checker not found at {CHECKER}"
    assert FIXTURES.is_dir(), f"fixtures dir not found at {FIXTURES}"
    assert PRODUCT_SPEC.exists(), f"product spec not found at {PRODUCT_SPEC}"


def test_every_family_has_a_valid_fixture():
    """Guard against a new family landing without a fixture."""
    assert set(VALID_FIXTURE_BY_FAMILY) == {f.value for f in WorkFamily}


# --------------------------------------------------------------------------- #
# Fixture matrix — one valid doc per family passes its --family profile
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("family,fixture", sorted(VALID_FIXTURE_BY_FAMILY.items()))
def test_valid_fixture_passes_its_family(family: str, fixture: str):
    result = _run("--family", family, str(FIXTURES / fixture))
    assert result.returncode == 0, (
        f"{fixture} should pass `--family {family}` cleanly, got "
        f"exit {result.returncode}:\n{result.stdout}{result.stderr}"
    )
    assert "error" not in result.stdout


# --------------------------------------------------------------------------- #
# Level-2 family assertions
# --------------------------------------------------------------------------- #
def test_padded_random_idea_fails():
    """Template-Enforcer guard: an empty Success Criteria table errors (regression)."""
    result = _run("--family", "random_idea", str(FIXTURES / "random_idea_padded.md"))
    assert result.returncode == 1
    assert "F2" in result.stdout
    assert "Success Criteria" in result.stdout


def test_bug_fix_missing_evidence_fails():
    result = _run("--family", "bug_fix", str(FIXTURES / "bug_fix_no_evidence.md"))
    assert result.returncode == 1
    assert "Evidence" in result.stdout


def test_data_analysis_directional_warns_not_errors():
    result = _run(
        "--family", "data_analysis", str(FIXTURES / "data_analysis_directional.md")
    )
    assert result.returncode == 0, "a present Directional section must WARN, not error"
    assert "warning F3" in result.stdout


def test_unknown_family_is_invocation_error():
    result = _run("--family", "not_a_family", str(FIXTURES / "generic_valid.md"))
    assert result.returncode == 2
    assert "unknown --family" in result.stderr


# --------------------------------------------------------------------------- #
# No-family path is byte-for-byte unchanged
# --------------------------------------------------------------------------- #
def test_no_family_product_spec_passes_unchanged():
    """A product spec (no classification front matter) passes with no flag, same as before."""
    result = _run(str(PRODUCT_SPEC))
    assert result.returncode == 0, (
        f"product spec regressed on the no-family path:\n{result.stdout}{result.stderr}"
    )
    assert result.stdout.strip() == ""


def test_no_family_does_not_apply_family_sections():
    """A bare ## Intent doc must NOT be required to have Intent on the no-family path
    (the no-family profile is the legacy full-spec set, which does not list Intent)."""
    no_flag = _run(str(FIXTURES / "random_idea_valid.md"))
    # The legacy full-spec path requires User Stories/FR/SC/Open Questions, so this
    # minimal doc fails WITHOUT a family — proving the family path is what relaxes it.
    assert no_flag.returncode == 1
    with_family = _run("--family", "random_idea", str(FIXTURES / "random_idea_valid.md"))
    assert with_family.returncode == 0


# --------------------------------------------------------------------------- #
# Pin test (Decision D5) — mirror must equal families.py as a FULL mapping
# --------------------------------------------------------------------------- #
def test_mirror_matches_families():
    """The checker's mirrored REQUIRED_SECTIONS_BY_FAMILY equals families.py's exactly
    (every family's full section tuple), not merely the same keys."""
    checker = _load_checker_module()
    mirror = checker.REQUIRED_SECTIONS_BY_FAMILY
    canonical = {fam.value: sections for fam, sections in FAMILIES_MAPPING.items()}

    assert set(mirror) == set(canonical), "mirror family keys drifted from families.py"
    for family, sections in canonical.items():
        assert mirror[family] == sections, (
            f"mirror[{family!r}] = {mirror[family]!r} != families.py {sections!r} — "
            f"the checker's copy drifted; re-sync the literal dict in bin/cast-spec-checker"
        )
    # Full-mapping equality (catches an extra family in either direction too).
    assert mirror == canonical


# --------------------------------------------------------------------------- #
# Phase-1 grammar bridge stays green
# --------------------------------------------------------------------------- #
def test_spec_grammar_bridge_still_imports():
    from cast_server.requirements_render import spec_grammar

    for name in (
        "US_HEADING_RE",
        "FR_ID_RE",
        "SC_ID_RE",
        "EARS_SCENARIO_RE",
        "SECTION_HEADING_RE",
        "NEEDS_CLAR_INLINE_RE",
    ):
        assert getattr(spec_grammar, name) is not None, f"{name} missing from bridge"
    assert spec_grammar._section_spans is not None
    assert spec_grammar.US_HEADING_RE.match("### US1 — Foo")
