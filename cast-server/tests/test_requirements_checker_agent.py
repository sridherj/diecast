"""Pin tests for the `cast-requirements-checker` agent prompt + config (Phase 3a, sp5a).

The checker's prompt embeds two contracts the rest of the phase depends on:

1. the **rubric names** lifted verbatim from cast-preso (`one-clear-takeaway`, `l1-l2-hierarchy`)
   — so the fleet shares one vocabulary and a rename in one place is caught here; and
2. **every canonical verdict key** — so the agent prompt and sp5b's spec can never drift on the
   verdict schema the eval harness parses.

These are string pins (precedent: `test_goal_classifier_prompt.py`). They check the prompt/verdict
shape only — config conformance (dispatch_mode/context_mode/timeout) is the job of
`/cast-agent-compliance`, run after `bin/generate-skills`.

REPO_ROOT is ``parents[2]`` from ``cast-server/tests/`` — [0]=tests, [1]=cast-server, [2]=repo.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = REPO_ROOT / "agents" / "cast-requirements-checker"
PROMPT_PATH = AGENT_DIR / "cast-requirements-checker.md"
CONFIG_PATH = AGENT_DIR / "config.yaml"

# The cast-preso rubric criteria the checker reuses verbatim (shared-context Naming Contract).
RUBRIC_NAMES = ("one-clear-takeaway", "l1-l2-hierarchy")

# The canonical verdict schema keys (shared-context "Verdict schema (canonical)").
VERDICT_KEYS = (
    "can_state_what",
    "restated_job",
    "restated_outcome",
    "restated_scope",
    "missing",
    "score",
    "issues",
)


@pytest.fixture(scope="module")
def prompt_text() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def test_prompt_file_exists() -> None:
    assert PROMPT_PATH.is_file(), f"missing checker prompt at {PROMPT_PATH}"


@pytest.mark.parametrize("rubric", RUBRIC_NAMES)
def test_prompt_names_each_reused_rubric(prompt_text: str, rubric: str) -> None:
    """The reused cast-preso rubric IDs must appear verbatim — fleet-vocabulary drift guard."""
    assert rubric in prompt_text, (
        f"rubric id {rubric!r} is not present in the checker prompt; it has drifted from the "
        f"cast-preso content checker vocabulary."
    )


@pytest.mark.parametrize("key", VERDICT_KEYS)
def test_prompt_names_every_canonical_verdict_key(prompt_text: str, key: str) -> None:
    """Every canonical verdict key must be documented in the prompt — schema-drift guard with
    sp5b's spec and the eval harness parser."""
    assert key in prompt_text, (
        f"canonical verdict key {key!r} is missing from the checker prompt."
    )


def test_prompt_states_binary_pass_rule_not_score(prompt_text: str) -> None:
    """PASS is the boolean `can_state_what` + `missing[]`, NEVER the score float."""
    lowered = prompt_text.lower()
    assert "can_state_what == true" in lowered
    # The score is explicitly disclaimed as the gate.
    assert "never the gate" in lowered or "not the gate" in lowered


def test_prompt_mandates_bare_json_no_fences(prompt_text: str) -> None:
    """Output contract: a single bare JSON object, no prose, no Markdown code fences."""
    lowered = prompt_text.lower()
    assert "bare json" in lowered
    assert "fence" in lowered, "must forbid Markdown code fences"


def test_prompt_judges_only_zero_click_surface(prompt_text: str) -> None:
    """The checker must run the extractor and judge ONLY its output — never the source."""
    assert "cast-render-zero-click" in prompt_text
    lowered = prompt_text.lower()
    assert "unfamiliar reader" in lowered


def test_prompt_declares_outside_delegation_contract(prompt_text: str) -> None:
    """Subagent-mode carve-out: bare JSON as final text, writes no `.output.json`."""
    assert "cast-delegation-contract" in prompt_text
    assert ".output.json" in prompt_text


def test_config_is_subagent_lightweight_noninteractive() -> None:
    """config.yaml must match the Naming Contract shape for the checker."""
    text = CONFIG_PATH.read_text(encoding="utf-8")
    assert "model: sonnet" in text
    assert "dispatch_mode: subagent" in text
    assert "interactive: false" in text
    assert "context_mode: lightweight" in text
    assert "timeout_minutes: 10" in text
