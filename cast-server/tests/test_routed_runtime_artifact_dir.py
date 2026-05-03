"""Regression tests for routed-run runtime artifact directory resolution.

Verifies that ``_resolve_runtime_artifact_dir`` returns the correct path
for both routed goals (with ``external_project_dir`` + ``folder_path``)
and non-routed goals, and that downstream functions
(``_handle_state_transition``, ``recheck_failed_run``, ``cancel_run``,
``continue_agent_run``, ``_finalize_run_from_monitor``,
``recover_stale_runs``) use it consistently so routed runs finalize from
the ``.cast`` target / ``folder_path`` location.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cast_server.db.connection import get_connection
from cast_server.services.agent_service import (
    _resolve_runtime_artifact_dir,
    _handle_state_transition,
    _finalize_run_from_monitor,
    cancel_run,
    continue_agent_run,
    create_agent_run,
    get_agent_run,
    recheck_failed_run,
    recover_stale_runs,
    update_agent_run,
)
from cast_server.infra.state_detection import AgentState

from tests.conftest import ensure_goal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_routed_goal(
    db_path: Path,
    tmp_path: Path,
    slug: str = "routed-goal",
    title: str = "Routed Goal",
) -> tuple[Path, Path]:
    """Create a routed goal: external_project_dir on disk + folder_path in DB.

    Returns (external_project_dir, folder_path) as Path objects.
    The folder_path directory is created on disk (simulating the .cast target).
    """
    ext_dir = tmp_path / "ext-project"
    ext_dir.mkdir(parents=True, exist_ok=True)
    folder = ext_dir / "docs" / "goal" / slug
    folder.mkdir(parents=True, exist_ok=True)

    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO goals "
            "(slug, title, folder_path, external_project_dir) "
            "VALUES (?, ?, ?, ?)",
            (slug, title, str(folder), str(ext_dir)),
        )
        conn.commit()
    finally:
        conn.close()
    return ext_dir, folder


def _ensure_nonrouted_goal(
    db_path: Path,
    goals_dir: Path,
    slug: str = "plain-goal",
    title: str = "Plain Goal",
) -> Path:
    """Create a non-routed goal (no external_project_dir)."""
    goal_dir = goals_dir / slug
    goal_dir.mkdir(parents=True, exist_ok=True)
    ensure_goal(db_path, slug=slug, title=title)
    return goal_dir


def _seed_running_run(
    db_path: Path,
    goal_slug: str,
    agent_name: str = "cast-test-agent",
    status: str = "running",
) -> str:
    """Insert a running agent_run and return its id."""
    rid = create_agent_run(
        agent_name=agent_name,
        goal_slug=goal_slug,
        task_id=None,
        input_params={"task_title": "test task"},
        status=status,
        db_path=db_path,
    )
    now = datetime.now(timezone.utc).isoformat()
    update_agent_run(rid, started_at=now, db_path=db_path)
    return rid


def _make_output_data(summary: str = "test summary") -> dict:
    """Build a valid contract-v2 output envelope."""
    return {
        "contract_version": "2",
        "agent_name": "cast-test-agent",
        "task_title": "test task",
        "status": "completed",
        "summary": summary,
        "artifacts": [],
        "errors": [],
        "next_steps": [],
        "human_action_needed": False,
        "human_action_items": [],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# _resolve_runtime_artifact_dir — unit tests
# ---------------------------------------------------------------------------

class TestResolveRuntimeArtifactDir:
    """Direct unit tests for the centralised resolver."""

    def test_routed_goal_returns_folder_path(self, isolated_db, tmp_path):
        """Routed goal → folder_path (the .cast symlink target)."""
        _ext_dir, folder = _ensure_routed_goal(isolated_db, tmp_path)
        result = _resolve_runtime_artifact_dir("routed-goal", db_path=isolated_db)
        assert result == folder

    def test_nonrouted_goal_returns_goals_dir_slug(self, isolated_db, tmp_path, monkeypatch):
        """Non-routed goal → GOALS_DIR / slug."""
        goals_dir = tmp_path / "goals"
        goals_dir.mkdir()
        import cast_server.services.agent_service as mod
        monkeypatch.setattr(mod, "GOALS_DIR", goals_dir)

        plain_dir = _ensure_nonrouted_goal(isolated_db, goals_dir, slug="plain-goal")
        result = _resolve_runtime_artifact_dir("plain-goal", db_path=isolated_db)
        assert result == plain_dir

    def test_routed_goal_empty_folder_path_falls_back(self, isolated_db, tmp_path, monkeypatch):
        """Routed goal with external_project_dir but empty folder_path → fallback."""
        goals_dir = tmp_path / "goals"
        goals_dir.mkdir()
        import cast_server.services.agent_service as mod
        monkeypatch.setattr(mod, "GOALS_DIR", goals_dir)

        ext_dir = tmp_path / "ext-project"
        ext_dir.mkdir()
        conn = get_connection(isolated_db)
        try:
            # folder_path NOT NULL — use empty string to simulate unset
            conn.execute(
                "INSERT OR REPLACE INTO goals "
                "(slug, title, folder_path, external_project_dir) "
                "VALUES (?, ?, ?, ?)",
                ("half-routed", "Half Routed", "", str(ext_dir)),
            )
            conn.commit()
        finally:
            conn.close()

        result = _resolve_runtime_artifact_dir("half-routed", db_path=isolated_db)
        # Empty folder_path is falsy → falls back to GOALS_DIR / slug
        assert result == goals_dir / "half-routed"

    def test_routed_goal_nonexistent_folder_path_falls_back(self, isolated_db, tmp_path, monkeypatch):
        """Routed goal whose folder_path doesn't exist on disk → fallback."""
        goals_dir = tmp_path / "goals"
        goals_dir.mkdir()
        import cast_server.services.agent_service as mod
        monkeypatch.setattr(mod, "GOALS_DIR", goals_dir)

        ext_dir = tmp_path / "ext-project"
        ext_dir.mkdir()
        conn = get_connection(isolated_db)
        try:
            conn.execute(
                "INSERT OR REPLACE INTO goals "
                "(slug, title, folder_path, external_project_dir) "
                "VALUES (?, ?, ?, ?)",
                ("stale-route", "Stale Route", "/nonexistent/path", str(ext_dir)),
            )
            conn.commit()
        finally:
            conn.close()

        result = _resolve_runtime_artifact_dir("stale-route", db_path=isolated_db)
        assert result == goals_dir / "stale-route"


