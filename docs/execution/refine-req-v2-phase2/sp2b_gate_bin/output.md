# sp2b_gate_bin — Output

**Status:** ✅ Complete. All success criteria met; 14/14 tests green.

## What was built

### `bin/cast-classify-gate` (created, executable)
Thin stdin→stdout wrapper that turns "gate in code, not the model" (FR-004) into a
deterministic, invokable artifact. It:
- Reads the classifier's raw JSON on stdin.
- Calls `validate_classification(raw)` + `gate(confidence)` from
  `cast_server.requirements_render.families` — **all** logic lives in `families.py`; the bin
  carries **no** thresholds or coercions.
- Emits `{"classification": {...validated, incl. coercions...}, "action": "...", "options": [...]}`
  on stdout.
- Uses the `sys.path`-bootstrap idiom from `bin/cast-doctor` (resolve repo root → insert
  `cast-server/` on path).

**Import policy (Decision D5):** the header comment states the bin imports `families.py`
**deliberately** because it is part of the classify orchestration — the **opposite** policy from
`bin/cast-spec-checker` (sp2c), which mirrors its own copy because it must run where `cast-server`
isn't importable. The headers warn maintainers not to "unify" the two bins.

### Contract details
| Input | Output |
|---|---|
| Parseable JSON (any shape) | exit `0`; off-schema fields coerced onto the `random_idea` floor with `coercions` recorded |
| Un-parseable / empty stdin | exit `2`; nothing on stdout (stdin treated as data only — never evaluated) |

**Gate → options:**
- `auto` (confidence ≥ 0.9) → `options: []`.
- `confirm` (≥ 0.5) → single pre-selected pick.
- `choose` (< 0.5) → 3 options: the model's pick (pre-filled `selected: true`), the
  `alt_family`, and the escape hatch `{"family":"random_idea","label":"just notes / not sure yet"}`.
  Deduped by family (e.g. an all-`random_idea` off-schema result collapses to one option).

Each option is `{"family": <value>, "label": <human label>, "selected": <bool>}`.

### `cast-server/tests/test_classify_gate.py` (created)
14 tests, invoking the bin as a real subprocess (covers the actual stdin→stdout→exit contract):
- **Gate boundaries** (parametrized): 0.95/0.9 → auto, 0.7/0.5 → confirm, 0.49/0.4 → choose.
- **Golden pairs**: high-conf auto (no options); mid-conf confirm (pre-selected pick); low-conf
  choose (3 options, escape hatch label + `random_idea` family, pick pre-selected).
- **Off-schema floor**: garbage family → `random_idea` exit 0; missing confidence → `0.0` → choose;
  bare JSON array → floored `random_idea`.
- **Un-parseable stdin**: `not json` and empty stdin → exit 2, empty stdout.

## Verification

- `bin/cast-classify-gate` is executable (`test -x` ✓).
- Validation scripts from the plan all produced expected output (auto/exit 0, off-schema
  random_idea/choose/exit 0, `not json`/exit 2).
- `uv run --project cast-server pytest cast-server/tests/test_classify_gate.py -v` → **14 passed**.
- `/cast-pytest-best-practices` applied: AAA structure, typed helpers, behavior-focused (tests the
  stdin→stdout→exit contract, not internals), no mocks/timestamps needed. JSON string literals
  intentionally pin the wire contract.

## Success criteria — all met
- [x] `bin/cast-classify-gate` exists, executable, thin wrapper over `families.py` (no logic dup).
- [x] Off-schema input → valid `random_idea` + exit 0; un-parseable stdin → exit 2.
- [x] Gate boundaries (0.9 / 0.5 / 0.49) verified by golden tests.
- [x] `choose` output carries 3 options with the escape hatch.
- [x] `pytest cast-server/tests/test_classify_gate.py` green.

## Notes for dependent sub-phases (sp3a)
- Invoke the gate by piping the classifier's raw JSON: `echo "$RAW_JSON" | bin/cast-classify-gate`.
- The `action` field drives the refine flow: `auto` → persist silently (`confirmed_by: auto`);
  `confirm`/`choose` → surface `options` to the user; off-schema/headless default lands on
  `random_idea` (`confirmed_by: fallback`).
- The validated `classification` dict (incl. `coercions`) is ready to feed `merge_front_matter()`
  after adding `confirmed_by` / `classified_at` / `taxonomy_version`.
