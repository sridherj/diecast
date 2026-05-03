# Shared Context: Child Delegation Integration Tests

## Source Documents
- High-level plan: `goals/child-delegation-integration-tests/plan.collab.md`
- Detailed plan (authority): `goals/child-delegation-integration-tests/plan_detailed.collab.md`
- Refined requirements (spec): `goals/child-delegation-integration-tests/refined_requirements.collab.md`
- Reference suites (read-only, on neighbor repo):
  - `<SECOND_BRAIN_ROOT>/taskos/tests/test_delegation.py`
  - `<SECOND_BRAIN_ROOT>/taskos/tests/e2e/test_tier2_delegation.py`

## Project Background

The diecast delegation code path (parent → child agent dispatch) is suspected of
multiple silent regressions: parent stalls after child finalize, orphan cleanup
files, allowlist/depth/output-JSON contract violations passing silently. The user's
"feels broken in several ways" symptom needs to become an enumerated list of
*concrete failing tests that flip green inside this same goal*.

The deliverable is a single goal that ships:
1. A fast T1 integration suite (<30s) mirroring second-brain's
   `test_delegation.py` coverage parity, adapted to diecast's file-canonical contract
2. Diecast-only T1 additions: `external_project_dir` 422 precondition, output-JSON
   contract v2 conformance (US13 open-question tags, US14 typed `next_steps`),
   mtime-heartbeat round-trip
3. A nightly T2 live HTTP E2E tier (real cast-server, real curl, ptyxis terminals)
4. A red→green commit trail (`fix(delegation): green <test_name>`) that closes
   ≥1 test per symptom bucket

**Operating mode: HOLD SCOPE.** Spec is rigorous and exhaustive (8 FRs, 7 SCs, 6 USs).
No expansion, no reduction. Coverage parity with second-brain is the floor;
diecast-only contracts are the additions.

## Codebase Conventions

- **File-canonical contract.** Tests assert against files on disk, NOT HTTP responses.
  cast-server is a read-through layer. T2 is the only tier where HTTP IS the boundary.
- **No Python HTTP imports** (FR-008): no `requests`, `httpx`, `urllib`. Bash-curl
  is the only allowed dispatch primitive in tests.
- **Test agents use `model: haiku`** for fast/cheap fixture runs.
- **`tmp_path` per test** for goal directories (T1). T2 uses dedicated
  `child-delegation-e2e` test goal, torn down between cases.
- **Commit convention** for fix sweep: `fix(delegation): green <test_name>` (FR-006).
- **Goal status flips** via `/cast-goals` skill, never direct edit of `goal.yaml`.
- **Spec changes** via `/cast-update-spec` skill, never hand-edit, never silent change.

## Key File Paths

| Path | Role |
|------|------|
| `cast-server/cast_server/services/agent_service.py` | `trigger_agent`, `_launch_agent`, `_finalize_run` (line ~1702), `_finalize_run_from_monitor` (line ~2520), `_get_delegation_depth`, `get_all_agents` (line ~1614, merge-with-collision-warn at 1618-1631), polling loop primitive |
| `cast-server/cast_server/models/agent_config.py` | `AgentConfig` model, `_candidate_config_paths` (line ~62), `_config_cache` (line ~59, mtime-invalidated), dispatch_mode validator (lines ~36-41, intentional silent fallback to `http`), `load_agent_config` (public seam — monkeypatch in tests) |
| `cast-server/cast_server/routes/api_agents.py` | `POST /api/agents/{name}/trigger` route, `/invoke` route (carved out from `external_project_dir` enforcement) |
| `cast-server/tests/integration/agents/<name>/config.yaml` | Fixture agents (created in sp1.2) — separate from `tests/ui/agents/` |
| `cast-server/tests/integration/test_child_delegation.py` | T1 suite (created across Phase 1 + 2 + 3 + 6) |
| `cast-server/tests/integration/conftest.py` | T1 fixture wiring (sp1.3) — sets `CAST_TEST_AGENTS_DIR`, autouse `_config_cache.clear()` |
| `cast-server/tests/integration/pytest.ini` | Suite-wide `timeout = 5` (sp2.1) |
| `cast-server/tests/e2e/test_tier_delegation.py` | T2 live HTTP E2E (sp5.x) |
| `cast-server/tests/e2e/conftest.py` | T2 session-scoped server spawn + per-test goal-dir reset (sp5.1) |
| `cast-server/tests/fixtures/next_steps.schema.json` | US14 typed-shape schema (created sp3.2) |
| `cast-server/tests/MANUAL_SUBAGENT_CHECKLIST.md` | Subagent live-exercise checklist (sp6.2) |
| `cast-server/tests/test_dispatch_precondition.py` | EXISTING — covers 8+ precondition cases; sp3.1 must NOT duplicate |

