---
status: refined
confidence:
  intent: high
  behavior: high
  constraints: high
  out_of_scope: high
open_unknowns: 2
questions_asked: 4
---

# Child Delegation Integration Tests — Spec

> **Spec maturity:** draft
> **Version:** 0.1.0
> **Linked files:** docs/specs/cast-delegation-contract.collab.md, docs/specs/cast-output-json-contract.collab.md, skills/claude-code/cast-child-delegation/SKILL.md, cast-server/cast_server/services/agent_service.py, cast-server/cast_server/models/agent_config.py, cast-server/tests/, <SECOND_BRAIN_ROOT>/taskos/tests/test_delegation.py (reference), <SECOND_BRAIN_ROOT>/taskos/tests/e2e/test_tier2_delegation.py (reference)

## Intent

**Job statement.** When delegation code changes (new dispatch path, prompt-builder edit,
contract version bump, finalizer refactor), we want a fast integration-test suite that
catches regressions before merge — and a slower nightly E2E tier that catches drift across
the cast-server boundary — so we can refactor delegation with confidence and pin down
the currently-suspected silent breakages (allowlist/depth/output-JSON violations,
cleanup-and-contract drift, parent stall after child finalize) as red tests that flip
green as fixes ship in this same goal.

The work is the diecast counterpart of second-brain's
`docs/specs/taskos_agent_delegation.collab.md` + `taskos/tests/test_delegation.py` +
`taskos/tests/e2e/test_tier2_delegation.py`, **adapted** to diecast's file-canonical
contract (`cast-delegation-contract.collab.md`) — not a port of taskos contracts that
have since drifted. Coverage parity is the floor; diecast-only behaviors
(`external_project_dir` 422 precondition, output-JSON contract v2 with US13 open-question
tags and US14 typed `next_steps`, mtime-heartbeat) are the additions.

The deliverable is a **single goal that ships both red tests AND the fixes that make
them green**, with each fix commit referencing the test it greens — turning the user's
"I feel it's breaking in quite a few ways" vibe into an enumerated list of resolved
regressions.

## User Stories

### US1 — T1 integration suite mirrors second-brain coverage on diecast contract (Priority: P1)

**As a** delegation-code maintainer, **I want to** run a fast integration suite that
exercises every test class second-brain's `test_delegation.py` had — adapted to diecast's
models, file-canonical contract, and naming, **so that** I get coverage parity with the
prior known-working baseline plus diecast-only contract checks.

**Independent test:** `pytest cast-server/tests/integration/test_child_delegation.py`
runs in <30s on a clean clone with `CAST_DISABLE_SERVER=1` and is green.

**Acceptance scenarios (EARS-style):**

- **Scenario 1:** WHEN a parent agent run with `allowed_delegations=[child]` calls
  `trigger_agent(child, ...)`, THE SYSTEM SHALL create a child run with
  `parent_run_id` linked, `status="pending"`, allowlist-validated, and depth ≤ MAX.
- **Scenario 2:** WHEN a parent calls `trigger_agent(other, ...)` where `other` is NOT
  in `allowed_delegations`, THE SYSTEM SHALL raise (or 422) before creating the run,
  with the message naming the disallowed target.
- **Scenario 3:** WHEN dispatch reaches depth 4 in a chain (`run0 → run1 → run2 → run3
  → run4`), THE SYSTEM SHALL refuse the 4th dispatch with a "max delegation depth" error.
- **Scenario 4:** WHEN `trigger_agent` is called with a `DelegationContext`, THE SYSTEM
  SHALL write `<goal_dir>/.delegation-<run_id>.json` containing `agent_name`,
  `parent_run_id`, `context.*`, `output.*` (verbatim from the model) BEFORE returning.
- **Scenario 5:** WHEN `_finalize_run_from_monitor` runs after a child completes, THE
  SYSTEM SHALL delete `.delegation-<run_id>.json`, `.agent-run_<run_id>.prompt`, and
  any `.continue` files for that run; `.agent-run_<run_id>.output.json` is retained.
- **Scenario 6:** WHEN a child's terminal `output.json` has a `summary` field longer
  than 300 chars, THE SYSTEM SHALL store `result_summary` truncated to exactly 300.
- **Scenario 7:** WHEN `_build_agent_prompt` is called with non-empty
  `allowed_delegations`, THE SYSTEM SHALL include the `CRITICAL`/no-inline block naming
  every target; with empty/None `allowed_delegations`, the block SHALL NOT be present.
