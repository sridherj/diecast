"""Phase 1b refinement-brain prompt pins — regression tripwires.

Pins every Phase 1b anchor that sp1–sp3 wrote into the
`cast-refine-requirements` agent prompt (and the spec template) so a future
editor — or a `bin/generate-skills` regen pass — cannot silently drop them.

Each anchor is asserted in BOTH places it must live:

  1. The source agent prompt
     `agents/cast-refine-requirements/cast-refine-requirements.md`.
  2. The regenerated user-facing skill
     `~/.claude/skills/cast-refine-requirements/SKILL.md` (regen-survival —
     the tripwire against generate-skills drift).

Mirrors the read-the-file / assert-substring pattern of
`tests/test_b1_domain_search.py`.

Anchors pinned (plan sp4, Decision #5):
  - `## Decisions` section in the spec template.
  - `scope_mode` front-matter field in the agent prompt.
  - Scope-mode tokens: SCOPE REDUCTION / HOLD SCOPE / SCOPE EXPANSION.
  - HARD-GATE sentence (stable substring `in your first response`).
  - Reviewer rubric's five dimensions:
    Completeness / Consistency / Clarity / Scope / Feasibility.
  - Evidence-quoting mandate (stable substring `verbatim quote`).
  - Negative pin: the CUT adversarial meta-pass rubric must NOT reappear as an
    active anchor (Decision #3).
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

PROMPT_PATH = (
    REPO_ROOT
    / "agents"
    / "cast-refine-requirements"
    / "cast-refine-requirements.md"
)
TEMPLATE_PATH = REPO_ROOT / "templates" / "cast-spec.template.md"
SKILL_PATH = (
    Path.home()
    / ".claude"
    / "skills"
    / "cast-refine-requirements"
    / "SKILL.md"
)

# Anchors that must appear verbatim in both the source prompt and the
# regenerated skill. (Stable substrings — chosen to survive light copy edits.)
PROMPT_ANCHORS = [
    "scope_mode",
    "SCOPE REDUCTION",
    "HOLD SCOPE",
    "SCOPE EXPANSION",
    "in your first response",  # HARD-GATE sentence
    "Completeness",
    "Consistency",
    "Clarity",
    "Feasibility",
    "verbatim quote",  # evidence-quoting mandate
]

# The CUT import (Decision #3). Pinning its absence guards against a future
# editor re-adding the adversarial meta-pass as an active rubric. The
# evidence-quoting mandate + the fresh-context reviewer subsume it; the
# tombstone reference ("activity-5 meta-pass was cut") is intentionally a
# *different* phrase and is allowed to remain.
CUT_META_PASS_ANCHOR = "adversarial meta-pass"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def prompt_text() -> str:
    return PROMPT_PATH.read_text()


@pytest.fixture(scope="module")
def template_text() -> str:
    return TEMPLATE_PATH.read_text()


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


@pytest.mark.parametrize("anchor", PROMPT_ANCHORS)
def test_source_prompt_contains_anchor(prompt_text, anchor):
    assert anchor in prompt_text, (
        f"Phase 1b anchor {anchor!r} missing from the source agent prompt "
        f"({PROMPT_PATH.name}); the owning sub-phase (sp1–sp3) must restore it"
    )


def test_template_has_decisions_section(template_text):
    assert "## Decisions" in template_text, (
        "`## Decisions` section missing from cast-spec.template.md (sp2 anchor)"
    )


def test_source_prompt_negative_no_meta_pass(prompt_text):
    """Decision #3: the adversarial meta-pass was CUT — never re-add it."""
    assert CUT_META_PASS_ANCHOR not in prompt_text, (
        f"the CUT {CUT_META_PASS_ANCHOR!r} rubric reappeared in the prompt; "
        "Decision #3 cut it — the reviewer subagent is the sole adversarial pass"
    )


# ---------------------------------------------------------------------------
# Regenerated-skill pins (regen-survival tripwire)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("anchor", PROMPT_ANCHORS)
def test_regenerated_skill_contains_anchor(skill_text, anchor):
    assert anchor in skill_text, (
        f"Phase 1b anchor {anchor!r} did not survive bin/generate-skills into "
        f"{SKILL_PATH.name}; regen dropped it — re-run generate-skills and "
        "investigate the generator if it persists"
    )


def test_regenerated_skill_has_decisions_section(skill_text):
    assert "## Decisions" in skill_text, (
        "`## Decisions` section did not survive regen into the skill"
    )


def test_regenerated_skill_negative_no_meta_pass(skill_text):
    assert CUT_META_PASS_ANCHOR not in skill_text, (
        f"the CUT {CUT_META_PASS_ANCHOR!r} rubric appears in the regenerated "
        "skill; Decision #3 cut it"
    )
