"""Unit tests for ``cast_server.bootstrap.common``.

Covers:
* backup destination calculation (relative to $HOME and outside $HOME)
* backup move semantics (exists, absent, symlink, dry-run)
* prune-to-5 retention
* symlink replacement behavior (install_diecast_skill_root)
* port-probe success/failure
* detached launch helper behavior
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

# Ensure cast-server/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "cast-server"))

from cast_server.bootstrap.common import (
    backup_destination,
    backup_if_exists,
    backup_root,
    detached_launch,
    install_diecast_skill_root,
    is_dry_run,
    log,
    warn,
    fail,
    probe_port,
    prune_old_backups,
    run_timestamp,
)


# ── backup_destination ─────────────────────────────────────────────


class TestBackupDestination:
    """Tests for backup_destination path calculation."""

    def test_path_under_home(self, tmp_path: Path) -> None:
        """Path under $HOME keeps the tail relative to $HOME."""
        bak = tmp_path / ".cast-bak-test"
        home = tmp_path / "fakehome"
        home.mkdir()
        src = home / ".claude" / "agents" / "foo"
        with mock.patch("cast_server.bootstrap.common.Path.home", return_value=home):
            dest = backup_destination(src, bak)
        assert dest == bak / ".claude" / "agents" / "foo"

    def test_path_outside_home(self, tmp_path: Path) -> None:
        """Path outside $HOME strips the leading '/'."""
        bak = tmp_path / ".cast-bak-test"
        src = Path("/opt/something/file.txt")
        with mock.patch("cast_server.bootstrap.common.Path.home", return_value=tmp_path / "nope"):
            dest = backup_destination(src, bak)
        assert dest == bak / "opt" / "something" / "file.txt"

    def test_uses_default_backup_root(self, tmp_path: Path) -> None:
        """When no bak_root is passed, backup_root() is used."""
        home = tmp_path / "fakehome"
        home.mkdir()
        src = home / "file.txt"
        with mock.patch("cast_server.bootstrap.common.Path.home", return_value=home):
            with mock.patch("cast_server.bootstrap.common.backup_root", return_value=tmp_path / "bak"):
                dest = backup_destination(src)
        assert dest == tmp_path / "bak" / "file.txt"


# ── backup_if_exists ───────────────────────────────────────────────


class TestBackupIfExists:
    """Tests for backup_if_exists move semantics."""

    def test_moves_existing_file(self, tmp_path: Path) -> None:
        """An existing regular file is moved into the backup root."""
        bak = tmp_path / "bak"
        home = tmp_path / "home"
        home.mkdir()
        src = home / "file.txt"
        src.write_text("content")
        with mock.patch("cast_server.bootstrap.common.Path.home", return_value=home):
            result = backup_if_exists(src, bak, dry_run=False)
        assert result is not None
        assert result.exists()
        assert result.read_text() == "content"
        assert not src.exists()

    def test_noop_when_absent(self, tmp_path: Path) -> None:
        """Returns None when the source does not exist."""
        bak = tmp_path / "bak"
        src = tmp_path / "nonexistent"
        result = backup_if_exists(src, bak, dry_run=False)
        assert result is None

    def test_moves_symlink(self, tmp_path: Path) -> None:
        """A dangling symlink counts as existing and gets moved."""
        bak = tmp_path / "bak"
        home = tmp_path / "home"
        home.mkdir()
        target = home / "target"
        link = home / "link"
        link.symlink_to(target)  # dangling symlink
        with mock.patch("cast_server.bootstrap.common.Path.home", return_value=home):
            result = backup_if_exists(link, bak, dry_run=False)
        assert result is not None
        assert not link.is_symlink()

    def test_dry_run_does_not_move(self, tmp_path: Path) -> None:
        """In dry-run mode the file stays in place and None is returned."""
        bak = tmp_path / "bak"
        home = tmp_path / "home"
        home.mkdir()
        src = home / "file.txt"
        src.write_text("content")
        with mock.patch("cast_server.bootstrap.common.Path.home", return_value=home):
            result = backup_if_exists(src, bak, dry_run=True)
        assert result is None
        assert src.exists()

    def test_moves_directory(self, tmp_path: Path) -> None:
        """An existing directory tree is moved completely."""
        bak = tmp_path / "bak"
        home = tmp_path / "home"
        home.mkdir()
        src = home / "agents"
        src.mkdir()
        (src / "readme.md").write_text("hello")
        with mock.patch("cast_server.bootstrap.common.Path.home", return_value=home):
            result = backup_if_exists(src, bak, dry_run=False)
        assert result is not None
        assert (result / "readme.md").read_text() == "hello"
        assert not src.exists()


# ── prune_old_backups ──────────────────────────────────────────────


class TestPruneOldBackups:
    """Tests for prune-to-5 retention policy."""

    def test_prune_keeps_5_newest(self, tmp_path: Path) -> None:
        """With 7 backup dirs, the 2 oldest are pruned."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        names = [f".cast-bak-2025010{i}T000000Z" for i in range(7)]
        for name in names:
            (claude_dir / name).mkdir()
        with mock.patch("cast_server.bootstrap.common.Path.home", return_value=tmp_path):
            pruned = prune_old_backups(keep=5, dry_run=False)
        assert len(pruned) == 2
        remaining = sorted(p.name for p in claude_dir.iterdir() if p.name.startswith(".cast-bak-"))
        assert len(remaining) == 5
        # Oldest two should be gone
        assert names[0] not in remaining
        assert names[1] not in remaining

    def test_no_prune_when_under_threshold(self, tmp_path: Path) -> None:
        """With 3 backup dirs and keep=5, nothing is pruned."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        for i in range(3):
            (claude_dir / f".cast-bak-2025010{i}T000000Z").mkdir()
        with mock.patch("cast_server.bootstrap.common.Path.home", return_value=tmp_path):
            pruned = prune_old_backups(keep=5, dry_run=False)
        assert pruned == []

    def test_dry_run_does_not_remove(self, tmp_path: Path) -> None:
        """Dry-run reports what it would prune but leaves dirs intact."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        for i in range(7):
            (claude_dir / f".cast-bak-2025010{i}T000000Z").mkdir()
        with mock.patch("cast_server.bootstrap.common.Path.home", return_value=tmp_path):
            pruned = prune_old_backups(keep=5, dry_run=True)
        assert len(pruned) == 2
        remaining = list(claude_dir.iterdir())
        assert len(remaining) == 7  # nothing removed

    def test_no_claude_dir(self, tmp_path: Path) -> None:
        """Gracefully returns empty list when ~/.claude does not exist."""
        with mock.patch("cast_server.bootstrap.common.Path.home", return_value=tmp_path):
            pruned = prune_old_backups(keep=5, dry_run=False)
        assert pruned == []


