# Sub-phase 4b: 7 per-screen test agents

> **Pre-requisite:** Read `docs/execution/cast-ui-test-harness/_shared_context.md` AND
> `skills/claude-code/cast-child-delegation/SKILL.md` before starting.

## Objective

Author the 7 per-screen test agents. Each delegates to runner.py via a single direct
script-path invocation, captures runner.py's `output.json`, and writes its own `output.json`
with the per-child schema from shared context. All 7 follow the canonical
`cast-child-delegation` skill verbatim.

The agents are tiny: each one is essentially a configuration shim around `runner.py
--screen=<name>`. The complexity lives in runner.py (sp3) — these agents are the dispatch
glue.

## Dependencies
- **Requires completed:** sp3 (`runner.py` CLI contract). The agents shell out to runner.py
  using the contract documented in shared context.
- **Assumed codebase state:** `cast-server/tests/ui/agents/` exists. sp4a may have landed
  in parallel — the 7 directories here are disjoint from sp4a's two.

## Scope

**In scope:** for each of the 7 screens, create:
- `cast-ui-test-<screen>/cast-ui-test-<screen>.md` (instructions)
- `cast-ui-test-<screen>/config.yaml`

Screens: `dashboard`, `agents`, `runs`, `scratchpad`, `goal-detail`, `focus`, `about`.
(Note: `goal-detail` keeps the dash in the agent name; runner.py normalizes via `--screen`.)

