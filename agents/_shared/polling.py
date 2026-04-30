"""File-based parent polling primitive — runtime encoding of cast-delegation-contract.

This is the Python implementation of the polling loop documented in
`docs/specs/cast-delegation-contract.collab.md` and
`skills/claude-code/cast-child-delegation/SKILL.md` (§ Section 2b).

NEVER `import requests | httpx | urllib` from this module — file is canonical.
The HTTP-API layer lives in cast-server (Phase 3b) and is best-effort augmentation.

Env-var contract:
    CAST_DELEGATION_IDLE_TIMEOUT_SECONDS  int    Default 300.
    CAST_DELEGATION_BACKOFF_OVERRIDE       csv    e.g. "10ms,20ms,50ms,100ms"
    CAST_DISABLE_SERVER                    "1"   Force file-based path; skip HTTP.

Public API:
    poll_for_terminal_output(output_path, *, idle_timeout=None, backoff=None,
                             clock=None, sleep=None, cancel=None) -> dict

Returns the child's terminal payload (the dict loaded from the output JSON), OR a
synthetic failure dict when the child times out, emits malformed JSON, or emits a
non-terminal status.

The function is fully injectable for tests:
    - clock: callable returning current monotonic seconds (default time.monotonic)
    - sleep: callable that sleeps for N seconds (default time.sleep)
    - cancel: callable returning True to cancel polling (default lambda: False)
"""

from __future__ import annotations

import json
import os
import time
from typing import Callable, Optional, Sequence

TERMINAL_STATUSES = frozenset({"completed", "partial", "failed"})

_DEFAULT_BACKOFF: tuple[float, ...] = (1.0, 2.0, 5.0, 10.0, 30.0)
_DEFAULT_IDLE_TIMEOUT_SECONDS: float = 300.0


def parse_duration(token: str) -> float:
    """Parse a duration token into seconds.

    Accepts:
        '500ms' -> 0.5
        '2s'    -> 2.0
        '10'    -> 10.0  (bare number = seconds)
        '1m'    -> 60.0
    """
    token = token.strip().lower()
    if not token:
        raise ValueError("empty duration token")
    if token.endswith("ms"):
        return float(token[:-2]) / 1000.0
    if token.endswith("s"):
        return float(token[:-1])
    if token.endswith("m"):
        return float(token[:-1]) * 60.0
    return float(token)


def parse_backoff_csv(csv: Optional[str]) -> Optional[tuple[float, ...]]:
    if csv is None:
        return None
    csv = csv.strip()
    if not csv:
        return None
    return tuple(parse_duration(part) for part in csv.split(","))


def _resolve_backoff(override: Optional[Sequence[float]] = None) -> tuple[float, ...]:
    if override is not None:
        return tuple(override)
    env_csv = os.environ.get("CAST_DELEGATION_BACKOFF_OVERRIDE")
    parsed = parse_backoff_csv(env_csv)
    if parsed:
        return parsed
    return _DEFAULT_BACKOFF


def _resolve_idle_timeout(override: Optional[float] = None) -> float:
    if override is not None:
        return float(override)
    env_val = os.environ.get("CAST_DELEGATION_IDLE_TIMEOUT_SECONDS")
    if env_val:
        return float(env_val)
    return _DEFAULT_IDLE_TIMEOUT_SECONDS


def _malformed(output_path: str, error: str) -> dict:
    return {
        "contract_version": "2",
        "agent_name": "<unknown>",
        "task_title": "",
        "status": "failed",
        "summary": "Parent observed malformed child output.",
        "artifacts": [],
        "errors": [f"malformed child output at {output_path}: {error}"],
        "next_steps": [],
        "human_action_needed": True,
        "human_action_items": [
            f"Inspect {output_path} for malformed JSON or non-terminal status."
        ],
        "started_at": "",
        "completed_at": "",
    }


def _idle_timeout_failure(output_path: str, idle_timeout: float) -> dict:
    return {
        "contract_version": "2",
        "agent_name": "<unknown>",
        "task_title": "",
        "status": "failed",
        "summary": f"Child idle for {idle_timeout}s; no mtime change observed.",
        "artifacts": [],
        "errors": [f"child idle for {idle_timeout}s; check {output_path}"],
        "next_steps": [],
        "human_action_needed": True,
        "human_action_items": [
            f"Inspect {output_path}; child may be hung or never started."
        ],
        "started_at": "",
        "completed_at": "",
    }


def _cancelled_failure() -> dict:
    return {
        "contract_version": "2",
        "agent_name": "<unknown>",
        "task_title": "",
        "status": "failed",
        "summary": "Polling cancelled.",
        "artifacts": [],
        "errors": ["cancelled"],
        "next_steps": [],
        "human_action_needed": False,
        "human_action_items": [],
        "started_at": "",
        "completed_at": "",
    }


def _try_read_terminal(output_path: str) -> tuple[Optional[dict], Optional[float]]:
    """Attempt to read terminal payload + current mtime.

    Returns (payload_or_None, mtime_or_None).
    payload is None when the file is empty (heartbeat-only) or has non-terminal status.
    Raises json.JSONDecodeError on malformed JSON (caller handles).
    """
    try:
        st = os.stat(output_path)
    except FileNotFoundError:
        return None, None

    mtime = st.st_mtime

    if st.st_size == 0:
        return None, mtime

    with open(output_path, "r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError:
            raise

    status = data.get("status") if isinstance(data, dict) else None
    if status in TERMINAL_STATUSES:
        return data, mtime
    return None, mtime


def poll_for_terminal_output(
    output_path: str,
    *,
    idle_timeout: Optional[float] = None,
    backoff: Optional[Sequence[float]] = None,
    clock: Optional[Callable[[], float]] = None,
    sleep: Optional[Callable[[float], None]] = None,
    cancel: Optional[Callable[[], bool]] = None,
) -> dict:
    """Block until the child writes a terminal output JSON or until idle timeout.

    See module docstring and `docs/specs/cast-delegation-contract.collab.md`
    for the full contract.
    """
    backoff_ladder = _resolve_backoff(backoff)
    timeout = _resolve_idle_timeout(idle_timeout)
    now = clock or time.monotonic
    do_sleep = sleep or time.sleep
    is_cancelled = cancel or (lambda: False)

    last_mtime: Optional[float] = None
    last_progress = now()
    i = 0

    while True:
        try:
            payload, mtime = _try_read_terminal(output_path)
        except json.JSONDecodeError as e:
            return _malformed(output_path, str(e))

        if payload is not None:
            return payload

        if mtime is not None and mtime != last_mtime:
            last_mtime = mtime
            last_progress = now()

        if is_cancelled():
            return _cancelled_failure()

        if now() - last_progress > timeout:
            return _idle_timeout_failure(output_path, timeout)

        do_sleep(backoff_ladder[min(i, len(backoff_ladder) - 1)])
        i += 1
