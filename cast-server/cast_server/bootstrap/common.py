# SPDX-License-Identifier: Apache-2.0
"""Stdlib-only bootstrap helpers — replacement for ``bin/_lib.sh``.

Provides the same primitives that ``_lib.sh`` exposed to ``setup`` and
``bin/cast-doctor``:

* ``log`` / ``warn`` / ``fail`` — formatted output helpers.
* ``backup_destination`` — compute a ``~/.claude/.cast-bak-<ts>/<rel>`` path.
* ``backup_if_exists`` — move a path into the backup root.
* ``prune_old_backups`` — keep newest *n* ``.cast-bak-*`` dirs (default 5).
* ``install_diecast_skill_root`` — create the ``~/.claude/skills/diecast``
  symlink pointing at the repo root.
* ``probe_port`` — check whether a TCP port is accepting connections.
* ``detached_launch`` — start a background process detached from the caller.

All functions use only the Python standard library so they are safe to call
before ``uv sync`` has installed project dependencies.
"""
from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Sequence

# ── Output helpers ─────────────────────────────────────────────────


def log(msg: str) -> None:
    """Print an informational ``[cast]`` line to stdout."""
    print(f"[cast] {msg}", flush=True)


def warn(msg: str) -> None:
    """Print a ``[cast] WARNING:`` line to stderr."""
    print(f"[cast] WARNING: {msg}", file=sys.stderr, flush=True)


def fail(msg: str) -> None:
    """Print a ``[cast] ERROR:`` line to stderr and exit with code 1.

    Raises:
        SystemExit: Always, with exit code 1.
    """
    print(f"[cast] ERROR: {msg}", file=sys.stderr, flush=True)
    sys.exit(1)


def is_dry_run() -> bool:
    """Return True when DRY_RUN=1 is set in the environment."""
    return os.environ.get("DRY_RUN", "0") == "1"


# ── Timestamp / backup root ───────────────────────────────────────

def run_timestamp() -> str:
    """Return a UTC timestamp string in ``YYYYMMDDTHHMMSSz`` format.

    Uses ``RUN_TIMESTAMP`` from the environment when set (allows a shared
    timestamp across a multi-step installer run); otherwise generates a
    fresh one.

    Returns:
        A UTC timestamp string like ``20250503T120000Z``.
    """
    ts = os.environ.get("RUN_TIMESTAMP")
    if ts:
        return ts
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def backup_root(timestamp: Optional[str] = None) -> Path:
    """Return the backup directory for a single installer run.

    Shape: ``~/.claude/.cast-bak-<timestamp>``.

    Args:
        timestamp: Override the timestamp component. When ``None``, reads
            ``CAST_BAK_ROOT`` from the environment or falls back to
            :func:`run_timestamp`.

    Returns:
        A ``Path`` to the backup directory.
    """
    env_root = os.environ.get("CAST_BAK_ROOT")
    if env_root:
        return Path(env_root)
    ts = timestamp or run_timestamp()
    return Path.home() / ".claude" / f".cast-bak-{ts}"


# ── Backup destination calculation ─────────────────────────────────

def backup_destination(src: Path, bak_root: Optional[Path] = None) -> Path:
    """Compute the backup path for *src* inside the backup root.

    The backup preserves the path tail relative to ``$HOME``.  For paths
    outside ``$HOME`` the leading ``/`` is stripped.

    Args:
        src: Absolute path to the file or directory to back up.
        bak_root: Override the backup root directory.

    Returns:
        Absolute ``Path`` where *src* would be moved during backup.

    Examples:
        >>> backup_destination(Path.home() / ".claude" / "agents")
        PosixPath('/home/user/.claude/.cast-bak-.../claude/agents')
    """
    root = bak_root or backup_root()
    home = Path.home()
    try:
        rel = src.relative_to(home)
    except ValueError:
        # Outside $HOME — strip leading slash.
        rel = Path(str(src).lstrip("/"))
    return root / rel


# ── Backup move semantics ─────────────────────────────────────────

def backup_if_exists(
    src: Path,
    bak_root: Optional[Path] = None,
    *,
    dry_run: Optional[bool] = None,
) -> Optional[Path]:
    """Move *src* into the backup root if it exists; no-op otherwise.

    Mirrors ``_lib.sh::backup_if_exists`` semantics exactly:

    * Symlinks are treated as existing (``-e`` or ``-L``).
    * The destination directory tree is created on demand.
    * Honours ``DRY_RUN`` — logs but does not move.

    Args:
        src: Absolute path to the file, directory, or symlink.
        bak_root: Override the backup root directory.
        dry_run: Explicit dry-run flag.  When ``None``, reads from the
            ``DRY_RUN`` environment variable.

    Returns:
        The destination ``Path`` where *src* was moved, or ``None`` when
        *src* did not exist or the operation was dry-run.
    """
    if not (src.exists() or src.is_symlink()):
        return None

    dest = backup_destination(src, bak_root)
    _dry = dry_run if dry_run is not None else is_dry_run()
    if _dry:
        log(f"DRY: backup {src} -> {dest}")
        return None

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))
    log(f"Backed up {src} -> {dest}")
    return dest


