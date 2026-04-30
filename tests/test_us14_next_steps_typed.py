"""US14 — typed next_steps array contract tests (sp4d).

Covers:
    - JSON Schema acceptance/rejection of typed shape.
    - Legacy string-shape rejection (post-migration regression guard).
    - resolve_proactive() resolution order.

Self-loop and parent-child suggestion checks live as runtime assertions in
the agent prompts; they are exercised in integration via the cast-* fleet
end-to-end tests, not here.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "tests" / "fixtures" / "next_steps.schema.json"
MIGRATOR = REPO_ROOT / "bin" / "migrate-next-steps-shape.py"


@pytest.fixture()
def schema():
    return json.loads(SCHEMA_PATH.read_text())


def test_us14_clean_typed_passes(schema):
    valid = [
        {
            "command": "/cast-task-suggester",
            "rationale": "decompose plan",
            "artifact_anchor": "plan.md",
        },
        {
            "command": "/cast-runs --recent",
            "rationale": "inspect dispatched children",
            "artifact_anchor": None,
        },
    ]
    jsonschema.validate(valid, schema)  # raises on failure


def test_us14_too_many_entries_fails(schema):
    invalid = [
        {"command": f"/cast-{i}", "rationale": "x", "artifact_anchor": None}
        for i in range(5)
    ]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(invalid, schema)


def test_us14_missing_rationale_fails(schema):
    invalid = [{"command": "/cast-X", "artifact_anchor": None}]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(invalid, schema)


def test_us14_legacy_string_shape_fails(schema):
    invalid = ["/cast-task-suggester decompose this plan"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(invalid, schema)


def test_us14_proactive_resolution_overrides(tmp_path):
    """proactive_overrides[name] beats per-agent default."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text("proactive_overrides:\n  cast-refine-requirements: false\n")
    from agents._shared.proactive import resolve_proactive

    # per-agent default is True for cast-refine-requirements; override flips it
    assert (
        resolve_proactive(
            "cast-refine-requirements", per_agent_default=True, config_path=cfg
        )
        is False
    )


def test_us14_proactive_global_fallback(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("proactive_global: true\n")
    from agents._shared.proactive import resolve_proactive

    # per-agent default is None (unknown agent); falls through to proactive_global
    assert (
        resolve_proactive("cast-unknown", per_agent_default=None, config_path=cfg)
        is True
    )


def test_us14_proactive_final_fallback_false(tmp_path):
    """No overrides, no per-agent default, no global → False."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text("")
    from agents._shared.proactive import resolve_proactive

    assert (
        resolve_proactive("cast-unknown", per_agent_default=None, config_path=cfg)
        is False
    )


def test_us14_self_loop_caught_by_runtime_assertion(tmp_path, schema):
    """A cast-X agent's own command MUST NOT appear in its own next_steps.

    Simulated by validating an output JSON's next_steps against the schema and
    asserting no entry's command equals the producing agent name. This is the
    runtime assertion any cast-* agent should make at terminal close-out.
    """
    output = {
        "agent_name": "cast-refine-requirements",
        "next_steps": [
            {
                "command": "/cast-task-suggester",
                "rationale": "decompose refined requirements",
                "artifact_anchor": "refined_requirements.collab.md",
            }
        ],
    }
    # Schema gate
    jsonschema.validate(output["next_steps"], schema)
    # Self-loop gate
    self_cmd = "/" + output["agent_name"]
    for step in output["next_steps"]:
        assert self_cmd not in step["command"], f"self-loop: {step}"


def test_us14_parent_child_suggestion_included(schema):
    """When an agent dispatched a child, /cast-runs --recent appears in next_steps."""
    output = {
        "agent_name": "cast-detailed-plan",
        "dispatched_children": ["run_abc"],
        "next_steps": [
            {
                "command": "/cast-runs --recent",
                "rationale": "Inspect dispatched runs",
                "artifact_anchor": None,
            },
            {
                "command": "/cast-task-suggester",
                "rationale": "Decompose the plan into atomic tasks",
                "artifact_anchor": "plan.md",
            },
        ],
    }
    jsonschema.validate(output["next_steps"], schema)
    assert any(
        "/cast-runs" in step["command"] for step in output["next_steps"]
    ), "parent-child contract violated: missing /cast-runs suggestion"


def test_us14_migrator_converts_string_shape(tmp_path):
    """bin/migrate-next-steps-shape.py rewrites legacy strings to typed shape."""
    out = tmp_path / ".agent-run_test.output.json"
    out.write_text(
        json.dumps(
            {
                "agent_name": "cast-foo",
                "next_steps": ["/cast-bar do something"],
            }
        )
    )
    result = subprocess.run(
        [sys.executable, str(MIGRATOR), str(out)],
        check=True,
        capture_output=True,
        text=True,
    )
    counts = json.loads(result.stdout.strip())
    assert counts["migrated"] == 1
    after = json.loads(out.read_text())
    assert after["next_steps"] == [
        {"command": "/cast-bar do something", "rationale": "", "artifact_anchor": None}
    ]


def test_us14_migrator_idempotent(tmp_path):
    """Re-running migrator on already-typed entries is a no-op."""
    out = tmp_path / ".agent-run_test.output.json"
    typed = [
        {"command": "/cast-bar", "rationale": "x", "artifact_anchor": None}
    ]
    out.write_text(json.dumps({"next_steps": typed}))
    subprocess.run(
        [sys.executable, str(MIGRATOR), str(out)],
        check=True,
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        [sys.executable, str(MIGRATOR), str(out)],
        check=True,
        capture_output=True,
        text=True,
    )
    counts = json.loads(result.stdout.strip())
    assert counts["migrated"] == 0
    assert counts["skipped"] == 1
