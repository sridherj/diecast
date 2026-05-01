# Gate A: Fixture Path + Dispatch Mode Declarations + Registry Seam

> **Context:** Read sp1.1's seam-verification note and sp1.2's four `config.yaml` files
> before deciding.

## Decision Criteria

Three confirmations needed from the human user before Phase 2 commits to writing tests
against these fixtures. Phase 1 is the cheapest place to revise — no test code yet
depends on any of these.

## Confirmations Needed

### 1. Fixture-agent location

Recommended: `cast-server/tests/integration/agents/<name>/config.yaml`
(separate from existing `cast-server/tests/ui/agents/`).

- **Acceptable as-is →** Continue to Phase 2.
- **Different location →** Move sp1.2 outputs and update sp1.3 conftest path.

### 2. Four fixtures' `dispatch_mode` + `allowed_delegations` declarations

Quote sp1.2's `config.yaml` files verbatim and confirm each:

| Fixture | dispatch_mode | allowed_delegations |
|---------|---------------|---------------------|
| `cast-test-parent-delegator` | `http` | `[cast-test-child-worker, cast-test-child-worker-subagent]` |
| `cast-test-child-worker` | `http` | `[]` |
| `cast-test-child-worker-subagent` | `subagent` | `[]` |
| `cast-test-delegation-denied` | `http` | `[cast-test-child-worker]` (deliberately fails by trying to dispatch a non-allowlisted target in its prompt) |

- **Acceptable as-is →** Continue to Phase 2.
- **Amend →** Update affected `config.yaml` and re-run sp1.3 verification test.

### 3. Registry-discovery seam

sp1.1 confirmed: existing `CAST_TEST_AGENTS_DIR` env-var seam at
`agent_config.py:62-70` + `agent_service.py:1618-1631` resolves the four-fixture layout
without code changes. Cache-isolation: monkeypatch `load_agent_config` per-test.

- **Acceptable as-is →** Continue to Phase 2.
- **Reject in favor of new seam (e.g., `CAST_AGENT_FIXTURE_DIRS`) →** Re-do sp1.3
  conftest with the new seam; document rationale.

## How to Proceed

1. Review sp1.1 output (5-line note) and sp1.2 fixture files.
2. Get user confirmation for all three points (one batch).
3. Update `_manifest.md`: set `GA` status to `Done`, write decisions into Notes.
4. Re-run any affected Phase 1 sub-phases if user amended.
5. Continue: orchestrator advances to sp2.1.
