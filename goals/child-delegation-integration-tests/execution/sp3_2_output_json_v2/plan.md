# sp3.2 — `TestOutputJsonContractV2` + Schema Fixture

> **Pre-requisite:** Read `goals/child-delegation-integration-tests/execution/_shared_context.md` first.

## Objective

Cover output JSON contract v2 conformance: non-terminal status detection,
US14-typed `next_steps` shape, US13 untagged-Open-Questions detection. Author the
JSON Schema fixture for `next_steps` per US14.

## Dependencies

- **Requires completed:** Phase 2 (test module exists with Phase 2 classes).
- **Assumed codebase state:** `docs/specs/cast-output-json-contract.collab.md`
  defines US13 and US14 contracts.

## Scope

**In scope:**
- `cast-server/tests/fixtures/next_steps.schema.json` (new) — typed shape per US14.
- `TestOutputJsonContractV2` test class (3 methods).

**Out of scope (do NOT do these):**
- Promote the schema to `cast-server/cast_server/contracts/`. Test-only for now
  (resolved open question — non-blocking).
- Re-validate the entire envelope. Only the three v2-specific contracts.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/fixtures/next_steps.schema.json` | Create | Does not exist |
| `cast-server/tests/integration/test_child_delegation.py` | Append 1 class | Has prior classes |
| `cast-server/tests/fixtures/__init__.py` | Create if needed | -- |

## Detailed Steps

### Step 3.2.1: Read US14 contract

Open `docs/specs/cast-output-json-contract.collab.md` and locate US14. The typed
shape per `next_steps` entry is `{command, rationale, artifact_anchor}` (per spec).

### Step 3.2.2: Author `next_steps.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "next_steps array entry (output JSON contract v2, US14)",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["command", "rationale", "artifact_anchor"],
    "properties": {
      "command": {"type": "string"},
      "rationale": {"type": "string"},
      "artifact_anchor": {"type": "string"}
    },
    "additionalProperties": false
  }
}
```

Verify it's valid JSON: `python -c "import json; json.load(open('cast-server/tests/fixtures/next_steps.schema.json'))"`.

### Step 3.2.3: Implement `TestOutputJsonContractV2`

```python
import json
from pathlib import Path

import pytest

# jsonschema is a permitted import (NOT requests/httpx/urllib)
try:
    from jsonschema import validate, ValidationError
except ImportError:
    pytest.skip("jsonschema not installed", allow_module_level=False)

NEXT_STEPS_SCHEMA = json.loads(
    Path(__file__).parent.parent.joinpath("fixtures/next_steps.schema.json").read_text()
)


class TestOutputJsonContractV2:
    """Output JSON contract v2 conformance: terminal status, US14 next_steps,
    US13 open-question tags.
    """

    @pytest.mark.parametrize("status", ["pending", "running", "idle"])
    def test_non_terminal_status_treated_as_malformed(self, status, tmp_path):
        """US2.S4: non-terminal status in output.json → parent finalizes failed+parse-error."""
        # Synthesize a child output.json with non-terminal status
        # Drive _finalize_run_from_monitor
        # Assert: parent run status == "failed" AND errors[] contains parse-error
        ...

    def test_next_steps_bare_string_fails_schema(self):
        """US2.S5: next_steps entry as bare string fails US14 typed schema."""
        bad_payload = ["just a bare string, not the typed shape"]
        with pytest.raises(ValidationError):
            validate(instance=bad_payload, schema=NEXT_STEPS_SCHEMA)

    def test_untagged_open_questions_flagged(self, tmp_path):
        """US2.S6: trailing Open Questions section with untagged item → contract violation per US13.
        
        Tags expected: [EXTERNAL] or [USER-DEFERRED].
        """
        # Synthesize child output.json with an Open Questions section containing
        # an item with no tag.
        # Drive whatever the contract validator surface is (locate it; may not
        # exist yet — if so, document for sp4c).
        # Assert: validation surfaces the violation.
        ...
```

### Step 3.2.4: Document if Open-Questions tag-validator does not yet exist

If the production validator for US13 untagged Open Questions DOES NOT exist yet,
the test is in the "expected red until sp4c authors it" state. Document this in
the test's docstring AND in the Gate B failing-test list.

Do NOT add `xfail`. The test is red → green via sp4c, no xfail markers per US2.

### Step 3.2.5: Update equivalence-map docstring

Replace the diecast-only addition entry with the concrete class name and method
list.

## Verification

### Automated Tests (permanent)

```
pytest cast-server/tests/integration/test_child_delegation.py -k "OutputJsonContractV2"
```
Collects 3+ methods.

### Validation Scripts (temporary)

```bash
python -c "import json; json.load(open('cast-server/tests/fixtures/next_steps.schema.json'))"
# exit 0
```

### Manual Checks

- Schema file is valid JSON-Schema syntax.
- Test imports `jsonschema` (permitted), NOT `requests`/`httpx`/`urllib`.
- US13 untagged-tag test docstring documents the validator-may-not-exist case.

### Success Criteria

- [ ] Schema fixture exists and is valid JSON.
- [ ] `TestOutputJsonContractV2` has at least 3 methods (3 parametrized status
      values count as one method but multiple cases).
- [ ] FR-008 grep clean.
- [ ] Equivalence map updated.

## Execution Notes

- **Spec-linked files:** `cast-output-json-contract.collab.md` (US13, US14,
  Terminal Status). Read all three sections before writing assertions.
- If `jsonschema` is not in the project's dev deps, add it via the project's
  pyproject/requirements management. This is a permitted dependency (not an
  HTTP client).
- Per the resolved open question, the schema is test-only for now. If sp4c needs
  to consume it from non-test code, promote to `cast-server/cast_server/contracts/`
  later — not in this sub-phase.