# ---------------------------------------------------------------------------
# Routed recheck_failed_run — regression test
# ---------------------------------------------------------------------------

class TestRecheckFailedRunRouted:
    """Regression: recheck_failed_run must look in the routed folder_path."""

    def test_recheck_finalizes_from_routed_dir(self, isolated_db, tmp_path):
        """Write .agent-<id>.output.json into routed folder_path and prove
        recheck_failed_run picks it up."""
        _ext_dir, folder = _ensure_routed_goal(isolated_db, tmp_path)
        run_id = _seed_running_run(isolated_db, "routed-goal", status="failed")

        # Write output file in the routed folder_path
        output_file = folder / f".agent-{run_id}.output.json"
        output_file.write_text(json.dumps(_make_output_data("All done from routed dir")))

        result = recheck_failed_run(run_id, db_path=isolated_db)
        assert result is not None
        assert result["status"] == "completed"
        assert result["output"]["summary"] == "All done from routed dir"

    def test_recheck_finalizes_from_done_file_in_routed_dir(self, isolated_db, tmp_path):
        """A .done file (no output.json) in the routed dir should also trigger
        finalization (failed status, since no output.json)."""
        _ext_dir, folder = _ensure_routed_goal(isolated_db, tmp_path)
        run_id = _seed_running_run(isolated_db, "routed-goal", status="failed")

        done_file = folder / f".agent-{run_id}.done"
        done_file.write_text("1")

        result = recheck_failed_run(run_id, db_path=isolated_db)
        assert result is not None
        # No output.json → finalize_run produces a synthetic failed output
        assert result["status"] == "failed"

    def test_recheck_returns_none_when_no_artifacts(self, isolated_db, tmp_path):
        """When the routed dir has no .done / .output.json, recheck returns None."""
        _ensure_routed_goal(isolated_db, tmp_path)
        run_id = _seed_running_run(isolated_db, "routed-goal", status="failed")

        result = recheck_failed_run(run_id, db_path=isolated_db)
        assert result is None


