"""Orchestration service — pure DAG logic for manifest parsing and phase execution planning.

Extracted from scripts/orchestrate.py. No subprocess/Claude/tmux dependencies.
"""

from __future__ import annotations

import json
import re
import sys
from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Phase:
    id: str
    name: str
    file: str
    depends_on: list[str] = field(default_factory=list)
    status: str = "Not Started"
    notes: str = ""


@dataclass
class GroupResult:
    """Result of executing one group (or batch within a group)."""
    succeeded: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    timed_out: list[str] = field(default_factory=list)
    rate_exhausted: list[str] = field(default_factory=list)

    @property
    def has_failures(self) -> bool:
        return bool(self.failed or self.timed_out or self.rate_exhausted)

    def merge(self, other: "GroupResult") -> None:
        """Merge another GroupResult into this one."""
        self.succeeded.extend(other.succeeded)
        self.failed.extend(other.failed)
        self.timed_out.extend(other.timed_out)
        self.rate_exhausted.extend(other.rate_exhausted)


def is_gate(phase: Phase) -> bool:
    """Check if a phase is a decision gate."""
    return phase.id.upper().startswith("G") or phase.file.startswith("gate_")


def parse_manifest(manifest_path: Path) -> list[Phase]:
    """Parse the Phase Overview table from a _manifest.md file."""
    text = manifest_path.read_text()
    phases: list[Phase] = []

    in_table = False
    _file_col_first = False

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_table:
                break  # table ended
            continue

        cells = [c.strip() for c in stripped.split("|")]
        cells = cells[1:-1]  # drop leading/trailing empties
        if len(cells) < 5:
            continue

        # Detect header row
        if cells[0] == "#" and "Phase" in cells[1]:
            in_table = True
            _file_col_first = "file" in cells[1].lower()
            continue

        # Skip separator row (---|---|...)
        if all(c.replace("-", "").replace(":", "").strip() == "" for c in cells):
            continue

        if not in_table:
            continue

        phase_id = cells[0].strip()

        # Support both 6-column formats:
        #   Legacy: # | Phase (name) | File | Deps | Status | Notes
        #   New:    # | Phase File   | Title | Deps | Status | Notes
        # and 5-column (# | Phase | Deps | Status | Notes).
        if len(cells) >= 6:
            if _file_col_first:
                file_cell = cells[1].strip().strip("`")
                name = cells[2].strip()
            else:
                name = cells[1].strip()
                file_cell = cells[2].strip().strip("`")
            deps_raw = cells[3].strip()
            status = cells[4].strip()
            notes = cells[5].strip()
        else:
            name = cells[1].strip()
            file_cell = name  # derive file from phase name
            deps_raw = cells[2].strip()
            status = cells[3].strip()
            notes = cells[4].strip() if len(cells) > 4 else ""

        # Parse dependencies
        depends_on: list[str] = []
        if deps_raw not in ("—", "---", "-", "–", "None", "none", "", "--"):
            dep_str = deps_raw.replace("Phase", "").replace("phase", "")
            for part in re.split(r"[,+]", dep_str):
                part = part.strip()
                if part:
                    depends_on.append(part)

        # Ensure file has .md extension
        if not file_cell.endswith(".md"):
            file_cell = file_cell + ".md"

        phases.append(Phase(
            id=phase_id,
            name=name,
            file=file_cell,
            depends_on=depends_on,
            status=status,
            notes=notes,
        ))

    if not phases:
        raise ValueError(f"No phases found in {manifest_path}")

    # Resolve "All" dependencies: replace with all other phase IDs
    all_ids = [p.id for p in phases]
    for p in phases:
        if "All" in p.depends_on or "all" in p.depends_on:
            p.depends_on = [pid for pid in all_ids if pid != p.id]

    return phases


def _reachable_forward(by_id: dict[str, Phase], start: str) -> set[str]:
    """BFS forward from `start` through the dependency graph."""
    children: dict[str, list[str]] = {pid: [] for pid in by_id}
    for p in by_id.values():
        for dep in p.depends_on:
            if dep in children:
                children[dep].append(p.id)

    reachable: set[str] = set()
    queue = deque([start])
    while queue:
        pid = queue.popleft()
        if pid in reachable:
            continue
        reachable.add(pid)
        for child in children[pid]:
            queue.append(child)
    return reachable


