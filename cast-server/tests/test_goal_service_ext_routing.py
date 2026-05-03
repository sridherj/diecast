"""Tests for goal_service.update_config external project routing.

Verifies that when external_project_dir is set on a goal, the goal's
folder_path is routed to <external_project_dir>/docs/goal/<slug>, existing
artifacts are moved, and goals without external_project_dir keep the default
GOALS_DIR/<slug> path.
"""

from __future__ import annotations

from pathlib import Path

import yaml


def _init_db_and_create_goal(
    tmp_path: Path, slug: str = "my-goal", title: str = "My Goal"
) -> tuple[Path, Path, Path]:
    """Bootstrap a test DB + goals_dir and create a goal.

    Returns (db_path, goals_dir, goal_dir).
    """
    from cast_server.db.connection import init_db, get_connection

    db_path = tmp_path / "test.db"
    goals_dir = tmp_path / "goals"
    goals_dir.mkdir()
    init_db(db_path)

    from cast_server.services.goal_service import create_goal

    create_goal(title, goals_dir=goals_dir, db_path=db_path)
    goal_dir = goals_dir / slug
    return db_path, goals_dir, goal_dir


class TestUpdateConfigExternalRouting:
    """Tests for the docs/goal/<slug> routing in update_config."""

    def test_external_project_dir_routes_to_docs_goal(self, tmp_path):
        """When external_project_dir is set, folder_path updates to
        <ext_dir>/docs/goal/<slug>."""
        from cast_server.services.goal_service import update_config, get_goal

        db_path, goals_dir, goal_dir = _init_db_and_create_goal(tmp_path)
        ext_dir = tmp_path / "ext-project"
        ext_dir.mkdir()

        result = update_config(
            "my-goal",
            external_project_dir=str(ext_dir),
            goals_dir=goals_dir,
            db_path=db_path,
        )

        expected_path = ext_dir / "docs" / "goal" / "my-goal"
        assert expected_path.exists(), "docs/goal/<slug> directory should be created"

        # The DB should have the updated folder_path
        goal = get_goal("my-goal", db_path=db_path)
        assert goal["folder_path"] == str(expected_path)

    def test_existing_artifacts_are_moved(self, tmp_path):
        """Existing artifacts in the old goal dir should be moved to
        the new docs/goal/<slug> directory."""
        from cast_server.services.goal_service import update_config

        db_path, goals_dir, goal_dir = _init_db_and_create_goal(tmp_path)
        ext_dir = tmp_path / "ext-project"
        ext_dir.mkdir()

        # Create an artifact in the old goal dir
        artifact = goal_dir / "notes.md"
        artifact.write_text("# My notes\n")

        update_config(
            "my-goal",
            external_project_dir=str(ext_dir),
            goals_dir=goals_dir,
            db_path=db_path,
        )

        new_goal_dir = ext_dir / "docs" / "goal" / "my-goal"
        moved_artifact = new_goal_dir / "notes.md"
        assert moved_artifact.exists(), "Artifact should be moved to new dir"
        assert moved_artifact.read_text() == "# My notes\n"

    def test_no_overwrite_on_conflict(self, tmp_path):
        """If a file already exists at the destination, it should NOT be
        overwritten during the move."""
        from cast_server.services.goal_service import update_config

        db_path, goals_dir, goal_dir = _init_db_and_create_goal(tmp_path)
        ext_dir = tmp_path / "ext-project"
        ext_dir.mkdir()

        # Create an artifact in the old goal dir
        artifact = goal_dir / "notes.md"
        artifact.write_text("old content\n")

        # Pre-create the destination with different content
        new_goal_dir = ext_dir / "docs" / "goal" / "my-goal"
        new_goal_dir.mkdir(parents=True)
        existing = new_goal_dir / "notes.md"
        existing.write_text("existing content\n")

        update_config(
            "my-goal",
            external_project_dir=str(ext_dir),
            goals_dir=goals_dir,
            db_path=db_path,
        )

        # Existing file should NOT be overwritten
        assert existing.read_text() == "existing content\n"

    def test_goal_yaml_updated_in_new_location(self, tmp_path):
        """goal.yaml in the new location should have external_project_dir set."""
        from cast_server.services.goal_service import update_config

        db_path, goals_dir, goal_dir = _init_db_and_create_goal(tmp_path)
        ext_dir = tmp_path / "ext-project"
        ext_dir.mkdir()

        update_config(
            "my-goal",
            external_project_dir=str(ext_dir),
            goals_dir=goals_dir,
            db_path=db_path,
        )

        new_goal_dir = ext_dir / "docs" / "goal" / "my-goal"
        yaml_path = new_goal_dir / "goal.yaml"
        assert yaml_path.exists(), "goal.yaml should exist in new location"

        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        assert data["external_project_dir"] == str(ext_dir)

    def test_no_external_project_dir_keeps_default(self, tmp_path):
        """Goals without external_project_dir should keep GOALS_DIR/<slug>."""
        from cast_server.services.goal_service import update_config, get_goal

        db_path, goals_dir, goal_dir = _init_db_and_create_goal(tmp_path)

        # Update only gstack_dir, no external_project_dir
        update_config(
            "my-goal",
            gstack_dir="/some/ref",
            goals_dir=goals_dir,
            db_path=db_path,
        )

        goal = get_goal("my-goal", db_path=db_path)
        # folder_path should still be the original goals_dir/<slug>
        assert goal["folder_path"] == str(goals_dir / "my-goal")

    def test_idempotent_when_already_routed(self, tmp_path):
        """Calling update_config again with the same external_project_dir
        should be a no-op (idempotent)."""
        from cast_server.services.goal_service import update_config, get_goal

        db_path, goals_dir, goal_dir = _init_db_and_create_goal(tmp_path)
        ext_dir = tmp_path / "ext-project"
        ext_dir.mkdir()

        update_config(
            "my-goal",
            external_project_dir=str(ext_dir),
            goals_dir=goals_dir,
            db_path=db_path,
        )

        new_goal_dir = ext_dir / "docs" / "goal" / "my-goal"
        artifact = new_goal_dir / "extra.md"
        artifact.write_text("# Extra\n")

        # Second call with the same ext_dir — should not lose the artifact
        update_config(
            "my-goal",
            external_project_dir=str(ext_dir),
            goals_dir=goals_dir,
            db_path=db_path,
        )

        goal = get_goal("my-goal", db_path=db_path)
        assert goal["folder_path"] == str(new_goal_dir)
        assert artifact.exists(), "Artifact should still exist after idempotent call"


