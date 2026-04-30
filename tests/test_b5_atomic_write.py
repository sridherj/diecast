"""B5 atomic-write contract test.

Per spec `docs/specs/cast-delegation-contract.collab.md` § Atomic Write Contract:
  - child writes to `<...>.output.json.tmp`, then `os.rename` to final.
  - parent NEVER reads `*.tmp`.
  - `os.rename` is atomic on POSIX local filesystems.

This test exercises a child that holds the .tmp file open with a partial-write
window (slow-atomic mode). The parent polls aggressively (5ms ticks) during the
write window. The contract guarantees the parent never observes a JSONDecodeError
and never sees half-written content — only the final, atomically-renamed payload.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNTHETIC_CHILD = REPO_ROOT / "tests" / "fixtures" / "synthetic_child.py"

sys.path.insert(0, str(REPO_ROOT))

from agents._shared.polling import poll_for_terminal_output  # noqa: E402


def test_b5_atomic_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Parent never observes JSONDecodeError or partial state during slow-atomic write."""
    monkeypatch.setenv("CAST_DISABLE_SERVER", "1")
    # 5ms ticks ensure the parent polls multiple times during the child's
    # ~1s write window — proving the atomic-rename guarantee, not just luck.
    monkeypatch.setenv("CAST_DELEGATION_BACKOFF_OVERRIDE", "5ms")
    monkeypatch.setenv("CAST_DELEGATION_IDLE_TIMEOUT_SECONDS", "30")

    run_id = "run_test_b5_atomic"
    output_path = tmp_path / f".agent-run_{run_id}.output.json"

    args = [
        sys.executable,
        str(SYNTHETIC_CHILD),
        "--output-path",
        str(output_path),
        "--run-id",
        run_id,
        "--mode",
        "slow-atomic",
    ]
    child = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        start = time.monotonic()
        result = poll_for_terminal_output(str(output_path))
        elapsed = time.monotonic() - start
    finally:
        child.wait(timeout=10)

    # Atomic rename guarantees the parent only ever observed the final content.
    assert result["status"] == "completed", (
        f"parent observed non-completed payload — atomic-rename contract may be broken: {result}"
    )
    assert "malformed" not in (result.get("summary") or "").lower(), (
        "parent observed malformed JSON during slow-atomic write — contract violated"
    )
    assert result["agent_name"] == "synthetic-child"
    assert result["contract_version"] == "2"
    # Final file must be valid JSON on disk.
    on_disk = json.loads(output_path.read_text(encoding="utf-8"))
    assert on_disk == result, "in-memory payload diverges from on-disk file"
    # No `.tmp` file should remain after a clean atomic rename.
    leftover_tmp = output_path.with_suffix(output_path.suffix + ".tmp")
    assert not leftover_tmp.exists(), f"residual .tmp file: {leftover_tmp}"
    # Sanity: the run actually exercised the write window (>=1s child sleep).
    assert elapsed >= 0.8, f"polling completed too fast — child may not have entered slow-atomic window: {elapsed:.2f}s"
