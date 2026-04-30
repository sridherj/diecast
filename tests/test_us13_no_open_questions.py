"""US13 close-out discipline — regression tests for the no-open-questions rule.

The rule is encoded in
`skills/claude-code/cast-interactive-questions/SKILL.md`
(§ "Close-out Discipline (US13)") and the schema impact is documented in
`docs/specs/cast-delegation-contract.collab.md`
(§ "Per-Agent Output Extensions" -> "Open-Question Tags (US13)").

These tests exercise the deterministic mirror in
`tests/helpers/refine_close_out_harness.py` -- the prompt-side wording is
LLM-driven, but the close-out discipline is a structural rule we can check
without a model in the loop.

Tests cover four behaviors:

  1. End-of-interactive-flow ambiguities are resolved interactively (folded
     into the body) OR tagged in the trailing Open Questions section.
  2. A user deferral surfaces as `[USER-DEFERRED]` with a Reason line.
  3. An untagged Open Questions line is flagged as a violation.
  4. `[EXTERNAL]` presence forces `human_action_needed: true` and lifts the
     items into `human_action_items[]`.

Plus a prompt-artifact regression guard: the discipline section MUST stay
documented in the skill file so the LLM-driven side does not drift.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tests.helpers.refine_close_out_harness import (  # noqa: E402
    StubUserAnswers,
    find_untagged_open_question_lines,
    run_refine_with_buggy_close_out_fixture,
    run_refine_with_close_out_fixture,
    run_refine_with_external_only_fixture,
)

FIXTURE_SOURCE = (
    REPO_ROOT / "tests" / "fixtures" / "refine_with_open_ambiguities"
)
SKILL_PATH = (
    REPO_ROOT
    / "skills"
    / "claude-code"
    / "cast-interactive-questions"
    / "SKILL.md"
)
SPEC_PATH = REPO_ROOT / "docs" / "specs" / "cast-delegation-contract.collab.md"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def stub_user_answers() -> StubUserAnswers:
    return StubUserAnswers()


@pytest.fixture
def isolated_fixture_dir(tmp_path: Path) -> Path:
    """Copy the static fixture into tmp_path so each test gets a clean
    artifact write target without disturbing the source tree.
    """
    target = tmp_path / "refine_with_open_ambiguities"
    shutil.copytree(FIXTURE_SOURCE, target)
    return target


# ---------------------------------------------------------------------------
# Behavior tests
# ---------------------------------------------------------------------------


def test_us13_close_out_resolves_ambiguities(
    stub_user_answers: StubUserAnswers, isolated_fixture_dir: Path
) -> None:
    """Two ambiguities at end of refine -> one resolved interactively, the
    other tagged [EXTERNAL] with a Reason. Resolved item leaves Open
    Questions; tagged item appears with the documented format.
    """
    stub_user_answers.queue(
        [
            ("ambiguity 1", "A"),  # resolved interactively
            ("ambiguity 2", "[EXTERNAL] vendor not yet committed"),
        ]
    )
    trace = run_refine_with_close_out_fixture(
        isolated_fixture_dir, stub_user_answers
    )
    artifact_text = trace.artifact_path.read_text()

    open_q_section = (
        artifact_text.split("Open Questions", 1)[1]
        if "Open Questions" in artifact_text
        else ""
    )

    # ambiguity 1 was resolved interactively -> not in Open Questions
    assert "ambiguity_1" not in open_q_section
    assert "ambiguity_1" in artifact_text  # but is in the body

    # ambiguity 2 is in Open Questions, properly tagged with a Reason
    assert "[EXTERNAL]" in open_q_section
    assert "vendor" in open_q_section
    assert "Reason:" in open_q_section


def test_us13_user_deferred_tag(
    stub_user_answers: StubUserAnswers, isolated_fixture_dir: Path
) -> None:
    """User explicitly defers an ambiguity -> [USER-DEFERRED] tag appears
    in the artifact with the Reason line populated.
    """
    stub_user_answers.queue(
        [
            (
                "ambiguity 1",
                "[USER-DEFERRED] skip -- we'll come back to this",
            ),
            ("ambiguity 2", "B"),  # resolved interactively, irrelevant here
        ]
    )
    trace = run_refine_with_close_out_fixture(
        isolated_fixture_dir, stub_user_answers
    )
    artifact_text = trace.artifact_path.read_text()

    assert "[USER-DEFERRED]" in artifact_text
    assert "Reason:" in artifact_text

    # USER-DEFERRED items must NOT appear in human_action_items[]
    assert trace.terminal_output["human_action_items"] == []


def test_us13_untagged_open_question_is_a_violation(
    isolated_fixture_dir: Path,
) -> None:
    """If the agent leaves an item in Open Questions without a tag, the
    validator helper flags it. This is the contract-v2 consumer's gate.
    """
    trace = run_refine_with_buggy_close_out_fixture(isolated_fixture_dir)
    violations = find_untagged_open_question_lines(trace.terminal_output)
    assert violations, "expected at least one untagged Open Questions line"
    # Every flagged line must reference one of the planted ambiguities,
    # ensuring we are catching the right thing rather than spurious lines.
    assert all("ambiguity_" in line for line in violations)


def test_us13_human_action_needed_when_external_present(
    isolated_fixture_dir: Path,
) -> None:
    """When [EXTERNAL] items exist, output JSON sets human_action_needed
    and lifts each item verbatim into human_action_items[]. [USER-DEFERRED]
    items are NOT lifted (covered above).
    """
    trace = run_refine_with_external_only_fixture(isolated_fixture_dir)
    output_json = trace.terminal_output
    assert output_json["human_action_needed"] is True
    assert len(output_json["human_action_items"]) > 0
    assert all(
        "[EXTERNAL]" in item for item in output_json["human_action_items"]
    )


# ---------------------------------------------------------------------------
# Prompt-artifact regression guards
# ---------------------------------------------------------------------------


def test_skill_file_documents_close_out_discipline() -> None:
    """The SKILL.md file MUST keep the Close-out Discipline section so the
    LLM-driven side does not silently drift from the harness's mirror.
    """
    text = SKILL_PATH.read_text()
    assert "Close-out Discipline" in text
    assert "[EXTERNAL]" in text
    assert "[USER-DEFERRED]" in text
    assert "Reason:" in text


def test_spec_documents_open_question_tags() -> None:
    """The cast-delegation-contract spec MUST keep the Open-Question Tags
    subsection so consumers (cast-server, downstream agents) can rely on
    the schema.
    """
    text = SPEC_PATH.read_text()
    assert "Open-Question Tags" in text
    assert "[EXTERNAL]" in text
    assert "[USER-DEFERRED]" in text
    assert "human_action_items" in text
