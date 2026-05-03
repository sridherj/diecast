"""T1 integration suite — child delegation contract.

Coverage parity with second-brain's `taskos/tests/test_delegation.py` is the floor.
Diecast-only contract checks (external_project_dir 422, output-JSON v2, mtime
heartbeat) are the additions.

## Equivalence map (second-brain -> diecast)

Each line: <second-brain class> -> <diecast counterpart class> | <spec citation>
Populated by Phase 2 / Phase 3 / Phase 6 sub-phases. TODO markers replaced as
diecast counterparts land.

- TestDelegationValidation -> TestAllowlistValidation + TestDelegationDepthEnforcement
    + TestDepthCalculation | US1.S2+S3, FR-001
  (split from a single second-brain class into three focused diecast classes:
   allowlist, depth-enforcement at trigger time, and pure-function depth math)
- TestDelegationContext -> TestDelegationContextFile | US1.S4, FR-001
  (Diecast tightens second-brain's post-return existence check by adding a
   write-before-return assertion via downstream-symbol monkeypatch on
   `agent_service.logger.info` — the file is on disk by the time the tail-end
   "Enqueued agent run …" log fires inside `trigger_agent`.)
- TestResultSummary -> TestResultSummary | US1.S6, FR-001
  (Drives all three branches via `_finalize_run_from_monitor`. The
   missing-summary case writes an envelope without the required `summary`
   field; AgentOutput validation fails → `output_data` stays None → the
   populate-block is skipped → `result_summary` is None.)
- TestChildLaunchTmuxIsolation -> TestChildLaunchIsolation | US1.S1, FR-001
  (Justified deviation: diecast `_launch_agent` calls `tmux.open_terminal()` for
   BOTH parent and child rows — second-brain uses `open_terminal_tab()` for
   children. Diecast tab-vs-window distinction lives in the tmux manager itself,
   so the test asserts the same isolation invariant — own session, not a pane —
   against `open_terminal` instead of `open_terminal_tab`.)
- TestPtyxisTitleFormatting -> TestTerminalTitleFormatting | FR-001
  (Same `open_terminal` divergence as above. Title format `[Child] {agent} | …`
   and `[Diecast] {agent} | goal: {slug}` is emitted inline by `_launch_agent`,
   not by a separate helper, and is truncated to 80 chars.)
- TestContinuationFileDelivery -> TestContinueAgentRun | US1.S10, FR-001
  (Three methods, security-relevant assertion FIRST per design-review flag.
   ``continue_agent_run`` (`agent_service.py:2039-2064`) is exercised under a
   mocked ``_get_tmux()`` returning a ``MagicMock``; ``session_exists`` toggles
   between alive/missing across cases. The security-relevant test pins the
   contract that the ``tmux.send_keys`` payload is exactly ``Read
   <continuation-path> and follow its instructions.`` and that the message
   body — proxied here by the ``EVIL_INJECTION_TOKEN`` sentinel — never leaks
   into the tmux send-keys stream (terminal-injection guardrail). Missing-
   session case asserts the raised ``ValueError`` carries the substring
   ``"no longer exists"`` so callers can distinguish the "use trigger_agent
   for a new run" branch.)
- TestPromptFileCleanup -> TestFinalizeCleanup | US1.S5, FR-001
  (Two methods, one per finalizer entry point — `_finalize_run` (sync,
   `agent_service.py:1702`) and `_finalize_run_from_monitor` (async,
   `agent_service.py:2520`). Pre-creates the four-file inventory
   (`.delegation`, `.prompt`, `.continue`, `.output.json`) and asserts the
   cleanup contract on BOTH paths. Divergence between the two finalizers is
   intentionally surfaced as a Gate B / sp4b candidate, not papered over.)
- TestNoInlineEnforcement -> TestPreambleAntiInline | US1.S7, FR-001
  (Diecast pins the verbatim anti-inline phrase ``"CRITICAL: NEVER inline an
   agent's work yourself."`` emitted by ``_universal_anti_inline``
   (`agent_service.py:1294-1311`). Block emits iff ``allowed_delegations`` is
   non-empty; absent for both ``[]`` and ``None``. Justified deviation: if the
   second-brain wording differs, the test pins the diecast phrase verbatim — the
   test IS the contract.)
- TestDelegationInstructionInPrompt -> TestPromptBuilder | US1.S7, FR-001
  (Delegation-instruction line ``"Your allowed_delegations: [...]"`` emits iff
   ``allowed_delegations`` is non-empty. Co-located with the interactive-block
   parametrization in TestPromptBuilder so a single class covers both
   conditional preamble blocks.)
- TestInteractivePromptBlock -> TestPromptBuilder | US1.S8, FR-001
  (``INTERACTIVE SESSION`` block emits iff ``interactive=True``. See above.)
- TestMixedTransportPreambleHarness -> TestMixedTransportPreamble | US1.S9, SC-004, FR-001
  (SC-004 invariant: when ``allowed_delegations`` mixes HTTP and subagent
   children, BOTH dispatch blocks emit, the anti-inline phrase appears EXACTLY
   ONCE, and each child name is whole-word-scoped to its own block via
   ``\b<name>\b`` regex (NOT substring ``in``). Substring matching was the bug
   second-brain hit historically; the regex form is non-negotiable. Block
   carving uses ``HTTP-dispatched delegations:`` / ``Subagent-dispatched
   delegations:`` as anchors — the diecast block headers, pinned verbatim.)

## Diecast-only additions (no second-brain counterpart)

- TestDispatchModeValidator (sp2.3) -- pins agent_config.py:36-41 silent fallback
- TestExternalProjectDirPrecondition (sp3.1) -- US2.S3, US2.S7, FR-002.
    Existing precondition cases (validate-raises, trigger-raises, route-422,
    launch-raises, malformed-context-422) already covered in
    cast-server/tests/test_dispatch_precondition.py:
      - test_validate_raises_when_goal_has_no_external_project_dir
      - test_validate_raises_when_external_project_dir_path_missing
      - test_validate_passes_when_external_project_dir_exists
      - test_trigger_agent_raises_before_enqueue_when_precondition_fails
      - test_trigger_route_returns_422_with_structured_payload
      - test_trigger_route_returns_422_when_path_missing
      - test_trigger_route_succeeds_when_external_project_dir_set
      - test_launch_agent_raises_when_external_project_dir_unset
      - test_trigger_returns_422_on_malformed_delegation_context
    Cross-checked under integration env vars (CAST_DISABLE_SERVER=1,
    CAST_DELEGATION_BACKOFF_OVERRIDE, CAST_DELEGATION_IDLE_TIMEOUT_SECONDS) —
    11 passed in 2.83s, no regressions. New methods added here pin the
    Diecast-only cases the existing suite does NOT cover:
      - test_depth4_dispatch_returns_422_before_row_create (US2.S7 — the
        depth-3 chain test in TestDelegationDepthEnforcement asserts the
        ValueError; this method ADDS the row-count-invariance assertion that
        proves the depth check fires BEFORE create_agent_run is reached).
      - test_invoke_route_does_not_422 (the `/invoke` carve-out preserved —
        invoke_agent intentionally skips _validate_dispatch_preconditions so
        CLI invocation works on goals without external_project_dir).
- TestOutputJsonContractV2 (sp3.2) -- US2.S4-S6, FR-002.
    Three methods covering the v2-specific contracts:
      - test_non_terminal_status_treated_as_malformed (US2.S4) — parametrized
        over ["pending", "running", "idle"]: synthesizes a child output.json
        with a non-terminal status, drives ``_finalize_run_from_monitor``,
        asserts parent finalizes with status="failed" AND error_message
        contains a parse-error marker. Currently RED: ``AgentOutput.status``
        is typed ``str`` (NOT ``Literal[...]``), so non-terminal values pass
        Pydantic validation and ``_finalize_run`` propagates them verbatim
        — Phase 4 / sp4c candidate (no xfail per US2).
      - test_next_steps_bare_string_fails_schema (US2.S5) — pure-unit
        validator pin: a ``next_steps`` entry as a bare string fails the
        US14 typed schema at ``cast-server/tests/fixtures/next_steps.schema.json``.
        Schema is test-only for now per resolved open question; promotion
        to ``cast_server/contracts/`` deferred to sp4d.
      - test_untagged_open_questions_flagged (US2.S6) — synthesizes a
        child output.json whose ``human_action_items[]`` contain entries
        without an ``[EXTERNAL]`` or ``[USER-DEFERRED]`` tag prefix and
        drives ``_finalize_run_from_monitor``; asserts the violation is
        surfaced (status="failed" + parse-error). The production validator
        for US13 untagged-tag enforcement DOES NOT yet exist (grep for
        `EXTERNAL` / `USER-DEFERRED` in ``cast_server/`` returns zero
        matches at sp3.2 authoring time) — the test is in the
        "expected red until sp4c authors it" state. NO xfail markers per
        US2; the test IS the contract.
- TestMtimeHeartbeatRoundTrip (sp3.3) -- US2.S1, FR-002.
    EXPECTED RED until sp4a; NO xfail per US2 — the test IS the contract.
    The diecast polling primitive is ``_monitor_loop`` (agent_service.py:2347)
    calling ``_check_all_agents`` (line 2360) once per ``AGENT_MONITOR_INTERVAL``
    via ``await asyncio.sleep(AGENT_MONITOR_INTERVAL)`` (line 2356). The test
    semantically equates one ``_check_all_agents`` call to one tick (the
    function the loop body sleeps BETWEEN), wraps it with a counting
    monkeypatch, drives one tick with no output (parent must NOT transition),
    writes the child's ``output.json`` (the write stamps mtime = now), then
    drives a single follow-up tick and asserts the parent reaches
    ``completed``/``failed`` within ≤1 tick. If the test happens to PASS at
    first try, that's a Gate B Option C signal (no parent-stall symptom in
    the basic file-detection path) — surface to the user.
- TestSubagentOnlyPreamble (sp6.1) -- US4.S2, FR-005.
    Three methods covering the subagent-only dispatch shape:
      - test_subagent_only_emits_subagent_block — verbatim header
        ``"Subagent-dispatched delegations:"`` + named target appears, and
        the universal anti-inline rule (``"CRITICAL: NEVER inline an agent's
        work yourself."``) fires because ``allowed_delegations`` is
        non-empty (US1.S7 invariant preserved across all dispatch mixes).
      - test_subagent_only_omits_http_block — HTTP block header
        ``"HTTP-dispatched delegations:"`` AND the curl quick-reference
        anchors (``"Quick reference (full patterns in the skill):"`` /
        ``"CHILD_RUN_ID=$(curl"``) are ABSENT. The API-routes preamble
        emits an unrelated ``"Health check: curl ..."`` line so plain
        ``"curl"`` is ambiguous; pin the dispatch-curl substring instead.
      - test_subagent_only_includes_structured_return_contract — the
        pass-through / no-summarize phrase
        ``"Never summarize the subagent's output. Return its verdict/report
        structurally (pass-through)."`` is pinned verbatim from
        ``_subagent_dispatch_rules`` (`agent_service.py:1332-1352`). This
        contract is what distinguishes subagent dispatch from HTTP
        dispatch at the prompt level.
    Builder-unit-test layer (T1) only — subagent live E2E is explicitly
    out of scope per spec; manual exercise lives in
    ``cast-server/tests/MANUAL_SUBAGENT_CHECKLIST.md`` (sp6.2).

## Test-environment expectations (FR-003)

This module runs under:
    CAST_DISABLE_SERVER=1
    CAST_DELEGATION_BACKOFF_OVERRIDE=10ms,20ms,50ms
    CAST_DELEGATION_IDLE_TIMEOUT_SECONDS=4

Wall-clock budget: <30s for the full module (including failing tests pre-Phase-4).
Per-test pytest-timeout=5 enforced via cast-server/tests/integration/pytest.ini.

Registry discovery: CAST_TEST_AGENTS_DIR seam (set by conftest.py).

NO Python imports of `requests`, `httpx`, `urllib` (FR-008).
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
CAST_SERVER_DIR = REPO_ROOT / "cast-server"
if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))


# ---------------------------------------------------------------------------
# Helpers + per-test env fixture
# ---------------------------------------------------------------------------


def _insert_goal(db_path: Path, slug: str, external_project_dir: str | None,
                 goals_dir: Path | None = None) -> None:
    """Insert a goal row and ensure the on-disk goal directory exists.

    `_launch_agent` writes the prompt under ``GOALS_DIR/<slug>/`` and
    `ensure_cast_symlink` resolves ``GOALS_DIR/<slug>`` — both fail loud if
    the directory is missing.
    """
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT OR REPLACE INTO goals "
            "(slug, title, status, created_at, folder_path, external_project_dir) "
            "VALUES (?, ?, 'accepted', '2026-04-30T00:00:00+00:00', ?, ?)",
            (slug, slug, slug, external_project_dir),
        )
        conn.commit()
    finally:
        conn.close()
    if goals_dir is not None:
        (goals_dir / slug).mkdir(parents=True, exist_ok=True)


@pytest.fixture
def env(monkeypatch, tmp_path):
    """Hermetic per-test env: fresh DB + goals dir + an existing
    ``external_project_dir`` so ``_validate_dispatch_preconditions`` passes.
    """
    pytest.importorskip("cast_server.config")

    goals_dir = tmp_path / "goals"
    goals_dir.mkdir()
    db_path = tmp_path / "test.db"
    ext_project = tmp_path / "ext-project"
    ext_project.mkdir()

    from cast_server import config as _config
    monkeypatch.setattr(_config, "DB_PATH", db_path)
    monkeypatch.setattr(_config, "GOALS_DIR", goals_dir)

    from cast_server.db import connection as _connection
    monkeypatch.setattr(_connection, "DB_PATH", db_path)

    from cast_server.services import agent_service
    monkeypatch.setattr(agent_service, "GOALS_DIR", goals_dir)
    # Eliminate the post-prompt sleep so each test stays under the 5s budget.
    monkeypatch.setattr(agent_service, "AGENT_SENDKEY_DELAY", 0)

    from cast_server.db.connection import init_db
    init_db(db_path)

    return {
        "db_path": db_path,
        "goals_dir": goals_dir,
        "tmp_path": tmp_path,
        "ext_project": ext_project,
    }


# ---------------------------------------------------------------------------
# US1.S2 — Allowlist validation (TestDelegationValidation, part 1)
# ---------------------------------------------------------------------------


class TestAllowlistValidation:
    """`trigger_agent` enforces ``parent.allowed_delegations`` before enqueueing."""

    def _stub_config(self, monkeypatch, configs: dict):
        from cast_server.services import agent_service
        from cast_server.models.agent_config import AgentConfig

        def fake_load(name: str) -> AgentConfig:
            if name in configs:
                return configs[name]
            return AgentConfig(agent_id=name)

        monkeypatch.setattr(agent_service, "load_agent_config", fake_load)

    def test_allowed_delegation_succeeds(self, env, monkeypatch):
        from cast_server.services import agent_service
        from cast_server.models.agent_config import AgentConfig

        _insert_goal(env["db_path"], "g1", str(env["ext_project"]), env["goals_dir"])
        parent_id = agent_service.create_agent_run(
            "cast-test-parent-delegator", "g1", None, None,
            db_path=env["db_path"],
        )
        agent_service.update_agent_run(
            parent_id, status="running", db_path=env["db_path"],
        )

        self._stub_config(monkeypatch, {
            "cast-test-parent-delegator": AgentConfig(
                agent_id="cast-test-parent-delegator",
                allowed_delegations=["cast-test-child-worker"],
            ),
            "cast-test-child-worker": AgentConfig(
                agent_id="cast-test-child-worker", allowed_delegations=[],
            ),
        })

        child_id = asyncio.run(agent_service.trigger_agent(
            "cast-test-child-worker", "g1",
            parent_run_id=parent_id, db_path=env["db_path"],
        ))
        child = agent_service.get_agent_run(child_id, db_path=env["db_path"])
        assert child is not None
        assert child["parent_run_id"] == parent_id
        assert child["status"] == "pending"

    def test_disallowed_delegation_raises(self, env, monkeypatch):
        from cast_server.services import agent_service
        from cast_server.models.agent_config import AgentConfig

        _insert_goal(env["db_path"], "g2", str(env["ext_project"]), env["goals_dir"])
        parent_id = agent_service.create_agent_run(
            "cast-test-parent-delegator", "g2", None, None,
            db_path=env["db_path"],
        )
        agent_service.update_agent_run(
            parent_id, status="running", db_path=env["db_path"],
        )

        # Parent only allows the worker; we attempt to dispatch a different
        # target that is NOT in the allowlist.
        self._stub_config(monkeypatch, {
            "cast-test-parent-delegator": AgentConfig(
                agent_id="cast-test-parent-delegator",
                allowed_delegations=["cast-test-child-worker"],
            ),
        })

        with pytest.raises(ValueError) as exc:
            asyncio.run(agent_service.trigger_agent(
                "cast-test-other-target", "g2",
                parent_run_id=parent_id, db_path=env["db_path"],
            ))
        msg = str(exc.value)
        assert "not allowed to delegate" in msg
        assert "cast-test-other-target" in msg


# ---------------------------------------------------------------------------
# US1.S3 — Depth enforcement at trigger (TestDelegationValidation, part 2)
# ---------------------------------------------------------------------------


class TestDelegationDepthEnforcement:
    """`trigger_agent` rejects the 4th hop in a parent → child chain."""

    def test_max_depth_enforced(self, env, monkeypatch):
        from cast_server.services import agent_service
        from cast_server.models.agent_config import AgentConfig

        _insert_goal(env["db_path"], "g3", str(env["ext_project"]), env["goals_dir"])

        # Build a chain run0 → run1 → run2 → run3 directly via create_agent_run
        # (bypasses the allowlist/depth checks in trigger_agent so we can stage
        # the depth-3 starting state).
        run0 = agent_service.create_agent_run(
            "cast-test-parent-delegator", "g3", None, None, db_path=env["db_path"],
        )
        run1 = agent_service.create_agent_run(
            "cast-test-child-worker", "g3", None, None,
            parent_run_id=run0, db_path=env["db_path"],
        )
        run2 = agent_service.create_agent_run(
            "cast-test-child-worker", "g3", None, None,
            parent_run_id=run1, db_path=env["db_path"],
        )
        run3 = agent_service.create_agent_run(
            "cast-test-child-worker", "g3", None, None,
            parent_run_id=run2, db_path=env["db_path"],
        )

        # Allowlist passes so the depth check is the failure cause.
        from cast_server.models.agent_config import AgentConfig as _AC
        cfg = _AC(
            agent_id="cast-test-child-worker",
            allowed_delegations=["cast-test-child-worker"],
        )
        monkeypatch.setattr(
            agent_service, "load_agent_config", lambda _name: cfg,
        )

        with pytest.raises(ValueError) as exc:
            asyncio.run(agent_service.trigger_agent(
                "cast-test-child-worker", "g3",
                parent_run_id=run3, db_path=env["db_path"],
            ))
        assert "Max delegation depth" in str(exc.value)


# ---------------------------------------------------------------------------
# US1.S3 — Depth math primitive (TestDelegationValidation, part 3)
# ---------------------------------------------------------------------------


class TestDepthCalculation:
    """Pure-function coverage for ``_get_delegation_depth``.

    Mocks the run-row fetcher so the test does not depend on any DB shape
    beyond a parent_run_id field. (Override applies via monkeypatch on the
    public seam ``agent_service.get_agent_run``.)
    """

    def _wire_chain(self, monkeypatch, chain: dict[str, str | None]):
        from cast_server.services import agent_service

        def fake_get_agent_run(run_id: str, db_path=None):
            if run_id not in chain:
                return None
            return {"id": run_id, "parent_run_id": chain[run_id]}

        monkeypatch.setattr(agent_service, "get_agent_run", fake_get_agent_run)

    def test_top_level_run_has_depth_zero(self, monkeypatch):
        from cast_server.services.agent_service import _get_delegation_depth
        self._wire_chain(monkeypatch, {"r0": None})
        assert _get_delegation_depth("r0") == 0

    def test_child_run_has_depth_one(self, monkeypatch):
        from cast_server.services.agent_service import _get_delegation_depth
        self._wire_chain(monkeypatch, {"r0": None, "r1": "r0"})
        assert _get_delegation_depth("r1") == 1

    def test_grandchild_has_depth_two(self, monkeypatch):
        from cast_server.services.agent_service import _get_delegation_depth
        self._wire_chain(monkeypatch, {"r0": None, "r1": "r0", "r2": "r1"})
        assert _get_delegation_depth("r2") == 2

    def test_safety_break_caps_walk_at_max_plus_one(self, monkeypatch):
        """Cyclic / pathological chains must NOT spin forever."""
        from cast_server.services import agent_service
        from cast_server.services.agent_service import (
            MAX_DELEGATION_DEPTH, _get_delegation_depth,
        )

        # Self-pointing parent — exercises the depth > MAX_DELEGATION_DEPTH+1
        # safety break.
        def fake_get_agent_run(run_id: str, db_path=None):
            return {"id": run_id, "parent_run_id": run_id}

        monkeypatch.setattr(agent_service, "get_agent_run", fake_get_agent_run)
        depth = _get_delegation_depth("loop")
        assert depth <= MAX_DELEGATION_DEPTH + 2


# ---------------------------------------------------------------------------
# US1.S1 — Child launch isolation (TestChildLaunchTmuxIsolation)
# ---------------------------------------------------------------------------


class TestChildLaunchIsolation:
    """Children get their OWN tmux session, not a split inside the parent's."""

    def _launch_with_mocks(self, env, monkeypatch, run_id, config):
        from cast_server.services import agent_service
        from cast_server.models.agent_config import AgentConfig as _AC

        mock_tmux = MagicMock()
        mock_tmux.wait_for_ready.return_value = True
        monkeypatch.setattr(agent_service, "_get_tmux", lambda: mock_tmux)
        monkeypatch.setattr(
            agent_service, "load_agent_config",
            lambda name: config if name == config.agent_id else _AC(agent_id=name),
        )

        asyncio.run(agent_service._launch_agent(run_id, db_path=env["db_path"]))
        return mock_tmux

    def test_child_creates_own_session(self, env, monkeypatch):
        from cast_server.services import agent_service
        from cast_server.models.agent_config import AgentConfig

        _insert_goal(env["db_path"], "g4", str(env["ext_project"]), env["goals_dir"])
        parent_id = agent_service.create_agent_run(
            "cast-test-parent-delegator", "g4", None, None,
            db_path=env["db_path"],
        )
        agent_service.update_agent_run(
            parent_id, status="running", db_path=env["db_path"],
        )
        child_id = agent_service.create_agent_run(
            "cast-test-child-worker", "g4", None, None,
            parent_run_id=parent_id, db_path=env["db_path"],
        )

        cfg = AgentConfig(agent_id="cast-test-child-worker", model="haiku")
        mock_tmux = self._launch_with_mocks(env, monkeypatch, child_id, cfg)

        # Own session, not a pane split. Session name binds to the CHILD run id,
        # never to the parent's.
        mock_tmux.create_session.assert_called_once()
        session_name = mock_tmux.create_session.call_args[0][0]
        assert session_name == f"agent-{child_id}"
        assert f"agent-{parent_id}" not in session_name

        # Child gets a terminal (diecast uses open_terminal for both child and
        # parent — see equivalence-map docstring divergence note).
        mock_tmux.open_terminal.assert_called_once()
        # Readiness check + prompt delivery happened.
        mock_tmux.wait_for_ready.assert_called_once()
        mock_tmux.send_keys.assert_called()

    def test_top_level_creates_session_keyed_to_own_run(self, env, monkeypatch):
        from cast_server.services import agent_service
        from cast_server.models.agent_config import AgentConfig

        _insert_goal(env["db_path"], "g5", str(env["ext_project"]), env["goals_dir"])
        run_id = agent_service.create_agent_run(
            "cast-test-parent-delegator", "g5", None, None,
            db_path=env["db_path"],
        )

        cfg = AgentConfig(agent_id="cast-test-parent-delegator", model="haiku")
        mock_tmux = self._launch_with_mocks(env, monkeypatch, run_id, cfg)

        mock_tmux.create_session.assert_called_once()
        assert mock_tmux.create_session.call_args[0][0] == f"agent-{run_id}"
        mock_tmux.open_terminal.assert_called_once()

    def test_launch_prompt_uses_routed_context_dir_and_runtime_output_path(
        self, env, monkeypatch,
    ):
        from cast_server.services import agent_service, goal_service
        from cast_server.models.agent_config import AgentConfig

        slug = "g_prompt_ctx"
        _insert_goal(env["db_path"], slug, str(env["ext_project"]), env["goals_dir"])
        goal_service.update_config(
            slug,
            external_project_dir=str(env["ext_project"]),
            goals_dir=env["goals_dir"],
            db_path=env["db_path"],
        )
        routed_dir = env["ext_project"] / "docs" / "goal" / slug
        (routed_dir / "notes.ai.md").write_text("# Notes\n\nContext body\n")

        run_id = agent_service.create_agent_run(
            "cast-test-parent-delegator", slug, None, None,
            db_path=env["db_path"],
        )

        cfg = AgentConfig(
            agent_id="cast-test-parent-delegator",
            model="haiku",
            context_mode="lightweight",
        )
        self._launch_with_mocks(env, monkeypatch, run_id, cfg)
        prompt_path = env["goals_dir"] / slug / f".agent-{run_id}.prompt"
        assert prompt_path.exists()
        prompt = prompt_path.read_text()

        assert f"Read {routed_dir}/.context-map.md for goal context overview." in prompt
        assert f"write this exact JSON structure to {env['ext_project']}/.cast/.agent-{run_id}.output.json" in prompt


