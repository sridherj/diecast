"""Per-agent configuration loaded from YAML files."""

import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator
import yaml

from cast_server.config import DIECAST_ROOT

KNOWN_MODELS = {"opus", "sonnet", "haiku"}
VALID_ARTIFACT_DIRECTORIES = {None, "goal_dir", "external_project_dir"}


class AgentConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    agent_id: str
    model: str = "opus"
    headless: bool = False
    timeout_minutes: int = 60
    trust_level: str = "standard"  # readonly | standard | privileged
    allowed_delegations: list[str] = []
    context_mode: str = "full"  # full | lightweight
    interactive: bool = False
    artifact_directory: str | None = None  # None | "goal_dir" | "external_project_dir"
    dispatch_mode: str = "http"

    @field_validator("model")
    @classmethod
    def validate_model(cls, v):
        if v not in KNOWN_MODELS:
            return "opus"  # Graceful fallback
        return v

    @field_validator("dispatch_mode")
    @classmethod
    def validate_dispatch_mode(cls, v):
        if v not in {"http", "subagent"}:
            return "http"  # Graceful fallback — preserves sibling fields
        return v

    @field_validator("timeout_minutes")
    @classmethod
    def validate_timeout(cls, v):
        if v <= 0:
            return 60
        return v

    @field_validator("artifact_directory")
    @classmethod
    def validate_artifact_directory(cls, v):
        if v not in VALID_ARTIFACT_DIRECTORIES:
            return None  # Graceful fallback for unknown values
        return v


# Cache: {agent_id: (mtime, AgentConfig)}
_config_cache: dict[str, tuple[float, AgentConfig]] = {}


def _candidate_config_paths(agent_id: str) -> list[Path]:
    """Production agents/ first; CAST_TEST_AGENTS_DIR (if set) as a fallback so
    test agents resolve in test-mode without polluting the prod registry. Mirrors
    the merge applied in agent_service.get_all_agents()."""
    paths = [Path(DIECAST_ROOT) / "agents" / agent_id / "config.yaml"]
    test_dir = os.environ.get("CAST_TEST_AGENTS_DIR")
    if test_dir:
        paths.append(Path(test_dir) / agent_id / "config.yaml")
    return paths


def load_agent_config(agent_id: str) -> AgentConfig:
    """Load agent config from agents/<agent_id>/config.yaml with mtime-based cache."""
    config_path = next(
        (p for p in _candidate_config_paths(agent_id) if p.exists()),
        None,
    )

    if config_path is not None:
        mtime = os.stat(config_path).st_mtime
        cache_key = f"{config_path}:{agent_id}"
        if cache_key in _config_cache and _config_cache[cache_key][0] == mtime:
            return _config_cache[cache_key][1]
        try:
            data = yaml.safe_load(config_path.read_text())
            config = AgentConfig(agent_id=agent_id, **(data or {}))
        except Exception:
            config = AgentConfig(agent_id=agent_id)  # Fallback to defaults
        _config_cache[cache_key] = (mtime, config)
        return config

    return AgentConfig(agent_id=agent_id)  # No config file -> defaults
