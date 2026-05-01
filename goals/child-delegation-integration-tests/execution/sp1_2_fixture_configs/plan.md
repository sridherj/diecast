# sp1.2 — Author Four Fixture `config.yaml` Files + Deterministic Prompts

> **Pre-requisite:** Read `goals/child-delegation-integration-tests/execution/_shared_context.md` first.

## Objective

Create the four delegation-test fixture agents on disk so T1 (via direct config
injection) and T2 (via the running cast-server's registry) can both reach them by
name. Prompts are **literal-output** (not paraphrasable) so T2 substring assertions
are byte-stable.

## Dependencies

- **Requires completed:** None (parallel-safe with sp1.1, sp1.4).
- **Assumed codebase state:** existing `cast-server/tests/ui/agents/<name>/` layout
  shows the expected directory shape (agent dir contains `config.yaml` and any
  prompt-body file the loader expects).

## Scope

**In scope:**
- Create four `config.yaml` files under
  `cast-server/tests/integration/agents/<name>/` with the exact `dispatch_mode`,
  `allowed_delegations`, and `model: haiku` from the shared context.
- Author **literal** prompts that instruct each child to write a verbatim
  contract-v2 output JSON envelope.
- Mirror `cast-server/tests/ui/agents/<name>/` layout for any additional files the
  agent loader expects (e.g., system prompt body file).

**Out of scope (do NOT do these):**
- Wiring the conftest to register the directory — that's sp1.3.
- Writing any test against these fixtures — that's Phase 2.
- Trying to make the prompts "smart" or non-deterministic. They MUST be literal.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/tests/integration/agents/cast-test-parent-delegator/config.yaml` | Create | Does not exist |
| `cast-server/tests/integration/agents/cast-test-child-worker/config.yaml` | Create | Does not exist |
| `cast-server/tests/integration/agents/cast-test-child-worker-subagent/config.yaml` | Create | Does not exist |
| `cast-server/tests/integration/agents/cast-test-delegation-denied/config.yaml` | Create | Does not exist |
| Prompt-body file alongside each `config.yaml` (if loader expects it) | Create | Does not exist |

## Detailed Steps

### Step 1.2.1: Inspect the existing fixture layout

Read one of the existing UI fixtures, e.g.,
`cast-server/tests/ui/agents/cast-ui-test-noop/config.yaml`, to confirm the file
shape (key names, prompt-body location). Mirror this layout exactly for the
integration fixtures — same loader applies.

### Step 1.2.2: Author `cast-test-parent-delegator`

```yaml
# cast-server/tests/integration/agents/cast-test-parent-delegator/config.yaml
agent_id: cast-test-parent-delegator
dispatch_mode: http
allowed_delegations:
  - cast-test-child-worker
  - cast-test-child-worker-subagent
model: haiku
trust_level: readonly  # or whatever the schema requires; mirror UI fixtures
```

Prompt body: dispatch `cast-test-child-worker` via the literal curl command, poll
the child's output file, then write the parent's literal contract-v2 JSON envelope.
Use the form:

```
Run this exact curl (no substitutions, no paraphrase):
  curl -X POST http://localhost:8765/api/agents/cast-test-child-worker/trigger \
       -H 'Content-Type: application/json' \
       -d '<payload-with-goal_slug-and-delegation-context>'

Then poll <child_output_path> until terminal status. Then write to <output_path>
EXACTLY this JSON, do not paraphrase, do not add fields:
{ "status": "completed", "summary": "<sentinel-string>", "next_steps": [...], ... }
```

Replace `<...>` placeholders with the literal contract-v2 envelope shape from
`docs/specs/cast-output-json-contract.collab.md`. The `summary` field must be
literal so T2 substring assertions can pin it.

### Step 1.2.3: Author `cast-test-child-worker`

Same shape as parent but `allowed_delegations: []`. Prompt body: write the literal
contract-v2 JSON envelope to `<output_path>` and exit. The `summary` field is a
fixed sentinel (e.g., `"cast-test-child-worker completed successfully"`) the T2
assertions match exactly.

### Step 1.2.4: Author `cast-test-child-worker-subagent`

`dispatch_mode: subagent`, `allowed_delegations: []`. Prompt body: return a
structured literal verdict string. Used by sp6.1 builder unit-tests; live exercise
per sp6.2 manual checklist.

### Step 1.2.5: Author `cast-test-delegation-denied`

`dispatch_mode: http`, `allowed_delegations: [cast-test-child-worker]`. Prompt
body: attempt curl to `/api/agents/cast-test-child-worker-subagent/trigger`
(NOT in this agent's allowlist), capture the 422 body, then write a parent
contract-v2 JSON whose `summary` literally contains the substring `"denied (422)"`
so sp5.2's assertion is deterministic.

Add a header comment to this fixture's `config.yaml` and prompt body:

```yaml
# DELIBERATELY-FAILING FIXTURE — do not "fix" the bug.
# This agent's prompt tries to dispatch a non-allowlisted target so US3.S2
# can assert that allowlist denial flows through to a 422 with a deterministic
# summary string. See sp1.2 of the execution plan.
```

## Verification

### Automated Tests (permanent)

The verification test is created in sp1.3
(`cast-server/tests/integration/test_fixture_agents_load.py`).

### Validation Scripts (temporary)

```bash
python -c "
from pathlib import Path
import yaml
for p in Path('cast-server/tests/integration/agents').rglob('config.yaml'):
    print(p, yaml.safe_load(p.read_text())['dispatch_mode'])
"
```

Expected output: four lines, each printing the path and dispatch_mode matching
the table in shared context.

### Manual Checks

- For each `config.yaml`: visually confirm `dispatch_mode`, `allowed_delegations`,
  `model: haiku` match shared context exactly.
- Confirm the deliberately-failing fixture has the warning comment.

### Success Criteria

- [ ] Four directories exist under `cast-server/tests/integration/agents/`.
- [ ] Each contains a `config.yaml` with the locked-decision values.
- [ ] Each contains a prompt body (if loader expects one) with a LITERAL
      contract-v2 envelope instruction.
- [ ] `cast-test-delegation-denied` has the "do not fix the bug" comment.
- [ ] `python -c "..."` validation script prints all four with correct dispatch_modes.

## Execution Notes

- **Determinism is non-negotiable.** The prompts must say "Write EXACTLY this
  JSON, do not paraphrase, do not add fields". This is Review #5's discipline.
  Without it, T2's substring assertions become flaky against LLM variance.
- **Spec-linked files:** `cast-output-json-contract.collab.md` defines the v2
  envelope shape. Read it to populate the literal envelope correctly.
- The deliberately-failing fixture is test-data, not a bug. Future readers will
  try to "fix" it; the comment header is your defense.
