#!/usr/bin/env python
"""SC-001 sign-off eval for the `cast-requirements-checker` agent (Phase 3a, sp5a — WP-F).

This is the **phase gate**, distinct from the deterministic golden snapshots that run in every
CI pass (`test_requirements_renderer.py`). It dispatches the checker — as an unfamiliar reader —
against each work-family's rendered Goal Card and asserts the headline criterion:

    SC-001: from the zero-click surface alone, the checker can state the WHAT.

Concretely the gate is, **for every family**:

    can_state_what == true   AND   missing[] contains no entry naming job / outcome / scope

(the binary PASS rule from the shared-context Naming Contract — the gate is the boolean, never
the `score` float, so judge variance cannot flip it).

Why it is NOT a `test_*` file
------------------------------
It is named ``eval_*`` so pytest's default collection skips it (the Phase 2 classifier-eval
precedent), and a live run shells out to the ``claude`` CLI (slow + network). Run it by hand:

    # Live — dispatch the real checker prompt per family (slow; needs the claude CLI):
    uv run --project cast-server python cast-server/tests/eval_render_checker.py --live

    # Offline replay from a saved verdicts file (deterministic, no network — makes the harness
    # itself testable and the report regenerable):
    uv run --project cast-server python cast-server/tests/eval_render_checker.py \
        --verdicts /tmp/render_verdicts.json

    # Save a live run's verdicts for later replay / inspection:
    uv run --project cast-server python cast-server/tests/eval_render_checker.py \
        --live --out-verdicts /tmp/render_verdicts.json

Faithfulness note
-----------------
The agent ships judging ONLY the zero-click surface, which it obtains by running
``bin/cast-render-zero-click``. This harness performs that exact extraction
(``extract_zero_click_view`` — the same code path the bin wraps) and feeds the result to the
checker as its input with tools disabled. So the INPUT is byte-deterministic (only the LLM
judgement varies), and the agent physically cannot see collapsed content — exactly the gate's
design. The checker prompt file is the single source of truth (also pinned by
``test_requirements_checker_agent.py``), so a live run exercises what ships.

Below the bar, the *first* lever is the checker prompt (a content edit to
``cast-requirements-checker.md``) or the renderer's Goal-Card IA — never weakening the gate.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# --- repo bootstrap (mirror conftest: put cast-server/ on sys.path) --------------------
_TESTS_DIR = Path(__file__).resolve().parent
_CAST_SERVER_DIR = _TESTS_DIR.parent
_REPO_ROOT = _CAST_SERVER_DIR.parent
if str(_CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(_CAST_SERVER_DIR))

from cast_server.requirements_render.families import WorkFamily  # noqa: E402
from cast_server.requirements_render.parser import parse_requirements  # noqa: E402
from cast_server.requirements_render.renderer import render_requirements  # noqa: E402
from cast_server.requirements_render.zero_click import extract_zero_click_view  # noqa: E402

_CHECKER_PROMPT = _REPO_ROOT / "agents" / "cast-requirements-checker" / "cast-requirements-checker.md"

# The gated WHAT pieces — a `missing[]` entry naming any of these fails the binary gate.
_GATED_PIECES = ("job", "outcome", "scope")


# ---------------------------------------------------------------------------
# Family render inputs — reuse the deterministic programmatic builders
# ---------------------------------------------------------------------------
# The Phase 2 WP-D `tests/fixtures/family_docs/` set has not landed; the goldens and this eval
# render the same programmatic family docs the behavioural suite builds (see
# test_requirements_renderer.py). Imported here so there is ONE builder, not a fork.
def _load_family_doc_builder():
    """Import `_build_family_doc` from the behavioural test module (single source of truth)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_rr_test_builders", _TESTS_DIR / "test_requirements_renderer.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module._build_family_doc


@dataclass
class FamilyCase:
    family: WorkFamily
    zero_click_view: str
    render_warnings: tuple[str, ...]


def build_cases() -> list[FamilyCase]:
    """Render each family, extract its zero-click surface (the checker's input)."""
    build_family_doc = _load_family_doc_builder()
    cases: list[FamilyCase] = []
    for family in list(WorkFamily):
        result = render_requirements(parse_requirements(build_family_doc(family)))
        cases.append(
            FamilyCase(
                family=family,
                zero_click_view=extract_zero_click_view(result.html),
                render_warnings=result.warnings,
            )
        )
    return cases