class TestCastSymlinkTargetsRuntimeDir:
    """Runtime tracking symlink should always point at the central goals dir."""

    def test_cast_symlink_targets_goals_dir_even_when_routed(self, tmp_path):
        """After routing user artifacts to docs/goal/<slug>, .cast should still
        point to the central goals_dir/<slug> runtime directory."""
        from cast_server.services.goal_service import update_config

        db_path, goals_dir, goal_dir = _init_db_and_create_goal(tmp_path)
        ext_dir = tmp_path / "ext-project"
        ext_dir.mkdir()

        update_config(
            "my-goal",
            external_project_dir=str(ext_dir),
            goals_dir=goals_dir,
            db_path=db_path,
        )

        symlink = ext_dir / ".cast"
        assert symlink.is_symlink(), ".cast symlink should exist"
        assert symlink.resolve() == goal_dir.resolve(), (
            f".cast should point to {goal_dir}, got {symlink.resolve()}"
        )

    def test_cast_symlink_without_routing_targets_goals_dir(self, tmp_path):
        """Without external routing, .cast should point to goals_dir/<slug>."""
        from cast_server.services.goal_service import ensure_cast_symlink

        db_path, goals_dir, goal_dir = _init_db_and_create_goal(tmp_path)
        ext_dir = tmp_path / "ext-project"
        ext_dir.mkdir()

        result = ensure_cast_symlink("my-goal", str(ext_dir), goals_dir)

        assert result is not None
        symlink = ext_dir / ".cast"
        assert symlink.is_symlink()
        assert symlink.resolve() == goal_dir.resolve()

    def test_re_calling_ensure_cast_symlink_after_routing_preserves_runtime_target(self, tmp_path):
        """Re-calling ensure_cast_symlink after routing should keep .cast at goals_dir/<slug>."""
        from cast_server.services.goal_service import (
            update_config, ensure_cast_symlink,
        )

        db_path, goals_dir, goal_dir = _init_db_and_create_goal(tmp_path)
        ext_dir = tmp_path / "ext-project"
        ext_dir.mkdir()

        update_config(
            "my-goal",
            external_project_dir=str(ext_dir),
            goals_dir=goals_dir,
            db_path=db_path,
        )

        # Re-call — should be idempotent, still pointing at central goals_dir
        ensure_cast_symlink("my-goal", str(ext_dir), goals_dir)

        symlink = ext_dir / ".cast"
        assert symlink.resolve() == goal_dir.resolve(), (
            "Runtime .cast should stay pointed at goals_dir/<slug>"
        )