# ---------------------------------------------------------------------------
# Routed _handle_state_transition — regression test
# ---------------------------------------------------------------------------

class TestHandleStateTransitionRouted:
    """Regression: _handle_state_transition polls .done/.output.json from routed dir."""

    def test_idle_with_output_in_routed_dir_triggers_finalize(
        self, isolated_db, tmp_path, fake_tmux, monkeypatch
    ):
        """IDLE state + output.json in routed folder_path → finalize."""
        from cast_server.services import agent_service

        async def _noop_cleanup(_session_name):
            return None

        monkeypatch.setattr(agent_service, "_cleanup_parent_session", _noop_cleanup)

        _ext_dir, folder = _ensure_routed_goal(isolated_db, tmp_path)
        run_id = _seed_running_run(isolated_db, "routed-goal")
        run = get_agent_run(run_id, db_path=isolated_db)

        # Write output file in routed dir
        output_file = folder / f".agent-{run_id}.output.json"
        output_file.write_text(json.dumps(
            _make_output_data("Routed finalization via state transition")
        ))

        asyncio.run(
            _handle_state_transition(run, AgentState.IDLE, db_path=isolated_db)
        )

        updated = get_agent_run(run_id, db_path=isolated_db)
        assert updated["status"] == "completed"
        assert updated["output"]["summary"] == "Routed finalization via state transition"

    def test_shell_returned_with_done_in_routed_dir_triggers_finalize(
        self, isolated_db, tmp_path, fake_tmux, monkeypatch
    ):
        """SHELL_RETURNED state + .done in routed dir → finalize."""
        from cast_server.services import agent_service

        async def _noop_cleanup(_session_name):
            return None

        monkeypatch.setattr(agent_service, "_cleanup_parent_session", _noop_cleanup)

        _ext_dir, folder = _ensure_routed_goal(isolated_db, tmp_path)
        run_id = _seed_running_run(isolated_db, "routed-goal")
        run = get_agent_run(run_id, db_path=isolated_db)

        done_file = folder / f".agent-{run_id}.done"
        done_file.write_text("0")

        asyncio.run(
            _handle_state_transition(run, AgentState.SHELL_RETURNED, db_path=isolated_db)
        )

        updated = get_agent_run(run_id, db_path=isolated_db)
        # No output.json → synthetic failed
        assert updated["status"] == "failed"


# ---------------------------------------------------------------------------
# Routed cancel_run — cleanup uses routed dir
# ---------------------------------------------------------------------------

class TestCancelRunRouted:
    """cancel_run must clean up dot-files from the routed folder_path."""

    def test_cancel_cleans_dot_files_in_routed_dir(self, isolated_db, tmp_path, fake_tmux):
        _ext_dir, folder = _ensure_routed_goal(isolated_db, tmp_path)
        run_id = _seed_running_run(isolated_db, "routed-goal")

        # Create dot-files in the routed dir (where agents write them)
        prompt_file = folder / f".agent-{run_id}.prompt"
        prompt_file.write_text("test prompt")
        delegation_file = folder / f".delegation-{run_id}.json"
        delegation_file.write_text("{}")

        cancel_run(run_id, db_path=isolated_db)

        assert not prompt_file.exists(), "Prompt file should be cleaned up"
        assert not delegation_file.exists(), "Delegation file should be cleaned up"

        updated = get_agent_run(run_id, db_path=isolated_db)
        assert updated["status"] == "failed"