**Out of scope (do NOT do these):**
- Do NOT author the orchestrator or noop agents (sp4a owns those).
- Do NOT modify `runner.py`.
- Do NOT inline curl-based delegation; the canonical skill is referenced (Decision #3).
- Do NOT add per-screen Python code to the runner — assertions belong in sp3's runner.py.

## Files to Create/Modify

| Directory | Files | Action |
|-----------|-------|--------|
| `cast-server/tests/ui/agents/cast-ui-test-dashboard/` | `cast-ui-test-dashboard.md`, `config.yaml` | Create |
| `cast-server/tests/ui/agents/cast-ui-test-agents/` | `cast-ui-test-agents.md`, `config.yaml` | Create |
| `cast-server/tests/ui/agents/cast-ui-test-runs/` | `cast-ui-test-runs.md`, `config.yaml` | Create |
| `cast-server/tests/ui/agents/cast-ui-test-scratchpad/` | `cast-ui-test-scratchpad.md`, `config.yaml` | Create |
| `cast-server/tests/ui/agents/cast-ui-test-goal-detail/` | `cast-ui-test-goal-detail.md`, `config.yaml` | Create |
| `cast-server/tests/ui/agents/cast-ui-test-focus/` | `cast-ui-test-focus.md`, `config.yaml` | Create |
| `cast-server/tests/ui/agents/cast-ui-test-about/` | `cast-ui-test-about.md`, `config.yaml` | Create |

## Detailed Steps

### Step 4b.1: Build the shared instructions template

Every per-screen child agent uses the same template (substitute `<screen>` per agent).
Author it once, then copy + customize for each screen:

```markdown
# cast-ui-test-<screen>

Drive the `<screen>` page of the Diecast UI in a Chromium browser via Playwright,
asserting smoke + functional behaviors.

## Inputs (from delegation_context)

- `goal_slug` (required, string): shared test goal slug, format `ui-test-<unix_ts>-<rand4>`.
- `base_url` (optional, string, default `http://127.0.0.1:8006`): test server.

## Output

Write `output.json` in the goal directory. Structure (mirrors runner.py's per-screen output):

```json
{
  "screen": "<screen>",
  "status": "completed" | "failed" | "skipped",
  "assertions_passed": [...],
  "assertions_failed": [...],
  "console_errors": [...],
  "console_warnings": [...],
  "screenshots": [...],
  "started_at": "ISO8601",
  "finished_at": "ISO8601"
}
```

The simplest implementation copies runner.py's output verbatim.

## Procedure

1. Read the canonical delegation contract: `/cast-child-delegation`. Apply it for any future
   sub-delegation; this child does not delegate further.

2. Resolve the runner output path inside this run's goal directory, e.g.:
   `<goal_dir>/runner-output.json`.

3. Invoke the runner directly (DO NOT use `python -m`):

   ```bash
   python "${DIECAST_ROOT}/cast-server/tests/ui/runner.py" \
       --screen=<screen-arg> \
       --base-url="<base_url>" \
       --goal-slug="<goal_slug>" \
       --output="<goal_dir>/runner-output.json"
   ```

   Where `<screen-arg>` is exactly:
   - dashboard:    `dashboard`
   - agents:       `agents`
   - runs:         `runs`
   - scratchpad:   `scratchpad`
   - goal-detail:  `goal-detail`  (runner.py normalizes the dash)
   - focus:        `focus`
   - about:        `about`

4. After runner.py exits, read `runner-output.json` and copy its contents to this agent's
   `output.json`. The runner is the source of truth for `assertions_passed/failed`,
   `console_errors/warnings`, and `screenshots`.

5. Exit cleanly.

## Constraints

- Do NOT touch the dev server on `:8000`.
- Per-assertion timeout: 30s (enforced by runner.py).
- This child's wall-clock cap (orchestrator-imposed): 90s.
- Console error policy: `level=='error'` or `level=='pageerror'` fail the run; warnings
  are recorded but do not fail (Decision #6, runner.py enforces).
- If runner.py exits non-zero, this agent's `output.json` should still mirror the runner's
  `output.json` (which carries the failure detail). Do NOT swallow failures.
```

### Step 4b.2: Per-screen specializations

The bulk of each agent's instructions is the shared template above. Specialize each one with
a "Screen-specific notes" section that points at the corresponding US4 scenarios:

**`cast-ui-test-dashboard`** — US4 S1, S2, S2b. Owns goal creation: this child is
dispatched first by the orchestrator and creates `goal_slug` (the shared goal). Also
creates a separate `ui-test-delete-<ts>` throwaway for the delete-flow assertion.

**`cast-ui-test-agents`** — US4 S6. Validates that `cast-ui-test-*` cards are visible on
`/agents` (proves the registry merge worked).

**`cast-ui-test-runs`** — US4 S7, S7b. Triggers `cast-ui-test-noop --sleep=20`, cancels
via UI, asserts cancelled status. (runner.py owns the HTTP trigger; agent just dispatches
the runner.)

**`cast-ui-test-scratchpad`** — US4 S8. Submit + delete entries.

**`cast-ui-test-goal-detail`** — US4 S3, S4, S5, S5b, S5c, S5d, S5e. The biggest screen
child by surface area: 5 tabs, idea→accepted transition, focus toggle, task CRUD, artifact
CRUD, trigger noop and assert run on `/runs`. All assertions live in runner.py; the agent
just dispatches `--screen=goal-detail`.

**`cast-ui-test-focus`** — US4 S9. Empty-state vs focused-goal branching.

**`cast-ui-test-about`** — US4 S10. Static content + zero JS console errors.

The "Screen-specific notes" section should be brief (3-6 lines) and reference the relevant
US4 scenarios by number — runner.py is where the actual assertion code lives.

### Step 4b.3: Per-screen `config.yaml`

All 7 share the same shape; substitute the agent name. Example for dashboard:

```yaml
name: cast-ui-test-dashboard
description: |
  Diecast UI e2e: dashboard screen. Smoke + functional asserts via Playwright.
entrypoint: cast-ui-test-dashboard.md
inputs:
  goal_slug:
    type: string
    required: true
  base_url:
    type: string
    required: false
    default: http://127.0.0.1:8006
tags:
  - test
  - ui
visible: true
```

Mirror the production `config.yaml` schema exactly (refer to one prod agent for the
canonical key list). For all 7 agents, only `name`, `description`, `entrypoint` differ.

### Step 4b.4: Verify all 7 directories created

```bash
ls cast-server/tests/ui/agents/ | grep -c '^cast-ui-test-'
# Expect 9 if sp4a also landed (orchestrator + noop + 7 screens), 7 if only sp4b.
```

### Step 4b.5: Spot-check one agent end-to-end

Once sp1, sp2, sp3, sp4a are all in place, you can manually drive a single screen child
to confirm the dispatch chain works (without needing the full orchestrator):

```bash
# Boot the test server manually.
CAST_TEST_AGENTS_DIR=$(pwd)/cast-server/tests/ui/agents \
CAST_DB_PATH=/tmp/diecast-uitest-manual.db \
CAST_HOST=127.0.0.1 CAST_PORT=8006 \
  bin/cast-server &
SERVER_PID=$!

# Wait for health.
until curl -fsS http://127.0.0.1:8006/api/health > /dev/null; do sleep 0.5; done

# Trigger one child directly.
curl -X POST http://127.0.0.1:8006/api/agents/cast-ui-test-about/trigger \
  -H 'Content-Type: application/json' \
  -d '{"goal_slug":"ui-test-manual-0001","delegation_context":{"goal_slug":"ui-test-manual-0001"}}'

# Wait/poll, inspect the child's output.json under goals/ui-test-manual-0001/.

# Cleanup.
kill $SERVER_PID
rm -f /tmp/diecast-uitest-manual.db /tmp/diecast-uitest-manual.db-*
rm -rf goals/ui-test-manual-0001
```

(This is a sp5-territory check; do it only as a smoke test if you have time.)

## Verification

### Automated Tests (permanent)

Permanent verification: sp1's `test_registry_visibility.py` expects all 9 names. After
sp4b lands, that meta-test should be fully green (assuming sp4a also landed).

### Validation Scripts (temporary)

```bash
# All 7 dirs exist with both required files.
for s in dashboard agents runs scratchpad goal-detail focus about; do
  d="cast-server/tests/ui/agents/cast-ui-test-$s"
  test -f "$d/cast-ui-test-$s.md" || echo "MISSING: $d/cast-ui-test-$s.md"
  test -f "$d/config.yaml"        || echo "MISSING: $d/config.yaml"
done
echo "(no MISSING output → all present)"

# Every config.yaml parses.
python -c "import yaml, pathlib; \
[yaml.safe_load(p.read_text()) \
 for p in pathlib.Path('cast-server/tests/ui/agents').rglob('config.yaml')]; \
print('all configs parsed')"

# Every instructions file references the canonical skill.
grep -L 'cast-child-delegation' \
  cast-server/tests/ui/agents/cast-ui-test-{dashboard,agents,runs,scratchpad,goal-detail,focus,about}/*.md
# Expect: empty output (no files missing the reference).

# Every instructions file references runner.py with direct script path (not -m).
grep -L 'runner.py' \
  cast-server/tests/ui/agents/cast-ui-test-{dashboard,agents,runs,scratchpad,goal-detail,focus,about}/*.md
# Expect: empty output.

# No `python -m` invocations leak in.
grep -l 'python -m' \
  cast-server/tests/ui/agents/cast-ui-test-{dashboard,agents,runs,scratchpad,goal-detail,focus,about}/*.md
# Expect: empty output.
```

### Manual Checks

- Diff one screen agent's instructions against the orchestrator's: confirm the canonical
  delegation skill is referenced in both styles (orchestrator delegates to multiple; screen
  child shells out to runner.py only).
- Diff `config.yaml` across all 7 screens to confirm only `name`/`description`/`entrypoint`
  differ — every other key is identical.

### Success Criteria

- [ ] All 14 files exist (7 dirs × 2 files).
- [ ] Every `config.yaml` parses as YAML and has `name`, `description`, `entrypoint`,
      `inputs.goal_slug`, `inputs.base_url`, `visible: true`.
- [ ] Every instructions file references `/cast-child-delegation` skill verbatim.
- [ ] Every instructions file invokes runner.py via direct script path (`python "${DIECAST_ROOT}/...runner.py"`),
      NOT `python -m`.
- [ ] `--screen` value matches the screen this agent owns (`dashboard`, ..., `goal-detail`,
      not `goal_detail`).
- [ ] Console-error policy + 30s/90s caps + canonical-skill reference all present.
- [ ] With `CAST_TEST_AGENTS_DIR` set to this dir, `get_all_agents()` returns all 7 names
      (plus orchestrator + noop from sp4a).

## Execution Notes

- **DRY pays here.** Author one template, then mass-produce 7 files. The differences are
  the screen name, the `--screen` arg, and a brief "screen-specific notes" section.
- **`goal-detail` is the dashed name.** The agent dir is `cast-ui-test-goal-detail`, the
  agent name is `cast-ui-test-goal-detail`, and the `--screen` arg passed to runner.py is
  `goal-detail`. Runner.py normalizes the dash to underscore internally for dispatch.
- **`${DIECAST_ROOT}` resolution:** the cast-server agent runtime is expected to set this
  env var (or an equivalent) for child agents. If it doesn't, document the correct path
  resolution in the agent instructions (e.g., absolute path to repo root). Confirm by
  inspecting an existing production agent that shells out — copy its convention.
- **Skill delegation:** -> Use `/cast-agent-design-guide` once on a representative screen
  agent to confirm the file structure and IO schema match project canon. Then mass-produce
  the rest.
- **Spec-linked files:** None of the modified files are covered by a spec in `docs/specs/`.
