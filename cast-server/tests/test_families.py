"""Unit tests for the Phase 2 classification keystone (`families.py`).

The bulk of sp1's correctness rides on these pins. They guard the cross-phase Naming Contract
(recipe invariants, gate boundaries), the defence-in-depth validation (`validate_classification`
never raises and always coerces to the floor), the deterministic front-matter merge (Decision
D3 — other keys + body survive byte-for-byte), the H2-level dedupe (Decision D4 — no family ×
modifier combination ever emits a duplicate H2), and the persist-once/consume-twice read path
(Decision D6 — the classification reads back through the parser without re-running the model).
"""
from __future__ import annotations

import itertools
from pathlib import Path

import pytest

from cast_server.requirements_render import parse_requirements_file
from cast_server.requirements_render.blocks import BlockKind
from cast_server.requirements_render.families import (
    FAMILY_PILL_LABELS,
    FAMILY_RECIPES,
    GATE_CONFIRM,
    GATE_SILENT,
    RECIPE_REALIZATION,
    REQUIRED_SECTIONS_BY_FAMILY,
    SECTION_TO_RECIPE_BLOCKS,
    Classification,
    Modifiers,
    RecipeBlock,
    WorkFamily,
    gate,
    merge_front_matter,
    modulate,
    validate_classification,
)

LEAD_BLOCKS = {RecipeBlock.PROBLEM, RecipeBlock.QUESTION}
MODIFIER_COMBOS = list(itertools.product([False, True], repeat=2))


# ---------------------------------------------------------------------------
# Taxonomy shape
# ---------------------------------------------------------------------------
def test_work_family_has_nine_values():
    assert len(WorkFamily) == 9


def test_recipe_block_has_six_values():
    assert len(RecipeBlock) == 6


def test_every_family_has_a_recipe_and_a_profile_and_a_pill():
    for family in WorkFamily:
        assert family in FAMILY_RECIPES
        assert family in REQUIRED_SECTIONS_BY_FAMILY
        assert family in FAMILY_PILL_LABELS


# ---------------------------------------------------------------------------
# Recipe invariants
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("family", list(WorkFamily))
def test_every_recipe_leads_with_problem_or_question(family: WorkFamily):
    assert FAMILY_RECIPES[family][0] in LEAD_BLOCKS


def test_random_idea_is_the_floor():
    assert FAMILY_RECIPES[WorkFamily.RANDOM_IDEA] == (RecipeBlock.PROBLEM,)


@pytest.mark.parametrize("family", list(WorkFamily))
def test_open_is_never_required(family: WorkFamily):
    assert "Open Questions" not in REQUIRED_SECTIONS_BY_FAMILY[family]


# ---------------------------------------------------------------------------
# Profile consistency (hand-derived, asserted against the recipes)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("family", list(WorkFamily))
def test_required_sections_trace_back_to_a_recipe_block(family: WorkFamily):
    recipe = set(FAMILY_RECIPES[family])
    for section in REQUIRED_SECTIONS_BY_FAMILY[family]:
        realizing_blocks = SECTION_TO_RECIPE_BLOCKS[section]
        assert recipe & realizing_blocks, (
            f"{family.value} requires {section!r} but no recipe block realizes it"
        )


def test_random_idea_requires_exactly_intent():
    assert REQUIRED_SECTIONS_BY_FAMILY[WorkFamily.RANDOM_IDEA] == ("Intent",)


# ---------------------------------------------------------------------------
# Gate boundaries
# ---------------------------------------------------------------------------
def test_gate_constants():
    assert GATE_SILENT == 0.9
    assert GATE_CONFIRM == 0.5


@pytest.mark.parametrize(
    ("confidence", "expected"),
    [
        (1.0, "auto"),
        (0.9, "auto"),
        (0.89, "confirm"),
        (0.5, "confirm"),
        (0.49, "choose"),
        (0.0, "choose"),
    ],
)
def test_gate_boundaries(confidence: float, expected: str):
    assert gate(confidence) == expected


