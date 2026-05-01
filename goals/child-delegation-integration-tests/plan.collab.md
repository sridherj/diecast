# High-Level Phasing Plan: Child Delegation Integration Tests

## Overview

Ship a single goal that delivers (a) a fast T1 integration suite mirroring second-brain's
`test_delegation.py` coverage adapted to diecast's file-canonical contract, (b) diecast-only
additions for `external_project_dir` 422, output-JSON v2 conformance, and mtime-heartbeat
round-trip, (c) a nightly T2 live HTTP E2E tier, and (d) commits that flip the user's
"feels broken in several ways" symptom buckets from red to green inside this same goal.

Approach is tests-first with a red→green commit trail. Coverage parity with second-brain
is the floor; diecast-only behaviors are the additions. The plan front-loads fixture
scaffolding (because every later phase depends on those agents) and gates twice for
human input — once to confirm fixture location and dispatch_mode declarations, once to
review the actual failing-test enumeration before fix work begins.

Recommended resolutions for the two parked spec questions:
- Fixture-agent location → `cast-server/tests/integration/agents/<name>/config.yaml`
  (separate from `cast-server/tests/ui/agents/`)
- T2 ptyxis-in-CI → self-hosted nightly runner with ptyxis (option a)

Both are revisited at gates — not assumed.

## Phase 1: Fixture Scaffolding & Registry Wiring

**Outcome:** Four fixture agents exist on disk, are loadable by `load_agent_config()`,
and are visible to a running cast-server's agent registry. Both T1 (config injection)
and T2 (live registry) can reach them by name.
**Dependencies:** None
**Estimated effort:** 1 session (2-3 hours)
**Verification:**
- `pytest cast-server/tests/integration/test_fixture_agents_load.py` passes
  (asserts each fixture loads via `load_agent_config()`, has `model: haiku`, and
  declares the expected `dispatch_mode` + `allowed_delegations`)
- Manual: `curl -X POST http://localhost:8765/api/agents/cast-test-parent-delegator/trigger`
  returns a non-404 response shape (422 acceptable — proves the fixture is registered)

Key activities:
- Create `cast-server/tests/integration/agents/` directory tree (recommended location;
  confirmed at Gate A)
- Author `config.yaml` for each of the four fixtures:
  - `cast-test-parent-delegator` — `dispatch_mode: http`, `allowed_delegations: [cast-test-child-worker, cast-test-child-worker-subagent]`, `model: haiku`
  - `cast-test-child-worker` — `dispatch_mode: http`, `allowed_delegations: []`, `model: haiku`
  - `cast-test-child-worker-subagent` — `dispatch_mode: subagent`, `allowed_delegations: []`, `model: haiku`
  - `cast-test-delegation-denied` — `dispatch_mode: http`, `allowed_delegations: [cast-test-child-worker]`, `model: haiku`; the agent's prompt deliberately tries to dispatch a NON-allowlisted target so US3 Scenario 2 can assert the 422
- Wire fixture directory into the agent registry loader (extend the existing discovery
  path or add a `CAST_AGENT_FIXTURE_DIRS` env-var hook — pick whichever is the smallest
  diff; check `agent_service.py` for the current registry discovery seam)
- Author the equivalence-map docstring stub at the top of
  `cast-server/tests/integration/test_child_delegation.py` listing all 11 second-brain
  test classes with TODO markers — populated as tests land in Phase 2

**[GATE A]** After this phase, surface the fixture-agent location and the four
`dispatch_mode`/`allowed_delegations` declarations to the user for confirmation
before writing any tests against them. If location or declarations change, this
phase is the cheapest place to revise.

## Phase 2: T1 Integration Suite — Coverage Parity Baseline

**Outcome:** All 11 test classes from second-brain's `test_delegation.py` have diecast
counterparts wired against the file-canonical contract. Suite runs in <30s under
`CAST_DISABLE_SERVER=1` with the env-var timing overrides. The equivalence-map
docstring is fully populated.
**Dependencies:** Phase 1
**Estimated effort:** 2-3 sessions (5-8 hours)
**Verification:**
- `CAST_DISABLE_SERVER=1 CAST_DELEGATION_BACKOFF_OVERRIDE=10ms,20ms,50ms CAST_DELEGATION_IDLE_TIMEOUT_SECONDS=4 pytest cast-server/tests/integration/test_child_delegation.py`
  exits non-zero (some failures expected — those are the symptom buckets) but
  every test class from second-brain is represented and runs
