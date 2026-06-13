# Sub-phase 1a: Family registry in `config.py` — the keystone

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase3b/_shared_context.md` before starting.
> Source: Work Package A of `docs/plan/2026-06-11-refine-requirements-v2-phase3b-workflow-router.md`.

## Objective

Add `WORKFLOW_REGISTRY` (and the derived `WORKFLOW_FAMILIES`) to
`cast-server/cast_server/config.py`, directly beside `STARTER_TASKS`. **The registry IS the router** —
every other Phase 3b sub-phase reads it. It is the family-keyed generalization of the phase-keyed
`STARTER_TASKS` table already in that file. Build it first; the resolver (sp2), the route (sp3), and
the spec (sp4b) all settle against these exact names and string values. Keep `config.py` the
dependency-free bottom layer: the keys are **string values**, not `WorkFamily` enum members, so config
imports nothing new (the enum coupling lives in exactly one pin test, co-located in sp2).

## Dependencies
- **Requires completed:** None within Phase 3b. **Phase 2 must be landed** (see `_shared_context.md` →
  "Hard Prerequisite") — only so the registry's keys can be pin-checked against `WorkFamily` (the pin
  test lives in sp2, not here; sp1a itself imports nothing from `families.py`).
- **Assumed codebase state:** `cast-server/cast_server/config.py` exists with `STARTER_TASKS` at
  line ~77. `cast-server/cast_server/requirements_render/families.py` exists with `WorkFamily` (9
  values: `new_initiative, pilot_poc, bug_fix, data_analysis, random_idea, testing_qa,
  refactor_migration, personal_non_eng, generic`).

## Scope

**In scope:**
- Add `WORKFLOW_REGISTRY: dict[str, dict]` and `WORKFLOW_FAMILIES = frozenset(WORKFLOW_REGISTRY)` to
  `config.py`, with the comment block from the Naming Contract.
- A small registry-shape unit test (status/`steps` validity) that is independently verifiable with no
  service/route/migration code present.

**Out of scope (do NOT do these):**
- The resolver service, `WorkflowHandle`, `resolve`, `record_routing_decision` (sp2). The registry is
  *data*; the consuming logic is sp2.
- The registry↔`WorkFamily` **key-set pin test** — it is **co-located in sp2's** test module
  (`test_workflow_router_service.py`), the one place Phase 3b imports `families.py` (tests only). Do
  NOT add a `families.py` import to `config.py` or to sp1a's test.
- Any DB work, route, agent, or spec.
- Flipping any family to `status="implemented"` or populating `pipeline_ref` — every value is `"stub"`
  in v2 (FR-015).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/config.py` | Modify | Exists; `STARTER_TASKS` at line ~77; no `WORKFLOW_REGISTRY` |
| `cast-server/tests/test_workflow_registry.py` | Create | Does not exist |

## Detailed Steps

### Step 1a.1: Add the registry beside `STARTER_TASKS`

In `cast-server/cast_server/config.py`, directly after the `STARTER_TASKS` block, add **verbatim**
(copy from `_shared_context.md` → Data Schemas & Contracts):

```python
# Workflow routing registry (Phase 3b). Keys are WorkFamily string values —
# one vocabulary, two homes; kept as strings so config.py stays the
# dependency-free bottom layer (no requirements_render import). A pin test
# asserts key-set equality with families.WorkFamily.
WORKFLOW_REGISTRY: dict[str, dict] = {
    "new_initiative":     {"status": "stub", "steps": ["PRD", "architecture", "phased plan", "execute"]},
    "pilot_poc":          {"status": "stub", "steps": ["one-screen WHAT", "spike", "demo", "learnings"]},
    "bug_fix":            {"status": "stub", "steps": ["logs", "RCA", "confirm", "fix/test"]},
    "data_analysis":      {"status": "stub", "steps": ["question", "sources", "analysis", "writeup"]},
    "random_idea":        {"status": "stub", "steps": ["capture", "incubate", "promote-or-archive"]},
    "testing_qa":         {"status": "stub", "steps": ["inventory", "coverage gaps", "test plan", "implement"]},
    "refactor_migration": {"status": "stub", "steps": ["map current", "target design", "migration steps", "verify parity"]},
    "personal_non_eng":   {"status": "stub", "steps": ["clarify outcome", "plan", "do", "reflect"]},
    "generic":            {"status": "stub", "steps": ["refine", "explore", "plan", "execute"]},
}
WORKFLOW_FAMILIES = frozenset(WORKFLOW_REGISTRY)   # the closed set, derived — cannot drift from the map
```