# ── Backup pruning ─────────────────────────────────────────────────

def prune_old_backups(
    keep: int = 5,
    *,
    dry_run: Optional[bool] = None,
) -> list[Path]:
    """Keep the *keep* newest ``~/.claude/.cast-bak-*`` dirs, remove the rest.

    Matches ``_lib.sh::prune_old_backups`` behavior: lexicographic sort on
    directory name (which embeds a UTC timestamp) and ``rm -rf`` the oldest.

    Args:
        keep: Number of backup directories to retain. Default 5.
        dry_run: Explicit dry-run flag. When ``None``, reads ``DRY_RUN``
            from the environment.

    Returns:
        List of ``Path`` objects that were (or would be) pruned.
    """
    root = Path.home() / ".claude"
    if not root.is_dir():
        return []

    pattern = re.compile(r"^\.cast-bak-")
    dirs = sorted(
        p for p in root.iterdir()
        if p.is_dir() and pattern.match(p.name)
    )
    if len(dirs) <= keep:
        return []

    _dry = dry_run if dry_run is not None else is_dry_run()
    pruned: list[Path] = []
    for d in dirs[: len(dirs) - keep]:
        if _dry:
            log(f"DRY: prune {d}")
        else:
            shutil.rmtree(d, ignore_errors=True)
            log(f"Pruned old backup {d}")
        pruned.append(d)
    return pruned


# ── Skill-root symlink ─────────────────────────────────────────────

def install_diecast_skill_root(
    repo_dir: Path,
    *,
    dry_run: Optional[bool] = None,
    bak_root: Optional[Path] = None,
) -> None:
    """Create ``~/.claude/skills/diecast`` as a symlink to the repo root.

    Mirrors ``_lib.sh::install_diecast_skill_root`` semantics:

    * If the target is already a symlink, remove and re-link.
    * If the target is a real directory or file, back it up first.
    * Honours ``DRY_RUN``.

    Args:
        repo_dir: Absolute path to the diecast repository root.
        dry_run: Explicit dry-run flag. When ``None``, reads ``DRY_RUN``
            from the environment.
        bak_root: Override backup root directory for ``backup_if_exists``.
    """
    _dry = dry_run if dry_run is not None else is_dry_run()
    skills_dir = Path.home() / ".claude" / "skills"
    target = skills_dir / "diecast"

    if _dry:
        log(f"DRY: ln -snf {repo_dir} {target}")
        return

    skills_dir.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        target.unlink()
    elif target.exists():
        backup_if_exists(target, bak_root, dry_run=False)
    target.symlink_to(repo_dir)
    log(f"Linked {target} -> {repo_dir}")


# ── Port probe ─────────────────────────────────────────────────────

def probe_port(host: str = "127.0.0.1", port: int = 8005, timeout: float = 1.0) -> bool:
    """Return True when *port* on *host* is accepting TCP connections.

    Args:
        host: Hostname or IP address. Default ``127.0.0.1``.
        port: TCP port number. Default ``8005``.
        timeout: Connection timeout in seconds. Default ``1.0``.

    Returns:
        ``True`` when the connection succeeds, ``False`` otherwise.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, ConnectionRefusedError):
        return False


# ── Detached launch ────────────────────────────────────────────────

def detached_launch(
    args: Sequence[str],
    *,
    env: Optional[dict[str, str]] = None,
    cwd: Optional[Path] = None,
    log_path: Optional[Path] = None,
) -> subprocess.Popen:
    """Start a background process fully detached from the calling terminal.

    Equivalent to ``nohup ... &>/dev/null &`` from bash.

    Args:
        args: Command and arguments as a sequence.
        env: Override environment variables. When ``None``, inherits
            the caller's environment.
        cwd: Working directory for the child process.
        log_path: Redirect stdout and stderr to this file. When ``None``,
            output is sent to ``/dev/null``.

    Returns:
        The ``Popen`` handle. The caller may poll ``pid`` or discard it.
    """
    log_fh = None
    if log_path:
        log_fh = open(log_path, "a")  # noqa: SIM115
        stdout = log_fh
        stderr = subprocess.STDOUT
    else:
        stdout = subprocess.DEVNULL
        stderr = subprocess.DEVNULL

    try:
        proc = subprocess.Popen(
            list(args),
            env=env,
            cwd=str(cwd) if cwd else None,
            stdout=stdout,
            stderr=stderr,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception:
        if log_fh is not None:
            log_fh.close()
        raise

    # Popen has dup'd the file descriptor; close the parent's copy to
    # avoid a resource leak during the parent's lifetime.
    if log_fh is not None:
        log_fh.close()

    return proc
