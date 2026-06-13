"""CI guard for the Phase-4a quality-gate eval (sp4a-3).

`eval_quality_gate.py` is `eval_`-prefixed so pytest never collects it (a live run shells out to
`claude`). This `test_*` module runs the eval's **replay** path — no LLM, fully deterministic — and
pins the two blocking halves of the calibration gate:

  • the committed low-quality fixture MUST fail the checker (`derive_pass` False) **while** passing
    the structural gate (`maker_gate.check_html`) — the load-bearing "two gates measure different
    things" thesis;
  • the gap-amnesty fixture MUST NOT be failed for a "missing outcome" — the revision-d amnesty
    clause that protects the Phase-5 gap contract.

It also pins the *eval-and-production-share-one-gate* discipline: the eval's `derive_pass` /
`canonical_score` must be the very objects from `checker_verdict`, never a copy.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parent
_CAST_SERVER_DIR = _TESTS_DIR.parent
if str(_CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(_CAST_SERVER_DIR))

from cast_server.requirements_render import checker_verdict  # noqa: E402
from cast_server.requirements_render import parse_requirements  # noqa: E402
from cast_server.requirements_render.maker_gate import check_html  # noqa: E402

_REPLAY = _TESTS_DIR / "fixtures" / "quality_gate" / "replay_verdicts.json"


def _load_eval():
    """Import the `eval_`-prefixed harness by path (pytest would otherwise never load it)."""
    spec = importlib.util.spec_from_file_location(
        "eval_quality_gate", _TESTS_DIR / "eval_quality_gate.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    # Register before exec so the @dataclass decorator can resolve `cls.__module__` (Case).
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def eval_mod():
    return _load_eval()


@pytest.fixture(scope="module")
def replay(eval_mod):
    import json
    raw = json.loads(_REPLAY.read_text(encoding="utf-8"))
    return {k: eval_mod._coerce_raw(v) for k, v in raw.items() if not k.startswith("_")}


def test_blocking_gate_passes_in_replay(eval_mod, replay, capsys):
    """The whole blocking calibration gate is green on the committed verdicts (CI's no-LLM path)."""
    cases = eval_mod.build_cases()
    blocking_ok, _carry = eval_mod.report(cases, replay)
    assert blocking_ok, capsys.readouterr().out


def test_low_quality_fixture_is_the_two_gates_thesis(eval_mod, replay):
    """low_quality: structurally VALID (check_html passes) yet checker-FAILING (derive_pass False)."""
    cases = {c.case_id: c for c in eval_mod.build_cases()}
    low = cases["low_quality"]

    # Structural gate: PASSES (ids verbatim, carriage intact, zero id=/anchors).
    rep = check_html(low.html, parse_requirements(low.structural_source))
    assert rep.passed, f"low-quality fixture must pass the structural gate: {rep.violations}"

    # Checker gate: FAILS.
    passed, reason, _score = eval_mod.gate_case(replay["low_quality"])
    assert passed is False, f"low-quality fixture must FAIL the checker (got {passed}: {reason})"


def test_gap_amnesty_not_failed_for_missing_outcome(eval_mod, replay):
    """gap_amnesty: the .rr-gap marker is honest source-gap communication — must NOT fail, and the
    verdict must NOT name 'outcome' in missing[] (the amnesty clause)."""
    verdict = checker_verdict.parse_verdict(replay["gap_amnesty"])
    assert checker_verdict.derive_pass(verdict) is True
    gated = [m for m in verdict.missing if "outcome" in str(m).lower()]
    assert not gated, f"gap-amnesty must not be failed for a missing outcome: {gated}"


def test_eval_imports_production_gate_not_a_copy(eval_mod):
    """The eval reuses the production gate by IMPORT — a second copy would be drift by construction."""
    assert eval_mod.derive_pass is checker_verdict.derive_pass
    assert eval_mod.canonical_score is checker_verdict.canonical_score
    assert eval_mod.parse_verdict is checker_verdict.parse_verdict
