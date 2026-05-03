"""Regression tests for the routed-goal runtime vs artifact directory split.

Runtime tracking dot-files always live in ``GOALS_DIR/<slug>``. User-facing
artifacts still live in the routed ``folder_path`` under
``<external_project_dir>/docs/goal/<slug>``.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from cast_server.db.connection import init_db
from cast_server.infra.state_detection import AgentState
from cast_server.services import agent_service
from cast_server.services.goal_service import create_goal, update_config


@pytest.fixture
def routed_goal_env(tmp_path: Path, monkeypatch) -> dict[str, Path | str]:
    """Create a routed goal with runtime GOALS_DIR patched to tmp paths."""
    db_path = tmp_path / "test.db"
    goals_dir = tmp_path / "goals"
    goals_dir.mkdir()
    ext_dir = tmp_path / "ext-project"
    ext_dir.mkdir()
    init_db(db_path)

    from cast_server import config as cast_config
    from cast_server.services import goal_service

    monkeypatch.setattr(cast_config, "GOALS_DIR", goals_dir)
    monkeypatch.setattr(agent_service, "GOALS_DIR", goals_dir)
    monkeypatch.setattr(goal_service, "GOALS_DIR", goals_dir)

    goal = create_goal("Split Goal", goals_dir=goals_dir, db_path=db_path)
    slug = goal["slug"]
    assert slug == "split-goal"

    update_config(
        slug,
        external_project_dir=str(ext_dir),
        goals_dir=goals_dir,
        db_path=db_path,
    )

    runtime_dir = goals_dir / slug
    routed_dir = ext_dir / "docs" / "goal" / slug
    return {
        "db_path": db_path,
        "goals_dir": goals_dir,
        "runtime_dir": runtime_dir,
        "routed_dir": routed_dir,
        "slug": slug,
    }


def _seed_run(db_path: Path, goal_slug: str, status: str = "running") -> str:
    """Create an agent run for the routed goal and mark it started."""
    run_id = agent_service.create_agent_run(
        "cast-test-child-worker",
        goal_slug,
        None,
        {"task_title": "test task"},
        status=status,
        db_path=db_path,
    )
    agent_service.update_agent_run(
        run_id,
        started_at=datetime.now(timezone.utc).isoformat(),
        db_path=db_path,
    )
    return run_id


def _output_payload(summary: str) -> dict:
    """Return a valid contract-v2 output payload."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "contract_version": "2",
        "agent_name": "cast-test-child-worker",
        "task_title": "test task",
        "status": "completed",
        "summary": summary,
        "artifacts": [],
        "errors": [],
        "next_steps": [],
        "human_action_needed": False,
        "human_action_items": [],
        "started_at": now,
        "completed_at": now,
    }


class TestRuntimeArtifactDirResolution:
    """Runtime resolution should ignore the routed folder_path."""

    def test_routed_goal_uses_central_runtime_dir(self, routed_goal_env):
        actual = agent_service._resolve_runtime_artifact_dir(
            routed_goal_env["slug"],
        )

        assert actual == routed_goal_env["runtime_dir"]
        assert actual != routed_goal_env["routed_dir"]

    def test_user_artifact_dir_uses_routed_folder_path(self, routed_goal_env):
        actual = agent_service._resolve_user_artifact_dir(
            routed_goal_env["slug"], db_path=routed_goal_env["db_path"],
        )

        assert actual == routed_goal_env["routed_dir"]
        assert actual != routed_goal_env["runtime_dir"]

    def test_user_artifact_dir_falls_back_when_folder_path_empty(
        self, routed_goal_env,
    ):
        """A routed goal whose folder_path is empty string should fall back."""
        from cast_server.db.connection import get_connection

        conn = get_connection(routed_goal_env["db_path"])
        try:
            conn.execute(
                "UPDATE goals SET folder_path = ? WHERE slug = ?",
                ("", routed_goal_env["slug"]),
            )
            conn.commit()
        finally:
            conn.close()

        actual = agent_service._resolve_user_artifact_dir(
            routed_goal_env["slug"], db_path=routed_goal_env["db_path"],
        )
        assert actual == routed_goal_env["runtime_dir"]

    def test_user_artifact_dir_falls_back_when_folder_path_nonexistent(
        self, routed_goal_env, tmp_path,
    ):
        """A routed goal whose folder_path doesn't exist on disk should fall back."""
        from cast_server.db.connection import get_connection

        nonexistent = str(tmp_path / "does-not-exist" / "docs" / "goal" / "split-goal")
        conn = get_connection(routed_goal_env["db_path"])
        try:
            conn.execute(
                "UPDATE goals SET folder_path = ? WHERE slug = ?",
                (nonexistent, routed_goal_env["slug"]),
            )
            conn.commit()
        finally:
            conn.close()

        actual = agent_service._resolve_user_artifact_dir(
            routed_goal_env["slug"], db_path=routed_goal_env["db_path"],
        )
        assert actual == routed_goal_env["runtime_dir"]