- `time` of the full suite invocation is <30s (failures count toward budget)
- Equivalence-map docstring lists all 11 second-brain classes, each named with its
  diecast counterpart class or marked justified-as-skipped

Key activities:
- Port test classes 1:1, mapped to US1 acceptance scenarios:
  - Allowlist validation (US1.S2) → `TestAllowlistValidation`
  - Depth enforcement (US1.S3) → `TestDelegationDepthEnforcement`
  - Depth calculation (US1.S3) → `TestDepthCalculation` (mocks `_get_delegation_depth`)
  - Delegation-context file write + JSON shape (US1.S4) → `TestDelegationContextFile`
  - Result_summary populate/None/truncate (US1.S6) → `TestResultSummary`
  - Child-launch isolation (US1.S1) → `TestChildLaunchIsolation`
  - Terminal title formatting → `TestTerminalTitleFormatting`
  - Continuation file delivery (US1.S10) → `TestContinueAgentRun`
  - Prompt + delegation file cleanup on finalize (US1.S5) → `TestFinalizeCleanup`
  - No-inline preamble injection (US1.S7) → `TestPreambleAntiInline`
  - Delegation-instruction-in-prompt + interactive block (US1.S7, S8) → `TestPromptBuilder`
  - Mixed-transport preamble (US1.S9) → `TestMixedTransportPreamble` (uses `\b<name>\b` regex matching second-brain pattern; asserts `out.count("NEVER inline") == 1`)
- Use `tmp_path`-scoped goal directories per test (constraint compliance)
- Honor `CAST_DELEGATION_BACKOFF_OVERRIDE` parsing (US6.S1) and `CAST_DISABLE_SERVER`
  short-circuit (US6.S2)
- NO Python imports of `requests`/`httpx`/`urllib` (FR-008); assert against files on disk
- DO NOT re-test B3/B4/B5 primitives — compose them at round-trip level only (Out of Scope)
- Populate the equivalence-map docstring as each class lands

**[GATE B]** After this phase: produce the failing-test list — the actual enumeration
of what's broken — and surface it to the user before committing to the fix-work in
Phase 4. This is the "convert vibe to enumerated regressions" moment that US2 hangs on.

## Phase 3: T1 Diecast-Only Additions

**Outcome:** Diecast behaviors that have no second-brain analogue are covered:
`external_project_dir` 422 precondition (both at trigger AND at launcher re-validate),
output-JSON contract v2 conformance (terminal status, US14 typed `next_steps`, US13
open-question tag enforcement), and mtime-heartbeat round-trip under parent→child.
**Dependencies:** Phase 2
**Estimated effort:** 1-2 sessions (3-5 hours)
**Verification:**
- New test classes in `test_child_delegation.py` for each of the three additions
- Specifically: `TestExternalProjectDirPrecondition`,
  `TestOutputJsonContractV2`, `TestMtimeHeartbeatRoundTrip`
- Suite still runs in <30s

Key activities:
- `TestExternalProjectDirPrecondition` (US2.S3, US2.S7, FR-002):
  - Trigger-side 422 with structured body (`error_code: "missing_external_project_dir"`,
    `goal_slug`, `configured_path`, `detail`, `hint`) when `external_project_dir` is
    unset or set-to-nonexistent
  - Launcher-side re-validation (`_launch_agent`) — same body shape
  - Depth-4 dispatch returns 422 BEFORE row creation (no row in `agent_runs`)
  - Honors `/invoke` carve-out (negative test: `/invoke` does NOT 422)
- `TestOutputJsonContractV2` (US2.S4, S5, S6, FR-002):
  - Non-terminal `status` (pending/running/idle) treated as malformed →
    parent finalizes `failed`+parse-error
  - `next_steps` validated against `tests/fixtures/next_steps.schema.json`
    (create the schema file as part of this phase — typed shape per US14)
  - Untagged `Open Questions` items flagged as US13 contract violation