# ---------------------------------------------------------------------------
# Terminal title formatting (TestPtyxisTitleFormatting → TestTerminalTitleFormatting)
# ---------------------------------------------------------------------------


class TestTerminalTitleFormatting:
    """`_launch_agent` builds prefixed, 80-char-truncated terminal titles."""

    def _launch_with_mocks(self, env, monkeypatch, run_id, config):
        from cast_server.services import agent_service
        from cast_server.models.agent_config import AgentConfig as _AC

        mock_tmux = MagicMock()
        mock_tmux.wait_for_ready.return_value = True
        monkeypatch.setattr(agent_service, "_get_tmux", lambda: mock_tmux)
        monkeypatch.setattr(
            agent_service, "load_agent_config",
            lambda name: config if name == config.agent_id else _AC(agent_id=name),
        )
        asyncio.run(agent_service._launch_agent(run_id, db_path=env["db_path"]))
        return mock_tmux

    def test_child_title_has_child_prefix_and_agent_name(self, env, monkeypatch):
        from cast_server.services import agent_service
        from cast_server.models.agent_config import AgentConfig

        _insert_goal(env["db_path"], "g6", str(env["ext_project"]), env["goals_dir"])
        parent_id = agent_service.create_agent_run(
            "cast-test-parent-delegator", "g6", None, None,
            db_path=env["db_path"],
        )
        agent_service.update_agent_run(
            parent_id, status="running", db_path=env["db_path"],
        )
        child_id = agent_service.create_agent_run(
            "cast-test-child-worker", "g6", None, None,
            parent_run_id=parent_id, db_path=env["db_path"],
        )

        cfg = AgentConfig(agent_id="cast-test-child-worker", model="haiku")
        mock_tmux = self._launch_with_mocks(env, monkeypatch, child_id, cfg)

        title = mock_tmux.open_terminal.call_args[1].get("title", "")
        assert title.startswith("[Child]")
        assert "cast-test-child-worker" in title

    def test_top_level_title_has_diecast_prefix_and_goal(self, env, monkeypatch):
        from cast_server.services import agent_service
        from cast_server.models.agent_config import AgentConfig

        _insert_goal(env["db_path"], "g7", str(env["ext_project"]), env["goals_dir"])
        run_id = agent_service.create_agent_run(
            "cast-test-parent-delegator", "g7", None, None,
            db_path=env["db_path"],
        )

        cfg = AgentConfig(agent_id="cast-test-parent-delegator", model="haiku")
        mock_tmux = self._launch_with_mocks(env, monkeypatch, run_id, cfg)

        title = mock_tmux.open_terminal.call_args[1].get("title", "")
        assert title.startswith("[Diecast]")
        assert "cast-test-parent-delegator" in title
        assert "g7" in title

    def test_long_title_truncated_to_80_chars(self, env, monkeypatch):
        import json as _json
        from cast_server.services import agent_service
        from cast_server.models.agent_config import AgentConfig

        _insert_goal(env["db_path"], "g8", str(env["ext_project"]), env["goals_dir"])
        parent_id = agent_service.create_agent_run(
            "cast-test-parent-delegator", "g8", None, None,
            db_path=env["db_path"],
        )
        agent_service.update_agent_run(
            parent_id, status="running", db_path=env["db_path"],
        )
        child_id = agent_service.create_agent_run(
            "cast-test-child-worker", "g8", None, None,
            parent_run_id=parent_id, db_path=env["db_path"],
        )
        # Force a long task_title so the composed title would exceed 80 chars
        # before the truncation slice.
        agent_service.update_agent_run(
            child_id,
            input_params=_json.dumps({"task_title": "A" * 100}),
            db_path=env["db_path"],
        )

        cfg = AgentConfig(agent_id="cast-test-child-worker", model="haiku")
        mock_tmux = self._launch_with_mocks(env, monkeypatch, child_id, cfg)

        title = mock_tmux.open_terminal.call_args[1].get("title", "")
        assert len(title) <= 80


