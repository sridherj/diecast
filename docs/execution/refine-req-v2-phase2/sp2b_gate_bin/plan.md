# Sub-phase 2b: `bin/cast-classify-gate` (the "code decides" enforcement point)

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase2/_shared_context.md` before starting.
> Source: Work Package C of `docs/plan/2026-06-11-refine-requirements-v2-phase2-classification.md`.

## Objective

Create `bin/cast-classify-gate` — a thin, stdlib + `cast_server`-importing executable that takes the
classifier's raw JSON on stdin and emits the validated classification plus the gate decision on
stdout. This makes "gate in code, not the model" a deterministic, unit-testable artifact that agents
*invoke* — exactly like `bin/cast-spec-checker`. Without it, the gate degrades into a prompt
instruction (the model self-gating — the playbook's named pitfall #2).

## Dependencies
- **Requires completed:** sp1 (`families.py` — `validate_classification`, `gate`).
- **Assumed codebase state:** `families.py` exposes `validate_classification(raw) -> Classification`
  and `gate(confidence) -> GateAction`.
- **Parallel with:** sp2a, sp2c. **No shared files** — sp2b touches `bin/cast-classify-gate` and a
  new test file only; it does NOT run `bin/generate-skills`.

## Scope

**In scope:**
- `bin/cast-classify-gate` — stdin→stdout wrapper, `sys.path` bootstrap to import
  `cast_server.requirements_render.families`.
- Golden in/out test pairs, including off-schema fixtures and both threshold boundaries.

**Out of scope (do NOT do these):**
- Any classification/gate **logic** — it all lives in `families.py` (sp1). The bin is a thin wrapper;
  put no thresholds or coercions in the bin itself.
- The two-level checker (sp2c) — a *separate* bin with the opposite import policy.
- Wiring into `cast-refine-requirements` (sp3a).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `bin/cast-classify-gate` | Create (executable, `chmod +x`) | Does not exist |
| `cast-server/tests/test_classify_gate.py` | Create | Does not exist |

## Detailed Steps

### Step 2b.1: The bin
- **Stdin:** the classifier's raw JSON (`{family, confidence, reasoning, uncertainty_factors,
  alt_family, modifiers}`).
- **Stdout:** validated classification + gate decision JSON:
  ```json
  {"classification": { ...validated Classification fields incl. coercions... },
   "action": "auto" | "confirm" | "choose",
   "options": [ ... ]}
  ```
  For `choose`, `options` carries `[family, alt_family, "just notes / not sure yet" → random_idea]`
  with the model's pick pre-filled.
- **Exit codes:** `0` on any **parseable** input (off-schema input still yields a valid `random_idea`
  result via `validate_classification` — never crash); `2` on unreadable/un-parseable stdin.
- **Implementation:** `sys.path` bootstrap to import
  `cast_server.requirements_render.families`, then call `validate_classification` + `gate`. Header
  comment must state: **this bin imports `families.py` deliberately — it is part of the classify
  orchestration, NOT a portable linter** (contrast with `bin/cast-spec-checker`, sp2c, which
  deliberately does NOT import; see Decision D5).

### Step 2b.2: `sys.path` bootstrap pattern
Mirror how existing bins that import `cast_server` locate the package (find the repo root, insert
`cast-server/` on `sys.path`). Check an existing bin for the exact idiom before inventing one:
```bash
grep -rl 'sys.path' bin/ | head; grep -n 'cast_server' bin/* 2>/dev/null | head
```

## Verification

### Automated Tests (permanent) — `cast-server/tests/test_classify_gate.py`
- Golden in/out pairs:
  - High-confidence clean input (`confidence: 0.95`) → `action: "auto"`.
  - Mid (`0.7`) → `action: "confirm"`.
  - Low (`0.4`) → `action: "choose"` with the 3 options including the escape hatch.
  - **Off-schema fixtures:** garbage `family` → validated `random_idea`, exit 0, never crashes;
    missing `confidence` → coerced `0.0` → `action: "choose"`.
  - **Threshold boundaries:** `0.9 → auto`, `0.5 → confirm`, `0.49 → choose`.
  - Un-parseable stdin (not JSON) → exit 2, no classification emitted.

→ **Delegate:** `/cast-pytest-best-practices` over the test file. Review output for compliance.

### Validation Scripts (temporary)
```bash
echo '{"family":"bug_fix","confidence":0.95,"alt_family":"data_analysis","modifiers":{"irreversible":false,"unknown_cause":false}}' | bin/cast-classify-gate ; echo "exit=$?"
echo '{"family":"not_a_family","confidence":"oops"}' | bin/cast-classify-gate ; echo "exit=$?"   # expect random_idea, choose, exit 0
echo 'not json' | bin/cast-classify-gate ; echo "exit=$?"                                         # expect exit 2
uv run --project cast-server pytest cast-server/tests/test_classify_gate.py -v
```

### Manual Checks
- `bin/cast-classify-gate` is executable (`test -x bin/cast-classify-gate`).
- Header comment states the deliberate-import rationale (Decision D5 divergence from `cast-spec-checker`).
- No threshold numbers or coercion logic duplicated in the bin — all delegated to `families.py`.

### Success Criteria
- [ ] `bin/cast-classify-gate` exists, executable, thin wrapper over `families.py`.
- [ ] Off-schema input yields valid `random_idea` + exit 0; un-parseable stdin → exit 2.
- [ ] Gate boundaries (0.9/0.5/0.49) verified by golden tests.
- [ ] `choose` output carries the 3 options with the escape hatch.
- [ ] `pytest cast-server/tests/test_classify_gate.py` green.

## Execution Notes
- This bin and `bin/cast-spec-checker` (sp2c) have **opposite import policies on purpose**: the gate
  bin imports `families.py` (it's part of the orchestration); the checker mirrors a copy (it's a
  portable stdlib linter that must run where `cast-server` isn't importable). Both bins' headers must
  state their policy so a later maintainer doesn't "unify" them (Decision D5).
- Treat stdin as **data only** — JSON parse errors exit 2 without evaluating content (security note).

**Spec-linked files:** The gate contract is documented by sp3b's `cast-goal-classification.collab.md`.
No existing spec governs this bin.
