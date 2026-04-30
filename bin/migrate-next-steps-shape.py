#!/usr/bin/env python3
"""Bulk-rewrite legacy ``next_steps: ["...", "..."]`` to the typed shape (US14).

Internal use; not on user PATH. One-shot data migration; obsolete after the
matching deploy. Kept for users on stale databases.

For each ``.agent-run_*.output.json`` (or ``.agent-<run_id>.output.json``), convert
string entries to ``{"command": <original>, "rationale": "", "artifact_anchor": null}``.

Run once per repo. Idempotent: skips already-typed entries. Returns counts on stdout.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


LEGACY_GLOBS = (".agent-run_*.output.json", ".agent-*.output.json")


def migrate_json(path: Path) -> dict:
    counts = {"migrated": 0, "skipped": 0, "errors": 0}
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        counts["errors"] += 1
        return counts
    if not isinstance(data, dict):
        counts["skipped"] += 1
        return counts
    steps = data.get("next_steps")
    if not isinstance(steps, list):
        counts["skipped"] += 1
        return counts
    new = []
    changed = False
    for s in steps:
        if isinstance(s, str):
            new.append({"command": s, "rationale": "", "artifact_anchor": None})
            changed = True
        elif isinstance(s, dict):
            new.append(s)  # already typed
        else:
            new.append(s)
    if changed:
        data["next_steps"] = new
        path.write_text(json.dumps(data, indent=2))
        counts["migrated"] = 1
    else:
        counts["skipped"] = 1
    return counts


def iter_targets(root: Path):
    if root.is_file():
        yield root
        return
    seen = set()
    for pattern in LEGACY_GLOBS:
        for p in root.rglob(pattern):
            if p in seen:
                continue
            seen.add(p)
            yield p


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", type=Path, help="Repo root or specific output JSON file")
    args = ap.parse_args()
    total = {"migrated": 0, "skipped": 0, "errors": 0}
    for p in iter_targets(args.root):
        r = migrate_json(p)
        for k, v in r.items():
            total[k] = total.get(k, 0) + v
    print(json.dumps(total))
    if total["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
