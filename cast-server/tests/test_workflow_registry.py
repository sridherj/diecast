"""Registry-shape tests for the Phase 3b workflow routing registry.

Pure data validity only — deliberately does NOT import `families.py`. The
registry↔`WorkFamily` key-set pin test lives in sp2's
`test_workflow_router_service.py`, the one place Phase 3b imports the enum.
"""

from cast_server.config import WORKFLOW_FAMILIES, WORKFLOW_REGISTRY


def test_every_entry_is_a_non_empty_stub():
    for fam, entry in WORKFLOW_REGISTRY.items():
        assert entry["status"] == "stub", f"{fam} must be a stub in v2 (FR-015)"
        assert entry["steps"], f"{fam} must have non-empty steps"
        assert all(isinstance(s, str) and s for s in entry["steps"])


def test_status_values_are_known():
    for entry in WORKFLOW_REGISTRY.values():
        assert entry["status"] in {"stub", "implemented"}


def test_families_is_derived_frozenset():
    assert WORKFLOW_FAMILIES == frozenset(WORKFLOW_REGISTRY)
    assert isinstance(WORKFLOW_FAMILIES, frozenset)


def test_bug_fix_steps_are_spec_mandated():
    assert WORKFLOW_REGISTRY["bug_fix"]["steps"] == ["logs", "RCA", "confirm", "fix/test"]


def test_registry_has_nine_families():
    assert len(WORKFLOW_REGISTRY) == 9