- **Scenario 8:** WHEN `_build_agent_prompt` is called with `interactive=True`, THE
  SYSTEM SHALL include the `INTERACTIVE SESSION` block; with `interactive=False`, it
  SHALL NOT.
- **Scenario 9:** WHEN `_build_agent_prompt` is called for a parent whose
  `allowed_delegations` mix HTTP and subagent `dispatch_mode`, THE SYSTEM SHALL emit
  both the HTTP-dispatch and Subagent-dispatch blocks, scope each child to its own
  block (whole-word match), and emit the universal anti-inline rule **exactly once**
  across the preamble.
- **Scenario 10:** WHEN `continue_agent_run(run_id, message)` is called for an idle
  child, THE SYSTEM SHALL write `.agent-<run_id>.continue` with the message verbatim
  AND send a tmux instruction containing `Read <path>` (the message itself MUST NOT
  be pasted into the terminal). If the tmux session no longer exists, raise
  `ValueError` containing the phrase "no longer exists".

### US2 — Currently-broken behaviors flip from red to green inside this goal (Priority: P1)

**As a** delegation-code maintainer, **I want to** turn the user's "feels like it's
breaking in quite a few ways" vibe into a concrete enumerated list of regressions —
each represented by a failing test that flips green inside this goal — **so that**
the goal closes with a verifiable proof that delegation works again, and we have a
record of what was actually broken (vs. what we feared was broken).

**Independent test:** Goal entry commit contains ≥ 1 `xfail`-or-failing test for each
of the three observed symptom buckets (parent stall after child finalize; cleanup or
contract drift — orphan files / 422 shape / mixed-transport preamble malformed;
allowlist or depth or output-JSON contract violations passing silently). Goal exit
commit shows every one of those tests passing without `xfail`.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a child writes a valid contract-v2 `output.json` and the
  finalizer runs, THE SYSTEM SHALL transition the parent's polling loop to terminal
  within ≤ 1 polling-tick after the child's `mtime` update is observed (no stall).
- **Scenario 2:** WHEN finalization completes for any child run, THE SYSTEM SHALL
  leave NO orphan `.delegation-*.json`, `.prompt`, `.continue`, or `.tmp` files for
  that run in the goal directory.
- **Scenario 3:** WHEN cast-server receives `POST /api/agents/{name}/trigger` for a
  goal whose `external_project_dir` is unset OR set-to-nonexistent-path, THE SYSTEM
  SHALL respond 422 with body `{error_code: "missing_external_project_dir",
  goal_slug, configured_path, detail, hint}` exactly as specified in
  `cast-delegation-contract.collab.md` §"Dispatch Precondition".
- **Scenario 4:** WHEN a child writes a non-terminal status (`pending`, `running`,
  `idle`) into `output.json`, THE SYSTEM SHALL treat it as malformed and finalize
  the parent with `failed`+parse-error in `errors[]`.
- **Scenario 5:** WHEN a child writes a `next_steps` entry as a bare string instead
  of `{command, rationale, artifact_anchor}`, THE SYSTEM SHALL fail validation
  against `tests/fixtures/next_steps.schema.json` (US14 contract).
- **Scenario 6:** WHEN a child writes a trailing `Open Questions` section with an
  untagged item (no `[EXTERNAL]` or `[USER-DEFERRED]`), THE SYSTEM SHALL surface it
  as a contract violation per US13 close-out discipline.
- **Scenario 7:** WHEN dispatch chain reaches depth 4, THE SYSTEM SHALL 422 BEFORE
  the run row is created (asserted by no row appearing in `agent_runs` for the
  4th dispatch attempt).

### US3 — T2 live HTTP E2E asserts cast-server boundary contract nightly (Priority: P1)

**As a** delegation-code maintainer, **I want to** run a nightly live E2E that
spawns cast-server, dispatches `cast-test-parent-delegator → cast-test-child-worker`
via real HTTP, and asserts parent_run_id linkage + tmux session teardown + dispatch
precondition (422) + allowlist denial against the running server, **so that** drift
in the HTTP contract, ptyxis launch race, or atomic-write timing surfaces in CI
instead of in production runs.

