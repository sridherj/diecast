"""Synthetic child agent for B5 polling integration tests.

CLI usage:
  python synthetic_child.py --output-path PATH --run-id RUN_ID --mode MODE [args]

Modes:
  --mode happy <delay_seconds>
      Sleep <delay_seconds>, then write a terminal output file with
      status="completed".

  --mode silent
      Run without ever writing the output file. Used to drive the parent's
      idle-timeout path.

  --mode heartbeat <total_seconds>
      Touch the output file every 2s for <total_seconds>; write a terminal
      payload at the end. Used to verify mtime-based heartbeat resets the
      idle-timeout countdown.

  --mode slow-atomic
      Open the .tmp file, sleep 1s with the file open and partial bytes
      buffered, then complete the write and rename. Used to verify the
      parent never observes a partially-written JSON during the .tmp
      window.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone


def _payload(run_id: str, status: str = "completed") -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "contract_version": "2",
        "agent_name": "synthetic-child",
        "task_title": "B5 fixture",
        "status": status,
        "summary": "synthetic-child terminal output",
        "artifacts": [],
        "errors": [],
        "next_steps": [],
        "human_action_needed": False,
        "human_action_items": [],
        "started_at": now,
        "completed_at": now,
    }


def write_terminal(output_path: str, run_id: str, status: str = "completed") -> None:
    """Atomic write: serialize to .tmp then os.rename to final."""
    tmp = f"{output_path}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(_payload(run_id, status), fh)
    os.rename(tmp, output_path)


def write_terminal_slow(output_path: str, run_id: str, mid_sleep: float = 1.0) -> None:
    """Atomic write with a deliberate delay between open and rename.

    Holds the .tmp file open with a partial-write window; verifies that
    the parent never observes the half-written content because the parent
    only reads the final (post-rename) path.
    """
    tmp = f"{output_path}.tmp"
    payload = json.dumps(_payload(run_id, "completed"))
    with open(tmp, "w", encoding="utf-8") as fh:
        # Write only the first half, flush, sleep with file open.
        half = len(payload) // 2
        fh.write(payload[:half])
        fh.flush()
        os.fsync(fh.fileno())
        time.sleep(mid_sleep)
        fh.write(payload[half:])
        fh.flush()
        os.fsync(fh.fileno())
    os.rename(tmp, output_path)


def mode_happy(output_path: str, run_id: str, delay_seconds: float) -> None:
    time.sleep(delay_seconds)
    write_terminal(output_path, run_id, status="completed")


def mode_silent() -> None:
    # Hold open long enough for any reasonable test idle-timeout to fire.
    # Tests typically use idle_timeout in [4, 30] seconds; sleep well beyond
    # the longest, but cap so a hung test doesn't wedge CI.
    time.sleep(120)


def mode_heartbeat(output_path: str, run_id: str, total_seconds: float) -> None:
    """Heartbeat by writing a parseable, non-terminal JSON file every 2s.

    The parent's polling loop calls `json.load` on the file each tick, so the
    heartbeat content must parse cleanly. We deliberately omit the `status`
    key so the loop's `data.status in {completed, partial, failed}` check
    evaluates to False and polling continues. Each subsequent tick re-writes
    the same heartbeat JSON via tmp+rename so mtime advances and the
    parent's idle-timeout countdown resets. At the deadline we atomic-rename
    a real terminal payload.
    """
    heartbeat_payload = {
        "contract_version": "2",
        "agent_name": "synthetic-child",
        "task_title": "B5 fixture",
        # status intentionally omitted — non-terminal heartbeat marker.
        "summary": "heartbeat",
        "artifacts": [],
        "errors": [],
        "next_steps": [],
        "human_action_needed": False,
        "human_action_items": [],
        "started_at": "",
        "completed_at": "",
    }
    deadline = time.monotonic() + total_seconds
    while time.monotonic() < deadline:
        tmp = f"{output_path}.tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(heartbeat_payload, fh)
            fh.flush()
            os.fsync(fh.fileno())
        os.rename(tmp, output_path)
        time.sleep(2)
    write_terminal(output_path, run_id, status="completed")


def mode_slow_atomic(output_path: str, run_id: str) -> None:
    write_terminal_slow(output_path, run_id, mid_sleep=1.0)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-path", required=True, help="Path to terminal output JSON")
    parser.add_argument("--run-id", required=True, help="Run id (used in payload)")
    parser.add_argument(
        "--mode",
        required=True,
        choices=("happy", "silent", "heartbeat", "slow-atomic"),
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Seconds to wait (happy mode) or total runtime (heartbeat mode).",
    )
    args = parser.parse_args(argv)

    # Ensure output directory exists.
    parent_dir = os.path.dirname(args.output_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    if args.mode == "happy":
        mode_happy(args.output_path, args.run_id, args.delay)
    elif args.mode == "silent":
        mode_silent()
    elif args.mode == "heartbeat":
        mode_heartbeat(args.output_path, args.run_id, args.delay)
    elif args.mode == "slow-atomic":
        mode_slow_atomic(args.output_path, args.run_id)
    else:
        parser.error(f"unknown mode: {args.mode}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
