#!/usr/bin/env python
"""Phase-4a sign-off eval for the maker-path **quality gate** (`cast-requirements-render-checker`).

This is the Phase-4a counterpart to `eval_render_checker.py` (the Phase-3a SC-001 cold-reader
gate). Where that eval asks "can the checker state the WHAT from the deterministic substrate?",
this one asks the load-bearing Phase-4a question:

    **Do the two gates measure different things?** — i.e. does the LLM checker FAIL a render the
    deterministic `maker_gate` PASSES, because the render is structurally clean but communicatively
    bad? And does it NOT fail a render that honestly surfaces a *source* gap?

It runs the real `cast-requirements-render-checker` over a small calibration corpus and applies the
**production** code-side gate — `checker_verdict.derive_pass` / `canonical_score`, imported, never
copied — to each verdict. The corpus:

  • `low_quality`   — the committed `fixtures/quality_gate/low_quality_attempt.html`: structurally
                      VALID (passes `maker_gate.check_html`) but communicatively BAD. **MUST FAIL**
                      the checker. This is the *deterministic, blocking* half of the gate.
  • `gap_amnesty`   — `fixtures/quality_gate/gap_amnesty_attempt.html`: a well-communicated page that
                      surfaces a *source* outcome gap with a `.rr-gap` marker. **MUST NOT FAIL** for
                      a "missing outcome" (the revision-d amnesty clause — protects the Phase-5 gap
                      contract). Also blocking.
  • `maker_evidence`— the Phase-1a maker-evidence HTML per family (`spikes/1a/*-maker.html`).
                      Expected PASS; a FAIL is a **human-eyeball carry-forward**, never a hard block
                      in autonomous (no-browser / no-human) mode (the project no-browser-visual-gate
                      convention — see [T3] below).
  • `deterministic` — the v2 deterministic render per family. Expected PASS; a FAIL is likewise a
                      carry-forward (the deterministic substrate's own SC-001 gate is
                      `eval_render_checker.py`, unmodified).

Calibration discipline (copied verbatim from `eval_render_checker.py`)
----------------------------------------------------------------------
Below the bar, the **first lever is ALWAYS the checker prompt** (a content edit to
`cast-requirements-render-checker.md`) — **never** weakening the code-side gate
(`checker_verdict.derive_pass`). A second copy of the gate would be drift by construction; this
harness IMPORTS it so eval and production can never disagree.

[T3] Autonomous-mode handling
-----------------------------
The "judged legitimate on human review" branch of the calibration gate cannot execute without a
human. So this eval splits its cases into **blocking** (deterministic, no human needed) and
**carry-forward** (a FAIL is recorded for a human eyeball, never silently passed, never a hard
block). In autonomous mode the ONLY blocking assertions are:

    low_quality   MUST fail   (fully deterministic — structural-valid + checker-fail)
    gap_amnesty   MUST pass   (the amnesty clause)

A human-run `--live` exercises the full discriminate-both-ways gate.

Why it is NOT a `test_*` file
-----------------------------
Named `eval_*` so pytest's default collection skips it (the classifier-eval precedent). A `--live`
run shells out to `claude` (slow + network). Run it by hand:

    # Live — dispatch the real checker per corpus case (slow; needs the claude CLI):
    uv run --project cast-server python cast-server/tests/eval_quality_gate.py --live

    # Offline replay from the committed calibration verdicts (deterministic, no network — this is
    # what CI / `test_eval_quality_gate.py` runs):
    uv run --project cast-server python cast-server/tests/eval_quality_gate.py \
        --verdicts cast-server/tests/fixtures/quality_gate/replay_verdicts.json

    # Save a live run's verdicts for later replay / inspection:
    uv run --project cast-server python cast-server/tests/eval_quality_gate.py \
        --live --out-verdicts /tmp/quality_verdicts.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# --- repo bootstrap (mirror conftest: put cast-server/ on sys.path) --------------------
_TESTS_DIR = Path(__file__).resolve().parent
_CAST_SERVER_DIR = _TESTS_DIR.parent
_REPO_ROOT = _CAST_SERVER_DIR.parent
if str(_CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(_CAST_SERVER_DIR))

from cast_server.requirements_render import parse_requirements  # noqa: E402
from cast_server.requirements_render.families import WorkFamily  # noqa: E402
from cast_server.requirements_render.maker_gate import check_html  # noqa: E402
from cast_server.requirements_render.renderer import render_requirements  # noqa: E402
from cast_server.requirements_render.zero_click import extract_zero_click_view  # noqa: E402

# THE production gate — imported, never copied (eval and production share ONE implementation).
from cast_server.requirements_render.checker_verdict import (  # noqa: E402
    CHECKER_CONTRACT,
    CheckerVerdictError,
    canonical_score,
    derive_pass,
    parse_verdict,
)

_CHECKER_PROMPT = (
    _REPO_ROOT / "agents" / "cast-requirements-render-checker"
    / "cast-requirements-render-checker.md"
)
_FIXTURES = _TESTS_DIR / "fixtures" / "quality_gate"
_SPIKE_1A = (
    _REPO_ROOT / "docs" / "goal" / "refine-requirements-better-rendering-v3"
    / "spikes" / "1a"
)

# The source the committed `low_quality_attempt.html` / `gap_amnesty_attempt.html` fixtures are
# authored against — byte-identical (US1/FR-001/SC-001) to `test_render_job_service._SOURCE`, so the
# fixtures provably PASS `maker_gate.check_html`. Kept here so the structural-validity half of the
# gate is self-contained (no import from a test module).
_PAD = " ".join(["The export must be dependable and observable across the whole nightly window."] * 20)
_FIXTURE_SOURCE = f"""\
---
classification:
  family: new_initiative
  confidence: 0.95