- `TestMtimeHeartbeatRoundTrip` (US2.S1, FR-002):
  - Parent observes child's mtime update within ≤1 polling-tick (using the
    `CAST_DELEGATION_BACKOFF_OVERRIDE` ladder from Phase 2)
  - File-canonical only; HTTP is mocked/disabled

## Phase 4: Red-to-Green Fix Sweep

**Outcome:** Every test added by this goal is green. Each of the three observed
symptom buckets has at least one dedicated `fix(delegation): green <test_name>`
commit. The "feels broken" vibe is converted to an enumerated record of resolved
regressions.
**Dependencies:** Phase 3, Gate B (the failing-test list must be reviewed first)
**Estimated effort:** 2-4 sessions (5-10 hours, scales with what Gate B reveals)
**Verification:**
- `git log --grep "fix(delegation): green"` shows ≥3 commits, each naming a
  distinct test from a distinct symptom bucket (SC-003)
- Full T1 suite green: `pytest cast-server/tests/integration/test_child_delegation.py`
  exits 0 in <30s
- No `xfail` markers remain on tests that this goal added
- No unrelated refactor in the diff (constraint check during PR review)

Key activities, sub-phased by symptom bucket:

### 4a — Parent stall after child finalize (US2.S1)
- Targets: any test in `TestMtimeHeartbeatRoundTrip` or finalize-poll classes that
  shows the parent failing to transition within 1 polling tick after child mtime updates
- Likely implicated code: `_finalize_run_from_monitor`, the polling loop in
  `agent_service.py`
- Fix scope: minimum diff to green the test — no broader polling refactor

### 4b — Cleanup or contract drift (US2.S2, S3, S5)
- Targets: orphan `.delegation-*.json` / `.prompt` / `.continue` / `.tmp` files,
  malformed 422 body shape, mixed-transport preamble emission errors
- Likely implicated code: finalizer cleanup, trigger route, `_build_agent_prompt`
  mixed-transport branch
- Fix scope: align observed behavior with `cast-delegation-contract.collab.md`
  exactly; if contract is the wrong shape, escalate (do NOT silently change spec)

### 4c — Allowlist / depth / output-JSON contract passing silently (US2.S4, S6, S7)
- Targets: non-terminal status not flagged, untagged Open Questions not flagged,
  4th-depth dispatch creating a row before refusing
- Likely implicated code: output-JSON parser/validator, `_get_delegation_depth`
  ordering vs row-create
- Fix scope: tighten validation to fail loudly; small diffs

For each sub-phase: pick a failing test → diagnose → apply minimum fix → commit
`fix(delegation): green <test_name>` (FR-006). Use `cast-detailed-plan` to split
each sub-phase into atomic tasks if the fix surface area is non-trivial.

## Phase 5: T2 Live HTTP E2E

**Outcome:** Three live HTTP E2E cases run against a spawned cast-server and assert
the boundary contract (parent_run_id linkage in DB, tmux session teardown, dispatch
precondition 422, allowlist denial). Suite is wired to a nightly CI workflow.
**Dependencies:** Phase 4 (T1 must be green before adding the slower live tier),
plus Gate C (CI strategy decision)
**Estimated effort:** 1-2 sessions (3-5 hours), excluding CI runner setup which is
external work
**Verification:**
- `pytest cast-server/tests/e2e/test_tier_delegation.py -m e2e` green on a host
  with cast-server bin available and ptyxis installed
- Nightly CI workflow shows green for ≥3 consecutive runs after this phase lands
  (counts toward SC-002, may complete after goal close)

Key activities:
- Author `cast-server/tests/e2e/test_tier_delegation.py` with three cases:
  - `test_parent_delegator_happy_path` (US3.S1): trigger
    `cast-test-parent-delegator`, poll for completion, assert ≥1 child run with
    `parent_run_id` set, `result_summary` non-empty, child's tmux session torn down
  - `test_delegation_denied` (US3.S2): trigger `cast-test-delegation-denied`,
    parent completes with no child rows, `result_summary` contains "422" or "denied"
  - `test_mid_flight_session_isolation` (US3.S3): poll within 60s for separate
    `agent-<parent>` and `agent-<child>` tmux sessions, parent has 1 pane (not split);
    `pytest.skip` if child completes too fast (matches second-brain pattern)
