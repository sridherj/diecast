#!/usr/bin/env python3
"""Set per-agent `proactive` defaults in agents/cast-*/config.yaml (US14).

Idempotent: re-running with the same data is a no-op. Creates `config.yaml`
when an agent in the table doesn't have one yet.
"""
from __future__ import annotations

from pathlib import Path

import yaml

CHAIN = {
    "cast-refine-requirements", "cast-goal-decomposer", "cast-explore", "cast-web-researcher",
    "cast-code-explorer", "cast-playbook-synthesizer", "cast-high-level-planner",
    "cast-detailed-plan", "cast-fanout-detailed-plan", "cast-create-execution-plan",
    "cast-update-spec", "cast-task-suggester", "cast-preso-narrative",
}
TERMINAL = {
    "cast-orchestrate", "cast-subphase-runner", "cast-tasks", "cast-goals", "cast-runs",
    "cast-review-code", "cast-plan-review", "cast-wrap-up",
}


def main() -> None:
    agents_dir = Path("agents")
    for name in sorted(CHAIN | TERMINAL):
        adir = agents_dir / name
        if not adir.is_dir():
            print(f"SKIP missing dir: {adir}")
            continue
        cfg = adir / "config.yaml"
        data = yaml.safe_load(cfg.read_text()) if cfg.exists() else {}
        data = data or {}
        proactive = name in CHAIN
        if data.get("proactive") == proactive:
            print(f"OK    {name}: proactive={proactive} (already set)")
            continue
        data["proactive"] = proactive
        cfg.write_text(yaml.safe_dump(data, sort_keys=False))
        print(f"WROTE {name}: proactive={proactive}")


if __name__ == "__main__":
    main()