class TestRoutedGoalWritePaths:
    """Regression: update_phase, toggle_focus, and tasks.md rendering must
    write to the routed folder_path, not the default goals_dir/<slug>."""

    def _route_goal(self, tmp_path):
        """Helper: create a goal, route it, return (db_path, goals_dir, ext_dir, routed_dir)."""
        from cast_server.services.goal_service import update_config

        db_path, goals_dir, goal_dir = _init_db_and_create_goal(tmp_path)
        ext_dir = tmp_path / "ext-project"
        ext_dir.mkdir()

        update_config(
            "my-goal",
            external_project_dir=str(ext_dir),
            goals_dir=goals_dir,
            db_path=db_path,
        )
        routed_dir = ext_dir / "docs" / "goal" / "my-goal"
        return db_path, goals_dir, ext_dir, routed_dir

    def test_update_phase_writes_to_routed_dir(self, tmp_path):
        """update_phase should write goal.yaml in the routed directory."""
        from cast_server.services.goal_service import update_phase

        db_path, goals_dir, ext_dir, routed_dir = self._route_goal(tmp_path)

        import yaml
        update_phase("my-goal", "execution", goals_dir=goals_dir, db_path=db_path)

        yaml_path = routed_dir / "goal.yaml"
        assert yaml_path.exists(), "goal.yaml should be in the routed directory"
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        assert data["phase"] == "execution"

    def test_toggle_focus_writes_to_routed_dir(self, tmp_path):
        """toggle_focus should write goal.yaml in the routed directory."""
        from cast_server.services.goal_service import toggle_focus

        db_path, goals_dir, ext_dir, routed_dir = self._route_goal(tmp_path)

        import yaml
        toggle_focus("my-goal", True, goals_dir=goals_dir, db_path=db_path)

        yaml_path = routed_dir / "goal.yaml"
        assert yaml_path.exists(), "goal.yaml should be in the routed directory"
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        assert data["in_focus"] is True

    def test_update_status_writes_to_routed_dir(self, tmp_path):
        """update_status should write goal.yaml in the routed directory."""
        from cast_server.services.goal_service import update_status

        db_path, goals_dir, ext_dir, routed_dir = self._route_goal(tmp_path)

        import yaml
        update_status("my-goal", "completed", goals_dir=goals_dir, db_path=db_path)

        yaml_path = routed_dir / "goal.yaml"
        assert yaml_path.exists(), "goal.yaml should be in the routed directory"
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        assert data["status"] == "completed"

    def test_rerender_tasks_md_writes_to_routed_dir(self, tmp_path):
        """_rerender_tasks_md should write tasks.md in the routed directory."""
        from cast_server.services.task_service import _rerender_tasks_md

        db_path, goals_dir, ext_dir, routed_dir = self._route_goal(tmp_path)

        _rerender_tasks_md("my-goal", goals_dir=goals_dir, db_path=db_path)

        tasks_path = routed_dir / "tasks.md"
        assert tasks_path.exists(), "tasks.md should be in the routed directory"

    def test_artifact_sidebar_resolves_routed_goal_dir(self, tmp_path):
        """artifact_sidebar should look for artifacts in the routed folder_path."""
        from cast_server.services.goal_service import get_goal

        db_path, goals_dir, ext_dir, routed_dir = self._route_goal(tmp_path)

        # Create an artifact in the routed dir
        artifact = routed_dir / "notes.ai.md"
        artifact.write_text("# Notes\nSome content\n")

        goal = get_goal("my-goal", db_path=db_path)
        fp = goal.get("folder_path")
        assert fp is not None

        # Verify the resolved path points to the routed location
        from pathlib import Path
        goal_dir = Path(fp)
        resolved = (goal_dir / "notes.ai.md").resolve()
        assert resolved.exists(), (
            "Artifact should be found via folder_path, not goals_dir/<slug>"
        )