- Use a dedicated `child-delegation-e2e` test goal directory; tear down after each run
- Run WITHOUT the `CAST_DISABLE_SERVER` / backoff overrides (production cadence)
- Wire to nightly CI workflow per Gate C decision

**[GATE C]** Before authoring the CI workflow YAML, confirm with the user:
self-hosted nightly runner with ptyxis (recommended option a) vs `xvfb-run` wrap
(option b) vs graceful-skip-when-ptyxis-missing (option c). The test code itself
is identical across options; only the workflow definition and runner labels differ.

## Phase 6: Subagent Coverage — Builder Unit Tests + Manual Checklist

**Outcome:** Subagent-mode regressions in the prompt-shape/preamble-builder are caught
automatically via T1 unit tests. A manual checklist file documents live verification
steps for periodic execution. No automated subagent live E2E (correctly out of scope).
**Dependencies:** Phase 2 (preamble tests live alongside the rest of T1)
**Estimated effort:** 1 session (2-3 hours)
**Verification:**
- `TestSubagentOnlyPreamble` and the mixed-transport assertions from Phase 2 are green
- `cast-server/tests/MANUAL_SUBAGENT_CHECKLIST.md` exists with ≤10 steps
- A maintainer NOT involved in writing the checklist follows it cold and confirms
  green in <5 min; result recorded in checklist's "verified by" footer (SC-005)

Key activities:
- Add `TestSubagentOnlyPreamble` to `test_child_delegation.py` (US4.S2):
  - `_build_agent_prompt` with `allowed_delegations=[subagent_only_target]`
    emits ONLY the Subagent-dispatch block, includes structured-return / no-summarize
    contract, does NOT emit curl/poll quick reference
- Author `cast-server/tests/MANUAL_SUBAGENT_CHECKLIST.md` (≤10 steps) covering
  US4.S1: dispatch via Claude Code's Agent tool, verify verdict surfaced as-is
  (not summarized), confirm no `agent_runs` row created (subagent-mode bypasses
  run queue), confirm preamble named target in Subagent block
- Include "verified by" footer with date/maintainer/result on first execution

This phase can run in parallel with Phase 5 — they touch independent code paths.
Marked Phase 6 (not 5b) because it's small enough that serial execution is fine
if a single person is driving.

## Phase 7: Close-Out

**Outcome:** Goal is closed cleanly. CI is wired and observed green. Equivalence map
is reviewed. Phase status flipped to closed.
**Dependencies:** Phases 4, 5, 6
**Estimated effort:** 0.5 session (1-2 hours, plus elapsed time waiting on nightly CI)
**Verification:**
- Nightly CI shows T2 green for ≥3 consecutive runs (SC-002)
- Reviewer signs off on equivalence-map docstring (SC-007)
- Manual checklist's "verified by" footer is populated (SC-005)
- `goal.yaml` shows `status: completed` (or whatever close state the goal model uses)

Key activities:
- Verify nightly CI has accumulated ≥3 green runs
- Reviewer cross-check: every second-brain `test_delegation.py` test class has either
  a diecast counterpart OR a justified-as-skipped entry in the equivalence map (SC-007)
- Update `cast-delegation-contract.collab.md` if any contract clarification surfaced
  during the fix sweep (Phase 4) — use `/cast-update-spec`
- Flip goal status to closed via `/cast-goals` (do NOT edit `goal.yaml` directly)

## Build Order

```
Phase 1 (Fixtures) ──► [GATE A] ──► Phase 2 (T1 Parity) ──► Phase 3 (Diecast Adds)
                                          │
                                          └──► [GATE B] ──► Phase 4 (Red→Green Fixes)
                                                                    │
                                                                    ├──► Phase 5 (T2 E2E) ──► [GATE C wires CI]
                                                                    │           │
                                                                    └──► Phase 6 (Subagent) ──┤
                                                                                              │
                                                                                              └──► Phase 7 (Close-out)
```

**Critical path:** Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 7

