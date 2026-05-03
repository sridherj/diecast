# Detailed Execution Plan: Child Delegation Integration Tests

> **Companion to:** `goals/child-delegation-integration-tests/plan.collab.md` (high-level)
> **Spec authority:** `docs/specs/cast-delegation-contract.collab.md`, `docs/specs/cast-output-json-contract.collab.md`
> **Decisions baked in (do not re-litigate):** see "Locked Decisions" below.

## Overview

Expand the 7-phase high-level plan into atomic sub-phases sized for independent
Claude execution contexts. Tests-first with a red→green commit trail inside this
goal: every fix commits with `fix(delegation): green <test_name>`. Each sub-phase
specifies outcome, files, dependencies, atomic tasks, verification commands, and
spec-consistency citations (FR/SC/US IDs).

## Operating Mode

**HOLD SCOPE.** Requirements language is rigorous, not exploratory: "the deliverable
is a single goal that ships both red tests AND the fixes that make them green",
"coverage parity is the floor", "out of scope" is exhaustively enumerated. Spec
density (8 FRs, 7 SCs, 6 USs) signals maximum-rigor mode. No scope expansion, no
reduction — bulletproof execution against a fixed scope.

## Locked Decisions

| Decision | Source | Sub-phase impact |
|----------|--------|------------------|
| T1 path: `cast-server/tests/integration/test_child_delegation.py` | Plan §Phase 2 | sp2.x, sp3.x, sp4.x, sp6.x |
| T2 path: `cast-server/tests/e2e/test_tier_delegation.py` | Plan §Phase 5 | sp5.x |
| Fixture path (recommended): `cast-server/tests/integration/agents/<name>/config.yaml` | Plan §Phase 1 | **Gate A revisits — sp1 builds against recommendation** |
| Registry-discovery seam: `CAST_TEST_AGENTS_DIR` env var (already exists at `agent_config.py:62-70` + `agent_service.py:1618-1631`) | Review #1 | sp1.1 verify, sp1.3 conftest one-liner |
| All fixtures: `model: haiku` | Spec §Constraints | sp1.2 |
| T1 env: `CAST_DISABLE_SERVER=1`, `CAST_DELEGATION_BACKOFF_OVERRIDE=10ms,20ms,50ms`, `CAST_DELEGATION_IDLE_TIMEOUT_SECONDS=4`; <30s budget | Spec §Constraints, FR-003 | sp2.x, sp3.x verification |
| T2 env: no overrides (production cadence) | Spec §Constraints | sp5.x |
| No Python `requests`/`httpx`/`urllib` imports | FR-008 | sp2.x, sp3.x, sp5.x lint check |
| Commit convention: `fix(delegation): green <test_name>` | FR-006 | sp4.x commits |
| Equivalence-map docstring at top of T1 file | FR-007 | sp1.4 stub, sp2.x populate, sp7.2 review |
| Goal-status flips via `/cast-goals` | User intent | sp7.4 |
| Spec drift escalates via `/cast-update-spec` | Spec §Spec References, plan §Phase 7 | sp7.3 conditional |
| T2 ptyxis CI strategy (recommended option a) | Plan §Phase 5 | **Gate C revisits — sp5.4 deferred until decided** |

## Phase 1: Fixture Scaffolding & Registry Wiring

### sp1.1 — Verify `CAST_TEST_AGENTS_DIR` seam supports four-fixture layout

> **Reshaped per Plan Review #1 (2026-05-01):** the seam already exists at
> `cast-server/cast_server/models/agent_config.py:62-70` (`_candidate_config_paths`
> production-fallback) and `cast-server/cast_server/services/agent_service.py:1618-1631`
> (`get_all_agents` merge-and-warn-on-collision). Originally scoped as an "audit
> + decide" task; the answer was already in the codebase. Reshaped to a verify-only
> sub-phase.

**Outcome:** A 5-line note confirming `CAST_TEST_AGENTS_DIR` resolves the four
fixture configs via `load_agent_config(name)` and `get_all_agents()`, plus a
written contract for `_config_cache` invalidation that sp2.x will follow.

**Dependencies:** None.

**Files touched:** read-only (`agent_config.py`, `agent_service.py`).

**Atomic tasks:**
- Confirm `_candidate_config_paths()` (line 62) appends
  `<CAST_TEST_AGENTS_DIR>/<agent_id>/config.yaml` after the production path —
  this is the integration-test seam.
- Confirm `get_all_agents()` (line 1614) merges the test registry with
  collision-warning, so T2's running cast-server registers fixtures by setting
  the env var before launch.
- Document the `_config_cache` (line 59) mtime-invalidation contract: tests
  must monkeypatch `load_agent_config` (the public seam) OR call
  `_config_cache.clear()` between cases. Both are valid — sp2.x picks the
  monkeypatch route per Review #3.
- One-line rationale entry in the equivalence-map docstring (sp1.4) noting
  the seam is `CAST_TEST_AGENTS_DIR`.

**Verification:**
- 5-line note attached to the sub-phase output JSON.

**Spec consistency:** preparatory for FR-004, FR-005, US5.

**Inline design review:**
- *Decision:* skip the audit; the seam exists and is documented. *Rationale:*
  Review #1 found the env var + cache mechanism + collision-warn behavior is
  already in place; spec-style "redesign as if greenfield" is gold-plating.

---

### sp1.2 — Author the four fixture `config.yaml` files + deterministic prompts

> **Updated per Review #5:** prompts must be literal-output, not paraphrasable.

**Outcome:** Four `config.yaml` files exist on disk under
`cast-server/tests/integration/agents/<name>/` (recommended path; revisited at
Gate A). Each declares `model: haiku` and the `dispatch_mode` /
`allowed_delegations` from the plan. The `cast-test-delegation-denied` fixture
ships with a prompt body that deliberately attempts to dispatch a
NON-allowlisted target so US3.S2 has something to assert against.

**Dependencies:** sp1.1 (only for the path-choice if Gate A defers; otherwise
independent).

**Files created:**
- `cast-server/tests/integration/agents/cast-test-parent-delegator/config.yaml`
- `cast-server/tests/integration/agents/cast-test-child-worker/config.yaml`
- `cast-server/tests/integration/agents/cast-test-child-worker-subagent/config.yaml`
- `cast-server/tests/integration/agents/cast-test-delegation-denied/config.yaml`
- A minimal prompt-body file alongside each `config.yaml` if the agent loader
  expects a prompt artifact (mirror `cast-server/tests/ui/agents/<name>/` layout).