def build_execution_groups(
    phases: list[Phase],
    from_phase: str | None = None,
) -> list[list[Phase]]:
    """Kahn's algorithm topological sort, returning groups of parallelizable phases.

    Phases with status Done/Verified are skipped but still resolve as deps.
    """
    by_id = {p.id: p for p in phases}

    if from_phase:
        if from_phase not in by_id:
            raise ValueError(f"--from-phase '{from_phase}' not found in manifest")
        reachable = _reachable_forward(by_id, from_phase)
        for p in phases:
            if p.id not in reachable:
                p.status = "Done"

    # Build adjacency + in-degree
    in_degree: dict[str, int] = {p.id: 0 for p in phases}
    children: dict[str, list[str]] = {p.id: [] for p in phases}
    for p in phases:
        for dep in p.depends_on:
            if dep in children:
                children[dep].append(p.id)
                in_degree[p.id] += 1

    # Kahn's
    queue = deque(pid for pid, deg in in_degree.items() if deg == 0)
    groups: list[list[Phase]] = []

    visited = 0
    while queue:
        group: list[Phase] = []
        next_queue: list[str] = []
        for pid in queue:
            visited += 1
            phase = by_id[pid]
            if phase.status not in ("Done", "Verified"):
                group.append(phase)
            for child in children[pid]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    next_queue.append(child)
        if group:
            groups.append(group)
        queue = deque(next_queue)

    if visited != len(phases):
        stuck = [p.id for p in phases if in_degree[p.id] > 0]
        raise ValueError(f"Dependency cycle detected involving phases: {stuck}")

    return groups


def update_manifest_status(
    manifest_path: Path, phase_id: str, new_status: str, notes: str = ""
) -> None:
    """Update the Status (and optionally Notes) cell for a given phase in the manifest table."""
    lines = manifest_path.read_text().splitlines()
    updated = False

    # First pass: find the Status and Notes column indices from the header row
    status_col = None
    notes_col = None
    for line in lines:
        if not line.strip().startswith("|"):
            continue
        raw_cells = line.split("|")
        for ci, cell in enumerate(raw_cells):
            if cell.strip().lower() == "status":
                status_col = ci
            if cell.strip().lower() == "notes":
                notes_col = ci
        if status_col is not None:
            break

    if status_col is None:
        return  # no Status column found

    for i, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        raw_cells = line.split("|")
        if len(raw_cells) <= status_col:
            continue
        # Match by phase id (first data column after leading empty)
        if len(raw_cells) > 1 and raw_cells[1].strip() == phase_id:
            raw_cells[status_col] = f" {new_status} "
            if notes and notes_col is not None and len(raw_cells) > notes_col:
                raw_cells[notes_col] = f" {notes} "
            lines[i] = "|".join(raw_cells)
            updated = True
            break

    if updated:
        manifest_path.write_text("\n".join(lines) + "\n")


# ── CLI interface ────────────────────────────────────────────────────────────


def _cli_parse_manifest(path: str) -> None:
    """CLI: parse manifest and output JSON."""
    manifest_path = Path(path)
    if not manifest_path.exists():
        print(json.dumps({"error": f"File not found: {path}"}), file=sys.stderr)
        sys.exit(1)

    phases = parse_manifest(manifest_path)
    groups = build_execution_groups(phases)

    output = {
        "phases": [asdict(p) for p in phases],
        "groups": [[asdict(p) for p in group] for group in groups],
    }
    print(json.dumps(output, indent=2))


def _cli_update_status(path: str, phase_id: str, status: str, notes: str = "") -> None:
    """CLI: update a phase's status in the manifest."""
    manifest_path = Path(path)
    if not manifest_path.exists():
        print(json.dumps({"error": f"File not found: {path}"}), file=sys.stderr)
        sys.exit(1)

    update_manifest_status(manifest_path, phase_id, status, notes)
    print(json.dumps({"updated": phase_id, "status": status}))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m taskos.services.orchestration_service <command> [args]")
        print("Commands: parse-manifest <path>, update-status <path> <phase_id> <status> [notes]")
        sys.exit(1)

    command = sys.argv[1]
    if command == "parse-manifest":
        if len(sys.argv) < 3:
            print("Usage: parse-manifest <manifest_path>", file=sys.stderr)
            sys.exit(1)
        _cli_parse_manifest(sys.argv[2])
    elif command == "update-status":
        if len(sys.argv) < 5:
            print("Usage: update-status <manifest_path> <phase_id> <status> [notes]", file=sys.stderr)
            sys.exit(1)
        notes = sys.argv[5] if len(sys.argv) > 5 else ""
        _cli_update_status(sys.argv[2], sys.argv[3], sys.argv[4], notes)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)