---
# Demo Goal

## Intent

The team wants a dependable nightly report export so downstream data lands on time. {_PAD}

## User Stories

### US1 — export cadence

As a user I want a recurring cadence for a report export.

Acceptance: the export runs nightly.

## Functional Requirements

| ID | Requirement | Source |
|---|---|---|
| FR-001 | The system must export nightly. | US1 |

## Success Criteria

| ID | Criterion | Measure |
|---|---|---|
| SC-001 | Exports complete within ten minutes. | timed |
"""

# The two families with committed Phase-1a maker evidence + a deterministic render to discriminate.
_CALIBRATION_FAMILIES = (WorkFamily.BUG_FIX, WorkFamily.NEW_INITIATIVE)


# ---------------------------------------------------------------------------
# Corpus
# ---------------------------------------------------------------------------
@dataclass
class Case:
    """One calibration case. `blocking` cases hard-fail the eval on a gate mismatch in autonomous
    mode; non-blocking cases route a mismatch to a human-eyeball carry-forward ([T3])."""

    case_id: str
    kind: str  # low_quality | gap_amnesty | maker_evidence | deterministic
    html: str
    expected_pass: bool
    blocking: bool
    family: str | None = None
    structural_source: str | None = None  # paired source for a check_html structural assertion
    notes: list[str] = field(default_factory=list)


def _load_family_doc_builder():
    """Import `_build_family_doc` from the behavioural test module (single source of truth — the
    same builder `eval_render_checker.py` reuses, never a fork)."""
    spec = importlib.util.spec_from_file_location(
        "_rr_test_builders", _TESTS_DIR / "test_requirements_renderer.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module._build_family_doc


def build_cases() -> list[Case]:
    """Assemble the calibration corpus: the two committed fixtures (blocking) + the per-family
    maker-evidence and deterministic renders (carry-forward)."""
    cases: list[Case] = [
        Case(
            case_id="low_quality",
            kind="low_quality",
            html=(_FIXTURES / "low_quality_attempt.html").read_text(encoding="utf-8"),
            expected_pass=False,   # MUST fail the checker …
            blocking=True,         # … the deterministic blocking half of the gate.
            structural_source=_FIXTURE_SOURCE,  # … while PASSING maker_gate.check_html.
            notes=["structurally valid, communicatively bad — the two-gates thesis"],
        ),
        Case(
            case_id="gap_amnesty",
            kind="gap_amnesty",
            html=(_FIXTURES / "gap_amnesty_attempt.html").read_text(encoding="utf-8"),
            expected_pass=True,    # MUST NOT fail for a 'missing outcome' …
            blocking=True,         # … the amnesty clause is blocking (protects the Phase-5 gap contract).
            structural_source=_FIXTURE_SOURCE,
            notes=[".rr-gap marker is honest source-gap communication, not a render defect"],
        ),
    ]

    build_family_doc = _load_family_doc_builder()
    for family in _CALIBRATION_FAMILIES:
        # v2 deterministic render of this family.
        det = render_requirements(parse_requirements(build_family_doc(family)))
        cases.append(Case(
            case_id=f"deterministic:{family.value}",
            kind="deterministic",
            html=det.html,
            expected_pass=True,
            blocking=False,  # the substrate's own gate is eval_render_checker.py — carry-forward here
            family=family.value,
        ))
        # Phase-1a maker evidence for this family, if committed.
        maker_path = _SPIKE_1A / f"{family.value}-maker.html"
        if maker_path.exists():
            cases.append(Case(
                case_id=f"maker_evidence:{family.value}",
                kind="maker_evidence",
                html=maker_path.read_text(encoding="utf-8"),
                expected_pass=True,
                blocking=False,  # a 1a-evidence FAIL → human-eyeball carry-forward ([T3])
                family=family.value,
            ))
    return cases


# ---------------------------------------------------------------------------
# Verdict backends
# ---------------------------------------------------------------------------
def _checker_user_msg(case: Case) -> str:
    """The runner's exact checker prompt shape (`render_job_service._build_checker_prompt`): the
    zero-click view first (what a non-clicking reader sees), then the full HTML + the family label.
    The checker is tool-free, so this text IS its whole world (the cold-reader property)."""
    zero_click = extract_zero_click_view(case.html)
    family = f"work_family: {case.family}\n" if case.family else ""
    return (
        f"Grade this rendered requirements page. Emit ONE bare JSON verdict (contract "
        f"{CHECKER_CONTRACT}) — no prose, no code fences.\n"
        f"{family}"
        f"\n----- BEGIN ZERO-CLICK VIEW (what a non-clicking reader sees) -----\n"
        f"{zero_click}\n"
        f"----- END ZERO-CLICK VIEW -----\n"
        f"\n----- BEGIN FULL RENDERED HTML -----\n"
        f"{case.html}\n"
        f"----- END FULL RENDERED HTML -----\n"
    )


def check_live(case: Case, model: str = "opus", timeout_s: int = 900) -> str:
    """Dispatch the real `cast-requirements-render-checker` over one case via `claude -p`. Returns
    the raw stdout (parsed by the PRODUCTION `parse_verdict`). `--tools ""` disables all tools — the
    harness has already produced the artifact, so the agent is pure text-in / JSON-out."""
    prompt = _CHECKER_PROMPT.read_text(encoding="utf-8")
    proc = subprocess.run(
        ["claude", "-p", _checker_user_msg(case),
         "--append-system-prompt", prompt, "--model", model, "--tools", ""],
        capture_output=True, text=True, timeout=timeout_s,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI failed for {case.case_id}: {proc.stderr.strip()[:400]}")
    return proc.stdout


def run_live_verdicts(cases: list[Case], model: str) -> dict[str, str]:
    """Check every case live; collect RAW verdict strings keyed by case_id. A per-case failure is
    recorded (never silently dropped) so the gate denominator stays honest."""
    verdicts: dict[str, str] = {}
    for i, case in enumerate(cases, 1):
        print(f"  [{i}/{len(cases)}] checking {case.case_id} ...", file=sys.stderr)
        try:
            verdicts[case.case_id] = check_live(case, model=model)
        except Exception as exc:  # noqa: BLE001 — record, don't abort the whole run
            print(f"      ERROR: {exc}", file=sys.stderr)
            verdicts[case.case_id] = json.dumps({"_error": str(exc)})
    return verdicts


def _coerce_raw(value) -> str:
    """A replay verdicts file may store each verdict as a JSON object (preferred — exercises the
    production `parse_verdict`) or as a raw string. Normalise to the raw string the gate parses."""
    return value if isinstance(value, str) else json.dumps(value)


# ---------------------------------------------------------------------------
# Gate (THE production gate — imported, never reimplemented)
# ---------------------------------------------------------------------------
def gate_case(raw: str) -> tuple[bool | None, str, float | None]:
    """Apply the production gate to one raw verdict → (passed, reason, canonical_score).

    `passed` is None when the checker was unavailable / unparseable (recorded, never coerced to a
    pass or a fail by THIS layer — that policy is the service's, not the eval's)."""
    try:
        obj = json.loads(raw) if raw.strip().startswith("{") else None
    except json.JSONDecodeError:
        obj = None
    if obj is not None and "_error" in obj:
        return None, f"checker unavailable: {obj['_error']}", None
    try:
        verdict = parse_verdict(raw)
    except CheckerVerdictError as exc:
        return None, f"unparseable verdict: {exc}", None
    passed = derive_pass(verdict)
    score = canonical_score(verdict)
    if passed:
        return True, "ok", score
    reasons = []
    if not verdict.can_state_what:
        reasons.append("can_state_what=false")
    gated = [m for m in verdict.missing
             if any(tok in str(m).lower() for tok in ("job", "outcome", "scope"))]
    if gated:
        reasons.append(f"missing names a gated WHAT piece: {gated}")
    if verdict.error_issues:
        reasons.append(f"{len(verdict.error_issues)} error-severity issue(s)")
    return False, "; ".join(reasons) or "derive_pass=false", score


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def report(cases: list[Case], verdicts: dict[str, str]) -> tuple[bool, list[str]]:
    """Print the per-case report; return (blocking_gate_ok, carry_forward_items).

    The blocking gate passes iff every BLOCKING case's derived pass/fail matches `expected_pass`.
    Non-blocking mismatches become human-eyeball carry-forward items (never a hard block)."""
    print("\n=== Phase-4a quality-gate eval — per-case verdicts ===\n")
    blocking_ok = True
    carry_forward: list[str] = []

    for case in cases:
        raw = verdicts.get(case.case_id, json.dumps({"_error": "no verdict produced"}))
        passed, reason, score = gate_case(_coerce_raw(raw))

        # Structural-validity assertion (deterministic; the low_quality blocking half).
        struct_note = ""
        if case.structural_source is not None:
            rep = check_html(case.html, parse_requirements(case.structural_source))
            struct_note = " struct=VALID" if rep.passed else f" struct=INVALID({rep.violations})"
            if not rep.passed and case.kind == "low_quality":
                blocking_ok = False  # the fixture must pass the structural gate to prove the thesis

        match = (passed is True) == case.expected_pass
        score_s = f"{score:.2f}" if score is not None else "—"
        want = "PASS" if case.expected_pass else "FAIL"
        got = "PASS" if passed is True else ("FAIL" if passed is False else "UNAVAIL")
        tag = "blocking" if case.blocking else "carry-fwd"
        mark = "OK " if match and passed is not None else "XX "
        print(f"[{mark}] {case.case_id:<28} want={want} got={got} score={score_s} "
              f"({tag}){struct_note}")
        if not match or passed is None:
            print(f"        reason: {reason}")
            for n in case.notes:
                print(f"        note  : {n}")

        if case.blocking:
            if not (match and passed is not None):
                blocking_ok = False
        else:
            if not match or passed is None:
                carry_forward.append(
                    f"{case.case_id}: want={want} got={got} ({reason}) — human-eyeball review"
                )

    print()
    print("BLOCKING gate:", "PASS" if blocking_ok else "FAIL",
          "— low_quality MUST-fail + gap_amnesty MUST-not-fail (+ structural validity)")
    if carry_forward:
        print("\nHuman-eyeball CARRY-FORWARD (never a silent pass, never a hard block — [T3]):")
        for item in carry_forward:
            print(f"  • {item}")
    return blocking_ok, carry_forward


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="eval_quality_gate",
        description="Phase-4a sign-off: discriminate good vs. low-quality renders via the real checker.",
    )
    parser.add_argument("--live", action="store_true",
                        help="Dispatch the real checker per case via the claude CLI (slow, network).")
    parser.add_argument("--verdicts", metavar="FILE",
                        help="Replay verdicts from a saved JSON file ({case_id: verdict}); no network.")
    parser.add_argument("--out-verdicts", metavar="FILE",
                        help="With --live, write the collected verdicts JSON here for later replay.")
    parser.add_argument("--model", default="opus", help="Model for --live (default: opus).")
    args = parser.parse_args(argv)

    cases = build_cases()

    if args.verdicts:
        raw = json.loads(Path(args.verdicts).read_text(encoding="utf-8"))
        verdicts = {k: _coerce_raw(v) for k, v in raw.items()}
    elif args.live:
        verdicts = run_live_verdicts(cases, model=args.model)
        if args.out_verdicts:
            Path(args.out_verdicts).write_text(json.dumps(verdicts, indent=2), encoding="utf-8")
            print(f"wrote verdicts → {args.out_verdicts}", file=sys.stderr)
    else:
        parser.error("pass --live (dispatch the checker) or --verdicts FILE (replay)")

    blocking_ok, _carry = report(cases, verdicts)
    return 0 if blocking_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