## Data Schemas & Contracts

### Fixture agent declarations (sp1.2)

```yaml
# cast-test-parent-delegator/config.yaml
dispatch_mode: http
allowed_delegations: [cast-test-child-worker, cast-test-child-worker-subagent]
model: haiku

# cast-test-child-worker/config.yaml
dispatch_mode: http
allowed_delegations: []
model: haiku

# cast-test-child-worker-subagent/config.yaml
dispatch_mode: subagent
allowed_delegations: []
model: haiku

# cast-test-delegation-denied/config.yaml
dispatch_mode: http
allowed_delegations: [cast-test-child-worker]   # tries to dispatch a NON-allowlisted target
model: haiku
```

### Determinism rule for fixture prompts (Review #5)

Every fixture prompt MUST instruct the child to write a LITERAL contract-v2 output
JSON envelope: `Write to <output_path> EXACTLY this JSON, do not paraphrase, do not
add fields: {...verbatim envelope...}`. This makes T2 substring assertions byte-stable.
The denied fixture's prompt MUST include the substring `"denied (422)"` literally
inside the parent's `summary`, so sp5.2 can assert deterministically.

### 422 dispatch-precondition body (cast-delegation-contract.collab.md)

```json
{
  "error_code": "missing_external_project_dir",
  "goal_slug": "...",
  "configured_path": "...",
  "detail": "...",
  "hint": "..."
}
```

### T1 environment

```
CAST_DISABLE_SERVER=1
CAST_DELEGATION_BACKOFF_OVERRIDE=10ms,20ms,50ms
CAST_DELEGATION_IDLE_TIMEOUT_SECONDS=4
```

T2 runs WITHOUT these (production cadence).

## Pre-Existing Decisions (locked — do not re-litigate)

| Decision | Source |
|----------|--------|
| T1 path: `cast-server/tests/integration/test_child_delegation.py` | Plan §Phase 2 |
| T2 path: `cast-server/tests/e2e/test_tier_delegation.py` | Plan §Phase 5 |
| Fixture path: `cast-server/tests/integration/agents/<name>/config.yaml` (revisited Gate A) | Plan §Phase 1 |
| Registry-discovery seam: `CAST_TEST_AGENTS_DIR` env var (already exists) | Review #1 |
| All fixtures: `model: haiku` | Spec §Constraints |
| Equivalence-map docstring at top of T1 module (NOT separate `.md`) | FR-007 |
| Cache-isolation: monkeypatch `load_agent_config` (not direct cache mutation) | Review #3 |
| Suite-wide `pytest-timeout = 5` for `tests/integration/` | Review #7 |
| Mixed-transport regex: `\b<name>\b` (matches second-brain verbatim) | SC-004 |
| sp3.3 mtime test is EXPECTED red until sp4a — NO `xfail` markers | Plan §sp3.3, US2 |
| sp4 atomic-task lists DEFERRED until Gate B fires (anti-speculation discipline) | Plan §Phase 4 |
| T2 HTTP via bash curl helper, NOT Python clients (FR-008) | Plan §sp5.1 |
| T2 lifecycle: cast-server session-scoped, goal-dir per-test reset | Review #9 |
| T2 per-case `@pytest.mark.timeout(360)` (idle 300s + 60s buffer) | Review #10 |
| Goal status flip via `/cast-goals` (never direct edit) | User-locked |
| Spec changes via `/cast-update-spec` (never hand-edit) | Plan §Phase 7 |