# ---------------------------------------------------------------------------
# validate_classification — defence in depth
# ---------------------------------------------------------------------------
def test_valid_classification_passes_through():
    actual = validate_classification(
        {
            "family": "bug_fix",
            "confidence": 0.82,
            "alt_family": "data_analysis",
            "reasoning": "500 error with a repro; no new scope.",
            "uncertainty_factors": ["no stack trace"],
            "modifiers": {"irreversible": False, "unknown_cause": True},
        }
    )
    assert actual.family is WorkFamily.BUG_FIX
    assert actual.confidence == 0.82
    assert actual.alt_family is WorkFamily.DATA_ANALYSIS
    assert actual.uncertainty_factors == ("no stack trace",)
    assert actual.modifiers == Modifiers(irreversible=False, unknown_cause=True)
    assert actual.coercions == ()


def test_garbage_family_coerces_to_random_idea():
    actual = validate_classification({"family": "not_a_family", "confidence": 0.7})
    assert actual.family is WorkFamily.RANDOM_IDEA
    assert any("family" in c for c in actual.coercions)


def test_missing_confidence_coerces_to_zero_and_forces_choose():
    actual = validate_classification({"family": "bug_fix"})
    assert actual.confidence == 0.0
    assert gate(actual.confidence) == "choose"
    assert any("confidence" in c for c in actual.coercions)


@pytest.mark.parametrize("bad_confidence", ["high", None, True, 1.5, -0.2, [0.5]])
def test_invalid_confidence_coerces_to_zero(bad_confidence: object):
    actual = validate_classification({"family": "bug_fix", "confidence": bad_confidence})
    assert actual.confidence == 0.0


def test_invalid_alt_family_coerces_to_random_idea():
    actual = validate_classification(
        {"family": "bug_fix", "confidence": 0.8, "alt_family": "bogus"}
    )
    assert actual.alt_family is WorkFamily.RANDOM_IDEA
    assert any("alt_family" in c for c in actual.coercions)


def test_missing_modifiers_default_to_false():
    actual = validate_classification({"family": "bug_fix", "confidence": 0.8})
    assert actual.modifiers == Modifiers(irreversible=False, unknown_cause=False)


@pytest.mark.parametrize(
    "raw",
    [
        {},
        None,
        "not a dict",
        {"family": 42, "confidence": "garbage", "modifiers": "nope"},
        {"family": None, "alt_family": [], "uncertainty_factors": "oops"},
    ],
)
def test_validate_never_raises_on_adversarial_input(raw: object):
    actual = validate_classification(raw)
    assert isinstance(actual, Classification)
    # All safety coercions land on the floor (Decision D2) — GENERIC is never a coercion target.
    assert actual.family is WorkFamily.RANDOM_IDEA


def test_coercion_target_is_random_idea_not_generic():
    actual = validate_classification({"family": "generic-ish-typo", "confidence": 0.3})
    assert actual.family is WorkFamily.RANDOM_IDEA


# ---------------------------------------------------------------------------
# merge_front_matter (Decision D3) — round-trip preservation
# ---------------------------------------------------------------------------
EXISTING_DOC = """---
status: draft
confidence:
  intent: high
  scope: medium
---
# My Goal

> Spec maturity: draft

## Intent

Fix the flaky thing.
"""

CLASSIFICATION_FM = {
    "family": "bug_fix",
    "confidence": 0.82,
    "alt_family": "data_analysis",
    "reasoning": "Describes a 500 error: with a repro; no new scope.",
    "uncertainty_factors": ["no stack trace attached"],
    "modifiers": {"irreversible": False, "unknown_cause": True},
    "confirmed_by": "user",
    "classified_at": "2026-06-11T17:00:00Z",
    "taxonomy_version": 1,
}


def _body_after_front_matter(text: str) -> str:
    lines = text.split("\n")
    assert lines[0].strip() == "---"
    closing = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    return "\n".join(lines[closing + 1 :])


def test_merge_preserves_body_byte_for_byte():
    expected_body = _body_after_front_matter(EXISTING_DOC)
    merged = merge_front_matter(EXISTING_DOC, CLASSIFICATION_FM)
    assert _body_after_front_matter(merged) == expected_body


def test_merge_preserves_other_front_matter_keys():
    merged = merge_front_matter(EXISTING_DOC, CLASSIFICATION_FM)
    assert "status: draft" in merged
    assert "  intent: high" in merged
    assert "  scope: medium" in merged


def test_merge_is_idempotent_no_duplicate_block():
    once = merge_front_matter(EXISTING_DOC, CLASSIFICATION_FM)
    twice = merge_front_matter(once, CLASSIFICATION_FM)
    assert once == twice
    assert twice.count("classification:") == 1