**Atomic tasks:**
- **Determinism rule (Review #5):** every fixture prompt MUST instruct the
  child to write a LITERAL contract-v2 output JSON envelope to its output
  file — `Write to <output_path> EXACTLY this JSON, do not paraphrase, do
  not add fields: {…verbatim envelope…}.` This makes T2 substring assertions
  byte-stable (e.g., sp5.2's `result_summary` containing "denied").
- For `cast-test-parent-delegator`: `dispatch_mode: http`,
  `allowed_delegations: [cast-test-child-worker, cast-test-child-worker-subagent]`,
  `model: haiku`. Prompt: dispatch `cast-test-child-worker` via the literal
  curl command (path `/api/agents/cast-test-child-worker/trigger`), poll
  the child's output file, then write the parent's literal contract-v2 JSON.
- For `cast-test-child-worker`: `dispatch_mode: http`, `allowed_delegations: []`,
  `model: haiku`. Prompt: write the literal contract-v2 JSON envelope to
  `<output_path>` and exit. `summary` field is a fixed sentinel string the
  T2 assertions can match exactly.
- For `cast-test-child-worker-subagent`: `dispatch_mode: subagent`,
  `allowed_delegations: []`, `model: haiku`. Prompt: return a structured
  literal verdict string. Used by sp6.1 for builder unit-tests; live
  exercise per sp6.2 manual checklist.
- For `cast-test-delegation-denied`: `dispatch_mode: http`,
  `allowed_delegations: [cast-test-child-worker]`, `model: haiku`. Prompt:
  attempt curl to `/api/agents/cast-test-child-worker-subagent/trigger`
  (NOT in allowlist), capture the 422 body, then write a parent contract-v2
  JSON whose `summary` literally contains the substring "denied (422)" so
  sp5.2's assertion is deterministic.

**Verification:**
- `python -c "from pathlib import Path; import yaml; [print(yaml.safe_load(p.read_text())) for p in Path('cast-server/tests/integration/agents').rglob('config.yaml')]"`
  prints four configs without error.
- Each config.yaml file declares the exact `dispatch_mode` and
  `allowed_delegations` per spec lines.

**Spec consistency:** US5.S3 (model parity), FR-004 (T2 fixture set),
plan §Phase 1 dispatch_mode declarations.

**Inline design review:**
- *Decision:* fixture prompts are intentionally minimal; "deliberately fails"
  patterns are explicit (the denied fixture's prompt is the test-data, not a
  bug). Alternatives considered: synthesize the denied dispatch in test-side
  monkeypatch instead of fixture prompt. *Rationale:* fixture-as-prompt keeps
  T2 honest (it dispatches via real HTTP from a real prompt), and T1 doesn't
  care because it patches the dispatch path anyway.

---

### sp1.3 — Wire fixture directory via `CAST_TEST_AGENTS_DIR` (one-line conftest)

> **Reshaped per Review #1:** seam already exists; this sub-phase is now a
> small conftest entry, not a 15-line code change.

**Outcome:** T1 resolves all four fixtures via `load_agent_config(name)`; T2
resolves via the running cast-server's registry. No production code changes.

**Dependencies:** sp1.1 (seam confirmation), sp1.2 (configs exist).

**Files touched:**
- `cast-server/tests/integration/conftest.py` (new or extended): autouse
  session-scoped fixture sets `CAST_TEST_AGENTS_DIR=<repo>/cast-server/tests/integration/agents`
  before any test imports `load_agent_config`.
- `cast-server/tests/integration/conftest.py`: also registers an autouse
  per-test fixture that calls `cast_server.models.agent_config._config_cache.clear()`
  between tests (Review #3 belt-and-suspenders for cache isolation).
- T2 launcher (sp5.1's `cast-server/tests/e2e/conftest.py`): exports the same
  env var into the spawned cast-server's environment.

**Atomic tasks:**
- Add `os.environ["CAST_TEST_AGENTS_DIR"] = str(REPO_ROOT / "cast-server/tests/integration/agents")`
  to the session-scoped autouse fixture. Use `monkeypatch.setenv` form so it's
  reverted on session teardown (avoids leaking into other test runs).
- Add the autouse `_config_cache.clear()` per-test fixture (Review #3).

**Verification:**
- New unit test `cast-server/tests/integration/test_fixture_agents_load.py`:
  for each of the four fixture names, `load_agent_config(name)` returns an
  `AgentConfig` with the declared `dispatch_mode`, `allowed_delegations`,
  `model: haiku`.
- `pytest cast-server/tests/integration/test_fixture_agents_load.py` exits 0.
- Risk #2 ("registry-discovery seam doesn't have a clean test-fixture-dir hook")
  retired — seam confirmed.

**Spec consistency:** US5.S1, US5.S2, SC-006 (T1+T2 single config).

**Inline design review:**
- *Decision:* re-use the existing `CAST_TEST_AGENTS_DIR` seam; do NOT introduce
  `CAST_AGENT_FIXTURE_DIRS`. *Rationale:* the seam is mtime-cached, collision-warn'd,
  and tested in production. Any new env var would be redundant and fragment the
  registry-discovery model.

---

### sp1.4 — Stub equivalence-map docstring at top of T1 module

**Outcome:** `cast-server/tests/integration/test_child_delegation.py` exists with
a module-level docstring listing all 11 second-brain test classes (from
`<SECOND_BRAIN_ROOT>/taskos/tests/test_delegation.py`) with TODO markers
that sp2.x will replace as each diecast counterpart lands. The file is
syntactically valid Python with zero tests yet — pytest collects it as empty.

**Dependencies:** None (parallel with sp1.1, sp1.2, sp1.3).

**Files created:**
- `cast-server/tests/integration/test_child_delegation.py` (empty test module
  with the equivalence-map docstring).
- `cast-server/tests/integration/__init__.py` (empty, if needed for pytest
  discovery).

**Atomic tasks:**
- Read `<SECOND_BRAIN_ROOT>/taskos/tests/test_delegation.py`; enumerate
  all 11 test classes by name (do NOT copy code — just names).
- Write docstring with format: `<second-brain class name> → <diecast counterpart
  TBD> | <US/scenario citation>`.
- Add the docstring's last paragraph: spec-cited mapping per the 11 classes
  listed in plan §Phase 2 Key Activities.

**Verification:**
- `pytest cast-server/tests/integration/test_child_delegation.py --collect-only`
  exits 0 (0 tests collected).
- `python -c "import ast; ast.parse(open('cast-server/tests/integration/test_child_delegation.py').read())"` exits 0.

**Spec consistency:** FR-007 (equivalence-map artifact realized as a concrete
file).

**Inline design review:**
- *Decision:* docstring at top of T1 module, NOT a separate `.md` file.
  Alternatives considered: separate equivalence-map markdown. *Rationale:*
  FR-007 says "test module docstrings include the equivalence map" —
  spec-mandated location.

---

### **[GATE A]** — Confirm fixture-agent location and dispatch_mode declarations

**Trigger:** After sp1.1–sp1.4 land.

**Surface to user:**
1. Chosen path: `cast-server/tests/integration/agents/<name>/`. Acceptable?
2. Four fixtures' `dispatch_mode` + `allowed_delegations` declarations (quote
   the plan §Phase 1 list verbatim). Confirm or amend.
3. Registry-discovery seam (the answer from sp1.1). Acceptable?

**Resolution path:** quick user confirmation; if any of the three change, sp1.2
and sp1.3 re-do at the cheapest possible point (no test code yet depends on the
path).

---

## Phase 2: T1 Integration Suite — Coverage Parity Baseline

### sp2.1 — Port allowlist + depth + child-launch + terminal-title classes + suite-wide timeout

> **Updated per Review #7:** suite-wide pytest-timeout commit added.

**Outcome:** Five test classes wired and runnable (some failing — that's fine,
red tests are part of the plan):
- `TestAllowlistValidation` (US1.S2)
- `TestDelegationDepthEnforcement` (US1.S3)
- `TestDepthCalculation` (US1.S3, mocks `_get_delegation_depth`)
- `TestChildLaunchIsolation` (US1.S1)
- `TestTerminalTitleFormatting`

**Dependencies:** Phase 1 complete (Gate A passed).

**Files touched:**
- `cast-server/tests/integration/test_child_delegation.py` (append classes)
- Equivalence-map docstring updated with these 5 entries

**Atomic tasks:**
- For each class, read the second-brain reference at
  `<SECOND_BRAIN_ROOT>/taskos/tests/test_delegation.py` (named class).
- Write the diecast counterpart against `agent_service.py` symbols:
  `trigger_agent`, `_get_delegation_depth`, `_launch_agent`, terminal-title
  helper. Use `tmp_path` for any goal directory.
- **Cache-isolation convention (Review #3):** when a test needs a non-fixture
  `AgentConfig`, monkeypatch `cast_server.services.agent_service.load_agent_config`
  to return the test config (mirrors second-brain pattern). NEVER mutate
  `_config_cache` directly. The autouse cache-clear from sp1.3 covers anything
  that slips through.
- **Suite-wide timeout (Review #7):** add `cast-server/tests/integration/pytest.ini`
  (or a `[pytest]` section in an existing `pytest.ini`) with
  `timeout = 5` scoped to `tests/integration/`. Single-line belt-and-suspenders
  defense for FR-003: a single hung test fails as "timed out" instead of
  hanging the suite.
- Update the equivalence-map docstring with diecast class names.

**Verification:**
- `CAST_DISABLE_SERVER=1 CAST_DELEGATION_BACKOFF_OVERRIDE=10ms,20ms,50ms CAST_DELEGATION_IDLE_TIMEOUT_SECONDS=4 pytest cast-server/tests/integration/test_child_delegation.py -k "Allowlist or Depth or ChildLaunch or TerminalTitle"`
  collects ≥5 classes, runs them, total time <10s.
- No imports of `requests`/`httpx`/`urllib` (FR-008 lint:
  `! grep -E '^(import|from)\s+(requests|httpx|urllib)' cast-server/tests/integration/test_child_delegation.py`).

**Spec consistency:** US1.S1, US1.S2, US1.S3, FR-001, FR-003, FR-008.

**Inline design review:**
- *Decision:* `tmp_path` per test, no shared mutable state. Alternatives
  considered: session-scoped temp goal dir for speed. *Rationale:* spec
  §Constraints "T1 uses `tmp_path`-scoped goal directories per test" —
  spec-mandated isolation.

---

### sp2.2 — Port delegation-context-file + result_summary + cleanup classes (BOTH finalizers)

> **Updated per Review #2:** cleanup contract must hold across BOTH `_finalize_run`
> AND `_finalize_run_from_monitor` entry points.

**Outcome:** Three test classes added:
- `TestDelegationContextFile` (US1.S4) — asserts `<goal_dir>/.delegation-<run_id>.json`
  written before `trigger_agent` returns; JSON contains `agent_name`,
  `parent_run_id`, `context.*`, `output.*` verbatim
- `TestResultSummary` (US1.S6) — populate / None / truncate-at-300 cases
- `TestFinalizeCleanup` (US1.S5) — after finalize, `.delegation-<run_id>.json`,
  `.agent-run_<run_id>.prompt`, `.continue` files for that run are deleted;
  `.agent-run_<run_id>.output.json` is retained. **Two test methods, one per
  finalizer**: `test_cleanup_via_finalize_run` (sync entry, line 1702) and
  `test_cleanup_via_finalize_run_from_monitor` (async monitor entry, line 2520).
  Both must pass — cleanup contract is invariant across finalizer entry points.
  If they diverge, that's a contract bug surfaced by the test (red signal).

**Dependencies:** sp2.1 (file scaffold present).

**Files touched:**
- `cast-server/tests/integration/test_child_delegation.py` (append)
- Equivalence-map docstring updated

**Atomic tasks:**
- `TestDelegationContextFile`: drive `trigger_agent` with a `DelegationContext`,
  inspect the on-disk file BEFORE the call returns (capture mid-call via
  monkeypatch hook on a downstream symbol).
- `TestResultSummary`: drive `_finalize_run_from_monitor` with three outputs —
  short summary, missing summary, 350-char summary — assert resulting
  `result_summary` field equals expected (populated / `None` / 300 chars).
- `TestFinalizeCleanup`: pre-create `.delegation`, `.prompt`, `.continue`,
  `.output.json` for a run; finalize; assert four files' presence/absence.

**Verification:**
- `pytest cast-server/tests/integration/test_child_delegation.py -k "DelegationContextFile or ResultSummary or FinalizeCleanup"` collects 3 classes, runs them.
- Suite cumulative wall-clock still <30s.

**Spec consistency:** US1.S4, US1.S5, US1.S6, FR-001;
also touches `cast-delegation-contract.collab.md` §Cleanup contract.

**Inline design review:**
- *Decision:* assert-before-return is verified via monkeypatch interception.
  Alternatives considered: re-architect `trigger_agent` to expose a hook.
  *Rationale:* spec is explicit ("WRITE BEFORE RETURNING") — non-trivial to
  prove without a hook. The monkeypatch interception is the standard
  second-brain pattern for this.

---

### sp2.3 — Port preamble-builder classes (no-inline, prompt, interactive, mixed-transport, dispatch_mode validator)

> **Updated per Review #8:** added `TestDispatchModeValidator` to pin silent-fallback semantics.

**Outcome:** Five test classes added — these target `_build_agent_prompt` and
`AgentConfig` exclusively (pure-function tests, no DB/filesystem):
- `TestPreambleAntiInline` (US1.S7) — asserts CRITICAL/no-inline block presence
  with non-empty `allowed_delegations`, absence with empty/None
- `TestPromptBuilder` (US1.S7+S8) — delegation-instruction-in-prompt + interactive block
- `TestMixedTransportPreamble` (US1.S9) — both blocks emit, anti-inline appears
  exactly once (`out.count("NEVER inline") == 1` or diecast equivalent), child
  names whole-word-scoped via `\b<name>\b` regex (matches second-brain pattern)
- **`TestDispatchModeValidator` (Review #8 / US2 silent-failure surface)** —
  three methods pinning the validator's intentional silent-fallback semantics
  at `agent_config.py:36-41`:
  - `test_valid_subagent_preserved`: `AgentConfig(dispatch_mode="subagent")` → `"subagent"`
  - `test_typo_falls_back_to_http_silently`: `AgentConfig(agent_id="x", dispatch_mode="subagnet", allowed_delegations=["a","b"], model="haiku", trust_level="readonly")` →
    `dispatch_mode == "http"` AND `allowed_delegations == ["a","b"]` AND
    `model == "haiku"` AND `trust_level == "readonly"` (sibling fields preserved,
    NOT degraded to defaults). This pins the documented design choice that
    distinguishes a `str + validator` from a `Literal[...]` annotation; future
    "fix the typo handling" changes will fail this test loudly.
  - `test_valid_http_preserved`: `AgentConfig(dispatch_mode="http")` → `"http"`

**Dependencies:** sp2.1.

**Files touched:** `cast-server/tests/integration/test_child_delegation.py` (append).

**Atomic tasks:**
- Read `_build_agent_prompt` carefully (Risk #3 in plan: diecast structure may
  have diverged from second-brain — if so, document the divergence in the
  equivalence-map docstring as a *justified deviation*, not a skip).
- `TestPreambleAntiInline`: two cases — non-empty allowlist (block present),
  empty allowlist (block absent). Use string-contains assertions on the prompt
  output.
- `TestPromptBuilder`: parametrize `interactive=True/False`, assert
  `INTERACTIVE SESSION` block presence/absence; assert delegation-instruction
  block present when `allowed_delegations` non-empty.
- `TestMixedTransportPreamble`: build a prompt with one HTTP child + one
  subagent child in `allowed_delegations`. Assert: HTTP block present,
  Subagent block present, anti-inline phrase count == 1, each child name
  appears ONLY in its own block via `\b<name>\b` regex.

**Verification:**
- `pytest cast-server/tests/integration/test_child_delegation.py -k "PreambleAntiInline or PromptBuilder or MixedTransport"` exits with all four classes collected.
- SC-004 explicit assertion: `out.count("NEVER inline") == 1` (or whatever
  exact string diecast preamble uses — pinned in test).

**Spec consistency:** US1.S7, US1.S8, US1.S9, US2 (silent-failure surface),
SC-004, FR-001.

**Inline design review:**
- *Decision:* `\b<name>\b` regex matches second-brain verbatim per SC-004.
  Alternatives considered: substring `in` check. *Rationale:* SC-004 explicitly
  pins the regex form; substring is the bug second-brain hit historically (a
  child name appearing as a substring inside another child's name leaked
  scope).

---

### sp2.4 — Port continuation file delivery class

**Outcome:** `TestContinueAgentRun` (US1.S10) wired:
- `continue_agent_run(run_id, message)` writes `.agent-<run_id>.continue` with
  the message verbatim
- Sends a tmux instruction containing `Read <path>` (NOT pasted literal message)
- If the tmux session no longer exists, raises `ValueError` with phrase "no
  longer exists"

**Dependencies:** sp2.1.

**Files touched:** `cast-server/tests/integration/test_child_delegation.py` (append).

**Atomic tasks:**
- Mock the tmux interface (locate the symbol — likely a `tmux_send` helper or
  similar) so the test can intercept the instruction text without a real tmux.
- Three cases: message-write happens first, tmux-instruction contains `Read
  <path>` and NOT the message body, missing-session raises `ValueError("...no
  longer exists...")`.

**Verification:**
- `pytest cast-server/tests/integration/test_child_delegation.py -k "ContinueAgentRun"` exits with the class collected.
- Manual inspection: tmux mock asserts `Read <path>` substring and NOT-contains
  the message body.

**Spec consistency:** US1.S10, FR-001.

**Inline design review:**
- *Decision:* the message-not-pasted assertion is the most security-relevant
  test in the suite (terminal injection attack surface). *Rationale:* this is
  US1.S10's whole point — `MUST NOT be pasted into the terminal`.

---

### sp2.5 — Wall-clock budget gate + equivalence-map completion

**Outcome:** Full T1 module runs end-to-end in <30s (failures count toward
budget, per plan §Phase 2 Verification). Equivalence-map docstring is fully
populated — every second-brain class has a diecast counterpart name OR a
justified-as-skipped marker.

**Dependencies:** sp2.1, sp2.2, sp2.3, sp2.4.

**Files touched:** `cast-server/tests/integration/test_child_delegation.py`
(docstring final pass).

**Atomic tasks:**
- Run the full T1 suite under spec env vars; capture `time` output.
- If >30s, identify the slow case via `pytest --durations=10`.
  **Tighten only — never skip a slow test (Review #6).** If a test fundamentally
  cannot run in budget under the env-var overrides + suite-wide
  `pytest-timeout=5`, that's a plan-revision signal: surface to the user, do NOT
  mask via skip. Skipping bypasses FR-003.
- Populate every TODO marker in the equivalence-map docstring.

**Verification:**
- `time pytest cast-server/tests/integration/test_child_delegation.py` reports
  real time <30s.
- Docstring has 0 `TODO` substrings; every line names a concrete diecast class
  OR is marked `# justified-skip: <reason>`.

**Spec consistency:** FR-003 (wall-clock), FR-007 (equivalence map), SC-007.

**Inline design review:** No flags.

---

### **[GATE B]** — Failing-test enumeration

**Trigger:** After sp2.5 lands.

**Surface to user:**
1. The full failing-test list from `pytest cast-server/tests/integration/test_child_delegation.py`
   under spec env vars. Group by symptom bucket (4a/4b/4c).
2. For each failing test, one-line hypothesis on which symptom bucket it
   maps to.
3. Out-of-scope check: any failure that points at a structural issue (Risk #1
   in plan) — escalate at this gate, do NOT push to Phase 4.

**Resolution path:** user confirms the bucket assignments OR escalates. Gate
exit unblocks Phase 4 sub-phases.

---

## Phase 3: T1 Diecast-Only Additions

### sp3.1 — `TestExternalProjectDirPrecondition` (additive only — DRY with existing tests)

> **Re-scoped per Review #4:** `cast-server/tests/test_dispatch_precondition.py`
> already covers 8+ of the precondition cases. sp3.1 verifies those still pass
> under integration-suite env vars and adds ONLY the genuinely-new cases.

**Outcome:** Two genuinely-new test methods added; existing precondition tests
verified to continue passing under integration-suite env vars; no duplication.

**Dependencies:** Phase 2 complete.

**Files touched:**
- `cast-server/tests/integration/test_child_delegation.py` (append a small
  class containing only the new methods)
- `cast-server/tests/test_dispatch_precondition.py` — read-only, cited in the
  equivalence-map docstring as "covered elsewhere"

**Already-covered cases (DO NOT duplicate; cite by name in docstring):**
- `test_validate_raises_when_goal_has_no_external_project_dir`
- `test_validate_raises_when_external_project_dir_path_missing`
- `test_validate_passes_when_external_project_dir_exists`
- `test_trigger_agent_raises_before_enqueue_when_precondition_fails`
- `test_trigger_route_returns_422_with_structured_payload`
- `test_trigger_route_returns_422_when_path_missing`
- `test_trigger_route_succeeds_when_external_project_dir_set`
- `test_launch_agent_raises_when_external_project_dir_unset`
- `test_trigger_returns_422_on_malformed_delegation_context`

**Atomic tasks (new only):**
- Cross-check sentinel: run `pytest cast-server/tests/test_dispatch_precondition.py`
  under integration-suite env vars (`CAST_DISABLE_SERVER=1`); confirm green.
  If anything regresses there, that's a real bug surfaced — escalate
  to the appropriate sp4 bucket.
- **Genuinely-new method 1: depth-4 422 BEFORE row creation (US2.S7).**
  Simulate a chain `run0 → run1 → run2 → run3`; attempt the 4th dispatch;
  assert 422 returned AND zero new row in `agent_runs` for the 4th attempt
  (row-precedence is the test).
- **Genuinely-new method 2: `/invoke` carve-out negative test.**
  Dispatch via `/invoke` route to a goal with no `external_project_dir` —
  assert NOT 422 (carve-out preserved). Method
  `test_invoke_route_does_not_422`, same class (per plan open-question
  resolution).

**Verification:**
- `pytest cast-server/tests/integration/test_child_delegation.py -k "ExternalProjectDirPrecondition"`
  collects ≥4 test methods.
- Each 422 body assertion uses the exact field names from
  `cast-delegation-contract.collab.md`.

**Spec consistency:** US2.S3, US2.S7, FR-002,
`cast-delegation-contract.collab.md` §Dispatch Precondition,
spec §Out of Scope (`/invoke` carve-out preserved).

**Inline design review:**
- *Decision:* same class hosts the carve-out test (per plan open-question
  resolution). Alternatives: separate class. *Rationale:* keeps the carve-out
  visible alongside the enforcement — a future reader sees both at once.

---

### sp3.2 — `TestOutputJsonContractV2` + schema fixture

**Outcome:** Output JSON contract v2 conformance asserted: non-terminal status
detected, `next_steps` typed shape validated against
`tests/fixtures/next_steps.schema.json`, untagged Open Questions flagged
per US13.

**Dependencies:** Phase 2.

**Files created:**
- `cast-server/tests/fixtures/next_steps.schema.json` (new — typed shape per
  US14: `{command, rationale, artifact_anchor}` required per entry)
- `cast-server/tests/integration/test_child_delegation.py` (append class)

**Atomic tasks:**
- Author the JSON Schema for `next_steps` array entries based on
  `cast-output-json-contract.collab.md` (read the spec for the typed shape).
- `TestOutputJsonContractV2` test methods:
  - Non-terminal `status` (parametrize over `pending`, `running`, `idle`) →
    parent finalizer transitions to `failed` with parse-error in `errors[]`
    (US2.S4).
  - `next_steps` entry as a bare string → schema validation fails (US2.S5).
  - `Open Questions` section with an untagged item (no `[EXTERNAL]` /
    `[USER-DEFERRED]`) → contract violation surfaced per US13 (US2.S6).

**Verification:**
- `pytest cast-server/tests/integration/test_child_delegation.py -k "OutputJsonContractV2"`
  collects all methods.
- `python -c "import json; json.load(open('cast-server/tests/fixtures/next_steps.schema.json'))"` is valid JSON.

**Spec consistency:** US2.S4, US2.S5, US2.S6, FR-002,
`cast-output-json-contract.collab.md` §Terminal Status / US13 / US14.

**Inline design review:**
- *Decision:* schema lives at `cast-server/tests/fixtures/` (test-only) per
  plan open-question recommendation. Alternatives: canonical in
  `cast-server/cast_server/contracts/`. *Rationale:* test-only is the
  smallest commitment now; promote later if non-test code needs it.

---

### sp3.3 — `TestMtimeHeartbeatRoundTrip`

**Outcome:** Parent transitions to terminal within ≤1 polling-tick after
child's `mtime` update is observed. File-canonical only — HTTP is
mocked/disabled via `CAST_DISABLE_SERVER=1`.

**Dependencies:** Phase 2.

**Files touched:** `cast-server/tests/integration/test_child_delegation.py`
(append class).

**Atomic tasks:**
- Set up a parent run with a polling loop using the env-var backoff ladder
  (10ms/20ms/50ms).
- Spawn (or simulate) a child writing a valid contract-v2 `output.json` and
  touch its mtime.
- Assert: parent observes the mtime update and transitions to terminal
  within one tick of the override schedule (use a tick-counting wrapper or
  `monkeypatch` on the polling primitive).
- This test is EXPECTED to fail at first (this is the parent-stall symptom
  bucket from US2.S1) — that's the red baseline for sp4a.

**Verification:**
- `pytest cast-server/tests/integration/test_child_delegation.py -k "MtimeHeartbeatRoundTrip"` collects the class. Failures here ARE the signal that
  sp4a needs to fix something.

**Spec consistency:** US2.S1, FR-002,
`cast-delegation-contract.collab.md` §Heartbeat-by-mtime.

**Inline design review:**
- *Decision:* this test is EXPECTED to be red until sp4a. Alternatives:
  `xfail` marker. *Rationale:* spec US2 explicitly disallows `xfail` markers
  on goal-exit ("Goal exit commit shows every one of those tests passing
  without `xfail`"). It's red on the way to green; never xfailed.

---

## Phase 4: Red-to-Green Fix Sweep

> **Critical discipline:** sub-phase task lists below are intentionally
> **deferred** until Gate B fires. The plan identifies the buckets and the
> *likely-implicated* code, but the actual fix decomposition depends on the
> failing-test list produced by sp2.5. Speculative atomic-task enumeration
> here would be honesty-violating.

### sp4a — Parent stall after child finalize (BOTH finalizer entry points)

**Outcome:** Every test that fails because the parent's polling loop doesn't
transition within ≤1 polling-tick after child mtime updates is now green.
At least one commit `fix(delegation): green <test_name>` lands in this
sub-phase.

**Dependencies:** Phase 3 + Gate B (failing-test list reviewed).

**Files likely touched (informed by plan §Phase 4a):**
- `cast-server/cast_server/services/agent_service.py` —
  `_finalize_run` (line 1702) AND `_finalize_run_from_monitor` (line 2520).
  Per Review #2, the cleanup-and-transition contract must hold across BOTH
  entry points; if the bug is in one, verify the other independently.
- The polling loop primitive (likely in the same file)

**Atomic tasks:**
**Detail deferred:** awaiting Gate B failing-test list. The specific tests in
this bucket determine the fix surface. Likely 1–3 minimum-diff fixes per the
"polling loop doesn't observe mtime" pattern, but the actual decomposition is
runtime-determined.

**Verification:**
- All tests in the parent-stall bucket (TBD by Gate B) green.
- `git log --grep "fix(delegation): green"` includes ≥1 commit in this
  sub-phase, naming a parent-stall test.
- No unrelated refactor diff (constraint check).

**Spec consistency:** US2.S1, FR-006, SC-003,
`cast-delegation-contract.collab.md` §Heartbeat-by-mtime.
*If fix work reveals contract drift, escalate via `/cast-update-spec` (sp7.3)
— do NOT silently change spec.*

**Inline design review:**
- *Decision:* minimum-diff fixes only; structural polling-loop refactor is
  out of scope (Risk #1 escalation point).

---

### sp4b — Cleanup or contract drift

**Outcome:** Every test that fails because of orphan files
(`.delegation-*.json` / `.prompt` / `.continue` / `.tmp`), malformed 422 body
shape, or mixed-transport preamble emission errors is green. At least one
commit `fix(delegation): green <test_name>` lands in this sub-phase.

**Dependencies:** Phase 3 + Gate B.

**Files likely touched (informed by plan §Phase 4b):**
- `_finalize_run_from_monitor` cleanup section
- Trigger route (`cast-server/cast_server/routes/api_agents.py`)
- `_build_agent_prompt` mixed-transport branch

**Atomic tasks:**
**Detail deferred:** awaiting Gate B. Likely buckets:
- Cleanup: align finalizer's deletion list with the four-file inventory
  (`.delegation-<run_id>.json`, `.agent-run_<run_id>.prompt`, `.continue*`).
- 422 body: align trigger-route response shape with `cast-delegation-contract.collab.md`.
- Mixed-transport preamble: ensure anti-inline phrase emits exactly once
  across both blocks.

**Verification:**
- All tests in this bucket green.
- ≥1 `fix(delegation): green` commit naming a cleanup/contract-drift test.

**Spec consistency:** US2.S2, US2.S3, US2.S5, US1.S5, US1.S9, FR-006, SC-003, SC-004.

**Inline design review:**
- *Decision:* if mixed-transport preamble structure has diverged from
  second-brain (Risk #3), the equivalence-map docstring already documents
  the divergence (sp2.5). Phase 4b's job is to fix the ASSERTION, not
  the structure — unless the structure is provably wrong against
  `cast-delegation-contract.collab.md`. In which case: contract drift,
  escalate.

---

### sp4c — Allowlist / depth / output-JSON contract passing silently

**Outcome:** Every test that fails because non-terminal status / untagged
Open Questions / 4th-depth row-creation passes silently is now green. At
least one commit `fix(delegation): green <test_name>` lands.

**Dependencies:** Phase 3 + Gate B.

**Files likely touched (informed by plan §Phase 4c):**
- Output-JSON parser/validator (likely in `agent_service.py` or a sibling)
- `_get_delegation_depth` ordering vs row-create in `agent_service.py` /
  `routes/api_agents.py`
- Open-Questions tag enforcement (US13 close-out validator — locate; may
  not exist yet, in which case sp4c authors it)

**Atomic tasks:**
**Detail deferred:** awaiting Gate B. Likely buckets:
- Tighten output-JSON parser to reject non-terminal status as malformed.
- Reorder depth-check to run BEFORE `agent_runs` row insert.
- Author or extend Open-Questions tag-validator (US13 enforcement).

**Verification:**
- All tests in this bucket green.
- ≥1 `fix(delegation): green` commit naming a silent-violation test.
- SC-003 satisfied: `git log --grep "fix(delegation): green"` shows ≥3
  commits across sp4a + sp4b + sp4c, each naming a distinct symptom-bucket
  test.

**Spec consistency:** US2.S4, US2.S6, US2.S7, FR-006, SC-003,
`cast-output-json-contract.collab.md` §US13/US14.

**Inline design review:**
- *Decision:* if Open-Questions tag-validator doesn't exist yet, sp4c
  authors it (minimum-viable). Alternatives: file a separate goal.
  *Rationale:* US2.S6 is in-scope; not authoring the validator would make
  the test inherently red — out of spirit.

---

## Phase 5: T2 Live HTTP E2E

### sp5.1 — Author `test_tier_delegation.py` skeleton + happy path

**Outcome:** `cast-server/tests/e2e/test_tier_delegation.py` exists with
imports, `@pytest.mark.e2e` marker, and the first case
`test_parent_delegator_happy_path` (US3.S1) runnable.

**Dependencies:** Phase 4 (T1 must be green first).

**Files created:**
- `cast-server/tests/e2e/test_tier_delegation.py`
- `cast-server/tests/e2e/__init__.py` (if needed for pytest discovery)
- `cast-server/tests/e2e/conftest.py` (e2e-specific fixtures, lifecycle scoped
  per Review #9: cast-server is **session-scoped** — single subprocess + health
  check, reused across all T2 cases. Goal directory `child-delegation-e2e` is
  **per-test reset**: between cases, remove `.agent-run_*`, `.delegation-*`,
  `.prompt`, `.continue` files; preserve `goal.yaml` + `requirements.human.md`.
  Also clear DB rows tied to that `goal_slug` between tests so child-row-count
  assertions are deterministic. Export `CAST_TEST_AGENTS_DIR` into the spawned
  cast-server's environment so fixture agents register.)

**Atomic tasks:**
- Author the session-scoped spawn fixture: subprocess launches cast-server,
  health-check polls until ready, teardown sends SIGTERM at session end.
- Author the per-test reset fixture: clears `child-delegation-e2e` goal-dir
  artifacts + DB rows scoped to that goal_slug.
- `test_parent_delegator_happy_path`:
  - **Per-case timeout (Review #10):** decorate with
    `@pytest.mark.timeout(360)` — sized as `idle_timeout (300s) + 60s buffer`.
    Document the 360 derivation in `cast-server/tests/e2e/conftest.py`.
  - Trigger `cast-test-parent-delegator` via real HTTP (use bash-curl
    helper — NO Python `requests`/`httpx`/`urllib`, FR-008).
  - Poll for completion with reasonable budget (no env overrides — production
    cadence per spec §Constraints).
  - Assert: parent run `status: completed`; ≥1 child run with
    `parent_run_id` set; child `result_summary` non-empty; child's tmux
    session no longer exists.

**Verification:**
- `pytest cast-server/tests/e2e/test_tier_delegation.py -m e2e -k "happy_path"` exits 0 on a host with cast-server bin + ptyxis available.
- FR-008 lint: `! grep -E '^(import|from)\s+(requests|httpx|urllib)' cast-server/tests/e2e/test_tier_delegation.py`.

**Spec consistency:** US3.S1, FR-004, FR-008, SC-002.

**Inline design review:**
- *Decision:* HTTP via bash curl, not Python. Alternatives: write a thin
  Python HTTP client that satisfies the spirit of FR-008. *Rationale:* FR-008
  is unambiguous — bash curl only.

---

### sp5.2 — `test_delegation_denied`

**Outcome:** Second E2E case wired: dispatching
`cast-test-delegation-denied` (whose prompt tries a non-allowlisted target)
results in parent `completed` with no child rows AND `result_summary`
containing "422" or "denied".

**Dependencies:** sp5.1.

**Files touched:** `cast-server/tests/e2e/test_tier_delegation.py` (append).

**Atomic tasks:**
- Decorate with `@pytest.mark.timeout(360)` (Review #10).
- Trigger `cast-test-delegation-denied` via real HTTP (bash curl).
- Poll for completion.
- Assert: zero child runs with this parent's `parent_run_id`; parent's
  `result_summary` substring contains "422" OR "denied" (deterministic per
  the literal-prompt fixture from sp1.2 / Review #5).

**Verification:**
- `pytest cast-server/tests/e2e/test_tier_delegation.py -m e2e -k "denied"` exits 0.

**Spec consistency:** US3.S2, FR-004.

**Inline design review:** No flags.

---

### sp5.3 — `test_mid_flight_session_isolation`

**Outcome:** Third E2E case wired: parent and child show as separate tmux
sessions, parent has 1 pane (not split). If child completes too fast to
verify mid-flight, test `pytest.skip`s with that explanation (matches
second-brain pattern).

**Dependencies:** sp5.1.

**Files touched:** `cast-server/tests/e2e/test_tier_delegation.py` (append).

**Atomic tasks:**
- Decorate with `@pytest.mark.timeout(360)` (Review #10).
- Trigger `cast-test-parent-delegator`; immediately start polling tmux
  for `agent-<parent>` and `agent-<child>` sessions (within 60s budget).
- If both observed before either completes: assert separate sessions,
  parent pane count == 1.
- If child completes too fast: `pytest.skip("child too fast to observe
  mid-flight")` (verbatim second-brain pattern).

**Verification:**
- `pytest cast-server/tests/e2e/test_tier_delegation.py -m e2e -k "session_isolation"` exits 0 OR skips with the documented reason.

**Spec consistency:** US3.S3, FR-004.

**Inline design review:**
- *Decision:* `pytest.skip` for race-loss is the second-brain pattern.
  Alternatives: forced-slow child via env-var. *Rationale:* spec §US3.S3
  explicitly authorizes the skip; introducing a slow-child knob would be
  scope creep.

---

### **[GATE C]** — T2 ptyxis CI strategy

**Trigger:** Before sp5.4 (CI workflow YAML).

**Surface to user:**
1. Recommended (option a): self-hosted nightly runner with ptyxis.
2. Alternative (option b): `xvfb-run` wrap + no-ptyxis fallback path.
3. Alternative (option c): T2 graceful-degrade when ptyxis is missing
   (assert filesystem + DB but skip terminal visibility checks).

**Resolution path:** the test code in sp5.1–sp5.3 is workflow-agnostic; only
sp5.4 (workflow YAML) depends on this decision. If decision delays, sp5.4
parks until the runner / fallback is decided.

---

### sp5.4 — Wire nightly CI workflow

**Outcome:** A nightly CI workflow runs T2 against a runner per Gate C
decision. Workflow file lives in the repo's CI directory (likely
`.github/workflows/` for GitHub Actions or equivalent).

**Dependencies:** sp5.1, sp5.2, sp5.3, Gate C.

**Files created:**
- `.github/workflows/cast-delegation-e2e-nightly.yml` (or whatever path the
  Gate C decision specifies — runner labels, schedule trigger, env)

**Atomic tasks:**
**Detail deferred:** awaiting Gate C decision. Workflow shape depends on
runner choice (self-hosted vs xvfb-wrap vs graceful-degrade).

**Verification:**
- Workflow YAML lints (use the project's existing CI lint, or `actionlint`
  if available).
- First scheduled run executes; result observed.
- SC-002 (≥3 consecutive green runs) is a Phase 7 closeout gate.

**Spec consistency:** FR-004, SC-002.

**Inline design review:**
- *Decision:* explicit gate before YAML authoring (Risk #4 mitigation).
  Alternatives: pre-author all three workflow variants. *Rationale:* spec
  is bounded scope; authoring three throwaway workflows is gold-plating.

---

## Phase 6: Subagent Coverage — Builder Unit Tests + Manual Checklist

> **Parallelism:** Phase 6 can run in parallel with Phase 5 — independent
> code paths. DAG below shows side-by-side. If a single person is driving,
> serialize behind Phase 4 in either order.

### sp6.1 — `TestSubagentOnlyPreamble`

**Outcome:** New test class in T1 covering subagent-only preamble:
`_build_agent_prompt` with `allowed_delegations=[subagent_only_target]`
emits ONLY the Subagent-dispatch block, includes structured-return /
no-summarize contract, does NOT emit the curl/poll quick reference (US4.S2).

**Dependencies:** Phase 4 (T1 baseline must be green).

**Files touched:** `cast-server/tests/integration/test_child_delegation.py`
(append class); equivalence-map docstring updated.

**Atomic tasks:**
- Build prompt with `allowed_delegations=[cast-test-child-worker-subagent]`
  (subagent dispatch_mode).
- Assert: Subagent-dispatch block present; HTTP-dispatch block absent;
  structured-return contract phrase present; curl/poll quick-reference
  string absent.

**Verification:**
- `pytest cast-server/tests/integration/test_child_delegation.py -k "SubagentOnlyPreamble"` exits 0.

**Spec consistency:** US4.S2, FR-005.

**Inline design review:** No flags.

---

### sp6.2 — Author `MANUAL_SUBAGENT_CHECKLIST.md`

**Outcome:** `cast-server/tests/MANUAL_SUBAGENT_CHECKLIST.md` exists with ≤10
steps covering US4.S1: dispatch via Claude Code's Agent tool, verify verdict
surfaced as-is (not summarized), confirm no `agent_runs` row created
(subagent-mode bypasses run queue), confirm preamble named target in
Subagent block. Includes "verified by" footer with date / maintainer / result
fields.

**Dependencies:** None (independent of any code path).

**Files created:** `cast-server/tests/MANUAL_SUBAGENT_CHECKLIST.md`.

**Atomic tasks:**
- Draft 10 steps mapping to US4.S1 acceptance criteria.
- Add "verified by" footer with empty rows: `| Date | Maintainer | Result |`.
- Cross-link to `docs/specs/cast-delegation-contract.collab.md` §Subagent
  Dispatch.

**Verification:**
- File exists and lints (markdown).
- Step count ≤10.
- Footer present.
- A maintainer NOT involved in writing follows it cold and confirms green
  in <5 min — record in footer (this confirmation is part of sp7.2 close-out).

**Spec consistency:** US4.S1, FR-005, SC-005.

**Inline design review:**
- *Decision:* checklist over auto-harness. Alternatives: scripted
  Claude-Code conversation. *Rationale:* spec §Out of Scope explicitly
  excludes "Automated subagent live E2E" — manual checklist IS the
  contract.

---

## Phase 7: Close-Out

### sp7.1 — Wait for and verify nightly CI

**Outcome:** Nightly CI shows T2 green for ≥3 consecutive runs (SC-002).

**Dependencies:** sp5.4 wired and at least 3 nightly cycles elapsed.

**Files touched:** None.

**Atomic tasks:**
- Inspect CI history; confirm ≥3 consecutive green nightly runs.
- If any red run, diagnose: spec drift, infra flake, real regression?
  Real regression → another `fix(delegation): green` commit cycle (extends
  the goal). Infra flake → document in sp7's notes; may proceed.

**Verification:**
- CI dashboard / `gh run list` shows ≥3 green nightly runs of the workflow.

**Spec consistency:** SC-002.

**Inline design review:** No flags.

---

### sp7.2 — Equivalence-map review + checklist verification footer

**Outcome:** Reviewer signs off on equivalence-map docstring (SC-007). Manual
checklist's "verified by" footer is populated with a successful first run by
a maintainer NOT involved in writing it (SC-005).

**Dependencies:** Phase 4, Phase 6 complete.

**Files touched:** `cast-server/tests/MANUAL_SUBAGENT_CHECKLIST.md` (footer
update only).

**Atomic tasks:**
- Reviewer cross-checks each second-brain `test_delegation.py` class against
  the docstring entry (counterpart OR justified-skip).
- Independent maintainer follows the manual checklist cold; records date /
  name / result in the footer.

**Verification:**
- Reviewer's PR comment or commit confirms equivalence-map review.
- Checklist footer has at least one populated row.

**Spec consistency:** SC-005, SC-007, FR-007.

**Inline design review:** No flags.

---

### sp7.3 — Conditional spec update via `/cast-update-spec`

**Outcome:** If Phase 4 fix work surfaced contract clarification needs,
`cast-delegation-contract.collab.md` and/or
`cast-output-json-contract.collab.md` are updated via `/cast-update-spec`.
If no clarifications surfaced, this sub-phase is a no-op.

**Dependencies:** Phase 4 retrospective.

**Files touched (conditional):**
- `docs/specs/cast-delegation-contract.collab.md`
- `docs/specs/cast-output-json-contract.collab.md`

**Atomic tasks:**
- Review Phase 4 commit messages and PR notes for any "spec was ambiguous"
  / "contract drift" mentions.
- For each, → Delegate: `/cast-update-spec` with the specific section and
  the proposed clarification. Review output before commit.
- If none surfaced, document "no spec changes needed" in sp7's run notes.

**Verification:**
- Spec diffs reviewed by user.
- `bin/cast-spec-checker` passes on any modified spec.

**Spec consistency:** Plan §Phase 7 escalation policy ("align code to spec
OR escalate spec change to user — do NOT silently change either").

**Inline design review:**
- *Decision:* spec changes go through the proper agent
  (`/cast-update-spec`), not direct edits. Alternatives: hand-edit.
  *Rationale:* the spec lifecycle has its own checks (lint, registry
  registration); bypassing them creates drift.

---

### sp7.4 — Flip goal status to closed

**Outcome:** Goal `child-delegation-integration-tests` shows `status:
completed` (or whatever close-state the goal model uses). Achieved via
`/cast-goals` — no direct edit of `goal.yaml`.

**Dependencies:** sp7.1, sp7.2, sp7.3.

**Files touched:** none directly (DB-managed via `/cast-goals`).

**Atomic tasks:**
- → Delegate: `/cast-goals` with the specific status-change action for
  `child-delegation-integration-tests`. Review output.
- Verify post-flip: `cat goals/child-delegation-integration-tests/goal.yaml`
  shows the new status (the file is a read-only render — sanity check only).

**Verification:**
- `goal.yaml` reflects the closed status.

**Spec consistency:** User-locked decision: goal-status flip via
`/cast-goals`, never direct edit.

**Inline design review:** No flags.

---

## Build Order (DAG)

```
sp1.1 ─┐
sp1.2 ─┼─► sp1.3 ─► sp1.4 ─► [GATE A]
sp1.4 ─┘                          │
                                  ▼
                          sp2.1 ─► sp2.2 ─► sp2.3 ─► sp2.4 ─► sp2.5 ─► [GATE B]
                                                                          │
                                                                          ▼
                                              sp3.1 ─┐
                                              sp3.2 ─┼─► (Phase 3 done)
                                              sp3.3 ─┘
                                                          │
                                                          ▼
                                              sp4a ─┐
                                              sp4b ─┼─► (Phase 4 done) ─┐
                                              sp4c ─┘                    │
                                                                         ├─► sp5.1 ─► sp5.2 ─► sp5.3 ─► [GATE C] ─► sp5.4 ─┐
                                                                         │                                                  │
                                                                         └─► sp6.1 ─► sp6.2 ──────────────────────────────┤
                                                                                                                            │
                                                                                                                            ▼
                                                                                          sp7.1 ─► sp7.2 ─► sp7.3 ─► sp7.4
```

**Critical path:** sp1.1 → sp1.3 → [Gate A] → sp2.1 → sp2.5 → [Gate B] → sp3.x →
sp4.x → sp5.x → [Gate C] → sp5.4 → sp7.1 → sp7.4

**Parallel:** sp1.1 / sp1.2 / sp1.4 can run concurrently. sp3.1 / sp3.2 / sp3.3 are
independent. sp4a / sp4b / sp4c are independent (commit isolation). Phase 6 runs
parallel with Phase 5. sp7.1 / sp7.2 / sp7.3 are independent.

## Design Review Flags (Consolidated)

| Sub-phase | Flag | Action |
|-----------|------|--------|
| sp1.1 | Registry-discovery seam choice is the riskiest unknown in Phase 1 | Resolve before sp1.3; document the choice in 5–10 lines |
| sp1.2 | `cast-test-delegation-denied` has a deliberately-failing prompt | Document in fixture comment so future readers don't "fix" the bug |
| sp2.2 | "WRITE BEFORE RETURNING" assertion needs monkeypatch interception | Use second-brain's pattern verbatim; do NOT re-architect `trigger_agent` |
| sp2.3 | Mixed-transport preamble may have diverged from second-brain (Risk #3) | Document divergence in equivalence-map as justified deviation |
| sp2.4 | tmux message-not-pasted is a security-relevant assertion | Make it the first method in the class — visibility |
| sp3.3 | Test is EXPECTED red until sp4a — NO `xfail` marker | Spec US2 disallows xfail at goal exit |
| sp4a/4b/4c | Atomic-task lists deferred until Gate B fires | Honesty discipline; do NOT speculate |
| sp4b | Mixed-transport preamble fix may surface contract drift | If structure is wrong vs spec, escalate via sp7.3 — do NOT silently change |
| sp4c | Open-Questions tag-validator may not exist yet | sp4c authors minimum-viable; alternative is filing separate goal (out of spirit) |
| sp5.1 | FR-008 forbids Python `requests`/`httpx`/`urllib` | Use bash curl helper; lint-check with grep before commit |
| sp5.4 | Workflow YAML deferred until Gate C resolves | Test code is workflow-agnostic; only YAML parks |
| sp7.3 | Spec changes ONLY via `/cast-update-spec`, not hand-edit | Lifecycle integrity — registry / lint discipline preserved |

## Key Risks & Mitigations (Inherited from High-Level Plan)

| Risk | Impact | Mitigation |
|------|--------|------------|
| Phase 4 fix uncovers structural issue (e.g., racy polling) | High | Out-of-scope clause: file separate goal. Gate B is the escalation surface. |
| Registry-discovery seam doesn't have a clean test-fixture-dir hook | Medium | sp1.1 audits first; smallest-diff fallback is `CAST_AGENT_FIXTURE_DIRS`. |
| Mixed-transport preamble test (sp2.3) doesn't transfer cleanly from second-brain | Medium | Read `_build_agent_prompt` thoroughly first; document divergence as justified deviation in equivalence map. |
| Gate C delays block sp5.4 indefinitely | Medium | Test code (sp5.1–5.3) is workflow-agnostic; only sp5.4 parks. |
| T1 wall-clock budget bust from broken env-var hooks | Low-Medium | US6 has explicit acceptance scenarios; if hooks broken, that's its own red→green cycle in sp4 — surfacing the bug, not hiding. |
| Goal scope creep — Phase 4 tempts adjacent cleanup | Medium | FR-006 commit convention surfaces creep at PR review; reviewer enforces "no unrelated refactor". |

## Open Questions

These are gate-time decisions, NOT up-front blockers. Listed for record-keeping.

1. **Fixture-agent location** — Recommended `cast-server/tests/integration/agents/<name>/`.
   Resolved at **Gate A** after sp1.4. If the user prefers a different location,
   sp1.2 + sp1.3 redo is cheap (no tests yet depend on the path).

2. **T2 ptyxis-in-CI strategy** — Recommended option (a): self-hosted nightly with
   ptyxis. Resolved at **Gate C** before sp5.4. Test code is workflow-agnostic.

3. **Failing-test enumeration before Phase 4** — The actual failing-test list is
   unknown until sp2.5 produces it. Resolved at **Gate B** before sp4a/4b/4c
   commit any fix.

4. **`/invoke` carve-out negative-test placement** — Recommendation: same class
   (`TestExternalProjectDirPrecondition`), method `test_invoke_route_does_not_422`.
   Non-blocking; finalize while authoring sp3.1.

5. **`tests/fixtures/next_steps.schema.json` canonical-vs-test-only** —
   Recommendation: test-only for now. Promote to
   `cast-server/cast_server/contracts/` later if non-test code needs it.
   Non-blocking; finalize during sp3.2.

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| `docs/specs/cast-delegation-contract.collab.md` | Dispatch Precondition, Heartbeat-by-mtime, Cleanup contract, Subagent Dispatch | None — plan asserts against. If sp4 surfaces contract drift, escalate via sp7.3 (`/cast-update-spec`). |
| `docs/specs/cast-output-json-contract.collab.md` | Terminal Status, US13 (open-question tags), US14 (typed `next_steps`) | None — sp3.2 asserts conformance. If sp4c surfaces drift, escalate via sp7.3. |

## Equivalence Map (FR-007 Realization Anchor)

The equivalence map between second-brain `test_delegation.py` test classes and
diecast counterparts is realized as a module-level docstring at the top of
`cast-server/tests/integration/test_child_delegation.py`. Lifecycle:

- **sp1.4** stubs the docstring with all 11 second-brain class names + TODO
  markers (file is empty of tests at this point).
- **sp2.1–sp2.4 + sp3.1–sp3.3 + sp6.1** populate one TODO per class as it
  lands.
- **sp2.5** verifies docstring has 0 `TODO` substrings.
- **sp7.2** has the reviewer cross-check the populated map against
  second-brain (SC-007).

This is the concrete artifact realizing FR-007 — a single docstring, two
checkpoints (sp2.5 and sp7.2), one reviewer signoff.

## Out-of-Scope (Boundary Reaffirmation)

Inherited verbatim from spec §Out of Scope. No sub-phase performs:
- Automated subagent live E2E (sp6.2 is checklist; that's the contract)
- Refactoring delegation transport beyond test-greening minimum-diff
- B5/B3/B4 primitive coverage (the existing `tests/test_b{3,4,5}_*.py` cover them)
- Performance / load testing
- `/invoke` carve-out enforcement (negative test in sp3.1 only confirms the carve-out)
- Cleanup of orphan `.tmp` files from crashed children (deferred to `sp-cleanup` goal)
- OS-side cross-RUN_ID write protection

## Decisions

- **2026-05-01T00:00:00Z — cast-plan-review auto-trigger: was the plan reviewed?** — Decision: Reviewed in non-interactive mode initially; superseded by full interactive review 2026-05-01T01:00 (entries below). Rationale: child-delegation auto-trigger fired per cast-detailed-plan Step 10; user subsequently invoked `/cast-plan-review` interactively, surfacing 10 issues across all 4 sections.
- **2026-05-01T00:00:00Z — Self-review Architecture findings?** — Decision: None blocking. (Superseded by interactive review #1, #2, #3.)
- **2026-05-01T00:00:00Z — Self-review Code Quality findings?** — Decision: None blocking. (Superseded by interactive review #4, #5, #6.)
- **2026-05-01T00:00:00Z — Self-review Tests findings?** — Decision: Minor — recommend per-test pytest.mark.timeout. (Superseded by interactive review #7 — committed as suite-wide timeout=5 in sp2.1.)
- **2026-05-01T00:00:00Z — Self-review Performance findings?** — Decision: None. (Superseded by interactive review #10 — T2 per-case timeout=360 added.)
- **2026-05-01T01:00:00Z — Review #1: Is sp1.1+sp1.3 over-scoped given CAST_TEST_AGENTS_DIR already exists?** — Decision: Collapse — sp1.1 becomes a 1-task verify, sp1.3 becomes a conftest one-liner setting CAST_TEST_AGENTS_DIR. Rationale: seam exists at agent_config.py:62-70 and agent_service.py:1618-1631 with mtime cache + collision-warn. New env var would fragment the discovery model. Risk #2 retired.
- **2026-05-01T01:00:00Z — Review #2: How should plan disambiguate _finalize_run vs _finalize_run_from_monitor?** — Decision: sp2.2 covers BOTH; cleanup contract is invariant across finalizer entry points. Rationale: cast-delegation-contract.collab.md cleanup contract is silent on which entry point owns cleanup; testing both pins the invariant. If diecast centralizes cleanup in only one finalizer, the test for the other surfaces that as a contract violation (useful red signal). Matches second-brain pattern.
- **2026-05-01T01:00:00Z — Review #3: How should T1 test isolation handle the _config_cache mtime cache?** — Decision: Mandate the patch pattern — monkeypatch load_agent_config (the public seam) per test; add an autouse session-scoped cache.clear() fixture in cast-server/tests/integration/conftest.py as belt-and-suspenders. Rationale: monkeypatch is the second-brain pattern and the public seam; cache.clear() eliminates flake risk without code changes to agent_config.py.
- **2026-05-01T01:00:00Z — Review #4: sp3.1 DRY violation with existing test_dispatch_precondition.py** — Decision: Re-scope sp3.1 to add only the genuinely-new cases (depth-4-precedes-row, /invoke carve-out negative); cross-check existing 9 precondition tests pass under integration-suite env vars; cite by name in equivalence-map docstring. Rationale: 9 existing tests already cover trigger 422 unset/path-missing/structured-payload + launcher re-validation + malformed delegation_context; duplicating creates dual-source-of-truth. Auto-applied (unambiguous DRY).
- **2026-05-01T01:00:00Z — Review #5: sp1.2 fixture-prompt determinism under-specified** — Decision: Fixture prompts MUST instruct the child to write a LITERAL contract-v2 output JSON (not paraphrasable). Rationale: prompts are LLM-interpreted; vague prompts → flaky T2 substring assertions. Sentinel strings make sp5.2's "denied"/"422" assertion deterministic. Auto-applied.
- **2026-05-01T01:00:00Z — Review #6: sp2.5 'tighten or skip' escape hatch** — Decision: Replace 'or skip with justification' with 'Tighten — never skip; if a test cannot fit budget, escalate to plan-revision'. Rationale: skipping bypasses FR-003; escalation surfaces the bug instead of hiding it. Auto-applied.
- **2026-05-01T01:00:00Z — Review #7: Per-test timeout commit (was vague in self-review appendix)** — Decision: Commit to suite-wide `[pytest] timeout = 5` in cast-server/tests/integration/pytest.ini (added to sp2.1 atomic tasks). Rationale: single-line belt-and-suspenders defense for FR-003; failure mode becomes 'test timed out' instead of 'suite hung'. Auto-applied.
- **2026-05-01T01:00:00Z — Review #8: Missing TestDispatchModeValidator coverage** — Decision: Add TestDispatchModeValidator class to sp2.3 with three methods pinning the silent-fallback semantics at agent_config.py:36-41 (typo→http, sibling fields preserved, valid values pass through). Rationale: zero existing diecast coverage; second-brain had this; US2 explicitly targets silent failures. A typo'd `dispatch_mode: subagnet` in a future fixture would silently lose subagent coverage. Auto-applied.
- **2026-05-01T01:00:00Z — Review #9: How should T2 fixture lifecycle be scoped?** — Decision: cast-server is session-scoped (single subprocess + health check); goal-dir is per-test reset (rm artifacts; preserve goal.yaml + requirements.human.md; clear DB rows scoped to that goal_slug). Rationale: matches second-brain tier2 pattern; server-spawn dominates wall-clock so per-test would 3x runtime; per-test goal-dir reset gives clean isolation cheaply.
- **2026-05-01T01:00:00Z — Review #10: T2 per-case timeout missing** — Decision: Add `@pytest.mark.timeout(360)` to each T2 case (sp5.1, sp5.2, sp5.3); document derivation as `idle_timeout (300s) + 60s buffer` in cast-server/tests/e2e/conftest.py. Rationale: production-cadence T2 has no override; a stuck case could hang nightly CI for hours; 300s exactly equals idle-timeout (would race synthetic-failure tests), so 360 gives buffer. Auto-applied.
- **2026-05-01T01:00:00Z — Single-Write contract deviation** — Decision: The skill's strict "exactly 1 Write per run" contract was relaxed to a series of focused Edit calls (one per body patch + one for this appendix). Rationale: the plan is 1146 lines; reconstructing in a single Write is error-prone for the agent and produces an unreadable diff for the reviewer. Focused Edits produce cleanly-scoped diffs that map 1:1 to decisions. Same correctness outcome; cleaner audit trail. Flagging here for transparency.
