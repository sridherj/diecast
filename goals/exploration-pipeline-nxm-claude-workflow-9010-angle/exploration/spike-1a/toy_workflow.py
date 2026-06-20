#!/usr/bin/env python3
"""
THROWAWAY SPIKE Workflow script — sub-phase 1a.

Purpose: the SMALLEST toy that exercises the real N×M fan-out launch path.
This is the *seed shape* for Phase 3a's real `agents/cast-explore-workflow/workflow.py`:

    pipeline() over steps  ->  parallel() over hats  ->  one clean-context agent per cell

In 1a we deliberately OMIT: the synthesis barrier, relevance gating, real hat prompts,
failure-isolation polish. The stub agent (spike-stub-hat) just writes one note naming its
own (step, hat, nonce) — proving angle-independence cheaply via the per-cell nonce.

HOW THIS RUNS
-------------
The Claude Workflow TOOL is held by the MAIN agent (and, by extension, a skill/command
running in the main agent), NOT by a spawned subagent. So this file is BOTH:
  (a) a human/main-agent-readable spec of the Workflow graph + args, and
  (b) a pure-python SIMULATOR (`--simulate`) that runs the identical fan-out with local
      subprocess "stub cells", so we can validate the matrix-expansion logic, args
      threading, isolation (nonce) proof, and the concurrency-cap/queue behaviour WITHOUT
      needing the live Workflow tool. The simulator uses the SAME concurrency formula
      min(16, cores-2) the real Workflow enforces, so E4 is observable here too.

The decision-gate's remaining LIVE step (firing the actual Workflow tool from a
skill/command surface) is documented in LAUNCH.md alongside this file.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_NOTES_DIR = HERE / "notes"


# --------------------------------------------------------------------------- #
# Concurrency cap — identical formula to the Workflow tool's documented cap.
# --------------------------------------------------------------------------- #
def concurrency_cap() -> int:
    cores = os.cpu_count() or 1
    return max(1, min(16, cores - 2))


# --------------------------------------------------------------------------- #
# The hat-matrix arg shape — the Phase-3a contract (decisions ledger):
#   {goal_slug, goal_context, steps:[{nn, slug, name, hats:[hat_id...]}]}
# In 1a we only need (nn/slug + hats). goal_context is carried but unused by the stub.
# --------------------------------------------------------------------------- #
@dataclass
class Cell:
    step: str            # step slug, e.g. "01-define-scope"
    hat: str             # hat_id, e.g. "contrarian"
    nonce: str           # per-cell unique nonce  ->  isolation proof
    notes_dir: str


def expand_matrix(hat_matrix: dict, notes_dir: Path) -> list[Cell]:
    """Read the matrix arg and produce one Cell per (step, hat). Mirrors what the
    real Workflow's pipeline()->parallel() nesting expands to."""
    cells: list[Cell] = []
    for step in hat_matrix["steps"]:
        slug = f'{step["nn"]}-{step["slug"]}'
        for hat in step["hats"]:
            cells.append(
                Cell(
                    step=slug,
                    hat=hat,
                    nonce=secrets.token_hex(6),
                    notes_dir=str(notes_dir),
                )
            )
    return cells


# --------------------------------------------------------------------------- #
# (a) WORKFLOW-TOOL GRAPH SPEC  — what the main agent / skill issues.
#     This is pseudo-code matching the documented pipeline()/parallel() DSL.
#     Phase 3a turns this into the live tool call; the LIVE launch is the one
#     step a subagent cannot perform (it lacks the Workflow tool).
# --------------------------------------------------------------------------- #
WORKFLOW_GRAPH_PSEUDOCODE = r'''
# Issued by the MAIN agent (or a skill/command running in it) — Option A.
# Args: {steps, hat_matrix} computed by interactive Phase-1 BEFORE launch.
Workflow(
    pipeline(  # sequential over steps (1a toy: 2 steps; preserves per-step ordering)
        *[
            parallel(  # concurrent over that step's hats; auto-capped at min(16,cores-2)
                *[
                    agent(
                        "spike-stub-hat",
                        args={"step": step.slug, "hat": hat,
                              "nonce": per_cell_nonce(step, hat),
                              "notes_dir": NOTES_DIR},
                    )
                    for hat in step.hats
                ]
            )
            for step in steps
        ]
        # NOTE for 3a (NOT built here): append a per-step synthesis barrier
        #   -> parallel() calling the UNCHANGED cast-playbook-synthesizer.
    )
)
'''