# ---------------------------------------------------------------------------
# US1.S4 — DelegationContext file (TestDelegationContext)
# ---------------------------------------------------------------------------


class TestDelegationContextFile:
    """`trigger_agent` writes ``.delegation-<run_id>.json`` BEFORE returning,
    and the JSON echoes the verbatim ``DelegationContext`` model fields.
    """

    def _build_context(self, parent_run_id: str, output_dir: str):
        from cast_server.models.delegation import (
            DelegationContext, DelegationContextData, DelegationOutputConfig,
        )
        return DelegationContext(
            agent_name="cast-test-child-worker",
            goal_slug="g_ctx",
            parent_run_id=parent_run_id,
            instructions="Do the thing",
            context=DelegationContextData(
                goal_title="Test Goal",
                goal_phase="execution",
                relevant_artifacts=["/abs/path/spec.md"],
                prior_output="prior summary",
                constraints=["read-only"],
            ),
            output=DelegationOutputConfig(
                output_dir=output_dir,
                expected_artifacts=["report.md"],
                contract_version="2.0",
            ),
        )

    def test_context_file_present_during_downstream_log(self, env, monkeypatch):
        """Monkeypatch interception: when `trigger_agent`'s tail-end
        ``logger.info`` runs, the file is already on disk. Proves
        write-before-return without injecting a hook into ``trigger_agent``.
        """
        from cast_server.services import agent_service
        from cast_server.models.agent_config import AgentConfig

        _insert_goal(env["db_path"], "g_ctx", str(env["ext_project"]),
                     env["goals_dir"])
        parent_id = agent_service.create_agent_run(
            "cast-test-parent-delegator", "g_ctx", None, None,
            db_path=env["db_path"],
        )
        agent_service.update_agent_run(
            parent_id, status="running", db_path=env["db_path"],
        )

        monkeypatch.setattr(
            agent_service, "load_agent_config",
            lambda _name: AgentConfig(
                agent_id="cast-test-parent-delegator",
                allowed_delegations=["cast-test-child-worker"],
            ),
        )

        deleg = self._build_context(parent_id, str(env["goals_dir"] / "g_ctx"))
        goal_dir = env["goals_dir"] / "g_ctx"

        # Downstream-symbol monkeypatch: spy on logger.info — called AFTER the
        # file write but BEFORE `trigger_agent` returns. The "Enqueued agent
        # run …" log is the canonical tail-end emission.
        snapshots: list[bool] = []
        real_info = agent_service.logger.info

        def info_spy(msg, *args, **kwargs):
            if isinstance(msg, str) and "Enqueued" in msg:
                files = list(goal_dir.glob(".delegation-*.json"))
                snapshots.append(bool(files))
            return real_info(msg, *args, **kwargs)

        monkeypatch.setattr(agent_service.logger, "info", info_spy)

        child_id = asyncio.run(agent_service.trigger_agent(
            "cast-test-child-worker", "g_ctx",
            parent_run_id=parent_id,
            delegation_context=deleg,
            db_path=env["db_path"],
        ))

        # The downstream log fired AT LEAST once with the file already on disk.
        assert snapshots, "trigger_agent did not emit the 'Enqueued' log"
        assert all(snapshots), (
            "delegation context file was missing during the downstream log "
            "callback — write-before-return invariant violated"
        )
        # Sanity: the file is still there post-return.
        assert (goal_dir / f".delegation-{child_id}.json").exists()

    def test_context_file_json_shape_is_verbatim(self, env, monkeypatch):
        """`agent_name`, `parent_run_id`, `context.*`, `output.*` round-trip
        into the on-disk JSON without rewriting or normalization.
        """
        from cast_server.services import agent_service
        from cast_server.models.agent_config import AgentConfig

        _insert_goal(env["db_path"], "g_ctx", str(env["ext_project"]),
                     env["goals_dir"])
        parent_id = agent_service.create_agent_run(
            "cast-test-parent-delegator", "g_ctx", None, None,
            db_path=env["db_path"],
        )
        agent_service.update_agent_run(
            parent_id, status="running", db_path=env["db_path"],
        )
        monkeypatch.setattr(
            agent_service, "load_agent_config",
            lambda _name: AgentConfig(
                agent_id="cast-test-parent-delegator",
                allowed_delegations=["cast-test-child-worker"],
            ),
        )

        output_dir = str(env["goals_dir"] / "g_ctx")
        deleg = self._build_context(parent_id, output_dir)

        child_id = asyncio.run(agent_service.trigger_agent(
            "cast-test-child-worker", "g_ctx",
            parent_run_id=parent_id,
            delegation_context=deleg,
            db_path=env["db_path"],
        ))

        context_file = env["goals_dir"] / "g_ctx" / f".delegation-{child_id}.json"
        data = json.loads(context_file.read_text())

        assert data["agent_name"] == "cast-test-child-worker"
        assert data["parent_run_id"] == parent_id
        assert data["instructions"] == "Do the thing"

        ctx = data["context"]
        assert ctx["goal_title"] == "Test Goal"
        assert ctx["goal_phase"] == "execution"
        assert ctx["relevant_artifacts"] == ["/abs/path/spec.md"]
        assert ctx["prior_output"] == "prior summary"
        assert ctx["constraints"] == ["read-only"]

        out = data["output"]
        assert out["output_dir"] == output_dir
        assert out["expected_artifacts"] == ["report.md"]
        assert out["contract_version"] == "2.0"