# ---------------------------------------------------------------------------
# Verdict backends
# ---------------------------------------------------------------------------
def check_live(case: FamilyCase, model: str = "sonnet", timeout_s: int = 240) -> dict:
    """Dispatch the real checker prompt over one family's zero-click view via ``claude -p``.

    `--tools ""` disables all tools: the harness has already produced the zero-click surface
    (the gate input by construction), so the agent is pure text-in / JSON-out here and must
    never act. The checker prompt is the single source of truth."""
    prompt = _CHECKER_PROMPT.read_text(encoding="utf-8")
    user_msg = (
        "Here is the zero-click view of a rendered refined_requirements.html "
        "(the exact output of `bin/cast-render-zero-click`). Judge ONLY this surface and "
        "emit your bare JSON verdict.\n\n"
        "----- BEGIN ZERO-CLICK VIEW -----\n"
        f"{case.zero_click_view}\n"
        "----- END ZERO-CLICK VIEW -----\n"
    )
    proc = subprocess.run(
        ["claude", "-p", user_msg, "--append-system-prompt", prompt, "--model", model, "--tools", ""],
        capture_output=True,
        text=True,
        timeout=timeout_s,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI failed for {case.family.value}: {proc.stderr.strip()[:400]}")
    return _parse_verdict_json(proc.stdout)


def _parse_verdict_json(raw: str) -> dict:
    """Extract the single bare JSON verdict object (tolerant of stray code fences)."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{") :]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON object in checker output: {raw[:200]!r}")
    return json.loads(text[start : end + 1])


def run_verdicts(cases: list[FamilyCase], model: str) -> dict[str, dict]:
    """Check every family live; collect verdicts keyed by family value. A per-family failure is
    recorded (never silently dropped) so the gate's denominator stays honest."""
    verdicts: dict[str, dict] = {}
    for i, case in enumerate(cases, 1):
        print(f"  [{i}/{len(cases)}] checking {case.family.value} ...", file=sys.stderr)
        try:
            verdicts[case.family.value] = check_live(case, model=model)
        except Exception as exc:  # noqa: BLE001 — record, don't abort the whole run
            print(f"      ERROR: {exc}", file=sys.stderr)
            verdicts[case.family.value] = {"_error": str(exc)}
    return verdicts


# ---------------------------------------------------------------------------
# Gate + report
# ---------------------------------------------------------------------------
def passes_gate(verdict: dict) -> tuple[bool, str]:
    """Apply the binary PASS rule. Returns (passed, reason). The boolean `can_state_what` plus
    `missing[]` IS the gate — the `score` float is never consulted here."""
    if "_error" in verdict:
        return False, f"checker error: {verdict['_error']}"
    if verdict.get("can_state_what") is not True:
        return False, "can_state_what is not true"
    missing = verdict.get("missing") or []
    gated_hits = [m for m in missing if any(p in str(m).lower() for p in _GATED_PIECES)]
    if gated_hits:
        return False, f"missing names a gated WHAT piece: {gated_hits}"
    return True, "ok"


def report(cases: list[FamilyCase], verdicts: dict[str, dict]) -> bool:
    """Print the per-family report; return True iff every family passes the gate."""
    by_family = {c.family.value: c for c in cases}
    all_pass = True
    print("\n=== SC-001 render-checker eval — per-family verdicts ===\n")
    for family_value in [c.family.value for c in cases]:
        verdict = verdicts.get(family_value, {"_error": "no verdict produced"})
        passed, reason = passes_gate(verdict)
        all_pass = all_pass and passed
        mark = "PASS" if passed else "FAIL"
        score = verdict.get("score", "—")
        print(f"[{mark}] {family_value:<20} score={score}  ({reason})")
        if not passed:
            print(f"        restated_job    : {verdict.get('restated_job', '—')}")
            print(f"        restated_outcome: {verdict.get('restated_outcome', '—')}")
            print(f"        missing         : {verdict.get('missing', [])}")
        warns = by_family[family_value].render_warnings
        if warns:
            print(f"        render warnings : {list(warns)}")
    print()
    print("SC-001 gate:", "PASS — every family states the WHAT" if all_pass else "FAIL")
    return all_pass


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="eval_render_checker",
        description="SC-001 sign-off: dispatch cast-requirements-checker per family and gate.",
    )
    parser.add_argument(
        "--live", action="store_true",
        help="Dispatch the real checker per family via the claude CLI (slow, network).",
    )
    parser.add_argument(
        "--verdicts", metavar="FILE",
        help="Replay verdicts from a saved JSON file ({family: verdict}); no network.",
    )
    parser.add_argument(
        "--out-verdicts", metavar="FILE",
        help="With --live, write the collected verdicts JSON here for later replay.",
    )
    parser.add_argument("--model", default="sonnet", help="Model for --live (default: sonnet).")
    args = parser.parse_args(argv)

    cases = build_cases()

    if args.verdicts:
        verdicts = json.loads(Path(args.verdicts).read_text(encoding="utf-8"))
    elif args.live:
        verdicts = run_verdicts(cases, model=args.model)
        if args.out_verdicts:
            Path(args.out_verdicts).write_text(json.dumps(verdicts, indent=2), encoding="utf-8")
            print(f"wrote verdicts → {args.out_verdicts}", file=sys.stderr)
    else:
        parser.error("pass --live (dispatch the checker) or --verdicts FILE (replay)")

    all_pass = report(cases, verdicts)
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
