"""Pin tests for the `cast-goal-classifier` agent prompt (Phase 2, sp2a).

The classifier prompt embeds the nine `WorkFamily` values as the labels the model must emit.
These pins make enum drift between `families.py` and the prompt a CI failure: if a family is
renamed/added/removed in the enum without updating the prompt (or vice versa), one of these
tests goes red. Precedent: prompt-section pin tests elsewhere in the suite.

REPO_ROOT is ``parents[2]`` from ``cast-server/tests/`` — [0]=tests, [1]=cast-server, [2]=repo.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from cast_server.requirements_render.families import WorkFamily

REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = REPO_ROOT / "agents" / "cast-goal-classifier" / "cast-goal-classifier.md"
CONFIG_PATH = REPO_ROOT / "agents" / "cast-goal-classifier" / "config.yaml"


@pytest.fixture(scope="module")
def prompt_text() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def test_prompt_file_exists() -> None:
    assert PROMPT_PATH.is_file(), f"missing classifier prompt at {PROMPT_PATH}"


@pytest.mark.parametrize("family", list(WorkFamily), ids=lambda f: f.value)
def test_prompt_names_every_work_family_value(prompt_text: str, family: WorkFamily) -> None:
    """Every `WorkFamily.value` must appear verbatim in the prompt — no enum drift."""
    assert family.value in prompt_text, (
        f"WorkFamily.{family.name} value {family.value!r} is not present in the "
        f"classifier prompt; prompt and families.py have drifted apart."
    )


def test_prompt_sharpens_generic_vs_random_idea_boundary(prompt_text: str) -> None:
    """Decision D2: the two low-structure fallbacks must be explicitly distinguished, or the
    sp4 corpus eval shows them bleeding together."""
    lowered = prompt_text.lower()
    assert "generic" in lowered and "random_idea" in lowered
    # The boundary discussion names both within a short window (a dedicated section).
    assert "wrong bucket" in lowered, "generic ('has shape, wrong bucket') framing missing"
    assert "not enough signal" in lowered, "random_idea ('not enough signal yet') framing missing"


def test_prompt_declares_random_idea_as_default_floor(prompt_text: str) -> None:
    """`random_idea` is the documented default-and-floor (the load-bearing design insight)."""
    lowered = prompt_text.lower()
    assert "default" in lowered and "floor" in lowered
    assert "doubt" in lowered, "the 'when in doubt, random_idea' tie-breaker must be stated"


def test_prompt_specifies_bare_json_no_fences(prompt_text: str) -> None:
    """Output contract: a single bare JSON object, explicitly no prose and no code fences."""
    lowered = prompt_text.lower()
    assert "bare json" in lowered
    assert "no" in lowered and "fence" in lowered, "must forbid Markdown code fences"
    for key in ("family", "confidence", "reasoning", "uncertainty_factors", "alt_family", "modifiers"):
        assert key in prompt_text, f"output contract key {key!r} missing from prompt"


def test_config_is_subagent_dispatch_non_interactive() -> None:
    """config.yaml must declare subagent dispatch (owner Decision #2) and be non-interactive."""
    text = CONFIG_PATH.read_text(encoding="utf-8")
    assert "dispatch_mode: subagent" in text
    assert "interactive: false" in text