# ---------------------------------------------------------------------------
# US1.S6 — result_summary populate / None / 300-truncate (TestResultSummary)
# ---------------------------------------------------------------------------


def _write_output_json(goal_dir: Path, run_id: str, payload: dict) -> Path:
    out_file = goal_dir / f".agent-{run_id}.output.json"
    out_file.write_text(json.dumps(payload))
    return out_file


def _agent_output_envelope(**overrides) -> dict:
    base = {
        "contract_version": "2",
        "agent_name": "cast-test-child-worker",
        "task_title": "Test",
        "status": "completed",
        "summary": "ok",
        "artifacts": [],
        "errors": [],
        "next_steps": [],
        "started_at": "2026-05-01T00:00:00+00:00",
        "completed_at": "2026-05-01T00:00:01+00:00",
    }
    base.update(overrides)
    return base


def _drive_finalize_from_monitor(env, monkeypatch, run_id: str) -> None:
    """Run `_finalize_run_from_monitor` for an existing DB run, with side-effect
    helpers patched to no-op so the call stays hermetic.
    """
    from cast_server.services import agent_service
    from cast_server.models.agent_config import AgentConfig

    monkeypatch.setattr(
        agent_service, "load_agent_config",
        lambda _name: AgentConfig(agent_id="cast-test-child-worker"),
    )

    async def _noop_cleanup(_session_name):
        return None

    monkeypatch.setattr(agent_service, "_cleanup_parent_session", _noop_cleanup)

    run = agent_service.get_agent_run(run_id, db_path=env["db_path"])
    asyncio.run(
        agent_service._finalize_run_from_monitor(run, db_path=env["db_path"])
    )


class TestResultSummary:
    """`_finalize_run_from_monitor` populates `agent_runs.result_summary` from
    the child's ``output.summary`` (truncated to 300 chars; ``None`` when the
    output yields no usable summary).
    """

    def _seed_running_run(self, env, slug: str) -> str:
        from cast_server.services import agent_service
        _insert_goal(env["db_path"], slug, str(env["ext_project"]),
                     env["goals_dir"])
        run_id = agent_service.create_agent_run(
            "cast-test-child-worker", slug, None, None, db_path=env["db_path"],
        )
        agent_service.update_agent_run(
            run_id, status="running",
            started_at="2026-05-01T00:00:00+00:00",
            db_path=env["db_path"],
        )
        return run_id

    def test_populated_summary_under_300(self, env, monkeypatch):
        from cast_server.services import agent_service

        run_id = self._seed_running_run(env, "g_rs1")
        goal_dir = env["goals_dir"] / "g_rs1"
        summary_text = "A" * 50
        _write_output_json(goal_dir, run_id,
                           _agent_output_envelope(summary=summary_text))

        _drive_finalize_from_monitor(env, monkeypatch, run_id)

        run = agent_service.get_agent_run(run_id, db_path=env["db_path"])
        assert run["result_summary"] == summary_text
        assert len(run["result_summary"]) == 50

    def test_missing_summary_yields_none(self, env, monkeypatch):
        """Output JSON without a usable ``summary`` field leaves
        ``result_summary`` as None.

        The contract: `_finalize_run` only assigns ``result_summary`` when the
        parsed output has a truthy ``summary`` (line 1786-1790). Omitting the
        required ``summary`` key fails `AgentOutput` validation, which in turn
        leaves ``output_data`` as ``None`` so the populate-block is skipped.
        """
        from cast_server.services import agent_service

        run_id = self._seed_running_run(env, "g_rs2")
        goal_dir = env["goals_dir"] / "g_rs2"

        # Construct an envelope WITHOUT the required ``summary`` field.
        envelope = _agent_output_envelope()
        del envelope["summary"]
        _write_output_json(goal_dir, run_id, envelope)

        _drive_finalize_from_monitor(env, monkeypatch, run_id)

        run = agent_service.get_agent_run(run_id, db_path=env["db_path"])
        assert run["result_summary"] is None

    def test_summary_over_300_is_truncated(self, env, monkeypatch):
        from cast_server.services import agent_service

        run_id = self._seed_running_run(env, "g_rs3")
        goal_dir = env["goals_dir"] / "g_rs3"
        long_summary = "B" * 350
        _write_output_json(goal_dir, run_id,
                           _agent_output_envelope(summary=long_summary))

        _drive_finalize_from_monitor(env, monkeypatch, run_id)

        run = agent_service.get_agent_run(run_id, db_path=env["db_path"])
        assert run["result_summary"] is not None
        assert len(run["result_summary"]) == 300
        assert run["result_summary"] == long_summary[:300]


# ---------------------------------------------------------------------------
# US1.S5 — Finalizer cleanup invariant across BOTH entry points
# ---------------------------------------------------------------------------