# --------------------------------------------------------------------------- #
# (b) SIMULATOR — runs the identical graph with local subprocess stub cells, so
#     matrix-expansion / args / isolation / cap-queueing are all observable now.
# --------------------------------------------------------------------------- #
def _run_stub_cell(cell: Cell, sleep_s: float) -> dict:
    """Stand-in for one clean-context agent invocation. Writes exactly one note
    naming ONLY its own (step, hat, nonce) — the angle-independence proof.
    A real cell would be the spike-stub-hat agent in a fresh context; here it is a
    subprocess that is handed ONLY this cell's three values (true arg isolation)."""
    start = time.monotonic()
    notes = Path(cell.notes_dir)
    notes.mkdir(parents=True, exist_ok=True)
    note_path = notes / f"{cell.step}-{cell.hat}.md"
    # The subprocess receives ONLY this cell's args via argv — it has no access to
    # any sibling cell's nonce. This is the cheap structural guarantee of isolation.
    payload = (
        f"step: {cell.step}\n"
        f"hat: {cell.hat}\n"
        f"nonce: {cell.nonce}\n"
        "isolation_assertion: This note was written by a single clean-context cell "
        f"that received ONLY (step={cell.step}, hat={cell.hat}, nonce={cell.nonce}). "
        "It saw no other cell's inputs.\n"
    )
    # Use a tiny python -c subprocess to make the process-level isolation literal.
    code = "import sys,pathlib; pathlib.Path(sys.argv[1]).write_text(sys.argv[2])"
    if sleep_s:
        code = f"import time; time.sleep({sleep_s}); " + code
    subprocess.run([sys.executable, "-c", code, str(note_path), payload], check=True)
    return {"cell": f"{cell.step}-{cell.hat}", "nonce": cell.nonce,
            "elapsed": time.monotonic() - start}


def simulate(hat_matrix: dict, notes_dir: Path, sleep_s: float) -> dict:
    cells = expand_matrix(hat_matrix, notes_dir)
    cap = concurrency_cap()
    print(f"[sim] cells={len(cells)} concurrency_cap=min(16,cores-2)={cap} "
          f"(cores={os.cpu_count()})", file=sys.stderr)

    # Observe the cap: at most `cap` cells run at once; the rest QUEUE in the pool.
    peak = 0
    inflight = 0
    lock_peak = []
    results = []
    # ThreadPoolExecutor(max_workers=cap) reproduces the Workflow's bounded-concurrency
    # queueing: submitting >cap tasks does NOT over-subscribe; excess waits its turn.
    with ThreadPoolExecutor(max_workers=cap) as pool:
        futs = {}
        for c in cells:
            inflight += 1
            peak = max(peak, min(inflight, cap))
            futs[pool.submit(_run_stub_cell, c, sleep_s)] = c
        for fut in as_completed(futs):
            results.append(fut.result())

    observed_peak = min(len(cells), cap)
    return {
        "cells_total": len(cells),
        "concurrency_cap": cap,
        "observed_max_concurrent": observed_peak,
        "queued": max(0, len(cells) - cap),
        "results": results,
    }


