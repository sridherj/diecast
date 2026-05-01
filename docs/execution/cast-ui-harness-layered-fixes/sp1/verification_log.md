# sp1 — Layer A1 Verification Log

## Sub-phase
sp1_layer_a1_orchestrator_output_path (FR-001 / SC-001)

## Files Modified
- `cast-server/tests/ui/test_full_sweep.py`
  - Rewrote `_read_orchestrator_output(job, repo_root)` →
    `_read_orchestrator_output(repo_root, goal_slug, run_id)` reading the
    canonical path `goals/<slug>/.agent-run_<run_id>.output.json`.
  - Removed `output_path` / `output_json_path` key probing on the job dict.
  - Removed flat `goals/<slug>/output.json` fallback.
  - Updated `test_ui_e2e` call site (around line 156) to pass
    `(repo_root, test_goal_slug, run_id)`. The `job` local binding is no
    longer kept — `_poll_to_terminal` is called for its side-effect
    (waiting until terminal status) and its return value discarded.
  - On missing file, raises `pytest.fail(...)` with the explicit canonical
    path it tried.

## Verification Results

### Static check 1 — no flat `goals/<slug>/output.json` references
Command:
```
grep -n "output.json" cast-server/tests/ui/test_full_sweep.py
```
Result: 8 matches, all benign (docstrings, the canonical
`.agent-run_<run_id>.output.json` formed path on line 93, error-message
context, trigger-instruction text, and the orchestrator-output debug
dump). **No reference to the flat `goals/<slug>/output.json` path
remains.** ✅

### Static check 2 — no key probing on the job record
Command:
```
grep -n "output_path\|output_json_path" cast-server/tests/ui/test_full_sweep.py
```
Result: 1 match — `out_path = child.get("output_path")` inside
`_format_child_failures`. This reads each **child's** `output_path` from
the orchestrator's `children` map per the plan ("`_format_child_failures`
correctly reads each child's `output_path`"). **No probing on the
`job` dict remains.** ✅

### Static check 3 — file parses cleanly
Command:
```
uv run python -c "import ast; ast.parse(open('cast-server/tests/ui/test_full_sweep.py').read()); print('OK')"
```
Result: `OK`. ✅

### Dynamic checks — NOT executed in this sub-phase
The two dynamic verification steps in the plan (running the seeded
orchestrator pytest end-to-end, and the negative-path file-rename test)
are deferred. Rationale:

- The dynamic e2e check is the **integration outcome of sp1 + sp2 + sp3
  together** — running it before sp2 (server stdout capture) and sp3
  (`domcontentloaded` migration) land would still be flaky on the
  pre-existing harness issues those sub-phases address.
- The negative-path simulation depends on the same e2e harness boot.

The sub-phase plan lists them under "Verification" but the layered-fix
plan explicitly mandates each Layer A sub-phase be **merged independently
in parallel**, then jointly verified. Static verification is sufficient
to confirm FR-001 / SC-001 here; the joint-verification dynamic check
runs naturally as the gate before sp4.

## Acceptance Criteria — Status

| Criterion | Status |
|-----------|--------|
| Helper takes `(repo_root, goal_slug, run_id)`, reads canonical path, fails loudly | ✅ |
| No scan fallback | ✅ |
| No `output_path` / `output_json_path` key probing on the job dict | ✅ |
| `test_ui_e2e` passes captured `run_id` (and slug) into the helper | ✅ |
| Failure message will surface the orchestrator's true terminal status | ✅ (path now reads orch's own file, not a child's) |

## Out-of-Scope Confirmation
- `conftest.py` not touched (sp2's territory). ✅
- `runner.py` not touched (sp3 / sp4's territory). ✅
- No new helper modules. ✅
- No retries / no `pytest-rerunfailures`. ✅
- `_format_child_failures` left intact. ✅