class TestFinalizeCleanup:
    """Per ``docs/specs/cast-delegation-contract.collab.md`` §Cleanup contract,
    finalization must delete ``.delegation-<id>.json``, ``.agent-<id>.prompt``,
    and ``.agent-<id>.continue`` while retaining ``.agent-<id>.output.json``.

    Two methods — one per finalizer entry point. If they diverge, that IS the
    bug (Gate B candidate for sp4b cleanup-contract drift). DO NOT paper over.
    """

    def _seed_run_and_files(self, env, slug: str) -> tuple[str, Path, dict[str, Path]]:
        from cast_server.services import agent_service

        _insert_goal(env["db_path"], slug, str(env["ext_project"]),
                     env["goals_dir"])
        run_id = agent_service.create_agent_run(
            "cast-test-child-worker", slug, None, None, db_path=env["db_path"],
        )
        agent_service.update_agent_run(
            run_id, status="running",
            started_at="2026-05-01T00:00:00+00:00",
            db_path=env["db_path"],
        )

        goal_dir = env["goals_dir"] / slug
        files = {
            "delegation": goal_dir / f".delegation-{run_id}.json",
            "prompt": goal_dir / f".agent-{run_id}.prompt",
            "continue": goal_dir / f".agent-{run_id}.continue",
            "output": goal_dir / f".agent-{run_id}.output.json",
        }
        files["delegation"].write_text('{"agent_name": "x"}')
        files["prompt"].write_text("read this prompt")
        files["continue"].write_text("follow up message")
        files["output"].write_text(json.dumps(_agent_output_envelope()))
        return run_id, goal_dir, files

    def _assert_cleanup_contract(self, files: dict[str, Path]) -> None:
        assert not files["delegation"].exists(), (
            ".delegation-<id>.json was retained after finalization"
        )
        assert not files["prompt"].exists(), (
            ".agent-<id>.prompt was retained after finalization"
        )
        assert not files["continue"].exists(), (
            ".agent-<id>.continue was retained after finalization"
        )
        assert files["output"].exists(), (
            ".agent-<id>.output.json was deleted but the contract says it "
            "must be retained for parent polling"
        )

    def test_cleanup_via_finalize_run(self, env, monkeypatch):
        """Sync entry point at ``agent_service.py:1702``."""
        from cast_server.services import agent_service

        run_id, goal_dir, files = self._seed_run_and_files(env, "g_fin1")

        agent_service._finalize_run(
            run_id, goal_dir,
            agent_name="cast-test-child-worker",
            task_title="Test",
            started_at="2026-05-01T00:00:00+00:00",
            db_path=env["db_path"],
        )

        self._assert_cleanup_contract(files)

    def test_cleanup_via_finalize_run_from_monitor(self, env, monkeypatch):
        """Async entry point at ``agent_service.py:2520``."""
        run_id, goal_dir, files = self._seed_run_and_files(env, "g_fin2")

        _drive_finalize_from_monitor(env, monkeypatch, run_id)

        self._assert_cleanup_contract(files)


# ---------------------------------------------------------------------------
# US1.S7 — Anti-inline preamble block (TestNoInlineEnforcement)
# ---------------------------------------------------------------------------


def _build_prompt_with_modes(monkeypatch, *, allowed_delegations,
                              interactive: bool = False,
                              modes: dict[str, str] | None = None,
                              context_dir: str | None = None,
                              context_map_exists: bool = False,
                              context_mode: str = "full") -> str:
    """Call ``_build_agent_prompt`` with hermetic delegation-mode wiring.

    ``_build_agent_prompt`` calls ``_partition_delegations_by_mode`` which in
    turn invokes ``load_agent_config(name)`` for each delegation target.
    Tests monkeypatch the public ``agent_service.load_agent_config`` seam to
    pin per-target ``dispatch_mode`` deterministically (no fixture-config
    filesystem dependency in pure-function tests).
    """
    from cast_server.services import agent_service
    from cast_server.models.agent_config import AgentConfig

    mode_map = modes or {}

    def fake_load(name: str) -> AgentConfig:
        return AgentConfig(
            agent_id=name,
            dispatch_mode=mode_map.get(name, "http"),
            context_mode=context_mode,
        )

    monkeypatch.setattr(agent_service, "load_agent_config", fake_load)

    return agent_service._build_agent_prompt(
        agent_name="cast-test-parent",
        goal_title="Test Goal",
        task_title="Test Task",
        task_outcome="ship it",
        runtime_dir="/tmp/goal",
        run_id="run_xyz",
        start_time_iso="2026-05-01T00:00:00+00:00",
        interactive=interactive,
        goal_slug="g_preamble",
        allowed_delegations=allowed_delegations,
        context_dir=context_dir,
        context_map_exists=context_map_exists,
        context_mode=context_mode,
    )


class TestPreambleAntiInline:
    """The universal anti-inline rule (``_universal_anti_inline``) emits iff
    ``allowed_delegations`` is non-empty (US1.S7).

    Diecast verbatim phrase: ``"CRITICAL: NEVER inline an agent's work
    yourself."`` — pinned here because the test IS the contract.
    """

    def test_block_present_with_non_empty_allowlist(self, monkeypatch):
        out = _build_prompt_with_modes(
            monkeypatch, allowed_delegations=["cast-test-child"],
        )
        assert "CRITICAL: NEVER inline an agent's work yourself." in out
        # The named target appears in the block too.
        assert "cast-test-child" in out

    def test_block_absent_with_empty_allowlist(self, monkeypatch):
        out = _build_prompt_with_modes(monkeypatch, allowed_delegations=[])
        assert "CRITICAL: NEVER inline" not in out
        assert "Your allowed_delegations:" not in out

    def test_block_absent_with_none_allowlist(self, monkeypatch):
        out = _build_prompt_with_modes(monkeypatch, allowed_delegations=None)
        assert "CRITICAL: NEVER inline" not in out
        assert "Your allowed_delegations:" not in out


# ---------------------------------------------------------------------------
# US1.S7 + US1.S8 — Delegation-instruction + interactive blocks (TestPromptBuilder)
# ---------------------------------------------------------------------------


class TestPromptBuilder:
    """Conditional preamble blocks: interactive (US1.S8) and delegation
    instruction (US1.S7).

    Both are independent toggles on ``_build_agent_prompt`` — covered via
    parametrize so a single class pins both invariants.
    """

    @pytest.mark.parametrize("interactive", [True, False])
    def test_interactive_block_emits_iff_interactive_true(
        self, monkeypatch, interactive,
    ):
        out = _build_prompt_with_modes(
            monkeypatch,
            allowed_delegations=[],
            interactive=interactive,
        )
        if interactive:
            assert "INTERACTIVE SESSION" in out
        else:
            assert "INTERACTIVE SESSION" not in out

    @pytest.mark.parametrize("delegations,expected_present", [
        (["cast-test-child"], True),
        (["a", "b"], True),
        ([], False),
        (None, False),
    ])
    def test_delegation_instruction_emits_iff_allowlist_non_empty(
        self, monkeypatch, delegations, expected_present,
    ):
        out = _build_prompt_with_modes(
            monkeypatch, allowed_delegations=delegations,
        )
        if expected_present:
            assert "Your allowed_delegations:" in out
        else:
            assert "Your allowed_delegations:" not in out

    def test_lightweight_context_map_uses_context_dir_while_output_json_stays_in_goal_dir(
        self, monkeypatch,
    ):
        out = _build_prompt_with_modes(
            monkeypatch,
            allowed_delegations=[],
            context_dir="/tmp/docs/goal/g_preamble",
            context_map_exists=True,
            context_mode="lightweight",
        )

        assert "Read /tmp/docs/goal/g_preamble/.context-map.md for goal context overview." in out
        assert "write this exact JSON structure to /tmp/goal/.agent-run_xyz.output.json" in out
        assert "Artifact paths must be relative to /tmp/goal." in out

    def test_full_context_block_labels_user_artifact_directory(self, monkeypatch):
        out = _build_prompt_with_modes(
            monkeypatch,
            allowed_delegations=[],
            context_dir="/tmp/docs/goal/g_preamble",
            context_map_exists=True,
            context_mode="full",
        )

        assert "Context instructions for this user-artifact directory (/tmp/docs/goal/g_preamble):" in out
        assert "For .ai.md files: read /tmp/docs/goal/g_preamble/.context-map.md first" in out


# ---------------------------------------------------------------------------
# US1.S9 / SC-004 — Mixed-transport preamble invariant (TestMixedTransportPreambleHarness)
# ---------------------------------------------------------------------------


class TestMixedTransportPreamble:
    """SC-004 invariant: with HTTP and subagent children both in the
    allowlist, BOTH dispatch blocks emit, the anti-inline phrase appears
    exactly once, and each child name is whole-word-scoped to its own block
    via ``\\b<name>\\b`` regex (NOT substring ``in``).

    Substring matching is the bug second-brain hit historically. The regex
    form is non-negotiable per plan §sp2.3 — the test pins it verbatim.

    Block headers ``HTTP-dispatched delegations:`` and ``Subagent-dispatched
    delegations:`` are pinned verbatim as the carving anchors.
    """

    HTTP_NAME = "cast-test-http-only"
    SUBAGENT_NAME = "cast-test-subagent-only"

    def _mixed_prompt(self, monkeypatch) -> str:
        return _build_prompt_with_modes(
            monkeypatch,
            allowed_delegations=[self.HTTP_NAME, self.SUBAGENT_NAME],
            modes={
                self.HTTP_NAME: "http",
                self.SUBAGENT_NAME: "subagent",
            },
        )

    def test_both_blocks_emit_with_mixed_transport(self, monkeypatch):
        out = self._mixed_prompt(monkeypatch)
        assert "HTTP-dispatched delegations:" in out
        assert "Subagent-dispatched delegations:" in out

    def test_anti_inline_phrase_appears_exactly_once(self, monkeypatch):
        """SC-004 explicit assertion — the universal anti-inline rule
        emits ONCE, not per dispatch block.
        """
        out = self._mixed_prompt(monkeypatch)
        assert out.count("NEVER inline an agent's work") == 1

    def test_child_names_scoped_to_their_blocks_via_word_boundary(
        self, monkeypatch,
    ):
        import re

        out = self._mixed_prompt(monkeypatch)

        # Carve the prompt into the two dispatch-rule sections using the
        # block-header anchors. HTTP runs from its header to the start of the
        # subagent header; subagent runs from its header to end-of-string.
        http_block_match = re.search(
            r"HTTP-dispatched delegations:[\s\S]*?(?=Subagent-dispatched delegations:|$)",
            out,
        )
        subagent_block_match = re.search(
            r"Subagent-dispatched delegations:[\s\S]*$", out,
        )
        assert http_block_match is not None, "HTTP block missing"
        assert subagent_block_match is not None, "Subagent block missing"

        http_block = http_block_match.group()
        subagent_block = subagent_block_match.group()

        # Each child name is whole-word-matched inside its own block...
        assert re.search(rf"\b{re.escape(self.HTTP_NAME)}\b", http_block), (
            "HTTP child name missing from HTTP block"
        )
        assert re.search(rf"\b{re.escape(self.SUBAGENT_NAME)}\b", subagent_block), (
            "Subagent child name missing from subagent block"
        )
        # ...and is NOT present in the other block (whole-word regex form,
        # not substring `in`). Names are deliberately non-overlapping so the
        # \b boundaries are meaningful for hyphenated identifiers.
        assert not re.search(
            rf"\b{re.escape(self.HTTP_NAME)}\b", subagent_block,
        ), "HTTP child name leaked into subagent block (SC-004 violation)"
        assert not re.search(
            rf"\b{re.escape(self.SUBAGENT_NAME)}\b", http_block,
        ), "Subagent child name leaked into HTTP block (SC-004 violation)"