def test_merge_round_trips_through_parser():
    merged = merge_front_matter(EXISTING_DOC, CLASSIFICATION_FM)
    parsed = _parse_text(merged)
    # Top-level confidence map survives and does NOT collide with classification.confidence.
    assert parsed.front_matter["status"] == "draft"
    assert parsed.front_matter["confidence"] == {"intent": "high", "scope": "medium"}
    assert parsed.front_matter["classification"]["family"] == "bug_fix"
    assert parsed.front_matter["classification"]["confidence"] == 0.82


def test_merge_creates_header_when_absent():
    body_only = "# Just a body\n\n## Intent\n\nnotes\n"
    merged = merge_front_matter(body_only, {"family": "random_idea"})
    assert merged.startswith("---\nclassification:\n")
    assert merged.endswith(body_only)


# ---------------------------------------------------------------------------
# modulate (Decision D4) — H2-level dedupe, no duplicate Intent
# ---------------------------------------------------------------------------
def _h2_targets(blocks: tuple[RecipeBlock, ...]) -> list[str]:
    return [RECIPE_REALIZATION[b].h2_primary for b in blocks]


@pytest.mark.parametrize("family", list(WorkFamily))
@pytest.mark.parametrize(("irreversible", "unknown_cause"), MODIFIER_COMBOS)
def test_modulate_never_produces_duplicate_h2(
    family: WorkFamily, irreversible: bool, unknown_cause: bool
):
    result = modulate(
        FAMILY_RECIPES[family], irreversible=irreversible, unknown_cause=unknown_cause
    )
    targets = _h2_targets(result)
    assert len(targets) == len(set(targets)), f"{family.value}: duplicate H2 in {targets}"


def test_unknown_cause_appends_open_not_a_second_intent():
    # bug_fix is PROBLEM-led; appending QUESTION would emit a second `## Intent`.
    result = modulate(FAMILY_RECIPES[WorkFamily.BUG_FIX], irreversible=False, unknown_cause=True)
    assert _h2_targets(result).count("Intent") == 1
    assert RecipeBlock.OPEN in result


def test_irreversible_ensures_scope():
    result = modulate(
        FAMILY_RECIPES[WorkFamily.PILOT_POC], irreversible=True, unknown_cause=False
    )
    assert "Out of Scope" in _h2_targets(result)


def test_irreversible_does_not_duplicate_existing_scope():
    # new_initiative already carries SCOPE — the modifier must not add a second one.
    result = modulate(
        FAMILY_RECIPES[WorkFamily.NEW_INITIATIVE], irreversible=True, unknown_cause=False
    )
    assert _h2_targets(result).count("Out of Scope") == 1


def test_modulate_no_op_returns_recipe_unchanged():
    recipe = FAMILY_RECIPES[WorkFamily.NEW_INITIATIVE]
    assert modulate(recipe, irreversible=False, unknown_cause=False) == recipe


# ---------------------------------------------------------------------------
# Realization layer wired to the real parser vocabulary
# ---------------------------------------------------------------------------
def test_realization_uses_real_block_kinds():
    for realization in RECIPE_REALIZATION.values():
        for kind in realization.block_kinds:
            assert isinstance(kind, BlockKind)


def test_problem_and_question_share_the_intent_h2():
    assert RECIPE_REALIZATION[RecipeBlock.PROBLEM].h2_primary == "Intent"
    assert RECIPE_REALIZATION[RecipeBlock.QUESTION].h2_primary == "Intent"


# ---------------------------------------------------------------------------
# No-reclassify read path (Decision D6) — persist once, consume twice
# ---------------------------------------------------------------------------
def test_classification_reads_back_through_parser_without_reclassifying(tmp_path: Path):
    doc = merge_front_matter(EXISTING_DOC, CLASSIFICATION_FM)
    path = tmp_path / "refined_requirements.collab.md"
    path.write_text(doc, encoding="utf-8")

    parsed = parse_requirements_file(path)

    # The family is read straight from front matter — no classifier was invoked.
    assert parsed.front_matter["classification"]["family"] == "bug_fix"
    assert parsed.front_matter["classification"]["confidence"] == 0.82


def _parse_text(text: str):
    from cast_server.requirements_render import parse_requirements

    return parse_requirements(text)
