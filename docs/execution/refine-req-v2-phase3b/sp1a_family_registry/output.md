# sp1a_family_registry — Output

**Status:** ✅ Completed — all Detailed Steps executed, all verification green, every success criterion met.

## What was done

Added the keystone `WORKFLOW_REGISTRY` (and the derived `WORKFLOW_FAMILIES`)
to `cast-server/cast_server/config.py`, directly beside `STARTER_TASKS`, and
created a registry-shape unit test. **The registry IS the router** — sp2
(`resolve`), sp3 (`/route`), and sp4b (spec) all settle against these exact
names and string values.

### Step 1a.1 — Registry in `config.py`
- Inserted `WORKFLOW_REGISTRY: dict[str, dict]` immediately after the
  `STARTER_TASKS` block (now at `config.py:103`), copied **verbatim** from the
  Naming Contract in `_shared_context.md`, including the comment block.
- `WORKFLOW_FAMILIES = frozenset(WORKFLOW_REGISTRY)` at `config.py:114` — the
  derived closed set that cannot drift from the map.
- All 9 families present as **string keys** (not `WorkFamily` enum members):
  `new_initiative, pilot_poc, bug_fix, data_analysis, random_idea, testing_qa,
  refactor_migration, personal_non_eng, generic`.
- Every value `status="stub"` (FR-015); `bug_fix` steps are the spec-mandated
  `["logs", "RCA", "confirm", "fix/test"]`; `generic` gets a named stub (announced
  decision, not a silent fallback).
- **Bottom-layer discipline preserved:** `config.py` imports nothing new — only
  `os`, `pathlib.Path`, `dotenv.load_dotenv` remain. No `requirements_render` /
  `families` import added (the lone "requirements_render" grep hit is the word
  inside the explanatory comment, not an import line). `/cast-python-best-practices`
  applied while writing.

### Step 1a.2 — Registry-shape unit test
- Created `cast-server/tests/test_workflow_registry.py` with 5 tests, pure data
  validity, **no `families.py` import** (the key-set pin test is sp2's job).
  `/cast-pytest-best-practices` applied.

## Verification results

| Check | Result |
|---|---|
| `pytest test_workflow_registry.py -v` | **5 passed** |
| `python -c "...registry OK"` (len==9, all stub+steps) | `registry OK` |
| No `requirements_render`/`families` **import** line | clean (only `os`, `pathlib`, `dotenv`) |
| `grep -c '"status": "stub"'` | `9` |
| `WORKFLOW_REGISTRY` beside `STARTER_TASKS` (same module) | ✅ line 103, after STARTER_TASKS at line 77 |

### Success Criteria — all met
- [x] `WORKFLOW_REGISTRY` (9 string keys matching `WorkFamily` values) + `WORKFLOW_FAMILIES` in `config.py`, beside `STARTER_TASKS`.
- [x] Every value `status="stub"` with non-empty `steps`; `bug_fix` steps are the spec-mandated four.
- [x] `config.py` imports nothing new.
- [x] `pytest cast-server/tests/test_workflow_registry.py` green.

## For dependent sub-phases (sp2, sp4b)
- Import names are final: `from cast_server.config import WORKFLOW_REGISTRY, WORKFLOW_FAMILIES`.
- `WORKFLOW_REGISTRY` keys ARE the contract — sp2's `resolve` indexes this dict by the
  persisted `goals.workflow_family` string; sp2's pin test must assert
  `set(WORKFLOW_REGISTRY) == {f.value for f in WorkFamily}`.
- Registry values are `{"status": "stub", "steps": [...]}`; `WORKFLOW_FAMILIES` is a `frozenset` of the keys.

## Files changed
- `cast-server/cast_server/config.py` (modified — added registry + frozenset, lines 99–114)
- `cast-server/tests/test_workflow_registry.py` (created — 5 tests)