# ---------------------------------------------------------------------------
# Routed continue_agent_run — continuation file uses routed dir
# ---------------------------------------------------------------------------

class TestContinueAgentRunRouted:
    """continue_agent_run must write .continue file to routed folder_path."""

    def test_continue_writes_to_routed_dir(self, isolated_db, tmp_path, fake_tmux, monkeypatch):
        import cast_server.services.agent_service as mod
        monkeypatch.setattr(mod, "AGENT_SENDKEY_DELAY", 0)

        _ext_dir, folder = _ensure_routed_goal(isolated_db, tmp_path)
        run_id = _seed_running_run(isolated_db, "routed-goal")

        asyncio.run(
            continue_agent_run(run_id, "follow-up message", db_path=isolated_db)
        )

        continue_file = folder / f".agent-{run_id}.continue"
        assert continue_file.exists(), ".continue file should be in routed dir"
        assert continue_file.read_text() == "follow-up message"


# ---------------------------------------------------------------------------
# Routed recover_stale_runs — dot-file recovery uses routed dir
# ---------------------------------------------------------------------------

class TestRecoverStaleRunsRouted:
    """recover_stale_runs must find dot-files in routed folder_path."""

    def test_recover_finds_output_in_routed_dir(self, isolated_db, tmp_path, fake_tmux):
        """A running run with no tmux session but .output.json in routed dir
        should be recovered."""
        _ext_dir, folder = _ensure_routed_goal(isolated_db, tmp_path)
        run_id = _seed_running_run(isolated_db, "routed-goal")

        # tmux session does not exist for this run
        fake_tmux.session_exists.return_value = False

        # Write output file in routed dir
        output_file = folder / f".agent-{run_id}.output.json"
        output_file.write_text(json.dumps(
            _make_output_data("Recovered from routed dir")
        ))

        recovered = recover_stale_runs(db_path=isolated_db)
        assert len(recovered) >= 1

        # Find the recovered run
        found = [r for r in recovered if r["id"] == run_id]
        assert len(found) == 1
        assert found[0]["status"] == "completed"
        assert found[0]["output"]["summary"] == "Recovered from routed dir"


# ---------------------------------------------------------------------------
# Routed _finalize_run_from_monitor — end-to-end
# ---------------------------------------------------------------------------

class TestFinalizeRunFromMonitorRouted:
    """_finalize_run_from_monitor reads and cleans up in routed folder_path."""

    def test_finalize_reads_output_and_cleans_prompt(
        self, isolated_db, tmp_path, fake_tmux, monkeypatch
    ):
        from cast_server.services import agent_service

        async def _noop_cleanup(_session_name):
            return None

        monkeypatch.setattr(agent_service, "_cleanup_parent_session", _noop_cleanup)

        _ext_dir, folder = _ensure_routed_goal(isolated_db, tmp_path)
        run_id = _seed_running_run(isolated_db, "routed-goal")
        run = get_agent_run(run_id, db_path=isolated_db)

        # Write prompt + output in routed dir
        prompt_file = folder / f".agent-{run_id}.prompt"
        prompt_file.write_text("prompt text")
        delegation_file = folder / f".delegation-{run_id}.json"
        delegation_file.write_text("{}")

        output_file = folder / f".agent-{run_id}.output.json"
        output_file.write_text(json.dumps(
            _make_output_data("Monitor finalized from routed dir")
        ))

        asyncio.run(
            _finalize_run_from_monitor(run, db_path=isolated_db)
        )

        updated = get_agent_run(run_id, db_path=isolated_db)
        assert updated["status"] == "completed"

        # Prompt + delegation files should be cleaned up
        assert not prompt_file.exists()
        assert not delegation_file.exists()
        # Output file is kept (parent polling reads it)
        assert output_file.exists()
