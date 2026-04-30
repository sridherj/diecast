"""Verify the on-disk agent registry replaces the dead `agents` table.

The legacy sync engine that populated `agents` was removed in Phase 3b sp13
(see cast-server/docs/scope-prune.md). `get_all_agents()` now reads
`agents/<name>/<name>.md` frontmatter directly. These tests pin that contract.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from cast_server.services.agent_service import (
    _load_agent_registry,
    _parse_frontmatter,
    get_all_agents,
)


def _write_agent(root: Path, name: str, frontmatter: str) -> None:
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.md").write_text(
        f"---\n{frontmatter}\n---\n\n# {name}\n\nbody here\n",
        encoding="utf-8",
    )


def test_parse_frontmatter_returns_dict(tmp_path: Path) -> None:
    md = tmp_path / "x.md"
    md.write_text("---\nname: foo\ndescription: bar\n---\n\nbody\n")
    assert _parse_frontmatter(md) == {"name": "foo", "description": "bar"}


def test_parse_frontmatter_no_frontmatter_returns_none(tmp_path: Path) -> None:
    md = tmp_path / "x.md"
    md.write_text("# heading\n\nno frontmatter here\n")
    assert _parse_frontmatter(md) is None


def test_load_registry_picks_up_cast_dirs(tmp_path: Path) -> None:
    _write_agent(tmp_path, "cast-foo", "name: cast-foo\ndescription: a foo agent")
    _write_agent(tmp_path, "cast-bar", "name: cast-bar\ndescription: a bar agent")
    # Non-cast dir and dir without matching .md should be ignored.
    (tmp_path / "_shared").mkdir()
    (tmp_path / "cast-empty").mkdir()

    registry = _load_agent_registry(tmp_path)
    assert set(registry.keys()) == {"cast-foo", "cast-bar"}
    assert registry["cast-foo"]["description"] == "a foo agent"


def test_load_registry_handles_yaml_block_scalar_description(tmp_path: Path) -> None:
    block = textwrap.dedent(
        """
        name: cast-blocky
        description: >
          first line
          second line.
          Trigger phrases: "go", "do".
        """
    ).strip()
    _write_agent(tmp_path, "cast-blocky", block)

    registry = _load_agent_registry(tmp_path)
    assert "cast-blocky" in registry
    desc = registry["cast-blocky"]["description"]
    assert "first line" in desc and "Trigger phrases" in desc


def test_get_all_agents_augments_with_run_count(tmp_path: Path, monkeypatch) -> None:
    # Build an isolated agents dir.
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    _write_agent(agents_dir, "cast-counted", "name: cast-counted\ndescription: d")
    _write_agent(agents_dir, "cast-uncounted", "name: cast-uncounted\ndescription: d")

    # Build an isolated DB with one schema-equivalent agent_runs table.
    import sqlite3
    db_path = tmp_path / "diecast.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE agent_runs (id TEXT, agent_name TEXT)")
    conn.executemany(
        "INSERT INTO agent_runs VALUES (?, ?)",
        [("r1", "cast-counted"), ("r2", "cast-counted"), ("r3", "cast-counted")],
    )
    conn.commit()
    conn.close()

    # Reset module cache so the tmp agents_dir takes effect via the explicit param.
    import cast_server.services.agent_service as svc
    svc._AGENT_REGISTRY_CACHE = None

    agents = get_all_agents(db_path=db_path, agents_dir=agents_dir)
    by_name = {a["name"]: a for a in agents}
    assert by_name["cast-counted"]["run_count"] == 3
    assert by_name["cast-uncounted"]["run_count"] == 0
    # Sorted by name.
    assert [a["name"] for a in agents] == ["cast-counted", "cast-uncounted"]


def test_load_registry_returns_empty_when_dir_missing(tmp_path: Path) -> None:
    assert _load_agent_registry(tmp_path / "does-not-exist") == {}
