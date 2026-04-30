"""B4 code-review delegation tests.

Covers the four mandated branches of the cast-subphase-runner Post-Execution
Review flow:

  * coding sub-phase + high-confidence Edit-applicable issue under allowed
    root → auto-apply
  * non-coding sub-phase → no review dispatched (classifier only)
  * coding sub-phase + low-confidence issue → recorded to followup
  * coding sub-phase + high-confidence Edit on out-of-tree path → refused

Per `docs/execution/diecast-open-source/phase-3a/sp3d_b4_code_review_delegation/plan.md`,
the path-traversal-rejected fixture is mandatory (plan-review Issue #11).

These tests exercise `agents/_shared/review_apply.py` — the deterministic
guts of the runner's review-handling flow. The runner prompt itself is
markdown that wires these primitives into a Claude session.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agents._shared.review_apply import (  # noqa: E402
    classify_subphase,
    is_path_under,
    process_review_payload,
)


FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "subphases"
PAYLOAD_ROOT = REPO_ROOT / "tests" / "fixtures" / "cast_review_code_payloads"


def _copy_fixture(name: str, tmp_path: Path) -> Path:
    """Copy a fixture sub-phase tree into tmp_path; returns the new plan.md path."""
    dst = tmp_path / name
    shutil.copytree(FIXTURE_ROOT / name, dst)
    return dst / "plan.md"


def _load_payload(name: str, target_override: Path | None = None) -> dict:
    """Load a stub cast-review-code payload, optionally rewriting issue.file paths.

    `target_override` lets a test point review issues at the copied fixture
    location inside `tmp_path` rather than the on-disk fixture directory.
    """
    raw = (PAYLOAD_ROOT / name).read_text()
    payload = json.loads(raw)
    if target_override is not None:
        for art in payload.get("artifacts", []):
            for issue in (art.get("metadata") or {}).get("issues", []):
                # Only rewrite paths that point at the source fixture tree;
                # leave out-of-tree paths (e.g. /etc/passwd) untouched.
                if issue.get("file", "").startswith("tests/fixtures/subphases/"):
                    fname = Path(issue["file"]).name
                    issue["file"] = str(target_override / fname)
    return payload


# --- classifier tests ----------------------------------------------------


def test_classify_coding_fixture_is_coding():
    plan_text = (FIXTURE_ROOT / "b4_coding_autofix" / "plan.md").read_text()
    assert classify_subphase(plan_text) == "coding"


def test_classify_non_coding_fixture_is_non_coding():
    plan_text = (FIXTURE_ROOT / "b4_non_coding" / "plan.md").read_text()
    assert classify_subphase(plan_text) == "non-coding"


# --- path-traversal guard ------------------------------------------------


def test_is_path_under_rejects_etc_passwd(tmp_path):
    allowed = [tmp_path]
    assert not is_path_under("/etc/passwd", allowed)


def test_is_path_under_accepts_subdirectory(tmp_path):
    target = tmp_path / "child" / "file.py"
    assert is_path_under(target, [tmp_path])


def test_is_path_under_rejects_dotdot_traversal(tmp_path):
    nested = tmp_path / "inside"
    nested.mkdir()
    escape = nested / ".." / ".." / "outside.txt"
    assert not is_path_under(escape, [nested])


# --- B4 mandated branches -------------------------------------------------


def test_b4_coding_autofix(tmp_path):
    """Coding + high-confidence + Edit-applicable + in-tree → auto-applied."""
    plan_path = _copy_fixture("b4_coding_autofix", tmp_path)
    target_dir = plan_path.parent
    payload = _load_payload("autofix.json", target_override=target_dir)

    target = target_dir / "b4_autofix_target.py"
    assert not target.read_text().endswith("\n"), "fixture should start without trailing newline"

    result = process_review_payload(
        payload,
        plan_path=plan_path,
        allowed_roots=[tmp_path],
    )

    assert len(result["auto_applied"]) == 1
    assert result["followup"] == []
    assert target.read_text().endswith("\n"), "high-confidence Edit should have landed"


def test_b4_non_coding_skips(tmp_path):
    """Non-coding sub-phase classifies as non-coding; no review processing required.

    The runner uses this signal to skip dispatch entirely. We assert the
    classifier output and confirm no followup file is created on a no-op
    review pass.
    """
    plan_path = _copy_fixture("b4_non_coding", tmp_path)
    plan_text = plan_path.read_text()

    assert classify_subphase(plan_text) == "non-coding"

    # If the runner were to (incorrectly) process an empty review payload, no
    # followup file should appear.
    result = process_review_payload(
        {"artifacts": []},
        plan_path=plan_path,
        allowed_roots=[tmp_path],
    )
    assert result["auto_applied"] == []
    assert result["followup"] == []
    assert not (plan_path.parent / "plan.md.followup.md").exists()


def test_b4_low_confidence_goes_to_followup(tmp_path):
    """Low-confidence issue → followup.md written; source untouched."""
    plan_path = _copy_fixture("b4_coding_ambiguous", tmp_path)
    target_dir = plan_path.parent
    payload = _load_payload("low_confidence.json", target_override=target_dir)

    source = target_dir / "b4_ambiguous_target.py"
    before = source.read_text()

    result = process_review_payload(
        payload,
        plan_path=plan_path,
        allowed_roots=[tmp_path],
    )

    assert result["auto_applied"] == []
    assert len(result["followup"]) == 1
    followup_path = result["followup_path"]
    assert followup_path.exists()
    text = followup_path.read_text()
    assert "low" in text  # confidence: low
    # Source file untouched
    assert source.read_text() == before


def test_b4_path_traversal_rejected(tmp_path):
    """High-confidence Edit on /etc/passwd → refused, recorded, no out-of-tree write."""
    plan_path = _copy_fixture("b4_coding_path_traversal", tmp_path)
    payload = _load_payload("path_traversal.json")  # leaves /etc/passwd as-is

    # Sanity: the issue really targets /etc/passwd
    issue = payload["artifacts"][0]["metadata"]["issues"][0]
    assert issue["file"] == "/etc/passwd"

    result = process_review_payload(
        payload,
        plan_path=plan_path,
        allowed_roots=[tmp_path],
    )

    assert result["auto_applied"] == []
    assert len(result["followup"]) == 1
    followup_text = result["followup_path"].read_text()
    assert "out-of-tree" in followup_text or "refused" in followup_text


def test_b4_high_confidence_but_file_creation_goes_to_followup(tmp_path):
    """High-confidence but no old_string (file-creation shape) → followup.

    Guards the auto-apply contract: only single-string Edit patches qualify.
    """
    plan_path = _copy_fixture("b4_coding_autofix", tmp_path)
    target_dir = plan_path.parent
    payload = {
        "contract_version": "2",
        "agent_name": "cast-review-code",
        "artifacts": [
            {
                "path": str(target_dir / "b4_autofix_target.py"),
                "type": "code",
                "metadata": {
                    "issues": [
                        {
                            "file": str(target_dir / "b4_autofix_target.py"),
                            "summary": "Create new helper module",
                            "new_string": "def helper(): ...\n",
                            "confidence": "high",
                        }
                    ]
                },
            }
        ],
    }
    result = process_review_payload(
        payload,
        plan_path=plan_path,
        allowed_roots=[tmp_path],
    )
    assert result["auto_applied"] == []
    assert len(result["followup"]) == 1
    assert "not Edit-tool-applicable" in result["followup_path"].read_text()