# ---------------------------------------------------------------------------
# Diecast-only — AgentConfig.dispatch_mode silent-fallback pin (Review #8 / US2)
# ---------------------------------------------------------------------------


class TestDispatchModeValidator:
    """Pin the intentional silent-fallback semantics of
    ``AgentConfig.dispatch_mode`` (`agent_config.py:36-41`).

    The validator coerces unknown values to ``"http"`` rather than raising —
    a deliberate ``str + validator`` design choice (NOT a strict
    ``Literal[...]`` annotation). Future "fix the typo handling" changes will
    fail these tests loudly. The test IS the documentation.
    """

    def test_valid_subagent_preserved(self):
        from cast_server.models.agent_config import AgentConfig

        cfg = AgentConfig(
            agent_id="x",
            dispatch_mode="subagent",
            allowed_delegations=[],
            model="haiku",
            trust_level="readonly",
        )
        assert cfg.dispatch_mode == "subagent"

    def test_valid_http_preserved(self):
        from cast_server.models.agent_config import AgentConfig

        cfg = AgentConfig(
            agent_id="x",
            dispatch_mode="http",
            allowed_delegations=[],
            model="haiku",
            trust_level="readonly",
        )
        assert cfg.dispatch_mode == "http"

    def test_typo_falls_back_to_http_silently(self):
        """Intentional silent fallback — a typo'd dispatch_mode is coerced
        to ``"http"`` rather than raising. Sibling fields MUST be preserved
        (NOT degraded to defaults), distinguishing this ``str + validator``
        shape from a strict ``Literal[...]`` annotation.
        """
        from cast_server.models.agent_config import AgentConfig

        cfg = AgentConfig(
            agent_id="x",
            dispatch_mode="subagnet",  # intentional typo
            allowed_delegations=["a", "b"],
            model="haiku",
            trust_level="readonly",
        )
        assert cfg.dispatch_mode == "http"
        # Sibling fields must round-trip unchanged, not collapse to defaults.
        assert cfg.allowed_delegations == ["a", "b"]
        assert cfg.model == "haiku"
        assert cfg.trust_level == "readonly"


# ---------------------------------------------------------------------------
# US1.S10 — continue_agent_run: continuation file + Read-path tmux delivery
# ---------------------------------------------------------------------------


class TestContinueAgentRun:
    """SECURITY-RELEVANT (US1.S10): the tmux instruction MUST NOT contain the
    message body.

    ``continue_agent_run`` (`agent_service.py:2039-2064`) writes the message
    verbatim to ``GOALS_DIR/<slug>/.agent-<run_id>.continue`` and then sends a
    single ``tmux.send_keys`` instruction of the form ``"Read <path> and follow
    its instructions."`` — the path, NOT the message body. Pasting arbitrary
    message text into the terminal opens a terminal-injection attack surface
    (control sequences, typed-shell commands, etc.). The first test in this
    class is the security guardrail. Do not water it down.

    The missing-session case raises ``ValueError`` with substring
    ``"no longer exists"`` — callers rely on this to distinguish "use
    trigger_agent for a new run" from genuine errors.
    """

    EVIL_INJECTION_TOKEN = "EVIL_INJECTION_TOKEN_8a3f"

    def _seed_running_run(self, env, slug: str) -> str:
        from cast_server.services import agent_service

        _insert_goal(env["db_path"], slug, str(env["ext_project"]),
                     env["goals_dir"])
        run_id = agent_service.create_agent_run(
            "cast-test-child-worker", slug, None, None, db_path=env["db_path"],
        )
        agent_service.update_agent_run(
            run_id, status="idle",
            started_at="2026-05-01T00:00:00+00:00",
            db_path=env["db_path"],
        )
        return run_id

    def _install_mock_tmux(self, monkeypatch, *, session_alive: bool = True):
        from cast_server.services import agent_service

        mock_tmux = MagicMock()
        mock_tmux.session_exists.return_value = session_alive
        sent_calls: list[tuple[str, str]] = []
        mock_tmux.send_keys.side_effect = lambda session, payload: sent_calls.append(
            (session, payload),
        )
        monkeypatch.setattr(agent_service, "_get_tmux", lambda: mock_tmux)
        return mock_tmux, sent_calls

    def test_tmux_instruction_uses_read_path_not_message_body(self, env, monkeypatch):
        """SECURITY: tmux must see ``Read <continuation-file>``, NEVER the
        message body. Distinguishes file-delivery from paste-delivery (US1.S10).
        """
        from cast_server.services import agent_service

        run_id = self._seed_running_run(env, "g_cont_sec")
        _, sent_calls = self._install_mock_tmux(monkeypatch)

        asyncio.run(agent_service.continue_agent_run(
            run_id, message=self.EVIL_INJECTION_TOKEN, db_path=env["db_path"],
        ))

        assert sent_calls, "send_keys was never called"
        all_payload = "\n".join(payload for _, payload in sent_calls)
        assert "Read " in all_payload
        assert f".agent-{run_id}.continue" in all_payload
        # The security assertion: the message body MUST NOT leak into tmux.
        assert self.EVIL_INJECTION_TOKEN not in all_payload, (
            "Message body leaked into tmux send_keys payload — terminal "
            "injection guardrail violated (US1.S10)."
        )

    def test_message_written_to_continue_file(self, env, monkeypatch):
        from cast_server.services import agent_service

        run_id = self._seed_running_run(env, "g_cont_write")
        self._install_mock_tmux(monkeypatch)

        asyncio.run(agent_service.continue_agent_run(
            run_id, message="hello world", db_path=env["db_path"],
        ))

        cont_path = env["goals_dir"] / "g_cont_write" / f".agent-{run_id}.continue"
        assert cont_path.exists()
        assert cont_path.read_text() == "hello world"

    def test_missing_session_raises_value_error(self, env, monkeypatch):
        from cast_server.services import agent_service

        run_id = self._seed_running_run(env, "g_cont_miss")
        self._install_mock_tmux(monkeypatch, session_alive=False)

        with pytest.raises(ValueError, match="no longer exists"):
            asyncio.run(agent_service.continue_agent_run(
                run_id, message="m", db_path=env["db_path"],
            ))


# ---------------------------------------------------------------------------
# US2.S3 / US2.S7 — Diecast-only external_project_dir precondition (sp3.1)
# ---------------------------------------------------------------------------


def _count_agent_rows(db_path: Path, slug: str) -> int:
    """Row count for ``agent_runs`` filtered by goal slug."""
    conn = sqlite3.connect(str(db_path))
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM agent_runs WHERE goal_slug = ?", (slug,),
        ).fetchone()[0]
    finally:
        conn.close()


class TestExternalProjectDirPrecondition:
    """Diecast-only precondition checks (sp3.1).

    Existing precondition cases — validate-raises, trigger-raises,
    route-422, launch-raises, malformed-context-422 — already covered in
    ``cast-server/tests/test_dispatch_precondition.py`` (cited verbatim in
    the equivalence-map docstring at the top of this module). Those tests
    are cross-checked under the integration env vars at the start of sp3.1
    and remain green (11 passed in 2.83s); duplicating them here would
    violate FR-007's "no parallel suites" rule.

    The two methods below pin the cases the existing suite does NOT cover:

    * ``test_depth4_dispatch_returns_422_before_row_create`` (US2.S7) —
      asserts row-count INVARIANCE across the failed 4th dispatch. Pins
      the depth-check-before-insert ordering: the ValueError fires before
      ``create_agent_run`` is reached, so the agent_runs table sees zero
      net rows for the failed attempt.
    * ``test_invoke_route_does_not_422`` — pins the `/invoke` carve-out
      (cast-delegation-contract.collab.md §`/invoke` Carve-Out). The
      invoke entry point intentionally skips
      ``_validate_dispatch_preconditions`` so CLI invocation works on
      goals without an ``external_project_dir``. FR-008 forbids HTTP
      imports — the test drives ``invoke_agent`` directly via the service
      layer.
    """

    def test_depth4_dispatch_returns_422_before_row_create(self, env, monkeypatch):
        """US2.S7: the depth check fires BEFORE the row insert.

        Stages a chain run0 → run1 → run2 → run3 (depth-3 starting state)
        via direct ``create_agent_run`` calls (bypassing trigger_agent's
        own checks so we can pre-build the chain), then attempts the 4th
        dispatch. ``trigger_agent`` raises ``ValueError("Max delegation
        depth ...")``. The key assertion is row-count INVARIANCE across
        the failed dispatch — duplicating ``TestDelegationDepthEnforcement``
        on the exception alone would not pin US2.S7's ordering invariant.
        """
        from cast_server.services import agent_service
        from cast_server.models.agent_config import AgentConfig

        slug = "g_d4"
        _insert_goal(env["db_path"], slug, str(env["ext_project"]),
                     env["goals_dir"])

        run0 = agent_service.create_agent_run(
            "cast-test-parent-delegator", slug, None, None,
            db_path=env["db_path"],
        )
        run1 = agent_service.create_agent_run(
            "cast-test-child-worker", slug, None, None,
            parent_run_id=run0, db_path=env["db_path"],
        )
        run2 = agent_service.create_agent_run(
            "cast-test-child-worker", slug, None, None,
            parent_run_id=run1, db_path=env["db_path"],
        )
        run3 = agent_service.create_agent_run(
            "cast-test-child-worker", slug, None, None,
            parent_run_id=run2, db_path=env["db_path"],
        )

        # Allowlist passes so the depth check is the failure cause (the
        # allowlist check runs FIRST inside trigger_agent — at line 1889 —
        # so it must succeed for the depth check at line 1896 to fire).
        cfg = AgentConfig(
            agent_id="cast-test-child-worker",
            allowed_delegations=["cast-test-child-worker"],
        )
        monkeypatch.setattr(agent_service, "load_agent_config", lambda _name: cfg)

        rows_before = _count_agent_rows(env["db_path"], slug)
        assert rows_before == 4, (
            "fixture invariant: chain depth-3 should have produced 4 rows"
        )

        with pytest.raises(ValueError, match="Max delegation depth"):
            asyncio.run(agent_service.trigger_agent(
                "cast-test-child-worker", slug,
                parent_run_id=run3, db_path=env["db_path"],
            ))

        rows_after = _count_agent_rows(env["db_path"], slug)
        assert rows_after == rows_before, (
            f"agent_runs row count changed during failed dispatch: "
            f"{rows_before} -> {rows_after}. The depth check must fire "
            "BEFORE create_agent_run (US2.S7); a row created and then "
            "rolled back would still bump the auto-id sequence and risks "
            "leaking partial state."
        )

    def test_invoke_route_does_not_422(self, env, monkeypatch):
        """`/invoke` carve-out preserved (cast-delegation-contract.collab.md
        §`/invoke` Carve-Out).

        ``invoke_agent`` (cast-server/cast_server/services/agent_service.py:1940)
        intentionally does NOT call ``_validate_dispatch_preconditions`` —
        CLI invocation must work on goals that have no
        ``external_project_dir`` configured. Driven through the service
        layer (FR-008 forbids Python HTTP imports). If the carve-out
        regressed, this would raise ``MissingExternalProjectDirError``.
        """
        from cast_server.services import agent_service
        from cast_server.services.agent_service import (
            MissingExternalProjectDirError,
        )
        from cast_server.models.agent_config import AgentConfig

        slug = "g_invoke_carveout"
        # Goal explicitly has NO external_project_dir — the carve-out is
        # the only reason this should not 422.
        _insert_goal(env["db_path"], slug, None, env["goals_dir"])

        # Empty allowed_delegations skips invoke_agent's tmux session
        # creation branch, keeping the test hermetic.
        monkeypatch.setattr(
            agent_service, "load_agent_config",
            lambda _name: AgentConfig(
                agent_id="cast-test-child-worker", allowed_delegations=[],
            ),
        )

        try:
            result = asyncio.run(agent_service.invoke_agent(
                agent_name="cast-test-child-worker",
                goal_slug=slug,
                db_path=env["db_path"],
            ))
        except MissingExternalProjectDirError as exc:  # pragma: no cover
            pytest.fail(
                "/invoke must NOT enforce external_project_dir (carve-out "
                f"preserved): raised {exc!r}"
            )

        # Sanity: invoke_agent returned the documented shape — proves the
        # call actually reached the success path, not a different early
        # exit that masked the carve-out check.
        assert "run_id" in result
        assert "prompt" in result

    def test_invoke_prompt_uses_routed_context_dir_when_context_map_exists(
        self, env, monkeypatch,
    ):
        from cast_server.services import agent_service, goal_service
        from cast_server.models.agent_config import AgentConfig

        slug = "g_invoke_ctx"
        _insert_goal(env["db_path"], slug, str(env["ext_project"]), env["goals_dir"])
        goal_service.update_config(
            slug,
            external_project_dir=str(env["ext_project"]),
            goals_dir=env["goals_dir"],
            db_path=env["db_path"],
        )
        routed_dir = env["ext_project"] / "docs" / "goal" / slug
        (routed_dir / "notes.ai.md").write_text("# Notes\n\nContext body\n")

        monkeypatch.setattr(
            agent_service, "load_agent_config",
            lambda _name: AgentConfig(
                agent_id="cast-test-child-worker",
                allowed_delegations=[],
                context_mode="lightweight",
            ),
        )

        result = asyncio.run(agent_service.invoke_agent(
            agent_name="cast-test-child-worker",
            goal_slug=slug,
            db_path=env["db_path"],
        ))

        prompt = result["prompt"]
        assert f"Read {routed_dir}/.context-map.md for goal context overview." in prompt
        assert f"write this exact JSON structure to {env['goals_dir'] / slug}/.agent-{result['run_id']}.output.json" in prompt