- `bug_fix`'s steps are **spec-mandated** (`logs→RCA→confirm→fix/test`) — do not alter. All other step
  wordings are the recorded default (owner-editable copy; see `_shared_context.md` → autonomous-run
  defaults). Editing them later changes data, not the plan.
- `generic` gets a *named* stub like every other family (it is model-selected, never a coercion
  target) — this is an announced decision, not the forbidden silent fallback.
- → **Delegate:** apply `/cast-python-best-practices` while writing; review output for compliance
  (constant naming, type annotation, no new imports at the config bottom layer).

### Step 1a.2: Registry-shape unit test

Create `cast-server/tests/test_workflow_registry.py` — pure data validity, **no `families.py`
import** (that pin is sp2's job):

```python
from cast_server.config import WORKFLOW_REGISTRY, WORKFLOW_FAMILIES

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
```

→ **Delegate:** apply `/cast-pytest-best-practices`; review output.

## Verification

### Automated Tests (permanent) — `cast-server/tests/test_workflow_registry.py`
- Every entry `status="stub"` + non-empty `steps` (all strings).
- `WORKFLOW_FAMILIES == frozenset(WORKFLOW_REGISTRY)`, is a `frozenset`.
- `bug_fix` steps exactly `["logs", "RCA", "confirm", "fix/test"]`.
- Exactly 9 families.

### Validation Scripts (temporary)
```bash
uv run --project cast-server pytest cast-server/tests/test_workflow_registry.py -v
python -c "from cast_server.config import WORKFLOW_REGISTRY, WORKFLOW_FAMILIES; assert len(WORKFLOW_REGISTRY)==9; assert all(e['status']=='stub' and e['steps'] for e in WORKFLOW_REGISTRY.values()); print('registry OK')"
# Confirm config.py did NOT acquire a requirements_render import (bottom-layer discipline):
! grep -q "requirements_render" cast-server/cast_server/config.py && echo "config.py is import-clean"
```

### Manual Checks
- `grep -c '"status": "stub"' cast-server/cast_server/config.py` → 9.
- Confirm `WORKFLOW_REGISTRY` sits beside `STARTER_TASKS`, not in a new module.

### Success Criteria
- [ ] `WORKFLOW_REGISTRY` (9 string keys matching the `WorkFamily` values) + `WORKFLOW_FAMILIES`
      present in `config.py`, beside `STARTER_TASKS`.
- [ ] Every value `status="stub"` with non-empty `steps`; `bug_fix` steps are the spec-mandated four.
- [ ] `config.py` imports nothing new (no `requirements_render`/`families` import).
- [ ] `pytest cast-server/tests/test_workflow_registry.py` green.

## Execution Notes
- **The string keys ARE the contract.** sp2's `resolve` indexes this dict by the persisted
  `goals.workflow_family` string; sp2's pin test asserts `set(WORKFLOW_REGISTRY) == {f.value for f in WorkFamily}`.
  If you mistype a key here, that pin test (in sp2) is what catches it — but get it right the first time.
- Do not be tempted to derive the registry from `WorkFamily` to "avoid duplication" — the string-keyed
  map is a deliberate decision to keep `config.py` the import-free bottom layer (Design Review flag);
  the single pin test is the chosen anti-drift mechanism (Phase 2 Decision #5 mirror discipline).

**Spec-linked files:** No spec covers `config.py`'s registry yet — sp4b authors
`cast-workflow-routing.collab.md` documenting `WORKFLOW_REGISTRY` semantics. No SAV behaviors to
preserve in this sub-phase.