**Independent test:** `pytest cast-server/tests/e2e/test_tier_delegation.py -m e2e`
on a host with cast-server bin available is green; the same suite is wired to a
nightly CI workflow.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `cast-test-parent-delegator` is triggered against a running
  cast-server with `external_project_dir` set, THE SYSTEM SHALL complete with status
  `completed`; ≥ 1 child run with `parent_run_id` set; child has non-empty
  `result_summary`; child's tmux session no longer exists (torn down).
- **Scenario 2:** WHEN `cast-test-delegation-denied` (whose `allowed_delegations`
  EXCLUDES the target it tries to dispatch) runs, THE SYSTEM SHALL complete the
  parent with no child rows AND `result_summary` containing "422" or "denied".
- **Scenario 3:** WHEN a parent dispatches a child and the test polls within 60s,
  THE SYSTEM SHALL show parent and child as separate tmux sessions (`agent-<parent>`,
  `agent-<child>`); parent has exactly 1 pane (not split). If the child completes
  too fast to verify mid-flight, the test `pytest.skip`s with that explanation
  (matching second-brain's pattern).
- **Scenario 4:** WHEN `POST /api/agents/{name}/trigger` is called against a goal
  with no `external_project_dir`, THE SYSTEM SHALL return 422 with the structured
  body from US2 Scenario 3.

### US4 — Subagent-mode covered: T1 builder unit + manual exercise checklist (Priority: P2)

**As a** delegation-code maintainer, **I want** preamble-builder coverage of
subagent-mode dispatch in T1 (no live Claude Code conversation) plus a manual
exercise checklist for live verification, **so that** subagent-mode regressions in
the prompt-shape/preamble-builder are caught automatically and live behavior is
documented for periodic manual confirmation.

**Independent test:** T1 mixed-transport preamble test passes (US1 Scenario 9);
checklist file `cast-server/tests/MANUAL_SUBAGENT_CHECKLIST.md` exists, lists ≤10
steps, and a maintainer following it on a clean machine reproduces a green result
in <5 min.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the checklist is followed end-to-end, THE SYSTEM SHALL
  guide the maintainer through: dispatch a subagent-mode child via Claude Code's
  Agent tool, verify the verdict is surfaced as-is (not summarized), confirm no
  `agent_runs` row is created (subagent-mode bypasses the run queue per
  `taskos_agent_delegation.collab.md` §Subagent Dispatch), and confirm the
  parent's preamble named the target in the Subagent block.
- **Scenario 2:** WHEN `_build_agent_prompt` is called with
  `allowed_delegations=[subagent_only_target]` and that target's `dispatch_mode
  == "subagent"`, THE SYSTEM SHALL emit ONLY the Subagent-dispatch block (no
  HTTP block), include the structured-return / no-summarize contract, and not
  emit the curl/poll quick reference.

### US5 — Test fixture agents are first-class and isolated from UI test fixtures (Priority: P2)

**As a** delegation-code maintainer, **I want** `cast-test-parent-delegator`,
`cast-test-child-worker`, `cast-test-child-worker-subagent`, and
`cast-test-delegation-denied` to live in a dedicated fixture-agents directory
(separate from `cast-server/tests/ui/agents/`), **so that** they are discoverable
as delegation-test fixtures (not UI fixtures), don't pollute `agents/` namespace,
and can be loaded by both T1 (via direct config injection) and T2 (via the running
cast-server's agent registry).

**Independent test:** Fixture agents load via `load_agent_config(<fixture-name>)`
under both T1 and T2; their `config.yaml` declares `model: haiku` and
`allowed_delegations` as appropriate for each fixture's role.

**Acceptance scenarios:**

- **Scenario 1:** WHEN T2 starts cast-server, THE SYSTEM SHALL register the
  fixture agents from the dedicated fixture directory, callable via
  `POST /api/agents/{fixture-name}/trigger`.
- **Scenario 2:** WHEN T1 patches `load_agent_config`, THE SYSTEM SHALL accept
  the fixture configs without touching the live agent registry.
- **Scenario 3:** WHEN `cast-test-parent-delegator` dispatches
  `cast-test-child-worker`, THE SYSTEM SHALL produce a parent run + child run
  pair where both `model == "haiku"` (cheap/fast).

### US6 — Suite respects diecast's env-var test hooks for deterministic timing (Priority: P3)

**As a** CI runner, **I want** the suite to honor `CAST_DELEGATION_BACKOFF_OVERRIDE`
and `CAST_DELEGATION_IDLE_TIMEOUT_SECONDS` and `CAST_DISABLE_SERVER`, **so that**
T1 runs sub-second per polling-loop case without sleeping for production cadence.

**Independent test:** Setting `CAST_DELEGATION_BACKOFF_OVERRIDE=10ms,20ms,50ms` and
`CAST_DELEGATION_IDLE_TIMEOUT_SECONDS=4` makes a polling-loop case complete in <1s.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `CAST_DELEGATION_BACKOFF_OVERRIDE` is set with `ms`/`s`
  suffixes, THE SYSTEM SHALL parse and use the CSV ladder, replacing the default
  `1, 2, 5, 10, 30` schedule.
- **Scenario 2:** WHEN `CAST_DISABLE_SERVER=1`, THE SYSTEM SHALL skip HTTP API
  attempts and drive parent state from the file alone.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | T1 suite ports the second-brain `test_delegation.py` test classes — adapted to diecast names — covering: allowlist validation, depth enforcement, depth calculation, delegation-context file write + JSON shape + cleanup, result_summary populate/None/truncate, child-launch isolation (own session), terminal title formatting (`[Child]` / `[Diecast]` / 80-char truncation), continuation file delivery, prompt+delegation file cleanup on finalize, no-inline preamble injection, delegation-instruction-in-prompt, interactive prompt block, mixed-transport preamble harness | Equivalence map to second-brain test classes lives in the test module's docstring. |
| FR-002 | T1 suite adds diecast-only coverage: `external_project_dir` 422 precondition (server-side at trigger AND launcher re-validate), output-JSON contract v2 conformance (terminal-status set, US14 typed `next_steps` shape, US13 open-question tag enforcement), file-canonical heartbeat-by-mtime under parent→child round-trip | Compose B5 primitives in feature scope; do NOT re-test the primitives themselves. |
| FR-003 | T1 suite runs in <30s with real DB + real filesystem + mocked tmux/launcher; runs under `CAST_DISABLE_SERVER=1` | Tier wall-clock target validated by CI duration tracking, not just per-test timeout. |
| FR-004 | T2 nightly E2E uses fixture agents `cast-test-parent-delegator`, `cast-test-child-worker`, `cast-test-child-worker-subagent`, `cast-test-delegation-denied`; spawns cast-server; dispatches via real HTTP; asserts parent_run_id linkage in DB and tmux session teardown | Wired to a nightly CI workflow. PR CI runs T1 only. |
| FR-005 | Subagent-mode coverage: T1 unit-tests on `_build_agent_prompt` for subagent-only and mixed allowed_delegations; live exercise documented as `cast-server/tests/MANUAL_SUBAGENT_CHECKLIST.md` | Matches second-brain's "covered manually in sp11" decision; auto-harness is OUT OF SCOPE. |
| FR-006 | Each fix commit references the failing test it greens; goal does not move to `accepted` until every test the goal added is green | Use commit-message convention `fix(delegation): green <test_name>`. |
| FR-007 | Test module docstrings include the equivalence map: each diecast test names its second-brain counterpart class for reviewer traceability | Reduces review cost; one-time write, persistent value. |
| FR-008 | No test imports `requests` / `httpx` / `urllib` from a Python implementation; bash-based curl is permitted only as a best-effort dispatch primitive | Same rule the SKILL.md already enforces — extended to test code. |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | T1 integration suite green on a clean clone | `pytest cast-server/tests/integration/test_child_delegation.py` exits 0 in <30s in CI |
| SC-002 | T2 nightly E2E green | Nightly CI workflow shows green for ≥3 consecutive runs after goal closes |
| SC-003 | Each of the three observed symptom buckets has ≥1 dedicated red-then-green commit | `git log --grep "fix(delegation): green"` shows ≥3 commits, each naming a distinct symptom-bucket test |
| SC-004 | Mixed-transport preamble test asserts: both blocks emit, anti-inline appears exactly once (`out.count("NEVER inline") == 1` or diecast equivalent), child names whole-word-scoped to their block | Test code uses regex `\b<name>\b` for scoping (matches second-brain pattern verbatim) |
| SC-005 | Manual subagent-mode checklist exists and reproduces in <5 min | A maintainer NOT involved in writing the checklist follows it cold and confirms green; recorded in checklist's "verified by" footer |
| SC-006 | Fixture agents load via both T1 (mocked) and T2 (live) without modification | A single `config.yaml` per fixture serves both tiers; T1 patches `load_agent_config`, T2 reads from disk via the running server |
| SC-007 | Coverage parity with second-brain: every test class in `taskos/tests/test_delegation.py` has a counterpart in diecast OR is justified-as-skipped in the test module's equivalence-map docstring | Manual cross-check during PR review; equivalence map enforced by reviewer |

## Constraints

- **File-canonical contract.** No test imports `requests`/`httpx`/`urllib` from Python.
  cast-server is read-through — tests assert against the file on disk, not HTTP responses,
  except in T2 where HTTP IS the boundary under test.
- **CI runtime budgets.** T1 wall-clock <30s on the integration suite as a whole; T2
  nightly only.
- **Fixture model.** Every fixture agent uses `model: haiku` for fast/cheap runs; explicit
  per-fixture `dispatch_mode` declared (no implicit default reliance).
- **Env-var hygiene.** T1 runs under `CAST_DISABLE_SERVER=1` + `CAST_DELEGATION_BACKOFF_OVERRIDE=10ms,20ms,50ms`
  + `CAST_DELEGATION_IDLE_TIMEOUT_SECONDS=4` for deterministic timing. T2 runs without
  these overrides (production cadence).
- **Test data isolation.** T1 uses `tmp_path`-scoped goal directories; T2 uses a
  dedicated `child-delegation-e2e` test goal that the suite tears down after each run.
- **No new transports.** Only HTTP and subagent dispatch are in scope. New transports
  (e.g., websocket, gRPC) are explicitly out of scope.

## Out of Scope

- **Automated subagent live E2E.** Intrinsically requires a Claude Code conversation;
  manual checklist is the contract.
- **Refactoring delegation transport** beyond what is needed to make tests pass. If a
  test reveals a deeper architectural issue, file a separate goal — do not expand
  this one.
- **B5 / B3 / B4 primitive coverage.** Already exercised by `tests/test_b5_*.py`,
  `tests/test_b3_*.py`, `tests/test_b4_*.py`. Integration tests **compose** these
  primitives at the parent→child round-trip level; they do NOT re-implement primitive
  cases.
- **Performance / load testing.** Concurrent dispatch under load, latency percentiles,
  throughput. Test density mirrors second-brain (4 dedicated tests per state-machine
  branch — happy / idle-timeout / heartbeat / atomic-write — not stress).
- **`/invoke` route delegation precondition.** `cast-delegation-contract.collab.md`
  explicitly carves out `/invoke` from `external_project_dir` enforcement; this goal
  honors that carve-out.
- **Cleanup of orphan `.tmp` files from crashed children.** Spec-deferred to a future
  `sp-cleanup`; not a delegation-integration concern.
- **Cross-RUN_ID write protection at the OS level.** Spec mandates the discipline;
  proving it OS-side is server-side enforcement work, not integration-test work.

## Open Questions

- **[NEEDS CLARIFICATION: fixture-agent location]** — the fixture agents
  (`cast-test-parent-delegator`, `cast-test-child-worker`,
  `cast-test-child-worker-subagent`, `cast-test-delegation-denied`) need a home. Recommended:
  `cast-server/tests/integration/agents/<name>/config.yaml` (separate from the existing
  `cast-server/tests/ui/agents/` family which is UI-only and dispatches nothing). Resolve
  before fixture-creation phase. Resolution path: short discussion at plan time, not a
  blocker for refining requirements. Reason: design choice with two reasonable options;
  matches `[USER-DEFERRED]` semantics if the user explicitly punts at planning.
- **[NEEDS CLARIFICATION: T2 ptyxis dependency in headless CI]** — T2 launches ptyxis
  windows for parent/child terminals. Headless CI runners typically lack ptyxis.
  Options: (a) skip T2 in PR CI, run on a self-hosted nightly runner with ptyxis;
  (b) wrap T2 invocations in `xvfb-run` + a no-ptyxis fallback path; (c) make T2
  graceful-degrade when ptyxis is missing (assert filesystem + DB but skip terminal
  visibility checks). Recommended: (a). Resolve before T2 implementation phase.
  Reason: depends on CI infra availability — `[EXTERNAL]` until the CI strategy is
  decided with the maintainer.