# ---------------------------------------------------------------------------
# US2.S4 / US2.S5 / US2.S6 — Output JSON contract v2 conformance (sp3.2)
# ---------------------------------------------------------------------------

# jsonschema is a permitted dep (NOT requests/httpx/urllib — FR-008 only
# forbids HTTP clients).
jsonschema = pytest.importorskip("jsonschema")
ValidationError = jsonschema.ValidationError

NEXT_STEPS_SCHEMA = json.loads(
    Path(__file__).resolve().parents[1].joinpath(
        "fixtures/next_steps.schema.json"
    ).read_text()
)


class TestOutputJsonContractV2:
    """Output JSON contract v2 conformance: terminal status (US2.S4), US14
    typed ``next_steps`` shape (US2.S5), US13 untagged Open-Questions
    detection (US2.S6).

    Spec anchors:
    * ``docs/specs/cast-output-json-contract.collab.md`` §"Status Allowed
      Values" — non-terminal status in the file is a malformed-output bug;
      parent must treat as ``failed`` with a parse error.
    * Same spec §"Future extensions" — sp4c open-question tagging on
      ``human_action_items[]``; sp4d typed ``next_steps``. The schema fixture
      lives in ``cast-server/tests/fixtures/next_steps.schema.json`` and is
      test-only for now (resolved open question; promotion to
      ``cast_server/contracts/`` deferred).

    Two of the three methods are EXPECTED RED at authoring time and become
    Phase 4 inputs (no xfail per US2):
      * test_non_terminal_status_treated_as_malformed — production
        ``AgentOutput.status`` is typed ``str`` (not ``Literal``); non-terminal
        values pass validation today, so the parent does not finalize as
        ``failed``. sp4c candidate.
      * test_untagged_open_questions_flagged — no production validator for
        ``human_action_items`` tag prefixes exists yet (grep ``EXTERNAL`` /
        ``USER-DEFERRED`` in ``cast_server/`` returns zero matches at sp3.2
        authoring time). sp4c candidate.
    """

    @pytest.mark.parametrize("status", ["pending", "running", "idle"])
    def test_non_terminal_status_treated_as_malformed(
        self, env, monkeypatch, status,
    ):
        """US2.S4: a child output.json with a non-terminal status MUST be
        treated as malformed — parent finalizes ``failed`` with a parse-error
        marker on ``error_message``.

        EXPECTED RED at authoring time: ``AgentOutput.status`` is typed
        ``str`` (`cast_server/models/agent_output.py:23`), so Pydantic
        accepts non-terminal values and ``_finalize_run`` propagates them
        verbatim into ``agent_runs.status``. sp4c is responsible for
        tightening the model (or adding a post-parse guard) to flip this
        green. NO xfail per US2 — the test IS the contract.
        """
        from cast_server.services import agent_service

        slug = f"g_status_{status}"
        _insert_goal(env["db_path"], slug, str(env["ext_project"]),
                     env["goals_dir"])
        run_id = agent_service.create_agent_run(
            "cast-test-child-worker", slug, None, None, db_path=env["db_path"],
        )
        agent_service.update_agent_run(
            run_id, status="running",
            started_at="2026-05-01T00:00:00+00:00",
            db_path=env["db_path"],
        )
        goal_dir = env["goals_dir"] / slug
        _write_output_json(
            goal_dir, run_id,
            _agent_output_envelope(status=status),
        )

        _drive_finalize_from_monitor(env, monkeypatch, run_id)

        run = agent_service.get_agent_run(run_id, db_path=env["db_path"])
        assert run["status"] == "failed", (
            f"non-terminal status {status!r} in output.json must be treated "
            f"as malformed; parent finalized as {run['status']!r} instead. "
            "Per cast-output-json-contract.collab.md §Status Allowed Values, "
            "non-terminal status in the terminal-output file is a parse "
            "error. EXPECTED RED until sp4c tightens AgentOutput.status."
        )
        err_msg = run.get("error_message") or ""
        assert (
            "parse" in err_msg.lower()
            or "malformed" in err_msg.lower()
            or "status" in err_msg.lower()
        ), (
            "error_message must surface the parse-error nature of the "
            f"non-terminal status; got {err_msg!r}."
        )

    def test_next_steps_bare_string_fails_schema(self):
        """US2.S5: a ``next_steps`` entry as a bare string fails the US14
        typed schema. Pure-unit validator pin — no DB, no env required.

        The schema lives at
        ``cast-server/tests/fixtures/next_steps.schema.json`` and pins the
        per-entry shape ``{command, rationale, artifact_anchor}`` per
        cast-output-json-contract.collab.md §Future extensions sp4d.
        """
        bad_payload = ["just a bare string, not the typed shape"]
        with pytest.raises(ValidationError):
            jsonschema.validate(instance=bad_payload, schema=NEXT_STEPS_SCHEMA)

        # Sanity: a typed entry passes — proves the schema isn't a pathological
        # always-fail.
        good_payload = [{
            "command": "cast-runs recheck <id>",
            "rationale": "Re-run after the fix lands",
            "artifact_anchor": "docs/plan/sp4c.md#L42",
        }]
        jsonschema.validate(instance=good_payload, schema=NEXT_STEPS_SCHEMA)

    def test_untagged_open_questions_flagged(self, env, monkeypatch):
        """US2.S6: ``human_action_items[]`` containing an entry without an
        ``[EXTERNAL]`` or ``[USER-DEFERRED]`` tag prefix is a contract
        violation per US13 (cast-output-json-contract.collab.md §Future
        extensions sp4c). Parent must surface the violation by finalizing
        ``failed`` with a parse-error marker.

        EXPECTED RED at authoring time: no production validator for
        human_action_items tag prefixes exists yet — ``grep -r 'EXTERNAL\\|
        USER-DEFERRED' cast-server/cast_server/`` returns zero matches.
        sp4c is responsible for adding the validator and flipping this green.
        NO xfail per US2 — the test IS the contract.
        """
        from cast_server.services import agent_service

        slug = "g_oq_untagged"
        _insert_goal(env["db_path"], slug, str(env["ext_project"]),
                     env["goals_dir"])
        run_id = agent_service.create_agent_run(
            "cast-test-child-worker", slug, None, None, db_path=env["db_path"],
        )
        agent_service.update_agent_run(
            run_id, status="running",
            started_at="2026-05-01T00:00:00+00:00",
            db_path=env["db_path"],
        )
        goal_dir = env["goals_dir"] / slug

        # Untagged entry — no [EXTERNAL] or [USER-DEFERRED] prefix.
        _write_output_json(
            goal_dir, run_id,
            _agent_output_envelope(
                status="completed",
                human_action_needed=True,
                human_action_items=[
                    "Resolve the open question about XYZ",  # untagged
                ],
            ),
        )

        _drive_finalize_from_monitor(env, monkeypatch, run_id)

        run = agent_service.get_agent_run(run_id, db_path=env["db_path"])
        assert run["status"] == "failed", (
            "untagged human_action_items entry must surface as a contract "
            "violation per US13; parent finalized as "
            f"{run['status']!r} instead. EXPECTED RED until sp4c authors "
            "the validator (grep EXTERNAL/USER-DEFERRED in cast_server/ "
            "returns zero matches at sp3.2 authoring time)."
        )
        err_msg = run.get("error_message") or ""
        assert (
            "tag" in err_msg.lower()
            or "open question" in err_msg.lower()
            or "human_action" in err_msg.lower()
            or "external" in err_msg.lower()
            or "user-deferred" in err_msg.lower()
        ), (
            "error_message must surface the untagged-Open-Questions "
            f"contract violation; got {err_msg!r}."
        )