## Relevant Specs

- `docs/specs/cast-delegation-contract.collab.md` — file-canonical delegation
  contract. Sections referenced: Dispatch Precondition, Heartbeat-by-mtime, Cleanup
  contract, Subagent Dispatch. **Sub-phase agents touching `agent_service.py`,
  `api_agents.py`, or `agent_config.py` MUST read this spec and verify SAV behaviors
  are preserved.** No spec changes anticipated; if Phase 4 surfaces drift, escalate
  via sp7.3 (`/cast-update-spec`).
- `docs/specs/cast-output-json-contract.collab.md` — output JSON contract v2.
  Sections: Terminal Status, US13 (open-question tags), US14 (typed `next_steps`).
  sp3.2 asserts conformance; sp4c may surface drift → escalate via sp7.3.

## Sub-Phase Dependency Summary

| ID | Type | Depends On | Blocks | Parallel With |
|----|------|------------|--------|---------------|
| sp1.1 | Sub-phase | -- | sp1.3 | sp1.2, sp1.4 |
| sp1.2 | Sub-phase | -- | sp1.3 | sp1.1, sp1.4 |
| sp1.3 | Sub-phase | sp1.1, sp1.2 | GA | -- |
| sp1.4 | Sub-phase | -- | GA | sp1.1, sp1.2, sp1.3 |
| GA | Gate | sp1.1-sp1.4 | sp2.1 | -- |
| sp2.1 | Sub-phase | GA | sp2.2 | -- |
| sp2.2 | Sub-phase | sp2.1 | sp2.5 | sp2.3, sp2.4 |
| sp2.3 | Sub-phase | sp2.1 | sp2.5 | sp2.2, sp2.4 |
| sp2.4 | Sub-phase | sp2.1 | sp2.5 | sp2.2, sp2.3 |
| sp2.5 | Sub-phase | sp2.1-sp2.4 | GB | -- |
| GB | Gate | sp2.5 | sp4a/4b/4c | -- |
| sp3.1 | Sub-phase | sp2.5 | Phase 4 | sp3.2, sp3.3 |
| sp3.2 | Sub-phase | sp2.5 | Phase 4 | sp3.1, sp3.3 |
| sp3.3 | Sub-phase | sp2.5 | sp4a | sp3.1, sp3.2 |
| sp4a | Sub-phase | Phase 3 + GB | sp5.x, sp6.x | sp4b, sp4c |
| sp4b | Sub-phase | Phase 3 + GB | sp5.x, sp6.x | sp4a, sp4c |
| sp4c | Sub-phase | Phase 3 + GB | sp5.x, sp6.x | sp4a, sp4b |
| sp5.1 | Sub-phase | Phase 4 | sp5.2, sp5.3 | sp6.x |
| sp5.2 | Sub-phase | sp5.1 | GC | sp5.3, sp6.x |
| sp5.3 | Sub-phase | sp5.1 | GC | sp5.2, sp6.x |
| GC | Gate | sp5.1-sp5.3 | sp5.4 | -- |
| sp5.4 | Sub-phase | GC | sp7.1 | sp6.x |
| sp6.1 | Sub-phase | Phase 4 | sp7.2 | sp5.x, sp6.2 |
| sp6.2 | Sub-phase | -- | sp7.2 | sp5.x, sp6.1 |
| sp7.1 | Sub-phase | sp5.4 (+ ≥3 nights) | sp7.4 | sp7.2, sp7.3 |
| sp7.2 | Sub-phase | Phase 4, Phase 6 | sp7.4 | sp7.1, sp7.3 |
| sp7.3 | Sub-phase | Phase 4 retro | sp7.4 | sp7.1, sp7.2 |
| sp7.4 | Sub-phase | sp7.1, sp7.2, sp7.3 | -- | -- |