class TestCentralRuntimeFilesForRoutedGoals:
    """Routed goals keep runtime files central even when user artifacts are routed."""

    def test_continue_agent_run_writes_continue_file_in_central_dir(
        self, routed_goal_env, monkeypatch,
    ):
        run_id = _seed_run(
            routed_goal_env["db_path"], routed_goal_env["slug"], status="idle",
        )

        mock_tmux = MagicMock()
        mock_tmux.session_exists.return_value = True
        monkeypatch.setattr(agent_service, "_get_tmux", lambda: mock_tmux)
        monkeypatch.setattr(agent_service, "AGENT_SENDKEY_DELAY", 0)

        asyncio.run(agent_service.continue_agent_run(
            run_id, "follow-up", db_path=routed_goal_env["db_path"],
        ))

        continue_file = routed_goal_env["runtime_dir"] / f".agent-{run_id}.continue"
        assert continue_file.exists()
        assert continue_file.read_text() == "follow-up"
        assert not (routed_goal_env["routed_dir"] / f".agent-{run_id}.continue").exists()

    def test_cancel_run_cleans_runtime_dotfiles_from_central_dir(
        self, routed_goal_env, monkeypatch,
    ):
        run_id = _seed_run(routed_goal_env["db_path"], routed_goal_env["slug"])

        prompt_file = routed_goal_env["runtime_dir"] / f".agent-{run_id}.prompt"
        delegation_file = routed_goal_env["runtime_dir"] / f".delegation-{run_id}.json"
        prompt_file.write_text("prompt")
        delegation_file.write_text("{}")

        mock_tmux = MagicMock()
        mock_tmux.session_exists.return_value = True
        monkeypatch.setattr(agent_service, "_get_tmux", lambda: mock_tmux)

        agent_service.cancel_run(run_id, db_path=routed_goal_env["db_path"])

        assert not prompt_file.exists()
        assert not delegation_file.exists()
        assert not (routed_goal_env["routed_dir"] / f".agent-{run_id}.prompt").exists()
        updated = agent_service.get_agent_run(run_id, db_path=routed_goal_env["db_path"])
        assert updated["status"] == "failed"

    def test_recheck_failed_run_reads_output_from_central_dir(self, routed_goal_env):
        run_id = _seed_run(
            routed_goal_env["db_path"], routed_goal_env["slug"], status="failed",
        )

        output_file = routed_goal_env["runtime_dir"] / f".agent-{run_id}.output.json"
        output_file.write_text(json.dumps(_output_payload("central runtime")))

        recovered = agent_service.recheck_failed_run(
            run_id, db_path=routed_goal_env["db_path"],
        )

        assert recovered is not None
        assert recovered["status"] == "completed"
        assert recovered["output"]["summary"] == "central runtime"
        assert not (routed_goal_env["routed_dir"] / f".agent-{run_id}.output.json").exists()

    def test_handle_state_transition_checks_central_done_file(
        self, routed_goal_env, monkeypatch,
    ):
        run_id = _seed_run(routed_goal_env["db_path"], routed_goal_env["slug"])
        run = agent_service.get_agent_run(run_id, db_path=routed_goal_env["db_path"])

        (routed_goal_env["runtime_dir"] / f".agent-{run_id}.done").write_text("1")

        finalized: list[str] = []

        async def fake_finalize(current_run, db_path=None):
            finalized.append(current_run["id"])

        monkeypatch.setattr(agent_service, "_finalize_run_from_monitor", fake_finalize)

        asyncio.run(agent_service._handle_state_transition(
            run, AgentState.IDLE, db_path=routed_goal_env["db_path"],
        ))

        assert finalized == [run_id]
        assert not (routed_goal_env["routed_dir"] / f".agent-{run_id}.done").exists()

    def test_finalize_run_from_monitor_reads_and_cleans_central_dir(
        self, routed_goal_env, monkeypatch,
    ):
        run_id = _seed_run(routed_goal_env["db_path"], routed_goal_env["slug"])
        run = agent_service.get_agent_run(run_id, db_path=routed_goal_env["db_path"])

        output_file = routed_goal_env["runtime_dir"] / f".agent-{run_id}.output.json"
        output_file.write_text(json.dumps(_output_payload("monitor finalize")))
        prompt_file = routed_goal_env["runtime_dir"] / f".agent-{run_id}.prompt"
        prompt_file.write_text("prompt")
        delegation_file = routed_goal_env["runtime_dir"] / f".delegation-{run_id}.json"
        delegation_file.write_text("{}")

        async def no_cleanup(_session_name: str) -> None:
            return None

        monkeypatch.setattr(agent_service, "_cleanup_parent_session", no_cleanup)

        asyncio.run(agent_service._finalize_run_from_monitor(
            run, db_path=routed_goal_env["db_path"],
        ))

        updated = agent_service.get_agent_run(run_id, db_path=routed_goal_env["db_path"])
        assert updated["status"] == "completed"
        assert updated["output"]["summary"] == "monitor finalize"
        assert not prompt_file.exists()
        assert not delegation_file.exists()
        assert output_file.exists()
        assert not (routed_goal_env["routed_dir"] / f".agent-{run_id}.prompt").exists()

    def test_recover_stale_runs_recovers_from_central_runtime_dir(
        self, routed_goal_env, monkeypatch,
    ):
        run_id = _seed_run(routed_goal_env["db_path"], routed_goal_env["slug"])

        output_file = routed_goal_env["runtime_dir"] / f".agent-{run_id}.output.json"
        output_file.write_text(json.dumps(_output_payload("startup recovery")))

        mock_tmux = MagicMock()
        mock_tmux.session_exists.return_value = False
        monkeypatch.setattr(agent_service, "_get_tmux", lambda: mock_tmux)

        recovered = agent_service.recover_stale_runs(db_path=routed_goal_env["db_path"])

        match = [run for run in recovered if run["id"] == run_id]
        assert match
        assert match[0]["status"] == "completed"
        assert match[0]["output"]["summary"] == "startup recovery"
        assert not (routed_goal_env["routed_dir"] / f".agent-{run_id}.output.json").exists()