# ---------------------------------------------------------------------------
# US2.S1 — Heartbeat-by-mtime round-trip (EXPECTED RED until sp4a)
# ---------------------------------------------------------------------------


class TestMtimeHeartbeatRoundTrip:
    """US2.S1: parent observes the child's ``output.json`` mtime within
    ≤1 polling-tick.

    EXPECTED RED until sp4a flips it green. NO ``xfail`` marker — US2
    explicitly disallows xfail at goal exit; the test exists to convert
    the parent-stall vibe into a concrete signal.

    The diecast polling primitive is ``_monitor_loop`` (agent_service.py:2347)
    calling ``_check_all_agents`` (line 2360) once per ``AGENT_MONITOR_INTERVAL``
    via ``await asyncio.sleep`` (line 2356). Each call to
    ``_check_all_agents`` IS one tick; the file-canonical heartbeat signal
    is the ``output_file.exists()`` branch inside ``_handle_state_transition``
    (line 2421) — once on disk, the parent must finalize within the next tick.

    Mock targets (locked):
      - ``agent_service._get_tmux`` -> MagicMock with idle pane content +
        session_exists=True
      - ``agent_service.detect_agent_state`` -> AgentState.IDLE (so the
        finalize-eligible branch fires)
      - ``agent_service.load_agent_config`` -> default AgentConfig
      - ``agent_service._cleanup_parent_session`` -> async no-op (avoid the
        leaked ``asyncio.create_task`` reaching real tmux)

    Per cast-delegation-contract.collab.md §Heartbeat-by-mtime, this is the
    ≤1-tick contract. If this happens to PASS at first try, that's a Gate B
    Option C signal (no parent-stall symptom in the basic file-detection
    path) — surface to the user; do NOT introduce xfail.
    """

    def test_parent_observes_child_mtime_within_one_tick(
        self, env, monkeypatch,
    ):
        """Pre-create a running parent run, drive ``_check_all_agents``
        once with no output.json (parent must NOT transition), synthesize
        the child finalize (write output.json — the act of writing sets
        mtime to "now"), drive a single follow-up ``_check_all_agents``
        and assert the parent reaches a terminal state.

        Tick semantics: each top-level ``_check_all_agents`` invocation is
        one tick. The contract is ≤1 tick after the mtime update.
        """
        from cast_server.services import agent_service
        from cast_server.models.agent_config import AgentConfig
        from cast_server.infra.state_detection import AgentState

        slug = "g_mtime_heartbeat"
        _insert_goal(env["db_path"], slug, str(env["ext_project"]),
                     env["goals_dir"])
        run_id = agent_service.create_agent_run(
            "cast-test-child-worker", slug, None, None,
            db_path=env["db_path"],
        )
        agent_service.update_agent_run(
            run_id, status="running",
            started_at="2026-05-01T00:00:00+00:00",
            db_path=env["db_path"],
        )

        # Hermetic finalize path.
        monkeypatch.setattr(
            agent_service, "load_agent_config",
            lambda _name: AgentConfig(agent_id="cast-test-child-worker"),
        )

        async def _noop_cleanup(_session_name):
            return None

        monkeypatch.setattr(
            agent_service, "_cleanup_parent_session", _noop_cleanup,
        )

        # tmux: agent appears idle, session is alive.
        session_name = f"agent-{run_id}"
        tmux_mock = MagicMock()
        tmux_mock.list_all_pane_commands.return_value = {session_name: "claude"}
        tmux_mock.capture_pane.return_value = []
        tmux_mock.session_exists.return_value = True
        monkeypatch.setattr(agent_service, "_get_tmux", lambda: tmux_mock)

        # Force IDLE so _handle_state_transition checks output_file.
        monkeypatch.setattr(
            agent_service, "detect_agent_state",
            lambda _pane_content, _pane_cmd: AgentState.IDLE,
        )

        # Tick counter — wraps the polling primitive used by _monitor_loop.
        # Each call to _check_all_agents is exactly one tick (the function
        # the loop body sleeps between).
        ticks_observed: list[float] = []
        original_check = agent_service._check_all_agents

        async def counting_check(*args, **kwargs):
            ticks_observed.append(1.0)
            return await original_check(*args, **kwargs)

        monkeypatch.setattr(
            agent_service, "_check_all_agents", counting_check,
        )

        # ---- Tick 0: no output yet — parent MUST NOT transition. ----
        asyncio.run(
            agent_service._check_all_agents(db_path=env["db_path"])
        )
        run_pre = agent_service.get_agent_run(
            run_id, db_path=env["db_path"],
        )
        assert run_pre["status"] == "running", (
            f"parent transitioned to {run_pre['status']!r} BEFORE the child "
            "wrote output.json — the file-canonical heartbeat contract "
            "requires the file to exist on disk before finalize fires."
        )
        ticks_before_write = len(ticks_observed)

        # ---- Child finalize: write output.json. The write itself stamps
        # mtime = now, which IS the heartbeat instant per spec. ----
        goal_dir = env["goals_dir"] / slug
        out_file = _write_output_json(
            goal_dir, run_id, _agent_output_envelope(),
        )
        assert out_file.exists(), "fixture write must succeed"

        # ---- Single follow-up tick: parent SHOULD reach terminal. ----
        asyncio.run(
            agent_service._check_all_agents(db_path=env["db_path"])
        )
        ticks_after_write = len(ticks_observed) - ticks_before_write

        run_post = agent_service.get_agent_run(
            run_id, db_path=env["db_path"],
        )
        assert run_post["status"] in ("completed", "failed"), (
            "parent did not transition to terminal within 1 tick after the "
            f"child's mtime update; status={run_post['status']!r}. "
            "Per cast-delegation-contract.collab.md §Heartbeat-by-mtime, "
            "the parent must observe the child's output.json mtime within "
            "≤1 polling-tick. EXPECTED RED until sp4a converts the "
            "parent-stall symptom into a green test."
        )
        assert ticks_after_write <= 1, (
            f"parent took {ticks_after_write} ticks to transition; spec "
            "says ≤1. EXPECTED RED until sp4a."
        )


# ---------------------------------------------------------------------------
# US4.S2 — Subagent-only preamble (TestSubagentOnlyPreamble, sp6.1)
# ---------------------------------------------------------------------------


class TestSubagentOnlyPreamble:
    """US4.S2 / FR-005: when ``allowed_delegations`` contains ONLY a
    subagent-mode target, ``_build_agent_prompt`` emits the Subagent-dispatch
    block with the structured-return / no-summarize contract, AND does NOT
    emit the HTTP-dispatch block or its curl/poll quick reference.

    Builder-unit-test layer (T1). Subagent live-exercise is covered out-of-band
    via ``cast-server/tests/MANUAL_SUBAGENT_CHECKLIST.md`` (sp6.2); the
    automated subagent E2E is explicitly out of scope per spec.

    Phrases pinned verbatim from ``agent_service._subagent_dispatch_rules``
    (`agent_service.py:1332-1352`), ``_http_dispatch_rules``
    (`agent_service.py:1314-1329`), and ``_quick_reference_curl``
    (`agent_service.py:1355-1391`):

    - Subagent block header: ``"Subagent-dispatched delegations:"``
    - Pass-through verdict / no-summarize contract:
      ``"Never summarize the subagent's output. Return its verdict/report "``
      ``"structurally (pass-through)."``
    - HTTP block header (must be ABSENT):
      ``"HTTP-dispatched delegations:"``
    - HTTP curl quick-reference anchor (must be ABSENT):
      ``"Quick reference (full patterns in the skill):"`` and the
      ``"CHILD_RUN_ID=$(curl"`` substring (the API-routes preamble emits a
      separate ``"Health check: curl ..."`` line, so plain ``"curl"`` is
      ambiguous — pin the dispatch-curl marker instead).
    """

    SUBAGENT_NAME = "cast-test-child-worker-subagent"

    def _subagent_only_prompt(self, monkeypatch) -> str:
        return _build_prompt_with_modes(
            monkeypatch,
            allowed_delegations=[self.SUBAGENT_NAME],
            modes={self.SUBAGENT_NAME: "subagent"},
        )

    def test_subagent_only_emits_subagent_block(self, monkeypatch):
        """Subagent block header + named target appear in the prompt."""
        out = self._subagent_only_prompt(monkeypatch)
        assert "Subagent-dispatched delegations:" in out
        assert self.SUBAGENT_NAME in out
        # Anti-inline rule fires whenever allowed_delegations is non-empty
        # (US1.S7), regardless of dispatch mix.
        assert "CRITICAL: NEVER inline an agent's work yourself." in out

    def test_subagent_only_omits_http_block(self, monkeypatch):
        """HTTP-dispatch block header AND curl quick-reference are absent."""
        out = self._subagent_only_prompt(monkeypatch)
        assert "HTTP-dispatched delegations:" not in out
        # The curl/poll quick reference is keyed on http_targets being
        # non-empty (`_quick_reference_curl` is invoked only then). Pin both
        # the canonical anchor phrase and the curl-trigger substring.
        assert "Quick reference (full patterns in the skill):" not in out
        assert "CHILD_RUN_ID=$(curl" not in out

    def test_subagent_only_includes_structured_return_contract(
        self, monkeypatch,
    ):
        """The pass-through verdict / no-summarize contract is pinned verbatim
        in the subagent block — distinguishes subagent dispatch from HTTP
        dispatch (where the parent would synthesize a final summary instead).
        """
        out = self._subagent_only_prompt(monkeypatch)
        assert (
            "Never summarize the subagent's output. Return its verdict/report"
            in out
        )
        assert "structurally (pass-through)" in out
