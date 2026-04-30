#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""bin/run-migrations.py — Diecast schema-migration runner.

Internal use; not on user PATH. **Deprecated by Alembic (sp3).** Will be
removed once all known DBs have been migrated. Do not invoke for new schema
changes — use ``cast-server/alembic/`` instead.

Invoked by `./setup --upgrade` between Step 2 (generate-skills) and Step 3
(install agents). v1 ships zero production migrations under `migrations/`,
so against the published set this runner is a no-op. The trivial fixture
migration under `tests/migrations-fixtures/` exercises the code path.

CLI:
    bin/run-migrations.py [--migrations-dir DIR] [--applied-file FILE]
                          [--dry-run]

Defaults:
    --migrations-dir   migrations/ (relative to repo root)
    --applied-file     ~/.cast/migrations.applied

Behaviour:
    1. Read --applied-file (one filename per line); compute applied-set.
    2. Enumerate *.py in --migrations-dir (sorted lex, skip __init__.py
       and dotfiles); compute on-disk-set.
    3. For each filename in (on-disk - applied) in lex order:
         - Load the module via importlib.util.spec_from_file_location.
         - Read ~/.cast/config.yaml as a dict (empty dict if absent).
         - Call module.up(config).
         - On success → append filename to --applied-file.
         - On failure → raise; the caller (./setup --upgrade) handles
           rollback via the most recent .cast-bak-<ts>/ directory.
    4. --dry-run: print "would apply: <name>" for each unapplied
       migration; exit 0 without mutation.

Seam choice: option (a) — invoked from ./setup. See migrations/README.md
"When migrations run" for rationale.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # type: ignore[assignment]


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _default_applied_file() -> Path:
    return Path(os.path.expanduser("~/.cast/migrations.applied"))


def _read_applied(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }


def _enumerate_migrations(migrations_dir: Path) -> list[Path]:
    if not migrations_dir.is_dir():
        return []
    return sorted(
        p
        for p in migrations_dir.iterdir()
        if p.is_file()
        and p.suffix == ".py"
        and p.name != "__init__.py"
        and not p.name.startswith(".")
    )


def _read_config() -> dict:
    cfg_path = Path(os.path.expanduser("~/.cast/config.yaml"))
    if not cfg_path.exists():
        return {}
    raw = cfg_path.read_text(encoding="utf-8")
    if yaml is None:
        # Best-effort fallback: callers that need config can import yaml
        # themselves. Returning an empty dict keeps the runner usable in
        # minimal environments (e.g. the e2e fixture).
        return {}
    parsed = yaml.safe_load(raw) or {}
    if not isinstance(parsed, dict):
        raise ValueError(
            f"~/.cast/config.yaml must parse to a mapping; got {type(parsed).__name__}"
        )
    return parsed


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(
        f"diecast_migration_{path.stem}", path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"could not build import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _append_applied(path: Path, name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(name + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bin/run-migrations.py",
        description="Apply un-applied Diecast migrations.",
    )
    parser.add_argument(
        "--migrations-dir",
        type=Path,
        default=_repo_root() / "migrations",
        help="Directory containing migration *.py files (default: migrations/).",
    )
    parser.add_argument(
        "--applied-file",
        type=Path,
        default=_default_applied_file(),
        help="Tracking file; one applied filename per line "
        "(default: ~/.cast/migrations.applied).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print would-apply names; do not mutate.",
    )
    args = parser.parse_args(argv)

    migrations_dir: Path = args.migrations_dir
    applied_file: Path = args.applied_file

    applied = _read_applied(applied_file)
    on_disk = _enumerate_migrations(migrations_dir)

    pending = [p for p in on_disk if p.name not in applied]

    if not pending:
        print(f"[run-migrations] up-to-date ({len(applied)} applied).")
        return 0

    if args.dry_run:
        for path in pending:
            print(f"would apply: {path.name}")
        return 0

    config = _read_config()

    for path in pending:
        print(f"[run-migrations] applying {path.name}…")
        module = _load_module(path)
        if not hasattr(module, "up"):
            raise AttributeError(
                f"{path.name} does not expose an up(config) function"
            )
        module.up(config)
        _append_applied(applied_file, path.name)
        print(f"[run-migrations] applied  {path.name}")

    print(f"[run-migrations] done ({len(pending)} applied this run).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
