# Sub-phase 1: Layer A1 — Orchestrator output-path fix (FR-001)

> **Pre-requisite:** Read `docs/execution/cast-ui-harness-layered-fixes/_shared_context.md` before starting.

## Objective

Fix `_read_orchestrator_output()` in `cast-server/tests/ui/test_full_sweep.py` so it
reads the canonical path defined by `cast-output-json-contract.collab.md`:

```
<repo_root>/goals/<orchestrator_goal_slug>/.agent-run_<orchestrator_run_id>.output.json
```

Currently the helper checks `job["output_path"]` / `job["output_json_path"]` keys (which
the job record does not expose) and then falls back to scanning
`goals/<slug>/output.json`, which is a flat filename that no agent ever writes. As a
result the test reads garbage and reports the wrong status (often a stray child's
`completed` instead of the orchestrator's `partial`).

This sub-phase delivers FR-001 and SC-001 of the layered-fixes plan.

## Dependencies
- **Requires completed:** None. Runs in parallel with sp2 and sp3.
- **Assumed codebase state:** `test_full_sweep.py` exists (sp5 of the original
  cast-ui-test-harness execution plan landed it). The trigger response handling around
  line 150 already captures `run_id` from the trigger POST response.

## Scope

**In scope:**
- Rewrite `_read_orchestrator_output` to take the orchestrator's `run_id` and goal slug
  (or repo_root + slug + run_id) and read the canonical file path. No key probing on
  the job record. No scan fallback.
- Update `test_ui_e2e` to pass the captured `run_id` (and slug) into the helper.
- If the canonical file does not exist when the orchestrator has reached terminal
  status, raise a clear `pytest.fail(...)` with the path it tried — that's a
  contract bug worth surfacing, not a bug to paper over.

**Out of scope (do NOT do these):**
- Do NOT touch `conftest.py` (sp2's territory).
- Do NOT touch `runner.py` (sp3 / sp4's territory).
- Do NOT add scan-the-directory fallbacks. The plan-review explicitly resolved this:
  deterministic path only.
- Do NOT change the orchestrator agent's definition (that already writes to the
  canonical path; the bug is on the reader side).
- Do NOT change `_format_child_failures` — it correctly reads each child's
  `output_path` from the orchestrator's `children` map.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/ui/test_full_sweep.py` | Modify | Has `_read_orchestrator_output` at line 86, called at line 156. |

## Detailed Steps

### Step 1.1: Verify the canonical-path contract

Read `docs/specs/cast-output-json-contract.collab.md` (around line 35) and confirm
the file naming. The expected path is:

```python
goal_dir / f".agent-run_{run_id}.output.json"
```

where `goal_dir = repo_root / "goals" / orchestrator_goal_slug`.

The `seeded_test_goal` fixture (in `conftest.py:73`, do NOT modify) yields the
orchestrator's goal slug — same slug used by all children for this run.

### Step 1.2: Rewrite `_read_orchestrator_output`

Replace the existing helper (lines ~86–98) with a deterministic reader. Suggested
shape:

```python
def _read_orchestrator_output(repo_root: Path, goal_slug: str, run_id: str) -> dict:
    """Read the orchestrator's terminal output JSON from its canonical path
    (per docs/specs/cast-output-json-contract.collab.md).

    Fails loudly if the file is missing — that indicates a contract bug, not a
    path-resolution problem.
    """
    path = repo_root / "goals" / goal_slug / f".agent-run_{run_id}.output.json"
    if not path.exists():
        pytest.fail(
            f"Orchestrator output JSON missing at canonical path: {path}\n"
            "This usually means the orchestrator did not finish writing its "
            "output, or the cast-output-json-contract has drifted."
        )
    return json.loads(path.read_text())
```

### Step 1.3: Update `test_ui_e2e` call site

Around line 156, the current code calls `_read_orchestrator_output(job, repo_root)`.
Change it to pass the run_id and slug instead — both are already in scope:

- `run_id` is captured from the trigger response near line 150.
- `test_goal_slug` is the value of `seeded_test_goal` already bound to
  `test_goal_slug` near line 126.

```python
orch_output = _read_orchestrator_output(repo_root, test_goal_slug, run_id)
```

The `job` dict is no longer needed for path resolution. Keep `job` in scope only if
something else still reads from it (e.g., the failure message). Otherwise drop the
local binding to avoid a dead reference.

### Step 1.4: Sanity-check the rest of the file

- The `_format_child_failures(orch_output)` helper takes an already-parsed orch_output
  dict and reads each child's `output_path` field directly. That's correct and stays.
- No imports change. `json`, `Path`, `pytest` are already imported.

## Verification

1. **Static check:** `grep -n "output.json" cast-server/tests/ui/test_full_sweep.py`
   should show zero references to the flat `goals/<slug>/output.json` path.
2. **Static check:** `grep -n "output_path\|output_json_path" cast-server/tests/ui/test_full_sweep.py`
   should show no key-probing on the `job` record.
3. **Dynamic check:** With the test cast-server seeded so the orchestrator runs and
   reaches `partial`, run `pytest cast-server/tests/ui/test_full_sweep.py::test_ui_e2e`.
   The failure message MUST include `status='partial'` (the orchestrator's true status),
   not a stray child's `'completed'`.
4. **Dynamic check (negative path):** rename the canonical file before the test reads
   it (or simulate the path being missing). The test MUST fail with the explicit
   "Orchestrator output JSON missing at canonical path: …" message — not silently
   resolve to a different file.

## Acceptance Criteria

- `_read_orchestrator_output` takes `(repo_root, goal_slug, run_id)` (or equivalent
  explicit parameters), reads the canonical path, and fails loudly on missing file.
- No scan fallback. No `output_path` / `output_json_path` key probing on the job dict.
- `test_ui_e2e` passes `run_id` (already in scope from the trigger response) into the
  helper.
- Pytest's failure output for a deliberately-failing run reports the orchestrator's
  true terminal status (`partial`/`completed`/`failed`), not a child's status.

## Risk / Notes

- **The orchestrator's run_id source.** The current code captures it via
  `triggered = _http_post(...)` then reads `triggered["run_id"]` (or similar) around
  line 150. Read the actual lines before editing — name the right key.
- **Out-of-band:** the `job` dict (returned by `_poll_to_terminal`) may still be useful
  in the failure message for debugging the polling path. If you keep it, only use it
  for diagnostics, not for path resolution.
- **Do not "improve" the helper signature beyond what FR-001 needs.** Keep the change
  minimal — it's a 10-line rewrite, not a refactor.
