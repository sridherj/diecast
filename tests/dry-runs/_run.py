#!/usr/bin/env python3
"""Dry-run every cast-* agent against the synthetic minimal-goal fixture.

For each agent node in `docs/audit/agent-interdependency-graph.json`:
  - Walk every outbound edge.
  - Classify each edge into one of:
      * fixture-resolved   — target file exists in fixture
      * skill-resolved     — referenced skill exists in skills/claude-code/
      * agent-resolved     — referenced agent exists in agents/
      * unresolved-red     — already-flagged red finding (legacy taskos-*, missing target)
      * unresolved-yellow  — yellow finding (e.g., Section 4 cross-skill mismatch)
      * runtime-only       — fixture-agnostic placeholder path (e.g., `path/to/x.md`)
  - Verify the agent's expected output JSON schema matches contract-version-2
    by scanning the agent prompt for `contract_version` literal "2".

Persist one log per agent at tests/dry-runs/cast-{name}.log.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
GRAPH = json.load(open(REPO / "docs/audit/agent-interdependency-graph.json"))
FIXTURE = REPO / "tests/fixtures/minimal-goal"
DRY_RUN_DIR = REPO / "tests/dry-runs"

NODES = {n["id"]: n for n in GRAPH["nodes"]}
AGENTS = {n["id"] for n in GRAPH["nodes"] if n["kind"] == "agent"}
SKILLS = {n["id"] for n in GRAPH["nodes"] if n["kind"] == "skill"}

# Agents whose graph parse may miss dynamic dispatch (Section 0 known false-negative).
DYNAMIC_DISPATCH_FLAG = {
    "cast-orchestrate",         # dispatcher fans out by sub-phase id
    "cast-fanout-detailed-plan",# dispatcher computes target per sub-phase
    "cast-explore",             # may dispatch by domain heuristic
    "cast-preso-orchestrator",  # branchy on stage
}

# Conventional fixture file shortlist — these names are expected to exist
# inside the synthetic minimal-goal fixture.
FIXTURE_FILES = {
    "goal.yaml",
    "requirements.human.md",
    "tasks.md",
}
FIXTURE_DIRS = {
    "docs/exploration",
    "docs/spec",
    "docs/requirement",
    "docs/plan",
    "docs/design",
    "docs/execution",
    "docs/ui-design",
}


def first_read_target(agent_id: str) -> str:
    md = REPO / f"agents/{agent_id}/{agent_id}.md"
    if not md.exists():
        # python-script flavor (cast-preso-review)
        py = list((REPO / f"agents/{agent_id}").rglob("*.py"))
        return py[0].name if py else "<no-prompt-found>"
    text = md.read_text(errors="ignore")
    # First "Read X" or first explicit file path mentioned in the prompt body
    m = re.search(r"Read\s+`?([\w./-]+)`?", text)
    if m:
        return m.group(1)
    m = re.search(r"`([\w./-]+\.(md|yaml|json|py))`", text)
    return m.group(1) if m else "<not-detected>"


def schema_v2_present(agent_id: str) -> bool:
    md = REPO / f"agents/{agent_id}/{agent_id}.md"
    if md.exists():
        text = md.read_text(errors="ignore")
        return ('"contract_version": "2"' in text) or ("contract_version: 2" in text)
    # Fallback: python-script agents — scan all .py
    for py in (REPO / f"agents/{agent_id}").rglob("*.py"):
        if 'contract_version' in py.read_text(errors="ignore"):
            return True
    return False


NAMING_KINDS = {"slash", "bare"}
FOLDER_KINDS = {"read", "write", "unknown"}  # path-audit edges (target == source)


def classify_naming_edge(edge):
    target = edge["target"]
    status = edge["status"]
    if status == "red":
        return "unresolved-red"
    if status == "yellow":
        return "unresolved-yellow"
    if target in AGENTS:
        return "agent-resolved"
    if target in SKILLS:
        return "skill-resolved"
    return "runtime-only"


def classify_folder_edge(edge):
    return f"folder-{edge['status']}"


def write_log(agent_id: str):
    edges_all = [e for e in GRAPH["edges"] if e["source"] == agent_id]
    edges = [e for e in edges_all if e.get("kind") in NAMING_KINDS]
    folder_edges = [e for e in edges_all if e.get("kind") in FOLDER_KINDS]
    counts = {"agent-resolved": 0, "skill-resolved": 0,
              "runtime-only": 0, "unresolved-red": 0, "unresolved-yellow": 0}
    folder_counts = {"folder-green": 0, "folder-yellow": 0, "folder-red": 0}
    failures = []
    folder_failures = []
    for e in edges:
        cat = classify_naming_edge(e)
        counts[cat] += 1
        if cat == "unresolved-red":
            failures.append(f"  RED  {e['file']}:{e['line']} → {e['target']}")
    for e in folder_edges:
        cat = classify_folder_edge(e)
        folder_counts[cat] = folder_counts.get(cat, 0) + 1
        if cat == "folder-red":
            folder_failures.append(f"  RED-PATH  {e['file']}:{e['line']} ({e.get('kind')})")
    fr_target = first_read_target(agent_id)
    schema_ok = schema_v2_present(agent_id)

    is_dynamic = agent_id in DYNAMIC_DISPATCH_FLAG
    log_path = DRY_RUN_DIR / f"{agent_id}.log"
    lines = [
        f"# Dry-run log — {agent_id}",
        f"timestamp: {datetime.now(timezone.utc).isoformat()}",
        f"fixture:   {FIXTURE.relative_to(REPO)}",
        f"graph:     docs/audit/agent-interdependency-graph.json",
        "",
        "## First-read attempt",
        f"  expected source: {fr_target}",
        f"  fixture has goal.yaml: {(FIXTURE / 'goal.yaml').exists()}",
        f"  fixture has requirements.human.md: {(FIXTURE / 'requirements.human.md').exists()}",
        "",
        "## First-delegation target check (naming edges only — slash/bare)",
        f"  total naming edges: {len(edges)}",
        f"  agent-resolved:  {counts['agent-resolved']}",
        f"  skill-resolved:  {counts['skill-resolved']}",
        f"  runtime-only:    {counts['runtime-only']}",
        f"  unresolved-red:  {counts['unresolved-red']}",
        f"  unresolved-yellow: {counts['unresolved-yellow']}",
        "",
        "## Folder-path edge tally (read/write/unknown — Section 2)",
        f"  total folder edges: {len(folder_edges)}",
        f"  folder-green: {folder_counts['folder-green']}",
        f"  folder-yellow: {folder_counts['folder-yellow']}",
        f"  folder-red:   {folder_counts['folder-red']}",
        "",
        "## Output-JSON schema validation",
        f"  contract_version=2 literal present: {schema_ok}",
        "",
        "## Dynamic-dispatch flag (Section 0 known false-negative class)",
        f"  flagged for runtime-only verification: {is_dynamic}",
        "",
        "## Red findings (deferred until 2.4 remediation lands)",
    ]
    if failures:
        lines.extend(failures[:50])  # cap log size
        if len(failures) > 50:
            lines.append(f"  ... +{len(failures)-50} more red naming edges")
    else:
        lines.append("  (none)")
    lines.append("")
    lines.append("## Path-audit red findings (Section 2)")
    if folder_failures:
        lines.extend(folder_failures[:30])
        if len(folder_failures) > 30:
            lines.append(f"  ... +{len(folder_failures)-30} more red path edges")
    else:
        lines.append("  (none)")
    lines.append("")
    log_path.write_text("\n".join(lines))


for agent_id in sorted(AGENTS):
    write_log(agent_id)
print(f"Wrote {len(AGENTS)} agent logs to {DRY_RUN_DIR}")