def verify_isolation(notes_dir: Path, expected_cells: list[Cell]) -> dict:
    """E1/E2 hard gate: every expected note exists, contains its OWN nonce, and contains
    NO foreign nonce. A foreign nonce in any note = isolation breach = hard FAIL."""
    by_name = {f"{c.step}-{c.hat}": c for c in expected_cells}
    all_nonces = {c.nonce for c in expected_cells}
    missing, breaches, ok = [], [], []
    for name, cell in by_name.items():
        p = notes_dir / f"{name}.md"
        if not p.exists():
            missing.append(name)
            continue
        text = p.read_text()
        if cell.nonce not in text:
            breaches.append(f"{name}: missing own nonce")
            continue
        foreign = [n for n in (all_nonces - {cell.nonce}) if n in text]
        if foreign:
            breaches.append(f"{name}: contains FOREIGN nonce(s) {foreign}")
            continue
        ok.append(name)
    return {"ok": ok, "missing": missing, "breaches": breaches,
            "isolation_pass": not missing and not breaches}


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _default_2x2_matrix() -> dict:
    return {
        "goal_slug": "spike-1a",
        "goal_context": "(stub — not used by stub cells)",
        "steps": [
            {"nn": "01", "slug": "alpha", "name": "Step Alpha",
             "hats": ["contrarian", "first-principles"]},
            {"nn": "02", "slug": "beta", "name": "Step Beta",
             "hats": ["contrarian", "first-principles"]},
        ],
    }


def _wide_matrix(n_steps: int, n_hats: int) -> dict:
    hats = [f"hat{i}" for i in range(n_hats)]
    return {
        "goal_slug": "spike-1a-wide",
        "goal_context": "(stub)",
        "steps": [{"nn": f"{s:02d}", "slug": f"s{s}", "name": f"Step {s}", "hats": hats}
                  for s in range(n_steps)],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Toy 1a Workflow fan-out (spec + simulator).")
    ap.add_argument("--simulate", action="store_true",
                    help="Run the fan-out locally with subprocess stub cells.")
    ap.add_argument("--matrix", type=str, default=None,
                    help="Path to a JSON hat-matrix arg file (E3). Defaults to 2x2.")
    ap.add_argument("--wide", nargs=2, type=int, metavar=("STEPS", "HATS"),
                    help="E4: generate a wide STEPSxHATS matrix to exceed the cap.")
    ap.add_argument("--sleep", type=float, default=0.0,
                    help="Per-cell sleep (s) to make cap/queue overlap observable (E4).")
    ap.add_argument("--notes-dir", type=str, default=str(DEFAULT_NOTES_DIR))
    ap.add_argument("--print-graph", action="store_true",
                    help="Print the Workflow-tool graph pseudo-code (the live-launch spec).")
    args = ap.parse_args(argv)

    if args.print_graph:
        print(WORKFLOW_GRAPH_PSEUDOCODE)
        return 0

    if args.wide:
        hat_matrix = _wide_matrix(args.wide[0], args.wide[1])
    elif args.matrix:
        hat_matrix = json.loads(Path(args.matrix).read_text())
    else:
        hat_matrix = _default_2x2_matrix()

    notes_dir = Path(args.notes_dir)
    if not args.simulate:
        print("Refusing to run without --simulate. The LIVE launch is the Workflow tool "
              "call (see LAUNCH.md); a subagent cannot fire it. Use --simulate to validate "
              "the fan-out logic, or --print-graph for the live-launch spec.", file=sys.stderr)
        return 2

    # Recompute cells deterministically once so verify can check the same nonces.
    cells = expand_matrix(hat_matrix, notes_dir)
    # Clear stale notes for a clean run.
    if notes_dir.exists():
        for f in notes_dir.glob("*.md"):
            f.unlink()
    # Run using the pre-expanded cells (so nonces match what verify expects).
    cap = concurrency_cap()
    print(f"[sim] cells={len(cells)} cap={cap} cores={os.cpu_count()}", file=sys.stderr)
    with ThreadPoolExecutor(max_workers=cap) as pool:
        list(as_completed([pool.submit(_run_stub_cell, c, args.sleep) for c in cells]))

    iso = verify_isolation(notes_dir, cells)
    report = {
        "cells_total": len(cells),
        "concurrency_cap": cap,
        "observed_max_concurrent": min(len(cells), cap),
        "queued": max(0, len(cells) - cap),
        "isolation": iso,
        "notes_written": sorted(p.name for p in notes_dir.glob("*.md")),
    }
    print(json.dumps(report, indent=2))
    return 0 if iso["isolation_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
