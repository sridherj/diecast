"""Golden in/out tests for the `bin/cast-classify-gate` executable.

The gate bin is the deterministic "code decides" enforcement point (FR-004): it
reads the classifier's raw JSON on stdin, validates it onto the family taxonomy,
applies the confidence gate, and emits the decision on stdout. These tests pin
that contract — gate boundaries, the off-schema RANDOM_IDEA floor, the `choose`
escape hatch, and the exit-code split between parseable and un-parseable stdin.

The bin is exercised as a subprocess (not imported) so the test covers the real
stdin → stdout → exit-code contract every caller depends on.
"""

import json
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_GATE_BIN = _REPO_ROOT / "bin" / "cast-classify-gate"


def run_gate(stdin: str) -> subprocess.CompletedProcess:
    """Invoke the gate bin with `stdin` and capture its result."""
    return subprocess.run(
        [str(_GATE_BIN)],
        input=stdin,
        capture_output=True,
        text=True,
    )


def run_gate_ok(stdin: str) -> dict:
    """Invoke the gate bin, assert a clean exit 0, and return parsed stdout JSON."""
    result = run_gate(stdin)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


class TestGateBoundaries:
    """The confidence → action mapping, pinned at the exact threshold boundaries."""

    @pytest.mark.parametrize(
        ("confidence", "expected_action"),
        [
            (0.95, "auto"),
            (0.9, "auto"),
            (0.7, "confirm"),
            (0.5, "confirm"),
            (0.49, "choose"),
            (0.4, "choose"),
        ],
    )
    def test_confidence_maps_to_action(self, confidence, expected_action):
        payload = json.dumps({"family": "bug_fix", "confidence": confidence})
        output = run_gate_ok(payload)
        assert output["action"] == expected_action


class TestGoldenPairs:
    """Representative in/out pairs across the three gate actions."""

    def test_high_confidence_auto_has_no_options(self):
        payload = json.dumps(
            {
                "family": "bug_fix",
                "confidence": 0.95,
                "alt_family": "data_analysis",
                "modifiers": {"irreversible": False, "unknown_cause": False},
            }
        )
        output = run_gate_ok(payload)
        assert output["action"] == "auto"
        assert output["classification"]["family"] == "bug_fix"
        assert output["classification"]["confidence"] == 0.95
        assert output["options"] == []

    def test_mid_confidence_confirm_pre_selects_pick(self):
        payload = json.dumps({"family": "pilot_poc", "confidence": 0.7})
        output = run_gate_ok(payload)
        assert output["action"] == "confirm"
        families = [opt["family"] for opt in output["options"]]
        assert families == ["pilot_poc"]
        assert output["options"][0]["selected"] is True

    def test_low_confidence_choose_offers_three_options_with_escape_hatch(self):
        payload = json.dumps(
            {
                "family": "bug_fix",
                "confidence": 0.4,
                "alt_family": "data_analysis",
            }
        )
        output = run_gate_ok(payload)
        assert output["action"] == "choose"

        options = output["options"]
        families = [opt["family"] for opt in options]
        # The model's pick (pre-filled), the alt_family, and the escape hatch.
        assert families == ["bug_fix", "data_analysis", "random_idea"]

        # The pick is pre-selected; nothing else is.
        assert options[0]["selected"] is True
        assert all(not opt["selected"] for opt in options[1:])

        # The escape hatch carries the human label and maps to the floor.
        escape = options[-1]
        assert escape["family"] == "random_idea"
        assert escape["label"] == "just notes / not sure yet"


class TestOffSchemaFloor:
    """Off-schema input never crashes — it coerces onto the RANDOM_IDEA floor."""

    def test_garbage_family_becomes_random_idea_exit_zero(self):
        result = run_gate('{"family":"not_a_family","confidence":0.95}')
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["classification"]["family"] == "random_idea"
        assert any("family" in c for c in output["classification"]["coercions"])

    def test_missing_confidence_coerces_to_zero_and_chooses(self):
        output = run_gate_ok('{"family":"bug_fix"}')
        assert output["classification"]["confidence"] == 0.0
        assert output["action"] == "choose"
        assert any("confidence" in c for c in output["classification"]["coercions"])

    def test_non_object_json_yields_floored_random_idea(self):
        # A bare JSON array is parseable but off-schema → floored, not a crash.
        output = run_gate_ok("[1, 2, 3]")
        assert output["classification"]["family"] == "random_idea"
        assert output["action"] == "choose"


class TestUnparseableStdin:
    """Un-parseable stdin is data only — exit 2, no classification emitted."""

    def test_non_json_exits_two_with_no_classification(self):
        result = run_gate("not json")
        assert result.returncode == 2
        assert result.stdout.strip() == ""

    def test_empty_stdin_exits_two(self):
        result = run_gate("")
        assert result.returncode == 2
        assert result.stdout.strip() == ""
