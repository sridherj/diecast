"""Rate-limit auto-restart regression test.

Phase 3b sp6 (Diecast OSS). Locks Q#18 / T1 — mock at the narrowest
implementation boundary, never at ``subprocess.Popen``.

Implementation map (full version: ``cast-server/docs/test-rate-limit-recovery.md``):

* Detection: ``cast_server.infra.state_detection.detect_agent_state``
  returns ``AgentState.RATE_LIMITED`` when pane content matches one of
  ``RATE_LIMIT_PRIMARY`` regexes.
* Reset-time parsing: ``cast_server.infra.rate_limit_parser.parse_rate_limit_reset``
  extracts a resume datetime from the captured pane text. Falls back to
  ``now + 15min`` (``FALLBACK_COOLDOWN_MINUTES``) when no reset pattern
  matches.
* Auto-restart fires in ``cast_server.services.agent_service._handle_state_transition``
  in the ``state == AgentState.RATE_LIMITED`` branch. The dispatcher does
  **not** re-spawn a subprocess — it sends a literal ``Enter`` to the
  still-running Claude tmux pane via ``TmuxSessionManager.send_enter``.

The mocks below patch the state-detection function and the tmux singleton;
``parse_rate_limit_reset`` is exercised end-to-end on real pane text in the
positive case so the test asserts the real parser-derived value flows through
the dispatcher's bookkeeping. The negative case calls the parser directly to
confirm the 15-minute fallback contract still holds.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta

import pytest

from cast_server.infra.rate_limit_parser import (
    FALLBACK_COOLDOWN_MINUTES,
    parse_rate_limit_reset,
)
from cast_server.infra.state_detection import AgentState
from cast_server.services import agent_service

from tests.conftest import make_running_run

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_run(db_path, run_id):
    return agent_service.get_agent_run(run_id, db_path=db_path)


def _patch_states(monkeypatch, sequence):
    """Patch ``detect_agent_state`` to return ``sequence`` values in order.

    ``_check_all_agents`` calls ``detect_agent_state`` once per running
    agent per tick. The test wants a deterministic state sequence
    independent of whatever pane regexes happen to match the canned text.
    """
    iterator = iter(sequence)

    def fake_detect(pane_content, pane_command):
        try:
            return next(iterator)
        except StopIteration:
            # Any tick beyond the scripted sequence keeps the agent IDLE so
            # the dispatcher does not flap. IDLE alone never finalises a run
            # because no .done / .output.json file is written in this test.
            return AgentState.IDLE

    monkeypatch.setattr(agent_service, "detect_agent_state", fake_detect)


# ---------------------------------------------------------------------------
# Positive path
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_rate_limit_auto_restart_returns_to_running(
    monkeypatch, isolated_db, fake_tmux,
):
    """Tick 1 detects rate limit; tick 2 (after cooldown) resumes the run.

    Asserts the run transitions ``running → rate_limited → running`` without
    manual intervention, that the dispatcher used the parser-derived wait,
    that ``send_enter`` was the resume primitive, and that the pause was
    persisted to ``agent_runs.rate_limit_pauses``.
    """
    run_id = make_running_run(isolated_db)
    session_name = f"agent-{run_id}"

    # Pane text the parser can read: "try again in 1 min" → resume in
    # 1 + BUFFER_MINUTES (2) = 3 minutes from "now". The exact value is what
    # the dispatcher must store in _cooldown_until.
    rate_limited_pane = [
        "you've hit your limit",
        "try again in 1 min",
    ]
    fake_tmux.list_all_pane_commands.return_value = {session_name: "claude"}
    fake_tmux.capture_pane.return_value = rate_limited_pane

    # Tick 1: RATE_LIMITED. Tick 2: RATE_LIMITED again (cooldown will have
    # been forced to the past via _cooldown_until below, so the dispatcher
    # treats it as expired and resumes).
    _patch_states(monkeypatch, [AgentState.RATE_LIMITED, AgentState.RATE_LIMITED])

    before_first_tick = datetime.now()

    asyncio.run(agent_service._check_all_agents(db_path=isolated_db))

    # Assert tick 1 outcome.
    run = _get_run(isolated_db, run_id)
    assert run["status"] == "rate_limited", (
        "first detection should flip status to rate_limited"
    )
    assert run_id in agent_service._cooldown_until, (
        "first detection should seed _cooldown_until"
    )
    assert run_id in agent_service._current_pause, (
        "first detection should seed _current_pause"
    )

    cooldown = agent_service._cooldown_until[run_id]

    # The wait value must come from parse_rate_limit_reset on the real pane
    # text. "try again in 1 min" + BUFFER_MINUTES (2) = ~3 minutes ahead.
    expected_wait_minutes = 3
    delta_minutes = (cooldown - before_first_tick).total_seconds() / 60
    assert (expected_wait_minutes - 0.5) <= delta_minutes <= (expected_wait_minutes + 0.5), (
        f"dispatcher stored cooldown ~{delta_minutes:.2f}min ahead, "
        f"expected ~{expected_wait_minutes}min from parse_rate_limit_reset"
    )
    # send_enter must NOT have fired yet — agent is still cooling down.
    assert fake_tmux.send_enter.call_count == 0

    # Force the cooldown into the past so tick 2 triggers the resume branch.
    agent_service._cooldown_until[run_id] = datetime.now() - timedelta(seconds=1)

    asyncio.run(agent_service._check_all_agents(db_path=isolated_db))

    # Tick 2 outcome: status flipped back to running, send_enter fired,
    # pause appended, bookkeeping cleared.
    run = _get_run(isolated_db, run_id)
    assert run["status"] == "running", (
        "second tick after cooldown should flip status back to running"
    )

    fake_tmux.send_enter.assert_called_once_with(session_name)

    pauses = json.loads(run.get("rate_limit_pauses") or "[]")
    assert len(pauses) == 1, "exactly one pause should be persisted"
    pause = pauses[0]
    assert "started_at" in pause and "ended_at" in pause
    assert "reset_time_parsed" in pause
    assert pause.get("duration_seconds", -1) >= 0

    assert run_id not in agent_service._cooldown_until
    assert run_id not in agent_service._current_pause
    assert agent_service._total_paused.get(run_id, 0) == pause["duration_seconds"]


# ---------------------------------------------------------------------------
# Negative path — default backoff
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_default_backoff_when_no_explicit_wait():
    """Parser falls back to ``now + 15min`` when the message has no wait.

    This is the documented dispatcher contract: when the parser cannot
    extract a reset time, ``_cooldown_until[run_id]`` is set to whatever
    the parser returns, which is ``now + FALLBACK_COOLDOWN_MINUTES``.
    Asserting on the parser keeps the test focused on the contract that
    actually backs the dispatcher.
    """
    assert FALLBACK_COOLDOWN_MINUTES == 15, (
        "If this constant changed, update sp6 docs and dependent agents."
    )

    before = datetime.now()
    resume_at = parse_rate_limit_reset("you've hit your limit")
    after = datetime.now()

    # Parser returns ~now + 15min with no buffer for the fallback case.
    lower = before + timedelta(minutes=FALLBACK_COOLDOWN_MINUTES) - timedelta(seconds=1)
    upper = after + timedelta(minutes=FALLBACK_COOLDOWN_MINUTES) + timedelta(seconds=1)
    assert lower <= resume_at <= upper, (
        f"parse_rate_limit_reset returned {resume_at}; expected ~now + 15min "
        f"(allowed window {lower} … {upper})"
    )


@pytest.mark.integration
def test_dispatcher_uses_parser_default_for_unparseable_message(
    monkeypatch, isolated_db, fake_tmux,
):
    """End-to-end: dispatcher's stored cooldown matches the parser default.

    Companion to ``test_default_backoff_when_no_explicit_wait`` — the
    standalone parser test confirms the constant; this test confirms the
    dispatcher actually plumbs the parser's value into ``_cooldown_until``
    when the rate-limit pane text has no parseable wait.
    """
    run_id = make_running_run(isolated_db, run_id="rl-fallback-run")
    session_name = f"agent-{run_id}"

    fake_tmux.list_all_pane_commands.return_value = {session_name: "claude"}
    # Primary pattern matches; no reset pattern → parser hits fallback.
    fake_tmux.capture_pane.return_value = ["you've hit your limit"]

    _patch_states(monkeypatch, [AgentState.RATE_LIMITED])

    before = datetime.now()
    asyncio.run(agent_service._check_all_agents(db_path=isolated_db))
    after = datetime.now()

    run = _get_run(isolated_db, run_id)
    assert run["status"] == "rate_limited"

    cooldown = agent_service._cooldown_until[run_id]
    lower = before + timedelta(minutes=FALLBACK_COOLDOWN_MINUTES) - timedelta(seconds=1)
    upper = after + timedelta(minutes=FALLBACK_COOLDOWN_MINUTES) + timedelta(seconds=1)
    assert lower <= cooldown <= upper, (
        f"dispatcher stored cooldown {cooldown}; expected ~now + 15min "
        f"(allowed window {lower} … {upper})"
    )