# ── install_diecast_skill_root ─────────────────────────────────────


class TestInstallDiecastSkillRoot:
    """Tests for the skill-root symlink installer."""

    def test_creates_symlink(self, tmp_path: Path) -> None:
        """Creates the skills/diecast symlink pointing at the repo dir."""
        home = tmp_path / "home"
        home.mkdir()
        repo = tmp_path / "repo"
        repo.mkdir()
        with mock.patch("cast_server.bootstrap.common.Path.home", return_value=home):
            install_diecast_skill_root(repo, dry_run=False)
        target = home / ".claude" / "skills" / "diecast"
        assert target.is_symlink()
        assert target.resolve() == repo.resolve()

    def test_replaces_existing_symlink(self, tmp_path: Path) -> None:
        """Re-links when a different symlink already exists."""
        home = tmp_path / "home"
        (home / ".claude" / "skills").mkdir(parents=True)
        old = tmp_path / "old_repo"
        old.mkdir()
        target = home / ".claude" / "skills" / "diecast"
        target.symlink_to(old)
        new_repo = tmp_path / "new_repo"
        new_repo.mkdir()
        with mock.patch("cast_server.bootstrap.common.Path.home", return_value=home):
            install_diecast_skill_root(new_repo, dry_run=False)
        assert target.is_symlink()
        assert target.resolve() == new_repo.resolve()

    def test_backs_up_real_directory(self, tmp_path: Path) -> None:
        """A real directory at the target path is backed up before linking."""
        home = tmp_path / "home"
        (home / ".claude" / "skills" / "diecast").mkdir(parents=True)
        (home / ".claude" / "skills" / "diecast" / "file.txt").write_text("old")
        repo = tmp_path / "repo"
        repo.mkdir()
        bak = tmp_path / "bak"
        with mock.patch("cast_server.bootstrap.common.Path.home", return_value=home):
            install_diecast_skill_root(repo, dry_run=False, bak_root=bak)
        target = home / ".claude" / "skills" / "diecast"
        assert target.is_symlink()

    def test_dry_run_does_not_create(self, tmp_path: Path) -> None:
        """In dry-run mode nothing is created."""
        home = tmp_path / "home"
        home.mkdir()
        repo = tmp_path / "repo"
        repo.mkdir()
        with mock.patch("cast_server.bootstrap.common.Path.home", return_value=home):
            install_diecast_skill_root(repo, dry_run=True)
        target = home / ".claude" / "skills" / "diecast"
        assert not target.exists()


