"""sp3a classify-integration prompt pins — regression tripwires.

Pins the "Step 0 — Classify" anchors that sp3a wired into the
`cast-refine-requirements` agent prompt + `config.yaml`, so a future editor — or
a `bin/generate-skills` regen pass — cannot silently drop the classify seam.

Each prompt anchor is asserted in BOTH places it must live:

  1. The source agent prompt
     `agents/cast-refine-requirements/cast-refine-requirements.md`.
  2. The regenerated user-facing skill
     `~/.claude/skills/cast-refine-requirements/SKILL.md` (regen-survival —
     the tripwire against generate-skills drift).

Mirrors the read-the-file / assert-substring pattern of
`tests/test_phase1b_prompt_pins.py`.

Anchors pinned (sp3a plan, Step 0):
  - `Step 0 — Classify` heading — the classify seam runs first.
  - `cast-goal-classifier` — the dispatched classifier subagent.
  - `cast-classify-gate` — the code-side gate bin.
  - `merge_front_matter` — the persist-once helper (Decision D3).
  - `FAMILY_RECIPES` — recipe-driven emission.
  - `--family` — the Level-2 checker flag the integration must pass.

Plus a length guard (the ~650-line prompt ceiling shared with Phase 1b) and a
`config.yaml` parse test pinning `allowed_delegations: [cast-goal-classifier]`.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

PROMPT_PATH = (
    REPO_ROOT / "agents" / "cast-refine-requirements" / "cast-refine-requirements.md"
)
SKILL_PATH = (
    Path.home() / ".claude" / "skills" / "cast-refine-requirements" / "SKILL.md"
)

# The ~650-line prompt ceiling (shared budget with Phase 1b / Phase 2 Step 0).
# A small slack over 650 is allowed so a one-line copy edit does not trip the
# guard, but a runaway Step 0 expansion does.
PROMPT_LINE_CEILING = 660

# Stable substrings — chosen to survive light copy edits.
STEP0_ANCHORS = [
    "Step 0 — Classify",
    "cast-goal-classifier",
    "cast-classify-gate",
    "merge_front_matter",
    "FAMILY_RECIPES",
    "--family",
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def prompt_text() -> str:
    return PROMPT_PATH.read_text()


@pytest.fixture(scope="module")
def skill_text() -> str:
    if not SKILL_PATH.exists():
        pytest.skip(
            f"regenerated skill not present at {SKILL_PATH}; "
            "run bin/generate-skills to enable the regen-survival pins"
        )
    return SKILL_PATH.read_text()


# ---------------------------------------------------------------------------
# Source-prompt pins
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("anchor", STEP0_ANCHORS)
def test_source_prompt_contains_step0_anchor(prompt_text: str, anchor: str) -> None:
    assert anchor in prompt_text, (
        f"sp3a Step 0 anchor {anchor!r} missing from the source agent prompt "
        f"({PROMPT_PATH.name}); the classify seam must restore it"
    )


def test_step0_runs_before_phase1(prompt_text: str) -> None:
    """Step 0 must be authored ahead of Phase 1 (classification shapes the draft)."""
    step0_idx = prompt_text.index("Step 0 — Classify")
    phase1_idx = prompt_text.index("Phase 1: Draft")
    assert step0_idx < phase1_idx, (
        "Step 0 — Classify must appear before Phase 1: Draft in the prompt; "
        "classification runs first and shapes the document recipe"
    )


def test_prompt_under_line_ceiling() -> None:
    line_count = len(PROMPT_PATH.read_text().splitlines())
    assert line_count <= PROMPT_LINE_CEILING, (
        f"{PROMPT_PATH.name} is {line_count} lines, over the ~650-line ceiling "
        f"(guard {PROMPT_LINE_CEILING}); Step 0 must stay terse — the gate logic "
        "lives in the bin, the family logic in families.py, classification in the subagent"
    )


# ---------------------------------------------------------------------------
# Regenerated-skill pins (regen-survival tripwire)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("anchor", STEP0_ANCHORS)
def test_regenerated_skill_contains_step0_anchor(skill_text: str, anchor: str) -> None:
    assert anchor in skill_text, (
        f"sp3a Step 0 anchor {anchor!r} did not survive bin/generate-skills into "
        f"{SKILL_PATH.name}; regen dropped it — re-run generate-skills and "
        "investigate the generator if it persists"
    )


# ---------------------------------------------------------------------------
# config.yaml allowed_delegations pin
# ---------------------------------------------------------------------------


def test_config_allows_classifier_delegation() -> None:
    sys.path.insert(0, str(REPO_ROOT / "cast-server"))
    from cast_server.models.agent_config import load_agent_config

    config = load_agent_config("cast-refine-requirements")
    assert "cast-goal-classifier" in config.allowed_delegations, (
        "config.yaml must list cast-goal-classifier in allowed_delegations "
        "(documents the Step 0 classify seam; makes a future HTTP switch config-only)"
    )