Phase 6 can run in parallel with Phase 5 if two people are driving; otherwise serialize
behind Phase 4 in any order (both small).

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Phase 4 fix work uncovers a deeper architectural issue (e.g., the polling loop is structurally racy, not just buggy) | High | Out-of-scope clause in spec: file a separate goal, do NOT expand this one. Gate B reviews the failing-test list before fix work — if a test points at a structural issue, escalate at the gate, not mid-fix. |
| Fixture-agent registry discovery mechanism doesn't have a clean seam for test-only fixture dirs | Medium | Phase 1 explicitly checks `agent_service.py` for the discovery seam first. If no seam exists, smallest-diff option is a `CAST_AGENT_FIXTURE_DIRS` env-var hook — adds one constant, one os.environ check, no architectural change. |
| Mixed-transport preamble test (`TestMixedTransportPreamble`) is the trickiest port — second-brain's regex `\b<name>\b` may not transfer cleanly if diecast preamble structure has diverged | Medium | Read `_build_agent_prompt` thoroughly before writing the test. If diecast structure has diverged, the test docstring documents the divergence in the equivalence map (justified deviation, not skipped). |
| ptyxis CI strategy (Gate C) blocks T2 indefinitely if no CI infra owner is available to set up self-hosted runner | Medium | Gate C is a decision, not a blocker — the test code in Phase 5 is independent of the runner choice. If Gate C decision delays, Phase 5 still ships test code; the workflow YAML is the only deferred artifact. |
| T1 wall-clock budget (<30s) busted by env-var timing not actually applying because the override hook is broken | Low-Medium | US6 has explicit acceptance scenarios for the env-var hooks. If the hooks don't work, that's its own red-then-green test in Phase 4 — surfacing the bug, not hiding it. |
| Goal scope creep — Phase 4 fix sweep tempts cleanup of adjacent code | Medium | FR-006 commit-message convention (`fix(delegation): green <test_name>`) makes scope creep visible at PR review. Constraint: "no unrelated refactor" is enforced by reviewer. |

## Open Questions

- **Fixture-agent location** — Recommended `cast-server/tests/integration/agents/<name>/`,
  separate from `cast-server/tests/ui/agents/`. Resolved at **Gate A** (after Phase 1
  scaffolding). If the user prefers a different location, Phase 1 is the cheapest place
  to revise — no test code yet depends on the path.
- **T2 ptyxis-in-CI strategy** — Recommended option (a): self-hosted nightly runner with
  ptyxis. Alternative (b): `xvfb-run` wrap. Alternative (c): graceful-degrade when ptyxis
  missing. Resolved at **Gate C** (before Phase 5 CI workflow YAML). Test code is
  workflow-agnostic.
- **Failing-test enumeration before Phase 4** — The spec's US2 hinges on converting the
  user's "feels broken" vibe to a concrete list. The actual list is unknown until Phase 2
  + Phase 3 produce real failures. Resolved at **Gate B** before any fix work commits.
- **`/invoke` carve-out negative test placement** — Spec explicitly carves `/invoke` out
  of `external_project_dir` enforcement. Phase 3 includes a negative test asserting this.
  Open: should the negative test live in `TestExternalProjectDirPrecondition` or a
  separate `TestInvokeRouteCarveOut` class? Recommendation: same class, named test method
  (`test_invoke_route_does_not_422`). Non-blocking — finalize while authoring Phase 3.
- **Fixture for `tests/fixtures/next_steps.schema.json`** — Phase 3 creates this schema
  file. Open: should it be canonical (referenced by non-test code as well) or test-only?
  Recommendation: test-only for now. If non-test code needs it later, promote to
  `cast-server/cast_server/contracts/`. Non-blocking.

## Spec References

Specs loaded for consistency check:
- `docs/specs/cast-delegation-contract.collab.md` — file-canonical delegation contract.
  This goal's tests assert against it; no spec changes anticipated unless Phase 4 fix
  sweep reveals contract drift, in which case `/cast-update-spec` is invoked from
  Phase 7.
- `docs/specs/cast-output-json-contract.collab.md` — output JSON contract v2 (terminal
  status, US13 open-question tags, US14 typed `next_steps`). Phase 3 asserts conformance;
  no spec changes anticipated.

No phase activity contradicts existing spec'd behavior. The plan is purely additive
(tests + minimum-diff fixes). If Phase 4 fix work reveals that observed behavior and
spec disagree, the resolution policy is: align code to spec OR escalate spec change
to user (do NOT silently change either).
