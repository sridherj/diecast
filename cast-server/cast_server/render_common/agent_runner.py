"""The tool-free `claude -p` agent subprocess seam, shared by both render-jobs.

`AgentRunner` is a Protocol so tests inject fakes; `ProductionAgentRunner` runs the real
`claude -p <msg> --append-system-prompt <agent.md> --model <m> --tools ""` subprocess with the
`agent_service.py` hygiene precedent (`env -u CLAUDECODE`, a clean child env, an explicit per-job
cwd). `--tools ""` disables every tool, so a maker is STRUCTURALLY unable to write a canonical file.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Protocol

from cast_server.config import DIECAST_ROOT
from cast_server.models.agent_config import load_agent_config


class AgentRunner(Protocol):
    """Run one tool-free agent and return its raw stdout. Tests inject fakes."""

    def run_agent(self, agent_name: str, user_msg: str, *, timeout_s: int) -> str: ...


class AgentRunError(RuntimeError):
    """A maker subprocess failed (non-zero exit, timeout, or spawn error)."""


def _clean_child_env(*exclude: str) -> dict[str, str]:
    """`os.environ` minus the excluded keys — never mutates the global env.

    Mirrors `agent_service._clean_child_env`: a `claude -p` that inherits a parent session's
    `CLAUDECODE` / `CLAUDE_SESSION_ID` can hang or recurse. Env isolation is not optional.
    """
    skip = set(exclude)
    return {k: v for k, v in os.environ.items() if k not in skip}


def _load_agent_md(agent_name: str) -> str:
    """Read `agents/<name>/<name>.md` (the agent's system prompt). Raises if absent."""
    path = Path(DIECAST_ROOT) / "agents" / agent_name / f"{agent_name}.md"
    return path.read_text(encoding="utf-8")


class ProductionAgentRunner:
    """Run an agent as `claude -p <msg> --append-system-prompt <agent.md> --model <m> --tools ""`.

    `--tools ""` disables all tools, so the maker is structurally unable to write any canonical
    file. The runner inlines every agent input into `user_msg` (the pipeline builds the prompts).
    Subprocess hygiene pins to the `agent_service.py` precedent: `env -u CLAUDECODE` + an explicit
    per-job cwd + a clean child env.
    """

    def __init__(self, cwd: Path) -> None:
        self._cwd = Path(cwd)

    def run_agent(self, agent_name: str, user_msg: str, *, timeout_s: int) -> str:
        agent_md = _load_agent_md(agent_name)
        cfg = load_agent_config(agent_name)
        env = _clean_child_env("CLAUDECODE", "CLAUDE_SESSION_ID")
        self._cwd.mkdir(parents=True, exist_ok=True)
        try:
            proc = subprocess.run(
                ["claude", "-p", user_msg, "--append-system-prompt", agent_md,
                 "--model", cfg.model, "--tools", ""],
                capture_output=True, text=True, timeout=timeout_s,
                cwd=str(self._cwd), env=env,
            )
        except subprocess.TimeoutExpired as exc:
            raise AgentRunError(f"{agent_name} timed out after {timeout_s}s") from exc
        except OSError as exc:
            raise AgentRunError(f"{agent_name} could not be spawned: {exc}") from exc
        if proc.returncode != 0:
            raise AgentRunError(
                f"{agent_name} exited {proc.returncode}: {proc.stderr.strip()[:300]}"
            )
        return proc.stdout