# ── probe_port ─────────────────────────────────────────────────────


class TestProbePort:
    """Tests for port-probe success/failure."""

    def test_open_port_returns_true(self) -> None:
        """Probe returns True when a socket is listening."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            s.listen(1)
            port = s.getsockname()[1]
            assert probe_port("127.0.0.1", port, timeout=1.0) is True

    def test_closed_port_returns_false(self) -> None:
        """Probe returns False when nothing is listening."""
        # Use a high-numbered port unlikely to be in use.
        assert probe_port("127.0.0.1", 59999, timeout=0.1) is False


# ── detached_launch ────────────────────────────────────────────────


class TestDetachedLaunch:
    """Tests for background process launching."""

    def test_launches_process(self, tmp_path: Path) -> None:
        """A detached process runs and produces output."""
        marker = tmp_path / "marker.txt"
        proc = detached_launch(
            [sys.executable, "-c", f"from pathlib import Path; Path('{marker}').write_text('ok')"],
            cwd=tmp_path,
        )
        proc.wait(timeout=10)
        assert marker.read_text() == "ok"

    def test_log_path_captures_output(self, tmp_path: Path) -> None:
        """When log_path is set, stdout is captured there."""
        log_file = tmp_path / "out.log"
        proc = detached_launch(
            [sys.executable, "-c", "print('hello from child')"],
            log_path=log_file,
        )
        proc.wait(timeout=10)
        assert "hello from child" in log_file.read_text()


# ── Output helpers ─────────────────────────────────────────────────


class TestOutputHelpers:
    """Tests for log, warn, fail."""

    def test_log_prints_to_stdout(self, capsys) -> None:
        """log() writes to stdout with [cast] prefix."""
        log("hello")
        assert "[cast] hello" in capsys.readouterr().out

    def test_warn_prints_to_stderr(self, capsys) -> None:
        """warn() writes to stderr with WARNING prefix."""
        warn("careful")
        assert "[cast] WARNING: careful" in capsys.readouterr().err

    def test_fail_exits(self) -> None:
        """fail() raises SystemExit with code 1."""
        with pytest.raises(SystemExit) as exc:
            fail("boom")
        assert exc.value.code == 1


# ── run_timestamp / backup_root ────────────────────────────────────


class TestTimestampAndRoot:
    """Tests for timestamp generation and backup root calculation."""

    def test_run_timestamp_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Uses RUN_TIMESTAMP from environment when set."""
        monkeypatch.setenv("RUN_TIMESTAMP", "20250101T000000Z")
        assert run_timestamp() == "20250101T000000Z"

    def test_run_timestamp_generates_fresh(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Generates a valid timestamp when env is unset."""
        monkeypatch.delenv("RUN_TIMESTAMP", raising=False)
        ts = run_timestamp()
        assert ts.endswith("Z")
        assert "T" in ts

    def test_backup_root_from_env(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """CAST_BAK_ROOT from environment is used when set."""
        bak = str(tmp_path / "custom-bak")
        monkeypatch.setenv("CAST_BAK_ROOT", bak)
        assert backup_root() == Path(bak)

    def test_backup_root_default_shape(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Default backup root is ~/.claude/.cast-bak-<ts>."""
        monkeypatch.delenv("CAST_BAK_ROOT", raising=False)
        root = backup_root("20250101T000000Z")
        assert root.name == ".cast-bak-20250101T000000Z"
        assert root.parent.name == ".claude"
