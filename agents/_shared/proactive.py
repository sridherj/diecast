"""Proactive flag resolution for cast-* agents (US14).

Resolution order (highest precedence first):

    1. proactive_overrides[<agent_name>] in ~/.cast/config.yaml
    2. per-agent default (config.yaml ``proactive`` key)
    3. proactive_global in ~/.cast/config.yaml
    4. False (final fallback)
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml


def resolve_proactive(
    agent_name: str,
    per_agent_default: Optional[bool],
    config_path: Optional[Path] = None,
) -> bool:
    """Return whether ``agent_name`` should render its next_steps proactively.

    ``per_agent_default`` is the value declared in the agent's own ``config.yaml``
    (``True``/``False``) or ``None`` when the agent does not declare one.
    """
    cfg = _load_config(config_path)
    overrides = cfg.get("proactive_overrides") or {}
    if agent_name in overrides:
        return bool(overrides[agent_name])
    if per_agent_default is not None:
        return bool(per_agent_default)
    if "proactive_global" in cfg:
        return bool(cfg["proactive_global"])
    return False


def _load_config(path: Optional[Path]) -> dict:
    p = path or Path.home() / ".cast" / "config.yaml"
    if not p.exists():
        return {}
    try:
        loaded = yaml.safe_load(p.read_text()) or {}
    except yaml.YAMLError:
        return {}
    return loaded if isinstance(loaded, dict) else {}