class TestExplorationOutputRoutedToUserArtifactDir:
    """Exploration-phase output_dir should go to docs/goal/<slug>/exploration,
    not under the runtime .cast directory."""

    def test_exploration_output_dir_is_under_user_artifact_dir(
        self, routed_goal_env, monkeypatch,
    ):
        from cast_server.services import task_service

        slug = routed_goal_env["slug"]
        db_path = routed_goal_env["db_path"]

        # Create an exploration-phase task
        task = task_service.create_task(
            slug, "Explore the codebase", phase="exploration",
            goals_dir=routed_goal_env["goals_dir"], db_path=db_path,
        )
        task_id = task["id"]

        run_id = agent_service.create_agent_run(
            "cast-test-child-worker", slug, task_id, {"task_title": "explore"},
            db_path=db_path,
        )
        agent_service.update_agent_run(
            run_id,
            started_at=datetime.now(timezone.utc).isoformat(),
            db_path=db_path,
        )

        mock_tmux = MagicMock()
        mock_tmux.wait_for_ready.return_value = True
        monkeypatch.setattr(agent_service, "_get_tmux", lambda: mock_tmux)

        asyncio.run(agent_service._launch_agent(run_id, db_path=db_path))

        # Read the prompt to check output_dir and output.json path
        prompt_path = routed_goal_env["runtime_dir"] / f".agent-{run_id}.prompt"
        assert prompt_path.exists(), "Prompt should be written to runtime dir"
        prompt = prompt_path.read_text()

        routed_exploration = routed_goal_env["routed_dir"] / "exploration"
        assert f"Output directory: {routed_exploration}" in prompt, (
            "Exploration output_dir should be under the user-artifact dir "
            f"({routed_exploration}), not under .cast"
        )
        # The .agent-*.output.json path should still be in the runtime .cast dir
        assert f".agent-{run_id}.output.json" in prompt
        # Verify exploration dir was created on disk under the user-artifact dir
        assert routed_exploration.exists(), (
            "exploration/ should be created under the routed user-artifact dir"
        )
